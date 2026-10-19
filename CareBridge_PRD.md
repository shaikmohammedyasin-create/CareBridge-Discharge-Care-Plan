# CareBridge: Product Requirements Document (PRD)

| Field | Value |
|---|---|
| Project | CareBridge: Discharge Summary to Patient-Understandable Care Plan |
| Hackathon | Talent AP Mega Hackathon, Problem H2 (Healthcare) |
| Team | BALLERINA |
| Team leader | Mohammed Yasin Shaik |
| Version | 1.0 (build-ready) |
| Date | 18 October 2026 |

---

## 1. One-line summary

CareBridge reads a clinical discharge summary and produces a verified, plain-language care plan in **English and Telugu**, plus a **one-page fridge sheet**, without ever dropping, changing or inventing a medical instruction.

**Analogy:** think of a trained interpreter who is not allowed to improvise. The interpreter reads the doctor's note, fills a fixed form, writes the patient version from approved sentences, and then a second person reads that version back and checks it against the original. If the two do not match, a nurse is called.

---

## 2. Problem

A patient goes home with a two-page summary full of short forms (BD, HS, pc), dosage tables and dates. They cannot read it, and in India they may not read English. Doses are missed, follow-ups are skipped, warning signs are ignored, and the patient comes back to hospital.

The challenge rules make one thing clear: **faithfulness is scored above fluency.** A dropped medicine, a changed dose or an invented instruction is a hard penalty. A beautiful but wrong care plan loses. A plain but correct one wins.

---

## 3. Goals and non-goals

### Goals

| ID | Goal | How we measure it |
|---|---|---|
| G1 | Zero dropped medicines, doses, frequencies, durations or follow-up dates | Extraction diff on all 2,000 summaries |
| G2 | Zero invented instructions | Every output line maps to a source span |
| G3 | Same faithfulness in Telugu as in English | Same diff applied to the Telugu output |
| G4 | Readable by a Class 8 student | Readability grade reported per output |
| G5 | A fridge sheet a family can use | One A4 page, large type, time-of-day blocks |
| G6 | Safe failure | Unclear items go to a nurse, never guessed |

### Non-goals

- No diagnosis, no new medical advice, no dose suggestions.
- No use of the patient's wider health record. The summary is the only input.
- No chat with the patient in the core product.
- No claim that the source summary is correct. We assume it is, as the problem states.

---

## 4. Users

| User | What they need |
|---|---|
| Patient (low literacy, may not read English) | Simple words, large print, pictures of morning, noon and night |
| Family caregiver | Clear list of what to give, when, and when to rush back to hospital |
| Discharge nurse (minutes per patient) | One click to generate, one screen to review flagged items, one click to print |
| Hospital quality lead | Proof that the output matches the source |

---

## 5. Scope

### MVP (must have, scored)

1. Input: discharge summary text (the 2,000 synthetic summaries).
2. Structured care plan: medicines (what, how much, when, how long), warning signs, diet and activity, follow-up appointments.
3. English and Telugu output.
4. Faithfulness check on both languages.
5. Readability score.
6. One-page fridge sheet (PDF).
7. Local `evaluate`-style report that mirrors the organizer's harness.

### Stretch (do after the MVP is stable)

- 7-day medicine timetable.
- Spoken audio version (Telugu and English).
- Nurse review screen with accept and edit.

### Out of scope for the hackathon

- Hospital system integration, WhatsApp delivery, extra languages. These appear in the rollout plan only.

---

## 6. Core design principle: extract, verify, render

The most important decision in this project:

> **The AI never writes free text for the patient.**
> It only fills a fixed form from the source. The patient-facing words come from reviewed templates. Then the result is read back and compared.

Why this works:

- A language model that writes freely tries to be helpful. In medicine that means it may add advice, round a dose or skip a line.
- If the model can only fill fields, and each field must point to words in the source, an invented instruction has nowhere to live.
- If the output is read back and compared, a mistake is caught before the family sees it.

Three safety layers:

| Layer | What it does |
|---|---|
| 1. Dual extraction | A rule-based parser reads the dosage tables. The LLM reads the narrative. They must agree. |
| 2. Source-span check | Every extracted field must quote or point to text in the source. No match, field removed. |
| 3. Round-trip check | Extract again from the English and Telugu output. Compare with the source. Any mismatch blocks release. |

---

## 7. System architecture

```
                   +-----------------------------------------+
                   |   Inputs: discharge summary             |
                   |   + abbreviation glossary + drug table  |
                   +--------------------+--------------------+
                                        |
                                        v
                   +-----------------------------------------+
                   |  1. INGEST / NORMALISE                  |
                   |  clean text, split sections, expand     |
                   |  short forms (BD, TDS, HS, pc, SOS)     |
                   +--------------------+--------------------+
                                        |
                 +----------------------+----------------------+
                 v                                             v
   +---------------------------+                 +---------------------------+
   | 2a. RULE PARSER           |                 | 2b. LLM EXTRACTOR         |
   | dosage tables, dates      |                 | narrative: warning signs, |
   | (regex + table parser)    |                 | diet, activity, follow-up |
   +-------------+-------------+                 +-------------+-------------+
                 |                                             |
                 +----------------------+----------------------+
                                        v
                   +-----------------------------------------+
                   |  3. MERGE + VERIFY (source-span check)  |
                   |  fields must agree and point to source  |
                   +----------+---------------------+--------+
                              | pass                | fail / unsure
                              v                     v
        +------------------------------+    +--------------------------+
        | 4. RENDER                    |    |  NURSE REVIEW QUEUE      |
        | English templates (Class 8)  |    |  never auto-released     |
        | Telugu: locked glossary,     |    +------------+-------------+
        | protected tokens             |                 ^
        +--------------+---------------+                 |
                       v                                 |
        +------------------------------+                 |
        | 5. ROUND-TRIP CHECK          |-----------------+
        | re-extract from EN and TE,   |   mismatch
        | diff against source          |
        +--------------+---------------+
                       | pass
                       v
        +------------------------------------------------------------+
        | 6. OUTPUTS: care plan (EN + TE) | readability score         |
        |    fridge sheet PDF | 7-day timetable | audio               |
        +------------------------------------------------------------+
```

### Component responsibilities

| Component | Responsibility | Never does |
|---|---|---|
| Normaliser | Cleans text, finds sections, expands short forms using the glossary | Guess an ambiguous short form |
| Rule parser | Reads dosage tables and dates with fixed rules | Interpret narrative |
| LLM extractor | Fills the care-plan schema from the narrative, with JSON schema output | Write patient-facing sentences |
| Verifier | Checks every field against the source text and merges both extractors | Auto-fix disagreements |
| Renderer | Turns the verified schema into English and Telugu using templates | Add content that is not in the schema |
| Round-trip checker | Extracts from the output and diffs against the source | Pass anything with a mismatch |
| Report module | Readability grade, metrics, evaluation report | Hide failures |
| Fridge sheet builder | Lays out one printable page | Change any content |

---

## 8. Technology stack

| Layer | Choice | Why | Alternative |
|---|---|---|---|
| Backend | Python 3.11 + FastAPI | Fast to build, strong text and ML libraries, easy typed schemas | Flask |
| Schema and validation | Pydantic v2 | Typed care-plan schema, strict validation, JSON schema for the LLM | dataclasses + jsonschema |
| Rule parsing | Python `re`, `pandas` | Dosage tables are structured, rules are more reliable than a model here | `camelot` for PDF tables |
| LLM | One model behind a thin adapter, JSON-schema constrained output, temperature 0 | Adapter lets you swap models if the organizer restricts them | Any API or local model with structured output |
| Telugu | Template library + locked glossary; LLM only for rare free-text items, flagged for review | Keeps doses and drug names exact | IndicTrans2 for rare sentences |
| Readability | `textstat` (Flesch-Kincaid grade) for English; sentence and word length proxy for Telugu | No standard grade exists for Telugu, so state the proxy openly | Custom Indic readability formula |
| Frontend | React + Vite + Tailwind | You already work in React; fast demo UI | Streamlit for speed |
| PDF fridge sheet | HTML to PDF (WeasyPrint) or ReportLab | Full control of layout and Telugu fonts | Playwright print |
| Telugu font | Noto Sans Telugu (embedded) | Prints correctly on any device | Nirmala UI |
| Audio (stretch) | gTTS or an Indic TTS model | Telugu and English voices | Browser SpeechSynthesis |
| Storage | SQLite (results, audit log) | Zero setup | JSON files |
| Testing | pytest + the organizer's `evaluate.py` | Reproducible scoring | none |
| Packaging | Docker (one container) plus a README with one-command run | Judges can run it | venv + requirements.txt |

**Rule for the LLM:** temperature 0, schema-constrained JSON, no free text output, retries limited to 2, every call logged.

---

## 9. Data model

### 9.1 Care-plan schema (the single source of truth)

```json
{
  "patient": { "name": "string|null", "age": "int|null", "condition_group": "diabetes|post_op|cardiac|respiratory|maternity" },
  "medicines": [
    {
      "id": "M1",
      "name_generic": "Metformin",
      "name_as_written": "Tab Metformin",
      "form": "tablet",
      "dose": "500 mg",
      "frequency_code": "BD",
      "frequency_plain": "2 times a day",
      "timing": "after food",
      "duration": "30 days",
      "route": "oral",
      "special_instruction": null,
      "source_span": [120, 160]
    }
  ],
  "warning_signs": [
    { "id": "W1", "text_source": "chest pain", "severity": "return_immediately", "source_span": [410, 421] }
  ],
  "diet": [ { "id": "D1", "text_source": "low sugar diet", "source_span": [500, 514] } ],
  "activity": [ { "id": "A1", "text_source": "avoid heavy lifting for 4 weeks", "source_span": [530, 562] } ],
  "follow_ups": [
    { "id": "F1", "department": "OPD", "date": "2026-10-26", "purpose": "review", "source_span": [600, 625] }
  ],
  "flags": [ { "field": "M2.frequency", "reason": "ambiguous short form", "action": "nurse_review" } ]
}
```

Rules:

- Every item has a `source_span`. No span, no item.
- Fields we cannot read are `null` and appear in `flags`. We never fill a gap.
- Doses, dates and drug names are stored exactly as in the source and are **protected tokens** in rendering.

### 9.2 Frequency map (fixed table)

| Source code | Plain English | Telugu (template) |
|---|---|---|
| OD | Once a day | రోజుకు 1 సారి |
| BD / BID | 2 times a day (morning and night) | రోజుకు 2 సార్లు (ఉదయం, రాత్రి) |
| TDS / TID | 3 times a day (morning, afternoon, night) | రోజుకు 3 సార్లు (ఉదయం, మధ్యాహ్నం, రాత్రి) |
| QID | 4 times a day | రోజుకు 4 సార్లు |
| HS | At bedtime | నిద్రపోయే ముందు |
| SOS / PRN | Only when needed, as written | అవసరమైనప్పుడు మాత్రమే |
| pc | After food | భోజనం తర్వాత |
| ac | Before food | భోజనానికి ముందు |

Ambiguity rule: `OD` also means "right eye" for eye drops. If the route or form is eye-related, flag it for a nurse. Never guess.

Telugu strings must be reviewed by a native speaker before the final demo.

---

## 10. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Accept a discharge summary as text or file and read its sections | Must |
| FR-2 | Expand short forms using the provided glossary, flag unknown ones | Must |
| FR-3 | Resolve brand names to generic names using the drug table | Must |
| FR-4 | Extract every medicine with name, dose, frequency, timing, duration | Must |
| FR-5 | Extract warning signs, diet, activity and follow-up appointments | Must |
| FR-6 | Every extracted item carries a source span | Must |
| FR-7 | Render an English care plan from reviewed templates | Must |
| FR-8 | Render a Telugu care plan with protected tokens | Must |
| FR-9 | Run the round-trip check on English and Telugu | Must |
| FR-10 | On any mismatch or low confidence, send to the nurse queue and block release | Must |
| FR-11 | Report a readability score for each output | Must |
| FR-12 | Generate a one-page fridge sheet PDF | Must |
| FR-13 | Produce a batch report over all 2,000 summaries with the metrics in section 14 | Must |
| FR-14 | Generate a 7-day medicine timetable | Should |
| FR-15 | Generate audio in Telugu and English | Should |
| FR-16 | Nurse review screen with accept and edit, edits are logged | Should |
| FR-17 | Show a side-by-side view: source with highlights next to the care plan | Should |

---

## 11. Non-functional requirements

| Area | Requirement |
|---|---|
| Faithfulness | 0 hard errors (dropped or altered medicine, dose, frequency, duration, date) on the evaluation set |
| Safety | Unsure always means nurse review, never a guess |
| Reading level | English at Class 8 or below, short sentences, no jargon |
| Speed | Under 10 seconds per summary on a normal laptop |
| Determinism | Same input gives same output (temperature 0, fixed templates) |
| Auditability | Every output stores its source spans, verifier result and model version |
| Privacy | Synthetic data only; no data leaves the machine except the LLM call; no patient data in logs beyond the audit store |
| Portability | Runs from one Docker command; README under one page |

---

## 12. Telugu strategy

Translation is where doses get damaged, so we use a controlled approach:

1. **Protected tokens.** Doses (`500 mg`), dates, and drug names are never translated. Drug names are written in Telugu script by a fixed transliteration table, and doses and numbers stay as digits.
2. **Locked glossary.** Frequency, timing, and common warning signs map to fixed reviewed Telugu phrases.
3. **Phrase library for the common 80 percent.** Diet, activity and warning-sign lines are matched to a finite library of reviewed sentences.
4. **Fallback for rare lines.** Translate with the LLM using the glossary and protected tokens, mark the line as `needs_review`, and show it to the nurse.
5. **Verification.** Re-extract from the Telugu output and diff against the source. Also check that every protected token appears exactly once where expected.
6. **Human review.** A native Telugu speaker reviews the template library once. This is a one-time cost.

Telugu readability: no accepted grade formula exists, so report a proxy (average words per sentence, share of short words) and say plainly that it is a proxy.

---

## 13. Outputs

### 13.1 Care plan (English and Telugu)

Fixed section order, same in both languages:

1. Your medicines (table: medicine, how much, when, for how long, with or without food)
2. Go to the hospital at once if (warning signs)
3. What to eat and avoid
4. Activity
5. Your next visits (department, date)

Rules: short sentences, one instruction per line, numbers as digits, no abbreviations.

### 13.2 Fridge sheet (one A4 page)

- Top: patient name, date, hospital contact line (if present in the source).
- Middle: a grid with four time blocks (morning, afternoon, night, bedtime) listing which medicine and how much.
- Red box: "Go to hospital at once if".
- Bottom: next visit date and department.
- Large font (minimum 14 pt body), high contrast, Telugu on one side and English on the other or two print versions.

### 13.3 Stretch outputs

- **7-day timetable:** a day-by-day grid generated only from verified frequencies and durations. A medicine stops on the day its duration ends.
- **Audio:** the care plan read aloud from the same verified text, so audio cannot differ from the print.

---

## 14. Verification specification

### 14.1 What is compared

For each medicine, the following must match the source after normalisation:

| Field | Comparison |
|---|---|
| Name | Generic name equal (after brand to generic mapping) |
| Dose | Exact string equal (number and unit) |
| Frequency | Same normalised code |
| Timing | Same (before, after, with food, bedtime) |
| Duration | Same number and unit |
| Follow-up date | Exact date equal |
| Warning signs | Every source warning sign appears in output |

### 14.2 Error classes

| Class | Meaning | Action |
|---|---|---|
| Dropped | In source, missing in output | Block, nurse review |
| Altered | In both, value differs | Block, nurse review |
| Invented | In output, no source span | Block, remove line |
| Unsure | Extractors disagree or short form ambiguous | Nurse review |

### 14.3 Pass rule

A summary is released only when dropped, altered and invented counts are all **zero**. There is no partial pass.

---

## 15. API design

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/generate` | Body: summary text. Returns care plan JSON, status, flags |
| GET | `/api/plans/{id}` | Fetch a stored plan with verifier result |
| GET | `/api/plans/{id}/fridge-sheet.pdf` | Download the fridge sheet |
| GET | `/api/plans/{id}/audio?lang=te` | Stretch: audio file |
| POST | `/api/batch` | Run all summaries, return the metric report |
| GET | `/api/review-queue` | List plans waiting for a nurse |
| POST | `/api/review/{id}` | Nurse accepts or edits a flagged item |
| GET | `/api/health` | Health check |

Response status values: `released`, `needs_review`, `blocked`.

---

## 16. UI screens

1. **Generate screen:** paste or select a summary, press Generate.
2. **Result screen:** left shows the source with highlighted spans, right shows the care plan with an English and Telugu toggle. A green banner says "0 mismatches" or an amber banner lists flagged items.
3. **Review queue:** flagged items with the reason and Accept or Edit buttons.
4. **Fridge sheet preview:** the printable page with a Print button.
5. **Metrics page:** batch results (faithfulness, readability, abstain rate, latency).

Design rule: nurse-first. Everything needed for one patient fits in one screen and takes under 60 seconds.

---

## 17. Folder structure

```
carebridge/
  README.md
  docker-compose.yml
  backend/
    app/
      main.py              # FastAPI app and routes
      schema.py            # Pydantic care-plan schema
      ingest.py            # cleaning, sections, glossary expansion
      rules_parser.py      # dosage tables and dates
      llm_extractor.py     # schema-constrained LLM call
      verifier.py          # merge, source-span check
      render_en.py         # English templates
      render_te.py         # Telugu templates and glossary
      roundtrip.py         # re-extract and diff
      readability.py       # grade scores
      fridge_sheet.py      # PDF builder
      timetable.py         # stretch
      audio.py             # stretch
    data/
      glossary.json
      drug_table.csv
      phrases_en.json
      phrases_te.json
    tests/
      test_rules_parser.py
      test_verifier.py
      test_roundtrip.py
    evaluate_local.py      # mirrors the organizer harness
  frontend/
    src/
      pages/ Generate.jsx Result.jsx Review.jsx Metrics.jsx
      components/ SourceView.jsx PlanView.jsx FridgeSheet.jsx
  reports/
    metrics.json
    sample_outputs/
```

---

## 18. Evaluation and metrics

Report these on the 2,000 summaries and on the 50 gold examples:

| Metric | Definition | Target |
|---|---|---|
| Medicine recall | Source medicines found in output / source medicines | 100% |
| Dose exact match | Doses equal / medicines | 100% |
| Frequency match | Frequencies equal / medicines | 100% |
| Duration match | Durations equal / medicines | 100% |
| Follow-up date match | Dates equal / dates | 100% |
| Invented instruction rate | Output lines without source span / output lines | 0% |
| Telugu faithfulness | Same checks on the Telugu round-trip | 100% |
| Hard errors | Dropped + altered + invented that reached release | 0 |
| Abstain rate | Plans sent to nurse / all plans | Report honestly (lower is better, but never hide) |
| Readability | Flesch-Kincaid grade (English), proxy (Telugu) | Class 8 or below |
| Latency | Seconds per summary | Under 10 |

Important: report the abstain rate openly. A system that sends everything to a nurse is safe but useless. A system that never abstains is unsafe. State where you sit.

Also compare against the 50 gold examples for readability and structure, not for word overlap.

---

## 19. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM adds or rounds a dose | Hard penalty | Extract-then-render, source-span check, round-trip diff |
| Extractors disagree on tables | Wrong dose | Rule parser is the authority for tables; disagreement goes to nurse |
| Telugu damages numbers or names | Hard penalty | Protected tokens, locked glossary, same diff on Telugu |
| Ambiguous short forms (OD, SOS) | Wrong instruction | Context rules, flag if unsure |
| Telugu phrases are wrong or stiff | Loss of trust | Native speaker review of the phrase library |
| Model restricted or unavailable at judging | Demo fails | Model adapter, cached outputs for the demo set |
| Too many abstentions | Looks useless | Tune rules on a validation split, report abstain rate |
| Time | Incomplete MVP | Build order in section 20, stretch only after MVP passes |
| Telugu font missing on print | Broken fridge sheet | Embed Noto Sans Telugu in the PDF |

---

## 20. Build plan (priority order)

Build in this order. Do not start a later step until the earlier one passes its check.

| Step | Build | Done when |
|---|---|---|
| 1 | `schema.py`, glossary and drug table loaders, `rules_parser.py` | Parser extracts all medicines and dates from 20 sample summaries correctly |
| 2 | `ingest.py` + `llm_extractor.py` + `verifier.py` | Merged schema passes the source-span check on 50 summaries |
| 3 | `render_en.py` + `roundtrip.py` + `readability.py` | English output has 0 hard errors on the 50 gold summaries; grade is Class 8 or below |
| 4 | `render_te.py` and Telugu round-trip | Telugu passes the same diff on the same 50 |
| 5 | `fridge_sheet.py` and the UI (Generate, Result) | One page PDF prints correctly in English and Telugu |
| 6 | `evaluate_local.py` batch run on all 2,000 | Metrics file produced and numbers recorded |
| 7 | Demo video (90 seconds) | Shows paste, extract, EN and TE plans, planted error caught, fridge sheet |
| 8 | Stretch: timetable, audio, nurse review screen | Only after steps 1 to 7 are done |

### Demo script (90 seconds)

1. Paste a summary full of short forms.
2. Click Generate. Source highlights appear.
3. Show the English and Telugu plans with the readability grade.
4. Show the banner: 0 mismatches.
5. Plant a small error (change a dose in the output). Show the checker catching it and sending it to the nurse.
6. Print the fridge sheet. Play the audio if built.

---

## 21. Definition of done

- [ ] All 2,000 summaries processed, metrics file saved
- [ ] 0 hard errors released, in English and in Telugu
- [ ] Readability reported for English and Telugu (proxy labelled)
- [ ] Fridge sheet prints on one A4 page in both languages
- [ ] Telugu phrase library reviewed by a native speaker
- [ ] Demo video recorded and the link added to the PPT
- [ ] README runs the project with one command
- [ ] PPT numbers replaced with real measured results

---

## 22. Assumptions and open questions

| Item | Status |
|---|---|
| Format of the organizer's summaries (plain text, PDF, JSON) | Unknown until the dataset is opened. Step 1 adapts the parser. |
| Organizer limits on which LLM can be used | Check the rules and FAQs. The adapter covers this. |
| Whether one team can submit to more than one problem | Check the FAQs tab on the portal before applying. |
| Which Indian language | Telugu chosen: local to Andhra Pradesh and the event location. |
| Exact scoring weights in `evaluate.py` | Read the harness first, then tune the abstain threshold. |

---

## 23. Rollout (after the hackathon)

1. **Phase 1:** hackathon build: English and Telugu, five clinical areas.
2. **Phase 2:** pilot in one district hospital, nurse signs off every plan.
3. **Phase 3:** add Hindi, Tamil and others by swapping the glossary and phrase library; integrate with the hospital system; deliver the fridge sheet by WhatsApp.
