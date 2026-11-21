"""add password hash to users

Revision ID: 6d09ea78836c
Revises: 551614facd0f
Create Date: 2026-08-22 23:06:08.876350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d09ea78836c'
down_revision: Union[str, Sequence[str], None] = '551614facd0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        'users',
        sa.Column(
            'password_hash',
            sa.String(length=255),
            nullable=True
        )
    )

    op.execute(
        "UPDATE users SET password_hash = 'TEMP_PASSWORD_HASH'"
    )

    op.alter_column(
        'users',
        'password_hash',
        existing_type=sa.String(length=255),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column('users', 'password_hash')