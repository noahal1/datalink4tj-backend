from sqlalchemy import Column, Integer
from db.database import Base
from datetime import datetime

class Ehs(Base):
    __tablename__ = "ehs"

    id = Column(Integer, primary_key=True, index=True)  
    lwd = Column(Integer, nullable=False)  
    week = Column(Integer, nullable=False) 
    year = Column(Integer, default=datetime.now().year, nullable=False) 