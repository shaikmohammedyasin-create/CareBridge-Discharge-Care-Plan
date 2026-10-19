# Tests for CareBridge Verifier and Dual Extractor
# Step 2 Gate Verification on 50 gold summaries

import json
from pathlib import Path
import pytest

from app.ingest import ingest
from app.llm_extractor import extract_narrative
from app.rules_parser import parse_rules
from app.verifier import merge_and_verify, verify

GOLD_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "samples" / "gold_50.json"


@pytest.fixture(scope="module")
def gold_summaries():
    with open(GOLD_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_gold_dataset_exists(gold_summaries):
    assert len(gold_summaries) == 50, "Step 2 requires exactly 50 gold clinical summaries"


@pytest.mark.parametrize("idx", range(50))
def test_gate_step2_merged_schema_passes_source_span_on_50_summaries(gold_summaries, idx):
    item = gold_summaries[idx]
    summary = item["summary"]

    # 1. Ingest
    ingest_res = ingest(summary)
    assert ingest_res.source_hash is not None

    # 2. Rule-based extraction (authority for dosage tables and Rx)
    rules_plan = parse_rules(summary)
    assert len(rules_plan.medicines) == item["expected_med_count"]

    # 3. LLM / narrative extraction
    narrative = extract_narrative(summary)

    # 4. Merge and verify
    merged_plan, result = merge_and_verify(summary, rules_plan, narrative)

    # Gate check: Must pass with 0 mismatches
    assert result.passed is True, f"Summary #{item['id']} ({item['category']}) failed verification: {result.issues}"
    assert result.mismatch_count == 0, f"Summary #{item['id']} had {result.mismatch_count} mismatches"
    assert result.checked_fields >= item["expected_med_count"] * 3

    # Every medicine must have verified source span in summary
    for med in merged_plan.medicines:
        s, e = med.source_span
        span_text = summary[s:e]
        assert med.dose.lower().replace(" ", "") in span_text.lower().replace(" ", "")

    # Follow up date must ground in summary
    assert len(merged_plan.follow_ups) >= 1
    for fu in merged_plan.follow_ups:
        s, e = fu.source_span
        span_text = summary[s:e]
        assert len(span_text) > 0


def test_verifier_blocks_tampered_dose(gold_summaries):
    # Rule 2: An altered dose must never pass verification
    summary = gold_summaries[0]["summary"]
    rules_plan = parse_rules(summary)
    narrative = extract_narrative(summary)
    merged_plan, _ = merge_and_verify(summary, rules_plan, narrative)

    # Tamper dose: change 500 mg to 1000 mg
    merged_plan.medicines[0].dose = "1000 mg"
    result = verify(summary, merged_plan)
    assert result.passed is False
    assert result.mismatch_count >= 1
    assert any("dose" in i.field.lower() for i in result.issues)


def test_verifier_blocks_invented_medicine(gold_summaries):
    # Rule 2 & 5: An invented medicine without source span must be blocked
    summary = gold_summaries[0]["summary"]
    rules_plan = parse_rules(summary)
    narrative = extract_narrative(summary)
    merged_plan, _ = merge_and_verify(summary, rules_plan, narrative)

    # Modify span to out-of-bounds or mismatch
    merged_plan.medicines[0].source_span = [9999, 10005]
    result = verify(summary, merged_plan)
    assert result.passed is False
    assert any("source_span" in i.field.lower() for i in result.issues)


def test_extractor_disagreement_becomes_nurse_flag(gold_summaries):
    # Extractor disagreement or ambiguous short form must become a flag
    summary = gold_summaries[0]["summary"]
    rules_plan = parse_rules(summary)
    narrative = extract_narrative(summary)
    # Inject disagreement in rules plan
    from app.schema import Flag
    rules_plan.flags.append(Flag(
        field="medicines[0].frequency",
        reason="Extractor disagreement: rule parser found BD, narrative claims TDS",
        action="nurse_review"
    ))
    merged_plan, result = merge_and_verify(summary, rules_plan, narrative)
    assert any("extractor disagreement" in i.message.lower() for i in result.issues)
