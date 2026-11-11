from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_interview_question(
        self,
        *,
        prompt: str,
        context: dict[str, object] | None = None,
    ) -> str:
        """Generate the next interview question based on prompt and context."""

    @abstractmethod
    async def generate_follow_up_question(
        self,
        *,
        prompt: str,
        context: dict[str, object] | None = None,
    ) -> str:
        """Generate a follow-up question after a candidate answer."""

    @abstractmethod
    async def generate_response(self, *, prompt: str, context: dict[str, object] | None = None) -> str:
        """Generate a generic text response with structured prompt and context."""
