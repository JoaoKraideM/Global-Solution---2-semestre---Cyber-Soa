"""initial domain models
Revision ID: 001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("stations",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(150), nullable=False), sa.Column("setting", sa.String(120), nullable=False),
        sa.Column("simulated", sa.Boolean(), nullable=False), sa.Column("api_key_hash", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_stations_code", "stations", ["code"], unique=True)
    op.create_table("readings",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("station_id", sa.Integer(), sa.ForeignKey("stations.id"), nullable=False),
        sa.Column("temperature_c", sa.Float(), nullable=False), sa.Column("humidity_pct", sa.Float(), nullable=False),
        sa.Column("is_simulated", sa.Boolean(), nullable=False), sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_readings_station_id", "readings", ["station_id"])
    op.create_index("ix_readings_measured_at", "readings", ["measured_at"])
    op.create_table("security_events", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(50), nullable=False), sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("outcome", sa.String(30), nullable=False), sa.Column("summary", sa.String(300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("audit_findings", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(80), nullable=False), sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("source", sa.String(60), nullable=False), sa.Column("sink", sa.String(60), nullable=False),
        sa.Column("field", sa.String(80), nullable=False), sa.Column("action", sa.String(30), nullable=False),
        sa.Column("evidence_redacted", sa.String(200), nullable=False), sa.Column("remediation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

def downgrade():
    op.drop_table("audit_findings")
    op.drop_table("security_events")
    op.drop_index("ix_readings_measured_at", table_name="readings")
    op.drop_index("ix_readings_station_id", table_name="readings")
    op.drop_table("readings")
    op.drop_index("ix_stations_code", table_name="stations")
    op.drop_table("stations")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
