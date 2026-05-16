# Node.js 进程与集群

> 单线程不是终点——掌握 child_process、Worker Threads、Cluster 三大多核利用方案，用 PM2 管理生产级 Node.js 应用。

---

## 1. 单线程的瓶颈与突破方向

### 1.1 回顾：为什么 Node.js 是单线程

```
Node.js 的线程模型：

  ┌──────────────────────────────────────┐
  │           Node.js 进程               │
  │                                      │
  │  ┌──────────────────────┐            │
  │  │  主线程（JS 执行）     │ ← 你的代码 │
  │  │  事件循环 + V8        │            │
  │  └──────────────────────┘            │
  │                                      │
  │  ┌──┬──┬──┬──┐                      │
  │  │T1│T2│T3│T4│ ← libuv 线程池       │
  │  └──┴──┴──┴──┘   (文件I/O、DNS等)    │
  │                                      │
  └──────────────────────────────────────┘
  
  关键：你的 JS 代码只在主线程上跑
```

### 1.2 问题：CPU 密集型任务阻塞事件循环

```javascript
const http = require('http');

const server = http.createServer((req, res) => {
  if (req.url === '/heavy') {
    // ❌ CPU 密集型：阻塞主线程 5 秒
    const start = Date.now();
    while (Date.now() - start < 5000) {} // 模拟计算
    res.end('计算完成');
  } else {
    res.end('Hello');  // 这个请求也要等 5 秒！
  }
});

server.listen(3000);
// 访问 /heavy 时，所有其他请求都被阻塞
```

```
阻塞事件循环的常见场景：

  1. 大量数据的 JSON.parse / JSON.stringify
  2. 加密/哈希计算（同步版本）
  3. 图片处理（缩放、格式转换）
  4. 复杂正则匹配
  5. 大数据排序/聚合
```

### 1.3 三条路：child_process / Worker Threads / Cluster

| | child_process | Worker Threads | Cluster |
|---|---|---|---|
| **本质** | 独立进程 | 同进程内的线程 | 多个进程监听同端口 |
| **内存** | 独立（不共享） | 可共享（SharedArrayBuffer） | 独立 |
| **启动开销** | 大（~30ms） | 中（~5ms） | 大 |
| **通信** | IPC / stdio | postMessage / 共享内存 | IPC |
| **适合** | 运行外部命令、隔离 | CPU 密集型计算 | HTTP 多核负载均衡 |
| **崩溃影响** | 不影响主进程 | 不影响主线程 | 不影响其他 Worker |

```
选择决策树：

  需要运行系统命令？ → child_process (exec/spawn)
  需要 CPU 密集计算？ → Worker Threads
  需要多核处理 HTTP？ → Cluster / PM2
  需要跨语言（Python等）？ → child_process (spawn)
```

---

## 2. child_process：子进程

### 2.1 exec 与 execFile：执行系统命令

```javascript
const { exec, execFile } = require('child_process');

// exec：通过 shell 执行（支持管道、通配符）
exec('ls -la | grep .js', (error, stdout, stderr) => {
  if (error) {
    console.error(`执行失败: ${error.message}`);
    return;
  }
  console.log(stdout);
});

// execFile：直接执行可执行文件（不经过 shell，更安全）
execFile('node', ['--version'], (error, stdout) => {
  console.log(`Node 版本: ${stdout.trim()}`);
});

// Promise 封装
const { promisify } = require('util');
const execAsync = promisify(exec);

async function getGitLog() {
  const { stdout } = await execAsync('git log -5 --oneline');
  return stdout.trim().split('\n');
}
```

exec vs execFile：

| | exec | execFile |
|---|---|---|
| **Shell** | ✅ 经过 shell | ❌ 直接执行 |
| **管道/通配符** | ✅ 支持 | ❌ 不支持 |
| **安全性** | ⚠️ 可能注入 | ✅ 更安全 |
| **输出** | 缓冲到内存 | 缓冲到内存 |

> ⚠️ `exec` 有输出缓冲上限（默认 1MB）。大输出用 `spawn`。

### 2.2 spawn：流式子进程（大数据量）

```javascript
const { spawn } = require('child_process');

// spawn 返回的子进程有 stdin/stdout/stderr 流
const child = spawn('find', ['.', '-name', '*.js']);

// stdout 是 Readable Stream
child.stdout.on('data', (data) => {
  console.log(`输出: ${data}`);
});

child.stderr.on('data', (data) => {
  console.error(`错误: ${data}`);
});

child.on('close', (code) => {
  console.log(`退出码: ${code}`);
});
```

实战：调用 Python 脚本

```javascript
function runPython(script, args = []) {
  return new Promise((resolve, reject) => {
    const child = spawn('python3', [script, ...args]);
    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => { stdout += data; });
    child.stderr.on('data', (data) => { stderr += data; });

    child.on('close', (code) => {
      if (code === 0) resolve(stdout.trim());
      else reject(new Error(`Python 退出 ${code}: ${stderr}`));
    });
  });
}

// 使用
const result = await runPython('analysis.py', ['--input', 'data.csv']);
```

流式管道（等效 `cat file | grep error | wc -l`）：

```javascript
const cat = spawn('cat', ['server.log']);
const grep = spawn('grep', ['ERROR']);
const wc = spawn('wc', ['-l']);

cat.stdout.pipe(grep.stdin);
grep.stdout.pipe(wc.stdin);

wc.stdout.on('data', (data) => {
  console.log(`错误行数: ${data.toString().trim()}`);
});
```

### 2.3 fork：Node.js 专属子进程 + IPC 通信

`fork()` 是 `spawn()` 的特化版——专门用于启动 Node.js 子进程，**自动建立 IPC 通道**：

```javascript
// ── master.js ──
const { fork } = require('child_process');

const worker = fork('./worker.js');

// 发送消息给子进程
worker.send({ type: 'compute', data: [1, 2, 3, 4, 5] });

// 接收子进程的响应
worker.on('message', (msg) => {
  console.log('子进程返回:', msg);  // { result: 15 }
});

worker.on('exit', (code) => {
  console.log(`子进程退出: ${code}`);
});
```

```javascript
// ── worker.js ──
process.on('message', (msg) => {
  if (msg.type === 'compute') {
    const result = msg.data.reduce((a, b) => a + b, 0);
    // 发送结果回主进程
    process.send({ result });
  }
});
```

```
fork 的 IPC 通道：

  主进程                      子进程
  ┌──────────┐    IPC       ┌──────────┐
  │ master.js│ ←─────────→ │ worker.js│
  │          │  send/on     │          │
  │          │  message     │          │
  └──────────┘              └──────────┘
  
  IPC = Inter-Process Communication
  底层通过 Unix Domain Socket 或 Windows Named Pipe
```

### 2.4 子进程生命周期与错误处理

```javascript
const { spawn } = require('child_process');

function createManagedProcess(command, args) {
  const child = spawn(command, args, {
    stdio: ['pipe', 'pipe', 'pipe'],
    detached: false,
  });

  // 错误事件（启动失败）
  child.on('error', (err) => {
    console.error(`启动失败: ${err.message}`);
    // 常见：ENOENT（命令不存在）
  });

  // 退出事件
  child.on('exit', (code, signal) => {
    if (signal) {
      console.log(`被信号终止: ${signal}`);
    } else if (code !== 0) {
      console.log(`异常退出: ${code}`);
    }
  });

  // 超时强制终止
  const timeout = setTimeout(() => {
    child.kill('SIGTERM');
    setTimeout(() => {
      if (!child.killed) child.kill('SIGKILL');
    }, 5000);
  }, 30000);

  child.on('close', () => clearTimeout(timeout));

  return child;
}
```

四种创建方式速查：

| 方法 | 输出方式 | Shell | 适合 |
|---|---|---|---|
| `exec` | 缓冲 | ✅ | 短命令，小输出 |
| `execFile` | 缓冲 | ❌ | 直接执行，更安全 |
| `spawn` | 流式 | 可选 | 大输出，长时间运行 |
| `fork` | IPC | ❌ | Node.js 子进程通信 |

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| exec | Shell 执行，缓冲输出，有 1MB 上限 |
| spawn | 流式 stdout/stderr，适合大数据量 |
| fork | Node.js 专属，自动 IPC 通道 |
| 管道 | `child1.stdout.pipe(child2.stdin)` |
| 生命周期 | error → exit → close 事件 |

> **下一章**：Worker Threads——同进程内的多线程，SharedArrayBuffer 共享内存，手写线程池。

---

## 3. Worker Threads：工作线程

### 3.1 进程 vs 线程：开销与适用场景

```
进程（child_process / fork）：
  ┌──────────┐    ┌──────────┐
  │ 进程 A    │    │ 进程 B    │
  │ V8 引擎   │    │ V8 引擎   │  ← 各自有独立的 V8 实例
  │ 堆内存    │    │ 堆内存    │  ← 内存完全隔离
  └──────────┘    └──────────┘
       ↕ IPC（序列化/反序列化）

线程（Worker Threads）：
  ┌────────────────────────────┐
  │         同一个进程          │
  │  ┌─────────┐ ┌─────────┐  │
  │  │ 主线程   │ │ Worker  │  │  ← 各自有独立的 V8 实例
  │  │ V8 + 堆  │ │ V8 + 堆 │  │  ← 但可以共享 ArrayBuffer
  │  └─────────┘ └─────────┘  │
  │     ↕ postMessage          │
  │     ↕ SharedArrayBuffer    │  ← 零拷贝共享内存
  └────────────────────────────┘
```

| | child_process | Worker Threads |
|---|---|---|
| **启动时间** | ~30ms | ~5ms |
| **内存开销** | ~30MB / 进程 | ~5MB / 线程 |
| **数据共享** | 序列化拷贝 | 可共享内存 |
| **崩溃隔离** | ✅ 进程独立 | ⚠️ 线程崩溃不影响主线程 |
| **适合** | 外部命令、强隔离 | CPU 计算、大量并行 |

### 3.2 Worker 基础：创建、消息传递、错误处理

```javascript
// ── main.js ──
const { Worker, isMainThread, parentPort } = require('worker_threads');

if (isMainThread) {
  // 主线程：创建 Worker
  const worker = new Worker('./worker.js', {
    workerData: { numbers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] }
  });

  worker.on('message', (result) => {
    console.log('计算结果:', result);  // 55
  });

  worker.on('error', (err) => {
    console.error('Worker 出错:', err);
  });

  worker.on('exit', (code) => {
    if (code !== 0) console.error(`Worker 异常退出: ${code}`);
  });
}
```

```javascript
// ── worker.js ──
const { workerData, parentPort } = require('worker_threads');

// CPU 密集计算
const sum = workerData.numbers.reduce((a, b) => a + b, 0);

// 发送结果回主线程
parentPort.postMessage(sum);
```

单文件写法（内联 Worker）：

```javascript
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

if (isMainThread) {
  // 主线程
  const worker = new Worker(__filename, {
    workerData: { n: 40 }
  });
  worker.on('message', (result) => console.log(`fib(40) = ${result}`));
} else {
  // Worker 线程
  function fib(n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
  }
  parentPort.postMessage(fib(workerData.n));
}
```

### 3.3 SharedArrayBuffer 与 Atomics：共享内存

普通 `postMessage` 传递的数据是**拷贝**的。`SharedArrayBuffer` 实现零拷贝共享：

```javascript
const { Worker, isMainThread, workerData } = require('worker_threads');

if (isMainThread) {
  // 创建共享内存（4 个 Int32 = 16 字节）
  const shared = new SharedArrayBuffer(4 * Int32Array.BYTES_PER_ELEMENT);
  const arr = new Int32Array(shared);

  // 多个 Worker 同时操作同一块内存
  const workers = [];
  for (let i = 0; i < 4; i++) {
    const w = new Worker(__filename, { workerData: { shared, index: i } });
    workers.push(w);
  }

  // 等所有 Worker 完成
  Promise.all(workers.map(w => new Promise(r => w.on('exit', r)))).then(() => {
    console.log('共享数组:', Array.from(arr));  // [100, 101, 102, 103]
  });
} else {
  const arr = new Int32Array(workerData.shared);
  // 原子操作：线程安全
  Atomics.store(arr, workerData.index, 100 + workerData.index);
}
```

```
SharedArrayBuffer vs postMessage：

  postMessage:
    主线程 {data} ──序列化──> 拷贝 ──反序列化──> Worker
    → 数据量大时开销巨大

  SharedArrayBuffer:
    主线程 ──────→ [共享内存] ←────── Worker
    → 零拷贝，但需要 Atomics 保证线程安全
```

### 3.4 实战：手写线程池（CPU 密集型任务分发）

```javascript
const { Worker } = require('worker_threads');
const os = require('os');

class ThreadPool {
  constructor(workerScript, size = os.cpus().length) {
    this.workerScript = workerScript;
    this.size = size;
    this.workers = [];
    this.queue = [];
    this.activeCount = 0;

    // 预创建线程
    for (let i = 0; i < size; i++) {
      this._createWorker();
    }
  }

  _createWorker() {
    const worker = new Worker(this.workerScript);
    worker.busy = false;

    worker.on('message', (result) => {
      worker.busy = false;
      worker._resolve(result);
      this.activeCount--;
      this._next();
    });

    worker.on('error', (err) => {
      worker.busy = false;
      worker._reject(err);
      this.activeCount--;
      this._next();
    });

    this.workers.push(worker);
  }

  _next() {
    if (this.queue.length === 0) return;
    const idle = this.workers.find(w => !w.busy);
    if (!idle) return;

    const { data, resolve, reject } = this.queue.shift();
    idle.busy = true;
    idle._resolve = resolve;
    idle._reject = reject;
    this.activeCount++;
    idle.postMessage(data);
  }

  run(data) {
    return new Promise((resolve, reject) => {
      this.queue.push({ data, resolve, reject });
      this._next();
    });
  }

  async destroy() {
    await Promise.all(this.workers.map(w => w.terminate()));
  }
}

// 使用
const pool = new ThreadPool('./compute-worker.js', 4);

const results = await Promise.all([
  pool.run({ type: 'fib', n: 40 }),
  pool.run({ type: 'fib', n: 41 }),
  pool.run({ type: 'fib', n: 42 }),
  pool.run({ type: 'fib', n: 43 }),
]);

console.log(results);
await pool.destroy();
```

```javascript
// ── compute-worker.js ──
const { parentPort } = require('worker_threads');

function fib(n) {
  if (n <= 1) return n;
  return fib(n - 1) + fib(n - 2);
}

parentPort.on('message', (msg) => {
  if (msg.type === 'fib') {
    parentPort.postMessage(fib(msg.n));
  }
});
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Worker 基础 | `new Worker()` + `postMessage` + `on('message')` |
| workerData | 创建时传入初始数据 |
| SharedArrayBuffer | 零拷贝共享内存，需 Atomics 保证线程安全 |
| 线程池 | 预创建 + 任务队列 + 空闲分发 |
| 适用场景 | CPU 密集计算（加密、图片处理、大数据聚合） |

---

## 4. Cluster 模块：多进程服务器

### 4.1 Cluster 原理：一个端口多个进程

```
Cluster 的工作原理：

  ┌─────────────────────────────────────────┐
  │            Master 进程                   │
  │                                          │
  │  监听端口 3000                            │
  │  接收连接 → 分发给 Worker                 │
  │                                          │
  │  ┌──────────┬──────────┬──────────┐     │
  │  │ Worker 1 │ Worker 2 │ Worker 3 │     │
  │  │ (进程)   │ (进程)   │ (进程)   │     │
  │  │ HTTP处理 │ HTTP处理 │ HTTP处理 │     │
  │  └──────────┴──────────┴──────────┘     │
  └─────────────────────────────────────────┘

  负载均衡策略（Linux/macOS 默认）：
  Round-Robin → 轮询分配连接给各 Worker
```

### 4.2 Master-Worker 模式完整实现

```javascript
const cluster = require('cluster');
const http = require('http');
const os = require('os');

const numCPUs = os.cpus().length;

if (cluster.isPrimary) {
  // ── Master 进程 ──
  console.log(`Master ${process.pid} 启动，CPU 核数: ${numCPUs}`);

  // 创建 Worker
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }

  // 监听 Worker 退出
  cluster.on('exit', (worker, code, signal) => {
    console.log(`Worker ${worker.process.pid} 退出 (${signal || code})`);
    // 自动重启
    console.log('正在重启新 Worker...');
    cluster.fork();
  });

  // 监听 Worker 上线
  cluster.on('online', (worker) => {
    console.log(`Worker ${worker.process.pid} 上线`);
  });

} else {
  // ── Worker 进程 ──
  const server = http.createServer((req, res) => {
    res.writeHead(200);
    res.end(`Worker ${process.pid} 处理\n`);
  });

  server.listen(3000);
  console.log(`Worker ${process.pid} 监听端口 3000`);
}
```

```bash
# 运行
node cluster-server.js

# 输出：
# Master 12345 启动，CPU 核数: 8
# Worker 12346 监听端口 3000
# Worker 12347 监听端口 3000
# ...（8 个 Worker）

# 测试
curl http://localhost:3000  # Worker 12346 处理
curl http://localhost:3000  # Worker 12347 处理（轮询）
```

### 4.3 优雅重启与零停机部署

```javascript
if (cluster.isPrimary) {
  const workers = [];

  function forkWorker() {
    const worker = cluster.fork();
    workers.push(worker);
    return worker;
  }

  // 初始化
  for (let i = 0; i < numCPUs; i++) {
    forkWorker();
  }

  // 零停机重启：逐个替换 Worker
  process.on('SIGUSR2', () => {
    console.log('收到 SIGUSR2，开始滚动重启...');

    const oldWorkers = [...Object.values(cluster.workers)];

    function restartNext(i) {
      if (i >= oldWorkers.length) {
        console.log('滚动重启完成');
        return;
      }

      const newWorker = cluster.fork();
      newWorker.on('listening', () => {
        // 新 Worker 就绪后，再关闭旧的
        oldWorkers[i].send('graceful-shutdown');
        oldWorkers[i].disconnect();
        setTimeout(() => {
          if (!oldWorkers[i].isDead()) oldWorkers[i].kill();
        }, 5000);
        restartNext(i + 1);
      });
    }

    restartNext(0);
  });
}

// Worker 端：优雅关闭
if (!cluster.isPrimary) {
  const server = http.createServer(handler);
  server.listen(3000);

  process.on('message', (msg) => {
    if (msg === 'graceful-shutdown') {
      // 停止接收新连接
      server.close(() => {
        console.log(`Worker ${process.pid} 优雅退出`);
        process.exit(0);
      });
    }
  });
}
```

```bash
# 发送信号触发滚动重启
kill -SIGUSR2 <master-pid>
```

### 4.4 Sticky Session：WebSocket 场景

WebSocket 是长连接，需要同一客户端始终连接到同一 Worker：

```javascript
const cluster = require('cluster');
const net = require('net');
const http = require('http');

if (cluster.isPrimary) {
  const workers = [];
  for (let i = 0; i < numCPUs; i++) {
    workers.push(cluster.fork());
  }

  // 自定义负载均衡：基于 IP 的 Sticky
  const server = net.createServer({ pauseOnConnect: true }, (conn) => {
    const ip = conn.remoteAddress;
    // 用 IP 哈希选择固定 Worker
    const index = hashCode(ip) % workers.length;
    workers[index].send('sticky-session', conn);
  });

  server.listen(3000);

  function hashCode(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash);
  }
} else {
  const server = http.createServer((req, res) => {
    res.end(`Worker ${process.pid}`);
  });

  // 接收 Master 转发的连接
  process.on('message', (msg, conn) => {
    if (msg === 'sticky-session') {
      server.emit('connection', conn);
      conn.resume();
    }
  });
}
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Cluster 原理 | Master 监听端口 → 轮询分发给 Worker 进程 |
| 自动重启 | `cluster.on('exit')` 中 `cluster.fork()` |
| 零停机重启 | SIGUSR2 → 逐个 fork 新 Worker → 关闭旧 Worker |
| Sticky Session | IP 哈希选择固定 Worker，WebSocket 必需 |

> **下一章**：PM2——生产级进程管理，ecosystem 配置，集群模式与监控。

---

## 5. PM2：生产级进程管理

### 5.1 PM2 基础：启动、停止、重启、日志

```bash
# 安装
npm install -g pm2

# 启动应用
pm2 start app.js
pm2 start app.js --name "api-server"   # 指定名称
pm2 start app.js -i max               # 集群模式（CPU 核数个进程）
pm2 start app.js -i 4                 # 集群模式（4 个进程）

# 管理
pm2 list                               # 查看所有进程
pm2 stop api-server                    # 停止
pm2 restart api-server                 # 重启
pm2 reload api-server                  # 零停机重启（集群模式）
pm2 delete api-server                  # 删除

# 日志
pm2 logs                               # 查看所有日志
pm2 logs api-server --lines 100        # 指定应用最近 100 行
pm2 flush                              # 清空日志

# 监控
pm2 monit                              # 实时监控面板（CPU/内存）
```

```
pm2 list 输出示例：

┌─────┬──────────────┬─────┬──────┬───────┬──────────┬─────────┐
│ id  │ name         │mode │ ↺    │ status│ cpu      │ memory  │
├─────┼──────────────┼─────┼──────┼───────┼──────────┼─────────┤
│ 0   │ api-server   │cluster│ 0   │ online│ 0.1%     │ 45.2 MB │
│ 1   │ api-server   │cluster│ 0   │ online│ 0.2%     │ 43.8 MB │
│ 2   │ api-server   │cluster│ 0   │ online│ 0.1%     │ 44.1 MB │
│ 3   │ api-server   │cluster│ 0   │ online│ 0.3%     │ 45.0 MB │
└─────┴──────────────┴─────┴──────┴───────┴──────────┴─────────┘
```

### 5.2 ecosystem.config.js 配置详解

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'api-server',
      script: './src/app.js',
      instances: 'max',           // 集群模式，CPU 核数个进程
      exec_mode: 'cluster',       // cluster | fork

      // 环境变量
      env: {
        NODE_ENV: 'development',
        PORT: 3000,
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 8080,
      },

      // 自动重启
      watch: false,               // 生产环境关闭 watch
      max_memory_restart: '500M', // 内存超 500MB 自动重启
      max_restarts: 10,           // 最大重启次数
      min_uptime: '5s',           // 最小存活时间（低于此视为崩溃）

      // 日志
      log_file: './logs/combined.log',
      error_file: './logs/error.log',
      out_file: './logs/out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,           // 集群模式合并日志

      // 优雅关闭
      kill_timeout: 5000,         // 优雅关闭等待时间
      listen_timeout: 3000,       // 等待 ready 信号超时
      wait_ready: true,           // 等待 process.send('ready')
    },
    {
      name: 'worker',
      script: './src/worker.js',
      instances: 2,
      exec_mode: 'fork',          // 后台任务用 fork 模式
      cron_restart: '0 3 * * *',  // 每天凌晨 3 点重启
      autorestart: true,
    },
  ],
};
```

```bash
# 使用 ecosystem 配置
pm2 start ecosystem.config.js
pm2 start ecosystem.config.js --env production
pm2 restart ecosystem.config.js
pm2 delete ecosystem.config.js

# 开机自启
pm2 startup                    # 生成开机脚本
pm2 save                       # 保存当前进程列表
```

### 5.3 集群模式与负载均衡

```bash
# 启动 4 个集群实例
pm2 start app.js -i 4

# 动态调整实例数
pm2 scale api-server 8         # 扩容到 8 个
pm2 scale api-server +2        # 增加 2 个

# 零停机重启（逐个重启 Worker）
pm2 reload api-server          # ← 生产环境用 reload 而不是 restart
```

```
pm2 reload vs restart：

  restart：
    停止所有 → 启动所有 → 有短暂停机

  reload（仅 cluster 模式）：
    启动新 Worker → 新 Worker 就绪 → 关闭旧 Worker → 逐个替换
    → 零停机
```

应用端配合优雅关闭：

```javascript
// app.js
const server = app.listen(3000, () => {
  // 告诉 PM2：我已准备好接收请求
  process.send('ready');
});

// 收到 PM2 的关闭信号
process.on('SIGINT', () => {
  console.log('收到关闭信号，优雅退出...');
  server.close(() => {
    // 关闭数据库连接等
    process.exit(0);
  });
});
```

### 5.4 监控、告警与自动重启

```bash
# 实时监控
pm2 monit

# 查看详细信息
pm2 show api-server

# 输出包含：
# - 重启次数、运行时间
# - CPU/内存使用
# - 日志路径
# - Git 信息
```

PM2 内置的保护机制：

| 配置 | 说明 |
|---|---|
| `max_memory_restart` | 内存超限自动重启 |
| `max_restarts` | 最大连续重启次数（防止死循环） |
| `min_uptime` | 启动后存活不足此时间视为崩溃 |
| `restart_delay` | 重启间隔（指数退避） |
| `cron_restart` | 定时重启（清理内存泄漏） |

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 核心命令 | start / stop / restart / reload / logs / monit |
| ecosystem | 统一配置多个应用，支持环境变量切换 |
| reload | 零停机重启，配合 `process.send('ready')` |
| 自动重启 | 内存超限 / 崩溃检测 / 定时重启 |

---

## 6. 进程间通信模式

### 6.1 IPC Channel：父子进程通信

```javascript
// 最常用：fork + send/on message
const { fork } = require('child_process');

const worker = fork('./task.js');

// 主进程 → 子进程
worker.send({ type: 'task', payload: { userId: 1001 } });

// 子进程 → 主进程
worker.on('message', (msg) => {
  if (msg.type === 'result') {
    console.log('任务完成:', msg.data);
  }
});
```

```
IPC 适用范围：

  ✅ 同一台机器的父子进程
  ✅ 结构化数据（JSON 序列化）
  ❌ 无关联的进程
  ❌ 跨机器
  ❌ 大数据量（序列化开销）
```

### 6.2 共享内存：Worker Threads 高性能方案

```javascript
// 大数据量的高性能通信：SharedArrayBuffer
const { Worker } = require('worker_threads');

// 100 万个 Float64 数据，共享而非拷贝
const shared = new SharedArrayBuffer(1_000_000 * Float64Array.BYTES_PER_ELEMENT);
const data = new Float64Array(shared);

// 主线程写入数据
for (let i = 0; i < data.length; i++) {
  data[i] = Math.random();
}

// Worker 直接读取，零拷贝
const worker = new Worker('./stats-worker.js', {
  workerData: { shared }
});

worker.on('message', ({ mean, max, min }) => {
  console.log(`均值: ${mean}, 最大: ${max}, 最小: ${min}`);
});
```

### 6.3 Redis Pub/Sub：跨机器通信

当你有多台服务器时，IPC 不够用了——用 Redis：

```javascript
const Redis = require('ioredis');

// ── 发布端（服务器 A）──
const pub = new Redis();
await pub.publish('events', JSON.stringify({
  type: 'user-login',
  userId: 1001,
  server: 'server-a',
}));

// ── 订阅端（服务器 B）──
const sub = new Redis();
sub.subscribe('events');
sub.on('message', (channel, message) => {
  const event = JSON.parse(message);
  console.log(`收到事件: ${event.type} from ${event.server}`);
});
```

### 6.4 通信方式选型指南

| 方式 | 范围 | 速度 | 数据量 | 适合 |
|---|---|---|---|---|
| **IPC (send)** | 父子进程 | 快 | 中 | fork 子进程通信 |
| **SharedArrayBuffer** | 同进程线程 | 极快 | 大 | 数值计算共享 |
| **postMessage** | 同进程线程 | 快 | 中 | Worker 通信 |
| **Redis Pub/Sub** | 跨机器 | 中 | 中 | 分布式事件 |
| **消息队列** | 跨机器 | 中 | 大 | 可靠异步任务 |
| **Unix Socket** | 同机器任意进程 | 快 | 大 | 自定义协议 |

---

## 7. 实战场景

### 7.1 图片处理微服务（Worker Threads）

```javascript
// ── image-service.js ──
const http = require('http');
const { ThreadPool } = require('./thread-pool');  // 第 3 章实现

const pool = new ThreadPool('./image-worker.js', 4);

const server = http.createServer(async (req, res) => {
  if (req.method === 'POST' && req.url === '/resize') {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const imageBuffer = Buffer.concat(chunks);

    try {
      const result = await pool.run({
        type: 'resize',
        buffer: imageBuffer,
        width: 800,
        height: 600,
      });
      res.writeHead(200, { 'Content-Type': 'image/jpeg' });
      res.end(Buffer.from(result.buffer));
    } catch (err) {
      res.writeHead(500).end('处理失败');
    }
  }
});

server.listen(3000);
```

```javascript
// ── image-worker.js ──
const { parentPort } = require('worker_threads');
const sharp = require('sharp');

parentPort.on('message', async (msg) => {
  if (msg.type === 'resize') {
    const result = await sharp(Buffer.from(msg.buffer))
      .resize(msg.width, msg.height)
      .jpeg({ quality: 80 })
      .toBuffer();

    parentPort.postMessage({ buffer: result });
  }
});
```

```
架构：
  HTTP 请求 → 主线程（不阻塞）→ 线程池分发 → Worker 处理图片 → 返回
  
  主线程始终空闲处理新请求，图片处理在 Worker 中并行执行
```

### 7.2 定时任务调度器（child_process）

```javascript
// ── scheduler.js ──
const { fork } = require('child_process');
const cron = require('node-cron');

const tasks = {
  'cleanup-logs': { script: './tasks/cleanup.js', schedule: '0 2 * * *' },
  'send-reports': { script: './tasks/report.js', schedule: '0 9 * * 1' },
  'sync-data': { script: './tasks/sync.js', schedule: '*/30 * * * *' },
};

for (const [name, config] of Object.entries(tasks)) {
  cron.schedule(config.schedule, () => {
    console.log(`[${new Date().toISOString()}] 启动任务: ${name}`);

    const child = fork(config.script, [], {
      stdio: ['pipe', 'pipe', 'pipe', 'ipc'],
    });

    child.on('message', (msg) => {
      console.log(`[${name}] ${JSON.stringify(msg)}`);
    });

    child.on('exit', (code) => {
      console.log(`[${name}] 完成，退出码: ${code}`);
    });

    // 超时保护
    setTimeout(() => {
      if (!child.killed) {
        console.warn(`[${name}] 超时，强制终止`);
        child.kill('SIGKILL');
      }
    }, 5 * 60 * 1000);  // 5 分钟
  });
}

console.log('调度器已启动');
```

### 7.3 高可用 HTTP 服务（Cluster + PM2）

完整的生产配置：

```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'web-api',
    script: './src/server.js',
    instances: 'max',
    exec_mode: 'cluster',
    env_production: {
      NODE_ENV: 'production',
      PORT: 8080,
    },
    max_memory_restart: '500M',
    wait_ready: true,
    listen_timeout: 10000,
    kill_timeout: 5000,
    merge_logs: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
  }],
};
```

```javascript
// src/server.js
const express = require('express');
const app = express();

app.get('/health', (req, res) => {
  res.json({ status: 'ok', pid: process.pid, uptime: process.uptime() });
});

app.get('/api/data', (req, res) => {
  res.json({ worker: process.pid, data: 'hello' });
});

const server = app.listen(process.env.PORT || 3000, () => {
  console.log(`Worker ${process.pid} 就绪`);
  if (process.send) process.send('ready');  // 通知 PM2
});

// 优雅关闭
process.on('SIGINT', () => {
  server.close(() => {
    console.log(`Worker ${process.pid} 优雅退出`);
    process.exit(0);
  });
});
```

```bash
# 部署
pm2 start ecosystem.config.js --env production
pm2 save
pm2 startup

# 更新代码后零停机重启
git pull
npm install
pm2 reload web-api

# 监控
pm2 monit
```

---

## 全书总结

```
┌─────────────────────────────────────────────────────────────┐
│          Node.js 进程与集群 · 知识地图                        │
│                                                              │
│  Ch.1  单线程瓶颈    CPU 密集阻塞 / 三种方案决策树            │
│  Ch.2  child_process exec·spawn·fork / IPC / 管道组合        │
│  Ch.3  Worker Threads 消息传递 / SharedArrayBuffer / 线程池   │
│  Ch.4  Cluster       端口共享 / Master-Worker / 零停机重启    │
│  Ch.5  PM2           ecosystem / reload / 监控 / 自动重启     │
│  Ch.6  进程间通信     IPC / 共享内存 / Redis / 选型指南        │
│  Ch.7  实战场景       图片处理 / 定时调度 / 高可用 HTTP        │
│                                                              │
│  7 章 24 节，从单线程突破到生产级多核部署。                    │
└─────────────────────────────────────────────────────────────┘
```

> 🎉 **核心口诀**：外部命令用 spawn，CPU 计算用 Worker，HTTP 多核用 Cluster，生产管理用 PM2。
