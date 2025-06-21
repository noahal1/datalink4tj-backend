from sqlalchemy import Column, Integer, String, Date, Float, Text, DateTime
from db.database import Base
from datetime import datetime

# 维修工作记录
class MaintenanceWork(Base):
    __tablename__ = 'maintenance_works'
    id = Column(Integer, primary_key=True)
    equipment = Column(String(255))
    description = Column(Text)
    date_reported = Column(Date)
    date_completed = Column(Date, nullable=True)
    status = Column(String(50))
    priority = Column(String(50))
    user_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

#日任务
class MaintDaily(Base):
    __tablename__ ='maint_daily'
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    user_id = Column(Integer)
    title = Column(String(255))
    wheres = Column(String(255))
    type = Column(Integer)
    #predict_time = Column(Integer,nullable=True) 
    content_daily = Column(String(255))
    solved_flag = Column(Integer)

 #周任务   
class MaintWeekly(Base):
    __tablename__ ='maint_weekly'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)  
    DateTime = Column(Date)
    title = Column(String(255))
    wheres = Column(String(255))
    content = Column(String(255))
    degree = Column(String(255))
    solved_flag = Column(Integer)

#维修数据指标
class MaintMetrics(Base):
    __tablename__ = 'maint_metrics'
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    line = Column(String(10))  # SWI-L, SWI-R, RWH-L, RWH-R
    downtime_count = Column(Integer)  # 停机次数1``
    downtime_minutes = Column(Float)  # 停机时间(分钟)
    parts_produced = Column(Integer)  # 生产零件总数
    shift_code = Column(Integer)  # 班次代码
    oee = Column(Float, nullable=True)  # 设备综合效率
    mttr = Column(Float, nullable=True)  # 平均修复时间
    mtbf = Column(Float, nullable=True)  # 平均故障间隔时间
    availability = Column(Float, nullable=True)  

class MaintDownRecords(Base):
    __tablename__ ='maint_down_records'
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    line = Column(String(10))  # SWI-L, SWI-R, RWH-L, RWH-R
    shift_code = Column(Integer)  # 班次代码
    type_code = Column(String(20))  
    reason_code = Column(String(20))  
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    remark = Column(String(155))

