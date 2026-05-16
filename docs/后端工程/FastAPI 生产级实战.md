# FastAPI 生产级实战

> 从入门到生产部署——涵盖项目结构、依赖注入、中间件、异常处理、数据库集成、后台任务、WebSocket、认证鉴权、测试、性能优化与 Docker 部署，一套完整的 FastAPI 生产级开发方法论。

---

## 1. 项目结构与工程规范

### 1.1 生产级项目目录结构

```
推荐目录结构（中大型项目）：

app/
├── main.py              ← 应用入口
├── config.py            ← 配置管理
├── database.py          ← 数据库连接
├── dependencies.py      ← 公共依赖
├── exceptions.py        ← 自定义异常
├── middleware.py         ← 中间件
│
├── models/              ← SQLAlchemy 模型
│   ├── __init__.py
│   ├── user.py
│   └── order.py
│
├── schemas/             ← Pydantic 请求/响应模型
│   ├── __init__.py
│   ├── user.py
│   └── order.py
│
├── api/                 ← 路由层（只做参数解析 + 调用 service）
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   └── orders.py
│   └── deps.py          ← 路由级依赖
│
├── services/            ← 业务逻辑层
│   ├── __init__.py
│   ├── user_service.py
│   └── order_service.py
│
├── repositories/        ← 数据访问层（CRUD）
│   ├── __init__.py
│   ├── base.py
│   └── user_repo.py
│
└── utils/               ← 工具函数
    ├── __init__.py
    └── security.py

tests/                   ← 测试
├── conftest.py
├── test_users.py
└── test_orders.py

alembic/                 ← 数据库迁移
├── versions/
└── env.py

pyproject.toml           ← 依赖 + 工具配置
docker-compose.yml
Dockerfile
.env                     ← 环境变量（不入 Git）
```

```python
# app/main.py — 应用入口
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1 import users, orders
from app.middleware import setup_middlewares
from app.database import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动/关闭时的资源管理"""
    # 启动时
    print("🚀 Starting up...")
    yield
    # 关闭时
    await engine.dispose()
    print("🛑 Shutting down...")

app = FastAPI(
    title="My API",
    version="1.0.0",
    lifespan=lifespan,
)

# 注册中间件
setup_middlewares(app)

# 注册路由
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
```

### 1.2 多环境配置管理（Pydantic Settings）

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置（自动读取 .env 文件和环境变量）"""
    
    # 基础
    APP_NAME: str = "MyAPI"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # development / staging / production
    
    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/mydb"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # 外部服务
    SENTRY_DSN: str = ""
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

@lru_cache
def get_settings() -> Settings:
    """缓存配置实例（整个应用生命周期只创建一次）"""
    return Settings()

# 用法：
# from app.config import get_settings
# settings = get_settings()
# print(settings.DATABASE_URL)
```

### 1.3 结构化日志（Loguru）

```python
# app/logger.py
import sys
from loguru import logger

def setup_logger(environment: str = "production"):
    """配置日志"""
    logger.remove()  # 移除默认 handler
    
    if environment == "development":
        # 开发环境：彩色终端输出
        logger.add(sys.stderr, level="DEBUG",
                   format="<green>{time:HH:mm:ss}</green> | "
                          "<level>{level:8}</level> | "
                          "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
                          "<level>{message}</level>")
    else:
        # 生产环境：JSON 格式（方便 ELK 采集）
        logger.add(sys.stderr, level="INFO", serialize=True)
    
    # 文件日志（按天轮转，保留 30 天）
    logger.add("logs/app_{time:YYYY-MM-DD}.log",
               rotation="00:00", retention="30 days",
               level="INFO", encoding="utf-8")

# 用法：
# from loguru import logger
# logger.info("用户登录", user_id=123, ip="1.2.3.4")
```

### 1.4 代码规范：Ruff + Pre-commit

```toml
# pyproject.toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["app"]
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **分层架构** | api(路由) → service(业务) → repository(数据) |
| **配置管理** | Pydantic Settings + .env + lru_cache |
| **日志** | Loguru，开发彩色/生产 JSON，按天轮转 |
| **代码规范** | Ruff 替代 flake8+black+isort |

---

## 2. 依赖注入深度实战

### 2.1 依赖注入原理与基本用法

```python
from fastapi import Depends, Query

# ── 最简单的依赖 ──
def pagination(page: int = Query(1, ge=1), size: int = Query(20, le=100)):
    """分页参数依赖"""
    return {"skip": (page - 1) * size, "limit": size}

@app.get("/users")
async def list_users(paging: dict = Depends(pagination)):
    # paging = {"skip": 0, "limit": 20}
    return await user_service.list(skip=paging["skip"], limit=paging["limit"])
```

### 2.2 嵌套依赖与依赖树

```python
# ── 依赖可以嵌套：A 依赖 B，B 依赖 C ──

def get_settings():
    return Settings()

def get_db_url(settings: Settings = Depends(get_settings)):
    return settings.DATABASE_URL

def get_db_session(db_url: str = Depends(get_db_url)):
    return create_session(db_url)

@app.get("/users")
async def list_users(db = Depends(get_db_session)):
    # FastAPI 自动解析依赖链：settings → db_url → db_session
    pass
```

```
依赖树可视化：

  list_users()
    └── get_db_session()
          └── get_db_url()
                └── get_settings()

  FastAPI 从叶子节点开始解析，自底向上注入
```

### 2.3 yield 依赖与资源生命周期管理

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """数据库会话依赖（yield 管理生命周期）"""
    async with async_session_factory() as session:
        try:
            yield session          # ← 请求处理期间持有 session
            await session.commit() # ← 请求成功则提交
        except Exception:
            await session.rollback()  # ← 异常则回滚
            raise
        # async with 退出时自动关闭 session

# yield 前的代码 = 请求前执行（获取资源）
# yield 的值   = 注入到路由函数
# yield 后的代码 = 请求后执行（释放资源），即使出异常也会执行
```

### 2.4 数据库 Session 依赖（异步 SQLAlchemy）

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DEBUG,  # 开发环境打印 SQL
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

# app/dependencies.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# 路由中使用
@app.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    return user
```

> 💡 **永远用 yield 管理数据库连接**——不用 yield 的话，忘记关闭连接就会导致连接池耗尽。yield 保证"请求结束 = 连接释放"。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Depends** | 声明式依赖，自动注入参数 |
| **嵌套依赖** | 依赖可以依赖其他依赖，形成依赖树 |
| **yield 依赖** | yield 前获取资源，yield 后释放资源 |
| **DB Session** | yield + async with = 自动提交/回滚/关闭 |

---

## 3. 中间件与请求生命周期

### 3.1 中间件执行顺序与洋葱模型

```
中间件执行顺序（洋葱模型）：

  请求进入 →
    中间件 A（前）→
      中间件 B（前）→
        中间件 C（前）→
          路由处理函数
        ← 中间件 C（后）
      ← 中间件 B（后）
    ← 中间件 A（后）
  ← 响应返回

  注册顺序 = 执行顺序（先注册的先执行前半段，后执行后半段）
```

```python
from starlette.middleware.base import BaseHTTPMiddleware

class TimingMiddleware(BaseHTTPMiddleware):
    """请求耗时监控"""
    async def dispatch(self, request, call_next):
        import time
        start = time.perf_counter()
        response = await call_next(request)  # ← 调用下一层
        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.3f}s"
        logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.3f}s)")
        return response
```

### 3.2 CORS 跨域配置

```python
from fastapi.middleware.cors import CORSMiddleware

def setup_middlewares(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

### 3.3 请求日志中间件（Request ID 追踪）

```python
import uuid

class RequestIDMiddleware(BaseHTTPMiddleware):
    """为每个请求分配唯一 ID，贯穿全链路日志"""
    
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        
        # 注入到 request.state（路由中可访问）
        request.state.request_id = request_id
        
        # 绑定到日志上下文
        with logger.contextualize(request_id=request_id):
            logger.info(f"→ {request.method} {request.url.path}")
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            logger.info(f"← {response.status_code}")
        
        return response
```

### 3.4 限流中间件（令牌桶）

```python
import time
from collections import defaultdict

class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的 IP 维度令牌桶限流"""
    
    def __init__(self, app, rate: int = 60, per: int = 60):
        super().__init__(app)
        self.rate = rate      # 令牌数
        self.per = per        # 时间窗口（秒）
        self.buckets = defaultdict(lambda: {"tokens": rate, "last": time.time()})
    
    async def dispatch(self, request, call_next):
        client_ip = request.client.host
        bucket = self.buckets[client_ip]
        
        now = time.time()
        elapsed = now - bucket["last"]
        bucket["tokens"] = min(self.rate, bucket["tokens"] + elapsed * (self.rate / self.per))
        bucket["last"] = now
        
        if bucket["tokens"] < 1:
            return JSONResponse({"detail": "请求过于频繁，请稍后再试"}, status_code=429)
        
        bucket["tokens"] -= 1
        return await call_next(request)

# 注册（60 次/分钟）
app.add_middleware(RateLimitMiddleware, rate=60, per=60)
```

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **洋葱模型** | 中间件 A前→B前→路由→B后→A后 |
| **CORS** | CORSMiddleware 一行配置 |
| **Request ID** | uuid 贯穿全链路，方便排查日志 |
| **限流** | 令牌桶按 IP 限制 QPS |

---

## 4. 异常处理与错误响应

### 4.1 全局异常处理器设计

```python
# app/exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse

class AppException(Exception):
    """应用基础异常"""
    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

# 注册全局异常处理器
def register_exception_handlers(app: FastAPI):
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "data": None},
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """兜底：捕获所有未处理异常"""
        logger.exception(f"未处理异常: {exc}")
        return JSONResponse(
            status_code=500,
            content={"code": 50000, "message": "服务器内部错误", "data": None},
        )
```

### 4.2 自定义业务异常与错误码体系

```python
# ── 错误码规范：5 位数字，前 2 位=模块，后 3 位=具体错误 ──
class ErrorCode:
    # 用户模块 10xxx
    USER_NOT_FOUND = (10001, "用户不存在", 404)
    USER_ALREADY_EXISTS = (10002, "用户已存在", 409)
    INVALID_PASSWORD = (10003, "密码错误", 401)
    
    # 订单模块 20xxx
    ORDER_NOT_FOUND = (20001, "订单不存在", 404)
    ORDER_ALREADY_PAID = (20002, "订单已支付", 409)
    
    # 认证模块 30xxx
    TOKEN_EXPIRED = (30001, "Token 已过期", 401)
    TOKEN_INVALID = (30002, "Token 无效", 401)
    PERMISSION_DENIED = (30003, "权限不足", 403)

# 使用方式
def raise_error(error: tuple):
    code, message, status = error
    raise AppException(code=code, message=message, status_code=status)

# 在 service 中
async def get_user(user_id: int):
    user = await repo.get(user_id)
    if not user:
        raise_error(ErrorCode.USER_NOT_FOUND)
    return user
```

### 4.3 Pydantic 校验错误美化

```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """将 Pydantic 校验错误转为友好格式"""
    errors = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"][1:])  # 去掉 body/query
        errors.append({"field": field, "message": error["msg"]})
    
    return JSONResponse(
        status_code=422,
        content={
            "code": 42200,
            "message": "参数校验失败",
            "data": {"errors": errors},
        },
    )

# 原始错误：[{"loc":["body","email"],"msg":"value is not a valid email"}]
# 美化后：  {"errors":[{"field":"email","message":"value is not a valid email"}]}
```

### 4.4 生产环境异常上报（Sentry 集成）

```python
import sentry_sdk

def setup_sentry(dsn: str, environment: str):
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=0.1,  # 10% 采样
        profiles_sample_rate=0.1,
    )

# 在 main.py 中调用
setup_sentry(settings.SENTRY_DSN, settings.ENVIRONMENT)
```

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **全局处理器** | exception_handler 捕获所有异常统一格式 |
| **错误码** | 5 位数字：10001=用户不存在，30001=Token 过期 |
| **校验美化** | 422 错误从嵌套 list 转为 field+message |
| **Sentry** | 生产异常自动上报 + 10% traces 采样 |

---

## 5. 数据库集成（异步 SQLAlchemy + Alembic）

### 5.1 异步 SQLAlchemy 2.0 配置

```python
# app/models/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func
from datetime import datetime

class Base(DeclarativeBase):
    """所有模型的基类"""
    pass

class TimestampMixin:
    """时间戳 Mixin"""
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
```

### 5.2 Model 设计与关联关系

```python
# app/models/user.py
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50))
    hashed_password: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(String(20), default="user")
    
    # 关联
    orders: Mapped[list["Order"]] = relationship(back_populates="user", lazy="selectin")
```

### 5.3 CRUD Repository 模式

```python
# app/repositories/base.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

class BaseRepository[T]:
    """通用 CRUD 基类"""
    
    def __init__(self, model: type[T], db: AsyncSession):
        self.model = model
        self.db = db
    
    async def get(self, id: int) -> T | None:
        return await self.db.get(self.model, id)
    
    async def list(self, skip: int = 0, limit: int = 20, **filters) -> list[T]:
        stmt = select(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create(self, **data) -> T:
        obj = self.model(**data)
        self.db.add(obj)
        await self.db.flush()  # 获取 ID，但不提交
        return obj
    
    async def update(self, id: int, **data) -> T | None:
        obj = await self.get(id)
        if obj:
            for key, value in data.items():
                setattr(obj, key, value)
            await self.db.flush()
        return obj
    
    async def delete(self, id: int) -> bool:
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            return True
        return False
    
    async def count(self, **filters) -> int:
        stmt = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.db.execute(stmt)
        return result.scalar_one()

# app/repositories/user_repo.py
class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
    
    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
```

### 5.4 Alembic 数据库迁移

```bash
# 初始化
alembic init alembic

# 生成迁移
alembic revision --autogenerate -m "add users table"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

```python
# alembic/env.py 关键配置（异步模式）
from app.models.base import Base
from app.config import get_settings

target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    engine = create_async_engine(get_settings().DATABASE_URL)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()
```

### 5.5 事务管理与并发控制

```python
# ── 显式事务 ──
async def transfer(db: AsyncSession, from_id: int, to_id: int, amount: float):
    """转账：必须在同一事务中"""
    async with db.begin():  # 开始事务
        sender = await db.get(Account, from_id, with_for_update=True)  # 行锁
        receiver = await db.get(Account, to_id, with_for_update=True)
        
        if sender.balance < amount:
            raise AppException(code=20003, message="余额不足")
        
        sender.balance -= amount
        receiver.balance += amount
    # async with 退出时自动提交，异常时自动回滚
```

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Mapped 语法** | SQLAlchemy 2.0 的类型安全模型定义 |
| **BaseRepository** | 泛型 CRUD 基类，子类继承即可 |
| **Alembic** | autogenerate 自动生成迁移脚本 |
| **事务** | async with db.begin() + with_for_update 行锁 |

---

## 6. 认证与鉴权

### 6.1 JWT Token 认证（Access + Refresh）

```python
# app/utils/security.py
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict, secret: str, expires_minutes: int) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(payload, secret, algorithm="HS256")

def create_tokens(user_id: int, role: str, settings) -> dict:
    """生成 Access + Refresh 双 Token"""
    access = create_token(
        {"sub": str(user_id), "role": role, "type": "access"},
        settings.SECRET_KEY, settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    refresh = create_token(
        {"sub": str(user_id), "type": "refresh"},
        settings.SECRET_KEY, settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60,
    )
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
```

### 6.2 OAuth2 密码模式与第三方登录

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await UserRepository(db).get_by_email(form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise_error(ErrorCode.INVALID_PASSWORD)
    return create_tokens(user.id, user.role, get_settings())

# 当前用户依赖
async def get_current_user(token: str = Depends(oauth2_scheme),
                            db: AsyncSession = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, get_settings().SECRET_KEY, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except JWTError:
        raise_error(ErrorCode.TOKEN_INVALID)
    
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise_error(ErrorCode.USER_NOT_FOUND)
    return user
```

### 6.3 RBAC 角色权限控制

```python
class RoleChecker:
    """角色检查依赖"""
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise_error(ErrorCode.PERMISSION_DENIED)
        return user

# 使用
allow_admin = RoleChecker(["admin"])
allow_editor = RoleChecker(["admin", "editor"])

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, user: User = Depends(allow_admin)):
    """只有 admin 能删除用户"""
    pass
```

### 6.4 API Key 认证（面向服务间调用）

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(key: str = Depends(api_key_header)) -> str:
    valid_keys = get_settings().API_KEYS  # 从配置读取
    if key not in valid_keys:
        raise HTTPException(403, "Invalid API Key")
    return key

@router.get("/internal/stats")
async def internal_stats(key: str = Depends(verify_api_key)):
    """内部服务调用接口"""
    pass
```

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **双 Token** | Access(30min) + Refresh(7天)，Refresh 换 Access |
| **OAuth2** | OAuth2PasswordBearer + 密码模式登录 |
| **RBAC** | RoleChecker 依赖，按角色控制接口权限 |
| **API Key** | X-API-Key Header，服务间调用鉴权 |

---

## 7. 后台任务与异步处理

### 7.1 BackgroundTasks：轻量级后台任务

```python
from fastapi import BackgroundTasks

async def send_welcome_email(email: str, username: str):
    """发送欢迎邮件（耗时操作）"""
    await asyncio.sleep(2)  # 模拟发送
    logger.info(f"欢迎邮件已发送: {email}")

@router.post("/register")
async def register(data: UserCreate, background_tasks: BackgroundTasks,
                    db: AsyncSession = Depends(get_db)):
    user = await user_service.create(db, data)
    
    # 注册后台任务（不阻塞响应）
    background_tasks.add_task(send_welcome_email, user.email, user.username)
    
    return {"id": user.id, "message": "注册成功，欢迎邮件稍后发送"}
```

> 💡 **BackgroundTasks 适合 < 30 秒的任务**（发邮件、写日志）。超过 30 秒的用 Celery。

### 7.2 Celery + Redis：重型异步任务

```python
# app/worker.py
from celery import Celery

celery_app = Celery("worker", broker="redis://localhost:6379/0",
                     backend="redis://localhost:6379/1")
celery_app.conf.update(
    task_serializer="json",
    result_expires=3600,
    task_track_started=True,
)

@celery_app.task(bind=True, max_retries=3)
def process_video(self, video_path: str):
    """视频处理（重型任务）"""
    try:
        result = do_heavy_processing(video_path)
        return {"status": "done", "output": result}
    except Exception as exc:
        self.retry(exc=exc, countdown=60)  # 60 秒后重试

# 在 API 中调用
@router.post("/videos/process")
async def trigger_process(video_id: int):
    task = process_video.delay(f"/data/videos/{video_id}.mp4")
    return {"task_id": task.id, "status": "processing"}
```

### 7.3 定时任务（Celery Beat）

```python
# celery 定时任务配置
celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens": {
        "task": "app.tasks.cleanup_tokens",
        "schedule": 3600.0,  # 每小时
    },
    "daily-report": {
        "task": "app.tasks.generate_daily_report",
        "schedule": crontab(hour=8, minute=0),  # 每天 8:00
    },
}
```

### 7.4 任务状态查询与进度通知

```python
from celery.result import AsyncResult

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """查询异步任务状态"""
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,     # PENDING/STARTED/SUCCESS/FAILURE
        "result": result.result if result.ready() else None,
        "progress": result.info.get("progress", 0) if result.state == "PROGRESS" else None,
    }
```

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **BackgroundTasks** | 轻量级，< 30 秒的任务用它 |
| **Celery** | 重型任务，支持重试、分布式 Worker |
| **Beat** | Celery 定时任务调度器 |
| **状态查询** | AsyncResult 查询 PENDING/SUCCESS/FAILURE |

---

## 8. WebSocket 与实时推送

### 8.1 WebSocket 基础与连接管理

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active: dict[str, WebSocket] = {}  # user_id → ws
    
    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self.active[user_id] = ws
        logger.info(f"WS 连接: {user_id}, 当前在线: {len(self.active)}")
    
    def disconnect(self, user_id: str):
        self.active.pop(user_id, None)
    
    async def send_to(self, user_id: str, message: dict):
        ws = self.active.get(user_id)
        if ws:
            await ws.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(ws: WebSocket, user_id: str):
    await manager.connect(user_id, ws)
    try:
        while True:
            data = await ws.receive_json()
            # 处理客户端消息
            await handle_ws_message(user_id, data)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
```

### 8.2 房间广播与消息路由

```python
class RoomManager:
    """房间管理：支持多房间广播"""
    
    def __init__(self):
        self.rooms: dict[str, set[str]] = {}  # room_id → {user_ids}
    
    def join(self, room_id: str, user_id: str):
        self.rooms.setdefault(room_id, set()).add(user_id)
    
    def leave(self, room_id: str, user_id: str):
        if room_id in self.rooms:
            self.rooms[room_id].discard(user_id)
    
    async def broadcast(self, room_id: str, message: dict, exclude: str = None):
        for user_id in self.rooms.get(room_id, set()):
            if user_id != exclude:
                await manager.send_to(user_id, message)
```

### 8.3 心跳检测与断线重连

```python
import asyncio

async def heartbeat_loop(ws: WebSocket, user_id: str, interval: int = 30):
    """服务端心跳"""
    try:
        while True:
            await asyncio.sleep(interval)
            await ws.send_json({"type": "ping"})
    except Exception:
        manager.disconnect(user_id)
```

### 8.4 实战：实时通知系统

```python
# 从 Celery 任务推送通知
@celery_app.task
def notify_user(user_id: str, title: str, content: str):
    """异步任务完成后推送 WebSocket 通知"""
    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete(
        manager.send_to(user_id, {
            "type": "notification",
            "title": title,
            "content": content,
        })
    )
```

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **ConnectionManager** | dict 存储 user_id → WebSocket 映射 |
| **房间广播** | RoomManager 管理多房间 + 排除发送者 |
| **心跳** | 30 秒一次 ping，检测死连接 |
| **通知推送** | Celery 任务完成后通过 WS 推给用户 |

---

## 9. 测试策略

### 9.1 pytest + httpx：异步 API 测试

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    """异步测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# tests/test_users.py
@pytest.mark.anyio
async def test_register(client: AsyncClient):
    resp = await client.post("/api/v1/users/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "Str0ngP@ss",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] > 0
    assert "password" not in data  # 密码不应返回

@pytest.mark.anyio
async def test_login(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "Str0ngP@ss",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()
```

### 9.2 测试数据库隔离（SQLite 内存库）

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
from app.dependencies import get_db

# 测试用 SQLite 内存数据库
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

@pytest.fixture(autouse=True)
async def setup_db():
    """每个测试用例前建表，测试后清空"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(setup_db):
    async def override_get_db():
        async with test_session_factory() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db  # ← 关键：替换依赖
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

### 9.3 Mock 外部服务（LLM API、第三方接口）

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.anyio
async def test_ai_endpoint(client: AsyncClient):
    """Mock LLM API 调用"""
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="模拟回答"))]
    
    with patch("app.services.ai_service.llm.chat", return_value=mock_response):
        resp = await client.post("/api/v1/ai/chat", json={"question": "测试"})
        assert resp.status_code == 200
        assert "模拟回答" in resp.json()["answer"]
```

### 9.4 CI 集成与覆盖率报告

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      
      - run: pip install -e ".[dev]"
      - run: pytest --cov=app --cov-report=xml -v
      
      - uses: codecov/codecov-action@v4
        with: { file: coverage.xml }
```

**第 9 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **httpx + ASGI** | 异步测试不启动真实服务器 |
| **依赖替换** | dependency_overrides 注入测试 DB |
| **Mock** | patch + AsyncMock 模拟外部 API |
| **CI** | GitHub Actions + pytest + Codecov |

---

## 10. 性能优化与生产部署

### 10.1 性能分析与瓶颈定位

```python
# ── 用中间件统计慢接口 ──
class SlowRequestLogger(BaseHTTPMiddleware):
    THRESHOLD = 1.0  # 超过 1 秒的请求记录为慢请求
    
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        
        if duration > self.THRESHOLD:
            logger.warning(f"🐌 慢请求: {request.method} {request.url.path} "
                          f"耗时 {duration:.2f}s")
        return response
```

```bash
# py-spy 实时火焰图（生产级性能分析）
pip install py-spy
py-spy record -o profile.svg -- python -m uvicorn app.main:app
```

### 10.2 连接池优化（数据库 / HTTP 客户端）

```python
# ── 数据库连接池 ──
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,       # 连接池大小（按 Worker 数调整）
    max_overflow=10,    # 超出 pool_size 时最多临时创建 10 个
    pool_timeout=30,    # 获取连接超时
    pool_recycle=1800,  # 30 分钟回收连接（防止 MySQL 超时断开）
)

# ── HTTP 客户端连接池（调外部 API）──
import httpx

# 全局复用，不要每次请求创建新 client
http_client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
)

# 在 lifespan 中关闭
@asynccontextmanager
async def lifespan(app):
    yield
    await http_client.aclose()
```

### 10.3 Redis 缓存层

```python
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost:6379/0")

def cache(ttl: int = 300):
    """缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            key = f"cache:{func.__name__}:{hash(str(args)+str(kwargs))}"
            
            cached = await redis_client.get(key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            await redis_client.set(key, json.dumps(result, default=str), ex=ttl)
            return result
        return wrapper
    return decorator

# 使用
@cache(ttl=600)
async def get_hot_products():
    return await product_repo.list(order_by="sales", limit=20)
```

### 10.4 Gunicorn + Uvicorn 部署配置

```python
# gunicorn.conf.py
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1  # CPU 核数 × 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

```bash
# 启动命令
gunicorn app.main:app -c gunicorn.conf.py
```

### 10.5 Docker 多阶段构建与 Compose 编排

```dockerfile
# Dockerfile（多阶段构建）
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini gunicorn.conf.py ./

EXPOSE 8000
CMD ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
```

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis]
    restart: unless-stopped

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    volumes: ["redisdata:/data"]

volumes:
  pgdata:
  redisdata:
```

**第 10 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **慢请求监控** | 中间件记录 > 1s 的请求 |
| **连接池** | DB pool_size=20 + httpx max_connections=100 |
| **缓存** | Redis 装饰器，TTL 5 分钟 |
| **部署** | Gunicorn(多进程) + Uvicorn(异步) + Docker |

---

## 附录

### A. FastAPI vs Flask vs Django 对比

| 维度 | FastAPI | Flask | Django |
|:---|:---|:---|:---|
| **异步支持** | 原生 async/await | 需要 Quart 改造 | Django 4.1+ 部分支持 |
| **性能** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **类型校验** | Pydantic 自动校验 | 手动 | DRF Serializer |
| **API 文档** | 自动生成 Swagger/ReDoc | 手动 | DRF |
| **学习曲线** | 中等 | 低 | 高 |
| **ORM** | 自选（SQLAlchemy） | 自选 | 内置 Django ORM |
| **适用场景** | API 服务、AI 应用 | 小型项目、原型 | 全栈 Web、CMS |

### B. 常用中间件速查表

| 中间件 | 功能 | 示例 |
|:---|:---|:---|
| **CORSMiddleware** | 跨域资源共享 | 前后端分离必备 |
| **TrustedHostMiddleware** | Host 白名单 | 防止 Host Header 攻击 |
| **GZipMiddleware** | 响应压缩 | 大 JSON 响应体积减 70% |
| **HTTPSRedirectMiddleware** | HTTP→HTTPS 重定向 | 生产环境必备 |
| **RequestID** | 请求追踪 | 贯穿日志链路 |
| **RateLimit** | 限流 | 防刷 / 防 DDoS |
| **Timing** | 耗时监控 | 慢接口告警 |

### C. 生产部署 Checklist

```
上线前检查清单：

  安全：
    ☐ SECRET_KEY 已更换为强随机值
    ☐ DEBUG = False
    ☐ CORS 白名单已配置（非 *）
    ☐ HTTPS 已配置
    ☐ Sentry DSN 已配置
    ☐ SQL 注入防护（参数化查询）

  性能：
    ☐ 数据库连接池已配置（pool_size）
    ☐ Redis 缓存已接入
    ☐ Gunicorn Worker 数 = CPU × 2 + 1
    ☐ 慢请求日志已开启

  运维：
    ☐ Docker 多阶段构建
    ☐ 健康检查端点 /health
    ☐ 日志输出为 JSON 格式
    ☐ Alembic 迁移已执行
    ☐ CI/CD Pipeline 已配置
    ☐ 备份策略已制定
```
