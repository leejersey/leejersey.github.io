# 第三章 State —— 图的共享记忆

---

## 3.1 什么是 State —— Graph 的"全局变量"

上一章我们用 `JokeState` 定义了 `topic`、`joke`、`translation` 三个字段。你可能觉得这只是个"数据容器"——但在 LangGraph 的世界里，**State 是整个系统的核心**，它的重要性远超你的第一印象。

### State 的角色

```
传统函数调用：
  result_1 = func_a(input)
  result_2 = func_b(result_1)
  result_3 = func_c(result_2)
  → 数据通过「参数传递」在函数间流转

LangGraph：
  所有节点共享同一个 State
  → 数据通过「读写共享 State」在节点间流转

  ┌─────────────────────────────────┐
  │           State                  │
  │  ┌─────────────────────────┐    │
  │  │ messages: [...]          │    │
  │  │ current_step: "analyze"  │    │
  │  │ results: {...}           │    │
  │  │ retry_count: 2           │    │
  │  └─────────────────────────┘    │
  │       ↑↓        ↑↓        ↑↓    │
  │    Node A    Node B    Node C   │
  └─────────────────────────────────┘
```

每个 Node 函数执行时：
1. **读取** State 中需要的字段
2. **处理**（调 LLM、查数据库、执行逻辑……）
3. **返回**要更新的字段（部分更新，不需要返回完整 State）

### State 不只是数据容器

State 在 LangGraph 中承担了**三重角色**：

| 角色 | 说明 | 类比 |
|------|------|------|
| 数据总线 | 节点之间传递数据的唯一通道 | 工厂流水线上的工单 |
| 执行快照 | Checkpointer 自动保存每步的 State | 游戏存档 |
| 决策依据 | 条件边根据 State 的值决定走向 | 铁路道岔 |

```python
# 示例：条件边根据 State 做路由决策
def should_retry(state):
    """根据 State 中的 retry_count 决定是否重试"""
    if state["retry_count"] < 3:
        return "retry"     # 重试次数 < 3，继续重试
    else:
        return "give_up"   # 超过 3 次，放弃

graph.add_conditional_edges("check", should_retry, {
    "retry": "process",   # 回到处理节点（循环！）
    "give_up": END        # 结束
})
```

### State 的设计原则

```
✅ 好的 State 设计：
  - 只包含节点间需要共享的数据
  - 字段名清晰，一看就知道是什么
  - 类型明确（str / list / dict）

❌ 坏的 State 设计：
  - 把所有临时变量都塞进 State
  - 字段名含糊（data、info、result）
  - 一个 dict 字段装所有东西
```

> **关键心法**：设计 State 时先问自己——"哪些数据需要在节点之间流转？哪些数据需要在中断后恢复？" 只有这些数据才需要放进 State。节点内部的临时变量用局部变量就好。

---

## 3.2 用 TypedDict 定义 State

TypedDict 是 LangGraph 中最常用的 State 定义方式。它来自 Python 标准库 `typing`，语法简洁，适合快速上手。

### 基本语法

```python
from typing import TypedDict

class MyState(TypedDict):
    messages: list          # 对话消息列表
    current_topic: str      # 当前话题
    search_results: list    # 搜索结果
    is_complete: bool       # 是否完成
```

然后把这个 State 类传给 `StateGraph`：

```python
from langgraph.graph import StateGraph

graph = StateGraph(MyState)
```

就这么简单。LangGraph 会根据 TypedDict 的字段定义来管理 State 的读写。

### Node 如何读写 State

```python
def my_node(state: MyState) -> dict:
    # 读取：直接用字典语法
    topic = state["current_topic"]
    msgs = state["messages"]

    # 处理...
    new_message = f"正在处理话题：{topic}"

    # 写入：返回要更新的字段（部分更新）
    return {
        "messages": [new_message],   # 更新 messages
        "is_complete": True          # 更新 is_complete
        # current_topic 和 search_results 不需要更新，不用写
    }
```

```
State 更新机制：

  执行前 State:
  ┌────────────────────────────────┐
  │ messages: ["你好"]              │
  │ current_topic: "AI"            │
  │ search_results: []             │
  │ is_complete: False             │
  └────────────────────────────────┘
                │
        Node 返回 {"messages": ["新消息"], "is_complete": True}
                │
                ↓  默认行为：覆盖（replace）
  ┌────────────────────────────────┐
  │ messages: ["新消息"]      ← 被覆盖！│
  │ current_topic: "AI"      ← 不变   │
  │ search_results: []       ← 不变   │
  │ is_complete: True        ← 被更新  │
  └────────────────────────────────┘
```

### ⚠️ 覆盖陷阱

注意上面的例子——`messages` 字段被完全**覆盖**了，原来的 `["你好"]` 丢失了！这是 TypedDict 的默认行为：**每次更新都是 replace，不是 append**。

```python
# 默认行为（覆盖）：
# 原始 State: {"messages": ["你好"]}
# Node 返回:  {"messages": ["新消息"]}
# 更新后:     {"messages": ["新消息"]}  ← 原来的 "你好" 丢了！

# 如果你想保留历史消息，你得手动拼接：
def my_node(state):
    old_messages = state["messages"]
    new_message = "新消息"
    return {"messages": old_messages + [new_message]}  # 手动追加
```

这种手动追加的方式既啰嗦又容易出错。有没有更好的办法？有——这就是下一节要讲的 **Reducer**。

### TypedDict 的局限

| 特性 | TypedDict |
|------|----------|
| 类型提示 | ✅ 有（IDE 可以自动补全） |
| 运行时校验 | ❌ 没有（类型写错也不报错） |
| 默认值 | ❌ 不支持 |
| 序列化/反序列化 | ❌ 需要手动处理 |

> **何时用 TypedDict**：快速原型、简单项目、State 字段不超过 10 个的场景。当你需要类型校验和默认值时，考虑用 3.4 节的 Pydantic。

---

## 3.3 Reducer：消息追加而非覆盖

上一节我们发现了 TypedDict 的默认行为——**覆盖**。这在大多数场景下都不是你想要的，尤其是 `messages` 这种需要不断追加的字段。

LangGraph 的解决方案叫 **Reducer**——你可以为每个字段指定一个"合并策略"。

### 什么是 Reducer

```
没有 Reducer（默认行为——覆盖）：
  旧值: ["消息1", "消息2"]
  Node 返回: ["消息3"]
  结果: ["消息3"]          ← 旧消息丢失！

有 Reducer（使用 operator.add——追加）：
  旧值: ["消息1", "消息2"]
  Node 返回: ["消息3"]
  结果: ["消息1", "消息2", "消息3"]  ← 追加成功！
```

### 语法：Annotated + operator.add

```python
from typing import TypedDict, Annotated
import operator

class ChatState(TypedDict):
    # 普通字段：默认覆盖
    current_topic: str

    # 带 Reducer 的字段：使用 operator.add 追加
    messages: Annotated[list, operator.add]
```

关键语法是 `Annotated[类型, reducer函数]`：

```
Annotated[list, operator.add]
    │        │        │
    │        │        └── Reducer 函数：operator.add（列表拼接）
    │        └────────── 字段类型：list
    └─────────────────── Python 类型注解包装器
```

### 实战对比

```python
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, START, END

# ====== 带 Reducer 的 State ======
class ChatState(TypedDict):
    messages: Annotated[list, operator.add]  # 追加模式
    count: int                                # 覆盖模式

# ====== 两个 Node ======
def node_a(state):
    return {
        "messages": ["Node A 说了一句话"],  # 追加到 messages
        "count": 1                          # 覆盖 count
    }

def node_b(state):
    return {
        "messages": ["Node B 也说了一句话"],  # 继续追加
        "count": 2                            # 覆盖为 2
    }

# ====== 构建并运行 ======
graph = StateGraph(ChatState)
graph.add_node("a", node_a)
graph.add_node("b", node_b)
graph.add_edge(START, "a")
graph.add_edge("a", "b")
graph.add_edge("b", END)

app = graph.compile()
result = app.invoke({"messages": [], "count": 0})

print(result["messages"])
# ["Node A 说了一句话", "Node B 也说了一句话"]  ← 追加成功！

print(result["count"])
# 2  ← 被覆盖（没有 Reducer）
```

### 常用 Reducer 函数

| Reducer | 效果 | 适用场景 |
|---------|------|---------|
| `operator.add` | 列表拼接 / 数字相加 | messages、日志、累计计数 |
| 自定义函数 | 你说了算 | 去重、限制长度、条件合并 |
| 不指定（默认） | 覆盖 | 普通标量字段（str / int / bool） |

### 自定义 Reducer

`operator.add` 不够用？你可以写自己的 Reducer 函数。Reducer 就是一个接收 `(旧值, 新值)` 的普通函数：

```python
def keep_latest_n(old: list, new: list) -> list:
    """自定义 Reducer：只保留最近 10 条消息"""
    combined = old + new
    return combined[-10:]  # 只留最后 10 条

class SmartState(TypedDict):
    messages: Annotated[list, keep_latest_n]   # 使用自定义 Reducer
    status: str                                 # 默认覆盖
```

```
自定义 Reducer 的签名：

  def my_reducer(old_value, new_value) -> merged_value:
      # old_value: State 中该字段的当前值
      # new_value: Node 返回的该字段的新值
      # 返回: 合并后的值
```

> **关键总结**：`Annotated[list, operator.add]` 是 LangGraph 中**最常用的一行代码**。几乎所有包含 `messages` 字段的 State 都需要它。记住这个模式，后面用到的频率极高。

---

## 3.4 用 Pydantic 定义 State（类型校验 + 默认值）

TypedDict 简单好用，但它只提供**静态类型提示**——运行时你传个错误类型的值，它不会报错，只会默默出 bug。当你的 State 字段变多、项目上线后，你需要更强的保障。

这就是 Pydantic 登场的时候。

### Pydantic State 的语法

```python
from pydantic import BaseModel, Field
from typing import Annotated
import operator

class AgentState(BaseModel):
    """用 Pydantic 定义的 State —— 带类型校验和默认值"""
    messages: Annotated[list, operator.add] = Field(default_factory=list)
    current_topic: str = ""
    retry_count: int = 0
    is_complete: bool = False
```

和 TypedDict 的关键区别：

```
TypedDict（只有类型提示）：
  class MyState(TypedDict):
      messages: list        # 没有默认值，invoke 时必须传
      count: int            # 传个 "abc" 也不报错

Pydantic（类型校验 + 默认值）：
  class MyState(BaseModel):
      messages: list = []   # 有默认值，invoke 时可以省略
      count: int = 0        # 传 "abc" 会报 ValidationError！
```

### Pydantic 的三大优势

**优势 1：默认值**

```python
# TypedDict —— 必须在 invoke 时传入所有字段
result = app.invoke({
    "messages": [],
    "current_topic": "",
    "retry_count": 0,
    "is_complete": False
})

# Pydantic —— 有默认值的字段可以省略
result = app.invoke({})  # 所有字段用默认值，一个不传也行！
```

**优势 2：运行时类型校验**

```python
# Pydantic 会在运行时检查类型
result = app.invoke({"retry_count": "不是数字"})
# → ValidationError: Input should be a valid integer

# TypedDict 不会报错，直到后面代码炸了才发现
```

**优势 3：复杂类型和嵌套**

```python
from pydantic import BaseModel, Field
from typing import Optional

class SearchResult(BaseModel):
    """搜索结果的结构化定义"""
    title: str
    url: str
    relevance_score: float = 0.0

class ResearchState(BaseModel):
    """带嵌套类型的复杂 State"""
    query: str = ""
    results: list[SearchResult] = Field(default_factory=list)
    summary: Optional[str] = None
    iteration: int = 0
```

### 完整示例

```python
from pydantic import BaseModel, Field
from typing import Annotated
import operator
from langgraph.graph import StateGraph, START, END

# ====== Pydantic State ======
class ReviewState(BaseModel):
    messages: Annotated[list, operator.add] = Field(default_factory=list)
    code: str = ""
    review_comments: Annotated[list, operator.add] = Field(default_factory=list)
    approved: bool = False

# ====== Node 函数（用法和 TypedDict 完全一样）======
def reviewer(state: ReviewState) -> dict:
    return {
        "review_comments": [f"代码 '{state.code[:20]}...' 审查通过"],
        "approved": True
    }

# ====== 构建 Graph ======
graph = StateGraph(ReviewState)
graph.add_node("review", reviewer)
graph.add_edge(START, "review")
graph.add_edge("review", END)

app = graph.compile()

# 只传需要的字段，其他用默认值
result = app.invoke({"code": "print('hello world')"})
print(result["approved"])         # True
print(result["review_comments"])  # ["代码 'print('hello world...' 审查通过"]
```

### TypedDict vs Pydantic 选型指南

| 维度 | TypedDict | Pydantic |
|------|----------|----------|
| 学习成本 | ⭐ 极低 | ⭐⭐ 需要了解 Pydantic |
| 类型校验 | 仅 IDE 提示 | ✅ 运行时校验 |
| 默认值 | ❌ 不支持 | ✅ 支持 |
| 嵌套类型 | 手动管理 | ✅ 原生支持 |
| 序列化 | 手动 | ✅ `.model_dump()` |
| 性能 | 更快（无校验开销） | 略慢（有校验开销） |
| 推荐场景 | 原型 / 教程 / 简单项目 | 生产项目 / 复杂 State |

> **务实建议**：学习阶段用 TypedDict（本教程大部分示例都用它），上生产换 Pydantic。两种方式在 LangGraph 中的使用方式几乎完全一样——Node 函数的写法不需要改任何东西。

---

## 3.5 MessagesState —— 对话场景的现成方案

前面三节你学会了 TypedDict、Reducer、Pydantic 三种定义 State 的方式。但在实际开发中，90% 的 LangGraph 应用都是**对话类 Agent**——它们的 State 的核心字段都是 `messages`。

为了避免你每次都重复写 `messages: Annotated[list, operator.add]`，LangGraph 提供了一个开箱即用的 State 基类：**MessagesState**。

### 使用 MessagesState

```python
from langgraph.graph import MessagesState

# 不需要自己定义 messages 字段——MessagesState 已经帮你定义好了
# 它等价于：
# class MessagesState(TypedDict):
#     messages: Annotated[list[AnyMessage], add_messages]
```

`MessagesState` 帮你做了两件事：
1. 定义了 `messages: list` 字段
2. 绑定了 `add_messages` Reducer（比 `operator.add` 更智能）

### add_messages vs operator.add

`MessagesState` 使用的不是简单的 `operator.add`，而是 LangGraph 专门为消息设计的 `add_messages` Reducer：

```
operator.add（简单拼接）：
  旧: [msg1, msg2]
  新: [msg3]
  结果: [msg1, msg2, msg3]  ← 纯拼接，没什么特殊的

add_messages（智能合并）：
  ① 正常追加：旧 [msg1] + 新 [msg2] → [msg1, msg2]
  ② ID 去重：如果新消息和旧消息 ID 相同 → 更新而非追加
  ③ 删除消息：传入 RemoveMessage(id=xxx) → 删除指定消息
```

大多数情况下两者行为一样，但 `add_messages` 在需要**修改历史消息**（比如压缩对话历史）时更灵活。

### 扩展 MessagesState

你的 Agent 通常不只需要 `messages`。用**继承**来扩展它：

```python
from langgraph.graph import MessagesState

class MyAgentState(MessagesState):
    """在 MessagesState 基础上扩展自己的字段"""
    current_tool: str = ""
    search_results: list = []
    iteration_count: int = 0
```

这样你就同时拥有了：
- `messages` 字段（带 `add_messages` Reducer，自动追加）
- 你自定义的字段（默认覆盖）

### 完整实战示例

```python
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, MessagesState, START, END

# ====== 使用 MessagesState ======
# 不需要定义 messages 字段，直接用！

llm = ChatDeepSeek(model="deepseek-chat", temperature=0)

def chatbot(state: MessagesState) -> dict:
    """聊天节点：把 messages 发给 LLM，追加回复"""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}  # add_messages 会自动追加

# ====== 构建 Graph ======
graph = StateGraph(MessagesState)
graph.add_node("chatbot", chatbot)
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)

app = graph.compile()

# ====== 运行 ======
result = app.invoke({
    "messages": [HumanMessage(content="用一句话解释什么是 LangGraph")]
})

# 查看所有消息
for msg in result["messages"]:
    print(f"{msg.type}: {msg.content}")

# 输出：
# human: 用一句话解释什么是 LangGraph
# ai: LangGraph 是一个用图结构来编排 AI Agent 工作流的 Python 框架...
```

### 三种 State 定义方式总结

```
选择哪种方式？

  只是学习/写 Demo？
  → MessagesState（最省事）

  对话类 Agent + 少量自定义字段？
  → 继承 MessagesState

  非对话场景（数据处理、工作流编排）？
  → TypedDict（快速原型）
  → Pydantic（生产项目）
```

| 方式 | 代码量 | 适用场景 |
|------|--------|---------|
| `MessagesState` | 最少 | 纯对话、快速原型 |
| 继承 `MessagesState` | 少 | 对话 + 自定义字段 |
| `TypedDict` | 中等 | 完全自定义、非对话场景 |
| `Pydantic BaseModel` | 中等 | 生产项目、复杂校验 |

> **实战推荐**：本教程后续章节的大部分示例都会使用 `MessagesState` 或其扩展版——因为对话 Agent 是 LangGraph 最核心的使用场景。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| State 的角色 | 数据总线 + 执行快照 + 决策依据，不只是数据容器 |
| TypedDict | 简洁好用，但默认覆盖、无校验、无默认值 |
| Reducer | `Annotated[list, operator.add]` 实现追加而非覆盖 |
| 自定义 Reducer | `def my_reducer(old, new) -> merged` |
| Pydantic | 类型校验 + 默认值 + 嵌套类型，适合生产 |
| MessagesState | 对话场景开箱即用，内置 `add_messages` Reducer |
| 设计原则 | 只把节点间需要共享的数据放进 State |

> **下一章预告**：Node 与 Edge —— 深入理解节点函数、普通边、条件边、路由函数，并构建一个带分支决策的问答路由器。


