from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload
from models.user import User
from schemas.user import UserCreate
import hashlib

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(plain_password, hashed_password):
    md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
    return md5_hash == hashed_password


def create_user_service(db: Session, user: UserCreate) -> User:
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


# 更新用户
def update_user_service(db: Session, user_id: int, user_update):
    db_user = get_user_service(db, user_id)
    if not db_user:
        return None
    for attr, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, attr, value)
    db.commit()
    db.refresh(db_user)
    return db_user


# 删除用户
def delete_user_service(db: Session, user_id: int):
    db_user = get_user_service(db, user_id)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True