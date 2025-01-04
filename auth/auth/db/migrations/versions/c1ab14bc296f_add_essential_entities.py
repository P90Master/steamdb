"""Add essential entities

Revision ID: c1ab14bc296f
Revises: 5ae8b1e8d0a4
Create Date: 2025-01-04 18:19:21.978315

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from auth.core.config import settings
from auth.utils import hash_secret
from auth.models import Scope, Role, Client
from auth.models.associations import scope_role_association, client_role_association


# revision identifiers, used by Alembic.
revision: str = 'c1ab14bc296f'
down_revision: Union[str, None] = '5ae8b1e8d0a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

essential_scopes = [
    {'name': 'Backend: Package', 'description': 'Permission to POST app packages', 'action': 'backend/package'},
    {'name': 'Backend: Read', 'description': 'Permission to GET and LIST operations', 'action': 'backend/read'},
    {'name': 'Backend: All permissions', 'description': 'All permissions for backend service', 'action': 'backend/*'},
    {'name': 'Orchestrator: Tasks', 'description': 'Permission to register tasks and check its status', 'action': 'orchestrator/tasks'},
    {'name': 'Orchestrator: All permissions', 'description': 'All permissions for orchestrator service', 'action': 'orchestrator/*'},
    {'name': '*', 'description': 'All permissions', 'action': '*/*'}
]

essential_roles = [
    {'name': 'Worker', 'description': 'Workers interact with the Steam API to obtain apps data and send it to Backend'},
    {'name': 'Backend', 'description': 'Backend provides access to the Steam apps database and registers tasks to retrieve data about a certain apps if needed'},
]

essential_clients = [
    {
        'id': settings.ESSENTIAL_WORKER_CLIENT_ID,
        'secret': hash_secret(settings.ESSENTIAL_WORKER_CLIENT_SECRET),
        'name': 'Worker',
        'description': 'Worker interacts with the Steam API to obtain apps data and send it to Backend'
    },
    {
        'id': settings.ESSENTIAL_BACKEND_CLIENT_ID,
        'secret': hash_secret(settings.ESSENTIAL_BACKEND_CLIENT_SECRET),
        'name': 'Backend',
        'description': 'Backend provides access to the Steam apps database and registers tasks to retrieve data about a certain apps if needed'
    },
]


def upgrade() -> None:
    for scope in essential_scopes:
        op.execute(
            sa.insert(Scope).values(**scope)
        )

    for role in essential_roles:
        op.execute(
            sa.insert(Role).values(**role)
        )

    for client in essential_clients:
        op.execute(
            sa.insert(Client).values(**client)
        )

    op.execute(
        sa.insert(scope_role_association).values(scope_id=1, role_id=1)
    )
    op.execute(
        sa.insert(scope_role_association).values(scope_id=4, role_id=2)
    )
    op.execute(
        sa.insert(client_role_association).values(role_id=1, client_id=1)
    )
    op.execute(
        sa.insert(client_role_association).values(role_id=2, client_id=2)
    )


def downgrade() -> None:
    for scope in essential_scopes:
        op.execute(
            sa.delete(Scope).where(sa.column('action') == scope['action'])
        )

    for role in essential_roles:
        op.execute(
            sa.delete(Role).where(sa.column('name') == role['name'])
        )
