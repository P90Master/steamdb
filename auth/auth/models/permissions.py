from typing import List
from sqlalchemy.orm import Mapped, relationship

from auth.db import Base, int_pk
from .associations import (
    scope_role_association,
    client_role_association,
    token_scope_association,
    client_scope_association
)


class Scope(Base):
    id: Mapped[int_pk]
    name: Mapped[str]
    description: Mapped[str]
    action: Mapped[str]

    roles = relationship(
        "Role",
        secondary=scope_role_association,
        back_populates="scopes",
        cascade="all, delete"
    )
    clients = relationship(
        "Client",
        secondary=client_scope_association,
        back_populates="personal_scopes",
        cascade="all, delete"
    )
    tokens = relationship(
        "AccessToken",
        secondary=token_scope_association,
        back_populates="scopes",
        cascade="all, delete"
    )


class Role(Base):
    id: Mapped[int_pk]
    name: Mapped[str]
    description: Mapped[str]

    scopes: Mapped[List[Scope]] = relationship(
        "Scope",
        secondary=scope_role_association,
        back_populates="roles",
        cascade = "all, delete"
    )
    clients = relationship(
        "Client",
        secondary=client_role_association,
        back_populates="roles",
        cascade="all, delete"
    )
