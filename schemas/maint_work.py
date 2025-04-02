from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

# 日维护任务Schema
class MaintDailyBase(BaseModel):
    """日维护任务基础Schema"""
    title: str = Field(..., description="任务标题")
    wheres: str = Field(..., description="维护位置/设备")
    content_daily: str = Field(..., description="维护内容")
    type: Optional[int] = Field(None, description="维护类型")

class MaintDailyCreate(MaintDailyBase):
    """创建日维护任务Schema"""
    title: str = Field(..., description="任务标题")
    date: str = Field(..., description="任务日期")
    user_id: int = Field(..., description="用户ID")
    wheres: str = Field(..., description="维护位置/设备")
    type: int = Field(..., description="维护类型")
    content_daily: str = Field(..., description="维护内容")
    solved: bool = Field(False, description="是否已解决")

class MaintDailyUpdate(BaseModel):
    """更新日维护任务Schema"""
    title: Optional[str] = Field(None, description="任务标题")
    wheres: Optional[str] = Field(None, description="维护位置/设备")
    content_daily: Optional[str] = Field(None, description="维护内容")
    type: Optional[int] = Field(None, description="维护类型")
    solved: Optional[bool] = Field(None, description="是否已解决")

class MaintDailyResponse(MaintDailyBase):
    """日维护任务响应Schema"""
    id: int
    date: date
    user_id: int
    solved: bool
    class Config:
        orm_mode = True
    
    @classmethod
    def model_validate_from_orm(cls, obj):
        # 创建一个对象的拷贝，避免修改原始对象
        data = {}
        for key, value in obj.__dict__.items():
            if key != "_sa_instance_state":  # 排除SQLAlchemy的内部属性
                data[key] = value
        
        # 添加solved属性
        data["solved"] = bool(obj.solved_flag)
        
        return cls.model_validate(data)

# 周任务Schema
class MaintWeeklyBase(BaseModel):
    """周任务基础Schema"""
    title: str = Field(..., description="任务标题")
    wheres: str = Field(..., description="维护位置/设备")
    content: str = Field(..., description="任务内容")
    degree: str = Field(..., description="严重程度")

class MaintWeeklyCreate(MaintWeeklyBase):
    """创建周任务Schema"""
    date_time: date = Field(..., description="任务日期")
    user_id: int = Field(..., description="用户ID")
    solved: bool = Field(False, description="是否已解决")

class MaintWeeklyUpdate(BaseModel):
    """更新周任务Schema"""
    title: Optional[str] = Field(None, description="任务标题")
    wheres: Optional[str] = Field(None, description="维护位置/设备")
    content: Optional[str] = Field(None, description="任务内容")
    degree: Optional[str] = Field(None, description="严重程度")
    date_time: Optional[date] = Field(None, description="任务日期")
    solved: Optional[bool] = Field(None, description="是否已解决")

class MaintWeeklyResponse(MaintWeeklyBase):
    """周任务响应Schema"""
    id: int
    date_time: date
    user_id: int
    solved: bool
    
    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }
    
    @classmethod
    def model_validate_from_orm(cls, obj):
        data = {}
        for key, value in obj.__dict__.items():
            if key != "_sa_instance_state":  # 排除SQLAlchemy的内部属性
                data[key] = value
        
        # 特殊处理DateTime字段映射到date_time
        if "DateTime" in data:
            data["date_time"] = data.pop("DateTime")
        
        # 添加solved属性
        data["solved"] = bool(obj.solved_flag)
        
        return cls.model_validate(data)