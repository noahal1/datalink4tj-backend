#!/usr/bin/env python
"""
简化权限修复工具 - 专注于解决质量页面访问权限问题
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
from models.permission import Role, Permission, role_permission
from models.route import Route
from models.route_permission import RoutePermission
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def fix_quality_page_access(db: Session):
    """修复质量页面访问权限"""
    logger.info("开始修复质量页面访问权限")
    
    # 查找质量页面路由
    quality_route = db.query(Route).filter(Route.path == "/quality").first()
    if not quality_route:
        logger.warning("未找到质量页面路由，尝试查找名称包含'质量'的路由")
        quality_route = db.query(Route).filter(Route.name.like('%质量%')).first()
    
    if not quality_route:
        logger.error("无法找到质量页面路由，修复失败")
        return False
    
    logger.info(f"找到质量页面路由: ID={quality_route.id}, 路径={quality_route.path}, 名称={quality_route.name}")
    
    # 查找所有角色
    roles = db.query(Role).all()
    logger.info(f"系统中共有 {len(roles)} 个角色")
    
    # 为所有角色添加质量页面访问权限
    for role in roles:
        logger.info(f"处理角色: {role.name}")
        
        # 检查是否已有权限记录
        existing_perm = db.query(RoutePermission).filter(
            RoutePermission.route_id == quality_route.id,
            RoutePermission.role_id == role.id
        ).first()
        
        if not existing_perm:
            logger.info(f"为角色 {role.name} 添加质量页面访问权限")
            route_perm = RoutePermission(
                route_id=quality_route.id,
                role_id=role.id
            )
            db.add(route_perm)
        else:
            logger.info(f"角色 {role.name} 已有质量页面访问权限")
    
    # 修改质量页面路由的meta信息，确保权限设置正确
    meta = quality_route.meta
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except:
            meta = {}
    
    if not isinstance(meta, dict):
        meta = {}
    
    # 设置为公共路由
    meta["permission"] = "*"
    quality_route.meta = meta
    
    # 提交更改
    db.commit()
    logger.info("质量页面访问权限修复完成")
    return True

def add_qa_read_permission_to_roles(db: Session):
    """为所有角色添加QA:READ权限"""
    logger.info("开始为所有角色添加QA:READ权限")
    
    # 查找或创建QA:READ权限
    qa_read_perm = db.query(Permission).filter(
        Permission.module == "QA",
        Permission.level == "READ"
    ).first()
    
    if not qa_read_perm:
        logger.info("创建QA:READ权限")
        qa_read_perm = Permission(module="QA", level="READ")
        db.add(qa_read_perm)
        db.commit()
        db.refresh(qa_read_perm)
    
    # 为所有角色添加此权限
    roles = db.query(Role).all()
    for role in roles:
        logger.info(f"处理角色: {role.name}")
        
        # 检查角色是否已有此权限
        has_perm = False
        for perm in role.permissions:
            if perm.module == "QA" and perm.level == "READ":
                has_perm = True
                break
        
        if not has_perm:
            logger.info(f"为角色 {role.name} 添加QA:READ权限")
            role.permissions.append(qa_read_perm)
        else:
            logger.info(f"角色 {role.name} 已有QA:READ权限")
    
    # 提交更改
    db.commit()
    logger.info("QA:READ权限添加完成")
    return True

def main():
    """主函数"""
    logger.info("开始执行简化权限修复工具")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 修复质量页面访问权限
        fix_quality_page_access(db)
        
        # 为所有角色添加QA:READ权限
        add_qa_read_permission_to_roles(db)
        
        logger.info("权限修复完成")
    except Exception as e:
        logger.error(f"执行过程中出错: {str(e)}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 