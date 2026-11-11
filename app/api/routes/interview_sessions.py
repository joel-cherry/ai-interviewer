from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.interview_session import InterviewSessionCreate, InterviewSessionRead, InterviewSessionUpdate
from app.services.interview_session_service import InterviewSessionService

router = APIRouter(prefix="/interview-sessions", tags=["interview-sessions"])


@router.post("", response_model=InterviewSessionRead, status_code=status.HTTP_201_CREATED)
async def create_interview_session(
    payload: InterviewSessionCreate,
    db: AsyncSession = Depends(get_db),
) -> InterviewSessionRead:
    service = InterviewSessionService(db)
    interview_session = await service.create(payload)
    return InterviewSessionRead.model_validate(interview_session)


@router.get("", response_model=list[InterviewSessionRead])
async def list_interview_sessions(
    db: AsyncSession = Depends(get_db),
    candidate_profile_id: UUID | None = Query(default=None),
    offset: int = 0,
    limit: int = 100,
) -> list[InterviewSessionRead]:
    service = InterviewSessionService(db)
    if candidate_profile_id is not None:
        interview_sessions = await service.get_by_candidate_profile_id(candidate_profile_id)
    else:
        interview_sessions = await service.repository.list(offset=offset, limit=limit)
    return [InterviewSessionRead.model_validate(item) for item in interview_sessions]


@router.get("/{interview_session_id}", response_model=InterviewSessionRead)
async def get_interview_session(interview_session_id: UUID, db: AsyncSession = Depends(get_db)) -> InterviewSessionRead:
    service = InterviewSessionService(db)
    interview_session = await service.get_by_id(interview_session_id)
    if interview_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
    return InterviewSessionRead.model_validate(interview_session)


@router.put("/{interview_session_id}", response_model=InterviewSessionRead)
async def update_interview_session(
    interview_session_id: UUID,
    payload: InterviewSessionUpdate,
    db: AsyncSession = Depends(get_db),
) -> InterviewSessionRead:
    service = InterviewSessionService(db)
    interview_session = await service.update(interview_session_id, payload)
    if interview_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
    return InterviewSessionRead.model_validate(interview_session)


@router.delete("/{interview_session_id}", status_code=status.HTTP_200_OK)
async def delete_interview_session(interview_session_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    service = InterviewSessionService(db)
    deleted = await service.delete(interview_session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
    return {"detail": "Interview session deleted successfully"}
