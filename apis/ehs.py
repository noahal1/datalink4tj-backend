from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models import ehs as ehs_model
from schemas import ehs as ehs_schema
from datetime import datetime

router = APIRouter(
    prefix="/ehs",
    tags=["EHS"],
    responses={404: {"description": "Not found"}},
)

# 获取所有EHS数据
@router.get("/", response_model=List[ehs_schema.Ehs])
async def get_ehs(db: Session = Depends(get_db)):
    year = datetime.now().year
    ehs_data = db.query(ehs_model.Ehs).filter(
        ehs_model.Ehs.year == year,
    ).all()
    return ehs_data

# 更新EHS数据
@router.put("/", summary="更新EHS数据")
async def update_ehs_entries(ehs_entries: List[ehs_schema.EhsUpdate], db: Session = Depends(get_db)):
    for entry in ehs_entries:
        db_entry = db.query(ehs_model.Ehs).filter(
            ehs_model.Ehs.week == entry.week,
            ehs_model.Ehs.year == entry.year
        ).first()
        if db_entry:
            db_entry.lwd = entry.lwd
        else:
            new_entry = ehs_model.Ehs(**entry.dict())
            db.add(new_entry)
    db.commit()
    return {"message": "EHS数据更新成功"}