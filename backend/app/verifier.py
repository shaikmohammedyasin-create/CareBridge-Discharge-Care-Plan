import re
from .models import CarePlan, VerificationResult, VerificationIssue

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()

def verify(source: str, plan: CarePlan) -> VerificationResult:
    src = norm(source)
    issues = []
    checked = 0

    for i, med in enumerate(plan.medications):
        fields = {
            f"medications[{i}].name": med.name,
            f"medications[{i}].dose": med.dose,
        }
        for field, value in fields.items():
            checked += 1
            if norm(value) not in src:
                # A medication name/dose can be represented with spacing differences,
                # so also check its original source span.
                if norm(value).replace(" ", "") not in src.replace(" ", ""):
                    issues.append(VerificationIssue(
                        severity="block",
                        field=field,
                        message=f"Value '{value}' was not found in the source.",
                        source_text=med.source_text,
                    ))

    for i, follow in enumerate(plan.follow_ups):
        checked += 1
        compact = follow.date.replace("-", "")
        source_digits = re.sub(r"\D", "", source)
        if compact not in source_digits:
            issues.append(VerificationIssue(
                severity="block",
                field=f"follow_ups[{i}].date",
                message=f"Follow-up date {follow.date} was not found in source.",
                source_text=follow.source_text,
            ))

    for ambiguity in plan.ambiguities:
        issues.append(VerificationIssue(
            severity="warn",
            field="ambiguity",
            message=ambiguity,
        ))

    return VerificationResult(
        passed=not any(x.severity == "block" for x in issues) and not plan.ambiguities,
        mismatch_count=sum(x.severity == "block" for x in issues),
        issues=issues,
        checked_fields=checked,
        source_hash=plan.source_hash,
    )
