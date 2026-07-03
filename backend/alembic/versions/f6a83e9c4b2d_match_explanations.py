"""match explanations

Revision ID: f6a83e9c4b2d
Revises: 7e7d91aae581
Create Date: 2026-07-03 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a83e9c4b2d"
down_revision: Union[str, None] = "7e7d91aae581"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("score_breakdown", sa.JSON(), nullable=True))
    op.add_column("matches", sa.Column("reasons", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "reasons")
    op.drop_column("matches", "score_breakdown")
