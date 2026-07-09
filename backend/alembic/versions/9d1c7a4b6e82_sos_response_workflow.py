"""sos response workflow

Revision ID: 9d1c7a4b6e82
Revises: 8b3d0f9a2c71
Create Date: 2026-07-09 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d1c7a4b6e82"
down_revision: Union[str, None] = "8b3d0f9a2c71"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sos_events", sa.Column("assigned_admin_id", sa.Integer(), nullable=True))
    op.add_column("sos_events", sa.Column("response_note", sa.Text(), nullable=True))
    op.add_column("sos_events", sa.Column("status_updated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_sos_events_assigned_admin_id"), "sos_events", ["assigned_admin_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sos_events_assigned_admin_id"), table_name="sos_events")
    op.drop_column("sos_events", "status_updated_at")
    op.drop_column("sos_events", "response_note")
    op.drop_column("sos_events", "assigned_admin_id")
