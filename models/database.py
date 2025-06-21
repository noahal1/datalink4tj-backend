from sqlalchemy import Column, Integer, String, Text, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime

# 从正确的模块导入
from db.database import SessionLocal, engine, Base
from db.session import get_db

# 维修指标表
class MaintenanceMetric(Base):
    __tablename__ = "maintenance_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    equipment_type = Column(String(20), nullable=False, index=True)
    shift = Column(String(10), nullable=False, default="day")  # 班次: day 白班, night 夜班
    date = Column(Date, nullable=False, index=True)
    downtime_count = Column(Integer, nullable=False, default=0)
    downtime_minutes = Column(Float, nullable=False, default=0)
    parts_produced = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    user_id = Column(Integer, ForeignKey("users.id"))

    # 外键关系
    user = relationship("User", back_populates="maintenance_metrics")

# 停机单表
class DowntimeRecord(Base):
    __tablename__ = "downtime_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    line = Column(String(20), nullable=False, index=True)  # 线体
    shift = Column(String(10), nullable=False, default="day")  # 班次: day 白班, night 夜班
    date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)  # 状态: pending 待处理, in_progress 处理中, closed 已关闭
    downtime_minutes = Column(Float, nullable=False, default=0)
    equipment_name = Column(String(100), nullable=False)
    fault_description = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    reporter_name = Column(String(100), nullable=False)
    maintainer_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    user_id = Column(Integer, ForeignKey("users.id"))

    # 外键关系
    user = relationship("User", back_populates="downtime_records")

# 在User类中添加反向关系，必须在User类加载后执行
def setup_relationships():
    from models.user import User
    User.maintenance_metrics = relationship("MaintenanceMetric", back_populates="user")
    User.downtime_records = relationship("DowntimeRecord", back_populates="user") 