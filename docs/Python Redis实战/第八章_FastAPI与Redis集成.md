# 第八章 FastAPI + Redis 集成

> 本章目标：在 FastAPI 项目中正确管理 Redis 连接生命周期、用依赖注入优雅传递 Redis 实例、实现 Session 管理和 WebSocket + Pub/Sub 实时推送。

---

## 8.1 FastAPI 生命周期管理 Redis 连接

### 问题：连接什么时候创建、什么时候关闭？

```python
# ❌ 反模式：在模块顶层创建连接
import redis.asyncio as aioredis

r = aioredis.Redis(host="127.0.0.1")  # 导入时就连接，测试/部署都可能出问题

# ❌ 反模式：在每个请求里创建连接
@app.get("/")
async def index():
    r = aioredis.Redis(host="127.0.0.1")  # 每次请求都建 TCP 连接
    await r.get("key")
    await r.aclose()  # 忘关就泄漏
```

### 正确做法：lifespan 生命周期

FastAPI 提供了 `lifespan` 上下文管理器，在**应用启动时创建连接，关闭时释放**：

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as aioredis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：管理 Redis 连接"""
    # ── 启动时 ──
    pool = aioredis.ConnectionPool(
        host="127.0.0.1",
        port=6379,
        db=0,
        max_connections=30,
        decode_responses=True,
    )
    app.state.redis = aioredis.Redis(connection_pool=pool)

    print("✅ Redis 连接池已创建")
    yield  # 应用运行中...

    # ── 关闭时 ──
    await app.state.redis.aclose()
    await pool.disconnect()
    print("✅ Redis 连接池已释放")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def index():
    # 通过 app.state 访问（但不够优雅，下节用依赖注入改进）
    pong = await app.state.redis.ping()
    return {"redis": "ok" if pong else "error"}
```

### 从环境变量读取配置

```python
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    redis_url: str = "redis://127.0.0.1:6379/0"
    redis_max_connections: int = 30

    class Config:
        env_file = ".env"


settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = aioredis.ConnectionPool.from_url(
        settings.redis_url,
        max_connections=settings.redis_max_connections,
        decode_responses=True,
    )
    app.state.redis = aioredis.Redis(connection_pool=pool)
    yield
    await app.state.redis.aclose()
    await pool.disconnect()
```

```bash
# .env
REDIS_URL=redis://:mypassword@redis-server:6379/0
REDIS_MAX_CONNECTIONS=50
```

---

## 8.2 依赖注入与 Session 管理

### 用 Depends 注入 Redis

比 `app.state.redis` 更优雅——路由函数直接声明参数：

```python
from fastapi import Depends, Request


async def get_redis(request: Request) -> aioredis.Redis:
    """依赖项：获取 Redis 连接"""
    return request.app.state.redis


@app.get("/users/{user_id}")
async def get_user(user_id: int, redis: aioredis.Redis = Depends(get_redis)):
    """路由直接使用注入的 redis 实例"""
    cached = await redis.get(f"cache:user:{user_id}")
    if cached:
        return {"source": "cache", "user": json.loads(cached)}

    # 模拟查数据库
    user = {"id": user_id, "name": "张三"}
    await redis.set(f"cache:user:{user_id}", json.dumps(user), ex=3600)
    return {"source": "db", "user": user}
```

### 封装 Redis 服务层

更进一步，把 Redis 操作封装成 Service 类：

```python
import json
from dataclasses import dataclass


@dataclass
class CacheService:
    """缓存服务"""
    redis: aioredis.Redis

    async def get(self, key: str) -> dict | None:
        data = await self.redis.get(key)
        if data and data != "__NULL__":
            return json.loads(data)
        return None

    async def set(self, key: str, value: dict, ttl: int = 3600):
        await self.redis.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)

    async def delete(self, key: str):
        await self.redis.delete(key)


async def get_cache_service(redis: aioredis.Redis = Depends(get_redis)) -> CacheService:
    """依赖项：获取缓存服务"""
    return CacheService(redis=redis)


@app.get("/articles/{article_id}")
async def get_article(article_id: int, cache: CacheService = Depends(get_cache_service)):
    cached = await cache.get(f"cache:article:{article_id}")
    if cached:
        return cached

    article = {"id": article_id, "title": "示例文章", "views": 0}
    await cache.set(f"cache:article:{article_id}", article, ttl=1800)
    return article
```

### Session 管理

用 Redis 存储用户 Session，替代服务端内存 Session——多实例部署时 Session 共享：

```python
import uuid
from fastapi import Response, Cookie
from typing import Optional


SESSION_TTL = 7 * 24 * 3600  # 7 天


class SessionService:
    """Redis Session 管理"""

    def __init__(self, redis: aioredis.Redis, prefix: str = "session"):
        self.redis = redis
        self.prefix = prefix

    def _key(self, session_id: str) -> str:
        return f"{self.prefix}:{session_id}"

    async def create(self, user_data: dict) -> str:
        """创建新 Session，返回 session_id"""
        session_id = str(uuid.uuid4())
        key = self._key(session_id)
        await self.redis.hset(key, mapping={
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            for k, v in user_data.items()
        })
        await self.redis.expire(key, SESSION_TTL)
        return session_id

    async def get(self, session_id: str) -> dict | None:
        """获取 Session 数据"""
        key = self._key(session_id)
        data = await self.redis.hgetall(key)
        if not data:
            return None
        # 续期
        await self.redis.expire(key, SESSION_TTL)
        return data

    async def update(self, session_id: str, data: dict):
        """更新 Session 字段"""
        key = self._key(session_id)
        await self.redis.hset(key, mapping={k: str(v) for k, v in data.items()})

    async def destroy(self, session_id: str):
        """销毁 Session"""
        await self.redis.delete(self._key(session_id))


async def get_session_service(redis: aioredis.Redis = Depends(get_redis)) -> SessionService:
    return SessionService(redis)


# ── 登录 ──
@app.post("/auth/login")
async def login(
    response: Response,
    session_svc: SessionService = Depends(get_session_service),
):
    # 验证用户（省略）
    user = {"user_id": "1001", "name": "张三", "role": "admin"}

    session_id = await session_svc.create(user)

    # 设置 Cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,       # 生产环境启用
        samesite="lax",
        max_age=SESSION_TTL,
    )
    return {"message": "登录成功"}


# ── 获取当前用户 ──
async def get_current_user(
    session_id: Optional[str] = Cookie(None),
    session_svc: SessionService = Depends(get_session_service),
) -> dict:
    """依赖项：从 Session 获取当前用户"""
    if not session_id:
        raise HTTPException(status_code=401, detail="未登录")

    session = await session_svc.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session 已过期")

    return session


from fastapi import HTTPException

@app.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"user": user}


# ── 登出 ──
@app.post("/auth/logout")
async def logout(
    response: Response,
    session_id: Optional[str] = Cookie(None),
    session_svc: SessionService = Depends(get_session_service),
):
    if session_id:
        await session_svc.destroy(session_id)
    response.delete_cookie("session_id")
    return {"message": "已登出"}
```

---

## 8.3 WebSocket + Redis Pub/Sub 实时推送

### 场景：多实例下的实时聊天

单实例时 WebSocket 消息可以在内存中广播。但部署多个实例后，用户可能连到不同的服务器——**需要 Redis Pub/Sub 做跨实例消息中转**：

```
用户 A ──WS──→ 服务器 1 ──PUBLISH──→ Redis ──→ 服务器 1 → 用户 A
                                           ──→ 服务器 2 → 用户 B
用户 B ──WS──→ 服务器 2                    ──→ 服务器 2 → 用户 C
用户 C ──WS──→ 服务器 2
```

### 完整实现

```python
from fastapi import WebSocket, WebSocketDisconnect
import asyncio


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # room_id → set of WebSocket connections
        self.rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.rooms:
            self.rooms[room_id].discard(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast_local(self, room_id: str, message: str, exclude: WebSocket = None):
        """广播给本实例中同一房间的所有连接"""
        if room_id not in self.rooms:
            return
        for ws in self.rooms[room_id].copy():
            if ws == exclude:
                continue
            try:
                await ws.send_text(message)
            except Exception:
                self.rooms[room_id].discard(ws)


manager = ConnectionManager()


async def redis_subscriber(redis: aioredis.Redis, room_id: str):
    """后台任务：监听 Redis Pub/Sub，广播到本地 WebSocket"""
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"chat:{room_id}")

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            # 广播给本实例的所有连接
            await manager.broadcast_local(room_id, message["data"])
    finally:
        await pubsub.unsubscribe(f"chat:{room_id}")
        await pubsub.aclose()


@app.websocket("/ws/chat/{room_id}")
async def websocket_chat(websocket: WebSocket, room_id: str):
    redis = websocket.app.state.redis

    # 连接
    await manager.connect(websocket, room_id)

    # 启动 Redis 订阅后台任务
    sub_task = asyncio.create_task(redis_subscriber(redis, room_id))

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.dumps({
                "room": room_id,
                "content": data,
                "timestamp": time.time(),
            })

            # 发布到 Redis（所有实例都会收到）
            await redis.publish(f"chat:{room_id}", message)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        sub_task.cancel()


# ── 客户端使用（JavaScript）──
# const ws = new WebSocket("ws://localhost:8000/ws/chat/room1");
# ws.onmessage = (e) => console.log(JSON.parse(e.data));
# ws.send("Hello, room!");
```

### 优化：连接级别的订阅管理

上面的实现每个 WebSocket 连接都创建一个 Pub/Sub 订阅。优化为**每个房间共享一个订阅**：

```python
class PubSubManager:
    """房间级 Pub/Sub 管理（每个房间只创建一个订阅）"""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self.subscriptions: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def ensure_subscription(self, room_id: str):
        """确保房间有一个订阅任务在运行"""
        async with self._lock:
            if room_id not in self.subscriptions:
                task = asyncio.create_task(self._subscribe_loop(room_id))
                self.subscriptions[room_id] = task

    async def _subscribe_loop(self, room_id: str):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"chat:{room_id}")
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                await manager.broadcast_local(room_id, message["data"])
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(f"chat:{room_id}")
            await pubsub.aclose()
            async with self._lock:
                self.subscriptions.pop(room_id, None)

    async def cleanup_room(self, room_id: str):
        """房间无人时清理订阅"""
        if room_id not in manager.rooms or not manager.rooms[room_id]:
            async with self._lock:
                task = self.subscriptions.pop(room_id, None)
                if task:
                    task.cancel()
```

### 消息持久化：聊天记录

Pub/Sub 不持久化消息。结合 List 或 Stream 保存聊天记录：

```python
async def save_and_publish(redis: aioredis.Redis, room_id: str, message: dict):
    """保存聊天记录 + 发布实时消息"""
    msg_json = json.dumps(message, ensure_ascii=False)

    pipe = redis.pipeline()
    # 保存到 List（最近 500 条）
    pipe.lpush(f"history:{room_id}", msg_json)
    pipe.ltrim(f"history:{room_id}", 0, 499)
    # 发布到 Pub/Sub
    pipe.publish(f"chat:{room_id}", msg_json)
    await pipe.execute()


async def get_chat_history(redis: aioredis.Redis, room_id: str, count: int = 50) -> list:
    """获取聊天记录"""
    messages = await redis.lrange(f"history:{room_id}", 0, count - 1)
    return [json.loads(m) for m in messages]


@app.get("/api/chat/{room_id}/history")
async def chat_history(room_id: str, redis: aioredis.Redis = Depends(get_redis)):
    messages = await get_chat_history(redis, room_id)
    return {"messages": messages}
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 生命周期 | `lifespan` 管理连接池创建和释放 |
| 配置 | `pydantic_settings` + `.env` 读取 Redis URL |
| 依赖注入 | `Depends(get_redis)` 注入到路由函数 |
| 服务层 | `CacheService` / `SessionService` 封装业务逻辑 |
| Session | Redis Hash 存储，Cookie 传递 session_id |
| WebSocket | Pub/Sub 跨实例广播 + List 保存聊天记录 |
| 房间管理 | 每房间共享一个 Pub/Sub 订阅，减少连接数 |

> **下一章预告**：生产环境最佳实践——Key 命名规范、序列化选型、异常处理与降级、内存与性能监控。
