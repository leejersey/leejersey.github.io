# Function Calling 与工具调用实战

> 从原理到生产——掌握 OpenAI / Claude / Gemini 的 Function Calling 机制，学会定义工具函数、处理模型调用、编排多工具协作，构建能"动手做事"的 AI 应用。

---

## 1. Function Calling 核心概念：让 LLM 从"只会说"到"能做事"

LLM 天生只能生成文本——你问它天气，它只能"编"一个答案。Function Calling 让模型能够调用你定义的工具函数，真正去查天气、查数据库、发邮件。这是 AI 应用从"聊天机器人"进化为"智能助手"的关键能力。

### 1.1 为什么需要 Function Calling：LLM 的能力边界

```
LLM 的能力边界：

  ✅ 能做的                    ❌ 不能做的
  ════════════                ════════════
  理解自然语言                 查询实时数据
  生成文本/代码                执行代码
  分析/总结内容                操作数据库
  翻译/改写                   调用外部 API
  推理/规划                   发送邮件/消息
  
  ═══════════════════════════════════════

  Function Calling 的作用：
  
  用户："帮我查一下北京今天的天气"
  
  没有 Function Calling：
  → 模型编一个答案："北京今天晴，25℃"（可能是错的）

  有了 Function Calling：
  → 模型决定调用 get_weather("北京")
  → 你执行函数，拿到真实数据
  → 模型基于真实数据生成回答
```

### 1.2 核心工作流程：定义 → 决策 → 执行 → 返回

```
Function Calling 的四步流程：

  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
  │ 1. 定义  │───→│ 2. 决策  │───→│ 3. 执行  │───→│ 4. 返回  │
  │ 你定义工具│     │ 模型决定 │     │ 你执行函数│     │ 模型生成 │
  │ JSON Schema│    │ 调不调、 │     │ 拿到结果  │     │ 最终回答 │
  │          │     │ 调哪个   │     │          │     │          │
  └─────────┘     └─────────┘     └─────────┘     └─────────┘
    你负责            模型负责          你负责           模型负责
```

```python
# 完整流程的伪代码
tools = [定义工具函数的 JSON Schema]

# Step 1: 发送请求（带工具定义）
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "北京今天天气怎么样？"}],
    tools=tools,
)

# Step 2: 模型决策（可能调用工具，也可能直接回答）
if response has tool_calls:
    # Step 3: 你执行函数
    result = get_weather("北京")
    
    # Step 4: 把结果回传给模型，生成最终回答
    final_response = client.chat.completions.create(
        messages=[...之前的消息..., tool_result],
    )
```

### 1.3 Function Calling vs Prompt Engineering

| 维度 | Prompt Engineering | Function Calling |
|:---|:---|:---|
| 原理 | 靠 Prompt 引导模型输出 JSON | 模型原生支持结构化工具调用 |
| 可靠性 | ⚠️ 格式不稳定，可能输出非 JSON | ✅ 模型保证输出合法调用 |
| 参数校验 | ❌ 需要手动解析和校验 | ✅ 基于 JSON Schema 自动校验 |
| 多工具选择 | ⚠️ 模型容易混乱 | ✅ 模型自主选择最合适的工具 |
| 并行调用 | ❌ 难以实现 | ✅ 原生支持一次调多个 |

> 💡 **结论**：简单场景（提取 3 个字段）用 Prompt + JSON 模式就够了。复杂场景（多工具选择、参数校验、链式调用）必须用 Function Calling。

### 1.4 各大模型支持情况：OpenAI / Claude / Gemini / 国产模型

| 模型 | Function Calling | 并行调用 | 流式支持 | API 参数名 |
|:---|:---|:---|:---|:---|
| GPT-4o / GPT-4o-mini | ✅ | ✅ | ✅ | `tools` |
| Claude 3.5 Sonnet | ✅ | ✅ | ✅ | `tools` |
| Gemini 1.5 Pro | ✅ | ✅ | ✅ | `tools` |
| 豆包（字节） | ✅ | ✅ | ✅ | `tools` |
| 通义千问 | ✅ | ⚠️ | ✅ | `tools` |
| DeepSeek | ✅ | ✅ | ✅ | `tools` |

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Function Calling** | 让模型调用你定义的函数，从"只会说"到"能做事" |
| **四步流程** | 定义工具 → 模型决策 → 你执行 → 模型生成回答 |
| **vs Prompt** | 简单提取用 Prompt，复杂工具调用用 FC |
| **模型支持** | 主流模型全部支持，API 格式略有差异 |

---

## 2. 快速上手：第一个工具调用

### 2.1 定义工具：用 JSON Schema 描述函数

```python
# 工具定义 = 告诉模型"你有哪些函数可以调用"
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",                    # 函数名
            "description": "获取指定城市的当前天气信息",  # 描述（越清晰越好）
            "parameters": {                            # 参数的 JSON Schema
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如 '北京'、'上海'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位，默认摄氏度"
                    }
                },
                "required": ["city"]                   # 必填参数
            }
        }
    }
]
```

### 2.2 完整调用流程：从请求到响应

```python
from openai import OpenAI
import json

client = OpenAI()

# ── Step 1: 发送请求（带工具定义） ──
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "北京今天天气怎么样？"}],
    tools=tools,
)

message = response.choices[0].message

# ── Step 2: 检查模型是否要调用工具 ──
if message.tool_calls:
    tool_call = message.tool_calls[0]
    
    print(f"模型决定调用: {tool_call.function.name}")
    print(f"参数: {tool_call.function.arguments}")
    # → 模型决定调用: get_weather
    # → 参数: {"city": "北京", "unit": "celsius"}
```

### 2.3 处理工具调用结果：回传给模型

```python
    # ── Step 3: 执行函数 ──
    args = json.loads(tool_call.function.arguments)
    weather_data = get_weather(**args)  # 你的真实函数
    
    # ── Step 4: 把结果回传给模型 ──
    messages = [
        {"role": "user", "content": "北京今天天气怎么样？"},
        message,                           # 模型的 tool_call 消息
        {
            "role": "tool",                # 工具结果消息
            "tool_call_id": tool_call.id,  # 必须对应 tool_call 的 id
            "content": json.dumps(weather_data, ensure_ascii=False)
        }
    ]
    
    # 模型基于真实数据生成最终回答
    final_response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )
    print(final_response.choices[0].message.content)
    # → "北京今天晴，气温 28℃，湿度 45%，适合外出。"
```

### 2.4 实战：天气查询助手

```python
import json
from openai import OpenAI

client = OpenAI()

# 模拟天气 API
def get_weather(city: str, unit: str = "celsius") -> dict:
    """真实项目中调用天气 API"""
    fake_data = {
        "北京": {"temp": 28, "condition": "晴", "humidity": 45},
        "上海": {"temp": 32, "condition": "多云", "humidity": 70},
    }
    data = fake_data.get(city, {"temp": 20, "condition": "未知", "humidity": 50})
    return {"city": city, **data, "unit": unit}

# 工具注册表：函数名 → 函数对象
TOOL_REGISTRY = {
    "get_weather": get_weather,
}

def chat_with_tools(user_message: str):
    messages = [{"role": "user", "content": user_message}]
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
    )
    
    message = response.choices[0].message
    
    # 如果模型不需要调用工具，直接返回
    if not message.tool_calls:
        return message.content
    
    # 执行所有工具调用
    messages.append(message)
    for tool_call in message.tool_calls:
        func = TOOL_REGISTRY[tool_call.function.name]
        args = json.loads(tool_call.function.arguments)
        result = func(**args)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False),
        })
    
    # 模型生成最终回答
    final = client.chat.completions.create(model="gpt-4o", messages=messages)
    return final.choices[0].message.content

# 测试
print(chat_with_tools("北京和上海今天天气怎么样？"))
```

> 💡 **TOOL_REGISTRY 模式**：用字典映射函数名→函数对象，这样添加新工具只需要注册一行，不需要 if/else。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **tools 参数** | JSON Schema 描述的函数列表 |
| **tool_calls** | 模型返回的工具调用请求（函数名+参数） |
| **role: tool** | 回传工具执行结果的消息角色 |
| **TOOL_REGISTRY** | 字典映射函数名→函数，方便扩展 |

---

## 3. 工具定义进阶：参数校验与复杂类型

### 3.1 用 Pydantic 自动生成 JSON Schema

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class TemperatureUnit(str, Enum):
    celsius = "celsius"
    fahrenheit = "fahrenheit"

class WeatherParams(BaseModel):
    """获取指定城市的当前天气信息"""
    city: str = Field(description="城市名称，如 '北京'、'上海'")
    unit: TemperatureUnit = Field(default=TemperatureUnit.celsius, description="温度单位")

# 自动生成 JSON Schema
print(WeatherParams.model_json_schema())
# → 完美的 JSON Schema，不用手写！
```

```python
# 通用：从 Pydantic 模型生成 OpenAI 工具定义
def pydantic_to_tool(model: type[BaseModel], func_name: str = None):
    schema = model.model_json_schema()
    return {
        "type": "function",
        "function": {
            "name": func_name or model.__name__.lower(),
            "description": model.__doc__ or "",
            "parameters": schema,
        }
    }

# 使用
tools = [pydantic_to_tool(WeatherParams, "get_weather")]
```

### 3.2 复杂参数类型：枚举、嵌套对象、数组

```python
class SearchFilters(BaseModel):
    """在数据库中搜索用户"""
    keyword: str = Field(description="搜索关键词")
    status: Optional[str] = Field(
        default=None,
        enum=["active", "inactive", "banned"],
        description="用户状态过滤"
    )
    tags: list[str] = Field(
        default=[],
        description="标签过滤，如 ['vip', 'new_user']"
    )
    pagination: dict = Field(
        default={"page": 1, "size": 20},
        description="分页参数，包含 page 和 size"
    )
```

### 3.3 工具描述的艺术：影响模型调用准确率的关键

| 要素 | ❌ 差的描述 | ✅ 好的描述 |
|:---|:---|:---|
| 函数描述 | `"查天气"` | `"获取中国城市的实时天气，返回温度、湿度和天气状况"` |
| 参数描述 | `"城市"` | `"中国城市名称，如 '北京'、'上海'、'广州'"` |
| 枚举说明 | 无 | `enum: ["celsius", "fahrenheit"]` |
| 边界说明 | 无 | `"日期格式 YYYY-MM-DD，不支持未来日期"` |

```python
# 好的工具定义示例
{
    "name": "search_orders",
    "description": "搜索用户的订单记录。支持按时间范围、状态、金额筛选。返回订单列表。",
    "parameters": {
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "用户 ID（必填）"
            },
            "status": {
                "type": "string",
                "enum": ["pending", "paid", "shipped", "completed", "cancelled"],
                "description": "订单状态，不传则返回所有状态"
            },
            "date_from": {
                "type": "string",
                "description": "起始日期，格式 YYYY-MM-DD"
            }
        },
        "required": ["user_id"]
    }
}
```

### 3.4 参数校验与错误处理

```python
import json
from pydantic import BaseModel, ValidationError

def execute_tool_call(tool_call, registry: dict):
    """安全地执行工具调用，带参数校验"""
    func_name = tool_call.function.name
    
    # 1. 检查函数是否存在
    if func_name not in registry:
        return json.dumps({"error": f"未知工具: {func_name}"})
    
    # 2. 解析参数
    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        return json.dumps({"error": "参数 JSON 解析失败"})
    
    # 3. 执行函数（捕获异常）
    try:
        result = registry[func_name](**args)
        return json.dumps(result, ensure_ascii=False, default=str)
    except TypeError as e:
        return json.dumps({"error": f"参数类型错误: {e}"})
    except Exception as e:
        return json.dumps({"error": f"执行失败: {e}"})
```

> 💡 **模型生成的参数不一定合法**——可能少字段、类型错、值越界。工具执行层必须做完整的参数校验和异常捕获，把错误信息返回给模型，让它重试。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Pydantic** | 用类定义参数，自动生成 JSON Schema |
| **描述质量** | 描述越清晰，模型调用准确率越高 |
| **枚举** | 限定取值范围，避免模型编造参数 |
| **错误处理** | 捕获异常→返回错误信息→让模型重试 |

---

## 4. 多工具编排：让模型选择正确的工具

### 4.1 多工具注册与模型自主选择

```python
tools = [
    pydantic_to_tool(WeatherParams, "get_weather"),
    pydantic_to_tool(SearchOrderParams, "search_orders"),
    pydantic_to_tool(SendEmailParams, "send_email"),
    pydantic_to_tool(CalcParams, "calculate"),
]

TOOL_REGISTRY = {
    "get_weather": get_weather,
    "search_orders": search_orders,
    "send_email": send_email,
    "calculate": calculate,
}

# 模型会根据用户意图自主选择调用哪个工具
# "今天北京天气如何？"     → get_weather
# "查一下我最近的订单"     → search_orders
# "帮我算一下 125 × 37"  → calculate
# "把报告发给张三"         → send_email
```

### 4.2 tool_choice：强制调用 vs 自动决策 vs 禁止调用

```python
# 自动决策（默认）：模型自己判断要不要调工具
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice="auto",       # 默认值
)

# 强制调用某个工具：不管用户说什么，必须调这个
response = client.chat.completions.create(
    tools=tools,
    tool_choice={"type": "function", "function": {"name": "get_weather"}},
)

# 禁止调用工具：只用文本回答
response = client.chat.completions.create(
    tools=tools,
    tool_choice="none",
)

# 强制调用任意一个工具（必须调，但选哪个由模型决定）
response = client.chat.completions.create(
    tools=tools,
    tool_choice="required",
)
```

| tool_choice | 行为 | 适用场景 |
|:---|:---|:---|
| `"auto"` | 模型自主决定 | 大部分场景 |
| `"none"` | 禁止调用 | 纯文本回答 |
| `"required"` | 必须调用某个工具 | 确保触发工具 |
| `{"function": {"name": "xxx"}}` | 强制调用指定工具 | 特定流程 |

### 4.3 并行工具调用：一次请求调用多个工具

```python
# 用户："北京和上海的天气分别怎么样？"
# 模型会返回 2 个 tool_calls：

message = response.choices[0].message
print(len(message.tool_calls))  # → 2

# tool_calls[0]: get_weather(city="北京")
# tool_calls[1]: get_weather(city="上海")

# 并行执行所有工具调用
import asyncio

async def execute_tools_parallel(tool_calls, registry):
    """并行执行多个工具调用"""
    async def run_one(tc):
        func = registry[tc.function.name]
        args = json.loads(tc.function.arguments)
        # 如果函数是同步的，放到线程池
        result = await asyncio.to_thread(func, **args)
        return {
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(result, ensure_ascii=False),
        }
    
    return await asyncio.gather(*[run_one(tc) for tc in tool_calls])
```

### 4.4 工具调用链：先查数据 → 再分析 → 再写报告

```python
def chat_loop(user_message: str, max_iterations: int = 5):
    """支持多轮工具调用的对话循环"""
    messages = [{"role": "user", "content": user_message}]
    
    for i in range(max_iterations):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
        )
        
        message = response.choices[0].message
        messages.append(message)
        
        # 没有工具调用 → 最终回答
        if not message.tool_calls:
            return message.content
        
        # 执行工具调用，把结果加入消息
        for tc in message.tool_calls:
            result = execute_tool_call(tc, TOOL_REGISTRY)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })
    
    return "达到最大迭代次数"

# 用户："查一下上个月的销售额，然后跟去年同期对比，给我写个报告"
# 模型执行链：
# 第 1 轮：search_sales(month="2024-03") → 拿到数据
# 第 2 轮：search_sales(month="2023-03") → 拿到对比数据
# 第 3 轮：生成对比报告（不调工具，直接输出文本）
```

> 💡 **max_iterations 必须设上限**——防止模型陷入无限循环调用。生产环境通常设 5-10 次。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **多工具注册** | 模型根据意图自主选择调用哪个 |
| **tool_choice** | auto/none/required/指定函数 |
| **并行调用** | 模型一次返回多个 tool_calls |
| **调用链** | 循环执行直到模型不再调用工具 |

---

## 5. 多模型适配：OpenAI / Claude / Gemini 统一封装

### 5.1 OpenAI：tools + tool_calls 标准格式

```python
# OpenAI 格式（标准）
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "...",
            "parameters": {...}
        }
    }],
)

# 响应中的 tool_calls
message.tool_calls[0].function.name       # "get_weather"
message.tool_calls[0].function.arguments  # '{"city": "北京"}'
message.tool_calls[0].id                  # "call_abc123"
```

### 5.2 Claude：tool_use content block 格式

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=[{
        "name": "get_weather",
        "description": "获取城市天气",
        "input_schema": {         # 注意：Claude 用 input_schema，不是 parameters
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名"}
            },
            "required": ["city"]
        }
    }],
    messages=[{"role": "user", "content": "北京天气"}],
)

# Claude 的响应格式不同
for block in response.content:
    if block.type == "tool_use":
        print(block.name)   # "get_weather"
        print(block.input)  # {"city": "北京"}
        print(block.id)     # "toolu_xxx"
```

### 5.3 Gemini：function_declarations 格式

```python
import google.generativeai as genai

# Gemini 的工具定义格式
weather_tool = genai.protos.Tool(
    function_declarations=[{
        "name": "get_weather",
        "description": "获取城市天气",
        "parameters": {
            "type": "OBJECT",            # 大写！
            "properties": {
                "city": {"type": "STRING", "description": "城市名"}
            },
            "required": ["city"]
        }
    }]
)

model = genai.GenerativeModel("gemini-1.5-pro", tools=[weather_tool])
response = model.generate_content("北京天气")
```

### 5.4 统一封装：一套代码适配多模型

```python
from abc import ABC, abstractmethod

class ToolCallResult:
    """统一的工具调用结果"""
    def __init__(self, tool_call_id: str, name: str, arguments: dict):
        self.id = tool_call_id
        self.name = name
        self.arguments = arguments

class LLMAdapter(ABC):
    @abstractmethod
    def chat(self, messages, tools) -> tuple[str | None, list[ToolCallResult]]:
        """返回 (文本回复, 工具调用列表)"""
        pass

class OpenAIAdapter(LLMAdapter):
    def chat(self, messages, tools):
        response = self.client.chat.completions.create(
            model="gpt-4o", messages=messages, tools=tools
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            calls = [ToolCallResult(tc.id, tc.function.name, 
                     json.loads(tc.function.arguments)) for tc in msg.tool_calls]
            return None, calls
        return msg.content, []

class ClaudeAdapter(LLMAdapter):
    def chat(self, messages, tools):
        # 转换工具格式：parameters → input_schema
        claude_tools = [self._convert_tool(t) for t in tools]
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514", messages=messages, tools=claude_tools
        )
        calls = [ToolCallResult(b.id, b.name, b.input)
                 for b in response.content if b.type == "tool_use"]
        text = next((b.text for b in response.content if b.type == "text"), None)
        return text, calls
```

> 💡 **适配器模式**：业务代码只跟 `LLMAdapter` 交互，切换模型只需换一个 Adapter 实例。这也是大模型网关的核心设计思路。

**第 5 章核心知识回顾：**

| 模型 | 工具定义字段 | 响应格式 |
|:---|:---|:---|
| OpenAI | `parameters` | `tool_calls[].function` |
| Claude | `input_schema` | `content[].type == "tool_use"` |
| Gemini | `parameters`（大写类型） | `candidates[].function_call` |

---

## 6. 流式工具调用：实时响应 + 工具执行

### 6.1 流式响应中的工具调用检测

```python
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    stream=True,
)

# 流式响应中，tool_calls 的参数是分块到达的
# chunk.choices[0].delta.tool_calls[0].function.arguments = '{"ci'
# chunk.choices[0].delta.tool_calls[0].function.arguments = 'ty":'
# chunk.choices[0].delta.tool_calls[0].function.arguments = ' "北京"}'
```

### 6.2 增量拼接：从 chunk 到完整的 function_call

```python
def collect_tool_calls_from_stream(stream):
    """从流式响应中收集完整的工具调用"""
    tool_calls_data = {}  # index → {id, name, arguments}
    content_parts = []
    
    for chunk in stream:
        delta = chunk.choices[0].delta
        
        # 收集文本内容
        if delta.content:
            content_parts.append(delta.content)
        
        # 收集工具调用（增量拼接）
        if delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index
                if idx not in tool_calls_data:
                    tool_calls_data[idx] = {"id": "", "name": "", "arguments": ""}
                if tc.id:
                    tool_calls_data[idx]["id"] = tc.id
                if tc.function and tc.function.name:
                    tool_calls_data[idx]["name"] = tc.function.name
                if tc.function and tc.function.arguments:
                    tool_calls_data[idx]["arguments"] += tc.function.arguments
    
    content = "".join(content_parts) if content_parts else None
    return content, list(tool_calls_data.values())
```

### 6.3 流式 + 工具调用的完整实现

```python
async def stream_chat_with_tools(user_message: str):
    messages = [{"role": "user", "content": user_message}]
    
    for _ in range(5):  # 最大迭代
        stream = client.chat.completions.create(
            model="gpt-4o", messages=messages, tools=tools, stream=True
        )
        
        content, tool_calls = collect_tool_calls_from_stream(stream)
        
        if not tool_calls:
            # 没有工具调用，流式输出文本
            yield {"type": "text", "content": content}
            return
        
        # 通知前端"正在执行工具"
        for tc in tool_calls:
            yield {"type": "tool_start", "name": tc["name"], "args": tc["arguments"]}
            
            result = execute_tool_call_dict(tc, TOOL_REGISTRY)
            
            yield {"type": "tool_end", "name": tc["name"], "result": result}
            
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
```

### 6.4 前端展示：调用中 → 执行中 → 结果返回

```
前端展示的状态流转：

  用户："帮我查北京天气和最近的订单"
  
  ┌─────────────────────────────────────┐
  │ 🤖 正在思考...                        │
  │                                     │
  │ 🔧 调用工具: get_weather             │
  │    参数: {"city": "北京"}             │
  │    ⏳ 执行中...                       │
  │    ✅ 结果: 晴，28℃                   │
  │                                      │
  │ 🔧 调用工具: search_orders            │
  │    参数: {"user_id": 123}             │
  │    ⏳ 执行中...                       │
  │    ✅ 结果: 3 条订单                   │
  │                                      │
  │ 北京今天天气晴朗，气温 28℃。            │
  │ 您最近有 3 条订单...                    │
  └─────────────────────────────────────┘
```

> 💡 **流式工具调用的用户体验**：关键是让用户看到"AI 正在做什么"——显示工具名称、参数和执行状态，而不是一片空白等待。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **增量拼接** | 流式中 arguments 分块到达，需要拼接 |
| **tool_start/tool_end** | 前端展示工具执行过程的事件 |
| **迭代循环** | 流式中也要支持多轮工具调用 |

---

## 7. 生产化：安全、限流与可观测

### 7.1 安全边界：工具白名单与参数过滤

```python
# 工具白名单：只允许注册的函数被调用
ALLOWED_TOOLS = {"get_weather", "search_orders", "calculate"}

def safe_execute(tool_call, registry):
    name = tool_call.function.name
    
    # 白名单检查
    if name not in ALLOWED_TOOLS:
        return json.dumps({"error": f"工具 {name} 未授权"})
    
    # 参数过滤（防止恶意字段）
    args = json.loads(tool_call.function.arguments)
    allowed_keys = get_allowed_params(name)  # 每个工具的允许参数列表
    filtered_args = {k: v for k, v in args.items() if k in allowed_keys}
    
    return registry[name](**filtered_args)
```

### 7.2 防注入：模型参数不可信，必须校验

```python
# ❌ 危险：直接拼接 SQL
def search_users(keyword: str):
    query = f"SELECT * FROM users WHERE name LIKE '%{keyword}%'"  # SQL 注入！
    
# ✅ 安全：参数化查询
def search_users(keyword: str):
    query = "SELECT * FROM users WHERE name LIKE %s"
    cursor.execute(query, [f"%{keyword}%"])

# ❌ 危险：直接执行命令
def run_command(cmd: str):
    os.system(cmd)  # 模型可能传入 "rm -rf /"！

# ✅ 安全：白名单命令
ALLOWED_COMMANDS = {"ls", "pwd", "date"}
def run_command(cmd: str):
    if cmd.split()[0] not in ALLOWED_COMMANDS:
        return {"error": "命令不在白名单中"}
```

### 7.3 超时与重试：工具执行的容错设计

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def execute_with_retry(func, **kwargs):
    """工具执行自动重试"""
    return await asyncio.wait_for(
        asyncio.to_thread(func, **kwargs),
        timeout=30  # 30 秒超时
    )
```

### 7.4 可观测性：日志追踪与调试

```python
import logging
import time

logger = logging.getLogger("tool_calls")

def traced_execute(tool_call, registry):
    """带追踪的工具执行"""
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    
    logger.info(f"🔧 Tool Call: {name}", extra={
        "tool_name": name,
        "arguments": args,
        "tool_call_id": tool_call.id,
    })
    
    start = time.time()
    try:
        result = registry[name](**args)
        duration = time.time() - start
        logger.info(f"✅ Tool Result: {name} ({duration:.2f}s)", extra={
            "tool_name": name,
            "duration": duration,
            "result_size": len(json.dumps(result)),
        })
        return result
    except Exception as e:
        duration = time.time() - start
        logger.error(f"❌ Tool Error: {name} ({duration:.2f}s): {e}")
        return {"error": str(e)}
```

> 💡 **生产三原则**：工具参数不可信（必须校验）、工具执行可能失败（必须超时+重试）、工具调用必须可追踪（必须日志）。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **白名单** | 只允许注册的工具被调用 |
| **防注入** | 模型参数 → 参数化查询，不拼接 |
| **超时重试** | 30s 超时 + 3 次重试 |
| **日志追踪** | 记录工具名、参数、耗时、结果 |

---

## 8. 综合实战：构建一个能操作数据库和 API 的 AI 助手

### 8.1 需求分析：一个能查数据、调 API、写报告的助手

```
AI 助手的能力：

  用户："上个月销售额最高的 5 个产品是什么？
        跟去年同期对比一下，然后给我发一封总结邮件。"

  助手执行链：
  ┌──────────────────────────────────────┐
  │ 1. query_database                     │
  │    SQL: 查上个月 TOP5 产品              │
  │                                       │
  │ 2. query_database                     │
  │    SQL: 查去年同期 TOP5 产品            │
  │                                       │
  │ 3. 模型分析对比（不调工具）              │
  │    生成对比报告文本                      │
  │                                       │
  │ 4. send_email                          │
  │    收件人: user@company.com            │
  │    内容: 对比报告                       │
  └──────────────────────────────────────┘
```

### 8.2 工具定义：SQL 查询 + HTTP 请求 + 文件操作

```python
from pydantic import BaseModel, Field

class QueryDatabase(BaseModel):
    """对 PostgreSQL 数据库执行只读查询，返回结果"""
    sql: str = Field(description="SELECT 查询语句（只允许 SELECT，不允许 INSERT/UPDATE/DELETE）")
    limit: int = Field(default=100, description="最大返回行数")

class HttpRequest(BaseModel):
    """发送 HTTP 请求到指定 API"""
    url: str = Field(description="请求 URL")
    method: str = Field(default="GET", enum=["GET", "POST"])
    body: dict | None = Field(default=None, description="POST 请求体")

class SendEmail(BaseModel):
    """发送邮件"""
    to: str = Field(description="收件人邮箱")
    subject: str = Field(description="邮件主题")
    body: str = Field(description="邮件正文（支持 Markdown）")
```

```python
# 工具实现（带安全校验）
def query_database(sql: str, limit: int = 100) -> dict:
    # 安全检查：只允许 SELECT
    if not sql.strip().upper().startswith("SELECT"):
        return {"error": "只允许 SELECT 查询"}
    
    sql = f"{sql.rstrip(';')} LIMIT {limit}"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return {"columns": columns, "rows": rows, "total": len(rows)}
```

### 8.3 对话循环：多轮对话中的工具调用管理

```python
class AIAssistant:
    def __init__(self, model: str = "gpt-4o"):
        self.client = OpenAI()
        self.model = model
        self.tools = [
            pydantic_to_tool(QueryDatabase, "query_database"),
            pydantic_to_tool(HttpRequest, "http_request"),
            pydantic_to_tool(SendEmail, "send_email"),
        ]
        self.registry = {
            "query_database": query_database,
            "http_request": http_request,
            "send_email": send_email,
        }
        self.messages = [
            {"role": "system", "content": "你是一个数据分析助手，可以查询数据库、调用 API、发送邮件。"}
        ]
    
    def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        
        for _ in range(10):  # 最大 10 轮工具调用
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
            )
            
            message = response.choices[0].message
            self.messages.append(message)
            
            if not message.tool_calls:
                return message.content
            
            for tc in message.tool_calls:
                result = traced_execute(tc, self.registry)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
        
        return "操作超过最大步数限制"
```

### 8.4 完整代码与运行效果

```python
# 使用
assistant = AIAssistant()

# 单工具调用
print(assistant.chat("数据库里有多少用户？"))
# → 🔧 query_database: SELECT COUNT(*) FROM users
# → "数据库里共有 15,234 个用户。"

# 多步调用链
print(assistant.chat(
    "查一下上个月销售额 TOP5 的产品，跟去年同期对比，给我发总结邮件到 boss@company.com"
))
# → 🔧 query_database: SELECT ... 本月 TOP5
# → 🔧 query_database: SELECT ... 去年同期
# → 🔧 send_email: to=boss@company.com, subject=月度销售对比
# → "已完成！对比报告已发送到 boss@company.com。主要发现：..."
```

---

## 附录：Function Calling 速查手册

### A.1 OpenAI / Claude / Gemini API 参数速查

| 参数 | OpenAI | Claude | Gemini |
|:---|:---|:---|:---|
| 工具定义 | `tools[].function.parameters` | `tools[].input_schema` | `tools[].function_declarations` |
| 工具选择 | `tool_choice` | `tool_choice` | `tool_config` |
| 响应检测 | `message.tool_calls` | `content[].type == "tool_use"` | `candidates[].function_call` |
| 结果回传 | `role: "tool"` | `role: "user"` + `tool_result` | `role: "function"` |

### A.2 JSON Schema 常用模式速查

```json
// 字符串 + 枚举
{"type": "string", "enum": ["a", "b", "c"]}

// 可选参数
{"type": "string", "description": "可选"}  // 不在 required 中

// 整数 + 范围
{"type": "integer", "minimum": 1, "maximum": 100}

// 数组
{"type": "array", "items": {"type": "string"}}

// 嵌套对象
{"type": "object", "properties": {"name": {"type": "string"}}}
```

### A.3 常见错误与解决方案

| 错误 | 原因 | 解决 |
|:---|:---|:---|
| 模型不调用工具 | 描述不清晰 | 改善工具描述 |
| 调错了工具 | 工具太相似 | 在描述中说明区别 |
| 参数格式错误 | Schema 定义不准确 | 用 Pydantic 生成 |
| 无限循环调用 | 没有退出条件 | 设 max_iterations |
| tool_call_id 不匹配 | 回传时 id 写错 | 用 `tc.id` 不要硬编码 |

### A.4 工具定义模板库

```python
# 数据库查询工具模板
class DBQuery(BaseModel):
    """查询数据库"""
    sql: str = Field(description="SQL 查询语句（仅 SELECT）")

# 搜索工具模板
class Search(BaseModel):
    """搜索内容"""
    query: str = Field(description="搜索关键词")
    top_k: int = Field(default=5, description="返回条数")

# 计算工具模板
class Calculate(BaseModel):
    """数学计算"""
    expression: str = Field(description="数学表达式，如 '125 * 37'")

# 发送通知模板
class Notify(BaseModel):
    """发送通知消息"""
    channel: str = Field(enum=["email", "slack", "feishu"])
    recipient: str = Field(description="接收人")
    message: str = Field(description="消息内容")
```
