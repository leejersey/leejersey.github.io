# AI Workflow 编排引擎设计

> 从零设计类 Dify/Coze 的 AI 工作流引擎——节点化组合 AI 能力，支持 LLM 调用、条件分支、循环、并行执行、人工审核，用 Python 实现一个可扩展的 Workflow Runtime。

---

## 1. 为什么需要 Workflow 引擎：从硬编码到可视化编排

### 1.1 AI 应用复杂度演进：从一次 API 调用到工作流

```
AI 应用的三个阶段：

  阶段 1：单次调用
  ═══════════════════════════════════════
  用户提问 → LLM 回答
  一个函数搞定，不需要引擎

  阶段 2：链式调用
  ═══════════════════════════════════════
  提取关键词 → 搜索 → 总结 → 翻译
  用 LangChain 的 Chain 或手写函数串联

  阶段 3：工作流（Workflow）
  ═══════════════════════════════════════
  条件分支 + 并行执行 + 循环 + 人工审核
  需要一个引擎来调度执行
  
  ─────────────────────────────────────
  硬编码 if/else 维护不了 → 需要引擎
```

### 1.2 Dify / Coze / LangGraph 架构对比

| 维度 | Dify | Coze | LangGraph |
|:---|:---|:---|:---|
| 定位 | 开源 LLM 应用平台 | 字节跳动 Bot 平台 | 编程框架 |
| 编排方式 | 可视化拖拽 | 可视化拖拽 | 代码定义状态图 |
| 节点类型 | LLM/知识库/代码/HTTP | LLM/插件/知识库 | 自定义函数节点 |
| 分支/循环 | ✅ 条件分支 | ✅ 条件分支 | ✅ 条件边 |
| 并行执行 | ✅ | ⚠️ 有限 | ✅ |
| 持久化 | ✅ PostgreSQL | ✅ 云端 | ✅ Checkpointer |
| 适用场景 | 完整平台 | 快速搭建 Bot | 代码级精细控制 |

### 1.3 核心概念：节点、边、图、执行引擎

```
Workflow 引擎的四个核心概念：

  🔲 节点（Node）
  ═══════════════════════════════════════
  一个独立的处理单元：LLM 调用、代码执行、HTTP 请求...
  输入 → 处理 → 输出

  ─→ 边（Edge）
  ═══════════════════════════════════════
  连接两个节点，定义数据流向
  可以是无条件的，也可以是条件分支

  📊 图（Graph / DAG）
  ═══════════════════════════════════════
  节点 + 边组成的有向无环图
  描述整个工作流的结构

  ⚙️ 执行引擎（Runtime）
  ═══════════════════════════════════════
  按照图的拓扑顺序执行节点
  管理状态、处理错误、支持暂停/恢复
```

### 1.4 我们要构建什么：一个最小可用的 Workflow Runtime

```
目标：用 Python 实现一个 Workflow 引擎

  支持的节点类型：
  ├── LLM 节点（调用大模型）
  ├── 代码节点（执行 Python）
  ├── 条件节点（if/else 分支）
  ├── HTTP 节点（调用外部 API）
  ├── 循环节点（批量处理）
  └── 人工审核节点（暂停等待）

  支持的特性：
  ├── DAG 拓扑排序执行
  ├── 并行执行
  ├── 变量传递
  ├── 错误处理与重试
  ├── 执行日志
  └── FastAPI 接口
```

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Workflow** | 用图编排多个 AI 能力，比硬编码更灵活 |
| **DAG** | 有向无环图，描述节点的执行依赖关系 |
| **Runtime** | 执行引擎，按拓扑顺序调度节点运行 |

---

## 2. 数据模型设计：节点、边与工作流定义

### 2.1 节点类型设计：LLM / 代码 / 条件 / HTTP / 人工审核

::: v-pre
```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Any

class NodeType(str, Enum):
    LLM = "llm"                # 大模型调用
    CODE = "code"              # Python 代码执行
    CONDITION = "condition"    # 条件分支
    HTTP = "http"              # HTTP 请求
    LOOP = "loop"              # 循环处理
    HUMAN = "human"            # 人工审核
    START = "start"            # 开始节点
    END = "end"                # 结束节点

class NodeConfig(BaseModel):
    """节点配置"""
    id: str = Field(description="节点唯一 ID")
    type: NodeType
    name: str = Field(description="节点显示名称")
    config: dict[str, Any] = Field(default={}, description="节点特定配置")
    
    # LLM 节点示例 config:
    # {"model": "gpt-4o", "prompt": "请总结：&#123;&#123;input&#125;&#125;", "temperature": 0.7}
    
    # 条件节点示例 config:
    # {"condition": "&#123;&#123;score&#125;&#125; > 0.8", "true_next": "node_3", "false_next": "node_4"}
```
:::

### 2.2 边与连接：数据如何在节点间流动

```python
class Edge(BaseModel):
    """边：连接两个节点"""
    source: str = Field(description="源节点 ID")
    target: str = Field(description="目标节点 ID")
    condition: str | None = Field(default=None, description="条件表达式，为空则无条件")

class WorkflowDefinition(BaseModel):
    """工作流定义"""
    id: str
    name: str
    description: str = ""
    nodes: list[NodeConfig]
    edges: list[Edge]
    variables: dict[str, Any] = Field(default={}, description="全局变量")
```

### 2.3 工作流定义格式：JSON Schema 设计

::: v-pre
```json
{
  "id": "content_pipeline",
  "name": "内容生成流水线",
  "nodes": [
    {"id": "start", "type": "start", "name": "开始"},
    {"id": "outline", "type": "llm", "name": "生成大纲", "config": {
      "model": "gpt-4o",
      "prompt": "为主题「&#123;&#123;topic&#125;&#125;」生成文章大纲"
    &#125;&#125;,
    {"id": "draft", "type": "llm", "name": "撰写初稿", "config": {
      "model": "gpt-4o",
      "prompt": "根据大纲撰写文章：\n&#123;&#123;outline.output&#125;&#125;"
    &#125;&#125;,
    {"id": "review", "type": "human", "name": "人工审核", "config": {
      "message": "请审核初稿质量"
    &#125;&#125;,
    {"id": "end", "type": "end", "name": "结束"}
  ],
  "edges": [
    {"source": "start", "target": "outline"},
    {"source": "outline", "target": "draft"},
    {"source": "draft", "target": "review"},
    {"source": "review", "target": "end"}
  ],
  "variables": {"topic": ""}
}
```
:::

### 2.4 变量系统：模板变量与数据引用

::: v-pre
```python
import re

class VariableResolver:
    """变量解析器：支持 &#123;&#123;node_id.output&#125;&#125; 语法"""
    
    def __init__(self, context: dict[str, Any]):
        self.context = context  # {"node_id": {"output": "...", "status": "..."&#125;&#125;
    
    def resolve(self, template: str) -> str:
        """解析模板中的变量引用"""
        pattern = r'\{\{(\w+(?:\.\w+)*)\}\}'
        
        def replace(match):
            path = match.group(1).split(".")
            value = self.context
            for key in path:
                if isinstance(value, dict):
                    value = value.get(key, f"&#123;&#123;&#123;&#123;UNDEFINED:{match.group(1)&#125;&#125;&#125;&#125;}")
                else:
                    return str(value)
            return str(value)
        
        return re.sub(pattern, replace, template)

# 使用
resolver = VariableResolver({
    "topic": "Python 异步编程",
    "outline": {"output": "1. 协程基础\n2. asyncio\n3. 实战"},
})
result = resolver.resolve("根据大纲撰写文章：\n&#123;&#123;outline.output&#125;&#125;")
# → "根据大纲撰写文章：\n1. 协程基础\n2. asyncio\n3. 实战"
```
:::

> 💡 **变量系统是 Workflow 引擎的"血管"**——节点间的数据传递全靠它。`<span v-pre>&#123;&#123; node_id.output &#125;&#125;</span>` 语法让非开发者也能理解数据流向。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **NodeConfig** | 节点定义：ID + 类型 + 配置 |
| **Edge** | 边：source → target，可带条件 |
| **WorkflowDefinition** | 节点列表 + 边列表 + 全局变量 |
| **变量引用** | `<span v-pre>&#123;&#123; node_id.output &#125;&#125;</span>` 引用其他节点的输出 |

---

## 3. 执行引擎：DAG 调度与运行时

### 3.1 DAG 调度原理：拓扑排序与依赖分析

```python
from collections import defaultdict, deque

def topological_sort(nodes: list[NodeConfig], edges: list[Edge]) -> list[str]:
    """拓扑排序：确定节点执行顺序"""
    in_degree = defaultdict(int)
    adjacency = defaultdict(list)
    
    node_ids = {n.id for n in nodes}
    for node_id in node_ids:
        in_degree[node_id] = 0
    
    for edge in edges:
        adjacency[edge.source].append(edge.target)
        in_degree[edge.target] += 1
    
    # BFS 拓扑排序
    queue = deque([n for n in node_ids if in_degree[n] == 0])
    order = []
    
    while queue:
        node_id = queue.popleft()
        order.append(node_id)
        for next_id in adjacency[node_id]:
            in_degree[next_id] -= 1
            if in_degree[next_id] == 0:
                queue.append(next_id)
    
    if len(order) != len(node_ids):
        raise ValueError("工作流中存在循环依赖！")
    
    return order
```

### 3.2 执行引擎实现：WorkflowRuntime

```python
import asyncio
from enum import Enum
from datetime import datetime

class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"    # 等待人工审核

class NodeResult(BaseModel):
    node_id: str
    status: NodeStatus
    output: Any = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

class WorkflowRuntime:
    """工作流执行引擎"""
    
    def __init__(self, definition: WorkflowDefinition):
        self.definition = definition
        self.context: dict[str, Any] = dict(definition.variables)
        self.results: dict[str, NodeResult] = {}
        self.node_map = {n.id: n for n in definition.nodes}
        self.resolver = VariableResolver(self.context)
    
    async def execute(self, inputs: dict[str, Any] = None) -> dict:
        """执行整个工作流"""
        if inputs:
            self.context.update(inputs)
        
        # 拓扑排序
        order = topological_sort(self.definition.nodes, self.definition.edges)
        
        for node_id in order:
            node = self.node_map[node_id]
            
            # 跳过 start/end 节点
            if node.type in (NodeType.START, NodeType.END):
                self.results[node_id] = NodeResult(node_id=node_id, status=NodeStatus.SUCCESS)
                continue
            
            # 检查条件分支（是否应该跳过）
            if self._should_skip(node_id):
                self.results[node_id] = NodeResult(node_id=node_id, status=NodeStatus.SKIPPED)
                continue
            
            # 执行节点
            result = await self._execute_node(node)
            self.results[node_id] = result
            
            # 更新上下文
            if result.status == NodeStatus.SUCCESS:
                self.context[node_id] = {"output": result.output}
                self.resolver = VariableResolver(self.context)
        
        return self._get_final_output()
```

### 3.3 并行执行：互不依赖的节点同时运行

```python
async def execute_parallel(self, inputs: dict = None):
    """支持并行的执行引擎"""
    if inputs:
        self.context.update(inputs)
    
    adjacency = defaultdict(list)
    in_degree = defaultdict(int)
    for edge in self.definition.edges:
        adjacency[edge.source].append(edge.target)
        in_degree[edge.target] += 1
    
    # 找到所有入度为 0 的节点（可以立即执行）
    ready = deque([n.id for n in self.definition.nodes if in_degree[n.id] == 0])
    
    while ready:
        # 并行执行所有就绪节点
        batch = list(ready)
        ready.clear()
        
        tasks = [self._execute_node(self.node_map[nid]) for nid in batch
                 if self.node_map[nid].type not in (NodeType.START, NodeType.END)]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果，更新入度
        for node_id, result in zip(batch, results):
            self.results[node_id] = result
            if result.status == NodeStatus.SUCCESS:
                self.context[node_id] = {"output": result.output}
            
            for next_id in adjacency[node_id]:
                in_degree[next_id] -= 1
                if in_degree[next_id] == 0:
                    ready.append(next_id)
```

### 3.4 执行上下文：变量存储与模板渲染

```python
async def _execute_node(self, node: NodeConfig) -> NodeResult:
    """执行单个节点"""
    started_at = datetime.now()
    
    try:
        # 解析配置中的变量引用
        resolved_config = {}
        for key, value in node.config.items():
            if isinstance(value, str):
                resolved_config[key] = self.resolver.resolve(value)
            else:
                resolved_config[key] = value
        
        # 根据节点类型分发执行
        executor = NODE_EXECUTORS.get(node.type)
        if not executor:
            raise ValueError(f"未知节点类型: {node.type}")
        
        output = await executor(resolved_config, self.context)
        
        return NodeResult(
            node_id=node.id, status=NodeStatus.SUCCESS,
            output=output, started_at=started_at, finished_at=datetime.now()
        )
    except Exception as e:
        return NodeResult(
            node_id=node.id, status=NodeStatus.FAILED,
            error=str(e), started_at=started_at, finished_at=datetime.now()
        )
```

> 💡 **并行执行的关键是入度**——入度为 0 意味着所有依赖都已完成，可以安全执行。这就是为什么要用 DAG 而不是简单的链表。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **拓扑排序** | BFS 确定节点执行顺序，检测循环依赖 |
| **WorkflowRuntime** | 按顺序/并行执行节点，管理上下文 |
| **入度为 0** | 所有依赖完成的节点可以并行执行 |

---

## 4. 核心节点实现

### 4.1 LLM 节点：Prompt 模板 + 模型调用

```python
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def execute_llm_node(config: dict, context: dict) -> str:
    """LLM 节点：调用大模型生成内容"""
    model = config.get("model", "gpt-4o")
    prompt = config["prompt"]                  # 已经过变量解析
    temperature = config.get("temperature", 0.7)
    system_prompt = config.get("system_prompt", "")
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content
```

### 4.2 代码节点：安全执行 Python 代码

```python
import ast

SAFE_BUILTINS = {"len", "str", "int", "float", "list", "dict", "range",
                 "enumerate", "zip", "map", "filter", "sorted", "sum", "max", "min"}

async def execute_code_node(config: dict, context: dict) -> Any:
    """代码节点：在沙箱中执行 Python"""
    code = config["code"]
    
    # 安全检查：禁止导入和危险操作
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise SecurityError("代码节点禁止使用 import")
    
    # 构建安全的执行环境
    safe_globals = {"__builtins__": {k: __builtins__[k] for k in SAFE_BUILTINS
                                     if k in __builtins__&#125;&#125;
    safe_globals["context"] = context
    safe_globals["json"] = __import__("json")
    
    local_vars = {}
    exec(code, safe_globals, local_vars)
    
    return local_vars.get("result", None)

# 示例代码节点配置：
# {"code": "data = json.loads(context['fetch']['output'])\nresult = len(data['items'])"}
```

### 4.3 条件节点：if/else 分支路由

::: v-pre
```python
async def execute_condition_node(config: dict, context: dict) -> dict:
    """条件节点：计算条件表达式，决定走哪条分支"""
    condition = config["condition"]    # 如 "&#123;&#123;score&#125;&#125; > 0.8"
    
    # 安全求值
    try:
        result = eval(condition, {"__builtins__": {&#125;&#125;, context)
    except Exception:
        result = False
    
    return {
        "result": bool(result),
        "branch": "true" if result else "false",
        "next_node": config.get("true_next" if result else "false_next"),
    }
```
:::

### 4.4 HTTP 节点：调用外部 API

```python
import httpx

async def execute_http_node(config: dict, context: dict) -> dict:
    """HTTP 节点：调用外部 API"""
    url = config["url"]
    method = config.get("method", "GET").upper()
    headers = config.get("headers", {})
    body = config.get("body", None)
    timeout = config.get("timeout", 30)
    
    async with httpx.AsyncClient() as http_client:
        response = await http_client.request(
            method=method, url=url, headers=headers,
            json=body if method == "POST" else None,
            timeout=timeout,
        )
        response.raise_for_status()
        
        return {
            "status_code": response.status_code,
            "body": response.json() if "json" in response.headers.get("content-type", "") else response.text,
        }
```

### 4.5 循环节点：批量处理列表数据

::: v-pre
```python
async def execute_loop_node(config: dict, context: dict) -> list:
    """循环节点：对列表中的每个元素执行子工作流"""
    items = config["items"]                 # 列表数据（或变量引用）
    if isinstance(items, str):
        items = context.get(items, [])
    
    sub_workflow_id = config["sub_workflow"]  # 子节点 ID
    max_concurrency = config.get("concurrency", 5)
    
    semaphore = asyncio.Semaphore(max_concurrency)
    results = []
    
    async def process_one(item):
        async with semaphore:
            sub_context = {**context, "item": item}
            executor = NODE_EXECUTORS[NodeType.LLM]
            return await executor({"prompt": config["prompt"].replace("&#123;&#123;item&#125;&#125;", str(item))}, sub_context)
    
    tasks = [process_one(item) for item in items]
    results = await asyncio.gather(*tasks)
    return list(results)
```
:::

```python
# 注册所有节点执行器
NODE_EXECUTORS = {
    NodeType.LLM: execute_llm_node,
    NodeType.CODE: execute_code_node,
    NodeType.CONDITION: execute_condition_node,
    NodeType.HTTP: execute_http_node,
    NodeType.LOOP: execute_loop_node,
}
```

> 💡 **代码节点的安全性是重中之重**——用户可以编写任意代码，必须禁止 `import`、`os`、`subprocess` 等危险操作。生产环境建议用 Docker 容器隔离。

**第 4 章核心知识回顾：**

| 节点类型 | 核心逻辑 |
|:---|:---|
| **LLM** | Prompt 变量解析 → 调用大模型 → 返回文本 |
| **代码** | AST 安全检查 → 沙箱执行 → 返回 result |
| **条件** | 表达式求值 → 返回 true/false 分支 |
| **HTTP** | httpx 异步请求 → 返回响应 |
| **循环** | 批量并发处理 → 返回结果列表 |

---

## 5. 高级特性：错误处理、重试与人工介入

### 5.1 错误处理策略：重试、跳过、中止

```python
from enum import Enum

class ErrorStrategy(str, Enum):
    RETRY = "retry"          # 重试 N 次
    SKIP = "skip"            # 跳过，继续执行后续节点
    ABORT = "abort"          # 终止整个工作流
    FALLBACK = "fallback"    # 使用备用值

class NodeErrorConfig(BaseModel):
    strategy: ErrorStrategy = ErrorStrategy.ABORT
    max_retries: int = 3
    retry_delay: float = 1.0          # 秒
    fallback_value: Any = None

async def execute_with_error_handling(
    node: NodeConfig, 
    executor, 
    config: dict, 
    context: dict
) -> NodeResult:
    """带错误处理的节点执行"""
    error_config = NodeErrorConfig(**node.config.get("error", {}))
    
    for attempt in range(error_config.max_retries + 1):
        try:
            output = await executor(config, context)
            return NodeResult(node_id=node.id, status=NodeStatus.SUCCESS, output=output)
        except Exception as e:
            if attempt < error_config.max_retries and error_config.strategy == ErrorStrategy.RETRY:
                await asyncio.sleep(error_config.retry_delay * (2 ** attempt))  # 指数退避
                continue
            
            if error_config.strategy == ErrorStrategy.SKIP:
                return NodeResult(node_id=node.id, status=NodeStatus.SKIPPED, error=str(e))
            
            if error_config.strategy == ErrorStrategy.FALLBACK:
                return NodeResult(node_id=node.id, status=NodeStatus.SUCCESS, 
                                  output=error_config.fallback_value)
            
            return NodeResult(node_id=node.id, status=NodeStatus.FAILED, error=str(e))
```

### 5.2 超时控制与熔断

```python
async def execute_with_timeout(executor, config: dict, context: dict, timeout: int = 60):
    """带超时的节点执行"""
    try:
        return await asyncio.wait_for(
            executor(config, context),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        raise TimeoutError(f"节点执行超时（{timeout}s）")
```

### 5.3 人工审核节点：暂停等待审批

```python
import uuid
from datetime import datetime

class HumanReviewStore:
    """人工审核状态管理"""
    
    def __init__(self):
        self._pending: dict[str, dict] = {}
    
    def create_review(self, workflow_run_id: str, node_id: str, data: dict) -> str:
        review_id = str(uuid.uuid4())
        self._pending[review_id] = {
            "workflow_run_id": workflow_run_id,
            "node_id": node_id,
            "data": data,
            "created_at": datetime.now(),
            "status": "pending",
        }
        return review_id
    
    def approve(self, review_id: str, feedback: str = "") -> dict:
        review = self._pending[review_id]
        review["status"] = "approved"
        review["feedback"] = feedback
        return review
    
    def reject(self, review_id: str, reason: str = "") -> dict:
        review = self._pending[review_id]
        review["status"] = "rejected"
        review["reason"] = reason
        return review

review_store = HumanReviewStore()

async def execute_human_node(config: dict, context: dict) -> dict:
    """人工审核节点：创建审核请求，暂停工作流"""
    review_id = review_store.create_review(
        workflow_run_id=context.get("_run_id", ""),
        node_id=context.get("_node_id", ""),
        data={"message": config["message"], "content": config.get("review_content", "")},
    )
    
    # 返回 WAITING 状态，工作流暂停
    return {"review_id": review_id, "status": "waiting_for_review"}
```

### 5.4 执行日志与可观测性

```python
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("workflow")

@dataclass
class ExecutionLog:
    """工作流执行日志"""
    run_id: str
    events: list[dict] = field(default_factory=list)
    
    def log_node_start(self, node_id: str, node_type: str):
        event = {"type": "node_start", "node_id": node_id, "node_type": node_type,
                 "timestamp": datetime.now().isoformat()}
        self.events.append(event)
        logger.info(f"▶️ 开始执行 [{node_id}] ({node_type})")
    
    def log_node_end(self, node_id: str, status: str, duration: float):
        event = {"type": "node_end", "node_id": node_id, "status": status,
                 "duration": duration, "timestamp": datetime.now().isoformat()}
        self.events.append(event)
        logger.info(f"{'✅' if status == 'success' else '❌'} 完成 [{node_id}] ({duration:.2f}s)")
    
    def get_summary(self) -> dict:
        return {
            "total_nodes": len([e for e in self.events if e["type"] == "node_start"]),
            "success": len([e for e in self.events if e.get("status") == "success"]),
            "failed": len([e for e in self.events if e.get("status") == "failed"]),
            "total_duration": sum(e.get("duration", 0) for e in self.events if "duration" in e),
        }
```

> 💡 **人工审核节点是 AI Workflow 区别于纯自动化的关键**——内容生成需要人审核、敏感操作需要人确认。工作流暂停→人审批→恢复执行，这个模式在 Dify 和 LangGraph 中都有实现。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **错误策略** | retry/skip/abort/fallback 四种策略 |
| **指数退避** | 重试间隔 1s → 2s → 4s，避免打爆下游 |
| **人工审核** | 创建审核请求→暂停→审批后恢复 |
| **执行日志** | 记录每个节点的开始/结束/耗时/状态 |

---

## 6. 持久化与 API 设计

### 6.1 数据库设计：工作流定义 + 执行记录

```sql
-- 工作流定义表
CREATE TABLE workflows (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    definition  JSONB NOT NULL,             -- 完整的工作流 JSON 定义
    version     INTEGER DEFAULT 1,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 工作流执行记录表
CREATE TABLE workflow_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id     UUID REFERENCES workflows(id),
    status          VARCHAR(20) DEFAULT 'running',   -- running/success/failed/paused
    inputs          JSONB DEFAULT '{}',
    outputs         JSONB DEFAULT '{}',
    node_results    JSONB DEFAULT '{}',              -- 每个节点的执行结果
    execution_log   JSONB DEFAULT '[]',
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    error           TEXT
);
```

### 6.2 FastAPI 接口：CRUD + 执行 + 状态查询

```python
from fastapi import FastAPI, HTTPException
from uuid import UUID

app = FastAPI(title="AI Workflow Engine")

@app.post("/api/workflows", summary="创建工作流")
async def create_workflow(req: WorkflowDefinition):
    workflow_id = await db.save_workflow(req)
    return {"id": workflow_id}

@app.post("/api/workflows/{workflow_id}/run", summary="执行工作流")
async def run_workflow(workflow_id: UUID, inputs: dict = {}):
    definition = await db.get_workflow(workflow_id)
    if not definition:
        raise HTTPException(404, "工作流不存在")
    
    run_id = await db.create_run(workflow_id, inputs)
    
    # 异步执行
    runtime = WorkflowRuntime(definition)
    asyncio.create_task(execute_and_save(runtime, run_id, inputs))
    
    return {"run_id": run_id, "status": "running"}

@app.get("/api/runs/{run_id}", summary="查询执行状态")
async def get_run_status(run_id: UUID):
    run = await db.get_run(run_id)
    return {
        "status": run["status"],
        "node_results": run["node_results"],
        "execution_log": run["execution_log"],
    }

@app.post("/api/reviews/{review_id}/approve", summary="审批通过")
async def approve_review(review_id: str, feedback: str = ""):
    review = review_store.approve(review_id, feedback)
    # 恢复工作流执行...
    return {"status": "approved"}
```

### 6.3 SSE 推送：实时推送执行进度

```python
from fastapi.responses import StreamingResponse

@app.get("/api/runs/{run_id}/stream", summary="流式获取执行进度")
async def stream_run(run_id: UUID):
    async def event_stream():
        while True:
            run = await db.get_run(run_id)
            yield f"data: {json.dumps({'status': run['status'], 'node_results': run['node_results']})}\n\n"
            
            if run["status"] in ("success", "failed"):
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### 6.4 工作流版本管理

```python
@app.put("/api/workflows/{workflow_id}", summary="更新工作流（创建新版本）")
async def update_workflow(workflow_id: UUID, req: WorkflowDefinition):
    current = await db.get_workflow(workflow_id)
    new_version = current["version"] + 1
    
    await db.update_workflow(workflow_id, req, version=new_version)
    
    return {"id": workflow_id, "version": new_version}
```

> 💡 **工作流定义用 JSONB 存储**——结构灵活、支持索引、PostgreSQL 原生 JSON 操作。不要用关系表拆分节点和边，那样查询会非常复杂。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **JSONB 存储** | 工作流定义整个存为 JSONB，灵活又高效 |
| **异步执行** | `create_task` 后台运行，立即返回 run_id |
| **SSE 推送** | 前端实时看到每个节点的执行进度 |
| **版本管理** | 更新即创建新版本，旧版本保留 |

---

## 7. 实战：构建三个典型 AI Workflow

### 7.1 内容生成流水线：大纲 → 初稿 → 审核 → 发布

::: v-pre
```json
{
  "id": "content_pipeline",
  "name": "AI 内容生成流水线",
  "nodes": [
    {"id": "start", "type": "start", "name": "开始"},
    {"id": "outline", "type": "llm", "name": "生成大纲", "config": {
      "model": "gpt-4o",
      "prompt": "为主题「&#123;&#123;topic&#125;&#125;」生成一篇 3000 字文章的大纲，包含 5-7 个章节"
    &#125;&#125;,
    {"id": "draft", "type": "llm", "name": "撰写初稿", "config": {
      "model": "gpt-4o",
      "prompt": "根据以下大纲撰写完整文章：\n\n&#123;&#123;outline.output&#125;&#125;\n\n要求：专业、有深度、带代码示例"
    &#125;&#125;,
    {"id": "quality_check", "type": "llm", "name": "质量检查", "config": {
      "model": "gpt-4o-mini",
      "prompt": "评估以下文章的质量（1-10 分），指出问题：\n\n&#123;&#123;draft.output&#125;&#125;"
    &#125;&#125;,
    {"id": "score_check", "type": "condition", "name": "分数检查", "config": {
      "condition": "int(quality_check['output'].split('分')[0][-1]) >= 7",
      "true_next": "review",
      "false_next": "rewrite"
    &#125;&#125;,
    {"id": "rewrite", "type": "llm", "name": "重写", "config": {
      "prompt": "根据反馈修改文章：\n\n反馈：&#123;&#123;quality_check.output&#125;&#125;\n\n原文：&#123;&#123;draft.output&#125;&#125;"
    &#125;&#125;,
    {"id": "review", "type": "human", "name": "人工审核", "config": {
      "message": "请审核以下文章是否可以发布"
    &#125;&#125;,
    {"id": "end", "type": "end", "name": "结束"}
  ],
  "edges": [
    {"source": "start", "target": "outline"},
    {"source": "outline", "target": "draft"},
    {"source": "draft", "target": "quality_check"},
    {"source": "quality_check", "target": "score_check"},
    {"source": "score_check", "target": "review", "condition": "true"},
    {"source": "score_check", "target": "rewrite", "condition": "false"},
    {"source": "rewrite", "target": "review"},
    {"source": "review", "target": "end"}
  ]
}
```
:::

### 7.2 智能客服流程：意图识别 → 路由 → 回复

::: v-pre
```json
{
  "id": "customer_service",
  "name": "智能客服工作流",
  "nodes": [
    {"id": "start", "type": "start", "name": "开始"},
    {"id": "intent", "type": "llm", "name": "意图识别", "config": {
      "model": "gpt-4o-mini",
      "prompt": "识别用户意图，输出类别：product_inquiry / complaint / refund / other\n\n用户消息：&#123;&#123;message&#125;&#125;"
    &#125;&#125;,
    {"id": "route", "type": "condition", "name": "路由", "config": {
      "condition": "'refund' in intent['output'] or 'complaint' in intent['output']",
      "true_next": "human_agent",
      "false_next": "kb_search"
    &#125;&#125;,
    {"id": "kb_search", "type": "http", "name": "知识库搜索", "config": {
      "url": "http://localhost:8000/api/search",
      "method": "POST",
      "body": {"query": "&#123;&#123;message&#125;&#125;", "top_k": 3}
    &#125;&#125;,
    {"id": "answer", "type": "llm", "name": "生成回复", "config": {
      "prompt": "基于知识库结果回答用户：\n\n知识库：&#123;&#123;kb_search.output&#125;&#125;\n\n用户问题：&#123;&#123;message&#125;&#125;"
    &#125;&#125;,
    {"id": "human_agent", "type": "human", "name": "转人工", "config": {
      "message": "用户需要退款/投诉处理，请人工介入"
    &#125;&#125;,
    {"id": "end", "type": "end", "name": "结束"}
  ]
}
```
:::

### 7.3 数据处理管道：采集 → 清洗 → 分析 → 报告

::: v-pre
```json
{
  "id": "data_pipeline",
  "name": "数据分析报告生成",
  "nodes": [
    {"id": "start", "type": "start", "name": "开始"},
    {"id": "fetch", "type": "http", "name": "获取数据", "config": {
      "url": "&#123;&#123;api_url&#125;&#125;",
      "method": "GET"
    &#125;&#125;,
    {"id": "clean", "type": "code", "name": "数据清洗", "config": {
      "code": "data = context['fetch']['output']['body']\nresult = [item for item in data if item.get('status') == 'active']"
    &#125;&#125;,
    {"id": "analyze", "type": "loop", "name": "逐条分析", "config": {
      "items": "clean",
      "prompt": "分析以下数据，提取关键指标：&#123;&#123;item&#125;&#125;",
      "concurrency": 5
    &#125;&#125;,
    {"id": "report", "type": "llm", "name": "生成报告", "config": {
      "model": "gpt-4o",
      "prompt": "基于以下分析结果，生成一份完整的数据分析报告：\n\n&#123;&#123;analyze.output&#125;&#125;"
    &#125;&#125;,
    {"id": "end", "type": "end", "name": "结束"}
  ]
}
```
:::

> 💡 **三个实战覆盖了最常见的 Workflow 模式**——顺序+条件分支（内容生成）、意图路由（客服）、循环+并行（数据处理）。理解这三个模式，就能组合出绝大多数 AI 工作流。

---

## 8. 进阶：性能优化与生产部署

### 8.1 异步与并发优化

```python
# 优化 1：LLM 节点连接池复用
from openai import AsyncOpenAI

# 全局复用客户端（连接池）
llm_client = AsyncOpenAI(max_retries=3, timeout=60)

# 优化 2：节点结果缓存
from functools import lru_cache
import hashlib

def cache_key(node_type: str, config: dict) -> str:
    return hashlib.md5(f"{node_type}:{json.dumps(config, sort_keys=True)}".encode()).hexdigest()

_node_cache: dict[str, Any] = {}

async def cached_execute(node_type, config, context):
    key = cache_key(node_type, config)
    if key in _node_cache:
        return _node_cache[key]
    result = await NODE_EXECUTORS[node_type](config, context)
    _node_cache[key] = result
    return result
```

### 8.2 分布式执行：Celery + Redis 任务队列

```python
from celery import Celery

celery_app = Celery("workflow", broker="redis://localhost:6379/0")

@celery_app.task(bind=True, max_retries=3)
def execute_node_task(self, node_config: dict, context: dict):
    """在 Celery Worker 中执行节点"""
    import asyncio
    
    node_type = NodeType(node_config["type"])
    executor = NODE_EXECUTORS[node_type]
    
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(executor(node_config["config"], context))
        return {"status": "success", "output": result}
    except Exception as e:
        self.retry(countdown=2 ** self.request.retries)
```

```
分布式架构：

  FastAPI（API 层）
    │
    ├─→ Redis（消息队列 + 状态存储）
    │       │
    │       ├─→ Worker 1（执行 LLM 节点）
    │       ├─→ Worker 2（执行 HTTP 节点）
    │       └─→ Worker 3（执行代码节点）
    │
    └─→ PostgreSQL（持久化）
```

### 8.3 工作流模板与复用

```python
# 模板库：预置常用工作流模板
WORKFLOW_TEMPLATES = {
    "content_generation": {
        "name": "内容生成",
        "description": "大纲→初稿→审核→发布",
        "definition": {...},
    },
    "customer_service": {
        "name": "智能客服",
        "description": "意图识别→路由→回复",
        "definition": {...},
    },
    "data_report": {
        "name": "数据报告",
        "description": "采集→清洗→分析→报告",
        "definition": {...},
    },
}

@app.post("/api/workflows/from-template/{template_id}")
async def create_from_template(template_id: str, customization: dict = {}):
    template = WORKFLOW_TEMPLATES[template_id]
    definition = {**template["definition"], **customization}
    return await create_workflow(WorkflowDefinition(**definition))
```

### 8.4 与 Dify / Coze / LangGraph 的对比总结

| 维度 | 本教程实现 | Dify | LangGraph |
|:---|:---|:---|:---|
| 代码量 | ~500 行 | 50000+ 行 | ~3000 行 |
| 可视化 | ❌ 需另建 | ✅ 内置 | ❌ 代码 |
| 节点类型 | 6 种 | 15+ 种 | 自定义 |
| 持久化 | ✅ PG | ✅ PG | ✅ 可选 |
| 分布式 | ✅ Celery | ✅ 内置 | ⚠️ 有限 |
| 学习价值 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

> 💡 **自己实现 Workflow 引擎的价值在于理解原理**——生产环境可以用 Dify（完整平台）或 LangGraph（编程灵活）。但只有理解了 DAG 调度、变量系统、错误处理的实现，才能在使用这些框架时做出正确的设计决策。

---

## 附录：Workflow 引擎速查手册

### A.1 节点类型与参数速查

| 节点类型 | 必填参数 | 可选参数 |
|:---|:---|:---|
| `llm` | `prompt` | `model`, `temperature`, `system_prompt` |
| `code` | `code` | — |
| `condition` | `condition`, `true_next`, `false_next` | — |
| `http` | `url` | `method`, `headers`, `body`, `timeout` |
| `loop` | `items`, `prompt` | `concurrency` |
| `human` | `message` | `review_content` |

### A.2 工作流 JSON 定义模板

```json
{
  "id": "template",
  "name": "工作流模板",
  "nodes": [
    {"id": "start", "type": "start", "name": "开始"},
    {"id": "node_1", "type": "llm", "name": "处理", "config": {"prompt": "..."&#125;&#125;,
    {"id": "end", "type": "end", "name": "结束"}
  ],
  "edges": [
    {"source": "start", "target": "node_1"},
    {"source": "node_1", "target": "end"}
  ],
  "variables": {}
}
```

### A.3 API 接口速查

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| POST | `/api/workflows` | 创建工作流 |
| GET | `/api/workflows/{id}` | 获取工作流定义 |
| PUT | `/api/workflows/{id}` | 更新（新版本） |
| POST | `/api/workflows/{id}/run` | 执行工作流 |
| GET | `/api/runs/{id}` | 查询执行状态 |
| GET | `/api/runs/{id}/stream` | SSE 流式进度 |
| POST | `/api/reviews/{id}/approve` | 审批通过 |

### A.4 常见 Workflow 模式

```
模式 1：顺序执行
  A → B → C → D

模式 2：条件分支
  A → 条件 ──true──→ B
          └─false─→ C

模式 3：并行合并
  A ──→ B ──┐
  A ──→ C ──┤→ D
  A ──→ D ──┘

模式 4：循环处理
  A → Loop(items) → B

模式 5：人工审核
  A → B → Human → C
```
