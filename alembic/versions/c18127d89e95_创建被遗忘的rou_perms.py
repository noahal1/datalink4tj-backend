"""创建被遗忘的rou—perms

Revision ID: c18127d89e95
Revises: f3420efa7eff
Create Date: 2025-06-16 14:22:22.867025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c18127d89e95'
down_revision: Union[str, None] = 'f3420efa7eff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
