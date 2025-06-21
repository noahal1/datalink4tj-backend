"""创建被遗忘的rou—perms

Revision ID: 7a88cb9e988a
Revises: c18127d89e95
Create Date: 2025-06-16 14:26:05.071325

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a88cb9e988a'
down_revision: Union[str, None] = 'c18127d89e95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
