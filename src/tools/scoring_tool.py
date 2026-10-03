from __future__ import annotations

from src.models.schemas import CriterionDefinition, CriterionResult, SupplierEvaluation


class ScoringTool:
    """Deterministic weighted scoring. The LLM never performs this arithmetic."""

    def score_supplier(
        self, evaluation: SupplierEvaluation, criteria: list[CriterionDefinition]
    ) -> tuple[list[CriterionResult], float]:
        criteria_by_id = {c.criterion_id: c for c in criteria}
        results: list[CriterionResult] = []
        absolute_score = 0.0

        for ce in evaluation.criteria:
            definition = criteria_by_id[ce.criterion_id]
            contribution = (ce.score / definition.max_score) * definition.weight if definition.max_score else 0.0
            absolute_score += contribution
            results.append(
                CriterionResult(
                    criterion_id=definition.criterion_id,
                    name=definition.name,
                    score=ce.score,
                    max_score=definition.max_score,
                    weight=definition.weight,
                    evidence=ce.evidence,
                    justification=ce.justification,
                )
            )

        return results, round(absolute_score, 2)
