# 向量数据库实战（Milvus/Chroma）

> 从 Embedding 的第一个维度到 RAG 系统的最后一公里——手把手带你玩转向量数据库。

---

## 5. Chroma 实战——5 分钟上手向量数据库

前 4 章讲了原理，现在终于要**动手操作**了。

我们先从 Chroma 开始——它是最容易上手的向量数据库，`pip install` 之后 5 行代码就能跑起来。这一章你会学到 Chroma 的所有核心操作：创建集合、增删改查向量、元数据过滤、持久化存储。

---

### 5.1 安装与第一个 Collection

### 安装

```bash
pip install chromadb
```

就这一行。不需要 Docker，不需要配置文件，不需要启动服务。

### 创建第一个向量集合

```python
import chromadb

# 创建客户端（内存模式，数据在关闭后丢失）
client = chromadb.Client()

# 创建一个 Collection（类似关系数据库中的"表"）
collection = client.create_collection(
    name="my_docs",
    metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
)

print(f"集合名称：{collection.name}")
print(f"当前文档数量：{collection.count()}")  # 0
```

```
Chroma 的核心概念映射：

  关系数据库           Chroma
  ─────────────────────────────────
  Database             Client
  Table                Collection
  Row                  Document（文档 + 向量 + 元数据）
  PRIMARY KEY          id
  Column               metadata 字段
  SELECT               query / get
  INSERT               add
  UPDATE               update
  DELETE               delete
```

### 添加第一批文档

Chroma 最方便的一点：**你不需要自己生成 Embedding**。它内置了一个默认的 Embedding 模型（all-MiniLM-L6-v2），直接传文本就行：

```python
# 添加文档——Chroma 自动帮你生成向量
collection.add(
    documents=[
        "Python 异步编程完全指南",
        "FastAPI 后端开发实战",
        "React 前端组件设计模式",
        "Docker 容器化部署教程",
        "PostgreSQL 索引优化技巧",
    ],
    ids=["doc1", "doc2", "doc3", "doc4", "doc5"],  # 每条必须有唯一 ID
    metadatas=[
        {"category": "python", "level": "advanced"},
        {"category": "python", "level": "intermediate"},
        {"category": "frontend", "level": "intermediate"},
        {"category": "devops", "level": "beginner"},
        {"category": "database", "level": "advanced"},
    ]
)

print(f"文档数量：{collection.count()}")  # 5
```

### 第一次语义搜索

```python
# 语义搜索——Chroma 自动把查询文本向量化，然后搜索最相似的文档
results = collection.query(
    query_texts=["怎么提升 Python 后端性能"],  # 用自然语言搜索
    n_results=3  # 返回 Top-3
)

print(results["documents"])
# ['FastAPI 后端开发实战',]('FastAPI 后端开发实战',#---'python-异步编程完全指南',
#---'postgresql-索引优化技巧')

print(results["distances"])
# [0.52, 0.61, 0.89](0.52, 0.61, 0.89)  # 距离越小越相似
```

> **5 行代码的魔力**：安装 → 创建集合 → 添加文档 → 搜索。从零到一个可用的语义搜索系统，只用了 5 分钟。

### 5.2 完整 CRUD：增删改查向量

实际项目中，你需要对向量数据做完整的增删改查。

### 增（Add）

```python
# 方式 1：传文本，Chroma 自动生成向量
collection.add(
    documents=["新的文档内容"],
    ids=["doc6"],
    metadatas=[{"category": "python", "level": "beginner"}]
)

# 方式 2：自己提供向量（用自己的 Embedding 模型）
collection.add(
    embeddings=[0.12, -0.34, 0.56, ...](0.12, -0.34, 0.56, ...),  # 你自己生成的向量
    documents=["文档原文"],                    # 可选，存原文方便后续使用
    ids=["doc7"],
    metadatas=[{"source": "manual"}]
)

# 方式 3：批量添加（推荐，效率更高）
collection.add(
    documents=["文档A", "文档B", "文档C"],
    ids=["batch1", "batch2", "batch3"],
    metadatas=[
        {"category": "a"},
        {"category": "b"},
        {"category": "c"}
    ]
)
```

### 查（Get / Query）

```python
# --- 按 ID 精确查询 ---
result = collection.get(ids=["doc1", "doc2"])
print(result["documents"])   # ['Python 异步编程完全指南', 'FastAPI 后端开发实战']
print(result["metadatas"])   # [{'category': 'python', ...}, ...]

# --- 按语义搜索（最常用） ---
results = collection.query(
    query_texts=["数据库优化"],
    n_results=3,
    include=["documents", "metadatas", "distances"]  # 指定返回哪些字段
)

# --- 获取所有文档 ---
all_docs = collection.get()
print(f"总文档数：{len(all_docs['ids'])}")

# --- 按元数据条件查询 ---
python_docs = collection.get(
    where={"category": "python"}  # 只返回 category 为 python 的文档
)
```

### 改（Update / Upsert）

```python
# --- Update：更新已有文档 ---
collection.update(
    ids=["doc1"],
    documents=["Python 异步编程完全指南（第二版）"],  # 更新文本
    metadatas=[{"category": "python", "level": "advanced", "version": 2}]
)

# --- Upsert：存在则更新，不存在则插入 ---
collection.upsert(
    ids=["doc1", "doc_new"],
    documents=[
        "Python 异步编程完全指南（第三版）",  # 已存在 → 更新
        "Rust 系统编程入门"                  # 不存在 → 插入
    ],
    metadatas=[
        {"category": "python", "version": 3},
        {"category": "rust", "level": "beginner"}
    ]
)
```

> **推荐用 Upsert**：在数据导入场景中，`upsert` 比 `add` 更安全——不用担心重复 ID 导致报错。

### 删（Delete）

```python
# --- 按 ID 删除 ---
collection.delete(ids=["doc3", "doc4"])

# --- 按条件删除 ---
collection.delete(
    where={"category": "frontend"}  # 删除所有前端分类的文档
)

# --- 删除整个 Collection ---
client.delete_collection("my_docs")
```

### 5.3 元数据过滤与混合查询

单纯的语义搜索有时不够用——你可能想"只在某个分类下搜索"或"只搜索最近更新的文档"。这就是**元数据过滤**。

### where 条件语法

```python
# --- 基础比较 ---
collection.query(
    query_texts=["Python 教程"],
    n_results=5,
    where={"category": "python"}           # 等于
)

collection.query(
    query_texts=["入门教程"],
    n_results=5,
    where={"level": {"$ne": "advanced"}}   # 不等于
)

# --- 数值比较 ---
collection.query(
    query_texts=["最新文档"],
    n_results=5,
    where={"version": {"$gt": 2}}          # 大于
)

# 所有支持的操作符：
# $eq   等于（默认）
# $ne   不等于
# $gt   大于
# $gte  大于等于
# $lt   小于
# $lte  小于等于
# $in   在列表中
# $nin  不在列表中
```

### 逻辑组合（AND / OR）

```python
# --- AND：同时满足多个条件 ---
collection.query(
    query_texts=["性能优化"],
    n_results=5,
    where={
        "$and": [
            {"category": "python"},
            {"level": "advanced"}
        ]
    }
)

# --- OR：满足任一条件 ---
collection.query(
    query_texts=["编程教程"],
    n_results=5,
    where={
        "$or": [
            {"category": "python"},
            {"category": "rust"}
        ]
    }
)

# --- 组合嵌套 ---
collection.query(
    query_texts=["后端开发"],
    n_results=5,
    where={
        "$and": [
            {"$or": [
                {"category": "python"},
                {"category": "database"}
            ]},
            {"level": {"$ne": "beginner"}}
        ]
    }
)
```

### where_document：按文档内容过滤

```python
# 除了 metadata 过滤，还可以按文档原文内容过滤
collection.query(
    query_texts=["编程入门"],
    n_results=5,
    where_document={"$contains": "Python"}  # 文档文本必须包含 "Python"
)
```

### 混合查询的典型应用

```
混合查询 = 语义搜索 + 元数据过滤

  场景：企业知识库问答
  ─────────────────────────────────────────

  用户问："怎么部署 Python 服务？"

  纯语义搜索：
    → 可能返回 Java 部署文档（语义相近但分类不对）

  混合查询：
    query_texts = "怎么部署 Python 服务？"
    where = {"category": "python"}
    → 只在 Python 分类中做语义搜索
    → 结果更精确

  场景：多租户 SaaS 系统
  ─────────────────────────────────────────
    → 每个租户的文档用 tenant_id 标记
    → 搜索时 where={"tenant_id": "company_a"}
    → 确保租户间数据隔离
```

> **最佳实践**：在设计元数据时，提前想好可能的过滤维度（分类、标签、时间、来源、权限等级）。好的元数据设计能让搜索精度提升一个台阶。

### 5.4 持久化与 Client-Server 模式

到目前为止，我们用的都是 `chromadb.Client()`——纯内存模式，程序关闭数据就没了。生产环境需要**持久化**。

### 持久化存储

```python
import chromadb

# 持久化客户端——数据保存到本地目录
client = chromadb.PersistentClient(path="./chroma_data")

# 后续操作完全一样
collection = client.get_or_create_collection("my_docs")

collection.add(
    documents=["Python 异步编程指南", "FastAPI 实战教程"],
    ids=["doc1", "doc2"],
    metadatas=[
        {"category": "python"},
        {"category": "python"}
    ]
)

# 程序关闭后再次打开，数据还在
# client = chromadb.PersistentClient(path="./chroma_data")
# collection = client.get_collection("my_docs")
# print(collection.count())  # 2 → 数据还在！
```

```
持久化目录结构：

  ./chroma_data/
  ├── chroma.sqlite3         ← 元数据和 ID 映射
  └── collections/
      └── my_docs/
          ├── data_level0.bin ← HNSW 索引数据
          └── length.bin      ← 向量长度信息

  注意事项：
    • 这个目录就是你的"数据库文件"，备份它 = 备份数据库
    • 不要手动修改目录里的文件
    • 多个进程不能同时写同一个目录
```

### Client-Server 模式

当多个应用需要共享同一个 Chroma 实例时，需要 Server 模式：

```bash
# 启动 Chroma Server
# 方式 1：命令行启动
chroma run --host 0.0.0.0 --port 8000 --path ./chroma_data

# 方式 2：Docker 启动（推荐）
docker run -d \
  --name chroma \
  -p 8000:8000 \
  -v ./chroma_data:/chroma/chroma \
  chromadb/chroma:latest
```

```python
import chromadb

# 连接远程 Server
client = chromadb.HttpClient(host="localhost", port=8000)

# 后续操作完全一样
collection = client.get_or_create_collection("my_docs")
collection.add(
    documents=["通过 HTTP 添加的文档"],
    ids=["remote_doc1"]
)

results = collection.query(query_texts=["搜索测试"], n_results=3)
print(results["documents"])
```

```
三种模式对比：

  ┌───────────────────┬──────────┬───────────┬──────────────┐
  │ 模式               │ 内存模式  │ 持久化模式 │ Server 模式   │
  ├───────────────────┼──────────┼───────────┼──────────────┤
  │ 创建方式            │ Client() │ Persistent│ HttpClient() │
  │                   │          │ Client()  │              │
  │ 数据是否持久化       │ ❌       │ ✅        │ ✅            │
  │ 多进程访问          │ ❌       │ ❌        │ ✅            │
  │ 适合场景            │ 测试/原型 │ 单机应用   │ 多服务共享    │
  │ 部署复杂度          │ 零       │ 零         │ 中等          │
  └───────────────────┴──────────┴───────────┴──────────────┘
```

### 使用自定义 Embedding 模型

默认的 all-MiniLM-L6-v2 对中文支持很弱。生产项目推荐换成更好的模型：

```python
import chromadb
from chromadb.utils.embedding_functions import (
    OpenAIEmbeddingFunction,
    SentenceTransformerEmbeddingFunction
)

# --- 方案 1：用 OpenAI Embedding ---
openai_ef = OpenAIEmbeddingFunction(
    api_key="sk-your-key",
    model_name="text-embedding-3-small"
)

collection = client.create_collection(
    name="my_docs_openai",
    embedding_function=openai_ef
)

# --- 方案 2：用本地 BGE 模型（中文推荐） ---
bge_ef = SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-large-zh-v1.5"
)

collection = client.create_collection(
    name="my_docs_bge",
    embedding_function=bge_ef
)

# 后续操作完全一样——add 和 query 时，
# Chroma 会自动用你指定的模型生成向量
```

> **重要提醒**：一个 Collection 一旦选定了 Embedding 模型，就**不能更换**。如果要换模型，必须创建新的 Collection 并重新导入所有数据。这是因为不同模型生成的向量空间完全不同，无法混用。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 安装 | `pip install chromadb`，零配置开箱即用 |
| Collection | 类似数据库中的表，存储向量 + 文档 + 元数据 |
| 自动 Embedding | 传文本即可，Chroma 自动向量化 |
| CRUD | add / get / query / update / upsert / delete |
| 元数据过滤 | where 条件支持 $eq / $gt / $lt / $and / $or 等 |
| 混合查询 | 语义搜索 + 元数据过滤，精度更高 |
| 持久化 | `PersistentClient(path=...)`，数据存本地目录 |
| Server 模式 | Docker 部署，多服务共享，通过 HttpClient 连接 |
| 自定义模型 | 中文场景务必换成 BGE 或 OpenAI Embedding |

> **下一章预告**：Milvus 实战——生产级向量数据库。我们会从 Docker 部署开始，学习 Milvus 的 Schema 设计、索引创建、搜索调优、分区管理，掌握生产环境中向量数据库的完整操作。
