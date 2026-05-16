# AI Agent 沙箱执行环境：让 Agent 安全地"动手"

> AI Agent 不只是"说话"——它需要执行代码、操作文件、运行命令。但你不会让一个 AI 直接在你的生产服务器上 `rm -rf /`。沙箱执行环境就是给 Agent 一台"用完即扔"的安全电脑：随便折腾，出了事也不影响你的系统。

---

## 1. 为什么 Agent 需要沙箱

当 Agent 只是"聊天"时，安全不是问题。但当 Agent 开始**执行代码**——写文件、跑命令、访问网络——一切都变了。

### 1.1 Agent 执行代码的四大安全风险

| 风险 | 场景 | 后果 |
|------|------|------|
| **容器/系统逃逸** | Agent 生成的代码利用内核漏洞突破隔离 | 攻击者获得宿主机控制权 |
| **文件系统污染** | Agent 修改了不该改的文件 | 系统配置损坏、数据丢失 |
| **网络攻击** | Agent 代码发起恶意请求 | DDoS 攻击、数据外泄 |
| **资源耗尽** | Agent 写了死循环或内存泄漏 | 服务器 CPU/内存被吃满 |

### 1.2 沙箱的核心价值：隔离、可控、可销毁

```
沙箱的三个核心特征：

  ① 隔离（Isolation）
     沙箱内的代码无论做什么，都不影响宿主系统
     → 即使 Agent 执行了 rm -rf /，也只删沙箱内的文件

  ② 可控（Control）
     你可以精确控制沙箱的资源（CPU/内存/网络/磁盘）
     → Agent 最多用 1 核 CPU、512MB 内存、10 秒超时

  ③ 可销毁（Ephemeral）
     沙箱用完即扔，不留痕迹
     → 每次执行都是一个干净的环境，没有状态泄漏
```

### 1.3 沙箱在 Agent 系统中的位置

```
Agent 系统架构中的沙箱：

  ┌──────────────────────────────────────┐
  │  你的应用服务器（安全区）              │
  │                                      │
  │  Agent 大脑（LLM）                    │
  │    ↓ "我要执行这段代码"               │
  │  沙箱管理器                           │
  │    ↓ 创建隔离环境                     │
  └──────┬───────────────────────────────┘
         │ API 调用
  ┌──────▼───────────────────────────────┐
  │  沙箱（隔离区）                       │
  │  ┌────────────────────────────────┐  │
  │  │ 独立内核 / 独立文件系统          │  │
  │  │ Agent 的代码在这里执行          │  │
  │  │ 资源受限、网络受控              │  │
  │  └────────────────────────────────┘  │
  │  执行完毕 → 返回结果 → 销毁沙箱      │
  └──────────────────────────────────────┘
```

> 💡 **核心原则：** Agent 的"大脑"（LLM）在你的安全区内，Agent 的"手"（代码执行）在沙箱里。大脑决定做什么，手在隔离环境里执行，结果通过 API 返回。

---

## 2. 隔离技术对比：从容器到 MicroVM

隔离技术是沙箱的基石——选错了，安全就是空谈。

### 2.1 Docker 容器：共享内核的风险

```
Docker 容器的隔离模型：

  宿主机内核（共享！）
  ┌──────────────────────────────────┐
  │  ┌──────┐  ┌──────┐  ┌──────┐  │
  │  │容器 A│  │容器 B│  │容器 C│  │
  │  │      │  │      │  │      │  │
  │  │ 进程  │  │ 进程  │  │ 进程  │  │
  │  └──────┘  └──────┘  └──────┘  │
  │          共享同一个内核           │
  └──────────────────────────────────┘

  问题：容器共享宿主机内核
  → 内核漏洞 = 所有容器都受影响
  → 容器逃逸攻击可以控制宿主机
  → 不适合执行不可信的 AI 生成代码
```

### 2.2 gVisor：用户态内核拦截

```
gVisor 的隔离模型：

  宿主机内核
  ┌──────────────────────────────────┐
  │  ┌────────────────────────────┐  │
  │  │  gVisor Sentry（用户态内核） │  │
  │  │  拦截所有系统调用           │  │
  │  │  ┌──────┐                  │  │
  │  │  │ 进程  │ → syscall       │  │
  │  │  └──────┘   → Sentry 拦截  │  │
  │  │              → 安全检查     │  │
  │  │              → 转发或拒绝   │  │
  │  └────────────────────────────┘  │
  └──────────────────────────────────┘

  优点：不需要完整 VM，性能开销小
  缺点：兼容性问题（部分 syscall 不支持）
  代表用户：Google Cloud Run、Modal
```

### 2.3 Kata Containers：轻量虚拟机

```
Kata Containers 的隔离模型：

  宿主机
  ┌──────────────────────────────────┐
  │  ┌────────────────────────────┐  │
  │  │  轻量 VM（QEMU/Cloud-HV）  │  │
  │  │  ┌──────────────────────┐  │  │
  │  │  │  独立 Guest 内核      │  │  │
  │  │  │  ┌──────┐            │  │  │
  │  │  │  │ 容器  │            │  │  │
  │  │  │  └──────┘            │  │  │
  │  │  └──────────────────────┘  │  │
  │  └────────────────────────────┘  │
  └──────────────────────────────────┘

  优点：兼容 Docker 生态 + VM 级隔离
  缺点：启动较慢（~1 秒）
```

### 2.4 Firecracker MicroVM：AWS Lambda 的底层技术

```
Firecracker 的隔离模型：

  宿主机
  ┌──────────────────────────────────┐
  │  ┌──────────┐  ┌──────────┐     │
  │  │ MicroVM  │  │ MicroVM  │     │
  │  │ 独立内核  │  │ 独立内核  │     │
  │  │ 独立网络  │  │ 独立网络  │     │
  │  │ 独立文件  │  │ 独立文件  │     │
  │  │  ~5MB    │  │  ~5MB    │     │
  │  │  ~125ms  │  │  ~125ms  │     │
  │  └──────────┘  └──────────┘     │
  └──────────────────────────────────┘

  优点：VM 级隔离 + 极快启动（~125ms）+ 极小内存（~5MB）
  缺点：只支持 Linux、功能精简
  代表用户：AWS Lambda、E2B、Fly.io
```

**四种技术的对比总结：**

| 技术 | 隔离级别 | 启动速度 | 兼容性 | 适合 AI 沙箱 |
|------|---------|---------|--------|------------|
| Docker | ⭐⭐ 进程级 | ~50ms | ⭐⭐⭐⭐⭐ | ❌ 不推荐 |
| gVisor | ⭐⭐⭐ 系统调用级 | ~100ms | ⭐⭐⭐ | ✅ 可用 |
| Kata | ⭐⭐⭐⭐ VM 级 | ~1s | ⭐⭐⭐⭐ | ✅ 推荐 |
| Firecracker | ⭐⭐⭐⭐⭐ VM 级 | ~125ms | ⭐⭐⭐ | ✅✅ 最佳 |

> 💡 **结论：** 执行不可信的 AI 生成代码，**Firecracker MicroVM** 是当前最优解——VM 级隔离 + 毫秒级启动。E2B 就是基于它构建的。

---

## 3. E2B 深度解析：临时执行的王者

E2B（Execute to Build）是当前 AI Agent 沙箱的**行业标准**——专为"执行 LLM 生成的代码"而设计。

### 3.1 架构设计：每个沙箱一个 MicroVM

```
E2B 的执行流程：

  你的 Agent 应用
    ↓ SDK 调用: sandbox.run_code("import pandas...")
    ↓
  E2B 云端
    ↓ 分配一个 Firecracker MicroVM
    ↓ ~125ms 冷启动
    ↓ 执行代码
    ↓ 返回 stdout/stderr/artifacts
    ↓ 保持沙箱存活（等待后续调用）
    ↓ 超时后自动销毁

  关键数据：
  - 冷启动: ~80-150ms
  - 每个沙箱: 独立 Linux 内核 + 文件系统
  - 默认存活: 5 分钟（可延长至 24 小时）
  - 支持: 文件读写、pip 安装、apt 安装、网络请求
```

### 3.2 Python SDK 实战：创建/执行/销毁

```bash
# 安装
pip install e2b-code-interpreter
```

```python
from e2b_code_interpreter import Sandbox
import os

# 设置 API Key
os.environ["E2B_API_KEY"] = "your-api-key"

# 方式一：上下文管理器（自动创建和销毁）
with Sandbox() as sandbox:
    # 执行 Python 代码
    result = sandbox.run_code("print('Hello from E2B!')")
    print(result.text)  # → Hello from E2B!
    
    # 执行多步代码（沙箱保持状态）
    sandbox.run_code("x = 42")
    result = sandbox.run_code("print(x * 2)")
    print(result.text)  # → 84
    
    # 安装 pip 包
    sandbox.run_code("!pip install requests")
    result = sandbox.run_code("""
    import requests
    resp = requests.get('https://httpbin.org/get')
    print(resp.status_code)
    """)
    print(result.text)  # → 200

# 方式二：手动管理生命周期
sandbox = Sandbox()
sandbox.run_code("print('Hello!')")
sandbox.kill()  # 手动销毁
```

### 3.3 Code Interpreter 模式：类 ChatGPT 的代码执行

```python
from e2b_code_interpreter import Sandbox

def ai_code_interpreter(user_query: str, llm):
    """构建一个类似 ChatGPT Code Interpreter 的服务"""
    
    with Sandbox() as sandbox:
        # Step 1: 上传用户数据
        sandbox.files.write("/data/sales.csv", user_csv_data)
        
        # Step 2: LLM 生成分析代码
        code = llm.generate(f"""
        用户问题: {user_query}
        数据文件在 /data/sales.csv
        请生成 Python 代码分析数据并生成图表。
        图表保存到 /output/chart.png
        """)
        
        # Step 3: 在沙箱中执行
        result = sandbox.run_code(code)
        
        # Step 4: 提取结果
        if result.error:
            return f"执行错误: {result.error}"
        
        # 下载生成的图表
        chart = sandbox.files.read("/output/chart.png")
        return {"text": result.text, "chart": chart}
```

### 3.4 自定义沙箱模板：预装你的依赖

每次沙箱都 `pip install` 太慢？用自定义模板**预装依赖**：

```toml
# e2b.toml（项目根目录）
[sandbox]
name = "data-analysis-sandbox"

[sandbox.setup]
# 这些命令在构建模板时执行一次
commands = [
    "pip install pandas numpy matplotlib seaborn scikit-learn",
    "pip install requests beautifulsoup4",
    "mkdir -p /data /output"
]
```

```bash
# 构建自定义模板
e2b template build

# 使用自定义模板创建沙箱（已预装所有依赖）
```

```python
# 使用自定义模板
with Sandbox(template="data-analysis-sandbox") as sandbox:
    # pandas 已预装，无需安装
    result = sandbox.run_code("import pandas; print(pandas.__version__)")
```

> 💡 **性能优化：** 自定义模板可以把冷启动时间从"启动+安装依赖=30 秒"降到"只启动=150ms"。生产环境必须使用自定义模板。

---

## 4. Daytona 深度解析：持久化工作区

E2B 是"用完即扔"的利器，但如果你的 Agent 需要**跨会话保持状态**呢？Daytona 填补了这个空白。

### 4.1 架构设计：可组合的"虚拟电脑"

```
Daytona 的核心理念：不是"沙箱"，是"虚拟电脑"

  ┌──────────────────────────────────────┐
  │  Daytona Sandbox                     │
  │                                      │
  │  ┌────────────────────────────────┐  │
  │  │ 独立 Linux 内核                 │  │
  │  │ 完整文件系统（可持久化）         │  │
  │  │ 网络栈（独立 IP）               │  │
  │  │ vCPU + RAM + Disk 配额         │  │
  │  └────────────────────────────────┘  │
  │                                      │
  │  能力：                              │
  │  - 文件系统操作 ✅                   │
  │  - Git 操作 ✅                      │
  │  - 进程管理 ✅                      │
  │  - 包管理（apt/pip/npm）✅          │
  │  - 网络请求 ✅                      │
  │  - 桌面 UI（Computer Use）✅        │
  │  - 快照/暂停/恢复 ✅                │
  └──────────────────────────────────────┘

  冷启动: ~60-90ms（比 E2B 更快）
  基于: OCI 容器标准（兼容 Docker Hub 镜像）
```

### 4.2 状态持久化：快照、暂停、恢复

这是 Daytona 与 E2B 的**最大差异**：

```python
from daytona_sdk import Daytona

daytona = Daytona()

# 创建一个沙箱
sandbox = daytona.create()

# 安装依赖（耗时 30 秒）
sandbox.process.exec("pip install torch transformers datasets")

# 拍快照 → 保存当前状态（含已安装的包）
snapshot_id = sandbox.snapshot()
print(f"快照已保存: {snapshot_id}")

# ... Agent 执行任务 ...

# 明天恢复：从快照启动（秒级，无需重新安装）
sandbox2 = daytona.create(snapshot=snapshot_id)
# torch/transformers 已经在里面了！

# 暂停沙箱（保持状态但释放计算资源）
sandbox.pause()

# 需要时恢复
sandbox.resume()
```

```
状态管理对比：

  E2B:     创建 → 执行 → 销毁（无状态）
  Daytona: 创建 → 执行 → 快照 → 暂停 → 恢复 → 分支
  
  Daytona 支持"分支"：
  快照 A → 创建沙箱 B（尝试方案 1）
         → 创建沙箱 C（尝试方案 2）
  → 哪个方案成功就保留哪个
```

### 4.3 Computer Use 沙箱：给 Agent 一个桌面

```python
# 创建一个带桌面的沙箱（用于 Computer Use Agent）
sandbox = daytona.create(
    image="daytona/desktop-vnc:latest",
    resources={"cpu": 2, "memory": "4GB", "disk": "20GB"}
)

# Agent 可以操作桌面
sandbox.process.exec("firefox https://example.com &")
screenshot = sandbox.desktop.screenshot()

# 返回截图给 LLM 分析
# LLM: "我看到了一个登录页面，我要点击用户名输入框..."
sandbox.desktop.click(x=350, y=200)
sandbox.desktop.type("admin@example.com")
```

### 4.4 自托管部署：在你自己的基础设施上运行

```
Daytona 的部署选项：

  ① 托管云（Daytona Cloud）
     → 即开即用，按分钟计费
     
  ② 自托管（On-Premise）
     → 在你自己的服务器/K8s 集群上部署
     → 数据不出你的网络
     → 适合对数据合规有要求的企业

  自托管安装：
  curl -sf https://download.daytona.io/install | bash
  daytona server start
```

> 💡 **Daytona 的定位：** 如果 E2B 是"一次性纸杯"，Daytona 就是"你自己的工作台"——可以暂停、恢复、分支、持久化，适合长期任务和 Coding Agent。

---

## 5. E2B vs Daytona：选型决策

两个都很好——但场景不同。

### 5.1 全面对比：八个维度

| 维度 | E2B | Daytona |
|------|-----|---------|
| **隔离技术** | Firecracker MicroVM | OCI 容器 + 独立内核 |
| **冷启动** | ~80-150ms | ~60-90ms |
| **状态管理** | 临时（用完即销毁） | 持久（快照/暂停/恢复） |
| **Computer Use** | ❌ 不支持 | ✅ 支持桌面 |
| **GPU 支持** | ❌ | ✅ |
| **自托管** | ❌ 仅云端 | ✅ 支持 |
| **SDK 成熟度** | ⭐⭐⭐⭐⭐ 非常成熟 | ⭐⭐⭐⭐ 快速迭代中 |
| **定价** | 按沙箱时间计费 | 按资源 + 存储计费 |

### 5.2 选型决策树：什么场景用什么

```
选型决策树：

  你的 Agent 需要什么？
  │
  ├─ 执行一段代码，拿到结果就行
  │  → E2B（临时沙箱 + Code Interpreter）
  │
  ├─ 安装大量依赖，多次迭代
  │  → Daytona（快照保存依赖环境）
  │
  ├─ 操作浏览器/桌面 UI
  │  → Daytona（Computer Use 沙箱）
  │
  ├─ 数据不能出公司网络
  │  → Daytona（自托管部署）
  │
  ├─ 需要 GPU 推理/训练
  │  → Daytona 或 Modal
  │
  └─ 集成到 LangChain/OpenAI SDK
     → E2B（生态最成熟）
```

### 5.3 混合方案：同时使用两者

```
最佳实践：E2B + Daytona 混合部署

  ┌─────────────────────────────────────────┐
  │  Agent 编排器                            │
  │                                         │
  │  简单代码执行 → E2B                      │
  │  （数据分析、API 调用、脚本运行）          │
  │                                         │
  │  复杂开发任务 → Daytona                  │
  │  （项目构建、测试运行、持久化工作区）       │
  └─────────────────────────────────────────┘
  
  示例：
  用户："帮我分析这个 CSV 文件"
  → Agent 选择 E2B（临时执行 pandas 代码）
  
  用户："帮我修复这个 GitHub Issue"
  → Agent 选择 Daytona（克隆仓库、修改、测试、提 PR）
```

> 💡 **一句话选型：** 需要"计算器"用 E2B，需要"工作台"用 Daytona。

---

## 6. 实战一：为 LangChain Agent 接入 E2B 沙箱

从零构建一个能**安全执行代码**的 LangChain Agent。

### 6.1 环境搭建与 API Key 获取

```bash
# 安装依赖
pip install e2b-code-interpreter langchain langchain-openai

# 获取 E2B API Key
# 1. 注册 https://e2b.dev
# 2. 进入 Dashboard → Settings → API Keys
# 3. 设置环境变量
export E2B_API_KEY="your-e2b-api-key"
export OPENAI_API_KEY="your-openai-api-key"
```

### 6.2 创建代码执行工具

```python
from langchain_core.tools import tool
from e2b_code_interpreter import Sandbox

@tool
def execute_python(code: str) -> str:
    """在安全沙箱中执行 Python 代码。
    
    用于数据分析、计算、文件处理等需要运行代码的任务。
    沙箱与宿主机完全隔离，可以安全执行任意代码。
    
    Args:
        code: 要执行的 Python 代码
    Returns:
        执行结果（stdout + stderr）
    """
    with Sandbox() as sandbox:
        result = sandbox.run_code(code)
        
        if result.error:
            return f"❌ 执行错误:\n{result.error.traceback}"
        
        output = result.text or "(无输出)"
        return f"✅ 执行成功:\n{output}"
```

### 6.3 集成到 ReAct Agent

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# 初始化 LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 系统提示
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个数据分析 Agent。
    当用户提出分析需求时，使用 execute_python 工具
    在安全沙箱中执行代码。
    
    规则：
    - 用 pandas 处理数据
    - 用 matplotlib 生成图表
    - 始终打印关键结果
    """),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# 创建 Agent
agent = create_react_agent(llm, [execute_python], prompt)
executor = AgentExecutor(agent=agent, tools=[execute_python])

# 使用
result = executor.invoke({
    "input": "生成 1 到 100 的随机数列表，计算均值和标准差"
})
```

### 6.4 完整示例：数据分析 Agent

```python
# 一个完整的数据分析 Agent 示例
@tool
def execute_with_data(code: str, csv_data: str = "") -> str:
    """在沙箱中执行代码，支持上传数据文件"""
    with Sandbox(template="data-analysis-sandbox") as sandbox:
        # 上传数据
        if csv_data:
            sandbox.files.write("/data/input.csv", csv_data)
        
        # 执行分析代码
        result = sandbox.run_code(code)
        
        # 检查是否生成了图表
        try:
            chart = sandbox.files.read("/output/chart.png")
            return f"✅ 结果:\n{result.text}\n📊 图表已生成"
        except:
            return f"✅ 结果:\n{result.text}"

# Agent 的典型对话：
# 用户: "分析 sales.csv 中每月的销售趋势"
# Agent 思考: 我需要用 pandas 读取数据，用 matplotlib 画趋势图
# Agent 调用: execute_with_data(code="import pandas as pd...")
# Agent 回复: "根据分析，Q3 销售额增长了 23%..."
```

> 💡 **工程提示：** 生产环境中，建议复用沙箱实例（不要每次都创建新的），用 `Sandbox.keep_alive()` 延长存活时间，减少冷启动开销。

---

## 7. 实战二：为 Coding Agent 接入 Daytona 工作区

与第 6 章的临时执行不同，这里构建的是一个能**持续工作**的 Coding Agent。

### 7.1 创建持久化开发环境

```python
from daytona_sdk import Daytona, CreateSandboxParams

daytona = Daytona()

# 创建一个开发环境沙箱
sandbox = daytona.create(CreateSandboxParams(
    image="python:3.12-slim",
    resources={"cpu": 2, "memory": "4GB", "disk": "10GB"},
    auto_stop_interval=0  # 不自动停止
))

# 安装开发工具
sandbox.process.exec("apt-get update && apt-get install -y git")
sandbox.process.exec("pip install pytest ruff mypy")

print(f"沙箱已就绪: {sandbox.id}")
```

### 7.2 在沙箱中执行 Git 工作流

```python
async def coding_agent_workflow(sandbox, repo_url: str, issue: str):
    """Coding Agent 的完整工作流"""
    
    # Step 1: 克隆仓库
    sandbox.process.exec(f"git clone {repo_url} /workspace")
    sandbox.process.exec("cd /workspace && git checkout -b fix/agent-patch")
    
    # Step 2: 分析代码库
    files = sandbox.files.list("/workspace/src")
    code_context = ""
    for f in files:
        if f.name.endswith(".py"):
            content = sandbox.files.read(f"/workspace/src/{f.name}")
            code_context += f"\n--- {f.name} ---\n{content}"
    
    # Step 3: LLM 生成修复代码
    fix = llm.generate(f"""
    Issue: {issue}
    代码库:
    {code_context}
    
    请生成修复代码，指明要修改哪个文件的哪些行。
    """)
    
    # Step 4: 在沙箱中应用修改
    sandbox.files.write(f"/workspace/src/{fix.file}", fix.new_content)
    
    # Step 5: 运行测试验证
    result = sandbox.process.exec("cd /workspace && pytest tests/ -v")
    
    if result.exit_code == 0:
        # 测试通过，提交
        sandbox.process.exec('cd /workspace && git add -A')
        sandbox.process.exec(f'cd /workspace && git commit -m "fix: {issue}"')
        return {"status": "success", "output": result.stdout}
    else:
        return {"status": "test_failed", "output": result.stderr}
```

### 7.3 快照与恢复：任务中断后继续

```python
# 场景：Agent 正在处理一个复杂的多步任务

# Step 1: 完成依赖安装后拍快照
sandbox.process.exec("pip install -r requirements.txt")  # 耗时 2 分钟
snapshot_base = sandbox.snapshot()  # 保存"依赖已装好"的状态

# Step 2: 尝试方案 A
sandbox_a = daytona.create(snapshot=snapshot_base)
result_a = try_approach_a(sandbox_a)

# Step 3: 方案 A 失败？从快照恢复，尝试方案 B
if not result_a.success:
    sandbox_b = daytona.create(snapshot=snapshot_base)
    result_b = try_approach_b(sandbox_b)
    # 无需重新安装依赖！

# Step 4: 完成后暂停（下次继续）
sandbox.pause()
# 保存 sandbox.id，下次 resume
```

### 7.4 完整示例：自动化 PR Review Agent

```python
class PRReviewAgent:
    """自动化 PR Review Agent：克隆→分析→测试→评审"""
    
    def __init__(self):
        self.daytona = Daytona()
    
    async def review_pr(self, repo_url: str, pr_branch: str):
        # 创建隔离的审查环境
        sandbox = self.daytona.create(CreateSandboxParams(
            image="python:3.12-slim",
            resources={"cpu": 2, "memory": "4GB"}
        ))
        
        try:
            # 克隆并切换到 PR 分支
            sandbox.process.exec(f"git clone {repo_url} /repo")
            sandbox.process.exec(f"cd /repo && git checkout {pr_branch}")
            
            # 安装依赖
            sandbox.process.exec("cd /repo && pip install -r requirements.txt")
            
            # 运行测试
            test_result = sandbox.process.exec("cd /repo && pytest -v")
            
            # 运行 linter
            lint_result = sandbox.process.exec("cd /repo && ruff check .")
            
            # 获取 diff
            diff = sandbox.process.exec(
                "cd /repo && git diff main...HEAD"
            )
            
            # LLM 分析
            review = llm.generate(f"""
            请审查这个 PR：
            
            Diff:
            {diff.stdout}
            
            测试结果: {"通过" if test_result.exit_code == 0 else "失败"}
            Lint 结果: {lint_result.stdout}
            
            请给出审查意见。
            """)
            
            return review
        finally:
            sandbox.delete()  # 清理环境
```

> 💡 **关键差异：** E2B 实战（第 6 章）是"执行一段代码"，Daytona 实战（第 7 章）是"在一个完整项目环境中工作"。前者像计算器，后者像开发机。

---

## 8. 安全加固与生产实践

沙箱本身提供了隔离，但**生产环境需要更多**。

### 8.1 网络策略：控制 Agent 的网络访问

```
网络策略设计：

  默认策略：拒绝所有出站流量
  
  白名单模式：
  ┌──────────────────────────────────────┐
  │  沙箱网络策略                         │
  │                                      │
  │  允许:                                │
  │  ✅ pypi.org (pip install)            │
  │  ✅ github.com (git clone)            │
  │  ✅ api.openai.com (LLM 调用)         │
  │                                      │
  │  拒绝:                                │
  │  ❌ 其他所有外部地址                   │
  │  ❌ 内网地址（10.x/172.x/192.168.x） │
  │  ❌ 元数据服务（169.254.169.254）     │
  └──────────────────────────────────────┘
```

### 8.2 资源限制：CPU/内存/磁盘配额

| 资源 | 推荐限制 | 原因 |
|------|---------|------|
| CPU | 1-2 核 | 防止挖矿/密集计算 |
| 内存 | 512MB-2GB | 防止内存泄漏拖垮宿主 |
| 磁盘 | 1-5GB | 防止填满磁盘 |
| 进程数 | 最多 50 个 | 防止 fork 炸弹 |
| 网络带宽 | 10Mbps | 防止 DDoS |

### 8.3 执行超时：防止死循环和资源泄漏

```python
import asyncio

async def safe_execute(sandbox, code: str, timeout: int = 30):
    """带超时的安全执行"""
    try:
        result = await asyncio.wait_for(
            sandbox.run_code_async(code),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        sandbox.kill()  # 强制终止沙箱
        return {"error": f"执行超时（{timeout}秒），已强制终止"}
```

### 8.4 审计日志：记录沙箱内的所有操作

```python
import logging
from datetime import datetime

audit_logger = logging.getLogger("sandbox.audit")

def log_sandbox_operation(
    sandbox_id: str,
    operation: str,
    code: str,
    result: str,
    user_id: str
):
    audit_logger.info(
        f"[{datetime.utcnow().isoformat()}] "
        f"sandbox={sandbox_id} user={user_id} "
        f"op={operation} "
        f"code_hash={hash(code)} "
        f"status={'success' if not result.error else 'error'}"
    )

# 每次沙箱操作都记录
# → 谁在什么时间执行了什么代码
# → 结果是成功还是失败
# → 用于安全审计和问题追踪
```

> 💡 **生产清单：** 上线前检查——① 网络白名单 ② 资源配额 ③ 执行超时 ④ 审计日志。缺一个都有安全隐患。

---

## 9. 生态与展望

### 9.1 更多选择：Modal、Fly.io Sprites

| 平台 | 定位 | 隔离技术 | 最佳场景 |
|------|------|---------|---------|
| **Modal** | Python ML 工作负载 | gVisor | GPU 推理、模型训练、数据管线 |
| **Fly.io Sprites** | 持久化 Agent 运行时 | Firecracker | 长期运行的 Agent、100GB 状态持久化 |
| **Morph** | 轻量代码执行 | 容器 | 简单脚本、低成本场景 |
| **RunLoop** | Coding Agent 专用 | MicroVM | 开发环境、CI/CD 集成 |

```
Modal 的独特优势（GPU 场景）：

  import modal
  
  app = modal.App("ai-agent")
  
  @app.function(gpu="A100", timeout=300)
  def run_inference(model_name, input_text):
      # 在 A100 GPU 上执行推理
      # 自动扩缩容，按秒计费
      model = load_model(model_name)
      return model.generate(input_text)
  
  → 如果你的 Agent 需要调用 GPU，Modal 是最佳选择
  → E2B/Daytona 都不支持 GPU
```

### 9.2 沙箱标准化：未来的统一接口

```
当前的痛点：每个平台 SDK 都不一样

  E2B:     sandbox.run_code(code)
  Daytona: sandbox.process.exec(code)
  Modal:   function.remote(args)
  
未来方向：统一的沙箱接口标准

  理想的统一 API：
  sandbox = UniversalSandbox.create(
      provider="e2b",        # 或 "daytona", "modal"
      resources={...},
      network_policy={...}
  )
  sandbox.execute(code)
  sandbox.files.read(path)
  sandbox.snapshot()
```

### 9.3 延伸阅读与参考资料

**官方资源：**
- [E2B 文档](https://e2b.dev/docs)
- [E2B GitHub](https://github.com/e2b-dev/e2b)
- [Daytona 文档](https://daytona.io/docs)
- [Daytona GitHub](https://github.com/daytonaio/daytona)

**关联教程：**
- [Agentic Coding 完全指南](Agentic Coding 完全指南) — Coding Agent 的完整方法论
- [Harness Engineering 完全指南](Harness Engineering 完全指南) — Agent 的安全边界设计

**底层技术：**
- [Firecracker GitHub](https://github.com/firecracker-microvm/firecracker) — AWS 开源的 MicroVM
- [gVisor 文档](https://gvisor.dev/) — Google 的用户态内核
- [OCI 规范](https://opencontainers.org/) — 容器镜像标准

---

> **全书完。**
>
> 沙箱执行环境的本质就一句话：
> **给 Agent 一台"用完即扔"的安全电脑，让它随便折腾。**
>
> 选择 E2B 还是 Daytona？记住：
> - 临时计算 → E2B（纸杯）
> - 持久工作 → Daytona（工作台）
> - GPU 推理 → Modal（算力池）
>
> 安全三铁律：隔离 + 限额 + 超时。做到这三点，你的 Agent 就可以放心"动手"了。🔒
