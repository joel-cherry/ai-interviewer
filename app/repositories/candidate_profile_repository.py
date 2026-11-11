from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_profile import CandidateProfile
from app.repositories.base_repository import BaseRepository


class CandidateProfileRepository(BaseRepository[CandidateProfile]):
    model = CandidateProfile

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_user_id(self, user_id: UUID) -> list[CandidateProfile]:
        stmt = select(CandidateProfile).where(CandidateProfile.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
