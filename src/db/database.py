from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.db.seed import DEFAULT_CRITERIA
from src.models.schemas import CriterionDefinition, CriterionResult, FinalSupplierResult, ValidationWarning

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()
        _seed_criteria_if_empty(conn)
    finally:
        conn.close()


def _seed_criteria_if_empty(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) FROM evaluation_criteria").fetchone()[0]
    if count > 0:
        return
    for c in DEFAULT_CRITERIA:
        conn.execute(
            "INSERT INTO evaluation_criteria (name, description, weight, max_score, is_active) "
            "VALUES (?, ?, ?, ?, ?)",
            (c["name"], c["description"], c["weight"], c["max_score"], 1),
        )
    conn.commit()


# ------------------------------------------------------------- criteria ----

def _row_to_criterion(row: sqlite3.Row) -> CriterionDefinition:
    return CriterionDefinition(
        criterion_id=row["criterion_id"],
        name=row["name"],
        description=row["description"],
        weight=row["weight"],
        max_score=row["max_score"],
        is_active=bool(row["is_active"]),
    )


def get_all_criteria(conn: sqlite3.Connection) -> list[CriterionDefinition]:
    rows = conn.execute("SELECT * FROM evaluation_criteria ORDER BY criterion_id").fetchall()
    return [_row_to_criterion(r) for r in rows]


def load_active_criteria(conn: sqlite3.Connection) -> list[CriterionDefinition]:
    rows = conn.execute(
        "SELECT * FROM evaluation_criteria WHERE is_active = 1 ORDER BY criterion_id"
    ).fetchall()
    return [_row_to_criterion(r) for r in rows]


def set_criterion_active(conn: sqlite3.Connection, criterion_id: int, is_active: bool) -> None:
    conn.execute(
        "UPDATE evaluation_criteria SET is_active = ? WHERE criterion_id = ?",
        (1 if is_active else 0, criterion_id),
    )
    conn.commit()


def set_criterion_weight(conn: sqlite3.Connection, criterion_id: int, weight: float) -> None:
    conn.execute(
        "UPDATE evaluation_criteria SET weight = ? WHERE criterion_id = ?",
        (weight, criterion_id),
    )
    conn.commit()


# ------------------------------------------------------------------ runs ---

def create_run(conn: sqlite3.Connection, *, run_id: str, status: str, llm_provider: str, llm_model: str, demo_mode: bool) -> None:
    conn.execute(
        "INSERT INTO rfp_runs (rfp_run_id, created_at, status, llm_provider, llm_model, demo_mode) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (run_id, datetime.now(timezone.utc).isoformat(), status, llm_provider, llm_model, int(demo_mode)),
    )
    conn.commit()


def update_run_status(conn: sqlite3.Connection, run_id: str, status: str) -> None:
    conn.execute("UPDATE rfp_runs SET status = ? WHERE rfp_run_id = ?", (status, run_id))
    conn.commit()


def save_supplier_result(conn: sqlite3.Connection, run_id: str, supplier: FinalSupplierResult) -> None:
    conn.execute(
        "INSERT INTO supplier_results (rfp_run_id, supplier_name, submission_date, "
        "experience_rating, absolute_score, ppi, final_rank, tie_break_notes, status, "
        "extraction_warning, result_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            run_id,
            supplier.supplier_name,
            supplier.submission_date.isoformat(),
            supplier.experience_rating,
            supplier.absolute_score,
            supplier.ppi,
            supplier.final_rank,
            supplier.tie_break_notes,
            supplier.status,
            supplier.extraction_warning,
            supplier.model_dump_json(),
        ),
    )


def save_criterion_results(conn: sqlite3.Connection, run_id: str, supplier_name: str, criteria: list[CriterionResult]) -> None:
    for cr in criteria:
        conn.execute(
            "INSERT INTO supplier_criterion_results (rfp_run_id, supplier_name, criterion_id, "
            "criterion_name, score, max_score, weight, benchmark, gap, relative_performance, "
            "evidence, justification, validation_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                supplier_name,
                cr.criterion_id,
                cr.name,
                cr.score,
                cr.max_score,
                cr.weight,
                cr.benchmark,
                cr.gap,
                cr.relative_performance,
                cr.evidence,
                cr.justification,
                cr.validation_status,
            ),
        )


def save_warnings(conn: sqlite3.Connection, run_id: str, supplier_name: str, warnings: list[ValidationWarning]) -> None:
    for w in warnings:
        conn.execute(
            "INSERT INTO run_warnings (rfp_run_id, supplier_name, warning_type, criterion_id, "
            "original_value, normalized_value, message) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                supplier_name,
                w.warning_type,
                w.criterion_id,
                w.original_value,
                w.normalized_value,
                w.message,
            ),
        )


def list_runs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT rfp_run_id, created_at, status, llm_provider, llm_model, demo_mode "
        "FROM rfp_runs ORDER BY created_at DESC"
    ).fetchall()


def fetch_run_suppliers(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM supplier_results WHERE rfp_run_id = ? ORDER BY "
        "CASE WHEN final_rank IS NULL THEN 1 ELSE 0 END, final_rank",
        (run_id,),
    ).fetchall()
    return [json.loads(r["result_json"]) for r in rows]


def fetch_run_warnings(conn: sqlite3.Connection, run_id: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM run_warnings WHERE rfp_run_id = ?", (run_id,)).fetchall()


def fetch_run_meta(conn: sqlite3.Connection, run_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM rfp_runs WHERE rfp_run_id = ?", (run_id,)).fetchone()
