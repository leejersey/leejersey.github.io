# Vercel AI SDK 全栈实战

> 从 `streamText` 到 AI Agent——Vercel AI SDK 是 TypeScript 生态中最成熟的 LLM 集成框架。本教程从核心 API 出发，逐步深入流式对话、Tool Calling、结构化输出、多模型切换、Generative UI 和生产级 Agent 构建，帮你用一套代码适配所有大模型。

---

## 1. 为什么选 Vercel AI SDK

你想用 TypeScript 调用 GPT-4 写个聊天机器人——听起来很简单？等你处理完流式解析、Tool Calling 回传、多模型适配、前端状态同步之后，你会发现自己在重复造 Vercel 已经造好的轮子。

### 1.1 裸调 LLM API 的痛点

```typescript
// 裸调 OpenAI API 的"真实"代码——远比你想象的复杂
const response = await fetch("https://api.openai.com/v1/chat/completions", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
  },
  body: JSON.stringify({
    model: "gpt-4o",
    messages: [{ role: "user", content: "你好" }],
    stream: true,     // 流式输出
  }),
});

// 问题来了：流式响应是 SSE 格式，你得手动解析
const reader = response.body!.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value);
  // 每个 chunk 可能包含多个 data: 行
  // 还可能在 chunk 边界截断一个 JSON 对象
  // 还要处理 [DONE] 标记
  // 还要处理 Tool Call 的分片...
  // 😱 你确定要自己写这些？
}
```

```
裸调 LLM API 的 5 大痛点：

  痛点 1：流式解析地狱
  → SSE 格式解析、chunk 边界处理、JSON 分片重组
  → 每个模型厂商的流格式还不一样

  痛点 2：Tool Calling 状态机
  → 模型返回 tool_call → 你执行工具 → 结果回传 → 模型继续生成
  → 多步调用？你需要手写循环 + 状态管理

  痛点 3：多模型适配
  → OpenAI 用 messages 格式
  → Anthropic 用不同的消息结构
  → Google 又是另一套 API
  → 切换模型 = 重写一半代码

  痛点 4：前后端状态同步
  → 后端在流式生成、前端要实时显示
  → 消息列表、加载状态、错误处理、中断重试
  → 你又在造 React 状态管理的轮子

  痛点 5：类型安全缺失
  → API 返回的是 any 类型的 JSON
  → Tool 参数没有校验
  → 结构化输出没有 Schema 保证
```

### 1.2 AI SDK 的设计哲学：Provider 抽象 + 流式优先

```typescript
// 用 AI SDK 做同样的事——3 行代码
import { streamText } from "ai";
import { openai } from "@ai-sdk/openai";

const result = streamText({
  model: openai("gpt-4o"),               // ← Provider 抽象
  prompt: "你好",
});
// → 自动处理流式解析、SSE 格式、chunk 重组
// → 返回类型安全的 AsyncIterable
// → 切换模型？改一行：model: anthropic("claude-4-sonnet")
```

```
AI SDK 的四大设计原则：

  原则 1：Provider 抽象——一套接口适配所有模型
  ──────────────────────────────────────────
  你的代码调用 streamText({ model: xxx })
  → xxx 可以是 openai("gpt-4o")
  → 可以是 anthropic("claude-4-sonnet")
  → 可以是 google("gemini-2.5-pro")
  → 你的业务代码一行不改

  原则 2：流式优先——默认就是流式
  ──────────────────────────────────────────
  streamText  → 流式文本（聊天场景）
  streamObject → 流式结构化数据（渐进渲染）
  generateText → 非流式（批处理场景，也支持）

  原则 3：类型安全——TypeScript 原生
  ──────────────────────────────────────────
  Tool 参数 → Zod Schema → 自动推导 TypeScript 类型
  结构化输出 → Zod Schema → 返回值有完整类型
  → 编译时就能发现错误，不用等运行时

  原则 4：全栈整合——前后端一体
  ──────────────────────────────────────────
  后端 streamText() → 返回标准 Response
  前端 useChat()   → 自动消费流式响应
  → 不需要手写 SSE 解析、WebSocket、状态管理
```

### 1.3 与 LangChain.js 的定位对比

```
两个框架不是竞品，而是不同层次的工具：

  Vercel AI SDK                    LangChain.js
  ──────────────                   ──────────────
  定位：LLM 调用层                   定位：LLM 应用编排层
  → "怎么调模型、怎么流式、          → "怎么串 Chain、怎么做 RAG、
     怎么渲染到 UI"                    怎么管 Memory"

  核心能力：                        核心能力：
  ✅ 流式文本 / 结构化输出           ✅ Chain / Agent 编排
  ✅ Tool Calling                  ✅ Document Loader / Splitter
  ✅ React Hooks（useChat）         ✅ Vector Store 集成
  ✅ Generative UI                 ✅ Memory / History 管理
  ✅ Provider 多模型适配             ✅ 复杂 RAG Pipeline

  不擅长：                          不擅长：
  ❌ 复杂 RAG 管线                  ❌ 前端 UI 集成
  ❌ 文档加载 / 向量检索              ❌ 流式渲染
  ❌ 长链编排                       ❌ React 状态管理
```

| 维度 | **Vercel AI SDK** | **LangChain.js** |
|:---|:---|:---|
| 核心场景 | Chat UI、流式应用 | RAG、复杂 Agent |
| 学习曲线 | ⭐ 低（API 少而精） | ⭐⭐⭐ 高（抽象多） |
| 前端集成 | ✅ 原生 React Hooks | ❌ 需要自己写 |
| 类型安全 | ✅ Zod + TypeScript | ⚠️ 部分支持 |
| 包体积 | 轻量（~50KB） | 较重（依赖多） |
| 搭配使用 | 前端+模型调用层 | 后端编排层 |

> 💡 **最佳实践**：两者可以搭配使用——LangChain.js 负责后端的 RAG Pipeline 和文档处理，Vercel AI SDK 负责前端交互和流式渲染。它们不冲突。

### 1.4 三层架构概览：Core / UI / Provider

```
Vercel AI SDK 的三层架构：

  ┌─────────────────────────────────────────────────┐
  │                   你的应用代码                     │
  ├─────────────────────────────────────────────────┤
  │                                                 │
  │  ┌───────────────┐    ┌───────────────────┐     │
  │  │  AI SDK UI    │    │   AI SDK Core     │     │
  │  │               │    │                   │     │
  │  │  useChat()    │───►│  streamText()     │     │
  │  │  useCompletion│    │  generateText()   │     │
  │  │  useObject()  │    │  generateObject() │     │
  │  │               │    │  streamObject()   │     │
  │  │  (React Hooks)│    │  (核心 API)        │     │
  │  └───────────────┘    └────────┬──────────┘     │
  │                                │                │
  │  ┌─────────────────────────────▼──────────────┐ │
  │  │            AI SDK Provider                  │ │
  │  │                                             │ │
  │  │  @ai-sdk/openai    → OpenAI / Azure         │ │
  │  │  @ai-sdk/anthropic → Claude                 │ │
  │  │  @ai-sdk/google    → Gemini / Vertex AI     │ │
  │  │  @ai-sdk/mistral   → Mistral                │ │
  │  │  @ai-sdk/xai       → Grok                   │ │
  │  │  (统一接口，可扩展)                            │ │
  │  └─────────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────┘
```

```
三层的职责分工：

  AI SDK Core（包名：ai）
  → 核心 API：streamText / generateText / generateObject / streamObject
  → Tool Calling 框架
  → 消息格式标准化
  → 不依赖任何前端框架，可以在任何 JS 运行时使用

  AI SDK UI（包名：ai/react、ai/svelte、ai/vue）
  → React Hooks：useChat / useCompletion / useObject
  → 消息状态管理、流式渲染、加载/错误状态
  → 也支持 Svelte 和 Vue（不只是 React）

  AI SDK Provider（包名：@ai-sdk/openai 等）
  → 每个 Provider 是独立的 npm 包
  → 实现统一的 LanguageModel 接口
  → 你只安装需要的 Provider → 按需引入，不膨胀
```

```bash
# 最小安装（只用 OpenAI）
pnpm add ai @ai-sdk/openai

# 多模型（OpenAI + Anthropic + Google）
pnpm add ai @ai-sdk/openai @ai-sdk/anthropic @ai-sdk/google

# 本地模型（Ollama 通过 OpenAI 兼容模式）
pnpm add ai @ai-sdk/openai
# → 配置 baseURL 指向 Ollama 即可
```

> 💡 **核心包 `ai` 只有 ~50KB**，不包含任何 Provider 实现——你用哪个模型就装哪个 Provider 包。这比 LangChain.js 的"全家桶"轻量得多。

---

## 2. 环境准备与第一个对话

这一章从零开始——安装依赖、配置 API Key、写出第一个 `generateText` 调用，然后升级到 `streamText` 流式输出。5 分钟内你就能跑通第一个 AI 对话。

### 2.1 安装与项目初始化

```bash
# 创建项目（以 Next.js 为例，AI SDK 也支持纯 Node.js / Express / Hono）
pnpm create next-app@latest my-ai-app --typescript --app --eslint
cd my-ai-app

# 安装 AI SDK 核心 + OpenAI Provider
pnpm add ai @ai-sdk/openai

# 可选：安装其他 Provider
pnpm add @ai-sdk/anthropic    # Claude
pnpm add @ai-sdk/google       # Gemini
pnpm add @ai-sdk/xai          # Grok

# 安装 Zod（结构化输出需要）
pnpm add zod
```

```bash
# 配置环境变量
cat > .env.local << 'EOF'
# OpenAI
OPENAI_API_KEY=sk-xxx

# Anthropic（可选）
ANTHROPIC_API_KEY=sk-ant-xxx

# Google（可选）
GOOGLE_GENERATIVE_AI_API_KEY=xxx
EOF

# ⚠️ 确保 .gitignore 包含 .env.local
```

```
AI SDK 的环境变量约定：

  每个 Provider 有固定的环境变量名：
  @ai-sdk/openai    → OPENAI_API_KEY
  @ai-sdk/anthropic → ANTHROPIC_API_KEY
  @ai-sdk/google    → GOOGLE_GENERATIVE_AI_API_KEY
  @ai-sdk/mistral   → MISTRAL_API_KEY
  @ai-sdk/xai       → XAI_API_KEY

  → 不需要手动传 API Key，Provider 自动读取环境变量
  → 也可以显式传入：openai("gpt-4o", { apiKey: "xxx" })
```

### 2.2 generateText：第一次调用

```typescript
// src/app/api/chat/route.ts（Next.js Route Handler）
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";

export async function POST(req: Request) {
  const { prompt } = await req.json();

  // generateText：非流式，等待完整响应
  const { text, usage, finishReason } = await generateText({
    model: openai("gpt-4o"),          // 指定模型
    prompt,                            // 用户输入
  });

  return Response.json({
    text,                              // 生成的文本
    usage,                             // Token 用量
    finishReason,                      // 结束原因
  });
}
```

```typescript
// generateText 的返回值（完整类型）
const result = await generateText({
  model: openai("gpt-4o"),
  prompt: "用一句话解释什么是 TypeScript",
});

console.log(result.text);
// → "TypeScript 是 JavaScript 的超集，添加了静态类型检查..."

console.log(result.usage);
// → { promptTokens: 12, completionTokens: 28, totalTokens: 40 }

console.log(result.finishReason);
// → "stop"（正常结束）
// → "length"（达到 maxTokens 限制）
// → "tool-calls"（模型请求调用工具）
```

```
generateText vs streamText 的选择：

  generateText（非流式）
  → 等模型生成完毕 → 一次性返回全部文本
  → 适合：批处理、后台任务、不需要实时显示的场景
  → 延迟：需要等待全部生成完成（可能 2-10 秒）

  streamText（流式）
  → 逐 token 返回 → 前端可以边生成边显示
  → 适合：聊天界面、实时交互、用户体感要好的场景
  → 延迟：首个 token 通常 200-500ms 就出来
```

### 2.3 streamText：流式输出

```typescript
// src/app/api/chat/route.ts —— 流式版本
import { streamText } from "ai";
import { openai } from "@ai-sdk/openai";

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai("gpt-4o"),
    system: "你是一个有帮助的 AI 助手，用中文回答。",  // 系统提示词
    messages,                          // 对话历史（多轮对话）
  });

  // toDataStreamResponse() → 返回标准的流式 Response
  // 前端的 useChat Hook 可以直接消费这个响应
  return result.toDataStreamResponse();
}
```

```typescript
// streamText 的多种消费方式

// 方式 1：在 Next.js 中返回流式 Response（最常用）
return result.toDataStreamResponse();

// 方式 2：在 Node.js 中逐 chunk 消费
for await (const chunk of result.textStream) {
  process.stdout.write(chunk);         // 逐字输出到终端
}

// 方式 3：转为 ReadableStream
const stream = result.toTextStreamResponse();  // 纯文本流

// 方式 4：获取最终完整文本（等流结束）
const fullText = await result.text;    // Promise<string>
const usage = await result.usage;      // Promise<TokenUsage>
```

```
streamText 的 messages 格式（多轮对话）：

  messages: [
    { role: "system",    content: "你是一个翻译助手" },
    { role: "user",      content: "翻译：Hello World" },
    { role: "assistant", content: "你好，世界" },
    { role: "user",      content: "翻译：Good morning" },
  ]

  → role 有 4 种：system / user / assistant / tool
  → 这和 OpenAI 的 messages 格式一致
  → AI SDK 在传给不同 Provider 时会自动转换格式
```

> 💡 **`prompt` vs `messages`**：单轮对话用 `prompt: "你的问题"`，多轮对话用 `messages: [...]`。两者互斥，不能同时使用。

### 2.4 模型参数与选项详解

```typescript
// streamText / generateText 的完整选项
const result = streamText({
  // ═══ 必选 ═══
  model: openai("gpt-4o"),             // Provider + 模型名
  messages: [...],                      // 或 prompt: "..."

  // ═══ 系统提示词 ═══
  system: "你是一个专业的技术顾问...",    // 系统角色设定

  // ═══ 生成控制 ═══
  maxTokens: 2048,                     // 最大输出 Token 数
  temperature: 0.7,                    // 随机性（0=确定，1=创意）
  topP: 0.9,                           // 核采样
  topK: 40,                            // Top-K 采样（部分模型支持）
  frequencyPenalty: 0.5,               // 降低重复词频率
  presencePenalty: 0.3,                // 鼓励话题多样性
  seed: 12345,                         // 固定随机种子（可复现）
  stopSequences: ["END", "---"],       // 遇到这些文本就停止

  // ═══ Tool Calling ═══
  tools: { ... },                      // 工具定义（第 5 章详解）
  maxSteps: 5,                         // 最大 Tool 调用轮数

  // ═══ 生命周期回调 ═══
  onFinish: ({ text, usage }) => {     // 生成完成回调
    console.log(`Tokens used: ${usage.totalTokens}`);
  },

  // ═══ 中断信号 ═══
  abortSignal: controller.signal,      // 支持取消请求
});
```

```
常用参数速查表：

  参数             │ 取值范围    │ 默认值  │ 用途
  ─────────────────┼────────────┼────────┼──────────────────
  temperature      │ 0 - 2      │ 1      │ 控制随机性
  maxTokens        │ 1 - ∞      │ 模型上限│ 限制输出长度
  topP             │ 0 - 1      │ 1      │ 核采样范围
  frequencyPenalty │ -2 - 2     │ 0      │ 降低重复
  presencePenalty  │ -2 - 2     │ 0      │ 鼓励新话题
  seed             │ 任意整数    │ 无     │ 固定输出（可复现）

  temperature 经验值：
  0.0  → 确定性输出（代码生成、数据提取）
  0.3  → 轻微创意（技术写作、摘要）
  0.7  → 适度创意（对话、内容创作）← 推荐默认
  1.0+ → 高度随机（头脑风暴、创意写作）
```

> 💡 **参数兼容性**：不是所有参数都被所有模型支持。比如 `seed` 只有 OpenAI 支持，`topK` 只有 Google Gemini 支持。AI SDK 会忽略模型不支持的参数，不会报错。

---

## 3. Provider 系统：一套代码适配所有模型

今天你用 GPT-4o，明天客户要求换 Claude，后天老板说试试 Gemini——如果每次换模型都要改业务代码，你就输了。Provider 系统让你的业务代码和模型解耦。

### 3.1 Provider 架构与统一接口

```
Provider 的核心思想——适配器模式：

  你的代码                AI SDK Core               Provider
  ────────               ──────────               ────────
  streamText({           统一的                    @ai-sdk/openai
    model: ???    ────►   LanguageModel   ◄────    @ai-sdk/anthropic
  })                     接口                      @ai-sdk/google

  你只面对 streamText / generateText 这些统一 API
  → 传入不同的 model 参数 → 自动路由到对应 Provider
  → Provider 负责：
    1. 把统一格式翻译成厂商 API 格式
    2. 把厂商响应翻译回统一格式
    3. 处理流式传输的差异
```

```typescript
// 同一份代码，切换模型只需改一行
import { streamText } from "ai";
import { openai } from "@ai-sdk/openai";
import { anthropic } from "@ai-sdk/anthropic";
import { google } from "@ai-sdk/google";

// 用 OpenAI
streamText({ model: openai("gpt-4o"), prompt: "你好" });

// 切换到 Claude —— 业务代码完全不变
streamText({ model: anthropic("claude-4-sonnet"), prompt: "你好" });

// 切换到 Gemini —— 还是不变
streamText({ model: google("gemini-2.5-pro"), prompt: "你好" });
```

### 3.2 主流 Provider 配置（OpenAI / Anthropic / Google）

```typescript
// ═══ OpenAI ═══
import { openai } from "@ai-sdk/openai";

// 基本用法（自动读取 OPENAI_API_KEY）
const model = openai("gpt-4o");

// 指定参数
const model = openai("gpt-4o-mini", {
  structuredOutputs: true,    // 启用结构化输出（更可靠的 JSON）
});

// 使用 Azure OpenAI
import { createAzure } from "@ai-sdk/azure";
const azure = createAzure({
  resourceName: "my-resource",
  apiKey: process.env.AZURE_API_KEY,
});
const model = azure("my-gpt4o-deployment");
```

```typescript
// ═══ Anthropic ═══
import { anthropic } from "@ai-sdk/anthropic";

// 基本用法（自动读取 ANTHROPIC_API_KEY）
const model = anthropic("claude-4-sonnet");

// Claude 特有功能：长上下文（200K tokens）
const model = anthropic("claude-4-sonnet", {
  cacheControl: true,         // 启用 Prompt Caching（省钱）
});
```

```typescript
// ═══ Google Gemini ═══
import { google } from "@ai-sdk/google";

// 基本用法（自动读取 GOOGLE_GENERATIVE_AI_API_KEY）
const model = google("gemini-2.5-pro");

// Gemini 特有：安全设置
const model = google("gemini-2.5-flash", {
  safetySettings: [
    { category: "HARM_CATEGORY_HARASSMENT", threshold: "BLOCK_NONE" },
  ],
});
```

| Provider | 包名 | 环境变量 | 推荐模型 |
|:---|:---|:---|:---|
| OpenAI | `@ai-sdk/openai` | `OPENAI_API_KEY` | gpt-4o / gpt-4o-mini |
| Anthropic | `@ai-sdk/anthropic` | `ANTHROPIC_API_KEY` | claude-4-sonnet |
| Google | `@ai-sdk/google` | `GOOGLE_GENERATIVE_AI_API_KEY` | gemini-2.5-pro |
| Mistral | `@ai-sdk/mistral` | `MISTRAL_API_KEY` | mistral-large |
| xAI | `@ai-sdk/xai` | `XAI_API_KEY` | grok-3 |

### 3.3 OpenAI 兼容模式：接入 DeepSeek / 本地 Ollama

```typescript
// 很多模型厂商的 API 兼容 OpenAI 格式
// → 用 createOpenAI 自定义 baseURL 就能接入

import { createOpenAI } from "@ai-sdk/openai";

// ═══ 接入 DeepSeek ═══
const deepseek = createOpenAI({
  baseURL: "https://api.deepseek.com/v1",
  apiKey: process.env.DEEPSEEK_API_KEY,
});
const model = deepseek("deepseek-chat");
// → 现在 streamText({ model }) 就能用 DeepSeek 了

// ═══ 接入本地 Ollama ═══
const ollama = createOpenAI({
  baseURL: "http://localhost:11434/v1",  // Ollama 本地地址
  apiKey: "ollama",                       // Ollama 不需要真实 Key
});
const model = ollama("llama3.1");
// → 零成本本地开发、离线使用

// ═══ 接入其他 OpenAI 兼容服务 ═══
const together = createOpenAI({
  baseURL: "https://api.together.xyz/v1",
  apiKey: process.env.TOGETHER_API_KEY,
});
const model = together("meta-llama/Llama-3.1-70B-Instruct-Turbo");
```

```
OpenAI 兼容模式适用的厂商：

  厂商           │ baseURL                              │ 热门模型
  ───────────────┼──────────────────────────────────────┼─────────────────
  DeepSeek       │ https://api.deepseek.com/v1          │ deepseek-chat
  Ollama（本地）  │ http://localhost:11434/v1            │ llama3.1 / qwen2
  Together AI    │ https://api.together.xyz/v1          │ Llama-3.1-70B
  Groq           │ https://api.groq.com/openai/v1      │ llama-3.1-70b
  OpenRouter     │ https://openrouter.ai/api/v1        │ 聚合多模型
  硅基流动       │ https://api.siliconflow.cn/v1        │ Qwen2.5-72B

  → 只要 API 兼容 OpenAI 格式，都能用 createOpenAI 接入
```

### 3.4 运行时动态切换与 Fallback 策略

```typescript
// 运行时根据参数动态选择模型
import { openai } from "@ai-sdk/openai";
import { anthropic } from "@ai-sdk/anthropic";
import { google } from "@ai-sdk/google";

// 模型注册表
const models: Record<string, ReturnType<typeof openai>> = {
  "gpt-4o":          openai("gpt-4o"),
  "gpt-4o-mini":     openai("gpt-4o-mini"),
  "claude-4-sonnet": anthropic("claude-4-sonnet"),
  "gemini-2.5-pro":  google("gemini-2.5-pro"),
};

// API 接收 modelId 参数，动态选择模型
export async function POST(req: Request) {
  const { messages, modelId = "gpt-4o" } = await req.json();

  const model = models[modelId];
  if (!model) return Response.json({ error: "Unknown model" }, { status: 400 });

  const result = streamText({ model, messages });
  return result.toDataStreamResponse();
}
// → 前端传 modelId: "claude-4-sonnet" 就能切换模型
// → 业务代码完全不变
```

```typescript
// Fallback 策略：主模型挂了自动切换备用模型
import { streamText } from "ai";

async function chatWithFallback(messages: Message[]) {
  const providers = [
    openai("gpt-4o"),              // 主模型
    anthropic("claude-4-sonnet"),  // 备用 1
    google("gemini-2.5-pro"),      // 备用 2
  ];

  for (const model of providers) {
    try {
      return streamText({ model, messages });
    } catch (error) {
      console.warn(`Model ${model} failed, trying next...`);
      continue;                    // 当前模型失败，尝试下一个
    }
  }
  throw new Error("All providers failed");
}
```

```
生产级模型路由策略：

  策略 1：成本优先
  → 简单问题用 gpt-4o-mini（便宜）
  → 复杂问题用 gpt-4o（贵但强）
  → 根据 prompt 长度或任务类型动态选择

  策略 2：速度优先
  → 并行调用多个模型 → 用最先返回的结果
  → 适合对延迟敏感的场景

  策略 3：Fallback 容错
  → 主模型 → 备用模型 → 兜底模型
  → 适合高可用要求的生产环境

  策略 4：A/B 测试
  → 随机分配用户到不同模型
  → 收集用户反馈 → 选出最佳模型
```

> 💡 **Provider 是 AI SDK 的核心优势之一**：你的业务逻辑和底层模型完全解耦。模型涨价了？换一个。新模型出来了？加一行配置。这在快速迭代的 AI 领域至关重要。

---

## 4. 结构化输出：让 LLM 返回类型安全的数据

LLM 默认返回自由文本——但你的前端需要 JSON，你的数据库需要结构化数据。`generateObject` 让模型直接返回符合 Zod Schema 的类型安全对象，编译时就能发现错误。

### 4.1 generateObject + Zod：类型安全的 LLM 返回值

```typescript
import { generateObject } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

// 定义输出结构（Zod Schema）
const recipeSchema = z.object({
  name: z.string().describe("菜名"),
  ingredients: z.array(
    z.object({
      name: z.string().describe("食材名称"),
      amount: z.string().describe("用量，如 200g"),
    })
  ).describe("食材列表"),
  steps: z.array(z.string()).describe("烹饪步骤"),
  cookTime: z.number().describe("烹饪时间（分钟）"),
  difficulty: z.enum(["easy", "medium", "hard"]).describe("难度"),
});

// 调用 generateObject → 返回类型安全的对象
const { object } = await generateObject({
  model: openai("gpt-4o"),
  schema: recipeSchema,                   // ← 传入 Schema
  prompt: "给我一个番茄炒蛋的食谱",
});

// object 的类型被自动推导！
console.log(object.name);                  // string ✅
console.log(object.ingredients[0].amount); // string ✅
console.log(object.cookTime);              // number ✅
console.log(object.difficulty);            // "easy" | "medium" | "hard" ✅
// → 编译时就有完整类型提示，不需要 as any
```

```
generateObject 的工作原理：

  你的 Zod Schema
       │
       ▼
  AI SDK 转换为 JSON Schema
       │
       ▼
  发送给模型（使用 Structured Outputs / Tool Calling 机制）
       │
       ▼
  模型返回 JSON
       │
       ▼
  AI SDK 用 Zod 校验 → 类型安全的对象
       │
       ▼
  返回 { object: T }

  → 如果模型返回的 JSON 不符合 Schema → 自动重试
  → 你拿到的 object 保证符合 Schema 定义
```

### 4.2 streamObject：流式结构化输出

```typescript
import { streamObject } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

// streamObject → 流式返回结构化数据（边生成边渲染）
const result = streamObject({
  model: openai("gpt-4o"),
  schema: z.object({
    title: z.string(),
    summary: z.string(),
    tags: z.array(z.string()),
    sentiment: z.enum(["positive", "neutral", "negative"]),
  }),
  prompt: "分析这篇文章：人工智能正在改变教育...",
});

// 方式 1：逐步消费 partial object（前端渐进渲染）
for await (const partialObject of result.partialObjectStream) {
  console.log(partialObject);
  // 第 1 次：{ title: "人工智能..." }
  // 第 2 次：{ title: "人工智能与教育", summary: "本文探讨..." }
  // 第 3 次：{ title: "...", summary: "...", tags: ["AI"] }
  // → 前端可以边生成边显示，用户不用等
}

// 方式 2：等待最终完整对象
const finalObject = await result.object;   // Promise<T>
```

```typescript
// 在 Next.js Route Handler 中使用 streamObject
export async function POST(req: Request) {
  const { article } = await req.json();

  const result = streamObject({
    model: openai("gpt-4o"),
    schema: articleAnalysisSchema,
    prompt: `分析这篇文章：${article}`,
  });

  return result.toTextStreamResponse();    // 返回流式响应
}
```

### 4.3 实战场景：数据提取、分类、内容生成

```typescript
// 场景 1：从文本中提取结构化数据
const { object: contact } = await generateObject({
  model: openai("gpt-4o"),
  schema: z.object({
    name: z.string(),
    email: z.string().email(),
    phone: z.string().optional(),
    company: z.string().optional(),
  }),
  prompt: "从这段话提取联系人信息：我是张三，在字节跳动工作，邮箱 zhangsan@bytedance.com",
});
// → { name: "张三", email: "zhangsan@bytedance.com", company: "字节跳动" }
```

```typescript
// 场景 2：分类任务（用 enum 模式更高效）
const { object: classification } = await generateObject({
  model: openai("gpt-4o-mini"),        // 分类任务用便宜的模型就够
  output: "enum",                       // ← enum 模式
  enum: ["spam", "support", "sales", "feedback"],
  prompt: "分类这封邮件：我的订单一直没发货，能帮我看看吗？",
});
// → "support"
// → enum 模式更快、更便宜、100% 返回指定值之一
```

```typescript
// 场景 3：批量内容生成
const { object: posts } = await generateObject({
  model: openai("gpt-4o"),
  schema: z.object({
    posts: z.array(z.object({
      title: z.string().describe("标题，20 字以内"),
      content: z.string().describe("正文，100-200 字"),
      hashtags: z.array(z.string()).max(5),
    })).length(3),                       // 生成 3 篇
  }),
  prompt: "为一个 AI 编程工具生成 3 篇小红书文案",
});
// → posts.posts[0].title / .content / .hashtags 全部类型安全
```

### 4.4 Schema 设计最佳实践

```
Schema 设计原则：

  ✅ 原则 1：用 .describe() 给每个字段加描述
  → z.string().describe("用户的真实姓名，非昵称")
  → 描述越精确，模型输出越准确
  → 这实际上是在给模型写"字段级提示词"

  ✅ 原则 2：用 .optional() 标记非必需字段
  → z.string().optional()
  → 让模型在信息不足时返回 undefined，而不是瞎编

  ✅ 原则 3：用 enum 约束有限选项
  → z.enum(["low", "medium", "high"]) 而不是 z.string()
  → 模型 100% 返回指定值之一

  ✅ 原则 4：保持 Schema 扁平
  → 嵌套超过 3 层 → 模型容易出错
  → 拆成多次调用比一次复杂 Schema 更可靠

  ❌ 避免：
  → z.any() → 失去类型安全的意义
  → 超大 Schema（20+ 字段） → 模型容易漏字段
  → 没有 describe 的字段 → 模型靠猜
```

```typescript
// 好的 Schema 设计示例
const schema = z.object({
  title: z.string().describe("文章标题，简洁有力，10-30 字"),
  category: z.enum(["tech", "life", "finance"]).describe("文章分类"),
  keyPoints: z.array(z.string())
    .min(3).max(5)
    .describe("核心要点，每条 20 字以内"),
  confidence: z.number().min(0).max(1)
    .describe("分析置信度，0-1 之间的浮点数"),
  isOriginal: z.boolean().describe("是否为原创内容"),
});
// → 每个字段都有 describe + 约束 → 模型输出非常稳定
```

> 💡 **`generateObject` vs `streamObject` 的选择**：如果你需要在前端渐进式显示（比如逐步填充一个卡片），用 `streamObject`。如果是后台处理（比如数据提取后存数据库），用 `generateObject`——更简单，保证拿到完整对象。

---

## 5. Tool Calling：让 LLM 调用外部工具

LLM 只能生成文本——但现实世界需要查数据库、调 API、执行代码。Tool Calling 让模型"长出手脚"：模型决定调什么工具、传什么参数，你的代码负责执行，结果自动回传给模型继续推理。

### 5.1 Tool 定义与基本流程

```typescript
import { streamText, tool } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

const result = streamText({
  model: openai("gpt-4o"),
  messages,
  tools: {
    // 定义一个天气查询工具
    getWeather: tool({
      description: "获取指定城市的当前天气",  // 告诉模型这个工具做什么
      parameters: z.object({                   // 工具的输入参数（Zod Schema）
        city: z.string().describe("城市名称，如'北京'"),
        unit: z.enum(["celsius", "fahrenheit"]).default("celsius"),
      }),
      execute: async ({ city, unit }) => {     // 实际执行函数
        // city 和 unit 的类型从 Zod Schema 自动推导！
        const response = await fetch(`https://api.weather.com/${city}`);
        const data = await response.json();
        return {
          city,
          temperature: data.temp,
          condition: data.condition,
        };
      },
    }),
  },
});
```

```
Tool Calling 的完整流程：

  用户："北京今天天气怎么样？"
       │
       ▼
  ┌──────────────────────────┐
  │ 模型分析用户意图            │
  │ → 需要调用 getWeather 工具  │
  │ → 参数：{ city: "北京" }   │
  └──────────┬───────────────┘
             │ tool_call
             ▼
  ┌──────────────────────────┐
  │ AI SDK 自动执行 execute() │
  │ → 调用天气 API             │
  │ → 返回 { temp: 28, ... }  │
  └──────────┬───────────────┘
             │ tool_result
             ▼
  ┌──────────────────────────┐
  │ 模型拿到工具结果            │
  │ → 生成自然语言回答          │
  │ → "北京今天 28°C，晴天"    │
  └──────────────────────────┘
```

### 5.2 多步 Tool Calling：maxSteps 自动循环

```typescript
// maxSteps：允许模型多次调用工具（自动循环）
const result = streamText({
  model: openai("gpt-4o"),
  messages: [
    { role: "user", content: "比较北京和上海今天的天气" },
  ],
  tools: { getWeather },
  maxSteps: 5,                // ← 最多执行 5 轮 Tool Calling
});

// 执行流程（maxSteps = 5）：
//
// Step 1: 模型 → tool_call: getWeather({ city: "北京" })
//         SDK   → execute → { temp: 28, condition: "晴" }
//
// Step 2: 模型 → tool_call: getWeather({ city: "上海" })
//         SDK   → execute → { temp: 31, condition: "多云" }
//
// Step 3: 模型 → 生成最终回答
//         "北京 28°C 晴天，上海 31°C 多云，上海比北京热 3°C"
//
// → 模型自动决定需要几次 Tool Calling
// → AI SDK 自动管理循环，你不需要手写 while loop
```

```
maxSteps 的工作机制：

  ┌─────┐    tool_call    ┌─────────┐    tool_result    ┌─────┐
  │模型  │───────────────►│ execute │───────────────────►│模型  │
  └─────┘                 └─────────┘                    └──┬──┘
     ▲                                                      │
     │                    ┌─────────┐                       │
     └────────────────────│ 继续？   │◄──────────────────────┘
                          └────┬────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
              还需要工具              不需要了
              → 回到 Step 1           → 生成文本回答
              → 直到 maxSteps         → 结束

  maxSteps 的选择：
  1   → 单步（只允许一次 Tool Calling）
  3-5 → 常见值（大多数场景够用）
  10+ → 复杂 Agent 场景
```

### 5.3 人工审批：needsApproval 安全机制

```typescript
// 某些工具有副作用（删除数据、发邮件、转账）
// → 需要人工确认后才能执行

const result = streamText({
  model: openai("gpt-4o"),
  messages,
  tools: {
    deleteUser: tool({
      description: "从数据库中删除用户",
      parameters: z.object({
        userId: z.string().describe("要删除的用户 ID"),
        reason: z.string().describe("删除原因"),
      }),
      // ⚠️ 没有 execute 函数！
      // → 模型只会生成 tool_call，不会自动执行
      // → 前端展示确认对话框 → 用户确认后手动执行
    }),

    getUser: tool({
      description: "查询用户信息",
      parameters: z.object({ userId: z.string() }),
      execute: async ({ userId }) => {
        // 查询操作是安全的 → 有 execute → 自动执行
        return db.user.findUnique({ where: { id: userId } });
      },
    }),
  },
  maxSteps: 3,
});
```

```
有 execute vs 没有 execute 的区别：

  有 execute 的工具（自动执行）：
  → 模型发起 tool_call → AI SDK 自动调用 execute()
  → 结果自动回传给模型
  → 适合：查询、计算、无副作用的操作

  没有 execute 的工具（需要人工审批）：
  → 模型发起 tool_call → AI SDK 不执行，只返回调用信息
  → 前端展示确认 UI → 用户点"确认" → 手动执行
  → 适合：删除、修改、发送、支付等危险操作

  这就是 AI SDK 的"人工审批"（Human-in-the-Loop）机制
  → 不需要额外配置，只需要不写 execute 函数
```

### 5.4 实战：天气查询 + 数据库检索 + 代码执行

```typescript
// 完整示例：一个有多个工具的 AI 助手
import { streamText, tool } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai("gpt-4o"),
    system: "你是一个全能 AI 助手，可以查天气、查数据库、做数学计算。",
    messages,
    tools: {
      // 工具 1：天气查询
      getWeather: tool({
        description: "获取城市当前天气",
        parameters: z.object({
          city: z.string().describe("城市名"),
        }),
        execute: async ({ city }) => {
          // 实际项目中调用天气 API
          return { city, temp: 28, condition: "晴", humidity: 45 };
        },
      }),

      // 工具 2：数据库查询
      searchProducts: tool({
        description: "搜索产品数据库",
        parameters: z.object({
          query: z.string().describe("搜索关键词"),
          maxResults: z.number().default(5),
        }),
        execute: async ({ query, maxResults }) => {
          const products = await db.product.findMany({
            where: { name: { contains: query } },
            take: maxResults,
          });
          return products;
        },
      }),

      // 工具 3：数学计算
      calculate: tool({
        description: "执行数学计算表达式",
        parameters: z.object({
          expression: z.string().describe("数学表达式，如 '(100 * 1.08) + 50'"),
        }),
        execute: async ({ expression }) => {
          const result = Function(`return ${expression}`)();
          return { expression, result };
        },
      }),
    },
    maxSteps: 5,
  });

  return result.toDataStreamResponse();
}

// 用户："北京天气怎样？帮我算一下如果酒店 500 元/晚住 3 晚加 15% 服务费是多少？"
// → 模型自动调用 getWeather + calculate
// → "北京 28°C 晴天。500×3×1.15 = 1725 元。"
```

> 💡 **Tool 的 description 非常重要**：模型根据 description 决定什么时候调用哪个工具。描述不准确 → 模型选错工具或不调用。把 description 当成"工具的说明书"来写。

---

## 6. AI SDK UI：React Hooks 构建对话界面

前几章解决了后端问题——怎么调模型、怎么流式、怎么用工具。这一章解决前端问题：`useChat` 一个 Hook 搞定消息列表、流式渲染、输入框绑定、加载状态，你只管写 UI。

### 6.1 useChat：核心对话 Hook

```tsx
// app/page.tsx —— 最简聊天界面（10 行核心代码）
"use client";
import { useChat } from "ai/react";

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: "/api/chat",            // 后端 Route Handler 地址
  });

  return (
    <div>
      {/* 消息列表 */}
      {messages.map((m) => (
        <div key={m.id}>
          <b>{m.role === "user" ? "你" : "AI"}：</b>
          {m.content}
        </div>
      ))}

      {/* 输入框 */}
      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="输入消息..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? "生成中..." : "发送"}
        </button>
      </form>
    </div>
  );
}
// → useChat 自动管理：消息列表、流式更新、输入状态、请求发送
// → 你只需要写 UI 布局
```

```typescript
// useChat 返回的完整 API
const {
  // ═══ 状态 ═══
  messages,          // Message[] → 完整对话历史
  input,             // string → 输入框当前值
  isLoading,         // boolean → 是否正在生成
  error,             // Error | undefined → 最近的错误

  // ═══ 操作 ═══
  handleInputChange, // (e: ChangeEvent) → 绑定输入框 onChange
  handleSubmit,      // (e: FormEvent) → 绑定表单 onSubmit
  append,            // (message: Message) → 手动追加消息
  reload,            // () → 重新生成最后一条回复
  stop,              // () → 中断当前生成
  setMessages,       // (messages: Message[]) → 手动设置消息列表
  setInput,          // (input: string) → 手动设置输入值

  // ═══ 高级 ═══
  data,              // JSONValue[] → 服务端发送的自定义数据
  addToolResult,     // (result) → 手动提交 Tool 执行结果
} = useChat({
  api: "/api/chat",
  initialMessages: [],         // 初始消息（恢复历史对话）
  body: { modelId: "gpt-4o" }, // 每次请求附带的额外数据
  onFinish: (message) => { },  // 生成完成回调
  onError: (error) => { },     // 错误回调
});
```

### 6.2 消息渲染与流式 UI

```tsx
// 流式渲染：消息在生成过程中逐字显示
// useChat 的 messages 数组会实时更新——最后一条消息的 content 逐步增长

{messages.map((m) => (
  <div key={m.id} className={m.role === "user" ? "user-msg" : "ai-msg"}>
    <div className="avatar">{m.role === "user" ? "👤" : "🤖"}</div>
    <div className="content">
      {m.content}
      {/* 流式生成时，最后一条消息的 content 在持续更新 */}
      {/* React 自动重渲染 → 用户看到逐字出现的效果 */}
    </div>
  </div>
))}

{/* 打字指示器：AI 正在思考 */}
{isLoading && (
  <div className="typing-indicator">
    <span>AI 正在思考</span>
    <span className="dots">...</span>
  </div>
)}
```

```
useChat 的消息流更新机制：

  用户点击"发送"
       │
       ▼
  messages 追加 user 消息
  → [{ role: "user", content: "你好" }]
       │
       ▼
  发送 POST /api/chat
  → isLoading = true
       │
       ▼
  后端 streamText 流式返回
  → messages 追加空的 assistant 消息
  → [{ role: "user", ... }, { role: "assistant", content: "" }]
       │
       ▼
  每收到一个 chunk → 更新 assistant.content
  → content: "你"
  → content: "你好"
  → content: "你好！"
  → content: "你好！有什么..."
  → React 自动重渲染 → 用户看到打字效果
       │
       ▼
  流结束
  → isLoading = false
```

### 6.3 useCompletion：单轮补全场景

```tsx
// useCompletion 适合"一问一答"场景——不维护对话历史
"use client";
import { useCompletion } from "ai/react";

export default function TranslatorPage() {
  const { completion, input, handleInputChange, handleSubmit, isLoading } =
    useCompletion({
      api: "/api/translate",
    });

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <textarea
          value={input}
          onChange={handleInputChange}
          placeholder="输入要翻译的文本..."
        />
        <button type="submit">翻译</button>
      </form>

      {/* completion 是一个字符串，不是消息数组 */}
      {completion && <div className="result">{completion}</div>}
    </div>
  );
}
```

```
useChat vs useCompletion 的选择：

  useChat（多轮对话）
  → 维护 messages 数组（完整对话历史）
  → 每次请求发送所有历史消息
  → 适合：聊天机器人、客服、AI 助手

  useCompletion（单轮补全）
  → 只有 completion 字符串（单次结果）
  → 每次请求只发送当前输入
  → 适合：翻译、摘要、代码生成、一次性任务
```

### 6.4 自定义消息组件与 Markdown 渲染

```tsx
// AI 回复通常包含 Markdown（标题、代码块、列表）
// 用 react-markdown 渲染
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

function MessageBubble({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="user-bubble">
        <p>{message.content}</p>
      </div>
    );
  }

  // AI 消息：渲染 Markdown + 代码高亮
  return (
    <div className="ai-bubble">
      <ReactMarkdown
        components={{
          // 自定义代码块渲染（语法高亮）
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            return match ? (
              <SyntaxHighlighter style={oneDark} language={match[1]}>
                {String(children).replace(/\n$/, "")}
              </SyntaxHighlighter>
            ) : (
              <code className={className} {...props}>{children}</code>
            );
          },
        }}
      >
        {message.content}
      </ReactMarkdown>
    </div>
  );
}
```

### 6.5 错误处理、重试与加载状态

```tsx
// 完整的错误处理 + 重试 + 中断
"use client";
import { useChat } from "ai/react";

export default function Chat() {
  const {
    messages, input, handleInputChange, handleSubmit,
    isLoading, error, reload, stop,
  } = useChat({
    api: "/api/chat",
    onError: (err) => {
      console.error("Chat error:", err);
      // 可以在这里上报到监控系统
    },
  });

  return (
    <div>
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}

      {/* 错误状态 */}
      {error && (
        <div className="error-banner">
          <span>⚠️ 生成失败：{error.message}</span>
          <button onClick={() => reload()}>重试</button>
          {/* reload() → 重新发送最后一条用户消息 */}
        </div>
      )}

      {/* 加载状态 + 中断按钮 */}
      {isLoading && (
        <button onClick={() => stop()} className="stop-btn">
          ⏹ 停止生成
          {/* stop() → 中断当前流式生成，保留已生成的内容 */}
        </button>
      )}

      <form onSubmit={handleSubmit}>
        <input value={input} onChange={handleInputChange} />
        <button type="submit" disabled={isLoading}>发送</button>
      </form>
    </div>
  );
}
```

> 💡 **`reload()` vs `stop()`**：`stop()` 中断生成但保留已有内容，`reload()` 删除最后一条 AI 回复并重新请求。用户点"重试"用 `reload()`，用户觉得回答够了点"停止"用 `stop()`。

---

## 7. Generative UI：流式渲染 React 组件

传统聊天机器人只能返回文本。Generative UI 更进一步——模型不只决定"说什么"，还决定"渲染什么 UI"。调用天气工具就渲染天气卡片，查询股票就渲染图表，搜索商品就渲染产品列表。

### 7.1 Generative UI 概念：模型驱动的界面

```
传统 Chat vs Generative UI：

  传统 Chat：
  用户："北京天气怎么样？"
  AI：  "北京今天 28°C，晴天，湿度 45%"  ← 纯文本

  Generative UI：
  用户："北京天气怎么样？"
  AI：  ┌─────────────────────────┐
        │ 🌤️ 北京 · 晴天            │
        │                          │
        │    28°C                   │
        │    湿度 45% · 风力 3 级    │
        │    ──────────────────     │
        │    📊 未来 7 天趋势        │
        └─────────────────────────┘
        ← 渲染了一个天气卡片组件！

  核心思想：
  → 模型调用 Tool → Tool 返回数据 → 数据映射为 React 组件
  → 模型不直接生成 UI，而是通过 Tool Calling 间接驱动 UI
```

### 7.2 Tool 结果映射为 React 组件

```tsx
// 前端：根据 Tool 调用渲染对应的 React 组件
"use client";
import { useChat } from "ai/react";

// 天气卡片组件
function WeatherCard({ data }: { data: { city: string; temp: number; condition: string } }) {
  return (
    <div className="weather-card">
      <h3>🌤️ {data.city}</h3>
      <div className="temp">{data.temp}°C</div>
      <div className="condition">{data.condition}</div>
    </div>
  );
}

// 产品列表组件
function ProductList({ data }: { data: Array<{ name: string; price: number }> }) {
  return (
    <div className="product-list">
      {data.map((p, i) => (
        <div key={i} className="product-item">
          <span>{p.name}</span>
          <span className="price">¥{p.price}</span>
        </div>
      ))}
    </div>
  );
}

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit } = useChat();

  return (
    <div>
      {messages.map((m) => (
        <div key={m.id}>
          {/* 渲染文本部分 */}
          {m.content && <p>{m.content}</p>}

          {/* 渲染 Tool 调用结果为 UI 组件 */}
          {m.toolInvocations?.map((tool, i) => {
            if (tool.state !== "result") return null;

            // 根据工具名称渲染不同组件
            switch (tool.toolName) {
              case "getWeather":
                return <WeatherCard key={i} data={tool.result} />;
              case "searchProducts":
                return <ProductList key={i} data={tool.result} />;
              default:
                return <pre key={i}>{JSON.stringify(tool.result)}</pre>;
            }
          })}
        </div>
      ))}

      <form onSubmit={handleSubmit}>
        <input value={input} onChange={handleInputChange} />
        <button type="submit">发送</button>
      </form>
    </div>
  );
}
```

### 7.3 多部分消息的流式渲染

```
一条 AI 消息可能包含多个部分（multi-part message）：

  用户："北京天气怎么样？推荐几个室外活动。"

  AI 回复的消息结构：
  ┌──────────────────────────────────────────┐
  │ Part 1: text                              │
  │ "让我查一下北京的天气..."                   │
  ├──────────────────────────────────────────┤
  │ Part 2: tool_call                         │
  │ { toolName: "getWeather", args: {...} }   │
  ├──────────────────────────────────────────┤
  │ Part 3: tool_result                       │
  │ { city: "北京", temp: 28, ... }           │
  ├──────────────────────────────────────────┤
  │ Part 4: text                              │
  │ "北京 28°C 晴天，非常适合户外活动！推荐：..."│
  └──────────────────────────────────────────┘

  → 一条消息里混合了文本 + 工具调用 + 工具结果 + 更多文本
  → 前端需要按顺序渲染每个 Part
```

```tsx
// 渲染多部分消息的完整模式
function AIMessage({ message }: { message: Message }) {
  return (
    <div className="ai-message">
      {/* 1. 渲染文本内容 */}
      {message.content && (
        <ReactMarkdown>{message.content}</ReactMarkdown>
      )}

      {/* 2. 渲染 Tool 调用（按状态区分） */}
      {message.toolInvocations?.map((tool, i) => {
        // 工具正在执行（还没有结果）
        if (tool.state === "call") {
          return (
            <div key={i} className="tool-loading">
              🔄 正在调用 {tool.toolName}...
            </div>
          );
        }
        // 工具执行完毕（有结果）
        if (tool.state === "result") {
          return renderToolResult(tool.toolName, tool.result, i);
        }
        return null;
      })}
    </div>
  );
}

// 根据工具名渲染对应组件
function renderToolResult(name: string, result: unknown, key: number) {
  const components: Record<string, React.FC<{ data: any }>> = {
    getWeather:      WeatherCard,
    searchProducts:  ProductList,
    getStockPrice:   StockChart,
  };
  const Component = components[name];
  return Component
    ? <Component key={key} data={result} />
    : <pre key={key}>{JSON.stringify(result, null, 2)}</pre>;
}
```

### 7.4 实战：动态卡片 + 图表 + 表单

```tsx
// 实战示例：股票查询 → 渲染交互式图表
function StockChart({ data }: { data: { symbol: string; prices: number[] } }) {
  return (
    <div className="stock-card">
      <h3>📈 {data.symbol}</h3>
      <div className="chart">
        {/* 使用 recharts 或其他图表库渲染 */}
        {data.prices.map((p, i) => (
          <div key={i} className="bar" style={{ height: `${p / 10}px` }} />
        ))}
      </div>
      <div className="actions">
        <button>查看详情</button>
        <button>添加自选</button>
      </div>
    </div>
  );
}

// 实战示例：AI 生成表单 → 用户可交互
function BookingForm({ data }: { data: { hotel: string; dates: string[] } }) {
  const [guests, setGuests] = useState(1);
  return (
    <div className="booking-card">
      <h3>🏨 {data.hotel}</h3>
      <p>日期：{data.dates.join(" → ")}</p>
      <label>
        入住人数：
        <select value={guests} onChange={(e) => setGuests(+e.target.value)}>
          {[1, 2, 3, 4].map((n) => <option key={n} value={n}>{n}人</option>)}
        </select>
      </label>
      <button>确认预订</button>
    </div>
  );
}
```

```
Generative UI 的最佳实践：

  ✅ 1. 每个 Tool 对应一个 UI 组件
  → getWeather → WeatherCard
  → searchProducts → ProductList
  → getStockPrice → StockChart

  ✅ 2. 组件要有 Loading 状态
  → tool.state === "call" 时显示骨架屏
  → tool.state === "result" 时渲染完整组件

  ✅ 3. 组件可交互
  → 不只是展示数据，还能有按钮、表单
  → 用户在 UI 组件上的操作可以触发新的对话

  ✅ 4. 兜底渲染
  → 未知 Tool 用 JSON.stringify 兜底
  → 不要因为缺少组件映射就报错
```

> 💡 **Generative UI 是 AI 应用的未来方向**：用户不再只是和文字聊天，而是和动态 UI 交互。模型成为了"UI 的路由器"——根据用户意图选择最合适的交互方式。

---

## 8. 多模态：图片、PDF 与语音

LLM 不再只看文字——GPT-4o 能看图、Gemini 能读 PDF、Claude 能处理超长文档。AI SDK 用统一的消息格式处理所有多模态输入。

### 8.1 图片理解：Vision 模型集成

```typescript
// 发送图片给模型（Vision 能力）
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";

const { text } = await generateText({
  model: openai("gpt-4o"),             // GPT-4o 支持视觉
  messages: [
    {
      role: "user",
      content: [
        { type: "text", text: "这张图里有什么？" },
        {
          type: "image",
          image: new URL("https://example.com/photo.jpg"),
          // 也支持：
          // image: Buffer.from(...)       ← Node.js Buffer
          // image: fs.readFileSync(...)   ← 本地文件
          // image: "data:image/png;base64,..." ← Base64
        },
      ],
    },
  ],
});
// → "这张图展示了一座雪山，前方有一片湖泊..."
```

### 8.2 PDF 文档解析与问答

```typescript
// 发送 PDF 给模型（部分模型原生支持）
import { generateText } from "ai";
import { google } from "@ai-sdk/google";
import fs from "fs";

const pdfBuffer = fs.readFileSync("./report.pdf");

const { text } = await generateText({
  model: google("gemini-2.5-pro"),      // Gemini 原生支持 PDF
  messages: [
    {
      role: "user",
      content: [
        { type: "text", text: "总结这份报告的核心观点" },
        {
          type: "file",
          data: pdfBuffer,
          mimeType: "application/pdf",   // 指定 MIME 类型
        },
      ],
    },
  ],
});
```

### 8.3 文件上传与多模态消息构建

```typescript
// Next.js 前端上传图片 → 发送给 AI
// app/api/chat/route.ts
export async function POST(req: Request) {
  const formData = await req.formData();
  const image = formData.get("image") as File;
  const prompt = formData.get("prompt") as string;

  const imageBuffer = Buffer.from(await image.arrayBuffer());

  const result = streamText({
    model: openai("gpt-4o"),
    messages: [
      {
        role: "user",
        content: [
          { type: "text", text: prompt },
          { type: "image", image: imageBuffer },
        ],
      },
    ],
  });

  return result.toDataStreamResponse();
}
```

### 8.4 语音集成思路：STT / TTS

```
语音 + AI SDK 的集成架构：

  用户说话
     │
     ▼
  浏览器 Web Speech API / Whisper
  → 语音转文字（STT）
     │
     ▼
  useChat({ ... })
  → 发送文字给 AI → 获取文字回复
     │
     ▼
  Web Speech API / OpenAI TTS
  → 文字转语音（TTS）
     │
     ▼
  播放给用户

  → AI SDK 负责中间的"文字对话"部分
  → STT/TTS 用浏览器原生 API 或 OpenAI 接口
  → 两者组合 = 语音 AI 助手
```

> 💡 **多模态消息的关键**：`content` 字段从 `string` 变成了 `Array<Part>`——可以混合 text、image、file 多种类型。这是 AI SDK 的统一多模态格式，所有 Provider 都支持。

---

## 9. Agent 构建：从对话到自主执行

Chat 是"你问我答"，Agent 是"你说目标，我自己想办法"。Agent 能自主决策调用哪些工具、按什么顺序执行、什么时候该停下来——而 AI SDK 的 `streamText` + `maxSteps` 就是构建 Agent 的基础设施。

### 9.1 Agent = 指令 + 工具 + 循环

```
Agent 的三要素：

  ┌─────────────────────────────────────────┐
  │                Agent                     │
  │                                          │
  │  ┌────────────┐                          │
  │  │  指令       │ System Prompt            │
  │  │  (Identity) │ → 你是谁、你的目标、规则  │
  │  └────────────┘                          │
  │                                          │
  │  ┌────────────┐                          │
  │  │  工具       │ Tools                    │
  │  │  (Actions)  │ → 你能做什么操作          │
  │  └────────────┘                          │
  │                                          │
  │  ┌────────────┐                          │
  │  │  循环       │ maxSteps                 │
  │  │  (Loop)     │ → 持续推理直到任务完成    │
  │  └────────────┘                          │
  └─────────────────────────────────────────┘

  Chat：用户说一句 → 模型回一句 → 结束
  Agent：用户说目标 → 模型思考 → 调工具 → 看结果
         → 继续思考 → 再调工具 → ... → 任务完成
```

### 9.2 用 streamText + maxSteps 构建 Agent

```typescript
// 完整示例：一个研究助手 Agent
import { streamText, tool } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai("gpt-4o"),
    system: `你是一个研究助手 Agent。
当用户提出研究问题时，你应该：
1. 先用搜索工具查找相关资料
2. 如果信息不足，继续搜索更具体的关键词
3. 汇总所有搜索结果，给出结构化的研究报告
4. 报告需包含：摘要、关键发现、数据来源`,
    messages,
    tools: {
      webSearch: tool({
        description: "搜索互联网获取最新信息",
        parameters: z.object({
          query: z.string().describe("搜索关键词"),
        }),
        execute: async ({ query }) => {
          // 实际项目中调用搜索 API（如 Serper / Tavily）
          const results = await searchAPI(query);
          return results;
        },
      }),
      readPage: tool({
        description: "读取网页的详细内容",
        parameters: z.object({
          url: z.string().url().describe("要读取的网页 URL"),
        }),
        execute: async ({ url }) => {
          const content = await fetchPageContent(url);
          return { url, content: content.slice(0, 3000) };
        },
      }),
      saveNote: tool({
        description: "保存研究笔记到数据库",
        parameters: z.object({
          title: z.string(),
          content: z.string(),
          sources: z.array(z.string().url()),
        }),
        execute: async (note) => {
          await db.note.create({ data: note });
          return { saved: true };
        },
      }),
    },
    maxSteps: 10,               // Agent 最多执行 10 步
    onFinish: ({ steps, usage }) => {
      console.log(`Agent 执行了 ${steps.length} 步`);
      console.log(`总消耗 ${usage.totalTokens} tokens`);
    },
  });

  return result.toDataStreamResponse();
}
// 用户："帮我调研 2025 年 TypeScript 的最新特性"
// Agent 自动执行：
//   Step 1: webSearch("TypeScript 2025 new features")
//   Step 2: readPage("https://devblogs.microsoft.com/...")
//   Step 3: webSearch("TypeScript 5.8 release notes")
//   Step 4: saveNote({ title: "TypeScript 2025 调研", ... })
//   Step 5: 生成完整研究报告
```

### 9.3 MCP 集成：连接外部数据源

```typescript
// MCP（Model Context Protocol）：让 Agent 连接外部工具和数据
// AI SDK 通过 @ai-sdk/mcp 包提供原生 MCP 支持

import { streamText } from "ai";
import { openai } from "@ai-sdk/openai";
import { experimental_createMCPClient as createMCPClient } from "ai";

// 连接 MCP Server
const mcpClient = await createMCPClient({
  transport: {
    type: "sse",                     // SSE 传输（HTTP）
    url: "http://localhost:3001/mcp", // MCP Server 地址
  },
});

// 获取 MCP Server 提供的工具
const mcpTools = await mcpClient.tools();

const result = streamText({
  model: openai("gpt-4o"),
  messages,
  tools: {
    ...mcpTools,                     // ← MCP 工具自动注入
    // 也可以和本地工具混合使用
    calculate: tool({ ... }),
  },
  maxSteps: 5,
});
```

```
MCP 的价值——工具复用：

  没有 MCP：
  → 每个应用都要自己实现工具（查数据库、读文件、调 API）
  → 工具逻辑分散在各个项目中
  → 不同 AI 客户端不能共享工具

  有了 MCP：
  → 工具逻辑写在 MCP Server 中（一次编写）
  → 任何支持 MCP 的客户端都能用（Claude、Cursor、你的应用）
  → AI SDK 用 @ai-sdk/mcp 自动发现和调用 MCP 工具

  MCP Server 示例：
  → 文件系统 MCP → 读写本地文件
  → 数据库 MCP   → 查询 PostgreSQL / MongoDB
  → GitHub MCP   → 搜索仓库、创建 Issue
  → Slack MCP    → 发消息、读频道
```

### 9.4 Agent 状态管理与会话记忆

```typescript
// Agent 需要"记忆"——跨请求保持上下文
// 方案 1：数据库持久化消息历史

import { streamText, Message } from "ai";

export async function POST(req: Request) {
  const { messages, sessionId } = await req.json();

  // 从数据库加载历史消息
  const history = await db.message.findMany({
    where: { sessionId },
    orderBy: { createdAt: "asc" },
  });

  const result = streamText({
    model: openai("gpt-4o"),
    system: "你是一个记忆力很好的助手...",
    messages: [...history, ...messages],  // 历史 + 新消息
    maxSteps: 5,
    tools: { ... },
    onFinish: async ({ text, steps }) => {
      // 生成完成后保存到数据库
      for (const step of steps) {
        await db.message.create({
          data: {
            sessionId,
            role: step.role,
            content: step.content,
          },
        });
      }
    },
  });

  return result.toDataStreamResponse();
}
```

```
Agent 记忆的三个层次：

  短期记忆（Session Memory）
  → 当前对话的消息历史
  → 用 useChat 的 messages 数组管理
  → 页面刷新就丢失

  长期记忆（Persistent Memory）
  → 存数据库（PostgreSQL / Redis）
  → 跨会话保持
  → 用 sessionId 关联

  工作记忆（Working Memory）
  → Agent 执行过程中的中间状态
  → 比如搜索了哪些关键词、读了哪些页面
  → 由 maxSteps 循环内的 steps 数组自动管理
```

### 9.5 多 Agent 协作与任务路由

```typescript
// 多 Agent 模式：不同 Agent 处理不同类型的任务
// 路由 Agent（Router）根据用户意图分发给专业 Agent

import { generateText, streamText, tool } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

// 路由 Agent：分析用户意图，选择专业 Agent
async function routeToAgent(userMessage: string) {
  const { object } = await generateObject({
    model: openai("gpt-4o-mini"),      // 路由用便宜模型
    schema: z.object({
      agent: z.enum(["coder", "researcher", "writer"]),
      reason: z.string(),
    }),
    prompt: `分析用户意图，选择合适的 Agent：
    - coder: 代码编写、调试、技术问题
    - researcher: 信息搜索、数据分析、调研
    - writer: 文案创作、翻译、摘要
    
    用户消息：${userMessage}`,
  });
  return object.agent;
}

// 专业 Agent 定义
const agents = {
  coder: {
    system: "你是一个高级程序员...",
    tools: { runCode, searchDocs, generateTests },
    model: openai("gpt-4o"),
  },
  researcher: {
    system: "你是一个研究分析师...",
    tools: { webSearch, readPage, saveNote },
    model: openai("gpt-4o"),
  },
  writer: {
    system: "你是一个专业文案...",
    tools: { translateText, summarize },
    model: anthropic("claude-4-sonnet"), // 写作用 Claude 更好
  },
};

// 执行路由
export async function POST(req: Request) {
  const { messages } = await req.json();
  const lastMessage = messages[messages.length - 1].content;

  const agentName = await routeToAgent(lastMessage);
  const agent = agents[agentName];

  const result = streamText({
    model: agent.model,
    system: agent.system,
    messages,
    tools: agent.tools,
    maxSteps: 8,
  });

  return result.toDataStreamResponse();
}
```

```
多 Agent 架构模式：

  模式 1：路由分发（Router Pattern）
  ──────────────────────────────────
  用户 → Router Agent → Coder Agent
                      → Researcher Agent
                      → Writer Agent
  → 适合：多技能 AI 助手

  模式 2：流水线（Pipeline Pattern）
  ──────────────────────────────────
  用户 → Researcher Agent → Writer Agent → 输出
       （搜索资料）         （撰写报告）
  → 适合：多步骤任务

  模式 3：监督者（Supervisor Pattern）
  ──────────────────────────────────
  Supervisor Agent
    ├─ 分配任务给 Worker Agent A
    ├─ 分配任务给 Worker Agent B
    └─ 汇总结果 → 输出
  → 适合：并行处理、复杂推理
```

> 💡 **Agent 是 AI SDK 的终极形态**：从简单的 `streamText` 开始，加上 Tools 变成 Tool Calling，加上 `maxSteps` 变成 Agent 循环，加上 Router 变成多 Agent 系统。整个进化过程是渐进式的，你不需要一步到位。

---

## 10. 生产部署与最佳实践

Demo 跑通很容易，上线才是真功夫。这一章覆盖 API 安全、成本控制、可观测性和常见踩坑——让你的 AI 应用从"能用"变成"好用"。

### 10.1 Next.js Route Handler 集成

```typescript
// app/api/chat/route.ts —— 生产级 Route Handler 模板
import { streamText } from "ai";
import { openai } from "@ai-sdk/openai";
import { auth } from "@/lib/auth";  // 你的认证模块

export const runtime = "edge";       // 使用 Edge Runtime（更快的冷启动）

export async function POST(req: Request) {
  // 1. 认证
  const session = await auth();
  if (!session?.user) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  // 2. 解析请求
  const { messages, modelId } = await req.json();

  // 3. 输入验证
  if (!messages || !Array.isArray(messages) || messages.length === 0) {
    return Response.json({ error: "Invalid messages" }, { status: 400 });
  }

  // 4. 调用模型
  const result = streamText({
    model: openai(modelId || "gpt-4o"),
    system: "你是一个有帮助的 AI 助手...",
    messages,
    maxTokens: 4096,
    onFinish: async ({ text, usage }) => {
      // 5. 记录日志
      await db.chatLog.create({
        data: {
          userId: session.user.id,
          model: modelId,
          promptTokens: usage.promptTokens,
          completionTokens: usage.completionTokens,
          createdAt: new Date(),
        },
      });
    },
  });

  return result.toDataStreamResponse();
}
```

### 10.2 API 安全：认证与限流

```typescript
// 限流中间件（基于 Upstash Redis）
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(20, "1 h"),  // 每小时 20 次
});

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  // 限流检查
  const { success, remaining } = await ratelimit.limit(session.user.id);
  if (!success) {
    return Response.json(
      { error: "Rate limit exceeded. Try again later." },
      { status: 429, headers: { "X-RateLimit-Remaining": String(remaining) } }
    );
  }

  // ... 正常处理
}
```

```
生产 API 安全检查清单：

  ✅ 认证（Authentication）
  → 每个请求验证用户身份
  → JWT / Session / API Key

  ✅ 限流（Rate Limiting）
  → 防止用户刷爆你的 API（和 OpenAI 账单）
  → 推荐 Upstash Ratelimit（Serverless 友好）

  ✅ 输入验证（Input Validation）
  → 验证 messages 格式
  → 限制消息长度（防止超大 prompt）
  → 过滤敏感内容

  ✅ 成本保护（Cost Guard）
  → 设置 maxTokens 上限
  → 监控用户级别的 Token 消耗
  → 设置月度预算告警
```

### 10.3 Token 追踪与成本控制

```typescript
// 每次请求记录 Token 消耗
const result = streamText({
  model: openai("gpt-4o"),
  messages,
  onFinish: async ({ usage, finishReason }) => {
    // usage 包含详细的 Token 统计
    const cost = calculateCost("gpt-4o", usage);

    await db.usageLog.create({
      data: {
        userId: session.user.id,
        model: "gpt-4o",
        promptTokens: usage.promptTokens,
        completionTokens: usage.completionTokens,
        totalTokens: usage.totalTokens,
        estimatedCost: cost,          // 单位：美元
        finishReason,
        createdAt: new Date(),
      },
    });
  },
});

// 成本计算函数
function calculateCost(model: string, usage: TokenUsage): number {
  const pricing: Record<string, { input: number; output: number }> = {
    "gpt-4o":      { input: 2.5 / 1_000_000,  output: 10 / 1_000_000 },
    "gpt-4o-mini": { input: 0.15 / 1_000_000, output: 0.6 / 1_000_000 },
    "claude-4-sonnet": { input: 3 / 1_000_000, output: 15 / 1_000_000 },
  };
  const p = pricing[model] ?? pricing["gpt-4o"];
  return usage.promptTokens * p.input + usage.completionTokens * p.output;
}
```

```
成本控制策略：

  策略 1：分级模型
  → 简单问题用 gpt-4o-mini（便宜 20 倍）
  → 复杂问题才用 gpt-4o
  → 分类任务用 enum 模式（最省钱）

  策略 2：用户配额
  → 免费用户：每天 20 次 / gpt-4o-mini
  → 付费用户：每天 200 次 / gpt-4o
  → 超出配额返回 429

  策略 3：Prompt 优化
  → 精简 system prompt（少说废话）
  → 消息历史只保留最近 N 条（滑动窗口）
  → 用摘要替代完整历史
```

### 10.4 可观测性：日志、追踪与监控

```typescript
// 使用 onFinish + onStepFinish 实现全链路追踪
const result = streamText({
  model: openai("gpt-4o"),
  messages,
  tools: { ... },
  maxSteps: 5,

  // 每一步执行完毕的回调
  onStepFinish: ({ stepType, text, toolCalls, toolResults, usage }) => {
    console.log(`[Step] type=${stepType}`);
    if (toolCalls) {
      for (const tc of toolCalls) {
        console.log(`  Tool: ${tc.toolName}(${JSON.stringify(tc.args)})`);
      }
    }
    console.log(`  Tokens: ${usage.totalTokens}`);
  },

  // 全部完成的回调
  onFinish: ({ text, steps, usage, finishReason }) => {
    console.log(`[Done] steps=${steps.length}, tokens=${usage.totalTokens}`);
    // 上报到监控系统（Datadog / Sentry / 自建）
    metrics.record({
      model: "gpt-4o",
      steps: steps.length,
      totalTokens: usage.totalTokens,
      latencyMs: Date.now() - startTime,
      finishReason,
    });
  },
});
```

```
AI 应用的可观测性三支柱：

  📝 日志（Logs）
  → 每次请求的 prompt / response / usage
  → Tool Calling 的参数和结果
  → 错误和异常

  📊 指标（Metrics）
  → 请求量 / 成功率 / 延迟分布
  → Token 消耗趋势
  → 模型成本 / 用户

  🔗 追踪（Traces）
  → 一次 Agent 执行的完整链路
  → 每个 Step 的耗时和结果
  → 推荐工具：Langfuse / Helicone / Vercel AI Observability
```

### 10.5 常见问题与 FAQ

```
Q1: useChat 的流式响应在 Vercel 部署后不工作？
─────────────────────────────────────────────
→ 检查是否设置了 export const runtime = "edge"
→ Node.js Runtime 的流式响应可能被 CDN 缓冲
→ Edge Runtime 没有这个问题

Q2: Tool Calling 不触发，模型直接回答了？
─────────────────────────────────────────────
→ 检查 Tool 的 description 是否足够清晰
→ 模型根据 description 决定是否调用工具
→ 试试在 system prompt 中明确指示"请使用工具"

Q3: generateObject 返回不符合 Schema 的数据？
─────────────────────────────────────────────
→ 换用更强的模型（gpt-4o 比 gpt-4o-mini 更可靠）
→ 简化 Schema（减少嵌套层级）
→ 给每个字段加 .describe() 描述
→ 使用 OpenAI 的 structuredOutputs: true 选项

Q4: 流式生成中断后如何恢复？
─────────────────────────────────────────────
→ useChat 的 reload() 方法可以重新生成最后一条
→ 网络中断时 onError 会触发
→ 可以在 onError 中自动 reload()（但注意防止无限循环）

Q5: 消息历史太长导致 Token 超限？
─────────────────────────────────────────────
→ 只发送最近 N 条消息（滑动窗口）
→ 用 generateText 生成历史摘要替代原始消息
→ 监控 usage.promptTokens，超阈值自动截断

Q6: 多模型切换时类型不兼容？
─────────────────────────────────────────────
→ 使用 LanguageModel 类型（从 ai 包导入）
→ 所有 Provider 返回的模型都实现了这个接口
→ const model: LanguageModel = openai("gpt-4o")
```

---
