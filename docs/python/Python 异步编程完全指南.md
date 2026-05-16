> **一句话导读**：从"为什么需要异步"到"手撕 asyncio 底层"，用最直觉的方式搞懂 Python 异步编程，写出真正高性能的后端代码。

---

## 1. 为什么需要异步？— 从一个真实的性能问题说起

在正式写代码之前，我们先搞清楚一个根本问题：**同步代码到底慢在哪，异步又凭什么能快？**

### 1.1 同步代码的瓶颈：CPU 在摸鱼

想象你是一个前台接待员，你的工作流程是这样的：

```
接待客户 A → 帮 A 打印材料（等打印机 30 秒）→ 把材料交给 A
接待客户 B → 帮 B 打印材料（等打印机 30 秒）→ 把材料交给 B
接待客户 C → ...
```

**问题出在哪？** 你在等打印机的 30 秒里，完全是呆站着的——不能接待后面的客户，不能做任何事。这就是**同步 (Synchronous)** 的工作方式。

在 Python 中，同步代码长这样：

```python
import requests
import time

def fetch_url(url):
    """同步请求：发出去之后，死等响应"""
    response = requests.get(url)  # 🧍 CPU 在这里干等 0.5~2 秒
    return len(response.text)

start = time.time()

# 依次请求 5 个网站（每个等 1 秒 = 总共等 5 秒）
urls = [
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
]

for url in urls:
    fetch_url(url)

print(f"同步耗时: {time.time() - start:.2f} 秒")
# 输出: 同步耗时: 5.12 秒 😱
```

**5 个请求，每个等 1 秒，总共 5 秒。** CPU 在这 5 秒里 99% 的时间都在"等网络响应"，真正计算的时间不到 0.01 秒。

> 💡 这种场景叫做 **I/O 密集型任务**（I/O-bound）：瓶颈不在 CPU 计算，而在「等待外部系统响应」。常见的 I/O 操作包括：网络请求、数据库查询、文件读写、API 调用。

### 1.2 一个实验：同步 vs 异步抓取 10 个网页

现在我们用代码做个对照实验。同样请求 10 个网页，看看异步到底能快多少。

**同步版本（你已经熟悉了）：**

```python
import requests
import time

urls = [f"https://httpbin.org/delay/1" for _ in range(10)]

start = time.time()
for url in urls:
    requests.get(url)
print(f"同步: {time.time() - start:.2f}s")
# 输出: 同步: 10.35s — 10个请求排队执行，老老实实等 10 秒
```

**异步版本（先看结果，后面解释语法）：**

```python
import asyncio
import httpx
import time

urls = [f"https://httpbin.org/delay/1" for _ in range(10)]

async def fetch(client, url):
    """异步请求：发出去就让出 CPU，不干等"""
    response = await client.get(url)  # await = "我先去忙别的，响应来了叫我"
    return len(response.text)

async def main():
    async with httpx.AsyncClient() as client:
        # gather = 同时发出所有请求，并发执行
        tasks = [fetch(client, url) for url in urls]
        await asyncio.gather(*tasks)

start = time.time()
asyncio.run(main())
print(f"异步: {time.time() - start:.2f}s")
# 输出: 异步: 1.28s — 10个请求同时发出，只等最慢的那个 🚀
```

**结果对比：**

| 指标 | 同步 (requests) | 异步 (httpx) | 提升 |
|:---|:---|:---|:---|
| 10 个请求耗时 | ~10.35s | ~1.28s | **⚡ 8 倍** |
| CPU 利用率 | <1%（全在等） | <1%（但等的时间重叠了） | — |
| 代码复杂度 | 简单 | 多了 async/await | 略高 |

> 💡 **关键洞察**：异步并没有让单个请求变快（每个还是 1 秒），而是让 10 个"等待"**重叠**了。就像你同时点了 10 杯外卖奶茶，不用等第 1 杯送到才点第 2 杯。

### 1.3 异步的本质：在等待时做别的事

回到前台接待员的例子。如果换一种工作方式呢？

```
接待客户 A → 提交打印任务 → 📌 不等了！立刻接待客户 B
接待客户 B → 提交打印任务 → 📌 不等了！立刻接待客户 C
接待客户 C → 提交打印任务 →
🔔 A 的材料打印好了 → 交给 A
🔔 B 的材料打印好了 → 交给 B
🔔 C 的材料打印好了 → 交给 C
```

**这就是异步 (Asynchronous)。** 核心思想只有一句话：

> **遇到需要等待的操作时，不要傻等，先去做别的事，等结果回来了再处理。**

用时间线对比来看更直观：

```
同步执行（串行等待）：
═══════════════════════════════════════════════
请求A ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
请求B          ████████░░░░░░░░░░░░░░░░░░░░░░░
请求C                   ████████░░░░░░░░░░░░░░
总耗时: ─────────────────────────────────── 3秒

异步执行（并发等待）：
═══════════════════════════════════════════════
请求A ████████
请求B ████████    ← 三个请求同时在"等"
请求C ████████
总耗时: ──────── 1秒
```

**总结一下第一章的核心认知：**

| 概念 | 说明 |
|:---|:---|
| **同步** | 一件事做完再做下一件，等待时 CPU 闲着 |
| **异步** | 遇到等待就切换去做别的，等待时间重叠 |
| **I/O 密集型** | 瓶颈在等待外部（网络/磁盘/数据库），异步特别有效 |
| **CPU 密集型** | 瓶颈在计算本身（如图像处理），异步帮不了，要用多进程 |

> 💡 **记住这个判断标准**：你的代码大部分时间在"等"还是在"算"？如果在"等"，异步就是你的银弹。FastAPI、爬虫、API 网关、微服务调用——这些全是"等"的场景。

---

## 2. 核心概念：协程、事件循环、await

上一章你已经看到了异步代码的威力。但 `async`、`await`、`asyncio.run()` 这些关键词到底是什么意思？

我们用一个**餐厅类比**把它们全部串起来。

```
🍽️ 异步编程 = 一个高效餐厅

👨‍🍳 事件循环 (Event Loop) = 唯一的服务员（调度中心）
📋 协程 (Coroutine) = 每张桌子的点单任务
⏸️ await = "菜还没好，先去服务其他桌"
```

### 2.1 协程 (Coroutine)：可以暂停的函数

普通函数一旦开始执行，必须跑完才能返回。**协程**不一样——它可以执行到一半「暂停」，把控制权交出去，等条件满足后再「恢复」继续执行。

```python
# 普通函数
def normal_func():
    print("开始")
    print("结束")  # 必须等上一行执行完才能到这里
    return "done"

# 协程函数（加了 async 关键字）
async def coroutine_func():
    print("开始")
    await asyncio.sleep(1)  # ⏸️ 暂停 1 秒，让出 CPU 去做别的事
    print("1 秒后恢复")     # 恢复执行
    return "done"
```

**关键区别**：调用协程函数**不会立即执行**，而是返回一个「协程对象」：

```python
# 普通函数 → 直接执行，返回结果
result = normal_func()        # 输出: 开始 → 结束, result = "done"

# 协程函数 → 不执行！只返回一个协程对象
coro = coroutine_func()       # 什么都没打印！
print(type(coro))             # <class 'coroutine'>

# 必须交给事件循环来执行
import asyncio
result = asyncio.run(coro)    # 现在才开始执行
```

> 💡 **类比**：`async def` 就像写了一份菜单（定义了要做什么），但没有服务员来处理它就只是一张纸。`asyncio.run()` 就是雇了一个服务员来执行这个菜单。

### 2.2 事件循环 (Event Loop)：调度中心

事件循环是异步编程的**大脑**。它做的事非常简单，就是一个无限循环：

```
while 还有任务没完成:
    拿出一个"准备好"的任务
    执行它，直到它遇到 await（暂停）
    把暂停的任务放回等待队列
    检查有没有其他任务"准备好了"
```

用代码来感受事件循环如何调度多个协程：

```python
import asyncio

async def cook(dish, seconds):
    """模拟做一道菜"""
    print(f"🍳 开始做: {dish}")
    await asyncio.sleep(seconds)  # 模拟等待（烹饪时间）
    print(f"✅ {dish} 做好了！(耗时 {seconds}s)")

async def main():
    """事件循环会同时调度这三个协程"""
    # create_task = 把协程"提交"给事件循环
    task1 = asyncio.create_task(cook("番茄炒蛋", 2))
    task2 = asyncio.create_task(cook("红烧肉", 5))
    task3 = asyncio.create_task(cook("蛋花汤", 1))

    # 等待所有任务完成
    await task1
    await task2
    await task3

asyncio.run(main())
```

**输出（注意顺序）：**

```
🍳 开始做: 番茄炒蛋
🍳 开始做: 红烧肉
🍳 开始做: 蛋花汤      ← 三道菜"同时"开始做
✅ 蛋花汤 做好了！(耗时 1s)    ← 最快的先好
✅ 番茄炒蛋 做好了！(耗时 2s)
✅ 红烧肉 做好了！(耗时 5s)    ← 最慢的最后
# 总耗时: ~5秒（不是 2+5+1=8 秒！）
```

> 💡 **事件循环就像餐厅唯一的服务员**：它不会站在厨房等红烧肉炖好（那要 5 分钟），而是先去做蛋花汤（1 分钟就好），再去翻炒番茄炒蛋。所有"等待"时间都被重叠利用了。

### 2.3 await：暂停点标记

`await` 是异步编程中最重要的一个关键字。它的意思是：

> **"这个操作需要等待，我先让出 CPU，等结果回来再继续。"**

**三条核心规则：**

```python
# ✅ 规则 1：await 只能在 async def 函数内使用
async def good():
    await asyncio.sleep(1)  # ✅ 合法

def bad():
    await asyncio.sleep(1)  # ❌ SyntaxError!

# ✅ 规则 2：只有"可等待对象"才能被 await
async def example():
    await asyncio.sleep(1)        # ✅ 协程
    await some_async_function()   # ✅ async def 定义的函数
    await asyncio.create_task(x)  # ✅ Task 对象
    
    await 42                      # ❌ TypeError! 数字不可等待
    await print("hello")          # ❌ TypeError! 普通函数不可等待

# ✅ 规则 3：忘了 await，协程就不会执行
async def oops():
    asyncio.sleep(1)              # ⚠️ 没有 await！这行什么都不做
    # Python 会警告: RuntimeWarning: coroutine was never awaited
```

**哪些东西可以 `await`？哪些不行？**

| 可以 `await` ✅ | 不可以 `await` ❌ |
|:---|:---|
| `asyncio.sleep()` | `time.sleep()`（会阻塞整个线程！） |
| `httpx.AsyncClient.get()` | `requests.get()`（同步库） |
| `async_session.execute()` | `session.execute()`（同步 ORM） |
| 任何 `async def` 定义的函数 | 任何普通 `def` 定义的函数 |
| `asyncio.create_task()` 返回的 Task | `open()` 读文件（用 `aiofiles` 代替） |

> 💡 **一句话总结**：`await` = "这里会等，先让别人用 CPU"。就像你在奶茶店下单后拿了个号码牌，然后去隔壁买东西，号码被叫到了再回来取奶茶。

### 2.4 async def vs def：到底区别在哪？

搞清楚这两者的区别，是成为异步程序员的分水岭。

```python
import asyncio
import time

# ──────────────────────────────────────────
# 普通函数：同步执行，调用即执行，阻塞式
# ──────────────────────────────────────────
def sync_task():
    time.sleep(1)           # 🚫 阻塞整个线程！
    return "sync done"

# ──────────────────────────────────────────
# 协程函数：异步执行，调用返回协程对象，非阻塞
# ──────────────────────────────────────────
async def async_task():
    await asyncio.sleep(1)  # ✅ 暂停协程，不阻塞线程
    return "async done"
```

**一张表讲清楚所有区别：**

| 对比维度 | `def`（普通函数） | `async def`（协程函数） |
|:---|:---|:---|
| 调用方式 | `result = func()` 直接拿结果 | `coro = func()` 拿到协程对象 |
| 执行方式 | 立即执行 | 需要 `await` 或 `asyncio.run()` |
| 等待操作 | `time.sleep(1)` 阻塞线程 | `await asyncio.sleep(1)` 让出线程 |
| 能否并发 | ❌ 串行执行 | ✅ 可以和其他协程并发 |
| 适用场景 | CPU 密集型、简单逻辑 | I/O 密集型（网络/数据库/文件） |

**什么时候用 `def`，什么时候用 `async def`？**

```
写一个函数时问自己：
    这个函数里有没有 I/O 操作（网络请求/数据库查询/文件读写）？
    │
    ├── 有  → async def + await → 不阻塞事件循环
    │
    └── 没有（纯计算/简单逻辑） → 普通 def 就好
```

> 💡 **常见误区**：不是所有函数都要加 `async`。如果一个函数里只有 `return a + b` 这种纯计算，加了 `async` 反而增加开销（创建协程对象有成本）。**只在有 I/O 等待的地方用异步。**

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **协程 (Coroutine)** | 可以暂停和恢复的函数，用 `async def` 定义 |
| **事件循环 (Event Loop)** | 调度协程的中心引擎，决定"谁先执行" |
| **await** | 暂停当前协程，让事件循环去执行其他就绪的协程 |
| **asyncio.run()** | 启动事件循环的入口，整个程序只调用一次 |
| **create_task()** | 把协程注册到事件循环，让它可以被并发调度 |

---

## 3. asyncio 基础实战

概念搞清楚了，该动手写代码了。这一章我们逐个击破 `asyncio` 最常用的 API。

### 3.1 第一个异步程序：asyncio.run()

`asyncio.run()` 是异步世界的"大门"——整个程序的入口，通常**只调用一次**。

```python
import asyncio

async def say_hello(name, delay):
    """一个简单的异步任务"""
    await asyncio.sleep(delay)
    print(f"Hello, {name}! (等了 {delay}s)")
    return f"{name} done"

async def main():
    """主协程：程序的入口"""
    result = await say_hello("World", 1)
    print(result)

# asyncio.run() 做了三件事：
# 1. 创建事件循环
# 2. 运行 main() 协程
# 3. 运行完毕后关闭事件循环
asyncio.run(main())
```

**常见错误：**

```python
# ❌ 错误 1：直接 await（不在 async def 里）
await say_hello("World", 1)  # SyntaxError!

# ❌ 错误 2：多次调用 asyncio.run()
asyncio.run(task_a())
asyncio.run(task_b())  # ⚠️ 虽然不报错，但每次都创建新的事件循环，效率低

# ✅ 正确做法：在 main() 里组织所有任务
async def main():
    await task_a()
    await task_b()
asyncio.run(main())  # 只调用一次
```

### 3.2 并发执行：asyncio.gather() vs asyncio.create_task()

这是最核心的 API——**让多个协程"同时"运行**。

#### `asyncio.gather()`：一把梭，全部并发

```python
import asyncio

async def fetch_data(source, delay):
    print(f"📡 开始请求 {source}...")
    await asyncio.sleep(delay)
    return f"{source} 的数据"

async def main():
    # gather 接收多个协程，同时执行，返回所有结果（有序）
    results = await asyncio.gather(
        fetch_data("数据库", 2),
        fetch_data("Redis", 0.5),
        fetch_data("外部API", 3),
    )
    
    print(results)
    # ['数据库 的数据', 'Redis 的数据', '外部API 的数据']
    # 总耗时 ≈ 3 秒（最慢的那个），不是 2+0.5+3=5.5 秒

asyncio.run(main())
```

#### `asyncio.create_task()`：更灵活的控制

```python
async def main():
    # create_task 把协程"提交"给事件循环，立即开始调度
    task1 = asyncio.create_task(fetch_data("数据库", 2))
    task2 = asyncio.create_task(fetch_data("Redis", 0.5))
    
    # 你可以先做别的事...
    print("🔄 任务已提交，我先做点别的计算...")
    
    # 需要结果时再 await
    result1 = await task1
    result2 = await task2
    print(f"结果: {result1}, {result2}")

asyncio.run(main())
```

#### 选择指南

| 场景 | 用什么 | 理由 |
|:---|:---|:---|
| 同时请求多个 API，等全部返回 | `gather()` | 简洁，自动收集结果 |
| 提交任务后还要做别的事 | `create_task()` | 灵活，可以延迟 await |
| 需要逐个处理完成的任务 | `create_task()` + `as_completed()` | 谁先好先处理谁 |
| 任务数量动态决定 | `gather(*task_list)` | 用列表解包传入 |

> 💡 **经验法则**：大多数情况用 `gather()` 就够了。只有当你需要"提交任务后不立刻等结果"时，才需要 `create_task()`。

### 3.3 超时控制：asyncio.wait_for()

在真实项目中，你不能让一个请求无限等下去。`wait_for()` 可以给任何协程加一个"倒计时"。

```python
import asyncio

async def slow_api_call():
    """模拟一个很慢的 API"""
    await asyncio.sleep(10)  # 模拟 10 秒才返回
    return "终于回来了"

async def main():
    try:
        # 給 slow_api_call 最多 3 秒的时间
        result = await asyncio.wait_for(slow_api_call(), timeout=3.0)
        print(result)
    except asyncio.TimeoutError:
        print("⏰ 超时了！3 秒内没响应，放弃")

asyncio.run(main())
# 输出: ⏰ 超时了！3 秒内没响应，放弃
```

**实际应用：给 gather 里的每个任务加超时**

```python
async def safe_fetch(url, timeout=5):
    """带超时保护的请求"""
    try:
        return await asyncio.wait_for(
            actual_fetch(url), 
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return f"❌ {url} 超时"

async def main():
    results = await asyncio.gather(
        safe_fetch("api-1.com"),
        safe_fetch("api-2.com"),
        safe_fetch("slow-api.com", timeout=2),  # 给慢的 API 更短的超时
    )
    print(results)
```

> 💡 **生产环境必须加超时**。没有超时控制的异步代码就像没有保险的赛车——跑得快，但迟早出事。

### 3.4 异步迭代与异步生成器

在第一阶段你学过普通的生成器 (`yield`)。异步版本就是加上 `async`，用 `async for` 来遍历。

**这在 AI 应用中非常常见**——比如 ChatGPT 的流式响应 (SSE)，就是一个字一个字"吐"出来的。

```python
import asyncio

# ──────────────────────────────────────────
# 异步生成器：用 async yield 一次返回一块数据
# ──────────────────────────────────────────
async def ai_stream_response(prompt):
    """模拟 LLM 的流式输出"""
    words = f"关于'{prompt}'的回答：异步编程是 Python 高性能的关键技术。".split()
    for word in words:
        await asyncio.sleep(0.3)  # 模拟网络延迟
        yield word                # async yield：每产生一个词就发送

# ──────────────────────────────────────────
# 用 async for 消费异步生成器
# ──────────────────────────────────────────
async def main():
    print("🤖 AI 正在思考...")
    
    # async for 逐块接收数据，不用等全部生成完
    async for word in ai_stream_response("什么是异步"):
        print(word, end=" ", flush=True)  # 逐词打印，模拟打字效果
    
    print("\n✅ 回答完毕")

asyncio.run(main())
```

**输出效果（逐词出现，就像 ChatGPT）：**

```
🤖 AI 正在思考...
关于'什么是异步'的回答：异步编程是 Python 高性能的关键技术。
✅ 回答完毕
```

> 💡 **实际用途**：在 FastAPI 中，`StreamingResponse` + 异步生成器 = SSE 流式接口。前端收到一个字就显示一个字，用户体验远好于"等 10 秒突然刷出整段文字"。

**第 3 章 API 速查表：**

| API | 用途 | 示例 |
|:---|:---|:---|
| `asyncio.run(main())` | 启动事件循环，程序入口 | 整个程序只调一次 |
| `asyncio.gather(*coros)` | 并发执行多个协程，等全部完成 | 批量 API 请求 |
| `asyncio.create_task(coro)` | 注册协程到事件循环 | 提交后做别的事 |
| `asyncio.wait_for(coro, timeout)` | 给协程加超时限制 | 防止无限等待 |
| `asyncio.sleep(seconds)` | 异步等待（不阻塞） | 模拟延迟、限流 |
| `async for ... in ...` | 遍历异步迭代器 | 流式处理数据 |

---

## 4. 异步 HTTP 请求：aiohttp / httpx

异步编程最高频的实战场景就是**网络请求**。这一章我们用 `httpx` 来实现真正的异步 HTTP 调用。

### 4.1 httpx：requests 的异步替代品

`httpx` 是 `requests` 的现代替代品，**同时支持同步和异步**，API 几乎一模一样，迁移零成本。

**安装：**

```bash
pip install httpx
```

**对比 requests 和 httpx：**

```python
# ──────────────────────────────────────────
# requests（同步）：你已经很熟了
# ──────────────────────────────────────────
import requests

response = requests.get("https://httpbin.org/get")
print(response.json())

# ──────────────────────────────────────────
# httpx（同步模式）：几乎一样的写法
# ──────────────────────────────────────────
import httpx

response = httpx.get("https://httpbin.org/get")
print(response.json())

# ──────────────────────────────────────────
# httpx（异步模式）：套上 async/await
# ──────────────────────────────────────────
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:  # 用 async with 管理连接
        response = await client.get("https://httpbin.org/get")
        print(response.json())

asyncio.run(main())
```

> 💡 **为什么推荐 httpx 而不是 aiohttp？** httpx 的 API 和 requests 完全一致，学习成本为零。而且它同时支持同步/异步两种模式，在测试或脚本中也能直接用。aiohttp 功能更强但 API 差异大，适合深度定制的场景。

### 4.2 实战：异步批量调用 API（以 LLM 接口为例）

这是你在 AI 应用开发中**最常遇到的场景**：一次性给 10 个用户生成内容，同步调用要等 10 倍时间，异步只需要等最慢的那个。

```python
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AI_API_KEY")
BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com/v1")

async def call_llm(client: httpx.AsyncClient, prompt: str) -> str:
    """异步调用大模型 API"""
    response = await client.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
        },
        timeout=30.0,  # 别忘了超时！
    )
    data = response.json()
    return data["choices"][0]["message"]["content"]

async def main():
    # 批量生成 5 个主题的摘要
    topics = ["Python异步编程", "Docker入门", "Redis缓存", "JWT认证", "WebSocket"]
    
    async with httpx.AsyncClient() as client:
        # 用 gather 并发调用 5 次 LLM
        tasks = [
            call_llm(client, f"用一句话解释{topic}")
            for topic in topics
        ]
        results = await asyncio.gather(*tasks)
    
    for topic, result in zip(topics, results):
        print(f"📝 {topic}: {result}\n")

asyncio.run(main())
# 5 个请求并发执行，总耗时 ≈ 最慢的那个请求（约2-3秒）
# 而不是 5 × 2秒 = 10秒
```

> 💡 **关键点**：`httpx.AsyncClient()` 要用 `async with` 来管理。它内部维护了连接池（Connection Pool），复用 TCP 连接，比每次新建连接快得多。

### 4.3 并发限制：asyncio.Semaphore 控制并发数

上面的代码有个隐患：如果你有 1000 个任务同时 `gather`，会瞬间发出 1000 个请求。大多数 API 都有限流 (Rate Limit)，会直接返回 `429 Too Many Requests`。

**Semaphore（信号量）** 就是解决这个问题的——它像一把只有 N 把钥匙的锁，同时最多只有 N 个协程能"通过"。

```python
import asyncio
import httpx

async def fetch_with_limit(
    client: httpx.AsyncClient, 
    url: str, 
    semaphore: asyncio.Semaphore
):
    """带并发限制的请求"""
    async with semaphore:  # 获取"钥匙"，没有就等
        print(f"🔓 获取许可，请求 {url}")
        response = await client.get(url)
        print(f"✅ 完成 {url} (状态码: {response.status_code})")
        return response.text

async def main():
    # 最多同时 3 个请求（即使有 20 个任务）
    semaphore = asyncio.Semaphore(3)
    
    urls = [f"https://httpbin.org/delay/1?id={i}" for i in range(10)]
    
    async with httpx.AsyncClient() as client:
        tasks = [fetch_with_limit(client, url, semaphore) for url in urls]
        results = await asyncio.gather(*tasks)
    
    print(f"共完成 {len(results)} 个请求")

asyncio.run(main())
# 10 个请求，每次最多并发 3 个
# 第 1 批: 请求 0,1,2 同时执行
# 第 2 批: 请求 3,4,5（等前面有完成的才开始）
# ...
# 总耗时 ≈ 4 秒（而不是不限流的 1 秒或串行的 10 秒）
```

**常用并发数参考：**

| 场景 | 建议并发数 | 理由 |
|:---|:---|:---|
| OpenAI / DeepSeek API | 5~10 | 免费版 RPM 限制通常 60/分钟 |
| 爬虫抓取网页 | 10~20 | 太快会被封 IP |
| 内部微服务调用 | 50~100 | 内部服务通常能扛 |
| 数据库连接 | 取决于连接池大小 | 通常 10~20 |

### 4.4 错误处理与重试机制

网络请求最大的特点就是"不靠谱"——超时、断连、限流、服务器 500 随时可能发生。**没有重试机制的异步代码不是生产级代码。**

#### 基础版：try/except + 手动重试

```python
import asyncio
import httpx

async def fetch_with_retry(
    client: httpx.AsyncClient, 
    url: str, 
    max_retries: int = 3
) -> str:
    """带重试的异步请求"""
    for attempt in range(1, max_retries + 1):
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()  # 4xx/5xx 会抛异常
            return response.text
        
        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            if attempt == max_retries:
                print(f"❌ {url} 失败，已重试 {max_retries} 次: {e}")
                return None
            
            # 指数退避：1秒 → 2秒 → 4秒（避免雪崩）
            wait = 2 ** (attempt - 1)
            print(f"⚠️ 第 {attempt} 次失败，{wait}s 后重试: {e}")
            await asyncio.sleep(wait)
```

#### 进阶版：通用重试装饰器

```python
import asyncio
import functools

def async_retry(max_retries=3, backoff_base=2, exceptions=(Exception,)):
    """
    异步重试装饰器（可复用）
    
    用法: @async_retry(max_retries=3)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise  # 最后一次还失败，抛出异常
                    wait = backoff_base ** (attempt - 1)
                    print(f"⚠️ {func.__name__} 第{attempt}次失败，{wait}s后重试")
                    await asyncio.sleep(wait)
        return wrapper
    return decorator

# 使用示例：
@async_retry(max_retries=3, exceptions=(httpx.TimeoutException,))
async def call_api(client, url):
    response = await client.get(url, timeout=5.0)
    return response.json()
```

> 💡 **指数退避 (Exponential Backoff)** 是行业标准做法。第 1 次失败等 1 秒，第 2 次等 2 秒，第 3 次等 4 秒……避免所有客户端同时重试导致服务器雪崩。AWS、Google Cloud 的 SDK 都用这个策略。

**第 4 章核心模式总结：**

```
异步 HTTP 请求的生产级写法：

httpx.AsyncClient()        → 管理连接池
  + asyncio.gather()       → 并发执行
  + asyncio.Semaphore()    → 控制并发数
  + async_retry()          → 失败自动重试
  + timeout                → 超时保护

五件套齐了，你的异步请求代码就是生产级的了 🎯
```

---

## 5. 异步数据库操作：SQLAlchemy Async

你的 FastAPI 后端每处理一个请求，都要查数据库。如果用同步方式查询，事件循环就被**卡死**了——等于异步白学了。这一章教你用 SQLAlchemy 2.0 的异步模式来避免这个问题。

### 5.1 为什么数据库操作也要异步？

先看一个直观的对比：

```
场景：100 个用户同时请求 /api/users（每次查询耗时 50ms）

同步路由 + 同步 DB：
├── 请求 1 → 查数据库（50ms）→ 返回 ← 在这 50ms 里其他 99 个请求排队等
├── 请求 2 → 查数据库（50ms）→ 返回
├── ...
└── 总耗时: 100 × 50ms = 5000ms 😱

异步路由 + 异步 DB：
├── 请求 1 → 发查询（await）→ 等的时候处理请求 2、3、4...
├── 请求 2 → 发查询（await）→ 等的时候处理请求 5、6、7...
├── ...（所有查询几乎同时在等）
└── 总耗时: ≈ 50ms（只等最慢的那个）🚀
```

> 💡 **数据库查询的本质也是 I/O 操作**（发 SQL → 等数据库引擎处理 → 收结果），和网络请求一样适合异步。

### 5.2 SQLAlchemy 2.0 异步引擎配置

**安装依赖：**

```bash
# aiosqlite: SQLite 的异步驱动
# asyncpg: PostgreSQL 的异步驱动（生产推荐）
pip install sqlalchemy[asyncio] aiosqlite
# 或者生产环境用 PostgreSQL:
# pip install sqlalchemy[asyncio] asyncpg
```

**完整配置（可直接复制到项目中）：**

```python
# database.py — 异步数据库配置

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# ──────────────────────────────────────────
# 1. 创建异步引擎（注意 URL 前缀不同）
# ──────────────────────────────────────────
# SQLite 异步:  sqlite+aiosqlite:///./app.db
# PostgreSQL:   postgresql+asyncpg://user:pass@localhost/dbname

DATABASE_URL = "sqlite+aiosqlite:///./app.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,       # 开发时打印 SQL 语句，生产环境关掉
    pool_size=20,     # 连接池大小（同时最多 20 个连接）
    max_overflow=10,  # 超出 pool_size 后最多再创建 10 个临时连接
)

# ──────────────────────────────────────────
# 2. 创建异步 Session 工厂
# ──────────────────────────────────────────
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不过期对象（避免 lazy load 报错）
)

# ──────────────────────────────────────────
# 3. 基类
# ──────────────────────────────────────────
class Base(DeclarativeBase):
    pass

# ──────────────────────────────────────────
# 4. 获取 Session 的依赖（给 FastAPI 用）
# ──────────────────────────────────────────
async def get_db():
    """FastAPI 依赖注入：每个请求一个 Session"""
    async with async_session() as session:
        yield session  # yield = 请求处理期间持有 session
        # async with 结束时自动关闭 session
```

**同步 vs 异步配置对比：**

| 配置项 | 同步写法 | 异步写法 |
|:---|:---|:---|
| 引擎 | `create_engine()` | `create_async_engine()` |
| Session | `sessionmaker()` | `async_sessionmaker()` |
| DB URL | `sqlite:///./app.db` | `sqlite+aiosqlite:///./app.db` |
| PostgreSQL URL | `postgresql://...` | `postgresql+asyncpg://...` |
| Session 类 | `Session` | `AsyncSession` |

### 5.3 AsyncSession 的正确用法

有了配置，来看实际的增删改查 (CRUD) 怎么用异步 Session 来写。

**先定义一个模型：**

```python
# models.py
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)
```

**异步 CRUD 操作：**

```python
# crud.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User

# ──────── 查询 ────────
async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """异步查询单个用户"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()  # 返回一个对象或 None

async def get_all_users(session: AsyncSession) -> list[User]:
    """异步查询所有用户"""
    result = await session.execute(select(User))
    return result.scalars().all()  # 返回列表

# ──────── 创建 ────────
async def create_user(session: AsyncSession, name: str, email: str) -> User:
    """异步创建用户"""
    user = User(name=name, email=email)
    session.add(user)
    await session.commit()      # 异步提交！
    await session.refresh(user) # 刷新获取数据库生成的 id
    return user

# ──────── 删除 ────────
async def delete_user(session: AsyncSession, user_id: int) -> bool:
    """异步删除用户"""
    user = await get_user_by_id(session, user_id)
    if user:
        await session.delete(user)
        await session.commit()
        return True
    return False
```

> 💡 **核心区别就一个**：所有涉及数据库 I/O 的操作前面都加 `await`。`session.execute()`、`session.commit()`、`session.refresh()` 都是异步的。

### 5.4 异步事务管理

当多个数据库操作需要"要么全成功，要么全回滚"时，就需要**事务 (Transaction)**。

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def transfer_credits(
    session: AsyncSession, 
    from_id: int, 
    to_id: int, 
    amount: int
):
    """
    转移积分：从 A 用户 → B 用户
    必须在一个事务里完成，否则可能出现 A 扣了但 B 没加的情况
    """
    async with session.begin():  # 开启事务，出错自动回滚
        # 查询两个用户
        from_user = await session.get(User, from_id)
        to_user = await session.get(User, to_id)
        
        if from_user.credits < amount:
            raise ValueError("积分不足")
        
        # 两个操作在同一个事务里
        from_user.credits -= amount
        to_user.credits += amount
        
        # session.begin() 的 async with 结束时自动 commit
        # 如果中间抛异常，自动 rollback
```

**事务管理的三种写法：**

```python
# 方式 1：session.begin()（推荐 ✅）
async with session.begin():
    session.add(user)
    # 自动 commit，出错自动 rollback

# 方式 2：手动 commit/rollback
try:
    session.add(user)
    await session.commit()
except Exception:
    await session.rollback()
    raise

# 方式 3：嵌套事务（Savepoint）
async with session.begin():
    session.add(user_a)
    
    async with session.begin_nested():  # 嵌套事务
        session.add(user_b)
        # 这里失败只回滚 user_b，不影响 user_a
```

> 💡 **推荐方式 1**。`async with session.begin()` 最安全——成功自动提交，异常自动回滚，不用手动写 try/except。

**第 5 章知识回顾：**

| 组件 | 作用 | 关键点 |
|:---|:---|:---|
| `create_async_engine()` | 创建连接池 | URL 前缀不同：`+aiosqlite` / `+asyncpg` |
| `async_sessionmaker()` | Session 工厂 | `expire_on_commit=False` 避免懒加载报错 |
| `AsyncSession` | 异步 Session | 所有操作前加 `await` |
| `session.begin()` | 事务管理 | `async with` 自动提交/回滚 |

---

## 6. 异步与 FastAPI 深度结合

前 5 章学的所有知识，在这一章汇聚。FastAPI 天生就是为异步设计的框架——让我们把 httpx、SQLAlchemy Async、WebSocket 全部接入。

### 6.1 FastAPI 的异步运行机制

FastAPI 底层使用 **Uvicorn**（ASGI 服务器）+ **Starlette**（异步 Web 框架），天然运行在一个事件循环上。

```
请求进来的完整链路：

用户浏览器
   │ HTTP 请求
   ▼
Uvicorn (ASGI Server)
   │ 转发给 FastAPI
   ▼
FastAPI 路由匹配
   │
   ├── async def 路由 → 直接在事件循环中执行 ✅ 高效
   │
   └── def 路由 → 扔到线程池执行 ⚠️ 有开销
```

**关键理解**：FastAPI 对 `async def` 和 `def` 的处理方式**完全不同**：

| 路由类型 | 执行方式 | 是否阻塞事件循环 |
|:---|:---|:---|
| `async def` | 在事件循环中直接执行 | 取决于你是否用了 `await` |
| `def` | 自动放到**线程池**中执行 | 不阻塞（但有线程切换开销） |

### 6.2 async def vs def 路由：什么时候该用哪个？

这是 FastAPI 开发中**最容易搞错**的地方。搞错了不会报错，但性能会悄悄下降。

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

# ──────────────────────────────────────────
# ✅ 正确：路由里有 await 操作 → 用 async def
# ──────────────────────────────────────────
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))  # 异步查数据库
    return result.scalars().all()

# ──────────────────────────────────────────
# ✅ 正确：路由里只有纯计算 → 用 def
# ──────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok"}  # 没有 I/O，不需要 async

# ──────────────────────────────────────────
# ❌ 错误：async def 里调用同步阻塞操作
# ──────────────────────────────────────────
@app.get("/bad")
async def bad_route():
    import time
    time.sleep(5)       # 🚫 阻塞整个事件循环 5 秒！所有请求排队等
    return {"data": "..."}

# ──────────────────────────────────────────
# ✅ 修复：如果必须调同步代码，用 run_in_executor
# ──────────────────────────────────────────
import asyncio

@app.get("/fixed")
async def fixed_route():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, blocking_function)  # 扔到线程池
    return {"data": result}
```

**决策流程图：**

```
你的路由函数里有什么操作？
│
├── 有 await（异步 DB/HTTP/Redis）
│   └── 用 async def ✅
│
├── 有同步阻塞（requests.get / time.sleep / 同步 ORM）
│   ├── 能换成异步版？ → 换掉，用 async def ✅
│   └── 换不了？ → 用 def（FastAPI 自动放线程池）✅
│
└── 纯计算（return a + b）
    └── 用 def ✅（async 也行，但没必要多此一举）
```

### 6.3 后台任务：BackgroundTasks vs Celery

有些操作不需要用户等结果——比如发邮件、生成报告、写日志。这种任务应该放到"后台"执行。

#### FastAPI 内置的 BackgroundTasks（轻量级）

```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

async def send_welcome_email(email: str):
    """后台发送邮件（用户不用等）"""
    print(f"📧 正在发送欢迎邮件到 {email}...")
    await asyncio.sleep(3)  # 模拟发邮件耗时
    print(f"✅ 邮件已发送到 {email}")

@app.post("/register")
async def register(email: str, bg: BackgroundTasks):
    # 1. 创建用户（用户等这个）
    user = {"email": email, "id": 1}
    
    # 2. 发邮件放到后台（用户不用等）
    bg.add_task(send_welcome_email, email)
    
    # 3. 立即返回（邮件在后台慢慢发）
    return {"message": "注册成功！欢迎邮件稍后到达"}
```

#### 什么时候用 BackgroundTasks，什么时候用 Celery？

| 对比 | BackgroundTasks | Celery |
|:---|:---|:---|
| 复杂度 | 零配置，FastAPI 内置 | 需要 Redis/RabbitMQ 做消息队列 |
| 执行位置 | 同一个进程内 | 独立的 Worker 进程 |
| 适用场景 | 发邮件、写日志、轻量通知 | 视频转码、AI 推理、批量数据处理 |
| 任务时长 | < 30 秒 | 几分钟到几小时 |
| 失败重试 | ❌ 无 | ✅ 自动重试、死信队列 |
| 任务监控 | ❌ 无 | ✅ Flower 监控面板 |

> 💡 **经验法则**：如果任务 < 30 秒且失败了无所谓 → `BackgroundTasks`。如果任务很重、需要重试、需要监控 → 上 Celery。

### 6.4 WebSocket 实时通信

WebSocket 是异步编程的"天然主场"——持久连接、双向通信、实时推送，全都需要非阻塞的事件循环。

**实战场景：AI 对话的实时流式输出**

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio

app = FastAPI()

async def ai_generate(prompt: str):
    """模拟 AI 流式生成回答"""
    answer = f"关于'{prompt}'：异步编程让 Python 后端性能提升数倍。"
    for char in answer:
        await asyncio.sleep(0.05)  # 模拟逐字生成
        yield char

@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()  # 接受 WebSocket 连接
    print("🔗 客户端已连接")
    
    try:
        while True:
            # 1. 接收用户消息
            user_message = await websocket.receive_text()
            print(f"👤 用户: {user_message}")
            
            # 2. 流式返回 AI 回复（逐字推送）
            async for char in ai_generate(user_message):
                await websocket.send_text(char)
            
            # 3. 发送结束标记
            await websocket.send_text("[END]")
    
    except WebSocketDisconnect:
        print("🔌 客户端断开连接")
```

**前端对接（极简 HTML）：**

```html
<script>
const ws = new WebSocket("ws://localhost:8000/ws/chat");
ws.onmessage = (event) => {
    if (event.data === "[END]") {
        console.log("回答完毕");
    } else {
        document.getElementById("output").innerText += event.data;
    }
};
ws.onopen = () => ws.send("什么是异步编程？");
</script>
<div id="output"></div>
```

> 💡 **为什么 AI 对话要用 WebSocket 而不是 SSE？** SSE 是单向的（服务器 → 客户端），适合简单的流式输出。WebSocket 是双向的，适合连续对话场景（用户可以随时发新消息、中断生成）。

**第 6 章知识回顾：**

| 技术点 | 何时使用 |
|:---|:---|
| `async def` 路由 | 路由里有 `await` 操作 |
| `def` 路由 | 纯计算或必须调用同步库 |
| `BackgroundTasks` | 轻量后台任务（< 30s） |
| `Celery` | 重型异步任务（分钟级） |
| `WebSocket` | 实时双向通信（聊天/通知） |

---

## 7. 异步编程的坑与最佳实践

异步代码"能跑"和"跑得对"是两回事。这一章总结了实战中最高频的 3 个坑，每个坑都有**错误代码 vs 正确代码**的直接对比。

### 7.1 坑一：在异步函数里调用同步阻塞代码

**这是最常见、杀伤力最大的坑。** 一个 `time.sleep()` 就能让整个服务器瘫痪。

```python
# ❌ 错误：async 里用 time.sleep（阻塞事件循环）
async def bad_handler():
    time.sleep(5)       # 整个事件循环卡死 5 秒
    return "done"       # 这 5 秒内所有其他请求都排队

# ✅ 正确：用 asyncio.sleep（非阻塞）
async def good_handler():
    await asyncio.sleep(5)  # 只暂停这个协程，其他协程正常运行
    return "done"
```

**常见"隐形杀手"清单（这些你可能不知道是阻塞的）：**

| 隐形阻塞操作 | 异步替代品 |
|:---|:---|
| `requests.get()` | `httpx.AsyncClient().get()` |
| `open().read()` | `aiofiles.open()` |
| `time.sleep()` | `asyncio.sleep()` |
| `session.execute()` (同步 ORM) | `await async_session.execute()` |
| `subprocess.run()` | `asyncio.create_subprocess_exec()` |
| `json.loads(大文件)` | `await loop.run_in_executor(None, json.loads, data)` |

**万能修复方案：`run_in_executor`**

如果实在没有异步替代品，把同步代码扔到线程池：

```python
import asyncio

async def safe_blocking_call():
    loop = asyncio.get_event_loop()
    # None = 使用默认线程池，blocking_io = 你的同步函数
    result = await loop.run_in_executor(None, blocking_io)
    return result
```

### 7.2 坑二：忘记 await 导致协程没执行

这个坑**不会报错**，只会给你一个警告，然后默默地什么都不做。

```python
# ❌ 错误：忘了 await，协程只被创建，没有执行
async def process():
    asyncio.sleep(1)          # ⚠️ 返回了一个协程对象，但没执行
    fetch_data_from_db()      # ⚠️ 如果这是 async def，同样没执行
    print("处理完成")          # 这行立刻执行了，但上面啥都没干

# Python 会给你一个警告（但不是错误！）：
# RuntimeWarning: coroutine 'sleep' was never awaited

# ✅ 正确：每个异步调用前都加 await
async def process():
    await asyncio.sleep(1)
    await fetch_data_from_db()
    print("处理完成")
```

**如何避免这个坑？**

```python
# 方法 1：开启警告（开发环境）
import warnings
warnings.filterwarnings("error", category=RuntimeWarning)
# 这样忘了 await 就直接报错，而不是只给个警告

# 方法 2：使用类型检查（推荐）
# 安装 mypy：pip install mypy
# 运行：mypy your_code.py
# mypy 会直接报错："Coroutine value is not used"
```

### 7.3 坑三：并发竞争与数据安全

多个协程"同时"访问共享数据时，可能出现数据不一致的问题。

```python
# ❌ 危险：多个协程同时修改同一个变量
counter = 0

async def increment():
    global counter
    temp = counter        # 协程 A 读到 counter = 0
    await asyncio.sleep(0.01)  # A 暂停，B 也读到 counter = 0
    counter = temp + 1    # A 写入 1，B 也写入 1（应该是 2！）

async def main():
    global counter
    counter = 0
    await asyncio.gather(*[increment() for _ in range(100)])
    print(f"最终值: {counter}")  # 期望 100，实际可能是 1 😱

# ✅ 安全：使用 asyncio.Lock
lock = asyncio.Lock()

async def safe_increment():
    global counter
    async with lock:       # 同一时间只有一个协程能进入
        temp = counter
        await asyncio.sleep(0.01)
        counter = temp + 1
```

**什么时候需要 Lock？**

| 场景 | 需要 Lock？ |
|:---|:---|
| 多个协程各自独立请求 API | ❌ 不需要 |
| 多个协程读同一个变量 | ❌ 只读不需要 |
| 多个协程修改同一个变量 | ✅ 需要 |
| 多个协程写同一个文件 | ✅ 需要 |
| 数据库操作 | ❌ 事务已经保护了 |

> 💡 **好消息**：Python 的 asyncio 是单线程的，只有在 `await` 点才会切换协程。所以只要你的"读→改→写"之间没有 `await`，就天然是安全的。

### 7.4 最佳实践清单

把第 7 章的经验浓缩成一张检查清单，写完异步代码后对照一遍：

```
✅ 异步代码审查清单

□ 所有 I/O 操作都用了 await？
  └── requests → httpx | time.sleep → asyncio.sleep | open → aiofiles

□ 没有在 async def 里调用同步阻塞函数？
  └── 实在无法避免就用 run_in_executor()

□ 每个 async 函数调用都有 await？
  └── 用 mypy 自动检查

□ 给所有外部请求加了超时？
  └── asyncio.wait_for() 或 httpx 的 timeout 参数

□ 大批量并发加了 Semaphore 限流？
  └── 根据目标 API 的限流策略设定并发数

□ 异步 Session/Client 用了 async with 管理？
  └── httpx.AsyncClient() / async_sessionmaker()

□ 共享可变状态有加锁保护？
  └── 大多数情况不需要，只在"读→await→写"模式下需要

□ 网络请求有重试机制？
  └── 指数退避 + 最大重试次数
```

---

## 8. 进阶：理解事件循环底层原理

这一章不影响你写业务代码，但会让你在面试中脱颖而出，也能帮你调试诡异的异步问题。

### 8.1 事件循环的工作原理（图解）

事件循环的核心就是一个 `while True` 循环，不停地做三件事：

```
事件循环的一轮 (Tick)
══════════════════════════════════════════════════

① 检查就绪队列：有没有可以立即执行的协程？
   │
   ├── 有 → 拿出来执行，直到它遇到 await
   │         └── await 后面的 I/O 还没好？→ 放回等待队列
   │         └── await 后面的 I/O 已完成？→ 继续执行
   │
   └── 没有 → 检查 I/O 事件

② 检查 I/O 事件：有没有完成的网络/文件/定时器操作？
   │
   ├── 有 → 把对应的协程从"等待"移到"就绪"
   └── 没有 → 短暂 sleep，避免 CPU 空转

③ 处理回调：有没有注册的回调函数需要执行？
   │
   └── 执行回调

→ 回到 ①，继续下一轮
```

### 8.2 手撕一个 50 行的迷你事件循环

理解原理最好的方式就是**自己写一个**。以下是一个极简的事件循环，只用 Python 标准库：

```python
import time
from collections import deque

class MiniEventLoop:
    """一个 50 行的迷你事件循环"""
    
    def __init__(self):
        self.ready = deque()     # 就绪队列：可以立即执行的任务
        self.sleeping = []       # 等待队列：定时器任务
    
    def call_soon(self, callback):
        """把任务加入就绪队列"""
        self.ready.append(callback)
    
    def call_later(self, delay, callback):
        """把任务加入定时等待队列"""
        deadline = time.time() + delay
        self.sleeping.append((deadline, callback))
        self.sleeping.sort()     # 按时间排序，最早的在前面
    
    def run_forever(self):
        """核心：事件循环的 while True"""
        while self.ready or self.sleeping:
            # ① 处理就绪队列
            while self.ready:
                callback = self.ready.popleft()
                callback()
            
            # ② 检查定时器：时间到了就移到就绪队列
            now = time.time()
            while self.sleeping and self.sleeping[0][0] <= now:
                _, callback = self.sleeping.pop(0)
                self.ready.append(callback)
            
            # ③ 如果没有就绪任务，短暂 sleep 避免 CPU 空转
            if not self.ready and self.sleeping:
                sleep_time = self.sleeping[0][0] - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)

# ──────── 使用示例 ────────
loop = MiniEventLoop()

def task_a():
    print(f"[{time.time():.1f}] 任务 A 执行")
    loop.call_later(2, task_a_done)  # 2 秒后执行回调

def task_a_done():
    print(f"[{time.time():.1f}] 任务 A 完成 (2秒后)")

def task_b():
    print(f"[{time.time():.1f}] 任务 B 执行")
    loop.call_later(1, task_b_done)  # 1 秒后执行回调

def task_b_done():
    print(f"[{time.time():.1f}] 任务 B 完成 (1秒后)")

loop.call_soon(task_a)  # 立即执行 A
loop.call_soon(task_b)  # 立即执行 B
loop.run_forever()

# 输出：
# [0.0] 任务 A 执行
# [0.0] 任务 B 执行     ← 两个任务"立即"开始
# [1.0] 任务 B 完成     ← B 先完成（只等 1 秒）
# [2.0] 任务 A 完成     ← A 后完成（等了 2 秒）
```

> 💡 **真正的 asyncio 事件循环**比这复杂得多（使用 `selectors` 模块监听 I/O 事件、支持协程/Future/Task 等），但核心思想完全一样：**就绪队列 + I/O 事件监听 + 循环调度**。

### 8.3 多线程 vs 多进程 vs 协程：终极对比

面试高频题。一张表讲清楚：

| 对比维度 | 多线程 (threading) | 多进程 (multiprocessing) | 协程 (asyncio) |
|:---|:---|:---|:---|
| **并发模型** | 抢占式（OS 调度） | 抢占式（OS 调度） | 协作式（代码主动 yield） |
| **GIL 影响** | ❌ 受 GIL 限制 | ✅ 每个进程独立 GIL | ❌ 单线程，无需 GIL |
| **适用场景** | I/O 密集型 | **CPU 密集型** | **I/O 密集型** |
| **内存开销** | 中（每线程 ~8MB 栈） | 高（每进程独立内存） | 极低（每协程 ~KB 级） |
| **创建开销** | 中（ms 级） | 高（100ms+ 级） | 极低（μs 级） |
| **并发数量** | 几百~几千 | 通常 = CPU 核数 | 轻松 **数万** |
| **数据共享** | 共享内存，需加锁 | 进程间通信（IPC） | 共享内存，await 点安全 |
| **调试难度** | 高（竞态条件） | 中 | 低（单线程，可预测） |
| **典型用途** | 爬虫、文件IO | 图像处理、科学计算 | Web 服务、API 网关 |

**选择决策树：**

```
你的任务是什么类型？
│
├── I/O 密集型（网络/数据库/文件）
│   ├── 需要高并发（1000+）→ asyncio 协程 ✅
│   └── 简单脚本，不想学 async → threading 也行
│
├── CPU 密集型（数学计算/图像处理/AI 推理）
│   └── multiprocessing ✅（绕过 GIL）
│
└── 混合型（先请求 API，再做 CPU 计算）
    └── asyncio + ProcessPoolExecutor
        → I/O 部分用协程，CPU 部分扔进程池
```

---

## 9. 核心概念速查表

一页纸总结全文精华，开发时随时回来翻阅。

### 关键词速查

| 关键词 | 含义 | 示例 |
|:---|:---|:---|
| `async def` | 定义协程函数 | `async def fetch():` |
| `await` | 暂停当前协程，等待结果 | `await asyncio.sleep(1)` |
| `asyncio.run()` | 启动事件循环（入口） | `asyncio.run(main())` |
| `asyncio.gather()` | 并发执行多个协程 | `await asyncio.gather(a(), b())` |
| `create_task()` | 注册协程到事件循环 | `task = asyncio.create_task(a())` |
| `wait_for()` | 超时控制 | `await asyncio.wait_for(a(), timeout=5)` |
| `Semaphore` | 控制并发数量 | `async with sem: await fetch()` |
| `Lock` | 异步锁，保护共享状态 | `async with lock: counter += 1` |
| `async with` | 异步上下文管理器 | `async with httpx.AsyncClient():` |
| `async for` | 异步迭代 | `async for chunk in stream():` |

### 常用异步库速查

| 需求 | 同步库 | 异步替代品 |
|:---|:---|:---|
| HTTP 请求 | `requests` | `httpx` / `aiohttp` |
| 数据库 ORM | `SQLAlchemy` | `SQLAlchemy[asyncio]` |
| PostgreSQL | `psycopg2` | `asyncpg` |
| SQLite | `sqlite3` | `aiosqlite` |
| Redis | `redis-py` | `redis.asyncio` |
| 文件操作 | `open()` | `aiofiles` |
| Web 框架 | `Flask` | `FastAPI` |
| 子进程 | `subprocess` | `asyncio.create_subprocess_exec()` |

### 决策速查

```
新写一个函数 → 有 I/O 操作吗？
├── 有 → async def + await
└── 没有 → 普通 def

选并发方案 → 什么类型的任务？
├── I/O 密集 → asyncio
├── CPU 密集 → multiprocessing
└── 混合 → asyncio + ProcessPoolExecutor

选 HTTP 库 → httpx（兼容 requests API）
选数据库 → SQLAlchemy + asyncpg/aiosqlite
选后台任务 → 轻量用 BackgroundTasks，重型用 Celery
选实时通信 → WebSocket
```

---

> 🎉 **恭喜你读完了整篇指南！** 从"为什么需要异步"到"手撕事件循环"，你已经具备了用 Python 异步编程构建高性能后端的全部知识。现在，去你的 FastAPI 项目里把同步代码改成异步的吧！
