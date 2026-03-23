"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-23

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("google_id", sa.String(128), unique=True, nullable=False),
        sa.Column("email", sa.String(256), unique=True, nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("access_token_enc", sa.Text(), nullable=False),
        sa.Column("refresh_token_enc", sa.Text(), nullable=True),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "provider", name="uq_oauth_tokens_user_provider"),
    )

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("focus_hours_per_day", sa.Integer(), default=2),
        sa.Column("focus_days_per_week", sa.Integer(), default=5),
        sa.Column("focus_preferred_time", sa.String(16), default="morning"),
        sa.Column("focus_min_block_minutes", sa.Integer(), default=60),
        sa.Column("focus_max_block_minutes", sa.Integer(), default=120),
        sa.Column("work_start_hour", sa.Integer(), default=9),
        sa.Column("work_end_hour", sa.Integer(), default=18),
        sa.Column("work_timezone", sa.String(64), default="America/New_York"),
        sa.Column("work_days", sa.JSON(), default=[0, 1, 2, 3, 4]),
        sa.Column("meeting_buffer_minutes", sa.Integer(), default=5),
        sa.Column("allow_auto_move_meetings", sa.Boolean(), default=False),
        sa.Column("no_meeting_days", sa.JSON(), default=[]),
        sa.Column("slack_status_sync_enabled", sa.Boolean(), default=True),
        sa.Column("slack_focus_status_text", sa.String(100), default="Focus Time"),
        sa.Column("slack_focus_status_emoji", sa.String(64), default=":dart:"),
        sa.Column("gong_auto_record_enabled", sa.Boolean(), default=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "scheduling_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slug", sa.String(128), unique=True, nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), default=30),
        sa.Column("buffer_before", sa.Integer(), default=0),
        sa.Column("buffer_after", sa.Integer(), default=0),
        sa.Column("rolling_days_available", sa.Integer(), default=14),
        sa.Column("custom_availability", sa.JSON(), nullable=True),
        sa.Column("questions", sa.JSON(), default=[]),
        sa.Column("active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "gong_invites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("google_event_id", sa.String(256), nullable=False),
        sa.Column("invited_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "google_event_id", name="uq_gong_invites_user_event"),
    )


def downgrade() -> None:
    op.drop_table("gong_invites")
    op.drop_table("scheduling_links")
    op.drop_table("user_preferences")
    op.drop_table("oauth_tokens")
    op.drop_table("users")
