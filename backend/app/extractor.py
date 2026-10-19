import hashlib, re
from .glossary import expand_frequency
from .models import CarePlan, Medication, FollowUp

MED_RE = re.compile(
    r"(?:Tab|Tablet|Cap|Capsule)\s+([A-Za-z][A-Za-z0-9\-]*)\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml))"
    r"(?:\s+([A-Za-z]+))?"
    r"(?:\s+([A-Za-z]+))?"
    r"(?:\s+x\s*(\d+)\s*days?)?",
    re.I,
)
DATE_RE = re.compile(r"(?:Review|Follow[- ]?up|OPD)[^\d]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", re.I)

def normalize_date(raw: str) -> str:
    parts = re.split(r"[/-]", raw)
    d, m, y = parts
    if len(y) == 2:
        y = "20" + y
    return f"{y}-{int(m):02d}-{int(d):02d}"

def extract(summary: str) -> CarePlan:
    meds = []
    for m in MED_RE.finditer(summary):
        name, dose, freq_token, timing_token, days = m.groups()
        freq = expand_frequency(freq_token or "OD") or (freq_token or "unspecified")
        timing = expand_frequency(timing_token or "") if timing_token else None
        source = m.group(0)
        meds.append(Medication(
            name=name,
            dose=dose.replace(" ", " "),
            frequency=freq,
            timing=timing,
            duration=f"{days} days" if days else None,
            source_text=source,
            confidence=0.98 if freq_token else 0.72,
        ))

    followups = []
    for m in DATE_RE.finditer(summary):
        raw = m.group(1)
        followups.append(FollowUp(date=normalize_date(raw), source_text=m.group(0)))

    def section(name):
        match = re.search(rf"{name}\s*:\s*(.+)", summary, re.I)
        return [x.strip() for x in match.group(1).split(",")] if match else []

    ambiguities = []
    if re.search(r"\bOD\b", summary, re.I):
        ambiguities.append("OD can be ambiguous in some clinical contexts; verify against local protocol.")
    if re.search(r"\bSOS\b", summary, re.I):
        ambiguities.append("SOS means when needed; exact indication may require nurse review.")

    return CarePlan(
        medications=meds,
        warning_signs=section("Warning signs"),
        diet=section("Diet"),
        activity=section("Activity"),
        follow_ups=followups,
        ambiguities=ambiguities,
        source_hash=hashlib.sha256(summary.encode()).hexdigest(),
    )
