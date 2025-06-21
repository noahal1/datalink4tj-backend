from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date

from db.session import get_db
from models.maint import MaintenanceWork, MaintDaily, MaintWeekly, MaintMetrics
from models.user import User
from core.security import get_current_user
from schemas.maint_work import (MaintDailyCreate, MaintDailyUpdate, MaintDailyResponse,
                                MaintWeeklyCreate, MaintWeeklyUpdate, MaintWeeklyResponse,
                                MaintMetricsCreate, MaintMetricsUpdate, MaintMetricsResponse)
from services.activity_service import record_activity, ActivityService
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 移除前缀，保持与主应用程序一致
router = APIRouter(
    tags=["维修工作"],
    responses={404: {"description": "Not found"}},
)

@router.get("/maint/daily", response_model=List[MaintDailyResponse], summary="获取所有日维护任务")
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

@router.get("/maint/daily/{task_id}", response_model=MaintDailyResponse, summary="获取单个日维护任务")
async def get_daily_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """旨在日历选取日期时显示具体工作"""
    query = db.query(MaintDaily)
    # 具体日期筛选
    if task_id:
        query = query.filter(MaintDaily.id == task_id)
    daily_tasks = query.order_by(MaintDaily.date).all()
    return MaintDailyResponse.model_validate_from_orm(daily_tasks[0])

@router.post("/maint/daily", response_model=MaintDailyResponse, summary="创建日维护任务")
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

@router.put("/maint/daily/{task_id}", response_model=MaintDailyResponse, summary="更新日维护任务")
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

@router.delete("/maint/daily/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除日维护任务")
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

@router.get("/maint/weekly", response_model=List[MaintWeeklyResponse], summary="获取所有周维护任务")
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

@router.get("/maint/weekly/{task_id}", response_model=MaintWeeklyResponse, summary="获取单个周任务")
async def get_weekly_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """根据ID获取特定的周任务"""
    task = db.query(MaintWeekly).filter(MaintWeekly.id == task_id).first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="周任务不存在"
        )
    return MaintWeeklyResponse.model_validate_from_orm(task)

@router.post("/maint/weekly", response_model=MaintWeeklyResponse, summary="创建周任务")
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

@router.put("/maint/weekly/{task_id}", response_model=MaintWeeklyResponse, summary="更新周任务")
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

@router.delete("/maint/weekly/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除周任务")
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

@router.post("/maint/issues", response_model=MaintWeeklyResponse, summary="创建问题记录")
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

@router.put("/maint/issues/{issue_id}", response_model=MaintWeeklyResponse, summary="更新问题记录")
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

@router.delete("/maint/issues/{issue_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除问题记录")
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

@router.get("/maint/issues", response_model=List[MaintWeeklyResponse], summary="获取所有问题记录")
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

@router.get("/maint/issues/{issue_id}", response_model=MaintWeeklyResponse, summary="获取单个问题记录")
async def get_issue(issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """根据ID获取特定的问题记录"""
    issue = db.query(MaintWeekly).filter(MaintWeekly.id == issue_id).first()
    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="问题记录不存在"
        )
    return MaintWeeklyResponse.model_validate_from_orm(issue)

# 维修数据指标相关API

@router.get("/maint/metrics", response_model=List[MaintMetricsResponse], summary="获取维修数据指标")
async def get_metrics(
    equipment_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取维修数据指标列表，可按设备类型、日期范围和用户ID筛选
    """
    query = db.query(MaintMetrics)
    
    # 应用筛选条件
    if equipment_type:
        query = query.filter(MaintMetrics.equipment_type == equipment_type)
    if start_date:
        query = query.filter(MaintMetrics.date >= start_date)
    if end_date:
        query = query.filter(MaintMetrics.date <= end_date)
    if user_id:
        query = query.filter(MaintMetrics.user_id == user_id)
    
    # 按日期降序排序
    metrics = query.order_by(MaintMetrics.date.desc()).all()
    return metrics

@router.get("/maint/metrics/{metric_id}", response_model=MaintMetricsResponse, summary="获取单个维修数据指标")
async def get_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个维修数据指标详情
    """
    metric = db.query(MaintMetrics).filter(MaintMetrics.id == metric_id).first()
    if metric is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="维修数据指标不存在"
        )
    return metric

@router.post("/maint/metrics", response_model=MaintMetricsResponse, summary="创建维修数据指标")
async def create_metric(
    metric: MaintMetricsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的维修数据指标记录，并自动计算OEE、MTTR、MTBF和设备可动率
    """
    # 创建基本数据
    db_metric = MaintMetrics(
        date=metric.date,
        user_id=metric.user_id,
        equipment_type=metric.equipment_type,
        downtime_count=metric.downtime_count,
        downtime_minutes=metric.downtime_minutes,
        parts_produced=metric.parts_produced
    )
    
    # 计算衍生指标
    # 假设每天工作时间为24小时（1440分钟）
    total_minutes = 1440
    
    # 计算设备可动率
    db_metric.availability = (total_minutes - db_metric.downtime_minutes) / total_minutes
    
    # 计算MTTR（平均修复时间）
    if db_metric.downtime_count > 0:
        db_metric.mttr = db_metric.downtime_minutes / db_metric.downtime_count
    else:
        db_metric.mttr = 0
    
    # 计算MTBF（平均故障间隔时间）
    if db_metric.downtime_count > 0:
        uptime_minutes = total_minutes - db_metric.downtime_minutes
        db_metric.mtbf = uptime_minutes / db_metric.downtime_count
    else:
        db_metric.mtbf = total_minutes  # 如果没有故障，则MTBF等于总时间
    
    # 简化的OEE计算（可用性 × 性能 × 质量）
    # 这里我们假设性能和质量都是100%，只考虑可用性
    db_metric.oee = db_metric.availability
    
    # 添加到数据库
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    
    # 记录活动
    try:
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="MAINT",
            action_type="CREATE",
            title="创建维修数据指标",
            action=f"创建了设备{metric.equipment_type}的维修数据指标",
            details=f"日期: {metric.date}, 停机次数: {metric.downtime_count}, 停机时间: {metric.downtime_minutes}分钟",
            after_data=metric.dict(),
            target="/maintenance"
        )
        logger.info(f"维修数据指标创建活动记录成功")
    except Exception as e:
        logger.error(f"记录维修数据指标创建活动失败: {str(e)}")
    
    return db_metric

@router.put("/maint/metrics/{metric_id}", response_model=MaintMetricsResponse, summary="更新维修数据指标")
async def update_metric(
    metric_id: int,
    metric: MaintMetricsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新维修数据指标，并重新计算OEE、MTTR、MTBF和设备可动率
    """
    # 查找记录
    db_metric = db.query(MaintMetrics).filter(MaintMetrics.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="维修数据指标不存在"
        )
    
    # 保存更新前的数据
    before_data = {
        "id": db_metric.id,
        "date": str(db_metric.date),
        "user_id": db_metric.user_id,
        "equipment_type": db_metric.equipment_type,
        "downtime_count": db_metric.downtime_count,
        "downtime_minutes": db_metric.downtime_minutes,
        "parts_produced": db_metric.parts_produced,
        "oee": db_metric.oee,
        "mttr": db_metric.mttr,
        "mtbf": db_metric.mtbf,
        "availability": db_metric.availability
    }
    
    # 更新字段
    update_data = metric.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_metric, key, value)
    
    # 重新计算衍生指标
    # 假设每天工作时间为24小时（1440分钟）
    total_minutes = 1440
    
    # 计算设备可动率
    db_metric.availability = (total_minutes - db_metric.downtime_minutes) / total_minutes
    
    # 计算MTTR（平均修复时间）
    if db_metric.downtime_count > 0:
        db_metric.mttr = db_metric.downtime_minutes / db_metric.downtime_count
    else:
        db_metric.mttr = 0
    
    # 计算MTBF（平均故障间隔时间）
    if db_metric.downtime_count > 0:
        uptime_minutes = total_minutes - db_metric.downtime_minutes
        db_metric.mtbf = uptime_minutes / db_metric.downtime_count
    else:
        db_metric.mtbf = total_minutes  # 如果没有故障，则MTBF等于总时间
    
    # 简化的OEE计算（可用性 × 性能 × 质量）
    # 这里我们假设性能和质量都是100%，只考虑可用性
    db_metric.oee = db_metric.availability
    
    db.commit()
    db.refresh(db_metric)
    
    # 记录活动
    try:
        after_data = {**before_data}
        after_data.update(update_data)
        
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="MAINT",
            action_type="UPDATE",
            title="更新维修数据指标",
            action=f"更新了设备{db_metric.equipment_type}的维修数据指标",
            details=f"指标ID: {metric_id}",
            before_data=before_data,
            after_data=after_data,
            target="/maintenance"
        )
        logger.info(f"维修数据指标更新活动记录成功")
    except Exception as e:
        logger.error(f"记录维修数据指标更新活动失败: {str(e)}")
    
    return db_metric

@router.delete("/maint/metrics/{metric_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除维修数据指标")
async def delete_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除维修数据指标
    """
    db_metric = db.query(MaintMetrics).filter(MaintMetrics.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="维修数据指标不存在"
        )
    
    # 保存删除前的数据
    before_data = {
        "id": db_metric.id,
        "date": str(db_metric.date),
        "user_id": db_metric.user_id,
        "equipment_type": db_metric.equipment_type,
        "downtime_count": db_metric.downtime_count,
        "downtime_minutes": db_metric.downtime_minutes,
        "parts_produced": db_metric.parts_produced
    }
    
    db.delete(db_metric)
    db.commit()
    
    # 记录活动
    try:
        ActivityService.record_data_change(
            db=db,
            user=current_user,
            module="MAINT",
            action_type="DELETE",
            title="删除维修数据指标",
            action=f"删除了设备{before_data['equipment_type']}的维修数据指标",
            details=f"指标ID: {metric_id}, 日期: {before_data['date']}",
            before_data=before_data,
            target="/maintenance"
        )
        logger.info(f"维修数据指标删除活动记录成功")
    except Exception as e:
        logger.error(f"记录维修数据指标删除活动失败: {str(e)}")
    
    return None