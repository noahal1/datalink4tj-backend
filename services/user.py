from sqlalchemy.orm import Session, joinedload
from models.user import User
from schemas.user import UserCreate, UserUpdate
from core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from typing import List, Optional
from datetime import timedelta
from fastapi import HTTPException, status
from services.permission_service import RoleService

# 通过用户名获取用户
def get_user_by_name(db: Session, username: str) -> Optional[User]:
    """
    通过用户名获取用户
    
    参数:
    - db: 数据库会话
    - username: 用户名
    
    返回:
    - 用户对象，如果不存在返回None
    """
    return db.query(User).filter(User.name == username).first()

# 获取单个用户
def get_user_service(db: Session, user_id: int) -> Optional[User]:
    """
    通过ID获取用户
    
    参数:
    - db: 数据库会话
    - user_id: 用户ID
    
    返回:
    - 用户对象，如果不存在返回None
    """
    return db.query(User).options(joinedload(User.roles)).filter(User.id == user_id).first()

# 获取用户列表
def get_users_service(db: Session, skip: int = 0, limit: int = 10) -> List[User]:
    """
    获取用户列表
    
    参数:
    - db: 数据库会话
    - skip: 跳过的记录数
    - limit: 返回的最大记录数
    
    返回:
    - 用户对象列表
    """
    try:
        users = db.query(User).options(joinedload(User.department), joinedload(User.roles)).offset(skip).limit(limit).all()
        # 日志记录用户数量，帮助调试
        print(f"获取到 {len(users)} 个用户")
        for user in users:
            # 确保每个用户的department不是None，否则可能导致序列化错误
            if user.department is None:
                print(f"警告: 用户 {user.name} (ID: {user.id}) 没有关联部门")
            if user.roles is None:
                user.roles = []
                print(f"警告: 用户 {user.name} (ID: {user.id}) 没有关联角色")
            else:
                print(f"用户 {user.name} 的角色: {[role.name for role in user.roles]}")
        return users
    except Exception as e:
        print(f"获取用户列表时发生错误: {str(e)}")
        # 重新抛出异常让调用者处理
        raise

# 创建用户
def create_user_service(db: Session, user: UserCreate) -> User:
    """
    创建新用户
    
    参数:
    - db: 数据库会话
    - user: 用户创建模式
    
    返回:
    - 创建的用户对象
    """
    # 检查用户名是否已经存在
    existing_user = db.query(User).filter(User.name == user.name).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 获取密码哈希
    hashed_password = get_password_hash(user.password)
    
    # 创建用户
    db_user = User(
        name=user.name, 
        password=hashed_password, 
        department_id=user.department_id,
        is_active=user.is_active
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 分配角色
    if user.role_ids:
        RoleService.assign_user_roles(db, db_user.id, user.role_ids)
        db.refresh(db_user)
    
    return db_user

# 更新用户
def update_user_service(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """
    更新用户信息
    
    参数:
    - db: 数据库会话
    - user_id: 用户ID
    - user_update: 更新的用户信息
    
    返回:
    - 更新后的用户对象，如果用户不存在返回None
    """
    db_user = get_user_service(db, user_id)
    if not db_user:
        return None
    
    # 更新用户字段
    update_data = user_update.dict(exclude={"role_ids"}, exclude_unset=True)
    
    # 如果更新包含密码，更新密码哈希
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    
    # 如果提供了角色ID，更新用户角色
    if user_update.role_ids is not None:
        RoleService.assign_user_roles(db, db_user.id, user_update.role_ids)
        db.refresh(db_user)
    
    return db_user

# 删除用户
def delete_user_service(db: Session, user_id: int) -> bool:
    """
    删除用户
    
    参数:
    - db: 数据库会话
    - user_id: 用户ID
    
    返回:
    - 删除成功返回True，用户不存在返回False
    """
    db_user = get_user_service(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    
    return True

# 用户认证
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    验证用户凭据
    
    参数:
    - db: 数据库会话
    - username: 用户名
    - password: 密码
    
    返回:
    - 验证成功返回用户对象，失败返回None
    """
    user = get_user_by_name(db, username)
    if not user:
        return None
    
    if not user.verify_password(password):
        return None
    
    # 检查用户是否激活
    if not user.is_active:
        return None
    
    return user

# 创建访问令牌
def create_user_token(user: User) -> str:
    """
    为用户创建访问令牌
    
    参数:
    - user: 用户对象
    
    返回:
    - JWT访问令牌
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": user.name},
        expires_delta=access_token_expires
    )

# 为用户分配角色
def assign_user_roles_service(db: Session, user_id: int, role_ids: List[int]) -> bool:
    """
    为用户分配角色
    
    参数:
    - db: 数据库会话
    - user_id: 用户ID
    - role_ids: 角色ID列表
    
    返回:
    - bool: 操作是否成功
    """
    try:
        # 使用RoleService的静态方法分配角色
        success = RoleService.assign_user_roles(db, user_id, role_ids)
        return success
    except Exception as e:
        print(f"分配用户角色服务出错: {str(e)}")
        return False