# Pydantic V2 完全指南

> 一句话导读：从"为什么需要数据校验"到"手撕 Pydantic V2 高级用法"，用最实战的方式掌握 Python 生态中最重要的数据校验库，让你的 FastAPI / LangChain 代码永远不因数据格式出 Bug。

---

## 1. 为什么需要 Pydantic？— 从一个线上 Bug 说起

在写第一行 Pydantic 代码之前，我们先搞清楚一个根本问题：**没有数据校验的代码，到底会出什么事？**

### 1.1 没有校验的 API 有多危险

你刚上线了一个 FastAPI 接口，接收用户的注册信息：

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/register")
async def register(data: dict):
    """用户注册接口 — 没有任何校验"""
    username = data["username"]
    age = data["age"]
    email = data["email"]
    
    # 存入数据库...
    return {"message": f"欢迎 {username}，注册成功！"}
```

看起来没问题？但前端传来了这些数据：

```python
# 正常数据 ✅
{"username": "张三", "age": 25, "email": "zhangsan@example.com"}

# 异常数据 1 ❌ — age 是字符串
{"username": "李四", "age": "二十五", "email": "lisi@example.com"}

# 异常数据 2 ❌ — 缺少 email 字段
{"username": "王五", "age": 30}

# 异常数据 3 ❌ — 恶意数据
{"username": "", "age": -1, "email": "not-an-email"}

# 异常数据 4 ❌ — SQL 注入
{"username": "'; DROP TABLE users; --", "age": 1, "email": "hack@evil.com"}
```

**结果**：
- 异常 1 → 数据库报错：`age` 列期望 int，收到了字符串
- 异常 2 → `KeyError: 'email'`，接口直接 500
- 异常 3 → 空用户名和负数年龄写入数据库，数据脏了
- 异常 4 → 如果没有参数化查询，数据库可能被删

> 💡 **核心问题**：`dict` 类型接收请求体 = **零校验**。任何格式、任何类型、任何值都能通过，所有防线都依赖后续代码手动处理——而手动处理迟早会漏。

### 1.2 手动 if-else 校验 vs Pydantic 一行搞定

于是你开始加校验逻辑。手动版本长这样：

```python
@app.post("/register")
async def register(data: dict):
    """手动校验 — 又臭又长"""
    # 1. 检查必填字段
    if "username" not in data:
        return {"error": "缺少 username"}, 422
    if "age" not in data:
        return {"error": "缺少 age"}, 422
    if "email" not in data:
        return {"error": "缺少 email"}, 422
    
    # 2. 检查类型
    if not isinstance(data["username"], str):
        return {"error": "username 必须是字符串"}, 422
    if not isinstance(data["age"], int):
        return {"error": "age 必须是整数"}, 422
    if not isinstance(data["email"], str):
        return {"error": "email 必须是字符串"}, 422
    
    # 3. 检查值的合法性
    if len(data["username"]) < 2 or len(data["username"]) > 20:
        return {"error": "username 长度必须在 2-20 之间"}, 422
    if data["age"] < 0 or data["age"] > 150:
        return {"error": "age 必须在 0-150 之间"}, 422
    if "@" not in data["email"]:
        return {"error": "email 格式不正确"}, 422
    
    # 终于可以处理业务了...
    return {"message": f"欢迎 {data['username']}"}
```

**30 行校验代码，3 行业务逻辑。** 而且这还只有 3 个字段——如果有 20 个字段呢？

现在看 Pydantic 版本：

```python
from pydantic import BaseModel, Field, EmailStr

class RegisterRequest(BaseModel):
    """用 Pydantic 定义数据模型 — 声明即校验"""
    username: str = Field(min_length=2, max_length=20)
    age: int = Field(ge=0, le=150)
    email: EmailStr

@app.post("/register")
async def register(data: RegisterRequest):
    # data 已经通过校验，类型安全，值合法
    return {"message": f"欢迎 {data.username}"}
```

**对比一下：**

| 维度 | 手动 if-else | Pydantic |
|:---|:---|:---|
| 代码量 | ~30 行校验 | 5 行模型定义 |
| 类型安全 | 手动检查 isinstance | 自动转换 + 校验 |
| 错误信息 | 自己拼字符串 | 自动生成结构化错误 |
| 新增字段 | 再加 10 行 if-else | 加一行类型声明 |
| 文档生成 | 没有 | FastAPI 自动生成 Swagger 文档 |
| 可维护性 | 散落在各处 | 集中在模型定义中 |

当你传入不合法的数据时，Pydantic 自动返回精确的错误信息：

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "username"],
      "msg": "String should have at least 2 characters",
      "input": "",
      "ctx": {"min_length": 2}
    },
    {
      "type": "less_than_equal",
      "loc": ["body", "age"],
      "msg": "Input should be less than or equal to 150",
      "input": 200
    }
  ]
}
```

> 💡 **Pydantic 的核心价值**：把"校验逻辑"从业务代码中剥离出来，变成**声明式的类型定义**。你只需要说"这个字段是什么类型、什么范围"，Pydantic 帮你处理所有校验、转换、错误信息。

### 1.3 Pydantic 在 Python 生态中的位置

Pydantic 不是一个小众库——它是 Python 生态中**下载量最高的数据校验库**，每月超过 3 亿次下载。几乎所有现代 Python 框架都在用它：

```
Pydantic 的生态位：

┌─────────────────────────────────────────────────┐
│                Python 应用                       │
│                                                 │
│  FastAPI ──── 请求/响应校验（内置 Pydantic）      │
│  LangChain ── Structured Output（用 Pydantic）   │
│  SQLModel ─── ORM 层（基于 Pydantic + SQLAlchemy）│
│  Prefect ──── 数据流编排（用 Pydantic）           │
│  dbt ──────── 数据建模（用 Pydantic）             │
│                                                 │
│  ┌──────────────────────────────────────────┐    │
│  │          Pydantic V2（核心层）             │    │
│  │  ✅ 数据校验     ✅ 类型转换               │    │
│  │  ✅ 序列化       ✅ JSON Schema 生成       │    │
│  │  ✅ 配置管理     ✅ 错误信息               │    │
│  │  ⚡ Rust 核心（pydantic-core）→ 极致性能   │    │
│  └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

**安装：**

```bash
# 基础安装
pip install pydantic

# 如果需要 EmailStr 等额外类型
pip install pydantic[email]

# 如果需要配置管理（BaseSettings）
pip install pydantic-settings
```

**版本说明**：本教程基于 **Pydantic V2**（2.x），它在 2023 年 6 月发布，核心用 Rust 重写，性能比 V1 快 5-50 倍。如果你还在用 V1，第 8 章有迁移指南。

**第 1 章核心认知：**

| 概念 | 说明 |
|:---|:---|
| **没有校验的 API** | 数据类型/格式/值全靠人肉检查，迟早出 Bug |
| **手动校验** | if-else 堆砌，代码量爆炸，维护噩梦 |
| **Pydantic** | 声明式校验——定义模型 = 定义校验规则，零额外代码 |
| **生态位** | FastAPI / LangChain / SQLModel 等主流框架的底层依赖 |

> 💡 **记住这个判断标准**：只要你的代码需要"接收外部数据"（API 请求、配置文件、LLM 输出、数据库结果），就应该用 Pydantic 做第一道防线。

---

## 2. 快速上手：BaseModel 与基础类型

上一章建立了直觉——**Pydantic = 声明式数据校验**。这一章我们来系统学习它的核心 API。

### 2.1 第一个 Pydantic 模型

Pydantic 的一切都围绕 `BaseModel` 展开。定义一个模型就像定义一个 dataclass，但自带校验超能力：

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    is_active: bool = True  # 默认值

# ✅ 正常创建
user = User(name="张三", age=25)
print(user)
# name='张三' age=25 is_active=True

# ✅ 自动类型转换（"25" → 25）
user2 = User(name="李四", age="25")
print(user2.age)       # 25（int，不是 str）
print(type(user2.age)) # <class 'int'>

# ❌ 无法转换的类型 → 报错
try:
    User(name="王五", age="不是数字")
except Exception as e:
    print(e)
    # 1 validation error for User
    # age
    #   Input should be a valid integer, unable to parse string as an integer
```

**关键行为**：Pydantic 会**尝试智能转换**类型。`"25"` 可以转成 `int`，所以通过；`"不是数字"` 转不了，所以报错。这叫做 **Lax Mode**（宽松模式）。

```python
# 模型实例的常用操作
user = User(name="张三", age=25)

# 1. 访问字段（像普通对象一样）
print(user.name)      # "张三"
print(user.age)       # 25

# 2. 转换为字典
print(user.model_dump())
# {'name': '张三', 'age': 25, 'is_active': True}

# 3. 转换为 JSON 字符串
print(user.model_dump_json())
# '{"name":"张三","age":25,"is_active":true}'

# 4. 从字典创建
user3 = User.model_validate({"name": "赵六", "age": 30})

# 5. 从 JSON 字符串创建
user4 = User.model_validate_json('{"name":"钱七","age":28}')

# 6. 查看 JSON Schema
print(User.model_json_schema())
# {'properties': {'name': {'title': 'Name', 'type': 'string'}, ...}, ...}
```

> 💡 **V2 重要变化**：V1 的 `.dict()` → V2 改成 `.model_dump()`，V1 的 `.json()` → V2 改成 `.model_dump_json()`。所有方法都加了 `model_` 前缀，旧方法已弃用。

### 2.2 常用字段类型速查

Pydantic 支持几乎所有 Python 内置类型和标准库类型。这里列出最常用的：

```python
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, HttpUrl
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Article(BaseModel):
    """一篇文章 — 展示各种字段类型"""
    
    # 基础类型
    title: str                          # 字符串
    word_count: int                     # 整数
    rating: float                       # 浮点数
    is_published: bool                  # 布尔值
    
    # 容器类型
    tags: list[str]                     # 字符串列表
    metadata: dict[str, str]            # 字典
    scores: set[int]                    # 集合（自动去重）
    coordinates: tuple[float, float]    # 固定长度元组
    
    # 日期时间
    created_at: datetime                # 日期时间
    publish_date: date                  # 日期
    
    # 枚举
    priority: Priority                  # 枚举值
    
    # 特殊类型（需要安装 pydantic[email]）
    author_email: EmailStr              # 邮箱校验
    source_url: HttpUrl                 # URL 校验

# 创建实例 — Pydantic 自动校验所有字段
article = Article(
    title="Pydantic V2 指南",
    word_count=5000,
    rating=4.8,
    is_published=True,
    tags=["python", "pydantic", "tutorial"],
    metadata={"category": "技术", "language": "zh"},
    scores={90, 85, 90},              # set 自动去重 → {85, 90}
    coordinates=(39.9, 116.4),
    created_at="2024-01-15T10:30:00",  # 字符串自动转 datetime ✨
    publish_date="2024-01-20",         # 字符串自动转 date ✨
    priority="high",                   # 字符串自动转枚举 ✨
    author_email="author@example.com",
    source_url="https://example.com/article",
)
```

**类型速查表：**

| Python 类型 | Pydantic 行为 | 自动转换示例 |
|:---|:---|:---|
| `str` | 接受任何字符串 | `123` → `"123"` |
| `int` | 接受整数或可转换的字符串 | `"42"` → `42` |
| `float` | 接受数值或字符串 | `"3.14"` → `3.14` |
| `bool` | 接受布尔值或可转换值 | `1` → `True`, `"false"` → `False` |
| `list[T]` | 列表，每个元素校验为 T | — |
| `dict[K, V]` | 字典，键值分别校验 | — |
| `datetime` | 日期时间 | `"2024-01-15T10:30:00"` → `datetime` |
| `Enum` | 枚举值 | `"high"` → `Priority.HIGH` |
| `EmailStr` | 邮箱格式校验 | 不合法直接报错 |
| `HttpUrl` | URL 格式校验 | 自动补全 scheme |

> 💡 **最实用的特性**：`datetime` 字段接受 ISO 格式字符串并自动转换。再也不用手动 `datetime.fromisoformat()` 了。

### 2.3 可选字段与默认值

在真实 API 中，很多字段不是必填的。Pydantic 提供了多种方式来处理"可能没有"的字段：

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CreatePostRequest(BaseModel):
    """创建文章的请求体 — 展示各种可选/默认写法"""
    
    # 必填字段（没有默认值 → 必须传）
    title: str
    content: str
    
    # 有默认值 → 可选，不传就用默认值
    is_draft: bool = True
    category: str = "未分类"
    
    # Optional[T] = T | None → 可以传 None
    cover_image: Optional[str] = None       # 可以不传（默认 None）
    subtitle: str | None = None             # Python 3.10+ 写法，效果一样
    
    # Field() 默认值 — 更多控制
    view_count: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)  # ⚠️ 可变类型用 default_factory
    
    # 动态默认值（每次创建时计算）
    created_at: datetime = Field(default_factory=datetime.now)

# 只传必填字段
post = CreatePostRequest(title="Hello", content="World")
print(post.model_dump())
# {
#   'title': 'Hello',
#   'content': 'World',
#   'is_draft': True,
#   'category': '未分类',
#   'cover_image': None,
#   'subtitle': None,
#   'view_count': 0,
#   'tags': [],
#   'created_at': datetime(2024, 1, 15, 10, 30, 0)  # 创建时的当前时间
# }
```

**关键区分：3 种"可选"的含义**

| 写法 | 含义 | 不传时的值 | 传 None |
|:---|:---|:---|:---|
| `name: str` | 必填 | ❌ 报错 | ❌ 报错 |
| `name: str = "默认"` | 可选，有默认值 | `"默认"` | ❌ 报错 |
| `name: Optional[str] = None` | 可选，可以为 None | `None` | ✅ 通过 |
| `name: str = Field(default=...)` | 可选，带约束的默认值 | 指定的默认值 | ❌ 报错 |

> 💡 **常见踩坑**：`tags: list[str] = []` 这样写有隐患——所有实例会共享同一个 list 对象。Pydantic V2 已经帮你处理了这个问题（每次创建新实例），但**推荐显式用 `Field(default_factory=list)`**，代码意图更清晰。

### 2.4 嵌套模型：模型套模型

真实项目中，数据结构往往是多层嵌套的。Pydantic 天然支持模型嵌套——外层模型会自动校验内层模型的所有字段。

```python
from pydantic import BaseModel, Field
from datetime import datetime

# ──────────────────────────────────────────
# 定义子模型
# ──────────────────────────────────────────
class Address(BaseModel):
    city: str
    district: str
    street: str
    zip_code: str | None = None

class Education(BaseModel):
    school: str
    degree: str  # "本科" / "硕士" / "博士"
    year: int = Field(ge=1950, le=2030)

# ──────────────────────────────────────────
# 父模型中引用子模型
# ──────────────────────────────────────────
class UserProfile(BaseModel):
    name: str
    age: int
    address: Address                    # 嵌套单个模型
    education: list[Education]          # 嵌套模型列表
    emergency_contact: Address | None = None  # 可选的嵌套模型

# 创建实例 — 可以传字典，Pydantic 自动转换为嵌套模型
profile = UserProfile(
    name="张三",
    age=28,
    address={                           # 字典自动转换为 Address 模型 ✨
        "city": "北京",
        "district": "海淀区",
        "street": "中关村大街1号",
    },
    education=[                         # 列表中的字典自动转换为 Education 模型 ✨
        {"school": "北京大学", "degree": "本科", "year": 2018},
        {"school": "清华大学", "degree": "硕士", "year": 2021},
    ],
)

# 访问嵌套字段
print(profile.address.city)           # "北京"
print(profile.education[0].school)    # "北京大学"
print(type(profile.address))          # <class 'Address'>

# 序列化 — 嵌套模型也会递归转换
print(profile.model_dump())
# {
#   'name': '张三',
#   'age': 28,
#   'address': {'city': '北京', 'district': '海淀区', 'street': '中关村大街1号', 'zip_code': None},
#   'education': [
#     {'school': '北京大学', 'degree': '本科', 'year': 2018},
#     {'school': '清华大学', 'degree': '硕士', 'year': 2021}
#   ],
#   'emergency_contact': None
# }
```

**嵌套校验的威力**：如果内层数据不合法，Pydantic 会精确定位到出错的字段路径：

```python
try:
    UserProfile(
        name="李四",
        age=25,
        address={"city": "上海", "district": "浦东"},  # ❌ 缺少 street
        education=[
            {"school": "复旦", "degree": "本科", "year": 1900},  # ❌ year < 1950
        ],
    )
except Exception as e:
    print(e)
    # 2 validation errors for UserProfile
    # address.street
    #   Field required
    # education.0.year
    #   Input should be greater than or equal to 1950
```

> 💡 **错误路径** `education.0.year` 精确指向了"education 列表的第 0 个元素的 year 字段"。这在调试嵌套 JSON 数据时极其有用。

**第 2 章核心回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **BaseModel** | Pydantic 的核心基类，定义模型 = 定义校验规则 |
| **自动类型转换** | `"25"` → `25`，`"2024-01-15"` → `date`，智能宽松 |
| **model_dump()** | 模型 → 字典，`model_dump_json()` → JSON 字符串 |
| **model_validate()** | 字典 → 模型，`model_validate_json()` → 从 JSON 创建 |
| **Optional[T]** | 字段可以是 T 或 None |
| **Field(default_factory=...)** | 可变类型的默认值工厂 |
| **嵌套模型** | 模型可以引用其他模型，字典自动递归转换 |

---

## 3. 数据校验：field_validator 与 model_validator

上一章学了 Pydantic 的自动类型校验——传错类型会报错、能转换的自动转。但实际业务中，**类型对了不代表值就合法**：

- 用户名是 `str` 类型没问题，但不能包含特殊字符
- 年龄是 `int` 没问题，但不能是负数
- 结束日期是 `date` 没问题，但必须晚于开始日期

这些**业务校验规则**，需要用 `field_validator` 和 `model_validator` 来实现。

### 3.1 field_validator：单字段校验

`field_validator` 用于校验**单个字段**的值。它在 Pydantic 完成类型转换之后执行（默认是 `after` 模式）。

```python
from pydantic import BaseModel, field_validator
import re

class CreateUserRequest(BaseModel):
    username: str
    age: int
    phone: str
    password: str

    @field_validator("username")
    @classmethod
    def username_must_be_valid(cls, v: str) -> str:
        """用户名校验：2-20位，只能包含字母数字下划线"""
        if len(v) < 2 or len(v) > 20:
            raise ValueError("用户名长度必须在 2-20 之间")
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', v):
            raise ValueError("用户名只能包含字母、数字、下划线、中文")
        return v  # ⚠️ 必须返回值！

    @field_validator("age")
    @classmethod
    def age_must_be_reasonable(cls, v: int) -> int:
        """年龄校验：0-150"""
        if v < 0 or v > 150:
            raise ValueError("年龄必须在 0-150 之间")
        return v

    @field_validator("phone")
    @classmethod
    def phone_must_be_valid(cls, v: str) -> str:
        """手机号校验：11 位数字"""
        v = v.replace("-", "").replace(" ", "")  # 清理格式
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError("手机号格式不正确")
        return v  # 返回清理后的值 ✨

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        """密码强度校验"""
        if len(v) < 8:
            raise ValueError("密码至少 8 位")
        if not re.search(r'[A-Z]', v):
            raise ValueError("密码必须包含大写字母")
        if not re.search(r'[0-9]', v):
            raise ValueError("密码必须包含数字")
        return v
```

**使用效果：**

```python
# ✅ 合法数据
user = CreateUserRequest(
    username="张三",
    age=25,
    phone="138-1234-5678",  # 自动清理格式 → "13812345678"
    password="MyPass123",
)
print(user.phone)  # "13812345678"（校验器返回了清理后的值）

# ❌ 不合法数据 — 一次返回所有错误
try:
    CreateUserRequest(
        username="a",           # 太短
        age=-1,                 # 负数
        phone="123",            # 格式错
        password="weak",        # 太弱
    )
except Exception as e:
    print(e)
    # 4 validation errors for CreateUserRequest
    # username: 用户名长度必须在 2-20 之间
    # age: 年龄必须在 0-150 之间
    # phone: 手机号格式不正确
    # password: 密码至少 8 位
```

**一个 validator 校验多个字段：**

```python
class Product(BaseModel):
    name: str
    description: str
    category: str

    @field_validator("name", "description", "category")  # 同时校验 3 个字段
    @classmethod
    def no_empty_strings(cls, v: str) -> str:
        """所有字符串字段不能为空白"""
        if not v.strip():
            raise ValueError("不能为空白字符串")
        return v.strip()  # 顺便去掉首尾空格
```

> 💡 **核心要点**：`field_validator` 的返回值会作为字段的最终值。所以你可以在校验器里做**数据清洗**（去空格、格式化手机号等），一举两得。

### 3.2 model_validator：跨字段联合校验

`field_validator` 只能看到自己负责的那个字段。如果校验逻辑需要**同时看多个字段**（比如"结束日期必须晚于开始日期"），就需要 `model_validator`。

```python
from pydantic import BaseModel, model_validator
from datetime import date

class EventRequest(BaseModel):
    """活动创建请求 — 需要跨字段校验"""
    name: str
    start_date: date
    end_date: date
    min_participants: int
    max_participants: int

    @model_validator(mode="after")
    def validate_dates_and_participants(self):
        """校验日期和人数的逻辑关系"""
        # 1. 结束日期必须晚于开始日期
        if self.end_date <= self.start_date:
            raise ValueError("结束日期必须晚于开始日期")
        
        # 2. 最大人数必须 >= 最小人数
        if self.max_participants < self.min_participants:
            raise ValueError(
                f"最大人数({self.max_participants})不能小于"
                f"最小人数({self.min_participants})"
            )
        
        return self  # ⚠️ after 模式必须返回 self
```

**使用效果：**

```python
# ❌ 日期不合逻辑
try:
    EventRequest(
        name="年会",
        start_date="2024-12-31",
        end_date="2024-12-01",     # 结束比开始早！
        min_participants=10,
        max_participants=5,         # 最大 < 最小！
    )
except Exception as e:
    print(e)
    # 1 validation error for EventRequest
    # 结束日期必须晚于开始日期
```

**另一个常见场景：密码确认**

```python
class RegisterForm(BaseModel):
    email: str
    password: str
    password_confirm: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("两次输入的密码不一致")
        return self
```

> 💡 **`field_validator` vs `model_validator` 选型**：校验只涉及一个字段 → `field_validator`；校验涉及多个字段的关系 → `model_validator`。

### 3.3 before vs after vs wrap 模式对比

前面的例子都用了默认的 `after` 模式。Pydantic V2 实际提供了 **3 种校验时机**：

```
数据传入 → [before 校验] → Pydantic 类型转换 → [after 校验] → 最终值
                                ↑
                          [wrap 校验] 包裹整个过程
```

**用同一个场景对比三种模式：**

```python
from pydantic import BaseModel, field_validator

# ──────────────────────────────────────────
# after 模式（默认）：类型转换之后执行
# ──────────────────────────────────────────
class UserAfter(BaseModel):
    age: int

    @field_validator("age", mode="after")  # 默认值，可以省略 mode
    @classmethod
    def check_age(cls, v: int) -> int:
        # v 已经是 int 了（Pydantic 自动转换 "25" → 25）
        if v < 0:
            raise ValueError("年龄不能为负数")
        return v

UserAfter(age="25")  # ✅ "25" → 25 → 校验通过

# ──────────────────────────────────────────
# before 模式：类型转换之前执行
# ──────────────────────────────────────────
class UserBefore(BaseModel):
    age: int

    @field_validator("age", mode="before")
    @classmethod
    def preprocess_age(cls, v):
        # v 还是原始输入，可能是任何类型！
        if isinstance(v, str) and v.endswith("岁"):
            v = v.replace("岁", "")  # "25岁" → "25"
        return v  # 返回后 Pydantic 再做类型转换

UserBefore(age="25岁")  # ✅ "25岁" → "25" → 25

# ──────────────────────────────────────────
# wrap 模式：包裹整个校验过程（最灵活）
# ──────────────────────────────────────────
from pydantic import field_validator
from pydantic.functional_validators import WrapValidator

class UserWrap(BaseModel):
    age: int

    @field_validator("age", mode="wrap")
    @classmethod
    def wrap_age(cls, v, handler):
        # handler = Pydantic 的默认校验逻辑
        # 你可以在调用 handler 前后做任何事
        print(f"原始值: {v}")
        result = handler(v)  # 调用默认校验（类型转换 + 约束检查）
        print(f"转换后: {result}")
        return result

UserWrap(age="25")
# 输出:
# 原始值: 25
# 转换后: 25
```

**三种模式速查表：**

| 模式 | 执行时机 | 参数类型 | 典型用途 |
|:---|:---|:---|:---|
| `after`（默认） | 类型转换**之后** | 已转换的目标类型 | 值范围校验、业务规则 |
| `before` | 类型转换**之前** | 原始输入（Any） | 数据预处理、格式清洗 |
| `wrap` | **包裹**整个过程 | 原始输入 + handler | 日志记录、条件性跳过校验 |

> 💡 **经验法则**：90% 的场景用 `after` 就够了。只有需要"在 Pydantic 转换之前先预处理数据"时才用 `before`（比如把 `"25岁"` 变成 `"25"`）。`wrap` 很少用，通常是框架级别的高级需求。

### 3.4 复用校验器：Annotated + AfterValidator

`field_validator` 的一个缺点是：**校验逻辑绑定在特定模型上，无法跨模型复用**。如果 10 个模型都有 `phone` 字段，你需要写 10 次一模一样的校验器。

Pydantic V2 引入了 `Annotated` + `AfterValidator` 来解决这个问题——把校验逻辑定义为**可复用的类型**：

```python
from typing import Annotated
from pydantic import AfterValidator, BaseModel
import re

# ──────────────────────────────────────────
# 定义可复用的校验函数
# ──────────────────────────────────────────
def validate_phone(v: str) -> str:
    """手机号校验 + 格式清理"""
    v = v.replace("-", "").replace(" ", "")
    if not re.match(r'^1[3-9]\d{9}$', v):
        raise ValueError("手机号格式不正确")
    return v

def validate_non_empty(v: str) -> str:
    """非空字符串校验"""
    if not v.strip():
        raise ValueError("不能为空白字符串")
    return v.strip()

def validate_positive(v: int) -> int:
    """正整数校验"""
    if v <= 0:
        raise ValueError("必须为正整数")
    return v

# ──────────────────────────────────────────
# 用 Annotated 创建可复用的类型别名
# ──────────────────────────────────────────
PhoneNumber = Annotated[str, AfterValidator(validate_phone)]
NonEmptyStr = Annotated[str, AfterValidator(validate_non_empty)]
PositiveInt = Annotated[int, AfterValidator(validate_positive)]

# ──────────────────────────────────────────
# 在任何模型中直接使用 — 零重复代码
# ──────────────────────────────────────────
class UserModel(BaseModel):
    name: NonEmptyStr
    phone: PhoneNumber
    age: PositiveInt

class OrderModel(BaseModel):
    customer_name: NonEmptyStr
    customer_phone: PhoneNumber    # 复用同一个校验逻辑 ✨
    quantity: PositiveInt

class EmployeeModel(BaseModel):
    full_name: NonEmptyStr
    mobile: PhoneNumber            # 又复用了 ✨
    department_id: PositiveInt
```

**对比一下两种方式：**

| 方式 | 校验逻辑位置 | 可复用性 | 推荐场景 |
|:---|:---|:---|:---|
| `@field_validator` | 绑定在模型内部 | ❌ 不可跨模型复用 | 模型特有的业务校验 |
| `Annotated[T, AfterValidator()]` | 独立的类型别名 | ✅ 任何模型都能用 | 通用的格式校验 |

> 💡 **最佳实践**：项目中建一个 `types.py` 文件，把 `PhoneNumber`、`NonEmptyStr`、`PositiveInt` 这些可复用类型集中定义，全项目 import 使用。

**第 3 章核心回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **field_validator** | 校验单个字段，返回值作为最终值（可做数据清洗） |
| **model_validator** | 校验多个字段之间的关系（如日期范围、密码确认） |
| **mode="after"** | 类型转换后执行（默认），拿到的是目标类型 |
| **mode="before"** | 类型转换前执行，拿到的是原始输入（适合预处理） |
| **Annotated + AfterValidator** | 把校验逻辑封装为可复用的类型别名 |

---

## 4. Field 配置与序列化控制

前面用 `Field()` 只设了 `min_length`、`ge` 这些简单约束。实际上 `Field()` 能做的事远不止这些——它是 Pydantic 中**控制字段行为最精细的工具**。

### 4.1 Field() 完整参数详解

```python
from pydantic import BaseModel, Field
from datetime import datetime

class Product(BaseModel):
    """商品模型 — 展示 Field() 的各种参数"""

    # ──── 约束类参数 ────
    name: str = Field(
        min_length=1,           # 最小长度
        max_length=100,         # 最大长度
    )
    price: float = Field(
        gt=0,                   # 大于 0（不包含 0）
        le=999999.99,           # 小于等于
        # ge=0  → 大于等于
        # lt=100 → 小于
    )
    stock: int = Field(
        ge=0,                   # 大于等于 0
        default=0,              # 默认值
    )
    tags: list[str] = Field(
        min_length=1,           # 列表至少 1 个元素
        max_length=10,          # 列表最多 10 个元素
        default_factory=list,
    )

    # ──── 文档类参数 ────
    description: str = Field(
        default="",
        title="商品描述",                  # Swagger UI 中显示的标题
        description="详细的商品描述信息",     # Swagger UI 中显示的描述
        examples=["iPhone 16 Pro Max"],    # 示例值（用于文档）
    )

    # ──── 特殊行为参数 ────
    sku: str = Field(
        pattern=r'^[A-Z]{2}-\d{6}$',       # 正则约束（如 "AB-123456"）
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        exclude=True,                       # 序列化时排除此字段
    )
    internal_code: str = Field(
        default="",
        repr=False,                         # print 时不显示此字段
    )

# 创建实例
product = Product(
    name="MacBook Pro",
    price=14999.00,
    sku="MB-000001",
    tags=["电脑", "苹果"],
)

print(product)
# name='MacBook Pro' price=14999.0 stock=0 tags=['电脑', '苹果'] ...
# 注意 internal_code 不会显示（repr=False）

print(product.model_dump())
# 注意 created_at 不会出现（exclude=True）
```

**Field() 参数速查表：**

| 参数 | 适用类型 | 作用 |
|:---|:---|:---|
| `default` / `default_factory` | 所有 | 默认值 / 可变类型默认值工厂 |
| `gt` / `ge` / `lt` / `le` | 数值 | 大于/大于等于/小于/小于等于 |
| `min_length` / `max_length` | str / list | 最小/最大长度 |
| `pattern` | str | 正则表达式约束 |
| `title` / `description` | 所有 | Swagger 文档标题/描述 |
| `examples` | 所有 | 文档示例值 |
| `exclude` | 所有 | `model_dump()` 时排除 |
| `repr` | 所有 | `print()` 时是否显示 |
| `alias` | 所有 | 字段别名（下节详讲） |
| `frozen` | 所有 | 字段不可修改 |

> 💡 **和 field_validator 的分工**：`Field()` 处理"声明式约束"（长度、范围、正则），`field_validator` 处理"逻辑性校验"（业务规则、跨字段关系）。能用 `Field()` 搞定的就不要写 validator。

### 4.2 别名系统（alias / validation_alias / serialization_alias）

别名系统解决的问题是：**外部数据的字段名和 Python 代码中的变量名不一致**。

最典型的场景：前端传 `camelCase`（`userName`），Python 用 `snake_case`（`user_name`）。

```python
from pydantic import BaseModel, Field, ConfigDict

# ──────────────────────────────────────────
# 方式 1：alias — 同时用于输入和输出
# ──────────────────────────────────────────
class UserV1(BaseModel):
    user_name: str = Field(alias="userName")
    email_address: str = Field(alias="emailAddress")

# 用别名创建（模拟前端传来的 JSON）
user = UserV1(userName="张三", emailAddress="zhang@example.com")
print(user.user_name)           # "张三"（用 Python 属性名访问）
print(user.model_dump())         # {'user_name': '张三', ...}（默认用 Python 名）
print(user.model_dump(by_alias=True))  # {'userName': '张三', ...}（用别名输出）

# ──────────────────────────────────────────
# 方式 2：分别控制输入别名和输出别名（V2 新特性）
# ──────────────────────────────────────────
class UserV2(BaseModel):
    user_name: str = Field(
        validation_alias="userName",       # 输入时用 camelCase
        serialization_alias="user_name",   # 输出时用 snake_case
    )

# 前端传 camelCase，后端存 snake_case
user = UserV2(userName="李四")
print(user.model_dump(by_alias=True))  # {'user_name': '李四'}

# ──────────────────────────────────────────
# 方式 3：全局自动转换（最推荐 ✨）
# ──────────────────────────────────────────
from pydantic import AliasGenerator
from pydantic.alias_generators import to_camel

class UserV3(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,       # 自动把 snake_case 转 camelCase
        populate_by_name=True,          # 允许同时用 Python 名和别名
    )
    
    user_name: str
    email_address: str
    phone_number: str | None = None

# 两种方式都能创建
user_a = UserV3(userName="张三", emailAddress="a@b.com")      # camelCase ✅
user_b = UserV3(user_name="张三", email_address="a@b.com")    # snake_case ✅

print(user_a.model_dump(by_alias=True))
# {'userName': '张三', 'emailAddress': 'a@b.com', 'phoneNumber': None}
```

**三种别名对比：**

| 别名类型 | 作用 | 典型场景 |
|:---|:---|:---|
| `alias` | 输入 + 输出统一使用 | 简单映射 |
| `validation_alias` | 仅影响输入（接收数据） | 前端 camelCase → 后端 snake_case |
| `serialization_alias` | 仅影响输出（序列化） | 后端 snake_case → 返回给前端 camelCase |
| `alias_generator` | 全局自动转换 | 整个模型统一转换命名风格 |

> 💡 **生产推荐**：用 `alias_generator=to_camel` + `populate_by_name=True`。一行配置搞定全部字段的命名风格转换，不用给每个字段手动写 alias。

### 4.3 序列化控制：model_dump() 与 model_dump_json()

`model_dump()` 远不止"转成字典"这么简单。它提供了丰富的参数来控制输出：

```python
from pydantic import BaseModel, Field
from datetime import datetime

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    password_hash: str
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    internal_note: str = ""

user = UserResponse(
    id=1, name="张三", email="zhang@example.com",
    password_hash="sha256:abc123", is_admin=True,
    internal_note="VIP 客户"
)

# ──── 基础序列化 ────
user.model_dump()
# 返回完整字典（包含所有字段）

# ──── 只包含指定字段 ────
user.model_dump(include={"id", "name", "email"})
# {'id': 1, 'name': '张三', 'email': 'zhang@example.com'}

# ──── 排除敏感字段 ────
user.model_dump(exclude={"password_hash", "internal_note"})
# {'id': 1, 'name': '张三', 'email': '...', 'is_admin': True, 'created_at': ...}

# ──── 排除值为 None 的字段 ────
user.model_dump(exclude_none=True)

# ──── 排除使用默认值的字段（只返回显式设置的） ────
user.model_dump(exclude_defaults=True)
# {'id': 1, 'name': '张三', 'email': '...', 'password_hash': '...', 'is_admin': True, 'internal_note': 'VIP 客户'}

# ──── 排除未显式传入的字段 ────
user.model_dump(exclude_unset=True)
# 只返回创建时明确传入的字段（不含靠默认值填充的）

# ──── mode="json" — 把不可 JSON 序列化的类型转成可序列化的 ────
user.model_dump(mode="json")
# datetime 自动变成 ISO 格式字符串，而不是 datetime 对象

# ──── 直接输出 JSON 字符串 ────
user.model_dump_json(indent=2)  # 带缩进的 JSON 字符串
```

**`model_dump()` 参数速查：**

| 参数 | 作用 | 示例 |
|:---|:---|:---|
| `include` | 只输出指定字段 | `include={"id", "name"}` |
| `exclude` | 排除指定字段 | `exclude={"password"}` |
| `exclude_none` | 排除值为 None 的字段 | PATCH 接口只传修改的字段 |
| `exclude_defaults` | 排除使用默认值的字段 | 减少冗余数据 |
| `exclude_unset` | 排除未显式传入的字段 | PATCH 更新时只更新传入的字段 |
| `by_alias` | 用别名作为 key | 返回给前端 camelCase |
| `mode="json"` | 把 datetime 等转成 JSON 兼容 | API 响应 |

> 💡 **最常用的组合**：API 响应用 `model_dump(exclude={"password_hash"}, by_alias=True, mode="json")`——排除敏感信息、用前端命名风格、确保可 JSON 序列化。

### 4.4 字段排除与动态序列化

在实际项目中，同一个实体往往需要多种"视图"：创建时需要密码、列表页不需要详情、管理员能看到更多字段。用**模型继承 + computed_field** 优雅解决：

```python
from pydantic import BaseModel, Field, computed_field
from datetime import datetime

# ──────────────────────────────────────────
# 基础模型：包含所有字段
# ──────────────────────────────────────────
class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    """创建用户 — 需要密码"""
    password: str = Field(min_length=8)

class UserResponse(UserBase):
    """API 响应 — 不暴露密码"""
    id: int
    is_active: bool = True
    created_at: datetime

    @computed_field                    # V2 新特性：计算字段 ✨
    @property
    def display_name(self) -> str:
        """自动计算的展示名（序列化时自动包含）"""
        return f"{self.name}（{self.email.split('@')[0]}）"

class UserAdmin(UserResponse):
    """管理员视图 — 额外信息"""
    last_login_ip: str | None = None
    internal_note: str = ""
```

**使用效果：**

```python
# FastAPI 中的典型用法
from fastapi import FastAPI

app = FastAPI()

@app.post("/users", response_model=UserResponse)
async def create_user(data: UserCreate):
    # data 包含 password（用于创建）
    # 但返回 UserResponse（不含 password）
    user = save_to_db(data)
    return UserResponse(
        id=user.id,
        name=data.name,
        email=data.email,
        created_at=datetime.now(),
    )

# UserResponse 序列化结果：
# {
#   "id": 1,
#   "name": "张三",
#   "email": "zhang@example.com",
#   "is_active": true,
#   "created_at": "2024-01-15T10:30:00",
#   "display_name": "张三（zhang）"     ← computed_field 自动计算
# }
# 注意：没有 password！
```

**`computed_field` 的价值**：
- 序列化时自动包含计算结果，不需要在数据库里存
- 类型安全——有 `-> str` 返回类型标注
- 自动出现在 JSON Schema / Swagger 文档中

> 💡 **设计模式**：`UserBase`（共享字段）→ `UserCreate`（输入模型，含密码）→ `UserResponse`（输出模型，不含密码）→ `UserAdmin`（管理员扩展）。这是 FastAPI 官方推荐的模型分层模式。

**第 4 章核心回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Field()** | 字段的精细控制：约束、文档、排除、正则等 |
| **alias / alias_generator** | 字段命名映射，解决 camelCase ↔ snake_case |
| **model_dump()** | 灵活的序列化控制：include/exclude/by_alias/mode |
| **exclude_unset** | PATCH 更新的利器——只更新用户传入的字段 |
| **computed_field** | 计算属性，序列化时自动包含 |
| **模型继承** | Base → Create → Response → Admin 分层模式 |

---

## 5. 高级类型：Literal / Discriminated Union / 自定义类型

前几章掌握了 Pydantic 的核心用法。这一章进入**进阶领域**——处理"多种可能的数据结构"。这在 AI 应用中特别常见：LLM 的 Function Calling 返回不同结构、Webhook 接收不同事件类型、消息系统处理不同消息格式。

### 5.1 Literal 与 Enum：限定取值范围

当一个字段只允许特定的几个值时，有两种方式：

```python
from pydantic import BaseModel
from typing import Literal
from enum import Enum

# ──────────────────────────────────────────
# 方式 1：Literal — 轻量级，适合简单场景
# ──────────────────────────────────────────
class LLMRequest(BaseModel):
    model: Literal["gpt-4o", "gpt-4o-mini", "deepseek-chat"]
    temperature: float = 0.7

LLMRequest(model="gpt-4o")          # ✅
LLMRequest(model="claude-3")        # ❌ 不在允许列表中

# ──────────────────────────────────────────
# 方式 2：Enum — 更正式，适合复杂场景
# ──────────────────────────────────────────
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(BaseModel):
    name: str
    status: TaskStatus = TaskStatus.PENDING

task = Task(name="数据清洗", status="running")  # 字符串自动转枚举 ✨
print(task.status)         # TaskStatus.RUNNING
print(task.status.value)   # "running"

# 序列化时自动转回字符串
print(task.model_dump())
# {'name': '数据清洗', 'status': 'running'}
```

**Literal vs Enum 选型：**

| 维度 | Literal | Enum |
|:---|:---|:---|
| 代码量 | 极少（一行） | 较多（定义类） |
| 可复用性 | ❌ 内联定义 | ✅ 独立类，多处引用 |
| IDE 支持 | 一般 | 好（自动补全） |
| 扩展能力 | 只有值 | 可以加方法/属性 |
| 推荐场景 | 2-5 个固定值 | 正式的状态/类型定义 |

> 💡 **经验法则**：随手写的限定用 `Literal`，作为项目核心概念的状态/类型用 `Enum`。

### 5.2 Discriminated Union：根据标签分发到不同模型

这是 Pydantic 最强大的高级特性之一。**场景**：一个接口可能接收不同结构的数据，靠某个"标签字段"来区分。

```python
from pydantic import BaseModel, Field
from typing import Literal, Union

# ──────────────────────────────────────────
# 定义不同类型的消息
# ──────────────────────────────────────────
class TextMessage(BaseModel):
    type: Literal["text"]              # 标签字段
    content: str
    
class ImageMessage(BaseModel):
    type: Literal["image"]             # 标签字段
    url: str
    width: int
    height: int

class AudioMessage(BaseModel):
    type: Literal["audio"]             # 标签字段
    url: str
    duration: float                    # 秒

# ──────────────────────────────────────────
# 用 Discriminated Union 自动路由
# ──────────────────────────────────────────
class ChatRequest(BaseModel):
    user_id: str
    message: Union[TextMessage, ImageMessage, AudioMessage] = Field(
        discriminator="type"           # 告诉 Pydantic 用 type 字段来判断
    )

# Pydantic 根据 type 字段自动选择正确的模型 ✨
req1 = ChatRequest(
    user_id="u001",
    message={"type": "text", "content": "你好"}
)
print(type(req1.message))  # <class 'TextMessage'>

req2 = ChatRequest(
    user_id="u001",
    message={"type": "image", "url": "https://...", "width": 800, "height": 600}
)
print(type(req2.message))  # <class 'ImageMessage'>

# 如果 type 不匹配任何模型 → 报错
try:
    ChatRequest(
        user_id="u001",
        message={"type": "video", "url": "https://..."}  # ❌ 没有 VideoMessage
    )
except Exception as e:
    print(e)
    # Input tag 'video' found using 'type' does not match any of the expected tags
```

**AI 场景的典型应用：Function Calling 结果分发**

```python
class SearchResult(BaseModel):
    tool: Literal["search"]
    query: str
    results: list[str]

class CalculateResult(BaseModel):
    tool: Literal["calculate"]
    expression: str
    answer: float

class WeatherResult(BaseModel):
    tool: Literal["weather"]
    city: str
    temperature: float

class ToolCallResponse(BaseModel):
    """LLM 工具调用的返回结果 — 根据 tool 字段自动分发"""
    result: Union[SearchResult, CalculateResult, WeatherResult] = Field(
        discriminator="tool"
    )
```

> 💡 **Discriminated Union 的性能优势**：普通 Union 会依次尝试每个类型直到匹配成功（O(n)）。Discriminated Union 直接根据标签字段定位到正确的类型（O(1)），在类型很多时差距明显。

### 5.3 自定义类型：用 Annotated 封装复杂校验

如果内置类型不够用，可以用 `Annotated` 组合多个校验器来创建**自定义类型**：

```python
from typing import Annotated
from pydantic import BaseModel, BeforeValidator, AfterValidator, Field
import re

# ──────────────────────────────────────────
# 自定义类型 1：中国身份证号
# ──────────────────────────────────────────
def validate_id_card(v: str) -> str:
    """校验 18 位身份证号"""
    v = v.strip().upper()  # X 转大写
    if not re.match(r'^\d{17}[\dX]$', v):
        raise ValueError("身份证号必须为 18 位")
    return v

IDCard = Annotated[str, AfterValidator(validate_id_card)]

# ──────────────────────────────────────────
# 自定义类型 2：JSON 字符串 → 自动解析为 dict
# ──────────────────────────────────────────
import json

def parse_json_string(v):
    """如果传入 JSON 字符串，自动解析为 dict"""
    if isinstance(v, str):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            raise ValueError("无效的 JSON 字符串")
    return v

JsonDict = Annotated[dict, BeforeValidator(parse_json_string)]

# ──────────────────────────────────────────
# 自定义类型 3：非空去重列表
# ──────────────────────────────────────────
def deduplicate_and_clean(v: list[str]) -> list[str]:
    """去重 + 去空字符串 + 保持顺序"""
    seen = set()
    result = []
    for item in v:
        item = item.strip()
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result

UniqueStrList = Annotated[list[str], AfterValidator(deduplicate_and_clean)]

# ──────────────────────────────────────────
# 在模型中使用自定义类型
# ──────────────────────────────────────────
class UserProfile(BaseModel):
    name: str
    id_card: IDCard                     # 身份证号校验
    preferences: JsonDict               # JSON 字符串自动解析
    skills: UniqueStrList               # 自动去重

profile = UserProfile(
    name="张三",
    id_card="11010519900101001X",
    preferences='{"theme": "dark", "lang": "zh"}',  # 传 JSON 字符串 ✨
    skills=["Python", "Python", " ", "FastAPI", "Python"],  # 自动去重 ✨
)

print(profile.preferences)  # {'theme': 'dark', 'lang': 'zh'}（已解析为 dict）
print(profile.skills)        # ['Python', 'FastAPI']（已去重去空）
```

> 💡 **实用建议**：大多数场景用 `Annotated` + `BeforeValidator`/`AfterValidator` 组合就够了，不需要去实现底层的 `__get_pydantic_core_schema__`。后者是给框架作者/库作者用的。

### 5.4 泛型模型（Generic Model）

泛型模型解决的问题是：**多个模型结构相同，只是内部数据类型不同**。最经典的场景就是统一 API 响应格式。

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

# ──────────────────────────────────────────
# 定义泛型变量
# ──────────────────────────────────────────
T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应格式 — 泛型版"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None

# ──────────────────────────────────────────
# 定义具体的数据模型
# ──────────────────────────────────────────
class User(BaseModel):
    id: int
    name: str

class Article(BaseModel):
    id: int
    title: str
    content: str

# ──────────────────────────────────────────
# 使用泛型 — 不同接口返回不同的 data 类型
# ──────────────────────────────────────────

# 返回单个用户
response_user = ApiResponse[User](
    data=User(id=1, name="张三")
)
# {"code": 200, "message": "success", "data": {"id": 1, "name": "张三"}}

# 返回文章列表
response_articles = ApiResponse[list[Article]](
    data=[
        Article(id=1, title="Pydantic 教程", content="..."),
        Article(id=2, title="FastAPI 实战", content="..."),
    ]
)

# 返回错误（data 为 None）
response_error = ApiResponse[None](
    code=404,
    message="用户不存在",
)
```

**在 FastAPI 中使用泛型响应：**

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}", response_model=ApiResponse[User])
async def get_user(user_id: int):
    user = await find_user(user_id)
    if not user:
        return ApiResponse(code=404, message="用户不存在")
    return ApiResponse(data=user)

@app.get("/articles", response_model=ApiResponse[list[Article]])
async def list_articles():
    articles = await get_all_articles()
    return ApiResponse(data=articles)
```

> 💡 **泛型的价值**：一套 `ApiResponse` 模型，搭配不同的类型参数，就能适配所有接口的响应格式。Swagger 文档也会自动生成正确的 Schema。

**第 5 章核心回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Literal** | 限定字段只能是指定的几个值（轻量级枚举） |
| **Enum** | 正式的枚举类型，可复用，有 IDE 补全 |
| **Discriminated Union** | 根据标签字段自动分发到不同模型（O(1) 性能） |
| **自定义类型（Annotated）** | 用 BeforeValidator/AfterValidator 封装可复用的校验逻辑 |
| **Generic Model** | 泛型模型，一套结构适配多种数据类型 |

---

## 6. Pydantic Settings：配置管理最佳实践

每个项目都需要管理配置——数据库连接串、API Key、服务端口等。`pydantic-settings` 把配置管理变成了**类型安全、可校验、可文档化**的体验。

### 6.1 BaseSettings 基础用法

```bash
# 先安装
pip install pydantic-settings
```

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """应用配置 — 自动从环境变量读取"""
    
    # 数据库配置
    database_url: str = "sqlite:///./dev.db"
    db_pool_size: int = 5
    
    # API 配置
    api_key: str                       # 必填！没有默认值 → 必须设置环境变量
    api_base_url: str = "https://api.openai.com/v1"
    
    # 应用配置
    debug: bool = False
    port: int = 8000
    allowed_origins: list[str] = ["http://localhost:3000"]

# 方式 1：从环境变量读取
# 在终端中设置：export API_KEY=sk-xxx
settings = Settings()
print(settings.api_key)  # "sk-xxx"（从环境变量读取）

# 方式 2：直接传参（用于测试）
settings = Settings(api_key="sk-test-key", debug=True)
```

**关键行为**：
- `BaseSettings` 会**自动从环境变量读取**与字段同名的值（不区分大小写）
- 字段名 `database_url` → 环境变量 `DATABASE_URL`
- 有默认值的字段可以不设环境变量；没有默认值的**必须设置**，否则启动报错

> 💡 **和 `os.getenv()` 的区别**：`os.getenv("PORT")` 返回字符串，你需要手动 `int()` 转换。BaseSettings 自动做类型转换 + 校验——`PORT=abc` 会直接报错，而不是到运行时才崩。

### 6.2 .env 文件与环境变量优先级

实际项目不会把配置写在环境变量里，而是放在 `.env` 文件中：

```bash
# .env 文件
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
API_KEY=sk-proj-abc123
DEBUG=true
PORT=8080
ALLOWED_ORIGINS=["http://localhost:3000","https://myapp.com"]
```

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",           # 指定 .env 文件路径
        env_file_encoding="utf-8",
        case_sensitive=False,      # 环境变量不区分大小写
    )
    
    database_url: str = "sqlite:///./dev.db"
    api_key: str
    debug: bool = False
    port: int = 8000
    allowed_origins: list[str] = ["http://localhost:3000"]

settings = Settings()
# 自动从 .env 文件读取配置
```

**优先级（从高到低）：**

```
1. 构造函数直接传参     Settings(debug=True)         → 最高优先级
2. 系统环境变量         export DEBUG=true             → 覆盖 .env
3. .env 文件           DEBUG=true                    → 覆盖默认值
4. 字段默认值           debug: bool = False           → 最低优先级
```

> 💡 **最佳实践**：`.env` 文件加入 `.gitignore`（不提交到 Git），提供一个 `.env.example` 作为模板。CI/CD 环境用系统环境变量覆盖 `.env` 的值。

### 6.3 嵌套配置与分组

当配置项变多后，扁平的字段列表变得难以维护。用**嵌套模型 + env_prefix** 来分组：

```python
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# ──────────────────────────────────────────
# 子配置（普通 BaseModel，不是 BaseSettings）
# ──────────────────────────────────────────
class DatabaseConfig(BaseModel):
    url: str = "sqlite:///./dev.db"
    pool_size: int = 5
    echo: bool = False

class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0

class LLMConfig(BaseModel):
    api_key: str = ""
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 2000

# ──────────────────────────────────────────
# 主配置
# ──────────────────────────────────────────
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",     # 用双下划线分隔嵌套层级 ✨
    )
    
    app_name: str = "MyApp"
    debug: bool = False
    
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    llm: LLMConfig = LLMConfig()
```

**对应的 .env 文件：**

```bash
# .env — 用 __ 分隔嵌套层级
APP_NAME=AI-Assistant
DEBUG=true

# 数据库配置
DATABASE__URL=postgresql://user:pass@db:5432/mydb
DATABASE__POOL_SIZE=10
DATABASE__ECHO=false

# Redis 配置
REDIS__HOST=redis-server
REDIS__PORT=6380

# LLM 配置
LLM__API_KEY=sk-proj-abc123
LLM__MODEL=gpt-4o
LLM__TEMPERATURE=0.3
```

```python
settings = Settings()
print(settings.database.url)       # "postgresql://user:pass@db:5432/mydb"
print(settings.llm.api_key)        # "sk-proj-abc123"
print(settings.redis.host)         # "redis-server"
```

> 💡 **`env_nested_delimiter="__"`** 是关键配置——它告诉 Pydantic 用双下划线 `__` 来解析嵌套层级。`DATABASE__URL` → `settings.database.url`。

### 6.4 多环境配置方案（dev / staging / prod）

真实项目需要在不同环境加载不同配置。推荐方案：**一套代码 + 多个 .env 文件 + 环境变量切换**。

```
项目根目录/
├── .env                 # 默认配置（开发环境）
├── .env.staging         # 预发布环境
├── .env.production      # 生产环境
├── .env.example         # 模板（提交到 Git）
└── config.py            # 配置加载逻辑
```

```python
# config.py
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
    )
    
    # 环境标识
    environment: str = "development"   # development / staging / production
    debug: bool = False
    
    # ... 其他配置字段 ...
    database_url: str = "sqlite:///./dev.db"
    api_key: str = ""

@lru_cache()
def get_settings() -> Settings:
    """
    单例模式获取配置（全应用只加载一次）
    
    通过 APP_ENV 环境变量切换配置文件：
    - APP_ENV=staging  → 加载 .env.staging
    - APP_ENV=production → 加载 .env.production
    - 默认 → 加载 .env
    """
    env = os.getenv("APP_ENV", "development")
    env_file = f".env.{env}" if env != "development" else ".env"
    
    return Settings(_env_file=env_file)

# 使用方式
settings = get_settings()
```

**在 FastAPI 中用依赖注入获取配置：**

```python
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "ok",
        "environment": settings.environment,
        "debug": settings.debug,
    }
```

**部署命令示例：**

```bash
# 开发环境（默认）
uvicorn main:app --reload

# 预发布环境
APP_ENV=staging uvicorn main:app

# 生产环境
APP_ENV=production uvicorn main:app --workers 4
```

> 💡 **`@lru_cache` 的作用**：确保 `get_settings()` 只执行一次，后续调用直接返回缓存的实例。避免每次请求都重新读取 .env 文件。

**第 6 章核心回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **BaseSettings** | 自动从环境变量读取配置，带类型校验 |
| **.env 文件** | 配置文件，不提交 Git，用 .env.example 做模板 |
| **优先级** | 构造函数 > 环境变量 > .env > 默认值 |
| **env_nested_delimiter** | 用 `__` 分隔嵌套配置层级 |
| **@lru_cache 单例** | 全应用只加载一次配置 |
| **多环境切换** | `APP_ENV=production` + 对应 .env 文件 |

---

## 7. 实战整合：Pydantic × FastAPI × LangChain

前面 6 章学的都是 Pydantic 本身的功能。这一章把它放到**真实项目**中——看看在 FastAPI、LangChain、SQLAlchemy 里怎么用。

### 7.1 FastAPI 请求体与响应模型

FastAPI 的核心就是 Pydantic。**请求校验、响应序列化、Swagger 文档生成**全靠它。

```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr, computed_field
from datetime import datetime
from typing import Optional

app = FastAPI()

# ──────────────────────────────────────────
# 模型分层设计（第 4 章的 Base→Create→Response 模式）
# ──────────────────────────────────────────
class ArticleBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=10)
    tags: list[str] = Field(default_factory=list, max_length=10)

class ArticleCreate(ArticleBase):
    """创建文章的请求体"""
    author_email: EmailStr

class ArticleUpdate(BaseModel):
    """更新文章的请求体 — 所有字段可选"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=10)
    tags: Optional[list[str]] = None

class ArticleResponse(ArticleBase):
    """文章响应体 — 包含 ID 和时间"""
    id: int
    author_email: EmailStr
    created_at: datetime

    @computed_field
    @property
    def summary(self) -> str:
        return self.content[:100] + "..." if len(self.content) > 100 else self.content

# ──────────────────────────────────────────
# CRUD 接口
# ──────────────────────────────────────────
@app.post("/articles", response_model=ArticleResponse, status_code=201)
async def create_article(data: ArticleCreate):
    """创建文章 — data 已经过 Pydantic 校验"""
    article = save_to_db(data)  # data 是类型安全的 ArticleCreate 实例
    return article

@app.patch("/articles/{article_id}", response_model=ArticleResponse)
async def update_article(article_id: int, data: ArticleUpdate):
    """部分更新 — 只更新传入的字段"""
    # exclude_unset=True 的威力：只拿用户明确传入的字段
    update_data = data.model_dump(exclude_unset=True)
    # update_data = {"title": "新标题"}  ← 只包含用户传的字段
    article = update_in_db(article_id, update_data)
    return article

@app.get("/articles", response_model=list[ArticleResponse])
async def list_articles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),    # Query 参数也能用 Pydantic 约束
    tag: Optional[str] = None,
):
    return get_articles(page=page, size=size, tag=tag)
```

> 💡 **`ArticleUpdate` 全字段 Optional 的设计**：配合 `model_dump(exclude_unset=True)`，实现 PATCH 语义——用户只传 `{"title": "新标题"}`，就只更新 title，其他字段不动。这是 FastAPI 官方推荐的 PATCH 模式。

### 7.2 LangChain Structured Output（让 LLM 输出结构化数据）

这是 Pydantic 在 AI 工程中**最亮眼的用法**——用 Pydantic 模型定义"你期望 LLM 输出什么格式"，LangChain 自动把 LLM 的自由文本转成类型安全的 Python 对象。

```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from typing import Literal

# ──────────────────────────────────────────
# Step 1：用 Pydantic 定义期望的输出格式
# ──────────────────────────────────────────
class SentimentResult(BaseModel):
    """情感分析结果"""
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0, le=1, description="置信度 0-1")
    keywords: list[str] = Field(description="关键情感词")
    summary: str = Field(description="一句话总结")

# ──────────────────────────────────────────
# Step 2：用 with_structured_output 绑定模型
# ──────────────────────────────────────────
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(SentimentResult)

# ──────────────────────────────────────────
# Step 3：调用 — 返回的就是 Pydantic 实例！
# ──────────────────────────────────────────
result = structured_llm.invoke("分析这条评论的情感：'这个产品太棒了，物超所值！'")

print(type(result))           # <class 'SentimentResult'>  ← 不是 dict，是强类型对象！
print(result.sentiment)       # "positive"
print(result.confidence)      # 0.95
print(result.keywords)        # ["太棒了", "物超所值"]
print(result.model_dump())    # 可以直接序列化为 JSON
```

**更复杂的场景：提取结构化信息**

```python
class ExtractedEntity(BaseModel):
    """从文本中提取的实体"""
    name: str = Field(description="人名/公司名")
    role: str = Field(description="角色或职位")
    relation: str = Field(description="与其他实体的关系")

class DocumentAnalysis(BaseModel):
    """文档分析结果"""
    topic: str = Field(description="文档主题")
    entities: list[ExtractedEntity] = Field(description="提取的实体列表")
    action_items: list[str] = Field(description="待办事项")
    urgency: Literal["low", "medium", "high"]

structured_llm = llm.with_structured_output(DocumentAnalysis)

analysis = structured_llm.invoke("""
    分析这封邮件：
    张总，明天下午3点需要和李经理确认Q2预算方案，
    另外王工的技术方案也需要在周五前审批。
""")

print(analysis.action_items)
# ['确认Q2预算方案', '审批王工的技术方案']
print(analysis.urgency)
# 'high'
```

> 💡 **Pydantic 的 `description` 字段在这里至关重要**——LangChain 会把 Pydantic 模型转成 JSON Schema 传给 LLM，`description` 就是告诉 LLM "这个字段应该填什么"。写好 description = 写好 Prompt。

### 7.3 SQLAlchemy 模型 ↔ Pydantic 模型转换

数据库用 SQLAlchemy ORM 模型，API 用 Pydantic 模型——两套模型之间需要转换。Pydantic V2 用 `from_attributes=True` 轻松搞定：

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel, ConfigDict
from datetime import datetime

# ──────────────────────────────────────────
# SQLAlchemy ORM 模型（数据库层）
# ──────────────────────────────────────────
class Base(DeclarativeBase):
    pass

class UserORM(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

# ──────────────────────────────────────────
# Pydantic 模型（API 层）
# ──────────────────────────────────────────
class UserSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,    # ✨ 关键配置：允许从 ORM 对象创建 Pydantic 模型
    )
    
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime

# ──────────────────────────────────────────
# 转换示例
# ──────────────────────────────────────────

# 1. ORM → Pydantic（数据库查询结果 → API 响应）
db_user = session.get(UserORM, 1)          # SQLAlchemy ORM 对象
api_user = UserSchema.model_validate(db_user)  # ✨ 自动从 ORM 属性读取
print(api_user.model_dump())
# {'id': 1, 'name': '张三', 'email': 'zhang@example.com', ...}

# 2. Pydantic → ORM（API 请求 → 数据库写入）
class UserCreate(BaseModel):
    name: str
    email: str

create_data = UserCreate(name="李四", email="li@example.com")
new_user = UserORM(**create_data.model_dump())  # 字典解包创建 ORM 对象
session.add(new_user)
session.commit()
```

> 💡 **`from_attributes=True`**（V1 叫 `orm_mode=True`）是关键。没有它，`model_validate(orm_obj)` 会报错，因为 Pydantic 默认只接受 dict，不认识 ORM 对象的属性访问方式。

### 7.4 统一错误处理与友好错误信息

Pydantic 校验失败时会抛出 `ValidationError`，包含详细的错误信息。在 FastAPI 中可以自定义错误响应格式：

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

app = FastAPI()

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """自定义校验错误的响应格式"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " → ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input"),
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "数据校验失败",
            "errors": errors,
        }
    )
```

**返回给前端的错误格式：**

```json
{
  "code": 422,
  "message": "数据校验失败",
  "errors": [
    {
      "field": "body → username",
      "message": "String should have at least 2 characters",
      "type": "string_too_short",
      "input": "a"
    },
    {
      "field": "body → age",
      "message": "Input should be less than or equal to 150",
      "type": "less_than_equal",
      "input": 200
    }
  ]
}
```

**在代码中主动校验并捕获错误：**

```python
from pydantic import BaseModel, ValidationError

class Config(BaseModel):
    host: str
    port: int

# 安全校验：不让程序崩溃
try:
    config = Config(host="localhost", port="不是数字")
except ValidationError as e:
    print(f"错误数量: {e.error_count()}")
    print(f"错误列表: {e.errors()}")
    print(f"友好信息: {e}")
    # 可以记录日志、返回默认值等
```

> 💡 **`ValidationError.errors()`** 返回结构化的错误列表，每个错误包含 `type`（错误类型）、`loc`（字段路径）、`msg`（错误信息）、`input`（原始输入），适合日志记录和前端展示。

**第 7 章核心回顾：**

| 场景 | Pydantic 的角色 |
|:---|:---|
| **FastAPI 请求体** | 自动校验 + 类型转换 + Swagger 文档生成 |
| **FastAPI PATCH** | `exclude_unset=True` 实现部分更新 |
| **LangChain Structured Output** | 定义 LLM 输出格式，description = Prompt |
| **SQLAlchemy 转换** | `from_attributes=True` + `model_validate()` |
| **错误处理** | `ValidationError.errors()` 结构化错误信息 |

---

## 8. 性能优化与迁移指南

最后一章聚焦两件事：如果你还在用 V1，**怎么迁移到 V2**；如果已经在用 V2，**怎么榨干它的性能**。

### 8.1 Pydantic V2 vs V1：核心变化一览

Pydantic V2 在 2023 年 6 月发布，核心用 Rust 重写（pydantic-core），API 也做了大量调整。

**API 变化对照表：**

| V1 写法 | V2 写法 | 说明 |
|:---|:---|:---|
| `user.dict()` | `user.model_dump()` | 转字典 |
| `user.json()` | `user.model_dump_json()` | 转 JSON 字符串 |
| `User.parse_obj(data)` | `User.model_validate(data)` | 从字典创建 |
| `User.parse_raw(json_str)` | `User.model_validate_json(json_str)` | 从 JSON 创建 |
| `User.schema()` | `User.model_json_schema()` | 获取 JSON Schema |
| `User.construct(**data)` | `User.model_construct(**data)` | 跳过校验创建 |
| `user.copy(update={})` | `user.model_copy(update={})` | 复制并更新 |
| `@validator` | `@field_validator` | 字段校验器 |
| `@root_validator` | `@model_validator` | 模型校验器 |
| `class Config: orm_mode=True` | `model_config = ConfigDict(from_attributes=True)` | ORM 模式 |

**迁移示例：**

```python
# ──── V1 写法（已弃用）────
from pydantic import BaseModel, validator

class UserV1(BaseModel):
    name: str
    age: int

    class Config:
        orm_mode = True

    @validator("name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("name 不能为空")
        return v

# ──── V2 写法（推荐）────
from pydantic import BaseModel, field_validator, ConfigDict

class UserV2(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    age: int

    @field_validator("name")
    @classmethod                    # V2 要求加 @classmethod
    def name_not_empty(cls, v: str) -> str:  # V2 要求类型标注
        if not v.strip():
            raise ValueError("name 不能为空")
        return v
```

> 💡 **迁移工具**：运行 `pip install bump-pydantic && bump-pydantic .` 可以自动批量修改 V1 代码为 V2 语法。

### 8.2 TypeAdapter：不用 BaseModel 也能校验

有时候你只想校验一个简单类型（比如 `list[int]`），不值得为此定义一个完整的 BaseModel。`TypeAdapter` 就是为这个场景设计的：

```python
from pydantic import TypeAdapter

# ──── 校验简单类型 ────
int_adapter = TypeAdapter(int)
result = int_adapter.validate_python("42")    # "42" → 42
print(result, type(result))                   # 42 <class 'int'>

# ──── 校验列表类型 ────
list_adapter = TypeAdapter(list[int])
result = list_adapter.validate_python(["1", "2", "3"])
print(result)  # [1, 2, 3]（字符串自动转 int）

# ──── 校验复杂嵌套类型 ────
from typing import Optional
complex_adapter = TypeAdapter(dict[str, list[Optional[int]]])
result = complex_adapter.validate_python({
    "scores": [1, 2, None, "4"],
    "ranks": ["10", None],
})
print(result)
# {'scores': [1, 2, None, 4], 'ranks': [10, None]}

# ──── 校验 Pydantic 模型列表 ────
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

users_adapter = TypeAdapter(list[User])
users = users_adapter.validate_python([
    {"name": "张三", "age": 25},
    {"name": "李四", "age": "30"},
])
print(users)  # [User(name='张三', age=25), User(name='李四', age=30)]

# ──── 生成 JSON Schema ────
print(users_adapter.json_schema())
```

**TypeAdapter vs BaseModel 选型：**

| 场景 | 用什么 |
|:---|:---|
| 校验 API 请求体 | `BaseModel` |
| 校验单个值或简单类型 | `TypeAdapter` |
| 校验从数据库/缓存读出的数据 | `TypeAdapter` |
| 校验 JSON 配置文件内容 | `TypeAdapter` |
| 需要自定义校验器 | `BaseModel` |

> 💡 **性能优势**：`TypeAdapter` 在创建时就编译好了校验逻辑（Rust 层面），重复调用 `validate_python()` 非常快。适合在循环中大量校验数据。

### 8.3 性能优化技巧

Pydantic V2 已经很快了（Rust 核心），但在高频场景下还有优化空间。

**技巧 1：跳过校验 — model_construct()**

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

# 正常创建（带校验）— 安全但有开销
user = User(name="张三", age=25)

# 跳过校验创建 — 数据来源可信时使用（如数据库查询结果）
user = User.model_construct(name="张三", age=25)
# ⚠️ 不会做类型转换和校验！传 age="abc" 也不会报错
```

**技巧 2：Strict Mode — 禁用自动类型转换**

```python
from pydantic import BaseModel, ConfigDict

class StrictUser(BaseModel):
    model_config = ConfigDict(strict=True)  # 严格模式
    
    name: str
    age: int

StrictUser(name="张三", age=25)    # ✅
StrictUser(name="张三", age="25")  # ❌ 报错！strict 模式不允许 str → int
```

**技巧 3：复用 TypeAdapter 实例**

```python
from pydantic import TypeAdapter

# ❌ 每次创建 TypeAdapter（有编译开销）
for item in data_list:
    adapter = TypeAdapter(MyModel)     # 每次都重新编译
    adapter.validate_python(item)

# ✅ 提前创建，复用实例
adapter = TypeAdapter(MyModel)         # 只编译一次
for item in data_list:
    adapter.validate_python(item)      # 复用编译结果
```

**V2 vs V1 性能对比：**

| 操作 | V1 | V2 | 提升 |
|:---|:---|:---|:---|
| 模型创建 | 1x | 5-10x 更快 | ⚡ |
| JSON 解析 | 1x | 10-50x 更快 | ⚡⚡ |
| JSON 序列化 | 1x | 5-15x 更快 | ⚡ |
| JSON Schema 生成 | 1x | 2-5x 更快 | ⚡ |

> 💡 **核心原则**：内部可信数据用 `model_construct()` 跳过校验；外部不可信数据永远走正常校验。性能和安全不要二选一。

### 8.4 常见踩坑与解决方案

**踩坑 1：模型实例是不可变的（默认）**

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

user = User(name="张三", age=25)
user.name = "李四"  # ❌ ValidationError: Instance is frozen

# 解决方案 1：用 model_copy 创建新实例
new_user = user.model_copy(update={"name": "李四"})

# 解决方案 2：配置为可变
from pydantic import ConfigDict

class MutableUser(BaseModel):
    model_config = ConfigDict(frozen=False)  # 默认就是 False，但可以显式设置
    name: str
    age: int
```

**踩坑 2：自引用模型（递归结构）**

```python
from __future__ import annotations  # ✨ 延迟类型解析
from pydantic import BaseModel

class TreeNode(BaseModel):
    value: str
    children: list[TreeNode] = []  # 引用自身

# 必须在文件顶部加 `from __future__ import annotations`
# 或者用字符串类型标注：children: list["TreeNode"] = []

node = TreeNode(
    value="root",
    children=[
        TreeNode(value="child1"),
        TreeNode(value="child2", children=[
            TreeNode(value="grandchild")
        ]),
    ]
)
```

**踩坑 3：dict 和 model_dump() 的区别**

```python
class User(BaseModel):
    name: str
    age: int
    scores: list[int]

user = User(name="张三", age=25, scores=[90, 85])

# dict() 只做浅转换（V1 遗留，V2 已弃用）
# model_dump() 做深度递归转换（推荐）
data = user.model_dump()
print(type(data["scores"]))  # <class 'list'>  ← 完整转换
```

**踩坑 4：`Optional[str]` 不等于 `str = None`**

```python
from typing import Optional

class Example(BaseModel):
    # 这两个 ≠ 相同！
    a: Optional[str]         # 必须传，但可以传 None
    b: str | None = None     # 可以不传（有默认值 None）
    c: Optional[str] = None  # 可以不传，也可以传 None（最常用 ✨）
```

> 💡 **推荐写法**：`field: str | None = None`（Python 3.10+）或 `field: Optional[str] = None`。显式给默认值 `= None`，意图最清晰。

**第 8 章核心回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **V1 → V2 迁移** | API 全加 `model_` 前缀，用 bump-pydantic 自动迁移 |
| **TypeAdapter** | 不用 BaseModel 也能校验简单类型 |
| **model_construct()** | 跳过校验，可信数据专用，极致性能 |
| **Strict Mode** | 禁用自动类型转换，更严格 |
| **frozen 模型** | 默认不可变，用 model_copy() 创建新实例 |

---

## 🎉 全文总结

恭喜你读完了 Pydantic V2 的完整教程！回顾一下学到了什么：

| 章节 | 核心能力 |
|:---|:---|
| **第 1 章** | 理解为什么需要 Pydantic：声明式校验 > 手动 if-else |
| **第 2 章** | BaseModel 基础：类型、默认值、嵌套、序列化 |
| **第 3 章** | 自定义校验：field_validator / model_validator / Annotated |
| **第 4 章** | Field 配置：约束、别名、序列化控制、computed_field |
| **第 5 章** | 高级类型：Literal / Discriminated Union / 泛型模型 |
| **第 6 章** | 配置管理：BaseSettings / .env / 多环境 |
| **第 7 章** | 实战整合：FastAPI × LangChain × SQLAlchemy |
| **第 8 章** | 性能优化：TypeAdapter / model_construct / 迁移指南 |

> **一句话总结**：Pydantic 不只是一个校验库——它是 Python 生态中**数据质量的守护者**。掌握它，你的 API 更安全、LLM 输出更可控、配置管理更优雅。

---
