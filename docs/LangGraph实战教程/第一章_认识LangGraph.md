# 第一章 认识 LangGraph

---

## 1.1 LangGraph 是什么 —— 一句话理解

**LangGraph = 用"图"来编排 AI Agent 工作流的 Python 框架。**

它来自 LangChain 团队，但解决的是一个全新的问题：让 LLM 应用不再只是"一条直线跑到底"，而是拥有**循环、分支、状态记忆和人工介入**的能力——就像一个真正会思考、会回头检查、会等你拍板的智能助手。

```
传统 LLM 链（Chain）：
  输入 → LLM → 输出
  输入 → LLM → 工具 → LLM → 输出
  单向流水线，跑完就结束。

LangGraph（Graph）：
  输入 → LLM → 决策
                ├── 需要工具 → 调工具 → 回到 LLM（循环！）
                ├── 需要人工确认 → 暂停等待 → 恢复执行
                └── 已完成 → 输出结果

  可以循环、可以分支、可以暂停、可以回溯。
```

### 核心定位

| 维度 | 说明 |
|------|------|
| 一句话 | 构建有状态的、多步骤的 AI Agent |
| 核心数据结构 | **有向图**（节点 = 工作步骤，边 = 控制流） |
| 设计哲学 | "Low-level" —— 给你最大控制力，而不是黑盒封装 |
| 开发语言 | Python（主要）/ JavaScript |
| 开源协议 | MIT |
| 版本 | 0.4.x+（2026 年初） |

> **一句话概括**：如果 LangChain 是"用链条串联 LLM 调用"，那 LangGraph 就是"用图结构编排 AI Agent 的完整行为"。

---

## 1.2 为什么需要 LangGraph

### 线性 Chain 的三大局限

你可能已经用过 LangChain 的 Chain 或 LCEL（LangChain Expression Language）。它们很好用——但当你的 Agent 变复杂时，会撞上三堵墙：

```
局限 1：不能循环

  Chain: A → B → C → 结束
  想让 C 发现结果不好后回到 A 重试？做不到。

  真实需求：AI 生成代码 → 运行出错 → 自动修复 → 再运行
  这需要循环！

局限 2：不能持久化

  用户问了第一轮，Agent 返回了结果。
  十分钟后用户问第二轮——Chain 已经忘了一切。

  真实需求：长时间运行的任务需要"存档/读档"
  服务器重启后还能从上次的位置继续。

局限 3：不能中断等人

  Chain 一旦启动，要么跑完要么报错，没有"暂停"。

  真实需求：Agent 准备删除一个文件 → 先问人"确定吗？"
  人点确认后再继续。
```

### LangGraph 如何解决

| 局限 | LangGraph 的方案 |
|------|-----------------|
| 不能循环 | **Edge 可以指回前面的节点**，天然支持循环 |
| 不能持久化 | **内置 Checkpointer**，每一步自动存档 |
| 不能中断等人 | **interrupt 机制**，在任意节点暂停等人类介入 |
| 状态丢失 | **全局 State** 贯穿整个图的执行生命周期 |

```
LangGraph 的执行模型：

  ┌──────────────────────────────────────┐
  │           StateGraph                  │
  │                                      │
  │  START → [Agent] → 需要工具？         │
  │              ↑        ├── 是 → [Tools]│
  │              │        └── 否 → END   │
  │              │              │         │
  │              └──────────────┘         │
  │              (循环回 Agent)            │
  │                                      │
  │  每一步都自动存档到 Checkpointer       │
  │  任意节点可以 interrupt 等待人类       │
  └──────────────────────────────────────┘
```

> **关键洞察**：LangGraph 不是"更好的 LangChain"，而是一个**全新的执行引擎**。LangChain 擅长"组合 LLM 调用"，LangGraph 擅长"编排 Agent 行为"。

---

## 1.3 LangGraph vs LangChain vs AutoGen vs CrewAI

2025-2026 年，AI Agent 框架百花齐放。理解它们各自的定位，才能做出正确的技术选型。

| 维度 | LangGraph | LangChain | AutoGen | CrewAI |
|------|----------|-----------|---------|--------|
| **定位** | Agent 编排引擎 | LLM 调用组合 | 多 Agent 对话 | 角色扮演多 Agent |
| **抽象级别** | Low-level（完全控制） | Mid-level | High-level | High-level |
| **核心概念** | State + Node + Edge | Chain + Prompt + Tool | Agent 对话 | Crew + Agent + Task |
| **循环支持** | ✅ 原生 | ❌ 不支持 | ✅ 对话循环 | ✅ 任务循环 |
| **持久化** | ✅ 内置 Checkpointer | ❌ 需自己实现 | ❌ 有限 | ❌ 有限 |
| **Human-in-the-Loop** | ✅ 原生 interrupt | ❌ 需自己实现 | ✅ 有限支持 | ❌ 无 |
| **可观测性** | ✅ LangSmith 深度集成 | ✅ LangSmith | ❌ 有限 | ❌ 有限 |
| **学习曲线** | 中等（需理解图概念） | 低 | 低 | 低 |
| **适合场景** | 生产级复杂 Agent | 简单 LLM 管道 | 研究/原型 | 快速原型 |

### 如何选型

```
你的需求是什么？

  只是串几个 LLM 调用？
  → LangChain / LCEL 就够了

  需要循环、分支、错误重试？
  → LangGraph ✅

  需要多个 Agent 互相"讨论"？
  → AutoGen 或 LangGraph 多 Agent

  想快速搭个多角色原型？
  → CrewAI

  需要上生产（持久化 + 可观测 + 人工审批）？
  → LangGraph ✅（目前唯一成熟方案）
```

> **关键判断**：如果你的 Agent 需要"像程序一样可靠地运行"（而不仅仅是一次性对话），LangGraph 是 2026 年最成熟的选择。

---

## 1.4 LangGraph 的核心三要素：State / Node / Edge

LangGraph 的整个世界观建立在三个概念上。理解了它们，就理解了 LangGraph 的 80%。

### State —— 共享记忆

State 是一个**字典（或 Pydantic 对象）**，它在整个图的执行过程中被**所有节点共享**。每个节点从 State 中读取数据，处理后把结果写回 State。

```
State 就像一个共享白板：

  ┌──────────────────────────────┐
  │          State (白板)         │
  │                              │
  │  messages: [用户说了什么...]   │
  │  tool_results: [工具返回...]  │
  │  final_answer: "..."        │
  │  step_count: 3              │
  └──────────────────────────────┘
         ↑ 读           ↑ 写
    ┌────┴────┐    ┌────┴────┐
    │ 节点 A  │    │ 节点 B  │
    │ (Agent) │    │ (Tools) │
    └─────────┘    └─────────┘
```

### Node —— 工作步骤

Node 就是一个**普通的 Python 函数**。它接收当前 State，做一些事情（调 LLM、查数据库、调 API……），然后返回对 State 的更新。

```python
def agent_node(state):
    """一个最简单的节点"""
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}  # 返回 State 更新
```

### Edge —— 控制流

Edge 决定了"执行完当前节点后，下一步去哪个节点"。有三种：

| 边类型 | 语法 | 说明 |
|--------|------|------|
| 普通边 | `graph.add_edge("A", "B")` | A 执行完后一定去 B |
| 条件边 | `graph.add_conditional_edges("A", route_fn)` | 根据函数返回值决定去哪 |
| 入口/出口 | `START` / `END` | 图的起点和终点 |

```
条件边的魔力——让 Agent 做决策：

  ┌────────┐     ┌─────────────┐
  │ Agent  │ ──→ │ 需要工具吗？ │
  └────────┘     └──────┬──────┘
       ↑               │
       │    ┌──── 是 ───┤
       │    ↓           │
  ┌────────┐       ┌────┴────┐
  │ Tools  │       │  END    │
  └────────┘       └─────────┘
       │              ← 否
       └──────────────────┘
         (用完工具回 Agent)
```

### 三要素的协作

```python
from langgraph.graph import StateGraph, START, END

# 1. 定义 State
class AgentState(TypedDict):
    messages: list

# 2. 定义 Node
def agent(state): ...
def tools(state): ...

# 3. 构建 Graph（用 Edge 连接 Node）
graph = StateGraph(AgentState)
graph.add_node("agent", agent)
graph.add_node("tools", tools)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_use_tools)
graph.add_edge("tools", "agent")

# 4. 编译并运行
app = graph.compile()
result = app.invoke({"messages": [("user", "今天天气怎么样？")]})
```

> **类比**：把 LangGraph 想象成一个**快递分拣中心**。State 是包裹上的标签（信息随包裹流转），Node 是分拣站（每站做一步处理），Edge 是传送带（决定包裹下一站去哪）。

---

## 1.5 整体架构概览

LangGraph 的执行分为四个阶段：**定义 → 编译 → 执行 → 持久化**。

```
┌─────────────────────────────────────────────────────┐
│                LangGraph 执行架构                     │
│                                                     │
│  Phase 1: 定义                                       │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐            │
│  │ State     │ │ Nodes    │ │ Edges    │            │
│  │ (TypedDict│ │ (函数)   │ │ (连线)    │            │
│  │  /Pydantic)│ │          │ │          │            │
│  └─────┬─────┘ └────┬─────┘ └────┬─────┘            │
│        └─────────────┼───────────┘                   │
│                      ↓                               │
│  Phase 2: 编译                                       │
│  ┌──────────────────────────┐                        │
│  │   StateGraph.compile()    │                       │
│  │   → 生成 CompiledGraph   │                        │
│  │   → 验证图结构            │                        │
│  │   → 挂载 Checkpointer    │                        │
│  └────────────┬─────────────┘                        │
│               ↓                                      │
│  Phase 3: 执行                                       │
│  ┌──────────────────────────┐                        │
│  │  app.invoke() / stream() │                        │
│  │  → 从 START 开始        │                         │
│  │  → 逐节点执行            │                        │
│  │  → 条件边做路由决策       │                        │
│  │  → 到 END 结束          │                         │
│  └────────────┬─────────────┘                        │
│               ↓                                      │
│  Phase 4: 持久化                                     │
│  ┌──────────────────────────┐                        │
│  │  Checkpointer            │                        │
│  │  → 每步后自动存档 State  │                         │
│  │  → 支持回溯、恢复、中断  │                         │
│  │  → 后端：内存/SQLite/PG  │                        │
│  └──────────────────────────┘                        │
└─────────────────────────────────────────────────────┘
```

### 关键组件一览

| 组件 | 作用 | 类比 |
|------|------|------|
| `StateGraph` | 定义图结构的蓝图 | 建筑图纸 |
| `CompiledGraph` | 可执行的图实例 | 盖好的房子 |
| `State` | 图执行过程中的共享数据 | 工厂流水线上的工单 |
| `Node` | 图中的工作步骤 | 流水线上的工位 |
| `Edge` | 节点之间的流转规则 | 传送带的路线 |
| `Checkpointer` | 状态持久化引擎 | 存档系统 |
| `START` / `END` | 图的入口和出口 | 工厂的进料口和出料口 |

### compile() 的常见参数

```python
app = graph.compile(
    checkpointer=MemorySaver(),       # 持久化后端
    interrupt_before=["human_review"], # 在哪些节点前暂停
    interrupt_after=["tools"],         # 在哪些节点后暂停
)
```

> **总结**：LangGraph 的使用流程永远是：**定义 State → 写 Node 函数 → 用 Edge 连线 → compile → invoke**。接下来的章节就是把每个步骤展开讲。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| LangGraph 定位 | 用图结构编排 AI Agent 工作流的 Python 框架 |
| vs Chain | Chain 是线性的；Graph 支持循环、分支、中断 |
| vs 其他框架 | LangGraph 偏 low-level，但生产特性最完善 |
| 核心三要素 | **State**（共享记忆）+ **Node**（工作步骤）+ **Edge**（控制流） |
| 执行四阶段 | 定义 → 编译 → 执行 → 持久化 |
| 设计哲学 | 给开发者最大控制力，不做黑盒封装 |

> **下一章预告**：动手搭建开发环境，安装 LangGraph，配置 LLM，运行你人生中第一个 Graph！


