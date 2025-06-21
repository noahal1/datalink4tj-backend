from sqlalchemy.orm import Session
from typing import List, Optional
from models.permission import Permission, Role, PermissionLevel, Module, role_permission
from models.user import User
from models.route import Route
from models.route_permission import RoutePermission
from schemas.permission import PermissionCreate, PermissionUpdate, RoleCreate, RoleUpdate
import logging
import json

logger = logging.getLogger(__name__)

# 权限相关服务
class PermissionService:
    def __init__(self):
        pass

    def create_permission(self, db: Session, permission: PermissionCreate) -> Permission:
        """
        创建新权限
        
        参数:
        - db: 数据库会话
        - permission: 权限创建模型
        
        返回:
        - 创建的权限对象
        """
        # 验证模块和权限等级
        if not Module.is_valid_module(permission.module):
            raise ValueError(f"无效的模块: {permission.module}")
            
        if permission.level not in [level.value for level in PermissionLevel]:
            raise ValueError(f"无效的权限等级: {permission.level}")
            
        db_permission = Permission(
            module=permission.module,
            level=permission.level,
            department_id=permission.department_id
        )
        db.add(db_permission)
        db.commit()
        db.refresh(db_permission)
        return db_permission
    
    def get_permission(self, db: Session, permission_id: int) -> Optional[Permission]:
        """通过ID获取权限"""
        return db.query(Permission).filter(Permission.id == permission_id).first()
    
    def get_permissions(self, db: Session, skip: int = 0, limit: int = 100) -> List[Permission]:
        """获取权限列表"""
        return db.query(Permission).offset(skip).limit(limit).all()
    
    def update_permission(self, db: Session, permission_id: int, permission: PermissionUpdate) -> Optional[Permission]:
        """
        更新权限
        
        参数:
        - db: 数据库会话
        - permission_id: 权限ID
        - permission: 权限更新模型
        
        返回:
        - 更新后的权限对象，如果不存在则返回None
        """
        db_permission = self.get_permission(db, permission_id)
        if not db_permission:
            return None
        
        # 验证模块和权限等级
        if permission.module is not None:
            if not Module.is_valid_module(permission.module):
                raise ValueError(f"无效的模块: {permission.module}")
                
        if permission.level is not None:
            if permission.level not in [level.value for level in PermissionLevel]:
                raise ValueError(f"无效的权限等级: {permission.level}")
            
        for key, value in permission.dict(exclude_unset=True).items():
            setattr(db_permission, key, value)
            
        db.commit()
        db.refresh(db_permission)
        return db_permission
    
    def delete_permission(self, db: Session, permission_id: int) -> bool:
        """删除权限"""
        permission = self.get_permission(db, permission_id)
        if not permission:
            return False
            
        db.delete(permission)
        db.commit()
        return True
        
    def ensure_route_permissions(self, db: Session):
        """确保ROUTE模块的权限存在"""
        logger.info("检查ROUTE模块权限...")
        
        # 创建权限服务实例
        permission_service = PermissionService()
        
        # 查找管理员角色
        admin_role = db.query(Role).filter(Role.name == "管理员").first()
        if not admin_role:
            logger.warning("未找到管理员角色，创建中...")
            admin_role = RoleService.create_simple_role(db, "管理员", "系统管理员角色")
        
        # 需要确保存在的权限
        required_permissions = [
            {"module": "ROUTE", "level": "READ"},
            {"module": "ROUTE", "level": "ADMIN"}
        ]
        
        # 检查并创建缺失的权限
        for perm_data in required_permissions:
            # 检查权限是否存在
            # 使用关联表查询，而不是直接使用Permission.role_id
            permission = db.query(Permission).join(
                role_permission, 
                Permission.id == role_permission.c.permission_id
            ).filter(
                role_permission.c.role_id == admin_role.id,
                Permission.module == perm_data["module"],
                Permission.level == perm_data["level"]
            ).first()
            
            # 如果不存在，创建权限
            if not permission:
                logger.info(f"创建{perm_data['module']}模块的{perm_data['level']}权限...")
                permission_service.create_permission(db, PermissionCreate(
                    module=perm_data["module"], 
                    level=perm_data["level"], 
                    department_id=None
                ))
        
        logger.info("ROUTE模块权限检查完成")

    def get_user_routes(self, db: Session, user: User):
        """
        获取用户可访问的路由列表
        
        参数:
        - db: 数据库会话
        - user: 用户对象
        
        返回:
        - 路由列表，按树形结构组织
        """
        from services.route_service import RouteService
        
        try:
            logger.info(f"正在获取用户 {user.name} 的路由权限")
            
            # 获取所有路由
            all_routes = RouteService.get_all_routes(db)
            logger.info(f"系统中共有 {len(all_routes)} 个路由")
            
            # 检查用户是否是超级管理员
            is_superadmin = False
            # 获取用户角色
            user_roles = []
            user_role_ids = []
            
            if user.roles:
                user_roles = user.roles
                user_role_ids = [role.id for role in user_roles]
                logger.info(f"用户 {user.name} 拥有角色: {[role.name for role in user_roles]}, 角色ID: {user_role_ids}")
                for role in user_roles:
                    if role.name == "超级管理员":
                        is_superadmin = True
                        break
            
            # 如果用户是超级管理员，返回所有路由
            if is_superadmin:
                logger.info(f"用户 {user.name} 是超级管理员，返回所有路由")
                return self._build_route_tree(all_routes)
            
            # 获取用户角色可访问的路由ID
            route_permissions = db.query(RoutePermission).filter(
                RoutePermission.role_id.in_(user_role_ids)
            ).all()
            
            accessible_route_ids = [perm.route_id for perm in route_permissions]
            logger.info(f"从route_permissions表获取到 {len(accessible_route_ids)} 个可访问路由ID: {accessible_route_ids}")
            
            # 存储用户可访问的路由
            accessible_routes = []
            
            # 根据用户权限过滤路由
            for route in all_routes:
                # 默认不可访问
                has_access = False
                
                # 检查路由ID是否在可访问列表中
                if route.id in accessible_route_ids:
                    logger.info(f"路由 {route.id}({route.name}) 在可访问列表中")
                    has_access = True
                    accessible_routes.append(route)
                    continue
                
                # 如果没有通过角色权限检查，则检查路由的meta信息
                # 获取meta信息
                meta = route.meta
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception as e:
                        logger.error(f"解析路由 {route.id} 的meta数据失败: {str(e)}")
                        meta = {}
                
                # 如果路由是公开的或对所有登录用户开放
                if not isinstance(meta, dict):
                    meta = {}
                
                # 检查是否是公开路由
                if meta.get("public") is True:
                    logger.info(f"路由 {route.id}({route.name}) 是公开路由，所有人可访问")
                    has_access = True
                # 检查是否对所有登录用户开放
                elif meta.get("permission") == "*":
                    logger.info(f"路由 {route.id}({route.name}) 对所有登录用户开放")
                    has_access = True
                # 检查allowed_roles字段
                elif "allowed_roles" in meta and isinstance(meta["allowed_roles"], list):
                    user_role_ids_str = [str(role_id) for role_id in user_role_ids]
                    for role_id in meta["allowed_roles"]:
                        if str(role_id) in user_role_ids_str:
                            logger.info(f"路由 {route.id}({route.name}) 允许角色ID {role_id}，用户拥有此角色")
                            has_access = True
                            break
                
                if has_access:
                    accessible_routes.append(route)
            
            logger.info(f"用户 {user.name} 可访问 {len(accessible_routes)} 个路由")
            
            # 构建路由树并返回
            route_tree = self._build_route_tree(accessible_routes)
            logger.info(f"最终返回的路由树包含 {len(route_tree)} 个顶级路由")
            return route_tree
            
        except Exception as e:
            logger.error(f"获取用户路由失败: {str(e)}", exc_info=True)
            return []
    
    def _build_route_tree(self, routes):
        """
        构建路由树
        
        参数:
        - routes: 路由列表
        
        返回:
        - 树形结构的路由列表
        """
        if not routes:
            return []
            
        # 创建一个映射来存储路由和它们的子路由
        routeMap = {}
        rootRoutes = []

        # 第一遍循环初始化所有路由对象
        for route in routes:
            # 复制路由对象并添加children数组
            routeObj = {
                "id": route.id,
                "path": route.path,
                "name": route.name,
                "component": route.component,
                "meta": route.meta,
                "parent_id": route.parent_id,
                "sort_order": route.sort_order or 0,  # 确保sort_order有默认值
                "children": []
            }
            routeMap[route.id] = routeObj
            
            # 如果没有父路由，则为根路由
            if not route.parent_id:
                rootRoutes.append(routeObj)

        # 第二遍循环建立父子关系
        for route in routes:
            # 如果有父路由，将此路由添加到父路由的children中
            if route.parent_id and route.parent_id in routeMap:
                routeMap[route.parent_id]["children"].append(routeMap[route.id])

        # 对每个层级的路由按sort_order排序
        def sort_routes(routeList):
            # 排序当前层级
            try:
                routeList.sort(key=lambda x: x.get("sort_order", 0))
            except Exception as e:
                logger.warning(f"路由排序失败: {str(e)}")
            
            # 递归排序子路由
            for route in routeList:
                if route["children"] and len(route["children"]) > 0:
                    sort_routes(route["children"])
            
            return routeList

        # 返回排序后的路由树
        return sort_routes(rootRoutes)

# 角色相关服务
class RoleService:
    @staticmethod
    def create_role(db: Session, role: RoleCreate) -> Role:
        """创建新角色"""
        db_role = Role(
            name=role.name,
            description=role.description
        )
        
        # 添加权限
        if role.permission_ids:
            for permission_id in role.permission_ids:
                permission = PermissionService().get_permission(db, permission_id)
                if permission:
                    db_role.permissions.append(permission)
        
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        return db_role
    
    @staticmethod
    def create_simple_role(db: Session, name: str, description: str = None) -> Role:
        """创建角色（简化版本，用于内部调用）"""
        role = Role(name=name, description=description)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    @staticmethod
    def get_role(db: Session, role_id: int) -> Optional[Role]:
        """通过ID获取角色"""
        return db.query(Role).filter(Role.id == role_id).first()
    
    @staticmethod
    def get_role_by_name(db: Session, name: str) -> Optional[Role]:
        """通过名称获取角色"""
        return db.query(Role).filter(Role.name == name).first()
    
    @staticmethod
    def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
        """获取角色列表"""
        return db.query(Role).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_role(db: Session, role_id: int, role: RoleUpdate) -> Optional[Role]:
        """更新角色"""
        db_role = RoleService.get_role(db, role_id)
        if not db_role:
            return None
        
        # 更新基本信息
        update_data = role.dict(exclude={"permission_ids"}, exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_role, key, value)
        
        # 更新权限
        if role.permission_ids is not None:
            db_role.permissions = []
            for permission_id in role.permission_ids:
                permission = PermissionService().get_permission(db, permission_id)
                if permission:
                    db_role.permissions.append(permission)
        
        db.commit()
        db.refresh(db_role)
        return db_role
    
    @staticmethod
    def delete_role(db: Session, role_id: int) -> bool:
        """删除角色"""
        role = RoleService.get_role(db, role_id)
        if not role:
            return False
            
        db.delete(role)
        db.commit()
        return True
    
    @staticmethod
    def assign_user_roles(db: Session, user_id: int, role_ids: List[int]) -> Optional[User]:
        """
        为用户分配角色
        
        参数:
        - db: 数据库会话
        - user_id: 用户ID
        - role_ids: 角色ID列表
        
        返回:
        - User: 更新后的用户对象，如果失败则返回None
        """
        try:
            # 获取用户
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"分配角色失败: 用户 {user_id} 不存在")
                return None
                
            # 清除现有角色并添加新角色
            user.roles = []
            for role_id in role_ids:
                role = RoleService.get_role(db, role_id)
                if role:
                    user.roles.append(role)
                else:
                    logger.warning(f"角色ID {role_id} 不存在，已跳过")
            
            db.commit()
            db.refresh(user)
            logger.info(f"成功为用户 {user_id} 分配 {len(role_ids)} 个角色")
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"分配用户角色时出错: {str(e)}")
            return None
    
    @staticmethod
    def check_permission(db: Session, user_id: int, module: str, level: str, target_department_id: Optional[int] = None) -> bool:
        """检查用户是否有权限"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
            
        return user.has_permission(module, level, target_department_id)

    @staticmethod
    def get_role_by_id(db: Session, role_id: int) -> Optional[Role]:
        """获取角色"""
        return db.query(Role).filter(Role.id == role_id).first()
    
    @staticmethod
    def get_all_roles(db: Session) -> List[Role]:
        """获取所有角色"""
        try:
            roles = db.query(Role).all()
            logger.info(f"获取所有角色成功: {len(roles)}个角色")
            return roles
        except Exception as e:
            logger.error(f"获取所有角色失败: {str(e)}")
            return []
    
    @staticmethod
    def get_permissions_by_role_id(db: Session, role_id: int) -> List[Permission]:
        """获取角色的所有权限"""
        role = RoleService.get_role_by_id(db, role_id)
        if not role:
            return []
        return role.permissions
    
    @staticmethod
    def create_permission(
        db: Session, 
        role_id: int, 
        module: str, 
        level: str,
        department_id: Optional[int] = None
    ) -> Optional[Permission]:
        """
        创建权限
        
        参数:
        - db: 数据库会话
        - role_id: 角色ID
        - module: 模块名称
        - level: 权限等级
        - department_id: 部门ID限制
        
        返回:
        - Permission: 创建的权限对象
        """
        role = RoleService.get_role_by_id(db, role_id)
        if not role:
            return None
            
        permission = Permission(
            role_id=role_id,
            module=module,
            level=level,
            department_id=department_id
        )
        
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission
    
    @staticmethod
    def delete_permission(db: Session, permission_id: int) -> bool:
        """删除权限"""
        permission_service = PermissionService()
        permission = permission_service.get_permission(db, permission_id)
        if not permission:
            return False
            
        db.delete(permission)
        db.commit()
        return True
        
    @staticmethod
    def ensure_route_permissions(db: Session):
        """确保ROUTE模块的权限存在"""
        logger.info("检查ROUTE模块权限...")
        
        # 创建权限服务实例
        permission_service = PermissionService()
        
        # 查找管理员角色
        admin_role = db.query(Role).filter(Role.name == "管理员").first()
        if not admin_role:
            logger.warning("未找到管理员角色，创建中...")
            admin_role = RoleService.create_simple_role(db, "管理员", "系统管理员角色")
        
        # 需要确保存在的权限
        required_permissions = [
            {"module": "ROUTE", "level": "READ"},
            {"module": "ROUTE", "level": "ADMIN"}
        ]
        
        # 检查并创建缺失的权限
        for perm_data in required_permissions:
            # 检查权限是否存在
            # 使用关联表查询，而不是直接使用Permission.role_id
            permission = db.query(Permission).join(
                role_permission, 
                Permission.id == role_permission.c.permission_id
            ).filter(
                role_permission.c.role_id == admin_role.id,
                Permission.module == perm_data["module"],
                Permission.level == perm_data["level"]
            ).first()
            
            # 如果不存在，创建权限
            if not permission:
                logger.info(f"创建{perm_data['module']}模块的{perm_data['level']}权限...")
                permission_service.create_permission(db, PermissionCreate(
                    module=perm_data["module"], 
                    level=perm_data["level"], 
                    department_id=None
                ))
        
        logger.info("ROUTE模块权限检查完成")

# 初始化权限和角色
def init_permissions_and_roles(db: Session):
    """初始化基本权限和角色"""
    try:
        # 检查是否已初始化
        if db.query(Role).count() > 0:
            logger.info("权限和角色已存在，跳过初始化")
            return
            
        logger.info("开始初始化权限和角色...")
            
        # 创建基本权限
        permissions = []
        
        # 超级管理员权限
        super_admin_perm = Permission(module="ALL", level="SUPER_ADMIN")
        permissions.append(super_admin_perm)
        
        # 定义模块和权限等级
        modules = ["USER", "DEPARTMENT", "EHS", "QA", "EVENT", "MAINT"]
        levels = ["READ", "WRITE", "ADMIN"]
        
        # 为每个模块创建所有等级的权限
        module_permissions = {}
        for module in modules:
            module_permissions[module] = {}
            for level in levels:
                perm = Permission(module=module, level=level)
                permissions.append(perm)
                module_permissions[module][level] = perm
        
        # 批量添加权限
        db.add_all(permissions)
        db.commit()
        
        # 刷新权限对象
        for p in permissions:
            db.refresh(p)
            
        # 创建基本角色
        roles = []
        
        # 超级管理员角色 - 拥有所有权限
        super_admin = Role(name="超级管理员", description="拥有所有权限")
        super_admin.permissions = [super_admin_perm]
        roles.append(super_admin)
        
        # 系统管理员角色 - 管理系统设置和用户
        admin = Role(name="系统管理员", description="管理系统设置和用户")
        admin.permissions = [
            module_permissions["USER"]["READ"],
            module_permissions["USER"]["WRITE"],
            module_permissions["USER"]["ADMIN"],
            module_permissions["DEPARTMENT"]["READ"],
            module_permissions["DEPARTMENT"]["WRITE"],
            module_permissions["DEPARTMENT"]["ADMIN"]
        ]
        roles.append(admin)
        
        # 部门管理员角色 - 管理部门内的功能
        dept_admin = Role(name="部门管理员", description="管理部门内的功能")
        dept_admin_perms = []
        # 添加所有模块的READ和WRITE权限
        for module in modules:
            dept_admin_perms.append(module_permissions[module]["READ"])
            dept_admin_perms.append(module_permissions[module]["WRITE"])
        # 添加非用户和部门模块的ADMIN权限
        for module in [m for m in modules if m not in ["USER", "DEPARTMENT"]]:
            dept_admin_perms.append(module_permissions[module]["ADMIN"])
        dept_admin.permissions = dept_admin_perms
        roles.append(dept_admin)
        
        # 普通用户角色 - 基本功能访问权限
        user_role = Role(name="普通用户", description="基本功能访问权限")
        user_role.permissions = [module_permissions[module]["READ"] for module in modules]
        roles.append(user_role)
        
        # 批量添加角色
        db.add_all(roles)
        db.commit()
        
        logger.info("基本权限和角色初始化完成")
        
    except Exception as e:
        db.rollback()
        logger.error(f"初始化权限和角色失败: {str(e)}", exc_info=True)
        raise 