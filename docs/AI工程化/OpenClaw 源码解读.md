# OpenClaw 源码解读

> OpenClaw（370k Star）——全平台多通道 AI 助手的开源实现。从 Gateway 架构、消息通道系统、Agent 核心、Session 模型、Tool 体系、Plugin SDK、语音 / Canvas / 安全沙箱，到生产化部署，拆解一个真正的"AI 操作系统"级项目。

---

## 1. 项目概览与架构总览

### 1.1 项目背景：什么是 OpenClaw

```
OpenClaw 是什么？

  一个运行在你自己设备上的全平台 AI 助手
  不是 Chatbot，是"AI 操作系统"

  核心理念：
  1. Local-first — 数据在你自己的设备上
  2. 全通道 — 25+ 消息平台统一接入
  3. 插件化 — 任何人都可以扩展
  4. 语音原生 — Voice Wake + Talk Mode

  规模：
  - 370k Star / 76.5k Fork / 44,964 Commits
  - TypeScript 91.8% / MIT License
  - 由 Peter Steinberger（知名 iOS 开发者）创建
  - 吉祥物：Molty — 太空龙虾 🦞
```

```
OpenClaw vs Claude Code vs ChatGPT：

  ┌──────────────┬──────────────┬──────────────┐
  │              │ Claude Code  │ OpenClaw     │
  ├──────────────┼──────────────┼──────────────┤
  │ 定位         │ 编程 CLI 助手 │ 全平台 AI 助手│
  │ 交互界面     │ 终端 REPL    │ 25+ 消息平台  │
  │ 架构核心     │ React Ink    │ Gateway 控制面│
  │ 扩展机制     │ MCP          │ Plugin SDK   │
  │ 运行方式     │ CLI 前台进程  │ Daemon 后台   │
  │ 多模态       │ 文本+代码    │ 语音+图片+视频│
  │ 部署方式     │ npm 安装     │ Docker/Fly.io│
  └──────────────┴──────────────┴──────────────┘
```

### 1.2 仓库结构全景图

```
openclaw/
├── src/                          # 核心源码（55+ 模块）
│   ├── entry.ts                  # ★ 程序入口
│   ├── bootstrap/                # 初始化引导
│   ├── gateway/                  # ★ Gateway 核心服务
│   ├── config/                   # 配置管理
│   ├── daemon/                   # 后台守护进程
│   │
│   ├── agents/                   # ★ Agent 核心
│   ├── sessions/                 # Session 生命周期
│   ├── routing/                  # 消息路由
│   ├── context-engine/           # 上下文引擎
│   ├── memory/                   # 持久记忆
│   ├── memory-host-sdk/          # 记忆主机 SDK
│   │
│   ├── channels/                 # ★ 通道抽象层
│   ├── pairing/                  # DM 配对安全
│   ├── auto-reply/               # 自动回复
│   ├── chat/                     # 聊天核心
│   │
│   ├── tools/                    # 内置工具
│   ├── commands/                 # 斜杠命令
│   ├── interactive/              # 交互确认
│   ├── flows/                    # 流程编排
│   ├── commitments/              # 承诺跟踪
│   │
│   ├── plugin-sdk/               # ★ 插件 SDK（100+ 导出）
│   ├── plugin-state/             # 插件状态
│   ├── plugins/                  # 插件管理
│   ├── hooks/                    # 生命周期钩子
│   │
│   ├── talk/                     # 语音模式
│   ├── tts/                      # 文本转语音
│   ├── realtime-transcription/   # 实时转写
│   ├── media/                    # 媒体处理
│   ├── media-understanding/      # 多模态理解
│   ├── image-generation/         # 图片生成
│   ├── video-generation/         # 视频生成
│   ├── music-generation/         # 音乐生成
│   │
│   ├── security/                 # 安全框架
│   ├── crestodian/               # 沙箱系统
│   ├── secrets/                  # 密钥管理
│   ├── proxy-capture/            # 代理捕获
│   │
│   ├── web/                      # Web 界面
│   ├── web-fetch/                # 网页抓取
│   ├── web-search/               # 网页搜索
│   ├── link-understanding/       # 链接理解
│   ├── tui/                      # 终端 UI
│   ├── terminal/                 # 终端管理
│   │
│   ├── cli/                      # CLI 命令
│   ├── wizard/                   # 安装向导
│   ├── cron/                     # 定时任务
│   ├── tasks/                    # 异步任务
│   ├── model-catalog/            # 模型目录
│   ├── mcp/                      # MCP 协议
│   ├── acp/                      # ACP 协议
│   ├── node-host/                # 节点管理
│   ├── i18n/                     # 国际化
│   ├── infra/                    # 基础设施
│   └── logging/                  # 日志系统
│
├── extensions/                   # 外部通道插件
│   ├── discord/                  # Discord
│   ├── whatsapp/                 # WhatsApp
│   ├── msteams/                  # Microsoft Teams
│   ├── matrix/                   # Matrix
│   ├── feishu/                   # 飞书
│   ├── line/                     # LINE
│   ├── qqbot/                    # QQ
│   ├── nostr/                    # Nostr
│   └── ...                       # 20+ 更多通道
│
├── apps/                         # 客户端应用
│   ├── macos/                    # macOS 菜单栏应用
│   ├── ios/                      # iOS 节点
│   └── android/                  # Android 节点
│
├── packages/                     # 共享包
├── ui/                           # Control UI（Web 管理界面）
├── skills/                       # 内置 Skill
├── config/                       # 默认配置
├── deploy/                       # 部署配置
├── docs/                         # 文档
├── qa/                           # QA 测试
└── package.json                  # pnpm Monorepo 根
```

### 1.3 技术栈选型：Node 24 + TypeScript + pnpm Workspace

| 层 | 技术 | 作用 |
|---|---|---|
| **运行时** | Node 24 / 22.16+ | 服务端 JS 运行时 |
| **语言** | TypeScript 91.8% | 类型安全 |
| **包管理** | pnpm Workspace | Monorepo 管理 |
| **构建** | tsdown（tsup 继任者） | TypeScript 打包 |
| **测试** | vitest | 单元 / 集成测试 |
| **代码规范** | oxlint + oxfmt | Rust 实现的超快 Lint |
| **原生应用** | Swift（macOS/iOS）+ Kotlin（Android） | 客户端 |
| **部署** | Docker / Fly.io / Render | 容器化部署 |
| **沙箱** | Docker / SSH / OpenShell | 工具隔离 |
| **协议** | MCP + ACP | 工具 / Agent 协议 |

### 1.4 构建系统与开发循环

```typescript
// package.json 核心脚本
{
  "bin": { "openclaw": "openclaw.mjs" },
  "scripts": {
    "build": "tsdown",              // 构建产物到 dist/
    "gateway:watch": "...",          // 开发模式（自动重载）
    "openclaw": "tsx src/entry.ts",  // 直接运行 TypeScript
    "ui:build": "...",               // 构建 Control UI
    "ui:dev": "...",                 // UI 开发模式
    "test": "vitest",
  }
}
```

```
开发循环：

  git clone → pnpm install → pnpm openclaw setup
    ↓
  pnpm gateway:watch（开发模式）
    ↓
  修改 src/ 代码 → 自动重载 → 测试
    ↓
  pnpm build → dist/（生产构建）

  关键点：
  1. pnpm openclaw ... 直接通过 tsx 运行 TypeScript
  2. pnpm build 产出 dist/ 供 npm 包 / Docker 使用
  3. extensions/* 在开发模式下直接加载源码
```

---

## 2. Gateway 核心架构

### 2.1 Gateway 是什么：控制平面概念

```
OpenClaw 的核心是 Gateway（网关）：

  Gateway 不是一个聊天机器人
  Gateway 是一个控制平面（Control Plane）

  ┌──────────────────────────────────────────────┐
  │  Gateway（控制平面）                          │
  │                                              │
  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐    │
  │  │ WA   │  │ TG   │  │ DC   │  │ Slack│    │
  │  │通道   │  │通道   │  │通道   │  │通道  │    │
  │  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘    │
  │     │         │         │         │          │
  │     └─────────┴────┬────┴─────────┘          │
  │                    ↓                         │
  │              消息路由引擎                      │
  │                    ↓                         │
  │    ┌───────────────┴───────────────┐         │
  │    ↓                               ↓        │
  │  Agent A（主）                   Agent B     │
  │  ├─ Session 1                   ├─ Session 3│
  │  └─ Session 2                   └─ Session 4│
  │    ↓                               ↓        │
  │  ┌─────────────────────────────────┐         │
  │  │  Tools / Skills / Memory / LLM  │         │
  │  └─────────────────────────────────┘         │
  └──────────────────────────────────────────────┘

  Gateway 的职责：
  1. 管理所有消息通道的连接
  2. 路由消息到正确的 Agent
  3. 管理 Session 生命周期
  4. 提供工具 / Skill / Memory
  5. 安全隔离（沙箱）
```

### 2.2 入口文件：entry.ts → bootstrap → Gateway

```
启动链路：

  openclaw gateway --port 18789 --verbose
    ↓
  openclaw.mjs → src/entry.ts
    ↓
  entry.compile-cache.ts       ← V8 编译缓存（加速启动）
    ↓
  entry.respawn.ts             ← 子进程重生（崩溃恢复）
    ↓
  entry.version-fast-path.ts   ← --version 快速退出
    ↓
  src/bootstrap/               ← 初始化链
    ├── loadConfig()           ← 加载 openclaw.json
    ├── initPlugins()          ← 注册所有插件
    ├── initChannels()         ← 连接消息通道
    ├── initAgents()           ← 初始化 Agent
    └── initSecurity()         ← 安全策略
    ↓
  src/gateway/                 ← Gateway 服务启动
    ├── HTTP Server            ← REST API + WebSocket
    ├── Channel Listeners      ← 各通道监听器
    └── Agent Harness          ← Agent 运行环境
```

### 2.3 配置体系：openclaw.json 深度解析

```typescript
// ~/.openclaw/openclaw.json — 最小配置
{
  "agent": {
    "model": "openai/gpt-4o",         // 模型提供商/模型 ID
  }
}

// 完整配置结构
{
  "agent": {
    "model": "anthropic/claude-sonnet-4-6",
    "thinkingLevel": "medium",          // 思考深度
  },
  "agents": {
    "defaults": {
      "workspace": "~/.openclaw/workspace",
      "sandbox": {
        "mode": "non-main",             // 非主 Session 隔离
        "backend": "docker",            // 沙箱后端
      },
    },
    // 多 Agent 路由
    "work": {
      "model": "anthropic/claude-opus-4-6",
      "channels": ["slack"],            // 只处理 Slack 消息
    },
    "personal": {
      "model": "openai/gpt-4o",
      "channels": ["telegram", "whatsapp"],
    },
  },
  "channels": {
    "telegram": {
      "token": "BOT_TOKEN",
      "dmPolicy": "pairing",           // DM 安全策略
    },
    "discord": {
      "token": "BOT_TOKEN",
      "dmPolicy": "pairing",
    },
  },
}
```

### 2.4 Daemon 守护进程与自动重启

```
src/daemon/ — 守护进程管理：

  安装命令：openclaw onboard --install-daemon

  macOS：launchd 用户服务
  Linux：systemd 用户服务
  Windows：WSL2 推荐

  Daemon 职责：
  1. 后台运行 Gateway
  2. 崩溃自动重启（entry.respawn.ts）
  3. 日志持久化
  4. 开机自启

  健康检查：openclaw doctor
  状态查看：openclaw status
```

---

## 3. 消息通道系统

### 3.1 通道抽象：Channel 接口与插件化设计

```
通道系统的核心设计：

  每个通道（WhatsApp、Telegram、Discord...）
  都是一个 Channel Plugin

  Channel Plugin 需要实现的接口：
  ┌──────────────────────────────────────┐
  │  ChannelPlugin                       │
  │                                      │
  │  setup()      ← 初始化连接           │
  │  onInbound()  ← 接收消息             │
  │  send()       ← 发送回复             │
  │  teardown()   ← 断开连接             │
  │                                      │
  │  配置 Schema  ← token / webhook 等   │
  │  DM Policy    ← 安全策略             │
  │  Capabilities ← 支持的功能           │
  │    ├─ 文本 / 图片 / 语音 / 视频      │
  │    ├─ 反应 / 回复 / 线程             │
  │    └─ 编辑 / 删除 / 转发             │
  └──────────────────────────────────────┘
```

```typescript
// Plugin SDK Channel 接口（简化版）

interface ChannelPlugin {
  // 通道名称
  readonly name: string;  // 'telegram' | 'discord' | ...

  // 初始化：建立与平台的连接
  setup(config: ChannelConfig): Promise<void>;

  // 接收到新消息时触发
  onInbound(envelope: InboundEnvelope): Promise<void>;

  // 发送消息到平台
  send(target: ChannelTarget, payload: ReplyPayload): Promise<void>;

  // 通道支持的功能
  capabilities: {
    text: true;
    images: boolean;
    voice: boolean;
    video: boolean;
    reactions: boolean;
    threads: boolean;
    editMessages: boolean;
  };
}

// 消息信封（统一格式）
interface InboundEnvelope {
  channel: string;           // 'telegram'
  sender: AccountId;         // 发送者
  text?: string;             // 文本内容
  media?: MediaAttachment[]; // 媒体附件
  replyTo?: string;          // 回复引用
  threadId?: string;         // 线程 ID
  timestamp: Date;
}
```

### 3.2 内置通道 vs 外部通道（extensions/）

```
通道分类：

  内置通道（src/channels/ 中）：
  ├── webchat     ← Web 聊天界面
  ├── irc         ← IRC 协议
  ├── signal      ← Signal 消息
  ├── imessage    ← iMessage（macOS）
  └── mattermost  ← Mattermost

  外部通道（extensions/ 中，可选安装）：
  ├── discord     ← Discord
  ├── whatsapp    ← WhatsApp（via Baileys）
  ├── telegram    ← Telegram Bot API
  ├── slack       ← Slack Bot
  ├── googlechat  ← Google Chat
  ├── msteams     ← Microsoft Teams
  ├── feishu      ← 飞书
  ├── line        ← LINE
  ├── qqbot       ← QQ
  ├── matrix      ← Matrix 协议
  ├── nostr       ← Nostr 协议
  ├── twitch      ← Twitch 聊天
  ├── tlon        ← Tlon（Urbit）
  ├── synology    ← Synology Chat
  ├── zalo        ← Zalo
  └── wechat      ← 微信

  为什么分离？
  1. 内置通道：轻量、无额外依赖
  2. 外部通道：有各自的 SDK 依赖（避免主包臃肿）
  3. 按需安装：用户只安装需要的通道
```

### 3.3 DM 安全：Pairing 配对机制

```
src/pairing/ — DM 安全机制：

  问题：OpenClaw 连接到真实消息平台
  → 任何人都可以私信你的 Bot
  → 如何防止未授权访问？

  解决方案：Pairing 配对

  ┌────────────────────────────────────────┐
  │  陌生人发消息给 Bot                     │
  │    ↓                                   │
  │  dmPolicy = "pairing"                  │
  │    ↓                                   │
  │  Bot 回复：请提供配对码 [A7X9]          │
  │    ↓                                   │
  │  管理员执行：                           │
  │  openclaw pairing approve telegram A7X9│
  │    ↓                                   │
  │  发送者加入本地白名单                   │
  │    ↓                                   │
  │  后续消息正常处理                       │
  └────────────────────────────────────────┘

  三种 DM 策略：
  - "pairing"  → 需要配对码（默认，最安全）
  - "closed"   → 完全拒绝陌生人
  - "open"     → 接受所有人（需显式启用）
```

### 3.4 消息流水线：Inbound → Agent → Outbound

```
完整的消息处理流水线：

  ① Inbound（入站）
  用户在 Telegram 发送消息
    ↓
  Telegram Channel Plugin.onInbound()
    ↓
  InboundEnvelope（统一消息格式）
    ↓
  ② 路由
  routing/ 根据 channel + sender 确定目标 Agent
    ↓
  ③ 安全检查
  pairing/ 检查 DM Policy
  security/ 检查权限
    ↓
  ④ Session 匹配
  sessions/ 查找或创建 Session
    ↓
  ⑤ Agent 处理
  agents/ 构建 Prompt → 调用 LLM → 执行 Tools
    ↓
  ⑥ Outbound（出站）
  ReplyPayload（统一回复格式）
    ↓
  reply-chunking（消息分段，适配平台限制）
    ↓
  Telegram Channel Plugin.send()
    ↓
  用户收到回复
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 项目定位 | 全平台 AI 助手，Local-first，25+ 通道 |
| Gateway | 控制平面，管理通道/Agent/Session/工具/安全 |
| 启动链 | entry.ts → bootstrap → gateway（含编译缓存/崩溃恢复） |
| 通道设计 | Plugin 化，统一 InboundEnvelope / ReplyPayload |
| DM 安全 | Pairing 配对机制，三种策略 |
| 消息流 | Inbound → 路由 → 安全 → Session → Agent → Outbound |

> **下一章**：Agent 与 Session 模型——Agent 核心、LLM 调用、Session 生命周期、多 Agent 路由。

---

## 4. Agent 与 Session 模型

### 4.1 Agent 核心：消息处理与 LLM 调用

```
src/agents/ — Agent 的本质：

  Agent ≠ LLM
  Agent = LLM + Tools + Memory + Context + Session

  OpenClaw 的 Agent 处理流程：

  ┌────────────────────────────────────────────┐
  │  Agent 处理一条消息                         │
  │                                            │
  │  ① 接收 InboundEnvelope                    │
  │     ↓                                      │
  │  ② 查找/创建 Session                       │
  │     ↓                                      │
  │  ③ 构建 Prompt                              │
  │     ├─ System Prompt（AGENTS.md / SOUL.md） │
  │     ├─ Session 历史                         │
  │     ├─ 可用工具列表                         │
  │     ├─ Skill 指令                           │
  │     └─ 用户消息                             │
  │     ↓                                      │
  │  ④ 调用 LLM（流式）                        │
  │     ↓                                      │
  │  ⑤ 解析 LLM 响应                           │
  │     ├─ 纯文本 → 直接回复                    │
  │     └─ Tool Call → 执行工具 → 回到 ④       │
  │     ↓                                      │
  │  ⑥ 构建 ReplyPayload                       │
  │     ↓                                      │
  │  ⑦ 通过 Channel 发送回复                   │
  └────────────────────────────────────────────┘
```

```typescript
// src/agents/ — Agent 核心循环（简化版伪代码）

class Agent {
  private model: ModelSession;
  private tools: ToolRegistry;
  private memory: MemoryStore;

  async handleMessage(
    envelope: InboundEnvelope,
    session: Session,
  ): Promise<ReplyPayload> {
    // 1. 构建消息列表
    const messages = [
      ...session.getHistory(),
      { role: 'user', content: envelope.text },
    ];

    // 2. 注入系统指令
    const systemPrompt = await this.buildSystemPrompt(session);

    // 3. Agent 循环（ReAct 模式）
    while (true) {
      const response = await this.model.chat({
        system: systemPrompt,
        messages,
        tools: this.tools.getSchemas(),
        stream: true,
      });

      // 4. 检查是否有 Tool Call
      if (response.toolCalls.length === 0) {
        // 纯文本回复，退出循环
        session.append(response);
        return { text: response.content };
      }

      // 5. 执行 Tool Calls
      for (const call of response.toolCalls) {
        const result = await this.tools.execute(
          call.name,
          call.arguments,
          session,  // 传入 Session 用于权限检查
        );
        messages.push({
          role: 'tool',
          toolCallId: call.id,
          content: JSON.stringify(result),
        });
      }
      // 回到循环顶部，让 LLM 处理工具结果
    }
  }
}
```

### 4.2 Session 模型：会话生命周期

```
src/sessions/ — Session 是什么？

  Session = 一次持续的对话
  不同于 Claude Code 的单次 Task，OpenClaw 的 Session 可以跨天持续

  Session 生命周期：

  创建 ──→ 活跃 ──→ 空闲 ──→ 归档
   │         ↑        │        │
   │         └────────┘        │
   │       （新消息激活）       │
   └──────────────────────────→│ （超时/手动 /new）
```

```typescript
// src/sessions/ — Session 模型

interface Session {
  id: string;
  agentId: string;                 // 归属的 Agent
  channelId: string;               // 来源通道
  senderId: AccountId;             // 发送者
  status: 'active' | 'idle' | 'archived';
  
  // 对话历史
  history: Message[];
  
  // Session 元数据
  createdAt: Date;
  lastActiveAt: Date;
  
  // 沙箱信息（非 main session 运行在沙箱中）
  sandbox?: SandboxInfo;
}

// Session 管理
class SessionManager {
  // 查找现有 Session 或创建新的
  async resolve(
    agentId: string,
    channelId: string,
    senderId: AccountId,
  ): Promise<Session> {
    // 1. 查找活跃 Session
    const existing = await this.store.find({
      agentId, channelId, senderId,
      status: ['active', 'idle'],
    });
    
    if (existing) {
      existing.status = 'active';
      existing.lastActiveAt = new Date();
      return existing;
    }
    
    // 2. 创建新 Session
    return this.store.create({
      agentId, channelId, senderId,
      status: 'active',
    });
  }
}
```

```
Session 相关的斜杠命令：

  /new       ← 开始新 Session（归档当前的）
  /reset     ← 清空 Session 历史
  /compact   ← 压缩 Session（摘要化历史，节省 Token）
  /status    ← 查看当前 Session 状态

  Session 工具（Agent 可调用）：
  sessions_list     ← 列出所有 Session
  sessions_history  ← 查看某个 Session 的历史
  sessions_send     ← 向另一个 Session 发消息
  sessions_spawn    ← 创建子 Session（Agent 编排）
```

### 4.3 多 Agent 路由：通道 → Agent 映射

```
多 Agent 路由机制：

  src/routing/ — 消息路由引擎

  配置示例：
  {
    "agents": {
      "work": {
        "model": "claude-opus-4-6",
        "channels": ["slack"],
      },
      "personal": {
        "model": "gpt-4o",
        "channels": ["telegram", "whatsapp"],
      },
      "code": {
        "model": "claude-sonnet-4-6",
        "channels": ["discord#dev-channel"],
      }
    }
  }

  路由规则：
  ┌──────────────┐     ┌──────────────┐
  │ Slack 消息    │────→│ work Agent   │
  └──────────────┘     │ (Claude Opus)│
                       └──────────────┘
  ┌──────────────┐     ┌──────────────┐
  │ Telegram 消息 │────→│ personal     │
  │ WhatsApp 消息 │────→│ Agent        │
  └──────────────┘     │ (GPT-4o)     │
                       └──────────────┘
  ┌──────────────┐     ┌──────────────┐
  │ Discord #dev │────→│ code Agent   │
  └──────────────┘     │ (Sonnet)     │
                       └──────────────┘

  每个 Agent：
  - 独立的 Workspace
  - 独立的 Session 池
  - 独立的 Model 配置
  - 独立的 Tool / Skill 权限
```

### 4.4 Context Engine 与持久记忆

```
src/context-engine/ — 上下文引擎：

  上下文的三层结构：

  ┌───────────────────────────────────────┐
  │  Layer 1：身份指令（永驻 System Prompt） │
  │  ├─ AGENTS.md   ← Agent 行为指令      │
  │  ├─ SOUL.md     ← 人格与价值观        │
  │  └─ TOOLS.md    ← 工具使用说明        │
  ├───────────────────────────────────────┤
  │  Layer 2：Session 历史（滑动窗口）     │
  │  ├─ 最近 N 轮对话                     │
  │  └─ 超出窗口的部分被 /compact 压缩    │
  ├───────────────────────────────────────┤
  │  Layer 3：持久记忆（Memory）           │
  │  ├─ 长期事实（用户偏好、项目信息）     │
  │  └─ 通过 memory/ + memory-host-sdk/   │
  └───────────────────────────────────────┘
```

```typescript
// src/memory/ — 持久记忆

interface MemoryStore {
  // 存储记忆
  save(key: string, content: string, metadata?: object): Promise<void>;
  
  // 检索相关记忆
  search(query: string, limit?: number): Promise<MemoryEntry[]>;
  
  // 列出所有记忆
  list(): Promise<MemoryEntry[]>;
  
  // 删除记忆
  delete(key: string): Promise<void>;
}

// 记忆后端（可插拔）
// - memory-host-sdk/   → 默认文件系统存储
// - extensions/memory-lancedb/ → LanceDB 向量存储
```

```
src/commitments/ — 承诺跟踪：

  独特功能：Agent 可以"承诺"未来要做的事

  示例：
  用户："明天提醒我检查服务器"
  Agent：创建 Commitment → 关联 Cron Job
  
  Commitment 结构：
  {
    description: "提醒用户检查服务器",
    dueDate: "2026-05-11T09:00:00",
    status: "pending",
    sessionId: "...",
  }
```

---

## 5. Tool 系统与 Skill 机制

### 5.1 内置工具集：bash / read / write / browser

```
src/tools/ — 内置工具体系：

  ┌─────────────────────────────────────────────┐
  │  工具分类                                    │
  │                                              │
  │  文件操作：                                   │
  │  ├─ read       ← 读取文件                    │
  │  ├─ write      ← 写入文件                    │
  │  └─ edit       ← 编辑文件（diff 模式）        │
  │                                              │
  │  系统操作：                                   │
  │  ├─ bash       ← 执行 Shell 命令             │
  │  └─ process    ← 进程管理                    │
  │                                              │
  │  网络操作：                                   │
  │  ├─ browser    ← 浏览器自动化                 │
  │  ├─ web-fetch  ← 网页抓取                    │
  │  └─ web-search ← 网页搜索                    │
  │                                              │
  │  会话操作：                                   │
  │  ├─ sessions_list    ← 列出会话              │
  │  ├─ sessions_history ← 查看历史              │
  │  ├─ sessions_send    ← 跨 Session 发消息     │
  │  └─ sessions_spawn   ← 创建子 Session        │
  │                                              │
  │  平台特有：                                   │
  │  ├─ canvas     ← Live Canvas 控制            │
  │  ├─ cron       ← 定时任务管理                │
  │  ├─ nodes      ← 节点设备管理                │
  │  ├─ discord    ← Discord 特有操作            │
  │  └─ gateway    ← Gateway 管理操作            │
  └─────────────────────────────────────────────┘
```

```typescript
// 工具定义格式（简化版）

interface ToolDefinition {
  name: string;
  description: string;
  parameters: JSONSchema;       // JSON Schema 参数定义
  
  // 执行函数
  execute(
    args: Record<string, unknown>,
    context: ToolContext,
  ): Promise<ToolResult>;
}

interface ToolContext {
  session: Session;             // 当前 Session
  agent: Agent;                 // 当前 Agent
  workspace: string;            // 工作目录
  sandbox?: SandboxRuntime;     // 沙箱运行时（如果有）
}

// 示例：bash 工具
const bashTool: ToolDefinition = {
  name: 'bash',
  description: 'Execute a shell command',
  parameters: {
    type: 'object',
    properties: {
      command: { type: 'string', description: 'The command to run' },
      cwd: { type: 'string', description: 'Working directory' },
      timeout: { type: 'number', default: 30000 },
    },
    required: ['command'],
  },
  
  async execute(args, context) {
    // 沙箱模式下通过 Docker 执行
    if (context.sandbox) {
      return context.sandbox.exec(args.command, args.cwd);
    }
    // 直接执行
    const result = await spawn(args.command, {
      cwd: args.cwd || context.workspace,
      timeout: args.timeout,
    });
    return { stdout: result.stdout, stderr: result.stderr };
  },
};
```

### 5.2 Skill 技能系统：SKILL.md 规范

```
skills/ — Skill 技能系统：

  Skill = 一组 Prompt 指令 + 可选文件
  Skill 不是代码插件，而是"指令集"

  ┌─────────────────────────────────────┐
  │  ~/.openclaw/workspace/skills/      │
  │  ├── daily-digest/                  │
  │  │   └── SKILL.md                   │
  │  ├── code-review/                   │
  │  │   └── SKILL.md                   │
  │  └── email-draft/                   │
  │      └── SKILL.md                   │
  │                                     │
  │  内置 skills/（仓库 skills/ 目录）   │
  │  ├── onboarding/                    │
  │  └── ...                            │
  └─────────────────────────────────────┘

  Skill 三种来源：
  1. Bundled（内置）— 仓库 skills/ 目录
  2. Managed（托管）— 从 ClawHub 安装
  3. Workspace（本地）— 用户自定义
```

```markdown
<!-- SKILL.md 示例：daily-digest -->

# Daily Digest

每天早上生成一份信息摘要。

## 触发条件
- 用户说"今日摘要"或"daily digest"
- Cron 触发（每天 8:00）

## 指令
1. 检查未读消息（通过 sessions_history 工具）
2. 检查日历事件（如果有 Google Calendar 集成）
3. 汇总 GitHub 通知
4. 格式化输出

## 输出格式
```
📅 [日期] 每日摘要
━━━━━━━━━━━━━━━━
📨 未读消息：X 条
📌 今日事项：...
🔔 GitHub 通知：...
```
```

### 5.3 斜杠命令：/status /new /think 等

```
src/commands/ — 斜杠命令系统：

  用户在任何通道中输入 /命令 触发

  ┌────────────┬─────────────────────────────────┐
  │ 命令        │ 作用                            │
  ├────────────┼─────────────────────────────────┤
  │ /status    │ 查看 Gateway 和 Session 状态     │
  │ /new       │ 开始新 Session                  │
  │ /reset     │ 清空当前 Session 历史            │
  │ /compact   │ 压缩历史（摘要化，节省 Token）   │
  │ /think     │ 设置思考深度（low/medium/high）  │
  │ /verbose   │ 开关详细模式                    │
  │ /trace     │ 开关调试追踪                    │
  │ /usage     │ Token 用量统计                   │
  │ /restart   │ 重启 Gateway                    │
  │ /activation│ 设置激活方式（mention/always）   │
  └────────────┴─────────────────────────────────┘
```

```typescript
// src/commands/ — 命令注册（简化版）

interface Command {
  name: string;              // 'status'
  aliases?: string[];        // ['s']
  description: string;
  
  // 执行命令
  execute(
    args: string[],
    session: Session,
    channel: ChannelPlugin,
  ): Promise<string>;
}

// /compact 命令实现
const compactCommand: Command = {
  name: 'compact',
  description: 'Summarize session history to save tokens',
  
  async execute(args, session) {
    const history = session.getHistory();
    
    // 调用 LLM 生成摘要
    const summary = await llm.chat({
      system: 'Summarize the following conversation concisely.',
      messages: [{ role: 'user', content: JSON.stringify(history) }],
    });
    
    // 替换历史为摘要
    session.replaceHistory([
      { role: 'system', content: `[Conversation summary]\n${summary}` },
    ]);
    
    return `✅ Compacted ${history.length} messages into summary.`;
  },
};
```

### 5.4 Cron 定时任务与 Webhooks

```
src/cron/ — 定时任务系统：

  Agent 可以创建定时任务：

  "每天早上 8 点给我发每日摘要"
    ↓
  Agent 调用 cron 工具
    ↓
  创建 CronJob：
  {
    schedule: "0 8 * * *",
    action: "发送每日摘要到 Telegram",
    sessionId: "...",
    skillRef: "daily-digest",
  }
    ↓
  Gateway 在指定时间触发
    ↓
  创建临时 Session → 执行 Skill → 发送结果

  管理命令：
  openclaw cron list
  openclaw cron delete <id>
```

```
Webhooks（自动化触发）：

  Gateway 暴露 Webhook 端点：
  POST /webhook/:hookId

  用途：
  1. GitHub Push → 通知 Agent 代码变更
  2. CI/CD 完成 → Agent 汇报结果
  3. 监控告警 → Agent 分析并通知
  4. Gmail Pub/Sub → Agent 处理新邮件

  配置：
  {
    "webhooks": {
      "github-push": {
        "secret": "...",
        "agent": "code",
        "skill": "code-review",
      }
    }
  }
```

```
src/interactive/ — 交互式确认：

  当 Agent 要执行危险操作时：

  Agent："我需要删除 data/ 目录，确认吗？"
    ↓
  interactive/ 发送确认请求到通道
    ↓
  用户在 Telegram/Discord 中回复 "是" 或 "否"
    ↓
  Agent 根据回复继续或取消

  不同于 CLI（直接 stdin），
  OpenClaw 的确认是跨通道异步的
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Agent 核心 | LLM + Tools + Memory + Context + Session |
| Agent 循环 | ReAct 模式：Prompt → LLM → Tool Call → 回到 LLM |
| Session | 可跨天持续，支持 /new /compact /reset |
| 多 Agent | 通道 → Agent 路由，每个 Agent 独立配置 |
| Context 三层 | 身份指令 + Session 历史 + 持久记忆 |
| 内置工具 | bash/read/write/edit/browser/sessions/canvas/cron |
| Skill 系统 | SKILL.md 指令集，三种来源（内置/托管/本地） |
| 定时任务 | Cron Job + Webhook 双触发机制 |

> **下一章**：Plugin SDK 与扩展开发——100+ 导出模块、Channel/Provider Plugin 开发、生命周期管理。

---

## 6. Plugin SDK 与扩展开发

### 6.1 Plugin SDK 架构：100+ 导出模块

```
src/plugin-sdk/ — 巨大的插件 SDK：

  为什么 Plugin SDK 有 100+ 导出？

  OpenClaw 几乎一切可扩展：
  ├─ 通道（Channel）     → 接入新消息平台
  ├─ 模型（Provider）    → 接入新 LLM 提供商
  ├─ 工具（Tool）        → 自定义工具
  ├─ 沙箱（Sandbox）     → 自定义隔离环境
  ├─ 记忆（Memory）      → 自定义记忆后端
  └─ 诊断（Diagnostic）  → 自定义健康检查

  SDK 模块分类：

  ┌─────────────────────────────────────────────┐
  │  核心运行时                                  │
  │  ├─ plugin-runtime     ← 插件基础运行时     │
  │  ├─ agent-runtime      ← Agent 运行时       │
  │  ├─ gateway-runtime    ← Gateway 运行时     │
  │  └─ config-runtime     ← 配置运行时         │
  │                                              │
  │  通道相关（Channel）                          │
  │  ├─ channel-runtime    ← 通道核心           │
  │  ├─ channel-setup      ← 通道初始化         │
  │  ├─ channel-inbound    ← 入站处理           │
  │  ├─ channel-streaming  ← 流式输出           │
  │  ├─ channel-envelope   ← 消息封装           │
  │  ├─ channel-contract   ← 通道契约           │
  │  └─ channel-actions    ← 平台特有操作       │
  │                                              │
  │  回复管线（Reply Pipeline）                  │
  │  ├─ reply-runtime      ← 回复核心           │
  │  ├─ reply-chunking     ← 消息分段           │
  │  ├─ reply-payload      ← 回复载荷           │
  │  ├─ reply-dedupe       ← 去重               │
  │  └─ reply-dispatch     ← 分发               │
  │                                              │
  │  安全相关                                    │
  │  ├─ security-runtime   ← 安全运行时         │
  │  ├─ sandbox            ← 沙箱接口           │
  │  ├─ ssrf-policy        ← SSRF 防护          │
  │  └─ command-auth       ← 命令鉴权           │
  │                                              │
  │  媒体相关                                    │
  │  ├─ media-runtime      ← 媒体处理           │
  │  ├─ media-store        ← 媒体存储           │
  │  ├─ media-generation   ← 媒体生成           │
  │  └─ tts-runtime        ← 语音合成           │
  │                                              │
  │  测试工具                                    │
  │  ├─ testing            ← 测试框架           │
  │  ├─ test-fixtures      ← 测试数据           │
  │  └─ plugin-test-api    ← 插件测试 API       │
  └─────────────────────────────────────────────┘
```

### 6.2 Channel Plugin 开发流程

```typescript
// extensions/telegram/ — Telegram 通道插件（简化版）

import {
  defineChannelPlugin,
  ChannelSetup,
  InboundEnvelope,
  ReplyPayload,
} from 'openclaw/plugin-sdk/channel-runtime';

export default defineChannelPlugin({
  name: 'telegram',
  version: '1.0.0',

  // 配置 Schema
  configSchema: {
    token: { type: 'string', required: true, secret: true },
    dmPolicy: { type: 'string', default: 'pairing' },
    allowFrom: { type: 'array', items: { type: 'string' } },
  },

  // 初始化
  async setup(ctx: ChannelSetup) {
    const bot = new TelegramBot(ctx.config.token);

    // 注册消息监听
    bot.on('message', async (msg) => {
      const envelope: InboundEnvelope = {
        channel: 'telegram',
        sender: { id: String(msg.from.id), name: msg.from.first_name },
        text: msg.text,
        media: msg.photo ? [{ type: 'image', url: '...' }] : [],
        timestamp: new Date(msg.date * 1000),
      };

      // 交给 Gateway 处理
      await ctx.inbound(envelope);
    });

    await bot.startPolling();
    return { bot };
  },

  // 发送回复
  async send(target, payload: ReplyPayload, state) {
    const { bot } = state;

    if (payload.text) {
      await bot.sendMessage(target.id, payload.text, {
        parse_mode: 'Markdown',
      });
    }

    if (payload.media) {
      for (const m of payload.media) {
        if (m.type === 'image') {
          await bot.sendPhoto(target.id, m.url);
        }
      }
    }
  },

  // 支持的功能
  capabilities: {
    text: true,
    images: true,
    voice: true,
    video: true,
    reactions: true,
    threads: false,
    editMessages: true,
  },
});
```

### 6.3 Provider Plugin：自定义模型接入

```
extensions/ 中的 Provider Plugin：

  OpenClaw 支持任意 LLM 提供商：

  src/model-catalog/ — 模型目录
  ├─ openai       (GPT-4o, o3, o4-mini)
  ├─ anthropic    (Claude Opus/Sonnet/Haiku)
  ├─ google       (Gemini 2.5 Pro/Flash)
  ├─ xai          (Grok)
  ├─ deepseek     (DeepSeek V3/R1)
  ├─ mistral      (Mistral Large)
  ├─ ollama       (本地模型)
  ├─ lmstudio     (LM Studio 本地)
  └─ ...          (更多自定义)

  模型配置格式：
  "agent": {
    "model": "<provider>/<model-id>"
  }

  示例：
  "openai/gpt-4o"
  "anthropic/claude-sonnet-4-6"
  "ollama/llama3.2"
  "lmstudio/deepseek-r1"
```

```typescript
// Provider Plugin 接口（简化版）

import { defineProviderPlugin } from 'openclaw/plugin-sdk/provider-setup';

export default defineProviderPlugin({
  name: 'custom-llm',

  // 模型列表
  models: [
    { id: 'custom-model-v1', contextWindow: 128000, pricing: {...} },
  ],

  // 认证配置
  authSchema: {
    apiKey: { type: 'string', secret: true },
    baseUrl: { type: 'string' },
  },

  // 聊天补全
  async chat(request, auth) {
    const response = await fetch(`${auth.baseUrl}/v1/chat/completions`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${auth.apiKey}` },
      body: JSON.stringify({
        model: request.model,
        messages: request.messages,
        tools: request.tools,
        stream: request.stream,
      }),
    });
    return parseOpenAIResponse(response);
  },
});
```

### 6.4 Plugin 生命周期与状态管理

```
Plugin 生命周期：

  ┌────────────────────────────────────────┐
  │  发现 → 加载 → 初始化 → 运行 → 卸载   │
  └────────────────────────────────────────┘

  1. 发现（Discovery）
     - 内置插件：src/plugins/ 自动扫描
     - 外部插件：extensions/ 目录
     - npm 插件：pnpm add openclaw-plugin-xxx

  2. 加载（Loading）
     - 读取插件 manifest
     - 验证配置 Schema
     - 解析依赖

  3. 初始化（Setup）
     - 调用 plugin.setup()
     - 建立连接（通道 Bot、API 等）
     - 注册工具 / 命令

  4. 运行（Running）
     - 处理消息
     - 执行工具
     - 状态持久化

  5. 卸载（Teardown）
     - 调用 plugin.teardown()
     - 断开连接
     - 清理资源
```

```typescript
// src/plugin-state/ — 插件状态管理

interface PluginStateStore {
  // 持久化键值存储（跨重启保持）
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T): Promise<void>;
  delete(key: string): Promise<void>;
}

// 用途示例：
// - Channel Plugin 存储 OAuth Token
// - Memory Plugin 存储索引状态
// - Provider Plugin 缓存模型列表

// src/hooks/ — 生命周期钩子
interface PluginHooks {
  onGatewayReady?: () => Promise<void>;
  onSessionCreated?: (session: Session) => Promise<void>;
  onBeforeAgentCall?: (messages: Message[]) => Promise<Message[]>;
  onAfterAgentCall?: (response: AgentResponse) => Promise<void>;
  onConfigChanged?: (newConfig: Config) => Promise<void>;
}
```

---

## 7. 多媒体与语音

### 7.1 Talk Mode：语音对话架构

```
src/talk/ — 语音对话系统：

  OpenClaw 的语音不是"语音转文字再回复"
  而是完整的语音对话体验

  ┌────────────────────────────────────────────┐
  │  语音对话架构                               │
  │                                            │
  │  用户说话                                   │
  │    ↓                                       │
  │  Voice Wake（唤醒词检测）                   │
  │    "Hey Molty" / 自定义唤醒词              │
  │    ↓                                       │
  │  realtime-transcription/（实时转写）        │
  │    音频流 → 文字（流式，边说边转）          │
  │    ↓                                       │
  │  Agent 处理（正常的文本处理流程）           │
  │    ↓                                       │
  │  tts/（文本转语音）                        │
  │    文字 → 音频流                           │
  │    ↓                                       │
  │  播放语音回复                               │
  └────────────────────────────────────────────┘

  平台支持：
  - macOS：系统级 Voice Wake + 菜单栏 push-to-talk
  - iOS：Voice trigger forwarding
  - Android：Connect/Chat/Voice tabs
```

### 7.2 TTS 与实时转写

```typescript
// src/tts/ — 文本转语音

interface TTSProvider {
  name: string;
  
  // 文本 → 音频
  synthesize(
    text: string,
    options: TTSOptions,
  ): Promise<AudioBuffer>;
  
  // 流式合成（边生成边播放）
  synthesizeStream(
    text: string,
    options: TTSOptions,
  ): AsyncIterable<AudioChunk>;
}

// TTS 提供商
// - ElevenLabs（高质量，推荐）
// - System TTS（系统内置，免费降级方案）
// - OpenAI TTS
// - 自定义 Provider

// src/realtime-transcription/ — 实时转写
interface TranscriptionProvider {
  // 音频流 → 文字流
  transcribe(
    audioStream: ReadableStream<AudioChunk>,
  ): AsyncIterable<TranscriptionSegment>;
}

// TranscriptionSegment
interface TranscriptionSegment {
  text: string;           // 转写文字
  isFinal: boolean;       // 是否为最终结果
  confidence: number;     // 置信度
  timestamp: number;      // 时间戳
}
```

### 7.3 多媒体管线：图片 / 视频 / 音乐生成

```
OpenClaw 的多媒体生成能力：

  src/image-generation/ — 图片生成
  ├─ DALL·E 3 / GPT-Image
  ├─ Stable Diffusion
  └─ 自定义 Provider

  src/video-generation/ — 视频生成
  ├─ Runway
  ├─ Sora（OpenAI）
  └─ 自定义 Provider

  src/music-generation/ — 音乐生成
  ├─ Suno
  ├─ Udio
  └─ 自定义 Provider

  src/media-generation/ — 统一生成接口
  ┌────────────────────────────────────────┐
  │  MediaGenerationRouter                 │
  │                                        │
  │  用户："画一只太空龙虾"                 │
  │    ↓                                   │
  │  Agent 判断 → 调用 image-generation    │
  │    ↓                                   │
  │  Provider 生成图片                     │
  │    ↓                                   │
  │  media/ 存储 → 通过通道发送给用户      │
  └────────────────────────────────────────┘
```

### 7.4 Media Understanding：多模态理解

```
src/media-understanding/ — 多模态理解：

  用户发送图片/视频/音频 → Agent 能理解内容

  ┌──────────────────────────────────────┐
  │  用户发送一张照片到 Telegram          │
  │    ↓                                 │
  │  Channel Plugin 提取媒体 URL         │
  │    ↓                                 │
  │  media-understanding/ 处理           │
  │    ├─ 图片 → Vision API 描述         │
  │    ├─ 音频 → 转写为文字              │
  │    └─ 视频 → 关键帧提取 + 描述       │
  │    ↓                                 │
  │  描述文字注入到消息中                 │
  │    ↓                                 │
  │  Agent 基于描述回复                   │
  └──────────────────────────────────────┘

  src/link-understanding/ — 链接理解：
  用户发送 URL → 自动抓取摘要 → 注入上下文
```

---

## 8. 安全模型与生产部署

### 8.1 安全模型：沙箱与权限隔离

```
src/crestodian/ — 沙箱系统：

  OpenClaw 连接到真实消息平台
  → Agent 有 bash/read/write 工具
  → 必须隔离不同用户的操作

  沙箱策略：
  ┌────────────────────────────────────────┐
  │  Main Session（你自己）                 │
  │    → 无沙箱，完全访问                   │
  │    → Agent 可以操作你的文件系统         │
  │                                        │
  │  Non-Main Session（其他用户 / 群组）    │
  │    → 沙箱隔离                          │
  │    → agents.defaults.sandbox.mode:     │
  │      "non-main"                        │
  └────────────────────────────────────────┘

  三种沙箱后端：
  ┌───────────┬────────────────────────────┐
  │ 后端       │ 实现方式                   │
  ├───────────┼────────────────────────────┤
  │ Docker    │ 每个 Session 一个容器      │
  │           │ 文件系统隔离、网络隔离      │
  │           │ 默认后端                    │
  ├───────────┼────────────────────────────┤
  │ SSH       │ SSH 到远程主机执行          │
  │           │ 适合已有服务器的场景        │
  ├───────────┼────────────────────────────┤
  │ OpenShell │ 轻量级进程隔离             │
  │           │ 不需要 Docker              │
  └───────────┴────────────────────────────┘
```

```
工具权限矩阵：

  ┌─────────────┬────────┬─────────┐
  │ 工具         │ Main   │ Sandbox │
  ├─────────────┼────────┼─────────┤
  │ bash        │ ✅     │ ✅ 隔离 │
  │ read        │ ✅     │ ✅ 隔离 │
  │ write       │ ✅     │ ✅ 隔离 │
  │ edit        │ ✅     │ ✅ 隔离 │
  │ process     │ ✅     │ ✅ 隔离 │
  │ sessions_*  │ ✅     │ ✅      │
  ├─────────────┼────────┼─────────┤
  │ browser     │ ✅     │ ❌ 禁止 │
  │ canvas      │ ✅     │ ❌ 禁止 │
  │ nodes       │ ✅     │ ❌ 禁止 │
  │ cron        │ ✅     │ ❌ 禁止 │
  │ discord     │ ✅     │ ❌ 禁止 │
  │ gateway     │ ✅     │ ❌ 禁止 │
  └─────────────┴────────┴─────────┘
```

### 8.2 密钥管理与 SSRF 防护

```
src/secrets/ — 密钥管理：

  配置中的 Secret 字段标记为 secret: true
  → 不写入日志
  → 不显示在 UI
  → 加密存储

  密钥来源：
  1. 配置文件直接写入（开发用）
  2. 环境变量引用：$ENV_VAR
  3. 文件引用：file:///path/to/secret
  4. Secret Manager 集成（企业用）
```

```
src/proxy-capture/ + plugin-sdk/ssrf-policy — SSRF 防护：

  Agent 可以调用 web-fetch / browser 工具
  → 必须防止 SSRF（服务端请求伪造）

  防护策略：
  1. 禁止访问内网地址（127.0.0.1 / 10.* / 192.168.*）
  2. 禁止访问元数据服务（169.254.169.254）
  3. DNS 重绑定防护
  4. 可配置白名单 / 黑名单

  proxy-capture/：
  代理所有 HTTP 请求，记录审计日志
```

### 8.3 WebChat 与 Live Canvas

```
src/web/ — WebChat 界面：

  Gateway 内置 Web 聊天界面
  访问 http://localhost:18789

  功能：
  - 浏览器中与 Agent 对话
  - 查看 Session 列表
  - 管理配置
  - 查看日志

ui/ — Control UI（管理面板）：
  独立的 Web 管理界面
  pnpm ui:build 构建
  包含完整的 Gateway 管理功能
```

```
Live Canvas — A2UI（Agent-to-UI）：

  OpenClaw 独特功能：Agent 可以生成交互式 UI

  ┌────────────────────────────────────────┐
  │  用户："给我画一个看板"                 │
  │    ↓                                   │
  │  Agent 调用 canvas 工具                │
  │    ↓                                   │
  │  生成 HTML/JS/CSS                      │
  │    ↓                                   │
  │  推送到 Canvas 表面（macOS/Web/iOS）   │
  │    ↓                                   │
  │  用户看到实时渲染的交互界面            │
  │  ┌──────────────────────────────┐      │
  │  │  📋 任务看板                  │      │
  │  │  ┌─────┐ ┌─────┐ ┌─────┐   │      │
  │  │  │ TODO│ │ WIP │ │ Done│   │      │
  │  │  │     │ │     │ │     │   │      │
  │  │  │ ...│ │ ... │ │ ... │   │      │
  │  │  └─────┘ └─────┘ └─────┘   │      │
  │  └──────────────────────────────┘      │
  │  用户可以与 Canvas 交互                │
  │  交互事件回传给 Agent                  │
  └────────────────────────────────────────┘
```

### 8.4 生产部署：Docker / Fly.io / Daemon

```
三种部署方式：

  1. Daemon 模式（推荐，Local-first）
     openclaw onboard --install-daemon
     - macOS：launchd 用户服务
     - Linux：systemd 用户服务
     - 开机自启、崩溃恢复
     - 数据在本地

  2. Docker 部署
     docker-compose.yml 一键启动
     ┌──────────────────────────┐
     │  docker-compose.yml      │
     │                          │
     │  services:               │
     │    openclaw:              │
     │      image: openclaw     │
     │      ports:               │
     │        - "18789:18789"   │
     │      volumes:             │
     │        - ./data:/data    │
     │      env_file: .env      │
     └──────────────────────────┘

  3. Fly.io 部署（远程访问）
     fly.toml + render.yaml 配置
     适合需要远程访问的场景
     配合 Tailscale 更安全
```

```
生产化清单：

  ┌────────────────────────────────────────┐
  │  ✅ 安全                               │
  │  ├─ dmPolicy 设为 pairing             │
  │  ├─ 非 main Session 启用沙箱          │
  │  ├─ SSRF 防护已启用                    │
  │  ├─ Secret 使用环境变量                │
  │  └─ openclaw doctor 检查通过           │
  │                                        │
  │  ✅ 可靠性                             │
  │  ├─ Daemon 已安装（自动重启）          │
  │  ├─ 日志级别设为 info                  │
  │  ├─ 配置备份                           │
  │  └─ Token 用量监控（/usage）           │
  │                                        │
  │  ✅ 性能                               │
  │  ├─ V8 编译缓存已启用                  │
  │  ├─ Session compact 定期执行           │
  │  └─ 模型 failover 已配置              │
  └────────────────────────────────────────┘
```

---

## 全书总结

```
┌──────────────────────────────────────────────────────────────────┐
│          OpenClaw 源码解读 · 知识地图                              │
│                                                                  │
│  Ch.1  项目概览     370k Star / src/ 55+ 模块 / pnpm Monorepo   │
│  Ch.2  Gateway      控制平面 / entry.ts 启动链 / Daemon 守护     │
│  Ch.3  消息通道     25+ Channel Plugin / DM Pairing / 消息流水线 │
│  Ch.4  Agent        ReAct 循环 / Session 模型 / 多 Agent 路由    │
│  Ch.5  Tool & Skill 内置工具 / SKILL.md / 斜杠命令 / Cron       │
│  Ch.6  Plugin SDK   100+ 导出 / Channel/Provider 插件开发        │
│  Ch.7  多媒体       Voice Wake / TTS / 图片视频音乐生成          │
│  Ch.8  安全部署     crestodian 沙箱 / SSRF / Canvas / Docker    │
│                                                                  │
│  8 章 32 节，从控制平面到消息通道，完整拆解一个"AI 操作系统"。    │
└──────────────────────────────────────────────────────────────────┘
```

> 🎉 **核心架构一句话总结**：Gateway 控制平面 → 25+ Channel 通道接入 → 路由到 Agent → Session + ReAct 循环调用 LLM + Tools → Plugin SDK 实现一切可扩展 → crestodian 沙箱保障安全。
