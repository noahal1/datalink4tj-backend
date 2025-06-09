from pydantic import BaseModel
from typing import List, Optional

class QaKpiBase(BaseModel):
    month: int
    year: int
    area: str
    description: str
    new_factory: float = 0
    old_factory: float = 0
    total: float = 0

class QaKpiCreate(QaKpiBase):
    pass

class QaKpiUpdate(QaKpiBase):
    pass

class QaKpi(QaKpiBase):
    id: int

    class Config:
        orm_mode = True

class QaKpiBulkUpdate(BaseModel):
    month: int
    year: int
    items: List[QaKpiUpdate] 