# Supabase 权威指南

> 开源的 Firebase 替代品——用 PostgreSQL 的力量，构建现代全栈应用。

---

## 一、Supabase 是什么

### 1. 定义与定位

#### 一句话定义

**Supabase 是一个开源的 Firebase 替代品**，基于 PostgreSQL 构建，为开发者提供数据库、认证、实时订阅、文件存储、边缘函数等全套后端能力——让你不需要从零搭建后端，就能快速构建现代全栈应用。

#### 什么是 "Backend as a Service"（BaaS）

在传统开发中，构建一个完整的应用需要大量后端工作：

```
 传统方式：自己搭建所有后端基础设施
 ═══════════════════════════════════════════════════

 你的应用
   ↓
 ┌─────────────────────────────────────────────────┐
 │  需要自己搞定的事情：                              │
 │                                                 │
 │  ☐ 选数据库（MySQL? PostgreSQL? MongoDB?）       │
 │  ☐ 搭 API 服务器（Express? Django? Spring?）     │
 │  ☐ 实现用户注册登录（密码加密、JWT、OAuth…）      │
 │  ☐ 实现文件上传下载（S3? 本地存储?）              │
 │  ☐ 实现实时功能（WebSocket 服务器）               │
 │  ☐ 部署运维（Docker、K8s、SSL 证书、监控…）       │
 │  ☐ 安全防护（SQL 注入、XSS、CSRF…）               │
 │                                                 │
 │  💀 光是这些就要忙好几周，还没开始写业务逻辑       │
 └─────────────────────────────────────────────────┘
```

BaaS（Backend as a Service）的思路是：**把这些通用的后端能力做成现成的服务，开发者直接调用 API 就行。**

```
 BaaS 方式：后端即服务
 ═══════════════════════════════════════════════════

 你的应用（只需要写前端 + 业务逻辑）
   ↓
 ┌─────────────────────────────────────────────────┐
 │  Supabase 帮你搞定的事情：                        │
 │                                                 │
 │  ✅ 数据库       → PostgreSQL，自动生成 REST API  │
 │  ✅ 用户认证     → 邮箱/OAuth/手机号，开箱即用     │
 │  ✅ 文件存储     → S3 兼容，自带 CDN               │
 │  ✅ 实时订阅     → 数据变更实时推送到客户端         │
 │  ✅ 边缘函数     → 自定义后端逻辑（Deno 运行时）   │
 │  ✅ 安全策略     → 行级安全（RLS）在数据库层面保护  │
 │                                                 │
 │  🚀 几分钟就能搭好后端，专注于你的产品             │
 └─────────────────────────────────────────────────┘
```

#### "开源 Firebase 替代品"是什么意思？

**Firebase** 是 Google 推出的 BaaS 平台，是这个领域的标杆产品。Supabase 瞄准的正是同一个市场，但走了一条完全不同的技术路线：

| 对比维度 | Firebase | Supabase |
| :--- | :--- | :--- |
| **开源性** | ❌ 闭源，Google 专有 | ✅ 完全开源（MIT 协议） |
| **数据库** | Firestore / Realtime DB（**NoSQL**） | **PostgreSQL**（关系型数据库） |
| **查询能力** | 受限的查询语法，不支持 JOIN | 完整 SQL 支持，JOIN / 子查询 / 窗口函数 |
| **数据模型** | 文档模型（嵌套 JSON） | 表 + 行 + 列（可使用 JSON 类型补充） |
| **数据迁移** | 困难，厂商锁定严重 | 标准 PostgreSQL，随时可迁出 |
| **自托管** | ❌ 不支持 | ✅ Docker 一键部署 |
| **定价** | 按读写次数计费（可能昂贵） | 按资源用量计费（更可预测） |

核心区别在于**数据库选择**：

```
 Firebase: 文档型数据库（NoSQL）
 ═══════════════════════════════

 users/
   ├── user_001/
   │     ├── name: "张三"
   │     ├── email: "zhang@test.com"
   │     └── orders/              ← 嵌套子集合
   │           ├── order_001/
   │           │     ├── product: "iPhone"
   │           │     └── price: 9999
   │           └── order_002/
   │                 └── ...
   └── user_002/
         └── ...

 ⚠️ 无法直接 JOIN
 ⚠️ 查询"所有价格超过 5000 的订单"很痛苦
 ⚠️ 数据一致性需要自己维护


 Supabase: 关系型数据库（PostgreSQL）
 ═══════════════════════════════

 users 表                          orders 表
 ┌────────┬──────┬──────────────┐  ┌────────┬─────────┬────────┬───────┐
 │ id     │ name │ email        │  │ id     │ user_id │ product│ price │
 ├────────┼──────┼──────────────┤  ├────────┼─────────┼────────┼───────┤
 │ 001    │ 张三 │ zhang@test   │  │ 001    │ 001     │ iPhone │ 9999  │
 │ 002    │ 李四 │ li@test      │  │ 002    │ 001     │ iPad   │ 5999  │
 └────────┴──────┴──────────────┘  │ 003    │ 002     │ Mac    │ 12999 │
                                   └────────┴─────────┴────────┴───────┘

 ✅ SELECT * FROM orders JOIN users ON orders.user_id = users.id
 ✅ SELECT * FROM orders WHERE price > 5000
 ✅ 外键约束保证数据一致性
```

> 💡 **一句话总结 Supabase 的定位**：
>
> Supabase = **PostgreSQL 的强大** + **Firebase 的易用** + **开源的自由**。它让你用熟悉的 SQL 和关系型思维，享受"后端即服务"的开发效率。

### 2. 为什么选择 Supabase

市面上 BaaS 产品不少，为什么 Supabase 在短短几年内成了最受欢迎的选择之一？

#### ① 开源 = 没有厂商锁定

这是 Supabase 最大的差异化优势。

```
 使用 Firebase                      使用 Supabase
 ═══════════════════════             ═══════════════════════

 数据存在 Google 的私有格式中        数据存在标准 PostgreSQL 中
       ↓                                   ↓
 想迁走？没有标准导出工具             想迁走？pg_dump 一行命令
 需要重写所有查询逻辑                 换个 PostgreSQL 托管商即可
 被 Google 定价绑死                   自托管 = 零平台费用
       ↓                                   ↓
 🔒 锁定                             🔓 自由
```

Supabase 的核心是**开源项目组合**，你可以：
- 在 Supabase Cloud 上使用（最方便）
- 用 Docker Compose 自托管在自己的服务器上（完全免费）
- 只使用其中某些组件（比如只用 GoTrue 做认证）

#### ② PostgreSQL = 站在巨人的肩膀上

PostgreSQL 是世界上最先进的开源关系型数据库，拥有 35+ 年的历史：

| PostgreSQL 能力 | 在 Supabase 中的体现 |
| :--- | :--- |
| 完整 SQL 支持 | 复杂查询、JOIN、子查询、CTE 窗口函数 |
| JSONB 数据类型 | 需要时也能存非结构化数据 |
| 全文搜索 | 内置搜索引擎，不需要 Elasticsearch |
| 扩展生态 | PostGIS（地理）、pgvector（AI 向量）、pg_cron（定时任务） |
| 行级安全（RLS） | 数据库层面的访问控制 |
| 外键 + 约束 | 数据一致性的硬保障 |

选择 PostgreSQL 意味着你的技能可迁移——不管以后是否继续用 Supabase，SQL 技能永远通用。

#### ③ 开箱即用的全家桶

不需要东拼西凑，Supabase 一站式解决：

```
 以前：自己组装技术栈               现在：Supabase 全包
 ═══════════════════════            ═══════════════════════

 数据库  → 自建 PostgreSQL           数据库  → ✅ 内置
 API     → 自建 Express/Django       API     → ✅ 自动生成
 认证    → 接入 Auth0 / Passport     认证    → ✅ 内置
 存储    → 接入 AWS S3               存储    → ✅ 内置
 实时    → 自建 WebSocket 服务       实时    → ✅ 内置
 函数    → 部署 AWS Lambda           函数    → ✅ 内置
 管理面板 → 自建 Admin Dashboard     管理面板 → ✅ 内置

 6+ 个独立服务需要维护               1 个平台全搞定
```

#### ④ 适合谁？

| 人群 | 为什么适合 |
| :--- | :--- |
| **独立开发者** | 一个人撑起整个后端，快速构建 MVP |
| **初创团队** | 不需要后端工程师就能起步，等业务跑起来再招人 |
| **全栈开发者** | 前端开发者的最佳拍档，用 SQL 的方式操作后端 |
| **Hackathon 参赛者** | 几小时内搭建完整的全栈应用 |
| **学习者** | 学到的是 PostgreSQL + SQL，而不是某个厂商的私有 API |

### 3. 架构总览

Supabase 不是一个单一的产品，而是一组**精心编排的开源工具**，每个组件负责一部分能力：

```
                        ┌──────────────────────────────────┐
                        │        Supabase Dashboard         │
                        │     （Web 管理面板，可视化操作）     │
                        └───────────────┬──────────────────┘
                                        │
                        ┌───────────────┴──────────────────┐
                        │         Kong API Gateway          │
                        │   （统一入口，路由 + 鉴权 + 限流）  │
                        └──┬─────┬──────┬──────┬──────┬────┘
                           │     │      │      │      │
              ┌────────────┘     │      │      │      └────────────┐
              ▼                  ▼      │      ▼                   ▼
     ┌──────────────┐  ┌────────────┐  │  ┌──────────┐  ┌──────────────┐
     │  PostgREST   │  │  GoTrue    │  │  │ Storage  │  │Edge Functions│
     │              │  │            │  │  │  API     │  │              │
     │ PostgreSQL   │  │  认证引擎   │  │  │ 文件存储 │  │  Deno 运行时  │
     │ → REST API   │  │ 邮箱/OAuth │  │  │ S3 兼容  │  │  自定义逻辑   │
     │ 自动映射      │  │ JWT 签发   │  │  │ 图片变换 │  │  Webhook     │
     └──────┬───────┘  └─────┬──────┘  │  └────┬─────┘  └──────┬───────┘
            │                │         │       │               │
            └────────────────┴────┬────┘───────┘               │
                                  │                            │
                        ┌─────────┴──────────┐                 │
                        │    PostgreSQL       │◀────────────────┘
                        │                    │
                        │  · 数据存储         │
                        │  · RLS 安全策略     │
                        │  · 函数 + 触发器    │
                        │  · 实时变更流       │
                        └─────────┬──────────┘
                                  │
                        ┌─────────┴──────────┐
                        │  Realtime Server   │
                        │  （Phoenix/Elixir） │
                        │                    │
                        │  · WebSocket 连接   │
                        │  · 数据库变更推送   │
                        │  · 广播 + 在线状态  │
                        └────────────────────┘
```

#### 各组件职责速查

| 组件 | 技术 | 职责 |
| :--- | :--- | :--- |
| **PostgreSQL** | PostgreSQL 15+ | 核心数据库，所有数据的最终归宿 |
| **PostgREST** | Haskell | 将 PostgreSQL 表自动映射为 RESTful API，无需手写接口 |
| **GoTrue** | Go | 认证引擎，处理注册、登录、OAuth，签发 JWT |
| **Realtime** | Elixir / Phoenix | 监听数据库变更，通过 WebSocket 实时推送给客户端 |
| **Storage API** | Node.js | 文件存储服务，S3 兼容，支持图片变换 |
| **Edge Functions** | Deno | 运行自定义后端逻辑，部署在边缘网络 |
| **Kong** | Lua / Nginx | API 网关，统一入口，处理路由、限流、鉴权 |
| **Dashboard** | Next.js | Web 管理面板，可视化操作数据库、用户、存储等 |

#### 请求链路示例

一个典型的数据查询请求是这样走的：

```
 前端代码
 const { data } = await supabase.from('todos').select('*')
       │
       ▼
 ① Supabase JS 客户端将请求构造为：
    GET https://xxx.supabase.co/rest/v1/todos
    Headers: Authorization: Bearer <JWT>
       │
       ▼
 ② Kong API Gateway 接收请求
    → 验证 API Key
    → 路由到 PostgREST 服务
       │
       ▼
 ③ PostgREST 解析请求
    → 将 REST 请求转换为 SQL: SELECT * FROM todos
    → 携带 JWT 中的用户信息执行查询
       │
       ▼
 ④ PostgreSQL 执行查询
    → 检查 RLS 策略：当前用户能看哪些行？
    → 过滤数据，只返回有权限的行
       │
       ▼
 ⑤ 结果原路返回 → JSON 格式 → 前端拿到数据
```

> 🔑 **关键洞察**：
>
> 注意到了吗？**你不需要写任何后端代码**——PostgREST 自动将数据库表映射为 API，RLS 在数据库层面处理权限。这就是 Supabase "无后端"开发体验的本质。

---

## 二、快速上手

### 1. 创建项目

#### 第一步：注册 Supabase 账号

访问 [supabase.com](https://supabase.com)，点击 "Start your project"。支持以下方式注册：

- **GitHub 账号**（推荐，一键登录）
- 邮箱 + 密码

注册后会进入 Dashboard，这就是你管理所有 Supabase 项目的主界面。

#### 第二步：新建项目

点击 "New Project"，需要填写以下配置：

| 配置项 | 说明 | 建议 |
| :--- | :--- | :--- |
| **Organization** | 项目所属组织（自动创建了一个） | 默认即可 |
| **Project Name** | 项目名称 | 取一个有意义的名字，如 `my-todo-app` |
| **Database Password** | 数据库密码 | 务必记住！后续直连数据库时需要 |
| **Region** | 数据中心区域 | 选离你用户最近的（东亚可选 `Northeast Asia (Tokyo)`） |
| **Pricing Plan** | 定价方案 | Free 免费版足够学习和小项目使用 |

```
 ┌─────────────────────────────────────────────┐
 │             Create a new project             │
 ├─────────────────────────────────────────────┤
 │                                             │
 │  Organization:  [ Personal          ▾]      │
 │                                             │
 │  Project name:  [ my-todo-app        ]      │
 │                                             │
 │  Database Password:                         │
 │  [ •••••••••••••••••  ] [Generate]          │
 │  ⚠️ 请保存好这个密码，之后无法找回            │
 │                                             │
 │  Region:  [ Northeast Asia (Tokyo)  ▾]      │
 │                                             │
 │  Pricing Plan:  ○ Free  ● Pro  ○ Team       │
 │                                             │
 │          [ Create new project ]              │
 └─────────────────────────────────────────────┘
```

点击创建后，Supabase 会花约 1~2 分钟初始化你的 PostgreSQL 实例和所有配套服务。

#### 第三步：认识 Dashboard

项目创建完成后，你会看到 Supabase 的管理面板。左侧导航栏对应了 Supabase 的核心功能模块：

```
 ┌──────────────────┬─────────────────────────────────────────┐
 │  📊 Home         │                                         │
 │                  │   Welcome to your project!               │
 │  📋 Table Editor │                                         │
 │     可视化管理表   │   Project URL:                           │
 │                  │   https://xxxx.supabase.co               │
 │  🔍 SQL Editor   │                                         │
 │     直接写 SQL    │   API Key (anon):                        │
 │                  │   eyJhbGciOiJIUzI1NiIs...                │
 │  🔐 Authentication│                                        │
 │     用户管理      │   API Key (service_role):                │
 │                  │   eyJhbGciOiJIUzI1NiIs...                │
 │  📦 Storage      │                                         │
 │     文件存储      │   ┌─────────────────────────────┐       │
 │                  │   │  Getting Started              │       │
 │  ⚡ Edge Functions│   │                               │       │
 │     无服务器函数   │   │  1. Create a table            │       │
 │                  │   │  2. Insert some data          │       │
 │  📊 Reports      │   │  3. Read data from client     │       │
 │     用量报告      │   └─────────────────────────────┘       │
 │                  │                                         │
 │  ⚙️ Settings     │                                         │
 │     项目设置      │                                         │
 └──────────────────┴─────────────────────────────────────────┘
```

> 💡 **免费版限制速览**：
>
> | 资源 | 免费额度 |
> | :--- | :--- |
> | 数据库大小 | 500 MB |
> | 文件存储 | 1 GB |
> | 带宽 | 5 GB / 月 |
> | 边缘函数调用 | 500K 次 / 月 |
> | 项目数量 | 2 个活跃项目 |
> | 暂停策略 | 7 天无活动后自动暂停（免费版） |
>
> 对于学习和个人项目完全够用。

### 2. 连接到你的应用

#### 获取连接信息

在 Dashboard 的 **Settings → API** 页面，你能找到两个关键信息：

| 信息 | 说明 |
| :--- | :--- |
| **Project URL** | 你的 Supabase API 地址，如 `https://xxxx.supabase.co` |
| **anon (public) key** | 匿名公钥，可安全暴露在前端代码中 |
| **service_role key** | 服务端密钥，**绝对不能暴露在前端**，拥有绕过 RLS 的完全权限 |

> ⚠️ **两个 Key 的区别至关重要**：
>
> ```
> anon key（公钥）                    service_role key（私钥）
> ═══════════════════════             ═══════════════════════
>
> ✅ 可以放在前端代码中                ❌ 只能在服务端使用
> ✅ 受 RLS 策略约束                  ❌ 绕过所有 RLS 策略
> ✅ 只能访问 RLS 允许的数据           ❌ 可以访问所有数据
>
> 类比：普通员工的门禁卡               类比：大楼管理员的万能钥匙
> ```

#### 安装客户端库

Supabase 提供多语言 SDK：

**JavaScript / TypeScript（最常用）**

```bash
npm install @supabase/supabase-js
```

**Python**

```bash
pip install supabase
```

**Flutter（Dart）**

```bash
flutter pub add supabase_flutter
```

**Swift（iOS）**

```swift
// Package.swift 添加依赖
.package(url: "https://github.com/supabase/supabase-swift.git", from: "2.0.0")
```

#### 初始化客户端

**JavaScript / TypeScript**

```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://xxxx.supabase.co'   // 替换为你的 Project URL
const supabaseKey = 'eyJhbGciOiJIUzI1NiIs...'    // 替换为你的 anon key

const supabase = createClient(supabaseUrl, supabaseKey)
```

**Python**

```python
from supabase import create_client

url = "https://xxxx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIs..."

supabase = create_client(url, key)
```

就这么简单——两行配置，客户端就准备好了。接下来可以直接操作数据库了。

### 3. 第一个 CRUD：5 分钟上手

让我们从零创建一个待办事项（Todo）的完整增删改查。

#### 第一步：在 Dashboard 中创建表

进入 **Table Editor → New Table**，创建 `todos` 表：

```
 表名：todos
 ┌──────────────┬───────────┬───────────┬──────────────────────────┐
 │  列名         │ 类型       │ 默认值     │ 说明                      │
 ├──────────────┼───────────┼───────────┼──────────────────────────┤
 │ id           │ int8      │ 自动生成   │ 主键，自增                 │
 │ created_at   │ timestamptz│ now()     │ 创建时间                  │
 │ title        │ text      │ -         │ 待办事项标题               │
 │ is_complete  │ bool      │ false     │ 是否完成                   │
 │ user_id      │ uuid      │ auth.uid()│ 用户 ID（关联认证系统）     │
 └──────────────┴───────────┴───────────┴──────────────────────────┘
```

或者用 SQL Editor 执行：

```sql
CREATE TABLE todos (
  id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now(),
  title TEXT NOT NULL,
  is_complete BOOLEAN DEFAULT false,
  user_id UUID DEFAULT auth.uid()
);

-- 启用行级安全
ALTER TABLE todos ENABLE ROW LEVEL SECURITY;

-- 创建策略：用户只能操作自己的 todo
CREATE POLICY "用户可以查看自己的 todo" ON todos
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "用户可以创建自己的 todo" ON todos
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "用户可以更新自己的 todo" ON todos
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "用户可以删除自己的 todo" ON todos
  FOR DELETE USING (auth.uid() = user_id);
```

#### 第二步：用客户端操作数据

**📌 创建（Insert）**

```javascript
const { data, error } = await supabase
  .from('todos')
  .insert({ title: '学习 Supabase', is_complete: false })
  .select()   // 返回插入的数据

console.log(data)
// [{ id: 1, title: '学习 Supabase', is_complete: false, ... }]
```

**📌 查询（Select）**

```javascript
// 查询所有 todo
const { data } = await supabase
  .from('todos')
  .select('*')

// 带条件查询：只查未完成的
const { data: pending } = await supabase
  .from('todos')
  .select('*')
  .eq('is_complete', false)     // WHERE is_complete = false
  .order('created_at', { ascending: false })  // ORDER BY created_at DESC
```

**📌 更新（Update）**

```javascript
const { data, error } = await supabase
  .from('todos')
  .update({ is_complete: true })
  .eq('id', 1)     // WHERE id = 1
  .select()
```

**📌 删除（Delete）**

```javascript
const { error } = await supabase
  .from('todos')
  .delete()
  .eq('id', 1)     // WHERE id = 1
```

#### 第三步：完整 React 示例

把上面的操作整合到一个 React 组件中：

```jsx
import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://xxxx.supabase.co', 'your-anon-key')

function TodoApp() {
  const [todos, setTodos] = useState([])
  const [newTitle, setNewTitle] = useState('')

  // 加载 todos
  useEffect(() => {
    fetchTodos()
  }, [])

  async function fetchTodos() {
    const { data } = await supabase
      .from('todos')
      .select('*')
      .order('created_at', { ascending: false })
    setTodos(data || [])
  }

  // 添加 todo
  async function addTodo() {
    if (!newTitle.trim()) return
    const { error } = await supabase
      .from('todos')
      .insert({ title: newTitle })
    if (!error) {
      setNewTitle('')
      fetchTodos()  // 重新加载
    }
  }

  // 切换完成状态
  async function toggleTodo(id, currentStatus) {
    await supabase
      .from('todos')
      .update({ is_complete: !currentStatus })
      .eq('id', id)
    fetchTodos()
  }

  // 删除 todo
  async function deleteTodo(id) {
    await supabase.from('todos').delete().eq('id', id)
    fetchTodos()
  }

  return (
    <div>
      <h1>My Todos</h1>
      <input
        value={newTitle}
        onChange={e => setNewTitle(e.target.value)}
        placeholder="添加新待办..."
        onKeyDown={e => e.key === 'Enter' && addTodo()}
      />
      <button onClick={addTodo}>添加</button>

      <ul>
        {todos.map(todo => (
          <li key={todo.id}>
            <input
              type="checkbox"
              checked={todo.is_complete}
              onChange={() => toggleTodo(todo.id, todo.is_complete)}
            />
            <span style={{
              textDecoration: todo.is_complete ? 'line-through' : 'none'
            }}>
              {todo.title}
            </span>
            <button onClick={() => deleteTodo(todo.id)}>删除</button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default TodoApp
```

> 🚀 **注意看——整个应用没有写一行后端代码！** 前端直接通过 Supabase JS 客户端操作数据库，RLS 策略在数据库层面保证了安全性。这就是 Supabase 的开发体验。

---

## 三、数据库（Database）

### 1. PostgreSQL 基础

#### 为什么是 PostgreSQL？

Supabase 选择 PostgreSQL 作为核心，不是因为它"够用"，而是因为它**最强**：

```
 数据库对比
 ═══════════════════════════════════════════════════

 MySQL         → 最流行，但功能相对基础
 SQLite        → 轻量，但不适合并发和生产环境
 MongoDB       → 灵活，但缺乏数据一致性保障
 PostgreSQL    → 功能最全，扩展性最强，社区最活跃
                  ↓
                  Supabase 的选择 ✅
```

PostgreSQL 的关键优势：
- **ACID 事务**：数据一致性的硬保障
- **JSONB 类型**：需要时也能像 MongoDB 一样存文档
- **扩展生态**：pgvector（AI 向量搜索）、PostGIS（地理位置）、pg_cron（定时任务）
- **行级安全（RLS）**：Supabase 安全模型的基石
- **35+ 年历史**：久经考验，企业级稳定性

#### 表、列与数据类型

PostgreSQL 中，数据按**表（Table）→ 行（Row）→ 列（Column）** 的结构组织：

```
 表：users
 ┌─────────┬──────────┬──────────────────┬─────────────────────┐
 │ id (int)│name(text)│ email (text)     │ created_at (timestamptz)│
 ├─────────┼──────────┼──────────────────┼─────────────────────┤
 │ 1       │ 张三     │ zhang@test.com   │ 2025-01-15 10:30:00 │  ← 行
 │ 2       │ 李四     │ li@test.com      │ 2025-01-16 14:20:00 │  ← 行
 │ 3       │ 王五     │ wang@test.com    │ 2025-01-17 09:00:00 │  ← 行
 └─────────┴──────────┴──────────────────┴─────────────────────┘
   ↑ 列       ↑ 列        ↑ 列                ↑ 列
```

Supabase 中最常用的数据类型：

| 类型 | 说明 | 示例 |
| :--- | :--- | :--- |
| `int4` / `int8` | 整数（4字节 / 8字节） | `id`, `age`, `count` |
| `text` | 不限长度的文本 | `name`, `description` |
| `varchar(n)` | 限定长度的文本 | `email`, `phone` |
| `bool` | 布尔值 | `is_active`, `is_complete` |
| `timestamptz` | 带时区的时间戳 | `created_at`, `updated_at` |
| `uuid` | 通用唯一标识符 | `user_id`（推荐用于主键） |
| `jsonb` | 二进制 JSON（可查询） | `metadata`, `settings` |
| `float8` | 双精度浮点数 | `price`, `latitude` |
| `text[]` | 文本数组 | `tags`, `categories` |

> 💡 **Supabase 推荐用 `uuid` 做主键**，而不是自增整数。UUID 在分布式环境下不会冲突，与 `auth.uid()` 天然兼容。

#### 主键、外键与索引

**主键（Primary Key）** —— 每行数据的唯一标识

```sql
CREATE TABLE users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,  -- UUID 主键
  name TEXT NOT NULL,
  email TEXT UNIQUE                                -- 唯一约束
);
```

**外键（Foreign Key）** —— 表与表之间的关联

```sql
CREATE TABLE posts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT,
  author_id UUID REFERENCES users(id) ON DELETE CASCADE
  --         ↑ 外键：关联到 users 表的 id
  --                                  ↑ 级联删除：用户删了，帖子也删
);
```

外键保证了**引用完整性**——不会出现"帖子的作者指向一个不存在的用户"这种脏数据。

**索引（Index）** —— 加速查询

```sql
-- 给 email 列创建索引，加速按邮箱查询
CREATE INDEX idx_users_email ON users(email);

-- 给 posts 的 author_id 创建索引，加速 JOIN 查询
CREATE INDEX idx_posts_author ON posts(author_id);

-- 复合索引：同时按状态和创建时间查询
CREATE INDEX idx_posts_status_date ON posts(is_published, created_at DESC);
```

> 🔑 **索引的直觉理解**：
>
> ```
> 没有索引  → 找一本书的某个章节 → 从第 1 页翻到最后一页
> 有索引    → 找一本书的某个章节 → 直接看目录，翻到对应页码
> ```
>
> Supabase 会自动为**主键和唯一约束**创建索引。外键列和频繁查询的列建议手动加索引。

### 2. Table Editor：可视化操作

Table Editor 是 Supabase Dashboard 中最直观的功能——不写一行 SQL，就能像操作 Excel 一样管理数据库。

#### 创建表

进入 **Table Editor → New Table**：

```
 ┌─────────────────────────────────────────────────────────┐
 │  Create a new table                                     │
 ├─────────────────────────────────────────────────────────┤
 │                                                         │
 │  Name: [ profiles              ]                        │
 │                                                         │
 │  Description: [ 用户资料表       ] (可选)                 │
 │                                                         │
 │  ☑ Enable Row Level Security (RLS)  ← 强烈建议开启      │
 │                                                         │
 │  Columns:                                               │
 │  ┌──────────┬───────┬────────┬─────────┬──────────────┐ │
 │  │ Name     │ Type  │Default │ Primary │ Nullable     │ │
 │  ├──────────┼───────┼────────┼─────────┼──────────────┤ │
 │  │ id       │ uuid  │ uuid() │  ✅     │  ☐           │ │
 │  │ username │ text  │  -     │  ☐     │  ☐           │ │
 │  │ avatar   │ text  │  -     │  ☐     │  ✅           │ │
 │  │ bio      │ text  │  -     │  ☐     │  ✅           │ │
 │  └──────────┴───────┴────────┴─────────┴──────────────┘ │
 │                                                         │
 │  [+ Add column]                                         │
 │                                                         │
 │              [ Save ]                                   │
 └─────────────────────────────────────────────────────────┘
```

创建后你会看到一个类似电子表格的界面，可以直接：
- **点击单元格** → 编辑数据
- **点击 + Insert row** → 新增行
- **右键列头** → 编辑列定义、排序、过滤

#### 关系可视化

当你创建了外键关系后，Table Editor 会自动识别并显示关联：

```
 profiles 表                              posts 表
 ┌────────────┬──────────┐               ┌──────────┬────────────┬─────────┐
 │ id (PK)    │ username │               │ id (PK)  │ title      │author_id│
 ├────────────┼──────────┤     1 : N     ├──────────┼────────────┼─────────┤
 │ abc-123    │ 张三     │ ◄────────────  │ post-001 │ 第一篇文章 │ abc-123 │
 │ def-456    │ 李四     │ ◄──────┐      │ post-002 │ 第二篇文章 │ abc-123 │
 └────────────┴──────────┘       └────── │ post-003 │ 李四的文章 │ def-456 │
                                         └──────────┴────────────┴─────────┘

 在 Table Editor 中，点击 author_id 的值可以直接跳转到关联的 profiles 记录。
```

#### 导入 CSV 数据

Table Editor 支持直接从 CSV 文件导入数据：

1. 点击 **New Table → Import data from CSV**
2. 拖拽或选择 CSV 文件
3. Supabase 会自动推断列名和数据类型
4. 预览数据 → 调整类型 → 确认创建

> 💡 对于已有表，也可以通过 **Insert → Import data from CSV** 批量导入行数据。

### 3. SQL Editor：高级操作

当可视化操作不够用时，SQL Editor 是你的利器——直接在浏览器中编写和执行 SQL。

#### 界面

```
 ┌─────────────────────────────────────────────────────────┐
 │  SQL Editor                              [Run] [Save]   │
 ├─────────────────────────────────────────────────────────┤
 │                                                         │
 │  SELECT                                                 │
 │    p.title,                                             │
 │    p.created_at,                                        │
 │    u.username AS author                                 │
 │  FROM posts p                                           │
 │  JOIN profiles u ON p.author_id = u.id                  │
 │  WHERE p.is_published = true                            │
 │  ORDER BY p.created_at DESC                             │
 │  LIMIT 10;                                              │
 │                                                         │
 ├─────────────────────────────────────────────────────────┤
 │  Results (10 rows)                      ⏱ 12ms          │
 │  ┌───────────────────┬────────────────┬────────┐        │
 │  │ title             │ created_at     │ author │        │
 │  ├───────────────────┼────────────────┼────────┤        │
 │  │ Supabase 入门指南  │ 2025-03-20    │ 张三   │        │
 │  │ ...               │ ...            │ ...    │        │
 │  └───────────────────┴────────────────┴────────┘        │
 └─────────────────────────────────────────────────────────┘
```

#### 常用 SQL 模式

**JOIN —— 关联查询**

```sql
-- 查询每篇文章的作者信息
SELECT
  posts.title,
  posts.created_at,
  profiles.username,
  profiles.avatar
FROM posts
JOIN profiles ON posts.author_id = profiles.id
ORDER BY posts.created_at DESC;
```

**聚合 —— 统计分析**

```sql
-- 每个用户发了多少篇文章
SELECT
  profiles.username,
  COUNT(posts.id) AS post_count
FROM profiles
LEFT JOIN posts ON profiles.id = posts.author_id
GROUP BY profiles.username
ORDER BY post_count DESC;
```

**子查询 —— 嵌套逻辑**

```sql
-- 找出发帖数超过平均值的用户
SELECT username, post_count
FROM (
  SELECT
    profiles.username,
    COUNT(posts.id) AS post_count
  FROM profiles
  LEFT JOIN posts ON profiles.id = posts.author_id
  GROUP BY profiles.username
) AS user_stats
WHERE post_count > (SELECT AVG(post_count) FROM (
  SELECT COUNT(id) AS post_count FROM posts GROUP BY author_id
) AS avg_stats);
```

**CTE（通用表表达式）—— 更清晰的复杂查询**

```sql
-- 同样的查询，用 CTE 写更清晰
WITH user_stats AS (
  SELECT
    author_id,
    COUNT(*) AS post_count
  FROM posts
  GROUP BY author_id
),
avg_posts AS (
  SELECT AVG(post_count) AS avg_count FROM user_stats
)
SELECT
  profiles.username,
  user_stats.post_count
FROM user_stats
JOIN profiles ON user_stats.author_id = profiles.id
CROSS JOIN avg_posts
WHERE user_stats.post_count > avg_posts.avg_count;
```

#### 保存和分享

- **保存查询**：点击 Save，给查询起个名字，下次直接调用
- **模板**：SQL Editor 内置了常用操作的模板（创建表、创建策略、创建函数等）
- **快捷键**：`Cmd/Ctrl + Enter` 运行选中的 SQL，`Cmd/Ctrl + S` 保存

### 4. 数据库函数（Database Functions）

PostgreSQL 允许你在数据库中编写自定义函数，把复杂的业务逻辑放在离数据最近的地方执行——更快、更安全。

#### 创建函数

```sql
-- 示例：搜索帖子（支持模糊搜索 + 分页）
CREATE OR REPLACE FUNCTION search_posts(
  search_term TEXT,
  page_number INT DEFAULT 1,
  page_size INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  author_name TEXT,
  created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id,
    p.title,
    p.content,
    profiles.username AS author_name,
    p.created_at
  FROM posts p
  JOIN profiles ON p.author_id = profiles.id
  WHERE
    p.title ILIKE '%' || search_term || '%'
    OR p.content ILIKE '%' || search_term || '%'
  ORDER BY p.created_at DESC
  LIMIT page_size
  OFFSET (page_number - 1) * page_size;
END;
$$;
```

#### 在客户端调用

Supabase 客户端可以直接调用数据库函数：

```javascript
// 调用 search_posts 函数
const { data, error } = await supabase
  .rpc('search_posts', {
    search_term: 'Supabase',
    page_number: 1,
    page_size: 20
  })

console.log(data)
// [{ id: '...', title: 'Supabase 入门', author_name: '张三', ... }]
```

> `.rpc()` 是 Supabase 调用数据库函数的专用方法，`rpc` = Remote Procedure Call。

#### 常见使用场景

| 场景 | 示例 |
| :--- | :--- |
| **复杂查询封装** | 多表 JOIN + 分页 + 搜索，封装成一个函数 |
| **数据验证** | 插入前检查业务规则（库存是否充足、余额是否足够） |
| **批量操作** | 一次性更新多条记录，避免多次网络请求 |
| **权限控制** | 结合 `auth.uid()` 实现精细的数据访问逻辑 |
| **聚合计算** | 排行榜、统计报表等需要复杂计算的场景 |

### 5. 触发器（Triggers）

触发器是数据库中的"自动化钩子"——当特定事件发生时（INSERT、UPDATE、DELETE），自动执行一段逻辑。

#### 基本概念

```
 触发器 = 事件 + 时机 + 动作

 事件：INSERT / UPDATE / DELETE
 时机：BEFORE（之前执行）/ AFTER（之后执行）
 动作：一个函数

 示例：
 "在 INSERT 到 orders 表 AFTER，执行 update_inventory 函数"
```

#### 实战：新用户注册时自动创建 Profile

这是 Supabase 中最常见的触发器用法——当用户通过 GoTrue 注册后，`auth.users` 表会新增一条记录。我们用触发器自动在 `profiles` 表中创建对应的用户资料：

```sql
-- 1. 创建 profiles 表
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  username TEXT UNIQUE,
  avatar_url TEXT,
  bio TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. 启用 RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- 3. 创建触发器函数
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER        -- 以创建者（管理员）权限执行
SET search_path = ''    -- 安全最佳实践
AS $$
BEGIN
  INSERT INTO public.profiles (id, username, avatar_url)
  VALUES (
    NEW.id,                                         -- 新用户的 UUID
    NEW.raw_user_meta_data->>'username',            -- 注册时传入的用户名
    NEW.raw_user_meta_data->>'avatar_url'           -- 注册时传入的头像
  );
  RETURN NEW;
END;
$$;

-- 4. 创建触发器
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION handle_new_user();
```

效果：

```
 用户注册
   ↓
 GoTrue 在 auth.users 中创建记录
   ↓
 触发器自动触发 ← AFTER INSERT
   ↓
 handle_new_user() 函数执行
   ↓
 profiles 表自动新增一行
   ↓
 用户资料创建完成！（用户无感知）
```

#### 其他常见触发器场景

| 触发时机 | 场景 | 示例 |
| :--- | :--- | :--- |
| AFTER INSERT | 新订单创建 → 扣减库存 | `update_inventory()` |
| AFTER UPDATE | 帖子被编辑 → 记录修改历史 | `log_changes()` |
| BEFORE DELETE | 删除前 → 软删除（标记而不真删） | `soft_delete()` |
| AFTER INSERT | 新评论 → 发送通知 | `send_notification()` |

### 6. 数据库迁移（Migrations）

当你的项目从"随便玩玩"变成"正式开发"，你需要**版本控制数据库结构**——就像 Git 管理代码一样。

#### Supabase CLI 迁移工作流

```
 ┌────────────────────┐     ┌────────────────────┐
 │   本地开发环境       │     │   远程 Supabase     │
 │   (Docker)          │     │   (Production)      │
 │                    │     │                    │
 │  修改数据库结构     │     │                    │
 │       ↓            │     │                    │
 │  生成迁移文件       │     │                    │
 │       ↓            │     │                    │
 │  测试通过          │     │                    │
 │       ↓            │     │                    │
 │  git commit        │─────│──▶ supabase db push │
 │                    │     │       ↓            │
 │                    │     │  应用迁移到生产环境  │
 └────────────────────┘     └────────────────────┘
```

#### 关键命令

```bash
# 初始化本地开发环境
supabase init
supabase start    # 启动本地 Docker 容器

# 创建新的迁移文件
supabase migration new add_posts_table
# → 生成 supabase/migrations/20250320_add_posts_table.sql

# 在迁移文件中写 SQL
# supabase/migrations/20250320_add_posts_table.sql
```

```sql
-- 迁移文件内容
CREATE TABLE posts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT,
  author_id UUID REFERENCES auth.users(id),
  is_published BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
```

```bash
# 应用迁移到本地数据库
supabase db reset    # 重置本地数据库并运行所有迁移

# 部署到远程生产环境
supabase db push     # 将未执行的迁移推送到远程

# 查看迁移状态
supabase migration list
```

#### 迁移文件的版本控制

```
 项目结构
 ├── src/               ← 应用代码
 ├── supabase/
 │   ├── config.toml    ← Supabase 本地配置
 │   ├── migrations/    ← 迁移文件（按时间排序）
 │   │   ├── 20250101_create_profiles.sql
 │   │   ├── 20250215_create_posts.sql
 │   │   ├── 20250310_add_tags_column.sql
 │   │   └── 20250320_create_comments.sql
 │   └── seed.sql       ← 种子数据（可选）
 └── .gitignore
```

> 🔑 **核心原则**：迁移文件一旦提交到 Git，**不要修改**。如果需要改动，创建新的迁移文件。这和 Git 的"不要修改已推送的 commit"是同一个道理。

---

## 四、认证（Authentication）

### 1. GoTrue 认证引擎

#### 什么是 GoTrue

**GoTrue** 是 Supabase 的认证服务核心——一个用 Go 语言编写的开源认证 API 服务器。它负责处理所有与用户身份相关的操作：注册、登录、登出、密码重置、第三方 OAuth、JWT 签发……

```
 ┌─────────────────────────────────────────────────────────┐
 │                    GoTrue 架构                           │
 ├─────────────────────────────────────────────────────────┤
 │                                                         │
 │  前端应用                                                │
 │    ↓  supabase.auth.signUp() / signInWithPassword()     │
 │    ↓                                                    │
 │  ┌───────────────────────────────────┐                  │
 │  │           GoTrue Server           │                  │
 │  │                                   │                  │
 │  │  · 验证用户凭证（密码/OAuth/OTP） │                  │
 │  │  · 管理用户会话                    │                  │
 │  │  · 签发 JWT（Access + Refresh）    │                  │
 │  │  · 发送确认邮件 / 重置密码邮件     │                  │
 │  │  · 处理 OAuth 回调                │                  │
 │  └──────────────┬────────────────────┘                  │
 │                 │                                        │
 │                 ▼                                        │
 │  ┌───────────────────────────────────┐                  │
 │  │         auth.users 表              │                  │
 │  │  （PostgreSQL，Supabase 内部管理） │                  │
 │  │                                   │                  │
 │  │  · id (UUID)                      │                  │
 │  │  · email                          │                  │
 │  │  · encrypted_password             │                  │
 │  │  · raw_user_meta_data (JSONB)     │                  │
 │  │  · created_at / last_sign_in_at   │                  │
 │  └───────────────────────────────────┘                  │
 └─────────────────────────────────────────────────────────┘
```

#### 认证流程（以邮箱密码为例）

```
 用户                 前端应用                GoTrue              PostgreSQL
  │                    │                       │                     │
  │  输入邮箱+密码     │                       │                     │
  │───────────────────▶│                       │                     │
  │                    │                       │                     │
  │                    │  POST /auth/v1/signup  │                     │
  │                    │──────────────────────▶│                     │
  │                    │                       │                     │
  │                    │                       │  INSERT INTO         │
  │                    │                       │  auth.users          │
  │                    │                       │─────────────────────▶│
  │                    │                       │                     │
  │                    │                       │  签发 JWT             │
  │                    │                       │  Access Token (1h)   │
  │                    │                       │  Refresh Token (7d)  │
  │                    │                       │                     │
  │                    │  返回 { user, session }│                     │
  │                    │◀──────────────────────│                     │
  │                    │                       │                     │
  │  登录成功！         │                       │                     │
  │◀───────────────────│                       │                     │
```

#### 支持的认证方式全景图

GoTrue 支持多种认证方式，覆盖了主流的登录场景：

| 认证方式 | 说明 | 典型场景 |
| :--- | :--- | :--- |
| **邮箱 + 密码** | 最传统的注册登录方式 | 通用 |
| **Magic Link** | 发送登录链接到邮箱，点击即登录 | 无密码体验 |
| **手机号 + OTP** | 短信验证码登录 | 移动端、国内应用 |
| **Google OAuth** | 使用 Google 账号登录 | 海外应用 |
| **GitHub OAuth** | 使用 GitHub 账号登录 | 开发者工具 |
| **Apple OAuth** | 使用 Apple ID 登录 | iOS 应用（必须支持） |
| **微信 / 微博** | 通过自定义 OAuth 接入 | 国内应用 |
| **SAML SSO** | 企业级单点登录 | 企业客户 |
| **MFA (TOTP)** | 多因素认证（二步验证） | 高安全场景 |
| **匿名登录** | 不注册直接使用，后续可绑定身份 | 试用体验 |

```
 认证方式选择指南
 ═══════════════════════════════════════════════════

 个人项目 / MVP      → 邮箱 + 密码 + Google OAuth
 SaaS 产品           → 邮箱 + Google + GitHub + Magic Link
 移动端应用          → 手机号 OTP + Apple（iOS 必须）+ Google
 企业级产品          → SAML SSO + MFA
 国内应用            → 手机号 OTP + 微信 OAuth
```

> 💡 **与 SSO/JWT 文章的衔接**：
>
> GoTrue 签发的 JWT 结构和我们在《什么是单点登录（SSO）与 JWT》中讲的完全一致——Header.Payload.Signature 三段式。Supabase 的 `anon key` 本质上就是一个特殊的 JWT，它告诉 PostgREST："这个请求来自匿名用户，请按 RLS 策略处理。"

### 2. 邮箱密码认证

最基础也最常用的认证方式。

#### 注册

```javascript
const { data, error } = await supabase.auth.signUp({
  email: 'zhang@example.com',
  password: 'my-secure-password',
  options: {
    data: {                           // 自定义元数据，存入 raw_user_meta_data
      username: '张三',
      avatar_url: 'https://...'
    }
  }
})

// data.user  → 用户信息
// data.session → 会话（如果开启了邮箱确认，此时为 null）
```

#### 登录

```javascript
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'zhang@example.com',
  password: 'my-secure-password'
})

// data.session.access_token  → JWT Access Token
// data.session.refresh_token → Refresh Token
// data.user                  → 用户信息
```

#### 登出

```javascript
const { error } = await supabase.auth.signOut()
// 清除本地会话，Refresh Token 失效
```

#### 邮箱确认流程

默认情况下，Supabase 会在注册后发送确认邮件：

```
 用户注册
   ↓
 GoTrue 创建用户（email_confirmed_at = null）
   ↓
 发送确认邮件到用户邮箱
   ↓
 用户点击邮件中的链接
   ↓
 https://your-app.com/auth/callback?token=xxx&type=signup
   ↓
 GoTrue 确认邮箱（email_confirmed_at = now()）
   ↓
 用户正式激活 ✅
```

> 💡 开发阶段可以在 **Dashboard → Authentication → Settings** 中关闭 "Enable email confirmations" 来跳过邮箱确认。

#### 密码重置

```javascript
// 1. 发送重置密码邮件
const { error } = await supabase.auth.resetPasswordForEmail(
  'zhang@example.com',
  { redirectTo: 'https://your-app.com/reset-password' }
)

// 2. 用户点击邮件链接后，在重置页面更新密码
const { error } = await supabase.auth.updateUser({
  password: 'new-secure-password'
})
```

### 3. 第三方 OAuth 认证

#### 配置流程（以 Google 为例）

```
 ① 在 Google Cloud Console 创建 OAuth 2.0 凭据
    → 获取 Client ID 和 Client Secret
    → 设置授权回调 URL：https://xxxx.supabase.co/auth/v1/callback

 ② 在 Supabase Dashboard → Authentication → Providers
    → 找到 Google，开启
    → 填入 Client ID 和 Client Secret

 ③ 前端调用：
```

```javascript
// Google 登录
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: 'https://your-app.com/dashboard'
  }
})

// GitHub 登录
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'github'
})

// Apple 登录
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'apple'
})
```

#### 回调处理

OAuth 登录后，用户会被重定向回你的应用。需要在回调页面处理 URL 中的认证信息：

```javascript
// 在回调页面（如 /auth/callback）
import { useEffect } from 'react'

useEffect(() => {
  // Supabase 客户端会自动从 URL 中提取 token
  // 并建立会话，无需手动处理
  supabase.auth.getSession().then(({ data: { session } }) => {
    if (session) {
      // 登录成功，跳转到主页
      router.push('/dashboard')
    }
  })
}, [])
```

#### 支持的 OAuth 提供商

| 提供商 | 配置难度 | 说明 |
| :--- | :--- | :--- |
| Google | ⭐⭐ | 最常用，需要 Google Cloud Console |
| GitHub | ⭐ | 最简单，适合开发者工具 |
| Apple | ⭐⭐⭐ | iOS 上架必须支持，配置较复杂 |
| Discord | ⭐ | 游戏/社区类应用 |
| Twitter | ⭐⭐ | 社交类应用 |
| 微信/微博 | ⭐⭐⭐ | 需通过自定义 OAuth 或 Edge Function 接入 |

### 4. 手机号认证（OTP）

#### 配置短信服务商

在 **Dashboard → Authentication → Phone Auth** 中配置：

| 服务商 | 覆盖范围 | 说明 |
| :--- | :--- | :--- |
| Twilio | 全球 | 最常用，文档完善 |
| MessageBird | 全球 | Twilio 替代品 |
| Vonage | 全球 | 企业级 |

#### 代码示例

```javascript
// 1. 发送验证码
const { error } = await supabase.auth.signInWithOtp({
  phone: '+8613800138000'
})

// 2. 验证验证码
const { data, error } = await supabase.auth.verifyOtp({
  phone: '+8613800138000',
  token: '123456',     // 用户输入的 6 位验证码
  type: 'sms'
})

// data.session → 登录成功，拿到会话
```

### 5. Magic Link（魔法链接）

无密码登录——用户只需输入邮箱，点击收到的链接即可登录。

```javascript
// 发送 Magic Link
const { error } = await supabase.auth.signInWithOtp({
  email: 'zhang@example.com',
  options: {
    emailRedirectTo: 'https://your-app.com/dashboard'
  }
})
```

```
 用户输入邮箱
   ↓
 Supabase 发送一封包含登录链接的邮件
   ↓
 用户点击链接
   ↓
 https://your-app.com/dashboard#access_token=xxx&refresh_token=yyy
   ↓
 Supabase 客户端自动提取 token，建立会话
   ↓
 登录成功！无需密码 ✅
```

> 💡 Magic Link 非常适合**低频使用**的应用（如月度报告系统），用户不需要记密码。

### 6. 会话管理与 JWT

#### Supabase 的 JWT 结构

GoTrue 签发的 JWT Payload 长这样：

```json
{
  "aud": "authenticated",
  "exp": 1710003600,
  "iat": 1710000000,
  "iss": "https://xxxx.supabase.co/auth/v1",
  "sub": "a1b2c3d4-5678-90ab-cdef-1234567890ab",   // 用户 UUID
  "email": "zhang@example.com",
  "role": "authenticated",
  "app_metadata": {
    "provider": "email",
    "providers": ["email"]
  },
  "user_metadata": {
    "username": "张三",
    "avatar_url": "https://..."
  }
}
```

> `sub` 字段就是用户的 UUID，也是 RLS 策略中 `auth.uid()` 返回的值。

#### 监听会话变化

```javascript
// 监听登录/登出/Token 刷新事件
supabase.auth.onAuthStateChange((event, session) => {
  console.log('事件:', event)        // SIGNED_IN / SIGNED_OUT / TOKEN_REFRESHED
  console.log('会话:', session)      // session 对象或 null

  if (event === 'SIGNED_IN') {
    // 用户登录了
  } else if (event === 'SIGNED_OUT') {
    // 用户登出了，跳转到登录页
  } else if (event === 'TOKEN_REFRESHED') {
    // Access Token 自动刷新了（用户无感知）
  }
})
```

#### 获取当前用户

```javascript
// 获取当前会话
const { data: { session } } = await supabase.auth.getSession()

// 获取当前用户
const { data: { user } } = await supabase.auth.getUser()

console.log(user.id)             // UUID
console.log(user.email)          // 邮箱
console.log(user.user_metadata)  // 自定义元数据
```

#### 自定义 JWT Claims

可以通过数据库函数向 JWT 中注入自定义数据（如用户角色）：

```sql
-- 创建函数：在 JWT 中添加 user_role
CREATE OR REPLACE FUNCTION custom_access_token_hook(event JSONB)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
  user_role TEXT;
BEGIN
  -- 从 profiles 表查询用户角色
  SELECT role INTO user_role
  FROM profiles
  WHERE id = (event->>'user_id')::UUID;

  -- 将角色写入 JWT claims
  event := jsonb_set(
    event,
    '{claims,user_role}',
    to_jsonb(user_role)
  );

  RETURN event;
END;
$$;
```

### 7. 多因素认证（MFA）

为高安全场景添加第二重验证——目前 Supabase 支持 **TOTP（基于时间的一次性密码）**。

#### 注册 MFA

```javascript
// 1. 为用户注册 TOTP 因子
const { data, error } = await supabase.auth.mfa.enroll({
  factorType: 'totp',
  friendlyName: 'My Authenticator'
})

// data.totp.qr_code  → 二维码 URI，用于展示给用户扫码
// data.totp.secret   → 密钥（手动输入用）
// data.id            → 因子 ID

// 2. 用户用 Google Authenticator / Authy 扫码后
//    输入 6 位验证码来确认注册
const { data: challenge } = await supabase.auth.mfa.challenge({
  factorId: data.id
})

const { data: verify } = await supabase.auth.mfa.verify({
  factorId: data.id,
  challengeId: challenge.id,
  code: '123456'     // 用户输入的 TOTP 码
})
```

#### MFA 登录流程

```
 用户输入邮箱 + 密码
   ↓
 第一步验证通过
   ↓
 检测到该用户开启了 MFA
   ↓
 跳转到 TOTP 输入页面
   ↓
 用户打开 Authenticator 应用，输入 6 位码
   ↓
 验证通过 → 完全登录 ✅
```

> ⚠️ MFA 是**可选增强**，不是默认开启的。建议在涉及资金、敏感数据的场景中提供 MFA 选项。

---

## 五、行级安全（Row Level Security, RLS）

### 1. 为什么 RLS 是 Supabase 的灵魂

在传统架构中，安全逻辑写在后端 API 里——前端永远不直接接触数据库。但 Supabase 让前端**直接查询数据库**，这就带来了一个核心问题：

```
 传统架构                              Supabase 架构
 ═══════════════════════                ═══════════════════════

 前端 → 后端 API → 数据库              前端 → PostgREST → 数据库
         ↑                                                ↑
    安全逻辑在这里                               安全逻辑在哪里？？
    if (user.id !== post.author_id)
      return 403

 后端负责过滤数据                       没有后端了！谁来过滤？
```

答案就是 **RLS（Row Level Security）**——把访问控制下沉到数据库层面：

```
 没有 RLS                              有 RLS
 ═══════════════════════                ═══════════════════════

 SELECT * FROM posts                   SELECT * FROM posts
   → 返回所有人的帖子 😱                 → 数据库自动过滤
                                        → 只返回当前用户有权看的帖子 ✅
```

> 🔑 **RLS 是 Supabase 安全模型的基石**。没有 RLS，你的 `anon key` 暴露在前端，任何人都能读写所有数据。有了 RLS，即使别人拿到你的 `anon key`，也只能访问策略允许的数据。

### 2. RLS 基础

#### 启用 RLS

```sql
-- 启用 RLS（创建表后必须做的第一件事）
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- 注意：启用 RLS 后，如果没有创建任何策略，
-- 所有查询都会返回空结果（默认拒绝一切）
```

#### 创建策略（Policy）

策略的基本语法：

```sql
CREATE POLICY "策略名称" ON 表名
  FOR 操作类型 (SELECT / INSERT / UPDATE / DELETE)
  TO 角色 (authenticated / anon / public)
  USING (条件表达式)              -- 用于 SELECT / UPDATE / DELETE
  WITH CHECK (条件表达式);         -- 用于 INSERT / UPDATE
```

#### 四种操作的策略示例

```sql
-- SELECT：用户只能查看自己的帖子
CREATE POLICY "用户查看自己的帖子" ON posts
  FOR SELECT
  TO authenticated
  USING (auth.uid() = author_id);

-- INSERT：用户只能创建属于自己的帖子
CREATE POLICY "用户创建自己的帖子" ON posts
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = author_id);

-- UPDATE：用户只能修改自己的帖子
CREATE POLICY "用户修改自己的帖子" ON posts
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = author_id)          -- 只能选中自己的行
  WITH CHECK (auth.uid() = author_id);    -- 修改后也必须属于自己

-- DELETE：用户只能删除自己的帖子
CREATE POLICY "用户删除自己的帖子" ON posts
  FOR DELETE
  TO authenticated
  USING (auth.uid() = author_id);
```

> 💡 **USING vs WITH CHECK**：
> - `USING` → 过滤**已有**的行（"你能看到/操作哪些行？"）
> - `WITH CHECK` → 验证**新写入**的行（"你写入的数据合法吗？"）

### 3. 常见策略模式

#### 模式一：用户只能访问自己的数据

最常见的模式，适用于个人数据（待办事项、笔记、订单等）：

```sql
CREATE POLICY "个人数据隔离" ON todos
  FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
```

#### 模式二：公开可读 + 仅作者可写

适用于博客、论坛等内容平台：

```sql
-- 所有人（包括未登录用户）都能读
CREATE POLICY "公开可读" ON posts
  FOR SELECT
  TO anon, authenticated
  USING (is_published = true);

-- 只有作者能写
CREATE POLICY "作者可写" ON posts
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = author_id);

CREATE POLICY "作者可改" ON posts
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = author_id);

CREATE POLICY "作者可删" ON posts
  FOR DELETE
  TO authenticated
  USING (auth.uid() = author_id);
```

#### 模式三：基于角色的访问控制

```sql
-- 管理员可以查看所有数据
CREATE POLICY "管理员全权限" ON posts
  FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role = 'admin'
    )
  );

-- 普通用户只能看自己的
CREATE POLICY "普通用户看自己的" ON posts
  FOR SELECT
  TO authenticated
  USING (auth.uid() = author_id);
```

#### 模式四：组织级别的数据隔离（多租户）

```sql
-- 用户只能访问自己所在组织的数据
CREATE POLICY "组织隔离" ON projects
  FOR ALL
  TO authenticated
  USING (
    org_id IN (
      SELECT org_id FROM org_members
      WHERE user_id = auth.uid()
    )
  )
  WITH CHECK (
    org_id IN (
      SELECT org_id FROM org_members
      WHERE user_id = auth.uid()
    )
  );
```

### 4. 进阶：使用 auth.uid() 和自定义 Claims

#### Supabase 内置的认证函数

| 函数 | 返回值 | 用途 |
| :--- | :--- | :--- |
| `auth.uid()` | UUID | 当前登录用户的 ID |
| `auth.jwt()` | JSONB | 当前用户的完整 JWT Payload |
| `auth.role()` | TEXT | 当前角色（`authenticated` 或 `anon`） |

#### 结合 JWT Claims 实现复杂权限

如果你在第四章中配置了自定义 JWT Claims（如 `user_role`），可以在 RLS 中直接使用：

```sql
-- 从 JWT 中读取自定义角色
CREATE POLICY "VIP 用户可以访问高级内容" ON premium_content
  FOR SELECT
  TO authenticated
  USING (
    (auth.jwt()->>'user_role') = 'vip'
    OR
    (auth.jwt()->>'user_role') = 'admin'
  );
```

```
 用户请求
   ↓
 JWT 中包含 { ..., "user_role": "vip" }
   ↓
 PostgREST 将 JWT 传给 PostgreSQL
   ↓
 RLS 策略读取 auth.jwt()->>'user_role'
   ↓
 'vip' 匹配策略条件 → 放行 ✅
```

### 5. RLS 性能优化

#### 策略对性能的影响

RLS 策略本质上是在每次查询时**自动追加 WHERE 条件**。复杂的策略可能拖慢查询：

```sql
-- 简单策略（快 ✅）：直接比较字段
USING (auth.uid() = user_id)
-- 等价于：WHERE user_id = '当前用户UUID'

-- 复杂策略（可能慢 ⚠️）：包含子查询
USING (
  org_id IN (
    SELECT org_id FROM org_members
    WHERE user_id = auth.uid()
  )
)
-- 每次查询都要执行这个子查询
```

#### 优化建议

| 优化手段 | 做法 |
| :--- | :--- |
| **给外键列加索引** | `CREATE INDEX idx_posts_author ON posts(author_id)` |
| **给策略中涉及的列加索引** | `CREATE INDEX idx_members_user ON org_members(user_id)` |
| **避免多层嵌套子查询** | 尽量用简单条件或 JOIN 替代 |
| **使用 security definer 函数** | 把复杂逻辑封装成函数，减少策略复杂度 |

#### 常见陷阱

```
 ❌ 陷阱 1：忘记启用 RLS
    → 任何人都能读写所有数据

 ❌ 陷阱 2：启用 RLS 但忘记创建策略
    → 所有查询返回空结果，以为是 bug

 ❌ 陷阱 3：只创建了 SELECT 策略
    → 用户可以查看但无法插入/更新数据

 ❌ 陷阱 4：在策略中使用 service_role 测试
    → service_role 绕过 RLS，测试结果不真实

 ✅ 调试技巧：
    → 在 SQL Editor 中用以下命令模拟特定用户：
    SET request.jwt.claim.sub = '用户UUID';
    SET role = 'authenticated';
    SELECT * FROM posts;  -- 看看能查到什么
```

---

## 六、实时功能（Realtime）

### 1. 架构原理

Supabase 的实时功能由 **Realtime Server** 提供，它基于 Elixir 语言的 **Phoenix 框架**构建——一个以高并发和低延迟著称的 WebSocket 服务器。

```
 ┌────────────────────────────────────────────────────────┐
 │                 Realtime 架构                           │
 ├────────────────────────────────────────────────────────┤
 │                                                        │
 │  前端客户端 A ──┐                                       │
 │  前端客户端 B ──┤── WebSocket ──▶ Realtime Server       │
 │  前端客户端 C ──┘               （Phoenix / Elixir）    │
 │                                        │               │
 │                    ┌───────────────────┼──────────┐    │
 │                    │                   │          │    │
 │                    ▼                   ▼          ▼    │
 │             Postgres Changes     Broadcast    Presence │
 │             （数据库变更推送）    （自定义消息）（在线状态）│
 │                    │                                   │
 │                    ▼                                   │
 │              PostgreSQL                                │
 │          （WAL 逻辑复制流）                              │
 └────────────────────────────────────────────────────────┘
```

Supabase Realtime 提供三种能力：

| 能力 | 数据源 | 延迟 | 场景 |
| :--- | :--- | :--- | :--- |
| **Postgres Changes** | 数据库变更（WAL） | ~100ms | 实时数据同步、协作编辑 |
| **Broadcast** | 客户端自定义消息 | ~10ms | 光标同步、游戏状态 |
| **Presence** | 客户端状态同步 | ~100ms | 在线状态、正在输入… |

### 2. 数据库变更监听（Postgres Changes）

最核心的实时功能——当数据库中的数据发生变化时，自动推送给订阅的客户端。

#### 基本用法

```javascript
// 监听 todos 表的所有变化
const channel = supabase
  .channel('todos-changes')
  .on(
    'postgres_changes',
    {
      event: '*',          // INSERT / UPDATE / DELETE / *（全部）
      schema: 'public',
      table: 'todos'
    },
    (payload) => {
      console.log('变化类型:', payload.eventType)   // INSERT / UPDATE / DELETE
      console.log('新数据:', payload.new)            // 变更后的行
      console.log('旧数据:', payload.old)            // 变更前的行（仅 UPDATE/DELETE）
    }
  )
  .subscribe()
```

#### 过滤条件

不需要监听整张表时，可以用过滤条件减少传输量：

```javascript
// 只监听当前用户的 todo 变化
const channel = supabase
  .channel('my-todos')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'todos',
      filter: `user_id=eq.${currentUserId}`   // 过滤条件
    },
    (payload) => {
      console.log('新增了一条 todo:', payload.new)
    }
  )
  .subscribe()
```

#### 实战：实时聊天

```javascript
function ChatRoom({ roomId }) {
  const [messages, setMessages] = useState([])

  useEffect(() => {
    // 1. 加载历史消息
    supabase
      .from('messages')
      .select('*, profiles(username, avatar_url)')
      .eq('room_id', roomId)
      .order('created_at')
      .then(({ data }) => setMessages(data || []))

    // 2. 监听新消息
    const channel = supabase
      .channel(`room-${roomId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'messages',
          filter: `room_id=eq.${roomId}`
        },
        (payload) => {
          setMessages(prev => [...prev, payload.new])
        }
      )
      .subscribe()

    // 3. 清理
    return () => { supabase.removeChannel(channel) }
  }, [roomId])

  // 4. 发送消息
  async function sendMessage(text) {
    await supabase.from('messages').insert({
      room_id: roomId,
      content: text
    })
    // 不需要手动更新 UI，实时监听会自动推送！
  }

  return (/* 渲染消息列表 */)
}
```

### 3. 广播（Broadcast）

广播是**不经过数据库**的实时消息——客户端之间直接通过 Realtime Server 中转，延迟更低。

#### 使用场景

```
 Postgres Changes：数据需要持久化 → 聊天消息、文档更新
 Broadcast：       数据不需要存储 → 光标位置、打字状态、游戏操作
```

#### 代码示例：多人光标同步

```javascript
// 发送光标位置
const channel = supabase.channel('cursor-room')

channel.subscribe((status) => {
  if (status === 'SUBSCRIBED') {
    // 发送自己的光标位置
    document.addEventListener('mousemove', (e) => {
      channel.send({
        type: 'broadcast',
        event: 'cursor-move',
        payload: {
          userId: currentUser.id,
          x: e.clientX,
          y: e.clientY
        }
      })
    })
  }
})

// 接收其他用户的光标位置
channel.on('broadcast', { event: 'cursor-move' }, (payload) => {
  const { userId, x, y } = payload.payload
  // 在屏幕上显示其他用户的光标
  moveCursor(userId, x, y)
})
```

### 4. 在线状态（Presence）

Presence 用于跟踪哪些用户**当前在线**，以及他们的状态信息。

#### 代码示例：在线用户列表

```javascript
const channel = supabase.channel('online-users')

// 监听在线状态变化
channel.on('presence', { event: 'sync' }, () => {
  const state = channel.presenceState()
  console.log('当前在线用户:', state)
  // { 'user-1': [{ username: '张三', status: 'online' }],
  //   'user-2': [{ username: '李四', status: 'away' }] }
})

channel.on('presence', { event: 'join' }, ({ key, newPresences }) => {
  console.log('用户上线:', key)
})

channel.on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
  console.log('用户离线:', key)
})

// 订阅并跟踪自己的状态
channel.subscribe(async (status) => {
  if (status === 'SUBSCRIBED') {
    await channel.track({
      username: currentUser.username,
      status: 'online',
      online_at: new Date().toISOString()
    })
  }
})
```

```
 用户 A 进入页面 → track({ status: 'online' })
   ↓
 Realtime Server 广播 presence:join 事件
   ↓
 用户 B、C 收到通知 → 更新在线列表

 用户 A 关闭页面 → WebSocket 断开
   ↓
 Realtime Server 自动广播 presence:leave 事件
   ↓
 用户 B、C 收到通知 → 从在线列表中移除 A
```

> 💡 **Presence vs Broadcast 的区别**：Presence 由 Realtime Server **自动管理**状态（加入/离开/同步），Broadcast 只是简单的消息转发，不维护状态。

---

## 七、文件存储（Storage）

### 1. 存储架构

Supabase Storage 是一个 **S3 兼容的对象存储服务**，专门用于管理文件（图片、视频、文档等）。

```
 ┌─────────────────────────────────────────────┐
 │              Supabase Storage                │
 ├─────────────────────────────────────────────┤
 │                                             │
 │  Bucket（存储桶）= 文件的顶层容器            │
 │                                             │
 │  ┌───────────────┐  ┌───────────────┐       │
 │  │  avatars       │  │  documents    │       │
 │  │  （公开桶）     │  │  （私有桶）    │       │
 │  │               │  │               │       │
 │  │  /user1.jpg   │  │  /report.pdf  │       │
 │  │  /user2.png   │  │  /invoice.xlsx│       │
 │  └───────────────┘  └───────────────┘       │
 │                                             │
 │  底层：S3 兼容存储（可对接 AWS S3 / MinIO）  │
 │  访问控制：Storage Policies（类似 RLS）       │
 │  额外功能：图片变换、签名 URL、CDN            │
 └─────────────────────────────────────────────┘
```

| 概念 | 说明 |
| :--- | :--- |
| **Bucket** | 存储桶，文件的顶层容器。类似文件夹 |
| **公开桶** | 任何人可通过 URL 直接访问文件 |
| **私有桶** | 需要认证 + 策略授权才能访问 |
| **对象路径** | 文件在桶中的路径，如 `avatars/user1.jpg` |

### 2. 基本操作

#### 创建 Bucket

```javascript
// 创建私有桶
const { data, error } = await supabase.storage.createBucket('documents', {
  public: false,         // 私有
  fileSizeLimit: 1024 * 1024 * 10,  // 10MB 限制
  allowedMimeTypes: ['application/pdf', 'image/*']
})

// 创建公开桶（如用户头像）
const { data, error } = await supabase.storage.createBucket('avatars', {
  public: true           // 公开，任何人可通过 URL 访问
})
```

#### 上传文件

```javascript
// 从 File 对象上传（浏览器）
const file = event.target.files[0]
const { data, error } = await supabase.storage
  .from('avatars')
  .upload(`${userId}/avatar.jpg`, file, {
    cacheControl: '3600',          // 缓存 1 小时
    upsert: true,                  // 存在则覆盖
    contentType: 'image/jpeg'
  })
```

#### 下载文件

```javascript
// 从私有桶下载
const { data, error } = await supabase.storage
  .from('documents')
  .download('reports/2025-q1.pdf')

// data 是 Blob 对象
const url = URL.createObjectURL(data)
```

#### 获取公开 URL

```javascript
// 公开桶：直接获取永久 URL
const { data } = supabase.storage
  .from('avatars')
  .getPublicUrl('user1/avatar.jpg')

console.log(data.publicUrl)
// https://xxxx.supabase.co/storage/v1/object/public/avatars/user1/avatar.jpg
```

#### 生成签名 URL（私有桶）

```javascript
// 私有桶：生成有时效的签名 URL
const { data, error } = await supabase.storage
  .from('documents')
  .createSignedUrl('reports/2025-q1.pdf', 3600)  // 有效期 1 小时

console.log(data.signedUrl)
// https://xxxx.supabase.co/storage/v1/object/sign/documents/reports/...?token=xxx
```

#### 删除文件

```javascript
const { error } = await supabase.storage
  .from('avatars')
  .remove(['user1/old-avatar.jpg'])
```

### 3. 图片变换（Image Transformations）

Supabase 支持通过 URL 参数**动态**调整图片，无需预先生成缩略图：

```javascript
// 获取带变换的公开 URL
const { data } = supabase.storage
  .from('avatars')
  .getPublicUrl('user1/avatar.jpg', {
    transform: {
      width: 200,
      height: 200,
      resize: 'cover',        // cover / contain / fill
      quality: 80,             // 图片质量（1-100）
      format: 'origin'         // origin / webp
    }
  })
```

常用变换参数：

| 参数 | 说明 | 示例 |
| :--- | :--- | :--- |
| `width` | 目标宽度（px） | `200` |
| `height` | 目标高度（px） | `200` |
| `resize` | 缩放模式 | `cover`（裁切填充）/ `contain`（完整显示） |
| `quality` | 压缩质量 | `80`（推荐值） |
| `format` | 输出格式 | `webp`（更小体积） |

```
 原图：3000x2000, 2.5MB
   ↓
 ?width=300&height=300&resize=cover&quality=80&format=webp
   ↓
 输出：300x300, ~15KB  ← 体积缩小 99%！
```

> 💡 图片变换是**按需生成**的（首次请求时处理），之后会被缓存。非常适合用户头像、商品缩略图等场景。

### 4. 存储策略（Storage Policies）

Storage Policies 的工作方式和 RLS 几乎一致——在数据库层面控制文件访问权限。

#### 常见策略模式

**模式一：用户只能管理自己的头像**

```sql
-- 上传：用户只能上传到自己的文件夹
CREATE POLICY "用户上传自己的头像" ON storage.objects
  FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = auth.uid()::TEXT
  );

-- 读取：所有人可以查看头像（公开桶）
CREATE POLICY "头像公开可读" ON storage.objects
  FOR SELECT
  TO public
  USING (bucket_id = 'avatars');

-- 更新/删除：用户只能操作自己的文件
CREATE POLICY "用户管理自己的头像" ON storage.objects
  FOR UPDATE
  TO authenticated
  USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = auth.uid()::TEXT
  );

CREATE POLICY "用户删除自己的头像" ON storage.objects
  FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = auth.uid()::TEXT
  );
```

**推荐的文件组织方式**：

```
 avatars/
 ├── {user_uuid_1}/
 │   └── avatar.jpg
 ├── {user_uuid_2}/
 │   └── avatar.png
 └── ...

 以用户 UUID 作为文件夹名 → 策略中直接用 auth.uid() 匹配
```

**模式二：文档只有上传者和管理员可以访问**

```sql
CREATE POLICY "文档访问控制" ON storage.objects
  FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'documents'
    AND (
      (storage.foldername(name))[1] = auth.uid()::TEXT
      OR
      EXISTS (
        SELECT 1 FROM profiles
        WHERE id = auth.uid() AND role = 'admin'
      )
    )
  );
```

---

## 八、边缘函数（Edge Functions）

### 1. 什么是 Edge Functions

Edge Functions 是 Supabase 中运行**自定义后端逻辑**的方式——当数据库函数和 PostgREST 不够用时，你就需要它。

```
 PostgREST / 数据库函数                    Edge Functions
 ═══════════════════════                    ═══════════════════════

 ✅ 数据 CRUD                              ✅ 调用第三方 API（OpenAI、Stripe…）
 ✅ 复杂 SQL 查询                           ✅ 处理 Webhook（GitHub、Stripe…）
 ✅ 数据验证和触发器                         ✅ 发送邮件/短信
 ❌ 无法调用外部 API                        ✅ 文件处理（PDF 生成、图片处理…）
 ❌ 无法执行非 SQL 逻辑                     ✅ 定时任务
```

#### Deno 运行时

Edge Functions 基于 **Deno** 运行——一个由 Node.js 创始人开发的现代 JavaScript/TypeScript 运行时：

| 特性 | 说明 |
| :--- | :--- |
| **TypeScript 原生** | 不需要编译，直接运行 `.ts` 文件 |
| **安全沙箱** | 默认无网络/文件权限，需显式授权 |
| **Web 标准 API** | 使用 `fetch`、`Request`、`Response` 等标准 API |
| **无 node_modules** | 通过 URL 导入模块，无需包管理器 |
| **冷启动快** | 毫秒级启动，比传统 Lambda 快很多 |

#### 适用场景

```
 需要 Edge Functions 的场景
 ═══════════════════════════════════════

 · 接入 OpenAI / Claude API → 生成文本/图片
 · 接入 Stripe → 处理支付回调
 · 发送 Webhook 通知 → 钉钉 / Slack / 飞书
 · 生成 PDF / 二维码
 · 定时清理过期数据
 · 复杂的业务编排（涉及多个外部服务）
```

### 2. 开发与部署

#### 创建函数

```bash
# 确保已安装 Supabase CLI
supabase functions new hello-world
# → 生成 supabase/functions/hello-world/index.ts
```

#### 编写函数

```typescript
// supabase/functions/hello-world/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  try {
    // 1. 获取请求数据
    const { name } = await req.json()

    // 2. 可选：创建已认证的 Supabase 客户端
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_ANON_KEY')!,
      {
        global: {
          headers: { Authorization: req.headers.get('Authorization')! }
        }
      }
    )

    // 3. 操作数据库
    const { data: user } = await supabase.auth.getUser()

    // 4. 返回响应
    return new Response(
      JSON.stringify({ message: `Hello ${name}!`, user: user }),
      { headers: { 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    )
  }
})
```

#### 本地调试

```bash
# 启动本地函数服务器
supabase functions serve hello-world --env-file .env.local

# 测试调用
curl -i --location --request POST \
  'http://localhost:54321/functions/v1/hello-world' \
  --header 'Authorization: Bearer YOUR_ANON_KEY' \
  --header 'Content-Type: application/json' \
  --data '{"name":"张三"}'
```

#### 部署到生产

```bash
# 部署单个函数
supabase functions deploy hello-world

# 部署所有函数
supabase functions deploy
```

#### 前端调用

```javascript
const { data, error } = await supabase.functions.invoke('hello-world', {
  body: { name: '张三' }
})

console.log(data.message)  // "Hello 张三!"
```

### 3. 实战示例

#### 示例一：调用 OpenAI API

```typescript
// supabase/functions/ai-chat/index.ts
serve(async (req) => {
  const { prompt } = await req.json()

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${Deno.env.get('OPENAI_API_KEY')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'gpt-4',
      messages: [{ role: 'user', content: prompt }]
    })
  })

  const result = await response.json()

  return new Response(
    JSON.stringify({ reply: result.choices[0].message.content }),
    { headers: { 'Content-Type': 'application/json' } }
  )
})
```

#### 示例二：Stripe 支付 Webhook

```typescript
// supabase/functions/stripe-webhook/index.ts
import Stripe from 'https://esm.sh/stripe@14?target=deno'

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY')!, {
  apiVersion: '2023-10-16'
})

serve(async (req) => {
  const signature = req.headers.get('stripe-signature')!
  const body = await req.text()

  const event = stripe.webhooks.constructEvent(
    body,
    signature,
    Deno.env.get('STRIPE_WEBHOOK_SECRET')!
  )

  switch (event.type) {
    case 'checkout.session.completed':
      // 支付成功 → 更新订单状态
      const session = event.data.object
      await supabase
        .from('orders')
        .update({ status: 'paid' })
        .eq('stripe_session_id', session.id)
      break
  }

  return new Response(JSON.stringify({ received: true }))
})
```

#### 示例三：定时任务（pg_cron + Edge Function）

```sql
-- 在 PostgreSQL 中设置定时任务，每天凌晨 2 点调用 Edge Function
SELECT cron.schedule(
  'daily-cleanup',
  '0 2 * * *',           -- 每天 02:00
  $$
  SELECT net.http_post(
    url := 'https://xxxx.supabase.co/functions/v1/daily-cleanup',
    headers := '{"Authorization": "Bearer SERVICE_ROLE_KEY"}'::JSONB
  );
  $$
);
```

### 4. 最佳实践

#### 错误处理

```typescript
serve(async (req) => {
  try {
    // 业务逻辑...
    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  } catch (error) {
    console.error('函数执行出错:', error)
    return new Response(JSON.stringify({
      error: error.message || 'Internal Server Error'
    }), {
      status: error.status || 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
})
```

#### 环境变量管理

```bash
# 设置环境变量（生产环境）
supabase secrets set OPENAI_API_KEY=sk-xxx
supabase secrets set STRIPE_SECRET_KEY=sk_live_xxx

# 查看已设置的变量
supabase secrets list

# 本地开发使用 .env.local 文件
echo "OPENAI_API_KEY=sk-xxx" >> .env.local
```

> ⚠️ `.env.local` 务必加入 `.gitignore`，不要提交密钥到 Git。

#### CORS 配置

```typescript
// 统一的 CORS 头
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // 处理预检请求
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  // 正常请求
  const data = { message: 'Hello!' }
  return new Response(JSON.stringify(data), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  })
})
```

---

## 九、Supabase CLI 与本地开发

### 1. CLI 安装与配置

#### 安装

```bash
# macOS
brew install supabase/tap/supabase

# npm（跨平台）
npm install -g supabase

# 验证安装
supabase --version
```

#### 连接到远程项目

```bash
# 登录（会打开浏览器授权）
supabase login

# 关联远程项目
supabase link --project-ref your-project-ref
# project-ref 在 Dashboard → Settings → General 中找到
```

#### 常用命令速查

| 命令 | 说明 |
| :--- | :--- |
| `supabase init` | 初始化本地项目 |
| `supabase start` | 启动本地开发环境（Docker） |
| `supabase stop` | 停止本地环境 |
| `supabase status` | 查看本地服务状态和端口 |
| `supabase db reset` | 重置本地数据库并运行所有迁移 |
| `supabase db push` | 将迁移推送到远程生产环境 |
| `supabase db pull` | 从远程拉取数据库结构 |
| `supabase migration new <name>` | 创建新迁移文件 |
| `supabase migration list` | 查看迁移状态 |
| `supabase functions new <name>` | 创建 Edge Function |
| `supabase functions serve` | 本地运行 Edge Function |
| `supabase functions deploy` | 部署 Edge Function |
| `supabase gen types typescript` | 生成 TypeScript 类型 |

### 2. 本地开发环境

#### 初始化与启动

```bash
# 在项目根目录初始化
supabase init

# 启动本地环境（需要 Docker）
supabase start
```

启动后会输出所有本地服务的地址：

```
 Started supabase local development setup.

         API URL: http://localhost:54321
     GraphQL URL: http://localhost:54321/graphql/v1
          DB URL: postgresql://postgres:postgres@localhost:54322/postgres
      Studio URL: http://localhost:54323       ← 本地 Dashboard
    Inbucket URL: http://localhost:54324       ← 本地邮件测试
      JWT secret: super-secret-jwt-token
        anon key: eyJhbGciOiJIUzI1NiIs...
service_role key: eyJhbGciOiJIUzI1NiIs...
```

#### 本地 Docker 容器

```
 supabase start 启动的容器
 ═══════════════════════════════════════

 ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
 │  PostgreSQL  │  │   GoTrue     │  │  PostgREST   │
 │  :54322      │  │   认证服务    │  │  REST API    │
 └──────────────┘  └──────────────┘  └──────────────┘

 ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
 │  Realtime    │  │  Storage     │  │  Kong        │
 │  实时服务     │  │  文件存储     │  │  API 网关    │
 └──────────────┘  └──────────────┘  └──────────────┘

 ┌──────────────┐  ┌──────────────┐
 │  Studio      │  │  Inbucket    │
 │  Dashboard   │  │  邮件测试     │
 │  :54323      │  │  :54324      │
 └──────────────┘  └──────────────┘
```

> 💡 **Inbucket** 是一个本地邮件服务器，注册确认邮件、密码重置邮件都会发到这里，不会真的发邮件。非常方便测试！

### 3. 迁移工作流

#### 开发流程

```bash
# 1. 在本地 Dashboard 中通过 UI 修改数据库结构
#    或者直接在 SQL Editor 中写 SQL

# 2. 将变更生成为迁移文件
supabase db diff -f add_posts_table
# → supabase/migrations/20250320_add_posts_table.sql

# 3. 验证迁移文件
supabase db reset    # 重置并重新运行所有迁移

# 4. 推送到远程
supabase db push
```

#### `db push` vs `db reset`

| 命令 | 行为 | 使用场景 |
| :--- | :--- | :--- |
| `supabase db reset` | 删除本地数据库，从零运行所有迁移 | 本地开发时验证迁移 |
| `supabase db push` | 只运行远程未执行的迁移，不删数据 | 部署到生产环境 |

#### CI/CD 集成

```yaml
# GitHub Actions 示例
name: Deploy Migrations
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: supabase/setup-cli@v1
        with:
          version: latest

      - run: supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}

      - run: supabase db push
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

### 4. 类型生成

#### 自动生成 TypeScript 类型

```bash
# 从远程项目生成
supabase gen types typescript --project-id your-project-ref > src/types/database.ts

# 从本地数据库生成
supabase gen types typescript --local > src/types/database.ts
```

生成的类型文件长这样：

```typescript
// src/types/database.ts（自动生成，不要手动修改）
export interface Database {
  public: {
    Tables: {
      todos: {
        Row: {
          id: number
          title: string
          is_complete: boolean
          user_id: string
          created_at: string
        }
        Insert: {
          id?: number
          title: string
          is_complete?: boolean
          user_id?: string
          created_at?: string
        }
        Update: {
          id?: number
          title?: string
          is_complete?: boolean
          user_id?: string
          created_at?: string
        }
      }
      // ... 其他表
    }
  }
}
```

#### 类型安全的查询

```typescript
import { createClient } from '@supabase/supabase-js'
import { Database } from './types/database'

// 创建带类型的客户端
const supabase = createClient<Database>(url, key)

// 现在所有查询都有类型提示！
const { data } = await supabase
  .from('todos')      // ← 自动补全表名
  .select('*')
  .eq('is_complete', false)  // ← 自动补全列名，类型检查值

// data 的类型自动推导为 Database['public']['Tables']['todos']['Row'][]
data?.[0].title     // ✅ string
data?.[0].count     // ❌ TypeScript 报错：'count' 不存在
```

> 🔑 **建议在 `package.json` 中添加类型生成脚本**：
> ```json
> {
>   "scripts": {
>     "gen:types": "supabase gen types typescript --local > src/types/database.ts"
>   }
> }
> ```
> 每次修改数据库结构后运行 `npm run gen:types` 即可保持类型同步。

---

## 十、实战项目：全栈 Todo 应用

### 1. 项目规划

#### 功能需求

```
 全栈 Todo 应用功能清单
 ═══════════════════════════════════════

 ☐ 用户注册 / 登录 / 登出（邮箱 + Google OAuth）
 ☐ Todo 增删改查（CRUD）
 ☐ 实时同步（多设备同时操作自动更新）
 ☐ 文件附件上传（给 todo 添加附件）
 ☐ RLS 数据隔离（用户只能看自己的 todo）
```

#### 技术栈

| 层 | 技术 | 说明 |
| :--- | :--- | :--- |
| 前端 | Next.js 14 (App Router) | React 全栈框架 |
| 样式 | Tailwind CSS | 快速出 UI |
| 后端 | Supabase | 数据库 + 认证 + 存储 + 实时 |
| 部署 | Vercel + Supabase Cloud | 前后端分别部署 |

### 2. 数据库设计

#### 表结构

```sql
-- 用户资料（通过触发器自动创建）
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Todo 表
CREATE TABLE todos (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  is_complete BOOLEAN DEFAULT false,
  attachment_url TEXT,        -- 附件路径
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON todos
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();
```

#### RLS 策略

```sql
ALTER TABLE todos ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Todos：用户只能操作自己的数据
CREATE POLICY "todos_select" ON todos FOR SELECT
  TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "todos_insert" ON todos FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);

CREATE POLICY "todos_update" ON todos FOR UPDATE
  TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "todos_delete" ON todos FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

-- Profiles：公开可读，仅自己可改
CREATE POLICY "profiles_select" ON profiles FOR SELECT
  TO authenticated USING (true);

CREATE POLICY "profiles_update" ON profiles FOR UPDATE
  TO authenticated USING (auth.uid() = id);
```

### 3. 认证集成

#### Supabase 客户端配置

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import { Database } from '@/types/database'

export const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
```

#### 登录页面

```tsx
// app/login/page.tsx
'use client'
import { supabase } from '@/lib/supabase'
import { useState } from 'react'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  async function handleLogin() {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (!error) window.location.href = '/dashboard'
  }

  async function handleGoogleLogin() {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${location.origin}/auth/callback` }
    })
  }

  return (
    <div>
      <input placeholder="邮箱" onChange={e => setEmail(e.target.value)} />
      <input type="password" placeholder="密码" onChange={e => setPassword(e.target.value)} />
      <button onClick={handleLogin}>登录</button>
      <button onClick={handleGoogleLogin}>Google 登录</button>
    </div>
  )
}
```

#### 路由保护

```typescript
// middleware.ts
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'

export async function middleware(req) {
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })
  const { data: { session } } = await supabase.auth.getSession()

  if (!session && req.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', req.url))
  }
  return res
}
```

### 4. 核心功能实现

#### Todo CRUD + 实时同步

```tsx
// app/dashboard/page.tsx
'use client'
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

export default function Dashboard() {
  const [todos, setTodos] = useState([])

  useEffect(() => {
    // 加载数据
    loadTodos()

    // 实时监听
    const channel = supabase
      .channel('my-todos')
      .on('postgres_changes',
        { event: '*', schema: 'public', table: 'todos' },
        () => loadTodos()  // 任何变化都重新加载
      )
      .subscribe()

    return () => { supabase.removeChannel(channel) }
  }, [])

  async function loadTodos() {
    const { data } = await supabase
      .from('todos')
      .select('*')
      .order('created_at', { ascending: false })
    setTodos(data || [])
  }

  async function addTodo(title: string) {
    await supabase.from('todos').insert({ title })
  }

  async function toggleTodo(id: string, current: boolean) {
    await supabase.from('todos').update({ is_complete: !current }).eq('id', id)
  }

  async function deleteTodo(id: string) {
    await supabase.from('todos').delete().eq('id', id)
  }

  // ... 渲染 UI
}
```

#### 文件附件上传

```typescript
async function uploadAttachment(todoId: string, file: File) {
  // 1. 上传文件到 Storage
  const path = `${todoId}/${file.name}`
  const { error: uploadError } = await supabase.storage
    .from('attachments')
    .upload(path, file)

  if (uploadError) return

  // 2. 获取公开 URL
  const { data } = supabase.storage
    .from('attachments')
    .getPublicUrl(path)

  // 3. 更新 todo 的附件字段
  await supabase
    .from('todos')
    .update({ attachment_url: data.publicUrl })
    .eq('id', todoId)
}
```

### 5. 部署上线

#### Vercel 部署

```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署（按提示操作）
vercel

# 设置环境变量
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
```

#### 环境变量清单

| 变量 | 值 | 位置 |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxx.supabase.co` | Vercel |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGciOi...` | Vercel |

#### 上线检查清单

```
 ☐ RLS 已在所有表上启用
 ☐ 所有表都有对应的策略
 ☐ service_role key 没有暴露在前端
 ☐ 邮箱确认已开启
 ☐ OAuth 回调地址已配置为生产域名
 ☐ 数据库密码足够强
```

---

## 十一、生产环境最佳实践

### 1. 安全加固

#### API Key 管理

```
 ⚠️ 最重要的安全原则
 ═══════════════════════════════════════

 anon key         → 可以暴露在前端（RLS 保护数据）
 service_role key → 绝对不能暴露！（绕过 RLS，全权访问）

 正确做法：
 ┌───────────┬──────────────────────────────────┐
 │ 前端代码   │ 只使用 anon key                   │
 │ Edge Func │ 通过环境变量使用 service_role key  │
 │ CI/CD     │ 通过 Secrets 管理                 │
 └───────────┴──────────────────────────────────┘
```

#### RLS 全面检查

```sql
-- 检查哪些表没有启用 RLS（危险！）
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
AND tablename NOT IN (
  SELECT tablename FROM pg_tables t
  JOIN pg_class c ON c.relname = t.tablename
  WHERE c.relrowsecurity = true
);

-- 检查哪些表没有策略（启用了 RLS 但没策略 = 拒绝一切）
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
AND tablename NOT IN (
  SELECT tablename FROM pg_policies WHERE schemaname = 'public'
);
```

### 2. 性能优化

#### 数据库索引策略

```sql
-- 1. 给高频查询列加索引
CREATE INDEX idx_todos_user ON todos(user_id);
CREATE INDEX idx_todos_created ON todos(created_at DESC);

-- 2. 复合索引（多条件查询）
CREATE INDEX idx_todos_user_status ON todos(user_id, is_complete);

-- 3. 部分索引（只索引活跃数据）
CREATE INDEX idx_active_todos ON todos(user_id)
WHERE is_complete = false;
```

#### 连接池（PgBouncer）

Supabase 内置 PgBouncer 连接池，默认通过端口 `6543` 访问：

| 连接方式 | 端口 | 说明 |
| :--- | :--- | :--- |
| 直连 | 5432 | 适合迁移、管理操作 |
| PgBouncer（Transaction 模式） | 6543 | 适合应用连接，复用连接 |

> 💡 Serverless 环境（如 Vercel Edge）应使用连接池模式，避免连接数爆满。

### 3. 监控与可观测性

#### Dashboard 监控

在 **Dashboard → Reports** 中可以查看：

| 指标 | 说明 |
| :--- | :--- |
| API 请求数 | 每日/每小时的请求量 |
| 数据库连接数 | 当前活跃连接 |
| 存储用量 | 文件存储已用空间 |
| 认证用户数 | 注册用户总数 |

#### 慢查询分析

```sql
-- 开启查询统计扩展
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 找出最慢的 10 条查询
SELECT
  query,
  calls,
  mean_exec_time::NUMERIC(10,2) AS avg_ms,
  total_exec_time::NUMERIC(10,2) AS total_ms
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### 4. 备份与恢复

| 方案 | 说明 | 可用计划 |
| :--- | :--- | :--- |
| **每日自动备份** | Supabase 自动执行，保留 7 天 | Pro 及以上 |
| **时间点恢复（PITR）** | 恢复到任意时间点 | Pro（附加购买） |
| **手动导出** | `pg_dump` 导出 SQL | 所有计划 |

```bash
# 手动导出数据库
pg_dump -h db.xxxx.supabase.co -U postgres -d postgres > backup.sql

# 恢复
psql -h db.xxxx.supabase.co -U postgres -d postgres < backup.sql
```

### 5. 扩展与限制

#### 计划对比

| 功能 | Free | Pro ($25/月) | Enterprise |
| :--- | :--- | :--- | :--- |
| 数据库大小 | 500 MB | 8 GB（可扩展） | 自定义 |
| 文件存储 | 1 GB | 100 GB | 自定义 |
| 带宽 | 5 GB | 250 GB | 自定义 |
| Edge Function 调用 | 50 万/月 | 200 万/月 | 自定义 |
| 并发连接 | 60（直连） | 200 | 自定义 |
| 每日备份 | ❌ | ✅ 7 天 | ✅ 自定义 |
| 自定义域名 | ❌ | ✅ | ✅ |
| SLA | ❌ | ❌ | ✅ 99.9% |

#### 何时考虑自托管

```
 继续使用 Supabase Cloud         考虑自托管
 ═══════════════════════          ═══════════════════════

 · 团队 < 50 人                  · 严格的数据合规（如金融、医疗）
 · 数据量 < 100 GB               · 需要完全控制基础设施
 · 预算可接受                     · 超大规模（TB 级数据）
 · 希望零运维                     · 有专职 DevOps 团队
```

---

## 十二、Supabase vs 竞品对比

### 1. Supabase vs Firebase

| 维度 | Supabase | Firebase |
| :--- | :--- | :--- |
| **数据库** | PostgreSQL（关系型） | Firestore（NoSQL 文档） |
| **查询能力** | 完整 SQL + JOIN + 聚合 | 有限查询，不支持 JOIN |
| **开源** | ✅ 完全开源 | ❌ 闭源 |
| **供应商锁定** | 低（可自托管，标准 PostgreSQL） | 高（绑定 Google Cloud） |
| **实时** | WebSocket + DB 监听 | 原生实时同步 |
| **定价** | 按资源用量，免费额度充足 | 按读写次数计费，可能超预期 |
| **学习曲线** | 需要 SQL 基础 | 更友好的 NoSQL API |

```
 选 Supabase 的场景                    选 Firebase 的场景
 ═══════════════════════                ═══════════════════════

 · 数据关系复杂（电商、SaaS）           · 快速原型验证
 · 需要复杂查询和报表                   · 移动端为主
 · 担心供应商锁定                       · 不懂 SQL
 · 团队熟悉 SQL/PostgreSQL              · 需要完善的移动 SDK
 · 需要自托管                           · 深度使用 Google 生态
```

### 2. Supabase vs Appwrite

| 维度 | Supabase | Appwrite |
| :--- | :--- | :--- |
| **数据库** | PostgreSQL | MariaDB |
| **实时** | ✅ Postgres Changes + Broadcast | ✅ Realtime Events |
| **边缘函数** | ✅ Deno 运行时 | ✅ 多语言运行时（Node/Python/Dart…） |
| **自托管** | Docker Compose（较复杂） | Docker 一键部署（更简单） |
| **云服务** | ✅ 稳定成熟 | ✅ 持续完善中 |
| **社区** | ⭐ 75k+ GitHub Stars | ⭐ 45k+ GitHub Stars |
| **SDK** | JavaScript, Python, Dart, Kotlin | 更多语言支持 |

> Appwrite 的自托管体验更好，但 Supabase 的 PostgreSQL 生态和云服务成熟度更高。

### 3. Supabase vs 组合方案（PlanetScale + Auth0 + S3）

| 维度 | Supabase（一站式） | 组合方案 |
| :--- | :--- | :--- |
| **复杂度** | 一个 Dashboard 搞定一切 | 需要管理 3-5 个服务 |
| **成本** | $25/月起（包含所有功能） | 各服务单独计费，可能更贵 |
| **灵活性** | 受限于 Supabase 提供的功能 | 每个组件都可以选最佳方案 |
| **调试** | 统一日志和监控 | 需要跨服务排查问题 |
| **上手速度** | 快（统一 API） | 慢（每个服务都要学） |

```
 选一站式 Supabase                     选组合方案
 ═══════════════════════                ═══════════════════════

 · 小团队 / 独立开发者                  · 大团队有专职架构师
 · 追求开发效率                         · 需要每个组件都用业界最强
 · 项目早期 / MVP                       · 超大规模 + 特殊需求
```

---

## 十三、总结与学习路线

### 1. 核心概念速查表

| 概念 | 一句话解释 |
| :--- | :--- |
| **Supabase** | 开源的 Firebase 替代品，基于 PostgreSQL |
| **PostgREST** | 自动把 PostgreSQL 表变成 REST API |
| **GoTrue** | 处理认证的服务器，签发 JWT |
| **RLS** | 行级安全，在数据库层面控制数据访问 |
| **Realtime** | 基于 Phoenix 的实时 WebSocket 服务 |
| **Storage** | S3 兼容的文件存储，支持图片变换 |
| **Edge Functions** | 基于 Deno 的 Serverless 函数 |
| **anon key** | 前端用的 API Key，受 RLS 约束 |
| **service_role key** | 后端用的管理员 Key，绕过 RLS |
| `auth.uid()` | RLS 中获取当前用户 ID 的函数 |
| `.rpc()` | 调用数据库函数的客户端方法 |
| `supabase db push` | 将迁移部署到远程数据库 |

### 2. 推荐学习路径

```
 初学者路线（2-3 天）
 ═══════════════════════════════════════

 第一天：
 ① 创建项目 → ② 用 Table Editor 建表 → ③ 5 分钟 CRUD

 第二天：
 ④ 邮箱认证 → ⑤ 启用 RLS → ⑥ 写第一条策略

 第三天：
 ⑦ 做一个简单的 Todo 应用 → ⑧ 部署上线

 ─────────────────────────────────────

 进阶路线（1-2 周）
 ═══════════════════════════════════════

 ⑨ 实时功能（聊天/协作）
 ⑩ 文件存储（头像上传）
 ⑪ Edge Functions（接入 AI API）
 ⑫ CLI + 本地开发 + 迁移工作流
 ⑬ TypeScript 类型生成
 ⑭ 生产部署 + 安全加固 + 监控
```

### 3. 社区资源

| 资源 | 链接 | 说明 |
| :--- | :--- | :--- |
| **官方文档** | supabase.com/docs | 最权威的参考 |
| **GitHub** | github.com/supabase/supabase | 源码 + Issues |
| **Discord** | discord.supabase.com | 最活跃的社区 |
| **YouTube** | @supabase | 官方教程视频 |
| **Blog** | supabase.com/blog | 最新功能和案例 |
| **Twitter/X** | @supabase | 最新动态 |

---

> 🎉 **恭喜你读完了整篇 Supabase 权威指南！**
>
> 从 PostgreSQL 到认证、从 RLS 到实时功能、从本地开发到生产部署——你现在已经具备了使用 Supabase 构建完整全栈应用的知识体系。
>
> **下一步：打开 supabase.com，创建你的第一个项目，把学到的东西用起来吧！**
