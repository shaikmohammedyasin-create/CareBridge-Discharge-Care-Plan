from app.rules_parser import parse_rules
from app.verifier import verify

SUMMARY = """Discharge Summary
Tab Metformin 500 mg BD pc x 30 days
Tab Amlodipine 5 mg OD x 30 days
Review OPD 26/10/2026
Warning signs: severe dizziness, chest pain
Diet: low salt diet
"""

def test_extract():
    plan = parse_rules(SUMMARY)
    assert len(plan.medicines) == 2
    assert plan.medicines[0].name_generic == "Metformin"
    assert plan.follow_ups[0].date == "2026-10-26"

def test_verify():
    plan = parse_rules(SUMMARY)
    result = verify(SUMMARY, plan)
    assert result.checked_fields >= 4

def test_tampered_plan_is_detected():
    plan = parse_rules(SUMMARY)
    plan.medicines[0].dose = "1000 mg"
    result = verify(SUMMARY, plan)
    assert not result.passed

