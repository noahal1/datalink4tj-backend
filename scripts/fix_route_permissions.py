#!/usr/bin/env python
"""
路由权限修复脚本

此脚本用于修复路由的权限设置，确保meta数据和route_permissions表的数据一致
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from db.session import get_db
from models.route import Route
from models.route_permission import RoutePermission
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def fix_route_permissions(db: Session):
    """修复路由权限设置"""
    logger.info("开始修复路由权限设置")
    
    # 获取所有路由
    routes = db.query(Route).all()
    logger.info(f"找到 {len(routes)} 个路由")
    
    for route in routes:
        logger.info(f"处理路由: {route.id} - {route.path} - {route.name}")
        
        # 获取路由的meta数据
        meta = route.meta
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception as e:
                logger.error(f"解析路由 {route.id} 的meta数据失败: {str(e)}")
                meta = {}
        
        if not isinstance(meta, dict):
            meta = {}
        
        # 获取路由的权限记录
        permissions = db.query(RoutePermission).filter(
            RoutePermission.route_id == route.id
        ).all()
        
        # 从权限记录中获取角色ID
        role_ids = [perm.role_id for perm in permissions]
        
        # 更新meta数据中的allowed_roles字段
        meta['allowed_roles'] = [str(role_id) for role_id in role_ids]
        
        # 更新路由的meta数据
        route.meta = meta
        
        # 提交更改
        db.commit()
        
        logger.info(f"路由 {route.id} 的权限设置已修复，角色ID: {role_ids}")
    
    logger.info("路由权限设置修复完成")

def main():
    """主函数"""
    logger.info("开始执行路由权限修复脚本")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 修复路由权限设置
        fix_route_permissions(db)
        
        logger.info("路由权限修复完成")
    except Exception as e:
        logger.error(f"执行过程中出错: {str(e)}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 