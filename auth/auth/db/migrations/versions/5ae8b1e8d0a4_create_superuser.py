"""create superuser

Revision ID: 5ae8b1e8d0a4
Revises: d4d14a21032a
Create Date: 2025-01-03 21:49:12.006014

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from auth.core.config import settings
from auth.utils import hash_secret


# revision identifiers, used by Alembic.
revision: str = '5ae8b1e8d0a4'
down_revision: Union[str, None] = '24cfc43dd154'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            f"INSERT INTO users (username, password, is_superuser) VALUES ('{settings.SUPERUSER_USERNAME}', '{hash_secret(settings.SUPERUSER_PASSWORD)}', true)"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM users WHERE id = 1"
        )
    )
