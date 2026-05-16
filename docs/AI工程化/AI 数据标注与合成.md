# AI 数据标注与合成

> 从人工标注到 LLM 辅助标注再到全自动合成数据——涵盖标注流程设计、标注规范制定、LLM-as-Annotator、合成数据生成策略、数据质量评估体系，一套完整方法论让你用更低的成本获得更高质量的训练数据。

---

## 1. 数据标注的重要性与挑战

### 1.1 "Garbage In, Garbage Out"：数据质量决定模型上限

在 AI 时代有一句话比任何时候都正确——**模型的天花板不是算法，而是数据**：

```
模型质量的决定因素：

  模型效果 = min(数据质量, 算法能力, 算力规模)

  数据质量 ▲
           │                    ● 高质量数据 + 好算法 = SOTA
           │          ● 中等数据 + 好算法 = 还行
           │ ● 垃圾数据 + 好算法 = 垃圾（GI/GO）
           └──────────────────────────→ 算法能力

  → 数据质量是木桶的最短板
```

> 💡 **OpenAI 不公开的秘密：GPT-4 的核心竞争力不是模型架构（Transformer 大家都有），而是百万级高质量人工标注数据（RLHF）。**

### 1.2 标注成本分析：人工 vs LLM vs 合成数据

| 方式 | 单条成本 | 质量 | 速度 | 适用场景 |
|:---|:---|:---|:---|:---|
| **纯人工标注** | ¥2-10/条 | ⭐⭐⭐⭐⭐ | 慢（100条/天/人） | 种子数据、高要求场景 |
| **LLM 辅助标注** | ¥0.1-0.5/条 | ⭐⭐⭐⭐ | 快（1000条/小时） | 扩量、预标注 |
| **合成数据** | ¥0.01-0.05/条 | ⭐⭐⭐ | 极快（万条/小时） | 大规模增强、冷启动 |
| **人工+LLM 混合** | ¥0.3-1/条 | ⭐⭐⭐⭐⭐ | 中（500条/小时） | **生产推荐** |

```
成本 vs 质量的最优路径：

  ① 人工标注 200 条种子数据      → ¥2,000  质量最高
  ② LLM 辅助扩量到 2,000 条     → ¥500   质量可控
  ③ 合成数据扩量到 10,000 条     → ¥200   补充覆盖
  
  总计 ¥2,700 获得 10,000 条可用数据
  vs 纯人工标注 10,000 条 → ¥50,000+
  
  → 成本节省 95%
```

### 1.3 标注的三大挑战：一致性 / 效率 / 覆盖度

```
三大挑战：

  ① 一致性 ─── 不同标注员对同一样本的判断不同
     │          "这条评论是中性还是负面？" → 3 个人 3 个答案
     │          解决：明确标注规范 + 交叉标注 + 仲裁机制
     │
  ② 效率 ──── 高质量标注很慢
     │          专业医疗标注：10 条/小时/人
     │          解决：LLM 预标注 + 人工修正 → 效率提升 3-5 倍
     │
  ③ 覆盖度 ── 真实场景千变万化，标注数据覆盖不全
                训练数据里没有方言 → 上线后方言全部判错
                解决：合成数据补充长尾场景
```

### 1.4 数据标注的技术演进：从纯人工到 AI 原生

```
数据标注的四个阶段：

  第一代（2015-2018）：纯人工
    └── 众包平台（MTurk）+ 简单规则

  第二代（2019-2021）：工具辅助
    └── 标注工具（Label Studio）+ 半自动化

  第三代（2022-2023）：LLM 辅助
    └── GPT-4 预标注 + 人工审核

  第四代（2024+）：AI 原生 ← 当前阶段
    └── 合成数据 + 自对弈 + 最少人工介入
```

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **数据 > 算法** | 数据质量是模型效果的天花板 |
| **混合标注** | 人工种子 + LLM 扩量 + 合成增强，成本降 95% |
| **三大挑战** | 一致性、效率、覆盖度 |
| **当前趋势** | AI 原生：合成数据 + 最少人工介入 |

---

## 2. 人工标注：流程设计与质量控制

### 2.1 标注需求分析：明确任务类型与标注 Schema

开始标注前，必须**定义清楚"标什么"和"怎么标"**：

```yaml
# 标注 Schema 示例：客服意图分类
task: intent_classification
version: v1.2

labels:
  - name: 咨询商品
    description: 用户询问商品信息（价格、规格、库存）
    examples: ["这个多少钱？", "有红色的吗？"]
  
  - name: 投诉问题
    description: 用户对商品或服务表达不满
    examples: ["收到的是坏的", "物流太慢了"]
  
  - name: 退换货
    description: 用户请求退货、换货或退款
    examples: ["我要退货", "能换个颜色吗"]
  
  - name: 闲聊
    description: 非业务相关的对话
    examples: ["你好", "今天天气怎么样"]

input_format: "单条用户消息文本"
output_format: '{"intent": "标签名", "confidence": "高/中/低"}'
ambiguity_rule: "当同时符合多个标签时，选择最具体的那个"
```

### 2.2 标注规范设计：Guideline 的核心要素

```
标注规范（Guideline）的 7 个必备部分：

  ① 任务描述 ─── 用一句话说清楚"这个任务在做什么"
  ② 标签定义 ─── 每个标签的精确定义 + 边界说明
  ③ 正面示例 ─── 每个标签 3-5 个典型案例
  ④ 反面示例 ─── "容易误标"的案例 + 正确标签
  ⑤ 边界案例 ─── 模糊地带的判定规则
  ⑥ 特殊情况 ─── 多标签、缺失信息怎么处理
  ⑦ FAQ ─────── 标注过程中常见疑问的标准答案
```

> 💡 **Guideline 的质量直接决定标注一致性**——花 2 天写一份好的 Guideline，比花 2 周修复不一致的标注数据划算得多。

### 2.3 标注工具选型：Label Studio / Doccano / Prodigy

| 工具 | 类型 | 部署 | 优势 | 适用场景 |
|:---|:---|:---|:---|:---|
| **Label Studio** | 开源 | 自部署 / 云 | 功能最全，支持所有任务 | **通用首选** |
| **Doccano** | 开源 | 自部署 | 轻量，NLP 专用 | 文本分类、NER |
| **Prodigy** | 商业 | 本地 | 主动学习内置 | 高效迭代标注 |
| **LabelBox** | 商业 | 云 | 多模态支持好 | 图片/视频标注 |

```bash
# Label Studio 一键部署
docker run -d -p 8080:8080 \
  -v label-studio-data:/label-studio/data \
  heartexlabs/label-studio:latest
```

### 2.4 质量控制机制：交叉标注 / IAA / 审核流程

```
质量控制的三道防线：

  第一道：交叉标注（每条数据 2-3 人标注）
    样本 A → 标注员1: 正面 | 标注员2: 正面 → 一致 ✅
    样本 B → 标注员1: 负面 | 标注员2: 中性 → 不一致 → 仲裁

  第二道：IAA（标注者间一致性）
    Cohen's Kappa > 0.8 → 优秀
    Cohen's Kappa 0.6-0.8 → 可接受
    Cohen's Kappa < 0.6 → 需要重新培训标注员

  第三道：抽样审核
    项目经理随机抽检 10% 的标注结果
    错误率 > 5% → 该标注员的数据全部返工
```

```python
from sklearn.metrics import cohen_kappa_score

def compute_iaa(annotator1: list, annotator2: list) -> dict:
    """计算标注者间一致性"""
    kappa = cohen_kappa_score(annotator1, annotator2)
    agreement = sum(a == b for a, b in zip(annotator1, annotator2)) / len(annotator1)
    
    quality = "优秀" if kappa > 0.8 else "可接受" if kappa > 0.6 else "需改进"
    return {"kappa": round(kappa, 3), "agreement": f"{agreement:.1%}", "quality": quality}
```

### 2.5 标注团队管理：培训、校准、迭代

```
标注团队管理的标准流程：

  ① 培训阶段（1-2 天）
     └── 讲解 Guideline → 试标 50 条 → 校准讨论

  ② 校准阶段（持续）
     └── 每周集体讨论边界案例 → 更新 Guideline

  ③ 监控阶段
     └── 计算每个标注员的 IAA → 低于阈值的人重新培训

  ④ 迭代阶段
     └── 分析错误模式 → 补充 Guideline → 重新标注争议样本
```

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Schema** | YAML 定义标签、示例、歧义规则 |
| **Guideline** | 7 要素：定义+正例+反例+边界+FAQ |
| **Label Studio** | 开源通用首选，Docker 一键部署 |
| **IAA** | Cohen's Kappa > 0.8 为优秀 |
| **团队管理** | 培训→校准→监控→迭代循环 |

---

## 3. LLM 辅助标注：用 AI 提升标注效率

### 3.1 LLM-as-Annotator：让大模型做标注员

用 GPT-4o 等大模型**直接做标注**——在很多任务上已经能达到甚至超过普通标注员的水平：

```python
async def llm_annotate(texts: list[str], schema: dict) -> list[dict]:
    """LLM 批量标注"""
    prompt = f"""
    你是一个专业的数据标注员。请按照以下标注规范标注文本：
    
    标签定义：{json.dumps(schema["labels"], ensure_ascii=False)}
    歧义规则：{schema["ambiguity_rule"]}
    
    对每条文本输出 JSON：{{"text": "原文", "label": "标签", "confidence": 0.0-1.0}}
    """
    
    results = []
    for batch in chunk(texts, 20):  # 每批 20 条
        batch_prompt = prompt + "\n\n待标注文本：\n" + "\n".join(
            f"{i+1}. {t}" for i, t in enumerate(batch)
        )
        response = await client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "user", "content": batch_prompt}],
            temperature=0,  # 标注任务用 0 温度
        )
        results.extend(json.loads(response.choices[0].message.content))
    
    return results
```

### 3.2 预标注 + 人工修正：效率提升 3-5 倍

最实用的模式——**LLM 先标一遍，人工只需要"改错"而不是"从头标"**：

```
预标注 + 人工修正流程：

  1000 条原始数据
    │
    ▼
  LLM 预标注（GPT-4o，temperature=0）
    │
    ├── 高置信度（>0.9）：650 条 → 人工抽检 10% → 直接采用
    ├── 中置信度（0.7-0.9）：250 条 → 人工逐条审核修正
    └── 低置信度（<0.7）：100 条 → 人工从头标注
    │
    ▼
  最终结果：1000 条高质量标注
  
  效率对比：
    纯人工：1000 条 × 2分钟/条 = 33 小时
    预标注+修正：
      抽检 65 条 + 审核 250 条 + 标注 100 条 ≈ 8 小时
    → 效率提升 4 倍
```

### 3.3 多模型共识标注：多个 LLM 投票决定标签

```python
async def consensus_annotate(text: str, models: list[str] = None) -> dict:
    """多模型共识标注：3 个模型投票"""
    models = models or ["gpt-4o", "claude-3-sonnet", "qwen-plus"]
    labels = []
    
    for model in models:
        result = await annotate_single(text, model)
        labels.append(result["label"])
    
    # 投票
    from collections import Counter
    vote = Counter(labels).most_common(1)[0]
    
    return {
        "text": text,
        "label": vote[0],
        "consensus": vote[1] / len(models),  # 一致度
        "votes": dict(zip(models, labels)),
        "needs_human": vote[1] < len(models),  # 不一致 → 转人工
    }
```

> 💡 **多模型共识的准确率通常比单模型高 5-8%**——不同模型的错误模式不同，投票能有效消除个体偏差。一致度 < 100% 的样本优先转人工审核。

### 3.4 主动学习：让模型选择最值得标注的样本

标注预算有限时，**不要随机选样本标注，而是让模型挑最"不确定"的样本**：

```python
class ActiveLearner:
    """主动学习：选择最值得标注的样本"""
    
    async def select_uncertain(self, pool: list[str], k: int = 50) -> list[str]:
        """选择模型最不确定的 k 个样本"""
        uncertainties = []
        
        for text in pool:
            # 用 LLM 标注 3 次（temperature > 0 引入随机性）
            labels = []
            for _ in range(3):
                result = await self.annotate(text, temperature=0.5)
                labels.append(result["label"])
            
            # 不确定性 = 标签多样性
            unique_labels = len(set(labels))
            uncertainties.append((text, unique_labels))
        
        # 返回最不确定的 k 个样本
        uncertainties.sort(key=lambda x: x[1], reverse=True)
        return [text for text, _ in uncertainties[:k]]
```

```
主动学习 vs 随机标注的效率对比：

  标注量 │ 随机标注准确率 │ 主动学习准确率
  ──────┼───────────────┼──────────────
  100 条 │    72%        │    78%
  200 条 │    78%        │    85%
  500 条 │    85%        │    91%

  → 用主动学习，标注 200 条 ≈ 随机标注 500 条的效果
```

### 3.5 LLM 标注的质量评估与校准

LLM 标注不是"标完就用"——需要**与人工标注对比校准**：

```python
def evaluate_llm_annotations(llm_labels: list, human_labels: list) -> dict:
    """评估 LLM 标注质量"""
    from sklearn.metrics import classification_report, confusion_matrix
    
    report = classification_report(human_labels, llm_labels, output_dict=True)
    cm = confusion_matrix(human_labels, llm_labels)
    
    return {
        "accuracy": report["accuracy"],
        "per_class": {k: v["f1-score"] for k, v in report.items() if k not in ["accuracy", "macro avg", "weighted avg"]},
        "confusion_matrix": cm.tolist(),
        "usable": report["accuracy"] > 0.90,  # 准确率 > 90% 才可用
    }
```

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **LLM-as-Annotator** | temperature=0 批量标注，成本降 90% |
| **预标注+修正** | LLM 先标，人工改错，效率提升 4 倍 |
| **多模型共识** | 3 个模型投票，准确率提升 5-8% |
| **主动学习** | 选最不确定的样本标注，200 条≈随机 500 条 |
| **质量校准** | 与人工标注对比，准确率 > 90% 才可用 |

---

## 4. 合成数据生成：从零构造训练数据

### 4.1 为什么需要合成数据：真实数据不够用的场景

```
合成数据的四大适用场景：

  ① 冷启动 ─── 新任务/新领域，完全没有标注数据
     例：刚进入法律行业，需要法律QA数据

  ② 长尾覆盖 ── 真实数据中罕见但重要的场景
     例：方言输入、极端情绪、专业术语

  ③ 隐私合规 ── 不能用真实用户数据训练
     例：医疗记录、金融数据、个人信息

  ④ 规模扩展 ── 人工标注太贵，需要快速扩量
     例：从 500 条人工数据扩展到 50,000 条
```

### 4.2 Self-Instruct：让 LLM 生成指令-回答对

Self-Instruct 是 Stanford Alpaca 使用的方法——**用少量种子任务引导 LLM 生成大量新任务**：

```python
async def self_instruct(seed_tasks: list[dict], n: int = 1000) -> list[dict]:
    """Self-Instruct：从种子任务扩展生成"""
    generated = []
    
    for i in range(0, n, 10):
        # 随机选 3 个种子作为示例
        examples = random.sample(seed_tasks + generated[:100], min(3, len(seed_tasks)))
        
        prompt = f"""
        以下是一些任务示例：
        {json.dumps(examples[:3], ensure_ascii=False, indent=2)}
        
        请生成 10 个新的、不同的任务。要求：
        1. 任务类型多样化（问答、分类、生成、翻译等）
        2. 难度从简单到复杂
        3. 不要重复已有任务
        
        输出 JSON 数组：[{{"instruction": "...", "input": "...", "output": "..."}}]
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,  # 生成任务用较高温度
        )
        new_tasks = json.loads(response.choices[0].message.content)
        generated.extend(new_tasks)
    
    return generated
```

### 4.3 Evol-Instruct：进化式指令增强

Evol-Instruct（WizardLM 采用的方法）**通过"进化"让简单指令变复杂**：

```python
EVOLUTION_STRATEGIES = {
    "add_constraint": "给以下指令增加一个约束条件，使其更具挑战性",
    "deepen": "让以下指令需要更深入的推理才能回答",
    "concretize": "让以下指令更加具体和详细",
    "increase_reasoning": "修改指令，使其需要多步推理",
    "broaden": "扩展指令的范围，使其涉及更多方面",
}

async def evolve_instruction(instruction: str, strategy: str) -> str:
    """进化一条指令"""
    prompt = f"""
    原始指令：{instruction}
    
    进化策略：{EVOLUTION_STRATEGIES[strategy]}
    
    请输出进化后的指令（只输出指令本身）：
    """
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()

# 示例
# 原始："什么是 Python？"
# add_constraint → "用 100 字以内解释什么是 Python，并给出一个代码示例"
# deepen → "对比 Python 和 Rust 在内存管理上的区别，并分析各自适用场景"
```

### 4.4 领域数据合成：从文档 / 知识库生成 QA 对

最适合 RAG 和垂直领域的方法——**从你自己的文档中生成 QA 对**：

```python
async def generate_qa_from_document(document: str, n_pairs: int = 20) -> list[dict]:
    """从文档生成 QA 对"""
    prompt = f"""
    根据以下文档内容，生成 {n_pairs} 个高质量的问答对。
    
    文档内容：
    {document[:3000]}
    
    要求：
    1. 问题要自然，像真实用户会问的
    2. 答案必须能从文档中找到依据
    3. 包含不同难度：简单事实题、理解题、推理题
    4. 包含一些文档中找不到答案的问题（标记为 "unanswerable"）
    
    输出 JSON：
    [{{"question": "...", "answer": "...", "difficulty": "easy|medium|hard", 
       "evidence": "文档中的依据句"}}]
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return json.loads(response.choices[0].message.content)
```

### 4.5 对话数据合成：多轮对话的自动生成

```python
async def generate_conversation(scenario: str, turns: int = 5) -> list[dict]:
    """合成多轮对话"""
    prompt = f"""
    请模拟一段 {turns} 轮的客服对话。

    场景：{scenario}
    
    要求：
    1. 用户的问题要自然、口语化
    2. 客服的回答要专业、有帮助
    3. 对话要有逻辑递进（不是每轮都独立）
    4. 包含追问、澄清、确认等自然对话元素
    
    输出格式：
    [{{"role": "user", "content": "..."}}, {{"role": "assistant", "content": "..."}}]
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(response.choices[0].message.content)

# 批量生成不同场景
scenarios = ["退货退款流程", "商品质量投诉", "物流延迟查询", "会员权益咨询"]
conversations = [await generate_conversation(s) for s in scenarios]
```

> 💡 **合成数据的最大风险是"模型幻觉"**——LLM 可能生成看起来合理但事实错误的数据。解决方案：对生成的 QA 对做事实一致性检查，或让另一个 LLM 验证答案是否与原文档一致。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Self-Instruct** | 种子任务引导 LLM 生成新任务 |
| **Evol-Instruct** | 5 种进化策略让简单指令变复杂 |
| **领域 QA 合成** | 从文档自动生成问答对 |
| **对话合成** | 按场景批量生成多轮对话 |
| **核心风险** | 模型幻觉→需事实一致性检查 |

---

## 5. 数据质量评估：确保数据可用

### 5.1 数据质量的五个维度：准确 / 一致 / 多样 / 均衡 / 新鲜

| 维度 | 定义 | 检测方法 | 达标标准 |
|:---|:---|:---|:---|
| **准确性** | 标签/内容是否正确 | 人工抽检 + LLM 验证 | > 95% |
| **一致性** | 相似样本的标签是否一致 | 近邻一致性检查 | > 90% |
| **多样性** | 是否覆盖足够多的场景 | 聚类 + 覆盖度分析 | > 80% 场景 |
| **均衡性** | 各类别样本比例是否合理 | 分布统计 | 无极端偏斜 |
| **新鲜度** | 数据是否反映当前需求 | 时间戳检查 | < 6 个月 |

### 5.2 自动质量检测：规则 + LLM 双重过滤

```python
class DataQualityFilter:
    """双重过滤器：规则 + LLM"""
    
    def filter(self, data: list[dict]) -> list[dict]:
        # 第一层：规则过滤（快速、零成本）
        clean = [d for d in data if self._rule_check(d)]
        
        # 第二层：LLM 过滤（慢，但能捕获语义问题）
        verified = [d for d in clean if await self._llm_check(d)]
        
        return verified
    
    def _rule_check(self, item: dict) -> bool:
        """规则过滤"""
        text = item.get("output", "")
        if len(text) < 10: return False                # 太短
        if len(text) > 5000: return False              # 太长
        if text.count("```") % 2 != 0: return False    # 代码块未闭合
        if "作为AI语言模型" in text: return False       # LLM 自我暴露
        if text == item.get("input"): return False     # 输出等于输入
        return True
    
    async def _llm_check(self, item: dict) -> bool:
        """LLM 质量检查"""
        prompt = f"""
        评估以下训练数据的质量（回答 PASS 或 FAIL）：
        指令：{item['instruction']}
        输出：{item['output'][:500]}
        
        FAIL 的标准：答非所问、事实错误、格式混乱、内容重复
        只回复 PASS 或 FAIL。
        """
        result = await self.llm(prompt)
        return "PASS" in result
```

### 5.3 数据去重：精确去重 / 语义去重 / MinHash

```python
from datasketch import MinHash, MinHashLSH

class DataDeduplicator:
    """三级去重"""
    
    def deduplicate(self, data: list[dict]) -> list[dict]:
        # Level 1: 精确去重（哈希）
        seen_hashes = set()
        unique = []
        for item in data:
            h = hashlib.md5(item["output"].encode()).hexdigest()
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique.append(item)
        
        # Level 2: 近似去重（MinHash LSH）
        lsh = MinHashLSH(threshold=0.8, num_perm=128)
        final = []
        for i, item in enumerate(unique):
            mh = MinHash(num_perm=128)
            for word in item["output"].split():
                mh.update(word.encode())
            
            if not lsh.query(mh):  # 没有近似重复
                lsh.insert(str(i), mh)
                final.append(item)
        
        return final
```

```
去重效果示例：

  原始数据：10,000 条
  精确去重后：9,200 条（去掉 800 条完全相同）
  MinHash 去重后：7,500 条（去掉 1,700 条近似重复）
  
  → 25% 的数据是冗余的
```

### 5.4 多样性评估：覆盖度分析与分布可视化

```python
from sklearn.cluster import KMeans
from collections import Counter

def evaluate_diversity(embeddings: list, labels: list, n_clusters: int = 20):
    """评估数据集多样性"""
    # 聚类分析
    kmeans = KMeans(n_clusters=n_clusters)
    clusters = kmeans.fit_predict(embeddings)
    
    cluster_sizes = Counter(clusters)
    coverage = len([c for c in cluster_sizes.values() if c > 0]) / n_clusters
    
    # 类别均衡性
    label_dist = Counter(labels)
    max_ratio = max(label_dist.values()) / min(label_dist.values())
    
    return {
        "coverage": f"{coverage:.0%}",          # 场景覆盖率
        "cluster_sizes": dict(cluster_sizes),    # 每个聚类的大小
        "label_balance": f"{max_ratio:.1f}:1",   # 类别比例
        "is_balanced": max_ratio < 5,            # 是否均衡
    }
```

### 5.5 数据偏见检测与缓解

```
常见的数据偏见类型：

  ① 长度偏见 ── 合成数据的回答普遍比人类标注长
     检测：比较合成 vs 人工数据的平均长度
     缓解：在生成 Prompt 中限制长度

  ② 风格偏见 ── 所有回答都是"首先...其次...最后..."
     检测：分析回答的开头词分布
     缓解：要求多样化的表达风格

  ③ 难度偏见 ── 合成指令偏简单或偏难
     检测：用 LLM 评估每条指令的难度
     缓解：Evol-Instruct 平衡难度分布

  ④ 文化偏见 ── 生成内容偏向英语文化
     检测：检查是否包含本土化内容
     缓解：在 Prompt 中明确文化背景
```

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **五维度** | 准确、一致、多样、均衡、新鲜 |
| **双重过滤** | 规则快速筛 + LLM 语义检查 |
| **MinHash** | 近似去重，去除表述相似的重复 |
| **覆盖度** | 聚类分析评估场景覆盖 |
| **偏见检测** | 长度/风格/难度/文化四类偏见 |

---

## 6. 数据管道：从标注到训练的工程化

### 6.1 数据格式标准化：Alpaca / ShareGPT / OpenAI 格式

```python
# ── Alpaca 格式（指令微调标准格式） ──
alpaca_format = {
    "instruction": "将以下英文翻译为中文",
    "input": "Hello, how are you?",
    "output": "你好，你怎么样？"
}

# ── ShareGPT 格式（多轮对话） ──
sharegpt_format = {
    "conversations": [
        {"from": "human", "value": "什么是 Python？"},
        {"from": "gpt", "value": "Python 是一种高级编程语言..."},
        {"from": "human", "value": "它和 Java 比有什么优势？"},
        {"from": "gpt", "value": "Python 相比 Java 有以下优势..."},
    ]
}

# ── OpenAI 格式（ChatML，微调专用） ──
openai_format = {
    "messages": [
        {"role": "system", "content": "你是一个翻译助手"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "你好"},
    ]
}
```

| 格式 | 用途 | 框架支持 |
|:---|:---|:---|
| **Alpaca** | 单轮指令微调 | LLaMA-Factory, Axolotl |
| **ShareGPT** | 多轮对话微调 | LLaMA-Factory, FastChat |
| **OpenAI (ChatML)** | OpenAI 微调 API | OpenAI Fine-tuning |

### 6.2 数据版本管理：DVC / HuggingFace Datasets

```bash
# ── DVC（Data Version Control）── 
pip install dvc

# 初始化 DVC
dvc init
dvc remote add -d storage s3://my-bucket/datasets

# 追踪数据集
dvc add data/train.jsonl
git add data/train.jsonl.dvc .gitignore
git commit -m "data: v1.0 初始标注 200 条种子数据"

# 版本切换
git checkout v2.0  # 切到 v2.0 的代码
dvc checkout       # 自动切到 v2.0 对应的数据
```

### 6.3 数据增强策略：回译 / 改写 / 噪声注入

```python
async def augment_data(item: dict, strategy: str) -> dict:
    """数据增强"""
    if strategy == "backtranslation":
        # 回译：中文→英文→中文，获得不同措辞
        en = await translate(item["output"], "zh", "en")
        augmented = await translate(en, "en", "zh")
    
    elif strategy == "paraphrase":
        # 改写：保持语义不变，换一种表达
        augmented = await llm(f"用不同的措辞改写以下文本，保持含义不变：\n{item['output']}")
    
    elif strategy == "noise":
        # 噪声注入：模拟用户的错别字、口语化
        augmented = await llm(f"将以下文本改写为口语化风格，可以加入一些自然的语气词：\n{item['input']}")
    
    return {**item, "output": augmented, "augmented": True}
```

### 6.4 端到端数据管道：从原始文档到训练就绪数据集

```
端到端数据管道：

  原始数据
    │
    ▼
  ① 预处理 ─── 格式统一、编码清洗、长度截断
    │
    ▼
  ② 标注 ───── 人工种子 → LLM 扩量 → 合成增强
    │
    ▼
  ③ 质量检查 ── 规则过滤 → LLM 检查 → 人工抽检
    │
    ▼
  ④ 去重 ───── 精确去重 → MinHash 近似去重
    │
    ▼
  ⑤ 格式转换 ── 转为 Alpaca / ShareGPT / OpenAI 格式
    │
    ▼
  ⑥ 数据拆分 ── train(90%) / val(5%) / test(5%)
    │
    ▼
  ⑦ 版本发布 ── DVC 提交 + 打 tag + 写 changelog
    │
    ▼
  训练就绪数据集 ✅
```

### 6.5 数据配比策略：多任务混合训练的配比艺术

```python
# 多任务数据配比
DATASET_MIX = {
    "general_chat": {"ratio": 0.30, "source": "通用对话"},
    "domain_qa":    {"ratio": 0.25, "source": "领域问答"},
    "instruction":  {"ratio": 0.20, "source": "指令跟随"},
    "code":         {"ratio": 0.15, "source": "代码生成"},
    "safety":       {"ratio": 0.10, "source": "安全对齐"},
}
```

> 💡 **配比原则：核心任务占比 > 30%，安全数据至少 10%**。配比不对会导致模型"偏科"——代码数据太多会降低对话能力，安全数据太少会导致有害输出。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Alpaca/ShareGPT** | 单轮用 Alpaca，多轮用 ShareGPT |
| **DVC** | Git for Data，数据版本管理 |
| **数据增强** | 回译、改写、噪声注入三种策略 |
| **端到端管道** | 预处理→标注→质检→去重→格式→拆分→发布 |
| **配比策略** | 核心 > 30%、安全 ≥ 10%，避免偏科 |

---

## 7. 实战案例：构建一个垂直领域的训练数据集

> 💡 **本章用一个完整案例串联前面所有章节的知识**——为电商客服场景从零构建 10,000 条 SFT 训练数据集，经历需求分析 → 人工种子 → LLM 扩量 → 合成增强 → 质量评估 → 最终交付的全流程。

### 7.1 需求分析：为客服场景构建 SFT 数据集

**项目背景**：某电商公司要微调一个 7B 模型作为智能客服，替代人工处理 70% 的常见咨询。

```
项目关键约束：

  目标 ──── 微调 Qwen2-7B 为电商客服助手
  数据量 ── 至少 10,000 条 SFT 数据
  预算 ──── ¥5,000（含人工标注 + API 调用）
  工期 ──── 2 周
  质量 ──── 人工抽检准确率 > 90%
```

**第一步：定义任务类型与覆盖场景**：

```
客服场景分类树：

  电商客服
    ├── 售前咨询（35%）
    │     ├── 商品信息查询
    │     ├── 价格/优惠/满减
    │     └── 库存/发货时间
    │
    ├── 售中服务（25%）
    │     ├── 订单状态查询
    │     ├── 修改订单信息
    │     └── 催发货
    │
    ├── 售后处理（30%）
    │     ├── 退货退款
    │     ├── 换货
    │     ├── 质量投诉
    │     └── 物流异常
    │
    └── 其他（10%）
          ├── 账户问题
          ├── 发票需求
          └── 闲聊/无关

  → 13 个细分场景，每个场景需要 700-800 条数据
```

**第二步：定义标注 Schema 与数据格式**：

```yaml
# customer_service_schema.yaml
task: customer_service_sft
version: v1.0

data_format: sharegpt  # 多轮对话格式
min_turns: 2
max_turns: 8
languages: ["zh-CN"]

intent_labels:
  - 商品查询
  - 价格优惠
  - 库存发货
  - 订单查询
  - 修改订单
  - 催发货
  - 退货退款
  - 换货
  - 质量投诉
  - 物流异常
  - 账户问题
  - 发票需求
  - 闲聊

response_requirements:
  tone: "专业友好，不卑不亢"
  max_length: 200  # 单轮回答不超过 200 字
  must_include: ["解决方案", "下一步操作指引"]
  forbidden: ["我不知道", "你自己看", "这不归我管"]
```

**第三步：制定执行计划**：

```
数据构建计划（2 周）：

  Week 1：
    Day 1-2 ── 编写标注 Guideline + 培训标注员
    Day 3-5 ── 人工标注 200 条种子数据（Phase 1）

  Week 2：
    Day 6-7 ── LLM 辅助扩量到 2,000 条（Phase 2）
    Day 8-9 ── 合成数据增强到 10,000 条（Phase 3）
    Day 10  ── 质量评估 + 数据交付

  预算分配：
    人工标注：200 条 × ¥5/条 = ¥1,000
    LLM 扩量：2,000 条 × ¥0.3/条 = ¥600
    合成生成：10,000 条 × ¥0.05/条 = ¥500
    质量检查：LLM 验证 + 人工抽检 = ¥400
    总计：¥2,500（预算内 ✅）
```

### 7.2 Phase 1：人工标注种子数据（200 条）

**编写标注 Guideline**（参考第 2 章 2.2 节的 7 要素框架）：

```markdown
# 电商客服对话标注指南 v1.0

## 任务描述
标注多轮客服对话数据，每条数据包含用户问题和客服回答。

## 标签定义与边界案例

| 意图 | 属于 | 不属于（易混淆） |
|:---|:---|:---|
| 退货退款 | "买了不想要了""质量有问题退款" | "能不能便宜点" → 价格优惠 |
| 质量投诉 | "颜色和图片不一样""有划痕" | "还没收到" → 物流异常 |
| 催发货 | "什么时候发货""已经3天了" | "修改地址" → 修改订单 |

## 回答规范
- 语气：专业友好（"亲，非常抱歉给您带来不便"）
- 结构：共情 → 解决方案 → 下一步指引
- 禁止用语："不知道""你自己看""不归我管"
```

**种子数据标注流程**：

```python
import json
from pathlib import Path

# ── 从历史客服记录中提取原始对话 ──
def extract_raw_conversations(log_dir: str, n: int = 300) -> list[dict]:
    """从客服日志中提取原始对话（多取 50% 用于筛选）"""
    conversations = []
    for log_file in Path(log_dir).glob("*.json"):
        with open(log_file) as f:
            records = json.load(f)
            for record in records:
                if 2 <= len(record["messages"]) <= 8:
                    conversations.append({
                        "id": record["session_id"],
                        "messages": record["messages"],
                        "timestamp": record["created_at"],
                    })
    
    # 按场景均匀采样，避免某个意图过多
    return stratified_sample(conversations, n)

# ── 标注员分配 ──
# 3 名标注员，每人标注 100 条（交叉率 50%）
# 总工作量：300 条标注 → 200 条最终数据（100 条双标注用于 IAA）
```

**交叉标注与质量校准**：

```python
from sklearn.metrics import cohen_kappa_score

def calibrate_seed_data(annotations: dict) -> list[dict]:
    """校准种子数据：处理标注分歧"""
    final_data = []
    
    for sample_id, labels in annotations.items():
        annotators = list(labels.keys())
        
        if len(annotators) == 1:
            # 单人标注 → 直接采用
            final_data.append(labels[annotators[0]])
        elif labels[annotators[0]]["intent"] == labels[annotators[1]]["intent"]:
            # 双标注一致 → 采用
            final_data.append(labels[annotators[0]])
        else:
            # 不一致 → 提交项目经理仲裁
            arbitrated = arbitrate(sample_id, labels)
            final_data.append(arbitrated)
    
    # 计算 IAA
    a1 = [annotations[sid]["annotator_1"]["intent"] for sid in cross_annotated]
    a2 = [annotations[sid]["annotator_2"]["intent"] for sid in cross_annotated]
    kappa = cohen_kappa_score(a1, a2)
    print(f"标注者间一致性 Kappa = {kappa:.3f}")  # 目标 > 0.8
    
    return final_data
```

```
Phase 1 产出：

  输入：300 条历史客服对话
  标注：3 人 × 100 条，交叉标注 50%
  质量：Kappa = 0.83（优秀）
  产出：200 条高质量种子数据
  耗时：3 天
  成本：¥1,000
```

### 7.3 Phase 2：LLM 辅助扩量（2000 条）

用 200 条种子数据引导 LLM 批量生成，然后**按置信度分层审核**：

```python
import asyncio
import json
from typing import AsyncIterator

async def llm_expand_dataset(
    seed_data: list[dict], 
    target_count: int = 2000,
    schema: dict = None,
) -> list[dict]:
    """Phase 2: LLM 辅助扩量"""
    expanded = []
    
    for intent, seeds in group_by_intent(seed_data).items():
        # 每个意图生成 ~150 条
        target_per_intent = target_count // len(schema["intent_labels"])
        
        for batch_idx in range(0, target_per_intent, 10):
            # 随机选 3 条种子作为 Few-shot 示例
            examples = random.sample(seeds, min(3, len(seeds)))
            
            prompt = f"""
            你是电商客服对话数据生成专家。
            
            参考以下真实对话示例：
            {json.dumps(examples, ensure_ascii=False, indent=2)}
            
            请生成 10 条新的「{intent}」场景对话。要求：
            1. 对话 2-6 轮，用户口语化、客服专业
            2. 场景多样：不同商品类型、不同问题细节
            3. 不要照搬示例，要有创新的场景变化
            4. 包含追问、澄清等自然对话元素
            
            输出 JSON 数组，每条格式：
            {{"intent": "{intent}", "conversations": [
                {{"from": "human", "value": "..."}},
                {{"from": "gpt", "value": "..."}}
            ], "confidence": 0.0-1.0}}
            """
            
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            batch = json.loads(response.choices[0].message.content)
            expanded.extend(batch)
    
    return expanded
```

**按置信度分层处理**——不是所有 LLM 生成的数据都同等对待：

```python
def triage_by_confidence(expanded: list[dict]) -> dict:
    """按置信度分层"""
    tiers = {"auto_accept": [], "human_review": [], "regenerate": []}
    
    for item in expanded:
        conf = item.get("confidence", 0.5)
        
        if conf >= 0.9:
            tiers["auto_accept"].append(item)     # 高置信 → 抽检 10%
        elif conf >= 0.7:
            tiers["human_review"].append(item)     # 中置信 → 逐条审核
        else:
            tiers["regenerate"].append(item)        # 低置信 → 重新生成
    
    return tiers

# 对中置信度的数据用多模型共识做二次验证
async def consensus_verify(items: list[dict]) -> list[dict]:
    """多模型共识验证"""
    verified = []
    for item in items:
        votes = []
        for model in ["gpt-4o", "claude-3-sonnet", "qwen-plus"]:
            result = await verify_single(item, model)
            votes.append(result["is_valid"])
        
        if sum(votes) >= 2:  # 至少 2/3 模型认为合格
            verified.append(item)
    
    return verified
```

```
Phase 2 产出：

  LLM 生成：2,500 条（多生成 25% 用于筛选）
  ├── 高置信（≥0.9）：1,600 条 → 抽检 10% 通过率 95%
  ├── 中置信（0.7-0.9）：650 条 → 共识验证通过 520 条
  └── 低置信（<0.7）：250 条 → 丢弃重生成

  最终保留：2,120 条（含 200 条种子）
  质量：人工抽检准确率 93%
  耗时：2 天
  成本：¥600（API 费用）
```

### 7.4 Phase 3：合成数据增强（10000 条）

从 2,000 条扩展到 10,000 条，需要**三种合成策略组合**：

```
合成策略组合：

  策略 ① Evol-Instruct 进化 ─── 从已有对话衍生更复杂的变体
    2,000 条 → 进化 → 4,000 条

  策略 ② 场景模板批量生成 ─── 用模板 + 变量组合批量生成
    模板 × 变量 → 3,000 条

  策略 ③ 长尾场景专项补充 ─── 针对覆盖不足的场景专项生成
    分析缺口 → 补充 1,000 条

  合计：2,000 + 4,000 + 3,000 + 1,000 = 10,000 条
```

**策略 ①：Evol-Instruct 进化已有对话**：

```python
async def evolve_conversations(
    base_data: list[dict], 
    n_evolved: int = 4000,
) -> list[dict]:
    """从已有对话进化出更复杂的变体"""
    strategies = [
        ("add_complication", "在对话中增加一个复杂情况（如跨订单、多商品）"),
        ("add_emotion",      "让用户带有更强烈的情绪（焦急、愤怒、失望）"),
        ("add_followup",     "在对话末尾增加 2 轮追问和解答"),
        ("change_product",   "将对话中的商品类型换成完全不同的品类"),
        ("add_policy",       "让客服回答中引用具体的平台政策条款"),
    ]
    
    evolved = []
    for item in random.sample(base_data, min(len(base_data), n_evolved)):
        strategy_name, strategy_desc = random.choice(strategies)
        
        prompt = f"""
        对以下客服对话进行进化改写：
        
        原始对话：{json.dumps(item["conversations"], ensure_ascii=False)}
        
        进化策略：{strategy_desc}
        
        要求：保持意图类别「{item['intent']}」不变，输出完整的新对话。
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )
        new_conv = json.loads(response.choices[0].message.content)
        evolved.append({**item, "conversations": new_conv, "source": "evolved"})
    
    return evolved
```

**策略 ②：场景模板批量生成**：

```python
# 定义模板变量
TEMPLATE_VARS = {
    "product_types": ["手机壳", "连衣裙", "运动鞋", "蓝牙耳机", "儿童玩具",
                      "化妆品", "书籍", "家具", "食品", "数码配件"],
    "issue_details": {
        "退货退款": ["不喜欢颜色", "尺码不合适", "和描述不符", "质量问题", "买多了"],
        "物流异常": ["显示已签收但没收到", "物流3天没更新", "快递破损", "送错地址"],
        "质量投诉": ["有划痕", "少了配件", "包装破损", "功能异常", "做工粗糙"],
    },
    "user_tones": ["礼貌", "着急", "不满", "犹豫", "简短直接"],
}

async def template_generate(n: int = 3000) -> list[dict]:
    """模板 + 变量组合批量生成"""
    generated = []
    
    for _ in range(n // 5):  # 每次生成 5 条
        product = random.choice(TEMPLATE_VARS["product_types"])
        intent = random.choice(list(TEMPLATE_VARS["issue_details"].keys()))
        detail = random.choice(TEMPLATE_VARS["issue_details"][intent])
        tone = random.choice(TEMPLATE_VARS["user_tones"])
        
        prompt = f"""
        生成 5 条电商客服对话，场景参数：
        - 商品：{product}
        - 意图：{intent}
        - 具体问题：{detail}
        - 用户语气：{tone}
        
        每条对话 3-5 轮，输出 ShareGPT 格式 JSON 数组。
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # 用更便宜的模型做批量生成
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
        )
        generated.extend(json.loads(response.choices[0].message.content))
    
    return generated
```

**策略 ③：长尾场景专项补充**：

```python
def analyze_coverage_gaps(current_data: list[dict]) -> list[str]:
    """分析覆盖缺口"""
    from collections import Counter
    
    intent_dist = Counter(item["intent"] for item in current_data)
    avg = len(current_data) / len(intent_dist)
    
    gaps = []
    for intent, count in intent_dist.items():
        if count < avg * 0.5:  # 低于平均值 50% 的意图
            gaps.append(f"{intent}（当前 {count} 条，目标 {int(avg)} 条）")
    
    # 检查是否缺少特殊场景
    special_scenes = ["方言用户", "老年用户", "多商品订单", "跨境购物", "直播间下单"]
    for scene in special_scenes:
        if not any(scene in str(item) for item in current_data):
            gaps.append(f"缺少场景：{scene}")
    
    return gaps

# 输出示例：
# ["闲聊（当前 80 条，目标 150 条）", "缺少场景：方言用户", "缺少场景：老年用户"]
# → 针对这些缺口专项生成补充数据
```

```
Phase 3 产出：

  Evol-Instruct 进化：4,200 条 → 去重后 3,800 条
  模板批量生成：3,200 条 → 质量过滤后 2,900 条
  长尾场景补充：1,100 条 → 过滤后 1,000 条

  Phase 3 新增：7,700 条
  累计总量：2,120 + 7,700 = 9,820 条
  补录缺口到 10,000 条 ✅
  耗时：2 天
  成本：¥500（主要用 gpt-4o-mini）
```

### 7.5 质量评估与最终交付

10,000 条数据生成后，**全量质检是最后一道关卡**：

```python
async def final_quality_audit(dataset: list[dict]) -> dict:
    """最终质量审计：五维度检查"""
    
    # ── 维度 1：准确性（抽检 500 条） ──
    sample = random.sample(dataset, 500)
    accuracy_checks = []
    for item in sample:
        result = await llm_verify(item)  # LLM 验证
        accuracy_checks.append(result["is_correct"])
    accuracy = sum(accuracy_checks) / len(accuracy_checks)
    
    # ── 维度 2：一致性（近邻检查） ──
    embeddings = await batch_embed([str(d["conversations"]) for d in dataset])
    consistency = check_neighbor_consistency(embeddings, dataset)
    
    # ── 维度 3：多样性（聚类覆盖） ──
    diversity = evaluate_diversity(embeddings, [d["intent"] for d in dataset])
    
    # ── 维度 4：均衡性（分布统计） ──
    from collections import Counter
    intent_dist = Counter(d["intent"] for d in dataset)
    balance_ratio = max(intent_dist.values()) / min(intent_dist.values())
    
    # ── 维度 5：去重 ──
    dedup = DataDeduplicator()
    clean_data = dedup.deduplicate(dataset)
    dedup_ratio = 1 - len(clean_data) / len(dataset)
    
    return {
        "accuracy": f"{accuracy:.1%}",          # 目标 > 90%
        "consistency": f"{consistency:.1%}",     # 目标 > 85%
        "coverage": diversity["coverage"],       # 目标 > 80%
        "balance_ratio": f"{balance_ratio:.1f}:1",  # 目标 < 5:1
        "dedup_ratio": f"{dedup_ratio:.1%}",     # 去重比例
        "final_count": len(clean_data),
    }
```

**格式转换与数据拆分**：

```python
def prepare_final_dataset(clean_data: list[dict], output_dir: str):
    """准备最终交付的数据集"""
    
    # ── 转换为 ShareGPT 格式 ──
    formatted = []
    for item in clean_data:
        formatted.append({
            "conversations": item["conversations"],
            "metadata": {
                "intent": item["intent"],
                "source": item.get("source", "human"),  
                "quality_score": item.get("quality_score", 1.0),
            }
        })
    
    # ── 按 90/5/5 拆分 ──
    random.shuffle(formatted)
    n = len(formatted)
    train = formatted[:int(n * 0.9)]
    val = formatted[int(n * 0.9):int(n * 0.95)]
    test = formatted[int(n * 0.95):]
    
    # ── 写入文件 ──
    for split, data in [("train", train), ("val", val), ("test", test)]:
        path = f"{output_dir}/{split}.jsonl"
        with open(path, "w") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"{split}: {len(data)} 条 → {path}")
    
    # ── DVC 版本管理 ──
    # dvc add data/customer_service_sft/
    # git commit -m "data: v1.0 客服SFT数据集 10,000条"

# 输出：
# train: 9,000 条 → data/train.jsonl
# val:     500 条 → data/val.jsonl
# test:    500 条 → data/test.jsonl
```

```
最终项目汇总：

  ┌─────────────────────────────────────────────┐
  │         客服 SFT 数据集 v1.0                 │
  ├─────────────┬───────────────────────────────┤
  │ 总量         │ 10,000 条                     │
  │ 格式         │ ShareGPT（多轮对话）           │
  │ 意图覆盖     │ 13 个场景，覆盖率 100%         │
  │ 数据来源     │ 人工 2% + LLM 20% + 合成 78%  │
  │ 准确率       │ 93%（LLM 验证 + 人工抽检）     │
  │ 一致性       │ 89%（近邻检查）                │
  │ 去重后       │ 9,800 条（去重率 2%）           │
  ├─────────────┼───────────────────────────────┤
  │ 总成本       │ ¥2,500                        │
  │ 总工期       │ 10 天                          │
  │ vs 纯人工    │ ¥50,000 + 50天                │
  │ 节省         │ 成本 95% ↓  工期 80% ↓        │
  └─────────────┴───────────────────────────────┘
```

**第 7 章核心知识回顾：**

| 阶段 | 做了什么 | 产出 | 成本 |
|:---|:---|:---|:---|
| **需求分析** | Schema + 场景树 + 执行计划 | 标注规范 | - |
| **Phase 1** | 人工标注 + 交叉校准 | 200 条种子 | ¥1,000 |
| **Phase 2** | LLM 扩量 + 分层审核 | 2,000 条 | ¥600 |
| **Phase 3** | 进化 + 模板 + 长尾补充 | 10,000 条 | ¥500 |
| **质量评估** | 五维审计 + 去重 + 拆分 | 交付数据集 | ¥400 |

---

## 附录

### A. 标注规范模板
### B. 数据格式速查表
### C. 工具与资源推荐
