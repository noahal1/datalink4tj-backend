from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from db.database import Base
from passlib.context import CryptContext
from models.permission import user_role, PermissionLevel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 超级管理员角色名称
SUPER_ADMIN_ROLE = "超级管理员"

class User(Base):
    """用户模型，定义系统用户及其权限"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, unique=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete="SET NULL"))
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)  # 用户是否激活
    
    # 关联
    department = relationship("Department", back_populates="users")
    activities = relationship("Activity", back_populates="user")
    roles = relationship("Role", secondary=user_role, back_populates="users")

    def verify_password(self, password: str) -> bool:
        """验证用户密码"""
        return pwd_context.verify(password, self.password)

    def set_password(self, password: str) -> None:
        """设置用户密码，自动进行哈希处理"""
        self.password = pwd_context.hash(password)
        
    def has_permission(self, module: str, level: str, target_department_id: int = None) -> bool:
        """
        检查用户是否拥有特定模块和等级的权限
        
        参数:
        - module: 模块名称
        - level: 权限等级
        - target_department_id: 目标部门ID，默认为None表示不限制部门
        
        返回:
        - bool: 是否拥有权限
        """
        # 检查用户的所有角色
        for role in self.roles:
            # 检查是否有超级管理员角色
            if role.name == SUPER_ADMIN_ROLE:
                return True
                
            for permission in role.permissions:
                # 检查模块匹配
                if permission.module != module and permission.module != "ALL":
                    continue
                    
                # 检查权限等级
                required_level_value = PermissionLevel.get_level_value(level)
                user_level_value = PermissionLevel.get_level_value(permission.level)
                
                if user_level_value < required_level_value:
                    continue
                    
                # 检查部门限制
                if permission.department_id is not None and target_department_id is not None:
                    if permission.department_id != target_department_id and permission.department_id != self.department_id:
                        continue
                        
                # 通过所有检查，拥有权限
                return True
                
        # 默认没有权限
        return False
        
    def get_roles(self) -> list:
        """获取用户角色名称列表"""
        return [role.name for role in self.roles] if self.roles else []
        
    def __repr__(self):
        return f"用户(ID: {self.id}, 名称: {self.name}, 部门ID: {self.department_id})"