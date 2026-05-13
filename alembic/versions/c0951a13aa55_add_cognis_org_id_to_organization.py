"""add cognis_org_id to organization

Revision ID: c0951a13aa55
Revises: 1c28e167b74f
Create Date: 2026-05-13 09:00:00.000000

Cognis fork: adds a nullable `cognis_org_id` column on the `organizations`
table so the Cognis Concierge auth middleware can map a Clerk JWT
`org_id` claim onto a Letta organization. A partial unique index
enforces uniqueness only when the column is populated, leaving
upstream rows (which never set this column) unaffected.

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c0951a13aa55"
down_revision: Union[str, None] = "1c28e167b74f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    organization_columns = {column["name"] for column in inspector.get_columns("organizations")}
    if "cognis_org_id" not in organization_columns:
        op.add_column("organizations", sa.Column("cognis_org_id", sa.Text(), nullable=True))

    organization_indexes = {index["name"] for index in inspector.get_indexes("organizations")}
    if "ix_organizations_cognis_org_id" not in organization_indexes:
        # Partial unique index — only enforces uniqueness for rows where
        # cognis_org_id is populated. Upstream rows leave the column NULL.
        # Falls back to a plain unique index on SQLite (no partial index support).
        if bind.dialect.name == "postgresql":
            op.create_index(
                "ix_organizations_cognis_org_id",
                "organizations",
                ["cognis_org_id"],
                unique=True,
                postgresql_where=sa.text("cognis_org_id IS NOT NULL"),
            )
        else:
            op.create_index(
                "ix_organizations_cognis_org_id",
                "organizations",
                ["cognis_org_id"],
                unique=True,
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    organization_indexes = {index["name"] for index in inspector.get_indexes("organizations")}
    if "ix_organizations_cognis_org_id" in organization_indexes:
        op.drop_index("ix_organizations_cognis_org_id", table_name="organizations")

    organization_columns = {column["name"] for column in inspector.get_columns("organizations")}
    if "cognis_org_id" in organization_columns:
        op.drop_column("organizations", "cognis_org_id")
