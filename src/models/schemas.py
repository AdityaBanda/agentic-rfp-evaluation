from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class CriterionDefinition(BaseModel):
    """A single evaluation criterion, loaded from SQLite. Never hard-coded."""

    criterion_id: int
    name: str
    description: str
    weight: float
    max_score: float
    is_active: bool = True


class CriterionEvaluation(BaseModel):
    """One criterion result as returned (and validated/normalized) from the LLM."""

    criterion_id: int
    score: float
    max_score: float
    justification: str = ""
    evidence: str = ""


class SupplierEvaluation(BaseModel):
    """The full LLM evaluation for a single supplier, after validation/normalization."""

    supplier_name: str
    criteria: list[CriterionEvaluation] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    overall_summary: str = ""


class ValidationWarning(BaseModel):
    warning_type: str
    criterion_id: Optional[int] = None
    original_value: Optional[str] = None
    normalized_value: Optional[str] = None
    message: str = ""


class CriterionResult(BaseModel):
    """A criterion result after deterministic scoring and benchmarking."""

    criterion_id: int
    name: str
    score: float
    max_score: float
    weight: float
    benchmark: Optional[float] = None
    gap: Optional[float] = None
    relative_performance: Optional[float] = None
    evidence: str = ""
    justification: str = ""
    validation_status: str = "OK"


class SupplierInput(BaseModel):
    """Raw input captured from the Streamlit UI for one supplier."""

    supplier_name: str
    submission_date: date
    experience_rating: float
    file_name: str
    file_bytes: bytes


class FinalSupplierResult(BaseModel):
    """The complete, persisted result for one supplier within a run."""

    supplier_name: str
    submission_date: date
    experience_rating: float
    absolute_score: float = 0.0
    ppi: float = 0.0
    final_rank: Optional[int] = None
    tie_break_notes: str = ""
    criteria: list[CriterionResult] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    overall_summary: str = ""
    warnings: list[ValidationWarning] = Field(default_factory=list)
    extraction_warning: Optional[str] = None
    status: str = "OK"  # OK | FAILED


class RFPRunResult(BaseModel):
    """The complete result of one RFP evaluation run, ready for persistence/export."""

    rfp_run_id: str
    created_at: datetime
    status: str
    criteria: list[CriterionDefinition]
    suppliers: list[FinalSupplierResult]
    llm_provider: str
    llm_model: str
    demo_mode: bool
