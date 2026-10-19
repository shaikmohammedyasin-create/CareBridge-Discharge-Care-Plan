# CareBridge Rule-based Clinical Information Extractor
# Implements PRD Section 6, 7 (Component 2a), 9.1, and 14

import hashlib
import re
from datetime import datetime
from typing import List, Optional, Tuple

from .glossary import expand_frequency, expand_timing, resolve_drug
from .schema import (
    ActivityItem,
    CarePlan,
    DietItem,
    Flag,
    FollowUp,
    Medicine,
    Patient,
    WarningSign,
)

# Regex patterns for clinical elements
DOSE_PATTERN = r"(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?|iu|puffs?|drops?|tablets?|capsules?|%))"
FREQ_PATTERN = r"\b(OD|QD|BD|BID|TDS|TID|QID|Q4H|Q6H|Q8H|HS|SOS|PRN|STAT|once daily|twice daily|thrice daily)\b"
TIMING_PATTERN = r"\b(pc|ac|after food|before food|with food|at bedtime|empty stomach|post meals?|pre meals?|inhalation|topical|oral|subcutaneous|when needed)\b"
DURATION_PATTERN = r"(?:(?:x|for)\s*)?(\d+)\s*(days?|weeks?|months?)\b"

# Matches linear prescription lines: e.g. "Tab Metformin 500 mg BD pc x 30 days"
LINEAR_MED_RE = re.compile(
    r"(?:^|\n)\s*(?:[-*•\d\.]+\s*)?"
    r"((?:Tab|Tablet|Cap|Capsule|Inj|Injection|Syp|Syrup|Susp|Eye Drops|Drops|Inhaler|Oint)?\s*[A-Z][A-Za-z0-9\-]*(?:\s+[A-Za-z0-9\-]+)?)\s+"
    + DOSE_PATTERN
    + r"(?:\s+"
    + FREQ_PATTERN
    + r")?"
    + r"(?:\s+"
    + TIMING_PATTERN
    + r")?"
    + r"(?:[^\n\d]*?"
    + DURATION_PATTERN
    + r")?",
    re.IGNORECASE,
)

# Date formats: 26/10/2026, 26-10-2026, 2026-10-26, 26 Oct 2026, 26th October 2026
DATE_RE = re.compile(
    r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b|"
    r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b|"
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{2,4})\b",
    re.IGNORECASE,
)


def _normalize_date_match(match: re.Match) -> Optional[str]:
    # Normalizes extracted date match into ISO YYYY-MM-DD
    g = match.groups()
    if g[0] and g[1] and g[2]:
        # DD/MM/YYYY or DD-MM-YYYY
        d, m, y = int(g[0]), int(g[1]), int(g[2])
        if y < 100:
            y += 2000
        try:
            return f"{y:04d}-{m:02d}-{d:02d}"
        except ValueError:
            return None
    elif g[3] and g[4] and g[5]:
        # YYYY-MM-DD
        y, m, d = int(g[3]), int(g[4]), int(g[5])
        return f"{y:04d}-{m:02d}-{d:02d}"
    elif g[6] and g[7] and g[8]:
        # 26 Oct 2026
        d = int(g[6])
        mon_str = g[7][:3].title()
        y = int(g[8])
        if y < 100:
            y += 2000
        months = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
        }
        m = months.get(mon_str, 1)
        return f"{y:04d}-{m:02d}-{d:02d}"
    return None


def _parse_table_rows(summary: str) -> List[Tuple[dict, list]]:
    # Detects Markdown or pipe-delimited dosage tables
    meds = []
    lines = summary.splitlines()
    offset = 0
    in_table = False
    headers = []

    for line in lines:
        line_start = offset
        line_end = offset + len(line)
        offset += len(line) + 1  # newline account

        clean = line.strip()
        if not clean:
            in_table = False
            continue

        if "|" in clean:
            cells = [c.strip() for c in clean.split("|")[1:-1]]
            if not cells:
                continue
            lower_cells = [c.lower() for c in cells]
            # Check for header row
            if any("med" in c or "drug" in c for c in lower_cells) and any("dose" in c for c in lower_cells):
                headers = lower_cells
                in_table = True
                continue
            if in_table and all(set(c) <= {"-", ":", " "} for c in cells):
                # separator row
                continue
            if in_table and len(cells) >= 2:
                # Table row data
                name, dose, freq, timing, duration = None, None, None, None, None
                for i, h in enumerate(headers):
                    if i >= len(cells):
                        break
                    val = cells[i]
                    if "med" in h or "drug" in h:
                        name = val
                    elif "dose" in h:
                        dose = val
                    elif "freq" in h:
                        freq = val
                    elif "time" in h or "instruction" in h:
                        timing = val
                    elif "dur" in h or "day" in h:
                        duration = val

                if name and dose:
                    meds.append(({
                        "name": name,
                        "dose": dose,
                        "freq": freq,
                        "timing": timing,
                        "duration": duration,
                    }, [line_start, line_end]))
    return meds


def parse_rules(summary: str) -> CarePlan:
    # Extracts care-plan elements deterministically with strict source spans
    clean_summary = summary.strip()
    source_hash = hashlib.sha256(summary.encode("utf-8")).hexdigest()

    medications: List[Medicine] = []
    flags: List[Flag] = []
    med_id_counter = 1

    # 1. Parse table-structured medications if present
    table_meds = _parse_table_rows(summary)
    consumed_spans = []

    for item, span in table_meds:
        raw_name = item["name"]
        generic_name, form, route, _ = resolve_drug(raw_name)
        freq_code = item["freq"] or "UNSPECIFIED"
        code, p_en, _, is_amb, note = expand_frequency(freq_code)

        timing_en, _ = expand_timing(item.get("timing") or "")
        dur = item.get("duration")

        if is_amb:
            flags.append(Flag(
                field=f"medicines[{med_id_counter-1}].frequency",
                reason=note or f"Ambiguous frequency '{freq_code}'",
                action="nurse_review",
            ))

        medications.append(Medicine(
            id=f"M{med_id_counter}",
            name_generic=generic_name,
            name_as_written=raw_name,
            form=form,
            dose=item["dose"],
            frequency_code=code,
            frequency_plain=p_en,
            timing=timing_en or (item.get("timing") if item.get("timing") else None),
            duration=dur,
            route=route,
            needs_confirmation=is_amb,
            source_span=span,
        ))
        consumed_spans.append(span)
        med_id_counter += 1

    # 2. Parse linear prescription lines if not already captured in table
    for match in LINEAR_MED_RE.finditer(summary):
        span = [match.start(), match.end()]
        # Skip if within an already consumed table span
        if any(cs[0] <= span[0] and span[1] <= cs[1] for cs in consumed_spans):
            continue

        raw_name = match.group(1).strip()
        dose = match.group(2).strip()
        freq_token = match.group(3)
        timing_token = match.group(4)
        duration_num = match.group(5)
        duration_unit = match.group(6) if match.lastindex and match.lastindex >= 6 else "days"

        # Rule 3 check: Missing frequency is NEVER guessed as OD
        if not freq_token:
            code = "UNSPECIFIED"
            plain_freq = "as directed by doctor"
            flags.append(Flag(
                field=f"medicines[{med_id_counter-1}].frequency",
                reason=f"Missing frequency for medication '{raw_name}'",
                action="nurse_review",
            ))
        else:
            code, plain_freq, _, is_amb, note = expand_frequency(freq_token)
            if is_amb:
                flags.append(Flag(
                    field=f"medicines[{med_id_counter-1}].frequency",
                    reason=note or f"Ambiguous frequency code '{freq_token}'",
                    action="nurse_review",
                ))

        timing_en, _ = expand_timing(timing_token or "")
        generic_name, form, route, _ = resolve_drug(raw_name)

        # Eye drop / OD check: PRD 9.2 ambiguity rule
        if "drop" in raw_name.lower() and code == "OD":
            flags.append(Flag(
                field=f"medicines[{med_id_counter-1}].frequency",
                reason="OD used with drops can mean right eye (oculus dexter); requires nurse review",
                action="nurse_review",
            ))

        dur = f"{duration_num} {duration_unit}" if duration_num else None
        needs_conf = bool(not freq_token or is_amb or ("drop" in raw_name.lower() and code == "OD"))

        medications.append(Medicine(
            id=f"M{med_id_counter}",
            name_generic=generic_name,
            name_as_written=raw_name,
            form=form,
            dose=dose,
            frequency_code=code,
            frequency_plain=plain_freq,
            timing=timing_en or (timing_token.lower() if timing_token else None),
            duration=dur,
            route=route,
            needs_confirmation=needs_conf,
            source_span=span,
        ))
        consumed_spans.append(span)
        med_id_counter += 1

    # 3. Follow-up appointments
    follow_ups: List[FollowUp] = []
    fu_id_counter = 1
    # Look for follow-up section or date mention
    fu_section_match = re.search(r"(?:Follow[- ]?up|Review|Next Visit)[^\n:]*[:\-]?\s*([^\n]+)", summary, re.I)
    if fu_section_match:
        sec_text = fu_section_match.group(0)
        sec_start = fu_section_match.start()
        for dmatch in DATE_RE.finditer(sec_text):
            iso_date = _normalize_date_match(dmatch)
            if iso_date:
                span = [sec_start + dmatch.start(), sec_start + dmatch.end()]
                # Check for department mention
                dept = None
                if re.search(r"\bOPD\b", sec_text, re.I):
                    dept = "OPD"
                elif re.search(r"\bCardiology\b", sec_text, re.I):
                    dept = "Cardiology"
                elif re.search(r"\bEndocrine\b", sec_text, re.I):
                    dept = "Endocrinology"
                elif re.search(r"\bSurgical\b", sec_text, re.I):
                    dept = "Surgery"

                follow_ups.append(FollowUp(
                    id=f"F{fu_id_counter}",
                    department=dept or "OPD",
                    date=iso_date,
                    purpose="clinical review",
                    source_span=span,
                ))
                fu_id_counter += 1
    else:
        # Search anywhere for dates associated with review
        for match in re.finditer(r"(?:review|visit|opd|appointment)[^.\n]*", summary, re.I):
            sentence = match.group(0)
            base_idx = match.start()
            for dmatch in DATE_RE.finditer(sentence):
                iso_date = _normalize_date_match(dmatch)
                if iso_date:
                    span = [base_idx + dmatch.start(), base_idx + dmatch.end()]
                    follow_ups.append(FollowUp(
                        id=f"F{fu_id_counter}",
                        department="OPD",
                        date=iso_date,
                        purpose="review",
                        source_span=span,
                    ))
                    fu_id_counter += 1

    # 4. Warning signs
    warning_signs: List[WarningSign] = []
    w_counter = 1
    w_match = re.search(r"(?:Warning signs?|Red flags?|Emergency|Seek medical help if)\s*[:\-]\s*([^\n]+)", summary, re.I)
    if w_match:
        full_line = w_match.group(1)
        base = w_match.start(1)
        items = re.split(r"[,;]|\band\b", full_line)
        cur_offset = 0
        for item in items:
            clean = item.strip()
            if clean:
                pos = full_line.find(clean, cur_offset)
                if pos != -1:
                    span = [base + pos, base + pos + len(clean)]
                    cur_offset = pos + len(clean)
                else:
                    span = [w_match.start(), w_match.end()]
                warning_signs.append(WarningSign(
                    id=f"W{w_counter}",
                    text_source=clean,
                    severity="return_immediately",
                    source_span=span,
                ))
                w_counter += 1

    # 5. Diet
    diet_items: List[DietItem] = []
    d_counter = 1
    d_match = re.search(r"(?:Diet|Dietary advice|Nutrition)\s*[:\-]\s*([^\n]+)", summary, re.I)
    if d_match:
        full_line = d_match.group(1)
        base = d_match.start(1)
        items = re.split(r"[,;]|\band\b", full_line)
        cur_offset = 0
        for item in items:
            clean = item.strip()
            if clean:
                pos = full_line.find(clean, cur_offset)
                span = [base + pos, base + pos + len(clean)] if pos != -1 else [d_match.start(), d_match.end()]
                diet_items.append(DietItem(
                    id=f"D{d_counter}",
                    text_source=clean,
                    source_span=span,
                ))
                d_counter += 1

    # 6. Activity
    activity_items: List[ActivityItem] = []
    a_counter = 1
    a_match = re.search(r"(?:Activity|Exercise|Rest|Precautions)\s*[:\-]\s*([^\n]+)", summary, re.I)
    if a_match:
        full_line = a_match.group(1)
        base = a_match.start(1)
        items = re.split(r"[,;]|\band\b", full_line)
        cur_offset = 0
        for item in items:
            clean = item.strip()
            if clean:
                pos = full_line.find(clean, cur_offset)
                span = [base + pos, base + pos + len(clean)] if pos != -1 else [a_match.start(), a_match.end()]
                activity_items.append(ActivityItem(
                    id=f"A{a_counter}",
                    text_source=clean,
                    source_span=span,
                ))
                a_counter += 1

    # 7. Patient info if available
    patient = None
    p_match = re.search(r"(?:Patient Name|Name)\s*[:\-]\s*([A-Za-z\s]+)", summary, re.I)
    age_match = re.search(r"(?:Age)\s*[:\-]\s*(\d+)", summary, re.I)
    if p_match or age_match:
        p_name = p_match.group(1).strip() if p_match else None
        p_age = int(age_match.group(1)) if age_match else None
        patient = Patient(name=p_name, age=p_age, condition_group=None)

    return CarePlan(
        patient=patient,
        medicines=medications,
        warning_signs=warning_signs,
        diet=diet_items,
        activity=activity_items,
        follow_ups=follow_ups,
        flags=flags,
        source_hash=source_hash,
        extractor="rules_parser",
    )
