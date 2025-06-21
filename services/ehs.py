"""
EHS 服务模块，提供EHS相关的业务逻辑服务
"""

from sqlalchemy.orm import Session
from models.ehs import Ehs
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class EhsService:
    """EHS服务类"""
    
    @staticmethod
    def get_all_ehs_records(db: Session) -> List[Ehs]:
        """
        获取所有EHS记录
        
        参数:
        - db: 数据库会话
        
        返回:
        - List[Ehs]: EHS记录列表
        """
        try:
            return db.query(Ehs).order_by(Ehs.id.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"获取所有EHS记录失败: {str(e)}")
            raise
    
    @staticmethod
    def get_ehs_by_id(db: Session, ehs_id: int) -> Optional[Ehs]:
        """
        通过ID获取EHS记录
        
        参数:
        - db: 数据库会话
        - ehs_id: EHS记录ID
        
        返回:
        - Optional[Ehs]: EHS记录对象，如果不存在返回None
        """
        try:
            return db.query(Ehs).filter(Ehs.id == ehs_id).first()
        except SQLAlchemyError as e:
            logger.error(f"通过ID获取EHS记录失败: {str(e)}")
            raise
