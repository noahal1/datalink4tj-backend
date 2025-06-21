from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base

class RoutePermission(Base):
    """
    路由权限关联表，用于存储角色可访问的路由
    """
    __tablename__ = "route_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    role = relationship("Role", back_populates="route_permissions")
    route = relationship("Route", back_populates="role_permissions")

    def __repr__(self):
        return f"<RoutePermission(role_id={self.role_id}, route_id={self.route_id})>" 