from db.database import Base
from models.user import User
from models.ehs import Ehs
from models.department import Department
from models.qa import Qa, Qad
from models.event import Event
from models.maint import MaintDaily, MaintWeekly
from db.database import engine

Base.metadata.create_all(bind=engine)

