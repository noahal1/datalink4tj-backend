"""add activity table if not exists

Revision ID: 4575b3854e82
Revises: add_activity_model
Create Date: 2025-05-30 12:26:10.033521

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import JSON


# revision identifiers, used by Alembic.
revision: str = '4575b3854e82'
down_revision: Union[str, None] = 'add_activity_model'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建一个语句来检查表是否存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # 检查表是否存在
    if 'activities' not in inspector.get_table_names():
        # 如果表不存在，创建它
        op.create_table(
            'activities',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('title', sa.String(length=255), nullable=False, comment='活动标题'),
            sa.Column('action', sa.String(length=255), nullable=False, comment='操作描述'),
            sa.Column('details', sa.Text(), nullable=True, comment='详细信息'),
            sa.Column('type', sa.String(length=50), nullable=False, comment='活动类型'),
            sa.Column('icon', sa.String(length=50), nullable=True, comment='图标'),
            sa.Column('color', sa.String(length=50), nullable=True, comment='颜色'),
            sa.Column('target', sa.String(length=255), nullable=True, comment='目标链接'),
            sa.Column('changes_before', JSON(), nullable=True, comment='变更前数据'),
            sa.Column('changes_after', JSON(), nullable=True, comment='变更后数据'),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('user_name', sa.String(length=50), nullable=True, comment='用户名称'),
            sa.Column('department', sa.String(length=50), nullable=True, comment='部门'),
            sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        # 创建索引
        op.create_index(op.f('ix_activities_id'), 'activities', ['id'], unique=False)
        
        print("活动表创建成功")
    else:
        print("活动表已存在，跳过创建")


def downgrade() -> None:
    # 删除表和索引
    op.drop_index(op.f('ix_activities_id'), table_name='activities')
    op.drop_table('activities')
