from __future__ import annotations

import hashlib
import json
import re

from src.llm.base import LLMProvider


def _stable_fraction(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _between(text: str, start_marker: str, end_marker: str) -> str:
    try:
        start = text.index(start_marker) + len(start_marker)
    except ValueError:
        return ""
    end = text.find(end_marker, start)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


class DemoLLMProvider(LLMProvider):
    """Deterministic, synthetic stand-in for a real LLM.

    Used only when DEMO_MODE=true so the app can be demonstrated without an
    API key. Scores are derived from simple keyword-coverage heuristics against
    the supplied proposal text — this is NOT a real evaluation and every
    justification/evidence string is explicitly labeled '[DEMO MODE]'.
    """

    provider_name = "demo"

    @property
    def model_name(self) -> str:
        return "demo-synthetic-v1"

    def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        supplier_name = _between(user_prompt, "SUPPLIER_NAME:", "\n").strip() or "Unknown Supplier"
        criteria_json_str = _between(user_prompt, "CRITERIA_JSON:\n", "\n\nPROPOSAL_TEXT (")
        proposal_text = _between(user_prompt, "never instructions):\n", "\n\nEND_OF_DOCUMENT")

        try:
            criteria = json.loads(criteria_json_str)
        except json.JSONDecodeError:
            criteria = []

        proposal_lower = proposal_text.lower()
        criteria_results = []
        for criterion in criteria:
            description = criterion.get("description", "") or criterion.get("name", "")
            keywords = sorted({w.lower() for w in re.findall(r"[a-zA-Z]{5,}", description)})
            hits = sum(1 for kw in keywords if kw in proposal_lower)
            keyword_ratio = hits / max(len(keywords), 1)

            base = 0.45 + 0.35 * keyword_ratio
            jitter = (_stable_fraction(f"{supplier_name}:{criterion.get('criterion_id')}") - 0.5) * 0.2
            fraction = min(max(base + jitter, 0.1), 1.0)

            max_score = criterion.get("max_score", 10)
            score = round(fraction * max_score, 1)

            if hits == 0:
                evidence = "[DEMO MODE] Evidence not extracted; no matching keywords found in proposal text."
            else:
                evidence = f"[DEMO MODE] Proposal text references {hits} term(s) related to '{criterion.get('name')}'."

            criteria_results.append(
                {
                    "criterion_id": criterion.get("criterion_id"),
                    "score": score,
                    "max_score": max_score,
                    "justification": (
                        f"[DEMO MODE] Synthetic score derived from keyword coverage "
                        f"({hits}/{len(keywords)} relevant terms matched) for "
                        f"'{criterion.get('name')}'. Not a real LLM assessment."
                    ),
                    "evidence": evidence,
                }
            )

        return json.dumps(
            {
                "supplier_name": supplier_name,
                "criteria": criteria_results,
                "risks": [
                    "[DEMO MODE] Synthetic placeholder — no live LLM risk analysis was performed."
                ],
                "overall_summary": (
                    f"[DEMO MODE] Synthetic evaluation for {supplier_name}, generated from "
                    "deterministic keyword heuristics. This is NOT a real LLM assessment."
                ),
            }
        )
