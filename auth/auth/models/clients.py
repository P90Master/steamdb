import asyncio

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Mapped, relationship, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from auth.utils import hash_secret
from auth.db import Base, int_pk, str_index
from .permissions import Role, Scope
from .associations import client_scope_association, client_role_association


class Client(Base):
    pk: Mapped[int_pk]
    id: Mapped[str_index]
    secret: Mapped[str]
    name: Mapped[str] = None
    description: Mapped[str] = None

    access_tokens = relationship(
        "AccessToken",
        back_populates="client"
    )
    refresh_token = relationship(
        "RefreshToken",
        back_populates="client"
    )
    roles = relationship(
        "Role",
        secondary=client_role_association,
        back_populates="clients",
        cascade="all, delete"
    )
    personal_scopes  = relationship(
        "Scope",
        secondary=client_scope_association,
        back_populates="clients",
        cascade="all, delete"
    )

    def check_secret(self, secret: str) -> bool:
        return bcrypt.checkpw(secret.encode('utf-8'), self.secret.encode('utf-8'))

    @classmethod
    async def register(
            cls,
            session: AsyncSession,
            id_: str,
            secret: str,
            name: str,
            description: str,
            personal_scopes: list[str] | None = None,
            roles: list[str] | None = None
    ) -> 'Client':
        hashed_password = hash_secret(secret)

        new_client = cls(id=id_, name=name, secret=hashed_password, description=description)

        async def get_roles() -> list:
            coros = (
                session.execute(select(Role).where(Role.id == int(role_id))) for role_id in roles
            )
            results = await asyncio.gather(*coros)
            return [result.scalars().first() for result in results]

        async def get_scopes() -> list:
            coros = (
                session.execute(select(Scope).where(Scope.id == int(scope_id))) for scope_id in personal_scopes
            )
            results = await asyncio.gather(*coros)
            return [result.scalars().first() for result in results]

        roles_obj, scopes_obj = await asyncio.gather(get_roles(), get_scopes())
        new_client.roles.extend(roles_obj)
        new_client.personal_scopes.extend(scopes_obj)

        session.add(new_client)
        await session.commit()
        await session.refresh(new_client)
        return new_client

    async def get_all_scopes(self, session: AsyncSession) -> list[Scope]:
        stmt = (
            select(Client)
            .options(
                joinedload(Client.personal_scopes),
                joinedload(Client.roles).joinedload(Role.scopes)
            )
            .where(Client.id == self.id)
        )

        result = await session.execute(stmt)
        client = result.scalars().first()

        if not client:
            return []

        scopes = set()
        scopes.update(client.personal_scopes)

        for role in client.roles:
            scopes.update(role.scopes)

        return list(scopes)
