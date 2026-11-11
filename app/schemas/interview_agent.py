from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StartInterviewRequest(BaseModel):
    title: str = Field(default="Technical Interview", min_length=1, max_length=255)
    candidate_profile_id: UUID | None = None


class StartInterviewResponse(BaseModel):
    session_id: UUID
    question: str
    status: str = "in_progress"
    turn_count: int = 1
    max_turns: int = 5


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1)


class SubmitAnswerResponse(BaseModel):
    session_id: UUID
    question: str | None = None
    status: str
    turn_count: int
    interview_complete: bool = False
    completion_summary: str | None = None


class InterviewStateResponse(BaseModel):
    current_stage: str = "not_started"
    turn_count: int = 0
    topics_covered: list[str] = Field(default_factory=list)
    topics_remaining: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    last_question: str | None = None
    interview_complete: bool = False


class TranscriptEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    interview_session_id: UUID
    sequence_number: int
    speaker: str
    content: str
    created_at: datetime


class TranscriptResponse(BaseModel):
    session_id: UUID
    entries: list[TranscriptEntryResponse]


class CompleteInterviewResponse(BaseModel):
    session_id: UUID
    status: str = "completed"
    summary: str | None = None
