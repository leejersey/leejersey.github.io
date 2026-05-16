# 第九章 Streaming —— 实时响应

---

## 9.1 为什么需要 Streaming

前面所有例子中，我们都用 `invoke()` 来运行图——它是**同步阻塞**的：发出请求后一直等到整个图执行完毕，才一次性返回所有结果。

问题来了：如果图里有多个 LLM 调用、多次工具执行，用户可能要**等几十秒**才能看到第一个字。

```
invoke() 的用户体验：

  用户: "帮我调研 LangGraph 并写篇文章"
  [发送请求]
  ...（等待 5 秒）...（Agent 思考）...
  ...（等待 8 秒）...（搜索工具执行）...
  ...（等待 10 秒）...（LLM 生成长文章）...
  [23 秒后] 一次性弹出所有内容

  → 用户体验：等了半天，以为卡了。

stream() 的用户体验：

  用户: "帮我调研 LangGraph 并写篇文章"
  [发送请求]
  [0.5 秒] 🔄 正在分析问题...
  [2 秒]   🔍 正在搜索 LangGraph 相关资料...
  [5 秒]   📝 正在生成文章...
  [5.5 秒] "Lang" "Graph" " 是" "一个" ...（逐字输出）

  → 用户体验：实时反馈，感觉很快。
```

### LangGraph 的三种运行模式

| 模式 | 方法 | 返回方式 | 适用场景 |
|------|------|---------|---------|
| 同步阻塞 | `invoke()` | 等全部完成后返回 | 后台任务、测试 |
| 流式输出 | `stream()` | 每步实时返回 | API 服务、UI |
| 异步流式 | `astream()` | 异步迭代器 | FastAPI、WebSocket |

> **经验法则**：开发调试用 `invoke()`，面向用户的产品**一定**用 `stream()` 或 `astream()`。没人愿意盯着空白屏幕等 20 秒。

---

## 9.2 stream_mode="values" vs "updates"

`stream()` 方法的 `stream_mode` 参数决定了每一步返回什么内容。有两种主要模式。

### stream_mode="values"（默认）

每一步返回**完整的 State 快照**：

```python
config = {"configurable": {"thread_id": "stream_demo"}}

for state_snapshot in app.stream(
    {"messages": [HumanMessage(content="北京天气怎么样？")]},
    config=config,
    stream_mode="values"
):
    # 每次迭代，state_snapshot 是完整的 State
    messages = state_snapshot["messages"]
    print(f"消息数量: {len(messages)}, 最新: {messages[-1].type}")
```

```
输出：

  消息数量: 1, 最新: human       ← 初始状态
  消息数量: 2, 最新: ai           ← Agent 节点执行后（有 tool_calls）
  消息数量: 3, 最新: tool         ← Tools 节点执行后
  消息数量: 4, 最新: ai           ← Agent 再次执行后（最终回答）
```

### stream_mode="updates"

每一步只返回**该节点产生的增量更新**：

```python
for node_name, update in app.stream(
    {"messages": [HumanMessage(content="北京天气怎么样？")]},
    config=config,
    stream_mode="updates"
):
    # node_name: 执行的节点名
    # update: 该节点返回的增量字典
    print(f"节点 [{node_name}] 更新: {list(update.keys())}")
```

```
输出：

  节点 [agent] 更新: ['messages']     ← Agent 添加了 AIMessage
  节点 [tools] 更新: ['messages']     ← Tools 添加了 ToolMessage
  节点 [agent] 更新: ['messages']     ← Agent 添加了最终回答
```

### 两种模式对比

| 特性 | values | updates |
|------|--------|---------|
| 每步返回 | 完整 State | 仅增量更新 |
| 数据量 | 较大（State 累积） | 较小 |
| 知道哪个节点 | ❌ 不知道 | ✅ 知道 |
| 适用场景 | 需要完整状态 | 需要追踪节点进度 |

### 实用示例：追踪执行进度

```python
for node_name, update in app.stream(input_data, config, stream_mode="updates"):
    if node_name == "agent":
        msg = update["messages"][-1]
        if msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"🤔 Agent 决定调用工具: {tc['name']}")
        else:
            print(f"💬 Agent 最终回答: {msg.content[:80]}...")
    elif node_name == "tools":
        for msg in update["messages"]:
            print(f"🔧 工具执行完成: {msg.content[:80]}...")
```

```
输出示例：

  🤔 Agent 决定调用工具: get_weather
  🔧 工具执行完成: 晴，25°C
  💬 Agent 最终回答: 北京今天天气晴朗，气温 25°C，适合出行...
```

> **推荐**：大多数场景使用 `stream_mode="updates"`——它数据量小，而且能告诉你是哪个节点在执行，方便做进度提示。

---

## 9.3 流式输出 LLM Token（astream_events）

`stream()` 的粒度是**节点级别**——每个节点执行完后返回一次。但如果你想要更细粒度的流式输出——像 ChatGPT 那样**逐个 Token** 输出，需要用 `astream_events`。

### Token 级别的流式输出

```python
async for event in app.astream_events(
    {"messages": [HumanMessage(content="用 200 字介绍 LangGraph")]},
    config=config,
    version="v2"
):
    kind = event["event"]

    # 过滤出 LLM 的流式 Token
    if kind == "on_chat_model_stream":
        token = event["data"]["chunk"].content
        if token:
            print(token, end="", flush=True)  # 逐字输出，不换行
```

```
输出效果（逐字出现）：

  L a n g G r a p h   是   一   个   ...
  ↑ 每个 token 到达时立即显示
```

### astream_events 的事件类型

`astream_events` 会发出各种类型的事件：

| 事件类型 | 说明 | 包含数据 |
|---------|------|---------|
| `on_chain_start` | 图/节点开始执行 | 节点名、输入 |
| `on_chain_end` | 图/节点执行完毕 | 节点名、输出 |
| `on_chat_model_start` | LLM 开始生成 | 模型名、输入 |
| `on_chat_model_stream` | LLM 输出一个 Token | Token 内容 |
| `on_chat_model_end` | LLM 生成完毕 | 完整回复 |
| `on_tool_start` | 工具开始执行 | 工具名、输入参数 |
| `on_tool_end` | 工具执行完毕 | 工具返回结果 |

### 实用示例：综合事件处理

```python
async for event in app.astream_events(input_data, config, version="v2"):
    kind = event["event"]
    name = event.get("name", "")

    if kind == "on_chain_start" and "agent" in name:
        print("🤖 Agent 开始思考...")

    elif kind == "on_chat_model_stream":
        token = event["data"]["chunk"].content
        if token:
            print(token, end="", flush=True)

    elif kind == "on_tool_start":
        tool_name = event["name"]
        print(f"\n🔧 调用工具: {tool_name}")

    elif kind == "on_tool_end":
        result = event["data"]["output"]
        print(f"   结果: {str(result)[:100]}")

    elif kind == "on_chain_end" and event.get("name") == "LangGraph":
        print("\n✅ 执行完成")
```

```
输出效果：

  🤖 Agent 开始思考...
  北京天气怎么样？让我查一下...
  🔧 调用工具: get_weather
     结果: 晴，25°C
  🤖 Agent 开始思考...
  北京今天天气晴朗，气温25°C，适合户外活动！
  ✅ 执行完成
```

> **注意**：`astream_events` 是**异步 API**，需要在 `async` 函数中使用。如果你的项目还没用 async，可以用 `asyncio.run()` 包一层。

---

## 9.4 实战：带进度反馈的 Agent

结合 `stream_mode="updates"` 和 `astream_events`，构建一个对用户友好的、有实时进度反馈的 Agent。

### 完整代码

```python
import asyncio
from langchain_deepseek import ChatDeepSeek
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# ====== 工具和 LLM ======
@tool
def search_docs(query: str) -> str:
    """搜索文档库中的相关内容。"""
    import time
    time.sleep(1)  # 模拟搜索延迟
    return f"关于 '{query}' 的搜索结果：LangGraph 支持循环、持久化和 Human-in-the-Loop。"

tools = [search_docs]
llm = ChatDeepSeek(model="deepseek-chat", temperature=0).bind_tools(tools)

# ====== 构建图（标准 ReAct 模式）======
def agent(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}

def should_continue(state: MessagesState):
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

graph = StateGraph(MessagesState)
graph.add_node("agent", agent)
graph.add_node("tools", ToolNode(tools))
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")

app = graph.compile(checkpointer=MemorySaver())

# ====== 流式运行 ======
async def run_with_progress():
    config = {"configurable": {"thread_id": "progress_demo"}}
    input_data = {"messages": [HumanMessage(content="帮我搜索 LangGraph 的核心特性")]}

    print("🚀 开始执行...\n")

    async for event in app.astream_events(input_data, config, version="v2"):
        kind = event["event"]

        if kind == "on_chat_model_start":
            print("🤖 Agent 正在思考...", flush=True)

        elif kind == "on_chat_model_stream":
            token = event["data"]["chunk"].content
            if token:
                print(token, end="", flush=True)

        elif kind == "on_tool_start":
            print(f"\n\n🔍 正在搜索: {event['data'].get('input', '')}")

        elif kind == "on_tool_end":
            result = str(event["data"]["output"])
            print(f"✅ 搜索完成（{len(result)} 字符）")

        elif kind == "on_chain_end" and event.get("name") == "LangGraph":
            print("\n\n🎉 全部完成！")

asyncio.run(run_with_progress())
```

### 运行效果

```
🚀 开始执行...

🤖 Agent 正在思考...
（Agent 正在分析问题并决定使用搜索工具...）

🔍 正在搜索: {'query': 'LangGraph 核心特性'}
✅ 搜索完成（89 字符）

🤖 Agent 正在思考...
根据搜索结果，LangGraph 的核心特性包括：

1. **循环支持** - 支持条件循环，是构建 Agent 的基础
2. **持久化** - 内置 Checkpointer，支持多轮对话和断点恢复
3. **Human-in-the-Loop** - 支持在关键节点暂停等待人类确认

🎉 全部完成！
```

---

## 9.5 SSE 推送到前端（FastAPI 集成）

在实际产品中，Agent 通常作为后端 API 服务运行，需要把流式结果**推送到前端**。最常用的方式是 **SSE（Server-Sent Events）**。

### FastAPI + SSE 集成

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
import json

fastapi_app = FastAPI()

@fastapi_app.post("/chat/stream")
async def chat_stream(message: str, thread_id: str):
    """流式聊天接口"""
    config = {"configurable": {"thread_id": thread_id}}
    input_data = {"messages": [HumanMessage(content=message)]}

    async def event_generator():
        async for event in app.astream_events(
            input_data, config, version="v2"
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                token = event["data"]["chunk"].content
                if token:
                    # SSE 格式：data: {json}\n\n
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            elif kind == "on_tool_start":
                yield f"data: {json.dumps({'type': 'tool_start', 'name': event['name']})}\n\n"

            elif kind == "on_tool_end":
                yield f"data: {json.dumps({'type': 'tool_end', 'result': str(event['data']['output'])[:200]})}\n\n"

        # 发送结束信号
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

### 前端接收（JavaScript）

```javascript
const eventSource = new EventSource('/chat/stream?message=你好&thread_id=user_001');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'token':
      // 逐字追加到聊天界面
      appendToChat(data.content);
      break;
    case 'tool_start':
      showStatus(`🔧 正在使用工具: ${data.name}`);
      break;
    case 'tool_end':
      showStatus(`✅ 工具执行完成`);
      break;
    case 'done':
      eventSource.close();
      break;
  }
};
```

### 三种前后端通信方式

| 方式 | 协议 | 适合场景 | 复杂度 |
|------|------|---------|--------|
| SSE | HTTP | 服务器 → 客户端单向推送 | ⭐ 低 |
| WebSocket | WS | 双向实时通信 | ⭐⭐ 中 |
| LangServe | HTTP | LangChain 官方方案 | ⭐ 低 |

> **推荐**：大多数 Agent 应用用 **SSE** 就够了——Agent 的交互模式本质上就是"用户发消息 → Agent 流式回复"，不需要双向通信。WebSocket 适合需要中途发送用户中断指令的场景。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 为什么 Streaming | 实时反馈 > 长时间等待，用户体验关键 |
| stream_mode="values" | 每步返回完整 State |
| stream_mode="updates" | 每步返回增量 + 节点名（推荐） |
| astream_events | Token 级别流式，最细粒度 |
| 事件类型 | on_chat_model_stream / on_tool_start / on_tool_end |
| SSE 集成 | FastAPI + StreamingResponse + 前端 EventSource |

> **下一章预告**：实战 —— 自纠错 RAG Agent。结合前面所有知识，构建一个能检索文档、自动评估答案质量、不满意就重新检索的完整 RAG Agent。


