from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from db.database import Base

# 权限等级枚举
class PermissionLevel(str, Enum):
    """权限等级枚举，定义系统中的权限级别"""
    READ = "READ"             # 只读权限
    WRITE = "WRITE"           # 写入权限
    ADMIN = "ADMIN"           # 管理员权限
    SUPER_ADMIN = "SUPER_ADMIN"  # 超级管理员权限
    
    @classmethod
    def get_level_value(cls, level):
        """获取权限等级的数值，用于比较权限高低"""
        level_values = {
            cls.READ: 1,
            cls.WRITE: 2,
            cls.ADMIN: 3,
            cls.SUPER_ADMIN: 4
        }
        return level_values.get(level, 0)

# 模块枚举
class Module(str, Enum):
    """模块枚举，定义系统中的功能模块"""
    USER = "USER"             # 用户管理
    DEPARTMENT = "DEPARTMENT" # 部门管理
    EHS = "EHS"               # EHS模块
    QA = "QA"                 # 质量管理
    EVENT = "EVENT"           # 事件管理
    MAINT = "MAINT"           # 维修管理
    ACTIVITY = "ACTIVITY"     # 活动管理
    ROUTE = "ROUTE"           # 路由管理
    ALL = "ALL"               # 所有模块
    
    @classmethod
    def is_valid_module(cls, module):
        """检查是否为有效的模块名称"""
        return module in [m.value for m in cls] or module == "ALL"

# 用户-角色关联表
user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE")),
)

# 角色-权限关联表
role_permission = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE")),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE")),
)

# 角色模型
class Role(Base):
    """角色模型，定义用户角色及其拥有的权限"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(String(200), nullable=True)
    
    # 关联
    users = relationship("User", secondary=user_role, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permission, back_populates="roles")
    route_permissions = relationship("RoutePermission", back_populates="role", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"角色(ID: {self.id}, 名称: {self.name})"
    
    def has_permission(self, module, level):
        """检查角色是否拥有指定模块和级别的权限"""
        required_level_value = PermissionLevel.get_level_value(level)
        
        for permission in self.permissions:
            # 检查模块是否匹配
            if permission.module != module and permission.module != "ALL":
                continue
                
            # 检查权限等级
            perm_level_value = PermissionLevel.get_level_value(permission.level)
            if perm_level_value >= required_level_value:
                return True
                
        return False

# 权限模型
class Permission(Base):
    """权限模型，定义系统中的权限项"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    module = Column(String(200), index=True)  # 模块
    level = Column(String(100), index=True)   # 权限等级
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)  # 部门约束
    
    # 关联
    department = relationship("Department", back_populates="permissions")
    roles = relationship("Role", secondary=role_permission, back_populates="permissions")
    
    def __repr__(self):
        dept = f"部门ID: {self.department_id}" if self.department_id else "所有部门"
        return f"权限(模块: {self.module}, 等级: {self.level}, {dept})"
    
    @staticmethod
    def format_permission(module, level):
        """格式化权限为字符串表示"""
        return f"{module}:{level}"
        
    @staticmethod
    def parse_permission(permission_string):
        """解析权限字符串为模块和等级"""
        parts = permission_string.split(":")
        if len(parts) != 2:
            return None, None
        return parts[0], parts[1] 