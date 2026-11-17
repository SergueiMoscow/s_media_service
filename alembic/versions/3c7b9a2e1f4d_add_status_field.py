"""add status field to files

Revision ID: 3c7b9a2e1f4d
Revises: eaa9f66b603d
Create Date: 2026-11-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c7b9a2e1f4d'
down_revision: Union[str, None] = 'eaa9f66b603d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'files',
        sa.Column(
            'status',
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
    )


def downgrade() -> None:
    op.drop_column('files', 'status')
