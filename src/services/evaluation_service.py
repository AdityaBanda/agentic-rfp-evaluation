from __future__ import annotations

import os
import sqlite3

from src.agents.orchestrator import RFPOrchestrator
from src.db import database as db
from src.llm.base import LLMError
from src.llm.demo_provider import DemoLLMProvider
from src.models.schemas import RFPRunResult, SupplierInput


class ConfigurationError(RuntimeError):
    """Raised when the configured LLM provider cannot be constructed (e.g. missing API key)."""


def is_demo_mode() -> bool:
    return os.environ.get("DEMO_MODE", "false").strip().lower() in {"1", "true", "yes"}


def get_llm_provider():
    """Build the configured LLM provider. Returns (provider, demo_mode)."""
    if is_demo_mode():
        return DemoLLMProvider(), True

    provider_name = os.environ.get("LLM_PROVIDER", "openai").strip().lower()

    if provider_name == "openai":
        from src.llm.openai_provider import OpenAIProvider

        try:
            return OpenAIProvider(), False
        except LLMError as exc:
            raise ConfigurationError(str(exc)) from exc

    if provider_name == "anthropic":
        from src.llm.anthropic_provider import AnthropicProvider

        try:
            return AnthropicProvider(), False
        except LLMError as exc:
            raise ConfigurationError(str(exc)) from exc

    raise ConfigurationError(f"Unknown LLM_PROVIDER '{provider_name}'. Use 'openai' or 'anthropic'.")


def run_evaluation(db_path: str, supplier_inputs: list[SupplierInput], on_event=None) -> RFPRunResult:
    """Entry point used by the Streamlit UI: resolves the LLM provider, opens the
    database, and runs the orchestrator's full agentic workflow.
    """
    provider, demo_mode = get_llm_provider()
    conn = db.get_connection(db_path)
    try:
        orchestrator = RFPOrchestrator(conn, provider, demo_mode=demo_mode, on_event=on_event)
        return orchestrator.run_evaluation(supplier_inputs)
    finally:
        conn.close()


def load_past_run(db_path: str, run_id: str) -> dict | None:
    """Reconstruct a lightweight summary of a previously persisted run, for
    browsing/downloading run history beyond the current session.
    """
    conn: sqlite3.Connection = db.get_connection(db_path)
    try:
        meta = db.fetch_run_meta(conn, run_id)
        if meta is None:
            return None
        suppliers = db.fetch_run_suppliers(conn, run_id)
        warnings = [dict(w) for w in db.fetch_run_warnings(conn, run_id)]
    finally:
        conn.close()

    return {
        "rfp_run_id": run_id,
        "created_at": meta["created_at"],
        "status": meta["status"],
        "llm_provider": meta["llm_provider"],
        "llm_model": meta["llm_model"],
        "demo_mode": bool(meta["demo_mode"]),
        "suppliers": suppliers,
        "warnings": warnings,
    }
