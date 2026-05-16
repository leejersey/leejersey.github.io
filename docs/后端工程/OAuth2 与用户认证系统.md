# OAuth2 与用户认证系统

> 从密码存储到 SSO——涵盖认证与授权基础、密码安全、JWT/Session 对比、OAuth2 四种授权模式、第三方登录集成、RBAC 权限控制、SSO 单点登录、Token 安全与刷新策略，一套完整的 Python 用户认证系统工程实践。

---

## 1. 认证与授权基础

### 1.1 认证（Authentication）vs 授权（Authorization）

```
两个完全不同的问题：

  认证（Authentication）= 你是谁？
    → 用户名密码登录、指纹、人脸识别
    → 结果：确认身份（user_id=123）

  授权（Authorization）= 你能做什么？
    → 角色检查、权限校验
    → 结果：允许/拒绝某个操作

  类比：
    认证 = 门禁卡刷卡（证明你是公司员工）
    授权 = 你能进哪些房间（普通员工 vs 管理层）
```

### 1.2 常见认证方案对比

| 方案 | 原理 | 优点 | 缺点 | 适用 |
|:---|:---|:---|:---|:---|
| **Session** | 服务端存状态，Cookie 传 ID | 可随时踢人 | 有状态，难扩展 | 传统 Web |
| **JWT** | 客户端存 Token，无状态 | 无状态，易扩展 | 无法主动失效 | API / SPA |
| **OAuth2** | 第三方授权协议 | 安全，标准化 | 流程复杂 | 第三方登录 |
| **API Key** | 固定密钥 | 简单 | 安全性低 | 服务间调用 |
| **SSO** | 一次登录多系统 | 用户体验好 | 架构复杂 | 企业多系统 |

### 1.3 安全第一原则：OWASP Top 10 认证相关

```
OWASP 认证相关风险（必须防御）：

  ① 暴力破解：登录限流 + 账户锁定
  ② 弱密码：密码强度校验（≥8位、含大小写+数字）
  ③ 凭证泄露：HTTPS + 密码哈希（绝不明文存储）
  ④ Session 劫持：Secure + HttpOnly Cookie
  ⑤ CSRF 攻击：SameSite Cookie + CSRF Token
  ⑥ JWT 滥用：短过期 + Refresh Token + 黑名单
```

### 1.4 本文技术栈与项目结构

```
技术栈：
  FastAPI + SQLAlchemy 2.0 + PostgreSQL
  python-jose (JWT) + passlib (密码哈希)
  Redis (Session/Token 黑名单)
  httpx (OAuth2 第三方调用)

依赖安装：
  pip install fastapi python-jose[cryptography] passlib[bcrypt]
  pip install sqlalchemy asyncpg redis httpx
```

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **认证** | 你是谁（登录） |
| **授权** | 你能干啥（权限） |
| **Session** | 有状态，服务端存储 |
| **JWT** | 无状态，客户端存储 |

---

## 2. 密码安全与用户注册

### 2.1 密码存储：bcrypt / argon2

```python
from passlib.context import CryptContext

# bcrypt（最常用，够安全）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# argon2（更安全，2015 年密码哈希竞赛冠军）
# pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """哈希密码（自动加盐）"""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain, hashed)

# hash_password("MyP@ss123")
# → "$2b$12$LJ3m4ys..."（每次不同，因为盐值不同）
```

```
⚠️ 绝对不要这样做：
  ❌ 明文存储：password = "123456"
  ❌ MD5/SHA256：容易被彩虹表破解
  ❌ 不加盐：相同密码 = 相同哈希 → 批量破解

✅ 正确做法：bcrypt/argon2 自动加盐 + 慢哈希
```

### 2.2 用户注册流程实现

```python
from pydantic import BaseModel, EmailStr, field_validator

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    
    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码至少 8 位")
        if not any(c.isupper() for c in v):
            raise ValueError("需包含大写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("需包含数字")
        return v

@router.post("/register")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    # 检查邮箱是否已存在
    existing = await user_repo.get_by_email(db, data.email)
    if existing:
        raise HTTPException(409, "邮箱已注册")
    
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        is_active=False,  # 未验证邮箱
    )
    db.add(user)
    await db.commit()
    
    await send_verification_email(user.email, user.id)
    return {"message": "注册成功，请查收验证邮件"}
```

### 2.3 邮箱验证与激活

```python
from jose import jwt
from datetime import timedelta

def create_verification_token(user_id: int) -> str:
    return jwt.encode(
        {"sub": str(user_id), "type": "email_verify",
         "exp": datetime.utcnow() + timedelta(hours=24)},
        SECRET_KEY, algorithm="HS256",
    )

@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "email_verify":
            raise HTTPException(400, "无效的验证链接")
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(400, "验证链接已过期")
    
    await user_repo.update(db, user_id, is_active=True)
    return {"message": "邮箱验证成功"}
```

### 2.4 密码强度校验与防暴力破解

```python
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost:6379/0")

async def check_login_rate(ip: str, max_attempts: int = 5, window: int = 300):
    """登录限流：同一 IP 5 分钟内最多 5 次"""
    key = f"login_attempts:{ip}"
    attempts = await redis_client.incr(key)
    if attempts == 1:
        await redis_client.expire(key, window)
    if attempts > max_attempts:
        raise HTTPException(429, f"登录尝试过多，请 {window//60} 分钟后重试")
```

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **bcrypt** | 慢哈希 + 自动加盐，密码存储首选 |
| **密码校验** | ≥8 位 + 大小写 + 数字 |
| **邮箱验证** | JWT Token 嵌入链接，24 小时过期 |
| **防暴力** | Redis 计数，IP 维度 5 次/5 分钟 |

---

## 3. Session 认证

### 3.1 Session 认证原理与流程

```
Session 认证流程：

  1. 用户提交用户名 + 密码
  2. 服务端验证 → 创建 Session（存 Redis）
  3. 返回 Set-Cookie: session_id=abc123
  4. 后续请求自动带 Cookie → 服务端查 Redis → 获取用户信息

  浏览器                    服务端                  Redis
    │                        │                      │
    │── POST /login ────────→│                      │
    │                        │── SET session:abc ──→│
    │←─ Set-Cookie: abc ────│                      │
    │                        │                      │
    │── GET /me (Cookie) ──→│                      │
    │                        │── GET session:abc ──→│
    │                        │←─ {user_id:123} ────│
    │←─ {username:"alice"} ─│                      │
```

### 3.2 Redis 存储 Session

```python
import uuid
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost:6379/1")
SESSION_TTL = 3600 * 24  # 24 小时

async def create_session(user_id: int) -> str:
    session_id = str(uuid.uuid4())
    await redis_client.setex(
        f"session:{session_id}",
        SESSION_TTL,
        json.dumps({"user_id": user_id, "created_at": datetime.utcnow().isoformat()}),
    )
    return session_id

async def get_session(session_id: str) -> dict | None:
    data = await redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None

async def destroy_session(session_id: str):
    await redis_client.delete(f"session:{session_id}")

# 登录接口
@router.post("/login")
async def login(data: LoginForm, response: Response, db=Depends(get_db)):
    user = await authenticate(db, data.email, data.password)
    session_id = await create_session(user.id)
    response.set_cookie(
        key="session_id", value=session_id,
        httponly=True,    # JS 无法读取
        secure=True,      # 仅 HTTPS
        samesite="lax",   # 防 CSRF
        max_age=SESSION_TTL,
    )
    return {"message": "登录成功"}
```

### 3.3 Session 安全：防劫持与防固定

```
Session 安全措施：

  ① HttpOnly Cookie：JS 无法 document.cookie 读取
  ② Secure Flag：仅通过 HTTPS 传输
  ③ SameSite=Lax：跨站请求不带 Cookie（防 CSRF）
  ④ 登录后重新生成 Session ID（防 Session 固定攻击）
  ⑤ 绑定 IP/User-Agent（检测异常登录）
```

### 3.4 适用场景与局限性

```
✅ Session 适合：
  - 传统 Web 应用（服务端渲染）
  - 需要随时踢人（删 Redis 即可）
  - 敏感操作场景（银行/后台管理）

❌ Session 不适合：
  - 多服务/微服务（需要共享 Session 存储）
  - 移动端 / SPA（Cookie 不方便）
  - 高并发 API（每请求查 Redis 有开销）
```

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Session** | 状态存服务端(Redis)，ID 存 Cookie |
| **HttpOnly** | JS 无法读取 Cookie，防 XSS |
| **SameSite** | 跨站不带 Cookie，防 CSRF |
| **踢人** | 删 Redis Key 即可立即失效 |

---

## 4. JWT 认证深度实战

### 4.1 JWT 结构解析（Header / Payload / Signature）

```
JWT = Header.Payload.Signature（三段 Base64，用 . 连接）

  Header：{"alg": "HS256", "typ": "JWT"}
  Payload：{"sub": "123", "role": "admin", "exp": 1700000000}
  Signature：HMAC-SHA256(base64(header) + "." + base64(payload), secret)

  ⚠️ Payload 是 Base64 编码，不是加密！
  → 任何人都能解码看到内容（不要放密码/敏感信息）
  → Signature 只保证"没被篡改"，不保证"看不到"
```

### 4.2 Access Token + Refresh Token 双 Token 方案

```python
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)

def create_access_token(user_id: int, role: str) -> str:
    return jwt.encode({
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": datetime.utcnow() + ACCESS_TOKEN_EXPIRE,
    }, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: int) -> str:
    return jwt.encode({
        "sub": str(user_id),
        "type": "refresh",
        "exp": datetime.utcnow() + REFRESH_TOKEN_EXPIRE,
    }, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login")
async def login(data: LoginForm, db=Depends(get_db)):
    user = await authenticate(db, data.email, data.password)
    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }
```

### 4.3 Token 刷新与无感续期

```python
@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """用 Refresh Token 换新的 Access Token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(401, "无效的 Refresh Token")
        
        user_id = int(payload["sub"])
        user = await user_repo.get(user_id)
        
        return {
            "access_token": create_access_token(user.id, user.role),
            "token_type": "bearer",
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Refresh Token 已过期，请重新登录")
```

```
双 Token 流程：

  Access Token：15 分钟过期（短命，减少泄露风险）
  Refresh Token：7 天过期（只用来换 Access Token）

  前端逻辑：
  1. 请求带 Access Token → 200 OK
  2. Access Token 过期 → 401 → 前端自动用 Refresh Token 换新的
  3. Refresh Token 也过期 → 跳转登录页
```

### 4.4 JWT 黑名单与强制登出

```python
async def blacklist_token(token: str):
    """将 Token 加入黑名单（用于强制登出）"""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    exp = payload["exp"]
    ttl = exp - int(datetime.utcnow().timestamp())
    if ttl > 0:
        await redis_client.setex(f"blacklist:{token}", ttl, "1")

async def is_blacklisted(token: str) -> bool:
    return await redis_client.exists(f"blacklist:{token}")

# 获取当前用户（检查黑名单）
async def get_current_user(token: str = Depends(oauth2_scheme)):
    if await is_blacklisted(token):
        raise HTTPException(401, "Token 已失效")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return await user_repo.get(int(payload["sub"]))

# 登出
@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    await blacklist_token(token)
    return {"message": "已登出"}
```

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **JWT 结构** | Header.Payload.Signature，Payload 不加密 |
| **双 Token** | Access 15 分钟 + Refresh 7 天 |
| **无感续期** | 前端拦截 401 → 自动 Refresh |
| **黑名单** | Redis 存失效 Token，TTL=剩余过期时间 |

---

## 5. OAuth2 协议详解

### 5.1 OAuth2 核心概念与角色

```
OAuth2 四个角色：

  Resource Owner（资源拥有者）= 用户
  Client（客户端）= 你的应用
  Authorization Server（授权服务器）= GitHub/Google
  Resource Server（资源服务器）= GitHub API

  核心思路：
  用户不把密码给你的应用，而是让授权服务器发一个临时令牌给你
  → 你拿令牌去访问 API → 用户随时可以撤销权限
```

### 5.2 授权码模式（Authorization Code）

```
授权码模式（最安全，推荐）：

  1. 你的应用 → 重定向到 GitHub 授权页
     https://github.com/login/oauth/authorize?
       client_id=xxx&redirect_uri=xxx&scope=user:email&state=random

  2. 用户点"授权" → GitHub 回调你的地址
     https://yourapp.com/callback?code=AUTH_CODE&state=random

  3. 你的后端用 code 换 token（服务端对服务端，不暴露 secret）
     POST https://github.com/login/oauth/access_token
     {client_id, client_secret, code}
     → 返回 access_token

  4. 用 access_token 调 GitHub API 获取用户信息
     GET https://api.github.com/user
     Authorization: Bearer access_token
```

### 5.3 PKCE 扩展：移动端/SPA 安全增强

```
PKCE（Proof Key for Code Exchange）：

  问题：SPA/移动端没有后端，无法保存 client_secret
  解决：用一次性的 code_verifier 替代 client_secret

  流程：
  1. 前端生成随机 code_verifier
  2. 计算 code_challenge = SHA256(code_verifier)
  3. 授权请求带 code_challenge
  4. 换 token 时带 code_verifier → 服务器验证

  安全性：即使 code 被截获，没有 code_verifier 也换不到 token
```

### 5.4 其他模式：密码模式、客户端凭证、隐式模式

| 模式 | 适用场景 | 安全性 | 状态 |
|:---|:---|:---|:---|
| **授权码** | Web / 移动端 | ⭐⭐⭐⭐⭐ | ✅ 推荐 |
| **授权码+PKCE** | SPA / 移动端 | ⭐⭐⭐⭐⭐ | ✅ 推荐 |
| **密码模式** | 高度信任的第一方应用 | ⭐⭐ | ⚠️ 不推荐 |
| **客户端凭证** | 服务间通信（无用户） | ⭐⭐⭐ | ✅ 适用 |
| **隐式模式** | 早期 SPA | ⭐ | ❌ 已废弃 |

```python
# 客户端凭证模式（服务间调用）
async def get_service_token():
    resp = await httpx.post("https://auth.example.com/token", data={
        "grant_type": "client_credentials",
        "client_id": SERVICE_CLIENT_ID,
        "client_secret": SERVICE_CLIENT_SECRET,
        "scope": "internal:read",
    })
    return resp.json()["access_token"]
```

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **授权码** | 最安全，code 换 token 在后端完成 |
| **PKCE** | SPA/移动端安全增强，替代 client_secret |
| **客户端凭证** | 服务间无用户场景 |
| **隐式模式** | 已废弃，用 PKCE 替代 |

---

## 6. 第三方登录集成

### 6.1 第三方登录通用流程

```
所有第三方登录都是同一套流程：

  1. 前端跳转到第三方授权页（GitHub/Google/微信）
  2. 用户授权 → 回调你的地址，带 code
  3. 后端用 code 换 access_token
  4. 用 access_token 拿用户信息（邮箱/头像/昵称）
  5. 查数据库：
     → 已绑定 → 直接登录（返回 JWT）
     → 未绑定 → 创建新用户 或 绑定已有账号
```

### 6.2 GitHub OAuth 登录实战

```python
import httpx

GITHUB_CLIENT_ID = "your_client_id"
GITHUB_CLIENT_SECRET = "your_client_secret"

@router.get("/auth/github")
async def github_login():
    """重定向到 GitHub 授权页"""
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}&scope=user:email"
    )

@router.get("/auth/github/callback")
async def github_callback(code: str, db=Depends(get_db)):
    """GitHub 回调 → 换 token → 获取用户信息"""
    # 1. code 换 token
    token_resp = await httpx.AsyncClient().post(
        "https://github.com/login/oauth/access_token",
        json={"client_id": GITHUB_CLIENT_ID, "client_secret": GITHUB_CLIENT_SECRET, "code": code},
        headers={"Accept": "application/json"},
    )
    access_token = token_resp.json()["access_token"]
    
    # 2. 获取用户信息
    user_resp = await httpx.AsyncClient().get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    github_user = user_resp.json()
    
    # 3. 查找或创建用户
    user = await oauth_repo.find_by_provider(db, "github", str(github_user["id"]))
    if not user:
        user = await create_user_from_oauth(db, "github", github_user)
    
    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id),
    }
```

### 6.3 Google OAuth 登录实战

```python
GOOGLE_CLIENT_ID = "your_google_client_id"
GOOGLE_CLIENT_SECRET = "your_google_client_secret"

@router.get("/auth/google")
async def google_login():
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri=http://localhost:8000/auth/google/callback"
        f"&response_type=code&scope=openid email profile"
    )

@router.get("/auth/google/callback")
async def google_callback(code: str, db=Depends(get_db)):
    # 1. code 换 token
    token_resp = await httpx.AsyncClient().post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code, "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": "http://localhost:8000/auth/google/callback",
            "grant_type": "authorization_code",
        },
    )
    id_token = token_resp.json()["id_token"]
    
    # 2. 解析 id_token（Google 用 OpenID Connect）
    payload = jwt.decode(id_token, options={"verify_signature": False})
    # payload: {"sub": "google_user_id", "email": "user@gmail.com", "name": "Alice"}
    
    user = await oauth_repo.find_by_provider(db, "google", payload["sub"])
    if not user:
        user = await create_user_from_oauth(db, "google", payload)
    
    return {"access_token": create_access_token(user.id, user.role)}
```

### 6.4 账号绑定与多登录方式管理

```python
# 数据库模型：一个用户可以绑定多个第三方账号
class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(ForeignKey("users.id"))
    provider = mapped_column(String(20))       # github / google / wechat
    provider_user_id = mapped_column(String(100))
    
    __table_args__ = (UniqueConstraint("provider", "provider_user_id"),)
```

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **通用流程** | 跳转→授权→回调→换 Token→获取用户 |
| **GitHub** | code 换 token → /user API |
| **Google** | OpenID Connect，id_token 含用户信息 |
| **多绑定** | oauth_accounts 表，provider + provider_user_id 唯一 |

---

## 7. RBAC 权限控制

### 7.1 RBAC 模型设计（用户-角色-权限）

```
RBAC（Role-Based Access Control）：

  用户 ←→ 角色 ←→ 权限

  例：
  用户 Alice → 角色 admin    → 权限 user:read, user:write, user:delete
  用户 Bob   → 角色 editor   → 权限 user:read, article:write
  用户 Carol → 角色 viewer   → 权限 user:read

  关键：用户不直接关联权限，而是通过角色间接关联
  → 新增用户只需分配角色，不用逐个配权限
```

### 7.2 数据库模型与关联关系

```python
# 角色表
class Role(Base):
    __tablename__ = "roles"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(50), unique=True)       # admin / editor / viewer
    permissions = relationship("Permission", secondary="role_permissions")

# 权限表
class Permission(Base):
    __tablename__ = "permissions"
    id = mapped_column(Integer, primary_key=True)
    code = mapped_column(String(100), unique=True)      # user:read / article:write
    description = mapped_column(String(200))

# 角色-权限关联表
class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id = mapped_column(ForeignKey("permissions.id"), primary_key=True)

# 用户-角色关联表
class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id = mapped_column(ForeignKey("roles.id"), primary_key=True)
```

### 7.3 FastAPI 权限装饰器实现

```python
from fastapi import Depends, HTTPException

class PermissionChecker:
    """权限检查器（作为 Depends 使用）"""
    
    def __init__(self, required_permissions: list[str]):
        self.required = required_permissions
    
    async def __call__(self, user=Depends(get_current_user), db=Depends(get_db)):
        user_permissions = await get_user_permissions(db, user.id)
        
        for perm in self.required:
            if perm not in user_permissions:
                raise HTTPException(403, f"缺少权限: {perm}")
        
        return user

# 使用
@router.get("/admin/users")
async def list_users(user=Depends(PermissionChecker(["user:read"]))):
    return await user_repo.list_all()

@router.delete("/admin/users/{id}")
async def delete_user(id: int, user=Depends(PermissionChecker(["user:delete"]))):
    await user_repo.delete(id)
```

### 7.4 动态权限与菜单控制

```python
@router.get("/me/permissions")
async def my_permissions(user=Depends(get_current_user), db=Depends(get_db)):
    """返回当前用户的所有权限（前端用来控制菜单/按钮显示）"""
    permissions = await get_user_permissions(db, user.id)
    return {
        "user": {"id": user.id, "username": user.username},
        "roles": [r.name for r in user.roles],
        "permissions": permissions,
        # 前端根据 permissions 控制：
        # "user:delete" 有 → 显示删除按钮
        # "user:delete" 没有 → 隐藏删除按钮
    }
```

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **RBAC** | 用户→角色→权限，三层间接关联 |
| **权限码** | resource:action 格式（user:read） |
| **PermissionChecker** | FastAPI Depends 注入，自动校验 |
| **动态菜单** | /me/permissions 返回权限列表，前端控制 UI |

---

## 8. SSO 单点登录

### 8.1 SSO 解决什么问题？

```
没有 SSO：
  用户登录 A 系统 → 跳到 B 系统 → 又要登录一次
  用户登录 B 系统 → 跳到 C 系统 → 又又要登录一次

有了 SSO：
  用户登录一次 → A/B/C 系统都认为已登录

  典型场景：
  - Google 登录一次 → Gmail/YouTube/Drive 都能用
  - 企业内部：OA/CRM/ERP 一次登录通行
```

### 8.2 基于 JWT 的轻量级 SSO

```python
# SSO Server（认证中心）
@router.post("/sso/login")
async def sso_login(data: LoginForm):
    user = await authenticate(data.email, data.password)
    token = create_access_token(user.id, user.role)
    return {"token": token, "redirect": data.redirect_url}

# 各子系统验证 Token（共享同一个 SECRET_KEY 或用 RSA 公钥验证）
async def verify_sso_token(token: str):
    payload = jwt.decode(token, SSO_PUBLIC_KEY, algorithms=["RS256"])
    return payload
```

```
JWT SSO 流程：

  1. 用户访问 A 系统 → 未登录 → 跳转 SSO 登录页
  2. SSO 登录成功 → 返回 JWT → 重定向回 A 系统
  3. A 系统用 SSO 公钥验证 JWT → 登录成功
  4. 用户访问 B 系统 → 检查 JWT → 有效 → 直接通过

  关键：所有子系统共享 SSO 的公钥（RSA 非对称）
  → SSO 用私钥签名，子系统用公钥验证
```

### 8.3 CAS 流程与实现

```
CAS（Central Authentication Service）流程：

  1. 用户访问 app.example.com
  2. App 重定向到 sso.example.com/login?service=app.example.com
  3. 用户在 SSO 登录 → SSO 生成 Service Ticket (ST)
  4. SSO 重定向回 app.example.com?ticket=ST-xxx
  5. App 后端拿 ST 去 SSO 验证 → SSO 返回用户信息
  6. App 创建本地 Session

  优点：Ticket 一次性使用，安全性高
  缺点：每次验证需要调 SSO（多一次网络请求）
```

### 8.4 跨域认证：Cookie vs Token

| 方案 | 跨域 | 安全性 | 适用 |
|:---|:---|:---|:---|
| **共享 Cookie** | 需要同一父域 (.example.com) | 中 | 同域子系统 |
| **JWT Header** | 无跨域限制 | 高 | API / SPA |
| **URL Token** | 无限制（但暴露在 URL） | 低 | 临时跳转 |
| **OAuth2** | 无限制 | 高 | 第三方系统 |

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **SSO** | 一次登录，多系统通行 |
| **JWT SSO** | 共享公钥验证，轻量无状态 |
| **CAS** | Service Ticket 一次性验证 |
| **跨域** | 同域用 Cookie，跨域用 JWT/OAuth2 |

---

## 9. 安全加固

### 9.1 CSRF 防护

```python
# 方案一：SameSite Cookie（推荐）
response.set_cookie("session_id", value, samesite="strict")
# strict：跨站完全不带 Cookie
# lax：安全的跨站请求（GET）会带，POST 不带

# 方案二：CSRF Token（传统方案）
@router.get("/csrf-token")
async def get_csrf_token():
    token = secrets.token_urlsafe(32)
    await redis_client.setex(f"csrf:{token}", 3600, "1")
    return {"csrf_token": token}

# 验证 CSRF Token
async def verify_csrf(csrf_token: str = Header(alias="X-CSRF-Token")):
    if not await redis_client.exists(f"csrf:{csrf_token}"):
        raise HTTPException(403, "CSRF Token 无效")
    await redis_client.delete(f"csrf:{csrf_token}")
```

### 9.2 XSS 防护与 Content Security Policy

```python
# CSP Header（控制页面能加载哪些资源）
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

# 输入过滤（防止存储型 XSS）
import html
def sanitize_input(text: str) -> str:
    return html.escape(text)
```

### 9.3 登录限流与 IP 封禁

```python
async def check_account_lock(email: str):
    """账户级别锁定：连续失败 10 次锁定 30 分钟"""
    key = f"login_fail:{email}"
    fails = int(await redis_client.get(key) or 0)
    if fails >= 10:
        raise HTTPException(423, "账户已锁定，30 分钟后重试")

async def record_login_failure(email: str):
    key = f"login_fail:{email}"
    await redis_client.incr(key)
    await redis_client.expire(key, 1800)  # 30 分钟

async def clear_login_failures(email: str):
    await redis_client.delete(f"login_fail:{email}")
```

### 9.4 安全审计日志

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(Integer, nullable=True)
    action = mapped_column(String(50))      # login / logout / password_change
    ip_address = mapped_column(String(45))
    user_agent = mapped_column(String(200))
    success = mapped_column(Boolean)
    created_at = mapped_column(DateTime, default=datetime.utcnow)

async def log_audit(db, action: str, request: Request, user_id=None, success=True):
    db.add(AuditLog(
        user_id=user_id, action=action, success=success,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
    ))
    await db.commit()
```

**第 9 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **CSRF** | SameSite Cookie 或 CSRF Token |
| **CSP** | 限制资源加载来源，防 XSS |
| **账户锁定** | 失败 10 次→锁 30 分钟 |
| **审计日志** | 记录登录/登出/改密全流程 |

---

## 10. 生产部署与最佳实践

### 10.1 HTTPS 与证书管理

```
HTTPS 是认证系统的前提（没有 HTTPS 一切安全措施都是摆设）：

  ✅ Let's Encrypt 免费证书（自动续期）
  ✅ Nginx 反向代理处理 TLS
  ✅ HSTS Header 强制 HTTPS

  Nginx 配置：
  server {
      listen 443 ssl;
      ssl_certificate /etc/nginx/ssl/cert.pem;
      ssl_certificate_key /etc/nginx/ssl/key.pem;
      add_header Strict-Transport-Security "max-age=31536000" always;
  }
```

### 10.2 密钥轮换策略

```python
# JWT 密钥轮换：支持新旧两个密钥并存
import os

CURRENT_KEY = os.environ["JWT_SECRET_CURRENT"]
PREVIOUS_KEY = os.environ.get("JWT_SECRET_PREVIOUS", "")

def decode_token_with_rotation(token: str):
    """尝试当前密钥，失败则尝试旧密钥"""
    try:
        return jwt.decode(token, CURRENT_KEY, algorithms=["HS256"])
    except jwt.InvalidSignatureError:
        if PREVIOUS_KEY:
            return jwt.decode(token, PREVIOUS_KEY, algorithms=["HS256"])
        raise
```

```
轮换流程：
  1. 生成新密钥 → 设为 CURRENT，旧密钥设为 PREVIOUS
  2. 新签发的 Token 用 CURRENT 签名
  3. 旧 Token 验证时先试 CURRENT，失败试 PREVIOUS
  4. 等旧 Token 全部过期后 → 删除 PREVIOUS
```

### 10.3 认证系统监控与告警

```
必须监控的指标：

  ┌──────────────────┬────────────────────────┐
  │ 登录成功率       │ < 95% → 告警            │
  │ 登录失败率       │ 某 IP 失败 > 50/小时     │
  │ Token 刷新频率   │ 异常频繁 → 可能被攻击    │
  │ 异地登录         │ IP 地理位置突变          │
  │ 密码重置频率     │ 异常高 → 可能批量攻击    │
  └──────────────────┴────────────────────────┘
```

### 10.4 生产部署 Checklist

```
认证系统上线检查清单：

  密码安全：
    ☐ 使用 bcrypt/argon2（不是 MD5/SHA）
    ☐ 密码强度校验（≥8 位 + 复杂度）
    ☐ 登录限流已配置（IP + 账户双维度）

  Token 安全：
    ☐ SECRET_KEY 已更换为强随机值
    ☐ Access Token ≤ 15 分钟
    ☐ Refresh Token ≤ 7 天
    ☐ JWT 黑名单已实现（登出/踢人）

  传输安全：
    ☐ HTTPS 已配置
    ☐ Cookie: HttpOnly + Secure + SameSite
    ☐ CORS 白名单已配置

  权限安全：
    ☐ 所有 API 都有认证检查
    ☐ RBAC 权限校验已就位
    ☐ 管理接口有额外限制

  运维安全：
    ☐ 审计日志已开启
    ☐ 登录异常告警已配置
    ☐ 密钥轮换方案已就绪
```

**第 10 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **HTTPS** | 认证系统的前提，没有等于裸奔 |
| **密钥轮换** | 新旧密钥并存，无缝切换 |
| **监控** | 登录成功率 + 失败 IP + 异地登录 |
| **Checklist** | 密码/Token/传输/权限/运维 5 大类 |

---

## 附录

### A. JWT vs Session 决策矩阵

| 维度 | 选 Session | 选 JWT |
|:---|:---|:---|
| **架构** | 单体 / 少量服务 | 微服务 / 多端 |
| **踢人需求** | 需要随时踢人 | 可接受等 Token 过期 |
| **扩展性** | 需要共享 Redis | 无状态，天然分布式 |
| **客户端** | Web（有 Cookie） | SPA / 移动端 / API |
| **安全性** | Cookie 自动管理 | 需自行管理 Token |
| **性能** | 每请求查 Redis | 无需查 Redis（签名验证） |

### B. OAuth2 Provider 配置速查

| Provider | 授权 URL | Token URL | 用户信息 URL |
|:---|:---|:---|:---|
| **GitHub** | github.com/login/oauth/authorize | github.com/login/oauth/access_token | api.github.com/user |
| **Google** | accounts.google.com/o/oauth2/v2/auth | oauth2.googleapis.com/token | OpenID id_token |
| **微信** | open.weixin.qq.com/connect/qrconnect | api.weixin.qq.com/sns/oauth2/access_token | api.weixin.qq.com/sns/userinfo |

### C. 常见认证漏洞与修复方案

| 漏洞 | 攻击方式 | 修复 |
|:---|:---|:---|
| **暴力破解** | 大量用户名密码组合 | 登录限流 + 账户锁定 + CAPTCHA |
| **凭证填充** | 用泄露的密码库尝试 | 防暴力 + 异地登录检测 |
| **JWT 泄露** | 窃取 Token 冒充身份 | 短过期 + HTTPS + HttpOnly |
| **CSRF** | 诱导用户发起请求 | SameSite Cookie + Token |
| **XSS 窃 Token** | JS 读取 localStorage | HttpOnly Cookie 存 Token |
| **Session 固定** | 登录前设好 Session ID | 登录后重新生成 Session |
| **密码重置漏洞** | 猜测重置链接 | 强随机 Token + 短过期 |
| **OAuth 钓鱼** | 伪造回调地址 | 严格验证 redirect_uri |
