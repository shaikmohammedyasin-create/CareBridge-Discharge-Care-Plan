# CareBridge English Template Renderer
# Implements PRD Section 6, 7 (Component 4), 13.1, and Non-Negotiable Rules 1, 4

from typing import List, Tuple

from .glossary import get_phrase
from .schema import CarePlan


def render_english(plan: CarePlan) -> Tuple[str, List[str]]:
    # Renders care plan into plain English following PRD Section 13.1 fixed section order.
    # Returns (rendered_text, protected_tokens).
    sections: List[str] = []
    protected_tokens: List[str] = []

    # Title header
    sections.append("CARE PLAN")
    if plan.patient and plan.patient.name:
        age_str = f", Age {plan.patient.age}" if plan.patient.age else ""
        sections.append(f"Patient: {plan.patient.name}{age_str}")
    sections.append("")

    # Section 1: YOUR MEDICINES
    sections.append("1. YOUR MEDICINES")
    if plan.medicines:
        for med in plan.medicines:
            # Protected tokens: exact drug name, dose, frequency, duration
            protected_tokens.extend([med.name_generic, med.dose])
            timing_str = f", {med.timing}" if med.timing else ""
            duration_str = f", for {med.duration}" if med.duration else ""
            line = f"- {med.name_generic} {med.dose}: take {med.frequency_plain}{timing_str}{duration_str}."
            sections.append(line)
    else:
        sections.append("- No discharge medicines prescribed.")
    sections.append("")

    # Section 2: GO TO THE HOSPITAL AT ONCE IF
    if plan.warning_signs:
        sections.append("2. GO TO THE HOSPITAL AT ONCE IF")
        for w in plan.warning_signs:
            line = f"- Seek emergency medical help if you experience {w.text_source}."
            sections.append(line)
        sections.append("")

    # Section 3: WHAT TO EAT AND AVOID
    if plan.diet:
        sections.append("3. WHAT TO EAT AND AVOID")
        for d in plan.diet:
            clean = d.text_source.strip().rstrip(".")
            sections.append(f"- {clean}.")
        sections.append("")

    # Section 4: ACTIVITY AND REST
    if plan.activity:
        sections.append("4. ACTIVITY AND REST")
        for a in plan.activity:
            clean = a.text_source.strip().rstrip(".")
            sections.append(f"- {clean}.")
        sections.append("")

    # Section 5: YOUR NEXT VISITS
    if plan.follow_ups:
        sections.append("5. YOUR NEXT VISITS")
        for f in plan.follow_ups:
            protected_tokens.append(f.date)
            dept = f.department or "the outpatient clinic (OPD)"
            purpose = f.purpose or "clinical checkup"
            sections.append(f"- Visit {dept} on {f.date} for {purpose}.")
        sections.append("")

    english_text = "\n".join(sections).strip()
    return english_text, protected_tokens
