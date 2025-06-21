from sqlalchemy.orm import Session
from sqlalchemy import text
from models.permission import Role, Permission, Module, PermissionLevel
from schemas.permission import PermissionCreate, RoleCreate
from services.permission_service import PermissionService, RoleService
import logging

logger = logging.getLogger(__name__)

def init_roles_and_permissions(db: Session):
    """初始化角色和权限"""
    logger.info("开始初始化角色和权限...")
    
    # 1. 创建超级管理员角色
    super_admin_role = RoleService.get_role_by_name(db, "超级管理员")
    if not super_admin_role:
        logger.info("创建超级管理员角色")
        super_admin_role = RoleService.create_role(db, RoleCreate(
            name="超级管理员", 
            description="系统超级管理员，拥有所有权限",
            permission_ids=[]
        ))
        
        # 添加最高级别的权限
        perm = PermissionCreate(
            module="ALL",
            level="SUPER_ADMIN",
            department_id=None
        )
        permission = PermissionService().create_permission(db, perm)
        # 将权限与角色关联
        db.execute(
            text("INSERT INTO role_permission (role_id, permission_id) VALUES (:role_id, :permission_id)"),
            {"role_id": super_admin_role.id, "permission_id": permission.id}
        )
    
    # 2. 创建部门负责人角色
    dept_manager_role = RoleService.get_role_by_name(db, "部门负责人")
    if not dept_manager_role:
        logger.info("创建部门负责人角色")
        dept_manager_role = RoleService.create_role(db, RoleCreate(
            name="部门负责人", 
            description="部门管理员，管理特定部门的所有数据",
            permission_ids=[]
        ))
        
        # 为部门负责人创建管理权限
        for module_name in ["USER", "DEPARTMENT", "EHS", "QA", "EVENT", "MAINT"]:
            perm = PermissionCreate(
                module=module_name,
                level="ADMIN",
                department_id=None  # 会根据用户的部门ID动态检查
            )
            permission = PermissionService().create_permission(db, perm)
            # 将权限与角色关联
            db.execute(
                text("INSERT INTO role_permission (role_id, permission_id) VALUES (:role_id, :permission_id)"),
                {"role_id": dept_manager_role.id, "permission_id": permission.id}
            )
    
    # 3. 创建班组负责人角色
    team_leader_role = RoleService.get_role_by_name(db, "班组负责人")
    if not team_leader_role:
        logger.info("创建班组负责人角色")
        team_leader_role = RoleService.create_role(db, RoleCreate(
            name="班组负责人", 
            description="部门内班组负责人，可编辑部门内特定模块数据",
            permission_ids=[]
        ))
        
        # 为班组负责人创建写入权限
        for module_name in ["EHS", "QA", "EVENT", "MAINT"]:
            perm = PermissionCreate(
                module=module_name,
                level="WRITE",
                department_id=None  # 会根据用户的部门ID动态检查
            )
            permission = PermissionService().create_permission(db, perm)
            # 将权限与角色关联
            db.execute(
                text("INSERT INTO role_permission (role_id, permission_id) VALUES (:role_id, :permission_id)"),
                {"role_id": team_leader_role.id, "permission_id": permission.id}
            )
    
    # 4. 创建普通用户角色
    normal_user_role = RoleService.get_role_by_name(db, "普通用户")
    if not normal_user_role:
        logger.info("创建普通用户角色")
        normal_user_role = RoleService.create_role(db, RoleCreate(
            name="普通用户", 
            description="基本用户，只有查看权限",
            permission_ids=[]
        ))
        
        # 为普通用户创建只读权限
        for module_name in ["EHS", "QA", "EVENT", "MAINT"]:
            perm = PermissionCreate(
                module=module_name,
                level="READ",
                department_id=None
            )
            permission = PermissionService().create_permission(db, perm)
            # 将权限与角色关联
            db.execute(
                text("INSERT INTO role_permission (role_id, permission_id) VALUES (:role_id, :permission_id)"),
                {"role_id": normal_user_role.id, "permission_id": permission.id}
            )
    
    db.commit()
    logger.info("角色和权限初始化完成")


def migrate_superuser_to_roles(db: Session):
    """将超级用户标志迁移到角色系统 - 兼容性函数，保留但不再实际查询超级用户标志"""
    logger.info("超级用户标志已删除，跳过迁移...")
    
    # 确保超级管理员角色存在
    super_admin_role = RoleService.get_role_by_name(db, "超级管理员")
    if not super_admin_role:
        logger.warning("未找到超级管理员角色，初始化角色系统")
        init_roles_and_permissions(db)
        super_admin_role = RoleService.get_role_by_name(db, "超级管理员")
    
    # 不再查询is_superuser，因为该字段已删除
    logger.info("超级用户标志已移除，迁移过程已在Alembic脚本中处理") 