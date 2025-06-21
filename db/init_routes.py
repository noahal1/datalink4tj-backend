from sqlalchemy.orm import Session
from db.session import get_db
from models.route import Route
import logging

logger = logging.getLogger(__name__)

def init_routes(db: Session):
    """
    初始化系统路由数据
    
    如果路由表为空，则插入默认路由数据
    
    参数:
    - db: 数据库会话
    """
    # 检查是否已有路由数据
    existing_routes = db.query(Route).count()
    if existing_routes > 0:
        logger.info(f"路由表已有 {existing_routes} 条数据，跳过初始化")
        return
    
    # 定义默认路由数据
    default_routes = [
        # 主菜单路由
        {
            "path": "/dashboard",
            "name": "Dashboard",
            "component": "Dashboard",
            "meta": {
                "title": "首页",
                "icon": "mdi-view-dashboard",
                "requiresAuth": False,
                "permission": "*",
                "group": "main"
            },
            "parent_id": None,
            "sort_order": 0
        },
        {
            "path": "/events",
            "name": "Events",
            "component": "Events",
            "meta": {
                "title": "重要事件",
                "icon": "mdi-calendar-text",
                "requiresAuth": True,
                "permission": "*",
                "group": "main"
            },
            "parent_id": None,
            "sort_order": 1
        },
        
        # 质量相关路由
        {
            "path": "/quality",
            "name": "Quality",
            "component": "Quality",
            "meta": {
                "title": "GP12数据",
                "icon": "mdi-checkbox-multiple-marked-circle-outline",
                "requiresAuth": True,
                "permission": "QA",
                "group": "qa"
            },
            "parent_id": None,
            "sort_order": 0
        },
        {
            "path": "/qa_others",
            "name": "QaOthers",
            "component": "Qa_others",
            "meta": {
                "title": "质量杂项",
                "icon": "mdi-account-group-outline",
                "requiresAuth": True,
                "permission": "QA",
                "group": "qa"
            },
            "parent_id": None,
            "sort_order": 1
        },
        
        # 生产相关路由
        {
            "path": "/assy",
            "name": "Assy",
            "component": "Assy",
            "meta": {
                "title": "生产",
                "icon": "mdi-hammer-wrench",
                "requiresAuth": True,
                "permission": "ASSY",
                "group": "assy"
            },
            "parent_id": None,
            "sort_order": 0
        },
        
        # 维修相关路由
        {
            "path": "/maintenance",
            "name": "Maintenance",
            "component": "Maintenance",
            "meta": {
                "title": "维修",
                "icon": "mdi-wrench",
                "requiresAuth": True,
                "permission": "MAT",
                "group": "mat"
            },
            "parent_id": None,
            "sort_order": 0
        },
        
        # 物流相关路由
        {
            "path": "/pcl",
            "name": "Pcl",
            "component": "Pcl",
            "meta": {
                "title": "物流",
                "icon": "mdi-truck",
                "requiresAuth": True,
                "permission": "PCL",
                "group": "pcl"
            },
            "parent_id": None,
            "sort_order": 0
        },
        
        # EHS相关路由
        {
            "path": "/ehs",
            "name": "EHS",
            "component": "EHS",
            "meta": {
                "title": "EHS",
                "icon": "mdi-security",
                "requiresAuth": True,
                "permission": "EHS",
                "group": "ehs"
            },
            "parent_id": None,
            "sort_order": 0
        },
        
        # 系统管理路由
        {
            "path": "/admin",
            "name": "Admin",
            "component": "Admin",
            "meta": {
                "title": "系统管理",
                "icon": "mdi-cog",
                "requiresAuth": True,
                "permission": "ADMIN",
                "group": "admin"
            },
            "parent_id": None,
            "sort_order": 0
        },
        
        # 系统管理子路由
        {
            "path": "/admin/users",
            "name": "AdminUsers",
            "component": "Admin",
            "meta": {
                "title": "用户管理",
                "icon": "mdi-account-group",
                "requiresAuth": True,
                "permission": "ADMIN",
                "group": "admin"
            },
            "parent_id": 9,  # 对应Admin路由的ID
            "sort_order": 0
        },
        {
            "path": "/admin/departments",
            "name": "AdminDepartments",
            "component": "AdminDepartments",
            "meta": {
                "title": "部门管理",
                "icon": "mdi-office-building",
                "requiresAuth": True,
                "permission": "ADMIN",
                "group": "admin"
            },
            "parent_id": 9,  # 对应Admin路由的ID
            "sort_order": 1
        },
        {
            "path": "/admin/activities",
            "name": "AdminActivities",
            "component": "AdminActivities",
            "meta": {
                "title": "操作记录",
                "icon": "mdi-history",
                "requiresAuth": True,
                "permission": "ADMIN",
                "group": "admin"
            },
            "parent_id": 9,  # 对应Admin路由的ID
            "sort_order": 2
        },
        {
            "path": "/admin/routes",
            "name": "RouteManagement",
            "component": "RouteManagement",
            "meta": {
                "title": "路由管理",
                "icon": "mdi-routes",
                "requiresAuth": True,
                "permission": "ADMIN",
                "group": "admin"
            },
            "parent_id": 9,  # 对应Admin路由的ID
            "sort_order": 3
        },
        
        # 登录页面（无需导航，但需要路由）
        {
            "path": "/login",
            "name": "Login",
            "component": "Login",
            "meta": {
                "title": "登录",
                "icon": "mdi-login",
                "requiresAuth": False,
                "public": True
            },
            "parent_id": None,
            "sort_order": 999  # 放在最后，通常不会显示在导航中
        }
    ]
    
    # 插入路由数据
    try:
        for route_data in default_routes:
            route = Route(**route_data)
            db.add(route)
        
        db.commit()
        logger.info(f"成功初始化 {len(default_routes)} 条路由数据")
    except Exception as e:
        db.rollback()
        logger.error(f"初始化路由数据失败: {str(e)}")
        raise e


if __name__ == "__main__":
    # 用于直接运行此脚本
    logging.basicConfig(level=logging.INFO)
    db = next(get_db())
    init_routes(db) 