# 第一章 初识 FastAPI

> **本章目标**：理解 FastAPI 是什么、为什么选它，并在 5 分钟内跑通第一个 API。
>
> **预计时长**：30 分钟

---

## 1.1 FastAPI 是什么

FastAPI 是一个用 Python 构建 Web API 的现代框架，由 Sebastián Ramírez 于 2018 年发布。

一句话总结：**用 Python 类型提示来定义 API，框架帮你自动完成参数校验、文档生成和序列化。**

### 核心卖点

| 特性 | 说明 |
|------|------|
| **快（性能）** | 基于 ASGI，性能与 Node.js、Go 同级别，是 Flask 的 5\~10 倍 |
| **快（开发）** | 类型提示驱动，编辑器自动补全极好，开发速度提升 200\~300% |
| **少 Bug** | 请求参数自动校验，类型错误在进入业务逻辑前就被拦截 |
| **标准化** | 完全兼容 OpenAPI（Swagger）和 JSON Schema 标准 |
| **自动文档** | 启动即自带交互式 API 文档，无需任何额外配置 |

### 技术架构

FastAPI 不是从零造轮子，它站在两个强大的库之上：

```
FastAPI
  ├── Starlette  → 负责 Web 层（路由、请求、响应、WebSocket、中间件）
  └── Pydantic   → 负责数据层（数据校验、序列化、类型转换）
```

你写的代码 → FastAPI 编排 → Starlette 处理 HTTP → Pydantic 校验数据。

这意味着：
- Starlette 能做的事（WebSocket、中间件、静态文件），FastAPI 都能做
- Pydantic 能做的事（复杂数据校验、嵌套模型），FastAPI 都能用

---

## 1.2 与 Flask / Django REST Framework 的对比

如果你之前用过 Flask 或 Django，这张对比表可以帮你快速定位 FastAPI：

| 维度 | Flask | Django REST Framework | FastAPI |
|------|-------|----------------------|---------|
| **定位** | 轻量 Web 框架 | 全功能 Web + API | 专注 API 开发 |
| **协议** | WSGI（同步） | WSGI（同步） | ASGI（异步） |
| **数据校验** | 手动 / 第三方库 | Serializer | Pydantic（自动） |
| **API 文档** | 需要 flask-swagger 等插件 | 内置但较重 | **自动生成，零配置** |
| **类型提示** | 不依赖 | 不依赖 | **核心驱动力** |
| **学习曲线** | 低 | 高 | 低 |
| **性能** | 一般 | 一般 | **极高** |
| **适合场景** | 小项目、快速原型 | 全栈 Web 应用 | API 服务、微服务 |

### 关键区别：WSGI vs ASGI

```
WSGI（Flask/Django）：一个请求占一个线程，等 I/O 时线程闲置
  请求1 ████████░░░░████  （░ = 等待数据库）
  请求2          ████████░░░░████
  → 同一时间只能处理有限请求

ASGI（FastAPI）：等 I/O 时切换去处理别的请求
  请求1 ████░░░░████
  请求2     ████░░░░████
  请求3         ████░░░░████
  → 同样的资源，吞吐量大幅提升
```

**简单说**：如果你的 API 经常要等数据库、等外部接口（大部分场景都是），FastAPI 的异步架构天然更高效。

---

## 1.3 五分钟跑通第一个 API

### 第一步：安装

```bash
# 推荐用 standard 选项，自带 uvicorn 服务器等常用组件
pip install "fastapi[standard]"
```

### 第二步：写代码

创建 `main.py`：

```python
from fastapi import FastAPI

# 创建应用实例
app = FastAPI()


# 定义一个 GET 接口
@app.get("/")
def hello():
    return {"message": "Hello, FastAPI!"}


# 带路径参数的接口
@app.get("/hello/{name}")
def hello_name(name: str):
    return {"message": f"Hello, {name}!"}
```

就这么几行，你已经有了：
- ✅ 一个能运行的 API 服务
- ✅ 自动参数类型校验
- ✅ 自动生成的交互式文档

### 第三步：启动

```bash
fastapi dev main.py
```

你会看到类似输出：

```
INFO     Using path main.py
INFO     Resolved absolute path d:\dw_ai_project\fastpai入门\main.py
INFO     Searching for package file structure from directories with __init__.py files
INFO     Importing from d:\dw_ai_project\fastpai入门

 ╭─ FastAPI CLI - Development mode ─╮
 │                                   │
 │  Serving at: http://127.0.0.1:8000│
 │                                   │
 │  API docs: http://127.0.0.1:8000  │
 │    /docs                          │
 │                                   │
 ╰───────────────────────────────────╯

INFO:     Will watch for changes in these directories: [...]
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

> **提示**：`fastapi dev` 是开发模式，支持代码热重载——修改代码后自动重启，非常方便。

### 第四步：验证

打开浏览器，访问以下地址：

| 地址 | 说明 |
|------|------|
| http://127.0.0.1:8000 | 接口返回 `{"message": "Hello, FastAPI!"}` |
| http://127.0.0.1:8000/hello/张三 | 接口返回 `{"message": "Hello, 张三!"}` |
| http://127.0.0.1:8000/docs | **Swagger UI** — 交互式文档，可以直接测试接口 |
| http://127.0.0.1:8000/redoc | **ReDoc** — 另一种风格的 API 文档 |

### 重点体验：/docs 页面

打开 `/docs`，你会看到一个漂亮的交互式文档页面：

1. 所有接口自动列出，包括路径、方法、参数
2. 点击任意接口 → 点击 **"Try it out"** → 填写参数 → 点击 **"Execute"**
3. 直接看到请求和响应结果

**这个文档是 FastAPI 根据你的代码自动生成的，不需要写任何额外的文档配置。** 这是 FastAPI 最让人爱不释手的特性之一。

---

## 1.4 代码解析：为什么这么简洁？

让我们回头看那几行代码，理解 FastAPI 的设计哲学：

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello/{name}")
def hello_name(name: str):
    return {"message": f"Hello, {name}!"}
```

这段代码同时做了 **5 件事**：

| 你写的代码 | FastAPI 自动帮你做的 |
|-----------|-------------------|
| `@app.get("/hello/{name}")` | 注册路由，声明 HTTP 方法为 GET |
| `name: str` | 从 URL 路径中提取参数，并校验类型 |
| `def hello_name(...)` | 函数名成为文档中的接口名称 |
| `return {"message": ...}` | 自动序列化为 JSON 响应 |
| （什么都没写） | 自动生成 OpenAPI 文档 |

**核心理念**：你只需要用 Python 的类型提示（Type Hints）描述你的接口「长什么样」，FastAPI 帮你处理一切。

---

## 1.5 动手练习

在 `main.py` 中新增以下接口，加深理解：

**练习 1**：创建一个计算器接口

```python
@app.get("/add/{a}/{b}")
def add(a: int, b: int):
    return {"result": a + b}
```

启动后访问 http://127.0.0.1:8000/add/3/5 ，观察返回结果。

然后试试访问 http://127.0.0.1:8000/add/hello/5 ，看看 FastAPI 如何处理类型错误——它会自动返回一个清晰的错误提示：

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "a"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "hello"
    }
  ]
}
```

**你没有写任何校验代码**，只是声明了 `a: int`，FastAPI 就自动帮你校验了。这就是类型提示驱动的威力。

**练习 2**：创建一个返回个人信息的接口

```python
@app.get("/profile/{username}")
def get_profile(username: str, age: int = 18):
    return {
        "username": username,
        "age": age,
        "is_adult": age >= 18
    }
```

试试这些访问方式，体会路径参数和查询参数的区别：
- http://127.0.0.1:8000/profile/张三 → 使用默认 age=18
- http://127.0.0.1:8000/profile/张三?age=25 → 指定 age=25

---

## 本章小结

| 概念 | 要点 |
|------|------|
| FastAPI 是什么 | 基于 Python 类型提示的现代 API 框架 |
| 技术栈 | FastAPI = Starlette（Web）+ Pydantic（数据） |
| 核心优势 | 高性能、开发快、自动校验、自动文档 |
| 启动命令 | `fastapi dev main.py` |
| 自动文档 | `/docs`（Swagger UI）、`/redoc`（ReDoc） |
| 核心理念 | 用类型提示描述接口，框架自动处理其余一切 |

**下一章预告**：我们将深入路由系统，学习路径参数、查询参数、请求体的完整用法，并实现一个 Todo CRUD 接口。
