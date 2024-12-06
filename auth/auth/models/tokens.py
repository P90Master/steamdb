from datetime import datetime
from secrets import token_hex
from typing import Annotated, List

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, relationship, mapped_column

from config import settings
from db.models import Base, str_pk
from models.associations import token_scope_association
from models.permissions import Scope

access_token_expiring = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now() + func.interval(settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    )
]
refresh_token_expiring = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now() + func.interval(settings.REFRESH_TOKEN_EXPIRE_SECONDS)
    )
]


class BaseToken(Base):
    __abstract__ = True

    token: Mapped[str_pk]
    client_id: Mapped[str_pk]
    is_active: Mapped[bool]


class AccessToken(BaseToken):
    client = relationship("Client", back_populates="access_tokens")
    expires_at: Mapped[access_token_expiring]
    scopes = relationship("Scope", secondary=token_scope_association, back_populates="tokens")

    @classmethod
    def get_inactive_tokens(cls, session) -> List['AccessToken']:
        return session.query(cls).filter(cls.is_active == False).all()

    @classmethod
    def get_expired_active_tokens(cls, session) -> List['AccessToken']:
        return session.query(cls).filter(cls.expires_at < func.now(), cls.is_active == True).all()

    @classmethod
    def create_token(cls, session, client_id: str, scopes: List[Scope]) -> 'AccessToken':
        clients_tokens_query = session.query(cls).filter(cls.client_id == client_id, cls.is_active == True)
        active_tokens_count = clients_tokens_query.count()

        if active_tokens_count >= settings.MAX_ACCESS_TOKENS_PER_CLIENT:
            clients_tokens_query.update({cls.is_active: False})
            session.commit()

        # TODO: think about token collisions
        new_token = cls(token=token_hex(settings.ACCESS_TOKEN_BYTES_LENGTH), client_id=client_id, is_active=True)
        new_token.scopes.extend(scopes)
        session.add(new_token)
        session.commit()
        return new_token


class RefreshToken(BaseToken):
    client = relationship("Client", back_populates="refresh_token")
    expires_at: Mapped[refresh_token_expiring]

    @classmethod
    def get_inactive_tokens(cls, session) -> List['RefreshToken']:
        return session.query(cls).filter(cls.is_active == False).all()

    @classmethod
    def get_expired_active_tokens(cls, session) -> List['RefreshToken']:
        return session.query(cls).filter(cls.expires_at < func.now(), cls.is_active == True).all()

    @classmethod
    def get_or_create_token(cls, session, client_id: str) -> 'RefreshToken':
        token = session.query(cls).filter(cls.client_id == client_id, cls.is_active == True).first()
        return token if token else cls._create_token_unsafe(session, client_id)

    @classmethod
    def create_token(cls, session, client_id: str) -> 'RefreshToken':
        session.query(cls).filter(cls.client_id == client_id, cls.is_active == True).update({cls.is_active: False})
        session.commit()
        return cls._create_token_unsafe(session, client_id)

    @classmethod
    def _create_token_unsafe(cls, session, client_id: str) -> 'RefreshToken':
        # TODO: think about token collisions
        new_token = cls(token=token_hex(settings.REFRESH_TOKEN_BYTES_LENGTH), client_id=client_id, is_active=True)
        session.add(new_token)
        session.commit()
        return new_token
