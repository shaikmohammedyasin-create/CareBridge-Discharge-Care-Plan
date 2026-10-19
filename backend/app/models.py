from typing import Literal, Optional
from pydantic import BaseModel, Field

Risk = Literal["low", "medium", "high", "critical"]

class Medication(BaseModel):
    name: str
    dose: str
    frequency: str
    timing: Optional[str] = None
    duration: Optional[str] = None
    source_text: str
    confidence: float = Field(ge=0, le=1)

class FollowUp(BaseModel):
    department: Optional[str] = None
    date: str
    source_text: str

class CarePlan(BaseModel):
    medications: list[Medication] = []
    warning_signs: list[str] = []
    diet: list[str] = []
    activity: list[str] = []
    follow_ups: list[FollowUp] = []
    ambiguities: list[str] = []
    source_hash: str
    extractor: str = "deterministic-demo"

class VerificationIssue(BaseModel):
    severity: Literal["block", "warn"]
    field: str
    message: str
    source_text: Optional[str] = None

class VerificationResult(BaseModel):
    passed: bool
    mismatch_count: int
    issues: list[VerificationIssue] = []
    checked_fields: int
    source_hash: str

class RenderedPlan(BaseModel):
    english: str
    telugu: str
    readability_grade: float
    protected_tokens: list[str]
