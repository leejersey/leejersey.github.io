# Monorepo 实战（Turborepo + pnpm）

> 一个仓库管所有项目，听起来疯狂？Turborepo + pnpm 让 Monorepo 从"大厂专属"变成"人人可用"——本教程从零搭建一个生产级 Monorepo，覆盖 Workspace 管理、任务编排、缓存策略、共享配置、包版本管理到 CI/CD 全流程。

---

## 1. 为什么选 Monorepo：从痛点到方案

你的团队有一个前端项目、一个后端项目、三个共享库——分散在 5 个 Git 仓库里。某天你改了共享库的一个接口，接下来的两小时用来挨个仓库改代码、发版本、升依赖。这就是 Polyrepo 的日常。

### 1.1 Polyrepo 的三大痛点

```
典型 Polyrepo 架构（5 个项目 = 5 个 Git 仓库）：

  repo-1: web-app          ← 前端应用
  repo-2: admin-panel      ← 管理后台
  repo-3: api-server       ← 后端服务
  repo-4: shared-utils     ← 共享工具库（npm 发布）
  repo-5: ui-components    ← 共享组件库（npm 发布）

  依赖关系：
  web-app ──────► shared-utils@1.2.0
  web-app ──────► ui-components@2.0.0
  admin-panel ──► shared-utils@1.1.0   ← 版本不一致！
  admin-panel ──► ui-components@2.0.0
  api-server ───► shared-utils@1.0.0   ← 更旧的版本！
```

**痛点一：依赖版本地狱**

```
shared-utils 发布了 v1.3.0，修复了一个关键 Bug：

  Step 1: 在 repo-4 改代码 → 跑测试 → 发 npm 包
  Step 2: 去 repo-1 → pnpm update shared-utils → 跑测试 → 部署
  Step 3: 去 repo-2 → pnpm update shared-utils → 跑测试 → 部署
  Step 4: 去 repo-3 → pnpm update shared-utils → 跑测试 → 部署

  问题：
  ❌ 3 个消费者可能各自停留在不同版本
  ❌ 忘记升级某个仓库 → 线上 Bug
  ❌ 版本不一致 → "在我机器上能跑"
```

**痛点二：重复配置**

```
每个仓库都有一套几乎相同的配置：

  repo-1/                  repo-2/                  repo-3/
  ├── tsconfig.json        ├── tsconfig.json        ├── tsconfig.json
  ├── eslint.config.js     ├── eslint.config.js     ├── eslint.config.js
  ├── prettier.config.js   ├── prettier.config.js   ├── prettier.config.js
  ├── .github/workflows/   ├── .github/workflows/   ├── .github/workflows/
  └── vitest.config.ts     └── vitest.config.ts     └── vitest.config.ts

  5 个仓库 × 5 个配置文件 = 25 个需要保持同步的文件
  → 改一个 ESLint 规则？改 5 次。漏了一个？代码风格不一致。
```

**痛点三：跨仓联调噩梦**

```
开发一个需要同时改 shared-utils 和 web-app 的功能：

  传统做法（npm link）：
  1. cd repo-4 && pnpm link --global        # 创建全局链接
  2. cd repo-1 && pnpm link shared-utils     # 消费链接
  3. 改 shared-utils 代码 → 手动重新构建
  4. 切回 web-app → 刷新 → 看效果
  5. 反复循环...
  6. 联调完成 → 先发 shared-utils → 再改 web-app 的依赖 → 提 PR

  问题：
  ❌ npm link 经常出现幽灵依赖（phantom dependencies）
  ❌ 两个仓库的改动无法在同一个 PR 里 Code Review
  ❌ 无法保证 shared-utils 和 web-app 的改动一起上线
```

> 💡 **核心问题**：Polyrepo 把"代码隔离"做到了极致，却牺牲了"协作效率"。当项目之间有频繁依赖关系时，仓库边界反而成了绊脚石。

### 1.2 Monorepo 的优势与常见误区

```
Monorepo 架构（5 个项目 = 1 个 Git 仓库）：

  my-monorepo/
  ├── apps/
  │   ├── web-app/          ← 前端应用
  │   ├── admin-panel/      ← 管理后台
  │   └── api-server/       ← 后端服务
  ├── packages/
  │   ├── shared-utils/     ← 共享工具库
  │   └── ui-components/    ← 共享组件库
  ├── package.json
  ├── pnpm-workspace.yaml
  └── turbo.json

  依赖关系：
  web-app ──────► shared-utils（源码直接引用，永远最新）
  web-app ──────► ui-components（同上）
  admin-panel ──► shared-utils（同上）
  api-server ───► shared-utils（同上）
  → 没有版本号，没有发布，永远一致 ✅
```

**优势一：原子提交（Atomic Commits）**

```
改 shared-utils 接口 + 改所有消费者 → 一个 PR 搞定：

  PR #42: "重构 formatDate 接口"
  ├── packages/shared-utils/src/date.ts    ← 改接口
  ├── apps/web-app/src/utils.ts            ← 改调用
  ├── apps/admin-panel/src/utils.ts        ← 改调用
  └── apps/api-server/src/helpers.ts       ← 改调用

  好处：
  ✅ Code Review 一次看完所有改动
  ✅ CI 一次验证所有项目是否兼容
  ✅ 要么全部上线，要么全部回滚
```

**优势二：共享一切**

```
配置只写一份，所有项目共享：

  my-monorepo/
  ├── tooling/
  │   ├── typescript-config/   ← 一份 tsconfig 基础配置
  │   ├── eslint-config/       ← 一份 ESLint 规则
  │   └── prettier-config/     ← 一份格式化规则
  ├── .github/workflows/       ← 一套 CI/CD
  └── turbo.json               ← 一套构建编排

  改 ESLint 规则？改 1 个文件 → 所有项目自动生效
```

**优势三：跨项目开发零摩擦**

```
在 Monorepo 中同时改 shared-utils 和 web-app：

  1. 改 packages/shared-utils/src/date.ts
  2. web-app 自动引用最新源码（workspace: 协议）
  3. HMR 热更新 → 浏览器立即看到效果
  4. 跑 turbo run test → 自动测试所有受影响的包
  5. 提交 → 一个 PR → 一次 Review → 一次部署

  无需 npm link、无需发版、无需手动同步
```

**常见误区澄清**

| 误区 | 事实 |
|:---|:---|
| "Monorepo = 一个巨大的项目" | 错。每个包仍然独立，有自己的 package.json、tsconfig、测试 |
| "Git 仓库会变得很慢" | 现代 Git（sparse checkout + shallow clone）可以处理超大仓库 |
| "所有人都能改所有代码" | 可以用 CODEOWNERS + 目录级权限控制 |
| "CI 每次都要全量构建" | Turborepo 的增量构建 + 缓存解决这个问题 |
| "Monorepo = Monolith" | Monorepo 是代码组织方式，Monolith 是架构模式，完全无关 |

### 1.3 工具选型：Turborepo vs Nx vs Lerna vs Bazel

```
Monorepo 工具的核心能力：

  1. 任务编排  → 按依赖关系决定构建顺序
  2. 增量构建  → 只重新构建受影响的包
  3. 缓存      → 跳过未改变的任务
  4. 依赖管理  → 统一管理 node_modules
```

| 维度 | **Turborepo** | **Nx** | **Lerna** | **Bazel** |
|:---|:---|:---|:---|:---|
| **定位** | 轻量任务编排 | 全功能 Monorepo 平台 | 版本发布工具 | 通用构建系统 |
| **学习成本** | ⭐ 极低 | ⭐⭐⭐ 较高 | ⭐⭐ 低 | ⭐⭐⭐⭐⭐ 极高 |
| **配置量** | 1 个 turbo.json | 多个配置文件 + 插件 | lerna.json | BUILD 文件（每个包） |
| **缓存** | ✅ 本地 + Remote | ✅ 本地 + Nx Cloud | ⚠️ 依赖 Nx/Turborepo | ✅ 本地 + Remote |
| **任务编排** | ✅ 拓扑排序 + 并行 | ✅ 拓扑排序 + 并行 | ⚠️ 基础 | ✅ 强大 |
| **代码生成** | ❌ 无 | ✅ Generator | ❌ 无 | ❌ 无 |
| **多语言** | ❌ JS/TS 专用 | ⚠️ 主打 JS/TS | ❌ JS/TS 专用 | ✅ 任何语言 |
| **适用规模** | 1-50 包 | 10-200+ 包 | 1-20 包 | 100+ 包（大厂） |
| **维护方** | Vercel | Nrwl | Nx 团队接管 | Google |

```
选型决策树：

  你的项目是纯 JS/TS 吗？
  ├── 否 → Bazel（多语言 Monorepo）
  └── 是 → 包的数量？
      ├── < 50 个包 → Turborepo（简单直接）
      ├── 50-200 个包 → Nx（需要 Generator、Graph 可视化等高级功能）
      └── 需要发布 npm 包？→ 加上 Changesets（任何工具都能搭配）

  Lerna 的定位：
  → 2024 年后已被 Nx 团队接管，底层用 Nx 引擎
  → 新项目不建议单独使用，选 Turborepo 或 Nx
```

### 1.4 为什么是 Turborepo + pnpm

```
Turborepo + pnpm 的分工：

  ┌─────────────────────────────────────────┐
  │              Turborepo                  │
  │  ┌─────────┬──────────┬──────────────┐  │
  │  │ 任务编排 │ 增量构建  │ 缓存（本地/远程）│  │
  │  └─────────┴──────────┴──────────────┘  │
  │  → 负责：怎么构建、按什么顺序、能不能跳过      │
  ├─────────────────────────────────────────┤
  │              pnpm                       │
  │  ┌─────────┬──────────┬──────────────┐  │
  │  │ 包管理   │ Workspace│ 依赖安装      │  │
  │  └─────────┴──────────┴──────────────┘  │
  │  → 负责：装什么依赖、包之间怎么链接、磁盘优化  │
  └─────────────────────────────────────────┘

  各司其职，组合起来 = 完整的 Monorepo 解决方案
```

**为什么是 pnpm 而不是 npm/yarn？**

| 维度 | **npm** | **yarn** | **pnpm** |
|:---|:---|:---|:---|
| **磁盘占用** | 重复安装 | 重复安装 | 内容寻址存储（全局共享） |
| **安装速度** | 慢 | 中等 | ⭐ 最快 |
| **幽灵依赖** | ❌ 有（扁平化） | ❌ 有（扁平化） | ✅ 无（严格模式） |
| **Workspace** | ⚠️ 基础 | ✅ 支持 | ✅ 最完善（catalog: 协议） |
| **Monorepo 生态** | ⚠️ 弱 | ⚠️ 一般 | ⭐ 最佳搭配 |

```
pnpm 的杀手级特性——内容寻址存储：

  npm/yarn：每个项目独立装依赖
    project-a/node_modules/lodash/  → 4.2 MB
    project-b/node_modules/lodash/  → 4.2 MB（重复！）
    project-c/node_modules/lodash/  → 4.2 MB（又重复！）
    → 总计 12.6 MB

  pnpm：全局 store + 硬链接
    ~/.pnpm-store/lodash@4.17.21/   → 4.2 MB（只存一份）
    project-a/node_modules/lodash/  → 硬链接 → 0 MB
    project-b/node_modules/lodash/  → 硬链接 → 0 MB
    project-c/node_modules/lodash/  → 硬链接 → 0 MB
    → 总计 4.2 MB（节省 67%）

  Monorepo 有 10 个包？节省更多！
```

**为什么是 Turborepo 而不是 Nx？**

```
Turborepo 的核心哲学：约定大于配置

  上手成本：
  Turborepo → 加一个 turbo.json，写 10 行配置，开跑
  Nx       → 装 @nx/core，选插件，配 project.json，学 Generator...

  配置对比：
  Turborepo 的 turbo.json（完整配置）：
  {
    "tasks": {
      "build": { "dependsOn": ["^build"], "outputs": ["dist/**"] },
      "test":  { "dependsOn": ["build"] },
      "lint":  {}
    }
  }
  → 7 行搞定所有任务编排

  Nx 等价配置：
  nx.json + 每个包的 project.json + @nx/webpack 插件 + targets 定义
  → 分散在多个文件中
```

> 💡 **总结**：Turborepo 专注做"任务编排 + 缓存"这一件事，pnpm 专注做"依赖管理 + Workspace"这一件事。两者组合覆盖了 Monorepo 的所有核心需求，且学习成本最低——如果你的团队不超过 50 个包，这就是 2026 年的最优解。

---

## 2. 环境准备与项目初始化

工欲善其事，必先利其器。这一章从安装 pnpm 开始，用官方脚手架一键创建 Turborepo 项目，然后理解目录结构背后的设计哲学。

### 2.1 安装 pnpm 与 Corepack 版本锁定

```bash
# 方式一：用 Corepack 管理 pnpm 版本（推荐）
# Corepack 是 Node.js 内置的包管理器版本管理工具（Node 16.13+）
corepack enable                    # 启用 Corepack
corepack prepare pnpm@latest --activate  # 安装最新 pnpm

# 方式二：独立安装
npm install -g pnpm

# 验证安装
pnpm --version   # 9.x 或 10.x
node --version   # 建议 Node 20+
```

```
为什么要用 Corepack？

  问题场景：
  开发者 A 用 pnpm 9.1.0
  开发者 B 用 pnpm 10.2.0
  CI 环境用 pnpm 9.5.0
  → 三个环境的 pnpm-lock.yaml 格式可能不兼容 → 幽灵 Bug

  Corepack 的解法——在 package.json 中声明版本：
  {
    "packageManager": "pnpm@10.8.1"
  }

  → 任何人 clone 项目后，Corepack 自动下载对应版本的 pnpm
  → 保证全团队 + CI 环境使用完全相同的 pnpm 版本
  → 类似 Python 的 pyenv 或 Rust 的 rustup
```

> 💡 **重要**：`packageManager` 字段是 Node.js 官方标准（在 `package.json` 的顶层），不是 pnpm 私有扩展。npm 和 yarn 也支持。

### 2.2 用 create-turbo 创建项目

```bash
# 一键创建 Turborepo 项目
pnpm dlx create-turbo@latest my-monorepo

# 交互式选项：
# ? Which package manager do you want to use? → pnpm（选 pnpm）
# ? Where would you like to create your turborepo? → my-monorepo

# 创建完成后
cd my-monorepo
pnpm install      # 安装所有依赖
pnpm dev           # 启动所有应用的开发服务器
```

```
create-turbo 生成的项目结构（2026 最新模板）：

  my-monorepo/
  ├── apps/
  │   ├── web/                  ← Next.js 前端应用
  │   │   ├── package.json
  │   │   ├── tsconfig.json
  │   │   └── src/
  │   └── docs/                 ← 文档站点
  │       ├── package.json
  │       └── src/
  ├── packages/
  │   ├── ui/                   ← 共享 UI 组件库
  │   │   ├── package.json
  │   │   └── src/
  │   ├── eslint-config/        ← 共享 ESLint 配置
  │   │   └── package.json
  │   └── typescript-config/    ← 共享 TypeScript 配置
  │       ├── base.json
  │       ├── nextjs.json
  │       └── package.json
  ├── package.json              ← 根配置
  ├── pnpm-workspace.yaml       ← Workspace 定义
  ├── turbo.json                ← Turborepo 任务配置
  └── pnpm-lock.yaml            ← 锁文件（整个 Monorepo 共享一个）
```

```bash
# 如果不想用脚手架，也可以手动初始化
mkdir my-monorepo && cd my-monorepo
pnpm init                      # 创建根 package.json
mkdir -p apps packages tooling  # 创建标准目录

# 创建 pnpm-workspace.yaml
cat > pnpm-workspace.yaml << 'EOF'
packages:
  - "apps/*"
  - "packages/*"
  - "tooling/*"
EOF

# 安装 Turborepo
pnpm add -D turbo -w            # -w 表示安装到 workspace 根目录

# 创建 turbo.json
cat > turbo.json << 'EOF'
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {},
    "test": {}
  }
}
EOF
```

### 2.3 目录结构规范：apps / packages / tooling

```
生产级 Monorepo 目录结构（推荐）：

  my-monorepo/
  │
  ├── apps/                     ← 可部署的应用（"薄"应用）
  │   ├── web/                  ← 前端应用（Next.js / Vite）
  │   ├── admin/                ← 管理后台
  │   ├── api/                  ← 后端服务（NestJS / Hono）
  │   └── mobile/               ← 移动端（React Native）
  │
  ├── packages/                 ← 共享的业务包
  │   ├── ui/                   ← UI 组件库
  │   ├── utils/                ← 工具函数
  │   ├── database/             ← 数据库层（Prisma/Drizzle）
  │   ├── api-client/           ← API 客户端（类型安全的 HTTP 封装）
  │   └── validators/           ← 校验规则（Zod Schema，前后端共享）
  │
  ├── tooling/                  ← 共享的开发工具配置
  │   ├── typescript-config/    ← tsconfig 基础配置
  │   ├── eslint-config/        ← ESLint 规则
  │   └── prettier-config/      ← Prettier 规则
  │
  ├── package.json              ← 根配置（private: true）
  ├── pnpm-workspace.yaml       ← Workspace 包发现
  ├── turbo.json                ← 任务编排
  ├── pnpm-lock.yaml            ← 全局锁文件
  └── .gitignore
```

```
三层目录的设计哲学：

  apps/     → "薄"应用：只做路由、组合、环境变量
             → 业务逻辑应该放在 packages/ 里
             → 每个 app 是独立可部署的单元

  packages/ → "厚"共享包：真正的业务逻辑在这里
             → 按领域拆分（ui、database、validators）
             → ❌ 不要搞一个万能 @repo/utils
             → ✅ 按职责拆成多个小包

  tooling/  → 纯配置包：不含业务代码
             → 只导出配置对象/文件
             → 所有 apps 和 packages 引用这里的配置

  为什么不把 tooling 放在 packages 里？
  → 职责不同：packages 是业务代码，tooling 是开发工具
  → 分开后在 pnpm-workspace.yaml 中可以独立管理
  → 一目了然：看目录名就知道是配置还是业务
```

| 目录 | 放什么 | 不放什么 |
|:---|:---|:---|
| **apps/** | 可部署的应用 | 共享逻辑、工具函数 |
| **packages/** | 共享业务逻辑、UI 组件 | 应用级路由、环境变量 |
| **tooling/** | ESLint/TS/Prettier 配置 | 业务代码、应用代码 |

### 2.4 根 package.json 配置详解

```jsonc
// 根 package.json —— Monorepo 的"入口配置"
{
  // ① 必须设为 private，防止根目录被意外发布到 npm
  "private": true,

  // ② 声明包管理器版本（Corepack 会读取这个字段）
  "packageManager": "pnpm@10.8.1",

  // ③ 根目录的 scripts 只做"转发"，不写具体逻辑
  "scripts": {
    "build": "turbo run build",
    "dev": "turbo run dev",
    "lint": "turbo run lint",
    "test": "turbo run test",
    "format": "prettier --write \"**/*.{ts,tsx,js,jsx,json,md}\"",
    "clean": "turbo run clean && rm -rf node_modules"
  },

  // ④ 根目录的 devDependencies —— 全局工具
  "devDependencies": {
    "turbo": "^2.5.0",        // Turborepo CLI
    "prettier": "^3.5.0"      // 格式化（根目录统一运行）
  }
}
```

```
根 package.json 的关键原则：

  1. private: true
     → 防止 pnpm publish 意外发布整个 Monorepo
     → 这是 pnpm workspace 的强制要求

  2. packageManager 字段
     → 锁定 pnpm 版本，保证一致性
     → CI 中 Corepack 会自动使用这个版本

  3. scripts 只转发给 turbo
     → ❌ "build": "cd apps/web && next build"   ← 不要直接调用
     → ✅ "build": "turbo run build"             ← 让 Turborepo 编排
     → 这样 Turborepo 才能做缓存和并行优化

  4. devDependencies 只放全局工具
     → turbo、prettier 等全局工具放根目录
     → 业务依赖（react、next）放各自的包里
     → ❌ 不要在根目录装 react —— 这不是 app
```

> 💡 **注意 `-w` 参数**：在 Monorepo 根目录安装依赖时，pnpm 要求加 `-w`（`--workspace-root`）参数：`pnpm add -D turbo -w`。这是 pnpm 的安全机制，防止你误操作把依赖装到根目录。

---

## 3. pnpm Workspace 深度使用

pnpm Workspace 是 Monorepo 的依赖管理基石——它决定了"哪些目录是包"、"包之间怎么链接"、"依赖版本怎么统一"。这一章把 pnpm 在 Monorepo 中的每个能力掰开揉碎。

### 3.1 pnpm-workspace.yaml 配置与包发现

```yaml
# pnpm-workspace.yaml —— 告诉 pnpm "哪些目录是 Workspace 包"
packages:
  - "apps/*"        # apps/ 下每个子目录是一个包
  - "packages/*"    # packages/ 下每个子目录是一个包
  - "tooling/*"     # tooling/ 下每个子目录是一个包
  # - "!packages/legacy"  # 用 ! 排除特定目录
```

```
pnpm 包发现机制：

  pnpm-workspace.yaml 中的 glob 模式：
  "apps/*"  → 匹配 apps/web、apps/admin、apps/api
              但不匹配 apps/web/src（不递归）

  "packages/**" → 匹配 packages/ui、packages/utils/core（递归）
                  → 通常不需要递归，一层就够

  发现规则：
  1. 扫描 glob 匹配的目录
  2. 在每个目录中查找 package.json
  3. 读取 package.json 的 name 字段 → 注册为 Workspace 包
  4. 没有 package.json 的目录会被忽略
```

```bash
# 查看当前 Workspace 中所有包
pnpm ls --depth -1 -r
# 输出：
# @repo/web 0.1.0 → apps/web
# @repo/admin 0.1.0 → apps/admin
# @repo/ui 0.1.0 → packages/ui
# @repo/utils 0.1.0 → packages/utils
# @repo/typescript-config 0.0.0 → tooling/typescript-config

# 包的命名约定（推荐统一前缀）
# @repo/web        ← @repo 是你的 scope
# @repo/ui
# @repo/utils
# → 所有内部包用同一个 scope，一眼就知道是内部包
```

> 💡 **命名建议**：所有内部包统一用 `@repo/xxx` 或 `@your-org/xxx` 前缀。这样在 import 时一眼就能区分内部包和第三方依赖。

### 3.2 workspace: 协议——内部包的依赖链接

```jsonc
// apps/web/package.json —— 一个消费内部包的应用
{
  "name": "@repo/web",
  "dependencies": {
    "@repo/ui": "workspace:*",       // 引用 packages/ui
    "@repo/utils": "workspace:*",    // 引用 packages/utils
    "react": "^18.3.0",              // 第三方依赖照常写
    "next": "^15.2.0"
  }
}
```

```
workspace: 协议的工作原理：

  "workspace:*"  → 链接到 Workspace 中同名包的当前版本
  "workspace:^"  → 同上，发布时转换为 ^x.y.z
  "workspace:~"  → 同上，发布时转换为 ~x.y.z

  pnpm install 时发生了什么？
  1. 看到 "@repo/ui": "workspace:*"
  2. 在 Workspace 中查找 name 为 "@repo/ui" 的包
  3. 找到 packages/ui/ → 创建符号链接（symlink）
  4. apps/web/node_modules/@repo/ui → ../../packages/ui

  效果：
  ✅ apps/web 直接引用 packages/ui 的源码
  ✅ 改了 packages/ui → apps/web 立即生效（HMR 热更新）
  ✅ 无需 npm link、无需发版
```

```
workspace: 协议 vs 直接写版本号：

  ❌ "@repo/ui": "^1.0.0"
  → pnpm 会去 npm registry 查找 @repo/ui
  → 找不到（内部包没发布）→ 安装失败

  ❌ "@repo/ui": "file:../../packages/ui"
  → 能工作，但不会自动跟踪版本
  → pnpm publish 时不会替换为真实版本

  ✅ "@repo/ui": "workspace:*"
  → pnpm 知道这是 Workspace 内部包
  → 开发时用 symlink，发布时自动替换为真实版本号
  → 这是 pnpm Monorepo 的标准做法
```

```
发布时 workspace: 协议的自动转换：

  开发时（package.json）：
  "@repo/ui": "workspace:*"    → 符号链接到本地源码
  "@repo/ui": "workspace:^"    → 符号链接到本地源码

  pnpm publish 时（发布到 npm 的 package.json）：
  "@repo/ui": "workspace:*"    → "@repo/ui": "1.2.3"  （精确版本）
  "@repo/ui": "workspace:^"    → "@repo/ui": "^1.2.3" （兼容版本）
  "@repo/ui": "workspace:~"    → "@repo/ui": "~1.2.3" （补丁版本）

  → pnpm 自动处理，你不需要手动改版本号
```

### 3.3 catalog: 协议——统一依赖版本管理

`catalog:` 是 pnpm 9.5+ 引入的杀手级特性——在一个地方定义依赖版本，所有包共享。

```yaml
# pnpm-workspace.yaml —— 在 Workspace 配置中定义 catalog
packages:
  - "apps/*"
  - "packages/*"
  - "tooling/*"

# 默认 catalog（用 catalog: 引用）
catalog:
  react: ^18.3.1
  react-dom: ^18.3.1
  typescript: ^5.8.3
  next: ^15.2.0
  zod: ^3.24.0

# 命名 catalog（用 catalog:名称 引用）
catalogs:
  testing:
    vitest: ^3.1.0
    playwright: ^1.50.0
    "@testing-library/react": ^16.0.0
  build:
    tsup: ^8.4.0
    esbuild: ^0.25.0
```

```jsonc
// apps/web/package.json —— 用 catalog: 引用版本
{
  "name": "@repo/web",
  "dependencies": {
    "react": "catalog:",          // → 解析为 ^18.3.1（来自默认 catalog）
    "react-dom": "catalog:",      // → 解析为 ^18.3.1
    "next": "catalog:",           // → 解析为 ^15.2.0
    "@repo/ui": "workspace:*"    // 内部包用 workspace: 协议
  },
  "devDependencies": {
    "typescript": "catalog:",           // → ^5.8.3
    "vitest": "catalog:testing",        // → ^3.1.0（来自 testing catalog）
    "tsup": "catalog:build"             // → ^8.4.0（来自 build catalog）
  }
}
```

```
catalog: vs 传统做法——为什么更好？

  传统做法（每个包单独写版本）：
  apps/web/package.json:      "react": "^18.3.0"
  apps/admin/package.json:    "react": "^18.2.0"   ← 版本不一致！
  packages/ui/package.json:   "react": "^18.3.1"   ← 又不一样！
  → 升级 React？改 3 个文件，容易漏

  catalog: 做法（版本集中定义）：
  pnpm-workspace.yaml:        react: ^18.3.1       ← 只定义一次
  所有 package.json:           "react": "catalog:"  ← 都引用这里
  → 升级 React？改 1 个文件，全部生效

  额外好处：
  ✅ 减少 Git 合并冲突（改依赖版本不再碰 package.json）
  ✅ pnpm publish 时自动替换为真实版本号
  ✅ 命名 catalog 可以按用途分组（testing、build）
```

> 💡 **迁移提示**：已有项目可以用 `pnpx codemod pnpm/catalog` 一键迁移到 catalog: 协议，自动提取所有 package.json 中的版本到 pnpm-workspace.yaml。

### 3.4 .npmrc 与依赖提升策略

```ini
# .npmrc —— 放在 Monorepo 根目录
# pnpm 的行为控制文件

# ① 严格模式（默认开启，推荐保持）
# pnpm 默认不会把依赖提升到根 node_modules
# → 每个包只能访问自己声明的依赖
# → 防止"幽灵依赖"（用了但没声明的依赖）

# ② 如果某些工具需要提升（如 React Native、Storybook）
# shamefully-hoist=true       # 全部提升（不推荐，破坏严格模式）
# public-hoist-pattern[]=*eslint*   # 只提升匹配的包
# public-hoist-pattern[]=*prettier* # 只提升匹配的包

# ③ CI 环境配置
frozen-lockfile=true           # CI 中冻结锁文件（不允许自动更新）

# ④ 注册表配置（可选）
# registry=https://registry.npmmirror.com  # 国内镜像
```

```
pnpm 的依赖隔离机制（vs npm/yarn）：

  npm/yarn 的扁平化安装：
  node_modules/
  ├── react/         ← 你声明的依赖
  ├── lodash/        ← 你没声明！但 react 依赖了它
  └── scheduler/     ← 你没声明！但 react 依赖了它
  → 你的代码可以 import lodash → 但它不在你的 package.json 里
  → 某天 react 不再依赖 lodash → 你的代码炸了 → 幽灵依赖

  pnpm 的严格隔离：
  node_modules/
  ├── .pnpm/              ← 真实的依赖存储（硬链接到全局 store）
  │   ├── react@18.3.1/
  │   ├── lodash@4.17.21/
  │   └── scheduler@0.23.0/
  └── react/              ← 符号链接 → .pnpm/react@18.3.1
  → 你只能 import react（你声明的）
  → import lodash → 报错！你没声明这个依赖
  → 强制你在 package.json 中声明所有依赖
```

| 配置项 | 作用 | 推荐值 |
|:---|:---|:---|
| `shamefully-hoist` | 提升所有依赖到根目录 | `false`（保持严格模式） |
| `public-hoist-pattern` | 只提升匹配的包 | 按需添加（如 ESLint 插件） |
| `frozen-lockfile` | CI 中禁止更新锁文件 | `true` |
| `strict-peer-dependencies` | 严格检查 peerDependencies | `false`（Monorepo 中通常关闭） |

### 3.5 pnpm 命令速查：filter / recursive / why

```bash
# ═══════════════════════════════════════
# pnpm --filter：对特定包执行命令（最常用）
# ═══════════════════════════════════════

# 给指定包安装依赖
pnpm add lodash --filter @repo/utils        # 给 @repo/utils 装 lodash
pnpm add -D vitest --filter @repo/web       # 给 @repo/web 装 vitest（devDep）

# 在指定包中运行脚本
pnpm --filter @repo/web dev                 # 只启动 web 应用
pnpm --filter @repo/web build               # 只构建 web 应用
pnpm --filter @repo/ui test                 # 只测试 ui 包

# 通配符过滤
pnpm --filter "@repo/*" build               # 构建所有 @repo/ 开头的包
pnpm --filter "./apps/*" dev                # 只启动 apps 目录下的应用

# 依赖关系过滤
pnpm --filter @repo/web...  build           # 构建 web 及其所有依赖（上游）
pnpm --filter ...@repo/ui   build           # 构建 ui 及所有依赖它的包（下游）
pnpm --filter @repo/web^... build           # 只构建 web 的依赖（不包含 web 自身）

# ═══════════════════════════════════════
# pnpm -r：递归在所有包中执行
# ═══════════════════════════════════════

pnpm -r run build                           # 所有包执行 build
pnpm -r run test                            # 所有包执行 test
pnpm -r exec -- rm -rf dist                 # 所有包执行 shell 命令

# ═══════════════════════════════════════
# pnpm why：调试依赖关系
# ═══════════════════════════════════════

pnpm why react                              # 谁依赖了 react？
pnpm why lodash --filter @repo/web          # web 为什么有 lodash？
# → 输出依赖链：@repo/web → @repo/utils → lodash
```

| 命令 | 用途 | 示例 |
|:---|:---|:---|
| `--filter <pkg>` | 针对单个包操作 | `pnpm --filter @repo/web dev` |
| `--filter <pkg>...` | 包及其上游依赖 | `pnpm --filter @repo/web... build` |
| `--filter ...<pkg>` | 包及其下游消费者 | `pnpm --filter ...@repo/ui test` |
| `-r` | 递归所有包 | `pnpm -r run lint` |
| `why` | 查询依赖来源 | `pnpm why lodash` |
| `ls -r` | 列出所有包 | `pnpm ls --depth -1 -r` |
| `-w` | 操作根目录 | `pnpm add -D turbo -w` |

> 💡 **Turborepo vs pnpm --filter**：在 Monorepo 中，日常开发用 `turbo run` 替代 `pnpm -r run`——Turborepo 有缓存和并行优化。但 `pnpm --filter` 仍然是安装依赖、调试的必备工具。

---

## 4. Turborepo 任务编排与 turbo.json

pnpm 管依赖，Turborepo 管任务——它知道你的包之间谁依赖谁，所以能按正确的顺序构建、能并行执行无依赖关系的任务、能跳过没变化的包。这一切的核心就是 `turbo.json`。

### 4.1 turbo.json 配置全解析

```jsonc
// turbo.json —— Turborepo 的唯一配置文件
{
  // JSON Schema 提供 IDE 自动补全
  "$schema": "https://turbo.build/schema.json",

  // 全局依赖：这些文件变了，所有任务的缓存全部失效
  "globalDependencies": [
    ".env",                    // 环境变量文件
    "tsconfig.base.json"       // 全局 TS 配置
  ],

  // 全局环境变量：这些变量参与所有任务的缓存哈希计算
  "globalEnv": [
    "NODE_ENV",
    "CI"
  ],

  // 任务定义（核心部分）
  "tasks": {
    "build": {
      "dependsOn": ["^build"],           // 先构建上游依赖
      "inputs": ["src/**", "tsconfig.json"],  // 这些文件参与缓存哈希
      "outputs": ["dist/**"],            // 构建产物（缓存恢复时还原）
      "env": ["API_URL"]                 // 任务级环境变量
    },
    "dev": {
      "cache": false,                    // 开发服务器不缓存
      "persistent": true                 // 长时间运行的任务
    },
    "lint": {
      "dependsOn": [],                   // 不依赖其他任务
      "outputs": []                      // 没有文件输出
    },
    "test": {
      "dependsOn": ["build"],            // 测试前先构建
      "outputs": ["coverage/**"],        // 覆盖率报告
      "env": ["DATABASE_URL"]
    },
    "clean": {
      "cache": false                     // 清理任务不缓存
    }
  }
}
```

```
turbo.json 关键字段速查：

  字段              │ 作用                    │ 默认值
  ──────────────────┼─────────────────────────┼──────────
  dependsOn         │ 任务执行前先完成哪些任务    │ []
  inputs            │ 哪些文件变化触发重新执行     │ 所有文件
  outputs           │ 构建产物路径（缓存恢复用）   │ []
  env               │ 影响缓存的环境变量          │ []
  cache             │ 是否启用缓存              │ true
  persistent        │ 是否为长时间运行的任务      │ false
  outputLogs        │ 日志输出方式               │ "full"
```

### 4.2 Task 定义：dependsOn 与拓扑排序

```
dependsOn 的三种写法——决定任务执行顺序：

  1. "dependsOn": ["^build"]
     ↑ ^ 符号 = "我的依赖包"的 build 任务先执行
     → 如果 web 依赖 ui，则先执行 ui 的 build，再执行 web 的 build
     → 这叫"拓扑排序"——按依赖图的顺序执行

  2. "dependsOn": ["build"]
     ↑ 没有 ^ = 同一个包内的 build 任务先执行
     → 先执行 web 的 build，再执行 web 的 test
     → 这叫"同包依赖"

  3. "dependsOn": ["^build", "lint"]
     ↑ 可以混合使用
     → 先执行依赖包的 build + 自己的 lint，再执行自己的 build
```

```
拓扑排序可视化——turbo run build 的执行顺序：

  依赖关系图：
  @repo/web ──────► @repo/ui ──────► @repo/utils
  @repo/admin ───► @repo/ui
  @repo/api ─────► @repo/utils

  turbo run build 的执行计划：
  ┌──────────────┐
  │ Round 1      │  @repo/utils build    ← 无依赖，最先执行
  ├──────────────┤
  │ Round 2      │  @repo/ui build       ← 依赖 utils，utils 完成后执行
  │ (并行)       │  @repo/api build      ← 只依赖 utils，也在这轮
  ├──────────────┤
  │ Round 3      │  @repo/web build      ← 依赖 ui，ui 完成后执行
  │ (并行)       │  @repo/admin build    ← 依赖 ui，也在这轮
  └──────────────┘

  → Turborepo 自动分析依赖图，最大化并行度
  → 你不需要手动排序，只需声明 "dependsOn": ["^build"]
```

```bash
# 可视化任务依赖图
turbo run build --graph            # 在浏览器中打开依赖图
turbo run build --graph=graph.svg  # 导出为 SVG 文件
turbo run build --graph=graph.dot  # 导出为 DOT 格式
```

### 4.3 inputs / outputs / env：精确控制缓存命中

```jsonc
// inputs —— 告诉 Turborepo "哪些文件变化算改动"
{
  "tasks": {
    "build": {
      // 默认：所有被 Git 跟踪的文件都参与哈希
      // 自定义 inputs 可以缩小范围 → 提高缓存命中率
      "inputs": [
        "src/**",              // 源码文件
        "tsconfig.json",       // TS 配置
        "package.json"         // 依赖变化
      ],
      // ↑ 这样改了 README.md 就不会触发重新构建

      // 排除语法
      "inputs": [
        "src/**",
        "!src/**/*.test.ts"    // 排除测试文件
        // → 改了测试不会触发 build 缓存失效
      ]
    }
  }
}
```

```jsonc
// outputs —— 告诉 Turborepo "构建产物在哪"
{
  "tasks": {
    "build": {
      "outputs": [
        "dist/**",             // 库包的构建产物
        ".next/**",            // Next.js 构建产物
        "!.next/cache/**"      // 排除 Next.js 内部缓存
      ]
      // Turborepo 缓存命中时：
      // 1. 跳过构建命令
      // 2. 从缓存中还原 dist/ 目录的所有文件
      // 3. 重放之前的终端输出
    },
    "lint": {
      "outputs": []            // lint 没有文件输出
      // → 缓存命中时只跳过执行 + 重放日志
    }
  }
}
```

```
env —— 环境变量如何影响缓存：

  场景：同一份代码，开发环境和生产环境的构建结果不同
  → API_URL=http://localhost:3000  vs  API_URL=https://api.prod.com
  → 必须把 API_URL 纳入缓存哈希，否则开发缓存会被当作生产缓存复用

  三级环境变量控制：
  ┌──────────────────┬───────────────────────────────┐
  │ globalEnv        │ 影响所有任务的缓存              │
  │                  │ "globalEnv": ["NODE_ENV", "CI"] │
  ├──────────────────┼───────────────────────────────┤
  │ tasks.xxx.env    │ 只影响特定任务的缓存             │
  │                  │ "env": ["API_URL"]              │
  ├──────────────────┼───────────────────────────────┤
  │ globalPassThrough│ 传递但不影响缓存               │
  │ Env              │ "globalPassThroughEnv": ["npm_│
  │                  │ lifecycle_event"]               │
  └──────────────────┴───────────────────────────────┘
```

> 💡 **常见坑**：如果你的构建依赖环境变量但没在 `env` 或 `globalEnv` 中声明，Turborepo 不会把它纳入哈希——导致不同环境的构建结果被错误复用。遇到"缓存了但结果不对"，先检查环境变量声明。

### 4.4 并行执行与 concurrency 调优

```bash
# Turborepo 默认最大并行度 = CPU 核心数
turbo run build                    # 自动并行（默认 10 个并发任务）

# 手动控制并发数
turbo run build --concurrency=5    # 最多 5 个任务并行
turbo run build --concurrency=1    # 串行执行（调试用）
turbo run build --concurrency=50%  # 使用 50% 的 CPU 核心

# 开发模式下的并行
turbo run dev                      # 同时启动所有 app 的 dev server
# → persistent: true 的任务会一直运行，不会阻塞后续任务
```

```
并行执行的约束规则：

  有 dependsOn 约束的任务 → 必须等依赖完成后才执行
  无 dependsOn 约束的任务 → 可以同时执行

  示例（5 个包，3 种任务）：
  ┌─────────────────────────────────────────────────────────┐
  │ 时间线 →                                                │
  │                                                         │
  │ lint:   [utils][ui][web][admin][api]  ← 全部并行（无依赖）│
  │                                                         │
  │ build:  [utils]──►[ui]──►[web]       ← 按拓扑排序       │
  │                  └──►[api]  [admin]   ← ui/api 并行     │
  │                                                         │
  │ test:   等 build 完成后 → [utils][ui][web][admin][api]    │
  └─────────────────────────────────────────────────────────┘

  → lint 没有 dependsOn → 5 个包的 lint 同时执行
  → build 有 "^build" → 按依赖顺序，同层并行
  → test 有 ["build"] → 等自己的 build 完成后执行
```

### 4.5 Pipeline 设计最佳实践

```jsonc
// 生产级 turbo.json 最佳实践模板
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": [".env"],
  "globalEnv": ["NODE_ENV", "CI"],
  "tasks": {
    // ① build：需要拓扑排序（库包先构建，应用后构建）
    "build": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "tsconfig.json", "package.json"],
      "outputs": ["dist/**", ".next/**", "!.next/cache/**"],
      "env": ["API_URL", "NEXT_PUBLIC_*"]
    },

    // ② dev：不缓存，长时间运行
    "dev": {
      "cache": false,
      "persistent": true
    },

    // ③ lint：独立执行，不依赖任何任务
    "lint": {
      "dependsOn": [],
      "inputs": ["src/**", "eslint.config.*"],
      "outputs": []
    },

    // ④ type-check：独立的类型检查（比 build 快）
    "type-check": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "tsconfig.json"],
      "outputs": []
    },

    // ⑤ test：需要先构建
    "test": {
      "dependsOn": ["build"],
      "inputs": ["src/**", "tests/**", "vitest.config.*"],
      "outputs": ["coverage/**"],
      "env": ["DATABASE_URL", "TEST_*"]
    },

    // ⑥ clean：清理产物，不缓存
    "clean": {
      "cache": false
    }
  }
}
```

```
Pipeline 设计原则：

  1. build 用 ^build（拓扑排序）
     → 确保依赖包先构建

  2. lint 不设 dependsOn
     → lint 不需要等构建完成，可以立即并行执行
     → 加快 CI 速度

  3. dev 用 persistent + cache:false
     → 开发服务器是长时间运行的，不能缓存

  4. 用 inputs 排除无关文件
     → 改 README 不触发 build
     → 改测试不触发 build（只触发 test）
     → 大幅提高缓存命中率

  5. 把 type-check 独立出来
     → 不需要生成 dist 文件，只做类型检查
     → 比 build 快，CI 中可以和 lint 并行
```

> 💡 **环境变量通配符**：`"env": ["NEXT_PUBLIC_*"]` 支持通配符——所有以 `NEXT_PUBLIC_` 开头的环境变量都纳入缓存哈希。Next.js 项目必须加这个，否则会出现客户端环境变量缓存不一致的问题。

---

## 5. 缓存策略：Turborepo 的核心武器

缓存是 Turborepo 存在的最大理由——改了 1 个文件只重新构建 1 个包，其余 49 个包直接从缓存恢复。这一章搞懂缓存的每一个环节。

### 5.1 内容哈希：缓存命中的判定机制

```
Turborepo 的缓存判定流程：

  每次执行任务前，Turborepo 计算一个哈希值：

  hash = SHA256(
    源码文件内容（inputs 匹配的文件）
    + 依赖包的哈希值（上游包的构建哈希）
    + package.json（依赖列表）
    + pnpm-lock.yaml 中该包的锁定部分
    + turbo.json 中该任务的配置
    + 环境变量值（env + globalEnv 声明的变量）
    + globalDependencies 的文件内容
  )

  判定逻辑：
  ┌──────────────────────────────────┐
  │ 计算当前哈希 → 12ab34cd          │
  │                                  │
  │ 查找缓存：                       │
  │ ├── 本地 .turbo 有 12ab34cd？    │
  │ │   └── ✅ 命中！跳过执行         │
  │ ├── Remote Cache 有 12ab34cd？   │
  │ │   └── ✅ 命中！下载并恢复       │
  │ └── 都没有？                     │
  │     └── ❌ 未命中，执行任务        │
  │         → 完成后将产物存入缓存     │
  └──────────────────────────────────┘
```

```
哈希敏感的因素（改了就缓存失效）：

  ✅ 会触发缓存失效：
  - 修改了 src/ 下的源码文件
  - 修改了 package.json 中的依赖版本
  - 修改了 tsconfig.json
  - 修改了 env 声明的环境变量的值
  - 上游依赖包的哈希变了

  ❌ 不会触发缓存失效（默认情况下）：
  - 修改了 README.md（如果 inputs 排除了它）
  - 修改了 .gitignore
  - 修改了未声明的环境变量
```

### 5.2 本地缓存：.turbo 目录解剖

```
本地缓存存储位置：

  node_modules/.cache/turbo/       ← Turborepo v2 的默认缓存目录
  ├── 12ab34cd5678ef90.tar.zst     ← 压缩的构建产物
  ├── 12ab34cd5678ef90-meta.json   ← 元数据（哈希、时间戳、日志）
  └── ...

  每个缓存条目包含：
  1. 构建产物的 tar.zst 压缩包（outputs 声明的文件）
  2. 终端输出日志（缓存命中时重放）
  3. 元数据（哈希、持续时间、时间戳）
```

```bash
# 缓存命中时的终端输出
$ turbo run build

 Tasks:    5 successful, 5 total
 Cached:   4 cached, 5 total         ← 4 个包命中缓存！
 Time:     1.2s                       ← 只花了 1.2 秒（全量构建要 45 秒）

# 缓存命中的包会显示：
@repo/utils:build: cache hit, replaying logs 12ab34cd
@repo/ui:build: cache hit, replaying logs 56ef78ab
# → "replaying logs" = 重放之前的终端输出，看起来像执行了一样

# 清除本地缓存
turbo run build --force             # 忽略缓存，强制重新执行
rm -rf node_modules/.cache/turbo    # 手动删除缓存目录
```

### 5.3 Remote Cache：团队共享缓存

```
Remote Cache 的价值——团队级缓存共享：

  没有 Remote Cache：
  开发者 A 构建了 50 个包 → 缓存在 A 的电脑上
  开发者 B pull 了同样的代码 → 从零构建 50 个包（A 的缓存用不上）
  CI 服务器构建 → 又从零构建 50 个包
  → 同样的代码被构建了 3 次

  有 Remote Cache：
  开发者 A 构建了 50 个包 → 缓存上传到 Remote Cache
  开发者 B pull 了同样的代码 → 从 Remote Cache 下载 → 0 秒
  CI 服务器构建 → 从 Remote Cache 下载 → 0 秒
  → 同样的代码只构建 1 次，全团队共享
```

```bash
# ═══════════════════════════════════════
# 方式一：Vercel Remote Cache（最简单）
# ═══════════════════════════════════════

# 登录 Vercel（免费额度足够小团队）
npx turbo login

# 链接到 Vercel 项目
npx turbo link

# 完成！之后 turbo run build 自动使用 Remote Cache
# → 构建产物上传到 Vercel
# → 其他开发者和 CI 自动下载

# ═══════════════════════════════════════
# 方式二：自建 Remote Cache 服务器
# ═══════════════════════════════════════

# 开源方案：ducktors/turborepo-remote-cache
# → 支持 S3、Google Cloud Storage、Azure Blob Storage
docker run -p 3000:3000 \
  -e STORAGE_PROVIDER=s3 \
  -e S3_ACCESS_KEY=xxx \
  -e S3_SECRET_KEY=xxx \
  -e S3_BUCKET=turbo-cache \
  ducktors/turborepo-remote-cache

# 在 turbo.json 或 .turbo/config.json 中配置
# {
#   "remoteCache": {
#     "apiUrl": "https://your-cache-server.com"
#   }
# }
```

```bash
# CI 中启用 Remote Cache（GitHub Actions 示例）
# 在 workflow 中设置环境变量
env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
  TURBO_TEAM: your-team-name

# turbo 会自动检测这些环境变量并启用 Remote Cache
```

### 5.4 缓存命中率优化技巧

```
提高缓存命中率的 5 个技巧：

  技巧 1：精确定义 inputs（排除无关文件）
  ──────────────────────────────────────
  ❌ 默认行为：所有 Git 跟踪文件参与哈希
  → 改 README.md → 缓存失效 → 重新构建

  ✅ 优化后：
  "inputs": ["src/**", "tsconfig.json", "package.json"]
  → 只有源码、配置、依赖变化才触发重新构建
  → 改 README、改测试 → 缓存不受影响

  技巧 2：把测试文件从 build 的 inputs 中排除
  ──────────────────────────────────────
  "build": { "inputs": ["src/**", "!src/**/*.test.*", "!src/**/*.spec.*"] }
  "test":  { "inputs": ["src/**", "tests/**", "vitest.config.*"] }
  → 改了测试 → build 缓存不失效，只有 test 重新执行

  技巧 3：分离 type-check 和 build
  ──────────────────────────────────────
  合并："build" 同时做类型检查 + 产物构建
  → 改了类型 → 整个 build 重新执行

  分离：
  "type-check": { "outputs": [] }   ← 只检查类型，无产物
  "build": { "outputs": ["dist/**"] } ← 只构建产物
  → 类型问题不影响 build 缓存

  技巧 4：稳定 globalDependencies
  ──────────────────────────────────────
  ❌ "globalDependencies": [".env"]
  → .env 文件频繁变化（本地开发不同的配置）
  → 所有缓存频繁失效

  ✅ 改用 env 字段精确声明
  → "env": ["API_URL", "DATABASE_URL"]
  → 只有特定变量变化才影响缓存

  技巧 5：排除 Next.js 内部缓存
  ──────────────────────────────────────
  "outputs": [".next/**", "!.next/cache/**"]
  → .next/cache 是 Next.js 自己的增量编译缓存
  → 不需要 Turborepo 来管理它
  → 排除后大幅减少缓存体积和传输时间
```

### 5.5 缓存调试：--dry-run 与 --summarize

```bash
# ═══════════════════════════════════════
# --dry-run：查看哪些任务会执行（不真正执行）
# ═══════════════════════════════════════

$ turbo run build --dry-run

# 输出每个任务的状态：
# @repo/utils#build
#   Task:           build
#   Hash:           12ab34cd
#   Cached:         true          ← 会命中缓存
#   Inputs:         src/index.ts, package.json, tsconfig.json
#   Outputs:        dist/**
#   Dependencies:   (none)

# @repo/web#build
#   Task:           build
#   Hash:           ef567890
#   Cached:         false         ← 不会命中缓存（有变化）
#   Inputs:         src/app/page.tsx (changed!)
#   Dependencies:   @repo/utils#build, @repo/ui#build

# → 不执行任何任务，只告诉你"如果执行会怎样"
# → 用来排查"为什么这个包没命中缓存"
```

```bash
# ═══════════════════════════════════════
# --summarize：生成详细的执行报告
# ═══════════════════════════════════════

$ turbo run build --summarize

# 在 .turbo/runs/ 目录生成 JSON 报告：
# .turbo/runs/2026-05-07T12-00-00.json

# 报告包含：
# - 每个任务的哈希值和输入文件列表
# - 缓存命中/未命中状态
# - 执行时间
# - 环境变量（脱敏后的）
# → 适合在 CI 中生成，用于事后分析缓存效率
```

```bash
# 常见调试场景

# "为什么这个包缓存没命中？"
turbo run build --dry-run --filter=@repo/web
# → 检查 Hash 值是否变化
# → 检查 Inputs 中哪个文件标记为 changed

# "缓存总是失效？"
turbo run build --summarize
# → 检查 globalDependencies 是否包含频繁变化的文件
# → 检查 env 是否包含不稳定的环境变量

# "想看 Turborepo 到底在干什么？"
turbo run build --verbosity=2    # 详细日志
# → 输出哈希计算过程、缓存查找过程
```

> 💡 **调试口诀**：缓存不命中 → `--dry-run` 看哈希变化 → 检查 inputs/env/globalDependencies → 找到频繁变化的源头 → 排除或稳定它。

---

## 6. 共享配置：TypeScript / ESLint / Prettier

Monorepo 的一大优势就是"配置只写一份"。这一章用 `tooling/` 目录创建共享配置包，让所有项目自动继承统一的代码规范。

### 6.1 tooling 包架构设计

```
tooling 目录结构：

  tooling/
  ├── typescript-config/          ← 共享 TypeScript 配置
  │   ├── package.json            ← name: "@repo/typescript-config"
  │   ├── base.json               ← 基础配置（所有包通用）
  │   ├── node.json               ← Node.js 后端项目配置
  │   ├── nextjs.json             ← Next.js 前端项目配置
  │   └── library.json            ← 库包配置
  │
  ├── eslint-config/              ← 共享 ESLint 配置
  │   ├── package.json            ← name: "@repo/eslint-config"
  │   ├── base.js                 ← 基础规则
  │   ├── react.js                ← React 项目规则
  │   └── node.js                 ← Node.js 项目规则
  │
  └── prettier-config/            ← 共享 Prettier 配置
      ├── package.json            ← name: "@repo/prettier-config"
      └── index.js                ← 格式化规则
```

```jsonc
// tooling/typescript-config/package.json
{
  "name": "@repo/typescript-config",
  "version": "0.0.0",
  "private": true,           // 不发布到 npm
  "files": ["*.json"]        // 只导出 JSON 配置文件
}
```

### 6.2 TypeScript 配置分层继承

```jsonc
// tooling/typescript-config/base.json —— 所有项目通用的基础配置
{
  "$schema": "https://json.schemastore.org/tsconfig",
  "compilerOptions": {
    // 类型安全（严格模式）
    "strict": true,
    "noUncheckedIndexedAccess": true,    // obj[key] 返回 T | undefined
    "noImplicitOverride": true,

    // 模块系统
    "module": "ESNext",
    "moduleResolution": "bundler",       // 适配现代打包工具
    "resolveJsonModule": true,
    "isolatedModules": true,             // 每个文件独立编译

    // 输出
    "target": "ES2022",
    "lib": ["ES2022"],
    "declaration": true,                 // 生成 .d.ts 类型声明
    "declarationMap": true,              // 生成声明的 source map
    "sourceMap": true,

    // 互操作
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "forceConsistentCasingInFileNames": true,

    // 跳过类型检查（加速）
    "skipLibCheck": true
  },
  "exclude": ["node_modules", "dist"]
}
```

```jsonc
// tooling/typescript-config/nextjs.json —— Next.js 项目继承基础配置
{
  "$schema": "https://json.schemastore.org/tsconfig",
  "extends": "./base.json",               // ← 继承 base.json
  "compilerOptions": {
    "target": "ES2017",                    // Next.js 要求
    "lib": ["DOM", "DOM.Iterable", "ES2022"],
    "module": "ESNext",
    "jsx": "preserve",                     // Next.js 处理 JSX
    "plugins": [{ "name": "next" }],       // Next.js TS 插件
    "paths": {
      "@/*": ["./src/*"]                   // 路径别名
    }
  }
}
```

```jsonc
// tooling/typescript-config/library.json —— 库包配置
{
  "$schema": "https://json.schemastore.org/tsconfig",
  "extends": "./base.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "declarationMap": true
  }
}
```

```jsonc
// apps/web/tsconfig.json —— 在应用中引用共享配置
{
  "extends": "@repo/typescript-config/nextjs.json",  // ← 继承！
  "compilerOptions": {
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src", "next-env.d.ts", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
// → 只需 6 行，所有严格模式、模块系统配置都来自共享包
```

```
TypeScript 配置继承链：

  base.json（严格模式 + 模块系统 + 通用选项）
    ├── nextjs.json（+ DOM lib + JSX + Next 插件）
    │     └── apps/web/tsconfig.json（+ paths 别名）
    │     └── apps/admin/tsconfig.json（+ paths 别名）
    ├── node.json（+ Node types + CommonJS 兼容）
    │     └── apps/api/tsconfig.json
    └── library.json（+ outDir + declaration）
          └── packages/ui/tsconfig.json
          └── packages/utils/tsconfig.json
```

### 6.3 ESLint Flat Config 共享方案

ESLint v9+ 使用 Flat Config（`eslint.config.js`），配置是普通 JS 对象数组，非常适合在 Monorepo 中共享。

```javascript
// tooling/eslint-config/base.js —— 基础规则（所有项目通用）
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import importPlugin from "eslint-plugin-import-x";

export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: { "import-x": importPlugin },
    rules: {
      // 统一的代码质量规则
      "no-console": "warn",
      "no-unused-vars": "off",                      // 用 TS 版本替代
      "@typescript-eslint/no-unused-vars": ["warn", {
        argsIgnorePattern: "^_",                     // 允许 _xxx 命名
      }],
      "@typescript-eslint/no-explicit-any": "warn",
      "import-x/order": ["warn", {                   // import 排序
        groups: ["builtin", "external", "internal", "parent", "sibling"],
        "newlines-between": "always",
      }],
    },
  },
  { ignores: ["dist/", "node_modules/", ".next/", "coverage/"] },
];
```

```javascript
// tooling/eslint-config/react.js —— React 项目规则（继承 base）
import base from "./base.js";
import reactPlugin from "eslint-plugin-react";
import hooksPlugin from "eslint-plugin-react-hooks";

export default [
  ...base,                               // ← 继承基础规则
  reactPlugin.configs.flat.recommended,
  { plugins: { "react-hooks": hooksPlugin },
    rules: {
      ...hooksPlugin.configs.recommended.rules,
      "react/prop-types": "off",          // 用 TypeScript 替代
      "react/react-in-jsx-scope": "off",  // React 17+ 不需要
    },
  },
];
```

```javascript
// apps/web/eslint.config.js —— 应用中直接导入共享配置
import config from "@repo/eslint-config/react";
export default config;
// → 1 行搞定！所有规则来自共享包
```

```jsonc
// tooling/eslint-config/package.json
{
  "name": "@repo/eslint-config",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "exports": {
    "./base": "./base.js",
    "./react": "./react.js",
    "./node": "./node.js"
  },
  "dependencies": {
    "@eslint/js": "^9.18.0",
    "typescript-eslint": "^8.20.0",
    "eslint-plugin-import-x": "^4.6.0",
    "eslint-plugin-react": "^7.37.0",
    "eslint-plugin-react-hooks": "^5.1.0"
  }
}
```

### 6.4 Prettier 统一格式化

```javascript
// tooling/prettier-config/index.js —— 统一格式化规则
/** @type {import("prettier").Config} */
export default {
  semi: true,                    // 行尾分号
  singleQuote: false,            // 双引号
  tabWidth: 2,                   // 2 空格缩进
  trailingComma: "all",          // 尾逗号
  printWidth: 100,               // 每行最大 100 字符
  bracketSpacing: true,          // { foo } 而不是 {foo}
  arrowParens: "always",         // (x) => x 而不是 x => x
  endOfLine: "lf",               // 统一换行符
  plugins: ["prettier-plugin-tailwindcss"],  // Tailwind 类名排序（可选）
};
```

```jsonc
// tooling/prettier-config/package.json
{
  "name": "@repo/prettier-config",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "exports": { ".": "./index.js" },
  "dependencies": {
    "prettier-plugin-tailwindcss": "^0.6.0"
  }
}
```

```jsonc
// 根 package.json —— 引用共享 Prettier 配置
{
  "prettier": "@repo/prettier-config"
  // ↑ 这一行就够了！Prettier 会自动读取共享配置
  // 所有包都继承这个格式化规则
}
```

```bash
# 在根目录统一格式化（不需要每个包单独跑）
pnpm format                    # 对应 "format": "prettier --write ..."
# → Prettier 从根目录递归格式化所有文件
# → 不需要在 turbo.json 中定义 format 任务
# → 因为 Prettier 本身就是全局工具，不需要按包拆分
```

### 6.5 配置引用与覆盖策略

```
配置引用的完整依赖链：

  应用/包的 package.json 需要声明对 tooling 包的依赖：

  // apps/web/package.json
  {
    "devDependencies": {
      "@repo/typescript-config": "workspace:*",
      "@repo/eslint-config": "workspace:*",
      "eslint": "^9.18.0",        // ESLint 本身需要每个包自己安装
      "typescript": "catalog:"     // 版本来自 catalog
    }
  }

  引用方式：
  ┌────────────────────┬──────────────────────────────────────┐
  │ TypeScript         │ tsconfig.json → "extends": "@repo/…" │
  ├────────────────────┼──────────────────────────────────────┤
  │ ESLint             │ eslint.config.js → import + export    │
  ├────────────────────┼──────────────────────────────────────┤
  │ Prettier           │ 根 package.json → "prettier": "@…"   │
  └────────────────────┴──────────────────────────────────────┘
```

```javascript
// 覆盖策略：应用需要额外规则时，在导入后追加

// apps/web/eslint.config.js —— 继承 + 覆盖
import base from "@repo/eslint-config/react";

export default [
  ...base,                                 // 继承所有共享规则
  {
    // 针对这个项目的额外规则
    rules: {
      "no-console": "off",                 // 这个项目允许 console
      "@typescript-eslint/no-explicit-any": "off",  // 临时放宽
    },
  },
  {
    // 针对特定文件的规则
    files: ["src/scripts/**"],
    rules: { "no-process-exit": "off" },
  },
];
```

```jsonc
// apps/web/tsconfig.json —— 继承 + 覆盖
{
  "extends": "@repo/typescript-config/nextjs.json",
  "compilerOptions": {
    // 覆盖共享配置中的某些选项
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"]  // 项目特有的路径别名
    }
  },
  "include": ["src", "next-env.d.ts"],
  "exclude": ["node_modules"]
}
```

> 💡 **覆盖原则**：共享配置定义 80% 的通用规则，各项目只覆盖 20% 的差异部分。如果发现多个项目都在覆盖同一个规则，说明应该把它提升到共享配置中。

---

## 7. 内部包开发：从共享库到 UI 组件

Monorepo 的核心价值在于共享——共享工具函数、共享 UI 组件、共享校验规则。这一章教你怎么创建规范的内部包，以及什么时候用"源码引用"、什么时候用"构建产物"。

### 7.1 内部包的 package.json 规范

```jsonc
// packages/utils/package.json —— 一个标准的内部库包
{
  "name": "@repo/utils",
  "version": "0.1.0",
  "private": true,                 // 内部包不发布
  "type": "module",                // 使用 ESM

  // ① exports 字段（Node.js 12+ 标准，推荐）
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",   // TypeScript 类型
      "import": "./dist/index.mjs",   // ESM 入口
      "require": "./dist/index.cjs"   // CJS 入口（兼容旧项目）
    },
    "./date": {
      "types": "./dist/date.d.ts",
      "import": "./dist/date.mjs"
    }
  },

  // ② 回退字段（兼容不支持 exports 的工具）
  "main": "./dist/index.cjs",
  "module": "./dist/index.mjs",
  "types": "./dist/index.d.ts",

  // ③ 脚本
  "scripts": {
    "build": "tsup",
    "dev": "tsup --watch",
    "lint": "eslint src/",
    "test": "vitest run",
    "clean": "rm -rf dist"
  },

  // ④ 依赖
  "dependencies": {
    "date-fns": "catalog:"          // 第三方依赖用 catalog: 协议
  },
  "devDependencies": {
    "@repo/typescript-config": "workspace:*",
    "tsup": "catalog:build",
    "typescript": "catalog:"
  }
}
```

```
package.json 关键字段解释：

  exports（推荐）
  → 定义包的公开入口点
  → 支持条件导出（import/require/types）
  → 可以导出子路径：import { formatDate } from "@repo/utils/date"

  main / module / types（回退）
  → 兼容旧版 Node.js 和不支持 exports 的打包工具
  → 如果同时有 exports 和 main，exports 优先

  private: true
  → 内部包不发布到 npm
  → 如果将来要发布，改为 false 并删除这行
```

### 7.2 tsup 构建：ESM / CJS 双格式输出

```typescript
// packages/utils/tsup.config.ts
import { defineConfig } from "tsup";

export default defineConfig({
  entry: [
    "src/index.ts",              // 主入口
    "src/date.ts",               // 子路径入口
  ],
  format: ["esm", "cjs"],         // 同时输出 ESM 和 CJS
  dts: true,                      // 生成 .d.ts 类型声明
  sourcemap: true,                // 生成 source map
  clean: true,                    // 构建前清理 dist/
  splitting: true,                // 代码分割（ESM only）
  treeshake: true,                // Tree Shaking
  outDir: "dist",
});
```

```bash
# tsup 构建输出
$ pnpm --filter @repo/utils build

# dist/
# ├── index.mjs       ← ESM 格式
# ├── index.cjs       ← CJS 格式
# ├── index.d.ts      ← 类型声明
# ├── index.d.mts     ← ESM 类型声明
# ├── date.mjs
# ├── date.cjs
# └── date.d.ts
```

```
为什么选 tsup？

  tsup 是基于 esbuild 的库打包工具：
  ✅ 速度极快（esbuild 是 Go 写的，比 tsc 快 100 倍）
  ✅ 零配置即可输出 ESM + CJS + .d.ts
  ✅ 支持 Tree Shaking、代码分割
  ✅ 在 Monorepo 社区中是事实标准

  对比：
  tsc        → 只做类型检查 + 转译，不打包，不做 Tree Shaking
  esbuild    → 极快，但不生成 .d.ts
  rollup     → 功能强大但配置复杂
  tsup       → esbuild + dts 插件，最佳平衡
```

### 7.3 源码引用 vs 构建产物：两种模式对比

```
Monorepo 内部包有两种消费方式：

  模式 A：构建产物模式（Build First）
  ──────────────────────────────────
  packages/utils/src/index.ts → tsup build → dist/index.mjs
  apps/web → import from "@repo/utils"  → 读取 dist/index.mjs

  → 消费者读取的是构建后的产物
  → 需要先 turbo run build，再运行应用
  → 适合：需要发布到 npm 的包、有复杂构建步骤的包

  模式 B：源码引用模式（Transpile on Demand）
  ──────────────────────────────────
  packages/utils/src/index.ts
  apps/web → import from "@repo/utils"  → 直接读取 src/index.ts

  → 消费者直接读取 TypeScript 源码
  → 由消费者的打包工具（Next.js/Vite）负责编译
  → 不需要 build 步骤，改代码立即生效
  → 适合：纯内部包、不发布的包
```

```jsonc
// 源码引用模式的 package.json（不需要 build）
{
  "name": "@repo/utils",
  "private": true,
  "type": "module",
  "exports": {
    ".": {
      "types": "./src/index.ts",      // ← 直接指向 .ts 源码
      "default": "./src/index.ts"
    }
  },
  "scripts": {
    // 没有 build 脚本！
    "lint": "eslint src/",
    "test": "vitest run"
  }
}
// → 消费者直接 import 源码 → 由 Next.js/Vite 编译
```

| 维度 | **构建产物模式** | **源码引用模式** |
|:---|:---|:---|
| 需要 build 步骤 | ✅ 是 | ❌ 否 |
| HMR 热更新速度 | ⚠️ 需要 watch | ⭐ 即时生效 |
| 可发布到 npm | ✅ 是 | ❌ 否 |
| 消费者配置 | 无需额外配置 | 需要配置 transpile |
| 适用场景 | 公开包、复杂构建 | 纯内部包、快速迭代 |

```javascript
// Next.js 中使用源码引用模式需要的配置
// next.config.js
const nextConfig = {
  transpilePackages: ["@repo/ui", "@repo/utils"],
  // ↑ 告诉 Next.js："这些包是 TypeScript 源码，帮我编译"
};
```

> 💡 **推荐策略**：内部不发布的包用"源码引用模式"（开发体验最好），需要发布到 npm 的包用"构建产物模式"（兼容性最好）。

### 7.4 实战：创建 @repo/ui 组件库

```bash
# 创建 UI 组件库
mkdir -p packages/ui/src
cd packages/ui
pnpm init
```

```jsonc
// packages/ui/package.json（源码引用模式）
{
  "name": "@repo/ui",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "exports": {
    "./button": { "types": "./src/button.tsx", "default": "./src/button.tsx" },
    "./card":   { "types": "./src/card.tsx",   "default": "./src/card.tsx" },
    "./input":  { "types": "./src/input.tsx",  "default": "./src/input.tsx" }
  },
  "scripts": {
    "lint": "eslint src/",
    "test": "vitest run"
  },
  "peerDependencies": {
    "react": "catalog:",
    "react-dom": "catalog:"
  },
  "devDependencies": {
    "@repo/typescript-config": "workspace:*",
    "@repo/eslint-config": "workspace:*",
    "react": "catalog:",
    "typescript": "catalog:"
  }
}
```

```tsx
// packages/ui/src/button.tsx
import { type ButtonHTMLAttributes, forwardRef } from "react";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline";
  size?: "sm" | "md" | "lg";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", className, children, ...props }, ref) => {
    return (
      <button ref={ref} data-variant={variant} data-size={size} {...props}>
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";
```

```tsx
// apps/web/src/app/page.tsx —— 在应用中消费 UI 组件
import { Button } from "@repo/ui/button";
import { Card } from "@repo/ui/card";

export default function Home() {
  return (
    <Card>
      <h1>Hello Monorepo!</h1>
      <Button variant="primary" onClick={() => alert("Clicked!")}>
        Click me
      </Button>
    </Card>
  );
}
// → 直接 import，无需构建，HMR 即时生效
```

### 7.5 实战：创建 @repo/utils 工具包

```typescript
// packages/utils/src/index.ts —— 主入口（re-export 所有模块）
export { formatDate, parseDate, isToday } from "./date";
export { cn } from "./cn";
export { sleep, retry } from "./async";
```

```typescript
// packages/utils/src/cn.ts —— 类名合并工具（类似 clsx）
export function cn(...inputs: (string | undefined | null | false)[]): string {
  return inputs.filter(Boolean).join(" ");
}

// 使用示例：
// cn("btn", isActive && "btn-active", size === "lg" && "btn-lg")
// → "btn btn-active btn-lg"
```

```typescript
// packages/utils/src/async.ts —— 异步工具函数
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function retry<T>(
  fn: () => Promise<T>,
  options: { attempts?: number; delay?: number } = {},
): Promise<T> {
  const { attempts = 3, delay = 1000 } = options;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === attempts - 1) throw error;
      await sleep(delay * (i + 1));  // 指数退避
    }
  }
  throw new Error("Unreachable");
}
```

```typescript
// apps/web/src/lib/api.ts —— 在应用中使用共享工具
import { retry } from "@repo/utils";

export async function fetchUser(id: string) {
  return retry(
    () => fetch(`/api/users/${id}`).then((r) => r.json()),
    { attempts: 3, delay: 500 },
  );
}
// → @repo/utils 的代码在 web 和 api 中都能用
// → 一处修改，全部生效
```

> 💡 **包拆分原则**：不要把所有工具函数塞进一个 `@repo/utils`。当某类工具函数只被特定场景使用时，拆成独立包（如 `@repo/validators`、`@repo/api-client`）——这样 Turborepo 的缓存粒度更细，构建更快。

---

## 8. 版本管理与发布：Changesets 工作流

当你的内部包需要发布到 npm 供外部消费时，版本管理就成了刚需。Changesets 是 Monorepo 社区的标准方案——它让"记录变更 → 升级版本 → 生成 Changelog → 发布 npm"全流程自动化。

### 8.1 Changesets 安装与初始化

```bash
# 安装 Changesets CLI
pnpm add -D @changesets/cli -w

# 初始化（在 Monorepo 根目录执行）
pnpm changeset init

# 生成的文件：
# .changeset/
# ├── config.json     ← Changesets 配置
# └── README.md       ← 说明文件
```

```jsonc
// .changeset/config.json —— 核心配置
{
  "$schema": "https://unpkg.com/@changesets/config@3.1.1/schema.json",
  "changelog": "@changesets/cli/changelog",   // Changelog 生成器
  "commit": false,                             // 不自动 git commit
  "fixed": [],                                 // 固定版本组（下面解释）
  "linked": [],                                // 联动版本组
  "access": "public",                          // npm 发布权限（public/restricted）
  "baseBranch": "main",                        // 基准分支
  "updateInternalDependencies": "patch",       // 内部依赖变更时的版本升级策略
  "ignore": [                                  // 忽略这些包（不参与版本管理）
    "@repo/web",                               // 应用不发布
    "@repo/admin",
    "@repo/typescript-config",                 // 配置包不发布
    "@repo/eslint-config",
    "@repo/prettier-config"
  ]
}
```

### 8.2 变更集工作流：add → version → publish

```
Changesets 的三步工作流：

  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │  Step 1  │────►│  Step 2  │────►│  Step 3  │
  │   add    │     │ version  │     │ publish  │
  │ 记录变更  │     │ 升级版本  │     │ 发布 npm │
  └──────────┘     └──────────┘     └──────────┘
   开发者做         CI/发布前做        CI 自动做
```

```bash
# ═══════════════════════════════════════
# Step 1: pnpm changeset（开发者在 PR 中执行）
# ═══════════════════════════════════════

$ pnpm changeset

# 交互式问答：
# ? Which packages would you like to include?
#   ◉ @repo/utils        ← 选择改动了哪些包
#   ◯ @repo/ui
# ? Which packages should have a major bump?
#   → 无（选 minor 或 patch）
# ? Summary:
#   → "新增 retry 函数，支持指数退避策略"

# 生成文件：.changeset/funny-cats-dance.md
# ---
# "@repo/utils": minor
# ---
# 新增 retry 函数，支持指数退避策略

# ═══════════════════════════════════════
# Step 2: pnpm changeset version（发布前执行）
# ═══════════════════════════════════════

$ pnpm changeset version

# 自动做了 3 件事：
# 1. 读取 .changeset/ 下所有变更文件
# 2. 更新受影响包的 package.json 版本号
#    @repo/utils: 0.1.0 → 0.2.0（minor）
# 3. 生成/更新 CHANGELOG.md
# 4. 删除已处理的 .changeset/*.md 文件

# ═══════════════════════════════════════
# Step 3: pnpm changeset publish（CI 中自动执行）
# ═══════════════════════════════════════

$ pnpm changeset publish

# 自动做了 2 件事：
# 1. 对所有版本号变化的包执行 pnpm publish
# 2. 创建 Git Tag（@repo/utils@0.2.0）
```

### 8.3 语义化版本与 Changelog 自动生成

```
语义化版本（SemVer）规则：

  MAJOR.MINOR.PATCH → 例如 2.3.1

  PATCH (2.3.1 → 2.3.2)
  → Bug 修复、性能优化
  → 不影响 API

  MINOR (2.3.1 → 2.4.0)
  → 新增功能、新增 API
  → 向后兼容

  MAJOR (2.3.1 → 3.0.0)
  → 破坏性变更（Breaking Changes）
  → 不向后兼容

  在 Changesets 中选择版本类型：
  pnpm changeset → 选 patch/minor/major
  → Changesets 自动根据选择升级版本号
```

```markdown
# 自动生成的 CHANGELOG.md 示例

## 0.3.0 (2026-05-07)

### Minor Changes

- 新增 `retry` 函数，支持指数退避策略
- 新增 `formatDate` 函数的时区参数

### Patch Changes

- 修复 `cn` 函数在传入 `undefined` 时的类型错误

## 0.2.0 (2026-04-20)

### Minor Changes

- 新增 `sleep` 函数
```

```
Changesets 的联动版本（linked）和固定版本（fixed）：

  linked（联动）：任一包升级，组内所有包版本号保持一致
  → 适合：一组紧密耦合的包（如 @repo/core + @repo/react + @repo/vue）
  "linked": [vue"]("@repo/core", "@repo/react", "@repo/vue")

  fixed（固定）：组内所有包共享同一版本号
  → 适合：像 Babel 那样所有插件同版本
  "fixed": [plugin-*"]("@repo/plugin-*")
```

### 8.4 Private 包与发布策略

```
Monorepo 中的包分类与发布策略：

  ┌────────────────┬────────────────┬──────────────────────┐
  │ 包类型          │ private 设置    │ 发布策略              │
  ├────────────────┼────────────────┼──────────────────────┤
  │ 应用（apps/）   │ private: true  │ ❌ 不发布 npm         │
  │                │                │ → 部署到服务器/CDN     │
  ├────────────────┼────────────────┼──────────────────────┤
  │ 配置（tooling/）│ private: true  │ ❌ 不发布 npm         │
  │                │                │ → Monorepo 内部使用   │
  ├────────────────┼────────────────┼──────────────────────┤
  │ 内部库          │ private: true  │ ❌ 不发布 npm         │
  │ （不共享给外部） │                │ → workspace: 引用     │
  ├────────────────┼────────────────┼──────────────────────┤
  │ 公开库          │ private: false │ ✅ 发布到 npm         │
  │ （共享给外部）   │                │ → Changesets 管理版本 │
  └────────────────┴────────────────┴──────────────────────┘

  在 .changeset/config.json 的 ignore 中排除不发布的包：
  "ignore": ["@repo/web", "@repo/admin", "@repo/typescript-config", ...]
  → Changesets 只管理需要发布的公开库
```

```bash
# 根 package.json 中添加发布脚本
{
  "scripts": {
    "changeset": "changeset",
    "version-packages": "changeset version",
    "publish-packages": "turbo run build --filter='./packages/*' && changeset publish"
  }
}

# 发布流程：
# 1. 开发者提 PR 时运行 pnpm changeset 记录变更
# 2. PR 合入 main 后，CI 自动运行：
#    pnpm version-packages    → 升级版本号 + 生成 Changelog
#    pnpm publish-packages    → 构建 + 发布到 npm
```

> 💡 **大多数 Monorepo 不需要发布**：如果你的所有包都是内部使用（private: true），那么不需要 Changesets。它只在你需要把包发布到 npm 供外部项目消费时才有价值。

---

## 9. CI/CD 实战：GitHub Actions 全流程

Monorepo 的 CI 和 Polyrepo 不一样——你不能每次都全量构建所有包，也不能简单地按目录拆 workflow。这一章给出一套完整的 GitHub Actions 配置。

### 9.1 Monorepo CI 的挑战与策略

```
Monorepo CI 的核心问题：

  问题 1：全量构建太慢
  → 改了 @repo/utils 的一行代码
  → CI 构建所有 50 个包？❌ 浪费 40 分钟

  问题 2：依赖关系复杂
  → 改了 @repo/utils → 哪些包受影响？
  → @repo/ui 依赖 utils → 需要重新测试
  → @repo/web 依赖 ui → 也需要重新测试

  解决方案：Turborepo 的增量构建 + 远程缓存
  → turbo run build → 自动跳过未变化的包
  → Remote Cache → 复用之前 CI 的构建结果
  → --filter → 只构建受影响的包
```

### 9.2 GitHub Actions Workflow 配置

```yaml
# .github/workflows/ci.yml —— PR 检查 Workflow
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

# 同一 PR 的新 push 自动取消旧的 CI 运行
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}     # Remote Cache 认证
  TURBO_TEAM: ${{ vars.TURBO_TEAM }}          # Remote Cache 团队

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      # ① 拉取代码
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2          # 需要 2 层深度来检测变化

      # ② 安装 pnpm（使用 Corepack 读取 packageManager 字段）
      - uses: pnpm/action-setup@v4
        # 不需要指定版本，自动读取 package.json 的 packageManager

      # ③ 安装 Node.js + 配置 pnpm store 缓存
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: "pnpm"           # 自动缓存 pnpm store

      # ④ 安装依赖（使用冻结的锁文件）
      - run: pnpm install --frozen-lockfile

      # ⑤ 运行所有检查（Turborepo 自动并行 + 缓存）
      - run: pnpm turbo run lint type-check test build
```

### 9.3 CI 中的缓存加速：pnpm store + Turborepo Remote Cache

```
CI 中有两层缓存——叠加后效果惊人：

  第一层：pnpm store 缓存（缓存 npm 包下载）
  ──────────────────────────────────────────
  actions/setup-node 的 cache: "pnpm" 自动实现
  → 首次 CI：下载所有 npm 包 → 存入 GitHub Actions 缓存
  → 后续 CI：从缓存恢复 pnpm store → pnpm install 只需几秒
  → 节省：npm 包下载时间（通常 30-60 秒 → 3 秒）

  第二层：Turborepo Remote Cache（缓存构建产物）
  ──────────────────────────────────────────
  设置 TURBO_TOKEN + TURBO_TEAM 环境变量自动启用
  → 首次 CI：构建所有包 → 产物上传到 Vercel Remote Cache
  → 后续 CI：未变化的包直接从 Remote Cache 恢复产物
  → 节省：构建时间（通常 5-10 分钟 → 30 秒）

  两层叠加效果：
  ┌──────────────┬──────────┬──────────┐
  │ 场景          │ 无缓存    │ 有缓存    │
  ├──────────────┼──────────┼──────────┤
  │ pnpm install │ 60 秒    │ 3 秒     │
  │ turbo build  │ 300 秒   │ 5 秒     │
  │ 总计          │ 360 秒   │ 8 秒     │
  │ 加速比        │ -        │ 45x ⚡   │
  └──────────────┴──────────┴──────────┘
```

### 9.4 --filter 增量构建：只构建受影响的包

```bash
# 只构建自上次提交以来变化的包及其下游
turbo run build --filter='...[HEAD^1]'

# 只构建自 main 分支以来变化的包（PR 场景）
turbo run build --filter='...[origin/main]'

# 组合使用：变化的包 + 它们的下游依赖
turbo run build test --filter='...[origin/main]...'
```

```yaml
# 在 GitHub Actions 中使用增量构建
- name: Build affected packages
  run: |
    if [ "${{ github.event_name }}" = "pull_request" ]; then
      # PR：只构建相对于 main 分支变化的包
      pnpm turbo run build test --filter='...[origin/main]'
    else
      # Push to main：全量构建（确保发布前一切正常）
      pnpm turbo run build test
    fi
```

```
--filter 与 Turborepo 缓存的配合：

  场景：PR 修改了 @repo/utils 的一个函数

  不用 --filter（全量，靠缓存加速）：
  turbo run build
  → 执行 50 个包的 build 任务
  → 49 个命中缓存 → 1 个重新构建
  → 总耗时 ~10 秒（缓存恢复也有开销）

  用 --filter（增量，直接跳过）：
  turbo run build --filter='...[origin/main]'
  → 只执行 3 个包（utils + ui + web）
  → 其中 ui 和 web 可能还命中缓存
  → 总耗时 ~3 秒

  → --filter 减少任务数量，缓存加速每个任务 → 双重优化
```

### 9.5 完整 Pipeline：Lint → Test → Build → Publish

```yaml
# .github/workflows/release.yml —— 发布 Workflow（main 分支触发）
name: Release

on:
  push:
    branches: [main]

env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
  TURBO_TEAM: ${{ vars.TURBO_TEAM }}

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write        # 创建 Git Tag
      id-token: write        # npm provenance（来源证明）
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: "pnpm"
          registry-url: "https://registry.npmjs.org"

      - run: pnpm install --frozen-lockfile

      # 全量检查（发布前必须通过）
      - run: pnpm turbo run lint type-check test build

      # 创建发布 PR 或直接发布
      - uses: changesets/action@v1
        with:
          publish: pnpm changeset publish     # 发布到 npm
          version: pnpm changeset version     # 升级版本号
          commit: "chore: version packages"
          title: "chore: version packages"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

```
完整 CI/CD 流程图：

  开发者 PR：
  ┌─────────┐    ┌──────┐    ┌────────────┐    ┌───────┐
  │ PR 提交  │───►│ lint │───►│ type-check │───►│ test  │
  └─────────┘    └──────┘    └────────────┘    └───────┘
                                                   │
                                               ┌───▼───┐
                                               │ build │
                                               └───────┘

  合入 main：
  ┌──────────┐    ┌──────────────┐    ┌──────────────┐
  │ 全量检查  │───►│ changeset    │───►│ 发布到 npm   │
  │ lint+test │    │ version      │    │ 创建 Git Tag │
  │ +build   │    │ 升级版本号    │    │ 更新 Changelog│
  └──────────┘    └──────────────┘    └──────────────┘
```

> 💡 **changesets/action**：这个 GitHub Action 会自动检测是否有待发布的变更。如果有，它会创建一个"Version Packages"的 PR；当该 PR 合入后，自动发布到 npm。

---

## 10. 生产级最佳实践与常见陷阱

最后一章收集实战中最常遇到的问题和对应的解法——这些都是踩过坑后总结的经验。

### 10.1 目录膨胀治理与包拆分原则

```
Monorepo 的包什么时候该拆、什么时候不该拆：

  ✅ 应该拆成独立包的情况：
  → 被 2 个以上项目引用的代码
  → 有独立的版本生命周期
  → 由不同团队维护
  → 可以独立测试

  ❌ 不应该拆的情况：
  → 只被一个项目使用的代码 → 留在该项目内部
  → 拆了之后只有 1 个文件 → 太细了，合并到上层包
  → 拆了之后产生循环依赖 → 设计有问题

  包的数量建议：
  5-10 个包：小团队，够用
  10-30 个包：中团队，合理
  30+ 个包：大团队，需要严格的 CODEOWNERS
  100+ 个包：考虑是否需要拆仓库
```

### 10.2 依赖循环检测与预防

```bash
# 检测循环依赖
pnpm ls -r --depth 0 --json | npx dpdm --circular

# 或使用 madge 工具
npx madge --circular packages/*/src/index.ts
```

```
循环依赖的常见模式与解法：

  ❌ 循环：A → B → A
  packages/ui → packages/utils（ui 用了 utils 的函数）
  packages/utils → packages/ui（utils 用了 ui 的类型）

  ✅ 解法 1：提取公共部分
  packages/ui → packages/shared-types
  packages/utils → packages/shared-types
  → 把共享的类型提取到新包

  ✅ 解法 2：依赖反转
  packages/ui 定义接口
  packages/utils 实现接口
  → 依赖指向抽象，不指向具体实现

  ✅ 解法 3：合并包
  → 如果两个包总是一起改动，说明它们就不该分开
```

### 10.3 Docker 多阶段构建：turbo prune 精准裁剪

```dockerfile
# Dockerfile —— 用 turbo prune 构建最小化镜像
# turbo prune 只复制目标应用及其依赖到临时目录

# Stage 1：安装依赖
FROM node:22-alpine AS base
RUN corepack enable

# Stage 2：turbo prune（只保留 @repo/web 及其依赖）
FROM base AS pruner
WORKDIR /app
COPY . .
RUN pnpm dlx turbo prune @repo/web --docker
# 生成 out/ 目录：
# out/json/     → 只有 web 及其依赖的 package.json
# out/full/     → 只有 web 及其依赖的完整源码
# out/pnpm-lock.yaml

# Stage 3：安装依赖（利用 Docker 层缓存）
FROM base AS installer
WORKDIR /app
COPY --from=pruner /app/out/json/ .
COPY --from=pruner /app/out/pnpm-lock.yaml .
RUN pnpm install --frozen-lockfile

# Stage 4：构建
COPY --from=pruner /app/out/full/ .
RUN pnpm turbo run build --filter=@repo/web

# Stage 5：运行（最小化镜像）
FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=installer /app/apps/web/.next/standalone ./
COPY --from=installer /app/apps/web/public ./apps/web/public
COPY --from=installer /app/apps/web/.next/static ./apps/web/.next/static

EXPOSE 3000
CMD ["node", "apps/web/server.js"]
```

```
turbo prune 的价值：

  不用 prune：
  → COPY . . 复制整个 Monorepo（可能 2GB）
  → docker build 慢、镜像大

  用 prune：
  → 只复制 @repo/web + @repo/ui + @repo/utils（50MB）
  → docker build 快、镜像小
  → pnpm install 只安装目标应用的依赖
```

### 10.4 从 Polyrepo 迁移到 Monorepo

```
渐进式迁移步骤（推荐）：

  Step 1：创建 Monorepo 骨架
  → 初始化根目录、turbo.json、pnpm-workspace.yaml
  → 创建 tooling/ 共享配置

  Step 2：迁移第一个项目
  → 选一个最独立的项目（如 utils 库）
  → git subtree 或手动复制到 packages/utils
  → 调整路径和依赖

  Step 3：迁移第二个项目
  → 选一个依赖 utils 的项目
  → 把 npm 依赖改为 workspace: 协议
  → 验证构建和测试

  Step 4：逐步迁移剩余项目
  → 每次迁移一个，验证一个
  → 抽取共享代码到 packages/

  Step 5：统一配置和 CI
  → 统一 TypeScript / ESLint / Prettier 配置
  → 合并为一个 CI Workflow

  注意事项：
  ❌ 不要一次性迁移所有项目
  ❌ 不要在迁移期间做功能开发
  ✅ 保留 Git 历史（用 git subtree 或 git filter-repo）
  ✅ 在 Monorepo 里先跑通 CI 再删除旧仓库
```

### 10.5 常见陷阱与 FAQ

```
Q1：pnpm install 报错 "ERR_PNPM_PEER_DEP_ISSUES"
──────────────────────────────────────────
→ pnpm 默认严格检查 peerDependencies
→ 解法：在 .npmrc 中添加 strict-peer-dependencies=false
→ 或在 package.json 中正确声明 peerDependencies

Q2：TypeScript 找不到内部包的类型
──────────────────────────────────────────
→ 检查内部包的 package.json 是否正确配置了 exports.types
→ 源码引用模式：exports.types 指向 .ts 文件
→ 构建产物模式：确保 tsup 生成了 .d.ts + 执行了 build

Q3：turbo run build 报 "missing script" 错误
──────────────────────────────────────────
→ 某个包没有 build 脚本，但 turbo.json 定义了 build 任务
→ Turborepo 会跳过没有对应脚本的包（默认行为）
→ 检查是否有包名拼写错误

Q4：ESLint 在 Monorepo 中运行很慢
──────────────────────────────────────────
→ 确保每个包有自己的 eslint.config.js
→ 用 turbo run lint 并行执行（而不是根目录全局 eslint）
→ 在 turbo.json 中配置 inputs 排除 node_modules

Q5：CI 缓存总是不命中
──────────────────────────────────────────
→ 运行 turbo run build --dry-run 检查哈希
→ 常见原因：
  - .env 文件在 globalDependencies 中且经常变化
  - 时间戳或随机值被包含在构建输出中
  - pnpm-lock.yaml 频繁变化（锁定版本不一致）

Q6：pnpm 的 node_modules 结构和 npm 不同，某些工具报错
──────────────────────────────────────────
→ pnpm 使用符号链接 + 硬链接的方式管理 node_modules
→ 某些工具（如老版本的 Storybook、React Native）需要提升
→ 在 .npmrc 中添加 public-hoist-pattern[]=*storybook*
→ 或更新到支持 pnpm 的新版本
```

---
