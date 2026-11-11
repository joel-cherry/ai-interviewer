from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.answer_evaluation import AnswerEvaluation
from app.models.candidate_score import CandidateScore
from app.models.interview_recommendation import InterviewRecommendation
from app.models.interview_report import InterviewReport
from app.models.interview_session import InterviewSession
from app.models.transcript_entry import TranscriptEntry


class InterviewEvaluationService:
    TECHNICAL_KEYWORDS = {
        "api",
        "database",
        "postgresql",
        "sql",
        "redis",
        "cache",
        "kubernetes",
        "docker",
        "python",
        "fastapi",
        "system design",
        "architecture",
        "performance",
        "observability",
        "monitoring",
        "microservices",
        "testing",
        "automation",
        "scalability",
        "fault tolerance",
        "security",
    }

    IMPACT_KEYWORDS = {
        "improved",
        "reduced",
        "increased",
        "optimized",
        "increased throughput",
        "decreased",
        "cut",
        "eliminated",
        "resolved",
        "fixed",
        "scaled",
        "reliable",
    }

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def evaluate_interview(self, interview_session_id: UUID) -> dict[str, Any]:
        interview_session = await self._get_interview_session(interview_session_id)
        transcript_entries = await self._get_transcript_entries(interview_session_id)
        candidate_answers = self._extract_candidate_answers(transcript_entries)

        if not candidate_answers:
            raise ValueError("Interview has no candidate answers to evaluate")

        evaluated_answers: list[dict[str, Any]] = []
        for index, answer in enumerate(candidate_answers, start=1):
            question = self._get_question_for_answer(transcript_entries, index)
            evaluation = self._score_answer(question, answer, interview_session)
            evaluated_answers.append(evaluation)

            record = await self._get_or_create_answer_evaluation(interview_session_id, evaluation)
            if record is not None:
                evaluation["id"] = str(record.id)

        score_breakdown = self._summarize_scores(evaluated_answers)
        overall_score = score_breakdown["overall_score"]
        recommendation = self._recommendation_for_score(overall_score)

        candidate_score = await self._upsert_candidate_score(interview_session, score_breakdown)
        interview_recommendation = await self._upsert_recommendation(interview_session, recommendation, score_breakdown)
        report = await self._upsert_report(interview_session, overall_score, recommendation, score_breakdown, evaluated_answers)

        return {
            "interview_session_id": str(interview_session.id),
            "overall_score": round(overall_score, 2),
            "recommendation": recommendation,
            "score_breakdown": score_breakdown,
            "answer_evaluations": evaluated_answers,
            "report": {
                "id": str(report.id),
                "overall_score": round(report.overall_score, 2),
                "recommendation": report.recommendation,
            },
            "candidate_score_id": str(candidate_score.id),
            "recommendation_id": str(interview_recommendation.id),
        }

    async def get_scores(self, interview_session_id: UUID) -> dict[str, Any]:
        interview_session = await self._get_interview_session(interview_session_id)
        evaluations = await self.session.execute(
            select(AnswerEvaluation).where(AnswerEvaluation.interview_session_id == interview_session_id).order_by(AnswerEvaluation.created_at)
        )
        rows = evaluations.scalars().all()
        if not rows:
            await self.evaluate_interview(interview_session_id)
            rows = (await self.session.execute(
                select(AnswerEvaluation).where(AnswerEvaluation.interview_session_id == interview_session_id).order_by(AnswerEvaluation.created_at)
            )).scalars().all()

        if not rows:
            raise ValueError("No evaluation scores found for this interview")

        score_values = {"technical_knowledge": 0.0, "problem_solving": 0.0, "communication": 0.0, "role_fit": 0.0, "confidence": 0.0, "experience_relevance": 0.0}
        for row in rows:
            score_values["technical_knowledge"] += row.score * 0.35
            score_values["problem_solving"] += row.score * 0.25
            score_values["communication"] += row.score * 0.2
            score_values["role_fit"] += row.score * 0.1
            score_values["confidence"] += row.score * 0.05
            score_values["experience_relevance"] += row.score * 0.05

        for key in score_values:
            score_values[key] = round(score_values[key] / max(len(rows), 1), 2)

        overall_score = round(sum(score_values.values()) / len(score_values), 2)
        candidate_score = await self.session.execute(
            select(CandidateScore).where(CandidateScore.interview_session_id == interview_session_id)
        )
        existing = candidate_score.scalar_one_or_none()
        if existing is not None:
            existing.technical_knowledge = score_values["technical_knowledge"]
            existing.problem_solving = score_values["problem_solving"]
            existing.communication = score_values["communication"]
            existing.role_fit = score_values["role_fit"]
            existing.confidence = score_values["confidence"]
            existing.experience_relevance = score_values["experience_relevance"]
            existing.overall_score = overall_score
            await self.session.commit()
            await self.session.refresh(existing)
            return {
                "interview_session_id": str(interview_session.id),
                "technical_knowledge": existing.technical_knowledge,
                "problem_solving": existing.problem_solving,
                "communication": existing.communication,
                "role_fit": existing.role_fit,
                "confidence": existing.confidence,
                "experience_relevance": existing.experience_relevance,
                "overall_score": existing.overall_score,
            }

        return {
            "interview_session_id": str(interview_session.id),
            **score_values,
            "overall_score": overall_score,
        }

    async def get_report(self, interview_session_id: UUID) -> dict[str, Any]:
        report = await self.session.execute(
            select(InterviewReport).where(InterviewReport.interview_session_id == interview_session_id)
        )
        existing = report.scalar_one_or_none()
        if existing is None:
            await self.evaluate_interview(interview_session_id)
            existing = (await self.session.execute(select(InterviewReport).where(InterviewReport.interview_session_id == interview_session_id))).scalar_one_or_none()
        if existing is None:
            raise ValueError("Interview report not found")

        return {
            "id": str(existing.id),
            "interview_session_id": str(existing.interview_session_id),
            "overall_score": round(existing.overall_score, 2),
            "recommendation": existing.recommendation,
            "markdown_report": existing.markdown_report,
            "json_report": json.loads(existing.json_report) if existing.json_report else {},
        }

    async def get_recommendation(self, interview_session_id: UUID) -> dict[str, Any]:
        recommendation = await self.session.execute(
            select(InterviewRecommendation).where(InterviewRecommendation.interview_session_id == interview_session_id)
        )
        existing = recommendation.scalar_one_or_none()
        if existing is None:
            await self.evaluate_interview(interview_session_id)
            existing = (await self.session.execute(select(InterviewRecommendation).where(InterviewRecommendation.interview_session_id == interview_session_id))).scalar_one_or_none()
        if existing is None:
            raise ValueError("Interview recommendation not found")

        return {
            "id": str(existing.id),
            "interview_session_id": str(existing.interview_session_id),
            "recommendation": existing.recommendation,
            "confidence": existing.confidence,
            "reasoning": existing.reasoning,
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
    def _extract_candidate_answers(transcript_entries: list[TranscriptEntry]) -> list[str]:
        answers: list[str] = []
        for entry in transcript_entries:
            if entry.speaker == "candidate":
                text = (entry.content or "").strip()
                if text:
                    answers.append(text)
        return answers

    @staticmethod
    def _get_question_for_answer(transcript_entries: list[TranscriptEntry], answer_index: int) -> str:
        interviewer_questions = [entry.content for entry in transcript_entries if entry.speaker == "interviewer"]
        return interviewer_questions[min(answer_index - 1, len(interviewer_questions) - 1)] if interviewer_questions else "Interview question"

    def _score_answer(self, question: str, answer: str, interview_session: InterviewSession) -> dict[str, Any]:
        text = answer.strip()
        words = text.split()
        keyword_hits = sum(keyword in answer.lower() for keyword in self.TECHNICAL_KEYWORDS)
        impact_hits = sum(keyword in answer.lower() for keyword in self.IMPACT_KEYWORDS)
        numeric_mentions = sum(ch.isdigit() for ch in answer)
        score = 50.0
        score += min(20, keyword_hits * 4)
        score += min(15, impact_hits * 5)
        if numeric_mentions > 0:
            score += 8
        if len(words) >= 25:
            score += 8
        if len(words) >= 45:
            score += 5

        score = min(100.0, max(35.0, score))
        strengths = []
        if keyword_hits > 0:
            strengths.append("Demonstrates relevant technical depth and domain knowledge")
        if impact_hits > 0:
            strengths.append("Provides evidence of measurable impact and outcomes")
        if len(words) >= 25:
            strengths.append("Answer is structured and detailed enough to explain the work clearly")

        weaknesses = []
        if keyword_hits == 0:
            weaknesses.append("Could include more concrete technical details and framework-specific examples")
        if impact_hits == 0:
            weaknesses.append("Could quantify the impact of the work with clearer outcomes or metrics")
        if len(words) < 20:
            weaknesses.append("Answer could provide more evidence, examples, or context")

        improvements = []
        if not strengths:
            improvements.append("Add a concrete example, the technical decision, and the resulting outcome")
        else:
            improvements.append("Use the STAR format to improve clarity: situation, task, action, and result")
            improvements.append("Mention the trade-offs and why the chosen approach was effective")

        stage = self._infer_stage(interview_session, question)

        return {
            "question_text": question,
            "candidate_answer": answer,
            "interview_stage": stage,
            "score": round(score, 2),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvement_suggestions": improvements,
            "reasoning": (
                "The response demonstrates concrete technical exposure and evidence of results, "
                "but can be strengthened further with more explicit business impact and deeper trade-off analysis."
            ),
        }

    @staticmethod
    def _infer_stage(interview_session: InterviewSession, question: str) -> str:
        text = (question or "").lower()
        stage_map = {
            "background": ["background", "experience", "career", "history"],
            "projects": ["project", "team", "work", "architecture", "design"],
            "technical": ["technical", "system design", "database", "api", "scaling", "performance"],
            "wrap_up": ["strengths", "weaknesses", "questions", "future"],
        }
        for stage_name, keywords in stage_map.items():
            if any(keyword in text for keyword in keywords):
                return stage_name
        return "background" if (interview_session.current_turn or 0) <= 2 else "technical"

    @staticmethod
    def _summarize_scores(evaluated_answers: list[dict[str, Any]]) -> dict[str, float]:
        if not evaluated_answers:
            return {"technical_knowledge": 0.0, "problem_solving": 0.0, "communication": 0.0, "role_fit": 0.0, "confidence": 0.0, "experience_relevance": 0.0, "overall_score": 0.0}
        totals = {"technical_knowledge": 0.0, "problem_solving": 0.0, "communication": 0.0, "role_fit": 0.0, "confidence": 0.0, "experience_relevance": 0.0}
        for item in evaluated_answers:
            total = float(item["score"])
            totals["technical_knowledge"] += total * 0.38
            totals["problem_solving"] += total * 0.22
            totals["communication"] += total * 0.18
            totals["role_fit"] += total * 0.12
            totals["confidence"] += total * 0.06
            totals["experience_relevance"] += total * 0.04

        count = float(len(evaluated_answers))
        normalized = {key: round(value / count, 2) for key, value in totals.items()}
        normalized["overall_score"] = round(sum(normalized.values()) / len(normalized), 2)
        return normalized

    @staticmethod
    def _recommendation_for_score(score: float) -> str:
        if score >= 80:
            return "Strong hire"
        if score >= 65:
            return "Proceed to next round"
        if score >= 50:
            return "Consider with coaching"
        return "Not a strong fit"

    async def _get_or_create_answer_evaluation(self, interview_session_id: UUID, evaluation: dict[str, Any]) -> AnswerEvaluation | None:
        existing = await self.session.execute(
            select(AnswerEvaluation).where(
                AnswerEvaluation.interview_session_id == interview_session_id,
                AnswerEvaluation.question_text == evaluation["question_text"],
                AnswerEvaluation.candidate_answer == evaluation["candidate_answer"],
            )
        )
        row = existing.scalar_one_or_none()
        if row is not None:
            row.score = evaluation["score"]
            row.strengths = evaluation["strengths"]
            row.weaknesses = evaluation["weaknesses"]
            row.improvement_suggestions = evaluation["improvement_suggestions"]
            row.reasoning = evaluation["reasoning"]
            row.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(row)
            return row

        row = AnswerEvaluation(
            interview_session_id=interview_session_id,
            question_text=evaluation["question_text"],
            candidate_answer=evaluation["candidate_answer"],
            interview_stage=evaluation["interview_stage"],
            score=evaluation["score"],
            strengths=evaluation["strengths"],
            weaknesses=evaluation["weaknesses"],
            improvement_suggestions=evaluation["improvement_suggestions"],
            reasoning=evaluation["reasoning"],
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def _upsert_candidate_score(self, interview_session: InterviewSession, score_breakdown: dict[str, float]) -> CandidateScore:
        existing = (await self.session.execute(
            select(CandidateScore).where(CandidateScore.interview_session_id == interview_session.id)
        )).scalar_one_or_none()

        if existing is not None:
            existing.technical_knowledge = score_breakdown["technical_knowledge"]
            existing.problem_solving = score_breakdown["problem_solving"]
            existing.communication = score_breakdown["communication"]
            existing.role_fit = score_breakdown["role_fit"]
            existing.confidence = score_breakdown["confidence"]
            existing.experience_relevance = score_breakdown["experience_relevance"]
            existing.overall_score = score_breakdown["overall_score"]
            existing.score_summary = self._recommendation_for_score(score_breakdown["overall_score"])
            existing.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        candidate_score = CandidateScore(
            interview_session_id=interview_session.id,
            technical_knowledge=score_breakdown["technical_knowledge"],
            problem_solving=score_breakdown["problem_solving"],
            communication=score_breakdown["communication"],
            role_fit=score_breakdown["role_fit"],
            confidence=score_breakdown["confidence"],
            experience_relevance=score_breakdown["experience_relevance"],
            overall_score=score_breakdown["overall_score"],
            score_summary=self._recommendation_for_score(score_breakdown["overall_score"]),
        )
        self.session.add(candidate_score)
        await self.session.commit()
        await self.session.refresh(candidate_score)
        return candidate_score

    async def _upsert_recommendation(
        self,
        interview_session: InterviewSession,
        recommendation: str,
        score_breakdown: dict[str, float],
    ) -> InterviewRecommendation:
        existing = (await self.session.execute(
            select(InterviewRecommendation).where(InterviewRecommendation.interview_session_id == interview_session.id)
        )).scalar_one_or_none()

        confidence = int(min(100, max(35, score_breakdown["overall_score"])))
        reasoning = (
            "This candidate shows solid evidence of technical depth, impact, and communication. "
            "The main improvement areas are providing more concrete trade-offs and measurable business outcomes."
        )

        if existing is not None:
            existing.recommendation = recommendation
            existing.confidence = confidence
            existing.reasoning = reasoning
            existing.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        row = InterviewRecommendation(
            interview_session_id=interview_session.id,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def _upsert_report(
        self,
        interview_session: InterviewSession,
        overall_score: float,
        recommendation: str,
        score_breakdown: dict[str, float],
        evaluated_answers: list[dict[str, Any]],
    ) -> InterviewReport:
        existing = (await self.session.execute(
            select(InterviewReport).where(InterviewReport.interview_session_id == interview_session.id)
        )).scalar_one_or_none()

        markdown_lines = [
            "# Interview Evaluation Report",
            f"- Candidate: {interview_session.title}",
            f"- Overall score: {overall_score:.2f}/100",
            f"- Recommendation: {recommendation}",
            "",
            "## Score breakdown",
        ]
        for metric, value in score_breakdown.items():
            if metric == "overall_score":
                continue
            markdown_lines.append(f"- {metric.replace('_', ' ').title()}: {value:.2f}")

        markdown_lines.append("")
        markdown_lines.append("## Answer review")
        for index, item in enumerate(evaluated_answers, start=1):
            markdown_lines.append(f"### Answer {index} ({item['interview_stage']})")
            markdown_lines.append(f"- Score: {item['score']:.2f}")
            markdown_lines.append(f"- Strengths: {', '.join(item['strengths']) if item['strengths'] else 'None'}")
            markdown_lines.append(f"- Improvements: {', '.join(item['improvement_suggestions']) if item['improvement_suggestions'] else 'None'}")

        markdown = "\n".join(markdown_lines)
        json_report = {
            "interview_session_id": str(interview_session.id),
            "overall_score": round(overall_score, 2),
            "recommendation": recommendation,
            "score_breakdown": score_breakdown,
            "answers": evaluated_answers,
        }

        if existing is not None:
            existing.json_report = json.dumps(json_report)
            existing.markdown_report = markdown
            existing.overall_score = overall_score
            existing.recommendation = recommendation
            existing.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        row = InterviewReport(
            interview_session_id=interview_session.id,
            json_report=json.dumps(json_report),
            markdown_report=markdown,
            overall_score=overall_score,
            recommendation=recommendation,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row
