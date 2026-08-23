"""Initial schema

Revision ID: 57382895edbf
Revises: 
Create Date: 2026-08-23 00:53:00.845687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57382895edbf'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Import every ORM model before creating the metadata.  This is deliberately
    # metadata-driven because this is the initial schema migration.
    from app import models  # noqa: F401
    from app.core.database import Base
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    from app import models  # noqa: F401
    from app.core.database import Base
    Base.metadata.drop_all(bind=op.get_bind())
