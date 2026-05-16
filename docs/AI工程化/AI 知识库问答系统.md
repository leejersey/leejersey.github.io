# AI 知识库问答系统

> 从零构建一个企业级知识库问答系统——涵盖文档导入与解析、智能分块策略、向量化与检索、RAG 问答引擎、引用溯源与可信度、多轮对话与上下文、权限控制与多租户、部署与效果评估，一套完整方案让企业知识真正被 AI 用起来。

---

## 1. 产品定义与架构设计

### 1.1 知识库问答系统能解决什么问题

```
企业知识的三大痛点：

  ① 知识散落 ── 文档在 Confluence、飞书、语雀、本地硬盘里
     "这个接口的文档在哪？" → 找了 30 分钟没找到

  ② 知识过时 ── 文档写了但没人更新
     "这个配置参数是什么意思？" → 文档是两年前的，已经不对了

  ③ 知识获取慢 ── 搜索引擎只能匹配关键词
     "新人入职要准备什么？" → 搜出 50 篇文档，不知道看哪篇

  AI 知识库问答系统的解决方案：
     用户用自然语言提问 → 系统从企业文档中找到答案 → 附上原文引用
     "新人入职第一天需要做什么？"
     → "根据《新人入职指南》，第一天需要完成以下步骤：1. ..."
        📎 来源：新人入职指南.pdf 第 3 页
```

### 1.2 核心流程：导入 → 分块 → 向量化 → 检索 → 生成 → 引用

```
知识库问答的六步流程：

  离线阶段（文档入库）：
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ ① 文档导入 │ → │ ② 智能分块 │ → │ ③ 向量化  │
  │ PDF/Word  │   │ 语义切分  │   │ Embedding │
  └──────────┘   └──────────┘   └─────┬────┘
                                       │ 存入向量库
  在线阶段（用户提问）：                    ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ ④ 检索    │ → │ ⑤ 生成    │ → │ ⑥ 引用    │
  │ 向量+关键词│   │ RAG 问答  │   │ 来源标注  │
  └──────────┘   └──────────┘   └──────────┘
```

### 1.3 整体架构设计

```
系统架构：

  用户（Web / 飞书Bot / API）
    │
    ▼
  ┌──────────────────────────────────────┐
  │           问答服务层                    │
  │  ┌──────────┐  ┌──────────┐         │
  │  │ 对话管理   │  │ 意图识别   │         │
  │  └──────────┘  └──────────┘         │
  │  ┌──────────┐  ┌──────────┐         │
  │  │ RAG 引擎  │  │ 引用生成   │         │
  │  └──────────┘  └──────────┘         │
  └──────┬───────────────┬──────────────┘
         │               │
  ┌──────┴──────┐ ┌──────┴──────────────┐
  │  检索层      │ │    文档处理层         │
  │ ┌─────────┐ │ │ ┌────────┐ ┌──────┐│
  │ │向量检索  │ │ │ │文档解析 │ │分块  ││
  │ │关键词检索│ │ │ └────────┘ └──────┘│
  │ │Rerank   │ │ │ ┌────────┐ ┌──────┐│
  │ └─────────┘ │ │ │向量化   │ │元数据││
  └──────┬──────┘ │ └────────┘ └──────┘│
         │        └────────────────────┘
  ┌──────┴──────┐
  │  存储层      │
  │ Milvus│Redis│PostgreSQL
  └─────────────┘
```

### 1.4 技术选型：向量库 / 模型 / 框架

| 组件 | 选型 | 理由 |
|:---|:---|:---|
| **Embedding** | BGE-M3 / text-embedding-3 | 中文效果好、多语言 |
| **向量库** | Milvus / Qdrant | 生产级、支持过滤 |
| **LLM** | DeepSeek-V3 | 中文优、性价比高 |
| **文档解析** | Unstructured / PyMuPDF | 多格式支持 |
| **后端** | FastAPI | 异步 + 流式 |
| **Rerank** | BGE-Reranker / Cohere | 精排提升准确率 |

> 💡 **知识库问答 = RAG，但比简单 RAG 难 10 倍**——生产级系统需要处理格式复杂的文档、保证引用准确、支持权限控制、实现增量更新。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **三大痛点** | 知识散落、过时、获取慢 |
| **六步流程** | 导入→分块→向量化→检索→生成→引用 |
| **架构分层** | 问答服务 + 检索层 + 文档处理 + 存储 |
| **核心差异** | 比简单 RAG 多了引用、权限、增量 |

---

## 2. 文档导入与解析：让 AI 读懂企业知识

### 2.1 多格式文档解析：PDF / Word / Markdown / HTML

```python
class DocumentParser:
    """多格式文档解析器"""
    
    PARSERS = {
        ".pdf": "_parse_pdf",
        ".docx": "_parse_docx",
        ".md": "_parse_markdown",
        ".html": "_parse_html",
        ".txt": "_parse_text",
        ".pptx": "_parse_pptx",
    }
    
    def parse(self, file_path: str) -> list[dict]:
        """解析文档，返回页面/段落列表"""
        ext = Path(file_path).suffix.lower()
        parser = getattr(self, self.PARSERS.get(ext, "_parse_text"))
        return parser(file_path)
    
    def _parse_pdf(self, path: str) -> list[dict]:
        """PDF 解析（PyMuPDF）"""
        import fitz
        doc = fitz.open(path)
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text("text")
            pages.append({
                "content": text,
                "page": i + 1,
                "metadata": {"source": path, "page": i + 1, "type": "pdf"},
            })
        return pages
    
    def _parse_docx(self, path: str) -> list[dict]:
        """Word 文档解析"""
        from docx import Document
        doc = Document(path)
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append({
                    "content": para.text,
                    "metadata": {"source": path, "style": para.style.name},
                })
        return paragraphs
```

### 2.2 复杂文档处理：表格 / 图片 / 代码块

```python
class TableExtractor:
    """PDF/Word 中的表格提取"""
    
    def extract_tables(self, path: str) -> list[dict]:
        import fitz
        doc = fitz.open(path)
        tables = []
        for page in doc:
            for table in page.find_tables():
                df = table.to_pandas()
                # 表格转为 Markdown 格式，方便 LLM 理解
                md_table = df.to_markdown(index=False)
                tables.append({
                    "content": md_table,
                    "metadata": {"type": "table", "page": page.number + 1},
                })
        return tables

class ImageHandler:
    """文档中的图片处理"""
    
    async def process_images(self, path: str) -> list[dict]:
        """用多模态模型提取图片中的文字信息"""
        import fitz
        doc = fitz.open(path)
        results = []
        for page in doc:
            for img in page.get_images():
                pix = fitz.Pixmap(doc, img[0])
                # 用多模态 LLM 描述图片内容
                description = await self.describe_image(pix.tobytes())
                results.append({
                    "content": f"[图片描述] {description}",
                    "metadata": {"type": "image", "page": page.number + 1},
                })
        return results
```

### 2.3 元数据提取：标题 / 作者 / 日期 / 标签

```python
class MetadataExtractor:
    """文档元数据提取"""
    
    def extract(self, path: str, content: str) -> dict:
        filename = Path(path).stem
        return {
            "filename": filename,
            "file_type": Path(path).suffix,
            "file_size": Path(path).stat().st_size,
            "modified_at": datetime.fromtimestamp(Path(path).stat().st_mtime),
            "title": self._extract_title(content, filename),
            "tags": self._extract_tags(content),
        }
    
    def _extract_title(self, content: str, fallback: str) -> str:
        """提取文档标题"""
        lines = content.strip().split("\n")
        for line in lines[:5]:
            if line.startswith("# ") or len(line.strip()) < 50:
                return line.strip().lstrip("# ")
        return fallback
```

### 2.4 增量更新：文档变更的自动同步

```python
class IncrementalUpdater:
    """增量更新：只处理变化的文档"""
    
    async def sync(self, doc_dir: str):
        """扫描目录，只处理新增/修改的文档"""
        current_files = self._scan_files(doc_dir)
        
        for path, mtime in current_files.items():
            existing = await self.db.get_doc_record(path)
            
            if not existing:
                # 新文档 → 全量处理
                await self._process_new(path)
            elif existing["modified_at"] < mtime:
                # 文档已修改 → 删旧入新
                await self._process_updated(path, existing["doc_id"])
        
        # 检查已删除的文档
        stored_paths = await self.db.get_all_paths()
        for path in stored_paths:
            if path not in current_files:
                await self._process_deleted(path)
    
    async def _process_updated(self, path: str, doc_id: str):
        """处理更新的文档：删除旧向量 → 重新解析入库"""
        await self.vector_store.delete(filter={"doc_id": doc_id})
        await self._process_new(path)
```

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **多格式解析** | PyMuPDF(PDF) + python-docx(Word) + 统一接口 |
| **复杂内容** | 表格转 Markdown、图片用多模态模型描述 |
| **元数据** | 文件名/类型/日期/标题/标签 |
| **增量更新** | 比较修改时间，增/改/删三种处理 |

---

## 3. 智能分块：切得好才答得准

### 3.1 为什么分块决定了问答质量

```
分块不好的三种灾难：

  ① 分块太大（2000+ Token）
     → 检索到的 Chunk 包含太多无关内容
     → LLM 被噪音干扰，回答不精确

  ② 分块太小（< 100 Token）
     → 一个知识点被切成多段，语义不完整
     → "什么是微服务？" 只检索到 "微服务是一种..."，缺少后半句

  ③ 切割位置不对
     → 把表格切成两半、把代码块切断
     → LLM 看到残缺的信息，生成错误答案

  → 好分块的标准：语义完整 + 大小适中 + 保留上下文
```

### 3.2 分块策略对比：固定 / 递归 / 语义 / 文档结构

| 策略 | 原理 | 优势 | 劣势 | 适用场景 |
|:---|:---|:---|:---|:---|
| **固定大小** | 按字符数硬切 | 简单 | 语义割裂 | 纯文本 |
| **递归分割** | 按 \n\n → \n → 句子递归 | 尊重段落 | 不识别语义 | 通用 |
| **语义分块** | 用 Embedding 相似度找断点 | 语义完整 | 速度慢 | 高质量需求 |
| **文档结构** | 按标题层级切分 | 保持结构 | 需要格式规范 | Markdown/HTML |

```python
class SmartChunker:
    """智能分块器"""
    
    def chunk_by_structure(self, text: str) -> list[dict]:
        """按文档结构分块（Markdown）"""
        import re
        chunks = []
        # 按一级/二级标题切分
        sections = re.split(r'\n(?=#{1,2}\s)', text)
        
        for section in sections:
            if len(section.strip()) < 50:
                continue
            
            # 提取标题
            lines = section.strip().split('\n')
            title = lines[0].lstrip('#').strip() if lines[0].startswith('#') else ""
            content = '\n'.join(lines[1:]).strip()
            
            # 如果单个 section 太长，递归再切
            if len(content) > 1500:
                sub_chunks = self._recursive_split(content, max_size=800)
                for i, sub in enumerate(sub_chunks):
                    chunks.append({"content": sub, "title": title, "part": i+1})
            else:
                chunks.append({"content": content, "title": title})
        
        return chunks
```

### 3.3 Chunk 大小与 Overlap 的调优

```python
# ── 推荐参数 ──
CHUNK_CONFIGS = {
    "技术文档": {"chunk_size": 500, "overlap": 100, "strategy": "structure"},
    "FAQ": {"chunk_size": 300, "overlap": 50, "strategy": "fixed"},
    "法律合同": {"chunk_size": 800, "overlap": 200, "strategy": "recursive"},
    "会议纪要": {"chunk_size": 400, "overlap": 80, "strategy": "semantic"},
}

# ── A/B 测试不同参数 ──
# chunk_size=300: 召回高但精度低（太多碎片）
# chunk_size=500: 平衡点 ✅
# chunk_size=800: 精度高但召回低（相关内容可能在大块中被淹没）
# overlap=0: 切割处信息丢失
# overlap=100: 边界信息保留 ✅
# overlap=200: 冗余增加，存储成本上升
```

### 3.4 保持层级关系：父子 Chunk 与上下文增强

```python
class HierarchicalChunker:
    """父子 Chunk：小 Chunk 检索，大 Chunk 回答"""
    
    def create_parent_child(self, text: str) -> list[dict]:
        """创建两级 Chunk"""
        # 父 Chunk：大块（1500 字）
        parent_chunks = self._split(text, size=1500, overlap=200)
        
        all_chunks = []
        for i, parent in enumerate(parent_chunks):
            parent_id = f"parent_{i}"
            
            # 子 Chunk：小块（300 字），用于检索
            children = self._split(parent, size=300, overlap=50)
            
            for j, child in enumerate(children):
                all_chunks.append({
                    "content": child,
                    "parent_content": parent,  # 保存父级全文
                    "parent_id": parent_id,
                    "chunk_id": f"{parent_id}_child_{j}",
                    "type": "child",
                })
        
        return all_chunks
    
    # 检索时：用子 Chunk 匹配，但返回父 Chunk 给 LLM
    # → 检索精度高（小块匹配），回答质量高（大块上下文完整）
```

> 💡 **父子 Chunk 是生产级 RAG 的标配**——检索用小 Chunk（精准匹配），回答用大 Chunk（上下文完整）。这个技巧能同时提升召回率和答案质量。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **分块重要性** | 太大噪音多、太小语义断、切错位置答错 |
| **推荐策略** | 结构化文档用标题切分，通用用递归 |
| **推荐参数** | chunk_size=500, overlap=100 |
| **父子 Chunk** | 小 Chunk 检索 + 大 Chunk 回答 |

---

## 4. 向量化与检索：找到最相关的知识

### 4.1 Embedding 模型选型与评测

| 模型 | 维度 | 中文能力 | 速度 | 特点 |
|:---|:---|:---|:---|:---|
| **BGE-M3** | 1024 | ⭐⭐⭐⭐⭐ | 中 | 多语言、本地部署 |
| **text-embedding-3-small** | 1536 | ⭐⭐⭐⭐ | 快 | OpenAI API、便宜 |
| **text-embedding-3-large** | 3072 | ⭐⭐⭐⭐ | 快 | 精度最高、贵 |
| **M3E-large** | 768 | ⭐⭐⭐⭐ | 快 | 国产、可私有部署 |
| **GTE-Qwen2** | 1536 | ⭐⭐⭐⭐⭐ | 中 | 阿里、免费 |

```python
class EmbeddingService:
    """Embedding 统一接口"""
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""
        # 使用 BGE-M3（本地部署 or API）
        response = await self.client.post("/embed", json={
            "texts": texts,
            "model": "bge-m3",
        })
        return response.json()["embeddings"]
    
    async def embed_query(self, query: str) -> list[float]:
        """查询向量化（加 instruction prefix）"""
        # BGE 系列需要给 query 加前缀
        prefixed = f"为这个句子生成表示以用于检索相关文章：{query}"
        return (await self.embed([prefixed]))[0]
```

### 4.2 向量数据库配置：Milvus / Qdrant / Chroma

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class VectorStore:
    """向量存储（Qdrant 示例）"""
    
    def __init__(self, url: str = "localhost:6333"):
        self.client = QdrantClient(url=url)
        self.collection = "knowledge_base"
    
    def create_collection(self, dim: int = 1024):
        """创建集合"""
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
    
    async def upsert(self, chunks: list[dict], embeddings: list):
        """写入向量"""
        points = [
            PointStruct(
                id=chunk["chunk_id"],
                vector=emb,
                payload={
                    "content": chunk["content"],
                    "source": chunk["metadata"]["source"],
                    "title": chunk.get("title", ""),
                    "page": chunk["metadata"].get("page"),
                    "doc_id": chunk["doc_id"],
                },
            )
            for chunk, emb in zip(chunks, embeddings)
        ]
        self.client.upsert(collection_name=self.collection, points=points)
    
    async def search(self, query_vector: list, top_k: int = 10,
                      filters: dict = None) -> list:
        """向量检索"""
        return self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filters,
        )
```

### 4.3 混合检索：向量 + 关键词 + 元数据过滤

```python
class HybridRetriever:
    """混合检索：向量 + BM25 + 元数据过滤"""
    
    async def retrieve(self, query: str, top_k: int = 10,
                        filters: dict = None) -> list[dict]:
        """混合检索"""
        # 1. 向量检索
        query_vec = await self.embedding.embed_query(query)
        vector_results = await self.vector_store.search(query_vec, top_k=top_k*2)
        
        # 2. BM25 关键词检索
        bm25_results = self.bm25_index.search(query, top_k=top_k*2)
        
        # 3. 融合排序（RRF = Reciprocal Rank Fusion）
        combined = self._rrf_fusion(vector_results, bm25_results)
        
        # 4. 元数据过滤
        if filters:
            combined = [r for r in combined if self._match_filter(r, filters)]
        
        return combined[:top_k]
    
    def _rrf_fusion(self, *result_lists, k=60) -> list:
        """RRF 融合多路检索结果"""
        scores = {}
        for results in result_lists:
            for rank, result in enumerate(results):
                doc_id = result["chunk_id"]
                scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

### 4.4 Rerank 精排：提升检索精度

```python
class Reranker:
    """Rerank 精排"""
    
    async def rerank(self, query: str, documents: list[dict],
                      top_k: int = 5) -> list[dict]:
        """用 Cross-Encoder 精排"""
        # 调用 BGE-Reranker 或 Cohere Rerank API
        pairs = [(query, doc["content"]) for doc in documents]
        
        scores = await self.rerank_model.predict(pairs)
        
        ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked[:top_k]]
```

> 💡 **检索三板斧：向量召回 → BM25 补充 → Rerank 精排**——向量检索擅长语义匹配（"如何部署" ≈ "怎么上线"），BM25 擅长关键词匹配（专有名词），Rerank 做最后精排。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Embedding** | BGE-M3 中文最优，1024 维 |
| **向量库** | Qdrant/Milvus，支持过滤+高性能 |
| **混合检索** | 向量 + BM25 + RRF 融合 |
| **Rerank** | Cross-Encoder 精排 Top 5 |

---

## 5. RAG 问答引擎：检索增强的答案生成

### 5.1 RAG Prompt 工程：让 LLM 基于文档回答

```python
RAG_PROMPT = """你是一个知识库问答助手。请严格根据以下参考文档来回答用户问题。

## 规则
1. 只使用参考文档中的信息来回答
2. 如果文档中没有答案，请明确告知"根据现有知识库文档，未找到相关信息"
3. 在回答中标注引用来源，格式：[来源：文档名 第X页]
4. 不要编造文档中不存在的信息
5. 如果多个文档有不同说法，请指出差异

## 参考文档
{context}

## 用户问题
{question}

请回答："""

class RAGEngine:
    """RAG 问答引擎"""
    
    async def answer(self, question: str, top_k: int = 5) -> dict:
        """RAG 问答"""
        # 1. 检索相关文档
        docs = await self.retriever.retrieve(question, top_k=top_k * 2)
        
        # 2. Rerank 精排
        docs = await self.reranker.rerank(question, docs, top_k=top_k)
        
        # 3. 组装上下文
        context = self._build_context(docs)
        
        # 4. LLM 生成
        prompt = RAG_PROMPT.format(context=context, question=question)
        
        response = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0.1, stream=True)
        
        return {
            "answer": response,
            "sources": [{"title": d["title"], "source": d["source"],
                         "page": d.get("page")} for d in docs],
        }
    
    def _build_context(self, docs: list[dict]) -> str:
        """组装上下文"""
        parts = []
        for i, doc in enumerate(docs):
            source = f"{doc['title']} (来源: {doc['source']}, 第{doc.get('page', '?')}页)"
            parts.append(f"### 文档 {i+1}: {source}\n{doc['content']}\n")
        return "\n".join(parts)
```

### 5.2 上下文窗口管理：多文档拼接策略

```python
class ContextManager:
    """上下文窗口管理"""
    
    MAX_CONTEXT_TOKENS = 8000  # 留给上下文的 Token 预算
    
    def select_documents(self, docs: list[dict]) -> list[dict]:
        """在 Token 预算内选择最相关的文档"""
        selected = []
        used_tokens = 0
        
        for doc in docs:
            doc_tokens = len(doc["content"]) // 1.5  # 粗略估算
            
            if used_tokens + doc_tokens > self.MAX_CONTEXT_TOKENS:
                # 预算不够了，用摘要代替
                summary = doc["content"][:200] + "..."
                selected.append({**doc, "content": summary, "truncated": True})
                break
            
            selected.append(doc)
            used_tokens += doc_tokens
        
        return selected
```

### 5.3 "我不知道"的勇气：拒答与兜底

```python
class RefusalDetector:
    """判断是否应该拒绝回答"""
    
    async def should_refuse(self, question: str, docs: list[dict]) -> dict:
        """判断知识库是否能回答该问题"""
        # 检查检索分数
        if not docs or docs[0].get("score", 0) < 0.5:
            return {"refuse": True, "reason": "未找到相关文档",
                    "suggestion": "请尝试用其他关键词提问"}
        
        # 检查文档相关性
        relevance_prompt = f"""判断以下文档是否能回答用户问题。
问题：{question}
文档摘要：{docs[0]['content'][:300]}
回复 JSON：{{"relevant": true/false, "confidence": 0-1}}"""
        
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": relevance_prompt}
        ], temperature=0)
        
        check = json.loads(result.choices[0].message.content)
        if not check["relevant"] or check["confidence"] < 0.3:
            return {"refuse": True, "reason": "文档与问题相关性不足"}
        
        return {"refuse": False}
```

### 5.4 答案质量控制：幻觉检测与事实核验

```python
class HallucinationDetector:
    """幻觉检测：检查答案是否有文档依据"""
    
    async def check(self, answer: str, source_docs: list[dict]) -> dict:
        prompt = f"""检查以下回答中是否有无法在参考文档中找到依据的信息（幻觉）。

回答：{answer}

参考文档：
{chr(10).join([d['content'] for d in source_docs])}

检查每个关键事实是否有出处。
回复 JSON：
{{
  "has_hallucination": true/false,
  "unsupported_claims": ["没有依据的描述1", ...],
  "confidence": 0-1
}}"""
        
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0)
        
        return json.loads(result.choices[0].message.content)
```

> 💡 **"我不知道"比"编一个答案"强 100 倍**——知识库问答的信任基石是准确性，一旦用户发现 AI 编造答案，就再也不会信任这个系统。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **RAG Prompt** | 文档上下文 + 严格引用规则 |
| **窗口管理** | 8000 Token 预算内优先选最相关文档 |
| **拒答机制** | 检索分低或相关性差就拒绝回答 |
| **幻觉检测** | 核验答案中每个事实是否有文档依据 |

---

## 6. 引用溯源：每句话都有出处

### 6.1 引用生成：让 LLM 标注来源

```python
CITATION_PROMPT = """回答用户问题时，请在每个关键事实后标注引用来源。

引用格式：在回答末尾列出引用，格式如下：
[1] 文档名, 第X页
[2] 文档名, 第X页

在回答文本中用上标 [1] [2] 标记引用位置。

参考文档：
{context}

用户问题：{question}

示例输出格式：
微服务架构的核心原则是服务自治[1]。每个服务独立部署[1]，通过 API 通信[2]。

引用：
[1] 微服务设计指南.pdf, 第5页
[2] API 规范文档.md, 第2节"""
```

### 6.2 引用验证：检查引用是否真实

```python
class CitationVerifier:
    """引用验证器"""
    
    def verify(self, answer: str, source_docs: list[dict]) -> dict:
        """检查回答中的引用是否真实"""
        import re
        
        # 提取引用标记 [1] [2] ...
        citations = re.findall(r'\[(\d+)\]', answer)
        
        # 提取引用列表
        citation_list = re.findall(r'\[(\d+)\]\s*(.+)', answer)
        
        results = {"verified": [], "invalid": [], "missing": []}
        
        for num, ref_text in citation_list:
            # 在源文档中搜索引用内容
            found = False
            for doc in source_docs:
                if self._fuzzy_match(ref_text, doc):
                    results["verified"].append({"citation": num, "ref": ref_text})
                    found = True
                    break
            
            if not found:
                results["invalid"].append({"citation": num, "ref": ref_text})
        
        return results
    
    def _fuzzy_match(self, ref_text: str, doc: dict) -> bool:
        """模糊匹配引用来源"""
        doc_name = doc.get("title", "") or doc.get("source", "")
        return any(keyword in doc_name 
                   for keyword in ref_text.split() if len(keyword) > 2)
```

### 6.3 原文定位与高亮展示

```python
class SourceLocator:
    """原文定位：找到答案在原文档中的精确位置"""
    
    def locate(self, answer_segment: str, source_doc: dict) -> dict:
        """定位答案片段在源文档中的位置"""
        content = source_doc["content"]
        
        # 精确匹配
        idx = content.find(answer_segment)
        if idx >= 0:
            return {
                "found": True, "start": idx, "end": idx + len(answer_segment),
                "context": content[max(0,idx-100):idx+len(answer_segment)+100],
                "highlight": answer_segment,
            }
        
        # 模糊匹配（用 difflib）
        from difflib import SequenceMatcher
        best_ratio = 0
        best_pos = 0
        window = len(answer_segment)
        
        for i in range(0, len(content) - window, 50):
            chunk = content[i:i + window]
            ratio = SequenceMatcher(None, answer_segment, chunk).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_pos = i
        
        if best_ratio > 0.6:
            return {
                "found": True, "start": best_pos, 
                "match_ratio": best_ratio,
                "context": content[best_pos:best_pos + window],
            }
        
        return {"found": False}
```

### 6.4 置信度评分：告诉用户答案有多靠谱

```python
class ConfidenceScorer:
    """答案置信度评分"""
    
    def score(self, answer: str, docs: list[dict],
               retrieval_scores: list[float]) -> dict:
        """计算综合置信度"""
        # 1. 检索置信度（最高检索分）
        retrieval_conf = max(retrieval_scores) if retrieval_scores else 0
        
        # 2. 引用置信度（有引用 > 无引用）
        import re
        citation_count = len(re.findall(r'\[\d+\]', answer))
        citation_conf = min(citation_count / 3, 1.0)
        
        # 3. 拒答置信度（说"不确定"扣分）
        uncertain_phrases = ["不确定", "可能", "也许", "未找到"]
        uncertainty = sum(1 for p in uncertain_phrases if p in answer)
        refusal_conf = max(1 - uncertainty * 0.3, 0)
        
        # 综合得分
        overall = (retrieval_conf * 0.4 + citation_conf * 0.3 + refusal_conf * 0.3)
        
        level = "高" if overall > 0.7 else "中" if overall > 0.4 else "低"
        
        return {"score": round(overall, 2), "level": level,
                "detail": {"retrieval": retrieval_conf, "citation": citation_conf}}
```

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **引用生成** | Prompt 要求 LLM 用 [1][2] 标注来源 |
| **引用验证** | 检查引用的文档名和页码是否真实 |
| **原文定位** | 精确/模糊匹配找到原文位置 |
| **置信度** | 检索分+引用数+不确定性综合评分 |

---

## 7. 多轮对话与高级功能

### 7.1 多轮对话：上下文理解与查询改写

```python
class QueryRewriter:
    """查询改写：解决多轮对话中的指代消解"""
    
    REWRITE_PROMPT = """根据对话历史，改写用户的最新问题为独立的检索查询。

对话历史：
{history}

用户最新问题：{question}

规则：
1. 将代词替换为具体名词（"它" → 具体指代对象）
2. 补充上下文中隐含的限定条件
3. 输出改写后的查询，不要解释

示例：
历史：用户问"什么是微服务"，AI回答了定义
最新问题："它和单体架构有什么区别？"
改写为："微服务架构和单体架构有什么区别？"

改写后的查询："""
    
    async def rewrite(self, question: str, history: list) -> str:
        if not history:
            return question
        
        history_text = "\n".join([
            f"{'用户' if h['role']=='user' else 'AI'}：{h['content'][:200]}"
            for h in history[-4:]  # 最近 2 轮
        ])
        
        prompt = self.REWRITE_PROMPT.format(history=history_text, question=question)
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0)
        
        return result.choices[0].message.content.strip()
```

### 7.2 追问引导：当答案不够满意时

```python
class FollowUpSuggester:
    """追问建议生成"""
    
    async def suggest(self, question: str, answer: str, 
                       docs: list[dict]) -> list[str]:
        """根据回答生成追问建议"""
        prompt = f"""根据以下问答生成 3 个有价值的追问建议。

用户问题：{question}
AI 回答：{answer[:500]}

追问方向：
1. 深入细节（问具体操作步骤）
2. 拓展关联（问相关主题）
3. 对比分析（问与其他方案的区别）

以 JSON 数组返回 3 个追问："""
        
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0.5)
        
        return json.loads(result.choices[0].message.content)
```

### 7.3 权限控制：谁能看什么文档

```python
class PermissionManager:
    """文档权限控制"""
    
    async def filter_by_permission(self, docs: list[dict],
                                     user_id: str) -> list[dict]:
        """根据用户权限过滤检索结果"""
        user_roles = await self.get_user_roles(user_id)
        user_groups = await self.get_user_groups(user_id)
        
        accessible = []
        for doc in docs:
            doc_perm = doc.get("permissions", {})
            
            # 公开文档
            if doc_perm.get("visibility") == "public":
                accessible.append(doc)
                continue
            
            # 角色权限
            if doc_perm.get("required_role") in user_roles:
                accessible.append(doc)
                continue
            
            # 组权限
            if set(doc_perm.get("groups", [])) & set(user_groups):
                accessible.append(doc)
        
        return accessible
```

### 7.4 多知识库路由：按主题自动选择知识库

```python
class KBRouter:
    """多知识库路由"""
    
    KB_CONFIGS = {
        "技术文档": {"collection": "kb_tech", "description": "API文档、技术规范"},
        "HR制度": {"collection": "kb_hr", "description": "考勤、福利、入职"},
        "产品手册": {"collection": "kb_product", "description": "产品功能和使用指南"},
        "财务制度": {"collection": "kb_finance", "description": "报销、预算、审批"},
    }
    
    async def route(self, question: str) -> list[str]:
        """根据问题自动选择知识库"""
        prompt = f"""从以下知识库中选择与问题最相关的 1-2 个。

知识库列表：
{json.dumps(self.KB_CONFIGS, ensure_ascii=False)}

问题：{question}

回复 JSON：{{"selected": ["知识库名1", "知识库名2"]}}"""
        
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0)
        
        return json.loads(result.choices[0].message.content)["selected"]
```

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **查询改写** | 指代消解 + 上下文补全 |
| **追问引导** | 深入/拓展/对比三个方向 |
| **权限控制** | 公开/角色/组三级过滤 |
| **知识库路由** | LLM 根据问题自动选择知识库 |

---

## 8. 实战案例：企业内部知识库问答系统

### 8.1 需求定义：面向技术团队的文档问答

```
项目：TechKB — 技术团队知识库问答

  文档来源：
    📁 Confluence（200+ 篇技术文档）
    📁 Markdown 仓库（API 文档、设计文档）
    📁 飞书文档（会议纪要、技术方案）
    📁 PDF（规范文档、第三方文档）

  典型问题：
    "部署服务需要哪些环境变量？"
    "订单超时未支付怎么处理？"
    "gRPC 接口的认证方式是什么？"
    "上次性能优化的结论是什么？"

  核心指标：
    回答准确率 > 85%
    引用正确率 > 90%
    首次响应 < 3 秒
    覆盖率 > 70%（能回答的问题比例）
```

### 8.2 核心功能实现：从上传到问答

```python
class TechKB:
    """技术知识库问答系统"""
    
    def __init__(self, db_url: str, vector_url: str):
        self.parser = DocumentParser()
        self.chunker = HierarchicalChunker()
        self.embedding = EmbeddingService()
        self.vector_store = VectorStore(url=vector_url)
        self.retriever = HybridRetriever()
        self.reranker = Reranker()
        self.rag = RAGEngine()
        self.rewriter = QueryRewriter()
    
    async def ingest(self, file_path: str, doc_id: str):
        """文档入库全流程"""
        # 1. 解析文档
        pages = self.parser.parse(file_path)
        
        # 2. 智能分块
        chunks = []
        for page in pages:
            page_chunks = self.chunker.create_parent_child(page["content"])
            for c in page_chunks:
                c["doc_id"] = doc_id
                c["metadata"] = page["metadata"]
            chunks.extend(page_chunks)
        
        # 3. 向量化
        texts = [c["content"] for c in chunks]
        embeddings = await self.embedding.embed(texts)
        
        # 4. 存入向量库
        await self.vector_store.upsert(chunks, embeddings)
        
        return {"chunks": len(chunks), "doc_id": doc_id}
    
    async def ask(self, question: str, user_id: str,
                   session_id: str) -> dict:
        """问答全流程"""
        # 1. 查询改写（多轮）
        rewritten = await self.rewriter.rewrite(question, self.get_history(session_id))
        
        # 2. 知识库路由
        kb_names = await self.router.route(rewritten)
        
        # 3. 检索 + Rerank
        docs = await self.retriever.retrieve(rewritten, top_k=10)
        docs = await self.reranker.rerank(rewritten, docs, top_k=5)
        
        # 4. 权限过滤
        docs = await self.perm_manager.filter_by_permission(docs, user_id)
        
        # 5. RAG 生成
        result = await self.rag.answer(rewritten, docs=docs)
        
        # 6. 引用验证
        citations = self.citation_verifier.verify(result["answer"], docs)
        
        # 7. 置信度评分
        confidence = self.scorer.score(result["answer"], docs, [d.get("score", 0) for d in docs])
        
        # 8. 追问建议
        follow_ups = await self.follow_up.suggest(question, result["answer"], docs)
        
        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "citations": citations,
            "confidence": confidence,
            "follow_ups": follow_ups,
        }
```

### 8.3 效果评估：准确率 / 召回率 / 引用率

```
评估结果（200 条测试问题）：

  ┌──────────────┬──────────┬──────────┐
  │ 指标          │ 目标      │ 实际      │
  ├──────────────┼──────────┼──────────┤
  │ 回答准确率    │ > 85%    │ 87% ✅   │
  │ 引用正确率    │ > 90%    │ 92% ✅   │
  │ 检索召回率    │ > 80%    │ 83% ✅   │
  │ 拒答正确率    │ > 70%    │ 75% ✅   │
  │ 幻觉率       │ < 10%    │ 7% ✅    │
  │ 平均响应时间  │ < 3s     │ 2.4s ✅  │
  │ 用户满意度    │ > 4.0/5  │ 4.1/5 ✅ │
  └──────────────┴──────────┴──────────┘
```

### 8.4 上线优化：从 Demo 到生产

```
生产级优化清单：

  性能优化：
    ✅ Embedding 批处理 + 异步
    ✅ 向量库索引优化（HNSW 参数调整）
    ✅ 热门问题缓存（Redis，TTL 1小时）
    ✅ 流式响应减少首字延迟

  质量优化：
    ✅ 分块参数 A/B 测试
    ✅ 增加 Rerank 提升 Top 5 精度
    ✅ 父子 Chunk 策略
    ✅ 幻觉检测后处理

  运维优化：
    ✅ 问答日志记录（问题/答案/来源/评分）
    ✅ 用户反馈收集（👍👎）
    ✅ 低分答案定期审查
    ✅ 文档更新定时同步（每小时增量）
```

**第 8 章核心知识回顾：**

| 阶段 | 做了什么 |
|:---|:---|
| **需求** | 200+ 文档、4 种来源、4 个核心指标 |
| **实现** | 8 步 Pipeline：改写→路由→检索→权限→生成→验证→评分→追问 |
| **效果** | 准确率 87%、引用率 92%、响应 2.4s |
| **优化** | 性能/质量/运维三方面 12 项优化 |

---

## 附录

### A. Embedding 模型评测对比

| 模型 | MTEB 中文 | 维度 | 价格 | 部署 | 推荐场景 |
|:---|:---|:---|:---|:---|:---|
| **BGE-M3** | 67.5 | 1024 | 免费 | 本地 | 私有化部署首选 |
| **GTE-Qwen2** | 68.2 | 1536 | 免费 | 本地 | 精度优先 |
| **M3E-large** | 65.8 | 768 | 免费 | 本地 | 资源有限 |
| **text-embedding-3-small** | 64.5 | 1536 | $0.02/M | API | 快速上线 |
| **text-embedding-3-large** | 66.8 | 3072 | $0.13/M | API | 精度优先+不差钱 |

### B. 分块策略选择决策树

```
你的文档是什么格式？
├── Markdown / HTML（有标题层级）
│   └── → 按文档结构分块（标题切分）
│       chunk_size=500, overlap=100
│
├── PDF / Word（段落分明）
│   └── → 递归分割
│       chunk_size=500, overlap=100
│
├── 纯文本（无格式）
│   └── → 语义分块 or 固定大小
│       chunk_size=400, overlap=80
│
└── FAQ / 问答对
    └── → 按 Q&A 对切分，一问一答为一个 Chunk
        不需要 overlap

进阶：对任何策略，都建议加上父子 Chunk 机制
  → 子 Chunk (300字) 用于检索
  → 父 Chunk (1500字) 用于生成
```

### C. RAG 评估指标速查表

| 指标 | 计算方式 | 目标值 | 说明 |
|:---|:---|:---|:---|
| **回答准确率** | 人工评判正确/总数 | > 85% | 核心指标 |
| **引用正确率** | 真实引用/总引用数 | > 90% | 信任基石 |
| **检索召回率** | 命中文档/相关文档 | > 80% | 检索质量 |
| **检索精度** | 相关文档/返回文档 | > 60% | 噪音控制 |
| **拒答正确率** | 正确拒答/应拒总数 | > 70% | 避免编造 |
| **幻觉率** | 编造内容的回答/总数 | < 10% | 越低越好 |
| **首字延迟** | 用户提问到首字返回 | < 1s | 用户体验 |
| **完整响应时间** | 从提问到完整回答 | < 5s | 整体性能 |
| **覆盖率** | 能回答的问题/提问总数 | > 70% | 知识库完整度 |
| **用户满意度** | 👍/(👍+👎) | > 80% | 最终指标 |
