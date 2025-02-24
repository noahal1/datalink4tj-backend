from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models import qa as qa_model
from schemas import qa as qa_schema
from datetime import datetime

router = APIRouter(
    prefix="/qa",
    tags=["qa"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=qa_schema.Qa, status_code=status.HTTP_201_CREATED, summary="Create a new QA entry")
async def create_qa(qa: qa_schema.QaCreate, db: Session = Depends(get_db)):
    db_qa = qa_model.Qa(**qa.dict())
    db.add(db_qa)
    db.commit()
    db.refresh(db_qa)
    return db_qa

@router.get("/", response_model=List[qa_schema.Qa], summary="Get QA entries by month")
async def read_qas(month: str, db: Session = Depends(get_db)):
    year = datetime.now().year
    qas = db.query(qa_model.Qa).filter(
        qa_model.Qa.year == str(year),
        qa_model.Qa.month == month
    ).all()
    return qas

@router.put("/", summary="Update QA entries")
async def update_qas(qas: List[qa_schema.QaUpdate], db: Session = Depends(get_db)):
    for qa in qas:
        db_qa = db.query(qa_model.Qa).filter(
            qa_model.Qa.day == qa.day,
            qa_model.Qa.month == qa.month,
            qa_model.Qa.year == qa.year,
            qa_model.Qa.line == qa.line,
            qa_model.Qa.scrapflag == qa.scrapflag
        ).first()
        if db_qa:
            for key, value in qa.dict().items():
                setattr(db_qa, key, value)
        else:
            new_qa = qa_model.Qa(**qa.dict())
            db.add(new_qa)
    db.commit()
    return {"message": "QA entries updated successfully"}

@router.delete("/{qa_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a QA entry by ID")
async def delete_qa(qa_id: int, db: Session = Depends(get_db)):
    db_qa = db.query(qa_model.Qa).filter(qa_model.Qa.id == qa_id).first()
    if not db_qa:
        raise HTTPException(status_code=404, detail="QA entry not found")
    
    db.delete(db_qa)
    db.commit()
    return {"message": "QA entry deleted successfully"}