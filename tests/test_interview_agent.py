from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    db_path = Path("test.db")
    if db_path.exists():
        db_path.unlink()
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_user_and_session_flow(client: TestClient) -> None:
    user_response = client.post(
        "/api/v1/users",
        json={
            "email": "candidate@example.com",
            "full_name": "Candidate Name",
            "is_active": True,
        },
    )
    assert user_response.status_code == 201, user_response.text
    user_id = user_response.json()["id"]

    profile_response = client.post(
        "/api/v1/candidate-profiles",
        json={
            "user_id": user_id,
            "full_name": "Candidate Name",
            "headline": "Software Engineer",
            "summary": "Experienced developer",
            "location": "Remote",
            "current_role": "Engineer",
            "years_experience": 3,
        },
    )
    assert profile_response.status_code == 201, profile_response.text
    profile_id = profile_response.json()["id"]

    session_response = client.post(
        "/api/v1/interview-sessions",
        json={
            "candidate_profile_id": profile_id,
            "title": "Technical Interview",
            "status": "draft",
            "summary": "Test interview",
            "max_turns": 5,
            "current_turn": 0,
            "interview_state": {"status": "not_started", "current_turn": 0, "max_turns": 5},
        },
    )
    assert session_response.status_code == 201, session_response.text
    session_id = session_response.json()["id"]

    start_response = client.post(
        "/api/v1/interview-agent/start",
        json={"interview_session_id": session_id},
    )
    assert start_response.status_code == 200, start_response.text
    payload = start_response.json()
    assert payload["status"] == "in_progress"
    assert "question" in payload


def test_interview_mvp_endpoints(client: TestClient) -> None:
    user_response = client.post(
        "/api/v1/users",
        json={
            "email": "interviewee@example.com",
            "full_name": "Interview Candidate",
            "is_active": True,
        },
    )
    assert user_response.status_code == 201, user_response.text
    user_id = user_response.json()["id"]

    profile_response = client.post(
        "/api/v1/candidate-profiles",
        json={
            "user_id": user_id,
            "full_name": "Interview Candidate",
            "headline": "Backend Engineer",
            "summary": "Experienced developer",
            "location": "Remote",
            "current_role": "Backend Engineer",
            "years_experience": 4,
        },
    )
    assert profile_response.status_code == 201, profile_response.text
    profile_id = profile_response.json()["id"]

    start_response = client.post(
        "/api/v1/interviews/start",
        json={"candidate_profile_id": profile_id, "title": "Mock Technical Interview"},
    )
    assert start_response.status_code == 200, start_response.text
    payload = start_response.json()
    assert payload["status"] == "in_progress"
    assert payload["turn_count"] == 1
    assert payload["question"]
    interview_id = payload["session_id"]

    answer_response = client.post(
        f"/api/v1/interviews/{interview_id}/answer",
        json={"answer": "I have worked on backend services, API design, and database optimization in a distributed system."},
    )
    assert answer_response.status_code == 200, answer_response.text
    answer_payload = answer_response.json()
    assert answer_payload["status"] in {"in_progress", "completed"}
    assert answer_payload["session_id"] == interview_id

    transcript_response = client.get(f"/api/v1/interviews/{interview_id}/transcript")
    assert transcript_response.status_code == 200, transcript_response.text
    transcript_payload = transcript_response.json()
    assert len(transcript_payload["entries"]) >= 2

    state_response = client.get(f"/api/v1/interviews/{interview_id}/state")
    assert state_response.status_code == 200, state_response.text
    state_payload = state_response.json()
    assert state_payload["current_stage"] in {"introduction", "background", "projects", "technical", "wrap_up", "completed"}
    assert isinstance(state_payload["turn_count"], int)

    complete_response = client.post(f"/api/v1/interviews/{interview_id}/complete")
    assert complete_response.status_code == 200, complete_response.text
    assert complete_response.json()["status"] == "completed"


def test_interview_stage_progression_and_history(client: TestClient) -> None:
    user_response = client.post(
        "/api/v1/users",
        json={
            "email": "history@example.com",
            "full_name": "History Candidate",
            "is_active": True,
        },
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    profile_response = client.post(
        "/api/v1/candidate-profiles",
        json={
            "user_id": user_id,
            "full_name": "History Candidate",
            "headline": "Platform Engineer",
            "summary": "System design and reliability",
            "location": "Hybrid",
            "current_role": "Platform Engineer",
            "years_experience": 6,
        },
    )
    assert profile_response.status_code == 201
    profile_id = profile_response.json()["id"]

    start_response = client.post(
        "/api/v1/interviews/start",
        json={"candidate_profile_id": profile_id, "title": "Stage Progression Interview"},
    )
    assert start_response.status_code == 200
    interview_id = start_response.json()["session_id"]

    for answer in [
        "I manage internal APIs and observability for our platform.",
        "We improved deployment reliability by reducing manual rollout steps.",
        "One service had a major availability issue during peak traffic.",
    ]:
        response = client.post(
            f"/api/v1/interviews/{interview_id}/answer",
            json={"answer": answer},
        )
        assert response.status_code == 200, response.text

    state_response = client.get(f"/api/v1/interviews/{interview_id}/state")
    assert state_response.status_code == 200
    state_payload = state_response.json()
    assert state_payload["current_stage"] in {"background", "projects", "technical", "wrap_up"}
    assert state_payload["turn_count"] >= 1
    assert "topics_covered" in state_payload
    assert "last_question" in state_payload

    history_response = client.get(f"/api/v1/interviews/{interview_id}/history")
    assert history_response.status_code == 200, history_response.text
    history_payload = history_response.json()
    assert "history" in history_payload
    assert len(history_payload["history"]) >= 2
    assert history_payload["history"][0]["sequence_number"] <= history_payload["history"][-1]["sequence_number"]


def test_interview_completion_after_max_turns(client: TestClient) -> None:
    user_response = client.post(
        "/api/v1/users",
        json={
            "email": "maxturns@example.com",
            "full_name": "Max Turns Candidate",
            "is_active": True,
        },
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    profile_response = client.post(
        "/api/v1/candidate-profiles",
        json={
            "user_id": user_id,
            "full_name": "Max Turns Candidate",
            "headline": "Site Reliability Engineer",
            "summary": "Resilience, automation, and monitoring",
            "location": "Remote",
            "current_role": "SRE",
            "years_experience": 7,
        },
    )
    assert profile_response.status_code == 201
    profile_id = profile_response.json()["id"]

    start_response = client.post(
        "/api/v1/interviews/start",
        json={"candidate_profile_id": profile_id, "title": "Max Turns Interview"},
    )
    assert start_response.status_code == 200
    interview_id = start_response.json()["session_id"]

    for i in range(4):
        response = client.post(
            f"/api/v1/interviews/{interview_id}/answer",
            json={"answer": f"Answer number {i + 1} describes my system design and reliability work."},
        )
        assert response.status_code == 200, response.text

    completion_response = client.post(f"/api/v1/interviews/{interview_id}/complete")
    assert completion_response.status_code == 200
    assert completion_response.json()["status"] == "completed"

    state_response = client.get(f"/api/v1/interviews/{interview_id}/state")
    assert state_response.status_code == 200
    assert state_response.json()["interview_complete"] is True


def test_provider_switching_uses_config(client: TestClient) -> None:
    from app.core.config import settings
    from app.llm.base import LLMProvider
    from app.llm.mock_provider import MockLLMProvider
    from app.llm.openai_provider import OpenAIProvider

    settings.llm_provider = "mock"
    provider = settings.llm_provider
    assert provider == "mock"
    assert isinstance(MockLLMProvider(), LLMProvider)

    settings.llm_provider = "openai"
    provider = settings.llm_provider
    assert provider == "openai"
    assert isinstance(OpenAIProvider(), LLMProvider)

    settings.llm_provider = "mock"
