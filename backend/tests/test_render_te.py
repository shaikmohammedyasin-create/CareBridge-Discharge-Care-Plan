# Tests for CareBridge Telugu Renderer & Telugu Round-trip Verification
# Step 4 Gate Verification on 50 gold summaries

import json
from pathlib import Path
import pytest

from app.llm_extractor import extract_narrative
from app.render_te import render_telugu
from app.roundtrip import verify_telugu_roundtrip
from app.rules_parser import parse_rules
from app.schema import DietItem
from app.verifier import merge_and_verify

GOLD_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "samples" / "gold_50.json"


@pytest.fixture(scope="module")
def gold_summaries():
    with open(GOLD_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("idx", range(50))
def test_gate_step4_telugu_passes_same_diff_on_50_summaries(gold_summaries, idx):
    item = gold_summaries[idx]
    summary = item["summary"]

    # 1. Parse and verify source plan
    rules_plan = parse_rules(summary)
    narrative = extract_narrative(summary)
    merged_plan, verif_result = merge_and_verify(summary, rules_plan, narrative)
    assert verif_result.passed is True

    # 2. Render Telugu care plan
    telugu_text, protected_tokens, needs_review = render_telugu(merged_plan)
    assert len(telugu_text) > 0
    assert len(protected_tokens) > 0

    # 3. Telugu Round-trip diff check
    rt_result = verify_telugu_roundtrip(telugu_text, merged_plan)
    assert rt_result.passed is True, f"Summary #{item['id']} failed Telugu roundtrip: {rt_result.issues}"
    assert rt_result.mismatch_count == 0, f"Summary #{item['id']} had {rt_result.mismatch_count} hard errors"

    # 4. Verify every protected token appears where expected
    for med in merged_plan.medicines:
        # Exact dose must appear in Telugu output
        assert med.dose in telugu_text, f"Protected dose {med.dose} missing from Telugu text"

    for fu in merged_plan.follow_ups:
        # Exact date must appear in Telugu output
        assert fu.date in telugu_text, f"Protected date {fu.date} missing from Telugu text"


def test_rare_free_text_marks_needs_review(gold_summaries):
    # PRD 12: Rare free text lines use the fallback and are marked needs_review
    summary = gold_summaries[0]["summary"]
    rules_plan = parse_rules(summary)
    narrative = extract_narrative(summary)
    merged_plan, _ = merge_and_verify(summary, rules_plan, narrative)

    # Add a completely novel/rare clinical instruction
    merged_plan.diet.append(DietItem(
        id="D_RARE",
        text_source="Custom bespoke ketogenic lipid emulsion formula 400ml",
        source_span=[0, 10]
    ))

    telugu_text, _, needs_review = render_telugu(merged_plan)
    assert needs_review is True
    assert "ప్రత్యేక గమనిక" in telugu_text


def test_telugu_roundtrip_blocks_altered_dose(gold_summaries):
    # Altered dose in Telugu must trigger hard error
    summary = gold_summaries[0]["summary"]
    rules_plan = parse_rules(summary)
    narrative = extract_narrative(summary)
    merged_plan, _ = merge_and_verify(summary, rules_plan, narrative)

    telugu_text, _, _ = render_telugu(merged_plan)
    tampered_text = telugu_text.replace("500 mg", "1000 mg")

    rt_result = verify_telugu_roundtrip(tampered_text, merged_plan)
    assert rt_result.passed is False
    assert any("dose" in i.field.lower() for i in rt_result.issues)


def test_telugu_roundtrip_blocks_altered_date(gold_summaries):
    # Altered follow-up date in Telugu must trigger hard error
    summary = gold_summaries[0]["summary"]
    rules_plan = parse_rules(summary)
    narrative = extract_narrative(summary)
    merged_plan, _ = merge_and_verify(summary, rules_plan, narrative)

    telugu_text, _, _ = render_telugu(merged_plan)
    tampered_text = telugu_text.replace("2026-10-26", "2026-12-25")

    rt_result = verify_telugu_roundtrip(tampered_text, merged_plan)
    assert rt_result.passed is False
    assert any("follow_ups" in i.field.lower() for i in rt_result.issues)
