from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview_session import InterviewSession
from app.models.interview_state import InterviewState
from app.models.transcript_entry import TranscriptEntry
from app.prompts.manager import PromptManager
from app.providers.base_provider import BaseLLMProvider
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.repositories.transcript_entry_repository import TranscriptEntryRepository


class InterviewAgentService:
    def __init__(
        self,
        session: AsyncSession,
        llm_provider: BaseLLMProvider,
        prompt_manager: PromptManager | None = None,
    ) -> None:
        self.session = session
        self.llm_provider = llm_provider
        self.prompt_manager = prompt_manager or PromptManager()
        self.interview_session_repository = InterviewSessionRepository(session)
        self.transcript_repository = TranscriptEntryRepository(session)

    async def start_interview(self, interview_session_id: UUID) -> dict[str, Any]:
        interview_session = await self.interview_session_repository.get_by_id(interview_session_id)
        if interview_session is None:
            raise ValueError("Interview session not found")

        if interview_session.started_at is None:
            interview_session.started_at = datetime.now(timezone.utc)
            interview_session.status = "in_progress"

        state = self._deserialize_state(interview_session.interview_state)
        if state.current_turn == 0 and not state.conversation_history:
            state.mark_started()
            turn_number = 1
            prompt = self.prompt_manager.get_question_prompt(
                interview_title=interview_session.title,
                turn_number=turn_number,
                max_turns=interview_session.max_turns,
            )
            question = await self.llm_provider.generate_interview_question(prompt=prompt, context={"turn": turn_number})
            interview_session.current_turn = 1
            interview_session.interview_state = state.to_dict()
            interview_session.interview_state["last_question"] = question
            interview_session.interview_state["status"] = "in_progress"
            interview_session.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(interview_session)
            return {
                "interview_session_id": str(interview_session.id),
                "turn": interview_session.current_turn,
                "question": question,
                "status": "in_progress",
            }

        return {
            "interview_session_id": str(interview_session.id),
            "turn": state.current_turn,
            "question": state.last_question,
            "status": state.status,
        }

    async def submit_answer(self, interview_session_id: UUID, answer: str) -> dict[str, Any]:
        interview_session = await self.interview_session_repository.get_by_id(interview_session_id)
        if interview_session is None:
            raise ValueError("Interview session not found")

        if interview_session.status == "completed":
            raise ValueError("Interview session is already completed")

        state = self._deserialize_state(interview_session.interview_state)
        if not state.last_question:
            raise ValueError("No active question to answer")

        transcript_entry = TranscriptEntry(
            interview_session_id=interview_session_id,
            sequence_number=len(interview_session.transcript_entries) + 1,
            speaker="candidate",
            content=answer,
        )
        await self.transcript_repository.create(transcript_entry)

        transcript_summary = self._build_transcript_summary(interview_session)
        if state.current_turn >= interview_session.max_turns:
            summary_prompt = self.prompt_manager.get_summary_prompt(
                interview_title=interview_session.title,
                transcript=transcript_summary,
            )
            summary = await self.llm_provider.generate_response(prompt=summary_prompt)
            interview_session.status = "completed"
            interview_session.ended_at = datetime.now(timezone.utc)
            interview_session.interview_state = {"status": "completed", "summary": summary, "current_turn": state.current_turn}
            interview_session.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            return {
                "interview_session_id": str(interview_session.id),
                "turn": state.current_turn,
                "status": "completed",
                "summary": summary,
            }

        next_turn = state.current_turn + 1
        prompt = self.prompt_manager.get_follow_up_prompt(
            interview_title=interview_session.title,
            turn_number=next_turn,
            max_turns=interview_session.max_turns,
            prior_answer=answer,
        )
        follow_up_question = await self.llm_provider.generate_follow_up_question(prompt=prompt, context={"turn": next_turn})

        state.add_exchange(question=state.last_question or "", answer=answer)
        state.last_question = follow_up_question
        state.status = "in_progress"
        interview_session.current_turn = next_turn
        interview_session.interview_state = state.to_dict()
        interview_session.updated_at = datetime.now(timezone.utc)

        transcript_entry_question = TranscriptEntry(
            interview_session_id=interview_session_id,
            sequence_number=len(interview_session.transcript_entries) + 2,
            speaker="interviewer",
            content=follow_up_question,
        )
        await self.transcript_repository.create(transcript_entry_question)
        await self.session.commit()
        await self.session.refresh(interview_session)

        return {
            "interview_session_id": str(interview_session.id),
            "turn": interview_session.current_turn,
            "question": follow_up_question,
            "status": "in_progress",
        }

    async def complete_interview(self, interview_session_id: UUID) -> dict[str, Any]:
        interview_session = await self.interview_session_repository.get_by_id(interview_session_id)
        if interview_session is None:
            raise ValueError("Interview session not found")

        transcript_summary = self._build_transcript_summary(interview_session)
        summary_prompt = self.prompt_manager.get_summary_prompt(
            interview_title=interview_session.title,
            transcript=transcript_summary,
        )
        summary = await self.llm_provider.generate_response(prompt=summary_prompt)

        interview_session.status = "completed"
        interview_session.ended_at = datetime.now(timezone.utc)
        interview_session.interview_state = {
            "status": "completed",
            "summary": summary,
            "current_turn": interview_session.current_turn,
        }
        interview_session.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(interview_session)

        return {
            "interview_session_id": str(interview_session.id),
            "status": "completed",
            "summary": summary,
        }

    @staticmethod
    def _deserialize_state(value: dict | None) -> InterviewState:
        if not value:
            return InterviewState(max_turns=5)
        return InterviewState(**value)

    @staticmethod
    def _build_transcript_summary(interview_session: InterviewSession) -> str:
        transcript_entries = sorted(interview_session.transcript_entries, key=lambda item: item.sequence_number)
        if not transcript_entries:
            return "No transcript entries available."
        return "\n".join(
            f"{entry.speaker}: {entry.content}" for entry in transcript_entries
        )


class InterviewMVPService:
    STAGE_SEQUENCE = [
        "introduction",
        "background",
        "projects",
        "technical",
        "wrap_up",
    ]

    def __init__(self, session: AsyncSession, llm_provider: Any | None = None) -> None:
        self.session = session
        self.llm_provider = llm_provider or __import__("app.llm.mock_provider", fromlist=["MockLLMProvider"]).MockLLMProvider()
        self.repository = InterviewSessionRepository(session)
        self.transcript_repository = TranscriptEntryRepository(session)

    async def start(self, *, title: str, candidate_profile_id: UUID | None = None) -> dict[str, Any]:
        if candidate_profile_id is None:
            raise ValueError("candidate_profile_id is required")

        stage = self._resolve_stage(1)
        question = await self._generate_question(previous_question=None, previous_answer=None, stage=stage)
        state = {
            "current_stage": stage,
            "turn_count": 1,
            "topics_covered": [stage],
            "topics_remaining": ["background", "projects", "technical", "wrap_up"],
            "strengths": [],
            "weaknesses": [],
            "last_question": question,
            "interview_complete": False,
        }

        interview_session = InterviewSession(
            title=title,
            status="in_progress",
            summary="",
            max_turns=5,
            current_turn=1,
            interview_state=state,
            candidate_profile_id=candidate_profile_id,
        )
        self.session.add(interview_session)
        await self.session.commit()
        await self.session.refresh(interview_session)

        transcript_entry = TranscriptEntry(
            interview_session_id=interview_session.id,
            sequence_number=1,
            speaker="interviewer",
            content=question,
        )
        self.session.add(transcript_entry)
        await self.session.commit()

        return {
            "session_id": interview_session.id,
            "question": question,
            "status": "in_progress",
            "turn_count": 1,
            "max_turns": interview_session.max_turns,
        }

    async def answer(self, interview_session_id: UUID, answer: str) -> dict[str, Any]:
        if not answer or not answer.strip():
            raise ValueError("Answer cannot be empty")

        interview_session = await self.repository.get_by_id(interview_session_id)
        if interview_session is None:
            raise ValueError("Interview session not found")
        if interview_session.status == "completed":
            raise ValueError("Interview session is already completed")

        current_turn = int(interview_session.current_turn or 0)
        state = self._normalize_state(interview_session.interview_state)
        history = await self.get_history(interview_session_id)
        prior_question = state.get("last_question")

        transcript_entry = TranscriptEntry(
            interview_session_id=interview_session.id,
            sequence_number=len(await self.transcript_repository.get_by_interview_session_id(interview_session.id)) + 1,
            speaker="candidate",
            content=answer,
        )
        self.session.add(transcript_entry)

        next_turn = current_turn + 1
        if next_turn > interview_session.max_turns:
            interview_session.status = "completed"
            interview_session.current_turn = interview_session.max_turns
            interview_session.ended_at = datetime.now(timezone.utc)
            state["current_stage"] = "completed"
            state["turn_count"] = interview_session.max_turns
            state["interview_complete"] = True
            state["last_question"] = prior_question or "Interview complete"
            interview_session.interview_state = state
            await self.session.commit()
            return {
                "session_id": interview_session.id,
                "question": None,
                "status": "completed",
                "turn_count": interview_session.max_turns,
                "interview_complete": True,
                "completion_summary": "Interview complete. The candidate answered the final question.",
            }

        next_stage = self._resolve_stage(next_turn)
        question = await self._generate_question(
            previous_question=prior_question,
            previous_answer=answer,
            stage=next_stage,
            history=history.get("history", []),
        )
        interview_session.current_turn = next_turn
        interview_session.status = "in_progress"
        interview_session.updated_at = datetime.now(timezone.utc)

        state["current_stage"] = next_stage
        state["turn_count"] = next_turn
        state["last_question"] = question
        state["interview_complete"] = False
        stage_name = next_stage
        if stage_name not in state.get("topics_covered", []):
            state["topics_covered"] = list(dict.fromkeys([*state.get("topics_covered", []), stage_name]))
        if stage_name in state.get("topics_remaining", []):
            state["topics_remaining"] = [item for item in state.get("topics_remaining", []) if item != stage_name]
        interview_session.interview_state = state

        follow_up_entry = TranscriptEntry(
            interview_session_id=interview_session.id,
            sequence_number=len(await self.transcript_repository.get_by_interview_session_id(interview_session.id)) + 2,
            speaker="interviewer",
            content=question,
        )
        self.session.add(follow_up_entry)
        await self.session.commit()

        return {
            "session_id": interview_session.id,
            "question": question,
            "status": "in_progress",
            "turn_count": next_turn,
            "interview_complete": False,
            "completion_summary": None,
        }

    async def complete(self, interview_session_id: UUID) -> dict[str, Any]:
        interview_session = await self.repository.get_by_id(interview_session_id)
        if interview_session is None:
            raise ValueError("Interview session not found")

        state = self._normalize_state(interview_session.interview_state)
        state["current_stage"] = "completed"
        state["interview_complete"] = True
        state["turn_count"] = int(interview_session.current_turn or 0)
        interview_session.status = "completed"
        interview_session.ended_at = datetime.now(timezone.utc)
        interview_session.interview_state = state
        interview_session.updated_at = datetime.now(timezone.utc)
        await self.session.commit()

        return {
            "session_id": interview_session.id,
            "status": "completed",
            "summary": "Interview completed successfully.",
        }

    async def get_state(self, interview_session_id: UUID) -> dict[str, Any]:
        interview_session = await self.repository.get_by_id(interview_session_id)
        if interview_session is None:
            raise ValueError("Interview session not found")
        return self._normalize_state(interview_session.interview_state)

    async def get_transcript(self, interview_session_id: UUID) -> dict[str, Any]:
        interview_session = await self.repository.get_by_id(interview_session_id)
        if interview_session is None:
            raise ValueError("Interview session not found")

        entries = await self.transcript_repository.get_by_interview_session_id(interview_session_id)
        ordered = sorted(entries, key=lambda item: item.sequence_number)
        return {
            "session_id": interview_session.id,
            "entries": [
                {
                    "id": item.id,
                    "interview_session_id": item.interview_session_id,
                    "sequence_number": item.sequence_number,
                    "speaker": item.speaker,
                    "content": item.content,
                    "created_at": item.created_at,
                }
                for item in ordered
            ],
        }

    async def get_history(self, interview_session_id: UUID) -> dict[str, Any]:
        transcript = await self.get_transcript(interview_session_id)
        entries = transcript["entries"]
        return {"session_id": transcript["session_id"], "history": entries}

    def _resolve_stage(self, turn_count: int) -> str:
        if turn_count <= 1:
            return "introduction"
        if turn_count == 2:
            return "background"
        if turn_count == 3:
            return "projects"
        if turn_count == 4:
            return "technical"
        return "wrap_up"

    def _normalize_state(self, raw_state: dict[str, Any] | None) -> dict[str, Any]:
        if not raw_state:
            return {
                "current_stage": "introduction",
                "turn_count": 0,
                "topics_covered": [],
                "topics_remaining": ["background", "projects", "technical", "wrap_up"],
                "strengths": [],
                "weaknesses": [],
                "last_question": None,
                "interview_complete": False,
            }

        normalized = dict(raw_state)
        normalized.setdefault("current_stage", "introduction")
        normalized.setdefault("turn_count", 0)
        normalized.setdefault("topics_covered", [])
        normalized.setdefault("topics_remaining", ["background", "projects", "technical", "wrap_up"])
        normalized.setdefault("strengths", [])
        normalized.setdefault("weaknesses", [])
        normalized.setdefault("last_question", None)
        normalized.setdefault("interview_complete", False)
        return normalized

    async def _generate_question(
        self,
        *,
        previous_question: str | None,
        previous_answer: str | None,
        stage: str,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        history = history or []
        recent_context = ""
        if history:
            latest = history[-3:]
            recent_context = "\n".join(
                f"{item.get('speaker', 'unknown')}: {item.get('content', '')}"
                for item in latest
            )

        question_map = {
            "introduction": "Could you briefly walk me through your background and the kind of work you enjoy doing?",
            "background": "What experiences most shaped your technical foundation, and what did you learn from them?",
            "projects": "Tell me about a project that best demonstrates your impact, the trade-offs you made, and the outcome.",
            "technical": "Describe a technical challenge you solved, how you approached it, and how you validated the result.",
            "wrap_up": "If you could improve one area of your profile or career trajectory, what would you focus on next?",
        }

        base_question = question_map.get(stage, question_map["introduction"])
        if not previous_answer:
            return base_question

        lower_answer = previous_answer.lower()
        if "project" in lower_answer or "system" in lower_answer or "architecture" in lower_answer:
            if stage == "projects":
                return "Which project had the strongest technical trade-offs, and what did you learn from that decision?"
            if stage == "technical":
                return "What was the hardest part of that system to scale, and how did you measure success?"
        if "team" in lower_answer or "lead" in lower_answer or "ment" in lower_answer:
            return "How did you influence the team or stakeholders when priorities changed, and what was the result?"
        if "api" in lower_answer or "database" in lower_answer or "service" in lower_answer:
            return "How did you decide on the design constraints for that service, and what trade-offs did you make?"
        if previous_question:
            return f"Building on your earlier answer about '{previous_question[:80]}', what would you do differently if you had to improve the outcome today?"

        return base_question
