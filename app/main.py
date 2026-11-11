from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.interview_agent import router as interview_agent_router
from app.api.routes.interview_sessions import router as interview_sessions_router
from app.api.routes.interviews import router as interviews_router
from app.api.routes.transcript_entries import router as transcript_entries_router
from app.api.routes.users import router as users_router
from app.api.routes.candidate_profiles import router as candidate_profiles_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine
from app.models import CandidateProfile, InterviewSession, JobDescription, ResumeDocument, TranscriptEntry, User

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.project_version,
        description="AI Mock Interviewer API for coaching, adaptive interviews, and evaluation.",
        debug=settings.debug,
        openapi_url=f"{settings.api_v1_str}/openapi.json",
        docs_url=f"{settings.api_v1_str}/docs",
        redoc_url=f"{settings.api_v1_str}/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix=settings.api_v1_str)
    app.include_router(users_router, prefix=settings.api_v1_str)
    app.include_router(candidate_profiles_router, prefix=settings.api_v1_str)
    app.include_router(interview_sessions_router, prefix=settings.api_v1_str)
    app.include_router(transcript_entries_router, prefix=settings.api_v1_str)
    app.include_router(interview_agent_router, prefix=settings.api_v1_str)
    app.include_router(interviews_router, prefix=settings.api_v1_str)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "app": settings.app_name,
            "version": settings.project_version,
            "status": "ok",
        }

    return app


app = create_app()
