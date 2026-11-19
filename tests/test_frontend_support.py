from __future__ import annotations

import io
import zipfile
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


def _docx_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "word/document.xml",
            f'<w:document><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>',
        )
    return buffer.getvalue()


def test_sign_in_is_idempotent(client: TestClient) -> None:
    payload = {"email": "signin@example.com", "full_name": "Sign In"}
    first = client.post("/api/v1/users/sign-in", json=payload)
    second = client.post("/api/v1/users/sign-in", json=payload)
    assert first.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_docx_resume_and_jd_linked_interview(client: TestClient) -> None:
    user = client.post("/api/v1/users/sign-in", json={"email": "docx@example.com", "full_name": "Docx"}).json()
    profile = client.post("/api/v1/candidate-profiles", json={"user_id": user["id"], "full_name": "Docx"}).json()

    resume = client.post(
        f"/api/v1/candidate-profiles/{profile['id']}/resumes",
        files={"file": ("cv.docx", _docx_bytes("Python and React developer with 4 years experience"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert resume.status_code == 201
    assert "python" in resume.json()["skills"]

    jd = client.post(
        f"/api/v1/candidate-profiles/{profile['id']}/job-descriptions",
        files={"file": ("jd.txt", b"Backend Engineer\nRequires python, docker and postgresql", "text/plain")},
    ).json()

    start = client.post(
        "/api/v1/interviews/start",
        json={"candidate_profile_id": profile["id"], "job_description_id": jd["id"]},
    )
    assert start.status_code == 200
    interview_id = start.json()["session_id"]

    for index in range(5):
        client.post(f"/api/v1/interviews/{interview_id}/answer", json={"answer": f"answer number {index}"})

    entries = client.get(f"/api/v1/interviews/{interview_id}/transcript").json()["entries"]
    assert [entry["sequence_number"] for entry in entries] == list(range(1, len(entries) + 1))
    questions = [entry["content"] for entry in entries if entry["speaker"] == "interviewer"]
    assert len(set(questions)) == len(questions)


def test_start_rejects_foreign_job_description(client: TestClient) -> None:
    user = client.post("/api/v1/users/sign-in", json={"email": "jd@example.com", "full_name": "JD"}).json()
    profile = client.post("/api/v1/candidate-profiles", json={"user_id": user["id"], "full_name": "JD"}).json()
    response = client.post(
        "/api/v1/interviews/start",
        json={"candidate_profile_id": profile["id"], "job_description_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 400


def test_scores_are_on_a_0_to_100_scale_and_discriminate(client: TestClient) -> None:
    user = client.post("/api/v1/users/sign-in", json={"email": "score@example.com", "full_name": "Score"}).json()
    profile = client.post("/api/v1/candidate-profiles", json={"user_id": user["id"], "full_name": "Score"}).json()
    strong = (
        "I built a FastAPI service on PostgreSQL because the API was slow. I decided to add Redis caching, "
        "which reduced latency from 900ms to 120ms and improved throughput 3x for 20k daily users."
    )
    results = []
    for answer in (strong, "i think maybe it was ok"):
        interview_id = client.post("/api/v1/interviews/start", json={"candidate_profile_id": profile["id"]}).json()["session_id"]
        for _ in range(5):
            client.post(f"/api/v1/interviews/{interview_id}/answer", json={"answer": answer})
        evaluation = client.post(f"/api/v1/interviews/{interview_id}/evaluate").json()
        scores = client.get(f"/api/v1/interviews/{interview_id}/scores").json()
        assert scores["overall_score"] == evaluation["overall_score"]
        results.append(evaluation["overall_score"])
    assert results[0] >= 75 > 50 >= results[1]
