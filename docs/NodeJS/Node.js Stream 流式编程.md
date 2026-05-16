# Node.js Stream 流式编程

> 掌握 Node.js Stream 的四种类型、背压控制、pipeline 组合与自定义流——用流式思维处理大文件、网络传输和实时数据管线。

---

## 1. Stream 是什么：为什么不能一次读完

### 1.1 大文件问题：readFile 的内存炸弹

```javascript
const fs = require('fs');

// ❌ 一次性读取 2GB 文件
fs.readFile('huge-log.csv', (err, data) => {
  // data 是一个 2GB 的 Buffer → 内存直接爆炸
  // Node.js 默认堆上限 ~1.5GB，直接 OOM
  console.log(data.length);
});
```

```
一次性读取的内存模型：

  ┌────────────────────────────────┐
  │          Node.js 内存           │
  │                                │
  │  ┌──────────────────────────┐  │
  │  │   2GB Buffer（整个文件）   │  │  ← 💥 OOM!
  │  └──────────────────────────┘  │
  │                                │
  │  堆上限 ~1.5GB                 │
  └────────────────────────────────┘
```

用 Stream 就不一样——每次只处理一小块（通常 64KB）：

```javascript
// ✅ 流式读取：内存始终在几十 MB
const readable = fs.createReadStream('huge-log.csv');
let lines = 0;

readable.on('data', (chunk) => {
  // chunk 通常 64KB，处理完就释放
  lines += chunk.toString().split('\n').length - 1;
});

readable.on('end', () => {
  console.log(`总行数: ${lines}`);
});
```

```
流式读取的内存模型：

  ┌────────────────────────────────┐
  │          Node.js 内存           │
  │                                │
  │  ┌────────┐                    │
  │  │ 64KB   │ ← 当前 chunk       │  ← 只占几十 MB
  │  └────────┘                    │
  │  处理完 → 释放 → 读下一块       │
  │                                │
  └────────────────────────────────┘
```

### 1.2 Stream 的核心思想：数据像水一样流过

Stream 不是"读完再处理"，而是"边读边处理"：

```
传统模式（蓄水池）：
  文件 ═══════════════> [   整个文件装入内存   ] ═══> 处理

Stream 模式（水管）：
  文件 ──chunk1──> 处理 ──chunk2──> 处理 ──chunk3──> 处理 ──> 完成
         64KB              64KB              64KB
```

Stream 的核心优势：

| | 一次性读取 | Stream |
|---|---|---|
| **内存** | 文件多大占多大 | 恒定（几十 MB） |
| **首字节时间** | 等全部读完 | 第一块就能处理 |
| **适合大文件** | ❌ OOM | ✅ |
| **可组合** | ❌ | ✅ pipe/pipeline |

### 1.3 四种 Stream 类型总览

| 类型 | 方向 | 核心方法 | 典型例子 |
|---|---|---|---|
| **Readable** | 只读（数据源） | `_read()` | `fs.createReadStream`、`http.IncomingMessage` |
| **Writable** | 只写（数据终点） | `_write()` | `fs.createWriteStream`、`http.ServerResponse` |
| **Duplex** | 双向（独立读写） | `_read()` + `_write()` | `net.Socket`、`WebSocket` |
| **Transform** | 双向（读入→变换→写出） | `_transform()` | `zlib.createGzip`、`crypto.createCipher` |

```
四种 Stream 的数据流向：

  Readable:    [数据源] ──读──> 消费者

  Writable:    生产者 ──写──> [数据终点]

  Duplex:      [读端] ──> 消费者
               生产者 ──> [写端]    （读写独立，互不影响）

  Transform:   [输入] ──变换──> [输出]   （读写关联：输入经变换后输出）
```

> 💡 **记忆法**：Readable 是水龙头，Writable 是下水道，Duplex 是电话（双向独立），Transform 是净水器（进去脏水，出来干净水）。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 一次性读取 | 文件多大内存占多大，大文件 OOM |
| Stream | 分块处理，内存恒定，边读边处理 |
| 四种类型 | Readable / Writable / Duplex / Transform |
| 核心优势 | 低内存、快响应、可组合 |

> **下一章**：深入 Readable Stream——Flowing/Paused 两种模式、for-await-of 现代消费、自定义数据源。

---

## 2. Readable Stream：数据从哪来

### 2.1 流模式（Flowing）vs 暂停模式（Paused）

Readable Stream 有两种消费模式：

```
暂停模式（Paused）← 默认
  数据在内部缓冲区等着，你主动 read() 才给你
  → 像自助取餐：你去拿才有

流模式（Flowing）
  数据自动推给你，通过 'data' 事件
  → 像传送带：不停地往你面前送

切换方式：
  暂停 → 流模式：
    1. 监听 'data' 事件
    2. 调用 stream.resume()
    3. 调用 stream.pipe()

  流模式 → 暂停：
    1. 调用 stream.pause()
    2. 移除所有 'data' 监听器
```

```javascript
const fs = require('fs');

// ── 流模式：监听 data 事件自动触发 ──
const stream1 = fs.createReadStream('file.txt');
stream1.on('data', (chunk) => {
  console.log(`收到 ${chunk.length} 字节`);
});

// ── 暂停模式：手动 read() ──
const stream2 = fs.createReadStream('file.txt');
stream2.on('readable', () => {
  let chunk;
  while ((chunk = stream2.read()) !== null) {
    console.log(`手动读取 ${chunk.length} 字节`);
  }
});
```

### 2.2 fs.createReadStream 逐行解析

```javascript
const fs = require('fs');

const stream = fs.createReadStream('server.log', {
  encoding: 'utf8',       // 自动解码为字符串（默认 Buffer）
  highWaterMark: 64 * 1024, // 每次读取的块大小（默认 64KB）
  start: 0,                // 起始字节位置
  // end: 1000,            // 结束字节位置（可选）
});

// 核心事件
stream.on('data', (chunk) => console.log('数据:', chunk.length));
stream.on('end', () => console.log('读取完毕'));
stream.on('error', (err) => console.error('出错:', err.message));
stream.on('close', () => console.log('流已关闭'));
```

事件生命周期：

```
创建 → 'open' → 'data' × N → 'end' → 'close'
                                 ↑
                           如果出错: 'error' → 'close'
```

### 2.3 for-await-of：现代消费方式

Node.js 10+ 的 Readable 实现了异步可迭代协议，可以用 `for-await-of` 消费：

```javascript
const fs = require('fs');

async function countLines(filepath) {
  const stream = fs.createReadStream(filepath, { encoding: 'utf8' });
  let count = 0;

  for await (const chunk of stream) {
    count += chunk.split('\n').length - 1;
  }
  // 循环结束 = 流自动关闭
  return count;
}

countLines('huge-file.csv').then(n => console.log(`${n} 行`));
```

`for-await-of` vs 事件监听：

| | 事件（data/end） | for-await-of |
|---|---|---|
| **风格** | 回调 | async/await |
| **错误处理** | `.on('error')` | `try/catch` |
| **流控制** | 需手动 pause/resume | 自动（内置背压） |
| **推荐** | 底层/高性能场景 | 大部分业务代码 ✅ |

### 2.4 自定义 Readable：实现 _read()

当你有自己的数据源（数据库、API、算法生成），可以自定义 Readable：

```javascript
const { Readable } = require('stream');

// 方式一：继承
class CounterStream extends Readable {
  constructor(max = 5) {
    super({ objectMode: false, highWaterMark: 16 });
    this.current = 1;
    this.max = max;
  }

  _read(size) {
    if (this.current > this.max) {
      this.push(null);  // null 表示数据结束
      return;
    }
    const data = `第 ${this.current} 行数据\n`;
    this.push(data);    // 推送数据给消费者
    this.current++;
  }
}

const counter = new CounterStream(3);
counter.on('data', (chunk) => process.stdout.write(chunk));
// 输出：第 1 行数据 / 第 2 行数据 / 第 3 行数据

// 方式二：工厂函数（更简洁）
const { Readable } = require('stream');

const stream = new Readable({
  read() {
    this.push('hello\n');
    this.push(null);  // 只发一条数据就结束
  }
});

stream.pipe(process.stdout);
```

实战：从数据库分批读取

```javascript
class DatabaseStream extends Readable {
  constructor(query, batchSize = 100) {
    super({ objectMode: true });  // 对象模式，每次 push 一个对象
    this.query = query;
    this.batchSize = batchSize;
    this.offset = 0;
  }

  async _read() {
    try {
      const rows = await db.query(this.query, {
        limit: this.batchSize,
        offset: this.offset,
      });

      if (rows.length === 0) {
        this.push(null);  // 没有更多数据
        return;
      }

      for (const row of rows) {
        this.push(row);   // 逐行推送
      }
      this.offset += rows.length;
    } catch (err) {
      this.destroy(err);  // 出错时销毁流
    }
  }
}
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 两种模式 | Flowing（自动推）vs Paused（手动拉） |
| 事件 | data → end → close；error 随时可能触发 |
| for-await-of | 现代写法，自动背压 + try/catch 错误处理 |
| 自定义 Readable | 实现 `_read()`，用 `push()` 发数据，`push(null)` 结束 |
| objectMode | 设为 true 可以 push 任意 JS 对象（不限于 Buffer/String） |

> **下一章**：Writable Stream——write() 返回值与 drain 事件、highWaterMark 背压触发、自定义 Writable。

---

## 3. Writable Stream：数据到哪去

### 3.1 write() 返回值与 drain 事件

`write()` 有一个**容易被忽略的返回值**：

```javascript
const fs = require('fs');
const writable = fs.createWriteStream('output.txt');

const ok = writable.write('hello\n');
console.log(ok);  // true 或 false
```

```
write() 返回值的含义：

  true  → 内部缓冲区还有空间，可以继续写
  false → 缓冲区满了！应该停止写入，等 'drain' 事件

  ┌──────────────────────────────┐
  │       Writable 内部缓冲区     │
  │                              │
  │  [data][data][data][data]    │  ← 数据先存这里
  │                              │
  │  highWaterMark = 16KB        │  ← 水位线
  │  当前已用 > 16KB → write() 返回 false
  └──────────────────────────────┘
           │
           ↓ 异步刷到磁盘/网络
```

```javascript
const writable = fs.createWriteStream('output.txt');

// ❌ 不检查返回值 → 内存堆积
for (let i = 0; i < 1000000; i++) {
  writable.write(`第 ${i} 行数据\n`);  // 返回值被忽略了！
}

// ✅ 正确：检查返回值 + 等 drain
function writeData(writable, total) {
  let i = 0;

  function write() {
    let ok = true;
    while (i < total && ok) {
      ok = writable.write(`第 ${i} 行数据\n`);
      i++;
    }
    if (i < total) {
      // 缓冲区满了，等 drain 再继续
      writable.once('drain', write);
    } else {
      writable.end();  // 写完了
    }
  }

  write();
}

writeData(writable, 1000000);
```

### 3.2 highWaterMark：背压的触发阈值

```javascript
// highWaterMark 决定内部缓冲区的"水位线"
const writable = fs.createWriteStream('output.txt', {
  highWaterMark: 1024,  // 1KB（默认 16KB）
});

// 当缓冲数据 > 1KB 时，write() 返回 false
// 当缓冲数据刷完后，触发 'drain' 事件
```

| highWaterMark | 效果 |
|---|---|
| 太小（如 1KB） | 频繁触发 drain，写入效率低 |
| 太大（如 10MB） | 内存占用高，背压反馈慢 |
| 默认 16KB | 适合大部分场景 |
| 文件写入推荐 | 64KB - 256KB |

### 3.3 自定义 Writable：实现 _write()

```javascript
const { Writable } = require('stream');

// 示例：写入到控制台（带行号）
class LineNumberWriter extends Writable {
  constructor() {
    super({ decodeStrings: true });
    this.lineNum = 1;
  }

  _write(chunk, encoding, callback) {
    const lines = chunk.toString().split('\n').filter(Boolean);
    for (const line of lines) {
      console.log(`${this.lineNum++}: ${line}`);
    }
    callback();  // 必须调用！告诉流"我处理完了，可以给下一块"
    // callback(new Error('写入失败'));  // 传 Error 表示失败
  }

  _final(callback) {
    console.log(`--- 总共 ${this.lineNum - 1} 行 ---`);
    callback();
  }
}

const writer = new LineNumberWriter();
writer.write('hello\nworld\n');
writer.end('bye\n');
// 输出：1: hello / 2: world / 3: bye / --- 总共 3 行 ---
```

实战：批量写入数据库

```javascript
class DatabaseWriter extends Writable {
  constructor(batchSize = 100) {
    super({ objectMode: true, highWaterMark: batchSize });
    this.batch = [];
    this.batchSize = batchSize;
  }

  async _write(record, encoding, callback) {
    this.batch.push(record);
    if (this.batch.length >= this.batchSize) {
      try {
        await db.batchInsert(this.batch);
        this.batch = [];
        callback();
      } catch (err) {
        callback(err);
      }
    } else {
      callback();
    }
  }

  async _final(callback) {
    // 刷入剩余数据
    if (this.batch.length > 0) {
      try {
        await db.batchInsert(this.batch);
        callback();
      } catch (err) {
        callback(err);
      }
    } else {
      callback();
    }
  }
}
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| write() 返回值 | true = 可继续写，false = 缓冲区满，等 drain |
| drain 事件 | 缓冲区排空时触发，恢复写入的信号 |
| highWaterMark | 缓冲区水位线，默认 16KB |
| 自定义 Writable | 实现 `_write(chunk, enc, cb)`，必须调用 `callback()` |
| _final | 流结束前的清理钩子（刷缓冲、关连接） |

---

## 4. 背压控制：不让内存爆炸

### 4.1 为什么会产生背压

当**生产者（Readable）比消费者（Writable）快**时，数据在中间堆积：

```
背压产生的过程：

  Readable（快）          Writable（慢）
  ┌────────┐              ┌────────┐
  │ 100MB/s│ ──────────→  │ 10MB/s │
  └────────┘              └────────┘
        ↓ 差值 90MB/s 堆在哪？
  ┌──────────────────────────────┐
  │    Writable 内部缓冲区        │
  │    不断膨胀...               │  ← 💥 内存爆炸！
  └──────────────────────────────┘
```

常见场景：
- 读 SSD 文件（500MB/s）→ 写网络（10MB/s）
- 读数据库（快）→ 写 CSV 文件（慢）
- HTTP 请求体（快）→ 处理逻辑（慢）

### 4.2 手动背压处理：pause/resume

```javascript
const fs = require('fs');

const readable = fs.createReadStream('huge-file.csv');
const writable = fs.createWriteStream('output.csv');

readable.on('data', (chunk) => {
  const ok = writable.write(chunk);
  if (!ok) {
    // 写端满了 → 暂停读取
    readable.pause();
  }
});

writable.on('drain', () => {
  // 写端缓冲排空 → 恢复读取
  readable.resume();
});

readable.on('end', () => {
  writable.end();
});

readable.on('error', (err) => console.error('读取错误:', err));
writable.on('error', (err) => console.error('写入错误:', err));
```

```
手动背压控制流程：

  Readable ──data──> write() 返回 false?
     │                    │
     │ YES               │ NO
     ↓                    ↓
  pause()            继续读取
     │
     │ 等待 drain
     ↓
  resume() ──> 继续读取
```

### 4.3 pipe()：自动背压的经典方案

上面的手动背压逻辑很繁琐。`pipe()` 帮你自动处理：

```javascript
const fs = require('fs');

// 一行代码搞定：自动背压 + 自动 end
fs.createReadStream('huge-file.csv')
  .pipe(fs.createWriteStream('output.csv'));
```

`pipe()` 内部做的事：

```javascript
// pipe() 的等效伪代码（简化版）
readable.pipe = function(writable) {
  this.on('data', (chunk) => {
    const ok = writable.write(chunk);
    if (!ok) this.pause();         // 自动暂停
  });

  writable.on('drain', () => {
    this.resume();                  // 自动恢复
  });

  this.on('end', () => {
    writable.end();                 // 自动结束
  });

  return writable;                  // 支持链式调用
};
```

链式 pipe：

```javascript
const zlib = require('zlib');

// 读文件 → 压缩 → 写文件（每一步自动背压）
fs.createReadStream('input.log')
  .pipe(zlib.createGzip())
  .pipe(fs.createWriteStream('input.log.gz'));
```

> ⚠️ **pipe() 的问题**：错误不会自动传播！如果中间某个流出错，其他流不会自动关闭，导致内存泄漏。第 6 章的 `pipeline()` 解决了这个问题。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 背压原因 | 生产者快 > 消费者慢，数据堆积在缓冲区 |
| 手动背压 | write() 返回 false → pause()，drain → resume() |
| pipe() | 自动背压 + 自动 end，但不传播错误 |
| 链式 pipe | `a.pipe(b).pipe(c)`，每步都有背压控制 |

> **下一章**：Transform 与 Duplex——流水线上的数据变换，行分割器、CSV 解析器、压缩流实战。

---

## 5. Transform 与 Duplex：数据变换

### 5.1 Transform：流水线上的加工站

Transform 是最常用的自定义流——数据进来，经过变换，再出去：

```
Transform 的数据流：

  输入（Writable 端）          输出（Readable 端）
  ┌────────────┐              ┌────────────┐
  │ 原始数据    │ ──_transform──> │ 变换后数据  │
  └────────────┘              └────────────┘

  例：
  "hello world" ──toUpperCase──> "HELLO WORLD"
  原始字节      ──gzip──>        压缩字节
  CSV 行        ──parse──>       JS 对象
```

```javascript
const { Transform } = require('stream');

// 最简单的 Transform：转大写
class UpperCaseTransform extends Transform {
  _transform(chunk, encoding, callback) {
    const upper = chunk.toString().toUpperCase();
    this.push(upper);  // push 到输出端
    callback();        // 告知处理完毕
  }
}

// 使用
process.stdin
  .pipe(new UpperCaseTransform())
  .pipe(process.stdout);
// 输入 hello → 输出 HELLO
```

`_flush()`：流结束时的最后处理

```javascript
class JsonArrayTransform extends Transform {
  constructor() {
    super();
    this.first = true;
    this.push('[');  // 开头
  }

  _transform(chunk, encoding, callback) {
    const prefix = this.first ? '' : ',';
    this.first = false;
    this.push(prefix + chunk.toString().trim());
    callback();
  }

  _flush(callback) {
    this.push(']');  // 结尾——只在流结束时调用一次
    callback();
  }
}
```

### 5.2 实战：行分割器 / CSV 解析器 / 压缩流

**行分割器**（处理跨 chunk 的断行）：

```javascript
class LineSplitter extends Transform {
  constructor() {
    super({ readableObjectMode: true });
    this._remainder = '';
  }

  _transform(chunk, encoding, callback) {
    const data = this._remainder + chunk.toString();
    const lines = data.split('\n');
    this._remainder = lines.pop();  // 最后一段可能不完整，留到下次

    for (const line of lines) {
      if (line.trim()) this.push(line);
    }
    callback();
  }

  _flush(callback) {
    if (this._remainder.trim()) {
      this.push(this._remainder);
    }
    callback();
  }
}

// 使用：大文件逐行处理
fs.createReadStream('server.log')
  .pipe(new LineSplitter())
  .on('data', (line) => {
    console.log('行:', line);
  });
```

> 💡 **为什么需要 LineSplitter？** `createReadStream` 按字节分块（64KB），不按行分割。一个 chunk 可能在一行的中间断开。LineSplitter 处理了这个边界问题。

**简易 CSV 解析器**：

```javascript
class CsvParser extends Transform {
  constructor(options = {}) {
    super({ readableObjectMode: true });
    this.separator = options.separator || ',';
    this.headers = null;
    this._remainder = '';
  }

  _transform(chunk, encoding, callback) {
    const data = this._remainder + chunk.toString();
    const lines = data.split('\n');
    this._remainder = lines.pop();

    for (const line of lines) {
      if (!line.trim()) continue;
      const values = line.split(this.separator).map(v => v.trim());

      if (!this.headers) {
        this.headers = values;  // 第一行是表头
      } else {
        const obj = {};
        this.headers.forEach((h, i) => obj[h] = values[i]);
        this.push(obj);
      }
    }
    callback();
  }
}

// name,age,city
// 张三,28,北京
// → { name: '张三', age: '28', city: '北京' }
```

**压缩流**（内置 Transform）：

```javascript
const zlib = require('zlib');

// zlib.createGzip() 就是一个 Transform
fs.createReadStream('big-data.json')
  .pipe(zlib.createGzip())                    // Transform: 压缩
  .pipe(fs.createWriteStream('big-data.json.gz'));

// 解压也是 Transform
fs.createReadStream('big-data.json.gz')
  .pipe(zlib.createGunzip())                  // Transform: 解压
  .pipe(fs.createWriteStream('big-data.json'));
```

### 5.3 Duplex 与 PassThrough

**Duplex**：读端和写端**完全独立**（不像 Transform 有输入→输出的关联）：

```javascript
const { Duplex } = require('stream');

// 典型 Duplex：net.Socket
// 写端：发送数据到对方
// 读端：接收对方发来的数据
// 两端没有因果关系

class EchoSocket extends Duplex {
  _read(size) { /* 等数据到来 */ }

  _write(chunk, encoding, callback) {
    // 写入的数据直接推到读端（Echo）
    this.push(chunk);
    callback();
  }
}
```

**PassThrough**：什么都不变的 Transform，用于观察/监控：

```javascript
const { PassThrough } = require('stream');

// 用 PassThrough 统计流经的数据量
const monitor = new PassThrough();
let totalBytes = 0;

monitor.on('data', (chunk) => {
  totalBytes += chunk.length;
});

monitor.on('end', () => {
  console.log(`总共传输: ${(totalBytes / 1024 / 1024).toFixed(2)} MB`);
});

// 插入到 pipe 链中，不影响数据
fs.createReadStream('file.dat')
  .pipe(monitor)
  .pipe(fs.createWriteStream('copy.dat'));
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Transform | 实现 `_transform()`，用 `push()` 输出，`_flush()` 收尾 |
| LineSplitter | 处理跨 chunk 断行的关键模式 |
| Duplex | 读写独立，典型例子是 Socket |
| PassThrough | "透明"流，用于监控/统计/分支 |

---

## 6. pipeline 与 compose：现代流组合

### 6.1 pipe() 的隐藏陷阱

```javascript
// pipe() 的错误处理问题
const readable = fs.createReadStream('input.txt');
const gzip = zlib.createGzip();
const writable = fs.createWriteStream('output.gz');

readable.pipe(gzip).pipe(writable);

// ❌ 如果 gzip 出错：
// - readable 不会自动关闭 → 文件描述符泄漏
// - writable 不会自动关闭 → 文件描述符泄漏
// - 没有统一的错误回调

// 你必须每个流都监听 error：
readable.on('error', cleanup);
gzip.on('error', cleanup);
writable.on('error', cleanup);

function cleanup(err) {
  readable.destroy();
  gzip.destroy();
  writable.destroy();
  console.error('出错:', err);
}
```

### 6.2 pipeline()：错误处理 + 自动清理

`pipeline()` 是 `pipe()` 的生产级替代品（Node.js 10+）：

```javascript
const { pipeline } = require('stream');
const { pipeline: pipelineAsync } = require('stream/promises');

// 回调风格
pipeline(
  fs.createReadStream('input.txt'),
  zlib.createGzip(),
  fs.createWriteStream('output.gz'),
  (err) => {
    if (err) console.error('管道失败:', err);
    else console.log('管道完成');
    // ✅ 无论成功失败，所有流都会自动关闭
  }
);

// async/await 风格（推荐）
async function compress(input, output) {
  try {
    await pipelineAsync(
      fs.createReadStream(input),
      zlib.createGzip(),
      fs.createWriteStream(output),
    );
    console.log('压缩完成');
  } catch (err) {
    console.error('压缩失败:', err);
    // ✅ 所有流已自动清理
  }
}
```

pipeline vs pipe：

| | pipe() | pipeline() |
|---|---|---|
| **错误传播** | ❌ 不传播 | ✅ 统一捕获 |
| **自动清理** | ❌ 需手动 destroy | ✅ 自动 destroy 所有流 |
| **async/await** | ❌ | ✅ `stream/promises` |
| **推荐** | 简单场景 | 生产代码 ✅ |

### 6.3 stream.compose()：组合多个 Transform

Node.js 19+ 的 `stream.compose()` 可以把多个 Transform 合并成一个：

```javascript
const { compose } = require('stream');

// 单独的 Transform
function toUpperCase() {
  return new Transform({
    transform(chunk, enc, cb) {
      cb(null, chunk.toString().toUpperCase());
    }
  });
}

function addLineNumber() {
  let n = 1;
  return new Transform({
    transform(chunk, enc, cb) {
      cb(null, `${n++}: ${chunk}`);
    }
  });
}

function addTimestamp() {
  return new Transform({
    transform(chunk, enc, cb) {
      cb(null, `[${new Date().toISOString()}] ${chunk}`);
    }
  });
}

// 组合成一个 Duplex 流
const logFormatter = compose(
  toUpperCase(),
  addLineNumber(),
  addTimestamp(),
);

// 当成一个整体使用
process.stdin.pipe(logFormatter).pipe(process.stdout);
// 输入: hello
// 输出: [2026-05-10T03:00:00.000Z] 1: HELLO
```

compose 的价值：**封装复杂管线为可复用组件**：

```javascript
// 把"读 CSV → 解析 → 过滤 → 格式化"封装成一个流
function createCsvProcessor(filter) {
  return compose(
    new LineSplitter(),
    new CsvParser(),
    new Transform({
      objectMode: true,
      transform(row, enc, cb) {
        if (filter(row)) this.push(JSON.stringify(row) + '\n');
        cb();
      }
    }),
  );
}

// 使用者不需要知道内部有多少步
await pipelineAsync(
  fs.createReadStream('data.csv'),
  createCsvProcessor(row => row.age > 18),
  fs.createWriteStream('adults.jsonl'),
);
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| pipe 缺陷 | 不传播错误、不自动清理、可能泄漏文件描述符 |
| pipeline | 统一错误处理 + 自动 destroy + 支持 async/await |
| compose | 多个 Transform 合并为一个 Duplex，封装可复用管线 |
| 推荐 | 生产代码一律用 `pipeline()`，不用 `pipe()` |

> **下一章**：对象模式、Readable.from()、Web Streams API 与性能调优。

---

## 7. 对象模式与高级特性

### 7.1 对象模式：流不只是 Buffer

默认 Stream 只处理 Buffer/String。开启 `objectMode` 后，可以传递任意 JS 对象：

```javascript
const { Transform } = require('stream');

// objectMode: true → push 任意对象
const jsonParser = new Transform({
  readableObjectMode: true,  // 输出端是对象
  transform(chunk, enc, cb) {
    try {
      const obj = JSON.parse(chunk.toString().trim());
      cb(null, obj);
    } catch (e) {
      cb(e);
    }
  }
});

jsonParser.write('{"name":"张三","age":28}');
jsonParser.on('data', (obj) => {
  console.log(obj.name);  // '张三' ← 是对象，不是字符串
  console.log(typeof obj); // 'object'
});
```

> ⚠️ 对象模式下 `highWaterMark` 单位是**对象个数**（默认 16 个），不再是字节数。

### 7.2 Readable.from()：可迭代对象 → Stream

把数组、Generator、异步迭代器快速转成 Readable Stream：

```javascript
const { Readable } = require('stream');

// 从数组
const stream1 = Readable.from(['hello\n', 'world\n', 'bye\n']);
stream1.pipe(process.stdout);

// 从 Generator
function* generateNumbers(n) {
  for (let i = 1; i <= n; i++) {
    yield `${i}\n`;
  }
}
Readable.from(generateNumbers(5)).pipe(process.stdout);

// 从异步 Generator（最强大：数据库分页、API 翻页）
async function* fetchPages(url) {
  let page = 1;
  while (true) {
    const res = await fetch(`${url}?page=${page}`);
    const data = await res.json();
    if (data.items.length === 0) return;
    for (const item of data.items) {
      yield JSON.stringify(item) + '\n';
    }
    page++;
  }
}

const { pipeline } = require('stream/promises');
await pipeline(
  Readable.from(fetchPages('https://api.example.com/users')),
  fs.createWriteStream('all-users.jsonl'),
);
```

### 7.3 Web Streams API：浏览器兼容标准

Node.js 18+ 内置了 Web Streams API（与浏览器 `ReadableStream`/`WritableStream` 相同）：

```javascript
// Web Streams（浏览器标准）
const webReadable = new ReadableStream({
  start(controller) {
    controller.enqueue('hello');
    controller.enqueue('world');
    controller.close();
  }
});

// Node Streams ↔ Web Streams 互转
const { Readable, Writable } = require('stream');

// Web → Node
const nodeReadable = Readable.fromWeb(webReadable);
nodeReadable.on('data', (chunk) => console.log(chunk));

// Node → Web
const nodeStream = fs.createReadStream('file.txt');
const webStream = Readable.toWeb(nodeStream);
// webStream 可以用在 fetch Response、Service Worker 等场景
```

什么时候用哪个？

| | Node Streams | Web Streams |
|---|---|---|
| **生态** | Node.js 原生，库支持最好 | 浏览器标准，跨运行时 |
| **性能** | ✅ 更快（C++ 绑定） | 稍慢 |
| **功能** | pipe/pipeline/compose 完整 | API 更简洁 |
| **推荐** | Node.js 后端 ✅ | 需要跨运行时（Deno/Edge） |

### 7.4 Stream 性能调优

```javascript
// 1. highWaterMark 调优
// 文件 I/O：增大 highWaterMark 减少系统调用
fs.createReadStream('huge.csv', { highWaterMark: 256 * 1024 }); // 256KB

// 2. 避免不必要的 toString()
// ❌ 每个 chunk 都转字符串
transform(chunk, enc, cb) {
  const str = chunk.toString();  // Buffer → String 有拷贝开销
  cb(null, str.toUpperCase());
}
// ✅ 直接操作 Buffer（如果可以的话）

// 3. 用 _writev 批量写入
class BatchWriter extends Writable {
  _writev(chunks, callback) {
    // chunks 是数组，一次处理多个 chunk，减少回调次数
    const combined = chunks.map(c => c.chunk).join('');
    fs.appendFile('output.txt', combined, callback);
  }
}

// 4. 用 pipeline 代替手动事件监听（减少事件开销）
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| objectMode | push 任意对象，highWaterMark 按个数计 |
| Readable.from | 数组/Generator/AsyncGenerator → Stream |
| Web Streams | `Readable.fromWeb()` / `Readable.toWeb()` 互转 |
| 性能调优 | 增大 highWaterMark、避免 toString、用 _writev 批量写 |

---

## 8. 实战场景

### 8.1 大文件逐行处理（GB 级 CSV）

```javascript
const fs = require('fs');
const { pipeline } = require('stream/promises');
const { Transform } = require('stream');

// LineSplitter（第 5 章已实现）+ 业务处理
class LineSplitter extends Transform {
  constructor() {
    super({ readableObjectMode: true });
    this._buf = '';
  }
  _transform(chunk, enc, cb) {
    const data = this._buf + chunk.toString();
    const lines = data.split('\n');
    this._buf = lines.pop();
    for (const l of lines) if (l.trim()) this.push(l);
    cb();
  }
  _flush(cb) {
    if (this._buf.trim()) this.push(this._buf);
    cb();
  }
}

// 统计 + 过滤 + 输出
async function processLargeCSV(input, output) {
  let processed = 0;
  let matched = 0;

  const filter = new Transform({
    objectMode: true,
    transform(line, enc, cb) {
      processed++;
      const cols = line.split(',');
      // 假设第 3 列是金额，过滤 > 1000 的
      if (parseFloat(cols[2]) > 1000) {
        matched++;
        this.push(line + '\n');
      }
      if (processed % 100000 === 0) {
        console.log(`已处理 ${processed} 行，匹配 ${matched} 行`);
      }
      cb();
    }
  });

  await pipeline(
    fs.createReadStream(input, { highWaterMark: 256 * 1024 }),
    new LineSplitter(),
    filter,
    fs.createWriteStream(output),
  );

  console.log(`完成：${processed} 行中匹配 ${matched} 行`);
}

processLargeCSV('transactions.csv', 'large-transactions.csv');
// 处理 5GB CSV 文件，内存稳定在 ~50MB
```

### 8.2 HTTP 流式代理与响应

```javascript
const http = require('http');
const { pipeline } = require('stream');
const zlib = require('zlib');

// 场景：代理请求并压缩响应
const server = http.createServer((req, res) => {
  // req 是 Readable，res 是 Writable
  if (req.url === '/download') {
    res.writeHead(200, {
      'Content-Type': 'application/octet-stream',
      'Content-Encoding': 'gzip',
    });

    pipeline(
      fs.createReadStream('big-report.csv'),
      zlib.createGzip(),
      res,  // HTTP 响应也是 Writable！
      (err) => {
        if (err) console.error('传输失败:', err);
      }
    );
    return;
  }

  // 场景：接收上传文件（req 是 Readable）
  if (req.method === 'POST' && req.url === '/upload') {
    const dest = fs.createWriteStream(`uploads/${Date.now()}.dat`);
    let bytes = 0;

    req.on('data', (chunk) => { bytes += chunk.length; });

    pipeline(req, dest, (err) => {
      if (err) {
        res.writeHead(500).end('上传失败');
      } else {
        res.writeHead(200).end(`上传成功: ${bytes} 字节`);
      }
    });
  }
});

server.listen(3000);
```

### 8.3 实时日志分析管线

```javascript
const { pipeline } = require('stream/promises');
const { Transform } = require('stream');

// 实时 tail -f 效果 + 过滤 + 统计
const fs = require('fs');

function createLogAnalyzer() {
  const stats = { total: 0, errors: 0, slow: 0 };

  const filter = new Transform({
    objectMode: true,
    transform(line, enc, cb) {
      stats.total++;
      // 提取日志级别和耗时
      const errorMatch = line.match(/\[ERROR\]/);
      const timeMatch = line.match(/(\d+)ms/);

      if (errorMatch) {
        stats.errors++;
        this.push(`🔴 ${line}\n`);
      } else if (timeMatch && parseInt(timeMatch[1]) > 1000) {
        stats.slow++;
        this.push(`🟡 ${line}\n`);
      }
      cb();
    },
    flush(cb) {
      this.push(`\n📊 统计: 总共 ${stats.total} 行, 错误 ${stats.errors}, 慢请求 ${stats.slow}\n`);
      cb();
    }
  });

  return filter;
}

await pipeline(
  fs.createReadStream('app.log'),
  new LineSplitter(),
  createLogAnalyzer(),
  process.stdout,  // 或写入告警文件
);
```

### 8.4 LLM 流式响应（Server-Sent Events）

AI 应用的核心场景——把 LLM 的流式输出通过 SSE 推给前端：

```javascript
const http = require('http');
const { Readable } = require('stream');

// 模拟 LLM 流式输出
async function* chatCompletion(prompt) {
  const words = `你好！这是一个关于 "${prompt}" 的回答。Node.js Stream 非常强大。`.split('');
  for (const char of words) {
    await new Promise(r => setTimeout(r, 50));  // 模拟逐字生成
    yield char;
  }
}

const server = http.createServer(async (req, res) => {
  if (req.url === '/api/chat') {
    // SSE 响应头
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
    });

    // 异步 Generator → 流式推送
    const prompt = 'Stream 流式编程';
    for await (const token of chatCompletion(prompt)) {
      res.write(`data: ${JSON.stringify({ token })}\n\n`);
    }
    res.write('data: [DONE]\n\n');
    res.end();
    return;
  }

  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end(`
    <div id="output" style="font-size:18px;padding:20px;"></div>
    <script>
      const es = new EventSource('/api/chat');
      es.onmessage = (e) => {
        if (e.data === '[DONE]') { es.close(); return; }
        const { token } = JSON.parse(e.data);
        document.getElementById('output').textContent += token;
      };
    </script>
  `);
});

server.listen(3000, () => console.log('http://localhost:3000'));
```

```
LLM 流式响应的数据流：

  LLM API ──token──> AsyncGenerator ──SSE──> HTTP Response ──> 前端逐字渲染
  (异步生成)         (for-await-of)         (res.write)       (EventSource)
```

---

## 全书总结

```
┌─────────────────────────────────────────────────────────────┐
│          Node.js Stream 流式编程 · 知识地图                   │
│                                                              │
│  Ch.1  为什么用 Stream   大文件 OOM / 分块处理 / 四种类型     │
│  Ch.2  Readable          Flowing·Paused / for-await-of      │
│  Ch.3  Writable          write()·drain / highWaterMark      │
│  Ch.4  背压控制           pause·resume / pipe 自动背压       │
│  Ch.5  Transform·Duplex  行分割 / CSV 解析 / PassThrough    │
│  Ch.6  pipeline·compose  错误传播 / 自动清理 / 管线封装      │
│  Ch.7  高级特性           objectMode / Readable.from / Web   │
│  Ch.8  实战场景           大文件 / HTTP 代理 / 日志 / LLM    │
│                                                              │
│  8 章 27 节，从概念到生产，掌握 Node.js 流式编程。           │
└─────────────────────────────────────────────────────────────┘
```

> 🎉 **核心口诀**：Readable 产数据，Writable 收数据，Transform 变数据，pipeline 串起来，背压不爆内存。
