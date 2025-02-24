from pydantic import BaseModel

class EhsBase(BaseModel):
    week: int
    year: int

class EhsUpdate(EhsBase):
    lwd: int

class Ehs(EhsBase):
    id: int
    lwd: int

    class Config:
        orm_mode = True