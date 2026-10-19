import re
from .models import CarePlan, RenderedPlan
from .glossary import telugu

def reading_grade(text: str) -> float:
    sentences = max(1, len(re.findall(r"[.!?]", text)))
    words = max(1, len(text.split()))
    syllables = sum(max(1, len(re.findall(r"[aeiouy]+", w.lower()))) for w in text.split())
    return round(0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59, 1)

def render(plan: CarePlan) -> RenderedPlan:
    en = ["CARE PLAN", "", "MEDICINES"]
    te = ["కేర్ ప్లాన్", "", "మందులు"]
    protected = []

    for m in plan.medications:
        protected += [m.name, m.dose]
        timing = f", {m.timing}" if m.timing else ""
        duration = f", for {m.duration}" if m.duration else ""
        en.append(f"{m.name} {m.dose}: take {m.frequency}{timing}{duration}.")
        freq_te = telugu(m.frequency)
        timing_te = telugu(m.timing) if m.timing else ""
        duration_te = ""
        if m.duration:
            n = re.search(r"\d+", m.duration)
            duration_te = f", {n.group(0)} {telugu('days')}" if n else ""
        en_line = f"{m.name} {m.dose}: {freq_te}{(' ' + timing_te) if timing_te else ''}{duration_te}."
        te.append(en_line)

    if plan.follow_ups:
        en += ["", "FOLLOW-UP"]
        te += ["", "తదుపరి సందర్శన"]
        for f in plan.follow_ups:
            en.append(f"Come for follow-up on {f.date}.")
            te.append(f"{f.date} నాడు ఫాలో-అప్‌కు రండి.")

    if plan.warning_signs:
        en += ["", "WARNING SIGNS"]
        te += ["", "హెచ్చరిక సంకేతాలు"]
        for x in plan.warning_signs:
            en.append(f"Seek medical help if {x}.")
            te.append(f"{x} ఉంటే వైద్య సహాయం పొందండి.")

    if plan.diet:
        en += ["", "DIET"]
        te += ["", "ఆహారం"]
        for x in plan.diet:
            en.append(x + ".")
            te.append(x + ".")

    english = "\n".join(en)
    telugu_text = "\n".join(te)
    return RenderedPlan(
        english=english,
        telugu=telugu_text,
        readability_grade=reading_grade(english),
        protected_tokens=protected,
    )
