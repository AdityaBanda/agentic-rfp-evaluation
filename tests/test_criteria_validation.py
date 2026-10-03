import pytest

from src.models.schemas import CriterionDefinition
from src.tools.criteria_validation import CriteriaWeightError, validate_weights_sum_to_100


def test_weights_sum_to_100_passes():
    criteria = [
        CriterionDefinition(criterion_id=1, name="A", description="d", weight=60, max_score=10),
        CriterionDefinition(criterion_id=2, name="B", description="d", weight=40, max_score=10),
    ]
    assert validate_weights_sum_to_100(criteria) == 100.0


def test_weights_not_summing_to_100_raises():
    criteria = [
        CriterionDefinition(criterion_id=1, name="A", description="d", weight=60, max_score=10),
        CriterionDefinition(criterion_id=2, name="B", description="d", weight=30, max_score=10),
    ]
    with pytest.raises(CriteriaWeightError):
        validate_weights_sum_to_100(criteria)


def test_no_active_criteria_raises():
    with pytest.raises(CriteriaWeightError):
        validate_weights_sum_to_100([])
