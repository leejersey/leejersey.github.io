# LangChain.js 实战指南

> LangChain.js 是 TypeScript 生态中最全面的 LLM 应用编排框架——从 Prompt 模板到 LCEL 链式组合，从文档加载到 RAG 检索增强，从简单 Tool 到 LangGraph 复杂 Agent，本教程带你从核心概念到生产级应用，掌握 AI 应用开发的"瑞士军刀"。

---

## 1. 为什么选 LangChain.js

"装个 `openai` 包直接调 API 不就行了？" —— 对简单场景确实够用。但当你的需求变成"从 PDF 里提取知识 → 存到向量数据库 → 用户提问时检索相关片段 → 组合成 Prompt → 调模型 → 记住对话历史"——你需要一个编排框架。

### 1.1 LLM 应用 ≠ 调 API

```
一个真实的 AI 应用需要处理的事情：

  裸调 API（你以为的 AI 开发）：
  → openai.chat.completions.create({ messages })
  → 搞定！

  实际的 AI 应用（真实世界）：
  ┌─────────────────────────────────────────────┐
  │ 文档解析 → PDF / Markdown / 网页 / 数据库     │
  │ 文本分割 → 按语义切块，保留元数据              │
  │ 向量化   → Embedding 模型 → 向量数据库         │
  │ 检索     → 相似度搜索 + 重排序 + 过滤           │
  │ 提示工程 → 模板管理 + 变量注入 + Few-shot       │
  │ 模型调用 → 多模型切换 + 流式 + 结构化输出       │
  │ 工具调用 → 搜索 / 计算 / 数据库 / API           │
  │ 记忆管理 → 对话历史 + 摘要 + 持久化             │
  │ 链式编排 → 串联多个步骤 + 条件分支 + 并行       │
  │ 可观测性 → 追踪 / 评估 / 调试 / 成本监控        │
  └─────────────────────────────────────────────┘
  → 每一项都需要标准化的抽象和工具
  → 这就是 LangChain.js 解决的问题
```

### 1.2 LangChain.js 的设计哲学：模块化 + 可组合

```
LangChain.js 的核心设计原则：

  原则 1：模块化
  ─────────────
  → 每个功能独立成包（@langchain/core, @langchain/openai, ...）
  → 按需安装，不引入不需要的依赖
  → 包体积可控

  原则 2：可组合
  ─────────────
  → 所有组件实现统一的 Runnable 接口
  → 可以用管道语法（.pipe()）自由组合
  → prompt.pipe(model).pipe(parser) = 一条链

  原则 3：生态丰富
  ─────────────
  → 150+ 集成（模型 / 向量库 / 工具 / Loader）
  → 社区包 @langchain/community
  → 官方维护的 Provider 包（OpenAI / Anthropic / Google）

  原则 4：渐进式
  ─────────────
  → 简单场景：ChatModel + PromptTemplate
  → 中等场景：LCEL Chain + RAG
  → 复杂场景：LangGraph Agent + 多步编排
```

### 1.3 与 Vercel AI SDK 的分工与协作

```
LangChain.js vs Vercel AI SDK——不是竞争，是互补：

  ┌───────────────────────────────────────────────────┐
  │                  你的 AI 应用                       │
  │                                                    │
  │   前端（React / Next.js）                           │
  │   ├─ useChat / useCompletion  ← Vercel AI SDK     │
  │   └─ 流式渲染 / 消息管理     ← Vercel AI SDK      │
  │                                                    │
  │   后端（Route Handler / API）                       │
  │   ├─ RAG Pipeline           ← LangChain.js        │
  │   ├─ Agent 编排             ← LangGraph.js        │
  │   ├─ Memory 管理            ← LangChain.js        │
  │   └─ streamText / toStream  ← Vercel AI SDK       │
  └───────────────────────────────────────────────────┘

  Vercel AI SDK：
  → 擅长"最后一公里"——模型调用、流式传输、前端渲染
  → 轻量、开箱即用、与 Next.js 深度集成

  LangChain.js：
  → 擅长"编排层"——Chain 组合、RAG、Memory、Agent
  → 生态丰富、高度可扩展、适合复杂管线

  最佳实践：后端用 LangChain.js 编排 → 结果通过 Vercel AI SDK 流式返回前端
```

### 1.4 核心模块概览与包结构

```typescript
// LangChain.js v1 的包结构
// ═══════════════════════════════

// 核心包（必装）
// @langchain/core     → 基础抽象（Runnable / PromptTemplate / Document）

// 模型 Provider（按需装）
// @langchain/openai   → OpenAI / Azure OpenAI
// @langchain/anthropic → Claude 系列
// @langchain/google-vertexai → Gemini

// 社区集成（按需装）
// @langchain/community → 150+ 集成（向量库 / Loader / 工具等）

// Agent 编排（高级场景）
// @langchain/langgraph → 状态图 Agent 编排

// 可观测性
// langsmith           → 追踪 / 评估 / 调试
```

```
安装哪些包？按场景选择：

  场景 1：简单 Chat
  → npm i @langchain/core @langchain/openai

  场景 2：RAG 知识库
  → npm i @langchain/core @langchain/openai
  → npm i @langchain/community  (Loader / VectorStore)

  场景 3：Agent + 工具
  → npm i @langchain/core @langchain/openai
  → npm i @langchain/langgraph  (Agent 编排)

  场景 4：全功能
  → npm i @langchain/core @langchain/openai @langchain/community @langchain/langgraph langsmith
```

---

## 2. 环境准备与第一条 Chain

### 2.1 安装与项目初始化

```bash
# 创建项目
mkdir langchain-demo && cd langchain-demo
npm init -y
npm i typescript tsx @types/node -D
npx tsc --init

# 安装 LangChain.js v1
npm i @langchain/core @langchain/openai
```

```bash
# .env 文件
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1   # 可选：自定义 API 地址
LANGSMITH_API_KEY=ls-your-key                # 可选：启用追踪
LANGSMITH_TRACING=true                       # 可选：启用追踪
```

### 2.2 ChatModel：调用大模型

```typescript
import { ChatOpenAI } from "@langchain/openai";

// 创建模型实例
const model = new ChatOpenAI({
  model: "gpt-4o",
  temperature: 0.7,
  maxTokens: 1024,
  // 如果 .env 设置了 OPENAI_API_KEY，会自动读取
});

// 最简调用：传入字符串
const response = await model.invoke("什么是 TypeScript？");
console.log(response.content);
// → "TypeScript 是 JavaScript 的超集..."

// 传入消息数组（更精确控制）
import { HumanMessage, SystemMessage } from "@langchain/core/messages";

const response2 = await model.invoke([
  new SystemMessage("你是一个 TypeScript 专家，回答简洁。"),
  new HumanMessage("interface 和 type 的区别？"),
]);
console.log(response2.content);
```

### 2.3 PromptTemplate：模板化提示词

```typescript
import { ChatPromptTemplate } from "@langchain/core/prompts";

// 创建提示词模板
const prompt = ChatPromptTemplate.fromMessages([
  ["system", "你是一个 {role}，用 {language} 回答问题。"],
  ["human", "{question}"],
]);

// 格式化模板 → 生成消息数组
const messages = await prompt.invoke({
  role: "资深前端工程师",
  language: "中文",
  question: "React 和 Vue 的区别？",
});
// → [SystemMessage("你是一个资深前端工程师..."), HumanMessage("React 和 Vue...")]

// 也可以直接和模型连接
const response = await model.invoke(messages);
```

### 2.4 第一条 LCEL Chain：prompt | model | parser

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const model = new ChatOpenAI({ model: "gpt-4o" });

const prompt = ChatPromptTemplate.fromMessages([
  ["system", "你是一个翻译专家。将用户输入翻译成 {targetLang}。"],
  ["human", "{text}"],
]);

const parser = new StringOutputParser();   // 把 AIMessage → 纯字符串

// 用 .pipe() 组合成一条链
const chain = prompt.pipe(model).pipe(parser);
//             ↑ 模板    ↑ 模型   ↑ 解析器
//             输入变量 → 消息 → AIMessage → string

// 调用链
const result = await chain.invoke({
  targetLang: "英语",
  text: "LangChain 是一个强大的 AI 编排框架",
});
console.log(result);
// → "LangChain is a powerful AI orchestration framework"

// 流式调用
const stream = await chain.stream({
  targetLang: "日语",
  text: "你好世界",
});
for await (const chunk of stream) {
  process.stdout.write(chunk);  // 逐字输出
}
```

```
LCEL Chain 的数据流：

  invoke({ targetLang: "英语", text: "..." })
       │
       ▼
  PromptTemplate
  → 模板填充 → [SystemMessage, HumanMessage]
       │
       ▼
  ChatOpenAI
  → 调用 GPT-4o → AIMessage { content: "..." }
       │
       ▼
  StringOutputParser
  → 提取 content → "LangChain is a powerful..."
       │
       ▼
  返回纯字符串

  → 每个组件都实现 Runnable 接口
  → .pipe() 把上一个的输出当作下一个的输入
  → 这就是 LCEL 的核心思想
```

---

## 3. LCEL 深度使用：声明式链组合

LCEL（LangChain Expression Language）是 LangChain.js 的灵魂——一切皆 `Runnable`，一切可 `.pipe()`。

### 3.1 管道语法与 Runnable 接口

```typescript
// 所有 LangChain 组件都实现了 Runnable 接口
// Runnable 提供三个核心方法：
//   .invoke(input)  → 单次调用
//   .stream(input)  → 流式输出
//   .batch(inputs)  → 批量调用

// .pipe() 把多个 Runnable 串联成链
const chain = prompt.pipe(model).pipe(parser);

// 等价写法（RunnableSequence）
import { RunnableSequence } from "@langchain/core/runnables";
const chain = RunnableSequence.from([prompt, model, parser]);

// 三种调用方式
const result = await chain.invoke({ text: "hello" });     // 单次
const stream = await chain.stream({ text: "hello" });     // 流式
const results = await chain.batch([                        // 批量
  { text: "hello" },
  { text: "world" },
]);
```

### 3.2 RunnableSequence / RunnableParallel / RunnablePassthrough

```typescript
import {
  RunnableSequence,
  RunnableParallel,
  RunnablePassthrough,
} from "@langchain/core/runnables";

// RunnableParallel：并行执行多个 Runnable
const parallel = RunnableParallel.from({
  translation: translationChain,      // 翻译
  summary: summaryChain,              // 摘要
  sentiment: sentimentChain,          // 情感分析
});

const result = await parallel.invoke({ text: "今天天气真好..." });
// → { translation: "...", summary: "...", sentiment: "positive" }
// → 三条链并行执行，结果合并为一个对象

// RunnablePassthrough：透传输入（常用于保留原始数据）
const chain = RunnableParallel.from({
  context: retriever,                 // 检索上下文
  question: new RunnablePassthrough(),// 透传用户问题
}).pipe(prompt).pipe(model).pipe(parser);
// → 把 "检索到的上下文" 和 "原始问题" 同时传给 Prompt
```

```
RunnableParallel 的数据流：

  输入: { text: "今天天气真好" }
       │
       ├──────────────────┬──────────────────┐
       │                  │                  │
       ▼                  ▼                  ▼
  translationChain    summaryChain     sentimentChain
  → "Nice weather"   → "描述天气"     → "positive"
       │                  │                  │
       └──────────────────┴──────────────────┘
       │
       ▼
  输出: { translation: "...", summary: "...", sentiment: "..." }
```

### 3.3 条件分支：RunnableBranch

```typescript
import { RunnableBranch } from "@langchain/core/runnables";

// 根据输入动态选择不同的 Chain
const branch = RunnableBranch.from([
  // 条件 1：如果是代码问题 → 用 codeChain
  [
    (input: { topic: string }) => input.topic === "code",
    codeChain,
  ],
  // 条件 2：如果是翻译 → 用 translationChain
  [
    (input: { topic: string }) => input.topic === "translation",
    translationChain,
  ],
  // 默认：用通用 Chain
  generalChain,
]);

await branch.invoke({ topic: "code", question: "怎么写快排？" });
// → 自动路由到 codeChain
```

### 3.4 流式输出与批量执行

```typescript
// 流式输出：LCEL 链天然支持流式
const chain = prompt.pipe(model).pipe(parser);

const stream = await chain.stream({
  targetLang: "英语",
  text: "你好",
});

for await (const chunk of stream) {
  process.stdout.write(chunk);
  // → "He" → "llo" → ...
}

// 批量执行（自动并行 + 速率限制）
const results = await chain.batch(
  [
    { targetLang: "英语", text: "你好" },
    { targetLang: "日语", text: "你好" },
    { targetLang: "法语", text: "你好" },
  ],
  { maxConcurrency: 3 },  // 并发数限制
);
// → ["Hello", "こんにちは", "Bonjour"]
```

### 3.5 LCEL 调试与 LangSmith 追踪

```typescript
// 方式 1：给链起名字（方便在 LangSmith 中识别）
const chain = prompt
  .pipe(model)
  .pipe(parser)
  .withConfig({ runName: "TranslationChain" });

// 方式 2：启用 LangSmith 自动追踪
// 设置环境变量即可，不需要改代码：
// LANGSMITH_API_KEY=ls-xxx
// LANGSMITH_TRACING=true

// → 每次调用自动记录到 LangSmith Dashboard
// → 可以看到每个步骤的输入 / 输出 / 延迟 / Token 消耗
```

```
LangSmith 追踪示例：

  TranslationChain (2.3s, 156 tokens)
  ├─ PromptTemplate (0.1ms)
  │  Input:  { targetLang: "英语", text: "你好" }
  │  Output: [SystemMessage, HumanMessage]
  ├─ ChatOpenAI (2.2s, 156 tokens)
  │  Input:  [SystemMessage, HumanMessage]
  │  Output: AIMessage { content: "Hello" }
  └─ StringOutputParser (0.1ms)
     Input:  AIMessage
     Output: "Hello"

  → 每一步的输入输出、耗时、Token 全部可见
  → 这就是 LangSmith 的核心价值
```

---

## 4. 文档加载与文本分割

RAG 的第一步是把数据灌进来——PDF、网页、CSV、Notion……LangChain.js 提供了 50+ Loader，把各种格式统一转成 `Document` 对象。

### 4.1 Document 数据结构与 Loader 体系

```typescript
// Document 是 LangChain 的核心数据结构
import { Document } from "@langchain/core/documents";

const doc = new Document({
  pageContent: "LangChain 是一个 AI 编排框架...",
  metadata: {
    source: "langchain.com",
    page: 1,
    title: "LangChain Introduction",
  },
});
// → pageContent: 文本内容
// → metadata: 元数据（来源、页码、时间等）
// → 所有 Loader 的输出都是 Document[]
```

```
Loader 体系一览：

  文件类 Loader
  ├─ PDFLoader          → PDF 文件（按页分割）
  ├─ TextLoader         → 纯文本文件
  ├─ CSVLoader          → CSV 表格
  ├─ JSONLoader         → JSON 文件（支持 JSONPath）
  └─ DocxLoader         → Word 文档

  网络类 Loader
  ├─ CheerioWebBaseLoader → 网页抓取（轻量级）
  ├─ PlaywrightWebBaseLoader → 动态网页（需要 JS 渲染）
  └─ SitemapLoader      → 批量抓取网站地图

  SaaS 类 Loader
  ├─ NotionAPILoader    → Notion 数据库 / 页面
  ├─ GitbookLoader      → Gitbook 文档
  └─ GithubRepoLoader   → GitHub 仓库文件
```

### 4.2 常用 Loader 实战（PDF / Web / CSV）

```typescript
// PDF 加载
import { PDFLoader } from "@langchain/community/document_loaders/fs/pdf";

const loader = new PDFLoader("./report.pdf", {
  splitPages: true,   // 按页分割（每页一个 Document）
});
const docs = await loader.load();
// → docs[0].pageContent = "第一页内容..."
// → docs[0].metadata = { source: "./report.pdf", page: 1 }

// 网页加载
import { CheerioWebBaseLoader } from "@langchain/community/document_loaders/web/cheerio";

const webLoader = new CheerioWebBaseLoader("https://js.langchain.com/docs/");
const webDocs = await webLoader.load();

// CSV 加载
import { CSVLoader } from "@langchain/community/document_loaders/fs/csv";

const csvLoader = new CSVLoader("./products.csv", {
  column: "description", // 只提取 description 列作为 pageContent
});
const csvDocs = await csvLoader.load();
```

### 4.3 文本分割策略：RecursiveCharacterTextSplitter

```typescript
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";

const splitter = new RecursiveCharacterTextSplitter({
  chunkSize: 500,       // 每块最大 500 字符
  chunkOverlap: 50,     // 块之间重叠 50 字符（保持上下文连贯）
  separators: ["\n\n", "\n", "。", "，", " ", ""],
  // → 优先按段落分割 → 按换行 → 按句号 → 按逗号 → 按空格 → 按字符
});

const splitDocs = await splitter.splitDocuments(docs);
// → 长文档被切成 500 字符的小块
// → metadata 自动继承原文档的元数据
```

```
文本分割的关键参数：

  chunkSize（块大小）
  ──────────────────
  太大（2000+）→ 检索精度低，但保留更多上下文
  太小（100-） → 检索精度高，但可能丢失上下文
  推荐：300-800（取决于 Embedding 模型的上下文窗口）

  chunkOverlap（重叠大小）
  ──────────────────
  太大 → 冗余高，存储浪费
  太小 → 块之间断裂，语义不连贯
  推荐：chunkSize 的 10-20%

  separators（分隔符优先级）
  ──────────────────
  中文推荐：["\n\n", "\n", "。", "！", "？", "，", " ", ""]
  代码推荐：["\nclass ", "\ndef ", "\n\n", "\n", " ", ""]
```

### 4.4 Metadata 管理与自定义 Loader

```typescript
// Metadata 在检索时非常有用——可以过滤、排序、展示来源

// 加载时注入自定义 Metadata
const docs = await loader.load();
const enrichedDocs = docs.map((doc) => ({
  ...doc,
  metadata: {
    ...doc.metadata,
    category: "技术文档",
    importDate: new Date().toISOString(),
    version: "v1.0",
  },
}));

// 自定义 Loader（从数据库加载）
import { BaseDocumentLoader } from "@langchain/core/document_loaders/base";

class DatabaseLoader extends BaseDocumentLoader {
  constructor(private db: any, private tableName: string) { super(); }

  async load(): Promise<Document[]> {
    const rows = await this.db.query(`SELECT * FROM ${this.tableName}`);
    return rows.map((row: any) => new Document({
      pageContent: row.content,
      metadata: { id: row.id, source: this.tableName, createdAt: row.created_at },
    }));
  }
}
```

---

## 5. Embedding 与向量存储

文本分割后的下一步：把文本块转成向量（数字数组），存到向量数据库，然后就能用"语义搜索"找到和用户问题最相关的内容。

### 5.1 Embedding 模型：文本转向量

```typescript
import { OpenAIEmbeddings } from "@langchain/openai";

const embeddings = new OpenAIEmbeddings({
  model: "text-embedding-3-small",    // 推荐：便宜且效果好
  // model: "text-embedding-3-large", // 更高精度，价格更高
});

// 单条文本 → 向量
const vector = await embeddings.embedQuery("什么是 RAG？");
// → [0.012, -0.034, 0.056, ...] （1536 维浮点数数组）

// 批量文本 → 向量
const vectors = await embeddings.embedDocuments([
  "RAG 是检索增强生成",
  "LangChain 是 AI 编排框架",
]);
// → [[0.012, ...], [0.045, ...]]
```

```
Embedding 模型选型：

  模型                        维度    价格         场景
  ─────────────────────────────────────────────────────
  text-embedding-3-small      1536    $0.02/1M     默认推荐
  text-embedding-3-large      3072    $0.13/1M     高精度需求
  本地模型（Ollama）           768+    免费          隐私敏感
  BGE-M3（开源）              1024    免费          中文优化

  → 索引和查询必须用同一个 Embedding 模型！
  → 换模型 = 重建整个向量索引
```

### 5.2 VectorStore 实战（Memory / Pinecone / FAISS）

```typescript
// 方式 1：MemoryVectorStore（内存，适合开发 / 小数据集）
import { MemoryVectorStore } from "langchain/vectorstores/memory";

const vectorStore = await MemoryVectorStore.fromDocuments(
  splitDocs,                          // Document[]
  new OpenAIEmbeddings(),             // Embedding 模型
);

// 相似度搜索
const results = await vectorStore.similaritySearch("RAG 的工作原理", 3);
// → 返回最相似的 3 个 Document
// → results[0].pageContent = "RAG 通过检索外部知识..."
// → results[0].metadata = { source: "...", page: 2 }
```

```typescript
// 方式 2：FAISS（本地持久化，适合中等数据集）
import { FaissStore } from "@langchain/community/vectorstores/faiss";

// 创建并保存
const store = await FaissStore.fromDocuments(splitDocs, embeddings);
await store.save("./faiss_index");

// 加载已有索引
const loadedStore = await FaissStore.load("./faiss_index", embeddings);
```

```typescript
// 方式 3：Pinecone（云端，适合生产大规模数据）
import { PineconeStore } from "@langchain/pinecone";
import { Pinecone } from "@pinecone-database/pinecone";

const pinecone = new Pinecone();
const index = pinecone.index("my-index");

const store = await PineconeStore.fromDocuments(
  splitDocs,
  embeddings,
  { pineconeIndex: index },
);
```

### 5.3 相似度搜索与 MMR 多样性检索

```typescript
// 普通相似度搜索：返回最相似的 K 个
const results = await vectorStore.similaritySearch("问题", 5);

// 带分数的搜索（可以用分数做阈值过滤）
const resultsWithScore = await vectorStore.similaritySearchWithScore("问题", 5);
// → [[Document, 0.95], [Document, 0.87], ...]

// MMR 搜索（Maximum Marginal Relevance）
// → 在"相关性"和"多样性"之间取平衡
// → 避免返回内容高度重复的结果
const mmrResults = await vectorStore.maxMarginalRelevanceSearch("问题", {
  k: 5,              // 返回 5 个
  fetchK: 20,        // 先取 20 个候选
  lambda: 0.5,       // 0=最大多样性，1=最大相关性
});
```

### 5.4 Retriever：从存储到检索接口

```typescript
// Retriever 是 VectorStore 的标准化封装
// → 实现 Runnable 接口 → 可以直接 .pipe() 进 LCEL 链

const retriever = vectorStore.asRetriever({
  k: 4,                              // 返回 4 个结果
  searchType: "mmr",                 // 使用 MMR 搜索
  searchKwargs: { fetchK: 20, lambda: 0.7 },
});

// 直接调用
const docs = await retriever.invoke("什么是 LCEL？");

// 用在 LCEL 链中（RAG 的核心模式）
const chain = RunnableParallel.from({
  context: retriever,                 // 检索相关文档
  question: new RunnablePassthrough(),// 透传用户问题
}).pipe(prompt).pipe(model).pipe(parser);

// → 这就是 RAG Chain 的雏形！下一章详细展开
```

> 💡 **VectorStore 的选择**：开发用 `MemoryVectorStore`（零配置），中等数据用 `FAISS`（本地持久化），生产用 `Pinecone` / `Qdrant` / `Weaviate`（云托管、自动扩展）。

---

## 6. RAG 全流程：检索增强生成

前三章（文档加载 → 文本分割 → Embedding → 向量存储）是 RAG 的"索引管线"。这一章把检索管线补上，完成从问题到答案的闭环。

### 6.1 RAG 双管线架构：索引 + 检索

```
RAG 的完整架构：

  ╔═══════════════════════════════════════════════════╗
  ║              索引管线（离线 / 定时执行）             ║
  ║                                                    ║
  ║   PDF/Web/DB → Loader → Splitter → Embeddings     ║
  ║                                          │         ║
  ║                                          ▼         ║
  ║                                    VectorStore     ║
  ╚═══════════════════════════════════════════════════╝
                                           │
                                           │ 存储
                                           ▼
  ╔═══════════════════════════════════════════════════╗
  ║              检索管线（实时 / 每次请求）             ║
  ║                                                    ║
  ║   用户问题 → Embedding → VectorStore 检索           ║
  ║                              │                     ║
  ║                              ▼                     ║
  ║   相关文档片段 + 用户问题 → Prompt → LLM → 回答     ║
  ╚═══════════════════════════════════════════════════╝
```

### 6.2 RetrievalQA Chain 实战

```typescript
// 完整 RAG Chain（用 LCEL 手动组合）
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnablePassthrough, RunnableParallel } from "@langchain/core/runnables";

const model = new ChatOpenAI({ model: "gpt-4o" });
const retriever = vectorStore.asRetriever({ k: 4 });

// RAG Prompt 模板
const ragPrompt = ChatPromptTemplate.fromMessages([
  ["system", `你是一个知识库问答助手。根据以下检索到的上下文回答问题。
如果上下文中没有相关信息，请说"我没有找到相关信息"。

上下文：
{context}`],
  ["human", "{question}"],
]);

// 格式化检索结果
function formatDocs(docs: Document[]): string {
  return docs.map((doc, i) =>
    `[${i + 1}] ${doc.pageContent}\n来源：${doc.metadata.source}`
  ).join("\n\n");
}

// 组装 RAG Chain
const ragChain = RunnableParallel.from({
  context: retriever.pipe(formatDocs),    // 检索 → 格式化
  question: new RunnablePassthrough(),    // 透传问题
})
  .pipe(ragPrompt)                        // 填充模板
  .pipe(model)                            // 调用模型
  .pipe(new StringOutputParser());        // 提取文本

// 使用
const answer = await ragChain.invoke("LangChain 的 LCEL 是什么？");
// → "LCEL（LangChain Expression Language）是 LangChain 的声明式链组合语法..."
```

### 6.3 Conversational RAG：带对话历史的问答

```typescript
// 带对话历史的 RAG（用户可以追问）
import { MessagesPlaceholder } from "@langchain/core/prompts";

// 步骤 1：重写问题（把追问转化为独立问题）
const contextualizePrompt = ChatPromptTemplate.fromMessages([
  ["system", `根据对话历史，将用户的最新问题重写为一个独立的、完整的问题。
不要回答问题，只重写。如果已经是独立问题，直接返回。`],
  new MessagesPlaceholder("chatHistory"),
  ["human", "{question}"],
]);

const contextualizeChain = contextualizePrompt
  .pipe(model)
  .pipe(new StringOutputParser());

// 步骤 2：用重写后的问题检索 + 回答
const conversationalRagChain = RunnableSequence.from([
  // 先重写问题
  {
    question: contextualizeChain,
    chatHistory: (input) => input.chatHistory,
  },
  // 再用 RAG 回答
  {
    context: (input) => retriever.invoke(input.question).then(formatDocs),
    question: (input) => input.question,
  },
  ragPrompt,
  model,
  new StringOutputParser(),
]);

// 使用
const answer1 = await conversationalRagChain.invoke({
  question: "LCEL 是什么？",
  chatHistory: [],
});
// → "LCEL 是 LangChain Expression Language..."

const answer2 = await conversationalRagChain.invoke({
  question: "它支持流式输出吗？",   // "它" 指 LCEL
  chatHistory: [
    new HumanMessage("LCEL 是什么？"),
    new AIMessage(answer1),
  ],
});
// → 先重写问题："LCEL 是否支持流式输出？"
// → 再检索 + 回答
```

### 6.4 RAG 质量优化：Reranking / HyDE / 多查询

```
RAG 质量优化三板斧：

  策略 1：多查询检索（Multi-Query Retriever）
  ──────────────────────────────────────────
  用户问题 → LLM 生成 3 个不同角度的查询
  → 分别检索 → 合并去重 → 覆盖更多相关内容
  → 解决：单一查询可能漏掉相关文档

  策略 2：HyDE（Hypothetical Document Embeddings）
  ──────────────────────────────────────────
  用户问题 → LLM 先生成一个"假设性答案"
  → 用这个假设性答案做 Embedding 检索
  → 解决：问题和文档的表述差异（query-document gap）

  策略 3：Reranking（重排序）
  ──────────────────────────────────────────
  检索 Top-20 → 用 Reranker 模型精排 → 取 Top-5
  → 第一阶段用 Embedding 粗排（快但不精确）
  → 第二阶段用 Cross-Encoder 精排（慢但精确）
  → 解决：Embedding 相似度不等于真正的相关性
```

> 💡 **RAG 的核心心智模型**：不要让 LLM 靠"记忆"回答——让它靠"阅读检索到的资料"回答。你的系统越像一个"开卷考试"，幻觉就越少。

---

## 7. Memory：对话记忆管理

LLM 天生没有记忆——每次调用都是独立的。Memory 模块帮你管理对话历史，让 AI 记住上下文。

### 7.1 Memory 类型全解析

```
LangChain.js 的 Memory 类型：

  BufferMemory（全量缓存）
  ──────────────────────
  → 存储完整的对话历史
  → 优点：不丢信息
  → 缺点：对话长了会超 Token 限制
  → 适合：短对话（< 20 轮）

  BufferWindowMemory（滑动窗口）
  ──────────────────────
  → 只保留最近 K 轮对话
  → 优点：Token 可控
  → 缺点：早期对话会丢失
  → 适合：客服、闲聊

  ConversationSummaryMemory（摘要记忆）
  ──────────────────────
  → 用 LLM 对历史对话做摘要
  → 优点：信息密度高，Token 少
  → 缺点：摘要可能丢失细节，额外 LLM 调用
  → 适合：长对话、复杂上下文
```

### 7.2 Memory 与 Chain 的集成

```typescript
// 在 LCEL 中手动管理对话历史（推荐方式）
import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";
import { ChatOpenAI } from "@langchain/openai";
import { HumanMessage, AIMessage, BaseMessage } from "@langchain/core/messages";

const prompt = ChatPromptTemplate.fromMessages([
  ["system", "你是一个有帮助的 AI 助手。"],
  new MessagesPlaceholder("history"),   // 对话历史占位
  ["human", "{input}"],
]);

const model = new ChatOpenAI({ model: "gpt-4o" });
const chain = prompt.pipe(model);

// 手动管理历史消息
const chatHistory: BaseMessage[] = [];

async function chat(userInput: string) {
  const response = await chain.invoke({
    input: userInput,
    history: chatHistory,
  });

  // 追加到历史
  chatHistory.push(new HumanMessage(userInput));
  chatHistory.push(new AIMessage(response.content as string));

  return response.content;
}

await chat("我叫张三");        // → "你好张三！"
await chat("我叫什么？");      // → "你叫张三。" ← 记住了！
```

### 7.3 持久化 Memory：Redis / 数据库

```typescript
// 把对话历史存到数据库（跨请求 / 跨会话保持）
class DatabaseChatHistory {
  constructor(private db: any, private sessionId: string) {}

  async getMessages(): Promise<BaseMessage[]> {
    const rows = await this.db.message.findMany({
      where: { sessionId: this.sessionId },
      orderBy: { createdAt: "asc" },
    });
    return rows.map((r: any) =>
      r.role === "human"
        ? new HumanMessage(r.content)
        : new AIMessage(r.content)
    );
  }

  async addMessage(message: BaseMessage) {
    await this.db.message.create({
      data: {
        sessionId: this.sessionId,
        role: message._getType(),
        content: message.content as string,
        createdAt: new Date(),
      },
    });
  }
}

// 使用
const history = new DatabaseChatHistory(db, "session-123");
const pastMessages = await history.getMessages();

const response = await chain.invoke({
  input: "继续我们上次的对话",
  history: pastMessages,
});
await history.addMessage(new HumanMessage("继续我们上次的对话"));
await history.addMessage(new AIMessage(response.content as string));
```

### 7.4 记忆优化：滑动窗口与自动摘要

```typescript
// 策略 1：滑动窗口（只保留最近 N 轮）
function getRecentHistory(history: BaseMessage[], maxRounds: number) {
  const maxMessages = maxRounds * 2;  // 每轮 = 1 human + 1 ai
  return history.slice(-maxMessages);
}

// 策略 2：自动摘要（历史太长时压缩）
async function summarizeIfNeeded(
  history: BaseMessage[],
  model: ChatOpenAI,
  maxTokens: number = 2000,
) {
  const totalLength = history.reduce((sum, m) =>
    sum + (m.content as string).length, 0
  );

  if (totalLength < maxTokens) return history;

  // 太长了 → 用 LLM 生成摘要
  const summaryResponse = await model.invoke([
    new SystemMessage("将以下对话历史压缩为一段简洁的摘要，保留关键信息。"),
    ...history,
  ]);

  return [new SystemMessage(`之前的对话摘要：${summaryResponse.content}`)];
}
```

> 💡 **Memory 的选择**：大多数场景用"手动管理 `BaseMessage[]`  + 持久化到数据库"就够了。`BufferMemory` 等封装类适合快速原型，生产环境建议自己控制。

---

## 8. Tool 与 Agent：让 LLM 使用工具

Chain 按预设步骤执行，Agent 自己决定下一步——根据用户的意图动态选择调用哪些工具、传什么参数、循环几次。

### 8.1 Tool 定义：DynamicTool 与 StructuredTool

```typescript
import { DynamicTool, DynamicStructuredTool } from "@langchain/core/tools";
import { z } from "zod";

// DynamicTool：简单工具（单个字符串输入）
const searchTool = new DynamicTool({
  name: "web_search",
  description: "搜索互联网获取最新信息。输入搜索关键词。",
  func: async (query: string) => {
    const results = await fetch(`https://api.search.com?q=${query}`);
    return JSON.stringify(await results.json());
  },
});

// DynamicStructuredTool：结构化工具（多个参数 + Zod 类型安全）
const calculatorTool = new DynamicStructuredTool({
  name: "calculator",
  description: "执行数学计算",
  schema: z.object({
    expression: z.string().describe("数学表达式，如 '2 + 3 * 4'"),
  }),
  func: async ({ expression }) => {
    const result = Function(`return ${expression}`)();
    return `${expression} = ${result}`;
  },
});

// tool() 函数式写法（更简洁，推荐）
import { tool } from "@langchain/core/tools";

const weatherTool = tool(
  async ({ city }) => {
    return JSON.stringify({ city, temp: 28, condition: "晴" });
  },
  {
    name: "get_weather",
    description: "获取城市天气",
    schema: z.object({
      city: z.string().describe("城市名称"),
    }),
  }
);
```

### 8.2 AgentExecutor：驱动 Agent 循环

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { createReactAgent } from "@langchain/langgraph/prebuilt";

const model = new ChatOpenAI({ model: "gpt-4o" });

// 创建 ReAct Agent（推荐方式，基于 LangGraph）
const agent = createReactAgent({
  llm: model,
  tools: [searchTool, calculatorTool, weatherTool],
});

// 调用 Agent
const result = await agent.invoke({
  messages: [{ role: "user", content: "北京今天天气怎么样？如果温度超过 30 度，帮我算一下需要多少瓶水（每人每小时 0.5 瓶，3 人 4 小时）" }],
});

// Agent 自动执行：
// Step 1: 调用 get_weather({ city: "北京" }) → { temp: 28 }
// Step 2: 28 < 30，不需要计算
// Step 3: 生成最终回答："北京 28°C，没有超过 30 度，不需要额外补水。"
```

```
Agent 的执行循环：

  用户输入
       │
       ▼
  ┌─────────────┐
  │ LLM 思考     │ ← "需要查天气"
  └──────┬──────┘
         │ tool_call
         ▼
  ┌─────────────┐
  │ 执行 Tool    │ ← get_weather("北京")
  └──────┬──────┘
         │ tool_result
         ▼
  ┌─────────────┐
  │ LLM 思考     │ ← "28°C 没超过 30，不需要算"
  └──────┬──────┘
         │ 决定结束
         ▼
  最终回答
```

### 8.3 ReAct Agent 模式详解

```
ReAct（Reasoning + Acting）模式：

  模型的思考过程：
  ──────────────────────────────
  Thought: 用户问北京天气，我需要调用天气工具
  Action:  get_weather
  Action Input: { "city": "北京" }
  Observation: { "temp": 28, "condition": "晴" }
  
  Thought: 温度 28°C 没超过 30°C，不需要计算
  Final Answer: 北京今天 28°C，晴天。温度未超过 30°C...

  ReAct 的核心：
  → Thought: 模型先"想"（推理）
  → Action:  再"做"（调用工具）
  → Observation: 看结果
  → 循环直到能给出 Final Answer

  → 这比直接让模型调用工具更可靠
  → 因为模型会先推理"是否需要工具"、"用哪个工具"
```

### 8.4 自定义 Tool 开发实战

```typescript
// 实战：数据库查询工具
const dbQueryTool = tool(
  async ({ sql }) => {
    // 安全检查：只允许 SELECT
    if (!sql.trim().toUpperCase().startsWith("SELECT")) {
      return "错误：只允许 SELECT 查询";
    }
    const results = await db.raw(sql);
    return JSON.stringify(results.rows.slice(0, 10)); // 最多 10 条
  },
  {
    name: "query_database",
    description: "查询 PostgreSQL 数据库。只支持 SELECT 语句。",
    schema: z.object({
      sql: z.string().describe("SQL 查询语句（仅限 SELECT）"),
    }),
  }
);

// 实战：文件读写工具
const readFileTool = tool(
  async ({ path }) => {
    const content = await fs.readFile(path, "utf-8");
    return content.slice(0, 5000);  // 限制返回长度
  },
  {
    name: "read_file",
    description: "读取本地文件内容",
    schema: z.object({
      path: z.string().describe("文件路径"),
    }),
  }
);
```

> 💡 **Tool 的 description 决定一切**：Agent 根据 description 判断何时使用哪个 Tool。写清楚"这个工具做什么、输入什么、限制什么"——就像给新同事写工具说明书。

---

## 9. LangGraph.js：复杂 Agent 编排

`createReactAgent` 够用了吗？简单场景够了。但当你需要条件分支、并行执行、人工审批、多 Agent 协作——你需要 LangGraph。

### 9.1 为什么需要 LangGraph

```
普通 Agent 的局限：

  createReactAgent：
  → 线性循环：思考 → 工具 → 思考 → 工具 → 结束
  → 没有条件分支（不能"如果 A 则走路径 1，否则走路径 2"）
  → 没有并行执行（不能同时调用多个工具链）
  → 没有状态持久化（重启就丢失）
  → 没有人工审批节点

  LangGraph 的解决方案：
  → 用"图"（Graph）建模 Agent 的执行流程
  → 节点（Node）= 一个执行步骤
  → 边（Edge）= 步骤之间的连接（可以有条件）
  → 状态（State）= 贯穿整个流程的共享数据
```

### 9.2 Graph 核心概念：Node / Edge / State

```typescript
import { StateGraph, Annotation, START, END } from "@langchain/langgraph";

// 1. 定义 State（图的共享状态）
const AgentState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (prev, next) => [...prev, ...next], // 消息追加
  }),
  currentStep: Annotation<string>(),
});

// 2. 定义 Node（图的节点 = 执行步骤）
async function analyzeNode(state: typeof AgentState.State) {
  const response = await model.invoke(state.messages);
  return { messages: [response], currentStep: "analyzed" };
}

async function toolNode(state: typeof AgentState.State) {
  // 执行工具调用...
  return { messages: [toolResult] };
}

// 3. 构建 Graph
const graph = new StateGraph(AgentState)
  .addNode("analyze", analyzeNode)
  .addNode("tools", toolNode)
  .addEdge(START, "analyze")           // 开始 → 分析
  .addConditionalEdges("analyze", (state) => {
    // 条件路由：有工具调用 → tools，否则 → 结束
    const lastMsg = state.messages[state.messages.length - 1];
    return lastMsg.tool_calls?.length ? "tools" : END;
  })
  .addEdge("tools", "analyze")         // 工具结果 → 回到分析
  .compile();

// 4. 执行
const result = await graph.invoke({
  messages: [new HumanMessage("搜索 LangGraph 的最新特性")],
});
```

```
LangGraph 的执行流程图：

  START
    │
    ▼
  ┌──────────┐
  │ analyze  │ ← LLM 分析 / 思考
  └────┬─────┘
       │
       ├── 有 tool_calls ──► ┌──────────┐
       │                     │  tools   │ ← 执行工具
       │                     └────┬─────┘
       │                          │
       │                          └─── 回到 analyze
       │
       └── 无 tool_calls ──► END（输出最终回答）
```

### 9.3 构建第一个 Graph Agent

```typescript
// 完整的 LangGraph Agent（带工具 + 条件路由）
import { StateGraph, Annotation, START, END } from "@langchain/langgraph";
import { ToolNode } from "@langchain/langgraph/prebuilt";
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({ model: "gpt-4o" }).bindTools(tools);

const AgentState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (prev, next) => [...prev, ...next],
  }),
});

// LLM 节点
async function callModel(state: typeof AgentState.State) {
  const response = await model.invoke(state.messages);
  return { messages: [response] };
}

// 路由函数
function shouldContinue(state: typeof AgentState.State) {
  const lastMsg = state.messages[state.messages.length - 1];
  return lastMsg.tool_calls?.length ? "tools" : END;
}

// 构建图
const app = new StateGraph(AgentState)
  .addNode("agent", callModel)
  .addNode("tools", new ToolNode(tools))
  .addEdge(START, "agent")
  .addConditionalEdges("agent", shouldContinue)
  .addEdge("tools", "agent")
  .compile();

const result = await app.invoke({
  messages: [new HumanMessage("帮我查北京天气，然后计算出行所需水量")],
});
```

### 9.4 条件路由与 Human-in-the-Loop

```typescript
// Human-in-the-Loop：某些步骤需要人工审批
const graph = new StateGraph(AgentState)
  .addNode("plan", planNode)         // AI 生成计划
  .addNode("approve", approveNode)   // 人工审批
  .addNode("execute", executeNode)   // 执行计划
  .addEdge(START, "plan")
  .addEdge("plan", "approve")
  .addConditionalEdges("approve", (state) => {
    return state.approved ? "execute" : "plan"; // 拒绝 → 重新规划
  })
  .addEdge("execute", END)
  .compile({
    checkpointer: new MemorySaver(),  // 状态持久化（等待人工审批时不丢失）
  });

// 执行到 approve 节点时会暂停，等待人工输入
const thread = { configurable: { thread_id: "task-1" } };
const state1 = await graph.invoke({ messages: [...] }, thread);
// → 暂停在 approve 节点

// 人工审批后恢复
await graph.invoke({ approved: true }, thread);
// → 继续执行 execute 节点
```

### 9.5 多 Agent 协作编排

```typescript
// 多 Agent 协作：Supervisor 分发任务给专业 Agent
const supervisorGraph = new StateGraph(AgentState)
  .addNode("supervisor", async (state) => {
    // Supervisor 决定下一步由谁执行
    const decision = await supervisorModel.invoke(state.messages);
    return { messages: [decision], nextAgent: decision.next };
  })
  .addNode("researcher", researcherAgent)
  .addNode("coder", coderAgent)
  .addNode("writer", writerAgent)
  .addEdge(START, "supervisor")
  .addConditionalEdges("supervisor", (state) => {
    return state.nextAgent; // "researcher" | "coder" | "writer" | END
  })
  .addEdge("researcher", "supervisor")  // 完成后回到 Supervisor
  .addEdge("coder", "supervisor")
  .addEdge("writer", "supervisor")
  .compile();
```

```
多 Agent 协作架构：

  START → Supervisor
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
  Researcher  Coder   Writer
    │        │        │
    └────────┴────────┘
             │
             ▼
         Supervisor → END（所有任务完成）
```

> 💡 **LangGraph vs 普通 Agent**：如果你的 Agent 只需要"思考 → 工具 → 回答"，用 `createReactAgent` 就够了。如果你需要条件分支、人工审批、多 Agent 协作、状态持久化——用 LangGraph。

---

## 10. 生产部署与最佳实践

框架跑通只是起点——生产环境需要可观测性、与前端集成、性能调优和健壮的错误处理。

### 10.1 LangSmith：追踪、评估与调试

```
LangSmith 是 LangChain 的可观测性平台：

  1. 追踪（Tracing）
  ─────────────────
  → 自动记录每条 Chain / Agent 的完整执行链路
  → 每个节点的输入 / 输出 / 延迟 / Token 消耗
  → 只需设置环境变量，代码零修改

  2. 评估（Evaluation）
  ─────────────────
  → 创建测试数据集（问题 + 期望答案）
  → 自动运行 Chain 并对比结果
  → 支持 LLM 自动评分（正确性、相关性、忠实度）

  3. 数据集（Datasets）
  ─────────────────
  → 收集生产环境的真实请求
  → 标注好/坏案例
  → 用于回归测试和持续优化
```

```bash
# 启用 LangSmith（只需要环境变量）
LANGSMITH_API_KEY=ls-your-key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=my-ai-app     # 项目名

# → 所有 LangChain 调用自动上报到 LangSmith Dashboard
# → 零代码修改！
```

### 10.2 与 Vercel AI SDK 集成

```typescript
// 最佳实践：后端用 LangChain 编排，前端用 Vercel AI SDK 渲染
// app/api/chat/route.ts

import { LangChainAdapter } from "ai";
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

export async function POST(req: Request) {
  const { messages } = await req.json();
  const lastMessage = messages[messages.length - 1].content;

  // LangChain 编排
  const model = new ChatOpenAI({ model: "gpt-4o", streaming: true });
  const prompt = ChatPromptTemplate.fromMessages([
    ["system", "你是一个有帮助的 AI 助手。"],
    ["human", "{input}"],
  ]);
  const chain = prompt.pipe(model).pipe(new StringOutputParser());

  // 用 LangChainAdapter 把 LangChain 流转换为 Vercel AI SDK 流
  const stream = await chain.stream({ input: lastMessage });

  return LangChainAdapter.toDataStreamResponse(stream);
}
```

```typescript
// 前端：标准 Vercel AI SDK useChat
"use client";
import { useChat } from "ai/react";

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit } = useChat();

  return (
    <div>
      {messages.map((m) => (
        <div key={m.id}>{m.role}: {m.content}</div>
      ))}
      <form onSubmit={handleSubmit}>
        <input value={input} onChange={handleInputChange} />
      </form>
    </div>
  );
}
```

```
LangChain + Vercel AI SDK 集成架构：

  前端（React）                后端（Route Handler）
  ─────────────               ────────────────────
  useChat() ──HTTP POST──►  接收 messages
                              │
                              ▼
                            LangChain Chain/Agent
                            (RAG / Memory / Tools)
                              │
                              ▼
                            chain.stream()
                              │
                              ▼
  流式渲染 ◄──SSE 流──── LangChainAdapter.toDataStreamResponse()
```

### 10.3 性能优化：缓存、并行与 Token 控制

```typescript
// 策略 1：语义缓存（相似问题命中缓存，跳过 LLM 调用）
import { CacheBackedEmbeddings } from "langchain/embeddings/cache_backed";
import { InMemoryStore } from "@langchain/core/stores";

const cache = new InMemoryStore();
const cachedEmbeddings = CacheBackedEmbeddings.fromBytesStore(
  new OpenAIEmbeddings(),
  cache,
  { namespace: "embeddings" },
);
// → 相同文本不会重复调用 Embedding API

// 策略 2：并行执行（RunnableParallel）
const parallel = RunnableParallel.from({
  answer: ragChain,
  relatedQuestions: suggestChain,
});
// → 两条链同时执行，总耗时 = max(a, b) 而非 a + b

// 策略 3：Token 控制
const model = new ChatOpenAI({
  model: "gpt-4o",
  maxTokens: 2048,          // 限制输出长度
});
// → 对话历史用滑动窗口截断（第 7 章）
// → 检索结果用 Top-K 限制（第 5 章）
```

### 10.4 错误处理与重试策略

```typescript
// LangChain 内置的重试与 Fallback 机制

// 方式 1：带重试的模型调用
const modelWithRetry = model.withRetry({
  stopAfterAttempt: 3,        // 最多重试 3 次
});

// 方式 2：Fallback（主模型失败时自动切换备用模型）
const modelWithFallback = model.withFallbacks({
  fallbacks: [
    new ChatOpenAI({ model: "gpt-4o-mini" }),  // 备用 1
  ],
});

// 方式 3：在 Chain 中捕获错误
import { RunnableLambda } from "@langchain/core/runnables";

const safeChain = RunnableLambda.from(async (input) => {
  try {
    return await riskyChain.invoke(input);
  } catch (error) {
    console.error("Chain 执行失败:", error);
    return "抱歉，处理您的请求时遇到了问题。请稍后再试。";
  }
});
```

### 10.5 常见问题与 FAQ

```
Q1: @langchain/core 版本冲突怎么办？
─────────────────────────────────────
→ @langchain/core 是 peer dependency
→ 确保所有 @langchain/* 包使用同一版本的 @langchain/core
→ 检查：npm ls @langchain/core

Q2: 流式输出在 Vercel 部署后卡住？
─────────────────────────────────────
→ 确保 Route Handler 返回的是流式 Response
→ 使用 LangChainAdapter.toDataStreamResponse()
→ 检查是否有中间件缓冲了响应

Q3: RAG 检索结果不相关？
─────────────────────────────────────
→ 检查 chunkSize 是否合适（太大/太小都不行）
→ 试试 MMR 搜索增加多样性
→ 检查 Embedding 模型是否适合你的语言（中文用 BGE-M3）
→ 考虑 Reranking 精排

Q4: Agent 陷入无限循环？
─────────────────────────────────────
→ LangGraph 的 createReactAgent 有内置 recursionLimit（默认 25）
→ 检查 Tool 是否返回了有用的结果
→ 检查 system prompt 是否引导 Agent 在合适时机停止

Q5: LangChain.js vs LangChain Python 的差异？
─────────────────────────────────────
→ API 基本一致，但 JS 版不是 Python 版的 1:1 移植
→ JS 版更强调 TypeScript 类型安全
→ 某些集成 JS 版可能滞后
→ LangGraph.js 和 LangGraph Python 功能基本对齐

Q6: 何时该用 LangChain，何时不该？
─────────────────────────────────────
→ 该用：RAG、Agent、复杂 Chain 编排、多步工作流
→ 不该用：简单的单次 API 调用（直接用 openai 包或 Vercel AI SDK）
→ 核心原则：框架应该减少复杂度，不应该增加
```

---
