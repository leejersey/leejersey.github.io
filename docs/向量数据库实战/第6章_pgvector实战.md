# 第 6 章 pgvector 实战——用 PostgreSQL 做向量搜索

> 已经有 PostgreSQL？那你根本不需要再部署一个独立的向量数据库——pgvector 扩展让你在现有数据库里直接存向量、建索引、做语义搜索，零额外基建。

---

## 6.1 为什么选 pgvector：已有 PostgreSQL 就够了

pgvector 的核心价值不是"最快的向量数据库"，而是**最低的接入门槛**：

| 维度 | pgvector | Chroma | Milvus |
| :--- | :--- | :--- | :--- |
| 部署方式 | PostgreSQL 扩展（`CREATE EXTENSION`） | 独立进程 / 嵌入式 | 独立集群（Docker） |
| 额外基建 | ❌ 无需 | 需要单独部署 | 需要 etcd + MinIO + 多组件 |
| 向量 + 业务数据 | ✅ 同一张表，同一个事务 | 独立存储，需要关联 | 独立存储，需要关联 |
| SQL 支持 | ✅ 完整 SQL（JOIN / WHERE / GROUP BY） | ❌ 只有简单过滤 | 有限的标量过滤 |
| 事务支持 | ✅ ACID 事务 | ❌ | ❌ |
| 适用规模 | 百万级向量 | 开发/原型 | 十亿级向量 |

**什么时候选 pgvector？**
- 项目已经在用 PostgreSQL
- 向量数据量在百万级以内
- 需要向量搜索和业务查询在同一个事务中
- 不想增加运维复杂度

---

## 6.2 安装与基础操作

### 安装 pgvector

```bash
# Docker（推荐）
docker run -d --name pgvector \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 或者在已有 PostgreSQL 上安装
# Ubuntu/Debian
sudo apt install postgresql-16-pgvector

# macOS (Homebrew)
brew install pgvector
```

### 启用扩展与基础操作

```sql
-- 启用扩展
CREATE EXTENSION vector;

-- 创建表（1536 维向量，匹配 OpenAI text-embedding-3-small）
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT,
    embedding vector(1536)   -- 向量列
);

-- 插入数据
INSERT INTO documents (title, content, embedding)
VALUES (
    'Python 异步编程',
    'asyncio 是 Python 的异步 I/O 框架...',
    '[0.1, 0.2, 0.3, ...]'::vector  -- 1536 维向量
);

-- 语义搜索（余弦距离，越小越相似）
SELECT title, content,
       embedding <=> '[0.1, 0.2, ...]'::vector AS distance
FROM documents
ORDER BY distance
LIMIT 5;
```

**三种距离运算符：**

| 运算符 | 距离类型 | 使用场景 |
| :--- | :--- | :--- |
| `<=>` | 余弦距离 | ⭐ 最常用，归一化向量 |
| `<->` | 欧氏距离（L2） | 绝对距离敏感场景 |
| `<#>` | 内积（负值） | 最大内积搜索 |

---

## 6.3 索引选型：HNSW vs IVFFlat

没有索引时，pgvector 做的是暴力搜索（精确但慢）。数据量超过几万条就必须建索引：

```sql
-- HNSW 索引（推荐）
CREATE INDEX ON documents
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 256);

-- IVFFlat 索引（构建快，但需要定期重建）
CREATE INDEX ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- lists ≈ sqrt(行数)
```

```sql
-- 查询时调优
SET hnsw.ef_search = 100;          -- HNSW：搜索精度（默认 40）
SET ivfflat.probes = 10;           -- IVFFlat：探测聚类数（默认 1）
```

| 维度 | HNSW | IVFFlat |
| :--- | :--- | :--- |
| 搜索精度 | ⭐ 更高 | 依赖参数调优 |
| 搜索速度 | ⭐ 更快且稳定 | 不稳定 |
| 构建速度 | 慢（内存密集） | ⭐ 快 |
| 增量更新 | ✅ 自动维护 | ❌ 需定期重建索引 |
| 推荐场景 | 生产环境（默认选择） | 数据频繁全量重建 |

> 💡 **结论：** 2025 年起，**HNSW 是默认选择**。IVFFlat 只在构建速度是瓶颈时才考虑。

---

## 6.4 与 SQLAlchemy 2.0 / FastAPI 集成

```python
# 安装依赖
# pip install sqlalchemy asyncpg pgvector

from sqlalchemy import String, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(50))
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
```

```python
# 语义搜索
from pgvector.sqlalchemy import CosineDistance

async def search_similar(
    session: AsyncSession,
    query_embedding: list[float],
    limit: int = 5
) -> list[Document]:
    stmt = (
        select(Document)
        .order_by(Document.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    return (await session.scalars(stmt)).all()
```

```python
# FastAPI 路由
from fastapi import FastAPI, Depends

app = FastAPI()

@app.post("/search")
async def search(
    query: str,
    db: AsyncSession = Depends(get_db)
):
    # 1. 生成查询向量
    query_embedding = await get_embedding(query)
    
    # 2. 向量搜索
    docs = await search_similar(db, query_embedding, limit=5)
    
    return [{"title": d.title, "content": d.content} for d in docs]
```

---

## 6.5 混合查询：向量搜索 + SQL 条件一条语句搞定

这是 pgvector 最大的杀手锏——**向量搜索和业务过滤在同一条 SQL 里**：

```python
# 向量搜索 + 分类过滤 + 时间范围 = 一条语句
stmt = (
    select(Document)
    .where(
        Document.category == "python",
        Document.created_at >= datetime(2025, 1, 1),
    )
    .order_by(Document.embedding.cosine_distance(query_embedding))
    .limit(5)
)

# 等价 SQL：
# SELECT * FROM documents
# WHERE category = 'python'
#   AND created_at >= '2025-01-01'
# ORDER BY embedding <=> $1
# LIMIT 5;
```

```python
# 更复杂的例子：JOIN + 向量搜索
stmt = (
    select(Document, User.name)
    .join(User, Document.author_id == User.id)
    .where(User.is_active == True)
    .order_by(Document.embedding.cosine_distance(query_embedding))
    .limit(10)
)
# 在 Chroma/Milvus 中，这需要两次查询 + 应用层关联
# 在 pgvector 中，一条 SQL 搞定
```

> 💡 **pgvector 的混合查询优势：** Chroma/Milvus 做过滤时，先向量搜索再过滤（post-filter），可能导致结果不足。pgvector 在数据库层面 WHERE + ORDER BY 一起执行，结果总是精确的。

---

## 6.6 pgvector vs Chroma vs Milvus 选型

| 维度 | pgvector | Chroma | Milvus |
| :--- | :--- | :--- | :--- |
| **定位** | PostgreSQL 扩展 | 开发友好型 | 企业级向量引擎 |
| **部署复杂度** | ⭐ 最低 | 低 | 高 |
| **适用规模** | < 500 万向量 | < 100 万向量 | 10 亿级 |
| **向量 + 业务数据** | ✅ 同表同事务 | ❌ 独立存储 | ❌ 独立存储 |
| **SQL 支持** | ✅ 完整 SQL | ❌ | 有限 |
| **混合检索** | ✅ SQL 原生 | 基础元数据过滤 | Dense + Sparse |
| **分布式** | 需 Citus 扩展 | ❌ | ✅ 原生 |
| **生态** | PostgreSQL 全生态 | LangChain 集成好 | 最丰富的向量工具 |

**选型决策树：**

```
你已经在用 PostgreSQL 吗？
├── 是 → 数据量 < 500 万？
│   ├── 是 → pgvector ✅（零基建，同表查询）
│   └── 否 → Milvus（专业向量引擎）
└── 否 → 只是做原型/实验？
    ├── 是 → Chroma（最快上手）
    └── 否 → 评估 Milvus 或 pgvector + 新建 PG
```

> 💡 **实战经验：** 80% 的 RAG 项目，数据量不会超过百万条文档。这意味着 pgvector 对于绝大多数团队来说**完全够用**——而且你省下了一整套向量数据库的部署和运维成本。
