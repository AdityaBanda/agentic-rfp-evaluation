from src.models.schemas import CriterionDefinition, CriterionEvaluation, SupplierEvaluation
from src.tools.scoring_tool import ScoringTool


def _criteria():
    return [
        CriterionDefinition(criterion_id=1, name="Technical", description="d", weight=30, max_score=10),
        CriterionDefinition(criterion_id=2, name="Plan", description="d", weight=20, max_score=10),
        CriterionDefinition(criterion_id=3, name="Commercial", description="d", weight=20, max_score=10),
        CriterionDefinition(criterion_id=4, name="Security", description="d", weight=20, max_score=10),
        CriterionDefinition(criterion_id=5, name="Support", description="d", weight=10, max_score=10),
    ]


def test_absolute_weighted_score():
    criteria = _criteria()
    evaluation = SupplierEvaluation(
        supplier_name="Test Co",
        criteria=[
            CriterionEvaluation(criterion_id=1, score=8, max_score=10),
            CriterionEvaluation(criterion_id=2, score=10, max_score=10),
            CriterionEvaluation(criterion_id=3, score=5, max_score=10),
            CriterionEvaluation(criterion_id=4, score=10, max_score=10),
            CriterionEvaluation(criterion_id=5, score=6, max_score=10),
        ],
    )
    results, absolute_score = ScoringTool().score_supplier(evaluation, criteria)
    # 8/10*30 + 10/10*20 + 5/10*20 + 10/10*20 + 6/10*10 = 24+20+10+20+6 = 80
    assert absolute_score == 80.0
    assert len(results) == 5


def test_single_criterion_contribution():
    criteria = [CriterionDefinition(criterion_id=1, name="Technical", description="d", weight=30, max_score=10)]
    evaluation = SupplierEvaluation(
        supplier_name="Test Co",
        criteria=[CriterionEvaluation(criterion_id=1, score=8, max_score=10)],
    )
    _, absolute_score = ScoringTool().score_supplier(evaluation, criteria)
    assert absolute_score == 24.0
