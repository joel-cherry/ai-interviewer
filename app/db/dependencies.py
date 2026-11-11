from typing import Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db


async def get_db_session() -> AsyncSession:
    async for session in get_db():
        return session

    raise RuntimeError("Database session could not be created")


async def get_request_context(request: Request) -> dict[str, Any]:
    return {
        "method": request.method,
        "path": request.url.path,
        "client": request.client.host if request.client else "unknown",
    }


DBSessionDep = Depends(get_db_session)
