from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume_document import ResumeDocument
from app.repositories.resume_document_repository import ResumeDocumentRepository


class ResumeDocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = ResumeDocumentRepository(session)

    async def create_for_candidate(
        self,
        *,
        candidate_profile_id: UUID,
        file_name: str,
        content_type: str | None,
        raw_text: str,
    ) -> ResumeDocument:
        summary, skills, experience_years = self._parse_resume(raw_text)

        resume = ResumeDocument(
            candidate_profile_id=candidate_profile_id,
            file_name=file_name,
            content_type=content_type,
            file_size_bytes=len(raw_text.encode("utf-8")),
            raw_text=raw_text,
            extracted_summary=summary,
            skills=skills,
            experience_years=experience_years,
            status="parsed",
        )
        return await self.repository.create(resume)

    async def list_for_candidate(self, candidate_profile_id: UUID) -> list[ResumeDocument]:
        return await self.repository.get_by_candidate_profile_id(candidate_profile_id)

    @staticmethod
    def _parse_resume(raw_text: str) -> tuple[str | None, list[str], int | None]:
        normalized = raw_text.replace("\r", "")
        text = " ".join(normalized.split())

        summary_match = re.search(r"Professional Summary:(.*?)(?:Experience:|Skills:|$)", text, flags=re.IGNORECASE | re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else text[:500].strip()

        skill_keywords = [
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
        ]

        found_skills = []
        lower_text = text.lower()
        for skill in skill_keywords:
            if skill in lower_text:
                found_skills.append(skill)

        skills = found_skills or ["general software engineering"]

        years_match = re.search(r"(\d+)\s+years?\s+(?:of\s+)?experience", text, flags=re.IGNORECASE)
        experience_years = int(years_match.group(1)) if years_match else None

        return summary or None, skills, experience_years
