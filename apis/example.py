"""
示例API模块
展示权限系统的使用方法
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from db.session import get_db
from models.user import User
from core.security import get_current_user
from core.permissions import require_permission, PermissionChecker
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/examples",
    tags=["示例"],
    responses={404: {"description": "未找到"}}
)

@router.get("/public", summary="公开接口示例")
async def public_endpoint():
    """
    公开接口，无需权限即可访问
    """
    return {
        "message": "这是一个公开接口，任何人都可以访问"
    }

@router.get("/basic-auth", summary="基本认证示例")
async def basic_auth_endpoint(current_user: User = Depends(get_current_user)):
    """
    基本认证接口，需要用户登录才能访问
    """
    return {
        "message": f"欢迎，{current_user.name}! 您已成功登录。",
        "user_id": current_user.id,
        "roles": [role.name for role in current_user.roles]
    }

@router.get("/user-permission", summary="使用装饰器的权限检查示例")
@require_permission("USER", "READ")
async def user_permission_endpoint(current_user: User = Depends(get_current_user)):
    """
    使用装饰器检查权限的接口
    需要USER模块的READ权限
    """
    return {
        "message": f"您有权限访问用户模块的读取功能",
        "permission": "USER:READ",
        "user": current_user.name
    }

@router.get("/admin-permission", summary="管理员权限示例")
@require_permission("USER", "ADMIN")
async def admin_permission_endpoint(current_user: User = Depends(get_current_user)):
    """
    需要管理员权限的接口
    需要USER模块的ADMIN权限
    """
    return {
        "message": f"您有管理员权限",
        "permission": "USER:ADMIN",
        "user": current_user.name
    }

@router.get("/manual-check", summary="手动检查权限示例")
async def manual_check_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    手动检查权限的接口示例
    根据不同的权限返回不同的内容
    """
    # 获取用户所有权限
    user_permissions = PermissionChecker.get_user_permissions(current_user)
    
    # 检查不同权限
    has_qa_read = PermissionChecker.check_user_permission(current_user, "QA", "READ")
    has_event_write = PermissionChecker.check_user_permission(current_user, "EVENT", "WRITE")
    has_user_admin = PermissionChecker.check_user_permission(current_user, "USER", "ADMIN")
    
    # 返回不同权限等级的信息
    result = {
        "user": current_user.name,
        "permissions": user_permissions,
        "access_levels": {
            "qa_read": has_qa_read,
            "event_write": has_event_write,
            "user_admin": has_user_admin
        }
    }
    
    # 根据权限添加额外信息
    if has_user_admin:
        result["admin_info"] = "这是管理员可见的信息"
    
    if has_qa_read:
        result["qa_info"] = "这是QA读取权限可见的信息"
        
    if has_event_write:
        result["event_info"] = "这是事件写入权限可见的信息"
    
    return result

@router.get("/multi-level", summary="多级权限示例")
async def multi_level_endpoint(
    current_user: User = Depends(get_current_user)
):
    """
    展示多级权限处理
    根据用户的权限级别返回不同内容
    """
    result = {
        "user": current_user.name,
        "base_content": "这是基础内容，所有认证用户可见"
    }
    
    # 使用权限工具类检查权限
    if PermissionChecker.check_user_permission(current_user, "USER", "READ"):
        result["read_content"] = "这是USER:READ可见的内容"
        
    if PermissionChecker.check_user_permission(current_user, "USER", "WRITE"):
        result["write_content"] = "这是USER:WRITE可见的内容"
        
    if PermissionChecker.check_user_permission(current_user, "USER", "ADMIN"):
        result["admin_content"] = "这是USER:ADMIN可见的内容"
    
    return result 