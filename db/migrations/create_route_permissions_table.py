"""创建路由权限表

Revision ID: route_permissions_table
Create Date: 2023-12-01 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = 'route_permissions_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建路由权限表
    op.create_table(
        'route_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now(), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index(op.f('ix_route_permissions_role_id'), 'route_permissions', ['role_id'], unique=False)
    op.create_index(op.f('ix_route_permissions_route_id'), 'route_permissions', ['route_id'], unique=False)
    
    # 创建唯一约束，确保每个角色-路由组合只出现一次
    op.create_index('uix_role_route', 'route_permissions', ['role_id', 'route_id'], unique=True)


def downgrade():
    # 删除索引和表
    op.drop_index('uix_role_route', table_name='route_permissions')
    op.drop_index(op.f('ix_route_permissions_route_id'), table_name='route_permissions')
    op.drop_index(op.f('ix_route_permissions_role_id'), table_name='route_permissions')
    op.drop_table('route_permissions') 