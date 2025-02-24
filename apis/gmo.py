from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models import event as event_model
from schemas import event as event_schema

router = APIRouter(
    prefix="/events",
    tags=["Events"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[event_schema.Event])
async def get_events(db: Session = Depends(get_db)):
    events = db.query(event_model.Event).all()
    return events

@router.post("/", response_model=event_schema.Event, status_code=status.HTTP_201_CREATED)
async def create_event(event: event_schema.EventCreate, db: Session = Depends(get_db)):
    db_event = event_model.Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.put("/{event_id}", response_model=event_schema.Event)
async def update_event(event_id: int, event: event_schema.EventCreate, db: Session = Depends(get_db)):
    db_event = db.query(event_model.Event).filter(event_model.Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    for key, value in event.dict().items():
        setattr(db_event, key, value)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, db: Session = Depends(get_db)):
    db_event = db.query(event_model.Event).filter(event_model.Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(db_event)
    db.commit()
    return None