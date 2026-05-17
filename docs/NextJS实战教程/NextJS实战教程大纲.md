# Next.js 全栈开发实战

> 从零到上线——App Router、Server Components、数据获取、认证鉴权、数据库集成、API 设计到 Vercel 部署，用一个完整项目贯穿 Next.js 15 全栈开发的每一个环节。

---

## 1. Next.js 是什么：为什么不只写 React

你已经会 React 了。能写组件、能用 Hooks、能用 React Router 搭 SPA。项目也能跑起来。

但当你想把它上线、被搜索引擎收录、让用户打开不白屏 3 秒时——你会发现纯 React 的"单页应用"模式有三个绕不过去的问题。Next.js 就是为了解决这三个问题而生的。

> 💡 **本章的目标**：理解 Next.js 解决了什么问题，了解四种渲染策略的区别，搭建好开发环境并认识项目结构。

### 1.1 React SPA 的三大痛点：SEO、首屏、路由

用 Create React App（CRA）或 Vite 创建的 React 项目，本质上是一个**单页应用（SPA）**。浏览器收到的 HTML 只有一个空的 `<div id="root"></div>`，所有内容都靠 JavaScript 在客户端动态渲染。

这带来了三个核心问题：

**痛点一：SEO 几乎为零**

搜索引擎爬虫（Googlebot 除外）不会执行 JavaScript。它们看到的你的页面是这样的：

```html
<!DOCTYPE html>
<html>
<head><title>My App</title></head>
<body>
  <div id="root"></div>            <!-- 空的！ -->
  <script src="/bundle.js"></script>  <!-- 爬虫不执行这个 -->
</body>
</html>
```

结果就是：你辛苦写的内容，搜索引擎根本看不到。对于博客、电商、营销页面，这是致命的。

**痛点二：首屏白屏时间长**

SPA 的加载流程是这样的：

```
用户请求页面
    → 下载空 HTML
    → 下载 JS Bundle（可能 500KB+）
    → 执行 JS
    → 发起 API 请求（获取数据）
    → 渲染页面

总耗时：2-5 秒（取决于网络和设备）
```

用户在这段时间里只能看到一片白屏（或一个 Loading 动画），体验很差。

**痛点三：路由管理繁琐**

React 本身不带路由。你需要安装 `react-router-dom`，然后手动配置路由表：

```tsx
// 纯 React 的路由配置——全部手动
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/blog/:slug" element={<BlogPost />} />
        <Route path="/dashboard" element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        {/* 每加一个页面，就要加一条路由 */}
      </Routes>
    </BrowserRouter>
  );
}
```

页面多了之后，路由配置越来越臃肿。而且还要手动处理 404、Loading 状态、布局嵌套等问题。

**Next.js 一句话总结：**

| 问题 | 纯 React SPA | Next.js |
|:---|:---|:---|
| SEO | ❌ 空 HTML，搜索引擎看不到内容 | ✅ 服务端预渲染，HTML 自带内容 |
| 首屏速度 | ❌ 等 JS 下载+执行 | ✅ 服务端直出 HTML，秒开 |
| 路由 | ❌ 手动配置 react-router | ✅ 文件系统路由，创建文件即创建路由 |
| 数据获取 | ❌ 客户端 useEffect + Loading | ✅ 服务端直接拿数据，组件拿到就是完整的 |
| API 层 | ❌ 另起一个后端服务 | ✅ 内置 Route Handlers，全栈一体 |

> 💡 **关键认知**：Next.js 不是"另一个前端框架"——它是**基于 React 的全栈框架**。React 负责 UI 组件，Next.js 负责路由、渲染、构建、部署等一切"框架层"的事情。

### 1.2 Next.js 的解决方案：渲染策略全览（CSR/SSR/SSG/ISR）

Next.js 解决 SPA 问题的核心武器就是**多种渲染策略**。不同页面可以选择不同的渲染方式，而不是一刀切。

先看一个全局对比，然后逐个拆解：

**四种渲染策略速览：**

| 策略 | 全称 | 渲染时机 | 适合场景 |
|:---|:---|:---|:---|
| CSR | Client-Side Rendering | 浏览器端，运行时 | 纯交互页面（后台管理） |
| SSR | Server-Side Rendering | 服务端，每次请求 | 实时数据页面（社交 Feed） |
| SSG | Static Site Generation | 构建时，一次生成 | 不常变的内容（博客、文档） |
| ISR | Incremental Static Regeneration | 构建时 + 定期更新 | 半静态内容（电商商品页） |

**CSR — 客户端渲染（和纯 React 一样）：**

```
浏览器收到空 HTML → 下载 JS → JS 渲染页面 → 显示内容

适合：不需要 SEO 的页面（登录后的 Dashboard）
缺点：首屏慢、SEO 差
```

在 Next.js 中，加上 `'use client'` 指令的组件就是客户端渲染：

```tsx
'use client';  // ← 标记为客户端组件

import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>点击 {count} 次</button>;
}
```

**SSR — 服务端渲染（每次请求都在服务端渲染）：**

```
用户请求 → 服务端执行组件代码 → 生成完整 HTML → 返回给浏览器

适合：内容频繁变化 + 需要 SEO（新闻详情、用户个人页）
缺点：每次请求都要服务端计算，有服务器压力
```

在 Next.js App Router 中，**Server Components 默认就是 SSR**：

```tsx
// app/posts/[id]/page.tsx — 这就是 SSR，不需要任何额外配置
export default async function PostPage({ params }: { params: { id: string } }) {
  // 在服务端直接查数据库——浏览器永远看不到这行代码
  const post = await db.post.findUnique({ where: { id: params.id } });

  return (
    <article>
      <h1>{post.title}</h1>
      <p>{post.content}</p>
    </article>
  );
}
```

> 💡 **这是 Next.js 最强大的地方**：组件里直接 `await` 拿数据，不需要 `useEffect`、不需要 Loading 状态、不需要额外的 API 路由。数据在服务端拿好，HTML 直接带着内容发给浏览器。

**SSG — 静态生成（构建时就生成 HTML）：**

```
npm run build 时 → 执行组件代码 → 生成 HTML 文件 → 部署到 CDN

适合：内容不怎么变的页面（博客文章、产品文档）
优点：最快，因为是提前生成好的静态文件
缺点：内容变了要重新构建
```

在 App Router 中，如果你的页面没有动态数据源，Next.js 会**自动静态生成**：

```tsx
// app/about/page.tsx — 没有动态数据，自动 SSG
export default function AboutPage() {
  return (
    <div>
      <h1>关于我们</h1>
      <p>我们是一家专注于 Web 开发的团队。</p>
    </div>
  );
}
// 构建时就生成好 HTML，访问时直接返回静态文件，极快
```

**ISR — 增量静态再生（SSG + 定期更新的混合体）：**

```
首次构建时生成静态 HTML → 用户访问时返回缓存版本
→ 超过设定时间后，下一次访问触发后台重新生成

适合：内容偶尔变化但不需要实时（电商价格、排行榜）
```

```tsx
// app/products/[id]/page.tsx — ISR：每 60 秒重新验证一次
export const revalidate = 60;  // ← 关键：设置重验证间隔（秒）

export default async function ProductPage({ params }: { params: { id: string } }) {
  const product = await fetch(`https://api.example.com/products/${params.id}`);
  const data = await product.json();

  return (
    <div>
      <h1>{data.name}</h1>
      <p>价格：¥{data.price}</p>
    </div>
  );
}
// 前 60 秒内所有用户看到的是缓存版本（极快）
// 60 秒后有人访问，后台自动重新生成（用户看到的可能是旧版本，下一个用户看到新版本）
```

**如何选择渲染策略：**

```
你的页面需要 SEO 吗？
├── 不需要 → CSR（'use client' 组件）
└── 需要
    ├── 内容经常变吗？
    │   ├── 每次请求都不同 → SSR（默认 Server Component）
    │   └── 偶尔变
    │       ├── 能接受几分钟延迟 → ISR（export const revalidate = N）
    │       └── 几乎不变 → SSG（静态页面，自动生成）
    └── 不确定 → 先用 SSR，后续优化为 ISR/SSG
```

> 💡 **实际项目中的建议**：不需要纠结"选哪个"。Next.js App Router 的默认行为已经很聪明了——有动态数据自动 SSR，没有动态数据自动 SSG。你只需要在需要 ISR 时加一行 `export const revalidate`，需要客户端交互时加 `'use client'`。

### 1.3 开发环境搭建：create-next-app + 项目结构速览

理论够了，动手搭环境。

**前置条件：**

- Node.js 18.18 或更高版本（推荐用 [nvm](https://github.com/nvm-sh/nvm) 管理版本）
- 一个趁手的编辑器（推荐 VS Code + [Next.js 官方插件](https://marketplace.visualstudio.com/items?itemName=nextjs.vscode-next)）

**创建项目：**

```bash
# 用 create-next-app 创建新项目（推荐配置）
npx create-next-app@latest my-next-app

# 交互式选项推荐选择：
# ✔ Would you like to use TypeScript?            → Yes
# ✔ Would you like to use ESLint?                → Yes
# ✔ Would you like to use Tailwind CSS?          → Yes
# ✔ Would you like your code inside a `src/` directory? → No
# ✔ Would you like to use App Router?            → Yes（必须！）
# ✔ Would you like to use Turbopack for next dev? → Yes
# ✔ Would you like to customize the import alias? → No
```

> 💡 **为什么选 App Router？** Next.js 有两套路由系统：旧的 Pages Router 和新的 App Router。App Router 是 Next.js 13+ 推出的新架构，支持 Server Components、嵌套布局等现代特性。本教程全程使用 App Router。

**启动开发服务器：**

```bash
cd my-next-app
npm run dev
# → 浏览器打开 http://localhost:3000
```

第一次打开，你会看到 Next.js 的默认欢迎页。

**项目结构速览：**

```
my-next-app/
├── app/                    # ⭐ 核心：所有页面和路由都在这里
│   ├── layout.tsx          # 根布局（相当于 HTML 的 <body> 外壳）
│   ├── page.tsx            # 首页（访问 / 时显示）
│   ├── globals.css         # 全局样式
│   └── favicon.ico         # 网站图标
├── public/                 # 静态资源（图片、字体等，直接通过 URL 访问）
├── next.config.ts          # Next.js 配置文件
├── tailwind.config.ts      # Tailwind CSS 配置
├── tsconfig.json           # TypeScript 配置
├── package.json            # 依赖和脚本
└── .eslintrc.json          # ESLint 配置
```

**你只需要关注的核心文件：**

`app/layout.tsx` — 根布局，所有页面共享的外壳：

```tsx
// app/layout.tsx — 根布局
import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'My Next App',
  description: 'A Next.js application',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>    {/* children 就是每个页面的内容 */}
    </html>
  );
}
```

`app/page.tsx` — 首页，试着改一下内容：

```tsx
// app/page.tsx — 把默认内容替换成你自己的
export default function HomePage() {
  return (
    <main>
      <h1>Hello Next.js!</h1>
      <p>这是我的第一个 Next.js 页面。</p>
    </main>
  );
}
```

保存后浏览器会自动刷新（Hot Reload），你会看到修改立即生效。

**常用命令速查：**

| 命令 | 作用 |
|:---|:---|
| `npm run dev` | 启动开发服务器（localhost:3000） |
| `npm run build` | 构建生产版本 |
| `npm run start` | 运行生产版本 |
| `npm run lint` | 运行 ESLint 检查 |

> 💡 **开发阶段只用 `npm run dev`**。`build` 和 `start` 是部署上线前才用的，我们在第 12 章会详细讲。

**第 1 章核心知识回顾：**

| 概念 | 要点 |
|:---|:---|
| React SPA 的问题 | SEO 差、首屏慢、路由手动管理 |
| Next.js 的定位 | 基于 React 的全栈框架，不是替代 React |
| CSR | 客户端渲染，适合纯交互页面 |
| SSR | 服务端渲染，每次请求动态生成，适合实时内容 |
| SSG | 静态生成，构建时生成 HTML，最快 |
| ISR | 增量静态再生，SSG + 定期更新 |
| App Router | Next.js 13+ 的新路由系统，基于文件系统 |
| `app/` 目录 | 所有页面和路由都在这个目录下 |

---

## 2. App Router 核心概念：文件即路由

Next.js 的路由系统不需要你写路由配置文件。你在 `app/` 目录下创建文件夹和文件，路由就自动生成了。

这不只是"省事"——文件系统路由让每个路由的布局、加载状态、错误处理都变成了约定好的文件名，一眼就能看懂整个应用的页面结构。

> 💡 **本章的目标**：掌握 App Router 的文件约定、嵌套布局机制、动态路由语法，以及三种导航方式。

### 2.1 文件系统路由：page.tsx、layout.tsx、loading.tsx、error.tsx

App Router 的核心思想：**一个文件夹 = 一个路由段（Route Segment）**，文件夹里的特定文件名决定了这个路由段的行为。

**最简单的例子——创建 3 个页面：**

```
app/
├── page.tsx              → /（首页）
├── about/
│   └── page.tsx          → /about
└── blog/
    └── page.tsx          → /blog
```

就是这么简单——创建文件夹 + 放一个 `page.tsx`，路由就有了。

**约定文件名速查：**

| 文件名 | 作用 | 必须？ |
|:---|:---|:---|
| `page.tsx` | 页面内容，让这个路由段**可访问** | ✅ 没有它，这个路由不可访问 |
| `layout.tsx` | 布局外壳，包裹当前和所有子路由 | 根目录必须有 |
| `loading.tsx` | 加载状态，页面数据还没好时显示 | 可选 |
| `error.tsx` | 错误边界，出错时兜底显示 | 可选 |
| `not-found.tsx` | 404 页面 | 可选 |
| `template.tsx` | 类似 layout，但每次导航都会重新挂载 | 可选，很少用 |

**`page.tsx` — 页面的"正文"：**

```tsx
// app/about/page.tsx
export default function AboutPage() {
  return (
    <div>
      <h1>关于我们</h1>
      <p>这是关于页面。</p>
    </div>
  );
}
// 访问 /about 就会渲染这个组件
```

> 💡 **关键规则**：只有包含 `page.tsx` 的文件夹才会成为可访问的路由。你可以在 `app/` 下创建 `components/` 文件夹放公共组件，它不会变成一个路由（因为没有 `page.tsx`）。

**`layout.tsx` — 不会重新渲染的"外壳"：**

```tsx
// app/layout.tsx — 根布局（必须存在）
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <nav>这是全局导航栏——所有页面都会显示</nav>
        <main>{children}</main>
        <footer>这是全局页脚</footer>
      </body>
    </html>
  );
}
```

Layout 的关键特性：**页面切换时 Layout 不会重新渲染**。如果你在导航栏里有一个搜索框，用户输入的内容在页面切换后还会保留。

**`loading.tsx` — 自动的 Loading 状态：**

```tsx
// app/blog/loading.tsx — 当 blog 页面在加载数据时自动显示
export default function Loading() {
  return (
    <div className="loading-spinner">
      <p>加载中...</p>
    </div>
  );
}
```

不需要在组件里手动写 `if (isLoading) return <Spinner />`——Next.js 用了 React 的 Suspense 机制，`loading.tsx` 会自动在数据准备好之前显示。

**`error.tsx` — 自动的错误边界：**

```tsx
// app/blog/error.tsx — 当 blog 页面出错时显示
'use client';  // ⚠️ error.tsx 必须是客户端组件

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div>
      <h2>出错了！</h2>
      <p>{error.message}</p>
      <button onClick={() => reset()}>重试</button>
    </div>
  );
}
```

> 💡 **error.tsx 必须加 `'use client'`**，因为它需要 `reset()` 函数来让用户点击重试——这是交互行为，需要在客户端执行。

**一个完整的路由段长什么样：**

```
app/blog/
├── layout.tsx      ← 博客区域的布局（侧边栏、面包屑等）
├── page.tsx        ← 博客列表页面（/blog）
├── loading.tsx     ← 加载中的骨架屏
├── error.tsx       ← 出错时的兜底页面
└── not-found.tsx   ← 博客找不到时的 404 页面
```

渲染顺序（从外到内）：

```
layout.tsx
└── loading.tsx（数据加载中时显示）
    └── page.tsx（数据加载完成后显示）
    └── error.tsx（page.tsx 出错时替换显示）
```

### 2.2 嵌套布局（Nested Layouts）：一次搞懂布局继承

嵌套布局是 App Router 最强大的特性之一——每个路由段可以有自己的 `layout.tsx`，子路由会**自动继承**父路由的布局。

**典型场景：Dashboard 后台**

```
app/
├── layout.tsx                  ← 根布局（导航栏 + 页脚）
├── page.tsx                    ← 首页
└── dashboard/
    ├── layout.tsx              ← Dashboard 布局（侧边栏）
    ├── page.tsx                ← /dashboard（概览页）
    ├── settings/
    │   └── page.tsx            ← /dashboard/settings
    └── analytics/
        └── page.tsx            ← /dashboard/analytics
```

用户访问 `/dashboard/settings` 时，渲染的组件层级是：

```
RootLayout（导航栏 + 页脚）
└── DashboardLayout（侧边栏）
    └── SettingsPage（设置页面内容）
```

**根布局——全局外壳：**

```tsx
// app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <header>🌐 全局导航栏</header>
        {children}
        <footer>© 2025 My App</footer>
      </body>
    </html>
  );
}
```

**Dashboard 布局——只在 /dashboard/* 下生效：**

::: v-pre
```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style=&#123;&#123; display: 'flex' &#125;&#125;>
      <aside style=&#123;&#123; width: '250px' &#125;&#125;>
        <nav>
          <a href="/dashboard">📊 概览</a>
          <a href="/dashboard/analytics">📈 分析</a>
          <a href="/dashboard/settings">⚙️ 设置</a>
        </nav>
      </aside>
      <div style=&#123;&#123; flex: 1 &#125;&#125;>
        {children}    {/* 这里渲染 settings/page.tsx 或 analytics/page.tsx */}
      </div>
    </div>
  );
}
```
:::

**布局嵌套的关键规则：**

1. **不重新渲染**：在 `/dashboard/settings` 和 `/dashboard/analytics` 之间切换时，`DashboardLayout` 不会重新挂载，侧边栏状态保持不变
2. **自动继承**：子路由自动被父级所有 layout 包裹，不需要手动套
3. **只影响子路由**：`app/dashboard/layout.tsx` 不会影响 `/about` 页面
4. **根 layout 是必须的**：`app/layout.tsx` 必须存在，且必须包含 `<html>` 和 `<body>` 标签

> 💡 **Layout vs Template**：如果你需要每次导航都重新挂载的布局（比如进入页面时播放动画），用 `template.tsx` 代替 `layout.tsx`。但 99% 的场景用 `layout.tsx` 就够了。

### 2.3 动态路由与路由分组：[slug]、[...catchAll]、(group)

不是所有页面都是固定路径。博客文章有 `/blog/my-first-post`，商品有 `/product/12345`——这些路径的一部分是动态的。App Router 用方括号 `[]` 来表示动态段。

**基础动态路由 — `[slug]`：**

```
app/blog/
├── page.tsx                → /blog（博客列表）
└── [slug]/
    └── page.tsx            → /blog/hello-world、/blog/nextjs-guide 等
```

```tsx
// app/blog/[slug]/page.tsx
export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;  // Next.js 15 中 params 是 Promise

  return <h1>文章：{slug}</h1>;
}

// 访问 /blog/hello-world → slug = "hello-world"
// 访问 /blog/nextjs-guide → slug = "nextjs-guide"
```

**全捕获路由 — `[...slug]`：**

当你需要匹配多层路径时：

```
app/docs/
└── [...slug]/
    └── page.tsx            → /docs/a、/docs/a/b、/docs/a/b/c 等
```

```tsx
// app/docs/[...slug]/page.tsx
export default async function DocsPage({
  params,
}: {
  params: Promise<{ slug: string[] }>;
}) {
  const { slug } = await params;  // slug 是数组！

  return <p>路径：{slug.join(' → ')}</p>;
}

// 访问 /docs/getting-started       → slug = ["getting-started"]
// 访问 /docs/api/auth/login         → slug = ["api", "auth", "login"]
```

**可选全捕获 — `[...slug](...slug)``：**

多了一层方括号，表示"也匹配没有参数的情况"：

```
app/shop/[...slug](...slug)/page.tsx
  → /shop（slug = undefined）
  → /shop/shoes（slug = ["shoes"]）
  → /shop/shoes/nike（slug = ["shoes", "nike"]）
```

**动态路由语法速查：**

| 语法 | 示例路径 | params |
|:---|:---|:---|
| `[slug]` | `/blog/hello` | `{ slug: "hello" }` |
| `[...slug]` | `/docs/a/b/c` | `{ slug: ["a", "b", "c"] }` |
| `[...slug](...slug)` | `/shop` 或 `/shop/a/b` | `{ slug: undefined }` 或 `{ slug: ["a", "b"] }` |

**路由分组 — `(group)`：**

有时候你想给一组路由共享布局，但不希望文件夹名出现在 URL 中。用圆括号 `()` 包裹文件夹名：

```
app/
├── (marketing)/            ← 不会出现在 URL 中！
│   ├── layout.tsx          ← 营销页共享布局（居中、大字体）
│   ├── page.tsx            → /（首页）
│   └── about/
│       └── page.tsx        → /about（不是 /marketing/about）
├── (dashboard)/            ← 也不会出现在 URL 中！
│   ├── layout.tsx          ← 后台共享布局（侧边栏）
│   ├── dashboard/
│   │   └── page.tsx        → /dashboard
│   └── settings/
│       └── page.tsx        → /settings
└── layout.tsx              ← 根布局
```

> 💡 **路由分组的主要用途**：(1) 让不同页面共享不同的布局，而不影响 URL 结构。(2) 按功能模块组织代码（marketing、dashboard、auth 等），保持代码整洁。

### 2.4 导航：Link 组件、useRouter、编程式跳转

Next.js 提供了三种页面间导航的方式，各有适合的场景。

**方式一：`<Link>` 组件（最常用）**

```tsx
import Link from 'next/link';

export default function Navbar() {
  return (
    <nav>
      <Link href="/">首页</Link>
      <Link href="/about">关于</Link>
      <Link href="/blog/hello-world">一篇博客</Link>

      {/* 动态路由 */}
      <Link href={`/blog/${post.slug}`}>{post.title}</Link>

      {/* 替换历史记录（不能返回） */}
      <Link href="/dashboard" replace>进入后台</Link>

      {/* 滚动到特定位置 */}
      <Link href="/docs#installation">跳到安装章节</Link>
    </nav>
  );
}
```

`<Link>` 的核心优势：
- **预取（Prefetch）**：在视口内可见的 Link，Next.js 会自动在后台预加载目标页面的数据，点击时秒开
- **客户端导航**：不会整页刷新，只更新变化的部分（Layout 保持不变）
- **自动代码分割**：每个页面的 JS 只在需要时加载

> 💡 **不要用 `<a>` 标签做内部导航**。`<a href="/about">` 会触发整页刷新，丢失所有客户端状态（表单输入、滚动位置等）。只有外部链接才用 `<a>`。

**方式二：`useRouter` Hook（编程式跳转）**

当你需要在某个事件（按钮点击、表单提交、定时器）之后跳转页面时：

```tsx
'use client';  // ⚠️ useRouter 只能在客户端组件中使用

import { useRouter } from 'next/navigation';  // ⚠️ 是 next/navigation，不是 next/router！

export default function LoginForm() {
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const success = await login();

    if (success) {
      router.push('/dashboard');       // 跳转到 /dashboard
      // router.replace('/dashboard'); // 替换当前历史记录（不能返回）
      // router.back();               // 返回上一页
      // router.refresh();            // 刷新当前页面（重新获取数据）
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* 表单内容 */}
      <button type="submit">登录</button>
    </form>
  );
}
```

**`useRouter` 常用方法速查：**

| 方法 | 作用 |
|:---|:---|
| `router.push(url)` | 跳转到新页面，加入历史记录 |
| `router.replace(url)` | 跳转到新页面，替换当前历史记录 |
| `router.back()` | 返回上一页 |
| `router.forward()` | 前进一页 |
| `router.refresh()` | 重新获取当前页面数据（不清除客户端状态） |
| `router.prefetch(url)` | 手动预取某个页面 |

> 💡 **常见错误**：从 `next/router` 导入 `useRouter` 是旧版 Pages Router 的用法。App Router 必须从 `next/navigation` 导入，否则会报错。

**方式三：`redirect()` — 服务端重定向**

在 Server Components 或 Server Actions 中，使用 `redirect()` 函数：

```tsx
import { redirect } from 'next/navigation';

export default async function ProtectedPage() {
  const user = await getUser();

  if (!user) {
    redirect('/login');  // 未登录 → 服务端直接重定向，浏览器收到的就是跳转后的页面
  }

  return <h1>欢迎，{user.name}</h1>;
}
```

**三种导航方式的选择：**

| 场景 | 推荐方式 |
|:---|:---|
| 页面上的导航链接 | `<Link>` 组件 |
| 按钮点击后跳转 | `useRouter().push()` |
| 服务端条件重定向 | `redirect()` |
| 外部链接 | `<a>` 标签 |

**第 2 章核心知识回顾：**

| 概念 | 要点 |
|:---|:---|
| 文件系统路由 | 文件夹 + `page.tsx` = 路由，不需要配置文件 |
| 约定文件 | `page.tsx`（页面）、`layout.tsx`（布局）、`loading.tsx`（加载）、`error.tsx`（错误） |
| 嵌套布局 | 子路由自动继承父布局，Layout 在页面切换时不重新渲染 |
| 动态路由 | `[slug]`（单段）、`[...slug]`（多段）、`[...slug](...slug)`（可选多段） |
| 路由分组 | `(group)` 文件夹不影响 URL，用于共享布局或组织代码 |
| 导航方式 | `<Link>`（声明式）、`useRouter`（编程式）、`redirect`（服务端） |

---

## 3. Server Components vs Client Components：React 的新范式

如果只能学 Next.js 的一个概念，就是这个。

Server Components 和 Client Components 是 React 18 引入、Next.js App Router 全面落地的新架构。搞懂它们的区别和边界，后面所有章节都会顺畅很多；搞不懂，你会反复踩坑。

> 💡 **本章的目标**：理解 Server 和 Client Components 的本质区别，知道什么时候用哪个，以及如何正确混合使用。

### 3.1 Server Components 原理：在服务端渲染、零 JS Bundle

**一句话定义**：Server Components 在服务端执行，生成的 HTML 直接发给浏览器，**组件的 JavaScript 代码不会发送到客户端**。

这意味着什么？看一个对比：

**传统 React 组件（全部在客户端）：**

```
服务端发送：组件的 JS 代码（可能 200KB）
    → 浏览器下载 JS
    → 浏览器执行 JS
    → 浏览器发起 API 请求获取数据
    → 浏览器渲染组件
```

**Server Component（在服务端执行）：**

```
服务端执行组件代码 + 获取数据
    → 生成渲染结果（HTML + RSC Payload）
    → 发送给浏览器
    → 浏览器直接显示，不需要执行任何 JS

组件的 JS 代码：0 KB 发送到客户端
```

**实际代码——一个读取数据库的组件：**

```tsx
// app/users/page.tsx — 这是一个 Server Component（默认就是！）
import { db } from '@/lib/db';

export default async function UsersPage() {
  // 直接在组件里查数据库——这行代码只在服务端执行
  const users = await db.user.findMany();

  // 直接读取环境变量——安全，不会泄露给客户端
  const apiKey = process.env.SECRET_API_KEY;

  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name} - {user.email}</li>
      ))}
    </ul>
  );
}
```

这个组件可以直接：
- ✅ 查数据库（`db.user.findMany()`）
- ✅ 读取服务端环境变量（`process.env.SECRET_API_KEY`）
- ✅ 调用内部 API（不经过网络，直接函数调用）
- ✅ 使用 `async/await`（组件本身就是 async 函数）

但**不能**：
- ❌ 使用 `useState`、`useEffect` 等 React Hooks
- ❌ 添加事件处理函数（`onClick`、`onChange` 等）
- ❌ 使用浏览器 API（`window`、`document`、`localStorage`）

**Server Components 的三大优势：**

| 优势 | 说明 |
|:---|:---|
| 零 JS Bundle | 组件代码不发送到客户端，页面加载更快 |
| 直接访问后端资源 | 数据库、文件系统、内部 API，没有网络延迟 |
| 安全 | 敏感信息（API Key、数据库连接）永远不会暴露给浏览器 |

> 💡 **关键认知**：在 App Router 中，**所有组件默认都是 Server Components**。你不需要做任何特殊标记。只有当你需要交互功能时，才显式标记为 Client Component。

### 3.2 Client Components：'use client' 指令与交互逻辑

当你需要用户交互（点击按钮、输入文字、切换 Tab）时，就需要 Client Component。

**标记方式——在文件顶部加 `'use client'`：**

```tsx
'use client';  // ← 这一行声明这是客户端组件

import { useState } from 'react';

export default function LikeButton() {
  const [likes, setLikes] = useState(0);

  return (
    <button onClick={() => setLikes(likes + 1)}>
      ❤️ {likes} 个赞
    </button>
  );
}
```

**什么时候必须用 Client Component：**

| 需要用到的功能 | 必须是 Client Component？ |
|:---|:---|
| `useState`、`useReducer` | ✅ 是 |
| `useEffect`、`useRef` | ✅ 是 |
| `onClick`、`onChange` 等事件 | ✅ 是 |
| `window`、`document`、`localStorage` | ✅ 是 |
| 第三方交互式组件（轮播图、日期选择器等） | ✅ 是 |
| 纯展示数据（不需要交互） | ❌ 用 Server Component |
| 读取数据库 / 环境变量 | ❌ 用 Server Component |

**`'use client'` 到底做了什么？**

很多人以为 `'use client'` 意味着"这个组件只在浏览器里渲染"。**不是的。**

```
'use client' 组件的渲染流程：

1. 首次访问时 → 服务端预渲染 HTML（用于 SEO 和快速首屏）
2. HTML 发送到浏览器 → 用户立即看到内容
3. JS Bundle 下载完成 → Hydration（注水）
4. Hydration 完成 → 事件处理函数生效，组件变得可交互

所以 Client Component 也有服务端预渲染！只是它的 JS 代码会发送到客户端。
```

> 💡 **`'use client'` 的真正含义**：不是"只在客户端渲染"，而是"这个组件的 JS 代码需要发送到客户端，因为它有交互逻辑"。它仍然会在服务端预渲染一次。

**`'use client'` 是一个边界声明：**

当你在一个文件顶部声明 `'use client'` 时，这个文件以及它导入的所有子模块，都会被当作客户端代码打包。

```tsx
'use client';

// 这个文件里 import 的所有东西，都会被包含在客户端 bundle 中
import { HeavyLibrary } from 'heavy-library';  // ← 这个库也会发送到客户端
import { ChildComponent } from './child';       // ← 这个组件也变成 Client

export default function Parent() {
  return <ChildComponent />;
}
```

这就是为什么要尽量**把 `'use client'` 往下推**——只在最需要交互的小组件上标记，而不是在整个页面组件上标记。

### 3.3 混合使用的黄金法则：Server 为主、Client 为辅

实际项目中，一个页面通常既有数据展示也有交互功能。关键是知道**在哪里划分边界**。

**黄金法则：Server Component 里嵌套 Client Component，而不是反过来。**

```
✅ 推荐的组件结构：

ServerPage（拿数据、渲染布局）
├── ServerHeader（纯展示、零 JS）
├── ServerArticle（纯展示、零 JS）
└── ClientLikeButton（需要 onClick → 'use client'）
    └── 只有这一小块发送 JS 到客户端

❌ 不推荐：

ClientPage（'use client' 标记在整个页面上）
├── ClientHeader（全部变成客户端代码）
├── ClientArticle（全部变成客户端代码）
└── ClientLikeButton
    整个页面的 JS 都发送到客户端，失去了 Server Components 的优势
```

**实战示例——一篇博客文章页面：**

```tsx
// app/blog/[slug]/page.tsx — Server Component（默认）
import { db } from '@/lib/db';
import LikeButton from '@/components/LikeButton';  // 这是 Client Component

export default async function BlogPost({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await db.post.findUnique({ where: { slug } });

  return (
    <article>
      {/* 这些是 Server Component 的输出——零 JS */}
      <h1>{post.title}</h1>
      <p className="date">{post.createdAt.toLocaleDateString()}</p>
      <div>{post.content}</div>

      {/* 只有这个小组件需要交互——它是 Client Component */}
      <LikeButton postId={post.id} initialLikes={post.likes} />
    </article>
  );
}
```

```tsx
// components/LikeButton.tsx — Client Component
'use client';

import { useState } from 'react';

export default function LikeButton({
  postId,
  initialLikes,
}: {
  postId: string;
  initialLikes: number;
}) {
  const [likes, setLikes] = useState(initialLikes);

  async function handleLike() {
    setLikes(likes + 1);
    await fetch(`/api/posts/${postId}/like`, { method: 'POST' });
  }

  return <button onClick={handleLike}>❤️ {likes}</button>;
}
```

注意这个模式：
1. **页面组件**（Server）负责拿数据发给子组件
2. **交互组件**（Client）只处理用户操作
3. Server → Client 的数据传递通过 **props** 完成（props 必须是可序列化的：字符串、数字、布尔值、数组、普通对象）

**Server Component 可以把 Client Component 作为 children 传入：**

```tsx
// ServerWrapper.tsx — Server Component
import ClientInteractive from './ClientInteractive';

export default function ServerWrapper() {
  return (
    <div className="server-styled-container">
      <ClientInteractive>
        {/* 这两个 Server Component 作为 children 传入 Client Component */}
        <ServerDataA />
        <ServerDataB />
      </ClientInteractive>
    </div>
  );
}
```

> 💡 **核心原则**：`'use client'` 标记要尽量往组件树的**叶子节点**推。页面级别的组件保持为 Server Component，只在需要交互的最小组件上标记 `'use client'`。

### 3.4 常见错误与踩坑：useState 在 Server Component 中报错怎么办

这里收集了最常见的 5 个坑，学完这一节可以少走很多弯路。

**坑 1：在 Server Component 中使用 useState / useEffect**

```tsx
// ❌ 报错！Server Component 不能用 Hooks
export default function Page() {
  const [count, setCount] = useState(0);  // ← Error!
  return <p>{count}</p>;
}
```

```
Error: useState only works in Client Components.
Add the "use client" directive at the top of the file to use it.
```

**解决方案**：把需要 state 的部分抽成独立的 Client Component：

```tsx
// ✅ 页面本身保持 Server Component
import Counter from '@/components/Counter';

export default async function Page() {
  const data = await fetchSomeData();  // 服务端拿数据
  return (
    <div>
      <h1>{data.title}</h1>
      <Counter />  {/* 交互部分用 Client Component */}
    </div>
  );
}
```

**坑 2：在 Client Component 中直接查数据库**

```tsx
// ❌ 这样写不行！
'use client';

import { db } from '@/lib/db';

export default function UserList() {
  const users = await db.user.findMany();  // ← 客户端不能访问数据库！
  return <ul>{users.map(u => <li>{u.name}</li>)}</ul>;
}
```

**解决方案**：在 Server Component 里查好数据，通过 props 传给 Client Component：

```tsx
// Server Component 查数据
export default async function Page() {
  const users = await db.user.findMany();
  return <UserList users={users} />;  // 通过 props 传递
}

// Client Component 只做交互
'use client';
export default function UserList({ users }) {
  const [filter, setFilter] = useState('');
  const filtered = users.filter(u => u.name.includes(filter));
  return (
    <>
      <input onChange={e => setFilter(e.target.value)} placeholder="搜索..." />
      <ul>{filtered.map(u => <li key={u.id}>{u.name}</li>)}</ul>
    </>
  );
}
```

**坑 3：给 Client Component 传递不可序列化的 props**

```tsx
// ❌ 函数不能作为 props 从 Server 传给 Client！
export default function Page() {
  const handleClick = () => console.log('clicked');
  return <ClientButton onClick={handleClick} />;  // ← Error!
}
```

Server → Client 的 props 必须是**可序列化**的（能变成 JSON 的）：

| ✅ 可序列化 | ❌ 不可序列化 |
|:---|:---|
| 字符串、数字、布尔值 | 函数 |
| 数组、普通对象 | Date 对象（传字符串代替） |
| `null`、`undefined` | Map、Set |
| Server Actions（特殊！可以传） | Class 实例 |

> 💡 **例外：Server Actions 可以从 Server 传给 Client**。这是 Next.js 的特殊机制，后面第 4 章会详细讲。

**坑 4：以为 `'use client'` 标记了就不在服务端渲染**

```tsx
'use client';

export default function MyComponent() {
  // ❌ 首次渲染时 window 是 undefined（因为服务端预渲染！）
  const width = window.innerWidth;  // ← Error: window is not defined

  return <p>窗口宽度：{width}</p>;
}
```

**解决方案**：用 `useEffect` 确保在客户端执行：

```tsx
'use client';
import { useState, useEffect } from 'react';

export default function WindowWidth() {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    // useEffect 只在客户端执行——安全使用 window
    setWidth(window.innerWidth);
  }, []);

  return <p>窗口宽度：{width || '加载中...'}</p>;
}
```

**坑 5：在 Client Component 中 import Server Component**

```tsx
// ❌ Client Component 不能 import Server Component！
'use client';

import ServerDataComponent from './ServerDataComponent';  // ← 这个会变成 Client

export default function Dashboard() {
  return <ServerDataComponent />;
}
// ServerDataComponent 的 async/await、数据库查询等都会失效
```

**解决方案**：通过 `children` 或 props 传入 Server Component（组合模式）：

```tsx
// ✅ Server Component 作为 children 传入
// app/dashboard/page.tsx（Server Component）
import ClientDashboard from './ClientDashboard';
import ServerStats from './ServerStats';

export default function Page() {
  return (
    <ClientDashboard>
      <ServerStats />  {/* Server Component 作为 children */}
    </ClientDashboard>
  );
}
```

**第 3 章核心知识回顾：**

| 概念 | 要点 |
|:---|:---|
| Server Components | 默认模式，在服务端执行，JS 不发送到客户端 |
| Client Components | 加 `'use client'`，JS 发送到客户端，支持交互 |
| 黄金法则 | Server 为主、Client 为辅，`'use client'` 尽量下推到叶子节点 |
| 数据传递 | Server → Client 通过可序列化的 props |
| 组合模式 | Server Component 嵌套 Client Component，反过来用 children |
| 常见错误 | Server 里用 Hooks、Client 里查数据库、传不可序列化的 props |

---

## 4. 数据获取：从 fetch 到 Server Actions

数据获取是全栈开发的核心问题。传统 React 里你需要 `useEffect` + `useState` + Loading 状态 + 错误处理，写一堆样板代码。Next.js 把这些大幅简化了。

本章覆盖四种数据获取方式，从最简单到最灵活，各有适用场景。

> 💡 **本章的目标**：掌握 Server Components 中的数据获取、缓存策略、Server Actions 的数据变更，以及客户端数据获取的最佳实践。

### 4.1 Server Components 中直接 async/await：最简单的数据获取

在 Server Components 中获取数据，简单到令人难以置信——直接写 `async/await`，不需要任何 Hook：

**传统 React vs Next.js Server Component：**

```tsx
// ❌ 传统 React — 又臭又长的样板代码
'use client';
import { useState, useEffect } from 'react';

export default function UserList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/users')
      .then(res => res.json())
      .then(data => setUsers(data))
      .catch(err => setError(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>加载中...</p>;
  if (error) return <p>出错了</p>;
  return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}
```

```tsx
// ✅ Next.js Server Component — 清爽
export default async function UserList() {
  const users = await fetch('https://api.example.com/users').then(r => r.json());

  return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}
// 没有 useState，没有 useEffect，没有 loading 状态
// loading 状态由 loading.tsx 自动处理
// 错误由 error.tsx 自动捕获
```

**直接查数据库——连 API 都不需要：**

```tsx
// app/posts/page.tsx
import { db } from '@/lib/db';  // Prisma Client

export default async function PostsPage() {
  // 直接查数据库，不需要经过 API 路由
  const posts = await db.post.findMany({
    orderBy: { createdAt: 'desc' },
    take: 10,
  });

  return (
    <div>
      <h1>最新文章</h1>
      {posts.map(post => (
        <article key={post.id}>
          <h2>{post.title}</h2>
          <p>{post.excerpt}</p>
        </article>
      ))}
    </div>
  );
}
```

> 💡 **为什么不需要 API 路由？** 因为 Server Component 在服务端执行，可以直接调用数据库。API 路由是给**客户端组件**或**外部服务**调用的。如果数据只用于页面展示，Server Component 直接查数据库，省掉一层网络请求。

**并行数据获取——避免瀑布流：**

```tsx
// ❌ 瀑布流：先等 user 查完，再查 posts，串行执行
export default async function Dashboard() {
  const user = await getUser();        // 等 500ms
  const posts = await getPosts();      // 再等 300ms
  const stats = await getStats();      // 再等 200ms
  // 总耗时：1000ms（串行）

  return <div>...</div>;
}

// ✅ 并行获取：所有请求同时发出
export default async function Dashboard() {
  const [user, posts, stats] = await Promise.all([
    getUser(),     // 500ms ─┐
    getPosts(),    // 300ms  ├── 同时执行
    getStats(),    // 200ms ─┘
  ]);
  // 总耗时：500ms（取决于最慢的那个）

  return <div>...</div>;
}
```

**数据获取的位置——就近原则：**

```tsx
// ✅ 推荐：每个组件自己获取需要的数据
async function UserAvatar({ userId }: { userId: string }) {
  const user = await getUser(userId);  // 这个组件只获取它需要的数据
  return <img src={user.avatar} alt={user.name} />;
}

async function UserPosts({ userId }: { userId: string }) {
  const posts = await getUserPosts(userId);  // 独立获取
  return <ul>{posts.map(p => <li key={p.id}>{p.title}</li>)}</ul>;
}

// 页面组件把它们组合起来
export default function UserPage({ params }) {
  return (
    <div>
      <UserAvatar userId={params.id} />
      <UserPosts userId={params.id} />
    </div>
  );
}
// React 会自动并行渲染这两个组件（因为它们没有依赖关系）
```

> 💡 **不用担心重复请求**：如果多个组件 fetch 同一个 URL，Next.js 会自动**去重（deduplication）**——同一个渲染周期内，相同的 fetch 请求只会执行一次。

### 4.2 缓存与重验证：fetch 的 cache 和 revalidate 选项

Next.js 对 `fetch` 做了扩展，可以通过选项控制缓存行为。这决定了数据是每次请求都重新获取，还是用缓存版本。

**三种缓存模式：**

```tsx
// 模式 1：强制缓存（默认行为）— 构建时获取，之后一直用缓存
const data = await fetch('https://api.example.com/posts', {
  cache: 'force-cache',  // 默认值，可以不写
});

// 模式 2：不缓存 — 每次请求都重新获取
const data = await fetch('https://api.example.com/posts', {
  cache: 'no-store',  // 总是获取最新数据
});

// 模式 3：定时重验证 — 缓存 N 秒，过期后重新获取
const data = await fetch('https://api.example.com/posts', {
  next: { revalidate: 60 },  // 缓存 60 秒
});
```

**缓存模式速查：**

| 模式 | 选项 | 行为 | 适合场景 |
|:---|:---|:---|:---|
| 静态缓存 | `cache: 'force-cache'` | 构建时获取，之后用缓存 | 几乎不变的数据（CMS 内容） |
| 不缓存 | `cache: 'no-store'` | 每次请求都重新获取 | 实时数据（用户信息、通知） |
| 定时重验证 | `next: { revalidate: N }` | 缓存 N 秒，过期后后台更新 | 偶尔变化的数据（商品价格） |

**页面级别的缓存控制：**

除了在 `fetch` 上设置，你也可以在页面文件中导出配置，影响整个页面的所有数据获取：

```tsx
// app/dashboard/page.tsx

// 方式 1：整个页面不缓存（等价于所有 fetch 都 no-store）
export const dynamic = 'force-dynamic';

// 方式 2：整个页面每 30 秒重验证一次
export const revalidate = 30;

// 方式 3：强制静态生成
export const dynamic = 'force-static';

export default async function DashboardPage() {
  const data = await fetchSomeData();
  return <div>{/* ... */}</div>;
}
```

**按需重验证——数据变更后立即更新：**

定时重验证有时不够及时。比如管理员更新了一篇文章，不想等 60 秒才生效。Next.js 提供了按需重验证：

```tsx
// app/api/revalidate/route.ts — 手动触发重验证的 API
import { revalidatePath, revalidateTag } from 'next/cache';

export async function POST(request: Request) {
  // 方式 1：按路径重验证
  revalidatePath('/blog');  // 重新生成 /blog 页面

  // 方式 2：按标签重验证（更精细）
  revalidateTag('posts');   // 重新获取所有带 'posts' 标签的数据

  return Response.json({ revalidated: true });
}
```

配合 fetch 标签使用：

```tsx
// 给 fetch 请求打标签
const posts = await fetch('https://api.example.com/posts', {
  next: { tags: ['posts'] },  // 标记这个请求属于 'posts' 组
});

// 当调用 revalidateTag('posts') 时，所有带这个标签的缓存都会失效
```

> 💡 **实际项目中的建议**：大多数页面用 `revalidate = 60`（或更长时间）就够了。只有用户个人页面、实时通知等场景才需要 `cache: 'no-store'`。按需重验证（`revalidateTag`）适合 CMS 内容发布后立即更新。

### 4.3 Server Actions：表单提交与数据变更的新范式

前面讲的都是"读"数据。那"写"数据呢？创建文章、更新设置、删除评论——这些操作用 Server Actions。

**Server Actions 是什么？** 在服务端执行的异步函数，可以直接在组件中调用或绑定到表单。不需要手动创建 API 路由。

**最简单的 Server Action——创建文章：**

```tsx
// app/posts/new/page.tsx
import { db } from '@/lib/db';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

export default function NewPostPage() {
  // 定义 Server Action——在 Server Component 里用 async 函数
  async function createPost(formData: FormData) {
    'use server';  // ← 标记这是一个 Server Action

    const title = formData.get('title') as string;
    const content = formData.get('content') as string;

    // 直接操作数据库
    await db.post.create({
      data: { title, content },
    });

    revalidatePath('/posts');  // 刷新文章列表页的缓存
    redirect('/posts');        // 跳转到文章列表
  }

  return (
    <form action={createPost}>  {/* 直接绑定 Server Action！ */}
      <input name="title" placeholder="文章标题" required />
      <textarea name="content" placeholder="文章内容" required />
      <button type="submit">发布</button>
    </form>
  );
}
```

注意这里的革命性变化：
1. 不需要创建 `/api/posts` 路由
2. 不需要 `fetch('/api/posts', { method: 'POST' })`
3. 不需要在客户端处理 JSON 序列化
4. 表单的 `action` 直接绑定一个服务端函数

**Server Actions 文件——独立管理：**

更规范的做法是把 Server Actions 放到独立文件中：

```tsx
// app/actions/post.ts
'use server';  // ← 整个文件的所有导出函数都是 Server Actions

import { db } from '@/lib/db';
import { revalidatePath } from 'next/cache';

export async function createPost(formData: FormData) {
  const title = formData.get('title') as string;
  const content = formData.get('content') as string;

  await db.post.create({ data: { title, content } });
  revalidatePath('/posts');
}

export async function deletePost(postId: string) {
  await db.post.delete({ where: { id: postId } });
  revalidatePath('/posts');
}

export async function likePost(postId: string) {
  await db.post.update({
    where: { id: postId },
    data: { likes: { increment: 1 } },
  });
  revalidatePath(`/posts/${postId}`);
}
```

**在 Client Component 中使用 Server Actions：**

```tsx
// components/DeleteButton.tsx
'use client';

import { deletePost } from '@/app/actions/post';
import { useTransition } from 'react';

export default function DeleteButton({ postId }: { postId: string }) {
  const [isPending, startTransition] = useTransition();

  function handleDelete() {
    if (!confirm('确定删除？')) return;
    startTransition(async () => {
      await deletePost(postId);  // 调用 Server Action
    });
  }

  return (
    <button onClick={handleDelete} disabled={isPending}>
      {isPending ? '删除中...' : '🗑️ 删除'}
    </button>
  );
}
```

> 💡 **Server Actions 的本质**：Next.js 在背后自动帮你创建了一个 API 端点。客户端调用 Server Action 时，实际上是发了一个 POST 请求到这个隐藏的端点。你不需要关心这些细节。

**Server Actions vs API 路由——怎么选？**

| 场景 | 推荐 |
|:---|:---|
| 表单提交（CRUD 操作） | Server Actions |
| 客户端组件中的数据变更 | Server Actions |
| 第三方 Webhook 回调 | API 路由（Route Handlers） |
| 提供给外部应用的 API | API 路由（Route Handlers） |
| 文件上传 | Server Actions（支持 FormData） |

### 4.4 客户端数据获取：useEffect + SWR/React Query

虽然 Server Components 能解决大部分数据获取需求，但有些场景必须在客户端获取数据：

- **实时轮询**：每隔几秒刷新数据（股票价格、聊天消息）
- **用户交互后获取**：搜索框输入后实时搜索
- **无限滚动**：滚动到底部加载更多
- **乐观更新**：先更新 UI，再等服务端确认

**方式一：SWR（推荐）**

[SWR](https://swr.vercel.app/) 是 Vercel 出品的轻量级数据获取库，名字来自 HTTP 的 `stale-while-revalidate` 策略。

```bash
npm install swr
```

```tsx
'use client';

import useSWR from 'swr';

// fetcher 函数：SWR 用它来发起请求
const fetcher = (url: string) => fetch(url).then(r => r.json());

export default function NotificationBell() {
  const { data, error, isLoading } = useSWR(
    '/api/notifications',  // API 路由（需要自己创建）
    fetcher,
    { refreshInterval: 5000 }  // 每 5 秒自动刷新
  );

  if (isLoading) return <span>🔔</span>;
  if (error) return <span>🔔 !</span>;

  return (
    <span>
      🔔 {data.unreadCount > 0 && <badge>{data.unreadCount}</badge>}
    </span>
  );
}
```

**SWR 的核心优势：**

| 特性 | 说明 |
|:---|:---|
| 自动缓存 | 相同 key 的请求自动去重和缓存 |
| 自动重新验证 | 窗口聚焦、网络恢复时自动刷新 |
| 乐观更新 | `mutate()` 可以先更新缓存，再发请求 |
| 轮询 | `refreshInterval` 自动定时刷新 |
| 分页 | `useSWRInfinite` 支持无限滚动 |

**方式二：搜索框实时搜索示例**

```tsx
'use client';

import { useState } from 'react';
import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then(r => r.json());

export default function SearchBox() {
  const [query, setQuery] = useState('');

  // query 为空时传 null，SWR 会跳过请求
  const { data, isLoading } = useSWR(
    query ? `/api/search?q=${query}` : null,
    fetcher
  );

  return (
    <div>
      <input
        type="text"
        placeholder="搜索文章..."
        value={query}
        onChange={e => setQuery(e.target.value)}
      />
      {isLoading && <p>搜索中...</p>}
      {data?.results?.map((item: any) => (
        <div key={item.id}>{item.title}</div>
      ))}
    </div>
  );
}
```

> 💡 **何时用 Server Component 获取，何时用 SWR？** 简单规则：**首次加载的数据用 Server Component**（SEO 友好、无闪烁），**之后需要实时更新的数据用 SWR**（客户端刷新、无需整页重载）。

**第 4 章核心知识回顾：**

| 概念 | 要点 |
|:---|:---|
| Server Component 数据获取 | 直接 `async/await`，可以查数据库、调 API |
| 并行获取 | `Promise.all()` 避免瀑布流 |
| fetch 缓存 | `force-cache`（默认）/ `no-store`（不缓存）/ `revalidate`（定时） |
| 按需重验证 | `revalidatePath()` / `revalidateTag()` |
| Server Actions | `'use server'` 标记，用于数据变更（CRUD） |
| 客户端获取 | SWR / React Query，用于实时更新、搜索、轮询 |

---

## 5. 样式方案：从 CSS Modules 到 Tailwind CSS

Next.js 不绑定任何特定的 CSS 方案——你用什么都行。但生态中有明确的"主流"：**Tailwind CSS** 占据了 Next.js 项目的绝对主导地位，配合 **shadcn/ui** 组件库，可以快速构建精美的界面。

本章先讲 CSS Modules（理解基础），再重点讲 Tailwind + shadcn/ui（实际项目首选）。

> 💡 **本章的目标**：掌握 CSS Modules 的基本用法，熟练使用 Tailwind CSS，了解 shadcn/ui 组件库，并实现暗色模式。

### 5.1 CSS Modules：零配置的模块化样式

CSS Modules 是 Next.js 内置支持的样式方案——不需要安装任何依赖，创建 `.module.css` 文件就能用。

**核心优势**：样式自动作用域隔离，不同组件的 `.title` 类名不会冲突。

**基本用法：**

```css
/* components/Card.module.css */
.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  transition: box-shadow 0.2s;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.description {
  color: #6b7280;
  line-height: 1.6;
}
```

```tsx
// components/Card.tsx
import styles from './Card.module.css';

export default function Card({ title, description }: {
  title: string;
  description: string;
}) {
  return (
    <div className={styles.card}>
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.description}>{description}</p>
    </div>
  );
}
```

编译后，类名会变成类似 `Card_title_x7f3a` 的唯一标识——不可能和其他组件冲突。

**组合多个类名：**

```tsx
// 方式 1：模板字符串
<div className={`${styles.card} ${styles.featured}`}>

// 方式 2：用 clsx 库（推荐）
import clsx from 'clsx';

<div className={clsx(styles.card, {
  [styles.featured]: isFeatured,
  [styles.disabled]: isDisabled,
})}>
```

**CSS Modules 的局限：**

| 优点 | 缺点 |
|:---|:---|
| 零配置，内置支持 | 需要在 CSS 文件和组件之间来回切换 |
| 自动作用域隔离 | 类名不直观（`styles.xxx`） |
| 支持所有 CSS 特性 | 样式和组件分离，维护成本稍高 |
| 无运行时开销 | 动态样式不太方便 |

> 💡 **何时用 CSS Modules？** 如果团队已经习惯传统 CSS 写法，或者项目需要高度自定义的复杂动画，CSS Modules 是稳妥的选择。但对于新项目，我更推荐 Tailwind CSS。

### 5.2 Tailwind CSS 集成：安装配置 + 实用技巧

如果你用 `create-next-app` 创建项目时选了 Tailwind CSS，它已经配置好了。如果没有，手动安装也很简单：

```bash
npm install -D tailwindcss @tailwindcss/postcss postcss
```

**Tailwind 的核心理念——在 HTML 中直接写样式：**

```tsx
// 传统 CSS 写法：
// <div class="card">
//   <h3 class="card-title">标题</h3>
// </div>
// + 一堆 CSS 文件...

// Tailwind 写法——样式直接在组件里，所见即所得：
export default function Card({ title, description }: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-gray-200 p-6 transition-shadow hover:shadow-lg">
      <h3 className="mb-2 text-xl font-semibold text-gray-900">{title}</h3>
      <p className="leading-relaxed text-gray-500">{description}</p>
    </div>
  );
}
// 不需要单独的 CSS 文件，组件即样式
```

**响应式设计——移动优先的断点：**

```tsx
<div className="
  grid
  grid-cols-1          /* 手机：1列 */
  md:grid-cols-2       /* 平板（768px+）：2列 */
  lg:grid-cols-3       /* 桌面（1024px+）：3列 */
  gap-6
">
  <Card />
  <Card />
  <Card />
</div>
```

Tailwind 的断点前缀：

| 前缀 | 最小宽度 | 典型设备 |
|:---|:---|:---|
| （无前缀） | 0px | 手机 |
| `sm:` | 640px | 大手机 |
| `md:` | 768px | 平板 |
| `lg:` | 1024px | 小桌面 |
| `xl:` | 1280px | 大桌面 |
| `2xl:` | 1536px | 超宽屏 |

**状态变体——hover、focus、active：**

```tsx
<button className="
  rounded-lg bg-blue-600 px-6 py-3 text-white
  hover:bg-blue-700        /* 鼠标悬浮 */
  focus:outline-none focus:ring-2 focus:ring-blue-500  /* 键盘聚焦 */
  active:bg-blue-800       /* 按下时 */
  disabled:opacity-50 disabled:cursor-not-allowed      /* 禁用时 */
  transition-colors        /* 颜色过渡动画 */
">
  提交
</button>
```

**自定义主题——在 CSS 中定义设计令牌：**

Tailwind v4 使用 CSS 变量来自定义主题，直接在 `globals.css` 中配置：

```css
/* app/globals.css */
@import "tailwindcss";

@theme {
  --color-primary: #6366f1;
  --color-primary-hover: #4f46e5;
  --color-secondary: #ec4899;
  --font-family-sans: 'Inter', sans-serif;
  --border-radius-card: 12px;
}
```

```tsx
// 使用自定义主题值
<button className="bg-primary hover:bg-primary-hover rounded-card">
  自定义主题按钮
</button>
```

**实用技巧——条件样式用 clsx：**

```bash
npm install clsx
```

```tsx
import clsx from 'clsx';

export default function Badge({ variant }: { variant: 'success' | 'warning' | 'error' }) {
  return (
    <span className={clsx(
      'rounded-full px-3 py-1 text-sm font-medium',  // 基础样式
      {
        'bg-green-100 text-green-800': variant === 'success',
        'bg-yellow-100 text-yellow-800': variant === 'warning',
        'bg-red-100 text-red-800': variant === 'error',
      }
    )}>
      {variant}
    </span>
  );
}
```

> 💡 **Tailwind 的学习曲线**：一开始觉得类名太多看着乱，但用几天之后你会回不去了。关键是装一个 [Tailwind CSS IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss) VS Code 插件，自动补全 + 悬浮预览，写起来飞快。

### 5.3 shadcn/ui 组件库：快速构建精美 UI

[shadcn/ui](https://ui.shadcn.com/) 不是传统的组件库——你不是 `npm install` 一个包，而是**把组件代码复制到你的项目里**。这意味着你可以完全自定义每个组件的样式和行为。

**初始化：**

```bash
npx shadcn@latest init

# 交互式选项：
# ✔ Which style would you like to use? → New York
# ✔ Which color would you like to use as the base color? → Zinc
# ✔ Would you like to use CSS variables for theming? → Yes
```

**添加组件——按需添加，不臃肿：**

```bash
# 只添加你需要的组件
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add input
npx shadcn@latest add dialog
npx shadcn@latest add dropdown-menu
```

组件代码会出现在 `components/ui/` 目录下——这些就是你的代码，随意修改。

**使用示例——按钮：**

```tsx
import { Button } from '@/components/ui/button';

export default function MyPage() {
  return (
    <div className="space-y-4">
      <Button>默认按钮</Button>
      <Button variant="secondary">次要按钮</Button>
      <Button variant="outline">轮廓按钮</Button>
      <Button variant="destructive">危险按钮</Button>
      <Button variant="ghost">幽灵按钮</Button>
      <Button size="sm">小按钮</Button>
      <Button size="lg">大按钮</Button>
      <Button disabled>禁用状态</Button>
    </div>
  );
}
```

**使用示例——卡片 + 表单组合：**

```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';

export default function LoginCard() {
  return (
    <Card className="w-[380px]">
      <CardHeader>
        <CardTitle>登录</CardTitle>
        <CardDescription>输入你的账号信息</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">邮箱</Label>
          <Input id="email" type="email" placeholder="you@example.com" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">密码</Label>
          <Input id="password" type="password" />
        </div>
      </CardContent>
      <CardFooter>
        <Button className="w-full">登录</Button>
      </CardFooter>
    </Card>
  );
}
```

**为什么 shadcn/ui 这么受欢迎：**

| 特点 | 说明 |
|:---|:---|
| 代码属于你 | 组件在你的项目里，随意改 |
| 基于 Radix UI | 底层用无样式的无障碍组件库，交互行为完善 |
| Tailwind 原生 | 所有样式都是 Tailwind 类名，风格统一 |
| 按需添加 | 不会引入不需要的组件，Bundle 最小 |
| 类型安全 | 完整的 TypeScript 类型支持 |

> 💡 **shadcn/ui 不等于 Radix UI**。Radix UI 是底层的无样式组件库（处理键盘导航、焦点管理等），shadcn/ui 是在 Radix UI 上面加了 Tailwind 样式的"预设"。你装的是 shadcn/ui，用的是 Radix 的交互能力。

### 5.4 全局样式与主题：暗色模式实现

**全局样式——`globals.css`：**

Next.js 的全局样式放在 `app/globals.css` 中，在 `app/layout.tsx` 中导入：

```css
/* app/globals.css */
@import "tailwindcss";

/* 全局基础样式 */
body {
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
}

/* 自定义滚动条（可选） */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}
```

**字体优化——`next/font`：**

Next.js 内置字体优化，自动下载字体文件并自托管，避免对 Google Fonts 的网络请求：

```tsx
// app/layout.tsx
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',          // 字体加载时先显示系统字体
  variable: '--font-sans',  // 定义 CSS 变量方便 Tailwind 使用
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={inter.variable}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
```

> 💡 **`next/font` 的优势**：字体文件在构建时下载到本地，用户访问时不需要请求 Google Fonts 服务器——更快、更私密、无布局偏移（FOUT）。

**暗色模式——用 `next-themes` 实现：**

```bash
npm install next-themes
```

**Step 1：创建 ThemeProvider：**

```tsx
// components/ThemeProvider.tsx
'use client';

import { ThemeProvider as NextThemesProvider } from 'next-themes';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider
      attribute="class"       // 基于 class 切换（Tailwind 要求）
      defaultTheme="system"   // 默认跟随系统
      enableSystem             // 支持系统偏好
    >
      {children}
    </NextThemesProvider>
  );
}
```

**Step 2：在根布局中包裹：**

```tsx
// app/layout.tsx
import { ThemeProvider } from '@/components/ThemeProvider';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
```

**Step 3：创建主题切换按钮：**

```tsx
// components/ThemeToggle.tsx
'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);
  if (!mounted) return null;  // 避免 Hydration 不匹配

  return (
    <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
      {theme === 'dark' ? '☀️ 浅色' : '🌙 深色'}
    </button>
  );
}
```

**Step 4：用 Tailwind 的 `dark:` 前缀写暗色样式：**

```tsx
<div className="bg-white dark:bg-gray-900">
  <h1 className="text-gray-900 dark:text-white">标题</h1>
  <p className="text-gray-600 dark:text-gray-300">正文内容</p>
  <div className="border-gray-200 dark:border-gray-700">卡片</div>
</div>
```

**第 5 章核心知识回顾：**

| 概念 | 要点 |
|:---|:---|
| CSS Modules | `.module.css` 文件，自动作用域隔离，零配置 |
| Tailwind CSS | 工具类优先，响应式前缀，状态变体 |
| shadcn/ui | 代码在你项目里，基于 Radix UI + Tailwind |
| `next/font` | 字体自托管，消除布局偏移 |
| 暗色模式 | `next-themes` + Tailwind `dark:` 前缀 |
| 全局样式 | `globals.css` 中定义基础样式和主题变量 |

---

## 6. API 路由与后端能力：Route Handlers

第 4 章提到 Server Components 可以直接查数据库，那还需要 API 吗？需要。

当你需要给**客户端组件提供数据接口**、接收**第三方 Webhook 回调**、或者对外暴露 **RESTful API** 时，Route Handlers 就是你的后端。

> 💡 **本章的目标**：掌握 Route Handlers 的创建和使用，理解中间件的工作原理，学会设计规范的 API。

### 6.1 Route Handlers 基础：GET/POST/PUT/DELETE

Route Handlers 是 App Router 中的 API 层。和页面路由类似，创建文件就是创建 API 端点——但文件名是 `route.ts`（不是 `page.tsx`）。

**创建第一个 API：**

```
app/
├── api/
│   └── hello/
│       └── route.ts        → GET /api/hello
```

```tsx
// app/api/hello/route.ts
export async function GET() {
  return Response.json({ message: 'Hello from Next.js!' });
}
```

访问 `http://localhost:3000/api/hello`，你就能看到 JSON 响应。

**支持多种 HTTP 方法：**

```tsx
// app/api/posts/route.ts — 一个文件处理多种 HTTP 方法

// GET /api/posts — 获取文章列表
export async function GET() {
  const posts = await db.post.findMany();
  return Response.json(posts);
}

// POST /api/posts — 创建新文章
export async function POST(request: Request) {
  const body = await request.json();
  const post = await db.post.create({
    data: { title: body.title, content: body.content },
  });
  return Response.json(post, { status: 201 });
}
```

**动态路由的 API：**

```
app/api/posts/[id]/route.ts    → GET/PUT/DELETE /api/posts/123
```

```tsx
// app/api/posts/[id]/route.ts

// GET /api/posts/123 — 获取单篇文章
export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const post = await db.post.findUnique({ where: { id } });

  if (!post) {
    return Response.json({ error: '文章不存在' }, { status: 404 });
  }
  return Response.json(post);
}

// PUT /api/posts/123 — 更新文章
export async function PUT(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  const post = await db.post.update({
    where: { id },
    data: { title: body.title, content: body.content },
  });
  return Response.json(post);
}

// DELETE /api/posts/123 — 删除文章
export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  await db.post.delete({ where: { id } });
  return new Response(null, { status: 204 });  // 204 No Content
}
```

**Route Handlers 支持的 HTTP 方法：**

| 导出函数名 | HTTP 方法 | 典型用途 |
|:---|:---|:---|
| `GET` | GET | 获取数据 |
| `POST` | POST | 创建数据 |
| `PUT` | PUT | 全量更新 |
| `PATCH` | PATCH | 部分更新 |
| `DELETE` | DELETE | 删除数据 |
| `HEAD` | HEAD | 检查资源是否存在 |
| `OPTIONS` | OPTIONS | CORS 预检 |

> 💡 **`route.ts` 和 `page.tsx` 不能在同一个文件夹里共存**。如果一个路由段既有 `page.tsx` 又有 `route.ts`，会冲突。把 API 路由放在 `app/api/` 下是最佳实践。

### 6.2 请求处理：参数解析、请求体、Headers、Cookies

Route Handlers 基于 Web 标准的 `Request` 和 `Response` API，Next.js 还提供了增强版的 `NextRequest`。

**URL 查询参数：**

```tsx
// GET /api/posts?page=2&limit=10&sort=latest
import { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const page = parseInt(searchParams.get('page') || '1');
  const limit = parseInt(searchParams.get('limit') || '10');
  const sort = searchParams.get('sort') || 'latest';

  const posts = await db.post.findMany({
    skip: (page - 1) * limit,
    take: limit,
    orderBy: { createdAt: sort === 'latest' ? 'desc' : 'asc' },
  });

  return Response.json({
    data: posts,
    pagination: { page, limit, total: await db.post.count() },
  });
}
```

**请求体（JSON / FormData）：**

```tsx
// POST /api/upload — 处理文件上传
export async function POST(request: Request) {
  const contentType = request.headers.get('content-type');

  if (contentType?.includes('application/json')) {
    // JSON 请求体
    const body = await request.json();
    console.log(body.title);
  } else if (contentType?.includes('multipart/form-data')) {
    // FormData（文件上传）
    const formData = await request.formData();
    const file = formData.get('file') as File;
    const bytes = await file.arrayBuffer();
    // 处理文件...
  }

  return Response.json({ success: true });
}
```

**Headers 和 Cookies：**

```tsx
import { cookies, headers } from 'next/headers';

export async function GET() {
  // 读取请求头
  const headersList = await headers();
  const userAgent = headersList.get('user-agent');
  const authToken = headersList.get('authorization');

  // 读取 Cookies
  const cookieStore = await cookies();
  const sessionId = cookieStore.get('session-id')?.value;

  // 设置 Cookies
  const response = Response.json({ data: 'hello' });
  cookieStore.set('visited', 'true', {
    httpOnly: true,
    secure: true,
    maxAge: 60 * 60 * 24,  // 1 天
  });

  return response;
}
```

**自定义响应头和状态码：**

```tsx
export async function GET() {
  return new Response(JSON.stringify({ data: 'hello' }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600',
      'X-Custom-Header': 'my-value',
    },
  });
}
```

> 💡 **`NextRequest` vs `Request`**：`NextRequest` 是 Next.js 对标准 `Request` 的扩展，多了 `nextUrl`（解析后的 URL 对象）、`cookies`（便捷的 Cookie 操作）等属性。两者都可以用，`NextRequest` 更方便。

### 6.3 中间件（Middleware）：鉴权拦截、重定向、国际化

中间件在**请求到达页面或 API 之前**执行，可以用来做鉴权、重定向、请求改写等操作。

**创建中间件——项目根目录下的 `middleware.ts`：**

```
my-next-app/
├── middleware.ts    ← 就放在这里，不在 app/ 目录下！
├── app/
│   └── ...
```

**基础示例——鉴权拦截：**

```tsx
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value;
  const isAuthPage = request.nextUrl.pathname.startsWith('/login');

  // 已登录访问登录页 → 重定向到首页
  if (isAuthPage && token) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  // 未登录访问受保护页面 → 重定向到登录页
  if (!isAuthPage && !token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', request.nextUrl.pathname);  // 记住来源
    return NextResponse.redirect(loginUrl);
  }

  // 放行
  return NextResponse.next();
}

// 配置哪些路径需要经过中间件
export const config = {
  matcher: ['/dashboard/:path*', '/settings/:path*', '/login'],
};
```

**`matcher` — 控制中间件的作用范围：**

```tsx
export const config = {
  // 只对这些路径执行中间件
  matcher: [
    '/dashboard/:path*',     // /dashboard 及所有子路由
    '/api/admin/:path*',     // /api/admin 下的所有 API
    '/settings',             // 精确匹配 /settings
  ],
};
```

如果不配置 `matcher`，中间件会对**所有请求**执行（包括静态文件、图片等），这通常不是你想要的。

**中间件可以做什么：**

| 操作 | 方法 |
|:---|:---|
| 重定向 | `NextResponse.redirect(url)` |
| 重写（URL 不变，内容变） | `NextResponse.rewrite(url)` |
| 设置请求头 | `NextResponse.next({ headers })` |
| 设置 Cookie | `response.cookies.set()` |
| 返回响应 | `new NextResponse(body, options)` |

**中间件的限制：**

- 必须放在项目根目录，整个项目只有一个 `middleware.ts`
- 运行在 Edge Runtime（轻量级运行时），不能用 Node.js 专有 API（如 `fs`）
- 不能直接查数据库（因为 Edge Runtime 限制）
- 应该保持轻量，不做复杂计算

> 💡 **中间件 vs Server Component 的鉴权**：中间件适合粗粒度的路由级鉴权（"这个人能不能访问 /dashboard"）。细粒度的权限控制（"这个人能不能编辑这篇文章"）放在 Server Component 或 Server Action 里做。

### 6.4 API 设计最佳实践：错误处理、响应格式规范

生产级 API 需要统一的响应格式和完善的错误处理。

**统一响应格式：**

```tsx
// lib/api-response.ts — 统一的 API 响应工具
export function successResponse(data: any, status = 200) {
  return Response.json(
    { success: true, data },
    { status }
  );
}

export function errorResponse(message: string, status = 400) {
  return Response.json(
    { success: false, error: message },
    { status }
  );
}
```

```tsx
// 使用统一响应
import { successResponse, errorResponse } from '@/lib/api-response';

export async function GET(request: NextRequest, { params }) {
  const { id } = await params;
  const post = await db.post.findUnique({ where: { id } });

  if (!post) return errorResponse('文章不存在', 404);
  return successResponse(post);
}
```

**输入验证——用 Zod：**

```bash
npm install zod
```

```tsx
// app/api/posts/route.ts
import { z } from 'zod';
import { errorResponse, successResponse } from '@/lib/api-response';

// 定义请求体的 Schema
const createPostSchema = z.object({
  title: z.string().min(1, '标题不能为空').max(100, '标题最多 100 字'),
  content: z.string().min(10, '内容至少 10 个字'),
  tags: z.array(z.string()).optional(),
});

export async function POST(request: Request) {
  try {
    const body = await request.json();

    // 验证请求体
    const validated = createPostSchema.safeParse(body);
    if (!validated.success) {
      return errorResponse(validated.error.errors[0].message, 422);
    }

    const post = await db.post.create({ data: validated.data });
    return successResponse(post, 201);
  } catch (error) {
    console.error('创建文章失败:', error);
    return errorResponse('服务器内部错误', 500);
  }
}
```

**API 错误处理的层次：**

```tsx
export async function POST(request: Request) {
  try {
    // 1. 解析请求体
    let body;
    try {
      body = await request.json();
    } catch {
      return errorResponse('请求体格式错误，需要 JSON', 400);
    }

    // 2. 验证输入
    const validated = schema.safeParse(body);
    if (!validated.success) {
      return errorResponse(validated.error.errors[0].message, 422);
    }

    // 3. 业务逻辑
    const result = await someBusinessLogic(validated.data);
    return successResponse(result, 201);

  } catch (error) {
    // 4. 兜底：未预期的错误
    console.error('Unexpected error:', error);
    return errorResponse('服务器内部错误', 500);
  }
}
```

**HTTP 状态码速查：**

| 状态码 | 含义 | 使用场景 |
|:---|:---|:---|
| 200 | OK | 成功获取 / 更新数据 |
| 201 | Created | 成功创建资源 |
| 204 | No Content | 成功删除（无返回体） |
| 400 | Bad Request | 请求格式错误 |
| 401 | Unauthorized | 未登录 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 422 | Unprocessable Entity | 验证失败 |
| 500 | Internal Server Error | 服务器出错 |

> 💡 **实际项目建议**：大多数内部数据操作用 Server Actions 更简单。Route Handlers 主要用于：(1) 给客户端组件用 SWR/fetch 调用的 API，(2) 第三方服务的 Webhook 回调，(3) 对外提供的 REST API。

**第 6 章核心知识回顾：**

| 概念 | 要点 |
|:---|:---|
| Route Handlers | `route.ts` 文件，导出 HTTP 方法函数 |
| 请求处理 | `NextRequest` 扩展对象，支持 JSON / FormData |
| 中间件 | 根目录 `middleware.ts`，请求到达前执行 |
| matcher | 控制中间件作用范围，避免对静态资源执行 |
| 统一响应 | 封装 `successResponse` / `errorResponse` |
| 输入验证 | Zod 做 Schema 验证，返回 422 状态码 |

---

## 7. 数据库集成：Prisma + PostgreSQL

全栈应用没有数据库就是个花瓶。Next.js 生态中最主流的数据库方案是 **Prisma ORM + PostgreSQL**——类型安全、自动补全、迁移管理一条龙。

> 💡 **本章的目标**：从零搭建 Prisma + PostgreSQL，掌握 CRUD 操作、关联查询，并在 Server Components 中直接使用。

### 7.1 Prisma 初始化：Schema 定义与数据库迁移

**安装 Prisma：**

```bash
npm install prisma --save-dev       # CLI 工具（开发依赖）
npm install @prisma/client          # 运行时客户端
npx prisma init                     # 初始化 Prisma
```

执行 `prisma init` 后会生成两个文件：

```
prisma/
└── schema.prisma    ← 数据库模型定义文件
.env                 ← 数据库连接字符串
```

**配置数据库连接：**

```env
# .env
DATABASE_URL="postgresql://user:password@localhost:5432/mydb?schema=public"
```

> 💡 **本地开发用 Docker 跑 PostgreSQL 最省心**：`docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:16`

**定义数据模型（Schema）：**

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// 用户表
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  avatar    String?
  posts     Post[]          // 一对多：一个用户有多篇文章
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

// 文章表
model Post {
  id        String   @id @default(cuid())
  title     String
  content   String
  published Boolean  @default(false)
  author    User     @relation(fields: [authorId], references: [id])
  authorId  String
  tags      Tag[]           // 多对多：文章和标签
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

// 标签表
model Tag {
  id    String @id @default(cuid())
  name  String @unique
  posts Post[]         // 多对多的另一端
}
```

**执行数据库迁移：**

```bash
# 根据 Schema 创建数据库表（生成迁移文件 + 执行）
npx prisma migrate dev --name init

# 查看数据库——Prisma 自带的数据库 GUI
npx prisma studio
# → 打开 http://localhost:5555，可以直接看和编辑数据
```

**Prisma Client 单例模式——避免开发环境连接泄漏：**

```tsx
// lib/db.ts
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const db = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = db;
}
```

> 💡 **为什么需要单例？** Next.js 开发模式下热重载会反复执行模块代码，如果每次都 `new PrismaClient()`，会创建大量数据库连接直到耗尽。全局单例确保只创建一个实例。

### 7.2 CRUD 操作：增删改查的最佳实践

Prisma 的 API 设计非常直觉化——方法名就是动作，TypeScript 自动推断类型。

**Create — 创建：**

```tsx
// 创建单条记录
const user = await db.user.create({
  data: {
    email: 'alice@example.com',
    name: 'Alice',
  },
});

// 创建时同时创建关联数据（嵌套创建）
const post = await db.post.create({
  data: {
    title: 'Hello Prisma',
    content: '这是第一篇文章',
    author: {
      connect: { id: userId },  // 关联到已有用户
    },
    tags: {
      connectOrCreate: [        // 标签存在则关联，不存在则创建
        { where: { name: 'nextjs' }, create: { name: 'nextjs' } },
        { where: { name: 'tutorial' }, create: { name: 'tutorial' } },
      ],
    },
  },
});

// 批量创建
const users = await db.user.createMany({
  data: [
    { email: 'bob@example.com', name: 'Bob' },
    { email: 'carol@example.com', name: 'Carol' },
  ],
});
```

**Read — 查询：**

```tsx
// 查询单条——按 ID
const user = await db.user.findUnique({
  where: { id: 'xxx' },
});

// 查询单条——按唯一字段
const user = await db.user.findUnique({
  where: { email: 'alice@example.com' },
});

// 查询列表——带筛选、排序、分页
const posts = await db.post.findMany({
  where: {
    published: true,                              // 只查已发布的
    title: { contains: '教程', mode: 'insensitive' },  // 标题包含"教程"
  },
  orderBy: { createdAt: 'desc' },                 // 按时间倒序
  skip: 0,                                        // 跳过前 N 条（分页）
  take: 10,                                       // 取 10 条
  select: {                                       // 只返回需要的字段
    id: true,
    title: true,
    createdAt: true,
    author: { select: { name: true } },           // 关联字段也能选
  },
});

// 统计数量
const count = await db.post.count({
  where: { published: true },
});
```

**Update — 更新：**

```tsx
// 更新单条
const post = await db.post.update({
  where: { id: postId },
  data: {
    title: '新标题',
    published: true,
  },
});

// 条件批量更新
const result = await db.post.updateMany({
  where: { authorId: userId },
  data: { published: false },  // 把某用户的所有文章设为未发布
});
// result.count → 更新了多少条

// 数值递增
await db.post.update({
  where: { id: postId },
  data: { views: { increment: 1 } },  // 浏览量 +1
});
```

**Delete — 删除：**

```tsx
// 删除单条
await db.post.delete({
  where: { id: postId },
});

// 条件批量删除
await db.post.deleteMany({
  where: {
    published: false,
    createdAt: { lt: new Date('2024-01-01') },  // 2024年前的未发布文章
  },
});
```

> 💡 **Prisma 的类型安全**是它的杀手特性：`db.post.create({ data: { titl: '...' } })` 会直接 TypeScript 报错——字段名写错了。所有查询条件、返回字段都有完整的自动补全。

### 7.3 关联查询：一对多、多对多关系

实际应用中，数据之间总是有关联的——用户有文章，文章有标签，评论属于文章和用户。Prisma 让关联查询变得非常直观。

**一对多——查询用户和他的所有文章：**

```tsx
// include：加载关联数据
const user = await db.user.findUnique({
  where: { id: userId },
  include: {
    posts: true,  // 加载这个用户的所有文章
  },
});
// user.posts → Post[] 数组

// include 可以嵌套 + 带条件
const user = await db.user.findUnique({
  where: { id: userId },
  include: {
    posts: {
      where: { published: true },       // 只加载已发布的
      orderBy: { createdAt: 'desc' },   // 按时间倒序
      take: 5,                          // 只取最新 5 篇
      include: {
        tags: true,                     // 文章的标签也一起加载
      },
    },
  },
});
```

**多对多——查询文章和它的标签：**

```tsx
const post = await db.post.findUnique({
  where: { id: postId },
  include: {
    author: { select: { name: true, avatar: true } },  // 作者信息
    tags: true,                                         // 所有标签
  },
});
// post.author.name → "Alice"
// post.tags → [{ id: "...", name: "nextjs" }, { id: "...", name: "tutorial" }]

// 反向查询：查某个标签下的所有文章
const tag = await db.tag.findUnique({
  where: { name: 'nextjs' },
  include: {
    posts: {
      where: { published: true },
      select: { id: true, title: true, createdAt: true },
    },
  },
});
```

**`include` vs `select` — 两种加载关联数据的方式：**

```tsx
// include：加载主体所有字段 + 关联数据
const post = await db.post.findUnique({
  where: { id: postId },
  include: { author: true },  // 返回 post 的所有字段 + author 的所有字段
});

// select：精确控制每个字段（性能更好）
const post = await db.post.findUnique({
  where: { id: postId },
  select: {
    title: true,
    content: true,
    author: {
      select: { name: true },  // 只取作者名字
    },
  },
});
// 返回值只有 { title, content, author: { name } }——最小数据量
```

> 💡 **性能建议**：`select` 比 `include` 更高效，因为它只查询你需要的字段。对于列表页面（展示标题和摘要），用 `select` 避免加载完整文章内容。

### 7.4 Prisma + Server Components：数据直连组件

把前面学的东西串起来——在 Server Component 里直接用 Prisma 查数据库，配合 Server Actions 做数据变更。

**完整示例——博客列表页：**

```tsx
// app/blog/page.tsx — 博客列表
import { db } from '@/lib/db';
import Link from 'next/link';

export default async function BlogPage() {
  const posts = await db.post.findMany({
    where: { published: true },
    orderBy: { createdAt: 'desc' },
    select: {
      id: true,
      title: true,
      createdAt: true,
      author: { select: { name: true } },
      tags: { select: { name: true } },
    },
  });

  return (
    <div>
      <h1>博客</h1>
      {posts.map(post => (
        <article key={post.id}>
          <Link href={`/blog/${post.id}`}>
            <h2>{post.title}</h2>
          </Link>
          <p>作者：{post.author.name} · {post.createdAt.toLocaleDateString()}</p>
          <div>
            {post.tags.map(tag => (
              <span key={tag.name}>#{tag.name} </span>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}
```

**完整示例——Server Action 创建文章：**

```tsx
// app/actions/post.ts
'use server';

import { db } from '@/lib/db';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { z } from 'zod';

const postSchema = z.object({
  title: z.string().min(1).max(100),
  content: z.string().min(10),
});

export async function createPost(formData: FormData) {
  const validated = postSchema.safeParse({
    title: formData.get('title'),
    content: formData.get('content'),
  });

  if (!validated.success) {
    throw new Error(validated.error.errors[0].message);
  }

  await db.post.create({
    data: {
      ...validated.data,
      published: true,
      authorId: 'current-user-id',  // 实际项目从 session 获取
    },
  });

  revalidatePath('/blog');
  redirect('/blog');
}
```

**常用 Prisma 命令速查：**

| 命令 | 作用 |
|:---|:---|
| `npx prisma init` | 初始化 Prisma |
| `npx prisma migrate dev --name xxx` | 创建并执行迁移 |
| `npx prisma migrate deploy` | 生产环境执行迁移 |
| `npx prisma generate` | 重新生成 Prisma Client |
| `npx prisma studio` | 打开数据库 GUI |
| `npx prisma db seed` | 执行种子数据脚本 |
| `npx prisma db push` | 快速同步 Schema（不生成迁移文件） |

**第 7 章核心知识回顾：**

| 概念 | 要点 |
|:---|:---|
| Prisma 初始化 | `prisma init` → 定义 Schema → `migrate dev` |
| 单例模式 | `lib/db.ts` 全局单例避免连接泄漏 |
| CRUD | `create` / `findMany` / `update` / `delete` |
| 关联查询 | `include` 加载关联数据，`select` 精确控制字段 |
| 与 Server Components | 组件中直接 `await db.xxx`，无需 API 中间层 |
| 与 Server Actions | `'use server'` 函数中操作数据库 + `revalidatePath` |

---

## 8. 认证与授权：NextAuth.js（Auth.js）

用户系统是几乎所有应用的基础。Next.js 生态的标准认证方案是 **NextAuth.js**（现已更名为 **Auth.js**），支持 OAuth、邮箱密码、Magic Link 等多种登录方式。

> 💡 **本章的目标**：集成 GitHub/Google 第三方登录，实现邮箱密码登录，理解会话管理，并用中间件保护受限路由。

### 8.1 NextAuth.js 安装与配置：GitHub/Google OAuth

**安装：**

```bash
npm install next-auth@beta
```

**配置 Auth.js——创建核心配置文件：**

```tsx
// auth.ts（项目根目录）
import NextAuth from 'next-auth';
import GitHub from 'next-auth/providers/github';
import Google from 'next-auth/providers/google';

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    GitHub({
      clientId: process.env.GITHUB_ID!,
      clientSecret: process.env.GITHUB_SECRET!,
    }),
    Google({
      clientId: process.env.GOOGLE_ID!,
      clientSecret: process.env.GOOGLE_SECRET!,
    }),
  ],
});
```

**创建 API 路由——处理 OAuth 回调：**

```tsx
// app/api/auth/[...nextauth]/route.ts
import { handlers } from '@/auth';

export const { GET, POST } = handlers;
```

这一行代码就搞定了所有认证相关的 API 端点：
- `GET /api/auth/signin` — 登录页面
- `GET /api/auth/signout` — 登出
- `POST /api/auth/callback/github` — GitHub OAuth 回调
- `GET /api/auth/session` — 获取当前会话

**配置环境变量：**

```env
# .env.local
AUTH_SECRET="your-random-secret-at-least-32-chars"  # npx auth secret 自动生成

# GitHub OAuth（在 github.com/settings/developers 创建）
GITHUB_ID="your-github-client-id"
GITHUB_SECRET="your-github-client-secret"

# Google OAuth（在 console.cloud.google.com 创建）
GOOGLE_ID="your-google-client-id"
GOOGLE_SECRET="your-google-client-secret"
```

**创建登录/登出按钮：**

```tsx
// components/AuthButtons.tsx
import { signIn, signOut, auth } from '@/auth';

export async function SignInButton() {
  const session = await auth();

  if (session?.user) {
    return (
      <form action={async () => {
        'use server';
        await signOut();
      &#125;&#125;>
        <p>已登录：{session.user.name}</p>
        <button type="submit">登出</button>
      </form>
    );
  }

  return (
    <div>
      <form action={async () => {
        'use server';
        await signIn('github');
      &#125;&#125;>
        <button type="submit">用 GitHub 登录</button>
      </form>
      <form action={async () => {
        'use server';
        await signIn('google');
      &#125;&#125;>
        <button type="submit">用 Google 登录</button>
      </form>
    </div>
  );
}
```

> 💡 **Auth.js v5（beta）的变化**：`signIn` 和 `signOut` 现在是 Server Actions，可以直接在 Server Component 中用 `<form action={signIn}>`。不再需要 `'use client'` + `useSession`（当然客户端组件中仍然可以用）。

### 8.2 Credentials Provider：邮箱密码登录

OAuth 很方便，但有些应用需要传统的邮箱 + 密码登录。Auth.js 用 Credentials Provider 支持。

**在 auth.ts 中添加 Credentials Provider：**

```tsx
// auth.ts
import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import GitHub from 'next-auth/providers/github';
import bcrypt from 'bcryptjs';
import { db } from '@/lib/db';

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    GitHub({ clientId: process.env.GITHUB_ID!, clientSecret: process.env.GITHUB_SECRET! }),
    Credentials({
      name: 'credentials',
      credentials: {
        email: { label: '邮箱', type: 'email' },
        password: { label: '密码', type: 'password' },
      },
      async authorize(credentials) {
        const { email, password } = credentials as {
          email: string;
          password: string;
        };

        // 查找用户
        const user = await db.user.findUnique({ where: { email } });
        if (!user || !user.hashedPassword) return null;

        // 验证密码
        const isValid = await bcrypt.compare(password, user.hashedPassword);
        if (!isValid) return null;

        return { id: user.id, name: user.name, email: user.email };
      },
    }),
  ],
});
```

```bash
npm install bcryptjs
npm install -D @types/bcryptjs
```

**注册功能——用 Server Action 实现：**

```tsx
// app/actions/auth.ts
'use server';

import bcrypt from 'bcryptjs';
import { db } from '@/lib/db';
import { signIn } from '@/auth';

export async function register(formData: FormData) {
  const email = formData.get('email') as string;
  const password = formData.get('password') as string;
  const name = formData.get('name') as string;

  // 检查用户是否已存在
  const existingUser = await db.user.findUnique({ where: { email } });
  if (existingUser) {
    throw new Error('该邮箱已注册');
  }

  // 密码哈希（永远不要存明文密码！）
  const hashedPassword = await bcrypt.hash(password, 12);

  // 创建用户
  await db.user.create({
    data: { email, name, hashedPassword },
  });

  // 自动登录
  await signIn('credentials', { email, password, redirectTo: '/dashboard' });
}
```

> 💡 **安全提醒**：Credentials Provider 需要你自己处理密码安全（哈希、防暴力破解等）。如果不想操心这些，优先用 OAuth 或 Magic Link 方案。

### 8.3 Session 与 JWT：会话管理策略

Auth.js 支持两种会话策略：**JWT（默认）** 和 **Database Session**。

**JWT 策略（默认）：**

```
用户登录 → 生成 JWT Token → 存在 Cookie 中
→ 每次请求带上 Cookie → 服务端验证 Token → 获取用户信息

优点：无需查数据库，速度快
缺点：不能主动"踢人下线"（Token 过期前一直有效）
```

**Database Session 策略：**

```
用户登录 → 在数据库创建 Session 记录 → Session ID 存在 Cookie 中
→ 每次请求带上 Cookie → 查数据库获取 Session → 获取用户信息

优点：可以主动删除 Session（踢人下线）
缺点：每次请求都查数据库，有性能开销
```

**在 Server Component 中获取会话：**

```tsx
// app/dashboard/page.tsx
import { auth } from '@/auth';

export default async function DashboardPage() {
  const session = await auth();  // 直接调用，不需要 Hook

  if (!session) {
    return <p>请先登录</p>;
  }

  return (
    <div>
      <h1>欢迎，{session.user?.name}</h1>
      <img src={session.user?.image || ''} alt="头像" />
      <p>{session.user?.email}</p>
    </div>
  );
}
```

**在 Client Component 中获取会话：**

```tsx
'use client';

import { useSession } from 'next-auth/react';

export default function UserMenu() {
  const { data: session, status } = useSession();

  if (status === 'loading') return <p>加载中...</p>;
  if (!session) return <p>未登录</p>;

  return <p>你好，{session.user?.name}</p>;
}
```

使用 `useSession` 需要在根布局中包裹 `SessionProvider`：

```tsx
// app/layout.tsx
import { SessionProvider } from 'next-auth/react';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
```

**获取会话的方式速查：**

| 场景 | 方法 | 需要 Provider？ |
|:---|:---|:---|
| Server Component | `await auth()` | 不需要 |
| Client Component | `useSession()` | 需要 `SessionProvider` |
| Server Action | `await auth()` | 不需要 |
| Route Handler | `await auth()` | 不需要 |
| Middleware | `auth` 配置中间件 | 不需要 |

> 💡 **推荐做法**：尽量在 Server Component 中用 `await auth()` 获取会话——不需要 Provider，不需要 `'use client'`，更简洁。只有在需要实时响应登录状态变化的 Client Component 中才用 `useSession`。

### 8.4 路由保护：中间件鉴权 + 页面级权限控制

保护路由有两层策略：**中间件（粗粒度）** 和 **页面/Action 内检查（细粒度）**。

**中间件鉴权——Auth.js 内置集成：**

```tsx
// middleware.ts
export { auth as middleware } from '@/auth';

export const config = {
  matcher: ['/dashboard/:path*', '/settings/:path*'],
};
```

然后在 `auth.ts` 中配置 `authorized` 回调：

```tsx
// auth.ts（添加 callbacks）
export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [/* ... */],
  callbacks: {
    authorized({ auth, request }) {
      const isLoggedIn = !!auth?.user;
      const isProtected = request.nextUrl.pathname.startsWith('/dashboard');

      if (isProtected && !isLoggedIn) {
        return false;  // 返回 false → 自动重定向到登录页
      }
      return true;     // 返回 true → 放行
    },
  },
});
```

**页面级权限控制——在 Server Component 中检查：**

```tsx
// app/admin/page.tsx
import { auth } from '@/auth';
import { redirect } from 'next/navigation';

export default async function AdminPage() {
  const session = await auth();

  // 未登录 → 重定向
  if (!session) redirect('/login');

  // 不是管理员 → 403
  if (session.user.role !== 'admin') {
    return (
      <div>
        <h1>403 — 无权访问</h1>
        <p>你没有管理员权限。</p>
      </div>
    );
  }

  return <h1>管理后台</h1>;
}
```

**Server Action 中的权限守卫：**

```tsx
// app/actions/admin.ts
'use server';

import { auth } from '@/auth';

export async function deleteUser(userId: string) {
  const session = await auth();

  // 双重检查：必须登录 + 必须是管理员
  if (!session) throw new Error('请先登录');
  if (session.user.role !== 'admin') throw new Error('无权操作');

  await db.user.delete({ where: { id: userId } });
  revalidatePath('/admin/users');
}
```

**三层防御的组合策略：**

```
第 1 层：中间件（粗粒度）
  → 未登录用户不能进入 /dashboard/*
  → 速度快，在请求到达页面之前就拦截

第 2 层：页面组件（细粒度）
  → 检查用户角色、权限等级
  → 可以返回自定义的 403 页面

第 3 层：Server Action（操作级）
  → 每个数据变更操作都检查权限
  → 防止绕过前端直接调用
```

> 💡 **安全原则**：永远不要只依赖前端来保护数据。即使中间件拦截了路由，Server Action 和 API 路由中仍然要做权限检查——因为恶意用户可以直接发 HTTP 请求。

**第 8 章核心知识回顾：**

| 概念 | 要点 |
|:---|:---|
| Auth.js 配置 | `auth.ts` 导出 `handlers`/`signIn`/`signOut`/`auth` |
| OAuth Provider | GitHub/Google 第三方登录，几行代码搞定 |
| Credentials | 邮箱密码登录，需要自己处理密码哈希 |
| Session 获取 | Server 用 `await auth()`，Client 用 `useSession()` |
| 中间件鉴权 | `export { auth as middleware }`，粗粒度路由保护 |
| 权限三层防御 | 中间件 → 页面组件 → Server Action |

---

## 9. 状态管理与表单处理

在纯 React 时代，状态管理是个大话题——Redux、Zustand、Jotai、Recoil……选择困难症。但在 Next.js App Router 下，**大部分状态问题已经被框架解决了**。

> 💡 **本章的目标**：理解 App Router 下的状态分类，学会用 URL 管理页面状态，掌握表单处理和乐观更新。

### 9.1 Server State vs Client State：何时需要状态管理

先搞清楚一个关键问题：App Router 下到底还需不需要状态管理库？

**状态分类：**

| 类型 | 描述 | 在哪管理 |
|:---|:---|:---|
| Server State | 来自数据库/API 的数据 | Server Components 直接获取，不需要状态管理 |
| URL State | 搜索、筛选、分页、排序 | `searchParams`，存在 URL 中 |
| Form State | 表单输入值、验证错误 | React Hook Form 或 `useState` |
| UI State | 模态框开关、侧边栏折叠 | `useState`（局部状态） |
| Global Client State | 跨组件共享的客户端状态 | Zustand / Context（很少需要） |

**关键认知——大部分 "状态管理" 已经不需要了：**

```
传统 React（SPA）：
  数据从 API 获取 → 存到 Redux/Zustand → 组件从 Store 读取
  → 需要处理 loading/error/缓存/同步/失效……

Next.js App Router：
  Server Component 直接拿数据 → 传给子组件
  → 没有 loading 问题（loading.tsx 自动处理）
  → 没有缓存问题（Next.js 内置缓存）
  → 没有同步问题（每次请求都是最新数据）
```

**什么时候真的需要客户端状态管理库？**

- ✅ **需要**：复杂的多步表单向导（5+ 步骤之间共享数据）
- ✅ **需要**：实时协作编辑器（多用户同时编辑同一文档）
- ✅ **需要**：购物车（跨多个页面的全局客户端状态）
- ❌ **不需要**：列表页面的数据展示（Server Component 搞定）
- ❌ **不需要**：搜索和筛选（URL State 搞定）
- ❌ **不需要**：一个模态框的开关（`useState` 搞定）

> 💡 **实际项目中的建议**：先不装任何状态管理库。遇到确实需要跨组件共享客户端状态时，用 **Zustand**（轻量、简单、不需要 Provider）。绝大多数 Next.js 项目不需要 Redux。

### 9.2 URL State：用 searchParams 管理筛选/分页状态

把搜索、筛选、分页状态存在 URL 中（`?q=nextjs&page=2&sort=latest`），是 Next.js 中最推荐的做法。

**为什么用 URL 而不是 `useState`？**
- ✅ 可分享：用户可以把带筛选条件的链接发给别人
- ✅ 可收藏：浏览器书签保存当前筛选状态
- ✅ SEO 友好：搜索引擎可以抓取不同的筛选结果页
- ✅ 浏览器前进/后退自然工作

**Server Component 读取 searchParams：**

```tsx
// app/posts/page.tsx
export default async function PostsPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; page?: string; sort?: string }>;
}) {
  const { q, page = '1', sort = 'latest' } = await searchParams;

  const posts = await db.post.findMany({
    where: q ? { title: { contains: q, mode: 'insensitive' } } : {},
    orderBy: { createdAt: sort === 'latest' ? 'desc' : 'asc' },
    skip: (parseInt(page) - 1) * 10,
    take: 10,
  });

  return (
    <div>
      <SearchBar defaultValue={q} />
      <PostList posts={posts} />
      <Pagination currentPage={parseInt(page)} />
    </div>
  );
}
```

**Client Component 更新 searchParams：**

```tsx
// components/SearchBar.tsx
'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useDebouncedCallback } from 'use-debounce';

export default function SearchBar({ defaultValue }: { defaultValue?: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // 防抖：用户停止输入 300ms 后才更新 URL
  const handleSearch = useDebouncedCallback((term: string) => {
    const params = new URLSearchParams(searchParams.toString());

    if (term) {
      params.set('q', term);
    } else {
      params.delete('q');
    }
    params.set('page', '1');  // 搜索时重置到第1页

    router.push(`?${params.toString()}`);
  }, 300);

  return (
    <input
      type="text"
      placeholder="搜索文章..."
      defaultValue={defaultValue}
      onChange={e => handleSearch(e.target.value)}
    />
  );
}
```

```bash
npm install use-debounce
```

> 💡 **URL 更新后会怎样？** `router.push('?q=nextjs')` 会触发页面的 Server Component 重新执行（带上新的 searchParams），数据自动刷新。不需要手动 fetch 或管理 loading 状态。

### 9.3 React Hook Form + Zod：类型安全的表单验证

复杂表单（多字段、嵌套验证、实时错误提示）用 React Hook Form + Zod 是最佳组合。

```bash
npm install react-hook-form @hookform/resolvers zod
```

**完整示例——注册表单：**

```tsx
// components/RegisterForm.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { register as registerAction } from '@/app/actions/auth';

// 定义 Schema——类型和验证规则一体化
const registerSchema = z.object({
  name: z.string().min(2, '姓名至少 2 个字'),
  email: z.string().email('请输入有效的邮箱'),
  password: z.string().min(8, '密码至少 8 位'),
  confirmPassword: z.string(),
}).refine(data => data.password === data.confirmPassword, {
  message: '两次密码不一致',
  path: ['confirmPassword'],
});

// 从 Schema 自动推断 TypeScript 类型
type RegisterValues = z.infer<typeof registerSchema>;

export default function RegisterForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
  });

  async function onSubmit(data: RegisterValues) {
    const formData = new FormData();
    formData.set('name', data.name);
    formData.set('email', data.email);
    formData.set('password', data.password);
    await registerAction(formData);
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <input {...register('name')} placeholder="姓名" />
        {errors.name && <p className="text-red-500">{errors.name.message}</p>}
      </div>

      <div>
        <input {...register('email')} type="email" placeholder="邮箱" />
        {errors.email && <p className="text-red-500">{errors.email.message}</p>}
      </div>

      <div>
        <input {...register('password')} type="password" placeholder="密码" />
        {errors.password && <p className="text-red-500">{errors.password.message}</p>}
      </div>

      <div>
        <input {...register('confirmPassword')} type="password" placeholder="确认密码" />
        {errors.confirmPassword && <p className="text-red-500">{errors.confirmPassword.message}</p>}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? '注册中...' : '注册'}
      </button>
    </form>
  );
}
```

**为什么用 React Hook Form？**

| 特性 | 说明 |
|:---|:---|
| 非受控组件 | 不用 `useState` 管理每个字段，性能更好 |
| 自动验证 | 配合 Zod resolver，输入时实时验证 |
| TypeScript 推断 | Schema → 类型自动推断，一处定义到处用 |
| 极小体积 | ~9KB gzipped，比 Formik 小得多 |

> 💡 **简单表单不需要 React Hook Form**。如果只有 1-2 个输入框，直接用 `<form action={serverAction}>` + 原生 FormData 就够了（参见第 4 章 Server Actions）。React Hook Form 适合 3+ 字段的复杂表单。

### 9.4 乐观更新与加载状态：useOptimistic、useFormStatus

**`useFormStatus` — 获取表单的提交状态：**

当用 `<form action={serverAction}>` 时，怎么知道表单正在提交中？用 `useFormStatus`。

```tsx
// components/SubmitButton.tsx
'use client';

import { useFormStatus } from 'react-dom';

export function SubmitButton({ children }: { children: React.ReactNode }) {
  const { pending } = useFormStatus();

  return (
    <button type="submit" disabled={pending}>
      {pending ? '提交中...' : children}
    </button>
  );
}
```

```tsx
// 使用——在任何 Server Action 表单中
import { SubmitButton } from '@/components/SubmitButton';

export default function NewPost() {
  return (
    <form action={createPost}>
      <input name="title" />
      <SubmitButton>发布文章</SubmitButton>  {/* 提交时自动显示"提交中…" */}
    </form>
  );
}
```

> ⚠️ **`useFormStatus` 必须在 `<form>` 的子组件中使用**，不能和 `<form>` 在同一个组件里。所以要把按钮抽成独立组件。

**`useOptimistic` — 乐观更新（先更新 UI，再等服务端确认）：**

```tsx
// components/LikeButton.tsx
'use client';

import { useOptimistic } from 'react';
import { likePost } from '@/app/actions/post';

export default function LikeButton({
  postId,
  initialLikes,
}: {
  postId: string;
  initialLikes: number;
}) {
  const [optimisticLikes, addOptimisticLike] = useOptimistic(
    initialLikes,
    (currentLikes: number) => currentLikes + 1  // 乐观更新逻辑
  );

  async function handleLike() {
    addOptimisticLike(1);       // 立即 +1（UI 瞬间响应）
    await likePost(postId);     // 然后发请求给服务端
    // 如果请求失败，React 会自动回滚到 initialLikes
  }

  return (
    <form action={handleLike}>
      <button type="submit">❤️ {optimisticLikes}</button>
    </form>
  );
}
```

**乐观更新的流程：**

```
用户点击"赞" → UI 立即显示 likes + 1（乐观更新）
    ↓
后台发 Server Action 请求
    ↓
成功 → 服务端返回真实数据，验证一致
失败 → React 自动回滚到点击前的状态
```

**第 9 章核心知识回顾：**

| 概念 | 要点 |
|:---|:---|
| 状态分类 | Server State / URL State / Form State / UI State / Global State |
| URL State | `searchParams` 管理筛选/分页，可分享、可收藏、SEO 友好 |
| React Hook Form | 非受控组件 + Zod 验证，适合复杂表单 |
| `useFormStatus` | 获取 `<form action>` 的提交状态（pending） |
| `useOptimistic` | 先更新 UI 再等服务端确认，失败自动回滚 |
| 状态管理库 | 绝大多数 Next.js 项目不需要 Redux，必要时用 Zustand |

---

## 10. 性能优化：让应用飞起来

Next.js 号称"零配置优化"，但要发挥最大效果，你需要理解它在背后做了什么，以及如何正确使用这些优化手段。

> 💡 **本章的目标**：掌握图片/字体优化、代码分割、缓存体系，让你的应用达到 Lighthouse 90+ 的性能评分。

### 10.1 图片优化：next/image 的正确使用

`next/image` 是 Next.js 最强大的内置优化之一——自动压缩、格式转换（WebP/AVIF）、懒加载、防止布局偏移。

**基本用法——已知尺寸的图片：**

```tsx
import Image from 'next/image';

export default function Hero() {
  return (
    <Image
      src="/hero.jpg"          // public 目录下的图片
      alt="首页横幅"
      width={1200}             // 必须指定宽高（防止布局偏移）
      height={600}
      priority                 // 首屏图片加 priority，禁用懒加载
    />
  );
}
```

**`next/image` 自动做了什么：**

```
原始图片：hero.jpg (2MB, 4000x2000, JPEG)

next/image 处理后：
  → 格式转换：自动转 WebP/AVIF（体积缩小 30-50%）
  → 尺寸适配：根据设备屏幕生成多种尺寸（srcset）
  → 懒加载：视口外的图片不加载，滚动到时才请求
  → 缓存：处理后的图片缓存在服务端，不重复处理
  → 防偏移：提前占位预留空间，图片加载时页面不跳动
```

**远程图片——需要配置域名：**

```tsx
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'avatars.githubusercontent.com',  // GitHub 头像
      },
      {
        protocol: 'https',
        hostname: '**.cloudinary.com',              // Cloudinary CDN
      },
    ],
  },
};

export default nextConfig;
```

```tsx
// 使用远程图片
<Image
  src="https://avatars.githubusercontent.com/u/12345"
  alt="用户头像"
  width={64}
  height={64}
  className="rounded-full"
/>
```

**Fill 模式——父容器决定尺寸：**

当你不知道图片的具体尺寸，或者想让图片充满父容器时：

```tsx
<div className="relative h-[400px] w-full">
  <Image
    src="/banner.jpg"
    alt="横幅"
    fill                          // 填充父容器
    className="object-cover"      // 裁剪方式
    sizes="(max-width: 768px) 100vw, 50vw"  // 响应式提示
  />
</div>
```

**`sizes` 属性——告诉浏览器图片的展示宽度：**

| `sizes` 值 | 含义 |
|:---|:---|
| `100vw` | 图片占满整个屏幕宽度 |
| `50vw` | 图片占屏幕宽度的一半 |
| `(max-width: 768px) 100vw, 33vw` | 手机上占满宽度，桌面上占 1/3 |

> 💡 **不加 `sizes` 属性，浏览器会默认按 100vw 来请求图片**——这意味着在小屏手机上也会下载超大图片，浪费带宽。列表页的缩略图一定要加 `sizes`。

### 10.2 字体优化：next/font 消除布局偏移

第 5 章已经介绍了 `next/font` 的基本用法。这里从性能角度深入解析。

**传统方式 vs next/font：**

```
传统方式（Google Fonts CDN）：
  1. 浏览器加载 HTML
  2. 解析到 <link href="fonts.googleapis.com/...">
  3. 发请求到 Google 服务器下载 CSS
  4. CSS 里又指向字体文件的 URL
  5. 再次请求下载字体文件
  6. 字体加载完成，页面文字突然变化 → 布局偏移（CLS）
  总共：2 次 DNS 解析 + 2 次请求 + 布局偏移

next/font：
  1. 构建时自动下载字体文件到本地
  2. 字体文件和应用一起部署
  3. 浏览器加载 HTML 时，字体 CSS 内联在 <head> 中
  4. 字体文件从同域加载（无额外 DNS）
  5. 自动添加 size-adjust，消除布局偏移
  总共：0 次外部 DNS + 0 布局偏移
```

**本地字体文件的使用：**

```tsx
import localFont from 'next/font/local';

const myFont = localFont({
  src: [
    { path: './fonts/MyFont-Regular.woff2', weight: '400', style: 'normal' },
    { path: './fonts/MyFont-Bold.woff2', weight: '700', style: 'normal' },
  ],
  display: 'swap',
  variable: '--font-custom',
});
```

**字体性能最佳实践：**

| 实践 | 说明 |
|:---|:---|
| 用 `display: 'swap'` | 字体未加载时先显示系统字体，不阻塞渲染 |
| 只加载需要的字重 | 每个字重约 20-50KB，少加载 = 少下载 |
| 用 `woff2` 格式 | 压缩率最高的字体格式 |
| 设置 `subsets` | 只加载需要的字符子集（如 `latin`） |
| 用 `variable` | 定义 CSS 变量，方便 Tailwind 引用 |

> 💡 **中文字体的特殊性**：中文字体文件通常很大（5-20MB），不适合用 `next/font` 整个加载。推荐方案：用系统中文字体（`"PingFang SC", "Microsoft YaHei", sans-serif`），或使用字体子集化服务只加载页面用到的汉字。

### 10.3 代码分割与懒加载：dynamic import

Next.js 自动对每个页面做代码分割——访问 `/about` 时不会加载 `/dashboard` 的代码。但有时你需要**更细粒度**的懒加载。

**`next/dynamic` — 组件级别的懒加载：**

```tsx
import dynamic from 'next/dynamic';

// 懒加载——只在需要时才加载这个组件的代码
const HeavyEditor = dynamic(() => import('@/components/RichTextEditor'), {
  loading: () => <p>编辑器加载中...</p>,  // 加载时的占位
});

export default function PostEditPage() {
  return (
    <div>
      <h1>编辑文章</h1>
      <HeavyEditor />  {/* 用户访问这个页面时才下载编辑器的 JS */}
    </div>
  );
}
```

**禁用 SSR——纯客户端组件：**

有些第三方库（图表、地图、编辑器）不支持服务端渲染，会报 `window is not defined`：

```tsx
// ❌ 直接 import 可能在服务端报错
import MapComponent from 'react-leaflet';

// ✅ 用 dynamic + ssr: false
const Map = dynamic(() => import('@/components/Map'), {
  ssr: false,  // 只在客户端加载，跳过服务端渲染
  loading: () => <div className="h-[400px] bg-gray-100 animate-pulse" />,
});
```

**什么时候用 dynamic？**

| 场景 | 是否用 dynamic |
|:---|:---|
| 富文本编辑器（Tiptap、CKEditor） | ✅ 体积大，按需加载 |
| 图表库（Recharts、Chart.js） | ✅ 不是每个用户都需要 |
| 地图组件（Leaflet、Mapbox） | ✅ 需要 `ssr: false` |
| 模态框内容 | ✅ 打开时才加载 |
| 导航栏、页脚 | ❌ 每个页面都需要，不用懒加载 |
| 小型 UI 组件（按钮、输入框） | ❌ 体积小，懒加载反而增加延迟 |

> 💡 **懒加载的代价**：每次 dynamic import 都会产生一次额外的网络请求。对于体积很小的组件（< 5KB），懒加载反而让体验变差（看到 loading 闪烁）。只对**体积大、非首屏**的组件使用 dynamic。

### 10.4 缓存策略全览：Data Cache、Full Route Cache、Router Cache

Next.js 有四层缓存机制，理解它们是性能调优的关键。

**四层缓存体系：**

```
请求进来 →

第 1 层：Request Memoization（请求去重）
  同一次渲染中，相同的 fetch URL 只执行一次
  范围：单次请求（页面渲染完成后自动清除）

第 2 层：Data Cache（数据缓存）
  fetch 结果缓存在服务端
  范围：跨请求持久化（直到 revalidate 触发）

第 3 层：Full Route Cache（完整路由缓存）
  静态生成的页面 HTML + RSC Payload 缓存
  范围：构建时生成，部署后持久化

第 4 层：Router Cache（路由缓存）
  客户端缓存访问过的路由
  范围：用户会话期间（浏览器内存中）
```

**四层缓存速查表：**

| 缓存层 | 位置 | 缓存什么 | 持续时间 | 如何失效 |
|:---|:---|:---|:---|:---|
| Request Memoization | 服务端 | 相同的 fetch 请求 | 单次渲染 | 自动清除 |
| Data Cache | 服务端 | fetch 响应数据 | 持久化 | `revalidate` / `revalidateTag` |
| Full Route Cache | 服务端 | HTML + RSC Payload | 持久化 | 重新部署 / `revalidatePath` |
| Router Cache | 客户端 | 已访问的路由 | 会话期间 | `router.refresh()` / 过期 |

**常见的缓存问题和解决方案：**

```tsx
// 问题 1："我更新了数据，但页面没变化"
// 原因：Data Cache 或 Full Route Cache 没有失效
// 解决：在 Server Action 中调用 revalidatePath
async function updatePost(formData: FormData) {
  'use server';
  await db.post.update({ ... });
  revalidatePath('/posts');  // ← 让缓存失效
}

// 问题 2："客户端导航回列表页，看到的是旧数据"
// 原因：Router Cache 缓存了之前的页面
// 解决：Server Action 中的 revalidatePath 会自动通知客户端
// 或者用 router.refresh() 强制刷新

// 问题 3："开发环境看到最新数据，部署后看不到"
// 原因：生产环境的默认缓存策略更激进
// 解决：根据页面特性设置正确的 revalidate 或 dynamic
export const revalidate = 60;  // 每 60 秒重新生成
// 或
export const dynamic = 'force-dynamic';  // 每次请求都重新渲染
```

**选择正确的缓存策略：**

| 页面类型 | 推荐策略 | 配置 |
|:---|:---|:---|
| 营销页面、关于我们 | 纯静态 | 默认（不需要配置） |
| 博客文章 | ISR | `revalidate = 3600`（1小时） |
| 商品列表 | ISR | `revalidate = 60`（1分钟） |
| 用户仪表盘 | 动态渲染 | `dynamic = 'force-dynamic'` |
| 实时聊天 | 动态 + 客户端 | Server Component + SWR 轮询 |

> 💡 **缓存调试技巧**：在开发环境中，Data Cache 默认不启用（每次都获取最新数据）。部署到生产环境后才能看到缓存效果。如果想在开发环境测试缓存行为，运行 `next build && next start` 启动生产模式。

**第 10 章核心知识回顾：**

| 概念 | 要点 |
|:---|:---|
| `next/image` | 自动格式转换、尺寸适配、懒加载、防偏移 |
| `next/font` | 字体自托管、构建时下载、零布局偏移 |
| `next/dynamic` | 组件级懒加载、`ssr: false` 禁用服务端渲染 |
| 四层缓存 | Memoization → Data → Full Route → Router |
| 缓存失效 | `revalidatePath` / `revalidateTag` / `router.refresh()` |
| 策略选择 | 根据数据更新频率选择静态/ISR/动态渲染 |

---

## 11. 测试策略：从单元测试到 E2E

不写测试的应用，改一个功能就可能蹦掉三个。Next.js 项目的测试有其特殊性——Server Components 和 Client Components 的测试方式不同。

> 💡 **本章的目标**：搭建 Jest + Playwright 测试环境，掌握不同层级的测试方法，建立实用的测试策略。

### 11.1 单元测试：Jest + React Testing Library

**安装和配置：**

```bash
npm install -D jest @jest/types ts-jest @testing-library/react @testing-library/jest-dom jest-environment-jsdom
```

```tsx
// jest.config.ts
import type { Config } from 'jest';
import nextJest from 'next/jest';

const createJestConfig = nextJest({
  dir: './',  // Next.js 项目根目录
});

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterSetup: ['<rootDir>/jest.setup.ts'],
};

export default createJestConfig(config);
```

```tsx
// jest.setup.ts
import '@testing-library/jest-dom';
```

```json
// package.json 添加脚本
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch"
  }
}
```

**测试 Client Component：**

```tsx
// components/Counter.tsx
'use client';
import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);
  return (
    <div>
      <p data-testid="count">计数：{count}</p>
      <button onClick={() => setCount(count + 1)}>+1</button>
    </div>
  );
}
```

```tsx
// components/__tests__/Counter.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import Counter from '../Counter';

describe('Counter', () => {
  it('初始值为 0', () => {
    render(<Counter />);
    expect(screen.getByTestId('count')).toHaveTextContent('计数：0');
  });

  it('点击按钮后计数加 1', () => {
    render(<Counter />);
    fireEvent.click(screen.getByText('+1'));
    expect(screen.getByTestId('count')).toHaveTextContent('计数：1');
  });
});
```

**测试工具函数（纯逻辑）：**

```tsx
// lib/utils.ts
export function formatDate(date: Date): string {
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
    .replace(/^-|-$/g, '');
}
```

```tsx
// lib/__tests__/utils.test.ts
import { formatDate, slugify } from '../utils';

describe('formatDate', () => {
  it('格式化日期为中文格式', () => {
    const date = new Date('2024-03-15');
    expect(formatDate(date)).toBe('2024年3月15日');
  });
});

describe('slugify', () => {
  it('将文本转为 URL 友好的 slug', () => {
    expect(slugify('Hello World')).toBe('hello-world');
    expect(slugify('Next.js 教程')).toBe('next-js-教程');
  });
});
```

> 💡 **运行测试**：`npm test` 运行所有测试，`npm run test:watch` 监听文件变化自动运行。

### 11.2 组件测试：Server Components 的测试挑战

Server Components 是 `async` 函数，直接获取数据——传统的 `render(<Component />)` 对它们不太好使。

**挑战与解决方案：**

```tsx
// ❌ 不能直接测试 async Server Component
// 原因：React Testing Library 不支持渲染 async 组件
import { render } from '@testing-library/react';
import PostsPage from '../app/posts/page';

render(<PostsPage />);  // ← 报错：不支持 async 组件
```

**策略 1：拆分逻辑，测试数据层：**

```tsx
// lib/posts.ts — 把数据获取逻辑独立出来
import { db } from '@/lib/db';

export async function getPublishedPosts() {
  return db.post.findMany({
    where: { published: true },
    orderBy: { createdAt: 'desc' },
  });
}
```

```tsx
// lib/__tests__/posts.test.ts
import { getPublishedPosts } from '../posts';
import { db } from '@/lib/db';

// Mock Prisma Client
jest.mock('@/lib/db', () => ({
  db: {
    post: {
      findMany: jest.fn(),
    },
  },
}));

describe('getPublishedPosts', () => {
  it('只返回已发布的文章，按时间倒序', async () => {
    const mockPosts = [
      { id: '1', title: '文章 1', published: true },
      { id: '2', title: '文章 2', published: true },
    ];
    (db.post.findMany as jest.Mock).mockResolvedValue(mockPosts);

    const result = await getPublishedPosts();

    expect(result).toEqual(mockPosts);
    expect(db.post.findMany).toHaveBeenCalledWith({
      where: { published: true },
      orderBy: { createdAt: 'desc' },
    });
  });
});
```

**策略 2：测试纯展示的子组件：**

```tsx
// components/PostCard.tsx — 纯展示组件（Server 或 Client 都可以）
export default function PostCard({ title, date }: { title: string; date: string }) {
  return (
    <article>
      <h2>{title}</h2>
      <time>{date}</time>
    </article>
  );
}
```

```tsx
// components/__tests__/PostCard.test.tsx
import { render, screen } from '@testing-library/react';
import PostCard from '../PostCard';

it('正确显示文章标题和日期', () => {
  render(<PostCard title="Hello" date="2024-03-15" />);
  expect(screen.getByText('Hello')).toBeInTheDocument();
  expect(screen.getByText('2024-03-15')).toBeInTheDocument();
});
```

> 💡 **实用建议**：不要强求测试 Server Component 本身。把数据获取逻辑抽到独立函数中测试，把 UI 拆成纯展示组件测试。真正的页面级测试交给 E2E（Playwright）。

### 11.3 E2E 测试：Playwright 集成

E2E（End-to-End）测试是最接近真实用户操作的测试——打开浏览器、点击按钮、填写表单、验证结果。

**安装 Playwright：**

```bash
npm install -D @playwright/test
npx playwright install  # 下载浏览器引擎
```

```tsx
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['iPhone 14'] } },
  ],
});
```

**完整的 E2E 测试示例：**

```tsx
// e2e/blog.spec.ts
import { test, expect } from '@playwright/test';

test.describe('博客功能', () => {
  test('首页显示文章列表', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.locator('article')).toHaveCount(10);  // 至少显示文章
  });

  test('点击文章进入详情页', async ({ page }) => {
    await page.goto('/blog');
    const firstArticle = page.locator('article').first();
    const title = await firstArticle.locator('h2').textContent();

    await firstArticle.click();

    // 验证跳转到了详情页，标题正确
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(title!);
    await expect(page.url()).toContain('/blog/');
  });

  test('搜索功能', async ({ page }) => {
    await page.goto('/blog');
    await page.getByPlaceholder('搜索文章').fill('Next.js');
    // 等待搜索结果更新
    await page.waitForURL('**/blog?q=Next.js**');
    // 验证结果中包含搜索词
    const articles = page.locator('article');
    await expect(articles.first()).toContainText('Next.js');
  });

  test('登录后才能发表文章', async ({ page }) => {
    await page.goto('/blog/new');
    // 未登录应重定向到登录页
    await expect(page.url()).toContain('/login');
  });
});
```

```json
// package.json 添加脚本
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

> 💡 **`playwright test --ui`** 会打开一个可视化界面，可以逐步回放测试过程、查看每一步的截图，调试非常方便。

### 11.4 测试策略：测什么、不测什么

时间有限，不可能测试每一行代码。关键是知道把精力花在哪。

**Next.js 项目的测试金字塔：**

```
              /\
             /  \      E2E 测试（Playwright）
            / 少 \     → 核心用户流程：登录、发文、付款
           /------\
          /        \   集成测试（Server Actions / API）
         /   适量   \  → 数据变更、权限校验
        /------------\
       /              \ 单元测试（Jest）
      /      多       \ → 工具函数、数据层、纯展示组件
     /------------------\
```

**应该测的（高价值）：**

| 类型 | 测什么 | 工具 |
|:---|:---|:---|
| 工具函数 | `formatDate`、`slugify`、计算逻辑 | Jest |
| 数据层 | `getPublishedPosts`、数据库查询逻辑 | Jest + Mock |
| Server Actions | 权限检查、输入验证、数据变更 | Jest |
| 表单交互 | 验证规则、提交流程、错误提示 | Testing Library |
| 核心流程 | 注册→登录→发文→查看 | Playwright |
| 权限控制 | 未登录访问受保护页面→重定向 | Playwright |

**不应该测的（低价值 / 浪费时间）：**

| 不要测 | 原因 |
|:---|:---|
| 框架行为 | `<Link>` 能不能跳转、`next/image` 会不会优化——这是 Next.js 的责任 |
| 第三方库 | shadcn/ui 的按钮能不能点击——这是它的责任 |
| 单纯的样式 | 按钮是不是蓝色——改个主题全都得改，脆弱测试 |
| 1:1 实现细节 | "组件内部 state 是不是 3"——测行为，不测实现 |

**实用的测试比例建议：**

```
新项目启动期：
  → 只写 E2E 测试覆盖核心流程（投入产出比最高）
  → 工具函数的单元测试

项目稳定期：
  → 单元测试 60%（覆盖所有工具函数和数据层）
  → E2E 测试 30%（覆盖所有用户关键路径）
  → 集成测试 10%（复杂的 Server Action 逻辑）
```

> 💡 **务实原则**：一个没有任何测试的项目，加 5 个 E2E 测试覆盖核心流程，比加 50 个单元测试有价值得多。先保证"用户能正常使用"，再去追求覆盖率。

**第 11 章核心知识回顾：**

| 概念 | 要点 |
|:---|:---|
| Jest 配置 | `next/jest` 自动处理 Next.js 相关配置 |
| Client Component 测试 | `render` + `fireEvent` + `expect` |
| Server Component 测试 | 拆分数据层独立测试 + 纯展示组件测试 |
| E2E 测试 | Playwright，测完整用户流程 |
| 测试策略 | 优先 E2E 核心流程 + 工具函数单元测试 |
| 不要测 | 框架行为、第三方库、纯样式 |

---

## 12. 部署与上线：Vercel + 自托管方案

代码写完了，怎么让全世界都能访问？Next.js 的部署方式从"零配置"到"完全掌控"都有选择。

> 💡 **本章的目标**：掌握 Vercel 一键部署、环境变量管理、Docker 自托管方案，以及 GitHub Actions CI/CD 流程。

### 12.1 Vercel 部署：Git Push 即上线

Vercel 是 Next.js 的"亲妈"公司，部署 Next.js 的体验是**最丝滑**的——推代码就上线。

**部署步骤（5 分钟搞定）：**

```
1. 把项目推到 GitHub 仓库
2. 访问 vercel.com → Sign up with GitHub
3. 点击 "Import Project" → 选择你的仓库
4. Vercel 自动检测到 Next.js → 点击 "Deploy"
5. 等待 1-2 分钟 → 部署完成，得到一个 xxx.vercel.app 的 URL
```

**之后每次更新：**

```
git add . && git commit -m "新功能" && git push

→ Vercel 自动触发构建
→ 构建成功 → 自动部署到生产环境
→ 构建失败 → 不影响现有版本，收到邮件通知
```

**Preview 环境——每个 PR 自动部署预览：**

```
你提交了一个 Pull Request
  → Vercel 自动为这个 PR 构建一个独立的预览环境
  → 生成 preview-xxx.vercel.app 的 URL
  → 团队成员可以直接访问预览链接 review 效果
  → PR 合并后预览环境自动删除
```

**Vercel 的内置优化：**

| 特性 | 说明 |
|:---|:---|
| 全球边缘网络 | 静态资源自动分发到全球 CDN |
| Serverless Functions | Server Components / API 路由自动变成 Serverless |
| 自动 HTTPS | 免费 SSL 证书，自动配置 |
| 域名绑定 | 添加自定义域名，自动 DNS 配置 |
| 分析面板 | Web Vitals、流量统计 |
| ISR 支持 | 增量静态再生成，开箱即用 |

> 💡 **Vercel 的限制**：免费版有带宽和执行时间限制（Hobby 计划），企业应用可能需要 Pro 计划（$20/月/成员）。如果需要完全掌控或有合规要求，考虑 Docker 自托管。

### 12.2 环境变量管理：开发/预览/生产环境

不同环境用不同的数据库、API Key——环境变量管理是部署的重要环节。

**Next.js 的 `.env` 文件层级：**

```
.env                  ← 基础值（所有环境通用）
.env.local            ← 本地覆盖（不提交到 Git！）
.env.development      ← 仅 npm run dev 时加载
.env.production       ← 仅 npm run build 时加载
```

加载优先级：`.env.local` > `.env.development` / `.env.production` > `.env`

**`NEXT_PUBLIC_` 前缀——决定变量是否暴露给客户端：**

```env
# .env.local

# ✅ 只在服务端可用——安全
DATABASE_URL="postgresql://..."
AUTH_SECRET="super-secret-key"
STRIPE_SECRET_KEY="sk_live_..."

# ✅ 客户端也可用（会打包到 JS 中）——只放公开信息
NEXT_PUBLIC_API_URL="https://api.example.com"
NEXT_PUBLIC_SITE_NAME="My Blog"
NEXT_PUBLIC_GA_ID="G-XXXXXXXXXX"
```

```tsx
// Server Component / Server Action — 可以访问所有环境变量
const dbUrl = process.env.DATABASE_URL;           // ✅
const apiUrl = process.env.NEXT_PUBLIC_API_URL;   // ✅

// Client Component — 只能访问 NEXT_PUBLIC_ 开头的
const apiUrl = process.env.NEXT_PUBLIC_API_URL;   // ✅
const dbUrl = process.env.DATABASE_URL;           // ❌ undefined
```

**Vercel 环境变量配置：**

```
Vercel Dashboard → 项目 → Settings → Environment Variables

每个变量可以指定生效的环境：
  ☑ Production     — 生产环境
  ☑ Preview        — PR 预览环境
  ☑ Development    — 开发环境（可以 vercel env pull 拉到本地）
```

**环境变量安全规则：**

| 规则 | 说明 |
|:---|:---|
| 敏感信息不加 `NEXT_PUBLIC_` | API Key、数据库密码只在服务端用 |
| `.env.local` 加入 `.gitignore` | 绝不把本地密钥提交到 Git |
| 生产密钥放在部署平台 | Vercel / 服务器的环境变量中配置 |
| 定期轮换密钥 | 尤其是 `AUTH_SECRET`、支付密钥 |

> 💡 **`vercel env pull`**：可以把 Vercel 上配置的环境变量拉到本地的 `.env.local` 文件中，省去手动复制。

### 12.3 Docker 自托管部署：Standalone Output

不想用 Vercel？可以用 Docker 部署到任何服务器（AWS、阿里云、自己的 VPS）。

**Step 1：启用 Standalone Output：**

```tsx
// next.config.ts
const nextConfig = {
  output: 'standalone',  // ← 生成独立可运行的输出
};

export default nextConfig;
```

`standalone` 模式会把所有需要的 Node.js 依赖打包在一起，生成一个最小化的部署包（通常只有 50-100MB，而不是完整的 node_modules 的 500MB+）。

**Step 2：多阶段 Dockerfile（生产级优化）：**

```dockerfile
# Dockerfile
FROM node:20-alpine AS base

# 安装依赖
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# 构建
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npx prisma generate
RUN npm run build

# 生产运行
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

# 创建非 root 用户（安全）
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 复制构建产物
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

**Step 3：构建并运行：**

```bash
# 构建镜像
docker build -t my-nextjs-app .

# 运行容器
docker run -p 3000:3000 \
  -e DATABASE_URL="postgresql://..." \
  -e AUTH_SECRET="..." \
  my-nextjs-app
```

**配合 Docker Compose（加上数据库）：**

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/mydb
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

> 💡 **Standalone 模式的 Docker 镜像只有约 100-150MB**，比不用 standalone 的 1GB+ 小很多。生产部署一定要用 standalone + 多阶段构建。

### 12.4 CI/CD 流程：GitHub Actions 自动化

CI/CD 让每次提交代码都自动经过检查、测试、构建、部署——避免"在我机器上是好的"。

**完整的 GitHub Actions 配置：**

::: v-pre
```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # 第 1 步：代码检查
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npx tsc --noEmit  # TypeScript 类型检查

  # 第 2 步：单元测试
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm test

  # 第 3 步：构建验证
  build:
    runs-on: ubuntu-latest
    needs: [lint, test]  # lint 和 test 通过后才构建
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run build
    env:
      DATABASE_URL: $&#123;&#123; secrets.DATABASE_URL &#125;&#125;

  # 第 4 步：部署到生产（仅 main 分支）
  deploy:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      # 如果用 Vercel，这一步可以省略（Vercel 会自动部署）
      # 如果用 Docker，在这里构建镜像并推送到容器仓库
      - name: Deploy to production
        run: echo "部署逻辑放在这里"
```
:::

**部署方案对比：**

| 方案 | 优点 | 缺点 | 适合 |
|:---|:---|:---|:---|
| Vercel | 零配置、自动 CI/CD、Preview | 有限制、成本递增 | 小到中型项目 |
| Docker + VPS | 完全掌控、成本固定 | 需要运维知识 | 合规要求高的项目 |
| Docker + 云服务 | 弹性伸缩（AWS ECS/GCP Cloud Run） | 配置复杂 | 大型生产应用 |
| 静态导出 | 最便宜（GitHub Pages/Cloudflare Pages） | 不支持动态功能 | 纯静态网站 |

> 💡 **新项目建议**：先用 Vercel 快速上线验证产品，等用户量增长或有特殊需求时再迁移到 Docker 自托管。不要在产品验证阶段花时间搞运维。

**第 12 章核心知识回顾：**

| 概念 | 要点 |
|:---|:---|
| Vercel 部署 | Git Push 即上线，Preview 环境，全球 CDN |
| 环境变量 | `NEXT_PUBLIC_` 前缀区分客户端/服务端变量 |
| Docker 部署 | `output: 'standalone'` + 多阶段 Dockerfile |
| CI/CD | GitHub Actions：lint → test → build → deploy |
| 方案选择 | 小项目用 Vercel，大项目用 Docker + 云服务 |

---

## 13. 实战项目：全栈博客系统

前 12 章学了一堆"零件"，现在该把它们组装成一辆"整车"了。

本章从零构建一个**全栈博客系统**，综合运用 Server Components、Server Actions、Prisma、Auth.js、Tailwind + shadcn/ui 等技术栈。

> 💡 **本章的目标**：不是写一个 Hello World 级别的博客，而是一个**接近生产级别**的项目——有用户系统、Markdown 渲染、评论功能、SEO 优化。

### 13.1 需求分析与技术架构设计

**功能清单：**

| 模块 | 功能 | 涉及章节 |
|:---|:---|:---|
| 首页 | 文章列表、搜索、分页 | Ch2 路由 + Ch4 数据获取 + Ch9 URL State |
| 文章详情 | Markdown 渲染、阅读量统计 | Ch3 Server Components + Ch10 性能优化 |
| 文章管理 | 创建/编辑/删除文章 | Ch4 Server Actions + Ch7 Prisma |
| 用户系统 | GitHub OAuth + 邮箱登录 | Ch8 Auth.js |
| 评论 | 发表/删除评论、乐观更新 | Ch9 useOptimistic |
| 样式 | 响应式设计、暗色模式 | Ch5 Tailwind + shadcn/ui |
| SEO | 动态 Metadata、sitemap | Ch10 性能优化 |
| 部署 | Vercel 一键上线 | Ch12 部署 |

**技术选型：**

```
框架：Next.js 15（App Router）
语言：TypeScript
样式：Tailwind CSS v4 + shadcn/ui
数据库：PostgreSQL + Prisma ORM
认证：Auth.js v5
Markdown：react-markdown + rehype-highlight
部署：Vercel
```

**项目目录结构：**

```
my-blog/
├── app/
│   ├── layout.tsx              # 根布局（字体、主题、导航）
│   ├── page.tsx                # 首页（文章列表）
│   ├── blog/
│   │   ├── page.tsx            # 博客列表（搜索 + 分页）
│   │   ├── [slug]/
│   │   │   └── page.tsx        # 文章详情
│   │   └── new/
│   │       └── page.tsx        # 新建文章（需登录）
│   ├── dashboard/
│   │   └── page.tsx            # 管理后台（我的文章）
│   ├── login/
│   │   └── page.tsx            # 登录页面
│   ├── api/
│   │   └── auth/[...nextauth]/
│   │       └── route.ts        # Auth.js API
│   └── actions/
│       ├── post.ts             # 文章相关 Server Actions
│       └── comment.ts          # 评论相关 Server Actions
├── components/
│   ├── ui/                     # shadcn/ui 组件
│   ├── Navbar.tsx              # 导航栏
│   ├── PostCard.tsx            # 文章卡片
│   ├── MarkdownRenderer.tsx    # Markdown 渲染器
│   ├── CommentSection.tsx      # 评论区
│   ├── SearchBar.tsx           # 搜索框
│   └── ThemeToggle.tsx         # 主题切换
├── lib/
│   ├── db.ts                   # Prisma Client 单例
│   └── utils.ts                # 工具函数
├── prisma/
│   └── schema.prisma           # 数据库模型
├── auth.ts                     # Auth.js 配置
└── middleware.ts               # 路由保护
```

### 13.2 数据库设计与 Prisma Schema

**完整的 Prisma Schema：**

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id             String    @id @default(cuid())
  name           String?
  email          String    @unique
  emailVerified  DateTime?
  image          String?
  hashedPassword String?
  role           String    @default("user")  // "user" | "admin"
  posts          Post[]
  comments       Comment[]
  accounts       Account[]  // OAuth 账号关联
  createdAt      DateTime  @default(now())
}

model Post {
  id        String    @id @default(cuid())
  slug      String    @unique
  title     String
  content   String    // Markdown 原文
  excerpt   String?   // 摘要（列表页显示）
  coverImage String?  // 封面图 URL
  published Boolean   @default(false)
  views     Int       @default(0)
  author    User      @relation(fields: [authorId], references: [id])
  authorId  String
  comments  Comment[]
  tags      Tag[]
  createdAt DateTime  @default(now())
  updatedAt DateTime  @updatedAt
}

model Comment {
  id        String   @id @default(cuid())
  content   String
  author    User     @relation(fields: [authorId], references: [id])
  authorId  String
  post      Post     @relation(fields: [postId], references: [id], onDelete: Cascade)
  postId    String
  createdAt DateTime @default(now())
}

model Tag {
  id    String @id @default(cuid())
  name  String @unique
  posts Post[]
}

// Auth.js 需要的 Account 模型（存储 OAuth 信息）
model Account {
  id                String  @id @default(cuid())
  userId            String
  type              String
  provider          String
  providerAccountId String
  refresh_token     String?
  access_token      String?
  expires_at        Int?
  token_type        String?
  scope             String?
  id_token          String?
  user              User    @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([provider, providerAccountId])
}
```

**种子数据（开发测试用）：**

```tsx
// prisma/seed.ts
import { PrismaClient } from '@prisma/client';
const db = new PrismaClient();

async function main() {
  // 创建测试用户
  const user = await db.user.create({
    data: {
      name: '测试作者',
      email: 'test@example.com',
      role: 'admin',
    },
  });

  // 创建几篇测试文章
  const posts = [
    { title: 'Next.js 入门指南', slug: 'nextjs-getting-started', content: '# Hello\n\n这是第一篇文章...' },
    { title: 'Prisma 数据库操作', slug: 'prisma-database', content: '# Prisma\n\n学习 Prisma ORM...' },
    { title: 'Tailwind CSS 实战', slug: 'tailwind-in-action', content: '# Tailwind\n\n工具类优先的 CSS...' },
  ];

  for (const post of posts) {
    await db.post.create({
      data: { ...post, published: true, authorId: user.id },
    });
  }

  console.log('✅ 种子数据创建完成');
}

main().catch(console.error).finally(() => db.$disconnect());
```

```bash
# 执行种子数据
npx tsx prisma/seed.ts
```

### 13.3 核心功能实现：文章 CRUD + Markdown 渲染

**文章列表页（搜索 + 分页）：**

```tsx
// app/blog/page.tsx
import { db } from '@/lib/db';
import PostCard from '@/components/PostCard';
import SearchBar from '@/components/SearchBar';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

const PAGE_SIZE = 6;

export default async function BlogPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; page?: string }>;
}) {
  const { q, page = '1' } = await searchParams;
  const currentPage = parseInt(page);

  const where = {
    published: true,
    ...(q ? { title: { contains: q, mode: 'insensitive' as const } } : {}),
  };

  const [posts, total] = await Promise.all([
    db.post.findMany({
      where,
      orderBy: { createdAt: 'desc' },
      skip: (currentPage - 1) * PAGE_SIZE,
      take: PAGE_SIZE,
      select: {
        id: true, slug: true, title: true, excerpt: true,
        coverImage: true, createdAt: true,
        author: { select: { name: true, image: true } },
        tags: { select: { name: true } },
      },
    }),
    db.post.count({ where }),
  ]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-8 text-3xl font-bold">博客</h1>
      <SearchBar defaultValue={q} />
      <div className="mt-8 grid gap-6 md:grid-cols-2">
        {posts.map(post => <PostCard key={post.id} post={post} />)}
      </div>
      {/* 分页 */}
      <div className="mt-8 flex gap-2 justify-center">
        {currentPage > 1 && <Link href={`?page=${currentPage - 1}`}><Button variant="outline">上一页</Button></Link>}
        <span className="py-2 px-4">第 {currentPage} / {totalPages} 页</span>
        {currentPage < totalPages && <Link href={`?page=${currentPage + 1}`}><Button variant="outline">下一页</Button></Link>}
      </div>
    </div>
  );
}
```

**文章详情页 + Markdown 渲染 + SEO Metadata：**

```bash
npm install react-markdown rehype-highlight remark-gfm
```

```tsx
// app/blog/[slug]/page.tsx
import { db } from '@/lib/db';
import { notFound } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import type { Metadata } from 'next';

// 动态生成 SEO Metadata
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const post = await db.post.findUnique({ where: { slug } });
  if (!post) return { title: '文章未找到' };
  return {
    title: post.title,
    description: post.excerpt || post.content.slice(0, 160),
  };
}

export default async function PostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await db.post.findUnique({
    where: { slug },
    include: { author: true, tags: true },
  });

  if (!post) notFound();

  // 阅读量 +1（不阻塞页面渲染）
  db.post.update({ where: { slug }, data: { views: { increment: 1 } } });

  return (
    <article className="prose prose-lg mx-auto max-w-3xl px-4 py-8 dark:prose-invert">
      <h1>{post.title}</h1>
      <p className="text-gray-500">
        {post.author.name} · {post.createdAt.toLocaleDateString('zh-CN')} · {post.views} 次阅读
      </p>
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
        {post.content}
      </ReactMarkdown>
    </article>
  );
}
```

**创建文章——Server Action：**

```tsx
// app/actions/post.ts
'use server';

import { db } from '@/lib/db';
import { auth } from '@/auth';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { z } from 'zod';

const postSchema = z.object({
  title: z.string().min(1, '标题不能为空'),
  content: z.string().min(10, '内容至少 10 个字'),
  excerpt: z.string().optional(),
});

export async function createPost(formData: FormData) {
  const session = await auth();
  if (!session) throw new Error('请先登录');

  const validated = postSchema.safeParse({
    title: formData.get('title'),
    content: formData.get('content'),
    excerpt: formData.get('excerpt'),
  });
  if (!validated.success) throw new Error(validated.error.errors[0].message);

  const slug = validated.data.title
    .toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-').replace(/^-|-$/g, '');

  await db.post.create({
    data: {
      ...validated.data,
      slug: `${slug}-${Date.now().toString(36)}`,
      published: true,
      authorId: session.user.id,
    },
  });

  revalidatePath('/blog');
  redirect('/blog');
}
```

### 13.4 用户系统：注册登录 + 评论功能

用户系统直接复用第 8 章 Auth.js 的配置。这里重点展示**评论功能**——综合了 Server Actions + 乐观更新。

**评论 Server Action：**

```tsx
// app/actions/comment.ts
'use server';

import { db } from '@/lib/db';
import { auth } from '@/auth';
import { revalidatePath } from 'next/cache';

export async function addComment(postSlug: string, content: string) {
  const session = await auth();
  if (!session) throw new Error('请先登录');
  if (!content.trim()) throw new Error('评论不能为空');

  await db.comment.create({
    data: {
      content: content.trim(),
      authorId: session.user.id,
      post: { connect: { slug: postSlug } },
    },
  });

  revalidatePath(`/blog/${postSlug}`);
}

export async function deleteComment(commentId: string) {
  const session = await auth();
  if (!session) throw new Error('请先登录');

  const comment = await db.comment.findUnique({ where: { id: commentId } });
  if (!comment || comment.authorId !== session.user.id) {
    throw new Error('无权删除');
  }

  await db.comment.delete({ where: { id: commentId } });
}
```

**评论区组件（乐观更新）：**

```tsx
// components/CommentSection.tsx
'use client';

import { useOptimistic, useState } from 'react';
import { addComment } from '@/app/actions/comment';
import { Button } from '@/components/ui/button';

type Comment = {
  id: string;
  content: string;
  createdAt: Date;
  author: { name: string; image: string | null };
};

export default function CommentSection({
  postSlug,
  initialComments,
  currentUser,
}: {
  postSlug: string;
  initialComments: Comment[];
  currentUser: { name: string; image: string | null } | null;
}) {
  const [input, setInput] = useState('');
  const [optimisticComments, addOptimistic] = useOptimistic(
    initialComments,
    (state: Comment[], newComment: Comment) => [...state, newComment]
  );

  async function handleSubmit(formData: FormData) {
    const content = formData.get('content') as string;
    if (!content.trim()) return;

    // 乐观更新——立即显示
    addOptimistic({
      id: `temp-${Date.now()}`,
      content,
      createdAt: new Date(),
      author: { name: currentUser?.name || '我', image: currentUser?.image || null },
    });

    setInput('');
    await addComment(postSlug, content);
  }

  return (
    <div className="mt-12">
      <h2 className="text-xl font-bold mb-4">评论（{optimisticComments.length}）</h2>

      {currentUser ? (
        <form action={handleSubmit} className="mb-6">
          <textarea
            name="content"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="写下你的想法..."
            className="w-full rounded-lg border p-3"
            rows={3}
          />
          <Button type="submit" className="mt-2">发表评论</Button>
        </form>
      ) : (
        <p className="mb-6 text-gray-500">请先登录后发表评论</p>
      )}

      <div className="space-y-4">
        {optimisticComments.map(comment => (
          <div key={comment.id} className="rounded-lg border p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-medium">{comment.author.name}</span>
              <span className="text-sm text-gray-400">
                {new Date(comment.createdAt).toLocaleDateString('zh-CN')}
              </span>
            </div>
            <p>{comment.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 13.5 部署上线与域名配置

**上线前的 Checklist：**

```
☑ 所有环境变量已配置（DATABASE_URL、AUTH_SECRET、OAuth Key）
☑ 数据库已迁移（npx prisma migrate deploy）
☑ npm run build 本地构建通过
☑ npm run lint 无错误
☑ 关键页面手动测试通过
☑ .env.local 不在 Git 仓库中
☑ Metadata（title、description）已设置
☑ OG Image 已配置
```

**Vercel 上线步骤：**

```bash
# 1. 推到 GitHub
git add . && git commit -m "ready for production" && git push

# 2. 在 Vercel 导入项目
#    vercel.com → Import → 选择仓库

# 3. 配置环境变量
#    Settings → Environment Variables:
#    DATABASE_URL = postgresql://...（生产数据库）
#    AUTH_SECRET = ...
#    GITHUB_ID = ...
#    GITHUB_SECRET = ...

# 4. 配置数据库
#    推荐 Vercel Postgres 或 Supabase（免费额度）
#    或自建 PostgreSQL（Railway / Neon）

# 5. 点击 Deploy → 等待构建完成

# 6. 配置域名（可选）
#    Settings → Domains → 添加 yourdomain.com
#    → 在域名注册商配置 DNS：CNAME → cname.vercel-dns.com
```

**常用的免费 PostgreSQL 托管服务：**

| 服务 | 免费额度 | 特点 |
|:---|:---|:---|
| Vercel Postgres | 256MB 存储 | 与 Vercel 深度集成 |
| Supabase | 500MB 存储 | 自带认证/存储/实时功能 |
| Neon | 512MB 存储 | Serverless PostgreSQL，冷启动快 |
| Railway | $5 免费额度/月 | 部署简单，支持多种数据库 |

> 💡 **恭喜！** 🎉 如果你从第 1 章跟到了这里，你已经完成了一个包含用户系统、文章管理、评论互动、Markdown 渲染、SEO 优化的全栈博客。这不是一个玩具项目——它可以作为你个人博客的起点。

**第 13 章核心知识回顾：**

| 知识点 | 在项目中的应用 |
|:---|:---|
| App Router | 文件路由、动态路由 `[slug]`、布局嵌套 |
| Server Components | 文章列表和详情页直接查库渲染 |
| Server Actions | 创建文章、发表/删除评论 |
| Prisma | User/Post/Comment 三表关联查询 |
| Auth.js | GitHub OAuth 登录、权限检查 |
| URL State | searchParams 搜索 + 分页 |
| `useOptimistic` | 评论的乐观更新 |
| Tailwind + shadcn/ui | 响应式布局、暗色模式、UI 组件 |
| SEO | `generateMetadata` 动态标题描述 |
| Vercel | Git Push 部署、环境变量、域名 |

---

## 14. Next.js 生态与进阶方向

前 13 章覆盖了 Next.js 全栈开发的核心知识。但 Web 开发的世界还有很多有趣的方向等你探索。本章介绍几个高价值的进阶主题，帮你规划下一步学习路线。

### 14.1 国际化（i18n）：多语言支持方案

当你的应用需要支持中文、英文、日文等多种语言时，需要国际化（i18n）方案。

**Next.js App Router 的 i18n 路由策略：**

```
方案 1：子路径路由（推荐）
  /en/blog → 英文版
  /zh/blog → 中文版
  /ja/blog → 日文版

方案 2：域名路由
  en.example.com → 英文版
  zh.example.com → 中文版
```

**推荐库——`next-intl`：**

```bash
npm install next-intl
```

```
app/
├── [locale]/          ← 动态路由段，作为语言标识
│   ├── layout.tsx
│   ├── page.tsx
│   └── blog/
│       └── page.tsx
├── messages/
│   ├── en.json        ← 英文翻译文件
│   └── zh.json        ← 中文翻译文件
```

```json
// messages/zh.json
{
  "home": {
    "title": "欢迎来到我的博客",
    "description": "这里分享技术文章和心得"
  },
  "nav": {
    "blog": "博客",
    "about": "关于"
  }
}
```

```json
// messages/en.json
{
  "home": {
    "title": "Welcome to My Blog",
    "description": "Sharing tech articles and insights"
  },
  "nav": {
    "blog": "Blog",
    "about": "About"
  }
}
```

```tsx
// app/[locale]/page.tsx
import { useTranslations } from 'next-intl';

export default function HomePage() {
  const t = useTranslations('home');

  return (
    <div>
      <h1>{t('title')}</h1>
      <p>{t('description')}</p>
    </div>
  );
}
// 访问 /zh → 显示中文
// 访问 /en → 显示英文
```

**中间件——自动语言检测与重定向：**

```tsx
// middleware.ts
import createMiddleware from 'next-intl/middleware';

export default createMiddleware({
  locales: ['en', 'zh', 'ja'],
  defaultLocale: 'zh',
});

export const config = {
  matcher: ['/((?!api|_next|.*\\..*).*)'],
};
```

> 💡 **i18n 的核心挑战不是技术，而是翻译管理**。小项目用 JSON 文件就够了。大项目考虑 Crowdin、Lokalise 等翻译管理平台，支持团队协作和机器翻译。

### 14.2 实时功能：WebSocket + Server-Sent Events

聊天、通知、实时协作——这些功能需要服务器主动推送数据给客户端。

**方案对比：**

| 技术 | 方向 | 适用场景 | Next.js 支持 |
|:---|:---|:---|:---|
| SSE（Server-Sent Events） | 单向（服务器→客户端） | 通知推送、实时数据流 | Route Handlers 直接支持 |
| WebSocket | 双向 | 聊天、协作编辑 | 需要独立服务器（Socket.io） |

**SSE 示例——用 Route Handler 推送实时通知：**

```tsx
// app/api/notifications/route.ts
export async function GET() {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      // 每 3 秒推送一条消息
      const interval = setInterval(() => {
        const data = JSON.stringify({
          id: Date.now(),
          message: '你有新的评论',
          time: new Date().toISOString(),
        });
        controller.enqueue(encoder.encode(`data: ${data}\n\n`));
      }, 3000);

      // 客户端断开时清理
      setTimeout(() => {
        clearInterval(interval);
        controller.close();
      }, 60000);  // 最多推送 1 分钟
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
```

```tsx
// 客户端接收 SSE
'use client';
import { useEffect, useState } from 'react';

export default function Notifications() {
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    const source = new EventSource('/api/notifications');
    source.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, data.message]);
    };
    return () => source.close();
  }, []);

  return (
    <div>
      {messages.map((msg, i) => <p key={i}>{msg}</p>)}
    </div>
  );
}
```

**WebSocket——需要独立服务：**

Next.js 的 Serverless 架构不原生支持 WebSocket 长连接。需要：
- 方案 A：独立的 WebSocket 服务器（Node.js + Socket.io），Next.js 客户端连接
- 方案 B：用第三方服务（Pusher、Ably、Supabase Realtime）
- 方案 C：自定义 Next.js 服务器（`server.ts`），但会失去 Vercel Serverless 部署能力

> 💡 **选择建议**：通知、数据更新推送用 SSE（简单、Next.js 原生支持）。聊天、协作编辑用 Pusher/Ably 等第三方 WebSocket 服务（省心、可靠）。

### 14.3 AI 集成：Vercel AI SDK + LLM Streaming

AI 功能已经成为现代 Web 应用的标配。Vercel AI SDK 让 Next.js 接入大语言模型变得异常简单。

```bash
npm install ai @ai-sdk/openai
```

**流式聊天 API：**

```tsx
// app/api/chat/route.ts
import { openai } from '@ai-sdk/openai';
import { streamText } from 'ai';

export async function POST(request: Request) {
  const { messages } = await request.json();

  const result = streamText({
    model: openai('gpt-4o-mini'),
    system: '你是一个友好的中文 AI 助手。',
    messages,
  });

  return result.toDataStreamResponse();
}
```

**聊天界面——一个 Hook 搞定：**

```tsx
// app/chat/page.tsx
'use client';

import { useChat } from 'ai/react';

export default function ChatPage() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat();

  return (
    <div className="mx-auto max-w-2xl p-4">
      <h1 className="mb-4 text-2xl font-bold">AI 聊天</h1>

      <div className="space-y-4 mb-4">
        {messages.map(m => (
          <div key={m.id} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            <span className="inline-block rounded-lg px-4 py-2 bg-gray-100 dark:bg-gray-800">
              {m.content}
            </span>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="输入消息..."
          className="flex-1 rounded-lg border px-4 py-2"
        />
        <button type="submit" disabled={isLoading} className="rounded-lg bg-blue-600 px-4 py-2 text-white">
          {isLoading ? '思考中...' : '发送'}
        </button>
      </form>
    </div>
  );
}
```

**`useChat` 自动做了什么：**

- ✅ 管理消息列表（用户消息 + AI 回复）
- ✅ 自动发 POST 请求到 `/api/chat`
- ✅ 流式接收 AI 回复（打字机效果）
- ✅ `isLoading` 状态管理
- ✅ 错误处理

> 💡 **Vercel AI SDK 支持多种模型**：OpenAI、Anthropic（Claude）、Google（Gemini）、Mistral、本地模型（Ollama）。换模型只需改一行 `model: xxx` 的代码。

### 14.4 从 Next.js 到全栈工程师：学习路线图

学完 14 章，你已经掌握了 Next.js 全栈开发的核心技能。但全栈工程师的路不止于此。

**阶段一：巩固基础（你已经在这里 ✅）**

```
Next.js 15（App Router）     ✅ 本教程
TypeScript                   ✅ 本教程中使用
Tailwind CSS + shadcn/ui     ✅ 本教程 
Prisma + PostgreSQL          ✅ 本教程
Auth.js                      ✅ 本教程
```

**阶段二：深化前端**

| 方向 | 学什么 | 推荐资源 |
|:---|:---|:---|
| React 深度 | React 19 新特性、Server Components 原理 | React 官方文档 |
| 动画 | Framer Motion、CSS 动画 | Framer Motion 官网 |
| 状态管理 | Zustand（简单场景）、Jotai（原子化） | 各自官方文档 |
| 移动端 | React Native / Expo | Expo 官方教程 |

**阶段三：拓展后端**

| 方向 | 学什么 | 何时需要 |
|:---|:---|:---|
| API 设计 | RESTful 规范、tRPC | 对外提供 API 时 |
| 消息队列 | Redis、BullMQ | 异步任务（发邮件、生成报告） |
| 文件存储 | S3、Cloudflare R2 | 用户上传图片/文件 |
| 搜索 | Elasticsearch、Meilisearch | 全文搜索需求 |
| 支付 | Stripe、LemonSqueezy | SaaS 收费功能 |

**阶段四：工程化与运维**

| 方向 | 学什么 | 收益 |
|:---|:---|:---|
| Docker | 容器化部署 | 环境一致性、可移植 |
| CI/CD | GitHub Actions | 自动化测试和部署 |
| 监控 | Sentry、Vercel Analytics | 生产环境错误追踪 |
| 日志 | Pino、Axiom | 线上问题排查 |
| Edge Computing | Cloudflare Workers | 全球低延迟 |

**阶段五：专业方向**

```
SaaS 开发     → 多租户架构、订阅计费、权限系统
AI 应用       → Vercel AI SDK、RAG、向量数据库
电商          → 库存管理、支付集成、订单系统
内容平台      → CMS（Sanity/Contentful）、富文本编辑器
实时协作      → CRDT、Y.js、WebSocket
```

**推荐的学习资源：**

| 资源 | 类型 | 链接 |
|:---|:---|:---|
| Next.js 官方文档 | 文档 | nextjs.org/docs |
| Next.js Learn | 交互教程 | nextjs.org/learn |
| Vercel Blog | 技术博客 | vercel.com/blog |
| Theo - t3.gg | YouTube | 前沿技术趋势 |
| Josh W Comeau | 博客/课程 | 深度 CSS/React 教学 |

---

## 结语

恭喜你完成了这份教程！🎉

从第 1 章的 `npx create-next-app` 到第 13 章的全栈博客上线，你已经走过了一条完整的 Next.js 全栈开发之路：

- **理解了 App Router 的核心哲学**：Server-first、文件即路由、布局嵌套
- **掌握了数据获取的全套范式**：Server Components 直接查库、Server Actions 数据变更、SWR 客户端获取
- **学会了生产级实践**：Prisma 数据库操作、Auth.js 认证授权、Zod 输入验证、三层权限防御
- **建立了工程化意识**：TypeScript 类型安全、Jest 测试、CI/CD 自动化、Docker 部署

**最重要的下一步**：不是再学一个新框架，而是用 Next.js **做一个真实的项目**。

一个有真实用户的项目，教会你的东西比任何教程都多。

祝你编码愉快！🚀
