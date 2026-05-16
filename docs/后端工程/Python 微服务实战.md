# Python 微服务实战

> 从单体到微服务——涵盖服务拆分策略、gRPC/HTTP 通信、服务注册与发现、API 网关、分布式事务、链路追踪、容错与熔断、容器化部署，一套完整的 Python 微服务工程实践。

---

## 1. 为什么要微服务？从单体说起

### 1.1 单体架构的天花板

```
单体架构的典型痛点（当你遇到 3 个以上就该考虑拆分）：

  ❌ 部署耦合：改一行代码，整个系统重新部署
  ❌ 扩展困难：订单模块扛不住流量，但只能整体扩容
  ❌ 技术锁定：所有模块绑定同一语言、框架、数据库
  ❌ 团队瓶颈：10 个人改同一个代码库，冲突不断
  ❌ 故障扩散：一个模块 OOM，整个服务挂掉
  ❌ 启动变慢：代码量大到启动需要 30 秒以上
```

### 1.2 微服务的核心原则

```
微服务的 5 个核心原则：

  1. 单一职责：每个服务只做一件事（用户/订单/支付）
  2. 独立部署：改用户服务不影响订单服务
  3. 独立数据：每个服务有自己的数据库，不共享表
  4. 去中心化：没有"上帝服务"，服务间平等通信
  5. 容错设计：一个服务挂了，其他服务能降级运行
```

### 1.3 什么时候不该用微服务

```
⚠️ 以下情况请留在单体：

  ✗ 团队 < 5 人（微服务的运维成本远超收益）
  ✗ 业务还没稳定（等领域边界清晰了再拆）
  ✗ 没有 DevOps 能力（CI/CD + 容器 + 监控是前提）
  ✗ 追求"技术先进"（微服务不是银弹，单体不是罪）

  正确路线：单体 → 模块化单体 → 微服务
  先把代码按模块分好包，再考虑拆成独立服务
```

### 1.4 Python 微服务技术栈全景

| 层级 | 技术 | 推荐 |
|:---|:---|:---|
| **Web 框架** | FastAPI / Flask | FastAPI（异步、类型安全） |
| **RPC 通信** | gRPC / Thrift | gRPC（Protobuf、流式） |
| **消息队列** | RabbitMQ / Kafka / Redis Streams | RabbitMQ（中小规模） |
| **服务发现** | Consul / etcd / Nacos | Consul（HTTP API 友好） |
| **API 网关** | Kong / Traefik / 自建 | Traefik（容器原生） |
| **分布式追踪** | OpenTelemetry + Jaeger | OTel（统一标准） |
| **监控** | Prometheus + Grafana | 行业标准 |
| **容器化** | Docker + Kubernetes | 必选项 |

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **单体痛点** | 部署耦合 + 扩展困难 + 故障扩散 |
| **核心原则** | 单一职责 + 独立部署 + 独立数据 |
| **前提条件** | 团队 ≥ 5 人 + DevOps 能力 + 领域边界清晰 |
| **正确路线** | 单体 → 模块化单体 → 微服务 |

---

## 2. 服务拆分策略

### 2.1 按业务领域拆分（DDD 思路）

```
领域驱动拆分三步法：

  Step 1：识别限界上下文（Bounded Context）
    → "用户"、"商品"、"订单"、"支付"、"库存"各自是独立的业务域
    → 每个域内部高内聚，域之间通过 API/事件松耦合

  Step 2：确定聚合根（Aggregate Root）
    → 用户域：User 是聚合根（地址、收藏夹是附属）
    → 订单域：Order 是聚合根（订单项、物流信息是附属）

  Step 3：划分服务边界
    → 一个限界上下文 = 一个微服务
    → 聚合根之间只能通过 ID 引用，不能直接外键关联
```

### 2.2 数据库拆分：每个服务独立数据库

```python
# ❌ 错误：多个服务共享一个数据库
#    用户服务和订单服务都直接查 orders 表 → 耦合

# ✅ 正确：每个服务有自己的数据库
# user-service  → user_db  (users, addresses)
# order-service → order_db (orders, order_items)
# product-service → product_db (products, categories)

# 跨服务查询怎么办？→ API 调用，不要 JOIN
async def get_order_detail(order_id: int):
    order = await order_repo.get(order_id)
    
    # 通过 API 获取用户信息（不是 JOIN）
    user = await user_client.get_user(order.user_id)
    
    # 通过 API 获取商品信息
    products = await product_client.get_products(order.product_ids)
    
    return {**order.dict(), "user": user, "products": products}
```

### 2.3 拆分粒度：拆多细才合适？

```
判断标准：

  太粗（该拆没拆）：
    → 一个服务有 50+ 张数据库表
    → 两个功能的发布周期完全不同但绑在一起
    → 一个团队改不过来

  太细（过度拆分）：
    → 两个服务每次都需要同时修改、同时部署
    → 一个请求需要跨 5 个服务串行调用
    → 服务之间的 API 调用比业务逻辑还多

  合适的粒度：
    → 一个服务由 2-5 人负责
    → 一个服务有 5-15 张表
    → 服务可以独立部署、独立测试
```

### 2.4 实战：电商系统拆分案例

```
电商系统拆分方案：

  单体时期（1 个服务、1 个数据库）：
  ┌───────────────────────────────┐
  │  用户 + 商品 + 订单 + 支付     │
  │  + 库存 + 通知 + 营销          │
  └───────────────────────────────┘

  微服务拆分后（7 个服务、7 个数据库）：
  ┌────────┐ ┌────────┐ ┌────────┐
  │ 用户    │ │ 商品    │ │ 订单    │
  │ 服务    │ │ 服务    │ │ 服务    │
  └────────┘ └────────┘ └────────┘
  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
  │ 支付    │ │ 库存    │ │ 通知    │ │ 营销    │
  │ 服务    │ │ 服务    │ │ 服务    │ │ 服务    │
  └────────┘ └────────┘ └────────┘ └────────┘
```

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **DDD 拆分** | 限界上下文 = 微服务边界 |
| **独立数据库** | 跨服务查数据用 API，不用 JOIN |
| **粒度判断** | 2-5 人负责、5-15 张表、独立部署 |
| **拆分路线** | 先画域 → 再定边界 → 最后拆服务 |

---

## 3. 服务间通信：HTTP vs gRPC

### 3.1 同步通信：REST API（httpx）

```python
import httpx

class UserServiceClient:
    """用户服务客户端（HTTP 调用）"""
    
    def __init__(self, base_url: str = "http://user-service:8001"):
        self.client = httpx.AsyncClient(base_url=base_url, timeout=10.0)
    
    async def get_user(self, user_id: int) -> dict:
        resp = await self.client.get(f"/api/v1/users/{user_id}")
        resp.raise_for_status()
        return resp.json()
    
    async def batch_get_users(self, user_ids: list[int]) -> list[dict]:
        resp = await self.client.post("/api/v1/users/batch", json={"ids": user_ids})
        resp.raise_for_status()
        return resp.json()
    
    async def close(self):
        await self.client.aclose()
```

### 3.2 同步通信：gRPC（高性能 RPC）

```protobuf
// proto/user.proto
syntax = "proto3";

service UserService {
  rpc GetUser (GetUserRequest) returns (UserResponse);
  rpc BatchGetUsers (BatchGetUsersRequest) returns (BatchGetUsersResponse);
}

message GetUserRequest {
  int32 user_id = 1;
}

message UserResponse {
  int32 id = 1;
  string username = 2;
  string email = 3;
}
```

```python
# gRPC 服务端
import grpc
from concurrent import futures
import user_pb2_grpc, user_pb2

class UserServicer(user_pb2_grpc.UserServiceServicer):
    async def GetUser(self, request, context):
        user = await user_repo.get(request.user_id)
        if not user:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("用户不存在")
            return user_pb2.UserResponse()
        return user_pb2.UserResponse(id=user.id, username=user.username, email=user.email)

async def serve():
    server = grpc.aio.server()
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServicer(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    await server.wait_for_termination()
```

```python
# gRPC 客户端
async def get_user_via_grpc(user_id: int):
    async with grpc.aio.insecure_channel("user-service:50051") as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
        response = await stub.GetUser(user_pb2.GetUserRequest(user_id=user_id))
        return {"id": response.id, "username": response.username}
```

### 3.3 异步通信：消息队列（RabbitMQ）

```python
import aio_pika

# ── 发布者（订单服务：下单后发事件）──
async def publish_order_created(order_id: int, user_id: int):
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("events", aio_pika.ExchangeType.TOPIC)
        
        message = aio_pika.Message(
            body=json.dumps({"order_id": order_id, "user_id": user_id}).encode(),
            content_type="application/json",
        )
        await exchange.publish(message, routing_key="order.created")

# ── 消费者（通知服务：监听下单事件 → 发短信）──
async def consume_order_events():
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("events", aio_pika.ExchangeType.TOPIC)
        queue = await channel.declare_queue("notification.order", durable=True)
        await queue.bind(exchange, routing_key="order.created")
        
        async with queue.iterator() as messages:
            async for message in messages:
                async with message.process():
                    data = json.loads(message.body)
                    await send_sms(data["user_id"], f"订单 {data['order_id']} 已创建")
```

### 3.4 通信模式选择指南

| 场景 | 推荐 | 原因 |
|:---|:---|:---|
| **查询类**（获取用户信息） | REST / gRPC | 需要同步等结果 |
| **命令类**（创建订单） | REST / gRPC | 需要立即知道成功/失败 |
| **通知类**（发短信/邮件） | 消息队列 | 不需要等结果，异步即可 |
| **事件广播**（订单创建 → 库存/通知/营销） | 消息队列 | 一对多，解耦 |
| **高性能内部调用** | gRPC | Protobuf 序列化比 JSON 快 10x |
| **对外暴露 API** | REST | 通用性好，前端/第三方都能调 |

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **REST** | 通用、简单、对外暴露首选 |
| **gRPC** | 高性能、强类型、内部调用首选 |
| **消息队列** | 异步解耦、事件广播、削峰填谷 |
| **选型原则** | 查询/命令→同步，通知/事件→异步 |

---

## 4. 服务注册与发现

### 4.1 为什么需要服务发现？

```
没有服务发现时（硬编码地址）：
  order-service → http://192.168.1.10:8001  ← IP 变了怎么办？
  order-service → http://192.168.1.11:8001  ← 新增实例怎么加？
  order-service → http://192.168.1.12:8001  ← 挂了怎么剔除？

有了服务发现后：
  order-service → 找 "user-service" → 注册中心返回可用地址列表
  → 自动感知上线/下线/扩容
```

### 4.2 Consul 服务注册与发现

```python
import consul.aio

class ServiceRegistry:
    """Consul 服务注册"""
    
    def __init__(self, consul_host: str = "consul", consul_port: int = 8500):
        self.client = consul.aio.Consul(host=consul_host, port=consul_port)
    
    async def register(self, name: str, host: str, port: int):
        """注册服务"""
        service_id = f"{name}-{host}-{port}"
        await self.client.agent.service.register(
            name=name,
            service_id=service_id,
            address=host,
            port=port,
            check=consul.Check.http(
                f"http://{host}:{port}/health",
                interval="10s",     # 每 10 秒检查一次
                timeout="5s",
                deregister="30s",   # 30 秒不健康则注销
            ),
        )
    
    async def discover(self, name: str) -> list[dict]:
        """发现服务（只返回健康实例）"""
        _, services = await self.client.health.service(name, passing=True)
        return [
            {"host": s["Service"]["Address"], "port": s["Service"]["Port"]}
            for s in services
        ]

# 在 FastAPI 启动时注册
@asynccontextmanager
async def lifespan(app):
    registry = ServiceRegistry()
    await registry.register("order-service", "order-service", 8002)
    yield
```

### 4.3 健康检查与自动注销

```python
# 每个服务必须暴露 /health 端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    checks = {
        "database": await check_db(),
        "redis": await check_redis(),
    }
    all_healthy = all(checks.values())
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={"status": "healthy" if all_healthy else "unhealthy", "checks": checks},
    )

async def check_db() -> bool:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

### 4.4 客户端负载均衡

```python
import random

class LoadBalancedClient:
    """客户端负载均衡"""
    
    def __init__(self, service_name: str, registry: ServiceRegistry):
        self.service_name = service_name
        self.registry = registry
    
    async def get_instance(self) -> str:
        """随机选一个健康实例"""
        instances = await self.registry.discover(self.service_name)
        if not instances:
            raise Exception(f"没有可用的 {self.service_name} 实例")
        
        inst = random.choice(instances)  # 随机负载均衡
        return f"http://{inst['host']}:{inst['port']}"
    
    async def request(self, method: str, path: str, **kwargs):
        base_url = await self.get_instance()
        async with httpx.AsyncClient() as client:
            return await client.request(method, f"{base_url}{path}", **kwargs)
```

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **服务发现** | 注册中心维护地址列表，调方只查名字 |
| **Consul** | HTTP API 友好的注册中心 |
| **健康检查** | 每 10 秒探活，30 秒不健康自动注销 |
| **负载均衡** | 客户端随机/轮询选择实例 |

---

## 5. API 网关

### 5.1 网关的职责：统一入口 + 横切关注点

```
API 网关做什么？

  客户端 → API 网关 → 微服务

  核心职责：
  ✅ 路由转发：/api/users → user-service，/api/orders → order-service
  ✅ 认证鉴权：统一验证 JWT，不需要每个服务都验
  ✅ 限流熔断：保护后端服务不被打爆
  ✅ 请求聚合：一个请求扇出到多个服务，聚合结果返回
  ✅ 协议转换：对外 REST，对内 gRPC
  ✅ 日志追踪：统一注入 Request ID
```

### 5.2 用 FastAPI 构建简易网关

```python
from fastapi import FastAPI, Request
import httpx

app = FastAPI(title="API Gateway")

# 路由映射表
ROUTE_MAP = {
    "/api/v1/users": "http://user-service:8001",
    "/api/v1/orders": "http://order-service:8002",
    "/api/v1/products": "http://product-service:8003",
}

@app.api_route("/api/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_proxy(service: str, path: str, request: Request):
    """通用反向代理"""
    target_base = ROUTE_MAP.get(f"/api/v1/{service}")
    if not target_base:
        return JSONResponse({"error": "服务不存在"}, status_code=404)
    
    target_url = f"{target_base}/api/v1/{service}/{path}"
    
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=request.method,
            url=target_url,
            headers={k: v for k, v in request.headers.items() if k != "host"},
            content=await request.body(),
            params=request.query_params,
        )
    
    return Response(content=resp.content, status_code=resp.status_code,
                    headers=dict(resp.headers))
```

### 5.3 认证统一处理（JWT 透传）

```python
from app.utils.security import decode_token

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """网关级统一认证"""
    # 白名单（不需要认证的路径）
    public_paths = ["/api/v1/auth/login", "/api/v1/auth/register", "/health"]
    if request.url.path in public_paths:
        return await call_next(request)
    
    # 解析 Token
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return JSONResponse({"error": "未登录"}, status_code=401)
    
    try:
        payload = decode_token(token)
        # 将用户信息注入 Header 透传给后端服务
        request.state.user_id = payload["sub"]
        request.headers.__dict__["_list"].append(
            (b"x-user-id", str(payload["sub"]).encode())
        )
    except Exception:
        return JSONResponse({"error": "Token 无效"}, status_code=401)
    
    return await call_next(request)
```

### 5.4 请求聚合：一个请求调多个服务

```python
import asyncio

@app.get("/api/v1/dashboard")
async def dashboard(request: Request):
    """首页聚合接口：并行调 3 个服务"""
    user_id = request.state.user_id
    
    async with httpx.AsyncClient() as client:
        user_task = client.get(f"http://user-service:8001/api/v1/users/{user_id}")
        orders_task = client.get(f"http://order-service:8002/api/v1/orders?user_id={user_id}&limit=5")
        stats_task = client.get(f"http://product-service:8003/api/v1/stats/hot")
        
        user_resp, orders_resp, stats_resp = await asyncio.gather(
            user_task, orders_task, stats_task
        )
    
    return {
        "user": user_resp.json(),
        "recent_orders": orders_resp.json(),
        "hot_products": stats_resp.json(),
    }
```

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **网关职责** | 路由 + 认证 + 限流 + 聚合 + 追踪 |
| **反向代理** | FastAPI 通用路由 → httpx 转发 |
| **JWT 透传** | 网关验 Token，Header 注入 user_id 给后端 |
| **请求聚合** | asyncio.gather 并行扇出，减少前端请求次数 |

---

## 6. 分布式事务与数据一致性

### 6.1 分布式事务的难题（CAP 定理）

```
CAP 定理：分布式系统只能同时满足其中两个

  C（一致性）：所有节点看到的数据相同
  A（可用性）：每个请求都能得到响应
  P（分区容忍）：网络分区时系统仍能工作

  微服务选择：AP + 最终一致性
  → 允许短暂的数据不一致，但最终会一致
  → 用 Saga 模式替代分布式事务
```

### 6.2 Saga 模式：编排型 vs 协调型

```python
# ── 编排型 Saga（中央协调器）──
class OrderSaga:
    """下单 Saga：创建订单 → 扣库存 → 扣款"""
    
    async def execute(self, order_data: dict):
        saga_id = str(uuid.uuid4())
        
        try:
            # Step 1: 创建订单（状态=待支付）
            order = await order_service.create(order_data, status="pending")
            
            # Step 2: 扣减库存
            await inventory_service.reserve(order.product_id, order.quantity)
            
            # Step 3: 扣款
            await payment_service.charge(order.user_id, order.amount)
            
            # 全部成功 → 更新订单状态
            await order_service.update_status(order.id, "paid")
            
        except InventoryError:
            # 库存不足 → 取消订单
            await order_service.update_status(order.id, "cancelled")
            
        except PaymentError:
            # 支付失败 → 释放库存 + 取消订单
            await inventory_service.release(order.product_id, order.quantity)
            await order_service.update_status(order.id, "cancelled")
```

```
协调型 Saga（事件驱动）：

  订单服务 → 发布 "order.created" 事件
       ↓
  库存服务 → 监听事件 → 扣库存 → 发布 "inventory.reserved"
       ↓
  支付服务 → 监听事件 → 扣款 → 发布 "payment.completed"
       ↓
  订单服务 → 监听事件 → 更新状态为 "paid"

  失败时反向补偿：
  支付失败 → 发布 "payment.failed" → 库存服务释放 → 订单取消
```

### 6.3 事件驱动架构：发布-订阅

```python
class EventBus:
    """简易事件总线"""
    
    async def publish(self, event_type: str, data: dict):
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }
        await self.mq.publish("events", json.dumps(message), routing_key=event_type)
    
    async def subscribe(self, event_type: str, handler):
        async def callback(message):
            event = json.loads(message.body)
            await handler(event["data"])
        
        await self.mq.subscribe("events", event_type, callback)
```

### 6.4 幂等性设计：重复请求不出错

```python
class IdempotencyGuard:
    """幂等性保护（用 Redis 记录已处理的请求）"""
    
    async def check_and_mark(self, idempotency_key: str, ttl: int = 3600) -> bool:
        """检查是否是重复请求"""
        result = await redis.set(f"idem:{idempotency_key}", "1", ex=ttl, nx=True)
        return result is not None  # True=首次，False=重复

# 使用
@router.post("/orders")
async def create_order(data: OrderCreate, idempotency_key: str = Header(None)):
    if idempotency_key:
        is_new = await guard.check_and_mark(idempotency_key)
        if not is_new:
            return {"message": "重复请求，已忽略"}
    
    return await order_saga.execute(data.dict())
```

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **CAP** | 微服务选 AP + 最终一致性 |
| **Saga 编排** | 中央协调器串行调用 + 失败补偿 |
| **Saga 协调** | 事件驱动，每个服务自己监听和发布 |
| **幂等性** | Redis NX 标记已处理的请求 |

---

## 7. 可观测性：日志、追踪、监控

### 7.1 分布式追踪（OpenTelemetry）

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def setup_tracing(service_name: str):
    """配置 OpenTelemetry 分布式追踪"""
    provider = TracerProvider()
    provider.add_span_processor(
        BatchSpanProcessor(JaegerExporter(agent_host_name="jaeger", agent_port=6831))
    )
    trace.set_tracer_provider(provider)

# 自动注入追踪（一行代码接入）
FastAPIInstrumentor.instrument_app(app)     # FastAPI 入口
HTTPXClientInstrumentor().instrument()       # httpx 出口调用

# 手动创建 Span（业务关键路径）
tracer = trace.get_tracer("order-service")

async def create_order(data: dict):
    with tracer.start_as_current_span("create_order") as span:
        span.set_attribute("user_id", data["user_id"])
        span.set_attribute("product_id", data["product_id"])
        order = await order_repo.create(**data)
        span.set_attribute("order_id", order.id)
        return order
```

### 7.2 统一日志聚合（ELK / Loki）

```python
# 日志格式：JSON + trace_id（和追踪串联）
import logging
from opentelemetry import trace

class TraceIDFilter(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        ctx = span.get_span_context()
        record.trace_id = format(ctx.trace_id, "032x") if ctx.trace_id else ""
        record.span_id = format(ctx.span_id, "016x") if ctx.span_id else ""
        return True

# 日志输出带 trace_id，方便在 Jaeger/ELK 中关联
# {"timestamp":"...","level":"INFO","trace_id":"abc123","message":"订单创建成功"}
```

### 7.3 Prometheus + Grafana 监控

```python
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

# 定义指标
REQUEST_COUNT = Counter("http_requests_total", "请求总数", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "请求耗时", ["method", "path"])

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        
        REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
        
        return response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

### 7.4 告警规则与 SLA 管理

```yaml
# Prometheus 告警规则
groups:
  - name: microservice_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "{{ $labels.service }} 错误率超过 5%"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        annotations:
          summary: "{{ $labels.service }} P95 延迟超过 2 秒"
      
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        annotations:
          summary: "{{ $labels.instance }} 服务不可用"
```

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **OpenTelemetry** | 统一追踪标准，自动/手动 Span |
| **trace_id 串联** | 日志里带 trace_id，和追踪系统关联 |
| **Prometheus** | Counter/Histogram 指标 + /metrics |
| **告警** | 错误率 > 5%、P95 > 2s、服务下线 |

---

## 8. 容错与弹性设计

### 8.1 服务雪崩与熔断器模式

```python
import time

class CircuitBreaker:
    """熔断器：连续失败 N 次后断开，停止调用下游"""
    
    CLOSED = "closed"       # 正常
    OPEN = "open"           # 熔断中（拒绝请求）
    HALF_OPEN = "half_open" # 试探中（放少量请求）
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.state = self.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
    
    async def call(self, func, *args, **kwargs):
        if self.state == self.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = self.HALF_OPEN  # 尝试恢复
            else:
                raise CircuitBreakerOpen("熔断中，请稍后重试")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failure_count = 0
        self.state = self.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN

# 使用
payment_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

async def charge_user(user_id, amount):
    return await payment_breaker.call(payment_service.charge, user_id, amount)
```

### 8.2 重试策略：指数退避 + 抖动

```python
import asyncio
import random

async def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """指数退避重试 + 随机抖动"""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            delay = base_delay * (2 ** attempt)            # 1s, 2s, 4s
            jitter = random.uniform(0, delay * 0.5)        # 随机抖动
            logger.warning(f"重试 {attempt+1}/{max_retries}，等待 {delay+jitter:.1f}s")
            await asyncio.sleep(delay + jitter)
```

### 8.3 降级方案：缓存兜底 / 默认值

```python
async def get_product_with_fallback(product_id: int):
    """降级策略：服务不可用时返回缓存数据"""
    try:
        return await product_client.get_product(product_id)
    except (httpx.ConnectError, CircuitBreakerOpen):
        # 降级 1：从缓存读取
        cached = await redis.get(f"product:{product_id}")
        if cached:
            logger.warning(f"商品服务不可用，使用缓存数据: {product_id}")
            return json.loads(cached)
        
        # 降级 2：返回默认值
        logger.error(f"商品服务不可用，无缓存: {product_id}")
        return {"id": product_id, "name": "商品信息暂时不可用", "price": 0}
```

### 8.4 超时控制：全链路 Timeout 传递

```python
async def order_with_timeout(data: dict, deadline: float = 5.0):
    """全链路超时：总超时 5 秒，分配给各子调用"""
    start = time.time()
    remaining = deadline
    
    # Step 1: 创建订单（最多 1 秒）
    order = await asyncio.wait_for(order_repo.create(**data), timeout=min(1.0, remaining))
    remaining = deadline - (time.time() - start)
    
    # Step 2: 扣库存（用剩余时间）
    await asyncio.wait_for(
        inventory_client.reserve(order.product_id, order.quantity),
        timeout=min(2.0, remaining),
    )
    remaining = deadline - (time.time() - start)
    
    # Step 3: 扣款（用剩余时间）
    await asyncio.wait_for(
        payment_client.charge(order.user_id, order.amount),
        timeout=remaining,
    )
    
    return order
```

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **熔断器** | 连续失败 5 次 → 断开 30 秒 → 半开试探 |
| **指数退避** | 1s→2s→4s + 随机抖动，避免同时重试 |
| **降级** | 缓存兜底 → 默认值，服务不可用也不报错 |
| **超时传递** | 总超时按比例分配给各子调用 |

---

## 9. 容器化部署与编排

### 9.1 每个服务一个 Docker 镜像

```dockerfile
# services/order-service/Dockerfile
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/
EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### 9.2 Docker Compose 本地编排

```yaml
# docker-compose.yml
services:
  gateway:
    build: ./services/gateway
    ports: ["8000:8000"]
    depends_on: [user-service, order-service, product-service]

  user-service:
    build: ./services/user-service
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@user-db:5432/users
    depends_on: [user-db]

  order-service:
    build: ./services/order-service
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@order-db:5432/orders
    depends_on: [order-db, rabbitmq]

  product-service:
    build: ./services/product-service
    depends_on: [product-db]

  user-db:
    image: postgres:16
    environment: { POSTGRES_DB: users, POSTGRES_USER: user, POSTGRES_PASSWORD: pass }

  order-db:
    image: postgres:16
    environment: { POSTGRES_DB: orders, POSTGRES_USER: user, POSTGRES_PASSWORD: pass }

  product-db:
    image: postgres:16
    environment: { POSTGRES_DB: products, POSTGRES_USER: user, POSTGRES_PASSWORD: pass }

  rabbitmq:
    image: rabbitmq:3-management
    ports: ["15672:15672"]

  consul:
    image: consul:1.15
    ports: ["8500:8500"]

  jaeger:
    image: jaegertracing/all-in-one
    ports: ["16686:16686"]
```

### 9.3 Kubernetes 基础：Pod / Service / Deployment

```yaml
# k8s/order-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
spec:
  replicas: 3
  selector:
    matchLabels: { app: order-service }
  template:
    metadata:
      labels: { app: order-service }
    spec:
      containers:
        - name: order-service
          image: registry.example.com/order-service:latest
          ports: [{ containerPort: 8002 }]
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef: { name: order-secrets, key: database-url }
          readinessProbe:
            httpGet: { path: /health, port: 8002 }
            initialDelaySeconds: 5
          resources:
            requests: { cpu: 100m, memory: 256Mi }
            limits: { cpu: 500m, memory: 512Mi }
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  selector: { app: order-service }
  ports: [{ port: 8002, targetPort: 8002 }]
```

### 9.4 CI/CD Pipeline（GitHub Actions → K8s）

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push: { branches: [main] }

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build & Push
        run: |
          docker build -t registry.example.com/order-service:${{ github.sha }} .
          docker push registry.example.com/order-service:${{ github.sha }}
      
      - name: Deploy to K8s
        run: |
          kubectl set image deployment/order-service \
            order-service=registry.example.com/order-service:${{ github.sha }}
          kubectl rollout status deployment/order-service
```

**第 9 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Docker** | 多阶段构建，每个服务独立镜像 |
| **Compose** | 本地开发一键启动全部服务 |
| **K8s** | Deployment(副本数) + Service(服务发现) + Probe(健康检查) |
| **CI/CD** | Push → Build → Push Image → kubectl set image |

---

## 10. 实战案例：电商微服务系统

### 10.1 系统架构设计

```
电商微服务架构：

  客户端（Web/App）
      │
  ┌───┴───────────────────────────────┐
  │           API Gateway              │
  │  认证 │ 路由 │ 限流 │ 聚合         │
  └───┬───────┬───────┬───────┬───────┘
      │       │       │       │
  ┌───┴──┐ ┌─┴────┐ ┌┴─────┐ ┌┴─────┐
  │ User │ │Product│ │Order │ │Payment│
  │ :8001│ │ :8003 │ │:8002 │ │ :8004 │
  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
     │        │        │        │
  ┌──┴──┐ ┌──┴──┐ ┌───┴──┐ ┌──┴──┐
  │UserDB│ │ProdDB│ │OrdDB │ │PayDB│
  └─────┘ └─────┘ └──────┘ └─────┘
               │
           RabbitMQ（事件总线）
```

### 10.2 核心服务实现（用户/商品/订单/支付）

```python
# ── 订单服务（核心：串联其他服务）──
class OrderService:
    def __init__(self, db, user_client, product_client, 
                 payment_client, inventory_client, event_bus):
        self.db = db
        self.user_client = user_client
        self.product_client = product_client
        self.payment_client = payment_client
        self.inventory_client = inventory_client
        self.event_bus = event_bus
    
    async def create_order(self, user_id: int, product_id: int, quantity: int):
        # 1. 验证用户
        user = await self.user_client.get_user(user_id)
        
        # 2. 获取商品信息 + 计算金额
        product = await self.product_client.get_product(product_id)
        amount = product["price"] * quantity
        
        # 3. 创建订单（状态=pending）
        order = await self.order_repo.create(
            user_id=user_id, product_id=product_id,
            quantity=quantity, amount=amount, status="pending",
        )
        
        # 4. 扣库存
        await self.inventory_client.reserve(product_id, quantity)
        
        # 5. 扣款
        await self.payment_client.charge(user_id, amount, order_id=order.id)
        
        # 6. 更新状态
        await self.order_repo.update(order.id, status="paid")
        
        # 7. 发布事件
        await self.event_bus.publish("order.paid", {
            "order_id": order.id, "user_id": user_id, "amount": amount,
        })
        
        return order
```

### 10.3 服务间调用流程

```
下单完整链路：

  用户点击"购买" 
    → Gateway 认证 JWT → 路由到 Order Service
      → Order Service
        ├─ GET  User Service     /users/123       (验证用户)
        ├─ GET  Product Service  /products/456    (获取商品)
        ├─ POST Inventory Service /reserve         (扣库存)
        ├─ POST Payment Service   /charge          (扣款)
        ├─ UPDATE Order DB        (status=paid)
        └─ PUBLISH RabbitMQ       "order.paid"
             ├─ Notification Service → 发短信
             └─ Analytics Service   → 记录统计

  耗时分布：
    Gateway 认证:    ~5ms
    User Service:    ~20ms
    Product Service: ~15ms
    Inventory:       ~30ms
    Payment:         ~200ms （最慢，外部支付接口）
    DB + MQ:         ~10ms
    总计:            ~280ms
```

### 10.4 部署与压测结果

```
压测结果（4 核 8G × 3 节点，每服务 3 副本）：

  ┌─────────────┬────────┬────────┬────────┐
  │ 指标         │ 目标    │ 实际    │ 状态   │
  ├─────────────┼────────┼────────┼────────┤
  │ QPS         │ > 500  │ 680    │ ✅     │
  │ P50 延迟    │ < 200ms│ 150ms  │ ✅     │
  │ P95 延迟    │ < 500ms│ 420ms  │ ✅     │
  │ P99 延迟    │ < 1s   │ 780ms  │ ✅     │
  │ 错误率      │ < 1%   │ 0.3%   │ ✅     │
  │ 可用性      │ 99.9%  │ 99.95% │ ✅     │
  └─────────────┴────────┴────────┴────────┘
```

**第 10 章核心知识回顾：**

| 阶段 | 做了什么 |
|:---|:---|
| **架构** | 4 核心服务 + 网关 + MQ + 独立 DB |
| **实现** | OrderService 串联 User/Product/Inventory/Payment |
| **调用链** | 总耗时 ~280ms，Payment 最慢(200ms) |
| **压测** | 680 QPS、P95 420ms、可用性 99.95% |

---

## 附录

### A. 微服务 vs 单体 决策矩阵

| 维度 | 选单体 | 选微服务 |
|:---|:---|:---|
| **团队规模** | < 5 人 | > 10 人 |
| **业务复杂度** | 域边界不清晰 | 域边界明确 |
| **发布频率** | 一周一次 | 每天多次独立发布 |
| **扩展需求** | 整体流量均匀 | 某模块流量激增 |
| **技术栈** | 统一即可 | 需要多语言/多框架 |
| **DevOps** | 没有容器化能力 | 有 CI/CD + K8s |
| **运维成本** | 尽量低 | 可以投入 |

### B. Python 微服务框架对比

| 框架 | 定位 | 异步 | gRPC | 适用场景 |
|:---|:---|:---|:---|:---|
| **FastAPI** | Web API | ✅ 原生 | 需要额外集成 | 通用首选 |
| **Nameko** | 微服务专用 | ❌ | 内置 RPC | 小型微服务 |
| **gRPC Python** | RPC 框架 | ✅ aio | 原生 | 高性能内部通信 |
| **Flask** | Web API | ❌ 需扩展 | 需要额外集成 | 简单场景 |
| **Robyn** | 高性能 | ✅ Rust | 需要额外集成 | 性能极致 |

### C. 常见踩坑与解决方案

| 踩坑 | 现象 | 解决 |
|:---|:---|:---|
| **分布式事务** | 扣款成功但库存没扣 | Saga 模式 + 补偿事务 |
| **服务雪崩** | 一个服务慢拖垮所有 | 熔断器 + 超时 + 降级 |
| **数据不一致** | 订单和库存数据对不上 | 事件溯源 + 定期对账 |
| **调试困难** | 不知道请求挂在哪里 | OpenTelemetry 分布式追踪 |
| **配置管理** | 每个服务的配置散落各处 | Consul KV / 配置中心 |
| **版本兼容** | 新旧服务 API 不兼容 | API 版本管理(/v1/ /v2/) |
| **日志追踪** | 日志找不到关联 | 统一 trace_id 贯穿全链路 |
| **网络延迟** | 服务间调用加起来太慢 | 并行调用 + 缓存 + gRPC |
