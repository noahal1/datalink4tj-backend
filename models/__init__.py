from db.database import Base, engine

# 导入所有模型
from models.user import User
from models.department import Department
from models.permission import Permission, Role
from models.route import Route
from models.event import Event
from models.maint import MaintenanceWork, MaintDaily, MaintWeekly, MaintMetrics
from models.activity import Activity
from models.ehs import Ehs
#from models.pcl import PCL
from models.qa import Qa, Qad, QaKpi, MonthlyTotal
# 创建所有表
Base.metadata.create_all(bind=engine)

