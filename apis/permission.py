from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from db.session import get_db
from models.user import User
from models.permission import PermissionLevel, Module
from schemas.permission import (
    Permission, PermissionCreate, PermissionUpdate,
    Role, RoleCreate, RoleUpdate,
    PermissionCheck, PermissionResult, UserRoleAssignment,
    RoleSimple
)
from services.permission_service import PermissionService, RoleService
from core.security import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["权限管理"],
    responses={404: {"description": "Not found"}}
)

# 权限管理API
@router.post("/permissions", response_model=Permission, summary="创建权限")
async def create_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的权限
    
    需要超级管理员权限
    """
    # 权限检查
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    # 验证模块和权限等级
    try:
        # 验证模块
        if permission.module != "ALL" and permission.module not in [m.value for m in Module]:
            raise ValueError(f"无效的模块: {permission.module}")
        
        # 验证权限等级
        if permission.level not in [level.value for level in PermissionLevel]:
            raise ValueError(f"无效的权限等级: {permission.level}")
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # 创建PermissionService实例
    permission_service = PermissionService()
    return permission_service.create_permission(db, permission)

@router.get("/permissions", response_model=List[Permission], summary="获取权限列表")
async def read_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取权限列表
    
    所有已登录用户均可访问此接口
    """
    # 不再需要权限检查，所有已登录用户都可以访问
    # 创建PermissionService实例
    permission_service = PermissionService()
    return permission_service.get_permissions(db, skip, limit)

@router.get("/permissions/{permission_id}", response_model=Permission, summary="获取单个权限")
async def read_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个权限详情
    
    需要系统管理员权限
    """
    # 权限检查
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )
    
    # 创建PermissionService实例
    permission_service = PermissionService()
    permission = permission_service.get_permission(db, permission_id)
    if permission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
        
    return permission

@router.put("/permissions/{permission_id}", response_model=Permission, summary="更新权限")
async def update_permission(
    permission_id: int,
    permission: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新权限
    
    需要超级管理员权限
    """
    # 权限检查
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
        
    # 验证模块和权限等级
    try:
        # 验证模块
        if permission.module is not None:
            if permission.module != "ALL" and permission.module not in [m.value for m in Module]:
                raise ValueError(f"无效的模块: {permission.module}")
        
        # 验证权限等级
        if permission.level is not None:
            if permission.level not in [level.value for level in PermissionLevel]:
                raise ValueError(f"无效的权限等级: {permission.level}")
                
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # 创建PermissionService实例
    permission_service = PermissionService()
    updated_permission = permission_service.update_permission(db, permission_id, permission)
    if updated_permission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
        
    return updated_permission

@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除权限")
async def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除权限
    
    需要超级管理员权限
    """
    # 权限检查
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    # 创建PermissionService实例
    permission_service = PermissionService()
    success = permission_service.delete_permission(db, permission_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
        
    return None

# 角色管理API
@router.post("/roles", response_model=Role, summary="创建角色")
async def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的角色
    
    需要系统管理员权限
    """
    # 权限检查
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )
        
    # 检查角色名称是否已存在
    existing_role = RoleService.get_role_by_name(db, role.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"角色名称 '{role.name}' 已存在"
        )
        
    return RoleService.create_role(db, role)

@router.get("/roles", response_model=List[Role], summary="获取角色列表")
async def read_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取角色列表
    
    需要系统管理员权限
    """
    # 权限检查
    if not current_user.has_permission("USER", "READ"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )
        
    return RoleService.get_roles(db, skip, limit)

@router.get("/simple-roles", response_model=List[RoleSimple], summary="获取简化角色列表")
async def read_simple_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取简化的角色列表（只包含基本信息，不包含权限详情）
    
    所有已登录用户均可访问此接口
    """
    return RoleService.get_all_roles(db)

@router.get("/roles/{role_id}", response_model=Role, summary="获取单个角色")
async def read_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个角色详情
    
    需要系统管理员权限
    """
    # 权限检查
    if not current_user.has_permission("USER", "READ"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )
        
    role = RoleService.get_role(db, role_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
        
    return role

@router.put("/roles/{role_id}", response_model=Role, summary="更新角色")
async def update_role(
    role_id: int,
    role: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新角色
    
    需要系统管理员权限
    """
    # 权限检查
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )
        
    # 检查角色名称是否已存在
    if role.name:
        existing_role = RoleService.get_role_by_name(db, role.name)
        if existing_role and existing_role.id != role_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"角色名称 '{role.name}' 已存在"
            )
            
    updated_role = RoleService.update_role(db, role_id, role)
    if updated_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
        
    return updated_role

@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除角色")
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除角色
    
    需要系统管理员权限
    """
    # 权限检查
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )
        
    success = RoleService.delete_role(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
        
    return None

# 用户角色分配API
@router.post("/users/{user_id}/roles", summary="为用户分配角色")
async def assign_user_roles(
    user_id: int,
    assignment: UserRoleAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    为用户分配角色
    
    需要系统管理员权限
    """
    # 权限检查
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )
        
    # 验证用户ID
    if user_id != assignment.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户ID不匹配"
        )
        
    user = RoleService.assign_user_roles(db, user_id, assignment.role_ids)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
        
    return {"message": "角色分配成功"}

# 权限检查API
@router.post("/check-permission", response_model=PermissionResult, summary="检查当前用户权限")
async def check_permission(
    permission_check: PermissionCheck,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检查当前用户是否拥有特定权限
    """
    has_permission = RoleService.check_permission(
        db, 
        current_user.id, 
        permission_check.module, 
        permission_check.level,
        permission_check.department_id
    )
    
    return PermissionResult(
        has_permission=has_permission,
        user_id=current_user.id,
        module=permission_check.module,
        level=permission_check.level
    )

# 获取用户可访问的路由列表
@router.get("/permissions/routes", summary="获取用户可访问的路由列表")
async def get_user_routes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户可访问的路由列表
    
    根据用户的权限过滤可访问的路由
    返回的路由列表会构建为菜单树结构
    """
    logger.info(f"用户 {current_user.name} (ID: {current_user.id}) 请求获取路由权限列表")
    
    try:
        # 创建权限服务实例
        permission_service = PermissionService()
        
        # 获取用户可访问的路由
        user_routes = permission_service.get_user_routes(db, current_user)
        
        logger.info(f"成功返回用户 {current_user.name} 的路由列表，共 {len(user_routes)} 个根路由")
        # 返回路由列表
        return user_routes
    except Exception as e:
        logger.error(f"获取用户路由列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取路由列表失败: {str(e)}"
        ) 