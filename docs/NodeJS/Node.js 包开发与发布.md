# Node.js 包开发与发布

> 从零开始构建一个专业的 npm 包——TypeScript 编写、tsup 构建、Vitest 测试、changesets 版本管理、GitHub Actions 自动发布。

---

## 1. npm 包的本质：package.json 全解析

### 1.1 一个包到底是什么

```
npm 包 = 一个有 package.json 的文件夹

  my-utils/
  ├── package.json    ← 包的"身份证"
  ├── dist/           ← 构建产物（用户实际引入的代码）
  │   ├── index.js
  │   ├── index.mjs
  │   └── index.d.ts
  ├── src/            ← 源码（不发布）
  │   └── index.ts
  └── README.md

  发布到 npm 后：
  npm install my-utils
  → 下载到 node_modules/my-utils/
  → 用户 import { foo } from 'my-utils'
  → Node.js 根据 package.json 的 exports 字段找到入口文件
```

### 1.2 package.json 关键字段详解

```json
{
  "name": "@yourname/utils",
  "version": "1.0.0",
  "description": "A collection of utility functions",
  "license": "MIT",
  "author": "Your Name <you@example.com>",
  "repository": {
    "type": "git",
    "url": "https://github.com/yourname/utils"
  },
  "keywords": ["utils", "typescript", "helpers"],

  "type": "module",

  "main": "./dist/index.cjs",
  "module": "./dist/index.js",
  "types": "./dist/index.d.ts",

  "exports": {
    ".": {
      "import": {
        "types": "./dist/index.d.ts",
        "default": "./dist/index.js"
      },
      "require": {
        "types": "./dist/index.d.cts",
        "default": "./dist/index.cjs"
      }
    },
    "./utils": {
      "import": "./dist/utils.js",
      "require": "./dist/utils.cjs"
    }
  },

  "files": ["dist", "README.md", "LICENSE"],

  "scripts": {
    "build": "tsup",
    "test": "vitest run",
    "prepublishOnly": "npm run build && npm run test"
  },

  "engines": {
    "node": ">=18"
  },

  "sideEffects": false,

  "devDependencies": {
    "tsup": "^8.0.0",
    "typescript": "^5.5.0",
    "vitest": "^2.0.0"
  }
}
```

各字段说明：

| 字段 | 作用 | 必要性 |
|---|---|---|
| `name` | 包名（@scope/name 或 name） | ✅ 必需 |
| `version` | 版本号（SemVer） | ✅ 必需 |
| `type` | `"module"` = ESM，不写 = CJS | 推荐 |
| `main` | CJS 入口（`require()` 用） | 兼容旧环境 |
| `module` | ESM 入口（打包工具用） | 推荐 |
| `types` | TypeScript 类型声明入口 | TS 包必需 |
| `exports` | **现代入口映射**（优先级最高） | ✅ 推荐 |
| `files` | 发布到 npm 的文件白名单 | ✅ 推荐 |
| `sideEffects` | 告诉打包工具可以 Tree-Shaking | 推荐 |
| `engines` | 声明支持的 Node.js 版本 | 推荐 |

> 💡 **`exports` 是 2024+ 的标准**。它比 main/module 更精确，支持条件导出（import/require/node/browser）。优先用 exports。

### 1.3 语义化版本（SemVer）

```
版本号格式：MAJOR.MINOR.PATCH

  1.0.0 → 1.0.1  PATCH：修复 Bug（向后兼容）
  1.0.0 → 1.1.0  MINOR：新增功能（向后兼容）
  1.0.0 → 2.0.0  MAJOR：破坏性变更（不兼容）

  特殊版本：
  0.x.x          → 开发阶段，API 可能随时变
  1.0.0-beta.1   → 预发布版本
  1.0.0-rc.1     → 候选发布版本

  依赖版本范围：
  "^1.2.3" → >=1.2.3 <2.0.0   （锁定 MAJOR）← 最常用
  "~1.2.3" → >=1.2.3 <1.3.0   （锁定 MINOR）
  "1.2.3"  → 精确版本
```

---

## 2. 项目初始化与 TypeScript 配置

### 2.1 项目结构设计

```bash
mkdir my-utils && cd my-utils
npm init -y
git init
```

推荐目录结构：

```
my-utils/
├── src/                  # 源码
│   ├── index.ts          # 主入口
│   ├── string.ts         # 字符串工具
│   └── array.ts          # 数组工具
├── tests/                # 测试
│   ├── string.test.ts
│   └── array.test.ts
├── dist/                 # 构建输出（gitignore）
├── package.json
├── tsconfig.json
├── tsup.config.ts        # 构建配置
├── vitest.config.ts      # 测试配置
├── .gitignore
├── .npmignore            # 或用 files 字段
├── LICENSE
├── README.md
└── CHANGELOG.md
```

`.gitignore`：

```
node_modules/
dist/
coverage/
*.tgz
.DS_Store
```

### 2.2 TypeScript 配置：面向库开发的 tsconfig

```bash
npm install -D typescript
```

```json
// tsconfig.json
{
  "compilerOptions": {
    // 输出
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "declaration": true,           // 生成 .d.ts
    "declarationMap": true,        // .d.ts 的 source map

    // 严格模式
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,

    // 路径
    "outDir": "./dist",
    "rootDir": "./src",

    // 兼容性
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,

    // 库开发特有
    "isolatedModules": true,       // 兼容 tsup/esbuild
    "verbatimModuleSyntax": true,  // 强制 type-only import
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

> 💡 **库 vs 应用的 tsconfig 差异**：库必须开 `declaration: true` 生成类型声明；`moduleResolution: "bundler"` 适合用构建工具（tsup/vite）的场景。

### 2.3 ESM 与 CJS 双格式输出

```
为什么需要双格式？

  用户 A：import { foo } from 'my-utils'  → 需要 ESM (.js/.mjs)
  用户 B：const { foo } = require('my-utils')  → 需要 CJS (.cjs)
  用户 C：TypeScript 项目  → 还需要 .d.ts 类型声明

  你的包需要同时提供三种文件：
  dist/
  ├── index.js      ← ESM
  ├── index.cjs     ← CJS
  ├── index.d.ts    ← 类型声明（ESM）
  └── index.d.cts   ← 类型声明（CJS）
```

package.json 中配置：

```json
{
  "type": "module",
  "exports": {
    ".": {
      "import": {
        "types": "./dist/index.d.ts",
        "default": "./dist/index.js"
      },
      "require": {
        "types": "./dist/index.d.cts",
        "default": "./dist/index.cjs"
      }
    }
  }
}
```

> ⚠️ **types 必须放在 default 前面**！Node.js 按顺序匹配条件，TypeScript 需要先找到类型。

---

## 3. 构建工具：tsup 实战

### 3.1 为什么需要构建工具

```
直接发布 .ts 源码？不行！

  1. 用户必须有 TypeScript → 增加依赖
  2. 用户的 tsconfig 可能和你不兼容
  3. 无法同时输出 ESM + CJS
  4. 无法 Tree-Shaking

  正确做法：
  src/*.ts → 构建工具 → dist/*.js + dist/*.d.ts
  发布 dist/，不发布 src/
```

### 3.2 tsup 配置详解

```bash
npm install -D tsup
```

```typescript
// tsup.config.ts
import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts'],       // 入口
  format: ['esm', 'cjs'],       // 同时输出 ESM 和 CJS
  dts: true,                    // 生成类型声明 .d.ts
  splitting: false,             // 不拆分代码（库通常不需要）
  sourcemap: true,              // 生成 source map
  clean: true,                  // 构建前清空 dist/
  treeshake: true,              // Tree-Shaking
  minify: false,                // 库不压缩（让用户的打包工具处理）

  // 外部依赖（不打包进产物）
  external: ['lodash'],

  // 目标环境
  target: 'node18',

  // 多入口
  // entry: ['src/index.ts', 'src/utils.ts'],
});
```

```bash
# 构建
npx tsup

# 输出：
# dist/index.js      (ESM)
# dist/index.cjs     (CJS)
# dist/index.d.ts    (类型声明)
# dist/index.d.cts   (CJS 类型声明)
```

在 package.json 中添加脚本：

```json
{
  "scripts": {
    "build": "tsup",
    "dev": "tsup --watch"
  }
}
```

### 3.3 构建工具对比：tsup vs tsc vs rollup vs unbuild

| | tsup | tsc | rollup | unbuild |
|---|---|---|---|---|
| **底层** | esbuild | TypeScript | rollup | rollup + esbuild |
| **速度** | ⚡ 极快 | 🐌 慢 | 中 | 快 |
| **ESM+CJS** | ✅ 一键 | 需两次构建 | ✅ 配置复杂 | ✅ 一键 |
| **dts 生成** | ✅ 内置 | ✅ 原生 | 需插件 | ✅ 内置 |
| **配置量** | 极少 | 中 | 多 | 少 |
| **Tree-Shaking** | ✅ | ❌ | ✅ | ✅ |
| **推荐** | 大部分库 ✅ | 简单项目 | 需要高度定制 | Nuxt 生态 |

> 💡 **推荐 tsup**：零配置起步、esbuild 极速构建、ESM/CJS/dts 一键输出。90% 的库用 tsup 就够了。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| exports 字段 | 现代入口映射，优先级最高，types 放在 default 前 |
| SemVer | MAJOR.MINOR.PATCH，^锁大版本 |
| tsconfig | `declaration: true` + `verbatimModuleSyntax` |
| 双格式 | ESM (.js) + CJS (.cjs) + 类型 (.d.ts) |
| tsup | esbuild 底层，一键 ESM/CJS/dts，推荐首选 |

> **下一章**：Vitest 单元测试——配置、Mock、覆盖率与 CI 集成。

---

## 4. 测试：Vitest 单元测试

### 4.1 Vitest 配置与基础用法

```bash
npm install -D vitest
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,            // 全局 describe/it/expect
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.ts'],
      exclude: ['src/index.ts'],  // 入口通常只是 re-export
    },
  },
});
```

编写测试：

```typescript
// src/string.ts
export function capitalize(str: string): string {
  if (!str) return '';
  return str[0].toUpperCase() + str.slice(1);
}

export function slugify(str: string): string {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, '-');
}
```

```typescript
// tests/string.test.ts
import { describe, it, expect } from 'vitest';
import { capitalize, slugify } from '../src/string';

describe('capitalize', () => {
  it('应该将首字母大写', () => {
    expect(capitalize('hello')).toBe('Hello');
  });

  it('空字符串返回空', () => {
    expect(capitalize('')).toBe('');
  });

  it('已经大写的不变', () => {
    expect(capitalize('Hello')).toBe('Hello');
  });
});

describe('slugify', () => {
  it('空格转连字符', () => {
    expect(slugify('Hello World')).toBe('hello-world');
  });

  it('去除特殊字符', () => {
    expect(slugify('Hello, World!')).toBe('hello-world');
  });
});
```

```bash
# 运行测试
npx vitest run          # 单次运行
npx vitest              # watch 模式
npx vitest run --reporter=verbose   # 详细输出
```

### 4.2 测试技巧：Mock、类型测试、边界用例

```typescript
// Mock 外部依赖
import { describe, it, expect, vi } from 'vitest';

// Mock 整个模块
vi.mock('node:fs', () => ({
  readFileSync: vi.fn().mockReturnValue('mock content'),
}));

// Mock 单个函数
const mockFetch = vi.fn().mockResolvedValue({
  json: () => Promise.resolve({ data: 'test' }),
});

// 类型测试（确保类型推断正确）
import { expectTypeOf } from 'vitest';

it('返回类型正确', () => {
  expectTypeOf(capitalize('hello')).toBeString();
  expectTypeOf(slugify).parameter(0).toBeString();
});
```

### 4.3 覆盖率与 CI 集成

```bash
# 生成覆盖率报告
npx vitest run --coverage
```

```json
// package.json scripts
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

---

## 5. 文档与 README

### 5.1 README 最佳实践

```markdown
# @yourname/utils

> 一句话描述你的包做什么。

[![npm version](https://img.shields.io/npm/v/@yourname/utils)](https://www.npmjs.com/package/@yourname/utils)
[![CI](https://github.com/yourname/utils/actions/workflows/ci.yml/badge.svg)](https://github.com/yourname/utils/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 安装

npm install @yourname/utils

## 快速开始

import { capitalize, slugify } from '@yourname/utils';

capitalize('hello');      // 'Hello'
slugify('Hello World');   // 'hello-world'

## API

### capitalize(str)

将字符串首字母大写。

| 参数 | 类型 | 说明 |
|------|------|------|
| str | string | 输入字符串 |

**返回值**: string

### slugify(str)

将字符串转为 URL 友好的 slug。

## License

MIT
```

README 必备要素：

| 要素 | 为什么 |
|---|---|
| **包名 + 一句话描述** | 用户 3 秒内判断是否需要 |
| **Badge 徽章** | 版本、CI 状态、许可证 |
| **安装命令** | 复制粘贴即用 |
| **快速开始** | 最少代码展示核心功能 |
| **API 文档** | 参数、返回值、示例 |
| **License** | 法律要求 |

### 5.2 API 文档自动生成

```bash
npm install -D typedoc
```

在源码中写 JSDoc：

```typescript
/**
 * 将字符串首字母大写
 *
 * @param str - 输入字符串
 * @returns 首字母大写的字符串
 *
 * @example
 * ```ts
 * capitalize('hello') // 'Hello'
 * ```
 */
export function capitalize(str: string): string {
  if (!str) return '';
  return str[0].toUpperCase() + str.slice(1);
}
```

```json
{
  "scripts": {
    "docs": "typedoc --out docs src/index.ts"
  }
}
```

### 5.3 示例项目与 Playground

```
my-utils/
├── examples/
│   ├── basic/
│   │   ├── package.json    ← 依赖指向本地包
│   │   └── index.ts
│   └── with-express/
│       ├── package.json
│       └── app.ts
```

```json
// examples/basic/package.json
{
  "dependencies": {
    "@yourname/utils": "file:../../"
  }
}
```

---

## 6. 版本管理：changesets

### 6.1 为什么不手动改版本号

```
手动管理版本的问题：

  1. 忘记改版本号 → 发布了相同版本
  2. 版本号不符合 SemVer → 用户升级爆炸
  3. CHANGELOG 懒得写 → 用户不知道改了什么
  4. 多人协作 → 版本号冲突
  5. Monorepo 多包 → 版本依赖关系混乱

  changesets 的解决方案：
  每个 PR 附带一个 changeset 文件
  → 发布时自动计算版本号 + 生成 CHANGELOG
```

### 6.2 changesets 工作流

```bash
# 安装
npm install -D @changesets/cli
npx changeset init
```

日常开发流程：

```bash
# 1. 开发完功能后，创建 changeset
npx changeset
# 交互式选择：
#   哪些包受影响？→ @yourname/utils
#   版本类型？→ minor（新增功能）
#   描述？→ 新增 slugify 函数

# 生成文件：.changeset/funny-dogs-dance.md
```

```markdown
<!-- .changeset/funny-dogs-dance.md（自动生成） -->
---
"@yourname/utils": minor
---

新增 `slugify` 函数，支持将字符串转为 URL 友好格式。
```

```bash
# 2. 提交 PR（changeset 文件一起提交）
git add .changeset/funny-dogs-dance.md
git commit -m "feat: add slugify function"

# 3. 合并 PR 后，执行版本更新
npx changeset version
# 自动：
#   - 删除 .changeset/funny-dogs-dance.md
#   - 更新 package.json 的 version（1.0.0 → 1.1.0）
#   - 更新 CHANGELOG.md

# 4. 发布
npx changeset publish
# 自动：npm publish + git tag
```

```
changeset 工作流：

  开发 → changeset add → PR 合并
    ↓
  changeset version → 自动算版本 + 更新 CHANGELOG
    ↓
  changeset publish → npm publish + git tag
```

### 6.3 Monorepo 多包版本管理

```
Monorepo 场景：

  packages/
  ├── core/      v1.0.0
  ├── utils/     v2.1.0  → 依赖 core
  └── cli/       v0.5.0  → 依赖 core + utils

  修改 core 时：
  changeset 自动识别 utils 和 cli 也需要更新
  → 级联版本升级
```

```json
// .changeset/config.json
{
  "$schema": "https://unpkg.com/@changesets/config@3.0.0/schema.json",
  "changelog": "@changesets/cli/changelog",
  "commit": false,
  "fixed": [],
  "linked": [utils"]("@yourname/core", "@yourname/utils"),
  "access": "public",
  "baseBranch": "main",
  "updateInternalDependencies": "patch"
}
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Vitest | 配置简单、支持 ESM、类型测试、v8 覆盖率 |
| README | 包名 + 安装 + 快速开始 + API + License |
| typedoc | JSDoc → HTML API 文档 |
| changesets | changeset add → version → publish |
| Monorepo | `linked` 配置级联版本升级 |

> **下一章**：npm publish 全流程与 GitHub Actions 自动发布。

---

## 7. 发布：npm publish 与 CI 自动化

### 7.1 手动发布：npm publish 全流程

```bash
# 1. 确认 npm 登录
npm whoami                    # 查看当前登录用户
npm login                    # 登录（或 npm adduser）

# 2. 构建 + 测试
npm run build
npm run test

# 3. 预检查：看看会发布哪些文件
npm pack --dry-run
# 输出文件列表 + 包大小

# 4. 本地试用（不发布到 npm）
npm pack                     # 生成 yourname-utils-1.0.0.tgz
# 在另一个项目中安装测试：
npm install ../my-utils/yourname-utils-1.0.0.tgz

# 5. 正式发布
npm publish                  # 普通包
npm publish --access public  # @scope 包必须加 --access public
```

```
发布前的 npm pack --dry-run 示例：

  npm notice 📦  @yourname/utils@1.0.0
  npm notice === Tarball Contents ===
  npm notice 1.2kB  dist/index.js
  npm notice 1.0kB  dist/index.cjs
  npm notice 0.5kB  dist/index.d.ts
  npm notice 0.5kB  dist/index.d.cts
  npm notice 2.1kB  README.md
  npm notice 1.1kB  LICENSE
  npm notice 0.8kB  package.json
  npm notice === Tarball Details ===
  npm notice name:    @yourname/utils
  npm notice version: 1.0.0
  npm notice total:   7.2 kB

  ✅ 没有 src/、node_modules/、tests/ → 正确
  ❌ 如果看到 src/ → files 字段配置错误
```

`files` 字段 vs `.npmignore`：

| | files（白名单） | .npmignore（黑名单） |
|---|---|---|
| **推荐** | ✅ 推荐 | ⚠️ 容易遗漏 |
| **原则** | 只发布列出的 | 排除列出的 |
| **配置** | `"files": ["dist"]` | `.npmignore` 文件 |

> 💡 **推荐用 `files` 白名单**。黑名单容易遗漏敏感文件（.env、测试数据）。

### 7.2 GitHub Actions 自动发布

::: v-pre
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: $&#123;&#123; matrix.node-version &#125;&#125;
      - run: npm ci
      - run: npm run build
      - run: npm test
```
:::

::: v-pre
```yaml
# .github/workflows/publish.yml
name: Publish

on:
  push:
    branches: [main]

concurrency: $&#123;&#123; github.workflow &#125;&#125;-$&#123;&#123; github.ref &#125;&#125;

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write
      id-token: write          # npm Provenance
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: 'https://registry.npmjs.org'

      - run: npm ci
      - run: npm run build
      - run: npm test

      # changesets 自动化
      - name: Create Release PR or Publish
        uses: changesets/action@v1
        with:
          publish: npx changeset publish
          version: npx changeset version
          commit: 'chore: release'
          title: 'chore: release'
        env:
          GITHUB_TOKEN: $&#123;&#123; secrets.GITHUB_TOKEN &#125;&#125;
          NPM_TOKEN: $&#123;&#123; secrets.NPM_TOKEN &#125;&#125;
          NODE_AUTH_TOKEN: $&#123;&#123; secrets.NPM_TOKEN &#125;&#125;
```
:::

配置 NPM_TOKEN：

```bash
# 1. 在 npm 网站生成 Access Token
#    npmjs.com → Access Tokens → Generate New Token → Automation

# 2. 添加到 GitHub Secrets
#    仓库 → Settings → Secrets → Actions → New secret
#    Name: NPM_TOKEN
#    Value: npm_xxxxxxxxxxxx
```

### 7.3 发布检查清单与常见问题

**发布前检查清单**：

```
□ package.json version 已更新
□ CHANGELOG.md 已更新
□ npm run build 成功
□ npm test 全部通过
□ npm pack --dry-run 只包含 dist/、README、LICENSE
□ README 的安装命令、API 文档是最新的
□ exports 字段的路径都指向存在的文件
□ TypeScript 类型声明可用（新项目安装后 IDE 有提示）
□ ESM 和 CJS 都能正常导入
```

**常见问题**：

| 问题 | 原因 | 解决 |
|---|---|---|
| 403 Forbidden | @scope 包默认 private | 加 `--access public` |
| 版本已存在 | 忘记更新 version | 改版本号或用 changesets |
| types 找不到 | exports 中 types 顺序不对 | types 放在 default 前面 |
| CJS require 报错 | 没有输出 .cjs 格式 | tsup format 加 'cjs' |
| 包太大 | 打包了 src/tests/node_modules | 检查 files 字段 |

---

## 8. 实战：从零发布一个工具库

### 8.1 需求设计与 API 定义

构建 `@yourname/str-utils`——一个字符串工具库：

```typescript
// 目标 API
import { capitalize, slugify, truncate, camelCase } from '@yourname/str-utils';

capitalize('hello world');          // 'Hello world'
slugify('Hello, World!');           // 'hello-world'
truncate('long text...', 10);       // 'long te...'
camelCase('hello-world');           // 'helloWorld'
```

### 8.2 编码、测试、构建

**初始化**：

```bash
mkdir str-utils && cd str-utils
npm init -y
npm install -D typescript tsup vitest @changesets/cli
npx changeset init
```

**源码**：

```typescript
// src/index.ts
export { capitalize } from './capitalize';
export { slugify } from './slugify';
export { truncate } from './truncate';
export { camelCase } from './camel-case';
```

```typescript
// src/capitalize.ts
export function capitalize(str: string): string {
  if (!str) return '';
  return str[0].toUpperCase() + str.slice(1);
}
```

```typescript
// src/slugify.ts
export function slugify(str: string): string {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/-+/g, '-');
}
```

```typescript
// src/truncate.ts
export function truncate(str: string, maxLength: number, suffix = '...'): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - suffix.length) + suffix;
}
```

```typescript
// src/camel-case.ts
export function camelCase(str: string): string {
  return str
    .replace(/[-_\s]+(.)?/g, (_, c) => (c ? c.toUpperCase() : ''))
    .replace(/^[A-Z]/, (c) => c.toLowerCase());
}
```

**测试**：

```typescript
// tests/index.test.ts
import { describe, it, expect } from 'vitest';
import { capitalize, slugify, truncate, camelCase } from '../src';

describe('capitalize', () => {
  it('首字母大写', () => expect(capitalize('hello')).toBe('Hello'));
  it('空字符串', () => expect(capitalize('')).toBe(''));
});

describe('slugify', () => {
  it('基本转换', () => expect(slugify('Hello World')).toBe('hello-world'));
  it('特殊字符', () => expect(slugify('a & b')).toBe('a--b'));
});

describe('truncate', () => {
  it('不需要截断', () => expect(truncate('hi', 10)).toBe('hi'));
  it('需要截断', () => expect(truncate('hello world', 8)).toBe('hello...'));
  it('自定义后缀', () => expect(truncate('hello world', 8, '…')).toBe('hello w…'));
});

describe('camelCase', () => {
  it('连字符', () => expect(camelCase('hello-world')).toBe('helloWorld'));
  it('下划线', () => expect(camelCase('hello_world')).toBe('helloWorld'));
  it('空格', () => expect(camelCase('hello world')).toBe('helloWorld'));
});
```

**配置文件**：

```typescript
// tsup.config.ts
import { defineConfig } from 'tsup';
export default defineConfig({
  entry: ['src/index.ts'],
  format: ['esm', 'cjs'],
  dts: true,
  clean: true,
  sourcemap: true,
  treeshake: true,
});
```

```json
// package.json（关键字段）
{
  "name": "@yourname/str-utils",
  "version": "0.0.0",
  "type": "module",
  "exports": {
    ".": {
      "import": { "types": "./dist/index.d.ts", "default": "./dist/index.js" },
      "require": { "types": "./dist/index.d.cts", "default": "./dist/index.cjs" }
    }
  },
  "files": ["dist"],
  "scripts": {
    "build": "tsup",
    "test": "vitest run",
    "prepublishOnly": "npm run build && npm run test"
  }
}
```

### 8.3 发布与迭代

```bash
# 构建 + 测试
npm run build
npm test

# 预检查
npm pack --dry-run

# 创建 changeset
npx changeset
# → 选择 minor → "Initial release with capitalize, slugify, truncate, camelCase"

# 更新版本
npx changeset version
# → package.json: 0.0.0 → 0.1.0
# → CHANGELOG.md 自动生成

# 发布！
npm publish --access public

# 验证
npm info @yourname/str-utils
```

```
完整的迭代循环：

  1. 写代码 + 写测试
  2. npx changeset（描述变更）
  3. git commit + push + PR
  4. CI 自动测试
  5. 合并 PR
  6. changesets/action 自动创建 Release PR
  7. 合并 Release PR → 自动 npm publish
  
  之后每次迭代重复 1-7
```

---

## 全书总结

```
┌─────────────────────────────────────────────────────────────┐
│        Node.js 包开发与发布 · 知识地图                        │
│                                                              │
│  Ch.1  package.json   exports / SemVer / files 白名单        │
│  Ch.2  TypeScript     tsconfig / ESM+CJS 双格式              │
│  Ch.3  tsup 构建      一键 ESM/CJS/dts / 工具对比            │
│  Ch.4  Vitest 测试    单测 / Mock / 类型测试 / 覆盖率        │
│  Ch.5  文档           README 模板 / typedoc / 示例项目        │
│  Ch.6  changesets     自动版本号 / CHANGELOG / Monorepo       │
│  Ch.7  发布           npm publish / GitHub Actions / CI       │
│  Ch.8  完整实战       str-utils 从零到 npm 上架               │
│                                                              │
│  8 章 24 节，掌握专业 npm 包的完整开发与发布流程。            │
└─────────────────────────────────────────────────────────────┘
```

> 🎉 **核心流程**：TypeScript 写码 → tsup 构建 → Vitest 测试 → changesets 版本 → GitHub Actions 发布。
