from datetime import datetime
from secrets import token_hex
from typing import Annotated, List, Sequence

from sqlalchemy import DateTime, func, select, update, text, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from auth.config import settings
from auth.db import Base, int_pk, str_unique
from auth.models.associations import token_scope_association
from auth.models.permissions import Scope


access_token_expiring = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=text(f"now() + INTERVAL '{settings.ACCESS_TOKEN_EXPIRE_SECONDS} seconds'")
    )
]
refresh_token_expiring = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=text(f"now() + INTERVAL '{settings.REFRESH_TOKEN_EXPIRE_SECONDS} seconds'")
    )
]


class BaseToken(Base):
    __abstract__ = True

    id: Mapped[int_pk]
    token: Mapped[str_unique]
    is_active: Mapped[bool]

    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)


class AccessToken(BaseToken):
    expires_at: Mapped[access_token_expiring]

    client = relationship("Client", back_populates="access_tokens")
    scopes = relationship("Scope", secondary=token_scope_association, back_populates="tokens")

    @classmethod
    async def get_inactive_tokens(cls, session: AsyncSession) -> Sequence['AccessToken']:
        sample = await session.execute(select(cls).where(cls.is_active == False))
        return sample.scalars().all()

    @classmethod
    async def get_expired_active_tokens(cls, session: AsyncSession) -> Sequence['AccessToken']:
        sample = await session.execute(
            select(cls).where(cls.expires_at < func.now(), cls.is_active == True)
        )
        return sample.scalars().all()

    @classmethod
    async def create_token(cls, session: AsyncSession, client_id: str, scopes: List[Scope]) -> 'AccessToken':
        clients_tokens_query = select(cls).where(cls.client_id == client_id, cls.is_active == True)
        active_tokens_count = await session.execute(func.count(clients_tokens_query))

        if active_tokens_count >= settings.MAX_ACCESS_TOKENS_PER_CLIENT:
            query = update(cls).where(cls.client_id == client_id, cls.is_active == True).values(is_active=False)
            await session.execute(query)
            await session.commit()

        # TODO: think about token collisions
        new_token = cls(token=token_hex(settings.ACCESS_TOKEN_BYTES_LENGTH), client_id=client_id, is_active=True)
        new_token.scopes.extend(scopes)
        session.add(new_token)
        await session.commit()
        return new_token


class RefreshToken(BaseToken):
    expires_at: Mapped[refresh_token_expiring]

    client = relationship("Client", back_populates="refresh_token")

    @classmethod
    async def get_inactive_tokens(cls, session: AsyncSession) -> Sequence['RefreshToken']:
        sample = await session.execute(select(cls).where(cls.is_active == False))
        return sample.scalars().all()

    @classmethod
    async def get_expired_active_tokens(cls, session: AsyncSession) -> Sequence['RefreshToken']:
        sample = await session.execute(select(cls).where(cls.expires_at < func.now(), cls.is_active == True))
        return sample.scalars().all()

    @classmethod
    async def get_or_create_token(cls, session: AsyncSession, client_id: str) -> 'RefreshToken':
        sample = await session.execute(select(cls).where(cls.client_id == client_id, cls.is_active == True))
        token = sample.scalars().one_or_none()
        return token if token else await cls._create_token_unsafe(session, client_id)

    @classmethod
    async def create_token(cls, session: AsyncSession, client_id: str) -> 'RefreshToken':
        await session.execute(
            update(cls).where(cls.client_id == client_id, cls.is_active == True).values(is_active=False)
        )
        await session.commit()
        return await cls._create_token_unsafe(session, client_id)

    @classmethod
    async def _create_token_unsafe(cls, session: AsyncSession, client_id: str) -> 'RefreshToken':
        # TODO: think about token collisions
        new_token = cls(token=token_hex(settings.REFRESH_TOKEN_BYTES_LENGTH), client_id=client_id, is_active=True)
        session.add(new_token)
        await session.commit()
        return new_token
