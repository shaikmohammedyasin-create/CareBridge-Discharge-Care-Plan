from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from .extractor import extract
from .verifier import verify
from .renderer import render
from .pdf import make_pdf

app = FastAPI(title="CareBridge API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    summary: str

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "carebridge"}

@app.post("/api/extract")
def extract_plan(req: GenerateRequest):
    if not req.summary.strip():
        raise HTTPException(400, "Discharge summary is empty.")
    return extract(req.summary)

@app.post("/api/generate")
def generate(req: GenerateRequest):
    plan = extract(req.summary)
    verification = verify(req.summary, plan)
    rendered = render(plan)
    return {"plan": plan, "verification": verification, "rendered": rendered}

@app.post("/api/verify")
def verify_plan(req: GenerateRequest):
    plan = extract(req.summary)
    return verify(req.summary, plan)

@app.post("/api/pdf")
def pdf(req: GenerateRequest):
    plan = extract(req.summary)
    verification = verify(req.summary, plan)
    if not verification.passed:
        raise HTTPException(409, "Plan failed verification and cannot be released.")
    rendered = render(plan)
    data = make_pdf(rendered.english, rendered.telugu)
    return Response(
        data,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=carebridge-fridge-sheet.pdf"},
    )
