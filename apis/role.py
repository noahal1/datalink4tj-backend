from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from schemas import permission as permission_schema
from services.permission_service import RoleService, PermissionService
from db.session import get_db
from core.security import get_current_user
from models.user import User
import logging
from services.activity_service import ActivityService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 路由器
router = APIRouter()

@router.get("/roles", response_model=List[permission_schema.Role], summary="获取角色列表")
async def get_roles(
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(100, description="返回记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取角色列表
    
    参数:
    - skip: 跳过的记录数
    - limit: 返回的最大记录数
    - db: 数据库会话
    - current_user: 当前用户
    
    返回:
    - 角色对象列表
    """
    logger.info(f"获取角色列表: 用户={current_user.name}")
    
    # 检查权限 - 只有管理员可以获取角色列表
    if not current_user.has_permission("USER", "ADMIN"):
        logger.warning(f"权限不足: 用户 {current_user.name} 尝试获取角色列表")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )
    
    try:
        roles = RoleService.get_roles(db, skip, limit)
        return roles
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色列表失败: {str(e)}"
        )

@router.get("/roles/{role_id}", response_model=permission_schema.Role, summary="获取角色详情")
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取角色详情
    
    参数:
    - role_id: 角色ID
    - db: 数据库会话
    - current_user: 当前用户
    
    返回:
    - 角色对象
    """
    logger.info(f"获取角色详情: role_id={role_id}, 用户={current_user.name}")
    
    try:
        role = RoleService.get_role(db, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取角色详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色详情失败: {str(e)}"
        )

@router.post("/roles", response_model=permission_schema.Role, summary="创建角色")
async def create_role(
    role: permission_schema.RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建角色
    
    参数:
    - role: 角色创建模式
    - db: 数据库会话
    - current_user: 当前用户
    
    返回:
    - 创建的角色对象
    """
    logger.info(f"创建角色: {role.name}, 用户={current_user.name}")
    logger.info(f"角色详细数据: {role}")
    
    # 检查权限
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有创建角色的权限"
        )
    
    try:
        # 检查角色名称是否已存在
        if RoleService.get_role_by_name(db, role.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色名称已存在"
            )
        
        # 创建角色
        new_role = RoleService.create_role(db, role)
        
        # 记录活动
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="PERMISSION",
            action_type="CREATE",
            title="创建角色",
            action=f"创建了角色 '{new_role.name}'",
            details=f"创建角色: {new_role.name}",
            after_data={
                "id": new_role.id,
                "name": new_role.name,
                "description": new_role.description
            },
            target=f"/admin/permissions"
        )
        
        return new_role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建角色失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建角色失败: {str(e)}"
        )

@router.put("/roles/{role_id}", response_model=permission_schema.Role, summary="更新角色")
async def update_role(
    role_id: int,
    role: permission_schema.RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新角色
    
    参数:
    - role_id: 角色ID
    - role: 角色更新模式
    - db: 数据库会话
    - current_user: 当前用户
    
    返回:
    - 更新后的角色对象
    """
    logger.info(f"更新角色: role_id={role_id}, 用户={current_user.name}")
    logger.info(f"接收到的角色数据: {role}")
    logger.info(f"角色数据详情: name={role.name}, description={role.description}, permission_ids={role.permission_ids}")
    
    # 检查权限
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有更新角色的权限"
        )
    
    try:
        # 获取角色
        existing_role = RoleService.get_role(db, role_id)
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 如果修改了名称，检查名称是否已存在
        if role.name and role.name != existing_role.name:
            if RoleService.get_role_by_name(db, role.name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="角色名称已存在"
                )
        
        # 记录更新前数据
        old_data = {
            "id": existing_role.id,
            "name": existing_role.name,
            "description": existing_role.description
        }
        
        # 更新角色
        updated_role = RoleService.update_role(db, role_id, role)
        
        # 记录活动
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="PERMISSION",
            action_type="UPDATE",
            title="更新角色",
            action=f"更新了角色 '{updated_role.name}'",
            details=f"更新角色: {updated_role.name}",
            before_data=old_data,
            after_data={
                "id": updated_role.id,
                "name": updated_role.name,
                "description": updated_role.description
            },
            target=f"/admin/permissions"
        )
        
        return updated_role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新角色失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新角色失败: {str(e)}"
        )

@router.delete("/roles/{role_id}", summary="删除角色")
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除角色
    
    参数:
    - role_id: 角色ID
    - db: 数据库会话
    - current_user: 当前用户
    
    返回:
    - 删除成功消息
    """
    logger.info(f"删除角色: role_id={role_id}, 用户={current_user.name}")
    
    # 检查权限
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有删除角色的权限"
        )
    
    try:
        # 获取角色信息
        role = RoleService.get_role(db, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 检查是否为保留角色（超级管理员等）
        if role.name in ["超级管理员", "部门负责人", "班组负责人", "普通用户"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除系统保留角色"
            )
        
        # 记录删除前数据
        old_data = {
            "id": role.id,
            "name": role.name,
            "description": role.description
        }
        
        # 删除角色
        success = RoleService.delete_role(db, role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 记录活动
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="PERMISSION",
            action_type="DELETE",
            title="删除角色",
            action=f"删除了角色 '{role.name}'",
            details=f"删除角色: {role.name}, ID: {role_id}",
            before_data=old_data,
            target="/admin/permissions"
        )
        
        return {"message": "角色删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除角色失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除角色失败: {str(e)}"
        )

@router.post("/roles/{role_id}/permissions", summary="为角色分配权限")
async def assign_role_permissions(
    role_id: int,
    permission_ids: List[int] = Body(..., description="权限ID列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    为角色分配权限
    
    参数:
    - role_id: 角色ID
    - permission_ids: 权限ID列表
    - db: 数据库会话
    - current_user: 当前用户
    
    返回:
    - 分配成功消息
    """
    logger.info(f"为角色分配权限: role_id={role_id}, permission_ids={permission_ids}, 用户={current_user.name}")
    
    # 检查权限
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有分配角色权限的权限"
        )
    
    try:
        # 确保所有permission_ids都是整数
        permission_ids = [int(pid) for pid in permission_ids]
        
        # 获取角色
        role = RoleService.get_role(db, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 记录更新前权限
        old_permissions = [p.id for p in role.permissions] if role.permissions else []
        
        # 更新角色权限
        role_update = permission_schema.RoleUpdate(permission_ids=permission_ids)
        updated_role = RoleService.update_role(db, role_id, role_update)
        
        # 记录活动
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="PERMISSION",
            action_type="UPDATE",
            title="分配角色权限",
            action=f"为角色 '{role.name}' 更新了权限",
            details=f"为角色 {role.name} 分配权限",
            before_data={"permission_ids": old_permissions},
            after_data={"permission_ids": permission_ids},
            target=f"/admin/permissions"
        )
        
        return {"message": "角色权限分配成功"}
    except ValueError as e:
        logger.error(f"权限ID格式错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"权限ID必须为整数: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配角色权限失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配角色权限失败: {str(e)}"
        ) 