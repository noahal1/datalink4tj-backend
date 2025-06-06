"""Add activity model

Revision ID: add_activity_model
Revises: 0568601ca0dc
Create Date: 2023-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import JSON


# revision identifiers, used by Alembic.
revision = 'add_activity_model'
down_revision = '0568601ca0dc'  # 基于最新的迁移
branch_labels = None
depends_on = None


def upgrade():
    # 创建活动表
    op.create_table(
        'activities',
        sa.Column('id', sa.Integer(), nullable=False),
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


def downgrade():
    # 删除表和索引
    op.drop_index(op.f('ix_activities_id'), table_name='activities')
    op.drop_table('activities') 