# API 设计最佳实践

> 从 URL 到文档——涵盖 RESTful 设计规范、URL 命名、HTTP 方法语义、请求响应设计、分页过滤排序、错误码体系、版本管理、认证方案、限流策略、OpenAPI 文档自动化，一套完整的生产级 API 设计方法论。

---

## 1. RESTful 设计核心原则

### 1.1 REST 不是规范，是约束

```
REST（Representational State Transfer）的 6 个约束：

  ① 客户端-服务端分离：前后端独立演化
  ② 无状态：每个请求包含所有信息，服务端不存会话
  ③ 可缓存：响应明确标记是否可缓存
  ④ 统一接口：资源通过 URL 标识，用 HTTP 方法操作
  ⑤ 分层系统：客户端不知道直连的是服务还是代理
  ⑥ 按需代码（可选）：服务端可以返回可执行代码

  核心思想：用 HTTP 协议本身的语义来设计 API
  → URL = 资源地址，Method = 操作，Status Code = 结果
```

### 1.2 资源思维：一切皆资源

```
❌ 动词思维（RPC 风格）：
  POST /createUser
  POST /getUserById
  POST /updateUserName
  POST /deleteUser

✅ 资源思维（REST 风格）：
  POST   /users          创建用户
  GET    /users/123      获取用户
  PATCH  /users/123      更新用户
  DELETE /users/123      删除用户

  资源 = 名词（users, orders, articles）
  操作 = HTTP 方法（GET, POST, PUT, PATCH, DELETE）
```

### 1.3 HTTP 方法语义（GET/POST/PUT/PATCH/DELETE）

| 方法 | 语义 | 幂等 | 安全 | 示例 |
|:---|:---|:---|:---|:---|
| **GET** | 查询 | ✅ | ✅ | GET /users/123 |
| **POST** | 创建 | ❌ | ❌ | POST /users |
| **PUT** | 全量更新 | ✅ | ❌ | PUT /users/123 |
| **PATCH** | 部分更新 | ✅ | ❌ | PATCH /users/123 |
| **DELETE** | 删除 | ✅ | ❌ | DELETE /users/123 |

```
幂等 = 执行多次结果相同
  GET    /users/123  → 多次查询结果一样 ✅
  DELETE /users/123  → 删了就删了，再删还是不存在 ✅
  POST   /users      → 多次提交创建多个用户 ❌

安全 = 不修改数据
  GET 是安全的（只读），其他都不安全
```

### 1.4 状态码用对了吗？

```
常用状态码（按场景分组）：

  成功：
    200 OK           → 通用成功
    201 Created      → 创建成功（POST）
    204 No Content   → 成功但无返回体（DELETE）

  客户端错误：
    400 Bad Request  → 参数错误
    401 Unauthorized → 未认证（没登录）
    403 Forbidden    → 无权限（登录了但没权限）
    404 Not Found    → 资源不存在
    409 Conflict     → 冲突（如邮箱已注册）
    422 Unprocessable→ 校验失败（Pydantic）
    429 Too Many     → 限流

  服务端错误：
    500 Internal     → 服务器异常
    502 Bad Gateway  → 上游服务挂了
    503 Unavailable  → 服务维护中
```

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **REST** | 用 HTTP 协议语义设计 API |
| **资源思维** | URL=名词，Method=动词 |
| **幂等性** | GET/PUT/DELETE 幂等，POST 不幂等 |
| **状态码** | 2xx 成功、4xx 客户端错、5xx 服务端错 |

---

## 2. URL 设计规范

### 2.1 URL 命名规则：名词复数、小写连字符

```
URL 命名 7 条规则：

  ✅ 名词复数：/users  /orders  /articles
  ✅ 小写字母：/user-profiles（不是 /UserProfiles）
  ✅ 连字符分词：/order-items（不是 /order_items）
  ✅ 不带文件后缀：/users（不是 /users.json）
  ✅ 不带动词：GET /users（不是 GET /getUsers）
  ✅ 不带版本在资源里：/v1/users（不是 /users-v1）
  ✅ 不超过 3 层嵌套：/users/123/orders（不是 /users/123/orders/456/items/789）
```

### 2.2 资源层级与嵌套关系

```
嵌套表示从属关系：

  GET  /users/123/orders          用户 123 的所有订单
  POST /users/123/orders          为用户 123 创建订单
  GET  /users/123/orders/456      用户 123 的订单 456

  ⚠️ 不要超过 2 层嵌套：
  ❌ /users/123/orders/456/items/789/reviews
  ✅ /order-items/789/reviews（扁平化）

  经验法则：
  - 子资源有独立 ID → 顶级资源（/orders/456）
  - 子资源必须依赖父资源 → 嵌套（/users/123/addresses）
```

### 2.3 动作型接口怎么设计？

```
有些操作确实不是 CRUD，怎么办？

  方案 1：用子资源表示状态变更
    POST /orders/123/cancel        取消订单
    POST /orders/123/pay           支付订单
    POST /users/123/activate       激活用户

  方案 2：当作资源创建
    POST /payments  {order_id: 123}  创建支付（= 支付订单）
    POST /refunds   {order_id: 123}  创建退款

  方案 3：用 PATCH + 状态字段（Pragmatics）
    PATCH /orders/123  {"status": "cancelled"}
```

### 2.4 URL 设计反模式

```
❌ 常见错误：

  /getUser?id=123         → GET /users/123
  /user/list              → GET /users
  /user/delete/123        → DELETE /users/123
  /api/v1/User            → /api/v1/users（复数+小写）
  /users/123/orders/456/items/789/reviews/12
                          → /reviews/12（扁平化）
```

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **命名** | 名词复数、小写、连字符 |
| **嵌套** | 最多 2 层，有独立 ID→顶级资源 |
| **动作** | 子资源 POST 或 PATCH 状态 |
| **反模式** | 不要动词、不要大写、不要深嵌套 |

---

## 3. 请求设计

### 3.1 参数应该放哪？Path / Query / Body

| 位置 | 用途 | 示例 |
|:---|:---|:---|
| **Path** | 资源标识（必填） | /users/**123** |
| **Query** | 过滤/分页/排序（可选） | /users?**role=admin&page=2** |
| **Body** | 创建/更新的数据 | POST /users `{"name":"Alice"}` |
| **Header** | 认证/元数据 | Authorization: Bearer xxx |

```
规则：
  - 资源 ID → Path（/users/123）
  - 筛选条件 → Query（?status=active）
  - 创建/更新的数据 → Body（JSON）
  - 认证/版本/格式 → Header
```

### 3.2 请求体设计与 Content-Type

```python
# 创建资源：只传必要字段
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

# 更新资源：所有字段可选（PATCH 语义）
class UserUpdate(BaseModel):
    username: str | None = None
    avatar: str | None = None
    bio: str | None = None

# Content-Type
# application/json   → 结构化数据（99% 场景）
# multipart/form-data → 文件上传
# application/x-www-form-urlencoded → 表单（少用）
```

### 3.3 幂等性设计：重复请求不出错

```python
# 用 Idempotency-Key 防止重复创建
@router.post("/orders")
async def create_order(data: OrderCreate, 
                       idempotency_key: str = Header(None)):
    if idempotency_key:
        cached = await redis.get(f"idem:{idempotency_key}")
        if cached:
            return json.loads(cached)  # 返回缓存结果
    
    order = await order_service.create(data)
    
    if idempotency_key:
        await redis.setex(f"idem:{idempotency_key}", 3600, 
                          json.dumps(order.dict()))
    return order
```

### 3.4 批量操作接口设计

```python
# 批量查询
GET /users?ids=1,2,3,4,5

# 批量创建
POST /users/batch
[{"name": "Alice"}, {"name": "Bob"}]

# 批量更新
PATCH /users/batch
[{"id": 1, "status": "active"}, {"id": 2, "status": "banned"}]

# 批量删除
DELETE /users/batch
{"ids": [1, 2, 3]}
```

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **参数位置** | ID→Path，过滤→Query，数据→Body |
| **PATCH** | 部分更新，字段可选 |
| **幂等性** | Idempotency-Key + Redis 缓存 |
| **批量** | /resource/batch + 数组 |

---

## 4. 响应设计

### 4.1 统一响应格式

```python
# 方案一：直接返回数据（推荐，简洁）
# 成功
{"id": 1, "username": "alice", "email": "alice@example.com"}

# 方案二：包装格式（适合需要额外元数据）
{
    "code": 0,
    "message": "success",
    "data": {"id": 1, "username": "alice"},
    "timestamp": "2025-01-01T12:00:00Z"
}

# 列表响应（带分页信息）
{
    "items": [{"id": 1}, {"id": 2}],
    "total": 100,
    "page": 1,
    "page_size": 20
}
```

### 4.2 嵌套层级控制与字段选择

```python
# 控制嵌套深度：默认只返回 ID，需要时展开
# GET /orders/123
{"id": 123, "user_id": 456, "product_id": 789}

# GET /orders/123?expand=user,product
{"id": 123, 
 "user": {"id": 456, "username": "alice"},
 "product": {"id": 789, "name": "iPhone"}}

# 字段选择：只返回需要的字段
# GET /users?fields=id,username,avatar
[{"id": 1, "username": "alice", "avatar": "url..."}]
```

### 4.3 空值处理：null vs 不返回

```
两种策略：

  策略 1：null 字段也返回（推荐，前端好处理）
  {"id": 1, "username": "alice", "bio": null, "avatar": null}

  策略 2：null 字段不返回（省带宽）
  {"id": 1, "username": "alice"}

  Pydantic 控制：
  model_config = ConfigDict(exclude_none=True)  # 不返回 None
```

### 4.4 HATEOAS：响应中带链接

```python
# HATEOAS = 响应中告诉客户端"下一步能做什么"
{
    "id": 123,
    "status": "pending",
    "_links": {
        "self": "/orders/123",
        "pay": "/orders/123/pay",
        "cancel": "/orders/123/cancel",
        "user": "/users/456"
    }
}
# 适合公开 API（如 GitHub API），内部 API 可选
```

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **统一格式** | 单个返回对象，列表返回 items+total |
| **expand** | 按需展开关联资源 |
| **fields** | 只返回需要的字段 |
| **HATEOAS** | 响应含链接，告诉客户端下一步 |

---

## 5. 分页、过滤与排序

### 5.1 Offset 分页 vs Cursor 分页

```
Offset 分页（传统）：
  GET /users?page=3&page_size=20
  → SQL: LIMIT 20 OFFSET 40
  ✅ 简单，支持跳页
  ❌ 深翻页性能差（OFFSET 10000 很慢）

Cursor 分页（推荐）：
  GET /users?cursor=eyJpZCI6MTAwfQ&limit=20
  → SQL: WHERE id > 100 LIMIT 20
  ✅ 性能稳定，适合无限滚动
  ❌ 不支持跳页
```

### 5.2 过滤参数设计

```
简单过滤（等值查询）：
  GET /users?role=admin&status=active

范围过滤：
  GET /orders?created_after=2025-01-01&created_before=2025-12-31
  GET /products?price_min=100&price_max=500

模糊搜索：
  GET /users?search=alice

多值过滤：
  GET /users?role=admin,editor（逗号分隔 = OR）
```

### 5.3 排序参数设计

```
单字段排序：
  GET /users?sort=created_at       升序
  GET /users?sort=-created_at      降序（前缀 -）

多字段排序：
  GET /users?sort=-created_at,username
  → ORDER BY created_at DESC, username ASC
```

### 5.4 FastAPI 实现完整示例

```python
from fastapi import Query

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("-created_at"),
    db: AsyncSession = Depends(get_db),
):
    query = select(User)
    
    # 过滤
    if role:
        query = query.where(User.role == role)
    if status:
        query = query.where(User.status == status)
    if search:
        query = query.where(User.username.ilike(f"%{search}%"))
    
    # 排序
    for field in sort.split(","):
        desc = field.startswith("-")
        col = getattr(User, field.lstrip("-"), None)
        if col:
            query = query.order_by(col.desc() if desc else col.asc())
    
    # 总数
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.scalars(query)
    
    return {"items": result.all(), "total": total, "page": page, "page_size": page_size}
```

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Offset** | page+page_size，简单但深翻页慢 |
| **Cursor** | 基于 ID 翻页，性能稳定 |
| **过滤** | 等值/范围/模糊 Query 参数 |
| **排序** | sort=-created_at，- 前缀表示降序 |

---

## 6. 错误码体系

### 6.1 HTTP 状态码速查与正确使用

```
最常犯的错误：

  ❌ 所有错误都返回 200 + {"code": -1, "message": "失败"}
  ❌ 参数错误返回 500（应该 400）
  ❌ 未登录返回 403（应该 401）
  ❌ 创建成功返回 200（应该 201）

  401 vs 403：
    401 = 你是谁？（没登录 / Token 无效）
    403 = 你没权限（登录了但不够格）
```

### 6.2 业务错误码设计（5 位编码）

```
5 位错误码规范：

  1XXXX = 用户模块
    10001 = 邮箱已注册
    10002 = 密码错误
    10003 = 用户不存在
    10004 = 账户已锁定

  2XXXX = 订单模块
    20001 = 订单不存在
    20002 = 库存不足
    20003 = 订单已取消

  3XXXX = 支付模块
    30001 = 余额不足
    30002 = 支付超时
```

### 6.3 统一错误响应格式

```python
# 统一错误格式
{
    "error": {
        "code": 10001,
        "message": "邮箱已注册",
        "details": "alice@example.com 已被其他账号使用",
        "doc_url": "https://docs.example.com/errors/10001"
    }
}

# Pydantic 模型
class ErrorResponse(BaseModel):
    code: int
    message: str
    details: str | None = None
    doc_url: str | None = None
```

### 6.4 FastAPI 全局异常处理

```python
class AppError(Exception):
    def __init__(self, code: int, message: str, status: int = 400, details: str = None):
        self.code = code
        self.message = message
        self.status = status
        self.details = details

@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    return JSONResponse(status_code=exc.status, content={
        "error": {"code": exc.code, "message": exc.message, "details": exc.details}
    })

@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc):
    return JSONResponse(status_code=422, content={
        "error": {"code": 40001, "message": "参数校验失败",
                  "details": str(exc.errors())}
    })

# 使用
raise AppError(10001, "邮箱已注册", 409, f"{email} 已被使用")
```

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **401 vs 403** | 没登录 vs 没权限 |
| **5 位错误码** | 模块(1位) + 编号(4位) |
| **统一格式** | {error: {code, message, details}} |
| **全局处理** | exception_handler 统一异常 |

---

## 7. API 版本管理

### 7.1 为什么需要版本管理？

```
API 演进不可避免：

  ❌ 直接改字段名 → 所有客户端崩溃
  ❌ 直接删字段 → 旧版 App 白屏
  ❌ 改变参数含义 → 数据错乱

  版本管理 = 给客户端升级窗口
  → 旧版本继续用，新版本另开
  → 等旧版本用户都迁完了再下线
```

### 7.2 三种版本策略对比

| 策略 | 示例 | 优点 | 缺点 |
|:---|:---|:---|:---|
| **URL 路径** | /api/v1/users | 直观，易切换 | URL 不够"纯净" |
| **Header** | Accept: application/vnd.api.v1+json | URL 干净 | 调试不方便 |
| **Query** | /users?version=1 | 简单 | 可能被缓存忽略 |

```python
# 推荐：URL 路径（最常用）
from fastapi import APIRouter

v1 = APIRouter(prefix="/api/v1")
v2 = APIRouter(prefix="/api/v2")

@v1.get("/users/{id}")
async def get_user_v1(id: int):
    return {"id": id, "name": "Alice"}

@v2.get("/users/{id}")
async def get_user_v2(id: int):
    return {"id": id, "username": "Alice", "avatar": "url..."}

app.include_router(v1)
app.include_router(v2)
```

### 7.3 向后兼容的 API 变更

```
✅ 向后兼容（不用新版本）：
  - 新增可选字段
  - 新增新的端点
  - 在响应中添加新字段
  - 放宽参数验证

❌ 不向后兼容（必须新版本）：
  - 删除字段
  - 重命名字段
  - 改变字段类型
  - 改变 URL 路径
  - 增加必填参数
```

### 7.4 API 废弃与迁移流程

```
废弃三步走：

  1. 标记废弃（保持可用）
     Deprecation: true
     Sunset: Sat, 01 Jul 2025 00:00:00 GMT

  2. 提供迁移指南
     文档中标注：v1 → v2 的变更内容
     在响应 Header 中带 Link: </api/v2/users>; rel="successor-version"

  3. 下线（至少 6 个月后）
     返回 410 Gone + 迁移链接
```

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **URL 版本** | /api/v1/resource，最常用 |
| **兼容变更** | 新增字段/端点 OK，删改不行 |
| **废弃流程** | 标记→迁移指南→6 个月后下线 |
| **Sunset** | Header 告诉客户端下线日期 |

---

## 8. 认证与安全

### 8.1 API 认证方案选型

| 场景 | 推荐方案 |
|:---|:---|
| 用户登录后操作 | JWT Bearer Token |
| 第三方开发者 | OAuth2 + API Key |
| 服务间调用 | 客户端凭证 / mTLS |
| Webhook 回调 | HMAC 签名验证 |
| 内网服务 | API Key / 网络隔离 |

### 8.2 API Key 管理最佳实践

```python
# API Key 设计规范
# 格式：前缀 + 随机字符（易识别来源）
# sk_live_a1b2c3d4e5f6g7h8   → 生产密钥
# sk_test_a1b2c3d4e5f6g7h8   → 测试密钥

import secrets

def generate_api_key(prefix: str = "sk_live") -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"

# 存储：只存哈希（和密码一样不能明文存）
# 传输：放 Header（不放 URL，避免日志泄露）
# Authorization: Bearer sk_live_xxx
```

### 8.3 请求限流（Rate Limiting）

```python
# 限流响应 Header（告诉客户端限流状态）
# X-RateLimit-Limit: 100        总额度
# X-RateLimit-Remaining: 42     剩余次数
# X-RateLimit-Reset: 1700000000 重置时间

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/users")
@limiter.limit("100/minute")   # 每分钟 100 次
async def list_users(request: Request):
    ...

# 超限返回 429 Too Many Requests
# {"error": {"code": 42900, "message": "请求过于频繁，请稍后重试"}}
```

### 8.4 CORS 与安全 Header

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(CORSMiddleware,
    allow_origins=["https://app.example.com"],  # 不要用 *
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)
```

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **JWT** | 用户 API 首选认证方案 |
| **API Key** | 带前缀 + 哈希存储 + Header 传输 |
| **限流** | 429 + RateLimit Header |
| **CORS** | 白名单域名，不要用 * |

---

## 9. OpenAPI 与文档自动化

### 9.1 OpenAPI 3.0 规范核心概念

```
OpenAPI = API 的"说明书"标准格式（YAML/JSON）

  核心组成：
  ┌──────────────┬──────────────────────────┐
  │ info         │ API 名称、版本、描述       │
  │ servers      │ 服务器地址                │
  │ paths        │ URL + Method → 操作定义    │
  │ components   │ 复用的 Schema/参数/响应    │
  │ security     │ 认证方案定义              │
  │ tags         │ 接口分组标签              │
  └──────────────┴──────────────────────────┘

  生态工具：
  - Swagger UI → 在线调试
  - ReDoc → 美化文档
  - openapi-generator → 生成客户端 SDK
```

### 9.2 FastAPI 自动生成文档

```python
app = FastAPI(
    title="My API",
    version="1.0.0",
    description="博客系统 API 文档",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc
)

# 访问 /docs → 自动生成交互式文档
# 访问 /openapi.json → 导出 OpenAPI Schema
```

### 9.3 丰富文档：示例、标签、描述

```python
@router.get("/users/{user_id}", tags=["用户管理"],
            summary="获取用户详情",
            description="根据用户 ID 获取用户完整信息。需要认证。",
            response_description="用户信息")
async def get_user(
    user_id: int = Path(..., description="用户 ID", example=123),
) -> UserResponse:
    ...

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    
    model_config = ConfigDict(json_schema_extra={
        "example": {"id": 123, "username": "alice", "email": "alice@example.com"}
    })
```

### 9.4 文档即代码：CI 中自动校验

```yaml
# GitHub Actions：每次 PR 自动检查 API 变更
- name: Generate OpenAPI spec
  run: python -c "from app.main import app; import json; print(json.dumps(app.openapi()))" > openapi.json

- name: Validate OpenAPI spec
  run: npx @redocly/cli lint openapi.json

- name: Check breaking changes
  run: npx oasdiff breaking openapi-main.json openapi.json
```

**第 9 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **OpenAPI** | API 说明书标准（YAML/JSON） |
| **FastAPI** | 自动生成 /docs 和 /redoc |
| **示例** | json_schema_extra + example |
| **CI** | 每次 PR 自动校验 Schema 变更 |

---

## 10. 实战：设计一个完整的 API

### 10.1 需求分析：博客系统 API

```
功能需求：
  - 用户注册/登录
  - 文章 CRUD + 发布/草稿
  - 评论（嵌套在文章下）
  - 标签管理
  - 文章搜索 + 分页
```

### 10.2 资源建模与 URL 设计

```
资源：users / articles / comments / tags

  用户：
    POST   /api/v1/users              注册
    POST   /api/v1/auth/login         登录
    GET    /api/v1/users/me            当前用户

  文章：
    GET    /api/v1/articles            列表（+分页过滤排序）
    POST   /api/v1/articles            创建
    GET    /api/v1/articles/{id}       详情
    PATCH  /api/v1/articles/{id}       更新
    DELETE /api/v1/articles/{id}       删除
    POST   /api/v1/articles/{id}/publish  发布

  评论（嵌套在文章下）：
    GET    /api/v1/articles/{id}/comments    文章评论列表
    POST   /api/v1/articles/{id}/comments    发表评论
    DELETE /api/v1/comments/{id}             删除评论

  标签：
    GET    /api/v1/tags                标签列表
    GET    /api/v1/articles?tag=python  按标签筛选
```

### 10.3 完整接口清单

| 方法 | URL | 描述 | 认证 | 状态码 |
|:---|:---|:---|:---|:---|
| POST | /users | 注册 | ❌ | 201 |
| POST | /auth/login | 登录 | ❌ | 200 |
| GET | /users/me | 当前用户 | ✅ | 200 |
| GET | /articles | 文章列表 | ❌ | 200 |
| POST | /articles | 创建文章 | ✅ | 201 |
| GET | /articles/{id} | 文章详情 | ❌ | 200 |
| PATCH | /articles/{id} | 更新文章 | ✅ | 200 |
| DELETE | /articles/{id} | 删除文章 | ✅ | 204 |
| POST | /articles/{id}/publish | 发布 | ✅ | 200 |
| GET | /articles/{id}/comments | 评论列表 | ❌ | 200 |
| POST | /articles/{id}/comments | 发表评论 | ✅ | 201 |
| DELETE | /comments/{id} | 删除评论 | ✅ | 204 |
| GET | /tags | 标签列表 | ❌ | 200 |

### 10.4 API 设计评审 Checklist

```
设计评审清单（每个接口过一遍）：

  URL：
    ☐ 名词复数、小写连字符
    ☐ 嵌套≤2 层
    ☐ 无动词（除非动作型子资源）

  方法：
    ☐ CRUD 用正确的 HTTP 方法
    ☐ POST 创建返回 201
    ☐ DELETE 返回 204

  参数：
    ☐ 列表接口支持分页
    ☐ 参数有校验（类型、范围、必填）
    ☐ 幂等接口有 Idempotency-Key

  响应：
    ☐ 统一响应格式
    ☐ 错误有业务错误码
    ☐ 文档有示例

  安全：
    ☐ 需要认证的接口已标记
    ☐ 有限流配置
    ☐ CORS 白名单
```

**第 10 章核心知识回顾：**

| 阶段 | 做了什么 |
|:---|:---|
| **需求** | 用户/文章/评论/标签 4 个资源 |
| **URL** | RESTful 命名 + 合理嵌套 |
| **接口** | 13 个端点，覆盖完整 CRUD |
| **Checklist** | URL/方法/参数/响应/安全 5 大类 |

---

## 附录

### A. HTTP 状态码速查表

| 状态码 | 含义 | 典型场景 |
|:---|:---|:---|
| 200 | OK | GET/PATCH 成功 |
| 201 | Created | POST 创建成功 |
| 204 | No Content | DELETE 成功 |
| 301 | Moved Permanently | URL 永久迁移 |
| 304 | Not Modified | 缓存命中 |
| 400 | Bad Request | 参数格式错误 |
| 401 | Unauthorized | 未认证 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 数据冲突 |
| 422 | Unprocessable Entity | 校验失败 |
| 429 | Too Many Requests | 限流 |
| 500 | Internal Server Error | 服务器异常 |
| 502 | Bad Gateway | 上游服务不可用 |
| 503 | Service Unavailable | 服务维护 |

### B. RESTful 成熟度模型（Richardson）

```
Level 0：一个 URL + POST（XML-RPC 风格）
  POST /api  {"action": "getUser", "id": 123}

Level 1：多个 URL，单一方法
  POST /users/123  {"action": "get"}

Level 2：URL + HTTP 方法（大部分 API 在这）
  GET /users/123
  POST /users

Level 3：HATEOAS（响应带链接，API 是自描述的）
  GET /users/123
  → {"id": 123, "_links": {"orders": "/users/123/orders"}}

大多数生产 API 达到 Level 2 即可
```

### C. API 设计自查清单

```
一份完整的 API 设计自查清单：

  ☐ URL 用名词复数、小写连字符
  ☐ 正确使用 HTTP 方法（CRUD 语义）
  ☐ 正确使用状态码（不是全返回 200）
  ☐ 列表接口支持分页、过滤、排序
  ☐ 统一响应格式（成功/错误）
  ☐ 错误有业务码 + 友好消息
  ☐ API 有版本管理（/api/v1/）
  ☐ 认证方案已确定（JWT/API Key）
  ☐ 限流已配置（429 + Header）
  ☐ CORS 白名单（不用 *）
  ☐ OpenAPI 文档已生成
  ☐ 文档有示例和描述
```
