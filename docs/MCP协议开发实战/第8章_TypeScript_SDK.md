# MCP 协议开发实战

> 从零构建你的第一个 MCP Server，让 AI 成为万能工具人。

---

## 8. TypeScript SDK —— 用 Node.js 构建 MCP Server

前面几章我们一直在用 Python。但如果你是前端开发者，或者团队以 TypeScript / Node.js 为主力栈，MCP 也有官方的 TypeScript SDK——而且用起来同样简洁。

这一章，我们用 TS SDK 从零搭建一个 MCP Server，并对比 Python 和 TypeScript 两种方案。

---

### 8.1 TypeScript SDK 快速上手

### 环境准备

```
前置要求：

  ✅ Node.js >= 18（推荐 LTS 版本）
  ✅ npm 或 pnpm 包管理器
  ✅ TypeScript（SDK 内置类型定义）

检查版本：
  $ node --version
  v20.11.0  ← 18 以上就行

  $ npm --version
  10.2.4
```

### 初始化项目

```bash
# 创建项目目录
mkdir my-mcp-ts-server && cd my-mcp-ts-server

# 初始化 package.json
npm init -y

# 安装 MCP TypeScript SDK
npm install @modelcontextprotocol/sdk

# 安装 TypeScript 和 Zod（参数校验）
npm install typescript zod
npm install -D @types/node tsx

# 初始化 tsconfig.json
npx tsc --init
```

修改 `tsconfig.json` 的关键配置：

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true
  }
}
```

修改 `package.json`，添加启动脚本：

```json
{
  "type": "module",
  "scripts": {
    "dev": "tsx server.ts",
    "build": "tsc",
    "start": "node dist/server.js"
  }
}
```

### 项目结构

```
my-mcp-ts-server/
├── node_modules/
├── package.json
├── tsconfig.json
└── server.ts          ← 你的 MCP Server 代码
```

### 第一个 TypeScript MCP Server

创建 `server.ts`，写入以下代码：

```typescript
// server.ts —— TypeScript 版天气查询 MCP Server
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// 创建 Server 实例
const server = new McpServer({
  name: "天气查询",
  version: "1.0.0",
});

// 模拟天气数据
const WEATHER_DATA: Record<string, {
  temp: number;
  condition: string;
  wind: string;
  humidity: string;
}> = {
  "北京": { temp: 25, condition: "晴", wind: "东北风3级", humidity: "45%" },
  "上海": { temp: 28, condition: "多云", wind: "东风2级", humidity: "72%" },
  "广州": { temp: 32, condition: "雷阵雨", wind: "南风4级", humidity: "85%" },
  "深圳": { temp: 30, condition: "阴", wind: "西南风2级", humidity: "78%" },
  "杭州": { temp: 26, condition: "晴转多云", wind: "东风1级", humidity: "60%" },
};

// 注册 Tool：查询天气
server.tool(
  "get_weather",                          // 工具名称
  "查询指定城市的当前天气信息",              // 工具描述
  {                                        // 参数 Schema（用 Zod）
    city: z.string().describe("城市名称，如 '北京'、'上海'"),
  },
  async ({ city }) => {                    // 处理函数
    const weather = WEATHER_DATA[city];

    if (!weather) {
      const available = Object.keys(WEATHER_DATA).join("、");
      return {
        content: [{
          type: "text" as const,
          text: `暂不支持查询 ${city} 的天气。目前支持的城市：${available}`,
        }],
      };
    }

    return {
      content: [{
        type: "text" as const,
        text: [
          `🌍 ${city} 当前天气：`,
          `🌡️ 温度：${weather.temp}°C`,
          `⛅ 天气：${weather.condition}`,
          `💨 风力：${weather.wind}`,
          `💧 湿度：${weather.humidity}`,
        ].join("\n"),
      }],
    };
  }
);

// 启动 Server（STDIO Transport）
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Python vs TypeScript 写法对比

```
同一个工具的两种写法：

  Python（FastMCP）：
  ┌─────────────────────────────────────────────┐
  │ @mcp.tool()                                  │
  │ def get_weather(city: str) -> str:           │
  │     """查询指定城市的当前天气。               │
  │     Args:                                     │
  │         city: 城市名称                        │
  │     """                                       │
  │     return f"{city} 今天 25°C"                │
  └─────────────────────────────────────────────┘
  → 装饰器风格，自动提取元数据
  → 6 行代码

  TypeScript（McpServer）：
  ┌─────────────────────────────────────────────┐
  │ server.tool(                                 │
  │   "get_weather",                             │
  │   "查询指定城市的当前天气",                   │
  │   { city: z.string().describe("城市名称") }, │
  │   async ({ city }) => ({                     │
  │     content: [{ type: "text", text: ... }]   │
  │   })                                         │
  │ );                                           │
  └─────────────────────────────────────────────┘
  → 链式调用风格，显式声明元数据
  → 7 行代码
```

> **核心差异**：Python 的 FastMCP 用装饰器 + 类型注解自动推断，写起来更"魔法"；TypeScript 用链式方法 + Zod Schema 显式定义，写起来更"明确"。两者的协议输出完全一致。

---

### 8.2 用 Zod 定义类型安全的参数

Python 用类型注解 + Pydantic 做参数校验，TypeScript 对应的方案是 **Zod**。

### Zod 基础类型

```typescript
import { z } from "zod";

// Zod 类型 → JSON Schema 映射（类比 Python）
z.string()          // → {"type": "string"}    ← Python: str
z.number()          // → {"type": "number"}    ← Python: float
z.number().int()    // → {"type": "integer"}   ← Python: int
z.boolean()         // → {"type": "boolean"}   ← Python: bool
z.array(z.string()) // → {"type": "array", ...} ← Python: list[str]
```

### 完整的参数示例

```typescript
// 注册一个有复杂参数的 Tool
server.tool(
  "search_logs",
  "搜索系统日志",
  {
    // 必填参数
    keyword: z.string()
      .describe("搜索关键词"),

    // 可选参数（用 .optional() 或 .default()）
    max_results: z.number().int()
      .default(10)
      .describe("最多返回条数，默认 10"),

    // 枚举参数（对应 Python 的 Literal）
    level: z.enum(["DEBUG", "INFO", "WARNING", "ERROR"])
      .default("INFO")
      .describe("日志级别过滤"),

    // 可选布尔值
    include_stack: z.boolean()
      .default(false)
      .describe("是否包含错误堆栈"),
  },
  async ({ keyword, max_results, level, include_stack }) => {
    // TypeScript 自动推断类型：
    // keyword: string
    // max_results: number (默认 10)
    // level: "DEBUG" | "INFO" | "WARNING" | "ERROR"
    // include_stack: boolean (默认 false)

    return {
      content: [{
        type: "text" as const,
        text: `搜索 "${keyword}"，级别 ${level}，最多 ${max_results} 条`,
      }],
    };
  }
);
```

```
Zod 与 Python Pydantic 的对应关系：

  Zod                           Python
  ────────────────────          ────────────────────
  z.string()                    str
  z.number().int()              int
  z.number()                    float
  z.boolean()                   bool
  z.array(z.string())           list[str]
  z.enum(["a", "b"])            Literal["a", "b"]
  .default(10)                  = 10（默认值）
  .optional()                   | None = None
  .describe("...")              Field(description="...")
```

### Resource 和 Prompt 的 TypeScript 写法

```typescript
// ═══════════════════════════════════════════
// Resource：类比 Python 的 @mcp.resource()
// ═══════════════════════════════════════════

// 静态 Resource
server.resource(
  "app-config",                          // 资源名称
  "config://app/settings",               // URI
  async () => ({
    contents: [{
      uri: "config://app/settings",
      mimeType: "application/json",
      text: JSON.stringify({
        version: "1.0.0",
        debug: false,
      }, null, 2),
    }],
  })
);

// Resource 模板
server.resource(
  "source-file",                          // 资源名称
  "file://project/src/{filename}",        // URI 模板
  async ({ filename }) => {
    const fs = await import("fs/promises");
    const content = await fs.readFile(`./src/${filename}`, "utf-8");
    return {
      contents: [{
        uri: `file://project/src/${filename}`,
        mimeType: "text/plain",
        text: content,
      }],
    };
  }
);

// ═══════════════════════════════════════════
// Prompt：类比 Python 的 @mcp.prompt()
// ═══════════════════════════════════════════

server.prompt(
  "code_review",                          // Prompt 名称
  "对代码进行专业审查",                     // 描述
  {                                        // 参数（Zod）
    code: z.string().describe("要审查的代码"),
    language: z.string().default("python").describe("编程语言"),
  },
  async ({ code, language }) => ({
    messages: [{
      role: "user" as const,
      content: {
        type: "text" as const,
        text: `你是 ${language} 专家。请审查以下代码：\n\n\`\`\`${language}\n${code}\n\`\`\``,
      },
    }],
  })
);
```

```
三大原语的 TypeScript API 总结：

  server.tool(name, description, zodSchema, handler)
    → 注册工具，handler 返回 { content: [...] }

  server.resource(name, uri, handler)
    → 注册资源，handler 返回 { contents: [...] }

  server.prompt(name, description, zodSchema, handler)
    → 注册模板，handler 返回 { messages: [...] }
```

> **提示**：TypeScript SDK 的 API 比 Python 的 FastMCP 更"底层"一些——你需要手动构造返回对象（`{ content: [...] }`），而 FastMCP 允许你直接 `return "字符串"`。这是风格差异，能力上没区别。

---

### 8.3 Python vs TypeScript：选型建议

两套 SDK 都是官方出品，能力完全一致。选哪个？取决于你的团队和场景。

### 详细对比

| 维度 | Python SDK | TypeScript SDK |
|------|------------|----------------|
| **高层 API** | FastMCP（装饰器风格） | McpServer（链式调用） |
| **参数校验** | Pydantic + 类型注解 | Zod |
| **代码风格** | 自动推断、隐式"魔法" | 显式声明、类型安全 |
| **异步模型** | asyncio（async/await） | Node.js 原生 async |
| **生态库** | requests、pandas、sqlalchemy | axios、prisma、drizzle |
| **AI/ML 库** | ✅ numpy、torch、langchain | ❌ 这方面较弱 |
| **包管理** | uv / pip | npm / pnpm |
| **开发体验** | 更简洁（行数少） | 更严格（类型推断强） |
| **社区 Server** | 偏多 | 也不少 |
| **Claude Desktop 配置** | `command: "uv"` | `command: "npx"` |

### 选择决策树

```
你应该选哪个？

  你的团队主力语言是什么？
  │
  ├── Python 为主
  │   └── 选 Python SDK ✅
  │       理由：团队熟悉、生态好、FastMCP 很省事
  │
  ├── TypeScript / Node.js 为主
  │   └── 选 TypeScript SDK ✅
  │       理由：团队熟悉、类型安全、前端可复用
  │
  ├── 都行 / 新学
  │   │
  │   ├── 要用 AI/ML 库？（numpy、torch、langchain）
  │   │   └── 选 Python ✅（这些库没有 TS 版本）
  │   │
  │   ├── 要和前端项目集成？
  │   │   └── 选 TypeScript ✅（monorepo 统一技术栈）
  │   │
  │   └── 只是写工具 Server？
  │       └── 选 Python ✅（FastMCP 入门门槛更低）
  │
  └── 两个都要用？
      └── 完全可以！见下方"混合方案"
```

### 混合方案

一个团队完全可以同时使用两种 SDK——MCP 是标准协议，不同语言的 Server 可以共存：

```
混合方案示例：

  Claude Desktop 的配置：
  {
    "mcpServers": {
      "ai-tools": {
        "command": "uv",
        "args": ["run", "ai_server.py"]
      },
      "web-tools": {
        "command": "npx",
        "args": ["tsx", "web_server.ts"]
      }
    }
  }

  Python Server（ai_server.py）：
    → 调用 AI 模型、数据分析、ML 推理
    → 利用 Python 丰富的 AI 生态

  TypeScript Server（web_server.ts）：
    → 调用前端 API、操作浏览器、管理 CMS
    → 利用 Node.js 丰富的 Web 生态

  两个 Server 同时连接 Claude Desktop
  → AI 在同一个对话中可以调用两个 Server 的工具
  → 各取所长，完美互补
```

> **底线原则**：选你团队最熟悉的语言。MCP 是协议标准，用什么语言实现不影响最终效果。不要为了学 MCP 而换语言——那是本末倒置。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| TS SDK 安装 | `npm install @modelcontextprotocol/sdk zod` |
| Server 创建 | `new McpServer({ name, version })` |
| 注册 Tool | `server.tool(name, desc, zodSchema, handler)` |
| 注册 Resource | `server.resource(name, uri, handler)` |
| 注册 Prompt | `server.prompt(name, desc, zodSchema, handler)` |
| Zod 类型 | z.string() / z.number() / z.enum() / .describe() |
| 返回格式 | 需要手动构造 `{ content: [...] }` 对象 |
| vs Python | TS 更显式严格，Python 更简洁隐式 |
| 选型建议 | 选团队最熟悉的语言，协议标准不受语言影响 |
| 混合方案 | 同时用两种 SDK，各取所长 |

> **下一章预告**：实战项目 —— 构建一个 GitHub 代码分析 MCP Server。我们将综合运用 Tools + Resources + Prompts，从零构建一个能查仓库、读代码、分析质量的完整 MCP Server，并部署到 Claude Desktop 实际使用。

