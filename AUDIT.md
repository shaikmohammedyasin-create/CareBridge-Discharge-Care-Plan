# CareBridge Codebase Audit (Phase 0)

| Field | Value |
|---|---|
| Project | CareBridge: Discharge Summary to Patient-Understandable Care Plan |
| Hackathon | Talent AP Mega Hackathon, Problem H2 (Healthcare) |
| Team | BALLERINA |
| Team Leader | Mohammed Yasin Shaik |
| Date | 19 October 2026 |
| Audit Status | Complete — Ready for Phase 1 Build |

---

## 1. Missing Organizer Files

The following files specified in the competition problem were not present in the repository or working environment:
- **2,000 Discharge Summaries**: Missing.
- **Abbreviation Glossary**: Missing (`glossary.json`).
- **Drug Table**: Missing (`drug_table.csv`).
- **50 Gold Examples**: Missing (`gold_50.json`).
- **Organizer Harness**: Missing (`evaluate.py`).

**Remediation Plan**:
As directed by Section 0 of the instructions, we construct a clearly labelled synthetic sample collection in `data/samples/` and `backend/data/`:
- `data/samples/sample_20.json`: 20 clinically realistic discharge summaries with ground-truth medicines and dates for Step 1 parser gate.
- `data/samples/gold_50.json`: 50 comprehensive summaries across all 5 clinical groups (diabetes, post_op, cardiac, respiratory, maternity) with complete gold care-plans for Steps 2, 3, 4 gates.
- `data/samples/synthetic_2000.json`: 2,000 synthetic summaries for Step 6 full batch evaluation.
- `backend/data/glossary.json`: Clinical abbreviations with Telugu translations.
- `backend/data/drug_table.csv`: Top 100 Indian hospital formulations (Brand, Generic, Form, Telugu transliteration).
- `backend/data/phrases_en.json` & `backend/data/phrases_te.json`: Reviewed English & Telugu template phrase libraries.

*Note: In all reports and documentation, synthetic sample metrics are clearly labelled as sample/synthetic evaluations.*

---

## 2. Requirement Traceability Matrix (FR-1 to FR-17)

| Requirement ID | PRD Requirement Description | Status | Current File(s) | Gap Analysis & Defects Found |
|---|---|---|---|---|
| **FR-1** | Accept discharge summary as text or file; parse sections | **Partial** | `backend/app/main.py`, `backend/app/extractor.py` | Accepts raw text in `/api/generate` and textarea. Section splitting uses single-line regex (`section(name)`), unable to handle multiline clinical sections or file uploads. |
| **FR-2** | Expand short forms using glossary; flag unknown ones | **Partial** | `backend/app/glossary.py`, `backend/app/extractor.py` | Hardcoded 12-item Python dict in `glossary.py`. Does not load from `glossary.json`. Defaults missing frequencies to "OD" (violates Rule 3). Does not flag unexpanded short forms. |
| **FR-3** | Resolve brand names to generic names using drug table | **Missing** | *None* | No drug table exists (`backend/data/drug_table.csv`). Brand names are left unresolved. |
| **FR-4** | Extract medicines (name, dose, frequency, timing, duration) | **Partial** | `backend/app/extractor.py`, `backend/app/models.py` | Basic single-line regex for Tab/Cap. Missing route, form, frequency_code, frequency_plain, and special instructions. Cannot parse dosage tables. |
| **FR-5** | Extract warning signs, diet, activity, follow-up appointments | **Partial** | `backend/app/extractor.py` | Extracted as unstructured comma-separated strings. Follow-up regex extracts single date but ignores department and purpose. |
| **FR-6** | Every extracted item carries a source span (`[start, end]`) | **Broken / Missing** | `backend/app/models.py`, `backend/app/extractor.py` | `Medication` only stores `source_text` string, NO character offset span `[start, end]`. Warning signs, diet, activity have zero source spans. Direct violation of Non-Negotiable Rule 5 ("No span, no item"). |
| **FR-7** | Render English care plan from reviewed templates (Class 8) | **Partial** | `backend/app/renderer.py` | Inlines hardcoded template strings. Does not enforce Class 8 reading level rules or separate English rendering from Telugu. |
| **FR-8** | Render Telugu care plan with protected tokens | **Broken** | `backend/app/renderer.py`, `backend/app/glossary.py` | Translates only frequency/timing tokens with a tiny dictionary. Raw English text for diet and activity is dumped directly into Telugu output (`te.append(x + ".")`). Drug names are not transliterated. |
| **FR-9** | Run round-trip check on English and Telugu | **Missing** | *None* | `roundtrip.py` is absent. No re-extraction from rendered outputs or diff against source. |
| **FR-10** | On mismatch or low confidence, send to nurse queue and block release | **Broken / Partial** | `backend/app/verifier.py` | Verifier contains a fatal date-checking bug (strips hyphens from ISO date `20261026` and tests substring against source digits `26102026`, causing valid dates to fail). No nurse review queue API or persistence exists. |
| **FR-11** | Report readability score for each output | **Partial** | `backend/app/renderer.py` | Naive inline syllable heuristic. Does not use standard `textstat`, does not report Telugu proxy, does not gate Class 8. |
| **FR-12** | Generate one-page fridge sheet PDF | **Broken** | `backend/app/pdf.py` | Simple linear text dump. Missing Noto Sans Telugu embedded font (Telugu characters fail to render/crash ReportLab). Missing 4-time-block grid layout and red warning box. |
| **FR-13** | Batch report over 2,000 summaries with PRD Section 18 metrics | **Missing** | *None* | `evaluate_local.py` does not exist. No metrics generation script or reports folder. |
| **FR-14** | Generate 7-day medicine timetable (Stretch) | **Missing** | *None* | `timetable.py` does not exist. |
| **FR-15** | Generate audio in Telugu and English (Stretch) | **Partial** | `frontend/src/App.tsx` | Client-side `speechSynthesis` only. No backend TTS endpoint (`/api/plans/{id}/audio`). |
| **FR-16** | Nurse review screen with accept and edit, logged (Stretch) | **Missing** | *None* | No review queue screen, no audit logging, no edit/accept endpoint. |
| **FR-17** | Side-by-side view: source with highlights next to care plan | **Partial** | `frontend/src/App.tsx` | Shows raw textarea next to output, but does NOT highlight source spans in the text. |

---

## 3. Problems and Defects Found

1. **Safety Violations (Non-Negotiable Rules)**:
   - **Rule 3 Violation**: `backend/app/extractor.py:25` defaults unparsed frequency to `"OD"`: `expand_frequency(freq_token or "OD")`. Guessing short forms is strictly forbidden.
   - **Rule 5 Violation**: No `source_span` `[start, end]` character offsets in `models.py` or `extractor.py`.
   - **Rule 8 Violation**: Telugu rendering leaves diet and activity instructions in English (`renderer.py:49`), creating mixed-language slop.
2. **Critical Bugs**:
   - **Verifier Date Check Failure (`verifier.py:32-34`)**: Compares ISO `YYYYMMDD` against DD/MM/YYYY source digits (`"20261026" not in "26102026"`), causing every standard Indian discharge date to be falsely blocked.
   - **ReportLab Telugu Font Crash (`pdf.py`)**: Uses default Helvetica font, which lacks Telugu glyphs and crashes on non-Latin Unicode.
3. **Architecture Gaps**:
   - Missing dual-extraction architecture (no `rules_parser.py`, no `llm_extractor.py`).
   - Missing round-trip verification (`roundtrip.py`).
   - Missing persistence and review queue endpoints.

---

## 4. Architectural Decisions: Keep, Fix, or Replace

| Module / Component | Decision | Rationale & Scope |
|---|---|---|
| `backend/app/models.py` | **REPLACE** -> `schema.py` | Align strictly with PRD Section 9.1 (`patient`, `medicines`, `warning_signs`, `diet`, `activity`, `follow_ups`, `flags`), requiring `source_span: list[int]` on every item. |
| `backend/app/glossary.py` | **REPLACE** | Replace hardcoded Python dict with file-driven loaders for `backend/data/glossary.json`, `drug_table.csv`, `phrases_en.json`, and `phrases_te.json`. |
| `backend/app/extractor.py` | **REPLACE** -> `rules_parser.py` + `llm_extractor.py` | Split into deterministic rule parser for dosage tables and dates with exact spans, plus schema-constrained LLM extractor adapter. |
| `backend/app/verifier.py` | **REPLACE** | Implement true source-span verification, dual-extractor merge, exact date matching, and field checking. |
| `backend/app/renderer.py` | **REPLACE** -> `render_en.py` + `render_te.py` | Separate English templates and Telugu locked templates with protected token enforcement and transliteration. |
| `roundtrip.py` | **NEW** | Re-extract from English & Telugu outputs and diff against source to block any hallucinated or modified fields. |
| `readability.py` | **NEW** | Implement Flesch-Kincaid grade calculation for English and syllable/word proxy for Telugu. |
| `backend/app/pdf.py` | **REPLACE** -> `fridge_sheet.py` | Professional one-page A4 fridge sheet with embedded Noto Sans Telugu font and 4-time-block dosage table. |
| `timetable.py` & `audio.py` | **NEW** (Stretch) | Day-by-day 7-day calendar and audio generation endpoint. |
| `backend/app/main.py` | **FIX & EXPAND** | Add review queue, plan retrieval, PDF, audio, and batch endpoints. |
| `frontend/src/App.tsx` | **FIX & EXPAND** | Upgrade to comprehensive nurse-first workspace: source highlights, bilingual care plan, nurse review queue, metrics dashboard, planted-error demo switch. |

---

## 5. Build Order & Gates (PRD Section 20)

We follow PRD Section 20 strictly with gate verification at every step:

- **Step 1: Schema, Glossary & Drug-Table Loaders, Rules Parser**
  - Files: `schema.py`, `glossary.py` (loader), `backend/data/` datasets, `rules_parser.py`, `test_rules_parser.py`.
  - Gate: 100% extraction accuracy of medicines and dates on `sample_20.json`.
- **Step 2: Ingest, LLM Extractor Adapter, Verifier**
  - Files: `ingest.py`, `llm_extractor.py`, `verifier.py`, `test_verifier.py`.
  - Gate: 50 summaries in `gold_50.json` pass source-span verification; extractor disagreements flag for nurse review.
- **Step 3: English Renderer, Round-trip Verification, Readability**
  - Files: `render_en.py`, `roundtrip.py`, `readability.py`, `test_roundtrip.py`.
  - Gate: 0 hard errors on 50 gold summaries; English Flesch-Kincaid <= Class 8.
- **Step 4: Telugu Renderer & Telugu Round-trip**
  - Files: `render_te.py`, transliteration mapping, Telugu round-trip verifier.
  - Gate: 0 hard errors on Telugu outputs; protected tokens appear exactly once.
- **Step 5: Fridge Sheet PDF & UI Overhaul**
  - Files: `fridge_sheet.py` with Noto Sans Telugu, UI components (SourceView highlights, bilingual cards, review queue, planted-error demo).
  - Gate: One A4 PDF in English & Telugu prints cleanly; UI shows source highlights and status banner.
- **Step 6: Batch Evaluation & Metrics**
  - Files: `evaluate_local.py`, `reports/metrics.json`, `reports/METRICS.md`.
  - Gate: Full run on 2,000 synthetic summaries producing all PRD Section 18 metrics.
- **Step 7: Demo Path & Planted Error Switch**
  - Files: `scripts/demo.md`, demo preset, error tamper switch in UI.
  - Gate: 90-second demo script executed and verified end-to-end.
- **Step 8 (Stretch): 7-Day Timetable, Audio, Nurse Review Logging**
  - Files: `timetable.py`, `audio.py`, nurse review acceptance log.
  - Gate: Complete stretch suite verified.
