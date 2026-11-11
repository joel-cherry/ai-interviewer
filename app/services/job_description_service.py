from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_description import JobDescription
from app.repositories.job_description_repository import JobDescriptionRepository

SKILL_KEYWORDS = [
    "python",
    "fastapi",
    "sqlalchemy",
    "postgresql",
    "docker",
    "aws",
    "kubernetes",
    "javascript",
    "typescript",
    "react",
    "node",
    "java",
    "csharp",
    "api",
    "sql",
    "microservices",
    "system design",
    "redis",
    "mongodb",
    "elasticsearch",
    "gcp",
    "linux",
    "ci/cd",
    "rest",
]


class JobDescriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = JobDescriptionRepository(session)

    async def create_for_candidate(
        self,
        *,
        candidate_profile_id: UUID,
        file_name: str,
        content_type: str | None,
        raw_text: str,
    ) -> JobDescription:
        title, summary, required_skills = self._parse_job_description(raw_text)
        job_description = JobDescription(
            candidate_profile_id=candidate_profile_id,
            file_name=file_name,
            content_type=content_type,
            raw_text=raw_text,
            title=title,
            summary=summary,
            required_skills=required_skills,
            required_experience_years=None,
            status="parsed",
        )
        return await self.repository.create(job_description)

    async def get_by_id(self, job_description_id: UUID) -> JobDescription | None:
        return await self.repository.get_by_id(job_description_id)

    async def list_for_candidate(self, candidate_profile_id: UUID) -> list[JobDescription]:
        return await self.repository.get_by_candidate_profile_id(candidate_profile_id)

    def match_resume(self, *, job_description: JobDescription, resume_skills: set[str]) -> dict[str, object]:
        normalized_resume = {skill.lower() for skill in resume_skills}
        required_skills = list(job_description.required_skills or [])
        required_lower = [skill.lower() for skill in required_skills]

        matched = sorted(
            {skill for skill in required_skills if skill.lower() in normalized_resume},
            key=lambda item: required_lower.index(item.lower()),
        )
        missing = sorted(
            {skill for skill in required_skills if skill.lower() not in normalized_resume},
            key=lambda item: required_lower.index(item.lower()),
        )
        score = len(matched) / len(required_skills) if required_skills else 0.0

        return {
            "job_description_id": job_description.id,
            "candidate_profile_id": job_description.candidate_profile_id,
            "overall_score": round(score, 2),
            "matched_skills": matched,
            "missing_skills": missing,
            "total_required_skills": len(required_skills),
            "resume_skill_count": len(normalized_resume),
        }

    @staticmethod
    def _parse_job_description(raw_text: str) -> tuple[str, str | None, list[str]]:
        normalized = raw_text.replace("\r", "")
        lines = [line.strip() for line in normalized.splitlines() if line.strip()]

        title = lines[0] if lines else "Job Description"
        summary = " ".join(lines[:5]) if lines else None

        skill_values = []
        lower_text = normalized.lower()
        for skill in SKILL_KEYWORDS:
            if skill in lower_text:
                skill_values.append(skill)

        required_skills = skill_values or ["general software engineering"]
        return title, summary, required_skills
