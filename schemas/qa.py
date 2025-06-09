from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class QABase(BaseModel):
    line: str
    day: str
    month: str
    year: str = str(datetime.now().year)
    value: str
    scrapflag: bool = False

class QACreate(QABase):
    pass

class QAResponse(QABase):
    id: int

    class Config:
        orm_mode = True

class QaUpdate(QABase):
    pass

class Qa(QABase):
    id: int

    class Config:
        orm_mode = True

class MonthlyTotalBase(BaseModel):
    line: str
    month: int
    year: int
    amount: int

class MonthlyTotalCreate(MonthlyTotalBase):
    pass

class MonthlyTotalResponse(MonthlyTotalBase):
    id: int

    class Config:
        orm_mode = True

class QaCreate(BaseModel):
    line: str
    day: str
    month: str
    year: str
    value: str
    scrapflag: bool