from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from schemas import user as user_schema
from services import user as user_service
from db.session import get_db
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from core.security import get_current_user, create_access_token
from models.user import User
import logging
from services.activity_service import ActivityService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 注意：不要使用前缀，保持与OAuth2配置一致
router = APIRouter()

@router.post("/users/token", summary="用户登录获取令牌")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录并获取访问令牌
    
    参数:
    - form_data: OAuth2表单数据，包含用户名和密码
    - db: 数据库会话
    
    返回:
    - access_token: JWT访问令牌
    - token_type: 令牌类型 (bearer)
    - user_id: 用户ID
    - user_name: 用户名
    - department: 用户部门
    - roles: 用户角色列表
    """
    logger.info(f"尝试登录用户: {form_data.username}")
    
    # 验证用户
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"登录失败: 用户名或密码不正确 - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token = user_service.create_user_token(user)
    logger.info(f"用户登录成功: {user.name}, 部门: {user.department.name if user.department else 'None'}")
    
    # 获取用户角色名称列表
    roles = [role.name for role in user.roles] if user.roles else []
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "user_name": user.name,
        "department": user.department.name if user.department else None,
        "roles": roles
    }

@router.get("/users/me", summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前已认证用户的信息
    
    该接口用于前端验证令牌是否有效，并获取最新的用户信息
    """
    try:
        # 确保current_user存在
        if not current_user:
            logger.error("获取当前用户信息失败: 用户不存在")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
            
        # 安全获取用户角色名称列表
        roles = []
        try:
            if current_user.roles:
                roles = [role.name for role in current_user.roles]
        except Exception as e:
            logger.error(f"处理用户角色时出错: {str(e)}")
            roles = []
            
        # 安全获取部门名称
        department = None
        try:
            if current_user.department:
                department = current_user.department.name
        except Exception as e:
            logger.error(f"处理用户部门时出错: {str(e)}")
            department = None
            
        # 构建响应
        response = {
            "user_id": current_user.id,
            "user_name": current_user.name,
            "department": department,
            "email": getattr(current_user, "email", None),
            "is_active": current_user.is_active,
            "roles": roles
        }
        
        logger.info(f"获取当前用户信息成功: {current_user.name}")
        return response
    except Exception as e:
        logger.error(f"获取当前用户信息时发生未预期的错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )

@router.post("/users", response_model=user_schema.User, summary="创建用户")
async def create_user(
    user: user_schema.UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新用户
    
    参数:
    - user: 用户创建模式
    - db: 数据库会话
    
    返回:
    - 创建的用户对象
    """
    # 权限检查
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有创建用户的权限"
        )
    
    try:
        # 创建用户
        new_user = user_service.create_user_service(db, user)
        
        # 记录活动
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="USER",
            action_type="CREATE",
            title="创建用户",
            action=f"创建了用户 '{new_user.name}'",
            details=f"创建用户: {new_user.name}, 部门: {new_user.department.name if new_user.department else '无'}",
            after_data={
                "id": new_user.id,
                "name": new_user.name,
                "department": new_user.department.name if new_user.department else None,
                "roles": [role.name for role in new_user.roles] if new_user.roles else []
            },
            target=f"/admin/users/{new_user.id}"
        )
        
        return new_user
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户失败: {str(e)}"
        )

@router.get("/users/permissions", summary="获取当前用户的权限信息")
async def get_current_user_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户的权限详细信息，包括角色和具体权限
    """
    try:
        # 获取用户角色
        roles = [{"id": role.id, "name": role.name} for role in current_user.roles]
        
        # 获取权限
        permissions = []
        for role in current_user.roles:
            for permission in role.permissions:
                permissions.append({
                    "module": permission.module,
                    "level": permission.level,
                    "department_id": permission.department_id
                })
        
        # 检查特定权限
        has_qa_read = any(
            p["module"] == "QA" and p["level"] in ["READ", "WRITE", "ADMIN"]
            for p in permissions
        )
        
        logger.info(f"获取用户 {current_user.name} 的权限信息成功")
        
        # 返回权限信息
        return {
            "roles": roles,
            "permissions": permissions,
            "has_qa_read": has_qa_read
        }
    except Exception as e:
        logger.error(f"获取用户权限信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取权限信息失败: {str(e)}"
        )

@router.get("/users/{user_id}", response_model=user_schema.User, summary="获取用户信息")
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取用户信息
    
    参数:
    - user_id: 用户ID
    - db: 数据库会话
    - current_user: 当前用户
    
    返回:
    - 用户对象
    """
    logger.info(f"获取用户信息: user_id={user_id}, 当前用户={current_user.name}, 部门={current_user.department}")
    
    # 检查权限 - 用户只能查看自己的信息，除非有USER模块的READ权限
    if current_user.id != user_id and not current_user.has_permission("USER", "READ"):
        logger.warning(f"权限不足: 用户 {current_user.name} 尝试访问用户 {user_id} 的信息")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此用户信息"
        )
    
    db_user = user_service.get_user_service(db, user_id)
    if not db_user:
        logger.warning(f"用户不存在: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return db_user

@router.get("/users", response_model=List[user_schema.User], summary="获取用户列表")
async def read_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取用户列表
    
    参数:
    - skip: 跳过的记录数
    - limit: 返回的最大记录数
    - db: 数据库会话
    - current_user: 当前用户
    
    返回:
    - 用户对象列表
    """
    logger.info(f"获取用户列表: 当前用户={current_user.name}, 部门={current_user.department}")
    
    # 只有管理员可以查看用户列表
    if not current_user.has_permission("USER", "READ"):
        logger.warning(f"权限不足: 用户 {current_user.name} 尝试获取用户列表")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看用户列表"
        )
    
    try:
        users = user_service.get_users_service(db, skip, limit)
        return users
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )

@router.put("/users/{user_id}", response_model=user_schema.User, summary="更新用户信息")
async def update_user(
    user_id: int,
    user_update: user_schema.UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    更新用户信息
    
    参数:
    - user_id: 用户ID
    - user_update: 更新的用户信息
    - db: 数据库会话
    - current_user: 当前用户
    
    返回:
    - 更新后的用户对象
    """
    # 检查权限 - 用户只能更新自己的信息，除非有USER模块的WRITE权限
    if current_user.id != user_id and not current_user.has_permission("USER", "WRITE"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权更新此用户信息"
        )
    
    # 特殊字段权限检查 - 只有管理员可以修改角色
    if user_update.role_ids is not None and not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改用户的角色"
        )
    
    try:
        # 获取更新前的用户数据，用于比较变化
        old_user = user_service.get_user_service(db, user_id)
        if not old_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 保存旧数据用于活动日志
        old_data = {
            "id": old_user.id,
            "name": old_user.name,
            "department": old_user.department.name if old_user.department else None,
            "is_active": old_user.is_active,
            "roles": [role.name for role in old_user.roles] if old_user.roles else []
        }
        
        # 移除is_superuser字段
        if hasattr(user_update, 'is_superuser'):
            delattr(user_update, 'is_superuser')
        
        # 更新用户
        updated_user = user_service.update_user_service(db, user_id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 保存新数据用于活动日志
        new_data = {
            "id": updated_user.id,
            "name": updated_user.name,
            "department": updated_user.department.name if updated_user.department else None,
            "is_active": updated_user.is_active,
            "roles": [role.name for role in updated_user.roles] if updated_user.roles else []
        }
        
        # 记录活动
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="USER",
            action_type="UPDATE",
            title="更新用户",
            action=f"更新了用户 '{updated_user.name}' 的信息",
            details=f"更新用户: {updated_user.name}",
            before_data=old_data,
            after_data=new_data,
            target=f"/admin/users/{updated_user.id}"
        )
        
        return updated_user
    except Exception as e:
        logger.error(f"更新用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户失败: {str(e)}"
        )

@router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    删除用户
    
    参数:
    - user_id: 用户ID
    - db: 数据库会话
    - current_user: 当前用户
    
    返回:
    - 删除成功消息
    """
    # 只有管理员可以删除用户
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除用户"
        )
    
    try:
        # 获取要删除的用户信息，用于活动日志
        user_to_delete = user_service.get_user_service(db, user_id)
        if not user_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 保存用户数据用于活动日志
        deleted_user_data = {
            "id": user_to_delete.id,
            "name": user_to_delete.name,
            "department": user_to_delete.department.name if user_to_delete.department else None,
            "roles": [role.name for role in user_to_delete.roles] if user_to_delete.roles else []
        }
        
        # 删除用户
        success = user_service.delete_user_service(db, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 记录活动
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="USER",
            action_type="DELETE",
            title="删除用户",
            action=f"删除了用户 '{user_to_delete.name}'",
            details=f"删除用户: {user_to_delete.name}, ID: {user_id}",
            before_data=deleted_user_data,
            target="/admin/users"
        )
        
        return {"message": "用户删除成功"}
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )

@router.post("/users/{user_id}/roles", summary="为用户分配角色")
async def assign_user_roles(
    user_id: int,
    assignment: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    为用户分配角色
    
    参数:
    - user_id: 用户ID
    - assignment: 角色分配请求体 {user_id: int, role_ids: List[int]}
    - db: 数据库会话
    - current_user: 当前用户
    
    返回:
    - 分配成功消息
    """
    # 权限检查
    if not current_user.has_permission("USER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权分配用户角色"
        )
        
    # 验证用户ID
    if user_id != assignment.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户ID不匹配"
        )
        
    # 角色ID列表
    role_ids = assignment.get("role_ids", [])
    if not isinstance(role_ids, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色ID必须是数组"
        )
        
    # 记录要分配的角色ID
    logger.info(f"为用户 {user_id} 分配角色: {role_ids}")
    
    try:
        # 获取用户当前角色，用于活动日志
        user_before = user_service.get_user_service(db, user_id)
        if not user_before:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 保存旧角色数据
        old_roles = [{"id": role.id, "name": role.name} for role in user_before.roles] if user_before.roles else []
        
        # 分配角色
        success = user_service.assign_user_roles_service(db, user_id, role_ids)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在或角色分配失败"
            )
        
        # 获取更新后的用户角色
        user_after = user_service.get_user_service(db, user_id)
        new_roles = [{"id": role.id, "name": role.name} for role in user_after.roles] if user_after.roles else []
        
        # 记录活动
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="USER",
            action_type="UPDATE",
            title="更新用户角色",
            action=f"更新了用户 '{user_before.name}' 的角色",
            details=f"为用户 {user_before.name} 分配新角色",
            before_data={"roles": old_roles},
            after_data={"roles": new_roles},
            target=f"/admin/users/{user_id}"
        )
        
        return {"message": "角色分配成功"}
    except Exception as e:
        logger.error(f"分配角色失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配角色失败: {str(e)}"
        )