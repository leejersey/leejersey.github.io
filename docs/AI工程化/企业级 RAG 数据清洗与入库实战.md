# 企业级 RAG 数据清洗与入库实战

> 从原始数据到可检索知识库：掌握多源文档采集、清洗去噪、智能分块、Embedding 生成、向量入库的完整 Pipeline。

---

## 1. 为什么数据质量决定 RAG 成败

RAG（Retrieval-Augmented Generation）的核心是"检索增强"——如果检索到的内容本身就是垃圾，大模型再强也救不了。**数据质量是 RAG 系统的地基**。

### 1.1 脏数据如何毁掉你的 RAG 系统

```
典型的"脏数据"问题及其后果：

  问题 1：文档中夹杂页眉页脚、广告、导航栏文字
  → 检索时这些噪声被当成"知识"返回
  → 大模型基于噪声生成答案 → 胡说八道

  问题 2：同一份文档被重复入库（不同格式/版本）
  → 检索 Top-K 中 3 条都是重复内容
  → 浪费检索配额，真正有用的文档被挤掉

  问题 3：分块不合理（一段话被从中间截断）
  → 检索到的片段缺少上下文
  → 大模型无法理解不完整的信息 → 幻觉

  问题 4：元数据缺失（不知道文档来源、时间、分类）
  → 无法做过滤检索（如"只查 2024 年之后的文档"）
  → 过时信息和最新信息混在一起 → 答案过期
```

> 💡 **一句话总结**：RAG 系统的效果上限不取决于大模型，而取决于你喂给它的数据质量。

### 1.2 企业级数据 Pipeline 全景架构

```
企业级 RAG 数据 Pipeline：

  ┌─────────────────────────────────────────────────────────┐
  │                    数据源层                              │
  │  PDF  │  网页  │  Word/Excel  │  数据库  │  API/爬虫    │
  └───┬───┴───┬────┴──────┬───────┴─────┬────┴──────┬──────┘
      │       │           │             │           │
      ▼       ▼           ▼             ▼           ▼
  ┌─────────────────────────────────────────────────────────┐
  │              ① 采集与解析层（第 2 章）                    │
  │  PyMuPDF / Trafilatura / python-docx / SQLAlchemy       │
  │  → 输出：统一的 Document 对象                            │
  └───────────────────────┬─────────────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────────────┐
  │              ② 清洗与去噪层（第 3 章）                    │
  │  文本清洗 → 去重 → 质量过滤 → 脱敏 → 元数据标准化        │
  │  → 输出：干净的 Document 列表                            │
  └───────────────────────┬─────────────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────────────┐
  │              ③ 分块层（第 4 章）                          │
  │  递归分块 / 语义分块 / 层级分块 + overlap 重叠            │
  │  → 输出：Chunk 列表（每个 Chunk 带元数据）               │
  └───────────────────────┬─────────────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────────────┐
  │              ④ 向量化层（第 5 章）                        │
  │  Embedding 模型（OpenAI / BGE / Jina）→ 批量生成向量     │
  │  → 输出：(Chunk, Vector, Metadata) 三元组               │
  └───────────────────────┬─────────────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────────────┐
  │              ⑤ 存储层（第 6 章）                          │
  │  向量数据库（Qdrant / Milvus / PGVector）               │
  │  → 批量写入 + 索引构建 + 元数据过滤                      │
  └───────────────────────┬─────────────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────────────┐
  │         ⑥ 维护层（第 7 章）+ ⑦ 评测层（第 8 章）         │
  │  增量更新 / 版本管理 / 定时同步 / 质量评测 / 优化闭环     │
  └─────────────────────────────────────────────────────────┘
```

```python
# ═══════════════════════════════════════
# 数据 Pipeline 的核心数据结构
# ═══════════════════════════════════════
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Document:
    """统一文档模型——贯穿整个 Pipeline"""
    content: str                          # 文本内容
    source: str                           # 来源（文件路径/URL/数据库表）
    doc_type: str                         # 类型（pdf/html/docx/db）
    metadata: dict = field(default_factory=dict)  # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    doc_hash: str = ""                    # 内容哈希（用于去重和变更检测）

@dataclass
class Chunk:
    """分块后的文本片段"""
    content: str                          # 片段内容
    doc_id: str                           # 所属文档 ID
    chunk_index: int                      # 在文档中的序号
    metadata: dict = field(default_factory=dict)
    embedding: list[float] | None = None  # 向量（向量化后填充）

# Pipeline 的每一层都基于这两个数据结构流转
# Document → 清洗 → Document → 分块 → Chunk → 向量化 → Chunk(带 embedding) → 入库
```

> 💡 **关键理解**：整个 Pipeline 就是一条数据加工流水线。原始文档进来，干净的向量出去。每一层只做一件事，层层递进。

---

## 2. 多源数据采集与解析

企业中的知识散落在各种格式中——PDF 技术文档、网页知识库、Word 方案、数据库记录。第一步是把它们全部"读出来"，转成统一的文本格式。

### 2.1 PDF 文档解析（表格、图片、多栏布局）

PDF 是企业文档中最常见也最难解析的格式。不同的库适合不同场景：

```python
# ═══════════════════════════════════════
# 方案 1：PyMuPDF（fitz）—— 速度快，适合纯文本 PDF
# ═══════════════════════════════════════
# pip install pymupdf
import fitz

def parse_pdf_pymupdf(file_path: str) -> list[Document]:
    """用 PyMuPDF 解析 PDF，逐页提取文本"""
    docs = []
    pdf = fitz.open(file_path)

    for page_num, page in enumerate(pdf):
        text = page.get_text("text")  # 提取纯文本
        if text.strip():
            docs.append(Document(
                content=text.strip(),
                source=f"{file_path}#page={page_num + 1}",
                doc_type="pdf",
                metadata={"page": page_num + 1, "total_pages": len(pdf)},
            ))

    pdf.close()
    return docs
# → 优点：速度极快（C 底层），支持中文
# → 缺点：对复杂表格支持一般
```

```python
# ═══════════════════════════════════════
# 方案 2：pdfplumber —— 擅长表格提取
# ═══════════════════════════════════════
# pip install pdfplumber
import pdfplumber

def parse_pdf_with_tables(file_path: str) -> list[Document]:
    """用 pdfplumber 解析 PDF，同时提取文本和表格"""
    docs = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # 提取正文文本
            text = page.extract_text() or ""

            # 提取表格（转为 Markdown 格式）
            tables = page.extract_tables()
            for table in tables:
                if table:
                    # 第一行作为表头
                    header = " | ".join(str(cell or "") for cell in table[0])
                    separator = " | ".join("---" for _ in table[0])
                    rows = "\n".join(
                        " | ".join(str(cell or "") for cell in row)
                        for row in table[1:]
                    )
                    table_md = f"\n{header}\n{separator}\n{rows}\n"
                    text += table_md

            if text.strip():
                docs.append(Document(
                    content=text.strip(),
                    source=f"{file_path}#page={page_num + 1}",
                    doc_type="pdf",
                    metadata={"page": page_num + 1, "has_tables": len(tables) > 0},
                ))

    return docs
# → 表格自动转 Markdown 格式，方便后续检索和 LLM 理解
```

```
PDF 解析库选型：

  库              速度    表格    多栏    OCR     适合场景
  ─────────────────────────────────────────────────────
  PyMuPDF         ⭐⭐⭐   一般    一般    ❌     纯文本 PDF、批量处理
  pdfplumber      ⭐⭐     ⭐⭐⭐  一般    ❌     含表格的 PDF
  MinerU          ⭐⭐     ⭐⭐⭐  ⭐⭐⭐  ✅     复杂版式、公式、图文混排
  Unstructured    ⭐       ⭐⭐    ⭐⭐⭐  ✅     复杂布局、混合文档
  PyPDF2          ⭐⭐     ❌     ❌     ❌     简单文本提取

  推荐：简单 PDF 用 PyMuPDF，表格用 pdfplumber
        复杂版式（公式/多栏/扫描件）首选 MinerU
```

```python
# ═══════════════════════════════════════
# 方案 3：MinerU —— 复杂 PDF 的终极方案
# ═══════════════════════════════════════
# MinerU 是 OpenDataLab 开源的文档解析工具
# 支持公式→LaTeX、表格→HTML、多栏重排、OCR 109 种语言
# 输出 Markdown/JSON，天然适合 RAG

# --- 方式 A：本地 SDK（数据隐私/大批量场景）---
# pip install "mineru[core]"

import os
os.environ['MINERU_MODEL_SOURCE'] = 'modelscope'  # 国内镜像加速

from mineru.api import MinerU

def parse_pdf_mineru(file_path: str, backend: str = "pipeline") -> list[Document]:
    """
    用 MinerU 解析复杂 PDF
    backend:
      - "pipeline"：传统模型，速度快，适合文字版 PDF
      - "vlm"：视觉语言模型，精度最高，需要 GPU
    """
    parser = MinerU(backend=backend)
    result = parser.process(file_path)

    docs = []
    # MinerU 输出 Markdown 格式，按页或按章节拆分
    if hasattr(result, 'markdown'):
        docs.append(Document(
            content=result.markdown,
            source=file_path,
            doc_type="pdf",
            metadata={
                "parser": "mineru",
                "backend": backend,
                "has_formula": True,  # MinerU 自动处理公式
            },
        ))

    return docs

# 用法：
# docs = parse_pdf_mineru("论文.pdf", backend="vlm")  # 学术论文用 VLM
# docs = parse_pdf_mineru("手册.pdf", backend="pipeline")  # 普通文档用 pipeline
```

```python
# --- 方式 B：调用 MinerU 在线 API（无需 GPU）---
import requests
import time

MINERU_API_KEY = "your_api_token"  # 在 mineru.net 申请

def parse_pdf_mineru_api(pdf_url: str) -> Document | None:
    """通过 MinerU 在线 API 解析 PDF（适合没有 GPU 的场景）"""
    headers = {
        "Authorization": f"Bearer {MINERU_API_KEY}",
        "Content-Type": "application/json",
    }

    # 1. 提交解析任务
    resp = requests.post(
        "https://mineru.net/api/v4/extract/task",
        headers=headers,
        json={"url": pdf_url, "is_ocr": True, "enable_formula": True},
    )
    task_id = resp.json()["data"]["task_id"]

    # 2. 轮询等待结果
    for _ in range(30):  # 最多等 5 分钟
        time.sleep(10)
        result = requests.get(
            f"https://mineru.net/api/v4/extract/task/{task_id}",
            headers=headers,
        ).json()

        if result["data"]["state"] == "success":
            # 下载 Markdown 结果
            md_content = requests.get(result["data"]["result_url"]).text
            return Document(
                content=md_content,
                source=pdf_url,
                doc_type="pdf",
                metadata={"parser": "mineru_api", "task_id": task_id},
            )
        elif result["data"]["state"] == "failed":
            print(f"[ERROR] MinerU 解析失败: {pdf_url}")
            return None

    return None
```

> 💡 **MinerU vs 传统解析库**：对于包含公式、多栏布局、扫描件的复杂 PDF，MinerU 的解析质量远超 PyMuPDF/pdfplumber。代价是速度较慢且需要 GPU（本地部署时）。建议：简单 PDF 用 PyMuPDF 批量处理，复杂 PDF 用 MinerU 精细解析。

### 2.2 网页与 HTML 正文提取

```python
# ═══════════════════════════════════════
# 方案 1：Trafilatura —— 一行代码提取网页正文（推荐）
# ═══════════════════════════════════════
# pip install trafilatura
import trafilatura

def parse_webpage(url: str) -> Document | None:
    """从 URL 提取网页正文，自动过滤导航栏/广告/页脚"""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None

    # extract() 自动去除 HTML 标签、导航、广告等噪声
    text = trafilatura.extract(
        downloaded,
        include_tables=True,       # 保留表格
        include_comments=False,    # 去掉评论区
        output_format="txt",       # 输出纯文本（也支持 "json"）
    )

    if not text:
        return None

    return Document(
        content=text,
        source=url,
        doc_type="html",
        metadata={"url": url},
    )

# → Trafilatura 的正文提取准确率在学术评测中排名前列
# → 比 BeautifulSoup 手动解析省 90% 的代码
```

```python
# ═══════════════════════════════════════
# 方案 2：批量采集多个网页
# ═══════════════════════════════════════
import asyncio
import httpx

async def batch_parse_urls(urls: list[str]) -> list[Document]:
    """异步批量采集网页"""
    docs = []

    async with httpx.AsyncClient(timeout=10) as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for url, resp in zip(urls, responses):
            if isinstance(resp, Exception):
                print(f"[WARN] 采集失败: {url} → {resp}")
                continue

            text = trafilatura.extract(resp.text)
            if text:
                docs.append(Document(
                    content=text,
                    source=url,
                    doc_type="html",
                    metadata={"status_code": resp.status_code},
                ))

    return docs
```
### 2.3 Office 文档与数据库导出

```python
# ═══════════════════════════════════════
# Word 文档解析（python-docx）
# ═══════════════════════════════════════
# pip install python-docx
from docx import Document as DocxDocument

def parse_docx(file_path: str) -> Document:
    """解析 Word 文档，提取段落和表格"""
    doc = DocxDocument(file_path)
    parts = []

    for para in doc.paragraphs:
        if para.text.strip():
            # 保留标题层级信息
            if para.style.name.startswith("Heading"):
                level = para.style.name.replace("Heading ", "")
                parts.append(f"{'#' * int(level)} {para.text}")
            else:
                parts.append(para.text)

    return Document(
        content="\n\n".join(parts),
        source=file_path,
        doc_type="docx",
    )
```

```python
# ═══════════════════════════════════════
# 数据库批量导出（SQLAlchemy）
# ═══════════════════════════════════════
from sqlalchemy import create_engine, text

def export_from_db(db_url: str, query: str) -> list[Document]:
    """从数据库批量导出记录为 Document"""
    engine = create_engine(db_url)
    docs = []

    with engine.connect() as conn:
        result = conn.execute(text(query))
        for row in result:
            # 将每行记录拼接为文本
            content = "\n".join(
                f"{col}: {val}" for col, val in zip(result.keys(), row)
            )
            docs.append(Document(
                content=content,
                source=f"db://{db_url.split('@')[-1]}",
                doc_type="db",
                metadata={"query": query},
            ))

    return docs

# 用法：
# docs = export_from_db(
#     "postgresql://user:pass@localhost/mydb",
#     "SELECT title, content, created_at FROM articles WHERE status = 'published'"
# )
```
### 2.4 统一文档模型：Document 数据结构

所有解析器的输出都是 `Document` 对象——这是 Pipeline 后续所有环节的统一接口：

```python
# ═══════════════════════════════════════
# 统一解析入口（工厂模式）
# ═══════════════════════════════════════
import hashlib
from pathlib import Path

class DocumentParser:
    """根据文件类型自动选择解析器"""

    PARSERS = {
        ".pdf": parse_pdf_pymupdf,
        ".docx": parse_docx,
        ".html": lambda f: [Document(content=open(f).read(), source=f, doc_type="html")],
        ".md": lambda f: [Document(content=open(f).read(), source=f, doc_type="markdown")],
        ".txt": lambda f: [Document(content=open(f).read(), source=f, doc_type="text")],
    }

    @classmethod
    def parse(cls, file_path: str) -> list[Document]:
        ext = Path(file_path).suffix.lower()
        parser = cls.PARSERS.get(ext)
        if not parser:
            raise ValueError(f"不支持的文件格式: {ext}")

        docs = parser(file_path)

        # 为每个文档计算内容哈希（用于后续去重和增量更新）
        for doc in docs:
            doc.doc_hash = hashlib.md5(doc.content.encode()).hexdigest()

        return docs

# 用法：
# docs = DocumentParser.parse("report.pdf")
# docs = DocumentParser.parse("guide.docx")
# docs = DocumentParser.parse("notes.md")
# → 不管什么格式，输出都是 list[Document]
```

> 💡 **第 2 章小结**：采集层的核心原则是"**统一输出**"——无论数据来自 PDF、网页还是数据库，最终都变成相同结构的 `Document` 对象，让后续的清洗、分块、向量化环节不需要关心数据来源。

---

## 3. 数据清洗与去噪

采集来的原始文档往往"脏得不能直接用"——乱码、重复、噪声、敏感信息。清洗层的目标是：**把脏数据变成干净、安全、标准化的数据**。

### 3.1 文本清洗：从乱码到干净文本

```python
# ═══════════════════════════════════════
# 文本清洗工具集
# ═══════════════════════════════════════
import re
import unicodedata

class TextCleaner:
    """文本清洗器——处理从 PDF/网页/Office 提取的原始文本"""

    @staticmethod
    def fix_encoding(text: str) -> str:
        """修复常见编码问题"""
        # 全角字符→半角
        text = unicodedata.normalize("NFKC", text)
        # 修复 Windows 换行符
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return text

    @staticmethod
    def remove_noise(text: str) -> str:
        """去除噪声文本"""
        # 去除零宽字符
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        # 去除连续多个空行 → 最多保留 2 个换行
        text = re.sub(r"\n{3,}", "\n\n", text)
        # 去除行首行尾空白
        text = "\n".join(line.strip() for line in text.split("\n"))
        # 去除多余空格（保留单个空格）
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()

    @staticmethod
    def remove_headers_footers(text: str) -> str:
        """去除 PDF 常见的页眉页脚"""
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            # 跳过纯页码行
            if re.match(r"^\s*-?\s*\d+\s*-?\s*$", line):
                continue
            # 跳过常见页眉模式（"第X页"、"Page X of Y"）
            if re.match(r"^\s*(第\s*\d+\s*页|Page\s+\d+\s*(of|/)\s*\d+)\s*$", line, re.I):
                continue
            # 跳过"机密"/"内部资料"等水印文字
            if re.match(r"^\s*(机密|内部资料|CONFIDENTIAL|DRAFT)\s*$", line, re.I):
                continue
            cleaned.append(line)
        return "\n".join(cleaned)

    @classmethod
    def clean(cls, text: str) -> str:
        """完整清洗流程"""
        text = cls.fix_encoding(text)
        text = cls.remove_noise(text)
        text = cls.remove_headers_footers(text)
        return text

# 用法：
# for doc in docs:
#     doc.content = TextCleaner.clean(doc.content)
```

### 3.2 去重策略：精确去重 / 模糊去重 / 语义去重

```python
# ═══════════════════════════════════════
# 三层去重策略
# ═══════════════════════════════════════
import hashlib
from collections import defaultdict

class Deduplicator:
    """文档去重器——从精确到模糊，三层过滤"""

    # ① 精确去重：内容完全相同（基于 MD5 哈希）
    @staticmethod
    def exact_dedup(docs: list[Document]) -> list[Document]:
        seen_hashes = set()
        unique_docs = []
        for doc in docs:
            content_hash = hashlib.md5(doc.content.encode()).hexdigest()
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                doc.doc_hash = content_hash
                unique_docs.append(doc)
        removed = len(docs) - len(unique_docs)
        print(f"[精确去重] {len(docs)} → {len(unique_docs)}（去除 {removed} 篇）")
        return unique_docs

    # ② 模糊去重：内容高度相似（基于 SimHash / 文本相似度）
    @staticmethod
    def fuzzy_dedup(docs: list[Document], threshold: float = 0.9) -> list[Document]:
        """基于 Jaccard 相似度的模糊去重"""
        from difflib import SequenceMatcher

        unique_docs = []
        for doc in docs:
            is_dup = False
            for existing in unique_docs:
                similarity = SequenceMatcher(
                    None, doc.content[:500], existing.content[:500]
                ).ratio()
                if similarity >= threshold:
                    is_dup = True
                    break
            if not is_dup:
                unique_docs.append(doc)

        removed = len(docs) - len(unique_docs)
        print(f"[模糊去重] {len(docs)} → {len(unique_docs)}（去除 {removed} 篇）")
        return unique_docs

    # ③ 语义去重：含义相同但表述不同（基于 Embedding 余弦相似度）
    @staticmethod
    def semantic_dedup(docs: list[Document], embeddings: list[list[float]],
                       threshold: float = 0.95) -> list[Document]:
        """基于向量余弦相似度的语义去重（需要先生成 Embedding）"""
        import numpy as np

        unique_indices = []
        for i, emb in enumerate(embeddings):
            is_dup = False
            for j in unique_indices:
                sim = np.dot(emb, embeddings[j]) / (
                    np.linalg.norm(emb) * np.linalg.norm(embeddings[j])
                )
                if sim >= threshold:
                    is_dup = True
                    break
            if not is_dup:
                unique_indices.append(i)

        unique_docs = [docs[i] for i in unique_indices]
        print(f"[语义去重] {len(docs)} → {len(unique_docs)}")
        return unique_docs

# 推荐的去重顺序：精确去重 → 模糊去重 → 语义去重
# 越靠前的越快越便宜，逐层过滤
```
### 3.3 内容质量过滤与敏感信息脱敏

```python
# ═══════════════════════════════════════
# 内容质量过滤
# ═══════════════════════════════════════

def filter_low_quality(docs: list[Document], min_length: int = 50) -> list[Document]:
    """过滤低质量文档"""
    quality_docs = []
    for doc in docs:
        text = doc.content

        # 过滤条件
        if len(text) < min_length:                    continue  # 太短，没有信息量
        if text.count("http") / max(len(text), 1) > 0.3: continue  # 纯链接堆砌
        if len(set(text)) < 20:                       continue  # 字符种类太少（乱码）

        quality_docs.append(doc)

    removed = len(docs) - len(quality_docs)
    print(f"[质量过滤] {len(docs)} → {len(quality_docs)}（过滤 {removed} 篇）")
    return quality_docs
```

```python
# ═══════════════════════════════════════
# 敏感信息脱敏
# ═══════════════════════════════════════
import re

class Desensitizer:
    """敏感信息脱敏——防止私密数据进入向量数据库"""

    PATTERNS = {
        "phone":    (r"1[3-9]\d{9}", "***PHONE***"),
        "email":    (r"[\w.-]+@[\w.-]+\.\w+", "***EMAIL***"),
        "id_card":  (r"\d{17}[\dXx]", "***ID_CARD***"),
        "api_key":  (r"(sk-|ak-|key-)[a-zA-Z0-9]{20,}", "***API_KEY***"),
        "ip_addr":  (r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "***IP***"),
    }

    @classmethod
    def desensitize(cls, text: str) -> str:
        for name, (pattern, replacement) in cls.PATTERNS.items():
            text = re.sub(pattern, replacement, text)
        return text

# 用法：
# for doc in docs:
#     doc.content = Desensitizer.desensitize(doc.content)
```
### 3.4 元数据标准化

元数据是 RAG 系统做**过滤检索**的关键——没有标准化的元数据，就无法按时间、来源、分类筛选文档。

```python
# ═══════════════════════════════════════
# 元数据标准化 + 完整清洗 Pipeline
# ═══════════════════════════════════════
from datetime import datetime
from pathlib import Path

def standardize_metadata(doc: Document) -> Document:
    """为文档填充标准化元数据"""
    meta = doc.metadata

    # 确保必填字段存在
    meta.setdefault("source", doc.source)
    meta.setdefault("doc_type", doc.doc_type)
    meta.setdefault("created_at", doc.created_at.isoformat())

    # 从文件路径推断分类
    if doc.source and "/" in doc.source:
        meta.setdefault("category", Path(doc.source).parent.name)

    # 文本统计信息（帮助后续质量分析）
    meta["char_count"] = len(doc.content)
    meta["word_count"] = len(doc.content.split())

    doc.metadata = meta
    return doc


def run_cleaning_pipeline(docs: list[Document]) -> list[Document]:
    """完整的清洗 Pipeline"""
    print(f"📥 输入文档数: {len(docs)}")

    # Step 1: 文本清洗
    for doc in docs:
        doc.content = TextCleaner.clean(doc.content)

    # Step 2: 精确去重
    docs = Deduplicator.exact_dedup(docs)

    # Step 3: 模糊去重
    docs = Deduplicator.fuzzy_dedup(docs, threshold=0.9)

    # Step 4: 质量过滤
    docs = filter_low_quality(docs, min_length=50)

    # Step 5: 敏感信息脱敏
    for doc in docs:
        doc.content = Desensitizer.desensitize(doc.content)

    # Step 6: 元数据标准化
    docs = [standardize_metadata(doc) for doc in docs]

    print(f"📤 输出文档数: {len(docs)}")
    return docs

# 用法：
# raw_docs = DocumentParser.parse("data/")
# clean_docs = run_cleaning_pipeline(raw_docs)
```

> 💡 **第 3 章小结**：清洗层的核心是"**分层过滤、逐步净化**"。精确去重最快放最前，语义去重最贵放最后。敏感信息脱敏是企业场景的刚需——千万不要把用户手机号存进向量数据库。

---

## 4. 文档分块策略

分块（Chunking）是 RAG 数据准备中**最影响检索质量**的环节——分太大，检索不精准；分太小，丢失上下文。

### 4.1 为什么分块策略如此重要

```
为什么必须分块：

  ① Embedding 模型有 Token 限制
  → OpenAI text-embedding-3-small: 最大 8191 tokens
  → BGE-large-zh: 最大 512 tokens
  → 一篇 5000 字的文档塞不进去

  ② 检索粒度影响答案质量
  → 分块太大（整篇文档）→ 检索到了但答案淹没在噪声中
  → 分块太小（单句）→ 丢失上下文，LLM 看不懂
  → 最佳粒度：一个"语义完整的段落"（200-500 字）

  ③ 分块质量 = 检索质量 = 答案质量
  → 分块断在句子中间 → 检索到残缺片段 → 幻觉
  → 分块保持语义完整 → 检索到高质量上下文 → 准确回答
```

### 4.2 基础分块：固定大小 / 段落 / 句子

```python
# ═══════════════════════════════════════
# 基础分块方法
# ═══════════════════════════════════════

# 方法 1：固定大小分块（最简单，但容易截断语义）
def chunk_by_size(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """按字符数切分，带重叠"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap  # 重叠部分保留上下文
    return chunks

# 方法 2：按段落分块（适合结构清晰的文档）
def chunk_by_paragraph(text: str, max_size: int = 800) -> list[str]:
    """按段落切分，合并短段落"""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) < max_size:
            current += para + "\n\n"
        else:
            if current.strip():
                chunks.append(current.strip())
            current = para + "\n\n"

    if current.strip():
        chunks.append(current.strip())
    return chunks

# 方法 3：按句子分块（适合需要高粒度检索的场景）
def chunk_by_sentence(text: str, sentences_per_chunk: int = 5) -> list[str]:
    """按句子切分"""
    import re
    sentences = re.split(r'(?<=[。！？.!?])\s*', text)
    chunks = []
    for i in range(0, len(sentences), sentences_per_chunk):
        chunk = "".join(sentences[i:i + sentences_per_chunk])
        if chunk.strip():
            chunks.append(chunk.strip())
    return chunks
```

### 4.3 高级分块：递归分块 / 语义分块 / 层级分块

```python
# ═══════════════════════════════════════
# 高级方法 1：递归字符分块（LangChain 内置，最常用）
# ═══════════════════════════════════════
# pip install langchain-text-splitters
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,            # 每个 chunk 最大字符数
    chunk_overlap=50,          # 重叠字符数
    separators=[               # 分隔符优先级（从高到低）
        "\n\n",                # 优先按段落分
        "\n",                  # 其次按换行
        "。", "！", "？",      # 再按中文句号
        ".", "!", "?",         # 英文句号
        " ",                   # 最后按空格
        "",                    # 兜底：强制切
    ],
    length_function=len,
)

chunks = splitter.split_text(doc.content)
# → 递归尝试每种分隔符，优先在自然边界切分
# → 是目前企业级 RAG 最常用的分块方案
```

```python
# ═══════════════════════════════════════
# 高级方法 2：语义分块（按语义相似度切分）
# ═══════════════════════════════════════
# pip install langchain-experimental
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

semantic_splitter = SemanticChunker(
    embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    breakpoint_threshold_type="percentile",  # 百分位阈值
    breakpoint_threshold_amount=95,          # 相似度低于 95% 时切分
)

chunks = semantic_splitter.split_text(doc.content)
# → 根据相邻句子的 Embedding 相似度决定是否切分
# → 效果最好，但成本高（每句都要调 Embedding API）
# → 适合高价值文档（如合同、法规、论文）
```

```python
# ═══════════════════════════════════════
# 高级方法 3：基于标题的层级分块（Markdown/HTML 文档）
# ═══════════════════════════════════════
from langchain_text_splitters import MarkdownHeaderTextSplitter

md_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]
)

chunks = md_splitter.split_text(doc.content)
# → 按 Markdown 标题层级切分
# → 每个 chunk 自动带上标题层级元数据
# → 检索时知道这段内容属于哪个章节
# → 非常适合技术文档、产品手册
```
### 4.4 分块参数调优与质量评估

```
分块策略选型指南：

  文档类型              推荐策略              chunk_size   overlap
  ──────────────────────────────────────────────────────────────
  技术文档/手册          Markdown 层级分块     500-800      50
  学术论文/合同          语义分块              400-600      0
  通用文本/博客          递归字符分块          500          50
  FAQ / 问答对          按段落分块            200-300      0
  代码文档              按函数/类分块         800-1200     0

  经验法则：
  → chunk_size 大 → 上下文丰富但检索不精准
  → chunk_size 小 → 检索精准但可能丢失上下文
  → overlap 20-50 字 → 防止语义在边界处断裂
```

```python
# ═══════════════════════════════════════
# 分块质量快速评估
# ═══════════════════════════════════════

def evaluate_chunks(chunks: list[str]) -> dict:
    """评估分块质量"""
    lengths = [len(c) for c in chunks]
    avg_len = sum(lengths) / len(lengths)

    # 检查是否有截断的句子（以非标点结尾）
    incomplete = sum(1 for c in chunks if not c[-1] in "。！？.!?\n")

    stats = {
        "total_chunks": len(chunks),
        "avg_length": round(avg_len),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "incomplete_chunks": incomplete,       # 不完整的 chunk 数量
        "incomplete_ratio": f"{incomplete / len(chunks):.1%}",
    }

    print(f"📊 分块统计: {stats}")
    return stats

# → incomplete_ratio 越低越好（< 10% 为合格）
# → 如果超过 20%，说明分块策略需要调整
```

> 💡 **第 4 章小结**：优先使用 `RecursiveCharacterTextSplitter`（递归分块），它在通用性和效果之间取得了最佳平衡。对于 Markdown 文档用层级分块，高价值文档用语义分块。

---

## 5. Embedding 生成与模型选型

分块完成后，每个 Chunk 需要转成向量（Embedding）才能存入向量数据库。选对模型、控制好并发，是这一层的核心。

### 5.1 Embedding 模型选型指南

```
主流 Embedding 模型对比（2024-2025）：

  模型                      维度    中文    最大Token  部署方式      成本
  ─────────────────────────────────────────────────────────────────────
  OpenAI text-embedding-3-small  1536   ✅     8191     云端 API     $0.02/1M tokens
  OpenAI text-embedding-3-large  3072   ✅     8191     云端 API     $0.13/1M tokens
  BGE-large-zh-v1.5              1024   ⭐⭐⭐  512      本地/API     免费（开源）
  BGE-M3                         1024   ⭐⭐⭐  8192     本地/API     免费（开源）
  Jina-embeddings-v3             1024   ✅     8192     本地/API     免费（开源）
  Cohere embed-v3                1024   ✅     512      云端 API     $0.1/1M tokens

  选型建议：
  → 中文为主 + 预算有限 → BGE-M3（免费、中文效果好、支持长文本）
  → 英文为主 + 追求效果 → OpenAI text-embedding-3-large
  → 多语言混合          → Jina-embeddings-v3 或 BGE-M3
  → 数据隐私要求高      → 本地部署 BGE 系列
```

### 5.2 批量 Embedding 生成（异步 + 重试 + 速率控制）

```python
# ═══════════════════════════════════════
# 批量 Embedding 生成器
# ═══════════════════════════════════════
import asyncio
from openai import AsyncOpenAI

class EmbeddingGenerator:
    def __init__(self, model: str = "text-embedding-3-small",
                 batch_size: int = 100, max_retries: int = 3):
        self.client = AsyncOpenAI()
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(5)  # 限制并发数

    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """对一批文本生成 Embedding（带重试）"""
        for attempt in range(self.max_retries):
            try:
                async with self.semaphore:
                    response = await self.client.embeddings.create(
                        model=self.model,
                        input=texts,
                    )
                return [item.embedding for item in response.data]
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait = 2 ** attempt  # 指数退避：1s, 2s, 4s
                print(f"[WARN] Embedding 失败，{wait}s 后重试: {e}")
                await asyncio.sleep(wait)

    async def generate(self, chunks: list[Chunk]) -> list[Chunk]:
        """批量生成 Embedding"""
        total = len(chunks)
        for i in range(0, total, self.batch_size):
            batch = chunks[i:i + self.batch_size]
            texts = [c.content for c in batch]

            embeddings = await self._embed_batch(texts)

            for chunk, emb in zip(batch, embeddings):
                chunk.embedding = emb

            print(f"📊 Embedding 进度: {min(i + self.batch_size, total)}/{total}")

        return chunks

# 用法：
# generator = EmbeddingGenerator(model="text-embedding-3-small", batch_size=100)
# chunks_with_embeddings = await generator.generate(chunks)
```

### 5.3 本地部署 vs 云端 API

```python
# ═══════════════════════════════════════
# 本地部署 Embedding（使用 sentence-transformers）
# ═══════════════════════════════════════
# pip install sentence-transformers
from sentence_transformers import SentenceTransformer

class LocalEmbeddingGenerator:
    def __init__(self, model_name: str = "BAAI/bge-large-zh-v1.5"):
        self.model = SentenceTransformer(model_name)

    def generate(self, chunks: list[Chunk], batch_size: int = 64) -> list[Chunk]:
        texts = [c.content for c in chunks]

        # sentence-transformers 自动处理批次
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,  # 归一化（余弦相似度必须）
        )

        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb.tolist()

        return chunks

# 用法：
# generator = LocalEmbeddingGenerator("BAAI/bge-m3")
# chunks = generator.generate(chunks)
```

```
本地 vs 云端 Embedding 选择：

  维度          本地部署                  云端 API
  ──────────────────────────────────────────────────
  数据隐私      ✅ 数据不出服务器         ❌ 需发送到第三方
  成本          GPU 硬件成本             按 Token 计费
  速度          取决于 GPU               取决于网络 + 限速
  维护          需要自己管理模型          零运维
  适合场景      大批量 / 隐私敏感         中小量 / 快速上手

  推荐：先用云端 API 验证效果，量大后迁移到本地
```

> 💡 **第 5 章小结**：Embedding 生成的关键是**批量化 + 异步 + 重试**。生产环境务必加速率控制（Semaphore），防止被 API 限流。

---

## 6. 向量数据库写入与索引管理

Embedding 生成完毕，最后一步是把 `(文本, 向量, 元数据)` 三元组写入向量数据库，构建可检索的知识库。

### 6.1 向量数据库选型与 Collection 设计

```
主流向量数据库对比：

  数据库        类型        性能    生态    易用性    适合场景
  ──────────────────────────────────────────────────────────
  Qdrant        独立服务    ⭐⭐⭐   ⭐⭐    ⭐⭐⭐    生产环境首选
  Milvus        独立服务    ⭐⭐⭐   ⭐⭐⭐  ⭐⭐     大规模（亿级）
  Weaviate      独立服务    ⭐⭐     ⭐⭐    ⭐⭐     多模态检索
  Chroma        嵌入式      ⭐⭐     ⭐      ⭐⭐⭐    开发测试/小规模
  PGVector      PG 扩展     ⭐⭐     ⭐⭐⭐  ⭐⭐⭐    已有 PG 基础设施

  选型建议：
  → 快速验证 → Chroma（嵌入式，零配置）
  → 生产环境 → Qdrant（性能好，API 友好）
  → 已有 PostgreSQL → PGVector（无需新增组件）
  → 亿级数据 → Milvus（分布式架构）
```

### 6.2 批量写入优化与错误处理

```python
# ═══════════════════════════════════════
# Qdrant 批量写入（生产级）
# ═══════════════════════════════════════
# pip install qdrant-client
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, 
    OptimizersConfigDiff
)
import uuid

class VectorStore:
    def __init__(self, url: str = "http://localhost:6333",
                 collection_name: str = "knowledge_base",
                 vector_size: int = 1536):
        self.client = QdrantClient(url=url)
        self.collection = collection_name
        self.vector_size = vector_size

    def create_collection(self):
        """创建 Collection（带索引优化）"""
        self.client.recreate_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=Distance.COSINE,  # 余弦相似度
            ),
            optimizers_config=OptimizersConfigDiff(
                indexing_threshold=20000,  # 超过 2w 条才建索引
            ),
        )
        print(f"✅ Collection '{self.collection}' 创建成功")

    def batch_upsert(self, chunks: list[Chunk], batch_size: int = 100):
        """批量写入（带错误处理和进度显示）"""
        total = len(chunks)
        success = 0
        failed = 0

        for i in range(0, total, batch_size):
            batch = chunks[i:i + batch_size]
            points = []

            for chunk in batch:
                if chunk.embedding is None:
                    failed += 1
                    continue

                points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=chunk.embedding,
                    payload={
                        "content": chunk.content,
                        "doc_id": chunk.doc_id,
                        "chunk_index": chunk.chunk_index,
                        **chunk.metadata,
                    },
                ))

            try:
                self.client.upsert(
                    collection_name=self.collection,
                    points=points,
                )
                success += len(points)
            except Exception as e:
                failed += len(points)
                print(f"[ERROR] 批次写入失败: {e}")

            print(f"📊 写入进度: {success + failed}/{total} "
                  f"(成功: {success}, 失败: {failed})")

        print(f"✅ 写入完成: {success}/{total}")
        return {"success": success, "failed": failed}
```

### 6.3 元数据索引与过滤查询

```python
# ═══════════════════════════════════════
# 在 VectorStore 类中扩展查询方法
# ═══════════════════════════════════════
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

class VectorStore(VectorStore):  # 扩展上面的类

    def search(self, query_embedding: list[float], top_k: int = 5,
               filters: dict | None = None) -> list[dict]:
        """向量检索 + 元数据过滤"""
        # 构建过滤条件
        qdrant_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, dict) and "gte" in value:
                    # 范围过滤（如时间）
                    conditions.append(FieldCondition(
                        key=key, range=Range(**value)
                    ))
                else:
                    # 精确匹配
                    conditions.append(FieldCondition(
                        key=key, match=MatchValue(value=value)
                    ))
            qdrant_filter = Filter(must=conditions)

        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            query_filter=qdrant_filter,
            limit=top_k,
        )

        return [
            {
                "content": hit.payload.get("content", ""),
                "score": hit.score,
                "metadata": hit.payload,
            }
            for hit in results
        ]

# 用法示例：
# 纯向量检索
# results = store.search(query_emb, top_k=5)

# 向量 + 元数据过滤（只搜 PDF 文档）
# results = store.search(query_emb, top_k=5, filters={"doc_type": "pdf"})

# 向量 + 时间范围过滤
# results = store.search(query_emb, top_k=5, filters={
#     "created_at": {"gte": "2024-01-01"}
# })
```
### 6.4 实战：Qdrant 完整入库流程

```python
# ═══════════════════════════════════════
# 完整的 Pipeline：从文件到向量数据库
# ═══════════════════════════════════════
import asyncio
from pathlib import Path

async def ingest_pipeline(
    data_dir: str,
    qdrant_url: str = "http://localhost:6333",
    collection_name: str = "knowledge_base",
    embedding_model: str = "text-embedding-3-small",
):
    """一键运行：采集 → 清洗 → 分块 → 向量化 → 入库"""

    # Step 1: 采集
    print("=" * 50)
    print("📥 Step 1: 采集文档")
    all_docs = []
    for file in Path(data_dir).rglob("*"):
        if file.suffix in DocumentParser.PARSERS:
            docs = DocumentParser.parse(str(file))
            all_docs.extend(docs)
    print(f"  采集到 {len(all_docs)} 篇文档")

    # Step 2: 清洗
    print("🧹 Step 2: 清洗文档")
    clean_docs = run_cleaning_pipeline(all_docs)

    # Step 3: 分块
    print("✂️ Step 3: 文档分块")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )

    chunks = []
    for doc in clean_docs:
        texts = splitter.split_text(doc.content)
        for i, text in enumerate(texts):
            chunks.append(Chunk(
                content=text,
                doc_id=doc.doc_hash,
                chunk_index=i,
                metadata=doc.metadata,
            ))
    print(f"  生成 {len(chunks)} 个 chunk")

    # Step 4: Embedding
    print("🧮 Step 4: 生成 Embedding")
    generator = EmbeddingGenerator(model=embedding_model, batch_size=100)
    chunks = await generator.generate(chunks)

    # Step 5: 入库
    print("💾 Step 5: 写入向量数据库")
    store = VectorStore(
        url=qdrant_url,
        collection_name=collection_name,
        vector_size=len(chunks[0].embedding),
    )
    store.create_collection()
    result = store.batch_upsert(chunks)

    print("=" * 50)
    print(f"🎉 Pipeline 完成！共入库 {result['success']} 条向量")
    return result

# 运行：
# asyncio.run(ingest_pipeline("./data/knowledge_base/"))
```

> 💡 **第 6 章小结**：向量数据库选型看规模和生态，批量写入要做好错误处理和进度监控。元数据索引是企业级 RAG 的刚需——让用户可以按来源、时间、分类过滤检索。

---

## 7. 增量更新与数据维护

知识库不是"建一次就完事"——文档会更新、新增、删除。增量更新机制让你不需要每次全量重建。

### 7.1 变更检测与增量同步

```python
# ═══════════════════════════════════════
# 增量更新：只处理变化的文档
# ═══════════════════════════════════════
import json
from pathlib import Path

class IncrementalSync:
    """基于文件哈希的增量同步"""

    def __init__(self, state_file: str = ".sync_state.json"):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if Path(self.state_file).exists():
            return json.loads(Path(self.state_file).read_text())
        return {}

    def _save_state(self):
        Path(self.state_file).write_text(json.dumps(self.state, indent=2))

    def detect_changes(self, data_dir: str) -> dict:
        """检测文件变更：新增 / 修改 / 删除"""
        current_files = {}
        for file in Path(data_dir).rglob("*"):
            if file.is_file() and file.suffix in DocumentParser.PARSERS:
                content_hash = hashlib.md5(file.read_bytes()).hexdigest()
                current_files[str(file)] = content_hash

        # 分类变更
        added = {f: h for f, h in current_files.items() if f not in self.state}
        modified = {f: h for f, h in current_files.items()
                    if f in self.state and self.state[f] != h}
        deleted = {f: h for f, h in self.state.items() if f not in current_files}

        print(f"📊 变更检测: 新增 {len(added)}, 修改 {len(modified)}, 删除 {len(deleted)}")
        return {"added": added, "modified": modified, "deleted": deleted}

    def update_state(self, changes: dict):
        """更新同步状态"""
        for f, h in changes["added"].items():
            self.state[f] = h
        for f, h in changes["modified"].items():
            self.state[f] = h
        for f in changes["deleted"]:
            self.state.pop(f, None)
        self._save_state()
```

### 7.2 文档版本管理与一致性保障

```python
# ═══════════════════════════════════════
# 增量入库：删旧 → 插新（保证一致性）
# ═══════════════════════════════════════

async def incremental_ingest(data_dir: str, store: VectorStore):
    """增量入库：只处理变化的文件"""
    sync = IncrementalSync()
    changes = sync.detect_changes(data_dir)

    # 处理删除：从向量数据库中移除
    for file_path in changes["deleted"]:
        doc_hash = hashlib.md5(Path(file_path).read_bytes()).hexdigest()
        store.client.delete(
            collection_name=store.collection,
            points_selector=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_hash))]
            ),
        )
        print(f"🗑️ 已删除: {file_path}")

    # 处理新增和修改
    files_to_process = {**changes["added"], **changes["modified"]}

    if files_to_process:
        # 修改的文件：先删旧数据，再插新数据
        for file_path in changes["modified"]:
            old_hash = sync.state.get(file_path)
            if old_hash:
                store.client.delete(
                    collection_name=store.collection,
                    points_selector=Filter(
                        must=[FieldCondition(key="doc_id", match=MatchValue(value=old_hash))]
                    ),
                )

        # 解析 → 清洗 → 分块 → 向量化 → 入库
        docs = []
        for file_path in files_to_process:
            docs.extend(DocumentParser.parse(file_path))

        clean_docs = run_cleaning_pipeline(docs)
        # ... 分块 + Embedding + 入库（同第 6 章流程）

    # 更新状态
    sync.update_state(changes)
    print("✅ 增量同步完成")
```

### 7.3 定时任务与数据生命周期管理

```python
# ═══════════════════════════════════════
# 定时同步（APScheduler）
# ═══════════════════════════════════════
# pip install apscheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# 每小时执行一次增量同步
@scheduler.scheduled_job("interval", hours=1)
async def scheduled_sync():
    print(f"⏰ 定时同步开始: {datetime.now()}")
    store = VectorStore()
    await incremental_ingest("./data/knowledge_base/", store)

# 每天凌晨 3 点清理过期数据
@scheduler.scheduled_job("cron", hour=3)
async def cleanup_expired():
    """清理超过 90 天的旧数据"""
    store = VectorStore()
    cutoff = (datetime.now() - timedelta(days=90)).isoformat()
    store.client.delete(
        collection_name=store.collection,
        points_selector=Filter(
            must=[FieldCondition(key="created_at", range=Range(lt=cutoff))]
        ),
    )
    print(f"🗑️ 已清理 90 天前的数据")

scheduler.start()
```

> 💡 **第 7 章小结**：增量更新的核心是"**文件哈希 + 删旧插新**"。用 `.sync_state.json` 记录上次同步状态，每次只处理变化的文件。定时任务确保知识库自动保持最新。

---

## 8. 数据质量评估与优化

数据入库只是开始——你需要持续评测检索效果，找到瓶颈并优化。这是 RAG 系统从"能用"到"好用"的关键。

### 8.1 检索质量评测：Recall@K / MRR / NDCG

```
RAG 检索质量的三个核心指标：

  ① Recall@K（召回率）
  → 在 Top-K 结果中，有多少相关文档被检索到
  → Recall@5 = 0.8 → 5 条结果中包含了 80% 的相关文档
  → 最重要的指标——检索不到就没法回答

  ② MRR（Mean Reciprocal Rank，平均倒数排名）
  → 第一个相关结果出现在第几位
  → MRR = 1.0 → 第一条就是相关的（完美）
  → MRR = 0.5 → 平均第 2 条才是相关的

  ③ NDCG（Normalized Discounted Cumulative Gain）
  → 综合考虑相关性和排名位置
  → 排名越靠前、相关性越高，分数越高
  → 适合多级相关性评估
```

```python
# ═══════════════════════════════════════
# 简易评测工具
# ═══════════════════════════════════════

def evaluate_retrieval(queries: list[dict], store: VectorStore,
                       embedding_fn, top_k: int = 5) -> dict:
    """
    评测检索质量
    queries: [{"question": "...", "expected_doc_ids": ["id1", "id2"]}]
    """
    recalls = []
    mrrs = []

    for q in queries:
        query_emb = embedding_fn(q["question"])
        results = store.search(query_emb, top_k=top_k)

        retrieved_ids = [r["metadata"].get("doc_id") for r in results]
        expected = set(q["expected_doc_ids"])

        # Recall@K
        hits = len(expected & set(retrieved_ids))
        recall = hits / len(expected) if expected else 0
        recalls.append(recall)

        # MRR
        rr = 0
        for rank, rid in enumerate(retrieved_ids, 1):
            if rid in expected:
                rr = 1 / rank
                break
        mrrs.append(rr)

    metrics = {
        "Recall@K": f"{sum(recalls) / len(recalls):.2%}",
        "MRR": f"{sum(mrrs) / len(mrrs):.3f}",
        "total_queries": len(queries),
    }
    print(f"📊 评测结果: {metrics}")
    return metrics
```

### 8.2 端到端评测与 A/B 测试

```python
# ═══════════════════════════════════════
# 使用 RAGAS 进行端到端评测
# ═══════════════════════════════════════
# pip install ragas
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from datasets import Dataset

def ragas_evaluate(qa_pairs: list[dict]):
    """
    RAGAS 端到端评测
    qa_pairs: [{
        "question": "什么是中间件？",
        "answer": "中间件是...",          # RAG 生成的答案
        "contexts": ["检索到的文本..."],   # 检索到的上下文
        "ground_truth": "中间件是..."     # 标准答案
    }]
    """
    dataset = Dataset.from_list(qa_pairs)

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
    )

    print(f"📊 RAGAS 评测结果:")
    print(f"  Faithfulness:      {result['faithfulness']:.3f}")  # 答案忠实度
    print(f"  Answer Relevancy:  {result['answer_relevancy']:.3f}")  # 答案相关性
    print(f"  Context Precision: {result['context_precision']:.3f}")  # 上下文精度
    return result
```

```
A/B 测试分块策略的思路：

  实验组 A: chunk_size=300, overlap=30, 递归分块
  实验组 B: chunk_size=500, overlap=50, 递归分块
  实验组 C: chunk_size=500, 语义分块

  评测方法：
  1. 准备 50-100 条测试问答对
  2. 三组分别入库 → 检索 → 生成答案
  3. 对比 Recall@5 / MRR / RAGAS 分数
  4. 选择效果最好的配置上线
```

### 8.3 常见问题诊断与优化闭环

```
RAG 数据质量问题诊断表：

  症状                    可能原因                    优化方向
  ─────────────────────────────────────────────────────────────
  检索不到相关文档         分块太大 / Embedding 不好   减小 chunk_size / 换模型
  检索到无关内容           噪声数据未清洗             加强清洗 + 去重
  答案包含过时信息         旧文档未清理               加元数据时间过滤
  答案不完整               分块在句子中间截断          加 overlap / 用语义分块
  答案幻觉（编造内容）     检索到的上下文质量差        提高 Top-K / 加 Rerank
  重复检索相同内容         文档重复入库               加强去重策略
```

```
数据质量持续改进闭环：

  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ 用户提问  │ ──→ │ 检索+生成 │ ──→ │ 用户反馈  │
  └──────────┘     └──────────┘     └────┬─────┘
                                         │
                                         ▼
                                    ┌──────────┐
                                    │ 质量评测  │
                                    │ (RAGAS)   │
                                    └────┬─────┘
                                         │
         ┌───────────────────────────────┼───────────────────┐
         ▼                               ▼                   ▼
  ┌──────────┐               ┌──────────┐          ┌──────────┐
  │ 调整分块  │               │ 优化清洗  │          │ 换Embedding│
  │ 策略      │               │ 规则      │          │ 模型       │
  └──────────┘               └──────────┘          └──────────┘
         │                               │                   │
         └───────────────────────────────┼───────────────────┘
                                         ▼
                                    ┌──────────┐
                                    │ 重新入库  │
                                    └──────────┘
```

> 🎉 **全文完成**。企业级 RAG 数据 Pipeline 的核心链路：**采集 → 清洗 → 分块 → 向量化 → 入库 → 维护 → 评测**。记住：数据质量决定 RAG 上限，模型能力决定下限。先把数据搞干净，比换大模型更有效。

---
