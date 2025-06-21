from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from models.permission import PermissionLevel, Module

# 权限基础模式
class PermissionBase(BaseModel):
    module: str = Field(..., description="模块名称")
    level: str = Field(..., description="权限等级")
    department_id: Optional[int] = Field(None, description="目标部门ID")

# 创建权限请求
class PermissionCreate(PermissionBase):
    pass

# 更新权限请求
class PermissionUpdate(BaseModel):
    module: Optional[str] = Field(None, description="模块名称")
    level: Optional[str] = Field(None, description="权限等级")
    department_id: Optional[int] = Field(None, description="目标部门ID")

# 权限响应模式
class Permission(PermissionBase):
    id: int
    
    model_config = {
        "from_attributes": True
    }

# 角色基础模式
class RoleBase(BaseModel):
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")

# 创建角色请求
class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")

# 更新角色请求
class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")

# 角色响应模式
class Role(RoleBase):
    id: int
    permissions: List[Permission] = []
    
    model_config = {
        "from_attributes": True
    }

# 简单角色响应模式（不包含权限详情）
class RoleSimple(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    
    model_config = {
        "from_attributes": True
    }

# 检查权限请求
class PermissionCheck(BaseModel):
    module: str = Field(..., description="模块名称")
    level: str = Field(..., description="所需权限等级")
    department_id: Optional[int] = Field(None, description="目标部门ID")

# 权限检查结果
class PermissionResult(BaseModel):
    has_permission: bool = Field(..., description="是否拥有权限")
    user_id: int = Field(..., description="用户ID")
    module: str = Field(..., description="请求的模块")
    level: str = Field(..., description="请求的权限等级")

# 用户角色分配请求
class UserRoleAssignment(BaseModel):
    user_id: int = Field(..., description="用户ID")
    role_ids: List[int] = Field(..., description="角色ID列表") 