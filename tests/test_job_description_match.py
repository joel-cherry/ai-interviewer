from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_job_description_upload_and_match() -> None:
    db_path = Path("test.db")
    if db_path.exists():
        db_path.unlink()

    with TestClient(app) as client:
        user_response = client.post(
            "/api/v1/users",
            json={
                "email": "job.match@example.com",
                "full_name": "JD Candidate",
                "is_active": True,
            },
        )
        assert user_response.status_code == 201, user_response.text
        user_id = user_response.json()["id"]

        profile_response = client.post(
            "/api/v1/candidate-profiles",
            json={
                "user_id": user_id,
                "full_name": "JD Candidate",
                "headline": "Senior Backend Engineer",
                "summary": "Python and systems engineering",
                "location": "Remote",
                "current_role": "Senior Backend Engineer",
                "years_experience": 5,
            },
        )
        assert profile_response.status_code == 201, profile_response.text
        profile_id = profile_response.json()["id"]

        resume_response = client.post(
            f"/api/v1/candidate-profiles/{profile_id}/resumes",
            files={
                "file": (
                    "resume.txt",
                    "Senior Python engineer with 5 years of experience building FastAPI APIs and PostgreSQL systems.",
                    "text/plain",
                )
            },
        )
        assert resume_response.status_code == 201, resume_response.text

        jd_text = """
        Senior Backend Engineer
        Company: Northwind Labs

        We are seeking a senior backend engineer with strong Python, FastAPI, SQLAlchemy, and PostgreSQL experience.
        You should be comfortable building APIs, working with Docker, and improving system reliability.

        Responsibilities:
        - design scalable APIs and services
        - improve observability and deployment workflows
        - collaborate across engineering teams

        Requirements:
        Python, FastAPI, SQLAlchemy, PostgreSQL, Docker, AWS
        """

        jd_response = client.post(
            f"/api/v1/candidate-profiles/{profile_id}/job-descriptions",
            files={"file": ("job_description.txt", jd_text, "text/plain")},
        )
        assert jd_response.status_code == 201, jd_response.text
        jd_payload = jd_response.json()
        assert jd_payload["title"]
        assert jd_payload["required_skills"]
        assert jd_payload["status"] == "parsed"

        match_response = client.post(
            f"/api/v1/candidate-profiles/{profile_id}/job-descriptions/{jd_payload['id']}/match"
        )
        assert match_response.status_code == 200, match_response.text
        match_payload = match_response.json()
        assert match_payload["overall_score"] >= 0.5
        assert "python" in [skill.lower() for skill in match_payload["matched_skills"]]
        assert "missing_skills" in match_payload
