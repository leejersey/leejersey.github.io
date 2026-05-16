# Harness Engineering：浏览器自动化 Agent 工程化实战

> 从 MCP 工具设计、Playwright 并行调度到 Orchestrator-Worker 任务编排——构建高成功率、可规模化的浏览器自动化 Agent 系统的完整工程方法论。

---

## 1. Harness Engineering 总论：从"能跑"到"跑得稳"

你让 GPT-4 打开浏览器、填一个表单、点一下提交——Demo 视频看起来丝滑无比。然后你把它放到生产环境，跑 1000 次，成功率 37%。

这个从「能跑」到「跑得稳」的鸿沟，就是 Harness Engineering 要解决的问题。

**Harness**（线束）这个词来自航天和汽车工业：发动机再强，如果线束不可靠，整辆车就是一堆废铁。在 AI Agent 系统中，LLM 是发动机，而 Harness Engineering 就是那套让发动机可靠运行的「线束工程」——工具层设计、并发调度、任务编排、上下文管理、可观测性，一切让 Agent 从实验品变成生产系统的工程化能力。

### 1.1 什么是 Harness Engineering？角色定位与能力模型

#### 定义

Harness Engineering（线束工程）是指：**围绕 AI Agent 核心能力（LLM 推理 + 工具调用），构建使其在生产环境中稳定、高效、可观测运行的全部工程化基础设施。**

它不是写 Prompt，不是训练模型，不是做前端——它是确保 Agent 系统在面对真实世界的复杂性（网络抖动、页面变化、并发冲突、资源泄漏、上下文溢出）时，依然能完成任务的那一层工程。

#### 与传统角色的区别

一个常见的误解是把 Harness Engineering 等同于「写自动化测试脚本」或「做 DevOps」。它们有交集，但定位完全不同：

| 维度 | QA / 测试工程师 | DevOps / SRE | Harness Engineer |
| :--- | :--- | :--- | :--- |
| **核心目标** | 验证软件行为是否符合预期 | 保障基础设施可用性 | 让 AI Agent 在生产环境稳定执行任务 |
| **控制对象** | 确定性代码路径 | 服务器/容器/网络 | 非确定性 Agent 行为 + 确定性工具层 |
| **面对的不确定性** | 低（测试用例明确） | 中（基础设施可预测） | 高（LLM 输出不可预测，外部页面随时变化） |
| **典型产出** | 测试用例、CI 流水线 | K8s 配置、监控大盘 | MCP 工具层、任务引擎、调度系统、上下文管理 |
| **失败模式** | 断言不通过 → 明确报错 | 服务宕机 → 告警恢复 | Agent 「静默偏离」→ 执行了错误操作但没报错 |

最后一行是关键区别。传统系统的失败是显式的——要么成功，要么报错。但 Agent 系统有一种独特的失败模式：**静默偏离（Silent Drift）**。Agent 可能填了错误的值、点了错误的按钮、漏掉了一个步骤，而整个流程看起来都「正常完成」了。Harness Engineering 的核心使命之一，就是让这种隐性失败变成显式的、可检测的、可恢复的。

#### 能力模型

一个合格的 Harness Engineer 需要覆盖以下能力：

```
┌─────────────────────────────────────────────────┐
│           Harness Engineer 能力模型              │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │  工具层    │  │  调度层    │  │  编排层    │   │
│  │  MCP 设计  │  │  asyncio  │  │ Orch-Worker│   │
│  │  Schema    │  │ Semaphore │  │  任务分发   │   │
│  │  校验/限流  │  │  队列管理  │  │  容错转移   │   │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘   │
│        │              │              │          │
│  ┌─────▼──────────────▼──────────────▼─────┐    │
│  │         自动化执行层（Playwright）         │    │
│  │    隔离架构 · 动作封装 · 反检测 · 资源管理   │    │
│  └─────────────────┬───────────────────────┘    │
│                    │                            │
│  ┌─────────────────▼───────────────────────┐    │
│  │           上下文管理                      │    │
│  │    滑动窗口 · 摘要压缩 · Token 预算       │    │
│  └─────────────────┬───────────────────────┘    │
│                    │                            │
│  ┌─────────────────▼───────────────────────┐    │
│  │           可观测性                        │    │
│  │    结构化日志 · Trace · 监控告警           │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
└─────────────────────────────────────────────────┘
```

这五层能力不是孤立的。一次浏览器自动化任务的执行，会同时穿透所有层：编排层分配任务 → 调度层控制并发 → 工具层执行动作 → 上下文管理维持 Agent 记忆 → 可观测性记录一切。本文的后续章节将逐一深入每一层。

### 1.2 浏览器 Agent 的工程化挑战：为什么"Demo 跑通"离"生产可用"还有 10 倍距离

让我们具体看看，一个浏览器自动化 Agent 从 Demo 到生产，会撞上哪些工程化问题。

#### 挑战 1：环境不确定性

Demo 环境里，目标网站的页面结构是固定的、网络是稳定的、没有验证码、不需要登录。生产环境中，这些假设全部失效：

- **页面结构会变**：A/B 测试导致按钮位置变化，前端框架升级导致 DOM 结构重构
- **网络会超时**：CDN 切换、DNS 解析延迟、代理节点故障
- **反爬会拦截**：Cloudflare、reCAPTCHA、行为指纹检测、IP 封禁
- **状态会丢失**：Session 过期、Cookie 被清除、登录态失效

> 💡 **核心矛盾**：LLM 每次推理都假设世界和上一次一样，但浏览器环境每分钟都在变。Harness 的职责就是在两者之间建立一个稳定的适配层。

#### 挑战 2：LLM 的非确定性

同一个 Prompt，GPT-4 今天用 `page.click('#submit-btn')` 完成任务，明天可能改用 `page.fill('#search', 'xxx')` 再点搜索结果——两种路径都「能到终点」，但后者多了两步，多消耗了 Token，还可能触发不同的页面状态。

这种非确定性带来的后果：

```
┌─────────────────────────────────────────────┐
│        LLM 非确定性的连锁反应                 │
├─────────────────────────────────────────────┤
│                                             │
│  相同输入 ──▶ 不同动作序列                    │
│              │                              │
│              ├──▶ 不同的中间页面状态           │
│              │    └──▶ 不同的截图 / DOM 快照   │
│              │         └──▶ 不同的下一步推理    │
│              │                              │
│              ├──▶ 不可预测的 Token 消耗        │
│              │                              │
│              └──▶ 不可预测的执行时长           │
│                                             │
└─────────────────────────────────────────────┘
```

传统自动化脚本是确定性的：步骤 A → B → C → 完成。Agent 是概率性的：步骤可能是 A → B → C，也可能是 A → D → E → F → C。你的 Harness 系统必须能处理这种路径发散。

#### 挑战 3：规模化后的资源压力

一个 Agent 跑一个任务时，你不需要考虑资源管理。当 50 个 Agent 同时跑 50 个任务时：

- **内存**：每个 Playwright Browser Context 占 50-200MB 内存，50 个并发 = 至少 2.5GB
- **CPU**：页面渲染、JavaScript 执行、截图生成都是 CPU 密集型
- **Token**：每个任务消耗 5K-50K Token，50 个并发任务 = 每分钟百万级 Token
- **网络**：代理池耗尽、目标网站限流、DNS 查询超时

没有资源管理，你的系统会在 10 分钟内 OOM（Out of Memory）。

#### 挑战 4：失败模式的多样性

在传统系统中，失败通常是二元的——成功或失败。浏览器 Agent 的失败模式要复杂得多：

| 失败类型 | 示例 | 检测难度 | 恢复策略 |
| :--- | :--- | :--- | :--- |
| **硬失败** | 页面 404、元素不存在 | ⭐ 容易 | 直接重试或终止 |
| **超时失败** | 页面加载超过 30s | ⭐⭐ 中等 | 重试 + 超时递增 |
| **静默偏离** | 填了错误的值但没报错 | ⭐⭐⭐ 困难 | 校验断言 + 截图比对 |
| **部分成功** | 5 个表单填了 4 个 | ⭐⭐⭐ 困难 | 检查点 + 断点续跑 |
| **语义错误** | 任务完成但结果不是用户想要的 | ⭐⭐⭐⭐ 极难 | 人工审核 + 结果校验 |

Harness 系统需要为每一种失败模式设计检测和恢复机制。这就是为什么「10 倍距离」不是夸张——每一个挑战都需要一整套工程化解决方案。

### 1.3 Harness 工程师的技术栈全景（MCP / Playwright / asyncio / 可观测性）

在深入每一层之前，先建立全局地图。以下是浏览器 Agent 系统中 Harness Engineer 需要掌握的核心技术栈，也是本文后续章节的展开主线：

#### 工具层：MCP（Model Context Protocol）

MCP 是 Agent 与外部世界交互的标准化协议。对于 Harness Engineer，它意味着：

- **Schema 设计**：为每个浏览器操作定义精确的 JSON Schema，约束 LLM 的工具调用参数
- **输入校验**：防止 LLM 生成的非法参数进入 Playwright 执行层
- **限流与审计**：控制工具调用频率，记录敏感操作

> 💡 把 MCP 想象成 Agent 的「API 网关」——所有工具调用都必须经过这层校验、限流、审计，然后才到达执行层。

#### 执行层：Playwright

Playwright 是浏览器自动化的事实标准。Harness Engineer 需要精通它的三层架构：

```
Browser（浏览器实例，通常 1 个）
  └── Context（隔离上下文，每任务 1 个）
        └── Page（页面标签，每步骤 1 个或多个）
```

核心关注点：
- **隔离性**：每个任务独立 Context，Cookie/Storage 互不干扰
- **性能**：Context 池化复用 vs 每次新建的权衡
- **稳定性**：超时策略、等待策略、异常恢复
- **反检测**：指纹伪装、行为模拟、代理轮换

#### 调度层：asyncio + 任务队列

Python 的 asyncio 是浏览器 Agent 并发调度的核心。关键原语包括：

```python
# 最小调度模型
semaphore = asyncio.Semaphore(10)    # 最多 10 个并发任务

async def run_task(task):
    async with semaphore:            # 获取信号量
        context = await browser.new_context()
        try:
            result = await execute(context, task)
            return result
        finally:
            await context.close()    # 确保资源释放

# TaskGroup 管理并发
async with asyncio.TaskGroup() as tg:
    for task in tasks:
        tg.create_task(run_task(task))
```

进阶时会引入 Redis/BullMQ 等外部队列，实现跨进程、跨机器的任务分发。

#### 编排层：Orchestrator-Worker

当单机无法承载时，需要分布式编排：

```
Orchestrator（编排器）
  ├── 接收任务请求
  ├── 拆分子任务
  ├── 分发到 Worker
  └── 聚合结果

Worker（执行器）
  ├── 注册 + 心跳
  ├── 拉取任务
  ├── 执行 Playwright 操作
  └── 上报结果
```

#### 上下文管理

LLM 的上下文窗口是有限的（128K Token 看起来很多，但浏览器操作的截图 + DOM 快照会迅速填满）。核心策略：

- **滑动窗口**：保留最近 N 轮对话，丢弃最早的
- **摘要压缩**：将历史操作压缩成「执行摘要」
- **预算分配**：为截图、DOM、对话历史分配 Token 预算

#### 可观测性

没有可观测性的 Agent 系统就是黑盒。核心建设：

- **结构化日志**：每次 tool call 记录 `{tool, params, result, duration, error_code}`
- **执行链路**：从用户指令到最终结果的完整操作时间线
- **监控告警**：成功率、P99 延迟、Token 消耗的实时大盘
- **失败复现**：从日志重建完整的执行上下文，一键复现问题

---

本文将从第 2 章开始，**自底向上**逐一深入每一层：工具层（第 2 章）→ 任务引擎（第 3 章）→ 上下文管理（第 4 章）→ 执行层（第 5 章）→ 调度层（第 6 章）→ 编排层（第 7 章）→ 可观测性（第 8 章）→ 工程基础（第 9 章），最终在第 10 章完成一个端到端的实战项目。

---

## 2. MCP Server 设计与维护：工具层的工程化

MCP（Model Context Protocol）是 Agent 调用外部工具的标准化接口。对浏览器自动化 Agent 来说，MCP Server 就是「所有浏览器操作的入口」——LLM 想点击一个按钮、填写一个表单、截取一张图，都必须通过 MCP 工具来完成。

工具层的质量直接决定 Agent 的成功率。一个设计粗糙的工具层，会让 LLM 传入非法参数、触发危险操作、并发冲突——而这些问题在 Demo 阶段不会暴露，只有在生产规模下才会爆发。

### 2.1 工具 Schema 设计规范：JSON Schema 约束、参数命名、版本演进

#### 为什么 Schema 如此重要？

Schema 是 LLM 理解「工具能做什么、参数怎么填」的唯一依据。一个模糊的 Schema 会导致 LLM 猜测参数含义，而猜测意味着错误。

看一个反面案例：

```json
{
  "name": "click",
  "description": "Click an element",
  "parameters": {
    "type": "object",
    "properties": {
      "target": { "type": "string" }
    }
  }
}
```

这个 Schema 有什么问题？`target` 是什么？CSS 选择器？XPath？文本内容？ARIA label？LLM 不知道，所以它可能随机猜测，导致不同次调用使用不同格式的参数。

正面案例：

```json
{
  "name": "browser_click",
  "description": "点击页面上指定的元素。优先使用 CSS 选择器定位，如果元素没有稳定的选择器，使用可见文本定位。",
  "parameters": {
    "type": "object",
    "properties": {
      "selector": {
        "type": "string",
        "description": "CSS 选择器，例如 '#submit-btn', '.form-input[name=email]'。优先使用 id 或 data-testid 属性。"
      },
      "text": {
        "type": "string",
        "description": "元素的可见文本内容，用于在无法获取稳定选择器时作为备选定位方式。例如 '提交订单'。"
      },
      "click_type": {
        "type": "string",
        "enum": ["left", "right", "double"],
        "default": "left",
        "description": "点击类型：left=左键单击，right=右键，double=双击"
      },
      "wait_after_ms": {
        "type": "integer",
        "minimum": 0,
        "maximum": 10000,
        "default": 1000,
        "description": "点击后等待的毫秒数，用于等待页面响应。默认 1000ms。"
      }
    },
    "required": ["selector"]
  }
}
```

#### Schema 设计的核心原则

| 原则 | 说明 | 示例 |
| :--- | :--- | :--- |
| **语义化命名** | 工具名和参数名必须自解释 | `browser_click` 而非 `click`，`selector` 而非 `target` |
| **精确约束** | 用 `enum`、`minimum`/`maximum`、`pattern` 限制参数范围 | `click_type: enum ["left","right","double"]` |
| **防御性默认值** | 为可选参数提供安全的默认值 | `wait_after_ms: default 1000` |
| **丰富的 description** | 每个参数都有详细说明 + 示例 | 包含具体的 CSS 选择器示例 |
| **命名空间前缀** | 避免工具名冲突 | `browser_click`、`browser_fill`、`browser_navigate` |

#### 版本演进策略

工具 Schema 会随着需求变化——新增参数、修改行为、废弃旧工具。直接修改会导致正在运行的 Agent 出错。推荐的版本管理策略：

```
版本管理策略：
  
  1. 新增参数 → 设置默认值，向后兼容
     browser_click v1: {selector}
     browser_click v2: {selector, click_type="left"}  ← 新参数有默认值
  
  2. 行为变更 → 新工具名 + 废弃旧工具
     browser_screenshot    → 旧版，返回 base64
     browser_screenshot_v2 → 新版，返回文件路径 + 元信息
  
  3. 废弃工具 → 标记 deprecated，保留 2 个版本周期
     {"name": "browser_screenshot", "deprecated": true,
      "description": "⚠️ 已废弃，请使用 browser_screenshot_v2"}
```

> 💡 **实战建议**：维护一个 `tools_manifest.json`，记录所有工具的版本号、状态（active/deprecated/removed）和变更日志。每次 Agent 启动时加载这个清单，确保使用的工具版本一致。

### 2.2 输入合法性验证：类型校验、路径注入防护、参数边界检查

JSON Schema 能约束参数的「格式」，但无法覆盖所有安全和业务逻辑。Harness Engineer 需要在工具执行层构建第二道防线——输入验证中间件。

#### 验证层架构

```
LLM 调用工具
    │
    ▼
┌───────────────────┐
│  JSON Schema 校验  │  ← 第 1 层：格式校验（类型、必填、枚举）
└────────┬──────────┘
         │
    ▼
┌───────────────────┐
│  业务逻辑验证       │  ← 第 2 层：语义校验（路径安全、范围合理、状态一致）
└────────┬──────────┘
         │
    ▼
┌───────────────────┐
│  执行 Playwright   │  ← 通过验证，安全执行
└───────────────────┘
```

#### 必须防护的攻击面

**路径注入**：LLM 可能生成包含路径穿越的参数：

```python
# 危险！LLM 可能生成这样的参数
await page.screenshot(path="../../etc/passwd.png")
await page.goto("file:///etc/shadow")

# 验证中间件
def validate_file_path(path: str) -> str:
    """确保文件路径在允许的目录内"""
    resolved = Path(path).resolve()
    allowed_dir = Path("/app/screenshots").resolve()
    if not str(resolved).startswith(str(allowed_dir)):
        raise ValidationError(f"路径 {path} 超出允许范围 {allowed_dir}")
    return str(resolved)
```

**选择器注入**：CSS 选择器可能被构造成执行 JavaScript：

```python
# 验证选择器不包含危险内容
def validate_selector(selector: str) -> str:
    # 禁止 javascript: 协议
    if "javascript:" in selector.lower():
        raise ValidationError("选择器不允许包含 javascript: 协议")
    # 限制选择器长度
    if len(selector) > 500:
        raise ValidationError("选择器长度不得超过 500 字符")
    return selector
```

**URL 白名单**：限制 Agent 只能访问预定义的域名：

```python
ALLOWED_DOMAINS = {"example.com", "app.example.com", "api.example.com"}

def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_DOMAINS:
        raise ValidationError(
            f"域名 {parsed.hostname} 不在白名单中。"
            f"允许的域名：{ALLOWED_DOMAINS}"
        )
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(f"不支持的协议：{parsed.scheme}")
    return url
```

#### 统一验证中间件模式

将所有验证逻辑封装成装饰器，统一应用到每个工具函数：

```python
def validate_inputs(**validators):
    """工具输入验证装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(**kwargs):
            for param_name, validator_fn in validators.items():
                if param_name in kwargs:
                    kwargs[param_name] = validator_fn(kwargs[param_name])
            return await func(**kwargs)
        return wrapper
    return decorator

# 使用方式
@validate_inputs(
    selector=validate_selector,
    url=validate_url,
    screenshot_path=validate_file_path
)
async def browser_navigate(url: str, **kwargs):
    await page.goto(url)
```

> 💡 验证失败时，返回结构化的错误信息给 LLM，让它能理解「哪个参数有问题、应该怎么修正」，而不是一个含糊的 500 错误。

### 2.3 限流与资源保护：单租户限流、全局并发上限、降级策略

当多个 Agent 实例同时运行时，工具层会面临并发压力。不加限制地执行所有请求，会导致目标网站封禁 IP、Playwright 资源耗尽、LLM Token 账单爆表。

#### 三级限流架构

```
┌──────────────────────────────────────────────┐
│              限流层级                          │
├──────────────────────────────────────────────┤
│                                              │
│  Level 1：单任务限流                           │
│  ── 同一任务的连续工具调用间隔 ≥ 500ms          │
│  ── 防止 LLM 在一轮推理中疯狂调用工具           │
│                                              │
│  Level 2：单租户限流                           │
│  ── 同一用户最多 5 个并发任务                   │
│  ── 防止单个用户独占全部资源                    │
│                                              │
│  Level 3：全局限流                             │
│  ── 系统总并发不超过 50 个 Browser Context      │
│  ── 保护基础设施不被压垮                       │
│                                              │
└──────────────────────────────────────────────┘
```

#### 实现：基于令牌桶的限流器

```python
import asyncio
import time

class TokenBucketRateLimiter:
    """令牌桶限流器，支持突发流量"""
    
    def __init__(self, rate: float, burst: int):
        self.rate = rate          # 每秒补充的令牌数
        self.burst = burst        # 桶的最大容量（允许的突发量）
        self.tokens = burst       # 当前令牌数
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            # 补充令牌
            elapsed = now - self.last_refill
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_refill = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    async def wait_and_acquire(self, timeout: float = 30.0):
        """等待直到获取令牌或超时"""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if await self.acquire():
                return True
            await asyncio.sleep(0.1)
        raise RateLimitExceeded("等待令牌超时")

# 使用方式
tool_limiter = TokenBucketRateLimiter(rate=2.0, burst=5)  # 每秒 2 次，突发 5 次

async def rate_limited_tool_call(tool_fn, **params):
    await tool_limiter.wait_and_acquire()
    return await tool_fn(**params)
```

#### 降级策略

当系统负载过高时，不应直接拒绝所有请求，而是分级降级：

| 负载水平 | 策略 | 具体行为 |
| :--- | :--- | :--- |
| **正常**（< 70%） | 全功能 | 所有工具正常可用 |
| **预警**（70-85%） | 限制非核心工具 | 禁用 `browser_screenshot`（截图最耗资源），只保留点击/填写/导航 |
| **过载**（85-95%） | 新任务排队 | 不再接受新任务，已有任务继续执行 |
| **危险**（> 95%） | 熔断 | 暂停所有工具调用，等待资源释放后恢复 |

### 2.4 敏感操作审计与确认流：支付/删除/登录等高风险动作的拦截机制

浏览器自动化的最大风险不是「Agent 跑不通」，而是「Agent 跑通了但做了不该做的事」。当 Agent 有能力点击「确认支付」按钮时，一次 LLM 幻觉可能造成真实的金钱损失。

#### 风险分级

先对所有工具进行风险分级：

| 风险等级 | 工具类型 | 处理方式 | 示例 |
| :--- | :--- | :--- | :--- |
| 🟢 **低风险** | 只读操作 | 自动执行 | 截图、读取文本、获取元素属性 |
| 🟡 **中风险** | 可逆写操作 | 执行 + 记录审计日志 | 填写表单、点击导航、选择下拉框 |
| 🔴 **高风险** | 不可逆操作 | 需要人工确认 | 确认支付、删除数据、提交订单 |
| ⚫ **禁止** | 超出任务范围 | 直接拒绝 | 修改密码、更改账户设置、卸载应用 |

#### 确认流实现

```python
from enum import Enum
from dataclasses import dataclass

class RiskLevel(Enum):
    LOW = "low"          # 自动执行
    MEDIUM = "medium"    # 审计日志
    HIGH = "high"        # 人工确认
    BLOCKED = "blocked"  # 直接拒绝

# 工具风险注册表
TOOL_RISK_REGISTRY = {
    "browser_screenshot": RiskLevel.LOW,
    "browser_get_text":   RiskLevel.LOW,
    "browser_click":      RiskLevel.MEDIUM,
    "browser_fill":       RiskLevel.MEDIUM,
    "browser_confirm_payment": RiskLevel.HIGH,
    "browser_delete_account":  RiskLevel.BLOCKED,
}

@dataclass
class ConfirmationRequest:
    tool_name: str
    params: dict
    risk_level: RiskLevel
    reason: str
    screenshot_base64: str   # 当前页面截图，帮助人工判断

async def execute_with_risk_check(tool_name: str, params: dict):
    risk = TOOL_RISK_REGISTRY.get(tool_name, RiskLevel.MEDIUM)
    
    if risk == RiskLevel.BLOCKED:
        return {"error": f"工具 {tool_name} 已被禁止执行", "code": "TOOL_BLOCKED"}
    
    if risk == RiskLevel.HIGH:
        # 暂停执行，发送确认请求给人工
        confirmation = await request_human_confirmation(
            ConfirmationRequest(
                tool_name=tool_name,
                params=params,
                risk_level=risk,
                reason=f"高风险操作：{tool_name}",
                screenshot_base64=await take_screenshot()
            )
        )
        if not confirmation.approved:
            return {"error": "人工审核拒绝", "code": "HUMAN_REJECTED"}
    
    # 执行并记录审计日志
    result = await execute_tool(tool_name, params)
    await audit_log.record(tool_name, params, result, risk)
    return result
```

#### 审计日志结构

每一次工具调用都应记录完整的审计日志，格式统一：

```json
{
  "timestamp": "2024-03-15T10:23:45.123Z",
  "task_id": "task_abc123",
  "tool_name": "browser_click",
  "params": {"selector": "#confirm-order", "text": "确认订单"},
  "risk_level": "medium",
  "result": {"success": true, "page_url_after": "https://example.com/order/confirmed"},
  "duration_ms": 1523,
  "page_screenshot_key": "s3://audit/task_abc123/step_007.png"
}
```

> 💡 **关键设计决策**：高风险操作的确认应该是异步的——Agent 发起请求后挂起等待，人工审核后 Agent 继续执行。这需要和任务引擎的「检查点」机制配合，避免等待期间上下文丢失（详见第 3 章）。

### 2.5 动作原子化封装：单一职责、幂等设计、组合可预测

MCP 工具设计的最后一个关键原则：**每个工具只做一件事，做完这件事后系统状态是可预测的。**

#### 单一职责：一个工具 = 一个原子操作

反面案例——一个「全能」工具：

```json
{
  "name": "browser_do",
  "description": "执行浏览器操作",
  "parameters": {
    "action": "navigate | click | fill | screenshot | scroll",
    "target": "...",
    "value": "..."
  }
}
```

问题在于：LLM 需要同时决定 `action` 类型和对应参数，参数的含义随 `action` 变化（`target` 在 navigate 时是 URL，在 click 时是选择器），校验逻辑也无法统一。

正确做法——拆分为独立工具：

```
browser_navigate(url)           → 导航到 URL
browser_click(selector)         → 点击元素
browser_fill(selector, value)   → 填写表单
browser_screenshot()            → 截图
browser_scroll(direction, px)   → 滚动页面
```

每个工具的参数含义明确，JSON Schema 约束精确，校验逻辑独立。

#### 幂等设计：重复执行不产生副作用

幂等性意味着：同一操作执行一次和执行多次，最终效果一样。这在 Agent 系统中至关重要——因为重试是家常便饭。

```python
# ❌ 非幂等：每次执行都追加内容
async def browser_fill(selector: str, value: str):
    element = await page.query_selector(selector)
    await element.type(value)  # type() 是追加，不是覆盖！

# ✅ 幂等：每次执行都覆盖为相同值
async def browser_fill(selector: str, value: str):
    element = await page.query_selector(selector)
    await element.fill("")     # 先清空
    await element.fill(value)  # 再填入
```

其他幂等设计模式：

| 操作 | 非幂等实现 | 幂等实现 |
| :--- | :--- | :--- |
| **导航** | `goto(url)` 不检查当前页面 | 先检查 `page.url`，如果已经在目标页则跳过 |
| **点击** | 直接点击 | 点击后验证预期状态变化，如果已经是目标状态则跳过 |
| **表单提交** | 直接提交 | 提交前检查是否已提交（查找确认页面元素） |

#### 统一返回结构

所有工具必须返回统一格式的结果，让 LLM 能一致地理解工具执行情况：

```python
@dataclass
class ToolResult:
    success: bool                  # 是否成功
    data: dict | None = None       # 成功时的返回数据
    error: str | None = None       # 失败时的错误信息
    error_code: str | None = None  # 机器可读的错误码
    page_url: str | None = None    # 执行后的页面 URL
    screenshot_key: str | None = None  # 执行后的截图路径

# 使用示例
async def browser_click(selector: str) -> ToolResult:
    try:
        await page.click(selector, timeout=5000)
        return ToolResult(
            success=True,
            data={"clicked_selector": selector},
            page_url=page.url
        )
    except TimeoutError:
        return ToolResult(
            success=False,
            error=f"元素 {selector} 在 5 秒内未找到",
            error_code="ELEMENT_NOT_FOUND",
            page_url=page.url
        )
```

> 💡 **第 2 章小结**：MCP 工具层是 Agent 系统的「API 网关」。精确的 Schema 减少 LLM 的猜测空间，输入验证阻止危险参数，限流保护系统资源，审计流防止高风险操作，原子化封装确保操作可预测可重试。这一层做好了，Agent 的成功率会有质的提升。

---

## 3. 自动化任务引擎：从脚本到可组合的任务系统

第 2 章解决了「单个工具怎么设计」的问题。但生产环境中，Agent 要完成的不是「点一个按钮」，而是「在电商网站下单：搜索商品 → 选规格 → 加购物车 → 填地址 → 确认支付」——这是一个由 10-50 个原子动作组成的**任务流程**。

当任务在第 37 步失败时，你是从头重跑（浪费 36 步的时间和 Token），还是从第 37 步恢复？当同一个任务模板要在 100 个不同账号上执行时，你是复制 100 份脚本，还是用参数化模板？

任务引擎就是解决这些问题的中间层——它把零散的原子动作组织成可管理、可恢复、可复用的任务系统。

### 3.1 原子动作库设计：可组合、可重试、可测试的动作体系

#### 从 MCP 工具到原子动作

第 2 章的 MCP 工具是面向 LLM 的接口——它定义了「Agent 能调用什么」。原子动作库则是面向任务引擎的内部模块——它定义了「任务模板能组合什么」。

两者的关系：

```
MCP 工具（外部接口）         原子动作（内部模块）
browser_click(selector)  →  click_action(selector, retry=3, timeout=5s)
browser_fill(selector)   →  fill_action(selector, value, verify=True)
browser_navigate(url)    →  navigate_action(url, wait_until="networkidle")
```

区别在于：原子动作封装了**重试策略、超时控制、前置/后置校验**，而 MCP 工具只是一层薄薄的参数映射。

#### 原子动作的标准接口

每个原子动作都实现统一的基类：

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class ActionContext:
    """动作执行的上下文"""
    page: Page                    # Playwright Page 实例
    task_id: str                  # 所属任务 ID
    step_index: int               # 当前步骤索引
    variables: dict = field(default_factory=dict)  # 任务级变量

@dataclass
class ActionResult:
    success: bool
    data: dict | None = None
    error: str | None = None
    error_code: str | None = None
    retryable: bool = True        # 失败是否可重试
    screenshot_key: str | None = None

class BaseAction(ABC):
    """原子动作基类"""
    
    name: str = "base_action"
    max_retries: int = 3
    timeout_ms: int = 10000
    retry_delay_ms: int = 1000
    
    @abstractmethod
    async def execute(self, ctx: ActionContext) -> ActionResult:
        """执行动作的核心逻辑"""
        ...
    
    async def pre_check(self, ctx: ActionContext) -> bool:
        """前置校验：执行前检查是否满足条件"""
        return True
    
    async def post_verify(self, ctx: ActionContext, result: ActionResult) -> bool:
        """后置校验：执行后验证结果是否符合预期"""
        return result.success
    
    async def run(self, ctx: ActionContext) -> ActionResult:
        """带重试的完整执行流程"""
        # 前置检查
        if not await self.pre_check(ctx):
            return ActionResult(
                success=True, 
                data={"skipped": True, "reason": "前置检查表明已完成"}
            )
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = await asyncio.wait_for(
                    self.execute(ctx),
                    timeout=self.timeout_ms / 1000
                )
                # 后置校验
                if await self.post_verify(ctx, result):
                    return result
                last_error = "后置校验失败"
            except asyncio.TimeoutError:
                last_error = f"执行超时（{self.timeout_ms}ms）"
            except Exception as e:
                last_error = str(e)
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay_ms / 1000)
        
        return ActionResult(
            success=False,
            error=f"重试 {self.max_retries} 次后仍失败：{last_error}",
            error_code="MAX_RETRIES_EXCEEDED"
        )
```

#### 具体动作示例

```python
class ClickAction(BaseAction):
    name = "click"
    
    def __init__(self, selector: str, wait_after_ms: int = 1000):
        self.selector = selector
        self.wait_after_ms = wait_after_ms
    
    async def execute(self, ctx: ActionContext) -> ActionResult:
        await ctx.page.click(self.selector)
        await ctx.page.wait_for_timeout(self.wait_after_ms)
        return ActionResult(success=True, data={"selector": self.selector})

class FillAction(BaseAction):
    name = "fill"
    
    def __init__(self, selector: str, value: str):
        self.selector = selector
        self.value = value
    
    async def execute(self, ctx: ActionContext) -> ActionResult:
        await ctx.page.fill(self.selector, "")  # 幂等：先清空
        await ctx.page.fill(self.selector, self.value)
        return ActionResult(success=True)
    
    async def post_verify(self, ctx: ActionContext, result: ActionResult) -> bool:
        """验证填入的值是否正确"""
        actual = await ctx.page.input_value(self.selector)
        return actual == self.value
```

#### 动作的可组合性

有了统一接口，动作可以任意组合成序列：

```python
# 一个完整的登录流程 = 3 个原子动作的组合
login_steps = [
    NavigateAction(url="https://example.com/login"),
    FillAction(selector="#username", value="${username}"),
    FillAction(selector="#password", value="${password}"),
    ClickAction(selector="#login-btn", wait_after_ms=3000),
]
```

注意 `${username}` 语法——这是模板变量，会在运行时从 `ActionContext.variables` 中注入。这个机制将在 3.2 节详细展开。

### 3.2 版本化任务模板：模板定义、参数注入、模板市场

#### 为什么需要任务模板？

假设你有一个「批量注册账号」任务，需要在 100 个不同的邮箱上执行。没有模板系统，你需要手写 100 个动作序列，每个序列只有邮箱不同。任务模板把**固定的流程骨架**和**可变的参数**分离，实现一份模板、多次实例化。

#### 模板定义格式

```python
@dataclass
class TaskTemplate:
    """任务模板定义"""
    template_id: str              # 唯一标识
    name: str                     # 人类可读名称
    version: str                  # 语义化版本号：major.minor.patch
    description: str              # 模板说明
    parameters: list[ParamDef]    # 参数定义列表
    steps: list[StepDef]          # 步骤定义列表
    created_at: datetime
    tags: list[str] = field(default_factory=list)

@dataclass
class ParamDef:
    """模板参数定义"""
    name: str                     # 参数名，如 "username"
    type: str                     # 类型：string, int, url, email
    required: bool = True
    default: Any = None
    description: str = ""
    validation: str | None = None  # 正则校验

@dataclass
class StepDef:
    """步骤定义"""
    action: str                   # 动作类型：click, fill, navigate...
    params: dict                  # 动作参数，支持 ${var} 引用
    description: str = ""
    is_checkpoint: bool = False   # 是否为检查点（详见 3.3）
```

一个完整的模板示例：

```yaml
# templates/ecommerce_order.yaml
template_id: ecommerce_order
name: 电商下单流程
version: "1.2.0"
description: 在目标电商网站搜索商品并完成下单
tags: [ecommerce, order]

parameters:
  - name: site_url
    type: url
    required: true
    description: 电商网站首页 URL
  - name: keyword
    type: string
    required: true
    description: 搜索关键词
  - name: quantity
    type: int
    default: 1
    description: 购买数量

steps:
  - action: navigate
    params: { url: "${site_url}" }
    description: 打开电商首页

  - action: fill
    params: { selector: "#search-input", value: "${keyword}" }
    description: 输入搜索关键词

  - action: click
    params: { selector: "#search-btn" }
    description: 点击搜索
    is_checkpoint: true           # 搜索完成是一个检查点

  - action: click
    params: { selector: ".product-item:first-child" }
    description: 选择第一个商品

  - action: click
    params: { selector: "#add-to-cart" }
    description: 加入购物车
    is_checkpoint: true
```

#### 参数注入引擎

模板中的 `${var}` 占位符在任务实例化时被替换：

```python
import re

def inject_params(template_value: str, variables: dict) -> str:
    """将模板中的 ${var} 替换为实际值"""
    def replacer(match):
        var_name = match.group(1)
        if var_name not in variables:
            raise TemplateError(f"未提供必需参数：{var_name}")
        return str(variables[var_name])
    
    return re.sub(r'\$\{(\w+)\}', replacer, template_value)

# 使用
params = {"site_url": "https://shop.example.com", "keyword": "机械键盘"}
url = inject_params("${site_url}/search?q=${keyword}", params)
# → "https://shop.example.com/search?q=机械键盘"
```

#### 版本管理策略

模板会随业务变化（目标网站改版、流程调整）。版本管理遵循语义化版本：

| 变更类型 | 版本号变化 | 示例 |
| :--- | :--- | :--- |
| 修复 bug | patch +1 | 1.2.0 → 1.2.1（修复选择器过期） |
| 新增可选步骤 | minor +1 | 1.2.1 → 1.3.0（新增优惠券输入步骤） |
| 流程结构变更 | major +1 | 1.3.0 → 2.0.0（网站改版，整个流程重写） |

> 💡 **模板市场**：当模板积累到一定数量后，可以建立内部模板市场——按行业（电商/金融/社交）、按操作（注册/下单/抓取）分类，团队成员可以搜索、复用、fork 已有模板。

### 3.3 断点续跑与检查点机制：任务中断后从最后成功步骤恢复

浏览器 Agent 任务经常中断——网络超时、页面崩溃、LLM 调用失败、甚至机器重启。如果每次中断都要从头重跑，50 步的任务在第 48 步失败就意味着浪费前 47 步的全部时间和 Token。

#### 检查点的本质

检查点（Checkpoint）就是任务执行过程中的「存档点」——保存当前状态快照，以便后续从这个点恢复执行。

```
任务执行时间线：
  
  Step 1 → Step 2 → [CP1] → Step 3 → Step 4 → [CP2] → Step 5 → ❌ 失败
                                                  │
                                                  └── 恢复点：从 CP2 恢复
                                                      跳过 Step 1-4，直接执行 Step 5
```

#### 检查点需要保存什么？

```python
@dataclass
class Checkpoint:
    """检查点快照"""
    task_id: str
    step_index: int                    # 当前执行到第几步
    timestamp: datetime
    
    # 浏览器状态
    page_url: str                      # 当前页面 URL
    cookies: list[dict]                # 所有 Cookie
    local_storage: dict                # LocalStorage 数据
    
    # 任务状态
    variables: dict                    # 任务级变量的当前值
    step_results: list[ActionResult]   # 已执行步骤的结果
    
    # 可选：页面快照
    screenshot_key: str | None = None  # 截图存储路径
    dom_snapshot: str | None = None    # 简化版 DOM

class CheckpointManager:
    """检查点管理器"""
    
    def __init__(self, storage: CheckpointStorage):
        self.storage = storage  # 可以是 Redis、SQLite、文件系统
    
    async def save(self, ctx: ActionContext, step_index: int) -> str:
        """保存检查点"""
        page = ctx.page
        checkpoint = Checkpoint(
            task_id=ctx.task_id,
            step_index=step_index,
            timestamp=datetime.utcnow(),
            page_url=page.url,
            cookies=await page.context.cookies(),
            local_storage=await page.evaluate("() => ({...localStorage})"),
            variables=ctx.variables.copy(),
            step_results=ctx.step_results[:step_index + 1],
        )
        cp_id = await self.storage.save(checkpoint)
        return cp_id
    
    async def restore(self, task_id: str) -> Checkpoint | None:
        """加载最近的检查点"""
        return await self.storage.get_latest(task_id)
```

#### 恢复执行流程

```python
async def execute_task_with_checkpoints(
    template: TaskTemplate, 
    variables: dict,
    checkpoint_mgr: CheckpointManager
):
    # 1. 尝试加载检查点
    checkpoint = await checkpoint_mgr.restore(template.template_id)
    
    if checkpoint:
        # 恢复浏览器状态
        start_step = checkpoint.step_index + 1
        await page.goto(checkpoint.page_url)
        await page.context.add_cookies(checkpoint.cookies)
        variables.update(checkpoint.variables)
        print(f"从检查点恢复，跳过前 {start_step} 步")
    else:
        start_step = 0
    
    # 2. 从恢复点开始执行
    for i in range(start_step, len(template.steps)):
        step = template.steps[i]
        action = create_action(step)
        
        ctx = ActionContext(page=page, task_id=task_id, 
                           step_index=i, variables=variables)
        result = await action.run(ctx)
        
        if not result.success:
            raise TaskStepFailed(step=i, error=result.error)
        
        # 3. 如果当前步骤是检查点，保存状态
        if step.is_checkpoint:
            await checkpoint_mgr.save(ctx, i)
```

#### 检查点放在哪里？

不是每一步都需要保存检查点——保存和恢复本身有开销。推荐的检查点放置策略：

| 放置位置 | 原因 |
| :--- | :--- |
| **页面导航后** | URL 变化后状态显著变化，是天然的恢复边界 |
| **表单提交后** | 提交是不可逆操作，必须在提交前保存 |
| **耗时操作完成后** | 避免重复执行耗时步骤（如文件上传、长等待） |
| **每 N 步定期保存** | 作为兜底策略，N 通常取 5-10 |

### 3.4 幂等执行：重复运行同一任务的安全保障

2.5 节讨论了单个动作的幂等性，这里从**任务级别**来看幂等问题：同一个任务（相同模板 + 相同参数）执行两次，结果应该是什么？

#### 任务级幂等的三种策略

```
策略 1：拒绝重复 ── 检测到相同任务已执行过，直接返回之前的结果
  适用于：数据抓取、信息查询等只读任务

策略 2：覆盖执行 ── 无论之前是否执行过，重新执行并覆盖结果
  适用于：状态同步、数据更新等幂等操作

策略 3：条件执行 ── 检查目标状态，如果已达到预期则跳过，否则执行
  适用于：表单提交、订单创建等有副作用的操作
```

#### 幂等键（Idempotency Key）

每个任务实例生成一个唯一的幂等键，用于检测重复执行：

```python
import hashlib

def generate_idempotency_key(template_id: str, params: dict) -> str:
    """基于模板 ID + 参数生成幂等键"""
    # 参数排序后序列化，确保相同参数生成相同的 key
    sorted_params = json.dumps(params, sort_keys=True, ensure_ascii=False)
    raw = f"{template_id}:{sorted_params}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

class IdempotentTaskRunner:
    def __init__(self, storage: TaskResultStorage):
        self.storage = storage
    
    async def run(self, template: TaskTemplate, params: dict, 
                  strategy: str = "reject") -> TaskResult:
        key = generate_idempotency_key(template.template_id, params)
        
        # 检查是否已执行过
        existing = await self.storage.get_by_key(key)
        
        if existing and existing.status == "completed":
            if strategy == "reject":
                return existing  # 返回之前的结果
            elif strategy == "conditional":
                # 检查目标状态是否仍然有效
                if await self.verify_result_still_valid(existing):
                    return existing
                # 状态已变化，需要重新执行
        
        # 执行任务
        result = await self.execute(template, params)
        result.idempotency_key = key
        await self.storage.save(result)
        return result
```

> 💡 幂等键的设计要注意：如果参数包含时间戳或随机数，需要排除这些字段再计算哈希，否则每次都会生成不同的 key。

### 3.5 任务状态机：pending → running → checkpoint → completed / failed

所有的检查点、幂等、恢复机制都依赖一个清晰的任务状态模型。一个设计良好的状态机，能让你在任何时刻准确回答：「这个任务现在处于什么阶段？下一步该做什么？」

#### 状态定义

```
                    ┌────────────┐
                    │  PENDING   │  任务已创建，等待执行
                    └─────┬──────┘
                          │ 资源就绪，开始执行
                          ▼
                    ┌────────────┐
              ┌────▶│  RUNNING   │  正在执行步骤
              │     └──┬───┬──┬──┘
              │        │   │  │
   重试 / 恢复  │        │   │  │ 到达检查点
              │        │   │  ▼
              │        │   │ ┌──────────────┐
              │        │   └▶│ CHECKPOINTED │  已保存检查点，可恢复
              │        │     └──────┬───────┘
              │        │            │ 继续执行
              │        │            ▼
              │        │      回到 RUNNING
              │        │
              │        │ 所有步骤完成
              │        ▼
              │  ┌────────────┐
              │  │ COMPLETED  │  任务成功完成
              │  └────────────┘
              │
              │        │ 执行失败
              │        ▼
              │  ┌────────────┐     重试次数未耗尽
              └──│   FAILED   │─────────────┘
                 └──────┬─────┘
                        │ 重试次数已耗尽
                        ▼
                 ┌────────────┐
                 │ TERMINATED │  最终失败，不再重试
                 └────────────┘
```

#### 状态机实现

```python
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    CHECKPOINTED = "checkpointed"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"

# 合法的状态转换
VALID_TRANSITIONS = {
    TaskStatus.PENDING:      {TaskStatus.RUNNING},
    TaskStatus.RUNNING:      {TaskStatus.CHECKPOINTED, TaskStatus.COMPLETED, TaskStatus.FAILED},
    TaskStatus.CHECKPOINTED: {TaskStatus.RUNNING},
    TaskStatus.FAILED:       {TaskStatus.RUNNING, TaskStatus.TERMINATED},
    TaskStatus.COMPLETED:    set(),      # 终态，不可转换
    TaskStatus.TERMINATED:   set(),      # 终态，不可转换
}

class TaskStateMachine:
    def __init__(self, task_id: str, max_retries: int = 3):
        self.task_id = task_id
        self.status = TaskStatus.PENDING
        self.retry_count = 0
        self.max_retries = max_retries
        self.history: list[tuple[TaskStatus, datetime]] = []
    
    def transition(self, target: TaskStatus):
        if target not in VALID_TRANSITIONS[self.status]:
            raise InvalidTransition(
                f"不允许从 {self.status.value} 转换到 {target.value}"
            )
        
        if target == TaskStatus.FAILED:
            self.retry_count += 1
            if self.retry_count >= self.max_retries:
                target = TaskStatus.TERMINATED  # 自动转为终态
        
        self.history.append((self.status, datetime.utcnow()))
        self.status = target
    
    @property
    def is_terminal(self) -> bool:
        return self.status in {TaskStatus.COMPLETED, TaskStatus.TERMINATED}
    
    @property
    def is_recoverable(self) -> bool:
        return self.status in {TaskStatus.FAILED, TaskStatus.CHECKPOINTED}
```

#### 状态持久化

任务状态必须持久化到数据库，防止进程重启后丢失：

```sql
CREATE TABLE tasks (
    id          VARCHAR(36) PRIMARY KEY,
    template_id VARCHAR(100) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending',
    params      JSONB NOT NULL,
    result      JSONB,
    retry_count INT DEFAULT 0,
    checkpoint  JSONB,                -- 最新检查点数据
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_status (status),
    INDEX idx_template (template_id)
);
```

> 💡 **第 3 章小结**：任务引擎是连接「单个动作」和「完整业务流程」的桥梁。原子动作库提供可组合的基础模块，任务模板让流程可复用可参数化，检查点和幂等机制让任务可中断可恢复，状态机让任务的生命周期清晰可追踪。这些组合在一起，构成了一个从「脚本」演进到「系统」的关键基础设施。

---

## 4. LLM 上下文管理：长任务不因上下文超限而中断

浏览器自动化任务有一个独特的特征：**上下文消耗速度极快**。每一次工具调用，LLM 需要接收页面截图（1000-5000 Token）、DOM 快照（500-3000 Token）、工具返回结果（200-500 Token）。一个 30 步的任务，仅工具交互就可能消耗 50K-100K Token——而这还没算 System Prompt 和对话历史。

如果不做上下文管理，你的 Agent 会在第 15 步左右撞上上下文窗口上限，然后要么被截断（丢失关键信息），要么直接报错中断。

### 4.1 上下文超限的典型症状与成本影响

#### 超限时会发生什么？

当上下文接近或超过模型窗口限制时，你会观察到以下递进的症状：

| 阶段 | Token 使用率 | 症状 | 影响 |
| :--- | :--- | :--- | :--- |
| **正常** | 0-60% | 推理准确，动作精确 | 无 |
| **预警** | 60-80% | 推理开始「偷懒」——跳过验证步骤，描述变简略 | 任务质量下降 |
| **危险** | 80-95% | 开始「遗忘」早期指令——忽略 System Prompt 中的约束 | 安全规则失效 |
| **超限** | >95% | API 报错 / 模型自动截断最早的消息 | 任务中断或静默偏离 |

最危险的不是「超限报错」——因为那至少是显式失败。最危险的是 80-95% 区间的**隐性退化**：Agent 仍然在「正常执行」，但已经忘记了你在 System Prompt 里写的安全约束和任务关键细节。

#### 浏览器任务的 Token 消耗结构

一个典型任务的 Token 消耗分布：

```
┌─────────────────────────────────────────────┐
│       30 步浏览器任务的 Token 消耗分布         │
├─────────────────────────────────────────────┤
│                                             │
│  System Prompt          ████  3K            │
│  任务目标描述            ██  1K              │
│  工具 Schema 定义        ██████  5K          │
│                                             │
│  每步消耗（× 30 步）：                       │
│    截图 / 视觉描述       ████████████ 60K    │
│    DOM 快照             ██████ 15K           │
│    对话历史             ████ 10K              │
│    工具调用 + 返回       ███ 6K               │
│                                             │
│  总计：约 100K Token                         │
│  ─────────────────────────────────          │
│  GPT-4o 128K 窗口：在第 20 步左右接近上限     │
│  Claude 200K 窗口：在第 35 步左右接近上限     │
│                                             │
└─────────────────────────────────────────────┘
```

#### 成本影响

上下文不仅影响功能，还直接影响钱包：

```
GPT-4o 价格：$2.50 / 1M input tokens
  
  不做上下文管理：100K tokens × $2.50/M = $0.25 / 任务
  做了上下文管理（压缩到 40K）：$0.10 / 任务
  
  日均 1000 个任务：
    不管理：$250/天 → $7,500/月
    管理后：$100/天 → $3,000/月
    节省：$4,500/月（60%）
```

> 💡 上下文管理不是可选项——它同时是**功能必需**（防止任务中断）和**成本必需**（控制 Token 消耗）。

### 4.2 滑动窗口截断：保留近期动作 + 任务目标的混合策略

最直接的上下文管理方法：保留最近 N 轮对话，丢弃最早的。但浏览器 Agent 的上下文有一个特殊性——**System Prompt 和任务目标永远不能被丢弃**，否则 Agent 会「忘记自己该做什么」。

#### 三区间上下文结构

```
┌──────────────────────────────────────────┐
│              上下文窗口（128K）             │
├──────────────────────────────────────────┤
│                                          │
│  🔒 固定区（永不截断）                     │
│  ├── System Prompt           3K          │
│  ├── 任务目标 & 约束          1K          │
│  └── 工具 Schema             5K          │
│       小计：~9K                           │
│                                          │
│  📋 摘要区（压缩后的历史）                  │
│  └── 早期步骤的执行摘要       5-10K        │
│                                          │
│  🔄 滑动区（保留最近 N 轮）                │
│  └── 最近 5-8 轮完整对话     30-50K       │
│       含截图、DOM、工具调用返回             │
│                                          │
│  💰 预留区（留给模型输出）                  │
│  └── 预留 4K Token 给输出    4K           │
│                                          │
└──────────────────────────────────────────┘
```

#### 实现

```python
class SlidingWindowContextManager:
    def __init__(self, max_tokens: int = 128000, output_reserve: int = 4000):
        self.max_tokens = max_tokens
        self.output_reserve = output_reserve
        self.fixed_messages: list[dict] = []     # 固定区
        self.summary_message: dict | None = None  # 摘要区
        self.sliding_messages: list[dict] = []    # 滑动区
    
    def set_fixed(self, system_prompt: str, task_goal: str, tool_schemas: list):
        """设置固定区内容（只设置一次）"""
        self.fixed_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"任务目标：{task_goal}"},
        ]
    
    def add_message(self, message: dict):
        """添加新消息到滑动区"""
        self.sliding_messages.append(message)
        self._trim()
    
    def _trim(self):
        """当总 Token 超限时进行截断"""
        while self._total_tokens() > self.max_tokens - self.output_reserve:
            if len(self.sliding_messages) <= 2:
                break  # 至少保留最近 1 轮对话
            
            # 移除最早的一轮（user + assistant）
            removed = self.sliding_messages[:2]
            self.sliding_messages = self.sliding_messages[2:]
            
            # 将移除的内容压缩到摘要区
            self._update_summary(removed)
    
    def _update_summary(self, removed_messages: list[dict]):
        """将被截断的消息压缩到摘要中"""
        summary_text = self._compress_to_summary(removed_messages)
        if self.summary_message:
            self.summary_message["content"] += f"\n{summary_text}"
        else:
            self.summary_message = {
                "role": "user",
                "content": f"[执行摘要]\n{summary_text}"
            }
    
    def get_messages(self) -> list[dict]:
        """获取当前完整的消息列表"""
        messages = self.fixed_messages.copy()
        if self.summary_message:
            messages.append(self.summary_message)
        messages.extend(self.sliding_messages)
        return messages
```

#### 截图的特殊处理

截图是上下文消耗的大户（单张图 1000-5000 Token）。几种优化策略：

| 策略 | 节省量 | 风险 |
| :--- | :--- | :--- |
| **降低分辨率** | 50-70% | 小字体/小按钮可能看不清 |
| **只保留最近 1 张截图** | 80% | 丢失中间状态的视觉信息 |
| **截图转文字描述** | 60-90% | 描述可能遗漏关键视觉细节 |
| **按区域裁剪** | 40-60% | 需要知道关注区域在哪 |

> 💡 **推荐组合**：保留最近 2 张原始截图（当前页面 + 上一步页面），更早的截图转成文字描述。这样既保留了「现在看到什么」的视觉信息，又控制了 Token 消耗。

### 4.3 长对话摘要压缩：何时压缩、如何压缩、压缩质量评估

滑动窗口解决了「保留多少」的问题，摘要压缩解决了「被丢弃的信息怎么保留关键部分」的问题。

#### 何时触发压缩？

```
触发条件（满足任一即触发）：

  1. Token 使用率 > 70%（预警线）
  2. 滑动区消息数 > 16 条（8 轮对话）
  3. 距离上次压缩已过 5 个步骤
```

#### 压缩 Prompt 设计

摘要压缩本身也是一次 LLM 调用，需要精心设计 Prompt：

```python
COMPRESSION_PROMPT = """你是一个浏览器自动化任务的执行日志压缩器。
将以下执行历史压缩为简洁的摘要，保留：
1. 已完成的关键步骤（成功做了什么）
2. 当前页面状态（在哪个 URL、看到了什么关键元素）
3. 已收集的数据（提取到的文本、数字、状态值）
4. 遇到的问题和解决方式

丢弃：
- 具体的 CSS 选择器（除非后续步骤需要复用）
- 中间页面的详细 DOM 结构
- 重复的成功确认消息

格式：用编号列表，每项一行，简明扼要。
"""

async def compress_history(messages: list[dict], llm_client) -> str:
    """将多轮对话压缩为摘要"""
    history_text = "\n".join(
        f"[{m['role']}] {m['content'][:500]}"  # 截断单条消息
        for m in messages
    )
    
    response = await llm_client.chat(
        model="gpt-4o-mini",   # 用更便宜的模型做压缩
        messages=[
            {"role": "system", "content": COMPRESSION_PROMPT},
            {"role": "user", "content": f"请压缩以下执行历史：\n{history_text}"}
        ],
        max_tokens=1000         # 限制摘要长度
    )
    return response.content
```

#### 压缩质量评估

压缩后的摘要可能丢失关键信息。如何检测质量？

```
低成本评估（线上使用）：
  ── 关键词保留率：任务目标中的关键实体是否在摘要中出现
  ── 状态完整性：当前 URL、登录状态等是否被保留
  ── 长度比：摘要长度 / 原文长度，理想值 15-25%

高成本评估（离线分析）：
  ── A/B 对比：压缩 vs 不压缩的任务完成率差异
  ── 回溯测试：给 LLM 摘要后问"第 3 步做了什么"，检查是否能准确回答
```

> 💡 **关键取舍**：用 `gpt-4o-mini` 做压缩可以节省 90% 的压缩成本，但压缩质量可能不如 `gpt-4o`。建议线上用 mini 压缩，定期用完整模型抽样评估质量。

### 4.4 Token 消耗治理：预算分配、实时计量、超限降级

上下文管理解决「怎么在窗口里装下更多内容」，Token 治理解决「怎么控制总支出」。两者互补：管理控制单次调用的 Token 量，治理控制全局的 Token 预算。

#### 预算分配模型

```python
@dataclass
class TokenBudget:
    """任务级 Token 预算"""
    task_id: str
    total_budget: int = 200000       # 单个任务的总预算（input + output）
    
    # 分项预算
    system_budget: int = 10000       # System Prompt + Schema
    screenshot_budget: int = 80000   # 截图消耗
    history_budget: int = 60000      # 对话历史
    output_budget: int = 50000       # 模型输出
    
    # 实时计量
    consumed: int = 0
    consumed_by_type: dict = field(default_factory=lambda: {
        "system": 0, "screenshot": 0, "history": 0, "output": 0
    })
    
    @property
    def remaining(self) -> int:
        return self.total_budget - self.consumed
    
    @property
    def usage_ratio(self) -> float:
        return self.consumed / self.total_budget
    
    def consume(self, amount: int, category: str):
        self.consumed += amount
        self.consumed_by_type[category] = (
            self.consumed_by_type.get(category, 0) + amount
        )
        
        if self.remaining <= 0:
            raise BudgetExhausted(f"任务 {self.task_id} Token 预算已耗尽")
```

#### 超限降级策略

当预算消耗到一定比例时，自动降低资源使用：

```
┌──────────────────────────────────────────────┐
│              Token 预算降级策略                 │
├──────────────────────────────────────────────┤
│                                              │
│  0-50% 消耗 ──▶ 全功能模式                    │
│    ·  每步截图（高清）                         │
│    · 完整 DOM 快照                             │
│    · 详细的对话历史                             │
│                                              │
│  50-70% 消耗 ──▶ 节约模式                     │
│    · 截图降低分辨率（-50% Token）               │
│    · DOM 快照只保留关键元素                     │
│    · 开始触发摘要压缩                          │
│                                              │
│  70-90% 消耗 ──▶ 精简模式                     │
│    · 取消截图，使用纯文本页面描述               │
│    · 只保留最近 3 轮对话                       │
│    · 切换到更便宜的模型（gpt-4o-mini）         │
│                                              │
│  >90% 消耗 ──▶ 紧急模式                      │
│    · 只保留 System Prompt + 最近 1 轮          │
│    · 任务降级为"尽力完成"模式                  │
│    · 记录预算预警日志                          │
│                                              │
└──────────────────────────────────────────────┘
```

#### 实时计量实现

```python
import tiktoken

class TokenMeter:
    """Token 实时计量器"""
    
    def __init__(self, model: str = "gpt-4o"):
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count_text(self, text: str) -> int:
        return len(self.encoding.encode(text))
    
    def count_messages(self, messages: list[dict]) -> int:
        """计算消息列表的总 Token 数"""
        total = 0
        for msg in messages:
            total += 4  # 每条消息的固定开销
            total += self.count_text(msg.get("content", ""))
            if "tool_calls" in msg:
                total += self.count_text(json.dumps(msg["tool_calls"]))
        total += 2  # 回复的固定开销
        return total
    
    def count_image(self, width: int, height: int, detail: str = "high") -> int:
        """估算图片的 Token 消耗"""
        if detail == "low":
            return 85
        # 高清模式：按 512×512 块计算
        tiles = ((width + 511) // 512) * ((height + 511) // 512)
        return 85 + 170 * tiles
```

> 💡 **第 4 章小结**：上下文管理是浏览器 Agent 的「续命术」。滑动窗口确保关键信息不丢失，摘要压缩将历史步骤凝练为精华，Token 预算机制防止成本失控。三者配合，让 Agent 能稳定执行 50 步以上的长任务而不中断。

---

## 5. Playwright 动作库工程化：可组合、可重试、隔离安全

第 3 章从任务引擎的视角设计了「原子动作」的抽象接口，本章进入执行层——基于 Playwright 实现这些动作的底层细节。Playwright 是浏览器自动化的事实标准，但「能用 Playwright 写脚本」和「能用 Playwright 构建生产级系统」之间有巨大鸿沟：隔离架构、错误处理、反检测、资源管理，每一项都需要严谨的工程化设计。

### 5.1 Browser → Context → Page 隔离架构的工程化落地

#### Playwright 的三层架构

Playwright 的核心抽象是三层嵌套结构：

```
Browser（浏览器进程）
  │  一个 Browser = 一个 Chromium 进程
  │  通常整个系统只启动 1 个
  │
  ├── BrowserContext（隔离上下文）
  │     │  一个 Context = 一个「隐身窗口」
  │     │  Cookie、Storage、缓存完全隔离
  │     │  每个任务分配 1 个 Context
  │     │
  │     ├── Page（标签页）
  │     │     一个 Page = 一个浏览器标签
  │     │     每个步骤在 Page 上操作
  │     │
  │     └── Page（可以有多个标签）
  │
  └── BrowserContext（另一个任务的隔离环境）
        └── Page
```

#### 为什么隔离如此重要？

想象两个 Agent 同时执行任务：Agent A 在京东下单，Agent B 在淘宝比价。如果它们共享同一个 Context：

- Agent A 的登录 Cookie 会被 Agent B 看到
- Agent B 设置的代理会影响 Agent A 的请求
- 一个 Page 崩溃可能导致另一个 Page 的状态丢失

Context 隔离保证：**每个任务的浏览器状态完全独立，互不干扰。**

#### 工程化实现：Context 工厂

```python
from playwright.async_api import async_playwright, Browser, BrowserContext

class BrowserManager:
    """浏览器管理器：管理 Browser 生命周期和 Context 分配"""
    
    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None
        self._active_contexts: dict[str, BrowserContext] = {}
    
    async def start(self):
        """启动浏览器（整个系统生命周期只调用一次）"""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",   # Docker 环境必须
                "--no-sandbox",               # Docker 环境必须
            ]
        )
    
    async def create_context(
        self, 
        task_id: str,
        proxy: dict | None = None,
        user_agent: str | None = None,
    ) -> BrowserContext:
        """为任务创建隔离的 BrowserContext"""
        context_options = {
            "viewport": {"width": 1280, "height": 720},
            "ignore_https_errors": True,
        }
        if proxy:
            context_options["proxy"] = proxy
        if user_agent:
            context_options["user_agent"] = user_agent
        
        context = await self._browser.new_context(**context_options)
        
        # 注入反检测脚本（详见 5.3）
        await context.add_init_script(STEALTH_SCRIPT)
        
        self._active_contexts[task_id] = context
        return context
    
    async def destroy_context(self, task_id: str):
        """任务完成后销毁 Context，释放资源"""
        context = self._active_contexts.pop(task_id, None)
        if context:
            # 关闭所有 Page
            for page in context.pages:
                await page.close()
            await context.close()
    
    async def shutdown(self):
        """关闭整个浏览器"""
        for task_id in list(self._active_contexts.keys()):
            await self.destroy_context(task_id)
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
```

#### 使用方式：Context 作为任务边界

```python
async def run_task(browser_mgr: BrowserManager, task: Task):
    """每个任务在独立的 Context 中执行"""
    context = await browser_mgr.create_context(
        task_id=task.id,
        proxy={"server": "http://proxy-pool:8080"},
    )
    try:
        page = await context.new_page()
        for step in task.steps:
            action = create_action(step)
            ctx = ActionContext(page=page, task_id=task.id, ...)
            result = await action.run(ctx)
            if not result.success:
                raise TaskStepFailed(step=step, error=result.error)
    finally:
        # 无论成功还是失败，都要清理 Context
        await browser_mgr.destroy_context(task.id)
```

> 💡 `finally` 块中的清理至关重要——如果不清理，每个失败的任务都会留下一个孤儿 Context，累积起来会导致内存泄漏。详见 5.4 节。

### 5.2 动作封装模式：统一返回结构、错误分类、超时策略

3.1 节定义了 `BaseAction` 的抽象接口，这里聚焦 Playwright 层面的实战细节：错误怎么分类、超时怎么设置、返回结构怎么保证一致。

#### Playwright 错误分类

Playwright 抛出的异常种类繁多，必须分类处理：

```python
from playwright.async_api import Error as PlaywrightError, TimeoutError

class ErrorClassifier:
    """将 Playwright 异常分类为可操作的错误类型"""
    
    @staticmethod
    def classify(error: Exception) -> tuple[str, bool]:
        """返回 (error_code, retryable)"""
        msg = str(error).lower()
        
        # 元素不存在 —— 可能是页面未加载完，可重试
        if "waiting for selector" in msg or "no element" in msg:
            return "ELEMENT_NOT_FOUND", True
        
        # 页面导航超时 —— 网络问题，可重试
        if isinstance(error, TimeoutError):
            return "TIMEOUT", True
        
        # 页面已关闭 —— Context 被销毁，不可重试
        if "target closed" in msg or "target page" in msg:
            return "PAGE_CLOSED", False
        
        # 元素被遮挡 —— 可能有弹窗，可重试（先关弹窗）
        if "intercept" in msg or "click" in msg and "other element" in msg:
            return "ELEMENT_INTERCEPTED", True
        
        # 导航被拒绝 —— 可能是反爬，可重试（换代理）
        if "net::err" in msg or "403" in msg or "blocked" in msg:
            return "NAVIGATION_BLOCKED", True
        
        # 未知错误
        return "UNKNOWN", False
```

#### 多级超时策略

不同操作需要不同的超时设置：

```python
class TimeoutConfig:
    """分层超时配置"""
    
    # 操作级超时
    CLICK_TIMEOUT = 5_000        # 点击：5s（元素应该已经可见）
    FILL_TIMEOUT = 3_000         # 填写：3s
    
    # 等待级超时
    ELEMENT_WAIT = 10_000        # 等待元素出现：10s
    NAVIGATION_WAIT = 30_000     # 等待页面导航：30s（一些网站确实很慢）
    NETWORK_IDLE = 15_000        # 等待网络空闲：15s
    
    # 任务级超时
    STEP_TIMEOUT = 60_000        # 单步总超时：60s
    TASK_TIMEOUT = 600_000       # 整个任务总超时：10min

# 应用到动作中
async def safe_click(page, selector: str) -> ActionResult:
    try:
        # 先等待元素可见
        await page.wait_for_selector(
            selector, 
            state="visible",
            timeout=TimeoutConfig.ELEMENT_WAIT
        )
        # 再执行点击
        await page.click(
            selector, 
            timeout=TimeoutConfig.CLICK_TIMEOUT
        )
        return ActionResult(success=True)
    except Exception as e:
        code, retryable = ErrorClassifier.classify(e)
        return ActionResult(
            success=False, error=str(e),
            error_code=code, retryable=retryable
        )
```

#### 智能等待：替代 sleep

`await page.wait_for_timeout(3000)` 是最常见的新手错误——用固定等待替代条件等待。Playwright 提供了更精确的等待方式：

| 场景 | ❌ 错误方式 | ✅ 正确方式 |
| :--- | :--- | :--- |
| 等待页面加载 | `sleep(3)` | `page.wait_for_load_state("networkidle")` |
| 等待元素出现 | `sleep(2)` | `page.wait_for_selector("#result", state="visible")` |
| 等待 URL 变化 | `sleep(5)` | `page.wait_for_url("**/confirm**")` |
| 等待请求完成 | `sleep(3)` | `page.wait_for_response("**/api/submit")` |

> 💡 固定 `sleep` 不仅浪费时间（页面可能 0.5s 就加载完了），还不可靠（慢网络下 3s 可能不够）。条件等待则是「满足条件立即继续，超时才失败」。

### 5.3 反检测与反爬对抗：指纹伪装、代理轮换、行为模拟

目标网站会通过多种手段检测自动化访问。如果被识别为 Bot，轻则触发验证码，重则 IP 封禁。Harness Engineer 需要构建一套反检测体系，让 Agent 的浏览器行为尽可能接近真人。

#### 检测维度与对抗策略

| 检测维度 | 检测方式 | 对抗策略 |
| :--- | :--- | :--- |
| **浏览器指纹** | `navigator.webdriver` 为 `true` | 注入脚本覆盖该属性 |
| **User-Agent** | 检查是否为 HeadlessChrome | 设置真实浏览器 UA |
| **WebGL 指纹** | 通过 Canvas/WebGL 生成唯一指纹 | 伪装 GPU 渲染器信息 |
| **IP 信誉** | 检查 IP 是否为数据中心 IP | 使用住宅代理 |
| **行为模式** | 点击间隔完全一致（机器特征） | 添加随机延迟和鼠标轨迹 |
| **TLS 指纹** | JA3 指纹识别自动化工具 | 使用与真实浏览器一致的 TLS 配置 |

#### 反检测脚本注入

```python
STEALTH_SCRIPT = """
// 1. 隐藏 webdriver 标志
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// 2. 伪装 Chrome 插件数组（真实浏览器有默认插件）
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
        { name: 'Native Client', filename: 'internal-nacl-plugin' },
    ]
});

// 3. 伪装语言列表
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en-US', 'en']
});

// 4. 修改 Chrome runtime
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
};

// 5. 通过 Permission API 检测（真实浏览器返回 'prompt'）
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);
"""
```

#### 代理轮换

```python
class ProxyRotator:
    """代理轮换器"""
    
    def __init__(self, proxies: list[str]):
        self.proxies = proxies
        self.current_index = 0
        self.failed_proxies: set[str] = set()
    
    def get_next(self) -> dict:
        """获取下一个可用代理"""
        available = [p for p in self.proxies if p not in self.failed_proxies]
        if not available:
            # 所有代理都失败了，重置并重试
            self.failed_proxies.clear()
            available = self.proxies
        
        proxy = available[self.current_index % len(available)]
        self.current_index += 1
        return {"server": proxy}
    
    def mark_failed(self, proxy_server: str):
        """标记代理为失败"""
        self.failed_proxies.add(proxy_server)
```

#### 行为模拟：让 Agent 像人一样操作

```python
import random

async def human_like_click(page, selector: str):
    """模拟人类点击行为"""
    element = await page.wait_for_selector(selector)
    box = await element.bounding_box()
    
    # 1. 在元素范围内随机选择点击位置（不总是点击中心）
    x = box["x"] + random.uniform(box["width"] * 0.2, box["width"] * 0.8)
    y = box["y"] + random.uniform(box["height"] * 0.2, box["height"] * 0.8)
    
    # 2. 模拟鼠标移动轨迹（不是瞬间跳过去）
    await page.mouse.move(x, y, steps=random.randint(5, 15))
    
    # 3. 随机短暂停顿（人类会有微小犹豫）
    await page.wait_for_timeout(random.randint(50, 200))
    
    # 4. 点击
    await page.mouse.click(x, y)

async def human_like_type(page, selector: str, text: str):
    """模拟人类打字行为"""
    await page.click(selector)
    for char in text:
        await page.keyboard.type(char, delay=random.randint(50, 150))
        # 偶尔打字会有较长停顿
        if random.random() < 0.05:
            await page.wait_for_timeout(random.randint(300, 800))
```

> 💡 反检测是攻防对抗，没有一劳永逸的方案。建议维护一个检测点清单，定期检查目标网站是否更新了检测策略。

### 5.4 资源生命周期管理：Context 池化、Page 回收、内存泄漏防护

每个 BrowserContext 大约占用 50-200MB 内存。如果创建后不回收，10 个并发任务就可能消耗 2GB 内存。资源管理是生产级 Playwright 系统的生死线。

#### Context 池化

频繁创建/销毁 Context 有开销（每次约 200-500ms）。对于高吞吐场景，可以池化复用：

```python
import asyncio

class ContextPool:
    """BrowserContext 对象池"""
    
    def __init__(self, browser: Browser, max_size: int = 20):
        self.browser = browser
        self.max_size = max_size
        self._pool: asyncio.Queue[BrowserContext] = asyncio.Queue(maxsize=max_size)
        self._created_count = 0
    
    async def acquire(self, task_id: str) -> BrowserContext:
        """从池中获取一个 Context"""
        try:
            # 优先复用已有的
            context = self._pool.get_nowait()
            # 清理上一个任务的状态
            await self._reset_context(context)
            return context
        except asyncio.QueueEmpty:
            if self._created_count < self.max_size:
                # 池未满，创建新的
                self._created_count += 1
                return await self.browser.new_context()
            else:
                # 池已满，等待释放
                return await asyncio.wait_for(
                    self._pool.get(), timeout=30.0
                )
    
    async def release(self, context: BrowserContext):
        """归还 Context 到池中"""
        try:
            # 关闭所有 Page，但保留 Context
            for page in context.pages:
                await page.close()
            await self._pool.put_nowait(context)
        except asyncio.QueueFull:
            # 池已满，直接销毁
            await context.close()
            self._created_count -= 1
    
    async def _reset_context(self, context: BrowserContext):
        """重置 Context 状态，为下一个任务准备"""
        await context.clear_cookies()
        for page in context.pages:
            await page.close()
```

#### 内存泄漏防护

Playwright 的常见内存泄漏场景：

```python
class MemoryGuard:
    """内存使用监控"""
    
    def __init__(self, threshold_mb: int = 2048):
        self.threshold_mb = threshold_mb
    
    async def check(self, browser_mgr: BrowserManager) -> dict:
        """检查内存使用情况"""
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        active_contexts = len(browser_mgr._active_contexts)
        
        status = {
            "memory_mb": round(memory_mb, 1),
            "active_contexts": active_contexts,
            "healthy": memory_mb < self.threshold_mb,
        }
        
        if not status["healthy"]:
            # 内存超标，强制回收最老的 Context
            await self._force_cleanup(browser_mgr)
        
        return status
    
    async def _force_cleanup(self, browser_mgr: BrowserManager):
        """紧急清理：释放最老的 Context"""
        contexts = list(browser_mgr._active_contexts.items())
        if contexts:
            oldest_task_id, _ = contexts[0]
            await browser_mgr.destroy_context(oldest_task_id)
```

#### Context 生命周期的完整管理

用 async context manager 确保资源一定被释放：

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_context(browser_mgr: BrowserManager, task_id: str, **kwargs):
    """确保 Context 在任何情况下都被释放"""
    context = await browser_mgr.create_context(task_id, **kwargs)
    try:
        yield context
    except Exception:
        # 异常时截图保存现场
        for page in context.pages:
            try:
                await page.screenshot(path=f"/app/crashes/{task_id}.png")
            except Exception:
                pass
        raise
    finally:
        await browser_mgr.destroy_context(task_id)

# 使用方式
async def run_task(browser_mgr, task):
    async with managed_context(browser_mgr, task.id) as context:
        page = await context.new_page()
        # ... 执行任务 ...
    # 离开 with 块时 Context 一定会被销毁
```

> 💡 **第 5 章小结**：Playwright 动作库的工程化核心是四个字——「隔离安全」。Context 隔离保证任务互不干扰，错误分类让失败可处理，反检测让 Agent 不被封禁，资源管理防止系统被撑爆。这是浏览器 Agent 最直接面对真实世界的一层，也是工程挑战最密集的一层。

---

## 6. 并行 Agent 调度：asyncio + Semaphore 到任务队列

前面 5 章讨论的都是「一个 Agent 执行一个任务」的场景。但生产环境中，你需要同时运行数十甚至数百个任务——批量数据抓取、多账号操作、并行表单填写。这时，**并发调度**就成了核心瓶颈：如何控制并发数量、如何处理任务失败、如何在不超出资源上限的前提下最大化吞吐？

### 6.1 asyncio 并发模型：Semaphore 限流、TaskGroup 管理、优雅取消

#### 为什么是 asyncio？

浏览器自动化的核心操作（页面加载、等待元素、网络请求）都是 **I/O 密集型**——大部分时间在等待响应。asyncio 的协程模型天然适合这类场景：一个任务在等待页面加载时，CPU 可以去执行另一个任务的动作。

```
多线程模型 vs asyncio 模型对比：

  多线程（10 个 Worker 线程）：
  Thread-1: [执行] [等待....] [执行] [等待......]
  Thread-2: [执行] [等待......] [执行] [等待..]
  ...
  → 10 个线程各自阻塞，资源利用率低，线程切换开销大

  asyncio（1 个事件循环，10 个协程）：
  EventLoop: [Task1执行][Task2执行][Task3执行][Task1继续][Task2继续]...
  → 单线程内切换，0 线程切换开销，I/O 等待期间自动切换
```

#### Semaphore 控制并发上限

不加限制地创建协程会导致资源耗尽。`asyncio.Semaphore` 是最直接的并发控制原语：

```python
import asyncio

class ConcurrentTaskRunner:
    """基于 Semaphore 的并发任务执行器"""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks: dict[str, asyncio.Task] = {}
    
    async def run_task(self, task_id: str, coro):
        """受限并发地执行任务"""
        async with self.semaphore:  # 最多 max_concurrent 个任务同时执行
            self.active_tasks[task_id] = asyncio.current_task()
            try:
                return await coro
            finally:
                self.active_tasks.pop(task_id, None)
    
    async def run_batch(self, tasks: list[tuple[str, Coroutine]]):
        """批量执行任务"""
        async with asyncio.TaskGroup() as tg:
            results = {}
            for task_id, coro in tasks:
                async def _wrapper(tid=task_id, c=coro):
                    results[tid] = await self.run_task(tid, c)
                tg.create_task(_wrapper())
        return results
```

#### TaskGroup：结构化并发

Python 3.11 引入的 `asyncio.TaskGroup` 解决了「一个任务失败，其他任务怎么办」的问题：

```python
# ❌ gather 的问题：一个失败，其他继续跑（浪费资源）
results = await asyncio.gather(*tasks, return_exceptions=True)

# ✅ TaskGroup：一个失败，自动取消其他任务
async with asyncio.TaskGroup() as tg:
    task1 = tg.create_task(run_agent("task_1"))
    task2 = tg.create_task(run_agent("task_2"))
    task3 = tg.create_task(run_agent("task_3"))
# 如果 task2 抛异常，task1 和 task3 会被自动 cancel
```

#### 优雅取消

取消一个正在执行 Playwright 操作的协程，需要清理浏览器资源：

```python
async def cancellable_task(browser_mgr: BrowserManager, task: Task):
    """支持优雅取消的任务执行"""
    context = None
    try:
        context = await browser_mgr.create_context(task.id)
        page = await context.new_page()
        
        for step in task.steps:
            # 每步之前检查是否被取消
            if asyncio.current_task().cancelled():
                break
            await execute_step(page, step)
            
    except asyncio.CancelledError:
        # 被取消时的清理逻辑
        print(f"任务 {task.id} 被取消，正在清理资源...")
        raise  # 必须重新抛出 CancelledError
    finally:
        if context:
            await browser_mgr.destroy_context(task.id)
```

> 💡 **关键规则**：捕获 `CancelledError` 做完清理后，必须 `raise` 重新抛出。如果吞掉这个异常，TaskGroup 无法感知到取消完成，会导致挂起。

### 6.2 任务队列选型：内存队列 vs Redis/BullMQ vs 专业队列

当任务量超过单进程的处理能力，就需要引入外部队列来解耦「任务提交」和「任务执行」。

#### 选型对比

| 方案 | 持久化 | 跨进程 | 延迟重试 | 优先级 | 适用规模 | 复杂度 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **asyncio.Queue** | ❌ | ❌ | ❌ | ❌ | < 100 任务/分钟 | ⭐ |
| **Redis + arq** | ✅ | ✅ | ✅ | ✅ | 100-5000 任务/分钟 | ⭐⭐ |
| **Celery + RabbitMQ** | ✅ | ✅ | ✅ | ✅ | 1000-50000 任务/分钟 | ⭐⭐⭐ |
| **Temporal / Prefect** | ✅ | ✅ | ✅ | ✅ | 无上限 | ⭐⭐⭐⭐ |

#### 推荐路径

```
起步阶段（< 10 并发）
  └── asyncio.Queue + Semaphore
      纯内存，零外部依赖，适合 MVP

成长阶段（10-100 并发）
  └── Redis + arq（Python）/ BullMQ（Node.js）
      轻量级持久化队列，支持延迟重试和优先级

规模化阶段（100+ 并发）
  └── Temporal / Celery
      完整的工作流编排，支持跨机器分布式执行
```

#### arq 实战示例

arq 是 Python 生态中最轻量的 Redis 任务队列，非常适合浏览器 Agent 场景：

```python
from arq import create_pool
from arq.connections import RedisSettings

# 定义 Worker 函数
async def execute_browser_task(ctx, task_id: str, template_id: str, params: dict):
    """arq Worker：执行浏览器任务"""
    browser_mgr = ctx["browser_mgr"]
    
    async with managed_context(browser_mgr, task_id) as context:
        page = await context.new_page()
        template = load_template(template_id)
        result = await run_template(page, template, params)
        return result

# Worker 配置
class WorkerSettings:
    functions = [execute_browser_task]
    redis_settings = RedisSettings(host="localhost", port=6379)
    max_jobs = 10              # 最多 10 个并发任务
    job_timeout = 600          # 单任务超时 10 分钟
    max_tries = 3              # 最多重试 3 次

# 提交任务
async def submit_task(task_id: str, template_id: str, params: dict):
    redis = await create_pool(RedisSettings())
    job = await redis.enqueue_job(
        "execute_browser_task",
        task_id, template_id, params,
        _job_id=task_id,        # 防止重复提交
        _queue_name="browser",
    )
    return job.job_id
```

### 6.3 超时取消与资源回收：防止僵尸任务和资源泄漏

僵尸任务是并发系统的头号杀手——一个任务卡在某个页面加载上永远不返回，它占用的 Context、内存、Semaphore 槽位都不会被释放，最终导致整个系统被「拖死」。

#### 多层超时防护

```
┌──────────────────────────────────────────┐
│           超时防护层级                      │
├──────────────────────────────────────────┤
│                                          │
│  L1：操作级超时（Playwright）               │
│  ── page.click(timeout=5000)             │
│  ── 单个操作最多等 5 秒                    │
│                                          │
│  L2：步骤级超时（BaseAction）               │
│  ── asyncio.wait_for(step, timeout=60)   │
│  ── 单个步骤（含重试）最多 60 秒            │
│                                          │
│  L3：任务级超时（TaskRunner）               │
│  ── asyncio.wait_for(task, timeout=600)  │
│  ── 整个任务最多 10 分钟                   │
│                                          │
│  L4：系统级超时（Watchdog）                 │
│  ── 定期扫描超时任务，强制杀死              │
│  ── 兜底保护，防止 L1-L3 全部失效           │
│                                          │
└──────────────────────────────────────────┘
```

#### Watchdog 看门狗实现

```python
class TaskWatchdog:
    """任务看门狗：定期扫描并清理超时任务"""
    
    def __init__(self, timeout_seconds: int = 600):
        self.timeout = timeout_seconds
        self.task_start_times: dict[str, float] = {}
        self._running = False
    
    def register(self, task_id: str):
        self.task_start_times[task_id] = time.monotonic()
    
    def deregister(self, task_id: str):
        self.task_start_times.pop(task_id, None)
    
    async def start(self, runner: ConcurrentTaskRunner, browser_mgr: BrowserManager):
        """启动看门狗循环"""
        self._running = True
        while self._running:
            now = time.monotonic()
            for task_id, start_time in list(self.task_start_times.items()):
                elapsed = now - start_time
                if elapsed > self.timeout:
                    print(f"⚠️ 任务 {task_id} 超时 ({elapsed:.0f}s)，强制终止")
                    
                    # 1. 取消协程
                    if task_id in runner.active_tasks:
                        runner.active_tasks[task_id].cancel()
                    
                    # 2. 清理浏览器资源
                    await browser_mgr.destroy_context(task_id)
                    
                    # 3. 从注册表移除
                    self.deregister(task_id)
            
            await asyncio.sleep(10)  # 每 10 秒扫描一次
```

> 💡 看门狗是最后一道防线——即使你的所有超时配置都失效了，看门狗仍然会把僵尸任务清理掉。

### 6.4 失败分级重试：瞬时失败 vs 可恢复失败 vs 永久失败

不是所有失败都值得重试。盲目重试不仅浪费资源，还可能加剧问题（比如对已被封禁的 IP 反复请求）。需要根据失败的性质制定不同的重试策略。

#### 三级失败分类

| 失败级别 | 特征 | 示例 | 重试策略 |
| :--- | :--- | :--- | :--- |
| 🟡 **瞬时失败** | 随机发生、短暂持续 | 网络抖动、DNS 解析延迟、页面加载慢 | 立即重试，最多 3 次 |
| 🟠 **可恢复失败** | 需要改变策略后重试 | IP 封禁、验证码、Session 过期 | 延迟重试 + 更换代理/刷新登录 |
| 🔴 **永久失败** | 无论如何重试都不会成功 | 目标页面 404、模板选择器全部失效 | 不重试，直接标记失败 |

#### 退避策略实现

```python
import random

class RetryPolicy:
    """分级重试策略"""
    
    @staticmethod
    def get_delay(error_code: str, attempt: int) -> float | None:
        """返回重试延迟（秒），None 表示不重试"""
        
        # 瞬时失败：指数退避 + 随机抖动
        if error_code in ("TIMEOUT", "ELEMENT_NOT_FOUND"):
            base_delay = min(2 ** attempt, 30)  # 1, 2, 4, 8, 16, 30
            jitter = random.uniform(0, base_delay * 0.3)
            return base_delay + jitter
        
        # 可恢复失败：更长的延迟 + 需要执行恢复动作
        if error_code in ("NAVIGATION_BLOCKED", "ELEMENT_INTERCEPTED"):
            return 30 + random.uniform(0, 30)   # 30-60 秒后重试
        
        # 永久失败：不重试
        if error_code in ("PAGE_CLOSED", "UNKNOWN"):
            return None
        
        # 未知错误：保守策略，重试 1 次
        return 5.0 if attempt < 1 else None
    
    @staticmethod
    def get_recovery_action(error_code: str) -> str | None:
        """某些错误需要在重试前执行恢复动作"""
        recovery_map = {
            "NAVIGATION_BLOCKED": "rotate_proxy",    # 换代理
            "ELEMENT_INTERCEPTED": "close_popups",   # 关弹窗
            "SESSION_EXPIRED": "re_login",           # 重新登录
        }
        return recovery_map.get(error_code)
```

### 6.5 结果聚合与部分成功处理

批量任务的执行结果很少是「全部成功」或「全部失败」——更常见的情况是「80% 成功，15% 可重试失败，5% 永久失败」。系统需要优雅地处理这种**部分成功**。

#### 批量结果结构

```python
@dataclass
class BatchResult:
    """批量任务执行结果"""
    total: int
    succeeded: list[TaskResult]
    failed: list[TaskResult]
    retryable: list[TaskResult]
    
    @property
    def success_rate(self) -> float:
        return len(self.succeeded) / self.total if self.total > 0 else 0
    
    @property
    def summary(self) -> dict:
        return {
            "total": self.total,
            "succeeded": len(self.succeeded),
            "failed": len(self.failed),
            "retryable": len(self.retryable),
            "success_rate": f"{self.success_rate:.1%}",
        }

async def run_batch_with_aggregation(
    tasks: list[Task],
    runner: ConcurrentTaskRunner
) -> BatchResult:
    """执行批量任务并聚合结果"""
    results = BatchResult(total=len(tasks), succeeded=[], failed=[], retryable=[])
    
    async def _execute_one(task: Task):
        try:
            result = await runner.run_task(task.id, execute_task(task))
            if result.success:
                results.succeeded.append(result)
            else:
                if result.retryable:
                    results.retryable.append(result)
                else:
                    results.failed.append(result)
        except Exception as e:
            results.failed.append(TaskResult(
                task_id=task.id, success=False, error=str(e)
            ))
    
    # 并发执行所有任务（Semaphore 控制并发数）
    async with asyncio.TaskGroup() as tg:
        for task in tasks:
            tg.create_task(_execute_one(task))
    
    return results
```

#### 部分成功的处理决策

```
批量结果处理策略：

  成功率 ≥ 95%  →  视为成功，retryable 的自动重试
  成功率 80-95% →  报告结果，retryable 的自动重试，通知运维
  成功率 50-80% →  暂停新任务提交，排查失败原因
  成功率 < 50%  →  熔断！停止所有任务，可能是系统级故障
```

> 💡 **第 6 章小结**：并行调度是将单个 Agent 扩展到生产规模的关键。asyncio + Semaphore 控制并发上限，任务队列实现持久化调度，多层超时防止僵尸任务，分级重试高效利用重试预算，结果聚合让批量任务的成败一目了然。这些技术组合起来，构成了一个可控、可观测、可伸缩的并行执行引擎。

---

## 7. Orchestrator-Worker 任务编排架构

第 6 章的并行调度解决了单机多任务的并发问题。但当任务量超过单机承载能力（一台机器最多同时跑 20-30 个浏览器 Context），就需要将任务分发到多台机器上——这就是 Orchestrator-Worker 架构要解决的问题。

### 7.1 架构设计：Orchestrator 调度 + Worker 执行的职责分离

#### 核心思想：调度与执行分离

```
                    ┌──────────────────┐
                    │   API / 用户请求   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Orchestrator    │
                    │   （编排器）        │
                    │                  │
                    │  · 接收任务请求    │
                    │  · 拆分子任务     │
                    │  · 选择 Worker    │
                    │  · 聚合结果      │
                    │  · 管理全局状态   │
                    └──┬─────┬─────┬───┘
                       │     │     │
              ┌────────┘     │     └────────┐
              ▼              ▼              ▼
        ┌───────────┐ ┌───────────┐ ┌───────────┐
        │  Worker 1  │ │  Worker 2  │ │  Worker 3  │
        │            │ │            │ │            │
        │ · Browser  │ │ · Browser  │ │ · Browser  │
        │ · Context  │ │ · Context  │ │ · Context  │
        │ · 执行任务  │ │ · 执行任务  │ │ · 执行任务  │
        └───────────┘ └───────────┘ └───────────┘
```

#### 职责边界

| 组件 | 职责 | 不做的事 |
| :--- | :--- | :--- |
| **Orchestrator** | 任务调度、Worker 管理、结果聚合、全局状态 | 不启动浏览器、不执行 Playwright 操作 |
| **Worker** | 启动浏览器、执行任务、上报结果、汇报健康状态 | 不做任务分配决策、不管理其他 Worker |

#### Orchestrator 核心实现

```python
class Orchestrator:
    """任务编排器"""
    
    def __init__(self):
        self.workers: dict[str, WorkerInfo] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.task_assignments: dict[str, str] = {}  # task_id → worker_id
    
    async def submit_task(self, task: Task) -> str:
        """接收任务并分发到合适的 Worker"""
        worker = self._select_worker(task)
        if not worker:
            # 没有可用 Worker，放入队列等待
            await self.task_queue.put(task)
            return "queued"
        
        self.task_assignments[task.id] = worker.worker_id
        await self._dispatch_to_worker(worker, task)
        return "dispatched"
    
    def _select_worker(self, task: Task) -> WorkerInfo | None:
        """选择最佳 Worker（详见 7.3）"""
        available = [
            w for w in self.workers.values()
            if w.status == "healthy" and w.current_load < w.max_capacity
        ]
        if not available:
            return None
        # 选择负载最低的 Worker
        return min(available, key=lambda w: w.current_load)
    
    async def handle_task_result(self, task_id: str, result: TaskResult):
        """处理 Worker 上报的任务结果"""
        worker_id = self.task_assignments.pop(task_id, None)
        if worker_id and worker_id in self.workers:
            self.workers[worker_id].current_load -= 1
        
        if not result.success and result.retryable:
            # 可重试的失败：重新分发（可能给不同的 Worker）
            await self.submit_task(result.original_task)
        
        # 检查队列中是否有等待的任务
        await self._drain_queue()

@dataclass
class WorkerInfo:
    worker_id: str
    address: str               # Worker 的 HTTP 地址
    status: str = "healthy"    # healthy / unhealthy / draining
    max_capacity: int = 10     # 最大并发任务数
    current_load: int = 0      # 当前执行中的任务数
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    tags: list[str] = field(default_factory=list)  # 用于亲和性调度
```

> 💡 Orchestrator 本身需要是无状态的（状态存 Redis/DB），这样 Orchestrator 故障后可以快速恢复。

### 7.2 Worker 注册、心跳与健康检查

Orchestrator 需要知道「有多少 Worker 可用、每个 Worker 的状态如何」。这通过注册-心跳-健康检查三步机制实现。

#### 注册流程

```
Worker 启动
    │
    ├── 1. 启动 Playwright Browser
    ├── 2. 自检通过（能正常创建 Context + Page）
    │
    └── 3. 向 Orchestrator 发送注册请求
           POST /api/workers/register
           {
             "worker_id": "worker-az1-001",
             "address": "http://10.0.1.5:8080",
             "max_capacity": 10,
             "tags": ["region:az1", "proxy:residential"],
             "version": "1.3.0"
           }
```

#### 心跳机制

Worker 每隔 N 秒向 Orchestrator 上报自身状态：

```python
class WorkerHeartbeat:
    """Worker 端的心跳上报"""
    
    def __init__(self, orchestrator_url: str, worker_id: str, interval: int = 15):
        self.orchestrator_url = orchestrator_url
        self.worker_id = worker_id
        self.interval = interval
    
    async def start(self, browser_mgr: BrowserManager):
        """定期发送心跳"""
        while True:
            heartbeat = {
                "worker_id": self.worker_id,
                "timestamp": datetime.utcnow().isoformat(),
                "current_load": len(browser_mgr._active_contexts),
                "memory_mb": self._get_memory_usage(),
                "cpu_percent": psutil.cpu_percent(),
                "active_tasks": list(browser_mgr._active_contexts.keys()),
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        f"{self.orchestrator_url}/api/workers/heartbeat",
                        json=heartbeat, timeout=5
                    )
            except Exception:
                pass  # 心跳失败不应影响任务执行
            
            await asyncio.sleep(self.interval)
```

#### Orchestrator 端的健康判断

```python
class HealthChecker:
    """Orchestrator 端：基于心跳判断 Worker 健康状态"""
    
    HEALTHY_THRESHOLD = 30     # 30 秒内有心跳 → 健康
    SUSPECT_THRESHOLD = 60     # 30-60 秒无心跳 → 疑似故障
    DEAD_THRESHOLD = 90        # 90 秒无心跳 → 判定死亡
    
    def evaluate(self, worker: WorkerInfo) -> str:
        elapsed = (datetime.utcnow() - worker.last_heartbeat).total_seconds()
        
        if elapsed < self.HEALTHY_THRESHOLD:
            return "healthy"
        elif elapsed < self.SUSPECT_THRESHOLD:
            return "suspect"     # 可能正忙，暂不分配新任务
        elif elapsed < self.DEAD_THRESHOLD:
            return "unhealthy"   # 标记不健康，开始任务转移
        else:
            return "dead"        # 判定死亡，强制回收任务
```

> 💡 不要只依赖心跳超时——Worker 可能进程还在但浏览器已经崩溃。心跳中携带 `memory_mb` 和 `cpu_percent` 可以帮助 Orchestrator 识别「活着但不健康」的 Worker。

### 7.3 任务分发策略：轮询 vs 负载感知 vs 亲和性调度

Orchestrator 收到任务后，要决定「交给哪个 Worker 执行」。不同的分发策略适用于不同场景。

#### 三种策略对比

| 策略 | 原理 | 优点 | 缺点 | 适用场景 |
| :--- | :--- | :--- | :--- | :--- |
| **轮询** | 按顺序依次分配 | 实现简单、分配均匀 | 不考虑 Worker 实际负载 | Worker 性能一致的环境 |
| **负载感知** | 选择负载最低的 Worker | 资源利用最优 | 需要实时负载数据 | 通用场景 |
| **亲和性调度** | 特定任务分配给特定 Worker | 缓存命中率高、减少冷启动 | 可能导致负载不均 | 同域名任务频繁执行 |

#### 亲和性调度的价值

浏览器自动化有一个独特特征：**同一域名的任务，在同一个 Worker 上执行效率更高**：

```
亲和性调度的优势：

  Worker A 已经访问过 example.com：
  ── DNS 缓存命中（省 200ms）
  ── 代理连接已建立（省 500ms）
  ── 如果是池化 Context，Cookie/Session 可能可复用
  ── 反检测指纹已经"热身"过

  Worker B 从未访问过 example.com：
  ── DNS 查询（200ms）
  ── 代理握手（500ms）
  ── 冷启动开销
```

实现亲和性调度只需在 Worker 选择逻辑中增加亲和性评分：

```python
def _select_worker_with_affinity(self, task: Task) -> WorkerInfo | None:
    available = [
        w for w in self.workers.values()
        if w.status == "healthy" and w.current_load < w.max_capacity
    ]
    if not available:
        return None
    
    target_domain = urlparse(task.target_url).hostname
    
    def score(worker: WorkerInfo) -> float:
        # 负载得分（越低越好）
        load_score = worker.current_load / worker.max_capacity
        # 亲和性得分（有该域名经验的 Worker 减分）
        affinity_score = 0 if target_domain in worker.tags else 0.3
        return load_score + affinity_score
    
    return min(available, key=score)
```

### 7.4 横向扩展：Worker 动态伸缩与无状态设计

当任务洪峰来临时（例如批量抓取 10000 个页面），固定数量的 Worker 无法满足需求。需要动态扩缩容——任务多时增加 Worker，空闲时减少 Worker。

#### 无状态 Worker 是扩缩容的前提

Worker 必须是无状态的——所有持久化状态都存在外部存储（Redis/DB）中：

```
有状态 Worker（❌ 无法扩缩容）：
  ── 任务进度存在本地内存
  ── 检查点存在本地文件系统
  ── 如果 Worker 被杀死，这些数据全部丢失

无状态 Worker（✅ 可自由扩缩容）：
  ── 任务进度存 Redis
  ── 检查点存 S3/数据库
  ── Worker 随时可被杀死，新 Worker 从 Redis 恢复状态继续执行
```

#### 基于容器的自动伸缩

```yaml
# Kubernetes HPA 配置示例
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: browser-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: browser-worker
  minReplicas: 2        # 最少保持 2 个 Worker
  maxReplicas: 20       # 最多扩展到 20 个 Worker
  metrics:
    - type: External
      external:
        metric:
          name: pending_tasks_count   # 基于待处理任务数伸缩
        target:
          type: AverageValue
          averageValue: "5"           # 每个 Worker 分配 5 个待处理任务
```

#### 优雅下线（Draining）

缩容时不能直接杀死 Worker——它可能正在执行任务。需要先「排空」：

```python
async def graceful_shutdown(worker: Worker):
    """Worker 优雅下线"""
    # 1. 通知 Orchestrator 不要再分配新任务
    worker.status = "draining"
    await worker.notify_orchestrator(status="draining")
    
    # 2. 等待当前任务完成（最多等 5 分钟）
    deadline = time.monotonic() + 300
    while worker.active_task_count > 0 and time.monotonic() < deadline:
        await asyncio.sleep(5)
    
    # 3. 如果还有未完成的任务，将检查点保存后强制终止
    for task_id in list(worker.active_tasks):
        await worker.save_checkpoint(task_id)
        await worker.cancel_task(task_id)
    
    # 4. 清理浏览器资源
    await worker.browser_mgr.shutdown()
    
    # 5. 注销
    await worker.deregister()
```

### 7.5 容错与故障转移：Worker 挂了怎么办

Worker 可能因为各种原因宕机——OOM、浏览器崩溃、机器故障、网络分区。Orchestrator 必须能检测到故障并将任务转移到其他 Worker。

#### 故障转移流程

```
Worker-2 宕机
    │
    ▼
Orchestrator 检测到心跳超时（90 秒无心跳）
    │
    ├── 1. 标记 Worker-2 为 "dead"
    │
    ├── 2. 查询 Worker-2 上正在执行的任务
    │      task_abc, task_def, task_ghi
    │
    ├── 3. 对每个任务：
    │      ├── 检查是否有检查点？
    │      │   ├── 有 → 从检查点恢复，分配给其他 Worker
    │      │   └── 无 → 从头重新执行
    │      │
    │      └── 重新调用 submit_task()
    │
    └── 4. 任务被分配给 Worker-1 或 Worker-3
```

#### 故障转移实现

```python
async def handle_worker_failure(self, worker_id: str):
    """处理 Worker 故障"""
    worker = self.workers.get(worker_id)
    if not worker:
        return
    
    # 1. 标记为死亡
    worker.status = "dead"
    
    # 2. 获取该 Worker 上的所有任务
    orphaned_tasks = [
        task_id for task_id, wid in self.task_assignments.items()
        if wid == worker_id
    ]
    
    # 3. 逐个转移
    for task_id in orphaned_tasks:
        self.task_assignments.pop(task_id, None)
        
        # 检查是否有检查点
        checkpoint = await self.checkpoint_mgr.restore(task_id)
        if checkpoint:
            # 从检查点恢复
            await self.submit_task_with_checkpoint(task_id, checkpoint)
        else:
            # 从头重新执行
            task = await self.task_store.get(task_id)
            if task:
                task.retry_count += 1
                await self.submit_task(task)
    
    # 4. 从 Worker 列表中移除
    del self.workers[worker_id]
```

#### 防止脑裂：任务锁

故障转移最危险的场景是**脑裂**——Worker 其实没有真的死，只是网络延迟导致心跳超时。如果 Orchestrator 把任务转移给了新 Worker，而旧 Worker 还在执行同一个任务，就会出现两个 Worker 同时操作同一个任务的情况。

解决方案：**分布式锁**。

```python
async def acquire_task_lock(task_id: str, worker_id: str, ttl: int = 120) -> bool:
    """尝试获取任务锁（Redis SET NX）"""
    lock_key = f"task_lock:{task_id}"
    acquired = await redis.set(lock_key, worker_id, nx=True, ex=ttl)
    return bool(acquired)

async def renew_task_lock(task_id: str, worker_id: str, ttl: int = 120) -> bool:
    """续期任务锁（仅当前持有者可续期）"""
    lock_key = f"task_lock:{task_id}"
    current = await redis.get(lock_key)
    if current == worker_id:
        await redis.expire(lock_key, ttl)
        return True
    return False  # 锁已被其他 Worker 持有
```

Worker 在执行任务前必须先获取锁，执行期间定期续期。如果 Worker 宕机，锁会在 TTL 后自动释放，此时新 Worker 才能接管。

> 💡 **第 7 章小结**：Orchestrator-Worker 架构将浏览器 Agent 系统从「单机艺术品」升级为「分布式生产系统」。Orchestrator 负责全局调度和容错，Worker 负责无状态执行，心跳机制保障可观测性，亲和性调度优化性能，优雅下线和故障转移保证任务不丢失。这套架构让系统具备了真正的横向扩展能力。

---

## 8. 可观测性建设：让每一次执行都可追踪、可复现

一个没有可观测性的 Agent 系统就是「黑盒赌博」——任务成功了你不知道为什么，失败了你也不知道为什么。当生产环境的成功率从 92% 突然掉到 75% 时，你能在 5 分钟内定位原因吗？

可观测性由三根支柱组成：**日志**（发生了什么）、**追踪**（执行路径是什么）、**指标**（系统健康状况如何）。对浏览器 Agent 系统来说，这三根支柱有独特的实现方式。

### 8.1 结构化日志规范：tool call 入参/出参/耗时/错误码的统一格式

#### 为什么必须是结构化的？

非结构化日志：
```
[2024-03-15 10:23:45] INFO: Clicked button #submit-btn, took 1.2s
[2024-03-15 10:23:46] ERROR: Failed to fill form, element not found
```

看起来可读，但无法被机器解析——你没法用 SQL 查询「过去一小时所有 ELEMENT_NOT_FOUND 错误的任务 ID」。

结构化日志：
```json
{"ts":"2024-03-15T10:23:45Z","level":"info","task_id":"t_abc","step":7,
 "tool":"browser_click","params":{"selector":"#submit-btn"},
 "result":{"success":true},"duration_ms":1200,"worker_id":"w-001"}
```

#### 统一日志格式

所有工具调用必须产出以下结构的日志：

```python
@dataclass
class ToolCallLog:
    # 时间与标识
    timestamp: str               # ISO 8601 格式
    task_id: str                 # 任务 ID
    step_index: int              # 步骤序号
    worker_id: str               # Worker ID
    
    # 工具调用
    tool_name: str               # 工具名称
    params: dict                 # 输入参数（脱敏后）
    
    # 执行结果
    success: bool
    result_data: dict | None     # 成功时的返回数据
    error: str | None            # 错误信息
    error_code: str | None       # 机器可读错误码
    
    # 性能指标
    duration_ms: int             # 执行耗时
    retry_count: int             # 重试次数
    
    # 上下文
    page_url: str | None         # 执行时的页面 URL
    screenshot_key: str | None   # 截图存储路径

class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, output: str = "stdout"):
        self.output = output
    
    def log_tool_call(self, log: ToolCallLog):
        entry = {
            "ts": log.timestamp,
            "task_id": log.task_id,
            "step": log.step_index,
            "worker": log.worker_id,
            "tool": log.tool_name,
            "params": self._sanitize(log.params),
            "success": log.success,
            "error_code": log.error_code,
            "duration_ms": log.duration_ms,
            "retries": log.retry_count,
            "page_url": log.page_url,
        }
        print(json.dumps(entry, ensure_ascii=False))
    
    def _sanitize(self, params: dict) -> dict:
        """脱敏：隐藏密码、Token 等敏感参数"""
        sensitive_keys = {"password", "token", "api_key", "secret"}
        return {
            k: "***" if k in sensitive_keys else v
            for k, v in params.items()
        }
```

> 💡 **黄金法则**：看到一条日志，就能回答「谁在什么时候对哪个页面做了什么操作，结果如何，花了多久」。缺少任何一个维度都会让排查变得困难。

### 8.2 操作时间线：从用户指令到最终结果的完整链路

单条日志告诉你「某一步做了什么」，操作时间线告诉你「整个任务的完整执行过程」。

#### 时间线数据结构

```python
@dataclass
class TaskTimeline:
    """任务执行时间线"""
    task_id: str
    template_id: str
    started_at: str
    completed_at: str | None
    status: str
    worker_id: str
    total_steps: int
    steps: list[StepRecord]

@dataclass
class StepRecord:
    index: int
    tool_name: str
    started_at: str
    completed_at: str
    duration_ms: int
    success: bool
    error_code: str | None
    page_url: str
    screenshot_key: str | None
```

#### 时间线可视化

将时间线渲染为人类可读的格式，用于调试和汇报：

```
任务 t_abc123 执行时间线
模板：ecommerce_order v1.2.0
Worker：w-az1-001
状态：completed ✅

 #   时间          耗时    工具              结果   页面
 ─────────────────────────────────────────────────────
 1   10:23:45.1    320ms   browser_navigate  ✅    shop.example.com
 2   10:23:45.5    1.2s    browser_fill      ✅    shop.example.com/search
 3   10:23:46.7    890ms   browser_click     ✅    shop.example.com/search
 4   10:23:47.6    2.1s    browser_click     ✅    shop.example.com/product/123
 5   10:23:49.7    450ms   browser_click     ✅    shop.example.com/cart
 6   10:23:50.2    1.8s    browser_fill      ❌ →  shop.example.com/checkout
                           ELEMENT_NOT_FOUND (retry 1/3)
 6'  10:23:52.0    920ms   browser_fill      ✅    shop.example.com/checkout
 7   10:23:52.9    3.2s    browser_click     ✅    shop.example.com/confirm

 总耗时：7.8s | 步骤：7/7 完成 | 重试：1 次 | Token：12.3K
```

这种时间线让你一眼就能看出：哪一步最慢（Step 7: 3.2s）、哪一步出了问题（Step 6: 重试）、整体耗时分布。

### 8.3 Playwright Trace + LLM 链路的关联追踪

浏览器 Agent 的执行链路跨越两个世界：**LLM 推理**（决定做什么）和 **Playwright 执行**（实际操作浏览器）。将两者关联起来是排查问题的关键。

#### Playwright Trace

Playwright 内置了 Trace 功能，可以录制完整的浏览器操作过程：

```python
async def execute_with_trace(context: BrowserContext, task: Task):
    """开启 Trace 录制"""
    # 启动录制
    await context.tracing.start(
        screenshots=True,    # 每步截图
        snapshots=True,      # DOM 快照
        sources=True,        # 源码定位
    )
    
    try:
        page = await context.new_page()
        result = await run_task(page, task)
        return result
    finally:
        # 保存 Trace 文件
        trace_path = f"/app/traces/{task.id}.zip"
        await context.tracing.stop(path=trace_path)
        # Trace 文件可以用 playwright show-trace 命令打开
        # 或上传到 trace.playwright.dev 在线查看
```

#### 关联 Trace ID

用统一的 Trace ID 将 LLM 调用和 Playwright 操作串联起来：

```python
import uuid

class TraceContext:
    """贯穿 LLM + Playwright 的追踪上下文"""
    
    def __init__(self, task_id: str):
        self.trace_id = str(uuid.uuid4())[:8]
        self.task_id = task_id
        self.spans: list[dict] = []
    
    def start_span(self, name: str, span_type: str) -> dict:
        span = {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "span_id": str(uuid.uuid4())[:8],
            "name": name,
            "type": span_type,     # "llm" | "playwright" | "tool"
            "started_at": datetime.utcnow().isoformat(),
        }
        self.spans.append(span)
        return span
    
    def end_span(self, span: dict, **kwargs):
        span["completed_at"] = datetime.utcnow().isoformat()
        span.update(kwargs)

# 使用示例
trace = TraceContext(task_id="t_abc")

# LLM 推理
llm_span = trace.start_span("llm_decide_action", "llm")
action = await llm.decide(messages)
trace.end_span(llm_span, tokens=1200, model="gpt-4o")

# Playwright 执行
pw_span = trace.start_span("browser_click", "playwright")
result = await page.click(action.selector)
trace.end_span(pw_span, success=True, selector=action.selector)
```

这样查询时，输入一个 `trace_id` 就能看到：LLM 花了多久决定做什么 → Playwright 花了多久执行 → 结果如何。

### 8.4 失败复现：从日志重建完整执行上下文

Agent 系统最痛苦的调试场景：「昨晚有 50 个任务失败了，现在复现不了」。失败复现能力是可观测性的终极目标——不仅要知道「出了什么错」，还要能「重现那个错误」。

#### 失败现场保存

任务失败时，自动保存完整的执行上下文：

```python
@dataclass
class FailureSnapshot:
    """失败现场快照"""
    task_id: str
    timestamp: str
    
    # 失败信息
    step_index: int
    error_code: str
    error_message: str
    
    # 浏览器现场
    page_url: str
    screenshot_path: str          # 失败时的截图
    dom_snapshot: str              # 失败时的 DOM
    console_logs: list[str]       # 浏览器控制台日志
    network_requests: list[dict]  # 网络请求记录
    
    # 执行上下文
    timeline: TaskTimeline        # 完整时间线
    variables: dict               # 任务变量的值
    llm_messages: list[dict]      # LLM 对话历史
    
    # Playwright Trace
    trace_path: str               # Trace 文件路径

async def capture_failure(page, ctx: ActionContext, error: Exception) -> FailureSnapshot:
    """捕获失败现场"""
    return FailureSnapshot(
        task_id=ctx.task_id,
        timestamp=datetime.utcnow().isoformat(),
        step_index=ctx.step_index,
        error_code=ErrorClassifier.classify(error)[0],
        error_message=str(error),
        page_url=page.url,
        screenshot_path=await _save_screenshot(page, ctx.task_id),
        dom_snapshot=await page.content(),
        console_logs=ctx.console_logs[-50:],   # 最近 50 条
        network_requests=ctx.network_log[-20:], # 最近 20 个请求
        timeline=ctx.timeline,
        variables=ctx.variables,
        llm_messages=ctx.llm_messages,
        trace_path=f"/app/traces/{ctx.task_id}.zip",
    )
```

#### 从快照重建现场

```python
async def replay_from_snapshot(snapshot: FailureSnapshot):
    """从快照重建执行环境，辅助调试"""
    print(f"=== 失败复现：任务 {snapshot.task_id} ===")
    print(f"失败步骤：#{snapshot.step_index}")
    print(f"错误码：{snapshot.error_code}")
    print(f"页面 URL：{snapshot.page_url}")
    print(f"错误信息：{snapshot.error_message}")
    print(f"\n--- 时间线（最后 5 步）---")
    for step in snapshot.timeline.steps[-5:]:
        status = "✅" if step.success else "❌"
        print(f"  #{step.index} {status} {step.tool_name} ({step.duration_ms}ms)")
    print(f"\n--- 网络请求（最后 5 个）---")
    for req in snapshot.network_requests[-5:]:
        print(f"  {req['method']} {req['url']} → {req['status']}")
    print(f"\n截图：{snapshot.screenshot_path}")
    print(f"Trace：{snapshot.trace_path}")
    print(f"  打开方式：playwright show-trace {snapshot.trace_path}")
```

> 💡 保存失败现场会占用存储空间。建议：保留最近 7 天的失败快照，更早的自动清理；对于高频失败（相同 error_code + 相同 step），只保留最近 3 个快照。

### 8.5 监控告警：成功率、延迟 P99、Token 消耗的大盘建设

日志和追踪解决「事后排查」，监控大盘解决「实时感知」——在问题发生的第一时间发现异常。

#### 核心指标体系

| 类别 | 指标 | 含义 | 告警阈值 |
| :--- | :--- | :--- | :--- |
| **成功率** | task_success_rate | 任务成功率 | < 90% → P1 告警 |
| **成功率** | step_success_rate | 步骤成功率 | < 95% → P2 告警 |
| **延迟** | task_duration_p50 | 任务耗时中位数 | > 60s → 通知 |
| **延迟** | task_duration_p99 | 任务耗时 99 分位 | > 300s → P2 告警 |
| **延迟** | llm_latency_p99 | LLM 调用延迟 99 分位 | > 10s → P2 告警 |
| **资源** | token_consumption | Token 消耗速率 | > 预算 120% → P1 告警 |
| **资源** | active_contexts | 活跃 Context 数 | > Worker 容量 90% → 通知 |
| **资源** | memory_usage_mb | 内存使用量 | > 阈值 80% → P2 告警 |
| **可用性** | worker_healthy_count | 健康 Worker 数 | < 2 → P0 告警 |

#### Prometheus 指标埋点

```python
from prometheus_client import Counter, Histogram, Gauge

# 计数器
task_total = Counter("agent_tasks_total", "总任务数", ["status", "template"])
step_total = Counter("agent_steps_total", "总步骤数", ["tool", "status", "error_code"])
token_consumed = Counter("agent_tokens_total", "Token 消耗", ["model", "type"])

# 直方图（延迟分布）
task_duration = Histogram(
    "agent_task_duration_seconds", "任务耗时",
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)
llm_latency = Histogram(
    "agent_llm_latency_seconds", "LLM 调用延迟",
    buckets=[0.5, 1, 2, 5, 10, 20]
)

# 仪表盘（实时值）
active_tasks = Gauge("agent_active_tasks", "当前执行中的任务数")
active_contexts = Gauge("agent_active_contexts", "活跃 Context 数")

# 在关键位置埋点
async def monitored_step(action: BaseAction, ctx: ActionContext):
    with task_duration.time():
        result = await action.run(ctx)
    
    step_total.labels(
        tool=action.name,
        status="success" if result.success else "failure",
        error_code=result.error_code or "none",
    ).inc()
    
    return result
```

#### 告警规则示例（Prometheus AlertManager）

```yaml
groups:
  - name: browser_agent_alerts
    rules:
      - alert: TaskSuccessRateLow
        expr: |
          rate(agent_tasks_total{status="success"}[5m]) 
          / rate(agent_tasks_total[5m]) < 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "任务成功率低于 90%"
          
      - alert: HighTokenConsumption
        expr: rate(agent_tokens_total[1h]) > 100000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Token 消耗速率异常（>10万/小时）"
```

> 💡 **第 8 章小结**：可观测性让 Agent 系统从「黑盒」变成「透明盒」。结构化日志让每条操作都可查询，时间线让执行过程可视化，Trace 关联让 LLM + Playwright 的完整链路一目了然，失败快照让问题可复现，监控大盘让异常可实时感知。这些能力合在一起，构成了一个「出了问题能在 5 分钟内定位原因」的工程基础。

---

## 9. 工程基础能力：数据库、网络、Linux 运维

前面 8 章聚焦于 Agent 系统本身的架构设计。但一个跑在生产环境的系统不是悬浮在空中的——它需要数据库存储任务状态、需要网络层管理代理和 Cookie、需要 Linux 运维保障进程稳定运行。这些「基础设施能力」虽然不是 Agent 独有的，但在浏览器自动化场景下有其独特的考量。

本章不是「数据库入门教程」或「Linux 命令速查」——你可以在任何地方找到这些。本章聚焦于：**这些基础能力在浏览器 Agent 系统中怎么用、有什么特殊设计。**

### 9.1 数据库基础：任务表设计、索引优化、Redis 状态管理

浏览器 Agent 系统的数据持久化需求可以分为两类：**关系型数据**（任务定义、执行记录、审计日志）和**热状态数据**（任务进度、锁、队列、检查点）。前者用 PostgreSQL/MySQL，后者用 Redis。

#### 任务表设计

任务系统的核心是一张 `tasks` 表。设计这张表时，需要考虑任务生命周期的所有状态：

```sql
CREATE TABLE tasks (
    -- 主键与标识
    id            VARCHAR(36) PRIMARY KEY,    -- UUID
    template_id   VARCHAR(64) NOT NULL,       -- 关联的任务模板
    
    -- 任务状态机
    status        VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending → queued → running → completed / failed / cancelled
    
    -- 输入参数（JSON 格式，支持任意模板参数）
    params        JSONB NOT NULL,             -- {"url": "...", "account": "..."}
    
    -- 执行信息
    worker_id     VARCHAR(64),                -- 执行该任务的 Worker
    started_at    TIMESTAMP,                  -- 开始执行时间
    completed_at  TIMESTAMP,                  -- 完成时间
    
    -- 结果
    result        JSONB,                      -- 成功时的结果数据
    error_code    VARCHAR(32),                -- 失败时的错误码
    error_message TEXT,                        -- 失败时的错误信息
    
    -- 重试
    retry_count   INT NOT NULL DEFAULT 0,     -- 已重试次数
    max_retries   INT NOT NULL DEFAULT 3,     -- 最大重试次数
    
    -- 检查点（断点续跑）
    checkpoint    JSONB,                      -- 最新检查点数据
    last_step     INT,                        -- 最后完成的步骤索引
    
    -- 元数据
    priority      INT NOT NULL DEFAULT 0,     -- 优先级（越大越先执行）
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- 租户隔离
    tenant_id     VARCHAR(64) NOT NULL        -- 多租户标识
);
```

> 💡 `params` 和 `result` 使用 JSONB 类型而非拆成多列。原因：不同模板的参数结构不同，用固定列无法适配。JSONB 既灵活又支持索引查询（GIN 索引）。

#### 索引策略

索引直接决定查询性能。根据浏览器 Agent 系统的查询模式，需要以下索引：

```sql
-- 1. 调度查询：找出等待执行的任务（最频繁的查询）
CREATE INDEX idx_tasks_scheduling 
  ON tasks (status, priority DESC, created_at ASC)
  WHERE status IN ('pending', 'queued');

-- 2. Worker 查询：某个 Worker 上正在执行的任务
CREATE INDEX idx_tasks_worker 
  ON tasks (worker_id, status)
  WHERE status = 'running';

-- 3. 租户查询：某个租户的所有任务
CREATE INDEX idx_tasks_tenant 
  ON tasks (tenant_id, created_at DESC);

-- 4. 失败分析：查找特定错误码的失败任务
CREATE INDEX idx_tasks_failures 
  ON tasks (error_code, created_at DESC)
  WHERE status = 'failed';

-- 5. 模板统计：按模板统计成功率
CREATE INDEX idx_tasks_template_status 
  ON tasks (template_id, status);
```

| 查询场景 | SQL | 使用的索引 |
| :--- | :--- | :--- |
| 取下一批待执行任务 | `WHERE status='pending' ORDER BY priority DESC, created_at LIMIT 10` | idx_tasks_scheduling |
| Worker 心跳上报活跃任务 | `WHERE worker_id='w-001' AND status='running'` | idx_tasks_worker |
| 用户查看自己的任务 | `WHERE tenant_id='user_123' ORDER BY created_at DESC` | idx_tasks_tenant |
| 排查 ELEMENT_NOT_FOUND 错误 | `WHERE error_code='ELEMENT_NOT_FOUND' AND status='failed'` | idx_tasks_failures |

> 💡 **部分索引**（`WHERE` 子句）是关键优化。`tasks` 表中 90% 的行是已完成的——完整索引会包含大量无用数据。部分索引只索引需要查询的子集，体积小、更新快。

#### 执行记录表

除了任务主表，还需要一张记录每一步执行细节的 `task_steps` 表：

```sql
CREATE TABLE task_steps (
    id           BIGSERIAL PRIMARY KEY,
    task_id      VARCHAR(36) NOT NULL REFERENCES tasks(id),
    step_index   INT NOT NULL,
    
    tool_name    VARCHAR(64) NOT NULL,
    params       JSONB NOT NULL,
    
    success      BOOLEAN NOT NULL,
    result_data  JSONB,
    error_code   VARCHAR(32),
    error_message TEXT,
    
    duration_ms  INT NOT NULL,
    retry_count  INT NOT NULL DEFAULT 0,
    
    page_url     TEXT,
    screenshot_key VARCHAR(256),
    
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE (task_id, step_index)  -- 同一任务的步骤索引唯一
);

-- 查询某个任务的完整时间线
CREATE INDEX idx_steps_task ON task_steps (task_id, step_index);

-- 按工具名统计错误率
CREATE INDEX idx_steps_tool_errors 
  ON task_steps (tool_name, error_code)
  WHERE success = FALSE;
```

#### Redis 状态管理

Redis 在 Agent 系统中承担三个角色：**实时状态存储**、**分布式锁**、**消息队列**。

```
┌──────────────────────────────────────────────────────┐
│              Redis 在 Agent 系统中的角色               │
├──────────────────────────────────────────────────────┤
│                                                      │
│  角色 1：实时状态                                      │
│  ── worker:{id}:status → Hash（负载、内存、心跳时间）   │
│  ── task:{id}:progress → String（当前步骤 / 总步骤）    │
│  ── task:{id}:checkpoint → Hash（检查点数据）          │
│                                                      │
│  角色 2：分布式锁（第 7 章已介绍）                       │
│  ── task_lock:{id} → String（持有者 Worker ID，TTL）   │
│                                                      │
│  角色 3：任务队列                                      │
│  ── queue:pending → Sorted Set（score=优先级）         │
│  ── queue:delayed → Sorted Set（score=执行时间戳）     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**实时状态管理**的实现：

```python
class RedisStateManager:
    """基于 Redis 的任务实时状态管理"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def update_worker_status(self, worker_id: str, status: dict):
        """更新 Worker 状态（Hash 结构，支持部分更新）"""
        key = f"worker:{worker_id}:status"
        await self.redis.hset(key, mapping={
            "load": status["current_load"],
            "memory_mb": status["memory_mb"],
            "cpu_percent": status["cpu_percent"],
            "heartbeat": datetime.utcnow().isoformat(),
        })
        await self.redis.expire(key, 120)  # 2 分钟过期（比心跳间隔长）
    
    async def save_checkpoint(self, task_id: str, checkpoint: dict):
        """保存检查点到 Redis（快速读写，不经过 DB）"""
        key = f"task:{task_id}:checkpoint"
        await self.redis.set(key, json.dumps(checkpoint), ex=86400)  # 24h 过期
    
    async def restore_checkpoint(self, task_id: str) -> dict | None:
        """恢复检查点"""
        key = f"task:{task_id}:checkpoint"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
```

**优先级任务队列**的实现：

```python
class RedisPriorityQueue:
    """基于 Sorted Set 的优先级任务队列"""
    
    def __init__(self, redis_client, queue_name: str = "queue:pending"):
        self.redis = redis_client
        self.queue_name = queue_name
    
    async def enqueue(self, task_id: str, priority: int = 0):
        """入队（priority 越大越先执行）"""
        # Sorted Set 的 score 用负数，因为 ZPOPMIN 取最小值
        await self.redis.zadd(self.queue_name, {task_id: -priority})
    
    async def dequeue(self, count: int = 1) -> list[str]:
        """出队（取优先级最高的 N 个任务）"""
        # ZPOPMIN 原子操作，取出并删除，避免重复消费
        items = await self.redis.zpopmin(self.queue_name, count)
        return [task_id for task_id, _ in items]
    
    async def queue_length(self) -> int:
        return await self.redis.zcard(self.queue_name)
```

> 💡 **PostgreSQL vs Redis 的分工原则**：写入后需要持久化 → PostgreSQL；需要高频读写且可容忍丢失 → Redis。检查点数据写 Redis（快），同时异步备份到 PostgreSQL（持久化）。两者配合，兼顾性能和可靠性。

### 9.2 HTTP 与网络：请求/响应结构、代理机制、Cookie/Session 管理

浏览器 Agent 的每一步操作背后都是 HTTP 请求。理解网络层的工作原理，是调试「页面加载失败」「被目标网站封禁」「登录态丢失」这些问题的基础。

#### 代理机制：为什么需要代理、如何管理代理池

浏览器 Agent 大规模运行时，用单个 IP 地址发起大量请求，会被目标网站的反爬系统识别和封禁。代理（Proxy）通过在 Agent 和目标网站之间增加一层中转，隐藏真实 IP。

```
Agent（真实 IP: 1.2.3.4）
    │
    ▼
代理服务器（IP: 5.6.7.8）
    │
    ▼
目标网站看到的请求 IP: 5.6.7.8
```

代理的类型和选择：

| 类型 | 原理 | 成本 | 匿名性 | 适用场景 |
| :--- | :--- | :--- | :--- | :--- |
| **数据中心代理** | 托管在云服务器上 | 💰 低 | ⭐⭐ 中 | 非敏感页面的批量抓取 |
| **住宅代理** | 使用真实家庭 IP | 💰💰💰 高 | ⭐⭐⭐ 高 | 需要模拟真实用户的场景 |
| **移动代理** | 使用移动运营商 IP | 💰💰💰💰 极高 | ⭐⭐⭐ 高 | 最严格的反爬检测 |
| **轮换代理** | 每次请求自动更换 IP | 💰💰 中 | ⭐⭐⭐ 高 | 高频请求、防封禁 |

在 Playwright 中配置代理：

```python
# 方式 1：Browser 级别代理（所有 Context 共享）
browser = await playwright.chromium.launch(
    proxy={"server": "http://proxy.example.com:8080"}
)

# 方式 2：Context 级别代理（每个任务独立代理）
context = await browser.new_context(
    proxy={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass",
    }
)
```

> 💡 **推荐 Context 级别代理**：每个任务使用不同的代理，一个代理被封禁不影响其他任务。配合第 7 章的亲和性调度，同一域名的任务使用同一组代理，减少 IP 切换带来的风险指纹。

#### 代理池管理

生产环境中需要管理一个代理池，实现自动轮换和故障摘除：

```python
class ProxyPool:
    """代理池：自动轮换、健康检查、故障摘除"""
    
    def __init__(self, proxies: list[str]):
        self.healthy: list[str] = list(proxies)
        self.unhealthy: dict[str, float] = {}   # proxy → 失败时间
        self._lock = asyncio.Lock()
    
    async def get_proxy(self) -> str:
        """获取一个可用代理（轮换策略）"""
        async with self._lock:
            if not self.healthy:
                # 尝试恢复部分不健康的代理
                await self._recover_proxies()
            if not self.healthy:
                raise RuntimeError("代理池耗尽")
            # 轮换：取第一个，放到末尾
            proxy = self.healthy.pop(0)
            self.healthy.append(proxy)
            return proxy
    
    async def mark_failed(self, proxy: str):
        """标记代理失败"""
        async with self._lock:
            if proxy in self.healthy:
                self.healthy.remove(proxy)
            self.unhealthy[proxy] = time.monotonic()
    
    async def _recover_proxies(self):
        """恢复超过冷却期的代理"""
        cooldown = 300  # 5 分钟冷却
        now = time.monotonic()
        recovered = [
            p for p, t in self.unhealthy.items()
            if now - t > cooldown
        ]
        for p in recovered:
            self.healthy.append(p)
            del self.unhealthy[p]
```

#### Cookie 与 Session 管理

Cookie 是浏览器维持登录态的核心机制。在 Agent 系统中，Cookie 管理需要解决两个问题：**持久化**（任务间共享登录态）和**隔离**（不同用户的 Cookie 不能混淆）。

Playwright 的 Context 天然实现了 Cookie 隔离——不同 Context 的 Cookie 互不可见。但 Context 关闭后 Cookie 就丢失了。需要手动持久化：

```python
class CookieManager:
    """Cookie 持久化管理"""
    
    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_cookies(self, context: BrowserContext, account_id: str):
        """保存 Context 的 Cookie 到文件"""
        cookies = await context.cookies()
        path = self.storage_dir / f"{account_id}.json"
        path.write_text(json.dumps(cookies, indent=2))
    
    async def load_cookies(self, context: BrowserContext, account_id: str) -> bool:
        """从文件加载 Cookie 到 Context"""
        path = self.storage_dir / f"{account_id}.json"
        if not path.exists():
            return False
        cookies = json.loads(path.read_text())
        # 过滤过期的 Cookie
        now = time.time()
        valid_cookies = [
            c for c in cookies
            if c.get("expires", float("inf")) > now
        ]
        await context.add_cookies(valid_cookies)
        return len(valid_cookies) > 0
    
    async def clear_cookies(self, account_id: str):
        """清除指定账号的 Cookie"""
        path = self.storage_dir / f"{account_id}.json"
        if path.exists():
            path.unlink()
```

更高级的方式是使用 Playwright 的 **Storage State**，它不仅保存 Cookie，还保存 localStorage：

```python
# 保存完整的浏览器状态（Cookie + localStorage）
storage = await context.storage_state()
Path("state.json").write_text(json.dumps(storage))

# 从状态恢复一个新 Context
context = await browser.new_context(storage_state="state.json")
```

#### Session 过期检测与自动恢复

Agent 执行长任务时，Session 可能中途过期。需要检测并自动恢复：

```python
class SessionMonitor:
    """Session 过期检测"""
    
    def __init__(self, login_indicators: list[str]):
        # 登录态标志：页面上存在这些元素说明已登录
        self.login_indicators = login_indicators
    
    async def is_logged_in(self, page) -> bool:
        """检查当前页面是否处于登录状态"""
        for selector in self.login_indicators:
            try:
                element = await page.query_selector(selector)
                if element:
                    return True
            except Exception:
                continue
        return False
    
    async def check_and_recover(self, page, login_fn) -> bool:
        """检查登录态，如果过期则自动重新登录"""
        if await self.is_logged_in(page):
            return True
        # Session 过期，执行重新登录
        return await login_fn(page)

# 使用方式
session_monitor = SessionMonitor(
    login_indicators=["#user-avatar", ".account-menu", "[data-user-id]"]
)

# 在每个关键步骤前检查登录态
if not await session_monitor.check_and_recover(page, auto_login):
    raise SessionExpiredError("重新登录失败")
```

> 💡 **Cookie 安全提醒**：Cookie 文件等同于登录凭证，必须加密存储。生产环境中建议将 Cookie 加密后存入数据库或密钥管理服务（如 AWS Secrets Manager），而非明文文件。

### 9.3 Linux 运维：进程管理、日志查看、容器化部署

浏览器 Agent 系统通常部署在 Linux 服务器上。与普通 Web 服务不同，它有一个特殊的运维挑战：**每个任务都会启动一个真实的浏览器进程**。浏览器是出了名的资源消耗大户——内存泄漏、僵尸进程、GPU 驱动崩溃都是家常便饭。

#### 进程管理：浏览器进程的生命周期

Playwright 启动的 Chromium 进程树比你想象的复杂：

```
playwright (主进程)
  └── chromium (Browser 进程)
        ├── chromium --type=gpu-process     (GPU 渲染)
        ├── chromium --type=utility         (网络服务)
        ├── chromium --type=renderer (Tab 1) (渲染进程)
        ├── chromium --type=renderer (Tab 2)
        └── chromium --type=renderer (Tab 3)
```

一个 Browser 实例可能产生 5-20 个子进程。如果主进程异常退出，这些子进程会变成**孤儿进程**，继续占用内存和 CPU。

**僵尸进程清理脚本**：

```bash
#!/bin/bash
# cleanup_zombie_browsers.sh
# 定时执行，清理无主的 chromium 进程

# 找出所有 chromium 进程
CHROME_PIDS=$(pgrep -f "chromium|chrome" | tr '\n' ' ')

for PID in $CHROME_PIDS; do
    # 检查父进程是否还存活
    PPID=$(ps -o ppid= -p $PID 2>/dev/null | tr -d ' ')
    if [ -z "$PPID" ] || [ "$PPID" = "1" ]; then
        # 父进程已死（PPID=1 说明被 init 收养）
        RUNTIME=$(ps -o etimes= -p $PID 2>/dev/null | tr -d ' ')
        if [ -n "$RUNTIME" ] && [ "$RUNTIME" -gt 600 ]; then
            # 运行超过 10 分钟的孤儿进程，kill
            echo "[$(date)] Killing orphan chromium PID=$PID (runtime=${RUNTIME}s)"
            kill -TERM $PID
            sleep 5
            kill -KILL $PID 2>/dev/null  # 确保杀死
        fi
    fi
done
```

在 Python 层面，确保浏览器资源被正确释放：

```python
class BrowserLifecycle:
    """浏览器进程生命周期管理"""
    
    def __init__(self):
        self.browser = None
        self._browser_pid = None
    
    async def start(self):
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",              # 无头环境不需要 GPU
                "--disable-dev-shm-usage",    # 避免 /dev/shm 空间不足
                "--no-sandbox",               # 容器环境必须
                "--disable-setuid-sandbox",
                "--single-process",           # 减少进程数（可选）
            ]
        )
        # 记录浏览器主进程 PID
        self._browser_pid = self.browser.process.pid
    
    async def shutdown(self):
        """确保浏览器完全关闭"""
        if self.browser:
            try:
                await asyncio.wait_for(self.browser.close(), timeout=10)
            except (asyncio.TimeoutError, Exception):
                # 强制杀死
                if self._browser_pid:
                    os.killpg(os.getpgid(self._browser_pid), signal.SIGKILL)
```

> 💡 `--disable-dev-shm-usage` 是容器环境中最常见的坑。Docker 默认的 `/dev/shm` 只有 64MB，Chromium 渲染大页面时会超出限制导致崩溃。这个参数让 Chromium 用 `/tmp` 代替。

#### 日志管理：结构化日志的落盘与查询

第 8 章设计了结构化日志格式，在运维层面需要解决「日志写到哪、保留多久、怎么查」。

```
┌──────────────────────────────────────────────────┐
│              日志管理流水线                        │
├──────────────────────────────────────────────────┤
│                                                  │
│  应用进程                                         │
│    │ stdout（JSON 格式）                          │
│    ▼                                              │
│  容器运行时（Docker / containerd）                  │
│    │ 自动捕获 stdout/stderr                       │
│    ▼                                              │
│  日志采集器（Filebeat / Fluentd / Vector）          │
│    │ 解析 JSON、添加元数据（Pod名、节点名）          │
│    ▼                                              │
│  日志存储（Elasticsearch / Loki / ClickHouse）     │
│    │                                              │
│    ▼                                              │
│  查询界面（Kibana / Grafana）                      │
│                                                  │
└──────────────────────────────────────────────────┘
```

**日志轮转配置**（防止磁盘写满）：

```json
// Docker daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
```

**实用的日志查询命令**（生产环境排查问题的高频操作）：

```bash
# 查看某个任务的完整日志
docker logs browser-worker-1 2>&1 | jq 'select(.task_id == "t_abc123")'

# 查看最近 10 分钟的所有错误
docker logs --since 10m browser-worker-1 2>&1 | jq 'select(.success == false)'

# 统计各错误码的出现次数
docker logs browser-worker-1 2>&1 | \
  jq -r 'select(.error_code != null) | .error_code' | \
  sort | uniq -c | sort -rn

# 查看某个 Worker 的内存使用趋势
docker stats --no-stream --format "{{.MemUsage}}" browser-worker-1
```

#### 容器化部署：Dockerfile 与资源限制

浏览器 Agent 的 Dockerfile 需要特别注意：**安装浏览器依赖**和**设置合理的资源限制**。

```dockerfile
# 多阶段构建：减小镜像体积
FROM python:3.11-slim AS base

# 安装 Chromium 运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chromium 依赖的系统库
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 \
    libasound2 libxshmfence1 \
    # 字体（中文网站必须）
    fonts-noto-cjk fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
RUN playwright install chromium

# 复制应用代码
COPY . .

# 非 root 用户运行（安全最佳实践）
RUN useradd -m -s /bin/bash agent
USER agent

CMD ["python", "-m", "worker.main"]
```

**Docker Compose 资源限制**：

```yaml
# docker-compose.yml
services:
  browser-worker:
    build: .
    deploy:
      resources:
        limits:
          memory: 4G          # 硬限制：最多 4GB
          cpus: "2.0"         # 最多 2 核
        reservations:
          memory: 2G          # 预留：至少 2GB
          cpus: "1.0"
      replicas: 3             # 启动 3 个 Worker 实例
    
    # 增大共享内存（Chromium 必须）
    shm_size: "512m"
    
    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s
    
    # 重启策略
    restart: unless-stopped
    
    environment:
      - ORCHESTRATOR_URL=http://orchestrator:8080
      - REDIS_URL=redis://redis:6379
      - DB_URL=postgresql://agent:pass@postgres:5432/agent_db
      - MAX_CONCURRENT_TASKS=10
```

#### 资源监控与自动恢复

在容器环境中，设置 OOM 和异常退出的自动恢复：

```python
import resource

def set_resource_limits():
    """设置进程级资源限制（防御最后一道防线）"""
    # 限制虚拟内存（4GB）
    max_memory = 4 * 1024 * 1024 * 1024  # 4GB
    resource.setrlimit(resource.RLIMIT_AS, (max_memory, max_memory))
    
    # 限制打开的文件描述符数（每个 Tab 消耗 ~10 个 fd）
    resource.setrlimit(resource.RLIMIT_NOFILE, (4096, 4096))

class MemoryWatchdog:
    """内存看门狗：在 OOM 之前主动清理"""
    
    def __init__(self, threshold_mb: int = 3500):
        self.threshold = threshold_mb * 1024 * 1024
    
    async def start(self, browser_mgr):
        while True:
            mem = psutil.Process().memory_info().rss
            if mem > self.threshold:
                # 内存接近上限，主动关闭最老的 Context
                oldest = browser_mgr.get_oldest_context()
                if oldest:
                    await browser_mgr.force_close(oldest)
                    logger.warning(f"内存预警：{mem // 1024 // 1024}MB，"
                                   f"已关闭最老的 Context")
            await asyncio.sleep(10)
```

> 💡 **第 9 章小结**：工程基础能力是让 Agent 系统「落地」的最后一公里。PostgreSQL 存储任务和执行记录，Redis 管理实时状态和队列，代理池和 Cookie 管理解决网络层问题，Linux 运维确保进程稳定和资源可控。这些基础能力虽然不如 Agent 架构那样「炫酷」，但缺了任何一个，系统都无法在生产环境存活。

---

## 10. 实战：从零搭建一个生产级浏览器 Agent 平台

前 9 章分别讲了工具层、任务引擎、上下文管理、执行层、调度层、编排层、可观测性和工程基础。每一章都是独立的「零件」。本章的目标是：**把所有零件组装成一台完整的机器**。

我们将从零搭建一个名为 **BrowserForge** 的浏览器 Agent 平台，它支持：多任务并行执行、断点续跑、代理轮换、结构化日志、Prometheus 监控，并以 Docker Compose 一键部署。

> 💡 本章不会重复前 9 章的理论。每个子章节会直接给出「落地代码」，并标注「这对应前面第 N 章的哪个设计」。如果某段代码看不懂，回去翻对应章节。

### 10.1 项目架构与技术选型

#### 系统全景架构

```
                        ┌─────────────┐
                        │  API Server  │
                        │  (FastAPI)   │
                        └──────┬──────┘
                               │ 提交任务 / 查询结果
                               ▼
┌─────────────────────────────────────────────────────┐
│                    Orchestrator                      │
│                                                     │
│  · 任务队列（Redis Sorted Set）                      │
│  · Worker 注册 + 健康检查                            │
│  · 任务分发（负载感知 + 亲和性）                      │
│  · 结果聚合 + 失败重试                               │
└───────┬──────────────┬──────────────┬───────────────┘
        │              │              │
        ▼              ▼              ▼
  ┌───────────┐  ┌───────────┐  ┌───────────┐
  │  Worker 1  │  │  Worker 2  │  │  Worker N  │
  │            │  │            │  │            │
  │  MCP Server│  │  MCP Server│  │  MCP Server│
  │  Playwright│  │  Playwright│  │  Playwright│
  │  动作库    │  │  动作库    │  │  动作库    │
  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
        │              │              │
        ▼              ▼              ▼
  ┌─────────────────────────────────────────┐
  │         基础设施层                        │
  │  PostgreSQL │ Redis │ Prometheus │ Loki  │
  └─────────────────────────────────────────┘
```

#### 技术选型决策

| 层 | 技术 | 选型理由 |
| :--- | :--- | :--- |
| **API 层** | FastAPI | 异步原生、自动生成 OpenAPI 文档、Pydantic 校验 |
| **编排器** | 自研 Python 服务 | Agent 调度逻辑复杂且定制性强，通用编排器（Airflow/Temporal）过重 |
| **执行器** | Playwright (Python) | 跨浏览器支持、原生 async、Trace 录制、社区活跃 |
| **任务队列** | Redis Sorted Set | 支持优先级、原子出队（ZPOPMIN）、延迟任务（score=时间戳） |
| **持久化** | PostgreSQL + JSONB | 任务参数结构多变，JSONB 灵活且支持 GIN 索引 |
| **缓存/锁** | Redis | 检查点快速存取、分布式任务锁（SET NX） |
| **监控** | Prometheus + Grafana | 行业标准、Pull 模式适合容器环境、Grafana 大盘开箱即用 |
| **日志** | 结构化 JSON → Loki | 轻量级日志聚合、与 Grafana 原生集成、LogQL 查询 |
| **容器化** | Docker Compose | 单机多服务编排，开发/测试/小规模生产通用 |

#### 项目目录结构

```
browserforge/
├── docker-compose.yml          # 一键部署
├── .env                        # 环境变量（密钥、配置）
├── requirements.txt            # Python 依赖
│
├── shared/                     # 共享模块（Orchestrator 和 Worker 都用）
│   ├── __init__.py
│   ├── models.py               # 数据模型（Task, StepRecord, etc.）
│   ├── config.py               # 配置管理
│   ├── db.py                   # PostgreSQL 连接与操作
│   └── redis_client.py         # Redis 连接与操作
│
├── orchestrator/               # 编排器
│   ├── __init__.py
│   ├── main.py                 # FastAPI 入口
│   ├── scheduler.py            # 任务调度逻辑
│   ├── health_checker.py       # Worker 健康检查
│   └── result_aggregator.py    # 结果聚合
│
├── worker/                     # 执行器
│   ├── __init__.py
│   ├── main.py                 # Worker 入口
│   ├── mcp_server.py           # MCP 工具层
│   ├── actions/                # 原子动作库
│   │   ├── __init__.py
│   │   ├── base.py             # BaseAction 基类
│   │   ├── navigate.py         # 导航动作
│   │   ├── click.py            # 点击动作
│   │   ├── fill.py             # 填写动作
│   │   └── screenshot.py       # 截图动作
│   ├── browser_manager.py      # 浏览器生命周期管理
│   ├── context_manager.py      # 上下文窗口管理
│   ├── proxy_pool.py           # 代理池
│   └── cookie_manager.py       # Cookie 持久化
│
├── templates/                  # 任务模板
│   └── ecommerce_order.json    # 示例：电商下单模板
│
├── observability/              # 可观测性
│   ├── logger.py               # 结构化日志
│   ├── metrics.py              # Prometheus 指标
│   └── tracer.py               # Trace 追踪
│
├── migrations/                 # 数据库迁移
│   └── 001_init.sql            # 初始建表
│
└── scripts/                    # 运维脚本
    ├── cleanup_zombies.sh      # 僵尸进程清理
    └── health_check.sh         # 健康检查
```

#### 核心数据模型

```python
# shared/models.py
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class TaskStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    template_id: str
    params: dict
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    tenant_id: str = ""
    worker_id: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    last_step: int | None = None
    checkpoint: dict | None = None
    result: dict | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class StepRecord:
    task_id: str
    step_index: int
    tool_name: str
    params: dict
    success: bool
    duration_ms: int
    result_data: dict | None = None
    error_code: str | None = None
    page_url: str | None = None
    screenshot_key: str | None = None
```

> 💡 这些数据模型贯穿整个系统——Orchestrator 用它们管理任务生命周期，Worker 用它们记录执行细节，可观测性层用它们生成日志和指标。定义一次，复用到底。

### 10.2 实现 MCP Server + 原子动作库

这一节把第 2 章的 MCP 设计和第 3 章的任务引擎落地为可运行的代码。

#### MCP 工具注册表

```python
# worker/mcp_server.py
"""MCP Server：Agent 调用浏览器工具的统一入口"""

from dataclasses import dataclass
from functools import wraps
import json, time, asyncio

@dataclass
class ToolResult:
    success: bool
    data: dict | None = None
    error: str | None = None
    error_code: str | None = None
    page_url: str | None = None

class MCPServer:
    """MCP 工具服务器（对应第 2 章）"""
    
    def __init__(self, browser_mgr, logger, metrics):
        self.browser_mgr = browser_mgr
        self.logger = logger
        self.metrics = metrics
        self.tools: dict[str, callable] = {}
        self._register_tools()
    
    def _register_tools(self):
        """注册所有浏览器工具"""
        self.tools = {
            "browser_navigate": self._navigate,
            "browser_click":     self._click,
            "browser_fill":      self._fill,
            "browser_screenshot": self._screenshot,
            "browser_get_text":  self._get_text,
            "browser_scroll":    self._scroll,
        }
    
    async def execute(self, tool_name: str, params: dict,
                      ctx: "ActionContext") -> ToolResult:
        """统一的工具执行入口（校验 → 限流 → 执行 → 日志）"""
        start = time.monotonic()
        
        # 1. 校验工具是否存在
        tool_fn = self.tools.get(tool_name)
        if not tool_fn:
            return ToolResult(
                success=False, error=f"未知工具: {tool_name}",
                error_code="UNKNOWN_TOOL"
            )
        
        # 2. 输入验证（对应第 2.2 节）
        validation_error = self._validate(tool_name, params)
        if validation_error:
            return validation_error
        
        # 3. 执行
        try:
            result = await asyncio.wait_for(
                tool_fn(ctx.page, **params), timeout=15
            )
        except asyncio.TimeoutError:
            result = ToolResult(
                success=False, error="执行超时（15s）",
                error_code="TIMEOUT"
            )
        except Exception as e:
            result = ToolResult(
                success=False, error=str(e),
                error_code="EXECUTION_ERROR"
            )
        
        # 4. 记录日志和指标
        duration_ms = int((time.monotonic() - start) * 1000)
        self.logger.log_tool_call(
            task_id=ctx.task_id, step=ctx.step_index,
            tool=tool_name, params=params,
            success=result.success, error_code=result.error_code,
            duration_ms=duration_ms
        )
        self.metrics.record_step(tool_name, result.success, 
                                  result.error_code, duration_ms)
        
        return result
    
    def _validate(self, tool_name: str, params: dict) -> ToolResult | None:
        """输入验证（对应第 2.2 节）"""
        if "url" in params:
            url = params["url"]
            if not url.startswith(("http://", "https://")):
                return ToolResult(
                    success=False,
                    error=f"不支持的 URL 协议: {url}",
                    error_code="INVALID_URL"
                )
        if "selector" in params:
            sel = params["selector"]
            if "javascript:" in sel.lower():
                return ToolResult(
                    success=False,
                    error="选择器不允许包含 javascript:",
                    error_code="INVALID_SELECTOR"
                )
        return None  # 校验通过
    
    # ── 工具实现 ──
    
    async def _navigate(self, page, url: str, **kw) -> ToolResult:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return ToolResult(success=True, 
                          data={"url": page.url}, page_url=page.url)
    
    async def _click(self, page, selector: str, **kw) -> ToolResult:
        await page.click(selector, timeout=5000)
        await page.wait_for_timeout(kw.get("wait_after_ms", 1000))
        return ToolResult(success=True, page_url=page.url)
    
    async def _fill(self, page, selector: str, value: str, **kw) -> ToolResult:
        await page.fill(selector, "")       # 先清空（幂等，第 2.5 节）
        await page.fill(selector, value)
        return ToolResult(success=True, page_url=page.url)
    
    async def _screenshot(self, page, **kw) -> ToolResult:
        path = f"/app/screenshots/{int(time.time()*1000)}.png"
        await page.screenshot(path=path, full_page=kw.get("full_page", False))
        return ToolResult(success=True, data={"path": path}, page_url=page.url)
    
    async def _get_text(self, page, selector: str, **kw) -> ToolResult:
        element = await page.query_selector(selector)
        if not element:
            return ToolResult(success=False, error=f"元素 {selector} 不存在",
                              error_code="ELEMENT_NOT_FOUND")
        text = await element.inner_text()
        return ToolResult(success=True, data={"text": text}, page_url=page.url)
    
    async def _scroll(self, page, direction: str = "down", 
                      pixels: int = 500, **kw) -> ToolResult:
        delta = pixels if direction == "down" else -pixels
        await page.mouse.wheel(0, delta)
        await page.wait_for_timeout(500)
        return ToolResult(success=True, page_url=page.url)
```

#### 原子动作库：带重试和校验的动作封装

```python
# worker/actions/base.py
"""原子动作基类（对应第 3.1 节）"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ActionContext:
    page: object           # Playwright Page
    task_id: str
    step_index: int
    variables: dict        # 任务级变量（跨步骤共享）
    mcp: "MCPServer"       # MCP 工具服务器引用

class BaseAction(ABC):
    name: str = "base"
    max_retries: int = 3
    timeout_ms: int = 10000
    
    @abstractmethod
    async def execute(self, ctx: ActionContext) -> ToolResult:
        ...
    
    async def pre_check(self, ctx: ActionContext) -> bool:
        """前置检查：如果已完成则跳过"""
        return True
    
    async def run(self, ctx: ActionContext) -> ToolResult:
        if not await self.pre_check(ctx):
            return ToolResult(success=True, data={"skipped": True})
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = await asyncio.wait_for(
                    self.execute(ctx), timeout=self.timeout_ms / 1000
                )
                if result.success:
                    return result
                last_error = result.error
            except asyncio.TimeoutError:
                last_error = f"超时（{self.timeout_ms}ms）"
            except Exception as e:
                last_error = str(e)
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
        
        return ToolResult(success=False, error=last_error,
                          error_code="MAX_RETRIES_EXCEEDED")
```

```python
# worker/actions/navigate.py
"""导航动作：打开 URL 并等待页面就绪"""

class NavigateAction(BaseAction):
    name = "navigate"
    
    def __init__(self, url: str, wait_selector: str | None = None):
        self.url = url
        self.wait_selector = wait_selector
    
    async def pre_check(self, ctx: ActionContext) -> bool:
        # 幂等：如果已经在目标页面，跳过
        return ctx.page.url != self.url
    
    async def execute(self, ctx: ActionContext) -> ToolResult:
        result = await ctx.mcp.execute(
            "browser_navigate", {"url": self.url}, ctx
        )
        if result.success and self.wait_selector:
            await ctx.page.wait_for_selector(
                self.wait_selector, timeout=10000
            )
        return result
```

```python
# worker/actions/fill.py
"""表单填写动作：填值 + 验证"""

class FillAction(BaseAction):
    name = "fill"
    
    def __init__(self, selector: str, value: str, verify: bool = True):
        self.selector = selector
        self.value = value
        self.verify = verify
    
    async def execute(self, ctx: ActionContext) -> ToolResult:
        result = await ctx.mcp.execute(
            "browser_fill",
            {"selector": self.selector, "value": self.value}, ctx
        )
        # 后置校验：检查填入的值是否正确
        if result.success and self.verify:
            actual = await ctx.page.input_value(self.selector)
            if actual != self.value:
                return ToolResult(
                    success=False,
                    error=f"填写验证失败：期望 '{self.value}'，"
                          f"实际 '{actual}'",
                    error_code="FILL_VERIFY_FAILED"
                )
        return result
```

> 💡 注意 `FillAction` 的后置校验——这就是第 3 章强调的「动作不只是执行，还要验证」。没有这个校验，Agent 可能以为自己填好了表单，但实际上值被前端 JS 覆盖了。

### 10.3 实现 Orchestrator-Worker 调度器

这一节将第 6 章的并行调度和第 7 章的 Orchestrator-Worker 架构组装成完整的调度系统。

#### Orchestrator：API + 调度核心

```python
# orchestrator/main.py
"""编排器入口：FastAPI + 任务调度"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio, uuid

app = FastAPI(title="BrowserForge Orchestrator")

# 全局状态（生产环境应存 Redis）
workers: dict[str, WorkerInfo] = {}
orchestrator = None  # 启动时初始化

class TaskRequest(BaseModel):
    template_id: str
    params: dict
    priority: int = 0
    tenant_id: str = "default"

@app.on_event("startup")
async def startup():
    global orchestrator
    orchestrator = Orchestrator(
        redis_url="redis://redis:6379",
        db_url="postgresql://agent:pass@postgres:5432/agent_db"
    )
    await orchestrator.initialize()
    # 启动后台任务：健康检查 + 队列排空
    asyncio.create_task(orchestrator.health_check_loop())
    asyncio.create_task(orchestrator.dispatch_loop())

@app.post("/api/tasks")
async def submit_task(req: TaskRequest):
    task = Task(
        id=str(uuid.uuid4())[:8],
        template_id=req.template_id,
        params=req.params,
        priority=req.priority,
        tenant_id=req.tenant_id,
    )
    await orchestrator.submit(task)
    return {"task_id": task.id, "status": "queued"}

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    task = await orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    return task

@app.post("/api/workers/register")
async def register_worker(info: dict):
    await orchestrator.register_worker(info)
    return {"status": "registered"}

@app.post("/api/workers/heartbeat")
async def worker_heartbeat(hb: dict):
    await orchestrator.handle_heartbeat(hb)
    return {"status": "ok"}

@app.post("/api/tasks/{task_id}/result")
async def report_result(task_id: str, result: dict):
    await orchestrator.handle_result(task_id, result)
    return {"status": "received"}
```

#### Orchestrator 核心调度逻辑

```python
# orchestrator/scheduler.py
"""任务调度核心（对应第 7 章）"""

class Orchestrator:
    def __init__(self, redis_url: str, db_url: str):
        self.redis = None
        self.db = None
        self.workers: dict[str, WorkerInfo] = {}
        self.queue = None  # RedisPriorityQueue
    
    async def initialize(self):
        self.redis = await aioredis.from_url(self.redis_url)
        self.queue = RedisPriorityQueue(self.redis)
        # 初始化数据库连接...
    
    async def submit(self, task: Task):
        """提交任务到队列（对应第 9.1 节的优先级队列）"""
        # 1. 持久化到 PostgreSQL
        await self.db.insert_task(task)
        # 2. 入队到 Redis
        await self.queue.enqueue(task.id, task.priority)
    
    async def dispatch_loop(self):
        """调度循环：持续从队列取任务分发给 Worker"""
        while True:
            # 找到有空闲容量的 Worker
            available = [
                w for w in self.workers.values()
                if w.status == "healthy" 
                and w.current_load < w.max_capacity
            ]
            
            if not available:
                await asyncio.sleep(1)
                continue
            
            # 取出任务
            task_ids = await self.queue.dequeue(count=len(available))
            
            for task_id, worker in zip(task_ids, available):
                task = await self.db.get_task(task_id)
                if not task:
                    continue
                
                # 负载感知选择（对应第 7.3 节）
                best_worker = min(available, 
                    key=lambda w: w.current_load / w.max_capacity)
                
                # 分发
                await self._dispatch(best_worker, task)
            
            await asyncio.sleep(0.5)
    
    async def _dispatch(self, worker: WorkerInfo, task: Task):
        """将任务发送给 Worker"""
        task.status = TaskStatus.RUNNING
        task.worker_id = worker.worker_id
        await self.db.update_task(task)
        
        worker.current_load += 1
        
        # 通过 HTTP 发送任务给 Worker
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{worker.address}/api/execute",
                json={"task_id": task.id, "template_id": task.template_id,
                      "params": task.params,
                      "checkpoint": task.checkpoint},
                timeout=aiohttp.ClientTimeout(total=5)
            )
    
    async def health_check_loop(self):
        """定期检查 Worker 健康状态（对应第 7.2 节）"""
        while True:
            now = datetime.utcnow()
            for wid, worker in list(self.workers.items()):
                elapsed = (now - worker.last_heartbeat).total_seconds()
                if elapsed > 90:
                    # Worker 已死，触发故障转移
                    await self._failover(wid)
                elif elapsed > 30:
                    worker.status = "suspect"
            await asyncio.sleep(15)
    
    async def _failover(self, worker_id: str):
        """故障转移（对应第 7.5 节）"""
        orphaned = await self.db.get_running_tasks(worker_id)
        for task in orphaned:
            task.retry_count += 1
            if task.retry_count <= task.max_retries:
                task.status = TaskStatus.PENDING
                await self.db.update_task(task)
                await self.queue.enqueue(task.id, task.priority)
            else:
                task.status = TaskStatus.FAILED
                task.error_code = "WORKER_DEAD"
                await self.db.update_task(task)
        del self.workers[worker_id]
```

#### Worker：执行引擎

```python
# worker/main.py
"""Worker 入口：注册 → 心跳 → 执行任务"""

import asyncio, os, uuid
from fastapi import FastAPI

app = FastAPI(title="BrowserForge Worker")
worker_id = f"w-{uuid.uuid4().hex[:6]}"
orchestrator_url = os.environ["ORCHESTRATOR_URL"]

browser_mgr = None
mcp = None

@app.on_event("startup")
async def startup():
    global browser_mgr, mcp
    
    # 1. 启动浏览器
    browser_mgr = BrowserManager(max_contexts=10)
    await browser_mgr.start()
    
    # 2. 初始化 MCP Server
    mcp = MCPServer(browser_mgr, StructuredLogger(), PrometheusMetrics())
    
    # 3. 注册到 Orchestrator
    await register()
    
    # 4. 启动心跳
    asyncio.create_task(heartbeat_loop())

async def register():
    async with aiohttp.ClientSession() as session:
        await session.post(f"{orchestrator_url}/api/workers/register", json={
            "worker_id": worker_id,
            "address": f"http://{os.environ.get('HOSTNAME', 'localhost')}:8080",
            "max_capacity": 10,
        })

async def heartbeat_loop():
    """每 15 秒上报心跳（对应第 7.2 节）"""
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{orchestrator_url}/api/workers/heartbeat",
                    json={
                        "worker_id": worker_id,
                        "current_load": browser_mgr.active_count,
                        "memory_mb": psutil.Process().memory_info().rss 
                                     // 1024 // 1024,
                    }, timeout=aiohttp.ClientTimeout(total=5)
                )
        except Exception:
            pass
        await asyncio.sleep(15)

@app.post("/api/execute")
async def execute_task(req: dict):
    """接收并执行任务"""
    asyncio.create_task(_run_task(req))
    return {"status": "accepted"}

async def _run_task(req: dict):
    """任务执行主循环（对应第 3 章任务引擎）"""
    task_id = req["task_id"]
    context = await browser_mgr.new_context()
    page = await context.new_page()
    
    try:
        # 加载任务模板
        template = load_template(req["template_id"])
        start_step = 0
        
        # 断点续跑（对应第 3.3 节）
        if req.get("checkpoint"):
            start_step = req["checkpoint"]["last_step"] + 1
        
        # 逐步执行
        for i, action_def in enumerate(template.actions[start_step:], 
                                        start=start_step):
            action = build_action(action_def)
            ctx = ActionContext(
                page=page, task_id=task_id, step_index=i,
                variables={}, mcp=mcp
            )
            result = await action.run(ctx)
            
            if not result.success:
                raise TaskError(result.error_code, result.error)
            
            # 每 5 步保存检查点
            if i % 5 == 0:
                await save_checkpoint(task_id, i)
        
        # 上报成功
        await report_result(task_id, success=True)
    
    except Exception as e:
        await report_result(task_id, success=False, 
                            error=str(e))
    finally:
        await context.close()
        browser_mgr.release(context)
```

> 💡 这段代码是整个系统的「心脏」——Worker 的执行循环。它串联了 MCP 工具调用（第 2 章）、原子动作重试（第 3 章）、检查点保存（第 3.3 节）、浏览器资源管理（第 5 章），在一个紧凑的循环中完成。

### 10.4 接入可观测性与监控

把第 8 章的三根支柱（日志、追踪、指标）集成到 BrowserForge 中。

#### 结构化日志

```python
# observability/logger.py
"""结构化日志（对应第 8.1 节）"""

import json, sys
from datetime import datetime

class StructuredLogger:
    def __init__(self, worker_id: str = ""):
        self.worker_id = worker_id
    
    def log_tool_call(self, task_id: str, step: int, tool: str,
                      params: dict, success: bool,
                      error_code: str | None, duration_ms: int):
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": "info" if success else "error",
            "worker": self.worker_id,
            "task_id": task_id,
            "step": step,
            "tool": tool,
            "params": self._sanitize(params),
            "success": success,
            "error_code": error_code,
            "duration_ms": duration_ms,
        }
        # 输出到 stdout，容器运行时自动捕获
        print(json.dumps(entry, ensure_ascii=False), file=sys.stdout,
              flush=True)
    
    def log_event(self, level: str, message: str, **extra):
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "worker": self.worker_id,
            "message": message,
            **extra,
        }
        print(json.dumps(entry, ensure_ascii=False), file=sys.stdout,
              flush=True)
    
    def _sanitize(self, params: dict) -> dict:
        sensitive = {"password", "token", "api_key", "secret", "cookie"}
        return {
            k: "***" if k in sensitive else v
            for k, v in params.items()
        }
```

#### Prometheus 指标

```python
# observability/metrics.py
"""Prometheus 指标埋点（对应第 8.5 节）"""

from prometheus_client import Counter, Histogram, Gauge, start_http_server

class PrometheusMetrics:
    def __init__(self, port: int = 9090):
        # 计数器
        self.tasks_total = Counter(
            "bf_tasks_total", "任务总数", ["status", "template"]
        )
        self.steps_total = Counter(
            "bf_steps_total", "步骤总数", ["tool", "status", "error_code"]
        )
        self.tokens_total = Counter(
            "bf_tokens_total", "Token 消耗", ["model"]
        )
        
        # 直方图
        self.task_duration = Histogram(
            "bf_task_duration_seconds", "任务耗时",
            buckets=[1, 5, 10, 30, 60, 120, 300]
        )
        self.step_duration = Histogram(
            "bf_step_duration_seconds", "步骤耗时",
            buckets=[0.1, 0.5, 1, 2, 5, 10]
        )
        
        # 仪表盘
        self.active_tasks = Gauge("bf_active_tasks", "当前执行中的任务数")
        self.active_contexts = Gauge("bf_active_contexts", "活跃 Context 数")
        self.memory_mb = Gauge("bf_memory_mb", "Worker 内存使用 MB")
        
        # 启动 metrics HTTP 端点
        start_http_server(port)
    
    def record_step(self, tool: str, success: bool, 
                    error_code: str | None, duration_ms: int):
        status = "success" if success else "failure"
        self.steps_total.labels(
            tool=tool, status=status, 
            error_code=error_code or "none"
        ).inc()
        self.step_duration.observe(duration_ms / 1000)
    
    def record_task_complete(self, template: str, success: bool, 
                              duration_s: float):
        status = "success" if success else "failure"
        self.tasks_total.labels(status=status, template=template).inc()
        self.task_duration.observe(duration_s)
```

#### Grafana 大盘核心查询

将以下 PromQL 查询配置到 Grafana 大盘中：

```
任务成功率（最近 5 分钟滚动窗口）：
  rate(bf_tasks_total{status="success"}[5m])
  / rate(bf_tasks_total[5m])

步骤 P99 延迟：
  histogram_quantile(0.99, rate(bf_step_duration_seconds_bucket[5m]))

按工具的错误率排行：
  topk(5,
    rate(bf_steps_total{status="failure"}[1h])
    / rate(bf_steps_total[1h])
  )

Token 消耗速率（每小时）：
  rate(bf_tokens_total[1h]) * 3600

活跃 Worker 数：
  count(bf_active_tasks > 0)
```

建议创建 4 个面板行：

| 行 | 面板 |
| :--- | :--- |
| **概览** | 任务成功率仪表盘、活跃任务数、Worker 健康数 |
| **性能** | 任务耗时 P50/P95/P99、步骤耗时热力图 |
| **错误** | 错误率趋势、Top 5 错误码、失败任务列表 |
| **资源** | Token 消耗趋势、内存使用、Context 数量 |

> 💡 可观测性的建设不是一次性工程——先搭建骨架（上面这些），然后在实际运行中根据遇到的问题逐步添加更细粒度的指标。不要试图一开始就监控所有东西。

### 10.5 Docker 容器化部署与生产配置

所有代码写完了，最后一步：用 Docker Compose 把整个系统打包成一键启动。

#### 完整的 docker-compose.yml

```yaml
# docker-compose.yml
# 一键启动 BrowserForge 全部服务

version: "3.8"

services:
  # ── 基础设施 ──
  
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: agent_password
      POSTGRES_DB: agent_db
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./migrations/001_init.sql:/docker-entrypoint-initdb.d/001_init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agent"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  # ── 应用服务 ──
  
  orchestrator:
    build:
      context: .
      dockerfile: Dockerfile
    command: uvicorn orchestrator.main:app --host 0.0.0.0 --port 8080
    ports:
      - "8080:8080"
    environment:
      - REDIS_URL=redis://redis:6379
      - DB_URL=postgresql://agent:agent_password@postgres:5432/agent_db
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
  
  worker-1:
    build:
      context: .
      dockerfile: Dockerfile
    command: uvicorn worker.main:app --host 0.0.0.0 --port 8080
    environment:
      - ORCHESTRATOR_URL=http://orchestrator:8080
      - REDIS_URL=redis://redis:6379
      - DB_URL=postgresql://agent:agent_password@postgres:5432/agent_db
      - MAX_CONCURRENT_TASKS=10
    shm_size: "512m"
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: "2.0"
    depends_on:
      - orchestrator
  
  worker-2:
    build:
      context: .
      dockerfile: Dockerfile
    command: uvicorn worker.main:app --host 0.0.0.0 --port 8080
    environment:
      - ORCHESTRATOR_URL=http://orchestrator:8080
      - REDIS_URL=redis://redis:6379
      - DB_URL=postgresql://agent:agent_password@postgres:5432/agent_db
      - MAX_CONCURRENT_TASKS=10
    shm_size: "512m"
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: "2.0"
    depends_on:
      - orchestrator
  
  # ── 可观测性 ──
  
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus

volumes:
  pgdata:
```

#### Prometheus 采集配置

```yaml
# observability/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "orchestrator"
    static_configs:
      - targets: ["orchestrator:9090"]
  
  - job_name: "workers"
    static_configs:
      - targets: ["worker-1:9090", "worker-2:9090"]
```

#### 一键启动与验证

```bash
# 1. 启动全部服务
docker compose up -d

# 2. 等待服务就绪（约 30 秒）
docker compose ps

# 3. 提交一个测试任务
curl -X POST http://localhost:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "ecommerce_order",
    "params": {"url": "https://example.com", "keyword": "test"},
    "priority": 5,
    "tenant_id": "user_001"
  }'

# 4. 查询任务状态
curl http://localhost:8080/api/tasks/{task_id}

# 5. 查看 Worker 日志
docker compose logs -f worker-1

# 6. 打开 Grafana 大盘
# 浏览器访问 http://localhost:3000（admin/admin）
```

#### 生产环境上线清单

在部署到生产环境之前，逐项检查以下清单：

```
┌──────────────────────────────────────────────────────┐
│           BrowserForge 生产上线清单 ✓                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  安全                                                │
│  □ .env 文件不在版本控制中（.gitignore）               │
│  □ 数据库密码使用强密码                               │
│  □ API 端点启用认证（API Key / JWT）                  │
│  □ Cookie 加密存储                                   │
│  □ URL 白名单已配置                                  │
│                                                      │
│  可靠性                                              │
│  □ PostgreSQL 开启定时备份                            │
│  □ Redis 开启 RDB 持久化                             │
│  □ Worker 配置自动重启（restart: unless-stopped）      │
│  □ 健康检查端点正常工作                               │
│  □ 僵尸进程清理脚本加入 crontab                       │
│                                                      │
│  可观测性                                            │
│  □ Prometheus 正常采集所有服务指标                     │
│  □ Grafana 大盘 4 个面板行就绪                        │
│  □ 告警规则配置（成功率 < 90% → P1）                  │
│  □ 日志轮转配置（max-size: 100m, max-file: 3）        │
│                                                      │
│  性能                                                │
│  □ Worker 数量匹配预期并发量                          │
│  □ shm_size 设置为 512m+                             │
│  □ 数据库索引全部创建                                 │
│  □ Redis maxmemory 设置合理                           │
│                                                      │
└──────────────────────────────────────────────────────┘
```

> 💡 **第 10 章小结**：BrowserForge 是一个完整的浏览器 Agent 生产系统的参考实现。它不是玩具——它有真实的任务持久化、分布式调度、故障恢复、可观测性和容器化部署。把前 9 章的每一个设计决策都落地为代码，才是 Harness Engineering 的最终价值：**让 Agent 系统从「实验室 Demo」变成「生产系统」。**

---

## 结语

回到第 1 章的那个场景：你让 GPT-4 打开浏览器填一个表单，Demo 丝滑，生产 37% 成功率。

现在你有了完整的工程化武器库：

```
成功率 37% → 92%+ 的路径：

  MCP 工具层       → 减少 LLM 参数猜测错误（第 2 章）
  任务引擎        → 断点续跑，不再从头重来（第 3 章）
  上下文管理      → Token 不会溢出（第 4 章）
  Playwright 执行层 → 隔离、池化、反检测（第 5 章）
  并行调度        → 50 个任务同时跑不 OOM（第 6 章）
  Orchestrator    → 跨机器分发，Worker 挂了自动转移（第 7 章）
  可观测性        → 5 分钟定位任何问题（第 8 章）
  工程基础        → 数据库、网络、运维兜底（第 9 章）
  实战集成        → 一键 Docker Compose 部署（第 10 章）
```

Harness Engineering 不是一个「新」的领域——它是「把 AI Agent 真正变成生产系统」这个需求催生的工程化学科。LLM 的能力在飞速进化，但 **让 LLM 稳定地在真实世界中执行任务** 的工程挑战，永远需要 Harness Engineer 来解决。

**Build the harness. Ship the agent. 🚀**
