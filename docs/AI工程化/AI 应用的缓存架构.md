# AI 应用的缓存架构

> 从精确缓存到语义缓存，构建 AI 应用的多级缓存体系——Prompt Hash、Embedding 相似度匹配、分层缓存策略、缓存失效与一致性，让你的 LLM 调用成本降低 60%、响应速度提升 10 倍。

---

## 1. 为什么 AI 应用必须做缓存

### 1.1 LLM 调用的痛点：慢、贵、不稳定

如果你做过 AI 应用，一定对这三个数字不陌生：

```
一次 GPT-4o 调用的真实成本：

  延迟     ─── 3-15 秒（复杂 Prompt 可达 30 秒）
  费用     ─── $0.01-$0.10 / 次（input + output tokens）
  可用性   ─── 99.5%（OpenAI 官方 SLA）

  对比传统 API：
  延迟     ─── 50-200ms
  费用     ─── 接近 $0
  可用性   ─── 99.99%
```

三个痛点叠加，意味着：

- **慢**：用户等 10 秒看到回复，但其中 80% 的问题可能之前已经回答过
- **贵**：日均 10 万次调用 × $0.03/次 = **$3000/月**，其中大量是重复请求
- **不稳定**：API 限流、网络抖动、服务降级——任何一环出问题用户就看到报错

> 💡 **缓存是 AI 应用的"第一性优化"**——不是锦上添花，而是生产环境的必需品。一个设计良好的缓存层可以拦截 40-70% 的 LLM 调用，同时将 P99 延迟从 15 秒降到 50ms。

### 1.2 AI 缓存 vs 传统 Web 缓存：四大不同

传统 Web 缓存（Nginx 缓存、CDN、Redis 热点数据）的经验不能直接搬到 AI 场景。两者有根本性差异：

| 维度 | 传统 Web 缓存 | AI 应用缓存 |
|:---|:---|:---|
| **Key 匹配** | URL / Query String 精确匹配 | 需要语义相似度匹配 |
| **缓存粒度** | 整个响应 / 页面片段 | Prompt + Model + Params 组合 |
| **失效策略** | 数据变更触发 | 模型升级 / Prompt 模板变更触发 |
| **命中判断** | 完全一致才命中 | "意思差不多"也应该命中 |

举个例子——这三个 Prompt 应该命中同一条缓存：

```
❌ 传统缓存：3 个不同的 Key，3 次 LLM 调用

  "Python 的 GIL 是什么？"
  "请解释一下 Python GIL"
  "什么是 Python 的全局解释器锁？"

✅ 语义缓存：识别为同一个问题，只调用 1 次 LLM

  Embedding("Python 的 GIL 是什么？") 
    ≈ Embedding("请解释一下 Python GIL")        → 相似度 0.96
    ≈ Embedding("什么是 Python 的全局解释器锁？") → 相似度 0.94
  
  阈值 0.92 → 全部命中 ✓
```

这就是 AI 缓存最核心的创新：**从精确匹配到语义匹配**。

### 1.3 缓存能带来什么：成本、延迟、稳定性的全面提升

用一组真实数据来量化缓存的价值（基于日均 10 万次 LLM 调用的中等规模应用）：

```
缓存前 vs 缓存后（语义缓存，命中率 55%）：

  ┌──────────────┬─────────────┬─────────────┐
  │     指标      │   缓存前     │   缓存后     │
  ├──────────────┼─────────────┼─────────────┤
  │ 月 LLM 费用   │  $3,000     │  $1,350     │ ↓ 55%
  │ P50 延迟      │  5.2s       │  0.8s       │ ↓ 85%
  │ P99 延迟      │  15.1s      │  2.3s       │ ↓ 85%
  │ 错误率        │  1.2%       │  0.5%       │ ↓ 58%
  │ 日 LLM 调用   │  100,000    │  45,000     │ ↓ 55%
  └──────────────┴─────────────┴─────────────┘
```

三个维度的提升逻辑：

- **成本**：命中缓存的请求不调用 LLM → 直接省钱。55% 命中率 = 55% 成本削减
- **延迟**：Redis 读取 < 5ms vs LLM 调用 3-15s → 命中时延迟降低 **1000 倍**
- **稳定性**：缓存命中不依赖外部 API → 不受 OpenAI 限流/故障影响，error rate 下降
### 1.4 缓存架构总览：三种缓存 × 三层架构

本文的核心架构——**三种缓存类型** × **三层存储层级**：

```
三种缓存类型：

  ① 精确缓存 ─── Prompt Hash 完全匹配
     │           命中率低（10-20%），但零误差
     │
  ② 语义缓存 ─── Embedding 向量相似度匹配
     │           命中率高（40-60%），有容错空间
     │
  ③ 结果片段缓存 ── 检索结果 / Embedding 向量复用
                    针对 RAG 的中间结果缓存
```

```
三层存储层级（L1 → L2 → L3）：

  请求进入
    │
    ▼
  L1 本地内存（LRU，< 1ms）
    │ miss
    ▼
  L2 Redis（精确 Hash，< 5ms）
    │ miss
    ▼
  L3 向量数据库（语义搜索，< 50ms）
    │ miss
    ▼
  调用 LLM（3-15s）
    │
    └──→ 写回 L1 + L2 + L3
```

> 💡 **三层缓存不是二选一，而是串联使用**——L1 拦截热点、L2 拦截精确重复、L3 拦截语义相似。三层叠加可以达到 50-70% 的总命中率。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **三大痛点** | LLM 调用慢（秒级）、贵（$0.01+/次）、不稳定 |
| **核心创新** | 从精确匹配到语义匹配，"意思相近"也能命中 |
| **量化收益** | 55% 命中率 → 成本降 55%、延迟降 85% |
| **三层架构** | L1 内存 → L2 Redis → L3 向量库，逐级兜底 |

---

## 2. 精确缓存：Prompt Hash 匹配

### 2.1 原理：相同输入 → 相同输出

精确缓存是最简单的 AI 缓存策略：**把 Prompt 内容做哈希，作为缓存 Key**。

```
精确缓存的工作流程：

  用户输入 Prompt
    │
    ▼
  规范化处理（去空格、排序参数）
    │
    ▼
  计算 SHA-256 Hash → cache_key
    │
    ├── Redis GET cache_key
    │     │
    │     ├── HIT  → 直接返回缓存的 response
    │     │
    │     └── MISS → 调用 LLM → 存入 Redis → 返回
    │
    ▼
  完成
```

精确缓存的前提是 **LLM 输出的确定性**。你需要把 `temperature` 设为 0：

```python
# temperature=0 时，相同输入 → 几乎相同输出
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "什么是 Python 的 GIL？"}],
    temperature=0,      # 关键：确保输出确定性
    seed=42,            # OpenAI 的确定性种子（beta）
)
```

> 💡 **`temperature=0` 不是 100% 确定性**——OpenAI 官方说明即使 temperature=0，输出也可能有微小差异。但对于缓存场景，这个差异可以忽略。精确缓存的价值在于"完全相同的问题不重复调用"。

### 2.2 哈希策略：如何规范化 Prompt 再计算 Hash

直接对原始 Prompt 字符串做 Hash 会有一个问题——**微小的格式差异会导致 Hash 不同**：

```
这两个 Prompt 语义完全相同，但 Hash 不同：

  "什么是Python的GIL？"     → Hash: a3f2...
  "什么是 Python 的 GIL？"  → Hash: 7b1e...   ← 多了空格
  "什么是 Python 的 GIL?"   → Hash: c9d4...   ← 全角→半角问号
```

解决方案是**先规范化，再哈希**：

```python
import hashlib
import json
import re
import unicodedata

class PromptNormalizer:
    """Prompt 规范化器：消除无意义的格式差异"""
    
    @staticmethod
    def normalize(text: str) -> str:
        # 1. Unicode 标准化（全角→半角等）
        text = unicodedata.normalize("NFKC", text)
        
        # 2. 统一空白字符（多个空格/tab → 单个空格）
        text = re.sub(r"\s+", " ", text).strip()
        
        # 3. 统一标点（中文标点 → 英文标点）
        punctuation_map = str.maketrans("，。！？；：""''", ",.!?;:\"\"''")
        text = text.translate(punctuation_map)
        
        # 4. 转小写（可选，取决于业务需求）
        text = text.lower()
        
        return text
    
    @staticmethod
    def compute_cache_key(
        messages: list[dict],
        model: str,
        temperature: float = 0,
        **kwargs
    ) -> str:
        """计算缓存 Key：model + params + messages_hash"""
        
        # 规范化每条消息
        normalized_messages = []
        for msg in messages:
            normalized_messages.append({
                "role": msg["role"],
                "content": PromptNormalizer.normalize(msg["content"]),
            })
        
        # 组合所有影响输出的参数
        cache_input = {
            "model": model,
            "temperature": temperature,
            "messages": normalized_messages,
        }
        
        # 序列化并计算 Hash
        content = json.dumps(cache_input, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

# 使用示例
normalizer = PromptNormalizer()
key = normalizer.compute_cache_key(
    messages=[{"role": "user", "content": "什么是 Python 的 GIL？"}],
    model="gpt-4o",
)
print(f"Cache Key: llm:exact:{key}")  # llm:exact:3a7f2b1c9d4e8f0a
```

> 💡 **缓存 Key 必须包含 model 和 temperature**——同一个 Prompt 用 GPT-4o 和 GPT-4o-mini 的回答不同，用 temperature=0 和 temperature=0.7 的回答也不同。这些参数都要参与哈希计算。

### 2.3 Redis 实现：完整的精确缓存服务

把规范化和 Redis 操作封装成一个完整的缓存服务：

```python
import redis.asyncio as redis
import json
import time
from dataclasses import dataclass

@dataclass
class CacheResult:
    """缓存查询结果"""
    hit: bool
    content: str | None = None
    cached_at: float | None = None    # 缓存写入时间
    model: str | None = None

class ExactCacheService:
    """精确缓存服务：基于 Prompt Hash 的 Redis 缓存"""
    
    PREFIX = "llm:exact"
    
    def __init__(self, redis_client: redis.Redis, default_ttl: int = 7200):
        self.redis = redis_client
        self.default_ttl = default_ttl  # 默认 2 小时
        self.normalizer = PromptNormalizer()
    
    async def get(self, messages: list[dict], model: str, **kwargs) -> CacheResult:
        """查询缓存"""
        cache_key = self._build_key(messages, model, **kwargs)
        
        data = await self.redis.get(cache_key)
        if data:
            parsed = json.loads(data)
            # 记录命中统计
            await self.redis.incr(f"{self.PREFIX}:stats:hits")
            return CacheResult(
                hit=True,
                content=parsed["content"],
                cached_at=parsed["cached_at"],
                model=parsed["model"],
            )
        
        await self.redis.incr(f"{self.PREFIX}:stats:misses")
        return CacheResult(hit=False)
    
    async def set(
        self, messages: list[dict], model: str,
        content: str, ttl: int | None = None, **kwargs
    ):
        """写入缓存"""
        cache_key = self._build_key(messages, model, **kwargs)
        
        data = json.dumps({
            "content": content,
            "model": model,
            "cached_at": time.time(),
        }, ensure_ascii=False)
        
        await self.redis.setex(cache_key, ttl or self.default_ttl, data)
    
    async def get_stats(self) -> dict:
        """获取命中率统计"""
        hits = int(await self.redis.get(f"{self.PREFIX}:stats:hits") or 0)
        misses = int(await self.redis.get(f"{self.PREFIX}:stats:misses") or 0)
        total = hits + misses
        return {
            "hits": hits,
            "misses": misses,
            "hit_rate": f"{hits / total * 100:.1f}%" if total > 0 else "N/A",
        }
    
    def _build_key(self, messages: list[dict], model: str, **kwargs) -> str:
        prompt_hash = self.normalizer.compute_cache_key(messages, model, **kwargs)
        return f"{self.PREFIX}:{prompt_hash}"
```

在 FastAPI 中集成：

```python
# 在路由中使用精确缓存
@chat_router.post("/completions")
async def chat_completions(
    request: ChatRequest,
    cache: ExactCacheService = Depends(get_cache_service),
    llm: AsyncOpenAI = Depends(get_llm),
):
    messages = [{"role": "user", "content": request.message}]
    
    # 1. 查缓存
    cached = await cache.get(messages, request.model)
    if cached.hit:
        return {"content": cached.content, "cached": True}
    
    # 2. 调用 LLM
    response = await llm.chat.completions.create(
        model=request.model,
        messages=messages,
        temperature=0,
    )
    content = response.choices[0].message.content
    
    # 3. 写缓存
    await cache.set(messages, request.model, content)
    
    return {"content": content, "cached": False}
```
### 2.4 适用场景与局限：什么时候精确缓存就够了

精确缓存简单可靠，但不是万能的。看看它在哪些场景下效果最好：

| 场景 | 命中率 | 推荐度 | 说明 |
|:---|:---|:---|:---|
| **FAQ / 知识库问答** | 30-50% | ⭐⭐⭐⭐⭐ | 用户问题高度重复 |
| **固定 Prompt 模板** | 50-80% | ⭐⭐⭐⭐⭐ | 模板 + 参数组合有限 |
| **代码生成** | 5-15% | ⭐⭐ | 输入太灵活，重复率低 |
| **自由对话** | 2-8% | ⭐ | 几乎每次都不一样 |
| **数据分析/报表** | 20-40% | ⭐⭐⭐⭐ | 相同数据+相同问题重复率高 |

精确缓存的局限性：

```
精确缓存解决不了的问题：

  "Python GIL 是什么？"        ← 已缓存 ✓
  "请解释 Python 的 GIL"       ← MISS ✗（字面不同）
  "什么是全局解释器锁？"        ← MISS ✗（换了说法）
  "GIL 对多线程有什么影响？"    ← MISS ✗（相关但不同）

  → 这些"同义不同形"的请求，需要语义缓存来解决
    （见第 3 章）
```

> 💡 **精确缓存是基础层，不是唯一层**——它的价值在于零成本命中（不需要计算 Embedding）、零误差（完全匹配才返回）。即使引入了语义缓存，精确缓存仍然应该作为 L2 层保留。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **核心原理** | Prompt Hash 精确匹配，相同输入复用输出 |
| **规范化** | Unicode 统一 + 空格合并 + 标点统一 + 转小写 |
| **Key 组成** | model + temperature + normalized_messages 的 SHA-256 |
| **命中率** | FAQ 场景 30-50%，自由对话仅 2-8% |
| **局限性** | 无法处理"同义不同形"的请求 |

---

## 3. 语义缓存：Embedding 相似度匹配

### 3.1 原理：意思相近 → 复用答案

语义缓存的核心思想：**把 Prompt 转成向量，在向量空间中找"最近的邻居"**。

```
语义缓存的工作流程：

  用户输入 "请解释一下 Python GIL"
    │
    ▼
  Embedding 模型 → 转成 1536 维向量 [0.023, -0.041, ...]
    │
    ▼
  在向量数据库中搜索最相似的已缓存 Prompt
    │
    ├── 找到 "Python 的 GIL 是什么？" → 相似度 0.96
    │     │
    │     ├── 0.96 > 阈值 0.92 → HIT ✓ 返回缓存的回答
    │     │
    │     └── 0.96 < 阈值 0.92 → MISS ✗ 调用 LLM
    │
    ▼
  若 MISS：调用 LLM → 把 Prompt 向量 + 回答 存入向量数据库
```

和精确缓存相比，语义缓存的关键差异：

```
精确缓存：input_hash == cached_hash → 命中
           │
           └── 只能处理完全相同的输入

语义缓存：cosine_similarity(input_vec, cached_vec) > threshold → 命中
           │
           └── 能处理"意思差不多"的输入
               命中率从 10-20% 提升到 40-60%
```

### 3.2 Embedding 模型选择与生成

选择 Embedding 模型要考虑三个因素：**质量、速度、成本**。

| 模型 | 维度 | 中文效果 | 延迟 | 价格 | 推荐场景 |
|:---|:---|:---|:---|:---|:---|
| `text-embedding-3-small` | 1536 | ★★★★ | ~20ms | $0.02/1M tokens | 通用首选 |
| `text-embedding-3-large` | 3072 | ★★★★★ | ~40ms | $0.13/1M tokens | 高精度需求 |
| `BGE-M3` | 1024 | ★★★★★ | ~15ms | 免费（自部署） | 中文优先/私有化 |
| `Jina-embeddings-v3` | 1024 | ★★★★ | ~20ms | 免费（自部署） | 多语言场景 |
| `豆包 Embedding` | 2560 | ★★★★★ | ~25ms | ¥0.0005/千tokens | 国内低成本 |

生成 Embedding 的代码：

```python
from openai import AsyncOpenAI
import numpy as np

class EmbeddingService:
    """Embedding 生成服务"""
    
    def __init__(self, client: AsyncOpenAI, model: str = "text-embedding-3-small"):
        self.client = client
        self.model = model
    
    async def embed(self, text: str) -> list[float]:
        """生成单条文本的 Embedding"""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding
    
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成 Embedding（单次最多 2048 条）"""
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]
    
    @staticmethod
    def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """计算余弦相似度"""
        a, b = np.array(vec_a), np.array(vec_b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

> 💡 **Embedding 的成本可以忽略不计**——`text-embedding-3-small` 每百万 token 仅 $0.02，一个普通 Prompt 约 100 tokens，也就是 $0.000002/次。相比 LLM 调用的 $0.01-$0.10，Embedding 成本只有 LLM 的万分之一。

### 3.3 向量检索：用 pgvector / Redis VSS / Milvus 做相似度搜索

向量存储方案有三种主流选择，各有优劣：

| 方案 | 适用场景 | 缓存条目量 | 查询延迟 | 部署成本 |
|:---|:---|:---|:---|:---|
| **pgvector** | 已有 PG，缓存 < 100 万条 | < 1M | 5-20ms | 零（PG 扩展） |
| **Redis VSS** | 已有 Redis，需极低延迟 | < 50 万 | 1-5ms | 零（Redis 模块） |
| **Milvus** | 大规模，缓存 > 100 万条 | 10M+ | 5-10ms | 独立服务 |

**方案一：pgvector（推荐起步方案）**

```sql
-- 安装 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建语义缓存表
CREATE TABLE semantic_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_text TEXT NOT NULL,               -- 原始 Prompt
    prompt_embedding vector(1536) NOT NULL,  -- Prompt 向量
    response TEXT NOT NULL,                  -- LLM 回答
    model VARCHAR(50) NOT NULL,              -- 使用的模型
    hit_count INTEGER DEFAULT 0,             -- 命中次数
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
);

-- 创建 HNSW 索引（比 IVFFlat 更快更准）
CREATE INDEX idx_semantic_cache_embedding 
ON semantic_cache 
USING hnsw (prompt_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

```python
# pgvector 查询示例
from sqlalchemy import text

async def search_similar(db: AsyncSession, query_vec: list[float], 
                          model: str, threshold: float = 0.92) -> dict | None:
    """在 pgvector 中搜索最相似的缓存"""
    result = await db.execute(
        text("""
            SELECT prompt_text, response, 
                   1 - (prompt_embedding <=> :vec) AS similarity
            FROM semantic_cache
            WHERE model = :model
              AND expires_at > NOW()
              AND 1 - (prompt_embedding <=> :vec) > :threshold
            ORDER BY prompt_embedding <=> :vec
            LIMIT 1
        """),
        {"vec": str(query_vec), "model": model, "threshold": threshold},
    )
    row = result.fetchone()
    if row:
        return {"prompt": row.prompt_text, "response": row.response, 
                "similarity": row.similarity}
    return None
```

**方案二：Redis VSS（极低延迟场景）**

::: v-pre
```python
import redis.asyncio as redis
from redis.commands.search.query import Query
from redis.commands.search.field import VectorField, TextField

async def setup_redis_vss(r: redis.Redis):
    """创建 Redis 向量搜索索引"""
    try:
        await r.ft("idx:semantic_cache").create_index([
            TextField("prompt"),
            TextField("response"),
            TextField("model"),
            VectorField("embedding", "HNSW", {
                "TYPE": "FLOAT32",
                "DIM": 1536,
                "DISTANCE_METRIC": "COSINE",
            }),
        ])
    except Exception:
        pass  # 索引已存在

async def search_redis_vss(r: redis.Redis, query_vec: list[float], 
                            model: str, threshold: float = 0.92) -> dict | None:
    """在 Redis VSS 中搜索"""
    import numpy as np
    
    q = (Query(f"(@model:&#123;&#123;{model&#125;&#125;})=>[KNN 1 @embedding $vec AS score]")
         .return_fields("prompt", "response", "score")
         .dialect(2))
    
    result = await r.ft("idx:semantic_cache").search(
        q, query_params={"vec": np.array(query_vec, dtype=np.float32).tobytes()}
    )
    
    if result.docs:
        doc = result.docs[0]
        similarity = 1 - float(doc.score)  # Redis 返回距离，需转为相似度
        if similarity >= threshold:
            return {"prompt": doc.prompt, "response": doc.response,
                    "similarity": similarity}
    return None
```
:::

> 💡 **起步用 pgvector，后期按需迁移**——如果你的应用已经用了 PostgreSQL，pgvector 是零成本的最佳起步方案。100 万条缓存以内，pgvector + HNSW 索引的查询延迟可以稳定在 10ms 以内。
### 3.4 相似度阈值调优：精确率 vs 召回率的平衡

阈值设置是语义缓存最关键的参数——**设太高命中太少，设太低会返回错误答案**：

```
阈值对命中质量的影响：

  阈值 0.98 ─── 极严格，几乎只命中同义句改写
               命中率 ~15%  |  错误率 ~0.1%
               
  阈值 0.95 ─── 严格，命中近义表达
               命中率 ~30%  |  错误率 ~0.5%
               
  阈值 0.92 ─── 推荐值，平衡命中率和准确率 ✓
               命中率 ~45%  |  错误率 ~1.5%
               
  阈值 0.88 ─── 宽松，可能命中相关但不同的问题
               命中率 ~60%  |  错误率 ~5%
               
  阈值 0.85 ─── 过于宽松，错误率不可接受 ✗
               命中率 ~70%  |  错误率 ~12%
```

不同业务场景的推荐阈值：

| 场景 | 推荐阈值 | 理由 |
|:---|:---|:---|
| **客服/FAQ** | 0.90-0.93 | 答案标准化，容错空间大 |
| **技术问答** | 0.93-0.95 | 细节差异可能导致答案不同 |
| **代码生成** | 0.95-0.98 | 微小差异 = 完全不同的代码 |
| **创意写作** | 0.88-0.92 | 相似主题可复用风格和结构 |
| **医疗/法律** | 0.96-0.99 | 零容错，宁可 miss 不能错 |

如何科学地确定阈值——**用评测集做二分搜索**：

```python
async def evaluate_threshold(
    cache_entries: list[dict],    # 已有缓存条目
    test_queries: list[dict],     # 测试查询（含标准答案）
    embedding_service: EmbeddingService,
    thresholds: list[float] = [0.88, 0.90, 0.92, 0.94, 0.96],
) -> dict:
    """评估不同阈值下的命中率和准确率"""
    results = {}
    
    for threshold in thresholds:
        hits, correct_hits, total = 0, 0, len(test_queries)
        
        for query in test_queries:
            query_vec = await embedding_service.embed(query["prompt"])
            
            # 搜索最相似的缓存
            best_sim, best_response = 0, None
            for entry in cache_entries:
                sim = EmbeddingService.cosine_similarity(query_vec, entry["embedding"])
                if sim > best_sim:
                    best_sim, best_response = sim, entry["response"]
            
            if best_sim >= threshold:
                hits += 1
                # 判断缓存的回答是否适用于当前问题
                if is_answer_acceptable(best_response, query["expected"]):
                    correct_hits += 1
        
        results[threshold] = {
            "hit_rate": f"{hits / total * 100:.1f}%",
            "precision": f"{correct_hits / hits * 100:.1f}%" if hits > 0 else "N/A",
            "f1": compute_f1(hits, correct_hits, total),
        }
    
    return results

# 输出示例：
# threshold=0.92: hit_rate=45.2%, precision=97.1%, f1=0.62
# threshold=0.94: hit_rate=32.8%, precision=98.9%, f1=0.49
```

> 💡 **阈值不是一成不变的**——建议上线后持续监控"缓存命中但用户不满意"的比例。如果该比例超过 3%，适当提高阈值；如果低于 0.5%，可以适当降低阈值来提升命中率。
### 3.5 完整实现：语义缓存服务

把前面的 Embedding 生成、向量检索、阈值判断整合成一个完整的服务类：

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
import time

class SemanticCacheService:
    """语义缓存服务：基于 Embedding 相似度的智能缓存"""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        threshold: float = 0.92,
        default_ttl_hours: int = 24,
    ):
        self.embedding = embedding_service
        self.threshold = threshold
        self.default_ttl_hours = default_ttl_hours
    
    async def get(self, prompt: str, model: str, 
                  db: AsyncSession) -> CacheResult:
        """查询语义缓存"""
        # 1. 生成查询向量
        query_vec = await self.embedding.embed(prompt)
        
        # 2. 在 pgvector 中搜索
        result = await db.execute(
            text("""
                SELECT id, prompt_text, response, model,
                       1 - (prompt_embedding <=> :vec) AS similarity,
                       created_at
                FROM semantic_cache
                WHERE model = :model
                  AND expires_at > NOW()
                ORDER BY prompt_embedding <=> :vec
                LIMIT 1
            """),
            {"vec": str(query_vec), "model": model},
        )
        row = result.fetchone()
        
        # 3. 判断是否超过阈值
        if row and row.similarity >= self.threshold:
            # 更新命中计数
            await db.execute(
                text("UPDATE semantic_cache SET hit_count = hit_count + 1 WHERE id = :id"),
                {"id": row.id},
            )
            await db.commit()
            
            return CacheResult(
                hit=True,
                content=row.response,
                cached_at=row.created_at.timestamp(),
                model=row.model,
            )
        
        return CacheResult(hit=False)
    
    async def set(self, prompt: str, model: str, 
                  response: str, db: AsyncSession):
        """写入语义缓存"""
        # 生成 Prompt 的 Embedding
        prompt_vec = await self.embedding.embed(prompt)
        
        await db.execute(
            text("""
                INSERT INTO semantic_cache 
                (prompt_text, prompt_embedding, response, model, expires_at)
                VALUES (:prompt, :embedding, :response, :model, 
                        NOW() + :ttl * INTERVAL '1 hour')
            """),
            {
                "prompt": prompt,
                "embedding": str(prompt_vec),
                "response": response,
                "model": model,
                "ttl": self.default_ttl_hours,
            },
        )
        await db.commit()
```

在 FastAPI 中集成语义缓存：

```python
@chat_router.post("/completions")
async def chat_with_semantic_cache(
    request: ChatRequest,
    exact_cache: ExactCacheService = Depends(get_exact_cache),
    semantic_cache: SemanticCacheService = Depends(get_semantic_cache),
    db: AsyncSession = Depends(get_db),
    llm: AsyncOpenAI = Depends(get_llm),
):
    messages = [{"role": "user", "content": request.message}]
    
    # 1. 先查精确缓存（快，< 5ms）
    cached = await exact_cache.get(messages, request.model)
    if cached.hit:
        return {"content": cached.content, "cache": "exact"}
    
    # 2. 再查语义缓存（稍慢，< 50ms）
    cached = await semantic_cache.get(request.message, request.model, db)
    if cached.hit:
        return {"content": cached.content, "cache": "semantic"}
    
    # 3. 都没命中，调用 LLM
    response = await llm.chat.completions.create(
        model=request.model, messages=messages, temperature=0,
    )
    content = response.choices[0].message.content
    
    # 4. 写入两级缓存
    await exact_cache.set(messages, request.model, content)
    await semantic_cache.set(request.message, request.model, content, db)
    
    return {"content": content, "cache": "miss"}
```

> 💡 **精确缓存和语义缓存不是二选一**——先查精确缓存（零 Embedding 成本，< 5ms），miss 后再查语义缓存（需要计算 Embedding，< 50ms）。两者串联使用，总命中率 = 精确命中 + 语义增量命中。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **核心原理** | Prompt → Embedding 向量 → 余弦相似度搜索 |
| **Embedding 模型** | text-embedding-3-small 通用首选，BGE-M3 中文最佳 |
| **向量存储** | pgvector 起步，Redis VSS 极速，Milvus 大规模 |
| **阈值选择** | 0.92 通用推荐，按场景在 0.88-0.98 间调整 |
| **串联策略** | 精确缓存（L2）+ 语义缓存（L3）叠加使用 |

---

## 4. 多级缓存策略：L1 / L2 / L3 三层设计

### 4.1 三层架构：本地内存 → Redis → 语义缓存

为什么要分三层？因为每层的**速度和命中能力不同**：

```
多级缓存的核心逻辑——用速度换命中率：

  ┌─────────┬──────────┬──────────┬──────────────────────┐
  │  层级    │  存储     │  延迟     │  匹配方式             │
  ├─────────┼──────────┼──────────┼──────────────────────┤
  │  L1     │  本地内存  │  < 0.1ms │  精确 Hash（热点）     │
  │  L2     │  Redis    │  < 5ms   │  精确 Hash（全量）     │
  │  L3     │  pgvector │  < 50ms  │  语义相似度（兜底）     │
  │  原始    │  LLM API  │  3-15s   │  —（缓存未命中）       │
  └─────────┴──────────┴──────────┴──────────────────────┘
```

```
请求的缓存查询路径：

  请求进入
    │
    ▼
  ① L1 本地内存 ──── 命中？──→ YES → 返回（< 0.1ms）
    │ NO                       命中率 ~15%
    ▼
  ② L2 Redis ──────── 命中？──→ YES → 返回 + 写回 L1（< 5ms）
    │ NO                       命中率 ~10%
    ▼
  ③ L3 pgvector ──── 命中？──→ YES → 返回 + 写回 L1 + L2（< 50ms）
    │ NO                       命中率 ~25%
    ▼
  ④ 调用 LLM API ─── 返回 + 写入 L1 + L2 + L3（3-15s）

  总命中率 ≈ 15% + 10% + 25% = 50%
  （各层命中率随业务场景差异较大）
```

### 4.2 L1 本地缓存：LRU + TTL 的进程内缓存

L1 层的目标是**拦截最热的请求**——那些在短时间内被频繁重复的 Prompt。

```python
import time
from collections import OrderedDict
from threading import Lock

class L1Cache:
    """L1 本地内存缓存：LRU 淘汰 + TTL 过期"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size        # 最多缓存 1000 条
        self.default_ttl = default_ttl  # 默认 5 分钟过期
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._lock = Lock()
        
        # 统计
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> str | None:
        """查询缓存（线程安全）"""
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None
            
            entry = self._cache[key]
            
            # 检查是否过期
            if time.time() > entry["expires_at"]:
                del self._cache[key]
                self.misses += 1
                return None
            
            # LRU：移到末尾（最近访问）
            self._cache.move_to_end(key)
            self.hits += 1
            return entry["content"]
    
    def set(self, key: str, content: str, ttl: int | None = None):
        """写入缓存"""
        with self._lock:
            # 如果已存在，先删除
            if key in self._cache:
                del self._cache[key]
            
            # 如果已满，淘汰最久未访问的（LRU）
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            
            self._cache[key] = {
                "content": content,
                "expires_at": time.time() + (ttl or self.default_ttl),
            }
    
    @property
    def hit_rate(self) -> str:
        total = self.hits + self.misses
        return f"{self.hits / total * 100:.1f}%" if total > 0 else "N/A"

# 全局单例（每个 Worker 进程一个）
l1_cache = L1Cache(max_size=1000, default_ttl=300)
```

> 💡 **L1 缓存每个 Worker 进程独立**——不同 Worker 的 L1 不共享。这意味着 4 个 Worker 会有 4 份独立的 L1 缓存。这是可接受的，因为热点请求会被每个 Worker 各自缓存，而且 L1 的目标就是"极速"，共享反而增加网络延迟。

### 4.3 L2 分布式缓存：Redis 精确匹配层

L2 层就是第 2 章实现的 `ExactCacheService`，这里补充多级缓存场景下的**关键配置**：

```python
# L2 层的 Redis 配置要点
L2_CONFIG = {
    "ttl": 7200,              # 2 小时（比 L1 长得多）
    "max_memory": "512mb",    # Redis 最大内存
    "eviction": "allkeys-lru", # 内存满时淘汰策略
    "key_prefix": "llm:l2",   # 与其他 Redis 数据隔离
}
```

L2 层的三个核心职责：

```
L2 Redis 在多级缓存中的角色：

  ① 跨 Worker 共享 ─── 所有 Worker 进程共享同一个 Redis
                       一个 Worker 写入，其他 Worker 都能命中
  
  ② 持久化比 L1 更久 ── L1 是 5 分钟，L2 是 2 小时
                       Worker 重启后 L1 清空，但 L2 还在
  
  ③ 写回 L1 ─────────── L2 命中时，自动写回 L1
                       下次同一个 Worker 收到相同请求，L1 直接命中
```

**写回策略的代码：**

```python
async def get_from_l2_with_writeback(
    key: str, l1: L1Cache, l2: ExactCacheService, messages: list[dict], model: str
) -> CacheResult:
    """L2 查询 + 写回 L1"""
    cached = await l2.get(messages, model)
    if cached.hit:
        # 写回 L1（让下次同 Worker 请求更快）
        l1.set(key, cached.content, ttl=300)
    return cached
```

### 4.4 L3 语义缓存：向量相似度兜底层

L3 层就是第 3 章实现的 `SemanticCacheService`，作为最后的兜底：

```
L3 的定位——"宁可多花 50ms，也不想花 $0.03"：

  L1 miss + L2 miss 之后：
    │
    ├── 不用 L3：直接调用 LLM（$0.03，5-15 秒）
    │
    └── 用 L3：花 50ms 做语义搜索
              │
              ├── HIT（25% 概率）→ 省了 $0.03 + 14.95 秒
              │
              └── MISS          → 只多花了 50ms，可忽略
  
  期望收益：0.25 × $0.03 = $0.0075/次 > Embedding 成本 $0.000002/次
  → ROI 超过 3000 倍 ✓
```

L3 命中后的写回策略：

```python
async def get_from_l3_with_writeback(
    prompt: str, model: str, key: str,
    l1: L1Cache, l2: ExactCacheService, l3: SemanticCacheService,
    messages: list[dict], db: AsyncSession,
) -> CacheResult:
    """L3 查询 + 写回 L1 和 L2"""
    cached = await l3.get(prompt, model, db)
    if cached.hit:
        # 写回 L1 和 L2（下次精确匹配就能命中）
        l1.set(key, cached.content, ttl=300)
        await l2.set(messages, model, cached.content, ttl=7200)
    return cached
```

> 💡 **L3 命中后写回 L1 + L2 是关键优化**——语义缓存命中说明这个 Prompt 的答案是有效的。把它同时写入精确缓存，下次完全相同的请求就不需要再做 Embedding 计算了。
### 4.5 统一缓存管理器：串联三层的完整实现

把三层缓存封装成一个统一的接口——调用者不需要关心缓存层级细节：

```python
class CacheManager:
    """多级缓存管理器：串联 L1 → L2 → L3"""
    
    def __init__(
        self,
        l1: L1Cache,
        l2: ExactCacheService,
        l3: SemanticCacheService,
        normalizer: PromptNormalizer,
    ):
        self.l1 = l1
        self.l2 = l2
        self.l3 = l3
        self.normalizer = normalizer
        
        # 各层统计
        self.stats = {"l1_hits": 0, "l2_hits": 0, "l3_hits": 0, "misses": 0}
    
    async def get(
        self, messages: list[dict], model: str, db: AsyncSession
    ) -> CacheResult:
        """三级缓存查询：L1 → L2 → L3"""
        cache_key = self.normalizer.compute_cache_key(messages, model)
        prompt = messages[-1]["content"]  # 取最后一条用户消息
        
        # ── L1：本地内存 ──
        content = self.l1.get(cache_key)
        if content:
            self.stats["l1_hits"] += 1
            return CacheResult(hit=True, content=content)
        
        # ── L2：Redis 精确匹配 ──
        cached = await self.l2.get(messages, model)
        if cached.hit:
            self.l1.set(cache_key, cached.content)  # 写回 L1
            self.stats["l2_hits"] += 1
            return cached
        
        # ── L3：语义相似度匹配 ──
        cached = await self.l3.get(prompt, model, db)
        if cached.hit:
            self.l1.set(cache_key, cached.content)  # 写回 L1
            await self.l2.set(messages, model, cached.content)  # 写回 L2
            self.stats["l3_hits"] += 1
            return cached
        
        self.stats["misses"] += 1
        return CacheResult(hit=False)
    
    async def set(
        self, messages: list[dict], model: str, 
        content: str, db: AsyncSession
    ):
        """写入所有三层缓存"""
        cache_key = self.normalizer.compute_cache_key(messages, model)
        prompt = messages[-1]["content"]
        
        self.l1.set(cache_key, content)
        await self.l2.set(messages, model, content)
        await self.l3.set(prompt, model, content, db)
    
    def get_stats(self) -> dict:
        """获取各层命中率统计"""
        total = sum(self.stats.values())
        if total == 0:
            return self.stats
        return {
            **self.stats,
            "total_requests": total,
            "total_hit_rate": f"{(total - self.stats['misses']) / total * 100:.1f}%",
            "l1_rate": f"{self.stats['l1_hits'] / total * 100:.1f}%",
            "l2_rate": f"{self.stats['l2_hits'] / total * 100:.1f}%",
            "l3_rate": f"{self.stats['l3_hits'] / total * 100:.1f}%",
        }
```

使用方式极其简洁：

```python
@chat_router.post("/completions")
async def chat(
    request: ChatRequest,
    cache: CacheManager = Depends(get_cache_manager),
    db: AsyncSession = Depends(get_db),
    llm: AsyncOpenAI = Depends(get_llm),
):
    messages = [{"role": "user", "content": request.message}]
    
    # 一行代码查三级缓存
    cached = await cache.get(messages, request.model, db)
    if cached.hit:
        return {"content": cached.content, "cached": True}
    
    # 缓存未命中，调用 LLM
    response = await llm.chat.completions.create(
        model=request.model, messages=messages, temperature=0,
    )
    content = response.choices[0].message.content
    
    # 一行代码写入三级缓存
    await cache.set(messages, request.model, content, db)
    
    return {"content": content, "cached": False}
```

> 💡 **CacheManager 是对外的唯一接口**——业务代码只需要调用 `cache.get()` 和 `cache.set()`，完全不需要知道底层有几层缓存、用了什么存储。后续新增缓存层或替换存储引擎，业务代码零改动。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **L1 本地内存** | LRU + TTL，< 0.1ms，拦截同进程热点 |
| **L2 Redis** | 精确 Hash，< 5ms，跨 Worker 共享 |
| **L3 pgvector** | 语义搜索，< 50ms，兜底捕捉相似请求 |
| **写回策略** | 低层命中自动写回高层，加速后续请求 |
| **CacheManager** | 统一接口，一行代码查三级缓存 |

---

## 5. 缓存 Key 设计与 Prompt 规范化

### 5.1 Prompt 规范化：去噪 → 排序 → 模板化

第 2 章介绍了基础的规范化（空格、标点、大小写）。在生产环境中，还需要处理更复杂的情况：

**问题一：System Prompt 的干扰**

```
同一个问题，不同用户可能带不同的 System Prompt：

  用户 A：
    system: "你是一个 Python 专家"
    user: "什么是 GIL？"
  
  用户 B：
    system: "你是一个编程助手，请用中文回答"
    user: "什么是 GIL？"
  
  → 如果把 system prompt 也纳入 Hash，这两个就是不同的缓存 Key
  → 但它们的答案其实高度相似
```

解决方案：**分层哈希**——System Prompt 和 User Prompt 分开处理：

```python
class AdvancedNormalizer:
    """进阶版规范化器：支持 System Prompt 分离"""
    
    def compute_cache_key(
        self, messages: list[dict], model: str,
        include_system: bool = True,
        **kwargs
    ) -> str:
        # 分离 system 和 user/assistant 消息
        system_msgs = [m for m in messages if m["role"] == "system"]
        other_msgs = [m for m in messages if m["role"] != "system"]
        
        # User 消息始终参与 Hash
        user_part = self._normalize_messages(other_msgs)
        
        if include_system and system_msgs:
            # System Prompt 参与 Hash（严格模式）
            system_part = self._normalize_messages(system_msgs)
            content = f"{model}:{system_part}:{user_part}"
        else:
            # 忽略 System Prompt（宽松模式，提高命中率）
            content = f"{model}:{user_part}"
        
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _normalize_messages(self, messages: list[dict]) -> str:
        normalized = []
        for msg in messages:
            text = PromptNormalizer.normalize(msg["content"])
            normalized.append(f"{msg['role']}:{text}")
        return "|".join(normalized)
```

**问题二：Prompt 模板中的变量**

```
模板化的 Prompt 只是变量不同：

  "请将以下文本翻译成英文：{text}"
  
  → text="你好世界"  ← 缓存价值高，可能重复
  → text="一段很长的独特文章..."  ← 缓存价值低，几乎不会重复
```

策略：**对模板类 Prompt，只用模板 ID + 变量 Hash 做缓存 Key**：

```python
def compute_template_cache_key(
    template_id: str, variables: dict, model: str
) -> str:
    """模板化 Prompt 的缓存 Key"""
    # 变量按 key 排序后序列化
    sorted_vars = json.dumps(variables, sort_keys=True, ensure_ascii=False)
    content = f"{model}:{template_id}:{sorted_vars}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]

# 使用示例
key = compute_template_cache_key(
    template_id="translate_v2",
    variables={"text": "你好世界", "target_lang": "en"},
    model="gpt-4o",
)
```

### 5.2 缓存 Key 组成：model + params + prompt_hash

一个完整的缓存 Key 应该包含**所有影响 LLM 输出的因素**：

```
缓存 Key 的完整组成：

  llm:l2:{model}:{params_hash}:{prompt_hash}
    │      │        │              │
    │      │        │              └── 规范化后的 Prompt 内容 Hash
    │      │        └── temperature + max_tokens + top_p 等参数的 Hash
    │      └── gpt-4o / claude-3-5-sonnet / ...
    └── 前缀，区分不同用途的缓存

  示例：llm:l2:gpt-4o:a3f2:7b1e9c4d
```

完整的 Key 构建器：

```python
class CacheKeyBuilder:
    """缓存 Key 构建器：处理各种复杂场景"""
    
    # 影响输出的参数白名单
    PARAMS_WHITELIST = ["temperature", "max_tokens", "top_p", 
                         "frequency_penalty", "presence_penalty"]
    
    @classmethod
    def build(
        cls,
        messages: list[dict],
        model: str,
        prefix: str = "llm:l2",
        include_system: bool = True,
        **kwargs
    ) -> str:
        # 1. 模型名称
        model_part = model.replace("/", "-")
        
        # 2. 参数哈希（只取影响输出的参数）
        params = {k: kwargs[k] for k in cls.PARAMS_WHITELIST if k in kwargs}
        params_hash = hashlib.md5(
            json.dumps(params, sort_keys=True).encode()
        ).hexdigest()[:4]
        
        # 3. Prompt 哈希
        normalizer = AdvancedNormalizer()
        prompt_hash = normalizer.compute_cache_key(
            messages, model, include_system=include_system
        )
        
        return f"{prefix}:{model_part}:{params_hash}:{prompt_hash}"

# 使用示例
key = CacheKeyBuilder.build(
    messages=[
        {"role": "system", "content": "你是一个 Python 专家"},
        {"role": "user", "content": "什么是 GIL？"},
    ],
    model="gpt-4o",
    temperature=0,
    max_tokens=2000,
)
# → "llm:l2:gpt-4o:b2a1:7c3e9f8d"
```

> 💡 **不要把 `response_format` 忽略**——如果你用了 JSON Mode（`response_format={"type": "json_object"}`），同一个 Prompt 的输出格式完全不同。记得把 `response_format` 也纳入参数哈希。

### 5.3 多轮对话的缓存策略：上下文窗口变化怎么办

多轮对话是缓存最棘手的场景——**每一轮对话的上下文都不同**：

```
多轮对话的缓存挑战：

  第 1 轮：[user: "什么是 GIL？"]              → 可缓存 ✓
  第 2 轮：[user: "什么是 GIL？", assistant: "...", user: "举个例子"]  → 上下文变了
  第 3 轮：[... 前面所有消息 ..., user: "还有其他影响吗？"]  → 又变了
  
  每轮的 messages 数组都不同 → 每轮的缓存 Key 都不同
  → 命中率极低
```

三种实用策略：

**策略一：只缓存最后一轮（最简单）**

```python
def compute_multiturn_key_last_only(messages: list[dict], model: str) -> str:
    """只用最后一条 user 消息做缓存 Key"""
    last_user_msg = [m for m in messages if m["role"] == "user"][-1]
    content = f"{model}:{PromptNormalizer.normalize(last_user_msg['content'])}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]
```

- ✅ 命中率最高（不同对话中的相同问题能命中）
- ❌ 可能返回脱离上下文的答案（"举个例子"缓存了但不知道什么的例子）

**策略二：最后 N 轮上下文（推荐）**

```python
def compute_multiturn_key_last_n(
    messages: list[dict], model: str, n: int = 3
) -> str:
    """用最后 N 轮消息做缓存 Key"""
    # 取最后 N 轮（每轮 = 1 user + 1 assistant）
    recent = messages[-(n * 2):] if len(messages) > n * 2 else messages
    
    normalized = []
    for msg in recent:
        text = PromptNormalizer.normalize(msg["content"])
        normalized.append(f"{msg['role']}:{text}")
    
    content = f"{model}:{'|'.join(normalized)}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]

# 只用最后 3 轮做 Key → 前面的历史消息变化不影响缓存
```

- ✅ 平衡命中率和上下文准确性
- ✅ 推荐 N=2 或 N=3

**策略三：上下文摘要缓存（高级）**

```python
async def compute_multiturn_key_with_summary(
    messages: list[dict], model: str, llm: AsyncOpenAI
) -> str:
    """用 LLM 生成对话摘要做缓存 Key（适合长对话）"""
    if len(messages) <= 4:
        # 短对话直接用全量消息
        return compute_multiturn_key_last_n(messages, model, n=10)
    
    # 长对话：提取核心意图
    summary_prompt = f"用一句话总结用户当前的问题意图：{messages[-1]['content']}"
    summary = await get_intent_summary(llm, messages, summary_prompt)
    
    content = f"{model}:{PromptNormalizer.normalize(summary)}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]
```

> 💡 **多轮对话优先用语义缓存**——对于多轮场景，精确匹配的命中率非常低。但语义缓存可以识别"不同对话中问的类似问题"，命中率提升显著。建议多轮场景把 L3 阈值适当放宽到 0.90。
### 5.4 带工具调用的缓存：Function Calling 场景

当 Prompt 包含 `tools` 定义时，缓存变得更加复杂——**同一个问题，有无工具定义、工具定义不同，LLM 的输出都会不同**：

```
Function Calling 的缓存挑战：

  场景 1：无工具
    user: "北京今天天气怎么样？"
    → LLM 回答: "我无法获取实时天气信息..."

  场景 2：有天气工具
    user: "北京今天天气怎么样？"
    tools: [get_weather]
    → LLM 回答: tool_call(get_weather, {"city": "北京"})

  → 同一个问题，输出完全不同！
```

解决方案：**tools 定义也要参与缓存 Key 计算**：

```python
def compute_fc_cache_key(
    messages: list[dict], model: str,
    tools: list[dict] | None = None, **kwargs
) -> str:
    """Function Calling 场景的缓存 Key"""
    # 1. 常规消息哈希
    msg_hash = PromptNormalizer().compute_cache_key(messages, model)
    
    # 2. 工具定义哈希
    if tools:
        # 只取工具名称和参数 schema（忽略描述文本的微调）
        tool_signatures = []
        for tool in sorted(tools, key=lambda t: t["function"]["name"]):
            tool_signatures.append({
                "name": tool["function"]["name"],
                "parameters": tool["function"].get("parameters", {}),
            })
        tools_hash = hashlib.md5(
            json.dumps(tool_signatures, sort_keys=True).encode()
        ).hexdigest()[:6]
    else:
        tools_hash = "no_tools"
    
    return f"llm:fc:{model}:{tools_hash}:{msg_hash}"
```

一个进阶优化——**拆分工具调用和工具结果的缓存**：

```
拆分缓存的两个层次：

  ① LLM 决策缓存：缓存 LLM 决定调用哪个工具 + 什么参数
     Key: prompt + tools → Value: tool_call(name, args)
     命中率高（同一类问题通常调用同一个工具）

  ② 工具结果缓存：缓存工具的执行结果
     Key: tool_name + args → Value: tool_result
     命中率取决于工具（天气=低，汇率=中，知识库=高）
```

```python
class FCCacheService:
    """Function Calling 分层缓存"""
    
    async def get_tool_decision(self, messages, model, tools) -> dict | None:
        """查询 LLM 的工具调用决策缓存"""
        key = compute_fc_cache_key(messages, model, tools)
        return await self.redis.get(f"fc:decision:{key}")
    
    async def get_tool_result(self, tool_name: str, args: dict) -> str | None:
        """查询工具执行结果缓存"""
        args_hash = hashlib.md5(
            json.dumps(args, sort_keys=True).encode()
        ).hexdigest()[:12]
        return await self.redis.get(f"fc:result:{tool_name}:{args_hash}")
    
    async def set_tool_result(self, tool_name: str, args: dict, 
                               result: str, ttl: int = 300):
        """缓存工具执行结果（TTL 按工具类型设置）"""
        args_hash = hashlib.md5(
            json.dumps(args, sort_keys=True).encode()
        ).hexdigest()[:12]
        await self.redis.setex(f"fc:result:{tool_name}:{args_hash}", ttl, result)
```

> 💡 **工具结果的 TTL 要按工具类型设置**——天气 API 结果缓存 5 分钟，知识库检索结果缓存 2 小时，计算类工具（无副作用）可以缓存 24 小时。不同工具的时效性差异巨大。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **System Prompt 分离** | 可选是否纳入 Hash，宽松模式提高命中率 |
| **模板变量哈希** | 模板 ID + 变量 Hash，比全文 Hash 命中率高 |
| **Key 完整组成** | prefix:model:params_hash:prompt_hash |
| **多轮对话** | 推荐最后 N 轮策略（N=2-3） |
| **Function Calling** | tools 签名 + 工具结果分层缓存 |

---

## 6. 缓存失效与更新策略

### 6.1 TTL 策略：不同场景的过期时间设计

缓存不是"存了就不管了"——**过期的缓存比没有缓存更危险**（返回过时信息）。

不同类型的 LLM 响应，时效性差异巨大：

| 缓存类型 | 推荐 TTL | 理由 |
|:---|:---|:---|
| **知识类回答** | 24-72h | "Python GIL 是什么"短期内不会变 |
| **翻译结果** | 7 天 | 翻译质量稳定，长期有效 |
| **代码生成** | 4-12h | 最佳实践可能演变 |
| **时效性信息** | 5-30min | 天气、股价、新闻相关 |
| **创意内容** | 1-2h | 不同用户可能想要不同风格 |
| **RAG 检索结果** | 1-4h | 知识库可能更新文档 |
| **工具调用决策** | 2-4h | 工具列表变化不频繁 |

实现**动态 TTL**——根据 Prompt 特征自动选择过期时间：

```python
import re

class DynamicTTL:
    """根据 Prompt 内容动态设置 TTL"""
    
    # 时效敏感关键词
    TIME_SENSITIVE = ["今天", "现在", "最新", "当前", "实时",
                      "today", "current", "latest", "now"]
    
    @classmethod
    def compute(cls, prompt: str, default_ttl: int = 7200) -> int:
        prompt_lower = prompt.lower()
        
        # 1. 时效性内容 → 短 TTL
        if any(kw in prompt_lower for kw in cls.TIME_SENSITIVE):
            return 300  # 5 分钟
        
        # 2. 代码生成 → 中等 TTL
        if any(kw in prompt_lower for kw in ["代码", "code", "实现", "implement"]):
            return 14400  # 4 小时
        
        # 3. 翻译 → 长 TTL
        if any(kw in prompt_lower for kw in ["翻译", "translate", "转换"]):
            return 604800  # 7 天
        
        # 4. 知识性问答 → 较长 TTL
        if any(kw in prompt_lower for kw in ["是什么", "什么是", "解释", "原理"]):
            return 86400  # 24 小时
        
        return default_ttl

# 使用示例
ttl = DynamicTTL.compute("今天北京的天气怎么样？")  # → 300 秒
ttl = DynamicTTL.compute("什么是 Python 的装饰器？")  # → 86400 秒
```

### 6.2 主动失效：Prompt 模板更新时清缓存

Prompt 模板一旦修改，旧缓存就可能返回不匹配的结果。需要**主动清除**相关缓存：

```
主动失效的触发场景：

  ① Prompt 模板修改 ─── 模板内容变了，旧答案不再适用
  ② 知识库更新 ──────── RAG 系统的文档变了，检索结果变了
  ③ 业务规则变更 ────── 价格/政策/功能更新，旧回答可能错误
```

实现方案——**基于模板版本号的缓存管理**：

```python
class TemplateVersionManager:
    """Prompt 模板版本管理 + 缓存联动失效"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def update_template(self, template_id: str, new_content: str):
        """更新模板时自动清除相关缓存"""
        # 1. 递增版本号
        version = await self.redis.incr(f"template:version:{template_id}")
        
        # 2. 保存新模板内容
        await self.redis.hset(f"template:{template_id}", mapping={
            "content": new_content,
            "version": version,
            "updated_at": time.time(),
        })
        
        # 3. 清除该模板的所有缓存（按前缀扫描删除）
        await self._invalidate_by_prefix(f"llm:*:template:{template_id}:*")
        
        return version
    
    async def _invalidate_by_prefix(self, pattern: str):
        """按前缀批量清除缓存"""
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        return deleted

# 使用示例：运营同学修改了翻译模板
manager = TemplateVersionManager(redis_client)
await manager.update_template("translate_v2", "请将以下文本翻译成{lang}，保持原有格式...")
# → 自动清除所有 translate_v2 的缓存，新请求会使用新模板
```

> 💡 **不要用 `KEYS` 命令做批量删除**——`KEYS` 会阻塞 Redis 主线程。生产环境必须用 `SCAN` 分批扫描。上面的代码已经用了 `SCAN`，每次只处理 100 个 key。

### 6.3 版本化缓存：模型升级后旧缓存怎么处理

当你把模型从 GPT-4o 升级到 GPT-4.1，或者 OpenAI 默默更新了模型版本，旧缓存的回答质量可能不如新模型。怎么办？

```
版本化缓存的策略：

  方案 A：一刀切清除（简单粗暴）
    模型升级 → 清除该模型的所有缓存 → 重新积累
    缺点：升级后短时间内命中率归零

  方案 B：版本号隔离（推荐）✓
    缓存 Key 带模型版本号 → 新旧版本共存
    旧版本自然过期淘汰 → 平滑过渡
```

```python
class VersionedCacheKey:
    """带版本号的缓存 Key"""
    
    # 模型版本映射（手动维护）
    MODEL_VERSIONS = {
        "gpt-4o": "2025-08-06",       # OpenAI 模型快照日期
        "gpt-4o-mini": "2025-07-18",
        "claude-3-5-sonnet": "20241022",
    }
    
    @classmethod
    def build(cls, messages: list[dict], model: str, **kwargs) -> str:
        version = cls.MODEL_VERSIONS.get(model, "latest")
        base_key = CacheKeyBuilder.build(messages, model, **kwargs)
        return f"{base_key}:v{version}"
    
    @classmethod
    def update_model_version(cls, model: str, new_version: str):
        """模型升级时更新版本号"""
        cls.MODEL_VERSIONS[model] = new_version
        # 旧版本的缓存不删除，自然过期即可

# key = "llm:l2:gpt-4o:b2a1:7c3e:v2025-08-06"
# 模型升级后新 key = "llm:l2:gpt-4o:b2a1:7c3e:v2025-11-20"
# → 旧缓存不影响新请求，自然过期
```

### 6.4 缓存预热：高频问题提前缓存

缓存预热是指**系统启动或缓存失效后，主动将高频请求的结果提前写入缓存**，避免冷启动期间大量请求直接打到 LLM。

```python
class CacheWarmer:
    """缓存预热器"""
    
    def __init__(self, cache: CacheManager, llm: AsyncOpenAI):
        self.cache = cache
        self.llm = llm
    
    async def warm_from_history(self, db: AsyncSession, top_n: int = 200):
        """从历史高频问题预热缓存"""
        # 查询最近 7 天命中率最高的缓存条目
        result = await db.execute(text("""
            SELECT prompt_text, model, response
            FROM semantic_cache
            WHERE created_at > NOW() - INTERVAL '7 days'
            ORDER BY hit_count DESC
            LIMIT :n
        """), {"n": top_n})
        
        count = 0
        for row in result.fetchall():
            messages = [{"role": "user", "content": row.prompt_text}]
            await self.cache.set(messages, row.model, row.response, db)
            count += 1
        
        return count
    
    async def warm_from_faq(self, faq_list: list[dict]):
        """从 FAQ 列表预热（适合客服场景）"""
        for item in faq_list:
            messages = [{"role": "user", "content": item["question"]}]
            # 直接用预设答案，不调用 LLM
            await self.cache.set(
                messages, "gpt-4o", item["answer"], db=None
            )
```

预热的触发时机：

```
缓存预热的四个时机：

  ① 系统启动 ──── 服务重启后 L1 全空，预热 Top 200 问题
  ② 定时任务 ──── 每天凌晨刷新即将过期的高频缓存
  ③ 模型升级 ──── 新版本上线后，用新模型重新生成高频答案
  ④ 大促/活动前 ── 提前预热活动相关的常见问题
```

> 💡 **预热不要一次性调用太多 LLM**——200 条预热如果同时发请求会触发限流。建议用 `asyncio.Semaphore` 限制并发数为 5-10，或者用 Celery 任务队列控制速率。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **动态 TTL** | 根据 Prompt 内容自动选择过期时间 |
| **主动失效** | 模板更新时用 SCAN 批量清除相关缓存 |
| **版本化 Key** | Key 带模型版本号，新旧版本平滑过渡 |
| **缓存预热** | 高频问题提前灌入缓存，避免冷启动 |

---

## 7. 生产环境实战：监控、容量与踩坑

### 7.1 缓存命中率监控与报警

缓存上线后，**命中率是最核心的指标**——它直接决定了成本节省了多少。

```python
from prometheus_client import Counter, Histogram, Gauge

# ── Prometheus 指标定义 ──
cache_requests = Counter(
    "llm_cache_requests_total", 
    "缓存请求总数",
    ["layer", "result"]  # layer=l1/l2/l3, result=hit/miss
)

cache_latency = Histogram(
    "llm_cache_latency_seconds",
    "缓存查询延迟",
    ["layer"],
    buckets=[0.0001, 0.001, 0.005, 0.01, 0.05, 0.1]
)

cache_hit_rate = Gauge(
    "llm_cache_hit_rate",
    "缓存命中率（最近 5 分钟）",
    ["layer"]
)

# ── 在 CacheManager 中埋点 ──
class MonitoredCacheManager(CacheManager):
    
    async def get(self, messages, model, db) -> CacheResult:
        # L1
        with cache_latency.labels(layer="l1").time():
            content = self.l1.get(cache_key)
        if content:
            cache_requests.labels(layer="l1", result="hit").inc()
            return CacheResult(hit=True, content=content)
        cache_requests.labels(layer="l1", result="miss").inc()
        
        # L2
        with cache_latency.labels(layer="l2").time():
            cached = await self.l2.get(messages, model)
        if cached.hit:
            cache_requests.labels(layer="l2", result="hit").inc()
            return cached
        cache_requests.labels(layer="l2", result="miss").inc()
        
        # L3 ... 同理
```

关键报警规则：

```
报警规则设计：

  ① 命中率跌破阈值
     条件：总命中率 < 30%（持续 10 分钟）
     原因：可能缓存被清空、Redis 故障、流量模式变化
     动作：通知值班 + 检查 Redis 状态

  ② 缓存延迟异常
     条件：L2 P99 > 50ms 或 L3 P99 > 200ms
     原因：Redis 慢查询、pgvector 索引失效
     动作：检查慢查询日志

  ③ 缓存内存告警
     条件：Redis 内存使用率 > 80%
     原因：缓存条目过多、TTL 设置过长
     动作：清理过期 Key、调整 TTL
```

### 7.2 内存容量规划：缓存要多大才够

缓存内存的计算公式：

```
内存估算公式：

  单条缓存大小 ≈ Key(100B) + Prompt(500B) + Response(2KB) + 元数据(200B)
               ≈ 3KB

  L2 Redis 内存需求：
    日均请求量 × (1 - L1命中率) × 缓存条目留存率
    = 100,000 × 0.85 × 0.3
    = 25,500 条
    × 3KB/条
    ≈ 75MB

  L3 pgvector 内存需求：
    缓存条目数 × (向量维度 × 4B + 原始数据)
    = 25,500 × (1536 × 4B + 3KB)
    = 25,500 × 9.1KB
    ≈ 230MB
```

不同规模的参考配置：

| 规模 | 日请求量 | L1 大小 | L2 Redis | L3 pgvector | 月成本 |
|:---|:---|:---|:---|:---|:---|
| **小型** | 1 万 | 200 条 / 1MB | 64MB | 100MB | ~$0 |
| **中型** | 10 万 | 1000 条 / 5MB | 256MB | 500MB | ~$20 |
| **大型** | 100 万 | 5000 条 / 25MB | 2GB | 5GB | ~$100 |
| **超大** | 1000 万 | 10000 条 / 50MB | 8GB | 20GB | ~$300 |

> 💡 **缓存的内存成本远低于 LLM 调用成本**——中型应用月缓存成本约 $20，但能节省 55% 的 LLM 费用（$1650/月）。投入产出比超过 80 倍。

### 7.3 缓存穿透 / 雪崩 / 击穿：AI 场景的三大风险

这三个经典缓存问题在 AI 场景中有不同的表现和解法：

**穿透：大量不存在的 Prompt 绕过缓存**

```
AI 场景的穿透特点：

  传统 Web：恶意用户查询不存在的 ID → 缓存没有 → 打到数据库
  AI 应用：每个用户的 Prompt 都是"独一无二"的 → 天然低命中

  防护策略：
  ① 语义缓存本身就是防穿透 ── 即使 Prompt 不完全相同也能命中
  ② 空结果缓存 ── 确认不适合缓存的请求标记为 "no_cache"
  ③ 布隆过滤器 ── 快速判断一个 Prompt 是否"有可能"被缓存过
```

```python
# 空结果缓存：防止同一个无法缓存的请求被反复查询
async def get_with_null_cache(cache, messages, model, db):
    cached = await cache.get(messages, model, db)
    if cached.hit:
        if cached.content == "__NULL__":
            return CacheResult(hit=False)  # 跳过缓存，直接调用 LLM
        return cached
    return CacheResult(hit=False)

async def set_null_cache(cache, messages, model, db):
    """标记某个请求不适合缓存（如流式创意内容）"""
    await cache.l2.set(messages, model, "__NULL__", ttl=600)
```

**雪崩：大量缓存同时过期**

```
防雪崩策略：

  ① TTL 随机化 ── 基础 TTL + 随机偏移，避免集体过期
  ② 缓存永不过期 + 异步刷新 ── 过期后仍返回旧值，后台刷新
  ③ 多级缓存本身就是防雪崩 ── L2 过期了 L3 还在
```

```python
import random

def randomized_ttl(base_ttl: int, jitter_ratio: float = 0.2) -> int:
    """给 TTL 加上随机抖动，防止集体过期"""
    jitter = int(base_ttl * jitter_ratio)
    return base_ttl + random.randint(-jitter, jitter)

# base_ttl=7200 → 实际 TTL 在 5760-8640 之间随机
```

**击穿：热点 Key 过期瞬间被大量请求击穿**

```python
import asyncio

class SingleFlightCache:
    """单飞模式：同一个 Key 只允许一个请求穿透到 LLM"""
    
    def __init__(self):
        self._locks: dict[str, asyncio.Lock] = {}
        self._inflight: dict[str, asyncio.Future] = {}
    
    async def get_or_create(self, key: str, create_fn):
        """获取缓存，如果不存在则只允许一个协程创建"""
        # 检查是否有其他协程正在创建
        if key in self._inflight:
            return await self._inflight[key]
        
        # 创建锁
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        
        async with self._locks[key]:
            # 双重检查
            if key in self._inflight:
                return await self._inflight[key]
            
            # 创建 Future，其他协程等待这个结果
            future = asyncio.get_event_loop().create_future()
            self._inflight[key] = future
            
            try:
                result = await create_fn()
                future.set_result(result)
                return result
            finally:
                del self._inflight[key]
```

> 💡 **AI 场景中击穿的影响比传统 Web 大得多**——传统 Web 击穿数据库可能只增加几毫秒延迟；AI 场景击穿 LLM 意味着多花 $0.03 和 10 秒延迟。SingleFlight 模式必须上。

### 7.4 性能基准测试：缓存前后的对比数据

用一组模拟真实负载的基准测试数据来展示缓存效果（10 万次请求，混合场景）：

```
基准测试环境：
  服务器：4 核 8GB + Redis 512MB + PG (pgvector)
  模型：GPT-4o
  测试集：10 万次请求（40% FAQ + 30% 技术问答 + 30% 自由对话）

┌──────────────────┬──────────┬──────────┬──────────┐
│      指标         │  无缓存   │ 仅精确缓存│ 多级缓存  │
├──────────────────┼──────────┼──────────┼──────────┤
│ 总命中率          │  0%      │  18.3%   │  52.7%   │
│ P50 延迟          │  4.8s    │  3.9s    │  0.6s    │
│ P99 延迟          │  14.2s   │  12.1s   │  3.2s    │
│ 月 LLM 费用       │  $3,000  │  $2,451  │  $1,419  │
│ 月缓存成本        │  $0      │  $5      │  $25     │
│ 净节省            │  —       │  $544    │  $1,556  │
│ 错误率            │  1.3%    │  1.1%    │  0.6%    │
│ 缓存查询开销（P99）│  —       │  3ms     │  42ms    │
└──────────────────┴──────────┴──────────┴──────────┘
```

各层命中率分布：

```
多级缓存命中率拆解：

  L1 本地内存：14.2%  ← 短时间热点重复请求
  L2 Redis：   12.8%  ← 跨 Worker 精确匹配
  L3 pgvector：25.7%  ← 语义相似匹配
  ──────────────────
  总命中率：   52.7%  ← 三层叠加

  命中来源分析：
  ├── FAQ 类请求（40%）：命中率 78%（大部分被 L2 精确拦截）
  ├── 技术问答（30%）：命中率 51%（L3 语义匹配贡献最大）
  └── 自由对话（30%）：命中率 22%（主要依赖 L3）
```

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **核心指标** | 各层命中率 + 延迟 P99 + 内存使用率 |
| **容量规划** | 中型应用缓存成本 ~$20/月，节省 ~$1500/月 |
| **防穿透** | 语义缓存 + 空结果缓存 + 布隆过滤器 |
| **防雪崩** | TTL 随机化 + 多级兜底 |
| **防击穿** | SingleFlight 单飞模式 |

---

## 8. 完整实战：为 RAG 系统添加多级缓存

### 8.1 RAG 系统的缓存机会点分析

RAG 系统有 **四个可以加缓存的环节**，每个环节的缓存价值不同：

```
RAG 系统的缓存机会点：

  用户查询
    │
    ▼
  ① 查询缓存（最终答案）─── 命中 → 直接返回，跳过所有后续步骤
    │ miss                   命中率高，价值最大
    ▼
  ② Embedding 缓存 ──────── 命中 → 跳过 Embedding 计算
    │ miss                   节省 Embedding API 调用
    ▼
  ③ 检索缓存（chunks）───── 命中 → 跳过向量检索
    │ miss                   节省向量数据库查询
    ▼
  向量检索 → 获取 chunks
    │
    ▼
  ④ LLM 生成缓存 ──────── 命中 → 跳过 LLM 生成
    │ miss                   等同于前面章节的精确/语义缓存
    ▼
  LLM 生成答案 → 返回
```

各环节的缓存 ROI 对比：

| 缓存环节 | 节省成本 | 节省时间 | 命中率 | 优先级 |
|:---|:---|:---|:---|:---|
| **① 查询缓存** | $0.03/次 | 5-15s | 40-60% | ⭐⭐⭐⭐⭐ |
| **② Embedding 缓存** | $0.000002/次 | 20ms | 30-50% | ⭐⭐ |
| **③ 检索缓存** | ~$0 | 10-50ms | 25-45% | ⭐⭐⭐ |
| **④ LLM 生成缓存** | $0.03/次 | 5-15s | 10-20% | ⭐⭐⭐⭐ |

> 💡 **优先实现查询缓存（①）**——它在最前面，命中后直接跳过所有后续步骤，ROI 最高。Embedding 缓存（②）的节省微不足道，优先级最低。

### 8.2 查询缓存：相似问题直接复用答案

查询缓存是 RAG 最有价值的缓存——**同样的问题（语义相似），在同一个知识库上的答案高度一致**。

```python
class RAGQueryCache:
    """RAG 查询缓存：语义匹配用户问题，直接返回最终答案"""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        db: AsyncSession,
        threshold: float = 0.93,  # RAG 场景比普通问答稍严格
    ):
        self.embedding = embedding_service
        self.db = db
        self.threshold = threshold
    
    async def get(self, query: str, knowledge_base_id: str) -> dict | None:
        """查询缓存：同一知识库 + 语义相似的问题"""
        query_vec = await self.embedding.embed(query)
        
        result = await self.db.execute(
            text("""
                SELECT query_text, answer, sources, 
                       1 - (query_embedding <=> :vec) AS similarity
                FROM rag_query_cache
                WHERE knowledge_base_id = :kb_id
                  AND expires_at > NOW()
                  AND 1 - (query_embedding <=> :vec) > :threshold
                ORDER BY query_embedding <=> :vec
                LIMIT 1
            """),
            {
                "vec": str(query_vec),
                "kb_id": knowledge_base_id,
                "threshold": self.threshold,
            },
        )
        row = result.fetchone()
        
        if row:
            return {
                "answer": row.answer,
                "sources": json.loads(row.sources),
                "similarity": row.similarity,
                "cached": True,
            }
        return None
    
    async def set(self, query: str, knowledge_base_id: str,
                  answer: str, sources: list[dict]):
        """缓存 RAG 查询结果"""
        query_vec = await self.embedding.embed(query)
        
        await self.db.execute(
            text("""
                INSERT INTO rag_query_cache
                (query_text, query_embedding, knowledge_base_id, 
                 answer, sources, expires_at)
                VALUES (:query, :embedding, :kb_id, :answer, :sources,
                        NOW() + INTERVAL '4 hours')
            """),
            {
                "query": query,
                "embedding": str(query_vec),
                "kb_id": knowledge_base_id,
                "answer": answer,
                "sources": json.dumps(sources, ensure_ascii=False),
            },
        )
        await self.db.commit()
```

需要的数据表：

```sql
CREATE TABLE rag_query_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    query_embedding vector(1536) NOT NULL,
    knowledge_base_id VARCHAR(100) NOT NULL,
    answer TEXT NOT NULL,
    sources JSONB DEFAULT '[]',
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '4 hours'
);

CREATE INDEX idx_rag_cache_embedding 
ON rag_query_cache 
USING hnsw (query_embedding vector_cosine_ops);

CREATE INDEX idx_rag_cache_kb 
ON rag_query_cache (knowledge_base_id, expires_at);
```

### 8.3 检索缓存：相同 query 复用 chunk 结果

当查询缓存未命中时，下一步是向量检索。相同（或相似）的查询会检索到相同的 chunks——可以缓存这一步：

```python
class RetrievalCache:
    """检索结果缓存：缓存 query → chunks 的映射"""
    
    def __init__(self, redis_client, default_ttl: int = 3600):
        self.redis = redis_client
        self.ttl = default_ttl
    
    async def get(self, query_hash: str, kb_id: str) -> list[dict] | None:
        """查询检索结果缓存"""
        key = f"rag:retrieval:{kb_id}:{query_hash}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set(self, query_hash: str, kb_id: str, chunks: list[dict]):
        """缓存检索到的 chunks"""
        key = f"rag:retrieval:{kb_id}:{query_hash}"
        # 只缓存 chunk 的 ID 和文本，不缓存完整元数据
        slim_chunks = [
            {"id": c["id"], "text": c["text"], "score": c["score"]}
            for c in chunks
        ]
        await self.redis.setex(key, self.ttl, json.dumps(slim_chunks, ensure_ascii=False))
    
    async def invalidate_kb(self, kb_id: str):
        """知识库更新后，清除该知识库的所有检索缓存"""
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor, match=f"rag:retrieval:{kb_id}:*", count=100
            )
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
```

> 💡 **知识库更新必须触发检索缓存失效**——如果文档被增删改，旧的检索结果就不准了。在知识库管理的文档上传/删除接口中调用 `invalidate_kb()` 联动清缓存。

### 8.4 Embedding 缓存：避免重复向量化

Embedding 缓存的成本节省很小（$0.000002/次），但在**自部署 Embedding 模型**时能显著降低 GPU 负载：

```python
class EmbeddingCache:
    """Embedding 向量缓存：避免重复计算"""
    
    def __init__(self, redis_client, ttl: int = 86400):
        self.redis = redis_client
        self.ttl = ttl  # 24 小时（Embedding 不会变）
    
    async def get_or_compute(
        self, text: str, embedding_service: EmbeddingService
    ) -> list[float]:
        """先查缓存，miss 才调用 Embedding API"""
        # 用文本 Hash 做 Key
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        key = f"emb:cache:{text_hash}"
        
        # 查缓存
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        # 计算 Embedding
        vector = await embedding_service.embed(text)
        
        # 写入缓存（向量序列化为 JSON 数组）
        await self.redis.setex(key, self.ttl, json.dumps(vector))
        
        return vector
    
    async def batch_get_or_compute(
        self, texts: list[str], embedding_service: EmbeddingService
    ) -> list[list[float]]:
        """批量版本：缓存命中的跳过，miss 的批量计算"""
        results = [None] * len(texts)
        texts_to_compute = []
        indices_to_compute = []
        
        # 1. 批量查缓存
        for i, text in enumerate(texts):
            text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
            cached = await self.redis.get(f"emb:cache:{text_hash}")
            if cached:
                results[i] = json.loads(cached)
            else:
                texts_to_compute.append(text)
                indices_to_compute.append(i)
        
        # 2. 批量计算 miss 的
        if texts_to_compute:
            vectors = await embedding_service.embed_batch(texts_to_compute)
            for idx, vec, text in zip(indices_to_compute, vectors, texts_to_compute):
                results[idx] = vec
                text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
                await self.redis.setex(
                    f"emb:cache:{text_hash}", self.ttl, json.dumps(vec)
                )
        
        return results
```

> 💡 **Embedding 缓存对 API 调用场景价值有限，但对自部署模型很有意义**——自部署的 BGE-M3 每次推理消耗 GPU 资源，缓存可以减少 30-50% 的推理次数，等于用 Redis 内存换 GPU 算力。
### 8.5 端到端集成：FastAPI + Redis + pgvector 完整代码

把前面四层缓存串联成一个完整的 RAG 服务：

```python
class CachedRAGService:
    """带多级缓存的 RAG 服务"""
    
    def __init__(
        self,
        query_cache: RAGQueryCache,
        retrieval_cache: RetrievalCache,
        embedding_cache: EmbeddingCache,
        embedding_service: EmbeddingService,
        vector_store,            # 向量数据库客户端
        llm: AsyncOpenAI,
        normalizer: PromptNormalizer,
    ):
        self.query_cache = query_cache
        self.retrieval_cache = retrieval_cache
        self.embedding_cache = embedding_cache
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.llm = llm
        self.normalizer = normalizer
    
    async def answer(
        self, query: str, kb_id: str, model: str = "gpt-4o"
    ) -> dict:
        """RAG 问答：四层缓存串联"""
        
        # ── ① 查询缓存：直接返回最终答案 ──
        cached_answer = await self.query_cache.get(query, kb_id)
        if cached_answer:
            return {**cached_answer, "cache_layer": "query"}
        
        # ── ② Embedding 缓存：避免重复向量化 ──
        query_vec = await self.embedding_cache.get_or_compute(
            query, self.embedding_service
        )
        
        # ── ③ 检索缓存：复用 chunk 结果 ──
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        chunks = await self.retrieval_cache.get(query_hash, kb_id)
        
        if not chunks:
            # 缓存未命中，执行向量检索
            chunks = await self.vector_store.search(
                vector=query_vec, kb_id=kb_id, top_k=5
            )
            await self.retrieval_cache.set(query_hash, kb_id, chunks)
        
        # ── ④ LLM 生成（无缓存，因为 context 每次不同） ──
        context = "\n\n".join([c["text"] for c in chunks])
        messages = [
            {"role": "system", "content": f"根据以下资料回答问题。\n\n{context}"},
            {"role": "user", "content": query},
        ]
        
        response = await self.llm.chat.completions.create(
            model=model, messages=messages, temperature=0,
        )
        answer = response.choices[0].message.content
        sources = [{"id": c["id"], "score": c["score"]} for c in chunks]
        
        # ── 写入查询缓存（供后续相似问题复用） ──
        await self.query_cache.set(query, kb_id, answer, sources)
        
        return {
            "answer": answer,
            "sources": sources,
            "cached": False,
            "cache_layer": "none",
        }
```

FastAPI 路由集成：

```python
@rag_router.post("/query")
async def rag_query(
    request: RAGQueryRequest,
    rag_service: CachedRAGService = Depends(get_rag_service),
):
    result = await rag_service.answer(
        query=request.query,
        kb_id=request.knowledge_base_id,
        model=request.model,
    )
    
    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "cached": result.get("cached", False),
        "cache_layer": result.get("cache_layer", "none"),
    }

# 知识库更新时联动清缓存
@kb_router.post("/{kb_id}/documents")
async def upload_document(
    kb_id: str, file: UploadFile,
    retrieval_cache: RetrievalCache = Depends(get_retrieval_cache),
):
    # ... 文档解析、分块、入库 ...
    
    # 清除该知识库的检索缓存和查询缓存
    await retrieval_cache.invalidate_kb(kb_id)
    
    return {"status": "uploaded"}
```

> 💡 **四层缓存的串联顺序很重要**——查询缓存（最前面，命中就全部跳过）→ Embedding 缓存 → 检索缓存 → LLM 生成。每一层只在前一层 miss 时才执行，形成漏斗式的成本过滤。

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **四个缓存点** | 查询→Embedding→检索→生成，漏斗式过滤 |
| **查询缓存** | ROI 最高，语义匹配直接返回最终答案 |
| **检索缓存** | Redis 缓存 chunks，知识库更新时联动失效 |
| **Embedding 缓存** | 自部署模型有价值，API 调用场景优先级低 |
| **联动失效** | 知识库更新必须清除检索缓存 + 查询缓存 |

---

## 附录

### A. 缓存方案选型对照表

| 维度 | 仅精确缓存 | 精确 + 语义 | 多级缓存（L1/L2/L3） |
|:---|:---|:---|:---|
| **实现复杂度** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **命中率** | 10-20% | 35-50% | 50-70% |
| **额外延迟** | < 5ms | < 50ms | < 50ms |
| **依赖** | Redis | Redis + Embedding API + pgvector | 同左 + 本地内存 |
| **适用场景** | FAQ、模板化 Prompt | 通用 AI 应用 | 高流量、成本敏感 |
| **推荐阶段** | MVP / POC | 正式上线 | 日均 10 万+ 请求 |

### B. 配置模板与 Docker Compose

```yaml
# docker-compose.yml - AI 缓存架构基础设施
version: "3.8"

services:
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ai_cache
      POSTGRES_USER: app
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  redis_data:
  pg_data:
```

### C. 推荐阅读与工具链

**开源工具：**
- **GPTCache**：LangChain 生态的语义缓存库，开箱即用
- **Redis Stack**：内置向量搜索（VSS），无需额外部署
- **pgvector**：PostgreSQL 向量扩展，零额外基础设施

**延伸阅读：**
- **[构建企业级 RAG 系统](构建企业级 RAG 系统)**：RAG 系统的完整工程实践
- **[AI 应用的成本控制与优化](python/AI 应用的成本控制与优化)**：缓存之外的成本优化手段
- **[AI 应用的后端架构设计](AI 应用的后端架构设计)**：FastAPI + Redis + PG 的标准架构
- **[Embedding 模型选型与微调](Embedding 模型选型与微调)**：如何选择和优化 Embedding 模型
