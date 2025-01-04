from typing import Any

import bcrypt
from sqlalchemy.orm import Mapped, relationship, validates, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from auth.db import Base, int_pk, str_unique
from auth.utils import hash_secret


class User(Base):
    id: Mapped[int_pk]
    username: Mapped[str_unique]
    password: Mapped[str]
    tokens = relationship(
        "AdminToken",
        back_populates="user"
    )
    is_superuser: Mapped[bool] = mapped_column(default=False)

    @validates('username')
    def validate_username(self, key: Any, username: str):
        if len(username) < 5:
            raise ValueError("Username must be at least 5 characters long.")

        if len(username) > 64:
            raise ValueError("Username must be at most 64 characters long.")

        return username

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    @classmethod
    async def register(
            cls,
            session: AsyncSession,
            username: str,
            password: str,
            is_superuser: bool,
    ) -> 'User':
        hashed_password = hash_secret(password)

        new_user = cls(username=username, password=hashed_password, is_superuser=is_superuser)

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
