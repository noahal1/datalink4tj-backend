from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class QaBase(BaseModel):
    line: str
    day: str
    month: str
    year: str = str(datetime.now().year)
    value: str
    scrapflag: bool = False

class QaCreate(QaBase):
    pass

class QaUpdate(QaBase):
    pass

class Qa(QaBase):
    id: int

    class Config:
        orm_mode = True