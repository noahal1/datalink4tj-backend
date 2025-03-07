from sqlalchemy import Column, Integer, String, Float, Boolean
from db.database import Base
from datetime import datetime

#质量GP12
class Qa(Base):
    __tablename__ = "qa"
    id = Column(Integer, primary_key=True, index=True)
    line = Column(String(255))
    day = Column(String(255))
    month = Column(String(255))
    year = Column(String(255), default=datetime.now().year, nullable=False)
    value = Column(String(255))
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
    scrap_rate_c = Column(Float)
    scrap_rate_m = Column(Float)
    Ftt_tjm = Column(Float)
    Ftt_tjc = Column(Float)