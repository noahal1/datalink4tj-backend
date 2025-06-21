# -*- coding: utf-8 -*-
# 重置admin密码脚本

import sys
import hashlib
from sqlalchemy.orm import Session
from db.session import get_db
from models.user import User, pwd_context

# 新密码
NEW_PASSWORD = "admin123"  # 您可以修改为您想要的密码

def main():
    print("开始重置admin用户密码...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 查找admin用户
        admin_user = db.query(User).filter(User.name == "admin").first()
        
        if admin_user:
            print(f"找到admin用户 (ID: {admin_user.id})")
            
            # 重置密码 - 使用User模型的set_password方法
            admin_user.set_password(NEW_PASSWORD)
            
            # 确保admin用户激活并拥有超级管理员权限
            admin_user.is_active = True
            admin_user.is_superuser = True
            
            # 更新数据库
            db.commit()
            print(f"admin用户密码已重置为: {NEW_PASSWORD}")
            print(f"admin用户已设置为超级管理员")
            print(f"操作完成! 管理员登录信息: 用户名=admin, 密码={NEW_PASSWORD}")
            
            # 打印用户信息
            print(f"用户ID: {admin_user.id}")
            print(f"用户名: {admin_user.name}")
            print(f"是否超级管理员: {admin_user.is_superuser}")
            print(f"是否激活: {admin_user.is_active}")
        else:
            print("未找到admin用户!")
        
    except Exception as e:
        db.rollback()
        print(f"重置密码时出错: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    main() 