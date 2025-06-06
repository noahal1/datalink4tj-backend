from sqlalchemy.orm import Session
from datetime import datetime
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from models.activity import Activity
from models.user import User

class ActivityService:
    """活动记录服务，用于记录数据变更"""
    
    @staticmethod
    def record_data_change(
        db: Session,
        user: User,
        module: str,
        action_type: str,
        title: str,
        action: str,
        details: str = None,
        before_data = None,
        after_data = None,
        target: str = None
    ):
        """
        记录数据变更
        
        参数:
        - db: 数据库会话
        - user: 当前用户
        - module: 模块名称 (如 "QA", "EHS", "ASSY")
        - action_type: 操作类型 (如 "CREATE", "UPDATE", "DELETE")
        - title: 活动标题
        - action: 操作描述
        - details: 详细信息
        - before_data: 变更前的数据
        - after_data: 变更后的数据
        - target: 目标链接
        
        返回:
        - 创建的活动记录
        """
        try:
            # 设置图标和颜色
            icon = "mdi-file-document-edit"
            color = "primary"
            
            # 根据操作类型设置图标和颜色
            if action_type == "CREATE":
                icon = "mdi-plus-circle"
                color = "success"
            elif action_type == "UPDATE":
                icon = "mdi-pencil"
                color = "primary"
            elif action_type == "DELETE":
                icon = "mdi-delete"
                color = "error"
            elif action_type == "UPLOAD":
                icon = "mdi-cloud-upload"
                color = "info"
            elif action_type == "EXPORT":
                icon = "mdi-download"
                color = "secondary"
            
            # 如果没有提供目标链接，则根据模块生成
            if not target:
                target = f"/{module.lower()}"
            
            # 记录日志
            logger.info(f"记录数据变更: 模块={module}, 操作={action_type}, 标题={title}")
            
            # 创建活动记录
            activity = Activity(
                title=title,
                action=action,
                details=details,
                type=f"{module.upper()}_{action_type}",
                icon=icon,
                color=color,
                target=target,
                user_id=user.id if user else None,
                user_name=user.name if user else "系统",
                department=user.department.name if user and user.department else None,
                changes_before=json.dumps(before_data, default=str) if before_data is not None else None,
                changes_after=json.dumps(after_data, default=str) if after_data is not None else None,
                created_at=datetime.now()
            )
            
            # 添加到数据库
            db.add(activity)
            db.commit()
            db.refresh(activity)
            
            logger.info(f"数据变更记录成功: ID={activity.id}")
            
            return activity
        except Exception as e:
            logger.error(f"记录数据变更失败: {str(e)}")
            db.rollback()
            raise e

    @staticmethod
    def format_changes(before_data, after_data):
        """格式化变更数据"""
        changes = {}
        
        # 处理变更前数据
        if before_data:
            changes["before"] = before_data
            
        # 处理变更后数据
        if after_data:
            changes["after"] = after_data
            
        return changes 