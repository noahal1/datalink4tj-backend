import os
from dotenv import load_dotenv
load_dotenv() 
#生产环境
#SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://tjm:magna123@10.227.122.217:3306/tj") 
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://noah:727127zb@noahall.chat:3306/tj")   