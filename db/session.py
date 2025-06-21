from db.database import SessionLocal
from core.config import settings

# 导出数据库URL供其他模块使用
DATABASE_URL = settings.DATABASE_URL

def get_db():
    """获取数据库会话函数的别名，保持兼容性"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
