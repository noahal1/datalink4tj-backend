# DataLink4TJ 后端

DataLink4TJ 是一个基于 FastAPI 和 Vue.js 的数据上报系统。本仓库包含后端部分。

## 项目结构

项目采用模块化结构，主要包括以下部分：

- `apis/`: API路由定义
- `core/`: 核心功能，如认证和安全
- `db/`: 数据库相关代码
- `models/`: 数据模型定义
- `schemas/`: Pydantic模型定义
- `services/`: 业务逻辑服务
- `tests/`: 测试代码

详细的项目结构请参考 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动服务

### 使用批处理文件启动（Windows）

```bash
run.bat
```

### 使用Python脚本启动

```bash
python run.py
```

## 重置管理员密码

如果需要重置管理员密码，可以运行以下命令：

```bash
python reset_password.py
```

默认管理员账户：
- 用户名：admin
- 密码：admin123

## API文档

启动服务后，可以通过以下URL访问API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 权限系统

系统采用基于角色的访问控制（RBAC）模型：

1. 用户可以拥有多个角色
2. 角色可以拥有多个权限
3. 权限定义为模块+操作级别的组合

操作级别包括：
- READ：读取权限
- WRITE：写入权限
- ADMIN：管理权限

## 开发指南

### 添加新的API端点

1. 在 `apis/` 目录下创建新的路由文件
2. 在 `main.py` 中注册新的路由
3. 在 `schemas/` 目录下定义请求和响应模型
4. 在 `services/` 目录下实现业务逻辑

### 数据库迁移

项目使用 SQLAlchemy 进行 ORM 操作，数据库迁移需要手动执行。

## 许可证

[MIT](LICENSE)