# MCP 协议开发实战

> 从零构建你的第一个 MCP Server，让 AI 成为万能工具人。

---

## 2. MCP 架构解剖 —— Host、Client、Server

### 2.1 Host / Client / Server 三角关系

上一章我们说 MCP 是"AI 世界的 USB-C"。那这根"USB-C 线"的内部到底长什么样？

MCP 的架构分三层：**Host、Client、Server**。这三个角色各司其职，构成了整个协议的骨架。

```
MCP 三层架构总览：

  ┌─────────────────────────────────────────────────┐
  │                   Host（宿主）                    │
  │          Claude Desktop / Cursor / Cline         │
  │                                                   │
  │   ┌──────────┐  ┌──────────┐  ┌──────────┐      │
  │   │ Client A │  │ Client B │  │ Client C │      │
  │   └────┬─────┘  └────┬─────┘  └────┬─────┘      │
  │        │              │              │            │
  └────────┼──────────────┼──────────────┼────────────┘
           │              │              │
           ↓              ↓              ↓
     ┌──────────┐  ┌──────────┐  ┌──────────┐
     │ Server A │  │ Server B │  │ Server C │
     │ (GitHub) │  │ (数据库)  │  │ (文件系统)│
     └──────────┘  └──────────┘  └──────────┘
```

### 三个角色分别是谁

**Host（宿主）**——面向用户的 AI 应用

Host 是你直接打交道的那个程序，比如 Claude Desktop、Cursor、Cline。它负责：

- 提供用户界面（聊天窗口、代码编辑器……）
- 内嵌 AI 模型（或调用远程模型 API）
- 管理一个或多个 MCP Client
- 控制安全策略（哪些 Server 允许连接、是否需要用户确认）

> **类比**：Host 就是你的笔记本电脑——它上面有屏幕、有键盘，但要连外部设备，得通过 USB 接口（Client）。

**Client（客户端）**——Host 内部的连接器

Client 藏在 Host 内部，你通常看不到它。它负责：

- 与**一个** MCP Server 建立连接（1:1 关系）
- 把 Server 的能力（工具、数据、模板）"翻译"给 Host 和 AI 模型
- 管理通信协议（序列化/反序列化 JSON-RPC 消息）
- 维护与 Server 之间的会话状态

> **关键点**：一个 Host 内部可以有**多个** Client，每个 Client 连一个 Server。Claude Desktop 同时连 GitHub Server + 数据库 Server + 文件系统 Server？那就有 3 个 Client 在工作。

**Server（服务器）**——能力的提供方

Server 是真正干活的那个。它是一个**独立的进程**，对外暴露三类能力：

- **Tools**：可以被 AI 调用的函数（查天气、写文件、发消息……）
- **Resources**：可以被 AI 读取的数据（文件内容、数据库记录……）
- **Prompts**：可复用的提示模板（代码审查模板、翻译模板……）

> **类比**：Server 就是 USB 外设——可以是鼠标、是硬盘、是摄像头。它只要遵守 USB（MCP）标准，任何电脑（Host）都能识别它。

### 一个请求的完整旅程

当你对 Claude Desktop 说"帮我查一下 GitHub 上 mcp-server 仓库的 star 数"，背后发生了什么？

```
用户请求的完整流转路径：

  你："查一下 mcp-server 的 star 数"
   │
   ↓
  ① Host（Claude Desktop）收到消息
   │  → 把消息发给 AI 模型
   │
   ↓
  ② AI 模型分析后决定调用工具
   │  → 返回：调用 get_repo_info(repo="mcp-server")
   │
   ↓
  ③ Host 找到负责 GitHub 的 Client
   │  → Client 把工具调用请求打包成 JSON-RPC 消息
   │
   ↓
  ④ Client ──→ GitHub MCP Server
   │  → Server 收到请求，调用 GitHub API
   │  → 拿到结果：{ stars: 12345 }
   │
   ↓
  ⑤ Server ──→ Client ──→ Host
   │  → 结果返回给 AI 模型
   │
   ↓
  ⑥ AI 模型生成自然语言回复
   │  → "mcp-server 仓库目前有 12,345 个 star"
   │
   ↓
  你看到了回答 ✅
```

整个过程对用户来说是透明的——你只是问了一句话，就拿到了结果。但底层经历了 6 个步骤，涉及 Host、Client、Server 三方协作。

### Host 与 Server 的信任边界

这里有一个重要的设计原则：**Host 控制权限，Server 提供能力，两者之间有明确的信任边界**。

```
信任边界示意图：

  ┌──────────────────────────────┐
  │          Host（权限控制方）     │
  │                              │
  │  ✦ 用户在 Host 中配置：       │
  │    - 允许连接哪些 Server     │
  │    - 工具调用是否需要确认     │
  │    - Server 的访问范围       │
  │                              │
  │  ✦ Host 可以：               │
  │    - 拒绝 Server 的请求      │
  │    - 弹窗让用户确认操作      │
  │    - 随时断开 Server 连接    │
  ├──────────────────────────────┤
  │  ═══════ 信任边界 ═══════    │
  ├──────────────────────────────┤
  │        Server（能力提供方）    │
  │                              │
  │  ✦ Server 只能：             │
  │    - 声明自己有什么能力       │
  │    - 等待被调用，不能主动骚扰  │
  │    - 返回结果，无法访问对话   │
  └──────────────────────────────┘
```

> **安全原则**：MCP Server 是"被动的服务提供者"。它不能主动给 AI 发消息，不能偷看用户的对话历史，更不能绕过 Host 直接执行操作。所有的权限都由 Host（和用户）控制。

---

### 2.2 JSON-RPC 2.0：MCP 的通信语言

Host、Client、Server 三方之间怎么"说话"？MCP 选择了一个已经存在十多年的成熟协议：**JSON-RPC 2.0**。

### 为什么选 JSON-RPC 而不是 REST

你可能会想："为什么不用大家都熟悉的 REST API？"

```
REST API 的问题：

  ① 太重了
     → 每个请求都带 HTTP 头、URL 路径、Method 区分
     → MCP 只需要"调个函数"，不需要这么多仪式

  ② 不支持双向通信
     → REST 是 Client → Server 单向的
     → MCP 需要 Server 也能主动通知 Client（比如数据变更）

  ③ 不够标准化
     → 同样是"创建用户"，不同 REST API 的 URL / 参数风格千差万别
     → JSON-RPC 的消息格式是固定的，解析逻辑一次编写到处复用

JSON-RPC 2.0 的优势：

  ✅ 轻量：就是一个 JSON 对象，没有 URL 路由、没有 HTTP Method
  ✅ 双向：Client 和 Server 都能发消息
  ✅ 标准：消息格式完全固定，极易解析
  ✅ 成熟：2010 年发布，VS Code、以太坊、各种 LSP 都在用
```

### JSON-RPC 消息的三种类型

MCP 中的所有通信都由三种 JSON-RPC 消息组成：

**① Request（请求）**——需要对方回复

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": { "city": "北京" }
  }
}
```

关键字段：
- `id`：请求编号，对方回复时用这个 id 关联
- `method`：要调用的方法名
- `params`：参数

**② Response（响应）**——对 Request 的回复

```json
// 成功响应
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      { "type": "text", "text": "北京今天 25°C，晴" }
    ]
  }
}

// 错误响应
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "城市名不能为空"
  }
}
```

关键字段：
- `id`：与对应 Request 的 id 一致
- `result` 或 `error`：二选一，成功返回 result，失败返回 error

**③ Notification（通知）**——不需要回复的单向消息

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": {
    "uri": "file:///data/config.json"
  }
}
```

关键字段：
- 没有 `id` 字段——这就是 Notification 和 Request 的区分标志
- 发出去就完事，不期待对方回复

### MCP 中常见的 Method 清单

```
初始化阶段：
  initialize          → Client 向 Server 发起握手
  initialized         → Client 通知 Server 握手完成（Notification）

工具相关：
  tools/list          → 列出 Server 提供的所有工具
  tools/call          → 调用某个工具

资源相关：
  resources/list      → 列出所有资源
  resources/read      → 读取某个资源

提示模板相关：
  prompts/list        → 列出所有 Prompt 模板
  prompts/get         → 获取某个 Prompt

变更通知（Notification）：
  notifications/tools/list_changed      → 工具列表变了
  notifications/resources/updated       → 某个资源更新了
```

### 一次完整的"初始化 → 调用工具"消息流

```
Client                              Server
  │                                    │
  │──── initialize ──────────────────→ │  ← Request（id:1）
  │                                    │
  │←─── result: capabilities ────────  │  ← Response（id:1）
  │                                    │
  │──── initialized ─────────────────→ │  ← Notification（无 id）
  │                                    │
  │──── tools/list ──────────────────→ │  ← Request（id:2）
  │                                    │
  │←─── result: [get_weather, ...] ──  │  ← Response（id:2）
  │                                    │
  │──── tools/call(get_weather) ─────→ │  ← Request（id:3）
  │                                    │
  │←─── result: "25°C, 晴" ──────────  │  ← Response（id:3）
  │                                    │
```

> **记住这个模式**：MCP 的所有交互都是 Request-Response 或 Notification——没有长轮询、没有 WebSocket 帧、没有复杂握手。简单到你用 `print(json.dumps(...))` 就能手搓一条合法的 MCP 消息。

---

### 2.3 Transport 层：STDIO vs HTTP+SSE

JSON-RPC 定义了消息的"格式"，但消息怎么**传输**？通过网络？还是通过管道？

MCP 定义了两种 Transport（传输层）：**STDIO** 和 **HTTP+SSE**。

### STDIO：本地通信的首选

STDIO 就是你在终端里最熟悉的标准输入输出（stdin / stdout）。

```
STDIO 工作原理：

  Host 进程（Claude Desktop）
      │
      │  启动子进程（fork / spawn）
      │
      ↓
  Server 进程（python my_server.py）
      │
      │  通信方式：
      │  Host → Server：写入 Server 的 stdin
      │  Server → Host：输出到 Server 的 stdout
      │
      ↓
  效果：两个进程通过管道互发 JSON-RPC 消息
```

**STDIO 的特点：**

| 优点 | 缺点 |
|------|------|
| 零配置——不需要端口、IP、启动 HTTP 服务 | 只能本地使用 |
| 启动快——Host 直接 spawn 子进程 | Server 必须和 Host 在同一台机器上 |
| 安全——进程间通信，不走网络 | 不支持多 Client 同时连一个 Server |
| 简单——适合开发调试阶段 | 调试难——print 会干扰 stdout 消息流 |

**消息传输格式：**

```
STDIO 中的消息是以换行符分隔的 JSON：

  Host 写入 Server 的 stdin：
  {"jsonrpc":"2.0","id":1,"method":"tools/list"}\n
  {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{...}}\n

  Server 写入 stdout 回复：
  {"jsonrpc":"2.0","id":1,"result":{"tools":[...]}}\n
  {"jsonrpc":"2.0","id":2,"result":{"content":[...]}}\n

  ⚠️ 每条消息一行，以 \n 结尾
  ⚠️ 不要在 Server 代码里 print() 调试信息——会被 Client 当成 JSON 解析然后报错！
     → 用 stderr 输出调试信息：print("debug", file=sys.stderr)
```

> **实际体验**：你在 Claude Desktop 的配置文件里写 `"command": "python", "args": ["my_server.py"]`，Claude 就会用 STDIO 方式启动你的 Server。开发阶段 90% 的场景都用 STDIO。

### HTTP+SSE：远程部署的方案

当 Server 不在本地——比如部署在云服务器上——就需要通过网络通信。MCP 使用 **HTTP + SSE（Server-Sent Events）** 的组合：

```
HTTP+SSE 工作原理：

  MCP Client                          MCP Server（远程）
      │                                    │
      │ ─── GET /sse ────────────────────→ │
      │                                    │  Server 返回 SSE 流
      │ ←── SSE: endpoint=/messages?id=abc │  告诉 Client 消息端点
      │                                    │
      │ ─── POST /messages?id=abc ───────→ │  Client 发送 Request
      │                                    │
      │ ←── SSE: data={result:...} ──────  │  Server 通过 SSE 返回响应
      │                                    │
      │ ←── SSE: data={notification:...} ─ │  Server 可以推送通知
      │                                    │
```

**为什么不用 WebSocket？**

```
WebSocket 的问题：
  ❌ 很多企业防火墙/代理不支持 WebSocket
  ❌ 需要专门的 WebSocket 服务器设施
  ❌ 连接状态管理复杂

HTTP+SSE 的优势：
  ✅ 走标准 HTTP——任何代理和 CDN 都支持
  ✅ SSE 是浏览器原生支持的技术
  ✅ Client → Server 用 POST（标准 HTTP）
  ✅ Server → Client 用 SSE（长连接推送）
  ✅ 足够覆盖 MCP 的双向通信需求
```

**HTTP+SSE 的特点：**

| 优点 | 缺点 |
|------|------|
| 支持远程部署——Server 可以在云上 | 需要启动 HTTP 服务 |
| 可穿越防火墙和代理 | 比 STDIO 多了网络延迟 |
| 支持多 Client 连接同一个 Server | 需要处理认证和安全 |
| 适合生产环境 | 配置略复杂 |

### 如何选择 Transport

```
选择决策树：

  Server 要远程访问吗？
      │
      ├── 否 → STDIO（简单、安全、零配置）
      │         适合：本地开发、Claude Desktop 配置、个人使用
      │
      └── 是 → HTTP+SSE（网络通信）
                适合：团队共享 Server、云端部署、生产环境
```

> **实操建议**：先用 STDIO 开发调试，功能稳定后再切到 HTTP+SSE 部署。MCP SDK 让这个切换非常简单——通常只需要改一行启动代码。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 三层架构 | Host（用户界面）→ Client（连接器）→ Server（能力提供方） |
| Host 的职责 | 管理 UI、管理 Client、控制安全策略 |
| Client 的关系 | 一个 Client 连一个 Server（1:1），Host 可有多个 Client |
| Server 的能力 | 暴露 Tools + Resources + Prompts |
| 信任边界 | Host 控制权限，Server 被动提供能力 |
| 通信协议 | JSON-RPC 2.0（Request / Response / Notification） |
| STDIO Transport | 本地通信，stdin/stdout，零配置，开发首选 |
| HTTP+SSE Transport | 远程通信，HTTP POST + SSE 推送，生产部署用 |

> **下一章预告**：MCP 的三大原语 —— Tools、Resources、Prompts。深入理解 MCP Server 到底能暴露哪三类能力，它们各自适合什么场景，以及实际的代码长什么样。


