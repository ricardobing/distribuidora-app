"""004 add telefono to remitos

Revision ID: 004
Revises: 003
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("remitos", sa.Column("telefono", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("remitos", "telefono")
