from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from db.session import get_db
from models.event import Event
from models.user import User
from schemas.event import EventCreate, Event as EventSchema
from apis.user import get_current_user
from services.activity_service import ActivityService

router = APIRouter()

@router.get("/events/", response_model=List[EventSchema])
def get_events(
    skip: int = 0,
    limit: int = 100,
    department: Optional[str] = None,
    upcoming: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取事件列表
    
    可以通过部门和是否即将到来进行筛选
    """
    query = db.query(Event)
    
    # 筛选条件
    if department:
        query = query.filter(Event.department == department)
    
    # 如果需要获取即将到来的事件
    if upcoming:
        today = datetime.now().date()
        query = query.filter(Event.start_time >= today)
    
    # 按开始时间排序
    query = query.order_by(Event.start_time)
    
    # 分页
    events = query.offset(skip).limit(limit).all()
    
    return events

@router.post("/events/", response_model=EventSchema)
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的事件
    """
    db_event = Event(
        name=event.name,
        department=event.department,
        start_time=event.start_time,
        end_time=event.end_time
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # 记录活动
    ActivityService.record_data_change(
        db=db,
        user=current_user,
        module="EVENT",
        action_type="CREATE",
        title="创建新事件",
        action=f"创建了事件: {event.name}",
        details=f"部门: {event.department}, 开始时间: {event.start_time}, 结束时间: {event.end_time}",
        after_data=event.dict(),
        target="/events"
    )
    
    return db_event

@router.get("/events/{event_id}", response_model=EventSchema)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定ID的事件
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event

@router.put("/events/{event_id}", response_model=EventSchema)
def update_event(
    event_id: int,
    event_update: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新指定ID的事件
    """
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # 保存更新前的数据
    before_data = {
        "id": db_event.id,
        "name": db_event.name,
        "department": db_event.department,
        "start_time": db_event.start_time.isoformat() if db_event.start_time else None,
        "end_time": db_event.end_time.isoformat() if db_event.end_time else None
    }
    
    # 更新事件信息
    db_event.name = event_update.name
    db_event.department = event_update.department
    db_event.start_time = event_update.start_time
    db_event.end_time = event_update.end_time
    
    db.commit()
    db.refresh(db_event)
    
    # 记录活动
    ActivityService.record_data_change(
        db=db,
        user=current_user,
        module="EVENT",
        action_type="UPDATE",
        title="更新事件",
        action=f"更新了事件: {db_event.name}",
        details=f"部门: {db_event.department}, 开始时间: {db_event.start_time}, 结束时间: {db_event.end_time}",
        before_data=before_data,
        after_data={
            "id": db_event.id,
            "name": db_event.name,
            "department": db_event.department,
            "start_time": db_event.start_time.isoformat() if db_event.start_time else None,
            "end_time": db_event.end_time.isoformat() if db_event.end_time else None
        },
        target="/events"
    )
    
    return db_event

@router.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除指定ID的事件
    """
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # 保存删除前的数据
    before_data = {
        "id": db_event.id,
        "name": db_event.name,
        "department": db_event.department,
        "start_time": db_event.start_time.isoformat() if db_event.start_time else None,
        "end_time": db_event.end_time.isoformat() if db_event.end_time else None
    }
    
    event_name = db_event.name
    event_department = db_event.department
    
    db.delete(db_event)
    db.commit()
    
    # 记录活动
    ActivityService.record_data_change(
        db=db,
        user=current_user,
        module="EVENT",
        action_type="DELETE",
        title="删除事件",
        action=f"删除了事件: {event_name}",
        details=f"部门: {event_department}, ID: {event_id}",
        before_data=before_data,
        target="/events"
    )
    
    return {"message": "Event deleted successfully"} 