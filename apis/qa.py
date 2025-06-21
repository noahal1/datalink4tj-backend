from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime, date
import logging

from db.session import get_db
from models.qa import Qa as qa_model
from models.user import User
from core.security import get_current_user
from schemas.qa import QaCreate, QaResponse, QaUpdate, Qa as qa_schema
from services.activity_service import record_activity
from models.qa import Qad as qad_model, QaKpi as qa_kpi_model, MonthlyTotal
from schemas.qa import MonthlyTotalCreate, MonthlyTotalResponse
from schemas.qad import Qad as qad_schema, QadCreate, QadUpdate
from schemas.qa_kpi import QaKpi as qa_kpi_schema, QaKpiCreate, QaKpiUpdate, QaKpiBulkUpdate
from models.activity import Activity

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/qa",
    tags=["qa"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=qa_schema, status_code=status.HTTP_201_CREATED, summary="Create a new QA entry")
async def create_qa(qa: QaCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 创建QA记录
    db_qa = qa_model(**qa.dict())
    db.add(db_qa)
    db.commit()
    db.refresh(db_qa)   
    
    # 记录活动
    try:
        activity = record_activity(
            db=db,
            user=current_user,
            module="QA",
            action_type="CREATE",
            title="创建GP12&报废数据",
            action=f"创建了{qa.line}的GP12&报废数据",
            details=f"日期: {qa.year}-{qa.month}-{qa.day}, 生产线: {qa.line}, 值: {qa.value}",
            after_data=qa.dict(),
            target="/quality"
        )
        logger.info(f"数据变更记录成功: {activity.id} - {activity.title}")
    except Exception as e:
        logger.error(f"记录数据变更失败: {str(e)}")
    
    return db_qa

@router.get("/", response_model=List[qa_schema], summary="Get QA entries by month")
async def read_qas(month: Optional[str] = None, db: Session = Depends(get_db)):
    year = datetime.now().year
    if month is None:
        # 如果未提供月份，默认使用当前月份
        month = str(datetime.now().month)
    
    qas = db.query(qa_model).filter(
        qa_model.year == str(year),
        qa_model.month == month
    ).all()
    return qas

@router.put("/", summary="Update QA entries")
async def update_qas(qas: List[QaUpdate], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated_entries = []
    created_entries = []
    
    for qa in qas:
        db_qa = db.query(qa_model).filter(
            qa_model.day == qa.day,
            qa_model.month == qa.month,
            qa_model.year == qa.year,
            qa_model.line == qa.line,
            qa_model.scrapflag == qa.scrapflag
        ).first()
        
        if db_qa:
            # 保存更新前的数据
            before_data = {
                "id": db_qa.id,
                "day": db_qa.day,
                "month": db_qa.month,
                "year": db_qa.year,
                "line": db_qa.line,
                "value": db_qa.value,
                "scrapflag": db_qa.scrapflag
            }
            
            # 更新数据
            for key, value in qa.dict().items():
                setattr(db_qa, key, value)
                
            updated_entries.append({
                "before": before_data,
                "after": qa.dict()
            })
        else:
            # 创建新记录
            new_qa = qa_model(**qa.dict())
            db.add(new_qa)
            created_entries.append(qa.dict())
    
    db.commit()
    
    # 记录更新活动
    if updated_entries:
        record_activity(
            db=db,
            user=current_user,
            module="QA",
            action_type="UPDATE",
            title="更新质量数据",
            action=f"更新了{len(updated_entries)}条质量数据",
            details=f"月份: {qas[0].month}, 年份: {qas[0].year}",
            before_data=[entry["before"] for entry in updated_entries],
            after_data=[entry["after"] for entry in updated_entries],
            target="/quality"
        )
    
    # 记录创建活动
    if created_entries:
        record_activity(
            db=db,
            user=current_user,
            module="QA",
            action_type="CREATE",
            title="创建质量数据",
            action=f"创建了{len(created_entries)}条质量数据",
            details=f"月份: {qas[0].month}, 年份: {qas[0].year}",
            after_data=created_entries,
            target="/quality"
        )
    
    return {"message": "QA entries updated successfully"}

@router.delete("/{qa_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a QA entry by ID")
async def delete_qa(qa_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_qa = db.query(qa_model).filter(qa_model.id == qa_id).first()
    if not db_qa:
        raise HTTPException(status_code=404, detail="QA entry not found")
    
    # 保存删除前的数据
    before_data = {
        "id": db_qa.id,
        "day": db_qa.day,
        "month": db_qa.month,
        "year": db_qa.year,
        "line": db_qa.line,
        "value": db_qa.value,
        "scrapflag": db_qa.scrapflag
    }
    
    # 删除记录
    db.delete(db_qa)
    db.commit()
    
    # 记录活动
    record_activity(
        db=db,
        user=current_user,
        module="QA",
        action_type="DELETE",
        title="删除质量数据",
        action=f"删除了ID为{qa_id}的质量数据",
        details=f"日期: {before_data['year']}-{before_data['month']}-{before_data['day']}, 生产线: {before_data['line']}",
        before_data=before_data,
        target="/quality"
    )
    
    return {"message": "QA entry deleted successfully"}

# 以下是qad的相关端点

@router.post("/qad/", response_model=qad_schema, status_code=status.HTTP_201_CREATED, summary="Create a new QAD entry")
async def create_qad(qad: QadCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 创建QAD记录
    db_qad = qad_model(**qad.dict())
    db.add(db_qad)
    db.commit()
    db.refresh(db_qad)
    
    # 记录活动
    record_activity(
        db=db,
        user=current_user,
        module="QA",
        action_type="CREATE",
        title="创建质量杂项数据",
        action=f"创建了{qad.month}月的质量杂项数据",
        details=f"年份: {qad.year}, 月份: {qad.month}",
        after_data=qad.dict(),
        target="/qa_others"
    )
    
    return db_qad

@router.get("/qad/", response_model=List[qad_schema], summary="Get QAD entries by month")
async def read_qads(month: Optional[str] = None, db: Session = Depends(get_db)):
    year = datetime.now().year
    if month is None:
        # 如果未提供月份，默认使用当前月份
        month = str(datetime.now().month)
        
    qads = db.query(qad_model).filter(
        qad_model.year == str(year),
        qad_model.month == month
    ).all()
    return qads

@router.put("/qad/{qad_id}", response_model=qad_schema, summary="Update a QAD entry by ID")
async def update_qad(qad_id: int, qad: QadUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_qad = db.query(qad_model).filter(qad_model.id == qad_id).first()
    if not db_qad:
        raise HTTPException(status_code=404, detail="QAD entry not found")
    
    # 保存更新前的数据
    before_data = {
        "id": db_qad.id,
        "month": db_qad.month,
        "year": db_qad.year,
        "supplier_defect": db_qad.supplier_defect,
        "formal_amount": db_qad.formal_amount,
        "informal_amount": db_qad.informal_amount,
        "qc_ignore_amount": db_qad.qc_ignore_amount,
        "scrap_rate_c": db_qad.scrap_rate_c,
        "scrap_rate_m": db_qad.scrap_rate_m,
        "Ftt_tjm": db_qad.Ftt_tjm,
        "Ftt_tjc": db_qad.Ftt_tjc
    }
    
    # 更新数据
    for key, value in qad.dict().items():
        setattr(db_qad, key, value)
    
    db.commit()
    db.refresh(db_qad)
    
    # 记录活动
    record_activity(
        db=db,
        user=current_user,
        module="QA",
        action_type="UPDATE",
        title="更新质量杂项数据",
        action=f"更新了{db_qad.month}月的质量杂项数据",
        details=f"年份: {db_qad.year}, 月份: {db_qad.month}",
        before_data=before_data,
        after_data=qad.dict(),
        target="/qa_others"
    )
    
    return db_qad

@router.delete("/qad/{qad_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a QAD entry by ID")
async def delete_qad(qad_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_qad = db.query(qad_model).filter(qad_model.id == qad_id).first()
    if not db_qad:
        raise HTTPException(status_code=404, detail="QAD entry not found")
    
    # 保存删除前的数据
    before_data = {
        "id": db_qad.id,
        "month": db_qad.month,
        "year": db_qad.year,
        "supplier_defect": db_qad.supplier_defect,
        "formal_amount": db_qad.formal_amount,
        "informal_amount": db_qad.informal_amount,
        "qc_ignore_amount": db_qad.qc_ignore_amount,
        "scrap_rate_c": db_qad.scrap_rate_c,
        "scrap_rate_m": db_qad.scrap_rate_m,
        "Ftt_tjm": db_qad.Ftt_tjm,
        "Ftt_tjc": db_qad.Ftt_tjc
    }
    
    # 删除记录
    db.delete(db_qad)
    db.commit()
    
    # 记录活动
    record_activity(
        db=db,
        user=current_user,
        module="QA",
        action_type="DELETE",
        title="删除质量杂项数据",
        action=f"删除了ID为{qad_id}的质量杂项数据",
        details=f"年份: {before_data['year']}, 月份: {before_data['month']}",
        before_data=before_data,
        target="/qa_others"
    )
    
    return {"message": "QAD entry deleted successfully"}

@router.get("/test-activity-record/", summary="Test activity record feature")
async def test_activity_record(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    测试数据变更记录功能
    """
    try:
        # 创建一个测试QA记录
        test_qa = qa_model(
            day="1",
            month="1",
            year="2023",
            line="TEST",
            value="100",
            scrapflag=False
        )
        db.add(test_qa)
        db.commit()
        db.refresh(test_qa)
        
        # 记录创建活动
        create_activity = record_activity(
            db=db,
            user=current_user,
            module="QA",
            action_type="CREATE",
            title="测试 - 创建质量数据",
            action="创建了测试生产线的质量数据",
            details="测试数据变更记录功能",
            after_data={"day": "1", "month": "1", "year": "2023", "line": "TEST", "value": "100"},
            target="/quality"
        )
        
        # 更新测试记录
        before_data = {
            "id": test_qa.id,
            "day": test_qa.day,
            "month": test_qa.month,
            "year": test_qa.year,
            "line": test_qa.line,
            "value": test_qa.value
        }
        
        test_qa.value = "200"
        db.commit()
        
        # 记录更新活动
        update_activity = record_activity(
            db=db,
            user=current_user,
            module="QA",
            action_type="UPDATE",
            title="测试 - 更新质量数据",
            action="更新了测试生产线的质量数据",
            details="测试数据变更记录功能",
            before_data=before_data,
            after_data={"day": "1", "month": "1", "year": "2023", "line": "TEST", "value": "200"},
            target="/quality"
        )
        
        # 删除测试记录
        db.delete(test_qa)
        db.commit()
        
        # 记录删除活动
        delete_activity = record_activity(
            db=db,
            user=current_user,
            module="QA",
            action_type="DELETE",
            title="测试 - 删除质量数据",
            action="删除了测试生产线的质量数据",
            details="测试数据变更记录功能",
            before_data={"id": test_qa.id, "day": "1", "month": "1", "year": "2023", "line": "TEST", "value": "200"},
            target="/quality"
        )
        
        # 获取所有活动记录
        activities = db.query(Activity).order_by(Activity.created_at.desc()).limit(10).all()
        
        activity_list = []
        for activity in activities:
            activity_list.append(activity.to_dict())
        
        return {
            "message": "测试数据变更记录功能成功",
            "activities": activity_list
        }
    except Exception as e:
        logger.error(f"测试数据变更记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")

# KPI 数据相关端点
@router.get("/kpi/", response_model=List[qa_kpi_schema], summary="获取KPI数据")
async def get_kpi_data(
    month: Optional[int] = None, 
    year: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
        
    kpi_data = db.query(qa_kpi_model).filter(
        qa_kpi_model.year == year,
        qa_kpi_model.month == month
    ).all()
    return kpi_data

@router.post("/kpi/", response_model=List[qa_kpi_schema], status_code=status.HTTP_201_CREATED, summary="创建KPI数据")
async def create_kpi_data(kpi_data: QaKpiBulkUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    created_items = []
    
    # 先删除该月份的所有数据
    db.query(qa_kpi_model).filter(
        qa_kpi_model.year == kpi_data.year,
        qa_kpi_model.month == kpi_data.month
    ).delete()
    
    # 创建新数据
    for item in kpi_data.items:
        db_item = qa_kpi_model(
            month=kpi_data.month,
            year=kpi_data.year,
            area=item.area,
            description=item.description,
            new_factory=item.new_factory,
            old_factory=item.old_factory,
            total=item.total
        )
        db.add(db_item)
        created_items.append(db_item)
    
    db.commit()
    
    # 刷新所有项以获取ID
    for item in created_items:
        db.refresh(item)
    
    # 记录活动
    record_activity(
        db=db,
        user=current_user,
        module="QA",
        action_type="CREATE",
        title="创建质量KPI数据",
        action=f"创建/更新了{kpi_data.month}月的质量KPI数据",
        details=f"年份: {kpi_data.year}, 月份: {kpi_data.month}, 条目数: {len(kpi_data.items)}",
        after_data=[{
            "area": item.area,
            "description": item.description,
            "new_factory": item.new_factory,
            "old_factory": item.old_factory,
            "total": item.total
        } for item in kpi_data.items],
        target="/qa_others"
    )
    
    return created_items

@router.put("/kpi/", response_model=List[qa_kpi_schema], summary="更新KPI数据")
async def update_kpi_data(kpi_data: QaKpiBulkUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 获取原始数据用于比较
    original_items = db.query(qa_kpi_model).filter(
        qa_kpi_model.year == kpi_data.year,
        qa_kpi_model.month == kpi_data.month
    ).all()
    
    original_data = [{
        "id": item.id,
        "area": item.area,
        "description": item.description,
        "new_factory": item.new_factory,
        "old_factory": item.old_factory,
        "total": item.total
    } for item in original_items]
    
    # 删除现有数据
    db.query(qa_kpi_model).filter(
        qa_kpi_model.year == kpi_data.year,
        qa_kpi_model.month == kpi_data.month
    ).delete()
    
    # 创建新数据
    created_items = []
    for item in kpi_data.items:
        db_item = qa_kpi_model(
            month=kpi_data.month,
            year=kpi_data.year,
            area=item.area,
            description=item.description,
            new_factory=item.new_factory,
            old_factory=item.old_factory,
            total=item.total
        )
        db.add(db_item)
        created_items.append(db_item)
    
    db.commit()
    
    # 刷新所有项以获取ID
    for item in created_items:
        db.refresh(item)
    
    # 记录活动
    record_activity(
        db=db,
        user=current_user,
        module="QA",
        action_type="UPDATE",
        title="更新质量KPI数据",
        action=f"更新了{kpi_data.month}月的质量KPI数据",
        details=f"年份: {kpi_data.year}, 月份: {kpi_data.month}, 条目数: {len(kpi_data.items)}",
        before_data=original_data,
        after_data=[{
            "area": item.area,
            "description": item.description,
            "new_factory": item.new_factory,
            "old_factory": item.old_factory,
            "total": item.total
        } for item in kpi_data.items],
        target="/qa_others"
    )
    
    return created_items

@router.get("/monthly", response_model=List[MonthlyTotalResponse])
def get_monthly_totals(
    month: Optional[str] = None, 
    year: Optional[str] = None, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """获取指定月份的月度总数"""
    # 设置默认值
    if month is None:
        month = str(datetime.now().month)
    if year is None:
        year = str(datetime.now().year)
        
    monthly_totals = db.query(MonthlyTotal).filter(
        MonthlyTotal.month == month,
        MonthlyTotal.year == year
    ).all()
    return monthly_totals

@router.put("/monthly")
def update_monthly_totals(monthly_totals: List[MonthlyTotalCreate], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新月度总数"""
    try:
        # 获取原始数据用于比较
        if monthly_totals and len(monthly_totals) > 0:
            sample = monthly_totals[0]
            original_data = db.query(MonthlyTotal).filter(
                MonthlyTotal.month == sample.month,
                MonthlyTotal.year == sample.year
            ).all()
            
            before_data = [{
                "line": item.line,
                "month": item.month,
                "year": item.year,
                "amount": item.amount
            } for item in original_data]
        else:
            before_data = []
        
        for total_data in monthly_totals:
            # 查找是否已存在记录
            existing = db.query(MonthlyTotal).filter(
                MonthlyTotal.line == total_data.line,
                MonthlyTotal.month == total_data.month,
                MonthlyTotal.year == total_data.year
            ).first()
            
            if existing:
                # 更新现有记录
                existing.amount = total_data.amount
            else:
                # 创建新记录
                new_total = MonthlyTotal(
                    line=total_data.line,
                    month=total_data.month,
                    year=total_data.year,
                    amount=total_data.amount
                )
                db.add(new_total)
        
        db.commit()
        
        # 记录活动
        if monthly_totals and len(monthly_totals) > 0:
            sample = monthly_totals[0]
            record_activity(
                db=db,
                user=current_user,
                module="QA",
                action_type="UPDATE",
                title="更新月度产量数据",
                action=f"更新了{sample.month}月的月度产量数据",
                details=f"年份: {sample.year}, 月份: {sample.month}, 条目数: {len(monthly_totals)}",
                before_data=before_data,
                after_data=[{
                    "line": item.line,
                    "month": item.month,
                    "year": item.year,
                    "amount": item.amount
                } for item in monthly_totals],
                target="/quality"
            )
        
        return {"message": "Monthly amounts updated successfully"}
    except Exception as e:
        logger.error(f"更新月度产量数据失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新月度产量数据失败: {str(e)}"
        )