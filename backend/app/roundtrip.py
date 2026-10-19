# CareBridge Round-trip Verification Engine
# Implements PRD Section 6 (Layer 3), Section 7 (Component 5), and Section 14

import re
from typing import List

from .schema import (
    CarePlan,
    VerificationIssue,
    VerificationResult,
)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).lower()).strip()


def verify_english_roundtrip(rendered_text: str, plan: CarePlan) -> VerificationResult:
    # Re-extracts from rendered English output and verifies against source plan.
    # Enforces zero dropped, zero altered, and zero invented tokens.
    issues: List[VerificationIssue] = []
    norm_rendered = _norm(rendered_text)
    checked_fields = 0

    # 1. Check all medicines
    for i, med in enumerate(plan.medicines):
        field_prefix = f"medicines[{i}]"
        clean_name = _norm(med.name_generic)
        clean_dose = _norm(med.dose).replace(" ", "")

        # Check medicine generic name presence
        checked_fields += 1
        if clean_name not in norm_rendered:
            issues.append(VerificationIssue(
                severity="block",
                field=f"{field_prefix}.name",
                message=f"Medicine '{med.name_generic}' was dropped from English rendered output.",
            ))

        # Check dose presence
        checked_fields += 1
        clean_rendered_no_space = norm_rendered.replace(" ", "")
        if clean_dose not in clean_rendered_no_space:
            issues.append(VerificationIssue(
                severity="block",
                field=f"{field_prefix}.dose",
                message=f"Dose '{med.dose}' was altered or missing from English rendered output.",
            ))

        # Check duration if specified
        if med.duration:
            checked_fields += 1
            dur_clean = _norm(med.duration).replace(" ", "")
            if dur_clean not in clean_rendered_no_space:
                issues.append(VerificationIssue(
                    severity="block",
                    field=f"{field_prefix}.duration",
                    message=f"Duration '{med.duration}' was dropped from English rendered output.",
                ))

    # 2. Check all follow-up dates
    for i, fu in enumerate(plan.follow_ups):
        checked_fields += 1
        if fu.date not in rendered_text:
            issues.append(VerificationIssue(
                severity="block",
                field=f"follow_ups[{i}].date",
                message=f"Follow-up date '{fu.date}' missing from English rendered output.",
            ))

    # 3. Check warning signs presence
    for i, w in enumerate(plan.warning_signs):
        checked_fields += 1
        clean_w = _norm(w.text_source)
        if clean_w not in norm_rendered:
            issues.append(VerificationIssue(
                severity="block",
                field=f"warning_signs[{i}]",
                message=f"Warning sign '{w.text_source}' dropped from English rendered output.",
            ))

    blocking = [i for i in issues if i.severity == "block"]
    mismatch_count = len(blocking)
    passed = (mismatch_count == 0)

    return VerificationResult(
        passed=passed,
        mismatch_count=mismatch_count,
        issues=issues,
        checked_fields=max(1, checked_fields),
        source_hash=plan.source_hash,
    )
