"""
Pydantic contract models for AI Health Copilot.
Field names are FROZEN — never rename without team consensus.
"""
from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# ── Fixed disclaimer (identical at every layer) ────────────────────────────────
DISCLAIMER = (
    "This is AI-generated information to help you understand your records. "
    "It is not a diagnosis or medical advice. Please consult your doctor."
)

# ── Type aliases ───────────────────────────────────────────────────────────────
FlagValue = Literal["LOW", "NORMAL", "HIGH", "UNKNOWN"]
DocType = Literal["prescription", "lab_report", "discharge_summary", "diagnostic_report"]
Language = Literal["en", "ta", "hi", "mixed"]
FoodInstruction = Literal["before_food", "after_food"]
ScheduleSlot = Literal["morning", "afternoon", "night"]

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ── Sub-models ─────────────────────────────────────────────────────────────────

class MedicineRecord(BaseModel):
    """One medicine entry extracted from a prescription or discharge summary."""
    name_raw: str
    generic: Optional[str] = None
    strength: Optional[str] = None
    schedule_raw: Optional[str] = None
    schedule_parsed: List[ScheduleSlot] = Field(default_factory=list)
    food_instruction: Optional[FoodInstruction] = None
    duration_days: Optional[int] = None
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: Optional[List[float]] = None

    @field_validator("schedule_parsed", mode="before")
    @classmethod
    def _coerce_schedule_parsed(cls, v: Any) -> list:
        if not v or not isinstance(v, list):
            return []
        slot_map = {0: "morning", 1: "afternoon", 2: "night"}
        if all(isinstance(x, (int, str)) and str(x) in ("0", "1") for x in v) and len(v) == 3:
            return [slot_map[i] for i, val in enumerate(v) if str(val) == "1"]
        valid = {"morning", "afternoon", "night"}
        return [str(x).lower() for x in v if str(x).lower() in valid]

    @field_validator("bbox")
    @classmethod
    def _bbox_len(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None and len(v) != 4:
            raise ValueError("bbox must have exactly 4 elements [x, y, w, h]")
        return v

    @field_validator("duration_days")
    @classmethod
    def _positive_days(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("duration_days must be positive")
        return v


class TestRecord(BaseModel):
    """One lab / diagnostic test result."""
    __test__ = False  # Prevent pytest from treating this model as a test suite
    name: str
    loinc: Optional[str] = None
    value: Optional[float] = None
    value_text: Optional[str] = None          # for non-numeric results (e.g. "Reactive")
    unit: Optional[str] = None
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    flag: FlagValue = "UNKNOWN"
    explanation_en: Optional[str] = None
    explanation_ta: Optional[str] = None
    explanation_hi: Optional[str] = None  # additive extension
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: Optional[List[float]] = None

    @field_validator("bbox")
    @classmethod
    def _bbox_len(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None and len(v) != 4:
            raise ValueError("bbox must have exactly 4 elements [x, y, w, h]")
        return v


class DiagnosisRecord(BaseModel):
    """A diagnosis text mention extracted from the document."""
    text: str
    icd10: Optional[str] = None               # additive extension: mapped ICD-10 code
    confidence: float = Field(ge=0.0, le=1.0)


class ErrorRecord(BaseModel):
    """Structured error — always present on failure, null on success."""
    code: str
    message: str


class HealthRecord(BaseModel):
    """Root contract model. All fields must match the shared contract exactly."""
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_type: DocType
    doc_date: Optional[str] = None
    collection_date: Optional[str] = None     # additive extension
    follow_up_date: Optional[str] = None      # additive extension
    language: Language = "en"
    patient_name_present: bool = False
    allergies: List[str] = Field(default_factory=list)  # additive extension
    medicines: List[MedicineRecord] = Field(default_factory=list)
    tests: List[TestRecord] = Field(default_factory=list)
    diagnoses: List[DiagnosisRecord] = Field(default_factory=list)
    summary_en: Optional[str] = None
    summary_ta: Optional[str] = None
    summary_hi: Optional[str] = None  # additive extension
    safety_alerts: List[Dict[str, Any]] = Field(default_factory=list)  # additive extension
    cost_savings: Optional[Dict[str, Any]] = None  # additive extension
    needs_review: List[str] = Field(default_factory=list)
    disclaimer: str = DISCLAIMER
    error: Optional[ErrorRecord] = None

    @field_validator("doc_date", "collection_date", "follow_up_date", mode="before")
    @classmethod
    def _validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if not _DATE_RE.match(str(v)):
            raise ValueError(f"Date must be YYYY-MM-DD, got: {v!r}")
        return v

    @field_validator("disclaimer")
    @classmethod
    def _fixed_disclaimer(cls, v: str) -> str:
        # Always overwrite with the canonical text
        return DISCLAIMER

    def mark_review(self, path: str) -> None:
        """Add a JSON-path string to needs_review (deduplicating)."""
        if path not in self.needs_review:
            self.needs_review.append(path)


# ── Error factory ──────────────────────────────────────────────────────────────

def make_error_record(code: str, message: str, doc_type: str = "lab_report") -> dict:
    """
    Return a contract-compliant dict representing an extraction failure.
    Never raises — safe to call from any except block.
    """
    return {
        "record_id": str(uuid.uuid4()),
        "doc_type": doc_type,
        "doc_date": None,
        "collection_date": None,
        "follow_up_date": None,
        "language": "en",
        "patient_name_present": False,
        "allergies": [],
        "medicines": [],
        "tests": [],
        "diagnoses": [],
        "summary_en": None,
        "summary_ta": None,
        "summary_hi": None,
        "needs_review": ["all"],
        "disclaimer": DISCLAIMER,
        "error": {"code": code, "message": message},
    }
