from sqlalchemy import Column, Integer, String, Date
from db.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    department = Column(String(255), nullable=False)  
    start_time = Column(Date, nullable=False)
    end_time = Column(Date, nullable=True)