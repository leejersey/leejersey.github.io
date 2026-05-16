# Python 类型系统实战：从注解到工程化

> Python 是动态语言，但不意味着你要放弃类型安全。类型注解 + 静态检查 + Pydantic，让你写出比 Java 更安全、比 Go 更灵活的代码——同时保留 Python 的优雅。

---

## 1. 为什么需要类型注解

Python 是动态语言——变量不需要声明类型，函数参数可以传任何东西。这在写小脚本时很爽，但在大型项目中会变成**维护噩梦**。

### 1.1 动态类型的代价：大型项目的真实痛点

```python
# 你写了一个函数
def process_data(data, config):
    result = data.get("items")
    for item in result:
        if item["status"] == config.active_status:
            yield transform(item, config.mode)
```

三个月后，另一个同事要调用它。他面对的问题：
- `data` 是什么？dict？DataFrame？自定义对象？
- `config` 有哪些字段？`active_status` 还是 `activeStatus`？
- `transform` 返回什么？`dict`？`list`？`None`？
- 如果 `data.get("items")` 返回 `None`，会怎样？

```python
# 加上类型注解后，一切清晰
from dataclasses import dataclass

@dataclass
class Config:
    active_status: str
    mode: str

def process_data(
    data: dict[str, list[dict[str, str]]],
    config: Config
) -> Iterator[dict[str, str]]:
    result = data.get("items", [])
    for item in result:
        if item["status"] == config.active_status:
            yield transform(item, config.mode)
```

> 💡 **核心观点：** 类型注解不是给 Python 运行时看的（它不会做运行时检查），而是给**人和工具**看的——你的同事、你的 IDE、你的 CI 管线。

### 1.2 类型注解的三重价值：文档/检查/智能提示

| 价值 | 说明 | 受益者 |
|------|------|--------|
| **活文档** | 类型注解就是最好的文档，永远不过期 | 你的同事和未来的你 |
| **静态检查** | mypy/pyright 在运行前发现类型错误 | CI 管线 |
| **智能提示** | IDE 精确补全属性和方法 | 开发者日常效率 |

```python
# 没有类型注解：IDE 不知道 user 有什么属性
def get_display_name(user):
    return user.name  # IDE: 🤷 user 是什么？

# 有类型注解：IDE 精确提示
def get_display_name(user: User) -> str:
    return user.name  # IDE: ✅ User.name: str
    # 输入 user. 后，IDE 自动列出所有属性
```
### 1.3 Python 类型系统的演进：3.5 到 3.13

| 版本 | 年份 | 关键特性 |
|------|------|---------|
| 3.5 | 2015 | `typing` 模块首次引入，支持函数注解 |
| 3.6 | 2016 | 变量注解 `x: int = 1`、`NamedTuple` 类语法 |
| 3.7 | 2018 | `from __future__ import annotations`（延迟求值） |
| 3.8 | 2019 | `TypedDict`、`Protocol`、`Literal`、`Final` |
| 3.9 | 2020 | `list[int]` 替代 `List[int]`（内置泛型） |
| 3.10 | 2021 | `X \| Y` 替代 `Union[X, Y]`、`TypeGuard`、`ParamSpec` |
| 3.11 | 2022 | `Self` 类型、`TypeVarTuple`（可变泛型） |
| 3.12 | 2023 | `type` 语句、`@override`、泛型新语法 `def f[T]()` |
| 3.13 | 2024 | `ReadOnly` TypedDict、`TypeIs`（替代 TypeGuard） |

> 💡 **版本建议：** 如果你的项目用 Python 3.10+，可以直接使用 `list[int]` 和 `X | Y` 语法。如果还在 3.9 以下，用 `from __future__ import annotations` 提前启用新语法。

---

## 2. 基础类型注解

掌握这些就能覆盖 90% 的日常类型标注需求。

### 2.1 基本类型与变量注解

```python
# 基本类型
name: str = "Alice"
age: int = 30
height: float = 1.75
is_active: bool = True

# 注意：注解不强制赋值
email: str  # 合法！只声明类型，不赋值（在 class 中常见）

# bytes 和 None
data: bytes = b"hello"
nothing: None = None
```

### 2.2 容器类型：list[int]、dict[str, Any]

```python
from typing import Any

# Python 3.9+ 可直接使用内置类型
names: list[str] = ["Alice", "Bob"]
scores: dict[str, int] = {"math": 95, "english": 88}
unique_ids: set[int] = {1, 2, 3}
coordinates: tuple[float, float] = (39.9, 116.4)  # 固定长度

# 可变长度元组
tags: tuple[str, ...] = ("python", "typing", "tutorial")

# 嵌套容器
matrix: list[list[int]] = [[1, 2], [3, 4]]
config: dict[str, Any] = {"debug": True, "port": 8080}

# Python 3.8 及以下需要从 typing 导入
# from typing import List, Dict, Set, Tuple
# names: List[str] = ["Alice", "Bob"]
```

**`tuple` 的两种用法：**

| 写法 | 含义 | 示例 |
|------|------|------|
| `tuple[int, str]` | 固定长度，每个位置有类型 | `(1, "hello")` |
| `tuple[int, ...]` | 可变长度，所有元素同类型 | `(1, 2, 3, 4)` |

### 2.3 可选与联合类型：Optional、Union、X | Y

```python
from typing import Optional, Union

# 三种写法，完全等价（Python 3.10+）
def find_user(user_id: int) -> Optional[str]:     # 方式1
def find_user(user_id: int) -> Union[str, None]:   # 方式2
def find_user(user_id: int) -> str | None:         # 方式3（推荐）
    ...

# 联合类型：接受多种类型
def parse_input(value: str | int | float) -> str:
    return str(value)

# ⚠️ Optional 的常见误解
# Optional[str] 不是"这个参数可以不传"
# 它的意思是"这个值可能是 str，也可能是 None"

def greet(name: str | None = None) -> str:
    # name 可以是 None（Optional）
    # name 有默认值 None（可以不传）
    # 这是两个独立的概念！
    if name is None:
        return "Hello, stranger!"
    return f"Hello, {name}!"
```

**None 安全处理模式：**

```python
# ❌ mypy 会报错：name 可能是 None
def get_length(name: str | None) -> int:
    return len(name)  # error: Argument of type "str | None"

# ✅ 先检查 None（类型缩窄）
def get_length(name: str | None) -> int:
    if name is None:
        return 0
    return len(name)  # mypy 知道这里 name 一定是 str
```
### 2.4 函数签名：参数注解与返回值

```python
from collections.abc import Iterator, Callable

# 基础函数签名
def add(a: int, b: int) -> int:
    return a + b

# 无返回值用 None
def log(message: str) -> None:
    print(message)

# *args 和 **kwargs
def flexible(*args: int, **kwargs: str) -> None:
    # args 的每个元素是 int
    # kwargs 的每个值是 str
    pass

# 回调函数类型
def apply(
    func: Callable[[int, int], int],  # 接受两个 int，返回 int
    x: int,
    y: int
) -> int:
    return func(x, y)

# 生成器
def count_up(n: int) -> Iterator[int]:
    for i in range(n):
        yield i

# 默认值
def connect(
    host: str = "localhost",
    port: int = 5432,
    timeout: float | None = None
) -> None:
    ...
```

> 💡 **实战建议：** 刚开始给项目加类型注解？从**函数签名**开始——它的投入产出比最高。函数内部的局部变量，mypy 通常能自动推断，不需要手动标注。

---

## 3. 进阶类型系统

这一章是 Python 类型系统的**真正威力所在**——掌握了这些，你就能写出媲美静态语言的类型安全代码。

### 3.1 泛型编程：TypeVar 与 Generic

```python
from typing import TypeVar, Generic

# 问题：这个函数接受任何类型，返回什么类型？
def first(items: list) -> ???:
    return items[0]

# TypeVar：声明一个类型变量
T = TypeVar("T")

def first(items: list[T]) -> T:
    """输入 list[int] 返回 int，输入 list[str] 返回 str"""
    return items[0]

# mypy 能推断：
x: int = first([1, 2, 3])      # ✅ T = int
y: str = first(["a", "b"])     # ✅ T = str
z: int = first(["a", "b"])     # ❌ error: str != int
```

```python
# 约束 TypeVar 的范围
from typing import TypeVar

# T 只能是 int 或 float
Number = TypeVar("Number", int, float)

def double(x: Number) -> Number:
    return x * 2

# bound：T 必须是某个类型的子类
from typing import TypeVar

T = TypeVar("T", bound="Comparable")

# 自定义泛型类
class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []
    
    def push(self, item: T) -> None:
        self._items.append(item)
    
    def pop(self) -> T:
        return self._items.pop()

# 使用
int_stack: Stack[int] = Stack()
int_stack.push(42)       # ✅
int_stack.push("hello")  # ❌ error: str != int
```

### 3.2 结构化子类型：Protocol 与鸭子类型的类型化

Python 的哲学是"鸭子类型"——Protocol 让它**既鸭子又安全**：

```python
from typing import Protocol, runtime_checkable

# 定义一个 Protocol：任何有 read() 方法的对象
class Readable(Protocol):
    def read(self) -> str: ...

# 这些类不需要继承 Readable！
class FileReader:
    def read(self) -> str:
        return open("data.txt").read()

class StringReader:
    def read(self) -> str:
        return "hello world"

class DatabaseReader:
    def read(self) -> str:
        return db.query("SELECT ...")

# 函数接受任何"可读"的对象
def process(source: Readable) -> str:
    return source.read().upper()

# 全部合法——只要有 read() 方法
process(FileReader())      # ✅
process(StringReader())    # ✅
process(DatabaseReader())  # ✅
process(42)                # ❌ int 没有 read()
```

```python
# @runtime_checkable：让 Protocol 支持 isinstance 检查
@runtime_checkable
class Closable(Protocol):
    def close(self) -> None: ...

f = open("test.txt")
print(isinstance(f, Closable))  # True（file 有 close 方法）
print(isinstance(42, Closable)) # False

# ⚠️ 注意：运行时检查只看方法名是否存在，
# 不检查参数类型和返回值类型
```

### 3.3 字面量类型：Literal 与 Enum 的对比

```python
from typing import Literal

# Literal：限制参数只能是特定值
def set_color(color: Literal["red", "green", "blue"]) -> None:
    print(f"Setting color to {color}")

set_color("red")     # ✅
set_color("yellow")  # ❌ error: "yellow" not in Literal

# 实际应用：API 状态码
def handle_response(
    status: Literal["success", "error", "pending"]
) -> str:
    match status:
        case "success": return "✅ Done"
        case "error":   return "❌ Failed"
        case "pending": return "⏳ Waiting"
```

**Literal vs Enum 选型：**

| 场景 | 用 Literal | 用 Enum |
|------|-----------|---------|
| 简单字符串约束 | ✅ `Literal["a", "b"]` | 过重 |
| 需要遍历所有值 | ❌ 不支持 | ✅ `for s in Status` |
| 需要关联方法/属性 | ❌ 不支持 | ✅ `Status.label()` |
| JSON 序列化 | ✅ 天然是 str/int | 需要自定义 |
### 3.4 类型守卫：TypeGuard 与类型缩窄

```python
from typing import TypeGuard

# 自定义类型守卫函数
def is_string_list(val: list[object]) -> TypeGuard[list[str]]:
    """检查列表是否全是字符串"""
    return all(isinstance(x, str) for x in val)

def process(data: list[object]) -> None:
    if is_string_list(data):
        # mypy 在这个分支里知道 data 是 list[str]
        print(data[0].upper())  # ✅ 可以调用 str 的方法
    else:
        print("Not all strings")

# Python 3.13 引入 TypeIs（更精确的替代）
from typing import TypeIs

def is_str(val: object) -> TypeIs[str]:
    return isinstance(val, str)

# TypeGuard vs TypeIs 的区别：
# TypeGuard: 只在 True 分支缩窄类型
# TypeIs:    True 和 False 分支都缩窄
```
### 3.5 装饰器类型：ParamSpec 与 Concatenate

装饰器是 Python 的灵魂——但在有 ParamSpec 之前，没法正确标注：

```python
from typing import ParamSpec, TypeVar, Callable
from functools import wraps
import time

P = ParamSpec("P")   # 捕获被装饰函数的参数类型
R = TypeVar("R")     # 捕获被装饰函数的返回值类型

def timer(func: Callable[P, R]) -> Callable[P, R]:
    """计时装饰器——保留被装饰函数的完整类型签名"""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.2f}s")
        return result
    return wrapper

@timer
def add(a: int, b: int) -> int:
    return a + b

# mypy 完整保留了 add 的类型签名
add(1, 2)        # ✅ 返回 int
add("a", "b")    # ❌ error: str != int
```

> 💡 **进阶总结：** TypeVar 解决泛型、Protocol 解决鸭子类型、Literal 解决枚举值、TypeGuard 解决类型缩窄、ParamSpec 解决装饰器。五个工具覆盖 99% 的进阶场景。

---

## 4. Python 3.12+ 新特性

Python 3.12 对类型系统做了**有史以来最大的语法升级**——写类型注解终于不再啰嗦。

### 4.1 type 语句：原生类型别名（PEP 695）

```python
# 旧写法（3.11 及以下）
from typing import TypeAlias, Union

Vector: TypeAlias = list[float]
Result: TypeAlias = dict[str, Union[int, str, None]]

# 新写法（3.12+）——原生 type 语句
type Vector = list[float]
type Result = dict[str, int | str | None]

# 支持递归类型（旧写法非常痛苦）
type JSON = str | int | float | bool | None | list["JSON"] | dict[str, "JSON"]

# 旧写法需要：
# JSON = Union[str, int, float, bool, None, list["JSON"], dict[str, "JSON"]]
# 还需要 from __future__ import annotations
```

**type 语句的优势：**
- 语法简洁，像赋值一样自然
- **延迟求值**——不需要引号包裹前向引用
- 支持递归类型定义

### 4.2 泛型新语法：def func[T](x: T) -> T

```python
# 旧写法（3.11 及以下）
from typing import TypeVar, Generic

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

def first(items: list[T]) -> T:
    return items[0]

class Pair(Generic[K, V]):
    def __init__(self, key: K, value: V) -> None:
        self.key = key
        self.value = value

# 新写法（3.12+）——直接在 [] 中声明类型参数
def first[T](items: list[T]) -> T:
    return items[0]

class Pair[K, V]:
    def __init__(self, key: K, value: V) -> None:
        self.key = key
        self.value = value

# 带约束的泛型
def max_value[T: (int, float)](a: T, b: T) -> T:
    return a if a > b else b

# bound 约束
from collections.abc import Hashable

def dedup[T: Hashable](items: list[T]) -> set[T]:
    return set(items)
```

| 对比 | 旧写法（3.11-） | 新写法（3.12+） |
|------|----------------|----------------|
| 声明 TypeVar | `T = TypeVar("T")` | 直接 `[T]` |
| 泛型类 | `class Foo(Generic[T])` | `class Foo[T]` |
| 约束 | `TypeVar("T", int, str)` | `[T: (int, str)]` |
| bound | `TypeVar("T", bound=X)` | `[T: X]` |

### 4.3 @override 装饰器：安全的方法重写

```python
from typing import override

class Animal:
    def speak(self) -> str:
        return "..."

class Dog(Animal):
    @override
    def speak(self) -> str:  # ✅ 正确重写
        return "Woof!"
    
    @override
    def spek(self) -> str:   # ❌ mypy error: 父类没有 spek 方法
        return "Woof!"       # 发现拼写错误！

# 没有 @override 时，spek 会被当成新方法，不报错
# 有了 @override，mypy 确保你真的在重写父类方法
```

### 4.4 Python 3.13 的类型改进

```python
# TypeIs：比 TypeGuard 更精确（PEP 742）
from typing import TypeIs

def is_str(val: str | int) -> TypeIs[str]:
    return isinstance(val, str)

def process(val: str | int) -> None:
    if is_str(val):
        print(val.upper())  # val: str
    else:
        print(val + 1)      # val: int ← TypeIs 能缩窄 else 分支！

# ReadOnly TypedDict（PEP 705）
from typing import ReadOnly, TypedDict

class Config(TypedDict):
    host: str
    port: ReadOnly[int]  # 只读字段

config: Config = {"host": "localhost", "port": 8080}
config["host"] = "0.0.0.0"  # ✅ 可修改
config["port"] = 3000        # ❌ error: port 是只读的
```

> 💡 **迁移建议：** 新项目直接用 3.12+ 语法（`type`、`[T]`、`@override`）。旧项目不需要急着迁移——旧写法依然 100% 有效。

---

## 5. Pydantic V2：运行时类型验证

typing 模块的类型注解在运行时**不做任何检查**——Pydantic 补上了这一环。

### 5.1 BaseModel 基础：定义与验证

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    email: str

# 合法数据 → 正常创建
user = User(name="Alice", age=30, email="alice@example.com")

# 类型错误 → 运行时抛出 ValidationError
try:
    user = User(name="Alice", age="not a number", email="alice@example.com")
except Exception as e:
    print(e)
    # age: Input should be a valid integer

# 自动类型转换（coercion）
user = User(name="Alice", age="30", email="alice@example.com")
print(user.age)        # 30（str → int 自动转换）
print(type(user.age))  # <class 'int'>
```

### 5.2 Field 验证：约束、默认值、别名

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="价格必须大于 0")
    quantity: int = Field(default=0, ge=0)
    sku: str = Field(alias="product_sku")  # JSON 中叫 product_sku

# 验证约束
Product(name="", price=10.0)       # ❌ name 太短
Product(name="iPhone", price=-1)   # ❌ price 必须 > 0
Product(name="iPhone", price=999)  # ✅

# 别名：接受 JSON 中的不同字段名
data = {"name": "iPhone", "price": 999, "product_sku": "IP-001"}
product = Product(**data)  # ✅ product_sku → sku
```

**常用 Field 约束速查：**

| 约束 | 适用类型 | 说明 |
|------|---------|------|
| `gt` / `ge` | 数值 | 大于 / 大于等于 |
| `lt` / `le` | 数值 | 小于 / 小于等于 |
| `min_length` / `max_length` | 字符串 | 长度范围 |
| `pattern` | 字符串 | 正则匹配 |
| `default` | 全部 | 默认值 |
| `alias` | 全部 | 字段别名 |

### 5.3 自定义验证器：@field_validator 与 @model_validator

```python
from pydantic import BaseModel, field_validator, model_validator

class UserCreate(BaseModel):
    username: str
    password: str
    confirm_password: str

    # 字段级验证器
    @field_validator("username")
    @classmethod
    def username_must_be_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("用户名只能包含字母和数字")
        return v.lower()  # 自动转小写

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码至少 8 位")
        return v

    # 模型级验证器：跨字段验证
    @model_validator(mode="after")
    def passwords_match(self) -> "UserCreate":
        if self.password != self.confirm_password:
            raise ValueError("两次密码不一致")
        return self
```

### 5.4 嵌套模型与 JSON 序列化

```python
from pydantic import BaseModel
from datetime import datetime

class Address(BaseModel):
    city: str
    street: str
    zipcode: str

class Order(BaseModel):
    id: int
    items: list[str]
    shipping_address: Address
    created_at: datetime

# 嵌套 JSON → 自动解析
data = {
    "id": 1,
    "items": ["iPhone", "Case"],
    "shipping_address": {
        "city": "Beijing",
        "street": "Chaoyang Road",
        "zipcode": "100000"
    },
    "created_at": "2025-01-15T10:30:00"
}

order = Order(**data)
print(order.shipping_address.city)  # Beijing
print(order.created_at.year)        # 2025（自动解析 datetime）

# 序列化
print(order.model_dump())           # → dict
print(order.model_dump_json())      # → JSON 字符串
```

### 5.5 Pydantic + FastAPI：请求/响应模型

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

# 请求模型
class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    email: str
    password: str = Field(min_length=8)

# 响应模型（不返回 password）
class UserResponse(BaseModel):
    id: int
    username: str
    email: str

@app.post("/users", response_model=UserResponse)
async def create_user(req: CreateUserRequest) -> UserResponse:
    # FastAPI 自动验证请求体
    # 如果 username 太短 → 自动返回 422 错误
    user = save_to_db(req)
    return UserResponse(id=user.id, username=req.username, email=req.email)
```

> 💡 **核心理解：** `typing` 是**静态**类型检查（IDE + mypy），Pydantic 是**运行时**类型验证（数据校验）。两者互补，不冲突——在 FastAPI 项目中，你同时用到两者。

---

## 6. mypy 静态检查实战

类型注解写了，谁来检查？**mypy** 是 Python 官方推荐的静态类型检查器。

### 6.1 安装与基础配置

```bash
# 安装
pip install mypy

# 检查单个文件
mypy app.py

# 检查整个项目
mypy src/

# 常用选项
mypy --ignore-missing-imports src/  # 忽略缺少类型存根的第三方库
mypy --show-error-codes src/        # 显示错误代码（便于配置忽略规则）
```

### 6.2 严格模式：--strict 的每一项含义

```bash
# --strict 等价于启用以下所有选项：
mypy --strict src/
```

| 选项 | 含义 | 建议 |
|------|------|------|
| `--disallow-untyped-defs` | 所有函数必须有类型注解 | ✅ 必开 |
| `--disallow-any-generics` | 禁止裸 `list`（必须 `list[int]`） | ✅ 推荐 |
| `--warn-return-any` | 警告返回 `Any` 类型 | ✅ 推荐 |
| `--no-implicit-optional` | `None` 默认值不自动变 Optional | ✅ 推荐 |
| `--strict-equality` | 禁止不同类型的 `==` 比较 | ⚠️ 可选 |
| `--disallow-untyped-calls` | 禁止调用未注解的函数 | ⚠️ 渐进开启 |

### 6.3 常见类型错误与修复方法

```python
# 错误 1: Incompatible return value type
def get_name() -> str:
    return None  # ❌ error
# 修复：
def get_name() -> str | None:
    return None  # ✅

# 错误 2: Item "None" of "Optional[str]" has no attribute "upper"
def shout(name: str | None) -> str:
    return name.upper()  # ❌ name 可能是 None
# 修复：
def shout(name: str | None) -> str:
    if name is None:
        return ""
    return name.upper()  # ✅

# 错误 3: Missing type annotation for function
def add(a, b):       # ❌ 缺少注解
    return a + b
# 修复：
def add(a: int, b: int) -> int:  # ✅
    return a + b

# 错误 4: 第三方库没有类型存根
import requests  # ❌ error: Missing library stubs
# 修复方案 A：安装类型存根
# pip install types-requests
# 修复方案 B：配置忽略
# mypy.ini: [mypy-requests.*] ignore_missing_imports = True
```

### 6.4 渐进式迁移：从 0 到全覆盖

```
迁移路线图：

  阶段 1（第 1 周）：基础启用
  → mypy src/ --ignore-missing-imports
  → 只修复最严重的错误
  
  阶段 2（第 2-4 周）：核心模块
  → 给核心模块的所有函数加注解
  → 启用 --disallow-untyped-defs（仅核心模块）
  
  阶段 3（第 1-2 月）：全量覆盖
  → 逐步扩展到所有模块
  → 启用 --strict
  → 接入 CI 门禁（mypy 失败 = 不能合并）
```

> 💡 **务实原则：** 不要试图一天内给整个项目加满类型注解。从核心模块的函数签名开始，逐步扩展——这比一步到位成功率高 10 倍。

---

## 7. dataclass 与类型化数据结构

dataclass 是 Python 标准库自带的"轻量数据建模"——不需要安装任何第三方库。

### 7.1 dataclass 高级用法：field、post_init、ordering

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Task:
    title: str
    priority: int = 0
    tags: list[str] = field(default_factory=list)  # 可变默认值
    created_at: datetime = field(default_factory=datetime.now)
    _id: int = field(init=False, repr=False)        # 不参与初始化

    def __post_init__(self) -> None:
        """初始化后自动执行"""
        self._id = hash(self.title + str(self.created_at))
        self.title = self.title.strip()

task = Task(title="  Write docs  ", priority=1, tags=["python"])
print(task.title)  # "Write docs"（自动 strip）
```

```python
# 排序支持
@dataclass(order=True)
class Student:
    gpa: float
    name: str = field(compare=False)  # name 不参与排序

students = [
    Student(3.8, "Alice"),
    Student(3.5, "Bob"),
    Student(3.9, "Charlie"),
]
print(sorted(students))  # 按 gpa 排序
```

### 7.2 slots=True：内存优化与性能提升

```python
@dataclass(slots=True)
class Point:
    x: float
    y: float

# slots=True 的效果：
# ✅ 内存减少 ~40%（不创建 __dict__）
# ✅ 属性访问快 ~10-20%
# ❌ 不能动态添加属性
# ❌ 不能使用多继承（有限制）

p = Point(1.0, 2.0)
p.z = 3.0  # ❌ AttributeError: 'Point' has no attribute 'z'
```

### 7.3 frozen=True：不可变数据对象

```python
@dataclass(frozen=True)
class Config:
    host: str
    port: int
    debug: bool = False

config = Config(host="localhost", port=8080)
config.port = 3000  # ❌ FrozenInstanceError

# frozen 对象可以作为 dict 的 key 和 set 的元素
configs = {config: "production"}  # ✅ 可哈希
```

### 7.4 dataclass vs Pydantic vs TypedDict 选型

| 维度 | dataclass | Pydantic | TypedDict |
|------|-----------|----------|-----------|
| **运行时验证** | ❌ | ✅ 自动验证 | ❌ |
| **性能** | ⚡ 最快 | 🐢 较慢（有验证开销） | ⚡ 最快（就是 dict） |
| **序列化** | 需手写 | ✅ model_dump / model_dump_json | 不需要（就是 dict） |
| **IDE 支持** | ✅ 好 | ✅ 好 | ✅ 好 |
| **不可变** | ✅ frozen=True | ✅ model_config frozen | ❌ |
| **适用场景** | 内部数据结构 | API 边界/外部数据 | 类型化 dict |

> 💡 **选型口诀：** 内部传数据用 **dataclass**，接收外部输入用 **Pydantic**，给 dict 加类型用 **TypedDict**。

---

## 8. 工程最佳实践

类型系统的最终目标不是"写注解"，而是**用类型驱动设计**。

### 8.1 类型驱动设计：NewType、TypeAlias、Annotated

```python
from typing import NewType, Annotated
from annotated_types import Gt, MaxLen

# NewType：创建语义不同的类型（编译期区分）
UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)

def get_user(user_id: UserId) -> User: ...
def get_order(order_id: OrderId) -> Order: ...

uid = UserId(42)
oid = OrderId(42)
get_user(uid)   # ✅
get_user(oid)   # ❌ error: OrderId != UserId
# 即使底层都是 int，mypy 也能区分！

# Annotated：给类型附加元数据
type PositiveInt = Annotated[int, Gt(0)]
type Username = Annotated[str, MaxLen(20)]

def create_user(name: Username, age: PositiveInt) -> None:
    ...
# Pydantic 和 FastAPI 会读取这些元数据做运行时验证
```

### 8.2 项目级配置：pyproject.toml 中的 mypy 配置

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true

# 第三方库配置
[tool.mypy.overrides](tool.mypy.overrides)
module = "requests.*"
ignore_missing_imports = true

[tool.mypy.overrides](tool.mypy.overrides)
module = "celery.*"
ignore_missing_imports = true

# 渐进式：对旧模块放宽要求
[tool.mypy.overrides](tool.mypy.overrides)
module = "legacy_module.*"
disallow_untyped_defs = false
```

### 8.3 mypy vs pyright vs pytype：选型建议

| 维度 | mypy | pyright | pytype |
|------|------|---------|--------|
| **维护者** | Python 官方 | Microsoft | Google |
| **速度** | 中等 | ⚡ 非常快 | 🐢 较慢 |
| **严格程度** | 中等 | 最严格 | 最宽松 |
| **IDE 集成** | 插件 | VS Code 内置（Pylance） | 插件 |
| **生态** | 最成熟 | 快速增长 | 较小 |
| **推荐** | 通用选择 | VS Code 用户 | 渐进迁移 |

### 8.4 团队协作：类型覆盖率目标与 CI 门禁

```yaml
# GitHub Actions CI 配置示例
name: Type Check
on: [push, pull_request]

jobs:
  mypy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install mypy
      - run: mypy src/ --strict
```

```
团队类型覆盖率目标：

  新项目：从第一天起 mypy --strict
  
  旧项目迁移：
  第 1 月：50% 覆盖率（核心模块）
  第 3 月：80% 覆盖率（大部分模块）
  第 6 月：95% 覆盖率（仅允许少量 type: ignore）
```

### 8.5 延伸阅读与参考资料

**官方资源：**
- [typing 模块文档](https://docs.python.org/3/library/typing.html)
- [mypy 文档](https://mypy.readthedocs.io/)
- [Pydantic V2 文档](https://docs.pydantic.dev/)
- [PEP 695 — Type Parameter Syntax](https://peps.python.org/pep-0695/)

**推荐阅读：**
- [Python 装饰器与元编程](Python 装饰器与元编程) — 装饰器的类型标注（ParamSpec）实战
- [Python 异步编程完全指南](Python 异步编程完全指南) — 异步代码的类型标注模式

---

> **全书完。**
>
> Python 类型系统的核心思路就一句话：
> **用类型注解说清楚"这是什么"，用 mypy 确保"说到做到"，用 Pydantic 在运行时兜底。**
>
> 从今天起，给每个新函数加上类型注解。
> 三个月后，你会感谢自己。🐍
