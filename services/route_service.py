from sqlalchemy.orm import Session
from models.route import Route
from models.permission import Role
from models.route_permission import RoutePermission
from schemas.route import RouteCreate, RouteUpdate
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
import logging
import json

logger = logging.getLogger(__name__)

class RouteService:
    """路由服务类"""
    
    @staticmethod
    def get_all_routes(db: Session) -> List[Route]:
        """
        获取所有路由
        
        参数:
        - db: 数据库会话
        
        返回:
        - List[Route]: 路由列表
        """
        try:
            return db.query(Route).order_by(Route.sort_order).all()
        except SQLAlchemyError as e:
            logger.error(f"获取所有路由失败: {str(e)}")
            raise
    
    @staticmethod
    def get_route_by_id(db: Session, route_id: int) -> Optional[Route]:
        """
        通过ID获取路由
        
        参数:
        - db: 数据库会话
        - route_id: 路由ID
        
        返回:
        - Optional[Route]: 路由对象，如果不存在返回None
        """
        try:
            return db.query(Route).filter(Route.id == route_id).first()
        except SQLAlchemyError as e:
            logger.error(f"通过ID获取路由失败: {str(e)}")
            raise
    
    @staticmethod
    def get_route_by_path(db: Session, path: str) -> Optional[Route]:
        """
        通过路径获取路由
        
        参数:
        - db: 数据库会话
        - path: 路由路径
        
        返回:
        - Optional[Route]: 路由对象，如果不存在返回None
        """
        try:
            return db.query(Route).filter(Route.path == path).first()
        except SQLAlchemyError as e:
            logger.error(f"通过路径获取路由失败: {str(e)}")
            raise
    
    @staticmethod
    def create_route(db: Session, route: RouteCreate) -> Route:
        """
        创建新路由
        
        参数:
        - db: 数据库会话
        - route: 路由创建模型
        
        返回:
        - Route: 创建的路由对象
        """
        try:
            # 创建路由对象
            route_data = route.dict(exclude={"path_config"})
            
            # 创建meta数据副本，确保permissions字段存在
            if route_data.get("meta") is not None:
                meta_dict = dict(route_data["meta"])
                if "permissions" not in meta_dict:
                    meta_dict["permissions"] = []
                route_data["meta"] = meta_dict
            else:
                route_data["meta"] = {"permissions": []}
            
            # 处理路径配置
            if route.path_config:
                # 将路径配置保存到meta中
                route_data["meta"]["pathConfig"] = route.path_config.dict()
                
                # 如果有动态参数，更新路径
                if route.path_config.hasDynamicSegments and route.path_config.params:
                    # 构建带参数的路径
                    path = route.path_config.basePath
                    for param in route.path_config.params:
                        param_suffix = "" if param.required else "?"
                        path += f"/:{param.name}{param_suffix}"
                    route_data["path"] = path
            
            db_route = Route(**route_data)
            
            # 保存到数据库
            db.add(db_route)
            db.commit()
            db.refresh(db_route)
            
            logger.info(f"路由创建成功: {route.name} (ID: {db_route.id})")
            return db_route
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"创建路由失败: {str(e)}")
            raise
    
    @staticmethod
    def update_route(db: Session, route_id: int, route: RouteUpdate) -> Optional[Route]:
        """
        更新路由
        
        参数:
        - db: 数据库会话
        - route_id: 路由ID
        - route: 路由更新模型
        
        返回:
        - Optional[Route]: 更新后的路由对象，如果不存在返回None
        """
        try:
            # 查找路由
            db_route = RouteService.get_route_by_id(db, route_id)
            if not db_route:
                logger.warning(f"更新路由失败: ID {route_id} 不存在")
                return None
            
            # 更新路由字段
            update_data = route.dict(exclude={"path_config"}, exclude_unset=True)
            
            # 如果更新了meta字段，确保权限信息正确
            if "meta" in update_data:
                meta_dict = dict(update_data["meta"])
                if "permissions" not in meta_dict:
                    # 保留原有权限或设置为空列表
                    original_meta = db_route.meta
                    if isinstance(original_meta, dict) and "permissions" in original_meta:
                        meta_dict["permissions"] = original_meta["permissions"]
                    else:
                        meta_dict["permissions"] = []
                update_data["meta"] = meta_dict
            else:
                # 确保meta字段存在
                if not db_route.meta:
                    update_data["meta"] = {"permissions": []}
                elif isinstance(db_route.meta, dict):
                    if "permissions" not in db_route.meta:
                        meta_dict = dict(db_route.meta)
                        meta_dict["permissions"] = []
                        update_data["meta"] = meta_dict
            
            # 处理路径配置
            if route.path_config:
                # 确保meta字段存在
                if "meta" not in update_data:
                    if db_route.meta and isinstance(db_route.meta, dict):
                        meta_dict = dict(db_route.meta)
                    else:
                        meta_dict = {}
                else:
                    meta_dict = update_data["meta"]
                
                # 将路径配置保存到meta中
                meta_dict["pathConfig"] = route.path_config.dict()
                update_data["meta"] = meta_dict
                
                # 如果有动态参数，更新路径
                if route.path_config.hasDynamicSegments and route.path_config.params:
                    # 构建带参数的路径
                    path = route.path_config.basePath
                    for param in route.path_config.params:
                        param_suffix = "" if param.required else "?"
                        path += f"/:{param.name}{param_suffix}"
                    update_data["path"] = path
            
            # 应用更新
            for key, value in update_data.items():
                setattr(db_route, key, value)
            
            # 保存到数据库
            db.commit()
            db.refresh(db_route)
            
            logger.info(f"路由更新成功: {db_route.name} (ID: {route_id})")
            return db_route
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"更新路由失败: {str(e)}")
            raise
    
    @staticmethod
    def patch_route(db: Session, route_id: int, route_data: Dict[str, Any]) -> Optional[Route]:
        """
        部分更新路由
        
        参数:
        - db: 数据库会话
        - route_id: 路由ID
        - route_data: 要更新的路由字段数据
        
        返回:
        - Optional[Route]: 更新后的路由对象，如果不存在返回None
        """
        try:
            # 查找路由
            db_route = RouteService.get_route_by_id(db, route_id)
            if not db_route:
                logger.warning(f"更新路由失败: ID {route_id} 不存在")
                return None
            
            # 更新提供的字段
            for key, value in route_data.items():
                if key == 'meta' and hasattr(db_route, 'meta'):
                    # 合并meta数据而不是完全替换
                    current_meta = db_route.meta or {}
                    if isinstance(current_meta, str):
                        try:
                            current_meta = json.loads(current_meta)
                        except:
                            current_meta = {}
                    
                    # 确保current_meta是字典
                    if not isinstance(current_meta, dict):
                        current_meta = {}
                    
                    # 合并新值
                    current_meta.update(value)
                    setattr(db_route, key, current_meta)
                else:
                    setattr(db_route, key, value)
            
            # 保存到数据库
            db.commit()
            db.refresh(db_route)
            
            logger.info(f"路由部分更新成功: {db_route.name} (ID: {route_id})")
            return db_route
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"部分更新路由失败: {str(e)}")
            raise
    
    @staticmethod
    def delete_route(db: Session, route_id: int) -> bool:
        """
        删除路由
        
        参数:
        - db: 数据库会话
        - route_id: 路由ID
        
        返回:
        - bool: 是否删除成功
        """
        try:
            # 查找路由
            db_route = RouteService.get_route_by_id(db, route_id)
            if not db_route:
                logger.warning(f"删除路由失败: ID {route_id} 不存在")
                return False
            
            # 检查是否有子路由
            children = db.query(Route).filter(Route.parent_id == route_id).all()
            if children:
                logger.warning(f"删除路由失败: ID {route_id} 存在子路由")
                return False
            
            # 删除路由
            db.delete(db_route)
            db.commit()
            
            logger.info(f"路由删除成功: ID {route_id}")
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"删除路由失败: {str(e)}")
            raise
            
    @staticmethod
    def get_route_permissions(db: Session, route_id: int) -> List[Dict]:
        """
        获取路由的角色权限
        
        参数:
        - db: 数据库会话
        - route_id: 路由ID
        
        返回:
        - List[Dict]: 有权访问该路由的角色列表
        """
        try:
            # 获取路由
            route = RouteService.get_route_by_id(db, route_id)
            if not route:
                logger.warning(f"获取路由权限失败: ID {route_id} 不存在")
                return []
            
            # 从数据库中查询路由-角色权限关系
            permissions = db.query(RoutePermission).filter(
                RoutePermission.route_id == route_id
            ).all()
            
            # 如果没有找到权限记录，尝试从路由的meta数据中获取
            if not permissions and hasattr(route, 'meta') and route.meta:
                meta = route.meta
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception as e:
                        logger.error(f"解析路由meta数据失败: {str(e)}")
                        meta = {}
                
                if isinstance(meta, dict) and meta.get('allowed_roles'):
                    allowed_roles = meta.get('allowed_roles')
                    logger.info(f"从meta数据中获取到角色权限: {allowed_roles}")
                    
                    try:
                        # 将字符串ID转换为整数
                        role_ids = [int(r) for r in allowed_roles if str(r).isdigit()]
                        
                        # 获取这些角色
                        roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
                        
                        # 为每个角色创建权限记录
                        for role in roles:
                            perm = RoutePermission(role_id=role.id, route_id=route_id)
                            db.add(perm)
                        
                        db.commit()
                        
                        # 重新查询权限
                        permissions = db.query(RoutePermission).filter(
                            RoutePermission.route_id == route_id
                        ).all()
                        
                        logger.info(f"从meta数据创建了 {len(permissions)} 个权限记录")
                    except Exception as e:
                        logger.error(f"从meta数据创建权限记录失败: {str(e)}")
            
            # 构建返回结果
            result = []
            for perm in permissions:
                role = db.query(Role).filter(Role.id == perm.role_id).first()
                if role:
                    result.append({
                        'role_id': role.id,
                        'route_id': route_id,
                        'role_name': role.name
                    })
            
            logger.info(f"路由 {route_id} 有 {len(result)} 个角色权限")
            return result
        except SQLAlchemyError as e:
            logger.error(f"获取路由权限失败: {str(e)}")
            raise
            
    @staticmethod
    def set_route_permissions(db: Session, route_id: int, role_ids: List[int]) -> bool:
        """
        设置路由的角色权限
        
        参数:
        - db: 数据库会话
        - route_id: 路由ID
        - role_ids: 允许访问的角色ID列表
        
        返回:
        - bool: 操作是否成功
        """
        try:
            # 获取路由
            route = RouteService.get_route_by_id(db, route_id)
            if not route:
                logger.warning(f"设置路由权限失败: ID {route_id} 不存在")
                return False
            
            # 验证角色是否存在
            valid_roles = set(r.id for r in db.query(Role).filter(Role.id.in_(role_ids)).all())
            invalid_roles = set(role_ids) - valid_roles
            if invalid_roles:
                logger.warning(f"设置路由权限失败: 角色ID {invalid_roles} 不存在")
                return False
            
            # 删除现有权限
            db.query(RoutePermission).filter(RoutePermission.route_id == route_id).delete()
            
            # 添加新权限
            for role_id in role_ids:
                perm = RoutePermission(role_id=role_id, route_id=route_id)
                db.add(perm)
            
            # 同时更新路由的meta数据，保持兼容性
            meta = route.meta
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception as e:
                    logger.error(f"解析路由meta数据失败: {str(e)}")
                    meta = {}
                    
            if not isinstance(meta, dict):
                meta = {}
                
            # 更新允许访问的角色列表
            meta['allowed_roles'] = [str(rid) for rid in role_ids]
            
            # 设置标记表示这是基于角色的权限
            meta['isRoleBased'] = True
            
            # 清除其他权限设置
            meta['permission'] = None
            meta['public'] = False
            
            # 确保meta是字典类型，不是字符串
            route.meta = meta
            
            # 提交更改到数据库
            db.commit()
            
            # 刷新路由对象，确保更改已保存
            db.refresh(route)
            
            logger.info(f"路由权限设置成功: 路由ID {route_id}, 角色IDs {role_ids}, meta: {route.meta}")
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"设置路由权限失败: {str(e)}")
            raise 