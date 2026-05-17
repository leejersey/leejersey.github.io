# Agentic RAG：从检索到自主推理

> 超越传统 RAG 的被动检索模式——让 AI Agent 自主决策"要不要搜"、"搜什么"、"搜几次"，实现多步推理、查询改写、工具增强的智能检索系统。

---

## 1. 从传统 RAG 到 Agentic RAG：为什么需要进化

### 1.1 传统 RAG 的局限：检索一次就生成

```
传统 RAG 的工作模式：

  用户提问 → 向量检索（1 次）→ 拼接 Context → LLM 生成
  
  局限性：
  ❌ 只检索一次，可能检索到错误内容
  ❌ 无法判断"需不需要检索"
  ❌ 复杂问题需要多步检索，但只做了一步
  ❌ 不会改写查询，用户问得模糊就搜得差
  ❌ 不会用其他工具（数据库、API、计算器）
```

### 1.2 Agentic RAG：让 Agent 自主决策检索

```
Agentic RAG 的工作模式：

  用户提问
    │
    ├─→ Agent 思考：需要检索吗？
    │     │
    │     ├─→ 不需要 → 直接用已有知识回答
    │     │
    │     └─→ 需要 → 用什么工具检索？
    │           │
    │           ├─→ 改写查询 → 向量检索 → 结果够吗？
    │           │     │
    │           │     ├─→ 够了 → 生成答案
    │           │     └─→ 不够 → 换个角度再搜
    │           │
    │           ├─→ SQL 查询（结构化数据）
    │           └─→ API 调用（实时数据）
```

### 1.3 核心区别：被动 vs 自主

| 维度 | 传统 RAG | Agentic RAG |
|:---|:---|:---|
| 检索决策 | 每次都检索 | Agent 决定要不要检索 |
| 检索次数 | 固定 1 次 | 动态 1~N 次 |
| 查询 | 原始问题 | Agent 改写优化 |
| 数据源 | 仅向量库 | 向量库 + SQL + API + 搜索 |
| 推理 | 单步 | 多步推理、反思 |

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **传统 RAG** | 被动检索一次就生成，无法应对复杂问题 |
| **Agentic RAG** | Agent 自主决策检索策略，支持多步推理 |
| **核心进化** | 从"固定流水线"到"智能决策" |

---

## 2. 检索决策：Agent 决定要不要搜

### 2.1 路由 Agent：分类问题类型

```python
from openai import AsyncOpenAI

client = AsyncOpenAI()

ROUTER_PROMPT = """分析用户问题，决定如何处理。

分类规则：
- "direct": 通用知识或闲聊，直接回答即可
- "retrieve": 需要查询知识库（公司文档、产品信息等）
- "sql": 需要查询数据库（数字、统计、报表）
- "web_search": 需要搜索互联网（实时信息、新闻）

输出 JSON：{"action": "direct|retrieve|sql|web_search", "reason": "一句话理由"}"""

async def route_question(question: str) -> dict:
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": ROUTER_PROMPT},
            {"role": "user", "content": question},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

# 示例
# "你好" → {"action": "direct", "reason": "闲聊"}
# "我们公司退货政策是什么" → {"action": "retrieve", "reason": "需要查知识库"}
# "上个月销售额多少" → {"action": "sql", "reason": "需要查数据库"}
# "今天比特币价格" → {"action": "web_search", "reason": "需要实时信息"}
```

### 2.2 置信度评估：检索结果够不够好

::: v-pre
```python
async def evaluate_retrieval(question: str, documents: list[str]) -> dict:
    """评估检索结果是否足够回答问题"""
    prompt = f"""评估以下检索结果能否回答用户问题。

用户问题：{question}

检索到的文档：
{chr(10).join(f'[{i+1}] {doc[:200]}' for i, doc in enumerate(documents))}

输出 JSON：
&#123;&#123;"sufficient": true/false, "confidence": 0.0~1.0, "missing": "缺少什么信息"&#125;&#125;"""
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
```
:::

### 2.3 自适应检索：动态决定检索策略

```python
async def adaptive_retrieve(question: str, knowledge_base) -> list[str]:
    """自适应检索：根据结果质量决定是否继续"""
    all_documents = []
    queries_tried = [question]
    max_attempts = 3
    
    for attempt in range(max_attempts):
        # 检索
        query = queries_tried[-1]
        docs = await knowledge_base.search(query, top_k=5)
        all_documents.extend(docs)
        
        # 评估
        eval_result = await evaluate_retrieval(question, all_documents)
        
        if eval_result["sufficient"] or eval_result["confidence"] > 0.8:
            break
        
        # 不够好 → 改写查询重新搜
        new_query = await rewrite_query(question, eval_result["missing"])
        queries_tried.append(new_query)
    
    return all_documents
```

> 💡 **"检索决策"是 Agentic RAG 最关键的一步**——不该检索的时候检索（浪费成本），该检索的时候不检索（回答错误），都是问题。用小模型（GPT-4o-mini）做路由，成本极低。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **路由 Agent** | 分类问题→direct/retrieve/sql/search |
| **置信度评估** | 检索后判断结果够不够好 |
| **自适应检索** | 不够好就改写查询、多搜几次 |

---

## 3. 查询改写：让检索更精准

### 3.1 查询分解：复杂问题拆成子问题

::: v-pre
```python
async def decompose_query(question: str) -> list[str]:
    """将复杂问题拆解为多个子查询"""
    prompt = f"""将以下复杂问题拆解为 2-4 个独立的子查询，每个子查询可以独立检索。

问题：{question}

输出 JSON：&#123;&#123;"sub_queries": ["子查询1", "子查询2", ...]&#125;&#125;"""
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    return result["sub_queries"]

# 示例
# "比较 React 和 Vue 在大型项目中的性能和学习曲线"
# → ["React 大型项目性能表现", "Vue 大型项目性能表现", 
#    "React 学习曲线", "Vue 学习曲线"]
```
:::

### 3.2 HyDE：假设性文档嵌入

```python
async def hyde_retrieval(question: str, knowledge_base) -> list[str]:
    """HyDE: 先让 LLM 生成假设答案，再用假设答案去检索"""
    
    # 1. 生成假设性文档
    prompt = f"请直接回答以下问题（即使你不确定）：\n{question}"
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    hypothetical_doc = response.choices[0].message.content
    
    # 2. 用假设文档作为查询去检索（语义更接近真实文档）
    docs = await knowledge_base.search(hypothetical_doc, top_k=5)
    return docs
```

### 3.3 Step-back Prompting：退一步思考

```python
async def stepback_query(question: str) -> str:
    """生成一个更抽象/更高层次的查询"""
    prompt = f"""将以下具体问题转化为一个更通用的查询，帮助检索到更全面的背景信息。

具体问题：{question}
通用查询："""
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
    )
    return response.choices[0].message.content.strip()

# "FastAPI 中如何处理 WebSocket 连接超时" 
# → "FastAPI WebSocket 连接管理和生命周期"
```

### 3.4 多路查询：同一问题的多种表述

```python
async def multi_query_retrieve(question: str, knowledge_base) -> list[str]:
    """生成多个变体查询，合并检索结果"""
    
    # 生成变体
    prompt = f"为以下问题生成 3 个不同的查询表述：\n{question}"
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    queries = response.choices[0].message.content.strip().split("\n")
    queries = [question] + [q.strip().lstrip("0123456789.-) ") for q in queries]
    
    # 并行检索所有查询
    import asyncio
    tasks = [knowledge_base.search(q, top_k=3) for q in queries]
    results = await asyncio.gather(*tasks)
    
    # 去重合并
    all_docs = []
    seen = set()
    for docs in results:
        for doc in docs:
            doc_hash = hash(doc[:100])
            if doc_hash not in seen:
                seen.add(doc_hash)
                all_docs.append(doc)
    
    return all_docs
```

> 💡 **HyDE 是最反直觉但最有效的检索增强技术**——先让 LLM"瞎编"一个答案，用这个答案去搜。因为假设答案和真实文档的语义更接近，检索效果比用原始问题好得多。

**第 3 章核心知识回顾：**

| 技术 | 核心思路 |
|:---|:---|
| **查询分解** | 复杂问题 → 2-4 个子查询，分别检索 |
| **HyDE** | 先生成假设答案，用答案去检索 |
| **Step-back** | 具体问题 → 更抽象的查询，获取背景 |
| **多路查询** | 同一问题多种表述，合并结果 |

---

## 4. 多步推理：检索-思考-再检索

### 4.1 ReAct 模式：推理 + 行动交替

```python
REACT_PROMPT = """你是一个研究助手，可以使用以下工具：

1. search(query) - 搜索知识库
2. sql_query(sql) - 查询数据库  
3. calculate(expr) - 数学计算

按以下格式思考和行动：
Thought: 我需要...
Action: search("查询内容")
Observation: [工具返回结果]
Thought: 根据结果，我还需要...
Action: ...
...
Thought: 我现在有足够信息了
Answer: 最终答案"""

async def react_agent(question: str, tools: dict, max_steps: int = 5) -> str:
    messages = [
        {"role": "system", "content": REACT_PROMPT},
        {"role": "user", "content": question},
    ]
    
    for step in range(max_steps):
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stop=["Observation:"],  # 在 Action 后停下来
        )
        content = response.choices[0].message.content
        messages.append({"role": "assistant", "content": content})
        
        # 解析 Action
        if "Answer:" in content:
            return content.split("Answer:")[-1].strip()
        
        if "Action:" in content:
            action = parse_action(content)
            result = await execute_tool(action, tools)
            messages.append({"role": "user", "content": f"Observation: {result}"})
    
    return "超过最大推理步数"
```

### 4.2 自我反思：检查答案质量并修正

::: v-pre
```python
async def self_reflect(question: str, answer: str, sources: list[str]) -> dict:
    """反思答案质量：是否有依据、是否完整、是否准确"""
    prompt = f"""评估以下答案的质量：

问题：{question}
答案：{answer}
参考来源：{chr(10).join(sources[:3])}

检查项：
1. 答案是否有来源支撑（不是编造的）？
2. 答案是否完整回答了问题？
3. 答案是否有明显错误？

输出 JSON：&#123;&#123;"quality": "good|needs_improvement|poor", "issues": ["问题1", ...], "suggestion": "改进建议"&#125;&#125;"""
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
```
:::

### 4.3 CRAG：纠正性检索增强生成

```python
async def corrective_rag(question: str, knowledge_base) -> str:
    """CRAG：检索后评估，不靠谱就换数据源"""
    
    # Step 1: 初始检索
    docs = await knowledge_base.search(question, top_k=5)
    
    # Step 2: 评估检索质量
    eval_result = await evaluate_retrieval(question, docs)
    
    if eval_result["confidence"] > 0.8:
        # 高置信度：直接用
        return await generate_answer(question, docs)
    
    elif eval_result["confidence"] > 0.4:
        # 中等置信度：知识库结果 + 网络搜索补充
        web_docs = await web_search(question)
        all_docs = docs + web_docs
        return await generate_answer(question, all_docs)
    
    else:
        # 低置信度：完全依赖网络搜索
        web_docs = await web_search(question)
        return await generate_answer(question, web_docs)
```

### 4.4 多跳推理：链式检索回答复杂问题

::: v-pre
```python
async def multi_hop_reasoning(question: str, knowledge_base) -> str:
    """多跳推理：需要多次检索才能回答的问题"""
    
    context = []
    current_question = question
    
    for hop in range(3):  # 最多 3 跳
        # 检索
        docs = await knowledge_base.search(current_question, top_k=3)
        context.extend(docs)
        
        # 判断是否需要继续
        eval_prompt = f"""基于已有信息，判断是否能回答原始问题。

原始问题：{question}
已有信息：{chr(10).join(context)}

如果能回答，输出 &#123;&#123;"can_answer": true&#125;&#125;
如果还需要更多信息，输出 &#123;&#123;"can_answer": false, "next_query": "下一步应该查什么"&#125;&#125;"""
        
        result = await llm_json(eval_prompt)
        
        if result["can_answer"]:
            break
        current_question = result["next_query"]
    
    return await generate_answer(question, context)
```
:::

> 💡 **CRAG 的核心洞察：不是所有检索结果都值得信任**——低质量的检索结果喂给 LLM，不如不检索。CRAG 加了一层"纠正"——结果不好就换数据源（网络搜索），而不是硬用差结果。

**第 4 章核心知识回顾：**

| 模式 | 核心思路 |
|:---|:---|
| **ReAct** | Thought→Action→Observation 循环 |
| **自我反思** | 生成答案后检查质量，不行就重来 |
| **CRAG** | 检索质量差→切换到网络搜索 |
| **多跳推理** | 逐步检索，前一步的结果指导下一步 |

---

## 5. 工具增强检索：超越向量搜索

### 5.1 多数据源 Agent：向量库 + SQL + API

```python
# 定义 Agent 可用的工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "vector_search",
            "description": "搜索知识库文档（产品文档、FAQ、技术手册）",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"&#125;&#125;,
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sql_query",
            "description": "查询业务数据库（订单、用户、销售数据）",
            "parameters": {
                "type": "object",
                "properties": {"sql": {"type": "string", "description": "SQL 查询语句"&#125;&#125;,
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索互联网（实时信息、最新新闻）",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"&#125;&#125;,
                "required": ["query"],
            },
        },
    },
]
```

### 5.2 Text-to-SQL：自然语言查数据库

```python
async def text_to_sql(question: str, schema: str) -> str:
    """将自然语言转为 SQL"""
    prompt = f"""根据数据库结构，将用户问题转为 SQL 查询。

数据库结构：
{schema}

规则：只用 SELECT，禁止 DELETE/UPDATE/DROP

用户问题：{question}
SQL："""
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    sql = response.choices[0].message.content.strip().strip("```sql").strip("```")
    return sql
```

### 5.3 混合检索编排

```python
async def hybrid_agent_search(question: str) -> str:
    """Agent 自主选择数据源进行混合检索"""
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是一个研究助手，根据问题类型选择合适的工具检索信息。"},
            {"role": "user", "content": question},
        ],
        tools=tools,
    )
    
    # 执行 Agent 选择的工具
    all_results = []
    for tool_call in response.choices[0].message.tool_calls or []:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        if name == "vector_search":
            result = await knowledge_base.search(args["query"])
        elif name == "sql_query":
            result = await db.execute(args["sql"])
        elif name == "web_search":
            result = await tavily_search(args["query"])
        
        all_results.append({"tool": name, "result": result})
    
    # 基于所有结果生成最终答案
    return await generate_final_answer(question, all_results)
```

> 💡 **Agentic RAG 的真正力量在于"多工具编排"**——向量搜索擅长语义匹配，SQL 擅长精确数据查询，网络搜索擅长实时信息。Agent 根据问题类型自动选择最合适的工具组合。

**第 5 章核心知识回顾：**

| 工具 | 擅长场景 |
|:---|:---|
| **向量搜索** | 文档语义匹配（FAQ、技术手册） |
| **SQL 查询** | 精确数据（销售额、用户数） |
| **网络搜索** | 实时信息（新闻、价格） |
| **Agent** | 自动选择最合适的工具 |

---

## 6. 完整实现：构建 Agentic RAG 系统

### 6.1 系统架构

```
Agentic RAG 完整架构：

  用户提问
    │
    ├─→ [路由 Agent] 分类问题类型
    │     │
    │     ├─→ direct → LLM 直接回答
    │     │
    │     ├─→ retrieve → [检索 Agent]
    │     │     │
    │     │     ├─→ 查询改写（HyDE/分解/多路）
    │     │     ├─→ 向量检索
    │     │     ├─→ 评估结果置信度
    │     │     ├─→ 不够？→ 改写重搜 / 网络搜索
    │     │     └─→ 生成答案 + 反思
    │     │
    │     ├─→ sql → Text-to-SQL → 执行 → 解释结果
    │     │
    │     └─→ web → 网络搜索 → 提取 → 生成
    │
    └─→ 返回答案 + 引用来源
```

### 6.2 完整代码实现

```python
class AgenticRAG:
    """Agentic RAG 系统"""
    
    def __init__(self, knowledge_base, db=None):
        self.kb = knowledge_base
        self.db = db
        self.client = AsyncOpenAI()
    
    async def answer(self, question: str) -> dict:
        # Step 1: 路由
        route = await route_question(question)
        
        if route["action"] == "direct":
            return await self._direct_answer(question)
        elif route["action"] == "retrieve":
            return await self._agentic_retrieve(question)
        elif route["action"] == "sql":
            return await self._sql_answer(question)
        elif route["action"] == "web_search":
            return await self._web_answer(question)
    
    async def _agentic_retrieve(self, question: str) -> dict:
        # Step 2: 查询改写 + 多路检索
        docs = await multi_query_retrieve(question, self.kb)
        
        # Step 3: 评估质量
        eval_result = await evaluate_retrieval(question, docs)
        
        # Step 4: 不够好就补充
        if eval_result["confidence"] < 0.6:
            hyde_docs = await hyde_retrieval(question, self.kb)
            docs.extend(hyde_docs)
        
        # Step 5: 生成答案
        answer = await generate_answer(question, docs)
        
        # Step 6: 自我反思
        reflection = await self_reflect(question, answer, docs)
        if reflection["quality"] == "poor":
            # 重新检索 + 生成
            docs = await adaptive_retrieve(question, self.kb)
            answer = await generate_answer(question, docs)
        
        return {"answer": answer, "sources": docs, "confidence": eval_result["confidence"]}
```

### 6.3 评测：传统 RAG vs Agentic RAG

| 指标 | 传统 RAG | Agentic RAG |
|:---|:---|:---|
| 简单问题准确率 | 85% | 88% |
| 复杂问题准确率 | 45% | 78% |
| 多跳推理准确率 | 20% | 65% |
| 平均检索次数 | 1 次 | 1.8 次 |
| 平均延迟 | 2s | 5s |
| Token 成本 | 1x | 3x |

> 💡 **Agentic RAG 用成本换质量**——简单问题差距不大，但复杂问题和多跳推理的提升巨大。建议用路由 Agent 分流：简单问题走传统 RAG（省钱），复杂问题走 Agentic RAG（质量）。

---

## 7. 进阶模式与优化

### 7.1 Graph RAG：知识图谱增强

```python
async def graph_rag(question: str, graph_db, vector_db) -> str:
    """Graph RAG：知识图谱 + 向量检索"""
    
    # 1. 提取实体
    entities = await extract_entities(question)
    
    # 2. 图谱检索（实体关系）
    graph_context = await graph_db.query(
        f"MATCH (n)-[r]-(m) WHERE n.name IN {entities} RETURN n, r, m LIMIT 20"
    )
    
    # 3. 向量检索（语义相关文档）
    vector_docs = await vector_db.search(question, top_k=5)
    
    # 4. 合并上下文生成答案
    return await generate_answer(question, graph_context + vector_docs)
```

### 7.2 缓存与成本优化

```python
import hashlib

class RAGCache:
    """语义缓存：相似问题复用答案"""
    
    def __init__(self, vector_db):
        self.cache_db = vector_db
    
    async def get(self, question: str, threshold: float = 0.95) -> str | None:
        results = await self.cache_db.search(question, top_k=1)
        if results and results[0]["score"] > threshold:
            return results[0]["answer"]
        return None
    
    async def set(self, question: str, answer: str):
        await self.cache_db.insert({"question": question, "answer": answer})
```

### 7.3 流式 Agentic RAG

```python
async def stream_agentic_rag(question: str):
    """流式输出：让用户看到思考过程"""
    
    yield {"type": "thinking", "content": "正在分析问题类型..."}
    route = await route_question(question)
    yield {"type": "route", "content": f"问题类型: {route['action']}"}
    
    yield {"type": "thinking", "content": "正在检索知识库..."}
    docs = await multi_query_retrieve(question, kb)
    yield {"type": "sources", "content": docs}
    
    yield {"type": "thinking", "content": "正在生成答案..."}
    async for chunk in generate_answer_stream(question, docs):
        yield {"type": "answer", "content": chunk}
```

---

## 附录：Agentic RAG 速查手册

### A.1 查询改写技术对比

| 技术 | 原理 | 适用场景 |
|:---|:---|:---|
| 查询分解 | 复杂问题→子问题 | 多方面比较类问题 |
| HyDE | 假设答案→检索 | 专业术语不匹配时 |
| Step-back | 具体→抽象 | 需要背景知识时 |
| 多路查询 | 同义改写→合并 | 提高召回率 |

### A.2 Agentic RAG vs 传统 RAG 决策表

| 场景 | 推荐方案 | 理由 |
|:---|:---|:---|
| 简单 FAQ | 传统 RAG | 成本低、速度快 |
| 复杂分析 | Agentic RAG | 需要多步推理 |
| 数据查询 | Text-to-SQL | 结构化数据 |
| 实时信息 | Web Search | 知识库没有 |
| 混合问题 | 完整 Agentic RAG | 自动路由 |

### A.3 核心 Prompt 模板

```python
# 路由分类
ROUTER = "分析问题类型: direct/retrieve/sql/web_search"

# 检索评估
EVALUATOR = "评估检索结果是否足够回答问题"

# 自我反思
REFLECTOR = "评估答案质量: good/needs_improvement/poor"

# 查询分解
DECOMPOSER = "将复杂问题拆为 2-4 个子查询"
```
