from __future__ import annotations

from src.models.schemas import CriterionDefinition


class CriteriaWeightError(ValueError):
    """Raised when active criteria weights do not sum to 100%, or none are active."""


def validate_weights_sum_to_100(criteria: list[CriterionDefinition], tolerance: float = 0.01) -> float:
    """Return the total active weight, or raise CriteriaWeightError.

    This is the single source of truth for the "weights must sum to 100%" rule,
    used by both the orchestrator (to block evaluation) and the Streamlit UI
    (to show a live validation message).
    """
    if not criteria:
        raise CriteriaWeightError("No active evaluation criteria are configured.")

    total = sum(c.weight for c in criteria)
    if abs(total - 100.0) > tolerance:
        raise CriteriaWeightError(
            f"Active criteria weights sum to {total:.2f}%, not 100%. "
            "Adjust weights before running an evaluation."
        )
    return total
