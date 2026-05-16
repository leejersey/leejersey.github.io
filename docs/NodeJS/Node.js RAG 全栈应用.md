# Node.js RAG 全栈应用

> 用 TypeScript 构建生产级 RAG 系统——文档解析、Embedding 生成、向量检索、LLM 增强回答、流式响应全链路实战。

---

## 1. RAG 是什么：为什么 LLM 需要外部知识

### 1.1 LLM 的知识局限与幻觉

```
LLM 的三大问题：

  1. 知识截止    → GPT-4 训练数据截止到某个日期，不知道最新信息
  2. 幻觉        → 一本正经地编造不存在的事实
  3. 私有数据盲区 → 不知道你公司的文档、产品手册、内部 Wiki

  例：
  Q: "我们公司的退款政策是什么？"
  A: "根据通用做法，退款通常在 30 天内..."  ← 编的！
```

RAG（Retrieval-Augmented Generation）的解决方案：**先检索，后生成**。

### 1.2 RAG 核心架构：索引 → 检索 → 生成

```
RAG 全链路数据流：

  ┌─ 离线阶段（Index）──────────────────────────┐
  │                                              │
  │  文档 → 解析 → 分块 → Embedding → 向量数据库  │
  │  (PDF)  (提取)  (chunk) (向量化)    (存储)    │
  └──────────────────────────────────────────────┘

  ┌─ 在线阶段（Retrieve + Generate）─────────────┐
  │                                              │
  │  用户提问 → Embedding → 向量检索 → Top-K 结果  │
  │                                    ↓         │
  │  Prompt = "基于以下上下文回答：" + 检索结果     │
  │                                    ↓         │
  │  LLM → 生成回答 → 流式返回给用户               │
  └──────────────────────────────────────────────┘
```

### 1.3 RAG vs 微调：什么时候用哪个

| | RAG | 微调（Fine-tuning） |
|---|---|---|
| **原理** | 检索外部知识注入 Prompt | 修改模型权重 |
| **数据更新** | 实时（更新向量库即可） | 需要重新训练 |
| **成本** | 低（只需 API 费用） | 高（训练 GPU 费用） |
| **幻觉** | ✅ 有来源可溯 | ⚠️ 仍可能幻觉 |
| **适合** | 知识库问答、文档搜索 | 风格调整、特定任务 |
| **推荐** | 大部分场景 ✅ | 需要改变模型行为时 |

---

## 2. 文档解析：PDF / Markdown / 网页

### 2.1 PDF 文本提取

```bash
npm install pdf-parse
```

```typescript
import fs from 'fs';
import pdfParse from 'pdf-parse';

async function extractPDF(filePath: string): Promise<string> {
  const buffer = fs.readFileSync(filePath);
  const data = await pdfParse(buffer);

  console.log(`页数: ${data.numpages}`);
  console.log(`字数: ${data.text.length}`);

  return data.text;  // 纯文本
}

const text = await extractPDF('company-handbook.pdf');
```

### 2.2 Markdown 与网页解析

```bash
npm install unified remark-parse remark-stringify
npm install cheerio
```

```typescript
// Markdown 解析：保留结构
function parseMarkdown(content: string): string[] {
  // 按标题分块
  const sections = content.split(/^#{1,3}\s+/m);
  return sections
    .map(s => s.trim())
    .filter(s => s.length > 50);  // 过滤太短的块
}

// 网页抓取
import * as cheerio from 'cheerio';

async function extractWebPage(url: string): Promise<string> {
  const response = await fetch(url);
  const html = await response.text();
  const $ = cheerio.load(html);

  // 移除非内容元素
  $('script, style, nav, footer, header').remove();

  // 提取正文
  const text = $('article, main, .content, body').text();
  return text.replace(/\s+/g, ' ').trim();
}
```

### 2.3 文本分块策略：固定 vs 语义 vs 递归

```
为什么需要分块？

  LLM 的 Context Window 有限（4K-128K tokens）
  一篇 100 页的 PDF → 不可能全部塞进 Prompt
  → 需要把文档切成小块 → 只检索最相关的几块
```

```typescript
// 策略一：固定大小分块（简单但可能切断句子）
function fixedChunk(text: string, chunkSize = 500, overlap = 50): string[] {
  const chunks: string[] = [];
  for (let i = 0; i < text.length; i += chunkSize - overlap) {
    chunks.push(text.slice(i, i + chunkSize));
  }
  return chunks;
}

// 策略二：递归分块（按自然边界切分）— 推荐
function recursiveChunk(
  text: string,
  maxSize = 500,
  separators = ['\n\n', '\n', '。', '. ', ' ']
): string[] {
  if (text.length <= maxSize) return [text];

  const sep = separators.find(s => text.includes(s)) || '';
  const parts = text.split(sep);
  const chunks: string[] = [];
  let current = '';

  for (const part of parts) {
    if ((current + sep + part).length > maxSize && current) {
      chunks.push(current.trim());
      current = part;
    } else {
      current = current ? current + sep + part : part;
    }
  }
  if (current.trim()) chunks.push(current.trim());

  return chunks.flatMap(c =>
    c.length > maxSize ? recursiveChunk(c, maxSize, separators.slice(1)) : [c]
  );
}
```

分块策略对比：

| 策略 | 优点 | 缺点 | 适合 |
|---|---|---|---|
| 固定大小 | 简单 | 切断句子/段落 | 快速原型 |
| 按段落 | 保留语义 | 段落大小不均 | Markdown |
| 递归分块 | 自适应边界 | 实现稍复杂 | 通用 ✅ |
| 语义分块 | 最精确 | 需要 Embedding | 高质量要求 |

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| RAG 架构 | Index（离线）→ Retrieve（检索）→ Generate（生成） |
| 文档解析 | pdf-parse / Cheerio / Markdown split |
| 分块策略 | 递归分块推荐，保留自然边界 + overlap |

---

## 3. Embedding：文本向量化

### 3.1 Embedding 原理：文本 → 向量

```
Embedding 的核心思想：

  "Node.js 是一个运行时"  →  [0.12, -0.34, 0.56, ..., 0.78]  (1536维)
  "JavaScript 服务端环境"  →  [0.11, -0.32, 0.55, ..., 0.77]  (1536维)
  "今天天气很好"          →  [0.89, 0.12, -0.67, ..., 0.03]  (1536维)

  语义相似的文本 → 向量距离近
  语义不同的文本 → 向量距离远

  相似度计算：
  cos("Node.js 运行时", "JavaScript 服务端") = 0.95  ← 高相似
  cos("Node.js 运行时", "今天天气很好")       = 0.12  ← 低相似
```

### 3.2 OpenAI text-embedding-3-small/large

```bash
npm install openai
```

```typescript
import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// 单条文本向量化
async function embed(text: string): Promise<number[]> {
  const response = await openai.embeddings.create({
    model: 'text-embedding-3-small',  // 1536 维，$0.02/1M tokens
    input: text,
  });
  return response.data[0].embedding;
}

// 批量向量化（API 支持批量）
async function embedBatch(texts: string[]): Promise<number[][]> {
  const response = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: texts,  // 最多 2048 条
  });
  return response.data.map(d => d.embedding);
}

const vector = await embed('Node.js Stream 流式编程');
console.log(`维度: ${vector.length}`);  // 1536
```

模型对比：

| 模型 | 维度 | 价格 | 性能 |
|---|---|---|---|
| `text-embedding-3-small` | 1536 | $0.02/1M tokens | 够用 ✅ |
| `text-embedding-3-large` | 3072 | $0.13/1M tokens | 更精确 |
| `text-embedding-ada-002` | 1536 | $0.10/1M tokens | 旧版 |

### 3.3 本地 Embedding（Ollama）

```bash
# 安装 Ollama + 下载模型
ollama pull nomic-embed-text
```

```typescript
// 本地 Embedding（免费，离线可用）
async function embedLocal(text: string): Promise<number[]> {
  const response = await fetch('http://localhost:11434/api/embeddings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'nomic-embed-text',
      prompt: text,
    }),
  });
  const data = await response.json();
  return data.embedding;  // 768 维
}
```

| | OpenAI API | Ollama 本地 |
|---|---|---|
| **费用** | 按 token 计费 | 免费 |
| **速度** | 快（GPU 服务器） | 取决于本地硬件 |
| **隐私** | 数据发送到 OpenAI | 数据不出本地 ✅ |
| **维度** | 1536/3072 | 768（nomic） |
| **推荐** | 生产环境 | 开发/隐私敏感 |

### 3.4 批量处理与性能优化

```typescript
// 带限流的批量 Embedding
async function embedChunks(
  chunks: string[],
  batchSize = 100,
  delayMs = 200,
): Promise<{ text: string; embedding: number[] }[]> {
  const results: { text: string; embedding: number[] }[] = [];

  for (let i = 0; i < chunks.length; i += batchSize) {
    const batch = chunks.slice(i, i + batchSize);
    const embeddings = await embedBatch(batch);

    for (let j = 0; j < batch.length; j++) {
      results.push({ text: batch[j], embedding: embeddings[j] });
    }

    console.log(`已处理 ${Math.min(i + batchSize, chunks.length)}/${chunks.length}`);

    // 限流：避免 API rate limit
    if (i + batchSize < chunks.length) {
      await new Promise(r => setTimeout(r, delayMs));
    }
  }

  return results;
}

// 使用
const chunks = recursiveChunk(documentText, 500);
const embedded = await embedChunks(chunks);
console.log(`${embedded.length} 个 chunk 已向量化`);
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Embedding | 文本 → 高维向量，语义相似 = 向量距离近 |
| OpenAI API | `text-embedding-3-small`，1536 维，批量支持 |
| Ollama 本地 | `nomic-embed-text`，免费离线，768 维 |
| 批量优化 | 分批 + 限流 + 进度日志 |

> **下一章**：向量数据库——Pinecone 云端 / pgvector 自托管，存储与检索实战。

---

## 4. 向量数据库：存储与检索

### 4.1 向量数据库选型对比

```
向量数据库的作用：

  Embedding 向量 [0.12, -0.34, ...] → 存储
  查询向量 [0.11, -0.32, ...]       → 找到最相似的 Top-K 条

  核心能力：
  1. 高效的近似最近邻（ANN）搜索
  2. 支持元数据过滤（按来源、日期等过滤）
  3. 支持百万/亿级向量
```

| | Pinecone | pgvector | Qdrant | Chroma |
|---|---|---|---|---|
| **部署** | 云托管 | PostgreSQL 插件 | 自托管/云 | 本地/嵌入式 |
| **规模** | 亿级 | 百万级 | 亿级 | 开发测试 |
| **免费额度** | ✅ 有 | ✅ 自托管免费 | ✅ 有 | ✅ 免费 |
| **元数据过滤** | ✅ | ✅ | ✅ | ✅ |
| **推荐场景** | 生产（免运维） | 已有 PG 的项目 | 高性能自托管 | 快速原型 |

### 4.2 Pinecone 云端方案

```bash
npm install @pinecone-database/pinecone
```

```typescript
import { Pinecone } from '@pinecone-database/pinecone';

const pc = new Pinecone({ apiKey: process.env.PINECONE_API_KEY! });

// 创建索引（只需一次）
await pc.createIndex({
  name: 'knowledge-base',
  dimension: 1536,       // 必须匹配 Embedding 模型维度
  metric: 'cosine',
  spec: { serverless: { cloud: 'aws', region: 'us-east-1' } },
});

const index = pc.index('knowledge-base');

// 写入向量
async function upsertChunks(
  chunks: { id: string; text: string; embedding: number[]; source: string }[]
) {
  const vectors = chunks.map(c => ({
    id: c.id,
    values: c.embedding,
    metadata: { text: c.text, source: c.source },
  }));

  // Pinecone 批量上限 100 条
  for (let i = 0; i < vectors.length; i += 100) {
    await index.upsert(vectors.slice(i, i + 100));
  }
}

// 查询：找到最相似的 5 条
async function search(queryEmbedding: number[], topK = 5) {
  const results = await index.query({
    vector: queryEmbedding,
    topK,
    includeMetadata: true,
  });

  return results.matches.map(m => ({
    score: m.score,
    text: m.metadata?.text as string,
    source: m.metadata?.source as string,
  }));
}
```

### 4.3 pgvector：PostgreSQL 原生向量

```sql
-- 安装 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建表
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  source TEXT,
  embedding VECTOR(1536),  -- 1536 维向量
  created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引（HNSW 高性能）
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
```

```bash
npm install pg pgvector
```

```typescript
import pg from 'pg';
import pgvector from 'pgvector/pg';

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
await pgvector.registerType(pool);

// 写入
async function insertChunk(content: string, source: string, embedding: number[]) {
  await pool.query(
    'INSERT INTO documents (content, source, embedding) VALUES ($1, $2, $3)',
    [content, source, pgvector.toSql(embedding)]
  );
}

// 相似度检索
async function search(queryEmbedding: number[], topK = 5) {
  const result = await pool.query(
    `SELECT content, source, 1 - (embedding <=> $1) AS score
     FROM documents
     ORDER BY embedding <=> $1
     LIMIT $2`,
    [pgvector.toSql(queryEmbedding), topK]
  );
  return result.rows;
}

// 带元数据过滤的检索
async function searchWithFilter(
  queryEmbedding: number[],
  source: string,
  topK = 5
) {
  const result = await pool.query(
    `SELECT content, source, 1 - (embedding <=> $1) AS score
     FROM documents
     WHERE source = $2
     ORDER BY embedding <=> $1
     LIMIT $3`,
    [pgvector.toSql(queryEmbedding), source, topK]
  );
  return result.rows;
}
```

### 4.4 相似度检索与元数据过滤

```
三种距离度量：

  余弦相似度（cosine）：
    cos(A, B) = A·B / (|A|·|B|)
    值域 [0, 1]，1 = 完全相同
    推荐：文本搜索 ✅

  欧氏距离（L2）：
    d(A, B) = √(Σ(ai - bi)²)
    值越小越相似
    推荐：图像特征

  内积（dot product）：
    A·B = Σ(ai × bi)
    值越大越相似
    推荐：已归一化的向量
```

---

## 5. 检索增强生成：RAG Pipeline

### 5.1 RAG Pipeline 完整实现

```typescript
import OpenAI from 'openai';

const openai = new OpenAI();

class RAGPipeline {
  constructor(
    private embedFn: (text: string) => Promise<number[]>,
    private searchFn: (embedding: number[], topK: number) => Promise<SearchResult[]>,
  ) {}

  async query(question: string): Promise<RAGResponse> {
    // Step 1: 将问题向量化
    const queryEmbedding = await this.embedFn(question);

    // Step 2: 检索相关文档
    const docs = await this.searchFn(queryEmbedding, 5);

    // Step 3: 构建 Prompt
    const context = docs.map((d, i) =>
      `[${i + 1}] ${d.text}\n来源: ${d.source}`
    ).join('\n\n');

    const prompt = buildPrompt(question, context);

    // Step 4: LLM 生成回答
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: prompt },
      ],
      temperature: 0.3,  // 低温度 = 更确定的回答
    });

    return {
      answer: completion.choices[0].message.content!,
      sources: docs.map(d => ({ text: d.text, source: d.source, score: d.score })),
    };
  }
}

interface SearchResult {
  text: string;
  source: string;
  score: number;
}

interface RAGResponse {
  answer: string;
  sources: { text: string; source: string; score: number }[];
}
```

### 5.2 Prompt 模板设计

```typescript
const SYSTEM_PROMPT = `你是一个知识库助手。根据提供的上下文回答用户问题。

规则：
1. 只基于上下文中的信息回答，不要编造
2. 如果上下文中没有相关信息，说"根据现有资料，无法回答此问题"
3. 回答时引用来源编号，如 [1]、[2]
4. 保持回答简洁、准确`;

function buildPrompt(question: string, context: string): string {
  return `## 上下文

${context}

## 问题

${question}

## 要求
请基于上述上下文回答问题，并标注引用来源编号。`;
}
```

```
Prompt 设计的关键原则：

  1. 角色定义  → System Prompt 限定行为边界
  2. 上下文注入 → 检索结果放在用户消息中
  3. 防幻觉    → "只基于上下文回答，不知道就说不知道"
  4. 源引用    → 要求标注 [1] [2] 来源编号
  5. 低温度    → temperature 0.1-0.3，减少随机性
```

### 5.3 Context Window 管理与截断策略

```typescript
function truncateContext(
  docs: SearchResult[],
  maxTokens = 3000,
  avgCharsPerToken = 4,
): SearchResult[] {
  const maxChars = maxTokens * avgCharsPerToken;
  const result: SearchResult[] = [];
  let totalChars = 0;

  for (const doc of docs) {
    if (totalChars + doc.text.length > maxChars) {
      // 截断最后一条
      const remaining = maxChars - totalChars;
      if (remaining > 100) {
        result.push({ ...doc, text: doc.text.slice(0, remaining) + '...' });
      }
      break;
    }
    result.push(doc);
    totalChars += doc.text.length;
  }

  return result;
}
```

### 5.4 源文档引用与溯源

```typescript
// 返回带引用的结构化回答
async function queryWithCitations(question: string) {
  const result = await rag.query(question);

  return {
    answer: result.answer,
    citations: result.sources.map((s, i) => ({
      id: i + 1,
      snippet: s.text.slice(0, 200) + '...',
      source: s.source,
      relevance: `${(s.score * 100).toFixed(1)}%`,
    })),
  };
}

// 输出示例：
// {
//   answer: "Node.js 的事件循环分为 6 个阶段 [1]，其中 Timer 阶段处理... [2]",
//   citations: [
//     { id: 1, snippet: "事件循环是 Node.js 的核心...", source: "runtime.pdf", relevance: "92.3%" },
//     { id: 2, snippet: "Timer 阶段执行 setTimeout...", source: "runtime.pdf", relevance: "87.1%" },
//   ]
// }
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Pinecone | 云托管、serverless、免运维、有免费额度 |
| pgvector | PostgreSQL 插件、HNSW 索引、适合已有 PG 的项目 |
| RAG Pipeline | Embed 问题 → 向量检索 → 构建 Prompt → LLM 生成 |
| Prompt 设计 | 角色限定 + 上下文注入 + 防幻觉 + 源引用 |
| 截断策略 | 按 token 预算截断，保证不超 Context Window |

> **下一章**：高级 RAG 策略——HyDE、多路召回、Hybrid Search、对话式 RAG。

---

## 6. 高级 RAG 策略

### 6.1 HyDE：假设性文档嵌入

```
普通 RAG 的问题：

  用户问题："Node.js 怎么处理并发？"
  → Embedding 是"问题"的向量
  → 但向量库里存的是"答案/文档"的向量
  → 问题和答案的语义空间可能不对齐

  HyDE 的解决方案：
  1. 先让 LLM 生成一个"假设性答案"
  2. 用这个假设答案的 Embedding 去检索
  3. 假设答案和真实文档语义更接近 → 检索更准
```

```typescript
async function hydeSearch(question: string) {
  // Step 1: LLM 生成假设性答案
  const hypothetical = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{
      role: 'user',
      content: `请简要回答以下问题（即使你不确定，也请尝试回答）：\n${question}`,
    }],
    temperature: 0.7,
    max_tokens: 200,
  });

  const fakeAnswer = hypothetical.choices[0].message.content!;

  // Step 2: 用假设答案的 Embedding 去检索
  const embedding = await embed(fakeAnswer);
  const docs = await search(embedding, 5);

  return docs;  // 通常比直接用问题检索更准
}
```

### 6.2 多路召回与 Rerank

```
单路检索的问题：

  只用语义检索 → 可能遗漏关键词精确匹配的结果
  只用关键词   → 可能遗漏同义词/近义词

  多路召回 + Rerank：
  1. 语义检索    → Top 20
  2. 关键词检索  → Top 20   → 合并去重 → Rerank → Top 5
  3. 混合得分排序
```

```typescript
async function multiRetrieval(question: string) {
  const embedding = await embed(question);

  // 路径 1：语义检索
  const semanticResults = await search(embedding, 20);

  // 路径 2：关键词检索（PostgreSQL 全文搜索）
  const keywordResults = await pool.query(
    `SELECT content, source, ts_rank(to_tsvector('english', content), plainto_tsquery($1)) AS score
     FROM documents
     WHERE to_tsvector('english', content) @@ plainto_tsquery($1)
     ORDER BY score DESC LIMIT 20`,
    [question]
  );

  // 合并去重
  const merged = mergeAndDeduplicate(
    semanticResults,
    keywordResults.rows,
  );

  // Rerank：用 LLM 重排序
  return await rerank(question, merged, 5);
}

async function rerank(
  question: string,
  docs: SearchResult[],
  topK: number,
): Promise<SearchResult[]> {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{
      role: 'user',
      content: `给以下文档按与问题的相关性打分（1-10）：

问题：${question}

${docs.map((d, i) => `文档${i}: ${d.text.slice(0, 200)}`).join('\n\n')}

返回 JSON 数组：[{ "index": 0, "score": 8 }, ...]`,
    }],
    response_format: { type: 'json_object' },
  });

  const scores = JSON.parse(response.choices[0].message.content!);
  return scores.items
    .sort((a: any, b: any) => b.score - a.score)
    .slice(0, topK)
    .map((s: any) => docs[s.index]);
}
```

### 6.3 Hybrid Search：向量 + 全文检索

```typescript
// pgvector + PostgreSQL 全文搜索的混合查询
async function hybridSearch(
  queryEmbedding: number[],
  queryText: string,
  topK = 5,
  semanticWeight = 0.7,
) {
  const result = await pool.query(
    `WITH semantic AS (
      SELECT id, content, source,
        1 - (embedding <=> $1) AS semantic_score
      FROM documents
      ORDER BY embedding <=> $1
      LIMIT 20
    ),
    keyword AS (
      SELECT id, content, source,
        ts_rank(to_tsvector('english', content), plainto_tsquery($2)) AS keyword_score
      FROM documents
      WHERE to_tsvector('english', content) @@ plainto_tsquery($2)
      LIMIT 20
    )
    SELECT
      COALESCE(s.id, k.id) AS id,
      COALESCE(s.content, k.content) AS content,
      COALESCE(s.source, k.source) AS source,
      (COALESCE(s.semantic_score, 0) * $3 +
       COALESCE(k.keyword_score, 0) * (1 - $3)) AS combined_score
    FROM semantic s
    FULL OUTER JOIN keyword k ON s.id = k.id
    ORDER BY combined_score DESC
    LIMIT $4`,
    [pgvector.toSql(queryEmbedding), queryText, semanticWeight, topK]
  );

  return result.rows;
}
```

```
Hybrid Search 的优势：

  "Node.js 事件循环"
    语义检索 → 找到 "event loop mechanism"（英文同义）
    关键词检索 → 找到 "事件循环" 精确匹配
    
  合并后覆盖面更广，效果优于单一路径
```

### 6.4 对话式 RAG：多轮上下文

```typescript
interface Message {
  role: 'user' | 'assistant';
  content: string;
}

class ConversationalRAG {
  private history: Message[] = [];
  private rag: RAGPipeline;

  constructor(rag: RAGPipeline) {
    this.rag = rag;
  }

  async chat(userMessage: string) {
    // Step 1: 用对话历史改写问题（消除代词）
    const rewrittenQuestion = await this.rewriteQuestion(userMessage);

    // Step 2: 用改写后的问题检索
    const result = await this.rag.query(rewrittenQuestion);

    // Step 3: 保存对话历史
    this.history.push(
      { role: 'user', content: userMessage },
      { role: 'assistant', content: result.answer },
    );

    // 保留最近 10 轮
    if (this.history.length > 20) {
      this.history = this.history.slice(-20);
    }

    return result;
  }

  private async rewriteQuestion(question: string): Promise<string> {
    if (this.history.length === 0) return question;

    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: '将用户的后续问题改写为独立完整的问题。只输出改写后的问题。',
        },
        ...this.history.slice(-6),
        { role: 'user', content: question },
      ],
      temperature: 0,
      max_tokens: 100,
    });

    return response.choices[0].message.content || question;
  }
}

// 使用
const chatRAG = new ConversationalRAG(rag);

await chatRAG.chat('Node.js 的事件循环是什么？');
// → 正常检索 "Node.js 事件循环"

await chatRAG.chat('它有几个阶段？');
// → 改写为 "Node.js 事件循环有几个阶段？" → 检索准确
```

```
对话式 RAG 的核心：

  用户: "Node.js 事件循环是什么？"
  AI:   "事件循环分为 6 个阶段..."

  用户: "它有几个阶段？"      ← "它" 指什么？
  → 改写: "Node.js 事件循环有几个阶段？"  ← 消除代词
  → 用改写后的问题检索 → 检索结果更准
```

---

## 7. 全栈实战：知识库问答应用

### 7.1 后端 API 设计

```bash
npm install hono @hono/node-server openai pg pgvector
```

```typescript
// src/app.ts
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { streamSSE } from 'hono/streaming';

const app = new Hono();
app.use('/*', cors());

// 健康检查
app.get('/health', (c) => c.json({ status: 'ok' }));

// 文档上传
app.post('/api/documents', async (c) => {
  const formData = await c.req.formData();
  const file = formData.get('file') as File;
  const source = formData.get('source') as string || file.name;

  const text = await extractText(file);
  const chunks = recursiveChunk(text, 500);
  const embedded = await embedChunks(chunks);

  for (const item of embedded) {
    await insertChunk(item.text, source, item.embedding);
  }

  return c.json({
    message: `已索引 ${embedded.length} 个文档块`,
    source,
    chunks: embedded.length,
  });
});

// 问答（非流式）
app.post('/api/ask', async (c) => {
  const { question } = await c.req.json();
  const result = await rag.query(question);
  return c.json(result);
});

// 问答（SSE 流式）
app.post('/api/ask/stream', async (c) => {
  const { question } = await c.req.json();

  // 检索
  const queryEmbedding = await embed(question);
  const docs = await search(queryEmbedding, 5);
  const context = docs.map((d, i) =>
    `[${i + 1}] ${d.text}\n来源: ${d.source}`
  ).join('\n\n');

  return streamSSE(c, async (stream) => {
    // 先发送检索到的源文档
    await stream.writeSSE({
      event: 'sources',
      data: JSON.stringify(docs),
    });

    // 流式生成回答
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: buildPrompt(question, context) },
      ],
      stream: true,
      temperature: 0.3,
    });

    for await (const chunk of completion) {
      const content = chunk.choices[0]?.delta?.content;
      if (content) {
        await stream.writeSSE({
          event: 'token',
          data: content,
        });
      }
    }

    await stream.writeSSE({ event: 'done', data: '' });
  });
});

export default app;
```

### 7.2 文档上传与索引管线

```typescript
// src/indexer.ts
async function extractText(file: File): Promise<string> {
  const buffer = Buffer.from(await file.arrayBuffer());
  const name = file.name.toLowerCase();

  if (name.endsWith('.pdf')) {
    const data = await pdfParse(buffer);
    return data.text;
  }

  if (name.endsWith('.md') || name.endsWith('.txt')) {
    return buffer.toString('utf-8');
  }

  throw new Error(`不支持的文件格式: ${name}`);
}

// 完整索引管线
async function indexDocument(file: File, source: string) {
  console.log(`[索引] 开始处理: ${source}`);

  // 1. 提取文本
  const text = await extractText(file);
  console.log(`[索引] 文本长度: ${text.length} 字符`);

  // 2. 分块
  const chunks = recursiveChunk(text, 500);
  console.log(`[索引] 分块数: ${chunks.length}`);

  // 3. 向量化
  const embedded = await embedChunks(chunks);
  console.log(`[索引] 向量化完成`);

  // 4. 存储到向量数据库
  for (const item of embedded) {
    await insertChunk(item.text, source, item.embedding);
  }

  console.log(`[索引] 完成: ${embedded.length} 个块已入库`);
  return { chunks: embedded.length };
}
```

### 7.3 流式问答接口（SSE）

```
SSE 流式响应的数据流：

  POST /api/ask/stream
    ↓
  event: sources
  data: [{"text":"...", "source":"doc.pdf", "score":0.92}]

  event: token
  data: Node.js

  event: token
  data: 的事件循环

  event: token
  data: 分为

  event: token
  data: 6 个阶段 [1]

  event: done
  data:
```

### 7.4 前端 Chat UI 集成

```typescript
// 前端消费 SSE 流
async function askQuestion(question: string) {
  const response = await fetch('/api/ask/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });

  const reader = response.body!
    .pipeThrough(new TextDecoderStream())
    .getReader();

  let answer = '';
  let sources: any[] = [];

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    // 解析 SSE 格式
    const lines = value.split('\n');
    for (const line of lines) {
      if (line.startsWith('event: sources')) {
        const dataLine = lines[lines.indexOf(line) + 1];
        sources = JSON.parse(dataLine.replace('data: ', ''));
        renderSources(sources);
      }
      if (line.startsWith('data: ') && !line.includes('event:')) {
        const token = line.replace('data: ', '');
        answer += token;
        renderAnswer(answer);  // 逐 token 渲染
      }
    }
  }
}

function renderAnswer(text: string) {
  document.getElementById('answer')!.textContent = text;
}

function renderSources(sources: any[]) {
  const list = sources.map(s =>
    `<li>${s.source} (相关度: ${(s.score * 100).toFixed(1)}%)</li>`
  ).join('');
  document.getElementById('sources')!.innerHTML = `<ul>${list}</ul>`;
}
```

---

## 全书总结

```
┌─────────────────────────────────────────────────────────────┐
│         Node.js RAG 全栈应用 · 知识地图                       │
│                                                              │
│  Ch.1  RAG 概念      LLM 幻觉 / Index→Retrieve→Generate     │
│  Ch.2  文档解析       PDF·MD·网页 / 递归分块策略              │
│  Ch.3  Embedding     OpenAI API / Ollama 本地 / 批量优化     │
│  Ch.4  向量数据库     Pinecone 云端 / pgvector 自托管         │
│  Ch.5  RAG Pipeline  完整实现 / Prompt 模板 / 源引用溯源      │
│  Ch.6  高级策略       HyDE / 多路召回 / Hybrid / 对话式 RAG   │
│  Ch.7  全栈实战       Hono API / 文档索引 / SSE 流式 / Chat   │
│                                                              │
│  7 章 25 节，从原理到生产级 RAG 系统完整实战。                │
└─────────────────────────────────────────────────────────────┘
```

> 🎉 **核心链路**：文档 → 分块 → Embedding → 向量库 → 检索 → Prompt → LLM → 流式响应。
