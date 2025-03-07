"""add new qad

Revision ID: e94ac3abca3a
Revises: d2be064b4d45
Create Date: 2025-03-05 09:51:29.245864

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e94ac3abca3a'
down_revision: Union[str, None] = 'd2be064b4d45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
