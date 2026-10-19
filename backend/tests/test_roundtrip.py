# Tests for CareBridge English Renderer & Roundtrip Verification
# Step 3 Gate Verification on 50 gold summaries

import json
from pathlib import Path
import pytest

from app.llm_extractor import extract_narrative
from app.readability import flesch_kincaid_grade
from app.render_en import render_english
from app.roundtrip import verify_english_roundtrip
from app.rules_parser import parse_rules
from app.verifier import merge_and_verify

GOLD_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "samples" / "gold_50.json"


@pytest.fixture(scope="module")
def gold_summaries():
    with open(GOLD_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("idx", range(50))
def test_gate_step3_zero_hard_errors_and_class_8_readability(gold_summaries, idx):
    item = gold_summaries[idx]
    summary = item["summary"]

    # 1. Parse and verify
    rules_plan = parse_rules(summary)
    narrative = extract_narrative(summary)
    merged_plan, verif_result = merge_and_verify(summary, rules_plan, narrative)
    assert verif_result.passed is True

    # 2. Render English care plan
    english_text, protected_tokens = render_english(merged_plan)
    assert len(english_text) > 0
    assert len(protected_tokens) > 0

    # 3. Round-trip verification: Re-extract and diff against source
    rt_result = verify_english_roundtrip(english_text, merged_plan)
    assert rt_result.passed is True, f"Summary #{item['id']} failed English roundtrip: {rt_result.issues}"
    assert rt_result.mismatch_count == 0, f"Summary #{item['id']} had {rt_result.mismatch_count} hard errors"

    # 4. Readability score evaluation (Target: Class 8 or below)
    grade = flesch_kincaid_grade(english_text)
    assert grade <= 8.0, f"Summary #{item['id']} reading grade {grade} exceeds Class 8 target"


def test_roundtrip_blocks_tampered_medicine(gold_summaries):
    # If English text has an altered medicine name, round-trip must block
    summary = gold_summaries[0]["summary"]
    rules_plan = parse_rules(summary)
    narrative = extract_narrative(summary)
    merged_plan, _ = merge_and_verify(summary, rules_plan, narrative)

    english_text, _ = render_english(merged_plan)
    # Alter medicine name in output text
    tampered_text = english_text.replace("Metformin", "Ibuprofen")

    rt_result = verify_english_roundtrip(tampered_text, merged_plan)
    assert rt_result.passed is False
    assert rt_result.mismatch_count >= 1
    assert any("metformin" in i.message.lower() for i in rt_result.issues)


def test_roundtrip_blocks_altered_dose(gold_summaries):
    # If English text has an altered dose, round-trip must block
    summary = gold_summaries[0]["summary"]
    rules_plan = parse_rules(summary)
    narrative = extract_narrative(summary)
    merged_plan, _ = merge_and_verify(summary, rules_plan, narrative)

    english_text, _ = render_english(merged_plan)
    tampered_text = english_text.replace("500 mg", "1000 mg")

    rt_result = verify_english_roundtrip(tampered_text, merged_plan)
    assert rt_result.passed is False
    assert any("dose" in i.field.lower() for i in rt_result.issues)


def test_roundtrip_blocks_altered_date(gold_summaries):
    # If English text has an altered date, round-trip must block
    summary = gold_summaries[0]["summary"]
    rules_plan = parse_rules(summary)
    narrative = extract_narrative(summary)
    merged_plan, _ = merge_and_verify(summary, rules_plan, narrative)

    english_text, _ = render_english(merged_plan)
    tampered_text = english_text.replace("2026-10-26", "2026-11-01")

    rt_result = verify_english_roundtrip(tampered_text, merged_plan)
    assert rt_result.passed is False
    assert any("follow_ups" in i.field.lower() for i in rt_result.issues)
