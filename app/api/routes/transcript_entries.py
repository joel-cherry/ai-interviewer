from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.transcript_entry import TranscriptEntryCreate, TranscriptEntryRead, TranscriptEntryUpdate
from app.services.transcript_entry_service import TranscriptEntryService

router = APIRouter(prefix="/transcript-entries", tags=["transcript-entries"])


@router.post("", response_model=TranscriptEntryRead, status_code=status.HTTP_201_CREATED)
async def create_transcript_entry(
    payload: TranscriptEntryCreate,
    db: AsyncSession = Depends(get_db),
) -> TranscriptEntryRead:
    service = TranscriptEntryService(db)
    transcript_entry = await service.create(payload)
    return TranscriptEntryRead.model_validate(transcript_entry)


@router.get("", response_model=list[TranscriptEntryRead])
async def list_transcript_entries(
    db: AsyncSession = Depends(get_db),
    interview_session_id: UUID | None = Query(default=None),
    offset: int = 0,
    limit: int = 100,
) -> list[TranscriptEntryRead]:
    service = TranscriptEntryService(db)
    if interview_session_id is not None:
        transcript_entries = await service.get_by_interview_session_id(interview_session_id)
    else:
        transcript_entries = await service.repository.list(offset=offset, limit=limit)
    return [TranscriptEntryRead.model_validate(item) for item in transcript_entries]


@router.get("/{transcript_entry_id}", response_model=TranscriptEntryRead)
async def get_transcript_entry(transcript_entry_id: UUID, db: AsyncSession = Depends(get_db)) -> TranscriptEntryRead:
    service = TranscriptEntryService(db)
    transcript_entry = await service.get_by_id(transcript_entry_id)
    if transcript_entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript entry not found")
    return TranscriptEntryRead.model_validate(transcript_entry)


@router.put("/{transcript_entry_id}", response_model=TranscriptEntryRead)
async def update_transcript_entry(
    transcript_entry_id: UUID,
    payload: TranscriptEntryUpdate,
    db: AsyncSession = Depends(get_db),
) -> TranscriptEntryRead:
    service = TranscriptEntryService(db)
    transcript_entry = await service.update(transcript_entry_id, payload)
    if transcript_entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript entry not found")
    return TranscriptEntryRead.model_validate(transcript_entry)


@router.delete("/{transcript_entry_id}", status_code=status.HTTP_200_OK)
async def delete_transcript_entry(transcript_entry_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    service = TranscriptEntryService(db)
    deleted = await service.delete(transcript_entry_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript entry not found")
    return {"detail": "Transcript entry deleted successfully"}
