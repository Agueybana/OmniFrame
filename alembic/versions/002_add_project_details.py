"""Add Project.details markdown column."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002_add_project_details"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("details", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "details")
