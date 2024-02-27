"""initial

Revision ID: 2dbbe08c0a1e
Revises: 
Create Date: 2024-02-20 13:20:38.025858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2dbbe08c0a1e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('files',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('size', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('type', sa.String(length=4), nullable=True),
    sa.Column('note', sa.String(length=255), nullable=True),
    sa.Column('is_public', sa.Boolean(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False, comment='File creation time'),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True, comment='Record creation time'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('storages',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('path', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('emoji',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('file_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=True),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('ip', sa.String(length=15), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True, comment='Record creation time'),
    sa.ForeignKeyConstraint(['file_id'], ['files.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('links',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('file_id', sa.Uuid(), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.Column('expire_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
    sa.ForeignKeyConstraint(['file_id'], ['files.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('storage_statistic',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('storage_id', sa.Uuid(), nullable=False),
    sa.Column('path', sa.String(length=255), nullable=False),
    sa.Column('files_count', sa.Integer(), nullable=False),
    sa.Column('folders_count', sa.Integer(), nullable=False),
    sa.Column('size', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True, comment='Record creation time'),
    sa.ForeignKeyConstraint(['storage_id'], ['storages.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_storage_statistic_path_created_at', 'storage_statistic', ['path', sa.text('created_at DESC')], unique=False)
    op.create_table('tags',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('file_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=True),
    sa.Column('ip', sa.String(length=15), nullable=True),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True, comment='Record creation time'),
    sa.ForeignKeyConstraint(['file_id'], ['files.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tags')
    op.drop_index('idx_storage_statistic_path_created_at', table_name='storage_statistic')
    op.drop_table('storage_statistic')
    op.drop_table('links')
    op.drop_table('emoji')
    op.drop_table('storages')
    op.drop_table('files')
    # ### end Alembic commands ###