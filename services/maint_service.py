from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import date, datetime, timedelta

from models.database import MaintenanceMetric, DowntimeRecord
from core.logger import get_logger

logger = get_logger("maint_service")

# 维修指标相关服务
def get_metrics(db: Session, filters: Dict = None) -> List[Dict]:
    """
    根据过滤条件获取维修指标列表
    
    参数:
    - db: 数据库会话
    - filters: 过滤条件
    
    返回:
    - List[Dict]: 维修指标列表
    """
    try:
        query = db.query(MaintenanceMetric)
        
        # 应用过滤条件
        if filters:
            if "user_id" in filters:
                query = query.filter(MaintenanceMetric.user_id == filters["user_id"])
            
            if "equipment_type" in filters:
                query = query.filter(MaintenanceMetric.equipment_type == filters["equipment_type"])
            
            if "shift" in filters:
                query = query.filter(MaintenanceMetric.shift == filters["shift"])
            
            if "date_range" in filters:
                start_date, end_date = filters["date_range"]
                query = query.filter(
                    MaintenanceMetric.date >= start_date,
                    MaintenanceMetric.date <= end_date
                )
        
        # 获取结果
        metrics = query.order_by(MaintenanceMetric.date.desc()).all()
        
        # 转换为字典列表
        result = []
        for metric in metrics:
            # 计算设备可动率
            total_minutes = 1440  # 24小时 = 1440分钟
            availability = (total_minutes - metric.downtime_minutes) / total_minutes
            
            # 计算设备综合效率 (OEE)
            # 这里简化计算，只考虑可用性
            oee = availability
            
            result.append({
                "id": metric.id,
                "equipment_type": metric.equipment_type,
                "shift": metric.shift,
                "date": metric.date.strftime("%Y-%m-%d") if metric.date else None,
                "downtime_count": metric.downtime_count,
                "downtime_minutes": metric.downtime_minutes,
                "parts_produced": metric.parts_produced,
                "availability": availability,
                "oee": oee,
                "created_at": metric.created_at.strftime("%Y-%m-%d %H:%M:%S") if metric.created_at else None,
                "updated_at": metric.updated_at.strftime("%Y-%m-%d %H:%M:%S") if metric.updated_at else None,
                "user_id": metric.user_id
            })
        
        return result
    except Exception as e:
        logger.error(f"获取维修指标列表失败: {str(e)}")
        raise

def get_metric_by_id(db: Session, metric_id: int) -> Optional[Dict]:
    """
    根据ID获取维修指标
    
    参数:
    - db: 数据库会话
    - metric_id: 维修指标ID
    
    返回:
    - Optional[Dict]: 维修指标
    """
    try:
        metric = db.query(MaintenanceMetric).filter(MaintenanceMetric.id == metric_id).first()
        
        if not metric:
            return None
        
        # 计算设备可动率
        total_minutes = 1440  # 24小时 = 1440分钟
        availability = (total_minutes - metric.downtime_minutes) / total_minutes
        
        # 计算设备综合效率 (OEE)
        oee = availability
        
        return {
            "id": metric.id,
            "equipment_type": metric.equipment_type,
            "shift": metric.shift,
            "date": metric.date.strftime("%Y-%m-%d") if metric.date else None,
            "downtime_count": metric.downtime_count,
            "downtime_minutes": metric.downtime_minutes,
            "parts_produced": metric.parts_produced,
            "availability": availability,
            "oee": oee,
            "created_at": metric.created_at.strftime("%Y-%m-%d %H:%M:%S") if metric.created_at else None,
            "updated_at": metric.updated_at.strftime("%Y-%m-%d %H:%M:%S") if metric.updated_at else None,
            "user_id": metric.user_id
        }
    except Exception as e:
        logger.error(f"获取维修指标失败: {str(e)}")
        raise

def create_metric(db: Session, metric_data: Dict) -> Dict:
    """
    创建新的维修指标
    
    参数:
    - db: 数据库会话
    - metric_data: 维修指标数据
    
    返回:
    - Dict: 创建的维修指标
    """
    try:
        # 创建新的维修指标
        metric = MaintenanceMetric(
            equipment_type=metric_data.equipment_type,
            shift=metric_data.shift,
            date=metric_data.date,
            downtime_count=metric_data.downtime_count,
            downtime_minutes=metric_data.downtime_minutes,
            parts_produced=metric_data.parts_produced,
            user_id=metric_data.user_id
        )
        
        # 保存到数据库
        db.add(metric)
        db.commit()
        db.refresh(metric)
        
        # 返回创建的维修指标
        return get_metric_by_id(db, metric.id)
    except Exception as e:
        db.rollback()
        logger.error(f"创建维修指标失败: {str(e)}")
        raise

def update_metric(db: Session, metric_id: int, metric_data: Dict) -> Optional[Dict]:
    """
    更新维修指标
    
    参数:
    - db: 数据库会话
    - metric_id: 维修指标ID
    - metric_data: 更新的维修指标数据
    
    返回:
    - Optional[Dict]: 更新后的维修指标
    """
    try:
        # 查询维修指标
        metric = db.query(MaintenanceMetric).filter(MaintenanceMetric.id == metric_id).first()
        
        if not metric:
            return None
        
        # 更新维修指标
        metric.equipment_type = metric_data.equipment_type
        metric.shift = metric_data.shift
        metric.date = metric_data.date
        metric.downtime_count = metric_data.downtime_count
        metric.downtime_minutes = metric_data.downtime_minutes
        metric.parts_produced = metric_data.parts_produced
        metric.updated_at = datetime.now()
        
        # 保存到数据库
        db.commit()
        db.refresh(metric)
        
        # 返回更新后的维修指标
        return get_metric_by_id(db, metric.id)
    except Exception as e:
        db.rollback()
        logger.error(f"更新维修指标失败: {str(e)}")
        raise

def delete_metric(db: Session, metric_id: int) -> bool:
    """
    删除维修指标
    
    参数:
    - db: 数据库会话
    - metric_id: 维修指标ID
    
    返回:
    - bool: 是否删除成功
    """
    try:
        # 查询维修指标
        metric = db.query(MaintenanceMetric).filter(MaintenanceMetric.id == metric_id).first()
        
        if not metric:
            return False
        
        # 删除维修指标
        db.delete(metric)
        db.commit()
        
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"删除维修指标失败: {str(e)}")
        raise

def get_metrics_stats(db: Session, filters: Dict = None) -> Dict:
    """
    获取维修指标统计数据
    
    参数:
    - db: 数据库会话
    - filters: 过滤条件
    
    返回:
    - Dict: 统计数据
    """
    try:
        query = db.query(MaintenanceMetric)
        
        # 应用过滤条件
        if filters:
            if "equipment_type" in filters:
                query = query.filter(MaintenanceMetric.equipment_type == filters["equipment_type"])
            
            if "shift" in filters:
                query = query.filter(MaintenanceMetric.shift == filters["shift"])
            
            if "date_range" in filters:
                start_date, end_date = filters["date_range"]
                query = query.filter(
                    MaintenanceMetric.date >= start_date,
                    MaintenanceMetric.date <= end_date
                )
        
        # 获取结果
        metrics = query.all()
        
        # 计算统计数据
        total_downtime_minutes = sum(metric.downtime_minutes for metric in metrics)
        total_downtime_count = sum(metric.downtime_count for metric in metrics)
        total_days = len(set(metric.date for metric in metrics))
        total_work_minutes = total_days * 1440  # 假设每天工作24小时
        
        # 计算MTTR（平均修复时间）
        mttr = total_downtime_minutes / total_downtime_count if total_downtime_count > 0 else 0
        
        # 计算MTBF（平均故障间隔时间）
        mtbf = (total_work_minutes - total_downtime_minutes) / total_downtime_count if total_downtime_count > 0 else total_work_minutes
        
        # 计算设备可动率
        availability = (total_work_minutes - total_downtime_minutes) / total_work_minutes if total_work_minutes > 0 else 1
        
        # 计算OEE（设备综合效率）
        oee = availability  # 简化计算，只考虑可用性
        
        # 按设备类型分组统计
        equipment_stats = {}
        for metric in metrics:
            equipment_type = metric.equipment_type
            if equipment_type not in equipment_stats:
                equipment_stats[equipment_type] = {
                    "downtime_minutes": 0,
                    "downtime_count": 0,
                    "days": set()
                }
            
            equipment_stats[equipment_type]["downtime_minutes"] += metric.downtime_minutes
            equipment_stats[equipment_type]["downtime_count"] += metric.downtime_count
            equipment_stats[equipment_type]["days"].add(metric.date)
        
        # 计算每种设备的统计数据
        equipment_metrics = {}
        for equipment_type, stats in equipment_stats.items():
            days_count = len(stats["days"])
            work_minutes = days_count * 1440
            
            eq_mttr = stats["downtime_minutes"] / stats["downtime_count"] if stats["downtime_count"] > 0 else 0
            eq_mtbf = (work_minutes - stats["downtime_minutes"]) / stats["downtime_count"] if stats["downtime_count"] > 0 else work_minutes
            eq_availability = (work_minutes - stats["downtime_minutes"]) / work_minutes if work_minutes > 0 else 1
            eq_oee = eq_availability
            
            equipment_metrics[equipment_type] = {
                "mttr": eq_mttr,
                "mtbf": eq_mtbf,
                "availability": eq_availability,
                "oee": eq_oee,
                "downtime_minutes": stats["downtime_minutes"],
                "downtime_count": stats["downtime_count"]
            }
        
        return {
            "mttr": mttr,
            "mtbf": mtbf,
            "availability": availability,
            "oee": oee,
            "total_downtime_minutes": total_downtime_minutes,
            "total_downtime_count": total_downtime_count,
            "equipment_metrics": equipment_metrics
        }
    except Exception as e:
        logger.error(f"获取维修指标统计数据失败: {str(e)}")
        raise

# 停机单相关服务
def get_downtime_records(db: Session, filters: Dict = None) -> List[Dict]:
    """
    根据过滤条件获取停机单列表
    
    参数:
    - db: 数据库会话
    - filters: 过滤条件
    
    返回:
    - List[Dict]: 停机单列表
    """
    try:
        query = db.query(DowntimeRecord)
        
        # 应用过滤条件
        if filters:
            if "user_id" in filters:
                query = query.filter(DowntimeRecord.user_id == filters["user_id"])
            
            if "line" in filters:
                query = query.filter(DowntimeRecord.line == filters["line"])
            
            if "shift" in filters:
                query = query.filter(DowntimeRecord.shift == filters["shift"])
            
            if "status" in filters:
                query = query.filter(DowntimeRecord.status == filters["status"])
            
            if "date_range" in filters:
                start_date, end_date = filters["date_range"]
                query = query.filter(
                    DowntimeRecord.date >= start_date,
                    DowntimeRecord.date <= end_date
                )
        
        # 获取结果
        records = query.order_by(DowntimeRecord.date.desc()).all()
        
        # 转换为字典列表
        result = []
        for record in records:
            result.append({
                "id": record.id,
                "line": record.line,
                "shift": record.shift,
                "date": record.date.strftime("%Y-%m-%d") if record.date else None,
                "status": record.status,
                "downtime_minutes": record.downtime_minutes,
                "equipment_name": record.equipment_name,
                "fault_description": record.fault_description,
                "resolution": record.resolution,
                "reporter_name": record.reporter_name,
                "maintainer_name": record.maintainer_name,
                "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S") if record.created_at else None,
                "updated_at": record.updated_at.strftime("%Y-%m-%d %H:%M:%S") if record.updated_at else None,
                "user_id": record.user_id
            })
        
        return result
    except Exception as e:
        logger.error(f"获取停机单列表失败: {str(e)}")
        raise

def get_downtime_record_by_id(db: Session, record_id: int) -> Optional[Dict]:
    """
    根据ID获取停机单
    
    参数:
    - db: 数据库会话
    - record_id: 停机单ID
    
    返回:
    - Optional[Dict]: 停机单
    """
    try:
        record = db.query(DowntimeRecord).filter(DowntimeRecord.id == record_id).first()
        
        if not record:
            return None
        
        return {
            "id": record.id,
            "line": record.line,
            "shift": record.shift,
            "date": record.date.strftime("%Y-%m-%d") if record.date else None,
            "status": record.status,
            "downtime_minutes": record.downtime_minutes,
            "equipment_name": record.equipment_name,
            "fault_description": record.fault_description,
            "resolution": record.resolution,
            "reporter_name": record.reporter_name,
            "maintainer_name": record.maintainer_name,
            "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S") if record.created_at else None,
            "updated_at": record.updated_at.strftime("%Y-%m-%d %H:%M:%S") if record.updated_at else None,
            "user_id": record.user_id
        }
    except Exception as e:
        logger.error(f"获取停机单失败: {str(e)}")
        raise

def create_downtime_record(db: Session, record_data: Dict) -> Dict:
    """
    创建新的停机单
    
    参数:
    - db: 数据库会话
    - record_data: 停机单数据
    
    返回:
    - Dict: 创建的停机单
    """
    try:
        # 创建新的停机单
        record = DowntimeRecord(
            line=record_data.line,
            shift=record_data.shift,
            date=record_data.date,
            status=record_data.status,
            downtime_minutes=record_data.downtime_minutes,
            equipment_name=record_data.equipment_name,
            fault_description=record_data.fault_description,
            resolution=record_data.resolution,
            reporter_name=record_data.reporter_name,
            maintainer_name=record_data.maintainer_name,
            user_id=record_data.user_id
        )
        
        # 保存到数据库
        db.add(record)
        db.commit()
        db.refresh(record)
        
        # 返回创建的停机单
        return get_downtime_record_by_id(db, record.id)
    except Exception as e:
        db.rollback()
        logger.error(f"创建停机单失败: {str(e)}")
        raise

def update_downtime_record(db: Session, record_id: int, record_data: Dict) -> Optional[Dict]:
    """
    更新停机单
    
    参数:
    - db: 数据库会话
    - record_id: 停机单ID
    - record_data: 更新的停机单数据
    
    返回:
    - Optional[Dict]: 更新后的停机单
    """
    try:
        # 查询停机单
        record = db.query(DowntimeRecord).filter(DowntimeRecord.id == record_id).first()
        
        if not record:
            return None
        
        # 更新停机单
        record.line = record_data.line
        record.shift = record_data.shift
        record.date = record_data.date
        record.status = record_data.status
        record.downtime_minutes = record_data.downtime_minutes
        record.equipment_name = record_data.equipment_name
        record.fault_description = record_data.fault_description
        record.resolution = record_data.resolution
        record.reporter_name = record_data.reporter_name
        record.maintainer_name = record_data.maintainer_name
        record.updated_at = datetime.now()
        
        # 保存到数据库
        db.commit()
        db.refresh(record)
        
        # 返回更新后的停机单
        return get_downtime_record_by_id(db, record.id)
    except Exception as e:
        db.rollback()
        logger.error(f"更新停机单失败: {str(e)}")
        raise

def delete_downtime_record(db: Session, record_id: int) -> bool:
    """
    删除停机单
    
    参数:
    - db: 数据库会话
    - record_id: 停机单ID
    
    返回:
    - bool: 是否删除成功
    """
    try:
        # 查询停机单
        record = db.query(DowntimeRecord).filter(DowntimeRecord.id == record_id).first()
        
        if not record:
            return False
        
        # 删除停机单
        db.delete(record)
        db.commit()
        
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"删除停机单失败: {str(e)}")
        raise

# 图表数据相关服务
def get_oee_trend_data(db: Session, filters: Dict = None) -> List[Dict]:
    """
    获取OEE趋势数据
    
    参数:
    - db: 数据库会话
    - filters: 过滤条件，包含日期范围和可选的设备类型
    
    返回:
    - List[Dict]: 包含日期和OEE的列表
    """
    try:
        metrics = get_metrics(db, filters)
        
        # 按日期分组并计算每天的OEE
        daily_oee = {}
        for metric in metrics:
            metric_date = datetime.strptime(metric["date"], "%Y-%m-%d").date()
            
            if metric_date not in daily_oee:
                daily_oee[metric_date] = {
                    "total_downtime": 0,
                    "count": 0
                }
                
            daily_oee[metric_date]["total_downtime"] += metric["downtime_minutes"]
            daily_oee[metric_date]["count"] += 1
        
        # 计算每天的OEE
        result = []
        for day, data in sorted(daily_oee.items()):
            # 简化计算，只考虑可用性作为OEE
            total_minutes = 1440  # 24小时 = 1440分钟
            availability = (total_minutes - data["total_downtime"]) / total_minutes
            oee = availability
            
            result.append({
                "date": day.strftime("%Y-%m-%d"),
                "oee": oee
            })
            
        return result
    except Exception as e:
        logger.error(f"获取OEE趋势数据失败: {str(e)}")
        raise

def get_mttr_mtbf_trend_data(db: Session, filters: Dict = None) -> List[Dict]:
    """
    获取MTTR和MTBF趋势数据
    
    参数:
    - db: 数据库会话
    - filters: 过滤条件，包含日期范围和可选的设备类型
    
    返回:
    - List[Dict]: 包含日期、MTTR和MTBF的列表
    """
    try:
        metrics = get_metrics(db, filters)
        
        # 按日期分组并计算每天的MTTR和MTBF
        daily_metrics = {}
        for metric in metrics:
            metric_date = datetime.strptime(metric["date"], "%Y-%m-%d").date()
            
            if metric_date not in daily_metrics:
                daily_metrics[metric_date] = {
                    "total_downtime": 0,
                    "downtime_count": 0,
                }
                
            daily_metrics[metric_date]["total_downtime"] += metric["downtime_minutes"]
            daily_metrics[metric_date]["downtime_count"] += metric["downtime_count"]
        
        # 计算每天的MTTR和MTBF
        result = []
        for day, data in sorted(daily_metrics.items()):
            # 计算MTTR（平均修复时间）
            mttr = data["total_downtime"] / data["downtime_count"] if data["downtime_count"] > 0 else 0
            
            # 计算MTBF（平均故障间隔时间）
            total_minutes = 1440  # 24小时 = 1440分钟
            mtbf = (total_minutes - data["total_downtime"]) / data["downtime_count"] if data["downtime_count"] > 0 else total_minutes
            
            result.append({
                "date": day.strftime("%Y-%m-%d"),
                "mttr": mttr,
                "mtbf": mtbf
            })
            
        return result
    except Exception as e:
        logger.error(f"获取MTTR/MTBF趋势数据失败: {str(e)}")
        raise

def get_line_comparison_data(db: Session, filters: Dict = None) -> List[Dict]:
    """
    获取生产线比较数据
    
    参数:
    - db: 数据库会话
    - filters: 过滤条件，包含日期范围
    
    返回:
    - List[Dict]: 包含各生产线关键指标的列表
    """
    try:
        # 获取所有设备类型的指标数据
        metrics = get_metrics(db, filters)
        
        # 计算日期范围内的总天数
        start_date, end_date = filters.get("date_range", (date.today() - timedelta(days=30), date.today()))
        days_count = (end_date - start_date).days + 1  # 包含起始日期
        total_minutes = days_count * 1440  # 总分钟数
        
        # 按设备类型分组并统计
        equipment_metrics = {}
        for metric in metrics:
            eq_type = metric["equipment_type"]
            
            if eq_type not in equipment_metrics:
                equipment_metrics[eq_type] = {
                    "total_downtime": 0,
                    "downtime_count": 0,
                    "parts_produced": 0
                }
                
            equipment_metrics[eq_type]["total_downtime"] += metric["downtime_minutes"]
            equipment_metrics[eq_type]["downtime_count"] += metric["downtime_count"]
            equipment_metrics[eq_type]["parts_produced"] += metric["parts_produced"]
        
        # 计算每种设备类型的关键指标
        result = []
        for eq_type, data in equipment_metrics.items():
            # 计算设备可用率
            availability = (total_minutes - data["total_downtime"]) / total_minutes
            
            # 计算OEE（简化为可用率）
            oee = availability
            
            # 计算MTTR
            mttr = data["total_downtime"] / data["downtime_count"] if data["downtime_count"] > 0 else 0
            
            # 计算MTBF
            mtbf = (total_minutes - data["total_downtime"]) / data["downtime_count"] if data["downtime_count"] > 0 else total_minutes
            
            result.append({
                "equipment_type": eq_type,
                "downtime_minutes": data["total_downtime"],
                "downtime_count": data["downtime_count"],
                "parts_produced": data["parts_produced"],
                "availability": availability,
                "oee": oee,
                "mttr": mttr,
                "mtbf": mtbf
            })
            
        return result
    except Exception as e:
        logger.error(f"获取生产线比较数据失败: {str(e)}")
        raise 