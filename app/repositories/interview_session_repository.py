from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview_session import InterviewSession
from app.repositories.base_repository import BaseRepository


class InterviewSessionRepository(BaseRepository[InterviewSession]):
    model = InterviewSession

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_candidate_profile_id(self, candidate_profile_id: UUID) -> list[InterviewSession]:
        stmt = select(InterviewSession).where(InterviewSession.candidate_profile_id == candidate_profile_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
