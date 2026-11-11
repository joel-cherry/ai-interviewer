from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
        unique=True,
    )
    candidate_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_turns: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    current_turn: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interview_state: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    candidate_profile: Mapped["CandidateProfile"] = relationship(back_populates="interview_sessions")
    transcript_entries: Mapped[list["TranscriptEntry"]] = relationship(
        back_populates="interview_session",
        cascade="all, delete-orphan",
        order_by="TranscriptEntry.sequence_number",
    )
    answer_evaluations: Mapped[list["AnswerEvaluation"]] = relationship(
        back_populates="interview_session",
        cascade="all, delete-orphan",
    )
    candidate_scores: Mapped[list["CandidateScore"]] = relationship(
        back_populates="interview_session",
        cascade="all, delete-orphan",
    )
    interview_reports: Mapped[list["InterviewReport"]] = relationship(
        back_populates="interview_session",
        cascade="all, delete-orphan",
    )
    interview_recommendations: Mapped[list["InterviewRecommendation"]] = relationship(
        back_populates="interview_session",
        cascade="all, delete-orphan",
    )
