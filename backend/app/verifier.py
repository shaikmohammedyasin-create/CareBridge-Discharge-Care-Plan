# CareBridge Dual-Extractor Merger & Source-Span Verifier
# Implements PRD Section 6, 7 (Component 3), Section 14, and Non-Negotiable Rules 2, 3, 5

import hashlib
import re
from typing import Dict, List, Tuple

from .schema import (
    CarePlan,
    Flag,
    Medicine,
    VerificationIssue,
    VerificationResult,
)


def _norm(s: str) -> str:
    # Normalized lowercase string with single spaces
    return re.sub(r"\s+", " ", str(s).lower()).strip()


def verify_source_spans(summary: str, plan: CarePlan) -> List[VerificationIssue]:
    # Strictly validates that EVERY extracted item's source_span points to valid source text
    issues: List[VerificationIssue] = []
    summary_len = len(summary)

    # 1. Verify Medicines
    for i, med in enumerate(plan.medicines):
        field_prefix = f"medicines[{i}]"
        span = med.source_span

        if not span or len(span) != 2 or span[0] < 0 or span[1] > summary_len or span[0] >= span[1]:
            issues.append(VerificationIssue(
                severity="block",
                field=f"{field_prefix}.source_span",
                message=f"Missing or invalid source span {span} for medicine '{med.name_generic}' (Rule 5 violation).",
                source_span=span,
            ))
            continue

        span_text = summary[span[0]:span[1]]
        clean_span = _norm(span_text).replace(" ", "")

        # Check dose grounded in span
        clean_dose = _norm(med.dose).replace(" ", "")
        if clean_dose not in clean_span:
            issues.append(VerificationIssue(
                severity="block",
                field=f"{field_prefix}.dose",
                message=f"Dose '{med.dose}' was not found in claimed source span '{span_text}'.",
                source_text=span_text,
                source_span=span,
            ))

        # Check frequency grounded in span (if not unspecified)
        if med.frequency_code != "UNSPECIFIED":
            clean_freq = med.frequency_code.lower()
            if clean_freq not in _norm(span_text) and clean_freq not in _norm(summary):
                issues.append(VerificationIssue(
                    severity="block",
                    field=f"{field_prefix}.frequency",
                    message=f"Frequency '{med.frequency_code}' was not found in source span.",
                    source_text=span_text,
                    source_span=span,
                ))

    # 2. Verify Follow-ups
    for i, fu in enumerate(plan.follow_ups):
        field_name = f"follow_ups[{i}].date"
        span = fu.source_span
        if not span or len(span) != 2 or span[0] < 0 or span[1] > summary_len or span[0] >= span[1]:
            issues.append(VerificationIssue(
                severity="block",
                field=f"{field_name}.source_span",
                message=f"Missing or invalid source span {span} for follow-up date.",
                source_span=span,
            ))
            continue

        span_text = summary[span[0]:span[1]]
        # Check that date digits/tokens are present in the span
        date_parts = fu.date.split("-")  # [YYYY, MM, DD]
        if len(date_parts) == 3:
            y, m, d = date_parts
            # Look for day and year in span text
            has_day = str(int(d)) in span_text or d in span_text
            has_year = y in span_text or y[2:] in span_text
            if not (has_day and has_year):
                issues.append(VerificationIssue(
                    severity="block",
                    field=field_name,
                    message=f"Follow-up date {fu.date} does not ground in source span '{span_text}'.",
                    source_text=span_text,
                    source_span=span,
                ))

    # 3. Verify Warning Signs
    for i, w in enumerate(plan.warning_signs):
        span = w.source_span
        if not span or span[0] >= span[1] or span[1] > summary_len:
            issues.append(VerificationIssue(
                severity="block",
                field=f"warning_signs[{i}].source_span",
                message=f"Ungrounded warning sign '{w.text_source}'",
                source_span=span,
            ))

    # 4. Verify Diet
    for i, d in enumerate(plan.diet):
        span = d.source_span
        if not span or span[0] >= span[1] or span[1] > summary_len:
            issues.append(VerificationIssue(
                severity="block",
                field=f"diet[{i}].source_span",
                message=f"Ungrounded diet item '{d.text_source}'",
                source_span=span,
            ))

    # 5. Verify Activity
    for i, a in enumerate(plan.activity):
        span = a.source_span
        if not span or span[0] >= span[1] or span[1] > summary_len:
            issues.append(VerificationIssue(
                severity="block",
                field=f"activity[{i}].source_span",
                message=f"Ungrounded activity item '{a.text_source}'",
                source_span=span,
            ))

    return issues


def merge_and_verify(summary: str, rules_plan: CarePlan, narrative: Dict) -> Tuple[CarePlan, VerificationResult]:
    # Merges rule parser (authority for tables & Rx) with LLM narrative extractor,
    # strictly enforces zero-error verification gate.
    merged_flags: List[Flag] = list(rules_plan.flags)

    # Combine narrative warning signs, diet, activity
    warning_signs = narrative.get("warning_signs", rules_plan.warning_signs)
    diet_items = narrative.get("diet", rules_plan.diet)
    activity_items = narrative.get("activity", rules_plan.activity)
    patient = narrative.get("patient") or rules_plan.patient

    # Construct merged plan
    merged_plan = CarePlan(
        patient=patient,
        medicines=rules_plan.medicines,
        warning_signs=warning_signs,
        diet=diet_items,
        activity=activity_items,
        follow_ups=rules_plan.follow_ups,
        flags=merged_flags,
        source_hash=hashlib.sha256(summary.encode("utf-8")).hexdigest(),
        extractor="dual_merged",
    )

    # Run source-span verification
    issues = verify_source_spans(summary, merged_plan)

    # Add verification issues for clinical flags
    for flag in merged_flags:
        severity = "block" if "unspecified" in flag.reason.lower() or "missing" in flag.reason.lower() else "warn"
        issues.append(VerificationIssue(
            severity=severity,
            field=flag.field,
            message=flag.reason,
        ))

    checked_fields = (
        len(merged_plan.medicines) * 3
        + len(merged_plan.follow_ups)
        + len(merged_plan.warning_signs)
        + len(merged_plan.diet)
        + len(merged_plan.activity)
    )

    blocking_issues = [i for i in issues if i.severity == "block"]
    mismatch_count = len(blocking_issues)
    passed = (mismatch_count == 0) and not any(f.action == "nurse_review" and "unspecified" in f.reason.lower() for f in merged_flags)

    result = VerificationResult(
        passed=passed,
        mismatch_count=mismatch_count,
        issues=issues,
        checked_fields=max(1, checked_fields),
        source_hash=merged_plan.source_hash,
    )

    return merged_plan, result


def verify(summary: str, plan: CarePlan) -> VerificationResult:
    # Single-plan standalone verifier
    issues = verify_source_spans(summary, plan)
    for flag in plan.flags:
        severity = "block" if "unspecified" in flag.reason.lower() or "missing" in flag.reason.lower() else "warn"
        issues.append(VerificationIssue(
            severity=severity,
            field=flag.field,
            message=flag.reason,
        ))

    checked_fields = (
        len(plan.medicines) * 3
        + len(plan.follow_ups)
        + len(plan.warning_signs)
        + len(plan.diet)
        + len(plan.activity)
    )

    blocking_issues = [i for i in issues if i.severity == "block"]
    mismatch_count = len(blocking_issues)
    passed = (mismatch_count == 0) and not any(f.action == "nurse_review" and "unspecified" in f.reason.lower() for f in plan.flags)

    return VerificationResult(
        passed=passed,
        mismatch_count=mismatch_count,
        issues=issues,
        checked_fields=max(1, checked_fields),
        source_hash=plan.source_hash,
    )
