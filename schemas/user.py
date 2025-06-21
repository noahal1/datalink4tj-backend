from typing import List, Optional
from pydantic import BaseModel, Field
from schemas.department import Department
from schemas.permission import Role

class UserBase(BaseModel):
    name: str = Field(..., description="用户名")
    
class UserCreate(UserBase):
    password: str = Field(..., description="密码")
    department_id: int = Field(..., description="部门ID")
    is_active: bool = Field(True, description="是否激活")
    is_superuser: bool = Field(False, description="是否为超级管理员")
    role_ids: Optional[List[int]] = Field([], description="角色ID列表")

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    department_id: Optional[int] = Field(None, description="部门ID")
    is_active: Optional[bool] = Field(None, description="是否激活")
    role_ids: Optional[List[int]] = Field(None, description="角色ID列表")

class User(UserBase):
    id: int
    department: Department
    is_active: bool
    roles: List[Role] = []
    
    model_config = {
        "from_attributes": True,
        "extra": "ignore"  # 忽略额外字段，比如password
    }

# 用户简单信息
class UserInfo(BaseModel):
    id: int
    name: str
    department_id: Optional[int] = None
    
    model_config = {
        "from_attributes": True
    }

# 用户权限信息
class UserPermissionInfo(UserInfo):
    roles: List[str] = []
    
    model_config = {
        "from_attributes": True
    }

# 登录响应
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    user_name: str
    department: Optional[str] = None 