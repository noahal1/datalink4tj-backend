"""迁移路由权限数据

Revision ID: migrate_route_permissions
Create Date: 2023-12-01 11:00:00

"""
from alembic import op
import sqlalchemy as sa
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = 'migrate_route_permissions'
down_revision = 'route_permissions_table'
branch_labels = None
depends_on = None

Base = declarative_base()

# 定义模型
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


def upgrade():
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


def downgrade():
    # 不需要回滚数据，因为我们保留了原始的meta数据
    pass 