from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from schemas import department as department_schema
from services import department as department_service
from db.database import get_db
from core.security import get_current_user  # 导入认证依赖
from models.user import User  # 导入用户模型
from apis.helpers import permission_required, record_activity, handle_exceptions, compose

# 修改前缀，移除多余的前缀设置
router = APIRouter(
    tags=["departments"],
    responses={404: {"description": "Not found"}},
)

# 设置日志
logger = logging.getLogger(__name__)
# 创建部门
@router.post("/departments/", response_model=department_schema.Department, summary="Create a new department")
def create_department(
    department: department_schema.DepartmentCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # 添加认证依赖
):
    try:
        return department_service.create_department_service(db, department)
    except SQLAlchemyError as e:
        logger.error(f"Error creating department: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/departments/{department_id}", response_model=department_schema.Department, summary="Get a department by ID")
def read_department(
    department_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # 添加认证依赖
):
    try:
        db_department = department_service.get_department_service(db, department_id)
        if not db_department:
            raise HTTPException(status_code=404, detail="Department not found")
        return db_department
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving department with id {department_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/departments/", response_model=list[department_schema.Department], summary="List all departments")
def read_departments(
    skip: int = 0, 
    limit: int = 10, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # 添加认证依赖
):
    try:
        departments = department_service.get_departments_service(db, skip, limit)
        logger.debug(f"Retrieved departments: {departments}")
        return departments
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving departments: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/departments/{department_id}", response_model=dict, summary="删除部门")
@compose(
    permission_required("DEPARTMENT", "ADMIN"),
    record_activity("DEPARTMENT", "DELETE", "删除部门 ID: {department_id}"),
    handle_exceptions("删除部门失败")
)
async def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除指定ID的部门
    
    - **department_id**: 要删除的部门ID
    
    返回:
    - 成功删除的确认信息
    """
    # 检查部门是否存在
    db_department = department_service.get_department_service(db, department_id)
    if not db_department:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    # 检查部门是否有关联用户
    if db_department.users and len(db_department.users) > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"无法删除：部门有{len(db_department.users)}个关联用户"
        )
    
    # 删除部门
    department_service.delete_department_service(db, department_id)
    
    return {"message": f"部门 '{db_department.name}' 已成功删除", "id": department_id}