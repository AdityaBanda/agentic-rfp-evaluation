from __future__ import annotations

import os

from src.llm.base import LLMError, LLMProvider


class AnthropicProvider(LLMProvider):
    provider_name = "anthropic"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise LLMError("The 'anthropic' package is not installed.") from exc

        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY is not set.")

        self._model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
        self._client = anthropic.Anthropic(api_key=api_key, timeout=60)

    @property
    def model_name(self) -> str:
        return self._model

    def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=2000,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except Exception as exc:  # noqa: BLE001 - any SDK failure must be contained
            raise LLMError(f"Anthropic call failed: {exc}") from exc
        parts = [block.text for block in response.content if getattr(block, "type", "") == "text"]
        return "".join(parts)
