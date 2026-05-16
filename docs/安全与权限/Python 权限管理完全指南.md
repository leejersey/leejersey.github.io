# Python 权限管理完全指南

> 从基础概念到框架实战——用 Python 构建安全可靠的权限管理系统。

---

## 一、权限管理基础概念

### 1. 什么是权限管理

#### 认证 vs 授权

权限管理包含两个核心环节，很多人容易混淆：

```
 认证（Authentication）             授权（Authorization）
 ═══════════════════                ═══════════════════

 "你是谁？"                         "你能干什么？"

 验证用户身份                       验证用户权限
 用户名 + 密码                      角色 + 权限规则
 JWT Token / Session               RBAC / ABAC 策略

 先认证 ──────────────────▶ 再授权
```

| 环节 | 解决的问题 | 典型技术 |
| :--- | :--- | :--- |
| **认证** | 确认"你是张三而不是李四" | 密码、JWT、OAuth、指纹 |
| **授权** | 确认"张三能访问哪些资源" | RBAC、ACL、ABAC |

> 💡 认证回答 **"Who are you?"**，授权回答 **"What can you do?"**。两者缺一不可。

#### 为什么需要权限管理

```
 ❌ 没有权限管理
 ═══════════════════════════════════════

 · 普通用户可以删除其他用户的数据
 · 未登录的人可以访问后台管理页面
 · 实习生可以执行数据库删表操作
 · API 接口谁都能调用，数据裸奔

 ✅ 有权限管理
 ═══════════════════════════════════════

 · 用户只能操作自己的数据
 · 管理后台只有管理员可进入
 · 不同角色看到不同的功能菜单
 · API 按权限分级，敏感操作需要高级授权
```

### 2. 常见权限模型

#### ACL（访问控制列表）

最直接的模型——给每个资源维护一张"谁能访问"的清单：

```python
# ACL 示例
acl = {
    "/admin":        ["admin"],
    "/user/profile": ["admin", "user"],
    "/public":       ["admin", "user", "guest"]
}

def check_acl(user_role, resource):
    return user_role in acl.get(resource, [])
```

| 优点 | 缺点 |
| :--- | :--- |
| 简单直观 | 用户多了难以维护 |
| 适合小型系统 | 没有角色抽象，重复配置多 |

#### RBAC（基于角色的访问控制）⭐ 最常用

在用户和权限之间加一层**角色**——用户绑定角色，角色绑定权限：

```
 用户             角色              权限
 ═════            ═════            ═════

 张三 ──▶ 管理员 ──▶ 用户管理
 李四 ──▶ 编辑   ──▶ 文章编辑
 王五 ──▶ 普通用户 ──▶ 文章查看
 赵六 ──▶ 编辑   ──▶ 文章编辑（和李四相同角色，自动拥有相同权限）
```

```python
# RBAC 示例
roles_permissions = {
    "admin":  ["user:read", "user:write", "user:delete", "article:*"],
    "editor": ["article:read", "article:write"],
    "viewer": ["article:read"]
}

user_roles = {
    "张三": ["admin"],
    "李四": ["editor"],
    "王五": ["viewer"]
}

def has_permission(username, permission):
    for role in user_roles.get(username, []):
        perms = roles_permissions.get(role, [])
        if permission in perms or "*" in [p.split(":")[1] for p in perms if ":" in p]:
            return True
    return False
```

| 优点 | 缺点 |
| :--- | :--- |
| 角色抽象，易维护 | 角色爆炸（权限组合太多时角色数量失控） |
| 业界最广泛使用 | 不支持动态条件（如"只能在工作时间访问"） |

#### ABAC（基于属性的访问控制）

根据**属性**动态判断权限——用户属性、资源属性、环境属性都可以作为条件：

```python
# ABAC 示例
def check_permission(user, resource, action, environment):
    # 规则：只有本部门的经理才能在工作时间审批请假
    if (action == "approve_leave"
        and user.role == "manager"
        and user.department == resource.department
        and 9 <= environment.hour <= 18):
        return True
    return False
```

| 优点 | 缺点 |
| :--- | :--- |
| 极其灵活，支持复杂条件 | 规则复杂，难以审计 |
| 适合大型企业系统 | 学习成本高 |

#### 四种模型对比

| 模型 | 复杂度 | 灵活性 | 适用场景 | Python 框架支持 |
| :--- | :--- | :--- | :--- | :--- |
| **ACL** | ⭐ | ⭐⭐ | 小型系统、文件权限 | 手写即可 |
| **RBAC** | ⭐⭐ | ⭐⭐⭐ | 绝大多数 Web 应用 | Django 内置 / Casbin |
| **ABAC** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 企业级、复杂业务规则 | Casbin / OPA |
| **PBAC** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 微服务、云原生 | OPA (Rego) |

> 💡 **选型建议**：80% 的项目用 RBAC 就够了。只有需要动态条件判断（如时间、地理位置、部门关系）时才考虑 ABAC。

### 3. 权限管理的核心要素

```
 ┌─────────────────────────────────────────────────┐
 │              权限管理四要素                        │
 ├─────────────────────────────────────────────────┤
 │                                                 │
 │  👤 用户（User）                                 │
 │  系统中的操作主体，有唯一标识                      │
 │  例：张三、李四、API 调用方                       │
 │                                                 │
 │  🎭 角色（Role）                                 │
 │  权限的集合，用于分组管理                          │
 │  例：管理员、编辑、普通用户、访客                  │
 │                                                 │
 │  🔑 权限（Permission）                            │
 │  对某个资源执行某个操作的授权                      │
 │  例：article:read、user:delete                  │
 │                                                 │
 │  📦 资源（Resource）                              │
 │  被保护的对象                                     │
 │  例：文章、用户数据、API 接口、文件                │
 │                                                 │
 └─────────────────────────────────────────────────┘
```

#### 它们之间的关系

```
 用户 ──(拥有)──▶ 角色 ──(包含)──▶ 权限 ──(操作)──▶ 资源

 示例：
 张三 ──▶ 管理员 ──▶ user:delete ──▶ 用户数据
 李四 ──▶ 编辑   ──▶ article:write ──▶ 文章
```

#### 权限命名规范

```python
# 推荐格式：资源:操作
permissions = [
    "user:read",       # 查看用户
    "user:write",      # 编辑用户
    "user:delete",     # 删除用户
    "article:read",    # 查看文章
    "article:write",   # 编辑文章
    "article:publish", # 发布文章
    "system:config",   # 系统配置
]

# 通配符
"article:*"  # 文章的所有权限
"*:read"     # 所有资源的读取权限
```

> 💡 **统一命名**可以让权限易读、易管理、易排查。建议团队在项目初期就定好规范。

---

## 二、Python 原生实现权限管理

### 1. 装饰器实现简单权限控制

装饰器是 Python 中最优雅的权限控制方式——**不侵入业务代码**，一行 `@` 搞定。

#### 登录验证装饰器

```python
from functools import wraps
from flask import request, jsonify

def login_required(f):
    """验证用户是否已登录"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "未登录，请先登录"}), 401
        
        user = verify_token(token)  # 解析 JWT Token
        if not user:
            return jsonify({"error": "Token 无效或已过期"}), 401
        
        request.current_user = user  # 将用户信息挂到 request 上
        return f(*args, **kwargs)
    return decorated


# 使用
@app.route("/profile")
@login_required
def get_profile():
    user = request.current_user
    return jsonify({"name": user.name})
```

#### 角色验证装饰器

```python
def role_required(*roles):
    """验证用户是否拥有指定角色"""
    def decorator(f):
        @wraps(f)
        @login_required  # 先认证，再授权
        def decorated(*args, **kwargs):
            user = request.current_user
            if user.role not in roles:
                return jsonify({"error": f"需要 {roles} 角色"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# 使用
@app.route("/admin/users")
@role_required("admin", "super_admin")
def manage_users():
    return jsonify({"users": get_all_users()})
```

#### 权限验证装饰器

```python
def permission_required(permission):
    """验证用户是否拥有指定权限"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            user = request.current_user
            user_permissions = get_user_permissions(user.id)
            
            if permission not in user_permissions:
                return jsonify({"error": f"缺少权限: {permission}"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# 使用
@app.route("/articles", methods=["POST"])
@permission_required("article:write")
def create_article():
    return jsonify({"msg": "文章创建成功"})

@app.route("/articles/<id>", methods=["DELETE"])
@permission_required("article:delete")
def delete_article(id):
    return jsonify({"msg": f"文章 {id} 已删除"})
```

#### 装饰器方案总结

```
 装饰器的执行顺序（从外到内）
 ═══════════════════════════════════════

 请求进入
   ↓
 @permission_required("article:write")  ← 检查权限
   ↓
 @login_required                        ← 检查登录
   ↓
 业务函数                               ← 执行业务逻辑
```

### 2. 中间件实现权限拦截

装饰器适合逐个接口控制，**中间件**适合全局统一拦截。

#### 基于路由的权限映射

```python
# 权限配置表：路由 → 所需权限
ROUTE_PERMISSIONS = {
    "GET:/api/users":      "user:read",
    "POST:/api/users":     "user:write",
    "DELETE:/api/users/*":  "user:delete",
    "GET:/api/articles":   "article:read",
    "POST:/api/articles":  "article:write",
    "GET:/api/public/*":    None,  # 公开接口，无需权限
}
```

#### Flask 中间件示例

```python
import re

@app.before_request
def check_permission():
    """全局权限拦截中间件"""
    
    # 1. 跳过公开路由
    public_paths = ["/api/public", "/api/auth/login", "/health"]
    if any(request.path.startswith(p) for p in public_paths):
        return None
    
    # 2. 验证登录
    token = request.headers.get("Authorization")
    user = verify_token(token)
    if not user:
        return jsonify({"error": "未登录"}), 401
    
    request.current_user = user
    
    # 3. 匹配路由权限
    route_key = f"{request.method}:{request.path}"
    required_permission = match_route_permission(route_key)
    
    if required_permission is None:
        return None  # 公开接口
    
    # 4. 检查用户权限
    user_permissions = get_user_permissions(user.id)
    if required_permission not in user_permissions:
        return jsonify({"error": f"缺少权限: {required_permission}"}), 403


def match_route_permission(route_key):
    """匹配路由到权限（支持通配符）"""
    for pattern, permission in ROUTE_PERMISSIONS.items():
        # 将通配符 * 转为正则
        regex = pattern.replace("*", ".*")
        if re.match(regex, route_key):
            return permission
    return "unknown"  # 未注册的路由默认拒绝
```

#### 装饰器 vs 中间件

| 对比 | 装饰器 | 中间件 |
| :--- | :--- | :--- |
| 粒度 | 单个接口 | 全局/路由组 |
| 灵活性 | 每个接口可不同权限 | 统一规则，集中管理 |
| 侵入性 | 需要在每个视图函数上加 | 一次配置，自动生效 |
| 适用场景 | 权限规则差异大的接口 | 权限规则统一的 API 系统 |

> 💡 **最佳实践**：中间件做**通用拦截**（认证 + 基础权限），装饰器做**精细控制**（特殊权限）。两者配合使用。

### 3. 手写 RBAC 模型

在不依赖任何框架的情况下，用 Python + SQLAlchemy 实现一个完整的 RBAC 系统。

#### 数据库表设计

```
 ┌──────────┐     ┌────────────────┐     ┌──────────┐
 │  users   │     │ user_roles     │     │  roles   │
 │──────────│     │────────────────│     │──────────│
 │ id       │──┐  │ user_id (FK)   │  ┌──│ id       │
 │ username │  └─▶│ role_id (FK)   │◀─┘  │ name     │
 │ password │     └────────────────┘     │ desc     │
 └──────────┘                            └──────────┘
                                              │
                  ┌────────────────┐           │
                  │role_permissions│           │
                  │────────────────│           │
                  │ role_id (FK)   │◀──────────┘
                  │ permission_id  │──┐
                  └────────────────┘  │  ┌──────────────┐
                                      └─▶│ permissions  │
                                         │──────────────│
                                         │ id           │
                                         │ code         │
                                         │ desc         │
                                         └──────────────┘
```

#### SQLAlchemy ORM 模型

```python
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# 用户-角色 多对多关联表
user_roles = Table(
    "user_roles", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("role_id", Integer, ForeignKey("roles.id"))
)

# 角色-权限 多对多关联表
role_permissions = Table(
    "role_permissions", Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id")),
    Column("permission_id", Integer, ForeignKey("permissions.id"))
)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    
    # 关联角色
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    
    def has_permission(self, permission_code: str) -> bool:
        """检查用户是否拥有某个权限"""
        for role in self.roles:
            for perm in role.permissions:
                if perm.code == permission_code:
                    return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """检查用户是否拥有某个角色"""
        return any(role.name == role_name for role in self.roles)
    
    @property
    def all_permissions(self) -> set:
        """获取用户的所有权限"""
        perms = set()
        for role in self.roles:
            for perm in role.permissions:
                perms.add(perm.code)
        return perms


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions,
                               back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)  # 如 "article:write"
    description = Column(String(200))
    
    roles = relationship("Role", secondary=role_permissions,
                         back_populates="permissions")
```

#### 使用示例

```python
# 创建角色和权限
admin_role = Role(name="admin", description="管理员")
editor_role = Role(name="editor", description="编辑")

perm_read = Permission(code="article:read", description="查看文章")
perm_write = Permission(code="article:write", description="编辑文章")
perm_delete = Permission(code="article:delete", description="删除文章")
perm_user = Permission(code="user:manage", description="用户管理")

# 角色绑定权限
admin_role.permissions = [perm_read, perm_write, perm_delete, perm_user]
editor_role.permissions = [perm_read, perm_write]

# 用户绑定角色
user = User(username="张三")
user.roles = [editor_role]

# 权限校验
user.has_permission("article:write")   # True ✅
user.has_permission("article:delete")  # False ❌
user.has_permission("user:manage")     # False ❌
user.has_role("editor")                # True ✅
user.all_permissions                   # {"article:read", "article:write"}
```

> 💡 这套手写 RBAC 虽然简单，但已经能满足大部分中小型项目的需求。当项目复杂度上升时，再考虑引入 Casbin 等专业框架。

---

## 三、FastAPI 权限管理

### 1. FastAPI 依赖注入实现权限

FastAPI 的权限管理天然适合用**依赖注入（Depends）** 实现——比装饰器更优雅，比中间件更灵活。

#### 核心思路

```
 传统框架：装饰器挂在函数上
 ═══════════════════════════════════════
 @login_required
 @role_required("admin")
 def view():
     pass

 FastAPI：依赖注入到参数中
 ═══════════════════════════════════════
 def view(user: User = Depends(get_current_user)):
     pass

 → 权限校验变成了函数参数，更 Pythonic
```

#### OAuth2 + JWT 认证基础

> 💡 关于 JWT 的原理和单点登录机制，详见 [什么是单点登录（SSO）与 JWT](什么是单点登录（SSO）与 JWT)。

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI()

# OAuth2 方案：从请求头提取 Bearer Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class TokenData(BaseModel):
    username: str
    role: str
    permissions: list[str] = []


def create_access_token(data: dict) -> str:
    """生成 JWT Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """从 Token 中解析当前用户（核心依赖）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token 无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "viewer")
        permissions: list = payload.get("permissions", [])
        if username is None:
            raise credentials_exception
        return TokenData(username=username, role=role, permissions=permissions)
    except JWTError:
        raise credentials_exception
```

#### 使用依赖注入

```python
# 任何需要登录的接口，只需加 Depends(get_current_user)
@app.get("/profile")
async def get_profile(user: TokenData = Depends(get_current_user)):
    return {"username": user.username, "role": user.role}
```

### 2. FastAPI 权限实战

#### 基于角色的权限依赖

```python
def require_role(*allowed_roles):
    """创建一个角色校验依赖"""
    async def role_checker(user: TokenData = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {allowed_roles} 角色，当前角色: {user.role}"
            )
        return user
    return role_checker


# 使用：只有 admin 可访问
@app.get("/admin/users")
async def list_users(user: TokenData = Depends(require_role("admin", "super_admin"))):
    return {"msg": f"{user.username} 正在查看用户列表"}


# 使用：admin 和 editor 可访问
@app.post("/articles")
async def create_article(user: TokenData = Depends(require_role("admin", "editor"))):
    return {"msg": "文章创建成功"}
```

#### 基于权限的精细控制

```python
def require_permission(permission: str):
    """创建一个权限校验依赖"""
    async def permission_checker(user: TokenData = Depends(get_current_user)):
        if permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {permission}"
            )
        return user
    return permission_checker


# 使用
@app.delete("/articles/{article_id}")
async def delete_article(
    article_id: int,
    user: TokenData = Depends(require_permission("article:delete"))
):
    return {"msg": f"文章 {article_id} 已被 {user.username} 删除"}
```

#### 基于 Scope 的细粒度权限

FastAPI 原生支持 OAuth2 Scope，适合第三方应用授权：

```python
from fastapi.security import SecurityScopes

async def get_current_user_with_scopes(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
) -> TokenData:
    """支持 Scope 校验的用户解析"""
    user = await get_current_user(token)
    
    # 检查 Token 中的权限是否包含所需的 Scope
    for scope in security_scopes.scopes:
        if scope not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少 scope: {scope}",
                headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'},
            )
    return user


# 使用 Security 声明所需 Scope
from fastapi import Security

@app.get("/users/me")
async def read_own_profile(
    user: TokenData = Security(get_current_user_with_scopes, scopes=["user:read"])
):
    return {"username": user.username}

@app.put("/users/me")
async def update_own_profile(
    user: TokenData = Security(get_current_user_with_scopes, scopes=["user:write"])
):
    return {"msg": "个人资料已更新"}
```

#### 三种方式对比

| 方式 | 粒度 | 适用场景 |
| :--- | :--- | :--- |
| `require_role()` | 角色级 | 简单的角色划分（管理员/编辑/用户） |
| `require_permission()` | 操作级 | 精细的操作控制（article:write） |
| `Security(scopes=)` | Scope 级 | OAuth2 第三方授权场景 |

### 3. 第三方库

| 库 | 说明 | 推荐指数 |
| :--- | :--- | :--- |
| **fastapi-users** | 开箱即用的用户管理（注册/登录/OAuth），自带权限 | ⭐⭐⭐⭐⭐ |
| **fastapi-permissions** | 基于 ACL 的权限库，支持资源级控制 | ⭐⭐⭐ |
| **PyCasbin + FastAPI** | 接入 Casbin 策略引擎，支持 RBAC/ABAC | ⭐⭐⭐⭐ |
| **Authlib** | OAuth 客户端/服务端完整实现 | ⭐⭐⭐⭐ |

#### fastapi-users 快速集成

```python
# pip install fastapi-users[sqlalchemy]

from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTStrategy, AuthenticationBackend, BearerTransport

# 1. 配置认证后端
bearer_transport = BearerTransport(tokenUrl="/auth/login")
jwt_strategy = JWTStrategy(secret=SECRET_KEY, lifetime_seconds=3600)
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: jwt_strategy,
)

# 2. 创建 FastAPIUsers 实例
fastapi_users = FastAPIUsers(get_user_manager, [auth_backend])

# 3. 注册路由（自动包含登录、注册、重置密码等）
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth")
app.include_router(fastapi_users.get_register_router(), prefix="/auth")

# 4. 获取当前用户的依赖
current_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

@app.get("/protected")
async def protected_route(user=Depends(current_user)):
    return {"msg": f"欢迎 {user.email}"}

@app.get("/admin")
async def admin_route(user=Depends(current_superuser)):
    return {"msg": "管理员页面"}
```

> 💡 **选型建议**：新项目直接用 `fastapi-users` 省心省力；需要复杂权限策略时加 Casbin；只做 API 认证就手写 JWT 依赖即可。如果后端使用 Supabase，可参考 [Supabase 权威指南](Supabase 权威指南) 中的内置权限系统。

---

## 四、专业权限框架

### 1. Casbin（推荐）⭐

#### 什么是 Casbin

Casbin 是一个**通用的权限策略引擎**——你只需定义策略文件，它帮你做所有的权限判断逻辑。

```
 你的代码                      Casbin
 ═══════                      ═══════

 "张三能不能删除文章 #42?"  →  读取策略文件
                              → 匹配规则
                              → 返回 True / False

 → 你不用写一行权限判断代码，全部交给 Casbin
```

#### 支持的权限模型

| 模型 | 支持 | 说明 |
| :--- | :--- | :--- |
| ACL | ✅ | 最简单的访问控制 |
| RBAC | ✅ | 基于角色，最常用 |
| RBAC + 域 | ✅ | 多租户下的角色控制 |
| ABAC | ✅ | 基于属性的动态判断 |
| RESTful | ✅ | 按 HTTP 方法 + 路径控制 |

#### PyCasbin 使用教程

```bash
pip install casbin
```

Casbin 的核心是两个文件：**Model 文件**（定义权限模型）和 **Policy 文件**（定义具体策略）。

##### RBAC Model 文件（`model.conf`）

```ini
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
```

```
 解读：
 r = sub, obj, act     → 请求三要素：谁(sub)、访问什么(obj)、做什么(act)
 p = sub, obj, act     → 策略格式：允许谁、访问什么、做什么
 g = _, _              → 角色继承关系
 m = ...               → 匹配规则：用户的角色匹配 + 资源匹配 + 操作匹配
```

##### Policy 文件（`policy.csv`）

```csv
p, admin, /users, read
p, admin, /users, write
p, admin, /users, delete
p, editor, /articles, read
p, editor, /articles, write
p, viewer, /articles, read

g, 张三, admin
g, 李四, editor
g, 王五, viewer
```

##### Python 代码

```python
import casbin

# 加载模型和策略
enforcer = casbin.Enforcer("model.conf", "policy.csv")

# 权限校验
enforcer.enforce("张三", "/users", "delete")     # True ✅ (admin 有权限)
enforcer.enforce("李四", "/articles", "write")    # True ✅ (editor 有权限)
enforcer.enforce("李四", "/users", "delete")      # False ❌ (editor 没有权限)
enforcer.enforce("王五", "/articles", "write")    # False ❌ (viewer 只能 read)
```

#### 与 FastAPI 集成

```python
import casbin
from fastapi import FastAPI, Depends, HTTPException

app = FastAPI()
enforcer = casbin.Enforcer("model.conf", "policy.csv")


def check_casbin_permission(resource: str, action: str):
    """Casbin 权限校验依赖"""
    async def checker(user: TokenData = Depends(get_current_user)):
        if not enforcer.enforce(user.username, resource, action):
            raise HTTPException(status_code=403, detail="权限不足")
        return user
    return checker


@app.get("/users")
async def list_users(user=Depends(check_casbin_permission("/users", "read"))):
    return {"users": [...]}

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, user=Depends(check_casbin_permission("/users", "delete"))):
    return {"msg": f"用户 {user_id} 已删除"}
```

### 2. OPA（Open Policy Agent）

#### 什么是 OPA

OPA 是一个**通用策略引擎**，比 Casbin 更强大，使用独立的 Rego 策略语言：

```
 Casbin                        OPA
 ═══════                      ═══════

 嵌入式库                      独立服务（HTTP API）
 CSV/数据库存储策略             Rego 语言编写策略
 轻量简单                      功能强大，学习曲线陡
 适合单体应用                   适合微服务/云原生
```

#### Rego 策略语言

```rego
# policy.rego
package authz

default allow = false

# 管理员拥有所有权限
allow {
    input.user.role == "admin"
}

# 编辑可以读写文章
allow {
    input.user.role == "editor"
    input.resource == "article"
    input.action == ["read", "write"][_]
}

# 所有人可以读取公开资源
allow {
    input.resource == "public"
    input.action == "read"
}
```

#### Python 客户端

```python
import requests

OPA_URL = "http://localhost:8181/v1/data/authz/allow"

def check_opa_permission(user: dict, resource: str, action: str) -> bool:
    """向 OPA 服务查询权限"""
    response = requests.post(OPA_URL, json={
        "input": {
            "user": user,
            "resource": resource,
            "action": action
        }
    })
    return response.json().get("result", False)


# 使用
check_opa_permission({"role": "admin"}, "users", "delete")   # True
check_opa_permission({"role": "editor"}, "article", "write")  # True
check_opa_permission({"role": "viewer"}, "users", "delete")   # False
```

#### Casbin vs OPA

| 对比 | Casbin | OPA |
| :--- | :--- | :--- |
| 部署方式 | Python 库，嵌入应用 | 独立服务，HTTP API |
| 策略语言 | CSV / 配置文件 | Rego（专用语言） |
| 学习成本 | ⭐⭐ 低 | ⭐⭐⭐⭐ 高 |
| 适用规模 | 中小型项目 | 大型 / 微服务 |
| 生态 | Go/Python/Java/Node | Kubernetes / 云原生 |

### 3. 其他工具

| 工具 | 用途 | 代码示例 |
| :--- | :--- | :--- |
| **python-jose** | JWT 编解码 | `jwt.encode(data, key)` / `jwt.decode(token, key)` |
| **Authlib** | OAuth 客户端/服务端 | 完整 OAuth2.0 流程实现 |
| **Permit.io** | 云端权限服务 | SaaS 方案，API 调用即可 |

#### python-jose 示例

```python
from jose import jwt

# 生成 Token
token = jwt.encode(
    {"sub": "张三", "role": "admin", "permissions": ["user:read", "user:write"]},
    "secret-key",
    algorithm="HS256"
)

# 解析 Token
payload = jwt.decode(token, "secret-key", algorithms=["HS256"])
# {'sub': '张三', 'role': 'admin', 'permissions': ['user:read', 'user:write']}
```

#### Authlib 示例

```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name="github",
    client_id="your-client-id",
    client_secret="your-client-secret",
    authorize_url="https://github.com/login/oauth/authorize",
    access_token_url="https://github.com/login/oauth/access_token",
    api_base_url="https://api.github.com/",
)

# FastAPI 路由中使用
@app.get("/login/github")
async def login_github(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)
```

> 💡 **工具选型总结**：JWT 处理用 `python-jose`，OAuth 集成用 `Authlib`，权限策略用 `Casbin`，微服务架构用 `OPA`。

---

## 五、权限模型深入：RBAC 实战

### 1. RBAC 数据库设计

第二章我们用 SQLAlchemy 实现了基础 RBAC 模型，这里进一步完善为**生产级**方案。

#### 完整 ER 图

```
 ┌──────────┐                                    ┌──────────────┐
 │  users   │     ┌────────────────┐              │ permissions  │
 │──────────│     │ user_roles     │              │──────────────│
 │ id       │──┐  │────────────────│   ┌──────┐   │ id           │
 │ username │  └─▶│ user_id        │   │roles │   │ code         │
 │ email    │     │ role_id        │◀──│──────│   │ name         │
 │ is_active│     │ granted_at     │   │ id   │──▶│ resource     │
 │ is_super │     │ granted_by     │   │ name │   │ action       │
 └──────────┘     └────────────────┘   │ level│   └──────────────┘
                                       │ pid  │          ▲
                                       └──────┘          │
                                           │    ┌────────────────┐
                                           └──▶ │role_permissions│
                                                │────────────────│
                                                │ role_id        │
                                                │ permission_id  │
                                                └────────────────┘
```

#### 增强版 ORM 模型

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

user_roles = Table(
    "user_roles", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("granted_at", DateTime, default=datetime.utcnow),
    Column("granted_by", Integer, ForeignKey("users.id"), nullable=True),
)

role_permissions = Table(
    "role_permissions", Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    roles = relationship("Role", secondary=user_roles, back_populates="users")


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    level = Column(Integer, default=0)               # 角色层级
    parent_id = Column(Integer, ForeignKey("roles.id"), nullable=True)  # 父角色
    
    parent = relationship("Role", remote_side=[id])   # 自引用
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions,
                               back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100))
    resource = Column(String(50))   # 资源类型：user / article / order
    action = Column(String(20))     # 操作类型：read / write / delete
    
    roles = relationship("Role", secondary=role_permissions,
                         back_populates="permissions")
```

### 2. RBAC 完整实现

#### 权限服务类

```python
from sqlalchemy.orm import Session

class PermissionService:
    def __init__(self, db: Session):
        self.db = db
    
    # ─── 角色分配与撤销 ───
    
    def assign_role(self, user_id: int, role_name: str):
        """给用户分配角色"""
        user = self.db.query(User).get(user_id)
        role = self.db.query(Role).filter(Role.name == role_name).first()
        if role and role not in user.roles:
            user.roles.append(role)
            self.db.commit()
    
    def revoke_role(self, user_id: int, role_name: str):
        """撤销用户角色"""
        user = self.db.query(User).get(user_id)
        role = self.db.query(Role).filter(Role.name == role_name).first()
        if role and role in user.roles:
            user.roles.remove(role)
            self.db.commit()
    
    # ─── 权限校验 ───
    
    def has_permission(self, user_id: int, permission_code: str) -> bool:
        """检查用户是否有某个权限"""
        user = self.db.query(User).get(user_id)
        
        # 超级管理员拥有所有权限
        if user.is_superuser:
            return True
        
        # 收集所有权限（含继承）
        all_perms = self._collect_permissions(user)
        return permission_code in all_perms
    
    def get_user_permissions(self, user_id: int) -> set:
        """获取用户所有权限（含角色继承）"""
        user = self.db.query(User).get(user_id)
        if user.is_superuser:
            # 超级管理员返回所有权限
            return {p.code for p in self.db.query(Permission).all()}
        return self._collect_permissions(user)
    
    # ─── 权限继承 ───
    
    def _collect_permissions(self, user: User) -> set:
        """收集用户的所有权限（含父角色继承）"""
        perms = set()
        for role in user.roles:
            perms.update(self._get_role_permissions_recursive(role))
        return perms
    
    def _get_role_permissions_recursive(self, role: Role) -> set:
        """递归获取角色权限（含父角色）"""
        perms = {p.code for p in role.permissions}
        if role.parent:
            perms.update(self._get_role_permissions_recursive(role.parent))
        return perms
```

#### 使用示例

```python
svc = PermissionService(db)

# 分配角色
svc.assign_role(user_id=1, role_name="editor")

# 权限校验
svc.has_permission(user_id=1, permission_code="article:write")  # True
svc.has_permission(user_id=1, permission_code="user:delete")    # False

# 获取所有权限
svc.get_user_permissions(user_id=1)
# {'article:read', 'article:write'}

# 超级管理员
svc.has_permission(user_id=admin_id, permission_code="anything")  # True ✅
```

#### 超级管理员处理

```
 超级管理员的三种实现方式
 ═══════════════════════════════════════

 ① 数据库标记（推荐）
    User.is_superuser = True
    → 代码中遇到 is_superuser 直接放行

 ② 特殊角色
    创建 "super_admin" 角色，绑定所有权限
    → 需要维护权限列表同步

 ③ 通配符权限
    给超级管理员分配 "*:*" 权限
    → 匹配逻辑中判断通配符
```

### 3. RBAC 进阶

#### RBAC 四个等级

```
 RBAC0 → RBAC1 → RBAC2 → RBAC3
 基础     继承     约束     统一

 每一级在前一级基础上增加能力
```

| 等级 | 名称 | 增加的能力 | 示例 |
| :--- | :--- | :--- | :--- |
| **RBAC0** | 基础 | 用户 ↔ 角色 ↔ 权限 | 张三是编辑，编辑能写文章 |
| **RBAC1** | 继承 | 角色层级继承 | 经理继承员工的所有权限 |
| **RBAC2** | 约束 | 互斥角色、数量限制 | 不能同时是审核人和申请人 |
| **RBAC3** | 统一 | RBAC1 + RBAC2 | 既有继承又有约束 |

#### 角色层级与继承（RBAC1）

```
 角色继承树
 ═══════════════════════════════════════

 超级管理员（level 0）
   └── 管理员（level 1）
         ├── 编辑（level 2）
         │     └── 投稿人（level 3）
         └── 审核员（level 2）

 → 管理员自动拥有编辑 + 审核员的所有权限
 → 编辑自动拥有投稿人的所有权限
```

```python
# 创建继承关系
superadmin = Role(name="superadmin", level=0)
admin = Role(name="admin", level=1, parent=superadmin)
editor = Role(name="editor", level=2, parent=admin)
contributor = Role(name="contributor", level=3, parent=editor)

# 张三是 editor，自动继承 contributor 的权限
# 李四是 admin，自动继承 editor + contributor 的权限
```

#### 互斥角色与约束（RBAC2）

```python
# 互斥角色定义
MUTEX_ROLES = [
    {"审核员", "申请人"},      # 不能同时审核和申请
    {"出纳", "会计"},          # 财务分离
    {"开发者", "审计员"},      # 职责分离
]

def validate_role_assignment(user: User, new_role: str) -> bool:
    """检查新角色是否与用户现有角色互斥"""
    current_roles = {r.name for r in user.roles}
    
    for mutex_group in MUTEX_ROLES:
        if new_role in mutex_group:
            conflict = current_roles & mutex_group
            if conflict:
                raise ValueError(
                    f"角色冲突：'{new_role}' 与 '{conflict}' 互斥，"
                    f"不能同时分配给同一用户"
                )
    return True


# 角色数量限制
MAX_ROLES_PER_USER = 5

def check_role_limit(user: User):
    if len(user.roles) >= MAX_ROLES_PER_USER:
        raise ValueError(f"每个用户最多 {MAX_ROLES_PER_USER} 个角色")
```

#### 实际项目中怎么选

```
 项目规模              推荐等级
 ═══════════════       ═══════════════

 个人项目 / MVP        RBAC0（基础就够）
 中型 SaaS             RBAC1（加上继承）
 企业级 / 金融         RBAC3（继承 + 约束）
```

> 💡 **核心建议**：先用 RBAC0 跑起来，遇到角色管理痛点时再逐步升级到 RBAC1/2/3。不要过度设计。

---

## 六、API 权限管理

第三章我们用 JWT 实现了基础认证，这里进一步讲解 **API 场景下的权限管理进阶方案**——Token 生命周期管理、OAuth2 Scope 授权、API Key 分级与限流。

### 1. JWT Token 权限控制

#### Token 载荷设计

```
 Token 中应该放什么？
 ═══════════════════════════════════════

 ✅ 建议放入                    ❌ 不建议放入
 ─────────────                  ─────────────
 用户 ID（sub）                 密码 / 密码哈希
 角色（role）                   敏感个人信息（身份证号）
 权限列表（permissions）         大段业务数据
 Token 类型（type）             频繁变更的数据
 过期时间（exp）                 数据库查询结果

 → Token 应该"轻量但够用"，放身份 + 权限即可
```

```python
# 推荐的 Token 载荷结构
token_payload = {
    # ─── 标准字段 ───
    "sub": "user_123",                    # 用户唯一标识
    "exp": 1700000000,                    # 过期时间
    "iat": 1699996400,                    # 签发时间
    "jti": "a1b2c3d4-uuid",              # Token 唯一 ID（用于黑名单）
    
    # ─── 权限字段 ───
    "role": "editor",                     # 用户角色
    "permissions": ["article:read", "article:write"],  # 权限列表
    "type": "access",                     # Token 类型：access / refresh
}
```

> 💡 **权限列表放 Token 里还是每次查数据库？** 权限少（< 20 个）直接放 Token，省一次数据库查询；权限多或频繁变更，Token 只放角色，权限实时查库。

#### 双 Token 机制（Access + Refresh）

```
 为什么需要两个 Token？
 ═══════════════════════════════════════

 只用 Access Token 的问题：
 · 有效期短（30 分钟）→ 用户频繁重新登录，体验差
 · 有效期长（7 天）  → Token 泄露后风险窗口太大

 解决方案：双 Token
 ─────────────────────────────────────
 Access Token   短命（15-30 分钟） 用于 API 请求
 Refresh Token  长命（7-30 天）    仅用于换取新 Access Token

 用户登录
   ↓
 服务器签发 Access Token + Refresh Token
   ↓
 客户端用 Access Token 请求 API
   ↓
 Access Token 过期
   ↓
 客户端用 Refresh Token 换取新 Access Token（无感刷新）
   ↓
 Refresh Token 也过期 → 需要重新登录
```

```python
from jose import jwt
from datetime import datetime, timedelta
from uuid import uuid4

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"


def create_token_pair(user_id: str, role: str, permissions: list) -> dict:
    """签发 Access + Refresh 双 Token"""
    
    # Access Token（短命）
    access_payload = {
        "sub": user_id,
        "role": role,
        "permissions": permissions,
        "type": "access",
        "jti": str(uuid4()),
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    
    # Refresh Token（长命，不含权限信息）
    refresh_payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": str(uuid4()),
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    
    return {
        "access_token": jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM),
        "refresh_token": jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM),
        "token_type": "bearer",
        "expires_in": 1800,  # 30 分钟（秒）
    }


def refresh_access_token(refresh_token: str) -> dict:
    """用 Refresh Token 换取新的 Access Token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise ValueError("不是有效的 Refresh Token")
        
        if is_token_blacklisted(payload["jti"]):
            raise ValueError("Token 已被吊销")
        
        # 从数据库查询最新权限（而不是用旧 Token 里的）
        user = get_user_from_db(payload["sub"])
        return create_token_pair(user.id, user.role, user.permissions)
    
    except jwt.ExpiredSignatureError:
        raise ValueError("Refresh Token 已过期，请重新登录")
```

#### Token 黑名单机制

JWT 是无状态的——一旦签发，在过期前始终有效。如果用户修改密码、被封禁、或主动登出，**需要一种方式让 Token 立即失效**。

```
 三种 Token 失效方案
 ═══════════════════════════════════════

 ① 短过期 + 不处理（最简单）
    Access Token 设 15 分钟，到期自然失效
    → 适合安全要求不高的场景

 ② 黑名单（推荐）⭐
    Redis 存储被吊销的 Token ID（jti）
    校验时检查黑名单，命中则拒绝
    → 安全性好，性能高

 ③ 版本号（适合全量踢出）
    数据库存  user.token_version = 3
    Token 中  {"ver": 3}
    修改密码时 token_version += 1
    → 所有旧 Token 一次性失效
```

```python
import redis

# Redis 存储黑名单（高性能，支持自动过期）
redis_client = redis.Redis(host="localhost", port=6379, db=0)
BLACKLIST_PREFIX = "token_blacklist:"


def add_to_blacklist(jti: str, expires_in: int):
    """将 Token 加入黑名单"""
    # 过期时间 = Token 原本的剩余时间，自然过期后记录自动清除
    redis_client.setex(f"{BLACKLIST_PREFIX}{jti}", expires_in, "revoked")


def is_token_blacklisted(jti: str) -> bool:
    """检查 Token 是否在黑名单中"""
    return redis_client.exists(f"{BLACKLIST_PREFIX}{jti}") > 0


# ─── 登出接口 ───

@app.post("/auth/logout")
async def logout(user: TokenData = Depends(get_current_user)):
    add_to_blacklist(user.jti, expires_in=1800)
    return {"msg": "已登出"}


# ─── 修改密码：吊销所有 Token ───

@app.post("/auth/change-password")
async def change_password(user: TokenData = Depends(get_current_user)):
    update_user_token_version(user.id)  # version += 1，旧 Token 全部失效
    return {"msg": "密码已修改，请重新登录"}
```

#### 完整的 Token 校验流程

```
 API 请求到来
   ↓
 ① 提取 Authorization Header 中的 Bearer Token
   ↓
 ② jwt.decode() 验签 + 检查过期
   ↓ 失败 → 401 Unauthorized
 ③ 检查 Token 类型（必须是 access）
   ↓ 失败 → 401
 ④ 检查黑名单（Redis 查 jti）
   ↓ 命中 → 401 "Token 已被吊销"
 ⑤ 提取 role / permissions
   ↓
 ⑥ 权限校验（role_required / permission_required）
   ↓ 不满足 → 403 Forbidden
 ⑦ 放行，执行业务逻辑 ✅
```

```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """完整的 Token 校验依赖（含黑名单检查）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token 无效或已过期",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # ① 检查 Token 类型
        if payload.get("type") != "access":
            raise credentials_exception
        
        # ② 检查黑名单
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            raise HTTPException(status_code=401, detail="Token 已被吊销")
        
        # ③ 提取用户信息
        return TokenData(
            user_id=payload["sub"],
            role=payload.get("role", "viewer"),
            permissions=payload.get("permissions", []),
            jti=jti,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.JWTError:
        raise credentials_exception
```

#### Token 安全最佳实践

| 实践 | 说明 |
| :--- | :--- |
| **使用 HTTPS** | Token 明文传输等于裸奔 |
| **Access Token ≤ 30 分钟** | 缩短泄露风险窗口 |
| **Refresh Token 存 httpOnly Cookie** | 前端 JS 无法读取，防 XSS |
| **每次刷新轮换 Refresh Token** | 旧 Refresh Token 立即失效（Rotation） |
| **敏感操作二次验证** | 修改密码、删除账户需要再次输入密码 |
| **不要存 localStorage** | 容易被 XSS 攻击窃取 |

> 💡 **一句话总结**：Access Token 管"能不能调 API"，Refresh Token 管"能不能续命"，黑名单管"能不能紧急踩刹车"。三者配合才是完整的 Token 权限方案。

### 2. OAuth2 Scope 权限

JWT Token 解决了"**你是谁**"的问题，但在第三方应用授权场景下，还需要回答一个更细粒度的问题——"**你能访问我的哪些数据**"。这就是 OAuth2 Scope 的作用。

#### 什么是 OAuth2 Scope

Scope（作用域）是 OAuth2 协议中**限定 Token 访问范围**的机制。你在使用"GitHub 登录"时一定见过类似的授权页面：

```
 ┌─────────────────────────────────────────────────┐
 │  "XXX 应用" 请求访问你的 GitHub 账户               │
 ├─────────────────────────────────────────────────┤
 │                                                 │
 │  该应用将获得以下权限：                            │
 │                                                 │
 │  ✅ 读取你的个人资料          (scope: user:read) │
 │  ✅ 读取你的公开仓库          (scope: repo:read) │
 │  ❌ 删除你的仓库              (未申请)            │
 │  ❌ 管理你的 SSH Key          (未申请)            │
 │                                                 │
 │         [ 授权 ]      [ 拒绝 ]                   │
 └─────────────────────────────────────────────────┘
```

这里的每一项权限就是一个 **Scope**——第三方应用只能拿到你授权的那些 Scope 对应的能力。

```
 传统权限 vs OAuth2 Scope
 ═══════════════════════════════════════

 传统 RBAC：
 用户 ──▶ 角色 ──▶ 权限
 → 用户有什么角色就有什么权限，全或无

 OAuth2 Scope：
 第三方应用 ──请求──▶ 用户授权 ──颁发──▶ 受限 Token
 → Token 只有用户授权的那几个 Scope，精确控制

 核心区别：
 · RBAC 控制的是"用户自己能干什么"
 · Scope 控制的是"第三方应用能代替用户干什么"
```

#### Scope 命名规范

```python
# ──── 常见的 Scope 命名风格 ────

# 风格 1：资源:操作（与权限命名一致，推荐）
scopes = {
    "user:read":    "读取用户信息",
    "user:write":   "修改用户信息",
    "article:read": "读取文章",
    "article:write":"创建/编辑文章",
    "admin:all":    "管理员所有权限",
}

# 风格 2：GitHub 风格（资源.粒度）
scopes = {
    "read:user":    "读取用户信息",
    "write:user":   "修改用户信息",
    "repo":         "仓库完全访问",
    "repo:status":  "仅仓库状态",
}

# 风格 3：Google 风格（URL 形式）
scopes = {
    "https://www.googleapis.com/auth/userinfo.profile": "用户资料",
    "https://www.googleapis.com/auth/gmail.readonly":   "只读邮件",
}
```

| 风格 | 示例 | 适用场景 |
| :--- | :--- | :--- |
| `资源:操作` | `user:read` | 内部 API，与 RBAC 权限统一 |
| `操作:资源` | `read:user` | 开放平台，GitHub 风格 |
| URL 形式 | `googleapis.com/...` | 超大型生态，Google/Microsoft 风格 |

> 💡 **推荐**：内部项目用 `资源:操作` 格式，与 RBAC 权限命名保持一致，避免维护两套命名体系。

#### FastAPI 中定义 Scope

FastAPI 原生支持 OAuth2 Scope，只需在 `OAuth2PasswordBearer` 中声明可用 Scope，然后用 `Security()` 替代 `Depends()` 即可。

```python
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import BaseModel

app = FastAPI()

# ──── 1. 定义系统支持的所有 Scope ────

SCOPES = {
    "user:read":     "读取用户信息",
    "user:write":    "修改用户信息",
    "article:read":  "读取文章",
    "article:write": "创建和编辑文章",
    "article:delete":"删除文章",
    "admin:all":     "管理员完全访问",
}

# 将 scopes 传入 OAuth2PasswordBearer，Swagger UI 会自动显示 Scope 选择框
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scopes=SCOPES,
)
```

```
 传入 scopes 后，Swagger UI 的变化
 ═══════════════════════════════════════

 之前：只有一个 Token 输入框
 之后：登录时可以勾选需要的 Scope ✅

 → 方便开发和测试，无需手动拼 Token
```

```python
# ──── 2. 签发带 Scope 的 Token ────

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"


def create_scoped_token(user_id: str, scopes: list[str]) -> str:
    """签发包含 Scope 信息的 JWT Token"""
    payload = {
        "sub": user_id,
        "scopes": scopes,   # 关键：将用户授权的 Scope 写入 Token
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# 登录时根据用户角色授予不同 Scope
@app.post("/auth/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # form.scopes 是用户在登录时申请的 Scope（Swagger UI 的勾选项）
    # 实际生产中需要校验：用户是否有资格获得这些 Scope
    allowed = get_user_allowed_scopes(user)
    granted = [s for s in form.scopes if s in allowed]
    
    token = create_scoped_token(user.id, scopes=granted)
    return {"access_token": token, "token_type": "bearer"}
```

#### Scope 校验依赖

```python
# ──── 3. 带 Scope 校验的用户解析 ────

class TokenData(BaseModel):
    user_id: str
    scopes: list[str] = []


async def get_current_user_with_scopes(
    security_scopes: SecurityScopes,       # FastAPI 自动注入所需 Scope
    token: str = Depends(oauth2_scheme),
) -> TokenData:
    """解析 Token 并校验 Scope"""
    
    # 构建 401 响应头（OAuth2 规范要求返回所需 scope）
    authenticate_value = (
        f'Bearer scope="{security_scopes.scope_str}"'
        if security_scopes.scopes else "Bearer"
    )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token 无效",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(user_id=user_id, scopes=token_scopes)
    except JWTError:
        raise credentials_exception
    
    # ── 核心：逐个检查所需 Scope 是否在 Token 中 ──
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少 scope: {scope}",
                headers={"WWW-Authenticate": authenticate_value},
            )
    
    return token_data
```

```
 Scope 校验流程
 ═══════════════════════════════════════

 API 声明需要 scopes=["article:write"]
   ↓
 SecurityScopes.scopes = ["article:write"]
   ↓
 解析 Token → scopes: ["article:read", "article:write"]
   ↓
 逐个检查："article:write" in Token.scopes?
   ↓ 是
 放行 ✅

 如果 Token 只有 ["article:read"]：
   ↓
 "article:write" not in Token.scopes
   ↓
 403 Forbidden ❌
```

#### 在接口中使用 Security

```python
# ──── 4. 用 Security() 代替 Depends() ────

# 只需读取权限
@app.get("/users/me")
async def read_own_profile(
    user: TokenData = Security(get_current_user_with_scopes, scopes=["user:read"])
):
    return {"user_id": user.user_id, "scopes": user.scopes}


# 需要写入权限
@app.put("/users/me")
async def update_own_profile(
    user: TokenData = Security(get_current_user_with_scopes, scopes=["user:write"])
):
    return {"msg": "个人资料已更新"}


# 需要多个 Scope（必须同时满足）
@app.delete("/articles/{article_id}")
async def delete_article(
    article_id: int,
    user: TokenData = Security(
        get_current_user_with_scopes,
        scopes=["article:read", "article:delete"]  # 两个都要有
    ),
):
    return {"msg": f"文章 {article_id} 已被删除"}


# 管理员接口
@app.get("/admin/dashboard")
async def admin_dashboard(
    user: TokenData = Security(get_current_user_with_scopes, scopes=["admin:all"])
):
    return {"msg": "管理员仪表盘"}
```

#### Scope 与 RBAC 融合

实际项目中，Scope 和 RBAC 往往**配合使用**——RBAC 决定用户拥有哪些 Scope，Scope 决定 Token 能访问哪些 API：

```
 角色 → Scope 映射
 ═══════════════════════════════════════

 admin   → ["user:read", "user:write", "article:*", "admin:all"]
 editor  → ["article:read", "article:write"]
 viewer  → ["user:read", "article:read"]

 签发流程：
 用户登录 → 查询角色 → 映射 Scope → 写入 Token
```

```python
# 角色 → Scope 映射表
ROLE_SCOPES = {
    "admin":  ["user:read", "user:write", "article:read", "article:write",
               "article:delete", "admin:all"],
    "editor": ["article:read", "article:write"],
    "viewer": ["user:read", "article:read"],
}


def get_user_allowed_scopes(user) -> list[str]:
    """根据用户角色获取允许的 Scope 列表"""
    scopes = set()
    for role in user.roles:
        scopes.update(ROLE_SCOPES.get(role.name, []))
    return list(scopes)
```

#### JWT Token vs OAuth2 Scope vs API Key

| 方案 | 认证方式 | 适用场景 | 权限粒度 |
| :--- | :--- | :--- | :--- |
| **JWT Token** | Bearer Token | 用户登录态 | 角色/权限 |
| **OAuth2 Scope** | Bearer Token + Scope | 第三方应用授权 | Scope 级 |
| **API Key** | 请求头/参数 | 机器调用、开放 API | Key 级 |

> 💡 **一句话总结**：JWT 管"你是谁"，Scope 管"你能做什么"，API Key 管"哪台机器在调"。三者解决的是不同层面的问题，复杂系统中经常同时存在。

### 3. API Key + 限流

JWT 和 OAuth2 Scope 都围绕**用户身份**做权限控制，但很多场景下调用方不是"人"而是"程序"——定时任务、第三方服务、开放 API 调用方。这时候用 **API Key** 更合适。

#### 什么是 API Key

API Key 是一个**预先分配给调用方的密钥字符串**，用于标识"谁在调用"并控制访问权限。

```
 JWT Token vs API Key
 ═══════════════════════════════════════

 JWT Token：
 用户登录 → 服务端签发 → 短期有效 → 自带用户信息
 → 适合：用户登录态、前端调用

 API Key：
 管理员手动创建 → 长期有效 → 关联到调用方/项目
 → 适合：服务间调用、开放 API、第三方集成

 ┌──────────────┬───────────────────┬───────────────────┐
 │              │    JWT Token      │    API Key        │
 ├──────────────┼───────────────────┼───────────────────┤
 │ 颁发方式     │ 登录后自动签发     │ 管理员手动创建     │
 │ 有效期       │ 分钟~小时级       │ 天~永久            │
 │ 携带信息     │ 用户ID、角色、权限 │ 仅标识调用方       │
 │ 使用方       │ 前端/移动端       │ 后端服务/脚本      │
 │ 吊销方式     │ 黑名单/过期       │ 数据库删除/禁用    │
 └──────────────┴───────────────────┴───────────────────┘
```

#### API Key 生成与安全存储

```python
import secrets
import hashlib
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class APIKey(Base):
    """API Key 数据模型"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)          # Key 名称（如 "生产环境-订单服务"）
    key_prefix = Column(String(8), nullable=False)      # Key 前缀（用于识别，如 "sk-a1b2"）
    key_hash = Column(String(64), nullable=False)       # Key 的 SHA-256 哈希（不存明文！）
    scopes = Column(String(500), default="")            # 允许的权限范围
    is_active = Column(Boolean, default=True)           # 是否启用
    rate_limit = Column(Integer, default=100)           # 每分钟请求上限
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)        # 过期时间（可选）


def generate_api_key(name: str, scopes: list[str] = None) -> dict:
    """生成新的 API Key"""
    
    # 1. 生成随机 Key（48 字节 → 64 字符的 hex 字符串）
    raw_key = secrets.token_hex(32)
    prefix = f"sk-{raw_key[:4]}"       # 前缀用于日志和识别
    full_key = f"{prefix}-{raw_key}"   # 完整 Key 返回给用户
    
    # 2. 哈希存储（和密码一样，绝不存明文）
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    # 3. 存入数据库
    api_key = APIKey(
        name=name,
        key_prefix=prefix,
        key_hash=key_hash,
        scopes=",".join(scopes or []),
    )
    db.add(api_key)
    db.commit()
    
    # 4. 返回明文 Key（仅此一次，之后无法找回）
    return {
        "api_key": full_key,           # ⚠️ 只展示一次！
        "prefix": prefix,
        "name": name,
        "msg": "请妥善保存，此 Key 不会再次显示",
    }
```

```
 ⚠️ 安全要点
 ═══════════════════════════════════════

 · API Key 只在创建时返回明文，之后只存哈希
 · 查询时：用 SHA-256(用户传入的Key) 去数据库匹配
 · 类比密码：你不会明文存密码，API Key 也一样
 · 前缀（sk-a1b2）用于日志排查，不暴露完整 Key
```

#### FastAPI 中校验 API Key

```python
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from datetime import datetime

app = FastAPI()

# 从请求头 X-API-Key 中提取 Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str = Security(api_key_header),
) -> APIKey:
    """校验 API Key 并返回关联信息"""
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 API Key，请在请求头中添加 X-API-Key",
        )
    
    # 1. 哈希后查数据库
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    key_record = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True,
    ).first()
    
    if not key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key 无效或已被禁用",
        )
    
    # 2. 检查过期
    if key_record.expires_at and key_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key 已过期",
        )
    
    # 3. 更新最后使用时间
    key_record.last_used_at = datetime.utcnow()
    db.commit()
    
    return key_record


def require_scope(scope: str):
    """检查 API Key 是否拥有指定 Scope"""
    async def checker(key: APIKey = Depends(verify_api_key)):
        key_scopes = key.scopes.split(",") if key.scopes else []
        if scope not in key_scopes and "*" not in key_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"此 API Key 缺少权限: {scope}",
            )
        return key
    return checker


# ──── 使用示例 ────

@app.get("/api/v1/articles")
async def list_articles(key: APIKey = Depends(require_scope("article:read"))):
    return {"articles": [...], "caller": key.name}

@app.post("/api/v1/articles")
async def create_article(key: APIKey = Depends(require_scope("article:write"))):
    return {"msg": "文章创建成功"}
```

#### API Key 限流

开放 API 最怕被"刷爆"——不限流的 API 等于邀请别人 DDoS 你。限流通常是**按 API Key 维度**控制每分钟/每小时的请求次数。

```
 常见限流算法
 ═══════════════════════════════════════

 ① 固定窗口（Fixed Window）
    每分钟计数，到 60 秒清零
    缺点：窗口边界可能突发 2x 流量

 ② 滑动窗口（Sliding Window）⭐ 推荐
    最近 60 秒内的请求数
    平滑限流，无边界突发

 ③ 令牌桶（Token Bucket）
    桶里定速放令牌，请求消耗令牌
    允许短时间突发，适合弹性场景

 ④ 漏桶（Leaky Bucket）
    请求排队，匀速处理
    严格平滑，适合支付等场景
```

##### 基于 Redis 的滑动窗口限流

```python
import redis
import time
from fastapi import HTTPException

redis_client = redis.Redis(host="localhost", port=6379, db=0)


class RateLimiter:
    """基于 Redis 滑动窗口的限流器"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> dict:
        """
        检查是否超出限流
        
        参数:
            key: 限流维度标识（如 API Key 的 prefix）
            max_requests: 窗口内最大请求数
            window_seconds: 窗口时间（秒）
        """
        now = time.time()
        window_start = now - window_seconds
        pipe_key = f"rate_limit:{key}"
        
        # 使用 Redis Pipeline 原子操作
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(pipe_key, 0, window_start)   # 移除窗口外的记录
        pipe.zadd(pipe_key, {str(now): now})               # 添加当前请求
        pipe.zcard(pipe_key)                               # 统计窗口内请求数
        pipe.expire(pipe_key, window_seconds)              # 设置过期时间
        results = pipe.execute()
        
        request_count = results[2]
        
        return {
            "allowed": request_count <= max_requests,
            "current": request_count,
            "limit": max_requests,
            "remaining": max(0, max_requests - request_count),
            "reset_at": int(now + window_seconds),
        }


rate_limiter = RateLimiter(redis_client)
```

##### 限流中间件

```python
from fastapi import Request
from fastapi.responses import JSONResponse


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """全局限流中间件（按 API Key 维度）"""
    
    # 跳过不需要限流的路径
    skip_paths = ["/docs", "/openapi.json", "/health"]
    if any(request.url.path.startswith(p) for p in skip_paths):
        return await call_next(request)
    
    # 提取 API Key
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return await call_next(request)  # 无 Key 的请求由认证中间件处理
    
    # 查询该 Key 的限流配额
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    key_record = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()
    
    if not key_record:
        return await call_next(request)  # 无效 Key 由认证依赖处理
    
    # 执行限流检查
    result = rate_limiter.check_rate_limit(
        key=key_record.key_prefix,
        max_requests=key_record.rate_limit,
        window_seconds=60,
    )
    
    # 设置标准限流响应头
    response = await call_next(request) if result["allowed"] else JSONResponse(
        status_code=429,
        content={
            "error": "请求过于频繁",
            "detail": f"限额 {result['limit']} 次/分钟，已使用 {result['current']} 次",
            "retry_after": result["reset_at"] - int(time.time()),
        },
    )
    
    response.headers["X-RateLimit-Limit"] = str(result["limit"])
    response.headers["X-RateLimit-Remaining"] = str(result["remaining"])
    response.headers["X-RateLimit-Reset"] = str(result["reset_at"])
    
    return response
```

```
 限流响应头（行业标准）
 ═══════════════════════════════════════

 X-RateLimit-Limit:     100       ← 每分钟配额
 X-RateLimit-Remaining: 67        ← 剩余次数
 X-RateLimit-Reset:     1711012800 ← 重置时间戳

 超限时返回：
 HTTP 429 Too Many Requests
 Retry-After: 23                   ← 建议等待秒数
```

#### API Key 管理接口

一个完整的 API Key 系统还需要管理功能——创建、列表、吊销：

```python
from pydantic import BaseModel


class CreateKeyRequest(BaseModel):
    name: str                      # Key 用途描述
    scopes: list[str] = []         # 授予的权限
    rate_limit: int = 100          # 每分钟请求上限
    expires_days: int | None = None  # 过期天数（None = 永不过期）


# ──── 创建 API Key ────

@app.post("/admin/api-keys")
async def create_key(
    req: CreateKeyRequest,
    user: TokenData = Depends(require_role("admin")),
):
    result = generate_api_key(
        name=req.name,
        scopes=req.scopes,
    )
    return result


# ──── 列出所有 API Key ────

@app.get("/admin/api-keys")
async def list_keys(user: TokenData = Depends(require_role("admin"))):
    keys = db.query(APIKey).all()
    return {
        "keys": [
            {
                "id": k.id,
                "name": k.name,
                "prefix": k.key_prefix,       # 只返回前缀，不返回完整 Key
                "scopes": k.scopes.split(","),
                "rate_limit": k.rate_limit,
                "is_active": k.is_active,
                "last_used_at": k.last_used_at,
                "created_at": k.created_at,
            }
            for k in keys
        ]
    }


# ──── 吊销 API Key ────

@app.delete("/admin/api-keys/{key_id}")
async def revoke_key(
    key_id: int,
    user: TokenData = Depends(require_role("admin")),
):
    key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Key 不存在")
    
    key.is_active = False
    db.commit()
    return {"msg": f"API Key [{key.key_prefix}] 已吊销"}
```

#### API Key 最佳实践

| 实践 | 说明 |
| :--- | :--- |
| **哈希存储** | Key 只存 SHA-256 哈希，类比密码绝不存明文 |
| **前缀标识** | `sk-a1b2` 前缀便于日志排查，不暴露完整 Key |
| **分级限流** | 免费用户 100 次/分，付费用户 1000 次/分 |
| **Scope 隔离** | 不同 Key 授予不同权限，遵循最小权限原则 |
| **过期策略** | 生产环境建议设置过期时间，定期轮换 |
| **HTTPS 传输** | API Key 是明文传输，必须走 HTTPS |
| **监控告警** | 限流命中率飙升时及时告警，可能是攻击或滥用 |

> 💡 **一句话总结**：API Key 是"机器对机器"认证的标配，搭配限流一起用。生成时只展示一次，存储时只存哈希，使用时配合 Scope 和限流控制风险。

---

## 七、最佳实践与安全

### 1. 权限设计原则

权限系统写得好不好，代码水平只是一方面——更重要的是**设计理念**。以下三条原则是安全领域的基石，无论你用什么技术栈都适用。

#### 最小权限原则（Principle of Least Privilege）

每个用户、角色、API Key 只授予**完成工作所需的最少权限**，不多给一个。

```
 ❌ 反例：图省事给大权限
 ═══════════════════════════════════════

 "这个实习生需要看文章数据"
 → 给了 admin 角色（因为 admin 什么都能看）
 → 结果实习生可以删库跑路 💀

 ✅ 正例：精确授权
 ═══════════════════════════════════════

 "这个实习生需要看文章数据"
 → 创建 article_viewer 角色
 → 只绑定 article:read 权限
 → 实习生只能看，不能改、不能删 ✅
```

```python
# ──── 最小权限的代码体现 ────

# ❌ 不要这样：用角色做粗粒度判断
@app.get("/articles/{id}")
async def get_article(user=Depends(require_role("admin", "editor", "viewer"))):
    return article  # admin 能看，但也能顺便调 delete 接口

# ✅ 应该这样：用权限做精细控制
@app.get("/articles/{id}")
async def get_article(user=Depends(require_permission("article:read"))):
    return article  # 只校验 read 权限，与角色解耦

# ✅ API Key 也一样：按需分配 Scope
generate_api_key(
    name="数据分析脚本",
    scopes=["article:read"],       # 只给读取权限
    # scopes=["article:*"],        # ❌ 不要给通配符
)
```

| 场景 | ❌ 过度授权 | ✅ 最小权限 |
| :--- | :--- | :--- |
| 实习生看数据 | 给 admin 角色 | 给 viewer 角色 + article:read |
| 定时脚本同步 | API Key 全部权限 | API Key 只给 data:read |
| 前端调用 | Token 含所有 Scope | Token 只含当前页面所需 Scope |
| 微服务间调用 | 共享 admin 账号 | 每个服务独立 Key + 独立 Scope |

#### 默认拒绝原则（Default Deny）

权限系统的默认行为应该是**拒绝一切**，只有明确授权的才放行。

```
 两种设计思路对比
 ═══════════════════════════════════════

 默认允许（黑名单模式）❌
 ──────────────────────
 "除了这几个接口需要权限，其他都可以随便访问"
 → 新加的接口忘了配权限 → 裸奔 💀
 → 攻击者专找你没有覆盖到的接口

 默认拒绝（白名单模式）✅
 ──────────────────────
 "除了这几个公开接口，其他全部需要权限"
 → 新加的接口自动受保护 ✅
 → 你忘了配权限？那就谁都访问不了（安全失败）
```

```python
# ──── 默认拒绝的代码实现 ────

# ✅ 中间件：默认拦截所有请求
PUBLIC_PATHS = [
    "/api/auth/login",
    "/api/auth/register",
    "/api/public/",
    "/health",
    "/docs",
]

@app.middleware("http")
async def default_deny_middleware(request: Request, call_next):
    # 白名单路径直接放行
    if any(request.url.path.startswith(p) for p in PUBLIC_PATHS):
        return await call_next(request)
    
    # 其他所有路径都必须携带有效 Token
    token = request.headers.get("Authorization")
    if not token:
        return JSONResponse(
            status_code=401,
            content={"error": "需要认证"},
        )
    
    # 校验 Token ...
    return await call_next(request)


# ✅ Casbin 策略：默认拒绝
# policy_effect: e = some(where (p.eft == allow))
# → 只有匹配到 allow 规则才放行，没有规则 = 拒绝
```

> 💡 **关键心态**：新增功能时不是"要不要加权限"，而是"权限默认就有，需要的话才开放白名单"。

#### 职责分离原则（Separation of Duties）

关键操作不应由同一个人/角色独立完成，需要**多方参与**，避免权力过于集中。

```
 现实类比
 ═══════════════════════════════════════

 银行转账 100 万：
 · 操作员发起转账 → 主管审批 → 系统执行
 · 操作员不能自己审批自己发起的转账

 系统设计：
 · 数据导出权限 ≠ 数据删除权限
 · 创建用户 ≠ 审核用户 ≠ 删除用户
 · 修改配置 ≠ 发布上线
```

```python
# ──── 职责分离的代码体现 ────

# 示例：文章发布流程（创建 → 审核 → 发布，三个角色）

@app.post("/articles")
async def create_article(
    user=Depends(require_permission("article:write")),
):
    """编辑创建文章（草稿状态）"""
    article = Article(author_id=user.user_id, status="draft")
    db.add(article)
    return {"msg": "草稿已保存", "status": "draft"}


@app.post("/articles/{id}/review")
async def review_article(
    id: int,
    user=Depends(require_permission("article:review")),
):
    """审核员审核文章"""
    article = get_article(id)
    
    # 审核员不能审核自己的文章
    if article.author_id == user.user_id:
        raise HTTPException(status_code=403, detail="不能审核自己的文章")
    
    article.status = "reviewed"
    article.reviewer_id = user.user_id
    return {"msg": "审核通过", "status": "reviewed"}


@app.post("/articles/{id}/publish")
async def publish_article(
    id: int,
    user=Depends(require_permission("article:publish")),
):
    """发布者发布文章（必须已审核）"""
    article = get_article(id)
    
    if article.status != "reviewed":
        raise HTTPException(status_code=400, detail="文章未审核，无法发布")
    
    # 发布者不能是作者或审核者（三权分立）
    if user.user_id in (article.author_id, article.reviewer_id):
        raise HTTPException(status_code=403, detail="发布者不能是作者或审核者")
    
    article.status = "published"
    return {"msg": "文章已发布", "status": "published"}
```

```
 文章发布的三权分立
 ═══════════════════════════════════════

 编辑（article:write）
   ↓ 创建草稿
 审核员（article:review）      ← 不能是作者
   ↓ 审核通过
 发布者（article:publish）     ← 不能是作者或审核员
   ↓ 正式发布

 → 任何一篇文章都至少经过 3 个人的手
```

#### 三大原则速查

| 原则 | 核心思想 | 一句话口诀 |
| :--- | :--- | :--- |
| **最小权限** | 只给必要的权限，不多给 | "够用就好，多了是祸" |
| **默认拒绝** | 没明确允许的一律拒绝 | "没说能做的，就是不能做" |
| **职责分离** | 关键操作需多人参与 | "自己不能审批自己" |

> 💡 这三条原则不仅适用于代码层面，在**数据库权限、服务器权限、云平台 IAM**中同样适用。把它们内化为设计习惯，权限系统就不会出大问题。

### 2. 常见安全陷阱

即使理解了权限模型和原则，实际开发中仍然有很多"看起来做了权限控制，实际上形同虚设"的坑。本节梳理最常见的三类安全陷阱。

#### 陷阱一：前端权限校验 ≠ 安全

这是**最常见、最危险**的误区——在前端（JavaScript / Vue / React）做了按钮隐藏或路由拦截，就认为"没权限的人访问不了"。

```
 前端校验只是 UI 优化，不是安全措施
 ═══════════════════════════════════════

 前端隐藏了「删除」按钮
   ↓
 用户打开浏览器 DevTools → 找到 API 地址
   ↓
 直接用 curl / Postman 调用 DELETE /api/users/123
   ↓
 后端没有校验 → 数据被删除 💀

 → 前端是"君子锁"，后端才是"防盗门"
```

##### ❌ 典型错误：只在前端拦截

```javascript
// 前端代码（React 示例）
function UserList({ currentUser }) {
    return (
        <div>
            {/* "我藏起来了，用户看不到！" */}
            {currentUser.role === "admin" && (
                <button onClick={() => deleteUser(id)}>删除用户</button>
            )}
        </div>
    );
}
```

```python
# 后端代码 ❌ 没有任何权限校验
@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    db.execute(f"DELETE FROM users WHERE id = {user_id}")  # 裸奔！
    return {"msg": "已删除"}
```

攻击者只需一行命令：

```bash
# 任何人都可以调用，因为后端根本没校验
curl -X DELETE http://yoursite.com/api/users/123
```

##### ✅ 正确做法：前后端都要校验

```python
# 后端代码 ✅ 必须有权限校验
@app.delete("/api/users/{user_id}")
async def delete_user(
    user_id: int,
    user: TokenData = Depends(require_permission("user:delete")),
):
    """只有拥有 user:delete 权限的用户才能调用"""
    db.execute("DELETE FROM users WHERE id = :id", {"id": user_id})
    return {"msg": f"用户 {user_id} 已被 {user.username} 删除"}
```

##### 前后端的正确分工

| 层级 | 职责 | 做的事 |
| :--- | :--- | :--- |
| **前端** | 用户体验优化 | 隐藏无权限的按钮、灰化不可用功能、提前提示 |
| **后端** | 真正的安全防线 | 校验 Token、校验角色/权限、校验数据归属 |

> 💡 **口诀**：前端管"看不看得到"，后端管"做不做得到"。两者缺一不可，但**安全依赖后端**。

#### 陷阱二：水平越权与垂直越权

越权（Broken Access Control）是 OWASP Top 10 常年排名第一的安全问题，分为两种：

```
 两种越权对比
 ═══════════════════════════════════════

 垂直越权（Privilege Escalation）
 ─────────────────────────────
 低权限用户 → 执行高权限操作
 普通用户调用了管理员的「删除用户」接口

 水平越权（Horizontal Privilege Escalation）
 ─────────────────────────────
 同级用户 → 访问其他用户的数据
 用户 A 通过修改 URL 中的 ID 查看了用户 B 的订单

 垂直 = 往上爬（越级操作）
 水平 = 往旁边走（越界访问）
```

##### 垂直越权示例

```python
# ❌ 只检查了登录，没检查角色
@app.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    user: TokenData = Depends(get_current_user),  # 只验证了登录
):
    # 普通用户也能调用这个接口！
    db.execute("DELETE FROM users WHERE id = :id", {"id": user_id})
    return {"msg": "已删除"}


# ✅ 必须检查管理员权限
@app.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    user: TokenData = Depends(require_role("admin")),  # 校验角色
):
    db.execute("DELETE FROM users WHERE id = :id", {"id": user_id})
    return {"msg": f"用户 {user_id} 已被管理员 {user.username} 删除"}
```

##### 水平越权示例（更隐蔽、更常见）

```python
# ❌ 用户可以通过修改 order_id 查看别人的订单
@app.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    user: TokenData = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    return order  # 没有检查这个订单是不是属于当前用户！


# ✅ 必须校验数据归属
@app.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    user: TokenData = Depends(get_current_user),
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user.user_id,  # 关键：加上归属校验
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order
```

```
 水平越权的攻击场景
 ═══════════════════════════════════════

 正常请求：GET /orders/1001    → 返回用户 A 自己的订单 ✅
 篡改请求：GET /orders/1002    → 返回用户 B 的订单 💀

 攻击者只需要遍历 ID：
 GET /orders/1001
 GET /orders/1002
 GET /orders/1003
 ...
 → 把所有用户的订单数据都爬走了
```

##### 防御水平越权的通用模式

```python
# ──── 通用的数据归属校验工具 ────

async def get_owned_resource(
    model,
    resource_id: int,
    user: TokenData,
    owner_field: str = "user_id",
):
    """通用资源归属校验：确保当前用户是资源的所有者"""
    resource = db.query(model).filter(model.id == resource_id).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")
    
    # 管理员可以访问所有资源
    if user.role == "admin":
        return resource
    
    # 普通用户只能访问自己的资源
    if getattr(resource, owner_field) != user.user_id:
        raise HTTPException(status_code=403, detail="无权访问该资源")
    
    return resource


# 使用
@app.get("/orders/{order_id}")
async def get_order(order_id: int, user=Depends(get_current_user)):
    return await get_owned_resource(Order, order_id, user)

@app.get("/profiles/{profile_id}")
async def get_profile(profile_id: int, user=Depends(get_current_user)):
    return await get_owned_resource(Profile, profile_id, user)
```

##### 两种越权对比

| 类型 | 攻击方式 | 案例 | 防御手段 |
| :--- | :--- | :--- | :--- |
| **垂直越权** | 低权限用户调用高权限接口 | 普通用户调 `/admin/delete` | 校验角色/权限（`require_role`） |
| **水平越权** | 同级用户访问他人数据 | 用户 A 看用户 B 的订单 | 校验数据归属（`WHERE user_id = ?`） |

> 💡 **关键点**：垂直越权靠**角色校验**防，水平越权靠**数据归属校验**防。很多开发者只做了前者，忽略了后者。

#### 陷阱三：IDOR（不安全的直接对象引用）

IDOR（Insecure Direct Object Reference）是水平越权的一个特例——直接把内部对象 ID 暴露在 URL 或参数中，攻击者只需要**猜测或遍历 ID** 就能访问他人数据。

```
 IDOR 攻击原理
 ═══════════════════════════════════════

 你的 API 设计：
 GET /api/invoices/10086          ← 自增整数 ID，可预测

 攻击者操作：
 GET /api/invoices/10085          ← 上一张发票（别人的）
 GET /api/invoices/10087          ← 下一张发票（别人的）
 for id in range(1, 100000):      ← 遍历所有发票 💀
     GET /api/invoices/{id}

 核心问题：ID 可预测 + 没有归属校验 = 数据泄露
```

##### ❌ IDOR 漏洞代码

```python
# 使用自增整数 ID，且没有归属校验
@app.get("/api/invoices/{invoice_id}")
async def get_invoice(invoice_id: int, user=Depends(get_current_user)):
    # 只用 ID 查询，没有校验 user_id
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    return invoice  # 任何人都能看到任何发票！


# 更危险：直接在 URL 中暴露文件路径
@app.get("/api/files")
async def get_file(path: str, user=Depends(get_current_user)):
    return FileResponse(path)  # 路径遍历攻击：../../etc/passwd 💀
```

##### ✅ 修复方案一：使用 UUID 替代自增 ID

```python
import uuid

class Invoice(Base):
    __tablename__ = "invoices"
    
    # 使用 UUID 作为外部标识，不可预测
    id = Column(Integer, primary_key=True)           # 内部 ID
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()),
                       unique=True, index=True)       # 外部 ID
    user_id = Column(Integer, ForeignKey("users.id"))


@app.get("/api/invoices/{public_id}")
async def get_invoice(public_id: str, user=Depends(get_current_user)):
    invoice = db.query(Invoice).filter(
        Invoice.public_id == public_id,
        Invoice.user_id == user.user_id,  # 仍然需要归属校验！
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    return invoice
```

```
 UUID vs 自增 ID 的区别
 ═══════════════════════════════════════

 自增 ID：     1, 2, 3, 4, 5, ...
               → 可预测，可遍历

 UUID：        a3f8b2c1-7d4e-4f5a-9c2b-1e3d5f7a9b0c
               → 不可预测，无法遍历
               → 但 UUID 不替代权限校验！依然需要检查归属
```

##### ✅ 修复方案二：签名 URL（适合文件/临时资源）

```python
from itsdangerous import URLSafeTimedSerializer

signer = URLSafeTimedSerializer("your-secret-key")


def generate_signed_url(resource_id: int, user_id: int) -> str:
    """生成带签名的临时访问链接"""
    token = signer.dumps({"resource_id": resource_id, "user_id": user_id})
    return f"/api/files/download?token={token}"


@app.get("/api/files/download")
async def download_file(token: str):
    try:
        data = signer.loads(token, max_age=3600)  # 1 小时有效
    except Exception:
        raise HTTPException(status_code=403, detail="链接无效或已过期")
    
    resource = get_resource(data["resource_id"])
    return FileResponse(resource.path)
```

##### ✅ 修复方案三：间接引用映射

```python
# 不暴露真实 ID，使用会话级映射
from fastapi import Request

@app.get("/api/documents")
async def list_documents(request: Request, user=Depends(get_current_user)):
    """列表接口返回映射后的 ref，而非真实 ID"""
    docs = db.query(Document).filter(Document.user_id == user.user_id).all()
    
    # 在会话中建立映射：ref → 真实 ID
    ref_map = {}
    result = []
    for i, doc in enumerate(docs):
        ref = f"doc_{i}"
        ref_map[ref] = doc.id
        result.append({"ref": ref, "title": doc.title})
    
    # 将映射存入 Redis（绑定用户会话）
    redis.setex(f"ref_map:{user.user_id}", 3600, json.dumps(ref_map))
    return result


@app.get("/api/documents/{ref}")
async def get_document(ref: str, user=Depends(get_current_user)):
    """通过 ref 查找，攻击者无法猜测"""
    ref_map = json.loads(redis.get(f"ref_map:{user.user_id}") or "{}")
    real_id = ref_map.get(ref)
    
    if not real_id:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return db.query(Document).filter(Document.id == real_id).first()
```

##### IDOR 防御方案对比

| 方案 | 适用场景 | 复杂度 | 安全性 |
| :--- | :--- | :--- | :--- |
| **UUID 替代自增 ID** | 通用，大部分 API | ⭐ 低 | ⭐⭐⭐ 搭配归属校验 |
| **签名 URL** | 文件下载、临时资源 | ⭐⭐ 中 | ⭐⭐⭐⭐ 时效 + 签名 |
| **间接引用映射** | 高安全场景（金融等） | ⭐⭐⭐ 高 | ⭐⭐⭐⭐⭐ 完全隐藏真实 ID |

#### 安全陷阱 Checklist

开发每个 API 接口时，对照以下清单自检：

| ✅ 检查项 | 说明 |
| :--- | :--- |
| 后端是否校验了权限？ | 不依赖前端隐藏按钮 |
| 是否校验了角色/权限？ | 防止垂直越权 |
| 是否校验了数据归属？ | 防止水平越权 |
| 外部 ID 是否不可预测？ | 使用 UUID 或签名，防 IDOR |
| 错误信息是否足够模糊？ | 返回 404 而非 403，避免泄露资源存在性 |
| 批量接口是否做了限制？ | 防止通过遍历批量窃取数据 |

> 💡 **一句话总结**：权限安全的本质是——**永远不要信任客户端**，所有校验都必须在后端完成。ID 不可预测是第二道防线，归属校验才是根本。

### 3. 权限管理选型建议

不同项目规模和业务复杂度，适合的权限方案差异很大。选错了方案，要么**杀鸡用牛刀**（小项目引入 OPA），要么**小马拉大车**（大型系统手写装饰器）。

#### 选型决策流程

```
 你的项目需要什么级别的权限管理？
 ═══════════════════════════════════════

 Q1: 有几个角色？
 │
 ├─ 2~3 个（如 admin / user）
 │   → 小项目方案（装饰器 + 简单 RBAC）
 │
 ├─ 5~20 个，且权限规则可能变化
 │   │
 │   ├─ 单体应用？
 │   │   → 中型项目方案（FastAPI Depends + Casbin）
 │   │
 │   └─ 微服务架构？
 │       → 大型项目方案（OPA / 权限网关）
 │
 └─ 20+ 个，且需要动态条件（时间、部门、地域）
     → 大型项目方案 + ABAC 策略引擎
```

#### 小项目：装饰器 + 简单 RBAC

**适用场景**：个人项目、内部工具、MVP 原型、用户量 < 1000

```python
# ──── 小项目的权限方案：简单够用 ────

# 整套方案只需要 3 个文件：

# 1. auth.py —— 认证 + 权限装饰器
def login_required(f):
    """登录校验"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = verify_token(request.headers.get("Authorization"))
        if not user:
            return jsonify({"error": "未登录"}), 401
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """角色校验"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            if request.current_user.role not in roles:
                return jsonify({"error": "权限不足"}), 403
            return f(*args, **kwargs)
        return decorator
    return decorator


# 2. models.py —— 用户表带一个 role 字段就够了
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password_hash = Column(String(128))
    role = Column(String(20), default="user")  # admin / editor / user


# 3. views.py —— 在需要的地方加装饰器
@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    return render_template("admin.html")
```

```
 小项目方案特点
 ═══════════════════════════════════════

 ✅ 优点                          ❌ 局限
 ─────                          ─────
 · 零依赖，纯 Python             · 角色写死在代码里
 · 10 分钟实现                   · 权限变更需要改代码重部署
 · 容易理解和维护                 · 不支持动态权限分配
 · 适合快速迭代                   · 不适合多租户场景
```

#### 中型项目：FastAPI 依赖注入 + Casbin

**适用场景**：团队协作产品、SaaS 应用、用户量 1K ~ 100K、需要动态配置权限

```python
# ──── 中型项目的权限方案：灵活可配 ────

import casbin
from fastapi import FastAPI, Depends

app = FastAPI()

# 1. Casbin 策略引擎（策略可以存数据库，运行时热更新）
enforcer = casbin.Enforcer("model.conf", "policy.csv")

# 2. FastAPI 依赖注入 —— 权限校验
def require_casbin_permission(resource: str, action: str):
    async def checker(user: TokenData = Depends(get_current_user)):
        if not enforcer.enforce(user.username, resource, action):
            raise HTTPException(status_code=403, detail="权限不足")
        return user
    return checker

# 3. 路由级别的权限控制
@app.get("/articles")
async def list_articles(user=Depends(require_casbin_permission("/articles", "read"))):
    return {"articles": [...]}

@app.post("/articles")
async def create_article(user=Depends(require_casbin_permission("/articles", "write"))):
    return {"msg": "创建成功"}

# 4. 管理接口 —— 运行时增删策略（无需重启）
@app.post("/admin/policies")
async def add_policy(
    sub: str, obj: str, act: str,
    user=Depends(require_role("admin")),
):
    enforcer.add_policy(sub, obj, act)
    enforcer.save_policy()
    return {"msg": f"已添加策略: {sub} -> {obj} -> {act}"}
```

```
 中型项目方案特点
 ═══════════════════════════════════════

 ✅ 优点                          ❌ 局限
 ─────                          ─────
 · 策略与代码分离                 · 需要学习 Casbin 的模型语法
 · 支持运行时热更新               · 单进程，不适合分布式部署
 · 支持 RBAC / ABAC 切换         · 策略量大时性能需关注
 · 社区活跃，文档完善              · 多服务间策略同步需额外方案
```

#### 大型项目：OPA + 微服务权限网关

**适用场景**：微服务架构、多团队协作、用户量 100K+、需要集中管控

```
 大型项目的权限架构
 ═══════════════════════════════════════

 客户端
   ↓ 请求
 API 网关（Kong / Envoy / Nginx）
   ↓ 认证（JWT 验签）
   ↓ 粗粒度鉴权（路由级别）
 权限服务（OPA / 自建）
   ↓ 细粒度鉴权（资源 + 操作 + 属性）
 业务微服务
   ↓ 数据归属校验（防水平越权）
 数据库

 → 三层防线：网关认证 → 权限服务鉴权 → 业务层归属校验
```

```python
# ──── 大型项目的权限方案：集中管控 ────

# 1. 权限网关中间件（每个微服务共用）
class PermissionMiddleware:
    def __init__(self, app, opa_url: str):
        self.app = app
        self.opa_url = opa_url
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # 向 OPA 查询权限
            allowed = await self.check_opa(
                user=request.state.user,
                path=request.url.path,
                method=request.method,
            )
            
            if not allowed:
                response = JSONResponse(
                    status_code=403,
                    content={"error": "权限不足"},
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
    
    async def check_opa(self, user, path, method) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.opa_url}/v1/data/authz/allow", json={
                "input": {
                    "user": {"role": user.role, "department": user.department},
                    "resource": path,
                    "action": method,
                }
            })
            return resp.json().get("result", False)


# 2. 每个微服务只需一行注册
app.add_middleware(PermissionMiddleware, opa_url="http://opa-service:8181")
```

```
 大型项目方案特点
 ═══════════════════════════════════════

 ✅ 优点                          ❌ 局限
 ─────                          ─────
 · 策略集中管控，统一审计          · 架构复杂，运维成本高
 · 跨语言、跨服务统一鉴权         · Rego 学习曲线陡峭
 · 支持 ABAC 复杂条件             · 每次请求多一次网络调用
 · 天然适配 K8s / 云原生          · 需要策略管理平台
```

#### 框架对比总结表

| 维度 | 手写装饰器 | FastAPI Depends | Casbin | OPA | Django 内置 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **学习成本** | ⭐ 极低 | ⭐⭐ 低 | ⭐⭐ 低 | ⭐⭐⭐⭐ 高 | ⭐⭐ 低 |
| **灵活性** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **策略热更新** | ❌ | ❌ | ✅ | ✅ | ✅（Admin 后台） |
| **支持模型** | ACL / 简单 RBAC | RBAC | RBAC / ABAC | RBAC / ABAC / PBAC | RBAC（Group + Permission） |
| **多服务支持** | ❌ | ❌ | ⚠️ 需额外方案 | ✅ 天然支持 | ❌ |
| **适合规模** | 小型 | 中小型 | 中型 | 大型 / 微服务 | 中型（Django 项目） |
| **部署复杂度** | 无（内嵌） | 无（内嵌） | 无（Python 库） | 高（独立服务） | 无（Django 自带） |

#### 选型口诀

```
 权限选型四句话
 ═══════════════════════════════════════

 角色少、变化少 → 装饰器搞定
 角色多、要热更 → Casbin 上阵
 微服务、跨语言 → OPA 出手
 用 Django？    → 先用内置的，不够再加
```

> 💡 **选型的核心原则**：**不要过度设计**。从最简单的方案开始，随着业务增长逐步演进。一个运行良好的 `@role_required("admin")` 装饰器，比一个配置错误的 OPA 策略安全得多。

---

## 八、总结

### 1. 核心概念速查表

#### 基础概念

| 概念 | 一句话解释 | 章节 |
| :--- | :--- | :--- |
| **认证（Authentication）** | 验证"你是谁"——用户名密码、JWT、OAuth | 一 |
| **授权（Authorization）** | 验证"你能做什么"——角色、权限、策略 | 一 |
| **ACL** | 每个资源维护一张"谁能访问"的清单 | 一 |
| **RBAC** | 用户 → 角色 → 权限，最常用的权限模型 | 一、五 |
| **ABAC** | 基于属性（用户/资源/环境）动态判断权限 | 一 |
| **PBAC** | 基于策略语言（如 Rego）描述权限规则 | 一 |

#### 实现方式

| 方式 | 适用场景 | 关键代码 | 章节 |
| :--- | :--- | :--- | :--- |
| **装饰器** | 单个接口的权限控制 | `@role_required("admin")` | 二 |
| **中间件** | 全局统一拦截（认证 + 基础权限） | `@app.before_request` | 二 |
| **依赖注入** | FastAPI 的权限控制方式 | `Depends(require_role(...))` | 三 |
| **Security Scope** | OAuth2 第三方授权场景 | `Security(scopes=["user:read"])` | 三 |
| **手写 RBAC** | 不依赖框架的完整权限系统 | User → Role → Permission 多对多 | 二 |

#### 框架与工具

| 工具 | 定位 | 适合规模 | 章节 |
| :--- | :--- | :--- | :--- |
| **FastAPI Depends** | 内置依赖注入做权限校验 | 中小型 | 三 |
| **fastapi-users** | 开箱即用的用户管理 + 认证 | 中小型 | 三 |
| **Casbin** | 通用策略引擎，支持 RBAC/ABAC | 中型 | 四 |
| **OPA** | 独立策略服务，Rego 语言 | 大型 / 微服务 | 四 |
| **python-jose** | JWT 编解码库 | 通用 | 四 |
| **Authlib** | OAuth 客户端 / 服务端完整实现 | 通用 | 四 |

#### API 安全

| 概念 | 说明 | 章节 |
| :--- | :--- | :--- |
| **JWT Token** | 无状态认证令牌，含用户信息和签名 | 六 |
| **Access + Refresh Token** | 短期访问令牌 + 长期刷新令牌组合 | 六 |
| **OAuth2 Scope** | 第三方授权中限定 Token 的权限范围 | 六 |
| **API Key** | 服务间调用的身份凭证 | 六 |
| **限流（Rate Limiting）** | 限制单位时间内的请求次数，防滥用 | 六 |

#### 安全原则与陷阱

| 概念 | 核心要点 | 章节 |
| :--- | :--- | :--- |
| **最小权限** | 只给必要的权限，不多给 | 七 |
| **默认拒绝** | 未明确允许的一律拒绝（白名单模式） | 七 |
| **职责分离** | 关键操作需多人参与，不能自己审批自己 | 七 |
| **前端校验 ≠ 安全** | 前端只管 UI，安全靠后端 | 七 |
| **垂直越权** | 低权限用户执行高权限操作，靠角色校验防 | 七 |
| **水平越权** | 同级用户访问他人数据，靠数据归属校验防 | 七 |
| **IDOR** | 暴露可预测 ID 导致数据泄露，用 UUID + 归属校验防 | 七 |
### 2. 框架选型决策树

```
 START: 你用什么框架？
 ═══════════════════════════════════════════════════════════════

 Q1: 你用什么 Web 框架？
 │
 ├─ Django
 │   │
 │   ├─ 内置的 Group + Permission 够用？
 │   │   ├─ Yes → ✅ Django 内置权限系统（零配置）
 │   │   └─ No  → 需要什么？
 │   │           ├─ 动态策略 → ✅ Django + Casbin
 │   │           └─ 对象级权限 → ✅ Django + django-guardian
 │   │
 │   └─ 需要 REST API 权限？
 │       → ✅ DRF（Django REST Framework）内置 Permission 类
 │
 ├─ FastAPI
 │   │
 │   ├─ 只需要认证 + 简单角色？
 │   │   → ✅ 手写 Depends + JWT（参考第三章）
 │   │
 │   ├─ 需要完整用户管理（注册/登录/OAuth）？
 │   │   → ✅ fastapi-users
 │   │
 │   ├─ 需要灵活的策略引擎？
 │   │   → ✅ FastAPI + Casbin
 │   │
 │   └─ 微服务 / 需要跨服务统一鉴权？
 │       → ✅ FastAPI + OPA
 │
 ├─ Flask
 │   │
 │   ├─ 简单角色控制？
 │   │   → ✅ 手写装饰器（参考第二章）
 │   │
 │   └─ 需要完整用户系统？
 │       → ✅ Flask-Login + Flask-Principal
 │
 └─ 微服务 / 多语言架构
     │
     ├─ 服务数量 < 10？
     │   → ✅ Casbin（每个服务嵌入）
     │
     └─ 服务数量 10+，需要集中管控？
         → ✅ OPA（独立部署）+ API 网关鉴权
```

#### 典型技术栈组合

| 项目类型 | 认证方案 | 权限方案 | 数据归属 |
| :--- | :--- | :--- | :--- |
| **个人博客 / 内部工具** | Session 或 JWT | `@role_required` 装饰器 | 单用户，无需 |
| **SaaS 产品（单体）** | JWT + Refresh Token | FastAPI Depends + Casbin | `WHERE user_id = ?` |
| **多租户 SaaS** | JWT + 租户隔离 | Casbin（RBAC with domains） | `WHERE tenant_id = ?` |
| **开放平台（第三方接入）** | OAuth2 + API Key | OAuth2 Scope + 限流 | Scope 限定范围 |
| **微服务集群** | JWT（网关验签） | OPA + 权限网关 | 各服务自行校验 |
| **Django 全栈** | Session（内置） | Group + Permission（内置） | `get_object_or_404` |

#### 速记建议

```
 一图记住选型
 ═══════════════════════════════════════

 简单 ──────────────────────────▶ 复杂

 装饰器        Depends       Casbin        OPA
 (Flask)      (FastAPI)     (策略引擎)    (微服务)

 │← 小项目 →│← 中型项目 →│← 大型项目 ──────→│

 关键判断点：
 · 角色写死在代码里能接受吗？  → Yes = 装饰器
 · 需要运行时改策略吗？       → Yes = Casbin
 · 有多个服务需要统一鉴权吗？  → Yes = OPA
```

> 💡 **记住**：决策树只是起点。实际项目中，最好的方案往往是**从简单开始，按需演进**——先用装饰器跑起来，业务复杂了再引入 Casbin，微服务化了再上 OPA。
### 3. 推荐学习资源

#### 官方文档（必读）

| 资源 | 说明 |
| :--- | :--- |
| [FastAPI Security 文档](https://fastapi.tiangolo.com/tutorial/security/) | OAuth2、JWT、Scope 的官方教程，示例清晰 |
| [Django 权限系统文档](https://docs.djangoproject.com/en/5.0/topics/auth/) | 内置 Group + Permission 的完整说明 |
| [Casbin 官方文档](https://casbin.org/docs/overview) | 模型语法、策略格式、多语言适配器 |
| [OPA 官方文档](https://www.openpolicyagent.org/docs/latest/) | Rego 语言教程、部署方案、与 K8s 集成 |
| [python-jose 文档](https://python-jose.readthedocs.io/) | JWT 编解码的 Python 实现 |
| [Authlib 文档](https://docs.authlib.org/) | OAuth 1.0/2.0、OpenID Connect 完整实现 |

#### 开源项目（实战参考）

| 项目 | 说明 |
| :--- | :--- |
| [fastapi-users](https://github.com/fastapi-users/fastapi-users) | FastAPI 用户管理最佳实践，含认证 + OAuth |
| [casbin/pycasbin](https://github.com/casbin/pycasbin) | Casbin 的 Python SDK，附大量示例 |
| [django-guardian](https://github.com/django-guardian/django-guardian) | Django 对象级权限扩展 |
| [Permit.io](https://github.com/permitio) | 云端权限即服务，SDK 开源 |
| [OWASP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) | OWASP 授权安全速查表 |

#### 安全知识（进阶）

| 资源 | 说明 |
| :--- | :--- |
| [OWASP Top 10](https://owasp.org/www-project-top-ten/) | Web 安全十大风险，Broken Access Control 排名第一 |
| [JWT.io](https://jwt.io/) | JWT 在线调试工具 + 各语言库索引 |
| [OAuth 2.0 Simplified](https://aaronparecki.com/oauth-2-simplified/) | 最通俗的 OAuth2 教程 |
| [The Copenhagen Book](https://thecopenhagenbook.com/) | 现代 Web 认证与安全最佳实践指南 |

#### 学习路径建议

```
 从零到精通的学习路线
 ═══════════════════════════════════════

 第 1 步：理解基础（1~2 天）
 ─────────────────────────
 · 认证 vs 授权的区别
 · RBAC 模型的核心概念
 · 本指南第一、二章

 第 2 步：框架实战（3~5 天）
 ─────────────────────────
 · 选一个框架（推荐 FastAPI）
 · 实现 JWT 登录 + 角色校验
 · 本指南第三章 + FastAPI 官方文档

 第 3 步：引入策略引擎（2~3 天）
 ─────────────────────────
 · 学习 Casbin 的 Model + Policy
 · 集成到现有项目中
 · 本指南第四章 + Casbin 官方文档

 第 4 步：安全加固（持续）
 ─────────────────────────
 · 学习 OWASP Top 10
 · 做一次自己项目的安全审计
 · 本指南第七章 + OWASP Cheat Sheet
```

> 💡 **最后一条建议**：权限管理不是"学完就结束"的知识，而是**需要在每个项目中反复实践**的能力。每次开发新接口时问自己三个问题：谁能访问？能做什么？数据是谁的？——长此以往，安全意识就会成为你的肌肉记忆。
