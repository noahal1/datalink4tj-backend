from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models import ehs as ehs_model
from schemas import ehs as ehs_schema
from datetime import datetime
from apis.user import get_current_user
from models.user import User
from services.activity_service import ActivityService
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ehs",
    tags=["EHS"],
    responses={404: {"description": "Not found"}},
)

# 获取所有EHS数据
@router.get("/", response_model=List[ehs_schema.Ehs])
async def get_ehs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    year = datetime.now().year
    ehs_data = db.query(ehs_model.Ehs).filter(
        ehs_model.Ehs.year == year,
    ).all()
    return ehs_data

# 获取LWD数据
@router.get("/lwd", response_model=List[ehs_schema.Ehs])
async def get_lwd_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    year = datetime.now().year
    ehs_data = db.query(ehs_model.Ehs).filter(
        ehs_model.Ehs.year == year,
    ).all()
    return ehs_data

# 更新LWD数据
@router.put("/lwd", summary="更新LWD数据")
async def update_lwd_data(ehs_entries: List[ehs_schema.EhsUpdate], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated_entries = []
    created_entries = []
    
    current_year = datetime.now().year
    
    for entry in ehs_entries:
        # 确保年份为当前年份
        entry_with_year = entry.dict()
        entry_with_year["year"] = current_year
        
        db_entry = db.query(ehs_model.Ehs).filter(
            ehs_model.Ehs.week == entry.week,
            ehs_model.Ehs.year == current_year
        ).first()
        
        if db_entry:
            # 保存更新前的数据
            before_data = {
                "id": db_entry.id,
                "week": db_entry.week,
                "year": db_entry.year,
                "lwd": db_entry.lwd
            }
            
            # 更新数据
            db_entry.lwd = entry.lwd
            
            updated_entries.append({
                "before": before_data,
                "after": entry_with_year
            })
        else:
            new_entry = ehs_model.Ehs(**entry_with_year)
            db.add(new_entry)
            created_entries.append(entry_with_year)
    
    db.commit()
    
    # 记录更新活动
    if updated_entries:
        try:
            ActivityService.record_data_change(
                db=db,
                user=current_user,
                module="EHS",
                action_type="UPDATE",
                title="更新LWD数据",
                action=f"更新了{len(updated_entries)}条LWD数据",
                details=f"年份: {current_year}",
                before_data=[entry["before"] for entry in updated_entries],
                after_data=[entry["after"] for entry in updated_entries],
                target="/ehs"
            )
            logger.info(f"LWD数据更新活动记录成功")
        except Exception as e:
            logger.error(f"记录LWD数据更新活动失败: {str(e)}")
    
    # 记录创建活动
    if created_entries:
        try:
            ActivityService.record_data_change(
                db=db,
                user=current_user,
                module="EHS",
                action_type="CREATE",
                title="创建LWD数据",
                action=f"创建了{len(created_entries)}条LWD数据",
                details=f"年份: {current_year}",
                after_data=created_entries,
                target="/ehs"
            )
            logger.info(f"LWD数据创建活动记录成功")
        except Exception as e:
            logger.error(f"记录LWD数据创建活动失败: {str(e)}")
    
    return {"message": "LWD数据更新成功"}

# 更新EHS数据
@router.put("/", summary="更新EHS数据")
async def update_ehs_entries(ehs_entries: List[ehs_schema.EhsUpdate], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated_entries = []
    created_entries = []
    
    for entry in ehs_entries:
        db_entry = db.query(ehs_model.Ehs).filter(
            ehs_model.Ehs.week == entry.week,
            ehs_model.Ehs.year == entry.year
        ).first()
        
        if db_entry:
            # 保存更新前的数据
            before_data = {
                "id": db_entry.id,
                "week": db_entry.week,
                "year": db_entry.year,
                "lwd": db_entry.lwd
            }
            
            # 更新数据
            db_entry.lwd = entry.lwd
            
            updated_entries.append({
                "before": before_data,
                "after": entry.dict()
            })
        else:
            new_entry = ehs_model.Ehs(**entry.dict())
            db.add(new_entry)
            created_entries.append(entry.dict())
    
    db.commit()
    
    # 记录更新活动
    if updated_entries:
        try:
            ActivityService.record_data_change(
                db=db,
                user=current_user,
                module="EHS",
                action_type="UPDATE",
                title="更新EHS数据",
                action=f"更新了{len(updated_entries)}条EHS数据",
                details=f"年份: {ehs_entries[0].year}",
                before_data=[entry["before"] for entry in updated_entries],
                after_data=[entry["after"] for entry in updated_entries],
                target="/ehs"
            )
            logger.info(f"EHS数据更新活动记录成功")
        except Exception as e:
            logger.error(f"记录EHS数据更新活动失败: {str(e)}")
    
    # 记录创建活动
    if created_entries:
        try:
            ActivityService.record_data_change(
                db=db,
                user=current_user,
                module="EHS",
                action_type="CREATE",
                title="创建EHS数据",
                action=f"创建了{len(created_entries)}条EHS数据",
                details=f"年份: {ehs_entries[0].year}",
                after_data=created_entries,
                target="/ehs"
            )
            logger.info(f"EHS数据创建活动记录成功")
        except Exception as e:
            logger.error(f"记录EHS数据创建活动失败: {str(e)}")
    
    return {"message": "EHS数据更新成功"}