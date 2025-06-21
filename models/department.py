from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.database import Base

class Department(Base):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(String(100), nullable=True) 
    
    # 关联
    users = relationship("User", back_populates="department")  # 定义与用户的关系
    permissions = relationship("Permission", back_populates="department")  # 与权限的关系
