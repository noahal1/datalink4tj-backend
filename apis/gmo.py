from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models import event as event_model
from schemas import event as event_schema
from apis.user import get_current_user
from models.user import User
from services.activity_service import ActivityService
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/events",
    tags=["Events"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[event_schema.Event])
async def get_events(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    events = db.query(event_model.Event).all()
    return events

@router.post("/", response_model=event_schema.Event, status_code=status.HTTP_201_CREATED)
async def create_event(event: event_schema.EventCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_event = event_model.Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # 记录活动
    try:
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="GMO",
            action_type="CREATE",
            title="创建事件",
            action=f"创建了事件: {event.name}",
            details=f"事件时间: {event.start_time} 至 {event.end_time}",
            after_data=event.dict(),
            target="/events"
        )
        logger.info(f"事件创建活动记录成功")
    except Exception as e:
        logger.error(f"记录事件创建活动失败: {str(e)}")
    
    return db_event

@router.put("/{event_id}", response_model=event_schema.Event)
async def update_event(event_id: int, event: event_schema.EventCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_event = db.query(event_model.Event).filter(event_model.Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # 保存更新前的数据
    before_data = {
        "id": db_event.id,
        "name": db_event.name,
        "department": db_event.department,
        "start_time": str(db_event.start_time) if db_event.start_time else None,
        "end_time": str(db_event.end_time) if db_event.end_time else None
    }
    
    # 更新事件
    for key, value in event.dict().items():
        setattr(db_event, key, value)
    
    db.commit()
    db.refresh(db_event)
    
    # 记录活动
    try:
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="GMO",
            action_type="UPDATE",
            title="更新事件",
            action=f"更新了事件: {event.name}",
            details=f"事件ID: {event_id}",
            before_data=before_data,
            after_data=event.dict(),
            target="/events"
        )
        logger.info(f"事件更新活动记录成功")
    except Exception as e:
        logger.error(f"记录事件更新活动失败: {str(e)}")
    
    return db_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_event = db.query(event_model.Event).filter(event_model.Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # 保存删除前的数据
    before_data = {
        "id": db_event.id,
        "name": db_event.name,
        "department": db_event.department,
        "start_time": str(db_event.start_time) if db_event.start_time else None,
        "end_time": str(db_event.end_time) if db_event.end_time else None
    }
    
    # 删除事件
    db.delete(db_event)
    db.commit()
    
    # 记录活动
    try:
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="GMO",
            action_type="DELETE",
            title="删除事件",
            action=f"删除了事件: {before_data['name']}",
            details=f"事件ID: {event_id}",
            before_data=before_data,
            target="/events"
        )
        logger.info(f"事件删除活动记录成功")
    except Exception as e:
        logger.error(f"记录事件删除活动失败: {str(e)}")
    
    return None