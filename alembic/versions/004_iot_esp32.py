"""Telemetria do ESP32 (Wokwi): dispositivos IoT e campos de risco térmico nas leituras.

Revision ID: 004
Revises: 003
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "iot_devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_iot_devices_device_id", "iot_devices", ["device_id"], unique=True)
    with op.batch_alter_table("readings") as batch:
        batch.add_column(sa.Column("source", sa.String(20), nullable=False, server_default="api"))
        batch.add_column(sa.Column("device_id", sa.String(64), nullable=True))
        batch.add_column(sa.Column("zone", sa.String(30), nullable=True))
        batch.add_column(sa.Column("heat_index_c", sa.Float(), nullable=True))
        batch.add_column(sa.Column("luminosity_lux", sa.Float(), nullable=True))
        batch.add_column(sa.Column("risk_level", sa.String(20), nullable=True))
        batch.add_column(sa.Column("heat_island_delta_c", sa.Float(), nullable=True))
        batch.add_column(sa.Column("official_temp_c", sa.Float(), nullable=True))
    op.create_index("ix_readings_device_id", "readings", ["device_id"])


def downgrade():
    op.drop_index("ix_readings_device_id", table_name="readings")
    with op.batch_alter_table("readings") as batch:
        for col in ("official_temp_c", "heat_island_delta_c", "risk_level", "luminosity_lux",
                    "heat_index_c", "zone", "device_id", "source"):
            batch.drop_column(col)
    op.drop_index("ix_iot_devices_device_id", table_name="iot_devices")
    op.drop_table("iot_devices")
