from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime

class Activity(Base):
    """活动记录模型"""
    
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, comment="活动标题")
    action = Column(String(255), nullable=False, comment="操作描述")
    details = Column(Text, nullable=True, comment="详细信息")
    
    # 活动元数据
    type = Column(String(50), nullable=False, comment="活动类型")
    icon = Column(String(50), nullable=True, comment="图标")
    color = Column(String(50), nullable=True, comment="颜色")
    target = Column(String(255), nullable=True, comment="目标链接")
    
    # 数据变更记录
    changes_before = Column(JSON, nullable=True, comment="变更前数据")
    changes_after = Column(JSON, nullable=True, comment="变更后数据")
    
    # 关联用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_name = Column(String(50), nullable=True, comment="用户名称")
    department = Column(String(50), nullable=True, comment="部门")
    
    # 时间记录
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关系
    user = relationship("User", back_populates="activities")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "action": self.action,
            "details": self.details,
            "type": self.type,
            "icon": self.icon,
            "color": self.color,
            "target": self.target,
            "changes": {
                "before": self.changes_before,
                "after": self.changes_after
            },
            "userId": self.user_id,
            "user": self.user_name,
            "department": self.department,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "time": self.format_time(self.created_at) if self.created_at else None
        }
    
    @staticmethod
    def format_time(dt):
        """格式化时间"""
        if not dt:
            return None
            
        now = datetime.now()
        diff = now - dt
        
        # 计算时间差
        seconds = diff.total_seconds()
        minutes = seconds / 60
        
        if minutes < 1:
            return "刚刚"
        if minutes < 60:
            return f"{int(minutes)} 分钟前"
            
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)} 小时前"
            
        days = diff.days
        if days < 7:
            if days == 1:
                return "昨天"
            return f"{days} 天前"
            
        return dt.strftime("%Y-%m-%d") 