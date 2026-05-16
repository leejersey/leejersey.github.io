# AI Agent Marketplace 设计

> 当 Agent 成为新的"App"，谁来做 Agent 时代的 App Store？本教程从零设计一个 Agent 分发平台——注册发现、版本管理、权限沙箱、计费结算、质量评审，构建可互操作的 Agent 生态。

---

## 1. 为什么需要 Agent Marketplace

2024 年，一个中等规模的 AI 团队可能有 5 个 Agent。2025 年底，这个数字变成了 50 个。到 2026 年，企业内部 Agent 数量突破 200——问题来了：**怎么找到那个能帮你完成任务的 Agent？怎么确认它安全可靠？怎么避免重复造轮子？**

> 💡 **本章目标**：理解 Agent Marketplace 的核心价值主张——它不只是一个"商店"，而是 Agent 生态的基础设施。

### 1.1 Agent 生态的现状与痛点

```
2026 年 Agent 生态的三大痛点：

1️⃣ 发现困难（Discovery）
   "我需要一个能帮我分析 PDF 发票的 Agent"
   → 在 GitHub 搜？在 Discord 问？在公司 Wiki 翻？
   → 没有统一的 Agent 目录，找 Agent 全靠口口相传

2️⃣ 信任缺失（Trust）
   "这个第三方 Agent 安全吗？会不会泄露我的数据？"
   → 没有审查机制、没有沙箱隔离、没有质量评分
   → 企业不敢用第三方 Agent，只能自己从零开发

3️⃣ 重复建设（Duplication）
   "隔壁团队也造了一个一模一样的 Agent"
   → 公司内部 3 个团队各自开发了"发邮件 Agent"
   → 没有共享和复用机制，人力极度浪费
```

### 1.2 从 App Store 到 Agent Store：范式类比

```
软件分发的三次革命：

  2008：App Store（Apple）
    软件从"光盘安装"变成"一键下载"
    → 开发者专注开发，平台负责分发和信任

  2010：npm / Docker Hub
    代码/环境从"手动搭建"变成"包管理器安装"
    → npm install express → 一行命令用上别人的代码

  2026：Agent Marketplace
    Agent 从"自己造"变成"搜索 + 安装 + 编排"
    → agent install invoice-analyzer → 一行命令用上别人的 Agent
```

| 类比 | App Store | npm | Agent Marketplace |
|:---|:---|:---|:---|
| **分发物** | App（二进制） | 代码包 | Agent（代码 + Prompt + 工具） |
| **身份标识** | App ID + 名称 | package.json | Agent Card |
| **版本管理** | Build Number | semver | semver + 模型版本 |
| **信任机制** | Apple 审核 | 下载量 + stars | 安全审查 + 质量评分 |
| **运行方式** | 用户设备 | 开发者机器 | 平台沙箱 / 用户自部署 |
| **计费** | 买断 / 订阅 | 免费 | 按次 / Token / 订阅 |

### 1.3 Marketplace 解决什么问题：发现、信任、复用

```
Agent Marketplace 的三层价值：

┌─────────────────────────────────────────┐
│           🔍 发现层                       │
│  分类目录 + 语义搜索 + 能力匹配 + 推荐    │
│  "帮我找一个能分析 Excel 的 Agent"        │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│           🛡️ 信任层                       │
│  安全审查 + 沙箱隔离 + 质量评分 + 用户评价 │
│  "这个 Agent 安全等级 A，成功率 95%"      │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│           🔄 复用层                       │
│  一键安装 + 版本管理 + 依赖解析 + 编排组合 │
│  "agent install + 三行代码就能用"         │
└─────────────────────────────────────────┘
```

> 💡 **核心洞察**：Agent Marketplace 不是"锦上添花"——当企业 Agent 数量超过 50 个时，它是**刚需基础设施**。没有它，Agent 生态就是一盘散沙。

---

## 2. 架构设计：Agent Marketplace 的核心组件

一个 Agent Marketplace 需要五大核心组件协同工作。本章给出整体架构，后续章节逐一深入。

### 2.1 系统架构全景图

```
Agent Marketplace 系统架构：

                        ┌───────────────────┐
                        │   开发者 / 调用者    │
                        └────────┬──────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      API Gateway         │
                    │  认证 / 限流 / 路由 / 计量  │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
  ┌───────▼───────┐    ┌───────▼───────┐    ┌────────▼────────┐
  │   Registry     │    │   Executor    │    │    Billing       │
  │  注册表服务     │    │   执行沙箱     │    │   计费结算       │
  │ ─────────────  │    │ ─────────────│    │ ───────────────  │
  │ Agent Card     │    │ Docker 容器   │    │ 用量计量         │
  │ 版本管理       │    │ 资源隔离      │    │ 账单生成         │
  │ 搜索索引       │    │ 超时控制      │    │ 开发者结算       │
  └───────┬───────┘    └───────┬───────┘    └────────┬────────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      Data Layer          │
                    │  PostgreSQL + Redis + S3  │
                    └─────────────────────────┘
```

### 2.2 Agent Registry：注册与元数据管理

```python
# 注册表核心数据模型
from sqlalchemy import Column, String, JSON, DateTime, Integer, Enum
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class AgentRecord(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True)         # uuid
    name = Column(String, unique=True, index=True) # "invoice-analyzer"
    display_name = Column(String)                  # "发票分析 Agent"
    author_id = Column(String, index=True)
    description = Column(String)
    version = Column(String)                       # "1.2.0"
    agent_card = Column(JSON)                      # 完整 Agent Card
    capabilities = Column(JSON)                    # ["pdf_parse", "ocr", "extract"]
    pricing = Column(JSON)                         # {"model": "per_call", "price": 0.01}
    trust_level = Column(String, default="unverified")  # unverified/community/official
    status = Column(String, default="pending")     # pending/active/suspended
    downloads = Column(Integer, default=0)
    avg_rating = Column(Integer, default=0)        # 1-5
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### 2.3 API Gateway：路由、限流与认证

```python
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
import time

app = FastAPI(title="Agent Marketplace Gateway")
security = HTTPBearer()

# 限流中间件
class RateLimiter:
    def __init__(self, redis_client, max_requests: int = 100, window: int = 60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window
    
    async def check(self, api_key: str) -> bool:
        key = f"rate:{api_key}:{int(time.time()) // self.window}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.window)
        return count <= self.max_requests

@app.post("/v1/agents/{agent_id}/invoke")
async def invoke_agent(agent_id: str, request: Request, token = Depends(security)):
    # 1. 认证
    user = await authenticate(token.credentials)
    
    # 2. 限流
    if not await rate_limiter.check(user.api_key):
        raise HTTPException(429, "请求过于频繁")
    
    # 3. 路由到执行沙箱
    result = await executor.run(agent_id, await request.json())
    
    # 4. 计量
    await billing.record_usage(user.id, agent_id, result.tokens, result.cost)
    
    return result
```

### 2.4 Execution Sandbox：安全隔离运行

```python
import docker
import asyncio

class AgentExecutor:
    def __init__(self):
        self.docker = docker.from_env()
    
    async def run(self, agent_id: str, input_data: dict, timeout: int = 120) -> dict:
        agent = await registry.get(agent_id)
        
        container = self.docker.containers.run(
            image=agent.docker_image,
            command=f"python run.py",
            environment={"INPUT": json.dumps(input_data)},
            mem_limit="512m",           # 内存限制
            cpu_period=100000,
            cpu_quota=50000,            # CPU 限制 50%
            network_mode="none",        # 默认无网络（除非声明需要）
            detach=True,
            auto_remove=True,
        )
        
        # 等待执行完成（带超时）
        try:
            result = container.wait(timeout=timeout)
            logs = container.logs().decode()
            return json.loads(logs)
        except Exception:
            container.kill()
            return {"error": "执行超时"}
```

### 2.5 技术选型与部署架构

| 组件 | 技术选型 | 说明 |
|:---|:---|:---|
| **API Gateway** | FastAPI + Uvicorn | 异步高性能，自带 OpenAPI 文档 |
| **数据库** | PostgreSQL + pgvector | 结构化数据 + Agent 能力向量搜索 |
| **缓存** | Redis | 限流计数 + 会话缓存 + 排行榜 |
| **对象存储** | MinIO / S3 | Agent 代码包、镜像、日志 |
| **容器运行时** | Docker / Firecracker | 沙箱隔离执行第三方 Agent |
| **消息队列** | Redis Streams / RabbitMQ | 异步任务、计费事件 |
| **搜索引擎** | pgvector + Embedding | 语义搜索 Agent 能力 |

> 💡 **MVP 建议**：初版用 FastAPI + PostgreSQL + Docker 就够了。不要一上来就上 Kubernetes——等 Agent 数量超过 100 个再考虑。

---

## 3. Agent Card：Agent 的"身份证"

Agent Card 是 Marketplace 的核心数据结构——它告诉所有人"这个 Agent 是什么、能做什么、怎么调用、多少钱"。

### 3.1 Agent Card 字段设计（JSON Schema）

```json
{
  "name": "invoice-analyzer",
  "display_name": "发票分析 Agent",
  "version": "1.2.0",
  "author": {
    "id": "dev-12345",
    "name": "张三",
    "verified": true
  },
  "description": "自动识别和提取 PDF/图片发票中的关键信息",
  "category": "document-processing",
  "tags": ["ocr", "invoice", "pdf", "extraction"],
  
  "capabilities": [
    "pdf_parsing",
    "image_ocr", 
    "structured_extraction"
  ],
  
  "input_schema": {
    "type": "object",
    "properties": {
      "file_url": {"type": "string", "description": "发票文件 URL"},
      "file_type": {"type": "string", "enum": ["pdf", "png", "jpg"]}
    },
    "required": ["file_url"]
  },
  
  "output_schema": {
    "type": "object",
    "properties": {
      "invoice_number": {"type": "string"},
      "amount": {"type": "number"},
      "date": {"type": "string", "format": "date"},
      "vendor": {"type": "string"},
      "items": {"type": "array"}
    }
  },
  
  "dependencies": {
    "tools": ["ocr_service", "pdf_parser"],
    "models": ["gpt-4o-mini"],
    "agents": []
  },
  
  "pricing": {
    "model": "per_call",
    "price_usd": 0.02,
    "free_quota": 100
  },
  
  "runtime": {
    "docker_image": "marketplace/invoice-analyzer:1.2.0",
    "memory_mb": 512,
    "timeout_s": 60,
    "requires_network": true
  },
  
  "trust_level": "community_verified",
  "quality_score": 4.5,
  "total_calls": 12500
}
```

### 3.2 能力声明：告诉调用者"我能做什么"

```python
from pydantic import BaseModel

class AgentCapability(BaseModel):
    """Agent 能力声明"""
    name: str               # "pdf_parsing"
    description: str         # "解析 PDF 文件并提取文本"
    input_types: list[str]   # ["application/pdf"]
    output_types: list[str]  # ["application/json"]
    confidence: float        # 0.95（自评置信度）

# 能力匹配：调用者描述需求，系统匹配 Agent
async def match_capabilities(requirement: str, embedding_model) -> list[dict]:
    """语义匹配：自然语言需求 → 最相关的 Agent"""
    req_embedding = await embedding_model.embed(requirement)
    # 在 pgvector 中做向量相似度搜索
    results = await db.execute(
        "SELECT *, capability_embedding <=> $1 AS distance "
        "FROM agents WHERE status = 'active' "
        "ORDER BY distance LIMIT 10",
        [req_embedding]
    )
    return results
```

### 3.3 输入输出 Schema：类型安全的接口契约

```python
from pydantic import BaseModel, ValidationError

def validate_agent_input(agent_card: dict, user_input: dict) -> dict:
    """根据 Agent Card 的 input_schema 校验输入"""
    schema = agent_card["input_schema"]
    required = schema.get("required", [])
    
    # 检查必填字段
    missing = [f for f in required if f not in user_input]
    if missing:
        return {"valid": False, "error": f"缺少必填字段: {missing}"}
    
    # 类型检查
    for field, spec in schema.get("properties", {}).items():
        if field in user_input:
            expected_type = spec.get("type")
            if expected_type == "string" and not isinstance(user_input[field], str):
                return {"valid": False, "error": f"{field} 应为 string"}
    
    return {"valid": True}
```

### 3.4 与 A2A 协议 / MCP 的互操作

```
Agent Card 与 A2A / MCP 的映射关系：

  Agent Card                    A2A Agent Card          MCP Tool
  ──────────                    ──────────────          ────────
  name                    →     name                →   name
  description             →     description         →   description
  input_schema            →     inputModes          →   inputSchema
  output_schema           →     outputModes         →   （无，靠约定）
  capabilities            →     skills              →   （无）
  pricing                 →     （扩展字段）          →   （无）
  runtime.docker_image    →     url（endpoint）      →   （无，由 Server 管理）
```

> 💡 **互操作是趋势**：Agent Card 应兼容 A2A 协议的 Agent Card 格式——这样你在 Marketplace 注册的 Agent，可以直接被任何 A2A 兼容的编排器发现和调用。

---

## 4. Agent 注册与发现

Marketplace 的核心用户体验：开发者能快速上架 Agent，调用者能用自然语言找到合适的 Agent。

### 4.1 注册流程：提交 → 校验 → 审核 → 上架

```
Agent 上架流程：

  开发者提交
  ├── agent_card.json        ← Agent 元数据
  ├── Dockerfile             ← 运行时定义
  └── README.md              ← 文档
       ↓
  自动校验（5 分钟）
  ├── ✅ agent_card.json Schema 合法
  ├── ✅ Docker 镜像能构建成功
  ├── ✅ 输入输出 Schema 有示例可验证
  ├── ✅ 安全扫描通过（无恶意代码）
  └── ✅ 冒烟测试通过（3 条测试用例）
       ↓
  人工审核（24h 内）
  ├── 描述是否准确
  ├── 定价是否合理
  └── 是否与已有 Agent 重复
       ↓
  ✅ 上架 → 出现在搜索结果中
```

```python
class AgentSubmission:
    async def submit(self, card: dict, dockerfile: str) -> str:
        # 1. Schema 校验
        errors = validate_agent_card(card)
        if errors:
            return {"status": "rejected", "errors": errors}
        
        # 2. 构建镜像
        image = await self.build_image(dockerfile, card["name"], card["version"])
        
        # 3. 冒烟测试
        test_results = await self.smoke_test(image, card.get("test_cases", []))
        if not all(r["passed"] for r in test_results):
            return {"status": "rejected", "errors": "冒烟测试未通过"}
        
        # 4. 生成能力向量（用于语义搜索）
        embedding = await embed_model.embed(
            f"{card['display_name']} {card['description']} {' '.join(card['tags'])}"
        )
        
        # 5. 入库（pending 状态）
        await db.insert_agent(card, image, embedding, status="pending_review")
        return {"status": "pending_review", "estimated_review": "24h"}
```

### 4.2 语义搜索：用自然语言找 Agent

```python
@app.get("/v1/agents/search")
async def search_agents(q: str, category: str = None, limit: int = 10):
    """语义搜索 + 过滤"""
    # 1. 将查询转为向量
    query_vec = await embed_model.embed(q)
    
    # 2. pgvector 相似度搜索
    sql = """
        SELECT id, name, display_name, description, quality_score, downloads,
               capability_embedding <=> $1 AS distance
        FROM agents 
        WHERE status = 'active'
    """
    params = [query_vec]
    if category:
        sql += " AND category = $2"
        params.append(category)
    sql += " ORDER BY distance LIMIT $" + str(len(params) + 1)
    params.append(limit)
    
    results = await db.fetch(sql, *params)
    return {"agents": results, "total": len(results)}
```

### 4.3 能力匹配：根据任务自动推荐 Agent

```python
RECOMMEND_PROMPT = """分析以下用户任务，提取关键能力需求：

任务：{task}

返回 JSON：{{"required_capabilities": ["能力1", "能力2"], "category": "分类"}}"""

async def recommend_agent(task: str, llm, top_k: int = 5) -> list[dict]:
    """LLM 分析任务 → 提取能力需求 → 匹配 Agent"""
    # 1. LLM 提取能力需求
    analysis = await llm.ainvoke(RECOMMEND_PROMPT.format(task=task))
    needs = json.loads(analysis)
    
    # 2. 用能力需求做语义搜索
    agents = await search_agents(
        q=" ".join(needs["required_capabilities"]),
        category=needs.get("category"),
        limit=top_k
    )
    
    return agents
```

### 4.4 版本管理：语义化版本与灰度发布

```
版本管理规则：

  1.2.0 → 1.2.1   补丁（Bug 修复，向后兼容）
  1.2.0 → 1.3.0   次版本（新功能，向后兼容）
  1.2.0 → 2.0.0   主版本（Breaking Change）

  灰度发布策略：
    新版本上线 → 10% 流量 → 观察 24h
    质量指标不下降 → 50% → 100%
    质量下降 → 自动回滚到旧版本
```

### 4.5 Agent 依赖：Agent 调用 Agent

```json
{
  "name": "expense-report-agent",
  "dependencies": {
    "agents": [
      {"name": "invoice-analyzer", "version": ">=1.0.0"},
      {"name": "currency-converter", "version": ">=2.1.0"}
    ]
  }
}
```

> 💡 **依赖解析**：和 npm 一样，Marketplace 需要解决依赖冲突（A 依赖 B v1，C 依赖 B v2）。初期可以采用"扁平依赖"策略——所有 Agent 独立运行，通过 API 调用而非代码引用。

---

## 5. 权限与安全：第三方 Agent 的信任模型

第三方 Agent 最大的问题是**信任**——它会不会读我的数据？会不会调用不该调的 API？本章设计 Marketplace 的安全架构。

### 5.1 Capability-based 权限模型

```
权限设计原则：Agent 只能做它在 Agent Card 中声明的事情。

  Agent Card 声明：
    "requires_network": true          → 允许访问网络
    "requires_filesystem": false      → 禁止访问文件系统
    "allowed_domains": ["api.openai.com"]  → 只能访问这些域名
    "max_memory_mb": 512              → 最大内存 512MB
    "max_execution_time_s": 60        → 最长执行 60 秒

  运行时强制执行：
    Docker 网络策略 + cgroups 资源限制 + seccomp 系统调用过滤
```

```python
from pydantic import BaseModel

class AgentPermissions(BaseModel):
    network: bool = False
    filesystem: bool = False
    allowed_domains: list[str] = []
    max_memory_mb: int = 256
    max_cpu_percent: int = 50
    max_execution_s: int = 60
    allowed_env_vars: list[str] = []

def enforce_permissions(permissions: AgentPermissions) -> dict:
    """将权限声明转为 Docker 运行参数"""
    docker_config = {
        "mem_limit": f"{permissions.max_memory_mb}m",
        "cpu_quota": permissions.max_cpu_percent * 1000,
        "network_mode": "none" if not permissions.network else "bridge",
        "read_only": not permissions.filesystem,
        "security_opt": ["no-new-privileges"],
    }
    return docker_config
```

### 5.2 沙箱隔离：Docker / Firecracker / E2B

| 方案 | 隔离级别 | 启动速度 | 资源开销 | 适用 |
|:---|:---|:---|:---|:---|
| **Docker** | 进程级 | ~1s | 低 | 可信 Agent |
| **gVisor** | 系统调用拦截 | ~2s | 中 | 半可信 Agent |
| **Firecracker** | microVM | ~125ms | 中 | 不可信 Agent |
| **E2B** | 云端沙箱 | ~3s | 高（托管） | 代码执行型 Agent |

### 5.3 数据隔离与租户安全

```
租户数据隔离策略：

  每次 Agent 调用 = 一个独立的容器实例
  ├── 独立的文件系统（tmpfs，销毁即清除）
  ├── 独立的网络命名空间
  ├── 无法访问其他租户的数据
  └── 日志和执行记录仅对调用者可见

  敏感数据处理：
    用户输入中的 PII → 在进入沙箱前脱敏
    Agent 输出中的 PII → 在返回前扫描和告警
```

### 5.4 安全审查清单与自动化扫描

```
上架前安全检查（自动化）：

  ✅ 静态代码扫描（Bandit / Semgrep）
  ✅ 依赖漏洞检查（Trivy / Snyk）
  ✅ Docker 镜像安全扫描
  ✅ Prompt 注入测试（10 条对抗样本）
  ✅ 网络行为审计（是否有非声明的外部请求）
  ✅ 资源使用检查（内存/CPU 是否在声明范围内）
```

### 5.5 信任等级：未验证 → 社区验证 → 官方认证

| 等级 | 标记 | 条件 | 权限范围 |
|:---|:---|:---|:---|
| **未验证** | ⬜ | 通过自动校验 | 无网络、256MB 内存、30s 超时 |
| **社区验证** | 🟢 | 100+ 次调用 + 4.0+ 评分 + 无安全事件 | 有网络、512MB、60s |
| **官方认证** | ✅ | 人工深度审查 + 安全审计 | 完整权限、1GB、120s |

> 💡 **信任是挣来的**。新上架的 Agent 默认最低权限——用调用量和好评"升级"信任等级。这和 App Store 的审核逻辑一致。

---

## 6. 计费与结算：Agent 经济体系

Marketplace 不只是技术平台——它是一个**经济系统**。好的计费模型让开发者有动力做好 Agent，让调用者付得起、用得值。

### 6.1 定价模型：按次 / Token / 订阅 / 免费增值

```
四种 Agent 定价模型：

  按次计费（Pay-per-call）
    每次调用 $0.01-$1.00
    适合：低频、高价值任务（如发票分析）

  按 Token 计费（Token-based）
    $X / 百万 Token（与底层 LLM 成本挂钩）
    适合：对话型 Agent、文本生成 Agent

  订阅制（Subscription）
    $9.99/月 无限调用（有 QPS 限制）
    适合：高频使用的工具型 Agent

  免费增值（Freemium）
    每月 100 次免费 → 超出收费
    适合：拉新、建立用户基础
```

### 6.2 用量计量与成本归因

```python
class UsageRecord(BaseModel):
    user_id: str
    agent_id: str
    timestamp: datetime
    tokens_input: int
    tokens_output: int
    execution_time_s: float
    cost_llm: float          # 底层 LLM 成本
    cost_compute: float      # 计算资源成本
    price_charged: float     # 向用户收取的价格
    developer_share: float   # 开发者分成

class BillingService:
    async def record(self, usage: UsageRecord):
        # 写入用量表
        await db.insert("usage_records", usage.dict())
        
        # 更新实时余额
        await self.redis.incrbyfloat(
            f"balance:{usage.user_id}", -usage.price_charged
        )
        
        # 检查余额告警
        balance = await self.redis.get(f"balance:{usage.user_id}")
        if float(balance) < 1.0:
            await notify(usage.user_id, "余额不足 $1.00，请充值")
```

### 6.3 收入分成与开发者结算

```
收入分成模型：

  用户支付 $1.00
  ├── 平台抽成: 20%  → $0.20（运维、审核、基础设施）
  ├── 开发者:   70%  → $0.70
  └── LLM 成本: 10%  → $0.10（底层模型 API 费用）

  结算周期：月结
  最低提现：$50
  支付方式：Stripe / PayPal / 银行转账
```

### 6.4 免费额度与试用机制

```python
FREE_TIER = {
    "calls_per_month": 100,     # 每月 100 次免费调用
    "tokens_per_month": 50000,  # 每月 5 万 Token
    "agents_can_publish": 3,    # 最多发布 3 个 Agent
}

async def check_free_tier(user_id: str, agent_id: str) -> bool:
    """检查是否在免费额度内"""
    month_key = f"usage:{user_id}:{datetime.now().strftime('%Y-%m')}"
    current = await redis.hget(month_key, "calls") or 0
    return int(current) < FREE_TIER["calls_per_month"]
```

> 💡 **定价建议**：初期所有 Agent 提供 100 次免费试用——降低使用门槛比赚钱更重要。等用户量起来后再优化定价策略。

---

## 7. 质量评审与排名

App Store 的核心竞争力是审核质量——Marketplace 也一样。本章设计 Agent 的质量管控与排名体系。

### 7.1 上架审查：自动化检查 + 人工审核

```
审查流水线：

  自动化（必须全过）             人工（抽查）
  ─────────────────           ──────────────
  ✅ Agent Card Schema 合法    📋 描述是否准确
  ✅ Docker 镜像构建成功        📋 是否与已有 Agent 重复
  ✅ 3 条冒烟测试通过           📋 定价是否合理
  ✅ 安全扫描无高危漏洞         📋 文档是否完整
  ✅ 响应时间 < 60s             📋 输出质量人工评估
  ✅ 无 Prompt 注入风险
```

### 7.2 质量指标体系：成功率 × 延迟 × 成本 × 安全

```python
class QualityMetrics:
    """Agent 质量指标（持续更新）"""
    
    def calculate(self, agent_id: str, days: int = 30) -> dict:
        records = self.get_records(agent_id, days)
        
        success_rate = sum(1 for r in records if r.success) / max(len(records), 1)
        avg_latency = sum(r.latency_s for r in records) / max(len(records), 1)
        avg_cost = sum(r.cost for r in records) / max(len(records), 1)
        
        # 综合质量分（0-5）
        quality_score = (
            success_rate * 2.5 +                          # 成功率权重最高
            min(1, 10 / max(avg_latency, 0.1)) * 1.0 +   # 延迟越低越好
            min(1, 0.05 / max(avg_cost, 0.001)) * 0.5 +   # 成本越低越好
            self.safety_score(agent_id) * 1.0              # 安全分
        )
        
        return {
            "quality_score": min(quality_score, 5.0),
            "success_rate": success_rate,
            "avg_latency_s": avg_latency,
            "avg_cost_usd": avg_cost,
            "total_calls": len(records),
        }
```

### 7.3 排名算法与推荐系统

```python
def ranking_score(agent: dict) -> float:
    """排名分 = 质量 × 活跃度 × 口碑"""
    quality = agent["quality_score"] / 5.0          # 0-1
    activity = min(agent["total_calls"] / 1000, 1)  # 调用量归一化
    reputation = agent["avg_rating"] / 5.0          # 用户评分
    freshness = recency_boost(agent["updated_at"])  # 新更新加分
    
    return quality * 0.4 + activity * 0.2 + reputation * 0.3 + freshness * 0.1
```

### 7.4 用户评价与反馈闭环

```python
class AgentReview(BaseModel):
    user_id: str
    agent_id: str
    rating: int              # 1-5 星
    comment: str
    usage_count: int         # 该用户累计使用次数（防刷评）
    verified_purchase: bool  # 是否真正调用过

@app.post("/v1/agents/{agent_id}/reviews")
async def submit_review(agent_id: str, review: AgentReview):
    # 只允许实际调用过的用户评价
    if review.usage_count < 3:
        raise HTTPException(403, "至少使用 3 次后才能评价")
    
    await db.insert("reviews", review.dict())
    # 更新 Agent 平均评分
    await update_avg_rating(agent_id)
```

### 7.5 下架与违规处理

```
下架触发条件：

  自动下架：
    🔴 成功率连续 7 天 < 50%
    🔴 安全扫描发现高危漏洞
    🔴 被 3 个以上用户举报安全问题

  人工下架：
    🟡 描述严重不符实际功能
    🟡 恶意定价（声称免费但暗中收费）
    🟡 抄袭其他开发者的 Agent
    
  申诉流程：
    下架通知 → 开发者修复 → 重新提交 → 重新审核
```

> 💡 **质量是 Marketplace 的命脉**。一个充斥低质量 Agent 的市场，用户会很快流失。宁可上架慢一天，也不放过一个有问题的 Agent。

---

## 8. 开发者体验：Agent SDK 与开发者门户

好的 Marketplace 让开发者"爽"——从开发到发布只需 5 分钟。

### 8.1 Agent SDK：一行代码发布 Agent

```python
# pip install agent-marketplace-sdk

from agent_sdk import Agent, tool, publish

@Agent(
    name="invoice-analyzer",
    description="自动识别和提取 PDF 发票中的关键信息",
    version="1.0.0",
    pricing={"model": "per_call", "price": 0.02},
)
class InvoiceAnalyzer:
    
    @tool("ocr_service")
    async def analyze(self, file_url: str, file_type: str = "pdf") -> dict:
        """分析发票，提取关键信息"""
        # 1. 下载文件
        content = await download(file_url)
        # 2. OCR 识别
        text = await self.ocr_service.extract_text(content)
        # 3. LLM 提取结构化信息
        result = await self.llm.extract(text, schema=InvoiceSchema)
        return result.dict()

# 一行发布
publish(InvoiceAnalyzer)
```

### 8.2 CLI 工具：publish / test / logs

```bash
# 初始化 Agent 项目
$ agent init my-agent
✅ 创建 agent_card.json, Dockerfile, README.md

# 本地测试
$ agent test --input '{"file_url": "test.pdf"}'
✅ 测试通过 (1.2s, 成功)

# 发布到 Marketplace
$ agent publish
📦 构建镜像... ✅
🔍 安全扫描... ✅
🧪 冒烟测试... ✅ (3/3 通过)
📤 提交审核... ✅
⏳ 等待人工审核（预计 24h 内）

# 查看线上日志
$ agent logs invoice-analyzer --last 100
2026-05-03 10:23:01 | ✅ 成功 | 1.3s | $0.018
2026-05-03 10:24:15 | ✅ 成功 | 0.9s | $0.012
2026-05-03 10:25:33 | ❌ 失败 | 超时 | $0.000

# 查看收入
$ agent revenue --month 2026-05
总调用: 1,250 次
总收入: $25.00
已结算: $17.50
待结算: $7.50
```

### 8.3 开发者门户：Dashboard 与 Analytics

```
开发者 Dashboard 核心页面：

┌──────────────────────────────────────────┐
│  📊 My Agents                            │
│  ┌────────┬────────┬────────┬──────────┐ │
│  │ Agent  │ 调用量  │ 成功率  │ 收入     │ │
│  ├────────┼────────┼────────┼──────────┤ │
│  │ 发票   │ 1,250  │ 96.2%  │ $25.00   │ │
│  │ 翻译   │   890  │ 94.5%  │ $8.90    │ │
│  │ 摘要   │   340  │ 91.1%  │ $3.40    │ │
│  └────────┴────────┴────────┴──────────┘ │
│                                          │
│  📈 30 天趋势图                           │
│  ▃▅▇▆▇█▇▆▅▇█▇▆▇█▇▅▆▇█▇▆▅▃▅▇▆▇█▇     │
│                                          │
│  ⚠️ 告警：「翻译 Agent」成功率下降 3%       │
└──────────────────────────────────────────┘
```

### 8.4 本地开发与调试环境

```bash
# 启动本地 Marketplace 模拟环境
$ agent dev
🚀 本地 Marketplace 启动: http://localhost:8080
📋 已加载 Agent: invoice-analyzer v1.0.0
🔧 热重载已开启

# 在另一个终端调用
$ curl -X POST http://localhost:8080/v1/agents/invoice-analyzer/invoke \
  -H "Content-Type: application/json" \
  -d '{"file_url": "test.pdf"}'
```

> 💡 **开发者体验决定生态繁荣**。如果发布一个 Agent 需要 2 小时配环境，没人愿意来。目标是"5 分钟从零到上架"。

---

## 9. 调用者体验：Agent 编排与组合

开发者发布 Agent 是供给侧，调用者使用 Agent 是需求侧。好的调用体验 = 简单安装 + 灵活编排。

### 9.1 安装与调用：像 npm install 一样简单

```python
# pip install agent-marketplace-sdk

from agent_sdk import MarketplaceClient

client = MarketplaceClient(api_key="your-key")

# 搜索 Agent
agents = await client.search("分析 PDF 发票")
print(agents[0].name)  # "invoice-analyzer"

# 直接调用
result = await client.invoke(
    agent="invoice-analyzer",
    input={"file_url": "https://example.com/invoice.pdf"}
)
print(result)
# {"invoice_number": "INV-2026-001", "amount": 1500.00, "vendor": "..."}
```

### 9.2 多 Agent 编排：串行 / 并行 / 条件分支

```python
from agent_sdk import Pipeline, parallel, condition

# 串行：翻译 → 摘要
pipeline = Pipeline([
    ("translator", {"text": "{input}", "target_lang": "zh"}),
    ("summarizer", {"text": "{translator.output}"}),
])

# 并行：同时分析多个文件
results = await parallel([
    client.invoke("invoice-analyzer", {"file_url": url})
    for url in file_urls
])

# 条件分支
async def smart_analyzer(file_url: str):
    file_type = detect_file_type(file_url)
    
    if file_type == "pdf":
        return await client.invoke("invoice-analyzer", {"file_url": file_url})
    elif file_type == "image":
        return await client.invoke("ocr-agent", {"image_url": file_url})
    else:
        return await client.invoke("text-extractor", {"file_url": file_url})
```

### 9.3 与 LangGraph / CrewAI 集成

```python
from langgraph.graph import StateGraph
from agent_sdk import MarketplaceClient

client = MarketplaceClient(api_key="your-key")

# 将 Marketplace Agent 包装为 LangGraph 节点
async def marketplace_node(state: dict) -> dict:
    result = await client.invoke(
        agent=state["agent_name"],
        input=state["agent_input"]
    )
    return {"agent_output": result}

# 构建 LangGraph 工作流
graph = StateGraph(dict)
graph.add_node("analyze", marketplace_node)
graph.add_node("summarize", marketplace_node)
graph.add_edge("analyze", "summarize")
```

### 9.4 Fallback 与降级策略

```python
class AgentWithFallback:
    """带降级的 Agent 调用"""
    
    def __init__(self, primary: str, fallback: str, client: MarketplaceClient):
        self.primary = primary
        self.fallback = fallback
        self.client = client
    
    async def invoke(self, input: dict, timeout: int = 30) -> dict:
        try:
            return await asyncio.wait_for(
                self.client.invoke(self.primary, input), timeout=timeout
            )
        except (asyncio.TimeoutError, Exception) as e:
            print(f"⚠️ {self.primary} 失败，降级到 {self.fallback}")
            return await self.client.invoke(self.fallback, input)

# 使用
analyzer = AgentWithFallback(
    primary="invoice-analyzer-pro",    # 首选（贵但准）
    fallback="invoice-analyzer-lite",  # 降级（便宜但简单）
    client=client
)
```

> 💡 **编排是 Marketplace 的杀手级特性**。单个 Agent 的价值有限，但 N 个 Agent 可以组合出 N² 种工作流——这才是平台的网络效应。

---

## 10. 生态展望：Agent 经济的未来

Agent Marketplace 不是终点，而是 Agent 生态的起点。本章分析现有平台、展望未来趋势。

### 10.1 现有平台横评：GPT Store / Coze / Dify / HuggingFace

| 平台 | 定位 | Agent 数量 | 计费 | 开放程度 | 局限性 |
|:---|:---|:---|:---|:---|:---|
| **GPT Store** | OpenAI 生态 | 300万+ | 免费（含在 Plus） | 封闭（仅 GPT） | 无法自部署、无 API |
| **Coze Bot Store** | 字节跳动生态 | 10万+ | 免费/按量 | 半开放 | 强绑定 Coze 平台 |
| **Dify Marketplace** | 开源社区 | 5000+ | 自定义 | 完全开放 | 生态还小、缺乏质量管控 |
| **HuggingFace Spaces** | ML 社区 | 50万+ | 免费/GPU 付费 | 完全开放 | 偏 Demo、非生产级 |

```
现有平台的共同问题：

  1. 缺乏标准化
     每个平台的 Agent 格式不同，无法互通
     → 在 GPT Store 发布的 Agent，无法在 Dify 上用

  2. 质量参差不齐
     大部分 Agent 是"玩具级"，缺乏生产级质量管控
     → 找到一个真正好用的 Agent 像大海捞针

  3. 缺乏经济激励
     GPT Store 没有开发者分成 → 没人认真做
     → 好的开发者没有动力把 Agent 做到极致

  4. 缺乏安全保障
     第三方 Agent 的安全性完全靠信任
     → 企业不敢用、不能用
```

### 10.2 互操作标准：A2A + MCP 的生态角色

```
Agent 生态的标准化层次：

  Layer 1: 工具层（MCP）
    标准化 Agent 调用工具的方式
    "不管什么 Agent，都用同样的方式调用工具"

  Layer 2: 通信层（A2A）
    标准化 Agent 之间的通信协议
    "不管什么 Agent，都能互相对话和协作"

  Layer 3: 分发层（Marketplace）
    标准化 Agent 的注册、发现、信任和交易
    "不管什么 Agent，都能在同一个市场上架和使用"

  三层结合 = Agent 生态的完整基础设施
```

### 10.3 Agent 组合爆炸：N 个 Agent → N² 种工作流

```
Agent 组合的网络效应：

  10 个 Agent → 45 种双 Agent 组合
  50 个 Agent → 1,225 种组合
  100 个 Agent → 4,950 种组合
  1000 个 Agent → 499,500 种组合

  示例组合：
    发票分析 + 翻译 → 多语言发票处理
    代码审查 + 安全扫描 → 安全代码审查
    数据分析 + 报告生成 + 邮件发送 → 自动化周报
    
  这就是为什么 Marketplace 有平台效应：
  每新增一个 Agent，对所有已有 Agent 的调用者都有价值
```

### 10.4 商业模式演进与技术挑战

```
商业模式演进路径：

  Phase 1: 工具（2024-2025）
    单个 Agent 解决单个问题
    商业模式：SaaS 订阅
    
  Phase 2: 平台（2025-2026）
    Marketplace 连接 Agent 供需
    商业模式：平台抽成 + 增值服务

  Phase 3: 生态（2027+）
    Agent 自主发现、协商、交易
    商业模式：基础设施 + 金融服务

技术挑战：
  ⚠️ Agent 质量评估的标准化
  ⚠️ 多 Agent 编排的可靠性保障
  ⚠️ Agent 间通信的安全与隐私
  ⚠️ 计费公平性（底层模型成本不透明）
  ⚠️ Agent 版本兼容性管理
```

### 10.5 Agent 经济的未来方向

```
未来 3 年的关键趋势：

  2026：标准化之年
    A2A + MCP 成为事实标准
    跨平台 Agent 互操作成为可能

  2027：专业化之年
    垂直行业 Marketplace 出现（医疗/金融/法律）
    企业内部 Marketplace 普及

  2028：自治之年
    Agent 能自主在 Marketplace 注册和交易
    Agent 经济开始自我演化
```

> 💡 **最后一句话**：Agent Marketplace 的终极形态不是"人去商店找 Agent"，而是"Agent 自己去商店找 Agent"——当你的 Agent 遇到它不会的任务时，它自动在 Marketplace 搜索、比价、调用合适的 Agent 来帮忙。这才是真正的 Agent 经济。
