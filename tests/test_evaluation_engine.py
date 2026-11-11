from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_interview_evaluation_and_reporting_flow() -> None:
    db_path = Path("test.db")
    if db_path.exists():
        db_path.unlink()

    with TestClient(app) as client:
        user_response = client.post(
            "/api/v1/users",
            json={
                "email": "eval@example.com",
                "full_name": "Evaluation Candidate",
                "is_active": True,
            },
        )
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]

        profile_response = client.post(
            "/api/v1/candidate-profiles",
            json={
                "user_id": user_id,
                "full_name": "Evaluation Candidate",
                "headline": "Backend Engineer",
                "summary": "Strong API and system design experience",
                "location": "Remote",
                "current_role": "Senior Backend Engineer",
                "years_experience": 5,
            },
        )
        assert profile_response.status_code == 201
        profile_id = profile_response.json()["id"]

        start_response = client.post(
            "/api/v1/interviews/start",
            json={"candidate_profile_id": profile_id, "title": "Evaluation Interview"},
        )
        assert start_response.status_code == 200
        interview_id = start_response.json()["session_id"]

        for answer in [
            "I designed and operated REST APIs for critical services, using PostgreSQL, Redis, and asynchronous workers to improve reliability.",
            "In one incident, I traced a database bottleneck to missing indexes and improved throughput by caching hot reads and tuning queries.",
        ]:
            response = client.post(
                f"/api/v1/interviews/{interview_id}/answer",
                json={"answer": answer},
            )
            assert response.status_code == 200, response.text

        evaluation_response = client.post(f"/api/v1/interviews/{interview_id}/evaluate")
        assert evaluation_response.status_code == 200, evaluation_response.text
        evaluation_payload = evaluation_response.json()
        assert evaluation_payload["overall_score"] >= 0
        assert evaluation_payload["overall_score"] <= 100
        assert "recommendation" in evaluation_payload
        assert len(evaluation_payload["answer_evaluations"]) >= 1

        scores_response = client.get(f"/api/v1/interviews/{interview_id}/scores")
        assert scores_response.status_code == 200
        assert scores_response.json()["overall_score"] >= 0

        report_response = client.get(f"/api/v1/interviews/{interview_id}/report")
        assert report_response.status_code == 200
        assert "overall_score" in report_response.json()

        recommendation_response = client.get(f"/api/v1/interviews/{interview_id}/recommendation")
        assert recommendation_response.status_code == 200
        assert "recommendation" in recommendation_response.json()
