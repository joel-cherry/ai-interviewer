from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobDescriptionBase(BaseModel):
    file_name: str = Field(..., max_length=255)
    content_type: str | None = Field(default=None, max_length=255)
    raw_text: str
    title: str = Field(..., max_length=255)
    summary: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    required_experience_years: int | None = Field(default=None, ge=0)
    status: str = "parsed"


class JobDescriptionRead(JobDescriptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    candidate_profile_id: UUID
    created_at: datetime
    updated_at: datetime


class JobDescriptionMatchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_description_id: UUID
    candidate_profile_id: UUID
    overall_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    total_required_skills: int
    resume_skill_count: int
