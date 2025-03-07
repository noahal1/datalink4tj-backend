from sqlalchemy import Column, Integer, String
from db.database import Base

class PCL(Base):
    __tablename__ = 'pcl'
    id = Column(Integer, primary_key=True, index=True)
    line = Column(String(255))
    downtime = Column(String(255)) 