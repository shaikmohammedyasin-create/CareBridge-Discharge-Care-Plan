# CareBridge Controlled Telugu Template Renderer
# Implements PRD Section 6, 7 (Component 4), Section 12, and Non-Negotiable Rules 1, 4, 10

import re
from typing import List, Tuple

from .glossary import (
    expand_frequency,
    expand_timing,
    get_phrase,
    transliterate_drug,
)
from .schema import CarePlan


def _match_phrase_library(text: str, section: str) -> Tuple[str, bool]:
    # Matches clinical narrative against reviewed phrase library.
    # Returns (telugu_phrase, is_fallback_needed).
    clean = text.lower().strip()
    # Check exact match in phrase library
    from .glossary import _PHRASES_TE
    library = _PHRASES_TE.get(section, {})
    for k, v in library.items():
        if k in clean or clean in k:
            return (v, False)

    # Fallback for rare free-text lines:
    # Preserves protected English text with explicit clinical notice, flagged for nurse review
    return (f"{text} (ప్రత్యేక గమనిక: వైద్య సిబ్బంది ధృవీకరించాలి)", True)


def render_telugu(plan: CarePlan) -> Tuple[str, List[str], bool]:
    # Renders care plan into Telugu using locked templates and protected tokens.
    # Returns (rendered_text, protected_tokens, needs_review).
    sections: List[str] = []
    protected_tokens: List[str] = []
    needs_review = False

    # Title header
    sections.append("సంరక్షణ ప్రణాళిక (CARE PLAN)")
    if plan.patient and plan.patient.name:
        age_str = f", వయస్సు: {plan.patient.age}" if plan.patient.age else ""
        sections.append(f"రోగి వివరాలు: {plan.patient.name}{age_str}")
    sections.append("")

    # Section 1: YOUR MEDICINES
    sections.append("1. మీరు వాడవలసిన మందులు (YOUR MEDICINES)")
    if plan.medicines:
        for med in plan.medicines:
            # Protected tokens: exact English drug name, dose, duration
            protected_tokens.extend([med.name_generic, med.dose])

            # Transliteration for local readability
            te_name = transliterate_drug(med.name_generic)
            # Both generic English and Telugu script are presented so tokens remain verifiable
            name_label = f"{med.name_generic} ({te_name})" if te_name != med.name_generic else med.name_generic

            # Frequency in Telugu
            _, _, freq_te, is_amb, _ = expand_frequency(med.frequency_code)
            if is_amb:
                needs_review = True

            # Timing in Telugu
            _, timing_te = expand_timing(med.timing or "")
            timing_str = f", {timing_te}" if timing_te else ""

            # Duration in Telugu (numbers preserved as digits)
            dur_str = ""
            if med.duration:
                protected_tokens.append(med.duration)
                m = re.search(r"\d+", med.duration)
                if m:
                    dur_str = f", {m.group(0)} రోజుల పాటు"
                else:
                    dur_str = f", {med.duration}"

            line = f"- {name_label} {med.dose}: {freq_te}{timing_str}{dur_str}."
            sections.append(line)
    else:
        sections.append("- డిశ్చార్జ్ మందులు లేవు.")
    sections.append("")

    # Section 2: WARNING SIGNS
    if plan.warning_signs:
        sections.append("2. ఈ క్రింది లక్షణాలు కనిపిస్తే వెంటనే ఆసుపత్రికి వెళ్ళండి (EMERGENCY)")
        for w in plan.warning_signs:
            phrase, is_fallback = _match_phrase_library(w.text_source, "common_warnings")
            if is_fallback:
                needs_review = True
            line = f"- {phrase} ఉంటే వెంటనే ఆసుపత్రికి రండి."
            sections.append(line)
        sections.append("")

    # Section 3: DIET
    if plan.diet:
        sections.append("3. ఆహార నియమాలు (DIET)")
        for d in plan.diet:
            phrase, is_fallback = _match_phrase_library(d.text_source, "common_diet")
            if is_fallback:
                needs_review = True
            sections.append(f"- {phrase}.")
        sections.append("")

    # Section 4: ACTIVITY
    if plan.activity:
        sections.append("4. విశ్రాంతి మరియు వ్యాయామం (ACTIVITY)")
        for a in plan.activity:
            phrase, is_fallback = _match_phrase_library(a.text_source, "common_activity")
            if is_fallback:
                needs_review = True
            sections.append(f"- {phrase}.")
        sections.append("")

    # Section 5: FOLLOW-UP
    if plan.follow_ups:
        sections.append("5. తదుపరి సందర్శన (NEXT VISITS)")
        for f in plan.follow_ups:
            protected_tokens.append(f.date)
            dept = f.department or "OPD"
            sections.append(f"- {f.date} నాడు {dept} విభాగంలో వైద్యులను తప్పనిసరిగా కలవండి.")
        sections.append("")

    telugu_text = "\n".join(sections).strip()
    return telugu_text, protected_tokens, needs_review
