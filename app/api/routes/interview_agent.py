from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.providers.openai_provider import OpenAIProvider
from app.prompts.manager import PromptManager
from app.services.interview_agent_service import InterviewAgentService

router = APIRouter(prefix="/interview-agent", tags=["interview-agent"])


class InterviewStartRequest(BaseModel):
    interview_session_id: UUID


class InterviewAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1)


@router.post("/start")
async def start_interview(
    payload: InterviewStartRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewAgentService(
            db,
            llm_provider=OpenAIProvider(),
            prompt_manager=PromptManager(),
        )
        result = await service.start_interview(payload.interview_session_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/submit-answer/{interview_session_id}")
async def submit_answer(
    interview_session_id: UUID,
    payload: InterviewAnswerRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewAgentService(
            db,
            llm_provider=OpenAIProvider(),
            prompt_manager=PromptManager(),
        )
        result = await service.submit_answer(interview_session_id, payload.answer)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/complete/{interview_session_id}")
async def complete_interview(
    interview_session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        service = InterviewAgentService(
            db,
            llm_provider=OpenAIProvider(),
            prompt_manager=PromptManager(),
        )
        result = await service.complete_interview(interview_session_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
