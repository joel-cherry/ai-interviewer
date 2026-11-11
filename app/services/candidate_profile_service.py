from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_profile import CandidateProfile
from app.repositories.candidate_profile_repository import CandidateProfileRepository
from app.schemas.candidate_profile import CandidateProfileCreate, CandidateProfileUpdate


class CandidateProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = CandidateProfileRepository(session)

    async def create(self, payload: CandidateProfileCreate) -> CandidateProfile:
        candidate = CandidateProfile(
            user_id=payload.user_id,
            full_name=payload.full_name,
            headline=payload.headline,
            summary=payload.summary,
            location=payload.location,
            current_role=payload.current_role,
            years_experience=payload.years_experience,
        )
        return await self.repository.create(candidate)

    async def get_by_id(self, candidate_profile_id: UUID) -> CandidateProfile | None:
        return await self.repository.get_by_id(candidate_profile_id)

    async def get_by_user_id(self, user_id: UUID) -> list[CandidateProfile]:
        return await self.repository.get_by_user_id(user_id)

    async def list(self, *, offset: int = 0, limit: int | None = None) -> list[CandidateProfile]:
        return await self.repository.list(offset=offset, limit=limit)

    async def update(self, candidate_profile_id: UUID, payload: CandidateProfileUpdate) -> CandidateProfile | None:
        candidate = await self.repository.get_by_id(candidate_profile_id)
        if candidate is None:
            return None

        for field_name, value in payload.model_dump(exclude_unset=True).items():
            setattr(candidate, field_name, value)

        await self.repository.session.commit()
        await self.repository.session.refresh(candidate)
        return candidate

    async def delete(self, candidate_profile_id: UUID) -> bool:
        candidate = await self.repository.get_by_id(candidate_profile_id)
        if candidate is None:
            return False
        await self.repository.delete(candidate)
        return True
