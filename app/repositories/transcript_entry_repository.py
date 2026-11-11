from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript_entry import TranscriptEntry
from app.repositories.base_repository import BaseRepository


class TranscriptEntryRepository(BaseRepository[TranscriptEntry]):
    model = TranscriptEntry

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_interview_session_id(self, interview_session_id: UUID) -> list[TranscriptEntry]:
        stmt = select(TranscriptEntry).where(TranscriptEntry.interview_session_id == interview_session_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
