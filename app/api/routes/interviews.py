from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_llm_provider
from app.services.interview_agent_service import InterviewMVPService
from app.services.interview_evaluation_service import InterviewEvaluationService
from app.services.speech_analytics_service import SpeechAnalyticsService

router = APIRouter(prefix="/interviews", tags=["interviews"])


class InterviewStartRequest(BaseModel):
    title: str = Field(default="Technical Interview", min_length=1, max_length=255)
    candidate_profile_id: UUID


class InterviewAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1)


@router.post("/start")
async def start_interview(
    payload: InterviewStartRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewMVPService(db, llm_provider=get_llm_provider())
        result = await service.start(title=payload.title, candidate_profile_id=payload.candidate_profile_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{interview_id}/answer")
async def submit_answer(
    interview_id: UUID,
    payload: InterviewAnswerRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewMVPService(db, llm_provider=get_llm_provider())
        result = await service.answer(interview_id, payload.answer)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{interview_id}/complete")
async def complete_interview(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewMVPService(db, llm_provider=get_llm_provider())
        return await service.complete(interview_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{interview_id}/evaluate")
async def evaluate_interview(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewEvaluationService(db)
        return await service.evaluate_interview(interview_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{interview_id}/state")
async def get_interview_state(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewMVPService(db, llm_provider=get_llm_provider())
        return await service.get_state(interview_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{interview_id}/transcript")
async def get_transcript(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewMVPService(db, llm_provider=get_llm_provider())
        return await service.get_transcript(interview_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{interview_id}/history")
async def get_interview_history(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewMVPService(db, llm_provider=get_llm_provider())
        return await service.get_history(interview_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{interview_id}/scores")
async def get_interview_scores(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewEvaluationService(db)
        return await service.get_scores(interview_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{interview_id}/report")
async def get_interview_report(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewEvaluationService(db)
        return await service.get_report(interview_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{interview_id}/recommendation")
async def get_interview_recommendation(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewEvaluationService(db)
        return await service.get_recommendation(interview_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{interview_id}/speech-analysis")
async def get_speech_analysis(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = SpeechAnalyticsService(db)
        return await service.analyze_interview(interview_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
