import bcrypt
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.asyncio import AsyncSession

from auth.db import Base, int_pk, str_unique


class User(Base):
    id: Mapped[int_pk]
    username: Mapped[str_unique]
    password: Mapped[str]

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_secret(self, secret: str) -> bool:
        return bcrypt.checkpw(secret.encode('utf-8'), self.password.encode('utf-8'))

    @classmethod
    async def register(
            cls,
            session: AsyncSession,
            username: str,
            password: str,
    ) -> 'User':
        hashed_password = cls.hash_password(password)

        new_user = cls(name=username, password=hashed_password)

        session.add(new_user)
        await session.commit()
        return new_user
