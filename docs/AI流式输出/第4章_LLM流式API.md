# AI 应用的流式输出全链路

> 从 LLM 的第一个 Token 到用户屏幕上的逐字渲染——拆解流式输出的每一层。

---

## 4. LLM 提供商的流式 API——OpenAI / Anthropic / 开源

上一章讲了传输协议（SSE/WebSocket/gRPC）。这一章进入实战——**实际调用各大提供商的流式 API**，逐行解析它们返回的每一个 chunk。

我们会覆盖三类提供商：闭源 API（OpenAI、Anthropic）和开源方案（vLLM、Ollama），最后用一个统一封装把它们全部适配。

---

### 4.1 OpenAI 流式 API 详解

OpenAI 是流式输出的"事实标准"——大多数其他提供商（包括国内的各种大模型 API）都在模仿 OpenAI 的 SSE chunk 格式。

### 开启流式输出

只需要一个参数：`stream=True`

```python
# openai_stream.py —— OpenAI 流式调用
from openai import OpenAI

client = OpenAI()  # 自动读取 OPENAI_API_KEY 环境变量

# 非流式（默认）
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "你好"}],
)
print(response.choices[0].message.content)  # 一次性返回全部

# 流式（加一个参数）⭐
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "你好"}],
    stream=True,  # ← 唯一的区别
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
```

### 流式 chunk 的完整数据结构

每个 chunk 是一个 `ChatCompletionChunk` 对象。我们逐个拆解：

```
OpenAI 流式输出的 chunk 序列（实际格式）：

  ════ 第 1 个 chunk（角色声明）═════
  data: {
    "id": "chatcmpl-abc123",
    "object": "chat.completion.chunk",
    "created": 1710000000,
    "model": "gpt-4o",
    "choices": [{
      "index": 0,
      "delta": {
        "role": "assistant",    ← 只有角色，没有内容
        "content": ""
      },
      "finish_reason": null
    }]
  }

  ════ 第 2-N 个 chunk（内容 Token）═════
  data: {"choices":[{"delta":{"content":"你"}}]}
  data: {"choices":[{"delta":{"content":"好"}}]}
  data: {"choices":[{"delta":{"content":"！"}}]}
  data: {"choices":[{"delta":{"content":"有"}}]}
  data: {"choices":[{"delta":{"content":"什么"}}]}
  ...

  ════ 最后一个 chunk（完成标记）═════
  data: {
    "choices": [{
      "delta": {},               ← delta 为空
      "finish_reason": "stop"    ← 表示正常结束
    }],
    "usage": {                   ← 仅在 stream_options 开启时出现
      "prompt_tokens": 10,
      "completion_tokens": 25,
      "total_tokens": 35
    }
  }

  ════ 终止信号 ═════
  data: [DONE]
```

### 获取流式输出中的 Token 用量

默认情况下，流式输出**不返回 usage 信息**。需要显式开启：

```python
# 开启流式 Token 用量统计
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "你好"}],
    stream=True,
    stream_options={"include_usage": True},  # ← 开启用量统计
)

total_content = ""
for chunk in stream:
    # 内容 Token
    if chunk.choices and chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        total_content += content
        print(content, end="", flush=True)

    # 用量信息（在最后一个 chunk 中）
    if chunk.usage:
        print(f"\n\n📊 Token 用量：")
        print(f"  输入: {chunk.usage.prompt_tokens}")
        print(f"  输出: {chunk.usage.completion_tokens}")
        print(f"  总计: {chunk.usage.total_tokens}")
```

### finish_reason 的含义

```
finish_reason 取值与含义：

  "stop"            → 模型正常完成，遇到了自然结束点或 stop 序列
  "length"          → 达到了 max_tokens 限制，内容被截断
  "content_filter"  → 触发了内容安全过滤
  "tool_calls"      → 模型决定调用工具（Function Calling）
  null              → 还在生成中（中间 chunk）

  在流式输出中的处理建议：
    → "stop"：正常结束，显示完毕
    → "length"：提示用户"回复被截断，可以让 AI 继续"
    → "content_filter"：显示"该内容无法生成"
    → "tool_calls"：进入工具调用流程
```

> **关键理解**：OpenAI 的流式格式中，`message.content` 被拆成了 `delta.content`——"delta"意味着"增量"。每个 chunk 只包含新增的部分，你需要自己把它们拼接起来。

### 4.2 Anthropic Claude 流式 API 详解

Anthropic 的流式 API 和 OpenAI 有本质区别——它不是简单的"逐 Token 推 delta"，而是一套**事件驱动模型**，不同类型的事件代表不同的流式阶段。

### 事件类型全景

```
Anthropic 流式输出的事件序列：

  ════ 1. 消息开始 ═════
  event: message_start
  data: {
    "type": "message_start",
    "message": {
      "id": "msg_abc123",
      "type": "message",
      "role": "assistant",
      "model": "claude-3-5-sonnet-20241022",
      "usage": {"input_tokens": 15, "output_tokens": 0}    ← 输入 Token 数
    }
  }

  ════ 2. 内容块开始 ═════
  event: content_block_start
  data: {
    "type": "content_block_start",
    "index": 0,
    "content_block": {"type": "text", "text": ""}
  }

  ════ 3. 内容增量（核心！逐 Token 推送）═════
  event: content_block_delta
  data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"你"}}

  event: content_block_delta
  data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"好"}}

  event: content_block_delta
  data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"！"}}
  ...

  ════ 4. 内容块结束 ═════
  event: content_block_stop
  data: {"type": "content_block_stop", "index": 0}

  ════ 5. 消息增量（输出 Token 统计）═════
  event: message_delta
  data: {
    "type": "message_delta",
    "delta": {"stop_reason": "end_turn"},
    "usage": {"output_tokens": 25}                          ← 输出 Token 数
  }

  ════ 6. 消息结束 ═════
  event: message_stop
  data: {"type": "message_stop"}
```

### Python 代码实现

```python
# anthropic_stream.py —— Anthropic Claude 流式调用
from anthropic import Anthropic

client = Anthropic()  # 自动读取 ANTHROPIC_API_KEY

# 方式 1：低层级——手动处理事件流
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好"}],
) as stream:
    for text in stream.text_stream:
        # text_stream 已经帮你提取了纯文本增量
        print(text, end="", flush=True)

# 方式 2：事件级别——完全控制
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好"}],
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            print(event.delta.text, end="", flush=True)
        elif event.type == "message_delta":
            print(f"\n停止原因: {event.delta.stop_reason}")
            print(f"输出 Token: {event.usage.output_tokens}")

# 方式 3：获取完整消息（流式传输，但最后拿完整结果）
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好"}],
) as stream:
    response = stream.get_final_message()  # 等待流完成，返回完整 Message
    print(response.content[0].text)
    print(f"总 Token: {response.usage.input_tokens + response.usage.output_tokens}")
```

### Anthropic vs OpenAI 流式格式对比

| 维度 | OpenAI | Anthropic |
|------|--------|-----------|
| 流式模式 | `stream=True` 参数 | `.stream()` 方法 |
| 数据格式 | 逐 chunk 推 delta | 事件驱动（6 种事件） |
| 内容增量 | `delta.content` | `delta.text`（在 `content_block_delta` 中） |
| Token 用量 | 需额外开启 `stream_options` | 自动包含在 `message_start` 和 `message_delta` 中 |
| 结束标记 | `data: [DONE]` | `event: message_stop` |
| 结束原因 | `finish_reason: "stop"` | `stop_reason: "end_turn"` |
| 工具调用 | `delta.tool_calls` | `content_block_start` 中 `type: "tool_use"` |
| SDK 便利性 | 自己遍历 chunk | 提供 `.text_stream` 快捷方式 |

> **关键差异**：Anthropic 的事件模型更结构化——你能精确知道"消息开始了、第几个内容块在推送、消息结束了"。OpenAI 更简洁——就是一堆 delta 和一个 `[DONE]`。两种风格各有优劣，但做统一封装时需要注意这些差异。

### 4.3 开源模型的流式输出（vLLM / Ollama）

不用闭源 API 也能搞流式输出。本地部署开源模型，TTFT 更低、成本为零、数据不出本机。

### Ollama：最简单的本地方案

Ollama 提供了兼容 OpenAI 格式的 API，流式输出开箱即用：

```python
# ollama_stream.py —— 两种调用 Ollama 流式输出的方式

# ═══════════════════════════════════════════
# 方式 1：Ollama 原生 API（默认就是流式！）
# ═══════════════════════════════════════════

import requests
import json

response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "llama3:8b",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": True,   # 默认就是 True
    },
    stream=True,
)

for line in response.iter_lines():
    if line:
        chunk = json.loads(line)
        # Ollama 原生格式：每行一个 JSON
        if not chunk.get("done"):
            print(chunk["message"]["content"], end="", flush=True)
        else:
            print(f"\n总耗时: {chunk['total_duration'] / 1e9:.2f}s")

# ═══════════════════════════════════════════
# 方式 2：用 OpenAI SDK 调 Ollama（兼容模式）⭐ 推荐
# ═══════════════════════════════════════════

from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",  # Ollama 的 OpenAI 兼容端点
    api_key="ollama",                       # 任意值即可
)

stream = client.chat.completions.create(
    model="llama3:8b",
    messages=[{"role": "user", "content": "你好"}],
    stream=True,
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
# → 代码和调 OpenAI 完全一样！只改了 base_url
```

### vLLM：生产级本地部署

vLLM 同样提供 OpenAI 兼容的流式 API：

```python
# vllm_stream.py —— 通过 vLLM 的 OpenAI 兼容 API 流式调用

# 启动 vLLM 服务（终端执行）：
# vllm serve meta-llama/Llama-3-8B-Instruct --port 8000

from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",  # vLLM 服务地址
    api_key="token-abc123",               # vLLM 启动时设置的 token
)

stream = client.chat.completions.create(
    model="meta-llama/Llama-3-8B-Instruct",
    messages=[{"role": "user", "content": "你好"}],
    stream=True,
    stream_options={"include_usage": True},  # vLLM 也支持用量统计
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
    if chunk.usage:
        print(f"\n📊 Token: {chunk.usage.total_tokens}")
```

```
Ollama vs vLLM 流式体验对比：

  维度           Ollama              vLLM
  ────────────────────────────────────────────
  安装难度       ⭐ 一条命令           ⭐⭐⭐ 需要配 CUDA
  API 兼容性     OpenAI 兼容          OpenAI 兼容
  流式格式       NDJSON / OpenAI      OpenAI 格式
  并发性能       ⭐⭐ 单请求优化       ⭐⭐⭐⭐⭐ 高并发优化
  量化支持       GGUF 格式            AWQ / GPTQ
  适合场景       个人开发/测试          团队共享/生产环境
  TTFT           ~50-100ms (8B)       ~30-80ms (8B)

  共同优势：
    ✅ 数据不出本机
    ✅ 无 Token 费用
    ✅ TTFT 极低（无网络延迟）
    ✅ 都兼容 OpenAI SDK（代码无需改动）
```

> **实用建议**：个人开发用 Ollama（安装简单），团队/生产用 vLLM（高并发、高性能）。两者都兼容 OpenAI SDK，切换成本几乎为零。

### 4.4 统一封装：多提供商流式适配层

实际项目中往往需要支持多个提供商——开发用 Ollama、测试用 Claude、生产用 GPT-4o。如果每次切换都要改业务代码，维护成本太高。

**解决方案**：抽象一个统一的流式生成器接口。

### 设计思路

```
统一适配层架构：

  业务代码（只关心文本流）
       │
       ▼
  ┌──────────────────────────────┐
  │     stream_chat()            │  ← 统一接口
  │     → AsyncGenerator[str]    │  ← 每次 yield 一个文本增量
  └──────┬───────┬───────┬───────┘
         │       │       │
    ┌────▼──┐ ┌──▼───┐ ┌─▼────┐
    │OpenAI │ │Claude│ │Ollama│    ← 各提供商适配器
    └───────┘ └──────┘ └──────┘

  设计原则：
    1. 统一返回 AsyncGenerator[str]（纯文本增量）
    2. 屏蔽各提供商的 chunk 格式差异
    3. 提供商切换只改配置，不改业务代码
```

### 完整实现

```python
# unified_stream.py —— 多提供商流式适配层
from typing import AsyncGenerator
from dataclasses import dataclass

@dataclass
class StreamConfig:
    provider: str          # "openai" | "anthropic" | "ollama"
    model: str
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 1024

async def stream_chat(
    messages: list[dict],
    config: StreamConfig,
) -> AsyncGenerator[str, None]:
    """统一流式接口：不管什么提供商，都 yield 纯文本增量"""

    if config.provider == "openai":
        async for text in _stream_openai(messages, config):
            yield text

    elif config.provider == "anthropic":
        async for text in _stream_anthropic(messages, config):
            yield text

    elif config.provider == "ollama":
        async for text in _stream_ollama(messages, config):
            yield text

    else:
        raise ValueError(f"不支持的提供商: {config.provider}")

# ═══════════════════════════════════════════
# OpenAI 适配器
# ═══════════════════════════════════════════

async def _stream_openai(
    messages: list[dict], config: StreamConfig
) -> AsyncGenerator[str, None]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url or None)
    stream = await client.chat.completions.create(
        model=config.model,
        messages=messages,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# ═══════════════════════════════════════════
# Anthropic 适配器
# ═══════════════════════════════════════════

async def _stream_anthropic(
    messages: list[dict], config: StreamConfig
) -> AsyncGenerator[str, None]:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=config.api_key)
    async with client.messages.stream(
        model=config.model,
        messages=messages,
        max_tokens=config.max_tokens,
    ) as stream:
        async for text in stream.text_stream:
            yield text

# ═══════════════════════════════════════════
# Ollama 适配器（复用 OpenAI 兼容模式）
# ═══════════════════════════════════════════

async def _stream_ollama(
    messages: list[dict], config: StreamConfig
) -> AsyncGenerator[str, None]:
    config.base_url = config.base_url or "http://localhost:11434/v1"
    config.api_key = config.api_key or "ollama"
    async for text in _stream_openai(messages, config):
        yield text
```

### 使用示例

```python
# 业务代码——切换提供商只需改 config
import asyncio

async def main():
    messages = [{"role": "user", "content": "用三句话介绍 Python"}]

    # 切换提供商：只改这一行配置
    config = StreamConfig(provider="openai", model="gpt-4o", api_key="sk-xxx")
    # config = StreamConfig(provider="anthropic", model="claude-3-5-sonnet-20241022", api_key="sk-ant-xxx")
    # config = StreamConfig(provider="ollama", model="llama3:8b")

    async for text in stream_chat(messages, config):
        print(text, end="", flush=True)

asyncio.run(main())
```

```
统一封装的价值：

  不用封装的痛苦：
    → 业务代码里散落着 if openai ... elif anthropic ... elif ollama ...
    → 每加一个提供商，所有调用处都要改
    → 测试要写 3 套

  用了封装之后：
    → 业务代码只调 stream_chat()，完全不知道底层是谁
    → 加新提供商只需写一个适配器函数
    → 运行时通过配置切换，支持 A/B 测试、降级
    → 符合开闭原则：对扩展开放，对修改关闭
```

> **下一步**：这个 `stream_chat()` 函数会在第 5 章作为后端中转的核心组件，被 FastAPI 包装成 SSE 端点推送给前端。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| OpenAI 流式 | `stream=True`，chunk 中 `delta.content` 是增量 |
| OpenAI 用量 | 需开启 `stream_options={"include_usage": True}` |
| finish_reason | stop/length/content_filter/tool_calls |
| Anthropic 流式 | 事件驱动，6 种事件类型，`text_stream` 最方便 |
| Ollama | 兼容 OpenAI SDK，改 `base_url` 即可 |
| vLLM | 生产级，OpenAI 兼容，支持 `stream_options` |
| 统一封装 | `AsyncGenerator[str]` 适配层，屏蔽提供商差异 |

> **下一章预告**：后端流式中转 —— 为什么不能让前端直连 LLM API？如何用 FastAPI 搭建一个流式中转层，把 stream_chat() 包装成 SSE 端点，加上鉴权、限流和错误处理。
