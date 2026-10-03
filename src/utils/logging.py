from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def get_logger(name: str = "rfp_evaluator") -> logging.Logger:
    """Return a configured logger. Never pass API keys or other secrets to it."""
    global _CONFIGURED
    if not _CONFIGURED:
        root = logging.getLogger("rfp_evaluator")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        root.setLevel(logging.INFO)
        root.addHandler(handler)
        root.propagate = False
        _CONFIGURED = True
    return logging.getLogger(name)


def log_stage(logger: logging.Logger, *, rfp_run_id: str, stage: str, status: str, supplier: str | None = None, **fields) -> None:
    parts = [f"run={rfp_run_id}"]
    if supplier:
        parts.append(f"supplier={supplier}")
    parts.append(f"stage={stage}")
    parts.append(f"status={status}")
    for key, value in fields.items():
        parts.append(f"{key}={value}")
    logger.info(" ".join(parts))
