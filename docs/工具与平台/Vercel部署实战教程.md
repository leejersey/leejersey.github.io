# Vercel 部署实战教程

> 从零开始掌握 Vercel：前端项目一键部署、自定义域名、Serverless Functions，以及生产环境最佳实践。

---

## 1. Vercel 是什么？为什么选它

[Vercel](https://vercel.com) 是一个**前端云平台**（Frontend Cloud），由 Next.js 的创建者 Guillermo Rauch 创立。它的核心定位是：**让前端项目的部署像 `git push` 一样简单**。

你可以把 Vercel 理解为：**GitHub Pages 的豪华升级版** —— 不仅能托管静态页面，还支持 Serverless Functions、Edge Computing、数据库集成等后端能力。

### 1.1 Vercel 核心优势

#### 零配置部署

Vercel 能自动检测你的框架类型（Next.js、Vite、Create React App、Nuxt、Astro 等），**无需手动配置构建命令和输出目录**：

```bash
# 传统部署：你需要手动配置一堆东西
npm run build
# 然后上传 dist/ 到服务器...
# 然后配置 Nginx...
# 然后配置 HTTPS...

# Vercel 部署：推送到 GitHub，完事
git push origin main
# → Vercel 自动构建 → 自动部署 → 自动 HTTPS → 自动 CDN
```

#### 全球 Edge Network

Vercel 在全球拥有**数十个边缘节点**，你的静态资源和 Edge Functions 会被自动分发到离用户最近的节点：

```
用户请求 → 就近边缘节点响应（~50ms）
          而不是跨越半个地球去源站（~300ms）
```

> 📝 **实际体验**：部署在 Vercel 上的页面，国外用户（美国、欧洲）访问体验极佳。中国大陆由于没有节点，速度可能不如国内 CDN，后面会讲优化方案。

#### 与 Next.js 深度绑定

Vercel 团队就是 Next.js 的开发团队，所以 Next.js 的所有特性在 Vercel 上都是**一等公民**：

| Next.js 特性 | Vercel 支持 | 说明 |
|--------------|-------------|------|
| SSR (服务端渲染) | ✅ 开箱即用 | 自动部署为 Serverless Function |
| SSG (静态生成) | ✅ 开箱即用 | 构建时生成静态页面 |
| ISR (增量静态再生) | ✅ 独家优化 | 其他平台支持有限 |
| App Router | ✅ 完整支持 | Server Components 原生支持 |
| Middleware | ✅ Edge 运行 | 在边缘节点执行，延迟极低 |
| Image Optimization | ✅ 内置服务 | 自动压缩、格式转换、CDN 缓存 |

> ⚠️ **不只是 Next.js**：Vercel 同样完美支持 Vite、React (CRA)、Vue、Svelte、Astro、Hugo、Hexo 等几乎所有前端框架。Next.js 只是"亲儿子"待遇更好。

#### 开发者体验（DX）

- **Preview Deployments**：每个 PR 自动生成独立预览链接，团队成员可以直接在线查看改动效果
- **即时回滚**：点一下按钮回滚到任意历史版本，不用重新部署
- **自动 HTTPS**：绑定域名后自动签发和续期 SSL 证书（Let's Encrypt）
- **集成生态**：一键对接常用数据库（Vercel Postgres、Neon）、分析工具、CMS 等

### 1.2 免费额度与付费方案

Vercel 的 **Hobby（免费）方案** 对个人开发者非常友好，足以覆盖大多数个人项目和学习场景：

| 资源 | Hobby（免费） | Pro（$20/月） | Enterprise |
|------|---------------|---------------|------------|
| 部署次数 | 每天 100 次 | 每天 6000 次 | 无限 |
| 带宽 | 100 GB/月 | 1 TB/月 | 自定义 |
| Serverless 执行时长 | 100 GB-Hours/月 | 1000 GB-Hours/月 | 自定义 |
| Serverless 函数超时 | 10 秒 | 60 秒 | 900 秒 |
| Edge Function 执行 | 500,000 次/月 | 1,000,000 次/月 | 自定义 |
| 构建时长 | 每次最长 45 分钟 | 每次最长 45 分钟 | 自定义 |
| 团队成员 | 仅个人 | 无限 | 无限 |
| 商业用途 | ❌ 不允许 | ✅ 允许 | ✅ 允许 |

> ⚠️ **注意**：Hobby 方案**禁止商业用途**。如果你的项目会产生收入（哪怕是个人博客挂了广告），严格来说需要升级到 Pro。实际上 Vercel 对个人小项目不会主动审查，但了解规则很重要。

#### 什么时候需要升级到 Pro？

- 你的网站**月流量超过 100 GB**（大约 10 万次页面访问）
- 你的 Serverless Function 需要**超过 10 秒**的执行时间（比如调用 AI API）
- 你需要**团队协作**（多人共享同一个项目）
- 你的项目有**商业用途**

> 📝 **个人开发者建议**：先用 Hobby 方案，等流量或需求超出限制再升级。$20/月 的 Pro 方案在同类产品中也算合理。
### 1.3 Vercel vs Netlify vs Cloudflare Pages

这三者是目前最主流的前端部署平台，各有侧重：

| 维度 | Vercel | Netlify | Cloudflare Pages |
|------|--------|---------|-----------------|
| **核心优势** | Next.js 亲儿子，DX 极致 | 表单/身份认证等内置功能多 | 全球最大 CDN 网络，速度快 |
| **框架支持** | 全部主流框架 | 全部主流框架 | 全部主流框架 |
| **Serverless** | ✅ Node/Python/Go/Ruby | ✅ 仅 Node/Go | ✅ Workers（V8 隔离，非 Node） |
| **Edge Computing** | Edge Functions | Edge Functions | Workers（原生优势） |
| **免费带宽** | 100 GB/月 | 100 GB/月 | 无限 |
| **免费构建时长** | 6000 分钟/月 | 300 分钟/月 | 500 次/月 |
| **中国大陆速度** | 一般（无国内节点） | 一般（无国内节点） | **较好**（有香港等亚洲节点） |
| **自定义域名** | ✅ 免费 | ✅ 免费 | ✅ 免费 |
| **价格** | Hobby 免费 / Pro $20 | Starter 免费 / Pro $19 | Free / Pro $20 |

#### 怎么选？

```
你用 Next.js？
  └→ 选 Vercel（原生支持最好，ISR/Middleware 零配置）

你需要极致的全球访问速度？
  └→ 选 Cloudflare Pages（CDN 网络覆盖最广，带宽免费）

你需要内置表单处理、身份认证？
  └→ 选 Netlify（内置 Forms、Identity 等功能）

你是纯静态站点（博客/文档）？
  └→ 三个都行，选哪个都不会错
```

> 📝 **本教程的选择**：我们选 Vercel，因为它的**部署体验是三者中最流畅的**，而且与 Next.js / React 生态结合最紧密。如果你的用户主要在中国大陆，可以考虑 Cloudflare Pages 或搭配国内 CDN 使用。

---

## 2. 前置准备

在正式部署之前，我们需要准备三样东西：Vercel 账号、CLI 工具、以及一个用于测试的 Demo 项目。

### 2.1 注册 Vercel 账号

#### 注册流程

1. 打开 [vercel.com](https://vercel.com)，点击右上角 **Sign Up**
2. 选择 **Continue with GitHub**（强烈推荐，因为后续部署要用 GitHub 仓库）
3. 授权 Vercel 访问你的 GitHub 账号
4. 选择 **Hobby**（免费方案），填写你的名字，完成注册

> 📝 **为什么推荐 GitHub 登录？** Vercel 的核心部署方式就是与 Git 仓库集成。用 GitHub 登录后，导入仓库时不需要再次授权，体验最丝滑。当然你也可以用 GitLab、Bitbucket 或邮箱注册。

#### 注册后你会看到什么

注册完成后进入 Dashboard（仪表盘），这里是你管理所有项目的地方：

```
┌─────────────────────────────────────────────────┐
│  Vercel Dashboard                               │
├─────────────────────────────────────────────────┤
│                                                 │
│  Overview    Projects    Storage    Settings     │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │  + Add New... → Project                 │    │
│  │               → Domain                  │    │
│  │               → Store                   │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  Your Projects:                                 │
│  （空的，等待你的第一个部署）                        │
│                                                 │
└─────────────────────────────────────────────────┘
```

几个关键区域：

| 区域 | 用途 |
|------|------|
| **Overview** | 所有项目的总览，包括最近的部署状态 |
| **Projects** | 管理你的每个项目（查看部署、日志、环境变量等） |
| **Storage** | Vercel 提供的数据库/存储服务（KV、Postgres、Blob） |
| **Settings** | 账号设置、域名管理、用量统计 |

> ⚠️ **Hobby 方案限制**：一个账号最多创建 **200 个项目**，每个项目最多绑定 **50 个域名**。对个人开发者来说绰绰有余。

### 2.2 安装 Vercel CLI

Vercel CLI 是官方命令行工具，用于在终端中部署、预览和管理项目。

#### 安装

```bash
# 使用 npm 全局安装（推荐）
npm install -g vercel

# 或者用 pnpm
pnpm add -g vercel

# 验证安装
vercel --version
# → Vercel CLI 39.x.x
```

> 📝 **Node.js 版本要求**：Vercel CLI 需要 Node.js 18.x 或更高版本。运行 `node -v` 检查你的版本。

#### 登录

```bash
# 登录到 Vercel（会打开浏览器授权）
vercel login

# 如果你用 GitHub 注册的，选择 "Continue with GitHub"
# 授权完成后终端显示：
# → Congratulations! You are now logged in.
```

> ⚠️ **CI/CD 场景**：在服务器或 CI 环境中，无法打开浏览器。可以用 Token 登录：
> ```bash
> # 在 https://vercel.com/account/tokens 创建 Token
> vercel login --token YOUR_TOKEN
> ```

#### 常用命令速查

先简单了解几个核心命令，后面章节会逐一详解：

| 命令 | 用途 | 示例 |
|------|------|------|
| `vercel` | 部署到预览环境 | `vercel` |
| `vercel --prod` | 部署到生产环境 | `vercel --prod` |
| `vercel dev` | 本地开发（模拟 Vercel 环境） | `vercel dev` |
| `vercel env` | 管理环境变量 | `vercel env add SECRET` |
| `vercel logs` | 查看部署日志 | `vercel logs your-project.vercel.app` |
| `vercel domains` | 管理域名 | `vercel domains ls` |

> 📝 **`vercel` vs `vc`**：`vc` 是 `vercel` 的短别名，功能完全一样。你可以用 `vc --prod` 代替 `vercel --prod`，少敲几个字。
### 2.3 准备一个 Demo 项目

我们需要一个真实的前端项目来练手。这里用 **Vite + React** 快速创建一个 Demo：

#### 创建项目

```bash
# 用 Vite 创建 React 项目
npm create vite@latest vercel-demo -- --template react

# 进入项目目录
cd vercel-demo

# 安装依赖
npm install

# 本地运行，确认项目正常
npm run dev
# → 浏览器打开 http://localhost:5173，看到 Vite + React 的默认页面
```

#### 推送到 GitHub

Vercel 的 Git 集成部署需要代码在 GitHub 上。如果你还没有仓库，按以下步骤创建：

```bash
# 1. 在 GitHub 上创建一个新仓库（名字：vercel-demo）
#    不勾选 README、.gitignore 等选项

# 2. 在本地项目中初始化 Git 并推送
cd vercel-demo
git init
git add .
git commit -m "feat: init vite react project"
git branch -M main
git remote add origin https://github.com/你的用户名/vercel-demo.git
git push -u origin main
```

#### 项目结构预览

```
vercel-demo/
├── public/
│   └── vite.svg
├── src/
│   ├── App.jsx        # 主组件
│   ├── App.css        # 样式
│   ├── main.jsx       # 入口文件
│   └── index.css      # 全局样式
├── index.html         # HTML 模板
├── package.json       # 依赖和脚本
└── vite.config.js     # Vite 配置
```

> 📝 **不想用 React？** 完全没问题。Vercel 支持几乎所有前端框架。你可以用 `npm create vite@latest -- --template vue` 创建 Vue 项目，或者直接用一个纯 HTML 文件夹。后续步骤完全一样。

> ⚠️ **确保项目能正常构建**：在部署前，先在本地运行 `npm run build`，确认没有构建错误。Vercel 的构建环境和你本地一致，本地能构建成功，Vercel 上 99% 也能成功。

准备工作完成，接下来我们正式开始部署 🚀

---

## 3. 部署方式一：Git 集成部署（推荐）

Git 集成是 Vercel 最核心的部署方式，也是官方最推荐的工作流。它的逻辑非常简单：**你 push 代码到 GitHub，Vercel 自动帮你构建和部署**。

```
开发者 → git push → GitHub → Vercel 自动检测 → 构建 → 部署 → 上线
                                                            ↓
                                            https://your-project.vercel.app
```

### 3.1 导入 GitHub 仓库

#### 在 Vercel Dashboard 中导入

1. 登录 [vercel.com](https://vercel.com)，进入 Dashboard
2. 点击 **Add New... → Project**
3. 在 **Import Git Repository** 页面，你会看到你 GitHub 上的所有仓库
4. 找到 `vercel-demo`，点击 **Import**

> 📝 **看不到仓库？** 如果列表中没有你要的仓库，点击 **Adjust GitHub App Permissions**，在 GitHub 设置中授权 Vercel 访问该仓库（可以选择授权所有仓库或指定仓库）。

#### 配置项目设置

导入后会进入配置页面，Vercel 会自动检测你的框架类型：

```
┌─────────────────────────────────────────────────┐
│  Configure Project                              │
├─────────────────────────────────────────────────┤
│                                                 │
│  Project Name: vercel-demo                      │
│                                                 │
│  Framework Preset: [Vite] ← 自动检测到           │
│                                                 │
│  Root Directory: ./                             │
│                                                 │
│  Build and Output Settings:                     │
│    Build Command:    npm run build  (默认)       │
│    Output Directory: dist           (默认)       │
│    Install Command:  npm install    (默认)       │
│                                                 │
│  Environment Variables:                         │
│    （暂时不需要，后面章节会讲）                      │
│                                                 │
│  [Deploy] ← 点这个按钮                           │
│                                                 │
└─────────────────────────────────────────────────┘
```

大多数情况下，**默认配置就够了**，直接点 **Deploy** 开始部署。

#### Vercel 支持的框架自动检测

Vercel 能识别以下框架并自动设置构建命令：

| 框架 | 构建命令 | 输出目录 |
|------|----------|----------|
| Vite | `npm run build` | `dist` |
| Next.js | `next build` | `.next` |
| Create React App | `react-scripts build` | `build` |
| Vue CLI | `vue-cli-service build` | `dist` |
| Nuxt | `nuxt build` | `.output` |
| Astro | `astro build` | `dist` |
| SvelteKit | `vite build` | `.svelte-kit` |

> ⚠️ **Monorepo 项目**：如果你的仓库是 Monorepo（一个仓库包含多个项目），需要在 **Root Directory** 中指定子目录路径，比如 `packages/frontend`。否则 Vercel 会在仓库根目录找不到 `package.json` 而构建失败。

#### 首次部署过程

点击 Deploy 后，你会看到实时的构建日志：

```bash
# Vercel 构建日志（简化版）
Cloning github.com/你的用户名/vercel-demo (Branch: main)
Cloning completed: 1.2s

Installing dependencies...
npm warn deprecated...
added 214 packages in 8s

Building project...
vite v6.x.x building for production...
✓ 34 modules transformed.
dist/index.html                  0.45 kB │ gzip:  0.29 kB
dist/assets/index-DiwrgTda.css   1.39 kB │ gzip:  0.72 kB
dist/assets/index-l0sNRNKZ.js  143.36 kB │ gzip: 46.09 kB
✓ built in 1.23s

Deployment completed!
```

构建成功后，Vercel 会分配一个默认域名：

```
https://vercel-demo.vercel.app          ← 生产环境 URL
https://vercel-demo-xxxxx.vercel.app    ← 本次部署的唯一 URL
```

> 📝 **两个 URL 的区别**：
> - **生产 URL**（`xxx.vercel.app`）：始终指向最新的生产部署
> - **部署 URL**（`xxx-xxxxx.vercel.app`）：指向这次特定的部署，永远不会变。适合用来回溯历史版本

恭喜，你的第一个 Vercel 项目已经上线了 🎉 在浏览器中打开这个 URL，你应该能看到 Vite + React 的默认页面。

### 3.2 构建配置详解

导入成功后，后续的部署流程就是全自动的。理解这个流程有助于排查问题。

#### 自动部署触发机制

```
git push origin main  →  触发生产部署（Production Deployment）
git push origin feature-x  →  触发预览部署（Preview Deployment）
创建 Pull Request  →  触发预览部署 + 在 PR 中显示预览链接
```

| 触发事件 | 部署类型 | URL 格式 |
|----------|----------|----------|
| Push 到 `main`（或默认分支） | 🟢 Production | `your-project.vercel.app` |
| Push 到其他分支 | 🟡 Preview | `your-project-xxx-username.vercel.app` |
| 创建 / 更新 Pull Request | 🟡 Preview | 同上，且自动评论在 PR 中 |

> 📝 **生产分支可以自定义**：默认是 `main`，但你可以在 **Project Settings → Git → Production Branch** 中改成其他分支，比如 `production` 或 `release`。

#### 覆盖构建设置

有时候默认检测的配置不够用，你可以在 **Project Settings → General → Build & Development Settings** 中手动覆盖：

```
Build Command:       npm run build:prod    ← 自定义构建命令
Output Directory:    build                  ← 自定义输出目录
Install Command:     yarn install           ← 换用 yarn 安装
Development Command: npm run dev            ← 本地 vercel dev 时使用
```

常见需要覆盖的场景：

| 场景 | 修改项 | 示例 |
|------|--------|------|
| 多环境构建脚本 | Build Command | `npm run build:staging` |
| CRA 项目输出目录 | Output Directory | `build`（而不是 `dist`） |
| 使用 pnpm | Install Command | `pnpm install` |
| Monorepo 子项目 | Root Directory | `apps/web` |

#### 忽略构建（Ignored Build Step）

如果某些 push 不需要触发重新部署（比如只改了 README），可以配置忽略规则：

```bash
# 在 Project Settings → Git → Ignored Build Step 中填入：
git diff --quiet HEAD^ HEAD ./src ./public

# 含义：如果 src/ 和 public/ 目录没有变化，就跳过本次构建
# → 节省构建次数（免费方案每天 100 次）
```

> ⚠️ **Hobby 方案注意**：每天最多 100 次部署。如果你频繁 push（比如调试 CI），很容易达到限制。配置 Ignored Build Step 可以有效节省配额。
### 3.3 Preview Deployments（PR 预览）

Preview Deployments 是 Vercel 最强大的协作功能之一。每当你创建或更新一个 Pull Request，Vercel 会自动构建该分支并生成一个**独立的预览链接**。

#### 工作流演示

```bash
# 1. 创建功能分支
git checkout -b feature/new-header

# 2. 修改代码
# （编辑 src/App.jsx，添加一个新的 Header 组件）

# 3. 提交并推送
git add .
git commit -m "feat: add new header component"
git push origin feature/new-header

# 4. 在 GitHub 上创建 Pull Request
#    → Vercel 自动触发预览构建
```

#### Vercel Bot 自动评论

PR 创建后，Vercel Bot 会在 PR 中自动发一条评论：

```
┌─────────────────────────────────────────────────┐
│  🔍 vercel bot                                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  The latest updates on your projects:           │
│                                                 │
│  ✅ vercel-demo – Ready                         │
│                                                 │
│  🔗 Preview: https://vercel-demo-abc123.vercel.app │
│  📝 Built with commit abc1234                   │
│  🕐 Dec 25, 2025 at 10:30 AM (1m 23s)          │
│                                                 │
│  [Visit Preview] [Inspect Deployment]           │
│                                                 │
└─────────────────────────────────────────────────┘
```

团队成员可以**直接点击预览链接查看效果**，不需要拉取代码、安装依赖、本地运行。

#### Preview vs Production 对比

| 维度 | Preview | Production |
|------|---------|------------|
| 触发方式 | Push 到非生产分支 / 创建 PR | Push 到生产分支（`main`） |
| URL | 每次部署唯一的随机 URL | 固定的项目域名 |
| 环境变量 | 使用 Preview 环境变量 | 使用 Production 环境变量 |
| 搜索引擎索引 | ❌ 自动添加 `X-Robots-Tag: noindex` | ✅ 允许索引 |
| 适用场景 | Code Review、QA 测试、设计验收 | 面向用户的正式版本 |

> 📝 **Preview 的实际价值**：这个功能看似简单，但在团队协作中价值巨大。设计师可以直接看到 UI 改动、PM 可以验证需求、QA 可以提前测试——所有人都不需要任何技术操作，只需点击一个链接。

#### 保护 Preview Deployments

默认情况下，Preview URL 是公开的，任何人都可以访问。如果你的预览环境包含敏感内容：

```
Project Settings → General → Vercel Authentication
→ 开启 "Protection Bypass for Preview Deployments"
→ 只有 Vercel 团队成员才能访问预览环境
```

> ⚠️ **Hobby 方案限制**：Vercel Authentication 保护功能仅在 Pro 及以上方案可用。Hobby 方案的 Preview URL 始终是公开的（但 URL 是随机的，不容易被猜到）。

---

## 4. 部署方式二：CLI 手动部署

除了 Git 集成，Vercel 还支持通过 CLI 直接从本地部署。这种方式**不需要代码在 GitHub 上**，适合快速原型验证、临时分享、或不希望关联 Git 仓库的场景。

### 4.1 首次部署

#### 初始化并部署

确保你已完成 2.2 节的 CLI 安装和登录，然后在项目目录中运行：

```bash
cd vercel-demo

# 首次运行 vercel，会进入交互式设置
vercel
```

CLI 会询问你一系列问题：

```bash
? Set up and deploy "~/vercel-demo"? [Y/n]
→ Y

? Which scope do you want to deploy to?
→ 选择你的账号名

? Link to existing project?
→ N（首次部署选 No，创建新项目）

? What's your project's name?
→ vercel-demo（直接回车用默认值）

? In which directory is your code located?
→ ./（直接回车）

? Want to modify these settings? [y/N]
→ N（使用自动检测的框架配置）
```

设置完成后，Vercel 会自动构建并部署到**预览环境**：

```bash
🔗  Linked to your-username/vercel-demo
🔍  Inspect: https://vercel.com/your-username/vercel-demo/xxx
✅  Preview: https://vercel-demo-xxx.vercel.app

# 注意：这是 Preview 部署，不是 Production！
```

> 📝 **首次 `vercel` 命令做了什么？** 三件事：① 在 Vercel 上创建项目 ② 在本地生成 `.vercel/` 目录（保存项目链接信息）③ 触发一次 Preview 部署。后续再运行 `vercel`，会跳过创建步骤，直接部署。

#### `.vercel/` 目录

首次部署后，项目根目录下会生成一个 `.vercel/` 文件夹：

```
vercel-demo/
├── .vercel/
│   └── project.json    # 保存项目 ID 和组织 ID
├── src/
├── package.json
└── ...
```

```json
// .vercel/project.json
{
  "projectId": "prj_xxxxxxxxxxxx",
  "orgId": "team_xxxxxxxxxxxx"
}
```

> ⚠️ **安全提示**：`.vercel/` 目录包含你的项目 ID。建议把它加入 `.gitignore`（Vite 和 Next.js 的模板默认已包含）。虽然泄露 ID 不会直接造成安全问题，但也没必要公开。

### 4.2 生产环境部署

`vercel` 命令默认部署到预览环境。要部署到**生产环境**（更新你的正式 URL），需要加 `--prod` 参数：

```bash
# 部署到生产环境
vercel --prod

# 输出：
🔗  Linked to your-username/vercel-demo
🔍  Inspect: https://vercel.com/your-username/vercel-demo/xxx
✅  Production: https://vercel-demo.vercel.app
```

#### Preview vs Production 部署命令对比

```bash
vercel              # → Preview 部署（测试用，不影响正式 URL）
vercel --prod       # → Production 部署（更新正式 URL）
```

这个设计是**安全防护**：防止你随手一个 `vercel` 就把未经验证的代码推到生产环境。正确的工作流是：

```
vercel         → 预览环境验证 → 确认没问题 → vercel --prod
```

#### 回滚到历史版本

如果生产环境出了问题，可以快速回滚：

```bash
# 方法 1：在 Dashboard 中点击 "Instant Rollback"
# Project → Deployments → 找到之前正常的部署 → ⋯ → Promote to Production

# 方法 2：用 CLI 回滚
vercel rollback
# → 选择要回滚到的部署版本
```

> 📝 **回滚 ≠ 重新部署**：回滚是瞬间完成的（~1 秒），因为只是把流量切换到之前已构建好的版本。不需要重新构建，所以不会消耗构建时长配额。

#### 部署特定目录

如果你想直接部署一个已经构建好的静态目录（不走 `npm run build`）：

```bash
# 先在本地构建
npm run build

# 直接部署 dist/ 目录（跳过 Vercel 的构建步骤）
vercel deploy ./dist --prod

# 适用场景：本地构建有特殊依赖，或者想加速部署
```
### 4.3 CLI vs Git 集成：何时用哪个

两种部署方式各有适用场景，不是"二选一"的关系：

| 维度 | Git 集成部署 | CLI 手动部署 |
|------|-------------|-------------|
| **触发方式** | 自动（`git push` 触发） | 手动（运行 `vercel` 命令） |
| **需要 GitHub？** | ✅ 必须有 Git 仓库 | ❌ 不需要 |
| **Preview 预览** | ✅ PR 自动预览 + Bot 评论 | ✅ 有预览，但没有 PR 关联 |
| **团队协作** | ✅ 完整的 CI/CD 工作流 | ⚠️ 仅限本地操作者 |
| **回滚** | ✅ 任意 commit 对应一个部署 | ✅ 历史部署列表 |
| **适用场景** | 正式项目、团队开发 | 原型验证、临时分享、本地测试 |

#### 推荐策略

```
正式项目、需要长期维护？
  └→ 用 Git 集成（推送即部署，PR 自动预览，完整的部署历史）

临时 Demo、快速验证、还没建 Git 仓库？
  └→ 用 CLI 部署（30 秒上线，分享链接给别人看效果）

两者混用？
  └→ 完全可以。同一个项目可以既绑定 GitHub 自动部署，
     也支持用 CLI 手动部署。互不冲突。
```

> 📝 **实际开发中**：大多数开发者的日常工作流是 Git 集成部署。CLI 更多用于初始化项目、调试部署配置、或在没有 Git 仓库时快速验证想法。

---

## 5. 环境变量与项目配置

大多数真实项目都需要配置 API 密钥、数据库地址等敏感信息，以及 URL 重写规则等部署行为。Vercel 通过 `vercel.json` 和环境变量系统来管理这些配置。

### 5.1 vercel.json 配置详解

`vercel.json` 是项目级配置文件，放在项目根目录。它控制 Vercel 的构建和部署行为。

#### 基础模板

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [],
  "redirects": [],
  "headers": []
}
```

> 📝 **大部分情况不需要 vercel.json**：如果你用的是 Vercel 支持的框架（Vite、Next.js 等），自动检测就够了。只有需要自定义行为时才创建这个文件。

#### 常用配置项速查

| 配置项 | 类型 | 用途 | 示例 |
|--------|------|------|------|
| `buildCommand` | string | 覆盖构建命令 | `"npm run build:prod"` |
| `outputDirectory` | string | 覆盖输出目录 | `"build"` |
| `installCommand` | string | 覆盖安装命令 | `"pnpm install"` |
| `framework` | string | 指定框架（覆盖自动检测） | `"vite"` |
| `rewrites` | array | URL 重写规则 | 见 5.3 节 |
| `redirects` | array | URL 重定向规则 | 见 5.3 节 |
| `headers` | array | 自定义响应头 | 见下方示例 |
| `cleanUrls` | boolean | 去掉 URL 中的 `.html` 后缀 | `true` |
| `trailingSlash` | boolean | URL 末尾是否加 `/` | `false` |

#### 实用配置示例：自定义响应头

```json
{
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" },
        { "key": "Access-Control-Allow-Methods", "value": "GET,POST,OPTIONS" }
      ]
    },
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" }
      ]
    }
  ]
}
```

> ⚠️ **vercel.json vs Dashboard 设置**：两者都能配置构建命令、输出目录等。`vercel.json` 的优先级**高于** Dashboard。建议统一用一种方式管理，避免混乱。推荐用 `vercel.json`，因为它可以跟着代码走（版本控制）。

### 5.2 环境变量管理

Vercel 的环境变量系统有一个核心设计：**三种环境隔离**。

#### 三种环境

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Development │    │   Preview    │    │  Production  │
│  本地开发环境   │    │  预览部署环境  │    │  生产部署环境  │
│              │    │              │    │              │
│ vercel dev   │    │ vercel       │    │ vercel --prod│
│ 或 npm run dev│    │ (PR 自动触发) │    │ (push main)  │
└──────────────┘    └──────────────┘    └──────────────┘
```

每个环境变量可以单独设置在哪些环境中生效：

| 变量 | Development | Preview | Production | 示例场景 |
|------|:-----------:|:-------:|:----------:|----------|
| `DATABASE_URL` | ✅ | ✅ | ✅ | 三个环境用同一个数据库 |
| `API_KEY` | ❌ | ✅ | ✅ | 本地用 mock，线上用真实 API |
| `DEBUG` | ✅ | ✅ | ❌ | 生产环境不开调试 |

#### 方式一：Dashboard 管理（推荐）

```
Project Settings → Environment Variables

┌────────────────────────────────────────────┐
│  Add New                                   │
│                                            │
│  Key:   DATABASE_URL                       │
│  Value: postgres://user:pass@host/db       │
│                                            │
│  Environments:                             │
│    ☑ Production  ☑ Preview  ☐ Development  │
│                                            │
│  [Save]                                    │
└────────────────────────────────────────────┘
```

> ⚠️ **修改环境变量后需要重新部署才能生效**。Vercel 不会自动重新部署，你需要手动触发一次（push 一次或在 Deployments 页面点 Redeploy）。

#### 方式二：CLI 管理

```bash
# 添加环境变量
vercel env add DATABASE_URL
# → 交互式选择环境（Production/Preview/Development）
# → 输入值

# 查看所有环境变量
vercel env ls

# 拉取环境变量到本地 .env 文件（用于 vercel dev）
vercel env pull .env.local
# → 生成 .env.local 文件，包含 Development 环境的所有变量

# 删除环境变量
vercel env rm DATABASE_URL
```

> 📝 **`vercel env pull` 的妙用**：团队开发时，新成员 clone 项目后，运行 `vercel link` + `vercel env pull` 就能拿到所有开发环境变量，不需要手动复制 `.env` 文件。

#### 前端项目的环境变量暴露规则

前端框架对环境变量有**安全前缀**要求，只有特定前缀的变量才会被打包到客户端代码中：

| 框架 | 前缀 | 示例 |
|------|------|------|
| Vite | `VITE_` | `VITE_API_URL` |
| Next.js | `NEXT_PUBLIC_` | `NEXT_PUBLIC_API_URL` |
| Create React App | `REACT_APP_` | `REACT_APP_API_URL` |

```javascript
// Vite 项目中使用环境变量
const apiUrl = import.meta.env.VITE_API_URL;

// Next.js 项目中使用环境变量
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
```

> ⚠️ **绝对不要在前端暴露敏感信息**：`VITE_` / `NEXT_PUBLIC_` 前缀的变量会被打包到 JavaScript 中，任何人都能在浏览器 DevTools 中看到。数据库密码、API Secret 等敏感信息**只能**用在 Serverless Functions 中（不带前缀），绝不能加 `VITE_` 前缀。
### 5.3 重写（Rewrites）与重定向（Redirects）

这两个功能在 `vercel.json` 中配置，是处理 URL 路由的利器。

#### Rewrites vs Redirects 的区别

```
Rewrite（重写）：URL 不变，内容变
  用户访问 /api/users → 实际请求 https://backend.example.com/users
  浏览器地址栏仍然显示 /api/users

Redirect（重定向）：URL 变，跳转过去
  用户访问 /old-page → 浏览器跳转到 /new-page
  浏览器地址栏变成 /new-page
```

| 特性 | Rewrite | Redirect |
|------|---------|----------|
| 浏览器 URL | 不变 | 变化 |
| HTTP 状态码 | 200 | 301/302/307/308 |
| 典型用途 | API 代理、SPA 路由 | 旧页面跳转、域名统一 |
| 对用户可见？ | ❌ 透明的 | ✅ 能看到 URL 变化 |

#### 实用场景 1：SPA 客户端路由

React / Vue 等 SPA 项目用的是客户端路由。如果用户直接访问 `/about`，服务器找不到 `about.html` 会返回 404。解决方案：

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

> 📝 **原理**：所有路径都指向 `index.html`，让前端路由（React Router / Vue Router）接管。这和 Nginx 的 `try_files $uri /index.html` 效果一样。

#### 实用场景 2：API 代理（解决跨域）

前端调用后端 API 时经常遇到跨域问题。用 Rewrite 做代理可以完美解决：

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend.example.com/api/:path*"
    }
  ]
}
```

```javascript
// 前端代码：直接请求同域 /api，不会跨域
fetch('/api/users')
// → Vercel 重写为 https://your-backend.example.com/api/users
// → 对浏览器来说是同域请求，不触发 CORS
```

> ⚠️ **代理的局限**：Rewrite 代理有 **10 秒超时**（Hobby 方案）。如果后端接口响应很慢（比如 AI 生成），可能会超时。这种场景建议用 Serverless Functions 或直接处理 CORS。

#### 实用场景 3：旧页面 301 重定向（SEO 友好）

网站改版后，旧 URL 需要跳转到新 URL，同时保留 SEO 权重：

```json
{
  "redirects": [
    {
      "source": "/blog/:slug",
      "destination": "/posts/:slug",
      "statusCode": 301
    },
    {
      "source": "/old-about",
      "destination": "/about",
      "statusCode": 301
    }
  ]
}
```

> 📝 **301 vs 308**：`301` 是永久重定向（搜索引擎会更新索引），`308` 也是永久重定向但保留请求方法（POST 不会变成 GET）。一般页面跳转用 `301`，API 跳转用 `308`。

---

## 6. Serverless Functions

Vercel 不只是静态托管平台——它还支持**后端逻辑**。通过 Serverless Functions，你可以在 Vercel 上运行 Node.js、Python、Go、Ruby 代码，处理 API 请求、数据库操作、第三方服务调用等。

```
前端（静态资源）     后端（Serverless Functions）
┌──────────┐       ┌──────────────────┐
│  React   │  →→→  │  /api/users.js   │  →→→  数据库 / 第三方 API
│  Vue     │       │  /api/auth.js    │
│  HTML    │       │  /api/webhook.py │
└──────────┘       └──────────────────┘
   dist/               api/
```

### 6.1 创建第一个 Serverless Function

#### 约定式路由：`api/` 目录

Vercel 的 Serverless Functions 遵循**文件即路由**的约定：把文件放在项目根目录的 `api/` 文件夹中，文件路径就是 API 路径。

```
项目根目录/
├── api/
│   ├── hello.js        → GET/POST /api/hello
│   ├── users.js        → GET/POST /api/users
│   └── auth/
│       ├── login.js    → POST /api/auth/login
│       └── logout.js   → POST /api/auth/logout
├── src/
├── package.json
└── ...
```

#### 编写一个 Hello World API

创建 `api/hello.js`：

```javascript
// api/hello.js
export default function handler(req, res) {
  const { name = 'World' } = req.query;

  res.status(200).json({
    message: `Hello, ${name}!`,
    method: req.method,
    timestamp: new Date().toISOString()
  });
}
```

部署后，访问 `https://your-project.vercel.app/api/hello?name=Vercel`，返回：

```json
{
  "message": "Hello, Vercel!",
  "method": "GET",
  "timestamp": "2026-04-02T10:00:00.000Z"
}
```

> 📝 **零配置**：不需要在 `vercel.json` 中注册路由，也不需要 Express 框架。放到 `api/` 目录就自动变成 API 端点。

#### Python 版本

Vercel 也支持 Python：

```python
# api/hello.py
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'message': 'Hello from Python!',
            'runtime': 'Python 3.9'
        }).encode())
```

> ⚠️ **Python 的限制**：Vercel 的 Python 运行时使用的是 WSGI 接口，不支持 FastAPI / Flask 的路由。每个 `.py` 文件就是一个独立的函数。如果需要完整的 Python Web 框架，建议用腾讯云 SCF 或 AWS Lambda。

#### 支持的运行时

| 运行时 | 文件后缀 | 版本 |
|--------|----------|------|
| Node.js | `.js` / `.ts` | 18.x / 20.x |
| Python | `.py` | 3.9 |
| Go | `.go` | 1.21 |
| Ruby | `.rb` | 3.2 |

### 6.2 路由与参数处理

#### 动态路由

和 Next.js 一样，Vercel 的 Serverless Functions 支持**文件名动态路由**：

```
api/
├── users/
│   ├── index.js         → /api/users
│   └── [id].js          → /api/users/123、/api/users/abc
├── posts/
│   └── [...slug].js     → /api/posts/a/b/c（Catch-all 路由）
```

```javascript
// api/users/[id].js
export default function handler(req, res) {
  const { id } = req.query;  // 从 URL 中获取动态参数

  res.status(200).json({
    userId: id,
    message: `正在查询用户 ${id} 的信息`
  });
}

// 访问 /api/users/42 → { userId: "42", message: "正在查询用户 42 的信息" }
```

#### 请求方法分发

一个函数文件会接收**所有 HTTP 方法**（GET、POST、PUT、DELETE），你需要手动分发：

```javascript
// api/users.js - 完整的 CRUD 端点
export default function handler(req, res) {
  switch (req.method) {
    case 'GET':
      // 查询用户列表
      res.status(200).json({ users: [] });
      break;

    case 'POST':
      // 创建用户（req.body 自动解析 JSON）
      const { name, email } = req.body;
      res.status(201).json({ message: '用户创建成功', name, email });
      break;

    case 'DELETE':
      res.status(200).json({ message: '用户已删除' });
      break;

    default:
      res.setHeader('Allow', ['GET', 'POST', 'DELETE']);
      res.status(405).json({ error: `不支持 ${req.method} 方法` });
  }
}
```

> 📝 **`req.body` 自动解析**：Vercel 会自动解析 `application/json` 和 `application/x-www-form-urlencoded` 类型的请求体。不需要 `body-parser` 中间件。

#### CORS 跨域处理

如果前端和 API 不在同一个域名，需要处理 CORS：

```javascript
// api/data.js - 带 CORS 的 API
export default function handler(req, res) {
  // 设置 CORS 头
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // 处理 OPTIONS 预检请求
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // 正常业务逻辑
  res.status(200).json({ data: '跨域请求成功' });
}
```

> ⚠️ **更好的方案**：如果前端也部署在同一个 Vercel 项目中，可以用 5.3 节的 Rewrite 代理来避免跨域，不需要手动处理 CORS。
### 6.3 Edge Functions vs Serverless Functions

Vercel 提供两种后端运行方式。理解它们的区别有助于选对方案。

#### 运行原理对比

```
Serverless Function（传统）：
  用户请求 → 最近的 CDN 节点 → 转发到固定区域的服务器（如 美东 us-east-1）→ 响应
                                    ↑ 冷启动：首次调用需要启动容器（~200ms）

Edge Function（边缘计算）：
  用户请求 → 最近的边缘节点直接执行代码 → 响应
                ↑ 无冷启动（V8 Isolate，~1ms 启动）
                ↑ 全球数十个节点，就近执行
```

#### 核心区别

| 维度 | Serverless Functions | Edge Functions |
|------|---------------------|----------------|
| **运行时** | Node.js（完整） | Edge Runtime（V8 Isolate，精简） |
| **冷启动** | ~200-500ms | ~1ms（几乎无感知） |
| **执行位置** | 固定区域（如 us-east-1） | 全球边缘节点（就近执行） |
| **超时时间** | 10s（Hobby）/ 60s（Pro） | 25s（统一） |
| **内存限制** | 1024 MB | 128 MB |
| **Node.js API** | ✅ 完整支持 | ⚠️ 部分支持（无 `fs`、`child_process` 等） |
| **npm 包** | ✅ 任意 npm 包 | ⚠️ 仅支持 Edge 兼容的包 |
| **适用场景** | 数据库查询、复杂计算、第三方 API | 认证、重定向、A/B 测试、轻量 API |

#### Edge Function 写法

```javascript
// api/hello.js（Edge Function 版本）
export const config = {
  runtime: 'edge',  // ← 加这一行就变成 Edge Function
};

export default function handler(req) {
  // 注意：Edge Function 使用 Web 标准 API（Request/Response）
  // 而不是 Node.js 的 req/res
  const { searchParams } = new URL(req.url);
  const name = searchParams.get('name') || 'World';

  return new Response(
    JSON.stringify({ message: `Hello, ${name}!` }),
    {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}
```

> 📝 **API 风格差异**：Serverless Function 用 Node.js 的 `(req, res) => {}` 风格；Edge Function 用 Web 标准的 `(request) => Response` 风格。如果你熟悉 Cloudflare Workers，Edge Function 的写法几乎一样。

#### 怎么选？

```
你的函数需要访问数据库（PostgreSQL、MongoDB 等）？
  └→ 用 Serverless Function（Edge 的数据库支持有限）

你的函数需要完整的 Node.js API（fs、crypto 等）？
  └→ 用 Serverless Function

你的函数只做轻量处理（认证验证、URL 重定向、JSON 转换）？
  └→ 用 Edge Function（启动更快、全球就近执行）

你追求极致的响应速度（< 50ms）？
  └→ 用 Edge Function

不确定用哪个？
  └→ 默认用 Serverless Function（兼容性最好）
```

> ⚠️ **Hobby 方案的 Serverless 超时只有 10 秒**。如果你需要调用 AI API（通常需要 5-30 秒），免费方案可能会超时。解决方案：① 升级到 Pro（60 秒超时）② 使用流式响应（Streaming）③ 改用 Edge Function（25 秒超时）。

---

## 7. 自定义域名与 HTTPS

默认的 `xxx.vercel.app` 域名用来测试完全够用，但正式项目总需要一个**自己的域名**。Vercel 对自定义域名的支持非常友好：添加域名后**自动签发 HTTPS 证书**，整个过程不需要你手动处理 SSL。

```
默认域名：https://my-project.vercel.app    ← 能用，但不专业
自定义域名：https://example.com             ← 品牌感、SEO 友好
           https://app.example.com        ← 子域名，区分不同服务
```

### 7.1 添加自定义域名

#### 前提：你需要一个域名

如果你还没有域名，需要先到域名注册商购买一个。常见选择：

| 注册商 | 特点 | 价格参考 |
|--------|------|----------|
| [Namecheap](https://namecheap.com) | 性价比高，界面友好 | `.com` 约 $10/年 |
| [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/) | 成本价销售（零利润），DNS 管理方便 | `.com` 约 $9/年 |
| [GoDaddy](https://godaddy.com) | 知名度最高，首年经常打折 | `.com` 首年约 $2，续费 $17/年 |
| [阿里云万网](https://wanwang.aliyun.com) | 国内首选，`.cn` 域名便宜 | `.com` 约 ¥69/年 |
| [腾讯云 DNSPod](https://dnspod.cloud.tencent.com) | 国内注册 + DNS 一体化 | `.com` 约 ¥60/年 |

> 📝 **推荐**：如果你的用户主要在海外，推荐 Cloudflare Registrar（最便宜 + DNS 管理最方便）。如果用户在国内且需要备案，选阿里云或腾讯云。

> ⚠️ **关于备案**：使用 Vercel 托管的网站，由于服务器在海外，**不需要也无法进行 ICP 备案**。如果你的域名需要备案后才能解析到国内服务器，这不影响解析到 Vercel（海外服务器）。但中国大陆用户的访问速度会受影响。

#### 方式一：Dashboard 添加域名

```
Project → Settings → Domains

┌────────────────────────────────────────────────┐
│  Domains                                       │
├────────────────────────────────────────────────┤
│                                                │
│  ┌──────────────────────────────────────┐      │
│  │  example.com                    [Add]│      │
│  └──────────────────────────────────────┘      │
│                                                │
│  Current Domains:                              │
│  ✅ my-project.vercel.app (默认，不可删除)      │
│                                                │
└────────────────────────────────────────────────┘
```

输入你的域名后点击 **Add**，Vercel 会检测你的 DNS 配置状态，并告诉你需要添加什么记录。

#### 方式二：CLI 添加域名

```bash
# 查看当前项目绑定的域名
vercel domains ls

# 添加域名
vercel domains add example.com
# → Vercel 会提示你需要配置的 DNS 记录

# 添加子域名
vercel domains add blog.example.com
```

#### 域名格式说明

你可以绑定多种格式的域名到同一个项目：

| 域名格式 | 示例 | 说明 |
|----------|------|------|
| 根域名（裸域） | `example.com` | 最常见，直接访问 |
| 子域名 | `app.example.com` | 区分不同服务（博客、API、后台等） |
| `www` 子域名 | `www.example.com` | 传统习惯，建议和裸域二选一做主域名 |
| 通配符域名 | `*.example.com` | 匹配所有子域名（Pro 方案及以上） |

> 📝 **推荐做法**：同时添加 `example.com` 和 `www.example.com`，让其中一个重定向到另一个。Vercel 在你添加这两个域名时会**自动建议配置重定向**，比如让 `www.example.com` → `example.com`（301 重定向）。

> ⚠️ **每个项目最多 50 个域名**（Hobby 方案），对大多数场景绰绰有余。

### 7.2 DNS 配置方式

添加域名后，你需要在域名注册商（或 DNS 服务商）的管理面板中配置 DNS 记录，让域名指向 Vercel 的服务器。

#### 两种 DNS 记录类型

Vercel 支持两种指向方式，取决于你绑定的是**子域名**还是**根域名**：

```
子域名（blog.example.com）→ 添加 CNAME 记录
根域名（example.com）      → 添加 A 记录
```

| 域名类型 | DNS 记录 | 记录值 | 说明 |
|----------|----------|--------|------|
| 子域名 | `CNAME` | `cname.vercel-dns.com.` | 推荐方式，Vercel 可自动管理指向 |
| 根域名 | `A` | `76.76.21.21` | 根域名不支持 CNAME，只能用 A 记录 |
| 根域名（备选） | `A` | `76.76.21.164` | 可以同时添加多条 A 记录做冗余 |

> 📝 **为什么根域名不能用 CNAME？** 这是 DNS 协议的限制：根域名（Zone Apex）不允许设置 CNAME 记录，因为 CNAME 会与 SOA、NS 等必要记录冲突。一些 DNS 服务商（如 Cloudflare）提供了 **CNAME Flattening** 功能来绕过这个限制，但标准做法还是用 A 记录。

#### 配置示例：以 Cloudflare 为例

如果你用 Cloudflare 管理 DNS，操作步骤如下：

```
1. 登录 Cloudflare Dashboard → 选择你的域名 → DNS → Records

2. 添加根域名的 A 记录：
   Type: A
   Name: @
   IPv4 address: 76.76.21.21
   Proxy status: DNS only (灰色云朵)  ← 重要！先关闭代理
   TTL: Auto

3. 添加 www 子域名的 CNAME 记录：
   Type: CNAME
   Name: www
   Target: cname.vercel-dns.com
   Proxy status: DNS only (灰色云朵)
   TTL: Auto
```

> ⚠️ **Cloudflare 代理模式注意**：如果开启了 Cloudflare 的代理（橙色云朵），Cloudflare 会拦截流量，可能导致 Vercel 的 HTTPS 证书签发失败。建议**先关闭代理**（灰色云朵），等 Vercel 的 SSL 证书签发成功后，再决定是否开启 Cloudflare 代理。

#### 配置示例：以阿里云为例

```
1. 登录阿里云控制台 → 域名 → 域名列表 → 点击域名 → 域名解析

2. 添加 A 记录：
   记录类型: A
   主机记录: @            ← 代表根域名
   记录值: 76.76.21.21
   TTL: 10 分钟

3. 添加 CNAME 记录：
   记录类型: CNAME
   主机记录: www
   记录值: cname.vercel-dns.com
   TTL: 10 分钟
```

#### 验证域名配置

配置完 DNS 后，回到 Vercel Dashboard 的 Domains 页面，Vercel 会自动检测 DNS 记录是否正确：

```
┌────────────────────────────────────────────────┐
│  Domains                                       │
├────────────────────────────────────────────────┤
│                                                │
│  ✅ example.com            Valid Configuration │
│     A Record: 76.76.21.21                      │
│                                                │
│  ✅ www.example.com        Valid Configuration │
│     CNAME: cname.vercel-dns.com                │
│     → Redirects to example.com                 │
│                                                │
│  ✅ my-project.vercel.app  Default             │
│                                                │
└────────────────────────────────────────────────┘
```

你也可以用命令行验证 DNS 是否生效：

```bash
# 检查 A 记录
dig example.com A +short
# → 76.76.21.21 ← 正确

# 检查 CNAME 记录
dig www.example.com CNAME +short
# → cname.vercel-dns.com. ← 正确

# 或用 nslookup（Windows / macOS 都可用）
nslookup example.com
# → Address: 76.76.21.21
```

#### DNS 生效时间

DNS 修改不会立即生效，需要等待**全球 DNS 缓存刷新**：

| 场景 | 预计生效时间 |
|------|-------------|
| 新域名首次配置 | 5 分钟 ~ 1 小时 |
| 修改已有记录 | 取决于原 TTL 值（通常 10 分钟 ~ 24 小时） |
| TTL 设为最小值 | 最快 ~2 分钟 |

> 📝 **加速生效技巧**：在修改 DNS 之前，先把 TTL 改成最小值（如 1 分钟或 60 秒），等 TTL 过期后再修改记录值。这样新记录能更快生效。修改完成后再把 TTL 改回正常值（如 1 小时或 Auto）。

> ⚠️ **常见问题：DNS 已配置但 Vercel 仍显示 "Invalid Configuration"**。可能原因：① DNS 还未全球生效（等几分钟再刷新）② 存在冲突的 DNS 记录（检查是否有重复的 A 或 CNAME 记录）③ Cloudflare 代理模式干扰（先关闭橙色云朵）。

### 7.3 自动 HTTPS 与证书管理

域名绑定成功后，Vercel 会**自动签发 SSL/TLS 证书**，让你的网站支持 HTTPS。整个过程完全自动化，不需要你手动操作。

#### 证书签发流程

```
域名 DNS 验证通过
  ↓
Vercel 自动向 Let's Encrypt 申请证书（~30 秒）
  ↓
证书签发成功，HTTPS 生效
  ↓
证书到期前 30 天自动续期（Let's Encrypt 证书有效期 90 天）
```

> 📝 **Let's Encrypt** 是一个免费、开放的证书颁发机构（CA），全球超过 3 亿个网站使用它的证书。Vercel 使用 Let's Encrypt 为你的自定义域名签发证书，**完全免费**。

#### 查看证书状态

```
Project → Settings → Domains

┌────────────────────────────────────────────────┐
│  example.com                                   │
│  ✅ Valid Configuration                        │
│  🔒 SSL Certificate: Valid                     │
│     Issued: 2026-04-02                         │
│     Expires: 2026-07-01                        │
│     Auto-renewal: Enabled                      │
└────────────────────────────────────────────────┘
```

也可以用浏览器验证：访问 `https://example.com`，点击地址栏的**锁头图标**，查看证书详情。

#### HTTP → HTTPS 自动跳转

Vercel 默认开启了 **HTTP 到 HTTPS 的自动重定向**。当用户访问 `http://example.com` 时，会被 **301 重定向**到 `https://example.com`：

```
http://example.com
  → 301 Redirect
  → https://example.com
```

这意味着你**不需要手动配置** HTTPS 强制跳转——Vercel 已经帮你做了。

#### HSTS（HTTP Strict Transport Security）

如果你希望进一步加强安全性，可以在 `vercel.json` 中添加 HSTS 响应头：

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Strict-Transport-Security",
          "value": "max-age=63072000; includeSubDomains; preload"
        }
      ]
    }
  ]
}
```

| HSTS 参数 | 含义 |
|-----------|------|
| `max-age=63072000` | 浏览器在接下来 2 年内，自动将 HTTP 请求升级为 HTTPS |
| `includeSubDomains` | 所有子域名也强制 HTTPS |
| `preload` | 申请加入浏览器的 HSTS 预加载列表（永久生效） |

> ⚠️ **谨慎使用 `preload`**：一旦加入 HSTS Preload List，浏览器会**永久强制 HTTPS**，即使你后续删除了 HSTS 头也无法撤销（需要手动申请移除，过程很慢）。确保你的网站会**长期使用 HTTPS** 再开启。

#### 证书签发失败排查

如果 Vercel 显示证书签发失败（SSL Certificate: Error），常见原因和解决方案：

| 原因 | 表现 | 解决方案 |
|------|------|----------|
| DNS 记录未配置或未生效 | Vercel 显示 "Invalid Configuration" | 检查 DNS 记录，等待生效（见 7.2 节） |
| Cloudflare 代理模式干扰 | 证书一直在 "Pending" | 关闭 Cloudflare 代理（橙色→灰色云朵） |
| CAA 记录限制 | 证书申请被拒绝 | 添加 CAA 记录：`0 issue "letsencrypt.org"` |
| 域名已过期 | DNS 无法解析 | 续费域名 |

```bash
# 检查是否有 CAA 记录限制证书签发
dig example.com CAA +short
# 如果输出 0 issue "某个非 letsencrypt 的 CA"
# → 需要添加：0 issue "letsencrypt.org"

# 如果没有 CAA 记录（空输出），说明没有限制，任何 CA 都可以签发
```

> 📝 **99% 的情况下**，你不需要操心证书的事情。只要 DNS 配置正确，Vercel 会自动搞定签发和续期。上面的排查指南是给那 1% 的异常情况准备的。

---

## 8. 实战案例：部署一个完整的 React + API 项目

前面的章节分别讲了前端部署、环境变量、Serverless Functions 等独立知识点。这一章我们把它们**串起来**，从零开始构建并部署一个完整的全栈项目——**「每日一句」名言展示应用**。

```
用户访问页面 → 前端 React 渲染 → 调用 /api/quote → Serverless Function 返回随机名言
                                   ↓
                          /api/quotes → 返回名言列表
                          /api/quote/random → 返回随机一条
```

### 8.1 项目结构设计

#### 功能需求

我们要构建的应用很简单，但覆盖了全栈部署的核心要素：

| 功能 | 实现方式 | 涉及知识点 |
|------|----------|------------|
| 展示每日名言 | React 前端组件 | 前端部署、静态资源 |
| 获取随机名言 API | Serverless Function | `api/` 目录、路由 |
| 名言列表 API（分页） | Serverless Function | 请求参数处理 |
| 点赞计数 | Serverless Function + 内存缓存 | POST 请求、状态管理 |
| 环境变量控制 | `VITE_API_BASE` | 环境变量（第 5 章） |

> 📝 **为什么选这个案例？** 它足够简单（一个页面 + 两三个 API），但涵盖了前后端交互、环境变量、部署验证等完整流程。学完这个案例，你就能把同样的模式应用到任何全栈项目。

#### 项目目录结构

```
daily-quote/
├── api/                        # Serverless Functions（后端）
│   ├── quotes.js               # GET /api/quotes — 名言列表
│   └── quote/
│       └── random.js           # GET /api/quote/random — 随机名言
├── src/                        # React 前端
│   ├── App.jsx                 # 主组件
│   ├── App.css                 # 样式
│   ├── main.jsx                # 入口文件
│   └── components/
│       └── QuoteCard.jsx       # 名言卡片组件
├── public/
│   └── favicon.svg             # 网站图标
├── index.html                  # HTML 模板
├── package.json                # 依赖管理
├── vite.config.js              # Vite 配置
└── vercel.json                 # Vercel 部署配置
```

注意关键的**两个目录**：

- `src/` — 前端代码，Vite 会把它构建成静态资源（dist/）
- `api/` — 后端 API，Vercel 自动识别为 Serverless Functions

```
构建后的部署结构：

Vercel 自动处理：
├── 静态资源（dist/）     → 全球 CDN 分发
└── Serverless Functions → 按需执行的后端函数
    ├── /api/quotes      → api/quotes.js
    └── /api/quote/random → api/quote/random.js
```

#### 初始化项目

```bash
# 1. 创建 Vite + React 项目
npm create vite@latest daily-quote -- --template react

# 2. 进入项目目录
cd daily-quote

# 3. 安装依赖
npm install

# 4. 创建 api 目录（Serverless Functions）
mkdir -p api/quote

# 5. 创建 vercel.json
touch vercel.json

# 6. 确认项目能正常运行
npm run dev
```

#### vercel.json 配置

```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

> 📝 **为什么需要这个配置？** 第一条规则确保 `/api/` 路径正确路由到 Serverless Functions；第二条规则是 SPA 客户端路由的回退处理（见 5.3 节）。实际上 Vercel 对 Vite 项目已经自动处理了大部分情况，但显式配置可以避免边界情况。

### 8.2 编写前端与 API

#### 后端：Serverless Functions

##### 名言数据源

先创建一个共享的数据模块。在 `api/` 目录下创建 `_data.js`（以 `_` 开头的文件不会被 Vercel 当作 API 路由）：

```javascript
// api/_data.js — 名言数据（下划线开头 = 不暴露为 API）
export const quotes = [
  { id: 1, text: "简单是终极的复杂。", author: "达芬奇", likes: 0 },
  { id: 2, text: "先完成，再完美。", author: "Facebook 格言", likes: 0 },
  { id: 3, text: "过早优化是万恶之源。", author: "Donald Knuth", likes: 0 },
  { id: 4, text: "好的代码是自己最好的文档。", author: "Steve McConnell", likes: 0 },
  { id: 5, text: "Talk is cheap. Show me the code.", author: "Linus Torvalds", likes: 0 },
  { id: 6, text: "任何可以用 JavaScript 编写的应用，最终都会用 JavaScript 编写。", author: "Jeff Atwood", likes: 0 },
  { id: 7, text: "删除代码比编写代码更能提升软件质量。", author: "Jeff Sickel", likes: 0 },
  { id: 8, text: "最好的错误消息是永远不会出现的那个。", author: "Thomas Fuchs", likes: 0 },
];
```

> 📝 **`_` 前缀约定**：Vercel 会忽略 `api/` 目录中以 `_` 开头的文件，不会将它们注册为 API 端点。利用这个约定可以存放工具函数、数据模块、中间件等共享代码。

##### 随机名言 API

```javascript
// api/quote/random.js
import { quotes } from '../_data.js';

export default function handler(req, res) {
  // 只允许 GET 请求
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: '仅支持 GET 请求' });
  }

  // 随机选取一条名言
  const randomIndex = Math.floor(Math.random() * quotes.length);
  const quote = quotes[randomIndex];

  // 设置缓存：CDN 缓存 60 秒，浏览器不缓存（每次刷新都能看到新名言）
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate');

  res.status(200).json({
    success: true,
    data: quote
  });
}
```

##### 名言列表 API（带分页）

```javascript
// api/quotes.js
import { quotes } from './_data.js';

export default function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: '仅支持 GET 请求' });
  }

  // 分页参数（默认第 1 页，每页 5 条）
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 5;

  // 参数校验
  if (page < 1 || limit < 1 || limit > 50) {
    return res.status(400).json({
      error: '参数无效：page >= 1, 1 <= limit <= 50'
    });
  }

  // 计算分页
  const startIndex = (page - 1) * limit;
  const endIndex = startIndex + limit;
  const paginatedQuotes = quotes.slice(startIndex, endIndex);

  res.status(200).json({
    success: true,
    data: paginatedQuotes,
    pagination: {
      page,
      limit,
      total: quotes.length,
      totalPages: Math.ceil(quotes.length / limit)
    }
  });
}
```

> ⚠️ **Serverless 的无状态特性**：每次调用 Serverless Function 可能在不同的容器中执行。`_data.js` 中的 `likes` 字段在函数重启后会重置为 0。如果需要持久化数据，应该使用数据库（Vercel KV、Vercel Postgres 等）。这里为了简化，我们用内存变量演示。

#### 前端：React 组件

##### QuoteCard 组件

```jsx
// src/components/QuoteCard.jsx
import { useState } from 'react';

export default function QuoteCard({ quote, onRefresh }) {
  const [likes, setLikes] = useState(quote?.likes || 0);
  const [isAnimating, setIsAnimating] = useState(false);

  const handleLike = () => {
    setLikes(prev => prev + 1);
    setIsAnimating(true);
    setTimeout(() => setIsAnimating(false), 300);
  };

  if (!quote) return null;

  return (
    <div className="quote-card">
      <blockquote className="quote-text">
        "{quote.text}"
      </blockquote>
      <p className="quote-author">—— {quote.author}</p>
      <div className="quote-actions">
        <button
          className={`btn-like ${isAnimating ? 'pulse' : ''}`}
          onClick={handleLike}
        >
          ❤️ {likes}
        </button>
        <button className="btn-refresh" onClick={onRefresh}>
          🔄 换一条
        </button>
      </div>
    </div>
  );
}
```

##### App 主组件

```jsx
// src/App.jsx
import { useState, useEffect, useCallback } from 'react';
import QuoteCard from './components/QuoteCard';
import './App.css';

// 从环境变量读取 API 基础路径（本地开发和线上可能不同）
const API_BASE = import.meta.env.VITE_API_BASE || '';

function App() {
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRandomQuote = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/quote/random`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setQuote(data.data);
    } catch (err) {
      setError('获取名言失败，请稍后重试');
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 页面加载时获取第一条名言
  useEffect(() => {
    fetchRandomQuote();
  }, [fetchRandomQuote]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>✨ 每日一句</h1>
        <p className="subtitle">每次刷新，遇见一句编程智慧</p>
      </header>

      <main className="app-main">
        {loading && <div className="loading">加载中...</div>}
        {error && <div className="error">{error}</div>}
        {!loading && !error && (
          <QuoteCard quote={quote} onRefresh={fetchRandomQuote} />
        )}
      </main>

      <footer className="app-footer">
        <p>
          Deployed on <a href="https://vercel.com" target="_blank" rel="noreferrer">▲ Vercel</a>
          {' | '}
          <a href="/api/quotes" target="_blank">查看 API</a>
        </p>
      </footer>
    </div>
  );
}

export default App;
```

> 📝 **`VITE_API_BASE` 的用途**：本地开发时 Vite dev server 和 API 不在同一个端口。你可以设置 `VITE_API_BASE=http://localhost:3000` 指向本地 API。部署到 Vercel 后，前端和 API 同域，留空即可（默认 `''`）。

##### 样式（App.css）

```css
/* src/App.css */
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter', -apple-system, sans-serif;
  background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  min-height: 100vh;
  color: #e0e0e0;
}

.app {
  max-width: 640px;
  margin: 0 auto;
  padding: 60px 20px;
  text-align: center;
}

.app-header h1 { font-size: 2.5rem; margin-bottom: 8px; }
.subtitle { color: #888; font-size: 1rem; margin-bottom: 48px; }

.quote-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 40px 32px;
  margin: 20px 0;
  transition: transform 0.2s;
}
.quote-card:hover { transform: translateY(-2px); }

.quote-text {
  font-size: 1.4rem;
  line-height: 1.8;
  font-style: italic;
  margin-bottom: 16px;
}
.quote-author { color: #aaa; font-size: 0.95rem; margin-bottom: 24px; }

.quote-actions { display: flex; gap: 12px; justify-content: center; }
.quote-actions button {
  padding: 8px 20px;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 8px;
  background: transparent;
  color: #e0e0e0;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}
.quote-actions button:hover {
  background: rgba(255,255,255,0.1);
  transform: scale(1.05);
}
.btn-like.pulse { animation: pulse 0.3s ease; }
@keyframes pulse {
  50% { transform: scale(1.2); }
}

.loading, .error { padding: 40px; font-size: 1.1rem; }
.error { color: #ff6b6b; }

.app-footer { margin-top: 60px; color: #666; font-size: 0.85rem; }
.app-footer a { color: #888; text-decoration: underline; }
```

### 8.3 部署与测试

代码写完了，现在按照完整流程把这个全栈应用部署到 Vercel。

#### Step 1：本地验证

部署前先在本地确认一切正常：

```bash
# 1. 确认构建没有错误
npm run build
# → dist/ 目录生成成功

# 2. 用 vercel dev 在本地模拟 Vercel 环境
#   （这样前端和 API 会在同一个端口运行）
vercel dev
# → Local: http://localhost:3000
# → 访问 http://localhost:3000 查看页面
# → 访问 http://localhost:3000/api/quote/random 测试 API
```

> 📝 **`vercel dev` vs `npm run dev`**：`npm run dev` 只启动前端 Vite 开发服务器，无法访问 `api/` 目录中的 Serverless Functions。`vercel dev` 会同时运行前端和后端，模拟 Vercel 的线上行为。推荐在全栈项目中使用 `vercel dev`。

#### Step 2：推送到 GitHub

```bash
# 1. 初始化 Git（如果还没有）
git init
git add .
git commit -m "feat: daily quote app with React + Serverless API"

# 2. 推送到 GitHub
git remote add origin https://github.com/你的用户名/daily-quote.git
git branch -M main
git push -u origin main
```

#### Step 3：在 Vercel 中导入项目

```
1. 登录 vercel.com → Dashboard → Add New → Project
2. 选择 daily-quote 仓库 → Import
3. 确认配置：
   - Framework Preset: Vite（自动检测）
   - Root Directory: ./
   - Build Command: npm run build（默认）
   - Output Directory: dist（默认）
4. 点击 Deploy
```

等待约 30-60 秒，部署完成后你会得到一个 URL：

```
✅ Production: https://daily-quote.vercel.app
```

#### Step 4：在线验证

部署完成后，逐个验证所有功能：

```bash
# 1. 测试 API — 随机名言
curl https://daily-quote.vercel.app/api/quote/random
# → {"success":true,"data":{"id":3,"text":"过早优化是万恶之源。","author":"Donald Knuth","likes":0}}

# 2. 测试 API — 名言列表（带分页）
curl "https://daily-quote.vercel.app/api/quotes?page=1&limit=3"
# → {"success":true,"data":[...],"pagination":{"page":1,"limit":3,"total":8,"totalPages":3}}

# 3. 测试前端页面
# 浏览器打开 https://daily-quote.vercel.app
# → 看到「每日一句」页面，显示一条随机名言
# → 点击「换一条」按钮，加载新的名言
# → 点击 ❤️ 按钮，点赞数 +1
```

#### Step 5：验证自动部署

现在验证 Git 集成的自动部署是否工作：

```bash
# 1. 修改一点代码（比如改标题）
# 把 App.jsx 中的 "每日一句" 改成 "每日一句 v2"

# 2. 提交并推送
git add .
git commit -m "feat: update title to v2"
git push origin main

# 3. 打开 Vercel Dashboard → Deployments
#    → 你会看到一条新的部署记录正在构建
#    → 构建完成后，访问 URL 看到标题已更新

# 整个过程：改代码 → push → 等 30 秒 → 上线。完毕。
```

#### 部署后常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 页面正常但 API 返回 404 | `api/` 目录位置不对 | 确保 `api/` 在项目**根目录**（和 `package.json` 同级） |
| API 返回 500 Internal Error | 函数代码有运行时错误 | 去 Dashboard → Deployments → 点击部署 → Functions → 查看日志 |
| 本地正常但线上 API 报错 | 环境差异（Node 版本等） | 检查 `package.json` 的 `engines` 字段，或在 Dashboard 设置 Node 版本 |
| 前端请求 API 跨域 | `VITE_API_BASE` 设置了外部域名 | 部署到 Vercel 后前端和 API 同域，`VITE_API_BASE` 应为空 |
| 页面刷新后 404 | SPA 路由未配置 | 确认 `vercel.json` 中有 `rewrites` 规则（见 8.1 节） |

> 📝 **查看 Serverless Function 日志**：`Dashboard → 项目 → Deployments → 选择一个部署 → Functions`。这里可以看到每个 API 的调用日志、执行时间、错误信息。这是排查 API 问题的**第一站**。

> ⚠️ **恭喜！** 到这里，你已经完成了一个完整的全栈应用从开发到部署的全流程。这个 `React + Serverless API` 的模式可以直接复用到绝大部分前端项目中——只需要替换前端组件和 API 逻辑即可。

---

## 9. 生产环境最佳实践

项目部署上线只是第一步。要让它在生产环境中**稳定、快速、安全、省钱**地运行，还需要一些额外的优化和配置。

### 9.1 性能优化

#### 缓存策略：`Cache-Control` 头

Vercel 的 Edge Network 会自动缓存静态资源。但对于 Serverless Functions 的响应，你需要**手动设置缓存策略**：

```javascript
// api/data.js — 设置缓存的 Serverless Function
export default function handler(req, res) {
  // 缓存策略：CDN 缓存 300 秒，过期后在后台重新生成（用户不等待）
  res.setHeader(
    'Cache-Control',
    's-maxage=300, stale-while-revalidate=600'
  );

  res.status(200).json({ data: '这个响应会被 CDN 缓存 5 分钟' });
}
```

常用的缓存指令组合：

| 场景 | Cache-Control 值 | 说明 |
|------|-------------------|------|
| 实时数据（股票、聊天） | `no-cache, no-store` | 每次请求都打到后端 |
| 准实时（新闻列表） | `s-maxage=60, stale-while-revalidate=300` | CDN 缓存 1 分钟，过期后后台刷新 |
| 低频变化（配置、公告） | `s-maxage=3600, stale-while-revalidate=86400` | CDN 缓存 1 小时 |
| 永不变化（版本化资源） | `public, max-age=31536000, immutable` | 缓存 1 年（文件名含 hash） |

> 📝 **`s-maxage` vs `max-age`**：`s-maxage` 只作用于 CDN/代理服务器（Vercel Edge Network），`max-age` 作用于浏览器。通常设置 `s-maxage` 让 CDN 缓存，而让浏览器每次都检查更新。

> ⚠️ **`stale-while-revalidate` 是性能利器**：当 CDN 缓存过期时，它会**先返回旧数据给用户**（不用等），同时在后台重新请求最新数据。用户体验极好——永远不会「等待加载」。

#### ISR（增量静态再生）— Next.js 专属

如果你用 Next.js，ISR 是最强大的性能优化手段之一：

```jsx
// pages/posts/[id].jsx（Next.js Pages Router）
export async function getStaticProps({ params }) {
  const post = await fetchPost(params.id);
  return {
    props: { post },
    revalidate: 60,  // ← 每 60 秒重新生成页面
  };
}

export async function getStaticPaths() {
  return {
    paths: [{ params: { id: '1' } }, { params: { id: '2' } }],
    fallback: 'blocking',  // 未预生成的页面首次访问时实时生成
  };
}
```

```
ISR 工作原理：

首次请求 → 生成静态 HTML → 缓存到 CDN（全球分发）
  ↓ 60 秒后
下一次请求 → 返回缓存页面（快）→ 后台重新生成新页面
  ↓
再下一次请求 → 返回新生成的页面
```

> 📝 **ISR 的本质**：结合了 SSG（静态生成的速度）和 SSR（动态数据的新鲜度）。页面用户体验像静态页一样快（从 CDN 返回），但数据又能定期更新。Vercel 是 ISR 支持最好的平台。

#### 图片优化

Vercel（配合 Next.js）提供自动图片优化服务：

```jsx
// Next.js 的 Image 组件 — 自动优化
import Image from 'next/image';

<Image
  src="/hero.jpg"
  width={800}
  height={400}
  alt="Hero image"
  priority          // 首屏图片优先加载
  placeholder="blur" // 加载时显示模糊占位图
/>
```

自动优化效果：

| 优化项 | 效果 |
|--------|------|
| 格式转换 | 自动转为 WebP/AVIF（体积减少 30-50%） |
| 尺寸适配 | 根据设备屏幕宽度返回合适尺寸 |
| 懒加载 | 非首屏图片延迟加载 |
| CDN 缓存 | 优化后的图片缓存在 Edge Network |

> ⚠️ **非 Next.js 项目**：Vercel 的图片优化服务仅对 Next.js 项目内置可用。Vite/React 项目可以用第三方服务（如 Cloudinary、imgix）或手动预处理图片。

#### 构建体积优化

构建产物越小，CDN 分发越快，用户加载越快：

```bash
# 分析构建体积（Vite 项目）
npx vite-bundle-visualizer

# 分析构建体积（Next.js 项目）
ANALYZE=true next build
# 需要安装 @next/bundle-analyzer
```

常见优化手段：

```
✅ 按需导入（避免引入整个库）
   import { Button } from 'antd'     ← 好：只引入需要的组件
   import antd from 'antd'            ← 差：引入整个库

✅ 动态导入（代码分割）
   const HeavyChart = lazy(() => import('./HeavyChart'))

✅ 移除未使用的依赖
   npx depcheck  ← 检查未使用的依赖

✅ 使用更轻量的替代品
   moment.js (300KB) → dayjs (2KB)
   lodash (72KB) → lodash-es + 按需导入
```

### 9.2 监控与日志

项目上线后，你需要知道：用户体验如何？有没有错误？API 调用情况怎样？

#### Vercel Analytics（流量分析）

Vercel 内置了轻量级的流量分析工具，无需安装第三方脚本：

```
Dashboard → 项目 → Analytics
```

| 指标 | 说明 |
|------|------|
| **Visitors** | 独立访客数 |
| **Page Views** | 页面浏览量 |
| **Top Pages** | 访问量最高的页面 |
| **Top Referrers** | 流量来源（Google、Twitter 等） |
| **Countries** | 用户地理分布 |
| **Devices** | 设备类型（桌面、手机、平板） |

开启方式：

```bash
# Next.js 项目 — 安装 Analytics 包
npm install @vercel/analytics

# 在 layout.tsx 或 _app.tsx 中引入
```

```jsx
// app/layout.tsx（Next.js App Router）
import { Analytics } from '@vercel/analytics/react';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />  {/* ← 加这一行 */}
      </body>
    </html>
  );
}
```

> 📝 **隐私友好**：Vercel Analytics 不使用 Cookie，不追踪个人用户，符合 GDPR。数据只保留在 Vercel 平台上，不会发送到第三方。

#### Speed Insights（性能监控）

Speed Insights 收集真实用户的 **Core Web Vitals** 数据：

```bash
# 安装 Speed Insights 包
npm install @vercel/speed-insights
```

```jsx
// app/layout.tsx
import { SpeedInsights } from '@vercel/speed-insights/react';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <SpeedInsights />
      </body>
    </html>
  );
}
```

开启后，在 Dashboard 中可以看到：

| Web Vitals 指标 | 含义 | 良好标准 |
|-----------------|------|----------|
| **LCP** (Largest Contentful Paint) | 最大内容渲染时间 | < 2.5 秒 |
| **FID** (First Input Delay) | 首次输入延迟 | < 100 毫秒 |
| **CLS** (Cumulative Layout Shift) | 累积布局偏移 | < 0.1 |
| **TTFB** (Time to First Byte) | 首字节时间 | < 800 毫秒 |

> ⚠️ **Hobby 方案限额**：Analytics 和 Speed Insights 在免费方案中有一定的事件数限额。对于个人小项目足够用，但高流量项目建议升级 Pro 或使用 Google Analytics 等免费替代方案。

#### Serverless Function 日志

查看 API 的运行日志是排查问题的核心手段：

```
Dashboard → 项目 → Deployments → 选择一个部署 → Functions

┌────────────────────────────────────────────────┐
│  Function Logs                                 │
├────────────────────────────────────────────────┤
│                                                │
│  /api/quote/random                             │
│  ├─ 10:30:01  200  GET   45ms   us-east-1     │
│  ├─ 10:30:05  200  GET   12ms   us-east-1     │ ← 热启动，更快
│  ├─ 10:31:22  500  GET  103ms   us-east-1     │ ← 错误！点击查看详情
│  └─ 10:32:00  200  GET   38ms   us-east-1     │
│                                                │
│  /api/quotes                                   │
│  ├─ 10:29:55  200  GET   52ms   us-east-1     │
│  └─ 10:31:10  200  GET   15ms   us-east-1     │
│                                                │
└────────────────────────────────────────────────┘
```

在函数代码中使用 `console.log` 输出的内容会出现在日志中：

```javascript
// api/quote/random.js
export default function handler(req, res) {
  console.log('收到请求:', req.method, req.url);  // ← 会显示在日志中
  console.error('错误信息也会记录');                // ← 错误日志

  // ...
}
```

#### Runtime Logs（实时日志）

Vercel 提供实时日志流，适合调试正在运行的生产环境：

```
Dashboard → 项目 → Logs（实时）
```

你也可以用 CLI 查看实时日志：

```bash
# 查看项目的实时日志（类似 tail -f）
vercel logs your-project.vercel.app --follow

# 只看错误日志
vercel logs your-project.vercel.app --follow --output=error
```

> 📝 **日志保留时间**：Hobby 方案的日志保留 **1 小时**，Pro 方案保留 **3 天**。如果需要长期保存日志，建议集成第三方日志服务（如 Datadog、LogDNA）或在函数中把日志写入外部存储。

#### 集成第三方监控

对于生产级项目，建议集成专业的错误监控服务：

```bash
# 以 Sentry 为例
npm install @sentry/nextjs

# 初始化（Sentry CLI 会引导你完成配置）
npx @sentry/wizard@latest -i nextjs
```

```javascript
// 在 Serverless Function 中手动上报错误
import * as Sentry from '@sentry/nextjs';

export default async function handler(req, res) {
  try {
    // 业务逻辑...
  } catch (error) {
    Sentry.captureException(error);  // ← 上报到 Sentry
    res.status(500).json({ error: '服务器内部错误' });
  }
}
```

> ⚠️ **不要在生产环境中依赖 `console.log` 调试**。`console.log` 适合临时排查，但不提供告警、聚合、趋势分析等能力。正式项目应该用 Sentry、Datadog 等工具做结构化监控。

### 9.3 费用控制与限额设置

Vercel 的免费方案很慷慨，但一旦升级到 Pro 或流量突增，费用可能会出乎意料。提前做好费用控制是生产环境的必修课。

#### 费用结构概览

Vercel 的计费主要在以下几个维度（Pro 方案基础上的超额部分）：

| 计费项 | Pro 包含额度 | 超额单价 |
|--------|-------------|----------|
| **带宽** | 1 TB/月 | $40/100 GB |
| **Serverless 执行时长** | 1000 GB-Hours/月 | $40/100 GB-Hours |
| **Edge Function 调用** | 1,000,000 次/月 | $2/1,000,000 次 |
| **Edge Middleware 调用** | 1,000,000 次/月 | $0.65/1,000,000 次 |
| **图片优化** | 5,000 次/月 | $5/1,000 次 |
| **Analytics 事件** | 25,000 次/月 | $14 / 额外 |

> 📝 **Hobby 方案不收费**：免费方案不会产生超额费用——达到限额后服务会被限制（而不是收费）。只有 Pro 及以上方案才会产生超额账单。

#### 查看用量

```
Dashboard → Settings → Billing → Usage

┌────────────────────────────────────────────────┐
│  Usage This Period (Apr 1 - Apr 30)            │
├────────────────────────────────────────────────┤
│                                                │
│  Bandwidth:        45.2 GB / 1 TB    (4.5%)   │
│  ████░░░░░░░░░░░░░░░░░░░░░░░░░░               │
│                                                │
│  Serverless:       12.3 GB-Hr / 1000  (1.2%)  │
│  █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░               │
│                                                │
│  Edge Invocations: 23,456 / 1M       (2.3%)   │
│  █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░               │
│                                                │
└────────────────────────────────────────────────┘
```

#### Spend Management（预算上限）

Vercel 提供了**硬性预算上限**功能，防止意外高额账单：

```
Dashboard → Settings → Billing → Spend Management

┌────────────────────────────────────────────────┐
│  Spend Management                              │
├────────────────────────────────────────────────┤
│                                                │
│  Monthly Budget Limit: $________               │
│                                                │
│  When budget is reached:                       │
│  ○ Pause all projects (停止服务)               │
│  ● Send notification only (仅通知)             │
│                                                │
│  Notification thresholds:                      │
│  ☑ 50% of budget                               │
│  ☑ 75% of budget                               │
│  ☑ 100% of budget                              │
│                                                │
│  [Save]                                        │
└────────────────────────────────────────────────┘
```

> ⚠️ **强烈建议设置预算上限**。互联网上有很多 Vercel 用户因为 DDoS 攻击或爬虫导致带宽暴增，收到数百甚至数千美元账单的案例。设置预算上限可以避免这种情况。

#### 费用优化实用技巧

```
1. 善用缓存（最重要）
   └→ Serverless 函数加 Cache-Control 头（见 9.1 节）
   └→ CDN 缓存命中率越高，实际的函数调用次数越少，费用越低

2. 选对运行时
   └→ 轻量操作用 Edge Function（更便宜，调用费低于 Serverless）
   └→ 重计算用 Serverless Function

3. 控制图片优化调用
   └→ Next.js Image 组件会自动调用优化 API
   └→ 对静态图片：构建时预处理，而不是运行时优化
   └→ 限制 Image 组件的 sizes 属性，减少生成的变体数量

4. 避免无限循环调用
   └→ Serverless 函数之间不要互相调用（A 调 B 调 A = 费用爆炸）
   └→ 前端 useEffect 中的 fetch 确保有依赖数组（避免无限重渲染）

5. 配置 Ignored Build Step
   └→ 只修改 README？跳过构建（见 3.2 节）
   └→ 节省构建时长 = 节省费用
```

> 📝 **个人开发者的现实建议**：如果你的项目月流量在 10 万 PV 以下，Hobby（免费）方案完全够用。超过了再升级到 Pro（$20/月），配合合理的缓存策略，Pro 的包含额度也能覆盖大多数中型项目。只有超高流量或商业项目才需要担心超额费用。

---

## 10. 常见问题与排错

无论准备多充分，部署过程中总会遇到各种报错。这一章汇总了 Vercel 部署中**最高频的问题**和对应的解决方案，帮你快速定位和修复。

### 10.1 构建与部署常见报错

#### 错误速查表

| 报错信息 | 原因 | 解决方案 |
|----------|------|----------|
| `Build Failed: Command "npm run build" exited with 1` | 代码有编译错误 | 先在本地 `npm run build`，修复所有错误后再推送 |
| `Error: Cannot find module 'xxx'` | 依赖未安装或未列入 package.json | 运行 `npm install xxx --save`，确保依赖在 `dependencies` 中 |
| `ENOENT: no such file or directory` | 文件路径引用错误（大小写敏感） | Linux 区分大小写！`import './App.css'` ≠ `import './app.css'` |
| `Error: Build exceeded maximum allowed duration` | 构建超过 45 分钟 | 优化构建流程、减少依赖、启用构建缓存 |
| `Warning: No Output Directory named "dist" found` | 输出目录配置错误 | 在 Settings 或 vercel.json 中修正 `outputDirectory` |

#### 高频问题 1：本地构建成功，Vercel 构建失败

这是最常见的问题，通常由以下原因导致：

```
原因 1：文件名大小写问题
  macOS / Windows: 不区分大小写（App.jsx = app.jsx）
  Linux (Vercel):  区分大小写（App.jsx ≠ app.jsx）

  → 解决：确保 import 语句中的文件名大小写与实际文件名完全一致
```

```
原因 2：依赖在 devDependencies 而不是 dependencies
  Vercel 默认安装 dependencies + devDependencies
  但如果设置了 NODE_ENV=production，只安装 dependencies

  → 解决：构建工具（vite、typescript 等）应放在 devDependencies
         运行时依赖放在 dependencies
         通常不需要改，默认行为是对的
```

```
原因 3：Node.js 版本不一致
  本地: Node 22.x
  Vercel: 默认 Node 20.x

  → 解决：在 package.json 中指定版本
```

```json
{
  "engines": {
    "node": "20.x"
  }
}
```

或者在 Vercel Dashboard 中设置：

```
Project Settings → General → Node.js Version → 选择 20.x 或 22.x
```

#### 高频问题 2：环境变量未生效

```
症状：本地运行正常，部署后读取不到环境变量（undefined）

排查步骤：
1. 确认变量已在 Dashboard 中添加（Settings → Environment Variables）
2. 确认变量勾选了正确的环境（Production / Preview / Development）
3. 确认修改后已重新部署（环境变量修改不会自动触发重新部署）
4. 前端变量需要加前缀（VITE_ / NEXT_PUBLIC_ / REACT_APP_）
```

```bash
# 快速排查：在 Serverless Function 中打印所有环境变量
// api/debug-env.js（排查完记得删除！）
export default function handler(req, res) {
  res.status(200).json({
    NODE_ENV: process.env.NODE_ENV,
    DATABASE_URL: process.env.DATABASE_URL ? '✅ 已设置' : '❌ 未设置',
    API_KEY: process.env.API_KEY ? '✅ 已设置' : '❌ 未设置',
  });
}
```

> ⚠️ **安全警告**：上面的调试端点**绝对不能**保留在生产环境中！用完立即删除。永远不要在 API 响应中暴露环境变量的实际值。

#### 高频问题 3：部署成功但页面显示 404

```
SPA 项目（React Router / Vue Router）：
  → 直接访问 /about 会 404，因为服务器没有 about.html
  → 解决：在 vercel.json 中配置 rewrites（见 5.3 节）

静态站点（Hugo / Hexo）：
  → 检查 outputDirectory 是否正确（Hugo 是 public/，Hexo 是 public/）
  → 确认构建命令正确（hugo、hexo generate）

Monorepo 项目：
  → 检查 Root Directory 是否指向正确的子目录
```

### 10.2 Serverless Functions 排错

Serverless Functions 的报错通常更隐蔽（不像构建错误那样有明确的错误日志），需要一些排查技巧。

#### 错误速查表

| 症状 | 可能原因 | 解决方案 |
|------|----------|----------|
| 返回 `404 Not Found` | 函数文件位置不对 | 确保在项目根目录的 `api/` 文件夹中 |
| 返回 `500 Internal Server Error` | 函数运行时报错 | 查看 Dashboard → Functions → 日志 |
| 返回 `504 Gateway Timeout` | 函数执行超过时间限制 | Hobby: 10 秒 / Pro: 60 秒。优化代码或升级方案 |
| 返回 `413 Payload Too Large` | 请求体超过 4.5 MB | 使用流式上传或减小请求体 |
| 函数不响应 | 忘记调用 `res.send()` 或 `res.json()` | 确保所有代码路径都有响应 |
| CORS 跨域错误 | 缺少跨域响应头 | 添加 CORS 头（见第 6 章）或用 Rewrite 代理 |

#### 超时问题详解

这是 Serverless Functions 最常遇到的问题，特别是调用外部 API 时：

```
Hobby 方案：函数最长执行 10 秒
Pro 方案：函数最长执行 60 秒
Enterprise：最长 900 秒

超过时间限制 → 504 Gateway Timeout
```

常见超时场景和解决方案：

```
场景 1：调用 AI API（OpenAI、Claude 等）
  问题：AI 生成通常需要 5-30 秒，Hobby 的 10 秒不够
  方案 A：升级到 Pro（60 秒超时）
  方案 B：使用流式响应（Streaming）
  方案 C：改用 Edge Function（25 秒超时）

场景 2：数据库查询很慢
  问题：复杂查询或远距离连接导致超时
  方案 A：优化查询（加索引、减少数据量）
  方案 B：选择离函数执行区域近的数据库
  方案 C：在函数中设置查询超时
```

流式响应示例（解决 AI API 超时）：

```javascript
// api/stream.js — 流式响应不受超时限制
export const config = {
  runtime: 'edge',  // Edge Function 支持流式
};

export default async function handler(req) {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      // 模拟逐步生成内容
      const chunks = ['Hello', ' ', 'World', '!'];
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
        await new Promise(r => setTimeout(r, 1000));  // 每秒发一块
      }
      controller.close();
    }
  });

  return new Response(stream, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' }
  });
}
```

#### 冷启动优化

Serverless Function 在一段时间未被调用后会被回收，下次调用需要「冷启动」：

```
冷启动：~200-500ms（包含容器启动 + 代码加载）
热启动：~5-50ms（容器已运行，直接执行）
```

减少冷启动影响的方法：

```
1. 减小函数体积
   └→ 只导入需要的模块（避免 import 整个 SDK）
   └→ 使用 ESM 模块（支持 Tree Shaking）

2. 减少顶层代码执行
   └→ 数据库连接放在 handler 外部（复用连接）
   └→ 但初始化逻辑本身要快

3. 考虑 Edge Function
   └→ V8 Isolate 冷启动 ~1ms（几乎无感知）
   └→ 适合轻量级函数
```

```javascript
// ✅ 好的做法：数据库连接复用
import { createClient } from '@supabase/supabase-js';

// 在 handler 外部创建连接（容器存活期间复用）
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

export default async function handler(req, res) {
  const { data } = await supabase.from('users').select('*');
  res.status(200).json(data);
}
```

#### 函数日志调试技巧

当 API 返回 500 但你不知道具体原因时：

```javascript
// api/users.js — 完善的错误处理模板
export default async function handler(req, res) {
  console.log('[users] 收到请求:', req.method, req.url);
  console.log('[users] Query:', JSON.stringify(req.query));

  try {
    // 你的业务逻辑
    const result = await someOperation();

    console.log('[users] 处理成功:', result.length, '条记录');
    res.status(200).json({ success: true, data: result });

  } catch (error) {
    // 详细记录错误（会出现在 Vercel 日志中）
    console.error('[users] 错误:', error.message);
    console.error('[users] 堆栈:', error.stack);

    res.status(500).json({
      error: '服务器内部错误',
      // 生产环境不要暴露 error.message 给前端
      ...(process.env.NODE_ENV !== 'production' && { detail: error.message })
    });
  }
}
```

> 📝 **在日志中加前缀**（如 `[users]`）是个好习惯。当你有多个 API 函数时，前缀能帮你快速筛选特定函数的日志。

### 10.3 中国大陆访问优化建议

这是使用 Vercel 时**中国开发者最关心的问题**。Vercel 的服务器和 CDN 节点主要分布在海外，中国大陆用户直接访问速度不理想。

#### 现状分析

```
中国大陆用户访问 Vercel 部署的网站：
  → DNS 解析：正常（~50ms）
  → TCP 连接：需要连接海外服务器（~150-300ms）
  → TTFB：首字节时间较长（~500-1500ms）
  → 整体加载：可能需要 3-8 秒（取决于页面大小和网络状况）

对比：同样的页面部署在国内 CDN 上：
  → 整体加载：通常 < 1 秒
```

> ⚠️ **Vercel 的 `vercel.app` 域名在部分地区偶尔会被间歇性屏蔽**。如果你的目标用户主要在中国大陆，使用自定义域名（而不是默认的 `.vercel.app`）可以降低被影响的概率。

#### 方案一：Cloudflare CDN 加速（推荐）

将域名的 DNS 托管到 Cloudflare，利用 Cloudflare 的全球 CDN（包括亚洲节点）做中间层加速：

```
用户（中国大陆）→ Cloudflare 亚洲节点 → Vercel 源站
                  ↑ 缓存命中则直接返回
                  ↑ 香港/新加坡/东京等节点
```

配置步骤：

```
1. 将域名 DNS 迁移到 Cloudflare
2. 配置 DNS 记录指向 Vercel（见 7.2 节）
3. 开启 Cloudflare 代理（橙色云朵）
   → 注意：先关闭代理让 Vercel SSL 证书签发成功，再开启
4. 在 Cloudflare 中配置缓存规则：
   → 静态资源（CSS/JS/图片）缓存 1 天
   → HTML 页面缓存 10 分钟或 Bypass
5. 开启 Cloudflare 的性能优化：
   → Auto Minify（CSS/JS/HTML 自动压缩）
   → Brotli 压缩
   → Early Hints
```

| 优点 | 缺点 |
|------|------|
| 免费方案即可使用 | Cloudflare 免费方案带宽不限，很良心 |
| 亚洲有香港、新加坡等节点 | 中国大陆仍无直连节点（绕路香港） |
| 额外提供 DDoS 防护、WAF | SSL 配置需要注意兼容（Full Strict 模式） |
| 缓存静态资源效果明显 | API 请求（动态内容）加速效果有限 |

> 📝 **实际效果**：开启 Cloudflare 加速后，中国大陆访问速度通常能从 3-8 秒降到 2-4 秒。虽然仍不及国内 CDN，但已经是零成本下的最佳方案。

#### 方案二：国内 CDN 回源 Vercel

如果你的网站主要面向国内用户且已完成 ICP 备案，可以使用国内 CDN 回源 Vercel：

```
用户（中国大陆）→ 阿里云 CDN / 腾讯云 CDN → Vercel 源站
                  ↑ 国内节点，延迟 < 50ms
                  ↑ 需要域名已备案
```

```
配置思路：
1. 在阿里云/腾讯云 CDN 控制台创建加速域名
2. 源站地址填 Vercel 的默认域名（xxx.vercel.app）
3. 回源 Host 设为你的自定义域名
4. 将自定义域名的 DNS 指向国内 CDN 的 CNAME
5. 在 CDN 中配置缓存规则
```

| 优点 | 缺点 |
|------|------|
| 国内访问速度极快（< 1 秒） | 需要域名 ICP 备案 |
| 可以覆盖全国所有地区 | 国内 CDN 需要付费（按流量计费） |
| 对用户完全透明 | 配置相对复杂 |

> ⚠️ **备案要求**：使用国内 CDN 必须有 ICP 备案。如果你的域名没有备案，国内 CDN 服务商会拒绝接入。

#### 方案三：双部署架构

对于对速度要求极高的正式项目，可以采用「前端国内 + API 国外」的双部署架构：

```
前端（静态资源）：部署到国内平台（腾讯云 COS + CDN / 阿里云 OSS + CDN）
  → 国内用户秒开

API（后端逻辑）：保留在 Vercel Serverless Functions
  → 或者也迁移到国内云函数（腾讯云 SCF / 阿里云 FC）
```

```
适用场景：
  ✅ 项目有大量中国大陆用户
  ✅ 对首屏加载速度有严格要求（< 2 秒）
  ✅ 有域名备案

不适用场景：
  ❌ 个人博客、学习项目（杀鸡用牛刀）
  ❌ 用户主要在海外
  ❌ 没有备案的域名
```

#### 方案选择指南

```
你的用户主要在哪里？

用户在海外（或全球分布）：
  └→ 直接用 Vercel，不需要额外优化。Vercel 的全球 CDN 体验已经很好。

用户在中国大陆，但不追求极致速度：
  └→ 方案一：Cloudflare CDN 加速（免费、简单、效果可接受）

用户在中国大陆，追求秒开体验，且有备案：
  └→ 方案二：国内 CDN 回源（快、稳、需付费）
  └→ 方案三：双部署架构（最快，但最复杂）

个人博客 / 学习项目 / Demo：
  └→ 不需要任何优化，直接用 Vercel 默认配置即可
```

> 📝 **务实建议**：除非你的项目有明确且大量的中国大陆用户，否则不需要折腾优化。Vercel 的默认体验对于个人项目、作品集、技术博客来说完全够用。把时间花在内容和功能上，远比优化几百毫秒的加载速度更有价值。

---

## 写在最后

恭喜你读完了这篇教程 🎉 让我们回顾一下你学会了什么：

```
✅ 第 1 章 — 理解 Vercel 的定位和核心优势
✅ 第 2 章 — 注册账号、安装 CLI、准备 Demo 项目
✅ 第 3 章 — Git 集成部署（推送即上线、PR 自动预览）
✅ 第 4 章 — CLI 手动部署（快速原型、临时分享）
✅ 第 5 章 — vercel.json 配置、环境变量、Rewrites/Redirects
✅ 第 6 章 — Serverless Functions（后端 API、动态路由、Edge Functions）
✅ 第 7 章 — 自定义域名与 HTTPS（DNS 配置、证书自动签发）
✅ 第 8 章 — 实战案例（React + API 全栈项目从零到部署）
✅ 第 9 章 — 生产最佳实践（缓存、监控、费用控制）
✅ 第 10 章 — 常见问题排查与中国访问优化
```

现在，拿起你的项目，`git push` 一下，30 秒后它就在全世界上线了。

**Happy Deploying! 🚀**
