from pydantic import BaseModel
from datetime import date
from typing import Optional

class EventBase(BaseModel):
    name: str
    department: str
    start_time: date
    end_time: Optional[date] = None

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    model_config = {"from_attributes" : True }
        