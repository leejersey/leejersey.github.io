# 大模型微调实战（LoRA/QLoRA）

> 从"调 API"到"训自己的模型"——用最低成本（单张消费级显卡）微调大语言模型，让它精通你的专属领域。

---

## 1. 为什么要微调？什么时候该微调？

你已经会用 LLM 的 API 了——写好 prompt，拿到回答。但有些场景，无论你怎么调 prompt，效果就是不够好。这时候就该考虑**微调（Fine-tuning）**了。

### 1.1 三种让 LLM "变聪明"的方式

| 方式 | 原理 | 成本 | 适用场景 |
|:---|:---|:---|:---|
| **Prompt Engineering** | 用精心设计的提示词引导模型 | 💰 最低 | 通用任务、快速验证 |
| **RAG（检索增强）** | 检索外部文档，拼进 prompt | 💰💰 中等 | 私有知识库问答 |
| **微调（Fine-tuning）** | 修改模型权重，让它"学会"新知识/风格 | 💰💰💰 较高 | 风格定制、格式控制、领域专精 |

```
决策流程：

你的需求是什么？
│
├── 模型能力够，只是表达不对 → Prompt Engineering
├── 需要基于私有数据回答 → RAG
├── 需要特定的输出格式/风格 → 微调 ✅
├── 需要领域专业知识（医疗/法律/金融） → 微调 ✅ 或 RAG
└── 需要降低推理成本（大模型→小模型蒸馏） → 微调 ✅
```

### 1.2 微调的适用场景：风格、格式、领域知识

**✅ 适合微调的场景：**

```python
# 场景 1：统一输出格式
# 你需要 LLM 始终按特定 JSON Schema 返回，prompt 很难 100% 保证
{"diagnosis": "...", "confidence": 0.95, "evidence": ["...", "..."]}

# 场景 2：定制对话风格
# 你需要客服机器人用特定语气、遵守特定话术规范
"亲，非常感谢您的反馈！关于您提到的退货问题，小智马上帮您处理～"

# 场景 3：领域知识内化
# 让模型"记住"你的产品文档、代码规范、行业术语
# （比 RAG 更快，不需要每次检索）

# 场景 4：小模型替代大模型
# 用大模型生成训练数据 → 微调小模型 → 降低推理成本 90%
```

**❌ 不适合微调的场景：**

- 知识会频繁更新（用 RAG 更灵活）
- 只有几十条数据（数据太少效果差）
- 调 prompt 就能解决的问题（杀鸡用牛刀）

### 1.3 微调的成本与收益：值不值得？

| 项目 | 全参数微调 | LoRA | QLoRA |
|:---|:---|:---|:---|
| 7B 模型显存需求 | ~56 GB | ~16 GB | ~6 GB |
| 可用显卡 | A100 80GB | RTX 4090 | RTX 4060 |
| 训练时长（1000条数据） | ~2 小时 | ~30 分钟 | ~45 分钟 |
| 云端 GPU 费用 | ~¥50 | ~¥15 | ~¥8 |
| 效果 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

> 💡 **结论**：对于大部分场景，LoRA/QLoRA 的效果已经非常接近全参数微调，但成本降低了 80%+。本教程重点讲 LoRA 和 QLoRA。

### 1.4 全参数微调 vs 参数高效微调（PEFT）

```
全参数微调（Full Fine-tuning）：
  修改模型的所有参数（70 亿个）
  ✅ 效果最好
  ❌ 需要超大显存，训练慢

参数高效微调（PEFT = Parameter-Efficient Fine-Tuning）：
  只修改一小部分参数（几百万个，<1%）
  ✅ 显存需求低，训练快
  ✅ 可以保存多个"适配器"，按需切换
  ❌ 效果略差于全参（但差距很小）
```

**PEFT 家族的主要方法：**

| 方法 | 原理 | 流行度 |
|:---|:---|:---|
| **LoRA** | 在权重矩阵旁插入低秩适配器 | ⭐⭐⭐⭐⭐ 最主流 |
| **QLoRA** | LoRA + 4-bit 量化 = 更省显存 | ⭐⭐⭐⭐⭐ 消费级首选 |
| Prefix Tuning | 在输入前插入可学习的向量 | ⭐⭐ |
| Adapter | 在每层 Transformer 中插入小模块 | ⭐⭐ |
| IA³ | 学习缩放向量 | ⭐ |

> 💡 **本教程聚焦 LoRA 和 QLoRA**——它们是目前工业界最广泛使用的微调方法，效果好、生态成熟、工具链完善。

---

## 2. LoRA 原理：用 0.1% 的参数撬动整个模型

理解 LoRA 的原理不需要数学博士学位。这一节用最直觉的方式解释它为什么能工作。

### 2.1 全量微调的问题：参数太多，显存不够

一个 7B 模型有 70 亿个参数。全量微调时，每个参数都需要存储：

```
全量微调的显存开销：

模型参数（FP16）：     7B × 2 bytes = 14 GB
梯度（FP16）：         7B × 2 bytes = 14 GB
优化器状态（AdamW）：  7B × 8 bytes = 56 GB  ← 这才是大头！
──────────────────────────────────────────
总计：                                  ~84 GB

结论：一张 A100 80GB 都不太够！
```

> 💡 **核心矛盾**：模型有 70 亿个参数，但微调一个特定任务可能只需要调整其中很小一部分。全量微调是"大炮打蚊子"。

### 2.2 LoRA 的核心思想：低秩分解

LoRA 的核心论文提出了一个关键观察：**微调时的权重变化矩阵 ΔW 是低秩的**——也就是说，它可以用两个小矩阵的乘积来近似。

```
原始权重矩阵 W：4096 × 4096 = 16,777,216 个参数

全量微调：
  W_new = W + ΔW
  ΔW 也是 4096 × 4096 = 16,777,216 个参数 ← 太多了！

LoRA 的做法：
  ΔW ≈ A × B
  A: 4096 × 8    = 32,768 个参数
  B: 8 × 4096    = 32,768 个参数
  总计：            65,536 个参数  ← 只有原来的 0.4%！

  其中 8 就是 rank（秩），控制"压缩程度"
```

**用图来理解：**

```
                    ┌─────────────┐
  输入 ──→ 原始权重 W（冻结🧊）  ──→ 输出
  x     │              │
        │   ┌───┐ ┌───┐│
        └──→│ A │→│ B │┘  ← LoRA 适配器（可训练🔥）
            │4096│ │ 8 │
            │× 8 │ │×  │
            └───┘ └4096┘
                    │
                    ↓
              ΔW = A × B
```

**训练时**：冻结原始权重 W，只训练 A 和 B。
**推理时**：把 A × B 的结果加回到 W 上，模型大小不变。

### 2.3 直觉理解：给模型加"外挂适配器"

把 LoRA 想象成**给一个已经训练好的员工加一个"技能备忘录"**：

```
类比：

原始模型 = 一个通才员工（什么都会一点，但不精通你的业务）
全量微调 = 送员工回学校重新学（太贵太慢）
LoRA    = 给员工一本薄薄的"工作手册"（快速上手，随时可替换）

手册（LoRA 适配器）的特点：
- 很薄（参数量小，~几 MB）
- 可以叠加多本（多任务切换）
- 不改变员工本身（原始模型不变）
- 取掉手册后，员工恢复原样
```

**LoRA 的三大优势：**

| 优势 | 说明 |
|:---|:---|
| **省显存** | 只训练 <1% 的参数，显存降低 80%+ |
| **多任务切换** | 一个基础模型 + 多个 LoRA，按需加载 |
| **合并无损** | 训练完后 A×B 加回 W，推理速度不变 |

### 2.4 关键超参数：rank、alpha、target_modules

```python
from peft import LoraConfig

lora_config = LoraConfig(
    r=8,                    # rank：低秩分解的秩
    lora_alpha=16,          # 缩放因子
    target_modules=["q_proj", "v_proj"],  # 应用 LoRA 的层
    lora_dropout=0.05,      # Dropout 防过拟合
    bias="none",            # 是否训练偏置
    task_type="CAUSAL_LM",  # 任务类型
)
```

**各参数详解：**

| 参数 | 含义 | 推荐值 | 影响 |
|:---|:---|:---|:---|
| **r (rank)** | 低秩矩阵的秩 | 8~64 | 越大 → 能力越强，但参数越多 |
| **lora_alpha** | 缩放因子（实际缩放 = alpha/r） | 通常 = 2×r | 控制 LoRA 权重的"影响力" |
| **target_modules** | 把 LoRA 加到哪些层 | q_proj, v_proj, k_proj, o_proj | 越多层 → 效果越好，显存越大 |
| **lora_dropout** | Dropout 概率 | 0.05~0.1 | 防止过拟合 |

```
rank 的选择经验：

r=8  ：简单任务（风格迁移、格式统一），够用
r=16 ：中等任务（领域知识、指令遵循），默认推荐
r=32 ：复杂任务（多技能、高精度要求）
r=64+：很少需要，边际收益递减
```

> 💡 **target_modules 怎么选？** 对于大部分模型，**至少加到 q_proj 和 v_proj**（注意力机制的核心）。想要更好效果，可以加上 k_proj、o_proj、gate_proj、up_proj、down_proj（基本覆盖所有线性层）。

### 2.5 QLoRA：4-bit 量化 + LoRA = 消费级显卡也能跑

QLoRA 在 LoRA 的基础上加了一层优化：**把基础模型量化到 4-bit 加载**，进一步压缩显存。

```
LoRA 的显存构成：
  基础模型（FP16）：14 GB   ← 大头
  LoRA 参数：        ~50 MB  ← 很小
  优化器状态：        ~200 MB ← 只有 LoRA 参数的
  ──────────────────────────
  总计：              ~16 GB  → RTX 4090 ✅

QLoRA 的改进：
  基础模型（4-bit）：  ~4 GB  ← 量化后大幅缩小！
  LoRA 参数（FP16）：  ~50 MB
  优化器状态：          ~200 MB
  ──────────────────────────
  总计：               ~6 GB  → RTX 4060 ✅
```

**QLoRA 的关键技术：**

| 技术 | 作用 |
|:---|:---|
| **NF4 量化** | 一种专为正态分布权重设计的 4-bit 量化格式 |
| **双重量化** | 对量化参数本身再做一次量化，进一步省内存 |
| **分页优化器** | 显存不够时自动转移到 CPU 内存 |

> 💡 **LoRA vs QLoRA 一句话总结**：如果你的显卡显存够（≥16 GB），用 LoRA（训练更快，精度略高）。如果显存紧张（8~12 GB），用 QLoRA（牺牲一点速度换显存空间）。

---

## 3. 环境搭建与工具链

工欲善其事必先利其器。微调大模型需要 GPU、正确的依赖版本、以及对 Hugging Face 生态的基本了解。

### 3.1 硬件要求：不同模型需要多少显存？

| 模型大小 | LoRA (FP16) | QLoRA (4-bit) | 推荐显卡 |
|:---|:---|:---|:---|
| **1.5B** (Qwen2.5-1.5B) | ~6 GB | ~3 GB | RTX 4060 / 3060 |
| **7B** (Qwen2.5-7B, Llama3-8B) | ~18 GB | ~8 GB | RTX 4090 / 3090 |
| **14B** (Qwen2.5-14B) | ~32 GB | ~12 GB | RTX 4090 24GB |
| **32B** (Qwen2.5-32B) | ~72 GB | ~24 GB | A100 / 双卡 4090 |
| **72B** (Qwen2.5-72B) | ~150 GB | ~48 GB | 多卡 A100 |

> 💡 **新手建议**：从 **7B + QLoRA** 开始，一张 RTX 4060（8GB）或 4090（24GB）就够了。验证流程跑通后再升级模型。

### 3.2 安装核心依赖：transformers + peft + bitsandbytes

```bash
# 创建虚拟环境（推荐）
conda create -n finetune python=3.11
conda activate finetune

# 安装 PyTorch（根据你的 CUDA 版本选择）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 核心依赖
pip install transformers>=4.45.0    # Hugging Face 模型库
pip install peft>=0.13.0            # LoRA / QLoRA 实现
pip install bitsandbytes>=0.44.0    # 4-bit 量化支持
pip install datasets>=3.0.0         # 数据集加载
pip install accelerate>=1.0.0       # 分布式训练
pip install trl>=0.12.0             # SFTTrainer（推荐的训练器）

# 可选但推荐
pip install wandb                   # 训练监控（可视化损失曲线）
pip install flash-attn              # FlashAttention 加速（需要 Ampere+ 显卡）
```

**验证安装：**

```python
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"显存: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB")

import transformers, peft, bitsandbytes
print(f"transformers: {transformers.__version__}")
print(f"peft: {peft.__version__}")
print(f"bitsandbytes: {bitsandbytes.__version__}")
```

### 3.3 Hugging Face 生态速览：模型、数据集、Trainer

Hugging Face 是微调的核心生态，你需要了解三个关键组件：

```
Hugging Face 核心三件套：

🤗 Model Hub (huggingface.co/models)
   → 下载预训练模型：Qwen2.5、Llama3、Mistral...
   → AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

📦 Datasets (huggingface.co/datasets)
   → 下载训练数据集，或上传你自己的
   → datasets.load_dataset("tatsu-lab/alpaca")

🏋️ Trainer / SFTTrainer
   → 封装好的训练循环：自动处理梯度、日志、保存checkpoint
   → 你只需要配置参数，不需要手写训练循环
```

### 3.4 云端 GPU 方案：Colab / AutoDL / 各大云平台

如果没有本地 GPU，可以用云端方案：

| 平台 | 免费额度 | 推荐显卡 | 适合 |
|:---|:---|:---|:---|
| **Google Colab** | 免费 T4 (15GB) | T4 / A100 | 学习、小规模实验 |
| **AutoDL** | 无免费 | RTX 4090, A100 | 国内首选，按小时计费 |
| **Lambda Cloud** | 无免费 | A100, H100 | 海外，性价比高 |
| **阿里云 PAI** | 有试用 | V100, A100 | 企业用户 |

```bash
# AutoDL 使用流程（国内推荐）：
# 1. 注册 autodl.com
# 2. 选择 RTX 4090 实例（~¥2/小时）
# 3. 选择 PyTorch 2.x + CUDA 12.x 镜像
# 4. SSH 连接后直接开始训练
```

> 💡 **省钱技巧**：先在 Colab 免费 T4 上用小数据集（100条）跑通流程，确认没有 bug 后再在云端 GPU 上跑完整训练。

---

## 4. 数据准备：决定微调成败的关键

微调界有句名言：**"数据质量决定上限，模型架构决定逼近速度"**。再好的模型，喂了垃圾数据也白搭。

### 4.1 微调数据的三种格式：指令、对话、续写

```python
# ── 格式 1：指令格式（Instruction） ──
# 适用：单轮问答、任务执行
{
    "instruction": "将以下英文翻译成中文",
    "input": "Machine learning is a subset of artificial intelligence.",
    "output": "机器学习是人工智能的一个子集。"
}

# ── 格式 2：对话格式（Conversation） ──
# 适用：多轮对话、客服机器人
{
    "conversations": [
        {"role": "system", "content": "你是一个专业的技术客服"},
        {"role": "user", "content": "我的订单怎么还没发货？"},
        {"role": "assistant", "content": "让我帮您查一下...订单 #1234 已于今天下午发出"},
        {"role": "user", "content": "大概几天能到？"},
        {"role": "assistant", "content": "预计 3-5 个工作日送达"}
    ]
}

# ── 格式 3：续写格式（Completion） ──
# 适用：文本生成、代码补全
{
    "text": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
}
```

### 4.2 数据质量 > 数据数量：高质量数据的标准

```
高质量微调数据的 5 个标准：

✅ 准确性：答案必须事实正确
✅ 一致性：相似问题的回答风格一致
✅ 完整性：回答覆盖问题的所有方面
✅ 格式规范：输出格式统一（JSON/Markdown/纯文本）
✅ 多样性：覆盖目标领域的各种场景
```

| 数据量 | 效果 | 适用场景 |
|:---|:---|:---|
| 50~200 条 | 基本的风格和格式学习 | 输出格式统一、简单风格迁移 |
| 500~1000 条 | 不错的领域适应 | 客服对话、特定任务 |
| 1000~5000 条 | 良好的领域专精 | 专业问答、复杂指令遵循 |
| 5000+ 条 | 深度领域知识 | 医疗/法律等专业场景 |

> 💡 **500 条高质量数据 > 5000 条低质量数据**。与其花时间收集大量数据，不如精心打磨少量高质量样本。

### 4.3 构造训练数据的实用方法

```python
# ── 方法 1：用 GPT-4 / Claude 生成种子数据 ──
prompt = """你是一个数据标注专家。请为"中文客服助手"生成 10 条高质量训练数据。

要求：
- 格式为 JSON，包含 user 和 assistant 字段
- 涵盖：退货、物流查询、产品咨询、投诉处理
- assistant 的回答要专业、友好、简洁

请直接输出 JSON 数组。"""

# 从大模型获取种子数据 → 人工审核修正 → 作为训练集

# ── 方法 2：从真实业务日志提取 ──
# 客服系统的聊天记录 → 脱敏 → 筛选优质对话 → 格式化

# ── 方法 3：Self-Instruct（自我指令生成） ──
# 用少量种子数据 → 让模型自动生成更多类似数据 → 人工过滤
```

### 4.4 对话模板（Chat Template）详解

每个模型都有自己的对话格式模板。**微调时必须使用与模型匹配的模板**，否则效果会大打折扣：

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

messages = [
    {"role": "system", "content": "你是一个有帮助的助手。"},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮你的？"},
]

# apply_chat_template 会自动按模型格式编排
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
print(text)

# Qwen2.5 的格式类似：
# <|im_start|>system
# 你是一个有帮助的助手。<|im_end|>
# <|im_start|>user
# 你好<|im_end|>
# <|im_start|>assistant
# 你好！有什么可以帮你的？<|im_end|>
```

> 💡 **关键原则**：永远用 `tokenizer.apply_chat_template()` 来格式化数据，不要手动拼字符串。不同模型的特殊 token 不同（`<|im_start|>` vs `[INST]` vs `<|begin_of_text|>`），用错了训练效果会很差。

### 4.5 实操：构建一个中文客服微调数据集

```python
import json

# ── 准备训练数据 ──
training_data = [
    {
        "conversations": [
            {"role": "system", "content": "你是智能客服小助手，回答要简洁专业、语气友好。"},
            {"role": "user", "content": "我想退货，怎么操作？"},
            {"role": "assistant", "content": "好的，退货流程如下：\n1. 进入"我的订单"页面\n2. 找到要退货的商品，点击"申请退货"\n3. 选择退货原因并提交\n\n审核通过后会发送退货地址，7个工作日内退款到账。还有其他问题吗？"},
        ]
    },
    {
        "conversations": [
            {"role": "system", "content": "你是智能客服小助手，回答要简洁专业、语气友好。"},
            {"role": "user", "content": "我的快递显示已签收但我没收到"},
            {"role": "assistant", "content": "很抱歉给您带来不便。这种情况可能是：\n1. 快递被放在了驿站或快递柜\n2. 被家人/邻居代收\n\n建议您先确认一下以上情况。如果确实没有收到，我帮您联系快递公司核实，请提供一下您的订单号。"},
        ]
    },
    # ... 更多数据（建议 500+ 条）
]

# ── 保存为 JSONL 格式 ──
with open("customer_service.jsonl", "w", encoding="utf-8") as f:
    for item in training_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

# ── 或者用 Hugging Face Datasets 加载 ──
from datasets import load_dataset
dataset = load_dataset("json", data_files="customer_service.jsonl")
print(dataset)
# DatasetDict({
#     train: Dataset({features: ['conversations'], num_rows: 500})
# })
```

---

## 5. 实战：用 LoRA 微调 Qwen2.5

终于到了写代码的时刻！这一章给你**完整的、可直接运行的 LoRA 微调代码**。

### 5.1 加载预训练模型与 Tokenizer

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "Qwen/Qwen2.5-7B-Instruct"

# ── 加载 Tokenizer ──
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token  # 设置 pad token

# ── 加载模型（FP16）──
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,    # 半精度加载
    device_map="auto",            # 自动分配到 GPU
    trust_remote_code=True,
)

print(f"模型参数量: {model.num_parameters() / 1e9:.1f}B")
print(f"显存占用: {torch.cuda.memory_allocated() / 1024**3:.1f} GB")
```

### 5.2 配置 LoRA 参数

```python
from peft import LoraConfig, get_peft_model, TaskType

lora_config = LoraConfig(
    r=16,                          # rank = 16，平衡效果和效率
    lora_alpha=32,                 # alpha = 2 * r
    target_modules=[               # 应用 LoRA 的层
        "q_proj", "k_proj", "v_proj", "o_proj",  # 注意力层
        "gate_proj", "up_proj", "down_proj",      # FFN 层
    ],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

# 应用 LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# trainable params: 13,631,488 || all params: 7,628,556,288 || trainable%: 0.1787%
# → 只训练 0.18% 的参数！
```

### 5.3 数据预处理与 DataCollator

```python
from datasets import load_dataset

# 加载数据集
dataset = load_dataset("json", data_files="customer_service.jsonl", split="train")

# ── 数据预处理函数 ──
def preprocess(example):
    """将对话格式转换为模型输入"""
    messages = example["conversations"]
    
    # 用 tokenizer 的 chat template 格式化
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )
    
    # Tokenize
    encodings = tokenizer(
        text,
        truncation=True,
        max_length=2048,
        padding=False,
    )
    
    # labels = input_ids（因为是自回归训练）
    encodings["labels"] = encodings["input_ids"].copy()
    return encodings

# 批量预处理
tokenized_dataset = dataset.map(preprocess, remove_columns=dataset.column_names)
print(f"训练样本数: {len(tokenized_dataset)}")
print(f"第一条样本 token 数: {len(tokenized_dataset[0]['input_ids'])}")
```

### 5.4 配置 TrainingArguments

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./qwen2.5-7b-lora",      # 输出目录
    
    # ── 训练参数 ──
    num_train_epochs=3,                    # 训练 3 个 epoch
    per_device_train_batch_size=4,         # 每 GPU batch size
    gradient_accumulation_steps=4,         # 梯度累积（等效 batch=16）
    
    # ── 优化器 ──
    learning_rate=2e-4,                    # LoRA 推荐学习率
    lr_scheduler_type="cosine",            # 余弦退火
    warmup_ratio=0.1,                      # 10% warmup
    weight_decay=0.01,
    
    # ── 精度与速度 ──
    fp16=True,                             # 半精度训练
    # bf16=True,                           # 如果显卡支持 BF16，用这个更好
    gradient_checkpointing=True,           # 用时间换显存
    
    # ── 日志与保存 ──
    logging_steps=10,                      # 每 10 步打印日志
    save_strategy="epoch",                 # 每个 epoch 保存
    save_total_limit=2,                    # 最多保留 2 个 checkpoint
    
    # ── Wandb 监控（可选） ──
    # report_to="wandb",
    # run_name="qwen2.5-7b-customer-service",
)
```

**关键参数解读：**

| 参数 | 推荐值 | 为什么 |
|:---|:---|:---|
| `learning_rate` | 1e-4 ~ 5e-4 | LoRA 的学习率比全量微调高一个数量级 |
| `num_train_epochs` | 2~5 | 太少学不会，太多过拟合 |
| `gradient_checkpointing` | True | 显存不够就开，速度慢 ~20% 但省 ~40% 显存 |
| `warmup_ratio` | 0.05~0.1 | 避免训练开始时 loss 暴涨 |

### 5.5 开始训练 + 监控损失曲线

```python
from transformers import Trainer, DataCollatorForLanguageModeling

# 数据整理器（自动处理 padding）
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)

# 🚀 开始训练！
trainer.train()

# 保存 LoRA 适配器（只有几十 MB）
trainer.save_model("./qwen2.5-7b-lora/final")
tokenizer.save_pretrained("./qwen2.5-7b-lora/final")
```

**健康的训练过程应该是这样的：**

```
Step 10:  loss=2.41  lr=5e-5
Step 20:  loss=1.83  lr=1e-4   ← loss 在下降 ✅
Step 50:  loss=1.12  lr=2e-4
Step 100: loss=0.78  lr=2e-4   ← 持续下降 ✅
Step 200: loss=0.45  lr=1.5e-4
Step 300: loss=0.31  lr=5e-5   ← 趋于平稳 ✅

⚠️ 异常信号：
- loss 不下降 → 学习率可能太小，或数据有问题
- loss 突然飙到 NaN → 学习率太大，或精度问题
- loss 降到 0.01 以下 → 严重过拟合！
```

### 5.6 常见报错与解决方案

| 报错 | 原因 | 解决 |
|:---|:---|:---|
| `CUDA out of memory` | 显存不够 | 减小 batch_size，开 gradient_checkpointing，用 QLoRA |
| `RuntimeError: expected scalar type Half` | 混合精度冲突 | 确保 fp16=True 且模型用 torch.float16 加载 |
| `ValueError: Tokenizer pad_token is not set` | 缺少 pad token | `tokenizer.pad_token = tokenizer.eos_token` |
| `loss=NaN` | 学习率太大或数据异常 | 降低 lr 到 1e-4，检查数据中是否有空样本 |
| `AssertionError: flash_attn` | Flash Attention 版本不对 | `pip install flash-attn --no-build-isolation` 或禁用 |

> 💡 **调试技巧**：先用 10 条数据、1 个 epoch 快速跑通全流程，确认没有报错后再用完整数据训练。

---

## 6. 实战：用 QLoRA 在消费级显卡上微调

如果你的显卡只有 8~12 GB 显存（RTX 4060/3060），QLoRA 是你的最佳选择。

### 6.1 4-bit 量化加载模型（bitsandbytes）

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

model_name = "Qwen/Qwen2.5-7B-Instruct"

# ── QLoRA 的关键：4-bit 量化配置 ──
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,                      # 4-bit 量化加载
    bnb_4bit_quant_type="nf4",              # NF4 量化格式（推荐）
    bnb_4bit_compute_dtype=torch.float16,   # 计算时用 FP16
    bnb_4bit_use_double_quant=True,         # 双重量化，进一步省内存
)

# 加载量化后的模型
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

print(f"显存占用: {torch.cuda.memory_allocated() / 1024**3:.1f} GB")
# → 约 4-5 GB（vs FP16 的 14 GB）
```

### 6.2 QLoRA 配置与训练

QLoRA 的训练代码和 LoRA 几乎一样，只是模型加载方式不同：

```python
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# ── 关键步骤：为量化模型准备训练 ──
model = prepare_model_for_kbit_training(model)

# LoRA 配置（和之前一样）
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ── 训练（和 LoRA 完全一样） ──
from transformers import TrainingArguments, Trainer, DataCollatorForLanguageModeling

training_args = TrainingArguments(
    output_dir="./qwen2.5-7b-qlora",
    num_train_epochs=3,
    per_device_train_batch_size=2,     # QLoRA 显存少，batch 可能要更小
    gradient_accumulation_steps=8,     # 累积来补偿
    learning_rate=2e-4,
    fp16=True,
    gradient_checkpointing=True,
    logging_steps=10,
    save_strategy="epoch",
    save_total_limit=2,
)

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)

trainer.train()
trainer.save_model("./qwen2.5-7b-qlora/final")
```

> 💡 **QLoRA 和 LoRA 的代码差异只有两处**：①模型加载时加 `BitsAndBytesConfig`，②训练前调用 `prepare_model_for_kbit_training()`。其他完全一样。

### 6.3 LoRA vs QLoRA：效果与速度对比

| 指标 | LoRA (FP16) | QLoRA (4-bit) |
|:---|:---|:---|
| 模型加载显存 | ~14 GB | ~4.5 GB |
| 训练峰值显存 | ~18 GB | ~8 GB |
| 训练速度 | ⭐⭐⭐⭐⭐ 快 | ⭐⭐⭐ 较慢（量化/反量化开销） |
| 微调效果 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ （略低，但差距很小） |
| 最低显卡 | RTX 4090 (24GB) | RTX 4060 (8GB) |

### 6.4 实测：RTX 4090 / 3090 / 4060 能跑多大的模型？

```
实测数据（Qwen2.5 系列，QLoRA，batch_size=1，max_length=2048）：

RTX 4060 8GB：
  ✅ 1.5B — 显存 ~4 GB，训练流畅
  ✅ 7B   — 显存 ~7.5 GB，刚好能跑
  ❌ 14B  — OOM

RTX 3090 / 4090 24GB：
  ✅ 7B   — 显存 ~8 GB，batch_size 可开到 4
  ✅ 14B  — 显存 ~12 GB，batch_size=2
  ✅ 32B  — 显存 ~22 GB，batch_size=1，刚好能跑
  ❌ 72B  — OOM

A100 80GB：
  ✅ 72B  — 显存 ~45 GB，batch_size=1
```

> 💡 **实用建议**：如果你只有 8GB 显卡，微调 7B 模型已经能获得很好的效果。不要盲目追求大模型——7B 微调后的效果往往比 72B 通用模型在特定任务上更好。

---

## 7. 模型评估与合并导出

训练完了，怎么知道微调效果好不好？怎么把 LoRA 适配器变成一个可以直接部署的模型？

### 7.1 训练损失 ≠ 模型好坏：如何正确评估

```
常见误区：

❌ "loss 降到 0.1 了，效果一定很好！"
   → loss 低可能是过拟合（在训练数据上背答案）

❌ "loss 还有 0.8，效果一定不好！"
   → loss 的绝对值取决于任务和数据，不能跨实验比较

✅ 正确的评估方式：
   1. 留出 10~20% 的数据作为验证集
   2. 用验证集 loss 判断是否过拟合
   3. 用人工测试判断真实效果
```

```python
# ── 加载微调后的模型进行测试 ──
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct", torch_dtype=torch.float16, device_map="auto"
)
model = PeftModel.from_pretrained(base_model, "./qwen2.5-7b-lora/final")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

# ── 测试 ──
test_questions = [
    "我想退货，怎么操作？",
    "快递多久能到？",
    "可以换货吗？",
    "你们有优惠活动吗？",  # ← 如果训练数据里没有，看模型是否能泛化
]

for q in test_questions:
    messages = [
        {"role": "system", "content": "你是智能客服小助手，回答要简洁专业、语气友好。"},
        {"role": "user", "content": q},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    
    outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.7)
    response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    
    print(f"问：{q}")
    print(f"答：{response}\n")
```

### 7.2 自动评测：perplexity、BLEU、人工打分

| 评测方式 | 衡量什么 | 适用场景 |
|:---|:---|:---|
| **Perplexity** | 模型对文本的"困惑度"，越低越好 | 通用语言能力 |
| **BLEU / ROUGE** | 生成文本与参考答案的相似度 | 翻译、摘要 |
| **人工评测** | 真实使用场景下的满意度 | 所有场景（最可靠） |
| **LLM-as-Judge** | 用 GPT-4 给模型打分 | 快速批量评估 |

```python
# ── 用 GPT-4 做自动评分（LLM-as-Judge） ──
judge_prompt = """请对以下客服回复打分（1-5分）：

用户问题：{question}
客服回复：{answer}

评分标准：
5分 = 完美回答，专业、友好、完整
4分 = 不错，有小瑕疵
3分 = 基本可用，但不够好
2分 = 有明显问题
1分 = 完全不合格

请直接给出分数和简短理由。"""
```

> 💡 **实际项目推荐**：自动评测做初筛（过滤明显差的），人工评测做最终判断。

### 7.3 合并 LoRA 适配器到基础模型

训练完的 LoRA 适配器只有几十 MB。你可以选择**保持分离**（灵活切换）或**合并到基础模型**（部署简单）：

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# ── 加载基础模型 + LoRA 适配器 ──
base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    torch_dtype=torch.float16,
    device_map="cpu",  # 合并时在 CPU 上操作，避免显存不够
)
model = PeftModel.from_pretrained(base_model, "./qwen2.5-7b-lora/final")

# ── 合并！ ──
merged_model = model.merge_and_unload()
# merge_and_unload() 做的事：W_new = W + A × B，然后删除 LoRA 模块

# ── 保存合并后的完整模型 ──
merged_model.save_pretrained("./qwen2.5-7b-merged")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
tokenizer.save_pretrained("./qwen2.5-7b-merged")

print("✅ 模型已合并保存，可以像普通模型一样使用了")
```

### 7.4 多种推理方式：transformers / vLLM / Ollama

合并后的模型可以用多种方式部署：

```bash
# ── 方式 1：transformers（开发测试） ──
# 就是上面的代码，直接加载推理

# ── 方式 2：vLLM（高性能推理服务） ──
pip install vllm
python -m vllm.entrypoints.openai.api_server \
    --model ./qwen2.5-7b-merged \
    --port 8000
# 自动提供 OpenAI 兼容的 API 接口

# ── 方式 3：Ollama（本地一键部署） ──
# 先转成 GGUF 格式
pip install llama-cpp-python
python convert_hf_to_gguf.py ./qwen2.5-7b-merged --outfile model.gguf

# 创建 Modelfile
echo 'FROM ./model.gguf
SYSTEM "你是智能客服小助手"' > Modelfile

ollama create my-customer-service -f Modelfile
ollama run my-customer-service
```

| 方式 | 适用场景 | 速度 |
|:---|:---|:---|
| **transformers** | 开发调试、小规模 | ⭐⭐ |
| **vLLM** | 生产 API 服务、高并发 | ⭐⭐⭐⭐⭐ |
| **Ollama** | 本地个人使用、演示 | ⭐⭐⭐ |

---

## 8. 进阶话题与最佳实践

最后一章汇总进阶技巧和避坑指南，帮你在实际项目中少走弯路。

### 8.1 超参数调优指南：rank、learning_rate、epochs

```
超参数调优优先级（从最重要到最不重要）：

1️⃣ 数据质量     → 垃圾数据再怎么调参也没用
2️⃣ learning_rate → 最敏感的参数，建议 1e-4 ~ 5e-4
3️⃣ epochs        → 2~5 之间，小数据集多几轮，大数据集少几轮
4️⃣ rank          → 默认 16 够用，复杂任务试 32~64
5️⃣ batch_size    → 越大训练越稳定，但受显存限制
```

**快速调优策略：**

| 阶段 | 数据量 | 目的 |
|:---|:---|:---|
| 🧪 探索 | 100 条 | 跑通流程，排除 bug |
| 📊 调参 | 500 条 | 尝试 3~5 组超参，选最优 |
| 🚀 正式训练 | 全量数据 | 用最佳超参跑完整训练 |

```python
# 推荐的超参搜索空间
experiments = [
    {"lr": 1e-4, "r": 8,  "epochs": 3},
    {"lr": 2e-4, "r": 16, "epochs": 3},  # 默认推荐
    {"lr": 5e-4, "r": 16, "epochs": 2},
    {"lr": 2e-4, "r": 32, "epochs": 3},
    {"lr": 2e-4, "r": 16, "epochs": 5},
]
# 用验证集 loss 和人工评测选出最佳组合
```

### 8.2 防止灾难性遗忘：微调不要"忘了老本"

微调最大的风险：**模型学会了新任务，但忘了原来会的东西**。

```
灾难性遗忘的表现：

微调前：能流畅地回答各种通用问题
微调后：客服问题答得很好，但问"1+1=?" 它都回答不了了 💀
```

**防止遗忘的策略：**

```python
# ── 策略 1：控制学习率（最重要！）──
# 学习率太大 → 原始权重被覆盖太多 → 遗忘
# 建议 LoRA lr: 1e-4 ~ 3e-4（比全量微调的 2e-5 高，但不要太高）

# ── 策略 2：减少 epoch 数 ──
# 训练轮数太多 → 过拟合到微调数据 → 丧失通用能力
# 建议：2~3 个 epoch，通过验证集 loss 确认

# ── 策略 3：混入通用数据 ──
# 在微调数据集中混入 10~20% 的通用对话数据
# 让模型在学习新任务的同时"复习旧知识"

# ── 策略 4：LoRA 本身就是防遗忘的 ──
# LoRA 冻结了原始权重，只训练适配器
# 这比全量微调天然不容易遗忘
# 如果适配器效果不好，随时移除，恢复原始模型
```

### 8.3 DPO / RLHF 简介：从 SFT 到对齐

本教程讲的都是 **SFT（Supervised Fine-Tuning）**——用标注好的问答对训练模型。但 ChatGPT 之所以好用，还有一步关键操作：**对齐（Alignment）**。

```
LLM 训练的三个阶段：

1. 预训练（Pre-training）
   → 用海量文本学"语言能力"
   → 产出：Base 模型（会说话，但没有"价值观"）

2. SFT（有监督微调）← 本教程
   → 用问答对学"怎么按指令做事"
   → 产出：Instruct 模型（能按指令回答，但可能不够安全/有偏见）

3. 对齐（RLHF / DPO）
   → 学"什么回答更好"
   → 产出：对齐后的模型（安全、有用、无害）
```

| 方法 | 原理 | 数据要求 | 难度 |
|:---|:---|:---|:---|
| **RLHF** | 训练奖励模型 + PPO 强化学习 | 人工偏好排序 | ⭐⭐⭐⭐⭐ 很难 |
| **DPO** | 直接从偏好数据优化，不需要奖励模型 | 人工偏好排序 | ⭐⭐⭐ 较简单 |

```python
# DPO 的数据格式（每条数据包含"好回答"和"差回答"）
{
    "prompt": "如何学习编程？",
    "chosen": "建议从 Python 开始...",     # 好回答 ✅
    "rejected": "编程很难，你可能学不会。"   # 差回答 ❌
}

# trl 库已内置 DPO 训练器
from trl import DPOTrainer
# 使用方式和 SFTTrainer 类似，只是数据格式不同
```

> 💡 **建议**：先用 SFT 把任务效果做好，如果还需要更精细的控制（安全性、回答偏好），再加 DPO。

### 8.4 微调 Checklist：上线前的检查清单

```
✅ 训练前
  □ 数据质量已人工审核（随机抽查 50 条）
  □ 数据格式与 chat_template 匹配
  □ 用 10 条数据跑通了完整流程
  □ 确认显存够用（留 10% 余量）

✅ 训练中
  □ loss 在持续下降（没有 NaN 或不下降）
  □ 验证集 loss 没有显著上升（没过拟合）
  □ 训练时长在预期范围内

✅ 训练后
  □ 人工测试通过 → 20+ 个覆盖各场景的测试问题
  □ 泛化测试通过 → 问训练集之外的问题看效果
  □ 通用能力未退化 → 基础问答仍然正常
  □ LoRA 适配器成功保存（检查文件大小）

✅ 部署前
  □ 确认合并/加载方式（分离部署 or 合并后部署）
  □ 推理速度满足要求（QPS 测试）
  □ 异常输入处理（空输入、超长输入、注入攻击）
  □ 上线监控（记录每次请求的输入输出，方便排查问题）
```

> 💡 **最后的建议**：微调不是一锤子买卖——它是一个**迭代过程**。第一版效果不好很正常，关键是建立"数据 → 训练 → 评估 → 改进数据"的闭环。数据质量每提升一个台阶，模型效果就会上一个台阶。
