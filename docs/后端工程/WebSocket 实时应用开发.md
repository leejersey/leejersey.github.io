# WebSocket 实时应用开发

> 从 HTTP 到全双工——WebSocket 协议原理、Python 后端实现、房间/频道模型、心跳重连、消息协议设计、认证鉴权、水平扩展，用 FastAPI + 前端代码构建生产级实时应用。

---

## 1. 为什么需要 WebSocket

你正在开发一个聊天应用——用户 A 发了一条消息，用户 B 要立刻看到。听起来很简单，但 HTTP 协议天生不支持这件事——它是"你问我答"的**请求-响应模型**，服务器永远不能主动推送数据给客户端。

在 WebSocket 出现之前，工程师们想了很多办法来"模拟"实时通信。我们先理解这些方案为什么不够好，才能真正理解 WebSocket 的价值。

### 1.1 HTTP 的实时困境：轮询、长轮询、SSE

**方案 1：短轮询（Polling）**

最朴素的思路——客户端每隔几秒问一次服务器"有新消息吗？"

```
短轮询时序图：

  客户端                              服务器
  ──────                              ──────
  GET /messages?since=100 ──────────▶  查数据库
                         ◀──────────  200 "无新消息"
  
  （等 3 秒）
  
  GET /messages?since=100 ──────────▶  查数据库
                         ◀──────────  200 "无新消息"
  
  （等 3 秒）
  
  GET /messages?since=100 ──────────▶  查数据库
                         ◀──────────  200 [新消息!]
  
  问题：
  → 99% 的请求返回"无新消息"——纯粹浪费
  → 3 秒轮询间隔 = 最差 3 秒延迟
  → 1000 个在线用户 = 每秒 333 个无用请求
  → 服务器和数据库不堪重负
```

**方案 2：长轮询（Long Polling）**

优化思路——服务器"hold 住"请求，有新消息再返回。

```
长轮询时序图：

  客户端                              服务器
  ──────                              ──────
  GET /messages?since=100 ──────────▶  没有新消息？
                                       不返回，hold 住连接
                                       ......等待......
                                       （30 秒后新消息来了）
                         ◀──────────  200 [新消息!]
  
  GET /messages?since=101 ──────────▶  继续 hold 住
                                       ......等待......

  比短轮询好在哪？
  → 有消息时立即返回（近乎实时）
  → 没消息时不会频繁请求
  
  但仍然有问题：
  → 每次消息后都要重新建立 HTTP 连接（TCP 握手开销）
  → 服务器要 hold 大量空闲连接（资源占用）
  → HTTP Header 每次 ~800 字节往返（协议开销大）
```

**方案 3：Server-Sent Events（SSE）**

HTML5 标准方案——服务器单向推送，基于 HTTP 长连接。

```
SSE 时序图：

  客户端                              服务器
  ──────                              ──────
  GET /events ──────────────────────▶  HTTP 200
  Accept: text/event-stream           Content-Type: text/event-stream
                                      Connection: keep-alive
                                      
                         ◀──────────  data: {"msg": "hello"}\n\n
                         ◀──────────  data: {"msg": "world"}\n\n
                         ◀──────────  data: {"msg": "!"}\n\n
  
  优点：
  → 原生浏览器支持（EventSource API）
  → 自动重连、事件 ID 追踪
  → 基于 HTTP，穿透性好
  
  致命缺陷：
  → 单向通信（服务器 → 客户端），客户端不能推消息给服务器
  → 每条消息仍然带 HTTP 头开销
  → 不支持二进制数据
```

**三种方案对比：**

| 方案 | 延迟 | 服务器开销 | 双向通信 | 协议开销 | 适用场景 |
|:---|:---|:---|:---|:---|:---|
| **短轮询** | 高（轮询间隔） | 极高（无用请求） | ❌ | 极高 | 简单通知（邮件检查） |
| **长轮询** | 低 | 高（hold 连接） | ❌ | 高 | 兼容旧浏览器 |
| **SSE** | 低 | 中 | ❌ 单向 | 中 | 服务器推送（股票行情） |
| **WebSocket** | 极低 | 低 | ✅ 全双工 | 极低（2-14 字节） | 聊天/游戏/协作/交易 |

### 1.2 WebSocket 的核心承诺：全双工、低延迟、低开销

WebSocket 协议（RFC 6455）在 2011 年正式标准化，它用一次 HTTP 握手"升级"为持久的全双工连接。

```
HTTP vs WebSocket 通信模型对比：

  HTTP（半双工，请求-响应）：
  ═══════════════════════════════════
  客户端 ─── 请求 ──▶ 服务器
  客户端 ◀── 响应 ─── 服务器
  客户端 ─── 请求 ──▶ 服务器
  客户端 ◀── 响应 ─── 服务器
  
  → 永远是客户端先说话
  → 每次对话都要带完整 HTTP 头（~800 字节）
  → 每次对话都是独立的 TCP 连接（或复用的 keep-alive）

  WebSocket（全双工，自由通信）：
  ═══════════════════════════════════
  客户端 ←──握手──→ 服务器  （1 次 HTTP 升级）
  
  客户端 ─── 消息 ──▶ 服务器  ┐
  客户端 ◀── 消息 ─── 服务器  │ 任意方向
  客户端 ─── 消息 ──▶ 服务器  │ 任意时刻
  客户端 ◀── 消息 ─── 服务器  │ 同时进行
  客户端 ◀── 消息 ─── 服务器  ┘
  
  → 任何一方都可以随时发消息
  → 消息头只有 2-14 字节（比 HTTP 小 98%）
  → 一个 TCP 连接持续整个会话
```

**量化开销对比：**

```
发送 1000 条聊天消息的网络开销：

  HTTP 短轮询：
  → 每条消息：~800 字节请求头 + ~800 字节响应头 + 数据
  → 1000 条：1000 × 1600 = 1,600,000 字节协议开销
  → 加上 99% 的空轮询：实际开销 × 10 以上
  
  WebSocket：
  → 握手：1 次 HTTP 升级（~200 字节）
  → 每条消息：2-6 字节帧头 + 数据
  → 1000 条：200 + 1000 × 6 = 6,200 字节协议开销

  → WebSocket 协议开销是 HTTP 的 1/258 ✅
```

> 💡 **核心价值**：WebSocket 不是"更快的 HTTP"——它是一种完全不同的通信范式。HTTP 是"你问我答"，WebSocket 是"打电话"。建立连接后，双方平等，随时说话，不挂断。
### 1.3 什么时候不需要 WebSocket

WebSocket 不是银弹。很多场景用 HTTP 或 SSE 就够了，强行用 WebSocket 反而增加复杂度：

```
不需要 WebSocket 的场景：

  ❌ 低频通知（每分钟 1 次）
  → 短轮询就够，1 分钟一个 GET 请求不算负担
  
  ❌ 纯服务器推送（客户端不需要发消息给服务器）
  → SSE 更简单：原生浏览器支持、自动重连、基于 HTTP 穿透性好
  → 股票行情、新闻推送、构建日志流 → 用 SSE
  
  ❌ 请求-响应模式（查询 API、表单提交）
  → HTTP RESTful API 就是最佳选择
  → WebSocket 没有 HTTP 的缓存、状态码、重定向等丰富语义
  
  ❌ 对基础设施要求低的项目
  → WebSocket 需要 Nginx 配合（proxy_pass 配置）
  → 需要处理心跳、重连、认证等额外复杂度
  → 小团队/小项目可能不值得
```

**技术选型决策树：**

```
你的需求是什么？
├── 客户端定期获取数据？
│   └── 短轮询 / HTTP 缓存
├── 服务器单向推送给客户端？
│   └── SSE（简单、原生支持、自动重连）
├── 双向实时通信？
│   ├── 延迟要求 < 100ms？
│   │   └── WebSocket ✅
│   └── 延迟要求 > 1s？
│       └── 长轮询也够用
└── 二进制数据传输（音视频、游戏状态）？
    └── WebSocket ✅（支持二进制帧）
```

> 💡 **务实建议**：如果你的项目只需要"服务器通知客户端有新数据"，**先试 SSE**。它比 WebSocket 简单一个数量级——不需要心跳、不需要消息协议、不需要 Nginx 特殊配置。等你真的需要双向实时通信了，再用 WebSocket。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **短轮询** | 定时 GET，99% 请求是浪费，延迟 = 轮询间隔 |
| **长轮询** | 服务器 hold 住请求直到有新数据，近乎实时但连接开销大 |
| **SSE** | 服务器单向推送，基于 HTTP，适合纯推送场景 |
| **WebSocket** | 全双工、2-14 字节帧头、一次握手持久连接、双方随时发消息 |
| **选型原则** | 纯推送用 SSE，双向实时用 WebSocket，低频通知用轮询 |

---

## 2. WebSocket 协议深入理解

很多人把 WebSocket 当黑盒用——调 API、发消息、收消息，不关心协议层面的细节。但当你遇到"Nginx 代理后连接断开"、"手机锁屏后消息收不到"、"奇怪的 1006 状态码"这些问题时，理解协议才能找到答案。

### 2.1 握手过程：从 HTTP 到 WebSocket 的升级

WebSocket 连接的建立从一个特殊的 HTTP 请求开始——**Upgrade 请求**。

```
完整的握手报文：

  客户端请求：
  ═══════════════════════════════════
  GET /chat HTTP/1.1
  Host: server.example.com
  Upgrade: websocket              ← 关键：请求协议升级
  Connection: Upgrade             ← 关键：连接升级
  Sec-WebSocket-Key: dGhlIHNhbXBsZQ==  ← 随机 Base64 字符串
  Sec-WebSocket-Version: 13       ← 协议版本（几乎总是 13）
  Sec-WebSocket-Protocol: chat    ← 可选：子协议协商
  Origin: http://example.com      ← 浏览器自动附加的来源

  服务器响应（同意升级）：
  ═══════════════════════════════════
  HTTP/1.1 101 Switching Protocols    ← 101 = 协议切换成功
  Upgrade: websocket
  Connection: Upgrade
  Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=  ← 验证值

  → 从这一刻起，这条 TCP 连接不再是 HTTP
  → 双方切换到 WebSocket 帧协议
  → 全双工通信正式开始 ✅
```

**Sec-WebSocket-Key 的验证机制：**

```
服务器怎么计算 Sec-WebSocket-Accept？

  1. 取客户端发的 Sec-WebSocket-Key
     → "dGhlIHNhbXBsZQ=="
  
  2. 拼接一个固定的 GUID（RFC 6455 规定的魔法字符串）
     → "dGhlIHNhbXBsZQ==" + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
  
  3. 对拼接结果做 SHA-1 哈希，再 Base64 编码
     → SHA1(...) → Base64 → "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
  
  → 这不是加密或安全机制！
  → 只是为了确认服务器真的理解 WebSocket 协议
  → 防止普通 HTTP 服务器意外接受 WebSocket 连接
```

**握手失败的常见原因：**

| 现象 | 原因 | 解决方案 |
|:---|:---|:---|
| 403 Forbidden | Origin 不在白名单 | 服务器配置 CORS 或检查 Origin 校验逻辑 |
| 400 Bad Request | 缺少 Upgrade 头 | 检查反向代理是否正确透传头信息 |
| 连接超时 | Nginx 没配 `proxy_set_header` | 加上 `Upgrade` 和 `Connection` 头透传 |
| 101 后立即断开 | 子协议不匹配 | 检查 `Sec-WebSocket-Protocol` 客户端/服务端是否一致 |

### 2.2 帧结构：理解 WebSocket 的数据格式

握手完成后，所有数据都以**帧（Frame）**的形式传输。理解帧结构能帮你调试很多"消息丢失"或"数据乱码"的问题。

```
WebSocket 帧格式（RFC 6455）：

  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-------+-+-------------+-------------------------------+
  |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
  |I|S|S|S|  (4)  |A|     (7)     |            (16/64)            |
  |N|V|V|V|       |S|             |                               |
  | |1|2|3|       |K|             |                               |
  +-+-+-+-+-------+-+-------------+-------------------------------+
  |     Masking-key (0 or 4 bytes)                                |
  +---------------------------------------------------------------+
  |     Payload Data                                              |
  +---------------------------------------------------------------+

  各字段含义：
  ═══════════════════════════════════
  FIN (1 bit)  → 1 = 这是消息的最后一帧，0 = 后面还有续帧
  Opcode (4 bit) → 帧类型（见下表）
  MASK (1 bit) → 1 = 数据被掩码处理（客户端→服务器必须 mask）
  Payload len  → 7 bit: 0-125 直接表示长度
                 7 bit = 126: 后续 2 字节表示长度（最大 65535）
                 7 bit = 127: 后续 8 字节表示长度（最大 ~9.2EB）
```

**Opcode 类型表：**

| Opcode | 名称 | 说明 |
|:---|:---|:---|
| `0x0` | Continuation | 续帧（大消息被拆成多帧时使用） |
| `0x1` | Text | 文本帧（UTF-8 编码） |
| `0x2` | Binary | 二进制帧（图片、音频、Protobuf） |
| `0x8` | Close | 关闭连接 |
| `0x9` | Ping | 心跳探测 |
| `0xA` | Pong | 心跳应答 |

```
为什么客户端发给服务器的数据要 Mask？

  → 不是为了加密（Mask Key 是明文发送的）
  → 是为了防止**代理缓存投毒攻击**
  → 旧的 HTTP 代理可能把 WebSocket 数据当 HTTP 缓存
  → Mask 让数据看起来像随机字节，代理就不会误缓存
  → 服务器发给客户端不需要 Mask（因为方向不经过代理）
```

> 💡 **实战意义**：你几乎永远不需要手动构造帧——所有 WebSocket 库都帮你处理了。但当你用 Wireshark 抓包调试时，理解帧结构能帮你快速定位 "帧被截断"、"Opcode 不对" 或 "Mask 错误" 的问题。
### 2.3 控制帧：Ping、Pong 与 Close 的协议语义

WebSocket 协议定义了三种控制帧，它们不携带业务数据，而是管理连接本身的状态。

**Ping / Pong（心跳探测）：**

```
Ping-Pong 机制：

  服务器 ─── Ping（可携带数据） ──▶ 客户端
  服务器 ◀── Pong（必须回传相同数据）── 客户端
  
  规则：
  → 收到 Ping 必须回 Pong（协议强制要求）
  → Pong 的 payload 必须和 Ping 完全一致
  → 可以发"主动 Pong"（不响应任何 Ping），用作单向心跳
  → 如果连续 N 次 Ping 没收到 Pong → 认为连接已死
```

**Close（优雅关闭）：**

```
Close 帧的两阶段关闭：

  发起方 ─── Close（状态码 + 原因） ──▶ 接收方
  发起方 ◀── Close（状态码 + 原因） ─── 接收方
  
  → 双方互发 Close 帧后，TCP 连接断开
  → 这叫"优雅关闭"（Clean Close）
  → 如果一方直接关 TCP 不发 Close → "异常关闭"
```

**常见 Close 状态码：**

| 状态码 | 名称 | 含义 |
|:---|:---|:---|
| `1000` | Normal Closure | 正常关闭（业务完成） |
| `1001` | Going Away | 服务器关机 / 客户端导航离开页面 |
| `1002` | Protocol Error | 协议错误（帧格式不对） |
| `1003` | Unsupported Data | 收到不支持的数据类型 |
| `1006` | Abnormal Closure | ⚠️ TCP 直接断了，没走 Close 流程 |
| `1008` | Policy Violation | 违反安全策略（认证失败、权限不足） |
| `1011` | Internal Error | 服务器内部错误 |

> 💡 **1006 是最常见的"幽灵错误"**：你在客户端 `onclose` 事件里看到 `code=1006`，说明连接不是优雅关闭的——可能是网络断了、手机锁屏了、Nginx 超时了。这不是 bug，而是现实。你的应用必须能优雅处理 1006（自动重连，详见第 6 章）。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **HTTP Upgrade** | WebSocket 通过一次 HTTP 101 响应完成协议切换 |
| **Sec-WebSocket-Key** | 不是加密，是验证服务器理解 WebSocket 协议 |
| **帧结构** | FIN + Opcode + Mask + Payload，最小开销 2 字节 |
| **Mask** | 客户端→服务器必须 Mask，防代理缓存投毒 |
| **Close 1006** | TCP 异常断开（非优雅关闭），客户端必须能处理 |

---

## 3. Python WebSocket 后端实战

理解了协议，现在动手写代码。Python 生态有多个 WebSocket 方案，选择困难是正常的——这一章帮你做决定，然后用 FastAPI 从零搭建一个可运行的 WebSocket 服务。

### 3.1 Python WebSocket 生态选型

```
三大方案定位：

  websockets（纯 WebSocket 库）
  ═══════════════════════════════════
  → 轻量、符合标准、无框架依赖
  → 适合：独立的 WebSocket 微服务
  → 不适合：需要 HTTP API + WebSocket 混合的场景
  
  FastAPI WebSocket（集成在 Web 框架里）
  ═══════════════════════════════════
  → FastAPI 原生支持 WebSocket 路由
  → HTTP API 和 WebSocket 共享路由、中间件、依赖注入
  → 适合：已用 FastAPI 的项目，前后端一体化
  → 底层就是 Starlette 的 WebSocket 支持
  
  python-socketio / Socket.IO
  ═══════════════════════════════════
  → 不是标准 WebSocket！是 Socket.IO 自有协议
  → 自带房间、广播、自动重连、命名空间
  → 前端必须用 socket.io-client（不能用原生 WebSocket API）
  → 适合：快速原型、不在意协议标准的项目
```

| 方案 | 协议标准 | 学习曲线 | 房间/广播 | HTTP 共存 | 适用场景 |
|:---|:---|:---|:---|:---|:---|
| **websockets** | ✅ RFC 6455 | 低 | ❌ 需自建 | ❌ 独立 | WebSocket 微服务 |
| **FastAPI WS** | ✅ RFC 6455 | 中 | ❌ 需自建 | ✅ 原生 | API + 实时混合 |
| **Socket.IO** | ❌ 私有协议 | 低 | ✅ 内置 | ✅ | 快速原型 |

> 💡 **本文选择 FastAPI WebSocket**。理由：1) 大多数 Python 后端项目已经在用 FastAPI；2) 标准 WebSocket 协议，前端可以用原生 API；3) 房间/广播虽然需要自建，但这正是你要学的核心技能。

### 3.2 FastAPI WebSocket：从零搭建

**安装依赖：**

```bash
pip install fastapi uvicorn[standard]
```

**最简 WebSocket 服务（echo 服务器）：**

```python
"""ws_echo.py - 最简 WebSocket echo 服务"""
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()  # 完成握手
    try:
        while True:
            data = await ws.receive_text()  # 等待客户端消息
            await ws.send_text(f"Echo: {data}")  # 回复
    except Exception:
        pass  # 连接断开时自然退出循环
```

**带连接管理的完整示例（支持多客户端广播）：**

```python
"""ws_server.py - 支持广播的 WebSocket 服务"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

class ConnectionManager:
    """管理所有 WebSocket 连接"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)
    
    def disconnect(self, ws: WebSocket):
        self.active_connections.remove(ws)
    
    async def broadcast(self, message: str):
        """向所有连接发送消息"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass  # 发送失败的连接会在下次循环中被清理

manager = ConnectionManager()

@app.websocket("/ws/chat")
async def chat_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            # 广播给所有在线用户
            await manager.broadcast(f"用户说: {data}")
    except WebSocketDisconnect:
        manager.disconnect(ws)
        await manager.broadcast("一位用户离开了聊天室")
```

**启动服务：**

```bash
uvicorn ws_server:app --reload --host 0.0.0.0 --port 8000
# WebSocket 地址：ws://localhost:8000/ws/chat
```

> 💡 **注意 `receive_text()` 的阻塞特性**：`await ws.receive_text()` 会一直等到客户端发消息为止。如果客户端静默了，这个协程就一直挂着——但因为是 async，不会阻塞其他连接。这就是 Python asyncio 的核心优势。
### 3.3 连接生命周期管理：打开、消息、关闭、异常

WebSocket 连接有四个阶段，每个阶段都要正确处理，否则会导致连接泄漏或状态不一致。

```
WebSocket 连接生命周期：

  ┌─────────┐   accept()    ┌─────────┐
  │ 握手中  │ ────────────▶ │  已连接  │
  └─────────┘               └────┬────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              receive_text() send_text()  异常发生
                    │            │            │
                    ▼            ▼            ▼
              ┌─────────┐              ┌──────────┐
              │ 通信中  │              │ 异常关闭  │
              └────┬────┘              └──────────┘
                   │
             WebSocketDisconnect
                   │
              ┌────▼────┐
              │ 已断开  │
              └─────────┘
```

**生产级的连接处理模式：**

```python
"""ws_lifecycle.py - 生产级连接生命周期管理"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)
app = FastAPI()

@app.websocket("/ws/{user_id}")
async def websocket_handler(ws: WebSocket, user_id: str):
    # 1. 握手阶段：可以在这里做认证检查
    # （拒绝连接：直接 await ws.close(code=1008)）
    await ws.accept()
    logger.info(f"用户 {user_id} 已连接")
    
    try:
        # 2. 通信阶段：消息循环
        while True:
            raw = await ws.receive_text()
            # 处理业务逻辑...
            await ws.send_text(f"收到: {raw}")
    
    except WebSocketDisconnect as e:
        # 3. 正常断开（客户端主动关闭或网络中断）
        logger.info(f"用户 {user_id} 断开，code={e.code}")
    
    except Exception as e:
        # 4. 异常关闭（服务器端错误）
        logger.error(f"用户 {user_id} 连接异常: {e}")
        try:
            await ws.close(code=1011)  # Internal Error
        except Exception:
            pass  # 连接可能已经死了
    
    finally:
        # 5. 清理阶段（无论如何都会执行）
        # 🔥 这里是关键——从连接池移除、清理房间、更新在线状态
        manager.disconnect(ws)
        logger.info(f"用户 {user_id} 资源已清理")
```

> 💡 **必须用 `finally` 做清理**。不要只在 `except WebSocketDisconnect` 里清理——如果服务器端代码抛出其他异常（比如数据库超时），会跳过 `WebSocketDisconnect` 分支，导致连接泄漏。`finally` 确保任何退出路径都会执行清理。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **websockets** | 纯 WebSocket 库，轻量独立，适合微服务 |
| **FastAPI WS** | 与 HTTP 路由共存，本文主选方案 |
| **Socket.IO** | 私有协议，内置房间广播，前端需配套库 |
| **ConnectionManager** | 维护 `active_connections` 列表，实现广播/单发 |
| **finally 清理** | 无论正常断开还是异常，都必须在 finally 中清理连接 |

---

## 4. 消息协议设计

WebSocket 只管传输字节——它不关心你发的是聊天消息、心跳包还是错误通知。你需要在 WebSocket 之上设计一套**应用层协议**，定义"消息长什么样、怎么区分类型、怎么确认收到"。

### 4.1 为什么裸 WebSocket 不够：应用层协议的必要性

```
裸 WebSocket 的问题——收到一条消息 "hello"：

  问题 1：这是什么消息？
  ═══════════════════════════════════
  → 是聊天内容？心跳？系统通知？加入房间的请求？
  → 没有类型字段，只能靠猜
  
  问题 2：这是谁发的？发给谁的？
  ═══════════════════════════════════
  → WebSocket 只知道"连接 A 发了消息"
  → 不知道这条消息是发给"所有人"还是"某个用户"
  
  问题 3：对方收到了吗？
  ═══════════════════════════════════
  → WebSocket 不保证应用层投递
  → TCP 保证传输层到达，但不保证对方应用层处理了
  → 关键消息（比如转账通知）需要 ACK 确认
  
  问题 4：请求和响应怎么对应？
  ═══════════════════════════════════
  → HTTP 天然有请求-响应对应关系
  → WebSocket 的消息是无序的流
  → 客户端发了两个请求，收到一个响应，不知道是回复哪个的
  
  问题 5：协议升级怎么办？
  ═══════════════════════════════════
  → 新版客户端发了新格式的消息，旧版服务器怎么处理？
  → 没有版本协商机制
```

> 💡 **类比**：裸 WebSocket 就像一根电话线——你能听到对方说话，但没有电话礼仪。应用层协议就是"先报名字、再说事情、说完等对方确认"的规矩。

### 4.2 消息格式设计：类型系统与序列化选型

**推荐的 JSON 消息格式：**

```json
// 所有消息都有这四个字段
{
  "type": "chat.message",      // 消息类型（命名空间.动作）
  "id": "msg_abc123",          // 消息 ID（用于 ACK 和去重）
  "data": {                    // 业务数据（类型不同，结构不同）
    "room_id": "room_001",
    "content": "大家好！",
    "sender": "user_42"
  },
  "ts": 1712836800             // 时间戳（秒级）
}
```

**消息类型设计（用命名空间分组）：**

```python
"""messages.py - 消息类型定义"""
from pydantic import BaseModel
from enum import Enum

class MessageType(str, Enum):
    # 聊天相关
    CHAT_MESSAGE = "chat.message"
    CHAT_TYPING = "chat.typing"
    
    # 房间相关
    ROOM_JOIN = "room.join"
    ROOM_LEAVE = "room.leave"
    ROOM_MEMBERS = "room.members"
    
    # 系统相关
    SYS_PING = "sys.ping"
    SYS_PONG = "sys.pong"
    SYS_ERROR = "sys.error"
    SYS_ACK = "sys.ack"

class WSMessage(BaseModel):
    """所有 WebSocket 消息的基类"""
    type: MessageType
    id: str | None = None
    data: dict = {}
    ts: int | None = None

# 收到原始文本后解析
import json
raw = await ws.receive_text()
msg = WSMessage(**json.loads(raw))

if msg.type == MessageType.CHAT_MESSAGE:
    await handle_chat(msg)
elif msg.type == MessageType.ROOM_JOIN:
    await handle_join(msg)
```

**序列化格式选型：**

| 格式 | 体积 | 可读性 | 浏览器原生 | Schema | 适用场景 |
|:---|:---|:---|:---|:---|:---|
| **JSON** | 大 | ✅ 可读 | ✅ | ❌ | 90% 的 Web 应用 |
| **MessagePack** | 小 30% | ❌ 二进制 | 需库 | ❌ | 对带宽敏感的移动端 |
| **Protobuf** | 最小 | ❌ 二进制 | 需库 | ✅ 强类型 | 高性能游戏/交易系统 |

> 💡 **90% 的项目用 JSON 就对了**。JSON 的"大"在 WebSocket 场景下并不是问题——一条聊天消息 JSON 格式大约 200 字节，比 HTTP 头小得多。只有在每秒上万条消息的游戏/交易场景，才值得引入 Protobuf。
### 4.3 请求-响应模式与消息确认（ACK）

WebSocket 天然是"事件驱动"的——没有 HTTP 那样天然的请求-响应对应关系。但很多场景（加入房间、发送消息）需要知道"操作是否成功"。这就需要用 **消息 ID 做请求-响应映射**。

```
请求-响应映射（通过 message ID）：

  客户端发送：
  {"type": "room.join", "id": "req_001", "data": {"room": "lobby"}}
  
  服务器回复（用同一个 id）：
  {"type": "sys.ack", "id": "req_001", "data": {"ok": true}}
  
  客户端匹配逻辑：
  → 发送 req_001 时，创建一个 Promise / Future
  → 收到 id=req_001 的响应后，resolve 这个 Promise
  → 如果 5 秒没收到响应 → 超时，reject
```

**Python 服务端 ACK 处理：**

```python
"""ack_handler.py - 服务端 ACK 响应"""
import json
import time
import uuid

async def handle_message(ws, raw_text: str):
    msg = json.loads(raw_text)
    msg_type = msg.get("type")
    msg_id = msg.get("id")
    
    try:
        if msg_type == "room.join":
            room_id = msg["data"]["room"]
            await join_room(ws, room_id)
            # 成功：返回 ACK
            await ws.send_text(json.dumps({
                "type": "sys.ack",
                "id": msg_id,  # 🔥 回传原始 ID，客户端用它匹配
                "data": {"ok": True, "room": room_id},
                "ts": int(time.time())
            }))
        
        elif msg_type == "chat.message":
            # 广播消息不需要 ACK（尽力而为）
            await broadcast_to_room(msg["data"])
    
    except Exception as e:
        # 失败：返回 error（也带上 msg_id）
        await ws.send_text(json.dumps({
            "type": "sys.error",
            "id": msg_id,
            "data": {"error": str(e), "code": "JOIN_FAILED"},
            "ts": int(time.time())
        }))
```

**什么消息需要 ACK，什么不需要？**

| 消息类型 | 需要 ACK？ | 原因 |
|:---|:---|:---|
| 加入/离开房间 | ✅ | 客户端需知道操作是否成功 |
| 聊天消息 | ⚠️ 可选 | 大多数场景不需要，关键消息（转账）需要 |
| 心跳 Ping | ❌ | 协议层自动处理 |
| 广播通知 | ❌ | 发了就发了，不需要每个人确认 |
| 在线状态变更 | ❌ | 最终一致即可 |

> 💡 **设计原则**：只对"需要知道结果的操作"做 ACK。如果每条消息都要 ACK，系统的消息量直接翻倍——聊天室里 100 人，一条消息就变成 100 条 ACK，这是不可接受的。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **应用层协议** | 在 WebSocket 之上自定义的消息格式和交互规则 |
| **消息四字段** | `type`（类型）+ `id`（去重/映射）+ `data`（业务）+ `ts`（时间） |
| **命名空间** | 用 `chat.message`、`room.join` 分组，避免类型冲突 |
| **ACK 确认** | 通过消息 ID 做请求-响应映射，超时未收到则重试 |
| **JSON 优先** | 90% 场景用 JSON，Protobuf 只在万级 QPS 场景才值得 |

---

## 5. 房间与频道模型

聊天应用的核心不是"一对一发消息"——而是"在一个房间里，多个人互相交流"。房间模型是 WebSocket 实时应用最核心的抽象，理解它就理解了 80% 的实时架构。

### 5.1 广播、组播、单播：三种推送模式

```
三种推送模式：

  广播（Broadcast）—— 发给所有在线用户
  ═══════════════════════════════════
  服务器 ──msg──▶ 用户 A
  服务器 ──msg──▶ 用户 B
  服务器 ──msg──▶ 用户 C
  服务器 ──msg──▶ 用户 D
  
  → 系统公告、全站维护通知
  
  
  组播（Multicast）—— 发给某个房间的所有成员
  ═══════════════════════════════════
  房间 "room_001" 的成员：A, B, C
  
  服务器 ──msg──▶ 用户 A  ✅ 在房间里
  服务器 ──msg──▶ 用户 B  ✅ 在房间里
  服务器 ──msg──▶ 用户 C  ✅ 在房间里
  服务器          用户 D  ❌ 不在房间里，不发
  
  → 群聊消息、游戏房间内通信
  
  
  单播（Unicast）—— 发给某个特定用户
  ═══════════════════════════════════
  服务器 ──msg──▶ 用户 B  ✅ 只有 B 收到
  
  → 私聊消息、个人通知、踢人
```

| 模式 | 接收方 | 实现复杂度 | 典型场景 |
|:---|:---|:---|:---|
| **广播** | 所有连接 | 低（遍历 active_connections） | 系统公告 |
| **组播** | 房间成员 | 中（需要维护房间-成员映射） | 群聊、协作文档 |
| **单播** | 特定用户 | 中（需要 user_id → connection 映射） | 私聊、个人推送 |

### 5.2 房间模型：数据结构与 Python 实现

房间模型需要维护两个核心映射：**房间 → 成员列表**，和 **用户 → 连接对象**。

```python
"""room_manager.py - 房间管理器"""
from fastapi import WebSocket
from collections import defaultdict

class RoomManager:
    """支持房间的连接管理器"""
    
    def __init__(self):
        # 房间 → 成员集合（user_id）
        self.rooms: dict[str, set[str]] = defaultdict(set)
        # 用户 → WebSocket 连接
        self.connections: dict[str, WebSocket] = {}
        # 用户 → 所在房间列表
        self.user_rooms: dict[str, set[str]] = defaultdict(set)
    
    async def connect(self, user_id: str, ws: WebSocket):
        """用户上线"""
        await ws.accept()
        self.connections[user_id] = ws
    
    def disconnect(self, user_id: str):
        """用户断开：清理所有房间和连接"""
        # 从所有房间中移除
        for room_id in self.user_rooms.get(user_id, set()):
            self.rooms[room_id].discard(user_id)
            if not self.rooms[room_id]:  # 房间空了就删除
                del self.rooms[room_id]
        self.user_rooms.pop(user_id, None)
        self.connections.pop(user_id, None)
    
    async def join_room(self, user_id: str, room_id: str):
        """加入房间"""
        self.rooms[room_id].add(user_id)
        self.user_rooms[user_id].add(room_id)
        # 通知房间内其他人
        await self.broadcast_to_room(
            room_id,
            {"type": "room.user_joined", "data": {"user": user_id}},
            exclude=user_id
        )
    
    async def leave_room(self, user_id: str, room_id: str):
        """离开房间"""
        self.rooms[room_id].discard(user_id)
        self.user_rooms[user_id].discard(room_id)
        await self.broadcast_to_room(
            room_id,
            {"type": "room.user_left", "data": {"user": user_id}}
        )
    
    async def broadcast_to_room(
        self, room_id: str, message: dict, exclude: str = None
    ):
        """组播：发送消息给房间内所有成员"""
        import json
        text = json.dumps(message)
        for user_id in self.rooms.get(room_id, set()):
            if user_id == exclude:
                continue
            ws = self.connections.get(user_id)
            if ws:
                try:
                    await ws.send_text(text)
                except Exception:
                    pass  # 发送失败的连接在 disconnect 时清理
    
    async def send_to_user(self, user_id: str, message: dict):
        """单播：发送消息给特定用户"""
        import json
        ws = self.connections.get(user_id)
        if ws:
            await ws.send_text(json.dumps(message))
```

> 💡 **为什么 `rooms` 用 `set` 而不是 `list`？** 因为加入/离开/查询成员都是 O(1) 操作。如果用 `list`，`remove()` 要 O(n) 遍历。一个 1000 人的房间，频繁的 join/leave 操作差距很大。
### 5.3 在线状态（Presence）：谁在房间里

在线状态（Presence）是实时应用的基础体验——"谁在线"、"房间里有几个人"、"谁正在打字"。

```python
"""presence.py - 在线状态查询"""

# 基于 RoomManager 扩展在线状态功能
class PresenceMixin:
    
    def get_room_members(self, room_id: str) -> list[str]:
        """获取房间内所有在线成员"""
        return list(self.rooms.get(room_id, set()))
    
    def get_online_count(self, room_id: str) -> int:
        """获取房间在线人数"""
        return len(self.rooms.get(room_id, set()))
    
    def is_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return user_id in self.connections
    
    async def broadcast_presence(self, room_id: str):
        """向房间广播最新的成员列表"""
        members = self.get_room_members(room_id)
        await self.broadcast_to_room(room_id, {
            "type": "room.members",
            "data": {
                "room": room_id,
                "members": members,
                "count": len(members)
            }
        })
```

**什么时候触发 Presence 更新？**

```
触发 Presence 广播的事件：

  用户加入房间  → 广播 room.members（含新加入的人）
  用户离开房间  → 广播 room.members（不含离开的人）
  用户断线      → 从所有房间移除 → 广播各房间的 room.members
  
  优化：
  → 不要每次有人上下线就广播完整列表
  → 改为增量更新：只发 "user_joined" / "user_left" 事件
  → 客户端本地维护成员列表，根据事件增删
  → 定期（每 30 秒）发一次完整列表做"校准"
```

> 💡 **Presence 的开销问题**：一个 500 人的群，每次有人进出都广播完整成员列表，就是 500 × 500 个用户名 = 25 万个字符串。必须用增量更新（只发 join/leave 事件），定期全量校准。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **广播/组播/单播** | 发给所有人 / 发给房间成员 / 发给特定用户 |
| **三层映射** | rooms（房间→成员）+ connections（用户→WS）+ user_rooms（用户→房间） |
| **set 而非 list** | 成员集合用 set，join/leave 均 O(1) |
| **Presence** | 在线状态通过 join/leave 增量事件 + 定期全量校准实现 |
| **disconnect 清理** | 断线时必须从所有房间移除并广播状态变更 |

---

## 6. 心跳、重连与断线恢复

WebSocket 连接不是"建完就一劳永逸"的——网络会抖、手机会锁屏、NAT 会超时、服务器会重启。一个没有心跳和重连机制的实时应用，用户体验会非常糟糕。

### 6.1 应用层心跳：为什么不能依赖 TCP Keepalive

```
TCP Keepalive 的三个致命问题：

  问题 1：默认间隔太长
  ═══════════════════════════════════
  Linux 默认 tcp_keepalive_time = 7200 秒（2 小时！）
  → 用户断网 2 小时后你才发现——早已超出业务容忍度
  
  问题 2：NAT/防火墙会杀连接
  ═══════════════════════════════════
  家用路由器 NAT 表项通常 5 分钟超时
  → 5 分钟没数据 → NAT 表项被删 → 连接被静默断开
  → TCP Keepalive 2 小时才发 → 早被 NAT 杀了
  → 服务器还以为连接活着 → 僵尸连接
  
  问题 3：检测粒度太粗
  ═══════════════════════════════════
  TCP Keepalive 只能检测"TCP 连接是否存活"
  → 不能检测"应用层是否正常"
  → 进程死锁了但 TCP 连接还在 → Keepalive 检测正常
```

**应用层心跳实现（服务端）：**

```python
"""heartbeat.py - 服务端心跳检测"""
import asyncio
import time

async def heartbeat_loop(ws, user_id: str, interval: int = 30):
    """
    后台协程：定期发 Ping，检测客户端是否存活
    与 receive 消息循环并行运行
    """
    while True:
        await asyncio.sleep(interval)
        try:
            # 发送应用层 Ping（不是 WebSocket 协议层的 Ping）
            await ws.send_text('{"type": "sys.ping", "ts": %d}' % int(time.time()))
        except Exception:
            break  # 发送失败 → 连接已死

# 在 WebSocket 端点中并行启动心跳
@app.websocket("/ws/{user_id}")
async def ws_endpoint(ws: WebSocket, user_id: str):
    await manager.connect(user_id, ws)
    
    # 🔥 并行运行：消息循环 + 心跳检测
    heartbeat_task = asyncio.create_task(heartbeat_loop(ws, user_id))
    
    try:
        while True:
            data = await ws.receive_text()
            await handle_message(ws, data)
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        manager.disconnect(user_id)
```

**推荐的心跳参数：**

| 参数 | 推荐值 | 原因 |
|:---|:---|:---|
| **心跳间隔** | 25-30 秒 | 小于 NAT 超时（通常 60 秒），大于网络抖动恢复时间 |
| **超时判定** | 连续 2 次无 Pong | 一次没回可能是网络抖动，连续 2 次基本确定断线 |
| **客户端超时** | 心跳间隔 × 2 + 5 秒 | 65 秒没收到服务器消息 → 认为断线，触发重连 |

### 6.2 客户端重连策略：指数退避与状态机

断线后立刻重连？如果服务器宕机了，1000 个客户端同时重连就是 DDoS。必须用**指数退避 + 抖动**打散重连时间。

```
客户端连接状态机：

  ┌──────────────┐
  │ Disconnected │ ◀──── 初始状态 / 连接失败
  └──────┬───────┘
         │ connect()
         ▼
  ┌──────────────┐    onopen     ┌───────────┐
  │ Connecting   │ ────────────▶ │ Connected │
  └──────┬───────┘               └─────┬─────┘
         │ 失败                        │ onclose / onerror
         ▼                             ▼
  ┌──────────────┐               ┌──────────────┐
  │    Failed    │ ◀──── 超过   │ Reconnecting │
  │  (放弃重连)  │   最大重试   └──────┬───────┘
  └──────────────┘    次数             │
                                       │ 等待退避时间后
                                       │ 重新 connect()
                                       ▼
                                ┌──────────────┐
                                │ Connecting   │ → 循环...
                                └──────────────┘
```

**JavaScript 客户端重连实现：**

```javascript
/** reconnecting_ws.js - 带自动重连的 WebSocket 客户端 */
class ReconnectingWebSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.maxRetries = options.maxRetries || 10;
    this.baseDelay = options.baseDelay || 1000;   // 初始等待 1 秒
    this.maxDelay = options.maxDelay || 30000;     // 最大等待 30 秒
    this.retryCount = 0;
    this.state = 'disconnected';
    this.connect();
  }
  
  connect() {
    this.state = 'connecting';
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      this.state = 'connected';
      this.retryCount = 0;  // 🔥 连接成功，重置重试计数
      console.log('WebSocket 已连接');
    };
    
    this.ws.onclose = (event) => {
      if (event.code === 1000) return; // 正常关闭，不重连
      this.scheduleReconnect();
    };
    
    this.ws.onerror = () => {
      this.ws.close(); // 触发 onclose → 进入重连
    };
  }
  
  scheduleReconnect() {
    if (this.retryCount >= this.maxRetries) {
      this.state = 'failed';
      console.error('重连失败，已达到最大重试次数');
      return;
    }
    
    this.state = 'reconnecting';
    
    // 指数退避 + 抖动
    const delay = Math.min(
      this.baseDelay * Math.pow(2, this.retryCount),
      this.maxDelay
    );
    const jitter = delay * 0.5 * Math.random();  // 0-50% 随机抖动
    const finalDelay = delay + jitter;
    
    console.log(`第 ${this.retryCount + 1} 次重连，等待 ${(finalDelay/1000).toFixed(1)}s`);
    this.retryCount++;
    
    setTimeout(() => this.connect(), finalDelay);
  }
}
```

> 💡 **`retryCount = 0` 的位置很关键**——必须在 `onopen`（连接成功）时重置，不是在 `connect()` 时。否则断线后第一次重连就重置了计数器，失去了退避效果。
### 6.3 断线恢复：离线消息队列与消息补推

重连解决了"恢复连接"的问题，但没解决"断线期间错过的消息怎么办"。

```
断线期间的消息丢失：

  时间线：
  ══════════════════════════════════════════════════
  t1: 用户 A 在线，收到消息 msg_001, msg_002
  t2: 用户 A 断线（网络切换 / 手机锁屏）
  t3: 房间里发了 msg_003, msg_004, msg_005  ← A 错过了！
  t4: 用户 A 重连成功
  
  问题：A 永远看不到 msg_003 ~ msg_005
  
  解决方案：离线消息队列 + 补推
  ══════════════════════════════════════════════════
  1. 每条消息都有递增 ID（msg_001, msg_002, ...）
  2. 客户端记住最后收到的 ID（last_seen_id = msg_002）
  3. 重连后发送：{"type": "sys.resume", "data": {"last_seen": "msg_002"}}
  4. 服务器查询 msg_002 之后的所有消息，一次性推送
```

**Python 服务端消息补推（基于 Redis）：**

```python
"""message_store.py - 基于 Redis 的消息存储与补推"""
import redis.asyncio as redis
import json

r = redis.Redis()

async def store_room_message(room_id: str, message: dict):
    """存储消息到 Redis（保留最近 1000 条）"""
    await r.zadd(
        f"room:{room_id}:messages",
        {json.dumps(message): message["ts"]}  # 按时间戳排序
    )
    # 只保留最近 1000 条
    await r.zremrangebyrank(f"room:{room_id}:messages", 0, -1001)

async def get_missed_messages(
    room_id: str, last_seen_ts: int
) -> list[dict]:
    """获取用户断线后错过的消息"""
    raw_messages = await r.zrangebyscore(
        f"room:{room_id}:messages",
        min=last_seen_ts + 1,  # 从上次看到的时间戳之后
        max="+inf"
    )
    return [json.loads(m) for m in raw_messages]
```

**补推策略对比：**

| 方案 | 实现复杂度 | 存储成本 | 适用场景 |
|:---|:---|:---|:---|
| **不补推** | 无 | 无 | 实时仪表盘（错过就算了） |
| **Redis ZSET** | 低 | 中（内存） | 聊天室（保留最近 N 条） |
| **数据库查询** | 中 | 低（磁盘） | 需要永久历史记录 |

> 💡 **不是所有消息都需要补推**。在线状态变更、打字提示——这些"时效性消息"断线后就没意义了。只有聊天内容、系统通知等"必达消息"才需要存储和补推。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **应用层心跳** | 25-30 秒间隔，解决 NAT 超时和僵尸连接问题 |
| **TCP Keepalive 不够** | 默认 2 小时太慢、不穿 NAT、不检测应用层死锁 |
| **指数退避 + 抖动** | 防止大量客户端同时重连造成 DDoS，retryCount 在 onopen 时重置 |
| **连接状态机** | Disconnected → Connecting → Connected → Reconnecting → Failed |
| **离线补推** | 客户端报告 last_seen_id，服务器查询并推送遗漏消息 |

---

## 7. 认证与安全

HTTP API 的认证很简单——`Authorization: Bearer <token>` 放在请求头里就行。但 WebSocket 不行——浏览器的 `new WebSocket(url)` API **不允许你设置自定义 HTTP Header**。这一章解决"WebSocket 怎么认证"以及"怎么防止被滥用"。

### 7.1 WebSocket 认证的特殊性

```
为什么 WebSocket 认证和 HTTP 不一样？

  HTTP API 认证：
  ═══════════════════════════════════
  fetch('/api/data', {
    headers: { 'Authorization': 'Bearer eyJhbG...' }
  })
  → 每个请求都带 Token → 服务器每次都验证
  → 无状态，简单优雅
  
  
  WebSocket 的困境：
  ═══════════════════════════════════
  // ❌ 浏览器不支持！没有 headers 参数！
  new WebSocket('ws://server/ws', {
    headers: { 'Authorization': 'Bearer ...' }  // 不存在这个 API
  })
  
  // 能设置的只有：
  new WebSocket('ws://server/ws')         // URL
  new WebSocket('ws://server/ws', ['v1']) // 子协议（不是用来传 Token 的）
  
  限制：
  1. 浏览器 WebSocket API 不能设自定义 Header
  2. 握手是 HTTP 请求，但你控制不了这个 HTTP 请求的 Header
  3. 连接建立后只有数据帧，没有 HTTP Header 概念了
```

> 💡 **注意**：非浏览器环境（Python `websockets` 库、Node.js `ws` 库）可以自由设置 Header。这个限制只存在于浏览器端。但作为后端开发者，你必须为"最受限的客户端"设计方案。

### 7.2 三种认证方案：Query Param / 首条消息 / Cookie

**方案 1：URL Query Param 传 Token（最常用）**

```python
"""auth_query.py - URL 参数认证"""

# 客户端：new WebSocket('ws://server/ws?token=eyJhbG...')

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket, token: str = Query(...)):
    # 握手前验证 Token
    try:
        user = verify_jwt(token)
    except InvalidToken:
        await ws.close(code=1008)  # Policy Violation
        return
    
    await ws.accept()
    # 认证通过，正常通信...
```

```
优点：简单、所有环境通用
缺点：Token 出现在 URL 中 → 会被日志记录、被 Referer 泄露
缓解：用短生命周期 Token（30 秒过期），专门为 WS 握手生成
```

**方案 2：首条消息认证（最安全）**

```python
"""auth_first_msg.py - 首条消息认证"""

# 客户端连接后，第一条消息发 Token

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()  # 先接受连接
    
    # 等待认证消息（5 秒超时）
    try:
        raw = await asyncio.wait_for(ws.receive_text(), timeout=5.0)
        msg = json.loads(raw)
        if msg["type"] != "auth":
            await ws.close(code=1008)
            return
        user = verify_jwt(msg["data"]["token"])
    except (asyncio.TimeoutError, InvalidToken):
        await ws.close(code=1008)
        return
    
    # 认证通过，进入消息循环...
```

```
优点：Token 不暴露在 URL 中，更安全
缺点：连接先建立再认证 → 短暂的"未认证连接"窗口
缓解：设置短超时（5 秒），超时未认证立刻关闭
```

**方案 3：Cookie 认证（与 Web 应用共享会话）**

```python
"""auth_cookie.py - Cookie 认证"""

# 浏览器已通过 HTTP 登录，拿到了 session Cookie
# WebSocket 握手时自动带上同域 Cookie

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    session_id = ws.cookies.get("session_id")
    if not session_id or not validate_session(session_id):
        await ws.close(code=1008)
        return
    
    await ws.accept()
    # ...
```

**三方案对比：**

| 方案 | 安全性 | 实现复杂度 | 跨域支持 | 推荐场景 |
|:---|:---|:---|:---|:---|
| **Query Param** | 中（URL 泄露风险） | 低 | ✅ | 移动端/第三方客户端 |
| **首条消息** | 高 | 中 | ✅ | 安全要求高的应用 |
| **Cookie** | 高 | 低 | ❌ 同域 | Web 应用内嵌 WS |

> 💡 **推荐组合**：Query Param + 短期 Token。先通过 HTTP API 用正式认证获取一个 30 秒有效的"WS 专用 Token"，再把它放在 URL 里。这样即使 URL 被日志记录，Token 很快过期也不会有安全问题。
### 7.3 安全防护：WSS、限流与防滥用

**WSS（WebSocket Secure）：必须用 TLS**

```
生产环境必须用 wss://（不是 ws://）

  ws://  = 明文传输 → 中间人可以窃听/篡改所有消息
  wss:// = TLS 加密 → 和 HTTPS 一样安全

  配置方式：通常在 Nginx 层做 TLS 终结
  → 客户端连 wss://yourdomain.com/ws
  → Nginx 解密后用 ws:// 转发给后端
  → 后端不需要处理 TLS
```

**WebSocket 消息限流（防刷屏/攻击）：**

```python
"""ws_ratelimit.py - 消息频率限制"""
import time
from collections import defaultdict

class MessageRateLimiter:
    """滑动窗口限流：每个用户每分钟最多 60 条消息"""
    
    def __init__(self, max_messages: int = 60, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window = window_seconds
        self.user_messages: dict[str, list[float]] = defaultdict(list)
    
    def allow(self, user_id: str) -> bool:
        now = time.time()
        timestamps = self.user_messages[user_id]
        
        # 清除窗口外的记录
        self.user_messages[user_id] = [
            ts for ts in timestamps if now - ts < self.window
        ]
        
        if len(self.user_messages[user_id]) >= self.max_messages:
            return False  # 限流
        
        self.user_messages[user_id].append(now)
        return True  # 放行

limiter = MessageRateLimiter()

# 在消息处理中使用
if not limiter.allow(user_id):
    await ws.send_text('{"type":"sys.error","data":{"error":"发送太频繁"}}')
    return
```

**防滥用安全清单：**

| 防护项 | 措施 | 原因 |
|:---|:---|:---|
| **消息大小** | 限制单条消息 ≤ 64KB | 防止内存耗尽攻击 |
| **消息频率** | 每人每分钟 ≤ 60 条 | 防刷屏、防攻击 |
| **连接数** | 每 IP ≤ 10 个 WS 连接 | 防资源耗尽 |
| **Origin 检查** | 只允许来自你域名的连接 | 防跨站 WebSocket 劫持（CSWSH） |
| **输入校验** | 所有消息 JSON 解析 + Schema 校验 | 防注入、防格式错误 |

> 💡 **跨站 WebSocket 劫持（CSWSH）** 是一个被低估的攻击——恶意网站可以用用户浏览器的 Cookie 建立 WebSocket 连接到你的服务器（因为浏览器自动带 Cookie）。必须在服务端检查 `Origin` 头，只接受来自你域名的连接。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **浏览器限制** | `new WebSocket()` 不能设自定义 Header，只能用 URL/Cookie |
| **Query Param + 短期 Token** | 最实用的认证方案，30 秒过期缓解 URL 泄露风险 |
| **首条消息认证** | 最安全但复杂度稍高，需设 5 秒认证超时 |
| **WSS 加密** | 生产必须用 `wss://`，Nginx 做 TLS 终结 |
| **CSWSH** | 检查 Origin 头，防止恶意网站用用户 Cookie 建立连接 |

---

## 8. 水平扩展：多实例部署

前面章节的所有代码都跑在一台服务器上——`ConnectionManager` 用一个 Python dict 管理所有连接。当用户量增长到一台服务器撑不住时怎么办？这章解决 WebSocket 水平扩展的核心难题：**跨实例消息路由**。

### 8.1 单实例瓶颈：一台服务器能撑多少连接

```
单实例 WebSocket 连接数上限估算：

  每个 WebSocket 连接的开销：
  ═══════════════════════════════════
  TCP 连接      → ~3.4KB 内核内存
  应用层缓冲区  → ~8KB（读写各 4KB）
  Python 对象   → ~2KB（WebSocket 对象、用户信息）
  合计：~14KB / 连接

  一台 8GB 内存的服务器：
  → 系统 + Python 进程占 2GB
  → 剩余 6GB 用于连接
  → 6GB / 14KB ≈ 430,000 个连接（理论上限）
  
  但实际受限于：
  → 文件描述符：默认 ulimit -n = 1024（需调高）
  → CPU：消息处理、JSON 解析、广播遍历
  → 实际安全值：单实例 5 万 ~ 10 万连接
```

**当你需要超过 10 万连接时，就必须多实例部署。但多实例有一个核心问题：**

```
多实例的困境：

  实例 A 管理连接：用户 1, 2, 3
  实例 B 管理连接：用户 4, 5, 6

  用户 1 在房间 "lobby" 发了一条消息
  → 实例 A 的 ConnectionManager 只知道用户 1, 2, 3
  → 用户 4, 5 也在 "lobby" 但在实例 B 上
  → 用户 4, 5 收不到消息！❌
  
  根本原因：
  → 每个实例的 ConnectionManager 是独立的
  → 跨实例的连接互相不可见
```

### 8.2 Redis Pub/Sub：跨实例消息路由

解决方案：用 **Redis Pub/Sub 作为消息总线**，所有实例都订阅同一个 Channel。

```
Redis Pub/Sub 架构：

  用户 1 (实例 A) 发消息到 "lobby"
       │
       ▼
  实例 A 收到消息
       │ PUBLISH room:lobby "用户1: hello"
       ▼
  ┌─────────┐
  │  Redis   │ ← 所有实例都订阅了 room:lobby
  └────┬────┘
       │
  ┌────┼────────────┐
  │    │            │
  ▼    ▼            ▼
实例 A          实例 B          实例 C
遍历本地连接    遍历本地连接    遍历本地连接
→ 发给 2, 3    → 发给 4, 5    → 发给 6
```

**Python 实现：**

```python
"""redis_pubsub.py - 基于 Redis 的跨实例消息路由"""
import redis.asyncio as redis
import json
import asyncio

r = redis.Redis()

class DistributedRoomManager(RoomManager):
    """在 RoomManager 基础上增加 Redis Pub/Sub"""
    
    async def publish_to_room(self, room_id: str, message: dict):
        """发布消息到 Redis（所有实例都能收到）"""
        await r.publish(
            f"room:{room_id}",
            json.dumps(message)
        )
    
    async def subscribe_loop(self):
        """后台任务：监听 Redis 订阅，转发给本地连接"""
        pubsub = r.pubsub()
        await pubsub.psubscribe("room:*")  # 订阅所有房间
        
        async for msg in pubsub.listen():
            if msg["type"] != "pmessage":
                continue
            
            # room:lobby → lobby
            room_id = msg["channel"].decode().split(":", 1)[1]
            message = json.loads(msg["data"])
            
            # 只发给本实例上的连接
            await self.broadcast_to_room(room_id, message)
```

> 💡 **Pub/Sub 的本质**：不是替代 ConnectionManager，而是在多个 ConnectionManager 之间建一座桥。每个实例仍然管理自己的本地连接，Redis 只负责"把消息复制到每个实例"。

### 8.3 Sticky Session vs 消息总线：两种扩展架构

```
方案对比：

  Sticky Session（会话粘滞）：
  ═══════════════════════════════════
  负载均衡器按 user_id 哈希，同一用户永远路由到同一实例
  
  客户端 ──▶ Nginx (hash $user_id) ──▶ 实例 A（固定）
  
  优点：
  → 不需要 Redis 消息总线
  → 同一用户的所有连接在一台机器上，本地操作即可
  
  缺点：
  → 某实例宕机 → 该实例上所有用户都断线
  → 负载不均匀（热门用户集中在某实例）
  → 扩缩容时需要重新映射（一致性哈希可缓解）
  
  
  Redis 消息总线（推荐）：
  ═══════════════════════════════════
  负载均衡器随机分配，消息通过 Redis Pub/Sub 跨实例同步
  
  客户端 ──▶ Nginx (随机/轮询) ──▶ 任意实例
  实例间通过 Redis 同步消息
  
  优点：
  → 任意实例可服务任意用户，无状态
  → 扩缩容简单（加实例即可）
  → 单实例宕机只影响其上连接，重连后自动迁移
  
  缺点：
  → Redis 成为单点（需要 Redis Sentinel/Cluster）
  → 每条消息多一跳 Redis 延迟（通常 < 1ms）
```

| 方案 | 扩缩容 | 容灾 | 实现复杂度 | 推荐 |
|:---|:---|:---|:---|:---|
| **Sticky Session** | 复杂（需重映射） | 差 | 低 | 小规模（< 5 实例） |
| **Redis Pub/Sub** | 简单（加实例） | 好 | 中 | ✅ 中大规模 |
| **Kafka/NATS** | 简单 | 最好 | 高 | 超大规模（> 100 万连接） |

> 💡 **绝大多数项目用 Redis Pub/Sub 就够了**。只有当 Pub/Sub 的"即发即忘"语义不能满足需求（需要消息持久化、重放），才考虑 Kafka 或 NATS。
### 8.4 连接数监控与自动扩缩容

**关键监控指标：**

```python
"""ws_metrics.py - WebSocket 监控指标"""
from prometheus_client import Gauge, Counter

# 当前活跃连接数
ws_connections_active = Gauge(
    'ws_connections_active', 
    '当前活跃 WebSocket 连接数',
    ['instance']
)

# 连接总数（累计）
ws_connections_total = Counter(
    'ws_connections_total',
    'WebSocket 连接总数',
    ['instance', 'status']  # status: connected / disconnected
)

# 消息吞吐量
ws_messages_total = Counter(
    'ws_messages_total',
    'WebSocket 消息总数',
    ['direction']  # direction: inbound / outbound
)

# 在 connect/disconnect 时更新
async def connect(self, user_id, ws):
    await ws.accept()
    ws_connections_active.labels(instance='ws-01').inc()
    ws_connections_total.labels(instance='ws-01', status='connected').inc()
```

**扩缩容策略：**

| 指标 | 扩容阈值 | 缩容阈值 | 说明 |
|:---|:---|:---|:---|
| **连接数** | > 5 万 / 实例 | < 1 万 / 实例 | 主要指标 |
| **CPU 使用率** | > 70% | < 20% | 消息处理密集时关注 |
| **消息延迟** | P99 > 50ms | — | 延迟升高说明处理不过来 |

> 💡 **WebSocket 扩缩容比 HTTP 更复杂**——缩容时不能直接关实例，因为断线会影响用户体验。正确的做法：先标记实例为"draining"，不接受新连接，等现有连接自然断开或迁移后再关闭。

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **单实例上限** | Python 实际安全值 5-10 万连接，瓶颈在文件描述符和 CPU |
| **多实例核心问题** | 跨实例连接不可见，需要消息总线同步 |
| **Redis Pub/Sub** | 推荐方案，每个实例订阅房间 Channel，收到后本地广播 |
| **Sticky vs 总线** | 小规模用 Sticky Session，中大规模用 Redis 总线 |
| **优雅缩容** | 先 draining（不接新连接），等旧连接迁移后再关实例 |

---

## 9. 性能优化与生产部署

开发环境能跑和生产环境能扛是两回事。这一章解决"怎么让 WebSocket 在生产环境稳定运行"——Nginx 配置、操作系统调优、优雅关机。

### 9.1 Nginx 反向代理 WebSocket 配置

WebSocket 通过 Nginx 代理是最常见的生产部署方式。但 Nginx 默认不转发 WebSocket 的 `Upgrade` 头——这是新手踩坑第一名。

**完整的 Nginx WebSocket 配置：**

```nginx
# /etc/nginx/conf.d/websocket.conf

upstream ws_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    # 多实例负载均衡
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # WebSocket 路由
    location /ws/ {
        proxy_pass http://ws_backend;
        proxy_http_version 1.1;
        
        # 🔥 关键：这两行不加，WebSocket 握手会失败！
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 透传客户端信息
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 🔥 关键：默认 60 秒没数据就断连，必须调大
        proxy_read_timeout 3600s;   # 1 小时
        proxy_send_timeout 3600s;
        
        # 关闭缓冲（WebSocket 消息不需要缓冲）
        proxy_buffering off;
    }
    
    # 普通 HTTP API 路由
    location /api/ {
        proxy_pass http://ws_backend;
    }
}
```

**常见踩坑：**

| 问题 | 原因 | 解决 |
|:---|:---|:---|
| 握手 400 | 缺少 `proxy_set_header Upgrade` | 加上两行 Upgrade 头转发 |
| 60 秒后自动断连 | `proxy_read_timeout` 默认 60s | 调大到 3600s + 配合应用层心跳 |
| 客户端拿不到真实 IP | Nginx 没传 `X-Real-IP` | 加 `proxy_set_header X-Real-IP` |
| WSS 证书错误 | Nginx SSL 配置问题 | 确认证书路径和域名匹配 |

> 💡 **`proxy_read_timeout` 和心跳的关系**：即使你设了 3600 秒超时，也必须有应用层心跳（第 6 章的 30 秒间隔）。心跳让 Nginx 知道"这个连接还活着"，超时只是最后一道保护。

### 9.2 操作系统调优：突破连接数上限

默认的 Linux 配置只允许 1024 个文件描述符——每个 WebSocket 连接占 1 个 fd，超过就报 "Too many open files"。

**必做的系统调优：**

```bash
# 1. 调高文件描述符限制
# 临时生效
ulimit -n 65535

# 永久生效：编辑 /etc/security/limits.conf
# *    soft    nofile    65535
# *    hard    nofile    65535

# 2. 调高系统级 fd 上限
sysctl -w fs.file-max=2000000

# 3. 调高 TCP 参数
sysctl -w net.core.somaxconn=65535        # 监听队列上限
sysctl -w net.ipv4.tcp_max_syn_backlog=65535   # SYN 队列

# 4. 调高端口范围（作为客户端连接其他服务时）
sysctl -w net.ipv4.ip_local_port_range="1024 65535"

# 写入 /etc/sysctl.conf 永久生效
```

**Nginx 也要调：**

```nginx
# /etc/nginx/nginx.conf
worker_processes auto;  # 自动匹配 CPU 核数

events {
    worker_connections 65535;   # 默认 512，必须调高
    use epoll;                  # Linux 下用 epoll
    multi_accept on;
}
```

**调优清单：**

| 参数 | 默认值 | 推荐值 | 影响 |
|:---|:---|:---|:---|
| `ulimit -n` | 1024 | 65535+ | 进程能打开的 fd 数 |
| `fs.file-max` | 65535 | 2000000 | 系统级 fd 上限 |
| `somaxconn` | 128 | 65535 | TCP 监听队列长度 |
| `worker_connections` | 512 | 65535 | Nginx 单 worker 连接数 |

> 💡 **别忘了 Uvicorn 的 worker 数**：`uvicorn app:app --workers 4` 启动 4 个进程。每个 worker 独立持有连接，所以 4 个 worker × 5 万连接 = 单机 20 万连接理论容量。
### 9.3 监控指标与优雅关机

**WebSocket 专属监控维度（配合第 8 章的 Prometheus 指标）：**

| 维度 | 指标 | 告警阈值 |
|:---|:---|:---|
| **连接** | 活跃连接数、连接/断开速率 | 连接数 > 容量 80% |
| **消息** | 入站/出站消息 QPS、消息大小分布 | QPS 异常波动 > 200% |
| **延迟** | 消息处理 P99、Redis Pub/Sub 延迟 | P99 > 50ms |
| **错误** | Close 1006 比例、认证失败率 | 1006 > 5% |
| **房间** | 活跃房间数、房间平均人数 | — |

**优雅关机（Graceful Shutdown）：**

```python
"""graceful_shutdown.py - 优雅关机"""
import signal
import asyncio

is_shutting_down = False

async def graceful_shutdown(app):
    """收到 SIGTERM 时优雅关闭所有连接"""
    global is_shutting_down
    is_shutting_down = True
    
    # 1. 通知所有客户端"服务器要关了"
    for user_id, ws in manager.connections.items():
        try:
            await ws.send_text('{"type":"sys.shutdown","data":{"reason":"server_restart"}}')
            await ws.close(code=1001)  # Going Away
        except Exception:
            pass
    
    # 2. 等待所有连接关闭（最多 10 秒）
    for _ in range(10):
        if not manager.connections:
            break
        await asyncio.sleep(1)
    
    print(f"优雅关机完成，剩余连接：{len(manager.connections)}")

# 注册信号处理
@app.on_event("shutdown")
async def on_shutdown():
    await graceful_shutdown(app)
```

```
优雅关机的关键：

  1. 收到 SIGTERM → 标记 is_shutting_down = True
  2. 不再接受新连接
  3. 向所有客户端发 sys.shutdown 消息 + Close 1001
  4. 客户端收到 1001 后重连到其他实例（不会显示"断线"）
  5. 等待所有连接清理完毕 → 进程退出
```

> 💡 **Close 1001（Going Away）** 是专门为服务器重启设计的状态码。客户端收到 1001 后应该立刻重连，且这次重连不需要指数退避——因为是服务器主动通知的。

**第 9 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Nginx 两行关键配置** | `proxy_set_header Upgrade` + `Connection "upgrade"` |
| **proxy_read_timeout** | 默认 60s，WebSocket 必须调大到 3600s |
| **ulimit -n** | 默认 1024，调到 65535+ 才能支撑万级连接 |
| **优雅关机** | 发 Close 1001 → 客户端自动重连到其他实例 → 无感知重启 |
| **is_shutting_down** | 关机期间拒绝新连接，让旧连接有序迁移 |

---

## 10. 实战：构建实时协作应用

前 9 章的知识串起来——用一个**多人实时聊天室**作为案例，提供 FastAPI 后端 + 原生 JS 前端的完整代码。每一步标注对应的章节知识。

### 10.1 需求分析与架构设计

```
功能需求：
═══════════════════════════════════
1. 用户输入昵称即可加入聊天室      → 第 7 章 认证
2. 支持多个房间，自由加入/离开      → 第 5 章 房间模型
3. 房间内消息实时广播               → 第 5 章 组播
4. 显示房间在线成员列表             → 第 5 章 Presence
5. 断线自动重连，不丢消息           → 第 6 章 心跳重连
6. 消息有类型区分                   → 第 4 章 消息协议

架构：
═══════════════════════════════════
  浏览器 (原生 WebSocket API)
       │ wss://
       ▼
  Nginx (TLS 终结 + Upgrade 透传)    → 第 9 章
       │ ws://
       ▼
  FastAPI + Uvicorn
  ├── ConnectionManager              → 第 3 章
  ├── RoomManager                    → 第 5 章
  ├── 心跳检测                       → 第 6 章
  └── 消息协议解析                    → 第 4 章
```

### 10.2 后端实现：FastAPI + Redis 全功能服务

```python
"""chat_server.py - 完整的实时聊天室后端"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from collections import defaultdict
import json
import time
import asyncio

app = FastAPI(title="实时聊天室")

# ========== 房间管理器（第 5 章）==========
class ChatRoomManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}
        self.rooms: dict[str, set[str]] = defaultdict(set)
        self.user_rooms: dict[str, set[str]] = defaultdict(set)
        self.usernames: dict[str, str] = {}
    
    async def connect(self, user_id: str, username: str, ws: WebSocket):
        await ws.accept()
        self.connections[user_id] = ws
        self.usernames[user_id] = username
    
    def disconnect(self, user_id: str):
        for room_id in list(self.user_rooms.get(user_id, set())):
            self.rooms[room_id].discard(user_id)
        self.user_rooms.pop(user_id, None)
        self.connections.pop(user_id, None)
        self.usernames.pop(user_id, None)
    
    async def join_room(self, user_id: str, room_id: str):
        self.rooms[room_id].add(user_id)
        self.user_rooms[user_id].add(room_id)
        username = self.usernames.get(user_id, "匿名")
        await self.send_to_room(room_id, {
            "type": "room.user_joined",
            "data": {"user": username, "room": room_id,
                     "members": self._get_members(room_id)},
            "ts": int(time.time())
        })
    
    async def leave_room(self, user_id: str, room_id: str):
        self.rooms[room_id].discard(user_id)
        self.user_rooms[user_id].discard(room_id)
        username = self.usernames.get(user_id, "匿名")
        await self.send_to_room(room_id, {
            "type": "room.user_left",
            "data": {"user": username, "room": room_id,
                     "members": self._get_members(room_id)},
            "ts": int(time.time())
        })
    
    async def send_to_room(self, room_id: str, message: dict, 
                           exclude: str = None):
        text = json.dumps(message, ensure_ascii=False)
        for uid in self.rooms.get(room_id, set()):
            if uid == exclude:
                continue
            ws = self.connections.get(uid)
            if ws:
                try:
                    await ws.send_text(text)
                except Exception:
                    pass
    
    def _get_members(self, room_id: str) -> list[str]:
        return [self.usernames.get(uid, "匿名") 
                for uid in self.rooms.get(room_id, set())]

manager = ChatRoomManager()

# ========== 消息路由（第 4 章）==========
async def handle_message(user_id: str, raw: str):
    msg = json.loads(raw)
    msg_type = msg.get("type")
    data = msg.get("data", {})
    
    if msg_type == "room.join":
        await manager.join_room(user_id, data["room"])
    
    elif msg_type == "room.leave":
        await manager.leave_room(user_id, data["room"])
    
    elif msg_type == "chat.message":
        username = manager.usernames.get(user_id, "匿名")
        await manager.send_to_room(data["room"], {
            "type": "chat.message",
            "data": {"sender": username, "content": data["content"],
                     "room": data["room"]},
            "ts": int(time.time())
        })
    
    elif msg_type == "sys.pong":
        pass  # 心跳响应，忽略

# ========== WebSocket 端点 ==========
@app.websocket("/ws/{username}")
async def ws_endpoint(ws: WebSocket, username: str):
    import uuid
    user_id = str(uuid.uuid4())[:8]
    await manager.connect(user_id, username, ws)
    
    # 并行启动心跳（第 6 章）
    async def heartbeat():
        while True:
            await asyncio.sleep(30)
            try:
                await ws.send_text(json.dumps({"type": "sys.ping",
                                               "ts": int(time.time())}))
            except Exception:
                break
    
    hb_task = asyncio.create_task(heartbeat())
    
    try:
        while True:
            raw = await ws.receive_text()
            await handle_message(user_id, raw)
    except WebSocketDisconnect:
        pass
    finally:
        hb_task.cancel()
        # 通知所有房间该用户离开
        for room_id in list(manager.user_rooms.get(user_id, set())):
            await manager.leave_room(user_id, room_id)
        manager.disconnect(user_id)
```

### 10.3 前端实现：原生 JS WebSocket 客户端

```javascript
/** chat_client.js - 带自动重连的聊天室客户端 */
class ChatClient {
  constructor(username) {
    this.username = username;
    this.url = `ws://${location.host}/ws/${username}`;
    this.retryCount = 0;
    this.maxRetries = 10;
    this.currentRoom = null;
    this.connect();
  }
  
  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('✅ 已连接');
      this.retryCount = 0;
      // 重连后自动重新加入房间（第 6 章）
      if (this.currentRoom) {
        this.joinRoom(this.currentRoom);
      }
    };
    
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      this.handleMessage(msg);
    };
    
    this.ws.onclose = (event) => {
      if (event.code === 1000) return;
      // 指数退避重连（第 6 章）
      const delay = Math.min(1000 * Math.pow(2, this.retryCount), 30000);
      const jitter = delay * 0.5 * Math.random();
      console.log(`🔄 ${(delay + jitter) / 1000}s 后重连...`);
      this.retryCount++;
      setTimeout(() => this.connect(), delay + jitter);
    };
  }
  
  // 消息路由（第 4 章）
  handleMessage(msg) {
    switch (msg.type) {
      case 'chat.message':
        console.log(`💬 [${msg.data.sender}]: ${msg.data.content}`);
        break;
      case 'room.user_joined':
        console.log(`👋 ${msg.data.user} 加入了房间，在线: ${msg.data.members}`);
        break;
      case 'room.user_left':
        console.log(`👋 ${msg.data.user} 离开了房间`);
        break;
      case 'sys.ping':
        // 回复心跳（第 6 章）
        this.ws.send(JSON.stringify({ type: 'sys.pong', ts: Date.now() }));
        break;
    }
  }
  
  joinRoom(roomId) {
    this.currentRoom = roomId;
    this.ws.send(JSON.stringify({ type: 'room.join', data: { room: roomId } }));
  }
  
  sendMessage(content) {
    this.ws.send(JSON.stringify({
      type: 'chat.message',
      data: { room: this.currentRoom, content }
    }));
  }
}

// 使用
const client = new ChatClient('小明');
client.joinRoom('lobby');
client.sendMessage('大家好！');
```

> 💡 **重连后自动 joinRoom**：这是容易被遗漏的关键细节。断线重连后，服务器不知道你之前在哪个房间——必须客户端主动重新加入。`currentRoom` 变量确保重连后能恢复到断线前的状态。
### 10.4 部署与压测：从开发到生产

**启动开发服务：**

```bash
# 安装依赖
pip install fastapi uvicorn[standard]

# 启动（开发模式）
uvicorn chat_server:app --reload --host 0.0.0.0 --port 8000

# 启动（生产模式，4 个 worker）
uvicorn chat_server:app --workers 4 --host 0.0.0.0 --port 8000
```

**WebSocket 压测（用 Python 脚本模拟并发连接）：**

```python
"""ws_benchmark.py - WebSocket 压测脚本"""
import asyncio
import websockets
import time
import json

async def simulate_user(user_id: int, room: str):
    uri = f"ws://localhost:8000/ws/user_{user_id}"
    async with websockets.connect(uri) as ws:
        # 加入房间
        await ws.send(json.dumps({"type": "room.join", "data": {"room": room}}))
        
        # 发 10 条消息
        for i in range(10):
            await ws.send(json.dumps({
                "type": "chat.message",
                "data": {"room": room, "content": f"消息 {i}"}
            }))
            await asyncio.sleep(0.1)
        
        # 保持连接 5 秒
        await asyncio.sleep(5)

async def main():
    start = time.time()
    # 模拟 100 个用户同时连接
    tasks = [simulate_user(i, "lobby") for i in range(100)]
    await asyncio.gather(*tasks)
    print(f"100 用户压测完成，耗时 {time.time()-start:.1f}s")

asyncio.run(main())
```

**生产部署清单：**

| 检查项 | 对应章节 | 状态 |
|:---|:---|:---|
| WSS 加密（Nginx TLS 终结） | 第 7、9 章 | ☐ |
| Nginx `proxy_set_header Upgrade` | 第 9 章 | ☐ |
| `proxy_read_timeout 3600s` | 第 9 章 | ☐ |
| `ulimit -n 65535` | 第 9 章 | ☐ |
| 应用层心跳（30 秒间隔） | 第 6 章 | ☐ |
| 客户端自动重连（指数退避） | 第 6 章 | ☐ |
| 消息协议有 type/id/data/ts | 第 4 章 | ☐ |
| Origin 检查（防 CSWSH） | 第 7 章 | ☐ |
| 消息限流（60 条/分钟） | 第 7 章 | ☐ |
| Prometheus 监控指标 | 第 8 章 | ☐ |
| 优雅关机（Close 1001） | 第 9 章 | ☐ |

---

**全书总结：WebSocket 开发 10 条军规**

1. **先试 SSE**——纯服务器推送不需要 WebSocket（第 1 章）
2. **理解协议**——Upgrade 握手、帧结构、Close 状态码，调试时救命（第 2 章）
3. **用 `finally` 清理**——无论如何退出都要清理连接，防止泄漏（第 3 章）
4. **设计应用层协议**——type/id/data/ts 四字段，别用裸 WebSocket（第 4 章）
5. **房间用 `set`**——join/leave O(1)，disconnect 时清理所有房间（第 5 章）
6. **心跳 30 秒**——不依赖 TCP Keepalive，防 NAT 超时和僵尸连接（第 6 章）
7. **认证用短期 Token**——Query Param + 30 秒有效期，缓解 URL 泄露（第 7 章）
8. **Redis Pub/Sub 扩展**——跨实例消息路由的标准方案（第 8 章）
9. **Nginx 两行必加**——`proxy_set_header Upgrade` + `Connection "upgrade"`（第 9 章）
10. **重连后恢复状态**——客户端记住 `currentRoom`，重连后自动 rejoin（第 10 章）

