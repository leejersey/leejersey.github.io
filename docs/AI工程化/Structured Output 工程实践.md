# Structured Output 工程实践

> LLM 输出是字符串，但你的代码需要 JSON。本教程解决 AI 应用中最常见的工程问题——如何让大模型稳定、可靠地输出结构化数据，从 JSON Mode 到 Pydantic 类型安全管线，再到 Instructor 库的生产级实践。

---

## 1. 为什么 Structured Output 是 AI 工程的刚需

LLM 输出的是字符串，但你的代码需要 `dict`、`list`、Pydantic 对象。这个"字符串→结构化数据"的转换，是 AI 应用中**最常见的故障来源**。

### 1.1 自由文本的困境：LLM 输出 ≠ 可用数据

```python
# 你想要的
{"name": "张三", "age": 28, "skills": ["Python", "SQL"]}

# LLM 实际给你的（五花八门）
"根据分析，该候选人姓名为张三，年龄28岁，技能包括Python和SQL。"
"```json\n{\"name\": \"张三\", \"age\": \"28\"}\n```"  # age 是字符串！
"{'name': '张三', 'age': 28}"  # 单引号，json.loads 会报错
"{name: 张三, age: 28}"  # 不是合法 JSON
```

### 1.2 解析失败的代价：生产环境的头号故障

```
真实生产事故案例：

  Agent 工具调用 → LLM 输出参数格式错误 → 工具执行失败 → 用户看到报错
  RAG 管线 → LLM 没按格式返回引用来源 → 前端渲染崩溃
  数据提取 → LLM 少了一个必填字段 → 写入数据库失败 → 整批任务回滚

  不可靠的结构化输出 = 不可靠的 AI 应用
```

### 1.3 结构化输出的四个层次

```
从弱到强的四个层次：

  Level 1: Prompt 工程 + json.loads()
  ├── "请以 JSON 格式输出"
  ├── 成功率 ~80%（经常多余文本、格式错误）
  └── ❌ 不可靠

  Level 2: JSON Mode
  ├── response_format={"type": "json_object"}
  ├── 保证输出是合法 JSON，但不保证字段正确
  └── ⚠️ 半可靠

  Level 3: Structured Outputs / Schema 约束
  ├── response_format=json_schema + 完整 Schema
  ├── 模型保证输出严格符合 Schema
  └── ✅ 可靠

  Level 4: Pydantic + Instructor + 重试
  ├── 类型安全 + 业务验证 + 自动重试 + 降级
  └── ✅✅ 生产级可靠
```

> 💡 **目标**：从 Level 1 升级到 Level 4——让结构化输出的成功率从 80% 提升到 99.9%。

---

## 2. 基础方法：Prompt 工程 + 后处理

最原始的方式——在 Prompt 里说"返回 JSON"，然后自己解析。有效，但脆弱。

### 2.1 Prompt 中要求 JSON 输出

```python
import json
from openai import OpenAI

client = OpenAI()

prompt = """从以下文本中提取人物信息，以 JSON 格式返回：
{"name": "姓名", "age": 年龄, "company": "公司"}

文本：张三今年28岁，在阿里巴巴工作。

只返回 JSON，不要其他文字。"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
)

# 祈祷它返回的是合法 JSON...
try:
    data = json.loads(response.choices[0].message.content)
except json.JSONDecodeError:
    print("解析失败！")  # 这种情况比你想的多得多
```

### 2.2 后处理：清洗、修复、重试

```python
import re

def extract_json(text: str) -> dict | None:
    """从 LLM 输出中提取 JSON（处理各种脏格式）"""
    # 1. 去掉 markdown 代码块
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    
    # 2. 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 3. 尝试提取 JSON 片段
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    # 4. 放弃
    return None
```

### 2.3 为什么 Prompt 工程不够用

```
Prompt 工程的失败模式（真实案例）：

  ❌ 多余解释："以下是提取的 JSON：{...}"
  ❌ 字段名不一致：要求 "name"，返回 "姓名"
  ❌ 类型错误：要求 int，返回 "28" (string)
  ❌ 缺少必填字段：小模型经常忘记某个字段
  ❌ 额外字段：返回了你没要求的字段
  ❌ 嵌套错误：数组变成了字符串

  根本原因：Prompt 是"建议"，不是"约束"
  模型可以选择不遵守
```

> 💡 **Prompt 工程是起点，不是终点**。它适合原型验证，但生产环境需要更强的保证。

---

## 3. JSON Mode：模型原生支持

JSON Mode 是第一个"模型级保证"——模型承诺输出合法 JSON。

### 3.1 OpenAI JSON Mode 详解

```python
from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "提取人物信息，返回 JSON"},
        {"role": "user", "content": "张三今年28岁，在阿里巴巴工作"},
    ],
    response_format={"type": "json_object"},  # ← 关键参数
)

# ✅ 保证是合法 JSON（不会有多余文本）
data = json.loads(response.choices[0].message.content)
# 但字段名和类型不保证！可能返回 {"姓名": "张三"} 而不是 {"name": "张三"}
```

### 3.2 各模型 JSON Mode 对比

| 模型 | JSON Mode | Structured Outputs | 可靠度 |
|:---|:---|:---|:---|
| **GPT-4o / 4o-mini** | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **Claude 3.5** | ✅（Prompt 指示） | ❌ | ⭐⭐⭐⭐ |
| **Gemini 2.0** | ✅ | ✅ | ⭐⭐⭐⭐ |
| **Qwen 2.5** | ✅（via Ollama） | ❌ | ⭐⭐⭐ |
| **Llama 3.3** | ✅（via vLLM） | ❌ | ⭐⭐⭐ |

### 3.3 JSON Mode 的局限：语法正确 ≠ 语义正确

```python
# JSON Mode 保证的：
{"name": "张三", "age": 28}           # ✅ 合法 JSON

# JSON Mode 不保证的：
{"name": "张三", "age": "二十八"}      # 语法合法，但 age 应该是 int
{"person_name": "张三"}               # 语法合法，但字段名不对
{"name": "张三"}                      # 语法合法，但缺少 age 字段
{"name": "张三", "age": 28, "hobby": "编程"}  # 多了个你没要求的字段
```

> 💡 **JSON Mode 只解决了一半问题**——保证"是 JSON"，但不保证"是你要的 JSON"。要解决另一半，需要 Structured Outputs。

---

## 4. Structured Outputs：Schema 级别的类型安全

OpenAI 的 Structured Outputs 是游戏规则改变者——模型**100% 保证**输出符合你定义的 JSON Schema。

### 4.1 OpenAI Structured Outputs 实战

```python
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class Person(BaseModel):
    name: str
    age: int
    company: str
    skills: list[str]

response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "张三今年28岁，在阿里巴巴工作，擅长 Python 和 SQL"},
    ],
    response_format=Person,  # ← 直接传 Pydantic 模型！
)

person = response.choices[0].message.parsed
print(person.name)    # "张三" (str)
print(person.age)     # 28 (int，不是 "28")
print(person.skills)  # ["Python", "SQL"] (list[str])
```

### 4.2 JSON Schema 定义最佳实践

```python
from pydantic import BaseModel, Field
from enum import Enum

class Sentiment(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"

class ReviewAnalysis(BaseModel):
    """商品评价分析结果"""
    sentiment: Sentiment = Field(description="情感倾向")
    score: float = Field(ge=0, le=1, description="情感分数 0-1")
    keywords: list[str] = Field(max_length=5, description="关键词，最多5个")
    summary: str = Field(max_length=200, description="一句话摘要")
    has_complaint: bool = Field(description="是否包含投诉")
```

### 4.3 约束解码原理：为什么能 100% 保证格式

```
约束解码（Constrained Decoding）原理：

  普通解码：模型从所有 Token 中选择下一个
  约束解码：根据当前 JSON 解析状态，屏蔽不合法的 Token

  示例（输出 {"name": "张三", "age": 28}）：
    已输出: {"name": "
    合法下一个 Token: 任意字符串字符
    不合法: 数字、}、] 等（因为还在字符串内部）

    已输出: {"name": "张三", "age":
    合法下一个 Token: 数字（因为 Schema 定义 age 为 int）
    不合法: "、字母等（不是合法整数开头）

  → 模型在生成每个 Token 时都受 Schema 约束
  → 所以 100% 保证格式正确
```

### 4.4 其他模型的 Schema 支持现状

| 模型 | Schema 约束 | 实现方式 |
|:---|:---|:---|
| **GPT-4o** | ✅ 原生 | response_format=json_schema |
| **Gemini 2.0** | ✅ 原生 | response_schema 参数 |
| **Claude** | ❌ 无原生 | 需要 Instructor 辅助 |
| **开源模型** | ⚠️ 框架层 | Outlines / llama.cpp grammar |

> 💡 **Structured Outputs 是目前最可靠的方案**——但它只在 OpenAI 和 Gemini 上原生支持。其他模型需要 Instructor 库来补齐。

---

## 5. Pydantic + LLM：Python 类型安全管线

Pydantic 是 Python 生态的类型验证之王——把它和 LLM 结合，就得到了类型安全的 AI 输出管线。

### 5.1 Pydantic 基础：从 BaseModel 开始

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class Invoice(BaseModel):
    invoice_number: str = Field(description="发票号码")
    amount: float = Field(gt=0, description="金额（正数）")
    currency: str = Field(default="CNY", description="币种")
    vendor: str = Field(description="供应商名称")
    date: str = Field(description="日期 YYYY-MM-DD")
    items: list[str] = Field(description="商品列表")
    tax: Optional[float] = Field(default=None, description="税额")
    
    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        from datetime import datetime
        datetime.strptime(v, "%Y-%m-%d")  # 验证日期格式
        return v
```

### 5.2 OpenAI + Pydantic：client.beta.chat.completions.parse()

```python
response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "发票内容：..."}],
    response_format=Invoice,
)

invoice = response.choices[0].message.parsed  # 直接是 Invoice 对象！
print(type(invoice))       # <class 'Invoice'>
print(invoice.amount)      # 1500.0 (float, 保证 > 0)
print(invoice.items)       # ["办公用品", "打印纸"] (list[str])
```

### 5.3 嵌套模型与复杂 Schema

```python
class Address(BaseModel):
    city: str
    district: str
    street: str

class Employee(BaseModel):
    name: str
    age: int = Field(ge=18, le=65)
    department: str
    address: Address                    # 嵌套对象
    projects: list[str]                 # 数组
    manager: Optional["Employee"] = None  # 递归引用
```

### 5.4 自定义验证器：业务规则校验

```python
class OrderExtraction(BaseModel):
    product: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(gt=0)
    total: float
    
    @field_validator("total")
    @classmethod
    def validate_total(cls, v, info):
        expected = info.data.get("quantity", 0) * info.data.get("unit_price", 0)
        if abs(v - expected) > 0.01:
            raise ValueError(f"总价不正确：{v} ≠ {expected}")
        return v
```

> 💡 **Pydantic 的验证器是你的安全网**——即使模型输出了格式正确但语义错误的数据（比如总价计算错误），验证器也能拦住。

---

## 6. Instructor 库：生产级结构化输出

Instructor 是目前最佳实践——Pydantic + 自动重试 + 多模型支持，一个库搞定一切。

### 6.1 Instructor 核心概念与安装

```bash
pip install instructor
```

### 6.2 基础使用：一行代码获得类型安全

```python
import instructor
from openai import OpenAI
from pydantic import BaseModel

# 用 instructor.patch() 增强 OpenAI client
client = instructor.from_openai(OpenAI())

class UserInfo(BaseModel):
    name: str
    age: int
    email: str

# 直接返回 Pydantic 对象——就这么简单
user = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "张三，28岁，zhangsan@example.com"}],
    response_model=UserInfo,
)

print(user)  # UserInfo(name='张三', age=28, email='zhangsan@example.com')
```

### 6.3 自动重试与错误修复

```python
# Instructor 内置重试：验证失败 → 把错误信息反馈给模型 → 重新生成
user = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "..."}],
    response_model=UserInfo,
    max_retries=3,  # 最多重试 3 次
)

# 重试时，Instructor 会自动将 Pydantic 验证错误发送给模型：
# "Validation error: age must be >= 0, got -5. Please fix."
# 模型看到错误后会自动修正
```

### 6.4 多模型支持：OpenAI / Claude / Ollama

```python
# Anthropic Claude
import anthropic
client = instructor.from_anthropic(anthropic.Anthropic())

# Ollama（本地模型）
from openai import OpenAI
client = instructor.from_openai(
    OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"),
    mode=instructor.Mode.JSON,  # Ollama 用 JSON Mode
)

# LiteLLM（统一多模型）
import litellm
client = instructor.from_litellm(litellm.completion)
```

> 💡 **Instructor 是当前最佳实践**。它封装了所有复杂性——Schema 传递、解析、验证、重试——你只需要定义 Pydantic 模型。

---

## 7. Tool Use / Function Calling：另一种结构化

Function Calling 本质上也是 Structured Output——模型输出结构化的函数参数。

### 7.1 Function Calling 的本质：结构化输出的变体

```python
# Function Calling = 模型输出 {"name": "函数名", "arguments": {结构化参数}}
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "北京明天的天气"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "date": {"type": "string", "format": "date"}
                },
                "required": ["city", "date"]
            }
        }
    }]
)
# 输出：{"city": "北京", "date": "2026-05-04"}  ← 这就是结构化输出！
```

### 7.2 Tool Use vs Structured Outputs：如何选择

| 维度 | Structured Outputs | Function Calling |
|:---|:---|:---|
| **用途** | 提取/生成结构化数据 | 触发工具执行 |
| **输出** | 完整的数据对象 | 函数名 + 参数 |
| **Schema 保证** | ✅ 100% | ✅ 100% |
| **适合** | 数据提取、分类、分析 | Agent 工具调用 |

### 7.3 并行函数调用与强制调用

```python
# 强制调用特定函数
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...],
    tools=[...],
    tool_choice={"type": "function", "function": {"name": "get_weather"}},
)
```

### 7.4 Function Calling 的 Schema 设计

```
Schema 设计原则：

  ✅ description 写清楚（模型靠这个理解参数含义）
  ✅ 用 enum 限制取值范围
  ✅ required 明确必填字段
  ✅ 参数名用英文（模型处理更准确）
  ❌ 不要超过 10 个参数（模型准确率下降）
  ❌ 不要嵌套超过 3 层
```

---

## 8. 流式结构化输出

流式 + 结构化 = 双重挑战。JSON 还没生成完，怎么解析？

### 8.1 流式输出的挑战：不完整的 JSON

```python
# 流式输出中间状态：
# chunk 1: {"name": "张
# chunk 2: 三", "age":
# chunk 3: 28}
# 前两个 chunk 都不是合法 JSON → json.loads() 会报错
```

### 8.2 Partial Parsing：边生成边解析

```python
from instructor import Partial

class UserInfo(BaseModel):
    name: str
    age: int
    bio: str

# Instructor 的 Partial 模式：每个 chunk 返回已解析的部分
for partial_user in client.chat.completions.create_partial(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "..."}],
    response_model=UserInfo,
):
    print(partial_user)
    # UserInfo(name='张三', age=None, bio=None)  ← 第一个 chunk
    # UserInfo(name='张三', age=28, bio=None)    ← 第二个 chunk
    # UserInfo(name='张三', age=28, bio='...')    ← 完整结果
```

### 8.3 Instructor 流式模式实战

```python
# 流式提取 + 实时展示
for partial in client.chat.completions.create_partial(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": invoice_text}],
    response_model=Invoice,
):
    # 实时更新 UI
    if partial.invoice_number:
        update_ui("发票号", partial.invoice_number)
    if partial.amount:
        update_ui("金额", partial.amount)
```

### 8.4 逐字段渲染的前端集成

```
流式结构化的前端集成：

  后端（SSE）→ 每个 chunk 发送 partial JSON
  前端 → 逐字段渲染，已解析的字段先显示
  
  用户体验：
    [发票号] INV-2026-001  ✅（先出来）
    [金额]   ████████       （加载中）
    [供应商] ████████       （加载中）
       ↓
    [发票号] INV-2026-001  ✅
    [金额]   ¥1,500.00     ✅（中间出来）
    [供应商] ████████       （加载中）
```

---

## 9. 错误处理与可靠性工程

生产环境中，结构化输出的故障是一定会发生的。本章教你如何做到 99.9% 的成功率。

### 9.1 常见失败模式与对策

```
失败模式 Top 5：

  1️⃣ 幻觉字段
     要求提取 email，模型编造了一个不存在的 email
     → 对策：校验字段合理性（正则/枚举）

  2️⃣ 类型错误
     age 应该是 int，模型返回 "二十八"
     → 对策：Pydantic 严格类型 + 重试

  3️⃣ 枚举越界
     情感分析应为 positive/negative/neutral，模型返回 "somewhat positive"
     → 对策：用 Enum 严格限制

  4️⃣ 数组长度异常
     要求 Top 5 关键词，返回了 20 个
     → 对策：Field(max_length=5)

  5️⃣ 嵌套缺失
     嵌套对象的某个子字段缺失
     → 对策：所有字段都加 description
```

### 9.2 重试策略：指数退避 + Prompt 修复

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def extract_with_retry(text: str, model_class):
    try:
        return client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": text}],
            response_model=model_class,
            max_retries=2,
        )
    except Exception as e:
        print(f"重试中: {e}")
        raise
```

### 9.3 降级与 Fallback：多层防御

```python
async def extract_safe(text: str) -> dict:
    """多层降级的结构化输出"""
    # Layer 1: Structured Outputs（最可靠）
    try:
        return client.beta.chat.completions.parse(
            model="gpt-4o-mini", messages=[...], response_format=Schema
        ).choices[0].message.parsed.dict()
    except Exception:
        pass
    
    # Layer 2: JSON Mode + 手动解析
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini", messages=[...],
            response_format={"type": "json_object"}
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        pass
    
    # Layer 3: 纯文本 + 正则提取（兜底）
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=[...])
    return extract_json(resp.choices[0].message.content) or {"error": "提取失败"}
```

### 9.4 监控与告警：结构化输出成功率

```python
# 关键监控指标
metrics = {
    "structured_output_success_rate": 0.0,    # 目标 > 99%
    "validation_error_rate": 0.0,              # 目标 < 1%
    "retry_rate": 0.0,                         # 目标 < 5%
    "avg_retries_per_request": 0.0,            # 目标 < 0.1
    "fallback_rate": 0.0,                      # 目标 < 0.1%
}
```

---

## 10. 实战：构建类型安全的数据提取管线

把前 9 章串起来——用 Instructor + Pydantic 构建一个生产级的简历信息提取管线。

### 10.1 项目架构与技术选型

```
resume-extractor/
├── models/
│   └── schema.py         # Pydantic 数据模型
├── extractors/
│   └── resume.py         # 提取逻辑
├── pipeline.py           # 批量处理管线
├── evaluate.py           # 质量评估
└── requirements.txt
```

### 10.2 定义提取 Schema（Pydantic 模型）

```python
# models/schema.py
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class EducationLevel(str, Enum):
    bachelor = "bachelor"
    master = "master"
    phd = "phd"
    other = "other"

class Education(BaseModel):
    school: str = Field(description="学校名称")
    degree: EducationLevel
    major: str = Field(description="专业")
    year: Optional[int] = Field(default=None, description="毕业年份")

class WorkExperience(BaseModel):
    company: str = Field(description="公司名称")
    title: str = Field(description="职位")
    years: float = Field(ge=0, description="工作年限")
    highlights: list[str] = Field(description="工作亮点，最多3条", max_length=3)

class ResumeInfo(BaseModel):
    """简历结构化信息"""
    name: str = Field(description="姓名")
    email: Optional[str] = Field(default=None, description="邮箱")
    phone: Optional[str] = Field(default=None, description="电话")
    total_experience_years: float = Field(ge=0, description="总工作年限")
    skills: list[str] = Field(description="技能列表")
    education: list[Education]
    work_experience: list[WorkExperience]
    summary: str = Field(max_length=200, description="一句话总结")
```

### 10.3 实现提取管线：批量 + 并发

```python
# pipeline.py
import instructor
import asyncio
from openai import AsyncOpenAI

client = instructor.from_openai(AsyncOpenAI())

async def extract_resume(text: str) -> ResumeInfo:
    return await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是简历信息提取专家。从文本中提取结构化信息。"},
            {"role": "user", "content": text},
        ],
        response_model=ResumeInfo,
        max_retries=3,
    )

async def batch_extract(texts: list[str], concurrency: int = 5) -> list[ResumeInfo]:
    semaphore = asyncio.Semaphore(concurrency)
    
    async def limited_extract(text):
        async with semaphore:
            return await extract_resume(text)
    
    return await asyncio.gather(*[limited_extract(t) for t in texts])
```

### 10.4 质量评估与持续优化

```python
def evaluate_extraction(predicted: ResumeInfo, expected: dict) -> dict:
    """评估提取质量"""
    scores = {}
    scores["name_match"] = predicted.name == expected.get("name", "")
    scores["skills_recall"] = len(
        set(predicted.skills) & set(expected.get("skills", []))
    ) / max(len(expected.get("skills", [])), 1)
    scores["edu_count_match"] = len(predicted.education) == len(expected.get("education", []))
    return scores
```

### 10.5 完整代码与部署

```
技术选型总结：

  方案选择决策树：
  │
  ├── 用 OpenAI？
  │     └── ✅ Structured Outputs（response_format=Pydantic）
  │
  ├── 用多个模型？
  │     └── ✅ Instructor（统一接口 + 自动重试）
  │
  ├── 用本地模型？
  │     └── ✅ Instructor + JSON Mode
  │
  └── 需要流式？
        └── ✅ Instructor Partial Mode
```

> 💡 **最后一句话**：Structured Output 不是可选的——它是 AI 应用工程化的**基础设施**。没有可靠的结构化输出，Agent 不能可靠地调用工具，RAG 不能可靠地返回引用，数据提取不能可靠地入库。**先解决结构化输出的可靠性，再谈其他功能。**
