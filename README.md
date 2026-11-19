# AI Mock Interviewer

FastAPI backend plus a React frontend (`frontend/`) for the AI Mock Interviewer platform.

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

## Frontend

React + TypeScript + Vite app in `frontend/`. Pages: sign-in, dashboard (resume/JD upload, skill match, interview history), interview room (text or voice answers, read-aloud questions), and report (score, rubric breakdown, delivery analysis, per-answer feedback, Markdown/PDF export).

### Develop

```bash
uvicorn app.main:app --reload          # API on :8000
cd frontend && npm install && npm run dev   # UI on http://localhost:5173 (proxies /api to :8000)
```

### Deploy options

1. **Served by the API (one deployment):** `cd frontend && npm run build`. FastAPI serves `frontend/dist` at `/app`. The Docker image does this automatically.
2. **Separate static host (Vercel, Netlify, GitHub Pages):** build with `VITE_API_URL=https://<your-api>/api/v1 npm run build`, upload `frontend/dist`, and add the frontend origin to `CORS_ORIGINS` on the API.

The app uses hash routing and relative asset paths, so it works from any domain or sub-folder without rewrite rules.

### Embed in a portfolio

```html
<div id="ai-interviewer"></div>
<script src="https://<frontend-host>/embed.js" data-target="#ai-interviewer"
        data-theme="dark" data-accent="22c55e"></script>
```

This inserts an auto-resizing iframe with microphone access. You can also link straight to `https://<frontend-host>/` or `.../index.html?embed=1&theme=light&accent=4f46e5`. Voice input needs HTTPS and works in Chrome, Edge and Safari; other browsers fall back to typing.

## Configuration

| Variable | Purpose |
| --- | --- |
| `LLM_PROVIDER` | `mock` (rule-based questions, no key) or `openai` (LLM questions tailored to resume and JD; falls back to the rule-based questions on errors) |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | Required when `LLM_PROVIDER=openai` |
| `CORS_ORIGINS` | Comma-separated allowed browser origins (`*` by default) |

## Notes

- Sign-in is passwordless (email only), so anyone who knows an email can open that user's data. Add real authentication before storing real candidate data publicly.
- Resume and JD uploads accept PDF, DOCX and TXT, up to 5 MB.
- AI providers and speech providers are isolated behind interfaces to support future expansion.
- The project is structured for modular extension as described in the architecture plan.
