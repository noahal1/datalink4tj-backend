import os
from dotenv import load_dotenv
load_dotenv() 

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://noah:727127zb@noahall.chat:3306/tj") 