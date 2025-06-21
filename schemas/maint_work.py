from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

# 维修工作记录Schema
class MaintenanceWorkBase(BaseModel):
    """维修工作记录基础Schema"""
    equipment: str = Field(..., description="设备名称")
    description: str = Field(..., description="维修描述")
    date_reported: date = Field(..., description="报告日期")
    status: str = Field(..., description="状态")
    priority: str = Field(..., description="优先级")

class MaintenanceWorkCreate(MaintenanceWorkBase):
    """创建维修工作记录Schema"""
    user_id: int = Field(..., description="用户ID")

class MaintenanceWorkUpdate(BaseModel):
    """更新维修工作记录Schema"""
    equipment: Optional[str] = Field(None, description="设备名称")
    description: Optional[str] = Field(None, description="维修描述")
    status: Optional[str] = Field(None, description="状态")
    priority: Optional[str] = Field(None, description="优先级")
    date_completed: Optional[date] = Field(None, description="完成日期")

class MaintenanceWorkResponse(MaintenanceWorkBase):
    """维修工作记录响应Schema"""
    id: int
    user_id: int
    date_completed: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }

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
    
    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }
    
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

# 维修数据指标Schema
class MaintMetricsBase(BaseModel):
    """维修数据指标基础Schema"""
    equipment_type: str = Field(..., description="设备类型(SWI-L, SWI-R, RWH-L, RWH-R)")
    downtime_count: int = Field(..., description="停机次数")
    downtime_minutes: float = Field(..., description="停机时间(分钟)")
    parts_produced: int = Field(..., description="生产零件总数")

class MaintMetricsCreate(MaintMetricsBase):
    """创建维修数据指标Schema"""
    date: str = Field(..., description="记录日期")

class MaintMetricsUpdate(BaseModel):
    """更新维修数据指标Schema"""
    equipment_type: Optional[str] = Field(None, description="设备类型(SWI-L, SWI-R, RWH-L, RWH-R)")
    downtime_count: Optional[int] = Field(None, description="停机次数")
    downtime_minutes: Optional[float] = Field(None, description="停机时间(分钟)")
    parts_produced: Optional[int] = Field(None, description="生产零件总数")

class MaintMetricsResponse(MaintMetricsBase):
    """维修数据指标响应Schema"""
    id: int
    date: date
    user_id: int
    oee: Optional[float] = Field(None, description="设备综合效率")
    mttr: Optional[float] = Field(None, description="平均修复时间")
    mtbf: Optional[float] = Field(None, description="平均故障间隔时间")
    availability: Optional[float] = Field(None, description="设备可动率")
    
    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }