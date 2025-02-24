from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from schemas import department as department_schema
from services import department as department_service
from db.database import get_db

router = APIRouter(
    prefix="/departments",
    tags=["departments"],
    responses={404: {"description": "Not found"}},
)

# 设置日志
logger = logging.getLogger(__name__)
# 创建部门
@router.post("/", response_model=department_schema.Department, summary="Create a new department")
def create_department(department: department_schema.DepartmentCreate, db: Session = Depends(get_db)):
    try:
        return department_service.create_department_service(db, department)
    except SQLAlchemyError as e:
        logger.error(f"Error creating department: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{department_id}", response_model=department_schema.Department, summary="Get a department by ID")
def read_department(department_id: int, db: Session = Depends(get_db)):
    try:
        db_department = department_service.get_department_service(db, department_id)
        if not db_department:
            raise HTTPException(status_code=404, detail="Department not found")
        return db_department
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving department with id {department_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/", response_model=list[department_schema.Department], summary="List all departments")
def read_departments(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    try:
        departments = department_service.get_departments_service(db, skip, limit)
        logger.debug(f"Retrieved departments: {departments}")
        return departments
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving departments: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")