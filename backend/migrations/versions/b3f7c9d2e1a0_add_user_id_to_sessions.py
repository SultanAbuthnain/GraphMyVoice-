"""Add user_id to sessions for multi-tenant isolation

Revision ID: b3f7c9d2e1a0
Revises: 09eaa2708d5a
Create Date: 2026-07-23

Adds a user_id column to the sessions table so that every session is
owned by exactly one user.  All query endpoints now filter on this column,
preventing cross-user data leakage.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f7c9d2e1a0'
down_revision: Union[str, None] = '09eaa2708d5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the column as nullable first so existing rows don't violate the
    # NOT NULL constraint, then backfill, then tighten the constraint.
    op.add_column(
        'sessions',
        sa.Column('user_id', sa.String(length=255), nullable=True),
    )
    # Backfill any pre-existing rows with a sentinel value so we can make
    # the column non-nullable.  In a real production deployment you would
    # set this to the actual owner's ID before the second step.
    op.execute("UPDATE sessions SET user_id = 'migrated_user' WHERE user_id IS NULL")
    op.alter_column('sessions', 'user_id', nullable=False)
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.drop_column('sessions', 'user_id')
