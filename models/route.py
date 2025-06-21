from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
import json

class Route(Base):
    """
    路由模型

    表示系统中的一个路由或菜单项
    """
    __tablename__ = 'routes'

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(255), unique=True, index=True, nullable=True)
    name = Column(String(100), nullable=False)
    component = Column(String(255), nullable=True)
    meta = Column(JSON, nullable=True)
    parent_id = Column(Integer, ForeignKey('routes.id', ondelete='SET NULL'), nullable=True)
    sort_order = Column(Integer, default=0)
    
    # 子路由关系
    children = relationship("Route", 
                           backref="parent",
                           remote_side=[id])
    
    # 角色权限关系
    role_permissions = relationship("RoutePermission", back_populates="route", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Route {self.name} ({self.path})>"
    
    def to_dict(self):
        """
        将路由对象转换为字典
        """
        return {
            "id": self.id,
            "path": self.path,
            "name": self.name,
            "component": self.component,
            "meta": self.meta,
            "parent_id": self.parent_id,
            "sort_order": self.sort_order
        }
    
    # 处理元数据的获取和设置
    @property
    def meta_dict(self):
        """获取 meta 字段的字典表示"""
        if self.meta is None:
            return {}
        if isinstance(self.meta, dict):
            return self.meta
        try:
            return json.loads(self.meta)
        except:
            return {}
    
    @meta_dict.setter
    def meta_dict(self, value):
        """设置 meta 字段的字典表示"""
        if isinstance(value, dict):
            self.meta = json.dumps(value)
        else:
            self.meta = value 