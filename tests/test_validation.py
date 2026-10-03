from src.models.schemas import CriterionDefinition
from src.tools.validation_tool import ValidationTool


def _criteria():
    return [
        CriterionDefinition(criterion_id=1, name="Technical", description="d", weight=50, max_score=10),
        CriterionDefinition(criterion_id=2, name="Plan", description="d", weight=50, max_score=10),
    ]


def test_missing_criterion_defaults_to_zero():
    raw = {"supplier_name": "X", "criteria": [{"criterion_id": 1, "score": 7}]}
    evaluation, warnings = ValidationTool().validate(raw, _criteria())
    scores = {c.criterion_id: c.score for c in evaluation.criteria}
    assert scores[2] == 0
    assert any(w.warning_type == "MISSING_CRITERION" for w in warnings)


def test_out_of_range_score_is_clipped():
    raw = {
        "supplier_name": "X",
        "criteria": [
            {"criterion_id": 1, "score": 14},
            {"criterion_id": 2, "score": -3},
        ],
    }
    evaluation, warnings = ValidationTool().validate(raw, _criteria())
    scores = {c.criterion_id: c.score for c in evaluation.criteria}
    assert scores[1] == 10
    assert scores[2] == 0
    assert sum(1 for w in warnings if w.warning_type == "OUT_OF_RANGE_SCORE") == 2


def test_duplicate_criterion_uses_first_and_warns():
    raw = {
        "supplier_name": "X",
        "criteria": [
            {"criterion_id": 1, "score": 5},
            {"criterion_id": 1, "score": 9},
            {"criterion_id": 2, "score": 6},
        ],
    }
    evaluation, warnings = ValidationTool().validate(raw, _criteria())
    scores = {c.criterion_id: c.score for c in evaluation.criteria}
    assert scores[1] == 5
    assert any(w.warning_type == "DUPLICATE_CRITERION" for w in warnings)


def test_unknown_criterion_is_ignored_and_warned():
    raw = {
        "supplier_name": "X",
        "criteria": [
            {"criterion_id": 1, "score": 5},
            {"criterion_id": 2, "score": 6},
            {"criterion_id": 99, "score": 10},
        ],
    }
    evaluation, warnings = ValidationTool().validate(raw, _criteria())
    assert {c.criterion_id for c in evaluation.criteria} == {1, 2}
    assert any(w.warning_type == "UNKNOWN_CRITERION" for w in warnings)


def test_non_numeric_score_defaults_to_zero():
    raw = {
        "supplier_name": "X",
        "criteria": [
            {"criterion_id": 1, "score": "high"},
            {"criterion_id": 2, "score": 6},
        ],
    }
    evaluation, warnings = ValidationTool().validate(raw, _criteria())
    scores = {c.criterion_id: c.score for c in evaluation.criteria}
    assert scores[1] == 0
    assert any(w.warning_type == "INVALID_SCORE_TYPE" for w in warnings)


def test_exactly_one_result_per_active_criterion_regardless_of_llm_output():
    raw = {
        "supplier_name": "X",
        "criteria": [
            {"criterion_id": 1, "score": 5},
            {"criterion_id": 1, "score": 9},
            {"criterion_id": 99, "score": 10},
        ],
    }
    evaluation, _ = ValidationTool().validate(raw, _criteria())
    assert len(evaluation.criteria) == len(_criteria())
