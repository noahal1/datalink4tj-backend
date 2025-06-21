from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings
import logging

# 设置数据库连接池
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 设置日志
logger = logging.getLogger(__name__)

def get_db():
    """获取数据库会话函数"""
    db = SessionLocal()
    logger.debug("创建新的数据库会话")
    try:
        yield db
    finally:
        logger.debug("关闭数据库会话")
        db.close()