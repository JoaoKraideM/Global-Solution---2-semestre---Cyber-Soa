"""Adiciona proveniência demonstrativa aos registros de segurança.

Revision ID: 002
Revises: 001
"""
from alembic import op
import sqlalchemy as sa
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("security_events", sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("audit_findings", sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()))

def downgrade():
    op.drop_column("audit_findings", "is_demo")
    op.drop_column("security_events", "is_demo")
