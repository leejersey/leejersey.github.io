# AI 应用的成本控制与优化

> 从一个月烧 $500 到 $50——手把手教你把 AI 应用的账单砍下来，同时不牺牲用户体验。

---

## 3. Prompt 工程：少花 Token 多办事

模型选对了，下一步就是**让每次请求消耗更少的 Token**。

Prompt 是 AI 应用中最容易被忽视的成本黑洞。很多开发者写 System Prompt 时像写论文一样详尽——殊不知那些精心雕琢的指令，每次请求都在重复发送、重复计费。

---

### 3.1 每一个 Token 都是钱：Prompt 成本意识

### Token 成本的乘数效应

```
一个容易被忽视的算术：

  你的 System Prompt = 1500 tokens
  每次 API 调用都会发送这 1500 tokens
  每天 3000 次调用

  每日 System Prompt Token 消耗：
    1500 × 3000 = 450 万 tokens/天

  月消耗：450 万 × 30 = 1.35 亿 tokens/月

  GPT-4o 输入成本：
    1.35 亿 × $2.50 / 1M = $337.5/月
    → 光 System Prompt 就花了 $337！

  如果把 System Prompt 砍到 500 tokens：
    500 × 3000 × 30 × $2.50 / 1M = $112.5/月
    → 省了 $225/月，一年省 $2700

  结论：System Prompt 每多 1 个 token
  = 每月多花 $0.225（按上述流量）
```

### Prompt 的成本地图

```
一次 RAG 请求的 Token 分布（典型场景）：

  ┌──────────────────────────────────────┐
  │          总输入 Token ≈ 2500          │
  │                                      │
  │  ████████████████  System Prompt     │
  │  1500 tokens (60%)  ← 最大头！       │
  │                                      │
  │  ████████          检索上下文         │
  │  800 tokens (32%)                    │
  │                                      │
  │  ██               用户问题           │
  │  200 tokens (8%)                     │
  └──────────────────────────────────────┘

  优化优先级：
    1. System Prompt（60%）→ 瘦身空间最大
    2. 检索上下文（32%）→ 减少检索数量、缩小分块
    3. 用户问题（8%）→ 基本无法控制
```

### 3.2 System Prompt 瘦身：从 2000 Token 到 500 Token

System Prompt 是成本优化中**投入产出比最高**的环节——改一次，永久生效。

### 臃肿 Prompt 的通病

```python
# ❌ 臃肿版 System Prompt（~1500 tokens）
BLOATED_PROMPT = """
你是一个专业的技术文档助手。你的主要职责是帮助用户解答各种技术问题。
你需要始终保持专业、友好、有耐心的态度来回答用户的每一个问题。

以下是你需要遵循的一些重要规则和指导方针：

1. 回答风格指南：
   - 你的回答应该清晰、准确、有条理
   - 使用简洁明了的语言，避免过于复杂的表述
   - 如果问题涉及代码，请提供可运行的代码示例
   - 代码示例应该包含适当的注释，以便用户理解
   - 回答的长度应该适中，既不要太短（缺乏信息）也不要太长（信息过载）

2. 知识库使用规则：
   - 你会收到一些参考资料，这些是从知识库中检索到的相关文档
   - 请主要基于这些参考资料来回答问题
   - 如果参考资料中没有足够的信息来回答问题，请诚实地告知用户
   - 不要编造或虚构任何信息
   - 如果你需要引用参考资料中的内容，请注明来源

3. 特殊情况处理：
   - 如果用户的问题超出了技术范围，礼貌地引导他们回到技术话题
   - 如果遇到你不确定的问题，建议用户查阅官方文档
   - 对于涉及安全或敏感信息的问题，提醒用户注意安全最佳实践
   - 如果用户的问题含糊不清，请先询问澄清问题

4. 输出格式要求：
   - 使用 Markdown 格式进行回答
   - 代码使用适当的语言标记
   - 重要信息使用加粗或列表突出
   - 如果回答内容较多，使用标题分层组织

请始终记住，你的目标是提供最有帮助、最准确的技术解答。
"""
```

```python
# ✅ 精简版 System Prompt（~300 tokens）
LEAN_PROMPT = """你是技术助手。基于参考资料回答，无相关内容则如实告知。
回答要求：简洁准确，含代码示例时加注释，用 Markdown 格式。"""
```

### 瘦身技巧清单

```
System Prompt 瘦身 7 板斧：

  1. 删除客套话
  ─────────────────────────────────────
    ❌ "你需要始终保持专业、友好、有耐心的态度"
    ✅ （删掉，模型默认就是友好的）

  2. 合并重复指令
  ─────────────────────────────────────
    ❌ "回答要清晰" + "回答要准确" + "回答要有条理"
    ✅ "回答要简洁准确"

  3. 删除模型已知的规范
  ─────────────────────────────────────
    ❌ "代码使用适当的语言标记"
    ✅ （删掉，模型默认会用代码块）

  4. 删除罕见场景的处理规则
  ─────────────────────────────────────
    ❌ "如果涉及安全或敏感信息..."
    ✅ （删掉，发生概率 < 1%，不值得占 Token）

  5. 用短句替代长句
  ─────────────────────────────────────
    ❌ "如果参考资料中没有足够的信息来回答问题，请诚实地告知用户"
    ✅ "无相关内容则如实告知"

  6. 用符号替代文字
  ─────────────────────────────────────
    ❌ "第一步...第二步...第三步..."
    ✅ "1. ... 2. ... 3. ..."

  7. 把低频指令移到用户消息中
  ─────────────────────────────────────
    ❌ System: "如果用户要求输出 JSON，就用 JSON 格式"
    ✅ User: "请用 JSON 格式回答：{问题}"
    → 只在需要时才发送，不是每次都带着
```

### 瘦身前后对比

| 维度 | 瘦身前 | 瘦身后 | 节省 |
|------|--------|--------|------|
| Token 数 | ~1500 | ~300 | 80% |
| 月成本（GPT-4o，3000 次/天） | $337 | $67 | $270/月 |
| 回答质量 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 基本不变 |

> **一个反直觉的发现**：更短的 System Prompt 有时候效果反而更好。因为长 Prompt 中的指令可能互相矛盾，让模型困惑。而简洁的指令更容易被模型准确执行。

### 3.3 Few-shot 的成本陷阱与替代方案

Few-shot（给模型几个示例）是提升回答质量的常用技巧。但它的**成本代价**经常被忽视。

### Few-shot 的成本问题

```
Few-shot 的 Token 消耗：

  典型的 3-shot Prompt：
  ─────────────────────────────────────
  System: "你是一个情感分析助手"           ~30 tokens
  User: "这个产品太棒了！"               ~15 tokens
  Assistant: {"sentiment": "positive"}   ~10 tokens
  User: "退货流程太复杂了"               ~15 tokens
  Assistant: {"sentiment": "negative"}   ~10 tokens
  User: "还行吧，没什么特别的"            ~15 tokens
  Assistant: {"sentiment": "neutral"}    ~10 tokens
  User: [实际用户输入]                   ~20 tokens
  ─────────────────────────────────────
  Total: ~125 tokens

  vs Zero-shot（无示例）：
  ─────────────────────────────────────
  System: "情感分析，返回 JSON: {sentiment: positive/negative/neutral}"
  User: [实际用户输入]
  ─────────────────────────────────────
  Total: ~50 tokens

  差异：125 vs 50 = 2.5 倍
  月额外成本（10万次，GPT-4o-mini）：
    (125-50) × 100,000 × $0.15 / 1M = $1.13/月
  → 对 mini 模型来说不多

  月额外成本（10万次，GPT-4o）：
    (125-50) × 100,000 × $2.50 / 1M = $18.75/月
  → GPT-4o 上就明显了
```

### 三种替代方案

```
替代方案 1：Zero-shot + 格式约束（推荐）
─────────────────────────────────────
  不给示例，但用精确的格式说明替代

  ❌ Few-shot（给 3 个示例 = 90 tokens）
  ✅ "返回 JSON：{sentiment: positive|negative|neutral}"
     （20 tokens，效果接近）

  适用：输出格式明确的任务（分类、提取、格式转换）


替代方案 2：Fine-tuning（大量重复任务）
─────────────────────────────────────
  把 Few-shot 示例"烧"进模型里

  → 微调后模型已经学会了你的格式
  → 推理时不需要再发送示例
  → Token 消耗降为 zero-shot 级别

  适用：每月 > 50 万次的固定格式任务
  成本：微调一次 ~$10-50，之后每次调用省 few-shot tokens


替代方案 3：动态 Few-shot（按需加载）
─────────────────────────────────────
  不是每次都带 3 个示例，而是根据用户输入动态选择

  步骤：
    1. 判断用户问题是否需要示例（简单问题不加）
    2. 需要时，从示例库中选 1 个最相关的（而非固定 3 个）
    3. 节省 60-80% 的 few-shot token

  适用：任务类型多变、部分需要示例引导
```

```python
def build_prompt_with_dynamic_fewshot(
    question: str,
    examples_db: list[dict],
    max_examples: int = 1
) -> list[dict]:
    """动态 Few-shot：只在需要时才加示例，且只加最相关的"""

    messages = [
        {"role": "system", "content": "情感分析，返回 JSON: {sentiment: positive|negative|neutral}"}
    ]

    # 判断是否需要示例（用简单的规则）
    needs_example = any(word in question for word in ["怎么", "什么格式", "举个例子"])

    if needs_example and examples_db:
        # 只选 1 个最相关的示例（而非全部）
        example = examples_db[0]  # 实际可以用语义相似度选择
        messages.append({"role": "user", "content": example["input"]})
        messages.append({"role": "assistant", "content": example["output"]})

    messages.append({"role": "user", "content": question})
    return messages
```

> **原则**：Few-shot 不是免费的午餐。每个示例都在消耗 Token。如果 zero-shot + 格式约束能达到 90% 的效果，就不要用 few-shot。

### 3.4 输出格式约束：让模型少说废话

还记得吗？**输出 Token 比输入 Token 贵 2-4 倍**。控制输出格式是最直接的省钱手段。

### 没有约束的模型会"废话连篇"

```
同一个问题，有无输出约束的差异：

  问题："Python 的 GIL 是什么？"

  无约束的输出（~300 tokens）：
  ─────────────────────────────────────
  "GIL，全称是 Global Interpreter Lock，即全局解释器锁，
  它是 CPython 解释器中的一个机制。简单来说，GIL 是一个
  互斥锁，它确保在任何时候只有一个线程可以执行 Python
  字节码。这意味着即使在多核处理器上，CPython 也无法真正
  地并行执行多个线程...（以下省略 200 字的详细解释）"

  有约束的输出（~80 tokens）：
  ─────────────────────────────────────
  Prompt 加上："请用 2-3 句话简洁回答"

  "GIL（全局解释器锁）是 CPython 中的互斥锁，确保同一
  时刻只有一个线程执行字节码。它导致多线程无法利用多核
  CPU 做并行计算，可通过多进程或 asyncio 绕过。"

  Token 差异：300 vs 80 = 3.75 倍
  成本差异（GPT-4o 输出 $10/M）：
    $0.003 vs $0.0008 → 省 73%
```

### 四种输出约束技巧

```python
# 技巧 1：max_tokens 硬限制
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": question}],
    max_tokens=200  # 硬性限制最大输出 200 tokens
)
# → 模型生成到 200 tokens 就停止
# → 注意：可能在句子中间被截断


# 技巧 2：Prompt 中指定长度
messages = [
    {"role": "system", "content": "回答限 3 句以内。"},
    {"role": "user", "content": question}
]
# → 模型会自觉控制长度
# → 比 max_tokens 更优雅，不会截断


# 技巧 3：JSON 结构化输出
messages = [
    {"role": "system", "content": """回答用户问题，返回 JSON：
{"answer": "简洁回答", "confidence": "high/medium/low"}"""},
    {"role": "user", "content": question}
]
# → JSON 强制模型只输出结构化内容
# → 没有寒暄、没有铺垫、没有总结
# → 通常比自由文本省 50-70% 的输出 token


# 技巧 4：OpenAI 的 response_format 参数
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    response_format={"type": "json_object"}  # 强制 JSON 输出
)
# → 官方保证输出是合法 JSON
# → 不需要在 Prompt 中反复强调"请返回 JSON"
```

### 不同场景的输出约束策略

| 场景 | 约束方式 | 预期 Token 节省 |
|------|---------|---------------|
| RAG 知识库问答 | "用 2-3 句话回答" | 50-70% |
| 信息提取 | 返回 JSON，指定字段 | 70-80% |
| 分类任务 | 只返回类别标签 | 90%+ |
| 客服回复 | max_tokens=300 + "简洁回答" | 40-60% |
| 代码生成 | "只返回代码，不要解释" | 30-50% |

### 完整的成本优化 Prompt 模板

```python
def build_cost_optimized_prompt(
    question: str,
    context: str,
    output_style: str = "concise"  # concise / json / label
) -> list[dict]:
    """构建成本优化的 Prompt"""

    style_instructions = {
        "concise": "用 2-3 句话简洁回答。无相关内容则回复'无相关信息'。",
        "json": '返回 JSON：{"answer": "回答", "sources": ["来源"]}',
        "label": "只返回分类标签，不要解释。",
    }

    system = f"技术助手。基于参考资料回答。{style_instructions[output_style]}"

    return [
        {"role": "system", "content": system},            # ~50 tokens
        {"role": "user", "content": f"参考：{context}\n\n问题：{question}"}
    ]
```

> **一句话总结**：控制输出 = 直接省钱。"请简洁回答"这 5 个字，可能是你写过的 ROI 最高的代码。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Token 乘数效应 | System Prompt 每多 1 token，月成本翻倍（按请求量） |
| 成本地图 | System Prompt 占输入 60%，是最大优化目标 |
| Prompt 瘦身 | 7 板斧砍掉 80%，从 1500 降到 300 tokens |
| 瘦身不影响质量 | 短 Prompt 有时效果更好（指令不矛盾） |
| Few-shot 陷阱 | 每个示例消耗 30-50 tokens，用 zero-shot+格式约束替代 |
| 动态 Few-shot | 只在需要时加 1 个最相关示例，省 60-80% |
| 输出约束 | "简洁回答"省 50-70%，JSON 格式省 70-80% |
| max_tokens | 硬限制输出长度，但可能截断 |

> **下一章预告**：缓存策略——相同的问题不要付两次钱。我们会实现精确缓存和语义缓存两种方案，用 Redis 构建 LLM 响应缓存，让重复问题的成本直接降为零。
