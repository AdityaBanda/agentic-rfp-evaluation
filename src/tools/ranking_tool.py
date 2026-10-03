from __future__ import annotations

from src.models.schemas import FinalSupplierResult, ValidationWarning


class RankingTool:
    """Deterministic peer benchmarking, PPI, and ranking with explicit tie-breaks.

    The LLM never ranks or scores suppliers against each other — all of that
    happens here, in plain Python, after LLM output has already been validated.
    """

    def calculate_benchmarks(self, suppliers: list[FinalSupplierResult]) -> None:
        valid = [s for s in suppliers if s.status == "OK"]

        best_by_criterion: dict[int, float] = {}
        for supplier in valid:
            for cr in supplier.criteria:
                current = best_by_criterion.get(cr.criterion_id)
                if current is None or cr.score > current:
                    best_by_criterion[cr.criterion_id] = cr.score

        for supplier in valid:
            for cr in supplier.criteria:
                benchmark = best_by_criterion.get(cr.criterion_id, 0.0)
                cr.benchmark = benchmark
                cr.gap = round(cr.score - benchmark, 2)
                if benchmark == 0:
                    cr.relative_performance = 0.0
                    cr.validation_status = "WARNING"
                    supplier.warnings.append(
                        ValidationWarning(
                            warning_type="ZERO_BENCHMARK",
                            criterion_id=cr.criterion_id,
                            message=(
                                f"Benchmark for '{cr.name}' is 0 (no supplier scored above 0 on "
                                "this criterion in this run). Relative performance set to 0."
                            ),
                        )
                    )
                else:
                    cr.relative_performance = round((cr.score / benchmark) * 100, 2)

    def calculate_ppi(self, suppliers: list[FinalSupplierResult]) -> None:
        """Peer Performance Index: weighted average of relative-performance %."""
        for supplier in suppliers:
            if supplier.status != "OK" or not supplier.criteria:
                supplier.ppi = 0.0
                continue
            weight_sum = sum(cr.weight for cr in supplier.criteria)
            if weight_sum == 0:
                supplier.ppi = 0.0
                continue
            weighted = sum((cr.relative_performance or 0.0) * cr.weight for cr in supplier.criteria)
            supplier.ppi = round(weighted / weight_sum, 2)

    def rank(self, suppliers: list[FinalSupplierResult]) -> list[FinalSupplierResult]:
        """Mandatory tie-break order:
        1) higher PPI, 2) earlier submission date, 3) higher experience rating,
        4) supplier name ascending. Ranks are assigned only after this complete
        stable sort. Failed suppliers are never ranked.
        """
        ranked_pool = [s for s in suppliers if s.status == "OK"]
        failed_pool = [s for s in suppliers if s.status != "OK"]

        ranked_pool.sort(
            key=lambda s: (
                -s.ppi,
                s.submission_date,
                -s.experience_rating,
                s.supplier_name.lower(),
            )
        )

        for index, supplier in enumerate(ranked_pool, start=1):
            supplier.final_rank = index
            supplier.tie_break_notes = (
                f"Ranked #{index} by PPI ({supplier.ppi}). Tie-break order applied: "
                "1) higher PPI, 2) earlier submission date, 3) higher experience rating, "
                "4) supplier name (A-Z)."
            )

        for supplier in failed_pool:
            supplier.final_rank = None
            supplier.tie_break_notes = "Not ranked: evaluation failed for this supplier."

        return ranked_pool + failed_pool
