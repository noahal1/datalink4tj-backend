#!/usr/bin/env python
"""
权限修复工具

此脚本用于检查和修复系统中的权限问题，包括：
1. 确保所有角色都有正确的权限
2. 确保所有路由都有正确的权限设置
3. 修复route_permissions表中的数据
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from db.session import get_db
from models.user import User
from models.permission import Role, Permission
from models.route import Route
from models.route_permission import RoutePermission
from services.permission_service import PermissionService
from services.route_service import RouteService
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("permission_fix.log")
    ]
)

logger = logging.getLogger(__name__)

def check_user_permissions(db: Session):
    """检查用户权限"""
    logger.info("开始检查用户权限")
    
    # 获取所有用户
    users = db.query(User).all()
    logger.info(f"系统中共有 {len(users)} 个用户")
    
    for user in users:
        logger.info(f"检查用户 {user.name} 的权限")
        
        # 检查用户角色
        roles = user.roles
        logger.info(f"用户 {user.name} 拥有角色: {[role.name for role in roles]}")
        
        # 检查用户是否有QA:READ权限
        has_qa_read = user.has_permission("QA", "READ")
        logger.info(f"用户 {user.name} 是否有QA:READ权限: {has_qa_read}")
    
    logger.info("用户权限检查完成")

def check_route_permissions(db: Session):
    """检查路由权限"""
    logger.info("开始检查路由权限")
    
    # 获取所有路由
    routes = db.query(Route).all()
    logger.info(f"系统中共有 {len(routes)} 个路由")
    
    for route in routes:
        logger.info(f"检查路由 {route.id}({route.name}) 的权限")
        
        # 获取meta信息
        meta = route.meta
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
                logger.info(f"路由 {route.id} 的meta是字符串格式，已转换为字典")
            except:
                meta = {}
                logger.warning(f"路由 {route.id} 的meta格式无效，已重置为空字典")
        
        # 检查meta是否是字典
        if not isinstance(meta, dict):
            logger.warning(f"路由 {route.id} 的meta不是字典格式，类型: {type(meta)}")
            meta = {}
        
        # 检查permission字段
        if "permission" in meta:
            permission = meta["permission"]
            logger.info(f"路由 {route.id} 的permission: {permission}")
            
            # 检查permission格式
            if isinstance(permission, dict):
                module = permission.get("module")
                level = permission.get("level")
                logger.info(f"路由 {route.id} 需要模块权限: {module}:{level}")
            elif isinstance(permission, str):
                if ":" in permission:
                    module, level = permission.split(":")
                    logger.info(f"路由 {route.id} 需要字符串权限: {module}:{level}")
                else:
                    logger.info(f"路由 {route.id} 需要部门权限: {permission}")
        else:
            logger.info(f"路由 {route.id} 没有permission字段，所有人可访问")
        
        # 检查allowed_roles字段
        if "allowed_roles" in meta:
            allowed_roles = meta["allowed_roles"]
            logger.info(f"路由 {route.id} 的allowed_roles: {allowed_roles}")
        
        # 检查route_permissions表
        route_permissions = db.query(RoutePermission).filter(RoutePermission.route_id == route.id).all()
        logger.info(f"路由 {route.id} 在route_permissions表中有 {len(route_permissions)} 条记录")
        
        # 打印允许访问的角色
        if route_permissions:
            role_ids = [perm.role_id for perm in route_permissions]
            roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
            logger.info(f"路由 {route.id} 允许的角色: {[role.name for role in roles]}")
    
    logger.info("路由权限检查完成")

def fix_route_permissions(db: Session):
    """修复路由权限"""
    logger.info("开始修复路由权限")
    
    # 获取所有路由
    routes = db.query(Route).all()
    logger.info(f"系统中共有 {len(routes)} 个路由")
    
    # 获取所有角色
    roles = db.query(Role).all()
    role_map = {role.name: role for role in roles}
    logger.info(f"系统中共有 {len(roles)} 个角色")
    
    # 特殊处理：确保质量页面可以被"普通用户"角色访问
    quality_route = db.query(Route).filter(Route.path == "/quality").first()
    if quality_route:
        logger.info(f"找到质量页面路由: {quality_route.id}({quality_route.name})")
        
        # 获取普通用户角色
        normal_user_role = role_map.get("普通用户")
        if normal_user_role:
            logger.info(f"找到普通用户角色: {normal_user_role.id}({normal_user_role.name})")
            
            # 检查是否已有权限记录
            existing_perm = db.query(RoutePermission).filter(
                RoutePermission.route_id == quality_route.id,
                RoutePermission.role_id == normal_user_role.id
            ).first()
            
            if not existing_perm:
                logger.info(f"为普通用户角色添加质量页面访问权限")
                route_perm = RoutePermission(
                    route_id=quality_route.id,
                    role_id=normal_user_role.id
                )
                db.add(route_perm)
                db.commit()
                logger.info(f"权限添加成功")
            else:
                logger.info(f"普通用户角色已有质量页面访问权限")
        else:
            logger.warning(f"未找到普通用户角色")
    else:
        logger.warning(f"未找到质量页面路由")
    
    logger.info("路由权限修复完成")

def main():
    """主函数"""
    logger.info("开始执行权限修复工具")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 检查用户权限
        check_user_permissions(db)
        
        # 检查路由权限
        check_route_permissions(db)
        
        # 修复路由权限
        fix_route_permissions(db)
        
        logger.info("权限修复工具执行完成")
    except Exception as e:
        logger.error(f"执行过程中出错: {str(e)}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    main() 