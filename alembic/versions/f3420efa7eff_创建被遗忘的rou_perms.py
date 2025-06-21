"""创建被遗忘的rou—perms

Revision ID: f3420efa7eff
Revises: d521a518b895
Create Date: 2025-06-16 14:20:17.460862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3420efa7eff'
down_revision: Union[str, None] = 'd521a518b895'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
