from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from db.session import get_db
from models.activity import Activity
from models.user import User
from schemas.activity import ActivityCreate, ActivityResponse, DataChangePayload
from apis.user import get_current_user

router = APIRouter()

@router.get("/activities/", response_model=List[ActivityResponse])
def get_activities(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    department: Optional[str] = None,
    type: Optional[str] = None,
    days: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取活动记录列表
    
    可以通过用户ID、部门、类型和时间范围进行筛选
    """
    query = db.query(Activity)
    
    # 筛选条件
    if user_id:
        query = query.filter(Activity.user_id == user_id)
    if department:
        query = query.filter(Activity.department == department)
    if type:
        query = query.filter(Activity.type == type)
    if days:
        date_from = datetime.now() - timedelta(days=days)
        query = query.filter(Activity.created_at >= date_from)
    
    # 排序：最新的在前面
    query = query.order_by(Activity.created_at.desc())
    
    # 分页
    activities = query.offset(skip).limit(limit).all()
    
    # 转换为响应格式
    return [activity.to_dict() for activity in activities]

@router.post("/activities/", response_model=ActivityResponse)
def create_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的活动记录
    """
    # 如果没有提供用户信息，则使用当前用户
    if not activity.user_id and current_user:
        activity.user_id = current_user.id
    if not activity.user_name and current_user:
        activity.user_name = current_user.name
    if not activity.department and current_user and current_user.department:
        activity.department = current_user.department.name
    
    # 创建活动记录
    db_activity = Activity(
        title=activity.title,
        action=activity.action,
        details=activity.details,
        type=activity.type,
        icon=activity.icon,
        color=activity.color,
        target=activity.target,
        user_id=activity.user_id,
        user_name=activity.user_name,
        department=activity.department,
        changes_before=activity.changes_before,
        changes_after=activity.changes_after
    )
    
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    
    return db_activity.to_dict()

@router.post("/activities/data-change/", response_model=ActivityResponse)
def record_data_change(
    payload: DataChangePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    记录数据变更活动
    """
    # 设置图标和颜色
    icon = "mdi-file-document-edit"
    color = "primary"
    
    # 根据操作类型设置图标和颜色
    if payload.type == "CREATE":
        icon = "mdi-plus-circle"
        color = "success"
    elif payload.type == "UPDATE":
        icon = "mdi-pencil"
        color = "primary"
    elif payload.type == "DELETE":
        icon = "mdi-delete"
        color = "error"
    elif payload.type == "UPLOAD":
        icon = "mdi-cloud-upload"
        color = "info"
    elif payload.type == "EXPORT":
        icon = "mdi-download"
        color = "secondary"
    
    # 构建标题和描述
    title = payload.title or f"{current_user.name}在{payload.module}模块进行了操作"
    action = payload.description or f"{payload.type}操作"
    details = str(payload.details) if payload.details else None
    
    # 创建活动记录
    db_activity = Activity(
        title=title,
        action=action,
        details=details,
        type=f"{payload.module.upper()}_{payload.type}",
        icon=icon,
        color=color,
        target=f"/{payload.module.lower()}",
        user_id=current_user.id,
        user_name=current_user.name,
        department=current_user.department.name if current_user.department else None,
        changes_before=payload.before,
        changes_after=payload.after
    )
    
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    
    return db_activity.to_dict()

@router.get("/activities/{activity_id}", response_model=ActivityResponse)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定ID的活动记录
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    return activity.to_dict() 