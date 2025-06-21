#!/usr/bin/env python
"""
路由角色权限修复工具 - 简化版

此脚本用于确保所有路由都有正确的角色权限设置，特别是质量相关页面
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
from models.permission import Role
from models.route import Route
from models.route_permission import RoutePermission
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def ensure_route_role_permissions(db: Session):
    """确保所有路由都有角色权限设置"""
    logger.info("开始确保所有路由都有角色权限设置")
    
    # 获取所有角色
    roles = db.query(Role).all()
    if not roles:
        logger.error("没有找到任何角色，请先创建角色")
        return False
    
    logger.info(f"找到 {len(roles)} 个角色")
    
    # 获取所有路由
    routes = db.query(Route).all()
    logger.info(f"找到 {len(routes)} 个路由")
    
    # 为每个路由设置角色权限
    for route in routes:
        logger.info(f"处理路由: {route.id} - {route.path} - {route.name}")
        
        # 获取当前路由的角色权限
        existing_perms = db.query(RoutePermission).filter(
            RoutePermission.route_id == route.id
        ).all()
        
        # 如果没有任何角色权限，则为所有角色添加权限
        if not existing_perms:
            logger.info(f"路由 {route.id} 没有角色权限，为所有角色添加权限")
            for role in roles:
                perm = RoutePermission(
                    route_id=route.id,
                    role_id=role.id
                )
                db.add(perm)
            
            # 更新路由的meta信息
            meta = route.meta
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except:
                    meta = {}
            
            if not isinstance(meta, dict):
                meta = {}
            
            # 添加allowed_roles字段
            meta["allowed_roles"] = [str(role.id) for role in roles]
            route.meta = meta
        else:
            logger.info(f"路由 {route.id} 已有 {len(existing_perms)} 个角色权限")
    
    # 提交更改
    db.commit()
    logger.info("路由角色权限设置完成")
    return True

def fix_quality_routes(db: Session):
    """特别处理质量相关页面，确保所有角色都有权限访问"""
    logger.info("开始处理质量相关页面")
    
    # 获取所有角色
    roles = db.query(Role).all()
    if not roles:
        logger.error("没有找到任何角色，请先创建角色")
        return False
    
    # 查找质量相关页面
    quality_routes = db.query(Route).filter(
        (Route.path == '/quality') | (Route.path == '/qa_others')
    ).all()
    
    if not quality_routes:
        logger.warning("未找到质量相关页面")
        return False
    
    logger.info(f"找到 {len(quality_routes)} 个质量相关页面")
    
    # 为每个质量页面设置所有角色权限
    for route in quality_routes:
        logger.info(f"处理质量页面: {route.id} - {route.path} - {route.name}")
        
        # 删除现有权限
        db.query(RoutePermission).filter(
            RoutePermission.route_id == route.id
        ).delete()
        
        # 为所有角色添加权限
        for role in roles:
            perm = RoutePermission(
                route_id=route.id,
                role_id=role.id
            )
            db.add(perm)
        
        # 更新路由的meta信息
        meta = route.meta
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except:
                meta = {}
        
        if not isinstance(meta, dict):
            meta = {}
        
        # 设置为公共路由
        meta["permission"] = "*"
        # 添加allowed_roles字段
        meta["allowed_roles"] = [str(role.id) for role in roles]
        route.meta = meta
    
    # 提交更改
    db.commit()
    logger.info("质量相关页面权限设置完成")
    return True

def main():
    """主函数"""
    logger.info("开始执行路由角色权限修复工具")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 确保所有路由都有角色权限
        ensure_route_role_permissions(db)
        
        # 特别处理质量相关页面
        fix_quality_routes(db)
        
        logger.info("路由角色权限修复完成")
    except Exception as e:
        logger.error(f"执行过程中出错: {str(e)}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 