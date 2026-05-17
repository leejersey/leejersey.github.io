# AI 工作流自动化实战

> 用 n8n + LLM 构建真正省时间的自动化工作流——从内容生产、数据处理到监控告警，手把手实现"让 AI 替你干重复的活"。

---

## 1. 为什么需要 AI 工作流自动化

你每天有多少时间花在"搬运数据"上？从邮箱复制内容到文档，从 RSS 里筛选值得看的文章，从日志里找异常然后发到群里。这些活不难，但**每天重复就是小时级的浪费**。传统自动化能解决一部分——但遇到"需要理解内容"的任务就无能为力了。LLM 的加入，补上了这块拼图。

### 1.1 传统自动化 vs AI 自动化：LLM 带来了什么

```
传统自动化的能力边界：

  IFTTT / Zapier / Make
  ═══════════════════════════════════════
  ✅ 能做的（基于规则）：
  • 收到邮件 → 转发到 Slack
  • GitHub 有新 PR → 发通知
  • 每天 9 点 → 发送固定模板消息
  • 表单提交 → 写入数据库

  ❌ 做不了的（需要"理解"）：
  • 收到邮件 → 判断是否紧急 → 分类推送
  • RSS 更新 → 生成中文摘要 → 推送有价值的
  • 客户反馈 → 情感分析 → 分类统计
  • 日志异常 → 判断严重程度 → 生成原因分析
```

LLM 的加入，让工作流具备了三个关键能力：

| 能力 | 传统自动化 | AI 工作流 |
|:---|:---|:---|
| **理解自然语言** | ❌ 只能正则/关键词匹配 | ✅ 语义理解，上下文推理 |
| **处理非结构化数据** | ❌ 只能处理 JSON/CSV | ✅ PDF、邮件正文、图片 OCR |
| **模糊判断** | ❌ 只能 if-else 规则 | ✅ "这封邮件重要吗"、"这条日志严重吗" |
| **内容生成** | ❌ 只能填模板 | ✅ 摘要、翻译、改写、回复草稿 |
| **确定性执行** | ✅ 100% 可预测 | ⚠️ LLM 输出有随机性，需要约束 |

```
一个典型的"传统做不了、AI 能做"的场景：

  技术资讯自动日报
  ═══════════════════════════════════════
  传统方案：
  RSS 更新 → 转发全部链接到 Slack → 50 条未筛选信息
  → 你还是要自己看哪条有价值

  AI 方案：
  RSS 更新 → LLM 阅读每篇文章
           → 判断"是否和你的技术栈相关"
           → 每篇生成一句话摘要
           → 按重要性排序
           → 推送 Top 5 到 Telegram
  → 你每天只需要看 5 条精选
```

> 💡 **LLM 不是替代传统自动化，而是补全它**——发邮件、写数据库这些确定性操作还是用传统节点做。LLM 负责"理解、判断、生成"这些传统节点做不了的事。

### 1.2 工作流 vs Agent：确定性编排 vs 自主决策

很多人搞混了"AI 工作流"和"AI Agent"——它们解决的是不同层次的问题。

```
工作流 vs Agent 的核心区别：

  工作流（Workflow）
  ═══════════════════════════════════════
  • 预定义的执行路径（DAG 有向无环图）
  • 开发者决定"做什么、怎么做、按什么顺序"
  • LLM 只是其中一个节点
  • 可预测、可调试、可审计
  • 适合：重复性任务、批量处理、ETL 管线

  Agent
  ═══════════════════════════════════════
  • LLM 自主决定"做什么、用什么工具"
  • 开发者只定义"目标和可用工具"
  • LLM 是决策核心（ReAct 循环）
  • 灵活但不可预测
  • 适合：对话式交互、开放性任务
```

| 维度 | 工作流 | Agent |
|:---|:---|:---|
| **决策者** | 开发者（预定义路径） | LLM（运行时决策） |
| **执行顺序** | 固定（DAG） | 动态（ReAct 循环） |
| **可预测性** | ⭐⭐⭐ 高 | ⭐ 低 |
| **调试难度** | 简单（节点级排查） | 困难（LLM 推理不透明） |
| **适合任务** | 批量、重复、有固定流程 | 开放式、交互式 |
| **代表工具** | n8n / Make / Dify | LangGraph / AutoGPT |
| **LLM 角色** | 管线中的一个处理节点 | 整个系统的"大脑" |

```
同一个需求，两种实现：

  需求："帮我分析客户反馈并生成周报"

  工作流实现（确定性）：
  ─────────────────────
  ① 定时触发（每周五 17:00）
  ② 从数据库拉取本周反馈（SQL 查询）
  ③ LLM 批量分类（正面/负面/建议）
  ④ 统计各分类数量
  ⑤ LLM 生成周报文字
  ⑥ 发送到飞书群

  Agent 实现（自主决策）：
  ─────────────────────
  用户："帮我分析本周的客户反馈"
  Agent → 思考 → 调用数据库工具 → 分析 → 生成 → 回复

  哪个更好？→ 这个场景用工作流更好（固定流程、批量处理）
```

> 💡 **经验法则**：如果你能用流程图画出来、且每次执行步骤一样——用工作流。如果步骤不确定、需要根据结果临时调整——用 Agent。90% 的企业自动化需求是工作流。
### 1.3 哪些流程值得自动化：ROI 评估框架

不是所有任务都值得自动化。投入 8 小时搭一个每天省 2 分钟的工作流，4 个月才回本。用这个框架快速判断：

```
自动化 ROI 评估公式：

  每次手动耗时 × 每月执行次数 × 12 个月
  ──────────────────────────────────── = 投资回报率
           搭建 + 维护耗时

  示例 1：技术资讯日报
  ═══════════════════════════════════════
  手动耗时：30 分钟/天（浏览 RSS + 筛选 + 整理）
  频率：每天
  年耗时：30min × 365 = 182 小时
  搭建耗时：3 小时
  ROI = 182/3 = 60x ✅ 非常值得

  示例 2：年度述职 PPT 自动化
  ═══════════════════════════════════════
  手动耗时：4 小时
  频率：每年 1 次
  年耗时：4 小时
  搭建耗时：10 小时
  ROI = 4/10 = 0.4x ❌ 不值得
```

**优先自动化的四类场景：**

| 优先级 | 场景特征 | 典型例子 |
|:---|:---|:---|
| ⭐⭐⭐ | 高频 + 耗时 + 有固定流程 | 日报周报、数据ETL、内容发布 |
| ⭐⭐ | 高频 + 简单 + 需要判断 | 邮件分类、告警降噪、反馈分析 |
| ⭐ | 低频 + 很耗时 + 流程固定 | 竞品分析报告、合同审核 |
| ❌ | 低频 + 简单 + 无需判断 | 偶尔发一封邮件、改个配置 |

> 💡 **优先自动化你每天都在做且感觉"机械"的事**——如果做某件事时你的大脑在自动驾驶模式，那它就是最好的自动化候选。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **AI 自动化** | 传统自动化 + LLM 理解/判断/生成能力 |
| **工作流** | 预定义路径，确定性执行，LLM 是处理节点之一 |
| **Agent** | LLM 自主决策，动态执行，适合开放式任务 |
| **ROI 框架** | 年节省时间 ÷ 搭建维护时间 > 3 才值得投入 |
| **优先级** | 高频 + 耗时 + 固定流程 = 最值得自动化 |

---

## 2. 工具选型：n8n 核心概念与部署

工作流引擎的选择直接决定了你的开发效率和运维成本。我们选 n8n——不是因为它最强，而是因为它在"可视化操作 + 代码自由度 + AI 节点支持"三个维度上，对开发者最友好。

### 2.1 n8n vs Dify vs Make：工作流引擎选型

```
四个主流工作流平台定位：

  n8n ⭐ 推荐
  ═══════════════════════════════════════
  • 开源、自托管（数据在你手里）
  • 可视化拖拽 + Code 节点（JS/Python）
  • 原生 AI Agent / LLM Chain 节点
  • 400+ 内置集成（Gmail / Slack / GitHub ...）
  • 社区活跃，迭代极快

  Dify
  ═══════════════════════════════════════
  • 专注 LLM 应用编排（RAG / Agent）
  • 可视化 Prompt 调试
  • 适合 AI 对话应用
  • 通用工作流能力较弱（不擅长 ETL / 定时任务）

  Make（原 Integromat）
  ═══════════════════════════════════════
  • 商业 SaaS，无需自托管
  • 可视化体验最好
  • AI 节点有限（依赖第三方模块）
  • 按操作数计费，成本不可控

  Zapier
  ═══════════════════════════════════════
  • 最老牌的自动化平台
  • 集成数量最多（6000+）
  • AI 能力弱，Code 节点限制多
  • 按任务数计费，成本高
```

| 维度 | n8n | Dify | Make | Zapier |
|:---|:---|:---|:---|:---|
| **开源** | ✅ | ✅ | ❌ | ❌ |
| **自托管** | ✅ | ✅ | ❌ | ❌ |
| **AI 原生** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ |
| **代码自由度** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ |
| **通用集成** | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **定时任务** | ✅ | ⚠️ | ✅ | ✅ |
| **成本** | 免费（自托管） | 免费（自托管） | $9-34/月 | $20-69/月 |

> 💡 **选择建议**：如果你是开发者且需要 AI + 通用自动化 → **n8n**。如果你只做 AI 对话/RAG 应用 → **Dify**。如果你不想运维、预算充足 → **Make**。

### 2.2 Docker 部署与基础配置

一条命令启动 n8n，3 分钟跑起来：

```bash
# 最简启动（开发体验）
docker run -it --rm \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n
```

**生产级 Docker Compose 配置：**

```yaml
# docker-compose.yml
version: "3.8"

services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      # 基础配置
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://your-domain.com/
      # 数据库（生产环境用 PostgreSQL）
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=${DB_PASSWORD}
      # 加密密钥（保护 Credentials）
      - N8N_ENCRYPTION_KEY=${ENCRYPTION_KEY}
      # AI 节点需要的 API Key
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=n8n
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  n8n_data:
  postgres_data:
```

```bash
# 启动
docker compose up -d

# 访问 http://localhost:5678
# 首次访问会引导你创建管理员账号
```

| 部署方式 | 适用场景 | 数据库 |
|:---|:---|:---|
| `docker run` | 本地体验、快速验证 | SQLite（默认） |
| Docker Compose | 个人/团队生产使用 | PostgreSQL |
| Kubernetes | 企业级高可用 | PostgreSQL + Redis |

> 💡 **`N8N_ENCRYPTION_KEY` 必须设置且不能丢失**——n8n 用这个密钥加密存储所有 Credential（API Key、OAuth Token 等）。如果丢失密钥，所有已保存的 Credential 都无法解密，需要重新配置。
### 2.3 核心概念：Trigger / Node / Connection / Credential

n8n 的心智模型很简单：**触发器启动 → 节点处理 → 连接传递数据 → 凭证授权访问外部服务**。

::: v-pre
```
n8n 工作流的四个核心概念：

  ① Trigger（触发器）── 工作流的起点
  ═══════════════════════════════════════
  • Schedule Trigger：定时触发（cron 表达式）
  • Webhook Trigger：外部 HTTP 请求触发
  • Email Trigger：收到邮件时触发
  • 各类 App Trigger：GitHub PR、Slack 消息等

  ② Node（节点）── 执行具体操作
  ═══════════════════════════════════════
  • HTTP Request：调用任意 API
  • Code：运行 JavaScript / Python 脚本
  • AI Agent / LLM Chain：调用大语言模型
  • Gmail / Slack / Notion：操作具体应用
  • IF / Switch：条件分支
  • Split In Batches：循环批量处理

  ③ Connection（连接）── 节点间的数据流
  ═══════════════════════════════════════
  • 上一个节点的输出 = 下一个节点的输入
  • 数据格式：JSON 数组 [{ key: value }, ...]
  • 可以用表达式引用：&#123;&#123; $json.fieldName &#125;&#125;

  ④ Credential（凭证）── 安全存储的密钥
  ═══════════════════════════════════════
  • 集中管理所有 API Key / OAuth Token
  • AES-256 加密存储
  • 一次配置，所有工作流共享
```
:::

**第一个工作流：Hello World（每小时获取天气并推送）：**

```
Schedule Trigger (每小时)
    │
    ▼
HTTP Request (调用天气 API)
    │ response.json → 温度、天气描述
    ▼
Code (格式化消息)
    │ "北京 25°C 晴，适合外出"
    ▼
Telegram (推送消息)
```

n8n 中每个节点的输入输出都是 JSON 数组，节点之间用**表达式**传递数据：

```javascript
// Code 节点中引用上一个 HTTP Request 的输出
const temp = $input.first().json.main.temp;
const desc = $input.first().json.weather[0].description;

return [{
  json: {
    message: `当前温度 ${temp}°C，${desc}`
  }
}];
```

> 💡 **n8n 的学习曲线很平**——拖几个节点、连上线、点 Test Workflow 就能看到结果。建议先在 UI 上玩 30 分钟，比读任何文档都有效。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **n8n** | 开源自托管工作流引擎，可视化 + Code 节点 + AI 原生 |
| **Docker 部署** | 一条命令启动，生产环境用 PostgreSQL + 加密密钥 |
| **Trigger** | 工作流的起点：定时 / Webhook / 事件触发 |
| **Node** | 执行单元：HTTP / Code / AI / 应用集成 |
| **Credential** | AES-256 加密存储 API Key，全局共享 |

---

## 3. LLM 节点：让工作流拥有"理解力"

n8n 原生支持 AI 节点——不需要写代码调 API，拖一个 LLM Chain 节点进来，配好 Prompt 和凭证就能用。这章讲如何在工作流中高效使用 LLM。

### 3.1 接入 LLM：OpenAI / DeepSeek / Ollama

n8n 提供了三种 AI 节点，适用于不同场景：

```
n8n 的三种 AI 节点：

  ① Basic LLM Chain
  ═══════════════════════════════════════
  • 最简单：输入文本 → LLM 处理 → 输出文本
  • 适合：摘要、分类、翻译、改写
  • 配置：选模型 + 写 Prompt + 设参数

  ② AI Agent
  ═══════════════════════════════════════
  • 带工具调用：LLM 可以调用其他节点
  • 适合：需要查数据库、调 API 的复杂任务
  • 本质：n8n 内置了一个 ReAct Agent

  ③ Custom Code + OpenAI API
  ═══════════════════════════════════════
  • Code 节点直接调 HTTP API
  • 最灵活，可以用任何模型
  • 适合：n8n 原生节点不支持的模型
```

**配置 DeepSeek 作为 LLM 后端（性价比最优）：**

n8n 的 OpenAI 节点支持自定义 Base URL，可以直接接 DeepSeek：

```
配置步骤：

  1. 在 n8n 中添加 Credential
     → 类型选 "OpenAI API"
     → API Key: 填 DeepSeek 的 API Key
     → Base URL: https://api.deepseek.com

  2. 在 LLM Chain 节点中
     → 选择刚创建的 Credential
     → Model: deepseek-chat
     → Temperature: 0.3（工作流场景建议低温度）
```

**接入本地 Ollama（零成本 + 隐私保护）：**

```bash
# 1. 安装并启动 Ollama
ollama pull qwen2.5:7b
ollama serve  # 默认监听 http://localhost:11434

# 2. n8n 中配置
# Credential → OpenAI API
# Base URL: http://host.docker.internal:11434/v1
# API Key: ollama（随便填，Ollama 不校验）
# Model: qwen2.5:7b
```

| 模型方案 | 成本 | 质量 | 延迟 | 隐私 |
|:---|:---|:---|:---|:---|
| GPT-4o | ~$15/1M tokens | ⭐⭐⭐ | 2-5s | ❌ 数据发美国 |
| DeepSeek V3 | ~$1/1M tokens | ⭐⭐⭐ | 1-3s | ⚠️ 数据发国内 |
| Ollama 本地 | $0 | ⭐⭐ | 3-10s | ✅ 完全本地 |

> 💡 **工作流场景优先用 DeepSeek**——因为工作流中的 LLM 调用通常是"摘要、分类、提取"这类简单任务，不需要 GPT-4o 级别的推理能力。DeepSeek V3 的质量完全够用，成本是 GPT-4o 的 1/15。

### 3.2 Prompt 设计：结构化输出与 JSON Mode

工作流中 LLM 的输出必须**可解析**——下游节点要用。自由格式的文本回复在工作流中是灾难。

```
工作流 Prompt 的黄金法则：

  ❌ 糟糕的 Prompt（自由文本）
  ═══════════════════════════════════════
  "分析以下邮件内容"
  → LLM 回复："这封邮件是关于 Q2 OKR 的..."
  → 下游节点无法可靠提取"是否紧急"

  ✅ 好的 Prompt（结构化输出）
  ═══════════════════════════════════════
  "分析以下邮件，输出 JSON：
   {
     \"category\": \"work|personal|spam\",
     \"urgency\": \"high|medium|low\",
     \"summary\": \"一句话摘要\",
     \"action_required\": true/false
   }
   只输出 JSON，不要其他文字。"
  → LLM 回复：{"category":"work","urgency":"high",...}
  → 下游节点直接 JSON.parse() 使用
```

**n8n 中的 Prompt 模板（使用表达式变量）：**

::: v-pre
```
System Prompt:
你是一个邮件分析助手。对每封邮件进行分析，
输出严格的 JSON 格式，不要附加任何解释文字。

User Prompt:
请分析以下邮件：

发件人：&#123;&#123; $json.from &#125;&#125;
主题：&#123;&#123; $json.subject &#125;&#125;
正文：&#123;&#123; $json.body &#125;&#125;

输出格式：
{
  "category": "work|personal|spam",
  "urgency": "high|medium|low",
  "summary": "一句话中文摘要",
  "action_required": true或false
}
```
:::

**用 Code 节点做后处理（防止 LLM 输出不合规）：**

```javascript
// 解析 LLM 的 JSON 输出（带容错）
const raw = $input.first().json.text;

try {
  // 尝试直接解析
  const result = JSON.parse(raw);
  return [{ json: result }];
} catch (e) {
  // LLM 可能在 JSON 外面包了 ```json ... ```
  const match = raw.match(/\{[\s\S]*\}/);
  if (match) {
    return [{ json: JSON.parse(match[0]) }];
  }
  // 兜底：返回默认值
  return [{ json: { category: "unknown", urgency: "low", 
                     summary: raw.slice(0, 100), action_required: false } }];
}
```

> 💡 **永远在 LLM 节点后面加一个 Code 节点做 JSON 解析和校验**——LLM 的输出不是 100% 可靠的。有时候会多输出一句话、漏掉一个字段、或者格式不对。Code 节点做容错是工作流稳定运行的保障。
### 3.3 Token 管理与批量调用优化

工作流中 LLM 调用往往是批量的——50 篇 RSS 文章要逐条摘要、100 条反馈要逐条分类。不优化的话，成本和延迟都会失控。

```
批量 LLM 调用的三种策略：

  ① 逐条调用（最简单，最慢）
  ═══════════════════════════════════════
  50 篇文章 → 调 50 次 LLM
  总延迟：50 × 2s = 100s
  优点：每条独立处理，不会互相影响
  缺点：慢、API 调用次数多

  ② 批量合并（推荐）
  ═══════════════════════════════════════
  50 篇文章 → 每 5 篇合并为 1 个 Prompt → 调 10 次
  总延迟：10 × 3s = 30s
  优点：减少调用次数，降低延迟
  缺点：单次 Prompt 不能超过上下文窗口

  ③ 并发控制
  ═══════════════════════════════════════
  50 篇文章 → 5 个并发 × 10 条
  总延迟：10 × 2s = 20s
  优点：最快
  缺点：可能触发 API 速率限制
```

**n8n 中实现批量合并的 Code 节点：**

```javascript
// 将输入项按 5 条一组合并
const items = $input.all();
const batchSize = 5;
const batches = [];

for (let i = 0; i < items.length; i += batchSize) {
  const batch = items.slice(i, i + batchSize);
  const combined = batch.map((item, idx) => 
    `[${i + idx + 1}] 标题：${item.json.title}\n摘要：${item.json.description}`
  ).join('\n\n---\n\n');
  
  batches.push({
    json: {
      batch_text: combined,
      batch_indices: batch.map((_, idx) => i + idx),
    }
  });
}

return batches;
// 输出 10 个批次，每个包含 5 篇文章的文本
```

**Token 成本速算表：**

| 任务类型 | 输入 Token | 输出 Token | DeepSeek 单价 | 100 次成本 |
|:---|:---|:---|:---|:---|
| 一句话摘要 | ~500 | ~50 | ¥0.001 | ¥0.1 |
| 邮件分类 | ~300 | ~30 | ¥0.001 | ¥0.1 |
| 长文摘要 | ~3000 | ~200 | ¥0.005 | ¥0.5 |
| 数据提取 | ~1000 | ~100 | ¥0.002 | ¥0.2 |

> 💡 **工作流 LLM 成本极低**——大部分工作流任务每次调用不到 ¥0.01。一个日均运行 5 次、每次调 20 次 LLM 的工作流，月成本约 ¥3。比你一杯咖啡还便宜。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **LLM Chain** | 最简单的 AI 节点：文本输入→LLM→文本输出 |
| **DeepSeek 接入** | OpenAI Credential + 自定义 Base URL |
| **结构化输出** | Prompt 中要求 JSON 格式，下游可靠解析 |
| **JSON 容错** | Code 节点做 parse + 正则提取 + 兜底默认值 |
| **批量合并** | 多条数据合并为一个 Prompt，减少调用次数 |

---

## 4. 实战场景一：内容生产自动化

内容生产是 AI 工作流最高频的应用场景——每天都要做、流程固定、且 LLM 在摘要/改写/生成方面表现极好。这章给出三个可以直接复用的工作流。

### 4.1 技术资讯日报：RSS → LLM 摘要 → 推送

这是最经典的 AI 工作流入门案例——每天自动帮你读 RSS，筛选有价值的文章，生成精选日报。

```
工作流节点编排：

  Schedule Trigger (每天 8:00)
      │
      ▼
  RSS Feed Read (读取多个 RSS 源)
      │ 返回 30-50 篇文章
      ▼
  Code (过滤 24 小时内的文章)
      │ 筛选出 20 篇新文章
      ▼
  Split In Batches (每 5 篇一批)
      │
      ▼
  LLM Chain (批量分析 + 摘要)
      │ Prompt: "分析以下文章，输出 JSON"
      │ → 每篇：relevance_score + 一句话摘要
      ▼
  Code (按相关度排序 + 取 Top 5)
      │
      ▼
  Code (格式化为日报消息)
      │
      ▼
  Telegram / 飞书 / 邮件 (推送)
```

**LLM 分析的 Prompt 设计：**

::: v-pre
```
你是一个技术内容分析助手。我的技术栈是：
Python, FastAPI, Docker, AI/LLM, 前端 React。

请分析以下文章列表，为每篇文章输出 JSON 数组：
[
  {
    "index": 1,
    "relevance": 1-10（与我的技术栈相关度），
    "summary": "一句话中文摘要（20字以内）",
    "worth_reading": true/false
  }
]

文章列表：
&#123;&#123; $json.batch_text &#125;&#125;
```
:::

**过滤和排序的 Code 节点：**

```javascript
// 合并所有批次结果，按相关度排序取 Top 5
const allResults = $input.all().flatMap(item => {
  try { return JSON.parse(item.json.text); }
  catch { return []; }
});

const top5 = allResults
  .filter(r => r.worth_reading && r.relevance >= 6)
  .sort((a, b) => b.relevance - a.relevance)
  .slice(0, 5);

// 格式化为推送消息
const message = `📰 今日技术精选（${new Date().toLocaleDateString('zh-CN')}）\n\n` +
  top5.map((r, i) => `${i+1}. ${r.summary}\n   📎 相关度：${'⭐'.repeat(Math.min(r.relevance, 5))}`
  ).join('\n\n');

return [{ json: { message } }];
```

> 💡 **在 Prompt 中声明你的技术栈**——这是让 LLM 帮你"个性化筛选"的关键。前端工程师和后端工程师关注的 RSS 内容完全不同，LLM 需要知道你是谁才能正确评分。

### 4.2 社交媒体内容管线：选题到发布的全流程

自媒体内容创作是另一个高 ROI 场景——从选题灵感到最终发布，AI 可以参与每一个环节。

```
社交媒体内容管线：

  ① 选题收集（自动）
  Webhook Trigger ← 你在微信/Telegram 发一条灵感
      │
      ▼
  ② LLM 扩展选题
  "把这个灵感扩展为 3 个可能的文章角度，
   每个角度给出标题 + 目标读者 + 预估热度"
      │
      ▼
  ③ 人工选择（Wait 节点）
  推送 3 个选题到 Telegram → 你回复数字选一个
      │
      ▼
  ④ LLM 生成初稿
  "根据选题生成 800 字的技术分享文，
   风格：通俗易懂、有代码示例、有个人观点"
      │
      ▼
  ⑤ LLM 润色 + SEO
  "优化这篇文章：加小标题、优化开头吸引力、
   补充 3-5 个相关 hashtag"
      │
      ▼
  ⑥ 存入 Notion（待发布队列）
  Notion API → 创建页面 → 状态设为"待审核"
```

**人工审核环节（Wait + Webhook）：**

```
关键设计：人机协作

  ┌──────────────────────────────────────┐
  │  不要让 AI 全自动发布！               │
  │                                      │
  │  AI 生成初稿 → 推送给你审核           │
  │  你修改/确认 → 工作流继续执行         │
  │                                      │
  │  n8n 实现方式：                       │
  │  • Wait 节点 + Webhook               │
  │  • 发 Telegram 消息带"确认/修改"按钮   │
  │  • 你点"确认"→ 触发 Webhook → 继续    │
  └──────────────────────────────────────┘
```

> 💡 **内容生产工作流的原则是"AI 起草、人类把关"**——AI 负责 80% 的搬砖工作（选题扩展、初稿生成、SEO 优化），你只做 20% 的判断工作（选哪个角度、初稿哪里需要改）。这才是效率最大化。
### 4.3 会议纪要自动化：录音→转录→结构化整理

会议纪要是最耗时的"手工活"之一——听 1 小时会议、整理 30 分钟纪要。用 Whisper + LLM 可以压缩到 2 分钟。

```
会议纪要工作流：

  Webhook Trigger (接收上传的录音文件)
      │
      ▼
  HTTP Request (调用 Whisper API 转录)
      │ 输出：完整的文字转录
      ▼
  Code (按时间段切分长文本)
      │ 避免超出 LLM 上下文窗口
      ▼
  LLM Chain (结构化整理)
      │ Prompt: "将会议记录整理为结构化纪要"
      ▼
  Code (合并各段落输出)
      │
      ▼
  Notion API (创建会议纪要页面)
```

**LLM 整理的 Prompt：**

::: v-pre
```
请将以下会议转录整理为结构化会议纪要，格式如下：

## 会议基本信息
- 主题：（从内容推断）
- 时长：&#123;&#123; $json.duration &#125;&#125;

## 关键讨论点
1. [讨论点]：[结论或共识]

## 待办事项（Action Items）
- [ ] [具体任务] — 负责人：[姓名] — 截止日期：[如有]

## 决策记录
- [决策内容]

转录内容：
&#123;&#123; $json.transcript &#125;&#125;
```
:::

| 方案 | STT 成本 | LLM 成本 | 总成本/小时会议 |
|:---|:---|:---|:---|
| Whisper API + DeepSeek | $0.36 | ~$0.01 | ~$0.37 |
| faster-whisper(本地) + DeepSeek | $0 | ~$0.01 | ~$0.01 |
| 飞书妙记（对比） | 免费(企业版) | - | $0 |

> 💡 **会议纪要的核心价值是 Action Items**——与会者最想看的不是"谁说了什么"，而是"我要做什么"。在 Prompt 中强调提取待办事项和负责人。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **RSS 日报** | RSS → LLM 评分筛选 → 格式化推送，ROI 60x |
| **内容管线** | 选题→初稿→润色→审核→发布，AI 做 80% 人做 20% |
| **人机协作** | Wait + Webhook 实现人工审核节点 |
| **会议纪要** | Whisper STT + LLM 结构化，重点提取 Action Items |
| **成本控制** | 本地 Whisper + DeepSeek，每小时会议仅 ¥0.07 |

---

## 5. 实战场景二：数据处理与分析

传统自动化最头疼的场景就是"非结构化数据"——合同扫描件、用户反馈文本、竞品网页。以前需要人工读、人工分类、人工录入。现在 LLM 可以直接"看懂"这些内容。

### 5.1 非结构化数据提取：合同 / 简历 / 发票

把 PDF/图片中的关键信息自动提取为结构化 JSON——这是企业场景中需求最大的 AI 工作流之一。

```
合同信息提取工作流：

  Webhook Trigger (接收上传的合同 PDF)
      │
      ▼
  Code (PDF → 文本转换)
      │ 使用 pdf-parse 或调用 OCR API
      ▼
  LLM Chain (关键信息提取)
      │ Prompt: "提取合同的关键信息，输出 JSON"
      ▼
  Code (校验 + 格式化)
      │
      ▼
  Google Sheets / 数据库 (写入结构化数据)
```

**合同提取的 Prompt：**

::: v-pre
```
请从以下合同文本中提取关键信息，输出 JSON：

{
  "contract_type": "服务合同|采购合同|租赁合同|劳动合同|其他",
  "parties": {
    "party_a": "甲方名称",
    "party_b": "乙方名称"
  },
  "amount": "合同金额（含币种）",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "key_terms": ["关键条款1", "关键条款2"],
  "payment_terms": "付款方式说明",
  "penalty_clause": "违约条款摘要"
}

注意：只提取文本中明确出现的信息，无法确定的字段填 null。

合同全文：
&#123;&#123; $json.text &#125;&#125;
```
:::

**三种文档类型的提取示例：**

| 文档类型 | 提取字段 | 准确率 | 适合度 |
|:---|:---|:---|:---|
| **合同** | 甲乙方、金额、期限、条款 | ~90% | ⭐⭐⭐ |
| **简历** | 姓名、教育、工作经历、技能 | ~95% | ⭐⭐⭐ |
| **发票** | 抬头、金额、税号、日期 | ~85% | ⭐⭐（OCR质量影响大） |

> 💡 **LLM 提取不是 100% 准确的**——金额、日期这类关键字段建议加一个人工复核步骤。工作流可以自动高亮"置信度低"的字段，只让人工检查这些。

### 5.2 竞品监控：定时抓取→变化检测→智能分析

竞品动态监控是市场团队和产品经理的刚需——但没人愿意每天手动去看 5 个竞品官网有没有更新。

```
竞品监控工作流：

  Schedule Trigger (每天 9:00)
      │
      ▼
  HTTP Request × N (抓取竞品页面)
      │ 抓取定价页、功能页、博客页
      ▼
  Code (提取页面核心文本 + 计算 Hash)
      │
      ▼
  IF (Hash 与上次不同？)
      │
      ├── 是 → LLM 分析变化
      │        │
      │        ▼
      │   LLM Chain
      │   "对比新旧版本，分析竞品做了什么变化，
      │    评估对我们的影响"
      │        │
      │        ▼
      │   飞书/Slack (推送变化分析)
      │
      └── 否 → 无变化，跳过
```

**变化检测的 Code 节点：**

```javascript
const crypto = require('crypto');

const currentContent = $input.first().json.body;
const currentHash = crypto.createHash('md5')
  .update(currentContent).digest('hex');

// 从 n8n 的 Static Data 读取上次的 hash
const lastHash = $workflow.staticData.lastHash || '';

if (currentHash !== lastHash) {
  // 有变化，保存新 hash
  $workflow.staticData.lastHash = currentHash;
  $workflow.staticData.lastContent = currentContent;
  
  return [{
    json: {
      changed: true,
      old_content: $workflow.staticData.lastContent || '(首次抓取)',
      new_content: currentContent,
    }
  }];
}

return [{ json: { changed: false } }];
```

**LLM 分析变化的 Prompt：**

::: v-pre
```
你是一个竞品分析专家。以下是竞品网站的页面变化：

旧版本：
&#123;&#123; $json.old_content &#125;&#125;

新版本：
&#123;&#123; $json.new_content &#125;&#125;

请分析：
1. 具体变化了什么（新功能/价格调整/界面改版）
2. 这个变化意味着什么（竞品的策略方向）
3. 对我们的影响和建议应对措施

输出格式简洁，控制在 200 字以内。
```
:::

> 💡 **`$workflow.staticData` 是 n8n 的持久化存储**——它在工作流的多次执行之间保持数据。非常适合存"上次抓取的内容 hash"这类跨执行状态，不需要外部数据库。
### 5.3 用户反馈分析：多渠道汇聚→分类→周报

用户反馈散落在 App Store 评论、微博、客服工单、问卷等多个渠道。手动看完所有反馈不现实，但 LLM 可以。

```
用户反馈分析工作流：

  ① 多渠道收集（并行触发）
  ═══════════════════════════════════════
  Schedule Trigger (每周五)
      │
      ├── HTTP Request → App Store 评论 API
      ├── HTTP Request → 微博关键词搜索
      ├── Google Sheets → 客服工单导出
      └── HTTP Request → 问卷星数据
      │
      ▼ Merge (合并所有渠道数据)

  ② LLM 批量分析
  ═══════════════════════════════════════
  Split In Batches → LLM Chain
  Prompt: "分析每条反馈的情感和分类"
  → {sentiment, category, summary}

  ③ 统计 + 生成报告
  ═══════════════════════════════════════
  Code (统计各分类数量、情感分布)
      │
      ▼
  LLM Chain (生成周报文字)
      │
      ▼
  飞书文档 / Notion (写入周报)
```

**反馈分析的 Prompt：**

::: v-pre
```
分析以下用户反馈，为每条输出 JSON：
[
  {
    "index": 1,
    "sentiment": "positive|negative|neutral",
    "category": "bug|feature_request|ux|performance|praise|other",
    "summary": "一句话摘要",
    "urgency": "high|medium|low"
  }
]

反馈列表：
&#123;&#123; $json.batch_text &#125;&#125;
```
:::

**周报生成的统计 Code：**

```javascript
const results = $input.all().flatMap(item => {
  try { return JSON.parse(item.json.text); }
  catch { return []; }
});

// 统计
const stats = {
  total: results.length,
  sentiment: { positive: 0, negative: 0, neutral: 0 },
  categories: {},
  urgent_issues: [],
};

results.forEach(r => {
  stats.sentiment[r.sentiment]++;
  stats.categories[r.category] = (stats.categories[r.category] || 0) + 1;
  if (r.urgency === 'high') stats.urgent_issues.push(r.summary);
});

return [{ json: stats }];
```

> 💡 **反馈分析工作流的价值是"发现趋势"**——单条反馈产品经理自己能看，但"本周 Bug 类反馈比上周增加 40%"、"最近用户集中反馈的是性能问题"这种趋势，需要汇总分析才能发现。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **数据提取** | PDF/图片→LLM 提取→结构化 JSON，合同/简历/发票通用 |
| **竞品监控** | 定时抓取→Hash 变化检测→LLM 差异分析→告警 |
| **staticData** | n8n 跨执行持久化存储，不需要外部数据库 |
| **反馈分析** | 多渠道汇聚→LLM 批量情感分类→统计→周报 |
| **核心价值** | "发现趋势"而非逐条阅读 |

---

## 6. 实战场景三：监控告警与运维

运维告警是"最怕漏、最烦多"的场景。漏掉一条关键告警可能导致线上故障，但每天收到 200 条告警又让你直接免疫。LLM 能帮你做到：**只有值得关注的告警才打扰你**。

### 6.1 日志异常检测：ELK → LLM 分析 → 智能告警

传统日志告警靠关键词匹配（`ERROR`、`Exception`），误报率高。LLM 可以**理解日志上下文**来判断是否真的有问题。

```
日志异常检测工作流：

  Webhook Trigger (接收 Elasticsearch 告警)
      │ ES Watcher 检测到 ERROR 日志激增
      ▼
  HTTP Request (查询最近 10 条 ERROR 日志详情)
      │
      ▼
  LLM Chain (分析异常)
      │ Prompt: "分析这些错误日志，判断严重程度"
      ▼
  IF (severity === "critical")
      │
      ├── critical → 钉钉/飞书 立即通知（@相关人）
      │
      ├── warning → 汇总到日报（不立即打扰）
      │
      └── noise → 忽略（记录到日志，不通知）
```

**日志分析的 Prompt：**

::: v-pre
```
你是一个资深 SRE 工程师。请分析以下服务器错误日志：

&#123;&#123; $json.error_logs &#125;&#125;

请输出 JSON：
{
  "severity": "critical|warning|noise",
  "root_cause": "可能的根因分析",
  "affected_service": "受影响的服务名",
  "is_recurring": true/false,
  "suggested_action": "建议的处理步骤",
  "summary": "一句话描述"
}

判断标准：
- critical：影响用户访问、数据丢失、安全漏洞
- warning：性能下降、非关键服务异常
- noise：已知问题、定时任务报错、调试日志
```
:::

| 传统告警 | AI 告警 |
|:---|:---|
| `grep "ERROR"` → 200 条/天 | LLM 分析 → 5 条 critical/天 |
| 运维疲劳，开始无视告警 | 每条都值得看 |
| 不知道根因 | 自动分析根因 + 建议修复 |
| 不分优先级 | 自动分 critical/warning/noise |

> 💡 **LLM 告警分析的关键是给足上下文**——不要只发一行错误信息，把前后 10 行日志、相关的服务名、最近的部署记录一起发给 LLM。上下文越丰富，分析越准确。

### 6.2 API 健康检查与故障报告自动生成

定时探测关键 API 端点，一旦异常立即生成故障分析报告并通知团队。

```
API 健康检查工作流：

  Schedule Trigger (每 5 分钟)
      │
      ▼
  HTTP Request × N (并行探测多个 API)
      │ GET /api/health → 记录状态码 + 响应时间
      │ GET /api/users  → 记录状态码 + 响应时间
      │ GET /api/orders → ...
      ▼
  Code (判断异常)
      │ 状态码 !== 200 或 响应时间 > 3s
      ▼
  IF (有异常端点？)
      │
      ├── 是 → LLM 生成故障报告
      │        │
      │        ▼
      │   LLM Chain
      │   "根据以下 API 探测结果生成故障分析报告"
      │        │
      │        ▼
      │   飞书/钉钉 (发送报告)
      │
      └── 否 → 正常，不做任何事
```

**探测和判断的 Code 节点：**

```javascript
const endpoints = $input.all();
const issues = [];

for (const ep of endpoints) {
  const { url, statusCode, responseTime } = ep.json;
  
  if (statusCode !== 200) {
    issues.push({
      url,
      issue: `返回状态码 ${statusCode}`,
      severity: statusCode >= 500 ? 'critical' : 'warning',
    });
  } else if (responseTime > 3000) {
    issues.push({
      url,
      issue: `响应时间 ${responseTime}ms（超过 3s 阈值）`,
      severity: 'warning',
    });
  }
}

return [{
  json: {
    has_issues: issues.length > 0,
    issues,
    check_time: new Date().toISOString(),
  }
}];
```

> 💡 **健康检查不要只查 `/health`**——很多服务的 health 端点永远返回 200，但实际业务 API 已经挂了。探测几个核心业务接口更可靠。
### 6.3 告警降噪：LLM 判断"这条告警值不值得打扰你"

告警降噪的核心思路：**不是过滤掉告警，而是给告警分级**。所有告警都记录，但只有 critical 级别才立即通知你。

```
告警降噪的分级策略：

  告警来源（Prometheus / Sentry / 云监控）
      │
      ▼
  Webhook Trigger (接收原始告警)
      │
      ▼
  Code (预处理：去重 + 格式统一)
      │ 同一告警 5 分钟内只保留第一条
      ▼
  LLM Chain (智能分级)
      │
      ▼
  Switch (按 severity 路由)
      │
      ├── 🔴 critical → 立即推送（电话/短信/钉钉@）
      │   "数据库连接池耗尽""支付接口 5xx"
      │
      ├── 🟡 warning → 汇总到日报（每天 9:00 推送）
      │   "慢查询增加""内存使用 85%"
      │
      └── ⚪ noise → 静默记录
          "定时任务超时""开发环境报错"
```

**LLM 降噪的 Prompt：**

::: v-pre
```
你是一个运维告警分析专家。请判断以下告警的真实严重程度。

告警信息：
- 来源：&#123;&#123; $json.source &#125;&#125;
- 内容：&#123;&#123; $json.message &#125;&#125;
- 触发时间：&#123;&#123; $json.timestamp &#125;&#125;
- 最近 1 小时同类告警数：&#123;&#123; $json.count &#125;&#125;

判断标准：
- critical：直接影响线上用户，需要立刻处理
- warning：有潜在风险但不紧急，可以白天处理
- noise：已知问题/误报/开发环境，不需要通知

历史规律：这个告警在过去 7 天触发了 &#123;&#123; $json.weekly_count &#125;&#125; 次。

输出 JSON：
{
  "severity": "critical|warning|noise",
  "reason": "判断理由（一句话）"
}
```
:::

**去重的 Code 节点：**

```javascript
const alertKey = `${$input.first().json.source}_${$input.first().json.alert_name}`;
const now = Date.now();
const lastSeen = $workflow.staticData[alertKey] || 0;

// 5 分钟内的重复告警只保留第一条
if (now - lastSeen < 5 * 60 * 1000) {
  return [];  // 返回空数组 = 跳过后续节点
}

$workflow.staticData[alertKey] = now;
return $input.all();
```

> 💡 **告警降噪的 ROI 极高**——如果你的团队每天收到 200 条告警，降噪到 10 条有效告警，相当于每天节省所有运维人员 30 分钟的注意力。而且关键告警不会被淹没了。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **日志分析** | LLM 理解日志上下文，自动分级 + 根因分析 |
| **API 健康检查** | 定时探测核心接口，异常时自动生成故障报告 |
| **告警降噪** | 去重→LLM 分级→只推送 critical，降噪 95% |
| **分级路由** | 🔴立即通知 / 🟡日报汇总 / ⚪静默记录 |
| **去重策略** | staticData 记录上次时间，5 分钟内去重 |

---

## 7. 工作流工程化：错误处理、调试与版本管理

工作流从"能跑"到"稳定跑"，差的就是工程化。一个没有错误处理的工作流，某天凌晨 3 点 API 超时了，你的日报、告警、数据同步全部静默失败——你第二天才发现。

### 7.1 错误处理：重试、降级与告警通知

n8n 提供了三层错误处理机制：

```
n8n 的错误处理三层机制：

  第 1 层：节点级重试（Node Settings）
  ═══════════════════════════════════════
  • 每个节点可配置 Retry On Fail
  • 最大重试次数 + 重试间隔
  • 适合：网络超时、API 限流等临时故障
  
  设置方式：
  节点 → Settings → Retry On Fail → Max Tries: 3
                                   → Wait: 1000ms

  第 2 层：Error Trigger（工作流级兜底）
  ═══════════════════════════════════════
  • 创建一个专门的 Error Workflow
  • 任何工作流出错都会触发它
  • 适合：统一错误通知和记录
  
  Error Workflow 内容：
  Error Trigger → Code (格式化错误信息)
               → 飞书/钉钉 (通知运维)

  第 3 层：Try-Catch 模式（Code 节点内）
  ═══════════════════════════════════════
  • 在 Code 节点内 try-catch
  • 返回默认值或降级结果
  • 适合：LLM 输出解析失败等可预见错误
```

**Error Workflow 的标准实现：**

::: v-pre
```
Error Trigger
    │ 自动接收：错误信息、失败节点名、工作流名
    ▼
Code (格式化)
    │ "🔴 工作流失败告警
    │  工作流：&#123;&#123; $json.workflow.name &#125;&#125;
    │  节点：&#123;&#123; $json.execution.lastNodeExecuted &#125;&#125;
    │  错误：&#123;&#123; $json.execution.error.message &#125;&#125;
    │  时间：&#123;&#123; $json.execution.startedAt &#125;&#125;"
    ▼
飞书 / Telegram (发送告警)
```
:::

| 错误类型 | 处理策略 | 配置位置 |
|:---|:---|:---|
| 网络超时 | 重试 3 次，间隔 1s | 节点 Settings |
| API 限流 (429) | 重试 3 次，间隔递增 | 节点 Settings |
| LLM 输出格式错误 | Code 节点 try-catch + 默认值 | Code 节点 |
| 凭证过期 | Error Workflow 通知 | 全局 Error Workflow |

> 💡 **每个生产工作流都必须配置 Error Workflow**——这是底线。否则工作流静默失败了你根本不知道。5 分钟就能配好，但能救你无数次。

### 7.2 调试技巧：执行历史与节点级测试

n8n 的调试体验是它的核心优势之一——每个节点的输入输出都**可视化可追溯**。

```
n8n 调试的四个利器：

  ① Test Workflow（手动触发执行）
  ═══════════════════════════════════════
  • 点 "Test Workflow" 按钮 → 整个工作流执行一次
  • 每个节点右边会显示输出数据
  • 最快的调试方式

  ② 节点级测试（Test Step）
  ═══════════════════════════════════════
  • 点单个节点的 "Test step"
  • 只执行这一个节点（使用上游节点的缓存数据）
  • 适合调试 Code 节点和 LLM Prompt

  ③ 执行历史（Executions）
  ═══════════════════════════════════════
  • 记录每次自动执行的完整数据
  • 可以查看每个节点的输入/输出
  • 失败的执行会标红，点进去看哪个节点挂了

  ④ Pin Data（固定测试数据）
  ═══════════════════════════════════════
  • 给节点"钉住"一组测试数据
  • 后续调试时跳过该节点，直接用固定数据
  • 适合：跳过 API 调用节点（省时间和钱）
```

**LLM 节点的调试技巧：**

```
调试 LLM Prompt 的最佳流程：

  1. 先 Pin Data 固定上游输入
     → 不用每次重新调 RSS / API
  
  2. 修改 Prompt → Test Step
     → 只执行 LLM 节点，看输出是否符合预期
  
  3. 在 LLM 节点后加 Code 节点做 JSON.parse
     → 验证 LLM 输出是否可解析
  
  4. 满意后取消 Pin Data，Test Workflow
     → 端到端验证
```

> 💡 **Pin Data 是调试 AI 工作流的关键技巧**——LLM 调用有成本，每次测试都从头跑会浪费钱。用 Pin Data 固定 LLM 上游的数据，只反复调试 Prompt 本身。
### 7.3 版本管理：JSON 导出 + Git 协作

n8n 的工作流本质是一个 JSON 文件。导出 JSON → 提交 Git → 团队协作 + 版本回滚。

```bash
# n8n CLI 导出所有工作流
n8n export:workflow --all --output=./workflows/

# 目录结构
workflows/
├── rss-daily-report.json        # RSS 日报工作流
├── email-classification.json    # 邮件分类工作流
├── alert-noise-reduction.json   # 告警降噪工作流
└── error-handler.json           # 统一错误处理工作流
```

```bash
# Git 版本管理
cd workflows/
git init
git add .
git commit -m "feat: 新增 RSS 日报工作流 v1.0"

# 工作流有改动后
n8n export:workflow --all --output=./workflows/
git diff  # 查看变化
git commit -am "fix: 优化 RSS 日报的 Prompt，提升筛选准确率"
```

```
工作流版本管理的最佳实践：

  ✅ 推荐做法
  ═══════════════════════════════════════
  • 每个工作流一个 JSON 文件
  • 用 Git 管理，commit message 说明修改原因
  • 重大变更前先导出备份
  • Credential 信息不在 JSON 中（自动排除）

  ❌ 常见坑
  ═══════════════════════════════════════
  • 不要导出 Credential（会暴露密钥）
  • 不要手动改 JSON（容易改坏节点连接）
  • 不要在 UI 上直接改生产工作流（先在开发环境测试）
```

> 💡 **n8n 的 JSON 导出不包含 Credential 的值**——只包含 Credential 的引用 ID。所以可以安全地提交到 Git。在新环境导入后，需要手动重新配置 Credential。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **三层错误处理** | 节点重试 → Error Workflow → Code try-catch |
| **Error Workflow** | 统一错误通知，每个生产工作流必配 |
| **Pin Data** | 固定测试数据，省钱省时间调试 LLM Prompt |
| **执行历史** | 每次执行可追溯，失败标红，节点级排查 |
| **Git 管理** | JSON 导出 + Git 版本控制，Credential 自动排除 |

---

## 8. 高级编排：条件分支、循环与子工作流

前面的实战案例已经用到了 IF、Split In Batches 等编排节点。本章系统讲解 n8n 的高级编排能力——让你的工作流能处理更复杂的业务逻辑。

### 8.1 条件分支与动态路由

n8n 提供两种条件分支节点：**IF**（二选一）和 **Switch**（多选一）。

::: v-pre
```
IF 节点（二分支）：

  LLM 分析结果
      │
      ▼
  IF: &#123;&#123; $json.urgency &#125;&#125; === "high"
      │
      ├── true  → 立即通知
      └── false → 汇总到日报
```
:::

::: v-pre
```
Switch 节点（多分支）：

  LLM 分类结果
      │
      ▼
  Switch: &#123;&#123; $json.category &#125;&#125;
      │
      ├── "bug"             → 创建 Jira Issue
      ├── "feature_request" → 加入需求池（Notion）
      ├── "praise"          → 转发到团队群
      └── default           → 归档
```
:::

**动态路由的 Code 实现（更灵活）：**

```javascript
// 当分支逻辑比 Switch 更复杂时，用 Code 节点
const item = $input.first().json;

// 多条件组合判断
if (item.urgency === 'high' && item.category === 'bug') {
  return [{ json: { ...item, route: 'critical_bug' } }];
}
if (item.sentiment === 'negative' && item.urgency !== 'low') {
  return [{ json: { ...item, route: 'angry_customer' } }];
}
return [{ json: { ...item, route: 'normal' } }];

// 下游 IF 节点按 route 字段分流
```

> 💡 **简单条件用 IF/Switch，复杂条件用 Code**——当你发现 IF 的条件表达式变得很长或嵌套时，换成 Code 节点写 JavaScript，可读性好得多。

### 8.2 批量处理：循环 + LLM 的性能优化

处理 100 条数据时，逐条调 LLM 太慢。n8n 的 Split In Batches 节点 + 批量合并是关键。

```
批量处理的两种模式：

  模式 A：Split In Batches（n8n 内置循环）
  ═══════════════════════════════════════
  100 条数据 → Split In Batches (size=1)
             → 循环 100 次，每次处理 1 条
             → 每条调一次 LLM
  总耗时：100 × 2s = 200s ❌ 太慢

  模式 B：Code 合并 + Split（推荐）
  ═══════════════════════════════════════
  100 条数据 → Code (每 10 条合并为 1 组)
             → Split In Batches (size=1)
             → 循环 10 次，每次处理 10 条
             → 每组调一次 LLM
  总耗时：10 × 3s = 30s ✅ 快 6 倍
```

**n8n 并发控制配置：**

```
Split In Batches 节点的关键参数：

  • Batch Size: 1（每次处理 1 个批次）
  • Options → Reset: false（保留之前的输出）

  注意：n8n 的 Split In Batches 是串行的！
  如果需要并行，用 n8n 的 "Execute Workflow" 节点
  调用子工作流，子工作流会并行执行。
```

| 策略 | 耗时 | LLM 调用次数 | 适用场景 |
|:---|:---|:---|:---|
| 逐条处理 | 200s | 100 次 | 需要独立处理每条 |
| 10 条合并 | 30s | 10 次 | 分类、摘要、评分 |
| 全部合并 | 5s | 1 次 | 数据量小（< 20 条） |

> 💡 **合并批次大小取决于单条数据长度**——如果每条数据 200 字，合并 10 条就是 2000 字，LLM 处理没问题。如果每条数据 2000 字，合并 3-5 条就好，避免超出上下文窗口。
### 8.3 子工作流与人工审核节点

**子工作流（Execute Workflow）** 实现模块化复用——把"LLM 分析 + JSON 解析"封装成独立工作流，多个主工作流共享调用。

```
子工作流的使用场景：

  主工作流 A（RSS 日报）
      │
      └──▶ 子工作流："LLM 文本摘要"
              输入：text
              输出：summary JSON

  主工作流 B（邮件分类）
      │
      └──▶ 子工作流："LLM 文本摘要"（复用同一个）

  主工作流 C（反馈分析）
      │
      └──▶ 子工作流："LLM 文本摘要"（复用同一个）
```

**人工审核节点（Wait + Webhook）：**

```
需要人工确认的工作流：

  LLM 生成了内容
      │
      ▼
  Telegram (推送内容 + 确认链接)
      │ 消息："生成了以下内容，点击确认发布"
      │ 按钮：[✅ 确认] [❌ 拒绝] [✏️ 修改]
      ▼
  Wait (等待 Webhook 回调)
      │ 超时时间：24 小时
      │ 超时行为：跳过/通知
      ▼
  IF (用户选择了什么)
      │
      ├── 确认 → 继续执行发布流程
      ├── 拒绝 → 归档 + 通知"已取消"
      └── 修改 → 回到 LLM 重新生成
```

> 💡 **人工审核是 AI 工作流的安全阀**——任何对外发布内容、发送邮件、创建工单的操作，都建议加一个人工确认步骤。AI 生成的内容可能有错误或不当，人工审核 10 秒钟就能避免事故。

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **IF/Switch** | 条件分支，简单逻辑用节点，复杂逻辑用 Code |
| **批量合并** | N 条数据合并为 1 个 Prompt，减少 LLM 调用次数 |
| **子工作流** | Execute Workflow 实现模块化复用 |
| **Wait 节点** | 暂停工作流等待外部信号（Webhook 回调） |
| **人工审核** | 对外操作前必须人工确认，10 秒避免事故 |

---

## 9. 生产部署与成本优化

工作流从"本地单机"到"生产级服务"，需要解决三个问题：**稳定性**（数据库 + 队列）、**成本**（LLM 调用优化）、**安全**（Credential + Webhook 保护）。

### 9.1 生产环境部署：PostgreSQL + Redis + Nginx

第 2 章的 Docker Compose 已经包含了 PostgreSQL。生产环境还需要加 Redis（队列管理）和 Nginx（反向代理 + HTTPS）。

```yaml
# 生产级 docker-compose.yml（在第 2 章基础上增强）
services:
  n8n:
    image: n8nio/n8n:latest
    environment:
      # 队列模式（多实例部署时必须）
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      # 保留执行历史（调试用）
      - EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
      - EXECUTIONS_DATA_SAVE_ON_ERROR=all
      # Webhook 外部 URL
      - WEBHOOK_URL=https://n8n.your-domain.com/
    depends_on:
      - postgres
      - redis

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

```
生产部署检查清单：

  ✅ 数据库：PostgreSQL（不要用 SQLite）
  ✅ 队列：Redis（队列模式处理并发执行）
  ✅ 反向代理：Nginx + HTTPS（Webhook 安全）
  ✅ 加密密钥：N8N_ENCRYPTION_KEY 已设置
  ✅ 数据备份：PostgreSQL 定时备份
  ✅ 日志：执行历史保留 30 天
  ✅ 监控：n8n 进程健康检查
```

### 9.2 LLM 成本控制：缓存、模型路由与本地降级

```
三种 LLM 成本优化策略：

  ① 结果缓存
  ═══════════════════════════════════════
  同样的输入 → 直接返回缓存结果
  适合：相似的 RSS 文章、重复的反馈文本
  实现：Code 节点用 staticData 做简单缓存

  ② 模型路由
  ═══════════════════════════════════════
  简单任务 → DeepSeek V3（$1/1M tokens）
  复杂任务 → GPT-4o（$15/1M tokens）
  Code 节点判断任务复杂度 → 选择不同 LLM 节点

  ③ 本地降级
  ═══════════════════════════════════════
  云端 API 不可用时 → 自动切换到 Ollama 本地模型
  实现：HTTP Request 调用 → 错误时走降级分支
```

### 9.3 安全加固与工作流监控

```
安全加固三要素：

  ① Webhook 鉴权
  ═══════════════════════════════════════
  • 使用 Header Auth（自定义密钥）
  • 或使用 n8n 的 Webhook Authentication
  • 永远不要用无认证的 Webhook（会被扫描利用）

  ② Credential 保护
  ═══════════════════════════════════════
  • N8N_ENCRYPTION_KEY 必须设置
  • 定期轮换 API Key
  • 工作流 JSON 导出不含 Credential 值

  ③ 访问控制
  ═══════════════════════════════════════
  • 设置强密码
  • 限制 n8n 管理界面的访问 IP
  • 生产环境必须 HTTPS
```

> 💡 **n8n 的 Webhook URL 是公开可访问的**——任何人知道你的 Webhook URL 就能触发你的工作流。务必在 Webhook 节点配置 Authentication，或在 Nginx 层做 IP 白名单。

**第 9 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **队列模式** | Redis + EXECUTIONS_MODE=queue 处理并发 |
| **LLM 缓存** | 相同输入直接返回缓存，用 staticData 实现 |
| **模型路由** | 简单任务用便宜模型，复杂任务用强模型 |
| **Webhook 鉴权** | 永远不用无认证 Webhook，防止被恶意触发 |
| **备份** | PostgreSQL 定时备份 + 工作流 JSON 版本管理 |

---

## 10. 从工作流到 AI 原生应用

n8n 能解决 80% 的自动化需求，但总有它兜不住的场景。本章讲清楚：**什么时候该从工作流毕业，以及毕业后怎么走**。

### 10.1 工作流的边界：什么时候该写代码

```
工作流适合 vs 不适合：

  ✅ 继续用 n8n 工作流
  ═══════════════════════════════════════
  • 流程固定、步骤清晰
  • 定时/事件触发的批量任务
  • 不需要实时交互
  • 团队中非开发人员也要维护

  ❌ 该换成代码/Agent 了
  ═══════════════════════════════════════
  • 需要实时对话交互
  • 步骤不确定（取决于 LLM 推理结果）
  • 需要复杂的状态管理（跨多步骤的上下文）
  • 性能要求高（毫秒级响应）
  • 需要深度自定义 LLM 行为（Fine-tuning、RAG）
```

| 场景 | 推荐方案 | 原因 |
|:---|:---|:---|
| 每日数据报表 | n8n 工作流 | 固定流程、定时触发 |
| 智能客服对话 | LangGraph Agent | 需要实时交互、动态决策 |
| 邮件自动分类 | n8n 工作流 | 批量处理、固定规则 |
| 个人 AI 助理 | LangGraph Agent | 对话式、多工具调用 |
| 竞品监控报告 | n8n 工作流 | 定时触发、固定管线 |

### 10.2 n8n + LangGraph 混合架构

最强大的方案是两者结合——n8n 做触发和分发，LangGraph 做复杂推理。

```
混合架构：

  n8n 层（触发 + 编排 + 分发）
  ═══════════════════════════════════════
  Schedule Trigger → 数据收集 → 格式化
      │
      ▼ HTTP Request（调用你的 Agent API）

  LangGraph 层（推理 + 决策）
  ═══════════════════════════════════════
  FastAPI + LangGraph Agent
      │ 接收 n8n 发来的数据
      │ 复杂推理 + 工具调用
      │ 返回结构化结果
      ▼

  n8n 层（后处理 + 分发）
  ═══════════════════════════════════════
  接收 Agent 结果 → 分类路由 → 推送通知
```

> 💡 **n8n 擅长"粘合"和"调度"，LangGraph 擅长"推理"和"决策"**——让每个工具做它最擅长的事。用 n8n 做定时触发和结果分发，用 LangGraph 处理需要多轮推理的复杂任务。

### 10.3 未来趋势：自然语言定义工作流

```
AI 工作流的未来演进：

  2024-2025：可视化编排 ← 我们现在在这里
  ═══════════════════════════════════════
  • 拖拽节点 + 连线
  • 手写 Prompt + Code 节点
  • n8n / Dify / Make

  2025-2026：自然语言编排
  ═══════════════════════════════════════
  • "帮我做一个每天推送 RSS 摘要的工作流"
  • AI 自动生成工作流 JSON
  • AI 自动调试和优化 Prompt

  2026-2027：自适应工作流
  ═══════════════════════════════════════
  • 工作流根据执行结果自动优化
  • LLM 学习用户偏好，自动调整筛选标准
  • 从"编排"到"意图"：你说目标，AI 搞定一切
```

| 技术方向 | 影响 | 当前状态 |
|:---|:---|:---|
| **MCP 协议** | 工具接入标准化 | 🟢 已可用 |
| **AI 生成工作流** | 自然语言→工作流 JSON | 🟡 早期探索 |
| **n8n AI 原生节点** | 内置 RAG、Agent、向量搜索 | 🟢 持续新增 |
| **Dify + n8n 互通** | Dify 做 AI 对话，n8n 做编排 | 🟡 社区集成 |

> 💡 **最好的自动化是你真正在用的那个**——不要追求完美方案。从一个 RSS 日报工作流开始，每天用起来，你会在使用中发现下一个值得自动化的场景。行动比规划重要 100 倍。

**第 10 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **工作流边界** | 固定流程用 n8n，动态决策用 Agent |
| **混合架构** | n8n 触发+分发，LangGraph 推理+决策 |
| **MCP 协议** | 工具接入标准化，一次开发到处可用 |
| **自然语言编排** | "帮我做一个工作流" → AI 自动生成 |
| **行动优先** | 从一个简单工作流开始，用起来再优化 |
