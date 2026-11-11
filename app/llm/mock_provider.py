from __future__ import annotations

from typing import Any

from app.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    _questions: list[str] = [
        "Tell me about yourself.",
        "Can you tell me more about your technical background?",
        "What project are you most proud of?",
        "What challenges did you face in that project?",
        "What would you improve if you rebuilt it today?",
    ]

    async def generate(self, messages: list[dict[str, str]]) -> str:
        if not messages:
            return "Tell me about yourself."

        last_user_message = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "Tell me about yourself.",
        )

        if "turn" in last_user_message.lower() or "next" in last_user_message.lower():
            return self._questions[0]

        if "background" in last_user_message.lower():
            return self._questions[2]

        if "project" in last_user_message.lower() or "proud" in last_user_message.lower():
            return self._questions[3]

        if "challenges" in last_user_message.lower() or "faced" in last_user_message.lower():
            return self._questions[4]

        return self._questions[0]

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        schema: type[Any],
    ) -> Any:
        if hasattr(schema, "model_validate"):
            return schema.model_validate({})
        return schema()
