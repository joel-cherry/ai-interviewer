from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript_entry import TranscriptEntry
from app.repositories.transcript_entry_repository import TranscriptEntryRepository
from app.schemas.transcript_entry import TranscriptEntryCreate, TranscriptEntryUpdate


class TranscriptEntryService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = TranscriptEntryRepository(session)

    async def create(self, payload: TranscriptEntryCreate) -> TranscriptEntry:
        transcript = TranscriptEntry(
            interview_session_id=payload.interview_session_id,
            sequence_number=payload.sequence_number,
            speaker=payload.speaker,
            content=payload.content,
        )
        return await self.repository.create(transcript)

    async def get_by_id(self, transcript_entry_id: UUID) -> TranscriptEntry | None:
        return await self.repository.get_by_id(transcript_entry_id)

    async def get_by_interview_session_id(self, interview_session_id: UUID) -> list[TranscriptEntry]:
        return await self.repository.get_by_interview_session_id(interview_session_id)

    async def update(self, transcript_entry_id: UUID, payload: TranscriptEntryUpdate) -> TranscriptEntry | None:
        transcript = await self.repository.get_by_id(transcript_entry_id)
        if transcript is None:
            return None

        for field_name, value in payload.model_dump(exclude_unset=True).items():
            setattr(transcript, field_name, value)

        await self.repository.session.commit()
        await self.repository.session.refresh(transcript)
        return transcript

    async def delete(self, transcript_entry_id: UUID) -> bool:
        transcript = await self.repository.get_by_id(transcript_entry_id)
        if transcript is None:
            return False
        await self.repository.delete(transcript)
        return True
