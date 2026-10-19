# CareBridge: Discharge Summary to Patient Care Plan

CareBridge reads a clinical discharge summary and produces a verified, plain-language care plan in **English (Class 8 or below)** and **Telugu**, plus a **one-page A4 fridge sheet**, without dropping, changing, or hallucinating medical instructions.

Team BALLERINA | Talent AP Mega Hackathon (Problem H2: Healthcare) | Team Leader: Mohammed Yasin Shaik

---

## Architecture & Runtime Execution Mode

CareBridge employs a dual-engine architecture:
- **Default Deterministic Pipeline (Offline)**: All dosage tables, medication orders, frequencies, durations, and follow-up dates are extracted via the deterministic rule parser (`rules_parser.py`), while narrative warning signs, diet, and activity are parsed via local section extractors. This pipeline runs 100% offline with zero external network calls, delivering sub-millisecond (0.0007s) execution latency. **All reported benchmark metrics reflect this deterministic mode.**
- **Optional LLM Adapter**: An OpenAI-compatible adapter (`llm_extractor.py`) is provided for environments with cloud model access (configured via `LLM_BASE_URL` in `.env`). It operates strictly at temperature 0, populating only the typed Pydantic schema without ever generating free-form patient text.
- **Safety Verification Gate**: In both modes, every extracted item must carry character source spans, and output plans undergo round-trip diff verification in English and Telugu before release. Ambiguities (such as eye drop `OD`) automatically route to the Nurse Review Queue.

---

## Quick Start (Run the App)

### Option 1: Docker (One Command)

```bash
docker compose up --build
```

Open `http://localhost:5173` in your browser. Backend runs on port `8000`.

### Option 2: Local Development

```bash
# Backend (FastAPI)
pip install -r backend/requirements.txt
python -m uvicorn --app-dir backend app.main:app --port 8001

# Frontend (React + Vite)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Backend health check: `http://localhost:8001/api/health`.

---

## Run Tests & Evaluation

### Run Test Suite (190 Tests)

```bash
PYTHONPATH=backend python -m pytest backend/tests/ -v
```

### Run Batch Evaluation (2,000 Summaries)

```bash
python evaluate_local.py
```

Produces:
- `reports/metrics.json`: Full benchmark metrics matching PRD Section 18.
- `reports/METRICS.md`: Human-readable performance report.
- `reports/sample_outputs/`: Sample English, Telugu, and fridge sheet PDF files.

---

## Measured Performance (On Project's Synthetic Set of 2,000 Summaries)

*Note on Data Provenance: The organizer's competition files were missing from the environment download; all benchmarks were executed on the project's synthetic dataset of 2,000 summaries (`data/samples/synthetic_2000.json`).*

- **Medicine Recall**: 100.0% (4,148 / 4,148 medicines detected)
- **Dose Exact Match**: 100.0% (4,148 / 4,148 exact matches)
- **Frequency Match**: 100.0% (4,148 / 4,148 exact matches)
- **Duration Match**: 100.0% (4,148 / 4,148 exact matches)
- **Follow-up Date Match**: 100.0% (2,000 / 2,000 exact matches)
- **Hard Errors Released**: 0 (zero dropped, altered, or invented instructions)
- **English Reading Level**: Class 4.3 (Flesch-Kincaid Grade Level)
- **Telugu Faithfulness**: 100.0% (protected tokens preserved)
- **Abstain Rate (Nurse Queue)**: 8.3% (166 / 2,000 cases with ophthalmic OD ambiguity)
- **Pipeline Latency**: 0.0007s per summary (offline deterministic engine)

---

## Demo Support

Follow `scripts/demo.md` for a 90-second judge presentation. Use the in-app **"Plant Tampered Error"** demo switch to demonstrate the safety verifier instantly blocking a tampered dose and routing it to the nurse review queue.

---

## Telugu Clinical Review Notice

All Telugu phrases in `backend/data/phrases_te.json` are draft phrases that must be formally reviewed by a native Telugu clinical linguist before real hospital deployment.
