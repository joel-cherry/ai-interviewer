from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.providers.base_provider import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self.model = model or settings.openai_model

    async def generate_interview_question(
        self,
        *,
        prompt: str,
        context: dict[str, object] | None = None,
    ) -> str:
        if not settings.openai_api_key:
            return self._fallback_question(prompt, context)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a professional interviewer. Ask exactly one focused interview question."},
                {"role": "user", "content": prompt + (self._format_context(context) if context else "")},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        return str(response.choices[0].message.content or "").strip()

    async def generate_follow_up_question(
        self,
        *,
        prompt: str,
        context: dict[str, object] | None = None,
    ) -> str:
        if not settings.openai_api_key:
            return self._fallback_follow_up(prompt, context)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a professional interviewer. Ask one concise, relevant follow-up question or move to the next question if the answer is complete."},
                {"role": "user", "content": prompt + (self._format_context(context) if context else "")},
            ],
            temperature=0.8,
            max_tokens=220,
        )
        return str(response.choices[0].message.content or "").strip()

    async def generate_response(self, *, prompt: str, context: dict[str, object] | None = None) -> str:
        if not settings.openai_api_key:
            return self._fallback_summary(prompt, context)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful interview coaching assistant."},
                {"role": "user", "content": prompt + (self._format_context(context) if context else "")},
            ],
            temperature=0.6,
            max_tokens=300,
        )
        return str(response.choices[0].message.content or "").strip()

    @staticmethod
    def _fallback_question(prompt: str, context: dict[str, object] | None = None) -> str:
        if context and "turn" in context:
            return f"For the {context['turn']}th step of this interview, tell me about a project where you had to solve an ambiguous problem and explain your decision-making."
        return "Tell me about a project where you had to solve an ambiguous problem and explain the trade-offs you considered."

    @staticmethod
    def _fallback_follow_up(prompt: str, context: dict[str, object] | None = None) -> str:
        if context and "turn" in context:
            return f"On your {context['turn']}th turn, what specific outcome did you measure, and how did you know your approach worked?"
        return "What specific outcome did you measure, and how did you know your approach worked?"

    @staticmethod
    def _fallback_summary(prompt: str, context: dict[str, object] | None = None) -> str:
        return "This interview covered the candidate's experience, technical decisions, and impact. The response is a local fallback summary for offline or unconfigured environments."

    @staticmethod
    def _format_context(context: dict[str, Any] | None) -> str:
        if not context:
            return ""
        formatted_items: list[str] = []
        for key, value in context.items():
            formatted_items.append(f"\n{key}: {value}")
        return "\nContext:\n" + "\n".join(formatted_items)
