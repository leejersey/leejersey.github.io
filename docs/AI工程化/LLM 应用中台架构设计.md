# LLM 应用中台架构设计

> 从单体应用到企业中台：掌握 API 网关→业务层→模型底座→存储层的四层中台架构、多租户隔离、灰度发布、企业级知识库架构与生产运维体系。

---

## 1. 为什么需要 LLM 中台

单个 AI 应用可以"烟囱式"开发，但当企业有 5 个以上 AI 应用时，模型管理、Prompt 管理、知识库、计费、监控全部重复建设——中台就是解决这个问题。

### 1.1 烟囱式开发 vs 中台化

```
烟囱式开发（每个应用独立）：

  应用 A          应用 B          应用 C
  ├── LLM 调用    ├── LLM 调用    ├── LLM 调用
  ├── Prompt 管理  ├── Prompt 管理  ├── Prompt 管理
  ├── 知识库       ├── 知识库       ├── 知识库
  ├── 用户管理     ├── 用户管理     ├── 用户管理
  └── 监控告警     └── 监控告警     └── 监控告警
  → 每个应用重复建设相同基础设施
  → 模型升级要改 N 个应用
  → 成本无法统一管控

中台化（共享基础设施）：

  应用 A    应用 B    应用 C
     \        |        /
      \       |       /
       ▼      ▼      ▼
  ┌──────────────────────┐
  │     LLM 应用中台      │
  │  统一网关 / 模型管理   │
  │  Prompt 库 / 知识库   │
  │  计费 / 监控 / 权限    │
  └──────────────────────┘
  → 基础设施复用，新应用快速接入
  → 模型升级一次生效全局
  → 成本统一管控
```

### 1.2 中台解决的核心问题

```
LLM 中台解决的 5 大问题：

  问题                      中台方案
  ──────────────────────────────────────────
  ① 模型管理混乱            统一模型注册 + 路由 + 降级
  ② Prompt 散落各处         Prompt 模板库 + 版本管理
  ③ 知识库重复建设           统一知识库平台 + 多租户
  ④ 成本不可控              统一计费 + Token 配额 + 告警
  ⑤ 质量无法监控            统一链路追踪 + 质量评测
```

---

## 2. 四层中台架构设计（面试核心）

### 2.1 架构全景图

```
LLM 应用中台四层架构：

  ┌─────────────────────────────────────────────┐
  │              ① 接入层（API Gateway）          │
  │  统一API / 鉴权认证 / 限流熔断 / 协议适配     │
  └──────────────────┬──────────────────────────┘
  ┌──────────────────┴──────────────────────────┐
  │              ② 业务层（Service Layer）        │
  │  Agent 服务 / RAG 服务 / 对话服务 / Workflow  │
  └──────────────────┬──────────────────────────┘
  ┌──────────────────┴──────────────────────────┐
  │              ③ 模型底座层（Model Layer）      │
  │  LLM 路由 / Embedding 服务 / Rerank 服务     │
  │  模型注册 / 负载均衡 / 降级策略               │
  └──────────────────┬──────────────────────────┘
  ┌──────────────────┴──────────────────────────┐
  │              ④ 存储层（Storage Layer）        │
  │  向量库 / 关系库 / 缓存 / 对象存储 / 消息队列  │
  └─────────────────────────────────────────────┘
```

### 2.2 接入层：API 网关设计

```python
# ═══════════════════════════════════════
# 统一 API 网关
# ═══════════════════════════════════════
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LLM 中台 API")

# 统一鉴权
async def verify_api_key(api_key: str = Header(...)):
    tenant = await get_tenant_by_key(api_key)
    if not tenant:
        raise HTTPException(401, "无效的 API Key")
    if tenant.quota_remaining <= 0:
        raise HTTPException(429, "Token 配额已用完")
    return tenant

# 统一 API 入口
@app.post("/v1/chat/completions")
async def chat(request: ChatRequest, tenant = Depends(verify_api_key)):
    """兼容 OpenAI API 格式"""
    # 路由到具体的模型服务
    result = await model_router.invoke(
        model=request.model,
        messages=request.messages,
        tenant_id=tenant.id,
    )
    # 记录用量
    await billing.record(tenant.id, result.usage)
    return result
```

### 2.3 业务层：核心服务

```
业务层四大核心服务：

  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Agent    │  │ RAG      │  │ 对话     │  │ Workflow │
  │ 服务     │  │ 服务     │  │ 服务     │  │ 服务     │
  │          │  │          │  │          │  │          │
  │ 工具调用  │  │ 知识库    │  │ 多轮对话  │  │ 流程编排  │
  │ 推理循环  │  │ 检索生成  │  │ 记忆管理  │  │ 节点执行  │
  └──────────┘  └──────────┘  └──────────┘  └──────────┘

  每个服务独立部署、独立扩容
  → Agent 服务调用量大 → 单独扩 3 个副本
  → RAG 服务计算密集 → 给更多 CPU/内存
```

### 2.4 模型底座层：统一模型管理

```python
# ═══════════════════════════════════════
# 模型路由器
# ═══════════════════════════════════════

class ModelRouter:
    """统一模型路由 + 负载均衡 + 降级"""

    def __init__(self):
        self.models = {}  # {name: [endpoint1, endpoint2]}
        self.fallbacks = {}  # {name: fallback_name}

    def register(self, name: str, endpoints: list, fallback: str = None):
        self.models[name] = endpoints
        if fallback:
            self.fallbacks[name] = fallback

    async def invoke(self, model: str, messages: list, **kwargs):
        endpoints = self.models.get(model, [])

        for endpoint in endpoints:
            try:
                return await endpoint.call(messages, **kwargs)
            except Exception as e:
                print(f"[WARN] {model}@{endpoint} 失败: {e}")

        # 所有端点失败 → 降级到备选模型
        fallback = self.fallbacks.get(model)
        if fallback:
            print(f"[INFO] 降级: {model} → {fallback}")
            return await self.invoke(fallback, messages, **kwargs)

        raise Exception(f"模型 {model} 所有端点和降级都失败")
```

### 2.5 存储层：多引擎协作

```
存储层选型：

  存储引擎          用途                    典型产品
  ──────────────────────────────────────────────────
  向量数据库        Embedding 存储与检索     Qdrant / Milvus
  关系数据库        用户/租户/配置/计费      PostgreSQL
  缓存              会话/语义缓存           Redis
  对象存储          文档原文/图片/音频       MinIO / S3
  消息队列          异步任务/事件驱动       Redis Stream / RabbitMQ
```

---

## 3. 多租户架构

### 3.1 租户隔离设计

```
多租户隔离策略：

  隔离级别        实现方式                    适用场景
  ──────────────────────────────────────────────────
  逻辑隔离        tenant_id 字段过滤          SaaS 平台
  Schema 隔离     每个租户独立 Schema         中等安全需求
  实例隔离        每个租户独立数据库实例       金融/政务

  推荐：逻辑隔离 + 向量库 Collection 隔离

  ┌──────────────────────────────────┐
  │         统一中台服务               │
  └──┬──────────┬──────────┬────────┘
     │          │          │
     ▼          ▼          ▼
  ┌────────┐┌────────┐┌────────┐
  │租户 A   ││租户 B   ││租户 C   │
  │Collection││Collection││Collection│
  │知识库    ││知识库    ││知识库    │
  └────────┘└────────┘└────────┘
```

### 3.2 配额与计费

```python
# ═══════════════════════════════════════
# 租户配额管理
# ═══════════════════════════════════════

class TenantQuota:
    """租户 Token 配额管理"""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def check_and_deduct(self, tenant_id: str, tokens: int) -> bool:
        """检查并扣减配额"""
        key = f"quota:{tenant_id}:monthly"
        remaining = await self.redis.get(key)

        if remaining is None:
            return False
        if int(remaining) < tokens:
            return False

        await self.redis.decrby(key, tokens)
        return True

    async def get_usage(self, tenant_id: str) -> dict:
        """获取用量统计"""
        used = await self.redis.get(f"usage:{tenant_id}:monthly")
        total = await self.redis.get(f"quota:{tenant_id}:monthly")
        return {
            "used": int(used or 0),
            "total": int(total or 0),
            "remaining": int(total or 0) - int(used or 0),
        }
```

---

## 4. 灰度发布与模型管理

### 4.1 灰度发布策略

```
模型灰度发布流程：

  场景：把 GPT-4o 从 v1 升级到 v2

  Phase 1: 内部测试（0%）
  → 只有内部测试账号走 v2
  → 对比 v1 和 v2 的输出质量

  Phase 2: 小流量灰度（5%）
  → 5% 用户请求走 v2，95% 走 v1
  → 监控错误率、延迟、用户反馈

  Phase 3: 扩大灰度（30%）
  → 确认无问题后扩大比例
  → 持续监控

  Phase 4: 全量切换（100%）
  → 全部切到 v2，保留 v1 回滚能力
```

### 4.2 模型版本管理

```python
# ═══════════════════════════════════════
# 灰度路由
# ═══════════════════════════════════════

class GrayRouter:
    """灰度发布路由"""

    def __init__(self):
        self.rules = {}  # {model: {new_version, percentage, whitelist}}

    def set_gray(self, model: str, new_version: str,
                 percentage: int, whitelist: list[str] = None):
        self.rules[model] = {
            "new_version": new_version,
            "percentage": percentage,
            "whitelist": whitelist or [],
        }

    def route(self, model: str, tenant_id: str) -> str:
        """决定走新版还是旧版"""
        rule = self.rules.get(model)
        if not rule:
            return model

        # 白名单直接走新版
        if tenant_id in rule["whitelist"]:
            return rule["new_version"]

        # 按比例灰度
        if hash(tenant_id) % 100 < rule["percentage"]:
            return rule["new_version"]

        return model  # 走旧版
```

---

## 5. 企业级知识库架构

### 5.1 知识库全生命周期管理

```
知识库生命周期：

  创建 → 导入文档 → 解析入库 → 检索使用 → 增量更新 → 归档/删除

  ┌──────────────────────────────────────────┐
  │              知识库管理平台                │
  │                                          │
  │  ┌────────┐  ┌────────┐  ┌────────┐     │
  │  │ 文档管理 │  │ 分块配置 │  │ 检索测试 │     │
  │  └────────┘  └────────┘  └────────┘     │
  │  ┌────────┐  ┌────────┐  ┌────────┐     │
  │  │ 权限管理 │  │ 版本管理 │  │ 质量评测 │     │
  │  └────────┘  └────────┘  └────────┘     │
  └──────────────────────────────────────────┘
```

### 5.2 部门级知识库隔离

```
企业知识库隔离架构：

  公司级知识库（全员可见）
  ├── 公司制度
  ├── 产品手册
  └── FAQ

  部门级知识库（部门内可见）
  ├── 技术部 → 技术文档、架构设计
  ├── 销售部 → 客户资料、报价单
  └── 法务部 → 合同模板、法规库

  个人知识库（仅个人可见）
  ├── 个人笔记
  └── 工作日志

  权限模型：
  → 查询时自动合并：公司级 + 所属部门级 + 个人
  → 向量检索时加 tenant_id + department_id 过滤
```

---

## 6. 可观测性与运维

### 6.1 监控大盘设计

```
LLM 中台监控指标：

  业务指标：
  → 日活 API 调用量、按模型/租户分布
  → 平均响应时间（P50/P95/P99）
  → 错误率、超时率

  模型指标：
  → Token 消耗量（按模型/租户/应用）
  → 模型调用成功率
  → 降级触发次数

  成本指标：
  → 日/月 Token 费用
  → 各租户费用占比
  → 缓存命中率（节省了多少钱）

  质量指标：
  → RAG 检索命中率
  → 用户满意度评分
  → 幻觉率
```

### 6.2 链路追踪

```
完整调用链路（一次请求的生命周期）：

  API Gateway
  └── 鉴权 (2ms)
  └── 限流检查 (1ms)
  └── 路由分发 → RAG 服务
      └── 查询改写 (200ms, 50 tokens)
      └── 向量检索 (15ms)
      └── BM25 检索 (8ms)
      └── RRF 融合 (1ms)
      └── Rerank (120ms)
      └── Prompt 拼装 (1ms)
      └── LLM 生成 (1500ms, 800 tokens)
  └── 计费记录 (2ms)
  └── 响应返回
  总耗时: 1850ms, 总 Token: 850

  → 每步耗时和 Token 都要记录
  → 出问题时可以快速定位瓶颈
```

---

## 7. 面试高频题汇总

```
LLM 中台架构面试题 TOP 8：

  ❓ Q1: LLM 中台的四层架构是什么？
  → 接入层（网关）→ 业务层（Agent/RAG/对话）→ 模型底座 → 存储层

  ❓ Q2: 多租户怎么隔离？
  → 逻辑隔离（tenant_id）+ 向量库 Collection 隔离 + 配额管理

  ❓ Q3: 模型怎么做灰度发布？
  → 白名单 → 5% 小流量 → 30% 扩大 → 100% 全量，全程监控

  ❓ Q4: 模型调用失败怎么办？
  → 多端点重试 → 降级到备选模型 → 返回缓存结果 → 兜底提示

  ❓ Q5: Token 成本怎么控制？
  → 配额管理 + 语义缓存 + 小模型路由 + Batch API

  ❓ Q6: 知识库怎么做权限隔离？
  → 公司级/部门级/个人三层，检索时按权限合并过滤

  ❓ Q7: 中台的监控指标有哪些？
  → 业务指标（QPS/延迟/错误率）+ 模型指标（Token/成功率）+ 成本指标

  ❓ Q8: 中台和微服务的关系？
  → 中台是业务中台（复用AI能力），微服务是技术架构（服务拆分部署）
```

> 🎉 **全文完成**。LLM 中台的核心价值：**让 AI 能力从"各自为战"变成"统一供给"**。四层架构 + 多租户 + 灰度 + 知识库 + 可观测性，是企业级 AI 落地的基础设施。

---
