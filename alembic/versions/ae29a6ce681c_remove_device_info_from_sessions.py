"""remove device info from sessions

Revision ID: ae29a6ce681c
Revises: eabf8b77cf0e
Create Date: 2026-07-07 13:52:00.084492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ae29a6ce681c'
down_revision: Union[str, Sequence[str], None] = 'eabf8b77cf0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_column("user_sessions", "device_name")
    op.drop_column("user_sessions", "device_type")
  

def downgrade():
    op.add_column(
        "user_sessions",
        sa.Column("device_name", sa.String(), nullable=False)
    )

    op.add_column(
        "user_sessions",
        sa.Column("device_type", sa.String(), nullable=False)
    )