# MCP 协议开发实战

> 从零构建你的第一个 MCP Server，让 AI 成为万能工具人。

---

## 4. 环境搭建与第一个 MCP Server（Python）

前三章是理论，从这一章开始——写代码。

我们的目标：用 Python 在 5 分钟内造一个能查天气的 MCP Server，然后连上 Claude Desktop 实际对话。

---

### 4.1 安装 Python MCP SDK

### 前置要求

```
开始之前，请确认你的环境：

  ✅ Python >= 3.10（MCP SDK 最低要求）
  ✅ 一个终端（macOS Terminal / Windows PowerShell / Linux Shell）
  ✅ 一个代码编辑器（VS Code / Cursor / PyCharm 都行）

检查 Python 版本：
  $ python3 --version
  Python 3.12.0  ← 3.10 以上就行
```

### 推荐用 uv（更快更省事）

MCP 官方推荐使用 **uv**（一个极快的 Python 包管理器）来管理项目。当然，用传统的 `pip` 也完全可以。

```bash
# 方式一：用 uv（推荐）
# 安装 uv（如果还没装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建项目目录
mkdir my-mcp-server && cd my-mcp-server

# 初始化项目
uv init

# 安装 MCP SDK（自带 FastMCP 高级 API）
uv add "mcp[cli]"
```

```bash
# 方式二：用 pip
# 创建项目目录
mkdir my-mcp-server && cd my-mcp-server

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装 MCP SDK
pip install "mcp[cli]"
```

### 项目结构

安装完毕后，你的项目结构应该是这样的：

```
my-mcp-server/
├── .venv/              ← 虚拟环境（uv 或 pip 创建）
├── pyproject.toml      ← 项目配置
└── server.py           ← 你的 MCP Server 代码（马上创建）
```

### 验证安装

```bash
# 确认 mcp 包已安装
python3 -c "import mcp; print(mcp.__version__)"
# 输出类似：1.x.x

# 如果用 uv，也可以这样验证
uv run python -c "import mcp; print('MCP SDK 安装成功！')"
```

> **常见问题**：如果 `import mcp` 报错 `ModuleNotFoundError`，检查你是否在虚拟环境中。用 `which python3` 确认使用的是 `.venv` 里的 Python。

---

### 4.2 Hello MCP：5 分钟写一个天气查询 Server

环境就绪，开始写代码。

### 认识 FastMCP

MCP Python SDK 提供了两层 API：

```
底层 API（Low-Level）：
  → 手动处理 JSON-RPC 消息、管理会话
  → 灵活但繁琐，适合需要极致控制的场景

高层 API —— FastMCP（推荐）：
  → 用装饰器（@mcp.tool / @mcp.resource / @mcp.prompt）定义能力
  → 自动处理序列化、参数校验、错误处理
  → 类似 FastAPI 的开发体验："Flask 之于 HTTP = FastMCP 之于 MCP"
```

我们用 FastMCP，因为它让你专注于业务逻辑，不用操心协议细节。

### 完整代码：天气查询 Server

创建 `server.py`，写入以下代码：

```python
# server.py —— 你的第一个 MCP Server
from mcp.server.fastmcp import FastMCP

# 创建 MCP Server 实例
mcp = FastMCP("天气查询")

# 模拟天气数据（实际项目中你会调用真实的天气 API）
WEATHER_DATA = {
    "北京": {"temp": 25, "condition": "晴", "wind": "东北风3级", "humidity": "45%"},
    "上海": {"temp": 28, "condition": "多云", "wind": "东风2级", "humidity": "72%"},
    "广州": {"temp": 32, "condition": "雷阵雨", "wind": "南风4级", "humidity": "85%"},
    "深圳": {"temp": 30, "condition": "阴", "wind": "西南风2级", "humidity": "78%"},
    "杭州": {"temp": 26, "condition": "晴转多云", "wind": "东风1级", "humidity": "60%"},
}

@mcp.tool()
def get_weather(city: str) -> str:
    """查询指定城市的当前天气信息。

    Args:
        city: 城市名称，如 "北京"、"上海"、"广州"
    """
    weather = WEATHER_DATA.get(city)
    if not weather:
        available = "、".join(WEATHER_DATA.keys())
        return f"暂不支持查询 {city} 的天气。目前支持的城市：{available}"

    return (
        f"🌍 {city} 当前天气：\n"
        f"🌡️ 温度：{weather['temp']}°C\n"
        f"⛅ 天气：{weather['condition']}\n"
        f"💨 风力：{weather['wind']}\n"
        f"💧 湿度：{weather['humidity']}"
    )

@mcp.tool()
def compare_weather(city1: str, city2: str) -> str:
    """对比两个城市的天气情况。

    Args:
        city1: 第一个城市名称
        city2: 第二个城市名称
    """
    w1 = WEATHER_DATA.get(city1)
    w2 = WEATHER_DATA.get(city2)

    if not w1:
        return f"暂不支持查询 {city1} 的天气"
    if not w2:
        return f"暂不支持查询 {city2} 的天气"

    return (
        f"📊 {city1} vs {city2} 天气对比：\n\n"
        f"{'指标':<6} {'  ' + city1:<10} {'  ' + city2:<10}\n"
        f"{'─' * 30}\n"
        f"{'温度':<6} {'  ' + str(w1['temp']) + '°C':<10} {'  ' + str(w2['temp']) + '°C':<10}\n"
        f"{'天气':<6} {'  ' + w1['condition']:<10} {'  ' + w2['condition']:<10}\n"
        f"{'湿度':<6} {'  ' + w1['humidity']:<10} {'  ' + w2['humidity']:<10}\n"
    )

if __name__ == "__main__":
    mcp.run()
```

### 代码逐行解析

```
第 1 行：from mcp.server.fastmcp import FastMCP
  → 导入 FastMCP 高层 API

第 4 行：mcp = FastMCP("天气查询")
  → 创建 Server 实例，"天气查询" 是 Server 名称
  → 这个名称会在 Host 端显示，帮助用户识别

第 18 行：@mcp.tool()
  → 装饰器，把函数注册为一个 MCP Tool
  → FastMCP 会自动从函数签名和 docstring 中提取：
    - 工具名称 → 函数名（get_weather）
    - 工具描述 → docstring 第一行
    - 参数 schema → 函数参数的类型注解（city: str）
    - 参数描述 → docstring 中的 Args 部分

第 19 行：def get_weather(city: str) -> str
  → 类型注解很重要！FastMCP 用它来生成 JSON Schema
  → city: str 会被转换为 {"type": "string"}
  → 返回值类型不影响协议，但有利于代码可读性

最后：mcp.run()
  → 默认以 STDIO Transport 启动
  → Server 进入等待状态，等 Client 发消息
```

### 运行你的 Server

```bash
# 用 uv 运行
uv run server.py

# 或用 python 直接运行
python3 server.py
```

运行后你会发现终端**没有任何输出**——这是正常的！STDIO 模式下，Server 在等待 stdin 输入，它不会主动打印任何东西。

```
运行后的状态：

  Server 进程（等待中）
      │
      │  stdin ← 等待客户端发来 JSON-RPC 消息
      │  stdout → 准备好回复消息
      │
      ↓
  你看到的：光标在闪，什么都没输出
  这是正常的！下一步我们用 MCP Inspector 来测试它
```

> **注意**：按 `Ctrl+C` 可以停止 Server。现在先停掉它，我们用更方便的方式来测试。

---

### 4.3 用 MCP Inspector 调试

Server 写好了，但怎么知道它是不是真的能工作？MCP 官方提供了一个可视化调试工具：**MCP Inspector**。

### 什么是 MCP Inspector

```
MCP Inspector 是什么：

  ✅ 一个 Web UI 调试工具
  ✅ 充当 MCP Client 的角色，连上你的 Server
  ✅ 可以查看 Server 暴露的所有 Tool / Resource / Prompt
  ✅ 可以手动调用工具、查看返回结果
  ✅ 类似 Postman 之于 REST API = MCP Inspector 之于 MCP Server
```

### 启动 Inspector

```bash
# 方式一：用 npx 直接启动（推荐）
npx @modelcontextprotocol/inspector uv run server.py

# 方式二：如果你用 pip 安装的
npx @modelcontextprotocol/inspector python3 server.py

# 方式三：用 mcp CLI（MCP SDK 自带）
mcp dev server.py
```

启动后，终端会输出类似信息：

```
Starting MCP Inspector...
⚡ Proxy server started on http://localhost:6277
🔍 Inspector UI:  http://localhost:6274
🔗 Connected to MCP server: 天气查询
```

**打开浏览器**，访问 `http://localhost:6274`，你就能看到 Inspector 的界面了。

### 使用 Inspector 测试

```
Inspector 界面布局：

  ┌────────────────────────────────────────────┐
  │  MCP Inspector                              │
  ├─────────────┬──────────────────────────────┤
  │             │                              │
  │  左侧面板    │        右侧面板              │
  │             │                              │
  │  📋 Tools   │  工具名称：get_weather       │
  │  • get_     │  ─────────────────────        │
  │    weather  │  参数：                       │
  │  • compare_ │  ┌──────────────────┐        │
  │    weather  │  │ city: [北京     ] │        │
  │             │  └──────────────────┘        │
  │  📄 Resour  │                              │
  │  (暂无)     │  [▶ 调用] [清除]             │
  │             │                              │
  │  💬 Prompt  │  返回结果：                   │
  │  (暂无)     │  🌍 北京 当前天气：           │
  │             │  🌡️ 温度：25°C               │
  │             │  ⛅ 天气：晴                  │
  │             │  💨 风力：东北风3级            │
  │             │  💧 湿度：45%                 │
  │             │                              │
  └─────────────┴──────────────────────────────┘
```

**操作步骤：**

1. 在左侧点击 **Tools** 标签
2. 你会看到 `get_weather` 和 `compare_weather` 两个工具
3. 点击 `get_weather`，右侧出现参数输入框
4. 在 `city` 输入框填入 `北京`
5. 点击 **调用（Call Tool）** 按钮
6. 下方显示返回结果——天气信息 ✅

试试 `compare_weather`，输入 `city1: 北京`、`city2: 上海`，看看对比结果。

### 调试技巧

```
Inspector 调试常用操作：

  ① 查看工具描述
     → 点击工具名称，右侧会显示 description 和 inputSchema
     → 确认 AI 看到的描述是否准确

  ② 测试边界情况
     → 输入不存在的城市名试试，看错误处理是否友好
     → 输入空字符串、特殊字符，检查健壮性

  ③ 查看原始 JSON
     → Inspector 底部有 "Raw JSON" 开关
     → 打开后可以看到实际的 JSON-RPC 请求和响应
     → 对照第 2 章学的协议格式，加深理解

  ④ 热重载
     → 修改 server.py 后，不需要重启 Inspector
     → 点击 Inspector 界面的 "Reconnect" 按钮即可
```

> **实操建议**：Inspector 是开发 MCP Server 的主力调试工具。在连接 Claude Desktop 之前，**务必先在 Inspector 中把所有工具测一遍**——确认参数正确、返回格式正常、错误处理到位。

---

### 4.4 连接 Claude Desktop / Cursor

Inspector 测试通过后，是时候让**真正的 AI** 来使用你的 Server 了。

### 连接 Claude Desktop

Claude Desktop 通过一个 JSON 配置文件来管理 MCP Server。

**第一步：找到配置文件**

```
配置文件位置：

  macOS：
    ~/Library/Application Support/Claude/claude_desktop_config.json

  Windows：
    %APPDATA%\Claude\claude_desktop_config.json

  如果文件不存在，手动创建即可。
```

**第二步：编辑配置文件**

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/你的项目绝对路径/my-mcp-server",
        "server.py"
      ]
    }
  }
}
```

如果你用 `python3` 而不是 `uv`：

```json
{
  "mcpServers": {
    "weather": {
      "command": "/你的项目绝对路径/my-mcp-server/.venv/bin/python3",
      "args": [
        "/你的项目绝对路径/my-mcp-server/server.py"
      ]
    }
  }
}
```

> **⚠️ 关键坑**：`command` 和 `args` 中的路径必须是**绝对路径**。用 `~` 或相对路径可能导致 Claude Desktop 找不到你的 Server。用 `pwd` 命令查看你的项目绝对路径。

**第三步：重启 Claude Desktop**

```
配置完成后：

  ① 完全退出 Claude Desktop（不是最小化，是 Cmd+Q / 右键退出）
  ② 重新打开 Claude Desktop
  ③ 在聊天输入框旁边，你会看到一个 🔧 图标
  ④ 点击 🔧 → 显示 "天气查询" Server 及其工具
  ⑤ 大功告成！
```

**第四步：实际对话**

在 Claude Desktop 中试试这些对话：

```
你：北京今天天气怎么样？

Claude：让我查询一下北京的天气信息。
       [调用工具 get_weather(city="北京")]

       🌍 北京 当前天气：
       🌡️ 温度：25°C
       ⛅ 天气：晴
       💨 风力：东北风3级
       💧 湿度：45%

       北京今天天气不错！晴天，温度25度，很适合外出。

你：帮我对比一下北京和广州的天气

Claude：[调用工具 compare_weather(city1="北京", city2="广州")]
       ...（显示对比结果）
```

### 连接 Cursor

Cursor 的 MCP 配置方式类似，也是通过 JSON 文件。

```
Cursor 的 MCP 配置文件：

  项目级配置（推荐）：
    你的项目根目录/.cursor/mcp.json

  全局配置：
    ~/.cursor/mcp.json
```

```json
// .cursor/mcp.json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/你的项目绝对路径/my-mcp-server",
        "server.py"
      ]
    }
  }
}
```

配置后重启 Cursor，在 AI 对话中就能使用你的天气查询工具了。

### 常见问题排查

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 🔧 图标没出现 | 配置文件路径错误 | 检查 JSON 文件位置和格式 |
| Server 连接失败 | command 路径不对 | 用绝对路径，确认 `uv` 或 `python3` 在 PATH 中 |
| 工具调用报错 | Server 代码有 bug | 先用 Inspector 测试通过 |
| JSON 解析错误 | 配置文件格式有误 | 检查 JSON 逗号、引号、括号 |
| 连接后没有工具 | Server 没注册 Tool | 检查 `@mcp.tool()` 装饰器是否正确 |
| 权限被拒绝 | macOS 安全限制 | 在系统偏好设置中允许 Python 执行 |

```
排查流程：

  ① JSON 格式正确吗？
     → 用 https://jsonlint.com 验证
  ② 命令能在终端直接运行吗？
     → 复制 command + args 到终端试一下
  ③ Inspector 能正常连接吗？
     → 如果 Inspector 都不行，是 Server 代码的问题
  ④ 查看 Claude Desktop 日志
     → macOS: ~/Library/Logs/Claude/
     → 搜索 "mcp" 相关错误信息
```

> **终极调试法**：如果怎么都不行，在终端直接运行 `uv run server.py`，然后手动给 stdin 发 JSON-RPC 消息试试。能走通 STDIO 通信，就是配置文件的问题；走不通，就是代码的问题。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| SDK 安装 | `uv add "mcp[cli]"` 或 `pip install "mcp[cli]"`，Python >= 3.10 |
| FastMCP | 高层 API，用装饰器定义 Tool / Resource / Prompt |
| @mcp.tool() | 把函数注册为 MCP Tool，自动提取名称、描述、参数 |
| 类型注解 | 很重要！FastMCP 用它生成 JSON Schema |
| docstring | description 来自 docstring 第一行，参数描述来自 Args 部分 |
| MCP Inspector | 可视化调试工具，`npx @modelcontextprotocol/inspector` 启动 |
| Claude Desktop | 编辑 `claude_desktop_config.json`，用绝对路径配置 |
| Cursor | 编辑 `.cursor/mcp.json`，格式与 Claude Desktop 相同 |

> **下一章预告**：深入 Tools —— 参数校验、异步、错误处理。我们将用 Pydantic 做类型校验、写异步工具函数、实现优雅的错误处理，并构建一个实用的数据库查询工具。

