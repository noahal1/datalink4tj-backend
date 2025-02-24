from pydantic import BaseModel 
from schemas.department  import Department 
 
class UserBase(BaseModel):
    name: str 
 
class UserCreate(UserBase):
    password: str 
    department_id: int 
 
class UserUpdate(UserBase):
    department_id: int 
 
class User(UserBase):
    id: int 
    department: Department 
    password: str 
 
    class Config:
        from_attributes = True 