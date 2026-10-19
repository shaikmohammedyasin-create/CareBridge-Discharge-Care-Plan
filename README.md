# CareBridge: Discharge Summary to Patient Care Plan

CareBridge reads a clinical discharge summary and produces a verified, plain-language care plan in **English (Class 8 or below)** and **Telugu**, plus a **one-page A4 fridge sheet**, without dropping, changing, or hallucinating medical instructions.

Team BALLERINA | Talent AP Mega Hackathon (Problem H2: Healthcare) | Team Leader: Mohammed Yasin Shaik

---

## Architecture & Safety Principles

1. **The AI never writes free text for the patient**: Language models only populate a typed care-plan schema. Patient-facing words come from reviewed templates and locked glossaries.
2. **Dual Extraction**: Deterministic rule parser (authority for dosage tables and dates) + thin LLM extractor (for narrative warning signs, diet, and activity).
3. **Source-Span Verification**: Every extracted medication, dose, frequency, and date carries an exact character source span. No span, no item.
4. **Protected Tokens**: Doses (`500 mg`), dates, and drug names are copied verbatim into English and Telugu outputs.
5. **Round-Trip Safety Diff**: Re-extracts from English and Telugu outputs to block any dropped or altered medicine.
6. **Safe Failure**: Ambiguities (such as eye drop `OD`) route to the Nurse Review Queue.

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

### Run Test Suite (189 Tests)

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

## Measured Performance (2,000 Cases)

- **Medicine Recall**: 100.0% (4,148 / 4,148 medicines detected)
- **Hard Errors Released**: 0 (zero dropped, altered, or invented instructions)
- **English Reading Level**: Class 4.3 (Flesch-Kincaid Grade Level)
- **Telugu Faithfulness**: 100.0% (protected tokens preserved)
- **Abstain Rate (Nurse Queue)**: 37.1% (calibrated safe failure on ambiguities)
- **Pipeline Latency**: 0.0019s per summary

---

## Demo Support

Follow `scripts/demo.md` for a 90-second judge presentation. Use the in-app **"Plant Tampered Error"** demo switch to demonstrate the safety verifier instantly blocking a tampered dose and routing it to the nurse review queue.

---

## Telugu Clinical Review Notice

All Telugu phrases in `backend/data/phrases_te.json` are draft phrases that must be formally reviewed by a native Telugu clinical linguist before real hospital deployment.
