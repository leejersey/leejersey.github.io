# Serverless 开发实战

> 从"有服务器"到"无服务器"的思维转变：函数即服务、事件驱动、按需付费——用最少的运维成本交付生产级应用。

---

## 1. Serverless 核心概念：理解范式转变

"Serverless" 不是没有服务器，而是**你不再需要关心服务器**。底层依然有物理/虚拟机在运行，只是它们完全由云厂商管理——你只负责写代码。

> 💡 **本章目标**：理解 Serverless 的核心理念，搞清 FaaS/BaaS 的边界，选对适合你的平台。

### 1.1 什么是 Serverless？FaaS vs BaaS vs 传统架构

**Serverless 的两大组成：**

```
Serverless = FaaS（Function as a Service）+ BaaS（Backend as a Service）

FaaS：你写的函数，由平台替你运行
  → AWS Lambda、Vercel Functions、Cloudflare Workers

BaaS：现成的后端服务，直接调 API
  → Supabase（数据库+认证）、Firebase（数据库+推送）
  → Stripe（支付）、Auth0（认证）、Algolia（搜索）
```

**三种架构的演进：**

```
传统服务器（VPS / 云主机）：
  ┌─────────────────────────────────────┐
  │  操作系统 │ 运行时 │ 应用 │ 扩容  │  ← 全部你管
  └─────────────────────────────────────┘

容器化（Docker + K8s）：
  ┌─────────────────────────────────────┐
  │  操作系统 │ 运行时 │ 应用 │ 扩容  │
  │  平台管 ──┤ 你管 ─────────┤ 半自动 │
  └─────────────────────────────────────┘

Serverless（FaaS）：
  ┌─────────────────────────────────────┐
  │  操作系统 │ 运行时 │ 应用 │ 扩容  │
  │  ──────── 全部平台管 ──────│ 你管 ─│  ← 你只写函数
  └─────────────────────────────────────┘
```

| 维度 | 传统服务器 | 容器化 | Serverless |
|:---|:---|:---|:---|
| 你管什么 | 一切 | 容器 + 编排 | 只管代码 |
| 扩容 | 手动 / 脚本 | 配置 HPA | 全自动（0 到 N） |
| 运维负担 | 重 | 中 | 几乎为零 |
| 冷启动 | 无 | 容器拉取 ~秒级 | 函数初始化 ~毫秒到秒 |
| 空闲成本 | 7×24 付费 | 最少 1 个 Pod | **零请求零费用** |
| 执行时长限制 | 无 | 无 | 有（通常 ≤ 15 分钟） |

### 1.2 Serverless 的优势与局限

**✅ 优势：**

| 优势 | 解释 |
|:---|:---|
| 零运维 | 不管操作系统、补丁、扩容——全交给平台 |
| 自动扩缩容 | 从 0 到成千上万并发，完全自动 |
| 按需付费 | 没有请求 = 不花钱。个人项目可能完全免费 |
| 快速交付 | 写完函数直接部署，不需要配置 Nginx、Docker |
| 全球分发 | Edge Functions 部署到全球 300+ 节点 |
| 天然高可用 | 平台保证 SLA（通常 99.95%+） |

**❌ 局限：**

| 局限 | 影响 |
|:---|:---|
| 冷启动延迟 | 空闲一段时间后，首次请求慢 100ms-几秒 |
| 执行时间限制 | Lambda 最多 15 分钟，Vercel 最多 300 秒 |
| 无状态 | 函数之间不共享内存，需要外部存储 |
| 调试困难 | 远程执行环境，本地难以完美复现 |
| 厂商锁定 | 深度依赖某个云厂商的 API 后，迁移成本高 |

**判断标准——什么项目适合 Serverless：**

```
✅ 适合：
  • API 后端（REST / GraphQL）
  • Webhook 处理（支付回调、CI/CD 触发）
  • 定时任务（数据同步、报表生成）
  • 轻量级微服务
  • 个人项目 / MVP / 副业产品

❌ 不适合：
  • 长时间运行的任务（视频转码、大规模数据处理）
  • WebSocket 长连接服务
  • 需要本地文件系统的应用
  • 对延迟极敏感的场景（高频交易）
```

### 1.3 主流平台对比：AWS Lambda / Vercel Functions / Cloudflare Workers / 腾讯云 SCF

| 维度 | AWS Lambda | Vercel Functions | Cloudflare Workers | 腾讯云 SCF |
|:---|:---|:---|:---|:---|
| **运行环境** | 容器（microVM） | AWS Lambda（底层） | V8 Isolate（轻量）| 容器 |
| **支持语言** | Node/Python/Go/Java/Rust/… | Node/Python/Go/Ruby | JS/TS/Rust/WASM | Node/Python/Go/Java/PHP |
| **冷启动** | 100ms-数秒 | 100ms-数秒 | **≈0ms（V8 隔离）** | 100ms-数秒 |
| **最长执行** | 15 分钟 | 300 秒（Hobby: 60s） | 30 秒（免费）/ 15 分钟 | 15 分钟 |
| **免费额度** | 100 万次/月 + 40 万 GB·s | 10 万次/月 | 10 万次/天 | 100 万次/月 |
| **配套生态** | 最丰富（SQS/S3/DynamoDB/…） | 与 Next.js 深度集成 | KV/D1/R2/Durable Objects | 与腾讯云生态集成 |
| **部署体验** | SAM/CDK/Serverless Framework | `git push` 自动部署 | `wrangler deploy` | 控制台/CLI |
| **适合谁** | 企业级/复杂架构 | 前端/全栈开发者 | 追求极致性能 | 国内业务 |

**选型建议：**

```
"我是全栈开发者，用 Next.js"
  → Vercel Functions（零配置，git push 即部署）

"我需要企业级功能，复杂事件编排"
  → AWS Lambda（生态最完整，配套服务最多）

"我追求最低延迟，全球边缘执行"
  → Cloudflare Workers（V8 隔离，几乎零冷启动）

"我的用户主要在中国大陆"
  → 腾讯云 SCF / 阿里云函数计算（合规、网络快）
```

> 💡 **不要一开始就纠结平台选择**。Serverless 函数的核心逻辑是平台无关的——一个处理 HTTP 请求的 JS 函数，换个平台只需改入口文件的格式。

---

## 2. 快速上手：第一个 Serverless 函数

Talk is cheap, show me the code. 我们用三个平台各写一个 "Hello World" API，体验从零到部署的全过程。

### 2.1 Vercel Serverless Functions（最简单的入门）

**零配置——文件即函数：**

```bash
# 创建 Next.js 项目（或任何 Vercel 项目）
npx create-next-app@latest my-app
cd my-app
```

```ts
// app/api/hello/route.ts（Next.js App Router）
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const name = searchParams.get('name') || 'World';

  return NextResponse.json({
    message: `Hello, ${name}!`,
    timestamp: new Date().toISOString(),
  });
}
// GET /api/hello?name=Alice → { "message": "Hello, Alice!" }
```

```bash
# 部署：推送到 GitHub，Vercel 自动部署
git push origin main
# 几秒后就能访问 https://your-app.vercel.app/api/hello
```

**Vercel 的好处**：`git push` = 部署。不需要配置 API Gateway、IAM 角色、部署包——零配置。

### 2.2 AWS Lambda + API Gateway（标准方案）

**手动方式——AWS Console：**

```js
// index.mjs（AWS Lambda 函数）
export const handler = async (event) => {
  const name = event.queryStringParameters?.name || 'World';

  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: `Hello, ${name}!`,
      timestamp: new Date().toISOString(),
      region: process.env.AWS_REGION,
    }),
  };
};
```

**用 Serverless Framework 部署（推荐）：**

```bash
npm install -g serverless
```

```yaml
# serverless.yml
service: hello-api
frameworkVersion: '3'

provider:
  name: aws
  runtime: nodejs20.x
  region: ap-northeast-1    # 东京区域

functions:
  hello:
    handler: index.handler
    events:
      - httpApi:
          path: /hello
          method: get
```

```bash
# 一键部署到 AWS
serverless deploy

# 输出：
# endpoints:
#   GET - https://xxxxxx.execute-api.ap-northeast-1.amazonaws.com/hello
```

**Lambda 的请求/响应格式：**

```
输入（event 对象）：
  event.queryStringParameters  → URL 查询参数
  event.body                  → POST 请求体
  event.headers               → 请求头
  event.pathParameters         → 路径参数

输出（返回对象）：
  { statusCode, headers, body }  → 必须是这个格式
```

### 2.3 Cloudflare Workers（边缘计算方案）

```bash
# 安装 Wrangler CLI
npm install -g wrangler

# 创建项目
wrangler init my-worker
cd my-worker
```

```ts
// src/index.ts（Cloudflare Workers 使用 Web 标准 API）
export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const name = url.searchParams.get('name') || 'World';

    return Response.json({
      message: `Hello, ${name}!`,
      timestamp: new Date().toISOString(),
      colo: request.cf?.colo,  // 执行该函数的边缘节点（如 HKG、NRT）
    });
  },
};
```

```bash
# 本地开发
wrangler dev

# 部署到全球边缘节点
wrangler deploy
# 部署后几秒就在全球 300+ 节点生效
```

**Workers 的独特之处**：使用 Web 标准 API（`Request`/`Response`/`fetch`），不是 Node.js 运行时。代码在 V8 引擎中直接运行，**几乎没有冷启动**。

> 💡 **三个平台的函数签名对比**：Vercel 用 Next.js API Route（`NextResponse`）、Lambda 用 `handler(event)` + `{ statusCode, body }`、Workers 用标准 `fetch(Request) → Response`。核心逻辑可复用，只是入口格式不同。

### 2.4 本地开发与调试工具

Serverless 函数运行在云端，但本地调试是必须的——总不能每改一行代码都部署一次。

| 平台 | 本地开发工具 | 命令 |
|:---|:---|:---|
| Vercel | `vercel dev` / `next dev` | 完整模拟 Serverless 环境 |
| AWS Lambda | `sam local invoke` / `serverless offline` | 用 Docker 模拟 Lambda |
| Cloudflare Workers | `wrangler dev` | 本地 V8 运行时模拟 |

**AWS Lambda 本地调试（SAM CLI）：**

```bash
# 安装 SAM CLI
brew install aws-sam-cli

# 本地启动 API（需要 Docker）
sam local start-api

# 单次调用测试
sam local invoke HelloFunction --event events/test.json
```

**通用调试技巧：**

```
1. 用 console.log() + 日志查看（最简单）
2. 用 HTTP 工具测试（curl / httpie / Postman）
3. 写单元测试——函数就是普通函数，可以直接 import 调用
4. 用环境变量区分 dev/prod：process.env.NODE_ENV
```

> 💡 **最佳实践**：把业务逻辑抽成纯函数（不依赖平台 API），在本地用 Jest/Vitest 测试。入口文件只做请求解析和响应格式化——这层薄壳才依赖平台。

---

## 3. 事件驱动架构：触发器与集成

Serverless 不是"你调用函数"，而是**"事件触发函数"**。HTTP 请求、定时器、文件上传、消息队列——任何事件都可以触发一个函数。

```
事件源                    触发器                函数
──────────               ──────               ──────
HTTP 请求        ──→    API Gateway    ──→    处理 API 请求
每天凌晨 2 点    ──→    CloudWatch     ──→    生成日报
用户上传图片     ──→    S3 Event       ──→    生成缩略图
订单创建         ──→    SQS 消息       ──→    发送确认邮件
数据库变更       ──→    DynamoDB Stream ──→   同步到搜索引擎
```

### 3.1 HTTP 触发（API Gateway / URL Route）

最常用的触发器——前面章节已经演示过了。补充几个关键知识：

**路径参数和请求方法路由（AWS Lambda）：**

```yaml
# serverless.yml
functions:
  getUser:
    handler: users.get
    events:
      - httpApi:
          path: /users/{id}
          method: get

  createUser:
    handler: users.create
    events:
      - httpApi:
          path: /users
          method: post
```

```js
// users.mjs
export const get = async (event) => {
  const userId = event.pathParameters.id;
  // 查询用户 ...
  return { statusCode: 200, body: JSON.stringify(user) };
};

export const create = async (event) => {
  const body = JSON.parse(event.body);
  // 创建用户 ...
  return { statusCode: 201, body: JSON.stringify(newUser) };
};
```

### 3.2 定时触发（Cron / 定时任务）

不需要用户请求也能触发函数——定时任务是 Serverless 非常实用的场景。

**AWS Lambda + CloudWatch Events：**

```yaml
# serverless.yml
functions:
  dailyReport:
    handler: cron.generateReport
    events:
      - schedule:
          rate: cron(0 2 * * ? *)    # 每天凌晨 2 点（UTC）
          enabled: true

  cleanupExpired:
    handler: cron.cleanup
    events:
      - schedule:
          rate: rate(1 hour)          # 每小时执行一次
```

**Vercel Cron Jobs：**

```json
// vercel.json
{
  "crons": [
    {
      "path": "/api/cron/daily-report",
      "schedule": "0 2 * * *"
    }
  ]
}
```

```ts
// app/api/cron/daily-report/route.ts
export async function GET(request: Request) {
  // 验证是 Vercel Cron 调用（防止外部触发）
  const authHeader = request.headers.get('authorization');
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return new Response('Unauthorized', { status: 401 });
  }

  // 生成报告逻辑 ...
  return Response.json({ success: true });
}
```

> 💡 **Cron 表达式速查**：`分 时 日 月 周`。`0 2 * * *` = 每天 2:00，`*/5 * * * *` = 每 5 分钟，`0 9 * * 1` = 每周一 9:00。

### 3.3 消息队列触发（SQS / EventBridge）

用户下单 → API 返回成功 → 后台异步发邮件/扣库存。这种**异步解耦**正是消息队列 + Serverless 的经典场景。

```yaml
# serverless.yml — SQS 触发 Lambda
functions:
  processOrder:
    handler: order.process
    events:
      - sqs:
          arn: !GetAtt OrderQueue.Arn
          batchSize: 10               # 每次最多处理 10 条消息
          maximumBatchingWindow: 5     # 最多等 5 秒凑满批次

resources:
  Resources:
    OrderQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: order-queue
        VisibilityTimeout: 60         # 处理超时后消息重新可见
        RedrivePolicy:                # 死信队列：失败 3 次后转移
          deadLetterTargetArn: !GetAtt DeadLetterQueue.Arn
          maxReceiveCount: 3
    DeadLetterQueue:
      Type: AWS::SQS::Queue
```

```js
// order.mjs — 批量处理消息
export const process = async (event) => {
  for (const record of event.Records) {
    const order = JSON.parse(record.body);
    console.log(`处理订单: ${order.orderId}`);
    // 发送确认邮件、扣减库存 ...
  }
};
```

> 💡 **SQS + Lambda 的好处**：API 函数只负责接收请求、写入队列、立即返回。后台 Lambda 从队列消费并处理。即使处理函数挂了，消息不会丢失——会重试或进入死信队列。

### 3.4 存储事件触发（S3 / 对象存储上传）

用户上传图片 → 自动触发 Lambda → 生成缩略图。这是最经典的 Serverless 用例之一。

```yaml
# serverless.yml
functions:
  generateThumbnail:
    handler: image.thumbnail
    events:
      - s3:
          bucket: my-uploads
          event: s3:ObjectCreated:*     # 任何文件创建都触发
          rules:
            - prefix: uploads/          # 只监听 uploads/ 目录
            - suffix: .jpg              # 只处理 .jpg 文件
```

```js
// image.mjs
import { S3Client, GetObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';
import sharp from 'sharp';

const s3 = new S3Client({});

export const thumbnail = async (event) => {
  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = record.s3.object.key;

    // 下载原图
    const { Body } = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
    const imageBuffer = await Body.transformToByteArray();

    // 生成缩略图（200x200）
    const thumbnail = await sharp(imageBuffer)
      .resize(200, 200, { fit: 'cover' })
      .jpeg({ quality: 80 })
      .toBuffer();

    // 上传缩略图
    const thumbKey = key.replace('uploads/', 'thumbnails/');
    await s3.send(new PutObjectCommand({
      Bucket: bucket,
      Key: thumbKey,
      Body: thumbnail,
      ContentType: 'image/jpeg',
    }));

    console.log(`缩略图已生成: ${thumbKey}`);
  }
};
```

> 💡 **注意避免无限循环**：如果 Lambda 把缩略图也写到同一个 bucket 的 `uploads/` 目录下，会再次触发自己！所以一定要用不同的前缀（`uploads/` → `thumbnails/`）。

### 3.5 数据库变更触发（DynamoDB Streams / Supabase Webhooks）

数据库中的数据变了 → 自动触发函数同步到其他系统（搜索引擎、缓存、通知）。

**DynamoDB Streams + Lambda：**

```yaml
# serverless.yml
functions:
  syncToSearch:
    handler: sync.toElasticsearch
    events:
      - stream:
          type: dynamodb
          arn: !GetAtt UsersTable.StreamArn
          batchSize: 100
          startingPosition: LATEST     # 只处理新变更
```

```js
// sync.mjs
export const toElasticsearch = async (event) => {
  for (const record of event.Records) {
    const { eventName, dynamodb } = record;

    if (eventName === 'INSERT' || eventName === 'MODIFY') {
      const newItem = dynamodb.NewImage;
      // 写入 Elasticsearch / Meilisearch ...
    }

    if (eventName === 'REMOVE') {
      const oldItem = dynamodb.OldImage;
      // 从搜索引擎删除 ...
    }
  }
};
```

**Supabase Database Webhooks（更简单）：**

Supabase 可以在 PostgreSQL 表变更时触发 HTTP 回调：

```
Supabase Dashboard → Database → Webhooks
  → 选择表：users
  → 事件：INSERT, UPDATE, DELETE
  → 目标 URL：https://your-app.vercel.app/api/webhook/user-sync
```

**五种触发器汇总：**

| 触发器 | 典型场景 | 平台支持 |
|:---|:---|:---|
| HTTP | API 后端 | 所有平台 |
| Cron | 定时报表、数据清理 | 所有平台 |
| 消息队列 | 异步任务、解耦 | AWS（SQS）、GCP（Pub/Sub） |
| 存储事件 | 图片处理、文件分析 | AWS（S3）、Cloudflare（R2） |
| 数据库变更 | 搜索同步、缓存刷新 | AWS（DynamoDB Streams）、Supabase |

---

## 4. 冷启动深度剖析与优化

冷启动是 Serverless 最大的性能痛点——理解它的原理，才能有效优化它。

### 4.1 冷启动原理：为什么第一次请求慢？

**冷启动 vs 热启动：**

```
冷启动（Cold Start）：函数实例不存在 → 需要从零创建
┌─────────────────────────────────────────────────────┐
│ 下载代码 → 创建容器 → 初始化运行时 → 加载依赖 → 执行 │
│ ~~~~~~~ 冷启动延迟（100ms - 数秒）~~~~~~~│ 执行  │
└─────────────────────────────────────────────────────┘

热启动（Warm Start）：函数实例已存在 → 直接复用
┌──────────────────┐
│ 执行（毫秒级）     │  ← 冷启动的容器会保留一段时间（5-60 分钟）
└──────────────────┘
```

**冷启动的触发条件：**

| 场景 | 是否冷启动 |
|:---|:---|
| 长时间没有请求（>5 分钟） | ✅ 冷启动 |
| 并发请求超过现有实例数 | ✅ 新实例冷启动 |
| 部署新版本代码 | ✅ 所有实例重建 |
| 连续请求、实例仍在 | ❌ 热启动 |

**冷启动耗时拆解：**

```
总冷启动时间 = 平台初始化 + 运行时初始化 + 你的代码初始化
              ~50ms（你控制不了） + ~50-200ms + ~10ms-数秒
                                              ▲ 这部分你能优化！
```

> 💡 **你能控制的部分**：减少依赖包大小、把初始化逻辑放到函数外部（handler 之外的代码只在冷启动时执行一次）。

### 4.2 语言运行时对比：Node.js vs Python vs Go vs Rust

不同语言的冷启动差异巨大：

| 语言 | 冷启动（P50） | 冷启动（P99） | 热启动 | 备注 |
|:---|:---|:---|:---|:---|
| **Node.js** | ~200ms | ~800ms | <5ms | 生态最丰富，推荐首选 |
| **Python** | ~250ms | ~1s | <5ms | AI/数据处理场景常用 |
| **Go** | ~80ms | ~200ms | <1ms | 编译型，冷启动极快 |
| **Rust** | ~50ms | ~150ms | <1ms | 最快，但开发效率低 |
| **Java** | ~1-3s | ~5-10s | <5ms | 冷启动最慢，不推荐 |

```
冷启动速度排名：Rust ≈ Go >> Node.js ≈ Python >> Java

推荐策略：
  大部分项目 → Node.js / TypeScript（生态好、冷启动可接受）
  延迟敏感   → Go / Rust（冷启动极快）
  AI 场景    → Python（库丰富，冷启动可用 Provisioned Concurrency 解决）
```

### 4.3 优化策略：预热、Provisioned Concurrency、最小化依赖

**策略 1：把初始化放到 handler 外部**

```js
// ❌ 每次请求都初始化数据库连接
export const handler = async (event) => {
  const db = new Database(process.env.DATABASE_URL);  // 每次冷启动+热启动都执行
  const result = await db.query('SELECT ...');
  return { statusCode: 200, body: JSON.stringify(result) };
};

// ✅ 只在冷启动时初始化一次
const db = new Database(process.env.DATABASE_URL);   // 冷启动时执行一次，热启动复用

export const handler = async (event) => {
  const result = await db.query('SELECT ...');
  return { statusCode: 200, body: JSON.stringify(result) };
};
```

**策略 2：最小化依赖包**

```bash
# 查看你的 Lambda 部署包有多大
du -sh .serverless/my-service.zip

# 目标：越小越好（<5MB 理想，<50MB 可接受）
```

```
优化手段：
  • 只安装 production 依赖：npm install --omit=dev
  • 用 esbuild / tsup 打包（tree-shaking 去除未使用代码）
  • 替换重量级库：moment.js(4.8MB) → dayjs(6KB)
  • AWS SDK v3 按需引入：@aws-sdk/client-s3 替代 aws-sdk
```

**策略 3：Provisioned Concurrency（预留并发）**

```yaml
# serverless.yml — 始终保持 5 个预热的实例
functions:
  api:
    handler: api.handler
    provisionedConcurrency: 5    # 永远有 5 个热实例等着
```

| 方案 | 冷启动 | 成本 | 适用场景 |
|:---|:---|:---|:---|
| 默认 | 有 | 最低 | 对延迟不敏感的内部 API |
| Provisioned Concurrency | 无 | 较高（按实例计费） | 面向用户的 API、支付回调 |
| 定时预热（Cron ping） | 可能有 | 低 | 简单场景的折中方案 |

**策略 4：选择合适的内存配置**

```
Lambda 的 CPU 和内存成正比：
  128MB  → 最小 CPU（便宜但慢）
  1024MB → 中等 CPU
  3008MB → 最大 CPU（贵但快）

反直觉的事实：加大内存可能更省钱！
  128MB × 3 秒 = 384 MB·s × $0.0000166 = $0.006
  1024MB × 0.4 秒 = 409 MB·s × $0.0000166 = $0.006
  → 价格差不多，但 1024MB 的用户体验好得多
```

> 💡 **用 AWS Lambda Power Tuning 工具**自动找到最佳内存配置——它会在不同内存下运行你的函数，给出性能和成本的最优平衡点。

### 4.4 Edge Functions：零冷启动的解决方案

Edge Functions 是对冷启动问题的**根本性解决**——它不使用容器，而是用 V8 Isolate（和 Chrome 浏览器同一个引擎）。

```
传统 FaaS（Lambda）：
  请求 → 启动容器 → 加载运行时 → 执行 → 返回
         ~~~ 冷启动 100ms-秒级 ~~~

Edge Functions（Workers / Vercel Edge）：
  请求 → V8 Isolate（已驻留内存）→ 执行 → 返回
         ~~~ 冷启动 <5ms ~~~
```

**为什么 Edge 快这么多？**

| 维度 | 传统 FaaS | Edge Functions |
|:---|:---|:---|
| 隔离方式 | 容器（microVM） | V8 Isolate |
| 启动开销 | 100ms-数秒 | <5ms |
| 执行位置 | 固定区域（如 us-east-1） | 全球 300+ 边缘节点 |
| 运行时 | Node.js / Python / Go | JS/TS + Web API（受限） |
| 可用 API | 完整 Node.js API | 不支持 fs、child_process 等 |
| 内存限制 | 最大 10GB | 通常 128MB |

**Edge Functions 的限制：**

```
❌ 不能用 Node.js 原生模块（fs、net、child_process）
❌ 不能用部分 npm 包（依赖 Node.js API 的）
❌ 内存限制小（128MB）
❌ 执行时间短（Cloudflare 免费版 10ms CPU time）
❌ 不能直连传统数据库（需要 HTTP 协议的数据库）
```

**最佳用法**：把 Edge 和传统 FaaS 组合使用。

```
用户请求 → Edge Function（鉴权、路由、缓存）→ Lambda（数据库操作、复杂业务）
           ~~~ 全球就近响应 ~~~                 ~~~ 靠近数据库 ~~~
```

> 💡 **选型总结**：简单逻辑（鉴权、重定向、A/B 测试、API 路由）用 Edge Functions。复杂业务（数据库 CRUD、文件处理）用传统 Lambda。两者搭配是目前的最佳架构。

---

## 5. 实战模式：常见应用架构

理论讲够了，现在进入实战。这一章用 5 个真实场景，展示 Serverless 如何构建生产级应用——每个场景都给出**可以直接用的代码**和架构设计。

> 💡 **本章目标**：掌握 Serverless 的 5 种典型应用模式，理解每种模式的架构选型和关键代码实现。

### 5.1 REST API / GraphQL 后端

最常见的 Serverless 用法——用函数搭建 API 后端。但"一个函数一个路由"会导致函数爆炸，所以实际项目都用**路由框架**。

**Serverless API 的分层架构：**

```
请求流程：
  客户端 → API Gateway / Platform Router → Lambda / Worker
                                              │
                                         路由框架（Hono / Express）
                                              │
                              ┌───────────────┼───────────────┐
                              │               │               │
                           中间件层        业务逻辑层       数据访问层
                         (鉴权/限流)    (Controller)    (DB/缓存)
```

**用 Hono 构建多平台 API（推荐）：**

Hono 是一个轻量级 Web 框架，专为 Serverless 设计——同一份代码可以运行在 Cloudflare Workers、Vercel、AWS Lambda 等多个平台。

```ts
// src/app.ts — 核心业务逻辑（平台无关）
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { jwt } from 'hono/jwt';

const app = new Hono();

// 中间件
app.use('/api/*', cors());
app.use('/api/protected/*', jwt({ secret: 'your-secret' }));

// RESTful 路由
app.get('/api/users', async (c) => {
  const users = await db.query('SELECT id, name, email FROM users LIMIT 20');
  return c.json({ data: users });
});

app.get('/api/users/:id', async (c) => {
  const id = c.req.param('id');
  const user = await db.query('SELECT * FROM users WHERE id = ?', [id]);
  if (!user) return c.json({ error: 'Not found' }, 404);
  return c.json({ data: user });
});

app.post('/api/users', async (c) => {
  const body = await c.req.json();
  const { name, email } = body;

  // 参数校验
  if (!name || !email) {
    return c.json({ error: 'name and email are required' }, 400);
  }

  const user = await db.insert('users', { name, email });
  return c.json({ data: user }, 201);
});

export default app;
```

```ts
// 入口文件 — Cloudflare Workers 版本
// src/index.ts
export default app;  // Hono 原生支持 Workers，直接导出即可

// 入口文件 — Vercel 版本
// app/api/[...route](...route)/route.ts
import { handle } from 'hono/vercel';
import app from '@/src/app';
export const GET = handle(app);
export const POST = handle(app);

// 入口文件 — AWS Lambda 版本
// lambda.ts
import { handle } from 'hono/aws-lambda';
import app from './src/app';
export const handler = handle(app);
```

> 💡 **为什么推荐 Hono**：体积极小（~14KB）、零依赖、类型安全、内置中间件（CORS / JWT / 限流）、支持所有主流 Serverless 平台。比 Express 更适合 Serverless 场景。

**GraphQL Serverless 方案：**

```ts
// app/api/graphql/route.ts（Vercel + Yoga）
import { createSchema, createYoga } from 'graphql-yoga';

const schema = createSchema({
  typeDefs: `
    type User {
      id: ID!
      name: String!
      email: String!
      posts: [Post!]!
    }
    type Post {
      id: ID!
      title: String!
      content: String!
    }
    type Query {
      user(id: ID!): User
      users(limit: Int = 10): [User!]!
    }
    type Mutation {
      createUser(name: String!, email: String!): User!
    }
  `,
  resolvers: {
    Query: {
      user: async (_, { id }) => await db.findUser(id),
      users: async (_, { limit }) => await db.listUsers(limit),
    },
    User: {
      posts: async (parent) => await db.findPostsByUser(parent.id),
    },
    Mutation: {
      createUser: async (_, { name, email }) => await db.createUser({ name, email }),
    },
  },
});

const { handleRequest } = createYoga({ schema, graphqlEndpoint: '/api/graphql' });
export { handleRequest as GET, handleRequest as POST };
```

**REST vs GraphQL 在 Serverless 中的选型：**

| 维度 | REST | GraphQL |
|:---|:---|:---|
| 冷启动影响 | 小（路由轻量） | 大（Schema 解析开销） |
| 缓存友好 | ✅ HTTP 缓存天然支持 | ❌ 需要额外缓存层 |
| 前端体验 | 多次请求拼数据 | 一次查询获取所有需要的字段 |
| 适合场景 | 简单 CRUD、对外 API | 复杂关联查询、BFF 层 |
| 推荐方案 | Hono / tRPC | GraphQL Yoga / Apollo |

### 5.2 Webhook 处理器（GitHub / Stripe / 支付回调）

Webhook 是第三方服务主动调用你的 API——支付成功通知、代码推送事件、表单提交等。Serverless 天然适合这种**低频、突发、异步**的场景。

**Webhook 的核心挑战——安全验证：**

```
第三方服务 → 你的 Webhook 端点
                  │
                  ├── 1. 验证签名（确认请求来源真实）
                  ├── 2. 幂等处理（同一事件可能发送多次）
                  └── 3. 快速返回（先返回 200，后台异步处理）
```

**Stripe 支付回调（生产级实现）：**

```ts
// app/api/webhook/stripe/route.ts
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: '2024-12-18.acacia' });

export async function POST(request: Request) {
  const body = await request.text();
  const signature = request.headers.get('stripe-signature')!;

  // 第 1 步：验证签名（防止伪造请求）
  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err) {
    console.error('签名验证失败:', err);
    return new Response('Invalid signature', { status: 400 });
  }

  // 第 2 步：幂等检查（Stripe 可能重发同一事件）
  const processed = await db.query(
    'SELECT 1 FROM webhook_events WHERE event_id = ?',
    [event.id]
  );
  if (processed) {
    return Response.json({ received: true });  // 已处理过，直接返回
  }

  // 第 3 步：按事件类型处理
  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;
      await activateSubscription(session.customer as string);
      break;
    }
    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice;
      await notifyPaymentFailed(invoice.customer as string);
      break;
    }
    case 'customer.subscription.deleted': {
      const sub = event.data.object as Stripe.Subscription;
      await deactivateSubscription(sub.customer as string);
      break;
    }
  }

  // 第 4 步：记录已处理（实现幂等）
  await db.insert('webhook_events', { event_id: event.id, type: event.type });
  return Response.json({ received: true });
}
```

**GitHub Webhook（代码推送触发部署）：**

```ts
// app/api/webhook/github/route.ts
import { createHmac, timingSafeEqual } from 'crypto';

function verifyGitHubSignature(payload: string, signature: string, secret: string): boolean {
  const expected = 'sha256=' + createHmac('sha256', secret).update(payload).digest('hex');
  return timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

export async function POST(request: Request) {
  const body = await request.text();
  const signature = request.headers.get('x-hub-signature-256')!;
  const event = request.headers.get('x-github-event')!;

  // 签名验证
  if (!verifyGitHubSignature(body, signature, process.env.GITHUB_WEBHOOK_SECRET!)) {
    return new Response('Invalid signature', { status: 401 });
  }

  const payload = JSON.parse(body);

  if (event === 'push' && payload.ref === 'refs/heads/main') {
    // 主分支推送 → 触发部署
    await triggerDeploy(payload.repository.full_name, payload.head_commit.id);
  }

  if (event === 'issues' && payload.action === 'opened') {
    // 新 Issue → 发送通知
    await sendNotification(`新 Issue: ${payload.issue.title}`);
  }

  return Response.json({ ok: true });
}
```

**Webhook 最佳实践清单：**

```
✅ 始终验证签名（HMAC-SHA256），不要信任任何未验证的请求
✅ 实现幂等性——用 event_id 做去重，同一事件处理多次不产生副作用
✅ 快速返回 2xx（< 3 秒），重逻辑放到后台队列异步执行
✅ 记录原始 payload（调试时非常有用）
✅ 用 timing-safe comparison 比较签名（防止时序攻击）
❌ 不要在 Webhook handler 中做耗时操作——第三方会超时重发
```

### 5.3 图片处理管线（上传→缩放→水印→CDN）

图片处理是 Serverless 的经典用例——用户上传一张原图，后台自动生成多种尺寸的缩略图、加水印、转换格式，最后通过 CDN 分发。

**端到端架构：**

```
客户端                  API 函数              S3 + Lambda              CDN
  │                       │                     │                     │
  ├─ 1. 请求上传 URL ────→│                     │                     │
  │←─ 返回预签名 URL ─────│                     │                     │
  ├─ 2. 直传 S3 ──────────────────────────────→│                     │
  │                       │   3. S3 Event 触发 →│ Lambda 处理          │
  │                       │                     ├─ 缩放 400x400       │
  │                       │                     ├─ 缩放 200x200       │
  │                       │                     ├─ 转 WebP 格式       │
  │                       │                     ├─ 加水印              │
  │                       │                     └─ 写入 processed/  →│ CDN 缓存
  │← 4. 通过 CDN 访问 ──────────────────────────────────────────────│
```

**第 1 步：预签名 URL（安全上传，不经过你的服务器）：**

```ts
// app/api/upload/route.ts — 生成预签名 URL
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { nanoid } from 'nanoid';

const s3 = new S3Client({ region: 'ap-northeast-1' });

export async function POST(request: Request) {
  const { contentType, fileName } = await request.json();

  // 校验文件类型
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowedTypes.includes(contentType)) {
    return Response.json({ error: '不支持的文件类型' }, { status: 400 });
  }

  // 生成唯一文件名（防止覆盖）
  const key = `uploads/${nanoid()}/${fileName}`;

  const command = new PutObjectCommand({
    Bucket: process.env.S3_BUCKET!,
    Key: key,
    ContentType: contentType,
    ContentLength: 10 * 1024 * 1024,  // 限制 10MB
  });

  // 预签名 URL 有效期 5 分钟
  const uploadUrl = await getSignedUrl(s3, command, { expiresIn: 300 });

  return Response.json({ uploadUrl, key });
}
```

**第 2 步：S3 触发 Lambda 处理图片：**

```ts
// image-processor.ts — Lambda 图片处理函数
import { S3Client, GetObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';
import sharp from 'sharp';

const s3 = new S3Client({});

// 定义需要生成的尺寸
const SIZES = [
  { name: 'large', width: 800, height: 800 },
  { name: 'medium', width: 400, height: 400 },
  { name: 'thumb', width: 200, height: 200 },
];

export const handler = async (event: any) => {
  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = decodeURIComponent(record.s3.object.key.replace(/\+/g, ' '));

    // 下载原图
    const { Body, ContentType } = await s3.send(
      new GetObjectCommand({ Bucket: bucket, Key: key })
    );
    const imageBuffer = Buffer.from(await Body!.transformToByteArray());

    // 并行生成多种尺寸
    const tasks = SIZES.map(async (size) => {
      const processed = await sharp(imageBuffer)
        .resize(size.width, size.height, { fit: 'inside', withoutEnlargement: true })
        .webp({ quality: 85 })          // 统一转 WebP，体积减少 30-50%
        .toBuffer();

      const outputKey = key
        .replace('uploads/', `processed/${size.name}/`)
        .replace(/\.\w+$/, '.webp');

      await s3.send(new PutObjectCommand({
        Bucket: bucket,
        Key: outputKey,
        Body: processed,
        ContentType: 'image/webp',
        CacheControl: 'public, max-age=31536000',  // CDN 缓存 1 年
      }));

      return { size: size.name, key: outputKey };
    });

    const results = await Promise.all(tasks);
    console.log(`图片处理完成: ${key}`, results);
  }
};
```

> 💡 **为什么用预签名 URL**：客户端直接上传到 S3，不经过你的 Serverless 函数——避免了函数处理大文件时的超时和内存限制。函数只负责生成一个"一次性授权 URL"。

**更简单的方案——Cloudflare Images：**

如果你不想自己写图片处理逻辑，Cloudflare Images 提供了开箱即用的方案：

```
上传一张原图 → Cloudflare 自动生成多种变体
访问时按需变换：
  /cdn-cgi/image/width=200,quality=80/your-image.jpg
  /cdn-cgi/image/width=800,format=webp/your-image.jpg
```

### 5.4 定时任务与批处理（数据清洗、报表生成）

"每天凌晨清理过期数据"、"每周生成运营报表"——这些任务不需要 7×24 运行的服务器，用 Cron + Serverless 函数就够了。

**数据清洗（定时清理过期记录）：**

```ts
// cron/cleanup.ts
export const handler = async () => {
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);

  // 清理过期的临时文件记录
  const deletedFiles = await db.execute(
    'DELETE FROM temp_files WHERE created_at < ? RETURNING id',
    [thirtyDaysAgo.toISOString()]
  );

  // 清理过期的 session
  const deletedSessions = await db.execute(
    'DELETE FROM sessions WHERE expires_at < NOW() RETURNING id'
  );

  // 清理未验证的注册用户（超过 7 天未验证邮箱）
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
  const deletedUsers = await db.execute(
    'DELETE FROM users WHERE verified = false AND created_at < ? RETURNING id',
    [sevenDaysAgo.toISOString()]
  );

  const summary = {
    tempFiles: deletedFiles.length,
    sessions: deletedSessions.length,
    unverifiedUsers: deletedUsers.length,
    executedAt: new Date().toISOString(),
  };

  console.log('清理完成:', summary);

  // 可选：发送清理报告到 Slack
  await sendSlackNotification(`🧹 数据清理完成: ${JSON.stringify(summary)}`);

  return summary;
};
```

**大批量数据处理——分片模式：**

当数据量太大（百万行），单个 Lambda 15 分钟跑不完时，需要**分片处理**：

```
Step Functions 编排：
  ┌────────────────┐
  │ 分片函数         │ → 把 100 万条数据分成 100 个批次
  └───────┬────────┘
          │ 并行触发
  ┌───────┼──────────────────────────────┐
  │       │             │                │
  ▼       ▼             ▼                ▼
批次 1   批次 2   ...  批次 99         批次 100
(1万条)  (1万条)       (1万条)         (1万条)
  │       │             │                │
  └───────┴──────────────┴────────┬───────┘
                                  │
                           ┌──────▼──────┐
                           │ 汇总函数     │ → 合并结果、生成报告
                           └─────────────┘
```

```ts
// batch/splitter.ts — 分片函数
export const handler = async () => {
  const totalCount = await db.queryOne('SELECT COUNT(*) as cnt FROM orders WHERE status = ?', ['pending']);
  const batchSize = 10000;
  const batches = Math.ceil(totalCount.cnt / batchSize);

  // 返回批次列表，Step Functions 会并行调用处理函数
  return Array.from({ length: batches }, (_, i) => ({
    offset: i * batchSize,
    limit: batchSize,
    batchIndex: i,
  }));
};

// batch/processor.ts — 单批次处理函数
export const handler = async (event: { offset: number; limit: number; batchIndex: number }) => {
  const orders = await db.query(
    'SELECT * FROM orders WHERE status = ? ORDER BY id LIMIT ? OFFSET ?',
    ['pending', event.limit, event.offset]
  );

  let processed = 0;
  for (const order of orders) {
    await processOrder(order);  // 你的业务逻辑
    processed++;
  }

  return { batchIndex: event.batchIndex, processed };
};
```

**报表生成（完整流程）：**

```ts
// cron/weekly-report.ts — 每周一生成运营报表
export const handler = async () => {
  const lastWeek = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

  // 聚合数据
  const stats = await db.queryOne(`
    SELECT
      COUNT(*) as total_orders,
      SUM(amount) as total_revenue,
      COUNT(DISTINCT user_id) as unique_customers,
      AVG(amount) as avg_order_value
    FROM orders
    WHERE created_at >= ?
  `, [lastWeek.toISOString()]);

  // 生成 CSV
  const csv = generateCSV(await db.query(
    'SELECT * FROM orders WHERE created_at >= ? ORDER BY created_at',
    [lastWeek.toISOString()]
  ));

  // 上传到 S3
  await s3.send(new PutObjectCommand({
    Bucket: 'reports',
    Key: `weekly/${formatDate(new Date())}.csv`,
    Body: csv,
    ContentType: 'text/csv',
  }));

  // 发送邮件通知
  await sendEmail({
    to: 'team@company.com',
    subject: `周报 ${formatDate(new Date())}`,
    body: `本周订单 ${stats.total_orders} 笔，收入 ¥${stats.total_revenue}`,
  });
};
```

> 💡 **Lambda 的 15 分钟限制**不是问题——单次清理、单个报表通常几十秒就完成。真正的大批量任务用 Step Functions 分片并行处理，每个分片只需几分钟。

### 5.5 AI 推理服务（LLM API 代理、向量搜索）

AI 应用是 Serverless 的新热门场景——用函数做 LLM API 代理、实现 RAG 检索、向量搜索。Serverless 的按需付费特性完美匹配 AI 推理的突发流量。

**LLM API 代理（流式响应）：**

```ts
// app/api/chat/route.ts — OpenAI 代理 + 流式输出
import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function POST(request: Request) {
  const { messages, model = 'gpt-4o-mini' } = await request.json();

  // 流式调用 OpenAI
  const stream = await openai.chat.completions.create({
    model,
    messages,
    stream: true,
    max_tokens: 2000,
  });

  // 用 ReadableStream 转发流式响应
  const encoder = new TextEncoder();
  const readable = new ReadableStream({
    async start(controller) {
      for await (const chunk of stream) {
        const content = chunk.choices[0]?.delta?.content || '';
        if (content) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ content })}\n\n`));
        }
      }
      controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      controller.close();
    },
  });

  return new Response(readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
```

**为什么要做代理而不是前端直连 AI API？**

```
❌ 前端直连：API Key 暴露在客户端 → 安全灾难
✅ Serverless 代理：
   客户端 → 你的 API（鉴权 + 限流）→ OpenAI / Claude
                │
                ├── 隐藏 API Key
                ├── 统一鉴权（JWT / API Key）
                ├── 用量限流（防止滥用）
                ├── 请求/响应日志（计费审计）
                └── 模型切换（前端无感知）
```

**向量搜索 + RAG：**

```ts
// app/api/search/route.ts — 语义搜索 + LLM 回答
export async function POST(request: Request) {
  const { query } = await request.json();

  // 第 1 步：把用户问题转成向量
  const embedding = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: query,
  });
  const queryVector = embedding.data[0].embedding;

  // 第 2 步：在向量数据库中搜索相似文档
  // 使用 Cloudflare Vectorize / Pinecone / Supabase pgvector
  const results = await vectorDB.query({
    vector: queryVector,
    topK: 5,
    includeMetadata: true,
  });

  // 第 3 步：用检索到的文档作为上下文，让 LLM 回答
  const context = results.matches.map(m => m.metadata.text).join('\n\n');
  const answer = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      { role: 'system', content: `基于以下文档回答问题，如果文档中没有相关信息就说不知道：\n\n${context}` },
      { role: 'user', content: query },
    ],
  });

  return Response.json({
    answer: answer.choices[0].message.content,
    sources: results.matches.map(m => ({
      title: m.metadata.title,
      score: m.score,
    })),
  });
}
```

**AI 场景的 Serverless 架构选型：**

| 场景 | 推荐方案 | 原因 |
|:---|:---|:---|
| LLM API 代理 | Vercel / Cloudflare Workers | 流式响应、低延迟 |
| 向量搜索 | Cloudflare Workers + Vectorize | 边缘执行、数据就近 |
| 图片/语音生成 | AWS Lambda（大内存） | 需要较多内存和执行时间 |
| 模型微调 | 不适合 Serverless | 用 GPU 云实例或专用平台 |

> 💡 **AI + Serverless 的最大优势是成本弹性**：你的 AI 应用可能白天有 1000 QPS、凌晨只有 10 QPS。Serverless 自动扩缩容 + 按需付费，比 7×24 跑 GPU 实例省太多了。

---

## 6. 数据持久化：Serverless 数据库选型

Serverless 函数是**无状态**的——每次执行完就可能被销毁，下次执行可能在完全不同的容器里。这意味着你不能像传统服务器那样维持一个全局数据库连接池。这一章解决核心问题：**无状态的函数如何高效地访问有状态的数据？**

> 💡 **本章目标**：理解 Serverless 环境的数据库挑战，掌握 Serverless-native 数据库、KV 存储和对象存储的选型与实战用法。

### 6.1 传统数据库的连接池问题

把一个传统 PostgreSQL / MySQL 直接连到 Lambda 函数上，几乎一定会遇到**连接池耗尽**的问题。

**为什么会崩？**

```
传统服务器（1 个进程，1 个连接池）：
  服务器 ──── 连接池（20 个连接）──── PostgreSQL
  同时处理 100 个请求，共享 20 个连接 → ✅ 没问题

Serverless（N 个函数实例，每个一个连接）：
  Lambda 实例 1 ── 1 个连接 ─┐
  Lambda 实例 2 ── 1 个连接 ─┤
  Lambda 实例 3 ── 1 个连接 ─┤── PostgreSQL（max_connections = 100）
  ...                        │
  Lambda 实例 150 ── 1 个连接 ┘ → ❌ 超过连接上限！
```

**连接数爆炸的根因：**

| 问题 | 原因 |
|:---|:---|
| 每个实例一个连接 | Lambda 实例之间不共享内存，无法共享连接池 |
| 并发 = 实例数 | 100 个并发请求 = 100 个 Lambda 实例 = 100 个数据库连接 |
| 连接不释放 | 热实例保持连接但可能空闲，占着连接不干活 |
| 流量尖峰 | 突然涌入 500 个请求 → 瞬间 500 个连接 → 数据库直接崩 |

**解决方案 1：连接池代理**

在 Lambda 和数据库之间加一个**连接池代理**，让代理管理连接的复用：

```
Lambda 实例群（可能几百个）
    │
    ▼
连接池代理（RDS Proxy / PgBouncer）← 管理连接复用
    │
    ▼ 只维持少量连接
PostgreSQL（max_connections = 100）
```

**AWS RDS Proxy 配置：**

```yaml
# serverless.yml
provider:
  environment:
    # 通过 RDS Proxy 连接，而不是直连数据库
    DATABASE_URL: postgresql://user:pass@my-proxy.proxy-xxx.rds.amazonaws.com:5432/mydb
```

**解决方案 2：HTTP 协议数据库（根本性解决）**

传统数据库用 TCP 长连接——这在 Serverless 中天生不友好。新一代 Serverless 数据库用 **HTTP 协议**：

```
传统方式（TCP 长连接）：
  Lambda → TCP 连接 → PostgreSQL
  问题：连接建立慢、连接数有限、空闲浪费

HTTP 方式（无连接状态）：
  Lambda → HTTP POST /query → Serverless DB（Neon / PlanetScale）
  优势：无连接管理、无限并发、每次请求独立
```

```ts
// 传统方式 — TCP 连接（有连接池问题）
import { Pool } from 'pg';
const pool = new Pool({ connectionString: process.env.DATABASE_URL, max: 1 });

// HTTP 方式 — Neon Serverless Driver（推荐）
import { neon } from '@neondatabase/serverless';
const sql = neon(process.env.DATABASE_URL!);

// 用法完全一样，但底层是 HTTP，没有连接池问题
const users = await sql`SELECT * FROM users WHERE active = true LIMIT 10`;
```

> 💡 **结论**：如果你用 PostgreSQL + Serverless，首选 Neon（HTTP 驱动 + 连接池内置）。如果必须用已有的 RDS，加上 RDS Proxy 缓解连接数问题。

### 6.2 Serverless-native 数据库：Neon / PlanetScale / Turso

这些数据库从设计之初就为 Serverless 优化——HTTP 协议、自动扩缩容、按用量计费、零连接管理。

**三大 Serverless 数据库对比：**

| 维度 | Neon | PlanetScale | Turso |
|:---|:---|:---|:---|
| **底层引擎** | PostgreSQL | MySQL (Vitess) | SQLite (libSQL) |
| **协议** | HTTP + WebSocket | HTTP | HTTP |
| **分支功能** | ✅ 数据库分支（类似 Git） | ✅ Schema 分支 | ✅ 数据库分支 |
| **自动休眠** | ✅ 空闲自动暂停 | ❌ | ✅ 空闲自动休眠 |
| **冷启动** | ~500ms（从休眠恢复） | 无（始终在线） | ~100ms |
| **免费额度** | 0.5GB 存储 + 190 小时计算 | 5GB 存储 + 10 亿行读取 | 9GB 存储 + 5 亿行读取 |
| **适合场景** | 全栈项目、需要 PG 生态 | 大规模、需要分库分表 | 边缘应用、嵌入式 |
| **ORM 支持** | Drizzle / Prisma / Kysely | Drizzle / Prisma | Drizzle / Prisma |

**Neon（推荐——PostgreSQL 兼容）：**

```ts
// 方式 1：Neon Serverless Driver（HTTP，最轻量）
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL!);

// Tagged template 语法，自动防 SQL 注入
const users = await sql`
  SELECT id, name, email
  FROM users
  WHERE created_at > ${thirtyDaysAgo}
  ORDER BY created_at DESC
  LIMIT 20
`;

// 方式 2：配合 Drizzle ORM（类型安全，推荐生产使用）
import { drizzle } from 'drizzle-orm/neon-http';
import { neon } from '@neondatabase/serverless';
import { users } from './schema';

const sql = neon(process.env.DATABASE_URL!);
const db = drizzle(sql);

const result = await db.select()
  .from(users)
  .where(gt(users.createdAt, thirtyDaysAgo))
  .orderBy(desc(users.createdAt))
  .limit(20);
```

**Turso（边缘数据库——SQLite 在云端）：**

Turso 的独特之处：数据库可以部署到全球边缘节点，读取延迟极低。

```ts
// Turso + Drizzle
import { drizzle } from 'drizzle-orm/libsql';
import { createClient } from '@libsql/client';

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

const db = drizzle(client);

// 用法和其他 Drizzle 一样
const posts = await db.select().from(postsTable).limit(10);
```

**选型决策树：**

```
需要 PostgreSQL 兼容（JSON、全文搜索、数组类型）？
  → Neon

需要 MySQL 兼容、水平分片、高写入吞吐？
  → PlanetScale

需要边缘部署、嵌入式、极低延迟读取？
  → Turso

不确定选哪个？
  → Neon（PostgreSQL 生态最成熟，Drizzle 支持最好）
```

> 💡 **数据库分支是杀手级特性**：Neon 和 Turso 都支持像 Git 一样创建数据库分支。每个 PR 可以有独立的数据库副本用于测试，合并后销毁——不影响生产数据。

### 6.3 键值存储：Vercel KV / Cloudflare KV / DynamoDB

不是所有数据都需要关系数据库。Session、缓存、配置、计数器——这些用**键值存储**更快、更便宜。

**KV 存储对比：**

| 维度 | Cloudflare KV | Vercel KV | DynamoDB |
|:---|:---|:---|:---|
| **底层** | 全球边缘分布式 | Redis (Upstash) | AWS 托管 |
| **一致性** | 最终一致（~60s） | 强一致 | 可选强/最终一致 |
| **延迟** | 读 <10ms（边缘） | 读 <5ms | 读 <10ms |
| **数据模型** | 纯 KV（字符串） | Redis（列表/集合/哈希） | 文档（JSON） |
| **免费额度** | 10 万次读/天 | 3000 次/天 | 25GB + 2500 万次读/月 |
| **最佳搭配** | Cloudflare Workers | Vercel Functions | AWS Lambda |

**Cloudflare KV（全球边缘缓存）：**

```ts
// Cloudflare Workers + KV
export default {
  async fetch(request: Request, env: Env) {
    const url = new URL(request.url);
    const cacheKey = `page:${url.pathname}`;

    // 先查缓存
    const cached = await env.MY_KV.get(cacheKey);
    if (cached) {
      return new Response(cached, {
        headers: { 'Content-Type': 'text/html', 'X-Cache': 'HIT' },
      });
    }

    // 缓存未命中 → 生成页面
    const html = await renderPage(url.pathname);

    // 写入缓存（TTL 1 小时）
    await env.MY_KV.put(cacheKey, html, { expirationTtl: 3600 });

    return new Response(html, {
      headers: { 'Content-Type': 'text/html', 'X-Cache': 'MISS' },
    });
  },
};
```

**Vercel KV（Redis 兼容——更丰富的数据结构）：**

```ts
// app/api/rate-limit/route.ts — 用 KV 实现 API 限流
import { kv } from '@vercel/kv';

export async function POST(request: Request) {
  const ip = request.headers.get('x-forwarded-for') || 'unknown';
  const key = `rate:${ip}`;
  const windowMs = 60;       // 60 秒窗口
  const maxRequests = 20;    // 最多 20 次

  // INCR 原子递增 + 设置过期时间
  const current = await kv.incr(key);
  if (current === 1) {
    await kv.expire(key, windowMs);  // 首次请求设置 TTL
  }

  if (current > maxRequests) {
    return Response.json(
      { error: '请求过于频繁，请稍后再试' },
      { status: 429, headers: { 'Retry-After': String(windowMs) } }
    );
  }

  // 正常处理请求 ...
  return Response.json({ data: 'ok', remaining: maxRequests - current });
}
```

**DynamoDB（AWS 生态的首选 NoSQL）：**

```ts
// 用 DynamoDB 存储用户 Session
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand, PutCommand } from '@aws-sdk/lib-dynamodb';

const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));

// 写入 Session
await client.send(new PutCommand({
  TableName: 'sessions',
  Item: {
    sessionId: 'sess_abc123',
    userId: 'user_456',
    data: { cart: ['item1', 'item2'] },
    ttl: Math.floor(Date.now() / 1000) + 86400,  // 24 小时后自动删除
  },
}));

// 读取 Session
const { Item } = await client.send(new GetCommand({
  TableName: 'sessions',
  Key: { sessionId: 'sess_abc123' },
}));
```

> 💡 **选型建议**：缓存/配置类数据用 Cloudflare KV（全球就近读取）。需要计数器/队列/排行榜等复杂操作用 Vercel KV（Redis 数据结构）。AWS 生态内的文档存储用 DynamoDB。

### 6.4 对象存储与文件管理：S3 / R2 / Supabase Storage

图片、视频、文档、用户上传的文件——这些非结构化数据用**对象存储**，不用数据库。

**对象存储对比：**

| 维度 | AWS S3 | Cloudflare R2 | Supabase Storage |
|:---|:---|:---|:---|
| **定价模型** | 存储 + 请求 + 出口流量 | 存储 + 请求（**零出口费**） | 存储 + 带宽 |
| **出口费用** | $0.09/GB（最贵） | **$0（免费！）** | $0.09/GB |
| **S3 兼容** | 原生 | ✅ 完全兼容 | 部分兼容 |
| **CDN 集成** | 需配合 CloudFront | 自带全球 CDN | 自带 CDN |
| **免费额度** | 5GB（12 个月） | 10GB + 100 万次读/月 | 1GB |
| **独特优势** | 生态最完整 | 零出口费用 | 集成 RLS 权限控制 |

**Cloudflare R2（推荐——零出口费用）：**

R2 最大的卖点：**没有出口流量费**。S3 的出口费用可能占总成本的 60-80%，R2 直接省掉。

```ts
// Cloudflare Workers + R2
export default {
  async fetch(request: Request, env: Env) {
    const url = new URL(request.url);
    const key = url.pathname.slice(1);  // /images/photo.jpg → images/photo.jpg

    if (request.method === 'GET') {
      const object = await env.MY_BUCKET.get(key);
      if (!object) return new Response('Not Found', { status: 404 });

      return new Response(object.body, {
        headers: {
          'Content-Type': object.httpMetadata?.contentType || 'application/octet-stream',
          'Cache-Control': 'public, max-age=31536000',
        },
      });
    }

    if (request.method === 'PUT') {
      await env.MY_BUCKET.put(key, request.body, {
        httpMetadata: { contentType: request.headers.get('Content-Type') || undefined },
      });
      return Response.json({ key, url: `https://cdn.example.com/${key}` });
    }
  },
};
```

**Supabase Storage（集成权限控制）：**

Supabase Storage 的独特之处是**行级安全策略（RLS）**——可以用 SQL 规则精细控制谁能访问哪些文件。

```ts
// 客户端上传（Supabase SDK）
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, key);

// 上传到 avatars bucket
const { data, error } = await supabase.storage
  .from('avatars')
  .upload(`${userId}/avatar.jpg`, file, {
    contentType: 'image/jpeg',
    upsert: true,  // 覆盖已有文件
  });

// 获取公开 URL
const { data: { publicUrl } } = supabase.storage
  .from('avatars')
  .getPublicUrl(`${userId}/avatar.jpg`);
```

```sql
-- Supabase Storage RLS 策略
-- 只允许用户访问自己的文件
CREATE POLICY "用户只能访问自己的文件"
ON storage.objects FOR SELECT
USING (auth.uid()::text = (storage.foldername(name))[1]);

-- 只允许用户上传到自己的目录
CREATE POLICY "用户只能上传到自己的目录"
ON storage.objects FOR INSERT
WITH CHECK (auth.uid()::text = (storage.foldername(name))[1]);
```

**第 6 章数据存储全景汇总：**

| 数据类型 | 推荐方案 | 原因 |
|:---|:---|:---|
| 结构化数据（用户、订单） | Neon / PlanetScale | SQL 查询、事务、关联 |
| Session / 缓存 | Vercel KV / Cloudflare KV | 低延迟读写、自动过期 |
| 文件 / 图片 / 视频 | Cloudflare R2 | 零出口费用、S3 兼容 |
| 全文搜索 | Meilisearch / Algolia | 专为搜索优化 |
| 向量数据 | Cloudflare Vectorize / Pinecone | AI/RAG 场景 |

> 💡 **一个典型的 Serverless 全栈应用的数据架构**：Neon（主数据库）+ Vercel KV（缓存 + Session）+ R2（文件存储）+ Meilisearch（搜索）。四个服务都有免费额度，个人项目基本零成本。

---

## 7. 部署与 CI/CD

手动在控制台上传代码？一次两次还行，长期维护不可能。Serverless 项目也需要**基础设施即代码（IaC）**——用配置文件描述你的函数、触发器、权限，一条命令完成部署。

> 💡 **本章目标**：掌握主流 Serverless 部署框架的使用方法，搭建从 Git Push 到自动部署的 CI/CD 流水线。

### 7.1 Serverless Framework（多云部署）

Serverless Framework 是最老牌、生态最丰富的 Serverless 部署框架——一个 YAML 文件定义所有资源，一条命令部署到 AWS / Azure / 腾讯云。

**核心概念——serverless.yml：**

```yaml
# serverless.yml — 一个完整的 API 项目
service: my-api
frameworkVersion: '3'

provider:
  name: aws
  runtime: nodejs20.x
  region: ap-northeast-1
  stage: ${opt:stage, 'dev'}          # 从命令行参数读取，默认 dev
  memorySize: 256                      # 默认内存（可按函数覆盖）
  timeout: 10                          # 默认超时（秒）
  environment:                         # 环境变量（所有函数共享）
    DATABASE_URL: ${env:DATABASE_URL}
    NODE_ENV: ${self:provider.stage}
  iam:                                 # IAM 权限（最小权限原则）
    role:
      statements:
        - Effect: Allow
          Action:
            - dynamodb:GetItem
            - dynamodb:PutItem
            - dynamodb:Query
          Resource: !GetAtt UsersTable.Arn

functions:
  getUser:
    handler: src/handlers/users.get
    events:
      - httpApi:
          path: /users/{id}
          method: get

  createUser:
    handler: src/handlers/users.create
    memorySize: 512                    # 覆盖默认值
    events:
      - httpApi:
          path: /users
          method: post

  processQueue:
    handler: src/handlers/queue.process
    timeout: 60
    events:
      - sqs:
          arn: !GetAtt TaskQueue.Arn
          batchSize: 10

  dailyCleanup:
    handler: src/handlers/cron.cleanup
    events:
      - schedule:
          rate: cron(0 2 * * ? *)      # 每天凌晨 2 点

resources:
  Resources:
    UsersTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: ${self:service}-users-${self:provider.stage}
        AttributeDefinitions:
          - AttributeName: id
            AttributeType: S
        KeySchema:
          - AttributeName: id
            KeyType: HASH
        BillingMode: PAY_PER_REQUEST

    TaskQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: ${self:service}-tasks-${self:provider.stage}
```

**多环境部署：**

```bash
# 部署到不同环境（通过 --stage 参数）
serverless deploy --stage dev        # 开发环境
serverless deploy --stage staging    # 预发布环境
serverless deploy --stage prod       # 生产环境

# 每个环境的资源完全独立：
#   dev:  my-api-users-dev、my-api-tasks-dev
#   prod: my-api-users-prod、my-api-tasks-prod

# 部署单个函数（更快，不重建整个 Stack）
serverless deploy function --function getUser --stage prod

# 查看日志
serverless logs --function getUser --stage prod --tail

# 删除整个项目（清理所有资源）
serverless remove --stage dev
```

**常用插件生态：**

| 插件 | 功能 |
|:---|:---|
| `serverless-offline` | 本地模拟 API Gateway + Lambda |
| `serverless-esbuild` | 用 esbuild 打包（极快，减少部署包体积） |
| `serverless-dotenv-plugin` | 从 .env 文件加载环境变量 |
| `serverless-domain-manager` | 自定义域名绑定 |
| `serverless-prune-plugin` | 自动清理旧版本部署（Lambda 有版本数限制） |

```yaml
# 插件配置示例
plugins:
  - serverless-esbuild
  - serverless-offline
  - serverless-dotenv-plugin

custom:
  esbuild:
    bundle: true
    minify: true
    sourcemap: true
    target: node20
    exclude:
      - '@aws-sdk/*'    # Lambda 运行时已内置，不需要打包
```

> 💡 **Serverless Framework 的核心优势**：多云支持（AWS/Azure/腾讯云）、插件丰富、社区大。缺点是 v3 之后部分功能需要付费（Dashboard），纯开源用户建议关注 SST。

### 7.2 AWS SAM（AWS 官方方案）

AWS SAM（Serverless Application Model）是 AWS 官方的 Serverless 部署工具——如果你只用 AWS，它比 Serverless Framework 更贴近底层，也不需要第三方付费。

**SAM 模板（template.yaml）：**

```yaml
# template.yaml — SAM 使用 CloudFormation 扩展语法
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: My Serverless API

Globals:                               # 全局默认配置
  Function:
    Runtime: nodejs20.x
    MemorySize: 256
    Timeout: 10
    Environment:
      Variables:
        NODE_ENV: !Ref Stage

Parameters:
  Stage:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]

Resources:
  GetUserFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src/handlers/users.get
      Events:
        GetUser:
          Type: HttpApi
          Properties:
            Path: /users/{id}
            Method: get
      Policies:
        - DynamoDBReadPolicy:          # SAM 内置策略模板（比手写 IAM 简单）
            TableName: !Ref UsersTable

  CreateUserFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src/handlers/users.create
      MemorySize: 512
      Events:
        CreateUser:
          Type: HttpApi
          Properties:
            Path: /users
            Method: post
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref UsersTable

  UsersTable:
    Type: AWS::Serverless::SimpleTable
    Properties:
      PrimaryKey:
        Name: id
        Type: String

Outputs:
  ApiUrl:
    Description: API Gateway URL
    Value: !Sub 'https://${ServerlessHttpApi}.execute-api.${AWS::Region}.amazonaws.com'
```

**SAM CLI 工作流：**

```bash
# 初始化项目（交互式选择模板）
sam init

# 构建（安装依赖、编译 TypeScript 等）
sam build

# 本地测试
sam local start-api                    # 启动本地 API（需要 Docker）
sam local invoke GetUserFunction \     # 单次调用测试
  --event events/get-user.json

# 部署（首次需要 --guided 交互式配置）
sam deploy --guided                    # 首次部署
sam deploy                             # 后续部署（使用 samconfig.toml 配置）

# 查看日志
sam logs --name GetUserFunction --tail

# 同步开发（文件修改自动部署，不需要重新 build）
sam sync --watch --stack-name my-api-dev
```

**SAM vs Serverless Framework 对比：**

| 维度 | AWS SAM | Serverless Framework |
|:---|:---|:---|
| 云平台 | 仅 AWS | AWS / Azure / 腾讯云 / GCP |
| 配置语法 | CloudFormation（冗长但精确） | 自有 YAML（简洁） |
| 本地调试 | `sam local`（Docker 模拟） | `serverless-offline`（插件） |
| 学习曲线 | 需要了解 CloudFormation | 相对简单 |
| 付费 | 完全免费开源 | Dashboard 部分功能付费 |
| 适合谁 | AWS 深度用户、企业合规 | 多云 / 快速原型 |

> 💡 **选 SAM 还是 Serverless Framework？** 如果你只用 AWS 且团队熟悉 CloudFormation → SAM。如果你要多云、追求简洁 → Serverless Framework。如果你用 TypeScript → 往下看 SST。

### 7.3 SST（TypeScript 优先的 Serverless 框架）

SST 是近年崛起最快的 Serverless 框架——**用 TypeScript 定义基础设施**（不是 YAML），拥有最好的本地开发体验。

**SST 的核心优势：**

```
1. TypeScript 定义基础设施 → 类型提示、自动补全、编译时检查
2. Live Lambda Dev → 本地代码直接连到云端资源调试（不需要 Docker）
3. 资源绑定（bind）→ 资源权限自动注入，不手写 IAM
4. SST Console → 可视化管理面板
```

**SST v3（Ion 架构）配置示例：**

```ts
// sst.config.ts — 用 TypeScript 定义所有资源
export default $config({
  app(input) {
    return {
      name: 'my-app',
      removal: input.stage === 'prod' ? 'retain' : 'remove',
      home: 'aws',
    };
  },
  async run() {
    // 创建数据库表
    const table = new sst.aws.DynamoTable('Users', {
      fields: { id: 'string', email: 'string' },
      primaryIndex: { hashKey: 'id' },
      globalIndexes: { emailIndex: { hashKey: 'email' } },
    });

    // 创建存储桶
    const bucket = new sst.aws.Bucket('Uploads');

    // 创建 API（自动绑定资源 → 函数内可直接访问）
    const api = new sst.aws.ApiGatewayV2('Api');

    api.route('GET /users/{id}', {
      handler: 'src/handlers/users.get',
      link: [table],           // 绑定 DynamoDB 表（权限自动注入）
    });

    api.route('POST /users', {
      handler: 'src/handlers/users.create',
      link: [table, bucket],   // 同时绑定表和存储桶
    });

    // 定时任务
    new sst.aws.Cron('DailyCleanup', {
      schedule: 'cron(0 2 * * ? *)',
      job: {
        handler: 'src/handlers/cron.cleanup',
        link: [table],
      },
    });

    return { apiUrl: api.url };
  },
});
```

**资源绑定——SST 最优雅的设计：**

```ts
// src/handlers/users.ts — 函数中通过 Resource 访问绑定的资源
import { Resource } from 'sst';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand } from '@aws-sdk/lib-dynamodb';

const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));

export const get = async (event: any) => {
  const { Item } = await client.send(new GetCommand({
    TableName: Resource.Users.name,    // 通过 Resource 获取表名（有类型提示！）
    Key: { id: event.pathParameters.id },
  }));

  return { statusCode: 200, body: JSON.stringify(Item) };
};
// 不需要手写 IAM 权限、不需要硬编码表名
// SST 的 link 机制自动处理了权限和环境变量注入
```

**SST CLI 工作流：**

```bash
# 创建项目
npx sst@latest init

# 本地开发（Live Lambda Dev — 云端资源 + 本地代码）
npx sst dev

# 部署到指定环境
npx sst deploy --stage prod

# 打开管理面板
npx sst console

# 删除环境
npx sst remove --stage dev
```

**三大框架最终对比：**

| 维度 | Serverless Framework | AWS SAM | SST |
|:---|:---|:---|:---|
| 配置语言 | YAML | YAML (CloudFormation) | **TypeScript** |
| 多云 | ✅ | ❌ 仅 AWS | ❌ 仅 AWS |
| 本地开发 | 插件模拟 | Docker 模拟 | **Live Dev（真实云端）** |
| 类型安全 | ❌ | ❌ | ✅ 完整类型提示 |
| 学习曲线 | 低 | 中 | 中 |
| 适合谁 | 多云 / 快速上手 | AWS 企业用户 | **TS 全栈开发者** |

> 💡 **如果你是 TypeScript 开发者，SST 是目前体验最好的选择**。用 TS 写配置有类型提示，Live Lambda Dev 让你像开发本地应用一样开发 Serverless——改代码不需要重新部署。

### 7.4 GitHub Actions 自动化部署流水线

框架解决了"怎么部署"，CI/CD 解决了"什么时候自动部署"——代码推到 main 分支自动部署生产，推到 PR 自动部署预览环境。

**AWS Lambda 的完整 CI/CD 流水线：**

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]           # 主分支推送 → 部署生产
  pull_request:
    branches: [main]           # PR → 部署预览环境

concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: true     # 同一分支的新推送取消旧部署

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run test

  deploy:
    needs: test                # 测试通过才部署
    runs-on: ubuntu-latest
    permissions:
      id-token: write          # OIDC 认证（不需要长期 AWS 密钥）
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci

      # 使用 OIDC 获取 AWS 临时凭证（比存 Access Key 更安全）
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ap-northeast-1

      # 根据分支决定部署环境
      - name: Deploy to staging (PR)
        if: github.event_name == 'pull_request'
        run: npx sst deploy --stage pr-${{ github.event.number }}

      - name: Deploy to production (main)
        if: github.ref == 'refs/heads/main'
        run: npx sst deploy --stage prod

      # PR 关闭时清理预览环境
  cleanup:
    if: github.event_name == 'pull_request' && github.event.action == 'closed'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ap-northeast-1
      - run: npx sst remove --stage pr-${{ github.event.number }}
```

**Vercel / Cloudflare 的零配置部署：**

如果你用 Vercel 或 Cloudflare Pages，CI/CD 几乎不需要配置：

```
Vercel 部署流程：
  1. GitHub 仓库连接到 Vercel
  2. 推送到 main → 自动部署生产
  3. 推送到 PR → 自动部署预览（每个 PR 一个独立 URL）
  4. 没了。不需要写 YAML。

Cloudflare Pages：
  1. GitHub 仓库连接到 Cloudflare Pages
  2. 配置构建命令：npm run build
  3. 推送自动部署
```

| 平台 | CI/CD 配置量 | Preview Deploy | 回滚 |
|:---|:---|:---|:---|
| Vercel | 零配置 | ✅ 每个 PR 自动部署 | 一键回滚到任意版本 |
| Cloudflare Pages | 极少配置 | ✅ 每个 PR 自动部署 | 一键回滚 |
| AWS (SAM/SST) | 需写 GitHub Actions | 需自行实现 | 重新部署旧版本 |

**CI/CD 最佳实践：**

```
✅ 用 OIDC 认证 AWS（不要在 GitHub Secrets 存 Access Key）
✅ PR 自动部署预览环境 + PR 关闭自动清理
✅ 生产部署前必须通过测试（needs: test）
✅ 用 concurrency 防止并发部署冲突
✅ 锁定依赖版本（npm ci 而不是 npm install）
❌ 不要在 CI 中硬编码环境变量——用 GitHub Secrets
```

> 💡 **对于个人项目或小团队**：直接用 Vercel / Cloudflare Pages 的零配置部署，省去写 CI/CD 的时间。只有当你需要 AWS 原生服务（Lambda + SQS + DynamoDB）时，才需要自己搭 GitHub Actions 流水线。

---

## 8. 可观测性与调试

Serverless 把运维交给了平台，但调试也变难了——没有服务器可以 SSH 上去看日志，函数分散在几十个 Lambda 里，一个请求可能经过 API Gateway → Lambda → SQS → Lambda → DynamoDB 多个环节。**你看不见的东西，就修不了。**

> 💡 **本章目标**：搭建完整的 Serverless 可观测性体系——日志、链路追踪、错误监控、性能分析，从"出了问题不知道哪里错"到"秒级定位根因"。

### 8.1 日志管理：CloudWatch / Vercel Logs / Axiom

**Serverless 日志的痛点：**

```
传统服务器：所有日志在一个地方（/var/log/app.log）
Serverless：
  → getUser 函数写到 /aws/lambda/my-api-dev-getUser
  → createUser 函数写到 /aws/lambda/my-api-dev-createUser
  → processQueue 函数写到 /aws/lambda/my-api-dev-processQueue
  → 每个函数一个日志组，每个实例一个日志流
  → 一个请求的日志可能分散在 3-5 个日志组里
```

**结构化日志（必须做！）：**

```ts
// ❌ 随意的 console.log（生产中几乎无法搜索）
console.log('用户创建成功');
console.log('错误:', error);

// ✅ 结构化日志（JSON 格式，可搜索、可聚合）
const logger = {
  info: (message: string, data?: object) =>
    console.log(JSON.stringify({ level: 'INFO', message, ...data, timestamp: Date.now() })),
  error: (message: string, error?: Error, data?: object) =>
    console.error(JSON.stringify({
      level: 'ERROR',
      message,
      error: error?.message,
      stack: error?.stack,
      ...data,
      timestamp: Date.now(),
    })),
};

// 使用
logger.info('用户创建成功', { userId: 'u_123', email: 'test@example.com' });
// → {"level":"INFO","message":"用户创建成功","userId":"u_123","email":"test@example.com","timestamp":1713000000}

logger.error('数据库查询失败', error, { query: 'SELECT * FROM users', duration: 1500 });
// → {"level":"ERROR","message":"数据库查询失败","error":"connection timeout","stack":"...","duration":1500}
```

**生产级日志中间件（推荐 powertools-lambda）：**

```ts
// 用 AWS Lambda Powertools 自动注入上下文信息
import { Logger } from '@aws-lambda-powertools/logger';

const logger = new Logger({
  serviceName: 'my-api',
  logLevel: 'INFO',
  persistentLogAttributes: {
    environment: process.env.STAGE,
  },
});

export const handler = async (event: any) => {
  // 自动附加 requestId、Lambda 上下文
  logger.addContext(context);

  logger.info('收到请求', { path: event.path, method: event.httpMethod });

  try {
    const result = await processRequest(event);
    logger.info('请求处理成功', { statusCode: 200 });
    return { statusCode: 200, body: JSON.stringify(result) };
  } catch (error) {
    logger.error('请求处理失败', error as Error);
    return { statusCode: 500, body: 'Internal Server Error' };
  }
};
```

**CloudWatch Logs Insights 查询（在海量日志中找到你要的）：**

```
# 查找所有错误日志
fields @timestamp, @message
| filter level = "ERROR"
| sort @timestamp desc
| limit 50

# 查找响应时间超过 3 秒的请求
fields @timestamp, message, duration
| filter duration > 3000
| sort duration desc

# 统计每小时错误率
fields @timestamp
| filter level = "ERROR"
| stats count() as errorCount by bin(1h)

# 查找特定用户的所有操作
fields @timestamp, @message
| filter userId = "u_123"
| sort @timestamp asc
```

**现代日志平台（更好的体验）：**

| 平台 | 优势 | 免费额度 |
|:---|:---|:---|
| **Axiom** | 无限留存、查询快、UI 好 | 500GB/月 |
| **Betterstack** | 漂亮的 Dashboard、告警 | 1GB/月 |
| **Vercel Logs** | Vercel 内置、零配置 | 1 小时留存（免费） |
| CloudWatch | AWS 原生、无需额外配置 | 5GB/月 |

> 💡 **推荐组合**：CloudWatch 作为基础日志（AWS 原生，Lambda 自动写入）+ Axiom 作为日志分析平台（免费额度大、查询体验好）。用 Lambda Extension 或 Subscription Filter 把 CloudWatch 日志转发到 Axiom。

### 8.2 分布式链路追踪：X-Ray / OpenTelemetry

日志告诉你"发生了什么"，链路追踪告诉你"请求经过了哪些服务、每一步花了多久"。

**分布式追踪的核心概念：**

```
一个用户请求的完整链路（Trace）：
┌─────────────────────────────────────────────────────────────┐
│ Trace ID: abc-123                                           │
│                                                             │
│ ├─ Span 1: API Gateway (2ms)                                │
│ │  └─ Span 2: Lambda getUser (45ms)                         │
│ │     ├─ Span 3: DynamoDB GetItem (12ms)                    │
│ │     ├─ Span 4: Redis GET cache (3ms)                      │
│ │     └─ Span 5: External API call (28ms)  ← 瓶颈在这里！    │
│ └─ 总耗时: 47ms                                              │
└─────────────────────────────────────────────────────────────┘

Trace = 一个完整请求的生命周期
Span  = Trace 中的一个操作步骤
```

**AWS X-Ray（最简单——一行配置启用）：**

```yaml
# serverless.yml — 全局启用 X-Ray
provider:
  tracing:
    apiGateway: true         # API Gateway 追踪
    lambda: true             # Lambda 追踪
```

```ts
// 自动追踪 AWS SDK 调用（DynamoDB、S3、SQS 等）
import { Tracer } from '@aws-lambda-powertools/tracer';

const tracer = new Tracer({ serviceName: 'my-api' });

// 自动捕获所有 AWS SDK 调用
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
const dynamodb = tracer.captureAWSv3Client(new DynamoDBClient({}));

export const handler = async (event: any) => {
  // 手动创建自定义 Span（追踪业务逻辑）
  const subsegment = tracer.getSegment()!.addNewSubsegment('processBusinessLogic');

  try {
    const result = await businessLogic();
    subsegment.addAnnotation('userId', event.userId);     // 可搜索的注解
    subsegment.addMetadata('result', result);              // 详细数据
    subsegment.close();
    return { statusCode: 200, body: JSON.stringify(result) };
  } catch (error) {
    subsegment.addError(error as Error);
    subsegment.close();
    throw error;
  }
};
```

**OpenTelemetry（跨平台方案）：**

如果你不只用 AWS，或者想用更通用的追踪方案，OpenTelemetry 是行业标准：

```ts
// otel-setup.ts — Lambda 中初始化 OpenTelemetry
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { trace } from '@opentelemetry/api';

const provider = new NodeTracerProvider();
provider.addSpanProcessor(
  new BatchSpanProcessor(
    new OTLPTraceExporter({
      url: process.env.OTEL_EXPORTER_ENDPOINT,  // Axiom / Honeycomb / Jaeger
    })
  )
);
provider.register();

const tracer = trace.getTracer('my-api');

// 在业务代码中使用
export async function getUser(userId: string) {
  return tracer.startActiveSpan('getUser', async (span) => {
    span.setAttribute('user.id', userId);

    const user = await db.query('SELECT * FROM users WHERE id = ?', [userId]);
    span.setAttribute('db.rowCount', user ? 1 : 0);

    span.end();
    return user;
  });
}
```

**X-Ray vs OpenTelemetry 选型：**

| 维度 | AWS X-Ray | OpenTelemetry |
|:---|:---|:---|
| 配置复杂度 | 极低（一行 YAML） | 中等（需要初始化） |
| AWS 集成 | 原生（自动追踪 SDK 调用） | 需要 instrumentation |
| 多云支持 | ❌ AWS only | ✅ 行业标准 |
| 后端选择 | 只能用 X-Ray Console | Axiom / Honeycomb / Jaeger / … |
| 成本 | 免费额度后按 Trace 计费 | 取决于后端 |

> 💡 **推荐策略**：AWS 项目先用 X-Ray（零配置启用一行搞定），等需要更灵活的分析时再迁移到 OpenTelemetry + Axiom/Honeycomb。

### 8.3 错误监控：Sentry 集成

日志和追踪是"事后查找"，错误监控是"实时告警"——生产环境出了异常，你应该在用户投诉之前就知道。

**Sentry + AWS Lambda 集成：**

```ts
// sentry.ts — 初始化 Sentry（放到 handler 外部，冷启动时执行一次）
import * as Sentry from '@sentry/aws-serverless';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.STAGE,
  tracesSampleRate: process.env.STAGE === 'prod' ? 0.1 : 1.0,  // 生产采样 10%
  beforeSend(event) {
    // 过滤掉不想上报的错误
    if (event.exception?.values?.[0]?.type === 'ValidationError') {
      return null;  // 参数校验错误不上报
    }
    return event;
  },
});

// 包装 handler（自动捕获未处理异常）
export const handler = Sentry.wrapHandler(async (event: any) => {
  // 添加用户上下文（错误关联到具体用户）
  Sentry.setUser({ id: event.userId, email: event.userEmail });

  // 添加自定义标签（用于过滤和搜索）
  Sentry.setTag('api.path', event.path);
  Sentry.setTag('api.method', event.httpMethod);

  try {
    const result = await processRequest(event);
    return { statusCode: 200, body: JSON.stringify(result) };
  } catch (error) {
    // 手动捕获并添加额外上下文
    Sentry.captureException(error, {
      extra: {
        requestBody: event.body,
        queryParams: event.queryStringParameters,
      },
    });

    return { statusCode: 500, body: 'Internal Server Error' };
  }
});
```

**Vercel / Next.js 集成（更简单）：**

```ts
// sentry.client.config.ts（Next.js + Sentry SDK 自动配置）
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.VERCEL_ENV,       // Vercel 自动注入环境变量
  integrations: [Sentry.replayIntegration()], // 录制用户操作回放
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,              // 出错时 100% 录制
});
```

**告警配置（不要让错误淹没在通知里）：**

```
Sentry 告警策略：
  ✅ 新错误类型首次出现 → 立即通知 Slack + 邮件
  ✅ 同一错误 1 小时内出现 > 100 次 → 高优先级告警
  ✅ 错误率超过 5% → P0 级别告警（可能需要回滚）
  ❌ 不要每个错误都通知——否则团队很快就会忽略所有通知
```

> 💡 **Sentry 的免费版（Developer Plan）**对个人项目完全够用：5000 次错误/月、1 个用户。生产项目建议 Team Plan（$26/月），支持更长留存期和更多功能。

### 8.4 性能分析：冷启动追踪、执行时间优化

知道函数跑了多久不够——你需要知道**为什么慢**、**哪里慢**、**冷启动占了多少**。

**Lambda 性能指标自动采集：**

每次 Lambda 执行，CloudWatch 自动记录这些指标：

```
REPORT RequestId: xxx
  Duration: 45.12 ms          ← 你的代码执行时间
  Billed Duration: 46 ms      ← 按 1ms 向上取整计费
  Memory Size: 256 MB          ← 配置的内存
  Max Memory Used: 89 MB       ← 实际使用的内存
  Init Duration: 234.56 ms     ← 冷启动时间（只在冷启动时出现！）
```

**自动识别冷启动：**

```ts
// 利用 Init Duration 是否存在来判断冷启动
import { Metrics, MetricUnit } from '@aws-lambda-powertools/metrics';

const metrics = new Metrics({ namespace: 'MyApp', serviceName: 'api' });

let isColdStart = true;  // 模块加载时为 true

export const handler = async (event: any) => {
  // 记录冷启动指标
  if (isColdStart) {
    metrics.addMetric('ColdStart', MetricUnit.Count, 1);
    isColdStart = false;   // 后续热启动不会再进来
  }

  const start = performance.now();

  // 业务逻辑 ...
  const result = await processRequest(event);

  // 记录执行时间
  const duration = performance.now() - start;
  metrics.addMetric('ProcessingTime', MetricUnit.Milliseconds, duration);
  metrics.publishStoredMetrics();

  return { statusCode: 200, body: JSON.stringify(result) };
};
```

**性能分析 Dashboard（CloudWatch 自定义面板）：**

```
关键监控指标：
┌──────────────────────────────────────────────────┐
│  冷启动率                                         │
│  ████░░░░░░░░░░ 12%  (过去 1 小时)               │
│  目标：< 5%                                       │
├──────────────────────────────────────────────────┤
│  P50 响应时间: 23ms  │  P99 响应时间: 450ms       │
│  目标：P99 < 500ms                                │
├──────────────────────────────────────────────────┤
│  错误率: 0.3%       │  节流(Throttle): 0          │
│  目标：< 1%                                       │
├──────────────────────────────────────────────────┤
│  并发实例数: 45/1000 │  内存利用率: 35%             │
└──────────────────────────────────────────────────┘
```

**定位慢请求的分析思路：**

```
P99 响应时间突然升高？按以下顺序排查：

1. 是不是冷启动导致的？
   → 查 Init Duration，看冷启动比例是否增加
   → 解决：Provisioned Concurrency 或减少依赖包

2. 是不是外部调用慢了？
   → 用 X-Ray Trace Map，找到耗时最长的 Span
   → 解决：加缓存、设超时、用异步队列替代同步调用

3. 是不是内存不够导致 GC 频繁？
   → 查 Max Memory Used 接近 Memory Size
   → 解决：增加内存配置（CPU 也会相应增加）

4. 是不是数据库连接慢？
   → 查数据库连接时间，是否每次都在建立新连接
   → 解决：复用连接（handler 外部初始化）、用 HTTP 数据库
```

**第 8 章可观测性体系总结：**

| 层次 | 工具 | 解决的问题 |
|:---|:---|:---|
| **日志** | CloudWatch + Axiom | 发生了什么？ |
| **追踪** | X-Ray / OpenTelemetry | 请求经过了哪些环节？哪里慢？ |
| **错误** | Sentry | 什么时候出了异常？影响了谁？ |
| **指标** | CloudWatch Metrics | 整体健康度怎么样？趋势如何？ |

> 💡 **可观测性不是"出了问题再加"**。从第一天就搭好结构化日志 + 错误监控，成本几乎为零（免费额度），但出问题时能救命。等生产事故发生才想起加日志，你已经错过了关键上下文。

---

## 9. 成本控制与生产最佳实践

"按需付费"听起来很美，但如果不注意优化，Serverless 的账单可能比你预期贵得多。反过来，精心设计的 Serverless 应用可以做到**个人项目几乎零成本、中等流量比传统服务器便宜 50-80%**。

> 💡 **本章目标**：算清楚 Serverless 的账单、掌握成本优化技巧、建立安全基线，最后给出"该不该用 Serverless"的决策框架。

### 9.1 定价模型详解：请求次数 × 执行时长 × 内存

**AWS Lambda 定价公式（最通用）：**

```
总费用 = 请求费用 + 计算费用

请求费用：
  $0.20 / 百万次请求
  免费额度：100 万次/月

计算费用：
  $0.0000166667 / GB·s（每 GB 内存每秒）
  免费额度：40 万 GB·s/月

实际算一笔账——一个中等流量的 API：
  每天 10 万次请求 × 30 天 = 300 万次/月
  每次请求执行 200ms，内存 256MB

  请求费用：(300万 - 100万免费) × $0.20 / 百万 = $0.40
  计算费用：300万 × 0.2秒 × 0.25GB = 15万 GB·s
           (15万 - 40万免费) = 免费额度内！

  月总费用 ≈ $0.40  ← 没看错，每月不到 1 美元！
```

**对比传统服务器（同等流量）：**

```
最便宜的 VPS（2核4G）：
  AWS EC2 t3.medium ≈ $30/月
  Vultr / DigitalOcean ≈ $24/月

Serverless vs 传统服务器成本对比：
┌─────────────────┬────────────┬────────────────┐
│ 月请求量         │ Lambda     │ EC2 t3.medium  │
├─────────────────┼────────────┼────────────────┤
│ 10 万次         │ $0（免费）  │ $30            │
│ 100 万次        │ $0（免费）  │ $30            │
│ 1000 万次       │ ~$5        │ $30            │
│ 1 亿次          │ ~$60       │ $30-60（需扩容）│
│ 10 亿次         │ ~$600      │ $300+（多台）   │
└─────────────────┴────────────┴────────────────┘

结论：
  < 5000 万次/月 → Serverless 更便宜
  > 1 亿次/月    → 传统服务器可能更划算（需要具体计算）
```

**各平台免费额度汇总：**

| 平台 | 免费额度 | 月成本（小项目） |
|:---|:---|:---|
| AWS Lambda | 100 万次 + 40 万 GB·s | $0 |
| Vercel | 10 万次函数执行 | $0（Hobby 免费） |
| Cloudflare Workers | 10 万次/天 (≈300 万/月) | $0 |
| 腾讯云 SCF | 100 万次 + 40 万 GB·s | ¥0 |

> 💡 **个人项目 / 副业产品的最优策略**：用 Cloudflare Workers（每日 10 万次免费）+ Neon（免费 PostgreSQL）+ R2（免费对象存储）。整套技术栈月费用 = $0。

### 9.2 成本优化策略：内存调优、执行时间控制、缓存层设计

知道了定价模型，就知道优化方向：**减少执行时间、选对内存配置、用缓存减少调用次数**。

**策略 1：内存调优（Lambda Power Tuning）**

```
费用 = 内存 × 时间
内存越大 → CPU 越快 → 执行时间越短

反直觉的结论：加内存可能反而省钱！

测试示例（某 API 函数）：
  128MB  × 3000ms = 384 MB·s  → $0.0064
  256MB  × 800ms  = 204 MB·s  → $0.0034  ← 省了 47%！
  512MB  × 400ms  = 204 MB·s  → $0.0034
  1024MB × 250ms  = 256 MB·s  → $0.0043

最优配置：256MB（性价比最高）
```

```bash
# 用 AWS Lambda Power Tuning 自动找最优配置
# 它会在 64MB-3008MB 范围内测试你的函数，给出成本/速度的帕累托最优解
# 开源工具：https://github.com/alexcasalboni/aws-lambda-power-tuning
```

**策略 2：缩短执行时间**

```ts
// ❌ 串行调用（总时间 = A + B + C）
const userInfo = await getUser(userId);         // 100ms
const orders = await getOrders(userId);          // 150ms
const notifications = await getNotifications();  // 80ms
// 总耗时：330ms

// ✅ 并行调用（总时间 = max(A, B, C)）
const [userInfo, orders, notifications] = await Promise.all([
  getUser(userId),          // 100ms
  getOrders(userId),        // 150ms
  getNotifications(),       // 80ms
]);
// 总耗时：150ms — 省了 55% 的时间和费用！
```

```ts
// ✅ 设置合理的超时（不要让失败的请求白白烧钱）
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 5000);  // 5 秒超时

try {
  const response = await fetch(externalApi, { signal: controller.signal });
  return await response.json();
} catch (error) {
  if (error.name === 'AbortError') {
    return { fallback: true, data: cachedData };  // 超时后返回缓存数据
  }
  throw error;
} finally {
  clearTimeout(timeout);
}
```

**策略 3：多级缓存（减少函数调用次数）**

```
请求 → CDN 缓存（命中 → 直接返回，不触发函数）
       ↓ 未命中
      Edge 缓存（Cloudflare Cache API）
       ↓ 未命中
      KV 缓存（Vercel KV / Cloudflare KV）
       ↓ 未命中
      函数执行 → 查数据库 → 写入缓存 → 返回

每一层缓存都能减少后续环节的调用次数：
  CDN 命中率 80% → 只有 20% 的请求触发函数
  KV 缓存命中率 90% → 只有 2% 的请求真正查数据库
```

```ts
// Edge 缓存示例（Cloudflare Workers）
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const cacheKey = new Request(request.url, request);
    const cache = caches.default;

    // 先查缓存
    let response = await cache.match(cacheKey);
    if (response) return response;

    // 缓存未命中 → 执行业务逻辑
    response = await handleRequest(request, env);

    // 写入缓存（后台异步，不阻塞响应）
    const cachedResponse = new Response(response.body, response);
    cachedResponse.headers.set('Cache-Control', 'public, max-age=300');
    ctx.waitUntil(cache.put(cacheKey, cachedResponse.clone()));

    return response;
  },
};
```

**策略 4：账单监控告警**

```
必须配置的告警：
  ✅ Lambda 月费用超过 $10 → 邮件通知
  ✅ 单日 Lambda 调用次数异常增长 → Slack 告警
  ✅ AWS Budget 设置月预算上限 $50

AWS Budget 配置（控制台）：
  Billing → Budgets → Create Budget → $50/月 → 邮件告警
```

> 💡 **成本优化的 80/20 法则**：并行化外部调用 + 加一层缓存，就能解决 80% 的成本问题。内存调优是锦上添花。不要过早优化，先上线再看账单。

### 9.3 安全最佳实践：最小权限、环境变量、API Key 管理

Serverless 减少了运维，但安全责任没有减少。函数暴露在公网上，每一个 API 端点都是攻击面。

**IAM 最小权限原则：**

```yaml
# ❌ 危险：给 Lambda 全部权限
provider:
  iam:
    role:
      statements:
        - Effect: Allow
          Action: '*'                   # 这个函数可以做任何事！
          Resource: '*'

# ✅ 安全：只给需要的权限
functions:
  getUser:
    handler: users.get
    iamRoleStatements:                  # 每个函数独立权限
      - Effect: Allow
        Action:
          - dynamodb:GetItem            # 只能读，不能写
          - dynamodb:Query
        Resource:
          - !GetAtt UsersTable.Arn      # 只能访问 Users 表

  deleteUser:
    handler: users.delete
    iamRoleStatements:
      - Effect: Allow
        Action:
          - dynamodb:DeleteItem         # 只有删除函数才有删除权限
        Resource:
          - !GetAtt UsersTable.Arn
```

**环境变量与密钥管理：**

```
❌ 绝对不能做的事：
  • 把 API Key 写死在代码里
  • 把密钥提交到 Git 仓库
  • 在 console.log 里打印密钥

✅ 正确的做法：
  • 用环境变量传递配置
  • 敏感密钥存 AWS Secrets Manager / SSM Parameter Store
  • 用 .env.local 本地开发，.gitignore 排除
```

```ts
// 从 Secrets Manager 获取密钥（Lambda）
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

const client = new SecretsManagerClient({});

// 冷启动时加载一次，后续复用
let cachedSecrets: Record<string, string> | null = null;

async function getSecrets() {
  if (cachedSecrets) return cachedSecrets;

  const { SecretString } = await client.send(
    new GetSecretValueCommand({ SecretId: 'my-app/prod/api-keys' })
  );
  cachedSecrets = JSON.parse(SecretString!);
  return cachedSecrets;
}

export const handler = async (event: any) => {
  const secrets = await getSecrets();
  const stripeKey = secrets.STRIPE_SECRET_KEY;
  // 使用密钥 ...
};
```

**API 安全防护：**

```ts
// 安全中间件示例（Hono）
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { secureHeaders } from 'hono/secure-headers';

const app = new Hono();

// 1. CORS — 限制来源域名
app.use('/api/*', cors({
  origin: ['https://myapp.com', 'https://staging.myapp.com'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE'],
}));

// 2. 安全响应头
app.use('*', secureHeaders());

// 3. 输入校验（防注入）
app.post('/api/users', async (c) => {
  const body = await c.req.json();

  // 用 Zod 做严格类型校验
  const schema = z.object({
    name: z.string().min(1).max(100),
    email: z.string().email(),
    age: z.number().int().min(0).max(150).optional(),
  });

  const result = schema.safeParse(body);
  if (!result.success) {
    return c.json({ error: result.error.issues }, 400);
  }

  // result.data 是经过校验的安全数据
  const user = await createUser(result.data);
  return c.json(user, 201);
});
```

**Serverless 安全检查清单：**

```
✅ 每个函数独立 IAM 角色（最小权限）
✅ 密钥存 Secrets Manager，不用环境变量存高敏感信息
✅ API 端点配置 CORS（限制来源域名）
✅ 所有输入做严格校验（Zod / Joi）
✅ 设置函数超时和内存上限（防止资源滥用）
✅ 启用 API Gateway 限流（防 DDoS）
✅ 日志中不打印敏感信息（密码、Token、信用卡号）
✅ 使用 HTTPS（所有平台默认启用）
✅ 定期轮换密钥（Secrets Manager 支持自动轮换）
```

> 💡 **安全不是可选项**。Serverless 函数直接暴露在公网上，任何人都可以调用。必须假设所有输入都是恶意的——校验每一个参数，限制每一个权限。

### 9.4 何时不该用 Serverless？架构决策指南

Serverless 不是银弹。有些场景用 Serverless 是在给自己找麻烦——知道什么时候**不该用**，比知道什么时候该用更重要。

**❌ 不适合 Serverless 的场景：**

| 场景 | 原因 | 替代方案 |
|:---|:---|:---|
| 长时间运行的任务（>15 分钟） | Lambda 有执行时间限制 | ECS Fargate / 云主机 |
| WebSocket 长连接 | 函数按执行时间计费，连接一小时成本爆炸 | 独立 WebSocket 服务 / Durable Objects |
| 高频率的批量计算 | 函数启动开销 × 百万次 = 大量浪费 | 容器批处理 / Spark |
| 需要 GPU 计算 | Lambda 不支持 GPU | GPU 云实例 / Modal |
| 对延迟极敏感（<10ms） | 冷启动无法完全消除 | 常驻进程服务 |
| 稳定高流量（7×24 满载） | 按量付费反而更贵 | 预留实例 / 容器 |
| 大量本地文件操作 | 函数只有 /tmp 512MB | EFS 挂载 / 容器 |

**架构决策流程图：**

```
你的工作负载是什么模式？

  间歇性 / 突发性流量？
    ├── 是 → ✅ Serverless（按需扩缩，空闲零成本）
    └── 否 → 继续判断 ↓

  7×24 稳定高流量（>80% 利用率）？
    ├── 是 → ❌ 容器 / 云主机（固定成本更低）
    └── 否 → 继续判断 ↓

  执行时间 > 15 分钟？
    ├── 是 → ❌ 容器（ECS Fargate / Cloud Run）
    └── 否 → 继续判断 ↓

  需要 GPU / 特殊硬件？
    ├── 是 → ❌ GPU 实例（Modal / RunPod）
    └── 否 → ✅ Serverless 是好选择！
```

**混合架构——最佳实践：**

很多生产系统不是纯 Serverless，而是混合架构：

```
典型的混合架构：
  ┌─────────────────────────┐
  │  Edge Functions          │ ← 鉴权、路由、A/B 测试（Serverless）
  ├─────────────────────────┤
  │  API Functions           │ ← CRUD 业务逻辑（Serverless）
  ├─────────────────────────┤
  │  WebSocket Server        │ ← 实时推送（容器长驻）
  ├─────────────────────────┤
  │  Background Workers      │ ← 视频转码、ML 推理（容器/GPU）
  ├─────────────────────────┤
  │  Cron Jobs               │ ← 定时任务（Serverless）
  └─────────────────────────┘

原则：能用 Serverless 的部分全用 Serverless，
     不适合的部分用最轻量的容器方案（Fargate / Cloud Run）。
```

**全书回顾——从 0 到生产的 Serverless 之路：**

```
第 1 章：理解范式转变 ←── 思维从"管理服务器"转为"只写业务代码"
第 2 章：第一个函数    ←── 三个平台的 Hello World
第 3 章：事件驱动      ←── HTTP / Cron / 消息队列 / 存储事件 / DB 变更
第 4 章：冷启动优化    ←── 对比运行时、优化策略、Edge Functions
第 5 章：实战模式      ←── API / Webhook / 图片处理 / 批处理 / AI 推理
第 6 章：数据持久化    ←── 连接池问题 / Neon / KV 存储 / 对象存储
第 7 章：部署 CI/CD    ←── Serverless Framework / SAM / SST / GitHub Actions
第 8 章：可观测性      ←── 日志 / 追踪 / 错误监控 / 性能分析
第 9 章：成本与安全    ←── 定价计算 / 优化策略 / 安全基线 / 决策指南
```

> 💡 **最后一条建议**：不要一开始就追求完美架构。用 Vercel + Neon + R2 快速上线你的想法，等流量来了再优化。Serverless 最大的价值不是技术先进，而是**让你把时间花在业务上，而不是运维上**。

