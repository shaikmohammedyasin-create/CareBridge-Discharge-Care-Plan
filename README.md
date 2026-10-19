# CareBridge

CareBridge converts a discharge summary into a source-grounded English + Telugu care plan, verifies every medication/date against the source, and blocks ambiguous or mismatched output for nurse review.

This implementation follows the submitted Round 1 design: extract into a fixed schema, source-span verification, reviewed templates, protected Telugu tokens, round-trip verification, nurse review queue, one-page fridge sheet, 7-day timetable, and audio. 

## Architecture

- Backend: FastAPI + Pydantic
- Frontend: React + TypeScript + Vite
- Extraction: deterministic demo extractor with optional OpenAI-compatible LLM adapter
- Verification: source-token and semantic field comparison
- Translation: locked Telugu templates; medicine names, doses and dates are protected
- PDF: ReportLab
- Audio: browser speech synthesis by default; backend audio endpoint can use `gTTS` if installed
- Storage: JSON files in `backend/data` for the demo

## Run

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Optional LLM

Set:

```text
LLM_BASE_URL=https://your-openai-compatible-endpoint/v1
LLM_API_KEY=...
LLM_MODEL=your-model
```

The app remains usable without an LLM using the deterministic demo extractor.

## Safety boundary

This is a hackathon prototype, not a medical device or substitute for clinical review. The system intentionally abstains when a medication instruction cannot be grounded in the source. Every generated plan should be reviewed by an authorized clinician before patient use.

## Demo

Paste:

```text
Discharge Summary
Tab Metformin 500 mg BD pc x 30 days
Tab Amlodipine 5 mg OD x 30 days
Review OPD 26/10/2026
Warning signs: severe dizziness, chest pain
Diet: low salt diet
```

The demo extractor produces a typed plan, then the verifier checks medications and dates against the original source.
