# AI 应用的可观测性

> 构建 LLM 应用的全链路可观测体系——调用追踪、Prompt 版本管理、质量评测、A/B 测试、成本监控，用 Langfuse + Prometheus 打造生产级 AI 应用监控大盘。

---

## 1. 为什么 AI 应用需要专属可观测性

### 1.1 传统 APM 不够用：缺少 Token、Prompt、质量维度

```
传统 APM（Datadog/New Relic）能监控什么：
  ✅ HTTP 延迟、错误率、吞吐量
  ✅ 数据库查询性能
  ✅ 内存/CPU 使用率

AI 应用还需要监控什么：
  ❌ 每次调用花了多少 Token（成本）
  ❌ 用了哪个 Prompt 版本（质量归因）
  ❌ 模型输出质量（幻觉/有害内容）
  ❌ RAG 检索的召回率和精度
  ❌ 不同模型的效果对比
```

### 1.2 AI 应用的五个监控维度：延迟/成本/质量/安全/使用

| 维度 | 关键指标 | 为什么重要 |
|:---|:---|:---|
| **延迟** | TTFT、P95 延迟 | 用户等不了 10 秒 |
| **成本** | Token/次、$/天 | 不控成本会破产 |
| **质量** | 幻觉率、满意度 | 输出垃圾就没人用 |
| **安全** | PII 泄露、注入攻击 | 出事就上新闻 |
| **使用** | DAU、调用量、留存 | 衡量产品价值 |

### 1.3 开源方案对比：Langfuse / LangSmith / Helicone

| 工具 | 类型 | 特点 | 价格 |
|:---|:---|:---|:---|
| **Langfuse** | 开源/自部署 | Trace + Prompt 管理 + 评测 | 免费（自部署） |
| LangSmith | 云服务 | LangChain 生态深度集成 | $39/月起 |
| Helicone | 云服务 | 代理模式、零代码接入 | 免费 10K 次 |
| Phoenix | 开源 | Arize 出品、可视化强 | 免费 |

### 1.4 可观测性架构：我们要构建什么

```
AI 可观测性全景架构：

  业务层
  ├── Langfuse SDK（调用追踪 + Prompt 管理）
  ├── 自定义评测（LLM-as-Judge）
  └── A/B 测试框架
          │
          ▼
  数据采集层
  ├── Langfuse Server（Trace 存储）
  ├── Prometheus（指标采集）
  └── PostgreSQL（日志 + 评测数据）
          │
          ▼
  展示层
  ├── Langfuse Dashboard（调用详情）
  ├── Grafana（监控大盘）
  └── 告警通知（飞书/Slack）
```

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **五维监控** | 延迟 + 成本 + 质量 + 安全 + 使用 |
| **Langfuse** | 开源首选，Trace + Prompt 管理 + 评测 |
| **传统 APM 不够** | 缺少 Token/Prompt/质量 维度 |

---

## 2. LLM 调用追踪：Trace 每一次对话

### 2.1 Trace 与 Span：追踪一次完整的 AI 调用链

```
Trace 示例：一次 RAG 问答的完整调用链

  Trace: "用户提问：Python asyncio 怎么用"
  │
  ├── Span: 查询改写 (GPT-4o-mini, 50ms, 120 tokens)
  │
  ├── Span: 向量检索 (Milvus, 30ms, 5 条结果)
  │
  ├── Span: Rerank (GPT-4o-mini, 80ms, 500 tokens)
  │
  └── Span: 答案生成 (GPT-4o, 2.3s, 1500 tokens)
       │
       ├── 输入: system prompt + context + 问题
       ├── 输出: 生成的答案
       ├── Token: prompt=800, completion=700
       └── 成本: $0.0095
```

### 2.2 Langfuse 快速集成：三行代码接入

```python
# pip install langfuse openai
from langfuse.openai import openai  # 替换 import，自动追踪

# 就这么简单！所有 OpenAI 调用自动上报到 Langfuse
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "你好"}],
)
```

```python
# 或者用装饰器方式，更灵活
from langfuse.decorators import observe, langfuse_context

@observe()
async def answer_question(question: str) -> str:
    # 自动创建 Trace
    langfuse_context.update_current_observation(
        metadata={"user_id": "user_123", "scene": "customer_service"}
    )
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": question}],
    )
    return response.choices[0].message.content
```

### 2.3 RAG 调用链追踪：检索 → Rerank → 生成

```python
from langfuse.decorators import observe

@observe()
async def rag_pipeline(question: str) -> str:
    """完整 RAG 流水线，每步自动追踪"""
    
    # Step 1: 查询改写
    query = await rewrite_query(question)
    
    # Step 2: 向量检索
    docs = await vector_search(query)
    
    # Step 3: Rerank
    ranked_docs = await rerank(question, docs)
    
    # Step 4: 生成答案
    answer = await generate_answer(question, ranked_docs)
    
    return answer

@observe()
async def rewrite_query(question: str) -> str:
    """查询改写（自动记录为子 Span）"""
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"改写查询: {question}"}],
    )
    return response.choices[0].message.content

@observe()
async def vector_search(query: str) -> list:
    """向量检索（自动记录为子 Span）"""
    results = await milvus.search(query, top_k=10)
    langfuse_context.update_current_observation(
        metadata={"result_count": len(results)}
    )
    return results
```

### 2.4 自定义 Span：追踪业务逻辑

```python
from langfuse import Langfuse

langfuse = Langfuse()

async def complex_workflow(question: str):
    trace = langfuse.trace(name="complex_workflow", user_id="user_123")
    
    # 自定义 Span：业务逻辑
    with trace.span(name="intent_detection") as span:
        intent = await detect_intent(question)
        span.update(output={"intent": intent})
    
    with trace.span(name="data_fetch") as span:
        data = await fetch_from_database(intent)
        span.update(metadata={"row_count": len(data)})
    
    # 记录 Generation（LLM 调用）
    generation = trace.generation(
        name="final_answer",
        model="gpt-4o",
        input={"question": question, "context": data},
    )
    answer = await llm_call(question, data)
    generation.end(output=answer, usage={"input": 500, "output": 300})
    
    trace.update(output={"answer": answer})
```

> 💡 **`@observe()` 装饰器是最省心的方案**——嵌套函数自动形成父子 Span，不需要手动管理 Trace ID。Langfuse 的装饰器模式比 LangSmith 的更 Pythonic。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Trace** | 一次完整请求的调用链 |
| **Span** | 调用链中的一个步骤 |
| **@observe()** | Langfuse 装饰器，自动追踪函数 |
| **Generation** | 专门追踪 LLM 调用的 Span |

---

## 3. Prompt 版本管理：像管代码一样管 Prompt

### 3.1 为什么 Prompt 需要版本管理

| 问题 | 解释 |
|:---|:---|
| 改了 Prompt 不知道效果变好还是变差 | 没有 A/B 对比 |
| 线上 Prompt 出问题想回滚 | 找不到上一版 |
| 团队协作冲突 | 谁改了什么不知道 |
| Prompt 散落在代码各处 | 改一个要发版 |

### 3.2 Langfuse Prompt Management 实战

```python
from langfuse import Langfuse

langfuse = Langfuse()

# 创建/更新 Prompt（在 Langfuse 控制台或 API）
langfuse.create_prompt(
    name="customer_service",
    prompt="你是一个专业客服。基于以下知识库内容回答用户问题：\n\n{{context}}\n\n用户问题：{{question}}",
    labels=["production"],          # 标签：production / staging / dev
    config={"model": "gpt-4o", "temperature": 0.3},
)

# 在代码中使用 Prompt（动态获取，无需发版）
async def answer_with_managed_prompt(question: str, context: str):
    prompt = langfuse.get_prompt("customer_service", label="production")
    
    compiled = prompt.compile(question=question, context=context)
    
    response = await client.chat.completions.create(
        model=prompt.config["model"],
        messages=[{"role": "user", "content": compiled}],
        temperature=prompt.config["temperature"],
    )
    return response.choices[0].message.content
```

### 3.3 Prompt 模板化：变量绑定与渲染

```python
class PromptTemplate:
    """Prompt 模板管理器"""
    
    def __init__(self, langfuse_client):
        self.langfuse = langfuse_client
        self._cache: dict[str, dict] = {}
    
    def get(self, name: str, label: str = "production") -> dict:
        cache_key = f"{name}:{label}"
        if cache_key not in self._cache:
            prompt = self.langfuse.get_prompt(name, label=label)
            self._cache[cache_key] = {
                "template": prompt.prompt,
                "config": prompt.config,
                "version": prompt.version,
            }
        return self._cache[cache_key]
    
    def render(self, name: str, **variables) -> str:
        prompt_data = self.get(name)
        template = prompt_data["template"]
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        return template

prompt_mgr = PromptTemplate(langfuse)
```

### 3.4 Prompt 灰度发布与快速回滚

```python
async def prompt_canary_deploy(prompt_name: str, new_version: str, traffic_pct: float = 0.1):
    """灰度发布：10% 流量用新 Prompt"""
    import random
    
    if random.random() < traffic_pct:
        prompt = langfuse.get_prompt(prompt_name, label="canary")
        variant = "canary"
    else:
        prompt = langfuse.get_prompt(prompt_name, label="production")
        variant = "production"
    
    # 记录使用的版本
    langfuse_context.update_current_observation(
        metadata={"prompt_variant": variant, "prompt_version": prompt.version}
    )
    return prompt
```

> 💡 **Prompt 管理最重要的是"改 Prompt 不需要改代码"**——代码里只写 `get_prompt("xxx")`，Prompt 内容在 Langfuse 控制台修改。改了可以灰度、可以回滚、可以对比效果。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Prompt 版本** | 每次修改自动生成新版本 |
| **标签** | production / staging / canary 区分环境 |
| **灰度发布** | 10% 流量用新 Prompt，对比效果 |
| **快速回滚** | 切换标签即回滚，秒级生效 |

---

## 4. 质量评测与在线评估

### 4.1 LLM-as-Judge：用大模型评大模型

```python
JUDGE_PROMPT = """评估以下 AI 回答的质量。

用户问题：{question}
AI 回答：{answer}
参考内容：{reference}

从三个维度打分（1-5 分）：
1. 相关性：回答是否针对问题
2. 忠实性：回答是否基于参考内容，没有编造
3. 完整性：回答是否全面

输出 JSON：{{"relevance": N, "faithfulness": N, "completeness": N, "explanation": "..."}}"""

async def llm_judge(question: str, answer: str, reference: str = "") -> dict:
    response = await client.chat.completions.create(
        model="gpt-4o",             # 用强模型做评测
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(
            question=question, answer=answer, reference=reference
        )}],
        response_format={"type": "json_object"},
        temperature=0,               # 评测要稳定
    )
    return json.loads(response.choices[0].message.content)
```

### 4.2 自动评分维度：相关性 / 忠实性 / 有害性

| 评分维度 | 评测方法 | 关注什么 |
|:---|:---|:---|
| 相关性 | LLM-as-Judge | 答案是否回答了问题 |
| 忠实性 | LLM-as-Judge | 有没有编造信息 |
| 有害性 | 分类模型 | 暴力/色情/歧视 |
| 格式 | 规则检查 | JSON 是否合法 |
| 延迟 | 计时 | 是否超时 |

### 4.3 人工标注：构建评测数据集

```python
from langfuse import Langfuse

langfuse = Langfuse()

# 创建评测数据集
dataset = langfuse.create_dataset(name="customer_service_eval_v1")

# 添加测试用例
langfuse.create_dataset_item(
    dataset_name="customer_service_eval_v1",
    input={"question": "你们支持退货吗？"},
    expected_output="支持 7 天无理由退货，商品需保持完好...",
)

# 批量运行评测
async def run_evaluation(dataset_name: str):
    dataset = langfuse.get_dataset(dataset_name)
    results = []
    
    for item in dataset.items:
        answer = await rag_pipeline(item.input["question"])
        score = await llm_judge(item.input["question"], answer, item.expected_output)
        
        # 记录评测结果
        item.link(trace_id=langfuse_context.get_current_trace_id())
        results.append(score)
    
    avg_scores = {
        "relevance": sum(r["relevance"] for r in results) / len(results),
        "faithfulness": sum(r["faithfulness"] for r in results) / len(results),
    }
    return avg_scores
```

### 4.4 在线评估：对每次调用实时打分

```python
from langfuse.decorators import observe

@observe()
async def answer_with_eval(question: str) -> dict:
    """每次调用后自动评分"""
    answer = await rag_pipeline(question)
    
    # 异步评分（不阻塞用户响应）
    asyncio.create_task(async_evaluate(question, answer))
    
    return {"answer": answer}

async def async_evaluate(question: str, answer: str):
    score = await llm_judge(question, answer)
    
    # 上报到 Langfuse
    langfuse.score(
        trace_id=langfuse_context.get_current_trace_id(),
        name="relevance",
        value=score["relevance"],
    )
    langfuse.score(
        trace_id=langfuse_context.get_current_trace_id(),
        name="faithfulness",
        value=score["faithfulness"],
    )
    
    # 低分告警
    if score["faithfulness"] < 3:
        await send_alert(f"⚠️ 低忠实度告警: {score}")
```

> 💡 **在线评估的关键是异步**——用户不能等你评完分再看到答案。`create_task` 后台评分，评完结果写入 Langfuse，在仪表盘实时看质量趋势。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **LLM-as-Judge** | 用 GPT-4o 给其他模型的输出打分 |
| **评测数据集** | 标准问答对，定期回归测试 |
| **在线评估** | 每次调用后台异步评分 |
| **低分告警** | 忠实度 < 3 分立即通知 |

---

## 5. A/B 测试：数据驱动的模型与 Prompt 优化

### 5.1 为什么需要 A/B 测试

| 场景 | 没有 A/B 测试 | 有 A/B 测试 |
|:---|:---|:---|
| 换模型 | "感觉 Claude 更好" | "Claude 忠实度 4.2 vs GPT 3.8" |
| 改 Prompt | "新版应该更好吧" | "新版相关性 +12%，成本 -8%" |
| 调参数 | "temperature 0.3 够了吧" | "0.3 比 0.7 幻觉率低 40%" |

### 5.2 模型 A/B 测试：GPT-4o vs Claude vs DeepSeek

```python
import random

class ABTest:
    """A/B 测试框架"""
    
    def __init__(self, experiment_name: str, variants: dict[str, float]):
        self.name = experiment_name
        self.variants = variants   # {"control": 0.5, "treatment": 0.5}
    
    def assign(self, user_id: str) -> str:
        # 基于 user_id 确定性分组（同一用户始终同组）
        hash_val = hash(f"{self.name}:{user_id}") % 100
        cumulative = 0
        for variant, weight in self.variants.items():
            cumulative += weight * 100
            if hash_val < cumulative:
                return variant
        return list(self.variants.keys())[-1]

# 定义实验
model_test = ABTest("model_comparison_v1", {
    "gpt-4o": 0.34,
    "claude-3-5": 0.33,
    "deepseek": 0.33,
})

async def answer_with_ab_test(question: str, user_id: str):
    variant = model_test.assign(user_id)
    model = variant  # 直接用 variant 名作为模型名
    
    response = await client.chat.completions.create(model=model, ...)
    
    # 记录实验数据
    langfuse_context.update_current_observation(
        metadata={"experiment": "model_comparison_v1", "variant": variant}
    )
    return response
```

### 5.3 Prompt A/B 测试：哪个 Prompt 更好

```python
prompt_test = ABTest("prompt_v2_test", {
    "production": 0.9,      # 90% 用现有 Prompt
    "canary": 0.1,          # 10% 用新 Prompt
})

async def answer_with_prompt_test(question: str, user_id: str):
    variant = prompt_test.assign(user_id)
    label = variant  # "production" 或 "canary"
    
    prompt = langfuse.get_prompt("customer_service", label=label)
    compiled = prompt.compile(question=question)
    
    response = await client.chat.completions.create(
        model=prompt.config["model"],
        messages=[{"role": "user", "content": compiled}],
    )
    
    langfuse_context.update_current_observation(
        metadata={"experiment": "prompt_v2_test", "variant": variant,
                  "prompt_version": prompt.version}
    )
    return response
```

### 5.4 统计显著性与决策

```python
from scipy import stats

def analyze_ab_test(control_scores: list[float], treatment_scores: list[float]) -> dict:
    """分析 A/B 测试结果"""
    t_stat, p_value = stats.ttest_ind(control_scores, treatment_scores)
    
    control_mean = sum(control_scores) / len(control_scores)
    treatment_mean = sum(treatment_scores) / len(treatment_scores)
    lift = (treatment_mean - control_mean) / control_mean * 100
    
    return {
        "control_mean": round(control_mean, 3),
        "treatment_mean": round(treatment_mean, 3),
        "lift": f"{lift:+.1f}%",
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
        "recommendation": "采用新版" if p_value < 0.05 and lift > 0 else "保持现有",
    }
```

> 💡 **用 user_id 做确定性分组**——同一个用户始终看到同一个版本，避免体验跳变。用 hash 分组比 random 更可靠。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **确定性分组** | 同一用户始终同组，用 hash 实现 |
| **灰度比例** | 新版先给 10%，验证后全量 |
| **p < 0.05** | 统计显著，结果可信 |

---

## 6. 成本与用量监控

### 6.1 Token 用量追踪：谁花了多少钱

```python
from langfuse.decorators import observe

@observe()
async def tracked_llm_call(question: str, user_id: str):
    """每次调用自动记录 Token 和成本"""
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": question}],
    )
    
    usage = response.usage
    cost = calculate_cost("gpt-4o", usage.prompt_tokens, usage.completion_tokens)
    
    # 上报
    langfuse_context.update_current_observation(
        metadata={"user_id": user_id, "cost_usd": cost},
        usage={"input": usage.prompt_tokens, "output": usage.completion_tokens},
    )
    return response
```

### 6.2 成本归因：按模型 / 用户 / 场景

```sql
-- 按模型统计本月成本（Langfuse 的 Trace 数据导出后分析）
SELECT 
    model,
    COUNT(*) as calls,
    SUM(usage_input + usage_output) as total_tokens,
    SUM(cost_usd) as total_cost
FROM traces
WHERE timestamp >= DATE_TRUNC('month', NOW())
GROUP BY model
ORDER BY total_cost DESC;

-- 按用户 Top 10
SELECT user_id, SUM(cost_usd) as cost
FROM traces
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY user_id
ORDER BY cost DESC
LIMIT 10;
```

### 6.3 异常检测与成本告警

```python
async def check_cost_anomaly(user_id: str, current_cost: float):
    """检测成本异常"""
    # 获取历史平均
    avg_daily_cost = await get_user_avg_daily_cost(user_id)
    
    if current_cost > avg_daily_cost * 3:
        await send_alert(
            f"⚠️ 成本异常告警\n"
            f"用户: {user_id}\n"
            f"今日成本: ${current_cost:.2f}\n"
            f"历史均值: ${avg_daily_cost:.2f}\n"
            f"倍率: {current_cost/avg_daily_cost:.1f}x"
        )
```

### 6.4 预算控制与自动熔断

```python
class BudgetGuard:
    """预算守卫：超预算自动熔断"""
    
    def __init__(self, daily_budget: float = 100.0):
        self.daily_budget = daily_budget
        self._today_cost = 0.0
    
    async def check(self, estimated_cost: float) -> bool:
        if self._today_cost + estimated_cost > self.daily_budget:
            await send_alert(f"🚫 预算耗尽！今日已花费 ${self._today_cost:.2f}")
            return False
        return True
    
    def record(self, cost: float):
        self._today_cost += cost

budget = BudgetGuard(daily_budget=50.0)
```

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **成本归因** | 按模型/用户/场景统计谁花了多少 |
| **异常检测** | 超过历史 3 倍均值立即告警 |
| **预算熔断** | 超预算自动拒绝请求 |

---

## 7. 监控大盘与告警体系

### 7.1 核心指标体系设计

| 类别 | 指标 | 类型 | 告警阈值 |
|:---|:---|:---|:---|
| 延迟 | TTFT（首字延迟） | Histogram | P95 > 3s |
| 延迟 | 端到端延迟 | Histogram | P95 > 10s |
| 成本 | 每小时 Token | Counter | > 500K/h |
| 成本 | 每小时费用 | Gauge | > $10/h |
| 质量 | 忠实度均分 | Gauge | < 3.5 |
| 质量 | 幻觉率 | Gauge | > 10% |
| 可用 | 错误率 | Counter | > 5% |
| 可用 | 降级率 | Counter | > 20% |

### 7.2 Prometheus 指标采集

```python
from prometheus_client import Counter, Histogram, Gauge

# LLM 调用指标
llm_requests = Counter("llm_requests_total", "Total LLM requests", ["model", "status"])
llm_latency = Histogram("llm_latency_seconds", "LLM latency", ["model"],
                         buckets=[0.5, 1, 2, 5, 10, 30])
llm_tokens = Counter("llm_tokens_total", "Tokens consumed", ["model", "type"])

# 质量指标
quality_score = Gauge("llm_quality_score", "Quality score (1-5)", ["dimension"])
hallucination_rate = Gauge("llm_hallucination_rate", "Hallucination rate")

# 成本指标
cost_total = Counter("llm_cost_usd_total", "Total cost in USD", ["model"])

# 中间件：自动采集
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    llm_latency.labels(model=request.state.model).observe(duration)
    llm_requests.labels(model=request.state.model, status="success").inc()
    return response
```

### 7.3 Grafana 看板搭建

```
推荐看板布局（4 行）：

  第 1 行：核心概览
  ┌──────────┬──────────┬──────────┬──────────┐
  │ 今日调用量 │ 今日成本   │ 平均延迟  │ 错误率    │
  │ 12,345   │ $42.30   │ 2.1s    │ 0.3%    │
  └──────────┴──────────┴──────────┴──────────┘

  第 2 行：趋势图
  ┌──────────────────────┬──────────────────────┐
  │ 调用量趋势（按小时）    │ 延迟趋势（P50/P95/P99）│
  └──────────────────────┴──────────────────────┘

  第 3 行：质量
  ┌──────────────────────┬──────────────────────┐
  │ 质量评分趋势           │ 幻觉率趋势            │
  └──────────────────────┴──────────────────────┘

  第 4 行：成本
  ┌──────────────────────┬──────────────────────┐
  │ 成本趋势（按模型）      │ Token 用量（按用户 Top10）│
  └──────────────────────┴──────────────────────┘
```

### 7.4 告警规则与通知

```yaml
# Prometheus 告警规则
groups:
  - name: llm_alerts
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, llm_latency_seconds) > 10
        for: 5m
        annotations:
          summary: "P95 延迟超过 10 秒"

      - alert: HighErrorRate
        expr: rate(llm_requests_total{status="error"}[5m]) / rate(llm_requests_total[5m]) > 0.05
        for: 3m
        annotations:
          summary: "错误率超过 5%"

      - alert: HighCost
        expr: increase(llm_cost_usd_total[1h]) > 10
        annotations:
          summary: "每小时成本超过 $10"
```

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **TTFT** | Time To First Token，首字延迟 |
| **Prometheus** | 指标采集和告警引擎 |
| **Grafana** | 可视化看板，实时展示趋势 |

---

## 8. 安全与合规监控

### 8.1 敏感信息检测：PII 自动脱敏

```python
import re

PII_PATTERNS = {
    "phone": r'1[3-9]\d{9}',
    "id_card": r'\d{17}[\dXx]',
    "email": r'[\w.-]+@[\w.-]+\.\w+',
    "bank_card": r'\d{16,19}',
}

def detect_and_mask_pii(text: str) -> tuple[str, list[str]]:
    """检测并脱敏 PII 信息"""
    detected = []
    masked_text = text
    
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            detected.append({"type": pii_type, "count": len(matches)})
            masked_text = re.sub(pattern, f"[{pii_type.upper()}_MASKED]", masked_text)
    
    return masked_text, detected

# 在调用 LLM 前脱敏
async def safe_llm_call(question: str):
    masked_question, pii_found = detect_and_mask_pii(question)
    
    if pii_found:
        langfuse_context.update_current_observation(
            metadata={"pii_detected": pii_found}
        )
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": masked_question}],
    )
    return response
```

### 8.2 Prompt 注入检测与告警

```python
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"你现在是一个",
    r"forget\s+everything",
    r"system\s*prompt",
    r"reveal\s+your\s+instructions",
]

async def detect_injection(user_input: str) -> bool:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, user_input, re.IGNORECASE):
            await send_alert(f"🚨 Prompt 注入尝试: {user_input[:100]}")
            return True
    return False
```

### 8.3 有害输出过滤

```python
async def check_output_safety(output: str) -> dict:
    """检查模型输出是否安全"""
    prompt = f"""检查以下 AI 回复是否包含有害内容。

AI 回复：{output[:1000]}

检查项：暴力、色情、歧视、违法建议、个人隐私泄露

输出 JSON：{{"safe": true/false, "issues": ["问题1", ...]}}"""
    
    result = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(result.choices[0].message.content)
```

### 8.4 审计日志与合规报告

```python
@dataclass
class AuditLog:
    timestamp: datetime
    user_id: str
    action: str            # llm_call / data_access / pii_detected
    model: str
    input_hash: str        # 输入的 hash（不存原文）
    output_hash: str
    pii_detected: bool
    injection_detected: bool
    cost: float

async def write_audit_log(log: AuditLog):
    """写入审计日志（合规要求保留 90 天）"""
    await db.execute(
        "INSERT INTO audit_logs (...) VALUES (...)",
        log.timestamp, log.user_id, log.action, ...
    )
```

> 💡 **PII 脱敏要在调用 LLM 之前做**——用户输入中的手机号、身份证号不应该发送给第三方模型 API。先脱敏再调用，Langfuse 中只记录脱敏后的内容。

---

## 附录：AI 可观测性速查手册

### A.1 Langfuse API 速查

| API | 用途 | 示例 |
|:---|:---|:---|
| `langfuse.trace()` | 创建 Trace | `trace(name="xxx", user_id="yyy")` |
| `trace.span()` | 创建子 Span | `span(name="retrieval")` |
| `trace.generation()` | 记录 LLM 调用 | `generation(model="gpt-4o")` |
| `langfuse.score()` | 上报评分 | `score(trace_id, name, value)` |
| `langfuse.get_prompt()` | 获取 Prompt | `get_prompt("name", label="prod")` |
| `@observe()` | 装饰器自动追踪 | `@observe()` |

### A.2 核心指标与推荐告警阈值

| 指标 | 推荐阈值 | 告警级别 |
|:---|:---|:---|
| P95 延迟 | > 10s | Warning |
| 错误率 | > 5% | Critical |
| 幻觉率 | > 10% | Warning |
| 忠实度均分 | < 3.5 | Warning |
| 每小时成本 | > $10 | Warning |
| PII 泄露 | > 0 | Critical |
| Prompt 注入 | > 0 | Critical |

### A.3 Grafana 看板 JSON 模板

```json
{
  "panels": [
    {"title": "调用量", "type": "stat", "targets": [{"expr": "sum(llm_requests_total)"}]},
    {"title": "P95 延迟", "type": "gauge", "targets": [{"expr": "histogram_quantile(0.95, llm_latency_seconds)"}]},
    {"title": "今日成本", "type": "stat", "targets": [{"expr": "sum(increase(llm_cost_usd_total[1d]))"}]},
    {"title": "错误率", "type": "gauge", "targets": [{"expr": "rate(llm_requests_total{status='error'}[5m])"}]}
  ]
}
```

### A.4 评测 Prompt 模板

```python
# 相关性评测
RELEVANCE_JUDGE = "回答是否针对问题？打分 1-5"

# 忠实性评测
FAITHFULNESS_JUDGE = "回答是否基于参考内容？有没有编造？打分 1-5"

# 有害性检测
SAFETY_CHECK = "检查是否包含暴力/色情/歧视/违法内容"

# 完整性评测
COMPLETENESS_JUDGE = "回答是否完整覆盖了问题的各个方面？打分 1-5"
```
