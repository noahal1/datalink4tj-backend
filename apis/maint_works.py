from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from db.database import get_db
from models.maint import MaintDaily, MaintWeekly
from schemas.maint_work import MaintDailyCreate, MaintDailyUpdate, MaintDailyResponse
from schemas.maint_work import MaintWeeklyCreate, MaintWeeklyUpdate, MaintWeeklyResponse
from apis.user import get_current_user
from models.user import User
from services.activity_service import ActivityService
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
async def get_daily_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """旨在日历选取日期时显示具体工作"""
    query = db.query(MaintDaily)
    # 具体日期筛选
    if task_id:
        query = query.filter(MaintDaily.id == task_id)
    daily_tasks = query.order_by(MaintDaily.date).all()
    return MaintDailyResponse.model_validate_from_orm(daily_tasks[0])

@router.post("/daily", response_model=MaintDailyResponse, summary="创建日维护任务")
async def create_daily_task(task: MaintDailyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
    
    # 记录活动
    try:
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="MAINT",
            action_type="CREATE",
            title="创建日维护任务",
            action=f"创建了日维护任务: {task.title}",
            details=f"日期: {task.date}, 位置: {task.wheres}, 类型: {task.type}",
            after_data=task.dict(),
            target="/maintenance"
        )
        logger.info(f"日维护任务创建活动记录成功")
    except Exception as e:
        logger.error(f"记录日维护任务创建活动失败: {str(e)}")
    
    return MaintDailyResponse.model_validate_from_orm(db_task)

@router.put("/daily/{task_id}", response_model=MaintDailyResponse, summary="更新日维护任务")
async def update_daily_task(task_id: int, task: MaintDailyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新现有的日维护任务"""
    # 查找任务
    db_task = db.query(MaintDaily).filter(MaintDaily.id == task_id).first()
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="维护任务不存在"
        )
    
    # 保存更新前的数据
    before_data = {
        "id": db_task.id,
        "date": str(db_task.date),
        "user_id": db_task.user_id,
        "title": db_task.title,
        "wheres": db_task.wheres,
        "type": db_task.type,
        "content_daily": db_task.content_daily,
        "solved": db_task.solved_flag == 1
    }
    
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
    
    # 记录活动
    try:
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="MAINT",
            action_type="UPDATE",
            title="更新日维护任务",
            action=f"更新了日维护任务: {db_task.title}",
            details=f"任务ID: {task_id}",
            before_data=before_data,
            after_data={**before_data, **update_data},
            target="/maintenance"
        )
        logger.info(f"日维护任务更新活动记录成功")
    except Exception as e:
        logger.error(f"记录日维护任务更新活动失败: {str(e)}")
    
    return MaintDailyResponse.model_validate_from_orm(db_task)

@router.delete("/daily/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除日维护任务")
async def delete_daily_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除日维护任务"""
    db_task = db.query(MaintDaily).filter(MaintDaily.id == task_id).first()
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="维护任务不存在"
        )
    
    # 保存删除前的数据
    before_data = {
        "id": db_task.id,
        "date": str(db_task.date),
        "user_id": db_task.user_id,
        "title": db_task.title,
        "wheres": db_task.wheres,
        "type": db_task.type,
        "content_daily": db_task.content_daily,
        "solved": db_task.solved_flag == 1
    }
    
    db.delete(db_task)
    db.commit()
    
    # 记录活动
    try:
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="MAINT",
            action_type="DELETE",
            title="删除日维护任务",
            action=f"删除了日维护任务: {before_data['title']}",
            details=f"任务ID: {task_id}, 日期: {before_data['date']}",
            before_data=before_data,
            target="/maintenance"
        )
        logger.info(f"日维护任务删除活动记录成功")
    except Exception as e:
        logger.error(f"记录日维护任务删除活动失败: {str(e)}")
    
    return None

@router.get("/weekly", response_model=List[MaintWeeklyResponse], summary="获取所有周维护任务")
async def get_all_weekly_tasks(
    user_id: Optional[int] = None, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取维护周任务列表：
    - 可按用户ID筛选
    - 可按开始日期筛选
    - 可按解决状态筛选
    """
    query = db.query(MaintWeekly)
    # 应用筛选条件
    if user_id:
        query = query.filter(MaintWeekly.user_id == user_id)    
    # 按日期升序排序
    weekly_tasks = query.order_by(MaintWeekly.DateTime.asc()).all()
    return [MaintWeeklyResponse.model_validate_from_orm(task) for task in weekly_tasks]

@router.get("/weekly/{task_id}", response_model=MaintWeeklyResponse, summary="获取单个周任务")
async def get_weekly_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """根据ID获取特定的周任务"""
    task = db.query(MaintWeekly).filter(MaintWeekly.id == task_id).first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="周任务不存在"
        )
    return MaintWeeklyResponse.model_validate_from_orm(task)

@router.post("/weekly", response_model=MaintWeeklyResponse, summary="创建周任务")
async def create_weekly_task(task: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建新的周任务或问题记录"""
    try:
        # 直接从字典中获取字段
        db_task = MaintWeekly(
            DateTime=task.get("DateTime") or task.get("date_time"),
            user_id=task.get("user_id"),
            title=task.get("title"),
            wheres=task.get("wheres", "问题记录"),
            content=task.get("content"),
            degree=task.get("degree", "中等"),
            solved_flag=task.get("solved_flag", 0)
        )
        
        # 添加到数据库
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        # 记录活动
        try:
            ActivityService.record_data_change(
                db=db,
                user=current_user,
                module="MAINT",
                action_type="CREATE",
                title="创建周维护任务",
                action=f"创建了周维护任务: {db_task.title}",
                details=f"日期: {db_task.DateTime}, 位置: {db_task.wheres}, 优先级: {db_task.degree}",
                after_data=task,
                target="/maintenance"
            )
            logger.info(f"周维护任务创建活动记录成功")
        except Exception as e:
            logger.error(f"记录周维护任务创建活动失败: {str(e)}")
        
        return MaintWeeklyResponse.model_validate_from_orm(db_task)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建失败: {str(e)}"
        )

@router.put("/weekly/{task_id}", response_model=MaintWeeklyResponse, summary="更新周任务")
async def update_weekly_task(task_id: int, task: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新现有的周任务或问题记录"""
    # 查找任务
    db_task = db.query(MaintWeekly).filter(MaintWeekly.id == task_id).first()
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="周任务不存在"
        )
    
    try:
        # 保存更新前的数据
        before_data = {
            "id": db_task.id,
            "DateTime": str(db_task.DateTime) if db_task.DateTime else None,
            "user_id": db_task.user_id,
            "title": db_task.title,
            "wheres": db_task.wheres,
            "content": db_task.content,
            "degree": db_task.degree,
            "solved_flag": db_task.solved_flag
        }
        
        # 处理前端直接提交的字段
        if "DateTime" in task:
            db_task.DateTime = task["DateTime"]
        elif "date_time" in task:
            db_task.DateTime = task["date_time"]
            
        if "user_id" in task:
            db_task.user_id = task["user_id"]
            
        if "title" in task:
            db_task.title = task["title"]
            
        if "wheres" in task:
            db_task.wheres = task["wheres"]
            
        if "content" in task:
            db_task.content = task["content"]
            
        if "degree" in task:
            db_task.degree = task["degree"]
            
        # 处理状态字段
        if "solved_flag" in task:
            db_task.solved_flag = task["solved_flag"]
        
        db.commit()
        db.refresh(db_task)
        
        # 记录活动
        try:
            ActivityService.record_data_change(
                db=db,
                user=current_user,
                module="MAINT",
                action_type="UPDATE",
                title="更新周维护任务",
                action=f"更新了周维护任务: {db_task.title}",
                details=f"任务ID: {task_id}",
                before_data=before_data,
                after_data=task,
                target="/maintenance"
            )
            logger.info(f"周维护任务更新活动记录成功")
        except Exception as e:
            logger.error(f"记录周维护任务更新活动失败: {str(e)}")
        
        return MaintWeeklyResponse.model_validate_from_orm(db_task)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新失败: {str(e)}"
        )

@router.delete("/weekly/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除周任务")
async def delete_weekly_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除周任务"""
    db_task = db.query(MaintWeekly).filter(MaintWeekly.id == task_id).first()
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="周任务不存在"
        )
    
    # 保存删除前的数据
    before_data = {
        "id": db_task.id,
        "DateTime": str(db_task.DateTime) if db_task.DateTime else None,
        "user_id": db_task.user_id,
        "title": db_task.title,
        "wheres": db_task.wheres,
        "content": db_task.content,
        "degree": db_task.degree,
        "solved_flag": db_task.solved_flag
    }
    
    db.delete(db_task)
    db.commit()
    
    # 记录活动
    try:
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="MAINT",
            action_type="DELETE",
            title="删除周维护任务",
            action=f"删除了周维护任务: {before_data['title']}",
            details=f"任务ID: {task_id}",
            before_data=before_data,
            target="/maintenance"
        )
        logger.info(f"周维护任务删除活动记录成功")
    except Exception as e:
        logger.error(f"记录周维护任务删除活动失败: {str(e)}")
    
    return None

@router.post("/issues", response_model=MaintWeeklyResponse, summary="创建问题记录")
async def create_issue(task: MaintWeeklyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建新的问题记录"""
    try:
        db_task = MaintWeekly(
            DateTime=task.DateTime,
            user_id=task.user_id,
            title=task.title,
            wheres=task.wheres or "问题记录",
            content=task.content,
            degree=task.degree or "中等",
            solved_flag=1 if task.solved else 0
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        # 记录活动
        try:
            ActivityService.record_data_change(
                db=db,
                user=current_user,
                module="MAINT",
                action_type="CREATE",
                title="创建问题记录",
                action=f"创建了问题记录: {task.title}",
                details=f"日期: {task.DateTime}, 位置: {task.wheres}, 优先级: {task.degree}",
                after_data=task.dict(),
                target="/maintenance/issues"
            )
            logger.info(f"问题记录创建活动记录成功")
        except Exception as e:
            logger.error(f"记录问题记录创建活动失败: {str(e)}")
        
        return MaintWeeklyResponse.model_validate_from_orm(db_task)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建问题记录失败: {str(e)}"
        )

@router.put("/issues/{issue_id}", response_model=MaintWeeklyResponse, summary="更新问题记录")
async def update_issue(issue_id: int, task: MaintWeeklyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新现有的问题记录"""
    db_task = db.query(MaintWeekly).filter(MaintWeekly.id == issue_id).first()
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="问题记录不存在"
        )
    
    try:
        # 保存更新前的数据
        before_data = {
            "id": db_task.id,
            "DateTime": str(db_task.DateTime) if db_task.DateTime else None,
            "user_id": db_task.user_id,
            "title": db_task.title,
            "wheres": db_task.wheres,
            "content": db_task.content,
            "degree": db_task.degree,
            "solved": db_task.solved_flag == 1
        }
        
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
        
        # 记录活动
        try:
            ActivityService.record_data_change(
                db=db,
                user=current_user,
                module="MAINT",
                action_type="UPDATE",
                title="更新问题记录",
                action=f"更新了问题记录: {db_task.title}",
                details=f"问题ID: {issue_id}",
                before_data=before_data,
                after_data={**before_data, **update_data},
                target="/maintenance/issues"
            )
            logger.info(f"问题记录更新活动记录成功")
        except Exception as e:
            logger.error(f"记录问题记录更新活动失败: {str(e)}")
        
        return MaintWeeklyResponse.model_validate_from_orm(db_task)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新问题记录失败: {str(e)}"
        )

@router.delete("/issues/{issue_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除问题记录")
async def delete_issue(issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除问题记录"""
    db_task = db.query(MaintWeekly).filter(MaintWeekly.id == issue_id).first()
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="问题记录不存在"
        )
    
    # 保存删除前的数据
    before_data = {
        "id": db_task.id,
        "DateTime": str(db_task.DateTime) if db_task.DateTime else None,
        "user_id": db_task.user_id,
        "title": db_task.title,
        "wheres": db_task.wheres,
        "content": db_task.content,
        "degree": db_task.degree,
        "solved": db_task.solved_flag == 1
    }
    
    db.delete(db_task)
    db.commit()
    
    # 记录活动
    try:
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="MAINT",
            action_type="DELETE",
            title="删除问题记录",
            action=f"删除了问题记录: {before_data['title']}",
            details=f"问题ID: {issue_id}",
            before_data=before_data,
            target="/maintenance/issues"
        )
        logger.info(f"问题记录删除活动记录成功")
    except Exception as e:
        logger.error(f"记录问题记录删除活动失败: {str(e)}")
    
    return None

@router.get("/issues", response_model=List[MaintWeeklyResponse], summary="获取所有问题记录")
async def get_all_issues(
    user_id: Optional[int] = None,
    solved: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有问题记录：
    - 可按用户ID筛选
    - 可按解决状态筛选
    """
    query = db.query(MaintWeekly)
    # 应用筛选条件
    if user_id:
        query = query.filter(MaintWeekly.user_id == user_id)
    if solved is not None:
        solved_flag = 1 if solved else 0
        query = query.filter(MaintWeekly.solved_flag == solved_flag)
    
    # 按日期降序排序
    issues = query.order_by(MaintWeekly.DateTime.desc()).all()
    return [MaintWeeklyResponse.model_validate_from_orm(issue) for issue in issues]

@router.get("/issues/{issue_id}", response_model=MaintWeeklyResponse, summary="获取单个问题记录")
async def get_issue(issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """根据ID获取特定的问题记录"""
    issue = db.query(MaintWeekly).filter(MaintWeekly.id == issue_id).first()
    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="问题记录不存在"
        )
    return MaintWeeklyResponse.model_validate_from_orm(issue)