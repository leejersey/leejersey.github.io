# Agent 监控与可观测性

> Langfuse / LangSmith / Arize 三大平台对比——Trace 链路追踪、Token 成本归因、质量评估告警、多 Agent 调试，构建 LLM 应用的"DevOps"体系。

---

## 1. 为什么 LLM 应用需要可观测性

### 1.1 LLM 应用的三大黑盒问题

```
传统 Web 应用 vs LLM 应用的监控差异：

  传统应用：
    输入确定 → 逻辑确定 → 输出确定
    监控关注：延迟、错误率、QPS
    出 Bug：看日志 + 堆栈 → 定位

  LLM 应用：
    输入确定 → 但 LLM 输出不确定 → 结果可能正确也可能幻觉
    监控关注：延迟 + 错误率 + 质量 + 成本 + Token 用量
    出 Bug：Prompt 改了一个字 → 全部输出变了 → 怎么定位？

  三大黑盒：
  1. 质量黑盒  → 回答正确率？幻觉率？
  2. 成本黑盒  → 每个用户花了多少 Token？哪个功能最烧钱？
  3. 链路黑盒  → Agent 为什么选了这个 Tool？中间推理步骤是什么？
```

### 1.2 可观测性三支柱：Trace / Metrics / Evaluation

```
LLM 可观测性三支柱：

  ┌─────────────────────────────────────────────┐
  │              可观测性平台                     │
  │                                              │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
  │  │  Trace   │ │ Metrics  │ │Evaluation│    │
  │  │ 链路追踪 │ │ 指标监控 │ │ 质量评估 │    │
  │  ├──────────┤ ├──────────┤ ├──────────┤    │
  │  │ 每次请求 │ │ 聚合统计 │ │ 质量打分 │    │
  │  │ 的完整   │ │ 延迟/成本│ │ 正确/幻觉│    │
  │  │ 调用链   │ │ Token量  │ │ 相关性   │    │
  │  └──────────┘ └──────────┘ └──────────┘    │
  │       ↓            ↓            ↓           │
  │   调试定位      趋势告警     质量回归检测     │
  └─────────────────────────────────────────────┘
```

| 支柱 | 回答的问题 | 粒度 |
|---|---|---|
| **Trace** | 这次请求经历了哪些步骤？ | 单次请求 |
| **Metrics** | 过去 24h 平均延迟多少？成本多少？ | 聚合统计 |
| **Evaluation** | 回答质量如何？幻觉率多少？ | 批量评估 |

### 1.3 监控平台选型总览

| | Langfuse | LangSmith | Arize Phoenix |
|---|---|---|---|
| **开源** | ✅ 完全开源 | ❌ 闭源 | ✅ 开源 |
| **自托管** | ✅ Docker 一键部署 | ❌ 仅云端 | ✅ |
| **定价** | 免费额度 + 付费 | 免费额度 + 付费 | 开源免费 |
| **SDK** | Python / JS / API | Python（LangChain） | Python |
| **Trace** | ✅ | ✅ | ✅ |
| **Prompt 管理** | ✅ | ✅ Hub | ❌ |
| **评估** | ✅ 内置 | ✅ 强大 | ✅ 强大 |
| **推荐** | 通用首选 ✅ | LangChain 用户 | ML 团队 |

---

## 2. Trace 链路追踪：看清每一步

### 2.1 Trace 与 Span：LLM 调用的"调用栈"

```
一个 RAG 问答请求的 Trace：

  Trace: "用户问：Node.js 事件循环是什么？"
  │
  ├─ Span: embedding (42ms, 15 tokens)
  │   └─ OpenAI text-embedding-3-small
  │
  ├─ Span: retrieval (28ms)
  │   └─ pgvector 检索 Top-5
  │
  ├─ Span: generation (1.2s, 580 tokens)
  │   ├─ Model: gpt-4o-mini
  │   ├─ Input: System Prompt + Context + Question
  │   └─ Output: "Node.js 事件循环分为 6 个阶段..."
  │
  └─ 总耗时: 1.27s | 总 Token: 595 | 成本: $0.0004

  一个 Agent 请求的 Trace（更复杂）：

  Trace: "帮我查询北京明天天气并发邮件提醒"
  │
  ├─ Span: planning (800ms, 200 tokens)
  │   └─ LLM 决定调用哪些 Tool
  │
  ├─ Span: tool_call - weather_api (350ms)
  │   └─ 返回：北京，晴，25°C
  │
  ├─ Span: tool_call - send_email (1.2s)
  │   └─ 发送给 user@example.com
  │
  └─ Span: summarize (600ms, 150 tokens)
      └─ LLM 生成最终回复
```

### 2.2 手动 Trace 埋点

```typescript
// 不依赖任何平台的手动 Trace 实现
interface Span {
  name: string;
  startTime: number;
  endTime?: number;
  metadata: Record<string, any>;
  children: Span[];
}

class Tracer {
  private root: Span;
  private stack: Span[] = [];

  constructor(name: string) {
    this.root = { name, startTime: Date.now(), metadata: {}, children: [] };
    this.stack.push(this.root);
  }

  startSpan(name: string, metadata: Record<string, any> = {}): void {
    const span: Span = { name, startTime: Date.now(), metadata, children: [] };
    this.stack[this.stack.length - 1].children.push(span);
    this.stack.push(span);
  }

  endSpan(metadata: Record<string, any> = {}): void {
    const span = this.stack.pop()!;
    span.endTime = Date.now();
    Object.assign(span.metadata, metadata);
  }

  end(): Span {
    this.root.endTime = Date.now();
    return this.root;
  }
}

// 使用
const tracer = new Tracer('rag-query');

tracer.startSpan('embedding', { model: 'text-embedding-3-small' });
const embedding = await embed(question);
tracer.endSpan({ tokens: 15, durationMs: 42 });

tracer.startSpan('retrieval', { engine: 'pgvector' });
const docs = await search(embedding, 5);
tracer.endSpan({ resultCount: docs.length });

tracer.startSpan('generation', { model: 'gpt-4o-mini' });
const answer = await llm.generate(prompt);
tracer.endSpan({ inputTokens: 400, outputTokens: 180 });

const trace = tracer.end();
console.log(JSON.stringify(trace, null, 2));
// → 发送到监控平台
```

### 2.3 自动 Trace（SDK 集成）

```typescript
// OpenAI SDK + Langfuse 自动追踪
import { observeOpenAI } from 'langfuse';
import OpenAI from 'openai';

const openai = observeOpenAI(new OpenAI(), {
  clientInitParams: {
    publicKey: process.env.LANGFUSE_PUBLIC_KEY,
    secretKey: process.env.LANGFUSE_SECRET_KEY,
    baseUrl: 'https://cloud.langfuse.com',
  },
});

// 正常使用 OpenAI SDK——Langfuse 自动记录每次调用
const result = await openai.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: '什么是事件循环？' }],
});
// → Langfuse 自动记录：模型、Prompt、输出、Token、延迟
```

---

## 3. Langfuse：开源首选

### 3.1 Langfuse 核心概念与架构

```
Langfuse 数据模型：

  Project
  └─ Trace（一次用户请求）
      ├─ Span（通用操作，如检索、预处理）
      ├─ Generation（LLM 调用，自动记录 Token/成本）
      ├─ Event（自定义事件，如用户反馈）
      └─ Score（质量评分）

  额外功能：
  ├─ Prompt Management（版本化 Prompt 管理）
  ├─ Dataset（评估数据集）
  └─ Dashboard（可视化仪表盘）
```

### 3.2 SDK 集成（Python / TypeScript）

```bash
npm install langfuse
```

```typescript
import { Langfuse } from 'langfuse';

const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,
  baseUrl: 'https://cloud.langfuse.com',
});

// 创建 Trace
async function ragQuery(question: string, userId: string) {
  const trace = langfuse.trace({
    name: 'rag-query',
    userId,
    metadata: { question },
    tags: ['rag', 'production'],
  });

  // Span: Embedding
  const embedSpan = trace.span({ name: 'embedding' });
  const embedding = await embed(question);
  embedSpan.end({ metadata: { model: 'text-embedding-3-small', tokens: 15 } });

  // Span: Retrieval
  const retrievalSpan = trace.span({ name: 'retrieval' });
  const docs = await search(embedding, 5);
  retrievalSpan.end({ metadata: { resultCount: docs.length } });

  // Generation: LLM 调用（自动记录 Token 和成本）
  const generation = trace.generation({
    name: 'answer-generation',
    model: 'gpt-4o-mini',
    input: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: buildPrompt(question, docs) },
    ],
    modelParameters: { temperature: 0.3 },
  });

  const answer = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: buildPrompt(question, docs) },
    ],
  });

  generation.end({
    output: answer.choices[0].message.content,
    usage: {
      input: answer.usage?.prompt_tokens,
      output: answer.usage?.completion_tokens,
      total: answer.usage?.total_tokens,
    },
  });

  // 确保数据发送
  await langfuse.flushAsync();

  return { answer: answer.choices[0].message.content, traceId: trace.id };
}
```

### 3.3 Prompt 版本管理

```typescript
// 在 Langfuse 中管理 Prompt 版本
// 1. 在 Langfuse 控制台创建 Prompt
// 2. 在代码中拉取最新版本

const prompt = await langfuse.getPrompt('rag-system-prompt');

const messages = prompt.compile({
  context: contextText,
  question: userQuestion,
});

// Prompt 版本化的好处：
// - 改 Prompt 不需要部署代码
// - 可以 A/B 测试不同版本
// - 每个 Trace 自动关联 Prompt 版本
```

```
Prompt 版本管理工作流：

  v1: "你是一个助手，回答用户问题"
    → 上线后发现幻觉率 15%

  v2: "你是一个助手，只基于上下文回答，不知道说不知道"
    → 幻觉率降到 3%

  v3: "你是一个知识库专家..."
    → A/B 测试中

  每个 Trace 自动记录用的是哪个版本
  → 可以按版本对比质量指标
```

### 3.4 评分与评估

```typescript
// 用户反馈评分
langfuse.score({
  traceId: trace.id,
  name: 'user-feedback',
  value: 1,  // 👍
  comment: '回答准确',
});

// LLM 自动评分
langfuse.score({
  traceId: trace.id,
  name: 'faithfulness',
  value: 0.92,
  comment: '回答基本忠实于上下文',
});

langfuse.score({
  traceId: trace.id,
  name: 'relevance',
  value: 0.85,
  comment: '与问题相关性高',
});
```

自托管部署：

```bash
# Docker Compose 一键部署
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up -d

# 访问 http://localhost:3000
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 三大黑盒 | 质量（幻觉）、成本（Token）、链路（Agent 决策） |
| Trace/Span | 每次请求的完整调用链，嵌套记录每一步 |
| Langfuse | 开源、自托管、Trace + Prompt 管理 + 评分 |
| 自动追踪 | `observeOpenAI()` 包装 SDK 即可 |

> **下一章**：LangSmith / Arize 对比，以及成本归因与质量告警。

---

## 4. LangSmith 与 Arize：商业方案对比

### 4.1 LangSmith：LangChain 生态闭环

```python
# LangSmith 与 LangChain 深度集成
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "ls_xxx"
os.environ["LANGCHAIN_PROJECT"] = "my-rag-app"

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 设置环境变量后，所有 LangChain 调用自动追踪
llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是知识库助手"),
    ("user", "{question}"),
])

chain = prompt | llm
result = chain.invoke({"question": "什么是事件循环？"})
# → LangSmith 自动记录完整 Trace
```

LangSmith 的核心优势：

| 特性 | 说明 |
|---|---|
| **零配置追踪** | 设置环境变量即可，无需改代码 |
| **Playground** | 在线调试 Prompt，实时看效果 |
| **Dataset** | 创建评估数据集 + 自动化回归测试 |
| **Hub** | Prompt 模板市场，社区共享 |
| **Annotation Queue** | 人工标注队列，团队协作评估 |

### 4.2 Arize Phoenix：ML 可观测扩展到 LLM

```python
# Arize Phoenix 本地启动
import phoenix as px

session = px.launch_app()
# → 浏览器自动打开 http://localhost:6006

# OpenTelemetry 自动追踪
from openinference.instrumentation.openai import OpenAIInstrumentor
from phoenix.otel import register

tracer_provider = register(endpoint="http://localhost:6006/v1/traces")
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

# 正常调用 OpenAI，Phoenix 自动收集
import openai
client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "什么是 RAG？"}],
)
```

Arize Phoenix 的核心优势：

| 特性 | 说明 |
|---|---|
| **OpenTelemetry 标准** | 基于开放标准，不锁定 |
| **Embedding 可视化** | UMAP 降维可视化向量分布 |
| **检索评估** | 自动评估 RAG 检索质量（NDCG/MRR） |
| **Hallucination 检测** | 内置幻觉检测评估器 |
| **本地运行** | `pip install arize-phoenix` 即可 |

### 4.3 三大平台横向对比

| 维度 | Langfuse | LangSmith | Arize Phoenix |
|---|---|---|---|
| **开源** | ✅ MIT | ❌ | ✅ |
| **自托管** | ✅ Docker | ❌ | ✅ pip install |
| **JS/TS SDK** | ✅ 原生支持 | ⚠️ LangChain.js | ❌ Python only |
| **追踪** | ✅ | ✅ 最强 | ✅ OpenTelemetry |
| **Prompt 管理** | ✅ 版本化 | ✅ Hub | ❌ |
| **成本追踪** | ✅ | ✅ | ✅ |
| **评估** | ✅ 内置 | ✅ 最完善 | ✅ Embedding 分析 |
| **Embedding 可视化** | ❌ | ❌ | ✅ 独有优势 |
| **适合** | Node.js / 通用 | LangChain 全家桶 | ML 团队 / 研究 |

```
选型决策：

  用 LangChain？ → LangSmith（零配置集成）
  用 Node.js？   → Langfuse（JS SDK + 开源自托管）
  ML/研究团队？   → Arize Phoenix（Embedding 可视化 + 检索评估）
  隐私要求高？   → Langfuse 或 Phoenix（自托管）
```

---

## 5. 成本归因与优化

### 5.1 Token 成本追踪

```typescript
// 每次 LLM 调用记录 Token 和成本
interface TokenUsage {
  model: string;
  inputTokens: number;
  outputTokens: number;
  cost: number;            // 美元
  traceId: string;
  userId: string;
  feature: string;         // 功能模块
  timestamp: Date;
}

// 定价表
const PRICING: Record<string, { input: number; output: number }> = {
  'gpt-4o':       { input: 2.50 / 1_000_000, output: 10.00 / 1_000_000 },
  'gpt-4o-mini':  { input: 0.15 / 1_000_000, output: 0.60 / 1_000_000 },
  'gpt-4.1':      { input: 2.00 / 1_000_000, output: 8.00 / 1_000_000 },
  'gpt-4.1-mini': { input: 0.40 / 1_000_000, output: 1.60 / 1_000_000 },
  'gpt-4.1-nano': { input: 0.10 / 1_000_000, output: 0.40 / 1_000_000 },
};

function calculateCost(model: string, inputTokens: number, outputTokens: number): number {
  const price = PRICING[model];
  if (!price) return 0;
  return inputTokens * price.input + outputTokens * price.output;
}
```

### 5.2 多维成本归因（用户 / 功能 / 模型）

```typescript
// 成本归因中间件
function costTracker(feature: string) {
  return async (ctx: any, next: () => Promise<void>) => {
    const startTime = Date.now();
    await next();

    // 从 response 提取 usage
    const usage = ctx.get('llmUsage');
    if (usage) {
      await db.insert(tokenUsageTable).values({
        model: usage.model,
        inputTokens: usage.inputTokens,
        outputTokens: usage.outputTokens,
        cost: calculateCost(usage.model, usage.inputTokens, usage.outputTokens),
        userId: ctx.get('userId'),
        feature,
        timestamp: new Date(),
      });
    }
  };
}

// 按维度查询
// 1. 按用户
const userCosts = await db
  .select({
    userId: tokenUsage.userId,
    totalCost: sql`sum(cost)`,
    totalTokens: sql`sum(input_tokens + output_tokens)`,
  })
  .from(tokenUsage)
  .where(gte(tokenUsage.timestamp, last30Days))
  .groupBy(tokenUsage.userId)
  .orderBy(desc(sql`sum(cost)`));

// 2. 按功能
const featureCosts = await db
  .select({
    feature: tokenUsage.feature,
    totalCost: sql`sum(cost)`,
    callCount: sql`count(*)`,
    avgCost: sql`avg(cost)`,
  })
  .from(tokenUsage)
  .groupBy(tokenUsage.feature)
  .orderBy(desc(sql`sum(cost)`));

// 3. 按模型
const modelCosts = await db
  .select({
    model: tokenUsage.model,
    totalCost: sql`sum(cost)`,
    totalInput: sql`sum(input_tokens)`,
    totalOutput: sql`sum(output_tokens)`,
  })
  .from(tokenUsage)
  .groupBy(tokenUsage.model);
```

```
成本归因报表示例：

  按功能：
  ┌──────────────┬──────────┬─────────┬──────────┐
  │ 功能          │ 总成本    │ 调用次数 │ 平均成本  │
  ├──────────────┼──────────┼─────────┼──────────┤
  │ RAG 问答      │ $12.50   │ 8,200   │ $0.0015  │
  │ 文档摘要      │ $8.30    │ 1,500   │ $0.0055  │
  │ Agent 任务    │ $25.00   │ 3,100   │ $0.0081  │
  └──────────────┴──────────┴─────────┴──────────┘
  → Agent 单次成本最高，优先优化
```

### 5.3 成本优化策略

```typescript
// 策略 1：语义缓存（相似问题复用答案）
class SemanticCache {
  async get(question: string): Promise<string | null> {
    const embedding = await embed(question);
    const cached = await db.query(
      `SELECT answer FROM cache
       WHERE 1 - (embedding <=> $1) > 0.95
       ORDER BY embedding <=> $1
       LIMIT 1`,
      [pgvector.toSql(embedding)]
    );
    return cached.rows[0]?.answer || null;
  }

  async set(question: string, answer: string): Promise<void> {
    const embedding = await embed(question);
    await db.query(
      'INSERT INTO cache (question, answer, embedding) VALUES ($1, $2, $3)',
      [question, answer, pgvector.toSql(embedding)]
    );
  }
}

// 策略 2：模型降级（复杂问题用大模型，简单问题用小模型）
async function selectModel(question: string): Promise<string> {
  const complexity = await openai.chat.completions.create({
    model: 'gpt-4.1-nano',
    messages: [{
      role: 'user',
      content: `判断这个问题的复杂度（simple/complex）：${question}\n只回答一个词`,
    }],
    max_tokens: 5,
  });

  const level = complexity.choices[0].message.content?.trim();
  return level === 'complex' ? 'gpt-4o' : 'gpt-4o-mini';
}

// 策略 3：预算控制
class BudgetGuard {
  async checkBudget(userId: string, maxDailyCost = 1.0): Promise<boolean> {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const result = await db.query(
      'SELECT COALESCE(SUM(cost), 0) as total FROM token_usage WHERE user_id = $1 AND timestamp >= $2',
      [userId, today]
    );

    return result.rows[0].total < maxDailyCost;
  }
}
```

| 策略 | 节省比例 | 适合场景 |
|---|---|---|
| 语义缓存 | 30-60% | 重复问题多（FAQ/客服） |
| 模型降级 | 40-70% | 问题复杂度差异大 |
| Prompt 压缩 | 10-30% | Prompt 模板冗长 |
| 预算控制 | 防超支 | To-C 应用 |

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| LangSmith | LangChain 零配置集成、Playground、Annotation Queue |
| Arize Phoenix | OpenTelemetry 标准、Embedding 可视化、本地运行 |
| 选型 | Node.js → Langfuse、LangChain → LangSmith、ML → Phoenix |
| 成本归因 | 按用户/功能/模型三维度统计 |
| 成本优化 | 语义缓存 + 模型降级 + 预算控制 |

> **下一章**：质量评估与告警——LLM-as-Judge、自动评估指标、回归检测。

---

## 6. 质量评估与告警

### 6.1 LLM-as-Judge 自动评估

```
传统软件测试 vs LLM 质量评估：

  传统：assert(result === expected)   ← 确定性输出
  LLM：回答可能有很多种正确写法       ← 不确定性输出

  解决方案：用另一个 LLM 当"评审官"
  → LLM-as-Judge
```

```typescript
// LLM-as-Judge 评估器
async function evaluateFaithfulness(
  question: string,
  context: string,
  answer: string,
): Promise<{ score: number; reasoning: string }> {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o',  // 用更强的模型做评审
    messages: [{
      role: 'user',
      content: `你是一个严格的质量评审员。请评估 AI 的回答是否忠实于给定的上下文。

## 上下文
${context}

## 问题
${question}

## AI 的回答
${answer}

## 评估标准
- 回答中的所有事实是否都能在上下文中找到依据？
- 是否有编造（幻觉）的内容？
- 是否有与上下文矛盾的内容？

请返回 JSON：
{
  "score": 0-1 之间的分数（1=完全忠实，0=完全幻觉）,
  "reasoning": "评估理由"
}`,
    }],
    response_format: { type: 'json_object' },
    temperature: 0,
  });

  return JSON.parse(response.choices[0].message.content!);
}
```

### 6.2 自定义评估指标

```typescript
// 评估指标体系
interface EvaluationResult {
  faithfulness: number;   // 忠实度：回答是否基于上下文
  relevance: number;      // 相关性：回答是否切题
  completeness: number;   // 完整性：是否回答了全部问题
  toxicity: number;       // 安全性：是否有有害内容
}

// 批量评估
async function evaluateBatch(
  testCases: { question: string; context: string; answer: string }[]
): Promise<{ averages: EvaluationResult; details: EvaluationResult[] }> {
  const results: EvaluationResult[] = [];

  for (const tc of testCases) {
    const faithfulness = await evaluateFaithfulness(tc.question, tc.context, tc.answer);
    const relevance = await evaluateRelevance(tc.question, tc.answer);
    const completeness = await evaluateCompleteness(tc.question, tc.answer);
    const toxicity = await evaluateToxicity(tc.answer);

    results.push({
      faithfulness: faithfulness.score,
      relevance: relevance.score,
      completeness: completeness.score,
      toxicity: toxicity.score,
    });
  }

  const averages = {
    faithfulness: avg(results.map(r => r.faithfulness)),
    relevance: avg(results.map(r => r.relevance)),
    completeness: avg(results.map(r => r.completeness)),
    toxicity: avg(results.map(r => r.toxicity)),
  };

  return { averages, details: results };
}

function avg(nums: number[]): number {
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}
```

```
评估指标参考标准：

  ┌──────────────┬──────────┬──────────┬──────────┐
  │ 指标          │ 优秀      │ 合格     │ 告警      │
  ├──────────────┼──────────┼──────────┼──────────┤
  │ Faithfulness │ ≥ 0.95   │ ≥ 0.85   │ < 0.85   │
  │ Relevance    │ ≥ 0.90   │ ≥ 0.80   │ < 0.80   │
  │ Completeness │ ≥ 0.85   │ ≥ 0.70   │ < 0.70   │
  │ Toxicity     │ ≤ 0.01   │ ≤ 0.05   │ > 0.05   │
  └──────────────┴──────────┴──────────┴──────────┘
```

### 6.3 质量告警与回归检测

```typescript
// 实时质量监控
class QualityMonitor {
  private window: number[] = [];  // 滑动窗口
  private readonly windowSize = 100;

  async checkAndAlert(score: number, metric: string): Promise<void> {
    this.window.push(score);
    if (this.window.length > this.windowSize) {
      this.window.shift();
    }

    const average = avg(this.window);
    const threshold = THRESHOLDS[metric];

    if (average < threshold.alert) {
      await this.sendAlert({
        level: 'critical',
        metric,
        value: average,
        threshold: threshold.alert,
        message: `${metric} 质量低于告警阈值: ${average.toFixed(3)} < ${threshold.alert}`,
      });
    } else if (average < threshold.warning) {
      await this.sendAlert({
        level: 'warning',
        metric,
        value: average,
        threshold: threshold.warning,
        message: `${metric} 质量接近告警: ${average.toFixed(3)}`,
      });
    }
  }

  private async sendAlert(alert: Alert): Promise<void> {
    // 发送到 Slack / 邮件 / PagerDuty
    console.warn(`[ALERT-${alert.level}] ${alert.message}`);
    await fetch(process.env.SLACK_WEBHOOK!, {
      method: 'POST',
      body: JSON.stringify({ text: `🚨 ${alert.message}` }),
    });
  }
}

const THRESHOLDS: Record<string, { warning: number; alert: number }> = {
  faithfulness: { warning: 0.90, alert: 0.85 },
  relevance:    { warning: 0.85, alert: 0.80 },
};
```

```typescript
// Prompt 变更的回归检测
async function regressionTest(promptVersion: string) {
  // 1. 加载测试数据集
  const testSet = await loadTestDataset('golden-qa-set');

  // 2. 用新 Prompt 跑全部测试
  const results = await Promise.all(
    testSet.map(async (tc) => {
      const answer = await rag.query(tc.question);  // 用新 Prompt
      const eval_ = await evaluateFaithfulness(tc.question, tc.context, answer.answer);
      return { ...tc, answer: answer.answer, score: eval_.score };
    })
  );

  // 3. 与上一版本对比
  const currentAvg = avg(results.map(r => r.score));
  const previousAvg = await getPreviousVersionScore(promptVersion);

  const regression = previousAvg - currentAvg;

  if (regression > 0.05) {
    console.error(`⚠️ 质量回归! v${promptVersion} 下降了 ${(regression * 100).toFixed(1)}%`);
    return { passed: false, regression };
  }

  console.log(`✅ 回归测试通过: ${currentAvg.toFixed(3)} (上版: ${previousAvg.toFixed(3)})`);
  return { passed: true, regression };
}
```

---

## 7. 多 Agent 调试与生产实践

### 7.1 多 Agent Trace 可视化

```
多 Agent 系统的 Trace 结构：

  Trace: "帮我分析这份财报并生成投资建议"
  │
  ├─ Span: orchestrator (规划 Agent)
  │   └─ 决策: 需要调用 3 个子 Agent
  │
  ├─ Span: agent-1 (数据提取 Agent)
  │   ├─ tool: parse_pdf → 提取营收数据
  │   ├─ tool: calculate → 同比增长 15%
  │   └─ generation → 数据摘要
  │
  ├─ Span: agent-2 (行业分析 Agent)
  │   ├─ tool: web_search → 行业动态
  │   └─ generation → 行业分析报告
  │
  ├─ Span: agent-3 (投资建议 Agent)
  │   ├─ input: agent-1 + agent-2 的输出
  │   └─ generation → 投资建议
  │
  └─ Span: synthesizer (汇总 Agent)
      └─ generation → 最终报告

  总耗时: 12.5s | 总 Token: 8,500 | 总成本: $0.035
  瓶颈: agent-2 的 web_search 耗时 6s
```

```typescript
// 多 Agent Trace 记录
async function multiAgentTask(task: string, userId: string) {
  const trace = langfuse.trace({
    name: 'multi-agent-task',
    userId,
    metadata: { task },
  });

  // Orchestrator
  const orchSpan = trace.span({ name: 'orchestrator' });
  const plan = await planTask(task);
  orchSpan.end({ output: plan });

  // 并行执行子 Agent
  const results = await Promise.all(
    plan.agents.map(async (agentConfig: any) => {
      const agentSpan = trace.span({
        name: `agent-${agentConfig.name}`,
        metadata: { role: agentConfig.role },
      });

      const result = await executeAgent(agentConfig, trace);

      agentSpan.end({
        output: result,
        metadata: {
          toolCalls: result.toolCalls?.length || 0,
          tokens: result.totalTokens,
        },
      });

      return result;
    })
  );

  // Synthesizer
  const synthGen = trace.generation({
    name: 'synthesizer',
    model: 'gpt-4o',
  });
  const finalReport = await synthesize(results);
  synthGen.end({ output: finalReport });

  await langfuse.flushAsync();
  return { report: finalReport, traceId: trace.id };
}
```

### 7.2 Agent 决策回放与调试

```typescript
// 记录 Agent 的决策日志
interface AgentDecision {
  step: number;
  thought: string;       // Agent 的推理过程
  action: string;        // 选择的 Tool
  actionInput: any;      // Tool 的输入
  observation: string;   // Tool 的返回
  timestamp: number;
}

// 决策回放查看器
async function replayAgentDecisions(traceId: string) {
  const trace = await langfuse.fetchTrace(traceId);
  const decisions: AgentDecision[] = [];

  for (const span of trace.observations) {
    if (span.name.startsWith('agent-step')) {
      decisions.push({
        step: span.metadata?.step,
        thought: span.metadata?.thought,
        action: span.metadata?.action,
        actionInput: span.input,
        observation: span.output,
        timestamp: new Date(span.startTime).getTime(),
      });
    }
  }

  // 格式化输出
  console.log(`=== Agent 决策回放 (Trace: ${traceId}) ===\n`);
  for (const d of decisions) {
    console.log(`Step ${d.step}:`);
    console.log(`  💭 思考: ${d.thought}`);
    console.log(`  🔧 行动: ${d.action}(${JSON.stringify(d.actionInput)})`);
    console.log(`  👁 观察: ${d.observation.slice(0, 200)}`);
    console.log();
  }
}
```

### 7.3 生产 Dashboard 搭建

```typescript
// Dashboard 数据 API
app.get('/api/dashboard', async (c) => {
  const timeRange = c.req.query('range') || '24h';

  // 1. 概览指标
  const overview = {
    totalRequests: await countRequests(timeRange),
    avgLatency: await avgLatency(timeRange),
    totalCost: await totalCost(timeRange),
    avgFaithfulness: await avgScore('faithfulness', timeRange),
    errorRate: await errorRate(timeRange),
  };

  // 2. 成本趋势（按小时）
  const costTrend = await db.query(
    `SELECT date_trunc('hour', timestamp) AS hour,
            SUM(cost) AS cost,
            SUM(input_tokens + output_tokens) AS tokens
     FROM token_usage
     WHERE timestamp >= NOW() - INTERVAL '${timeRange}'
     GROUP BY hour
     ORDER BY hour`
  );

  // 3. 质量趋势
  const qualityTrend = await db.query(
    `SELECT date_trunc('hour', timestamp) AS hour,
            AVG(CASE WHEN name = 'faithfulness' THEN value END) AS faithfulness,
            AVG(CASE WHEN name = 'relevance' THEN value END) AS relevance
     FROM scores
     WHERE timestamp >= NOW() - INTERVAL '${timeRange}'
     GROUP BY hour
     ORDER BY hour`
  );

  // 4. Top 错误
  const topErrors = await db.query(
    `SELECT error_message, COUNT(*) AS count
     FROM traces
     WHERE status = 'error' AND timestamp >= NOW() - INTERVAL '${timeRange}'
     GROUP BY error_message
     ORDER BY count DESC
     LIMIT 10`
  );

  return c.json({ overview, costTrend: costTrend.rows, qualityTrend: qualityTrend.rows, topErrors: topErrors.rows });
});
```

```
生产 Dashboard 核心面板：

  ┌─────────────────────────────────────────────────────┐
  │  LLM 可观测性 Dashboard                              │
  │                                                      │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
  │  │请求量     │ │平均延迟   │ │日成本     │ │忠实度   │ │
  │  │ 12,500   │ │ 1.2s    │ │ $45.80  │ │ 0.93   │ │
  │  │ ▲12%     │ │ ▼8%     │ │ ▲5%     │ │ ▲0.02  │ │
  │  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
  │                                                      │
  │  成本趋势（24h）        质量趋势（24h）              │
  │  ████▇▆▅▆▇████         ▁▂▃▄▅▆▇█▇▆▅▄               │
  │                                                      │
  │  Top 5 高成本功能        Top 5 低质量 Trace          │
  │  1. Agent 任务 $25      1. trace-abc (0.42)         │
  │  2. RAG 问答   $12      2. trace-def (0.55)         │
  │  3. 文档摘要   $8       3. trace-ghi (0.61)         │
  └─────────────────────────────────────────────────────┘
```

---

## 全书总结

```
┌─────────────────────────────────────────────────────────────┐
│       Agent 监控与可观测性 · 知识地图                          │
│                                                              │
│  Ch.1  为什么需要    三大黑盒 / 三支柱 / 平台选型             │
│  Ch.2  Trace 追踪   Span 嵌套 / 手动埋点 / SDK 自动追踪      │
│  Ch.3  Langfuse     SDK / Prompt 版本 / 评分 / 自托管         │
│  Ch.4  LangSmith    零配置 / Playground / 三平台横评          │
│        Arize        OpenTelemetry / Embedding 可视化          │
│  Ch.5  成本归因      Token 追踪 / 多维归因 / 缓存·降级·预算   │
│  Ch.6  质量评估      LLM-as-Judge / 四指标体系 / 回归检测     │
│  Ch.7  多 Agent      Trace 可视化 / 决策回放 / Dashboard      │
│                                                              │
│  7 章 22 节，构建 LLM 应用的完整可观测性体系。               │
└─────────────────────────────────────────────────────────────┘
```

> 🎉 **核心公式**：可观测性 = Trace（看链路）+ Metrics（看趋势）+ Evaluation（看质量）。
