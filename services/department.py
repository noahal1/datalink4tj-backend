from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from models.department import Department
from schemas.department import DepartmentCreate

# 设置日志
logger = logging.getLogger(__name__)

def create_department_service(db: Session, department: DepartmentCreate) -> Department:
    try:
        db_department = Department(name=department.name)
        db.add(db_department)
        db.commit()
        db.refresh(db_department)
        return db_department
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating department: {e}")
        raise

def get_department_service(db: Session, department_id: int) -> Department:
    try:
        return db.query(Department).filter(Department.id == department_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving department with id {department_id}: {e}")
        raise

def get_departments_service(db: Session, skip: int = 0, limit: int = 10) -> list[Department]:
    try:
        return db.query(Department).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving departments: {e}")
        raise