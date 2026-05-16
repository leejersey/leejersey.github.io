# DeepAgent 完全指南：从 ReAct 循环到端到端深度推理 Agent

> 传统 Agent 像个"只会按菜谱做菜的厨师"——你给它工具清单，它按步骤执行。DeepAgent 像个"会自己逛超市找食材的大厨"——它能自主发现工具、压缩记忆、在长时程任务中持续深度推理。

---

## 1. 为什么传统 Agent 架构不够用

2023 年你用 LangChain 搭了一个 ReAct Agent，接上搜索引擎和计算器，它能回答"今天天气怎么样"和"123×456 等于多少"。你觉得 AI Agent 的时代来了。

2025 年你让同一个 Agent 做一份"竞品分析报告"——搜索 10 个竞品、整理各自的产品线、对比定价策略、生成结构化报告。它搜了 3 轮就开始重复自己，第 5 轮忘了前面搜过什么，第 8 轮直接幻觉了一个不存在的竞品。

**问题不在模型变笨了，而在架构太浅了。** 传统 Agent 被设计成"一次一个循环"的短程执行者，面对需要深度推理、持续记忆和动态工具使用的长程任务，它的架构从根子上就不够用。

### 1.1 ReAct 循环回顾：Think → Act → Observe

几乎所有传统 Agent 框架（LangChain Agent、AutoGPT 早期版本、BabyAGI）都基于同一个核心循环——**ReAct**：

```
ReAct 循环：

  ┌─────────────────────────────────────┐
  │                                     │
  │  Think：思考下一步该做什么            │
  │    ↓                                │
  │  Act：调用一个工具（搜索/计算/代码）   │
  │    ↓                                │
  │  Observe：观察工具返回的结果          │
  │    ↓                                │
  │  判断：任务完成了吗？                 │
  │    ├── 是 → 输出最终答案              │
  │    └── 否 → 回到 Think ←─────────────┘
  │
  └──────── 单次循环，每轮独立 ──────────┘
```

这个循环简洁优雅，在**简单任务**上表现极好。但它有一个隐含的假设：**每一轮循环是独立的，Agent 不需要"记住"太多历史，也不需要"规划"多步之后的行动。**

就像一个只会按菜谱做菜的厨师——你告诉他"第一步切洋葱，第二步热锅，第三步炒"，他能做出来。但如果你说"做一桌年夜饭"，他就懵了——因为他不会规划菜单、不会同时管多个灶台、也记不住前面做到哪了。

### 1.2 三大瓶颈：工具集固定、上下文爆炸、长程失控

**瓶颈一：工具集固定——你给它几个工具，它就只会用几个**

传统 Agent 启动时，工具列表是**写死在 System Prompt 里的**。5 个工具？每次推理都要把 5 个工具的描述塞进上下文。50 个工具？Prompt 直接爆了。5000 个工具（比如 RapidAPI 上的各种 API）？完全不可能。

```
传统 Agent 的工具注入：
  System Prompt = "你可以使用以下工具：
    1. search(query) - 搜索互联网
    2. calculator(expr) - 数学计算  
    3. weather(city) - 查天气
    ...就这 3 个，没了"
```

**瓶颈二：上下文爆炸——对话越长，Agent 越"痴呆"**

每轮 Think-Act-Observe 都会往上下文里追加内容。10 轮之后，上下文可能已经有 20K token——中间的信息开始被"遗忘"（Lost in the Middle 效应）。30 轮之后，即使模型支持 128K 上下文，大量的历史信息也变成了噪音，Agent 开始重复之前的行为或遗忘关键信息。

**瓶颈三：长程失控——走着走着就迷路了**

没有规划能力的 Agent 就像在迷宫里随机游走——每一步看起来都合理，但整体上毫无方向。它不会"先想清楚要做什么，再去做"，而是"走一步看一步"。在需要 20 步以上才能完成的任务中，这种策略的成功率急剧下降。

| 瓶颈 | 根因 | 典型症状 |
|------|------|---------|
| 工具集固定 | 工具描述写死在 Prompt 里 | 遇到新需求无法扩展，Prompt 过长 |
| 上下文爆炸 | 历史信息全部保留在上下文 | 重复行为、遗忘关键信息、幻觉 |
| 长程失控 | 缺乏规划，每步独立决策 | 20+ 步任务成功率骤降，目标漂移 |
### 1.3 从 Shallow Agent 到 Deep Agent：范式转换

这三个瓶颈不是通过"调参"或"换更好的模型"能解决的——它们需要**架构层面的变革**。

```
Shallow Agent（传统）：
  固定工具 + 全量上下文 + 逐步反应
  = 适合 5 步以内的简单任务

Deep Agent（新范式）：
  动态工具发现 + 记忆压缩 + 规划驱动 + 反思修正
  = 适合 50+ 步的复杂长程任务
```

| 维度 | Shallow Agent | Deep Agent |
|------|--------------|------------|
| 思维模式 | 反应式（ReAct 循环） | 规划驱动 + 反思修正 |
| 工具使用 | 固定工具箱（5-10 个） | 按需发现（5000+ 个） |
| 记忆管理 | 全量保留在上下文 | 结构化压缩 + 持久化 |
| 任务规模 | 短程（< 10 步） | 长程（50+ 步、跨小时/天） |
| 错误恢复 | 无（出错就崩） | 检查点 + 回滚 + 反思 |
| 控制结构 | 线性循环 | 层级委派（Orchestrator + Sub-agents） |

DeepAgent 就是为解决这些问题而生的。接下来的章节，我们会逐一拆解它的核心机制：**记忆折叠**（第 3 章）、**按需工具发现**（第 4 章）、**强化学习训练**（第 5 章）和**规划引擎**（第 6 章）。

> 💡 **核心洞察：** 从 Shallow Agent 到 Deep Agent 的转变，本质上是从"给模型塞更多 Prompt"到"给模型造一个大脑"的转变。大脑有工作记忆、有长期记忆、有规划能力、有反思能力——这些不是一个循环能搞定的。

---

## 2. DeepAgent 核心架构：端到端深度推理

上一章诊断了传统 Agent 的三大瓶颈。现在来看 DeepAgent 是怎么**从架构层面**解决这些问题的。

### 2.1 一句话定义：End-to-End Deep Reasoning Agent

**DeepAgent = 在单一连贯的推理过程中，自主完成思考、工具发现、动作执行和记忆管理的端到端 Agent。**

关键词拆解：
- **端到端（End-to-End）**：不依赖人为预定义的工作流模板，Agent 自己决定"接下来该干什么"
- **深度推理（Deep Reasoning）**：不是"想一步做一步"，而是在 extended thinking 中进行多步推理后再行动
- **自主（Autonomous）**：工具不是"给定的"，是"自己找的"；记忆不是"全量保留"，是"自己压缩的"

### 2.2 与传统架构的对比：预定义工作流 vs 自主推理

```
传统 Agent（预定义工作流）：

  开发者定义：
    Step 1 → 搜索
    Step 2 → 提取信息
    Step 3 → 生成报告
    
  Agent 照做，没有自主权

DeepAgent（自主推理）：

  Agent 自己想：
    "这个任务需要先了解背景…我需要一个搜索工具…
     让我从工具库里找找…找到了，调用它…
     结果不够详细，我需要换一个更专业的 API…
     之前搜过的内容先压缩存起来，继续深入…"

  Agent 自己走完全程
```

### 2.3 核心组件全景：思考引擎 + 工具发现 + 记忆折叠 + 动作执行

DeepAgent 的架构可以拆成四个核心组件：

```
DeepAgent 核心组件全景：

  ┌────────────────────────────────────────────┐
  │              思考引擎（Brain）               │
  │  Extended Thinking / Chain-of-Thought       │
  │  规划 + 推理 + 反思，一体化                   │
  └──────────┬─────────────┬───────────────────┘
             │             │
    ┌────────▼───────┐  ┌──▼──────────────┐
    │  工具发现        │  │  记忆折叠        │
    │  (Tool Discovery)│  │  (Memory Folding)│
    │                  │  │                  │
    │  从开放工具库    │  │  情景记忆         │
    │  动态检索        │  │  工作记忆         │
    │  按需调用        │  │  工具记忆         │
    └────────┬────────┘  └──┬───────────────┘
             │              │
    ┌────────▼──────────────▼──────────────┐
    │          动作执行（Action）            │
    │  工具调用 + 结果观察 + 状态更新         │
    └──────────────────────────────────────┘
```

四个组件的分工：

| 组件 | 职责 | 解决第 1 章的哪个瓶颈 |
|------|------|-------------------|
| 思考引擎 | 规划任务、推理决策、反思修正 | 长程失控 |
| 工具发现 | 从大规模工具库动态检索和调用工具 | 工具集固定 |
| 记忆折叠 | 压缩长交互历史为结构化记忆 | 上下文爆炸 |
| 动作执行 | 执行工具调用、观察结果、更新状态 | 基础执行层 |

> 💡 **核心设计哲学：** 传统 Agent 是"开发者给它造一条路，它沿着走"。DeepAgent 是"给它一个大脑和一双腿，它自己找路走"。路可能是弯的、可能要回头、可能要绕远——但它能到达传统 Agent 根本到不了的地方。

---

## 3. 自主记忆折叠：让 Agent 拥有"大脑"

记忆折叠（Autonomous Memory Folding）是 DeepAgent 最受脑科学启发的设计——它模仿人脑的记忆系统，把"所有信息全塞在脑子里"变成"重要的记住、不重要的压缩、用过的归档"。

### 3.1 上下文窗口的天花板：为什么 128K Token 也不够

你可能觉得"模型支持 128K 上下文，够用了吧？"

做个简单的算术：一个复杂任务需要 30 轮工具调用，每轮的 Think + Act + Observe 平均消耗 2K token。30 轮下来就是 60K token，加上 System Prompt 和工具描述，**你已经用掉了一半的上下文窗口。** 如果任务需要 100 轮呢？200K token——任何模型都装不下。

更要命的是 **Lost in the Middle 效应**——即使装得下，模型对中间位置信息的注意力也会衰减。第 5 轮的搜索结果被第 20 轮的内容"淹没"了，Agent 就会重复搜索同样的东西。

```
上下文窗口的困境：

  轮次:  1   5   10   15   20   25   30
  Token: 2K  10K  20K  30K  40K  50K  60K
                          ↑
                     注意力开始衰减
                     Agent 开始重复行为
```

### 3.2 三种结构化记忆：情景、工作、工具

DeepAgent 的解法借鉴了认知科学中的**人脑记忆模型**——把一锅粥式的上下文拆成三种功能不同的记忆：

```
三种结构化记忆：

  ┌─────────────────────────────────────┐
  │  情景记忆（Episodic Memory）         │
  │  "我之前做过什么"                    │
  │  存储：关键决策、转折点、里程碑       │
  │  类比：日记本                        │
  ├─────────────────────────────────────┤
  │  工作记忆（Working Memory）          │
  │  "我当前在做什么"                    │
  │  存储：当前子任务的上下文、中间结果   │
  │  类比：书桌上摊开的资料               │
  ├─────────────────────────────────────┤
  │  工具记忆（Tool Memory）             │
  │  "我用过什么工具、结果怎么样"         │
  │  存储：工具调用历史、成功/失败经验    │
  │  类比：工具使用手册上的笔记           │
  └─────────────────────────────────────┘
```

| 记忆类型 | 存什么 | 什么时候用 | 保留多久 |
|---------|--------|----------|---------|
| 情景记忆 | 关键决策和转折点 | 规划下一步时回顾 | 整个任务周期 |
| 工作记忆 | 当前子任务的详细上下文 | 执行当前步骤 | 子任务完成后压缩 |
| 工具记忆 | 工具调用的输入/输出摘要 | 决定调什么工具 | 按相关性保留 |

### 3.3 记忆折叠的触发机制与压缩策略

记忆折叠不是"到了某个阈值就全部压缩"——它是**自主的、渐进的**：

```
记忆折叠触发条件：

  条件 1：上下文使用率 > 70%
    → 压缩最旧的工具记忆（保留摘要，丢弃原始输出）

  条件 2：当前子任务完成
    → 将工作记忆压缩为情景记忆中的一条记录
    → 释放工作记忆空间给下一个子任务

  条件 3：Agent 主动判断"这段信息后面不太会用到"
    → 类似人脑的"选择性遗忘"
```

压缩策略的核心是**保留决策相关信息，丢弃执行细节**：

| 压缩前 | 压缩后 |
|--------|-------|
| "调用 search('Python 异步编程')，返回了 10 条结果：1. 《Python asyncio 完全指南》……（2000 token）" | "搜索了 Python 异步编程，找到 10 条相关结果，最有价值的是 asyncio 和 trio 两个框架" |
| "执行 calculate(3.14159 * 25)，结果是 78.53975" | "计算了圆的面积，结果约 78.5" |

压缩比通常在 **5:1 到 10:1** 之间——30 轮交互的 60K token 可以压缩到 6-12K token，轻松装进上下文。

### 3.4 与外部文件系统的协同：持久化记忆

记忆折叠解决了"单次会话内"的上下文问题。但如果任务需要**跨会话**（今天做一半，明天继续），就需要把记忆**持久化到文件系统**：

```
持久化记忆架构：

  Agent 运行时内存               文件系统
  ┌──────────────┐         ┌──────────────────┐
  │ 工作记忆      │ ──存档→ │ workspace/        │
  │ 情景记忆      │ ──存档→ │ ├── episodes.md   │
  │ 工具记忆      │ ──存档→ │ ├── tools_log.md  │
  └──────────────┘         │ └── state.json    │
                           └──────────────────┘
         ↑                          │
         └───── 下次启动时加载 ──────┘
```

这就是 LangChain DeepAgents 中 `write_file` / `read_file` 工具的本质——它不只是"Agent 可以读写文件"，更是**Agent 的外部大脑**。Claude Code 的 CLAUDE.md、Cursor 的 .cursorrules，本质上都是持久化记忆的具体实现。

> 💡 **核心洞察：** 记忆折叠的哲学来自一个简单的观察——**人不需要记住做过的每一件事，只需要记住关键决策和教训。** Agent 也一样。与其让上下文窗口越来越大（硬件解法），不如让 Agent 学会"记重要的、忘不重要的"（软件解法）。

---

## 4. 按需工具发现：从固定工具箱到开放工具市场

传统 Agent 的工具是"出生就决定了的"——开发者在 System Prompt 里写死 5 个工具，Agent 一辈子只会用这 5 个。DeepAgent 的工具发现机制让 Agent **像人类一样，需要什么就去"市场"上找什么**。

### 4.1 固定工具箱的局限：5 个工具 vs 5000 个工具

```
固定工具箱的困境：

  场景：用户问"帮我查一下上海到东京的航班"
  
  传统 Agent 的工具箱：[search, calculator, weather]
  Agent："我没有航班查询工具，只能用 search 搜一下…"
  → 结果质量差，可能过时

  DeepAgent 的工具市场：[RapidAPI 上的 5000+ 个 API]
  Agent："让我找找有没有航班 API…找到了 Skyscanner API…调用它"
  → 直接返回实时航班数据
```

这个差异在**垂直领域**尤其明显——你不可能提前预知用户会问什么，也不可能把所有可能用到的工具都塞进 Prompt。

### 4.2 工具检索管线：Query → 候选 → 选择 → 调用

DeepAgent 的工具发现是一个**四步管线**：

```
工具检索管线：

  ① Agent 推理："我需要一个能查航班的工具"
     ↓
  ② 生成查询：query = "flight search API real-time"
     ↓
  ③ 向量检索：从工具注册中心检索 Top-K 候选工具
     候选 1：Skyscanner API（相似度 0.92）
     候选 2：Google Flights API（相似度 0.87）
     候选 3：天气 API（相似度 0.31）← 过滤掉
     ↓
  ④ 选择 + 调用：Agent 阅读工具文档，选择最合适的
     → 调用 Skyscanner API，传入参数
     → 获取结果
```

### 4.3 开放工具集（Open-set）vs 标注工具集（Labeled）

DeepAgent 论文中区分了两种场景：

| 场景 | 说明 | 工具来源 | 难度 |
|------|------|---------|------|
| 标注工具集 | 任务预先标注了"应该用哪些工具" | 由评测方提供 | ⭐⭐ |
| 开放工具集 | 不告诉 Agent 用什么工具，自己找 | 从 RapidAPI 等平台检索 | ⭐⭐⭐⭐⭐ |

**开放工具集是 DeepAgent 的核心创新点**——在 ToolBench 基准测试中，大多数 Agent 框架只支持标注工具集（你告诉它用哪个 API），而 DeepAgent 能在 16,000+ 个 RapidAPI 工具中自主检索并调用正确的工具。

### 4.4 工具描述的向量化与语义匹配

工具检索的关键是**把工具描述变成向量**，让 Agent 能通过语义匹配找到合适的工具：

```python
# 工具注册中心的构建（离线）
tools_registry = []
for api in rapidapi_catalog:
    embedding = embed_model.encode(
        f"{api.name}: {api.description}\n"
        f"Parameters: {api.params}\n"
        f"Returns: {api.response_format}"
    )
    tools_registry.append({"api": api, "embedding": embedding})

# 运行时检索（在线）
def discover_tool(agent_query: str, top_k=5):
    query_embedding = embed_model.encode(agent_query)
    candidates = vector_search(query_embedding, tools_registry, top_k)
    return candidates
```

> 💡 **关键洞察：** 按需工具发现本质上是一个"工具版的 RAG"——只不过检索的不是文档块，而是工具描述。向量相似度匹配让 Agent 能从几千个工具中秒级定位到合适的那一个。

---

## 5. ToolPO：用强化学习教 Agent 使用工具

Agent 会"找工具"了（第 4 章），但怎么教它"用好工具"？DeepAgent 提出了 **ToolPO**——一种专门为工具调用设计的端到端强化学习训练策略。

### 5.1 为什么监督微调（SFT）不够：工具调用的探索性

传统的做法是收集"正确的工具调用轨迹"，然后用 SFT 训练模型模仿。问题在于：

```
SFT 的局限：

  训练数据："用户问航班 → 调 Skyscanner API → 成功"
  
  但现实中：
  - 同一个任务可能有多种正确的工具选择
  - 有些工具调用"部分正确"（参数错了但方向对了）
  - 有些失败的尝试也是有价值的学习经验

  SFT 只能学"一条正确路径"，学不到"在多条路径中选最优"
```

这就是强化学习（RL）的用武之地——RL 允许 Agent **探索不同的工具调用策略，通过奖励信号找到最优解**。

### 5.2 ToolPO 训练框架：LLM 模拟 API + 强化学习

ToolPO 的核心创新是用 **LLM 来模拟 API 的行为**——不需要真的调用几千个 API，只需要让一个 LLM 扮演 API 返回合理的结果：

```
ToolPO 训练循环：

  ① Agent（待训练的 LLM）接收任务
     ↓
  ② Agent 推理并生成工具调用
     → call(flight_search, {from: "上海", to: "东京"})
     ↓
  ③ 模拟器（另一个 LLM）扮演 API 返回结果
     → {"flights": [{"airline": "ANA", "price": 2500}...]}
     ↓
  ④ Agent 继续推理，可能再调用工具
     ↓
  ⑤ 任务完成，评估奖励
     → 正确完成 = +1，部分完成 = +0.5，失败 = 0
     ↓
  ⑥ 用 PPO/DPO 更新 Agent 的策略
```

用 LLM 模拟 API 的好处：**训练成本降低 100x**，不用真的调几千次付费 API。

### 5.3 细粒度信用归因：只奖励工具调用 Token

传统 RL 训练的奖励是"整条轨迹对或错"——但一条 50 步的轨迹中，可能只有第 23 步的工具选择是关键的。**ToolPO 的创新是 tool-call advantage attribution**——把奖励精确归因到"工具调用相关的 Token"上：

```
信用归因示例：

  Token 序列：
  "我需要查航班…" ← 普通推理 Token，标准奖励
  "<tool_call>flight_search({...})</tool_call>" ← 工具调用 Token，加权奖励
  "结果显示有3个航班…" ← 普通 Token
  "<tool_call>price_compare({...})</tool_call>" ← 工具调用 Token，加权奖励
  "综合比较，推荐…" ← 普通 Token

  只有工具调用 Token 获得额外的优势奖励/惩罚
```

这让模型学到的是"**什么时候该调什么工具**"，而不是"如何把推理写得好看"。

### 5.4 训练数据构造：从 ToolBench 到合成数据

训练 ToolPO 需要大量多样的任务-工具对：

| 数据源 | 内容 | 规模 |
|--------|------|------|
| ToolBench | 来自 RapidAPI 的 16K+ 工具 + 人工标注的任务 | ~12K 任务 |
| API-Bank | 多领域 API 调用数据集 | ~3K 任务 |
| 合成数据 | 用 GPT-4 生成新任务+工具组合 | 可无限扩展 |

> 💡 **核心认知：** ToolPO 的价值不在于"让模型调用工具"——任何 LLM 加个 function calling 就能调工具。它的价值在于**让模型学会在海量工具中自主选择最合适的那一个**，并且在错误中学习改进。这是从"能用工具"到"善用工具"的质变。

---

## 6. 规划引擎与层级委派：复杂任务的分治策略

前面三章讲了 DeepAgent 的"硬件"——记忆、工具、训练。本章讲它的"软件"——**怎么把一个大任务拆成小任务，然后有条不紊地执行完**。

### 6.1 规划先于行动：结构化任务分解

DeepAgent 的第一条铁律：**先规划，再动手。**

```
传统 Agent：
  "帮我做竞品分析" → 直接开始搜索 → 搜着搜着就迷路了

DeepAgent：
  "帮我做竞品分析" → 先生成 TODO List：
  
  - [ ] 1. 确定分析维度（产品功能/定价/市场份额）
  - [ ] 2. 搜索并列出 Top 5 竞品
  - [ ] 3. 逐个收集竞品的产品信息
  - [ ] 4. 逐个收集竞品的定价策略
  - [ ] 5. 制作对比表格
  - [ ] 6. 撰写分析报告

  → 按 TODO List 逐步执行，每完成一项打勾
```

这个 TODO List 不是形式主义——它是 Agent 的**导航地图**，防止目标漂移。

### 6.2 Orchestrator + Sub-Agent 层级架构

对于复杂任务，单个 Agent 忙不过来。DeepAgent 引入了**层级委派**模式：

```
层级委派架构：

  ┌──────────────────────────────────┐
  │  Orchestrator（编排器）           │
  │  负责：规划、分配、验收            │
  └──────┬──────────┬──────────┬─────┘
         │          │          │
  ┌──────▼────┐ ┌──▼──────┐ ┌▼─────────┐
  │ 搜索 Agent │ │代码 Agent│ │ 分析 Agent│
  │ 工具：     │ │工具：    │ │ 工具：    │
  │ search     │ │ python   │ │ calculator│
  │ browser    │ │ bash     │ │ chart     │
  └────────────┘ └─────────┘ └──────────┘
```

Orchestrator 自己不执行具体任务——它只做三件事：**拆任务、派活、验收**。每个 Sub-Agent 专注于自己擅长的领域，拥有自己的工具集和记忆空间。

### 6.3 防止目标漂移：检查点与进度验证

长程任务最大的风险是**目标漂移**——做着做着忘了最初的目标，开始"跑偏"。DeepAgent 用两个机制防止这个问题：

**机制一：检查点（Checkpoint）**
每完成一个子任务，保存当前状态。如果后续出错，可以回滚到上一个检查点而不是从头开始。

**机制二：进度验证**
每 N 步回顾一次 TODO List，检查：
- 已完成的任务是否真的完成了？（质量检查）
- 当前正在做的是否还在正确的方向上？（方向检查）
- 是否需要调整计划？（动态重规划）

### 6.4 反思机制：执行后的自我评估与修正

DeepAgent 在每个子任务完成后会进行**自我反思**：

```
反思 Prompt 模板：

  "我刚刚完成了 [子任务名称]。
   
   结果评估：
   - 信息是否完整？
   - 有没有遗漏的重要方面？
   - 结果质量是否达到预期？
   
   如果不满意，我应该：
   - 重做这个步骤？
   - 补充额外的搜索？
   - 还是接受当前结果继续前进？"
```

反思机制让 Agent 从"执行者"升级为"执行者+审查者"。它可能会决定"这个搜索结果太浅了，再搜一次"，也可能会决定"这个已经足够好了，节省时间继续下一步"。

> 💡 **核心原则：** 规划引擎的哲学是"磨刀不误砍柴工"——花 10% 的时间做规划，可以节省 50% 的执行时间和 90% 的重做时间。没有规划的 Agent 就是在烧钱。

---

## 7. LangChain DeepAgents 实战：从零搭建

理论到此为止，现在**写代码**。LangChain 官方的 `deepagents` 包是目前最成熟的 Deep Agent 工程框架，基于 LangGraph 构建。

### 7.1 环境搭建与依赖安装

```bash
# 创建虚拟环境
python -m venv deepagent-env
source deepagent-env/bin/activate

# 安装核心依赖
pip install langchain langgraph langchain-openai
pip install langchain-community  # 社区工具包

# 设置 API Key
export OPENAI_API_KEY="sk-your-key"
```

### 7.2 核心概念：LangGraph 状态机 + 检查点

LangGraph 是 Deep Agent 的"底盘"——它把 Agent 的执行过程建模为**状态机**：

```
LangGraph 状态机：

  [Start] → [Plan] → [Execute] → [Reflect] → [Done?]
              ↑                      │           │
              └──────── 否 ──────────┘           │
                                            [Output]
```

关键特性：
- **检查点（Checkpointing）**：每个状态转换自动保存，支持断点恢复
- **流式输出（Streaming）**：执行过程实时可见，不用等到最后
- **持久化（Persistence）**：用 SQLite/PostgreSQL 存储状态，跨会话可恢复

### 7.3 第一个 Deep Agent：带规划和文件系统的研究助手

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_community.tools import TavilySearchResults
from langchain_core.tools import tool

# 定义工具
search = TavilySearchResults(max_results=5)

@tool
def write_file(filename: str, content: str) -> str:
    """将内容写入文件（Agent 的外部记忆）"""
    with open(f"workspace/{filename}", "w") as f:
        f.write(content)
    return f"已写入 {filename}"

@tool
def read_file(filename: str) -> str:
    """读取文件内容"""
    with open(f"workspace/{filename}", "r") as f:
        return f.read()

@tool
def write_todos(todos: str) -> str:
    """创建或更新任务清单"""
    with open("workspace/todos.md", "w") as f:
        f.write(todos)
    return "任务清单已更新"

# 创建 Agent
llm = ChatOpenAI(model="gpt-4o", temperature=0)
agent = create_react_agent(
    llm, 
    tools=[search, write_file, read_file, write_todos]
)

# 执行任务
result = agent.invoke({
    "messages": [("user", "帮我做一份 2025 年 AI Agent 框架的竞品分析报告")]
})
```

### 7.4 子 Agent 委派实战：代码 + 搜索 + 分析

```python
from langgraph.graph import StateGraph, MessagesState

# 定义子 Agent
search_agent = create_react_agent(llm, tools=[search])
code_agent = create_react_agent(llm, tools=[python_repl])
writer_agent = create_react_agent(llm, tools=[write_file])

# 编排器：根据任务类型分派
def orchestrator(state: MessagesState):
    last_msg = state["messages"][-1].content
    if "搜索" in last_msg or "查找" in last_msg:
        return "search"
    elif "代码" in last_msg or "计算" in last_msg:
        return "code"
    else:
        return "writer"

# 构建状态图
graph = StateGraph(MessagesState)
graph.add_node("search", search_agent)
graph.add_node("code", code_agent)
graph.add_node("writer", writer_agent)
graph.add_conditional_edges("orchestrator", orchestrator)
```

### 7.5 Human-in-the-Loop：关键节点的人工介入

对于高风险操作（发邮件、修改数据库、提交代码），Agent 应该**暂停并等待人工确认**：

```python
from langgraph.checkpoint.memory import MemorySaver

# 在关键节点设置中断点
graph.add_node("human_review", lambda state: state)  # 暂停节点
graph.add_edge("execute", "human_review")  # 执行后需要人工审查

# 带检查点的编译
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer, interrupt_before=["human_review"])
```

> 💡 **务实建议：** 如果你是第一次搭 Deep Agent，从最简版开始——一个 LLM + search + write_file + write_todos，这四个工具就足以体验到"规划+记忆+执行"的完整循环。不要一开始就搞多 Agent 编排。

---

## 8. 学术 DeepAgent 复现：从论文到代码

第 7 章用 LangChain 从工程角度搭建了 Deep Agent。本章换个视角——**从学术论文出发**，复现中国人民大学团队发表的 DeepAgent 研究。

### 8.1 论文架构解读：端到端推理流程图

论文《DeepAgent: A General Reasoning Agent with Scalable Toolsets》（WWW 2026）的核心架构：

```
DeepAgent 论文架构：

  输入任务
    ↓
  ┌──────────────────────────────────┐
  │  Deep Reasoning（深度推理过程）    │
  │                                   │
  │  <think>                         │
  │    分析任务 → 需要什么工具？       │
  │    从工具库检索候选 → 选择最优     │
  │    制定行动计划                    │
  │  </think>                        │
  │                                   │
  │  <tool_call>                     │
  │    调用选中的工具                  │
  │  </tool_call>                    │
  │                                   │
  │  <observe>                       │
  │    观察结果 → 是否需要更多工具？   │
  │  </observe>                      │
  │                                   │
  │  [记忆折叠：压缩历史，继续推理]    │
  │                                   │
  └──────────────────────────────────┘
    ↓
  最终答案
```

与传统 ReAct 的关键区别：**Think-Act-Observe 不是分离的循环，而是融合在一个连贯的推理流中。**

### 8.2 开源代码：github.com/RUC-NLPIR/DeepAgent

```bash
# 克隆代码
git clone https://github.com/RUC-NLPIR/DeepAgent.git
cd DeepAgent

# 安装依赖
pip install -r requirements.txt
```

核心目录结构：

```
DeepAgent/
├── agent/              ← Agent 核心逻辑
│   ├── reasoning.py    ← 深度推理引擎
│   ├── memory.py       ← 记忆折叠模块
│   └── tool_retriever.py ← 工具检索模块
├── training/           ← ToolPO 训练代码
│   ├── toolpo.py       ← 强化学习训练
│   └── simulator.py    ← LLM API 模拟器
├── benchmarks/         ← 评测脚本
└── configs/            ← 配置文件
```

### 8.3 环境配置与工具注册中心搭建

```bash
# 1. 配置基础模型（支持 OpenAI API 或本地模型）
cp configs/config_template.yaml configs/my_config.yaml
# 编辑 my_config.yaml，填入 API Key 和模型选择

# 2. 构建工具注册中心（向量化工具描述）
python scripts/build_tool_registry.py \
  --tool_data data/toolbench_tools.json \
  --output tool_registry/

# 3. 验证安装
python -m agent.test_setup
```

### 8.4 在 ToolBench 和 GAIA 上跑基准测试

```bash
# ToolBench 评测（工具使用能力）
python benchmarks/run_toolbench.py \
  --config configs/my_config.yaml \
  --mode open_set \    # 开放工具集模式
  --output results/toolbench/

# GAIA 评测（通用 Agent 能力）
python benchmarks/run_gaia.py \
  --config configs/my_config.yaml \
  --output results/gaia/
```

> 💡 **复现提示：** 论文的完整复现需要较大的计算资源（ToolPO 训练需要 GPU）。如果只想体验推理阶段，可以直接使用论文提供的预训练模型权重，跳过训练步骤。

---

## 9. Deep Research 范式：超越单次问答的自主研究

Deep Research 是 DeepAgent 最直观的应用场景——它展示了"深度 Agent"和"浅层 Agent"的差距有多大。

### 9.1 什么是 Deep Research：从问答到研究报告

```
传统 RAG/Agent：
  用户："AI Agent 框架有哪些？"
  Agent："主要有 LangChain、AutoGPT、CrewAI…"（搜一次，回答一次）

Deep Research：
  用户："帮我研究 AI Agent 框架的发展趋势"
  Agent：花 30 分钟自主完成：
    → 搜索 50+ 篇文章
    → 识别 8 个主要框架
    → 整理各自的优劣势
    → 分析发展时间线
    → 生成 5000 字结构化报告（含引用来源）
```

### 9.2 核心流程：分解 → 搜索 → 合成 → 精炼 → 报告

```
Deep Research 五步流程：

  ① 分解：将大问题拆成 5-10 个子问题
     "发展趋势" → 框架列表 + 架构对比 + 社区活跃度 + 融资情况 + 技术方向
     
  ② 搜索：对每个子问题进行多轮搜索
     每轮根据上一轮结果调整搜索策略（迭代式）
     
  ③ 合成：将搜索结果整合为结构化笔记
     写入文件系统（持久化记忆）
     
  ④ 精炼：审查笔记，发现空白点，补充搜索
     "定价信息不够，再搜一轮"
     
  ⑤ 报告：从笔记中生成最终报告
     结构化输出 + 引用来源 + 数据表格
```

### 9.3 主流 Deep Research 产品对比

| 产品 | 提供方 | 模型基础 | 特点 |
|------|-------|---------|------|
| Deep Research | OpenAI | o3/o4-mini | 最强推理，支持文件上传 |
| Deep Research | Google Gemini | Gemini 2.5 | 搜索能力强，支持多模态 |
| Deep Research | Perplexity | 多模型 | 实时搜索，引用精确 |
| Claude with MCP | Anthropic | Claude 4 | 工具生态灵活 |
| 开源方案 | LangChain 等 | 可选 | 完全可控，成本可控 |

### 9.4 自建 Deep Research Agent 的架构模板

```python
# 最小可用的 Deep Research Agent 架构
class DeepResearchAgent:
    def __init__(self, llm, search_tool):
        self.llm = llm
        self.search = search_tool
        self.notes = {}  # 持久化笔记
    
    def run(self, question: str) -> str:
        # 1. 分解
        sub_questions = self.decompose(question)
        
        # 2-4. 对每个子问题：搜索 → 合成 → 精炼
        for sq in sub_questions:
            results = self.iterative_search(sq, max_rounds=3)
            self.notes[sq] = self.synthesize(results)
        
        # 5. 生成报告
        return self.generate_report(question, self.notes)
```

> 💡 **实用提示：** Deep Research 的核心不是"搜得多"，而是"知道什么时候该停"。好的 Deep Research Agent 会在信息饱和时自动停止搜索，而不是无限循环。

---

## 10. 性能评测与基准测试

"效果好不好"不能靠感觉——需要**量化评测**。本章梳理 Agent 领域的主要基准和 DeepAgent 的表现。

### 10.1 主流基准一览：ToolBench、GAIA、WebShop、ALFWorld

| 基准 | 评测能力 | 任务类型 | 规模 |
|------|---------|---------|------|
| ToolBench | 工具使用 | 调用 RapidAPI 完成指定任务 | 12K+ 任务 |
| API-Bank | API 调用 | 多领域 API 组合调用 | 3K+ 任务 |
| GAIA | 通用 Agent | 需要搜索+推理+工具的综合题 | 466 题 |
| WebShop | 网页操作 | 在模拟电商网站上购物 | 12K 商品 |
| ALFWorld | 具身交互 | 在虚拟房间中完成家务任务 | 3.5K 任务 |
| HLE | 高难推理 | 人类专家级别的困难问题 | 500 题 |

### 10.2 DeepAgent vs ReAct vs 其他 Agent 框架

论文报告的核心结果（部分摘录）：

| 框架 | ToolBench（Open-set） | GAIA | WebShop |
|------|---------------------|------|---------|
| ReAct | 42.3% | 31.2% | 54.7% |
| Reflexion | 48.7% | 35.6% | 61.2% |
| DFSDT | 51.2% | - | - |
| **DeepAgent** | **62.8%** | **45.3%** | **68.4%** |

DeepAgent 在**开放工具集**场景下优势最大——这正是记忆折叠和按需工具发现发挥作用的地方。

### 10.3 设计你自己的 Agent 评测基准

如果你要评测自己的 Deep Agent，建议从三个维度设计测试集：

| 维度 | 测什么 | 怎么测 |
|------|-------|-------|
| 任务完成率 | Agent 能不能完成任务 | 100 个任务，统计成功比例 |
| 效率 | 完成任务需要多少步/多少 Token | 记录每个任务的步数和 Token 消耗 |
| 鲁棒性 | 遇到工具报错/网络超时能不能恢复 | 人为注入 20% 的工具失败 |

### 10.4 评测陷阱：高分不等于好用

⚠️ **常见陷阱：**

- **基准过拟合**：模型可能"背住了"基准测试的答案模式，换个问法就不行了
- **延迟盲区**：基准只看结果对不对，不看花了多长时间。一个花 10 分钟才完成的 Agent 在实际产品中不可用
- **成本忽略**：调了 200 次 GPT-4o 才完成一个任务，准确率 100%——但成本 $5/任务，生产中用不起

> 💡 **评测三角：** 完整的 Agent 评测应该同时看 **准确率 × 延迟 × 成本**，而不是只看准确率。

---

## 11. 生产部署与工程实践

把 Deep Agent 从 Demo 推到生产，需要回答四个问题：**挂了怎么办、钱够不够、安全吗、怎么管理它。**

### 11.1 可靠性工程：检查点、回滚与错误恢复

```
可靠性三层防线：

  第一层：自动重试
    工具调用失败 → 等待 2s → 重试（最多 3 次）
    
  第二层：检查点回滚
    子任务失败 → 回滚到上一个检查点 → 换一种策略重试
    
  第三层：人工兜底
    连续 3 次失败 → 暂停 Agent → 通知人工介入
```

### 11.2 成本控制：Token 预算与工具调用限流

| 控制手段 | 实现方式 | 效果 |
|---------|---------|------|
| Token 预算 | 设定单任务最大 Token 消耗 | 防止失控循环烧钱 |
| 工具调用限流 | 单任务最多 N 次工具调用 | 防止无限搜索/计算 |
| 模型降级 | 简单子任务用 mini 模型 | 降低 50-80% 成本 |
| 缓存 | 相同查询复用历史结果 | 避免重复 API 调用 |

```python
# Token 预算控制示例
MAX_TOKENS_PER_TASK = 100_000
MAX_TOOL_CALLS = 50

class BudgetGuard:
    def __init__(self):
        self.tokens_used = 0
        self.tool_calls = 0
    
    def check(self):
        if self.tokens_used > MAX_TOKENS_PER_TASK:
            raise BudgetExceeded("Token 预算耗尽")
        if self.tool_calls > MAX_TOOL_CALLS:
            raise BudgetExceeded("工具调用次数超限")
```

### 11.3 安全边界：沙箱执行与权限管控

Deep Agent 能执行代码、读写文件、调用 API——这意味着它也能**搞破坏**。生产环境必须设置安全边界：

- **沙箱执行**：代码运行在 Docker 容器中，限制文件系统和网络访问
- **权限分级**：读操作自动执行，写操作需要人工确认，删除操作默认禁止
- **敏感信息过滤**：自动检测并屏蔽 API Key、密码等敏感信息

### 11.4 与 Harness Engineering 的关系：给 Deep Agent 上马鞍

**Harness Engineering**（参见《Harness Engineering 完全指南》）是给 AI Agent 设计"基础设施"的工程范式。Deep Agent 和 Harness 的关系：

```
Deep Agent 是马，Harness 是马鞍：

  Deep Agent 提供：推理能力、工具使用、记忆管理
  Harness 提供：约束规则、质量检查、安全边界、可观测性

  没有 Harness 的 Deep Agent = 一匹脱缰的野马
  没有 Deep Agent 的 Harness = 一副没有马的马鞍
```

> 💡 **生产铁律：** Deep Agent 越强大，Harness 越重要。一个能自主执行 100 步任务的 Agent，比一个只会回答问题的 Chatbot 需要**多 10 倍的基础设施**来确保安全和可靠。

---

## 12. 延伸阅读与参考资料

### 12.1 核心论文

| 论文 | 核心贡献 |
|------|---------|
| [DeepAgent: A General Reasoning Agent with Scalable Toolsets (2025)](https://arxiv.org/abs/2510.21618) | 端到端深度推理 + 记忆折叠 + ToolPO |
| [ReAct: Synergizing Reasoning and Acting (2023)](https://arxiv.org/abs/2210.03629) | 奠定 Think-Act-Observe 循环范式 |
| [Reflexion: Language Agents with Verbal Reinforcement Learning (2023)](https://arxiv.org/abs/2303.11366) | Agent 自我反思机制 |
| [Toolformer: Language Models Can Teach Themselves to Use Tools (2023)](https://arxiv.org/abs/2302.04761) | LLM 自主学习工具使用 |
| [Voyager: An Open-Ended Embodied Agent (2023)](https://arxiv.org/abs/2305.16291) | 自动生成技能库 + 持久化记忆 |

### 12.2 开源框架与工具链

| 项目 | 用途 | 链接 |
|------|------|------|
| DeepAgent (RUC) | 学术参考实现 | [github.com/RUC-NLPIR/DeepAgent](https://github.com/RUC-NLPIR/DeepAgent) |
| LangGraph | Agent 状态机框架 | [github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) |
| LangChain DeepAgents | 生产级 Deep Agent 模板 | [github.com/langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) |
| CrewAI | 多 Agent 协作框架 | [github.com/crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) |
| AutoGen | 微软多 Agent 对话框架 | [github.com/microsoft/autogen](https://github.com/microsoft/autogen) |
| Tavily | Agent 专用搜索 API | [tavily.com](https://tavily.com/) |

### 12.3 社区资源与进阶教程

- [LangGraph Academy](https://academy.langchain.com/courses/intro-to-langgraph)：官方 LangGraph 教程
- [ToolBench Leaderboard](https://huggingface.co/spaces/ToolBench/ToolEval)：工具使用能力排行榜
- [GAIA Benchmark](https://huggingface.co/gaia-benchmark)：通用 Agent 能力评测
- [Agent Protocol](https://agentprotocol.ai/)：Agent 通信标准化协议

---

> **全书完。**
>
> DeepAgent 的核心就一句话：**让 Agent 从"按菜谱做菜的厨师"进化为"会自己逛超市、记菜谱、管厨房的大厨"。**
>
> 从今天开始：装一个 LangGraph，写一个 `write_todos` 工具，让你的 Agent 学会"先规划再动手"——这一步比你想的简单，效果比你想的惊艳。
>
> 祝你的 Agent 越来越深。 🧠
