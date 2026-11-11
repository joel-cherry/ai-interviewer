from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = UserRepository(session)

    async def create(self, payload: UserCreate) -> User:
        existing = await self.repository.get_by_email(payload.email)
        if existing:
            raise ValueError("User with this email already exists")

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            is_active=payload.is_active,
        )
        return await self.repository.create(user)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.repository.get_by_id(user_id)

    async def list(self, *, offset: int = 0, limit: int | None = None) -> list[User]:
        return await self.repository.list(offset=offset, limit=limit)

    async def update(self, user_id: UUID, payload: UserUpdate) -> User | None:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            return None

        if payload.email is not None:
            user.email = payload.email
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.is_active is not None:
            user.is_active = payload.is_active

        await self.repository.session.commit()
        await self.repository.session.refresh(user)
        return user

    async def delete(self, user_id: UUID) -> bool:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            return False
        await self.repository.delete(user)
        return True
