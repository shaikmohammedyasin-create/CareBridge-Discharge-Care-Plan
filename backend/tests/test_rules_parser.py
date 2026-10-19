# Tests for CareBridge Rule-based Extractor
# Step 1 Gate Verification on 20 sample summaries

import json
from pathlib import Path
import pytest

from app.rules_parser import parse_rules
from app.schema import CarePlan

SAMPLES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "samples" / "sample_20.json"


@pytest.fixture(scope="module")
def samples():
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_sample_dataset_exists(samples):
    assert len(samples) == 20, "Must have exactly 20 sample summaries for Step 1 gate"


@pytest.mark.parametrize("idx", range(20))
def test_gate_extract_medicines_and_dates_on_20_samples(samples, idx):
    sample = samples[idx]
    summary = sample["summary"]
    expected_meds = sample["expected_medicines"]
    expected_dates = sample["expected_dates"]

    plan: CarePlan = parse_rules(summary)

    # 1. Verify every extracted medicine carries a valid source span
    for med in plan.medicines:
        assert med.source_span is not None, f"Medicine {med.name_generic} missing source span"
        assert len(med.source_span) == 2, f"Invalid span length for {med.name_generic}"
        start, end = med.source_span
        assert 0 <= start < end <= len(summary), f"Out of bounds span for {med.name_generic}"
        span_text = summary[start:end]
        assert len(span_text.strip()) > 0, "Source span text must not be empty"

    # 2. Verify all expected medicines are captured with exact generic names, doses, and frequency
    extracted_meds_summary = [
        {
            "generic": m.name_generic.lower(),
            "dose": m.dose.lower().replace(" ", ""),
            "freq": m.frequency_code.upper(),
        }
        for m in plan.medicines
    ]

    for exp in expected_meds:
        exp_generic = exp["name_generic"].lower()
        exp_dose = exp["dose"].lower().replace(" ", "")
        exp_freq = exp["frequency_code"].upper()

        found = any(
            m["generic"] == exp_generic and m["dose"] == exp_dose and m["freq"] == exp_freq
            for m in extracted_meds_summary
        )
        assert found, f"Sample #{sample['id']} missing expected medicine: {exp}. Extracted: {extracted_meds_summary}"

    # 3. Verify all expected follow-up dates are extracted
    extracted_dates = [f.date for f in plan.follow_ups]
    for exp_date in expected_dates:
        assert exp_date in extracted_dates, f"Sample #{sample['id']} missing expected date {exp_date}. Extracted: {extracted_dates}"
        # Also check span of follow up
        matching_fu = next(f for f in plan.follow_ups if f.date == exp_date)
        start, end = matching_fu.source_span
        assert 0 <= start < end <= len(summary)


def test_rule3_never_guess_missing_frequency():
    # Non-negotiable Rule 3: Missing frequency must NEVER be guessed as OD
    text = "Tab Amlodipine 5 mg x 30 days"
    plan = parse_rules(text)
    assert len(plan.medicines) == 1
    med = plan.medicines[0]
    assert med.frequency_code == "UNSPECIFIED"
    assert any("frequency" in flag.field for flag in plan.flags)


def test_od_eyedrop_ambiguity_flagged():
    # PRD 9.2: OD with eye drops must be flagged for nurse review
    text = "Eye Drops Ciprofloxacin 0.3% OD"
    plan = parse_rules(text)
    assert any("right eye" in flag.reason.lower() or "od" in flag.reason.lower() for flag in plan.flags)


def test_table_parsing_with_spans():
    table_text = """Discharge Summary
Medication Table:
| Drug | Dose | Frequency | Timing | Duration |
| Tab Metformin | 500 mg | BD | after food | 30 days |
| Tab Amlodipine | 5 mg | OD | after food | 30 days |
Review: OPD 26/10/2026
"""
    plan = parse_rules(table_text)
    assert len(plan.medicines) == 2
    assert plan.medicines[0].name_generic == "Metformin"
    assert plan.medicines[0].dose == "500 mg"
    assert plan.medicines[0].frequency_code == "BD"
    assert plan.medicines[1].name_generic == "Amlodipine"
    assert len(plan.follow_ups) == 1
    assert plan.follow_ups[0].date == "2026-10-26"
