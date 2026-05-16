# Agent 架构设计全解

> 从底层原理到生产实践：掌握 Agent 五层通用架构、四大推理范式（ReAct/CoT/Self-Reflection/Plan-and-Execute）、记忆系统设计、上下文管理与多 Agent 协作编排。

---

## 1. 什么是 AI Agent：从 ChatBot 到自主智能体

### 1.1 ChatBot vs Agent：本质区别

```
ChatBot（对话机器人）：
  用户说一句 → 模型回一句 → 结束
  → 无记忆、无规划、无行动能力
  → 本质是"一问一答的文本生成器"

Agent（智能体）：
  用户提出目标 → Agent 自主规划 → 调用工具 → 观察结果
  → 判断是否完成 → 不满意则自我修正 → 直到任务达成
  → 本质是"能自主思考和行动的决策系统"
```

```
核心区别对比：

  维度          ChatBot              Agent
  ──────────────────────────────────────────────
  交互模式      一问一答              目标驱动、多轮自主
  推理能力      单步生成              多步推理、任务拆解
  行动能力      ❌ 只能说             ✅ 能调用工具、执行代码
  记忆能力      ❌ 无状态             ✅ 短时+长时记忆
  自我修正      ❌ 不会               ✅ 反思→纠错→重试
  典型产品      ChatGPT 基础对话      Cursor/Devin/AutoGPT
```

### 1.2 LLM 为什么让 Agent 成为可能

```
LLM 赋予 Agent 的三大核心能力：

  ① 通用推理能力（大脑）
  → 传统 Agent 需要手写规则，LLM 天然会"思考"
  → 能理解模糊指令、处理开放性任务
  → CoT/ReAct 让推理过程可控

  ② 工具调用能力（双手）
  → Function Calling 让 LLM 能操作外部世界
  → 搜索、数据库查询、代码执行、API 调用
  → 从"只能说"变成"能做事"

  ③ 自然语言接口（沟通）
  → 用户用自然语言下达目标
  → Agent 用自然语言汇报进展
  → 零门槛交互，无需学习命令语法
```

### 1.3 Agent 典型应用场景

```
六大 Agent 应用场景：

  场景 1：AI 编程助手（Cursor / Devin）
  → 理解需求 → 规划实现方案 → 写代码 → 运行测试 → 修 Bug

  场景 2：智能客服 Agent
  → 意图识别 → 查知识库 → 调业务 API → 生成回答 → 转人工

  场景 3：数据分析 Agent
  → 理解分析需求 → 写 SQL → 执行查询 → 生成图表 → 总结洞察

  场景 4：自动化运维 Agent
  → 监控告警 → 诊断问题 → 执行修复命令 → 验证恢复

  场景 5：研究助手 Agent
  → 拆解研究问题 → 搜索文献 → 提取信息 → 综合分析 → 撰写报告

  场景 6：工作流自动化 Agent
  → 解析用户目标 → 编排多步工作流 → 协调多个 API → 输出结果
```

> 💡 **一句话总结**：Agent = LLM（大脑）+ Tools（双手）+ Memory（记忆）+ Planning（规划）。LLM 提供推理能力，工具提供行动能力，记忆提供持续性，规划提供目标导向性。

---

## 2. Agent 五层通用架构（面试核心）

这是面试中被问到最多的架构题——"画一下 Agent 的整体架构"。五层架构是最通用的回答框架：

```
Agent 五层通用架构：

  ┌─────────────────────────────────────────────────────┐
  │                 ⑤ 反思迭代层                         │
  │     结果校验 → 自我纠错 → 多轮反思 → 记忆更新        │
  └────────────────────────┬────────────────────────────┘
                           ↑ 结果不满意则回到规划层
  ┌────────────────────────┴────────────────────────────┐
  │                 ④ 执行层                             │
  │     工具调用 / API 请求 / 代码执行 / RAG 检索        │
  └────────────────────────┬────────────────────────────┘
                           ↑ 决策层告诉执行层"做什么"
  ┌────────────────────────┴────────────────────────────┐
  │                 ③ 决策层                             │
  │     路由选择 / 工具匹配 / 分支判断 / 置信度评估      │
  └────────────────────────┬────────────────────────────┘
                           ↑ 规划层拆解后交给决策层
  ┌────────────────────────┴────────────────────────────┐
  │                 ② 规划层                             │
  │     任务拆解 / CoT 推理 / 目标分解 / 步骤排序        │
  └────────────────────────┬────────────────────────────┘
                           ↑ 感知层的结构化输入
  ┌────────────────────────┴────────────────────────────┐
  │                 ① 感知层                             │
  │     用户输入解析 / 多模态理解 / 上下文记忆加载        │
  └─────────────────────────────────────────────────────┘
```

### 2.1 感知层：理解用户意图与环境

```
感知层的职责：把"原始输入"变成"结构化的任务描述"

  输入源                    处理方式                    输出
  ──────────────────────────────────────────────────────────
  用户文本消息              意图识别 + 实体提取          结构化意图
  上传的图片/文件           多模态模型理解               文本描述
  对话历史                  记忆加载 + 上下文拼装        完整上下文
  系统环境状态              环境变量 / 数据库状态         当前状态
```

```python
# ═══════════════════════════════════════
# 感知层实现示例
# ═══════════════════════════════════════

class PerceptionLayer:
    """感知层：理解用户意图 + 加载上下文"""

    def __init__(self, memory_store, context_builder):
        self.memory = memory_store
        self.context = context_builder

    async def perceive(self, user_input: str, session_id: str) -> dict:
        """将原始输入转化为结构化的任务描述"""

        # 1. 加载对话历史（短时记忆）
        history = self.memory.get_recent(session_id, limit=10)

        # 2. 召回相关长时记忆
        relevant_memories = self.memory.recall(user_input, top_k=3)

        # 3. 构建完整上下文
        context = self.context.build(
            system_prompt="你是一个智能助手...",
            history=history,
            memories=relevant_memories,
            user_input=user_input,
        )

        return {
            "user_input": user_input,
            "context": context,
            "session_id": session_id,
        }
```

### 2.2 规划层：任务拆解与推理

```
规划层的职责：把"用户目标"拆解成"可执行的步骤序列"

  用户说："帮我分析上个月的销售数据并生成报告"

  规划层拆解：
  ├── Step 1: 查询数据库获取上月销售数据
  ├── Step 2: 计算关键指标（总销售额、同比增长、Top 品类）
  ├── Step 3: 生成可视化图表
  └── Step 4: 撰写分析报告并输出
```

```python
# ═══════════════════════════════════════
# 规划层实现示例（LLM 驱动的任务规划）
# ═══════════════════════════════════════

PLANNING_PROMPT = """你是一个任务规划器。
根据用户的目标，将其拆解为具体的执行步骤。

用户目标：{goal}
可用工具：{available_tools}

请输出 JSON 格式的步骤列表：
[
  {"step": 1, "action": "工具名", "input": "输入参数", "reason": "为什么"},
  ...
]
"""

class PlanningLayer:
    """规划层：LLM 驱动的任务拆解"""

    def __init__(self, llm):
        self.llm = llm

    async def plan(self, goal: str, tools: list[dict]) -> list[dict]:
        """将用户目标拆解为步骤序列"""
        prompt = PLANNING_PROMPT.format(
            goal=goal,
            available_tools=json.dumps(tools, ensure_ascii=False),
        )

        response = await self.llm.invoke(prompt)
        steps = json.loads(response.content)

        print(f"📋 规划完成: {len(steps)} 个步骤")
        return steps
```

### 2.3 决策层：路由选择与工具匹配

```python
# ═══════════════════════════════════════
# 决策层：根据当前步骤选择执行方式
# ═══════════════════════════════════════

class DecisionLayer:
    """决策层：路由选择 + 工具匹配"""

    def __init__(self, llm, tool_registry):
        self.llm = llm
        self.tools = tool_registry

    async def decide(self, step: dict, context: str) -> dict:
        """为当前步骤选择最合适的执行方式"""

        # LLM 根据步骤描述匹配工具
        decision = await self.llm.invoke(f"""
        当前步骤：{step}
        可用工具：{self.tools.list_tools()}

        请选择：
        1. 需要调用哪个工具？
        2. 调用参数是什么？
        3. 置信度（0-1）？

        如果不需要工具，直接用 LLM 回答即可。
        """)

        return {
            "tool": decision.tool_name,       # 选中的工具
            "params": decision.params,         # 调用参数
            "confidence": decision.confidence,  # 置信度
            "fallback": "llm_direct",          # 工具失败时的降级策略
        }
```

### 2.4 执行层：工具调用与 API 请求

```python
# ═══════════════════════════════════════
# 执行层：真正"干活"的地方
# ═══════════════════════════════════════

class ExecutionLayer:
    """执行层：工具调用 + 错误处理 + 结果格式化"""

    def __init__(self, tool_registry):
        self.tools = tool_registry

    async def execute(self, decision: dict) -> dict:
        """执行决策层的指令"""
        tool_name = decision["tool"]
        params = decision["params"]

        try:
            # 调用工具
            tool = self.tools.get(tool_name)
            result = await tool.invoke(**params)

            return {
                "status": "success",
                "result": result,
                "tool_used": tool_name,
            }

        except Exception as e:
            # 工具调用失败，尝试降级
            print(f"[WARN] 工具 {tool_name} 调用失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "tool_used": tool_name,
                "need_retry": True,
            }
```

### 2.5 反思迭代层：自我校验与纠错

```python
# ═══════════════════════════════════════
# 反思迭代层：Agent 的"自我审查"能力
# ═══════════════════════════════════════

class ReflectionLayer:
    """反思层：校验结果 → 决定是否重试"""

    def __init__(self, llm, max_retries: int = 3):
        self.llm = llm
        self.max_retries = max_retries

    async def reflect(self, goal: str, result: dict, attempt: int) -> dict:
        """校验执行结果，决定下一步"""

        # 让 LLM 评估结果是否满足目标
        evaluation = await self.llm.invoke(f"""
        用户目标：{goal}
        执行结果：{result}

        请评估：
        1. 结果是否满足用户目标？(yes/no)
        2. 如果不满足，问题出在哪？
        3. 应该如何修正？
        """)

        if evaluation.satisfied or attempt >= self.max_retries:
            return {"action": "finish", "result": result}
        else:
            return {
                "action": "retry",
                "feedback": evaluation.feedback,
                "correction": evaluation.correction,
            }
```

```
五层架构的执行流程（面试回答模板）：

  用户输入 → ① 感知层（理解意图、加载记忆）
           → ② 规划层（拆解任务为步骤序列）
           → ③ 决策层（为每步选择工具）
           → ④ 执行层（调用工具、获取结果）
           → ⑤ 反思层（校验结果是否满足目标）
                ├── 满足 → 返回最终结果
                └── 不满足 → 带着反馈回到 ② 重新规划
```

> 💡 **面试答题技巧**：画五层架构图时重点强调"反思迭代层"——这是 Agent 和普通 ChatBot 的核心区别。Agent 能自我纠错，ChatBot 不能。

---

## 3. 四大推理范式（面试必背）

Agent 的"思维方式"决定了它如何解决问题。四大范式各有特点，面试必问"这四种有什么区别、分别适合什么场景"。

### 3.1 ReAct：推理与行动交替

```
ReAct 执行流程（Thought → Action → Observation 循环）：

  用户问题："北京今天天气怎么样？适合户外活动吗？"

  第 1 轮：
  ├── Thought: 用户想知道天气，我需要查天气 API
  ├── Action:  call weather_api(city="北京")
  └── Observation: 晴，25°C，空气质量良

  第 2 轮：
  ├── Thought: 天气是晴天 25°C，很适合户外活动
  ├── Action:  直接回答（无需再调工具）
  └── Final Answer: "北京今天晴，25°C，非常适合户外活动！"
```

```python
# ═══════════════════════════════════════
# ReAct 循环核心实现
# ═══════════════════════════════════════

async def react_loop(llm, tools, user_input: str, max_steps: int = 5):
    """ReAct: 推理→行动→观察 循环"""
    messages = [{"role": "user", "content": user_input}]

    for step in range(max_steps):
        # Thought + Action: LLM 思考并决定是否调用工具
        response = await llm.invoke(messages, tools=tools)

        if response.tool_calls:
            # 有工具调用 → 执行工具
            for tool_call in response.tool_calls:
                result = await execute_tool(tool_call)
                # Observation: 把工具结果反馈给 LLM
                messages.append({
                    "role": "tool",
                    "content": str(result),
                    "tool_call_id": tool_call.id,
                })
        else:
            # 没有工具调用 → LLM 直接给出最终答案
            return response.content

    return "达到最大步数限制"
# → ReAct 是目前最主流的 Agent 范式
# → OpenAI Function Calling 本质就是 ReAct
```

### 3.2 CoT 思维链：分步推理

```
CoT（Chain of Thought）的核心：让 LLM "一步一步思考"

  没有 CoT：
  → 问："一个商店有 23 个苹果，卖了 15 个，又进了 8 个，还剩多少？"
  → 答："16 个"（直接输出，可能出错）

  有 CoT：
  → 问：同上 + "请一步一步思考"
  → 答：
     Step 1: 初始有 23 个苹果
     Step 2: 卖了 15 个 → 23 - 15 = 8 个
     Step 3: 又进了 8 个 → 8 + 8 = 16 个
     答案：16 个 ✅
```

```python
# ═══════════════════════════════════════
# CoT 的两种使用方式
# ═══════════════════════════════════════

# ① Zero-shot CoT（零样本，加一句话就行）
zero_shot_prompt = """
{question}

请一步一步思考，然后给出答案。
"""

# ② Few-shot CoT（给示例，效果更稳定）
few_shot_prompt = """
示例问题：小明有 5 个苹果，给了小红 2 个，又买了 3 个，现在有几个？
思考过程：
1. 初始：5 个
2. 给了小红 2 个：5 - 2 = 3 个
3. 又买了 3 个：3 + 3 = 6 个
答案：6 个

现在请解答：
{question}
"""

# → CoT 适合推理密集型任务（数学、逻辑、代码分析）
# → 缺点：不能调用工具，只能"想"不能"做"
# → 通常和 ReAct 结合使用
```

### 3.3 Self-Reflection：自省与纠错

```
Self-Reflection 闭环架构：

  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │  生成     │ ──→ │  校验     │ ──→ │  满足？   │
  │  (LLM)   │     │  (评估)   │     │          │
  └──────────┘     └──────────┘     └────┬─────┘
       ↑                                  │
       │              ┌───────────────────┤
       │              ↓ NO                ↓ YES
  ┌──────────┐   ┌──────────┐      ┌──────────┐
  │  修正     │ ← │  分析错误 │      │  输出结果 │
  │  重新生成 │   │  提取反馈 │      │          │
  └──────────┘   └──────────┘      └──────────┘
```

```python
# ═══════════════════════════════════════
# Self-Reflection 实现
# ═══════════════════════════════════════

async def self_reflection_loop(llm, task: str, max_rounds: int = 3):
    """自省循环：生成→校验→纠错→重生成"""

    result = None
    feedback = ""

    for round_num in range(max_rounds):
        # 生成（带上之前的反馈）
        prompt = f"任务: {task}\n"
        if feedback:
            prompt += f"上次的问题: {feedback}\n请修正后重新回答。"

        result = await llm.invoke(prompt)

        # 校验（用 LLM 自己当评审）
        check = await llm.invoke(f"""
        任务: {task}
        回答: {result.content}

        请评估这个回答：
        1. 是否完整回答了问题？
        2. 是否有事实错误？
        3. 评分（1-10）：
        如果评分 >= 8，输出 PASS；否则输出具体问题。
        """)

        if "PASS" in check.content:
            print(f"✅ 第 {round_num + 1} 轮通过")
            return result.content
        else:
            feedback = check.content
            print(f"🔄 第 {round_num + 1} 轮未通过，修正中...")

    return result.content  # 达到最大轮次，返回最后结果

# → 适合：代码生成、写作、数据分析等需要高质量输出的场景
# → 缺点：多轮调用 LLM，成本翻倍
```

### 3.4 Plan-and-Execute：先规划再执行

```
Plan-and-Execute vs ReAct 的区别：

  ReAct（边想边做）：
  → Think → Act → Observe → Think → Act → ...
  → 每步都重新思考，灵活但可能跑偏

  Plan-and-Execute（先想好再做）：
  → Plan: [Step1, Step2, Step3, Step4]
  → Execute: Step1 → Step2 → Step3 → Step4
  → 先全局规划，再逐步执行，目标更明确
```

```python
# ═══════════════════════════════════════
# Plan-and-Execute 实现
# ═══════════════════════════════════════

async def plan_and_execute(planner_llm, executor_llm, tools, goal: str):
    """先规划任务清单，再逐个执行"""

    # Phase 1: 规划（一次性生成所有步骤）
    plan = await planner_llm.invoke(f"""
    目标: {goal}
    可用工具: {[t.name for t in tools]}

    请制定完整的执行计划，输出 JSON 列表。
    """)
    steps = json.loads(plan.content)
    print(f"📋 计划: {len(steps)} 个步骤")

    # Phase 2: 逐步执行
    results = []
    for i, step in enumerate(steps):
        print(f"  ▶ 执行 Step {i+1}: {step['action']}")
        result = await executor_llm.invoke(
            f"执行: {step}\n已完成步骤的结果: {results}",
            tools=tools,
        )
        results.append({"step": i+1, "result": result.content})

    return results

# → 适合：复杂多步任务（研究报告、项目规划、数据管线）
# → 缺点：规划阶段不灵活，如果某步失败需要重新规划
```

### 3.5 四大范式对比与选型

```
四大推理范式对比（面试直接背这个表）：

  范式              核心思想          工具调用   适合场景              代表框架
  ───────────────────────────────────────────────────────────────────────
  ReAct             边想边做          ✅        通用 Agent            LangChain/OpenAI
  CoT               先想后答          ❌        推理/数学/分析        直接 Prompt
  Self-Reflection   做完自检          ✅        高质量输出            Reflexion
  Plan-and-Execute  先规划再执行      ✅        复杂多步任务          LangGraph

  选型建议：
  → 大多数场景 → ReAct（最通用、生态最好）
  → 需要深度推理 → CoT + ReAct 组合
  → 需要高质量输出 → Self-Reflection
  → 复杂多步任务 → Plan-and-Execute
  → 实际生产中常常组合使用，不是非此即彼
```

> 💡 **面试答题技巧**：先说"四大范式分别是什么"，再说"它们的核心区别"，最后说"实际项目中我用的是 ReAct，因为..."。有项目经验加分。

---

## 4. Agent 记忆架构（高频面试题）

记忆是 Agent 保持"连贯性"和"个性化"的关键——没有记忆的 Agent 每次对话都像失忆。

### 4.1 短时记忆：对话上下文管理

```python
# ═══════════════════════════════════════
# 短时记忆：滑动窗口 + 摘要压缩
# ═══════════════════════════════════════

class ShortTermMemory:
    """短时记忆：管理当前对话的上下文"""

    def __init__(self, max_messages: int = 20):
        self.sessions: dict[str, list] = {}
        self.max_messages = max_messages

    def add(self, session_id: str, role: str, content: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({"role": role, "content": content})

        # 滑动窗口：超出限制则裁剪最早的消息
        if len(self.sessions[session_id]) > self.max_messages:
            self.sessions[session_id] = self.sessions[session_id][-self.max_messages:]

    def get_recent(self, session_id: str, limit: int = 10) -> list:
        return self.sessions.get(session_id, [])[-limit:]
```

### 4.2 长时记忆：向量记忆库与用户画像

```python
# ═══════════════════════════════════════
# 长时记忆：向量数据库存储 + 语义召回
# ═══════════════════════════════════════

class LongTermMemory:
    """长时记忆：持久化存储 + 语义检索"""

    def __init__(self, vector_store, embedding_fn):
        self.store = vector_store
        self.embed = embedding_fn

    async def save(self, session_id: str, content: str, importance: float = 0.5):
        """保存重要记忆"""
        embedding = await self.embed(content)
        self.store.upsert({
            "id": f"{session_id}_{hash(content)}",
            "vector": embedding,
            "payload": {
                "content": content,
                "session_id": session_id,
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
            },
        })

    async def recall(self, query: str, top_k: int = 5) -> list[str]:
        """基于语义相似度召回记忆"""
        query_emb = await self.embed(query)
        results = self.store.search(query_emb, top_k=top_k)
        return [r["payload"]["content"] for r in results]
```

### 4.3 记忆召回、压缩与遗忘策略

```
记忆管理三大策略：

  ① 召回策略（怎么找到相关记忆）
  → 语义相似度：Embedding 余弦距离
  → 时间衰减：最近的记忆权重更高
  → 重要性评分：LLM 判断记忆的重要程度
  → 综合得分 = 0.5×相似度 + 0.3×时间新鲜度 + 0.2×重要性

  ② 压缩策略（记忆太多时怎么办）
  → 摘要压缩：把 20 轮对话压缩成 3 句话摘要
  → 关键信息提取：只保留实体/结论/偏好
  → 层级压缩：近期保留原文，远期只保留摘要

  ③ 遗忘策略（什么时候删记忆）
  → TTL 过期：超过 30 天自动清理
  → 重要性阈值：重要性 < 0.3 的记忆定期淘汰
  → 容量淘汰：超过 1000 条时删除最不重要的
```

### 4.4 生产级记忆系统架构设计

```
生产级 Agent 记忆系统架构：

  ┌─────────────────────────────────────────────┐
  │                 Agent 核心                    │
  └────────────────────┬────────────────────────┘
                       │ 读写记忆
  ┌────────────────────┴────────────────────────┐
  │              记忆管理器（Memory Manager）      │
  │   召回排序 / 压缩 / 遗忘 / 重要性评分         │
  └───┬──────────┬──────────┬───────────────────┘
      │          │          │
      ▼          ▼          ▼
  ┌──────┐  ┌──────┐  ┌──────────┐
  │ 短时  │  │ 长时  │  │ 用户画像  │
  │ 记忆  │  │ 记忆  │  │ 记忆      │
  │      │  │      │  │          │
  │ Redis │  │向量库 │  │ 关系库    │
  └──────┘  └──────┘  └──────────┘

  短时记忆 → Redis（对话窗口，session 级别）
  长时记忆 → 向量数据库（语义检索，用户级别）
  用户画像 → PostgreSQL（偏好/标签，结构化存储）
```

> 💡 **面试答题要点**：被问"Agent 的记忆系统怎么设计"时，先说三种记忆（短时/长时/用户画像），再说三大策略（召回/压缩/遗忘），最后画存储架构图。

---

## 5. 上下文工程（Context Engineering）

Andrej Karpathy 说过："Agent 的关键不是 Prompt Engineering，而是 Context Engineering"——给 LLM 组装正确的上下文比写好 Prompt 更重要。

### 5.1 从 Prompt Engineering 到 Context Engineering

```
Prompt Engineering vs Context Engineering：

  Prompt Engineering（写好指令）：
  → 关注：怎么写 System Prompt
  → 范围：单次 LLM 调用的指令优化
  → 举例："请用专业的语气回答以下问题..."

  Context Engineering（组装正确的上下文）：
  → 关注：LLM 看到的完整信息是什么
  → 范围：系统指令 + 对话历史 + 工具结果 + 记忆 + RAG 的拼装
  → 举例：在有限 Token 内放入最有价值的信息

  核心区别：
  → Prompt 是"怎么问"，Context 是"带着什么信息去问"
  → Agent 的成败 80% 取决于上下文质量
```

### 5.2 上下文窗口管理：裁剪、压缩与优先级

```
上下文优先级排序（从高到低）：

  优先级 1: 系统指令（System Prompt）          必须保留
  优先级 2: 当前步骤的工具执行结果              必须保留
  优先级 3: 用户最新输入                        必须保留
  优先级 4: 最近 3-5 轮对话历史                 优先保留
  优先级 5: RAG 检索到的相关文档                按相关度裁剪
  优先级 6: 长时记忆召回                        按重要性裁剪
  优先级 7: 早期对话历史                        压缩为摘要
```

### 5.3 上下文拼装模式与 Token 预算分配

```python
# ═══════════════════════════════════════
# 上下文工程：Token 预算分配器
# ═══════════════════════════════════════

class ContextBuilder:
    """上下文拼装器：在 Token 预算内组装最优上下文"""

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    def build(self, system_prompt: str, history: list,
              tool_results: list, memories: list,
              rag_context: list, user_input: str) -> list[dict]:
        """按优先级拼装上下文"""
        messages = []
        used_tokens = 0

        # 预算分配
        budget = {
            "system":    int(self.max_tokens * 0.15),  # 15%
            "tools":     int(self.max_tokens * 0.20),  # 20%
            "history":   int(self.max_tokens * 0.25),  # 25%
            "rag":       int(self.max_tokens * 0.20),  # 20%
            "memory":    int(self.max_tokens * 0.10),  # 10%
            "user":      int(self.max_tokens * 0.10),  # 10%（预留给输出）
        }

        # 按优先级依次填充
        messages.append({"role": "system", "content": self._truncate(system_prompt, budget["system"])})

        # 工具结果（最新的最重要）
        for result in tool_results[-3:]:
            messages.append({"role": "tool", "content": self._truncate(str(result), budget["tools"] // 3)})

        # 对话历史（最近的优先）
        for msg in history[-5:]:
            messages.append(msg)

        # RAG 上下文
        if rag_context:
            rag_text = "\n".join(rag_context[:3])
            messages.append({"role": "system", "content": f"参考资料:\n{self._truncate(rag_text, budget['rag'])}"})

        # 用户输入
        messages.append({"role": "user", "content": user_input})

        return messages

    def _truncate(self, text: str, max_chars: int) -> str:
        return text[:max_chars] if len(text) > max_chars else text
```

> 💡 **面试答题要点**："上下文工程的核心是在有限 Token 预算内，按优先级放入最有价值的信息。系统指令和工具结果不能丢，早期历史可以压缩成摘要。"

---

## 6. 工具调用架构（Skill/Tool System）

工具是 Agent 的"双手"——没有工具的 Agent 只能说，不能做。

### 6.1 工具系统五层架构

```
工具系统五层架构：

  ┌─────────────────────────────────────────────┐
  │          ⑤ 权限与安全层                      │
  │    工具权限控制 / 调用频率限制 / 沙箱隔离     │
  └──────────────────┬──────────────────────────┘
  ┌──────────────────┴──────────────────────────┐
  │          ④ 结果处理层                        │
  │    返回值解析 / 格式标准化 / 错误映射        │
  └──────────────────┬──────────────────────────┘
  ┌──────────────────┴──────────────────────────┐
  │          ③ 工具调用层                        │
  │    参数校验 / 函数执行 / API 请求 / 超时控制  │
  └──────────────────┬──────────────────────────┘
  ┌──────────────────┴──────────────────────────┐
  │          ② 工具路由层                        │
  │    意图匹配 / 工具选择 / 多工具编排           │
  └──────────────────┬──────────────────────────┘
  ┌──────────────────┴──────────────────────────┐
  │          ① 工具注册层                        │
  │    工具描述 / JSON Schema / 入参出参定义      │
  └─────────────────────────────────────────────┘
```

### 6.2 Function Call 底层执行链路

```
Function Call 完整链路：

  LLM 输出                     应用层处理
  ──────────                   ──────────
  {"tool": "search",     →    ① 解析 JSON
   "params": {           →    ② 参数校验（类型/必填/范围）
     "query": "天气"     →    ③ 调用函数 search(query="天气")
   }}                    →    ④ 获取结果 {"temp": "25°C"}
                         →    ⑤ 格式化结果回传给 LLM
                         →    ⑥ LLM 基于结果生成最终回答
```

```python
# ═══════════════════════════════════════
# 工具注册与执行
# ═══════════════════════════════════════

class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: dict[str, callable] = {}
        self._schemas: dict[str, dict] = {}

    def register(self, name: str, func: callable, schema: dict):
        """注册工具"""
        self._tools[name] = func
        self._schemas[name] = schema

    async def execute(self, name: str, params: dict) -> dict:
        """执行工具（带校验和错误处理）"""
        if name not in self._tools:
            return {"error": f"工具 {name} 不存在"}

        try:
            result = await self._tools[name](**params)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def list_schemas(self) -> list[dict]:
        """返回所有工具的 JSON Schema（给 LLM 看）"""
        return list(self._schemas.values())
```

### 6.3 多工具编排：串行、并行与 DAG

```
三种工具编排模式：

  ① 串行（Sequential）：
  工具A → 工具B → 工具C
  → A 的输出是 B 的输入
  → 适合：有依赖关系的步骤

  ② 并行（Parallel）：
  工具A ─┐
  工具B ─┼→ 合并结果
  工具C ─┘
  → 三个工具同时执行
  → 适合：独立的信息收集

  ③ DAG（有向无环图）：
  工具A ─→ 工具C ─┐
  工具B ──────────┼→ 工具D
  → 混合串并行
  → 适合：复杂工作流
```

> 💡 **面试答题要点**：工具系统的关键是"注册描述要精确"——LLM 通过工具描述来决定调用哪个工具，描述写不好 Agent 就选错工具。

---

## 7. Multi-Agent 多智能体架构

当任务太复杂、单个 Agent 搞不定时，就需要多个 Agent 分工协作。

### 7.1 三大架构模式：主从、联邦、团队协作

```
① 主从架构（Supervisor）：

  ┌──────────────┐
  │  Supervisor  │  ← 管理者：任务分发、结果汇总
  │  (主 Agent)  │
  └──┬───┬───┬──┘
     │   │   │
     ▼   ▼   ▼
  ┌────┐┌────┐┌────┐
  │搜索││分析││写作│  ← 工人：各司其职
  └────┘└────┘└────┘

② 联邦架构（Peer-to-Peer）：

  ┌────┐ ←→ ┌────┐
  │ A  │     │ B  │  ← 平等协作
  └────┘ ←→ └────┘
     ↕         ↕
  ┌────┐ ←→ ┌────┐
  │ C  │     │ D  │
  └────┘     └────┘

③ 团队协作架构（Hierarchical）：

  ┌──────────┐
  │ 总指挥    │
  └──┬───┬──┘
     │   │
  ┌──┴┐ ┌┴──┐
  │组长│ │组长│
  └┬─┬┘ └┬─┬┘
   │ │   │ │
  工人们  工人们
```

### 7.2 Agent 间通信与状态共享

```
Agent 间通信三种模式：

  模式              实现方式              适合场景
  ────────────────────────────────────────────────
  共享状态          共享 State 对象       LangGraph（推荐）
  消息传递          消息队列/事件         分布式 Agent
  黑板模式          共享数据库/缓存       异步协作

  LangGraph 的共享状态模式（最推荐）：
  → 所有 Agent 共享同一个 State 对象
  → 每个 Agent 读取 State、执行任务、写回结果
  → 状态驱动流转，简单直观
```

### 7.3 LangGraph 多 Agent 编排实战

```python
# ═══════════════════════════════════════
# LangGraph 多 Agent 编排（Supervisor 模式）
# ═══════════════════════════════════════
from langgraph.graph import StateGraph, END

# 定义共享状态
class TeamState(TypedDict):
    task: str
    research_result: str
    analysis_result: str
    final_report: str

# 定义各个 Agent 节点
async def researcher(state: TeamState) -> dict:
    """研究 Agent：搜索和收集信息"""
    result = await research_llm.invoke(f"研究: {state['task']}")
    return {"research_result": result.content}

async def analyst(state: TeamState) -> dict:
    """分析 Agent：分析研究结果"""
    result = await analyst_llm.invoke(
        f"分析以下研究结果:\n{state['research_result']}"
    )
    return {"analysis_result": result.content}

async def writer(state: TeamState) -> dict:
    """写作 Agent：撰写最终报告"""
    result = await writer_llm.invoke(
        f"基于分析撰写报告:\n{state['analysis_result']}"
    )
    return {"final_report": result.content}

# 构建工作流
workflow = StateGraph(TeamState)
workflow.add_node("researcher", researcher)
workflow.add_node("analyst", analyst)
workflow.add_node("writer", writer)

workflow.add_edge("researcher", "analyst")  # 研究 → 分析
workflow.add_edge("analyst", "writer")      # 分析 → 写作
workflow.add_edge("writer", END)            # 写作 → 结束

workflow.set_entry_point("researcher")
app = workflow.compile()

# 运行
# result = await app.ainvoke({"task": "分析 2024 年 AI 行业趋势"})
```

> 💡 **面试答题要点**：多 Agent 选型——简单任务用主从（Supervisor），复杂任务用层级（Hierarchical），需要灵活协作用联邦（Peer-to-Peer）。LangGraph 是目前最主流的编排框架。

---

## 8. 生产级 Agent 系统设计

从 Demo 到生产，Agent 需要"看得见、管得住、用得起"。

### 8.1 可观测性：追踪 Agent 的每一步决策

```
Agent 可观测性三要素：

  ① 调用链追踪（Tracing）
  → 记录 Agent 每一步：感知→规划→决策→执行→反思
  → 每步的输入/输出/耗时/Token 消耗
  → 工具：Langfuse / LangSmith / Phoenix

  ② 决策日志（Decision Log）
  → 为什么选了这个工具？置信度多少？
  → 反思层为什么判定需要重试？
  → 用于事后分析和优化

  ③ 指标监控（Metrics）
  → 任务完成率、平均步骤数、工具调用成功率
  → P95 延迟、Token 成本/任务
  → 异常率、重试率
```

### 8.2 安全、评测与成本控制

```
Agent 安全三道防线：

  防线 1: 输入防护
  → Prompt 注入检测（检查用户输入是否尝试劫持指令）
  → 输入长度限制、特殊字符过滤

  防线 2: 工具权限控制
  → 工具白名单（Agent 只能调用预注册的工具）
  → 参数范围校验（防止 SQL 注入、路径遍历）
  → 沙箱执行（代码执行类工具在隔离环境运行）

  防线 3: 输出过滤
  → 敏感信息检测（防止泄露内部数据）
  → 内容安全审核（防止生成有害内容）
```

```
成本控制策略：

  策略              实现方式              节省效果
  ────────────────────────────────────────────────
  模型降级          简单任务用小模型       60-80%
  结果缓存          相似问题复用答案       30-50%
  步骤限制          max_steps = 5          防止死循环
  Token 预算        每次请求设上限         可控成本
  批量处理          合并多个工具调用       减少 LLM 调用次数
```

### 8.3 Agent 架构面试高频题汇总

```
面试高频题 TOP 10：

  ❓ Q1: 画一下 Agent 的整体架构
  → 五层架构图（感知→规划→决策→执行→反思），重点讲反思层

  ❓ Q2: ReAct 和 CoT 有什么区别？
  → ReAct 能调用工具（边想边做），CoT 只能推理（先想后答）

  ❓ Q3: Agent 的记忆系统怎么设计？
  → 短时（Redis 滑动窗口）+ 长时（向量库语义召回）+ 用户画像

  ❓ Q4: 如何防止 Agent 陷入死循环？
  → max_steps 限制 + 重复检测 + Token 预算 + 反思层强制退出

  ❓ Q5: Multi-Agent 和 Single Agent 怎么选？
  → 简单任务 Single Agent + ReAct 够用
  → 复杂任务（多步骤、多角色）才上 Multi-Agent

  ❓ Q6: Agent 的上下文窗口满了怎么办？
  → 对话历史摘要压缩 + 按优先级裁剪 + Token 预算分配

  ❓ Q7: Function Calling 的完整链路是什么？
  → LLM 输出 JSON → 解析 → 参数校验 → 函数执行 → 结果回传 LLM

  ❓ Q8: 怎么评估 Agent 的效果？
  → 任务完成率 + 平均步骤数 + 工具调用准确率 + 用户满意度

  ❓ Q9: Agent 的安全问题有哪些？
  → Prompt 注入 + 工具越权 + 数据泄露 + 死循环消耗

  ❓ Q10: Agentic RAG 和普通 RAG 的区别？
  → 普通 RAG 是固定流程（检索→生成）
  → Agentic RAG 是 Agent 自主决定是否检索、检索什么、要不要改写查询
```

> 🎉 **全文完成**。Agent 架构设计的核心知识体系：**五层架构 → 四大范式 → 记忆系统 → 上下文工程 → 工具系统 → 多 Agent → 生产化**。面试时按这个顺序讲，清晰完整。

---
