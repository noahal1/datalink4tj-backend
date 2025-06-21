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

def delete_department_service(db: Session, department_id: int) -> bool:
    """
    删除指定ID的部门
    
    参数:
    - db: 数据库会话
    - department_id: 要删除的部门ID
    
    返回:
    - 布尔值，表示操作是否成功
    
    异常:
    - SQLAlchemyError: 数据库操作错误
    """
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            logger.warning(f"尝试删除不存在的部门: {department_id}")
            return False
            
        db.delete(department)
        db.commit()
        logger.info(f"成功删除部门: {department_id} - {department.name}")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"删除部门时出错 (ID: {department_id}): {str(e)}")
        raise