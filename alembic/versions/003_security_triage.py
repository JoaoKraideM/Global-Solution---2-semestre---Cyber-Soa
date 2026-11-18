"""Centro operacional e trilha de tratamento de incidentes.

Revision ID: 003
Revises: 002
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("security_events", sa.Column("triage_status", sa.String(20), nullable=False, server_default="new"))
    op.add_column("security_events", sa.Column("triage_note", sa.String(300), nullable=False, server_default=""))
    op.add_column("security_events", sa.Column("triaged_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table("security_triage_actions",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("event_id",sa.Integer(),sa.ForeignKey("security_events.id"),nullable=False),
        sa.Column("actor_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),
        sa.Column("previous_status",sa.String(20),nullable=False),
        sa.Column("next_status",sa.String(20),nullable=False),
        sa.Column("note",sa.String(300),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_security_triage_actions_event_id", "security_triage_actions", ["event_id"])

def downgrade():
    op.drop_index("ix_security_triage_actions_event_id",table_name="security_triage_actions")
    op.drop_table("security_triage_actions")
    op.drop_column("security_events","triaged_at")
    op.drop_column("security_events","triage_note")
    op.drop_column("security_events","triage_status")
