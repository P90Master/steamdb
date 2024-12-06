from typing import List
from sqlalchemy.orm import Mapped, relationship

from db.models import Base, int_pk
from .associations import scope_role_association


class Scope(Base):
    """
    Model of scope - permission that the client can request to allow it to access certain attributes or actions.

    Args:
        id (Mapped[int_pk]): An identifier for the scope.
        name (Mapped[str]): A name of the scope.
        action (Mapped[str]): An action associated with the scope.
        description (Mapped[str]): A human-readable description of the scope and what it allows the client to do.
    """
    id: Mapped[int_pk]
    name: Mapped[str]
    description: Mapped[str]
    action: Mapped[str]

    roles = relationship(
        "Role",
        secondary=scope_role_association,
        back_populates="scopes"
    )
    clients = relationship(
        "Client",
        secondary="client_scope",
        back_populates="personal_scopes"
    )


class Role(Base):
    """
    Model of role - permanent personalized set of scopes.

    Args:
        id (Mapped[int_pk]): An identifier for the role.
        name (Mapped[str]): A name of the role.
        description (Mapped[str]): A human-readable description of the role and what it allows the client to do.
        scopes (Mapped[List[Scope]]): A list of scopes that current role grants to the client.
    """
    id: Mapped[int_pk]
    name: Mapped[str]
    description: Mapped[str]

    scopes: Mapped[List[Scope]] = relationship(
        "Scope",
        secondary=scope_role_association,
        back_populates="roles"
    )
