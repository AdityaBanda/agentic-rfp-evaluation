from __future__ import annotations

from src.models.schemas import CriterionDefinition, CriterionEvaluation, SupplierEvaluation, ValidationWarning


class ValidationTool:
    """Deterministically validates and normalizes a raw LLM evaluation.

    Guarantees the caller always gets exactly one CriterionEvaluation per active
    criterion, with a numeric, in-range score — regardless of what the LLM
    actually returned. Every correction is recorded as a ValidationWarning.
    """

    def validate(
        self, raw: dict, active_criteria: list[CriterionDefinition]
    ) -> tuple[SupplierEvaluation, list[ValidationWarning]]:
        warnings: list[ValidationWarning] = []
        supplier_name = str(raw.get("supplier_name") or "Unknown Supplier")

        raw_criteria = raw.get("criteria")
        if not isinstance(raw_criteria, list):
            raw_criteria = []

        active_ids = {c.criterion_id for c in active_criteria}
        by_id: dict[int, dict] = {}
        for entry in raw_criteria:
            if not isinstance(entry, dict):
                continue
            cid = entry.get("criterion_id")
            try:
                cid = int(cid)
            except (TypeError, ValueError):
                continue

            if cid not in active_ids:
                warnings.append(
                    ValidationWarning(
                        warning_type="UNKNOWN_CRITERION",
                        criterion_id=cid,
                        message=f"LLM returned a result for criterion_id {cid}, which is not an active criterion. Ignored.",
                    )
                )
                continue

            if cid in by_id:
                warnings.append(
                    ValidationWarning(
                        warning_type="DUPLICATE_CRITERION",
                        criterion_id=cid,
                        message=f"LLM returned multiple results for criterion_id {cid}. Using the first.",
                    )
                )
                continue

            by_id[cid] = entry

        normalized: list[CriterionEvaluation] = []
        for criterion in active_criteria:
            entry = by_id.get(criterion.criterion_id)

            if entry is None:
                warnings.append(
                    ValidationWarning(
                        warning_type="MISSING_CRITERION",
                        criterion_id=criterion.criterion_id,
                        original_value=None,
                        normalized_value="0",
                        message=f"No result returned for '{criterion.name}'. Defaulted score to 0.",
                    )
                )
                normalized.append(
                    CriterionEvaluation(
                        criterion_id=criterion.criterion_id,
                        score=0.0,
                        max_score=criterion.max_score,
                        justification="No evaluation was returned by the LLM for this criterion.",
                        evidence="",
                    )
                )
                continue

            raw_score = entry.get("score")
            try:
                score = float(raw_score)
            except (TypeError, ValueError):
                warnings.append(
                    ValidationWarning(
                        warning_type="INVALID_SCORE_TYPE",
                        criterion_id=criterion.criterion_id,
                        original_value=str(raw_score),
                        normalized_value="0",
                        message=f"Non-numeric score '{raw_score}' for '{criterion.name}'. Defaulted to 0.",
                    )
                )
                score = 0.0

            clipped = min(max(score, 0.0), criterion.max_score)
            if clipped != score:
                warnings.append(
                    ValidationWarning(
                        warning_type="OUT_OF_RANGE_SCORE",
                        criterion_id=criterion.criterion_id,
                        original_value=str(score),
                        normalized_value=str(clipped),
                        message=(
                            f"Score {score} for '{criterion.name}' out of range "
                            f"[0, {criterion.max_score}]. Clipped to {clipped}."
                        ),
                    )
                )

            normalized.append(
                CriterionEvaluation(
                    criterion_id=criterion.criterion_id,
                    score=clipped,
                    max_score=criterion.max_score,
                    justification=str(entry.get("justification") or ""),
                    evidence=str(entry.get("evidence") or ""),
                )
            )

        risks = raw.get("risks")
        risks = [str(r) for r in risks] if isinstance(risks, list) else []
        overall_summary = str(raw.get("overall_summary") or "")

        evaluation = SupplierEvaluation(
            supplier_name=supplier_name,
            criteria=normalized,
            risks=risks,
            overall_summary=overall_summary,
        )
        return evaluation, warnings
