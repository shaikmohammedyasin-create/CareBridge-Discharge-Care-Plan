from app.extractor import extract
from app.verifier import verify

SUMMARY = """Discharge Summary
Tab Metformin 500 mg BD pc x 30 days
Tab Amlodipine 5 mg OD x 30 days
Review OPD 26/10/2026
Warning signs: severe dizziness, chest pain
Diet: low salt diet
"""

def test_extract():
    plan = extract(SUMMARY)
    assert len(plan.medications) == 2
    assert plan.medications[0].name == "Metformin"
    assert plan.follow_ups[0].date == "2026-10-26"

def test_verify():
    plan = extract(SUMMARY)
    result = verify(SUMMARY, plan)
    assert result.checked_fields >= 4

def test_tampered_plan_is_detected():
    plan = extract(SUMMARY)
    plan.medications[0].dose = "1000 mg"
    result = verify(SUMMARY, plan)
    assert not result.passed
