from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.qa import Qa as qa_model,Qad as qad_model
from schemas.qa import Qa as qa_schema, QaCreate, QaUpdate
from schemas.qad import Qad as qad_schema, QadCreate, QadUpdate
from datetime import datetime

router = APIRouter(
    prefix="/qa",
    tags=["qa"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=qa_schema, status_code=status.HTTP_201_CREATED, summary="Create a new QA entry")
async def create_qa(qa: QaCreate, db: Session = Depends(get_db)):
    db_qa = qa_model(**qa.dict())
    db.add(db_qa)
    db.commit()
    db.refresh(db_qa)
    return db_qa

@router.get("/", response_model=List[qa_schema], summary="Get QA entries by month")
async def read_qas(month: str, db: Session = Depends(get_db)):
    year = datetime.now().year
    qas = db.query(qa_model).filter(
        qa_model.year == str(year),
        qa_model.month == month
    ).all()
    return qas

@router.put("/", summary="Update QA entries")
async def update_qas(qas: List[QaUpdate], db: Session = Depends(get_db)):
    for qa in qas:
        db_qa = db.query(qa_model).filter(
            qa_model.day == qa.day,
            qa_model.month == qa.month,
            qa_model.year == qa.year,
            qa_model.line == qa.line,
            qa_model.scrapflag == qa.scrapflag
        ).first()
        if db_qa:
            for key, value in qa.dict().items():
                setattr(db_qa, key, value)
        else:
            new_qa = qa_model(**qa.dict())
            db.add(new_qa)
    db.commit()
    return {"message": "QA entries updated successfully"}

@router.delete("/{qa_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a QA entry by ID")
async def delete_qa(qa_id: int, db: Session = Depends(get_db)):
    db_qa = db.query(qa_model).filter(qa_model.id == qa_id).first()
    if not db_qa:
        raise HTTPException(status_code=404, detail="QA entry not found")
    
    db.delete(db_qa)
    db.commit()
    return {"message": "QA entry deleted successfully"}

# 以下是qad的相关端点

@router.post("/qad/", response_model=qad_schema, status_code=status.HTTP_201_CREATED, summary="Create a new QAD entry")
async def create_qad(qad: QadCreate, db: Session = Depends(get_db)):
    db_qad = qad_model(**qad.dict())
    db.add(db_qad)
    db.commit()
    db.refresh(db_qad)
    return db_qad

@router.get("/qad/", response_model=List[qad_schema], summary="Get QAD entries by month")
async def read_qads(month: str, db: Session = Depends(get_db)):
    year = datetime.now().year
    qads = db.query(qad_model).filter(
        qad_model.year == str(year),
        qad_model.month == month
    ).all()
    return qads

@router.put("/qad/{qad_id}", response_model=qad_schema, summary="Update a QAD entry by ID")
async def update_qad(qad_id: int, qad: QadUpdate, db: Session = Depends(get_db)):
    db_qad = db.query(qad_model).filter(qad_model.id == qad_id).first()
    if not db_qad:
        raise HTTPException(status_code=404, detail="QAD entry not found")
    
    for key, value in qad.dict().items():
        setattr(db_qad, key, value)
    
    db.commit()
    db.refresh(db_qad)
    return db_qad

@router.delete("/qad/{qad_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a QAD entry by ID")
async def delete_qad(qad_id: int, db: Session = Depends(get_db)):
    db_qad = db.query(qad_model).filter(qad_model.id == qad_id).first()
    if not db_qad:
        raise HTTPException(status_code=404, detail="QAD entry not found")
    
    db.delete(db_qad)
    db.commit()
    return {"message": "QAD entry deleted successfully"}