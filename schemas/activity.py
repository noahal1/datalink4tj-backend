from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union, List
from datetime import datetime

class ActivityBase(BaseModel):
    """活动基础模型"""
    title: str = Field(..., description="活动标题")
    action: str = Field(..., description="操作描述")
    details: Optional[str] = Field(None, description="详细信息")
    type: str = Field(..., description="活动类型")
    icon: Optional[str] = Field(None, description="图标")
    color: Optional[str] = Field(None, description="颜色")
    target: Optional[str] = Field(None, description="目标链接")
    user_id: Optional[int] = Field(None, description="用户ID")
    user_name: Optional[str] = Field(None, description="用户名称")
    department: Optional[str] = Field(None, description="部门")

class ActivityCreate(ActivityBase):
    """创建活动模型"""
    changes_before: Optional[Dict[str, Any]] = Field(None, description="变更前数据")
    changes_after: Optional[Dict[str, Any]] = Field(None, description="变更后数据")

class ActivityUpdate(BaseModel):
    """更新活动模型"""
    title: Optional[str] = Field(None, description="活动标题")
    action: Optional[str] = Field(None, description="操作描述")
    details: Optional[str] = Field(None, description="详细信息")
    type: Optional[str] = Field(None, description="活动类型")
    icon: Optional[str] = Field(None, description="图标")
    color: Optional[str] = Field(None, description="颜色")
    target: Optional[str] = Field(None, description="目标链接")

class ActivityInDB(ActivityBase):
    """数据库中的活动模型"""
    id: int
    changes_before: Optional[Dict[str, Any]] = None
    changes_after: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

class ActivityResponse(BaseModel):
    """API响应的活动模型"""
    id: int
    title: str
    action: str
    details: Optional[str] = None
    type: str
    icon: Optional[str] = None
    color: Optional[str] = None
    target: Optional[str] = None
    changes: Dict[str, Any] = Field(default_factory=dict)
    userId: Optional[int] = None
    user: Optional[str] = None
    department: Optional[str] = None
    timestamp: Optional[str] = None
    time: Optional[str] = None
    
    class Config:
        orm_mode = True

class PaginatedActivityResponse(BaseModel):
    """分页的活动响应模型"""
    total: int
    items: List[ActivityResponse]

class DataChangePayload(BaseModel):
    """数据变更负载"""
    module: str = Field(..., description="模块名称")
    type: str = Field(..., description="操作类型 (CREATE, UPDATE, DELETE, UPLOAD, EXPORT)")
    title: Optional[str] = Field(None, description="活动标题")
    description: Optional[str] = Field(None, description="操作描述")
    before: Optional[Dict[str, Any]] = Field(None, description="变更前数据")
    after: Optional[Dict[str, Any]] = Field(None, description="变更后数据")
    details: Optional[Dict[str, Any]] = Field(None, description="其他详细信息") 