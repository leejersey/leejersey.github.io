# A2A 协议实战指南：让 AI Agent 学会"团队协作"

> MCP 是 Agent 的"手"——让它能抓住工具。A2A 是 Agent 的"嘴"——让它能和其他 Agent 对话、分工、协作。两个协议组合起来，Agent 才真正从"单兵作战"进化为"团队作战"。

---

## 1. 为什么 Agent 需要一个通信协议

你用 LangGraph 搭了一个搜索 Agent，用 CrewAI 搭了一个分析 Agent，用 AutoGen 搭了一个代码 Agent。三个 Agent 各自表现优秀。但当你想让它们**协作完成一个复杂任务**时——搜索 Agent 找到数据，传给分析 Agent 做分析，再传给代码 Agent 生成可视化——你发现：**它们根本不会说话。**

### 1.1 多 Agent 系统的"巴别塔困境"

每个 Agent 框架都有自己的内部通信方式：

```
当前的困境：

  LangGraph Agent ──── 自己的 State 格式
  CrewAI Agent   ──── 自己的 Task 格式
  AutoGen Agent  ──── 自己的 Message 格式
  OpenAI Agent   ──── 自己的 Handoff 格式

  它们之间怎么通信？答案是：不能。
  
  除非你写大量胶水代码，手动转换格式。
```

这就像 2000 年代的手机充电器——每个品牌一种接口，Nokia 的线不能给 Motorola 充电。直到 USB-C 出现，一条线通吃所有设备。

**A2A 协议就是 Agent 世界的 USB-C。**

### 1.2 现有方案的局限：Function Calling ≠ Agent 协作

你可能想："用 Function Calling 不就行了？把另一个 Agent 封装成一个函数，调用它就好了。"

这在简单场景下可以，但面对真正的 Agent 协作，Function Calling 缺少三个关键能力：

| 需求 | Function Calling | A2A 协议 |
|------|-----------------|---------|
| 发现能力 | 手动写死函数定义 | Agent Card 自动发现 |
| 长时间任务 | 同步调用，必须等返回 | 异步任务 + 流式更新 |
| 多轮协商 | 一次调用一次返回 | input-required 暂停等待 |
| 框架无关 | 绑定特定框架 | HTTP 标准，任何框架通用 |

### 1.3 A2A 要解决的核心问题：发现、委派、协作

A2A 协议聚焦三个核心问题：

```
A2A 要解决的三个问题：

  ① 发现（Discovery）
     "我怎么知道哪个 Agent 能帮我完成这个子任务？"
     → Agent Card：每个 Agent 发布自己的能力描述

  ② 委派（Delegation）
     "我怎么把任务交给另一个 Agent？"
     → Task + Message：标准化的任务请求和响应格式

  ③ 协作（Collaboration）
     "任务进行到一半，我怎么跟踪进度、提供追加信息？"
     → SSE 流式更新 + input-required 多轮交互
```

> 💡 **核心洞察：** A2A 的设计哲学不是"发明新技术"，而是"用最成熟的 Web 标准来解决 Agent 通信问题"——HTTPS、JSON-RPC 2.0、SSE。所有 Web 开发者都会用，零学习成本。

---

## 2. A2A 协议全景：五分钟读懂核心设计

这一章用一张全景图把 A2A 的所有核心概念串起来。读完这章，你就知道 A2A"长什么样"。

### 2.1 一句话定义：Agent 间的 HTTP API 标准

**A2A = 一套基于 HTTPS + JSON-RPC 2.0 的开放协议，让不同框架的 AI Agent 能互相发现、委派任务和交换结果。**

由 Google 在 2025 年 4 月发布，随后移交 Linux 基金会管理，50+ 科技公司参与共建（包括 Salesforce、SAP、Atlassian 等）。

### 2.2 Client-Server 模型：谁发起、谁执行

A2A 的通信模型很简单——**谁发任务谁是 Client，谁做任务谁是 Server**：

```
A2A 通信模型：

  Client Agent（发起方）          Server Agent（执行方）
  ┌──────────────┐               ┌──────────────┐
  │ "帮我翻译    │  ── Task ──→  │  翻译 Agent   │
  │  这段文字"   │               │              │
  │              │  ←─ Result ── │  处理并返回   │
  └──────────────┘               └──────────────┘

  同一个 Agent 可以同时是 Client 和 Server：
  - 作为 Server：接收编排器的任务
  - 作为 Client：把子任务委派给其他 Agent
```

### 2.3 核心概念图谱：Agent Card → Task → Message → Artifact

A2A 协议由四个核心概念组成：

```
A2A 核心概念图谱：

  Agent Card          →    Task           →    Message       →    Artifact
  ┌──────────┐        ┌──────────────┐    ┌──────────────┐   ┌──────────┐
  │ 名片      │        │ 任务         │    │ 消息         │   │ 产出物    │
  │          │        │              │    │              │   │          │
  │ name     │  发现   │ id           │  包含 │ role        │ 附带│ type     │
  │ skills   │ ────→  │ status       │ ───→ │ content     │ ──→│ data     │
  │ endpoint │        │ messages[]   │    │ artifacts[] │   │ name     │
  │ auth     │        │ artifacts[]  │    │              │   │          │
  └──────────┘        └──────────────┘    └──────────────┘   └──────────┘
  "我是谁，           "做什么事，          "说了什么话，       "产出了什么
   我能做什么"          做到哪了"            附带了什么"         结果"
```

| 概念 | 作用 | 类比 |
|------|------|------|
| Agent Card | 描述 Agent 的能力和访问方式 | LinkedIn 个人主页 |
| Task | 一次任务的完整生命周期 | 一张工单 |
| Message | 任务中的一条消息（请求或回复） | 工单里的评论 |
| Artifact | 任务产出的结构化结果 | 工单的附件/交付物 |

### 2.4 与 MCP 的关系：垂直工具接入 vs 水平 Agent 协作

A2A 和 MCP **不是竞争关系，而是互补关系**——它们解决的是完全不同层面的问题：

```
协议分层：

  ┌──────────────────────────────────┐
  │  A2A 层（水平协作）               │
  │  Agent ↔ Agent                  │
  │  "帮我做这个子任务"               │
  └──────────┬───────────────────────┘
             │
  ┌──────────▼───────────────────────┐
  │  MCP 层（垂直工具接入）            │
  │  Agent ↔ Tool / Database / API   │
  │  "帮我查这个数据"                 │
  └──────────────────────────────────┘
```

| 维度 | MCP | A2A |
|------|-----|-----|
| 连接对象 | Agent ↔ 工具/数据源 | Agent ↔ Agent |
| 关系 | 上下级（Host → Tool） | 对等（Peer ↔ Peer） |
| 发现方式 | 工具清单（Tool Schema） | Agent Card（能力名片） |
| 任务模式 | 同步调用 | 同步 / 异步 / 流式 / 多轮 |
| 类比 | 员工使用办公软件 | 员工之间开会协作 |

> 💡 **一句话记住：** MCP 让 Agent 有"手"，A2A 让 Agent 有"嘴"。手用来操作工具，嘴用来和同事协作。一个完整的 Agent 系统两者都需要。

---

## 3. Agent Card：Agent 的"数字名片"

Agent Card 是 A2A 协议的**入口**——没有它，别的 Agent 就找不到你、不知道你能做什么、不知道怎么调你。

### 3.1 Agent Card 的完整 JSON 结构

```json
{
  "name": "翻译 Agent",
  "description": "支持 50+ 语言的专业翻译服务",
  "url": "https://translate-agent.example.com",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true
  },
  "skills": [
    {
      "id": "translate",
      "name": "文本翻译",
      "description": "将文本从源语言翻译为目标语言",
      "inputModes": ["text"],
      "outputModes": ["text"]
    },
    {
      "id": "detect-language",
      "name": "语言检测",
      "description": "自动检测文本的语言",
      "inputModes": ["text"],
      "outputModes": ["text"]
    }
  ],
  "authentication": {
    "schemes": ["Bearer"],
    "credentials": "OAuth 2.0 access token required"
  }
}
```

每个字段的作用：

| 字段 | 说明 | 必填 |
|------|------|------|
| `name` | Agent 的名称 | ✅ |
| `description` | Agent 的能力描述 | ✅ |
| `url` | Agent 的服务端点 | ✅ |
| `version` | 协议版本 | ✅ |
| `capabilities` | 支持的通信能力（流式/推送） | ✅ |
| `skills` | Agent 能做的事情列表 | ✅ |
| `authentication` | 认证方式 | 可选 |

### 3.2 Skills 定义：告诉世界你的 Agent 能做什么

Skills 是 Agent Card 中最重要的部分——它决定了**别的 Agent 会不会找你**：

```
Skills 的设计原则：

  ✅ 好的 Skills 定义：
     id: "translate"
     description: "将文本从源语言翻译为目标语言，
                   支持中/英/日/韩等 50+ 语言"
     → 具体、明确，别人一看就知道能不能用

  ❌ 差的 Skills 定义：
     id: "process"
     description: "处理文本"
     → 太模糊，别人不知道这能干嘛
```

### 3.3 发现机制：.well-known/agent.json 约定

A2A 借鉴了 Web 的 `.well-known` 标准——Agent Card 发布在固定路径：

```
发现流程：

  Client Agent 想找一个翻译 Agent
    ↓
  请求 GET https://translate-agent.example.com/.well-known/agent.json
    ↓
  返回 Agent Card JSON
    ↓
  Client 解析 skills，确认这个 Agent 能翻译
    ↓
  开始发送任务
```

这个设计和 OAuth 的 `.well-known/openid-configuration` 如出一辙——约定大于配置，零协商成本。

### 3.4 认证声明：OAuth 2.0 / API Key / mTLS

Agent Card 里的 `authentication` 字段告诉调用方"怎么证明你有权限"：

| 认证方式 | 场景 | 复杂度 |
|---------|------|-------|
| API Key | 内部 Agent 间调用 | ⭐ |
| Bearer Token (OAuth 2.0) | 企业级、跨组织调用 | ⭐⭐⭐ |
| mTLS | 高安全级别、金融/医疗 | ⭐⭐⭐⭐⭐ |

> 💡 **实用建议：** 起步阶段用 API Key 就够了。等你的 Agent 需要对外暴露服务时，再升级到 OAuth 2.0。不要在 MVP 阶段就上 mTLS，那是"大炮打蚊子"。

---

## 4. Task 生命周期：从请求到完成

Task 是 A2A 的核心数据对象——每一次"帮我做件事"都是一个 Task。理解 Task 的生命周期，就理解了 A2A 的运作方式。

### 4.1 Task 状态机：6 个状态的流转

```
Task 状态机：

  ┌─────────┐
  │submitted│ ← 刚创建，还没开始处理
  └────┬────┘
       ↓
  ┌────┴────┐
  │ working │ ← 正在处理中
  └────┬────┘
       ├──────────────────┐
       ↓                  ↓
  ┌────┴──────────┐  ┌───┴────────┐
  │input-required │  │ completed  │ ← 成功完成
  │ 需要更多信息   │  └────────────┘
  └────┬──────────┘
       ↓                  
  （Client 补充信息后）    
       → 回到 working      
                          ┌────────┐
  任何状态都可能跳转到 →  │ failed │ ← 执行失败
                          └────────┘
                          ┌──────────┐
  任何状态都可能跳转到 →  │ canceled │ ← 被取消
                          └──────────┘
```

| 状态 | 含义 | 触发条件 |
|------|------|---------|
| `submitted` | 任务已提交，等待处理 | Client 发送 message/send |
| `working` | 正在处理中 | Server 开始执行 |
| `input-required` | 需要 Client 提供更多信息 | Server 信息不足以继续 |
| `completed` | 任务成功完成 | Server 返回最终结果 |
| `failed` | 任务失败 | 执行出错 |
| `canceled` | 任务被取消 | Client 主动取消 |

### 4.2 同步任务：发送消息，立即返回结果

最简单的场景——发一个请求，立即得到结果：

```json
// Client 发送请求
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"text": "把 Hello World 翻译成中文"}]
    }
  },
  "id": "req-001"
}

// Server 立即返回
{
  "jsonrpc": "2.0",
  "result": {
    "id": "task-001",
    "status": {"state": "completed"},
    "artifacts": [{
      "parts": [{"text": "你好世界"}]
    }]
  },
  "id": "req-001"
}
```

### 4.3 异步任务：SSE 流式更新 + Push Notification

对于长时间任务（如深度研究、数据分析），A2A 支持两种异步模式：

**模式一：SSE 流式（Client 保持连接）**
```
Client ──── GET message/stream ────→ Server
       ←── event: status=working ────
       ←── event: artifact=部分结果 ──
       ←── event: artifact=更多结果 ──
       ←── event: status=completed ──
```

**模式二：Push Notification（Client 注册 Webhook）**
```
Client ──── POST message/send ────→ Server
       ←── 202 Accepted, taskId ────
       
       （Client 去做别的事）

Server ──── POST webhook/callback ──→ Client
             { taskId, status: completed, artifacts: [...] }
```

### 4.4 交互式任务：input-required 与多轮协商

最强大的场景——Server 做到一半，发现需要更多信息，**主动暂停并向 Client 请求输入**：

```
交互式任务流程：

  Client: "帮我翻译这篇文章"
  Server: status=working → "正在翻译..."
  Server: status=input-required → "这篇文章有多个专业术语，
          请确认以下翻译是否正确：
          - 'gradient descent' → '梯度下降' 还是 '梯度降低'？"
  Client: "用'梯度下降'"
  Server: status=working → "继续翻译..."
  Server: status=completed → "翻译完成" + 完整译文
```

> 💡 **核心价值：** `input-required` 状态让 A2A 支持**真正的 Agent 协商**——不是简单的"请求-响应"，而是像人类同事之间那样"做到一半，停下来讨论，达成共识后继续"。这是 Function Calling 永远做不到的。

---

## 5. 通信协议详解：JSON-RPC 2.0 + SSE

A2A 没有发明新的通信协议——它复用了三个成熟的 Web 标准：**HTTPS** 做传输、**JSON-RPC 2.0** 做消息格式、**SSE** 做流式推送。

### 5.1 JSON-RPC 2.0 消息格式

所有 A2A 通信都封装在 JSON-RPC 2.0 信封里：

```json
// 请求（Client → Server）
{
  "jsonrpc": "2.0",
  "method": "message/send",      // 方法名
  "params": { ... },             // 参数
  "id": "req-001"                // 请求 ID（用于匹配响应）
}

// 成功响应
{
  "jsonrpc": "2.0",
  "result": { ... },             // 结果
  "id": "req-001"                // 对应请求 ID
}

// 错误响应
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid request"
  },
  "id": "req-001"
}
```

### 5.2 核心方法：message/send、message/stream、tasks/get

A2A 定义了几个核心方法：

| 方法 | 说明 | 返回方式 |
|------|------|---------|
| `message/send` | 发送消息并等待结果 | 同步返回 Task |
| `message/stream` | 发送消息并流式接收 | SSE 事件流 |
| `tasks/get` | 查询任务状态 | 返回 Task 快照 |
| `tasks/cancel` | 取消任务 | 返回确认 |
| `tasks/pushNotification/set` | 注册 Webhook 回调 | 返回确认 |

### 5.3 SSE 流式通信：实时状态推送

当使用 `message/stream` 时，Server 通过 SSE（Server-Sent Events）推送更新：

```
SSE 事件格式：

  data: {"jsonrpc":"2.0","result":{
    "id":"task-001",
    "status":{"state":"working"},
    "artifacts":[]
  }}

  data: {"jsonrpc":"2.0","result":{
    "id":"task-001",
    "status":{"state":"working"},
    "artifacts":[{"parts":[{"text":"正在分析..."}]}]
  }}

  data: {"jsonrpc":"2.0","result":{
    "id":"task-001",
    "status":{"state":"completed"},
    "artifacts":[{"parts":[{"text":"分析完成，结论是..."}]}]
  }}
```

每个 `data:` 行就是一个完整的 JSON-RPC 响应——Client 只需要逐行解析即可。如果你之前做过 LLM 流式输出（参见《AI 应用的流式输出全链路》），这个模式你一定不陌生。

### 5.4 Push Notification：Webhook 回调机制

对于超长时间任务（几分钟到几小时），SSE 连接可能断开。这时用 Webhook：

```json
// Step 1：注册 Webhook
{
  "jsonrpc": "2.0",
  "method": "tasks/pushNotification/set",
  "params": {
    "taskId": "task-001",
    "pushNotificationConfig": {
      "url": "https://my-agent.com/webhook/a2a",
      "authentication": {
        "schemes": ["Bearer"],
        "credentials": "webhook-secret-token"
      }
    }
  }
}

// Step 2：Server 完成后，POST 到你的 Webhook
POST https://my-agent.com/webhook/a2a
{
  "taskId": "task-001",
  "status": {"state": "completed"},
  "artifacts": [{"parts": [{"text": "分析报告..."}]}]
}
```

> 💡 **选择建议：** 任务 < 30 秒用 `message/send`（同步）。任务 30 秒~5 分钟用 `message/stream`（SSE）。任务 > 5 分钟用 Push Notification（Webhook）。

---

## 6. 实战一：用 Python 构建 A2A Server

理论讲完了，**写代码**。本章用 FastAPI 从零实现一个 A2A 兼容的翻译 Agent 服务。

### 6.1 环境搭建与 a2a-sdk 安装

```bash
# 创建项目
mkdir a2a-translate-agent && cd a2a-translate-agent
python -m venv venv && source venv/bin/activate

# 安装依赖
pip install fastapi uvicorn httpx
pip install a2a-sdk            # Google 官方 A2A SDK
pip install langchain-openai   # LLM 调用
```

### 6.2 实现 Agent Card 端点

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

AGENT_CARD = {
    "name": "翻译 Agent",
    "description": "支持中英日韩等 50+ 语言的专业翻译服务",
    "url": "http://localhost:8000",
    "version": "1.0.0",
    "capabilities": {
        "streaming": True,
        "pushNotifications": False
    },
    "skills": [
        {
            "id": "translate",
            "name": "文本翻译",
            "description": "将文本从一种语言翻译为另一种语言",
            "inputModes": ["text"],
            "outputModes": ["text"]
        }
    ]
}

@app.get("/.well-known/agent.json")
async def get_agent_card():
    """暴露 Agent Card——这是 A2A 的入口"""
    return JSONResponse(content=AGENT_CARD)
```

### 6.3 实现 message/send 处理器

```python
from fastapi import Request
from langchain_openai import ChatOpenAI
import uuid

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

@app.post("/")
async def handle_jsonrpc(request: Request):
    """处理 JSON-RPC 2.0 请求"""
    body = await request.json()
    method = body.get("method")
    req_id = body.get("id")
    
    if method == "message/send":
        return await handle_message_send(body["params"], req_id)
    elif method == "message/stream":
        return await handle_message_stream(body["params"], req_id)
    else:
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
            "id": req_id
        })

async def handle_message_send(params: dict, req_id: str):
    """同步处理翻译请求"""
    user_text = params["message"]["parts"][0]["text"]
    
    # 调用 LLM 翻译
    result = llm.invoke(f"请翻译以下文本为中文：\n\n{user_text}")
    
    return JSONResponse(content={
        "jsonrpc": "2.0",
        "result": {
            "id": str(uuid.uuid4()),
            "status": {"state": "completed"},
            "artifacts": [{
                "parts": [{"text": result.content}]
            }]
        },
        "id": req_id
    })
```

### 6.4 实现 SSE 流式响应

```python
from fastapi.responses import StreamingResponse
import json, asyncio

async def handle_message_stream(params: dict, req_id: str):
    """流式处理翻译请求"""
    user_text = params["message"]["parts"][0]["text"]
    task_id = str(uuid.uuid4())
    
    async def event_generator():
        # 发送 working 状态
        yield f"data: {json.dumps({
            'jsonrpc': '2.0',
            'result': {
                'id': task_id,
                'status': {'state': 'working'},
                'artifacts': []
            }
        })}\n\n"
        
        # 流式调用 LLM
        chunks = []
        async for chunk in llm.astream(f"请翻译以下文本为中文：\n\n{user_text}"):
            chunks.append(chunk.content)
            yield f"data: {json.dumps({
                'jsonrpc': '2.0',
                'result': {
                    'id': task_id,
                    'status': {'state': 'working'},
                    'artifacts': [{'parts': [{'text': ''.join(chunks)}]}]
                }
            })}\n\n"
        
        # 发送 completed 状态
        yield f"data: {json.dumps({
            'jsonrpc': '2.0',
            'result': {
                'id': task_id,
                'status': {'state': 'completed'},
                'artifacts': [{'parts': [{'text': ''.join(chunks)}]}]
            }
        })}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 6.5 完整代码：一个翻译 Agent 的 A2A 服务

把以上代码合并到一个 `server.py` 中，然后运行：

```bash
# 启动服务
uvicorn server:app --host 0.0.0.0 --port 8000

# 验证 Agent Card
curl http://localhost:8000/.well-known/agent.json

# 测试同步翻译
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"text": "Hello, how are you?"}]
      }
    },
    "id": "test-001"
  }'
```

> 💡 **关键收获：** 一个 A2A Server 本质上就是一个"遵循特定 JSON-RPC 格式的 Web API"——如果你会写 FastAPI，你就会写 A2A Server。

---

## 7. 实战二：用 Python 构建 A2A Client

有了 Server，现在构建 Client——**发现远程 Agent、发送任务、接收结果**。

### 7.1 发现远程 Agent：解析 Agent Card

```python
import httpx

async def discover_agent(base_url: str) -> dict:
    """发现并解析远程 Agent 的能力"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{base_url}/.well-known/agent.json")
        agent_card = resp.json()
        
        print(f"发现 Agent: {agent_card['name']}")
        print(f"能力: {[s['name'] for s in agent_card['skills']]}")
        print(f"支持流式: {agent_card['capabilities']['streaming']}")
        
        return agent_card

# 使用
card = await discover_agent("http://localhost:8000")
# → 发现 Agent: 翻译 Agent
# → 能力: ['文本翻译']
# → 支持流式: True
```

### 7.2 发送同步任务请求

```python
async def send_task(base_url: str, text: str) -> dict:
    """发送同步翻译任务"""
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"text": text}]
            }
        },
        "id": "req-001"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(base_url, json=payload)
        result = resp.json()
        
        task = result["result"]
        print(f"Task {task['id']}: {task['status']['state']}")
        print(f"翻译结果: {task['artifacts'][0]['parts'][0]['text']}")
        
        return task

# 使用
task = await send_task("http://localhost:8000", "Hello, how are you?")
# → Task task-001: completed
# → 翻译结果: 你好，你怎么样？
```

### 7.3 消费 SSE 流式响应

```python
async def stream_task(base_url: str, text: str):
    """流式接收翻译结果"""
    payload = {
        "jsonrpc": "2.0",
        "method": "message/stream",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"text": text}]
            }
        },
        "id": "req-002"
    }
    
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", base_url, json=payload) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    task = data["result"]
                    state = task["status"]["state"]
                    
                    if state == "working" and task["artifacts"]:
                        # 打印中间结果（逐字输出效果）
                        text = task["artifacts"][0]["parts"][0]["text"]
                        print(f"\r翻译中: {text}", end="", flush=True)
                    elif state == "completed":
                        print(f"\n✅ 翻译完成!")
                        return task
```

### 7.4 编排器模式：一个 Client 调度多个 Server

```python
class AgentOrchestrator:
    """编排器：发现并调度多个远程 Agent"""
    
    def __init__(self):
        self.agents = {}  # name → {card, url}
    
    async def register(self, url: str):
        """发现并注册一个远程 Agent"""
        card = await discover_agent(url)
        self.agents[card["name"]] = {"card": card, "url": url}
    
    async def find_agent_for_skill(self, skill_keyword: str):
        """根据技能关键词找到合适的 Agent"""
        for name, info in self.agents.items():
            for skill in info["card"]["skills"]:
                if skill_keyword in skill["description"]:
                    return info
        return None
    
    async def delegate(self, skill: str, text: str):
        """委派任务给合适的 Agent"""
        agent = await self.find_agent_for_skill(skill)
        if not agent:
            raise ValueError(f"没有找到支持 '{skill}' 的 Agent")
        
        print(f"→ 委派给 {agent['card']['name']}")
        return await send_task(agent["url"], text)

# 使用
orchestrator = AgentOrchestrator()
await orchestrator.register("http://localhost:8000")  # 翻译 Agent
await orchestrator.register("http://localhost:8001")  # 摘要 Agent

# 自动找到翻译 Agent 并委派
result = await orchestrator.delegate("翻译", "Hello World")
```

> 💡 **架构洞察：** 编排器模式的关键是**Agent Card 驱动的路由**——编排器不需要硬编码"翻译用 A、摘要用 B"，而是根据 Agent Card 里的 skills 描述自动匹配。新增一个 Agent，只需要注册它的 URL 即可。

---

## 8. MCP + A2A 双协议架构：完整通信栈

这是本指南最重要的架构章节——如何在**同一个系统**中同时使用 MCP 和 A2A，构建真正的多 Agent 协作系统。

### 8.1 两个协议的分工：纵向 vs 横向

```
双协议架构图：

  ┌─────────────────────────────────────────────┐
  │              A2A 层（水平协作）                │
  │                                              │
  │  编排器 ←─A2A─→ 翻译Agent ←─A2A─→ 分析Agent  │
  │    Agent                                     │
  └──────┬──────────────┬───────────────┬────────┘
         │              │               │
  ┌──────▼──────┐ ┌─────▼─────┐  ┌─────▼─────┐
  │  MCP 层      │ │  MCP 层    │  │  MCP 层    │
  │              │ │            │  │            │
  │ ┌──────────┐ │ │ ┌────────┐│  │ ┌────────┐│
  │ │搜索工具  │ │ │ │翻译API ││  │ │数据库  ││
  │ │文件系统  │ │ │ │字典API ││  │ │图表工具││
  │ └──────────┘ │ │ └────────┘│  │ └────────┘│
  └──────────────┘ └───────────┘  └───────────┘
```

**一句话总结：A2A 管"谁做什么"，MCP 管"用什么工具做"。**

### 8.2 架构范式：Orchestrator + A2A + MCP

在生产系统中，典型的请求流程：

```
用户请求："帮我分析竞品 Notion 和 Obsidian 的差异"

  ① 编排器 Agent 收到请求，规划子任务
  ② 编排器 → [A2A] → 搜索 Agent："搜索 Notion 的功能特性"
  ③ 搜索 Agent → [MCP] → Tavily 搜索工具：执行搜索
  ④ 搜索 Agent → [A2A] → 编排器：返回搜索结果
  ⑤ 编排器 → [A2A] → 搜索 Agent："搜索 Obsidian 的功能特性"
  ⑥ 搜索 Agent → [MCP] → Tavily 搜索工具：执行搜索
  ⑦ 搜索 Agent → [A2A] → 编排器：返回搜索结果
  ⑧ 编排器 → [A2A] → 分析 Agent："对比这两组数据"
  ⑨ 分析 Agent → [MCP] → 图表工具：生成对比表
  ⑩ 分析 Agent → [A2A] → 编排器：返回分析报告
  ⑪ 编排器 → 用户：呈现最终报告
```

### 8.3 实战：搜索 Agent（MCP 接工具）+ 分析 Agent（A2A 协作）

```python
# 搜索 Agent：内部用 MCP 连接搜索工具，对外暴露 A2A 接口
class SearchAgentServer:
    def __init__(self):
        # MCP 层：连接搜索工具
        self.search_tool = TavilySearchResults(max_results=5)
    
    async def handle_a2a_task(self, message: str):
        """通过 A2A 接收任务，用 MCP 工具执行"""
        # 用 MCP 工具搜索
        results = self.search_tool.invoke(message)
        
        # 通过 A2A 返回结果
        return {
            "status": {"state": "completed"},
            "artifacts": [{
                "parts": [{"text": json.dumps(results, ensure_ascii=False)}]
            }]
        }

# 编排器：通过 A2A 调度搜索 Agent 和分析 Agent
async def orchestrate_analysis(query: str):
    orchestrator = AgentOrchestrator()
    await orchestrator.register("http://localhost:8000")  # 搜索 Agent
    await orchestrator.register("http://localhost:8001")  # 分析 Agent
    
    # Step 1：委派搜索
    search_result = await orchestrator.delegate("搜索", query)
    
    # Step 2：委派分析（把搜索结果传给分析 Agent）
    analysis = await orchestrator.delegate(
        "分析", f"请分析以下数据：{search_result}"
    )
    
    return analysis
```

### 8.4 Agent-as-a-Tool 模式：用 MCP 封装 A2A Agent

一种巧妙的混合模式——**把一个 A2A Agent 封装成 MCP Tool**，让不支持 A2A 的框架也能调用远程 Agent：

```python
from langchain_core.tools import tool

@tool
def call_translate_agent(text: str) -> str:
    """调用远程翻译 Agent（A2A 协议）
    
    将文本翻译为中文。底层通过 A2A 协议
    调用远程翻译 Agent 服务。
    """
    import asyncio
    result = asyncio.run(send_task(
        "http://translate-agent:8000", text
    ))
    return result["artifacts"][0]["parts"][0]["text"]

# 这个 tool 可以被任何 LangChain Agent 使用
# Agent 不需要知道底层是 A2A 协议
agent = create_react_agent(llm, tools=[call_translate_agent])
```

> 💡 **架构金句：** Agent-as-a-Tool 是 MCP 和 A2A 的**桥梁模式**——它让已有的 MCP 生态（LangChain/Claude Desktop 的工具体系）能无缝接入 A2A 的 Agent 网络。你不需要二选一，可以两者兼得。

---

## 9. 安全与企业级考量

Agent 能互相通信了——但**谁都能调你的 Agent** 显然不行。生产环境必须有安全防线。

### 9.1 认证与授权：OAuth 2.0 集成

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证 OAuth 2.0 Bearer Token"""
    token = credentials.credentials
    # 验证 token（调用 OAuth 服务器的 introspection 端点）
    if not await validate_with_oauth_server(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

@app.post("/")
async def handle_jsonrpc(request: Request, token: str = Depends(verify_token)):
    """所有 A2A 请求都需要认证"""
    # ... 处理逻辑
```

### 9.2 传输安全：HTTPS + mTLS

| 安全层 | 保护什么 | 实现方式 |
|--------|---------|---------|
| HTTPS | 传输加密，防窃听 | TLS 证书（Let's Encrypt） |
| mTLS | 双向身份验证 | 客户端证书 + 服务端证书 |
| 消息签名 | 防篡改 | HMAC-SHA256 签名 |

### 9.3 权限管控：谁能调谁的 Agent

```
权限控制矩阵：

  Agent Card 中声明权限要求：
  "authentication": {
    "schemes": ["Bearer"],
    "scopes": ["translate:read", "translate:write"]
  }

  Client 调用时携带的 Token 必须包含对应 scope
  → 没有 translate:write 权限？只能用翻译，不能修改翻译配置
```

### 9.4 审计日志：记录所有 Agent 间通信

生产环境必须记录每一次 Agent 间通信：

```python
import logging
from datetime import datetime

audit_logger = logging.getLogger("a2a.audit")

async def log_a2a_interaction(
    client_agent: str,
    server_agent: str, 
    method: str,
    task_id: str,
    status: str
):
    audit_logger.info(
        f"[{datetime.utcnow().isoformat()}] "
        f"{client_agent} → {server_agent} | "
        f"method={method} task={task_id} status={status}"
    )
```

> 💡 **企业级清单：** 上生产前检查四件事——① 所有端点 HTTPS ② Token 验证 ③ 权限 scope 控制 ④ 审计日志开启。缺一个都不要上线。

---

## 10. 生态与展望

### 10.1 支持 A2A 的主要框架与平台

| 框架/平台 | A2A 支持方式 | 成熟度 |
|-----------|-------------|--------|
| Google Vertex AI | 原生集成 | ⭐⭐⭐⭐⭐ |
| LangGraph | 社区适配器 | ⭐⭐⭐⭐ |
| CrewAI | 官方支持 | ⭐⭐⭐⭐ |
| AutoGen | 社区集成 | ⭐⭐⭐ |
| Salesforce AgentForce | 企业级支持 | ⭐⭐⭐⭐ |
| SAP Joule | 企业级支持 | ⭐⭐⭐ |

### 10.2 Linux 基金会与标准化进程

A2A 已移交 Linux 基金会管理——这意味着它不再是"Google 的协议"，而是**行业标准**。标准化路径：

```
标准化进程：

  2025.04  Google 发布 A2A 协议
  2025.06  50+ 公司加入 A2A 联盟
  2025.Q3  移交 Linux 基金会
  2025.Q4  发布 A2A 1.0 正式规范
  2026+    与 MCP 生态深度整合
```

### 10.3 A2A 的局限与未来演进

**当前局限：**

- **服务发现**：目前依赖手动注册 Agent URL，缺少自动化的 Agent 注册中心/市场
- **性能开销**：每次通信都走 HTTP + JSON 序列化，高频场景有延迟
- **错误处理**：协议规范对错误恢复、重试策略的定义还不够细致
- **多模态**：当前主要支持文本，图片/音频/视频的 Artifact 传输标准待完善

**未来方向：**

- **Agent Registry**：类似 Docker Hub 的 Agent 注册中心，自动发现和管理 Agent
- **gRPC 支持**：高性能场景下的二进制通信替代方案
- **多模态 Artifact**：标准化图片、文件、结构化数据的交换格式
- **与 MCP 的深度融合**：统一的 Agent 通信标准栈

### 10.4 延伸阅读与参考资料

**官方资源：**
- [A2A 协议官网](https://a2aprotocol.ai/)
- [A2A GitHub 仓库](https://github.com/google/A2A)
- [A2A Python SDK](https://pypi.org/project/a2a-sdk/)
- [Google A2A 发布博客](https://blog.google/technology/ai/agent-to-agent-protocol/)

**对比阅读：**
- [MCP协议开发实战大纲](../MCP协议开发实战/MCP协议开发实战大纲) — MCP 协议详解（已完成）
- [MCP 官方文档](https://modelcontextprotocol.io/)
- [Agent Protocol](https://agentprotocol.ai/) — 另一个 Agent 通信标准

**论文参考：**
- [Communicative Agents for Software Development](https://arxiv.org/abs/2307.07924) — ChatDev 多 Agent 协作
- [AutoGen: Enabling Next-Gen LLM Applications](https://arxiv.org/abs/2308.08155) — 微软多 Agent 对话框架

---

> **全书完。**
>
> A2A 协议的本质就两句话：
> - **Agent Card 让 Agent 被发现**——"我是谁，我能做什么"
> - **Task + Message 让 Agent 协作**——"帮我做这件事，做到哪了，还需要什么"
>
> 开始你的第一步：写一个 FastAPI 服务，暴露 `/.well-known/agent.json`，实现 `message/send`。就这三件事，你的 Agent 就能被全世界的 A2A Client 调用。
>
> 欢迎来到 Agent 互联网时代。 🌐
