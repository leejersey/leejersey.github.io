# AI 应用的后端架构设计

> 从零搭建生产级 AI 应用后端——FastAPI + Celery + Redis + PostgreSQL 的标准架构，涵盖异步任务、流式响应、文件处理、缓存策略、多租户、部署运维，一套架构支撑所有 AI 产品。

---

## 1. AI 应用后端的独特挑战

### 1.1 AI 应用 vs 传统 Web：四大不同

| 维度 | 传统 Web | AI 应用 |
|:---|:---|:---|
| **响应时间** | 50-200ms | 3-30s（LLM 生成） |
| **输出方式** | 一次性返回 | 流式逐字输出 |
| **计算成本** | 几乎为零 | $0.01-$0.1/次 |
| **文件处理** | 简单上传 | PDF 解析、向量化、分块 |
| **状态管理** | 无状态 | 对话历史、上下文窗口 |

### 1.2 技术栈选型：FastAPI + Celery + Redis + PG

```
为什么选这套：

  FastAPI ─── 异步原生、类型安全、自动文档
     │        比 Flask 快 3x，比 Django 轻量
     │
  Celery ──── 分布式任务队列、重试、优先级
     │        LLM 长任务不阻塞 API
     │
  Redis ───── 缓存 + 消息队列 + 会话存储
     │        亚毫秒延迟，Celery Broker
     │
  PostgreSQL ─ JSONB 灵活存储 + 全文检索 + pgvector
               一个数据库搞定结构化+向量数据
```

### 1.3 单体还是微服务：AI 应用的最佳起步

| 阶段 | 架构 | 理由 |
|:---|:---|:---|
| 0→1 | 单体 + Celery | 快速迭代，一个仓库搞定 |
| 1→10 | 模块化单体 | 分 package 但不分服务 |
| 10→100 | 拆关键服务 | 向量检索、文件处理独立 |

> 💡 **90% 的 AI 应用不需要微服务**——单体 + Celery Worker 可以支撑日均 10 万次调用。过早拆分只会增加复杂度。

### 1.4 整体架构总览

```
AI 应用后端标准架构：

  客户端（Web/App）
    │
    ▼
  Nginx（反向代理 + SSL + 负载均衡）
    │
    ▼
  FastAPI（API 层）
  ├── /api/chat         → SSE 流式对话
  ├── /api/tasks        → 异步任务提交
  ├── /api/files        → 文件上传处理
  └── /api/admin        → 管理后台
    │           │
    │           ▼
    │      Celery Worker（异步任务）
    │      ├── LLM 调用
    │      ├── 文件解析
    │      └── 向量化入库
    │
    ├──→ Redis（缓存 + Broker + 会话）
    ├──→ PostgreSQL（业务数据 + pgvector）
    └──→ MinIO/S3（文件对象存储）
```

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **四大不同** | 慢响应 + 流式 + 高成本 + 大文件 |
| **技术栈** | FastAPI + Celery + Redis + PG |
| **单体优先** | 90% 场景不需要微服务 |

---

## 2. FastAPI 核心层：API 设计与请求处理

### 2.1 项目结构：分层架构设计

```
app/
├── main.py                 # FastAPI 入口
├── config.py               # 配置管理
├── api/                    # 路由层
│   ├── __init__.py
│   ├── chat.py             # 对话接口
│   ├── tasks.py            # 异步任务接口
│   ├── files.py            # 文件处理接口
│   └── users.py            # 用户认证接口
├── services/               # 业务逻辑层
│   ├── chat_service.py
│   ├── file_service.py
│   └── llm_service.py
├── models/                 # 数据模型层
│   ├── database.py         # SQLAlchemy 配置
│   ├── user.py
│   ├── conversation.py
│   └── message.py
├── schemas/                # Pydantic 模型
│   ├── chat.py
│   ├── task.py
│   └── user.py
├── workers/                # Celery 任务
│   ├── celery_app.py
│   ├── llm_tasks.py
│   └── file_tasks.py
├── middleware/             # 中间件
│   ├── auth.py
│   ├── rate_limit.py
│   └── logging.py
└── utils/                  # 工具函数
    ├── cache.py
    └── storage.py
```

### 2.2 API 设计规范：路由 + Pydantic 模型

```python
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel, Field
from datetime import datetime

app = FastAPI(title="AI App Backend", version="1.0.0")

# ── Pydantic 模型 ──
class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str = Field(..., min_length=1, max_length=10000)
    model: str = "gpt-4o"
    stream: bool = True

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    model: str
    usage: dict
    created_at: datetime

# ── 路由 ──
chat_router = APIRouter(prefix="/api/chat", tags=["Chat"])

@chat_router.post("/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest, user = Depends(get_current_user)):
    """对话补全接口"""
    return await chat_service.complete(request, user)

app.include_router(chat_router)
```

### 2.3 中间件栈：认证 → 限流 → 日志 → 错误处理

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time, uuid

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        start = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start
        logger.info(f"[{request_id}] {request.method} {request.url.path} "
                     f"→ {response.status_code} ({duration:.2f}s)")
        response.headers["X-Request-ID"] = request_id
        return response

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "服务内部错误"})

# 中间件注册顺序（从外到内）
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)
```

### 2.4 依赖注入：数据库/Redis/LLM 客户端

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from openai import AsyncOpenAI
import redis.asyncio as redis

# 数据库会话
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/aiapp")
SessionLocal = async_sessionmaker(engine, class_=AsyncSession)

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

# Redis 客户端
redis_pool = redis.ConnectionPool.from_url("redis://localhost:6379")

async def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=redis_pool)

# LLM 客户端（全局复用）
llm_client = AsyncOpenAI()

async def get_llm() -> AsyncOpenAI:
    return llm_client

# 在路由中使用
@chat_router.post("/completions")
async def chat(request: ChatRequest,
               db: AsyncSession = Depends(get_db),
               cache: redis.Redis = Depends(get_redis),
               llm: AsyncOpenAI = Depends(get_llm)):
    ...
```

> 💡 **LLM 客户端必须全局复用**——`AsyncOpenAI()` 内部维护了连接池，每次请求都创建会导致连接泄漏。用依赖注入保证全局一个实例。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **分层架构** | api → service → model，职责清晰 |
| **Pydantic** | 请求/响应自动校验和序列化 |
| **中间件栈** | 认证→限流→日志，按顺序拦截 |
| **依赖注入** | 数据库/Redis/LLM 统一管理生命周期 |

---

## 3. 异步任务系统：Celery + Redis

### 3.1 为什么需要异步：LLM 调用不能阻塞请求

```
同步模式的问题：

  客户端 ──POST /api/generate──→ FastAPI
                                    │
                                    ├── 调用 LLM（等 10 秒...）
                                    │
                                    └── 返回结果
  
  问题：10 秒内 HTTP 连接被占用，Nginx 可能超时

异步模式：

  客户端 ──POST /api/generate──→ FastAPI
                                    │
                                    ├── 提交 Celery 任务 → 立即返回 task_id
                                    │
  客户端 ──GET /api/tasks/{id}──→ 轮询任务状态
                                    │
                                    └── status: running → success
```

### 3.2 Celery + Redis 快速搭建

```python
# workers/celery_app.py
from celery import Celery

celery_app = Celery(
    "ai_app",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    result_expires=3600,           # 结果保留 1 小时
    task_soft_time_limit=120,      # 软超时 2 分钟
    task_time_limit=180,           # 硬超时 3 分钟
    worker_prefetch_multiplier=1,  # 一次只取一个任务（LLM 任务耗时长）
    worker_concurrency=4,          # 4 个并发 Worker
)
```

```python
# workers/llm_tasks.py
from workers.celery_app import celery_app
from openai import OpenAI

@celery_app.task(bind=True, max_retries=2)
def generate_content(self, prompt: str, model: str = "gpt-4o"):
    """LLM 内容生成任务"""
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return {
            "content": response.choices[0].message.content,
            "usage": response.usage.model_dump(),
        }
    except Exception as e:
        self.retry(countdown=5, exc=e)
```

### 3.3 任务状态追踪与前端轮询

```python
# api/tasks.py
from celery.result import AsyncResult

@task_router.post("/submit")
async def submit_task(request: TaskRequest, user = Depends(get_current_user)):
    task = generate_content.delay(request.prompt, request.model)
    
    # 记录到数据库
    await db.save_task(user.id, task.id, request.prompt)
    
    return {"task_id": task.id, "status": "submitted"}

@task_router.get("/{task_id}")
async def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    
    response = {"task_id": task_id, "status": result.status}
    
    if result.ready():
        if result.successful():
            response["result"] = result.get()
        else:
            response["error"] = str(result.result)
    elif result.status == "PROGRESS":
        response["progress"] = result.info
    
    return response
```

### 3.4 优先级队列与定时任务

```python
# 优先级队列
celery_app.conf.task_routes = {
    "workers.llm_tasks.generate_content": {"queue": "llm"},
    "workers.file_tasks.parse_document": {"queue": "file"},
}

# 启动不同队列的 Worker
# celery -A workers.celery_app worker -Q llm -c 4
# celery -A workers.celery_app worker -Q file -c 2

# 定时任务
celery_app.conf.beat_schedule = {
    "cleanup_expired_tasks": {
        "task": "workers.cleanup.remove_old_tasks",
        "schedule": 3600,  # 每小时
    },
    "daily_usage_report": {
        "task": "workers.report.generate_daily_report",
        "schedule": 86400,  # 每天
    },
}
```

> 💡 **`worker_prefetch_multiplier=1` 是关键配置**——LLM 任务耗时长，默认预取 4 个会导致任务堆积在一个 Worker 上。设为 1 确保每个 Worker 做完一个再取下一个。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **异步模式** | 提交任务 → 返回 task_id → 轮询结果 |
| **prefetch=1** | LLM 任务必须设为 1，避免堆积 |
| **队列分离** | LLM / 文件 / 清理 用不同队列 |
| **定时任务** | Celery Beat 驱动周期性任务 |

---

## 4. 流式响应：SSE 与 WebSocket

### 4.1 SSE：最简单的流式输出方案

```python
from fastapi.responses import StreamingResponse
import json

@chat_router.post("/stream")
async def chat_stream(request: ChatRequest, user = Depends(get_current_user)):
    """SSE 流式对话"""
    
    async def event_stream():
        # 1. 创建会话和消息记录
        conversation = await get_or_create_conversation(request, user)
        full_content = ""
        
        # 2. 流式调用 LLM
        stream = await llm_client.chat.completions.create(
            model=request.model,
            messages=conversation.to_messages() + [{"role": "user", "content": request.message}],
            stream=True,
        )
        
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full_content += delta
            yield f"data: {json.dumps({'type': 'content', 'content': delta})}\n\n"
        
        # 3. 保存完整消息
        await save_message(conversation.id, "assistant", full_content)
        yield f"data: {json.dumps({'type': 'done', 'message_id': message_id})}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### 4.2 WebSocket：实时双向通信

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self.active[user_id] = ws
    
    def disconnect(self, user_id: str):
        self.active.pop(user_id, None)
    
    async def send(self, user_id: str, data: dict):
        if ws := self.active.get(user_id):
            await ws.send_json(data)

manager = ConnectionManager()

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(ws: WebSocket, user_id: str):
    await manager.connect(user_id, ws)
    try:
        while True:
            data = await ws.receive_json()
            
            # 流式回复
            stream = await llm_client.chat.completions.create(
                model="gpt-4o", messages=data["messages"], stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                await ws.send_json({"type": "content", "content": delta})
            
            await ws.send_json({"type": "done"})
    except WebSocketDisconnect:
        manager.disconnect(user_id)
```

### 4.3 流式 + 异步任务的组合模式

```python
@chat_router.post("/smart-stream")
async def smart_stream(request: ChatRequest, user = Depends(get_current_user)):
    """混合模式：短任务走 SSE，长任务走 Celery"""
    
    estimated_time = estimate_task_time(request)
    
    if estimated_time < 30:
        # 短任务：直接流式
        return StreamingResponse(stream_llm(request), media_type="text/event-stream")
    else:
        # 长任务：提交异步
        task = generate_content.delay(request.prompt)
        return {"task_id": task.id, "mode": "async", "estimated_time": estimated_time}
```

### 4.4 断线重连与消息补偿

```python
@chat_router.get("/stream/resume/{message_id}")
async def resume_stream(message_id: str, last_offset: int = 0):
    """断线重连：从上次断开处继续"""
    
    cached_content = await redis.get(f"stream:{message_id}")
    if not cached_content:
        raise HTTPException(404, "流已过期")
    
    async def resume_generator():
        content = cached_content[last_offset:]
        for i in range(0, len(content), 10):
            yield f"data: {json.dumps({'content': content[i:i+10], 'offset': last_offset + i})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(resume_generator(), media_type="text/event-stream")
```

> 💡 **SSE 比 WebSocket 简单得多，大多数场景用 SSE 就够了**——SSE 基于 HTTP，天然支持重连和认证。WebSocket 只在需要双向通信（实时协作）时才用。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **SSE** | 服务端推送，最简单的流式方案 |
| **WebSocket** | 双向通信，适合实时协作 |
| **混合模式** | 短任务 SSE + 长任务 Celery |
| **断线重连** | 缓存已生成内容，按 offset 续传 |

---

## 5. 数据层：PostgreSQL + Redis + 对象存储

### 5.1 数据库设计：用户 / 会话 / 消息 / 文件

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(200) UNIQUE NOT NULL,
    hashed_password VARCHAR(200) NOT NULL,
    tier VARCHAR(20) DEFAULT 'free',      -- free / pro / enterprise
    api_key VARCHAR(100) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 会话表
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    title VARCHAR(200) DEFAULT '新对话',
    model VARCHAR(50) DEFAULT 'gpt-4o',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 消息表
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,             -- user / assistant / system
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    cost DECIMAL(10, 6) DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 文件表
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_size BIGINT,
    storage_path VARCHAR(1000),           -- MinIO/S3 路径
    status VARCHAR(20) DEFAULT 'uploaded', -- uploaded / processing / ready / failed
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.2 SQLAlchemy 异步 ORM

```python
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, relationship
import uuid
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    title = Column(String(200), default="新对话")
    model = Column(String(50), default="gpt-4o")
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime, default=datetime.now)
    
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID, ForeignKey("conversations.id", ondelete="CASCADE"))
    role = Column(String(20))
    content = Column(Text)
    token_count = Column(Integer, default=0)
    
    conversation = relationship("Conversation", back_populates="messages")

# CRUD 操作
async def create_conversation(db: AsyncSession, user_id: str, title: str) -> Conversation:
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    await db.commit()
    return conv
```

### 5.3 Redis 缓存策略：会话 / LLM 响应 / 配置

```python
import redis.asyncio as redis
import json

class CacheService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    # 1. 会话缓存（最近 N 条消息）
    async def cache_messages(self, conv_id: str, messages: list[dict], ttl: int = 3600):
        await self.redis.setex(f"conv:{conv_id}:messages", ttl, json.dumps(messages))
    
    async def get_cached_messages(self, conv_id: str) -> list[dict] | None:
        data = await self.redis.get(f"conv:{conv_id}:messages")
        return json.loads(data) if data else None
    
    # 2. LLM 响应缓存（相同问题不重复调用）
    async def cache_llm_response(self, prompt_hash: str, response: str, ttl: int = 7200):
        await self.redis.setex(f"llm:{prompt_hash}", ttl, response)
    
    # 3. 配置缓存（模型/Prompt 配置热加载）
    async def get_config(self, key: str) -> dict | None:
        data = await self.redis.get(f"config:{key}")
        return json.loads(data) if data else None
```

### 5.4 文件处理：上传 / 解析 / 对象存储

```python
from fastapi import UploadFile
from miniopy_async import Minio

minio_client = Minio("localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)

@file_router.post("/upload")
async def upload_file(file: UploadFile, user = Depends(get_current_user), db = Depends(get_db)):
    # 1. 上传到 MinIO
    object_name = f"{user.id}/{uuid.uuid4()}/{file.filename}"
    await minio_client.put_object("ai-files", object_name, file.file, file.size)
    
    # 2. 记录到数据库
    file_record = File(user_id=user.id, filename=file.filename,
                        file_type=file.content_type, file_size=file.size,
                        storage_path=object_name, status="uploaded")
    db.add(file_record)
    await db.commit()
    
    # 3. 提交异步解析任务
    parse_document.delay(str(file_record.id), object_name)
    
    return {"file_id": file_record.id, "status": "processing"}
```

> 💡 **文件处理一定要异步**——PDF 解析、向量化可能需要几分钟。上传后立即返回 file_id，后台 Celery Worker 处理完更新状态。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **JSONB** | PG 原生 JSON 存储，灵活存 metadata |
| **异步 ORM** | SQLAlchemy + asyncpg，不阻塞事件循环 |
| **三级缓存** | 会话 + LLM 响应 + 配置 |
| **对象存储** | 文件不存数据库，存 MinIO/S3 |

---

## 6. 认证与多租户

### 6.1 JWT 认证：注册 / 登录 / Token 刷新

```python
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])
SECRET_KEY = "your-secret-key"

def create_token(user_id: str, expires_delta: timedelta = timedelta(hours=24)) -> str:
    payload = {"sub": user_id, "exp": datetime.now() + expires_delta}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

async def get_current_user(request: Request, db = Depends(get_db)):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = await db.get(User, payload["sub"])
        if not user:
            raise HTTPException(401, "用户不存在")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token 已过期")

@auth_router.post("/login")
async def login(email: str, password: str, db = Depends(get_db)):
    user = await get_user_by_email(db, email)
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(401, "邮箱或密码错误")
    
    return {
        "access_token": create_token(str(user.id)),
        "refresh_token": create_token(str(user.id), timedelta(days=30)),
    }
```

### 6.2 API Key 管理：给开发者的接口

```python
import secrets

@auth_router.post("/api-keys")
async def create_api_key(user = Depends(get_current_user), db = Depends(get_db)):
    api_key = f"sk-{secrets.token_urlsafe(32)}"
    user.api_key = api_key
    await db.commit()
    return {"api_key": api_key}

async def get_current_user(request: Request, db = Depends(get_db)):
    """支持 Bearer Token 和 API Key 两种认证"""
    auth = request.headers.get("Authorization", "")
    
    if auth.startswith("Bearer sk-"):
        # API Key 认证
        user = await get_user_by_api_key(db, auth.replace("Bearer ", ""))
    elif auth.startswith("Bearer ey"):
        # JWT 认证
        user = await verify_jwt(auth.replace("Bearer ", ""), db)
    else:
        raise HTTPException(401, "未提供认证信息")
    
    return user
```

### 6.3 多租户设计：数据隔离与配额

```python
class TenantConfig(BaseModel):
    """租户配额配置"""
    tier: str                      # free / pro / enterprise
    daily_requests: int = 100
    daily_tokens: int = 100_000
    max_file_size_mb: int = 10
    allowed_models: list[str] = ["gpt-4o-mini"]

TIER_CONFIGS = {
    "free":       TenantConfig(tier="free", daily_requests=100, daily_tokens=100_000,
                               allowed_models=["gpt-4o-mini"]),
    "pro":        TenantConfig(tier="pro", daily_requests=1000, daily_tokens=1_000_000,
                               allowed_models=["gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet"]),
    "enterprise": TenantConfig(tier="enterprise", daily_requests=10000, daily_tokens=10_000_000,
                               allowed_models=["gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet", "gpt-4.5"]),
}

async def check_tenant_quota(user, request: ChatRequest):
    config = TIER_CONFIGS[user.tier]
    
    if request.model not in config.allowed_models:
        raise HTTPException(403, f"当前套餐不支持 {request.model}")
    
    usage = await get_today_usage(user.id)
    if usage["requests"] >= config.daily_requests:
        raise HTTPException(429, "今日请求次数已用完")
```

### 6.4 RBAC 权限控制

```python
from enum import Enum

class Permission(str, Enum):
    CHAT = "chat"
    FILE_UPLOAD = "file:upload"
    ADMIN = "admin"

ROLE_PERMISSIONS = {
    "user": [Permission.CHAT],
    "pro_user": [Permission.CHAT, Permission.FILE_UPLOAD],
    "admin": [Permission.CHAT, Permission.FILE_UPLOAD, Permission.ADMIN],
}

def require_permission(permission: Permission):
    async def checker(user = Depends(get_current_user)):
        user_permissions = ROLE_PERMISSIONS.get(user.role, [])
        if permission not in user_permissions:
            raise HTTPException(403, "权限不足")
        return user
    return checker

@admin_router.get("/users", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def list_users():
    ...
```

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **JWT + API Key** | 两种认证方式，自动识别 |
| **多租户配额** | free/pro/enterprise 不同限制 |
| **RBAC** | 基于角色的权限控制 |

---

## 7. 生产部署：Docker + Nginx + CI/CD

### 7.1 Docker Compose：一键启动全部服务

```yaml
# docker-compose.yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db/aiapp
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on: [db, redis]
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
  
  worker:
    build: .
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db/aiapp
      - REDIS_URL=redis://redis:6379
    depends_on: [db, redis]
    command: celery -A app.workers.celery_app worker -Q llm,file -c 4
  
  beat:
    build: .
    depends_on: [redis]
    command: celery -A app.workers.celery_app beat
  
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: aiapp
      POSTGRES_PASSWORD: postgres
    volumes: ["pgdata:/var/lib/postgresql/data"]
  
  redis:
    image: redis:7-alpine
  
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]

volumes:
  pgdata:
```

### 7.2 Nginx 反向代理与 SSL

```nginx
upstream api {
    server api:8000;
}

server {
    listen 443 ssl;
    server_name api.example.com;
    
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    
    # API 请求
    location /api/ {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # SSE 流式接口（关键：关闭缓冲）
    location /api/chat/stream {
        proxy_pass http://api;
        proxy_buffering off;              # 关闭缓冲！
        proxy_cache off;
        proxy_read_timeout 300s;          # SSE 需要长超时
        proxy_set_header Connection '';
        chunked_transfer_encoding off;
    }
    
    # WebSocket
    location /ws/ {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 7.3 GitHub Actions：自动化部署

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build & Push Docker Image
        run: |
          docker build -t registry.example.com/ai-app:${{ github.sha }} .
          docker push registry.example.com/ai-app:${{ github.sha }}
      
      - name: Deploy to Server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: deploy
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/ai-app
            docker compose pull
            docker compose up -d --force-recreate
```

### 7.4 健康检查与优雅关停

```python
@app.get("/health")
async def health_check(db = Depends(get_db), cache = Depends(get_redis)):
    checks = {}
    
    # 检查数据库
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except:
        checks["database"] = "error"
    
    # 检查 Redis
    try:
        await cache.ping()
        checks["redis"] = "ok"
    except:
        checks["redis"] = "error"
    
    status = 200 if all(v == "ok" for v in checks.values()) else 503
    return JSONResponse(status_code=status, content=checks)

# 优雅关停
@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()          # 关闭数据库连接池
    await redis_pool.disconnect()   # 关闭 Redis 连接池
```

> 💡 **Nginx 的 `proxy_buffering off` 是 SSE 必须项**——不关的话 Nginx 会缓冲响应，用户看到的就不是流式输出了。这是最容易踩的坑。

---

## 8. 性能优化与扩展

### 8.1 连接池：数据库 / Redis / HTTP

```python
# 数据库连接池
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,              # 连接池大小
    max_overflow=10,           # 最大溢出
    pool_timeout=30,           # 获取连接超时
    pool_recycle=3600,         # 1 小时回收
)

# Redis 连接池
redis_pool = redis.ConnectionPool.from_url(
    REDIS_URL,
    max_connections=50,
    decode_responses=True,
)

# HTTP 连接池（调用外部 API）
import httpx
http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    timeout=httpx.Timeout(30.0),
)
```

### 8.2 并发控制：Semaphore 限制 LLM 并发

```python
import asyncio

# 限制同时只有 10 个 LLM 调用
llm_semaphore = asyncio.Semaphore(10)

async def rate_limited_llm_call(messages, model="gpt-4o"):
    async with llm_semaphore:
        return await llm_client.chat.completions.create(
            model=model, messages=messages,
        )
```

### 8.3 水平扩展：多 Worker + 负载均衡

```
水平扩展策略：

  阶段 1（单机）：
    1 × API (4 workers) + 1 × Celery (4 workers)
    支撑：~100 并发
  
  阶段 2（双机）：
    2 × API (4 workers each) + 2 × Celery (4 workers each)
    Nginx 负载均衡
    支撑：~400 并发
  
  阶段 3（集群）：
    K8s + HPA 自动扩缩
    API 按 CPU 扩缩，Celery 按队列深度扩缩
    支撑：~2000+ 并发
```

### 8.4 性能监控与瓶颈定位

```python
# 慢查询日志
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# 自定义性能指标
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    if duration > 5.0:
        logger.warning(f"🐌 慢请求: {request.url.path} ({duration:.2f}s)")
    
    return response
```

---

## 附录：AI 后端架构速查手册

### A.1 项目结构模板

```
ai-backend/
├── app/
│   ├── main.py            # FastAPI 入口
│   ├── config.py           # 配置（环境变量）
│   ├── api/                # 路由（chat/files/users/tasks）
│   ├── services/           # 业务逻辑
│   ├── models/             # SQLAlchemy 模型
│   ├── schemas/            # Pydantic 模型
│   ├── workers/            # Celery 任务
│   ├── middleware/         # 中间件
│   └── utils/              # 工具
├── docker-compose.yaml
├── Dockerfile
├── nginx.conf
├── requirements.txt
└── .github/workflows/deploy.yml
```

### A.2 Docker Compose 完整模板

| 服务 | 镜像 | 端口 | 用途 |
|:---|:---|:---|:---|
| api | 自建 | 8000 | FastAPI 主服务 |
| worker | 自建 | — | Celery Worker |
| beat | 自建 | — | 定时任务 |
| db | postgres:16 | 5432 | 数据库 |
| redis | redis:7 | 6379 | 缓存 + 消息队列 |
| minio | minio | 9000 | 文件存储 |
| nginx | nginx | 80/443 | 反向代理 |

### A.3 生产部署 Checklist

- [ ] 环境变量不硬编码，用 `.env` 或 Secrets Manager
- [ ] 数据库连接池配置合理（pool_size=20）
- [ ] Nginx 关闭 SSE 接口的 proxy_buffering
- [ ] Celery prefetch_multiplier=1
- [ ] 健康检查接口 `/health`
- [ ] 日志结构化输出（JSON 格式）
- [ ] SSL 证书自动续期（Let's Encrypt）
- [ ] 数据库自动备份（pg_dump）
- [ ] 监控告警（Prometheus + Grafana）

### A.4 常见问题排查

| 问题 | 原因 | 解决 |
|:---|:---|:---|
| SSE 不流式 | Nginx 缓冲 | `proxy_buffering off` |
| Celery 任务堆积 | prefetch 太高 | 设为 1 |
| 数据库连接耗尽 | 连接池太小/泄漏 | 增大 pool_size，检查 yield |
| WebSocket 断开 | Nginx 超时 | 增大 proxy_read_timeout |
| LLM 调用超时 | 模型过载 | 加超时 + 降级策略 |
