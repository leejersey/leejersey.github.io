# 第十章 实战项目：自纠错 RAG Agent

---

## 10.1 项目设计：自纠错 RAG 的完整架构

这一章我们把前面学的所有知识综合起来，构建一个**生产级**的项目——自纠错 RAG Agent。它能检索文档、生成回答、**自动评估质量**，不满意就重新检索。

### 什么是 RAG

RAG = **R**etrieval **A**ugmented **G**eneration（检索增强生成）。简单说就是：先搜索相关文档，再基于文档内容让 LLM 回答问题。

```
普通 LLM：
  用户提问 → LLM 回答（可能编造事实）

RAG：
  用户提问 → 搜索文档 → 把相关文档塞给 LLM → LLM 基于事实回答
```

### 为什么需要"自纠错"

基础 RAG 有一个问题：检索到的文档**不一定相关**，LLM 基于不相关的文档回答，结果可能比瞎编还离谱。

```
基础 RAG 的问题：

  用户: "LangGraph 怎么做持久化？"
  检索: 找到了 LangChain 的文档（不完全相关）
  LLM:  "用 LangChain 的 Memory 组件..."（错误！）
  → 检索不精准 → 回答不准确 → 用户不满意

自纠错 RAG 的方案：

  用户: "LangGraph 怎么做持久化？"
  检索: 找到了 LangChain 的文档
  评估: "这些文档不够相关，重新搜索！"
  重新检索: 换个关键词搜 → 找到 LangGraph Checkpointer 文档
  LLM:  "用 Checkpointer，支持 MemorySaver 和 SqliteSaver..."（正确！）
```

### 完整架构

```
自纠错 RAG Agent 的图结构：

  START
    │
    ↓
  [rewrite_query]    ← 优化搜索关键词
    │
    ↓
  [retrieve]          ← 检索文档
    │
    ↓
  [grade_documents]   ← 评估文档相关性
    │
    ├── 文档不相关 → [rewrite_query]（重写查询，循环！）
    │
    └── 文档相关 → [generate]    ← 基于文档生成回答
                      │
                      ↓
                  [grade_answer]  ← 评估回答质量
                      │
                      ├── 回答不好 → [generate]（重新生成）
                      │
                      └── 回答合格 → END
```

### 涉及的 LangGraph 知识点

| 知识点 | 在本项目中的应用 |
|--------|----------------|
| State | 存储 question、documents、answer、retry_count |
| Node | 5 个节点函数（rewrite、retrieve、grade_docs、generate、grade_answer） |
| 条件边 | 文档评估和回答评估的条件路由 |
| 循环 | 不满意 → 重新检索/重新生成 |
| Checkpointer | 多轮对话支持 |

> **学习目标**：通过这个项目，你将理解如何用 LangGraph 的条件边和循环构建一个**会自我修正的**智能系统——这正是图结构区别于线性 Chain 的核心价值。

---

## 10.2 构建检索模块（文档加载 + 向量搜索）

### Step 1：定义 State

```python
from typing import TypedDict, Annotated, List
import operator

class RAGState(TypedDict):
    question: str                            # 用户的原始问题
    rewritten_query: str                     # 优化后的搜索查询
    documents: List[str]                     # 检索到的文档
    answer: str                              # 生成的回答
    doc_grade: str                           # 文档相关性评分：relevant / not_relevant
    answer_grade: str                        # 回答质量评分：good / bad
    retry_count: int                         # 重试次数（防无限循环）
    messages: Annotated[list, operator.add]  # 对话历史
```

### Step 2：构建简易文档库

为了让教程可以直接运行，我们用一个简单的内存文档库代替真实的向量数据库：

```python
# 模拟文档库（实际项目中替换为 FAISS / Chroma / Pinecone）
KNOWLEDGE_BASE = [
    {
        "title": "LangGraph 持久化",
        "content": "LangGraph 使用 Checkpointer 实现持久化。支持 MemorySaver（内存）、SqliteSaver（SQLite）和 PostgresSaver（PostgreSQL）。通过在 compile() 时传入 checkpointer 参数启用。"
    },
    {
        "title": "LangGraph State 定义",
        "content": "LangGraph 的 State 可以用 TypedDict 或 Pydantic BaseModel 定义。推荐使用 Annotated 配合 Reducer（如 operator.add）来控制字段的更新方式。"
    },
    {
        "title": "LangGraph 条件边",
        "content": "条件边用 add_conditional_edges 创建，需要一个路由函数。路由函数接收 state，返回目标节点名。这是实现 Agent 决策和循环的核心机制。"
    },
    {
        "title": "Python GIL",
        "content": "Python 的 GIL（全局解释器锁）确保同一时刻只有一个线程执行 Python 字节码。这限制了多线程的并行性能，但不影响 I/O 密集型任务。"
    },
    {
        "title": "LangGraph Tool Calling",
        "content": "LangGraph 使用 @tool 装饰器定义工具，通过 bind_tools 绑定到 LLM。ToolNode 自动执行工具调用，返回 ToolMessage。ReAct 模式通过条件边实现思考-行动循环。"
    },
]

def simple_search(query: str, top_k: int = 2) -> List[str]:
    """简易搜索：基于关键词匹配"""
    scored = []
    query_lower = query.lower()
    for doc in KNOWLEDGE_BASE:
        score = sum(1 for word in query_lower.split() if word in doc["content"].lower())
        scored.append((score, doc["content"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [content for _, content in scored[:top_k]]
```

### Step 3：定义检索和查询重写节点

```python
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatDeepSeek(model="deepseek-chat", temperature=0)

def rewrite_query(state: RAGState) -> dict:
    """查询重写节点：优化搜索关键词"""
    if state["retry_count"] == 0:
        # 第一次：直接用原始问题
        return {"rewritten_query": state["question"]}
    else:
        # 重试：让 LLM 重写查询
        response = llm.invoke([
            SystemMessage(content="你是一个搜索优化专家。请重写用户的查询，使其更适合文档检索。只返回优化后的查询，不要解释。"),
            HumanMessage(content=f"原始问题：{state['question']}\n之前的查询 '{state['rewritten_query']}' 没有找到相关文档，请换一种方式表达。")
        ])
        return {"rewritten_query": response.content.strip()}

def retrieve(state: RAGState) -> dict:
    """检索节点：从文档库搜索"""
    query = state["rewritten_query"]
    documents = simple_search(query, top_k=2)
    return {"documents": documents}
```

> **生产提示**：实际项目中，`simple_search` 应替换为向量数据库（如 Chroma、FAISS、Pinecone）的语义搜索。LangChain 提供了丰富的 VectorStore 接入方案。

---

## 10.3 构建生成与评估模块

### Step 4：文档相关性评估节点

```python
def grade_documents(state: RAGState) -> dict:
    """评估检索到的文档是否与问题相关"""
    question = state["question"]
    docs = state["documents"]
    docs_text = "\n---\n".join(docs)

    response = llm.invoke([
        SystemMessage(content="""你是一个文档相关性评估专家。
判断给定的文档是否包含与用户问题相关的信息。
只返回 "relevant" 或 "not_relevant"，不要解释。"""),
        HumanMessage(content=f"问题：{question}\n\n文档内容：\n{docs_text}")
    ])
    grade = response.content.strip().lower()
    return {"doc_grade": grade}
```

### Step 5：基于文档生成回答节点

```python
def generate(state: RAGState) -> dict:
    """基于检索到的文档生成回答"""
    question = state["question"]
    docs = state["documents"]
    docs_text = "\n---\n".join(docs)

    response = llm.invoke([
        SystemMessage(content="""你是一个知识助手。请严格基于以下参考文档回答用户问题。
如果文档中没有足够信息，请如实说明。不要编造事实。"""),
        HumanMessage(content=f"参考文档：\n{docs_text}\n\n用户问题：{question}")
    ])
    return {"answer": response.content}
```

### Step 6：回答质量评估节点

```python
def grade_answer(state: RAGState) -> dict:
    """评估生成的回答质量"""
    question = state["question"]
    answer = state["answer"]

    response = llm.invoke([
        SystemMessage(content="""你是一个回答质量评估专家。
判断回答是否准确、完整地解答了用户问题。
只返回 "good" 或 "bad"，不要解释。"""),
        HumanMessage(content=f"问题：{question}\n回答：{answer}")
    ])
    grade = response.content.strip().lower()
    return {"answer_grade": grade}
```

```
三个评估/生成节点的分工：

  grade_documents → 检索到的文档相不相关？
                     ├── relevant → 继续生成回答
                     └── not_relevant → 重新检索

  generate        → 基于文档生成回答

  grade_answer    → 生成的回答好不好？
                     ├── good → 完成！
                     └── bad → 重新生成
```

---

## 10.4 构建反馈循环（不满意 → 重新检索）

### Step 7：路由函数

```python
MAX_RETRIES = 3

def route_after_doc_grade(state: RAGState) -> str:
    """文档评估后的路由"""
    if state["doc_grade"] == "relevant":
        return "generate"        # 文档相关 → 生成回答
    elif state["retry_count"] >= MAX_RETRIES:
        return "generate"        # 超过重试上限 → 强制生成（用现有文档凑合）
    else:
        return "rewrite_query"   # 文档不相关 → 重写查询

def route_after_answer_grade(state: RAGState) -> str:
    """回答评估后的路由"""
    if "good" in state["answer_grade"]:
        return END               # 回答合格 → 结束
    elif state["retry_count"] >= MAX_RETRIES:
        return END               # 超过重试上限 → 强制结束
    else:
        return "generate"        # 回答不好 → 重新生成

def increment_retry(state: RAGState) -> dict:
    """递增重试计数（在重写查询前调用）"""
    return {"retry_count": state["retry_count"] + 1}
```

### Step 8：组装完整的图

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

graph = StateGraph(RAGState)

# 添加节点
graph.add_node("rewrite_query", rewrite_query)
graph.add_node("retrieve", retrieve)
graph.add_node("grade_documents", grade_documents)
graph.add_node("generate", generate)
graph.add_node("grade_answer", grade_answer)

# 添加边
graph.add_edge(START, "rewrite_query")
graph.add_edge("rewrite_query", "retrieve")
graph.add_edge("retrieve", "grade_documents")

# 条件边 1：文档评估后
graph.add_conditional_edges("grade_documents", route_after_doc_grade, {
    "generate": "generate",
    "rewrite_query": "rewrite_query",
})

graph.add_edge("generate", "grade_answer")

# 条件边 2：回答评估后
graph.add_conditional_edges("grade_answer", route_after_answer_grade, {
    "generate": "generate",
    END: END,
})

# 编译
app = graph.compile(checkpointer=MemorySaver())
```

```
完整的图结构（包含两个反馈循环）：

  START → [rewrite_query] → [retrieve] → [grade_documents]
              ↑                                │
              │                    ┌───────────┴───────────┐
              │                    ↓                       ↓
              └── not_relevant ── [重试]            [generate]
                  (重写查询)                            │
                                                       ↓
                                               [grade_answer]
                                                       │
                                           ┌───────────┴───────────┐
                                           ↓                       ↓
                                      [generate]                  END
                                      (重新生成)              (回答合格)
```

---

## 10.5 完整代码与运行演示

### 运行测试

```python
config = {"configurable": {"thread_id": "rag_demo"}}

# 测试 1：能找到相关文档的问题
print("=== 测试 1：LangGraph 持久化 ===")
result = app.invoke({
    "question": "LangGraph 怎么实现持久化？",
    "rewritten_query": "",
    "documents": [],
    "answer": "",
    "doc_grade": "",
    "answer_grade": "",
    "retry_count": 0,
    "messages": [],
}, config={"configurable": {"thread_id": "test_1"}})

print(f"检索查询: {result['rewritten_query']}")
print(f"文档评分: {result['doc_grade']}")
print(f"回答评分: {result['answer_grade']}")
print(f"重试次数: {result['retry_count']}")
print(f"回答: {result['answer'][:200]}...")

# 测试 2：需要重写查询的问题
print("\n=== 测试 2：模糊问题 ===")
result = app.invoke({
    "question": "图怎么存状态？",
    "rewritten_query": "",
    "documents": [],
    "answer": "",
    "doc_grade": "",
    "answer_grade": "",
    "retry_count": 0,
    "messages": [],
}, config={"configurable": {"thread_id": "test_2"}})

print(f"最终查询: {result['rewritten_query']}")
print(f"重试次数: {result['retry_count']}")
print(f"回答: {result['answer'][:200]}...")
```

### 预期输出

```
=== 测试 1：LangGraph 持久化 ===
检索查询: LangGraph 怎么实现持久化？
文档评分: relevant
回答评分: good
重试次数: 0
回答: LangGraph 通过 Checkpointer 机制实现持久化。它支持三种存储后端：
- MemorySaver：内存存储，适合开发调试
- SqliteSaver：SQLite 文件存储，适合单机部署
- PostgresSaver：PostgreSQL 数据库存储，适合生产环境
你只需要在 compile() 时传入 checkpointer 参数即可启用...

=== 测试 2：模糊问题 ===
最终查询: LangGraph State 持久化 Checkpointer   ← LLM 重写了查询
重试次数: 1                                     ← 重试了 1 次
回答: LangGraph 的状态持久化通过 Checkpointer 实现...
```

### 用 stream 追踪执行过程

```python
for node_name, update in app.stream(input_data, config, stream_mode="updates"):
    print(f"📍 执行节点: {node_name}")
    if "doc_grade" in update:
        print(f"   文档评分: {update['doc_grade']}")
    if "answer_grade" in update:
        print(f"   回答评分: {update['answer_grade']}")
    if "rewritten_query" in update:
        print(f"   搜索查询: {update['rewritten_query']}")
```

```
输出：

  📍 执行节点: rewrite_query
     搜索查询: LangGraph 怎么实现持久化？
  📍 执行节点: retrieve
  📍 执行节点: grade_documents
     文档评分: relevant
  📍 执行节点: generate
  📍 执行节点: grade_answer
     回答评分: good
```

> **关键收获**：整个自纠错 RAG Agent 的核心就是**两个条件边形成的两个反馈循环**——文档不相关就重新检索，回答不好就重新生成。这种"评估 → 重试"的模式可以应用到任何需要质量保证的 Agent 系统中。

---

## 本章小结

| 知识点 | 在项目中的应用 |
|--------|--------------|
| State 设计 | 7 个字段覆盖 RAG 的完整生命周期 |
| 查询重写 | 第一次直接用，重试时 LLM 重写 |
| 检索 | 简易关键词匹配（可替换为向量搜索） |
| LLM 评估 | 文档相关性 + 回答质量双重评估 |
| 条件边 | 两个路由函数实现两个反馈循环 |
| 循环 + 兜底 | retry_count 防止无限循环 |
| Streaming | 实时追踪执行节点和评估结果 |

> **下一章预告**：生产部署与最佳实践 —— LangGraph Cloud / LangGraph Platform、性能优化、监控和可观测性。从"能跑"到"能用于生产"。


