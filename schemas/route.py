from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, validator, Field

# 路由元数据模式
class RouteMeta(BaseModel):
    title: Optional[str] = None
    icon: Optional[str] = None
    requiresAuth: Optional[bool] = True
    permission: Optional[str] = None
    public: Optional[bool] = False
    group: Optional[str] = None  # 导航分组

# 路由基础模式
class RouteBase(BaseModel):
    """路由基础模型"""
    path: Optional[str] = None
    name: str
    component: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = Field(default=0)

# 路径参数模型
class RoutePathParam(BaseModel):
    name: str
    type: str = "string"
    description: Optional[str] = None
    required: bool = True

# 路径配置模型
class RoutePathConfig(BaseModel):
    basePath: str
    hasDynamicSegments: bool = False
    params: List[RoutePathParam] = []

# 路由创建模型
class RouteCreate(BaseModel):
    path: Optional[str] = None
    name: str
    component: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = 0
    path_config: Optional[RoutePathConfig] = None

# 路由更新模型
class RouteUpdate(BaseModel):
    path: Optional[str] = None
    name: Optional[str] = None
    component: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    path_config: Optional[RoutePathConfig] = None
    
    @validator('meta', pre=True)
    def validate_empty_meta(cls, v):
        """确保meta不为None"""
        if v is None:
            return {}
        return v

# 路由响应模型
class RouteResponse(BaseModel):
    id: int
    path: Optional[str] = None
    name: str
    component: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    parent_id: Optional[int] = None
    sort_order: int = 0
    path_config: Optional[RoutePathConfig] = None
    
    class Config:
        from_attributes = True  # 允许从ORM模型创建

# 路由树节点模型
class RouteTree(RouteResponse):
    """路由树节点模型"""
    children: List['RouteTree'] = []

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

# 处理循环引用问题
RouteTree.update_forward_refs()

# 导航菜单项
class NavMenuItem(BaseModel):
    id: int
    path: str
    title: str
    icon: Optional[str] = None
    children: Optional[List['NavMenuItem']] = []

# 导航菜单组
class NavMenuGroup(BaseModel):
    id: str
    title: str
    items: List[NavMenuItem]

# 路由权限响应模型
class RoutePermissionResponse(BaseModel):
    route_id: int
    role_id: int
    
    class Config:
        from_attributes = True 