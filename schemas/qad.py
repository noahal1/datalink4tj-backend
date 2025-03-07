from pydantic import BaseModel

class QadBase(BaseModel):
    month: int  
    year: int  
    supplier_defect: int  
    formal_amount: int  
    informal_amount: int  
    qc_ignore_amount: int  
    scrap_rate_c: float  
    scrap_rate_m: float  
    Ftt_tjm: float 
    Ftt_tjc: float  

class QadCreate(QadBase):
    pass

class QadUpdate(QadBase):
    pass

class Qad(QadBase):
    id: int

    class Config:
        orm_mode = True