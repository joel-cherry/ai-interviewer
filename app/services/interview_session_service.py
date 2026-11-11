from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview_session import InterviewSession
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.schemas.interview_session import InterviewSessionCreate, InterviewSessionUpdate


class InterviewSessionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = InterviewSessionRepository(session)

    async def create(self, payload: InterviewSessionCreate) -> InterviewSession:
        session = InterviewSession(
            candidate_profile_id=payload.candidate_profile_id,
            title=payload.title,
            status=payload.status,
            summary=payload.summary,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
        )
        return await self.repository.create(session)

    async def get_by_id(self, interview_session_id: UUID) -> InterviewSession | None:
        return await self.repository.get_by_id(interview_session_id)

    async def get_by_candidate_profile_id(self, candidate_profile_id: UUID) -> list[InterviewSession]:
        return await self.repository.get_by_candidate_profile_id(candidate_profile_id)

    async def update(self, interview_session_id: UUID, payload: InterviewSessionUpdate) -> InterviewSession | None:
        interview_session = await self.repository.get_by_id(interview_session_id)
        if interview_session is None:
            return None

        for field_name, value in payload.model_dump(exclude_unset=True).items():
            setattr(interview_session, field_name, value)

        interview_session.updated_at = datetime.now(timezone.utc)
        await self.repository.session.commit()
        await self.repository.session.refresh(interview_session)
        return interview_session

    async def delete(self, interview_session_id: UUID) -> bool:
        interview_session = await self.repository.get_by_id(interview_session_id)
        if interview_session is None:
            return False
        await self.repository.delete(interview_session)
        return True
