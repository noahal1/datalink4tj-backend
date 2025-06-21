"""
数据库初始化脚本
在首次启动应用时创建所有必要的数据库表
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from models import Base
from db.session import DATABASE_URL

logger = logging.getLogger(__name__)

def init_db():
    """
    初始化数据库，创建所有表
    """
    try:
        logger.info("开始初始化数据库...")
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        logger.info("数据库初始化完成")
        return True
    except SQLAlchemyError as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    # 执行初始化
    init_db() 