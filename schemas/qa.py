from pydantic import BaseModel
from typing import Optional, List
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

class QaResponse(QaBase):
    id: int
    model_config = {"from_attributes": True}

class MonthlyTotalBase(BaseModel):
    line: str
    month: int
    year: int
    amount: int

class MonthlyTotalCreate(MonthlyTotalBase):
    pass

class MonthlyTotalResponse(MonthlyTotalBase):
    id: int
    model_config = {"from_attributes": True}

# 别名，用于向后兼容
QACreate = QaCreate
QAResponse = QaResponse
QAUpdate = QaUpdate
Qa = QaResponse