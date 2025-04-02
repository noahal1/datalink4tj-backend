from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from db.database import get_db
from models.maint import MaintDaily, MaintWeekly
from schemas.maint_work import MaintDailyCreate, MaintDailyUpdate, MaintDailyResponse
from schemas.maint_work import MaintWeeklyCreate, MaintWeeklyUpdate, MaintWeeklyResponse

router = APIRouter(
    prefix="/maint",
    tags=["维修工作"],
    responses={404: {"description": "Not found"}},
)

@router.get("/daily", response_model=List[MaintDailyResponse], summary="获取所有日维护任务")
async def get_all_daily_tasks(
    user_id: Optional[int] = None, 
    start_date: Optional[date] = None,
    solved: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    获取维护日任务列表，旨在日维护任务未完成任务显示在本周维修计划内
    - 按用户ID筛选、开始之后未完成的本周任务接口
    """
    query = db.query(MaintDaily)
    # 应用筛选条件
    if user_id:
        query = query.filter(MaintDaily.user_id == user_id)
    if start_date:
        query = query.filter(MaintDaily.date >= start_date)
    if solved is not None:
        solved_flag = 1 if solved else 0
        query = query.filter(MaintDaily.solved_flag == solved_flag)
    
    # 按日期升序排序
    daily_tasks = query.order_by(MaintDaily.date.asc()).all()
    return [MaintDailyResponse.model_validate_from_orm(task) for task in daily_tasks]

@router.get("/daily/{task_id}", response_model=MaintDailyResponse, summary="获取单个日维护任务")
async def get_daily_task(task_id: int, db: Session = Depends(get_db)):
    """旨在日历选取日期时显示具体工作"""
    query = db.query(MaintDaily)
    # 具体日期筛选
    if task_id:
        query = query.filter(MaintDaily.id == task_id)
    daily_tasks = query.order_by(MaintDaily.date).all()
    return MaintDailyResponse.model_validate_from_orm(daily_tasks[0])

@router.post("/daily", response_model=MaintDailyResponse, summary="创建日维护任务")
async def create_daily_task(task:MaintDailyCreate, db: Session = Depends(get_db)):
    """创建新的日维护任务"""
    db_task = MaintDaily(
        date=task.date,
        user_id=task.user_id,
        title=task.title,
        wheres=task.wheres,
        type=task.type,
        content_daily=task.content_daily,
        solved_flag=1 if task.solved else 0
    )
    
    # 添加到数据库
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return MaintDailyResponse.model_validate_from_orm(db_task)

@router.put("/daily/{task_id}", response_model=MaintDailyResponse, summary="更新日维护任务")
async def update_daily_task(task_id: int, task: MaintDailyUpdate, db: Session = Depends(get_db)):
    """更新现有的日维护任务"""
    # 查找任务
    db_task = db.query(MaintDaily).filter(MaintDaily.id == task_id).first()
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="维护任务不存在"
        )
    
    # 更新字段
    update_data = task.dict(exclude_unset=True)
    
    # 特殊处理solved字段，需要转换为solved_flag
    if "solved" in update_data:
        update_data["solved_flag"] = 1 if update_data.pop("solved") else 0
    
    # 应用更新
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return MaintDailyResponse.model_validate_from_orm(db_task)

@router.delete("/daily/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除日维护任务")
async def delete_daily_task(task_id: int, db: Session = Depends(get_db)):
    """删除日维护任务"""
    db_task = db.query(MaintDaily).filter(MaintDaily.id == task_id).first()
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="维护任务不存在"
        )
    
    db.delete(db_task)
    db.commit()
    return None


@router.get("/weekly/{task_id}", response_model=MaintWeeklyResponse, summary="获取单个周任务")
async def get_weekly_task(task_id: int, db: Session = Depends(get_db)):
    """根据ID获取特定的周任务"""
    task = db.query(MaintWeekly).filter(MaintWeekly.id == task_id).first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="周任务不存在"
        )
    return MaintDailyResponse.model_validate_from_orm(task)

@router.post("/weekly", response_model=MaintWeeklyResponse, summary="创建周任务")
async def create_weekly_task(task: MaintWeeklyCreate, db: Session = Depends(get_db)):
    """创建新的周任务"""
    # 创建数据库对象
    db_task = MaintWeekly(
        DateTime=task.date_time,
        user_id=task.user_id,
        title=task.title,
        wheres=task.wheres,
        content=task.content,
        degree=task.degree,
        solved_flag=1 if task.solved else 0
    )
    
    # 添加到数据库
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return MaintWeeklyResponse.model_validate_from_orm(db_task)

@router.put("/weekly/{task_id}", response_model=MaintWeeklyResponse, summary="更新周任务")
async def update_weekly_task(task_id: int, task: MaintWeeklyUpdate, db: Session = Depends(get_db)):
    """更新现有的周任务"""
    # 查找任务
    db_task = db.query(MaintWeekly).filter(MaintWeekly.id == task_id).first()
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="周任务不存在"
        )
    
    # 更新字段
    update_data = task.dict(exclude_unset=True)
    
    # 特殊处理字段映射
    if "date_time" in update_data:
        update_data["DateTime"] = update_data.pop("date_time")
    
    # 特殊处理solved字段，需要转换为solved_flag
    if "solved" in update_data:
        update_data["solved_flag"] = 1 if update_data.pop("solved") else 0
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return MaintWeeklyResponse.model_validate_from_orm(db_task)

@router.delete("/weekly/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除周任务")
async def delete_weekly_task(task_id: int, db: Session = Depends(get_db)):
    """删除周任务"""
    db_task = db.query(MaintWeekly).filter(MaintWeekly.id == task_id).first()
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="周任务不存在"
        )
    
    db.delete(db_task)
    db.commit()
    return None