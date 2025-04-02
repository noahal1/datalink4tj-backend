from sqlalchemy import Column, Integer, String, Date
from db.database import Base

#日任务
class MaintDaily(Base):
    __tablename__ ='maint_daily'
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    user_id = Column(Integer)
    title = Column(String(255))
    wheres = Column(String(255))
    type = Column(Integer)
    #predict_time = Column(Integer,nullable=True)  预计工时暂时不考虑
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

