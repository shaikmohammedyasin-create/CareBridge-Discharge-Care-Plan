# CareBridge 7-Day Medication Timetable Generator
# Implements PRD Section 13.3 and FR-14 (Stretch Goal)

import re
from typing import Dict, List

from .schema import CarePlan, Medicine


def _parse_duration_days(duration_str: str | None) -> int:
    # Parses duration string into number of days (default 7 if unspecified)
    if not duration_str:
        return 7
    m = re.search(r"(\d+)\s*(days?|weeks?|months?)", duration_str, re.I)
    if not m:
        return 7
    qty = int(m.group(1))
    unit = m.group(2).lower()
    if "week" in unit:
        return qty * 7
    elif "month" in unit:
        return qty * 30
    return qty


def generate_7day_timetable(plan: CarePlan) -> Dict:
    # Generates a 7-day daily medication schedule based strictly on verified durations.
    days_schedule: List[Dict] = []

    for day_num in range(1, 8):
        day_meds = []
        for med in plan.medicines:
            dur_days = _parse_duration_days(med.duration)
            is_active = (day_num <= dur_days)

            day_meds.append({
                "medicine_id": med.id,
                "name": med.name_generic,
                "dose": med.dose,
                "frequency": med.frequency_code,
                "timing": med.timing or "after food",
                "active_today": is_active,
                "stop_flag": (day_num == dur_days),
                "status_note": f"Stop after Day {day_num}" if (day_num == dur_days) else ("Take as scheduled" if is_active else "Course finished")
            })

        days_schedule.append({
            "day": f"Day {day_num}",
            "day_number": day_num,
            "medicines": day_meds,
        })

    return {
        "title": "7-Day Home Medication Timetable",
        "total_days": 7,
        "schedule": days_schedule,
    }
