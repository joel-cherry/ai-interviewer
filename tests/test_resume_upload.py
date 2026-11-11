from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_resume_upload_and_parsing() -> None:
    db_path = Path("test.db")
    if db_path.exists():
        db_path.unlink()

    with TestClient(app) as client:
        user_response = client.post(
            "/api/v1/users",
            json={
                "email": "resume.candidate@example.com",
                "full_name": "Resume Candidate",
                "is_active": True,
            },
        )
        assert user_response.status_code == 201, user_response.text
        user_id = user_response.json()["id"]

        profile_response = client.post(
            "/api/v1/candidate-profiles",
            json={
                "user_id": user_id,
                "full_name": "Resume Candidate",
                "headline": "Senior Backend Engineer",
                "summary": "Python and systems engineering",
                "location": "Remote",
                "current_role": "Senior Backend Engineer",
                "years_experience": 5,
            },
        )
        assert profile_response.status_code == 201, profile_response.text
        profile_id = profile_response.json()["id"]

        resume_text = """
        Alice Johnson
        Senior Python Engineer

        Email: alice.johnson@example.com
        Phone: +1 (555) 123-4567

        Skills: Python, FastAPI, SQLAlchemy, PostgreSQL, Docker, AWS

        Professional Summary:
        Senior backend engineer with 5 years of experience building APIs, services, and data systems.
       
        Experience:
        - Built resilient Python APIs using FastAPI and PostgreSQL.
        - Led service reliability improvements in Dockerized AWS deployments.
        """

        response = client.post(
            f"/api/v1/candidate-profiles/{profile_id}/resumes",
            files={"file": ("alice_resume.txt", resume_text, "text/plain")},
        )
        assert response.status_code == 201, response.text
        payload = response.json()
        assert payload["file_name"] == "alice_resume.txt"
        assert payload["status"] == "parsed"
        assert payload["experience_years"] >= 4
        assert isinstance(payload["skills"], list)
        assert any("python" == skill.lower() for skill in payload["skills"])
        assert payload["extracted_summary"]

        list_response = client.get(f"/api/v1/candidate-profiles/{profile_id}/resumes")
        assert list_response.status_code == 200, list_response.text
        assert len(list_response.json()) == 1
