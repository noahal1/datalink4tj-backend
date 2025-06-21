from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import date, datetime

# 维修指标模型
class MaintenanceMetric(BaseModel):
    id: Optional[int] = None
    equipment_type: str
    shift: Optional[str] = "day"  # 班次: day 白班, night 夜班
    date: date
    downtime_count: int = 0
    downtime_minutes: float = 0.0
    parts_produced: int = 0
    oee: Optional[float] = None
    mttr: Optional[float] = None
    mtbf: Optional[float] = None
    availability: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: int

    class Config:
        orm_mode = True

# 停机单模型
class DowntimeRecord(BaseModel):
    id: Optional[int] = None
    line: str  # 线体
    shift: str = "day"  # 班次: day 白班, night 夜班
    date: date
    status: str = "pending"  # 状态: pending 待处理, in_progress 处理中, closed 已关闭
    downtime_minutes: float
    equipment_name: str
    fault_description: str
    resolution: Optional[str] = None
    reporter_name: str
    maintainer_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: int

    class Config:
        orm_mode = True

# 图表响应模型 - OEE趋势
class OEEDataPoint(BaseModel):
    date: str
    oee: float

class OEETrendResponse(BaseModel):
    start_date: str
    end_date: str
    equipment_type: Optional[str] = None
    trend_data: List[OEEDataPoint]

# 图表响应模型 - MTTR和MTBF趋势
class MTTRMTBFDataPoint(BaseModel):
    date: str
    mttr: float  # 平均修复时间
    mtbf: float  # 平均故障间隔时间

class MTTRMTBFTrendResponse(BaseModel):
    start_date: str
    end_date: str
    equipment_type: Optional[str] = None
    trend_data: List[MTTRMTBFDataPoint]

# 图表响应模型 - 生产线比较
class LineComparisonData(BaseModel):
    equipment_type: str
    downtime_minutes: float
    downtime_count: int
    parts_produced: int
    availability: float
    oee: float
    mttr: float
    mtbf: float

class LineComparisonResponse(BaseModel):
    start_date: str
    end_date: str
    comparison_data: List[LineComparisonData]

# 图表请求参数模型
class ChartQueryParams(BaseModel):
    equipment_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None 