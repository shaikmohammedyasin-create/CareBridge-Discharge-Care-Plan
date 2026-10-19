# Tests for CareBridge Fridge Sheet PDF Builder
# Step 5 Gate Verification

from pathlib import Path
import pytest

from app.fridge_sheet import build_fridge_sheet_pdf
from app.rules_parser import parse_rules

TEST_SUMMARY = """DISCHARGE SUMMARY
Patient Name: Ramesh Kumar Age: 52
Diagnosis: Type 2 Diabetes Mellitus
Rx:
Tab Metformin 500 mg BD pc x 30 days
Tab Glimepiride 1 mg OD ac x 30 days
Follow-up: Review in Endocrine OPD on 26/10/2026
Warning signs: severe dizziness, sweating
Diet: diabetic diet
Activity: regular morning walking
"""


def test_gate_step5_fridge_sheet_pdf_validity():
    plan = parse_rules(TEST_SUMMARY)
    pdf_bytes = build_fridge_sheet_pdf(plan, lang="both")

    # 1. Must be non-empty bytes
    assert len(pdf_bytes) > 5000, "PDF bytes must be generated and non-trivial"

    # 2. Must start with standard PDF signature
    assert pdf_bytes.startswith(b"%PDF"), "Output must be a valid PDF binary file"

    # 3. Must contain trailer EOF marker
    assert b"%%EOF" in pdf_bytes[-1024:], "PDF must contain valid EOF marker"


def test_fridge_sheet_with_different_languages():
    plan = parse_rules(TEST_SUMMARY)
    pdf_en = build_fridge_sheet_pdf(plan, lang="en")
    pdf_te = build_fridge_sheet_pdf(plan, lang="te")

    assert pdf_en.startswith(b"%PDF")
    assert pdf_te.startswith(b"%PDF")
