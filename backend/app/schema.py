# CareBridge typed care-plan schema
# Source of truth: CareBridge PRD Section 9.1 and Section 14

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

ConditionGroup = Literal["diabetes", "post_op", "cardiac", "respiratory", "maternity"]
Severity = Literal["return_immediately", "urgent", "monitor"]
IssueSeverity = Literal["block", "warn"]


class Patient(BaseModel):
    # Patient demographics and condition category
    name: Optional[str] = None
    age: Optional[int] = None
    condition_group: Optional[ConditionGroup] = None


class Medicine(BaseModel):
    # Single medication order strictly grounded in source
    id: str = Field(description="Unique medicine ID e.g. M1, M2")
    name_generic: str = Field(description="Generic molecule name")
    name_as_written: str = Field(description="Exact medication name written in source")
    form: Optional[str] = Field(default=None, description="tablet, capsule, syrup, injection, drops")
    dose: str = Field(description="Dose string e.g. 500 mg, 5 mg, 10 ml")
    frequency_code: str = Field(description="Standard clinical frequency code e.g. BD, OD, TDS, HS, SOS")
    frequency_plain: str = Field(description="Plain English frequency e.g. 2 times a day")
    timing: Optional[str] = Field(default=None, description="after food, before food, with food, at bedtime")
    duration: Optional[str] = Field(default=None, description="e.g. 30 days, 5 days")
    route: Optional[str] = Field(default="oral", description="oral, topical, ophthalmic, inhaled")
    special_instruction: Optional[str] = None
    needs_confirmation: bool = Field(default=False, description="Flagged for clinical confirmation by nurse")
    source_span: list[int] = Field(
        description="Character offset [start, end] in raw source text"
    )

    @field_validator("source_span")
    @classmethod
    def validate_span(cls, v: list[int]) -> list[int]:
        if len(v) != 2 or v[0] < 0 or v[1] < v[0]:
            raise ValueError(f"Invalid source_span: {v}. Must be [start, end] with start <= end.")
        return v


class WarningSign(BaseModel):
    # Warning sign indicating when patient should return to hospital
    id: str = Field(description="W1, W2...")
    text_source: str = Field(description="Exact or normalized warning text from source")
    severity: Severity = Field(default="return_immediately")
    source_span: list[int] = Field(description="[start, end] offset in source text")

    @field_validator("source_span")
    @classmethod
    def validate_span(cls, v: list[int]) -> list[int]:
        if len(v) != 2 or v[0] < 0 or v[1] < v[0]:
            raise ValueError(f"Invalid source_span: {v}")
        return v


class DietItem(BaseModel):
    # Dietary instruction
    id: str
    text_source: str
    source_span: list[int]

    @field_validator("source_span")
    @classmethod
    def validate_span(cls, v: list[int]) -> list[int]:
        if len(v) != 2 or v[0] < 0 or v[1] < v[0]:
            raise ValueError(f"Invalid source_span: {v}")
        return v


class ActivityItem(BaseModel):
    # Physical activity restriction or guidance
    id: str
    text_source: str
    source_span: list[int]

    @field_validator("source_span")
    @classmethod
    def validate_span(cls, v: list[int]) -> list[int]:
        if len(v) != 2 or v[0] < 0 or v[1] < v[0]:
            raise ValueError(f"Invalid source_span: {v}")
        return v


class FollowUp(BaseModel):
    # Scheduled follow-up consultation
    id: str
    department: Optional[str] = None
    date: str = Field(description="Normalized ISO date YYYY-MM-DD")
    purpose: Optional[str] = "review"
    source_span: list[int]

    @field_validator("source_span")
    @classmethod
    def validate_span(cls, v: list[int]) -> list[int]:
        if len(v) != 2 or v[0] < 0 or v[1] < v[0]:
            raise ValueError(f"Invalid source_span: {v}")
        return v


class Flag(BaseModel):
    # Ambiguity, conflict, or clinical uncertainty requiring nurse review
    field: str
    reason: str
    action: str = "nurse_review"


class CarePlan(BaseModel):
    # The unified single source of truth care plan
    patient: Optional[Patient] = None
    medicines: list[Medicine] = []
    warning_signs: list[WarningSign] = []
    diet: list[DietItem] = []
    activity: list[ActivityItem] = []
    follow_ups: list[FollowUp] = []
    flags: list[Flag] = []
    source_hash: str
    extractor: str = "rules_parser"


class VerificationIssue(BaseModel):
    # Granular verification result per field
    severity: IssueSeverity
    field: str
    message: str
    source_text: Optional[str] = None
    source_span: Optional[list[int]] = None


class VerificationResult(BaseModel):
    # Complete gate check result
    passed: bool
    mismatch_count: int
    issues: list[VerificationIssue] = []
    checked_fields: int
    source_hash: str


class RenderedPlan(BaseModel):
    # Patient-facing generated outputs
    english: str
    telugu: str
    readability_grade: float
    readability_telugu_proxy: dict = Field(default_factory=dict)
    protected_tokens: list[str] = []
    is_unreviewed_telugu: bool = True
