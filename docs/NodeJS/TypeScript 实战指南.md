# TypeScript 实战指南

> 从 JavaScript 的"类型裸奔"到 TypeScript 的"类型护甲"——本教程面向有 Python/JavaScript 基础的开发者，从零构建类型思维，一路打通基础类型、泛型、类型体操、声明文件到工程化配置，用真实代码而非抽象理论，让类型系统成为你最好的"编译期 Code Review"。

---

## 1. 为什么需要 TypeScript

"JavaScript 写起来很爽，直到项目大了你开始怀疑人生。" —— 这句话几乎是所有中大型 JS 项目的真实写照。TypeScript 的出现，不是要替代 JavaScript，而是在它上面加一层**编译期的类型护甲**。

### 1.1 JavaScript 的类型"惊喜"

JavaScript 是动态弱类型语言——变量没有固定类型，运算时还会自动做隐式转换。这带来了灵活性，也带来了"惊喜"：

```javascript
// 惊喜 1：隐式类型转换
console.log("5" - 3);       // → 2（字符串变数字）
console.log("5" + 3);       // → "53"（数字变字符串）
console.log(true + true);   // → 2（布尔变数字）
console.log([] + {});       // → "[object Object]"（？？？）

// 惊喜 2：参数传错了，运行时才炸
function getUser(id) {
  return fetch(`/api/users/${id}`);
}
getUser({ userId: 123 });  // 不报错！请求了 /api/users/[object Object]

// 惊喜 3：属性名拼错了，undefined 静悄悄
const config = { timeout: 3000, retries: 3 };
console.log(config.timout);  // → undefined（少了个 e，没有任何报错）

// 惊喜 4：重构恐惧
// 你把 user.name 改成了 user.fullName
// 然后在 47 个文件中搜索替换 .name
// 然后发现还有 10 个动态属性访问 user[key] 漏了
// 然后线上炸了
```

```
JavaScript 类型问题的三大痛点：

  痛点 1：运行时才报错
  ──────────────────
  → 写的时候没提示，部署后才发现 undefined is not a function
  → 测试覆盖不到的路径 = 定时炸弹

  痛点 2：IDE 无法帮你
  ──────────────────
  → 函数参数是什么？返回什么？—— 不知道
  → 对象有哪些属性？—— 猜
  → 自动补全？—— 半猜半蒙

  痛点 3：重构 = 赌博
  ──────────────────
  → 改个字段名、拆个函数 → 全局搜索替换 → 祈祷没漏
  → 项目越大，重构越怕 → 最终不敢改 → 代码腐烂
```

### 1.2 TypeScript = JavaScript + 编译期类型检查

TypeScript 的本质很简单：**JavaScript + 类型注解 + 编译器检查**。它不是一门新语言，而是 JavaScript 的超集——所有合法的 JS 代码都是合法的 TS 代码。

```typescript
// TypeScript 在编译期就拦住问题

// ✅ 隐式转换？编译器直接报错
const result: number = "5" - 3;
//                     ~~~ 错误：不能将类型 string 分配给类型 number

// ✅ 参数类型不对？写的时候就知道
function getUser(id: number): Promise<User> {
  return fetch(`/api/users/${id}`);
}
getUser({ userId: 123 });
//      ~~~~~~~~~~~~~~~~~
//      错误：类型 { userId: number } 不能分配给类型 number

// ✅ 属性名拼错？红色波浪线伺候
const config = { timeout: 3000, retries: 3 };
console.log(config.timout);
//                 ~~~~~~ 错误：属性 timout 不存在，你是不是想写 timeout？

// ✅ 重构？F2 一键重命名，编译器保证全量替换
// → 改 user.name 为 user.fullName
// → 编译器自动标红所有引用 → 零遗漏
```

```
TypeScript 的核心价值：

  价值 1：编译期类型检查
  ──────────────────
  → 错误从"运行时才发现"提前到"写代码时就发现"
  → 相当于免费的、永远在线的 Code Reviewer

  价值 2：IDE 智能提示
  ──────────────────
  → 参数类型、返回值、对象属性 → 全部自动补全
  → Ctrl+Space 按下去，所有可选项清清楚楚
  → 文档写在类型里，不需要翻文档

  价值 3：重构信心
  ──────────────────
  → 改名、提取、内联 → 编译器保证不遗漏
  → "改了之后能不能跑"从赌博变成确定性事件
  → 代码越改越好，而不是越改越怕

  价值 4：团队协作
  ──────────────────
  → 类型 = 代码级别的接口文档
  → 新人看类型就知道怎么用，不需要问人
  → "这个函数接收什么参数"→ 看类型签名就行
```

```
TypeScript 的工作原理：

  你写的代码（.ts）        编译器（tsc）         运行时（Node.js / 浏览器）
  ┌────────────────┐     ┌──────────────┐     ┌──────────────────┐
  │ const x: number│     │ 类型检查 ✓    │     │ const x = 42;    │
  │   = 42;        │ ──▶ │ 擦除类型注解  │ ──▶ │                  │
  │ const y: string│     │ 输出 .js 文件 │     │ const y = "hi";  │
  │   = "hi";      │     │              │     │                  │
  └────────────────┘     └──────────────┘     └──────────────────┘
                              │
                         ❌ 类型错误？
                         → 编译失败，不会生成 .js
                         → 错误在这里就被拦住

  关键理解：
  → 类型注解在编译后被完全擦除，运行时无任何性能开销
  → TypeScript 不改变 JavaScript 的运行时行为
  → 它只是一个"超强的 Linter"，帮你在写代码时找 Bug
```

### 1.3 与 Python 类型系统的对照

如果你是 Python 开发者，好消息是——Python 3.5+ 也有类型注解（Type Hints）。坏消息是——两套系统的设计哲学完全不同：

```
TypeScript vs Python 类型系统对照表：

  维度              TypeScript                    Python (typing)
  ───────────────────────────────────────────────────────────────────
  定位              编译期强制检查                  运行时可选提示
  检查时机          编译时（tsc）                   需要额外工具（mypy/pyright）
  不写类型          仍然有类型推断兜底              完全无约束
  类型擦除          ✅ 编译后擦除                   ✅ 运行时忽略
  泛型语法          <T>                            [T]（Python 3.12+）
  联合类型          string | number                str | int（Python 3.10+）
  空安全            strictNullChecks               Optional[T] / T | None
  工具类型          Partial/Pick/Omit 等            无内置，需手写
  装饰器            TC39 Stage 3                   原生支持
  社区类型          @types/xxx                     typeshed / py.typed
  主流态度          "不用 TS = 裸奔"               "用不用看心情"
```

```typescript
// TypeScript 的类型注解
function greet(name: string, age: number): string {
  return `Hello, ${name}! You are ${age} years old.`;
}

greet("Alice", 30);     // ✅
greet("Alice", "30");   // ❌ 编译报错：string 不能赋值给 number
```

```python
# Python 的类型注解（Type Hints）
def greet(name: str, age: int) -> str:
    return f"Hello, {name}! You are {age} years old."

greet("Alice", 30)      # ✅
greet("Alice", "30")    # ⚠️ Python 解释器不报错！正常运行！
                        # 只有 mypy/pyright 静态检查才会标记
```

```
关键差异总结：

  TypeScript：编译器是"门卫"
  ──────────────────────────
  → 类型错误 = 编译失败 = 代码跑不起来
  → 你不得不修复类型错误
  → 团队中每个人都必须遵守类型约束

  Python：类型注解是"建议"
  ──────────────────────────
  → 类型错误？解释器完全不管
  → 需要额外运行 mypy/pyright 才能检查
  → CI 里没配 mypy？等于没有类型检查
  → 团队成员可以选择性忽略

  对 Python 开发者的建议：
  ──────────────────────────
  → 把 TypeScript 的类型想成"有牙齿的 mypy"
  → 不是建议，是强制
  → 写法几乎一样（function(x: Type)），但检查是真的
```
### 1.4 值空间与类型空间：两个平行世界

理解 TypeScript 最重要的心智模型：**你的代码同时存在于两个平行世界**——值空间（Value Space）和类型空间（Type Space）。

```typescript
// 值空间：运行时存在的东西（变量、函数、对象）
const name = "Alice";            // 值
function add(a: number, b: number) { return a + b; }  // 值（函数）
class User { name = ""; }       // 值（构造函数）+ 类型（同时存在于两个空间！）

// 类型空间：编译期存在的东西（类型注解、接口、类型别名）
type Name = string;              // 类型（编译后消失）
interface IUser { name: string } // 类型（编译后消失）
type Status = "active" | "inactive"; // 类型（编译后消失）

// 编译后的 JavaScript（类型空间全部被擦除）：
// const name = "Alice";
// function add(a, b) { return a + b; }
// class User { name = ""; }
// → type、interface 全部消失了！
```

```
值空间 vs 类型空间：

  ┌──────────────────────────────────────────────────┐
  │                  TypeScript 源码                   │
  │                                                    │
  │  值空间（运行时存在）     类型空间（编译期存在）      │
  │  ─────────────────     ─────────────────          │
  │  const x = 42          type X = number            │
  │  function fn() {}      interface IFn {}            │
  │  class User {}         type Status = "ok"|"err"   │
  │  enum Color {}         type Color = ...           │
  │       │                       │                    │
  │       │    class / enum       │                    │
  │       │◄──── 同时存在 ──────►│                    │
  │       │    于两个空间         │                    │
  │       │                       │                    │
  │       ▼                       ▼                    │
  │  编译后保留              编译后擦除                 │
  └──────────────────────────────────────────────────┘

  跨界选手（同时存在于两个空间）：
  → class   → 值空间是构造函数，类型空间是实例类型
  → enum    → 值空间是对象，类型空间是联合类型
  → namespace → 值空间是对象，类型空间是类型命名空间
```

```typescript
// "类型是集合" —— 理解 TypeScript 类型系统的第二个关键心智模型

// string 是所有字符串值的集合
// number 是所有数字值的集合
// "hello" 是只包含 "hello" 这一个值的集合（字面量类型）

// 联合类型 = 集合的并集
type StringOrNumber = string | number;
// → 包含所有 string 值 + 所有 number 值

// 交叉类型 = 集合的交集
type Named = { name: string };
type Aged = { age: number };
type Person = Named & Aged;
// → 同时满足 Named 和 Aged 的值的集合
// → 即 { name: string; age: number }

// never = 空集（没有任何值属于这个类型）
type Impossible = string & number;  // → never
// → 一个值不可能同时是 string 又是 number

// unknown = 全集（所有值都属于这个类型）
let x: unknown = 42;       // ✅
x = "hello";               // ✅
x = { a: 1 };              // ✅
// → unknown 包含一切值，但你不能直接用它（需要先收窄）

// 类型兼容性 = 子集关系
type A = "hello";           // { "hello" }
type B = string;            // { 所有字符串 }
// A 是 B 的子集 → A 可以赋值给 B
const a: A = "hello";
const b: B = a;             // ✅ 子集可以赋值给父集
```

> 💡 **建立"类型是集合"的心智模型**后，你会发现 TypeScript 的很多行为都变得直觉化了：`extends` 是"子集"、`never` 是"空集"、`unknown` 是"全集"、联合是"并集"、交叉是"交集"。后面的泛型和类型体操章节会反复用到这个思路。

---

## 2. 环境搭建与 tsconfig 配置

工欲善其事，必先利其器。TypeScript 的开发体验好不好，80% 取决于 tsconfig 配得对不对。这一章从零搭建 TS 项目，把 tsconfig 的核心配置吃透。

### 2.1 安装与第一个 .ts 文件

```bash
# 前提：安装 Node.js 18+（推荐用 nvm 管理版本）
node -v   # → v22.x.x

# 创建项目
mkdir ts-playground && cd ts-playground
npm init -y

# 安装 TypeScript（项目级别，不推荐全局安装）
npm i typescript -D

# 初始化 tsconfig.json
npx tsc --init
# → 生成 tsconfig.json，包含所有配置项（大部分被注释掉了）

# 安装开发工具（三选一，后面详解）
npm i tsx -D          # 推荐：零配置直接运行 .ts
# npm i ts-node -D   # 老牌方案，需要额外配置
# npx tsc            # 编译成 .js 再用 node 运行
```

```typescript
// src/hello.ts —— 你的第一个 TypeScript 文件

interface User {
  name: string;
  age: number;
  email?: string;       // ? 表示可选属性
}

function greet(user: User): string {
  const emailInfo = user.email ? ` (${user.email})` : "";
  return `Hello, ${user.name}${emailInfo}! You are ${user.age}.`;
}

const alice: User = { name: "Alice", age: 30, email: "alice@example.com" };
const bob: User = { name: "Bob", age: 25 };

console.log(greet(alice));  // → Hello, Alice (alice@example.com)! You are 30.
console.log(greet(bob));    // → Hello, Bob! You are 25.

// 试试传错参数——编译器立刻报错：
// greet({ name: "Charlie" });
// → 错误：缺少属性 age
```

```
三种运行 .ts 文件的方式：

  方式 1：tsx（推荐日常开发）
  ──────────────────────────
  npx tsx src/hello.ts
  → 零配置、速度快（基于 esbuild）
  → 支持 ESM 和 CJS
  → 支持 watch 模式：npx tsx watch src/hello.ts

  方式 2：tsc 编译 → node 运行
  ──────────────────────────
  npx tsc                    # 编译所有 .ts → .js
  node dist/hello.js         # 运行编译后的 JS
  → 适合生产构建、CI/CD
  → 能看到编译后的 JS 长什么样

  方式 3：ts-node
  ──────────────────────────
  npx ts-node src/hello.ts
  → 老牌方案，社区成熟
  → 速度较慢（每次都完整编译）
  → ESM 支持需要额外配置

  推荐策略：
  → 日常开发用 tsx（快、省心）
  → 生产构建用 tsc（严格检查 + 输出 .js）
  → 调试类型问题用 tsc --noEmit（只检查不输出）
```

```json
// package.json 推荐 scripts
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "typecheck": "tsc --noEmit"
  }
}
```

### 2.2 tsconfig.json 核心配置详解

tsconfig.json 有 100+ 个配置项，但日常只需要关注 20 个左右。按功能分组理解：

```json
// tsconfig.json —— 核心配置分组详解
{
  "compilerOptions": {

    // ═══════════════════════════════════════
    // 第 1 组：编译目标
    // ═══════════════════════════════════════
    "target": "ES2022",
    // → 编译输出的 JS 版本
    // → ES2022 支持 top-level await、private fields 等
    // → Node.js 18+ 完全支持 ES2022

    "module": "NodeNext",
    // → 模块系统
    // → NodeNext = 让 Node.js 自己决定 ESM 还是 CJS
    // → 其他选项：ESNext（纯 ESM）、CommonJS（纯 CJS）

    "moduleResolution": "NodeNext",
    // → 模块解析策略（怎么找到 import 的文件）
    // → 必须和 module 配套：NodeNext ↔ NodeNext

    "lib": ["ES2022"],
    // → 包含哪些内置类型声明
    // → ES2022 = Promise、Map、Set 等
    // → 前端项目加上 "DOM"：["ES2022", "DOM"]

    // ═══════════════════════════════════════
    // 第 2 组：严格模式（强烈建议全开）
    // ═══════════════════════════════════════
    "strict": true,
    // → 一键开启所有严格检查，等价于：
    // "strictNullChecks": true,       → null/undefined 必须显式处理
    // "noImplicitAny": true,          → 不允许隐式 any
    // "strictFunctionTypes": true,    → 函数参数类型严格检查
    // "strictPropertyInitialization": true,  → 类属性必须初始化
    // "noImplicitThis": true,         → this 必须有明确类型
    // "alwaysStrict": true,           → 输出 "use strict"
    // "strictBindCallApply": true,    → bind/call/apply 参数检查

    // 额外推荐开启的检查：
    "noUncheckedIndexedAccess": true,
    // → obj["key"] 返回 T | undefined 而不是 T
    // → 防止数组越界访问不报错

    "noUnusedLocals": true,
    // → 未使用的局部变量报错

    "noUnusedParameters": true,
    // → 未使用的函数参数报错（用 _ 前缀忽略）

    // ═══════════════════════════════════════
    // 第 3 组：输出控制
    // ═══════════════════════════════════════
    "outDir": "./dist",
    // → 编译输出目录

    "rootDir": "./src",
    // → 源码根目录（影响输出目录结构）

    "declaration": true,
    // → 生成 .d.ts 类型声明文件（发布 npm 包必需）

    "sourceMap": true,
    // → 生成 .js.map（调试时映射回 .ts 源码）

    "skipLibCheck": true,
    // → 跳过 node_modules 中 .d.ts 的类型检查
    // → 大幅加速编译，几乎所有项目都应该开

    // ═══════════════════════════════════════
    // 第 4 组：路径与互操作
    // ═══════════════════════════════════════
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    },
    // → 路径别名：import { foo } from "@/utils/foo"
    // → 注意：运行时还需要 tsconfig-paths 或打包器支持

    "esModuleInterop": true,
    // → 允许 import fs from "fs"（而不是 import * as fs）
    // → 处理 CJS/ESM 互操作问题

    "resolveJsonModule": true,
    // → 允许 import config from "./config.json"

    "forceConsistentCasingInFileNames": true
    // → 强制文件名大小写一致（macOS 不区分，Linux 区分）
  },

  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

```
tsconfig 配置的心智模型：

  ┌──────────────────────────────────────────────┐
  │                tsconfig.json                   │
  │                                                │
  │  编译目标 ──→ "你要输出什么版本的 JS？"          │
  │  target / module / moduleResolution / lib      │
  │                                                │
  │  严格模式 ──→ "你要多严格的类型检查？"           │
  │  strict / noUncheckedIndexedAccess             │
  │                                                │
  │  输出控制 ──→ "编译结果放哪里？生成什么？"       │
  │  outDir / rootDir / declaration / sourceMap     │
  │                                                │
  │  路径互操作 ──→ "怎么找模块？怎么兼容？"         │
  │  paths / esModuleInterop / resolveJsonModule   │
  │                                                │
  │  文件范围 ──→ "编译哪些文件？"                   │
  │  include / exclude                             │
  └──────────────────────────────────────────────┘

  原则：strict 全开 + skipLibCheck 开 + 其余按场景选
```
### 2.3 三种典型配置模板

不同场景的 tsconfig 差异主要在 `target`、`module` 和 `lib` 三个配置上。以下是三种拿来即用的模板：

```json
// 模板 1：Node.js 后端项目
// 场景：Express / Fastify / NestJS 等服务端项目
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "declaration": true,
    "sourceMap": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

```json
// 模板 2：React / Next.js 前端项目
// 场景：Vite + React、Next.js App Router
// 注意：通常 Vite/Next.js 自带配置，你只需微调
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "isolatedModules": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
// → noEmit: true → 不输出 JS（交给 Vite / Next.js 的打包器处理）
// → jsx: "react-jsx" → 支持 JSX，不需要 import React
// → moduleResolution: "Bundler" → 适配 Vite/Webpack 的模块解析
```

```json
// 模板 3：npm 库开发
// 场景：发布到 npm 的工具库 / SDK
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
// → target: ES2020 → 兼容更多使用方
// → declaration + declarationMap → 使用方能跳转到你的源码
// → 通常配合 tsup/unbuild 打包，同时输出 ESM + CJS
```

```
三种模板的关键差异：

  配置项              Node.js 后端     React 前端      npm 库
  ─────────────────────────────────────────────────────────
  target              ES2022          ES2022         ES2020
  module              NodeNext        ESNext         ESNext
  moduleResolution    NodeNext        Bundler        Bundler
  lib                 ES2022          ES2022+DOM     ES2020
  jsx                 无              react-jsx      看情况
  noEmit              false           true           false
  declaration         可选            不需要          必须
  outDir              ./dist          不需要          ./dist
```
### 2.4 开发工具链：ESLint + Prettier + VS Code

TypeScript 编译器只管类型检查，代码风格和最佳实践需要 ESLint + Prettier 搭档。

```bash
# 安装 ESLint v9+（Flat Config）+ TypeScript 支持
npm i eslint @eslint/js typescript-eslint -D

# 安装 Prettier + ESLint 集成
npm i prettier eslint-config-prettier eslint-plugin-prettier -D
```

```javascript
// eslint.config.mjs —— ESLint v9 Flat Config
import eslint from "@eslint/js";
import tseslint from "typescript-eslint";
import prettier from "eslint-config-prettier";

export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  prettier,  // 关闭与 Prettier 冲突的 ESLint 规则
  {
    files: ["**/*.ts"],
    rules: {
      // TypeScript 特有规则
      "@typescript-eslint/no-unused-vars": ["error", {
        argsIgnorePattern: "^_",          // 允许 _arg 形式的未使用参数
        varsIgnorePattern: "^_",
      }],
      "@typescript-eslint/no-explicit-any": "warn",   // any 警告而非报错
      "@typescript-eslint/explicit-function-return-type": "off", // 不强制返回类型
      "@typescript-eslint/consistent-type-imports": "error",     // 强制 import type
      // → import type { User } from "./types"
      // → 而不是 import { User } from "./types"
      // → 确保类型导入在编译后被完全擦除
    },
  },
  {
    ignores: ["dist/", "node_modules/"],
  },
);
```

```json
// .prettierrc —— Prettier 配置
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 100,
  "arrowParens": "always"
}
```

```json
// .vscode/settings.json —— VS Code 推荐配置
{
  // 保存时自动格式化 + 修复
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  },

  // TypeScript 增强
  "typescript.preferences.importModuleSpecifier": "relative",
  "typescript.suggest.autoImports": true,
  "typescript.updateImportsOnFileMove.enabled": "always",

  // 推荐扩展
  // → ESLint (dbaeumer.vscode-eslint)
  // → Prettier (esbenp.prettier-vscode)
  // → Pretty TypeScript Errors (yoavbls.pretty-ts-errors)
  //   → 把 TS 错误信息格式化成可读的样子，强烈推荐！
}
```

```
完整工具链的协作关系：

  你写代码（.ts）
       │
       ├──▶ TypeScript 编译器（tsc）
       │    → 类型检查：参数对不对？返回值对不对？
       │    → 编译输出：.ts → .js
       │
       ├──▶ ESLint + typescript-eslint
       │    → 代码质量：未使用变量？any 滥用？
       │    → 最佳实践：consistent-type-imports 等
       │
       ├──▶ Prettier
       │    → 代码格式：缩进、引号、分号、换行
       │    → 团队统一，不争论风格
       │
       └──▶ VS Code
            → 实时反馈：红色波浪线（TS 错误）
            → 自动修复：保存时 ESLint fix + Prettier format
            → 智能提示：参数补全、类型推断、跳转定义

  → 三者分工明确：TS 管类型，ESLint 管质量，Prettier 管格式
  → VS Code 把三者整合成无缝体验
```

> 💡 **一个常见误区**：把 ESLint 配成同时检查格式 + 质量。现代方案是 ESLint 只管代码质量，格式交给 Prettier。用 `eslint-config-prettier` 关闭 ESLint 中与 Prettier 冲突的规则，两者各司其职。

---

## 3. 基础类型系统

TypeScript 的类型系统建立在 JavaScript 的 7 种原始类型之上，然后扩展出字面量类型、联合/交叉类型、元组、枚举等强大工具。这一章把基础打牢——后面的泛型和类型体操全靠这些积木。

### 3.1 原始类型与字面量类型

```typescript
// ═══════════════════════════════════════
// 7 种原始类型（Primitive Types）
// ═══════════════════════════════════════

const name: string = "Alice";
const age: number = 30;               // 整数和浮点数都是 number
const isActive: boolean = true;
const nothing: null = null;
const notDefined: undefined = undefined;
const id: symbol = Symbol("id");
const bigNum: bigint = 9007199254740991n;  // 超大整数

// 实际开发中，大部分类型注解不需要手写——TypeScript 会自动推断：
const city = "Shanghai";     // 推断为 string
const count = 42;            // 推断为 number
const done = false;          // 推断为 boolean
// → TS 的类型推断非常智能，能推断的就别手写
// → 手写类型注解的场景：函数参数、函数返回值、复杂对象
```

```typescript
// ═══════════════════════════════════════
// 字面量类型（Literal Types）
// ═══════════════════════════════════════

// 字面量类型 = 把一个具体的值当作类型
// → "hello" 不只是一个字符串值，它本身也是一个类型（只包含 "hello" 这一个值的集合）

let changeable = "hello";            // 推断为 string（let 可变，所以宽泛推断）
const fixed = "hello";               // 推断为 "hello"（const 不可变，精确推断）

// 字面量类型的实际用途——限制取值范围：
type Direction = "up" | "down" | "left" | "right";
type HttpStatus = 200 | 301 | 400 | 404 | 500;
type YesNo = true | false;

function move(direction: Direction): void {
  console.log(`Moving ${direction}`);
}

move("up");      // ✅
move("down");    // ✅
move("forward"); // ❌ 错误：类型 "forward" 不能赋值给类型 Direction
// → 比 string 精确得多——编译器帮你限制了合法值
```

```
let vs const 对类型推断的影响：

  const x = "hello";     → 类型是 "hello"（字面量类型）
  let   x = "hello";     → 类型是 string（宽泛类型）

  const n = 42;           → 类型是 42
  let   n = 42;           → 类型是 number

  为什么？
  → const 声明的变量不会再变 → 编译器推断为精确的字面量类型
  → let 声明的变量可能被重新赋值 → 编译器推断为宽泛的原始类型

  实践意义：
  → 默认用 const → 获得更精确的类型推断
  → 需要字面量类型时用 as const 断言（后面会讲）
```

### 3.2 联合类型、交叉类型与类型收窄

联合类型和交叉类型是 TypeScript 最常用的类型组合方式——分别对应集合论中的"并集"和"交集"。

```typescript
// ═══════════════════════════════════════
// 联合类型（Union Types）—— 用 | 表示"或"
// ═══════════════════════════════════════

// 一个值可以是多种类型之一
type StringOrNumber = string | number;

let value: StringOrNumber;
value = "hello";    // ✅
value = 42;         // ✅
value = true;       // ❌ 错误：boolean 不能赋值给 string | number

// 实际场景：API 返回值可能是多种形态
type ApiResponse = 
  | { status: "success"; data: User[] }
  | { status: "error"; message: string }
  | { status: "loading" };
```

```typescript
// ═══════════════════════════════════════
// 交叉类型（Intersection Types）—— 用 & 表示"且"
// ═══════════════════════════════════════

// 一个值必须同时满足多个类型
type HasName = { name: string };
type HasAge = { age: number };
type HasEmail = { email: string };

type Person = HasName & HasAge;
// → 等价于 { name: string; age: number }

type DetailedPerson = HasName & HasAge & HasEmail;
// → 等价于 { name: string; age: number; email: string }

const person: Person = { name: "Alice", age: 30 };        // ✅
const bad: Person = { name: "Bob" };                       // ❌ 缺少 age
```

```typescript
// ═══════════════════════════════════════
// 类型收窄（Type Narrowing）—— 联合类型的灵魂伴侣
// ═══════════════════════════════════════

// 联合类型的问题：编译器不知道值到底是哪个类型
function processValue(value: string | number) {
  // value.toUpperCase();  // ❌ 错误：number 没有 toUpperCase 方法
  // → 怎么办？—— 用"类型收窄"告诉编译器

  // 方式 1：typeof 守卫
  if (typeof value === "string") {
    console.log(value.toUpperCase());   // ✅ 编译器知道这里是 string
  } else {
    console.log(value.toFixed(2));      // ✅ 编译器知道这里是 number
  }
}

// 方式 2：instanceof 守卫（类实例判断）
function logDate(value: Date | string) {
  if (value instanceof Date) {
    console.log(value.getFullYear());   // ✅ Date
  } else {
    console.log(Date.parse(value));     // ✅ string
  }
}

// 方式 3：in 守卫（属性存在性判断）
type Fish = { swim: () => void };
type Bird = { fly: () => void };

function move(animal: Fish | Bird) {
  if ("swim" in animal) {
    animal.swim();   // ✅ Fish
  } else {
    animal.fly();    // ✅ Bird
  }
}

// 方式 4：可辨识联合（Discriminated Unions）—— 最强大的收窄方式
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rectangle"; width: number; height: number }
  | { kind: "triangle"; base: number; height: number };

function getArea(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;      // ✅ 编译器知道有 radius
    case "rectangle":
      return shape.width * shape.height;        // ✅ 编译器知道有 width/height
    case "triangle":
      return 0.5 * shape.base * shape.height;   // ✅ 编译器知道有 base/height
  }
}
```

```
类型收窄的 4 种方式总结：

  typeof         → 原始类型判断（string / number / boolean）
  instanceof     → 类实例判断（Date / Error / 自定义类）
  in             → 属性存在性判断（"swim" in animal）
  可辨识联合      → 用一个公共字段（kind/type/status）区分变体

  最佳实践：
  → 优先用可辨识联合（最清晰、最安全）
  → API 响应、状态机、事件系统 → 都用可辨识联合
  → 简单场景用 typeof / instanceof 即可
```
### 3.3 数组、元组与枚举

```typescript
// ═══════════════════════════════════════
// 数组类型（Array Types）
// ═══════════════════════════════════════

// 两种等价写法：
const numbers: number[] = [1, 2, 3];
const names: Array<string> = ["Alice", "Bob"];   // 泛型写法

// 只读数组（防止意外修改）
const frozen: readonly number[] = [1, 2, 3];
frozen.push(4);   // ❌ 错误：readonly number[] 没有 push 方法
// → 适合函数参数——承诺不修改传入的数组
```

```typescript
// ═══════════════════════════════════════
// 元组类型（Tuple Types）
// ═══════════════════════════════════════

// 元组 = 固定长度、每个位置类型确定的数组
const pair: [string, number] = ["Alice", 30];
const triple: [number, number, string] = [1, 2, "hello"];

// 访问元组元素：编译器知道每个位置的精确类型
pair[0].toUpperCase();   // ✅ pair[0] 是 string
pair[1].toFixed(2);      // ✅ pair[1] 是 number

// 解构赋值：自动推断类型
const [name, age] = pair;
// name: string, age: number

// 带标签的元组（增加可读性，TS 4.0+）
type Range = [start: number, end: number];
type Response = [status: number, body: string, headers: Record<string, string>];

// 实际用途：函数返回多个值（类似 Python 的多返回值）
function useState<T>(initial: T): [T, (value: T) => void] {
  let state = initial;
  const setState = (value: T) => { state = value; };
  return [state, setState];
}
const [count, setCount] = useState(0);   // React useState 的类型就是这样定义的
```

```typescript
// ═══════════════════════════════════════
// as const 断言 —— 把值"冻结"为字面量类型
// ═══════════════════════════════════════

// 普通数组推断：
const colors = ["red", "green", "blue"];
// → 类型是 string[]

// as const 断言：
const colors2 = ["red", "green", "blue"] as const;
// → 类型是 readonly ["red", "green", "blue"]
// → 每个元素都是字面量类型，且数组是只读的

// 实际用途：定义常量配置
const CONFIG = {
  api: "https://api.example.com",
  timeout: 3000,
  retries: 3,
} as const;
// → 类型是 { readonly api: "https://api.example.com"; readonly timeout: 3000; ... }
// → 所有属性都变成 readonly + 字面量类型
```

```typescript
// ═══════════════════════════════════════
// 枚举（Enum）
// ═══════════════════════════════════════

// 数字枚举：自动递增
enum Direction {
  Up,      // 0
  Down,    // 1
  Left,    // 2
  Right,   // 3
}
const dir: Direction = Direction.Up;   // → 0

// 字符串枚举：推荐使用（可读性好）
enum Status {
  Active = "ACTIVE",
  Inactive = "INACTIVE",
  Pending = "PENDING",
}
const status: Status = Status.Active;  // → "ACTIVE"

// const enum：编译时内联，不生成 JS 对象
const enum Color {
  Red = "RED",
  Green = "GREEN",
  Blue = "BLUE",
}
const c = Color.Red;  // 编译后直接变成 const c = "RED"
// → 性能更好，但不能动态访问 Color[key]
```

```
枚举的使用建议：

  ✅ 推荐：字符串枚举 or 联合类型
  ──────────────────────────────
  → 字符串枚举：需要在运行时用到枚举值时
  → 联合类型：大多数场景的更好选择

  // 联合类型替代枚举（推荐）：
  type Status = "active" | "inactive" | "pending";
  → 更轻量（编译后消失）
  → 不引入额外的运行时对象
  → 与 JSON API 更兼容

  ⚠️ 谨慎：数字枚举
  ──────────────────────────────
  → 值是数字 → 容易误传 → Direction.Up === 0
  → 反向映射 → Direction[0] === "Up"（容易搞混）

  ❌ 避免：异构枚举（混合数字和字符串）
  ──────────────────────────────
  → enum Mixed { A = 0, B = "hello" }  → 别这么干
```
### 3.4 特殊类型：any / unknown / never / void

这四个类型在类型系统中扮演特殊角色——理解它们就是理解 TypeScript 类型系统的边界。

```typescript
// ═══════════════════════════════════════
// any —— "关闭类型检查"（逃生舱口）
// ═══════════════════════════════════════

let anything: any = 42;
anything = "hello";           // ✅ 不报错
anything = { a: 1 };          // ✅ 不报错
anything.nonExistent.method();// ✅ 不报错！—— 但运行时会炸
// → any 完全关闭类型检查，等于回到 JavaScript
// → 能赋值给任何类型，也能接收任何类型

// any 的"传染性"——碰到 any 的都变成 any：
const result = anything + 1;  // result 也是 any
// → 一个 any 可能污染整条调用链
```

```typescript
// ═══════════════════════════════════════
// unknown —— 类型安全的 any（推荐替代方案）
// ═══════════════════════════════════════

let mystery: unknown = 42;
mystery = "hello";            // ✅ 可以接收任何值
mystery = { a: 1 };           // ✅ 可以接收任何值

// 但是——不能直接使用！
// mystery.toString();         // ❌ 错误：unknown 类型不能调用方法
// const num: number = mystery; // ❌ 错误：unknown 不能赋值给 number

// 必须先收窄类型：
if (typeof mystery === "string") {
  console.log(mystery.toUpperCase());  // ✅ 收窄后可以用
}

if (typeof mystery === "number") {
  console.log(mystery.toFixed(2));     // ✅ 收窄后可以用
}

// 实际场景：处理外部输入（API 响应、JSON 解析、第三方库返回值）
async function fetchData(url: string): Promise<unknown> {
  const response = await fetch(url);
  return response.json();  // 返回 unknown，强制调用方做类型检查
}
```

```typescript
// ═══════════════════════════════════════
// never —— "不可能的类型"（空集）
// ═══════════════════════════════════════

// never 表示"永远不会有值"的类型

// 场景 1：永远不返回的函数
function throwError(message: string): never {
  throw new Error(message);   // 永远不会正常返回
}

function infiniteLoop(): never {
  while (true) {}             // 永远不会结束
}

// 场景 2：穷尽检查（Exhaustive Check）—— never 的杀手级应用
type Shape = "circle" | "rectangle" | "triangle";

function getArea(shape: Shape): number {
  switch (shape) {
    case "circle":    return 100;
    case "rectangle": return 200;
    case "triangle":  return 150;
    default:
      // 如果所有 case 都覆盖了，shape 在这里是 never 类型
      const _exhaustive: never = shape;
      return _exhaustive;
      // → 如果以后新增了 "pentagon" 但忘记加 case
      // → 编译器会报错："pentagon" 不能赋值给 never
      // → 强制你处理所有变体！
  }
}
```

```typescript
// ═══════════════════════════════════════
// void —— "没有返回值"
// ═══════════════════════════════════════

// void 表示函数不返回有意义的值
function logMessage(msg: string): void {
  console.log(msg);
  // 隐式返回 undefined
}

// void vs undefined 的区别：
// → void 作为返回类型时，允许返回 undefined 或不写 return
// → 回调函数的 void 更宽松——允许忽略返回值

type Callback = (value: string) => void;

// 即使回调返回了值，void 也不报错——返回值被忽略
const cb: Callback = (v) => v.length;  // ✅ 返回 number，但被忽略
// → 这是设计如此：Array.forEach 的回调就是 (item) => void
// → 你可以在回调里 return，但调用方不会用这个返回值
```

```
四种特殊类型的全景对比：

  类型        集合含义    能赋值给它    能从它赋值    使用场景
  ───────────────────────────────────────────────────────────
  any         "作弊码"   任何值 ✅     任何类型 ✅   逃生、渐进迁移
  unknown     "全集"     任何值 ✅     必须收窄 ❌   外部输入、安全替代 any
  never       "空集"     没有值 ❌     任何类型 ✅   穷尽检查、不可达代码
  void        "无返回"   undefined     不可用       函数无返回值

  选择策略：
  → 接收外部数据 → unknown（比 any 安全）
  → 函数无返回 → void
  → 函数永不返回 → never
  → any？尽量避免，实在需要时用 // eslint-disable 标记
```

> 💡 **黄金法则**：遇到 `any` 就想想能不能换成 `unknown`。`unknown` 强制你在使用前做类型检查，从而避免运行时错误。把 `any` 当作"技术债标记"——每用一次，就欠编译器一个人情。

---

## 4. 函数与对象的类型化

函数和对象是 JavaScript 的两大基石。TypeScript 为它们提供了丰富的类型化工具——从函数签名到重载，从 interface 到索引签名，从类型断言到 satisfies。

### 4.1 函数类型签名与重载

```typescript
// ═══════════════════════════════════════
// 函数参数与返回值类型
// ═══════════════════════════════════════

// 基本签名：参数类型 + 返回值类型
function add(a: number, b: number): number {
  return a + b;
}

// 返回值通常不需要手写——编译器会推断
function multiply(a: number, b: number) {
  return a * b;   // 推断返回值为 number
}

// 箭头函数
const divide = (a: number, b: number): number => a / b;

// 可选参数（用 ? 标记，必须在必选参数后面）
function greet(name: string, greeting?: string): string {
  return `${greeting ?? "Hello"}, ${name}!`;
}
greet("Alice");             // ✅ → "Hello, Alice!"
greet("Alice", "Hi");       // ✅ → "Hi, Alice!"

// 默认值参数（自动推断类型，不需要 ?）
function createUser(name: string, role: string = "viewer") {
  return { name, role };
}
// role 的类型自动推断为 string，调用时可省略

// 剩余参数（Rest Parameters）
function sum(...numbers: number[]): number {
  return numbers.reduce((acc, n) => acc + n, 0);
}
sum(1, 2, 3, 4, 5);   // → 15
```

```typescript
// ═══════════════════════════════════════
// 函数类型表达式（描述"函数长什么样"）
// ═══════════════════════════════════════

// 用类型别名定义函数类型
type MathFn = (a: number, b: number) => number;

const add: MathFn = (a, b) => a + b;     // ✅ 参数类型从 MathFn 推断
const sub: MathFn = (a, b) => a - b;     // ✅

// 回调函数类型
type OnSuccess = (data: User[]) => void;
type OnError = (error: Error) => void;

function fetchUsers(onSuccess: OnSuccess, onError: OnError): void {
  // ...
}

// 带泛型的函数类型（预告，第 5 章详解）
type Transform<T, U> = (input: T) => U;
const toString: Transform<number, string> = (n) => String(n);
```

```typescript
// ═══════════════════════════════════════
// 函数重载（Overload Signatures）
// ═══════════════════════════════════════

// 问题：一个函数根据不同参数返回不同类型
// → 不用重载：返回类型是联合类型，调用方需要自己判断
// → 用重载：编译器根据参数自动推断返回类型

// 重载签名（声明多种调用方式）
function parse(input: string): number;
function parse(input: number): string;
// 实现签名（处理所有情况）
function parse(input: string | number): string | number {
  if (typeof input === "string") {
    return parseInt(input, 10);
  }
  return String(input);
}

// 调用时，编译器根据参数类型推断返回类型：
const num = parse("42");     // 推断为 number
const str = parse(42);       // 推断为 string
// → 不需要调用方做类型收窄！

// 更实际的例子：createElement 风格的重载
function createElement(tag: "div"): HTMLDivElement;
function createElement(tag: "span"): HTMLSpanElement;
function createElement(tag: "input"): HTMLInputElement;
function createElement(tag: string): HTMLElement;
function createElement(tag: string): HTMLElement {
  return document.createElement(tag);
}

const div = createElement("div");     // HTMLDivElement
const input = createElement("input"); // HTMLInputElement
```

```
函数重载 vs 联合类型——怎么选？

  用联合类型：
  → 参数和返回值之间没有关联
  → function log(value: string | number): void

  用重载：
  → 参数类型决定返回值类型（1 对 1 映射）
  → parse("42") → number, parse(42) → string
  → 调用方不需要做类型收窄

  用泛型（第 5 章）：
  → 参数和返回值的类型关系是通用规律
  → function identity<T>(x: T): T
```

### 4.2 interface vs type：定义对象类型

这是 TypeScript 社区最常见的争论之一。先看能力差异，再给选型建议。

```typescript
// ═══════════════════════════════════════
// interface —— 定义对象的"契约"
// ═══════════════════════════════════════

interface User {
  id: number;
  name: string;
  email: string;
}

// 继承（extends）
interface Admin extends User {
  role: "admin";
  permissions: string[];
}

// 多继承
interface SuperAdmin extends Admin {
  level: number;
}

const admin: Admin = {
  id: 1,
  name: "Alice",
  email: "alice@example.com",
  role: "admin",
  permissions: ["read", "write", "delete"],
};
```

```typescript
// ═══════════════════════════════════════
// type —— 类型别名（更通用）
// ═══════════════════════════════════════

type User = {
  id: number;
  name: string;
  email: string;
};

// "继承"用交叉类型
type Admin = User & {
  role: "admin";
  permissions: string[];
};

// type 能做但 interface 不能做的事：
type StringOrNumber = string | number;           // 联合类型
type Pair = [string, number];                    // 元组
type Callback = (data: string) => void;          // 函数类型
type Status = "active" | "inactive";             // 字面量联合
type MaybeUser = User | null;                    // 可空类型
```

```typescript
// ═══════════════════════════════════════
// interface 独有能力：声明合并（Declaration Merging）
// ═══════════════════════════════════════

// 同名 interface 会自动合并
interface Window {
  myCustomProp: string;
}
// → 原有的 Window 接口被扩展了 myCustomProp 属性
// → 这就是为什么你能给全局对象（Window / Express.Request）添加属性

// type 不能声明合并：
// type Window = { myCustomProp: string };
// → ❌ 错误：标识符 Window 重复

// 实际应用：扩展第三方库的类型
declare module "express" {
  interface Request {
    userId?: string;    // 给 Express Request 添加自定义属性
    sessionId?: string;
  }
}
```

```
interface vs type 选型指南：

  场景                          推荐             原因
  ──────────────────────────────────────────────────────
  定义对象形状                  interface        语义更清晰
  需要 extends 继承             interface        语法更自然
  需要声明合并（扩展全局/库）    interface        type 不支持
  联合类型 / 元组 / 函数类型    type             interface 不支持
  映射类型 / 条件类型           type             interface 不支持
  复杂类型组合                  type             更灵活

  团队规范建议：
  → 对象形状用 interface，其余用 type
  → 或者：统一用 type（更简单，少一个选择）
  → 重点是团队一致，别混着来
```
### 4.3 可选、只读与索引签名

```typescript
// ═══════════════════════════════════════
// 可选属性（Optional Properties）
// ═══════════════════════════════════════

interface CreateUserInput {
  name: string;          // 必选
  email: string;         // 必选
  avatar?: string;       // 可选（类型实际是 string | undefined）
  bio?: string;          // 可选
}

// 可选属性的坑：strictNullChecks 下需要处理 undefined
function displayUser(user: CreateUserInput) {
  // user.avatar.toUpperCase();  // ❌ avatar 可能是 undefined
  user.avatar?.toUpperCase();    // ✅ 可选链
  user.avatar ?? "default.png";  // ✅ 空值合并
}
```

```typescript
// ═══════════════════════════════════════
// 只读属性（Readonly Properties）
// ═══════════════════════════════════════

interface Config {
  readonly apiUrl: string;
  readonly timeout: number;
  retries: number;           // 可修改
}

const config: Config = {
  apiUrl: "https://api.example.com",
  timeout: 3000,
  retries: 3,
};

config.retries = 5;          // ✅ 可以修改
// config.apiUrl = "xxx";    // ❌ 错误：无法分配到 apiUrl，因为它是只读属性

// Readonly 工具类型：一键把所有属性变成只读
type FrozenConfig = Readonly<Config>;
// → { readonly apiUrl: string; readonly timeout: number; readonly retries: number }
```

```typescript
// ═══════════════════════════════════════
// 索引签名（Index Signatures）
// ═══════════════════════════════════════

// 当你不知道对象会有哪些属性，但知道属性值的类型
interface StringMap {
  [key: string]: string;     // 任意 string 键 → string 值
}

const headers: StringMap = {
  "Content-Type": "application/json",
  "Authorization": "Bearer xxx",
  "X-Custom": "value",
};

// 索引签名 + 固定属性
interface ApiResponse {
  status: number;            // 固定属性
  message: string;           // 固定属性
  [key: string]: unknown;    // 其余属性可以是任意类型
}

// Record 工具类型——更简洁的索引签名替代
type UserRoles = Record<string, string[]>;
// → 等价于 { [key: string]: string[] }

// Record 配合联合类型——精确限制键名
type StatusMap = Record<"success" | "error" | "pending", string>;
// → { success: string; error: string; pending: string }

const messages: StatusMap = {
  success: "操作成功",
  error: "操作失败",
  pending: "处理中",
};
```

```
属性修饰符速查：

  语法              含义                       场景
  ─────────────────────────────────────────────────────
  prop: T           必选属性                   大多数情况
  prop?: T          可选属性（T | undefined）  创建/更新输入
  readonly prop: T  只读属性                   配置、ID、创建时间
  [key: string]: T  索引签名                   动态键名的对象
  Record<K, V>      Record 工具类型            替代索引签名
```
### 4.4 类型断言与 satisfies 运算符

类型断言是"你告诉编译器：我比你更了解这个值的类型"。但滥用断言等于绕过类型检查——所以 TypeScript 4.9 引入了更安全的 `satisfies`。

```typescript
// ═══════════════════════════════════════
// as 类型断言——"我比编译器更懂"
// ═══════════════════════════════════════

// 场景 1：DOM 操作（编译器不知道元素的具体类型）
const input = document.getElementById("email");
// → 推断为 HTMLElement | null

// 断言为具体类型：
const emailInput = document.getElementById("email") as HTMLInputElement;
emailInput.value = "alice@example.com";   // ✅ 现在可以访问 .value

// 场景 2：JSON 解析
const data = JSON.parse('{"name":"Alice"}') as { name: string };

// ⚠️ 断言不会做运行时检查！如果断言错误，运行时才会出问题：
const wrong = "hello" as unknown as number;
// wrong.toFixed(2);  // 编译通过，运行时炸！
// → 断言是"信任声明"，不是类型转换
```

```typescript
// ═══════════════════════════════════════
// 非空断言（! 后缀）
// ═══════════════════════════════════════

// 告诉编译器"这个值一定不是 null/undefined"
const element = document.getElementById("app")!;
// → 去掉了 | null，断言元素一定存在

// 更安全的替代方案——先检查再用：
const el = document.getElementById("app");
if (el) {
  el.textContent = "Hello";   // ✅ 编译器自动收窄
}

// 或者抛出明确错误：
function assertDefined<T>(value: T | null | undefined, name: string): T {
  if (value == null) {
    throw new Error(`${name} is required but was ${value}`);
  }
  return value;
}
const safeEl = assertDefined(document.getElementById("app"), "app element");
```

```typescript
// ═══════════════════════════════════════
// satisfies 运算符（TS 4.9+）—— 安全的类型验证
// ═══════════════════════════════════════

// 问题：as 断言会丢失精确类型
type ColorMap = Record<string, string | number[]>;

// 用 as 的问题：
const colors1 = {
  red: "#ff0000",
  green: [0, 255, 0],
} as ColorMap;
// colors1.red → 类型是 string | number[]（丢失了精确类型！）
// colors1.red.toUpperCase();  // ❌ 编译器不确定是 string

// 用 satisfies 的好处：
const colors2 = {
  red: "#ff0000",
  green: [0, 255, 0],
} satisfies ColorMap;
// colors2.red → 类型是 string（保留了精确类型！）
// colors2.green → 类型是 number[]
colors2.red.toUpperCase();     // ✅ 编译器知道是 string

// satisfies 的核心价值：
// → 检查值是否符合某个类型约束
// → 但不改变推断出的精确类型
// → 鱼和熊掌兼得：既有类型检查，又有精确推断
```

```
as vs satisfies vs 类型注解——三者对比：

  方式                    类型检查    保留精确类型    使用场景
  ──────────────────────────────────────────────────────────
  const x: Type = val     ✅         ❌ 宽化为 Type   变量声明
  const x = val as Type   ❌ 可绕过   ❌ 强制为 Type   DOM、JSON、外部数据
  const x = val satisfies Type  ✅   ✅ 保留推断     配置对象、常量映射

  黄金法则：
  → 能用类型注解就用类型注解（最安全）
  → 需要精确推断时用 satisfies（次安全）
  → as 断言是最后手段（谨慎使用）
  → 非空断言 ! 尽量避免（用 if 检查替代）
```

> 💡 **`satisfies` 的典型场景**：路由配置、主题色映射、i18n 翻译对象——这些场景需要"确保结构正确"的同时"保留每个值的精确类型"。如果你在用 `as const` + 类型检查的组合，`satisfies` 通常是更好的选择。

---

## 5. 泛型编程

泛型是 TypeScript 类型系统的"发动机"——如果基础类型是积木，泛型就是让积木变成乐高的关键齿轮。掌握泛型，你才能写出真正可复用的类型安全代码。

### 5.1 泛型入门：类型的"函数"

泛型的核心思想：**把类型当参数传递**。就像函数接收值参数一样，泛型函数接收类型参数。

```typescript
// ═══════════════════════════════════════
// 从一个具体问题开始
// ═══════════════════════════════════════

// 不用泛型：每种类型都要写一个函数
function identityString(value: string): string { return value; }
function identityNumber(value: number): number { return value; }
// → 写了两个功能完全相同的函数，只是类型不同

// 用 any？类型信息丢了：
function identityAny(value: any): any { return value; }
const result = identityAny("hello");  // result 是 any，不是 string

// 用泛型：一个函数搞定所有类型
function identity<T>(value: T): T {
  return value;
}
//            ↑ T 是类型参数（类型的"形参"）

const str = identity<string>("hello");   // 显式传入类型参数 → string
const num = identity(42);                // 自动推断 T = number → number
const arr = identity([1, 2, 3]);         // 自动推断 T = number[] → number[]
// → 输入什么类型，输出就是什么类型，类型信息完美保留
```

```
泛型 = 类型的"函数"：

  普通函数：  function add(a, b) → 传入值参数，返回值
  泛型函数：  function fn<T>(x: T): T → 传入类型参数，返回类型

  identity<string>("hello")
              ↑        ↑
         类型实参    值实参
              ↓        ↓
         T = string  value = "hello"
              ↓
         返回类型 = string

  → <T> 是类型的形参，<string> 是类型的实参
  → 大多数时候不需要手写 <string>，编译器自动推断
```

```typescript
// ═══════════════════════════════════════
// 泛型函数的常见模式
// ═══════════════════════════════════════

// 多个类型参数
function pair<A, B>(first: A, second: B): [A, B] {
  return [first, second];
}
const p = pair("hello", 42);   // 推断为 [string, number]

// 数组操作
function first<T>(arr: T[]): T | undefined {
  return arr[0];
}
const n = first([1, 2, 3]);      // T 推断为 number → number | undefined
const s = first(["a", "b"]);     // T 推断为 string → string | undefined

// 回调泛型
function map<T, U>(arr: T[], fn: (item: T) => U): U[] {
  return arr.map(fn);
}
const lengths = map(["hello", "world"], (s) => s.length);
// T = string, U = number → lengths: number[]
```

```typescript
// ═══════════════════════════════════════
// 泛型接口与泛型类型别名
// ═══════════════════════════════════════

// 泛型接口
interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

const userResponse: ApiResponse<User> = {
  code: 200,
  message: "success",
  data: { id: 1, name: "Alice", email: "alice@example.com" },
};

const listResponse: ApiResponse<User[]> = {
  code: 200,
  message: "success",
  data: [{ id: 1, name: "Alice", email: "alice@example.com" }],
};

// 泛型类型别名
type Result<T, E = Error> = 
  | { ok: true; value: T }
  | { ok: false; error: E };

function divide(a: number, b: number): Result<number, string> {
  if (b === 0) return { ok: false, error: "Division by zero" };
  return { ok: true, value: a / b };
}

const result = divide(10, 3);
if (result.ok) {
  console.log(result.value.toFixed(2));  // ✅ 编译器知道是 number
} else {
  console.log(result.error.toUpperCase()); // ✅ 编译器知道是 string
}
```

### 5.2 泛型约束与默认值

无约束的泛型 `<T>` 太宽泛了——T 可能是任何类型，你什么操作都做不了。**泛型约束**用 `extends` 限制 T 的范围。

```typescript
// ═══════════════════════════════════════
// 问题：无约束的泛型
// ═══════════════════════════════════════

function getLength<T>(value: T): number {
  // return value.length;  // ❌ 错误：T 上不存在 length 属性
  // → T 可能是 number，number 没有 .length
  return 0;
}

// 解决：用 extends 约束 T 必须有 length 属性
function getLength<T extends { length: number }>(value: T): number {
  return value.length;     // ✅ 编译器知道 T 一定有 length
}

getLength("hello");        // ✅ string 有 length
getLength([1, 2, 3]);      // ✅ array 有 length
getLength({ length: 10 }); // ✅ 对象有 length
// getLength(42);           // ❌ number 没有 length
```

```typescript
// ═══════════════════════════════════════
// keyof 约束——安全地访问对象属性
// ═══════════════════════════════════════

// keyof 操作符：提取对象类型的所有键
type UserKeys = keyof User;   // → "id" | "name" | "email"

// 经典泛型模式：类型安全的属性访问
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { id: 1, name: "Alice", email: "alice@example.com" };

const name = getProperty(user, "name");     // 推断为 string
const id = getProperty(user, "id");         // 推断为 number
// getProperty(user, "age");                // ❌ "age" 不在 keyof User 中

// → K extends keyof T 确保 key 一定是 obj 的合法属性
// → T[K] 是索引访问类型，返回对应属性的精确类型
```

```typescript
// ═══════════════════════════════════════
// 多重约束与接口约束
// ═══════════════════════════════════════

// 多重约束：用 & 组合
interface Serializable {
  serialize(): string;
}

interface Loggable {
  log(): void;
}

function process<T extends Serializable & Loggable>(item: T): string {
  item.log();                // ✅ T 一定有 log()
  return item.serialize();   // ✅ T 一定有 serialize()
}
```

```typescript
// ═══════════════════════════════════════
// 默认类型参数
// ═══════════════════════════════════════

// 给泛型参数设默认值（类似函数参数的默认值）
interface PaginatedResponse<T = unknown> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

// 使用时可以省略类型参数：
const response1: PaginatedResponse = {
  items: [],            // items: unknown[]
  total: 0, page: 1, pageSize: 20,
};

// 也可以显式指定：
const response2: PaginatedResponse<User> = {
  items: [{ id: 1, name: "Alice", email: "a@b.com" }],
  total: 1, page: 1, pageSize: 20,
};

// 实际应用：事件发射器
type EventHandler<T = void> = (payload: T) => void;
const onClick: EventHandler = () => {};            // 无参数事件
const onData: EventHandler<string> = (data) => {}; // 带参数事件
```

```
泛型约束速查：

  语法                          含义
  ───────────────────────────────────────────────
  <T>                           无约束，T 可以是任何类型
  <T extends SomeType>          T 必须是 SomeType 的子类型
  <T extends { length: number }> T 必须有 length 属性
  <K extends keyof T>           K 必须是 T 的键
  <T extends A & B>             T 必须同时满足 A 和 B
  <T = DefaultType>             T 有默认值
  <T extends Base = Default>    约束 + 默认值组合
```
### 5.3 条件类型：类型级的 if-else

条件类型让你在类型层面做分支判断——`T extends U ? X : Y` 就像类型世界的三元运算符。

```typescript
// ═══════════════════════════════════════
// 基本语法
// ═══════════════════════════════════════

// T extends U ? X : Y
// → 如果 T 是 U 的子类型，结果是 X，否则是 Y

type IsString<T> = T extends string ? true : false;

type A = IsString<string>;     // → true
type B = IsString<number>;     // → false
type C = IsString<"hello">;    // → true（"hello" 是 string 的子类型）

// 实际应用：根据输入类型决定输出类型
type Flatten<T> = T extends Array<infer U> ? U : T;

type D = Flatten<string[]>;     // → string（数组 → 提取元素类型）
type E = Flatten<number>;       // → number（非数组 → 原样返回）
```

```typescript
// ═══════════════════════════════════════
// 分发特性（Distributive Conditional Types）
// ═══════════════════════════════════════

// 当 T 是联合类型时，条件类型会自动"分发"——逐个检查

type ToArray<T> = T extends any ? T[] : never;

type F = ToArray<string | number>;
// → ToArray<string> | ToArray<number>
// → string[] | number[]
// 注意：不是 (string | number)[]

// 这就是 Exclude 和 Extract 的实现原理：

// Exclude：从联合类型中排除某些成员
type Exclude<T, U> = T extends U ? never : T;

type G = Exclude<"a" | "b" | "c", "a">;
// → "a" extends "a" ? never : "a" → never
// → "b" extends "a" ? never : "b" → "b"
// → "c" extends "a" ? never : "c" → "c"
// → never | "b" | "c" → "b" | "c"

// Extract：从联合类型中提取某些成员
type Extract<T, U> = T extends U ? T : never;

type H = Extract<string | number | boolean, string | boolean>;
// → string | boolean
```

```typescript
// ═══════════════════════════════════════
// 条件类型 + 泛型 = 类型级编程
// ═══════════════════════════════════════

// 根据类型返回不同的处理函数签名
type Processor<T> = T extends string
  ? (input: string) => string[]      // 字符串 → 返回分词结果
  : T extends number
  ? (input: number) => number        // 数字 → 返回计算结果
  : (input: T) => string;            // 其他 → 返回字符串

// 使用：编译器根据 T 推断正确的函数签名
const stringProcessor: Processor<string> = (s) => s.split(" ");
const numberProcessor: Processor<number> = (n) => n * 2;
```

```
条件类型的心智模型：

  T extends U ? X : Y

  → 理解为："T 是 U 的子集吗？"
  → 是 → 结果类型为 X
  → 否 → 结果类型为 Y

  分发特性（T 是联合类型时）：
  → (A | B | C) extends U ? X : Y
  → 等价于 (A extends U ? X : Y) | (B extends U ? X : Y) | ...
  → 每个成员分别检查，结果合并

  → 这个特性是 Exclude/Extract/NonNullable 的实现基础
```
### 5.4 实战：类型安全的 API 响应封装

把前面学的泛型技巧串起来，构建真实项目中的类型安全模式。

```typescript
// ═══════════════════════════════════════
// 实战 1：通用 API 响应包装
// ═══════════════════════════════════════

// 定义统一的响应结构
interface ApiSuccess<T> {
  success: true;
  data: T;
  meta?: {
    page?: number;
    total?: number;
    timestamp: number;
  };
}

interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

type ApiResponse<T> = ApiSuccess<T> | ApiError;

// 类型安全的 API 客户端
async function apiCall<T>(url: string): Promise<ApiResponse<T>> {
  const response = await fetch(url);
  return response.json() as Promise<ApiResponse<T>>;
}

// 使用——编译器自动推断 data 的类型：
interface User { id: number; name: string; email: string; }

const result = await apiCall<User>("/api/users/1");
if (result.success) {
  console.log(result.data.name);      // ✅ data 是 User 类型
} else {
  console.log(result.error.message);  // ✅ error 有 message 属性
}

const listResult = await apiCall<User[]>("/api/users");
if (listResult.success) {
  listResult.data.forEach((u) => console.log(u.email)); // ✅ User[]
}
```

```typescript
// ═══════════════════════════════════════
// 实战 2：通用 CRUD Repository
// ═══════════════════════════════════════

interface BaseEntity {
  id: number;
  createdAt: Date;
  updatedAt: Date;
}

// 泛型 Repository：T 必须有 id/createdAt/updatedAt
interface Repository<T extends BaseEntity> {
  findById(id: number): Promise<T | null>;
  findAll(filter?: Partial<T>): Promise<T[]>;
  create(data: Omit<T, "id" | "createdAt" | "updatedAt">): Promise<T>;
  update(id: number, data: Partial<Omit<T, "id">>): Promise<T>;
  delete(id: number): Promise<void>;
}

// 具体实体
interface User extends BaseEntity {
  name: string;
  email: string;
  role: "admin" | "viewer";
}

interface Post extends BaseEntity {
  title: string;
  content: string;
  authorId: number;
}

// 使用：
// userRepo.create({ name: "Alice", email: "a@b.com", role: "viewer" })
// → ✅ 不需要传 id/createdAt/updatedAt（Omit 自动排除）
// → ❌ 漏传 name 会报错
// → ❌ 多传 id 会报错
```

```typescript
// ═══════════════════════════════════════
// 实战 3：类型安全的事件总线
// ═══════════════════════════════════════

// 定义事件映射表
interface EventMap {
  "user:login": { userId: string; timestamp: number };
  "user:logout": { userId: string };
  "post:created": { postId: number; title: string };
  "error": Error;
}

// 泛型事件发射器——事件名和 payload 严格对应
class TypedEventEmitter<T extends Record<string, unknown>> {
  private listeners = new Map<string, Set<Function>>();

  on<K extends keyof T>(event: K, handler: (payload: T[K]) => void): void {
    if (!this.listeners.has(event as string)) {
      this.listeners.set(event as string, new Set());
    }
    this.listeners.get(event as string)!.add(handler);
  }

  emit<K extends keyof T>(event: K, payload: T[K]): void {
    this.listeners.get(event as string)?.forEach((fn) => fn(payload));
  }
}

// 使用：
const bus = new TypedEventEmitter<EventMap>();

bus.on("user:login", (payload) => {
  console.log(payload.userId);     // ✅ 自动推断为 { userId: string; timestamp: number }
});

bus.emit("user:login", { userId: "u1", timestamp: Date.now() }); // ✅
// bus.emit("user:login", { wrong: true }); // ❌ 类型不匹配
// bus.emit("typo:event", {});              // ❌ 事件名不存在
```

> 💡 **泛型的核心价值**：不是让代码更复杂，而是让"可复用"和"类型安全"同时成立。一个好的泛型设计，使用方几乎不需要手写类型参数——编译器自动推断，体验和 JavaScript 一样流畅，但多了编译期保障。

---

## 6. 类型体操核心技巧

"类型体操"听起来吓人，但它的本质是**用类型系统的原语（映射、条件、infer、递归）组合出新的类型**——就像用基础函数组合出复杂逻辑一样。这一章从内置工具类型开始，逐步深入到自定义类型工具。

### 6.1 内置工具类型全解析

TypeScript 内置了 20+ 个工具类型，按用途分为四组：

```typescript
// ═══════════════════════════════════════
// 第 1 组：属性修饰
// ═══════════════════════════════════════

interface User {
  id: number;
  name: string;
  email: string;
  avatar?: string;
}

// Partial<T> → 所有属性变可选
type PartialUser = Partial<User>;
// → { id?: number; name?: string; email?: string; avatar?: string }
// 场景：更新接口，只传需要改的字段

// Required<T> → 所有属性变必选
type RequiredUser = Required<User>;
// → { id: number; name: string; email: string; avatar: string }
// 场景：确保配置对象所有字段都填了

// Readonly<T> → 所有属性变只读
type ReadonlyUser = Readonly<User>;
// → { readonly id: number; readonly name: string; ... }
// 场景：冻结对象，防止意外修改
```

```typescript
// ═══════════════════════════════════════
// 第 2 组：键选择与排除
// ═══════════════════════════════════════

// Pick<T, K> → 从 T 中选取指定属性
type UserPreview = Pick<User, "id" | "name">;
// → { id: number; name: string }

// Omit<T, K> → 从 T 中排除指定属性
type CreateUserInput = Omit<User, "id">;
// → { name: string; email: string; avatar?: string }

// Record<K, V> → 构造键值对类型
type RolePermissions = Record<"admin" | "editor" | "viewer", string[]>;
// → { admin: string[]; editor: string[]; viewer: string[] }

// Exclude<T, U> → 从联合类型中排除
type NonString = Exclude<string | number | boolean, string>;
// → number | boolean

// Extract<T, U> → 从联合类型中提取
type Primitives = Extract<string | number | User, string | number>;
// → string | number

// NonNullable<T> → 排除 null 和 undefined
type SafeString = NonNullable<string | null | undefined>;
// → string
```

```typescript
// ═══════════════════════════════════════
// 第 3 组：函数工具
// ═══════════════════════════════════════

function createUser(name: string, age: number, role: string): User {
  return { id: 1, name, email: "", avatar: "" };
}

// ReturnType<T> → 提取函数返回类型
type CreateUserReturn = ReturnType<typeof createUser>;
// → User

// Parameters<T> → 提取函数参数类型（元组）
type CreateUserParams = Parameters<typeof createUser>;
// → [string, number, string]

// ConstructorParameters<T> → 提取构造函数参数
class UserService {
  constructor(private db: Database, private cache: Cache) {}
}
type ServiceParams = ConstructorParameters<typeof UserService>;
// → [Database, Cache]
```

```typescript
// ═══════════════════════════════════════
// 第 4 组：Promise 与异步工具
// ═══════════════════════════════════════

// Awaited<T> → 递归解包 Promise
type A = Awaited<Promise<string>>;              // → string
type B = Awaited<Promise<Promise<number>>>;     // → number（递归解包）
type C = Awaited<string | Promise<boolean>>;    // → string | boolean

// 实际场景：推断异步函数的返回值
async function fetchUser(): Promise<User> { /* ... */ }
type FetchResult = Awaited<ReturnType<typeof fetchUser>>;
// → User（而不是 Promise<User>）
```

```
内置工具类型速查表：

  属性修饰          Partial / Required / Readonly
  键选择            Pick / Omit / Record
  联合操作          Exclude / Extract / NonNullable
  函数提取          ReturnType / Parameters / ConstructorParameters
  异步解包          Awaited

  → 这些工具类型都是用映射类型 + 条件类型实现的
  → 下一节我们拆解它们的实现原理
```

### 6.2 映射类型与键重映射

映射类型是工具类型的实现基础——它用 `in` 操作符遍历键，对每个属性做变换。

```typescript
// ═══════════════════════════════════════
// 映射类型基本语法
// ═══════════════════════════════════════

// Partial 的实现原理：
type MyPartial<T> = {
  [K in keyof T]?: T[K];
//  ↑ 遍历 T 的每个键
//              ↑ 加上 ?（变可选）
//                  ↑ 值类型不变
};

// Readonly 的实现原理：
type MyReadonly<T> = {
  readonly [K in keyof T]: T[K];
};

// Required 的实现原理（用 - 去掉 ?）：
type MyRequired<T> = {
  [K in keyof T]-?: T[K];
//              ↑ -? 表示去掉可选修饰符
};

// Pick 的实现原理：
type MyPick<T, K extends keyof T> = {
  [P in K]: T[P];
//  ↑ 只遍历 K 中的键（不是 keyof T 的全部键）
};
```

```typescript
// ═══════════════════════════════════════
// 键重映射（Key Remapping，TS 4.1+）
// ═══════════════════════════════════════

// 用 as 子句在映射过程中重命名键

// 给所有键加前缀
type Prefixed<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

interface User { name: string; age: number; }
type UserGetters = Prefixed<User>;
// → { getName: () => string; getAge: () => number }

// 过滤键（返回 never 的键会被排除）
type OnlyStrings<T> = {
  [K in keyof T as T[K] extends string ? K : never]: T[K];
};

interface Mixed { name: string; age: number; email: string; active: boolean; }
type StringProps = OnlyStrings<Mixed>;
// → { name: string; email: string }
// → age 和 active 被过滤掉了（因为值类型不是 string）
```

```
映射类型的心智模型：

  { [K in Keys]: ValueType }

  → 类似 for...of 循环：
  → for (const K of Keys) { result[K] = ValueType }

  修饰符操作：
  → +?  / ?   → 加上可选（Partial）
  → -?        → 去掉可选（Required）
  → +readonly → 加上只读（Readonly）
  → -readonly → 去掉只读

  键重映射（as 子句）：
  → as NewKey      → 重命名键
  → as never       → 过滤掉该键
  → as `prefix${K}` → 加前缀/后缀
```
### 6.3 模板字面量类型

模板字面量类型（TS 4.1+）把 JavaScript 的模板字符串搬到了类型层面——你可以在类型中做字符串拼接和模式匹配。

```typescript
// ═══════════════════════════════════════
// 基本语法：类型级的字符串拼接
// ═══════════════════════════════════════

type Greeting = `Hello, ${string}`;       // 匹配 "Hello, " 开头的任意字符串
type Port = `${number}`;                  // 匹配任意数字字符串
type EventName = `on${string}`;           // 匹配 "on" 开头的事件名

// 联合类型 + 模板字面量 = 排列组合
type Color = "red" | "green" | "blue";
type Size = "sm" | "md" | "lg";

type ClassName = `${Color}-${Size}`;
// → "red-sm" | "red-md" | "red-lg"
// | "green-sm" | "green-md" | "green-lg"
// | "blue-sm" | "blue-md" | "blue-lg"
// → 3 × 3 = 9 种组合，自动生成！

// 实际应用：CSS 属性生成
type Direction = "top" | "right" | "bottom" | "left";
type CSSMargin = `margin-${Direction}`;
// → "margin-top" | "margin-right" | "margin-bottom" | "margin-left"

type CSSPadding = `padding-${Direction}`;
// → "padding-top" | "padding-right" | ... 
```

```typescript
// ═══════════════════════════════════════
// 内置字符串工具类型
// ═══════════════════════════════════════

type A = Uppercase<"hello">;       // → "HELLO"
type B = Lowercase<"HELLO">;       // → "hello"
type C = Capitalize<"hello">;      // → "Hello"
type D = Uncapitalize<"Hello">;    // → "hello"

// 组合使用：生成事件处理器名
type Events = "click" | "focus" | "blur";
type Handlers = `on${Capitalize<Events>}`;
// → "onClick" | "onFocus" | "onBlur"

// 配合映射类型：自动生成 getter/setter
interface State { count: number; name: string; }

type Setters<T> = {
  [K in keyof T as `set${Capitalize<string & K>}`]: (value: T[K]) => void;
};

type StateMutations = Setters<State>;
// → { setCount: (value: number) => void; setName: (value: string) => void }
```

```
模板字面量类型的应用场景：

  场景 1：类型安全的路由
  → type Route = `/users/${number}` | `/posts/${number}/comments`
  → 编译器检查路由格式是否正确

  场景 2：CSS-in-JS 类名生成
  → type ClassName = `${Color}-${Size}-${Variant}`
  → 自动生成所有合法的类名组合

  场景 3：事件系统
  → type Handler = `on${Capitalize<EventName>}`
  → onClick、onFocus、onBlur 自动生成

  场景 4：配合映射类型生成 API
  → getter/setter、validator、serializer 名自动生成
```
### 6.4 infer 模式匹配与递归类型

`infer` 是条件类型中的"模式匹配变量"——它让你在 `extends` 检查中**捕获**一部分类型，类似正则表达式的捕获组。

```typescript
// ═══════════════════════════════════════
// infer 基本用法：在条件类型中"捕获"类型
// ═══════════════════════════════════════

// 提取数组元素类型
type ElementOf<T> = T extends (infer U)[] ? U : never;
//                           ↑ infer U 捕获数组元素的类型

type A = ElementOf<string[]>;       // → string
type B = ElementOf<number[]>;       // → number
type C = ElementOf<(string | number)[]>; // → string | number

// 提取函数返回类型（ReturnType 的实现原理）
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
//                                                   ↑ infer R 捕获返回类型

type D = MyReturnType<() => string>;     // → string
type E = MyReturnType<(x: number) => boolean>; // → boolean

// 提取 Promise 内部类型
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;

type F = UnwrapPromise<Promise<string>>;  // → string
type G = UnwrapPromise<number>;           // → number（非 Promise，原样返回）
```

```typescript
// ═══════════════════════════════════════
// infer 高级用法：字符串模式匹配
// ═══════════════════════════════════════

// 提取字符串的第一个字符
type FirstChar<S extends string> = S extends `${infer F}${string}` ? F : never;
type H = FirstChar<"hello">;  // → "h"

// 去掉字符串前缀
type RemovePrefix<S extends string, P extends string> =
  S extends `${P}${infer Rest}` ? Rest : S;

type I = RemovePrefix<"onClick", "on">;  // → "Click"
type J = RemovePrefix<"hello", "on">;    // → "hello"（没有前缀，原样返回）

// 提取函数的第一个参数类型
type FirstParam<T> = T extends (first: infer P, ...rest: any[]) => any ? P : never;
type K = FirstParam<(name: string, age: number) => void>; // → string
```

```typescript
// ═══════════════════════════════════════
// 递归类型
// ═══════════════════════════════════════

// 递归解包嵌套 Promise（Awaited 的实现原理）
type DeepAwaited<T> = T extends Promise<infer U> ? DeepAwaited<U> : T;

type L = DeepAwaited<Promise<Promise<Promise<string>>>>;  // → string

// 递归把所有属性变成只读（深度 Readonly）
type DeepReadonly<T> = {
  readonly [K in keyof T]: T[K] extends object ? DeepReadonly<T[K]> : T[K];
};

// 递归把所有属性变成可选（深度 Partial）
type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K];
};

interface NestedConfig {
  server: { host: string; port: number };
  database: { url: string; pool: { min: number; max: number } };
}

type ReadonlyConfig = DeepReadonly<NestedConfig>;
// → server.host 是 readonly，database.pool.min 也是 readonly
// → 不只是第一层，所有层级都是只读
```

```
infer 的心智模型：

  T extends Pattern<infer U> ? UseU : Fallback

  → "T 符合 Pattern 的形状吗？"
  → 如果符合 → U 捕获了 Pattern 中的变量部分 → 用 U 构造结果
  → 如果不符合 → 走 Fallback

  类比正则表达式：
  → /hello (\w+)/.exec("hello world") → 捕获组 = "world"
  → "hello world" extends `hello ${infer W}` → W = "world"

  递归类型注意：
  → 必须有终止条件（否则无限递归）
  → TS 有递归深度限制（通常 50 层够用）
```
### 6.5 实战：自定义高级工具类型

把映射类型、条件类型、infer、递归组合起来，构建真实项目中实用的类型工具。

```typescript
// ═══════════════════════════════════════
// 工具 1：PickByValue —— 按值类型筛选属性
// ═══════════════════════════════════════

type PickByValue<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K];
};

interface User {
  id: number;
  name: string;
  email: string;
  age: number;
  active: boolean;
}

type StringFields = PickByValue<User, string>;
// → { name: string; email: string }

type NumberFields = PickByValue<User, number>;
// → { id: number; age: number }
```

```typescript
// ═══════════════════════════════════════
// 工具 2：StrictOmit —— 更安全的 Omit
// ═══════════════════════════════════════

// 内置的 Omit 不检查 key 是否存在：
type Bad = Omit<User, "typo">;  // ✅ 不报错！但 "typo" 根本不是 User 的键

// StrictOmit 要求 key 必须存在于 T 中：
type StrictOmit<T, K extends keyof T> = Omit<T, K>;

// type Bad2 = StrictOmit<User, "typo">;  // ❌ 报错：typo 不在 keyof User 中
type Good = StrictOmit<User, "id">;        // ✅ → { name; email; age; active }
```

```typescript
// ═══════════════════════════════════════
// 工具 3：PathKeys —— 嵌套对象的路径类型
// ═══════════════════════════════════════

// 生成嵌套对象所有可访问路径的联合类型
type PathKeys<T, Prefix extends string = ""> = T extends object
  ? {
      [K in keyof T & string]: T[K] extends object
        ? PathKeys<T[K], `${Prefix}${K}.`> | `${Prefix}${K}`
        : `${Prefix}${K}`;
    }[keyof T & string]
  : never;

interface AppConfig {
  server: { host: string; port: number };
  database: { url: string; pool: { min: number; max: number } };
}

type ConfigPaths = PathKeys<AppConfig>;
// → "server" | "server.host" | "server.port"
// | "database" | "database.url" | "database.pool"
// | "database.pool.min" | "database.pool.max"
// → 配合 get(config, "database.pool.min") 实现类型安全的深层访问
```

```typescript
// ═══════════════════════════════════════
// 工具 4：MutableKeys / ReadonlyKeys —— 分离可变/只读属性
// ═══════════════════════════════════════

// 判断属性是否只读
type IfEquals<X, Y, A, B> =
  (<T>() => T extends X ? 1 : 2) extends (<T>() => T extends Y ? 1 : 2) ? A : B;

type ReadonlyKeys<T> = {
  [K in keyof T]: IfEquals<
    { [P in K]: T[K] },
    { readonly [P in K]: T[K] },
    K, never
  >;
}[keyof T];

interface Mixed {
  readonly id: number;
  name: string;
  readonly createdAt: Date;
  email: string;
}

type RO = ReadonlyKeys<Mixed>;  // → "id" | "createdAt"
// → 自动识别出哪些属性是 readonly
```

> 💡 **类型体操的边界**：这些技巧很强大，但不要过度使用。如果一个类型定义需要同事花 10 分钟才能理解，它可能太复杂了。好的类型工具应该是——定义者花精力，使用者零负担。

---

## 7. 类型安全的实战模式

前面 6 章打好了基础，这一章把类型系统运用到真实业务场景——可辨识联合管理状态、类型守卫做运行时校验、事件系统保证类型匹配、Builder 模式实现链式类型推断。

### 7.1 可辨识联合与穷尽检查

可辨识联合在第 3 章简单介绍过，这里展开到真实业务场景。

```typescript
// ═══════════════════════════════════════
// 场景 1：异步请求状态管理
// ═══════════════════════════════════════

type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: Error; retryCount: number };

function renderUserProfile(state: AsyncState<User>) {
  switch (state.status) {
    case "idle":
      return "Click to load";
    case "loading":
      return "Loading...";
    case "success":
      return `Hello, ${state.data.name}`;     // ✅ data 存在
    case "error":
      return `Error: ${state.error.message}`; // ✅ error 存在
  }
}
```

```typescript
// ═══════════════════════════════════════
// 场景 2：表单校验结果
// ═══════════════════════════════════════

type ValidationResult =
  | { valid: true; value: string }
  | { valid: false; errors: string[] };

function validateEmail(input: string): ValidationResult {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (emailRegex.test(input)) {
    return { valid: true, value: input };
  }
  return { valid: false, errors: ["Invalid email format"] };
}

const result = validateEmail("test@example.com");
if (result.valid) {
  sendEmail(result.value);    // ✅ value 存在
} else {
  showErrors(result.errors);  // ✅ errors 存在
}
```

```typescript
// ═══════════════════════════════════════
// 穷尽检查：确保处理了所有变体
// ═══════════════════════════════════════

type PaymentMethod =
  | { type: "credit_card"; cardNumber: string; cvv: string }
  | { type: "paypal"; email: string }
  | { type: "bank_transfer"; iban: string };

// 穷尽检查辅助函数
function assertNever(value: never): never {
  throw new Error(`Unhandled case: ${JSON.stringify(value)}`);
}

function processPayment(method: PaymentMethod): string {
  switch (method.type) {
    case "credit_card":
      return `Charging card ${method.cardNumber}`;
    case "paypal":
      return `Charging PayPal ${method.email}`;
    case "bank_transfer":
      return `Transferring to ${method.iban}`;
    default:
      return assertNever(method);
      // → 如果新增了 { type: "crypto" } 但忘记加 case
      // → 编译器报错："crypto" 类型不能赋值给 never
      // → 编译期就强制你处理所有分支！
  }
}
```

```
可辨识联合的设计规范：

  1. 每个变体必须有一个公共字段（辨识符）
     → status / type / kind / tag
     → 值必须是字面量类型（"success" / "error"）

  2. 辨识符用 switch 做分支
     → 编译器自动收窄每个 case 中的类型

  3. default 分支用 assertNever 做穷尽检查
     → 新增变体忘记处理 → 编译报错
     → 比注释 // TODO 靠谱一万倍

  4. 适用场景：
     → API 响应状态、表单校验、支付方式
     → WebSocket 消息、Redux Action、状态机
```

### 7.2 类型守卫与自定义守卫函数

内置的 `typeof` / `instanceof` / `in` 只能处理简单情况。对于业务类型，需要自定义类型守卫。

```typescript
// ═══════════════════════════════════════
// 自定义类型守卫（Type Predicate）
// ═══════════════════════════════════════

interface Cat { meow(): void; whiskers: number; }
interface Dog { bark(): void; breed: string; }
type Pet = Cat | Dog;

// 用 is 关键字定义类型守卫
function isCat(pet: Pet): pet is Cat {
  return "meow" in pet;
//       ↑ 运行时检查逻辑
//                        ↑ pet is Cat 告诉编译器：返回 true 时，pet 是 Cat
}

function handlePet(pet: Pet) {
  if (isCat(pet)) {
    pet.meow();              // ✅ 编译器知道是 Cat
    console.log(pet.whiskers);
  } else {
    pet.bark();              // ✅ 编译器知道是 Dog
    console.log(pet.breed);
  }
}
```

```typescript
// ═══════════════════════════════════════
// 实际场景：API 响应验证
// ═══════════════════════════════════════

interface User { id: number; name: string; email: string; }

// 验证 unknown 数据是否是 User
function isUser(data: unknown): data is User {
  return (
    typeof data === "object" &&
    data !== null &&
    "id" in data && typeof (data as any).id === "number" &&
    "name" in data && typeof (data as any).name === "string" &&
    "email" in data && typeof (data as any).email === "string"
  );
}

// 安全地处理外部数据
async function fetchUser(id: number): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  const data: unknown = await response.json();

  if (isUser(data)) {
    return data;           // ✅ data 已经是 User 类型
  }
  throw new Error("Invalid user data from API");
}
```

```typescript
// ═══════════════════════════════════════
// 断言函数（Assertion Functions）
// ═══════════════════════════════════════

// 断言函数不返回值，而是"断言"参数的类型
// → 如果断言失败，抛出错误
// → 如果断言成功，后续代码中参数的类型被收窄

function assertIsString(value: unknown): asserts value is string {
  if (typeof value !== "string") {
    throw new Error(`Expected string, got ${typeof value}`);
  }
}

function processInput(input: unknown) {
  assertIsString(input);
  // → 如果执行到这里，说明断言通过了
  console.log(input.toUpperCase());  // ✅ input 是 string
}

// 断言非空
function assertDefined<T>(
  value: T | null | undefined,
  name: string
): asserts value is T {
  if (value == null) {
    throw new Error(`${name} must be defined`);
  }
}

const config = getConfig();        // Config | undefined
assertDefined(config, "config");
console.log(config.apiUrl);        // ✅ config 是 Config（不是 undefined）
```

```
类型守卫 vs 断言函数：

  类型守卫（is）：
  → 返回 boolean
  → 用在 if/else 分支中
  → 不改变控制流（两个分支都继续执行）

  断言函数（asserts）：
  → 不返回值（void）
  → 失败时抛出异常
  → 成功后，后续代码的类型被收窄
  → 类似 assert() 函数的行为
```
### 7.3 类型安全的事件系统

第 5 章展示了基础版 TypedEventEmitter，这里进阶到生产级设计。

```typescript
// ═══════════════════════════════════════
// 生产级类型安全事件系统
// ═══════════════════════════════════════

// 1. 定义事件映射（契约）
interface AppEvents {
  "auth:login": { userId: string; role: string };
  "auth:logout": { userId: string };
  "data:loaded": { items: unknown[]; total: number };
  "error": { code: number; message: string };
  "notification": string;
}

// 2. 类型安全的事件总线
class EventBus<T extends Record<string, unknown>> {
  private handlers = new Map<keyof T, Set<Function>>();

  // 订阅——事件名和回调参数严格对应
  on<K extends keyof T>(event: K, handler: (payload: T[K]) => void): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);

    // 返回取消订阅函数
    return () => this.handlers.get(event)?.delete(handler);
  }

  // 一次性订阅
  once<K extends keyof T>(event: K, handler: (payload: T[K]) => void): void {
    const unsubscribe = this.on(event, (payload) => {
      unsubscribe();
      handler(payload);
    });
  }

  // 发布——payload 类型自动匹配
  emit<K extends keyof T>(event: K, payload: T[K]): void {
    this.handlers.get(event)?.forEach((fn) => fn(payload));
  }
}

// 3. 使用
const bus = new EventBus<AppEvents>();

// ✅ 事件名和 payload 类型自动对应
bus.on("auth:login", (payload) => {
  console.log(payload.userId);   // ✅ 推断为 { userId: string; role: string }
});

bus.on("notification", (msg) => {
  console.log(msg.toUpperCase()); // ✅ 推断为 string
});

bus.emit("auth:login", { userId: "u1", role: "admin" }); // ✅
// bus.emit("auth:login", { wrong: true });                // ❌ 类型不匹配
// bus.emit("typo", {});                                   // ❌ 事件不存在

// 取消订阅
const unsub = bus.on("error", (err) => console.log(err.message));
unsub(); // 取消订阅
```

```
类型安全事件系统的关键设计：

  1. 事件映射接口 → 单一源头定义所有事件 + payload 类型
  2. K extends keyof T → 限制事件名必须合法
  3. T[K] → 索引访问类型自动推断 payload
  4. 返回 unsubscribe 函数 → 防止内存泄漏

  → 添加新事件只需修改 AppEvents 接口
  → 编译器自动检查所有 emit/on 调用是否匹配
  → 重构事件名/payload → 全量编译报错 → 零遗漏
```
### 7.4 Builder 模式与链式类型推断

Builder 模式是泛型的高级应用——每次链式调用后，类型系统自动"记住"已设置的字段。

```typescript
// ═══════════════════════════════════════
// 类型安全的 Builder
// ═══════════════════════════════════════

interface ServerConfig {
  host: string;
  port: number;
  ssl: boolean;
  timeout: number;
}

// Builder：每次 set 都返回一个"记住了新字段"的新类型
class ConfigBuilder<T extends Partial<ServerConfig> = {}> {
  private config: T;

  constructor(config: T = {} as T) {
    this.config = config;
  }

  // 每个 set 方法返回类型包含了新设置的字段
  setHost(host: string): ConfigBuilder<T & { host: string }> {
    return new ConfigBuilder({ ...this.config, host });
  }

  setPort(port: number): ConfigBuilder<T & { port: number }> {
    return new ConfigBuilder({ ...this.config, port });
  }

  setSsl(ssl: boolean): ConfigBuilder<T & { ssl: boolean }> {
    return new ConfigBuilder({ ...this.config, ssl });
  }

  setTimeout(timeout: number): ConfigBuilder<T & { timeout: number }> {
    return new ConfigBuilder({ ...this.config, timeout });
  }

  // build 方法要求 T 必须是完整的 ServerConfig
  build(this: ConfigBuilder<ServerConfig>): ServerConfig {
    return this.config;
  }
}

// 使用：
const config = new ConfigBuilder()
  .setHost("localhost")
  .setPort(3000)
  .setSsl(true)
  .setTimeout(5000)
  .build();              // ✅ 所有字段都设置了，build 成功

// 缺少字段时：
// new ConfigBuilder()
//   .setHost("localhost")
//   .setPort(3000)
//   .build();            // ❌ 编译报错：缺少 ssl 和 timeout
//                        // → this 的类型是 ConfigBuilder<{ host; port }>
//                        // → 不满足 ConfigBuilder<ServerConfig> 的约束
```

```typescript
// ═══════════════════════════════════════
// 更简洁的写法：泛型 set 方法
// ═══════════════════════════════════════

class Builder<T extends Record<string, unknown> = {}> {
  constructor(private data: T = {} as T) {}

  set<K extends string, V>(
    key: K,
    value: V
  ): Builder<T & Record<K, V>> {
    return new Builder({ ...this.data, [key]: value } as T & Record<K, V>);
  }

  getData(): T {
    return this.data;
  }
}

const result = new Builder()
  .set("name", "Alice")
  .set("age", 30)
  .set("active", true)
  .getData();

// result 的类型：{ name: string; age: number; active: boolean }
// → 完全由链式调用推断出来，不需要手动定义！
```

> 💡 **Builder 模式的核心技巧**：每次方法调用返回 `Builder<T & { newKey: newType }>`，用交叉类型逐步"积累"已设置的字段。`build()` 方法用 `this` 参数约束最终类型必须满足完整接口。这在 ORM 查询构建器、HTTP 请求构建器等场景非常实用。

---

## 8. 类与装饰器

TypeScript 的类在 JavaScript 类的基础上增加了访问修饰符、抽象类、接口实现等特性。装饰器则是元编程利器——NestJS、TypeORM 等框架的核心就是装饰器。

### 8.1 TypeScript 类的类型特性

```typescript
// ═══════════════════════════════════════
// 访问修饰符
// ═══════════════════════════════════════

class User {
  public name: string;          // 默认 public，任何地方都能访问
  private password: string;     // 只能在类内部访问
  protected role: string;       // 类内部 + 子类可以访问
  readonly id: number;          // 只读，初始化后不可修改

  constructor(id: number, name: string, password: string, role: string) {
    this.id = id;
    this.name = name;
    this.password = password;
    this.role = role;
  }

  // private 方法
  private hashPassword(): string {
    return `hashed_${this.password}`;
  }
}

const user = new User(1, "Alice", "123456", "admin");
user.name;           // ✅ public
// user.password;    // ❌ private，外部不可访问
// user.id = 2;      // ❌ readonly，不可修改
```

```typescript
// ═══════════════════════════════════════
// 参数属性简写（Parameter Properties）
// ═══════════════════════════════════════

// 上面的 User 类可以简写为：
class User {
  constructor(
    public readonly id: number,
    public name: string,
    private password: string,
    protected role: string,
  ) {}
  // → 修饰符 + 参数 = 自动声明 + 赋值
  // → 省去了手动 this.xxx = xxx
}
// 这是 TypeScript 独有语法，非常实用
```

```typescript
// ═══════════════════════════════════════
// implements —— 类实现接口
// ═══════════════════════════════════════

interface Serializable {
  serialize(): string;
}

interface Loggable {
  log(message: string): void;
}

// 一个类可以实现多个接口
class UserService implements Serializable, Loggable {
  constructor(private users: User[] = []) {}

  serialize(): string {
    return JSON.stringify(this.users);
  }

  log(message: string): void {
    console.log(`[UserService] ${message}`);
  }

  // 类自己的方法
  addUser(user: User): void {
    this.users.push(user);
    this.log(`Added user: ${user.name}`);
  }
}
// → implements 是编译期检查：确保类实现了接口的所有方法
// → 不实现 serialize() → 编译报错
```

```
TypeScript 类 vs JavaScript 类：

  特性                  JS      TS
  ─────────────────────────────────
  public/private        #       public/private/protected
  readonly              无      readonly
  参数属性简写          无      constructor(public x)
  implements            无      implements Interface
  abstract              无      abstract class
  泛型类                无      class Box<T>
  方法重载              无      overload signatures

  注意：
  → TS 的 private 是编译期检查，运行时仍可访问
  → 真正的运行时私有用 JS 原生的 #field
  → 建议：private 用于类型检查，# 用于真正的封装
```

### 8.2 泛型类与 abstract 抽象类

```typescript
// ═══════════════════════════════════════
// 泛型类——类型安全的容器
// ═══════════════════════════════════════

class Stack<T> {
  private items: T[] = [];

  push(item: T): void {
    this.items.push(item);
  }

  pop(): T | undefined {
    return this.items.pop();
  }

  peek(): T | undefined {
    return this.items[this.items.length - 1];
  }

  get size(): number {
    return this.items.length;
  }
}

const numStack = new Stack<number>();
numStack.push(1);
numStack.push(2);
numStack.pop();           // → number | undefined

const strStack = new Stack<string>();
strStack.push("hello");
// strStack.push(42);     // ❌ 类型 number 不能赋值给 string
```

```typescript
// ═══════════════════════════════════════
// abstract 抽象类——模板方法模式
// ═══════════════════════════════════════

// 抽象类不能直接实例化，只能被继承
abstract class BaseRepository<T extends { id: number }> {
  // 抽象方法：子类必须实现
  abstract findById(id: number): Promise<T | null>;
  abstract save(entity: T): Promise<T>;
  abstract delete(id: number): Promise<void>;

  // 具体方法：子类继承直接使用
  async findByIdOrThrow(id: number): Promise<T> {
    const entity = await this.findById(id);
    if (!entity) {
      throw new Error(`Entity with id ${id} not found`);
    }
    return entity;
  }

  async upsert(entity: T): Promise<T> {
    const existing = await this.findById(entity.id);
    if (existing) {
      return this.save({ ...existing, ...entity });
    }
    return this.save(entity);
  }
}

// 具体实现
interface User { id: number; name: string; email: string; }

class UserRepository extends BaseRepository<User> {
  private users: User[] = [];

  async findById(id: number): Promise<User | null> {
    return this.users.find((u) => u.id === id) ?? null;
  }

  async save(user: User): Promise<User> {
    const index = this.users.findIndex((u) => u.id === user.id);
    if (index >= 0) {
      this.users[index] = user;
    } else {
      this.users.push(user);
    }
    return user;
  }

  async delete(id: number): Promise<void> {
    this.users = this.users.filter((u) => u.id !== id);
  }
}

// 使用：
const repo = new UserRepository();
await repo.save({ id: 1, name: "Alice", email: "a@b.com" });
const user = await repo.findByIdOrThrow(1);  // ✅ User 类型
// → findByIdOrThrow 和 upsert 是从 BaseRepository 继承的通用方法
```

```
abstract 类 vs interface：

  abstract 类：
  → 可以有具体实现（模板方法）
  → 可以有 constructor
  → 单继承（一个类只能 extends 一个抽象类）
  → 编译后存在于 JS 中（有运行时开销）

  interface：
  → 只有类型声明，没有实现
  → 没有 constructor
  → 多实现（一个类可以 implements 多个接口）
  → 编译后完全消失（零运行时开销）

  选择：需要共享代码 → abstract 类；只需类型契约 → interface
```
### 8.3 装饰器：从实验性到 Stage 3 标准

TypeScript 5.0+ 支持 TC39 Stage 3 标准装饰器。与旧的实验性装饰器语法不同，标准装饰器不需要 `experimentalDecorators` 配置。

```typescript
// ═══════════════════════════════════════
// 方法装饰器——最常用的装饰器类型
// ═══════════════════════════════════════

// 日志装饰器：记录方法调用
function log(
  target: any,
  context: ClassMethodDecoratorContext
) {
  const methodName = String(context.name);

  return function (this: any, ...args: any[]) {
    console.log(`→ Calling ${methodName} with`, args);
    const result = target.apply(this, args);
    console.log(`← ${methodName} returned`, result);
    return result;
  };
}

// 性能计时装饰器
function timing(
  target: any,
  context: ClassMethodDecoratorContext
) {
  const methodName = String(context.name);

  return function (this: any, ...args: any[]) {
    const start = performance.now();
    const result = target.apply(this, args);
    const duration = performance.now() - start;
    console.log(`${methodName} took ${duration.toFixed(2)}ms`);
    return result;
  };
}

class UserService {
  @log
  @timing
  findUser(id: number): string {
    return `User_${id}`;
  }
}
// → 调用 findUser(1) 会打印：
// → Calling findUser with [1]
// → findUser took 0.05ms
// → findUser returned User_1
```

```typescript
// ═══════════════════════════════════════
// 类装饰器
// ═══════════════════════════════════════

// 注册装饰器：把类注册到全局注册表
const registry = new Map<string, any>();

function register(target: any, context: ClassDecoratorContext) {
  registry.set(context.name as string, target);
}

@register
class PaymentService {
  process() { return "paid"; }
}

// registry.get("PaymentService") → PaymentService 类
```

```
Stage 3 标准 vs 实验性装饰器：

  特性              标准装饰器（5.0+）         实验性装饰器
  ─────────────────────────────────────────────────────────
  配置              不需要额外配置             需要 experimentalDecorators
  参数              (target, context)          (target, key, descriptor)
  context           ClassMethodDecoratorContext PropertyDescriptor
  参数装饰器        不支持                     支持
  元数据            context.metadata           reflect-metadata
  NestJS            暂未迁移                   当前使用

  建议：
  → 新项目用标准装饰器
  → NestJS / TypeORM 项目继续用实验性装饰器
  → 两者不能混用
```
### 8.4 装饰器实战：手写一个迷你 IoC 容器

理解 NestJS 的核心原理——用装饰器实现依赖注入（IoC）。以下使用实验性装饰器（NestJS 当前使用的方式）。

```typescript
// ═══════════════════════════════════════
// 迷你 IoC 容器（需要 experimentalDecorators + emitDecoratorMetadata）
// ═══════════════════════════════════════
import "reflect-metadata";

// 依赖容器
const container = new Map<string, any>();

// @Injectable() 装饰器——标记一个类可以被注入
function Injectable(): ClassDecorator {
  return (target) => {
    // 获取构造函数参数的类型（通过 reflect-metadata）
    const deps = Reflect.getMetadata("design:paramtypes", target) || [];
    // 注册到容器
    container.set(target.name, { target, deps });
  };
}

// resolve 函数——递归解析依赖
function resolve<T>(Target: new (...args: any[]) => T): T {
  const entry = container.get(Target.name);
  if (!entry) throw new Error(`${Target.name} is not injectable`);

  // 递归解析依赖
  const deps = entry.deps.map((Dep: any) => resolve(Dep));
  return new Target(...deps);
}
```

```typescript
// ═══════════════════════════════════════
// 使用 IoC 容器
// ═══════════════════════════════════════

@Injectable()
class DatabaseService {
  query(sql: string): string {
    return `Result of: ${sql}`;
  }
}

@Injectable()
class LoggerService {
  log(message: string): void {
    console.log(`[LOG] ${message}`);
  }
}

@Injectable()
class UserService {
  // 构造函数参数自动注入
  constructor(
    private db: DatabaseService,
    private logger: LoggerService,
  ) {}

  findUser(id: number): string {
    this.logger.log(`Finding user ${id}`);
    return this.db.query(`SELECT * FROM users WHERE id = ${id}`);
  }
}

// 解析——自动创建整个依赖链
const userService = resolve(UserService);
// → 自动创建 DatabaseService 和 LoggerService
// → 注入到 UserService 的构造函数中

userService.findUser(1);
// [LOG] Finding user 1
// Result of: SELECT * FROM users WHERE id = 1
```

```
IoC 容器的工作原理：

  @Injectable()
  class UserService {                    ┌─────────────┐
    constructor(                         │  container   │
      private db: DatabaseService,  ──→  │              │
      private logger: LoggerService ──→  │ UserService  │
    ) {}                                 │   ├── DatabaseService
  }                                      │   └── LoggerService
                                         └─────────────┘

  resolve(UserService)
    1. 从 container 找到 UserService
    2. 读取它的依赖：[DatabaseService, LoggerService]
    3. 递归 resolve 每个依赖
    4. new UserService(dbInstance, loggerInstance)

  → 这就是 NestJS 的核心原理！
  → NestJS 的 Module/Controller/Service 都是装饰器 + IoC
```

---

## 9. 声明文件与模块系统

当你用 TypeScript 调用 JavaScript 库时，类型信息从哪里来？答案是声明文件（`.d.ts`）。这一章讲清楚声明文件的生态、编写方式，以及 ESM/CJS 模块系统在 TypeScript 中的坑。

### 9.1 .d.ts 声明文件原理

```typescript
// ═══════════════════════════════════════
// 什么是 .d.ts 文件？
// ═══════════════════════════════════════

// .d.ts 文件只包含类型声明，不包含实现
// → 告诉 TypeScript 编译器："这个 JS 库长这样"

// 例如 lodash 没有自带类型，@types/lodash 提供了 .d.ts：
// node_modules/@types/lodash/index.d.ts
declare function chunk<T>(array: T[], size?: number): T[][];
declare function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait?: number
): T;

// 有了这些声明，你就能享受类型检查和智能提示：
import { chunk } from "lodash";
const result = chunk([1, 2, 3, 4], 2);  // → number[][]
```

```
.d.ts 的来源（按优先级）：

  1. 库自带类型
     → package.json 中 "types": "./dist/index.d.ts"
     → 现代库（zod、drizzle、hono）都自带类型

  2. @types 包（DefinitelyTyped 社区）
     → npm i @types/lodash -D
     → npm i @types/express -D
     → 自动从 node_modules/@types/ 加载

  3. 手写 .d.ts
     → 当库既不自带类型，也没有 @types 时
     → 创建 src/types/xxx.d.ts 手动声明
```

### 9.2 为第三方库编写类型声明

```typescript
// ═══════════════════════════════════════
// 场景：用了一个没有类型的 JS 库
// ═══════════════════════════════════════

// 方式 1：declare module（最常用）
// 创建 src/types/some-lib.d.ts：
declare module "some-legacy-lib" {
  export function doSomething(input: string): number;
  export function transform(data: unknown[]): string[];
  export const VERSION: string;
}

// 方式 2：快速跳过（临时方案）
declare module "untyped-lib";
// → 所有导入都是 any
// → 至少不报 "Cannot find module" 错误

// 方式 3：全局变量声明（script 标签引入的库）
// src/types/global.d.ts：
declare const gtag: (
  command: string,
  eventName: string,
  params?: Record<string, unknown>
) => void;

declare const __APP_VERSION__: string;  // 构建工具注入的全局变量
```

```typescript
// ═══════════════════════════════════════
// 扩展已有库的类型
// ═══════════════════════════════════════

// 给 Express Request 添加自定义属性
declare module "express" {
  interface Request {
    userId?: string;
    role?: "admin" | "viewer";
  }
}

// 使用时：
app.get("/profile", (req, res) => {
  console.log(req.userId);   // ✅ string | undefined
  console.log(req.role);     // ✅ "admin" | "viewer" | undefined
});

// 给全局 Window 添加属性
declare global {
  interface Window {
    analytics: {
      track(event: string, data?: Record<string, unknown>): void;
    };
  }
}
```

### 9.3 模块系统：ESM / CJS 与 TypeScript

```typescript
// ═══════════════════════════════════════
// ESM vs CJS 在 TypeScript 中的区别
// ═══════════════════════════════════════

// ESM（推荐）
import { readFile } from "fs/promises";
import type { User } from "./types.js";   // 注意：.js 后缀！
export function createUser(): User { /* ... */ }

// CJS
const fs = require("fs");
module.exports = { createUser };

// TypeScript 中的关键配置：
// "module": "NodeNext" → 让 Node.js 自己决定 ESM 还是 CJS
// → .ts 文件 → 看 package.json 的 "type" 字段
// → "type": "module" → ESM
// → "type": "commonjs" 或无 → CJS
```

```
Node.js + TypeScript 的模块决策树：

  package.json 有 "type": "module" ?
  ├── 是 → 默认 ESM
  │   → import/export 语法
  │   → 导入路径需要 .js 后缀（即使源码是 .ts）
  │   → import x from "./utils.js"（编译后文件名）
  │
  └── 否 → 默认 CJS
      → require/module.exports
      → 或者用 import（TypeScript 编译成 require）

  tsconfig 配置搭配：
  → "module": "NodeNext"
  → "moduleResolution": "NodeNext"
  → 让 TypeScript 完全遵循 Node.js 的模块规则
```

### 9.4 全局类型扩展与路径别名

```typescript
// ═══════════════════════════════════════
// 全局类型：项目级的公共类型定义
// ═══════════════════════════════════════

// src/types/global.d.ts
declare global {
  // 给 Array 添加自定义方法（谨慎使用）
  interface Array<T> {
    first(): T | undefined;
    last(): T | undefined;
  }

  // 全局类型别名
  type Nullable<T> = T | null;
  type Optional<T> = T | undefined;
}

export {};  // 让文件成为模块（必须）
```

```json
// ═══════════════════════════════════════
// 路径别名配置
// ═══════════════════════════════════════

// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@config/*": ["./src/config/*"],
      "@utils/*": ["./src/utils/*"],
      "@types/*": ["./src/types/*"]
    }
  }
}

// 使用（代替 ../../../utils/helper）：
// import { formatDate } from "@utils/helper"
// import type { User } from "@types/models"
// import { config } from "@config/app"

// ⚠️ 注意：tsconfig paths 只解决编译期
// 运行时需要额外配置：
// → tsx / ts-node → 需要 tsconfig-paths
// → Vite / Next.js → 自动支持
// → Node.js 原生 → 需要 --loader 或打包后使用
```

---

## 10. TypeScript 工程化最佳实践

最后一章聚焦工程化——怎么把 TypeScript 用好，而不是"用了但没完全用"。

### 10.1 渐进式迁移：从 JS 到 TS

```
渐进式迁移路线图（4 个阶段）：

  阶段 1：允许 JS 共存（1-2 天）
  ────────────────────────
  → tsconfig.json 添加 "allowJs": true, "checkJs": false
  → 把 .js 文件直接放进 TS 项目
  → 新文件用 .ts 写，旧文件暂时不动
  → 目标：项目能编译通过

  阶段 2：开启 JS 检查（1-2 周）
  ────────────────────────
  → "checkJs": true → 给 .js 文件做类型检查
  → 用 // @ts-ignore 临时跳过报错
  → 统计 @ts-ignore 数量 = 技术债看板
  → 目标：了解类型问题的规模

  阶段 3：逐文件迁移（2-4 周）
  ────────────────────────
  → 按依赖层级从底向上：utils → services → controllers
  → 每次改一个文件：.js → .ts + 加类型注解
  → 优先处理公共模块（被 import 最多的文件）
  → 目标：核心模块全部 .ts 化

  阶段 4：开启严格模式（1 周）
  ────────────────────────
  → "strict": true → 开启所有严格检查
  → 修复 strictNullChecks / noImplicitAny 报错
  → 去掉所有 @ts-ignore
  → 目标：零 any、零 ignore、全量类型覆盖
```

### 10.2 类型优先的 API 设计

```typescript
// ═══════════════════════════════════════
// 原则：先写类型，再写实现
// ═══════════════════════════════════════

// 步骤 1：定义数据模型
interface User {
  id: number;
  name: string;
  email: string;
  role: "admin" | "editor" | "viewer";
  createdAt: Date;
}

// 步骤 2：定义 API 接口契约
interface UserAPI {
  getUser(id: number): Promise<User | null>;
  listUsers(filter: {
    role?: User["role"];
    search?: string;
    page?: number;
    pageSize?: number;
  }): Promise<{ items: User[]; total: number }>;
  createUser(data: Omit<User, "id" | "createdAt">): Promise<User>;
  updateUser(id: number, data: Partial<Omit<User, "id">>): Promise<User>;
  deleteUser(id: number): Promise<void>;
}

// 步骤 3：实现——编译器确保你的实现与契约一致
class UserService implements UserAPI {
  // → 缺少方法 → 编译报错
  // → 参数类型不对 → 编译报错
  // → 返回类型不对 → 编译报错
  // ...
}

// → 类型是文档、是测试、是契约
// → 新同事看 UserAPI 接口就知道这个模块能做什么
```

### 10.3 反模式清单与规避策略

```typescript
// ═══════════════════════════════════════
// ❌ 反模式 1：any 污染
// ═══════════════════════════════════════

// 坏：
function parse(data: any): any { return JSON.parse(data); }
// → any 进去，any 出来，整条链路失去类型检查

// 好：
function parse<T>(data: string): T { return JSON.parse(data); }
// 更好（运行时校验）：
function parse(data: string): unknown { return JSON.parse(data); }
```

```typescript
// ═══════════════════════════════════════
// ❌ 反模式 2：不必要的类型断言
// ═══════════════════════════════════════

// 坏：
const user = getUser() as User;           // 如果返回 null 呢？

// 好：
const user = getUser();
if (user) { /* 使用 user */ }              // 编译器自动收窄

// 更好：
const user = getUser() ?? throwError("User not found");
```

```typescript
// ═══════════════════════════════════════
// ❌ 反模式 3：过度类型注解
// ═══════════════════════════════════════

// 坏（冗余注解）：
const name: string = "Alice";                          // string 是多余的
const numbers: number[] = [1, 2, 3].map((n: number): number => n * 2);

// 好（让编译器推断）：
const name = "Alice";                                  // 推断为 "Alice"
const numbers = [1, 2, 3].map((n) => n * 2);          // 推断为 number[]
```

```
反模式速查清单：

  ❌ any 到处飞              → 用 unknown + 类型守卫
  ❌ 过度 as 断言            → 用 if 收窄 + satisfies
  ❌ 非空断言 ! 滥用         → 用 ?? / ?. / assertDefined
  ❌ 冗余类型注解            → 信任编译器推断
  ❌ 数字枚举                → 用字符串枚举或联合类型
  ❌ interface 和 type 混用  → 选一种团队统一
  ❌ 忽略 strictNullChecks   → 一定要开
  ❌ 导出 any                → 公共 API 必须有精确类型
```

### 10.4 TypeScript 5.x 新特性与未来方向

```typescript
// ═══════════════════════════════════════
// TS 5.0：标准装饰器 + const 类型参数
// ═══════════════════════════════════════

// const 类型参数：让泛型推断出字面量类型
function createRoute<const T extends readonly string[]>(paths: T): T {
  return paths;
}

const routes = createRoute(["home", "about", "contact"]);
// → 类型是 readonly ["home", "about", "contact"]（而不是 string[]）
// → 不用写 as const，泛型自动推断字面量
```

```typescript
// ═══════════════════════════════════════
// TS 5.2+：using 声明（显式资源管理）
// ═══════════════════════════════════════

// 类似 Python 的 with 语句 / C# 的 using
class DatabaseConnection {
  [Symbol.dispose]() {
    console.log("Connection closed");
  }
}

function queryDB() {
  using conn = new DatabaseConnection();
  // ... 使用 conn
  // 函数结束时自动调用 conn[Symbol.dispose]()
}
// → 不需要 try/finally，自动清理资源
```

```
TypeScript 的未来方向：

  已落地：
  → 标准装饰器（5.0）
  → satisfies 运算符（4.9）
  → const 类型参数（5.0）
  → using 资源管理（5.2）

  进行中 / 讨论中：
  → 类型独立声明（isolatedDeclarations）→ 加速 .d.ts 生成
  → 模式匹配增强 → 更强的 infer 能力
  → 更好的 ESM 支持 → 简化模块配置

  生态趋势：
  → 运行时验证库（zod/valibot）与 TS 深度集成
  → 全栈类型安全（tRPC / Hono RPC）
  → 类型测试成为标配（vitest typecheck）
```

---

> 🎉 **全文完成**。从 JavaScript 的类型陷阱出发，经过环境搭建、基础类型、函数与对象、泛型、类型体操、实战模式、类与装饰器、声明文件，到工程化最佳实践——你已经掌握了 TypeScript 的核心知识体系。下一步：在真实项目中用起来，让编译器成为你最可靠的搭档。
