# MCP 协议开发实战

> 从零构建你的第一个 MCP Server，让 AI 成为万能工具人。

---

## 1. MCP 是什么 —— AI 世界的 USB-C

### 1.1 从碎片化到标准化：为什么需要 MCP

你有没有遇到过这样的场景：

```
场景 1：你想让 Claude 读你的本地文件
  → 手动复制粘贴到对话框？文件太大粘不下？

场景 2：你想让 GPT 查你的数据库
  → 写一个 API → 包装成 Function Calling → 只能给 GPT 用
  → 换个模型？全部重写。

场景 3：你想让 AI 助手操控 Slack / GitHub / Jira
  → 每个 AI 产品都要单独开发插件
  → Claude 的插件给 ChatGPT 用不了
  → N 个 AI 产品 × M 个服务 = N×M 个集成
```

这就是 MCP 诞生前的现实：**每个 AI 产品都在重复造轮子**。

### MCP 的解决方案

MCP（**M**odel **C**ontext **P**rotocol，模型上下文协议）是 Anthropic 在 2024 年底发布的**开放标准**。它的目标很简单：让所有 AI 应用以**统一的方式**连接外部数据和工具。

```
没有 MCP 的世界（N×M 问题）：

  Claude ──→ GitHub 集成
  Claude ──→ Slack 集成
  Claude ──→ 数据库集成
  GPT   ──→ GitHub 集成（重新开发！）
  GPT   ──→ Slack 集成（重新开发！）
  GPT   ──→ 数据库集成（重新开发！）
  Gemini──→ ...（又要重新开发！）

  3 个 AI × 3 个服务 = 9 个集成

有 MCP 的世界（N+M 方案）：

  Claude ──┐
  GPT    ──┼──→ MCP 协议 ──→ GitHub MCP Server
  Gemini ──┘                  Slack MCP Server
                              数据库 MCP Server

  3 个 AI + 3 个 Server = 6 个组件（各开发一次）
```

> **一句话概括**：MCP 就是 AI 世界的 **USB-C**。不管什么设备（AI 模型），不管连什么外设（工具/数据源），用同一个接口标准就行。

### 为什么叫"模型上下文协议"

名字很直白：

- **Model**：AI 模型（Claude、GPT、Gemini 等）
- **Context**：上下文——文件内容、数据库记录、API 数据……一切 AI 需要"看到"或"操作"的外部信息
- **Protocol**：协议——沟通的标准格式和规则

所以 MCP = 让 AI 模型以标准化方式获取和操作外部上下文的协议。

---

### 1.2 MCP vs Function Calling vs Plugin —— 关键区别

你可能会问："这跟 OpenAI 的 Function Calling 有什么区别？跟 ChatGPT 的 Plugin 呢？"

区别很大。它们解决的问题层级不同：

```
层级对比：

  Function Calling（函数调用）
  → AI 模型层面的能力：模型能输出结构化的函数调用请求
  → 但"谁来执行函数、怎么连接外部服务"——不管

  Plugin / GPTs
  → 特定平台的解决方案：只在 ChatGPT 生态内有效
  → 换个 AI 平台 → 插件报废

  MCP（模型上下文协议）
  → 通用的连接标准：不绑定任何模型或平台
  → 写一次 MCP Server → Claude、Cursor、Cline、你的自定义 Agent 都能用
```

### 三者的详细对比

| 特性 | Function Calling | ChatGPT Plugin | MCP |
|------|-----------------|----------------|-----|
| 提出者 | OpenAI | OpenAI | Anthropic |
| 定位 | 模型能力 | 平台插件 | **通用协议** |
| 绑定平台 | ❌ 仅 OpenAI API | ❌ 仅 ChatGPT | ✅ 任何支持 MCP 的 Host |
| 执行方在哪 | 你的代码里 | OpenAI 服务器 | MCP Server（本地或远程） |
| 支持的能力 | 工具调用 | 工具 + 数据 | **工具 + 数据 + 提示模板** |
| 协议标准 | JSON Schema | OpenAPI | **JSON-RPC 2.0** |
| 状态管理 | 无 | 无 | 有（会话级别） |
| 开源 | 部分 | 否 | **完全开源** |

### 关键差异图解

```
Function Calling：
  你的代码 ──→ OpenAI API ──→ 模型返回 tool_calls
                                    │
              你自己执行函数 ←────────┘
  → 你负责一切：执行、连接、错误处理

MCP：
  MCP Host（Claude/Cursor）
      │
      ↓
  MCP Client ──→ MCP Server（独立进程）
                      │
                      ├── 暴露工具（Tools）
                      ├── 提供数据（Resources）
                      └── 提供模板（Prompts）
  → Server 是独立的、标准化的、可复用的
```

> **类比**：Function Calling 好比"你告诉 AI 你家有哪些工具，但每次用工具都得你亲手来"。MCP 好比"你开了一家工具店（MCP Server），任何 AI 顾客进来都能自助使用，不需要你一对一服务"。

---

### 1.3 谁在用 MCP？生态现状一览

MCP 虽然年轻（2024 年 11 月发布），但生态扩展速度远超预期。

### 支持 MCP 的 Host（AI 应用）

| Host | 类型 | MCP 支持 |
|------|------|---------|
| Claude Desktop | AI 助手 | ✅ 原生支持（官方出品） |
| Cursor | AI 编程 IDE | ✅ 原生支持 |
| Cline | VS Code 插件 | ✅ 原生支持 |
| Windsurf | AI 编程 IDE | ✅ 原生支持 |
| Zed | 编辑器 | ✅ 原生支持 |
| Continue | AI 编程助手 | ✅ 原生支持 |
| OpenAI Agents SDK | Agent 框架 | ✅ 已支持 |
| LangChain | Agent 框架 | ✅ 已支持 |

### 官方和社区 MCP Server

```
官方提供的 Server（开箱即用）：

  📁 Filesystem    → 读写本地文件
  🐙 GitHub        → 仓库操作、PR、Issue
  🐘 PostgreSQL    → 数据库查询
  📊 Google Drive  → 文档读取
  💬 Slack         → 消息发送和搜索
  🔍 Brave Search  → 网页搜索
  🐳 Docker        → 容器管理
  ☁️  AWS           → 云服务操作

社区开发的 Server（持续增长）：

  📝 Notion        → 笔记和数据库
  📧 Gmail         → 邮件操作
  📅 Google Calendar → 日历管理
  🎵 Spotify       → 音乐控制
  🏠 Home Assistant → 智能家居
  ... 数百个，而且每天都在增加
```

### MCP 的行业认可

2025 年以来的关键里程碑：

- **OpenAI** 宣布在 Agents SDK 中支持 MCP（最大的竞争对手也认了这个标准）
- **Google** 的 Gemini 生态开始支持 MCP
- **微软** 的 Copilot Studio 支持 MCP
- GitHub 上 MCP 相关仓库的 star 数持续飙升

> **判断标准**：当一个协议连它的竞争对手都在支持时，它就不仅仅是一个公司的项目了——它正在成为**事实标准**。MCP 正处于这个阶段。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| MCP 是什么 | 模型上下文协议，AI 世界的 USB-C |
| 解决的问题 | N×M 集成问题 → N+M 标准化方案 |
| vs Function Calling | FC 是模型能力，MCP 是通信协议 |
| vs Plugin | Plugin 锁平台，MCP 跨平台 |
| 三大原语 | Tools（工具）、Resources（数据）、Prompts（模板） |
| 生态现状 | Claude/Cursor/Cline 原生支持，OpenAI/Google 也已加入 |

> **下一章预告**：MCP 架构解剖 —— Host、Client、Server 三层架构、JSON-RPC 2.0 通信协议、Transport 层的选择。了解 MCP 内部是怎么运转的。
