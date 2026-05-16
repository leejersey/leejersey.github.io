# SQLAlchemy 2.0 完全指南：从 ORM 到异步实战

> SQLAlchemy 2.0 是 Python 生态中最成熟的 ORM 框架——全新的类型注解模型定义、原生异步支持、2.0 风格查询 API。这篇指南带你从零掌握它的每一个核心能力。

---

## 1. 从 1.x 到 2.0：为什么要升级

SQLAlchemy 2.0 不是小版本更新——它是一次**范式级重构**，改变了你定义模型、编写查询、管理会话的方式。

### 1.1 SQLAlchemy 2.0 的三大变革

```
变革一：类型安全的模型定义
  旧: Column(String)         → 运行时才知道类型
  新: name: Mapped[str]      → IDE 实时补全 + mypy 检查

变革二：2.0 风格查询 API
  旧: session.query(User).filter(User.name == "Alice")
  新: session.execute(select(User).where(User.name == "Alice"))
  → 统一了 ORM 和 Core 的查询接口

变革三：原生异步支持
  旧: 需要第三方库 databases/encode
  新: AsyncEngine + AsyncSession，官方原生支持
```

### 1.2 新旧 API 对比速查

| 操作 | 1.x 旧写法 | 2.0 新写法 |
|------|-----------|-----------|
| **基类** | `declarative_base()` | `class Base(DeclarativeBase)` |
| **列定义** | `name = Column(String)` | `name: Mapped[str]` |
| **主键** | `id = Column(Integer, primary_key=True)` | `id: Mapped[int] = mapped_column(primary_key=True)` |
| **可空** | `Column(String, nullable=True)` | `name: Mapped[str \| None]` |
| **查询** | `session.query(User).all()` | `session.scalars(select(User)).all()` |
| **过滤** | `.filter(User.name == "x")` | `.where(User.name == "x")` |
| **获取一个** | `.query(User).get(1)` | `session.get(User, 1)` |
| **异步** | ❌ 需第三方库 | ✅ `AsyncSession` 原生 |

### 1.3 迁移策略：渐进式升级

```bash
# 安装
pip install "sqlalchemy>=2.0" alembic

# 如果需要异步
pip install "sqlalchemy[asyncio]" aiosqlite  # SQLite 异步
# 或
pip install "sqlalchemy[asyncio]" asyncpg    # PostgreSQL 异步
```

```
迁移路线（不需要一步到位）：

  阶段 1：启用 2.0 兼容模式（在 1.4 中）
  → from sqlalchemy import create_engine
  → engine = create_engine(..., future=True)

  阶段 2：新代码用 2.0 API
  → 新模型用 Mapped + mapped_column
  → 新查询用 select() 替代 query()

  阶段 3：逐步迁移旧代码
  → 旧模型不急着改（1.x 语法在 2.0 中仍可用）
  → 旧查询按模块迁移
```

> 💡 **好消息：** SQLAlchemy 2.0 对 1.x API 做了**向后兼容**——旧代码不会立即报错。你可以按自己的节奏渐进迁移。

---

## 2. 模型定义：Mapped 与 mapped_column

这是 2.0 最直观的变化——模型定义终于有了**类型安全**。

### 2.1 DeclarativeBase：新的基类

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, create_engine

# 2.0 新写法：继承 DeclarativeBase
class Base(DeclarativeBase):
    pass

# 1.x 旧写法（仍可用，但不推荐）
# Base = declarative_base()

# 创建引擎
engine = create_engine("sqlite:///app.db", echo=True)

# 创建所有表
Base.metadata.create_all(engine)
```

### 2.2 Mapped 与 mapped_column：类型安全的列定义

```python
from datetime import datetime
from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    # 主键：必须用 mapped_column 指定 primary_key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 必填字段：Mapped[str] → NOT NULL
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    
    # 可空字段：Mapped[str | None] → NULLABLE
    bio: Mapped[str | None] = mapped_column(Text, default=None)
    
    # 带默认值
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # 服务端默认值（由数据库生成）
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )
    
    # repr 输出
    def __repr__(self) -> str:
        return f"User(id={self.id}, name={self.name!r})"
```

```
类型映射规则：

  Mapped[str]          → VARCHAR NOT NULL
  Mapped[str | None]   → VARCHAR NULL（可空）
  Mapped[int]          → INTEGER NOT NULL
  Mapped[float]        → FLOAT NOT NULL
  Mapped[bool]         → BOOLEAN NOT NULL
  Mapped[datetime]     → DATETIME NOT NULL
  
  关键理解：
  Mapped[str]       = 必填（NOT NULL）
  Mapped[str | None] = 可空（NULLABLE）
  → 可空性直接从类型注解推断！
```

### 2.3 type_annotation_map：自定义类型映射

```python
from typing import Annotated, Any
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import DeclarativeBase

# 在 Base 中定义全局类型映射
class Base(DeclarativeBase):
    type_annotation_map = {
        str: String(255),       # 所有 str 默认映射到 VARCHAR(255)
        dict[str, Any]: JSON,   # dict 映射到 JSON 列
    }

# 使用 Annotated 创建可复用的类型别名
str_50 = Annotated[str, mapped_column(String(50))]
str_pk = Annotated[str, mapped_column(String(36), primary_key=True)]
text_col = Annotated[str, mapped_column(Text)]

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str_pk]                    # VARCHAR(36) PK
    title: Mapped[str_50]                 # VARCHAR(50) NOT NULL
    content: Mapped[text_col]             # TEXT NOT NULL
    name: Mapped[str]                     # VARCHAR(255)（来自 type_annotation_map）
    metadata_: Mapped[dict[str, Any]]     # JSON（来自 type_annotation_map）
```

### 2.4 常用列类型速查

| Python 类型 | SQLAlchemy 类型 | SQL 类型 |
|------------|----------------|---------|
| `int` | `Integer` | INTEGER |
| `str` | `String(n)` | VARCHAR(n) |
| `str`（长文本） | `Text` | TEXT |
| `float` | `Float` | FLOAT |
| `bool` | `Boolean` | BOOLEAN |
| `datetime` | `DateTime` | DATETIME |
| `date` | `Date` | DATE |
| `Decimal` | `Numeric(10, 2)` | NUMERIC |
| `bytes` | `LargeBinary` | BLOB |
| `dict` | `JSON` | JSON |
| `uuid.UUID` | `Uuid` | UUID（PG）|

> 💡 **模型定义口诀：** 用 `Mapped[类型]` 声明字段，用 `mapped_column()` 添加约束（primary_key、unique、index）。可空性从 `Mapped[str | None]` 自动推断。

---

## 3. 关联关系：relationship 完全指南

ORM 的灵魂是关联——掌握 `relationship` + `ForeignKey` 的四种模式，你就能建模任何业务。

### 3.1 一对多关系

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# 一个用户有多篇文章
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    
    # "一"的一侧：反向引用文章列表
    articles: Mapped[list["Article"]] = relationship(
        back_populates="author"
    )

class Article(Base):
    __tablename__ = "articles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    
    # 外键：指向 users.id
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # "多"的一侧：反向引用作者
    author: Mapped["User"] = relationship(back_populates="articles")

# 使用
user = User(name="Alice")
user.articles.append(Article(title="Hello World"))
# 或
article = Article(title="Hello", author=user)
```

```
一对多关联结构：

  User (一)          Article (多)
  ┌────────┐        ┌────────────────┐
  │ id     │←───────│ author_id (FK) │
  │ name   │        │ title          │
  │ articles│───────→│ author         │
  └────────┘        └────────────────┘
  
  back_populates 确保双向同步：
  user.articles ↔ article.author
```

### 3.2 多对多关系与 Association Table

```python
from sqlalchemy import Table, Column, ForeignKey

# 关联表（不是模型类，是 Table 对象）
article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", ForeignKey("articles.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

class Article(Base):
    __tablename__ = "articles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    
    tags: Mapped[list["Tag"]] = relationship(
        secondary=article_tags,  # 指定关联表
        back_populates="articles"
    )

class Tag(Base):
    __tablename__ = "tags"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    
    articles: Mapped[list["Article"]] = relationship(
        secondary=article_tags,
        back_populates="tags"
    )

# 使用
python_tag = Tag(name="Python")
article = Article(title="Type Hints Guide")
article.tags.append(python_tag)
```

### 3.3 一对一关系

```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    
    # uselist=False → 返回单个对象而非列表
    profile: Mapped["Profile | None"] = relationship(
        back_populates="user", uselist=False
    )

class Profile(Base):
    __tablename__ = "profiles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    bio: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True  # unique 确保一对一
    )
    user: Mapped["User"] = relationship(back_populates="profile")

# user.profile → Profile 对象（不是列表）
```

### 3.4 自引用关联（树形结构）

```python
# 评论的回复（树状结构）
class Comment(Base):
    __tablename__ = "comments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    
    # 自引用外键
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id")
    )
    
    # 子评论列表
    replies: Mapped[list["Comment"]] = relationship(
        back_populates="parent"
    )
    # 父评论
    parent: Mapped["Comment | None"] = relationship(
        back_populates="replies", remote_side=[id]
    )

# 使用
root = Comment(content="Great article!")
reply = Comment(content="Thanks!", parent=root)
root.replies  # [reply]
```

> 💡 **关联关系速记：** 一对多 → `list["X"]` + `ForeignKey`，多对多 → `secondary=关联表`，一对一 → `uselist=False` + `unique=True`，自引用 → `remote_side=[id]`。

---

## 4. 查询 API：select 语句详解

2.0 最大的 API 变化：**统一用 `select()` 替代 `session.query()`**。

### 4.1 基础查询：select、where、order_by

```python
from sqlalchemy import select

# 查询所有用户
stmt = select(User)
users = session.scalars(stmt).all()

# 条件过滤
stmt = select(User).where(User.name == "Alice")
user = session.scalars(stmt).first()  # 返回第一个或 None

# 多条件（AND）
stmt = select(User).where(
    User.is_active == True,
    User.age >= 18
)

# OR 条件
from sqlalchemy import or_
stmt = select(User).where(
    or_(User.name == "Alice", User.name == "Bob")
)

# 排序
stmt = select(User).order_by(User.created_at.desc())

# LIKE / IN
stmt = select(User).where(User.name.like("%ali%"))
stmt = select(User).where(User.id.in_([1, 2, 3]))

# 唯一结果（确保只有一个）
user = session.scalars(stmt).one()        # 没有或多个都报错
user = session.scalars(stmt).one_or_none() # 没有返回 None
```

### 4.2 关联查询：join 与 subquery

```python
# 隐式 join（通过 relationship）
stmt = (
    select(Article)
    .join(Article.author)
    .where(User.name == "Alice")
)

# 显式 join
stmt = (
    select(User.name, Article.title)
    .join(Article, User.id == Article.author_id)
)

# 左外连接
stmt = (
    select(User, Article)
    .outerjoin(Article, User.id == Article.author_id)
)

# 子查询
subq = (
    select(func.count(Article.id).label("article_count"), Article.author_id)
    .group_by(Article.author_id)
    .subquery()
)
stmt = (
    select(User.name, subq.c.article_count)
    .join(subq, User.id == subq.c.author_id)
)
```

### 4.3 聚合与分组：func、group_by、having

```python
from sqlalchemy import func

# COUNT
stmt = select(func.count()).select_from(User)
total = session.scalar(stmt)  # 单个值用 scalar()

# GROUP BY + HAVING
stmt = (
    select(User.is_active, func.count(User.id).label("cnt"))
    .group_by(User.is_active)
    .having(func.count(User.id) > 5)
)

# 多个聚合
stmt = (
    select(
        Article.author_id,
        func.count(Article.id).label("total"),
        func.max(Article.created_at).label("latest"),
    )
    .group_by(Article.author_id)
)
```

### 4.4 分页与游标分页

```python
# 传统分页（OFFSET + LIMIT）
def get_users_page(session, page: int = 1, size: int = 20):
    stmt = (
        select(User)
        .order_by(User.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    return session.scalars(stmt).all()

# 游标分页（大数据集推荐，避免 OFFSET 性能问题）
def get_users_cursor(session, cursor_id: int = 0, size: int = 20):
    stmt = (
        select(User)
        .where(User.id > cursor_id)
        .order_by(User.id)
        .limit(size)
    )
    users = session.scalars(stmt).all()
    next_cursor = users[-1].id if users else None
    return users, next_cursor
```

> 💡 **查询口诀：** 构建用 `select()`，执行用 `session.scalars()`，单值用 `session.scalar()`。永远不要再写 `session.query()`。

---

## 5. Session 与事务管理

Session 是你和数据库之间的**对话窗口**——所有 CRUD 都通过它完成。

### 5.1 Session 生命周期与最佳实践

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

engine = create_engine("sqlite:///app.db")
SessionLocal = sessionmaker(bind=engine)

# 方式 1：上下文管理器（推荐）
with SessionLocal() as session:
    user = session.get(User, 1)
    # session 退出时自动 close

# 方式 2：try-finally
session = SessionLocal()
try:
    user = session.get(User, 1)
    session.commit()
except Exception:
    session.rollback()
    raise
finally:
    session.close()
```

### 5.2 CRUD 操作模式

```python
with SessionLocal() as session:
    # CREATE
    user = User(name="Alice", email="alice@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)  # 刷新以获取自增 ID
    print(user.id)  # 1
    
    # READ
    user = session.get(User, 1)  # 按主键查
    users = session.scalars(select(User)).all()  # 查所有
    
    # UPDATE
    user.name = "Alice Updated"
    session.commit()  # 脏检查自动生成 UPDATE
    
    # DELETE
    session.delete(user)
    session.commit()
```

### 5.3 事务控制：begin、commit、rollback

```python
# 嵌套事务（savepoint）
with SessionLocal() as session:
    session.add(User(name="Alice"))
    
    try:
        with session.begin_nested():  # SAVEPOINT
            session.add(User(name="Bob"))
            raise ValueError("模拟错误")
    except ValueError:
        pass  # Bob 被回滚，Alice 不受影响
    
    session.commit()  # 只有 Alice 入库
```

```
flush vs commit：

  session.flush()   → 将变更发送到数据库（生成 SQL）
                      但事务未提交，可以回滚
  session.commit()  → flush + 提交事务
                      变更永久生效
  
  什么时候用 flush？
  → 需要在 commit 前获取自增 ID
  → 需要触发数据库约束检查
```

### 5.4 批量操作：bulk_save 与 insert 优化

```python
from sqlalchemy import insert

# ❌ 慢：逐个 add（N 次 INSERT）
for i in range(10000):
    session.add(User(name=f"user_{i}"))
session.commit()

# ✅ 快：批量 insert（1 次 INSERT + VALUES）
session.execute(
    insert(User),
    [{"name": f"user_{i}", "email": f"u{i}@test.com"} for i in range(10000)]
)
session.commit()

# ✅ 也可以用 add_all
users = [User(name=f"user_{i}") for i in range(10000)]
session.add_all(users)
session.commit()
```

> 💡 **Session 铁律：** 一个请求一个 Session，用完就关。不要跨请求复用 Session——这是连接泄漏的头号杀手。

---

## 6. 异步 SQLAlchemy：AsyncSession 实战

FastAPI 是异步的，SQLAlchemy 2.0 终于原生支持了——但有几个**必须知道的坑**。

### 6.1 异步引擎与 Session 配置

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

# 异步引擎（注意：连接字符串要用异步驱动）
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/mydb",
    # "sqlite+aiosqlite:///app.db",  # SQLite 异步
    echo=True,
    pool_size=20,
    max_overflow=10,
)

# 异步 Session 工厂
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # ⚠️ 异步模式必须设为 False
)
```

### 6.2 异步 CRUD 完整示例

```python
async def create_user(name: str, email: str) -> User:
    async with async_session() as session:
        user = User(name=name, email=email)
        session.add(user)
        await session.commit()
        return user

async def get_user(user_id: int) -> User | None:
    async with async_session() as session:
        return await session.get(User, user_id)

async def list_users() -> list[User]:
    async with async_session() as session:
        result = await session.scalars(select(User))
        return result.all()

async def update_user(user_id: int, name: str) -> User:
    async with async_session() as session:
        user = await session.get(User, user_id)
        user.name = name
        await session.commit()
        return user
```

### 6.3 异步的坑：expire_on_commit 与 lazy loading

```python
# 坑 1：expire_on_commit 导致属性失效
# 默认 expire_on_commit=True 时：
async with async_session() as session:
    user = User(name="Alice")
    session.add(user)
    await session.commit()
    print(user.name)  # ❌ MissingGreenlet 错误！
    # commit 后属性过期，访问时触发同步 lazy load → 异步下报错

# 解决：设置 expire_on_commit=False（已在 6.1 中配置）

# 坑 2：lazy loading 关联对象
async with async_session() as session:
    user = await session.get(User, 1)
    print(user.articles)  # ❌ 报错！lazy load 不支持异步
    
# 解决：显式 eager loading
from sqlalchemy.orm import selectinload

async with async_session() as session:
    stmt = select(User).options(selectinload(User.articles))
    user = (await session.scalars(stmt)).first()
    print(user.articles)  # ✅ 已预加载
```

### 6.4 与 FastAPI 的深度集成

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# 依赖注入：每个请求一个 Session
async def get_db():
    async with async_session() as session:
        yield session

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return {"id": user.id, "name": user.name}

@app.post("/users")
async def create_user(
    name: str,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    user = User(name=name, email=email)
    db.add(user)
    await db.commit()
    return {"id": user.id, "name": user.name}
```

> 💡 **异步三铁律：** ① `expire_on_commit=False` ② 关联对象必须 eager load ③ 连接字符串用异步驱动（asyncpg/aiosqlite）。

---

## 7. 关联加载策略与性能优化

ORM 最常见的性能问题不是 ORM 慢——是你**不知道它生成了多少 SQL**。

### 7.1 N+1 问题：ORM 最常见的性能杀手

```python
# ❌ N+1 问题示例
users = session.scalars(select(User)).all()
for user in users:
    print(user.articles)  # 每个 user 触发一次 SELECT！
    # 如果有 100 个用户 → 1 + 100 = 101 次查询

# SQL 日志：
# SELECT * FROM users                    ← 1 次
# SELECT * FROM articles WHERE user_id=1 ← +1
# SELECT * FROM articles WHERE user_id=2 ← +1
# ...                                    ← +98
# 共 101 次查询！
```

### 7.2 四种加载策略对比

```python
from sqlalchemy.orm import (
    selectinload,   # 推荐：集合（一对多）
    joinedload,     # 推荐：单对象（多对一）
    subqueryload,   # 子查询加载
    raiseload,      # 防御性：禁止 lazy load
)

# selectinload：用 IN 子句批量加载（推荐用于一对多）
stmt = select(User).options(selectinload(User.articles))
# SQL: SELECT * FROM users
# SQL: SELECT * FROM articles WHERE user_id IN (1,2,3,...) ← 只 2 次！

# joinedload：用 JOIN 一次性加载（推荐用于多对一）
stmt = select(Article).options(joinedload(Article.author))
# SQL: SELECT * FROM articles JOIN users ON ...  ← 只 1 次！

# raiseload：开发时禁止 lazy load，发现遗漏
stmt = select(User).options(raiseload(User.articles))
# user.articles → 立即报错，而不是悄悄发 N 条 SQL
```

| 策略 | SQL 次数 | 适用场景 | 注意事项 |
|------|---------|---------|---------|
| `selectinload` | 2 | 一对多集合 | ⭐ 最通用 |
| `joinedload` | 1 | 多对一/一对一 | 集合用会产生笛卡尔积 |
| `subqueryload` | 2 | 嵌套集合 | 类似 selectinload |
| `raiseload` | 0 | 开发调试 | 忘记 eager load 时立即报错 |

### 7.3 load_only：只加载需要的列

```python
from sqlalchemy.orm import load_only

# 只查 id 和 name（不加载其他列）
stmt = select(User).options(load_only(User.id, User.name))

# 组合使用
stmt = (
    select(User)
    .options(
        load_only(User.id, User.name),
        selectinload(User.articles).load_only(Article.id, Article.title)
    )
)
# 只加载必要字段 → 减少数据传输量
```

### 7.4 性能诊断：echo=True 与查询日志

```python
# 开发时开启 SQL 日志
engine = create_engine("sqlite:///app.db", echo=True)
# 控制台输出所有 SQL 语句

# 生产环境：用 logging 模块
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# 统计查询次数（调试利器）
from sqlalchemy import event

query_count = 0

@event.listens_for(engine, "before_cursor_execute")
def count_queries(conn, cursor, statement, parameters, context, executemany):
    global query_count
    query_count += 1

# 请求结束后检查：query_count > 10 → 可能有 N+1
```

> 💡 **性能优化口诀：** 一对多用 `selectinload`，多对一用 `joinedload`，开发时用 `raiseload` 防漏，上线前用 `echo=True` 审计 SQL 数量。

---

## 8. Alembic 数据库迁移

模型改了字段，数据库怎么同步？**Alembic** 就是 SQLAlchemy 的数据库版本管理工具。

### 8.1 初始化与基础配置

```bash
# 安装
pip install alembic

# 初始化（同步项目）
alembic init migrations

# 初始化（异步项目）
alembic init -t async migrations
```

```python
# migrations/env.py 关键配置
from app.models import Base  # 导入你的 Base

target_metadata = Base.metadata  # 让 Alembic 知道你的模型

# alembic.ini 关键配置
# sqlalchemy.url = sqlite:///app.db
```

### 8.2 自动生成迁移脚本

```bash
# 自动检测模型变化并生成迁移
alembic revision --autogenerate -m "add users table"

# 执行迁移
alembic upgrade head

# 回滚最近一次迁移
alembic downgrade -1

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

### 8.3 手动编写迁移：常见场景

```python
# migrations/versions/xxxx_add_age_column.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 添加列
    op.add_column("users", sa.Column("age", sa.Integer, nullable=True))
    
    # 添加索引
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    
    # 重命名列
    op.alter_column("users", "name", new_column_name="full_name")

def downgrade():
    op.alter_column("users", "full_name", new_column_name="name")
    op.drop_index("ix_users_email", "users")
    op.drop_column("users", "age")
```

```
⚠️ autogenerate 不能自动检测的操作：

  - 列重命名（会被识别为 drop + add）
  - 表重命名
  - 约束名称变更
  - 数据迁移（backfill）
  
  这些需要手动编写！
```

### 8.4 异步环境的 Alembic 配置

```python
# migrations/env.py（异步版本关键改动）
from sqlalchemy.ext.asyncio import create_async_engine

async def run_migrations_online():
    engine = create_async_engine(
        "postgresql+asyncpg://user:pass@localhost/mydb"
    )
    
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    
    await engine.dispose()

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()

import asyncio
asyncio.run(run_migrations_online())
```

> 💡 **迁移铁律：** 永远不要手动改数据库 schema，永远通过 Alembic 迁移。`autogenerate` 是起点，不是终点——生成后必须人工审核。

---

## 9. 工程实践与最佳模式

模型、查询、迁移都会了——最后把它们组织成**可维护的项目结构**。

### 9.1 项目结构组织

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── database.py          # Engine + Session 配置
│   ├── models/
│   │   ├── __init__.py      # 导出所有模型
│   │   ├── base.py          # Base + Mixin
│   │   ├── user.py          # User 模型
│   │   └── article.py       # Article 模型
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py          # 通用 Repository
│   │   └── user_repo.py     # User Repository
│   └── api/
│       ├── __init__.py
│       └── users.py         # 路由
├── migrations/               # Alembic 迁移
│   ├── env.py
│   └── versions/
├── alembic.ini
└── pyproject.toml
```

### 9.2 Repository 模式：分离数据访问逻辑

```python
# repositories/base.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

class BaseRepository[T]:
    """通用 Repository 基类（Python 3.12+ 泛型语法）"""
    
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model
    
    async def get(self, id: int) -> T | None:
        return await self.session.get(self.model, id)
    
    async def list(self, offset: int = 0, limit: int = 20) -> list[T]:
        stmt = select(self.model).offset(offset).limit(limit)
        return (await self.session.scalars(stmt)).all()
    
    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        return instance
    
    async def delete(self, id: int) -> None:
        instance = await self.get(id)
        if instance:
            await self.session.delete(instance)
            await self.session.commit()
    
    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        return await self.session.scalar(stmt)
```

```python
# repositories/user_repo.py
class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return (await self.session.scalars(stmt)).first()
    
    async def get_active_users(self) -> list[User]:
        stmt = select(User).where(User.is_active == True)
        return (await self.session.scalars(stmt)).all()

# 使用
async def get_user_handler(db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    return await repo.get_by_email("alice@example.com")
```

### 9.3 常用 Mixin：时间戳、软删除、审计

```python
from datetime import datetime
from sqlalchemy import func, Boolean
from sqlalchemy.orm import Mapped, mapped_column

class TimestampMixin:
    """自动管理 created_at / updated_at"""
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now()
    )

class SoftDeleteMixin:
    """软删除：标记删除而非物理删除"""
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)

# 使用：多继承
class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    # 自动拥有 created_at, updated_at, is_deleted, deleted_at
```

### 9.4 延伸阅读与参考资料

**官方资源：**
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/)
- [Alembic 文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 迁移指南](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)

**推荐阅读：**
- [FastAPI 生产级实战](FastAPI 生产级实战) — FastAPI + AsyncSession 完整集成
- [API 设计最佳实践](API 设计最佳实践) — RESTful API 与 ORM 的配合
- [Python 类型系统实战](../python/Python 类型系统实战) — Mapped 类型注解的深入理解

---

> **全书完。**
>
> SQLAlchemy 2.0 的核心思路就三句话：
> **用 `Mapped` 定义模型，用 `select()` 构建查询，用 `AsyncSession` 驱动异步。**
>
> 配合 Alembic 管理迁移、Repository 分离逻辑、Mixin 复用字段——
> 这就是生产级 Python ORM 的完整工程体系。🐍
