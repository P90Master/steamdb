from typing import List

import bcrypt
from sqlalchemy.orm import Mapped, relationship

from db.models import Base, str_pk
from .associations import client_scope_association, client_role_association


class Client(Base):
    id: Mapped[str_pk]
    secret: Mapped[str]
    name: Mapped[str]
    description: Mapped[str]

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
        back_populates="clients"
    )
    personal_scopes  = relationship(
        "Scope",
        secondary=client_scope_association,
        back_populates="clients"
    )

    @staticmethod
    def hash_secret(secret: str) -> str:
        return bcrypt.hashpw(secret.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_secret(self, secret: str) -> bool:
        return bcrypt.checkpw(secret.encode('utf-8'), self.secret.encode('utf-8'))

    @classmethod
    def register(
            cls,
            session,
            secret: str,
            name: str,
            description: str,
            personal_scopes,
            roles
    ) -> 'Client':
        hashed_password = cls.hash_secret(secret)

        new_client = cls(
            name=name,
            secret=hashed_password,
            description=description
        )

        new_client.roles.extend(roles)
        new_client.personal_scopes.extend(personal_scopes)
        session.add(new_client)
        session.commit()
        return new_client
