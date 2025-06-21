"""
API辅助工具 - 提供常用装饰器和工具函数，减少API处理代码冗余
"""
from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Callable, Dict, Any, List, Optional, Type, Union
from pydantic import BaseModel
from models.user import User
from core.security import get_current_user
from db.session import get_db
from services.activity_service import ActivityService
import logging

# 配置日志
logger = logging.getLogger(__name__)

def permission_required(module: str, level: str, verify_target_dept: bool = False):
    """
    权限检查装饰器
    
    参数:
    - module: 模块名称
    - level: 权限级别
    - verify_target_dept: 是否验证目标部门
    
    用法:
    @router.get("/items")
    @permission_required("ITEM", "READ")
    async def get_items():
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, 
                         current_user: User = Depends(get_current_user), 
                         db: Session = Depends(get_db),
                         **kwargs):
            target_department_id = kwargs.get('department_id')
            
            # 权限检查
            if not current_user.has_permission(module, level, 
                                               target_department_id if verify_target_dept else None):
                logger.warning(f"用户 {current_user.name} 尝试访问 {module} 模块，但权限不足 (需要: {level})")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足: 需要 {module} 模块的 {level} 权限"
                )
                
            return await func(*args, current_user=current_user, db=db, **kwargs)
        return wrapper
    return decorator

def record_activity(module: str, action_type: str, title_template: str = None):
    """
    记录用户活动的装饰器
    
    参数:
    - module: 模块名称
    - action_type: 操作类型 (CREATE/UPDATE/DELETE/VIEW)
    - title_template: 活动标题模板 (可使用格式化字符串，会传入所有原始参数)
    
    用法:
    @router.post("/users")
    @record_activity("USER", "CREATE", "创建用户 {user.name}")
    async def create_user(user: UserCreate):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, 
                          current_user: User = Depends(get_current_user), 
                          db: Session = Depends(get_db),
                          **kwargs):
            # 调用原始函数
            result = await func(*args, current_user=current_user, db=db, **kwargs)
            
            try:
                # 尝试构建活动标题
                title = title_template
                if title_template:
                    # 合并所有参数以供格式化使用
                    format_args = {**kwargs}
                    
                    # 如果结果是字典或对象，添加到格式化参数
                    if isinstance(result, dict):
                        format_args.update(result)
                    elif hasattr(result, '__dict__'):
                        format_args.update(vars(result))
                        
                    # 格式化标题
                    title = title_template.format(**format_args)
                else:
                    title = f"{module} {action_type}"
                
                # 记录活动
                ActivityService.record_data_change(
                    db=db,
                    user=current_user,
                    module=module,
                    action_type=action_type,
                    title=title,
                    action=title,
                    details=f"{action_type}: {title}",
                    after_data=result if isinstance(result, dict) else None,
                )
            except Exception as e:
                # 记录活动失败不应影响API正常响应
                logger.error(f"记录用户活动失败: {str(e)}")
            
            return result
        return wrapper
    return decorator

def handle_exceptions(error_message: str = "操作失败"):
    """
    异常处理装饰器
    
    参数:
    - error_message: 默认错误消息
    
    用法:
    @router.post("/items")
    @handle_exceptions("创建项目失败")
    async def create_item(item: ItemCreate):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # 直接重新抛出HTTP异常
                raise
            except Exception as e:
                logger.error(f"{error_message}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{error_message}: {str(e)}"
                )
        return wrapper
    return decorator

def compose(*decorators):
    """
    组合多个装饰器
    
    用法:
    @router.post("/items")
    @compose(
        permission_required("ITEM", "WRITE"),
        record_activity("ITEM", "CREATE", "创建项目 {name}"),
        handle_exceptions("创建项目失败")
    )
    async def create_item(item: ItemCreate):
        ...
    """
    def decorator(func):
        for dec in reversed(decorators):
            func = dec(func)
        return func
    return decorator 