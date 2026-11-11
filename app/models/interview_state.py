from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class InterviewState(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str = "not_started"
    current_turn: int = 0
    max_turns: int = 5
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    last_question: str | None = None
    last_answer: str | None = None
    completed: bool = False
    summary: str | None = None

    def add_exchange(self, *, question: str, answer: str) -> None:
        self.conversation_history.append({"question": question, "answer": answer})
        self.current_turn += 1
        self.last_question = question
        self.last_answer = answer
        if self.current_turn >= self.max_turns:
            self.completed = True
            self.status = "completed"
        else:
            self.status = "in_progress"

    def mark_started(self) -> None:
        self.status = "in_progress"

    def mark_completed(self, summary: str | None = None) -> None:
        self.status = "completed"
        self.completed = True
        self.summary = summary

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
