from pydantic import BaseModel
from typing import Optional

class QaBase(BaseModel):
    line: str
    day: str
    month: str
    year: str
    value: str
    scrapflag: bool

class QaCreate(QaBase):
    pass

class QaUpdate(QaBase):
    pass

class Qa(QaBase):
    id: int

    class Config:
        orm_mode = True