from fastapi import APIRouter, Depends, HTTPException, status, Security 
from sqlalchemy.orm  import Session 
from typing import List, Optional 
from schemas import user as user_schema 
from services import user as user_service 
from db.database  import get_db 
from fastapi.security  import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from datetime import timedelta 
from fastapi.responses  import JSONResponse 
from fastapi.encoders  import jsonable_encoder 
import jwt
 
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)
 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
 
# 权限依赖项 
async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = user_service.decode_token(token) 
        username: str = payload.get("sub") 
        if username is None:
            raise credentials_exception 
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception 
    
    user = db.query(user_service.User).filter(user_service.User.name  == username).first()
    if user is None:
        raise credentials_exception 
    return user 
 
@router.post("/token",  summary="Login and get token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(user_service.User).filter(user_service.User.name  == form_data.username).first() 
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user_service.verify_password(form_data.password,  user.password): 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=user_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = user_service.create_access_token( 
        data={"sub": user.name},  expires_delta=access_token_expires 
    )
    
    return JSONResponse(
        content=jsonable_encoder({"access_token": access_token, "token_type": "bearer", "department": user.department.name }),
        status_code=status.HTTP_200_OK 
    )
 
@router.post("/create",  response_model=user_schema.User, summary="Create user")
async def create_user(
    user: user_schema.UserCreate,
    db: Session = Depends(get_db)):
    return user_service.create_user_service(db,  user)
 
@router.get("/{user_id}",  response_model=user_schema.User, summary="Get user by ID")
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    if current_user.id  != user_id and not current_user.is_admin: 
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this user."
        )
    
    db_user = user_service.get_user_service(db,  user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user 
 
@router.get("/",  response_model=List[user_schema.User], summary="List users")
async def read_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    users = user_service.get_users_service(db,  skip, limit)
    return users 
 
@router.put("/{user_id}",  response_model=user_schema.User, summary="Update user")
async def update_user(
    user_id: int,
    user_update: user_schema.UserUpdate,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    if current_user.id  != user_id and not current_user.is_admin: 
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this user."
        )
    
    db_user = user_service.update_user_service(db,  user_id, user_update)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user 
 
@router.delete("/{user_id}",  summary="Delete user")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Security(get_current_user)
):
    if current_user.id  == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself."
        )
    
    success = user_service.delete_user_service(db,  user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}