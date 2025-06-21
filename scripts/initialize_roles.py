#!/usr/bin/env python3
"""
角色初始化脚本 - 创建系统预设角色并分配相应权限

运行方法:
python -m scripts.initialize_roles
"""

import os
import sys
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import get_db
from models.permission import Role, Permission
from models.user import User

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 预设角色和权限
PREDEFINED_ROLES = [
    {
        "name": "超级管理员",
        "description": "系统超级管理员，拥有所有权限",
        "permissions": [
            {"module": "ALL", "level": "SUPER_ADMIN"}
        ]
    },
    {
        "name": "部门负责人",
        "description": "部门负责人，可以管理本部门数据和用户",
        "permissions": [
            {"module": "USER", "level": "WRITE"},  # 管理本部门用户
            {"module": "DATA", "level": "ADMIN"},  # 管理本部门数据
            {"module": "REPORT", "level": "ADMIN"},  # 管理本部门报表
            {"module": "EVENT", "level": "ADMIN"}   # 管理本部门事件
        ]
    },
    {
        "name": "班组负责人",
        "description": "班组负责人，可以管理班组数据",
        "permissions": [
            {"module": "DATA", "level": "WRITE"},  # 编辑数据
            {"module": "REPORT", "level": "WRITE"},  # 编辑报表
            {"module": "EVENT", "level": "WRITE"}   # 编辑事件
        ]
    },
    {
        "name": "普通用户",
        "description": "普通用户，基础查看权限",
        "permissions": [
            {"module": "DATA", "level": "READ"},  # 查看数据
            {"module": "REPORT", "level": "READ"},  # 查看报表
            {"module": "EVENT", "level": "READ"}   # 查看事件
        ]
    }
]


def create_role_if_not_exists(db: Session, role_data):
    """创建角色（如果不存在）"""
    role_name = role_data["name"]
    
    # 检查角色是否已存在
    existing_role = db.query(Role).filter(Role.name == role_name).first()
    
    if existing_role:
        logger.info(f"角色 '{role_name}' 已存在，更新描述")
        existing_role.description = role_data["description"]
        db.commit()
        return existing_role
    
    # 创建新角色
    new_role = Role(name=role_name, description=role_data["description"])
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    logger.info(f"创建角色: {role_name}")
    return new_role


def get_or_create_permission(db: Session, permission_data):
    """获取或创建权限"""
    module = permission_data["module"]
    level = permission_data["level"]
    
    # 检查权限是否已存在
    existing_permission = db.query(Permission).filter(
        Permission.module == module,
        Permission.level == level,
        Permission.department_id == None  # 全局权限
    ).first()
    
    if existing_permission:
        return existing_permission
    
    # 创建新权限
    new_permission = Permission(module=module, level=level)
    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)
    
    logger.info(f"创建权限: {module}:{level}")
    return new_permission


def assign_permission_to_role(db: Session, role, permission):
    """为角色分配权限"""
    # 检查角色是否已有该权限
    statement = text("""
        SELECT 1 FROM role_permission 
        WHERE role_id = :role_id AND permission_id = :permission_id
    """)
    
    result = db.execute(statement, {
        "role_id": role.id, 
        "permission_id": permission.id
    }).fetchone()
    
    if result:
        logger.debug(f"角色 '{role.name}' 已有权限 {permission.module}:{permission.level}")
        return
    
    # 添加权限到角色
    insert_statement = text("""
        INSERT INTO role_permission (role_id, permission_id)
        VALUES (:role_id, :permission_id)
    """)
    
    db.execute(insert_statement, {
        "role_id": role.id, 
        "permission_id": permission.id
    })
    
    logger.info(f"为角色 '{role.name}' 添加权限: {permission.module}:{permission.level}")


def initialize_roles():
    """初始化预设角色"""
    db = next(get_db())
    
    try:
        logger.info("开始初始化预设角色...")
        
        for role_data in PREDEFINED_ROLES:
            # 创建角色
            role = create_role_if_not_exists(db, role_data)
            
            # 为角色分配权限
            for permission_data in role_data["permissions"]:
                permission = get_or_create_permission(db, permission_data)
                assign_permission_to_role(db, role, permission)
        
        logger.info("角色初始化完成")
        
    except Exception as e:
        logger.error(f"初始化角色时出错: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    initialize_roles() 