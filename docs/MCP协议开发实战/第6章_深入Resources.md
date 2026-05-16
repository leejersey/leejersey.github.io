# MCP 协议开发实战

> 从零构建你的第一个 MCP Server，让 AI 成为万能工具人。

---

## 6. 深入 Resources —— 文件、数据库、API 数据源

第 3 章我们说过：Resource 是 AI 的"眼睛"，让 AI 看到外部数据。第 5 章的数据库工具已经让 AI 能"查数据"了，但那是通过 Tool 主动查询——Resource 的方式不同，它是**把数据摆在那里，等 AI 或应用来取**。

这一章，我们深入 `@mcp.resource` 的所有用法。

---

### 6.1 Resource 定义与 URI 规范

### @mcp.resource 装饰器

用 `@mcp.resource()` 定义一个 Resource，核心要素是 **URI**：

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("资源示例")

@mcp.resource("config://app/settings")
def get_app_settings() -> str:
    """应用程序的配置信息"""
    return """
    {
        "app_name": "My MCP Server",
        "version": "1.0.0",
        "debug": false,
        "max_connections": 100
    }
    """
```

```
对比 @mcp.tool() 和 @mcp.resource()：

  @mcp.tool()
    → 不需要参数（名称从函数名自动提取）
    → 有 inputSchema（接受参数）
    → AI 主动调用

  @mcp.resource("config://app/settings")
    → 必须指定 URI（这是 Resource 的唯一标识）
    → 没有 inputSchema（不接受参数，除非用模板）
    → 应用程序或用户选择加载
```

### 自动提取机制

和 Tool 类似，FastMCP 也会从 Resource 函数中提取元数据：

| 来源 | 提取内容 | 协议字段 |
|------|----------|---------|
| 装饰器参数 `"config://app/settings"` | Resource URI | `uri` |
| 函数名 `get_app_settings` | Resource 名称 | `name` |
| docstring 第一行 | 描述 | `description` |
| 返回值类型 | MIME 类型推断 | `mimeType` |

你也可以手动覆盖名称、描述和 MIME 类型：

```python
@mcp.resource(
    "data://reports/daily",
    name="每日报告",
    description="今日的系统运行数据报告",
    mime_type="application/json"
)
def daily_report() -> str:
    ...
```

### URI 设计原则

URI 是 Resource 的"地址"，设计得好坏直接影响可用性：

```
URI 设计最佳实践：

  ① 使用有意义的协议前缀
     ✅ file:///project/src/main.py    → 明确是文件
     ✅ db://myapp/users               → 明确是数据库
     ✅ config://app/settings           → 明确是配置
     ❌ resource://abc123               → 看不出是什么

  ② 路径层级清晰
     ✅ db://myapp/tables/users         → 数据库 / 表
     ✅ log://server/2025/04/01         → 日志 / 年 / 月 / 日
     ❌ db://users_table_data           → 扁平，不好扩展

  ③ 保持一致性
     ✅ 同一个 Server 内所有 Resource 用相同的 URI 风格
     ❌ 混用 file://、File://、FILE://
```

### 返回值类型

Resource 函数可以返回文本或二进制数据：

```python
# ① 返回文本（最常见）
@mcp.resource("file:///config.json")
def get_config() -> str:
    """应用配置文件"""
    with open("config.json", "r") as f:
        return f.read()

# ② 返回二进制数据（图片、PDF 等）
@mcp.resource("file:///logo.png")
def get_logo() -> bytes:
    """应用 Logo"""
    with open("logo.png", "rb") as f:
        return f.read()
# 协议层：返回 base64 编码的 blob
```

```
返回值规则：

  返回 str   → 协议层生成 text 字段
  返回 bytes → 协议层生成 blob 字段（base64 编码）

  大多数场景用 str 就够了——代码、文档、JSON、日志都是文本。
  只有图片、PDF、二进制文件才需要返回 bytes。
```

> **注意**：Resource 的返回值会被完整地传给 AI 模型。所以不要把几 MB 的大文件作为 Resource——AI 的上下文窗口是有限的。如果数据量大，应该用 Tool + 分页查询的方式。

---

### 6.2 静态 Resource vs Resource 模板

MCP 支持两种 Resource：**静态 Resource**（固定 URI）和 **Resource 模板**（参数化 URI）。理解两者的区别，是正确使用 Resource 的关键。

### 静态 Resource

静态 Resource 的 URI 是固定的，在 `resources/list` 中直接列出：

```python
mcp = FastMCP("静态资源示例")

# 静态 Resource：URI 固定，数据可以是动态的
@mcp.resource("config://app/settings")
def app_settings() -> str:
    """当前应用配置"""
    return json.dumps({
        "version": "1.0.0",
        "debug": True,
        "database": "sqlite:///app.db"
    }, indent=2, ensure_ascii=False)

@mcp.resource("status://server/health")
def server_health() -> str:
    """服务器健康状态"""
    return json.dumps({
        "status": "healthy",
        "uptime": "3 days 12 hours",
        "memory_usage": "256MB",
        "cpu_load": "15%"
    }, indent=2, ensure_ascii=False)

@mcp.resource("doc://readme")
def readme() -> str:
    """项目 README 文档"""
    with open("README.md", "r") as f:
        return f.read()
```

```
静态 Resource 的特征：

  ① URI 在 Server 启动时就确定了
     → config://app/settings 永远是这个地址

  ② 数据可以是动态的
     → 每次读取时重新执行函数，拿到最新数据
     → URI 固定 ≠ 数据固定

  ③ 在 resources/list 中直接列出
     → Client 一调 resources/list 就能看到所有静态 Resource
     → AI 和用户知道有哪些资源可用

  适用场景：
     ✅ 已知的、有限的资源（配置、README、系统状态）
     ✅ 资源数量不多（几个到几十个）
```

### Resource 模板

当资源数量太多或是动态的，就需要 Resource 模板——URI 中带 `{参数}`：

```python
mcp = FastMCP("模板资源示例")

# Resource 模板：URI 中的 {filename} 是参数
@mcp.resource("file://project/src/{filename}")
def source_file(filename: str) -> str:
    """项目源代码文件

    Args:
        filename: 文件名，如 'main.py'、'utils.py'
    """
    filepath = f"./src/{filename}"
    try:
        with open(filepath, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"文件不存在：{filepath}"

# 另一个模板：用户数据
@mcp.resource("db://myapp/users/{user_id}")
def user_data(user_id: str) -> str:
    """指定用户的详细信息

    Args:
        user_id: 用户 ID
    """
    # 查询数据库...
    user = get_user_by_id(user_id)
    return json.dumps(user, ensure_ascii=False, indent=2)

# 日志查询模板
@mcp.resource("log://server/{date}")
def server_log(date: str) -> str:
    """指定日期的服务器日志

    Args:
        date: 日期字符串，格式 YYYY-MM-DD
    """
    log_path = f"./logs/{date}.log"
    try:
        with open(log_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"没有找到 {date} 的日志文件"
```

```
Resource 模板的特征：

  ① URI 中有 {参数}
     → "file://project/src/{filename}" 中的 {filename} 是变量
     → 客户端需要填入具体值：file://project/src/main.py

  ② 在 resources/templates/list 中列出（不是 resources/list）
     → Client 知道有这个模板，但不知道具体有哪些实例
     → 需要用具体的 URI 去 resources/read

  ③ 函数参数与 URI 参数对应
     → {filename} → 函数参数 filename: str
     → FastMCP 自动解析 URI 中的值并传入函数

  适用场景：
     ✅ 大量动态资源（任意文件、任意用户、任意日期的日志）
     ✅ 资源数量不确定或很多
```

### 两者的对比

| 维度 | 静态 Resource | Resource 模板 |
|------|-------------|--------------|
| URI | 固定值 | 含 `{参数}` |
| 列出方式 | `resources/list` | `resources/templates/list` |
| 资源数量 | 已知、有限 | 动态、大量 |
| 参数 | 无 | 有（从 URI 提取） |
| 类比 | 书架上摆好的书 | 图书馆搜索系统 |
| 适合 | 配置、README、状态 | 文件系统、数据库记录、日志 |

### 变更通知

当 Resource 的数据发生变化时，Server 可以通知 Client：

```python
# 在某个事件触发时，通知 Client 资源已更新
async def on_config_changed():
    """配置文件被修改时调用"""
    await mcp.notification(
        "notifications/resources/updated",
        {"uri": "config://app/settings"}
    )
    # Client 收到通知后，可以重新读取这个 Resource
```

```
变更通知的工作流程：

  ① Resource 数据发生变化
     → 比如配置文件被手动修改了

  ② Server 发送 Notification
     → notifications/resources/updated
     → 告诉 Client："config://app/settings 变了"

  ③ Client 决定是否重新读取
     → Client 可以选择立即 resources/read 获取最新数据
     → 也可以忽略通知

  注意：这是 Notification（不是 Request），不需要回复。
```

> **实际情况**：目前大多数 MCP Host（包括 Claude Desktop）对 Resource 的支持还在完善中。资源变更通知等高级特性可能尚未在所有 Host 中生效。但协议层已经定义好了，等 Host 支持跟上就能用。

---

### 6.3 实战：暴露本地文件和 SQLite 数据表

综合前面学到的知识，构建一个实用的 **文件 + 数据库 Resource Server**。这个 Server 同时暴露本地文件系统和 SQLite 数据库，并结合 Tool 实现完整的数据访问体验。

### 完整代码

```python
# resource_server.py —— 文件 + 数据库 Resource Server
import os
import json
import aiosqlite
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("数据访问助手")

# 配置
PROJECT_DIR = "./my-project"     # 项目目录（修改为你的实际路径）
DB_PATH = "./demo.db"            # 数据库文件

# ═══════════════════════════════════════════
# 静态 Resource：项目概览信息
# ═══════════════════════════════════════════

@mcp.resource("project://overview")
def project_overview() -> str:
    """项目的目录结构和基本信息"""
    result = "📁 项目目录结构：\n\n"

    for root, dirs, files in os.walk(PROJECT_DIR):
        # 跳过隐藏目录和 __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

        level = root.replace(PROJECT_DIR, '').count(os.sep)
        indent = "  " * level
        result += f"{indent}📁 {os.path.basename(root)}/\n"

        sub_indent = "  " * (level + 1)
        for file in sorted(files):
            size = os.path.getsize(os.path.join(root, file))
            result += f"{sub_indent}📄 {file} ({size} bytes)\n"

    return result

@mcp.resource("project://readme")
def project_readme() -> str:
    """项目 README 文档"""
    readme_path = os.path.join(PROJECT_DIR, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "README.md 文件不存在"

# ═══════════════════════════════════════════
# Resource 模板：读取任意源代码文件
# ═══════════════════════════════════════════

@mcp.resource("file://project/{filepath}")
def read_project_file(filepath: str) -> str:
    """读取项目中的指定文件

    Args:
        filepath: 相对于项目根目录的文件路径，如 'src/main.py'
    """
    full_path = os.path.join(PROJECT_DIR, filepath)

    # 安全检查：防止路径穿越攻击
    real_path = os.path.realpath(full_path)
    real_project = os.path.realpath(PROJECT_DIR)
    if not real_path.startswith(real_project):
        return "❌ 安全限制：不能访问项目目录之外的文件"

    if not os.path.exists(full_path):
        return f"❌ 文件不存在：{filepath}"

    if not os.path.isfile(full_path):
        return f"❌ {filepath} 是目录，不是文件"

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        return f"❌ {filepath} 不是文本文件，无法读取"

# ═══════════════════════════════════════════
# Resource 模板：数据库表数据预览
# ═══════════════════════════════════════════

@mcp.resource("db://tables/{table_name}")
async def table_preview(table_name: str) -> str:
    """预览数据库表的结构和前 20 行数据

    Args:
        table_name: 数据库中的表名
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # 检查表是否存在
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not await cursor.fetchone():
            return f"❌ 表 '{table_name}' 不存在"

        # 获取表结构
        cursor = await db.execute(f"PRAGMA table_info([{table_name}])")
        columns = await cursor.fetchall()

        result = f"📋 表 {table_name}\n\n"
        result += "字段结构：\n"
        col_names = []
        for col in columns:
            col_names.append(col[1])
            pk_mark = " 🔑" if col[5] else ""
            result += f"  • {col[1]} ({col[2] or 'TEXT'}){pk_mark}\n"

        # 获取前 20 行数据
        cursor = await db.execute(
            f"SELECT * FROM [{table_name}] LIMIT 20"
        )
        rows = await cursor.fetchall()

        result += f"\n数据预览（前 {len(rows)} 行）：\n\n"
        header = " | ".join(f"{c:<12}" for c in col_names)
        result += header + "\n"
        result += "─" * len(header) + "\n"
        for row in rows:
            row_str = " | ".join(f"{str(v):<12}" for v in row)
            result += row_str + "\n"

        return result

# ═══════════════════════════════════════════
# 静态 Resource：数据库表清单
# ═══════════════════════════════════════════

@mcp.resource("db://tables")
async def database_tables() -> str:
    """数据库中所有表的清单"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = await cursor.fetchall()

        if not tables:
            return "数据库中没有表"

        result = "📊 数据库表清单：\n\n"
        for (name,) in tables:
            cursor = await db.execute(f"SELECT COUNT(*) FROM [{name}]")
            (count,) = await cursor.fetchone()
            result += f"  • {name}（{count} 行）→ db://tables/{name}\n"

        return result

if __name__ == "__main__":
    mcp.run()
```

### Resource + Tool 组合使用

在实际项目中，Resource 和 Tool 常常配合使用：

```
Resource 和 Tool 的分工：

  Resource 负责"读"：
    → 暴露项目结构、文件内容、数据库预览
    → AI 通过 Resource 了解上下文
    → 只读，不产生副作用

  Tool 负责"写"和"计算"：
    → 执行 SQL 查询（带复杂条件）
    → 写入文件、修改数据
    → 调用外部 API

  组合模式：
    ① 用户问"项目里有什么文件？"
       → Host 加载 Resource: project://overview
       → AI 看到项目结构

    ② 用户问"帮我看看 main.py 的代码"
       → Host 加载 Resource: file://project/main.py
       → AI 看到代码内容

    ③ 用户问"数据库里年龄大于 30 的用户有哪些？"
       → AI 先通过 Resource db://tables 了解表结构
       → 再调用 Tool query_data 执行 SQL 查询
       → 返回查询结果
```

> **设计原则**：Resource 提供"概览和上下文"，Tool 执行"精确操作"。Resource 让 AI 知道有什么数据，Tool 让 AI 能对数据做事情。两者结合，AI 才能既"看得见"又"做得到"。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| @mcp.resource() | 必须指定 URI，从函数自动提取 name/description |
| 返回值 | str → text 字段，bytes → blob 字段（base64） |
| URI 设计 | 有意义的协议前缀 + 清晰的路径层级 + 一致的风格 |
| 静态 Resource | 固定 URI，在 resources/list 中列出 |
| Resource 模板 | URI 含 {参数}，在 resources/templates/list 中列出 |
| 参数提取 | {filename} → 函数参数 filename: str，自动解析 |
| 变更通知 | Server 可发 notifications/resources/updated |
| 数据量 | 不要放大文件，AI 上下文有限，大数据用 Tool 分页查 |
| 与 Tool 组合 | Resource 提供概览和上下文，Tool 执行精确操作 |

> **下一章预告**：深入 Prompts —— 可复用的提示工程。我们将学习 @mcp.prompt 的用法，构建参数化的提示模板，以及 Prompts + Tools + Resources 的组合使用模式。

