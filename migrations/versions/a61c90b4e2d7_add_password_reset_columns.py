"""Add password reset token storage.

Revision ID: a61c90b4e2d7
Revises: 57382895edbf
Create Date: 2026-08-23
"""

from alembic import op
import sqlalchemy as sa


revision = "a61c90b4e2d7"
down_revision = "57382895edbf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The original migration creates metadata from the current ORM models on a
    # fresh database, while existing deployments need these columns added.
    existing_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "password_reset_token_hash" not in existing_columns:
        op.add_column("users", sa.Column("password_reset_token_hash", sa.String(length=255), nullable=True))
    if "password_reset_expires_at" not in existing_columns:
        op.add_column("users", sa.Column("password_reset_expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    existing_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "password_reset_expires_at" in existing_columns:
        op.drop_column("users", "password_reset_expires_at")
    if "password_reset_token_hash" in existing_columns:
        op.drop_column("users", "password_reset_token_hash")
