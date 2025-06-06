import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from models.event import Event
from models.activity import Activity
from models.user import User
from db.database import SessionLocal

def init_events(db: Session):
    """初始化事件数据"""
    # 清除现有事件数据
    db.query(Event).delete()
    
    # 当前日期
    today = datetime.now().date()
    
    # 创建一些示例事件
    events = [
        Event(
            name="质量月度会议",
            department="QA",
            start_time=today + timedelta(days=2),
            end_time=today + timedelta(days=2)
        ),
        Event(
            name="安全培训",
            department="EHS",
            start_time=today + timedelta(days=5),
            end_time=today + timedelta(days=5)
        ),
        Event(
            name="生产计划评审",
            department="ASSY",
            start_time=today,
            end_time=today
        ),
        Event(
            name="设备维护",
            department="MAINT",
            start_time=today + timedelta(days=1),
            end_time=today + timedelta(days=3)
        ),
        Event(
            name="年度审核",
            department="ADMIN",
            start_time=today + timedelta(days=10),
            end_time=today + timedelta(days=12)
        )
    ]
    
    # 添加事件到数据库
    for event in events:
        db.add(event)
    
    db.commit()
    print(f"已添加 {len(events)} 个事件")

def init_activities(db: Session):
    """初始化活动记录数据"""
    # 清除现有活动记录
    db.query(Activity).delete()
    
    # 获取用户
    users = db.query(User).all()
    if not users:
        print("没有用户数据，无法创建活动记录")
        return
    
    # 当前时间
    now = datetime.now()
    
    # 创建一些示例活动记录
    activities = [
        Activity(
            title="质量部更新了 GP12 数据",
            action="上传了SWI生产线GP12数据",
            details="2023年7月15日数据",
            type="DATA_UPLOAD",
            icon="mdi-clipboard-check",
            color="primary",
            target="/quality",
            user_id=users[0].id if len(users) > 0 else None,
            user_name=users[0].name if len(users) > 0 else "系统用户",
            department="QA",
            changes_before=json.dumps({"date": "2023-07-15", "value": 0}),
            changes_after=json.dumps({"date": "2023-07-15", "value": 125}),
            created_at=now - timedelta(minutes=10)
        ),
        Activity(
            title="EHS 上报了新的 LWD 数据",
            action="记录了一起轻微安全事件",
            details="无人员伤亡，设备轻微损坏",
            type="INCIDENT_REPORT",
            icon="mdi-shield-alert",
            color="warning",
            target="/ehs",
            user_id=users[1].id if len(users) > 1 else None,
            user_name=users[1].name if len(users) > 1 else "李经理",
            department="EHS",
            changes_before=None,
            changes_after=json.dumps({
                "incident_id": "INC-2023-07",
                "severity": "轻微",
                "location": "A区域生产线",
                "description": "设备轻微损坏，无人员伤亡"
            }),
            created_at=now - timedelta(hours=1)
        ),
        Activity(
            title="管理员更新了系统配置",
            action="更新了用户权限设置",
            details="调整了质量部门的数据访问权限",
            type="SYSTEM_CONFIG",
            icon="mdi-cog",
            color="grey",
            target="/admin",
            user_id=users[0].id if len(users) > 0 else None,
            user_name=users[0].name if len(users) > 0 else "系统管理员",
            department="ADMIN",
            changes_before=json.dumps({"role": "QA", "permissions": ["read", "report"]}),
            changes_after=json.dumps({"role": "QA", "permissions": ["read", "report", "export"]}),
            created_at=now - timedelta(days=1)
        ),
        Activity(
            title="生产部提交了新的生产计划",
            action="上传了下周生产计划",
            details="包含所有生产线的排产信息",
            type="PRODUCTION_PLAN",
            icon="mdi-calendar-check",
            color="success",
            target="/assy",
            user_id=users[2].id if len(users) > 2 else None,
            user_name=users[2].name if len(users) > 2 else "王主管",
            department="ASSY",
            changes_before=json.dumps({"week": "2023-W28", "status": "draft"}),
            changes_after=json.dumps({"week": "2023-W28", "status": "published"}),
            created_at=now - timedelta(days=2)
        ),
        Activity(
            title="系统维护完成",
            action="完成了系统例行维护",
            details="更新了数据库并优化了系统性能",
            type="SYSTEM_MAINTENANCE",
            icon="mdi-tools",
            color="info",
            target="/admin",
            user_id=users[0].id if len(users) > 0 else None,
            user_name=users[0].name if len(users) > 0 else "IT部门",
            department="ADMIN",
            changes_before=json.dumps({"version": "1.2.3", "status": "maintenance"}),
            changes_after=json.dumps({"version": "1.2.4", "status": "online"}),
            created_at=now - timedelta(days=3)
        )
    ]
    
    # 添加活动记录到数据库
    for activity in activities:
        db.add(activity)
    
    db.commit()
    print(f"已添加 {len(activities)} 条活动记录")

def init_all(db: Session):
    """初始化所有示例数据"""
    init_events(db)
    init_activities(db)
    print("示例数据初始化完成")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        init_all(db)
    finally:
        db.close() 