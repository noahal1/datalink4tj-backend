from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from models.database import get_db
from models.schema import DowntimeRecord, MaintenanceMetric, OEETrendResponse, MTTRMTBFTrendResponse, LineComparisonResponse, ChartQueryParams
from services import maint_service
from core.security import get_current_user
from core.logger import get_logger

router = APIRouter(
    prefix="/maint",
    tags=["maintenance"]
)

logger = get_logger("maint_api")

# 维修指标相关接口
@router.get("/metrics")
async def get_metrics(
    user_id: Optional[int] = None,
    equipment_type: Optional[str] = None,
    shift: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取维修指标数据列表
    """
    try:
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if equipment_type:
            filters["equipment_type"] = equipment_type
        if shift:
            filters["shift"] = shift
        if start_date and end_date:
            filters["date_range"] = (start_date, end_date)
            
        metrics = maint_service.get_metrics(db, filters)
        return metrics
    except Exception as e:
        logger.error(f"获取维修指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取维修指标失败: {str(e)}")

@router.post("/metrics")
async def create_metric(
    metric: MaintenanceMetric,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    创建新的维修指标
    """
    try:
        result = maint_service.create_metric(db, metric)
        return result
    except Exception as e:
        logger.error(f"创建维修指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建维修指标失败: {str(e)}")

@router.put("/metrics/{metric_id}")
async def update_metric(
    metric_id: int,
    metric: MaintenanceMetric,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    更新维修指标
    """
    try:
        result = maint_service.update_metric(db, metric_id, metric)
        if not result:
            raise HTTPException(status_code=404, detail=f"维修指标ID {metric_id} 不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新维修指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新维修指标失败: {str(e)}")

@router.delete("/metrics/{metric_id}")
async def delete_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    删除维修指标
    """
    try:
        success = maint_service.delete_metric(db, metric_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"维修指标ID {metric_id} 不存在")
        return {"message": "维修指标删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除维修指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除维修指标失败: {str(e)}")

# 停机单管理相关接口
@router.get("/downtime-records")
async def get_downtime_records(
    user_id: Optional[int] = None,
    line: Optional[str] = None,
    shift: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取停机单列表
    """
    try:
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if line:
            filters["line"] = line
        if shift:
            filters["shift"] = shift
        if status:
            filters["status"] = status
        if start_date and end_date:
            filters["date_range"] = (start_date, end_date)
            
        records = maint_service.get_downtime_records(db, filters)
        return records
    except Exception as e:
        logger.error(f"获取停机单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取停机单失败: {str(e)}")

@router.get("/downtime-records/{record_id}")
async def get_downtime_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取停机单详情
    """
    try:
        record = maint_service.get_downtime_record_by_id(db, record_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"停机单ID {record_id} 不存在")
        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取停机单详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取停机单详情失败: {str(e)}")

@router.post("/downtime-records")
async def create_downtime_record(
    record: DowntimeRecord,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    创建新的停机单
    """
    try:
        result = maint_service.create_downtime_record(db, record)
        return result
    except Exception as e:
        logger.error(f"创建停机单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建停机单失败: {str(e)}")

@router.put("/downtime-records/{record_id}")
async def update_downtime_record(
    record_id: int,
    record: DowntimeRecord,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    更新停机单
    """
    try:
        result = maint_service.update_downtime_record(db, record_id, record)
        if not result:
            raise HTTPException(status_code=404, detail=f"停机单ID {record_id} 不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新停机单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新停机单失败: {str(e)}")

@router.delete("/downtime-records/{record_id}")
async def delete_downtime_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    删除停机单
    """
    try:
        success = maint_service.delete_downtime_record(db, record_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"停机单ID {record_id} 不存在")
        return {"message": "停机单删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除停机单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除停机单失败: {str(e)}")

# 获取指标统计数据
@router.get("/metrics/stats")
async def get_metrics_stats(
    equipment_type: Optional[str] = None,
    shift: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取维修指标统计数据
    """
    try:
        filters = {}
        if equipment_type:
            filters["equipment_type"] = equipment_type
        if shift:
            filters["shift"] = shift
            
        # 默认查询最近30天
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
            
        filters["date_range"] = (start_date, end_date)
        
        stats = maint_service.get_metrics_stats(db, filters)
        return stats
    except Exception as e:
        logger.error(f"获取维修指标统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取维修指标统计失败: {str(e)}")

# 图表相关端点
@router.get("/charts/oee-trend", response_model=OEETrendResponse)
async def get_oee_trend(
    equipment_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取OEE趋势图表数据
    """
    try:
        # 默认查询最近30天
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
            
        filters = {"date_range": (start_date, end_date)}
        if equipment_type:
            filters["equipment_type"] = equipment_type
            
        # 使用服务方法获取趋势数据
        trend_data = maint_service.get_oee_trend_data(db, filters)
            
        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "equipment_type": equipment_type,
            "trend_data": trend_data
        }
    except Exception as e:
        logger.error(f"获取OEE趋势数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取OEE趋势数据失败: {str(e)}")

@router.get("/charts/mttr-mtbf-trend", response_model=MTTRMTBFTrendResponse)
async def get_mttr_mtbf_trend(
    equipment_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取MTTR和MTBF趋势图表数据
    """
    try:
        # 默认查询最近30天
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
            
        filters = {"date_range": (start_date, end_date)}
        if equipment_type:
            filters["equipment_type"] = equipment_type
            
        # 使用服务方法获取趋势数据
        trend_data = maint_service.get_mttr_mtbf_trend_data(db, filters)
            
        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "equipment_type": equipment_type,
            "trend_data": trend_data
        }
    except Exception as e:
        logger.error(f"获取MTTR/MTBF趋势数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取MTTR/MTBF趋势数据失败: {str(e)}")

@router.get("/charts/line-comparison", response_model=LineComparisonResponse)
async def get_line_comparison(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取不同生产线比较图表数据
    """
    try:
        # 默认查询最近30天
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
            
        filters = {"date_range": (start_date, end_date)}
        
        # 使用服务方法获取比较数据
        comparison_data = maint_service.get_line_comparison_data(db, filters)
            
        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "comparison_data": comparison_data
        }
    except Exception as e:
        logger.error(f"获取生产线比较数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取生产线比较数据失败: {str(e)}") 