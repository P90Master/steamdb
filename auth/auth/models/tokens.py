import asyncio
from datetime import datetime
from secrets import token_hex
from typing import Annotated, List

from sqlalchemy import DateTime, func, select, update, text, ForeignKey, event
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from auth.core.config import settings
from auth.db import Base, int_pk, str_index
from auth.models.associations import token_scope_association
from auth.models.permissions import Scope
from auth.utils.cache import CacheManager


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
admin_token_expiring = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=text(f"now() + INTERVAL '{settings.ADMIN_TOKEN_EXPIRE_SECONDS} seconds'")
    )
]


class BaseToken(Base):
    __abstract__ = True

    id: Mapped[int_pk]
    token: Mapped[str_index]
    is_active: Mapped[bool]

    client_pk: Mapped[int] = mapped_column(ForeignKey("clients.pk"), nullable=True)


class AccessToken(BaseToken):
    expires_at: Mapped[access_token_expiring]

    client = relationship("Client", back_populates="access_tokens")
    scopes = relationship(
        "Scope",
        secondary=token_scope_association,
        back_populates="tokens",
    )

    @classmethod
    async def create_token(cls, session: AsyncSession, client_pk: int, scopes: List[Scope]) -> 'AccessToken':
        active_tokens_count_query = select(func.count()).select_from(
            cls
        ).where(
            cls.client_pk == client_pk,
            cls.is_active == True
        )
        active_tokens_count = (await session.execute(active_tokens_count_query)).scalar()

        # TODO: Threat of endless access_token creation spam. Request throttling for clients?
        if active_tokens_count >= settings.MAX_ACCESS_TOKENS_PER_CLIENT:
            query = update(cls).where(cls.client_pk == client_pk, cls.is_active == True).values(is_active=False)
            await session.execute(query)
            await session.commit()

        # TODO: think about token collisions
        new_token = cls(token=token_hex(settings.ACCESS_TOKEN_BYTES_LENGTH), client_pk=client_pk, is_active=True)
        new_token.scopes.extend(scopes)
        session.add(new_token)
        await session.commit()
        await session.refresh(new_token)
        return new_token


class RefreshToken(BaseToken):
    expires_at: Mapped[refresh_token_expiring]

    client = relationship("Client", back_populates="refresh_token")

    @classmethod
    async def get_or_create_token(cls, session: AsyncSession, client_pk: int) -> 'RefreshToken':
        sample = await session.execute(select(cls).where(cls.client_pk == client_pk, cls.is_active == True))
        token = sample.scalars().one_or_none()
        return token if token else await cls._create_token_unsafe(session, client_pk)

    @classmethod
    async def create_token(cls, session: AsyncSession, client_pk: int) -> 'RefreshToken':
        await session.execute(
            update(cls).where(cls.client_pk == client_pk, cls.is_active == True).values(is_active=False)
        )
        await session.commit()
        return await cls._create_token_unsafe(session, client_pk)

    @classmethod
    async def _create_token_unsafe(cls, session: AsyncSession, client_pk: int) -> 'RefreshToken':
        # TODO: think about token collisions
        new_token = cls(token=token_hex(settings.REFRESH_TOKEN_BYTES_LENGTH), client_pk=client_pk, is_active=True)
        session.add(new_token)
        await session.commit()
        return new_token


class AdminToken(Base):
    id: Mapped[int_pk]
    token: Mapped[str_index]
    is_active: Mapped[bool]

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True)
    expires_at: Mapped[admin_token_expiring]

    user = relationship("User", back_populates="tokens")

    @classmethod
    async def get_or_create_token(cls, session: AsyncSession, user_id: int) -> 'AdminToken':
        sample = await session.execute(select(cls).where(cls.user_id == user_id, cls.is_active == True))
        token = sample.scalars().one_or_none()
        return token if token else await cls._create_token_unsafe(session, user_id)

    @classmethod
    async def create_token(cls, session: AsyncSession, user_id: int) -> 'AdminToken':
        await session.execute(
            update(cls).where(cls.user_id == user_id, cls.is_active == True).values(is_active=False)
        )
        await session.commit()
        return await cls._create_token_unsafe(session, user_id)

    @classmethod
    async def _create_token_unsafe(cls, session: AsyncSession, user_id: int) -> 'AdminToken':
        # TODO: think about token collisions
        new_token = cls(token=token_hex(settings.ADMIN_TOKEN_BYTES_LENGTH), user_id=user_id, is_active=True)
        session.add(new_token)
        await session.commit()
        return new_token


async def clear_cache_task(target: str):
    cache_key = f'token_{target}'
    await CacheManager.clear(cache_key)


@event.listens_for(AccessToken, 'after_update')
def after_access_token_update(mapper, connection, target: AccessToken):
    asyncio.create_task(clear_cache_task(target.token))
