from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResumeDocumentBase(BaseModel):
    file_name: str = Field(..., max_length=255)
    content_type: str | None = Field(default=None, max_length=255)
    file_size_bytes: int = Field(default=0, ge=0)
    raw_text: str
    extracted_summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: int | None = Field(default=None, ge=0)
    status: str = "parsed"


class ResumeDocumentRead(ResumeDocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    candidate_profile_id: UUID
    created_at: datetime
    updated_at: datetime
