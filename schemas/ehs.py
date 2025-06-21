from pydantic import BaseModel
from typing import Optional

class EhsBase(BaseModel):
    week: int
    year: int

class EhsCreate(EhsBase):
    lwd: int

class EhsUpdate(EhsBase):
    lwd: int

class EhsResponse(EhsBase):
    id: int
    lwd: int
    model_config = {"from_attributes": True}

# 兼容原有代码，保留Ehs类
class Ehs(EhsResponse):
    pass