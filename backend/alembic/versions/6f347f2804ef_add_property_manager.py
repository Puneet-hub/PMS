"""add property manager

Revision ID: 6f347f2804ef
Revises: 89b882db5d88
Create Date: 2026-08-22 15:49:22.246205

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6f347f2804ef"
down_revision: Union[str, Sequence[str], None] = "89b882db5d88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add manager_id temporarily as nullable
    op.add_column(
        "properties",
        sa.Column("manager_id", sa.Integer(), nullable=True)
    )

    # 2. Give existing properties a valid manager.
    #    User ID 1 already exists in your database.
    op.execute(
        "UPDATE properties SET manager_id = 1 WHERE manager_id IS NULL"
    )

    # 3. Make manager_id NOT NULL
    op.alter_column(
        "properties",
        "manager_id",
        existing_type=sa.Integer(),
        nullable=False
    )

    # 4. Create the foreign key
    op.create_foreign_key(
        "fk_properties_manager_id_users",
        "properties",
        "users",
        ["manager_id"],
        ["id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_properties_manager_id_users",
        "properties",
        type_="foreignkey"
    )

    op.drop_column("properties", "manager_id")