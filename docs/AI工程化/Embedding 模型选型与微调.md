# Embedding 模型选型与微调

> 从原理到实战——理解向量嵌入的本质，掌握中英文 Embedding 模型选型（OpenAI/BGE/Jina/Cohere），学会用自有数据微调 Embedding 模型，显著提升 RAG 检索质量。

---

## 1. Embedding 基础：为什么向量是 AI 搜索的基石

### 1.1 什么是 Embedding：文本到向量的映射

```
Embedding 的本质：

  "Python 异步编程"  →  [0.12, -0.34, 0.67, ..., 0.23]   (1536 维向量)
  "asyncio 教程"     →  [0.11, -0.31, 0.65, ..., 0.25]   (相似)
  "今天天气真好"      →  [-0.45, 0.22, -0.11, ..., 0.78]  (不同)

  语义相近的文本 → 向量距离近
  语义不同的文本 → 向量距离远
```

### 1.2 语义搜索 vs 关键词搜索：为什么需要向量

| 维度 | 关键词搜索 (BM25) | 语义搜索 (Embedding) |
|:---|:---|:---|
| 查询 | "Python 异步" | "Python 异步" |
| 能搜到 | 包含"Python"和"异步"的文档 | 包含 asyncio/协程/await 的文档 |
| 搜不到 | 不含关键词但语义相关的 | — |
| 优势 | 精确匹配、速度快 | 语义理解、同义词 |
| 劣势 | 不理解同义词 | 可能匹配到无关内容 |

### 1.3 向量维度、相似度与距离度量

```python
import numpy as np

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """余弦相似度：最常用的度量方式"""
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 三种常用距离度量
# 1. 余弦相似度：[-1, 1]，1 表示完全相同（RAG 首选）
# 2. 欧氏距离：  [0, ∞]，0 表示完全相同
# 3. 内积：      [-∞, ∞]，归一化后等于余弦相似度
```

| 度量 | 公式 | 适用场景 |
|:---|:---|:---|
| 余弦相似度 | cos(a,b) | 文本检索（推荐） |
| 欧氏距离 | ‖a-b‖₂ | 聚类、分类 |
| 内积 | a·b | 归一化向量 |

### 1.4 Embedding 在 RAG 中的关键角色

```
RAG 流程中 Embedding 出现两次：

  离线阶段（索引构建）：
    文档 → 分块 → Embedding 模型 → 向量 → 存入向量数据库
  
  在线阶段（查询检索）：
    用户问题 → Embedding 模型 → 查询向量 → 向量数据库检索 → Top-K 结果

  关键：两次必须用同一个 Embedding 模型！
```

> 💡 **Embedding 模型的选择直接决定 RAG 的检索质量**——模型不好，检索到的都是无关内容，后面的 LLM 再强也没用。Embedding 是 RAG 的"地基"。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Embedding** | 把文本映射到高维向量空间 |
| **余弦相似度** | 衡量两个向量方向的接近程度 |
| **语义搜索** | 理解含义而非匹配关键词 |

---

## 2. 主流模型对比：选哪个 Embedding 模型

### 2.1 API 模型：OpenAI / Cohere / Voyage

| 模型 | 维度 | 最大 Token | 价格 ($/1M tokens) | 特点 |
|:---|:---|:---|:---|:---|
| **text-embedding-3-small** | 1536 | 8191 | $0.02 | 性价比之王 |
| **text-embedding-3-large** | 3072 | 8191 | $0.13 | OpenAI 最强 |
| Cohere embed-v3 | 1024 | 512 | $0.10 | 多语言优秀 |
| Voyage-3 | 1024 | 32000 | $0.06 | 长文本、代码 |

### 2.2 开源模型：BGE / Jina / E5 / GTE

| 模型 | 维度 | 参数量 | 中文 | MTEB 排名 |
|:---|:---|:---|:---|:---|
| **bge-large-zh-v1.5** | 1024 | 326M | ⭐⭐⭐⭐⭐ | 中文 Top1 |
| **bge-m3** | 1024 | 568M | ⭐⭐⭐⭐⭐ | 多语言顶级 |
| jina-embeddings-v3 | 1024 | 570M | ⭐⭐⭐⭐ | 长文本 8192 |
| e5-large-v2 | 1024 | 335M | ⭐⭐⭐ | 英文顶级 |
| gte-large-zh | 1024 | 326M | ⭐⭐⭐⭐ | 阿里出品 |

### 2.3 中文场景专项对比

```python
# 中文检索测试
queries = [
    "Python 的异步编程怎么用",
    "如何处理数据库连接泄漏",
    "机器学习和深度学习的区别",
]

# 测试结果排名（中文检索 Recall@5）
# 1. bge-large-zh-v1.5     → 0.89
# 2. bge-m3                → 0.87
# 3. gte-large-zh          → 0.85
# 4. text-embedding-3-large→ 0.83
# 5. jina-embeddings-v3    → 0.81
# 6. text-embedding-3-small→ 0.78
```

### 2.4 MTEB 排行榜解读与选型决策树

```
选型决策树：

  需要 Embedding 模型
  │
  ├─ 不想自部署？
  │   ├─ 预算充足 → text-embedding-3-large
  │   └─ 控制成本 → text-embedding-3-small
  │
  └─ 自部署（更便宜/更可控）？
      │
      ├─ 主要是中文？
      │   ├─ 性能优先 → bge-large-zh-v1.5
      │   └─ 多语言   → bge-m3
      │
      ├─ 主要是英文？
      │   └─ e5-large-v2 或 gte-large-en
      │
      └─ 长文本（>512 token）？
          └─ jina-embeddings-v3（支持 8192）
```

> 💡 **中文场景首选 BGE**——智源出品的 BGE 系列在中文检索任务上持续霸榜。bge-m3 是"瑞士军刀"，支持 100+ 语言且能同时做稠密+稀疏检索。

**第 2 章核心知识回顾：**

| 场景 | 推荐模型 |
|:---|:---|
| 中文 RAG | bge-large-zh-v1.5 |
| 多语言 | bge-m3 |
| 不想部署 | text-embedding-3-small |
| 长文本 | jina-embeddings-v3 |

---

## 3. 快速上手：调用与部署 Embedding 模型

### 3.1 OpenAI Embedding API：最简方案

```python
from openai import OpenAI

client = OpenAI()

def get_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding

# 单条
vec = get_embedding("Python 异步编程教程")
print(f"维度: {len(vec)}")  # 1536

# 批量（一次最多 2048 条）
def batch_embed(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    response = client.embeddings.create(input=texts, model=model)
    return [d.embedding for d in sorted(response.data, key=lambda x: x.index)]
```

### 3.2 sentence-transformers：本地部署开源模型

```python
# pip install sentence-transformers
from sentence_transformers import SentenceTransformer

# 加载模型（首次下载约 1.2GB）
model = SentenceTransformer("BAAI/bge-large-zh-v1.5")

# 编码
texts = ["Python 异步编程", "asyncio 协程教程", "今天天气真好"]
embeddings = model.encode(texts, normalize_embeddings=True)

print(f"维度: {embeddings.shape}")  # (3, 1024)

# 计算相似度
from sentence_transformers.util import cos_sim
similarities = cos_sim(embeddings[0], embeddings[1:])
print(similarities)  # tensor([0.89, 0.12](0.89, 0.12))  # 第一个相似，第二个不相似
```

### 3.3 批量向量化：高效处理大量文档

```python
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

model = SentenceTransformer("BAAI/bge-large-zh-v1.5")

def batch_encode(texts: list[str], batch_size: int = 64, show_progress: bool = True):
    """批量编码，带进度条"""
    all_embeddings = []
    
    for i in tqdm(range(0, len(texts), batch_size), disable=not show_progress):
        batch = texts[i:i + batch_size]
        embeddings = model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
        all_embeddings.extend(embeddings)
    
    return all_embeddings

# 10 万条文档，batch_size=64，约 20 分钟（CPU）/ 2 分钟（GPU）
vectors = batch_encode(documents, batch_size=64)
```

### 3.4 GPU 加速与量化部署

```python
# GPU 加速
model = SentenceTransformer("BAAI/bge-large-zh-v1.5", device="cuda")

# ONNX 加速（CPU 场景提速 2-3 倍）
# pip install optimum[onnxruntime]
from optimum.onnxruntime import ORTModelForFeatureExtraction

ort_model = ORTModelForFeatureExtraction.from_pretrained(
    "BAAI/bge-large-zh-v1.5", export=True
)

# 量化（模型体积缩小 4 倍，速度提升 2 倍，精度损失 <1%）
from optimum.onnxruntime import ORTQuantizer, AutoQuantizationConfig

quantizer = ORTQuantizer.from_pretrained(ort_model)
config = AutoQuantizationConfig.avx512_vnni(is_static=False)
quantizer.quantize(save_dir="./quantized_model", quantization_config=config)
```

> 💡 **生产环境建议 ONNX + 量化**——纯 CPU 部署场景，ONNX 量化模型的速度是原始 PyTorch 的 3-5 倍，精度损失可忽略。

**第 3 章核心知识回顾：**

| 方案 | 速度 | 成本 | 适用 |
|:---|:---|:---|:---|
| OpenAI API | 快 | $0.02/1M | 不想部署 |
| sentence-transformers | 中 | 免费 | GPU 服务器 |
| ONNX 量化 | 快 | 免费 | 纯 CPU 部署 |

---

## 4. 检索质量评测：怎么知道 Embedding 好不好

### 4.1 核心指标：Recall@K / MRR / NDCG

| 指标 | 含义 | 计算方式 |
|:---|:---|:---|
| **Recall@K** | Top-K 中有多少相关文档 | 检索到的相关数 / 总相关数 |
| **MRR** | 第一个相关文档排第几 | 1 / 排名位置 的均值 |
| **NDCG@K** | 排序质量（考虑位置） | 加权排名分 |
| **Hit Rate** | Top-K 中有没有相关的 | 有=1，没有=0 |

```python
def recall_at_k(retrieved_ids: list, relevant_ids: set, k: int) -> float:
    """Recall@K：Top-K 中有多少相关文档"""
    top_k = set(retrieved_ids[:k])
    return len(top_k & relevant_ids) / len(relevant_ids)

def mrr(retrieved_ids: list, relevant_ids: set) -> float:
    """MRR：第一个相关文档的排名"""
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0
```

### 4.2 构建领域评测数据集

```python
async def generate_eval_dataset(documents: list[str], n_queries: int = 100) -> list[dict]:
    """用 LLM 自动生成评测数据集"""
    eval_data = []
    
    for doc in random.sample(documents, n_queries):
        # 让 LLM 根据文档生成可能的用户查询
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": 
                f"根据以下文档内容，生成 2 个用户可能会搜索的问题：\n\n{doc[:500]}"}],
        )
        queries = response.choices[0].message.content.strip().split("\n")
        
        for query in queries:
            eval_data.append({
                "query": query.strip().lstrip("0123456789.-) "),
                "relevant_doc_id": doc_id,
            })
    
    return eval_data
```

### 4.3 自动化评测框架

```python
class EmbeddingEvaluator:
    """Embedding 模型评测框架"""
    
    def __init__(self, eval_dataset: list[dict], documents: list[str]):
        self.eval_data = eval_dataset
        self.documents = documents
    
    async def evaluate(self, model_name: str, encode_fn) -> dict:
        # 1. 向量化所有文档
        doc_embeddings = encode_fn(self.documents)
        
        # 2. 对每个查询计算指标
        recalls, mrrs, hit_rates = [], [], []
        
        for item in self.eval_data:
            query_vec = encode_fn([item["query"]])[0]
            
            # 计算相似度并排序
            scores = cosine_similarity(query_vec, doc_embeddings)
            top_k_ids = scores.argsort()[-10:][::-1]
            
            relevant = {item["relevant_doc_id"]}
            recalls.append(recall_at_k(top_k_ids, relevant, k=5))
            mrrs.append(mrr(top_k_ids, relevant))
            hit_rates.append(1.0 if relevant & set(top_k_ids[:5]) else 0.0)
        
        return {
            "model": model_name,
            "recall@5": sum(recalls) / len(recalls),
            "mrr": sum(mrrs) / len(mrrs),
            "hit_rate@5": sum(hit_rates) / len(hit_rates),
        }
```

### 4.4 多模型对比实验

```python
models = {
    "bge-large-zh": lambda texts: SentenceTransformer("BAAI/bge-large-zh-v1.5").encode(texts),
    "bge-m3": lambda texts: SentenceTransformer("BAAI/bge-m3").encode(texts),
    "openai-small": lambda texts: batch_embed_openai(texts, "text-embedding-3-small"),
    "openai-large": lambda texts: batch_embed_openai(texts, "text-embedding-3-large"),
}

results = []
for name, encode_fn in models.items():
    result = await evaluator.evaluate(name, encode_fn)
    results.append(result)

# 打印对比表
# | 模型           | Recall@5 | MRR   | HitRate@5 |
# | bge-large-zh   | 0.892    | 0.756 | 0.934     |
# | bge-m3         | 0.878    | 0.741 | 0.921     |
# | openai-large   | 0.834    | 0.698 | 0.889     |
# | openai-small   | 0.781    | 0.652 | 0.845     |
```

> 💡 **一定要用自己的数据做评测**——MTEB 排行榜是通用场景的排名，你的领域数据可能完全不同。BGE 在通用中文上第一，但金融/医疗领域未必。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Recall@K** | Top-K 中找到了多少相关文档 |
| **MRR** | 第一个相关文档排得越前越好 |
| **领域评测** | 用自己的数据评测，不依赖 MTEB |

---

## 5. 微调 Embedding：用自有数据提升检索质量

### 5.1 为什么需要微调：通用模型的局限

| 场景 | 通用模型 Recall@5 | 微调后 Recall@5 | 提升 |
|:---|:---|:---|:---|
| 技术文档 | 0.82 | 0.91 | +11% |
| 医疗问答 | 0.65 | 0.84 | +29% |
| 法律条文 | 0.58 | 0.79 | +36% |
| 金融研报 | 0.71 | 0.88 | +24% |

> 领域越专业，微调提升越大。通用模型不懂行业术语和缩写。

### 5.2 训练数据构造：正例对、负例对、硬负例

```python
# 训练数据格式：(query, positive, negative)
# 正例对：query 和 positive 是语义相关的
# 负例对：query 和 negative 是语义不相关的
# 硬负例：看起来相关但实际不相关的（最重要！）

training_data = [
    {
        "query": "Python 协程和线程的区别",
        "positive": "asyncio 协程是单线程并发，通过事件循环切换任务...",
        "negative": "Python 列表推导式是一种优雅的创建列表方式...",       # 简单负例
        "hard_negative": "Java 线程是操作系统级别的并发单元...",           # 硬负例
    },
]
```

```python
async def generate_training_pairs(documents: list[str], n: int = 1000) -> list[dict]:
    """用 LLM 自动生成训练对"""
    pairs = []
    
    for doc in random.sample(documents, n):
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": 
                f"为以下文档生成 1 个搜索查询：\n\n{doc[:300]}\n\n只输出查询，不要解释。"}],
        )
        query = response.choices[0].message.content.strip()
        
        # 正例 = 当前文档
        # 负例 = 随机选一个不相关文档
        negative = random.choice([d for d in documents if d != doc])
        
        pairs.append({"query": query, "positive": doc, "negative": negative})
    
    return pairs
```

### 5.3 sentence-transformers 微调实战

```python
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# 1. 加载预训练模型
model = SentenceTransformer("BAAI/bge-large-zh-v1.5")

# 2. 准备训练数据
train_examples = []
for pair in training_data:
    # 三元组格式：(anchor, positive, negative)
    train_examples.append(InputExample(
        texts=[pair["query"], pair["positive"], pair["negative"]]
    ))

train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)

# 3. 定义损失函数
train_loss = losses.TripletLoss(model=model)

# 4. 开始训练
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=3,
    warmup_steps=100,
    output_path="./finetuned_embedding",
    show_progress_bar=True,
)

# 5. 加载微调后的模型
finetuned = SentenceTransformer("./finetuned_embedding")
```

### 5.4 损失函数选择：对比学习 vs 三元组

| 损失函数 | 输入格式 | 适用场景 |
|:---|:---|:---|
| **MultipleNegativesRankingLoss** | (query, positive) | 正例对，自动构造负例 |
| **TripletLoss** | (query, positive, negative) | 有明确负例时 |
| **CosineSimilarityLoss** | (text_a, text_b, score) | 连续相似度标注 |
| **ContrastiveLoss** | (text_a, text_b, label) | 二分类（相关/不相关） |

```python
# 推荐：MultipleNegativesRankingLoss（最简单高效）
# 只需要 (query, positive) 对，同 batch 内的其他 positive 自动作为负例
from sentence_transformers import losses

train_examples = [InputExample(texts=[q, p]) for q, p in query_positive_pairs]
train_loss = losses.MultipleNegativesRankingLoss(model)
```

> 💡 **MultipleNegativesRankingLoss 是"最省数据"的方式**——只需要正例对，batch 内交叉作为负例。batch_size 越大效果越好，建议 ≥ 32。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **硬负例** | 看起来相关但不相关的样本，最能提升效果 |
| **三元组** | (query, positive, negative) 训练格式 |
| **MNRL 损失** | 只需正例对，batch 内自动构造负例 |

---

## 6. 高级微调技巧

### 6.1 硬负例挖掘：让模型学会区分细微差异

```python
def mine_hard_negatives(model, queries: list[str], documents: list[str], top_k: int = 10):
    """用当前模型挖掘硬负例"""
    doc_embeddings = model.encode(documents, normalize_embeddings=True)
    hard_negatives = []
    
    for query, true_doc_id in zip(queries, true_doc_ids):
        query_vec = model.encode(query, normalize_embeddings=True)
        scores = cosine_similarity(query_vec, doc_embeddings)
        
        # 取排名靠前但不是正确答案的文档作为硬负例
        top_ids = scores.argsort()[-top_k:][::-1]
        hard_neg_ids = [i for i in top_ids if i != true_doc_id][:3]
        
        hard_negatives.append({
            "query": query,
            "positive": documents[true_doc_id],
            "hard_negatives": [documents[i] for i in hard_neg_ids],
        })
    
    return hard_negatives
```

### 6.2 Matryoshka 训练：一个模型支持多种维度

```python
from sentence_transformers import losses

# Matryoshka：训练时同时优化多个维度的子向量
# 结果：前 256 维就能达到不错效果，完整 1024 维效果最好
matryoshka_loss = losses.MatryoshkaLoss(
    model=model,
    loss=losses.MultipleNegativesRankingLoss(model),
    matryoshka_dims=[64, 128, 256, 512, 1024],
)

# 使用时可以灵活截断
embeddings = model.encode(texts, normalize_embeddings=True)
dim_256 = embeddings[:, :256]    # 只用前 256 维（更小更快）
dim_1024 = embeddings[:, :1024]  # 完整维度（更准）
```

### 6.3 知识蒸馏：从大模型蒸馏到小模型

```python
from sentence_transformers import SentenceTransformer, losses

# 教师模型（大且准）
teacher = SentenceTransformer("BAAI/bge-large-zh-v1.5")

# 学生模型（小且快）
student = SentenceTransformer("BAAI/bge-small-zh-v1.5")

# 蒸馏训练：让学生模型的输出接近教师模型
train_examples = [InputExample(texts=[text]) for text in documents]
train_dataloader = DataLoader(train_examples, batch_size=32)

distill_loss = losses.MSELoss(model=student)

# 生成教师标签
teacher_embeddings = teacher.encode(documents, normalize_embeddings=True)
```

### 6.4 数据增强：用 LLM 生成训练数据

```python
async def augment_queries(original_query: str, n: int = 3) -> list[str]:
    """用 LLM 生成查询的多种表述"""
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": 
            f"改写以下查询为 {n} 种不同的表述，保持语义不变：\n\n{original_query}"}],
    )
    return response.choices[0].message.content.strip().split("\n")

# 一条训练数据 → 4 条（原始 + 3 个改写）
# "Python 协程怎么用"
# → "Python asyncio 教程"
# → "如何在 Python 中使用协程"
# → "Python 异步编程入门"
```

> 💡 **硬负例挖掘 → 数据增强 → 继续训练**——这是一个迭代循环。每轮训练后用新模型挖掘更难的硬负例，效果逐步提升。

**第 6 章核心知识回顾：**

| 技巧 | 效果 |
|:---|:---|
| **硬负例挖掘** | 提升区分细微差异的能力 |
| **Matryoshka** | 一个模型灵活调整维度/速度 |
| **知识蒸馏** | 大模型效果 + 小模型速度 |
| **LLM 增强** | 低成本扩充训练数据 |

---

## 7. 生产实践：Embedding 系统的工程优化

### 7.1 向量缓存：避免重复计算

```python
import hashlib

class EmbeddingCache:
    def __init__(self, redis_client, model):
        self.redis = redis_client
        self.model = model
    
    async def encode(self, text: str) -> list[float]:
        cache_key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
        
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        embedding = self.model.encode(text, normalize_embeddings=True).tolist()
        await self.redis.setex(cache_key, 86400, json.dumps(embedding))  # 缓存 24 小时
        return embedding
```

### 7.2 在线 vs 离线向量化

```
在线向量化（查询阶段）：
  用户查询 → 实时编码 → 检索
  要求：低延迟（< 50ms），模型常驻内存

离线向量化（索引阶段）：
  新文档 → 异步队列 → 批量编码 → 入库
  要求：高吞吐，可以慢一点，用 GPU 加速

  最佳实践：
  - 在线用 ONNX 量化模型，CPU 即可（30ms/条）
  - 离线用 GPU 全精度模型，批量处理（1000 条/秒）
```

### 7.3 模型版本管理与向量迁移

```python
class EmbeddingVersionManager:
    """Embedding 模型版本管理"""
    
    def __init__(self):
        self.current_version = "bge-large-zh-v1.5"
        self.new_version = "bge-large-zh-v1.5-finetuned-v2"
    
    async def migrate_vectors(self, vector_db, documents: list):
        """模型升级时，重新计算所有向量"""
        new_model = SentenceTransformer(self.new_version)
        
        # 批量重新编码
        for batch in chunked(documents, 100):
            new_vectors = new_model.encode([d["content"] for d in batch])
            await vector_db.upsert(
                ids=[d["id"] for d in batch],
                vectors=new_vectors,
                metadata={"model_version": self.new_version},
            )
```

### 7.4 多语言与跨语言检索

```python
# bge-m3：同一个模型处理多语言
model = SentenceTransformer("BAAI/bge-m3")

# 中文查询 → 检索英文文档（跨语言）
query_zh = model.encode("如何使用 Python 异步编程")
doc_en = model.encode("How to use Python asyncio for async programming")

similarity = cos_sim(query_zh, doc_en)
# 0.87 — 跨语言也能匹配！
```

> 💡 **模型升级 = 全量重建向量**——换了 Embedding 模型，旧向量就废了，必须全部重新编码。这是 Embedding 系统最昂贵的操作，提前规划好模型选型。

---

## 附录：Embedding 速查手册

### A.1 主流模型参数对比表

| 模型 | 维度 | 参数 | 中文 | 多语言 | 长文本 | 价格 |
|:---|:---|:---|:---|:---|:---|:---|
| text-embedding-3-small | 1536 | — | ⭐⭐⭐ | ✅ | 8K | $0.02/1M |
| text-embedding-3-large | 3072 | — | ⭐⭐⭐⭐ | ✅ | 8K | $0.13/1M |
| bge-large-zh-v1.5 | 1024 | 326M | ⭐⭐⭐⭐⭐ | ❌ | 512 | 免费 |
| bge-m3 | 1024 | 568M | ⭐⭐⭐⭐⭐ | ✅ | 8K | 免费 |
| jina-embeddings-v3 | 1024 | 570M | ⭐⭐⭐⭐ | ✅ | 8K | 免费 |

### A.2 微调超参推荐配置

| 参数 | 推荐值 | 说明 |
|:---|:---|:---|
| batch_size | 32-64 | MNRL 损失越大越好 |
| learning_rate | 2e-5 | 微调不要太大 |
| epochs | 3-5 | 过大容易过拟合 |
| warmup_ratio | 0.1 | 前 10% 步预热 |
| max_seq_length | 512 | BGE 默认 512 |

### A.3 评测脚本模板

```python
# 完整评测流程
model = SentenceTransformer("your_model")
evaluator = EmbeddingEvaluator(eval_dataset, documents)
result = await evaluator.evaluate("your_model", model.encode)
print(f"Recall@5: {result['recall@5']:.3f}, MRR: {result['mrr']:.3f}")
```

### A.4 常见问题与排查

| 问题 | 原因 | 解决 |
|:---|:---|:---|
| 检索结果不相关 | 模型不适合领域 | 换模型或微调 |
| 编码速度慢 | CPU + PyTorch | 用 ONNX 量化 |
| 向量维度太大 | 存储成本高 | Matryoshka 截断降维 |
| 中英混合效果差 | 单语言模型 | 换 bge-m3 |
| 微调后效果变差 | 过拟合 / 数据质量 | 减少 epoch / 清洗数据 |
