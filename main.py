from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from db.session import get_db
import logging
import time
from sqlalchemy.orm import Session

# 先导入数据库配置
from core.config import settings

# 导入数据库模型 - 确保所有模型都已加载
from models import database, user
from models.database import setup_relationships

# 设置模型关系
setup_relationships()

# 导入初始化服务
from db.init_data import init_data
from services.permission_service import init_permissions_and_roles, PermissionService
from services.init_service import init_roles_and_permissions, migrate_superuser_to_roles

# 导入路由模块
from apis import (
    department, ehs, user, qa, event, 
    maint_works, activity, route, 
    permission, role, maint, example
)

# 配置日志 - 使用更高效的配置
logger = logging.getLogger(__name__)

def setup_logging():
    """配置日志系统"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level = getattr(logging, settings.LOG_LEVEL)
    
    # 确保日志目录存在
    import os
    os.makedirs("logs", exist_ok=True)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            # 添加文件处理器，记录到文件
            logging.FileHandler(f"logs/app.log"),
            # 添加控制台处理器
            logging.StreamHandler()
        ]
    )

# 设置日志
setup_logging()
logger.info(f"正在启动 {settings.PROJECT_NAME} v{settings.VERSION}")

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Datalink4TJ的后端API服务",
    version=settings.VERSION,
    docs_url=None  # 自定义Swagger UI
)

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义Swagger UI界面
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.PROJECT_NAME} - API文档",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
    )

# 添加请求日志和性能监控中间件
@app.middleware("http")
async def log_and_monitor_requests(request: Request, call_next):
    """请求日志和性能监控中间件"""
    # 记录请求开始时间
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    # 简化日志记录
    logger.info(f"请求开始: {method} {path}")
    
    # 处理请求
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        status_code = response.status_code
        
        # 基于状态码使用不同的日志级别
        if 200 <= status_code < 400:
            logger.info(f"请求成功: {method} {path} - 状态码: {status_code} - 处理时间: {process_time:.4f}秒")
        elif 400 <= status_code < 500:
            logger.warning(f"客户端错误: {method} {path} - 状态码: {status_code} - 处理时间: {process_time:.4f}秒")
        else:
            logger.error(f"服务器错误: {method} {path} - 状态码: {status_code} - 处理时间: {process_time:.4f}秒")
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"请求异常: {method} {path} - 错误: {str(e)} - 处理时间: {process_time:.4f}秒")
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误"}
        )

# 注册所有API路由
routers = [
    department.router,
    user.router,
    qa.router,
    ehs.router,
    event.router,
    maint_works.router,
    activity.router,
    route.router,
    permission.router,
    role.router,
    maint.router,
    example.router
]

for router in routers:
    app.include_router(router)

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的初始化操作"""
    logger.info(f"正在初始化应用 {settings.PROJECT_NAME} v{settings.VERSION}...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 初始化基础数据
        init_data(db)
        
        # 初始化权限和角色
        init_permissions_and_roles(db)
        
        # 初始化新的角色体系并迁移超级用户
        init_roles_and_permissions(db)
        migrate_superuser_to_roles(db)
        
        # 初始化路由数据
        from db.init_routes import init_routes
        init_routes(db)
        
        # 确保路由模块权限存在
        permission_service = PermissionService()
        permission_service.ensure_route_permissions(db)
        
        logger.info("应用初始化完成")
    except Exception as e:
        logger.error(f"应用初始化失败: {str(e)}")
        raise e  # 重新抛出异常，确保启动失败时能够得到通知
    finally:
        db.close()

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("应用正在关闭...")
    # 在此添加清理资源的代码，如关闭连接池等

@app.get("/")
async def root():
    """API根路径，返回应用信息"""
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 获取数据库会话并测试连接
        db = next(get_db())
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )

# 在主模块末尾添加这段代码用于直接运行
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"以独立模式启动{settings.PROJECT_NAME}服务器...")
    
    # 启动服务器
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )