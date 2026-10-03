from __future__ import annotations

from abc import ABC, abstractmethod


class LLMError(RuntimeError):
    """Raised for missing configuration, timeouts, or provider-level failures."""


class LLMProvider(ABC):
    provider_name: str = "base"

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM and return raw text expected to be JSON (not yet parsed)."""
        ...
