from datetime import date

from src.models.schemas import CriterionResult, FinalSupplierResult
from src.tools.ranking_tool import RankingTool


def _supplier(name, score, submission_date=date(2026, 1, 1), experience_rating=5, weight=30):
    criteria = [CriterionResult(criterion_id=1, name="Technical", score=score, max_score=10, weight=weight)]
    return FinalSupplierResult(
        supplier_name=name,
        submission_date=submission_date,
        experience_rating=experience_rating,
        criteria=criteria,
        status="OK",
    )


def test_benchmark_and_relative_performance():
    a = _supplier("A", 8)
    b = _supplier("B", 10)
    RankingTool().calculate_benchmarks([a, b])

    assert a.criteria[0].benchmark == 10
    assert a.criteria[0].gap == -2
    assert a.criteria[0].relative_performance == 80.0

    assert b.criteria[0].benchmark == 10
    assert b.criteria[0].gap == 0
    assert b.criteria[0].relative_performance == 100.0


def test_zero_benchmark_handling():
    a = _supplier("A", 0)
    RankingTool().calculate_benchmarks([a])
    assert a.criteria[0].benchmark == 0
    assert a.criteria[0].relative_performance == 0.0
    assert any(w.warning_type == "ZERO_BENCHMARK" for w in a.warnings)


def test_ppi_weighted_average():
    supplier = _supplier("A", 8, weight=30)
    supplier.criteria[0].relative_performance = 80.0
    supplier.criteria.append(
        CriterionResult(criterion_id=2, name="Plan", score=5, max_score=10, weight=70, relative_performance=50.0)
    )
    RankingTool().calculate_ppi([supplier])
    # (80*30 + 50*70) / 100 = (2400 + 3500) / 100 = 59
    assert supplier.ppi == 59.0


def test_tie_break_order_earlier_submission_wins_over_experience():
    # Both suppliers have equal PPI; A submitted earlier but has lower experience.
    # Per the mandated tie-break order, submission date is checked before experience.
    a = _supplier("Alpha", 8, submission_date=date(2026, 9, 20), experience_rating=8)
    b = _supplier("Bravo", 8, submission_date=date(2026, 9, 21), experience_rating=10)
    a.ppi = 90.0
    b.ppi = 90.0

    ranked = RankingTool().rank([b, a])

    assert [s.supplier_name for s in ranked] == ["Alpha", "Bravo"]
    assert ranked[0].final_rank == 1
    assert ranked[1].final_rank == 2


def test_tie_break_falls_through_to_name_when_all_else_equal():
    a = _supplier("Zeta", 8, submission_date=date(2026, 1, 1), experience_rating=5)
    b = _supplier("Alpha", 8, submission_date=date(2026, 1, 1), experience_rating=5)
    a.ppi = 75.0
    b.ppi = 75.0

    ranked = RankingTool().rank([a, b])

    assert [s.supplier_name for s in ranked] == ["Alpha", "Zeta"]


def test_higher_ppi_ranks_first():
    a = _supplier("A", 8)
    b = _supplier("B", 8)
    a.ppi = 60.0
    b.ppi = 90.0

    ranked = RankingTool().rank([a, b])

    assert ranked[0].supplier_name == "B"
    assert ranked[0].final_rank == 1


def test_failed_suppliers_ranked_last_and_unranked():
    ok = _supplier("Alpha", 8)
    ok.ppi = 90.0
    failed = FinalSupplierResult(
        supplier_name="Failed Co",
        submission_date=date(2026, 9, 20),
        experience_rating=5,
        status="FAILED",
    )

    ranked = RankingTool().rank([failed, ok])

    assert ranked[0].supplier_name == "Alpha"
    assert ranked[0].final_rank == 1
    assert ranked[1].supplier_name == "Failed Co"
    assert ranked[1].final_rank is None
