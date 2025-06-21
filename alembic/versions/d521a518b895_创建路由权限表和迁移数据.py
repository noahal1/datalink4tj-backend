"""创建路由权限表和迁移数据

Revision ID: d521a518b895
Revises: 
Create Date: 2025-06-16 14:16:12.689750

"""
from typing import Sequence, Union
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision: str = 'd521a518b895'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

Base = declarative_base()

# 定义模型用于迁移数据
class Route(Base):
    __tablename__ = 'routes'
    id = sa.Column(sa.Integer, primary_key=True)
    meta = sa.Column(sa.JSON)

class Role(Base):
    __tablename__ = 'roles'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)

class RoutePermission(Base):
    __tablename__ = 'route_permissions'
    id = sa.Column(sa.Integer, primary_key=True)
    role_id = sa.Column(sa.Integer)
    route_id = sa.Column(sa.Integer)


def upgrade() -> None:
    # 第一步：创建路由权限表
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

    # 第二步：迁移数据
    # 创建数据库连接
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # 获取所有路由
        routes = session.query(Route).all()
        
        # 获取所有角色
        roles = session.query(Role).all()
        roles_dict = {role.id: role for role in roles}
        
        # 迁移权限数据
        for route in routes:
            if not route.meta:
                continue
                
            meta = route.meta
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except:
                    continue
                    
            if not isinstance(meta, dict):
                continue
                
            # 从meta中获取角色权限
            allowed_roles = meta.get('allowed_roles', [])
            
            # 如果没有allowed_roles，尝试从permission字段获取
            if not allowed_roles and meta.get('permission'):
                permission = meta.get('permission')
                # 如果permission是对象并且有roles字段
                if isinstance(permission, dict) and permission.get('roles'):
                    allowed_roles = permission.get('roles')
                # 如果permission是字符串"*"，表示所有角色都有权限
                elif permission == '*':
                    allowed_roles = [str(role.id) for role in roles]
            
            # 添加超级管理员角色
            super_admin = next((role for role in roles if role.name == "超级管理员"), None)
            if super_admin and str(super_admin.id) not in allowed_roles:
                allowed_roles.append(str(super_admin.id))
            
            # 为每个角色创建权限记录
            for role_id_str in allowed_roles:
                try:
                    role_id = int(role_id_str)
                    if role_id in roles_dict:
                        # 检查是否已存在记录
                        existing = session.query(RoutePermission).filter_by(
                            role_id=role_id, route_id=route.id
                        ).first()
                        
                        if not existing:
                            perm = RoutePermission(role_id=role_id, route_id=route.id)
                            session.add(perm)
                except ValueError:
                    # 如果role_id不是数字，尝试按名称查找
                    for role in roles:
                        if role.name == role_id_str:
                            # 检查是否已存在记录
                            existing = session.query(RoutePermission).filter_by(
                                role_id=role.id, route_id=route.id
                            ).first()
                            
                            if not existing:
                                perm = RoutePermission(role_id=role.id, route_id=route.id)
                                session.add(perm)
                            break
        
        # 提交事务
        session.commit()
        print("路由权限数据迁移完成")
        
    except Exception as e:
        session.rollback()
        print(f"迁移失败: {str(e)}")
        raise
    finally:
        session.close()


def downgrade() -> None:
    # 删除索引和表
    op.drop_index('uix_role_route', table_name='route_permissions')
    op.drop_index(op.f('ix_route_permissions_route_id'), table_name='route_permissions')
    op.drop_index(op.f('ix_route_permissions_role_id'), table_name='route_permissions')
    op.drop_table('route_permissions')
