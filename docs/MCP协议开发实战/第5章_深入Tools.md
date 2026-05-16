# MCP 协议开发实战

> 从零构建你的第一个 MCP Server，让 AI 成为万能工具人。

---

## 5. 深入 Tools —— 参数校验、异步、错误处理

上一章我们用 `@mcp.tool()` 写了第一个工具。但那只是入门——实际项目中，你需要处理更复杂的参数、调用异步 API、优雅地处理错误。

这一章，我们把 Tool 的每个细节都吃透。

---

### 5.1 @mcp.tool 装饰器全解析

`@mcp.tool()` 是 FastMCP 的核心装饰器。它把一个普通的 Python 函数变成 MCP Tool。但它到底做了哪些"魔法"？

### 自动提取机制

```
FastMCP 从你的函数中自动提取 4 样东西：

  ┌──────────────────────────────────────────────┐
  │  @mcp.tool()                                  │
  │  def search_users(name: str, age: int) -> str │
  │      """根据姓名和年龄搜索用户。              │
  │                                                │
  │      Args:                                     │
  │          name: 用户姓名（支持模糊搜索）        │
  │          age: 用户年龄                         │
  │      """                                       │
  └──────────────────────────────────────────────┘
       │           │             │            │
       ↓           ↓             ↓            ↓
  工具名称     参数 Schema    工具描述      参数描述
  search_     name: string  "根据姓名和   name: "用户
  users       age: integer  年龄搜索用户"  姓名..."
```

**提取规则详解：**

| 来源 | 提取内容 | 生成协议字段 |
|------|----------|-------------|
| 函数名 `search_users` | 工具名称 | `name: "search_users"` |
| docstring 第一行 | 工具描述 | `description: "根据姓名和年龄搜索用户"` |
| 类型注解 `name: str` | 参数 JSON Schema | `{"type": "string"}` |
| docstring Args 部分 | 参数描述 | `"description": "用户姓名（支持模糊搜索）"` |

### 装饰器的可选参数

`@mcp.tool()` 接受几个可选参数，让你覆盖自动提取的值：

```python
# 默认行为：名称和描述从函数自动提取
@mcp.tool()
def my_tool(x: str) -> str:
    """这是工具描述"""
    ...

# 自定义名称和描述
@mcp.tool(
    name="custom_tool_name",        # 覆盖工具名称
    description="自定义的工具描述",   # 覆盖描述
)
def my_tool(x: str) -> str:
    ...
```

```
什么时候需要手动指定 name？

  ① 函数名不适合做工具名
     → 函数名有下划线前缀（_internal_func）
     → 函数名太长或太技术化

  ② 多个函数冲突
     → 两个模块都有 search() 函数
     → 用 name 参数区分

  大多数情况下，直接用函数名就好——简单、可读、一致。
```

### 返回值类型

Tool 函数可以返回多种类型，FastMCP 会自动转换为 MCP 协议格式：

```python
# ① 返回字符串 → 自动包装为 TextContent
@mcp.tool()
def simple_tool() -> str:
    return "Hello, MCP!"
# 协议层：{"content": [{"type": "text", "text": "Hello, MCP!"}]}

# ② 返回列表 → 多个 Content 项
@mcp.tool()
def multi_content() -> list:
    return [
        "第一段文字",
        "第二段文字",
    ]

# ③ 返回字典 → 自动序列化为 JSON 字符串
@mcp.tool()
def dict_tool() -> dict:
    return {"status": "ok", "count": 42}
# 协议层：{"content": [{"type": "text", "text": "{\"status\": \"ok\", \"count\": 42}"}]}
```

> **最佳实践**：大多数 Tool 返回 `str` 就够了。如果你要返回结构化数据，返回格式化好的文本比返回 JSON 更好——因为 AI 模型更擅长理解自然语言，而不是解析 JSON。

---

### 5.2 参数校验与类型安全

上一章的天气工具参数很简单——一个 `city: str` 就够了。但真实项目中，参数可能更复杂：有可选参数、有枚举值、有嵌套对象……

FastMCP 结合 Python 类型注解和 Pydantic，提供了强大的参数校验能力。

### 基础类型映射

Python 类型注解会被自动转换为 JSON Schema：

| Python 类型 | JSON Schema | 示例值 |
|------------|-------------|--------|
| `str` | `{"type": "string"}` | `"hello"` |
| `int` | `{"type": "integer"}` | `42` |
| `float` | `{"type": "number"}` | `3.14` |
| `bool` | `{"type": "boolean"}` | `true` |
| `list[str]` | `{"type": "array", "items": {"type": "string"}}` | `["a", "b"]` |
| `dict` | `{"type": "object"}` | `{"key": "val"}` |

```python
@mcp.tool()
def create_task(
    title: str,          # 必填，字符串
    priority: int,       # 必填，整数
    score: float,        # 必填，浮点数
    is_urgent: bool,     # 必填，布尔值
    tags: list[str],     # 必填，字符串数组
) -> str:
    """创建一个新任务。"""
    ...
```

### 可选参数与默认值

用 Python 的默认值来标记可选参数：

```python
@mcp.tool()
def search_logs(
    keyword: str,                    # 必填
    max_results: int = 10,           # 可选，默认 10
    level: str = "INFO",             # 可选，默认 "INFO"
    include_stack_trace: bool = False # 可选，默认 False
) -> str:
    """搜索系统日志。

    Args:
        keyword: 搜索关键词
        max_results: 最多返回条数，默认 10
        level: 日志级别过滤（DEBUG/INFO/WARNING/ERROR）
        include_stack_trace: 是否包含错误堆栈，默认不包含
    """
    ...
```

```
生成的 JSON Schema：

  required: ["keyword"]     ← 只有 keyword 是必填的
  properties:
    keyword:       {type: string}
    max_results:   {type: integer, default: 10}
    level:         {type: string,  default: "INFO"}
    include_stack_trace: {type: boolean, default: false}
```

> **提醒**：AI 模型会看到 `default` 值和 `description`，所以它知道哪些参数可以省略。一个好的默认值可以让 AI 在大多数场景下不需要额外问用户。

### 用 Enum 约束参数值

当参数只有几个合法值时，用 `Literal` 或 `Enum`：

```python
from typing import Literal

@mcp.tool()
def format_code(
    code: str,
    language: Literal["python", "javascript", "typescript", "go", "rust"],
    style: Literal["compact", "readable"] = "readable"
) -> str:
    """格式化代码。

    Args:
        code: 要格式化的代码
        language: 编程语言
        style: 格式化风格
    """
    ...
```

```
Literal 的效果：

  JSON Schema 中会生成 enum 字段：
  language: {type: string, enum: ["python", "javascript", ...]}

  AI 模型看到 enum 后：
  ✅ 只会从合法值中选择，不会瞎编
  ✅ 减少参数错误
  ✅ 用户体验更好
```

### 用 Pydantic 定义复杂参数

当参数是嵌套对象时，用 Pydantic BaseModel：

```python
from pydantic import BaseModel, Field

class DatabaseQuery(BaseModel):
    """数据库查询参数"""
    table: str = Field(description="要查询的表名")
    columns: list[str] = Field(
        default=["*"],
        description="要查询的列名列表，默认查询所有列"
    )
    where: str | None = Field(
        default=None,
        description="WHERE 条件，如 'age > 18 AND city = \"北京\"'"
    )
    limit: int = Field(
        default=100,
        description="最多返回行数",
        ge=1,        # 最小值 1
        le=1000      # 最大值 1000
    )
    order_by: str | None = Field(
        default=None,
        description="排序字段，如 'created_at DESC'"
    )

@mcp.tool()
def query_database(query: DatabaseQuery) -> str:
    """执行数据库查询。"""
    # query.table, query.columns 等已经过类型校验
    ...
```

```
Pydantic 带来的好处：

  ① 自动类型校验
     → limit 必须是 1~1000 之间的整数
     → 传入 limit: -1 会自动报错，不需要你手写校验

  ② 丰富的 JSON Schema
     → Field(description=...) 生成参数描述
     → Field(ge=1, le=1000) 生成 minimum/maximum 约束
     → AI 能看到这些约束，就不会传离谱的值

  ③ 嵌套对象
     → 复杂参数结构清晰，代码可读性好
     → 比起一堆 str/int 平铺参数，组织更合理
```

### description 写作指南

参数描述直接影响 AI 的调用质量。几个实用技巧：

```
✅ 好的 description：

  city: "城市名称，如 '北京'、'上海'。支持国内主要城市"
  → 给了示例值，AI 知道格式
  → 说明了范围，AI 不会传入奇怪的值

  sql: "SQLite SQL 语句，只支持 SELECT 查询，不允许 INSERT/UPDATE/DELETE"
  → 明确了限制，AI 会遵守

  date: "日期字符串，格式 YYYY-MM-DD，如 '2025-04-01'"
  → 给了精确的格式要求

❌ 差的 description：

  city: "城市"          → 太模糊，哪个城市？什么格式？
  sql: "SQL"            → 什么类型的 SQL？有啥限制？
  date: "日期"          → 什么格式？'4月1日' 行不行？
```

> **经验法则**：写 description 时，想象你在教一个聪明但对你的系统一无所知的实习生——他需要示例、格式说明、和边界限制。

---

### 5.3 异步工具与错误处理

真实世界的工具往往需要调用外部 API、查询数据库、读写文件——这些都是 I/O 操作，用异步可以避免阻塞。同时，这些操作随时可能失败，所以错误处理也很关键。

### 异步工具

把 `def` 换成 `async def`，就变成了异步工具：

```python
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("异步工具示例")

@mcp.tool()
async def fetch_github_repo(owner: str, repo: str) -> str:
    """查询 GitHub 仓库信息。

    Args:
        owner: 仓库所有者，如 'anthropics'
        repo: 仓库名称，如 'mcp'
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}"
        )
        data = response.json()

    return (
        f"📦 {data['full_name']}\n"
        f"⭐ Stars: {data['stargazers_count']}\n"
        f"🍴 Forks: {data['forks_count']}\n"
        f"📝 描述: {data.get('description', '无')}"
    )
```

### 什么时候用 async

```
选择 def 还是 async def：

  同步（def）适合：
    ✅ 纯计算（字符串处理、数学运算）
    ✅ 内存中的数据查询
    ✅ 不涉及任何外部调用

  异步（async def）适合：
    ✅ HTTP API 调用（httpx、aiohttp）
    ✅ 数据库查询（aiosqlite、asyncpg）
    ✅ 文件读写（aiofiles）
    ✅ 任何可能耗时的 I/O 操作

  经验法则：
    → 如果你需要 import requests → 用 async + httpx
    → 如果你需要 import sqlite3 → 用 async + aiosqlite
    → 如果不确定 → 用 async，不会错
```

> **注意**：FastMCP 同时支持同步和异步工具，可以混用。你不需要把所有工具都改成 async——按需选择即可。

### 错误处理

Tool 的错误处理有三种模式，从简单到完善：

**模式一：返回错误信息（最简单）**

```python
@mcp.tool()
def read_file(path: str) -> str:
    """读取文件内容。"""
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"❌ 文件不存在：{path}"
    except PermissionError:
        return f"❌ 没有权限读取：{path}"
```

这种方式可以工作，但 AI 模型不知道这是"成功"还是"失败"——它只看到一段文本。

**模式二：抛出异常（推荐）**

```python
from mcp.server.fastmcp import FastMCP
from mcp.types import McpError, ErrorCode

@mcp.tool()
def divide(a: float, b: float) -> str:
    """计算 a 除以 b 的结果。"""
    if b == 0:
        raise McpError(
            ErrorCode.InvalidParams,
            "除数不能为零"
        )
    return f"{a} ÷ {b} = {a / b:.4f}"
```

```
raise McpError 的效果：

  协议层返回 error response（而不是 result）：
  {
    "error": {
      "code": -32602,
      "message": "除数不能为零"
    }
  }

  AI 模型收到后：
  → 明确知道这次调用失败了
  → 会尝试修正参数重试，或告诉用户出了什么问题

常用的 ErrorCode：
  ErrorCode.InvalidParams    → 参数有误（最常用）
  ErrorCode.InternalError    → 服务器内部错误
  ErrorCode.MethodNotFound   → 方法不存在
```

**模式三：返回 isError 标记（精细控制）**

```python
from mcp.types import TextContent, CallToolResult

@mcp.tool()
def risky_operation(action: str) -> CallToolResult:
    """执行一个可能失败的操作。"""
    try:
        result = do_something(action)
        return CallToolResult(
            content=[TextContent(type="text", text=f"✅ 成功：{result}")],
            isError=False
        )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"❌ 失败：{str(e)}")],
            isError=True  # 告诉 AI "这是个错误结果"
        )
```

```
三种错误处理方式的对比：

  模式一（返回字符串）：
    简单 ✅  AI 能区分成功/失败 ❌  适合：简单工具

  模式二（raise McpError）：
    简洁 ✅  AI 能区分 ✅  适合：大多数场景（推荐）

  模式三（CallToolResult）：
    灵活 ✅  AI 能区分 ✅  适合：需要精细控制返回内容的场景
```

### 使用 Context 对象

FastMCP 提供了一个 `Context` 对象，让你在工具函数中访问日志、进度报告等功能：

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("上下文示例")

@mcp.tool()
async def long_running_task(
    steps: int,
    ctx: Context      # 加上 ctx 参数，FastMCP 自动注入
) -> str:
    """执行一个耗时任务。

    Args:
        steps: 任务步骤数
    """
    for i in range(steps):
        # 记录日志（输出到 stderr，不干扰 STDIO 通信）
        ctx.info(f"正在执行步骤 {i+1}/{steps}")

        # 报告进度（Host 可以展示进度条）
        await ctx.report_progress(i + 1, steps)

        # 模拟耗时操作
        await asyncio.sleep(1)

    return f"✅ 任务完成！共执行了 {steps} 个步骤"
```

```
Context 提供的能力：

  ctx.info(msg)              → 记录 INFO 级别日志
  ctx.debug(msg)             → 记录 DEBUG 级别日志
  ctx.warning(msg)           → 记录 WARNING 级别日志
  ctx.error(msg)             → 记录 ERROR 级别日志
  await ctx.report_progress  → 报告进度（current, total）
  ctx.request_id             → 当前请求的 ID
```

> **注意**：`ctx` 参数不会出现在生成的 JSON Schema 中——FastMCP 知道这是框架注入的，不是用户传入的。AI 模型看不到这个参数。

---

### 5.4 实战：数据库查询工具

学了装饰器、参数校验、异步、错误处理，现在把它们全部用上——构建一个实用的 **SQLite 数据库查询 MCP Server**。

### 完整代码

```python
# db_server.py —— SQLite 数据库查询 MCP Server
import aiosqlite
from typing import Literal
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("数据库助手")

# 数据库路径（修改为你的实际路径）
DB_PATH = "demo.db"

@mcp.tool()
async def list_tables(ctx: Context) -> str:
    """列出数据库中所有表名及其行数。"""
    ctx.info("正在查询数据库表信息...")

    async with aiosqlite.connect(DB_PATH) as db:
        # 获取所有表名
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = await cursor.fetchall()

        if not tables:
            return "数据库中没有任何表"

        # 获取每个表的行数
        result = "📊 数据库表列表：\n\n"
        for (table_name,) in tables:
            cursor = await db.execute(
                f"SELECT COUNT(*) FROM [{table_name}]"
            )
            (count,) = await cursor.fetchone()
            result += f"  • {table_name}（{count} 行）\n"

    return result

@mcp.tool()
async def describe_table(table_name: str, ctx: Context) -> str:
    """查看表的结构（列名、类型）。

    Args:
        table_name: 要查看的表名
    """
    ctx.info(f"正在查询表结构：{table_name}")

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(f"PRAGMA table_info([{table_name}])")
        columns = await cursor.fetchall()

        if not columns:
            return f"❌ 表 '{table_name}' 不存在"

        result = f"📋 表 {table_name} 的结构：\n\n"
        result += f"{'列名':<20} {'类型':<15} {'可空':<8} {'默认值':<10}\n"
        result += "─" * 55 + "\n"

        for col in columns:
            # col: (cid, name, type, notnull, default, pk)
            name = col[1]
            col_type = col[2] or "TEXT"
            nullable = "否" if col[3] else "是"
            default = str(col[4]) if col[4] is not None else "-"
            pk = " 🔑" if col[5] else ""
            result += f"{name:<20} {col_type:<15} {nullable:<8} {default:<10}{pk}\n"

    return result

@mcp.tool()
async def query_data(
    sql: str,
    limit: int = 50,
    ctx: Context = None
) -> str:
    """执行 SELECT 查询并返回结果。

    Args:
        sql: SELECT SQL 语句。只允许 SELECT 查询，禁止 INSERT/UPDATE/DELETE
        limit: 最大返回行数，默认 50，最大 500
    """
    # 安全校验：只允许 SELECT
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        return "❌ 安全限制：只允许 SELECT 查询。禁止 INSERT、UPDATE、DELETE 等操作。"

    # 限制返回行数
    limit = min(limit, 500)
    if "LIMIT" not in sql_upper:
        sql = f"{sql.rstrip(';')} LIMIT {limit}"

    if ctx:
        ctx.info(f"执行查询：{sql}")

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql)
            rows = await cursor.fetchall()

            if not rows:
                return "查询结果为空（0 行）"

            # 获取列名
            columns = [desc[0] for desc in cursor.description]

            # 格式化输出
            result = f"查询结果（{len(rows)} 行）：\n\n"

            # 表头
            header = " | ".join(f"{col:<15}" for col in columns)
            result += header + "\n"
            result += "─" * len(header) + "\n"

            # 数据行
            for row in rows:
                row_str = " | ".join(
                    f"{str(row[col]):<15}" for col in columns
                )
                result += row_str + "\n"

            return result

    except Exception as e:
        return f"❌ 查询失败：{str(e)}"

if __name__ == "__main__":
    mcp.run()
```

### 创建测试数据库

在运行 Server 之前，先创建一个测试数据库：

```python
# create_demo_db.py —— 创建测试数据
import sqlite3

conn = sqlite3.connect("demo.db")
c = conn.cursor()

# 创建用户表
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER,
        city TEXT,
        email TEXT
    )
""")

# 插入测试数据
users = [
    ("张三", 28, "北京", "zhangsan@example.com"),
    ("李四", 35, "上海", "lisi@example.com"),
    ("王五", 22, "广州", "wangwu@example.com"),
    ("赵六", 31, "深圳", "zhaoliu@example.com"),
    ("孙七", 26, "杭州", "sunqi@example.com"),
]
c.executemany(
    "INSERT INTO users (name, age, city, email) VALUES (?, ?, ?, ?)",
    users
)

conn.commit()
conn.close()
print("✅ 测试数据库创建完成！")
```

```bash
# 先创建测试数据
python3 create_demo_db.py

# 用 Inspector 测试
npx @modelcontextprotocol/inspector uv run db_server.py
```

### Tool 调用的完整生命周期

回顾一下，一个 Tool 从注册到被调用，经历了哪些步骤：

```
Tool 的完整生命周期：

  ① 注册阶段（Server 启动时）
     @mcp.tool() →
       → 解析函数签名和 docstring
       → 生成 Tool 定义（name, description, inputSchema）
       → 注册到 Server 的工具列表中

  ② 发现阶段（Client 连接后）
     Client 发送 tools/list →
       → Server 返回所有注册的 Tool 定义
       → Host 把工具信息告诉 AI 模型
       → AI 模型记住"我有哪些工具可以用"

  ③ 调用阶段（用户提问后）
     用户："查一下数据库里有哪些表" →
       → AI 分析后决定调用 list_tables
       → Host 通过 Client 发送 tools/call
       → Server 收到请求

  ④ 执行阶段（Server 内部）
     → FastMCP 解析参数并校验类型
     → 校验失败 → 返回 error
     → 校验通过 → 调用你的函数
     → 函数执行完毕 → 返回结果

  ⑤ 返回阶段
     → FastMCP 把返回值包装成协议格式
     → Server → Client → Host → AI 模型
     → AI 模型生成自然语言回复
     → 用户看到答案 ✅
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| @mcp.tool() | 自动提取函数名→名称、docstring→描述、类型注解→Schema |
| 可选参数 | 覆盖 name/description |
| 类型映射 | str→string、int→integer、float→number、bool→boolean |
| 可选参数 | 用默认值标记，非必填参数会有 default |
| Literal | 约束参数为枚举值，AI 不会瞎编 |
| Pydantic | 复杂参数用 BaseModel + Field，自动校验 |
| async 工具 | async def + await，用于 I/O 操作 |
| 错误处理 | 推荐 raise McpError，AI 能区分成功/失败 |
| Context | ctx.info() 记录日志、report_progress 报告进度 |
| description | 写得好 AI 就用得好——给示例、给格式、给限制 |

> **下一章预告**：深入 Resources —— 文件、数据库、API 数据源。我们将学习 @mcp.resource 的用法，实现静态 Resource 和 Resource 模板，暴露本地文件系统和 SQLite 数据表。

