from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime

#质量GP12
class Qa(Base):
    __tablename__ = "qa"
    id = Column(Integer, primary_key=True, index=True)
    line = Column(String, index=True)
    day = Column(String)
    month = Column(String)
    year = Column(String)
    value = Column(String)
    scrapflag = Column(Boolean, default=False)

#质量杂项数据
class Qad(Base):
    __tablename__ = "qad"
    id = Column(Integer, primary_key=True, index=True)
    month = Column(Integer)
    year = Column(Integer, default=datetime.now().year, nullable=False)
    supplier_defect = Column(Integer)
    formal_amount = Column(Integer)
    informal_amount = Column(Integer)
    qc_ignore_amount = Column(Integer)
    Ftt_tjm = Column(Float)
    Ftt_tjc = Column(Float)

#质量KPI数据
class QaKpi(Base):
    __tablename__ = "qa_kpi"
    id = Column(Integer, primary_key=True, index=True)
    month = Column(Integer)
    year = Column(Integer, default=datetime.now().year, nullable=False)
    area = Column(String(50))  # 区域：新厂、老厂、汇总
    description = Column(String(255))  # KPI描述
    new_factory = Column(Float, default=0)  # 新厂数据
    old_factory = Column(Float, default=0)  # 老厂数据
    total = Column(Float, default=0)  # 汇总数据

class MonthlyTotal(Base):
    __tablename__ = "monthly_totals"

    id = Column(Integer, primary_key=True, index=True)
    line = Column(String(20), index=True)
    month = Column(Integer)
    year = Column(Integer)
    amount = Column(Integer)  # 月度总数