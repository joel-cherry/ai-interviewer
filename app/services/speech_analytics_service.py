from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview_session import InterviewSession
from app.models.transcript_entry import TranscriptEntry


class SpeechAnalyticsService:
    FILLER_WORDS = {
        "um",
        "uh",
        "like",
        "basically",
        "literally",
        "sorta",
        "kinda",
        "you know",
        "youknow",
        "actually",
    }

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def analyze_interview(self, interview_session_id: UUID) -> dict[str, Any]:
        interview_session = await self._get_interview_session(interview_session_id)
        transcript_entries = await self._get_transcript_entries(interview_session_id)

        candidate_entries = [entry for entry in transcript_entries if entry.speaker == "candidate"]
        if not candidate_entries:
            raise ValueError("Interview has no candidate responses to analyze")

        candidate_text = " ".join((entry.content or "").strip() for entry in candidate_entries if (entry.content or "").strip())
        normalized_words = re.findall(r"[A-Za-z']+", candidate_text.lower())
        filler_word_count = sum(1 for word in normalized_words if word in self.FILLER_WORDS)
        candidate_word_count = len(normalized_words)

        response_times = []
        for candidate_entry in candidate_entries:
            previous_interviewer = self._previous_interviewer_entry(transcript_entries, candidate_entry.sequence_number)
            if previous_interviewer is None or candidate_entry.created_at is None or previous_interviewer.created_at is None:
                continue
            delta = candidate_entry.created_at - previous_interviewer.created_at
            if delta.total_seconds() > 0:
                response_times.append(delta.total_seconds())

        average_response_time = round(sum(response_times) / len(response_times), 2) if response_times else 0.0
        clarity_score = self._calculate_clarity_score(candidate_word_count, filler_word_count, average_response_time)
        insights = self._build_insights(candidate_word_count, filler_word_count, clarity_score, average_response_time, len(candidate_entries))

        return {
            "interview_session_id": str(interview_session.id),
            "candidate_word_count": candidate_word_count,
            "response_count": len(candidate_entries),
            "filler_word_count": filler_word_count,
            "average_response_time_seconds": average_response_time,
            "speech_clarity_score": clarity_score,
            "insights": insights,
        }

    async def _get_interview_session(self, interview_session_id: UUID) -> InterviewSession:
        interview_session = await self.session.get(InterviewSession, interview_session_id)
        if interview_session is None:
            raise ValueError("Interview session not found")
        return interview_session

    async def _get_transcript_entries(self, interview_session_id: UUID) -> list[TranscriptEntry]:
        result = await self.session.execute(
            select(TranscriptEntry)
            .where(TranscriptEntry.interview_session_id == interview_session_id)
            .order_by(TranscriptEntry.sequence_number)
        )
        return list(result.scalars().all())

    @staticmethod
    def _previous_interviewer_entry(transcript_entries: list[TranscriptEntry], sequence_number: int) -> TranscriptEntry | None:
        prior_entries = [entry for entry in transcript_entries if entry.sequence_number < sequence_number and entry.speaker == "interviewer"]
        return prior_entries[-1] if prior_entries else None

    @staticmethod
    def _calculate_clarity_score(candidate_word_count: int, filler_word_count: int, average_response_time: float) -> int:
        score = 70
        if 25 <= candidate_word_count <= 180:
            score += 15
        elif candidate_word_count < 15:
            score -= 15

        if average_response_time > 0:
            if 3 <= average_response_time <= 20:
                score += 10
            elif average_response_time > 20:
                score += 5

        score -= filler_word_count * 8
        score = max(0, min(100, score))
        return score

    @staticmethod
    def _build_insights(
        candidate_word_count: int,
        filler_word_count: int,
        clarity_score: int,
        average_response_time: float,
        response_count: int,
    ) -> list[str]:
        insights: list[str] = []

        if candidate_word_count >= 80:
            insights.append("The candidate provided substantial detail across the response set.")
        else:
            insights.append("The candidate could deepen responses with more specific examples and outcomes.")

        if filler_word_count > 0:
            insights.append(f"Filler usage detected: {filler_word_count} filler words across {response_count} responses.")
        else:
            insights.append("No filler words were detected in the candidate responses.")

        if clarity_score >= 80:
            insights.append("Speech clarity is strong and the responses are easy to follow.")
        elif clarity_score >= 60:
            insights.append("Speech clarity is moderate; tighter examples would improve delivery.")
        else:
            insights.append("Speech clarity is low; more concise and structured answers would help.")

        if average_response_time >= 3:
            insights.append(f"Average response latency was {average_response_time:.1f}s, indicating thoughtful pacing.")
        else:
            insights.append("Responses were very rapid, suggesting the candidate may be speaking more from recall than reflection.")

        return insights
