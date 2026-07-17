"""create wallets

Revision ID: e75cd1f91740
Revises:
Create Date: 2026-07-12 02:00:05.657289

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e75cd1f91740"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "wallets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("balance", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("wallets")
