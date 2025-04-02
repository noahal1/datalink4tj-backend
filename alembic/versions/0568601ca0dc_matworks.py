"""matworks

Revision ID: 0568601ca0dc
Revises: 8268902168ce
Create Date: 2025-04-01 20:56:23.044118

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0568601ca0dc'
down_revision: Union[str, None] = '8268902168ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
