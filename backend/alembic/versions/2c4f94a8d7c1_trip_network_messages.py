"""trip network messages

Revision ID: 2c4f94a8d7c1
Revises: f6a83e9c4b2d
Create Date: 2026-07-06 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2c4f94a8d7c1"
down_revision: Union[str, None] = "f6a83e9c4b2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trip_messages",
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.String(length=600), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sender_id"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.trip_id"]),
        sa.PrimaryKeyConstraint("message_id"),
    )
    op.create_index(op.f("ix_trip_messages_message_id"), "trip_messages", ["message_id"], unique=False)
    op.create_index(op.f("ix_trip_messages_sender_id"), "trip_messages", ["sender_id"], unique=False)
    op.create_index(op.f("ix_trip_messages_trip_id"), "trip_messages", ["trip_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trip_messages_trip_id"), table_name="trip_messages")
    op.drop_index(op.f("ix_trip_messages_sender_id"), table_name="trip_messages")
    op.drop_index(op.f("ix_trip_messages_message_id"), table_name="trip_messages")
    op.drop_table("trip_messages")
