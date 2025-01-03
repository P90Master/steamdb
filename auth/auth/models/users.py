import bcrypt
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.asyncio import AsyncSession

from auth.db import Base, int_pk, str_unique
from auth.utils import hash_secret


class User(Base):
    id: Mapped[int_pk]
    username: Mapped[str_unique]
    password: Mapped[str]

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    @classmethod
    async def register(
            cls,
            username: str,
            password: str,
            session: AsyncSession,
    ) -> 'User':
        hashed_password = hash_secret(password)

        new_user = cls(username=username, password=hashed_password)

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
