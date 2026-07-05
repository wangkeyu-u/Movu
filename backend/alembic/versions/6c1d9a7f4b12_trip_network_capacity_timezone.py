"""trip network capacity and timezone metadata

Revision ID: 6c1d9a7f4b12
Revises: 2c4f94a8d7c1
Create Date: 2026-07-06 01:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6c1d9a7f4b12"
down_revision: Union[str, None] = "2c4f94a8d7c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ride_requests",
        sa.Column("preferred_time_timezone", sa.String(length=64), nullable=False, server_default="Asia/Kuala_Lumpur"),
    )
    op.add_column(
        "trips",
        sa.Column("departure_time_timezone", sa.String(length=64), nullable=False, server_default="Asia/Kuala_Lumpur"),
    )
    op.create_index("ix_matches_trip_status", "matches", ["trip_id", "status"], unique=False)
    op.create_index("ix_matches_request_status", "matches", ["request_id", "status"], unique=False)
    op.create_index("ix_trips_status_departure", "trips", ["status", "departure_time"], unique=False)
    op.create_index("ix_ride_requests_status_time", "ride_requests", ["status", "preferred_time"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ride_requests_status_time", table_name="ride_requests")
    op.drop_index("ix_trips_status_departure", table_name="trips")
    op.drop_index("ix_matches_request_status", table_name="matches")
    op.drop_index("ix_matches_trip_status", table_name="matches")
    op.drop_column("trips", "departure_time_timezone")
    op.drop_column("ride_requests", "preferred_time_timezone")
