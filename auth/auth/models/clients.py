from typing import List
from sqlalchemy.orm import Mapped, relationship

from db.models import Base, str_pk
from .permissions import Scope, Role
from .associations import client_scope_association, client_role_association


class Client(Base):
    """
    Model of client - registered application/service in the system by this auth service.

    Args:
        client_id (Mapped[str_pk]): The client's identifier.
        client_secret (Mapped[str]): A random string that is used to authenticate the application. Stored as a hash.
        name (Mapped[str]): The name of the client.
        description (Mapped[str]): A description of the application/service/client and why it needs access to certain scopes.
        roles (Mapped[List[Role]]): List of roles provided to the client.
        personal_scopes (Mapped[List[Scope]]): List of personal scopes provided to the client.
    """

    client_id: Mapped[str_pk]
    client_secret: Mapped[str]
    name: Mapped[str]
    description: Mapped[str]

    roles: Mapped[List[Role]] = relationship(
        "Role",
        secondary=client_role_association,
        back_populates="clients"
    )
    personal_scopes: Mapped[List[Scope]]  = relationship(
        "Scope",
        secondary=client_scope_association,
        back_populates="clients"
    )
