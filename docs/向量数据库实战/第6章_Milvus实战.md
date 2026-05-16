# 向量数据库实战（Milvus/Chroma）

> 从 Embedding 的第一个维度到 RAG 系统的最后一公里——手把手带你玩转向量数据库。

---

## 6. Milvus 实战——生产级向量数据库

Chroma 适合快速上手和中小型项目。但当你的数据量增长到百万级、需要分布式部署、要求毫秒级延迟和高可用——你需要 **Milvus**。

Milvus 是目前最成熟的开源向量数据库，背后有 Zilliz 公司维护，在生产环境中被广泛使用。这一章我们从部署到操作，完整走通 Milvus 的核心功能。

---

### 6.1 三种部署模式：从 Lite 到分布式

```
Milvus 的三种部署模式：

  ┌─────────────────────────────────────────────────┐
  │                                                 │
  │  Milvus Lite（嵌入式）                            │
  │  ─────────────────────                           │
  │  • pip install pymilvus 即可使用                  │
  │  • 数据存在本地文件                               │
  │  • 适合：开发调试、学习、Jupyter Notebook          │
  │  • 限制：单进程，无持久化服务                      │
  │                                                 │
  │  Milvus Standalone（单机版）                      │
  │  ─────────────────────                           │
  │  • Docker Compose 一键部署                        │
  │  • 包含完整功能：索引、持久化、API 服务             │
  │  • 适合：中小型生产环境，百万级数据                 │
  │  • 限制：单节点，无法水平扩展                      │
  │                                                 │
  │  Milvus Distributed（分布式）                     │
  │  ─────────────────────                           │
  │  • Kubernetes 部署                               │
  │  • 组件分离：Proxy / DataNode / QueryNode / ...   │
  │  • 适合：大规模生产环境，亿级数据                   │
  │  • 依赖：K8s + etcd + MinIO + Pulsar             │
  │                                                 │
  └─────────────────────────────────────────────────┘

  选择建议：
    学习/开发 → Milvus Lite
    中小型生产 → Standalone（本章重点）
    大规模生产 → Distributed 或 Zilliz Cloud（托管服务）
```

### 6.2 Docker 部署与 pymilvus 连接

### 快速部署 Standalone

```bash
# 1. 下载 docker-compose 文件
wget https://github.com/milvus-io/milvus/releases/download/v2.4.0/milvus-standalone-docker-compose.yml \
  -O docker-compose.yml

# 2. 一键启动
docker compose up -d

# 3. 检查状态
docker compose ps
# NAME         STATUS
# milvus-etcd         running
# milvus-minio        running
# milvus-standalone   running
```

```
Standalone 架构组件：

  ┌──────────────────────────────────────┐
  │          Milvus Standalone            │
  │                                      │
  │  ┌──────────┐  ┌──────────────────┐  │
  │  │   etcd    │  │  Milvus Server   │  │
  │  │ (元数据)  │  │  (核心引擎)       │  │
  │  └──────────┘  └──────────────────┘  │
  │  ┌──────────┐         ↑              │
  │  │  MinIO   │    端口 19530          │
  │  │ (对象存储)│    gRPC API            │
  │  └──────────┘                        │
  └──────────────────────────────────────┘

  • etcd：存储 Collection 元数据和配置
  • MinIO：存储向量数据和索引文件
  • Milvus Server：核心引擎，端口 19530
```

### 安装 Python SDK 并连接

```python
# 安装 pymilvus
# pip install pymilvus

from pymilvus import connections, utility

# --- 连接 Milvus ---
connections.connect(
    alias="default",     # 连接别名
    host="localhost",     # Milvus 地址
    port="19530"          # 默认端口
)

# 验证连接
print(f"已连接：{utility.get_server_version()}")

# --- 或者用 Milvus Lite（无需 Docker） ---
from pymilvus import MilvusClient

# Lite 模式：数据存在本地文件
client = MilvusClient("./milvus_demo.db")
```

### Milvus Lite vs pymilvus 两套 API

```
Milvus 提供两套 Python API：

  1. MilvusClient（新版简化 API）
     ─────────────────────────────────────
     from pymilvus import MilvusClient
     client = MilvusClient("./demo.db")    # Lite 模式
     client = MilvusClient(uri="http://localhost:19530")  # Server 模式
     → 更简洁，推荐新项目使用

  2. ORM 风格 API（传统 API）
     ─────────────────────────────────────
     from pymilvus import connections, Collection, FieldSchema
     connections.connect(host="localhost", port="19530")
     → 更灵活，适合需要精细控制的场景
     → 本教程两种都会展示

  选择建议：
    快速上手 / 简单项目 → MilvusClient
    生产级 / 需要细粒度控制 → ORM API
```

### 6.3 Schema 设计与数据写入

和 Chroma 的"无 Schema"不同，Milvus 要求**先定义字段结构**再插入数据——这和关系数据库的理念一致。

### 定义 Schema

```python
from pymilvus import (
    connections, Collection, CollectionSchema,
    FieldSchema, DataType, utility
)

connections.connect(host="localhost", port="19530")

# 定义字段
fields = [
    # 主键：每条记录的唯一标识
    FieldSchema(
        name="id",
        dtype=DataType.INT64,
        is_primary=True,
        auto_id=True       # 自动生成 ID
    ),

    # 标量字段：存储元数据
    FieldSchema(
        name="title",
        dtype=DataType.VARCHAR,
        max_length=512      # VARCHAR 必须指定最大长度
    ),
    FieldSchema(
        name="category",
        dtype=DataType.VARCHAR,
        max_length=64
    ),
    FieldSchema(
        name="word_count",
        dtype=DataType.INT64
    ),

    # 向量字段：存储 Embedding
    FieldSchema(
        name="embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=1024            # 向量维度，必须和 Embedding 模型一致
    ),
]

# 创建 Schema
schema = CollectionSchema(
    fields=fields,
    description="技术文档知识库"
)

# 创建 Collection
collection = Collection(
    name="tech_docs",
    schema=schema
)

print(f"Collection 创建成功：{collection.name}")
```

```
Milvus 支持的字段类型：

  向量类型：
    FLOAT_VECTOR    → 浮点向量（最常用）
    BINARY_VECTOR   → 二进制向量（省内存）
    FLOAT16_VECTOR  → 半精度浮点向量
    SPARSE_FLOAT_VECTOR → 稀疏向量（混合检索用）

  标量类型：
    BOOL            → 布尔值
    INT8 / INT16 / INT32 / INT64  → 整数
    FLOAT / DOUBLE  → 浮点数
    VARCHAR         → 字符串（需指定 max_length）
    JSON            → JSON 对象（灵活但查询较慢）
    ARRAY           → 数组类型
```

### 插入数据

```python
from sentence_transformers import SentenceTransformer
import random

# 准备 Embedding 模型
model = SentenceTransformer("BAAI/bge-large-zh-v1.5")

# 准备文档数据
docs = [
    {"title": "Python 异步编程完全指南",   "category": "python",   "word_count": 5000},
    {"title": "FastAPI 后端开发实战",       "category": "python",   "word_count": 8000},
    {"title": "React 组件设计模式",         "category": "frontend", "word_count": 6000},
    {"title": "Docker 容器化部署教程",      "category": "devops",   "word_count": 4000},
    {"title": "PostgreSQL 索引优化",       "category": "database", "word_count": 3000},
    {"title": "Redis 缓存策略详解",         "category": "database", "word_count": 4500},
    {"title": "Kubernetes 集群管理",       "category": "devops",   "word_count": 7000},
    {"title": "Python 装饰器与元编程",      "category": "python",   "word_count": 5500},
]

# 生成向量
titles = [d["title"] for d in docs]
embeddings = model.encode(titles, normalize_embeddings=True).tolist()

# 插入数据
collection.insert([
    titles,                                      # title 字段
    [d["category"] for d in docs],               # category 字段
    [d["word_count"] for d in docs],             # word_count 字段
    embeddings                                    # embedding 字段
])

# 刷新，确保数据持久化
collection.flush()

print(f"插入完成，总文档数：{collection.num_entities}")
```

> **批量插入性能**：Milvus 推荐每次 insert 1000-10000 条数据。如果有百万级数据要导入，用 `pymilvus` 的 `BulkInsert` 功能，速度可以提升 10 倍以上。

### 6.4 索引创建与搜索调优

数据插入后，必须**先建索引**才能高效搜索。

### 创建索引

```python
# 创建 HNSW 索引（推荐）
index_params = {
    "metric_type": "COSINE",     # 距离度量：COSINE / L2 / IP
    "index_type": "HNSW",        # 索引类型
    "params": {
        "M": 16,                  # 每层最大邻居数
        "efConstruction": 200     # 建索引搜索宽度
    }
}

collection.create_index(
    field_name="embedding",       # 对哪个字段建索引
    index_params=index_params
)

print("索引创建完成")

# 查看索引信息
print(collection.index().params)
```

### 加载到内存并搜索

```python
# ⚠️ 重要：搜索前必须先加载到内存
collection.load()

# 准备查询
query_text = "怎么提升 Python 后端性能"
query_embedding = model.encode([query_text], normalize_embeddings=True).tolist()

# 执行搜索
results = collection.search(
    data=query_embedding,                    # 查询向量
    anns_field="embedding",                  # 搜索哪个向量字段
    param={
        "metric_type": "COSINE",
        "params": {"ef": 128}                # HNSW 搜索宽度
    },
    limit=5,                                 # 返回 Top-5
    output_fields=["title", "category", "word_count"]  # 返回哪些字段
)

# 解析结果
for hits in results:
    for hit in hits:
        print(f"  ID: {hit.id}")
        print(f"  标题: {hit.entity.get('title')}")
        print(f"  分类: {hit.entity.get('category')}")
        print(f"  相似度: {hit.distance:.4f}")
        print(f"  ---")
```

### 带过滤条件的搜索

```python
# 搜索时加上标量过滤（类似 SQL WHERE）
results = collection.search(
    data=query_embedding,
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"ef": 128}},
    limit=5,
    expr='category == "python" and word_count > 3000',  # 过滤表达式
    output_fields=["title", "category", "word_count"]
)

# Milvus 的过滤表达式语法（类似 SQL）：
#   category == "python"          等于
#   word_count > 3000             大于
#   category in ["python", "database"]   在列表中
#   title like "Python%"          模糊匹配
#   category == "python" and word_count > 3000   AND 组合
#   category == "python" or category == "devops"  OR 组合
```

> **搜索性能调优**：`ef` 参数是搜索质量的关键旋钮。`ef=64` 速度快但可能漏结果，`ef=256` 结果更全但更慢。生产环境推荐从 `ef=128` 开始，根据实际召回率调整。

### 6.5 分区、别名与数据管理

### 分区（Partition）

分区是 Milvus 的一个重要特性——把数据按逻辑分组，搜索时可以只搜特定分区：

```python
# 创建分区
collection.create_partition("python_docs")
collection.create_partition("database_docs")

# 查看所有分区
print(collection.partitions)
# [{"name": "_default"}, {"name": "python_docs"}, {"name": "database_docs"}]

# 插入数据到指定分区
collection.insert(
    data=[titles, categories, word_counts, embeddings],
    partition_name="python_docs"
)

# 只在特定分区中搜索（更快）
results = collection.search(
    data=query_embedding,
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"ef": 128}},
    limit=5,
    partition_names=["python_docs"],  # 只搜 Python 分区
    output_fields=["title"]
)
```

```
分区 vs 元数据过滤：

  分区（Partition）：
    → 数据物理隔离，搜索时直接跳过其他分区
    → 性能更好，但分区数有上限（默认 1024）
    → 适合粗粒度分类：按租户、按大类

  元数据过滤（expr）：
    → 数据逻辑过滤，搜索时仍扫描全量索引
    → 更灵活，字段数无限制
    → 适合细粒度过滤：按标签、按时间范围

  最佳实践：大类用分区，小类用元数据过滤
```

### Collection 别名（Alias）

别名适合**无缝切换**数据版本——比如重建索引时：

```python
from pymilvus import utility

# 给 Collection 创建别名
utility.create_alias(collection_name="tech_docs", alias="prod_docs")

# 应用代码通过别名访问
collection = Collection("prod_docs")  # 实际指向 tech_docs

# 当你需要更新数据时：
# 1. 创建新 Collection "tech_docs_v2"，导入新数据
# 2. 切换别名指向
utility.alter_alias(collection_name="tech_docs_v2", alias="prod_docs")
# → 应用代码无需修改，自动指向新数据
# → 确认无问题后再删除旧 Collection
```

### 数据管理常用操作

```python
from pymilvus import utility

# --- 查看所有 Collection ---
print(utility.list_collections())

# --- 查看 Collection 信息 ---
print(f"文档数：{collection.num_entities}")
print(f"Schema：{collection.schema}")
print(f"索引：{collection.index().params}")

# --- 删除数据 ---
# 按表达式删除
collection.delete(expr='category == "frontend"')

# 按 ID 删除
collection.delete(expr="id in [1, 2, 3]")

# --- 释放内存 ---
collection.release()  # 从内存中卸载，不删数据

# --- 删除 Collection ---
utility.drop_collection("tech_docs")

# --- 断开连接 ---
connections.disconnect("default")
```

> **生产提示**：`collection.load()` 和 `collection.release()` 是 Milvus 特有的操作。数据必须 load 到内存才能搜索，release 后释放内存但数据仍在磁盘。合理管理 load/release 可以在多 Collection 场景下节省大量内存。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 三种部署 | Lite（学习）→ Standalone（中小生产）→ Distributed（大规模） |
| Docker 部署 | docker-compose 一键启动，端口 19530 |
| 两套 API | MilvusClient（简洁）和 ORM API（灵活） |
| Schema | 必须预定义字段类型，向量字段必须指定维度 |
| 数据插入 | 按字段列表插入，推荐每批 1000-10000 条 |
| 索引 | 必须建索引才能搜索，推荐 HNSW + COSINE |
| 搜索流程 | 建索引 → load → search → 解析结果 |
| 过滤表达式 | 类 SQL 语法：==、>、in、like、and/or |
| 分区 | 物理隔离数据，按租户/大类分区，搜索更快 |
| 别名 | 无缝切换数据版本，不影响应用代码 |

> **下一章预告**：混合检索——当语义搜索遇上关键词搜索。我们会探讨纯语义搜索的盲区，学习 Dense + Sparse 混合检索和 Reranker 重排序，用实测数据证明混合检索如何大幅提升召回精度。
