import os
from dotenv import load_dotenv
load_dotenv() 

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:magna123@10.227.122.217:3306/tj") 