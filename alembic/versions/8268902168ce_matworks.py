"""matworks

Revision ID: 8268902168ce
Revises: e94ac3abca3a
Create Date: 2025-04-01 20:52:40.252536

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8268902168ce'
down_revision: Union[str, None] = 'e94ac3abca3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
