from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_speech_analytics_endpoint() -> None:
    db_path = Path("test.db")
    if db_path.exists():
        db_path.unlink()

    with TestClient(app) as client:
        user_response = client.post(
            "/api/v1/users",
            json={
                "email": "speech@example.com",
                "full_name": "Speech Candidate",
                "is_active": True,
            },
        )
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]

        profile_response = client.post(
            "/api/v1/candidate-profiles",
            json={
                "user_id": user_id,
                "full_name": "Speech Candidate",
                "headline": "Backend Engineer",
                "summary": "Strong systems and API experience",
                "location": "Remote",
                "current_role": "Backend Engineer",
                "years_experience": 4,
            },
        )
        assert profile_response.status_code == 201
        profile_id = profile_response.json()["id"]

        start_response = client.post(
            "/api/v1/interviews/start",
            json={"candidate_profile_id": profile_id, "title": "Speech Analytics Interview"},
        )
        assert start_response.status_code == 200
        interview_id = start_response.json()["session_id"]

        for answer in [
            "I designed REST APIs and improved system reliability by reducing latency and improving observability with dashboards and alerts.",
            "Um, I also worked on database tuning and query optimization, and I used caching to cut read latency for high-traffic endpoints.",
        ]:
            response = client.post(
                f"/api/v1/interviews/{interview_id}/answer",
                json={"answer": answer},
            )
            assert response.status_code == 200, response.text

        speech_response = client.get(f"/api/v1/interviews/{interview_id}/speech-analysis")
        assert speech_response.status_code == 200, speech_response.text

        payload = speech_response.json()
        assert payload["interview_session_id"] == interview_id
        assert payload["candidate_word_count"] > 0
        assert payload["filler_word_count"] >= 0
        assert 0 <= payload["speech_clarity_score"] <= 100
        assert isinstance(payload["insights"], list)
