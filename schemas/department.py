from pydantic import BaseModel
from typing import Optional

class DepartmentBase(BaseModel):
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None

class DepartmentResponse(DepartmentBase):
    id: int
    description: Optional[str] = None
    model_config = {"from_attributes": True}

# 兼容原有代码，保留Department类
class Department(DepartmentResponse):
    pass