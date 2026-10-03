from __future__ import annotations

import os

from src.llm.base import LLMError, LLMProvider


class OpenAIProvider(LLMProvider):
    provider_name = "openai"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise LLMError("The 'openai' package is not installed.") from exc

        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("OPENAI_API_KEY is not set.")

        self._model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self._client = OpenAI(api_key=api_key)

    @property
    def model_name(self) -> str:
        return self._model

    def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                timeout=60,
            )
        except Exception as exc:  # noqa: BLE001 - any SDK failure must be contained
            raise LLMError(f"OpenAI call failed: {exc}") from exc
        return response.choices[0].message.content or ""
