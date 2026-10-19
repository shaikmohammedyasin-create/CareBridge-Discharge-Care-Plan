# CareBridge FastAPI Backend Service
# Implements PRD Section 7, 14, 15, and FR-1 through FR-17

import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .fridge_sheet import build_fridge_sheet_pdf
from .ingest import ingest
from .llm_extractor import extract_narrative
from .readability import flesch_kincaid_grade, telugu_readability_proxy
from .render_en import render_english
from .render_te import render_telugu
from .roundtrip import verify_english_roundtrip, verify_telugu_roundtrip
from .rules_parser import parse_rules
from .schema import (
    CarePlan,
    RenderedPlan,
    VerificationResult,
)

app = FastAPI(title="CareBridge Clinical Care Plan API", version="2.0.0")

# Enable CORS for frontend Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for plans and nurse review queue
STORED_PLANS: Dict[str, dict] = {}
REVIEW_QUEUE: List[dict] = []
REVIEW_LOG: List[dict] = []


class GenerateRequest(BaseModel):
    summary: str = Field(description="Raw discharge summary text")
    plant_error: bool = Field(default=False, description="Demo switch: intentionally alters a dose to show verifier catching it")


class ReviewActionRequest(BaseModel):
    action: str = Field(description="accept or edit")
    reviewer_notes: Optional[str] = "Reviewed by discharge nurse"
    edited_plan: Optional[dict] = None


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "CareBridge",
        "team": "BALLERINA",
        "version": "2.0.0",
        "verification_gate": "zero-error",
    }


@app.post("/api/generate")
def generate(req: GenerateRequest):
    raw_summary = req.summary.strip()
    if not raw_summary:
        raise HTTPException(400, "Discharge summary text cannot be empty.")

    # 1. Ingestion
    ingest_result = ingest(raw_summary)

    # 2. Rule Parser (Authority for dosage tables and dates)
    rules_plan = parse_rules(raw_summary)

    # 3. LLM / Narrative Extractor
    narrative = extract_narrative(raw_summary)

    # 4. Merger & Source-Span Verifier
    from .verifier import merge_and_verify
    plan, verification = merge_and_verify(raw_summary, rules_plan, narrative)

    # Demo planted-error switch: intentionally alters first dose to demonstrate safety gate
    if req.plant_error and plan.medicines:
        original_dose = plan.medicines[0].dose
        plan.medicines[0].dose = "9999 mg [TAMPERED_DEMO_ERROR]"
        from .verifier import verify
        verification = verify(raw_summary, plan)

    # 5. Render English & Telugu
    english_text, protected_en = render_english(plan)
    telugu_text, protected_te, needs_review_te = render_telugu(plan)

    # 6. Round-trip verification
    rt_en = verify_english_roundtrip(english_text, plan)
    rt_te = verify_telugu_roundtrip(telugu_text, plan)

    # Combine roundtrip results into verification
    combined_issues = list(verification.issues) + list(rt_en.issues) + list(rt_te.issues)
    blocking_count = sum(1 for i in combined_issues if i.severity == "block")
    passed = verification.passed and rt_en.passed and rt_te.passed and (blocking_count == 0)

    # Readability scoring
    grade_en = flesch_kincaid_grade(english_text)
    proxy_te = telugu_readability_proxy(telugu_text)

    # Status determination: released, needs_review, or blocked
    if passed and not needs_review_te and not plan.flags:
        status = "released"
    elif blocking_count > 0:
        status = "blocked"
    else:
        status = "needs_review"

    plan_id = str(uuid.uuid4())[:8]

    final_verification = VerificationResult(
        passed=passed,
        mismatch_count=blocking_count,
        issues=combined_issues,
        checked_fields=verification.checked_fields + rt_en.checked_fields + rt_te.checked_fields,
        source_hash=plan.source_hash,
    )

    rendered = RenderedPlan(
        english=english_text,
        telugu=telugu_text,
        readability_grade=grade_en,
        readability_telugu_proxy=proxy_te,
        protected_tokens=list(set(protected_en + protected_te)),
        is_unreviewed_telugu=True,
    )

    record = {
        "id": plan_id,
        "status": status,
        "summary": raw_summary,
        "plan": plan.model_dump(),
        "verification": final_verification.model_dump(),
        "rendered": rendered.model_dump(),
        "sections": {k: v._asdict() for k, v in ingest_result.sections.items()},
    }

    STORED_PLANS[plan_id] = record

    # Route to review queue if blocked or needs review
    if status in ["blocked", "needs_review"]:
        REVIEW_QUEUE.append({
            "plan_id": plan_id,
            "patient_name": plan.patient.name if plan.patient else "Patient",
            "status": status,
            "issues": [i.model_dump() for i in final_verification.issues],
            "flags": [f.model_dump() for f in plan.flags],
            "summary_snippet": raw_summary[:120] + "...",
        })

    return {
        "id": plan_id,
        "status": status,
        "plan": plan,
        "verification": final_verification,
        "rendered": rendered,
        "sections": {k: {"start": v.start, "end": v.end} for k, v in ingest_result.sections.items()},
    }


@app.get("/api/plans/{plan_id}")
def get_plan(plan_id: str):
    record = STORED_PLANS.get(plan_id)
    if not record:
        raise HTTPException(404, f"Care plan '{plan_id}' not found.")
    return record


@app.get("/api/plans/{plan_id}/fridge-sheet.pdf")
def get_fridge_sheet(plan_id: str):
    record = STORED_PLANS.get(plan_id)
    if not record:
        raise HTTPException(404, f"Care plan '{plan_id}' not found.")
    plan = CarePlan(**record["plan"])
    pdf_bytes = build_fridge_sheet_pdf(plan, lang="both")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=carebridge-{plan_id}-fridge-sheet.pdf"},
    )


@app.post("/api/pdf")
def generate_pdf_legacy(req: GenerateRequest):
    # Generates fridge sheet PDF directly from summary
    plan = parse_rules(req.summary)
    pdf_bytes = build_fridge_sheet_pdf(plan, lang="both")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=carebridge-fridge-sheet.pdf"},
    )


@app.get("/api/review-queue")
def get_review_queue():
    # Returns items requiring nurse review
    return {
        "count": len(REVIEW_QUEUE),
        "items": REVIEW_QUEUE,
    }


@app.post("/api/review/{plan_id}")
def review_action(plan_id: str, req: ReviewActionRequest):
    record = STORED_PLANS.get(plan_id)
    if not record:
        raise HTTPException(404, f"Care plan '{plan_id}' not found.")

    log_entry = {
        "plan_id": plan_id,
        "action": req.action,
        "notes": req.reviewer_notes,
    }
    REVIEW_LOG.append(log_entry)

    # Remove from review queue
    global REVIEW_QUEUE
    REVIEW_QUEUE = [q for q in REVIEW_QUEUE if q["plan_id"] != plan_id]

    record["status"] = "released" if req.action == "accept" else "edited_and_released"
    return {"status": "success", "action": req.action, "plan_id": plan_id}


@app.get("/api/plans/{plan_id}/timetable")
def get_plan_timetable(plan_id: str):
    # Returns 7-day medication administration calendar
    from .timetable import generate_7day_timetable
    record = STORED_PLANS.get(plan_id)
    if not record:
        raise HTTPException(404, f"Care plan '{plan_id}' not found.")
    plan = CarePlan(**record["plan"])
    return generate_7day_timetable(plan)


@app.get("/api/plans/{plan_id}/audio")
def get_plan_audio(plan_id: str, lang: str = Query(default="en")):
    # Returns spoken audio for verified text
    from .audio import generate_audio_bytes
    record = STORED_PLANS.get(plan_id)
    if not record:
        raise HTTPException(404, f"Care plan '{plan_id}' not found.")

    text = record["rendered"]["telugu"] if lang.startswith("te") else record["rendered"]["english"]
    audio_bytes = generate_audio_bytes(text, lang)
    if not audio_bytes:
        # Fallback response for client-side TTS
        return {
            "status": "client_synthesis_fallback",
            "lang": lang,
            "text": text,
            "notice": "Backend gTTS offline; client-side speech synthesis available in browser.",
        }

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"inline; filename=carebridge-{plan_id}-{lang}.mp3"},
    )


@app.get("/api/review-log")
def get_review_log():
    # Complete audit trail of nurse decisions
    return {
        "count": len(REVIEW_LOG),
        "logs": REVIEW_LOG,
    }

