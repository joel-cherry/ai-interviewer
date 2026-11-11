from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self.model = model or settings.openai_model

    async def generate(self, messages: list[dict[str, str]]) -> str:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=220,
        )
        return str(response.choices[0].message.content or "").strip()

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        schema: type[Any],
    ) -> Any:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        response = await self.client.responses.create(
            model=self.model,
            input=messages,
            response_format=schema,
        )

        output = response.output_text
        if not output:
            return schema()
        return schema.model_validate_json(output)
