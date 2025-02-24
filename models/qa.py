from sqlalchemy import Column, Integer, String, Boolean
from db.database import Base
from datetime import datetime

class Qa(Base):
    __tablename__ = "qa"
    id = Column(Integer, primary_key=True, index=True)
    line = Column(String(255))
    day = Column(String(255))
    month = Column(String(255))
    year = Column(String(255), default=datetime.now().year, nullable=False)
    value = Column(String(255))
    scrapflag = Column(Boolean, default=False)