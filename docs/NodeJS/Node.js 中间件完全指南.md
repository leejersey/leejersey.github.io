# Node.js 中间件完全指南

> 从原理到实战：理解 Node.js 中间件模型，掌握 Express、Koa、NestJS 三大框架的中间件开发。

---

## 1. 中间件核心概念

在 Node.js 的 Web 框架中，中间件（Middleware）是处理 HTTP 请求的**核心机制**。每个请求从进入服务器到返回响应，都会经过一系列中间件函数——就像工厂的流水线，每个工位负责一道工序。

### 1.1 什么是中间件：req → middleware → res

中间件是一个函数，它可以**访问请求对象（req）、响应对象（res）和下一个中间件函数（next）**：

```javascript
// 最简单的中间件
function myMiddleware(req, res, next) {
  console.log('我是一个中间件');
  next(); // 调用下一个中间件
}
```

```
中间件在请求生命周期中的位置：

  客户端请求
    │
    ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ 中间件 1  │ → │ 中间件 2  │ → │ 中间件 3  │ → │ 路由处理  │
  │ (日志)    │   │ (认证)    │   │ (解析body)│   │ (业务)    │
  └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                     │
                                                     ▼
                                                  响应返回
```

### 1.2 中间件链与 next() 机制

`next()` 是中间件的核心——它把控制权交给下一个中间件。**不调用 next()，请求就卡住了**。

```javascript
// next() 的三种用法：
function middleware(req, res, next) {
  // 用法 1：放行——调用 next() 继续执行下一个中间件
  next();

  // 用法 2：短路——直接返回响应，不调用 next()
  res.status(401).json({ error: 'Unauthorized' });

  // 用法 3：报错——传参给 next()，跳到错误处理中间件
  next(new Error('Something went wrong'));
}
```

```
next() 的执行流程：

  app.use(A)    A 执行 → next() →
  app.use(B)                       B 执行 → next() →
  app.use(C)                                          C 执行 → 响应

  如果 B 不调用 next()：
  app.use(A)    A 执行 → next() →
  app.use(B)                       B 执行 → res.send() → 响应
  app.use(C)                       C 永远不会执行！（被 B 短路了）
```

### 1.3 中间件的分类

```
Node.js 中间件的四种类型：

  ① 应用级中间件
  → app.use(middleware)
  → 对所有请求生效
  → 典型：日志、CORS、body 解析

  ② 路由级中间件
  → router.use(middleware) 或挂在特定路由上
  → 只对匹配的路由生效
  → 典型：某个模块的认证检查

  ③ 错误处理中间件
  → function(err, req, res, next) ← 四个参数！
  → 只在 next(err) 被调用时触发
  → 典型：统一错误格式、错误日志

  ④ 第三方中间件
  → npm 安装，app.use() 注册
  → 典型：cors、helmet、morgan、compression
```

---

## 2. 从零手写一个中间件引擎

不用 Express，不用 Koa，只用 Node.js 原生的 `http` 模块——我们来手写一个中间件引擎，彻底搞懂 `use()` 和 `next()` 的底层原理。

### 2.1 原生 http 模块：没有中间件的痛苦

```javascript
// ═══════════════════════════════════════
// 没有中间件时，所有逻辑堆在一个回调里
// ═══════════════════════════════════════
const http = require('http');

const server = http.createServer((req, res) => {
  // 日志
  console.log(`${req.method} ${req.url}`);

  // 认证
  if (req.url.startsWith('/api/') && !req.headers.authorization) {
    res.writeHead(401);
    res.end(JSON.stringify({ error: 'Unauthorized' }));
    return;
  }

  // 路由
  if (req.url === '/api/users' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ users: ['Alice', 'Bob'] }));
  } else if (req.url === '/health') {
    res.writeHead(200);
    res.end('OK');
  } else {
    res.writeHead(404);
    res.end('Not Found');
  }
});

server.listen(3000);
// → 所有逻辑挤在一个函数里
// → 添加新功能 = 加更多 if-else
// → 无法复用、无法排序、无法拆分 → 这就是为什么需要中间件！
```

### 2.2 手写 Express 风格中间件引擎（线性模型）

```javascript
// ═══════════════════════════════════════
// MiniExpress：30 行实现中间件引擎
// ═══════════════════════════════════════
const http = require('http');

class MiniExpress {
  constructor() {
    this.middlewares = []; // 中间件数组
  }

  // 注册中间件
  use(fn) {
    this.middlewares.push(fn);
  }

  // 启动服务器
  listen(port, cb) {
    const server = http.createServer((req, res) => {
      this.handleRequest(req, res);
    });
    server.listen(port, cb);
  }

  // 核心：按顺序执行中间件
  handleRequest(req, res) {
    let index = 0;

    const next = () => {
      if (index >= this.middlewares.length) return; // 没有更多中间件了
      const middleware = this.middlewares[index++];  // 取出当前中间件并递增
      middleware(req, res, next);                    // 执行，把 next 传进去
    };

    next(); // 启动第一个中间件
  }
}
```

```javascript
// ═══════════════════════════════════════
// 使用 MiniExpress
// ═══════════════════════════════════════
const app = new MiniExpress();

// 中间件 1：日志
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`);
  next(); // 继续下一个
});

// 中间件 2：认证
app.use((req, res, next) => {
  if (req.url.startsWith('/api/') && !req.headers.authorization) {
    res.writeHead(401);
    res.end('Unauthorized');
    return; // 短路！不调用 next()
  }
  next();
});

// 中间件 3：路由处理
app.use((req, res, next) => {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ message: 'Hello!' }));
});

app.listen(3000, () => console.log('Server on :3000'));
// → 这就是 Express 的核心原理！
```

```
next() 的本质——递归调用：

  middlewares = [A, B, C]

  handleRequest():
    index = 0
    next() → middlewares[0] = A(req, res, next)
                                      │
                              A 调用 next()
                                      │
               next() → middlewares[1] = B(req, res, next)
                                                  │
                                          B 调用 next()
                                                  │
                           next() → middlewares[2] = C(req, res, next)

  → next() 就是"调用下一个函数"的递归机制
  → Express 源码的核心就是这个模式
```
### 2.3 手写 Koa 风格中间件引擎（洋葱模型）

```javascript
// ═══════════════════════════════════════
// MiniKoa：async/await 洋葱模型
// ═══════════════════════════════════════
const http = require('http');

class MiniKoa {
  constructor() {
    this.middlewares = [];
  }

  use(fn) {
    this.middlewares.push(fn);
  }

  // 核心：compose 组合中间件（Koa 源码的精髓）
  compose(middlewares) {
    return function (ctx) {
      let index = -1;

      function dispatch(i) {
        if (i <= index) return Promise.reject(new Error('next() 被多次调用'));
        index = i;

        const fn = middlewares[i];
        if (!fn) return Promise.resolve();

        // 关键：next = () => dispatch(i + 1)
        // → next() 返回 Promise，可以 await
        return Promise.resolve(fn(ctx, () => dispatch(i + 1)));
      }

      return dispatch(0);
    };
  }

  listen(port, cb) {
    const handler = this.compose(this.middlewares);

    const server = http.createServer(async (req, res) => {
      const ctx = { req, res }; // 简易上下文
      await handler(ctx);
    });

    server.listen(port, cb);
  }
}
```

```javascript
// ═══════════════════════════════════════
// 使用 MiniKoa——体验洋葱模型
// ═══════════════════════════════════════
const app = new MiniKoa();

// 中间件 1：计时（前半 + 后半）
app.use(async (ctx, next) => {
  const start = Date.now();
  console.log('→ 进入中间件 1');

  await next();  // 等待内层中间件全部执行完

  const duration = Date.now() - start;
  console.log(`← 离开中间件 1（耗时 ${duration}ms）`);
});

// 中间件 2：认证
app.use(async (ctx, next) => {
  console.log('→ 进入中间件 2');
  await next();
  console.log('← 离开中间件 2');
});

// 中间件 3：路由处理
app.use(async (ctx, next) => {
  console.log('→ 进入中间件 3（处理请求）');
  ctx.res.writeHead(200);
  ctx.res.end('Hello from MiniKoa!');
});

app.listen(3000);
// 控制台输出：
// → 进入中间件 1
// → 进入中间件 2
// → 进入中间件 3（处理请求）
// ← 离开中间件 2
// ← 离开中间件 1（耗时 3ms）
// → 这就是洋葱模型！先进后出
```
### 2.4 两种模型的本质区别

```
Express 线性模型 vs Koa 洋葱模型：

  Express（线性）：
  A → B → C → 响应
  → next() 是同步调用
  → 调用 next() 后，控制权就交出去了
  → 无法在 next() 之后可靠地做后处理

  Koa（洋葱）：
  A前 → B前 → C前 → 响应 → C后 → B后 → A后
  → next() 返回 Promise，可以 await
  → await next() 之后的代码在内层执行完才运行
  → 天然支持"前处理 + 后处理"（如计时、日志）
```

| 特性 | Express 线性模型 | Koa 洋葱模型 |
|------|:---:|:---:|
| **next() 返回值** | undefined | Promise |
| **后处理（next 之后的代码）** | 不可靠 | ✅ await next() 后执行 |
| **计时中间件** | 需要 hack | 天然支持 |
| **错误捕获** | next(err) 传递 | try/catch 包裹 await next() |
| **学习曲线** | 更简单 | 需理解 async/await |

> 💡 **一句话总结**：Express 的 next() 是"把球传出去就不管了"，Koa 的 await next() 是"把球传出去，等它回来再继续"。

---

## 3. Express 中间件

Express 是 Node.js 最流行的 Web 框架，它的中间件系统简单直观——就是我们在第 2 章手写的线性模型的完善版。

### 3.1 Express 中间件基础语法

```javascript
const express = require('express');
const app = express();

// ═══════════════════════════════════════
// 中间件的三种注册方式
// ═══════════════════════════════════════

// 方式 1：匹配所有路径
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`);
  next();
});

// 方式 2：匹配指定路径前缀
app.use('/api', (req, res, next) => {
  console.log('进入 /api 路由');
  next();
});

// 方式 3：挂在具体路由上
app.get('/users', (req, res, next) => {
  // 这也是一个中间件，只不过通常是最后一个（发送响应）
  res.json({ users: [] });
});
```

### 3.2 应用级 vs 路由级中间件

```javascript
const express = require('express');
const app = express();

// ═══════════════════════════════════════
// 应用级中间件：app.use()，全局生效
// ═══════════════════════════════════════
app.use(express.json()); // 所有路由都能解析 JSON body

// ═══════════════════════════════════════
// 路由级中间件：router.use()，模块化
// ═══════════════════════════════════════
const userRouter = express.Router();
const adminRouter = express.Router();

// 只在 userRouter 范围内生效的中间件
userRouter.use((req, res, next) => {
  console.log('User 模块中间件');
  next();
});

userRouter.get('/', (req, res) => res.json({ users: [] }));
userRouter.get('/:id', (req, res) => res.json({ id: req.params.id }));

// adminRouter 有自己的中间件
adminRouter.use((req, res, next) => {
  if (req.headers['x-admin-key'] !== 'secret') {
    return res.status(403).json({ error: 'Admin only' });
  }
  next();
});

adminRouter.get('/stats', (req, res) => res.json({ total: 100 }));

// 挂载路由
app.use('/api/users', userRouter);
app.use('/api/admin', adminRouter);

// → /api/users/* 走 userRouter 中间件
// → /api/admin/* 走 adminRouter 中间件（需要 admin key）
// → 路由级中间件让代码更模块化
```

### 3.3 错误处理中间件

Express 用**四个参数**来区分错误处理中间件——这是唯一的判断标准：

```javascript
// ═══════════════════════════════════════
// 错误处理中间件：必须有 4 个参数（err, req, res, next）
// ═══════════════════════════════════════

// 普通中间件中抛出错误
app.get('/api/users/:id', (req, res, next) => {
  const user = findUser(req.params.id);
  if (!user) {
    // 传错误给 next() → 跳到错误处理中间件
    return next(new Error('User not found'));
  }
  res.json(user);
});

// 异步路由中捕获错误（Express 5 之前需要手动 catch）
app.get('/api/data', async (req, res, next) => {
  try {
    const data = await fetchData();
    res.json(data);
  } catch (err) {
    next(err); // 传递给错误处理中间件
  }
});

// ═══════════════════════════════════════
// 错误处理中间件（放在所有路由之后！）
// ═══════════════════════════════════════
app.use((err, req, res, next) => {
  console.error(`[ERROR] ${req.method} ${req.url}: ${err.message}`);

  res.status(err.status || 500).json({
    error: err.message || 'Internal Server Error',
  });
});

// ⚠️ 注意：错误处理中间件必须放在最后面！
// → Express 遇到 next(err) 时，会跳过所有普通中间件，
//   直接找到第一个四参数中间件
```
### 3.4 常用内置与第三方中间件

```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');

const app = express();

// ═══════════════════════════════════════
// 内置中间件
// ═══════════════════════════════════════
app.use(express.json());                    // 解析 JSON body
app.use(express.urlencoded({ extended: true })); // 解析表单
app.use(express.static('public'));          // 静态文件服务

// ═══════════════════════════════════════
// 常用第三方中间件
// ═══════════════════════════════════════
app.use(cors());                // CORS 跨域
app.use(helmet());              // 安全响应头（X-Frame-Options 等）
app.use(morgan('dev'));         // 请求日志（dev 格式：简洁彩色）
app.use(compression());         // GZip 响应压缩

// npm install cors helmet morgan compression
```

```
Express 推荐的中间件注册顺序：

  1. helmet()          ← 安全头（最先）
  2. cors()            ← 跨域
  3. morgan('dev')     ← 日志
  4. compression()     ← 压缩
  5. express.json()    ← body 解析
  6. 自定义认证中间件    ← 认证
  7. 路由               ← 业务逻辑
  8. 404 处理           ← 未匹配路由
  9. 错误处理中间件      ← 必须放最后
```
### 3.5 实战：认证 + 日志 + 限流中间件

```javascript
const express = require('express');
const app = express();

// ═══════════════════════════════════════
// 中间件 1：请求日志
// ═══════════════════════════════════════
function logger(req, res, next) {
  const start = Date.now();

  // 监听响应完成事件
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${req.method} ${req.url} → ${res.statusCode} (${duration}ms)`);
  });

  next();
}

// ═══════════════════════════════════════
// 中间件 2：Token 认证
// ═══════════════════════════════════════
function auth(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (!token) {
    return res.status(401).json({ error: 'Missing token' });
  }

  // 实际项目用 jsonwebtoken 验证
  try {
    req.user = { id: 1, name: 'Alice' }; // 解码后的用户信息
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
}

// ═══════════════════════════════════════
// 中间件 3：IP 限流
// ═══════════════════════════════════════
function rateLimit({ windowMs = 60000, max = 60 } = {}) {
  const requests = new Map();

  return (req, res, next) => {
    const ip = req.ip;
    const now = Date.now();

    // 获取该 IP 的请求记录
    const record = requests.get(ip) || { count: 0, resetTime: now + windowMs };

    // 窗口过期，重置
    if (now > record.resetTime) {
      record.count = 0;
      record.resetTime = now + windowMs;
    }

    record.count++;
    requests.set(ip, record);

    if (record.count > max) {
      return res.status(429).json({ error: 'Too many requests' });
    }

    next();
  };
}

// ═══════════════════════════════════════
// 注册中间件 + 路由
// ═══════════════════════════════════════
app.use(logger);
app.use(rateLimit({ windowMs: 60000, max: 100 }));
app.use(express.json());

app.get('/health', (req, res) => res.json({ status: 'ok' }));
app.get('/api/profile', auth, (req, res) => {
  // auth 中间件挂在单个路由上（路由级）
  res.json({ user: req.user });
});

app.listen(3000);
```

> 💡 **Express 中间件小结**：注册用 `app.use()`，三参数是普通中间件，四参数是错误处理中间件。注意顺序——日志放前面，错误处理放最后。

---

## 4. Koa 中间件

Koa 是 Express 原班人马打造的下一代框架，核心改进就是中间件模型——从线性变成了**洋葱模型**。

### 4.1 洋葱模型与 async/await

```javascript
const Koa = require('koa');
const app = new Koa();

// ═══════════════════════════════════════
// Koa 中间件：async 函数 + await next()
// ═══════════════════════════════════════
app.use(async (ctx, next) => {
  console.log('→ 中间件 1 前半');
  await next();                    // 等待内层中间件全部执行完
  console.log('← 中间件 1 后半');  // 内层执行完才到这里
});

app.use(async (ctx, next) => {
  console.log('→ 中间件 2 前半');
  await next();
  console.log('← 中间件 2 后半');
});

app.use(async (ctx) => {
  console.log('● 路由处理');
  ctx.body = 'Hello Koa!';
});

app.listen(3000);
// 输出顺序：
// → 中间件 1 前半
// → 中间件 2 前半
// ● 路由处理
// ← 中间件 2 后半
// ← 中间件 1 后半
```

### 4.2 ctx 上下文与中间件组合

```javascript
// ═══════════════════════════════════════
// ctx（Context）整合了 req 和 res
// ═══════════════════════════════════════
app.use(async (ctx, next) => {
  // 请求信息
  ctx.method;          // GET / POST / ...
  ctx.url;             // /api/users
  ctx.headers;         // 请求头
  ctx.query;           // URL 查询参数 { page: '1' }
  ctx.request.body;    // 请求体（需要 koa-bodyparser）

  // 响应
  ctx.status = 200;
  ctx.body = { data: [] };  // 自动设置 Content-Type

  // 状态传递（替代 Express 的 req.user）
  ctx.state.user = { id: 1, name: 'Alice' };

  await next();
});
```

```javascript
// ═══════════════════════════════════════
// 常用 Koa 中间件生态
// ═══════════════════════════════════════
const Router = require('@koa/router');
const bodyParser = require('koa-bodyparser');
const cors = require('@koa/cors');

app.use(cors());              // 跨域
app.use(bodyParser());        // 解析请求体

const router = new Router();
router.get('/api/users', async (ctx) => {
  ctx.body = { users: [] };
});

app.use(router.routes());
app.use(router.allowedMethods());
```

### 4.3 Koa vs Express 中间件对比

| 特性 | Express | Koa |
|------|---------|-----|
| **中间件签名** | `(req, res, next)` | `async (ctx, next)` |
| **上下文** | req + res 分开 | ctx 统一封装 |
| **next()** | 同步调用，无返回值 | 返回 Promise，可 await |
| **后处理** | 不可靠（res.on('finish')） | ✅ await next() 之后 |
| **错误处理** | `(err, req, res, next)` 四参数 | try/catch 包裹 |
| **内置功能** | 多（json/static/urlencoded） | 极简（几乎什么都没有） |
| **生态** | 最大（npm 最多中间件） | 较小但够用 |

### 4.4 实战：请求计时 + 统一错误处理

```javascript
const Koa = require('koa');
const app = new Koa();

// ═══════════════════════════════════════
// 中间件 1：统一错误处理（放最外层）
// ═══════════════════════════════════════
app.use(async (ctx, next) => {
  try {
    await next();
  } catch (err) {
    ctx.status = err.status || 500;
    ctx.body = {
      error: err.message || 'Internal Server Error',
    };
    // Koa 内置的错误事件
    ctx.app.emit('error', err, ctx);
  }
});

// ═══════════════════════════════════════
// 中间件 2：请求计时 + 日志
// ═══════════════════════════════════════
app.use(async (ctx, next) => {
  const start = Date.now();

  await next();  // 等待业务处理完成

  const duration = Date.now() - start;
  ctx.set('X-Response-Time', `${duration}ms`);
  console.log(`${ctx.method} ${ctx.url} → ${ctx.status} (${duration}ms)`);
});

// ═══════════════════════════════════════
// 路由
// ═══════════════════════════════════════
app.use(async (ctx) => {
  if (ctx.url === '/error') {
    throw new Error('故意抛出的错误');
  }
  ctx.body = { message: 'Hello!' };
});

// 错误事件监听
app.on('error', (err) => {
  console.error('[Koa Error]', err.message);
});

app.listen(3000);
// → 洋葱模型让计时和错误处理变得极其自然
// → try/catch + await next() = 完美的错误边界
```

> 💡 **Koa 中间件小结**：洋葱模型天然支持前后处理，`await next()` 是核心。错误处理用 try/catch 比 Express 的四参数更直观。

---

## 5. NestJS 中间件与拦截器

NestJS 基于 Express（或 Fastify），但在中间件之上增加了**Guards、Interceptors、Pipes、Filters** 四层管道——比 Express 的中间件体系更精细。

### 5.1 NestJS 中间件基础

```typescript
// ═══════════════════════════════════════
// NestJS 中间件：实现 NestMiddleware 接口
// ═══════════════════════════════════════
import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';

@Injectable()
export class LoggerMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: NextFunction) {
    console.log(`${req.method} ${req.url}`);
    next();
  }
}

// 在 Module 中注册中间件
import { Module, MiddlewareConsumer } from '@nestjs/common';

@Module({})
export class AppModule {
  configure(consumer: MiddlewareConsumer) {
    consumer
      .apply(LoggerMiddleware)
      .forRoutes('*'); // 所有路由
      // .forRoutes('users')          → 只对 /users 生效
      // .exclude('health')           → 排除 /health
  }
}
```

### 5.2 Guards / Interceptors / Pipes / Filters

NestJS 的请求处理管道比 Express 更精细，分为 5 层：

```
NestJS 请求处理管道（按执行顺序）：

  请求 → Middleware → Guards → Interceptors(前) → Pipes → Handler
                                                           │
  响应 ←              Filters ← Interceptors(后) ←─────────┘

  每一层的职责：
  ┌──────────────┬────────────────────────────────────┐
  │ Middleware    │ 通用的前后处理（日志、CORS）         │
  │ Guards       │ 认证/授权（返回 true/false）         │
  │ Interceptors │ 响应转换、缓存、日志（洋葱模型）     │
  │ Pipes        │ 参数校验和转换（DTO 验证）           │
  │ Filters      │ 异常捕获和格式化                    │
  └──────────────┴────────────────────────────────────┘
```

### 5.3 中间件 vs 拦截器 vs 守卫：怎么选

| 需求 | 选择 | 原因 |
|------|------|------|
| 请求日志、CORS | **Middleware** | 全局通用，与业务无关 |
| 认证（JWT 验证） | **Guard** | 返回 boolean，语义清晰 |
| 角色权限（admin/user） | **Guard** | 可以读取路由元数据 |
| 响应格式统一包装 | **Interceptor** | 可以修改响应（洋葱模型） |
| 请求耗时统计 | **Interceptor** | 前后处理天然支持 |
| 参数校验（DTO） | **Pipe** | 与 class-validator 集成 |
| 统一错误格式 | **ExceptionFilter** | 捕获特定类型异常 |

### 5.4 实战：JWT 守卫 + 日志拦截器

```typescript
// ═══════════════════════════════════════
// Guard：JWT 认证守卫
// ═══════════════════════════════════════
import { CanActivate, ExecutionContext, Injectable, UnauthorizedException } from '@nestjs/common';

@Injectable()
export class AuthGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    const token = request.headers.authorization?.replace('Bearer ', '');

    if (!token) {
      throw new UnauthorizedException('Missing token');
    }

    // 实际项目用 jsonwebtoken 验证
    request.user = { id: 1, name: 'Alice' };
    return true; // true = 放行，false = 拒绝
  }
}

// 使用：挂在 Controller 或单个路由上
@Controller('users')
@UseGuards(AuthGuard) // 整个 Controller 需要认证
export class UserController {
  @Get()
  findAll() { return []; }
}
```

```typescript
// ═══════════════════════════════════════
// Interceptor：日志 + 响应包装
// ═══════════════════════════════════════
import { CallHandler, ExecutionContext, Injectable, NestInterceptor } from '@nestjs/common';
import { Observable, tap, map } from 'rxjs';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const req = context.switchToHttp().getRequest();
    const start = Date.now();

    return next.handle().pipe(
      tap(() => {
        const duration = Date.now() - start;
        console.log(`${req.method} ${req.url} (${duration}ms)`);
      }),
      // 统一包装响应格式
      map((data) => ({
        code: 200,
        data,
        timestamp: new Date().toISOString(),
      })),
    );
  }
}

// 全局注册
app.useGlobalInterceptors(new LoggingInterceptor());
// → 所有路由的响应自动变成 { code: 200, data: ..., timestamp: ... }
```

> 💡 **NestJS 中间件小结**：简单的全局逻辑用 Middleware，认证用 Guard，响应处理用 Interceptor，参数校验用 Pipe，错误处理用 Filter。五层管道各司其职。

---

## 6. 最佳实践与常见陷阱

### 6.1 中间件设计原则

```
Node.js 中间件设计的 5 个原则：

  ① 保持轻量
  → 中间件对每个请求都执行，避免阻塞事件循环
  → 不要在中间件中做 CPU 密集型操作（如加密、图片处理）
  → 数据库查询用缓存，文件读取用流

  ② 单一职责
  → 一个中间件只做一件事
  → 日志中间件不应该顺带做认证

  ③ 可配置
  → 用工厂函数返回中间件，支持参数配置
  → rateLimit({ max: 100, windowMs: 60000 })
  → 而不是硬编码在中间件内部

  ④ 顺序敏感
  → 日志 → 安全头 → CORS → body解析 → 认证 → 路由 → 错误处理
  → body 解析必须在路由之前（否则 req.body 是 undefined）

  ⑤ 错误安全
  → 中间件自身的错误不应该导致进程崩溃
  → 异步中间件必须捕获 Promise rejection
```

### 6.2 常见陷阱与排错

```javascript
// ═══════════════════════════════════════
// 陷阱 1：异步中间件忘记错误处理（Express）
// ═══════════════════════════════════════

// ❌ 错误：async 函数中抛出异常，Express 不会捕获
app.use(async (req, res, next) => {
  const data = await fetchData(); // 如果抛出异常 → 进程卡死
  next();
});

// ✅ 正确：用 try/catch 包裹
app.use(async (req, res, next) => {
  try {
    const data = await fetchData();
    next();
  } catch (err) {
    next(err); // 传递给错误处理中间件
  }
});

// ✅ 更好：用包装函数
const asyncHandler = (fn) => (req, res, next) =>
  Promise.resolve(fn(req, res, next)).catch(next);

app.use(asyncHandler(async (req, res, next) => {
  const data = await fetchData(); // 异常自动传给 next(err)
  next();
}));
```

```javascript
// ═══════════════════════════════════════
// 陷阱 2：next() 之后还在执行代码
// ═══════════════════════════════════════

// ❌ 错误：next() 之后的代码仍然会执行
app.use((req, res, next) => {
  if (!req.headers.authorization) {
    res.status(401).json({ error: 'Unauthorized' });
    next(); // 不应该调用 next()！响应已经发送了
  }
  next();
});

// ✅ 正确：用 return 终止
app.use((req, res, next) => {
  if (!req.headers.authorization) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
});
```

```javascript
// ═══════════════════════════════════════
// 陷阱 3：中间件注册顺序错误
// ═══════════════════════════════════════

// ❌ 错误：路由在 body 解析之前
app.get('/api/users', (req, res) => {
  console.log(req.body); // undefined！还没解析
});
app.use(express.json()); // 太晚了

// ✅ 正确：body 解析在路由之前
app.use(express.json());
app.get('/api/users', (req, res) => {
  console.log(req.body); // ✅ 正确解析
});
```

### 6.3 三大框架中间件对比总表

| 特性 | Express | Koa | NestJS |
|------|---------|-----|--------|
| **中间件模型** | 线性（单向） | 洋葱（双向） | 分层管道 |
| **中间件签名** | `(req, res, next)` | `async (ctx, next)` | `use(req, res, next)` |
| **next() 返回值** | undefined | Promise | void |
| **后处理支持** | 不可靠 | ✅ await next() 后 | ✅ Interceptor |
| **错误处理** | 四参数中间件 | try/catch | ExceptionFilter |
| **认证机制** | 中间件 | 中间件 | Guard（专用层） |
| **参数校验** | 中间件/手动 | 中间件/手动 | Pipe（专用层） |
| **响应转换** | 中间件 | 中间件 | Interceptor（专用层） |
| **TypeScript** | 需额外配置 | 需额外配置 | 原生支持 |
| **适合项目** | 小中型、API | 中型、注重优雅 | 大型企业级 |

---

> 🎉 **全文完成**。中间件是 Node.js Web 开发的基石——Express 的线性模型简单直接，Koa 的洋葱模型优雅强大，NestJS 的分层管道企业级专业。理解了底层的 `use()` + `next()` 机制，切换任何框架都能快速上手。
