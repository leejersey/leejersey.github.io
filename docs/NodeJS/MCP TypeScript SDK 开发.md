# MCP TypeScript SDK 开发

> 用 TypeScript 从零构建 MCP Server——掌握 @modelcontextprotocol/sdk 的 Tool/Resource/Prompt 三大原语、Stdio/HTTP 双传输层、Zod Schema 验证、与 Claude/Cursor 集成调试的完整开发流程。

---

## 1. MCP 协议速览：为什么 AI 需要标准化工具接口

### 1.1 从 Function Calling 到 MCP：工具标准化之路

```
AI 工具调用的碎片化问题：

  OpenAI Function Calling：
  → 只适用于 OpenAI 模型
  → 工具定义用 JSON Schema
  → 每个应用自己实现工具执行

  Anthropic Tool Use：
  → 只适用于 Claude 模型
  → 格式和 OpenAI 不完全一样
  → 又是一套独立实现

  问题：
  → 你写了一个"查天气"工具，给 OpenAI 用了
  → 想给 Claude 也用？→ 重写一遍
  → 想给 Cursor/Windsurf 也用？→ 再写一遍
  → N 个模型 × M 个工具 = N×M 种适配 💀

  MCP 的解法：
  → 定义一个标准协议（Model Context Protocol）
  → 工具写一次，所有支持 MCP 的客户端都能用
  → N + M 替代 N × M
```

```
Function Calling vs MCP 对比：

  维度              Function Calling         MCP
  ────────────────────────────────────────────────────
  标准化            ❌ 各厂商格式不同        ✅ 统一协议
  工具复用          ❌ 跨模型要重写          ✅ 写一次到处用
  运行方式          应用内执行               独立进程/服务
  能力范围          只有 Tool                Tool + Resource + Prompt
  传输层            HTTP API                 Stdio / HTTP
  生态              各厂商封闭               开放标准，社区共建
  典型场景          单模型应用               多客户端通用工具
```

### 1.2 MCP 架构：Host / Client / Server

```
MCP 三角色架构：

  ┌─────────────────────────────────────────────┐
  │                Host（宿主）                   │
  │     Claude Desktop / Cursor / Windsurf       │
  │                                              │
  │   ┌──────────┐  ┌──────────┐                │
  │   │ MCP      │  │ MCP      │  ← 每个 Server │
  │   │ Client 1 │  │ Client 2 │    对应一个     │
  │   └────┬─────┘  └────┬─────┘    Client      │
  └────────┼──────────────┼─────────────────────┘
           │              │
     Stdio/HTTP      Stdio/HTTP
           │              │
  ┌────────┴─────┐ ┌──────┴──────┐
  │  MCP Server  │ │  MCP Server │
  │  天气查询     │ │  数据库操作  │
  │  (你写的)     │ │  (你写的)    │
  └──────────────┘ └─────────────┘

  Host: AI 应用（Claude Desktop、Cursor 等）
  Client: Host 内部的 MCP 客户端（自动管理）
  Server: 你开发的工具服务（独立进程）
```

```
MCP Server 暴露三种能力（三大原语）：

  原语          作用                  类比
  ─────────────────────────────────────────
  Tool          让 AI 调用函数        Function Calling
  Resource      让 AI 读取数据        GET API / 文件系统
  Prompt        可复用的交互模板      Prompt 模板库

  Tool → AI 主动调用（"帮我查天气"）
  Resource → AI 主动读取（"读取这个文件的内容"）
  Prompt → 用户选择触发（"用代码审查模板"）
```

### 1.3 TypeScript SDK 定位与生态

```
MCP SDK 生态：

  语言          包名                          适合场景
  ──────────────────────────────────────────────────────
  TypeScript    @modelcontextprotocol/sdk     Node.js 生态、Web 开发者
  Python        mcp                           AI/ML 生态、数据科学
  Kotlin        io.modelcontextprotocol:sdk   Android/JVM 生态
  C#            ModelContextProtocol          .NET 生态

  TypeScript SDK 的优势：
  → Zod Schema 验证（类型安全 + 运行时校验）
  → npm 生态（npx 一键运行）
  → 与 Node.js 工具链无缝集成
  → 前后端同构（同一语言覆盖 Server + Client）
```

> 💡 **一句话理解 MCP**：MCP 就是 AI 世界的 USB-C——不管什么设备（AI 客户端），插上就能用你的工具，不需要为每个设备写专用驱动。

---

## 2. 环境搭建与 Hello MCP

### 2.1 项目初始化与依赖安装

```bash
# 创建项目
mkdir my-mcp-server && cd my-mcp-server
npm init -y

# 安装核心依赖
npm i @modelcontextprotocol/sdk zod
# → @modelcontextprotocol/sdk: MCP 协议实现
# → zod: 参数 Schema 定义（必装，SDK 依赖它）

# 安装开发依赖
npm i -D typescript @types/node tsx
npx tsc --init
```

```json
// tsconfig.json 关键配置
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

### 2.2 McpServer 高阶 API vs Server 底层 API

```
SDK 提供两层 API：

  ┌─────────────────────────────────────────┐
  │  McpServer（高阶 API）← 推荐            │
  │  自动处理：能力协商、请求路由、输入校验   │
  │  你只需要：注册 Tool/Resource/Prompt     │
  └────────────────────┬────────────────────┘
                       │ 基于
  ┌────────────────────┴────────────────────┐
  │  Server（底层 API）                      │
  │  手动处理：所有协议细节                   │
  │  适合：自定义协议扩展、极致性能优化       │
  └─────────────────────────────────────────┘

  选型建议：
  → 99% 场景用 McpServer（本教程主要使用）
  → 只有做协议级扩展时才用 Server
```

### 2.3 第一个 Tool：Hello MCP

```typescript
// src/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// 1. 创建 MCP Server 实例
const server = new McpServer({
  name: "hello-mcp",        // Server 名称（客户端显示用）
  version: "1.0.0",         // 版本号
});

// 2. 注册一个 Tool
server.tool(
  "greet",                              // Tool 名称
  "向某人打招呼",                         // Tool 描述（AI 用这个决定何时调用）
  {
    name: z.string().describe("要打招呼的人名"),
  },
  async ({ name }) => {                  // Tool 执行函数
    return {
      content: [
        { type: "text", text: `你好，${name}！欢迎使用 MCP！` },
      ],
    };
  },
);

// 3. 启动 Server（Stdio 传输）
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Server 已启动");    // 注意：用 stderr，stdout 留给协议通信
}
main();
```

```bash
# 运行测试
npx tsx src/index.ts
# → Server 启动，等待 Stdio 输入（此时看不到输出是正常的）
# → 需要用 MCP 客户端或 mcp-inspector 来交互
```

### 2.4 用 mcp-inspector 调试

```bash
# 安装 MCP Inspector（官方调试工具）
npx @modelcontextprotocol/inspector npx tsx src/index.ts

# → 浏览器自动打开调试界面
# → 可以看到注册的 Tools 列表
# → 可以手动输入参数调用 Tool
# → 查看请求/响应的完整 JSON
```

```
mcp-inspector 调试界面功能：

  ┌─────────────────────────────────────┐
  │  MCP Inspector                      │
  ├─────────────────────────────────────┤
  │  📋 Tools        → 查看所有 Tool    │
  │  📁 Resources    → 查看所有 Resource│
  │  💬 Prompts      → 查看所有 Prompt  │
  │  🔍 Test Tool    → 输入参数测试调用  │
  │  📝 Protocol Log → 查看协议日志      │
  └─────────────────────────────────────┘

  → 开发阶段必用的调试工具
  → 比直接连 Claude Desktop 调试效率高 10 倍
```

> 💡 **重要提醒**：MCP Server 使用 `stdout` 做协议通信，所以你的代码中 **绝对不能用 `console.log()`**——会破坏协议数据流。调试日志请用 `console.error()`。

---

## 3. Tool 开发：让 AI 调用你的函数

Tool 是 MCP 最核心的能力——它让 AI 从"只能说"变成"能动手做"。

### 3.1 Tool 注册与 Zod Schema

```typescript
// server.tool() 的完整签名：
server.tool(
  name: string,           // Tool 名称（唯一标识）
  description: string,    // Tool 描述（AI 靠这个判断何时调用）
  inputSchema: ZodObject,  // 输入参数 Schema（Zod 定义）
  handler: (params) => Promise<CallToolResult>,  // 执行函数
);
```

```typescript
// Zod Schema 详解——定义 Tool 的输入参数

import { z } from "zod";

// 基础类型
const schema = {
  name: z.string().describe("用户姓名"),          // 字符串
  age: z.number().min(0).max(150).describe("年龄"), // 数字（带范围）
  active: z.boolean().describe("是否激活"),          // 布尔
};

// 可选参数
const schema2 = {
  query: z.string().describe("搜索关键词"),
  limit: z.number().optional().default(10).describe("返回数量"), // 可选，默认 10
  format: z.enum(["json", "text"]).optional().describe("输出格式"),
};

// 复杂类型
const schema3 = {
  filters: z.object({
    category: z.string(),
    minPrice: z.number(),
  }).describe("过滤条件"),
  tags: z.array(z.string()).describe("标签列表"),
};

// → Zod 做了两件事：
// 1. 生成 JSON Schema → 发送给 AI，AI 知道参数结构
// 2. 运行时校验 → AI 传了错误参数会自动报错
```

### 3.2 实战：天气查询 / 数据库查询 / 文件操作

```typescript
// 实战 1：天气查询 Tool
server.tool(
  "get_weather",
  "查询指定城市的天气信息",
  {
    city: z.string().describe("城市名称，如：北京、上海"),
    unit: z.enum(["celsius", "fahrenheit"]).optional()
      .default("celsius").describe("温度单位"),
  },
  async ({ city, unit }) => {
    // 调用天气 API
    const response = await fetch(
      `https://api.weather.com/v1/current?city=${encodeURIComponent(city)}`
    );
    const data = await response.json();

    const temp = unit === "fahrenheit"
      ? data.temp * 9/5 + 32
      : data.temp;

    return {
      content: [{
        type: "text",
        text: `${city}当前温度：${temp}°${unit === "fahrenheit" ? "F" : "C"}，${data.condition}`,
      }],
    };
  },
);

// 实战 2：数据库查询 Tool
server.tool(
  "query_database",
  "查询数据库中的数据（只读）",
  {
    sql: z.string().describe("SQL 查询语句（仅支持 SELECT）"),
    database: z.enum(["users", "orders", "products"]).describe("数据库名称"),
  },
  async ({ sql, database }) => {
    // 安全检查：只允许 SELECT
    if (!sql.trim().toUpperCase().startsWith("SELECT")) {
      return {
        content: [{ type: "text", text: "错误：只允许 SELECT 查询" }],
        isError: true,  // ← 标记为错误（AI 会知道调用失败了）
      };
    }

    const results = await db.query(sql);
    return {
      content: [{
        type: "text",
        text: JSON.stringify(results, null, 2),
      }],
    };
  },
);

// 实战 3：文件操作 Tool
server.tool(
  "read_file",
  "读取指定路径的文件内容",
  {
    path: z.string().describe("文件绝对路径"),
    encoding: z.enum(["utf-8", "base64"]).optional()
      .default("utf-8").describe("文件编码"),
  },
  async ({ path, encoding }) => {
    const fs = await import("node:fs/promises");
    try {
      const content = await fs.readFile(path, encoding as BufferEncoding);
      return {
        content: [{ type: "text", text: content }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `读取失败: ${(error as Error).message}` }],
        isError: true,
      };
    }
  },
);
```

### 3.3 错误处理与返回值规范

```typescript
// Tool 返回值结构（CallToolResult）
type CallToolResult = {
  content: Array<
    | { type: "text"; text: string }         // 文本内容
    | { type: "image"; data: string; mimeType: string }  // 图片（Base64）
    | { type: "resource"; resource: { uri: string; text: string } }  // 资源引用
  >;
  isError?: boolean;  // 标记为错误返回（AI 会知道需要重试或换方式）
};
```

```
Tool 返回值最佳实践：

  场景                    isError    content
  ───────────────────────────────────────────────
  成功返回数据            false      结果文本/JSON
  参数合法但无结果         false      "未找到相关数据"
  参数不合法              true       "错误：参数 xxx 不合法"
  外部 API 调用失败       true       "错误：API 请求超时"
  权限不足                true       "错误：无权访问该资源"

  isError = true 的效果：
  → AI 知道本次调用失败了
  → AI 可能会修正参数后重试
  → AI 可能会告诉用户"我无法完成这个操作"
```

> 💡 **Tool 描述是最重要的**——AI 完全靠 `description` 来决定什么时候调用你的 Tool。描述写得差，AI 就不会用它；描述太模糊，AI 可能乱用。花在描述上的时间比代码实现更重要。

---

## 4. Resource 与 Prompt：完整能力三角

Tool 让 AI 执行操作，Resource 让 AI 读取数据，Prompt 让 AI 使用预设模板——三者配合才是完整的 MCP Server。

### 4.1 Resource：暴露数据给 AI 读取

```typescript
// Resource = 只读数据，AI 可以主动读取
// 类似于 REST API 的 GET 请求

// 静态 Resource：固定 URI
server.resource(
  "config",                              // Resource 名称
  "app://config",                        // URI（唯一标识）
  "应用的配置信息",                        // 描述
  async () => ({
    contents: [{
      uri: "app://config",
      text: JSON.stringify({
        version: "1.0.0",
        environment: process.env.NODE_ENV,
        features: ["search", "chat", "translate"],
      }, null, 2),
      mimeType: "application/json",
    }],
  }),
);

// AI 可以这样使用：
// "请读取应用配置" → AI 调用 resource://app://config → 拿到配置 JSON
```

### 4.2 Resource Template：动态 URI 模式

```typescript
// Resource Template = 带参数的动态 Resource
// 类似 REST 的 /users/:id

server.resource(
  "user-profile",
  "app://users/{userId}",                // URI 模板（{userId} 是参数）
  "查看用户的个人资料",
  async (uri) => {
    // 从 URI 中提取参数
    const userId = uri.pathname.split("/").pop();
    const user = await db.users.findById(userId);

    return {
      contents: [{
        uri: uri.href,
        text: JSON.stringify(user, null, 2),
        mimeType: "application/json",
      }],
    };
  },
);

// 列表型 Resource：返回所有可用资源
server.resource(
  "all-documents",
  "app://documents",
  "所有文档列表",
  async () => {
    const docs = await db.documents.findAll();
    return {
      contents: docs.map(doc => ({
        uri: `app://documents/${doc.id}`,
        text: doc.content,
        mimeType: "text/plain",
      })),
    };
  },
);
```

### 4.3 Prompt：可复用的交互模板

```typescript
// Prompt = 预定义的交互模板，用户在 AI 客户端中选择使用

server.prompt(
  "code-review",                         // Prompt 名称
  "代码审查模板",                          // 描述
  {
    // 参数 Schema
    language: z.string().describe("编程语言"),
    code: z.string().describe("要审查的代码"),
  },
  async ({ language, code }) => ({
    messages: [
      {
        role: "user",
        content: {
          type: "text",
          text: `请审查以下 ${language} 代码，关注：
1. 代码质量和可读性
2. 潜在的 Bug
3. 性能问题
4. 安全隐患

代码：
\`\`\`${language}
${code}
\`\`\``,
        },
      },
    ],
  }),
);

// 用户在 Claude Desktop 中：
// 1. 点击 Prompt 图标 → 看到 "code-review"
// 2. 填写 language 和 code 参数
// 3. 生成完整的 Prompt 发送给 AI
```

### 4.4 三大原语的协作模式

```
Tool / Resource / Prompt 的协作：

  用户："审查我的项目代码"

  ① Prompt（code-review 模板）
     → 生成结构化的审查指令

  ② Resource（app://project/src）
     → AI 读取项目源码文件列表

  ③ Tool（read_file）
     → AI 调用 Tool 逐个读取文件内容

  ④ AI 综合所有信息 → 输出审查报告

  ─────────────────────────────────────

  选择哪个原语？

  "AI 需要执行操作"      → Tool（查天气、发邮件、写文件）
  "AI 需要读取数据"      → Resource（配置、用户信息、文档）
  "用户需要预设模板"     → Prompt（代码审查、SQL 生成、翻译）

  经验法则：
  → 大多数 MCP Server 以 Tool 为主
  → Resource 适合暴露静态/半静态数据
  → Prompt 适合标准化常见工作流
```

> 💡 **先做 Tool，再考虑 Resource 和 Prompt**。80% 的 MCP Server 只需要 Tool 就够了。Resource 和 Prompt 是锦上添花——当你发现 AI 经常需要读取某些固定数据，或者用户总是用相同的提问模式时，再加。

---

## 5. 传输层：Stdio 与 HTTP

传输层决定 MCP Server 怎么和 AI 客户端通信——本地用 Stdio，远程用 HTTP。

### 5.1 Stdio 传输：本地集成首选

```typescript
// Stdio 传输：通过标准输入/输出通信
// → 客户端以子进程方式启动你的 Server
// → stdin/stdout 传递 JSON-RPC 消息
// → 最简单、零配置

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new McpServer({ name: "my-server", version: "1.0.0" });
// ... 注册 Tools/Resources/Prompts ...

const transport = new StdioServerTransport();
await server.connect(transport);
```

```
Stdio 传输的工作流程：

  Claude Desktop                    你的 MCP Server
       │                                  │
       │── 启动子进程 ──────────────────────▶│
       │                                  │
       │── stdin: {"method":"initialize"} ──▶│
       │◀── stdout: {"result":{...}} ──────│
       │                                  │
       │── stdin: {"method":"tools/call"} ──▶│
       │◀── stdout: {"result":{...}} ──────│
       │                                  │
       │── 关闭进程 ────────────────────────▶│

  → stdin = 客户端发给 Server 的请求
  → stdout = Server 返回给客户端的响应
  → stderr = 你的调试日志（不影响协议）
```

### 5.2 StreamableHTTP：远程部署方案

```typescript
// StreamableHTTP 传输：通过 HTTP 通信
// → Server 作为 HTTP 服务运行
// → 支持远程访问、负载均衡、无状态部署

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

const server = new McpServer({ name: "my-server", version: "1.0.0" });
// ... 注册 Tools ...

// 无状态模式（推荐：适合 Serverless）
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined,  // 无状态
});
await server.connect(transport);
```

### 5.3 Express 集成实战

```typescript
// 用 Express 包装 MCP Server（生产级方案）
import express from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

const app = express();
app.use(express.json());

const server = new McpServer({ name: "my-server", version: "1.0.0" });
// ... 注册 Tools ...

// MCP 端点
app.post("/mcp", async (req, res) => {
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
  });
  await server.connect(transport);

  // 处理请求
  await transport.handleRequest(req, res);
});

// 健康检查
app.get("/health", (req, res) => {
  res.json({ status: "ok", server: "my-mcp-server" });
});

app.listen(3000, () => {
  console.log("MCP HTTP Server running on http://localhost:3000");
});
```

### 5.4 传输层选型指南

```
传输层选型：

  场景                      推荐传输          原因
  ──────────────────────────────────────────────────────
  Claude Desktop 本地       Stdio             零配置，最简单
  Cursor 集成               Stdio             官方推荐
  远程服务器部署             StreamableHTTP    支持网络访问
  Serverless（Vercel等）    StreamableHTTP    无状态，按需启动
  多用户共享服务             StreamableHTTP    单实例多客户端
  内部工具（个人使用）       Stdio             够用，不用部署

  → 个人开发者：先用 Stdio，后期需要远程时再加 HTTP
  → 团队/企业：直接上 HTTP，方便统一管理
```

> 💡 **Stdio 和 HTTP 可以同时支持**——同一个 Server 可以根据启动参数选择不同传输层，代码逻辑完全复用。

---

## 6. 与 Claude Desktop / Cursor 集成

写好的 MCP Server 怎么接入真正的 AI 客户端？配置文件加几行 JSON 就行。

### 6.1 Claude Desktop 集成配置

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
// %APPDATA%\Claude\claude_desktop_config.json (Windows)

{
  "mcpServers": {
    "my-tools": {
      "command": "npx",
      "args": ["tsx", "/absolute/path/to/src/index.ts"],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}
```

```
配置字段说明：

  字段        类型        说明
  ────────────────────────────────────────────
  command     string      启动命令（node/npx/python）
  args        string[]    命令参数
  env         object      环境变量（传 API Key 等）

  常用启动方式：

  方式 1: 直接运行 TypeScript（开发阶段）
  "command": "npx", "args": ["tsx", "/path/to/src/index.ts"]

  方式 2: 运行编译后的 JS（生产阶段）
  "command": "node", "args": ["/path/to/dist/index.js"]

  方式 3: 通过 npx 运行发布的包
  "command": "npx", "args": ["-y", "my-mcp-server"]
```

### 6.2 Cursor 集成配置

```json
// 项目根目录/.cursor/mcp.json（项目级别）
// 或 ~/.cursor/mcp.json（全局级别）

{
  "mcpServers": {
    "my-tools": {
      "command": "npx",
      "args": ["tsx", "/absolute/path/to/src/index.ts"],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}
// → 配置格式和 Claude Desktop 基本一致
// → 项目级配置优先于全局配置
```

### 6.3 调试技巧与问题排查

```
常见问题排查：

  问题                          原因                      解决方案
  ───────────────────────────────────────────────────────────────────
  Server 不出现在工具列表       配置文件路径错误           检查绝对路径
  "spawn ENOENT"               command 找不到             用 which npx 确认路径
  连接后立即断开                Server 启动就崩溃          先单独运行测试
  Tool 调用无响应               stdout 被 console.log 污染 改用 console.error
  参数验证失败                  Zod Schema 不匹配         检查 .describe() 描述
  环境变量读不到                env 配置未传递             检查 JSON 中的 env 字段

  调试步骤：
  1. 先用 mcp-inspector 确认 Server 正常
  2. 检查配置文件 JSON 语法（逗号、引号）
  3. 用绝对路径替代相对路径
  4. 查看客户端日志（Claude: Developer Tools → Console）
```

> 💡 **配置完成后需要重启客户端**——Claude Desktop 和 Cursor 都会在启动时读取配置文件，修改后必须重启才能生效。

---

## 7. 生产级 MCP Server 开发模式

从 Demo 到 npm 发布——让别人一行 `npx` 就能用你的 MCP Server。

### 7.1 项目结构与工程化配置

```
推荐的项目结构：

  my-mcp-server/
  ├── src/
  │   ├── index.ts           ← 入口（创建 Server + 连接传输层）
  │   ├── tools/
  │   │   ├── weather.ts     ← 天气 Tool
  │   │   ├── database.ts    ← 数据库 Tool
  │   │   └── index.ts       ← 统一导出注册函数
  │   ├── resources/
  │   │   └── config.ts      ← Resource 定义
  │   └── prompts/
  │       └── code-review.ts ← Prompt 定义
  ├── package.json
  ├── tsconfig.json
  └── README.md
```

```typescript
// src/tools/weather.ts — 单个 Tool 模块化
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

export function registerWeatherTools(server: McpServer) {
  server.tool(
    "get_weather",
    "查询城市天气",
    { city: z.string().describe("城市名称") },
    async ({ city }) => ({
      content: [{ type: "text", text: `${city}: 晴，25°C` }],
    }),
  );
}

// src/index.ts — 入口文件
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerWeatherTools } from "./tools/weather.js";

const server = new McpServer({ name: "my-server", version: "1.0.0" });

// 注册所有 Tools
registerWeatherTools(server);

const transport = new StdioServerTransport();
await server.connect(transport);
```

### 7.2 npm 发布：让别人一键 npx 运行

```json
// package.json 关键配置
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "bin": {
    "my-mcp-server": "./dist/index.js"
  },
  "files": ["dist"],
  "scripts": {
    "build": "tsc",
    "dev": "npx @modelcontextprotocol/inspector npx tsx src/index.ts",
    "prepublishOnly": "npm run build"
  }
}
```

```bash
# 发布流程
npm run build        # 编译 TypeScript
npm publish          # 发布到 npm

# 别人使用
npx -y my-mcp-server  # 一键运行

# Claude Desktop 配置
# "command": "npx", "args": ["-y", "my-mcp-server"]
```

```
dist/index.js 顶部添加 shebang：

  #!/usr/bin/env node

  → 让系统知道用 Node.js 执行
  → npx 运行时自动找到这个入口
```

### 7.3 安全、日志与测试

```
安全清单：

  ✅ 输入校验：用 Zod Schema 严格定义参数
  ✅ SQL 注入防护：只允许 SELECT / 用参数化查询
  ✅ 路径遍历防护：限制文件操作目录
  ✅ API Key 保护：通过 env 传入，不硬编码
  ✅ 超时控制：外部 API 调用设置 timeout
  ❌ 不要信任 AI 的输入——AI 可能被 Prompt 注入操纵
```

```typescript
// 测试策略：直接调用 Tool handler 测试
import { describe, it, expect } from "vitest";

describe("weather tool", () => {
  it("should return weather info", async () => {
    const server = new McpServer({ name: "test", version: "0.0.1" });
    registerWeatherTools(server);

    // 通过 MCP Client 测试
    const client = new Client({ name: "test-client", version: "0.0.1" });
    const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
    await server.connect(serverTransport);
    await client.connect(clientTransport);

    const result = await client.callTool({
      name: "get_weather",
      arguments: { city: "北京" },
    });

    expect(result.content[0].text).toContain("北京");
  });
});
```

> 🎉 **全文完成**。MCP TypeScript SDK 开发的核心路径：**协议理解 → 环境搭建 → Tool 开发 → Resource/Prompt → 传输层 → 客户端集成 → npm 发布**。一个 MCP Server 从 Hello World 到生产级发布，全流程覆盖。

---
