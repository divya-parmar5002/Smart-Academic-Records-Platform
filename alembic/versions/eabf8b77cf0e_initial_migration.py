"""Initial migration

Revision ID: eabf8b77cf0e
Revises:
Create Date: 2026-07-03

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "eabf8b77cf0e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.create_table(
        "user_sessions",

        sa.Column(
            "session_id",
            sa.Integer(),
            primary_key=True
        ),

        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "refresh_token_hash",
            sa.String(),
            nullable=False
        ),

        sa.Column(
            "device_name",
            sa.String(),
            nullable=False
        ),

        sa.Column(
            "device_type",
            sa.String(),
            nullable=False
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true")
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()")
        ),

        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()")
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            ondelete="CASCADE"
        )
    )

    op.create_index(
        "ix_user_sessions_session_id",
        "user_sessions",
        ["session_id"]
    )


def downgrade() -> None:

    op.drop_index(
        "ix_user_sessions_session_id",
        table_name="user_sessions"
    )

    op.drop_table("user_sessions")