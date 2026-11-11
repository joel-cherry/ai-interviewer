# AI Mock Interviewer Backend

This repository contains the backend foundation for the AI Mock Interviewer platform.

## Stack

- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- Docker / Docker Compose
- Pytest

## Project purpose

This is the backend scaffold for a coaching-oriented AI mock interview platform that supports:

- resume and job description ingestion
- adaptive interview orchestration
- interview memory and session state
- rubric-based evaluation and reports
- future voice integration with STT/TTS abstractions

## Getting started

### 1. Copy environment variables

```bash
cp .env.example .env
```

### 2. Start services with Docker Compose

```bash
docker compose up --build
```

### 3. Access the API

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/api/v1/docs
- Health check: http://localhost:8000/api/v1/health

### 4. Run migrations

```bash
docker compose exec api alembic upgrade head
```

## Repository structure

```text
ai_interviewer/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py
│   │   └── __init__.py
│   ├── db/
│   │   ├── base.py
│   │   ├── dependencies.py
│   │   ├── session.py
│   │   └── __init__.py
│   ├── logging.py
│   ├── main.py
│   └── __init__.py
├── alembic/
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
├── .dockerignore
├── requirements.txt
├── README.md
└── pytest.ini
```

## Notes

- This repository intentionally contains the backend skeleton only.
- Frontend work is intentionally excluded.
- AI providers and speech providers are isolated behind interfaces to support future expansion.
- The project is structured for modular extension as described in the architecture plan.
