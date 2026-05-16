# AI 应用的成本控制与优化

> 从一个月烧 $500 到 $50——手把手教你把 AI 应用的账单砍下来，同时不牺牲用户体验。

---

## 5. RAG 成本优化：检索层的省钱之道

前面我们优化了模型选型、Prompt、缓存——但 RAG 系统中还有一个关键环节直接影响成本：**你往 LLM 里塞了多少检索结果**。

塞得越多 → 输入 Token 越多 → 成本越高。但塞得太少 → 漏掉关键信息 → 回答质量差。这一章，我们找到这个平衡点。

---

### 5.1 Embedding 成本：计算一次还是每次都算

### 两种 Embedding 成本

```
Embedding 成本分为两部分：

  1. 文档入库（离线，一次性）
  ─────────────────────────────────────
    场景：把 1000 篇文档向量化存入数据库
    计算量：1000 篇 × 平均 10 块/篇 = 10000 次 Embedding
    
    OpenAI text-embedding-3-small：
      10000 × 平均 200 tokens × $0.02/1M = $0.04
      → 几乎可以忽略

    本地 BGE-large-zh：
      10000 次 × 50ms/次 = 500 秒 ≈ 8 分钟
      → 成本 = 电费 ≈ ¥0.1

    结论：入库成本很低，不是优化重点


  2. 查询向量化（在线，每次都算）
  ─────────────────────────────────────
    场景：用户每次提问都要向量化查询
    月查询量：10 万次

    OpenAI：
      100000 × 20 tokens × $0.02/1M = $0.04/月
      → 也很低

    本地 BGE：
      100000 × 30ms/次 = 3000 秒 = 50 分钟 CPU 时间
      → 成本可以忽略

    结论：查询 Embedding 成本也很低
    
  真正的结论：
    Embedding 本身的成本不是大头
    但 Embedding 的结果——检索出的上下文
    喂给 LLM 后产生的 Token 成本，才是大头！
```

### 什么时候 Embedding 成本值得关注

| 场景 | 文档规模 | 入库成本 | 是否需要优化 |
|------|---------|---------|------------|
| 小型知识库 | < 1 万块 | ~$0.04 | ❌ 不需要 |
| 中型知识库 | 1-10 万块 | ~$0.4 | ❌ 不需要 |
| 大型知识库 | 10-100 万块 | ~$4 | ⚠️ 考虑本地模型 |
| 超大型 + 频繁更新 | > 100 万块，每天更新 | ~$120/月 | ✅ 必须用本地模型 |

> **省 Embedding 钱的唯一场景**：超大型知识库 + 频繁全量重建。这种时候用本地 BGE 模型可以把 Embedding 成本降为电费。

### 5.2 Context 窗口管理：喂给 LLM 的不是越多越好

这是 RAG 成本优化中**最重要的一环**——控制喂给 LLM 的上下文数量。

### 检索数量 vs 成本

```
不同检索数量的成本对比：

  假设每个文档块 ≈ 200 tokens

  检索数量    上下文 Token    输入总量     单次成本(4o-mini)   月成本(10万次)
  ─────────────────────────────────────────────────────────────
  Top-3       600            1100        $0.000165          $16.5
  Top-5       1000           1500        $0.000225          $22.5
  Top-10      2000           2500        $0.000375          $37.5
  Top-20      4000           4500        $0.000675          $67.5

  （输入总量 = 上下文 + System Prompt 500 tokens）

  从 Top-10 降到 Top-5：
    月省 $15（10万次），年省 $180
    
  从 Top-10 降到 Top-3：
    月省 $21（10万次），年省 $252

  如果用 GPT-4o（输入价贵 16 倍）：
    Top-10 → Top-3 月省 $336
```

### 更少但更准 > 更多但有噪声

```
一个反直觉的实验结果：

  实验：100 个测试问题，评估回答准确率

  Top-3 检索（精选）：
    → 回答准确率：87%
    → 3 个块都高度相关
    → LLM 注意力集中在有效信息上

  Top-10 检索（大量）：
    → 回答准确率：82% ← 反而更低！
    → 其中 5-6 个块是噪声
    → LLM 被无关内容干扰

  为什么更多反而更差？
  ─────────────────────────────────────
  • LLM 的注意力会被无关内容分散
  • 噪声块可能包含"误导信息"
  • 上下文太长时，LLM 容易忽略中间内容
    （"Lost in the Middle" 问题）

  结论：Top-5 配合 Reranker 是性价比之王
  → 检索 Top-20 → Reranker 精选 Top-5 → 喂给 LLM
  → 既保证了召回率，又控制了输入 Token
```

### 实战：动态上下文数量

```python
def adaptive_context(
    question: str,
    search_results: list[dict],
    max_tokens: int = 1500
) -> list[dict]:
    """动态控制上下文数量，不超过 Token 预算"""
    
    selected = []
    total_tokens = 0
    
    for result in search_results:
        chunk_tokens = len(result["content"]) // 2  # 粗估中文 token
        
        if total_tokens + chunk_tokens > max_tokens:
            break  # 超预算，停止添加
        
        selected.append(result)
        total_tokens += chunk_tokens
    
    return selected

# 用法：无论检索多少，上下文总 Token 不超过 1500
results = vector_search(question, top_k=20)  # 检索 20 个
context = adaptive_context(question, results, max_tokens=1500)
# → 通常选出 5-7 个最相关的块
```

> **Token 预算**：给上下文设一个硬预算（如 1500 tokens），无论检索多少条，喂给 LLM 的总量不超过这个预算。这是最简单粗暴但极其有效的成本控制手段。

### 5.3 分块策略对成本的影响

分块大小直接决定了每次检索喂给 LLM 多少 Token。

### 分块大小 vs Token 消耗

```
相同知识库，不同分块策略的对比：

  原始文档：1000 篇 × 平均 2000 字 = 200 万字

  分块 800 字（大块）：
    块数 ≈ 2500 块
    Top-5 上下文 ≈ 4000 字 ≈ 2600 tokens
    月成本（10万次，4o-mini）：$39

  分块 400 字（中块）：
    块数 ≈ 5000 块
    Top-5 上下文 ≈ 2000 字 ≈ 1300 tokens
    月成本（10万次，4o-mini）：$19.5

  分块 200 字（小块）：
    块数 ≈ 10000 块
    Top-5 上下文 ≈ 1000 字 ≈ 650 tokens
    月成本（10万次，4o-mini）：$9.75

  ─────────────────────────────────────
  800字 → 200字：成本降低 75%！
  但！块太小可能导致语义不完整，召回率下降
```

### 分块大小的最优区间

```
分块大小 vs 质量 vs 成本的三角关系：

  分块太大（> 600 字）：
    ✅ 语义完整，上下文充分
    ❌ Token 消耗高
    ❌ 可能包含无关段落

  分块太小（< 150 字）：
    ✅ Token 消耗低
    ❌ 语义可能不完整
    ❌ 检索可能切掉关键上下文

  最优区间：250-400 字（中文）
  ─────────────────────────────────────
    → 每块约 150-250 tokens
    → Top-5 上下文约 750-1250 tokens
    → 语义基本完整
    → 成本可控

  推荐参数：
    chunk_size = 350（中文字符）
    chunk_overlap = 70（20% 重叠）
```

### 5.4 预过滤与重排序：少喂无关内容

检索出来的 Top-K 结果中，不是每一条都值得喂给 LLM。

### 三级过滤漏斗

```
从检索到 LLM 输入的过滤漏斗：

  向量检索 Top-20
       │         ← 20 个候选，可能含噪声
       ▼
  相似度阈值过滤（> 0.7）
       │         ← 过滤掉不相关的，剩 12-15 个
       ▼
  Reranker 重排序 + 取 Top-5
       │         ← 精选最相关的 5 个
       ▼
  Token 预算裁剪（< 1500 tokens）
       │         ← 确保不超预算
       ▼
  喂给 LLM（5 个高质量块）

  效果：
    无过滤（Top-10 直喂）：~2500 tokens，准确率 82%
    三级过滤后（Top-5）：~1200 tokens，准确率 89%
    → Token 减少 52%，准确率反而提升 7%
```

### 实战代码：带成本控制的 RAG 流水线

```python
def cost_optimized_rag(
    question: str,
    collection,
    embedding_model,
    reranker,
    llm_client,
    similarity_threshold: float = 0.7,
    max_context_tokens: int = 1500,
    top_k_retrieval: int = 20,
    top_k_final: int = 5,
    model: str = "gpt-4o-mini"
) -> dict:
    """成本优化的 RAG 流水线"""

    # 1. 向量检索（宽泛）
    query_emb = embedding_model.encode([question])
    raw_results = collection.query(
        query_embeddings=query_emb.tolist(),
        n_results=top_k_retrieval
    )

    # 2. 相似度阈值过滤
    filtered = []
    for doc, distance in zip(raw_results["documents"][0], raw_results["distances"][0]):
        similarity = 1 - distance  # 如果用 L2 距离
        if similarity >= similarity_threshold:
            filtered.append({"content": doc, "similarity": similarity})

    # 3. Reranker 精排
    if len(filtered) > top_k_final:
        pairs = [question, doc["content"](question, doc["content") for doc in filtered]
        scores = reranker.predict(pairs)
        ranked = sorted(zip(filtered, scores), key=lambda x: x[1], reverse=True)
        filtered = [doc for doc, _ in ranked[:top_k_final]]

    # 4. Token 预算裁剪
    context_parts = []
    total_tokens = 0
    for doc in filtered:
        chunk_tokens = len(doc["content"]) // 2
        if total_tokens + chunk_tokens > max_context_tokens:
            break
        context_parts.append(doc["content"])
        total_tokens += chunk_tokens

    context = "\n\n---\n\n".join(context_parts)

    # 5. LLM 生成（精简 Prompt）
    response = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "技术助手。基于参考资料简洁回答。无相关内容则告知。"},
            {"role": "user", "content": f"参考：\n{context}\n\n问题：{question}"}
        ],
        max_tokens=500
    )

    return {
        "answer": response.choices[0].message.content,
        "chunks_used": len(context_parts),
        "context_tokens": total_tokens,
        "total_tokens": response.usage.total_tokens,
        "model": model
    }
```

> **成本公式**：RAG 单次成本 ≈ (System Prompt + 检索上下文 + 问题) × 输入单价 + 回答 × 输出单价。通过三级过滤，检索上下文部分可以减少 50% 以上。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Embedding 成本 | 本身很便宜（$0.04/10万次），不是优化重点 |
| 真正的大头 | 检索结果喂给 LLM 产生的 Token 成本 |
| Context 管理 | Top-10→Top-5 省 $15/月，Top-10→Top-3 省 $21/月 |
| Lost in the Middle | 上下文太长反而降低准确率，精选 > 堆量 |
| Token 预算 | 给上下文设硬预算（1500 tokens），超了就截 |
| 分块最优区间 | 250-400 字/块（中文），chunk_overlap=20% |
| 三级过滤 | 阈值过滤 → Reranker → Token 裁剪，省 52% |
| 性价比之王 | 检索 Top-20 → Reranker 选 Top-5 → 喂 LLM |

> **下一章预告**：流量控制与限流——防止账单爆炸。我们会实现 Token 预算机制、用户级配额、FastAPI 限流中间件，以及账单异常告警和自动熔断。
