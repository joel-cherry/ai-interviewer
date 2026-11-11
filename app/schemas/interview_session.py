from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InterviewSessionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    status: str = Field(default="draft", max_length=50)
    summary: str | None = None
    max_turns: int = Field(default=5, ge=1, le=5)
    current_turn: int = Field(default=0, ge=0)
    interview_state: dict | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class InterviewSessionCreate(InterviewSessionBase):
    candidate_profile_id: UUID


class InterviewSessionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, max_length=50)
    summary: str | None = None
    max_turns: int | None = Field(default=None, ge=1, le=5)
    current_turn: int | None = Field(default=None, ge=0)
    interview_state: dict | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class InterviewSessionRead(InterviewSessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    candidate_profile_id: UUID
    created_at: datetime
    updated_at: datetime
