from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Callable, Optional

from src.agents.evaluation_agent import EvaluationAgent
from src.db import database as db
from src.llm.base import LLMProvider
from src.models.schemas import (
    CriterionDefinition,
    FinalSupplierResult,
    RFPRunResult,
    SupplierInput,
)
from src.tools.criteria_validation import validate_weights_sum_to_100
from src.tools.document_tool import DocumentExtractionTool
from src.tools.ranking_tool import RankingTool
from src.tools.scoring_tool import ScoringTool
from src.tools.validation_tool import ValidationTool
from src.utils.ids import generate_rfp_run_id
from src.utils.logging import get_logger, log_stage

logger = get_logger(__name__)

OnEvent = Callable[..., None]


class RFPOrchestrator:
    """Explicit agentic workflow for one RFP evaluation run.

    run_evaluation()
        +-- load_active_criteria()
        +-- validate_criteria()
        +-- create_run()
        +-- for each supplier:
        |     +-- extract_document()
        |     +-- evaluate_supplier()      (LLM)
        |     +-- validate_evaluation()    (deterministic)
        |     +-- calculate_scores()       (deterministic)
        +-- calculate_benchmarks()         (deterministic)
        +-- calculate_ppi()                (deterministic)
        +-- rank_suppliers()               (deterministic)
        +-- persist_results()
        +-- return_run()

    Each step has one clear responsibility and is individually callable/testable.
    The LLM is used ONLY inside evaluate_supplier(); every other step is plain,
    deterministic Python.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        llm_provider: LLMProvider,
        demo_mode: bool = False,
        on_event: Optional[OnEvent] = None,
    ):
        self.conn = conn
        self.llm_provider = llm_provider
        self.demo_mode = demo_mode
        self.on_event = on_event

        self.evaluation_agent = EvaluationAgent(llm_provider)
        self.document_tool = DocumentExtractionTool()
        self.validation_tool = ValidationTool()
        self.scoring_tool = ScoringTool()
        self.ranking_tool = RankingTool()

    def _log(self, run_id: str, stage: str, status: str, supplier: str | None = None, **fields) -> None:
        log_stage(logger, rfp_run_id=run_id, stage=stage, status=status, supplier=supplier, **fields)
        if self.on_event:
            self.on_event(stage, supplier, status, **fields)

    # ---- individual workflow steps --------------------------------------

    def load_active_criteria(self) -> list[CriterionDefinition]:
        return db.load_active_criteria(self.conn)

    def validate_criteria(self, criteria: list[CriterionDefinition]) -> None:
        validate_weights_sum_to_100(criteria)

    def create_run(self, run_id: str) -> None:
        db.create_run(
            self.conn,
            run_id=run_id,
            status="RUNNING",
            llm_provider=self.llm_provider.provider_name,
            llm_model=self.llm_provider.model_name,
            demo_mode=self.demo_mode,
        )

    def extract_document(self, supplier: SupplierInput):
        return self.document_tool.extract(supplier.file_bytes)

    def evaluate_supplier(self, run_id: str, supplier: SupplierInput, proposal_text: str, criteria):
        return self.evaluation_agent.evaluate(
            rfp_run_id=run_id,
            supplier_name=supplier.supplier_name,
            proposal_text=proposal_text,
            criteria=criteria,
        )

    def validate_evaluation(self, raw: dict, criteria):
        return self.validation_tool.validate(raw, criteria)

    def calculate_scores(self, evaluation, criteria):
        return self.scoring_tool.score_supplier(evaluation, criteria)

    def calculate_benchmarks(self, suppliers: list[FinalSupplierResult]) -> None:
        self.ranking_tool.calculate_benchmarks(suppliers)

    def calculate_ppi(self, suppliers: list[FinalSupplierResult]) -> None:
        self.ranking_tool.calculate_ppi(suppliers)

    def rank_suppliers(self, suppliers: list[FinalSupplierResult]) -> list[FinalSupplierResult]:
        return self.ranking_tool.rank(suppliers)

    def persist_results(self, run_id: str, suppliers: list[FinalSupplierResult], status: str) -> None:
        db.update_run_status(self.conn, run_id, status)
        for supplier in suppliers:
            db.save_supplier_result(self.conn, run_id, supplier)
            db.save_criterion_results(self.conn, run_id, supplier.supplier_name, supplier.criteria)
            db.save_warnings(self.conn, run_id, supplier.supplier_name, supplier.warnings)
        self.conn.commit()

    def return_run(self, run_id: str, criteria, suppliers, status: str) -> RFPRunResult:
        return RFPRunResult(
            rfp_run_id=run_id,
            created_at=datetime.now(timezone.utc),
            status=status,
            criteria=criteria,
            suppliers=suppliers,
            llm_provider=self.llm_provider.provider_name,
            llm_model=self.llm_provider.model_name,
            demo_mode=self.demo_mode,
        )

    # ---- top-level orchestration ------------------------------------------

    def run_evaluation(self, supplier_inputs: list[SupplierInput]) -> RFPRunResult:
        criteria = self.load_active_criteria()
        self.validate_criteria(criteria)

        run_id = generate_rfp_run_id()
        self.create_run(run_id)
        self._log(run_id, "create_run", "ok", suppliers=len(supplier_inputs))

        results: list[FinalSupplierResult] = [
            self._evaluate_one_supplier(run_id, supplier, criteria) for supplier in supplier_inputs
        ]

        self.calculate_benchmarks(results)
        self._log(run_id, "calculate_benchmarks", "ok")

        self.calculate_ppi(results)
        self._log(run_id, "calculate_ppi", "ok")

        ranked = self.rank_suppliers(results)
        self._log(run_id, "rank_suppliers", "ok")

        run_status = "COMPLETED" if any(s.status == "OK" for s in ranked) else "FAILED"
        self.persist_results(run_id, ranked, run_status)
        self._log(run_id, "persist_results", "ok", suppliers_ok=sum(1 for s in ranked if s.status == "OK"))

        self._log(run_id, "run_evaluation", run_status)
        return self.return_run(run_id, criteria, ranked, run_status)

    def _evaluate_one_supplier(self, run_id: str, supplier: SupplierInput, criteria) -> FinalSupplierResult:
        base_kwargs = dict(
            supplier_name=supplier.supplier_name,
            submission_date=supplier.submission_date,
            experience_rating=supplier.experience_rating,
        )

        doc = self.extract_document(supplier)
        self._log(
            run_id, "extract_document", "warning" if doc.warning else "ok",
            supplier=supplier.supplier_name,
        )

        if not doc.full_text:
            return FinalSupplierResult(
                **base_kwargs,
                status="FAILED",
                extraction_warning=doc.warning or "No text extracted from document.",
                overall_summary="Evaluation could not proceed: document extraction failed.",
            )

        attempt = self.evaluate_supplier(run_id, supplier, doc.full_text, criteria)
        self._log(
            run_id, "evaluate_supplier", "ok" if attempt.parsed else "failed",
            supplier=supplier.supplier_name,
        )

        if attempt.parsed is None:
            return FinalSupplierResult(
                **base_kwargs,
                status="FAILED",
                extraction_warning=doc.warning,
                overall_summary=f"Evaluation failed: {attempt.error or 'LLM did not return valid JSON.'}",
            )

        evaluation, warnings = self.validate_evaluation(attempt.parsed, criteria)
        self._log(
            run_id, "validate_evaluation", "ok",
            supplier=supplier.supplier_name, warnings=len(warnings),
        )

        criterion_results, absolute_score = self.calculate_scores(evaluation, criteria)
        warning_criterion_ids = {w.criterion_id for w in warnings if w.criterion_id is not None}
        for cr in criterion_results:
            if cr.criterion_id in warning_criterion_ids:
                cr.validation_status = "WARNING"

        self._log(
            run_id, "calculate_scores", "ok",
            supplier=supplier.supplier_name, absolute_score=absolute_score,
        )

        return FinalSupplierResult(
            **base_kwargs,
            absolute_score=absolute_score,
            criteria=criterion_results,
            risks=evaluation.risks,
            overall_summary=evaluation.overall_summary,
            warnings=warnings,
            extraction_warning=doc.warning,
            status="OK",
        )
