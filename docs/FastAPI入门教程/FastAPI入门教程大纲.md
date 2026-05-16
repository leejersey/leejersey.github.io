# FastAPI 入门教程大纲

> **目标**：用最短时间建立 FastAPI 全貌认知，掌握核心功能，具备独立开发 REST API 的能力。
>
> **预计时长**：6\~8 小时（含动手练习）
>
> **前置要求**：Python 3.10+基础、了解 HTTP 基本概念

---

## 第一章 初识 FastAPI（30 min）

### 1.1 FastAPI 是什么
- 基于 Python 的现代 Web 框架，专注于构建 API
- 核心卖点：**快（性能）、快（开发）、少 Bug、标准化**
- 底层基于 Starlette（Web 部分）+ Pydantic（数据校验部分）

### 1.2 与 Flask / Django REST Framework 的定位对比
- 性能对比（ASGI vs WSGI）
- 开发体验对比（类型提示驱动 vs 手动校验）

### 1.3 五分钟跑通第一个 API
- 安装：`pip install "fastapi[standard]"`
- 最小示例：Hello World
- 启动：`fastapi dev main.py`
- 打开自动文档：`/docs`（Swagger UI）和 `/redoc`

---

## 第二章 路由与请求处理（60 min）

### 2.1 路由基础
- 路径操作装饰器：`@app.get()` / `@app.post()` / `@app.put()` / `@app.delete()`
- HTTP 方法与 RESTful 语义的对应关系

### 2.2 路径参数
- 基本用法：`/users/{user_id}`
- 类型自动转换与校验（int、str、UUID 等）
- 路径参数的顺序问题（固定路径 vs 动态路径）

### 2.3 查询参数
- 基本用法：`/items?skip=0&limit=10`
- 可选参数与默认值
- 多种类型的查询参数

### 2.4 请求体（Request Body）
- 使用 Pydantic Model 定义请求体
- 路径参数 + 查询参数 + 请求体的混合使用
- FastAPI 如何自动区分三者

### 2.5 实战练习
- 实现一个简单的 Todo CRUD 接口（内存存储）

---

## 第三章 数据校验与序列化 —— Pydantic 核心（60 min）

### 3.1 Pydantic Model 基础
- 字段类型声明
- 必填字段 vs 可选字段（`Optional`、`None` 默认值）
- 字段默认值

### 3.2 数据校验
- 内置校验：类型、范围、长度
- `Field()` 进阶约束：`gt`、`le`、`min_length`、`max_length`、`pattern`
- 自定义校验器：`@field_validator`

### 3.3 嵌套模型与复杂结构
- 模型嵌套
- `List[Model]`、`Dict` 等复合类型

### 3.4 响应模型
- `response_model` 参数控制返回数据结构
- 区分输入模型 / 输出模型 / 数据库模型（读写分离思想）

---

## 第四章 自动交互式文档（20 min）

### 4.1 Swagger UI（/docs）
- 在线测试 API
- 查看请求/响应 Schema

### 4.2 ReDoc（/redoc）
- 适合分享给前端/第三方的文档风格

### 4.3 如何优化文档展示
- 路由的 `summary`、`description`、`tags` 参数
- Pydantic Model 的 `model_config` 中设置 `json_schema_extra`（示例值）
- 接口分组与排序

---

## 第五章 依赖注入系统（60 min）

### 5.1 什么是依赖注入
- 核心概念：把「准备工作」抽出来，按需注入
- FastAPI 的 `Depends()` 机制

### 5.2 基础用法
- 函数作为依赖
- 公共查询参数提取
- 多级依赖（依赖的依赖）

### 5.3 典型应用场景
- 数据库 Session 管理（`yield` 依赖）
- 获取当前登录用户
- 权限校验

### 5.4 类作为依赖
- 用类替代函数实现更复杂的依赖逻辑

---

## 第六章 中间件与异常处理（40 min）

### 6.1 异常处理
- `HTTPException` 的使用
- 自定义异常处理器：`@app.exception_handler()`
- `RequestValidationError` 的全局捕获

### 6.2 中间件
- 什么是中间件（请求/响应的拦截器）
- 自定义中间件：记录请求耗时
- CORS 中间件配置（前后端分离必备）

---

## 第七章 异步与性能（30 min）

### 7.1 async/await 基础回顾
- 同步 vs 异步的区别
- 什么时候用 `async def`，什么时候用普通 `def`

### 7.2 FastAPI 的异步处理机制
- I/O 密集型任务适合异步
- CPU 密集型任务的处理方式
- FastAPI 对同步函数的自动线程池处理

### 7.3 异步数据库操作简介
- 简要提及 SQLAlchemy async、Tortoise ORM 等方案

---

## 第八章 数据库集成实战（60 min）

### 8.1 SQLAlchemy + FastAPI 集成
- 安装与配置
- 定义 ORM 模型
- 创建数据库会话依赖

### 8.2 完整 CRUD 实战
- 将第二章的 Todo 改为数据库版本
- Repository / Service 分层思路

### 8.3 数据库迁移简介
- Alembic 基本用法（init → revision → upgrade）

---

## 第九章 认证与安全（50 min）

### 9.1 OAuth2 密码模式 + JWT
- 认证流程概览
- 使用 `python-jose` 生成/验证 JWT
- 使用 `passlib` 做密码哈希

### 9.2 FastAPI 的安全工具
- `OAuth2PasswordBearer`：声明认证方式
- `OAuth2PasswordRequestForm`：标准登录表单
- 依赖注入实现 `get_current_user`

### 9.3 权限控制
- 基于角色的简单权限示例

---

## 第十章 项目结构与工程化（40 min）

### 10.1 APIRouter —— 路由拆分
- 按功能模块拆分路由
- `prefix`、`tags`、`dependencies` 参数

### 10.2 推荐项目结构

```
project/
├── app/
│   ├── main.py            # 应用入口
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── models/            # ORM 模型
│   ├── schemas/           # Pydantic 模型
│   ├── routers/           # 路由模块
│   ├── services/          # 业务逻辑
│   └── dependencies/      # 公共依赖
├── alembic/               # 数据库迁移
├── tests/                 # 测试
└── requirements.txt
```

### 10.3 配置管理
- 使用 Pydantic `BaseSettings` 读取环境变量
- `.env` 文件管理

### 10.4 启动事件与生命周期
- `lifespan` 上下文管理器（替代已废弃的 `on_event`）

---

## 第十一章 测试（30 min）

### 11.1 使用 TestClient 编写测试
- `from fastapi.testclient import TestClient`
- 编写接口测试用例

### 11.2 依赖覆盖
- `app.dependency_overrides` 替换依赖（mock 数据库等）

### 11.3 异步测试
- 使用 `httpx.AsyncClient` 进行异步测试

---

## 第十二章 部署上线（30 min）

### 12.1 生产启动方式
- Uvicorn 生产配置：`uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`
- Gunicorn + Uvicorn Worker 组合

### 12.2 Docker 部署
- 编写 Dockerfile
- 多阶段构建优化镜像大小

### 12.3 部署 checklist
- CORS 配置
- 环境变量管理
- 日志配置
- HTTPS（反向代理 Nginx）

---

## 附录

### A. 常用速查表
| 功能 | 关键代码 |
|------|---------|
| 路径参数 | `@app.get("/items/{item_id}")` |
| 查询参数 | `def read(skip: int = 0, limit: int = 10)` |
| 请求体 | `def create(item: Item)` — Item 为 Pydantic Model |
| 响应模型 | `@app.get("/items", response_model=list[Item])` |
| 依赖注入 | `def read(db: Session = Depends(get_db))` |
| 异常 | `raise HTTPException(status_code=404, detail="Not found")` |
| 路由拆分 | `router = APIRouter(prefix="/api/v1")` |
| 中间件 | `@app.middleware("http")` |
| 认证 | `OAuth2PasswordBearer(tokenUrl="token")` |
| 测试 | `client = TestClient(app)` |

### B. 推荐学习资源
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)（最权威，质量极高）
- [FastAPI GitHub](https://github.com/tiangolo/fastapi)
- [Pydantic V2 文档](https://docs.pydantic.dev/)
- [Starlette 文档](https://www.starlette.io/)

---

> **教学建议**：每章讲完核心概念后，立即让学生动手写代码。建议以一个贯穿全教程的「Todo 应用」为主线，每章在上一章的基础上迭代，最终形成一个完整的、可部署的项目。
