# 多 Agent 协作架构设计

> 一个 Agent 能力有限，多个 Agent 协同工作才能解决复杂任务。本教程深入讲解多 Agent 系统的设计模式——从任务分解到角色分工，从通信机制到框架实战，带你构建能自主协作的 AI 团队。

---

## 1. 为什么需要多 Agent？

你已经会用单个 Agent 了——给它工具，让它自主决策。但当任务变复杂，一个 Agent 就像一个"全栈独狼"，什么都要干，最终什么都干不好。

### 1.1 单 Agent 的三大局限

```
单 Agent 的困境：

1️⃣ 角色混乱
   一个 Agent 既要搜索资料、又要写代码、又要审核质量
   → 就像让一个人同时当产品经理+开发+测试，质量难以保证

2️⃣ 上下文爆炸
   所有信息塞进一个对话窗口
   → Token 越来越多，模型注意力分散，后面的输出质量下降

3️⃣ 推理链过长
   复杂任务需要 10+ 步推理
   → 步骤越多，每一步出错的概率累积，最终结果不可靠
```

```python
# ❌ 单 Agent 处理复杂任务
agent = create_agent(
    tools=[search, write_code, review_code, write_docs, deploy],
    system_prompt="你是一个全能开发者，负责搜索、编码、测试、文档、部署..."
)
# 问题：Agent 不知道什么时候该用什么身份
# 搜索时可能跳去写代码，写文档时可能去部署

# ✅ 多 Agent 各司其职
researcher = create_agent(tools=[search], system_prompt="你是资深技术研究员...")
coder = create_agent(tools=[write_code], system_prompt="你是高级开发工程师...")
reviewer = create_agent(tools=[review_code], system_prompt="你是代码审查专家...")
# 每个 Agent 专注一件事，做到最好
```

### 1.2 多 Agent 的核心优势

| 优势 | 说明 | 类比 |
|:---|:---|:---|
| **专业化** | 每个 Agent 专注一个角色，prompt 更精准 | 公司里有产品、开发、测试分工 |
| **并行化** | 独立的 Agent 可以同时工作 | 多个人同时做不同的模块 |
| **可扩展** | 增加新能力只需加一个新 Agent | 新需求来了招个新人 |
| **容错性** | 一个 Agent 失败不影响其他 | 一个人请假了团队还能运转 |
| **可维护** | 每个 Agent 的 prompt 小而精 | 小函数比大函数好维护 |

```
单 Agent vs 多 Agent 效果对比（实际项目经验）：

任务：研究某个技术主题 → 写技术文章 → 审核质量

单 Agent：
  准确性: ⭐⭐⭐     （研究和写作混在一起，常遗漏关键点）
  格式质量: ⭐⭐     （没有独立审核，格式不统一）
  耗时: 1 轮对话     （但 token 用量很高）

多 Agent（研究员 + 作家 + 编辑）：
  准确性: ⭐⭐⭐⭐⭐  （研究员专注收集信息，更全面）
  格式质量: ⭐⭐⭐⭐  （编辑专门检查格式和逻辑）
  耗时: 3 轮对话     （但每轮 token 少，总成本相近）
```

### 1.3 什么时候该用多 Agent？决策框架

```
决策流程：你需要多 Agent 吗？

你的任务复杂度如何？
│
├── 单步骤，一个 prompt 就能搞定
│   → ❌ 不需要 Agent，更不需要多 Agent
│
├── 多步骤，但角色单一（搜索→总结）
│   → 用单 Agent + 工具就够了
│
├── 多步骤 + 多角色（研究→写作→审核）
│   → ✅ 适合多 Agent（顺序协作）
│
├── 多个独立子任务可并行
│   → ✅ 适合多 Agent（并行协作）
│
└── 需要不同视角的碰撞（辩论/brainstorm）
    → ✅ 适合多 Agent（讨论模式）
```

**具体场景示例：**

| 场景 | 推荐方案 | Agent 配置 |
|:---|:---|:---|
| 简单问答 | 单次 LLM 调用 | 不需要 Agent |
| 搜索+总结 | 单 Agent + 工具 | 1 个 Agent |
| 技术调研+写报告 | 多 Agent 顺序 | 研究员 → 作家 |
| 竞品分析 | 多 Agent 并行 | N 个分析员同时分析 |
| 代码开发+审查 | 多 Agent 层级 | Manager → Coder + Reviewer |
| 产品头脑风暴 | 多 Agent 讨论 | PM + 设计师 + 工程师 |

> 💡 **黄金原则**：能用单 Agent 解决的就不要用多 Agent。多 Agent 增加了复杂度、成本和调试难度——只有当任务真正需要**多角色协作**时才值得。

---

## 2. 多 Agent 协作模式

不同的任务适合不同的协作方式。这一章介绍四种最常用的模式。

### 2.1 顺序执行：流水线模式

最简单的多 Agent 模式——Agent A 的输出是 Agent B 的输入，依次传递。

```
流水线模式：

  研究员 ──→ 作家 ──→ 编辑 ──→ 最终输出
  (搜集资料)  (写初稿)  (润色审核)
```

```python
# 伪代码
async def pipeline(topic: str):
    # Agent 1：研究员收集资料
    research = await researcher.run(f"研究 {topic} 的最新进展")
    
    # Agent 2：作家基于资料写初稿
    draft = await writer.run(f"基于以下资料写一篇文章:\n{research}")
    
    # Agent 3：编辑审核润色
    final = await editor.run(f"审核并润色以下文章:\n{draft}")
    
    return final
```

**适用场景**：任务有明确的先后依赖，每一步的输出是下一步的输入。

### 2.2 并行执行：分治模式

多个 Agent 同时处理不同的子任务，最后汇总结果。

```
分治模式：

          ┌→ 分析员 A（分析竞品 1）──┐
  任务 ──→├→ 分析员 B（分析竞品 2）──├→ 汇总员 → 最终报告
          └→ 分析员 C（分析竞品 3）──┘
```

```python
import asyncio

async def parallel_analysis(competitors: list[str]):
    # 并行：多个分析员同时工作
    tasks = [
        analyst.run(f"深度分析 {comp} 的产品特点、优劣势")
        for comp in competitors
    ]
    results = await asyncio.gather(*tasks)
    
    # 汇总
    summary = await summarizer.run(
        f"综合以下分析报告，写出对比结论:\n" +
        "\n---\n".join(results)
    )
    return summary
```

**适用场景**：子任务之间相互独立，可以同时进行。大幅缩短总耗时。

### 2.3 层级管理：Manager-Worker 模式

一个 Manager Agent 负责任务分解和调度，多个 Worker Agent 执行具体任务。

```
Manager-Worker 模式：

  用户需求 → Manager（任务分解+调度）
                │
                ├──→ Coder（写代码）
                ├──→ Tester（写测试）
                └──→ DocWriter（写文档）
                │
             Manager（汇总+质检）→ 最终交付
```

```python
async def manager_worker(requirement: str):
    # Manager 分解任务
    plan = await manager.run(f"""分析以下需求，拆解为具体任务：
    {requirement}
    
    返回 JSON: [{{"agent": "coder/tester/doc", "task": "具体任务描述"}}]""")
    
    tasks = json.loads(plan)
    
    # 分配给 Workers 执行
    results = {}
    for task in tasks:
        agent = workers[task["agent"]]
        results[task["agent"]] = await agent.run(task["task"])
    
    # Manager 汇总质检
    final = await manager.run(f"检查以下工作成果，给出整体评估:\n{results}")
    return final
```

**适用场景**：复杂项目需要统一协调，Manager 充当"项目经理"角色。

### 2.4 辩论与共识：多角色讨论模式

多个 Agent 从不同角度发表观点，通过讨论达成共识。

```
辩论模式：

  主持人：  "我们来讨论是否应该用微服务架构"
  架构师：  "微服务适合大团队，但增加运维复杂度..."
  开发者：  "从开发效率看，单体更快..."
  运维：    "微服务的部署和监控成本不能忽视..."
  主持人：  "综合各方观点，结论是..."
```

```python
async def debate(topic: str, rounds: int = 3):
    history = []
    
    agents = {
        "architect": architect_agent,
        "developer": developer_agent,
        "ops": ops_agent,
    }
    
    for round in range(rounds):
        for role, agent in agents.items():
            response = await agent.run(
                f"讨论主题：{topic}\n"
                f"之前的讨论：{history}\n"
                f"请从 {role} 的角度发表观点，可以反驳他人观点。"
            )
            history.append({"role": role, "round": round, "content": response})
    
    # 主持人总结
    conclusion = await moderator.run(
        f"请基于以下讨论总结结论：\n{history}"
    )
    return conclusion
```

**适用场景**：需要多角度分析的决策问题，策略制定，风险评估。

### 2.5 模式选择指南

| 模式 | 适用场景 | 优点 | 缺点 |
|:---|:---|:---|:---|
| **流水线** | 明确的先后步骤 | 简单直观 | 不能并行，慢 |
| **分治** | 独立的子任务 | 并行快速 | 子任务必须独立 |
| **Manager-Worker** | 复杂项目统筹 | 灵活可控 | Manager 是瓶颈 |
| **辩论** | 需要多视角分析 | 结论更全面 | Token 消耗大 |

> 💡 **实际项目中经常混合使用**——比如 Manager 把任务分解后，一部分用流水线串行执行，一部分用分治并行执行。

---

## 3. Agent 间通信机制

多个 Agent 怎么交换信息？这是多 Agent 系统的"基础设施"。

### 3.1 消息传递：直接通信 vs 消息队列

```
两种通信方式：

直接通信（函数调用）：
  Agent A 的返回值 → 直接传给 Agent B
  ✅ 简单直接
  ❌ 耦合度高，不灵活

消息队列（事件驱动）：
  Agent A → 发消息到队列 → Agent B 从队列取消息
  ✅ 解耦，可异步
  ❌ 复杂度高
```

```python
# ── 方式 1：直接通信（适合简单场景） ──
result_a = await agent_a.run(task)
result_b = await agent_b.run(f"基于这些信息工作：{result_a}")

# ── 方式 2：消息队列（适合复杂场景） ──
from asyncio import Queue

message_bus = Queue()

async def agent_a_loop():
    result = await agent_a.run(task)
    await message_bus.put({"from": "agent_a", "content": result})

async def agent_b_loop():
    msg = await message_bus.get()
    result = await agent_b.run(f"收到消息：{msg['content']}")
```

### 3.2 共享状态：黑板模式（Blackboard）

所有 Agent 共享一块"黑板"，谁都可以读写，非常适合需要共享上下文的场景：

```python
from dataclasses import dataclass, field

@dataclass
class Blackboard:
    """共享黑板：所有 Agent 可读写"""
    topic: str = ""
    research_data: str = ""
    draft: str = ""
    review_comments: list = field(default_factory=list)
    final_output: str = ""
    metadata: dict = field(default_factory=dict)
    
    def log(self, agent_name: str, action: str):
        """记录操作日志"""
        self.metadata.setdefault("logs", []).append(
            {"agent": agent_name, "action": action}
        )

# 使用
board = Blackboard(topic="LangGraph 入门")

# 研究员写入调研结果
board.research_data = await researcher.run(board.topic)
board.log("researcher", "completed research")

# 作家读取调研，写入初稿
board.draft = await writer.run(f"基于：{board.research_data}")
board.log("writer", "completed draft")

# 编辑读取初稿，写入审核意见
board.review_comments.append(await editor.run(f"审核：{board.draft}"))
board.log("editor", "completed review")
```

**黑板模式 vs 消息传递：**

| 方面 | 黑板模式 | 消息传递 |
|:---|:---|:---|
| 数据访问 | 所有 Agent 共享 | 点对点 |
| 耦合度 | 低（通过黑板解耦） | 中（需要知道目标） |
| 适用场景 | 需要全局状态的任务 | 流水线式的任务 |
| 冲突风险 | 有（多 Agent 同时写） | 无 |

### 3.3 结构化消息协议设计

Agent 之间传递的不应该是随意的字符串，而是**结构化的消息**：

```python
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class MessageType(str, Enum):
    TASK = "task"           # 任务分配
    RESULT = "result"       # 任务结果
    FEEDBACK = "feedback"   # 反馈/审核
    QUESTION = "question"   # 提问/澄清
    ERROR = "error"         # 错误报告

class AgentMessage(BaseModel):
    """Agent 间通信的标准消息格式"""
    id: str
    from_agent: str
    to_agent: str
    type: MessageType
    content: str
    metadata: dict = {}
    timestamp: datetime = None
    
    def model_post_init(self, __context):
        if self.timestamp is None:
            self.timestamp = datetime.now()

# 使用
msg = AgentMessage(
    id="msg-001",
    from_agent="manager",
    to_agent="coder",
    type=MessageType.TASK,
    content="实现用户登录功能，支持 JWT 认证",
    metadata={"priority": "high", "deadline": "2024-03-20"},
)
```

### 3.4 上下文管理：如何传递长对话历史

多 Agent 系统最容易出问题的地方：**上下文太长，后面的 Agent 看不完前面所有的信息**。

```python
class ContextManager:
    """上下文管理器：控制传给每个 Agent 的信息量"""
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self.full_history = []
    
    def add(self, agent: str, content: str):
        self.full_history.append({"agent": agent, "content": content})
    
    def get_context_for(self, agent_role: str) -> str:
        """根据角色裁剪上下文"""
        if agent_role == "researcher":
            # 研究员只需要知道任务目标
            return self._get_latest("manager", n=1)
        
        elif agent_role == "writer":
            # 作家需要研究结果 + 任务要求
            return self._get_latest("researcher", n=1) + \
                   self._get_latest("manager", n=1)
        
        elif agent_role == "editor":
            # 编辑需要初稿 + 原始要求（不需要研究细节）
            return self._get_latest("writer", n=1) + \
                   self._get_latest("manager", n=1)
    
    def _get_latest(self, agent: str, n: int = 1) -> str:
        msgs = [h for h in self.full_history if h["agent"] == agent]
        return "\n".join(m["content"] for m in msgs[-n:])
```

> 💡 **核心原则**：每个 Agent 只应该收到它**需要的信息**，而不是全部的对话历史。信息过载会显著降低 Agent 的表现。

---

## 4. 框架实战：CrewAI

CrewAI 是目前最流行的多 Agent 框架之一，设计理念是"像组建一个团队一样组建 AI"。

### 4.1 CrewAI 核心概念：Agent / Task / Crew

```
CrewAI 的三个核心概念：

Agent（成员） → 有角色、目标、可用工具的 AI 个体
Task（任务）  → 需要完成的具体工作，指定由哪个 Agent 执行
Crew（团队）  → 一组 Agent + 一组 Task 的组合，定义协作方式
```

```bash
pip install crewai crewai-tools
```

### 4.2 定义 Agent 角色与工具

```python
from crewai import Agent
from crewai_tools import SerperDevTool, WebsiteSearchTool

# ── 研究员 Agent ──
researcher = Agent(
    role="资深技术研究员",
    goal="搜集关于 {topic} 的最新、最全面的技术信息",
    backstory="""你是一位有 10 年经验的技术研究员，
    擅长从海量信息中提炼关键洞察。你总是追求准确性，
    每一个结论都有信息来源支撑。""",
    tools=[SerperDevTool(), WebsiteSearchTool()],
    verbose=True,
    llm="deepseek/deepseek-chat",
)

# ── 作家 Agent ──
writer = Agent(
    role="技术内容作家",
    goal="基于研究资料撰写一篇高质量、易于理解的技术文章",
    backstory="""你是一位技术写作专家，擅长把复杂的技术概念
    用通俗的语言解释清楚。你的文章结构清晰，示例丰富。""",
    verbose=True,
    llm="deepseek/deepseek-chat",
)

# ── 编辑 Agent ──
editor = Agent(
    role="资深内容编辑",
    goal="审核文章质量，确保准确性、可读性和格式规范",
    backstory="""你是一位严格的编辑，有丰富的技术内容审核经验。
    你关注事实准确性、逻辑连贯性和读者体验。""",
    verbose=True,
    llm="deepseek/deepseek-chat",
)
```

### 4.3 任务编排与依赖关系

```python
from crewai import Task

# 任务 1：研究（无依赖）
research_task = Task(
    description="深入研究 {topic}，收集最新的技术资料、核心概念和实际应用案例。",
    expected_output="一份结构化的研究报告，包含：核心概念、技术原理、应用场景、优缺点分析。",
    agent=researcher,
)

# 任务 2：写作（依赖任务 1）
writing_task = Task(
    description="基于研究报告，撰写一篇面向中级开发者的技术文章。要求通俗易懂，有代码示例。",
    expected_output="一篇完整的技术文章，包含标题、引言、正文（3-5个章节）和总结。",
    agent=writer,
    context=[research_task],  # 告诉 CrewAI：先执行 research_task
)

# 任务 3：审核（依赖任务 2）
editing_task = Task(
    description="审核文章质量。检查事实准确性、代码正确性、逻辑连贯性。给出修改建议并直接修改。",
    expected_output="审核后的最终版文章，附带审核意见摘要。",
    agent=editor,
    context=[writing_task],
)
```

### 4.4 实操：构建一个内容创作团队

```python
from crewai import Crew, Process

# ── 组建团队 ──
content_crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.sequential,  # 顺序执行（流水线模式）
    verbose=True,
)

# ── 启动！──
result = content_crew.kickoff(inputs={"topic": "LangGraph 状态机"})
print(result)
```

**CrewAI 还支持层级模式：**

```python
# Manager 模式：让 Manager Agent 自动分配任务
manager_crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.hierarchical,     # 层级模式
    manager_llm="deepseek/deepseek-chat",  # Manager 用的模型
)
```

> 💡 **CrewAI 的优势**：API 设计最简洁直观，10 行代码就能跑起来一个多 Agent 团队。

---

## 5. 框架实战：AutoGen

AutoGen（微软）的核心理念不同于 CrewAI——它让 Agent 之间**自主对话**，而不是预先编排好任务流程。

### 5.1 AutoGen 核心概念：ConversableAgent / GroupChat

```
AutoGen 的核心设计：

ConversableAgent → 可以对话的 Agent（支持 LLM / 人类 / 代码执行）
  ├── AssistantAgent   → LLM 驱动的 Agent
  ├── UserProxyAgent   → 代表人类的 Agent（可执行代码）
  └── GroupChat        → 多个 Agent 的群聊

关键区别：
CrewAI  → "预定义任务 → 分配给 Agent"（任务驱动）
AutoGen → "Agent 自由对话 → 自然涌现结果"（对话驱动）
```

```bash
pip install autogen-agentchat
```

### 5.2 双 Agent 对话模式

```python
from autogen import AssistantAgent, UserProxyAgent

# ── 创建 Agent ──
assistant = AssistantAgent(
    name="程序员",
    system_message="""你是一个 Python 专家。
    用户给你需求，你写代码解决。
    代码要放在 ```python 代码块中。""",
    llm_config={"model": "deepseek-chat", "api_key": "..."},
)

user_proxy = UserProxyAgent(
    name="用户代理",
    human_input_mode="NEVER",      # 不需要人类确认
    code_execution_config={
        "work_dir": "coding",       # 代码执行目录
        "use_docker": False,        # 不用 Docker
    },
)

# ── 开始对话 ──
user_proxy.initiate_chat(
    assistant,
    message="写一个 Python 函数，计算斐波那契数列前 N 项，并画出折线图。",
)
# AutoGen 会自动：
# 1. 程序员写代码
# 2. 用户代理执行代码
# 3. 如果报错，程序员修改代码
# 4. 循环直到成功
```

### 5.3 GroupChat：多人讨论

```python
from autogen import GroupChat, GroupChatManager

# ── 定义多个 Agent ──
pm = AssistantAgent(
    name="产品经理",
    system_message="你是产品经理，负责需求分析和功能定义。",
    llm_config=llm_config,
)

architect = AssistantAgent(
    name="架构师",
    system_message="你是软件架构师，负责技术方案设计和技术选型。",
    llm_config=llm_config,
)

developer = AssistantAgent(
    name="开发者",
    system_message="你是高级开发者，负责编写代码和实现功能。",
    llm_config=llm_config,
)

tester = AssistantAgent(
    name="测试员",
    system_message="你是 QA 工程师，负责设计测试用例和发现 Bug。",
    llm_config=llm_config,
)

# ── 组建群聊 ──
group_chat = GroupChat(
    agents=[pm, architect, developer, tester],
    messages=[],
    max_round=12,                    # 最多 12 轮对话
    speaker_selection_method="auto", # 自动选择下一个发言者
)

manager = GroupChatManager(
    groupchat=group_chat,
    llm_config=llm_config,
)

# ── 启动讨论 ──
pm.initiate_chat(
    manager,
    message="我们需要开发一个简单的 TODO 应用，支持增删改查。请大家讨论技术方案。",
)
```

### 5.4 实操：构建一个代码开发团队

```python
# 完整的代码开发流程：需求 → 设计 → 编码 → 测试

coder = AssistantAgent(
    name="Coder",
    system_message="""你是一个资深 Python 开发者。
    - 代码要放在 ```python 代码块中
    - 代码要有完整的类型注解和文档字符串
    - 每个函数都要写单元测试""",
    llm_config=llm_config,
)

reviewer = AssistantAgent(
    name="Reviewer",
    system_message="""你是一个代码审查专家。
    - 检查代码质量、潜在 bug、安全问题
    - 检查是否有测试覆盖
    - 给出具体的改进建议（不要只说"不错"）""",
    llm_config=llm_config,
)

executor = UserProxyAgent(
    name="Executor",
    human_input_mode="NEVER",
    code_execution_config={"work_dir": "dev_output", "use_docker": False},
    default_auto_reply="请继续。如果任务已完成，回复 TERMINATE。",
    max_consecutive_auto_reply=5,
)

# 群聊：Coder 写代码 → Executor 执行 → Reviewer 审查 → 循环
dev_chat = GroupChat(
    agents=[coder, executor, reviewer],
    messages=[],
    max_round=15,
)

dev_manager = GroupChatManager(groupchat=dev_chat, llm_config=llm_config)

executor.initiate_chat(
    dev_manager,
    message="实现一个 LRU Cache，支持 get/put 操作，时间复杂度 O(1)。要求有完整的测试。",
)
```

> 💡 **AutoGen 的优势**：Agent 对话更自然灵活，代码自动执行+自动修复，特别适合编程类任务。

---

## 6. 框架实战：LangGraph 多 Agent

LangGraph 用**状态图（State Graph）**来编排 Agent，控制力最强，适合需要精确控制流程的场景。

### 6.1 LangGraph 实现多 Agent 的思路

```
LangGraph 的多 Agent 思路：

每个 Agent 是图中的一个节点（Node）
Agent 之间的流转由边（Edge）控制
状态（State）在节点之间传递

         ┌──→ researcher ──┐
start ──→│                  │──→ writer ──→ editor ──→ end
         └──→ analyst ─────┘
                    ↑ 条件路由
```

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    """多 Agent 共享的状态"""
    task: str
    research: str
    draft: str
    review: str
    next_agent: str
    messages: Annotated[list, operator.add]
```

### 6.2 Supervisor 模式：主管分配任务

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatOpenAI(model="deepseek-chat")

# ── Supervisor：决定下一步由谁执行 ──
def supervisor_node(state: AgentState) -> AgentState:
    response = llm.invoke([
        SystemMessage(content="""你是团队主管。根据当前进度，决定下一步交给谁：
        - "researcher"：需要搜集信息
        - "writer"：信息够了，可以写文章
        - "editor"：初稿写好了，需要审核
        - "FINISH"：任务完成
        只返回 Agent 名称，不要解释。"""),
        HumanMessage(content=f"任务: {state['task']}\n当前状态: {state}"),
    ])
    return {"next_agent": response.content.strip()}

# ── Worker 节点 ──
def researcher_node(state: AgentState) -> AgentState:
    result = llm.invoke([
        SystemMessage(content="你是技术研究员，搜集以下主题的关键信息。"),
        HumanMessage(content=state["task"]),
    ])
    return {"research": result.content, "messages": [f"研究完成"]}

def writer_node(state: AgentState) -> AgentState:
    result = llm.invoke([
        SystemMessage(content="你是技术作家，基于以下资料写文章。"),
        HumanMessage(content=f"资料：{state['research']}"),
    ])
    return {"draft": result.content, "messages": [f"初稿完成"]}

def editor_node(state: AgentState) -> AgentState:
    result = llm.invoke([
        SystemMessage(content="你是编辑，审核并润色文章。"),
        HumanMessage(content=f"初稿：{state['draft']}"),
    ])
    return {"review": result.content, "messages": [f"审核完成"]}

# ── 构建状态图 ──
graph = StateGraph(AgentState)

graph.add_node("supervisor", supervisor_node)
graph.add_node("researcher", researcher_node)
graph.add_node("writer", writer_node)
graph.add_node("editor", editor_node)

# 条件路由：Supervisor 决定下一步
def route_next(state: AgentState):
    return state["next_agent"]

graph.add_conditional_edges("supervisor", route_next, {
    "researcher": "researcher",
    "writer": "writer",
    "editor": "editor",
    "FINISH": END,
})

# Worker 完成后都回到 Supervisor
graph.add_edge("researcher", "supervisor")
graph.add_edge("writer", "supervisor")
graph.add_edge("editor", "supervisor")

graph.set_entry_point("supervisor")
app = graph.compile()
```

### 6.3 Swarm 模式：Agent 间自主切换

```python
# Swarm 模式：Agent 自己决定把任务交给谁（不需要 Supervisor）

def smart_researcher(state: AgentState) -> AgentState:
    result = llm.invoke([
        SystemMessage(content="""你是研究员。完成研究后，决定下一步：
        - 如果信息足够 → 返回 "handoff:writer"
        - 如果需要更多调研 → 返回 "handoff:researcher"
        先给出研究结果，最后一行写 handoff 指令。"""),
        HumanMessage(content=state["task"]),
    ])
    content = result.content
    # 解析 handoff 指令
    if "handoff:writer" in content:
        next_agent = "writer"
    else:
        next_agent = "researcher"
    return {"research": content, "next_agent": next_agent}

# 每个 Agent 自主决定把任务交给谁
# 不需要中心化的 Supervisor
# 更灵活，但也更难控制
```

### 6.4 实操：构建一个研究分析团队

```python
# 完整可运行的 LangGraph 多 Agent 示例

result = app.invoke({
    "task": "分析 2024 年大模型微调技术的发展趋势",
    "research": "",
    "draft": "",
    "review": "",
    "next_agent": "",
    "messages": [],
})

print("=== 最终结果 ===")
print(result["review"])
print(f"\n=== 执行日志 ===")
for msg in result["messages"]:
    print(f"  → {msg}")
```

> 💡 **LangGraph 的优势**：流程控制最精细——可以实现循环、条件分支、并行、子图等复杂逻辑。代价是代码量比 CrewAI 多。

---

## 7. 生产级多 Agent 系统设计

Demo 能跑和生产能用是两回事。这一章讲多 Agent 系统上线前必须解决的四大问题。

### 7.1 错误处理与容错：Agent 失败怎么办

```python
import asyncio
from typing import Callable

class ResilientAgent:
    """带容错能力的 Agent 包装器"""
    
    def __init__(self, agent, name: str, max_retries: int = 3,
                 fallback: Callable = None):
        self.agent = agent
        self.name = name
        self.max_retries = max_retries
        self.fallback = fallback
    
    async def run(self, task: str) -> str:
        for attempt in range(self.max_retries):
            try:
                result = await asyncio.wait_for(
                    self.agent.run(task),
                    timeout=60,  # 60 秒超时
                )
                return result
            except asyncio.TimeoutError:
                print(f"⚠️ {self.name} 第 {attempt+1} 次超时")
            except Exception as e:
                print(f"⚠️ {self.name} 第 {attempt+1} 次失败: {e}")
            
            await asyncio.sleep(2 ** attempt)  # 指数退避
        
        # 所有重试都失败了
        if self.fallback:
            print(f"🔄 {self.name} 降级到 fallback")
            return await self.fallback(task)
        
        raise RuntimeError(f"❌ {self.name} 在 {self.max_retries} 次重试后仍失败")
```

**多 Agent 容错策略汇总：**

| 策略 | 适用场景 | 实现方式 |
|:---|:---|:---|
| **重试** | 偶发性错误（网络抖动） | 指数退避重试 |
| **超时** | Agent 卡死/死循环 | asyncio.wait_for |
| **降级** | 非关键 Agent 失败 | 用简单模型替代 |
| **跳过** | 可选步骤失败 | 捕获异常继续流程 |
| **熔断** | 连续失败 | 暂停该 Agent，报警 |

### 7.2 成本控制：避免 Token 爆炸

```
多 Agent 的成本陷阱：

单 Agent：1 次调用 × 2000 tokens = 2000 tokens
多 Agent（3 个）：3 次调用 × 2000 tokens = 6000 tokens
多 Agent（辩论 3 轮 × 3 人）：9 次调用 × 2000 tokens = 18000 tokens 💸
```

```python
class CostTracker:
    """Token 成本追踪器"""
    
    def __init__(self, budget_limit: int = 100000):
        self.total_tokens = 0
        self.budget_limit = budget_limit
        self.per_agent = {}
    
    def record(self, agent_name: str, input_tokens: int, output_tokens: int):
        total = input_tokens + output_tokens
        self.total_tokens += total
        self.per_agent[agent_name] = self.per_agent.get(agent_name, 0) + total
        
        if self.total_tokens > self.budget_limit:
            raise RuntimeError(
                f"🚨 Token 预算超限！已用 {self.total_tokens}/{self.budget_limit}\n"
                f"各 Agent 用量：{self.per_agent}"
            )
    
    def report(self):
        print(f"总 Token: {self.total_tokens}")
        for agent, tokens in sorted(self.per_agent.items(), key=lambda x: -x[1]):
            print(f"  {agent}: {tokens} ({tokens/self.total_tokens:.0%})")
```

**省 Token 的实用技巧：**

```
1. 精简上下文 → 每个 Agent 只传必要信息（参考 3.4 节）
2. 分级模型   → 简单任务用小模型，关键任务用大模型
3. 限制轮次   → 设置 max_round 避免无限讨论
4. 缓存结果   → 相同输入不重复调用
5. 预算熔断   → 超过预算自动停止
```

### 7.3 人机协作：Human-in-the-Loop

不是所有决策都该让 AI 做。关键节点需要人类确认：

```python
class HumanInTheLoop:
    """在关键节点加入人类审批"""
    
    def __init__(self, auto_approve_threshold: float = 0.9):
        self.threshold = auto_approve_threshold
    
    async def checkpoint(self, agent_name: str, result: str,
                         confidence: float = 0.0) -> str:
        """关键节点：人类审批"""
        if confidence >= self.threshold:
            print(f"✅ {agent_name} 结果自动通过（置信度 {confidence:.0%}）")
            return result
        
        print(f"\n{'='*50}")
        print(f"🔍 {agent_name} 的工作需要人类审批：")
        print(f"{'='*50}")
        print(result[:500])
        print(f"{'='*50}")
        
        action = input("操作 [a]通过 / [r]驳回重做 / [e]手动编辑: ").strip()
        
        if action == "a":
            return result
        elif action == "r":
            feedback = input("请输入改进建议：")
            return f"REDO:{feedback}"
        elif action == "e":
            edited = input("请输入修改后的内容：")
            return edited

# 在流水线中使用
hitl = HumanInTheLoop()
draft = await writer.run(research)
approved_draft = await hitl.checkpoint("writer", draft, confidence=0.75)
```

### 7.4 可观测性：追踪多 Agent 的决策链路

```python
import json
from datetime import datetime

class AgentTracer:
    """多 Agent 执行追踪器"""
    
    def __init__(self):
        self.traces = []
    
    def trace(self, agent: str, action: str, input_summary: str,
              output_summary: str, tokens: int = 0, duration: float = 0):
        self.traces.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "input": input_summary[:200],
            "output": output_summary[:200],
            "tokens": tokens,
            "duration_ms": int(duration * 1000),
        })
    
    def print_timeline(self):
        print("\n🕐 执行时间线：")
        for i, t in enumerate(self.traces):
            print(f"  {i+1}. [{t['agent']}] {t['action']}")
            print(f"     耗时: {t['duration_ms']}ms | Tokens: {t['tokens']}")
            print(f"     输出: {t['output'][:80]}...")
    
    def export(self, path: str = "trace.json"):
        with open(path, "w") as f:
            json.dump(self.traces, f, ensure_ascii=False, indent=2)

# 使用
tracer = AgentTracer()
# 每个 Agent 调用后记录
tracer.trace("researcher", "search", "LangGraph 趋势", "找到 15 篇相关文章...", tokens=1200, duration=3.2)
tracer.trace("writer", "write", "基于 15 篇文章...", "初稿：LangGraph 是...", tokens=2000, duration=5.1)
tracer.print_timeline()
```

> 💡 **生产环境推荐**：用 LangFuse 或 LangSmith 做全链路追踪，它们对多 Agent 有专门的可视化支持。

---

## 8. 框架对比与最佳实践

最后一章汇总三大框架的全面对比，帮你做出选型决策。

### 8.1 三大框架全面对比

| 维度 | CrewAI | AutoGen | LangGraph |
|:---|:---|:---|:---|
| **设计理念** | 像组建团队一样组建 AI | Agent 自主对话 | 用状态图编排流程 |
| **核心抽象** | Agent / Task / Crew | ConversableAgent / GroupChat | Node / Edge / State |
| **流程控制** | ⭐⭐⭐ 中等 | ⭐⭐ 较弱 | ⭐⭐⭐⭐⭐ 最强 |
| **上手难度** | ⭐ 最简单 | ⭐⭐ 简单 | ⭐⭐⭐⭐ 较难 |
| **代码量** | 少（10 行起步） | 中等 | 多（需要定义图） |
| **灵活性** | 中等 | 高（自由对话） | 最高（任意拓扑） |
| **代码执行** | 需额外配置 | ✅ 原生支持 | 需要自己实现 |
| **人机交互** | ✅ 支持 | ✅ 原生支持 | ✅ 支持（interrupt） |
| **生态集成** | LangChain 工具 | 独立生态 | LangChain 深度集成 |
| **适合场景** | 任务明确的团队协作 | 编程/对话类任务 | 需要精细控制的复杂流程 |

### 8.2 选型决策树

```
你的多 Agent 项目该用哪个框架？

你需要 Agent 自动执行代码吗？
├── 是 → AutoGen（原生代码执行 + 自动修复）
└── 否 → 继续 ↓

你的流程是否复杂（有循环、条件分支、并行）？
├── 是 → LangGraph（状态图，控制力最强）
└── 否 → 继续 ↓

你想尽快出 MVP 吗？
├── 是 → CrewAI（最简洁，10 分钟上手）
└── 否 → LangGraph（长期可维护性更好）
```

**按场景推荐：**

| 场景 | 首选 | 原因 |
|:---|:---|:---|
| 内容创作团队 | CrewAI | 流水线任务，CrewAI 最直观 |
| 代码生成+调试 | AutoGen | 原生代码执行和自动修复 |
| 客服路由系统 | LangGraph | 需要条件路由和状态管理 |
| 研究分析 | CrewAI 或 LangGraph | 取决于复杂度 |
| 产品讨论会 | AutoGen | GroupChat 最自然 |
| 复杂工作流 | LangGraph | 唯一支持任意拓扑 |

### 8.3 多 Agent 系统的设计 Checklist

```
✅ 设计阶段
  □ 确认任务确实需要多 Agent（不要过度设计）
  □ 每个 Agent 的角色定义清晰、不重叠
  □ 选择了合适的协作模式（流水线/分治/层级/辩论）
  □ 通信机制已设计（消息格式、上下文管理）

✅ 开发阶段
  □ 每个 Agent 的 prompt 独立测试过
  □ 错误处理：重试、超时、降级、熔断
  □ 成本控制：Token 预算、轮次限制
  □ 关键节点有 Human-in-the-Loop

✅ 测试阶段
  □ 端到端测试覆盖主要场景
  □ 边界情况：Agent 失败、超时、死循环
  □ 成本测试：确认 Token 用量在预算内
  □ 压力测试：并发场景下的表现

✅ 上线阶段
  □ 全链路追踪已接入（LangFuse/LangSmith）
  □ 监控告警已配置（错误率、延迟、成本）
  □ 回滚方案：可以快速切回单 Agent
  □ 日志记录：每次执行可回溯
```

### 8.4 未来趋势：MCP、A2A、Agent 生态

```
多 Agent 生态正在快速演进：

MCP（Model Context Protocol）
  → Anthropic 提出的标准协议
  → 让 Agent 统一接入各种工具和数据源
  → 类比：USB 接口标准化了外设连接

A2A（Agent-to-Agent Protocol）
  → Google 提出的 Agent 间通信协议
  → 让不同框架的 Agent 可以互相协作
  → 类比：HTTP 标准化了服务器间通信

趋势总结：
  1. Agent 工具接入标准化（MCP）
  2. Agent 间通信标准化（A2A）
  3. Agent 可组合性越来越强
  4. 从"手动编排"走向"自主协作"
```

> 💡 **最后的建议**：多 Agent 是一个强大但复杂的模式。**从简单开始**——先用 2 个 Agent 跑通一个流水线，验证效果后再逐步增加复杂度。记住，最好的系统不是最复杂的系统，而是**刚好满足需求的系统**。
