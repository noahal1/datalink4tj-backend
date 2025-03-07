"""add qa's customer

Revision ID: 18b470bceeb9
Revises: b900a967c84e
Create Date: 2025-02-28 13:56:16.126691

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18b470bceeb9'
down_revision: Union[str, None] = 'b900a967c84e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
