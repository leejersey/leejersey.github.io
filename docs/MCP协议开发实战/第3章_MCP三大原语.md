# MCP 协议开发实战

> 从零构建你的第一个 MCP Server，让 AI 成为万能工具人。

---

## 3. MCP 的三大原语 —— Tools、Resources、Prompts

上一章我们看到了 MCP Server 对外暴露三类能力。这一章，我们深入每一类——它们各自是什么、长什么样、什么时候用哪个。

```
MCP 三大原语概览：

  ┌──────────────────────────────────────────────────┐
  │                  MCP Server                       │
  │                                                    │
  │   🔧 Tools          📄 Resources      💬 Prompts  │
  │   ──────────       ──────────────     ──────────  │
  │   AI 调用的函数     AI 读取的数据      可复用的     │
  │   执行操作          提供上下文          提示模板     │
  │                                                    │
  │   控制方：AI 模型   控制方：应用程序    控制方：用户  │
  └──────────────────────────────────────────────────┘
```

> **核心区别预告**：Tools 由 AI 决定何时调用；Resources 由应用程序决定何时加载；Prompts 由用户决定何时使用。记住这条主线，下面的内容会反复印证它。

---

### 3.1 Tools：让 AI 执行动作

Tools 是 MCP 中**最常用**的原语。如果你只学一个，学这个就够了。

### 什么是 Tool

Tool 就是你暴露给 AI 模型的**可调用函数**。AI 在对话过程中，可以自主决定"我需要调用这个工具来完成用户的请求"。

```
Tool 的核心特征：

  ① 由 AI 模型控制（Model-Controlled）
     → AI 分析用户的问题后，自己决定调不调、调哪个
     → 不是你手动触发的，是 AI 自主判断的

  ② 需要用户确认
     → Host 可以在 AI 调用 Tool 前弹窗问你"允许吗？"
     → 这是安全机制——防止 AI 乱删文件、乱发消息

  ③ 有输入有输出
     → 接收参数（JSON Schema 定义）
     → 返回结果（文本、图片、或其他内容）
```

### Tool 在协议层长什么样

当 Client 调用 `tools/list` 时，Server 返回的 Tool 描述是这样的：

```json
{
  "tools": [
    {
      "name": "get_weather",
      "description": "查询指定城市的当前天气信息",
      "inputSchema": {
        "type": "object",
        "properties": {
          "city": {
            "type": "string",
            "description": "城市名称，如 '北京'、'上海'"
          },
          "unit": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"],
            "description": "温度单位，默认 celsius"
          }
        },
        "required": ["city"]
      }
    }
  ]
}
```

注意这三个关键字段：

| 字段 | 作用 | 给谁看 |
|------|------|--------|
| `name` | 工具的唯一标识符 | 程序用 |
| `description` | 工具的自然语言描述 | **AI 模型用**——AI 靠这个判断该不该调 |
| `inputSchema` | JSON Schema 格式的参数定义 | AI 模型 + 校验逻辑 |

> **重点提醒**：`description` 是 Tool 最重要的字段之一。它写得好不好，直接决定了 AI 模型能不能正确地选择和调用这个工具。一个模糊的描述会让 AI 误判，一个精确的描述会让 AI 如臂使指。

### Tool 的调用与返回

当 AI 决定调用工具时，消息流是这样的：

```
调用请求（Client → Server）：
{
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": { "city": "北京" }
  }
}

成功返回（Server → Client）：
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "北京当前天气：25°C，晴，东北风3级"
      }
    ]
  }
}

错误返回（Server → Client）：
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "查询失败：城市名 'xxx' 无法识别"
      }
    ],
    "isError": true
  }
}
```

注意：错误返回中 `isError: true` 是给 AI 模型看的信号——告诉 AI"这次调用失败了，你可以换个参数再试，或者告诉用户出了什么问题"。

### Tool 适合做什么

```
✅ 适合用 Tool 的场景：

  • 执行操作        → 写文件、发邮件、创建 Issue
  • 查询外部 API    → 查天气、查股价、搜索网页
  • 计算与处理      → 运行代码、转换格式、生成图表
  • 数据库操作      → 插入记录、更新状态、执行 SQL

❌ 不适合用 Tool 的场景：

  • 提供静态数据    → 用 Resource（下一节）
  • 提供提示模板    → 用 Prompt（3.3 节）
  • 大量数据加载    → 用 Resource（Tool 返回应简洁）
```

> **一句话概括**：Tool = AI 的"手"。AI 靠它来**做事情**。

---

### 3.2 Resources：给 AI 喂数据

如果说 Tool 是 AI 的"手"，那 Resource 就是 AI 的"眼睛"——让 AI **看到**外部数据。

### 什么是 Resource

Resource 是 MCP Server 暴露给 AI 的**只读数据源**。它不执行操作，只提供信息。

```
Resource 的核心特征：

  ① 由应用程序控制（Application-Controlled）
     → 不是 AI 自己决定读什么，而是 Host 应用决定加载哪些 Resource
     → 比如：Cursor 自动把你打开的文件作为 Resource 传给 AI
     → 或者：用户在 Claude Desktop 的侧边栏手动选择 Resource

  ② 只读的
     → Resource 只提供数据，不修改任何东西
     → 想修改数据？那是 Tool 的活

  ③ 用 URI 标识
     → 每个 Resource 都有一个唯一的 URI（统一资源标识符）
     → 类似网页有 URL，Resource 有自己的 URI
```

### Resource 的 URI 规范

MCP 用 URI 来标识每一个 Resource，格式灵活：

```
常见的 Resource URI 格式：

  file:///home/user/documents/report.txt    → 本地文件
  db://mydb/users/123                       → 数据库记录
  config://app/settings                     → 应用配置
  github://repos/anthropic/mcp/readme       → GitHub 文件
  log://server/2025-04-01                   → 日志数据

  URI 的规则：
  ✅ 协议前缀（file://、db://、自定义://）+ 路径
  ✅ 由 Server 自行定义 URI 命名规范
  ✅ 必须全局唯一（在同一个 Server 内）
```

### Resource 在协议层长什么样

**静态 Resource**——列出所有可用资源：

```json
// Client 调用 resources/list，Server 返回：
{
  "resources": [
    {
      "uri": "file:///project/README.md",
      "name": "项目 README",
      "description": "项目的说明文档",
      "mimeType": "text/markdown"
    },
    {
      "uri": "db://mydb/users",
      "name": "用户表",
      "description": "所有注册用户的列表",
      "mimeType": "application/json"
    }
  ]
}
```

**读取 Resource**——获取具体内容：

```json
// Client 调用 resources/read：
{
  "method": "resources/read",
  "params": {
    "uri": "file:///project/README.md"
  }
}

// Server 返回：
{
  "result": {
    "contents": [
      {
        "uri": "file:///project/README.md",
        "mimeType": "text/markdown",
        "text": "# My Project\n\n这是一个示例项目..."
      }
    ]
  }
}
```

### 静态 Resource vs Resource 模板

MCP 支持两种 Resource：

```
① 静态 Resource（固定列表）
   → 在 resources/list 中列出，URI 是固定的
   → 适合：已知的、有限的资源
   → 例如：配置文件、README、特定数据表

② Resource 模板（动态 URI）
   → 在 resources/templates/list 中列出，URI 包含 {参数}
   → 适合：大量的、动态的资源
   → 例如：任意用户的信息 → db://users/{user_id}
```

Resource 模板的协议定义：

```json
{
  "resourceTemplates": [
    {
      "uriTemplate": "db://mydb/users/{user_id}",
      "name": "用户详情",
      "description": "根据 user_id 查询用户的详细信息",
      "mimeType": "application/json"
    },
    {
      "uriTemplate": "file:///logs/{date}.log",
      "name": "日志文件",
      "description": "指定日期的服务器日志",
      "mimeType": "text/plain"
    }
  ]
}
```

> **类比**：静态 Resource 好比书架上摆好的几本书——你看得到有哪些，直接拿就行。Resource 模板好比图书馆的搜索系统——书太多不能全列出来，但你给个书号就能找到任意一本。

### Resource 适合做什么

```
✅ 适合用 Resource 的场景：

  • 提供文件内容    → 源代码、文档、配置文件
  • 提供数据库数据  → 表结构、记录、查询结果
  • 提供实时状态    → 系统指标、日志、监控数据
  • 提供结构化信息  → API 文档、项目结构、依赖列表

❌ 不适合用 Resource 的场景：

  • 执行操作        → 用 Tool（Resource 是只读的）
  • AI 主动搜索数据  → 用 Tool（Resource 是被动的）
  • 写入或修改数据  → 用 Tool
```

> **一句话概括**：Resource = AI 的"眼睛"。AI 靠它来**看东西**。

---

### 3.3 Prompts：可复用的提示模板

Tool 是 AI 的"手"，Resource 是 AI 的"眼睛"，而 Prompt 是给 AI 的**"剧本"**——预先写好的指令模板，用户选择使用。

### 什么是 Prompt

Prompt 是 MCP Server 定义的**可复用提示模板**。它本质上是一组预设的消息（系统消息 + 用户消息），可以带参数。

```
Prompt 的核心特征：

  ① 由用户控制（User-Controlled）
     → 用户主动选择"我要用这个 Prompt"
     → 在 Claude Desktop 中，用户通过 / 命令或侧边栏选择
     → AI 不会自己自动使用某个 Prompt

  ② 本质是消息模板
     → 一个 Prompt 返回一个消息列表（messages）
     → 可以包含系统提示词（system）+ 用户消息（user）
     → 类似于把你常用的 prompt 做成了"快捷方式"

  ③ 可以带参数
     → 参数让同一个模板适配不同场景
     → 例如："代码审查"模板 + 参数{language: "python"}
```

### Prompt 在协议层长什么样

**列出所有 Prompt**：

```json
// Client 调用 prompts/list，Server 返回：
{
  "prompts": [
    {
      "name": "code_review",
      "description": "对指定语言的代码进行审查，给出改进建议",
      "arguments": [
        {
          "name": "language",
          "description": "编程语言",
          "required": true
        },
        {
          "name": "style",
          "description": "审查风格：strict（严格）或 friendly（友好）",
          "required": false
        }
      ]
    },
    {
      "name": "translate",
      "description": "将文本翻译为指定语言，保持原文风格",
      "arguments": [
        {
          "name": "target_language",
          "description": "目标语言，如 '中文'、'英语'、'日语'",
          "required": true
        }
      ]
    }
  ]
}
```

**获取 Prompt 内容**（带参数）：

```json
// Client 调用 prompts/get：
{
  "method": "prompts/get",
  "params": {
    "name": "code_review",
    "arguments": {
      "language": "python",
      "style": "strict"
    }
  }
}

// Server 返回一组消息：
{
  "result": {
    "description": "Python 代码审查（严格模式）",
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "你是一位资深的 Python 代码审查专家。请用严格标准审查以下代码，重点检查：\n1. 代码风格是否符合 PEP 8\n2. 是否有潜在的性能问题\n3. 错误处理是否完善\n4. 类型注解是否完整\n\n请逐条列出问题并给出修改建议。"
        }
      }
    ]
  }
}
```

### Prompt 可以嵌入 Resource

Prompt 的强大之处在于它能**组合其他原语**。一个 Prompt 的消息中可以引用 Resource：

```json
{
  "result": {
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "请审查以下代码文件："
        }
      },
      {
        "role": "user",
        "content": {
          "type": "resource",
          "resource": {
            "uri": "file:///project/src/main.py",
            "mimeType": "text/x-python",
            "text": "import os\n\ndef main():\n    ..."
          }
        }
      }
    ]
  }
}
```

这意味着：Prompt 模板可以自动把相关的文件内容、数据库记录等 Resource 注入到提示词中，用户不需要手动复制粘贴。

### Prompt vs 直接写提示词

你可能会问："我直接在对话框里打提示词不就行了？为什么要用 Prompt？"

```
直接写提示词的问题：

  ❌ 每次都要重新打一遍
  ❌ 不同的人写的提示词质量参差不齐
  ❌ 没办法自动注入上下文数据
  ❌ 提示词散落在各处，无法统一管理

MCP Prompt 的优势：

  ✅ 写一次，到处用——团队共享标准化提示词
  ✅ 带参数——同一个模板适配不同场景
  ✅ 嵌入 Resource——自动注入数据，不需要手动粘贴
  ✅ 集中管理——所有 Prompt 在 Server 中维护
  ✅ 版本控制——Prompt 在代码仓库中，可以迭代改进
```

### Prompt 适合做什么

```
✅ 适合用 Prompt 的场景：

  • 标准化工作流    → 代码审查、翻译、写日报、生成测试用例
  • 复杂提示词      → 需要精心设计的 system prompt
  • 团队共享        → 让整个团队用同样质量的提示词
  • 带数据的模板    → 需要自动注入文件或数据库内容

❌ 不适合用 Prompt 的场景：

  • 一次性的简单问题  → 直接在对话框打就行
  • AI 需要自主决策  → 用 Tool（Prompt 是用户触发的）
  • 提供数据        → 用 Resource
```

> **一句话概括**：Prompt = AI 的"剧本"。用户给 AI 一个**预设角色和任务**，AI 照着演。

---

### 3.4 三者的选型指南

三个原语都学完了。实际开发中，怎么决定用哪个？

### 对比总表

| 维度 | Tools | Resources | Prompts |
|------|-------|-----------|---------|
| **一句话** | AI 调用的函数 | AI 读取的数据 | 预设的提示模板 |
| **类比** | AI 的"手" | AI 的"眼睛" | AI 的"剧本" |
| **控制方** | AI 模型 | 应用程序 | 用户 |
| **方向** | 执行操作 | 提供信息 | 构造提示 |
| **读写** | 可读可写 | 只读 | 不涉及 |
| **触发方式** | AI 自主判断 | Host 自动加载或用户选择 | 用户主动选择 |
| **是否需要确认** | 通常需要 | 不需要 | 不需要 |
| **返回内容** | 操作结果 | 数据内容 | 消息列表 |
| **API 动词** | `tools/call` | `resources/read` | `prompts/get` |

### 决策树

遇到一个新功能，用这个决策树快速判断该用什么：

```
你的功能是什么类型的？
│
├── 需要执行操作（写入、修改、调用外部 API）
│   └── 用 Tool ✅
│       例：发邮件、写文件、创建 Issue、查天气
│
├── 需要提供数据（让 AI 看到某些信息）
│   └── 用 Resource ✅
│       例：读文件内容、查数据库表结构、看日志
│
├── 需要标准化提示词（给 AI 一个角色/任务模板）
│   └── 用 Prompt ✅
│       例：代码审查模板、翻译模板、日报生成模板
│
└── 不确定？看控制权：
    ├── AI 自己决定什么时候用  →  Tool
    ├── 应用自动加载          →  Resource
    └── 用户手动选择          →  Prompt
```

### 组合使用才是常态

在实际项目中，三大原语往往是**组合使用**的：

```
典型组合场景："代码审查 MCP Server"

  📄 Resource：暴露项目文件内容
     → uri: file:///project/src/{filename}
     → 让 AI 能"看到"代码

  🔧 Tool：在 GitHub 上创建 Review Comment
     → create_review_comment(file, line, comment)
     → 让 AI 能"执行"审查动作

  💬 Prompt：代码审查模板
     → 注入 Resource（代码文件）+ 预设审查标准
     → 用户选择"开始审查"时触发

  完整流程：
  ① 用户选择 Prompt → "代码审查模板"
  ② Prompt 自动注入 Resource → 代码文件内容
  ③ AI 阅读代码，决定调用 Tool → 创建审查评论
  ④ 用户看到审查结果 ✅
```

> **设计原则**：不要把所有功能都塞进 Tool 里。数据用 Resource 暴露，模板用 Prompt 定义，操作用 Tool 实现。**各司其职，组合才强大。**

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Tools | AI 调用的函数，AI 模型控制，用于执行操作 |
| Tool 关键字段 | name（标识符）、description（给 AI 看）、inputSchema（参数） |
| Resources | 只读数据源，应用程序控制，用 URI 标识 |
| 静态 vs 模板 | 静态列出固定资源，模板用 {参数} 匹配动态资源 |
| Prompts | 可复用提示模板，用户控制，可嵌入 Resource |
| Tool 类比 | AI 的"手"——做事情 |
| Resource 类比 | AI 的"眼睛"——看东西 |
| Prompt 类比 | AI 的"剧本"——定角色 |
| 选型关键 | 看控制权：AI 控制→Tool，应用控制→Resource，用户控制→Prompt |
| 最佳实践 | 三者组合使用，各司其职 |

> **下一章预告**：环境搭建与第一个 MCP Server（Python）。终于要写代码了！我们将用 Python SDK + FastMCP 在 5 分钟内创建一个能查天气的 MCP Server，并连上 Claude Desktop 实际体验。

