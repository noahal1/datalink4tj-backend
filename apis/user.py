from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from schemas import user as user_schema
from services import user as user_service
from db.database import get_db

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post("/create", response_model=user_schema.User, summary="Create user")
async def create_user(
    user: user_schema.UserCreate,
    db: Session = Depends(get_db)
):
    return user_service.create_user_service(db, user)


@router.get("/{user_id}", response_model=user_schema.User, summary="Get user by ID")
async def read_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    db_user = user_service.get_user_service(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/", response_model=List[user_schema.User], summary="List users")
async def read_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    users = user_service.get_users_service(db, skip, limit)
    return users


@router.put("/{user_id}", response_model=user_schema.User, summary="Update user")
async def update_user(
    user_id: int,
    user_update: user_schema.UserUpdate,
    db: Session = Depends(get_db)
):
    db_user = user_service.update_user_service(db, user_id, user_update)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/{user_id}", summary="Delete user")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    success = user_service.delete_user_service(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}