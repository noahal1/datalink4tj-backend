# DataLink4TJ 项目结构

本文档详细描述了 DataLink4TJ 后端项目的目录结构和主要文件的功能。

## 目录结构

```
datalink4tj-backend/
├── apis/                  # API路由定义
│   ├── activity.py        # 操作记录API
│   ├── assembly.py        # 生产模块API
│   ├── department.py      # 部门管理API
│   ├── ehs.py             # EHS模块API
│   ├── event.py           # 事件模块API
│   ├── maintenance.py     # 维修模块API
│   ├── pcl.py             # 物流模块API
│   ├── quality.py         # 质量模块API
│   ├── route.py           # 路由管理API
│   └── user.py            # 用户管理API
├── core/                  # 核心功能
│   └── security.py        # 安全和认证相关功能
├── db/                    # 数据库相关
│   ├── database.py        # 数据库连接
│   ├── init_data.py       # 初始数据
│   ├── init_routes.py     # 初始路由
│   └── session.py         # 数据库会话
├── logs/                  # 日志文件夹
├── models/                # 数据模型
│   ├── activity.py        # 操作记录模型
│   ├── assembly.py        # 生产数据模型
│   ├── department.py      # 部门模型
│   ├── ehs.py             # EHS数据模型
│   ├── event.py           # 事件模型
│   ├── maintenance.py     # 维修数据模型
│   ├── pcl.py             # 物流数据模型
│   ├── permission.py      # 权限和角色模型
│   ├── quality.py         # 质量数据模型
│   ├── route.py           # 路由模型
│   └── user.py            # 用户模型
├── schemas/               # Pydantic模型
│   ├── activity.py        # 操作记录模式
│   ├── assembly.py        # 生产数据模式
│   ├── department.py      # 部门模式
│   ├── ehs.py             # EHS数据模式
│   ├── event.py           # 事件模式
│   ├── maintenance.py     # 维修数据模式
│   ├── pcl.py             # 物流数据模式
│   ├── permission.py      # 权限和角色模式
│   ├── quality.py         # 质量数据模式
│   ├── route.py           # 路由模式
│   └── user.py            # 用户模式
├── services/              # 业务逻辑服务
│   ├── activity_service.py    # 操作记录服务
│   ├── assembly_service.py    # 生产数据服务
│   ├── department.py          # 部门服务
│   ├── ehs_service.py         # EHS数据服务
│   ├── event_service.py       # 事件服务
│   ├── maintenance_service.py # 维修数据服务
│   ├── pcl_service.py         # 物流数据服务
│   ├── permission_service.py  # 权限服务
│   ├── quality_service.py     # 质量数据服务
│   └── user.py                # 用户服务
├── tests/                 # 测试代码
├── main.py                # 应用程序入口
├── requirements.txt       # 依赖列表
├── reset_password.py      # 重置密码脚本
├── run.bat                # Windows启动脚本
└── run.py                 # 启动脚本
```

## 主要组件说明

### API路由 (apis/)

API路由定义了系统的所有HTTP端点，处理请求和响应。每个模块有自己的路由文件。

### 核心功能 (core/)

包含系统的核心功能，如认证和安全。

- `security.py`: 实现JWT认证、密码哈希和验证等安全功能。

### 数据库 (db/)

处理数据库连接和初始化。

- `database.py`: 定义数据库连接
- `session.py`: 提供数据库会话
- `init_data.py`: 初始化基础数据
- `init_routes.py`: 初始化路由数据

### 数据模型 (models/)

定义SQLAlchemy ORM模型，映射到数据库表。

### Pydantic模型 (schemas/)

定义API请求和响应的数据结构，提供数据验证。

### 业务逻辑服务 (services/)

包含业务逻辑代码，处理数据处理和业务规则。

### 主要文件

- `main.py`: 应用程序入口，配置FastAPI应用
- `run.py`: 启动脚本，使用uvicorn运行应用
- `reset_password.py`: 重置管理员密码的脚本

## 数据流

1. 客户端发送请求到API路由
2. API路由验证请求数据（使用Pydantic模型）
3. API路由调用相应的服务处理业务逻辑
4. 服务层与数据库交互（使用SQLAlchemy ORM模型）
5. 服务层返回结果给API路由
6. API路由将结果转换为响应模型并返回给客户端

## 认证流程

1. 用户通过 `/users/token` 端点登录
2. 系统验证用户凭据并生成JWT令牌
3. 客户端在后续请求中使用Bearer认证头携带令牌
4. `get_current_user` 依赖项验证令牌并获取当前用户

## 权限系统

系统使用基于角色的访问控制（RBAC）：

1. 用户可以拥有多个角色
2. 角色可以拥有多个权限
3. 权限定义为模块+操作级别的组合

操作级别包括：
- READ：读取权限
- WRITE：写入权限
- ADMIN：管理权限 