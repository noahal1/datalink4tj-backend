from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload
from models.user import User
from schemas.user import UserCreate
import jwt
import hashlib
from typing import Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "key4magnatj"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # 设置token过期时间


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_password_hash(password):
    # 使用 MD5 进行哈希
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(plain_password, hashed_password):
    # 验证 MD5 哈希
    md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
    return md5_hash == hashed_password

def delete_user_service(db: Session, user_id: int):
    db_user = get_user_service(db, user_id)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True

def create_user_service(db: Session, user: UserCreate) -> User:
    # 检查用户名是否已经存在
    existing_user = db.query(User).filter(User.name == user.name).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    # 获取 MD5 哈希后的密码
    hashed_password = get_password_hash(user.password)
    db_user = User(name=user.name, password=hashed_password, department_id=user.department_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# 获取用户
def get_user_service(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()


# 获取用户列表
def get_users_service(db: Session, skip: int = 0, limit: int = 10) -> list[User]:
    return db.query(User).options(joinedload(User.department)).offset(skip).limit(limit).all()