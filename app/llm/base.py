from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict[str, str]]) -> str:
        """Generate a textual response from a message list."""

    @abstractmethod
    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        schema: type[Any],
    ) -> Any:
        """Generate a response that conforms to a structured schema."""
