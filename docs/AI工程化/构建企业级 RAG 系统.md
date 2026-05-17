# 构建企业级 RAG 系统

> 从"能用的 Demo"到"扛得住生产流量的系统"——深入企业级 RAG 的全链路工程实践：复杂文档解析、高级分块策略、查询理解与改写、多路召回与精排、端到端评测、以及生产环境的部署与运维。

---

## 1. 企业级 RAG 的挑战与架构设计

你可能已经跟着各种教程搭过一个 RAG Demo——加载文档、分块、向量化、检索、拼 Prompt、调 LLM——20 分钟就能跑起来。但当你把它交给真实用户使用时，问题立刻涌现：回答驴唇不对马嘴、PDF 表格全丢了、用户问稍微换个说法就检索不到……

这一章，我们先站在全局视角，看清 Demo 和生产之间的鸿沟，然后设计一套能支撑企业级需求的 RAG 架构。

### 1.1 Demo 级 RAG vs 生产级 RAG：差距在哪

先看一个典型的 Demo 级 RAG 长什么样：

```python
# Demo 级 RAG：20 行搞定
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 加载 → 分块 → 向量化 → 存储
docs = TextLoader("faq.txt").load()
chunks = RecursiveCharacterTextSplitter(chunk_size=500).split_documents(docs)
vectorstore = Chroma.from_documents(chunks, OpenAIEmbeddings())

# 检索 → 生成
retriever = vectorstore.as_retriever()
prompt = ChatPromptTemplate.from_template(
    "根据以下资料回答问题：\n{context}\n\n问题：{question}"
)
chain = prompt | ChatOpenAI() | StrOutputParser()

# 用户提问
docs = retriever.invoke("退货政策是什么？")
answer = chain.invoke({"context": docs, "question": "退货政策是什么？"})
```

这段代码能跑，但在真实业务中会暴露**至少 8 个致命问题**：

```
Demo 级 RAG 的致命问题：

1️⃣ 只能处理纯文本
   → 企业文档 80% 是 PDF、Word、PPT，里面还有表格和图片

2️⃣ 一刀切的分块策略
   → 把代码块切断、把表格拆散、把标题和正文分离

3️⃣ 用户原始查询直接检索
   → "我们那个系统咋退货来着" 这种口语化表达检索不到任何结果

4️⃣ 单路语义检索
   → 遇到精确术语（产品编号、法条编号）召回率骤降

5️⃣ 没有精排（Reranker）
   → Top-5 结果里可能 3 个是噪音

6️⃣ Prompt 太简陋
   → LLM 编造信息、不标注来源、无法拒绝回答

7️⃣ 没有评测
   → 改了 Prompt 不知道是变好还是变差

8️⃣ 没有监控
   → 上线后完全黑盒，问题只能靠用户投诉发现
```

**Demo 级 vs 企业级的差距一览：**

| 维度 | Demo 级 | 企业级 |
|:---|:---|:---|
| 文档格式 | 纯文本 / Markdown | PDF、Word、HTML、PPT、扫描件 |
| 分块策略 | 固定长度递归分块 | 语义分块 + 结构化分块 + 父子块 |
| 查询处理 | 原始查询直接检索 | 查询改写 + HyDE + Multi-Query |
| 检索方式 | 纯向量检索 | 多路召回（Dense + Sparse + 过滤） |
| 精排 | 无 | Cross-Encoder Reranker |
| 生成控制 | 简单 Prompt | 引用溯源 + 拒绝回答 + 自我检查 |
| 评测 | 手动试几个问题 | 自动化评测流水线 + 持续监控 |
| 运维 | 无 | 增量更新 + 监控告警 + 成本追踪 |

> 💡 **核心认知**：Demo 到生产的距离不是 20%，是 300%。RAG 的难点从来不在"跑通"，而在"跑好"——每个环节提升 5%，端到端就能从 60 分到 90 分。

### 1.2 企业级 RAG 的四大核心挑战

搭建企业级 RAG 系统时，你会反复踩进四个深坑。提前认清它们，才能在架构设计阶段就做好防御。

```
企业级 RAG 的四大核心挑战：

  挑战一：数据质量 ─── Garbage In, Garbage Out
  ═══════════════════════════════════════════════
  企业文档千奇百怪：
    • 扫描版 PDF（纯图片，不可复制文字）
    • Word 里的嵌套表格、批注、修订标记
    • HTML 里的导航栏、广告、页脚噪音
    • PPT 里的流程图（信息在图片里，不在文字里）
  
  → 如果解析不干净，后面全白搭

  挑战二：检索精度 ─── 找到"对的"而不是"像的"
  ═══════════════════════════════════════════════
  用户问 "2024 年 Q3 华东区销售额"
    • 语义检索找到一堆含"销售额"的文档 → 但年份、区域全不对
    • 需要 语义 + 结构化过滤（年份=2024, 区域=华东）
  
  用户问 "合同编号 HT-2024-0892 的违约条款"
    • 语义检索对精确编号无能为力
    • 需要 关键词检索兜底

  挑战三：可观测性 ─── 不能让系统当黑盒
  ═══════════════════════════════════════════════
  上线后你需要知道：
    • 每次检索返回了哪些文档？为什么返回它们？
    • 哪些问题的检索质量差？用户反馈了什么？
    • Prompt 版本 v2 比 v1 好在哪？数据说了算
  
  → 没有可观测性 = 盲人摸象式优化

  挑战四：成本控制 ─── 不能用 GPT-4 回答所有问题
  ═══════════════════════════════════════════════
  企业场景的 Token 消耗惊人：
    • 每次问答：检索 5 个 Chunk × 500 字 + Prompt ≈ 3000 Token 输入
    • 日均 10000 次问答 → 每天 3000 万 Token
    • 全用 GPT-4o → 每天 ~$150 → 每月 ~$4500
  
  → 需要模型分级、缓存策略、Batch 优化
```

**四大挑战的优先级排序：**

| 优先级 | 挑战 | 原因 |
|:---|:---|:---|
| 🥇 P0 | 数据质量 | 地基不牢，地动山摇 |
| 🥈 P1 | 检索精度 | 找不到对的文档，回答必然差 |
| 🥉 P2 | 可观测性 | 有数据才能持续优化 |
| 4️⃣ P3 | 成本控制 | 先做对，再做省 |

> 💡 **实战经验**：90% 的 RAG 质量问题最终都会追溯到前两个环节——要么是解析丢了信息，要么是检索找错了文档。先把数据质量和检索精度做好，其他问题都是锦上添花。

### 1.3 分层架构设计：数据层 → 检索层 → 生成层 → 评估层

一个企业级 RAG 系统，本质上由**四层架构**组成。每层各司其职，通过标准接口连接：

```
                    企业级 RAG 系统架构

  ┌─────────────────────────────────────────────────────┐
  │                  📊 评估层（Evaluation）              │
  │                                                      │
  │   检索评测  │  生成评测  │  端到端评测  │  监控告警    │
  │   Recall@K     Faithfulness   用户满意度    成本追踪   │
  ├─────────────────────────────────────────────────────┤
  │                  💬 生成层（Generation）              │
  │                                                      │
  │   Prompt 工程  │  引用溯源  │  拒绝策略  │  流式输出   │
  │   RAG Prompt     来源标注     知识边界       SSE      │
  ├─────────────────────────────────────────────────────┤
  │                  🔍 检索层（Retrieval）               │
  │                                                      │
  │   查询理解     │  多路召回      │  精排              │
  │   改写/HyDE      Dense+Sparse    Reranker            │
  │   Multi-Query    结构化过滤      Score Fusion         │
  ├─────────────────────────────────────────────────────┤
  │                  📄 数据层（Data）                    │
  │                                                      │
  │   文档解析  │  智能分块  │  Embedding  │  向量存储    │
  │   PDF/Word     语义分块     BGE-M3       Milvus      │
  │   OCR/表格     父子块       多语言       增量更新     │
  └─────────────────────────────────────────────────────┘
```

**每层的核心职责与关键指标：**

| 层级 | 核心职责 | 关键指标 | 本教程对应章节 |
|:---|:---|:---|:---|
| **数据层** | 把原始文档变成高质量的 Chunk + 向量 | 解析覆盖率、分块合理性 | 第 2-3 章 |
| **检索层** | 根据用户意图找到最相关的 Chunk | Recall@K、MRR、检索延迟 | 第 4-5 章 |
| **生成层** | 基于检索结果生成准确、可溯源的回答 | Faithfulness、相关性 | 第 6 章 |
| **评估层** | 量化系统质量、驱动持续优化 | 端到端准确率、用户满意度 | 第 7 章 |

**各层之间的数据流：**

```
用户提问："我们的年假制度是怎样的？"
    │
    ▼
┌─ 检索层 ───────────────────────────────────────────┐
│  ① 查询改写："年假制度" → "年休假天数规定 请假流程"    │
│  ② 多路召回：向量检索 20 条 + 关键词检索 20 条        │
│  ③ RRF 融合去重 → 30 条候选                          │
│  ④ Reranker 精排 → Top 5                            │
└────────────────────────────────────────────────────┘
    │
    ▼
┌─ 生成层 ───────────────────────────────────────────┐
│  ⑤ 组装 RAG Prompt（System + Context + Question）    │
│  ⑥ LLM 生成回答 + 引用来源标注                       │
│  ⑦ 后处理：格式化、安全检查                           │
└────────────────────────────────────────────────────┘
    │
    ▼
┌─ 评估层 ───────────────────────────────────────────┐
│  ⑧ 记录 Trace（查询 → 检索结果 → 生成结果 → 延迟）   │
│  ⑨ 异步评估：忠实度检查、质量评分                      │
│  ⑩ 聚合指标：日报/周报、告警                          │
└────────────────────────────────────────────────────┘
```

> 💡 **设计哲学**：四层架构的核心思想是**关注点分离**。数据层不关心检索策略，检索层不关心 Prompt 写法，评估层横切所有环节。这样每层可以独立迭代和优化，不会牵一发动全身。

### 1.4 技术选型与依赖安装

本教程的技术栈围绕**可落地的生产方案**选择，优先考虑社区成熟度和中文支持：

```
本教程的技术选型：

  组件              选型                 推荐理由
  ─────────────────────────────────────────────────────────
  框架              LangChain 0.3+       生态最丰富，组件最全
  文档解析          Unstructured         支持 PDF/Word/HTML/PPT 等 20+ 格式
  Embedding         BAAI/bge-m3          多语言、Dense+Sparse 一体
  向量数据库        Milvus 2.4+          生产级，支持混合检索
  Reranker          BAAI/bge-reranker    中文效果最佳
  LLM               DeepSeek / GPT-4o    按场景分级使用
  评测              RAGAS                RAG 评测事实标准
  可观测性          LangSmith            LangChain 原生集成
  ─────────────────────────────────────────────────────────

  替代方案（按需替换）：
  • Embedding：OpenAI text-embedding-3-small（省事、效果好）
  • 向量数据库：Chroma（轻量原型）、Qdrant（Rust 高性能）
  • LLM：Claude 3.5 Sonnet、Qwen-Plus（国内友好）
```

**安装依赖：**

```bash
# ── 核心框架 ──
pip install langchain langchain-core langchain-openai langchain-community

# ── 文档解析 ──
pip install unstructured[all-docs]   # PDF、Word、HTML、PPT 全格式支持
pip install pdfplumber               # PDF 表格提取（备选）

# ── Embedding + Reranker ──
pip install sentence-transformers    # BGE 模型运行时
pip install FlagEmbedding            # BGE-M3 和 Reranker

# ── 向量数据库 ──
pip install pymilvus                 # Milvus 客户端
# 或
pip install chromadb                 # Chroma（轻量方案）

# ── 评测 ──
pip install ragas                    # RAG 评测框架

# ── 工具 ──
pip install python-dotenv httpx      # 环境变量、HTTP 客户端
```

**验证安装：**

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# 验证 LLM 连接
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)
response = llm.invoke("你好，RAG！")
print(f"✅ LLM 连接成功: {response.content[:50]}")

# 验证 Embedding 模型
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-m3")
vector = model.encode("测试向量化")
print(f"✅ Embedding 模型加载成功，维度: {len(vector)}")

# 验证 Milvus 连接
from pymilvus import connections
connections.connect(host="localhost", port="19530")
print("✅ Milvus 连接成功")
```

> 💡 **本教程同时使用 DeepSeek 和 GPT-4o**。DeepSeek 用于日常问答（性价比高），GPT-4o 用于评测 Judge 和复杂推理场景。所有代码只需改一行配置即可切换模型。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Demo vs 生产** | 从能跑到好用，每个环节都需要工程化升级 |
| **四大挑战** | 数据质量 → 检索精度 → 可观测性 → 成本控制 |
| **四层架构** | 数据层 → 检索层 → 生成层 → 评估层，各层独立迭代 |
| **技术选型** | LangChain + BGE-M3 + Milvus + DeepSeek/GPT-4o |

---

## 2. 文档解析：把非结构化数据变成干净文本

RAG 的第一步不是 Embedding，不是向量检索——是**把各种格式的原始文档变成干净的纯文本**。这一步做不好，后面所有环节都是在"垃圾数据"上做优化，越优化越离谱。

### 2.1 为什么文档解析是 RAG 的第一道坎

看一组真实数据，你就明白解析的重要性了：

```
一个企业知识库的典型文档构成：

  格式          占比      解析难度     常见陷阱
  ──────────────────────────────────────────────────────
  PDF           45%       ⭐⭐⭐⭐    表格错位、扫描件、多栏排版
  Word          25%       ⭐⭐⭐      批注、修订标记、嵌套表格
  HTML/网页     15%       ⭐⭐        导航栏/页脚噪音、动态渲染
  Markdown      8%        ⭐          几乎无损
  PPT           5%        ⭐⭐⭐⭐    信息在图片和布局里
  Excel/CSV     2%        ⭐⭐        纯表格，需要转成自然语言描述
```

**PDF 是最大的"坑王"**——同一个 PDF 文件，不同解析器的输出可能天差地别：

```
同一份 PDF 的不同解析结果：

  原文（PDF 中的一个表格）：
  ┌────────────┬──────────┬──────────┐
  │ 产品名称    │ 单价     │ 库存量    │
  ├────────────┼──────────┼──────────┤
  │ Widget A   │ ¥99      │ 1500     │
  │ Widget B   │ ¥199     │ 800      │
  └────────────┴──────────┴──────────┘

  PyPDF2 解析结果（乱序）：
  "产品名称 单价 库存量 Widget A ¥99 1500 Widget B ¥199 800"
  → 表格结构完全丢失，信息混成一团

  pdfplumber 解析结果（保留结构）：
  "产品名称: Widget A, 单价: ¥99, 库存量: 1500
   产品名称: Widget B, 单价: ¥199, 库存量: 800"
  → 表格信息被正确提取为结构化文本

  Unstructured 解析结果（带元素分类）：
  [Table] 产品名称 | 单价 | 库存量
          Widget A | ¥99  | 1500
          Widget B | ¥199 | 800
  → 不仅保留结构，还标记了元素类型
```

**解析质量直接决定 RAG 的天花板**：

| 解析质量 | 对 RAG 的影响 |
|:---|:---|
| 表格结构丢失 | 用户问"Widget A 多少钱"→ 检索到混乱文本 → LLM 无法回答 |
| 页眉页脚未清理 | 每个 Chunk 都带"第X页 / 公司机密"→ 检索噪音 |
| 图片未处理 | 流程图、架构图里的关键信息完全丢失 |
| 编码问题 | 乱码 → 向量化质量暴跌 → 检索失败 |

> 💡 **核心认知**：文档解析是 RAG 系统中投入产出比最高的环节。在解析上多花 1 小时，比在检索和 Prompt 上调 3 天效果都好。

### 2.2 多格式解析实战：PDF、Word、HTML、Markdown

**PDF 解析**——根据 PDF 类型选择不同策略：

```python
import pdfplumber
from unstructured.partition.pdf import partition_pdf

# ── 方案 1：pdfplumber（适合有表格的 PDF） ──
def parse_pdf_with_pdfplumber(file_path: str) -> list[dict]:
    """解析 PDF，分别提取文本和表格"""
    results = []
    
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # 提取正文文本
            text = page.extract_text() or ""
            if text.strip():
                results.append({
                    "content": text,
                    "type": "text",
                    "metadata": {"source": file_path, "page": i + 1}
                })
            
            # 提取表格（转为 Markdown 格式）
            for table in page.extract_tables():
                md_table = table_to_markdown(table)
                results.append({
                    "content": md_table,
                    "type": "table",
                    "metadata": {"source": file_path, "page": i + 1}
                })
    
    return results

def table_to_markdown(table: list[list]) -> str:
    """将二维数组转为 Markdown 表格"""
    if not table or not table[0]:
        return ""
    
    # 表头
    header = "| " + " | ".join(str(cell or "") for cell in table[0]) + " |"
    separator = "| " + " | ".join("---" for _ in table[0]) + " |"
    
    # 表体
    rows = []
    for row in table[1:]:
        rows.append("| " + " | ".join(str(cell or "") for cell in row) + " |")
    
    return "\n".join([header, separator] + rows)
```

```python
# ── 方案 2：Unstructured（全能解析，适合复杂 PDF） ──
def parse_pdf_with_unstructured(file_path: str) -> list[dict]:
    """使用 Unstructured 解析 PDF，自动识别元素类型"""
    elements = partition_pdf(
        filename=file_path,
        strategy="hi_res",          # 高精度模式（较慢但准确）
        # strategy="fast",          # 快速模式（适合纯文本 PDF）
        infer_table_structure=True,  # 推断表格结构
        languages=["chi_sim", "eng"],  # 中英文 OCR
    )
    
    results = []
    for el in elements:
        results.append({
            "content": str(el),
            "type": el.category,  # "NarrativeText" / "Table" / "Title" 等
            "metadata": {
                "source": file_path,
                "page": el.metadata.page_number,
                "element_type": el.category,
            }
        })
    
    return results
```

```
PDF 解析策略选择：

  PDF 类型               推荐方案           原因
  ────────────────────────────────────────────────────
  纯文本 PDF             pdfplumber         简单快速
  含表格的 PDF           pdfplumber         表格提取最稳定
  扫描件 / 图片 PDF      Unstructured       内置 OCR 支持
  复杂排版（多栏等）     Unstructured       hi_res 模式处理好
  混合类型               Unstructured       一站式解决
```

**Word 文档解析：**

```python
from unstructured.partition.docx import partition_docx

def parse_word(file_path: str) -> list[dict]:
    """解析 Word 文档，保留标题层级"""
    elements = partition_docx(filename=file_path)
    
    results = []
    current_heading = ""
    
    for el in elements:
        # 记录当前所属标题（用于元数据）
        if el.category == "Title":
            current_heading = str(el)
        
        results.append({
            "content": str(el),
            "type": el.category,
            "metadata": {
                "source": file_path,
                "heading": current_heading,  # 所属章节标题
            }
        })
    
    return results
```

**HTML 解析——关键是去噪：**

```python
from unstructured.partition.html import partition_html
import re

def parse_html(file_path_or_url: str) -> list[dict]:
    """解析 HTML，自动去除导航栏、页脚等噪音"""
    elements = partition_html(
        filename=file_path_or_url,
        skip_headers_and_footers=True,  # 跳过页眉页脚
    )
    
    results = []
    for el in elements:
        text = str(el).strip()
        
        # 过滤噪音内容
        if len(text) < 10:  # 太短的内容通常是噪音
            continue
        if is_boilerplate(text):  # 模板化内容
            continue
        
        results.append({
            "content": text,
            "type": el.category,
            "metadata": {"source": file_path_or_url}
        })
    
    return results

def is_boilerplate(text: str) -> bool:
    """检测是否是模板化噪音内容"""
    patterns = [
        r"©\s*\d{4}",           # 版权声明
        r"All rights reserved",  # 版权声明
        r"cookie",               # Cookie 提示
        r"隐私政策",              # 隐私政策链接
        r"关注我们",              # 社交媒体引导
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)
```

**Markdown 解析——最简单但别大意：**

```python
def parse_markdown(file_path: str) -> list[dict]:
    """解析 Markdown，按标题层级拆分"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 按一级和二级标题拆分
    sections = re.split(r'\n(?=#{1,2}\s)', content)
    
    results = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # 提取标题
        title_match = re.match(r'^(#{1,6})\s+(.+)', section)
        title = title_match.group(2) if title_match else "无标题"
        level = len(title_match.group(1)) if title_match else 0
        
        results.append({
            "content": section,
            "type": "markdown_section",
            "metadata": {
                "source": file_path,
                "heading": title,
                "heading_level": level,
            }
        })
    
    return results
```

> 💡 **选择原则**：如果你的知识库 80% 以上是 PDF，直接用 Unstructured 一把梭最省事。如果对表格精度要求极高，用 pdfplumber 专门处理表格，Unstructured 处理正文。

### 2.3 表格与图片：结构化信息的保留策略

表格和图片是企业文档中**信息密度最高的部分**，但也是最容易在解析中丢失的。

**表格处理的三种策略：**

```
表格处理策略对比：

  策略                     适用场景           效果
  ──────────────────────────────────────────────────────
  1. 转 Markdown 表格       简单表格          保留结构，检索友好
  2. 转自然语言描述         复杂/嵌套表格      LLM 理解性最好
  3. 保留原始 + 摘要        数据密集型表格      兼顾精度和语义
```

```python
def table_to_natural_language(table: list[list], context: str = "") -> str:
    """
    将表格转为自然语言描述
    适合复杂表格：合并单元格、嵌套表格等
    """
    if not table or len(table) < 2:
        return ""
    
    headers = [str(h or "").strip() for h in table[0]]
    descriptions = []
    
    for row in table[1:]:
        cells = [str(c or "").strip() for c in row]
        # 将每行转为"字段: 值"的描述
        pairs = [f"{h}: {v}" for h, v in zip(headers, cells) if v]
        if pairs:
            descriptions.append("；".join(pairs))
    
    result = "。\n".join(descriptions) + "。"
    
    if context:
        result = f"以下是关于{context}的信息：\n{result}"
    
    return result

# 示例
table = [
    ["产品", "价格", "库存"],
    ["Widget A", "¥99", "1500"],
    ["Widget B", "¥199", "800"],
]

print(table_to_natural_language(table, "产品价格"))
# 以下是关于产品价格的信息：
# 产品: Widget A；价格: ¥99；库存: 1500。
# 产品: Widget B；价格: ¥199；库存: 800。
```

**图片处理——用多模态 LLM 生成文字描述：**

```python
import base64
from openai import OpenAI

def describe_image(image_path: str, context: str = "") -> str:
    """
    用多模态 LLM 描述图片内容
    适合：流程图、架构图、截图等
    """
    client = OpenAI()
    
    # 读取图片并编码
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    prompt = "请详细描述这张图片的内容。"
    if context:
        prompt += f"\n这张图片来自文档「{context}」，请结合上下文描述。"
    prompt += "\n重点描述：文字信息、流程步骤、数据关系。"
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{image_data}"
                &#125;&#125;,
            ],
        }],
        max_tokens=500,
    )
    
    return response.choices[0].message.content
```

```
图片处理决策树：

  图片类型是什么？
      │
  ┌───┼───────┬──────────┐
  │   │       │          │
  截图  流程图   数据图表   装饰图
  │   │       │          │
  OCR  多模态   多模态     跳过
  提取  LLM     LLM      （不影响
  文字  描述    描述      语义）
```

> 💡 **成本提示**：用 GPT-4o 描述图片每张约 ¥0.05-0.1。如果知识库有大量图片，建议先用规则过滤掉 Logo、装饰图等无信息图片，只对有内容的图片做多模态解析。

### 2.4 构建文档解析流水线（Pipeline）

把各种解析器组装成一条**自动化流水线**——丢进去任意格式的文档，自动检测格式、解析、清洗、输出标准化结果：

```python
from pathlib import Path
from dataclasses import dataclass
import hashlib
import re

@dataclass
class ParsedElement:
    """解析后的标准化文档元素"""
    content: str           # 文本内容
    element_type: str      # text / table / image_desc / title
    source: str            # 来源文件路径
    page: int = 0          # 页码（PDF/Word 有效）
    heading: str = ""      # 所属章节标题
    content_hash: str = "" # 内容哈希（用于去重）

class DocumentParser:
    """文档解析流水线"""
    
    # 支持的文件格式 → 解析器映射
    PARSER_MAP = {
        ".pdf": "parse_pdf",
        ".docx": "parse_word",
        ".doc": "parse_word",
        ".html": "parse_html",
        ".htm": "parse_html",
        ".md": "parse_markdown",
        ".txt": "parse_text",
    }
    
    def __init__(self, pdf_strategy: str = "unstructured"):
        self.pdf_strategy = pdf_strategy  # "pdfplumber" 或 "unstructured"
    
    def parse(self, file_path: str) -> list[ParsedElement]:
        """解析单个文档（自动检测格式）"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix not in self.PARSER_MAP:
            raise ValueError(f"不支持的文件格式: {suffix}")
        
        # 调用对应的解析器
        parser_method = getattr(self, self.PARSER_MAP[suffix])
        raw_elements = parser_method(file_path)
        
        # 后处理：清洗 + 去重 + 质量检查
        cleaned = self._clean(raw_elements)
        deduped = self._deduplicate(cleaned)
        
        return deduped
    
    def parse_directory(self, dir_path: str) -> list[ParsedElement]:
        """批量解析目录下所有文档"""
        all_elements = []
        path = Path(dir_path)
        
        for file in path.rglob("*"):
            if file.suffix.lower() in self.PARSER_MAP:
                try:
                    elements = self.parse(str(file))
                    all_elements.extend(elements)
                    print(f"✅ {file.name}: {len(elements)} 个元素")
                except Exception as e:
                    print(f"❌ {file.name}: {e}")
        
        print(f"\n总计: {len(all_elements)} 个元素")
        return all_elements
    
    def _clean(self, elements: list[ParsedElement]) -> list[ParsedElement]:
        """清洗：去噪、标准化"""
        cleaned = []
        for el in elements:
            text = el.content.strip()
            
            # 跳过空内容
            if not text or len(text) < 5:
                continue
            
            # 去除多余空白
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r' {2,}', ' ', text)
            
            # 去除页眉页脚模式
            if re.match(r'^第?\s*\d+\s*页', text):
                continue
            if re.match(r'^Page\s+\d+', text, re.IGNORECASE):
                continue
            
            el.content = text
            el.content_hash = hashlib.md5(text.encode()).hexdigest()
            cleaned.append(el)
        
        return cleaned
    
    def _deduplicate(self, elements: list[ParsedElement]) -> list[ParsedElement]:
        """基于内容哈希去重"""
        seen = set()
        unique = []
        for el in elements:
            if el.content_hash not in seen:
                seen.add(el.content_hash)
                unique.append(el)
        return unique

# ── 使用 ──
parser = DocumentParser(pdf_strategy="unstructured")

# 解析单个文件
elements = parser.parse("./docs/company_policy.pdf")
for el in elements[:3]:
    print(f"[{el.element_type}] {el.content[:80]}...")

# 批量解析目录
all_docs = parser.parse_directory("./knowledge_base/")
```

```
文档解析流水线的完整流程：

  📁 原始文档目录
      │
      ▼
  ① 格式检测（.pdf → PDF解析器 / .docx → Word解析器）
      │
      ▼
  ② 格式解析（提取文本、表格、图片）
      │
      ▼
  ③ 内容清洗（去页眉页脚、去多余空白、去噪音）
      │
      ▼
  ④ 内容去重（基于哈希去除完全重复）
      │
      ▼
  ⑤ 输出标准化元素列表
     每个元素 = content + type + metadata
      │
      ▼
  → 送入下一步：分块（第 3 章）
```

> 💡 **生产建议**：解析流水线建议跑在异步任务队列（Celery）中，因为大 PDF 的 OCR 解析可能需要几十秒。文档入库应该是后台任务，不要阻塞用户请求。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **解析的重要性** | 解析质量决定 RAG 天花板，Garbage In Garbage Out |
| **PDF 解析** | 简单 PDF 用 pdfplumber，复杂 PDF 用 Unstructured |
| **表格处理** | 转 Markdown 表格或自然语言描述，保留结构信息 |
| **图片处理** | 多模态 LLM 生成描述，先过滤无信息图片控制成本 |
| **解析流水线** | 自动检测格式 → 解析 → 清洗 → 去重 → 标准化输出 |

---

## 3. 高级分块策略：让每个 Chunk 都有意义

上一章把文档解析成了干净的文本元素。这一章解决下一个关键问题：**怎么把长文本切成大小合适、语义完整的块（Chunk）**。分块策略直接决定检索质量——切得好，用户一问就能命中；切得差，答案就在文档里但死活检索不到。

### 3.1 基础分块的局限性

我们在向量数据库教程中已经学过 `RecursiveCharacterTextSplitter`——按字符数切割，遇到段落分隔符优先切。它覆盖了 80% 的场景，但在企业文档中会遇到**三个致命问题**：

```
基础分块的三大局限：

  问题一：语义被切断
  ════════════════════════════════════════════════
  原文：
    "Python 的 GIL（Global Interpreter Lock）是 CPython 中的
     全局解释器锁。它的作用是确保同一时刻只有一个线程执行
     Python 字节码。这意味着 Python 的多线程无法利用多核
     CPU 进行并行计算。但 I/O 密集型任务仍然可以从多线
  ─ ─ ─ ─ ─ ─ ← chunk_size=200，这里被切断
     程中受益，因为 GIL 在等待 I/O 时会释放。"

  → 第一个 Chunk 只有问题描述，没有解决方案
  → 第二个 Chunk 只有解决方案，没有上下文
  → 用户问"Python 多线程能不能用"→ 两个 Chunk 都答不全

  问题二：标题和正文分离
  ════════════════════════════════════════════════
  原文：
    "## 3.2 退货政策
     顾客可在购买后 30 天内无理由退货。退货商品需保持原包装..."

  如果 chunk_size 刚好把标题切到上一个 Chunk：
    Chunk A：[...前文内容...] ## 3.2 退货政策
    Chunk B：顾客可在购买后 30 天内无理由退货...

  → Chunk B 丢失了"这是退货政策"的上下文
  → 用户问"退货政策"→ Chunk B 可能检索不到（没有标题关键词）

  问题三：表格和代码块被拆散
  ════════════════════════════════════════════════
  一个 20 行的代码块被切成两半：
    Chunk A：```python\ndef process(data):\n    result = []\n    for item...
    Chunk B：    ...in data:\n        result.append(transform(item))\n    return result\n```

  → 两半代码都不完整，都无法理解
  → 向量化后语义也是碎片
```

**基础分块 vs 高级分块的效果对比：**

| 场景 | 基础分块 Recall@5 | 高级分块 Recall@5 | 提升 |
|:---|:---|:---|:---|
| 常规段落文本 | 78% | 82% | +4% |
| 含标题层级的文档 | 65% | 84% | **+19%** |
| 含表格的文档 | 52% | 79% | **+27%** |
| 代码密集型文档 | 58% | 81% | **+23%** |

> 💡 **核心认知**：基础分块在"纯文本、无结构"的文档上表现尚可，但面对真实企业文档（有标题、有表格、有代码），高级分块策略能带来 **15-25% 的检索召回率提升**。

### 3.2 语义分块：基于 Embedding 相似度的智能切分

语义分块的核心思想：**不按字符数切，按语义切**。相邻句子的 Embedding 相似度骤降的地方，就是主题切换点——在那里切一刀。

```
语义分块的原理：

  句子 1: "Python 是一门解释型语言..."          ┐
  句子 2: "它支持多种编程范式..."               ├ 相似度高 → 同一主题
  句子 3: "Python 3.12 引入了模式匹配..."       ┘
                                                 ← 相似度骤降 = 切割点
  句子 4: "如何安装 Python 开发环境..."          ┐
  句子 5: "首先下载 Python 安装包..."           ├ 相似度高 → 同一主题
  句子 6: "配置环境变量 PATH..."                ┘

  对比基础分块：
    基础分块：每 500 字切一刀 → 可能把"主题A的结尾"和"主题B的开头"混在一起
    语义分块：在主题切换处切  → 每个 Chunk 只讲一个完整的子主题
```

```python
import numpy as np
from sentence_transformers import SentenceTransformer

class SemanticChunker:
    """基于语义相似度的智能分块器"""
    
    def __init__(self, model_name: str = "BAAI/bge-m3",
                 similarity_threshold: float = 0.5,
                 max_chunk_size: int = 800,
                 min_chunk_size: int = 100):
        self.model = SentenceTransformer(model_name)
        self.threshold = similarity_threshold
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
    
    def chunk(self, text: str) -> list[str]:
        """将文本按语义边界切分"""
        # 1. 按句子拆分
        sentences = self._split_sentences(text)
        if len(sentences) <= 1:
            return [text]
        
        # 2. 计算每个句子的 Embedding
        embeddings = self.model.encode(sentences)
        
        # 3. 计算相邻句子的余弦相似度
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)
        
        # 4. 找到相似度骤降的位置（= 主题切换点）
        breakpoints = self._find_breakpoints(similarities)
        
        # 5. 按切割点生成 Chunk
        chunks = self._merge_by_breakpoints(sentences, breakpoints)
        
        return chunks
    
    def _split_sentences(self, text: str) -> list[str]:
        """按句号、换行等拆分句子"""
        import re
        sentences = re.split(r'(?<=[。！？\n])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _cosine_similarity(self, a, b) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def _find_breakpoints(self, similarities: list[float]) -> list[int]:
        """找到相似度低于阈值的位置作为切割点"""
        breakpoints = []
        for i, sim in enumerate(similarities):
            if sim < self.threshold:
                breakpoints.append(i + 1)  # 在第 i+1 个句子前切
        return breakpoints
    
    def _merge_by_breakpoints(self, sentences: list[str],
                               breakpoints: list[int]) -> list[str]:
        """按切割点合并句子为 Chunk，同时控制大小"""
        chunks = []
        start = 0
        
        for bp in breakpoints + [len(sentences)]:
            chunk_text = "".join(sentences[start:bp])
            
            # 如果 Chunk 太大，回退到基础分块
            if len(chunk_text) > self.max_chunk_size:
                # 按 max_chunk_size 再次拆分
                for i in range(0, len(chunk_text), self.max_chunk_size):
                    sub = chunk_text[i:i + self.max_chunk_size]
                    if len(sub) >= self.min_chunk_size:
                        chunks.append(sub)
            elif len(chunk_text) >= self.min_chunk_size:
                chunks.append(chunk_text)
            elif chunks:
                # 太短的 Chunk 合并到上一个
                chunks[-1] += chunk_text
            
            start = bp
        
        return chunks

# ── 使用 ──
chunker = SemanticChunker(similarity_threshold=0.5)
chunks = chunker.chunk(long_document_text)

for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1} ({len(chunk)} 字): {chunk[:60]}...")
```

```
语义分块的参数调优：

  similarity_threshold（切割阈值）：
    0.3 → 切得很碎（每个 Chunk 很短，语义很集中）
    0.5 → 中等（推荐起点）
    0.7 → 切得很粗（每个 Chunk 较长，可能混入多个子主题）

  → 建议用自己的数据试 0.4~0.6，看检索效果调整

  计算开销：
    需要对所有句子做一次 Embedding（只在入库时跑一次）
    1000 个句子 ≈ 3-5 秒（GPU）/ 15-30 秒（CPU）
    → 离线处理，不影响在线查询性能
```

> 💡 **何时用语义分块**：文档内容主题多变、段落间没有明显的结构化标记（标题、分隔线）时效果最好。如果文档本身有清晰的标题层级，优先用下一节的层级分块。

### 3.3 层级分块与父子关系：Small-to-Big 检索策略

这是企业级 RAG 中**最有价值的分块技巧**。核心思想：**用小块做检索（精准命中），用大块送给 LLM（完整上下文）**。

```
Small-to-Big 检索策略：

  原始文档（一个章节）
  ┌──────────────────────────────────────────────┐
  │ ## 3. 退货政策                                │
  │                                               │
  │ 3.1 退货条件                                   │ ← Parent Chunk
  │ 顾客可在购买后 30 天内退货，商品需保持原包装... │    （大块，~1500 字）
  │                                               │
  │ 3.2 退货流程                                   │
  │ 第一步：登录官网提交退货申请...                  │
  │ 第二步：打印退货标签...                         │
  │                                               │
  │ 3.3 退款时间                                   │
  │ 退款将在收到退货后 5-7 个工作日内处理...         │
  └──────────────────────────────────────────────┘
        │
        │ 拆分为小块
        ▼
  ┌────────────┐  ┌────────────┐  ┌────────────┐
  │ Child 1:   │  │ Child 2:   │  │ Child 3:   │
  │ 3.1 退货条件│  │ 3.2 退货流程│  │ 3.3 退款时间│  ← Child Chunks
  │ (~300 字)  │  │ (~400 字)  │  │ (~200 字)  │     （小块，用于检索）
  └────────────┘  └────────────┘  └────────────┘

  检索时：
    用户问 "退款要多久" → 命中 Child 3（精准匹配）
    送给 LLM 的是 Parent Chunk（包含完整退货政策上下文）
    → LLM 能给出更全面的回答
```

```python
from dataclasses import dataclass, field
import uuid

@dataclass
class HierarchicalChunk:
    """层级 Chunk：支持父子关系"""
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = ""
    parent_id: str = ""      # 父 Chunk ID（空 = 自己就是顶层）
    children_ids: list = field(default_factory=list)
    level: int = 0           # 0=parent, 1=child
    metadata: dict = field(default_factory=dict)

class HierarchicalChunker:
    """层级分块器：生成 Parent + Child 双层 Chunk"""
    
    def __init__(self, parent_chunk_size: int = 1500,
                 child_chunk_size: int = 300,
                 child_overlap: int = 50):
        self.parent_size = parent_chunk_size
        self.child_size = child_chunk_size
        self.child_overlap = child_overlap
    
    def chunk(self, text: str, source: str = "") -> list[HierarchicalChunk]:
        """生成父子层级 Chunk"""
        all_chunks = []
        
        # 1. 先按大块切（Parent）
        parent_texts = self._split_by_size(text, self.parent_size)
        
        for parent_text in parent_texts:
            parent = HierarchicalChunk(
                content=parent_text,
                level=0,
                metadata={"source": source, "role": "parent"}
            )
            
            # 2. 每个 Parent 再切成小块（Children）
            child_texts = self._split_by_size(
                parent_text, self.child_size, self.child_overlap
            )
            
            for child_text in child_texts:
                child = HierarchicalChunk(
                    content=child_text,
                    parent_id=parent.chunk_id,
                    level=1,
                    metadata={
                        "source": source,
                        "role": "child",
                        "parent_id": parent.chunk_id,
                    }
                )
                parent.children_ids.append(child.chunk_id)
                all_chunks.append(child)
            
            all_chunks.append(parent)
        
        return all_chunks
    
    def _split_by_size(self, text, size, overlap=0):
        """按大小切分文本"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=size, chunk_overlap=overlap,
            separators=["\n\n", "\n", "。", "，", " ", ""]
        )
        return splitter.split_text(text)

# ── 检索时的使用方式 ──
def retrieve_with_parent(query: str, child_collection, 
                          parent_store: dict, top_k: int = 3):
    """
    Small-to-Big 检索：
    1. 用 Child Chunk 做向量检索（精准命中）
    2. 返回对应的 Parent Chunk（完整上下文）
    """
    # 在 Child 集合中检索
    results = child_collection.query(query_texts=[query], n_results=top_k * 2)
    
    # 去重：同一个 Parent 只取一次
    seen_parents = set()
    parent_chunks = []
    
    for metadata in results["metadatas"][0]:
        parent_id = metadata.get("parent_id", "")
        if parent_id and parent_id not in seen_parents:
            seen_parents.add(parent_id)
            parent_chunks.append(parent_store[parent_id])
        
        if len(parent_chunks) >= top_k:
            break
    
    return parent_chunks  # 返回完整的 Parent Chunk 给 LLM
```

**Small-to-Big 的效果：**

| 策略 | 检索精度 | LLM 回答质量 | 原因 |
|:---|:---|:---|:---|
| 只用大块检索 | 中等 | 高 | 大块语义模糊，检索不够精准 |
| 只用小块检索 + 小块给 LLM | 高 | **低** | 检索精准但上下文不足 |
| **小块检索 + 大块给 LLM** | **高** | **高** | 两全其美 ✅ |

> 💡 **推荐参数**：Parent 块 1000-2000 字，Child 块 200-400 字。Child 块用来检索，Parent 块用来喂给 LLM。这是目前生产环境中效果最好的分块策略之一。

### 3.4 Chunk 元数据设计：让检索更精准

分块不只是切文本——**给每个 Chunk 打上丰富的元数据标签**，能让检索从"语义匹配"升级为"语义 + 结构化过滤"的组合拳。

```
为什么元数据很重要？

  没有元数据的检索：
    用户问 "2024 年的退货政策"
    → 向量检索返回 5 个含"退货政策"的 Chunk
    → 其中 3 个是 2022 年的旧版本 ← 答错了！

  有元数据的检索：
    用户问 "2024 年的退货政策"
    → 向量检索 + 过滤 year=2024
    → 只返回 2024 年版本的 Chunk ← 精准命中
```

**推荐的 Chunk 元数据 Schema：**

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ChunkMetadata:
    """企业级 Chunk 元数据标准"""
    
    # ── 来源信息 ──
    source: str = ""              # 文件路径或 URL
    source_type: str = ""         # pdf / docx / html / markdown
    page: int = 0                 # 页码（PDF/Word）
    
    # ── 结构信息 ──
    heading: str = ""             # 所属章节标题
    heading_level: int = 0        # 标题层级（1=H1, 2=H2...）
    chunk_index: int = 0          # 在文档中的序号
    element_type: str = "text"    # text / table / code / image_desc
    
    # ── 层级关系 ──
    parent_id: str = ""           # 父 Chunk ID
    role: str = "standalone"      # parent / child / standalone
    
    # ── 业务信息 ──
    department: str = ""          # 所属部门（HR / 技术 / 财务）
    doc_category: str = ""        # 文档类别（制度 / 教程 / FAQ）
    version: str = ""             # 文档版本号
    effective_date: str = ""      # 生效日期
    
    # ── 技术信息 ──
    content_hash: str = ""        # 内容哈希（去重）
    char_count: int = 0           # 字符数
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
```

**利用元数据做结构化过滤：**

```python
# ── Milvus 中的结构化过滤示例 ──

# 场景 1：只搜索特定部门的文档
results = collection.search(
    data=[query_embedding],
    anns_field="dense_embedding",
    param={"metric_type": "COSINE"},
    limit=10,
    expr='department == "HR"',     # 只搜 HR 部门的文档
    output_fields=["content", "heading", "source"]
)

# 场景 2：搜索特定时间段的制度文件
results = collection.search(
    data=[query_embedding],
    anns_field="dense_embedding",
    param={"metric_type": "COSINE"},
    limit=10,
    expr='doc_category == "制度" and effective_date >= "2024-01-01"',
    output_fields=["content", "heading", "version"]
)

# 场景 3：只搜索表格类型的 Chunk（用户问数据类问题）
results = collection.search(
    data=[query_embedding],
    anns_field="dense_embedding",
    param={"metric_type": "COSINE"},
    limit=10,
    expr='element_type == "table"',
    output_fields=["content", "source", "page"]
)
```

**在 Chunk 内容中注入标题上下文：**

```python
def enrich_chunk_with_heading(chunk_text: str, heading: str) -> str:
    """
    把章节标题注入到 Chunk 文本前面
    解决"标题和正文分离"导致的检索失败问题
    """
    if heading and heading not in chunk_text:
        return f"[{heading}]\n{chunk_text}"
    return chunk_text

# 示例
chunk = "顾客可在购买后 30 天内无理由退货。退货商品需保持原包装..."
enriched = enrich_chunk_with_heading(chunk, "退货政策")
# → "[退货政策]\n顾客可在购买后 30 天内无理由退货..."
# 现在搜"退货政策"就能命中这个 Chunk 了！
```

**分块策略完整选型指南：**

```
不同文档类型的最佳分块策略：

  文档类型         推荐分块策略              关键参数
  ──────────────────────────────────────────────────────────
  纯文本/博客      递归字符分块              size=500, overlap=100
  技术文档(有标题) 按标题层级 + 递归分块      按 ## 切 Parent, ### 切 Child
  FAQ / Q&A       按问答对切分              每个 Q+A 为一个 Chunk
  法律合同         按条款编号切分            每个条款 = 一个 Chunk
  代码文件         按函数/类切分             保持代码块完整
  混合型文档       层级分块(Small-to-Big)    Parent=1500, Child=300
  无结构长文       语义分块                  threshold=0.5
```

> 💡 **实战建议**：不要执着于找到"完美的分块策略"——先用递归字符分块快速上线，然后通过评测数据发现具体哪类文档检索效果差，针对性地优化分块策略。这就是第 7 章"评测驱动优化"的思路。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **基础分块局限** | 语义切断、标题分离、表格拆散，结构化文档检索暴跌 |
| **语义分块** | 按 Embedding 相似度变化切割，每个 Chunk 语义完整 |
| **Small-to-Big** | 小块检索精准命中，大块（Parent）提供完整上下文给 LLM |
| **元数据设计** | 部门/类别/日期/标题等标签，支持结构化过滤 |
| **标题注入** | 把章节标题拼到 Chunk 前面，解决标题丢失问题 |

---

## 4. 查询理解与改写：让检索"听懂"用户意图

前面三章解决了"数据怎么存"的问题。从这一章开始，我们聚焦"数据怎么找"。用户输入的查询往往是口语化、模糊、甚至有歧义的——直接拿去做向量检索，效果会大打折扣。**查询理解与改写**就是在检索前，先把用户的问题"翻译"成更适合检索的形式。

### 4.1 为什么原始查询直接检索效果差

看几个真实场景，你就明白为什么不能直接把用户的原始问题丢给向量数据库：

```
原始查询直接检索的三种失败模式：

  失败模式一：口语化 vs 书面化
  ════════════════════════════════════════════════
  用户问：  "咱们公司请假咋整啊"
  知识库：  "员工请假须通过 OA 系统提交申请..."
  
  → 语义相关，但措辞差异太大
  → Embedding 相似度只有 0.42 → 检索不到

  改写后："公司请假流程和申请方式"
  → 相似度提升到 0.81 → 检索命中 ✅

  失败模式二：过于简短
  ════════════════════════════════════════════════
  用户问：  "GIL"
  知识库：  "Python 的 GIL（Global Interpreter Lock）是..."

  → 3 个字符的查询向量几乎没有语义信息
  → 什么都检索不到，或者检索到不相关的内容

  改写后："Python GIL 全局解释器锁的原理和影响"
  → 语义信息丰富，精准命中 ✅

  失败模式三：多轮对话中的指代
  ════════════════════════════════════════════════
  用户第一轮："Python 和 Java 哪个更适合做后端？"
  用户第二轮："那它的性能怎么样？"

  → "它"指的是什么？Python？Java？
  → 直接拿"那它的性能怎么样"去检索 → 完全检索不到

  改写后："Python 做后端的性能表现如何"
  → 补全了指代，精准检索 ✅
```

**查询质量对检索效果的量化影响：**

| 查询类型 | 平均 Recall@5 | 示例 |
|:---|:---|:---|
| 精确书面查询 | 85% | "员工年休假天数规定" |
| 口语化查询 | 58% | "年假几天啊" |
| 过于简短 | 35% | "年假" |
| 多轮指代 | 22% | "那个怎么算" |
| **经过改写** | **82-90%** | **自动改写为检索友好的形式** |

> 💡 **核心认知**：查询改写是"性价比最高"的 RAG 优化手段——不需要改动知识库、不需要重新向量化、只需要在检索前加一步处理，就能把召回率从 50-60% 提升到 80-90%。

### 4.2 查询改写（Query Rewriting）：让问题更具检索性

最直接的方案：**用 LLM 把用户的口语化问题改写成检索友好的形式**。

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1")

# ── 查询改写 Prompt ──
rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个查询改写助手。将用户的口语化问题改写为更适合知识库检索的形式。

改写规则：
1. 保持原意，不要添加或改变意思
2. 使用书面化、专业化的表达
3. 补充必要的关键词（如缩写的全称）
4. 如果用户问题已经很规范，不需要改写，直接返回原文
5. 只返回改写后的查询，不要解释"""),
    ("human", "{query}"),
])

rewrite_chain = rewrite_prompt | llm | StrOutputParser()

# 测试
print(rewrite_chain.invoke({"query": "咱们公司请假咋整啊"}))
# → "公司员工请假流程和申请方式"

print(rewrite_chain.invoke({"query": "GIL"}))
# → "Python GIL（Global Interpreter Lock）全局解释器锁的原理"
```

**处理多轮对话中的指代——上下文感知改写：**

```python
# ── 带对话历史的查询改写 ──
contextualize_prompt = ChatPromptTemplate.from_messages([
    ("system", """根据对话历史，将用户的最新问题改写为一个独立的、完整的问题。
要求：消除指代词（它、这个、那个），补全上下文信息。
如果最新问题已经是独立的，直接返回原文。
只返回改写后的问题。"""),
    ("human", """对话历史：
{chat_history}

最新问题：{query}"""),
])

contextualize_chain = contextualize_prompt | llm | StrOutputParser()

# 测试
result = contextualize_chain.invoke({
    "chat_history": "用户: Python 和 Java 哪个更适合做后端？\nAI: 两者各有优势...",
    "query": "那它的性能怎么样？"
})
print(result)
# → "Python 做后端开发的性能表现如何"
```

```
查询改写的完整流程：

  用户原始查询
      │
      ▼
  是否是多轮对话？─── 是 ──→ 先做指代消解
      │                       │
      否                      ▼
      │               独立化后的查询
      ▼                       │
  是否口语化/过短？── 是 ──→ LLM 改写
      │                       │
      否                      ▼
      │               改写后的查询
      ▼                       │
  原始查询（不改写）           │
      │                       │
      └───────┬───────────────┘
              ▼
         送入检索层
```

> 💡 **性能提示**：查询改写会增加一次 LLM 调用（~200-500ms）。可以用小模型（DeepSeek-chat / GPT-3.5-turbo）做改写，性价比更高。也可以本地部署 Qwen-1.8B 等小模型做改写，延迟可压到 50ms 以内。

### 4.3 HyDE：用假设答案提升检索召回

HyDE（Hypothetical Document Embeddings）是一个巧妙的思路：**不用问题去检索，用"假设的答案"去检索**。因为答案和文档的措辞更接近，检索效果更好。

```
HyDE 的核心思路：

  传统方式：
    问题 "Python GIL 怎么绕过"  ──→  Embedding  ──→  检索
                                      ↑ 问题和文档的措辞差异大

  HyDE 方式：
    问题 "Python GIL 怎么绕过"
      │
      ▼ LLM 生成假设答案（不需要准确）
    "可以使用多进程(multiprocessing)替代多线程，
     或使用 C 扩展释放 GIL，或使用其他 Python
     实现如 PyPy..."
      │
      ▼ 用假设答案做 Embedding
    Embedding  ──→  检索
      ↑ 假设答案和真实文档的措辞更接近！
```

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ── HyDE Prompt：让 LLM 生成假设答案 ──
hyde_prompt = ChatPromptTemplate.from_messages([
    ("system", """请根据用户的问题，写一段假设性的回答。
要求：
- 不需要完全正确，写出你认为合理的答案即可
- 使用专业术语和书面化表达
- 控制在 100-200 字
- 直接写答案，不要说"我认为"或"可能是"这样的前缀"""),
    ("human", "{query}"),
])

hyde_chain = hyde_prompt | llm | StrOutputParser()

def retrieve_with_hyde(query: str, retriever, llm_chain, top_k: int = 5):
    """HyDE 检索：用假设答案代替原始问题做检索"""
    
    # 1. 生成假设答案
    hypothetical_doc = llm_chain.invoke({"query": query})
    
    # 2. 用假设答案做向量检索（而不是用原始问题）
    results = retriever.similarity_search(hypothetical_doc, k=top_k)
    
    return results

# 使用
results = retrieve_with_hyde("GIL怎么绕过", retriever, hyde_chain)
```

**HyDE 的效果对比：**

| 查询类型 | 直接检索 Recall@5 | HyDE Recall@5 | 提升 |
|:---|:---|:---|:---|
| 简短查询（"GIL"） | 35% | 72% | **+37%** |
| 口语化查询 | 58% | 78% | **+20%** |
| 概念性问题 | 62% | 81% | **+19%** |
| 已经很精确的查询 | 85% | 83% | -2% |

```
HyDE 的适用场景：

  ✅ 适合：简短/模糊的查询、概念性问题、问"怎么做"类问题
  ❌ 不适合：精确查询（产品编号、人名）、已经很规范的查询
  
  → HyDE 的假设答案可能"编造"细节，如果用来检索精确信息反而会偏
  → 最佳实践：HyDE + 原始查询 同时检索，取并集
```

> 💡 **HyDE 的代价**：多一次 LLM 调用（生成假设答案）。适合质量优先的场景。如果延迟敏感，可以和 Query Rewriting 二选一——两者解决的问题类似，HyDE 在简短查询上效果更好。

### 4.4 Multi-Query：多角度查询扩展

一个问题可以从多个角度提问。Multi-Query 的思路：**让 LLM 把原始问题改写成 3-5 个不同视角的查询，每个查询分别检索，最后合并去重**。

```
Multi-Query 的原理：

  原始问题："Python 异步编程怎么做"
      │
      ▼ LLM 生成多角度查询
  ┌─ "Python asyncio 异步编程入门教程"
  │
  ├─ "Python 协程 coroutine 的使用方法"
  │
  └─ "Python 并发编程 async await 语法"
      │
      ▼ 每个查询分别检索
  ┌─ 检索结果 A（5 条）
  ├─ 检索结果 B（5 条）
  └─ 检索结果 C（5 条）
      │
      ▼ 合并去重
  最终结果（8-12 条不重复的高质量文档）
```

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ── Multi-Query Prompt ──
multi_query_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个查询扩展助手。将用户的问题改写为 3 个不同角度的查询。

要求：
1. 每个查询从不同角度/维度提问
2. 使用不同的关键词和表达方式
3. 每行一个查询，不要编号
4. 保持与原始问题相同的意图"""),
    ("human", "{query}"),
])

multi_query_chain = multi_query_prompt | llm | StrOutputParser()

def retrieve_with_multi_query(query: str, retriever, 
                                llm_chain, top_k: int = 5):
    """Multi-Query 检索：多角度查询 + 合并去重"""
    
    # 1. 生成多个查询
    queries_text = llm_chain.invoke({"query": query})
    queries = [q.strip() for q in queries_text.split("\n") if q.strip()]
    
    # 加上原始查询
    all_queries = [query] + queries
    
    # 2. 每个查询分别检索
    all_docs = []
    seen_contents = set()
    
    for q in all_queries:
        results = retriever.similarity_search(q, k=top_k)
        for doc in results:
            # 基于内容去重
            content_hash = hash(doc.page_content[:200])
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                all_docs.append(doc)
    
    # 3. 按相关性排序（可选：用 Reranker 重排）
    return all_docs[:top_k]

# 使用
results = retrieve_with_multi_query(
    "Python 异步编程怎么做", retriever, multi_query_chain
)
```

**三种查询增强策略对比：**

| 策略 | 原理 | LLM 调用次数 | 检索调用次数 | 最佳场景 |
|:---|:---|:---|:---|:---|
| **Query Rewriting** | 改写为检索友好形式 | 1 次 | 1 次 | 口语化/指代问题 |
| **HyDE** | 用假设答案做检索 | 1 次 | 1 次 | 简短/模糊查询 |
| **Multi-Query** | 多角度查询取并集 | 1 次 | 3-5 次 | 需要高召回率 |

> 💡 **生产环境推荐组合**：Query Rewriting（必选，处理指代和口语化）+ Multi-Query（可选，需要高召回率时启用）。HyDE 和 Multi-Query 二选一即可，同时使用成本太高。

### 4.5 查询路由：根据意图选择检索策略

不同类型的问题需要不同的检索策略。**查询路由**就是先分析用户意图，再决定走哪条检索路径。

```
查询路由决策：

  用户查询
      │
      ▼
  LLM 意图分类
      │
  ┌───┼────────┬─────────────┐
  │   │        │             │
  知识库问答  精确数据查询   闲聊/通用
  │   │        │             │
  │   │        │             ▼
  │   │        │         LLM 直接回答
  │   │        │         （不走检索）
  │   │        ▼
  │   │   SQL 数据库查询
  │   │   （结构化数据）
  │   ▼
  │  向量检索 + Reranker
  │  （非结构化知识）
  ▼
  根据分数决定是否使用检索结果
```

::: v-pre
```python
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

class RouteDecision(BaseModel):
    """路由决策结果"""
    route: str = Field(description="路由目标: rag / database / direct")
    confidence: float = Field(description="置信度 0-1")
    reason: str = Field(description="路由原因")

# ── 查询路由器 ──
router_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个查询路由器。根据用户问题判断应该走哪条处理路径。

路由规则：
- "rag": 需要查询知识库（公司制度、产品文档、技术方案等）
- "database": 需要查询具体业务数据（订单、库存、用户信息等）
- "direct": 通用知识或闲聊，LLM 可以直接回答

我们的知识库包含：公司规章制度、产品使用文档、技术架构方案、FAQ。

返回 JSON 格式：
&#123;&#123;"route": "rag/database/direct", "confidence": 0.9, "reason": "简短原因"&#125;&#125;"""),
    ("human", "{query}"),
])

router_chain = router_prompt | llm.with_structured_output(RouteDecision)

# ── 完整的查询处理管线 ──
class QueryProcessor:
    """查询处理器：路由 + 改写 + 检索"""
    
    def __init__(self, router, rewriter, retriever, llm):
        self.router = router
        self.rewriter = rewriter
        self.retriever = retriever
        self.llm = llm
    
    def process(self, query: str, chat_history: str = "") -> dict:
        """处理用户查询"""
        
        # 1. 查询路由
        route = self.router.invoke({"query": query})
        
        if route.route == "direct":
            # 不走检索，LLM 直接回答
            return {"route": "direct", "answer": self.llm.invoke(query).content}
        
        if route.route == "database":
            # 走结构化查询（这里简化处理）
            return {"route": "database", "message": "请转接数据查询服务"}
        
        # 2. 查询改写（处理口语化和指代）
        rewritten = self.rewriter.invoke({
            "query": query,
            "chat_history": chat_history
        })
        
        # 3. 向量检索
        docs = self.retriever.similarity_search(rewritten, k=5)
        
        return {
            "route": "rag",
            "original_query": query,
            "rewritten_query": rewritten,
            "retrieved_docs": docs,
        }
```
:::

**路由决策速查表：**

| 用户问题 | 路由 | 原因 |
|:---|:---|:---|
| "公司年假几天" | `rag` | 需要查公司制度 |
| "订单 20240301 的状态" | `database` | 精确数据查询 |
| "Python 怎么写循环" | `direct` | 通用编程知识 |
| "帮我写一首诗" | `direct` | 创意任务 |
| "我们产品支持哪些格式" | `rag` | 产品文档 |
| "今天天气怎么样" | `direct` | 与知识库无关 |

> 💡 **务实建议**：如果你的 RAG 系统只服务于知识库问答（没有数据库查询需求），可以跳过路由，直接用"先检索 + 分数阈值判断"的策略（第 1 章讨论过的）。路由器适合有多种数据源的复合系统。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **查询改写** | 用 LLM 把口语化/指代问题改写为检索友好形式 |
| **HyDE** | 用 LLM 生成假设答案，用答案做检索（答案比问题更像文档） |
| **Multi-Query** | 把问题从多个角度改写，分别检索取并集，提高召回率 |
| **查询路由** | 先分析意图（知识库/数据库/直接回答），再选择检索策略 |
| **推荐组合** | 改写（必选）+ Multi-Query 或 HyDE（可选）+ 路由（复杂系统） |

---

## 5. 多路召回与精排：从召回到精准

上一章解决了"怎么理解用户意图"，这一章解决"怎么找到最相关的文档"。核心策略是**多路召回 + 精排**——先用多种方式各检索一批候选文档（追求"不遗漏"），再用精排模型筛选出最相关的 Top-K（追求"最精准"）。

### 5.1 单路召回的瓶颈与多路召回设计

只用向量检索（Dense Retrieval）有一个致命盲点：**精确匹配能力差**。

```
单路向量检索的盲点：

  场景一：精确术语/编号
  ════════════════════════════════════════════════
  用户问："合同编号 HT-2024-0892 的违约条款"
  
  向量检索：把"HT-2024-0892"编码成语义向量
    → 但"HT-2024-0892"没有语义！它是一个标识符
    → 检索出一堆含"合同""违约"的文档，但编号不对
  
  关键词检索：直接匹配"HT-2024-0892"字符串
    → 精准命中 ✅

  场景二：专业缩写
  ════════════════════════════════════════════════
  用户问："BGE-M3 支持哪些语言"
  
  向量检索：可能把"BGE-M3"理解为某种语义模糊的概念
    → 检索结果质量不稳定
  
  关键词检索：精确匹配"BGE-M3"
    → 直接命中包含这个词的文档 ✅

  结论：
    向量检索 → 擅长语义匹配（同义词、换一种说法）
    关键词检索 → 擅长精确匹配（编号、专有名词、缩写）
    → 两者互补，而不是替代关系
```

**多路召回的设计思想：**

```
多路召回架构：

  用户查询（经过改写）
      │
      ├──→ 🔢 Dense 检索（向量语义匹配） ──→ Top 20
      │
      ├──→ 🔤 Sparse 检索（关键词 BM25）  ──→ Top 20
      │
      └──→ 🏷️ 结构化过滤（元数据条件）   ──→ 过滤条件
      │
      ▼
  RRF / 加权融合 ──→ 合并去重 ──→ 30 条候选
      │
      ▼
  Reranker 精排 ──→ Top 5 最终结果
```

| 召回路 | 擅长什么 | 不擅长什么 |
|:---|:---|:---|
| **Dense（向量）** | 语义匹配、同义词、换说法 | 精确编号、专有名词 |
| **Sparse（BM25）** | 精确关键词、编号、缩写 | 同义词、换说法 |
| **结构化过滤** | 按部门/日期/类别精确限定 | 无法处理语义 |

> 💡 **核心认知**：多路召回不是"换一种检索方式"，而是"多种检索方式取并集"。Dense 漏掉的，Sparse 可能捞回来；反过来也一样。两者结合通常比任何单一方式好 10-15%。

### 5.2 混合检索实战：Dense + Sparse + 结构化过滤

用 Milvus 实现完整的混合检索——同时做向量检索和关键词检索，用 RRF 融合排序：

```python
from pymilvus import (
    Collection, AnnSearchRequest, RRFRanker
)
from pymilvus.model.hybrid import BGEM3EmbeddingFunction

# BGE-M3 同时生成 Dense 和 Sparse 向量
bge_m3 = BGEM3EmbeddingFunction(model_name="BAAI/bge-m3", device="cpu")

def hybrid_search(query: str, collection: Collection,
                   top_k: int = 5, filter_expr: str = "") -> list:
    """
    混合检索：Dense + Sparse + 结构化过滤
    """
    collection.load()
    
    # 1. 生成查询的 Dense + Sparse 向量
    query_emb = bge_m3.encode_queries([query])
    
    # 2. Dense 检索请求（语义匹配）
    dense_req = AnnSearchRequest(
        data=query_emb["dense"],
        anns_field="dense_embedding",
        param={"metric_type": "COSINE", "params": {"ef": 128&#125;&#125;,
        limit=20,
        expr=filter_expr,  # 结构化过滤条件
    )
    
    # 3. Sparse 检索请求（关键词匹配）
    sparse_req = AnnSearchRequest(
        data=query_emb["sparse"],
        anns_field="sparse_embedding",
        param={"metric_type": "IP", "params": {&#125;&#125;,
        limit=20,
        expr=filter_expr,
    )
    
    # 4. RRF 融合两路结果
    results = collection.hybrid_search(
        reqs=[dense_req, sparse_req],
        ranker=RRFRanker(k=60),  # RRF 融合参数
        limit=top_k * 4,         # 多取一些，后续给 Reranker 用
        output_fields=["content", "source", "heading", "department"],
    )
    
    return results[0]  # 返回融合后的结果

# ── 使用示例 ──

# 纯语义检索
results = hybrid_search("公司的年假制度", collection)

# 带结构化过滤
results = hybrid_search(
    "退货政策",
    collection,
    filter_expr='department == "客服" and effective_date >= "2024-01-01"'
)
```

**RRF（Reciprocal Rank Fusion）融合的原理：**

```
RRF 公式：score(d) = Σ 1 / (k + rank_i(d))

  k = 60（默认值）
  rank_i(d) = 文档 d 在第 i 路检索中的排名

  示例：
    文档 A：Dense 排名第 2，Sparse 排名第 5
    RRF(A) = 1/(60+2) + 1/(60+5) = 0.0161 + 0.0154 = 0.0315

    文档 B：Dense 排名第 10，Sparse 排名第 1
    RRF(B) = 1/(60+10) + 1/(60+1) = 0.0143 + 0.0164 = 0.0307

  → 文档 A 综合排名更靠前（两路都不错）
  → RRF 天然偏好"在多个路都有不错排名"的文档

  RRF 的优势：
    ✅ 不需要归一化各路分数（不同检索器的分数范围不同）
    ✅ 对异常值不敏感
    ✅ 调参简单（只有一个 k 值）
```

> 💡 **实测数据**：在中文企业知识库场景中，Dense + Sparse 混合检索比纯 Dense 检索的 Recall@10 提升约 **12-18%**，主要在精确术语和编号查询上获益。

### 5.3 Reranker 精排：Cross-Encoder 重排序

混合检索返回了 20-30 条候选文档，但其中可能有不少噪音。**Reranker 的作用是对候选文档做精细排序，只留下最相关的 Top-K**。

```
为什么需要 Reranker？

  Bi-Encoder（向量检索用的）：
    查询 和 文档 分别 编码为向量，然后计算余弦相似度
    → 快（毫秒级检索百万文档）
    → 但精度有限（查询和文档独立编码，无法交互）

  Cross-Encoder（Reranker 用的）：
    把 [查询, 文档] 拼起来 一起 送入模型
    → 模型能看到查询和文档的每个词之间的关系
    → 精度高得多（但速度慢，不能用来检索百万文档）

  所以最佳组合是：
    Bi-Encoder 粗筛  ──→  Cross-Encoder 精排
    （快，找到 20 条候选）   （慢但准，排出 Top 5）
```

```python
from sentence_transformers import CrossEncoder

class Reranker:
    """Reranker 精排器"""
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.model = CrossEncoder(model_name, max_length=512)
    
    def rerank(self, query: str, documents: list[dict],
               top_k: int = 5) -> list[dict]:
        """
        对候选文档重排序
        documents: [{"content": "...", "source": "...", ...}, ...]
        """
        if not documents:
            return []
        
        # 1. 构建 [query, document] 对
        pairs = [query, doc["content"](query, doc["content") for doc in documents]
        
        # 2. Cross-Encoder 打分
        scores = self.model.predict(pairs)
        
        # 3. 按分数排序
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # 4. 返回 Top-K，附带分数
        results = []
        for doc, score in scored_docs[:top_k]:
            doc["rerank_score"] = float(score)
            results.append(doc)
        
        return results

# ── 与混合检索组合使用 ──
reranker = Reranker()

def search_and_rerank(query: str, collection, top_k: int = 5):
    """完整的检索流程：混合检索 → Reranker 精排"""
    
    # 1. 混合检索获取候选（多取一些）
    candidates = hybrid_search(query, collection, top_k=20)
    
    # 2. 转换格式
    docs = [{"content": hit.entity.get("content"),
             "source": hit.entity.get("source"),
             "heading": hit.entity.get("heading")}
            for hit in candidates]
    
    # 3. Reranker 精排
    top_docs = reranker.rerank(query, docs, top_k=top_k)
    
    return top_docs
```

**Reranker 模型选型：**

| 模型 | 中文效果 | 速度 | 模型大小 | 推荐场景 |
|:---|:---|:---|:---|:---|
| **bge-reranker-v2-m3** | ⭐⭐⭐⭐⭐ | 中等 | 568M | **中文首选** |
| bge-reranker-large | ⭐⭐⭐⭐ | 较慢 | 1.3G | 极致精度 |
| ms-marco-MiniLM | ⭐⭐ | 快 | 66M | 英文/轻量 |
| cohere-rerank-v3 | ⭐⭐⭐⭐ | API | - | 不想自部署 |

> 💡 **性能数据**：Reranker 处理 20 条候选文档约 30-80ms（GPU）/ 200-500ms（CPU）。对于延迟敏感的场景，可以把候选数从 20 降到 10，精度损失很小但速度翻倍。

### 5.4 上下文压缩与窗口扩展：给 LLM 最优输入

经过精排拿到了 Top-5 文档，但直接丢给 LLM 还有两个问题：① 每个文档中可能只有一小段和问题相关，其他是噪音（浪费 Token）；② 某些 Chunk 的上下文被分块切断了（信息不完整）。

**上下文压缩——只保留与问题相关的段落：**

```python
def compress_context(query: str, documents: list[str], llm) -> list[str]:
    """
    用 LLM 压缩检索到的文档，只保留与问题相关的部分
    可以节省 40-60% 的 Token
    """
    compress_prompt = """从以下文档中提取与用户问题直接相关的信息。
只保留有用的部分，删除无关内容。如果整篇文档都无关，返回"无相关信息"。

用户问题：{query}

文档内容：
{document}

提取的相关信息："""
    
    compressed = []
    for doc in documents:
        result = llm.invoke(
            compress_prompt.format(query=query, document=doc)
        ).content.strip()
        
        if result != "无相关信息" and len(result) > 20:
            compressed.append(result)
    
    return compressed
```

**窗口扩展——检索命中的 Chunk 前后各取一块：**

```python
def expand_window(chunk_index: int, all_chunks: list[str],
                   window_size: int = 1) -> str:
    """
    把命中 Chunk 的前后各 window_size 个 Chunk 拼在一起
    提供更完整的上下文

    比如命中了 Chunk 5：
      window_size=1 → 返回 Chunk 4 + 5 + 6
      window_size=2 → 返回 Chunk 3 + 4 + 5 + 6 + 7
    """
    start = max(0, chunk_index - window_size)
    end = min(len(all_chunks), chunk_index + window_size + 1)
    
    return "\n\n".join(all_chunks[start:end])
```

```
上下文优化决策：

  检索到的文档太长？── 是 ──→ 上下文压缩（节省 Token）
      │
      否
      │
  Chunk 上下文不完整？── 是 ──→ 窗口扩展（补全上下文）
      │
      否
      │
  直接送给 LLM ✅

  也可以两者结合：
    先窗口扩展（补全）→ 再上下文压缩（精简）
    → 既完整又精炼
```

> 💡 **取舍建议**：上下文压缩多一次 LLM 调用（增加延迟和成本），只有当 Token 成本是瓶颈时才值得做。窗口扩展没有额外成本，**强烈推荐**在所有场景中使用。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **多路召回** | Dense（语义）+ Sparse（关键词）互补，取并集 |
| **RRF 融合** | 按排名倒数加权合并多路结果，不需要归一化 |
| **Reranker** | Cross-Encoder 精排，对候选文档精细打分 |
| **上下文压缩** | 用 LLM 去除检索文档中的无关段落，节省 Token |
| **窗口扩展** | 拼接命中 Chunk 的前后块，补全被切断的上下文 |
| **完整流程** | 混合检索 20 条 → RRF 融合 → Reranker 精排 Top 5 → 送给 LLM |

---

## 6. 生成优化：让 LLM 回答更准确

检索做得再好，最终质量还是取决于 LLM 怎么用检索到的内容生成回答。这一章聚焦**生成层的工程优化**——如何写出高质量的 RAG Prompt、如何让回答可溯源、如何让 LLM 学会说"不知道"。

### 6.1 RAG Prompt 工程最佳实践

RAG 的 Prompt 和普通对话 Prompt 有本质区别——你需要精确控制 LLM **如何使用检索到的上下文**。

**生产级 RAG Prompt 模板：**

```python
RAG_SYSTEM_PROMPT = """你是一个企业知识库助手。请严格根据【参考资料】回答用户问题。

## 回答规则

1. **基于事实**：只使用参考资料中的信息回答，不要编造或推测
2. **标注来源**：每个关键信息点后标注来源，格式为 [来源: 文件名]
3. **坦诚不知**：如果参考资料中没有相关信息，直接回答"根据现有资料，暂无相关信息"
4. **结构清晰**：使用分点或表格组织回答，避免大段文字
5. **简洁准确**：不要重复参考资料的原文，用自己的话总结核心信息

## 参考资料

{context}

## 注意事项

- 如果参考资料之间有矛盾，指出矛盾并说明各资料的出处
- 如果用户问题超出参考资料的范围，明确告知并建议用户咨询相关部门
- 不要使用"根据我所知"等暗示你有独立知识的表达"""

RAG_USER_PROMPT = """用户问题：{question}

请根据上述参考资料回答。"""
```

**Prompt 设计的五大关键原则：**

```
RAG Prompt 设计原则：

  1️⃣ 明确信息边界
  ─────────────────────────────────
  ❌ "回答用户问题"
  ✅ "只使用【参考资料】中的信息回答，不要使用你的训练知识"
  → 减少幻觉的核心手段

  2️⃣ 教会 LLM 说"不知道"
  ─────────────────────────────────
  ❌ 不提 → LLM 会编造答案
  ✅ "如果参考资料中没有相关信息，回答：根据现有资料暂无此信息"
  → 宁可不答，不可胡答

  3️⃣ 要求标注来源
  ─────────────────────────────────
  ❌ 直接输出答案
  ✅ "每个关键信息后标注 [来源: 文件名/章节]"
  → 让用户可以验证、建立信任

  4️⃣ 处理矛盾信息
  ─────────────────────────────────
  知识库中可能有新旧版本的文档
  ✅ "如果资料之间有矛盾，指出矛盾并标注各自的来源和日期"
  → 让用户自行判断

  5️⃣ 控制输出格式
  ─────────────────────────────────
  ✅ "使用分点列表组织回答" / "以表格形式对比"
  → 结构化输出更易阅读，也便于后续解析
```

**组装检索上下文的代码：**

```python
def build_context(documents: list[dict], max_tokens: int = 3000) -> str:
    """将检索到的文档组装为 Prompt 中的上下文"""
    context_parts = []
    total_chars = 0
    
    for i, doc in enumerate(documents, 1):
        # 格式化每个文档块
        source = doc.get("source", "未知来源")
        heading = doc.get("heading", "")
        content = doc["content"]
        
        # Token 预算控制（1 个中文字 ≈ 1.5 token）
        if total_chars + len(content) > max_tokens * 0.67:
            break
        
        header = f"【资料 {i}】来源: {source}"
        if heading:
            header += f" | 章节: {heading}"
        
        context_parts.append(f"{header}\n{content}")
        total_chars += len(content)
    
    return "\n\n---\n\n".join(context_parts)
```

> 💡 **实战经验**：Prompt 中"教 LLM 说不知道"和"要求标注来源"这两条规则，能显著降低幻觉率。实测从无这两条时的 ~25% 幻觉率降到 ~5%。

### 6.2 引用溯源：让每句回答都有据可查

企业级 RAG 的一个关键需求：**用户需要知道回答的依据是什么**。引用溯源不仅建立信任，还能帮助用户判断信息是否过时。

```python
from pydantic import BaseModel, Field

class Citation(BaseModel):
    """引用信息"""
    text: str = Field(description="引用的原文片段")
    source: str = Field(description="来源文件名")
    page: int = Field(default=0, description="页码")

class RAGResponse(BaseModel):
    """带引用的 RAG 回答"""
    answer: str = Field(description="回答内容，关键信息后用 [1][2] 标注引用编号")
    citations: list[Citation] = Field(description="引用列表")
    confidence: float = Field(description="回答置信度 0-1")
    has_sufficient_info: bool = Field(description="参考资料是否足够回答问题")

# ── 带引用的 RAG Prompt ──
CITATION_PROMPT = """你是一个知识库助手。请根据参考资料回答问题，并标注引用来源。

## 参考资料
{context}

## 回答要求
1. 在回答中用 [1][2] 等编号标注信息来源（对应参考资料编号）
2. 在 citations 中列出每个引用的原文片段和来源
3. 如果资料不足以回答，设置 has_sufficient_info 为 false
4. confidence 反映你对回答准确性的评估

返回 JSON 格式的 RAGResponse。"""

# 使用 structured output
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1")
citation_chain = llm.with_structured_output(RAGResponse)

# 示例输出：
# {
#   "answer": "公司年假规定如下：工作满1年享有5天年假 [1]，
#              满10年享有10天 [1]。申请需提前3个工作日 [2]。",
#   "citations": [
#     {"text": "工作满1年可享有5天年假，满10年10天", "source": "员工手册.pdf", "page": 15},
#     {"text": "年假申请须提前3个工作日提交", "source": "请假制度.docx", "page": 3}
#   ],
#   "confidence": 0.92,
#   "has_sufficient_info": true
# }
```

```
引用溯源的价值：

  对用户：可以点击来源查看原文 → 建立信任
  对运维：可以追踪哪些文档被引用最多 → 优化知识库
  对评测：可以自动检查引用是否准确 → 量化忠实度
```

> 💡 **简化替代方案**：如果不需要结构化引用，可以在 Prompt 里简单要求"回答末尾列出参考资料"，效果也不错，实现成本更低。

### 6.3 Self-RAG：LLM 自我判断是否需要检索

Self-RAG 是一种更高级的 RAG 模式：**让 LLM 自己决定是否需要检索、检索结果是否有用、自己的回答是否有足够依据**。

```
Self-RAG 的决策流程：

  用户问题
      │
      ▼
  LLM 判断：我需要外部知识吗？
      │
  ┌───┴───┐
  不需要   需要
  │       │
  │       ▼
  │   执行检索，获取候选文档
  │       │
  │       ▼
  │   LLM 判断：每条检索结果和问题相关吗？
  │       │
  │       ▼ 过滤掉不相关的
  │   LLM 生成回答
  │       │
  │       ▼
  │   LLM 自检：我的回答有事实依据吗？
  │       │
  │   ┌───┴───┐
  │   有依据   无依据
  │   │       │
  │   │       ▼
  │   │   重新检索或拒绝回答
  │   ▼
  ▼   ▼
  输出最终回答
```

```python
class SelfRAG:
    """Self-RAG：自适应检索与自我评估"""
    
    def __init__(self, llm, retriever):
        self.llm = llm
        self.retriever = retriever
    
    def answer(self, query: str) -> dict:
        """Self-RAG 完整流程"""
        
        # Step 1: 判断是否需要检索
        need_retrieval = self._need_retrieval(query)
        
        if not need_retrieval:
            response = self.llm.invoke(query).content
            return {"answer": response, "used_rag": False}
        
        # Step 2: 检索 + 过滤不相关的结果
        docs = self.retriever.similarity_search(query, k=5)
        relevant_docs = self._filter_relevant(query, docs)
        
        if not relevant_docs:
            return {
                "answer": "根据现有知识库，暂无与此问题直接相关的信息。",
                "used_rag": True,
                "docs_found": False,
            }
        
        # Step 3: 基于相关文档生成回答
        context = "\n\n".join([d.page_content for d in relevant_docs])
        answer = self._generate_with_context(query, context)
        
        # Step 4: 自检——回答是否有事实依据
        is_grounded = self._check_grounding(answer, context)
        
        if not is_grounded:
            answer += "\n\n⚠️ 注意：以上回答可能不完全基于现有资料，建议核实。"
        
        return {
            "answer": answer,
            "used_rag": True,
            "is_grounded": is_grounded,
            "sources": [d.metadata.get("source") for d in relevant_docs],
        }
    
    def _need_retrieval(self, query: str) -> bool:
        """判断是否需要检索"""
        result = self.llm.invoke(
            f"判断以下问题是否需要查询外部知识库才能回答。"
            f"如果是通用知识或闲聊，回答'否'。"
            f"如果涉及特定公司/产品/项目的信息，回答'是'。"
            f"\n问题: {query}\n只回答'是'或'否'："
        ).content.strip()
        return "是" in result
    
    def _filter_relevant(self, query, docs):
        """过滤不相关的检索结果"""
        return [d for d in docs if self._is_relevant(query, d)]
    
    def _is_relevant(self, query, doc) -> bool:
        """判断单个文档是否与查询相关"""
        result = self.llm.invoke(
            f"判断以下文档是否与用户问题相关。\n"
            f"问题: {query}\n文档: {doc.page_content[:300]}\n"
            f"只回答'相关'或'不相关'："
        ).content.strip()
        return "相关" in result
    
    def _check_grounding(self, answer, context) -> bool:
        """检查回答是否有事实依据"""
        result = self.llm.invoke(
            f"检查以下回答是否完全基于参考资料，没有编造信息。\n"
            f"参考资料: {context[:500]}\n回答: {answer}\n"
            f"只回答'是'（有依据）或'否'（有编造）："
        ).content.strip()
        return "是" in result
```

> 💡 **成本提示**：Self-RAG 每次回答会多 3-5 次 LLM 调用（判断 + 过滤 + 自检）。适合对准确性要求极高的场景（法律、医疗、金融）。普通场景用"先检索 + 分数阈值"就够了。

### 6.4 多轮对话中的 RAG：上下文管理策略

多轮对话是企业 RAG 的刚需——用户不会只问一个问题就走。但多轮对话带来一个棘手的问题：**每一轮都要带上历史上下文，Token 窗口很快就爆了**。

```
多轮对话 RAG 的三大挑战：

  挑战一：Token 窗口爆炸
  ════════════════════════════════════════════════
  第 1 轮：Prompt(500) + Context(2000) + 回答(800)  = 3300 Token
  第 2 轮：历史(3300) + Prompt + Context + 回答      = 6600 Token
  第 3 轮：历史(6600) + Prompt + Context + 回答      = 9900 Token
  ...
  第 10 轮：早就超出 GPT-4o 的 128K 窗口了
  → 而且大部分 Token 花在了旧对话上，成本飙升

  挑战二：何时重新检索
  ════════════════════════════════════════════════
  用户第 1 轮："公司年假制度是什么？" → 检索 ✅
  用户第 2 轮："那产假呢？"            → 需要重新检索！主题变了
  用户第 3 轮："多少天？"              → 不需要重新检索，沿用上一轮结果

  → 不是每一轮都需要检索，但也不能完全不检索

  挑战三：历史上下文干扰检索
  ════════════════════════════════════════════════
  如果把整个对话历史都拼进检索查询：
    "年假制度 + 产假 + 多少天 + 申请流程 + ..."
  → 检索请求太杂，反而什么都检索不准
```

**多轮对话 RAG 的核心架构：**

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class ConversationalRAG:
    """多轮对话 RAG：上下文管理 + 智能检索"""
    
    def __init__(self, llm, retriever, reranker=None,
                 max_history_turns: int = 5):
        self.llm = llm
        self.retriever = retriever
        self.reranker = reranker
        self.max_turns = max_history_turns
        self.history = []           # [(query, answer), ...]
        self.last_docs = []         # 上一轮检索到的文档
        self.history_summary = ""   # 压缩后的历史摘要
    
    def chat(self, query: str) -> dict:
        """处理一轮对话"""
        
        # 1. 指代消解：把"它""那个"替换成具体内容
        standalone_query = self._resolve_references(query)
        
        # 2. 判断是否需要重新检索
        need_search = self._should_retrieve(standalone_query)
        
        if need_search:
            # 3a. 重新检索
            docs = self.retriever.similarity_search(standalone_query, k=5)
            if self.reranker:
                docs = self.reranker.rerank(standalone_query, docs)
            self.last_docs = docs
        else:
            # 3b. 沿用上一轮的检索结果
            docs = self.last_docs
        
        # 4. 构建带历史的 Prompt
        context = "\n\n".join([d.page_content for d in docs[:3]])
        history_text = self._get_compressed_history()
        
        answer = self._generate(query, context, history_text)
        
        # 5. 更新历史
        self._update_history(query, answer)
        
        return {
            "answer": answer,
            "new_retrieval": need_search,
            "sources": [d.metadata.get("source") for d in docs[:3]],
        }
    
    def _resolve_references(self, query: str) -> str:
        """指代消解：把多轮中的'它''那个'替换为具体内容"""
        if not self.history:
            return query
        
        recent = self.history[-2:]  # 只看最近 2 轮
        history_str = "\n".join(
            [f"用户: {q}\nAI: {a[:100]}" for q, a in recent]
        )
        
        result = self.llm.invoke(
            f"根据对话历史，将最新问题改写为独立完整的问题。\n"
            f"对话历史:\n{history_str}\n"
            f"最新问题: {query}\n"
            f"改写后的问题（如果不需要改写就返回原文）:"
        ).content.strip()
        
        return result
    
    def _should_retrieve(self, query: str) -> bool:
        """判断是否需要重新检索（避免每轮都检索）"""
        if not self.last_docs:
            return True  # 第一轮必须检索
        
        # 用 LLM 判断当前问题是否能用已有文档回答
        docs_summary = "\n".join(
            [d.page_content[:100] for d in self.last_docs[:3]]
        )
        result = self.llm.invoke(
            f"判断以下问题是否能用已有资料回答。\n"
            f"已有资料摘要:\n{docs_summary}\n"
            f"新问题: {query}\n"
            f"回答'能'或'不能':"
        ).content.strip()
        
        return "不能" in result
    
    def _get_compressed_history(self) -> str:
        """获取压缩后的对话历史"""
        if not self.history:
            return ""
        
        # 最近 2 轮保留原文
        recent = self.history[-2:]
        recent_text = "\n".join(
            [f"用户: {q}\nAI: {a}" for q, a in recent]
        )
        
        # 更早的用摘要
        if self.history_summary:
            return f"[历史摘要] {self.history_summary}\n\n[近期对话]\n{recent_text}"
        
        return recent_text
    
    def _update_history(self, query: str, answer: str):
        """更新对话历史（含压缩）"""
        self.history.append((query, answer))
        
        # 超过阈值时压缩旧历史
        if len(self.history) > self.max_turns:
            old = self.history[:-2]  # 保留最近 2 轮不压缩
            old_text = "\n".join(
                [f"用户: {q}\nAI: {a[:80]}" for q, a in old]
            )
            self.history_summary = self.llm.invoke(
                f"将以下对话历史压缩为一段简短摘要（50字以内）：\n{old_text}"
            ).content.strip()
            self.history = self.history[-2:]  # 只保留最近 2 轮
```

**对话历史压缩策略对比：**

| 策略 | 原理 | Token 消耗 | 信息保留 | 推荐场景 |
|:---|:---|:---|:---|:---|
| **固定窗口** | 只保留最近 N 轮 | 低 | 旧信息丢失 | 简单问答、FAQ |
| **滑动摘要** | 旧对话压缩为摘要 | 中 | 大部分保留 | **通用推荐** |
| **全量保留** | 所有历史原文带入 | 高 | 完整 | 超长上下文模型 |
| **语义选择** | 只保留与当前相关的历史 | 中低 | 选择性保留 | 主题跳跃频繁 |

```
多轮对话 RAG 的完整流程：

  用户新消息
      │
      ▼
  指代消解（"那个" → 具体内容）
      │
      ▼
  是否需要重新检索？
      │
  ┌───┴───┐
  需要     不需要
  │       │
  ▼       │
  检索 + 精排  │
  │       │
  ▼       ▼
  合并：压缩历史 + 检索上下文 + 当前问题
      │
      ▼
  LLM 生成回答
      │
      ▼
  更新历史（超过阈值则压缩）
```

> 💡 **务实建议**：对于大多数企业场景，「固定窗口（最近 3-5 轮）+ 指代消解」就够了。滑动摘要适合深度咨询类场景（如法律、医疗问诊）。不要过度设计——先上线，再根据用户反馈迭代。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **RAG Prompt** | 明确信息边界 + 教会说不知道 + 要求标注来源 |
| **引用溯源** | 结构化输出引用编号和原文片段，让回答可验证 |
| **Self-RAG** | LLM 自主决定是否检索、过滤无关结果、自检依据 |
| **多轮对话** | 指代消解 + 智能检索判断 + 历史压缩，控制 Token |
| **取舍原则** | 简单场景用阈值 + 固定窗口，复杂场景用 Self-RAG + 滑动摘要 |

---

## 7. 端到端评测体系：量化 RAG 质量

前面六章把 RAG 的全链路都搭好了——解析、分块、检索、精排、生成。但一个关键问题始终悬而未决：**你怎么知道系统是好还是差、改了 Prompt 之后到底是变好了还是变差了？** 没有评测体系的 RAG 优化就是盲人摸象。这一章建立一套**可量化、可自动化、可持续运行**的评测体系。

### 7.1 RAG 评测的三个层次：检索 → 生成 → 端到端

RAG 评测不是一个指标就能搞定的。你需要分层评测——定位问题是出在检索还是生成，才能对症下药。

```
RAG 评测的三个层次：

  层次一：检索评测 ─── 找到"对的"文档了吗？
  ═══════════════════════════════════════════════
  评测对象：Retriever 返回的文档列表
  核心问题：相关文档是否被召回？排名是否靠前？
  
  关键指标：
    • Recall@K   → 相关文档有多少被检索到
    • MRR        → 第一个相关文档排在第几位
    • NDCG       → 综合考虑排名和相关性等级

  层次二：生成评测 ─── 回答"忠实"且"有用"吗？
  ═══════════════════════════════════════════════
  评测对象：LLM 的最终回答
  核心问题：回答是否基于检索结果？是否完整回答了问题？
  
  关键指标：
    • Faithfulness   → 回答是否忠于检索到的文档（不编造）
    • Relevancy      → 回答是否与用户问题相关
    • Correctness    → 回答是否正确

  层次三：端到端评测 ─── 用户满意吗？
  ═══════════════════════════════════════════════
  评测对象：整个 RAG 系统（从问题到回答）
  核心问题：真实用户使用的效果如何？
  
  关键指标：
    • Answer Accuracy  → 对比标准答案的准确率
    • User Satisfaction → 用户满意度评分
    • Latency          → 端到端响应时间
```

**三层评测的定位逻辑：**

```
当回答质量差时，怎么定位问题？

  回答不准确
      │
      ▼
  检查检索层：相关文档被检索到了吗？
      │
  ┌───┴───┐
  没检索到  检索到了
  │       │
  ▼       ▼
  检索问题    检查生成层：LLM 有没有正确使用文档？
  • 分块不对      │
  • 查询改写差  ┌───┴───┐
  • 向量模型弱  忠实    不忠实
              │       │
              ▼       ▼
          端到端问题   生成问题
          • 标准答案    • Prompt 需优化
            可能有误    • LLM 能力不足
```

**评测数据集的构建——这是最费时间但最重要的一步：**

```python
from dataclasses import dataclass, field

@dataclass
class EvalSample:
    """一条评测样本"""
    question: str                            # 用户问题
    ground_truth: str                        # 标准答案
    relevant_doc_ids: list[str] = field(     # 相关文档 ID 列表
        default_factory=list
    )
    category: str = ""                       # 问题类别（FAQ/制度/产品）
    difficulty: str = "medium"               # 难度：easy/medium/hard

class EvalDataset:
    """评测数据集管理器"""
    
    def __init__(self):
        self.samples: list[EvalSample] = []
    
    def add(self, question: str, ground_truth: str, 
            relevant_doc_ids: list[str] = None, **kwargs):
        self.samples.append(EvalSample(
            question=question,
            ground_truth=ground_truth,
            relevant_doc_ids=relevant_doc_ids or [],
            **kwargs,
        ))
    
    def save(self, path: str):
        """保存为 JSON"""
        import json
        data = [vars(s) for s in self.samples]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "EvalDataset":
        """从 JSON 加载"""
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ds = cls()
        ds.samples = [EvalSample(**d) for d in data]
        return ds

# ── 构建评测集 ──
dataset = EvalDataset()

dataset.add(
    question="公司年假制度是怎样的？",
    ground_truth="工作满1年享有5天年假，满10年享有10天。申请需提前3个工作日。",
    relevant_doc_ids=["doc_001", "doc_002"],
    category="制度",
    difficulty="easy",
)

dataset.add(
    question="合同编号 HT-2024-0892 的违约金条款是什么？",
    ground_truth="违约方应支付合同金额的 15% 作为违约金。",
    relevant_doc_ids=["doc_045"],
    category="合同",
    difficulty="hard",
)

dataset.save("eval_dataset.json")
```

```
构建评测数据集的原则：

  1️⃣ 覆盖所有问题类型
     FAQ（简单事实问答）     → 20%
     制度/流程类问题         → 30%
     精确查询（编号/数据）   → 20%
     需要跨文档综合的问题    → 20%
     知识库外问题（应拒绝）  → 10%

  2️⃣ 数量要求
     最低 50 条（能跑通流程）
     推荐 200 条（统计显著）
     理想 500+ 条（覆盖长尾）

  3️⃣ 标注要求
     每条都需要：标准答案 + 相关文档 ID
     → 这样才能同时评测检索和生成

  4️⃣ 数据来源
     • 真实用户日志（最有价值）
     • 业务专家人工编写
     • LLM 辅助生成 + 人工校验
```

> 💡 **核心认知**：评测数据集的质量决定了评测结论的可信度。花 2 天整理一份 200 条的高质量评测集，比花 2 周调参数有价值得多——因为没有评测集，你连\"改进\"还是\"退步\"都不知道。

### 7.2 检索质量评测：Recall、MRR、NDCG

检索评测回答一个根本问题：**相关的文档到底有没有被找到？**

```
三个核心检索指标：

  Recall@K（召回率）
  ════════════════════════════════════════════════
  定义：在 Top K 个检索结果中，实际相关的文档占所有相关文档的比例
  
  公式：Recall@K = |检索到的相关文档| / |所有相关文档|
  
  示例：
    相关文档有 3 个：[A, B, C]
    Top 5 检索结果：[A, X, B, Y, Z]
    Recall@5 = 2/3 = 66.7%（C 没被检索到）

  MRR（Mean Reciprocal Rank，平均倒数排名）
  ════════════════════════════════════════════════
  定义：第一个相关文档的排名的倒数，越靠前越好
  
  公式：RR = 1 / rank_of_first_relevant
  
  示例：
    查询 1：第一个相关在第 1 位 → RR = 1/1 = 1.0
    查询 2：第一个相关在第 3 位 → RR = 1/3 = 0.33
    查询 3：第一个相关在第 5 位 → RR = 1/5 = 0.2
    MRR = (1.0 + 0.33 + 0.2) / 3 = 0.51

  NDCG@K（归一化折损累计增益）
  ════════════════════════════════════════════════
  定义：不仅看"有没有相关文档"，还看"相关文档的排名是否靠前"
  
  直觉：排在第 1 位的相关文档比排在第 5 位的价值更大
  
  计算：
    DCG@K = Σ (rel_i / log2(i+1))   (对每个位置求和)
    NDCG@K = DCG@K / IDCG@K          (除以理想排列的 DCG)
  
  → NDCG = 1.0 表示完美排序（所有相关文档都在最前面）
```

```python
import numpy as np

class RetrievalEvaluator:
    """检索质量评测器"""
    
    def recall_at_k(self, retrieved_ids: list[str], 
                     relevant_ids: list[str], k: int = 5) -> float:
        """计算 Recall@K"""
        if not relevant_ids:
            return 0.0
        retrieved_set = set(retrieved_ids[:k])
        relevant_set = set(relevant_ids)
        return len(retrieved_set & relevant_set) / len(relevant_set)
    
    def mrr(self, retrieved_ids: list[str], 
            relevant_ids: list[str]) -> float:
        """计算 MRR（单个查询的 Reciprocal Rank）"""
        relevant_set = set(relevant_ids)
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant_set:
                return 1.0 / (i + 1)
        return 0.0  # 没找到任何相关文档
    
    def ndcg_at_k(self, retrieved_ids: list[str],
                   relevant_ids: list[str], k: int = 5) -> float:
        """计算 NDCG@K"""
        relevant_set = set(relevant_ids)
        
        # 计算 DCG
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_ids[:k]):
            rel = 1.0 if doc_id in relevant_set else 0.0
            dcg += rel / np.log2(i + 2)  # i+2 因为 log2(1)=0
        
        # 计算理想 DCG（所有相关文档排最前面）
        ideal_rels = sorted(
            [1.0 if doc_id in relevant_set else 0.0 
             for doc_id in retrieved_ids[:k]],
            reverse=True
        )
        idcg = sum(r / np.log2(i + 2) for i, r in enumerate(ideal_rels))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def evaluate_batch(self, eval_results: list[dict]) -> dict:
        """
        批量评测
        eval_results: [{"retrieved_ids": [...], "relevant_ids": [...]}, ...]
        """
        recalls = []
        mrrs = []
        ndcgs = []
        
        for result in eval_results:
            retrieved = result["retrieved_ids"]
            relevant = result["relevant_ids"]
            
            recalls.append(self.recall_at_k(retrieved, relevant, k=5))
            mrrs.append(self.mrr(retrieved, relevant))
            ndcgs.append(self.ndcg_at_k(retrieved, relevant, k=5))
        
        return {
            "Recall@5": round(np.mean(recalls), 4),
            "MRR": round(np.mean(mrrs), 4),
            "NDCG@5": round(np.mean(ndcgs), 4),
            "num_queries": len(eval_results),
        }

# ── 使用示例 ──
evaluator = RetrievalEvaluator()

# 单条评测
print(evaluator.recall_at_k(
    retrieved_ids=["d1", "d5", "d2", "d8", "d3"],
    relevant_ids=["d1", "d2", "d7"],
    k=5
))
# → 0.667（3 个相关文档检索到了 2 个）

# 批量评测
results = evaluator.evaluate_batch([
    {"retrieved_ids": ["d1", "d2", "d3"], "relevant_ids": ["d1", "d2"]},
    {"retrieved_ids": ["d5", "d1", "d4"], "relevant_ids": ["d1"]},
    {"retrieved_ids": ["d9", "d8", "d7"], "relevant_ids": ["d3"]},
])
print(results)
# → {"Recall@5": 0.833, "MRR": 0.833, "NDCG@5": 0.876, "num_queries": 3}
```

**检索指标怎么看、怎么改进：**

| 指标 | 达标线 | 优秀线 | 低于达标时怎么改 |
|:---|:---|:---|:---|
| **Recall@5** | ≥ 0.75 | ≥ 0.90 | 增加检索路数、降低分块大小、加 Multi-Query |
| **MRR** | ≥ 0.60 | ≥ 0.80 | 加 Reranker、优化 Embedding 模型 |
| **NDCG@5** | ≥ 0.65 | ≥ 0.85 | 改善分块质量 + Reranker + 元数据过滤 |

> 💡 **优先看 Recall@5**。Recall 低说明相关文档根本没被找到——这是检索层的"硬伤"。MRR 和 NDCG 更关注排序质量，Recall 解决了之后再优化这两个。

### 7.3 生成质量评测：忠实度、相关性、完整性

检索质量达标后，下一个瓶颈就在**生成层**——LLM 有没有正确使用检索到的文档？有没有编造信息？

```
三个核心生成指标：

  Faithfulness（忠实度）─── 回答是否忠于检索文档？
  ════════════════════════════════════════════════
  定义：回答中的每个信息点，是否都能在检索文档中找到依据
  
  满分：所有信息都有据可查
  扣分：每编造一个信息点就扣分
  
  示例：
    检索文档："年假 5 天，工龄满 10 年为 10 天"
    回答："年假 5 天，满 10 年 10 天，满 20 年 15 天"
                                      ↑ 编造！文档没说 20 年
    Faithfulness ≈ 0.67（3 个信息点，2 个有据）

  Answer Relevancy（回答相关性）─── 回答是否对题？
  ════════════════════════════════════════════════
  定义：回答是否直接回答了用户的问题（而不是答非所问）
  
  示例：
    问题："Python GIL 是什么？"
    回答："Python 的安装步骤是..."
    → Relevancy ≈ 0.1（完全不对题）

  Answer Correctness（答案正确性）─── 对比标准答案
  ════════════════════════════════════════════════
  定义：回答与标准答案的语义一致程度
  
  需要：人工标注的标准答案（Ground Truth）
  方式：LLM 判断 + 语义相似度综合评分
```

**用 LLM-as-Judge 实现自动评测：**

```python
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class FaithfulnessScore(BaseModel):
    """忠实度评分结果"""
    score: float = Field(description="忠实度评分 0-1")
    unfaithful_claims: list[str] = Field(
        description="不忠实的信息点列表"
    )
    reason: str = Field(description="评分理由")

class GenerationEvaluator:
    """生成质量评测器（LLM-as-Judge）"""
    
    def __init__(self, judge_model: str = "gpt-4o"):
        self.judge = ChatOpenAI(model=judge_model)
    
    def faithfulness(self, answer: str, context: str) -> dict:
        """评测忠实度：回答是否忠于检索文档"""
        prompt = f"""评估以下回答是否完全基于参考资料，没有编造信息。

参考资料：
{context}

回答：
{answer}

评分标准：
- 1.0：所有信息都能在参考资料中找到依据
- 0.5：部分信息有依据，部分是编造的
- 0.0：大部分信息是编造的

列出所有不忠实的信息点（如果有的话）。"""
        
        result = self.judge.with_structured_output(
            FaithfulnessScore
        ).invoke(prompt)
        
        return {
            "faithfulness": result.score,
            "unfaithful_claims": result.unfaithful_claims,
            "reason": result.reason,
        }
    
    def relevancy(self, question: str, answer: str) -> float:
        """评测回答相关性：回答是否直接回答了问题"""
        result = self.judge.invoke(
            f"评估以下回答是否直接回答了用户的问题。\n"
            f"问题: {question}\n回答: {answer}\n"
            f"只返回一个 0-1 的分数（1=完全相关，0=完全不相关）:"
        ).content.strip()
        
        try:
            return float(result)
        except ValueError:
            return 0.5
    
    def correctness(self, answer: str, ground_truth: str) -> float:
        """评测正确性：对比标准答案"""
        result = self.judge.invoke(
            f"对比以下回答和标准答案的语义一致程度。\n"
            f"标准答案: {ground_truth}\n"
            f"实际回答: {answer}\n"
            f"只返回一个 0-1 的分数（1=语义完全一致，0=完全不一致）:"
        ).content.strip()
        
        try:
            return float(result)
        except ValueError:
            return 0.5
    
    def evaluate_sample(self, question: str, answer: str,
                         context: str, ground_truth: str) -> dict:
        """评测单条样本的所有指标"""
        faith = self.faithfulness(answer, context)
        relev = self.relevancy(question, answer)
        correct = self.correctness(answer, ground_truth)
        
        return {
            "faithfulness": faith["faithfulness"],
            "relevancy": relev,
            "correctness": correct,
            "unfaithful_claims": faith["unfaithful_claims"],
        }

# ── 使用 ──
gen_eval = GenerationEvaluator(judge_model="gpt-4o")

result = gen_eval.evaluate_sample(
    question="公司年假几天？",
    answer="工作满1年享有5天年假，满10年享有10天年假。",
    context="根据公司制度，员工工作满1年可享有5天年假，满10年10天。",
    ground_truth="工作满1年5天，满10年10天。",
)
print(result)
# → {"faithfulness": 1.0, "relevancy": 0.95, "correctness": 0.95, ...}
```

**生成指标怎么看、怎么改进：**

| 指标 | 达标线 | 优秀线 | 低于达标时怎么改 |
|:---|:---|:---|:---|
| **Faithfulness** | ≥ 0.85 | ≥ 0.95 | 加强 Prompt 约束、加 Self-RAG 自检 |
| **Relevancy** | ≥ 0.80 | ≥ 0.90 | 优化 Prompt 格式要求、改善检索相关性 |
| **Correctness** | ≥ 0.70 | ≥ 0.85 | 提升检索召回 + Prompt + 模型能力 |

```
生成评测的成本和频率：

  每次评测 = N 条样本 × 3 个指标 × 1 次 LLM 调用
  
  200 条样本 × 3 = 600 次 GPT-4o 调用
  ≈ $3-5 / 每次完整评测

  推荐频率：
    • 开发期：每次改动后跑一次
    • 上线后：每周跑一次，或每次知识库更新后跑
    • 紧急排查：随时跑
```

> 💡 **成本提示**：用 GPT-4o 做 Judge 效果最好但也最贵。如果评测频率高，可以用 DeepSeek-chat 做日常评测（准确率约为 GPT-4o 的 85-90%），每周用 GPT-4o 跑一次基线对比。

### 7.4 RAGAS 框架实战：一键跑通 RAG 评测

手动实现评测器虽然灵活，但 **RAGAS** 已经把上述所有指标都封装好了——并且做了大量的 Prompt 优化，比自己写的 Judge 更稳定。

```
RAGAS 是什么？

  R.A.G.A.S = Retrieval Augmented Generation Assessment
  
  核心价值：
    ✅ 开箱即用的 RAG 评测指标
    ✅ 不需要标准答案也能评测（无参考评测）
    ✅ 内置 LLM-as-Judge Prompt（经过大量调优）
    ✅ 支持批量评测 + 结果分析
  
  内置指标：
    检索层：context_precision, context_recall
    生成层：faithfulness, answer_relevancy
    端到端：answer_correctness, answer_similarity
```

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
)
from datasets import Dataset

# ── 1. 准备评测数据 ──
# RAGAS 需要 4 个字段：question, answer, contexts, ground_truth
eval_data = {
    "question": [
        "公司年假制度是怎样的？",
        "合同编号 HT-2024-0892 的违约条款？",
        "Python GIL 怎么绕过？",
    ],
    "answer": [
        "工作满1年享有5天年假，满10年享有10天。申请需提前3个工作日。",
        "违约方应支付合同金额的 15% 作为违约金。",
        "可以使用多进程(multiprocessing)替代多线程来绕过 GIL。",
    ],
    "contexts": [
        ["员工工作满1年可享有5天年假，满10年10天。请假需提前3个工作日申请。"],
        ["合同 HT-2024-0892 违约条款：违约方应支付合同金额15%的违约金。"],
        ["GIL 限制了多线程并行。可以用 multiprocessing 模块创建多进程。"],
    ],
    "ground_truth": [
        "工作满1年5天年假，满10年10天，需提前3个工作日申请。",
        "违约方应支付合同金额的 15% 作为违约金。",
        "使用 multiprocessing 多进程、C 扩展释放 GIL、或使用 PyPy。",
    ],
}

dataset = Dataset.from_dict(eval_data)

# ── 2. 运行评测 ──
results = evaluate(
    dataset=dataset,
    metrics=[
        faithfulness,          # 忠实度
        answer_relevancy,      # 回答相关性
        context_precision,     # 检索精确度
        context_recall,        # 检索召回率
        answer_correctness,    # 答案正确性
    ],
)

# ── 3. 查看结果 ──
print(results)
# {
#   "faithfulness": 0.95,
#   "answer_relevancy": 0.91,
#   "context_precision": 0.88,
#   "context_recall": 0.92,
#   "answer_correctness": 0.87,
# }

# 转为 DataFrame 查看每条样本的详情
df = results.to_pandas()
print(df["question", "faithfulness", "answer_correctness"]("question", "faithfulness", "answer_correctness"))
```

**把 RAGAS 集成到你的 RAG 系统中：**

```python
class RAGEvaluator:
    """RAGAS 评测集成器"""
    
    def __init__(self, rag_system):
        self.rag = rag_system  # 你的 RAG 系统实例
    
    def run_eval(self, eval_dataset: list[dict]) -> dict:
        """
        对评测集运行完整评测
        eval_dataset: [{"question": "...", "ground_truth": "..."}, ...]
        """
        questions = []
        answers = []
        contexts_list = []
        ground_truths = []
        
        for sample in eval_dataset:
            q = sample["question"]
            
            # 调用你的 RAG 系统获取回答和检索上下文
            result = self.rag.query(q)
            
            questions.append(q)
            answers.append(result["answer"])
            contexts_list.append(
                [doc["content"] for doc in result["retrieved_docs"]]
            )
            ground_truths.append(sample["ground_truth"])
        
        # 构建 RAGAS Dataset
        dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts_list,
            "ground_truth": ground_truths,
        })
        
        # 运行评测
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness, answer_relevancy,
            context_recall, answer_correctness,
        )
        
        results = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy, 
                     context_recall, answer_correctness],
        )
        
        return results

# 使用
# evaluator = RAGEvaluator(my_rag_system)
# results = evaluator.run_eval(eval_samples)
```

```
RAGAS 各指标的含义速查：

  指标                    含义                     是否需要标准答案
  ──────────────────────────────────────────────────────────
  faithfulness           回答忠于检索文档吗           不需要 ✅
  answer_relevancy       回答和问题相关吗             不需要 ✅
  context_precision      检索结果里有用的排前面吗      需要
  context_recall         相关文档都检索到了吗          需要
  answer_correctness     回答和标准答案一致吗          需要
  answer_similarity      回答与标准答案语义相似度      需要
  ──────────────────────────────────────────────────────────
  
  → faithfulness 和 answer_relevancy 不需要标准答案
  → 没有标准答案时也能做基本的质量评测！
```

> 💡 **务实建议**：如果你没时间标注标准答案，先只用 `faithfulness` + `answer_relevancy` 两个无参考指标跑。它们就能发现 80% 的问题（幻觉和答非所问）。等有资源了再补标准答案、加 `correctness`。

### 7.5 构建持续评测流水线

评测不是一次性的——RAG 系统的知识库在更新、Prompt 在调整、用户需求在变化。你需要一条**持续运行的评测流水线**，自动追踪质量趋势、及时发现倒退。

```
持续评测流水线架构：

  ┌─────────────────────────────────────────────┐
  │              定时触发（每日/每周）             │
  │                    或                        │
  │         事件触发（知识库更新/Prompt 修改）     │
  └────────────────────┬────────────────────────┘
                       │
                       ▼
  ┌─ 评测流水线 ────────────────────────────────┐
  │  ① 加载评测数据集（200+ 条）                 │
  │  ② 对每条样本调用 RAG 系统获取回答            │
  │  ③ 用 RAGAS 计算所有指标                     │
  │  ④ 存储结果（带时间戳和版本标签）             │
  │  ⑤ 对比历史数据，检测是否倒退                │
  │  ⑥ 低于阈值 → 发告警                        │
  └─────────────────────────────────────────────┘
                       │
                       ▼
  ┌─ 结果看板 ─────────────────────────────────┐
  │  📈 指标趋势图（按天/按版本）                │
  │  📊 分类分析（哪类问题变差了）               │
  │  🔴 告警记录                                │
  └─────────────────────────────────────────────┘
```

```python
import json
from datetime import datetime
from pathlib import Path

class EvalPipeline:
    """持续评测流水线"""
    
    def __init__(self, rag_system, eval_dataset_path: str,
                 results_dir: str = "./eval_results"):
        self.rag = rag_system
        self.dataset = self._load_dataset(eval_dataset_path)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # 告警阈值
        self.thresholds = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.80,
            "context_recall": 0.75,
            "answer_correctness": 0.70,
        }
    
    def run(self, version_tag: str = "") -> dict:
        """运行一次完整评测"""
        timestamp = datetime.now().isoformat()
        tag = version_tag or timestamp[:10]
        
        print(f"🚀 开始评测 [{tag}]，共 {len(self.dataset)} 条样本")
        
        # 1. 对每条样本获取 RAG 回答
        eval_records = []
        for i, sample in enumerate(self.dataset):
            result = self.rag.query(sample["question"])
            eval_records.append({
                "question": sample["question"],
                "answer": result["answer"],
                "contexts": [d["content"] for d in result["retrieved_docs"]],
                "ground_truth": sample["ground_truth"],
            })
            if (i + 1) % 20 == 0:
                print(f"  进度: {i+1}/{len(self.dataset)}")
        
        # 2. 运行 RAGAS 评测
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness, answer_relevancy,
            context_recall, answer_correctness,
        )
        from datasets import Dataset
        
        dataset = Dataset.from_dict({
            k: [r[k] for r in eval_records]
            for k in ["question", "answer", "contexts", "ground_truth"]
        })
        
        results = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy,
                     context_recall, answer_correctness],
        )
        
        # 3. 存储结果
        report = {
            "timestamp": timestamp,
            "version": tag,
            "num_samples": len(self.dataset),
            "metrics": dict(results),
        }
        
        result_file = self.results_dir / f"eval_{tag}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 4. 检查告警
        alerts = self._check_alerts(dict(results))
        if alerts:
            report["alerts"] = alerts
            print(f"🔴 告警: {alerts}")
        else:
            print(f"✅ 所有指标达标")
        
        # 5. 对比上次结果
        diff = self._compare_with_last(dict(results))
        if diff:
            report["diff_from_last"] = diff
            print(f"📊 变化: {diff}")
        
        print(f"\n📋 评测结果:")
        for k, v in dict(results).items():
            print(f"   {k}: {v:.4f}")
        
        return report
    
    def _check_alerts(self, metrics: dict) -> list[str]:
        """检查是否有指标低于阈值"""
        alerts = []
        for metric, threshold in self.thresholds.items():
            if metric in metrics and metrics[metric] < threshold:
                alerts.append(
                    f"{metric}={metrics[metric]:.3f} < {threshold}"
                )
        return alerts
    
    def _compare_with_last(self, current: dict) -> dict:
        """与上次评测结果对比"""
        result_files = sorted(self.results_dir.glob("eval_*.json"))
        if len(result_files) < 2:
            return {}
        
        with open(result_files[-2], "r") as f:
            last = json.load(f)["metrics"]
        
        diff = {}
        for k in current:
            if k in last:
                change = current[k] - last[k]
                if abs(change) > 0.01:  # 忽略微小变化
                    diff[k] = f"{'+' if change > 0 else ''}{change:.4f}"
        
        return diff
```

**评测驱动优化的闭环流程：**

```
评测驱动优化闭环：

  ① 跑评测 → 得到基线指标
      │
      ▼
  ② 分析薄弱项
     • Recall 低 → 检索问题（分块/查询改写/Embedding）
     • Faithfulness 低 → 生成问题（Prompt/Self-RAG）
     • 某类问题分数特别低 → 针对性优化
      │
      ▼
  ③ 做改进（改分块/换模型/优化 Prompt）
      │
      ▼
  ④ 重新跑评测
      │
      ▼
  ⑤ 对比改进前后的指标
     • 变好 → 合并上线 ✅
     • 没变化 → 方向不对，换策略
     • 变差 → 回滚 ❌
      │
      ▼
  ⑥ 回到 ①，持续迭代
```

| 优化目标 | 优先改什么 | 期望提升 |
|:---|:---|:---|
| Recall@5 < 0.75 | 加 Multi-Query / 混合检索 | +10-20% |
| Faithfulness < 0.85 | 强化 Prompt 约束 / Self-RAG | +10-15% |
| Correctness < 0.70 | 先查 Recall（地基问题） | 取决于根因 |
| 某类问题集体差 | 针对该类文档优化分块策略 | 个案优化 |

> 💡 **核心认知**：评测不是目的，**评测驱动的持续优化**才是。建立「改动 → 评测 → 对比 → 决策」的闭环，让每一次改动都有数据支撑，这才是企业级 RAG 的工程化精髓。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **三层评测** | 检索层（Recall/MRR）→ 生成层（Faithfulness）→ 端到端 |
| **评测数据集** | 200+ 条带标准答案的样本，覆盖所有问题类型 |
| **RAGAS** | 开箱即用的 RAG 评测框架，支持有参考和无参考评测 |
| **持续评测** | 定时/事件触发的自动化流水线 + 告警 + 趋势追踪 |
| **闭环优化** | 改动 → 评测 → 对比 → 决策，数据驱动每次改进 |

---

## 8. 生产部署与运维：让 RAG 稳定运行

前面 7 章我们打通了 RAG 的全链路——从文档解析到评测闭环。但技术验证通过，离真正上生产还差最后一座大山：**运维**。一个日均承接 1 万次查询的 RAG 系统，如果平均响应 8 秒、知识库一周没更新、出了问题全靠猜——再高的检索精度也留不住用户。

这一章聚焦五个生产必修课：性能调优、知识库增量更新、全链路可观测性、成本控制，以及故障排查。

### 8.1 性能优化三板斧：缓存、异步、批处理

一个未经优化的 RAG 问答请求，耗时分布通常长这样：

```
一次 RAG 请求的耗时瀑布（未优化）：

  查询改写（LLM）      ██████████░░░░░░░░░░░  800ms
  Embedding            ███░░░░░░░░░░░░░░░░░░  150ms
  向量检索             ████░░░░░░░░░░░░░░░░░  200ms
  Reranker             ██████░░░░░░░░░░░░░░░  400ms
  LLM 生成             ████████████████████░  2500ms
  ────────────────────────────────────────────────
  总计                                         ~4 秒

  其中 LLM 调用占 80%+，是最大瓶颈
```

**第一板斧：语义缓存——相似问题不重复算**

大量用户问的是同一类问题，只是换了措辞。语义缓存的思路：把新查询的 Embedding 和缓存里的历史查询做相似度匹配，超过阈值就直接返回缓存结果。

```python
import hashlib
import json
import time
import numpy as np
from dataclasses import dataclass

@dataclass
class CacheEntry:
    """缓存条目"""
    query: str              # 原始查询
    query_embedding: list   # 查询向量
    answer: str             # 缓存的回答
    sources: list           # 来源文档
    created_at: float       # 创建时间
    hit_count: int = 0      # 命中次数

class SemanticCache:
    """语义缓存：相似问题直接返回缓存结果"""
    
    def __init__(self, embedding_model, similarity_threshold: float = 0.95,
                 max_size: int = 10000, ttl_seconds: int = 86400):
        self.embedding_model = embedding_model
        self.threshold = similarity_threshold
        self.max_size = max_size
        self.ttl = ttl_seconds  # 缓存过期时间（默认 24 小时）
        self.cache: dict[str, CacheEntry] = {}
    
    def get(self, query: str) -> dict | None:
        """查找语义相似的缓存"""
        query_emb = self.embedding_model.encode(query)
        
        best_match = None
        best_score = 0.0
        
        now = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            # 检查过期
            if now - entry.created_at > self.ttl:
                expired_keys.append(key)
                continue
            
            # 余弦相似度
            score = self._cosine_similarity(query_emb, entry.query_embedding)
            if score > best_score:
                best_score = score
                best_match = entry
        
        # 清理过期缓存
        for key in expired_keys:
            del self.cache[key]
        
        # 超过阈值则命中
        if best_match and best_score >= self.threshold:
            best_match.hit_count += 1
            return {
                "answer": best_match.answer,
                "sources": best_match.sources,
                "cache_hit": True,
                "similarity": best_score,
            }
        
        return None  # 未命中
    
    def put(self, query: str, answer: str, sources: list):
        """写入缓存"""
        # 容量淘汰：优先删命中次数最低的
        if len(self.cache) >= self.max_size:
            lfu_key = min(self.cache, key=lambda k: self.cache[k].hit_count)
            del self.cache[lfu_key]
        
        query_emb = self.embedding_model.encode(query)
        cache_key = hashlib.md5(query.encode()).hexdigest()
        
        self.cache[cache_key] = CacheEntry(
            query=query,
            query_embedding=query_emb.tolist(),
            answer=answer,
            sources=sources,
            created_at=time.time(),
        )
    
    def _cosine_similarity(self, a, b) -> float:
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

```
语义缓存的关键参数调优：

  参数                推荐值        说明
  ─────────────────────────────────────────────────────
  similarity_threshold  0.95       太低会返回不相关的缓存
                                   太高则命中率过低
  ttl_seconds          86400       知识库更新频率高就缩短
  max_size             10000       根据内存容量调整
  
  生产经验：
  • 阈值 0.95 通常能拦住 30-50% 的重复查询
  • 阈值 0.90 命中率更高但有误命中风险
  • 建议先 0.95 跑一周，根据日志微调
```

**第二板斧：异步化——不要让用户干等**

查询改写和 Embedding 可以并行；检索多个来源可以并发；LLM 生成用流式输出让用户边看边等：

```python
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

async def async_rag_query(query: str, retriever, reranker, llm):
    """异步 RAG 查询：并行化 + 流式输出"""
    
    # ── 阶段 1：查询改写 + Embedding 并行 ──
    rewrite_task = asyncio.create_task(rewrite_query(query, llm))
    embedding_task = asyncio.create_task(embed_query(query))
    
    rewritten, query_emb = await asyncio.gather(
        rewrite_task, embedding_task
    )
    
    # ── 阶段 2：多路召回并发 ──
    dense_task = asyncio.create_task(
        retriever.dense_search(query_emb, top_k=20)
    )
    sparse_task = asyncio.create_task(
        retriever.sparse_search(rewritten, top_k=20)
    )
    
    dense_results, sparse_results = await asyncio.gather(
        dense_task, sparse_task
    )
    
    # ── 阶段 3：融合 + 精排 ──
    candidates = rrf_fusion(dense_results, sparse_results)
    top_docs = reranker.rerank(rewritten, candidates, top_k=5)
    
    # ── 阶段 4：流式生成 ──
    context = "\n\n".join(d["content"] for d in top_docs)
    
    async for chunk in llm.astream(
        f"根据以下资料回答问题：\n{context}\n\n问题：{rewritten}"
    ):
        yield chunk  # 流式返回给前端
```

```
异步化前后的耗时对比：

  同步模式（串行）：
  改写 → Embed → Dense → Sparse → 融合 → 精排 → 生成
  800  + 150  + 200  + 200   + 50  + 400 + 2500 = 4300ms

  异步模式（并行 + 流式）：
  [改写 ┬ Embed]  → [Dense ┬ Sparse] → 融合 → 精排 → 生成(流式)
   800ms(取大)      200ms(取大)         50    400    首字 200ms
  ════════════════════════════════════════════════════════════
  首字延迟: ~1650ms（体感提升 60%）    总延迟: ~4000ms
  
  关键收益：用户在 1.6 秒后就看到第一个字，不再干等
```

**第三板斧：批处理——离线任务别抢在线资源**

文档入库（解析 + 分块 + Embedding + 写向量库）是典型的离线批量任务，不要和在线查询抢资源：

```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

class BatchProcessor:
    """批量文档处理器"""
    
    def __init__(self, embedding_model, vector_store,
                 batch_size: int = 32, max_workers: int = 4):
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.batch_size = batch_size
        self.max_workers = max_workers
    
    def process_documents(self, documents: list[dict]) -> dict:
        """批量处理文档：分块 → 批量 Embedding → 批量入库"""
        stats = {"total": len(documents), "success": 0, "failed": 0}
        
        all_chunks = []
        
        # 1. 并行分块
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            chunk_results = list(pool.map(self._chunk_document, documents))
        
        for chunks in chunk_results:
            all_chunks.extend(chunks)
        
        print(f"📦 共 {len(all_chunks)} 个 Chunk，开始批量 Embedding...")
        
        # 2. 批量 Embedding（GPU 批处理最高效）
        for i in range(0, len(all_chunks), self.batch_size):
            batch = all_chunks[i:i + self.batch_size]
            texts = [c["content"] for c in batch]
            
            embeddings = self.embedding_model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
            )
            
            # 3. 批量写入向量库
            self.vector_store.insert(
                vectors=embeddings.tolist(),
                documents=batch,
            )
            
            stats["success"] += len(batch)
            print(f"  ✅ {stats['success']}/{len(all_chunks)}")
        
        return stats
```

> 💡 **性能优化的优先级**：语义缓存的投入产出比最高（改动小、收益大），建议第一个上；异步化需要改接口层但体感提升明显；批处理是基础设施，文档量大时必须有。

### 8.2 知识库的持续更新：增量索引与版本管理

企业知识库不是一次性导入就完事的。制度文件会修订、产品文档会更新、FAQ 会新增——如果系统回答的还是三个月前的旧版内容，用户很快就会失去信任。

```
知识库更新的三种模式：

  全量重建              增量更新              实时同步
  ═══════════          ═══════════          ═══════════
  删除全部旧数据        只处理变更的文档        文件变更立即触发
  重新跑完整流水线      对比 → 增/删/改        WebHook / 文件监听
  
  适用：初始化、             适用：日常维护          适用：Wiki/CMS
       重大结构变更          （推荐默认方案）        实时性要求高
  
  耗时：小时级              耗时：分钟级            耗时：秒级
  风险：停服维护              风险：低               风险：中（需幂等）
```

**增量更新的核心：变更检测**

```python
import hashlib
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class DocumentRecord:
    """文档索引记录"""
    file_path: str
    content_hash: str       # 文件内容的 MD5
    chunk_ids: list[str]    # 该文档对应的所有 Chunk ID
    indexed_at: str         # 上次索引时间
    file_size: int          # 文件大小

class IncrementalIndexer:
    """增量索引管理器"""
    
    def __init__(self, vector_store, doc_parser, chunker,
                 index_path: str = "./index_registry.json"):
        self.vector_store = vector_store
        self.parser = doc_parser
        self.chunker = chunker
        self.index_path = Path(index_path)
        self.registry = self._load_registry()
    
    def sync(self, source_dir: str) -> dict:
        """同步知识库目录：检测变更 → 增删改"""
        stats = {"added": 0, "updated": 0, "deleted": 0, "unchanged": 0}
        
        source = Path(source_dir)
        current_files = {
            str(f): self._file_hash(f)
            for f in source.rglob("*")
            if f.suffix.lower() in {".pdf", ".docx", ".md", ".html", ".txt"}
        }
        
        # 1. 检测新增和修改
        for file_path, file_hash in current_files.items():
            if file_path not in self.registry:
                # 新文件 → 解析 + 入库
                self._index_document(file_path, file_hash)
                stats["added"] += 1
            elif self.registry[file_path].content_hash != file_hash:
                # 文件变更 → 删旧 + 重新入库
                self._remove_document(file_path)
                self._index_document(file_path, file_hash)
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1
        
        # 2. 检测删除
        deleted = set(self.registry.keys()) - set(current_files.keys())
        for file_path in deleted:
            self._remove_document(file_path)
            stats["deleted"] += 1
        
        # 3. 持久化索引注册表
        self._save_registry()
        
        print(f"📊 同步完成: +{stats['added']} ~{stats['updated']} "
              f"-{stats['deleted']} ={stats['unchanged']}")
        return stats
    
    def _index_document(self, file_path: str, file_hash: str):
        """索引单个文档"""
        # 解析 → 分块 → Embedding → 入库
        elements = self.parser.parse(file_path)
        chunks = self.chunker.chunk(elements)
        chunk_ids = self.vector_store.add(chunks)
        
        self.registry[file_path] = DocumentRecord(
            file_path=file_path,
            content_hash=file_hash,
            chunk_ids=chunk_ids,
            indexed_at=datetime.now().isoformat(),
            file_size=Path(file_path).stat().st_size,
        )
    
    def _remove_document(self, file_path: str):
        """删除文档的所有 Chunk"""
        if file_path in self.registry:
            chunk_ids = self.registry[file_path].chunk_ids
            self.vector_store.delete(ids=chunk_ids)
            del self.registry[file_path]
    
    def _file_hash(self, path: Path) -> str:
        """计算文件内容哈希"""
        return hashlib.md5(path.read_bytes()).hexdigest()
    
    def _load_registry(self) -> dict:
        if self.index_path.exists():
            data = json.loads(self.index_path.read_text())
            return {k: DocumentRecord(**v) for k, v in data.items()}
        return {}
    
    def _save_registry(self):
        data = {k: asdict(v) for k, v in self.registry.items()}
        self.index_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2)
        )
```

**版本管理：让每一次变更可追溯**

```
知识库版本管理策略：

  ┌─────────────────────────────────────────────────┐
  │  版本号     时间         变更摘要        操作者   │
  ├─────────────────────────────────────────────────┤
  │  v2.3.1    04-03 10:00  更新年假制度     张三    │
  │  v2.3.0    04-01 14:00  新增产品手册     系统    │
  │  v2.2.0    03-28 09:00  重建索引(换模型) 李四    │
  └─────────────────────────────────────────────────┘
  
  每个版本记录：
  • 变更了哪些文件
  • 影响了哪些 Chunk（新增/删除/修改的 ID）
  • 触发方式（手动/定时/WebHook）
  
  → 出了问题可以快速回滚到上一个稳定版本
```

| 更新场景 | 推荐策略 | 频率 |
|:---|:---|:---|
| 制度文件修订 | 增量更新 + 版本记录 | 事件触发 |
| 日常 FAQ 新增 | 增量更新 | 每日定时 |
| Embedding 模型升级 | 全量重建 | 季度一次 |
| 紧急错误修正 | 单文档热更新 | 即时 |

> 💡 **实战经验**：增量更新一定要做**幂等设计**——同一个文件多次触发更新，结果必须一致。否则在 WebHook 重试、定时任务重叠等场景下，会产生重复 Chunk，严重污染检索质量。
### 8.3 监控与可观测性：追踪每一次检索和生成

RAG 系统上线后最怕的不是「出了问题」，而是「出了问题但不知道」。用户说「回答不准」，你需要能立刻查到：当时检索返回了哪些文档？Reranker 排序对不对？Prompt 里塞了什么内容？LLM 为什么生成了那个答案？

```
RAG 可观测性的三个层次：

  Layer 1：请求级 Trace（每次查询的全链路追踪）
  ═══════════════════════════════════════════════
  查询 → 改写结果 → 检索返回的文档 → Reranker 排序
  → Prompt 全文 → LLM 输入/输出 → 延迟 → Token 消耗
  
  → 用于排查单个 Bad Case

  Layer 2：系统级 Metrics（聚合指标 + 趋势）
  ═══════════════════════════════════════════════
  QPS / 平均延迟 / P99 延迟 / 缓存命中率 /
  检索平均返回数 / Token 消耗趋势 / 错误率
  
  → 用于监控系统健康度

  Layer 3：业务级 Analytics（用户行为分析）
  ═══════════════════════════════════════════════
  高频问题 TOP 20 / 用户反馈（👍👎）/ 
  知识盲区（检索召回为空的查询）/ 问题类型分布
  
  → 用于驱动知识库和系统优化
```

**实现请求级 Trace：**

```python
import uuid
import time
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path

@dataclass
class RAGTrace:
    """一次 RAG 请求的全链路追踪"""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    
    # 输入
    original_query: str = ""
    rewritten_query: str = ""
    
    # 检索
    retrieved_docs: list = field(default_factory=list)   # 召回的文档
    reranked_docs: list = field(default_factory=list)     # 精排后的文档
    retrieval_latency_ms: float = 0
    
    # 生成
    prompt_template: str = ""
    context_length: int = 0     # 上下文 Token 数
    answer: str = ""
    generation_latency_ms: float = 0
    
    # 资源
    total_latency_ms: float = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit: bool = False
    
    # 反馈
    user_feedback: str = ""     # "positive" / "negative" / ""
    error: str = ""

class RAGObserver:
    """RAG 可观测性管理器"""
    
    def __init__(self, log_dir: str = "./rag_traces"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "errors": 0,
            "total_latency_ms": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
        }
    
    def record(self, trace: RAGTrace):
        """记录一次请求的 Trace"""
        self.metrics["total_queries"] += 1
        self.metrics["total_latency_ms"] += trace.total_latency_ms
        self.metrics["total_input_tokens"] += trace.input_tokens
        self.metrics["total_output_tokens"] += trace.output_tokens
        
        if trace.cache_hit:
            self.metrics["cache_hits"] += 1
        if trace.error:
            self.metrics["errors"] += 1
        
        # 按天存储日志
        date_str = trace.timestamp[:10]
        log_file = self.log_dir / f"traces_{date_str}.jsonl"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(trace), ensure_ascii=False) + "\n")
    
    def get_summary(self) -> dict:
        """获取汇总指标"""
        total = self.metrics["total_queries"]
        if total == 0:
            return self.metrics
        
        return {
            **self.metrics,
            "avg_latency_ms": self.metrics["total_latency_ms"] / total,
            "cache_hit_rate": self.metrics["cache_hits"] / total,
            "error_rate": self.metrics["errors"] / total,
            "avg_tokens_per_query": (
                self.metrics["total_input_tokens"] +
                self.metrics["total_output_tokens"]
            ) / total,
        }
    
    def find_bad_cases(self, date: str, 
                       min_latency_ms: float = 5000) -> list:
        """查找慢查询和报错请求"""
        log_file = self.log_dir / f"traces_{date}.jsonl"
        if not log_file.exists():
            return []
        
        bad_cases = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                trace = json.loads(line)
                if (trace["total_latency_ms"] > min_latency_ms 
                    or trace["error"]
                    or trace["user_feedback"] == "negative"):
                    bad_cases.append(trace)
        
        return bad_cases
```

**关键监控指标与告警阈值：**

| 指标 | 告警阈值 | 应对方式 |
|:---|:---|:---|
| P99 延迟 | > 8 秒 | 检查 LLM 服务、是否需要加缓存 |
| 错误率 | > 2% | 检查下游服务可用性 |
| 缓存命中率 | < 20%（预期 40%+） | 检查缓存配置、TTL 是否过短 |
| 日 Token 消耗 | 超预算 30% | 检查是否有异常高频调用 |
| 检索空结果率 | > 15% | 知识库覆盖不足，需补充文档 |

> 💡 **LangSmith 集成**：如果你用的是 LangChain，强烈推荐接入 LangSmith——只需设置 `LANGCHAIN_TRACING_V2=true` 和 API Key，自动记录所有 Chain 的输入输出和延迟，零代码改动。自建方案适合对数据安全有要求的企业。
### 8.4 成本控制：在质量和成本之间找到平衡

RAG 系统的成本构成不是只有 LLM 调用费——Embedding、向量库存储、Reranker 推理、文档解析都要算进去。先搞清楚钱花在哪，才知道该从哪省。

```
RAG 系统成本结构（日均 10000 次查询为例）：

  成本项              单次费用           日消耗          占比
  ──────────────────────────────────────────────────────────
  LLM 生成            ~3000 Token       $120-150        60%
  查询改写(LLM)       ~500 Token        $15-20          8%
  Embedding           ~100 Token        $2-3            1%
  Reranker            本地推理          GPU 算力         15%
  向量数据库          按存储 + QPS      $10-30/月        5%
  文档解析(离线)      一次性成本        摊销 $5/月       1%
  ──────────────────────────────────────────────────────────
  总计                                  ~$180/天        100%

  → LLM 是最大成本项，也是优化空间最大的
```

**四大成本优化策略：**

```
策略 ①：模型分级路由
═══════════════════════════════════════════════
简单 FAQ           → DeepSeek / GPT-4o-mini    便宜 90%
复杂综合推理       → GPT-4o / Claude 3.5       贵但质量高
知识库外的闲聊     → 直接拒绝，不调 LLM        零成本

策略 ②：语义缓存（8.1 已实现）
═══════════════════════════════════════════════
相同/相似问题命中缓存 → 节省 LLM 调用
命中率 40% → 日成本直降 40%

策略 ③：Prompt 瘦身
═══════════════════════════════════════════════
Context 塞 5 个 Chunk × 500 字 = 2500 字 → 可能浪费
实际有用的通常 2-3 个 → 精排后只取 Top 3
减少 40% Context Token

策略 ④：离线批处理优化
═══════════════════════════════════════════════
Embedding 用批量接口（降低 API 调用开销）
文档解析在低峰期执行（抢低价 GPU）
评测任务用便宜模型（不要用 GPT-4o 跑全量评测）
```

```python
class CostAwareRouter:
    """成本感知的模型路由器"""
    
    def __init__(self):
        # 模型配置：按成本从低到高
        self.models = {
            "cheap": {
                "name": "deepseek-chat",
                "input_price_per_1m": 0.14,   # $/1M Token
                "output_price_per_1m": 0.28,
            },
            "standard": {
                "name": "gpt-4o-mini",
                "input_price_per_1m": 0.15,
                "output_price_per_1m": 0.60,
            },
            "premium": {
                "name": "gpt-4o",
                "input_price_per_1m": 2.50,
                "output_price_per_1m": 10.00,
            },
        }
    
    def route(self, query: str, retrieval_results: list) -> str:
        """根据查询复杂度选择模型"""
        
        # 规则 1：检索结果为空 → 不调 LLM，直接拒绝
        if not retrieval_results:
            return "reject"
        
        # 规则 2：简单 FAQ（检索置信度高、只需1个文档）
        top_score = retrieval_results[0].get("score", 0)
        if top_score > 0.9 and len(retrieval_results) <= 2:
            return "cheap"
        
        # 规则 3：需要综合多个文档
        if len(retrieval_results) >= 4:
            return "premium"
        
        # 默认
        return "standard"
    
    def estimate_cost(self, model_tier: str, 
                      input_tokens: int, output_tokens: int) -> float:
        """估算本次调用成本"""
        if model_tier == "reject":
            return 0.0
        
        model = self.models[model_tier]
        cost = (
            input_tokens * model["input_price_per_1m"] / 1_000_000 +
            output_tokens * model["output_price_per_1m"] / 1_000_000
        )
        return cost
```

| 优化策略 | 实施难度 | 节省比例 | 质量影响 |
|:---|:---|:---|:---|
| 语义缓存 | ⭐⭐ | 30-50% | 无 |
| 模型分级路由 | ⭐⭐⭐ | 40-60% | 极小（简单问题不需要强模型） |
| Prompt 瘦身 | ⭐ | 15-25% | 需评测验证 |
| 批处理优化 | ⭐⭐ | 10-20% | 无 |

> 💡 **成本优化的黄金法则**：先保证质量，再压缩成本。每一次成本优化都必须跑一遍评测，确认核心指标（Faithfulness、Correctness）没有下降。用 5% 的质量换 50% 的成本通常是值得的，但用 20% 的质量换 10% 的成本就不值得了。
### 8.5 常见故障与排查指南

生产环境的问题千奇百怪，但 RAG 系统的故障模式是有规律可循的。这份排查手册按**现象 → 根因 → 解法**的结构组织，帮你快速定位问题。

```
故障 ①：回答完全不相关（答非所问）
═══════════════════════════════════════════════════════

  排查路径：
  ┌─ 检查检索结果 ──────────────────────────────┐
  │  查看 Trace 中 retrieved_docs 的内容          │
  │                                               │
  │  检索结果相关？                                │
  │    ├─ 是 → 问题在生成层（Prompt 或模型）       │
  │    │       → 检查 Prompt 模板，加强指令约束     │
  │    │                                          │
  │    └─ 否 → 问题在检索层                        │
  │            ├─ 查询改写是否合理？                │
  │            ├─ Embedding 模型是否匹配文档语言？  │
  │            └─ 分块策略是否把相关内容拆散了？     │
  └────────────────────────────────────────────────┘

故障 ②：回答包含编造内容（幻觉）
═══════════════════════════════════════════════════════

  常见原因：
  • Context 中没有足够信息，LLM 自行补充
  • Prompt 没有「不知道就说不知道」的约束
  • 检索到的文档部分相关，LLM 过度推断

  解法：
  • 强化 Prompt 的忠实度约束（第 6 章 System Prompt）
  • 加 Self-RAG 自我检查机制
  • 降低 temperature（0.1 ~ 0.3）

故障 ③：检索结果为空或极少
═══════════════════════════════════════════════════════

  排查顺序：
  1. 向量库里有数据吗？ → 检查 collection 文档数
  2. 查询向量和文档向量维度一致吗？
  3. Embedding 模型版本是否变更过？
     → 模型换了但没重建索引 = 维度/空间不匹配
  4. 相似度阈值是不是设太高了？（> 0.9 太严格）
  5. 分块太大导致语义稀释？

故障 ④：响应超时（> 10 秒）
═══════════════════════════════════════════════════════

  耗时定位（看 Trace 各阶段延迟）：
  • 查询改写慢 → LLM API 延迟，加超时重试
  • 向量检索慢 → 数据量大，需要加索引/分片
  • Reranker 慢 → 候选文档太多，减少召回数
  • LLM 生成慢 → 换小模型 / 缩短 Context / 流式化
```

**生产环境故障快查表：**

| 现象 | 首先检查 | 常见根因 | 快速修复 |
|:---|:---|:---|:---|
| 全部请求报错 | LLM API 状态 | API Key 过期/余额不足 | 切换备用 Key |
| 部分请求乱码 | 文档编码 | 解析时未指定 UTF-8 | 重新解析问题文档 |
| 某类问题突然变差 | 知识库最近更新 | 文档更新导致分块变化 | 回滚上一版本 |
| 缓存命中率骤降 | 缓存 TTL 设置 | 知识库更新触发缓存清空 | 调整清空策略为增量 |
| Token 消耗突增 | 最近 Prompt 修改 | System Prompt 变长了 | 检查 Prompt 长度 |
| 不同时间答案不同 | LLM temperature | 设了 > 0 的随机性 | 生产环境设 0.1 |

```python
class HealthChecker:
    """RAG 系统健康检查"""
    
    def __init__(self, llm, embedding_model, vector_store):
        self.llm = llm
        self.embedding = embedding_model
        self.vector_store = vector_store
    
    def full_check(self) -> dict:
        """运行所有健康检查"""
        results = {}
        
        # 1. LLM 连通性
        try:
            resp = self.llm.invoke("ping")
            results["llm"] = "✅ 正常"
        except Exception as e:
            results["llm"] = f"❌ {e}"
        
        # 2. Embedding 模型
        try:
            vec = self.embedding.encode("测试")
            results["embedding"] = f"✅ 维度={len(vec)}"
        except Exception as e:
            results["embedding"] = f"❌ {e}"
        
        # 3. 向量数据库
        try:
            count = self.vector_store.count()
            results["vector_store"] = f"✅ 文档数={count}"
        except Exception as e:
            results["vector_store"] = f"❌ {e}"
        
        # 4. 端到端测试
        try:
            test_query = "这是一个健康检查测试查询"
            test_emb = self.embedding.encode(test_query)
            search_results = self.vector_store.search(test_emb, top_k=1)
            results["e2e_search"] = f"✅ 返回 {len(search_results)} 条"
        except Exception as e:
            results["e2e_search"] = f"❌ {e}"
        
        # 汇总
        all_ok = all("✅" in v for v in results.values())
        results["status"] = "🟢 HEALTHY" if all_ok else "🔴 UNHEALTHY"
        
        return results

# 建议在 API 中暴露健康检查端点
# GET /health → HealthChecker().full_check()
```

> 💡 **运维最佳实践**：上线前跑一次 `full_check()`，确认所有组件连通；上线后每 5 分钟自动跑一次，异常立刻告警。大多数「用户反馈系统挂了」其实是 LLM API Key 过期或向量库连接断了——健康检查 5 秒就能定位。

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **性能三板斧** | 语义缓存（拦重复）+ 异步化（减等待）+ 批处理（提吞吐） |
| **增量索引** | 基于文件哈希检测变更，只处理增/删/改的文档 |
| **可观测性** | 请求级 Trace + 系统级 Metrics + 业务级 Analytics |
| **成本控制** | 模型分级路由 + 缓存 + Prompt 瘦身 + 离线批处理 |
| **故障排查** | 按现象定位层级（检索 or 生成），Trace 是最好的排查工具 |

---

## 9. 综合实战：从 0 到 1 构建企业知识库助手

前面 8 章我们逐个攻克了 RAG 的每个核心模块。这一章，我们把它们串成一个**完整可运行的系统**——用 FastAPI 做后端、LangChain 做编排、Milvus 做向量存储，构建一个企业知识库问答助手。

这个系统包含三大功能模块：文档管理（上传→解析→入库）、智能问答（改写→检索→生成）、评测看板（自动化质量追踪）。

### 9.1 系统架构与技术方案

先看全局架构，理解各模块之间的关系：

```
企业知识库助手 —— 系统架构：

  ┌─ 前端（可选）───────────────────────────────────┐
  │  文档上传页  │  问答对话页  │  评测看板页          │
  └──────┬───────────┬──────────────┬───────────────┘
         │           │              │
         ▼           ▼              ▼
  ┌─ FastAPI 后端 ──────────────────────────────────┐
  │                                                  │
  │  POST /docs/upload     文档管理模块              │
  │  GET  /docs/list       ├ 解析 → 分块 → 入库      │
  │  DELETE /docs/{id}     └ 增量更新 + 版本管理      │
  │                                                  │
  │  POST /chat/query      智能问答模块              │
  │  POST /chat/feedback   ├ 查询改写 → 多路召回     │
  │                        └ 精排 → 生成 → 引用溯源   │
  │                                                  │
  │  GET  /eval/run        评测模块                  │
  │  GET  /eval/history    └ 自动化评测 + 趋势追踪    │
  │                                                  │
  │  GET  /health          健康检查                  │
  ├──────────────────────────────────────────────────┤
  │                  核心依赖                         │
  │  LangChain │ BGE-M3 │ Milvus │ DeepSeek/GPT-4o  │
  └──────────────────────────────────────────────────┘
```

**项目目录结构：**

```
rag-assistant/
├── main.py                  # FastAPI 入口
├── config.py                # 配置管理
├── requirements.txt
│
├── modules/
│   ├── __init__.py
│   ├── parser.py            # 文档解析（第 2 章）
│   ├── chunker.py           # 智能分块（第 3 章）
│   ├── embedder.py          # Embedding 封装
│   ├── retriever.py         # 多路检索 + 融合（第 4-5 章）
│   ├── reranker.py          # 精排器（第 5 章）
│   ├── generator.py         # RAG 生成（第 6 章）
│   ├── cache.py             # 语义缓存（第 8 章）
│   └── observer.py          # 可观测性（第 8 章）
│
├── routers/
│   ├── __init__.py
│   ├── docs.py              # 文档管理 API
│   ├── chat.py              # 智能问答 API
│   └── eval.py              # 评测 API
│
├── knowledge_base/          # 文档存放目录
├── eval_data/               # 评测数据集
└── traces/                  # 请求日志
```

**核心配置文件：**

```python
# config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    """系统配置"""
    
    # ── LLM ──
    llm_model: str = "deepseek-chat"
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    llm_temperature: float = 0.1
    
    # ── Embedding ──
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimension: int = 1024
    
    # ── Milvus ──
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    collection_name: str = "knowledge_base"
    
    # ── 检索 ──
    dense_top_k: int = 20
    sparse_top_k: int = 20
    rerank_top_k: int = 5
    
    # ── 缓存 ──
    cache_similarity_threshold: float = 0.95
    cache_ttl_seconds: int = 86400
    
    # ── 路径 ──
    knowledge_base_dir: str = "./knowledge_base"
    eval_data_dir: str = "./eval_data"
    trace_dir: str = "./traces"
    index_registry_path: str = "./index_registry.json"

settings = Settings()
```

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from routers import docs, chat, eval as eval_router

# ── 应用生命周期管理 ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化，关闭时清理"""
    # 启动：初始化各模块
    print("🚀 初始化 RAG 系统...")
    
    from modules.embedder import get_embedder
    from modules.retriever import get_retriever
    from modules.generator import get_generator
    from modules.cache import get_cache
    from modules.observer import get_observer
    
    app.state.embedder = get_embedder()
    app.state.retriever = get_retriever()
    app.state.generator = get_generator()
    app.state.cache = get_cache(app.state.embedder)
    app.state.observer = get_observer()
    
    print("✅ 所有模块初始化完成")
    yield
    
    # 关闭：保存状态
    print("🛑 系统关闭，保存状态...")

# ── 创建应用 ──
app = FastAPI(
    title="企业知识库助手",
    description="基于 RAG 的智能文档问答系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ──
app.include_router(docs.router, prefix="/docs", tags=["文档管理"])
app.include_router(chat.router, prefix="/chat", tags=["智能问答"])
app.include_router(eval_router.router, prefix="/eval", tags=["评测"])

@app.get("/health")
async def health_check():
    """系统健康检查"""
    from modules.observer import get_observer
    observer = app.state.observer
    return {"status": "healthy", "metrics": observer.get_summary()}
```

> 💡 **架构设计原则**：每个模块（parser、chunker、retriever……）都是独立的类，通过 `config.py` 统一配置、通过 `app.state` 在请求间共享实例。这样任何模块都可以单独替换——比如把 Milvus 换成 Qdrant，只需改 `retriever.py`，其他代码不动。

### 9.2 实现文档管理模块：上传 → 解析 → 分块 → 入库

文档管理模块负责知识库的生命周期——从用户上传文件到文本入库，整条链路自动化。

```python
# routers/docs.py
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from pydantic import BaseModel

from config import settings
from modules.parser import DocumentParser
from modules.chunker import SmartChunker

router = APIRouter()

class UploadResponse(BaseModel):
    filename: str
    num_elements: int    # 解析出的元素数
    num_chunks: int      # 分块后的 Chunk 数
    message: str

@router.post("/upload", response_model=UploadResponse)
async def upload_document(request: Request, file: UploadFile = File(...)):
    """上传文档：保存 → 解析 → 分块 → Embedding → 入库"""
    
    # 1. 验证文件格式
    allowed_exts = {".pdf", ".docx", ".md", ".html", ".txt"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {suffix}，支持: {allowed_exts}"
        )
    
    # 2. 保存文件到知识库目录
    save_dir = Path(settings.knowledge_base_dir)
    save_dir.mkdir(exist_ok=True)
    save_path = save_dir / file.filename
    
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # 3. 解析文档
    parser = DocumentParser()
    elements = parser.parse(str(save_path))
    
    # 4. 智能分块
    chunker = SmartChunker()
    chunks = chunker.chunk(elements)
    
    # 5. Embedding + 入库
    embedder = request.app.state.embedder
    retriever = request.app.state.retriever
    
    texts = [c["content"] for c in chunks]
    embeddings = embedder.encode(texts)
    
    # 写入向量数据库（带元数据）
    chunk_ids = retriever.add_documents(
        embeddings=embeddings,
        documents=chunks,
        source=file.filename,
    )
    
    # 6. 记录 Trace
    observer = request.app.state.observer
    observer.log_event("doc_upload", {
        "filename": file.filename,
        "elements": len(elements),
        "chunks": len(chunks),
    })
    
    return UploadResponse(
        filename=file.filename,
        num_elements=len(elements),
        num_chunks=len(chunks),
        message=f"✅ 文档已入库，生成 {len(chunks)} 个检索单元",
    )

@router.get("/list")
async def list_documents(request: Request):
    """列出知识库中的所有文档"""
    kb_dir = Path(settings.knowledge_base_dir)
    if not kb_dir.exists():
        return {"documents": []}
    
    docs = []
    for f in kb_dir.iterdir():
        if f.is_file() and not f.name.startswith("."):
            docs.append({
                "filename": f.name,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "modified": f.stat().st_mtime,
            })
    
    return {"documents": docs, "total": len(docs)}

@router.delete("/{filename}")
async def delete_document(filename: str, request: Request):
    """删除文档：同时清理文件和向量库中的数据"""
    file_path = Path(settings.knowledge_base_dir) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 1. 从向量库中删除该文档的所有 Chunk
    retriever = request.app.state.retriever
    deleted_count = retriever.delete_by_source(filename)
    
    # 2. 删除本地文件
    file_path.unlink()
    
    return {
        "message": f"✅ 已删除 {filename}，清理了 {deleted_count} 个检索单元",
    }
```

```
文档上传的完整流程：

  用户上传 company_policy.pdf
       │
       ▼
  ① 文件格式校验 ──→ 不支持？ → 400 错误
       │
       ▼
  ② 保存到 ./knowledge_base/company_policy.pdf
       │
       ▼
  ③ DocumentParser 解析
     → 58 个元素（35 段正文 + 8 个表格 + 15 个标题）
       │
       ▼
  ④ SmartChunker 分块
     → 42 个 Chunk（语义分块 + 表格保留）
       │
       ▼
  ⑤ BGE-M3 批量 Embedding
     → 42 个 1024 维向量
       │
       ▼
  ⑥ 写入 Milvus
     → 42 条记录（向量 + 原文 + 元数据）
       │
       ▼
  ⑦ 返回结果
     → {"num_chunks": 42, "message": "✅ 文档已入库"}
```

> 💡 **生产建议**：大文件上传应该改为异步任务（返回任务 ID，前端轮询进度）。一个 200 页的 PDF 解析 + Embedding 可能需要 30 秒以上，同步接口会超时。
### 9.3 实现智能问答模块：查询改写 → 多路召回 → 精排 → 生成

这是整个系统的核心——用户提问后，串联前面所有章节的技术，返回准确、可溯源的回答。

```python
# routers/chat.py
import time
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    stream: bool = True          # 是否流式输出
    use_cache: bool = True       # 是否启用缓存

class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]          # 引用来源
    trace_id: str
    cache_hit: bool
    latency_ms: float

@router.post("/query")
async def query(req: QueryRequest, request: Request):
    """智能问答：完整 RAG 流水线"""
    start_time = time.time()
    
    cache = request.app.state.cache
    embedder = request.app.state.embedder
    retriever = request.app.state.retriever
    generator = request.app.state.generator
    observer = request.app.state.observer
    
    # ── 阶段 0：语义缓存 ──
    if req.use_cache:
        cached = cache.get(req.question)
        if cached:
            latency = (time.time() - start_time) * 1000
            observer.record_query(
                query=req.question, answer=cached["answer"],
                cache_hit=True, latency_ms=latency,
            )
            return QueryResponse(
                answer=cached["answer"],
                sources=cached["sources"],
                trace_id=cached.get("trace_id", "cache"),
                cache_hit=True,
                latency_ms=latency,
            )
    
    # ── 阶段 1：查询改写 ──
    rewritten = await generator.rewrite_query(req.question)
    
    # ── 阶段 2：多路召回 ──
    query_embedding = embedder.encode(rewritten)
    
    # Dense 检索（语义）
    dense_results = retriever.dense_search(
        query_embedding, top_k=20
    )
    # Sparse 检索（关键词）
    sparse_results = retriever.sparse_search(
        rewritten, top_k=20
    )
    
    # RRF 融合
    candidates = retriever.rrf_fusion(dense_results, sparse_results)
    
    # ── 阶段 3：Reranker 精排 ──
    top_docs = retriever.rerank(rewritten, candidates, top_k=5)
    
    # ── 阶段 4：生成回答 ──
    if req.stream:
        # 流式输出
        async def stream_answer():
            full_answer = ""
            async for chunk in generator.stream_generate(
                question=req.question,
                rewritten_question=rewritten,
                context_docs=top_docs,
            ):
                full_answer += chunk
                yield chunk
            
            # 流式结束后，异步写入缓存和日志
            latency = (time.time() - start_time) * 1000
            sources = [{"title": d["metadata"].get("heading", ""),
                        "source": d["metadata"]["source"],
                        "page": d["metadata"].get("page", 0)}
                       for d in top_docs]
            
            cache.put(req.question, full_answer, sources)
            observer.record_query(
                query=req.question, answer=full_answer,
                cache_hit=False, latency_ms=latency,
                retrieved_count=len(candidates),
                reranked_count=len(top_docs),
            )
        
        return StreamingResponse(
            stream_answer(),
            media_type="text/plain",
        )
    
    else:
        # 非流式输出
        answer = await generator.generate(
            question=req.question,
            rewritten_question=rewritten,
            context_docs=top_docs,
        )
        
        latency = (time.time() - start_time) * 1000
        sources = [{"title": d["metadata"].get("heading", ""),
                    "source": d["metadata"]["source"],
                    "page": d["metadata"].get("page", 0)}
                   for d in top_docs]
        
        cache.put(req.question, answer, sources)
        observer.record_query(
            query=req.question, answer=answer,
            cache_hit=False, latency_ms=latency,
        )
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            trace_id=observer.last_trace_id,
            cache_hit=False,
            latency_ms=latency,
        )

class FeedbackRequest(BaseModel):
    trace_id: str
    feedback: str    # "positive" 或 "negative"
    comment: str = ""

@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest, request: Request):
    """用户反馈：标记回答质量"""
    observer = request.app.state.observer
    observer.record_feedback(
        trace_id=req.trace_id,
        feedback=req.feedback,
        comment=req.comment,
    )
    return {"message": "✅ 反馈已记录，感谢！"}
```

```
一次完整的问答请求流程：

  用户: "我们的年假制度是怎样的？"
       │
       ▼
  ① 语义缓存查找 → 未命中
       │
       ▼
  ② 查询改写
     → "年休假天数规定 请假流程 休假制度"
       │
       ▼
  ③ 多路召回
     Dense: 20 条 ┐
                  ├→ RRF 融合去重 → 28 条候选
     Sparse: 20 条┘
       │
       ▼
  ④ Reranker 精排 → Top 5
     [0.95] 员工手册-休假制度.pdf (p.12)
     [0.91] 人事政策-年假规定.docx (p.3)
     [0.85] FAQ-常见问题.md (#休假)
     [0.72] 员工手册-考勤制度.pdf (p.8)
     [0.68] 入职指南.pdf (p.15)
       │
       ▼
  ⑤ RAG 生成（流式输出）
     "根据公司制度，年假规定如下：
      1. 工作满1年不满10年：5天...
      2. 工作满10年不满20年：10天...
      
      📎 来源：员工手册-休假制度 第12页"
       │
       ▼
  ⑥ 写入缓存 + 记录 Trace
```

> 💡 **流式输出是刚需**：生产环境中 LLM 生成通常需要 2-3 秒。用流式输出，用户在 200ms 内就能看到第一个字，体感完全不同。FastAPI 的 `StreamingResponse` + LangChain 的 `astream()` 是最简洁的实现方式。
### 9.4 实现评测看板：自动化质量追踪

有了问答模块，还需要一套**持续验证系统质量**的机制。评测看板把第 7 章的评测能力包装成 API，支持一键跑评测、查看历史趋势。

```python
# routers/eval.py
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Request
from pydantic import BaseModel

from config import settings

router = APIRouter()

class EvalResult(BaseModel):
    version: str
    timestamp: str
    num_samples: int
    metrics: dict
    alerts: list[str]

@router.post("/run")
async def run_evaluation(request: Request, version_tag: str = ""):
    """运行一次完整评测"""
    
    # 1. 加载评测数据集
    eval_file = Path(settings.eval_data_dir) / "eval_dataset.json"
    if not eval_file.exists():
        return {"error": "评测数据集不存在，请先准备 eval_dataset.json"}
    
    with open(eval_file, "r", encoding="utf-8") as f:
        eval_data = json.load(f)
    
    tag = version_tag or datetime.now().strftime("%Y%m%d_%H%M")
    
    # 2. 对每条样本调用 RAG 系统
    results = []
    for i, sample in enumerate(eval_data):
        # 调用问答接口（不走缓存）
        from routers.chat import query as chat_query
        from pydantic import BaseModel
        
        class MockReq:
            question = sample["question"]
            stream = False
            use_cache = False
        
        response = await chat_query(MockReq(), request)
        
        results.append({
            "question": sample["question"],
            "answer": response.answer,
            "ground_truth": sample.get("ground_truth", ""),
            "sources": response.sources,
        })
        
        if (i + 1) % 10 == 0:
            print(f"  评测进度: {i+1}/{len(eval_data)}")
    
    # 3. 计算指标（简化版，生产用 RAGAS）
    metrics = calculate_metrics(results)
    
    # 4. 检查告警
    alerts = []
    thresholds = {
        "answer_relevancy": 0.80,
        "source_coverage": 0.75,
    }
    for metric, threshold in thresholds.items():
        if metric in metrics and metrics[metric] < threshold:
            alerts.append(f"⚠️ {metric}={metrics[metric]:.3f} < {threshold}")
    
    # 5. 存储结果
    report = {
        "version": tag,
        "timestamp": datetime.now().isoformat(),
        "num_samples": len(eval_data),
        "metrics": metrics,
        "alerts": alerts,
    }
    
    results_dir = Path(settings.eval_data_dir) / "results"
    results_dir.mkdir(exist_ok=True)
    
    with open(results_dir / f"eval_{tag}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return EvalResult(**report)

@router.get("/history")
async def eval_history():
    """查看评测历史和趋势"""
    results_dir = Path(settings.eval_data_dir) / "results"
    if not results_dir.exists():
        return {"history": []}
    
    history = []
    for f in sorted(results_dir.glob("eval_*.json")):
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            history.append({
                "version": data["version"],
                "timestamp": data["timestamp"],
                "metrics": data["metrics"],
                "alerts": data.get("alerts", []),
            })
    
    return {
        "history": history,
        "total_runs": len(history),
        "latest": history[-1] if history else None,
    }

def calculate_metrics(results: list[dict]) -> dict:
    """计算评测指标（简化版）"""
    if not results:
        return {}
    
    relevancy_scores = []
    source_coverage = []
    
    for r in results:
        # 简单相关性：回答中是否包含 ground_truth 的关键词
        if r["ground_truth"]:
            gt_keywords = set(r["ground_truth"].split())
            answer_keywords = set(r["answer"].split())
            overlap = len(gt_keywords & answer_keywords) / len(gt_keywords)
            relevancy_scores.append(min(overlap * 1.5, 1.0))
        
        # 来源覆盖：是否返回了有效来源
        source_coverage.append(1.0 if r["sources"] else 0.0)
    
    return {
        "answer_relevancy": sum(relevancy_scores) / len(relevancy_scores)
            if relevancy_scores else 0.0,
        "source_coverage": sum(source_coverage) / len(source_coverage),
        "total_evaluated": len(results),
    }
```

```
评测看板的使用流程：

  ① 准备评测数据集
     eval_data/eval_dataset.json:
     [
       {"question": "年假多少天？", "ground_truth": "工作满1年5天..."},
       {"question": "报销流程？", "ground_truth": "提交申请→主管审批..."},
       ...
     ]
  
  ② 运行评测
     POST /eval/run?version_tag=v1.2
     → 自动对每条样本调用 RAG 系统
     → 计算指标 + 生成报告
  
  ③ 查看历史
     GET /eval/history
     → 返回所有历史评测指标
     → 前端可画趋势图
  
  ④ 对比版本
     v1.0: relevancy=0.72  ──→  v1.2: relevancy=0.85  📈
     v1.0: coverage=0.80   ──→  v1.2: coverage=0.90   📈
```

> 💡 **生产级评测**：这里的 `calculate_metrics` 是简化版，生产环境建议直接用 RAGAS（第 7 章已详细介绍）。简化版适合快速验证和 CI/CD 流水线中的冒烟测试。

**第 9 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **系统架构** | FastAPI + LangChain + Milvus，模块化设计、独立可替换 |
| **文档管理** | 上传 → 解析 → 分块 → Embedding → 入库，全链路自动化 |
| **智能问答** | 缓存 → 改写 → 多路召回 → 精排 → 流式生成 → 引用溯源 |
| **评测看板** | 一键跑评测 + 历史趋势 + 版本对比 + 告警 |
| **生产化要点** | 异步任务、流式输出、健康检查、模块化配置 |

---

## 附录：RAG 工程速查手册

这份速查手册汇总了全教程的核心参数和选型建议，方便日常开发时快速查阅。

### A.1 分块策略参数速查表

| 文档类型 | 推荐策略 | chunk_size | chunk_overlap | 注意事项 |
|:---|:---|:---|:---|:---|
| 内部 FAQ | 按问答对分块 | 200-300 | 0 | 一问一答完整保留 |
| 技术文档 | 按标题层级 + 语义 | 500-800 | 100 | 保留代码块完整性 |
| 合同/法规 | 按条款结构 | 300-500 | 50 | 按条款编号分块 |
| 产品手册 | 语义分块 | 400-600 | 80 | 表格和图片独立处理 |
| 会议纪要 | 按时间/议题 | 300-500 | 50 | 保留发言人信息 |
| 学术论文 | 按章节 | 600-1000 | 100 | 摘要和结论单独作为 Chunk |

```
分块黄金法则：

  ① chunk_size 的选择
     太小（<200）→ 上下文不足，LLM 无法理解
     太大（>1000）→ 语义稀释，检索不精准
     甜蜜点：400-800 字符（取决于文档类型）

  ② chunk_overlap 的选择
     通常设为 chunk_size 的 10-20%
     代码类文档可以设 0（按代码块完整切）

  ③ 表格永远不拆
     一个表格 = 一个 Chunk，不管多大
     超大表格转自然语言描述
```

### A.2 Embedding 模型选型对比

| 模型 | 维度 | 中文效果 | 多语言 | 速度 | 成本 | 推荐场景 |
|:---|:---|:---|:---|:---|:---|:---|
| **BAAI/bge-m3** | 1024 | ⭐⭐⭐⭐⭐ | ✅ | 中等 | 本地免费 | 首选方案，中文最强 |
| **bge-large-zh** | 1024 | ⭐⭐⭐⭐ | ❌ | 中等 | 本地免费 | 纯中文场景 |
| **text-embedding-3-small** | 1536 | ⭐⭐⭐⭐ | ✅ | 快 | $0.02/1M | 省事、效果好 |
| **text-embedding-3-large** | 3072 | ⭐⭐⭐⭐⭐ | ✅ | 快 | $0.13/1M | 精度优先 |
| **m3e-base** | 768 | ⭐⭐⭐ | ❌ | 快 | 本地免费 | 轻量中文场景 |
| **jina-embeddings-v3** | 1024 | ⭐⭐⭐⭐ | ✅ | 快 | API 付费 | 多语言 + 长文本 |

```
Embedding 选型决策树：

  是否需要中文？
  ├─ 是 → 是否能本地部署 GPU？
  │       ├─ 是 → BGE-M3（最佳性价比）
  │       └─ 否 → text-embedding-3-small（API 调用）
  │
  └─ 否 → text-embedding-3-small/large
           （英文场景 OpenAI 最省事）
```

### A.3 Reranker 模型选型对比

| 模型 | 中文效果 | 速度 | 最大长度 | 推荐场景 |
|:---|:---|:---|:---|:---|
| **bge-reranker-v2-m3** | ⭐⭐⭐⭐⭐ | 中等 | 8192 | 首选方案 |
| **bge-reranker-large** | ⭐⭐⭐⭐ | 慢 | 512 | 短文本精排 |
| **Cohere Rerank v3** | ⭐⭐⭐⭐ | 快 | 4096 | API 调用，多语言 |
| **cross-encoder/ms-marco** | ⭐⭐ | 中等 | 512 | 英文场景 |

> 💡 Reranker 是 RAG 中投入产出比最高的组件——加一个 Reranker 通常能让端到端准确率提升 10-15%，而代码改动不到 20 行。

### A.4 RAG Prompt 模板库

**通用问答 Prompt：**

```
你是一个企业知识库助手。请严格根据下方【参考资料】回答用户的问题。

规则：
1. 只使用参考资料中的信息回答，不要编造或推测
2. 如果参考资料中没有相关信息，请明确说"根据现有资料，我无法回答这个问题"
3. 在回答末尾标注信息来源（文档名称和页码）
4. 使用 Markdown 格式组织答案

【参考资料】
{context}

【用户问题】
{question}
```

**严格型 Prompt（合规/法务场景）：**

```
你是法务合规助手。基于下方参考资料回答问题。

硬性规则（不可违反）：
1. 必须逐字引用原文，不得改写或概括
2. 每一句回答都必须标注来源段落
3. 如无法从资料中找到答案，回复："该问题需要法务团队人工确认"
4. 不提供任何法律建议或个人分析

【参考资料】
{context}

【问题】
{question}
```

**摘要型 Prompt（报告/周报场景）：**

```
请根据下方资料，整理出一份结构化摘要。

要求：
1. 分点总结（不超过 5 个要点）
2. 每个要点一句话概括 + 关键数据
3. 最后给出一句话总结
4. 标注每个要点的来源文档

【资料】
{context}

【主题】
{question}
```

### A.5 常见问题 FAQ

**Q: 向量数据库选 Milvus 还是 Chroma？**
> Chroma 适合原型验证和小数据量（<10 万条），零配置开箱即用。Milvus 适合生产环境（百万级以上），支持分布式、混合检索、细粒度过滤。如果数据量 < 50 万且不需要关键词检索，Qdrant 也是个好选择——Rust 写的，性能优秀。

**Q: Embedding 模型换了，需要重建索引吗？**
> 必须重建。不同模型的向量空间完全不同，旧向量和新查询向量无法比较。这也是为什么 8.2 节强调版本管理——换模型属于「全量重建」场景。

**Q: chunk_size 到底设多少？**
> 没有万能答案。从 500 开始，跑一次评测；分别试 300 和 800，再跑评测，比较 Recall@5。通常 FAQ 类文档 300 最优，技术文档 500-800 最优，法律文档 300-500 最优。

**Q: 要不要用 LangChain？还是自己写？**
> 如果你的团队不超过 3 人、项目需要快速交付，用 LangChain——生态丰富、集成方便。如果你追求极致性能和完全控制，自己写核心逻辑（检索 + Prompt 组装），用 LangChain 做胶水代码。LangChain 最大的价值在于它的抽象层，方便快速切换底层组件。

**Q: RAG 和 Fine-tuning 什么时候该选哪个？**
> 简单判断：如果问题是「让模型知道新知识」→ RAG；如果问题是「让模型学会新能力/风格」→ Fine-tuning。两者不矛盾，可以组合使用——Fine-tuned 模型 + RAG 在企业场景中效果最好。

**Q: 如何处理多语言文档？**
> 使用多语言 Embedding 模型（BGE-M3 或 text-embedding-3）。查询和文档可以是不同语言，多语言模型会把它们映射到同一个向量空间。但要注意：分块时需要按语言设置不同的 chunk_size（中文字符密度高，通常比英文文档设小 20%）。

