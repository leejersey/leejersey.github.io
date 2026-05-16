# RAG 进阶检索架构

> 从单路向量检索到多路混合检索：掌握混合检索融合、Rerank 精排、层级 RAG（父子块）、结构化与非结构化联合检索、检索路由策略的完整架构设计。

---

## 1. 朴素 RAG 的瓶颈与进阶方向

### 1.1 标准 RAG 架构回顾与瓶颈分析

```
标准 RAG 流程（面试必画）：

  用户提问 → Embedding → 向量检索 Top-K → 拼接 Prompt → LLM 生成

  这个流程的三大瓶颈：

  瓶颈 1：语义鸿沟（Semantic Gap）
  → 用户问"苹果股价"，向量检索可能返回"苹果的营养价值"
  → 向量检索对精确关键词/专有名词不敏感
  → 解决：混合检索（向量 + 关键词 BM25）

  瓶颈 2：排序粗糙（Ranking Quality）
  → 向量相似度 ≠ 相关性，Top-5 中可能 3 条无关
  → Embedding 模型的能力上限导致粗排不够精准
  → 解决：Rerank 重排序（粗检索 100 条 → 精排 5 条）

  瓶颈 3：上下文断裂（Context Fragmentation）
  → 小块检索精准，但丢失上下文
  → 大块保留上下文，但检索不精准
  → 解决：层级 RAG（小块检索 → 返回父块）
```

### 1.2 进阶 RAG 架构全景图

```
进阶 RAG 检索架构全景：

  用户提问
      │
      ▼
  ┌──────────────┐
  │ ① 查询处理    │  查询改写 / HyDE / Multi-Query
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ ② 检索路由    │  根据问题类型选择检索策略
  └──┬───┬───┬──┘
     │   │   │
     ▼   ▼   ▼
  ┌────┐┌────┐┌────┐
  │向量││BM25││SQL │   ③ 多路并行检索
  │检索││检索││查询│
  └─┬──┘└─┬──┘└─┬──┘
    │     │     │
    └─────┼─────┘
          ▼
  ┌──────────────┐
  │ ④ 融合排序    │  RRF / 加权融合
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ ⑤ Rerank     │  Cross-Encoder 精排
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ ⑥ 上下文扩展  │  父块扩展 / 窗口扩展
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ ⑦ LLM 生成   │  拼接 Prompt + 生成答案
  └──────────────┘
```

> 💡 **面试答题框架**：被问"RAG 怎么优化"时，按这 7 层回答——查询改写 → 多路检索 → 融合排序 → Rerank → 上下文扩展 → LLM 生成。

---

## 2. 多路混合检索架构

单靠向量检索不够——关键词搜不到、专有名词匹配不上。混合检索是生产环境的标配。

### 2.1 向量检索 vs 关键词检索 vs 全文检索

```
三种检索方式对比：

  检索方式     原理               擅长                  不擅长
  ─────────────────────────────────────────────────────────────
  向量检索     Embedding 相似度   语义理解/同义词        精确关键词/专有名词
  关键词 BM25  词频统计            精确匹配/专有名词      语义理解/同义词
  全文检索     倒排索引+TF-IDF    长文本/模糊匹配        语义理解

  举例：
  → 问"Python 怎么读取 Excel"
  → 向量检索可能返回"如何用编程语言处理表格"（语义对但模糊）
  → BM25 直接匹配"Python" + "Excel"（精确命中）
  → 混合检索两个都返回，效果最好
```

### 2.2 混合检索融合策略：RRF 与加权融合

```python
# ═══════════════════════════════════════
# RRF（Reciprocal Rank Fusion）融合算法
# ═══════════════════════════════════════

def reciprocal_rank_fusion(
    results_lists: list[list[dict]],
    k: int = 60,
) -> list[dict]:
    """
    RRF 融合：多路检索结果合并排序
    - 每条结果的得分 = Σ 1/(k + rank)
    - k=60 是论文推荐的常数
    """
    scores = {}

    for results in results_lists:
        for rank, doc in enumerate(results, 1):
            doc_id = doc["id"]
            if doc_id not in scores:
                scores[doc_id] = {"doc": doc, "score": 0}
            scores[doc_id]["score"] += 1 / (k + rank)

    # 按融合分数排序
    fused = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    return [item["doc"] for item in fused]

# 用法：
# vector_results = vector_store.search(query_emb, top_k=50)
# bm25_results = bm25_search(query_text, top_k=50)
# fused = reciprocal_rank_fusion([vector_results, bm25_results])
# → 融合后取 Top-5
```

### 2.3 实战：Qdrant + BM25 混合检索

```python
# ═══════════════════════════════════════
# 混合检索器
# ═══════════════════════════════════════
from rank_bm25 import BM25Okapi
import jieba

class HybridRetriever:
    """混合检索：向量 + BM25"""

    def __init__(self, vector_store, documents: list[dict]):
        self.vector_store = vector_store

        # 构建 BM25 索引
        tokenized = [list(jieba.cut(d["content"])) for d in documents]
        self.bm25 = BM25Okapi(tokenized)
        self.documents = documents

    def search(self, query: str, query_embedding: list[float],
               top_k: int = 5, vector_weight: float = 0.6) -> list[dict]:
        """混合检索"""
        # 路线 1: 向量检索
        vector_results = self.vector_store.search(query_embedding, top_k=50)

        # 路线 2: BM25 关键词检索
        query_tokens = list(jieba.cut(query))
        bm25_scores = self.bm25.get_scores(query_tokens)
        bm25_top = sorted(
            enumerate(bm25_scores), key=lambda x: x[1], reverse=True
        )[:50]
        bm25_results = [self.documents[i] for i, _ in bm25_top]

        # 融合
        fused = reciprocal_rank_fusion([vector_results, bm25_results])
        return fused[:top_k]
```

> 💡 **面试答题要点**："混合检索用 RRF 融合，向量检索解决语义匹配，BM25 解决精确关键词匹配，两路互补。"

---

## 3. Rerank 重排序架构

粗检索只是"海选"，Rerank 才是"精挑"——把真正相关的结果排到最前面。

### 3.1 粗检索 + 精排序的两阶段架构

```
两阶段检索架构：

  阶段 1: 粗检索（Retrieval）
  → 方式：向量 + BM25 混合
  → 范围：从 100 万条中召回 Top-100
  → 速度：快（毫秒级）
  → 精度：一般（可能混入无关结果）

  阶段 2: 精排序（Rerank）
  → 方式：Cross-Encoder 逐对打分
  → 范围：对 Top-100 重新排序，取 Top-5
  → 速度：慢（百毫秒级，但只排 100 条）
  → 精度：高（直接建模 query-doc 相关性）

  为什么不直接用 Rerank 检索全部？
  → Cross-Encoder 需要逐对比较，100 万条太慢
  → 所以先粗检索缩小范围，再精排序提升质量
```

### 3.2 Rerank 模型选型与对比

```
主流 Rerank 模型：

  模型                      中文    部署方式    效果     成本
  ──────────────────────────────────────────────────────────
  Cohere Rerank v3          ✅      云端 API    ⭐⭐⭐   $2/1000次
  BGE-Reranker-v2-m3        ⭐⭐⭐  本地部署    ⭐⭐⭐   免费
  Jina-Reranker-v2          ✅      本地/API    ⭐⭐     免费
  ms-marco-MiniLM (英文)    ❌      本地部署    ⭐⭐     免费

  推荐：
  → 中文场景 → BGE-Reranker-v2-m3（免费、中文效果最好）
  → 快速验证 → Cohere Rerank API（零部署）
```

### 3.3 实战：Cross-Encoder Rerank

```python
# ═══════════════════════════════════════
# Rerank 实现（Cross-Encoder）
# ═══════════════════════════════════════
# pip install sentence-transformers
from sentence_transformers import CrossEncoder

class Reranker:
    """Cross-Encoder 重排序"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: list[dict],
               top_k: int = 5) -> list[dict]:
        """对检索结果重新排序"""
        # 构建 query-doc 对
        pairs = [(query, doc["content"]) for doc in documents]

        # Cross-Encoder 打分
        scores = self.model.predict(pairs)

        # 按分数排序
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [
            {**doc, "rerank_score": float(score)}
            for doc, score in scored_docs[:top_k]
        ]

# 用法：
# retriever = HybridRetriever(vector_store, documents)
# candidates = retriever.search(query, query_emb, top_k=50)
# reranker = Reranker()
# final = reranker.rerank(query, candidates, top_k=5)
# → 检索质量显著提升（Recall@5 通常提升 10-20%）
```

> 💡 **面试答题要点**："Rerank 是 RAG 质量提升最明显的优化手段——只加一个 Rerank 步骤，Recall@5 通常提升 10-20%，投入产出比最高。"

---

## 4. 层级 RAG 架构（父子块）

分块的两难困境——小块精准但缺上下文，大块完整但检索不准。层级 RAG 同时解决两个问题。

### 4.1 父子块架构：小块检索 + 大块生成

```
父子块架构核心思想：

  传统方案（只有一种块）：
  → chunk_size=500（检索精准，但上下文少）
  → chunk_size=2000（上下文多，但检索不精准）
  → 怎么都不完美

  父子块方案（两层块）：
  → 子块（Child）：200 字，用于检索（精准匹配）
  → 父块（Parent）：1000 字，用于生成（完整上下文）
  → 检索时用子块 → 命中后返回对应的父块给 LLM

  ┌─────────────────────────────────────┐
  │            父块（1000 字）            │  ← 这个给 LLM
  │  ┌─────┐  ┌─────┐  ┌─────┐         │
  │  │子块1 │  │子块2 │  │子块3 │        │  ← 这些用来检索
  │  └─────┘  └─────┘  └─────┘         │
  └─────────────────────────────────────┘
```

### 4.2 摘要级粗检 → 细节块精检

```
两级检索架构：

  Level 1: 文档摘要级检索
  → 每篇文档生成一段摘要（LLM 总结）
  → 先用摘要做粗检索，定位相关文档
  → 快速过滤不相关的文档

  Level 2: 细节块级精检
  → 在定位到的文档内，搜索具体的内容块
  → 返回精确匹配的段落

  效果：
  → 100 篇文档 × 50 块 = 5000 个块（传统方案全搜）
  → 摘要检索选出 5 篇 × 50 块 = 250 个块（缩小 20 倍）
```

### 4.3 实战：ParentDocumentRetriever

```python
# ═══════════════════════════════════════
# 父子块检索器
# ═══════════════════════════════════════

class ParentChildRetriever:
    """父子块检索：子块检索 + 父块返回"""

    def __init__(self, vector_store, parent_store: dict):
        self.vector_store = vector_store  # 子块向量库
        self.parent_store = parent_store  # 父块存储 {parent_id: content}

    def ingest(self, documents: list[dict],
               child_size: int = 200, parent_size: int = 1000):
        """入库：同时生成父块和子块"""
        for doc in documents:
            # 生成父块
            parent_chunks = chunk_by_size(doc["content"], parent_size, overlap=0)

            for p_idx, parent_text in enumerate(parent_chunks):
                parent_id = f"{doc['id']}_p{p_idx}"
                self.parent_store[parent_id] = parent_text

                # 在父块内生成子块
                child_chunks = chunk_by_size(parent_text, child_size, overlap=20)
                for c_idx, child_text in enumerate(child_chunks):
                    self.vector_store.upsert({
                        "content": child_text,
                        "parent_id": parent_id,  # 关联到父块
                        "embedding": embed(child_text),
                    })

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[str]:
        """检索子块 → 返回父块"""
        # 用子块检索
        child_results = self.vector_store.search(query_embedding, top_k=top_k * 2)

        # 去重：同一个父块只返回一次
        seen_parents = set()
        parent_texts = []
        for child in child_results:
            parent_id = child["metadata"]["parent_id"]
            if parent_id not in seen_parents:
                seen_parents.add(parent_id)
                parent_texts.append(self.parent_store[parent_id])
            if len(parent_texts) >= top_k:
                break

        return parent_texts  # 返回父块给 LLM
```

> 💡 **面试答题要点**："层级 RAG 解决分块粒度的两难问题——小块保证检索精度，父块保证上下文完整性。"

---

## 5. 混合数据源联合检索

企业知识不只在文档里——数据库有结构化数据，知识图谱有关系数据。联合检索才能全覆盖。

### 5.1 结构化 + 非结构化联合检索

```
联合检索架构：

  用户问："上个月销售额最高的产品是什么？相关的产品手册在哪？"

  路线 1（结构化）: Text-to-SQL
  → 查 MySQL："SELECT product, SUM(amount) ... ORDER BY ... LIMIT 1"
  → 结果："产品 A，销售额 500 万"

  路线 2（非结构化）: RAG 向量检索
  → 搜向量库："产品 A 手册"
  → 结果："产品 A 技术规格书.pdf 第 3 页"

  融合输出：
  → "上月销售额最高的是产品 A（500 万），这是它的技术手册..."
```

### 5.2 Text-to-SQL + RAG 混合架构

```python
# ═══════════════════════════════════════
# Text-to-SQL + RAG 混合检索
# ═══════════════════════════════════════

class HybridDataRetriever:
    """结构化 + 非结构化联合检索"""

    def __init__(self, llm, db_engine, vector_store):
        self.llm = llm
        self.db = db_engine
        self.vector_store = vector_store

    async def retrieve(self, query: str, query_embedding: list[float]) -> dict:
        """根据问题同时查数据库和向量库"""
        results = {}

        # 尝试 Text-to-SQL（如果问题涉及数据查询）
        sql = await self.llm.invoke(f"""
        根据以下问题生成 SQL（如果不适合 SQL 查询则返回 NONE）：
        问题: {query}
        表结构: sales(date, product, amount, region)
        """)

        if "NONE" not in sql.content:
            try:
                db_result = self.db.execute(sql.content)
                results["structured"] = db_result
            except Exception:
                pass

        # 向量检索
        rag_results = self.vector_store.search(query_embedding, top_k=3)
        results["unstructured"] = rag_results

        return results
```

### 5.3 GraphRAG：知识图谱增强检索

```
GraphRAG 架构思路：

  传统 RAG：
  → 文本 → 分块 → 向量检索 → 返回文本片段

  GraphRAG：
  → 文本 → 提取实体关系 → 构建知识图谱
  → 检索时：向量检索 + 图谱遍历
  → 返回：相关文本 + 关联实体 + 上下游关系

  优势：
  → 能回答关系类问题："谁是 CEO？他管理哪些部门？"
  → 能做多跳推理："A 的合作伙伴 B 的产品是什么？"
  → 传统 RAG 对这类问题无能为力
```

> 💡 **面试答题要点**："企业级 RAG 不能只有向量检索——结构化数据用 Text-to-SQL，关系数据用知识图谱，文档数据用向量检索，三路结果融合生成。"

---

## 6. 检索路由与自适应策略

不同的问题需要不同的检索策略——技术问题查文档，数据问题查数据库，模糊问题先改写再检索。

### 6.1 检索路由器：为不同问题选择最优策略

```python
# ═══════════════════════════════════════
# 检索路由器
# ═══════════════════════════════════════

class RetrievalRouter:
    """根据问题类型选择检索策略"""

    def __init__(self, llm):
        self.llm = llm

    async def route(self, query: str) -> str:
        """LLM 路由：判断该用哪种检索"""
        response = await self.llm.invoke(f"""
        判断以下问题应该用什么检索方式：
        问题: {query}

        选项：
        - "vector": 语义理解类（概念解释、方案推荐）
        - "keyword": 精确查找类（报错信息、API 名称）
        - "hybrid": 混合检索（不确定时）
        - "sql": 数据查询类（统计数字、排名）
        - "none": 不需要检索（闲聊、常识）

        只输出选项名称。
        """)
        return response.content.strip()

# 用法：
# strategy = await router.route("去年Q4的营收是多少？")
# → "sql"
# strategy = await router.route("什么是 RAG？")
# → "vector"
```

### 6.2 查询改写与扩展：HyDE / Multi-Query

```python
# ═══════════════════════════════════════
# 查询改写策略
# ═══════════════════════════════════════

# ① HyDE（Hypothetical Document Embedding）
# 思路：让 LLM 先生成一个"假设的答案"，用答案去检索
async def hyde_rewrite(llm, query: str) -> str:
    """HyDE: 用假设文档替代原始查询"""
    response = await llm.invoke(f"""
    请写一段简短的文本来回答这个问题（不需要准确，只需要包含相关术语）：
    {query}
    """)
    return response.content
    # → 用这段"假设答案"的 Embedding 去检索
    # → 比直接用问题检索效果好 20%

# ② Multi-Query（多查询扩展）
# 思路：把一个问题改写成多个角度，分别检索再合并
async def multi_query_rewrite(llm, query: str) -> list[str]:
    """生成多个角度的查询"""
    response = await llm.invoke(f"""
    将以下问题从 3 个不同角度改写，用于搜索：
    原始问题: {query}
    输出 3 个改写后的查询，每行一个。
    """)
    return response.content.strip().split("\n")
    # → 3 个查询分别检索，结果合并去重
```

### 6.3 实战：Agentic RAG 自适应检索

```
Agentic RAG 自适应流程：

  用户提问
      │
      ▼
  ① Agent 判断：需不需要检索？
      ├── 不需要 → 直接回答
      └── 需要 → 进入检索
          │
          ▼
  ② Agent 判断：用什么策略？
      ├── 模糊问题 → HyDE 改写后检索
      ├── 精确问题 → 关键词检索
      ├── 数据问题 → Text-to-SQL
      └── 通用问题 → 混合检索
          │
          ▼
  ③ 检索结果够不够？
      ├── 够了 → 生成答案
      └── 不够 → 换策略重试 / 改写查询重试
```

> 💡 **面试答题要点**："Agentic RAG 的核心是把检索决策交给 Agent——Agent 自主判断是否需要检索、用什么策略、结果够不够，而不是固定的检索流程。"

---

## 7. 检索质量评测与调优

### 7.1 评测指标与 A/B 测试方法

```
核心评测指标：

  指标        含义                    目标值        计算方式
  ──────────────────────────────────────────────────────────
  Recall@5    Top-5 中包含相关文档    > 80%         命中数/相关总数
  MRR         第一个相关结果的排名    > 0.7         1/排名 的均值
  Hit Rate    至少有一条命中          > 90%         命中查询/总查询
  NDCG@5      排名加权的相关性        > 0.8         DCG/IDCG

  A/B 测试方案：
  → 控制组：朴素向量检索
  → 实验组 A：混合检索（向量 + BM25）
  → 实验组 B：混合检索 + Rerank
  → 实验组 C：混合检索 + Rerank + 父子块
  → 用 50 条测试 Query 对比各组 Recall@5
```

### 7.2 检索失败诊断与调优指南

```
检索失败诊断表：

  症状                    根因                      解决方案
  ─────────────────────────────────────────────────────────────
  关键词搜不到            纯向量检索                加 BM25 混合检索
  语义相关但排名低        粗排不够精准              加 Rerank
  检索到但上下文不够      分块太小                  父子块 / 加 overlap
  完全搜不到相关内容      数据没入库 / 查询太模糊    查入库日志 / HyDE 改写
  返回过时内容            无时间过滤                加元数据时间过滤
  同一文档重复出现        去重不够                  按 doc_id 去重

  参数调优速查：
  → Top-K 太小（如 3）→ 召回率低 → 调到 5-10
  → Top-K 太大（如 50）→ 噪声多 → 加 Rerank 精排
  → 相似度阈值太高 → 漏掉相关结果 → 降低阈值
  → chunk_size 太大 → 检索不精准 → 减小 + 父子块
```

### 7.3 RAG 检索架构面试高频题

```
面试高频题 TOP 8：

  ❓ Q1: 朴素 RAG 有什么问题？怎么优化？
  → 三大瓶颈（语义鸿沟/排序粗糙/上下文断裂）
  → 对应方案（混合检索/Rerank/父子块）

  ❓ Q2: 向量检索和 BM25 各有什么优缺点？
  → 向量擅长语义、BM25 擅长精确关键词，混合互补

  ❓ Q3: RRF 融合算法是什么？
  → 多路检索结果按排名倒数求和，score = Σ 1/(k+rank)

  ❓ Q4: Rerank 放在哪一步？为什么？
  → 粗检索之后、LLM 之前。因为 Cross-Encoder 慢但准

  ❓ Q5: 什么是父子块？解决什么问题？
  → 小块检索精准，大块保留上下文，两全其美

  ❓ Q6: HyDE 是什么？
  → 先让 LLM 生成假设答案，用答案的 Embedding 去检索

  ❓ Q7: Agentic RAG 和普通 RAG 的区别？
  → 普通 RAG 是固定管线，Agentic RAG 是 Agent 自主决策

  ❓ Q8: 怎么评估 RAG 检索质量？
  → Recall@K + MRR + NDCG + RAGAS 端到端评测
```

> 🎉 **全文完成**。RAG 进阶检索的核心优化链路：**混合检索 → RRF 融合 → Rerank 精排 → 父子块扩展 → 查询改写 → 自适应路由**。每加一层优化，Recall 提升 5-20%。

---
