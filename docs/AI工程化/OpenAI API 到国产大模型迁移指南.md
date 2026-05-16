# OpenAI API 到国产大模型迁移指南

> 从 OpenAI 迁移到 DeepSeek / 通义千问 / 智谱 GLM / 豆包——API 差异对照、SDK 适配层封装、Prompt 迁移策略、Function Calling 兼容方案、多模态差异处理、多模型统一兼容层构建，一套实用方法论让你用最小成本完成平滑迁移。

---

## 1. 为什么要迁移：动机、收益与风险评估

### 1.1 迁移的三大驱动力：成本 / 合规 / 中文能力

2024-2025 年，越来越多的团队开始从 OpenAI 迁移到国产大模型。这不是"爱国情怀"，而是**实实在在的工程决策**：

```
迁移的三大驱动力：

  ① 成本 ─────── 国产模型便宜 5-50 倍
     ═══════════════════════════════════════
     GPT-4o：$2.5/M input + $10/M output
     DeepSeek-V3：¥1/M input + ¥2/M output（≈$0.14 + $0.28）
     
     同样 100 万次调用：
       OpenAI → $12,500
       DeepSeek → $420
     → 成本降低 97%

  ② 合规 ─────── 数据不出境、内容审核合规
     ═══════════════════════════════════════
     《数据安全法》《个人信息保护法》要求：
       - 用户数据不得传输到境外服务器
       - 内容生成需符合国内审核标准
     → OpenAI 服务器在美国，天然不合规

  ③ 中文能力 ── 中文场景下国产模型更强
     ═══════════════════════════════════════
     国产模型中文训练语料占比更高：
       - 成语理解、公文写作、古文翻译
       - 中国法律/医疗/金融领域术语
       - 方言理解、网络用语、拼音纠错
     → GPT-4o 中文能力好，但细分场景不如国产模型
```

> 💡 **迁移不是"非此即彼"**——最佳实践是多模型混用：英文/代码任务用 OpenAI，中文任务用国产模型，通过统一网关动态路由（参考《[大模型网关设计与实现](大模型网关设计与实现)》）。

### 1.2 国产大模型横向对比：DeepSeek / Qwen / GLM / 豆包

| 模型 | 厂商 | 定位 | 输入价格 (¥/M Token) | 输出价格 | API 兼容 | 核心优势 |
|:---|:---|:---|:---|:---|:---|:---|
| **DeepSeek-V3** | DeepSeek | 通用旗舰 | ¥1 | ¥2 | ✅ OpenAI | 推理强、代码强、性价比极高 |
| **DeepSeek-R1** | DeepSeek | 深度推理 | ¥4 | ¥16 | ✅ OpenAI | 思维链推理，数学/逻辑天花板 |
| **Qwen-Max** | 阿里 | 通用旗舰 | ¥2 | ¥6 | ✅ OpenAI | 中英文均衡、长上下文（128K） |
| **Qwen-Turbo** | 阿里 | 轻量快速 | ¥0.3 | ¥0.6 | ✅ OpenAI | 极致速度、低延迟 |
| **GLM-4-Plus** | 智谱 | 通用旗舰 | ¥5 | ¥5 | ✅ OpenAI | Agent 能力强、中文理解好 |
| **Doubao-Pro** | 字节 | 通用旗舰 | ¥0.8 | ¥2 | ✅ OpenAI | 多模态好、豆包生态 |
| **Hunyuan-Turbo** | 腾讯 | 通用旗舰 | ¥1.5 | ¥5 | ✅ OpenAI | 微信/企微生态集成 |

```
选型决策树：

  你的核心需求是什么？
    │
    ├── 极致性价比 → DeepSeek-V3 ⭐（便宜 + 效果好）
    │
    ├── 复杂推理/数学 → DeepSeek-R1（思维链推理）
    │
    ├── 长上下文（>32K）→ Qwen-Max（128K 稳定）
    │
    ├── 低延迟/高吞吐 → Qwen-Turbo（响应最快）
    │
    ├── Agent/工具调用 → GLM-4-Plus（Agent 能力完善）
    │
    └── 多模态（图片/视频）→ Doubao-Pro / Qwen-VL
```

> 💡 **2025 年的共识：DeepSeek-V3 是性价比之王**——价格是 GPT-4o 的 1/20，中文效果持平甚至更好。大部分迁移场景首选 DeepSeek，特殊场景再选其他模型。

### 1.3 迁移收益量化：成本节省 vs 效果变化

```
迁移收益量化（以日均 10 万次调用为例）：

  ┌──────────────┬──────────────┬──────────────┐
  │              │  迁移前       │  迁移后       │
  │              │  (GPT-4o)    │  (DeepSeek)  │
  ├──────────────┼──────────────┼──────────────┤
  │ 月 API 费用   │  $8,000      │  $350        │
  │ 中文准确率    │  92%         │  94%         │
  │ 英文准确率    │  96%         │  93%         │
  │ 平均延迟      │  1.2s        │  0.8s        │
  │ 合规风险      │  高（数据出境）│  无          │
  ├──────────────┼──────────────┼──────────────┤
  │ 综合评估      │  效果好但贵   │  中文更好更便宜│
  └──────────────┴──────────────┴──────────────┘

  年化节省：($8,000 - $350) × 12 = $91,800/年
```

**效果对比的正确姿势**——不要看通用榜单，要**跑自己的业务数据**：

```python
async def benchmark_migration(
    test_cases: list[dict],
    models: dict[str, dict],  # {"gpt-4o": {...}, "deepseek-v3": {...}}
) -> dict:
    """迁移效果对比测试"""
    results = {}
    
    for model_name, config in models.items():
        scores = []
        latencies = []
        costs = []
        
        for case in test_cases:
            start = time.time()
            response = await call_model(model_name, config, case["input"])
            latency = time.time() - start
            
            # 用 LLM 评分（或人工评分）
            score = await evaluate(response, case["expected_output"])
            cost = calculate_cost(model_name, response["usage"])
            
            scores.append(score)
            latencies.append(latency)
            costs.append(cost)
        
        results[model_name] = {
            "avg_score": sum(scores) / len(scores),
            "avg_latency": f"{sum(latencies)/len(latencies):.2f}s",
            "total_cost": f"${sum(costs):.2f}",
            "pass_rate": f"{sum(1 for s in scores if s >= 0.8) / len(scores):.0%}",
        }
    
    return results
```

### 1.4 迁移风险清单与决策框架

```
迁移五大风险及缓解措施：

  ① 效果下降 ──── 某些任务国产模型表现不如 GPT-4o
     缓解：先跑 benchmark → 按任务分配模型 → 差的任务保留 OpenAI

  ② 功能缺失 ──── 部分高级特性（如 Structured Output）支持不全
     缓解：逐项排查功能依赖 → 用 Prompt 工程绕过 → 关键功能保留 OpenAI

  ③ 稳定性风险 ── 国产模型 API 偶有不稳定
     缓解：多模型 Fallback → 降级机制 → 缓存兜底

  ④ 内容审核 ──── 国产模型对敏感内容的过滤更严格
     缓解：提前测试边界 → 调整 Prompt → 必要时加白名单

  ⑤ 迁移成本 ──── Prompt 适配、代码改造、测试验证的人力投入
     缓解：分阶段迁移 → 先迁简单任务 → 积累经验再迁核心
```

**Go / No-Go 决策矩阵**：

| 条件 | Go ✅ | No-Go ❌ |
|:---|:---|:---|
| 月 API 费用 | > $1,000 | < $100 |
| 合规要求 | 有数据出境限制 | 无合规压力 |
| 中文占比 | > 50% | < 10% |
| 业务复杂度 | 标准对话/RAG | 深度依赖 OpenAI 独有特性 |
| 团队能力 | 有 LLM 工程经验 | 完全没接触过 |

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **三大驱动力** | 成本降 95%、合规需求、中文能力更强 |
| **首选模型** | DeepSeek-V3 性价比之王，特殊场景选其他 |
| **效果对比** | 跑自己的业务 benchmark，不看通用榜单 |
| **迁移策略** | 分阶段、多模型混用、保留 Fallback |

---

## 2. API 差异全面对照：哪些要改、哪些不用改

### 2.1 接口兼容度概览：谁真正兼容 OpenAI 格式

好消息是——**大部分国产模型都兼容 OpenAI 的 `/v1/chat/completions` 接口格式**，迁移工作量比你想象的小：

| 特性 | DeepSeek | Qwen | GLM-4 | 豆包 | 腾讯混元 |
|:---|:---|:---|:---|:---|:---|
| **Chat Completions** | ✅ 完全 | ✅ 完全 | ✅ 完全 | ✅ 完全 | ✅ 完全 |
| **Streaming (SSE)** | ✅ 完全 | ✅ 完全 | ✅ 完全 | ✅ 完全 | ✅ 完全 |
| **Function Calling** | ✅ 完全 | ✅ 完全 | ✅ 完全 | ⚠️ 部分 | ⚠️ 部分 |
| **JSON Mode** | ✅ 完全 | ✅ 完全 | ⚠️ 部分 | ❌ 无 | ❌ 无 |
| **Vision (图片)** | ✅ V3 | ✅ VL | ✅ 4V | ✅ 完全 | ✅ 完全 |
| **Embeddings** | ✅ 独立 | ✅ 完全 | ✅ 完全 | ✅ 完全 | ✅ 完全 |
| **用 openai SDK 直连** | ✅ 换URL | ✅ 换URL | ✅ 换URL | ✅ 换URL | ✅ 换URL |

```
兼容度分级：

  Level 1 ── 换 base_url 就能用（零改动）
    └── DeepSeek、Qwen（最常用的两个，完全兼容）

  Level 2 ── 换 base_url + 少量参数调整
    └── GLM-4（JSON Mode 需要 Prompt 实现）
    └── 豆包（Function Calling 参数名略有不同）

  Level 3 ── 需要适配层封装
    └── Claude（非 OpenAI 格式，需要完整适配）
    └── Gemini（请求/响应格式完全不同）

  → 国产模型基本都是 Level 1-2，迁移成本极低
```

### 2.2 请求参数差异对照表：model / temperature / max_tokens / stop

| 参数 | OpenAI | DeepSeek | Qwen | GLM-4 | 注意事项 |
|:---|:---|:---|:---|:---|:---|
| `model` | gpt-4o | deepseek-chat | qwen-max | glm-4-plus | 模型名不同，需映射 |
| `temperature` | 0-2 | 0-2 | 0-2 | 0-1 | ⚠️ GLM 范围是 0-1 |
| `max_tokens` | ✅ | ✅ | ✅ | ✅ | 各模型上限不同 |
| `top_p` | 0-1 | 0-1 | 0-1 | 0-1 | 一致 |
| `stop` | 字符串/数组 | 字符串/数组 | 字符串/数组 | 字符串/数组 | 一致 |
| `stream` | true/false | true/false | true/false | true/false | 一致 |
| `response_format` | ✅ JSON | ✅ JSON | ✅ JSON | ❌ 不支持 | ⚠️ GLM 需 Prompt 控制 |
| `seed` | ✅ | ✅ | ❌ | ❌ | ⚠️ 仅 DeepSeek 支持 |
| `frequency_penalty` | -2 到 2 | -2 到 2 | ✅ | ✅ | 一致 |
| `presence_penalty` | -2 到 2 | -2 到 2 | ✅ | ✅ | 一致 |

```python
# ── 参数适配器：自动处理各模型差异 ──
def adapt_params(params: dict, provider: str) -> dict:
    """根据 Provider 适配请求参数"""
    adapted = params.copy()
    
    if provider == "zhipu":
        # GLM temperature 范围 0-1，需要缩放
        if "temperature" in adapted:
            adapted["temperature"] = min(adapted["temperature"] / 2, 0.99)
        # GLM 不支持 response_format
        adapted.pop("response_format", None)
        adapted.pop("seed", None)
    
    elif provider == "qwen":
        adapted.pop("seed", None)  # Qwen 不支持 seed
    
    # max_tokens 上限检查
    MAX_TOKENS = {
        "deepseek": 8192, "qwen": 8192, 
        "zhipu": 4096, "doubao": 4096,
    }
    if "max_tokens" in adapted:
        limit = MAX_TOKENS.get(provider, 4096)
        adapted["max_tokens"] = min(adapted["max_tokens"], limit)
    
    return adapted
```

> 💡 **最容易踩的坑是 temperature 范围**——OpenAI 是 0-2，GLM 是 0-1。如果你在 OpenAI 上用 `temperature=1.2`，直接传给 GLM 会报错。建议统一用 0-1 范围，需要高随机性时再做缩放。

### 2.3 响应格式差异：usage / choices / finish_reason

**响应格式差异比请求小得多**——大部分国产模型的响应结构与 OpenAI 一致，但有几个细节需要注意：

| 字段 | OpenAI | DeepSeek | Qwen | GLM-4 |
|:---|:---|:---|:---|:---|
| `id` | chatcmpl-xxx | chatcmpl-xxx | chatcmpl-xxx | 数字 ID |
| `usage.prompt_tokens` | ✅ | ✅ | ✅ | ✅ |
| `usage.completion_tokens` | ✅ | ✅ | ✅ | ✅ |
| `finish_reason` | stop/length/tool_calls | stop/length/tool_calls | stop/length | stop/length/tool_calls |
| `choices[0].message.content` | ✅ | ✅ | ✅ | ✅ |
| `choices[0].message.reasoning_content` | ❌ | ✅ (R1) | ❌ | ❌ |

```python
def normalize_response(raw: dict, provider: str) -> dict:
    """归一化响应格式"""
    # DeepSeek-R1 有 reasoning_content（思维链），需要特殊处理
    if provider == "deepseek":
        message = raw["choices"][0]["message"]
        if "reasoning_content" in message and message["reasoning_content"]:
            # 将思维链附加到 metadata，不改变主输出
            raw["_reasoning"] = message.pop("reasoning_content")
    
    # GLM 的 id 是数字，统一转字符串
    if provider == "zhipu" and isinstance(raw.get("id"), int):
        raw["id"] = f"chatcmpl-{raw['id']}"
    
    return raw
```

### 2.4 流式输出差异：SSE 格式 / chunk 结构 / 终止标记

流式输出是差异最明显的地方：

```
各模型流式输出的格式对比：

  OpenAI / DeepSeek / Qwen（标准格式）：
    data: {"choices":[{"delta":{"content":"你"}}]}
    data: {"choices":[{"delta":{"content":"好"}}]}
    data: [DONE]

  GLM-4（基本一致，终止信号不同）：
    data: {"choices":[{"delta":{"content":"你"}}]}
    data: {"choices":[{"delta":{},"finish_reason":"stop"}]}
    data: [DONE]

  DeepSeek-R1（多一个 reasoning_content 字段）：
    data: {"choices":[{"delta":{"reasoning_content":"让我思考"}}]}
    data: {"choices":[{"delta":{"reasoning_content":"..."}}]}
    data: {"choices":[{"delta":{"content":"答案是"}}]}
    data: [DONE]
```

```python
async def unified_stream(raw_stream, provider: str):
    """统一流式输出：屏蔽各模型差异"""
    async for line in raw_stream:
        if not line.strip() or line.strip() == "data: [DONE]":
            continue
        
        data = json.loads(line.replace("data: ", ""))
        delta = data.get("choices", [{}])[0].get("delta", {})
        
        # DeepSeek-R1：reasoning_content 和 content 分开处理
        if provider == "deepseek" and "reasoning_content" in delta:
            yield {"type": "reasoning", "content": delta["reasoning_content"]}
            continue
        
        content = delta.get("content", "")
        if content:
            yield {"type": "content", "content": content}
```

### 2.5 错误码与异常处理差异

| 错误类型 | OpenAI (HTTP) | DeepSeek | Qwen | GLM-4 |
|:---|:---|:---|:---|:---|
| 认证失败 | 401 | 401 | 401 | 401 |
| 限流 | 429 | 429 | 429 | 429 |
| 模型过载 | 503 | 503 | 503 | 529 ⚠️ |
| Token 超限 | 400 | 400 | 400 | 400 |
| 内容审核拒绝 | 400 | 400 | 400 (filtered) | 400 |
| 错误信息字段 | `error.message` | `error.message` | `error.message` | `error.message` |

```python
class UnifiedAPIError(Exception):
    """统一 API 错误"""
    def __init__(self, provider: str, status: int, message: str, retryable: bool):
        self.provider = provider
        self.status = status
        self.message = message
        self.retryable = retryable

def handle_api_error(provider: str, status: int, body: dict) -> UnifiedAPIError:
    """统一错误处理"""
    message = body.get("error", {}).get("message", str(body))
    
    # 内容审核拒绝（国产模型更严格）
    if "content_filter" in message or "安全" in message or "filtered" in message:
        return UnifiedAPIError(provider, status, f"内容审核拒绝: {message}", retryable=False)
    
    # 限流/过载 → 可重试
    retryable = status in (429, 503, 529)
    return UnifiedAPIError(provider, status, message, retryable=retryable)
```

> 💡 **国产模型的内容审核比 OpenAI 严格得多**——涉及政治、暴力、色情等内容会直接返回 400。迁移时要特别注意测试边界场景，必要时调整 Prompt 规避敏感词。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **兼容度** | DeepSeek/Qwen 完全兼容，换 URL 就行 |
| **参数差异** | 主要是 temperature 范围和 response_format |
| **响应差异** | 基本一致，DeepSeek-R1 多 reasoning_content |
| **流式差异** | 格式相同，终止标记和特殊字段有差异 |
| **错误处理** | 错误码基本一致，内容审核更严格 |

---

## 3. SDK 适配层：最小改动完成切换

### 3.1 最简迁移：换 base_url 三行搞定

**如果你只用 DeepSeek 或 Qwen，迁移只需要改 3 行代码**：

```python
from openai import AsyncOpenAI

# ── 迁移前：OpenAI ──
client = AsyncOpenAI(api_key="sk-openai-xxx")

# ── 迁移后：DeepSeek（改 2 行） ──
client = AsyncOpenAI(
    api_key="sk-deepseek-xxx",
    base_url="https://api.deepseek.com",  # ← 只加这一行
)

# ── 迁移后：Qwen ──
client = AsyncOpenAI(
    api_key="sk-qwen-xxx",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# ── 迁移后：GLM-4 ──
client = AsyncOpenAI(
    api_key="your-zhipu-key",
    base_url="https://open.bigmodel.cn/api/paas/v4",
)

# ── 迁移后：豆包 ──
client = AsyncOpenAI(
    api_key="your-doubao-key",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

# 调用代码完全不变！
response = await client.chat.completions.create(
    model="deepseek-chat",  # ← 只改模型名
    messages=[{"role": "user", "content": "你好"}],
)
```

```
各模型的 base_url 速查：

  DeepSeek ─── https://api.deepseek.com
  Qwen ────── https://dashscope.aliyuncs.com/compatible-mode/v1
  GLM-4 ───── https://open.bigmodel.cn/api/paas/v4
  豆包 ────── https://ark.cn-beijing.volces.com/api/v3
  腾讯混元 ── https://api.hunyuan.cloud.tencent.com/v1
```

### 3.2 多 Provider 适配层封装：统一接口抹平差异

当你需要**同时使用多个模型**时，封装一个统一适配层：

```python
from dataclasses import dataclass
from openai import AsyncOpenAI

@dataclass
class ProviderConfig:
    name: str
    api_key: str
    base_url: str
    default_model: str
    param_adapters: dict = None  # 参数适配规则

# ── 配置所有 Provider ──
PROVIDERS = {
    "deepseek": ProviderConfig(
        name="deepseek", api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        default_model="deepseek-chat",
    ),
    "qwen": ProviderConfig(
        name="qwen", api_key=os.getenv("QWEN_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-max",
    ),
    "zhipu": ProviderConfig(
        name="zhipu", api_key=os.getenv("ZHIPU_API_KEY"),
        base_url="https://open.bigmodel.cn/api/paas/v4",
        default_model="glm-4-plus",
        param_adapters={"temperature": lambda t: min(t / 2, 0.99)},
    ),
}

class UnifiedLLM:
    """统一 LLM 客户端"""
    
    def __init__(self):
        self.clients = {
            name: AsyncOpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
            for name, cfg in PROVIDERS.items()
        }
    
    async def chat(self, provider: str, messages: list, **kwargs) -> dict:
        """统一调用接口"""
        config = PROVIDERS[provider]
        client = self.clients[provider]
        
        # 适配参数
        adapted = self._adapt_params(kwargs, config)
        
        response = await client.chat.completions.create(
            model=adapted.pop("model", config.default_model),
            messages=messages,
            **adapted,
        )
        return response
    
    def _adapt_params(self, params: dict, config: ProviderConfig) -> dict:
        adapted = params.copy()
        for key, adapter in (config.param_adapters or {}).items():
            if key in adapted:
                adapted[key] = adapter(adapted[key])
        return adapted

# 使用
llm = UnifiedLLM()
response = await llm.chat("deepseek", messages=[{"role": "user", "content": "你好"}])
```

### 3.3 各模型 SDK 安装与初始化速查

```bash
# 所有国产模型都可以用 openai SDK！无需安装额外包
pip install openai

# 如果需要用各家原生 SDK（高级特性）：
pip install zhipuai          # 智谱 GLM
pip install dashscope        # 通义千问
pip install volcengine-python # 豆包
```

| 模型 | 推荐方式 | 原因 |
|:---|:---|:---|
| DeepSeek | openai SDK | 完全兼容，无需原生 SDK |
| Qwen | openai SDK | 兼容模式完善 |
| GLM-4 | openai SDK + 参数适配 | 少数参数需要调整 |
| 豆包 | openai SDK | 兼容 OpenAI 格式 |

> 💡 **统一用 openai SDK 是最优解**——一个包搞定所有模型，降低依赖复杂度。只有当你需要某个模型的独有特性（如智谱的知识检索）时，才用原生 SDK。

### 3.4 异步调用与连接池配置差异

```python
import httpx

# ── 各模型的连接配置建议 ──
CONN_CONFIG = {
    "deepseek": {
        "timeout": httpx.Timeout(connect=5, read=60, write=10, pool=5),
        "limits": httpx.Limits(max_connections=100, max_keepalive_connections=20),
    },
    "qwen": {
        "timeout": httpx.Timeout(connect=5, read=45, write=10, pool=5),
        "limits": httpx.Limits(max_connections=80, max_keepalive_connections=20),
    },
    "zhipu": {
        "timeout": httpx.Timeout(connect=5, read=60, write=10, pool=5),
        "limits": httpx.Limits(max_connections=50, max_keepalive_connections=10),
    },
}

def create_client(provider: str) -> AsyncOpenAI:
    """创建带连接池配置的客户端"""
    config = PROVIDERS[provider]
    conn = CONN_CONFIG.get(provider, {})
    
    http_client = httpx.AsyncClient(
        timeout=conn.get("timeout", httpx.Timeout(60)),
        limits=conn.get("limits", httpx.Limits(max_connections=100)),
    )
    
    return AsyncOpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        http_client=http_client,
    )
```

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **最简迁移** | 换 base_url + 模型名，3 行代码 |
| **统一封装** | UnifiedLLM 类统一管理多 Provider |
| **SDK 选择** | 统一用 openai SDK，无需原生包 |
| **连接池** | 按模型配置超时和连接数上限 |

---

## 4. Prompt 迁移：同一个 Prompt 为什么效果不同

### 4.1 Prompt 表现差异的根因分析

同一个 Prompt 在不同模型上效果差异很大——这不是 bug，而是**模型对齐方式不同**：

```
Prompt 表现差异的三大根因：

  ① 训练数据差异 ── 中文语料比例不同
     OpenAI：英文为主，中文为辅
     国产模型：中文占比更高，理解更深
     → 中文任务国产模型更好，英文任务 OpenAI 更好

  ② 对齐策略差异 ── RLHF/DPO 偏好不同
     OpenAI：倾向简洁、直接回答
     国产模型：倾向详细、礼貌、结构化回答
     → 同一个 Prompt，国产模型的回答通常更长

  ③ System Prompt 响应差异
     OpenAI：严格遵循 System Prompt
     国产模型：部分模型对 System Prompt 的遵循度较弱
     → 需要在 User Message 中重复关键指令
```

### 4.2 System Prompt 适配：角色设定与指令风格

```python
# ── OpenAI 风格：简洁指令 ──
openai_system = "你是一个翻译助手。将用户输入翻译为英文。只输出翻译结果。"

# ── 国产模型风格：明确 + 约束 + 示例 ──
domestic_system = """你是一个专业翻译助手。

## 任务
将用户输入的中文翻译为英文。

## 规则
1. 只输出翻译结果，不要输出解释或其他内容
2. 保持原文的语气和风格
3. 专业术语使用行业标准翻译

## 示例
输入：机器学习是人工智能的一个子领域
输出：Machine learning is a subfield of artificial intelligence

请直接输出翻译结果："""
```

```
System Prompt 适配的四个技巧：

  ① 明确角色 ── "你是一个 XXX" 比 "请帮我 XXX" 效果好
  ② 结构化指令 ── 用 ## 标题分隔任务/规则/示例
  ③ 重复关键约束 ── 在末尾重复最重要的指令
  ④ 加 Few-shot ── 国产模型对示例的响应比纯指令更好
```

### 4.3 输出格式控制：JSON Mode / 结构化输出差异

| 特性 | OpenAI | DeepSeek | Qwen | GLM-4 |
|:---|:---|:---|:---|:---|
| `response_format: json` | ✅ 原生 | ✅ 原生 | ✅ 原生 | ❌ 需 Prompt |
| Structured Output | ✅ 原生 | ❌ | ❌ | ❌ |
| 命中率 (JSON) | ~99% | ~95% | ~93% | ~85% |

```python
def ensure_json_output(prompt: str, provider: str) -> tuple[str, dict]:
    """确保输出为 JSON 格式"""
    extra_params = {}
    
    if provider in ("deepseek", "qwen"):
        # 支持 response_format
        extra_params["response_format"] = {"type": "json_object"}
    
    elif provider == "zhipu":
        # 不支持 response_format，用 Prompt 控制
        prompt += "\n\n请严格以 JSON 格式输出，不要输出任何其他内容。"
    
    # 所有模型都加 Prompt 兜底（提升命中率）
    if "JSON" not in prompt and "json" not in prompt:
        prompt += "\n输出格式：JSON"
    
    return prompt, extra_params

# 加一层 JSON 解析重试
async def call_with_json_retry(client, messages, max_retries=3, **kwargs):
    """带 JSON 解析重试的调用"""
    for i in range(max_retries):
        response = await client.chat.completions.create(messages=messages, **kwargs)
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取 JSON（可能混有 markdown 代码块）
            import re
            match = re.search(r'```json?\s*(.*?)\s*```', content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            if i < max_retries - 1:
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": "请只输出纯 JSON，不要包含 markdown 代码块。"})
    raise ValueError(f"JSON 解析失败: {content[:200]}")
```

### 4.4 中文场景专项优化：分词 / 成语 / 长文本

```
中文场景的三个专项优化：

  ① 分词差异 ── Token 数不同
     "机器学习"：
       OpenAI tokenizer → 2-3 tokens
       国产模型 tokenizer → 1-2 tokens
     → 同样的中文文本，国产模型消耗更少 Token

  ② 成语/惯用语理解
     "画蛇添足"：
       GPT-4o → 能理解字面意思  
       DeepSeek → 能理解比喻含义并灵活运用
     → 中文写作任务优先用国产模型

  ③ 长中文文本处理
     超长中文文档（>50K 字）：
       GPT-4o → 128K 上下文，中文性能略降
       Qwen-Max → 128K 上下文，中文专项优化
     → 长文本场景推荐 Qwen-Max
```

### 4.5 Prompt 迁移自动化：批量测试与效果对比框架

```python
class PromptMigrationTester:
    """Prompt 迁移自动化测试"""
    
    def __init__(self, llm: UnifiedLLM):
        self.llm = llm
    
    async def run_comparison(
        self, 
        test_cases: list[dict],
        source: str = "openai",
        targets: list[str] = None,
    ) -> dict:
        """对比多个模型的 Prompt 效果"""
        targets = targets or ["deepseek", "qwen"]
        all_providers = [source] + targets
        results = {p: [] for p in all_providers}
        
        for case in test_cases:
            for provider in all_providers:
                response = await self.llm.chat(
                    provider, case["messages"], temperature=0
                )
                output = response.choices[0].message.content
                
                # 自动评估
                score = await self._evaluate(output, case.get("expected"))
                results[provider].append({
                    "input": case["messages"][-1]["content"][:50],
                    "output": output[:100],
                    "score": score,
                })
        
        # 汇总报告
        summary = {}
        for provider, scores in results.items():
            avg = sum(s["score"] for s in scores) / len(scores)
            summary[provider] = {
                "avg_score": f"{avg:.2f}",
                "pass_rate": f"{sum(1 for s in scores if s['score'] >= 0.8)/len(scores):.0%}",
            }
        
        return summary
    
    async def _evaluate(self, output: str, expected: str = None) -> float:
        """用 LLM 评估输出质量（0-1）"""
        if not expected:
            return 1.0  # 无标准答案时默认通过
        prompt = f"评估以下回答的质量（0-1分）：\n期望：{expected}\n实际：{output}\n只输出数字："
        result = await self.llm.chat("deepseek", [{"role": "user", "content": prompt}])
        return float(result.choices[0].message.content.strip())

# 使用
tester = PromptMigrationTester(UnifiedLLM())
report = await tester.run_comparison(test_cases, source="openai", targets=["deepseek", "qwen"])
# 输出：{"openai": {"avg_score": "0.92"}, "deepseek": {"avg_score": "0.94"}, ...}
```

> 💡 **迁移 Prompt 不是一次性工作**——建议建立持续回归测试，每次模型更新后自动跑一遍 benchmark。国产模型迭代速度很快，新版本有时反而需要简化 Prompt。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **差异根因** | 训练数据 + 对齐策略 + System Prompt 响应 |
| **适配技巧** | 结构化指令 + 重复约束 + 加 Few-shot |
| **JSON 输出** | 支持的用 response_format，不支持的加 Prompt 兜底 |
| **中文优势** | 分词更省 Token、成语更准、长文本更好 |
| **自动化测试** | 批量对比框架 + LLM 自动评分 |

---

## 5. Function Calling 与工具调用兼容

### 5.1 各模型 Function Calling 支持度对比

| 能力 | OpenAI | DeepSeek | Qwen | GLM-4 | 豆包 |
|:---|:---|:---|:---|:---|:---|
| **基础 FC** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Parallel FC** | ✅ | ✅ | ✅ | ⚠️ 不稳定 | ❌ |
| **流式 FC** | ✅ | ✅ | ⚠️ 部分 | ❌ | ❌ |
| **tool_choice** | auto/required/none | auto/required/none | auto | auto | auto |
| **strict mode** | ✅ | ❌ | ❌ | ❌ | ❌ |

```
Function Calling 迁移难度：

  DeepSeek ── ⭐ 最简单，格式完全一致
  Qwen ───── ⭐ 基本一致，tool_choice 略有限制
  GLM-4 ──── ⭐⭐ 需测试 Parallel FC 稳定性
  豆包 ───── ⭐⭐⭐ 不支持 Parallel FC，需要串行化
```

### 5.2 参数格式差异：tools / functions / input_schema

```python
# ── OpenAI / DeepSeek / Qwen 格式（完全一致）──
tools_openai = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取城市天气",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名"},
            },
            "required": ["city"],
        },
    },
}]

# → DeepSeek 和 Qwen 直接用上面的格式，0 改动

# ── GLM-4 格式（基本一致，有细微差异）──
# GLM-4 也用 tools 格式，但偶尔对 description 的理解不如 OpenAI 精准
# 建议：description 写得更详细，加中文示例
tools_glm = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取指定城市的天气信息。例如：查询北京的天气",  # 更详细
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，如'北京'、'上海'"},
            },
            "required": ["city"],
        },
    },
}]
```

### 5.3 统一工具调用封装：一套代码适配全部模型

```python
class UnifiedToolCaller:
    """统一工具调用封装"""
    
    def __init__(self, llm: UnifiedLLM):
        self.llm = llm
    
    async def call_with_tools(
        self, provider: str, messages: list, tools: list, **kwargs
    ) -> dict:
        """统一工具调用"""
        # 适配 tool_choice
        tool_choice = kwargs.pop("tool_choice", "auto")
        if provider in ("qwen", "doubao") and tool_choice == "required":
            tool_choice = "auto"  # 不支持 required，降级为 auto
        
        response = await self.llm.chat(
            provider, messages,
            tools=tools, tool_choice=tool_choice, **kwargs,
        )
        
        message = response.choices[0].message
        
        # 标准化 tool_calls 格式
        if hasattr(message, 'tool_calls') and message.tool_calls:
            return {
                "type": "tool_calls",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments),
                    }
                    for tc in message.tool_calls
                ],
            }
        
        return {"type": "text", "content": message.content}
    
    async def execute_tool_loop(
        self, provider: str, messages: list, 
        tools: list, tool_handlers: dict, max_rounds: int = 5,
    ) -> str:
        """完整的工具调用循环"""
        for _ in range(max_rounds):
            result = await self.call_with_tools(provider, messages, tools)
            
            if result["type"] == "text":
                return result["content"]
            
            # 执行工具，收集结果
            for tc in result["tool_calls"]:
                handler = tool_handlers.get(tc["name"])
                if handler:
                    tool_result = await handler(**tc["arguments"])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    })
        
        return "工具调用轮数超限"
```

### 5.4 Parallel Function Calling 与流式工具调用差异

```
Parallel Function Calling 兼容方案：

  场景：用户说"北京和上海今天天气怎么样？"
  
  OpenAI / DeepSeek：一次返回 2 个 tool_calls ✅
    tool_calls: [get_weather("北京"), get_weather("上海")]
  
  GLM-4：可能返回 1 或 2 个（不稳定）⚠️
    需要做兜底：如果只返回 1 个，追问第 2 个
  
  豆包：只返回 1 个 ❌
    需要串行化：先查北京 → 再查上海
```

```python
async def handle_parallel_fc(provider: str, tool_calls: list, expected_count: int):
    """处理 Parallel FC 的兼容性"""
    if len(tool_calls) >= expected_count:
        return tool_calls  # 正常返回
    
    if provider in ("zhipu", "doubao"):
        # 不支持或不稳定的模型，串行补充
        # 将已有的 tool_calls 结果回填，让模型继续调用
        return tool_calls  # 由外层 loop 自动补充
    
    return tool_calls
```

> 💡 **Function Calling 是迁移中最需要测试的部分**——表面上格式一样，但不同模型对复杂工具调用（嵌套参数、多工具并行）的能力差异很大。建议用真实业务的工具定义做回归测试。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **格式差异** | DeepSeek/Qwen 完全一致，GLM 需详细 description |
| **Parallel FC** | DeepSeek 支持，GLM 不稳定，豆包不支持 |
| **统一封装** | UnifiedToolCaller 抹平差异 + tool loop |
| **迁移建议** | 用真实工具定义做回归测试 |

---

## 6. 多模态能力迁移：视觉 / 音频 / 文件

### 6.1 视觉理解 API 差异：image_url / base64 / 文件上传

| 能力 | OpenAI (GPT-4o) | DeepSeek-V3 | Qwen-VL | GLM-4V |
|:---|:---|:---|:---|:---|
| **URL 图片** | ✅ image_url | ✅ image_url | ✅ image_url | ✅ image_url |
| **Base64** | ✅ | ✅ | ✅ | ✅ |
| **多图理解** | ✅ 多张 | ⚠️ 单张 | ✅ 多张 | ✅ 多张 |
| **图片分辨率** | auto/low/high | auto | auto | auto |
| **视频理解** | ❌ | ❌ | ✅ Qwen-VL | ❌ |

```python
def build_vision_message(image_source: str, prompt: str, provider: str) -> dict:
    """构建视觉消息（统一格式）"""
    # 所有国产模型都兼容 OpenAI 的 content 数组格式
    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": image_source}},
    ]
    
    # Base64 格式统一
    if image_source.startswith("data:"):
        content[1] = {"type": "image_url", "image_url": {"url": image_source}}
    elif image_source.startswith("http"):
        content[1] = {"type": "image_url", "image_url": {"url": image_source}}
    else:
        # 本地文件 → 转 base64
        import base64
        with open(image_source, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        content[1] = {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"},
        }
    
    return {"role": "user", "content": content}
```

### 6.2 语音/音频能力对比与适配

| 能力 | OpenAI | 国产替代 |
|:---|:---|:---|
| **TTS** | openai.audio.speech | 阿里 CosyVoice / 讯飞 |
| **STT** | openai.audio.transcriptions | 阿里 Paraformer / 讯飞 |
| **实时语音** | Realtime API | 豆包语音 / 通义听悟 |

> 💡 **语音能力无法用 openai SDK 直连**——需要用各家原生 SDK。好消息是中文语音识别国产方案普遍比 Whisper 更好。

### 6.3 文档/文件处理能力差异

```
文档理解能力对比：

  OpenAI ── 无原生文档解析，需自行提取文本
  Qwen-Long ── ✅ 原生支持长文档输入（最大 10M Token）
  GLM-4 ── 支持文件上传 API（PDF/Word/Excel）
  豆包 ── 支持文件 URL 输入

  推荐方案：
    简单文档 → 用 Qwen-Long 直接输入全文
    复杂文档 → 自行解析（PyMuPDF/Unstructured）后送入任意模型
```

### 6.4 多模态统一适配层设计

```python
class MultimodalAdapter:
    """多模态统一适配层"""
    
    # 各模型的多模态模型名映射
    VISION_MODELS = {
        "openai": "gpt-4o",
        "deepseek": "deepseek-chat",  # V3 支持视觉
        "qwen": "qwen-vl-max",
        "zhipu": "glm-4v-plus",
    }
    
    async def vision_chat(self, provider: str, image: str, prompt: str) -> str:
        """统一视觉对话"""
        model = self.VISION_MODELS[provider]
        message = build_vision_message(image, prompt, provider)
        
        response = await self.llm.chat(
            provider, [message], model=model,
        )
        return response.choices[0].message.content

    async def document_chat(self, provider: str, doc_text: str, question: str) -> str:
        """统一文档问答"""
        if provider == "qwen" and len(doc_text) > 50000:
            # Qwen-Long 支持超长文档
            model = "qwen-long"
        else:
            model = None  # 使用默认模型
        
        messages = [
            {"role": "system", "content": "根据以下文档回答问题。"},
            {"role": "user", "content": f"文档内容：\n{doc_text}\n\n问题：{question}"},
        ]
        response = await self.llm.chat(provider, messages, model=model)
        return response.choices[0].message.content
```

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **视觉 API** | 格式基本一致，多图和分辨率支持有差异 |
| **语音能力** | 需用原生 SDK，中文识别国产更好 |
| **文档处理** | Qwen-Long 原生支持超长文档 |
| **统一适配** | MultimodalAdapter 按能力路由到合适模型 |

---

## 7. 多模型兼容层：生产级统一接入方案

> 💡 本章与《[大模型网关设计与实现](大模型网关设计与实现)》互补——网关侧重架构设计，本章**聚焦迁移场景**下如何渐进式切换模型。

### 7.1 兼容层架构设计：Provider 模式

```
迁移场景的兼容层架构：

  业务代码（不改任何代码）
    │
    ▼
  ┌─────────────────────────────────┐
  │        MigrationRouter           │
  │  ┌─────────┐  ┌──────────────┐  │
  │  │ 流量分配 │  │ 效果监控     │  │
  │  │ A: 80%  │  │ 实时对比     │  │
  │  │ B: 20%  │  │ 质量告警     │  │
  │  └─────────┘  └──────────────┘  │
  ├────────────┬────────────────────┤
  │  OpenAI    │  DeepSeek（新）     │
  │  (旧模型)   │  (迁移目标)        │
  └────────────┴────────────────────┘
```

```python
class MigrationRouter:
    """迁移专用路由器：支持灰度切换"""
    
    def __init__(self, llm: UnifiedLLM):
        self.llm = llm
        self.traffic_split = {
            "openai": 0.8,    # 80% 流量走 OpenAI
            "deepseek": 0.2,  # 20% 流量走 DeepSeek
        }
        self.metrics = {"openai": [], "deepseek": []}
    
    async def route(self, messages: list, **kwargs) -> dict:
        """按流量比例路由"""
        import random
        r = random.random()
        
        cumulative = 0
        for provider, ratio in self.traffic_split.items():
            cumulative += ratio
            if r <= cumulative:
                start = time.time()
                response = await self.llm.chat(provider, messages, **kwargs)
                latency = time.time() - start
                
                # 记录指标
                self.metrics[provider].append({
                    "latency": latency,
                    "tokens": response.usage.total_tokens,
                    "timestamp": time.time(),
                })
                return response
    
    def update_split(self, new_split: dict):
        """动态调整流量比例"""
        self.traffic_split = new_split
        # 例：确认效果后 → {"openai": 0, "deepseek": 1.0}
```

### 7.2 模型路由策略：按任务 / 成本 / 质量自动选择

```python
# ── 按任务类型自动选择模型 ──
TASK_ROUTING = {
    "中文对话":    "deepseek",    # 中文最强
    "英文翻译":    "openai",      # 英文最好
    "代码生成":    "deepseek",    # 代码能力强
    "复杂推理":    "deepseek-r1", # 思维链推理
    "长文档摘要":  "qwen",        # 128K 上下文
    "图片理解":    "qwen-vl",     # 多模态最好
}

async def smart_route(task_type: str, messages: list, **kwargs) -> dict:
    """按任务类型智能路由"""
    provider = TASK_ROUTING.get(task_type, "deepseek")  # 默认 DeepSeek
    return await llm.chat(provider, messages, **kwargs)
```

### 7.3 降级与 Fallback：主模型挂了自动切换

```python
FALLBACK_CHAINS = {
    "deepseek": ["qwen", "zhipu", "openai"],
    "qwen":     ["deepseek", "zhipu", "openai"],
    "openai":   ["deepseek", "qwen"],
}

async def call_with_fallback(provider: str, messages: list, **kwargs) -> dict:
    """带降级的调用"""
    chain = [provider] + FALLBACK_CHAINS.get(provider, [])
    
    for p in chain:
        try:
            return await asyncio.wait_for(
                llm.chat(p, messages, **kwargs), timeout=30
            )
        except Exception as e:
            logger.warning(f"{p} 调用失败: {e}，尝试降级...")
    
    raise RuntimeError("所有模型均不可用")
```

### 7.4 效果监控与 A/B 测试：持续评估迁移效果

```python
class MigrationMonitor:
    """迁移效果持续监控"""
    
    async def compare_realtime(self, messages: list) -> dict:
        """实时双跑对比（Shadow Mode）"""
        # 主路径：走新模型
        primary = await llm.chat("deepseek", messages)
        
        # 影子路径：异步走旧模型（不影响响应时间）
        shadow_task = asyncio.create_task(llm.chat("openai", messages))
        
        # 异步评估差异
        asyncio.create_task(self._evaluate_diff(primary, shadow_task))
        
        return primary  # 只返回主路径结果
    
    async def _evaluate_diff(self, primary, shadow_task):
        shadow = await shadow_task
        p_content = primary.choices[0].message.content
        s_content = shadow.choices[0].message.content
        
        # 简单差异检测
        if len(p_content) < len(s_content) * 0.5:
            logger.warning(f"迁移质量告警：新模型回答过短")
```

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **灰度路由** | 按比例分配流量，渐进切换 |
| **任务路由** | 中文/代码/推理/长文档各用最优模型 |
| **Fallback** | 主模型失败自动降级到备用 |
| **Shadow Mode** | 双跑对比，不影响线上响应 |

---

## 8. 实战案例：从 OpenAI 全家桶迁移到国产模型

### 8.1 项目背景：月费 $2000 的 OpenAI 依赖

```
项目概况：

  产品 ──── 企业级智能客服 + 知识库问答系统
  用户 ──── 日活 5,000 用户，日均 30,000 次 LLM 调用
  
  当前技术栈：
    对话：GPT-4o（主力）
    Embedding：text-embedding-3-small
    意图分类：GPT-4o-mini
    文档摘要：GPT-4o
  
  痛点：
    ① 月费 $2,000+，领导说太贵了
    ② 数据出境不合规，客户审计不通过
    ③ 中文客服场景 GPT-4o 还需 Prompt 优化
  
  目标：
    → 迁移到国产模型，月费降到 $400 以内
    → 中文效果不降反升
    → 2 周内完成迁移
```

### 8.2 Phase 1：API 兼容性评估与模型选型

```
Phase 1 执行（Day 1-2）：

  Step 1：梳理所有 OpenAI 调用点
    grep -r "openai" --include="*.py" src/
    
    找到 4 类调用：
      ① chat.completions.create（15 处）
      ② embeddings.create（3 处）
      ③ tools/function_calling（5 处）
      ④ streaming（8 处）

  Step 2：选型决策
    对话 → DeepSeek-V3（性价比最高，中文好）
    Embedding → 阿里 text-embedding-v3（中文优化）
    意图分类 → DeepSeek-V3（比 mini 便宜且更准）
    文档摘要 → Qwen-Max（长上下文 128K）

  Step 3：准备测试数据集
    从线上日志抽取 200 条真实对话
    覆盖：售前咨询、售后投诉、知识库问答、闲聊
```

### 8.3 Phase 2：Prompt 适配与效果对比测试

```python
# ── 实际的 Prompt 适配示例 ──

# 原始 Prompt（OpenAI 风格，简洁）
ORIGINAL_SYSTEM = "你是客服助手，回答用户问题。"

# 适配后 Prompt（国产模型风格，结构化）
ADAPTED_SYSTEM = """你是一个专业的电商客服助手。

## 角色
- 语气友好专业，像真人客服一样
- 先理解用户问题，再给出解决方案

## 回答规则
1. 先表达理解（"明白您的问题"）
2. 给出具体解决方案
3. 告知下一步操作
4. 回答控制在 150 字以内

## 禁止
- 不说"我不知道"，换成"我帮您查一下"
- 不用 AI 腔调（"作为AI助手"）"""
```

```
Phase 2 效果对比（200 条测试数据）：

  ┌───────────┬──────────┬──────────┬──────────┐
  │ 指标       │ GPT-4o   │ DeepSeek │ Qwen-Max │
  ├───────────┼──────────┼──────────┼──────────┤
  │ 中文准确率  │  91%     │  94% ⭐  │  92%     │
  │ 回答质量    │  4.1/5   │  4.3/5 ⭐│  4.0/5   │
  │ 平均延迟    │  1.4s    │  0.9s ⭐ │  1.1s    │
  │ 格式遵循    │  95%     │  92%     │  90%     │
  │ 单条成本    │  $0.008  │  $0.0004 │  $0.001  │
  └───────────┴──────────┴──────────┴──────────┘

  结论：DeepSeek 中文效果 + 速度 + 成本全面领先
  唯一不足：格式遵循稍弱 → 用 response_format 补齐
```

### 8.4 Phase 3：灰度切换与线上验证

```
灰度切换计划（Day 6-10）：

  Day 6 ── 10% 流量切到 DeepSeek
    监控指标：响应时间、用户满意度、异常率
    结果：一切正常 ✅

  Day 7 ── 30% 流量
    发现问题：某些专业术语回答不如 GPT-4o
    处理：在 Prompt 中加术语表 → 问题解决

  Day 8 ── 50% 流量
    Shadow Mode 双跑对比运行中
    差异率 < 5% ✅

  Day 9 ── 80% 流量
    客服团队反馈：中文回答更自然了 ✅

  Day 10 ── 100% 切换
    保留 OpenAI 作为 Fallback（DeepSeek 挂了自动降级）
```

### 8.5 迁移结果：成本降 80%、中文效果提升 15%

```
最终迁移结果：

  ┌─────────────────────────────────────────────┐
  │          迁移效果汇总                         │
  ├─────────────┬───────────┬───────────────────┤
  │ 指标         │ 迁移前     │ 迁移后            │
  ├─────────────┼───────────┼───────────────────┤
  │ 月 API 费用  │ $2,100    │ $380 (-82%)       │
  │ 中文效果     │ 91%       │ 94% (+3%)         │
  │ 平均延迟     │ 1.4s      │ 0.9s (-36%)       │
  │ 合规风险     │ 高        │ 无 ✅              │
  │ 可用性       │ 99.5%     │ 99.8% ✅           │
  ├─────────────┼───────────┼───────────────────┤
  │ 模型分配     │ 100% OpenAI│ 90% DeepSeek      │
  │             │           │ 8% Qwen（长文档）   │
  │             │           │ 2% OpenAI（Fallback）│
  └─────────────┴───────────┴───────────────────┘
  
  年化节省：($2,100 - $380) × 12 = $20,640
```

```
迁移经验总结（避坑指南）：

  ✅ 做对了：
    1. 先跑业务 benchmark，不看通用榜单
    2. 分阶段灰度，不一步到位
    3. 保留 OpenAI 作为 Fallback
    4. Prompt 适配要结构化、加 Few-shot

  ❌ 踩过的坑：
    1. 直接用 OpenAI 的 Prompt → 效果差 → 要适配！
    2. 没测边界（内容审核）→ 线上被拒 → 要预测试
    3. 没做 Shadow Mode → 上线后才发现问题 → 要双跑
```

**第 8 章核心知识回顾：**

| 阶段 | 做了什么 | 耗时 |
|:---|:---|:---|
| **评估选型** | 梳理调用点 + 模型选型 + 准备测试集 | 2 天 |
| **Prompt 适配** | 结构化改造 + 200 条 benchmark | 3 天 |
| **灰度切换** | 10% → 30% → 50% → 80% → 100% | 5 天 |
| **最终效果** | 成本 -82%、中文 +3%、延迟 -36% | — |

---

## 附录

### A. API 参数差异速查表

| 参数 | OpenAI | DeepSeek | Qwen | GLM-4 | 豆包 |
|:---|:---|:---|:---|:---|:---|
| `base_url` | api.openai.com | api.deepseek.com | dashscope..../v1 | open.bigmodel.cn/.../v4 | ark.cn-beijing..../v3 |
| `temperature` | 0-2 | 0-2 | 0-2 | **0-1** | 0-2 |
| `max_tokens` | 16384 | 8192 | 8192 | 4096 | 4096 |
| `response_format` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `seed` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `tools` | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| `tool_choice` | auto/required/none | auto/required/none | auto | auto | auto |
| `stream` | ✅ | ✅ | ✅ | ✅ | ✅ |

### B. 各模型定价对比（持续更新）

| 模型 | 输入 (¥/M Token) | 输出 (¥/M Token) | 上下文 | 备注 |
|:---|:---|:---|:---|:---|
| GPT-4o | ¥18 ($2.5) | ¥72 ($10) | 128K | 综合最强 |
| GPT-4o-mini | ¥1.1 ($0.15) | ¥4.3 ($0.60) | 128K | 性价比 |
| DeepSeek-V3 | ¥1 | ¥2 | 64K | **性价比之王** |
| DeepSeek-R1 | ¥4 | ¥16 | 64K | 深度推理 |
| Qwen-Max | ¥2 | ¥6 | 128K | 长上下文 |
| Qwen-Turbo | ¥0.3 | ¥0.6 | 128K | 最便宜 |
| GLM-4-Plus | ¥5 | ¥5 | 128K | Agent |
| Doubao-Pro | ¥0.8 | ¥2 | 128K | 多模态 |

> 💡 价格截至 2025 年 Q1，各厂商经常调价（通常是降价），请以官方文档为准。

### C. 迁移检查清单（Checklist）

```
迁移前检查 ────────────────────────────────
  □ 梳理所有 OpenAI API 调用点
  □ 列出使用的高级特性（FC / streaming / JSON Mode）
  □ 准备 200+ 条业务测试数据
  □ 确认合规需求（数据出境限制）
  □ 申请国产模型 API Key

Prompt 适配 ────────────────────────────────
  □ System Prompt 结构化改造
  □ 加 Few-shot 示例
  □ 测试 JSON 输出命中率
  □ 测试内容审核边界
  □ 跑 benchmark 对比效果

代码改造 ──────────────────────────────────
  □ 替换 base_url 和 api_key
  □ 适配 temperature 范围（GLM: 0-1）
  □ 处理 response_format 不支持的情况
  □ 测试 Function Calling 兼容性
  □ 测试流式输出

灰度上线 ──────────────────────────────────
  □ 配置 Fallback 降级链
  □ 10% 流量切换 + 监控
  □ Shadow Mode 双跑
  □ 逐步提升到 100%
  □ 保留旧模型作为 Fallback

上线后 ────────────────────────────────────
  □ 监控响应时间和错误率
  □ 收集用户反馈
  □ 持续优化 Prompt
  □ 关注模型更新，及时测试新版本
```
