from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TranscriptEntryBase(BaseModel):
    sequence_number: int = Field(..., ge=1)
    speaker: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1)


class TranscriptEntryCreate(TranscriptEntryBase):
    interview_session_id: UUID


class TranscriptEntryUpdate(BaseModel):
    sequence_number: int | None = Field(default=None, ge=1)
    speaker: str | None = Field(default=None, min_length=1, max_length=50)
    content: str | None = Field(default=None, min_length=1)


class TranscriptEntryRead(TranscriptEntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    interview_session_id: UUID
    created_at: datetime
    updated_at: datetime
