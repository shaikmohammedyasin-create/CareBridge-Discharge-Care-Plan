# CareBridge Thin LLM Adapter & Narrative Extractor
# Implements PRD Section 6, 7 (Component 2b), 8, and Non-Negotiable Rules 1, 9

import json
import logging
import os
import re
from typing import Dict, List, Optional

import httpx

from .schema import (
    ActivityItem,
    CarePlan,
    DietItem,
    FollowUp,
    Patient,
    WarningSign,
)

logger = logging.getLogger("carebridge.llm_extractor")
logger.setLevel(logging.INFO)

# Configurable environment variables for thin LLM adapter
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
MAX_RETRIES = 2
TEMPERATURE = 0.0

# Prompt strictly instructs LLM to fill fields and forbid free-text patient generation
SYSTEM_PROMPT = """You are a clinical extraction engine for CareBridge.
Your job is ONLY to extract facts from the discharge summary into a structured JSON schema.
NEVER generate medical advice, diagnosis, or patient-facing sentences.
For every extracted item, you MUST provide the exact exact text as it appears in the source.

Return JSON in this exact structure:
{
  "condition_group": "diabetes" | "post_op" | "cardiac" | "respiratory" | "maternity" | null,
  "patient_name": "string" | null,
  "patient_age": int | null,
  "warning_signs": ["exact source phrase", ...],
  "diet": ["exact source phrase", ...],
  "activity": ["exact source phrase", ...]
}
"""


def _find_source_span(source: str, query: str, start_search_from: int = 0) -> List[int]:
    # Locates exact character span of query in source text
    if not query:
        return [0, 0]
    pos = source.lower().find(query.lower(), start_search_from)
    if pos != -1:
        return [pos, pos + len(query)]
    # Fallback to word-boundary search if whitespace differs
    words = [re.escape(w) for w in query.split()]
    if words:
        pattern = r"\s+".join(words)
        m = re.search(pattern, source, re.IGNORECASE)
        if m:
            return [m.start(), m.end()]
    return [0, len(source)]


def _fallback_narrative_extraction(summary: str) -> Dict:
    # Deterministic narrative parser when no external LLM endpoint is provided
    # Detects condition group from diagnoses
    lower = summary.lower()
    cond = None
    if any(k in lower for k in ["diabet", "glycomet", "metformin", "sugar", "hba1c"]):
        cond = "diabetes"
    elif any(k in lower for k in ["cardiac", "hypertens", "ptca", "angio", "stent", "infarct"]):
        cond = "cardiac"
    elif any(k in lower for k in ["asthma", "copd", "bronch", "pulmon", "respirat"]):
        cond = "respiratory"
    elif any(k in lower for k in ["post-op", "append", "surg", "hernia", "suture", "laparosc"]):
        cond = "post_op"
    elif any(k in lower for k in ["postnatal", "ftnd", "lscs", "gravida", "matern", "obstet"]):
        cond = "maternity"

    # Extract warning signs
    warning_signs = []
    wm = re.search(r"(?:Warning signs?|Red flags?|Emergency|Seek medical help if)\s*[:\-]\s*([^\n]+)", summary, re.I)
    if wm:
        warning_signs = [x.strip() for x in re.split(r"[,;]|\band\b", wm.group(1)) if x.strip()]

    # Extract diet
    diet = []
    dm = re.search(r"(?:Diet|Dietary advice|Nutrition)\s*[:\-]\s*([^\n]+)", summary, re.I)
    if dm:
        diet = [x.strip() for x in re.split(r"[,;]|\band\b", dm.group(1)) if x.strip()]

    # Extract activity
    activity = []
    am = re.search(r"(?:Activity|Exercise|Rest|Precautions)\s*[:\-]\s*([^\n]+)", summary, re.I)
    if am:
        activity = [x.strip() for x in re.split(r"[,;]|\band\b", am.group(1)) if x.strip()]

    # Patient info
    p_name = None
    p_age = None
    pm = re.search(r"(?:Patient Name|Name)\s*[:\-]\s*([A-Za-z\s]+)", summary, re.I)
    if pm:
        p_name = pm.group(1).strip()
    agm = re.search(r"(?:Age)\s*[:\-]\s*(\d+)", summary, re.I)
    if agm:
        p_age = int(agm.group(1))

    return {
        "condition_group": cond,
        "patient_name": p_name,
        "patient_age": p_age,
        "warning_signs": warning_signs,
        "diet": diet,
        "activity": activity,
    }


def call_llm_json(prompt: str) -> Optional[Dict]:
    # Thin adapter calling external LLM with temperature 0 and max 2 retries
    if not LLM_BASE_URL or not LLM_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "temperature": TEMPERATURE,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }

    url = f"{LLM_BASE_URL.rstrip('/')}/chat/completions"

    for attempt in range(MAX_RETRIES + 1):
        try:
            logger.info("Calling LLM adapter (attempt %d/%d) model=%s", attempt + 1, MAX_RETRIES + 1, LLM_MODEL)
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
                else:
                    logger.warning("LLM API error status=%d body=%s", res.status_code, res.text)
        except Exception as e:
            logger.error("LLM adapter request failed: %s", str(e))

    return None


def extract_narrative(summary: str) -> Dict:
    # Extracts narrative elements using external LLM or deterministic fallback
    llm_result = call_llm_json(f"Discharge Summary:\n\n{summary}")
    if not llm_result:
        llm_result = _fallback_narrative_extraction(summary)

    # Attach exact source spans
    warning_signs: List[WarningSign] = []
    for i, w in enumerate(llm_result.get("warning_signs", [])):
        span = _find_source_span(summary, w)
        warning_signs.append(WarningSign(
            id=f"W{i+1}",
            text_source=w,
            severity="return_immediately",
            source_span=span,
        ))

    diet_items: List[DietItem] = []
    for i, d in enumerate(llm_result.get("diet", [])):
        span = _find_source_span(summary, d)
        diet_items.append(DietItem(
            id=f"D{i+1}",
            text_source=d,
            source_span=span,
        ))

    activity_items: List[ActivityItem] = []
    for i, a in enumerate(llm_result.get("activity", [])):
        span = _find_source_span(summary, a)
        activity_items.append(ActivityItem(
            id=f"A{i+1}",
            text_source=a,
            source_span=span,
        ))

    patient = None
    if llm_result.get("patient_name") or llm_result.get("patient_age") or llm_result.get("condition_group"):
        patient = Patient(
            name=llm_result.get("patient_name"),
            age=llm_result.get("patient_age"),
            condition_group=llm_result.get("condition_group"),
        )

    return {
        "patient": patient,
        "warning_signs": warning_signs,
        "diet": diet_items,
        "activity": activity_items,
    }
