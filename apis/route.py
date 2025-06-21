from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
import logging

from db.session import get_db
from schemas.route import RouteCreate, RouteUpdate, RouteResponse
from models.route import Route
from models.user import User
from core.security import get_current_user
from services.activity_service import record_activity
from services.route_service import RouteService
from services.permission_service import RoleService
from services.permission_service import PermissionService

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["路由管理"],
    responses={404: {"description": "Not found"}}
)

@router.get("/routes", response_model=List[RouteResponse], summary="获取所有路由")
async def get_routes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有路由配置
    
    需要管理员权限
    """
    if not current_user.has_permission("ROUTE", "READ"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此功能"
        )
    
    routes = RouteService.get_all_routes(db)
    return routes

@router.get("/routes/{route_id}", response_model=RouteResponse, summary="获取单个路由")
async def get_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个路由配置
    
    需要管理员权限
    """
    if not current_user.has_permission("ROUTE", "READ"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此功能"
        )
    
    route = RouteService.get_route_by_id(db, route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="路由不存在"
        )
    
    return route

@router.post("/routes", response_model=RouteResponse, summary="创建路由")
async def create_route(
    route: RouteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的路由配置
    
    需要管理员权限
    
    可以通过path_config字段设置动态路径参数
    """
    if not current_user.has_permission("ROUTE", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此功能"
        )
    
    # 检查路径是否已存在
    if route.path:
        existing_route = RouteService.get_route_by_path(db, route.path)
        if existing_route:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="路径已存在"
            )
    
    # 创建路由
    new_route = RouteService.create_route(db, route)
    return new_route

@router.put("/routes/{route_id}", response_model=RouteResponse, summary="更新路由")
async def update_route(
    route_id: int,
    route: RouteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新路由配置
    
    需要管理员权限
    
    可以通过path_config字段设置动态路径参数
    """
    if not current_user.has_permission("ROUTE", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此功能"
        )
    
    # 检查路由是否存在
    existing_route = RouteService.get_route_by_id(db, route_id)
    if not existing_route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="路由不存在"
        )
    
    # 如果更新了路径，检查是否与其他路由冲突
    if route.path and route.path != existing_route.path:
        path_conflict = RouteService.get_route_by_path(db, route.path)
        if path_conflict and path_conflict.id != route_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="路径已被其他路由占用"
            )
    
    # 更新路由
    updated_route = RouteService.update_route(db, route_id, route)
    if not updated_route:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新路由失败"
        )
    
    return updated_route

@router.delete("/routes/{route_id}", summary="删除路由")
async def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除路由配置
    
    需要管理员权限
    """
    if not current_user.has_permission("ROUTE", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此功能"
        )
    
    # 检查路由是否存在
    existing_route = RouteService.get_route_by_id(db, route_id)
    if not existing_route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="路由不存在"
        )
    
    # 删除路由
    success = RouteService.delete_route(db, route_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除路由失败"
        )
    
    return {"detail": "路由已删除"}

# 获取用户菜单导航
@router.get("/navigation", summary="获取用户导航菜单")
async def get_navigation_menu(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户的导航菜单结构
    
    会根据用户权限过滤可访问的菜单
    """
    from services.permission_service import PermissionService
    
    logger.info(f"用户 {current_user.name} 请求获取导航菜单")
    
    try:
        permission_service = PermissionService()
        user_routes = permission_service.get_user_routes(db, current_user)
        return user_routes
    except Exception as e:
        logger.error(f"获取导航菜单失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取导航菜单失败: {str(e)}"
        )

# 新增: 获取路由的角色权限
@router.get("/routes/{route_id}/permissions", summary="获取路由的角色权限")
async def get_route_permissions(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定路由的角色权限设置
    
    需要路由管理员权限
    """
    if not current_user.has_permission("ROUTE", "READ"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此功能"
        )
    
    # 检查路由是否存在
    route = RouteService.get_route_by_id(db, route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="路由不存在"
        )
    
    # 获取路由的角色权限
    permissions = RouteService.get_route_permissions(db, route_id)
    return permissions

# 新增: 设置路由的角色权限
@router.post("/routes/{route_id}/permissions", summary="设置路由的角色权限")
async def set_route_permissions(
    route_id: int,
    role_ids: Dict[str, List[int]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    设置指定路由的角色权限
    
    需要路由管理员权限
    
    请求体格式:
    {
        "role_ids": [1, 2, 3]  # 角色ID列表
    }
    """
    if not current_user.has_permission("ROUTE", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此功能"
        )
    
    # 检查路由是否存在
    route = RouteService.get_route_by_id(db, route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="路由不存在"
        )
    
    # 设置路由的角色权限
    success = RouteService.set_route_permissions(db, route_id, role_ids.get("role_ids", []))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设置路由权限失败"
        )
    
    # 记录活动
    record_activity(
        db=db,
        user_id=current_user.id,
        action="设置路由权限",
        target_type="route",
        target_id=route_id,
        details=f"设置路由 {route.name} 的角色权限，角色IDs: {role_ids.get('role_ids', [])}"
    )
    
    return {"detail": "路由权限设置成功"}

# 新增: PATCH更新路由的部分属性
@router.patch("/routes/{route_id}", response_model=RouteResponse, summary="更新路由部分属性")
async def patch_route(
    route_id: int,
    route_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    部分更新路由配置，只更新提供的字段
    
    需要管理员权限
    """
    if not current_user.has_permission("ROUTE", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此功能"
        )
    
    # 检查路由是否存在
    existing_route = RouteService.get_route_by_id(db, route_id)
    if not existing_route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="路由不存在"
        )
    
    # 更新路由
    updated_route = RouteService.patch_route(db, route_id, route_data)
    if not updated_route:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新路由失败"
        )
    
    return updated_route 