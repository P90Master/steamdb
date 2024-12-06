from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Mapped, relationship

from db.models import Base, str_pk
from models.associations import token_scope_association


class TokenType(Enum):
    """
    Token types.
    """
    ACCESS = "access"
    REFRESH = "refresh"


class BaseToken(Base):
    """
    Base token data.

    Args:
        token (str): The token value.
        expires_at (datetime): The expiration time of the token.
        client_id (str): The client_id of token owner.
    """

    token: Mapped[str_pk]
    expires_at: Mapped[datetime]
    client_id: Mapped[str_pk]

    client = relationship("Client", back_populates="tokens")


class AccessToken(BaseToken):
    """
    Access token data.

    Args:
        token (str): The token value.
        expires_at (datetime): The expiration time of the token.
        client_id (str): The client_id of token owner.
        scopes (List[Scope]): The scopes of the token.
    """
    scopes = relationship("Scope", secondary=token_scope_association, back_populates="tokens")


class RefreshToken(BaseToken):
    """
    Refresh token data.
    """
    pass
