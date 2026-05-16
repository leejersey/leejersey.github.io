# 第七章 Human-in-the-Loop —— 人机协作

---

## 7.1 什么是 Human-in-the-Loop（人在回路中）

前面的 Agent 都是"全自动"的——用户提问后，Agent 自己思考、自己调工具、自己回答，中间没有人类介入的机会。

但在很多场景下，你**不希望** Agent 完全自主：

```
场景 1：高风险操作
  Agent: "我要删除数据库中的这条记录。"
  → 你希望：先让我看看，确认后再删！

场景 2：敏感信息
  Agent: "我准备发送这封邮件给客户。"
  → 你希望：让我先审核一下内容！

场景 3：不确定的决策
  Agent: "搜索结果有两种理解方式，我选择了 A。"
  → 你希望：等等，让我看看 B 是不是更好？

场景 4：合规要求
  金融/医疗/法律领域
  → 某些操作必须经过人工确认才能执行。
```

### Human-in-the-Loop 的核心机制

LangGraph 的解决方案很优雅：让图执行在**指定节点**前或后**暂停**，等待人类输入后再继续。

```
普通执行流程：
  START → Agent → Tools → Agent → END
  ↑ 启动                        ↑ 自动结束

Human-in-the-Loop 流程：
  START → Agent → [暂停！等人确认] → Tools → Agent → END
                       ↑
                 人类审核 tool_calls
                 ├── 确认 → 继续执行
                 ├── 修改 → 改参数后继续
                 └── 拒绝 → 直接结束
```

### 前提条件

Human-in-the-Loop **必须**搭配 Checkpointer 使用。原因很简单：暂停后图的状态需要"存档"，等人类确认后再"读档"继续。

```python
from langgraph.checkpoint.memory import MemorySaver

# ❌ 没有 checkpointer → 无法暂停
app = graph.compile()

# ✅ 有 checkpointer → 可以暂停
app = graph.compile(checkpointer=MemorySaver())
```

> **一句话概括**：Human-in-the-Loop = Checkpointer（存档） + interrupt（暂停） + update_state（人类修改） + invoke(None)（恢复执行）。

---

## 7.2 interrupt_before / interrupt_after —— 暂停执行

LangGraph 提供了两种暂停方式：在节点**执行前**暂停，或在节点**执行后**暂停。

### interrupt_before：在节点执行前暂停

```python
# 在 "tools" 节点执行前暂停
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["tools"]   # ← 关键参数
)
```

```
执行流程：

  START → Agent → 生成 tool_calls
                       │
              interrupt_before=["tools"]
                       │
                  [暂停！]  ← 图执行到这里停住
                       │
              人类审核 tool_calls
                       │
              invoke(None) 恢复
                       │
                       ↓
                    Tools → Agent → END
```

### interrupt_after：在节点执行后暂停

```python
# 在 "agent" 节点执行后暂停
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_after=["agent"]   # ← 节点执行完毕后暂停
)
```

```
区别：

  interrupt_before=["tools"]
  → Agent 执行完 → 暂停 → 人确认 → Tools 开始执行
  （人看到的是 Agent 生成的 tool_calls，还没执行工具）

  interrupt_after=["tools"]
  → Tools 执行完 → 暂停 → 人确认 → Agent 继续
  （人看到的是工具执行的结果，可以决定要不要给 Agent 看）
```

### 暂停后如何恢复

暂停后调用 `invoke(None)` 即可恢复执行：

```python
config = {"configurable": {"thread_id": "review_session"}}

# 第一次 invoke → 跑到 interrupt 点后暂停
result = app.invoke(
    {"messages": [HumanMessage(content="帮我删除文件 test.txt")]},
    config=config
)
# 图暂停了，result 返回到暂停前的 State

# 查看当前状态：Agent 要调用什么工具？
state = app.get_state(config)
print(state.values["messages"][-1].tool_calls)
# [{"name": "delete_file", "args": {"path": "test.txt"}}]

# 人类审核后决定继续
# 用 invoke(None) 恢复执行
result = app.invoke(None, config=config)
# → 从暂停点继续，执行 Tools → Agent → END
```

```
恢复执行的关键：

  invoke(None, config=config)
    │      │         │
    │      │         └── 用同一个 thread_id
    │      └──────────── 输入为 None（不传新数据）
    └─────────────────── 从上次暂停的位置继续
```

### 可以同时使用多个 interrupt

```python
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["tools"],          # 工具执行前暂停
    interrupt_after=["sensitive_action"]  # 敏感操作后暂停
)
```

> **核心理解**：`interrupt_before` / `interrupt_after` 就像给图的执行流程加了"红绿灯"。遇到指定节点就亮红灯（暂停），等人类"放行"（`invoke(None)`）后继续。

---

## 7.3 实战：工具调用前的人工审批

最经典的 Human-in-the-Loop 场景：Agent 要调用工具时，先暂停让人类审核，确认后再执行。

### 完整代码

```python
from langchain_deepseek import ChatDeepSeek
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# ====== 定义一个"危险"工具 ======
@tool
def delete_file(filename: str) -> str:
    """删除指定的文件。这是一个危险操作！

    Args:
        filename: 要删除的文件名
    """
    # 模拟删除（实际不真的删）
    return f"文件 '{filename}' 已被删除。"

@tool
def read_file(filename: str) -> str:
    """读取指定文件的内容。

    Args:
        filename: 要读取的文件名
    """
    return f"文件 '{filename}' 的内容是：Hello World"

# ====== 构建 Agent ======
tools = [delete_file, read_file]
llm = ChatDeepSeek(model="deepseek-chat", temperature=0).bind_tools(tools)

def agent(state: MessagesState):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: MessagesState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# ====== 构建图 ======
graph = StateGraph(MessagesState)
graph.add_node("agent", agent)
graph.add_node("tools", ToolNode(tools))

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")

# ====== 关键：interrupt_before ======
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["tools"]   # 在工具执行前暂停！
)

# ====== 使用流程 ======
config = {"configurable": {"thread_id": "approval_demo"}}

# Step 1: 发送请求 → Agent 生成 tool_calls → 暂停
print("=== Step 1: Agent 分析请求 ===")
result = app.invoke(
    {"messages": [HumanMessage(content="请删除 secret.txt 这个文件")]},
    config=config
)

# Step 2: 人类审核
state = app.get_state(config)
last_msg = state.values["messages"][-1]
print(f"\nAgent 想要调用的工具：")
for tc in last_msg.tool_calls:
    print(f"  工具: {tc['name']}")
    print(f"  参数: {tc['args']}")

# Step 3: 人类决策
human_decision = input("\n是否批准？(yes/no): ")

if human_decision.lower() == "yes":
    # 批准 → 恢复执行
    print("\n=== Step 3: 批准，继续执行 ===")
    result = app.invoke(None, config=config)
    print(result["messages"][-1].content)
else:
    # 拒绝 → 不继续，告诉用户
    print("\n操作已被人工拒绝。")
```

### 运行效果

```
=== Step 1: Agent 分析请求 ===

Agent 想要调用的工具：
  工具: delete_file
  参数: {'filename': 'secret.txt'}

是否批准？(yes/no): yes

=== Step 3: 批准，继续执行 ===
文件 'secret.txt' 已被成功删除。
```

```
如果输入 no：

是否批准？(yes/no): no

操作已被人工拒绝。
（工具没有执行，文件安全！）
```

> **要点**：整个流程的核心是 `interrupt_before=["tools"]` + `invoke(None)`。Agent 的"想法"（tool_calls）被暂停在那里，人类可以看了再决定是否放行。

---

## 7.4 修改 State 后恢复执行（update_state）

上一节我们实现了"批准/拒绝"两种选择。但实际场景中经常需要第三种操作：**修改后继续**——人类看了 Agent 的 tool_calls，觉得参数不对，改一下再让 Agent 继续。

### 场景

```
Agent: "我要调用 delete_file('important.db')"
人类:  "等等，你应该删的是 'temp.db'，不是 'important.db'！"
→ 修改 tool_calls 的参数 → 继续执行
```

### 修改 State 的三种方式

#### 方式一：修改 tool_calls 的参数

```python
from langchain_core.messages import AIMessage

config = {"configurable": {"thread_id": "edit_demo"}}

# Agent 在 interrupt 点暂停后...
state = app.get_state(config)
last_msg = state.values["messages"][-1]
print(f"Agent 要调用: {last_msg.tool_calls}")
# [{"name": "delete_file", "args": {"filename": "important.db"}, "id": "call_xxx"}]

# 人类修改参数：把 important.db 改成 temp.db
corrected_tool_calls = last_msg.tool_calls.copy()
corrected_tool_calls[0]["args"]["filename"] = "temp.db"

# 构造修正后的 AIMessage
corrected_message = AIMessage(
    content=last_msg.content,
    tool_calls=corrected_tool_calls,
    id=last_msg.id  # 保持同一个 ID，触发消息替换
)

# 用 update_state 替换 Agent 的消息
app.update_state(config, {"messages": [corrected_message]})

# 恢复执行（用修正后的参数调用工具）
result = app.invoke(None, config=config)
# → 删除的是 temp.db，不是 important.db！
```

#### 方式二：直接注入人类消息

```python
# 不修改 Agent 的 tool_calls，而是注入一条人类反馈
app.update_state(
    config,
    {"messages": [HumanMessage(content="不要删除文件，改为列出文件列表")]},
    as_node="agent"  # 假装这条消息是 agent 节点发出的
)

# 恢复执行 → Agent 会重新思考
result = app.invoke(None, config=config)
```

#### 方式三：跳过工具，直接给结果

```python
from langchain_core.messages import ToolMessage

# 不执行工具，直接提供"工具结果"
tool_call = state.values["messages"][-1].tool_calls[0]

app.update_state(
    config,
    {"messages": [ToolMessage(
        content="操作已取消：该文件受保护，不允许删除。",
        tool_call_id=tool_call["id"]
    )]},
    as_node="tools"  # 假装是 tools 节点返回的结果
)

# 恢复执行 → Agent 看到"工具结果"后组织回答
result = app.invoke(None, config=config)
# Agent: "抱歉，该文件受保护，无法删除。"
```

### as_node 参数

`update_state` 的 `as_node` 参数控制"这个更新假装是从哪个节点发出的"：

```
as_node="agent"  → 更新发生在 agent 节点的位置
                    → 恢复后执行 agent 之后的节点

as_node="tools"  → 更新发生在 tools 节点的位置
                    → 恢复后执行 tools 之后的节点（即 agent）

不指定 as_node   → 默认是最后一个执行的节点
```

> **核心模式**：`update_state` 给了人类**完全的控制权**——你可以修改参数、注入消息、甚至伪造工具结果。这使得 LangGraph 的 Human-in-the-Loop 不仅仅是"批准/拒绝"，而是真正的**人机协作**。

---

## 7.5 动态断点：根据条件决定是否中断

`interrupt_before` / `interrupt_after` 是**静态**的——每次执行到指定节点都会暂停。但有些场景下，你只想在**特定条件**下暂停。

### 场景

```
Agent 调用 read_file → 安全操作 → 不需要审批，直接执行
Agent 调用 delete_file → 危险操作 → 需要暂停审批！

如果用 interrupt_before=["tools"]，读文件也会暂停 → 太烦了。
我们需要"只有危险工具才暂停"。
```

### 方式一：在 Node 函数中使用 interrupt()

LangGraph 提供了 `interrupt()` 函数，允许你在 Node 内部按条件触发中断：

```python
from langgraph.types import interrupt

DANGEROUS_TOOLS = {"delete_file", "send_email", "execute_sql"}

def human_review_tools(state: MessagesState):
    """自定义工具执行节点：危险工具先审批"""
    last_message = state["messages"][-1]

    for tool_call in last_message.tool_calls:
        if tool_call["name"] in DANGEROUS_TOOLS:
            # 触发中断，等待人类确认
            human_response = interrupt({
                "question": f"Agent 要调用危险工具 '{tool_call['name']}'，参数: {tool_call['args']}。是否批准？",
                "tool_call": tool_call
            })

            if human_response.get("action") != "approve":
                # 人类拒绝 → 返回拒绝消息
                return {"messages": [ToolMessage(
                    content=f"操作被拒绝：{human_response.get('reason', '用户拒绝')}",
                    tool_call_id=tool_call["id"]
                )]}

    # 所有工具都通过审核（或没有危险工具）→ 正常执行
    tool_node = ToolNode(tools)
    return tool_node.invoke(state)
```

### 方式二：用条件边实现审批路由

另一种思路——在 Agent 和 Tools 之间加一个"审批路由"节点：

```python
def approval_router(state: MessagesState) -> str:
    """根据工具类型决定走哪条路"""
    last_message = state["messages"][-1]
    tool_names = [tc["name"] for tc in last_message.tool_calls]

    if any(name in DANGEROUS_TOOLS for name in tool_names):
        return "needs_approval"  # 走审批路径
    return "safe_tools"          # 走直接执行路径

graph.add_conditional_edges("agent", approval_router, {
    "needs_approval": "human_review",  # 需要审批的路径
    "safe_tools": "tools",             # 安全工具直接执行
    END: END
})

# 只在 human_review 节点前暂停
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["human_review"]
)
```

```
动态审批的图结构：

  START → [Agent] → 危险工具？
                       ├── 是 → [human_review] → 暂停！→ [tools] → Agent
                       └── 否 → [tools] → Agent
                                              ↑ 直接执行，不暂停
```

### 两种方式对比

| 方式 | 优点 | 缺点 |
|------|------|------|
| `interrupt()` 函数 | 灵活，可在任意位置中断 | 需要自定义节点 |
| 条件边 + 静态 interrupt | 图结构清晰，易理解 | 需要多一个节点 |

> **实践建议**：简单场景用条件边（图结构清晰），复杂场景用 `interrupt()`（灵活性高）。两种方式可以混合使用。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Human-in-the-Loop | 让 Agent 在关键时刻暂停，等人类确认后继续 |
| 前提条件 | 必须搭配 Checkpointer 使用 |
| interrupt_before | 在指定节点**执行前**暂停 |
| interrupt_after | 在指定节点**执行后**暂停 |
| invoke(None) | 从暂停点恢复执行 |
| update_state | 人类修改 State 后恢复（修改参数、注入消息、伪造结果） |
| as_node | 控制 update 假装从哪个节点发出 |
| 动态断点 | `interrupt()` 函数或条件边实现按条件暂停 |

> **下一章预告**：子图与多智能体协作 —— 图中嵌套图、Supervisor 模式、Handoff 模式。从单 Agent 进化到多 Agent 团队协作。


