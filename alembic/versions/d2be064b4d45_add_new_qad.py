"""add new qad

Revision ID: d2be064b4d45
Revises: 18b470bceeb9
Create Date: 2025-03-05 09:43:34.838511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2be064b4d45'
down_revision: Union[str, None] = '18b470bceeb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
