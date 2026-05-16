# Claude Code 源码解读

> Anthropic Claude Code CLI 逆向还原项目（CCB）源码深度解读——从项目架构、CLI 启动流程、React Ink 终端渲染、Agent 循环、Tool 系统、MCP 集成到 Prompt 工程，拆解一个生产级 AI 编程助手的内部实现。

---

## 1. 项目概览与架构总览

### 1.1 项目背景：为什么逆向 Claude Code

```
Claude Code 是什么？

  Anthropic 官方推出的 AI 编程 CLI 工具
  用户在终端中与 Claude 交互，Claude 可以：
  - 读写文件
  - 执行命令
  - 搜索代码
  - 浏览网页
  - 调用 MCP 工具

  问题：Claude Code 是闭源的
  → 社区逆向还原了一份可运行、可调试的版本
  → 这就是 CCB（Claude Code Best）
  → 17.9k Star, 15.7k Fork
```

### 1.2 仓库结构全景图

```
claude-code/
├── src/                    # 核心源码（30+ 模块）
│   ├── entrypoints/        # CLI 入口文件
│   ├── cli/                # 命令行解析（Commander.js）
│   ├── bootstrap/          # 初始化引导链
│   ├── main.tsx            # 主渲染入口（React Ink）
│   │
│   ├── assistant/          # ★ Agent 核心循环
│   ├── coordinator/        # 多 Agent 编排
│   ├── services/           # 外部服务抽象
│   ├── bridge/             # 进程间通信
│   │
│   ├── Tool.ts             # Tool 基类定义
│   ├── tools.ts            # Tool 注册表
│   ├── commands.ts         # 斜杠命令注册
│   ├── context.ts          # 上下文管理
│   ├── Task.ts             # 任务模型
│   │
│   ├── components/         # React Ink 组件
│   ├── screens/            # 页面/屏幕
│   ├── hooks/              # React Hooks
│   ├── keybindings/        # 快捷键系统
│   ├── vim/                # Vim 模式
│   ├── outputStyles/       # 输出样式
│   │
│   ├── context/            # 上下文加载器
│   ├── state/              # 全局状态管理
│   ├── types/              # TypeScript 类型
│   ├── schemas/            # Zod 验证模式
│   ├── constants/          # 常量定义
│   ├── utils/              # 通用工具函数
│   │
│   ├── plugins/            # 插件系统
│   ├── skills/             # Skill 技能模块
│   ├── voice/              # 语音模式
│   ├── buddy/              # 协作模式
│   ├── daemon/             # 后台守护进程
│   ├── remote/             # 远程控制
│   ├── ssh/                # SSH 连接
│   ├── server/             # HTTP 服务
│   ├── jobs/               # 异步任务
│   └── proactive/          # 主动建议
│
├── packages/               # Monorepo 子包
│   ├── @ant/               # Anthropic 内部包还原
│   │   ├── model-provider/ # 多模型提供商抽象
│   │   ├── computer-use*/  # Computer Use 实现
│   │   └── claude-for-chrome-mcp/
│   ├── @anthropic-ai/      # Anthropic SDK 扩展
│   ├── @claude-code-best/  # CCB 自有包
│   │   ├── builtin-tools/  # 内置工具集
│   │   ├── agent-tools/    # Agent 扩展工具
│   │   └── mcp-client/     # MCP 客户端
│   └── @anthropic/ink/     # 定制 Ink 渲染器
│
├── build.ts                # 构建脚本（Code Splitting）
├── vite.config.ts          # Vite 构建配置
├── biome.json              # 代码规范（Biome）
└── package.json            # Monorepo 根配置
```

### 1.3 技术栈选型：Bun + React Ink + Anthropic SDK

| 层 | 技术 | 作用 |
|---|---|---|
| **运行时** | Bun ≥ 1.3 | 高性能 JS 运行时，替代 Node.js |
| **终端 UI** | React + Ink | 用 React 组件渲染终端界面 |
| **命令行** | Commander.js | CLI 参数解析 |
| **AI SDK** | @anthropic-ai/sdk | Claude API 调用 |
| **多模型** | OpenAI SDK | 兼容 OpenAI/Gemini 协议 |
| **MCP** | @modelcontextprotocol/sdk | MCP 工具协议 |
| **构建** | Vite + 自定义 build.ts | Code Splitting 打包 |
| **规范** | Biome | Lint + Format（替代 ESLint + Prettier） |
| **监控** | Langfuse + Sentry + OTel | 可观测性三件套 |
| **验证** | Zod v4 | 运行时类型校验 |
| **状态** | React Hooks + 自定义 | 全局状态管理 |

### 1.4 构建系统与 Monorepo 工作空间

```typescript
// build.ts — Code Splitting 多文件打包
// 产物：dist/cli.js（入口）+ ~450 个 chunk 文件
// 支持 Bun 和 Node 双模式运行

// package.json 中的 Monorepo 工作空间
{
  "workspaces": [
    "packages/*",
    "packages/@ant/*",
    "packages/@anthropic-ai/*"
  ],
  "bin": {
    "ccb": "dist/cli-node.js",       // Node 模式入口
    "ccb-bun": "dist/cli-bun.js",    // Bun 模式入口
  }
}
```

```
构建流程：

  src/*.ts → Vite/build.ts → dist/
                                ├── cli-node.js    (Node 入口)
                                ├── cli-bun.js     (Bun 入口)
                                └── chunks/        (~450 个分片)

  为什么用 Code Splitting？
  1. 首屏加载快——只加载当前需要的代码
  2. 内存占用低——不用一次加载全部模块
  3. 双模式兼容——Bun 和 Node 共享 chunk
```

---

## 2. CLI 启动与引导流程

### 2.1 入口文件：entrypoints → cli → main

```
启动链路：

  用户执行 ccb
    ↓
  dist/cli-node.js (或 cli-bun.js)
    ↓
  src/entrypoints/     ← 入口分发
    ├── cli.ts         ← 主 CLI 入口
    ├── query.ts       ← 单次查询模式（非交互）
    └── server.ts      ← HTTP API 模式
    ↓
  src/cli/             ← Commander.js 命令解析
    ├── parseArgs()    ← 解析 --model, --debug 等参数
    └── dispatch()     ← 分发到对应模式
    ↓
  src/bootstrap/       ← 初始化链
    ├── loadConfig()   ← 加载配置
    ├── initAuth()     ← 鉴权检查
    ├── setupTools()   ← 注册工具
    └── initUI()       ← 初始化终端 UI
    ↓
  src/main.tsx         ← React Ink 渲染入口
    └── <App />        ← 启动 REPL 交互循环
```

### 2.2 Bootstrap 初始化链

```typescript
// src/bootstrap/ — 初始化引导（伪代码还原）
async function bootstrap(options: CLIOptions) {
  // 1. 加载环境变量和配置文件
  const config = await loadConfig();
  
  // 2. 检查认证状态
  const auth = await initAuth(config);
  if (!auth.valid) {
    // 引导用户执行 /login
    return showLoginScreen();
  }
  
  // 3. 加载项目上下文（CLAUDE.md, AGENTS.md）
  const projectContext = await loadProjectContext(process.cwd());
  
  // 4. 初始化模型提供商
  const provider = await initModelProvider(config, auth);
  
  // 5. 注册内置工具
  const tools = registerBuiltinTools();
  
  // 6. 加载 MCP 服务器
  const mcpTools = await loadMCPServers(config);
  tools.push(...mcpTools);
  
  // 7. 初始化 Feature Flags（GrowthBook）
  await initFeatureFlags();
  
  // 8. 启动可观测性（Langfuse + Sentry）
  await initObservability();
  
  // 9. 启动 React Ink 渲染
  render(<App config={config} tools={tools} provider={provider} />);
}
```

### 2.3 配置加载与多提供商登录（/login）

```
/login 鉴权流程：

  用户输入 /login
    ↓
  选择提供商：
    ├── Anthropic（官方）
    ├── Anthropic Compatible（第三方兼容 API）
    ├── OpenAI Compatible
    ├── Gemini Compatible
    ├── AWS Bedrock
    └── Google Vertex
    ↓
  填写配置：
    ├── Base URL: https://api.example.com/v1
    ├── API Key:  sk-xxx
    ├── Haiku Model:  claude-haiku-4-5-20251001
    ├── Sonnet Model: claude-sonnet-4-6
    └── Opus Model:   claude-opus-4-6
    ↓
  保存到 ~/.claude-code-best/config.json
```

```typescript
// src/services/ — 多提供商抽象
// packages/@ant/model-provider/ — 模型提供商统一接口

interface ModelProvider {
  chat(messages: Message[], options: ChatOptions): AsyncGenerator<StreamChunk>;
  countTokens(text: string): Promise<number>;
  getModelInfo(model: string): ModelInfo;
}

// 支持的提供商
type ProviderType = 
  | 'anthropic'           // 官方 API
  | 'anthropic-compatible' // 兼容 API
  | 'openai'              // OpenAI 协议
  | 'gemini'              // Gemini 协议
  | 'bedrock'             // AWS Bedrock
  | 'vertex';             // Google Vertex
```

### 2.4 Feature Flags 系统

```typescript
// GrowthBook 功能开关
// 所有功能通过 FEATURE_<FLAG_NAME>=1 环境变量启用

// 示例启动命令
// FEATURE_BUDDY=1 FEATURE_FORK_SUBAGENT=1 bun run dev

// 已知的 Feature Flags：
const FEATURES = {
  BUDDY: '协作模式（多人共享 Session）',
  FORK_SUBAGENT: '子 Agent 分叉（并行执行子任务）',
  VOICE: '语音输入模式（豆包 ASR）',
  COMPUTER_USE: 'Computer Use（屏幕操作）',
  CHROME_USE: 'Chrome 浏览器自动化',
  REMOTE_CONTROL: '远程控制模式',
  AUTO_DREAM: '自动 Dream 模式',
  LANGFUSE: 'Langfuse 监控集成',
};
```

---

## 3. 终端 UI：React Ink 渲染引擎

### 3.1 React Ink：用 React 写终端 UI

```
React Ink 的核心思想：

  Web 世界：React → ReactDOM → 浏览器 DOM
  终端世界：React → Ink     → 终端字符

  JSX 组件不是渲染到 HTML，而是渲染到终端！

  <Box flexDirection="column">
    <Text color="green">✅ 成功</Text>
    <Text color="red">❌ 失败</Text>
  </Box>

  终端输出：
  ✅ 成功
  ❌ 失败

  优势：
  1. 组件化——复杂 UI 拆分为可复用组件
  2. 状态管理——useState, useEffect 完全可用
  3. 声明式——描述"是什么"而非"怎么画"
```

```typescript
// src/main.tsx — React Ink 渲染入口（简化版）
import { render } from '@anthropic/ink';
import React from 'react';

function App({ config, tools, provider }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isThinking, setIsThinking] = useState(false);

  const handleUserInput = async (input: string) => {
    // 检查是否是斜杠命令
    if (input.startsWith('/')) {
      return handleCommand(input);
    }

    setIsThinking(true);
    const response = await agent.run(input, messages);
    setMessages(prev => [...prev, ...response.newMessages]);
    setIsThinking(false);
  };

  return (
    <Box flexDirection="column">
      <MessageList messages={messages} />
      {isThinking && <ThinkingIndicator />}
      <InputPrompt onSubmit={handleUserInput} />
    </Box>
  );
}

render(<App />);
```

### 3.2 组件体系：components/ 目录解读

```
src/components/ — 核心 UI 组件库：

  ┌──────────────────────────────────────────┐
  │  App (根组件)                             │
  │                                          │
  │  ┌────────────────────────────────────┐  │
  │  │ MessageList 消息列表               │  │
  │  │  ├─ UserMessage 用户消息           │  │
  │  │  ├─ AssistantMessage AI 回复       │  │
  │  │  │   ├─ MarkdownRenderer 渲染      │  │
  │  │  │   ├─ CodeBlock 代码块           │  │
  │  │  │   └─ ToolResult 工具结果        │  │
  │  │  └─ SystemMessage 系统消息         │  │
  │  ├────────────────────────────────────┤  │
  │  │ ThinkingIndicator 思考中...        │  │
  │  ├────────────────────────────────────┤  │
  │  │ ToolConfirmation 工具确认弹窗      │  │
  │  │  "是否允许执行 rm -rf ？"          │  │
  │  ├────────────────────────────────────┤  │
  │  │ InputPrompt 输入框                 │  │
  │  │  ├─ 普通输入模式                   │  │
  │  │  └─ Vim 编辑模式                   │  │
  │  ├────────────────────────────────────┤  │
  │  │ StatusBar 状态栏                   │  │
  │  │  模型 | Token | 成本 | 延迟        │  │
  │  └────────────────────────────────────┘  │
  └──────────────────────────────────────────┘
```

```typescript
// 组件实现示例（简化版）
function AssistantMessage({ content, toolCalls }) {
  return (
    <Box flexDirection="column">
      <Box>
        <Text color="magenta" bold>Claude</Text>
        <Text> </Text>
        <MarkdownRenderer content={content} />
      </Box>
      {toolCalls?.map(tc => (
        <ToolCallDisplay key={tc.id} toolCall={tc} />
      ))}
    </Box>
  );
}

function ToolCallDisplay({ toolCall }) {
  const icon = toolCall.status === 'success' ? '✅' : '❌';
  return (
    <Box>
      <Text dimColor>{icon} {toolCall.name}</Text>
      <Text color="gray"> → {toolCall.result?.slice(0, 100)}</Text>
    </Box>
  );
}
```

### 3.3 屏幕与路由：screens/ 页面管理

```
src/screens/ — 不同的"页面"：

  主 REPL 屏幕（默认）
    → 消息列表 + 输入框 + 工具确认

  登录屏幕 (/login)
    → 提供商选择 + 配置填写

  帮助屏幕 (/help)
    → 命令列表 + 快捷键说明

  设置屏幕 (/config)
    → 模型切换 + 参数调整

  状态屏幕
    → 连接状态 + MCP 服务器列表

  切换逻辑类似 React Router，但在终端中
```

### 3.4 快捷键与 Vim 模式

```typescript
// src/keybindings/ — 快捷键系统

const KEYBINDINGS = {
  'Escape':       '取消当前操作 / 退出 Vim 插入模式',
  'Ctrl+C':       '中断当前执行',
  'Ctrl+D':       '退出 CCB',
  'Ctrl+L':       '清屏',
  'Tab':          '自动补全 / 切换字段',
  'Shift+Tab':    '反向切换',
  'Up/Down':      '历史命令导航',
  'Shift+Down':   '打开管道模式（Pipes）',
};

// src/vim/ — Vim 模式
// 支持 Normal / Insert / Visual 三种模式
// 在输入框中使用 Vim 快捷键编辑
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 项目定位 | Claude Code 逆向还原，可运行/可调试/可扩展 |
| 技术栈 | Bun + React Ink + Anthropic SDK + MCP |
| 启动链 | entrypoints → cli → bootstrap → main.tsx |
| 终端 UI | React Ink 将 JSX 组件渲染到终端字符 |
| 组件体系 | MessageList / InputPrompt / ToolConfirmation |

> **下一章**：Agent 核心循环——assistant/ 模块、消息流、Tool 调用链。

---

## 4. Agent 核心循环

### 4.1 Agent 循环：用户输入 → LLM → Tool → 输出

```
Claude Code 的核心是一个 ReAct Agent 循环：

  ┌──────────────────────────────────────────────────┐
  │                                                  │
  │  用户输入                                        │
  │    ↓                                             │
  │  构建 Messages（System + History + User）         │
  │    ↓                                             │
  │  调用 Claude API（流式）                          │
  │    ↓                                             │
  │  解析响应                                        │
  │    ├── 纯文本 → 直接展示给用户                    │
  │    └── Tool Call → 执行工具                       │
  │                     ↓                            │
  │                   工具结果 → 追加到 Messages       │
  │                     ↓                            │
  │                   再次调用 Claude API ←──── 循环  │
  │                     ↓                            │
  │                   直到没有 Tool Call → 输出        │
  │                                                  │
  └──────────────────────────────────────────────────┘

  关键点：
  1. 这是一个 while 循环，不是单次调用
  2. Claude 可以连续调用多个工具
  3. 每次工具结果都会反馈给 Claude
  4. Claude 决定何时停止（不再调用工具）
```

### 4.2 assistant/ 模块：消息构建与流式处理

```typescript
// src/assistant/ — Agent 核心（伪代码还原）

class Assistant {
  private provider: ModelProvider;
  private tools: Tool[];
  private messages: Message[] = [];

  async run(userInput: string): Promise<AssistantResponse> {
    // 1. 追加用户消息
    this.messages.push({ role: 'user', content: userInput });

    // 2. Agent 循环
    while (true) {
      // 2.1 构建完整消息（含 System Prompt）
      const systemPrompt = await buildSystemPrompt(this.tools);
      
      // 2.2 调用 LLM（流式）
      const stream = this.provider.chat(this.messages, {
        system: systemPrompt,
        tools: this.tools.map(t => t.toSchema()),
        max_tokens: 16384,
        stream: true,
      });

      // 2.3 流式处理响应
      const response = await this.processStream(stream);

      // 2.4 追加 AI 消息
      this.messages.push({
        role: 'assistant',
        content: response.content,
        tool_calls: response.toolCalls,
      });

      // 2.5 如果没有工具调用，结束循环
      if (!response.toolCalls?.length) {
        return response;
      }

      // 2.6 执行工具调用
      const toolResults = await this.executeTools(response.toolCalls);
      
      // 2.7 追加工具结果消息
      for (const result of toolResults) {
        this.messages.push({
          role: 'tool',
          tool_call_id: result.id,
          content: result.output,
        });
      }
      // → 回到循环开头，再次调用 LLM
    }
  }

  private async processStream(
    stream: AsyncGenerator<StreamChunk>
  ): Promise<AssistantResponse> {
    let content = '';
    const toolCalls: ToolCall[] = [];

    for await (const chunk of stream) {
      switch (chunk.type) {
        case 'content_block_delta':
          // 实时输出文本到终端
          content += chunk.delta.text;
          this.emit('text', chunk.delta.text);
          break;
          
        case 'tool_use':
          // 收集工具调用
          toolCalls.push({
            id: chunk.id,
            name: chunk.name,
            input: chunk.input,
          });
          this.emit('tool_call', chunk);
          break;
          
        case 'message_stop':
          break;
      }
    }

    return { content, toolCalls };
  }
}
```

### 4.3 Task 任务模型

```typescript
// src/Task.ts — 任务管理

interface Task {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  input: string;
  messages: Message[];
  tokenUsage: {
    input: number;
    output: number;
    cacheRead: number;
    cacheWrite: number;
  };
  cost: number;
  startedAt: Date;
  completedAt?: Date;
}
```

```
Task 生命周期：

  pending → running → completed
                   ↘ failed
                   ↘ cancelled (Ctrl+C)

  每个用户问题是一个 Task
  一个 Task 内可能包含多轮 LLM 调用（因为 Tool 循环）

  Task 状态驱动 UI 渲染：
  - pending:   显示"等待中..."
  - running:   显示思考动画 + 流式文本
  - completed: 显示完整回复
  - failed:    显示错误信息
```

### 4.4 Coordinator：多 Agent 编排

```
src/coordinator/ — 多 Agent 协调（高级特性）：

  场景：复杂任务需要拆分给多个 Agent

  Main Agent（Claude Sonnet/Opus）
    ├── Sub-Agent 1: 读取文件
    ├── Sub-Agent 2: 搜索代码
    └── Sub-Agent 3: 执行测试

  Coordinator 的职责：
  1. 拆分任务 → 分配给子 Agent
  2. 管理子 Agent 的并发执行
  3. 汇总子 Agent 的结果
  4. 向主 Agent 报告
```

```typescript
// src/coordinator/ — 多 Agent 编排（简化版）

class Coordinator {
  private mainAgent: Assistant;
  private subAgents: Map<string, Assistant> = new Map();

  async dispatchSubTask(task: SubTask): Promise<SubTaskResult> {
    // 1. 为子任务创建轻量级 Agent
    const subAgent = new Assistant({
      model: 'claude-haiku-4-5',  // 子 Agent 用便宜模型
      tools: task.allowedTools,    // 限制可用工具
      maxTokens: 4096,
    });

    this.subAgents.set(task.id, subAgent);

    // 2. 执行子任务
    const result = await subAgent.run(task.instruction);

    // 3. 返回结果给主 Agent
    return {
      taskId: task.id,
      output: result.content,
      tokenUsage: result.tokenUsage,
    };
  }

  async runParallel(tasks: SubTask[]): Promise<SubTaskResult[]> {
    // 并行执行多个子任务
    return Promise.all(tasks.map(t => this.dispatchSubTask(t)));
  }
}
```

---

## 5. Tool 系统：文件读写 / 命令执行 / 搜索

### 5.1 Tool 接口设计：Tool.ts

```typescript
// src/Tool.ts — Tool 基类定义

interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: ZodSchema;        // Zod 验证输入
  isReadOnly: boolean;           // 是否只读（只读工具不需要确认）
  requiresConfirmation: boolean; // 是否需要用户确认
}

abstract class Tool {
  abstract readonly name: string;
  abstract readonly description: string;
  abstract readonly inputSchema: ZodSchema;

  // 是否需要用户确认才能执行
  get requiresConfirmation(): boolean {
    return !this.isReadOnly;
  }

  // 执行工具
  abstract execute(input: unknown): Promise<ToolResult>;

  // 转换为 Anthropic API 的 tool schema
  toSchema(): AnthropicTool {
    return {
      name: this.name,
      description: this.description,
      input_schema: zodToJsonSchema(this.inputSchema),
    };
  }
}

interface ToolResult {
  output: string;
  isError?: boolean;
  metadata?: Record<string, unknown>;
}
```

### 5.2 内置工具集：builtin-tools 包

```
packages/@claude-code-best/builtin-tools/ — 内置工具清单：

  ┌─────────────────────────────────────────────────────────┐
  │  文件操作                                                │
  │  ├─ Read File      读取文件内容（支持行范围）             │
  │  ├─ Write File     写入/创建文件                         │
  │  ├─ Edit File      精准编辑文件（搜索替换）               │
  │  ├─ List Dir       列出目录内容                          │
  │  └─ MultiEdit      批量编辑多个文件                      │
  ├─────────────────────────────────────────────────────────┤
  │  命令执行                                                │
  │  ├─ Bash           执行 Shell 命令                       │
  │  └─ Background     后台执行长时间命令                     │
  ├─────────────────────────────────────────────────────────┤
  │  搜索                                                    │
  │  ├─ Grep Search    ripgrep 模式搜索                      │
  │  ├─ Glob Search    文件名模式匹配                        │
  │  └─ Semantic Search 语义搜索（向量匹配）                  │
  ├─────────────────────────────────────────────────────────┤
  │  浏览器                                                  │
  │  └─ Web Browser    Puppeteer 网页浏览                    │
  └─────────────────────────────────────────────────────────┘
```

```typescript
// 内置工具实现示例：ReadFile

class ReadFileTool extends Tool {
  name = 'Read';
  description = '读取文件内容。支持指定行范围以减少 Token 消耗。';
  isReadOnly = true;  // 只读，不需要确认

  inputSchema = z.object({
    file_path: z.string().describe('文件的绝对路径'),
    offset: z.number().optional().describe('起始行号（1-indexed）'),
    limit: z.number().optional().describe('读取行数'),
  });

  async execute(input: { file_path: string; offset?: number; limit?: number }) {
    const content = await Bun.file(input.file_path).text();
    const lines = content.split('\n');
    
    const start = (input.offset ?? 1) - 1;
    const end = input.limit ? start + input.limit : lines.length;
    const selected = lines.slice(start, end);
    
    return {
      output: selected.map((l, i) => `${start + i + 1}: ${l}`).join('\n'),
      metadata: { totalLines: lines.length },
    };
  }
}

// 内置工具实现示例：Bash

class BashTool extends Tool {
  name = 'Bash';
  description = '在用户的 Shell 中执行命令。对于长时间运行的命令，考虑后台执行。';
  isReadOnly = false;  // 写操作，需要确认
  requiresConfirmation = true;

  inputSchema = z.object({
    command: z.string().describe('要执行的 Shell 命令'),
    timeout: z.number().optional().default(30000).describe('超时毫秒'),
  });

  async execute(input: { command: string; timeout?: number }) {
    const proc = Bun.spawn(['bash', '-c', input.command], {
      cwd: process.cwd(),
      timeout: input.timeout,
    });
    
    const stdout = await new Response(proc.stdout).text();
    const stderr = await new Response(proc.stderr).text();
    const exitCode = await proc.exited;
    
    return {
      output: stdout + (stderr ? `\nSTDERR: ${stderr}` : ''),
      isError: exitCode !== 0,
      metadata: { exitCode },
    };
  }
}
```

### 5.3 权限模型与安全沙箱

```
工具权限模型：

  ┌─────────────┬──────────────┬──────────────┐
  │ 工具类型     │ 是否确认      │ 示例         │
  ├─────────────┼──────────────┼──────────────┤
  │ 只读工具     │ 自动执行      │ Read, Grep   │
  │ 写入工具     │ 需要确认      │ Write, Edit  │
  │ 危险命令     │ 强制确认      │ Bash(rm/sudo)│
  │ MCP 工具     │ 首次确认      │ 第三方工具    │
  └─────────────┴──────────────┴──────────────┘

  权限检查流程：
  1. Tool 声明 isReadOnly / requiresConfirmation
  2. Bash 工具额外检查命令内容（rm, sudo, chmod 等）
  3. 用户可设置 "auto-approve" 策略跳过确认
  4. AGENTS.md 可声明项目级别的工具权限
```

```typescript
// 权限检查（简化版）
async function checkToolPermission(
  tool: Tool,
  input: unknown,
  config: Config,
): Promise<boolean> {
  // 1. 只读工具直接通过
  if (tool.isReadOnly) return true;

  // 2. 检查 auto-approve 配置
  if (config.autoApprove.includes(tool.name)) return true;

  // 3. Bash 工具特殊检查
  if (tool.name === 'Bash') {
    const cmd = (input as { command: string }).command;
    const dangerous = /\b(rm|sudo|chmod|chown|mkfs|dd)\b/.test(cmd);
    if (dangerous) {
      return await promptUser(`⚠️ 危险命令：${cmd}\n确认执行？`);
    }
  }

  // 4. 需要确认的工具，弹出确认框
  if (tool.requiresConfirmation) {
    return await promptUser(`执行 ${tool.name}？`);
  }

  return true;
}
```

### 5.4 Agent Tools 扩展机制

```typescript
// packages/@claude-code-best/agent-tools/ — 高级 Agent 工具

// 这些工具不直接操作文件系统，而是操作 Agent 自身

const AGENT_TOOLS = {
  // Task 工具：创建子任务
  Task: '将复杂任务拆分为子任务，每个子任务由独立的 Agent 执行',

  // Query 工具：单次查询模式
  QueryEngine: '非交互式查询，获取一次性回答',

  // Memory 工具：读写持久化记忆
  Memory: '读取/更新 .claude/ 目录下的项目记忆',
};
```

```
Tool 注册流程：

  src/tools.ts — 工具注册表

  function registerAllTools(): Tool[] {
    return [
      // 1. 内置工具（builtin-tools 包）
      ...builtinTools,

      // 2. Agent 工具（agent-tools 包）
      ...agentTools,

      // 3. MCP 工具（动态加载）
      ...mcpTools,

      // 4. 插件工具（Channels）
      ...channelTools,
    ];
  }

  最终 Claude 看到的 tools 参数：
  [
    { name: "Read", description: "读取文件..." },
    { name: "Write", description: "写入文件..." },
    { name: "Bash", description: "执行命令..." },
    { name: "Grep", description: "搜索代码..." },
    { name: "mcp__github__create_issue", description: "..." },
    ...
  ]
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Agent 循环 | ReAct 模式：LLM → Tool → Result → LLM... 直到无 Tool Call |
| 流式处理 | AsyncGenerator 逐 chunk 处理，实时渲染到终端 |
| Task 模型 | 每个用户问题 = 一个 Task，管理状态和 Token |
| Coordinator | 主 Agent 拆分子任务，子 Agent 用便宜模型并行执行 |
| Tool 基类 | name + description + inputSchema + execute() |
| 内置工具 | Read/Write/Edit/Bash/Grep/Glob/Browser |
| 权限模型 | 只读自动执行，写操作需确认，危险命令强制确认 |

> **下一章**：Context 与 Prompt 工程——System Prompt 构建、CLAUDE.md 加载、Token 预算。

---

## 6. Context 与 Prompt 工程

### 6.1 System Prompt 构建流程

```
System Prompt 的组装过程：

  ┌─────────────────────────────────────────────────┐
  │  System Prompt（最终发送给 Claude 的系统指令）     │
  │                                                  │
  │  1. 基础身份 Prompt                               │
  │     "你是 Claude Code, 一个 AI 编程助手..."       │
  │                                                  │
  │  2. 工具说明                                      │
  │     "你可以使用以下工具：Read, Write, Bash..."     │
  │                                                  │
  │  3. 项目上下文                                    │
  │     CLAUDE.md 的内容                              │
  │     AGENTS.md 的内容                              │
  │                                                  │
  │  4. 环境信息                                      │
  │     操作系统、当前目录、时间、Shell 类型           │
  │                                                  │
  │  5. 安全规则                                      │
  │     "不得执行 rm -rf /, 不得泄露 API Key..."      │
  │                                                  │
  │  6. 输出格式指令                                  │
  │     "使用 Markdown, 代码块标注语言..."            │
  └─────────────────────────────────────────────────┘
```

```typescript
// src/context.ts — System Prompt 构建（伪代码还原）

async function buildSystemPrompt(
  tools: Tool[],
  projectContext: ProjectContext,
  env: EnvironmentInfo,
): Promise<string> {
  const sections: string[] = [];

  // 1. 基础身份
  sections.push(`You are Claude Code, an interactive CLI tool that helps 
users with software engineering tasks. You operate directly in the user's 
terminal and have access to their file system and shell.`);

  // 2. 环境信息
  sections.push(`## Environment
- OS: ${env.os} ${env.arch}
- Shell: ${env.shell}
- CWD: ${env.cwd}
- Date: ${new Date().toISOString()}
- Editor: ${env.editor || 'none'}`);

  // 3. 可用工具列表
  const toolDescriptions = tools
    .map(t => `- ${t.name}: ${t.description}`)
    .join('\n');
  sections.push(`## Available Tools\n${toolDescriptions}`);

  // 4. 项目上下文（CLAUDE.md）
  if (projectContext.claudeMd) {
    sections.push(`## Project Instructions\n${projectContext.claudeMd}`);
  }

  // 5. 安全规则
  sections.push(`## Safety Rules
- Never execute destructive commands without user confirmation
- Never expose API keys or secrets in output
- Always prefer non-destructive file operations
- Respect .gitignore patterns`);

  return sections.join('\n\n');
}
```

### 6.2 项目上下文：CLAUDE.md 加载机制

```
CLAUDE.md / AGENTS.md 加载层级：

  ~/.claude/CLAUDE.md          ← 全局级（所有项目共享）
    ↓ 合并
  /project/CLAUDE.md           ← 项目根目录
    ↓ 合并
  /project/.claude/CLAUDE.md   ← .claude 子目录
    ↓ 合并
  /project/AGENTS.md           ← Agent 行为指令

  加载顺序：全局 → 项目根 → .claude 子目录 → AGENTS.md
  后加载的覆盖/补充先加载的
```

```typescript
// src/context/ — 上下文加载器

async function loadProjectContext(cwd: string): Promise<ProjectContext> {
  const context: ProjectContext = { claudeMd: '', agentsMd: '' };

  // 1. 全局 CLAUDE.md
  const globalPath = path.join(os.homedir(), '.claude', 'CLAUDE.md');
  if (await fileExists(globalPath)) {
    context.claudeMd += await readFile(globalPath);
  }

  // 2. 项目根 CLAUDE.md
  const projectRoot = await findProjectRoot(cwd);
  const projectPath = path.join(projectRoot, 'CLAUDE.md');
  if (await fileExists(projectPath)) {
    context.claudeMd += '\n\n' + await readFile(projectPath);
  }

  // 3. .claude 子目录
  const dotClaudePath = path.join(projectRoot, '.claude', 'CLAUDE.md');
  if (await fileExists(dotClaudePath)) {
    context.claudeMd += '\n\n' + await readFile(dotClaudePath);
  }

  // 4. AGENTS.md
  const agentsPath = path.join(projectRoot, 'AGENTS.md');
  if (await fileExists(agentsPath)) {
    context.agentsMd = await readFile(agentsPath);
  }

  return context;
}
```

### 6.3 Context Window 管理与 Token 预算

```
Token 预算管理策略：

  Claude 的 Context Window：200K tokens

  ┌─────────────────────────────────────────────┐
  │  System Prompt         ~2K-5K tokens        │
  │  项目上下文（CLAUDE.md）~1K-3K tokens       │
  │  对话历史              动态增长              │
  │  工具结果              可能很大（文件内容）   │
  │  预留输出空间          ~16K tokens           │
  └─────────────────────────────────────────────┘

  当总 Token 接近上限时的处理策略：
  1. 截断工具结果（文件内容只保留关键部分）
  2. 压缩历史对话（摘要化早期对话）
  3. 丢弃旧的工具调用结果
  4. 提示用户开始新对话
```

```typescript
// Token 管理（简化版）

class ContextManager {
  private maxTokens = 200_000;
  private reservedForOutput = 16_384;
  
  async fitMessages(
    messages: Message[],
    systemPrompt: string,
  ): Promise<Message[]> {
    const systemTokens = await countTokens(systemPrompt);
    let budget = this.maxTokens - systemTokens - this.reservedForOutput;
    
    // 从最新消息开始，向前保留
    const fitted: Message[] = [];
    for (let i = messages.length - 1; i >= 0; i--) {
      const msg = messages[i];
      const tokens = await countTokens(JSON.stringify(msg));
      
      if (budget - tokens < 0) {
        // 预算不足，截断
        break;
      }
      
      budget -= tokens;
      fitted.unshift(msg);
    }
    
    // 如果丢弃了历史，添加摘要
    if (fitted.length < messages.length) {
      const droppedCount = messages.length - fitted.length;
      fitted.unshift({
        role: 'system',
        content: `[已省略 ${droppedCount} 条早期消息以节省上下文空间]`,
      });
    }
    
    return fitted;
  }
}
```

### 6.4 成本追踪：cost-tracker

```typescript
// src/cost-tracker.ts — 成本追踪

interface TokenPricing {
  inputPerMillion: number;
  outputPerMillion: number;
  cacheReadPerMillion: number;
  cacheWritePerMillion: number;
}

const PRICING: Record<string, TokenPricing> = {
  'claude-sonnet-4-6': {
    inputPerMillion: 3.0,
    outputPerMillion: 15.0,
    cacheReadPerMillion: 0.3,
    cacheWritePerMillion: 3.75,
  },
  'claude-haiku-4-5': {
    inputPerMillion: 0.80,
    outputPerMillion: 4.0,
    cacheReadPerMillion: 0.08,
    cacheWritePerMillion: 1.0,
  },
};

class CostTracker {
  private totalCost = 0;
  private totalTokens = { input: 0, output: 0 };

  track(model: string, usage: TokenUsage) {
    const pricing = PRICING[model];
    const cost =
      (usage.input * pricing.inputPerMillion +
       usage.output * pricing.outputPerMillion +
       usage.cacheRead * pricing.cacheReadPerMillion) / 1_000_000;
    
    this.totalCost += cost;
    this.totalTokens.input += usage.input;
    this.totalTokens.output += usage.output;
  }

  // 在状态栏显示：Token: 12.5K | Cost: $0.042
  getSummary(): string {
    const k = (n: number) => (n / 1000).toFixed(1) + 'K';
    return `Token: ${k(this.totalTokens.input + this.totalTokens.output)} | Cost: $${this.totalCost.toFixed(3)}`;
  }
}
```

---

## 7. MCP 集成与外部扩展

### 7.1 MCP 协议集成：mcp-client 包

```
MCP（Model Context Protocol）：

  Claude Code 如何调用外部工具？

  传统方式：每个工具硬编码在 builtin-tools 里
  MCP 方式：通过标准协议连接任意外部工具服务器

  ┌──────────┐     MCP 协议      ┌──────────────┐
  │          │ ◄──────────────► │ MCP Server 1  │
  │ Claude   │     stdio/SSE    │ (GitHub)      │
  │ Code     │                  └──────────────┘
  │ (Client) │     MCP 协议      ┌──────────────┐
  │          │ ◄──────────────► │ MCP Server 2  │
  └──────────┘     stdio/SSE    │ (Database)    │
                                └──────────────┘
```

```typescript
// packages/@claude-code-best/mcp-client/ — MCP 客户端

import { Client } from '@modelcontextprotocol/sdk/client';

class MCPManager {
  private clients: Map<string, Client> = new Map();

  async connectServer(config: MCPServerConfig): Promise<Tool[]> {
    const client = new Client({
      name: 'claude-code',
      version: '2.3.0',
    });

    // 连接 MCP Server（通过 stdio 或 SSE）
    if (config.transport === 'stdio') {
      await client.connect(new StdioTransport({
        command: config.command,
        args: config.args,
      }));
    } else {
      await client.connect(new SSETransport(config.url));
    }

    this.clients.set(config.name, client);

    // 获取 Server 提供的工具列表
    const { tools } = await client.listTools();

    // 将 MCP 工具包装为内部 Tool 格式
    return tools.map(t => new MCPToolWrapper(config.name, t, client));
  }
}

// MCP 工具包装器
class MCPToolWrapper extends Tool {
  name: string;        // 格式：mcp__<server>__<tool>
  description: string;

  constructor(serverName: string, mcpTool: MCPTool, client: Client) {
    this.name = `mcp__${serverName}__${mcpTool.name}`;
    this.description = mcpTool.description;
    this.client = client;
    this.mcpToolName = mcpTool.name;
  }

  async execute(input: unknown): Promise<ToolResult> {
    const result = await this.client.callTool({
      name: this.mcpToolName,
      arguments: input,
    });
    return { output: JSON.stringify(result.content) };
  }
}
```

### 7.2 Channels 插件与 Marketplace

```
Channels 插件系统：

  启动命令：
  ccb --channels plugin:name@marketplace

  工作方式：
  1. 从 Marketplace 下载插件
  2. 插件本质是一个 MCP Server
  3. 自动注册工具到 Claude 的工具列表

  示例插件：
  - github: GitHub Issue/PR 管理
  - slack:  Slack 消息发送
  - notion: Notion 页面操作
  - jira:   Jira 工单管理

  src/plugins/ — 插件管理器
  ├── ChannelManager.ts   ← 插件安装/卸载/更新
  ├── PluginRegistry.ts   ← 插件注册表
  └── Marketplace.ts      ← 市场 API 交互
```

### 7.3 Bridge 通信层：IPC / LAN / Remote

```
src/bridge/ — 进程间通信层：

  三种通信模式：

  1. Pipe IPC（本地进程间通信）
     同一台机器上的多个 CCB 实例通信
     场景：IDE 插件 ↔ CCB 终端
     命令：/pipes

  2. LAN（局域网通信）
     同一网络内的设备通信
     场景：从手机控制桌面上的 CCB
     传输：WebSocket

  3. Remote Control（远程控制）
     通过云服务中继
     场景：远程服务器上的 CCB
     传输：WebSocket + OAuth
     命令：ccb --remote-control
```

```typescript
// src/bridge/ — 通信层（简化版）

interface Bridge {
  // 发送消息
  send(message: BridgeMessage): Promise<void>;
  // 接收消息
  onMessage(handler: (msg: BridgeMessage) => void): void;
  // 连接状态
  isConnected(): boolean;
}

type BridgeMessage =
  | { type: 'user_input'; content: string }
  | { type: 'assistant_output'; content: string }
  | { type: 'tool_call'; name: string; input: unknown }
  | { type: 'tool_result'; output: string }
  | { type: 'status'; state: 'thinking' | 'idle' };
```

### 7.4 Chrome Use 与 Computer Use

```
高级交互工具：

  1. Chrome Use（浏览器自动化）
     packages/@ant/claude-for-chrome-mcp/
     通过 MCP 协议控制 Chrome 浏览器
     ├── 打开网页
     ├── 点击元素
     ├── 填写表单
     ├── 截屏
     └── 提取页面内容

  2. Computer Use（桌面操作）
     packages/@ant/computer-use-mcp/
     packages/@ant/computer-use-input/
     packages/@ant/computer-use-swift/  (macOS)
     ├── 鼠标移动/点击
     ├── 键盘输入
     ├── 屏幕截图
     └── 窗口管理

     Computer Use 本质：
     Claude 看到屏幕截图 → 决定操作 → 执行操作 → 再截图
     这是一个"看-想-做"循环
```

---

## 8. 高级特性与生产化

### 8.1 语音模式：voice/ 模块

```
src/voice/ — 语音输入模式：

  启用：/voice doubao

  工作流：
  麦克风 → 豆包 ASR SDK → 文本 → 作为用户输入发送

  依赖：
  - doubaoime-asr（豆包语音识别 SDK）
  - audio-capture-napi（音频采集原生模块）

  优势：
  - 无需 Anthropic OAuth（使用第三方 ASR）
  - 支持中文语音
  - 流式识别（边说边转文字）
```

### 8.2 Buddy 协作模式

```
src/buddy/ — 多人协作：

  启用：FEATURE_BUDDY=1

  场景：多人共享同一个 CCB Session

  工作方式：
  User A ─┐
           ├──→ 共享的 CCB Session ──→ Claude
  User B ─┘

  功能：
  - 多人同时输入
  - 共享上下文和对话历史
  - 实时同步工具执行结果
  - 权限隔离（只有 Owner 可执行危险操作）
```

### 8.3 可观测性：Langfuse + Sentry + OpenTelemetry

```typescript
// 三件套集成

// 1. Langfuse — LLM 调用追踪
// @langfuse/otel + @langfuse/tracing
// 每次 LLM 调用自动记录：
// - 输入/输出 Token
// - 延迟
// - 成本
// - Prompt 版本

// 2. Sentry — 错误追踪
// @sentry/node
// 捕获运行时异常：
// - Tool 执行失败
// - API 调用超时
// - 未处理的 Promise Rejection

// 3. OpenTelemetry — 分布式追踪
// @opentelemetry/* 全家桶
// 追踪完整链路：
// 用户输入 → System Prompt 构建 → API 调用 → Tool 执行 → 渲染输出
```

```
可观测性架构：

  CCB 运行时
    │
    ├── Langfuse Exporter ──→ Langfuse Dashboard
    │   (Trace / Span / Score)    LLM 质量监控
    │
    ├── Sentry SDK ─────────→ Sentry Dashboard
    │   (Error / Exception)       错误告警
    │
    └── OTLP Exporter ──────→ Grafana / Jaeger
        (Traces / Metrics)        全链路追踪

  可选依赖（通过 Feature Flag 控制启用）
```

### 8.4 Daemon 后台进程与 SSH 远程

```
src/daemon/ — 后台守护进程：

  场景：长时间运行的任务不占用终端
  CCB 退出后，Daemon 继续执行任务

  启动方式：
  ccb → 执行任务 → 检测到长时间任务 → 自动转 Daemon
  或者手动：ccb --daemon

src/ssh/ — SSH 远程连接：

  场景：在远程服务器上运行 CCB
  本地终端 ←SSH→ 远程 CCB 实例

  工作流：
  1. 本地 ccb --ssh user@server
  2. SSH 连接到远程服务器
  3. 在远程启动 CCB 实例
  4. 双向同步输入/输出
```

---

## 全书总结

```
┌────────────────────────────────────────────────────────────────┐
│          Claude Code 源码解读 · 知识地图                        │
│                                                                │
│  Ch.1  项目架构     src/ 30+ 模块 / Bun + React Ink / Monorepo │
│  Ch.2  启动流程     entrypoints → bootstrap → main.tsx         │
│  Ch.3  终端 UI      React Ink 渲染 / 组件体系 / Vim 模式       │
│  Ch.4  Agent 循环   ReAct Loop / 流式处理 / Coordinator        │
│  Ch.5  Tool 系统    基类设计 / 内置工具 / 权限沙箱              │
│  Ch.6  Prompt 工程  System Prompt / CLAUDE.md / Token 预算     │
│  Ch.7  MCP 集成     MCP Client / Channels / Bridge / 浏览器    │
│  Ch.8  高级特性     语音 / Buddy / 可观测性 / Daemon / SSH     │
│                                                                │
│  8 章 32 节，从入口到内核，完整拆解一个生产级 AI 编程助手。     │
└────────────────────────────────────────────────────────────────┘
```

> 🎉 **核心架构一句话总结**：CLI 入口 → Bootstrap 初始化 → React Ink 渲染终端 UI → ReAct Agent 循环调用 Claude API + Tool → MCP 扩展外部能力 → Langfuse/Sentry 生产化监控。
