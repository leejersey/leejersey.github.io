# LangChain 实战教程

> 从"调一次 API"到"构建完整 AI 应用"——用最实战的方式掌握 LangChain 核心组件，搭建 RAG、Agent、多轮对话等真实场景应用。

---

## 1. LangChain 是什么？为什么需要它？

你已经会用 `requests` 或 `httpx` 调用大模型的 API 了——传一段 prompt，拿到一段回答。但当你想构建一个**真正的 AI 应用**（带记忆的对话、基于私有文档的问答、能自主使用工具的 Agent），直接调 API 就远远不够了。LangChain 正是为了解决这个问题而生的。

### 1.1 直接调 API 有什么问题？

先来看一个最简单的大模型调用：

```python
import httpx
import os

API_KEY = os.getenv("DEEPSEEK_API_KEY")

response = httpx.post(
    "https://api.deepseek.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "用一句话解释什么是 LangChain"}],
    },
)
print(response.json()["choices"][0]["message"]["content"])
```

这段代码能跑，但当需求变复杂时，你会遇到**四个核心痛点**：

| 痛点 | 场景 | 裸调 API 的代价 |
|:---|:---|:---|
| **没有记忆** | 多轮对话，LLM 不记得上一句话 | 手动维护 messages 列表，越来越长 |
| **没有知识** | 问你的私有文档内容，LLM 一无所知 | 自己实现 RAG 全套流程（加载→分割→向量化→检索→拼接） |
| **没有工具** | 让 LLM 查数据库、搜网页、调计算器 | 自己写 JSON 解析 + 工具分发 + 错误处理 |
| **难以组合** | 多步骤工作流（总结→翻译→格式化） | 手动串联多次 API 调用，代码变成意大利面 |

```
裸调 API 适合：一问一答的简单场景
LangChain 适合：需要记忆 / 需要知识库 / 需要工具 / 需要多步编排的复杂应用
```

> 💡 **类比**：裸调 API 就像你手动操作数据库——`cursor.execute("SELECT ...")`。LangChain 就像 ORM（Django Model / SQLAlchemy）——帮你抽象掉重复的底层细节，让你专注于业务逻辑。

### 1.2 LangChain 的核心定位：LLM 应用开发框架

LangChain 不是一个模型，也不是一个 API 服务——它是一个**连接大模型与外部世界的框架**。

```
LangChain 的一句话定位：

「用标准化的组件，把 LLM 从一个"聊天接口"变成一个能记忆、能检索、
  能使用工具、能编排复杂流程的完整应用。」
```

**LangChain 的核心思想是"模块化 + 可组合"**：

```
┌──────────────────────────────────────────────────┐
│              你的 AI 应用                          │
├──────────────────────────────────────────────────┤
│  Model I/O  │  Chain  │  Memory  │  Agent        │
│  (模型交互)  │  (编排)  │  (记忆)   │  (自主决策)    │
├──────────────────────────────────────────────────┤
│  Document Loaders  │  Embeddings  │  Vector      │
│  (文档加载)          │  (向量嵌入)   │  Stores      │
├──────────────────────────────────────────────────┤
│  Middleware（中间件）│  LangGraph（Agent 运行时）   │
├──────────────────────────────────────────────────┤
│  LLM（DeepSeek / OpenAI / Claude / 本地模型）      │
└──────────────────────────────────────────────────┘
```

**LangChain 的几个设计原则：**

| 原则 | 含义 | 好处 |
|:---|:---|:---|
| **模型无关** | 同一套代码，换一行配置就能切换 DeepSeek → OpenAI → Claude | 不被厂商锁定 |
| **组件可组合** | 每个模块独立，像乐高一样自由拼装 | 按需使用，不用全买 |
| **LCEL 管道** | 用 `|` 操作符串联组件，代码像读句子一样自然 | 可读性极高 |
| **可观测** | 内置与 LangSmith 集成，追踪每一步的输入输出 | 调试不再抓瞎 |

> 💡 **LangChain 于 2025 年 10 月正式发布 v1.0 稳定版**，当前最新为 v1.2。v1.0 带来了重大升级：全新的 `create_agent` 抽象、中间件系统、`with_structured_output` 结构化输出、以及基于 LangGraph 的 Agent 运行时。旧版功能已迁移至 `langchain-classic` 包。本教程基于 v1.x 最新架构编写。

### 1.3 架构全景图：核心模块一览

本教程会按照以下顺序，逐一讲解 LangChain 的核心模块：

```
第 2 章              第 3 章           第 4 章          第 5 章          第 6 章
Model I/O    →    Chain (LCEL)   →   Memory     →    RAG        →    Agent
模型交互           链式编排           对话记忆          检索增强          自主决策
prompt → LLM     A | B | C        记住上下文      基于文档问答      使用工具

                              ↓ 组合到一起 ↓

                        第 7 章：综合实战项目
                    FastAPI + LangChain 知识库助手
```

**每个模块解决什么问题？**

| 模块 | 一句话说明 | 解决什么痛点 |
|:---|:---|:---|
| **Model I/O** | 统一的模型调用 + Prompt 模板 + 输出解析 | 不同模型 API 格式不一样 |
| **Chain (LCEL)** | 用 `|` 把多个步骤串成流水线 | 多步编排代码混乱 |
| **Memory** | 自动管理对话历史 | LLM 没有记忆 |
| **RAG** | 文档加载 → 向量化 → 检索 → 回答 | LLM 不懂你的私有数据 |
| **Agent** | LLM 自己决定用什么工具、怎么用 | 需要 LLM 执行真实操作 |

### 1.4 安装与环境配置

**环境要求：**

- **Python ≥ 3.9**（v1.0 起不再支持 Python 3.8）
- **Pydantic v2**（v1.0 起不再支持 Pydantic v1）

**安装核心包：**

```bash
# 核心框架（必装，自动包含 langchain-core）
pip install langchain

# 模型提供商（按需选择一个）
pip install langchain-deepseek       # DeepSeek（官方集成包，推荐）
pip install langchain-openai         # OpenAI（也可用于兼容 OpenAI 接口的服务）
# pip install langchain-anthropic    # Claude
# pip install langchain-google-genai # Gemini

# Agent 运行时（第 6 章用到，v1.0 的 Agent 基于 LangGraph）
pip install langgraph

# RAG 相关（第 5 章用到）
pip install langchain-chroma         # Chroma 向量数据库
pip install langchain-community      # 社区集成（文档加载器等）
```

**配置 API Key（推荐用 `.env` 文件）：**

```bash
# .env 文件
DEEPSEEK_API_KEY=sk-your-api-key-here
# 或
OPENAI_API_KEY=sk-your-api-key-here
```

```python
# 在代码中加载
from dotenv import load_dotenv
load_dotenv()  # 自动读取 .env 文件中的环境变量

# ── 方式 1：使用官方提供商包（推荐） ──
from langchain_deepseek import ChatDeepSeek

# DeepSeek 有专用的 langchain-deepseek 包，无需手动配置 base_url
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.7,
    # api_key 自动从 DEEPSEEK_API_KEY 环境变量读取
)

response = llm.invoke("你好，LangChain！")
print(response.content)
# 你好！我是一个 AI 助手，很高兴通过 LangChain 与你交流！

# ── 方式 2：init_chat_model 统一接口（v1.0 新增，推荐） ──
from langchain.chat_models import init_chat_model

# 使用 "provider:model" 统一格式，一个函数搞定所有提供商
llm = init_chat_model("deepseek:deepseek-chat")  # DeepSeek
# 切换 OpenAI：init_chat_model("openai:gpt-4o")
# 切换 Claude：init_chat_model("anthropic:claude-sonnet-4-20250514")

# 也可以用 model_provider 参数分开指定
# llm = init_chat_model("deepseek-chat", model_provider="deepseek")
```

> 💡 **本教程使用 DeepSeek 作为主要模型**（性价比高、中文能力强、兼容 OpenAI 接口），但所有代码只需改一行配置即可切换为 OpenAI / Claude / Gemini。

---

## 2. Model I/O：与大模型交互的标准化接口

Model I/O 是 LangChain 最基础的模块——它解决的是"怎么和大模型说话、怎么让大模型按你想要的格式回答"。三个核心组件：**ChatModel**（调用模型）→ **PromptTemplate**（构造输入）→ **OutputParser**（解析输出）。

### 2.1 ChatModel：统一的模型调用接口

LangChain 用 `ChatModel` 把所有大模型的 API 差异抹平了。无论你用 DeepSeek、OpenAI 还是 Claude，代码结构完全一样：

```python
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, SystemMessage

# ── 创建模型实例 ──
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.7,   # 创造性：0=确定性，1=更随机
    max_tokens=1000,    # 最大输出 token 数
)

# ── 方式 1：直接传字符串（最简单） ──
response = llm.invoke("Python 有几种基本数据类型？")
print(response.content)

# ── 方式 2：传 Message 列表（更精确地控制角色） ──
messages = [
    SystemMessage(content="你是一个资深 Python 教师，回答要简洁。"),
    HumanMessage(content="解释什么是列表推导式"),
]
response = llm.invoke(messages)
print(response.content)
```

**Message 的三种角色：**

| 角色 | 类 | 作用 |
|:---|:---|:---|
| **System** | `SystemMessage` | 设定 AI 的身份和行为规范 |
| **Human** | `HumanMessage` | 用户的输入 |
| **AI** | `AIMessage` | AI 之前的回复（用于多轮对话） |

**切换模型只需改一行：**

```python
# ── 方式 A：每个提供商用各自的类 ──
from langchain_deepseek import ChatDeepSeek
llm = ChatDeepSeek(model="deepseek-chat")  # DeepSeek

from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o")  # OpenAI

from langchain_anthropic import ChatAnthropic  # pip install langchain-anthropic
llm = ChatAnthropic(model="claude-sonnet-4-20250514")  # Claude

# ── 方式 B：init_chat_model（v1.0 新增，推荐） ──
from langchain.chat_models import init_chat_model

# 同一个函数，用 "provider:model" 格式切换提供商
llm = init_chat_model("deepseek:deepseek-chat")
llm = init_chat_model("openai:gpt-4o")
llm = init_chat_model("anthropic:claude-sonnet-4-20250514")
```

> 💡 **v1.0 新增的 `init_chat_model`** 是更优雅的选择：不需要记住每个提供商的类名，统一用一个函数，通过 `"provider:model"` 格式切换。特别适合“用户可选模型”的场景——配置文件里存一个字符串就行。

> 💡 `invoke()` 是同步调用。LangChain 还提供了 `ainvoke()`（异步）、`stream()`（流式输出，一个 token 一个 token 返回）、`batch()`（批量调用）。

### 2.2 PromptTemplate：告别手拼字符串

手动拼接 prompt 字符串很容易出错，也不利于复用。`PromptTemplate` 让你像写 f-string 模板一样构造 prompt：

```python
from langchain_core.prompts import ChatPromptTemplate

# ── 定义模板 ──
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，擅长用通俗易懂的方式解释技术概念。"),
    ("human", "请解释什么是{concept}，给一个{language}的代码示例。"),
])

# ── 填充变量 ──
messages = prompt.invoke({
    "role": "Python 教师",
    "concept": "装饰器",
    "language": "Python",
})

print(messages)
# [SystemMessage(content='你是一个Python 教师，擅长用通俗易懂的方式解释技术概念。'),
#  HumanMessage(content='请解释什么是装饰器，给一个Python的代码示例。')]

# ── 直接送给模型 ──
response = llm.invoke(messages)
print(response.content)
```

**PromptTemplate 支持多种构造方式：**

```python
# 方式 1：from_messages（最常用，精确控制每条消息的角色）
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是{role}"),
    ("human", "{question}"),
])

# 方式 2：from_template（简单场景，只有一条 human 消息）
from langchain_core.prompts import PromptTemplate
prompt = PromptTemplate.from_template("请把以下内容翻译成{language}：\n\n{text}")

# 方式 3：包含聊天历史占位符（第 4 章 Memory 会用到）
from langchain_core.prompts import MessagesPlaceholder
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有帮助的助手。"),
    MessagesPlaceholder(variable_name="chat_history"),  # 动态插入历史消息
    ("human", "{question}"),
])
```

> 💡 **PromptTemplate 的价值不只是"好看"**——它让 prompt 变成了可复用、可测试、可版本管理的代码组件。你可以把一套精心调试好的 prompt 保存为模板，团队共享。

### 2.3 OutputParser：让 LLM 返回结构化数据

LLM 默认返回自由文本。但在实际应用中，你通常需要结构化数据（JSON、列表、Pydantic 对象）。`OutputParser` 负责把 LLM 的文本输出**解析成你想要的格式**。

```python
# ── 最简单的 Parser：直接提取文本 ──
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
# 把 AIMessage 对象 → 纯字符串
text = parser.invoke(response)  # "Python 有 6 种基本数据类型..."
```

```python
# ── JSON Parser：让 LLM 返回 JSON ──
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个数据分析助手。请以 JSON 格式返回结果。"),
    ("human", "分析这个城市的基本信息：{city}\n\n{format_instructions}"),
])

# parser 自动生成格式说明，教 LLM 怎么输出 JSON
prompt_with_instructions = prompt.partial(
    format_instructions=parser.get_format_instructions()
)

chain = prompt_with_instructions | llm | parser

result = chain.invoke({"city": "杭州"})
print(result)
# {'name': '杭州', 'province': '浙江', 'population': '约1237万', 'famous_for': '西湖'}
print(type(result))  # <class 'dict'>  ← 已经是 Python 字典了！
```

```python
# ── Pydantic Parser：类型安全的结构化输出 ──
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class CityInfo(BaseModel):
    """城市信息"""
    name: str = Field(description="城市名称")
    province: str = Field(description="所属省份")
    population: str = Field(description="人口数量")
    highlights: list[str] = Field(description="城市亮点，3-5 个")

parser = PydanticOutputParser(pydantic_object=CityInfo)

# parser.get_format_instructions() 会自动生成详细的格式说明
# 告诉 LLM 需要返回什么字段、什么类型
chain = prompt_with_instructions | llm | parser

result = chain.invoke({"city": "成都"})
print(result.name)        # 成都
print(result.highlights)  # ['大熊猫繁育基地', '宽窄巷子', '火锅文化', ...]
print(type(result))       # <class 'CityInfo'>  ← Pydantic 对象，有类型校验！
```

```python
# ── with_structured_output：模型原生结构化输出（v1.0 新增，强烈推荐） ──
# 这是 v1.0 引入的最优雅方式：直接让模型返回 Pydantic 对象，
# 不需要手动拼 format_instructions，不需要单独的 Parser！

from pydantic import BaseModel, Field

class CityInfo(BaseModel):
    """城市信息"""
    name: str = Field(description="城市名称")
    province: str = Field(description="所属省份")
    population: str = Field(description="人口数量")
    highlights: list[str] = Field(description="城市亮点，3-5 个")

# 一行代码：把模型“绑定”为返回 CityInfo 的版本
structured_llm = llm.with_structured_output(CityInfo)

result = structured_llm.invoke("介绍一下成都这个城市")
print(result.name)        # 成都
print(result.highlights)  # ['大熊猫繁育基地', '宽窄巷子', '火锅文化', ...]
print(type(result))       # <class 'CityInfo'>  ← 直接拿到 Pydantic 对象！
```

> 💡 **四种结构化输出方式的选择（v1.x）：**
> - 纯文本：`StrOutputParser`
> - 需要字典：`JsonOutputParser`
> - 需要类型安全（经典方式）：`PydanticOutputParser`
> - **生产环境首选：`model.with_structured_output(Schema)`**——代码最简洁、延迟最低、可靠性最高

### 2.4 实战：构建一个智能翻译器

现在把 ChatModel + PromptTemplate + `with_structured_output` 组合起来，做一个有**语言自动检测 + 翻译 + 置信度评分**的翻译器：

```python
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# ── Step 1：定义输出结构 ──
class TranslationResult(BaseModel):
    source_language: str = Field(description="原文语言")
    target_language: str = Field(description="目标语言")
    translation: str = Field(description="翻译结果")
    confidence: float = Field(description="翻译置信度，0-1")
    alternatives: list[str] = Field(description="其他可能的翻译，最多 2 个")

# ── Step 2：构建 Prompt ──
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业翻译。请自动检测原文语言，翻译成{target_lang}。
如果原文已经是目标语言，请翻译成英文。"""),
    ("human", "{text}"),
])

# ── Step 3：用 with_structured_output 组装成链（v1.0 推荐方式） ──
llm = ChatDeepSeek(model="deepseek-chat")
structured_llm = llm.with_structured_output(TranslationResult)

translate_chain = prompt | structured_llm

# ── Step 4：使用 ──
result = translate_chain.invoke({
    "target_lang": "中文",
    "text": "The quick brown fox jumps over the lazy dog",
})

print(f"原文语言: {result.source_language}")     # 英文
print(f"翻译结果: {result.translation}")          # 敏捷的棕色狐狸跳过了那只懒狗
print(f"置信度: {result.confidence}")              # 0.95
print(f"其他翻译: {result.alternatives}")          # ['快速的棕色狐狸...', ...]
```

**这个例子展示了 Model I/O 三大组件的完美配合：**

```
PromptTemplate          ChatModel            OutputParser
  (构造输入)       →    (调用模型)       →    (解析输出)
                                           
{text, target_lang}  →  DeepSeek API   →  TranslationResult
                                            .translation
                                            .confidence
                                            .alternatives
```

**第 2 章核心知识回顾：**

| 组件 | 一句话解释 |
|:---|:---|
| **ChatModel** | 统一的模型调用接口，一行代码切换模型 |
| **init_chat_model** | v1.0 新增的统一初始化接口，一个函数搞定所有提供商 |
| **PromptTemplate** | 可复用的 prompt 模板，支持变量注入 |
| **OutputParser** | 把 LLM 文本输出解析为结构化数据（dict/Pydantic） |
| **with_structured_output** | v1.0 推荐的结构化输出，模型原生支持，最简洁可靠 |
| **管道组合** | `prompt \| llm \| parser` → 一条完整的处理链 |

---

## 3. Chain：用链式调用编排 LLM 工作流

上一章的 `prompt | llm | parser` 其实已经是一条 Chain 了。这一章深入 LangChain 的**编排核心—— LCEL（LangChain Expression Language）**，学习如何用最优雅的方式组合复杂的多步骤工作流。

### 3.1 LCEL（LangChain Expression Language）入门

LCEL 是 LangChain 的核心编排方式（始于 v0.2，v1.x 延续）。它的核心思想极其简单：**所有组件都实现 `Runnable` 接口，用 `|` 串联。**

```python
# LCEL 的核心理念：
# 任何实现了 Runnable 接口的对象，都可以用 | 串联

chain = component_a | component_b | component_c

# 等价于：
# result = component_c.invoke(component_b.invoke(component_a.invoke(input)))
# 但 LCEL 写法更简洁，而且自动支持：流式、异步、批量、并行
```

**Runnable 接口提供的方法：**

| 方法 | 作用 | 适用场景 |
|:---|:---|:---|
| `invoke(input)` | 同步调用，返回完整结果 | 最常用 |
| `ainvoke(input)` | 异步调用 | FastAPI 等异步框架 |
| `stream(input)` | 流式输出（逐 token 返回） | 聊天界面 |
| `batch([input1, input2])` | 批量调用 | 批处理任务 |

### 3.2 管道操作符 `|`：像搭积木一样组合

`|` 操作符把多个组件**串联成一条流水线**——前一个组件的输出，自动变成后一个组件的输入：

```python
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatDeepSeek(model="deepseek-chat")

# ── 链 1：生成代码 ──
code_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个 Python 专家。只返回代码，不要解释。"),
    ("human", "写一个{task}的函数"),
])

code_chain = code_prompt | llm | StrOutputParser()

# ── 链 2：解释代码 ──
explain_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个编程老师。用中文逐行解释下面的代码。"),
    ("human", "{code}"),
])

explain_chain = explain_prompt | llm | StrOutputParser()

# ── 串联两条链：生成代码 → 解释代码 ──
from langchain_core.runnables import RunnablePassthrough

full_chain = (
    code_chain                                     # Step 1: 生成代码
    | (lambda code: {"code": code})                # 把字符串包装成字典
    | explain_chain                                # Step 2: 解释代码
)

result = full_chain.invoke({"task": "快速排序"})
print(result)
# 逐行解释快速排序的 Python 实现...
```

**用 `RunnableLambda` 替代裸 lambda（推荐）：**

```python
from langchain_core.runnables import RunnableLambda

# 自定义中间处理步骤
def format_as_input(code_text: str) -> dict:
    """把上一步的纯文本输出，转成下一步需要的字典格式"""
    return {"code": code_text}

full_chain = code_chain | RunnableLambda(format_as_input) | explain_chain
```

### 3.3 RunnableParallel：并行执行多条链

有时候你需要**同时执行多个任务**，然后把结果合并。`RunnableParallel` 正是干这个的：

```python
from langchain_core.runnables import RunnableParallel

# 定义三条并行链
summary_chain = (
    ChatPromptTemplate.from_template("用一句话总结：{text}")
    | llm | StrOutputParser()
)

keywords_chain = (
    ChatPromptTemplate.from_template("提取 5 个关键词（用逗号分隔）：{text}")
    | llm | StrOutputParser()
)

sentiment_chain = (
    ChatPromptTemplate.from_template("分析情感倾向（正面/负面/中性）：{text}")
    | llm | StrOutputParser()
)

# 用 RunnableParallel 并行执行
analysis_chain = RunnableParallel(
    summary=summary_chain,
    keywords=keywords_chain,
    sentiment=sentiment_chain,
)

result = analysis_chain.invoke({
    "text": "LangChain 是一个强大的 LLM 应用开发框架，但学习曲线比较陡峭。"
})

print(result)
# {
#   'summary': 'LangChain 是强大但学习成本高的 LLM 框架。',
#   'keywords': 'LangChain, LLM, 框架, 学习曲线, 应用开发',
#   'sentiment': '中性（既肯定了优势，也指出了不足）'
# }
```

```
RunnableParallel 的执行方式：

                    ┌─ summary_chain ──→ summary
input ──→ 复制 3 份 ├─ keywords_chain ──→ keywords    ──→ 合并为字典
                    └─ sentiment_chain ─→ sentiment
```

> 💡 **并行 ≠ 多线程**。`RunnableParallel` 在同步模式下是依次调用（但 API 请求本身是 I/O 等待），在 `ainvoke()` 异步模式下才是真正的并发请求。生产环境建议用异步。

### 3.4 流式输出：一个字一个字吐出来

ChatGPT 那种"打字机效果"是怎么实现的？用 `stream()` 方法：

```python
chain = (
    ChatPromptTemplate.from_template("写一首关于{topic}的五言绝句")
    | llm
    | StrOutputParser()
)

# ── 流式输出 ──
for chunk in chain.stream({"topic": "秋天"}):
    print(chunk, end="", flush=True)
# 秋｜风｜吹｜落｜叶，
# 寒｜露｜染｜山｜红。
# ...
```

**在 FastAPI 中做流式响应：**

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/chat")
async def chat(question: str):
    chain = prompt | llm | StrOutputParser()
    
    async def generate():
        async for chunk in chain.astream({"question": question}):
            yield chunk  # 一个 token 一个 token 发给前端
    
    return StreamingResponse(generate(), media_type="text/plain")
```

> 💡 **关键区别**：`invoke()` 等所有 token 生成完才返回（用户等很久），`stream()` / `astream()` 边生成边返回（用户体验好很多）。LCEL 的一大优势是：**你用 `|` 组装的链，自动支持流式**，不需要额外改代码。

### 3.5 实战：多步骤内容生成管线

构建一个"技术博客自动生成器"：输入一个主题 → 并行生成大纲和关键要点 → 根据大纲撰写全文：

```python
from langchain_core.runnables import RunnableParallel, RunnableLambda

# ── Step 1：并行生成大纲 + 关键要点 ──
outline_chain = (
    ChatPromptTemplate.from_template(
        "为主题「{topic}」生成一篇技术博客的大纲（3-5 个章节标题）"
    )
    | llm | StrOutputParser()
)

points_chain = (
    ChatPromptTemplate.from_template(
        "列出关于「{topic}」最重要的 5 个技术要点（简短的要点列表）"
    )
    | llm | StrOutputParser()
)

parallel_step = RunnableParallel(outline=outline_chain, key_points=points_chain)

# ── Step 2：根据大纲和要点撰写全文 ──
write_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "你是一个技术博客作者。根据给定的大纲和关键要点，撰写一篇完整的博客文章。"),
        ("human", "大纲：\n{outline}\n\n关键要点：\n{key_points}\n\n请撰写完整文章。"),
    ])
    | llm | StrOutputParser()
)

# ── 组合完整管线 ──
blog_pipeline = parallel_step | write_chain

# 使用
article = blog_pipeline.invoke({"topic": "Python 异步编程入门"})
print(article)
```

**管线执行流程：**

```
                    ┌─ outline_chain ──→ outline ─┐
{"topic": "..."} ──→                               ├──→ write_chain ──→ 完整文章
                    └─ points_chain ──→ key_points ┘
```

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **LCEL** | LangChain 的编排语言，所有组件通过 `|` 串联 |
| **Runnable** | 统一接口，支持 invoke/stream/batch/ainvoke |
| **RunnableParallel** | 并行执行多条链，结果合并为字典 |
| **RunnableLambda** | 把普通函数包装成 Runnable，插入管道中 |
| **stream()** | 流式输出，打字机效果 |

---

## 4. Memory：让 LLM 拥有记忆

你有没有发现，每次调用 LLM 都像是"第一次见面"？它完全不记得上一轮你说了什么。这一章解决这个问题——让你的 AI 应用拥有**多轮对话记忆**。

### 4.1 LLM 为什么"没有记忆"？

LLM 本身是**无状态的**。每次调用都是独立的——模型不会自动保存上一次的对话内容。

```python
llm = ChatDeepSeek(model="deepseek-chat")

# 第 1 轮
response1 = llm.invoke("我叫小明")
print(response1.content)  # 你好小明！很高兴认识你！

# 第 2 轮
response2 = llm.invoke("我叫什么名字？")
print(response2.content)  # 抱歉，我不知道你叫什么名字。 ← 完全忘了！
```

**为什么？** 因为第 2 轮调用时，API 收到的只有 `"我叫什么名字？"` 这一条消息。第 1 轮的对话内容根本没有传过去。

**"记忆"的本质就是：把历史对话拼接到新请求里。**

```python
from langchain_core.messages import HumanMessage, AIMessage

# 手动拼接历史 → LLM 就"记住"了
messages = [
    HumanMessage(content="我叫小明"),
    AIMessage(content="你好小明！很高兴认识你！"),  # 上一轮的回复
    HumanMessage(content="我叫什么名字？"),          # 新问题
]

response = llm.invoke(messages)
print(response.content)  # 你叫小明！ ← 记住了！
```

> 💡 **核心认知**：LLM 的"记忆"不是模型内部的功能，而是**应用层**的工作——你需要在每次请求时，把之前的对话历史拼到 messages 里发过去。LangChain 的 Memory 模块就是帮你自动化这个过程。

### 4.2 ConversationBufferMemory：完整对话记忆

在 LangChain 的最新 LCEL 架构里，推荐的方式是用 `ChatMessageHistory` + `RunnableWithMessageHistory` 来管理记忆：

```python
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

llm = ChatDeepSeek(model="deepseek-chat")

# ── Step 1：定义带历史占位符的 Prompt ──
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的助手。"),
    MessagesPlaceholder(variable_name="chat_history"),  # 历史消息插入这里
    ("human", "{input}"),
])

chain = prompt | llm | StrOutputParser()

# ── Step 2：创建会话存储（按 session_id 隔离） ──
store = {}  # 简单的内存存储

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# ── Step 3：包装成带记忆的链 ──
chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# ── 使用：同一个 session_id 的对话共享记忆 ──
config = {"configurable": {"session_id": "user_001"}}

print(chain_with_memory.invoke({"input": "我叫小明，我是一个 Python 程序员"}, config=config))
# 你好小明！很高兴认识你，Python 是一门很棒的语言！

print(chain_with_memory.invoke({"input": "我叫什么？我的职业是什么？"}, config=config))
# 你叫小明，你是一个 Python 程序员！ ← 完美记住了！

# 不同 session_id = 不同的对话记忆
config2 = {"configurable": {"session_id": "user_002"}}
print(chain_with_memory.invoke({"input": "我叫什么？"}, config=config2))
# 抱歉，你还没有告诉我你的名字。 ← 新会话，没有记忆
```

**记忆的工作流程：**

```
用户发送 "我叫什么名字？"
       │
       ▼
RunnableWithMessageHistory：
  1. 根据 session_id 取出历史消息
  2. 把历史 + 新消息组装成完整 messages
  3. 发送给 LLM
  4. 把新的问答对存回历史
       │
       ▼
LLM 收到的实际消息：
  [system] 你是一个友好的助手。
  [human]  我叫小明，我是 Python 程序员   ← 历史
  [ai]     你好小明！...                  ← 历史
  [human]  我叫什么名字？                  ← 新消息
```

> 💡 **Buffer 记忆的问题**：随着对话轮数增加，历史消息会越来越长，最终超出模型的 context window。解决方案：摘要记忆。

### 4.3 ConversationSummaryMemory：摘要式记忆

当对话很长时（几十轮甚至上百轮），把所有历史消息都塞进 prompt 会**撑爆 context window**。摘要记忆的思路是：**用 LLM 把之前的对话压缩成一段摘要**，而不是保留完整历史。

```python
from langchain_core.messages import HumanMessage, AIMessage

def summarize_history(llm, messages, max_messages=6):
    """
    当历史消息超过 max_messages 条时，
    用 LLM 生成摘要来替代旧消息
    """
    if len(messages) <= max_messages:
        return messages  # 没超限，直接返回
    
    # 取出需要被压缩的旧消息
    old_messages = messages[:-max_messages]
    recent_messages = messages[-max_messages:]
    
    # 用 LLM 生成摘要
    old_text = "\n".join(
        f"{'用户' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
        for m in old_messages
    )
    
    summary = llm.invoke(
        f"请用 2-3 句话总结以下对话的关键信息：\n\n{old_text}"
    ).content
    
    # 返回：摘要 + 最近的消息
    from langchain_core.messages import SystemMessage
    return [SystemMessage(content=f"之前对话的摘要：{summary}")] + recent_messages
```

**三种记忆策略对比：**

| 策略 | 原理 | 优点 | 缺点 |
|:---|:---|:---|:---|
| **Buffer** | 保留全部历史 | 信息无损 | 长对话会超出 token 限制 |
| **Summary** | 旧消息压缩为摘要 | 支持超长对话 | 摘要可能丢失细节 |
| **Window** | 只保留最近 N 轮 | 简单高效 | 完全丢失早期信息 |

> 💡 **生产环境推荐**：混合策略——最近 5-10 轮用 Buffer（保留细节），更早的部分用 Summary（压缩但不丢失关键信息）。

### 4.4 实战：构建一个有上下文的多轮对话机器人

把前面学的组合起来，构建一个完整的多轮对话机器人，支持**角色设定、记忆管理、流式输出**：

```python
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# ── 配置 ──
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.7,
    streaming=True,  # 启用流式
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个名叫"小智"的 AI 编程助手。
你的特点：
- 擅长 Python、JavaScript、Rust
- 回答简洁，代码示例清晰
- 会记住用户之前说过的话，主动关联上下文"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

chain = prompt | llm | StrOutputParser()

# ── 记忆管理 ──
store = {}

def get_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

chatbot = RunnableWithMessageHistory(
    chain, get_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# ── 交互循环 ──
def chat(session_id="default"):
    config = {"configurable": {"session_id": session_id}}
    print("🤖 小智：你好！我是 AI 编程助手小智，有什么可以帮你的？")
    print("（输入 'quit' 退出）\n")
    
    while True:
        user_input = input("你：")
        if user_input.lower() == "quit":
            break
        
        print("🤖 小智：", end="")
        # 流式输出
        for chunk in chatbot.stream({"input": user_input}, config=config):
            print(chunk, end="", flush=True)
        print("\n")

# chat()  # 取消注释即可运行
```

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **LLM 无状态** | 每次调用独立，需要应用层管理记忆 |
| **Buffer 记忆** | 保留完整历史，简单但有 token 限制 |
| **Summary 记忆** | 压缩旧对话为摘要，支持长对话 |
| **RunnableWithMessageHistory** | 简单链的记忆管理方式 |
| **LangGraph Checkpointer** | Agent 场景推荐，持久化完整图状态（v1.0） |
| **session_id** | 用于隔离不同用户/会话的记忆 |

> 💡 **v1.0 记忆管理策略选择：**
> - **简单聊天链**：继续用 `RunnableWithMessageHistory`，简单够用
> - **Agent / 复杂工作流**：用 LangGraph + Checkpointer（如 `MemorySaver`、`PostgresSaver`），能持久化完整状态
> - **旧版 `ConversationBufferMemory` 等已弃用**，新项目请勿使用

---

## 5. RAG（检索增强生成）：让 LLM 基于你的数据回答

RAG 是当前最热门的 LLM 应用模式——你的公司有几百份内部文档，想让 AI 基于这些文档回答问题，但又不想花大钱微调模型。**RAG 就是答案**：先检索相关文档片段，再把它们塞进 prompt 让 LLM 回答。

### 5.1 RAG 是什么？为什么比微调更实用？

```
RAG（Retrieval-Augmented Generation）= 检索 + 生成

传统方式：用户提问 → LLM 凭"记忆"回答 → 可能瞎编（幻觉）
RAG 方式：用户提问 → 检索相关文档 → 把文档+问题一起给 LLM → 基于事实回答
```

**RAG vs 微调 vs 长上下文：**

| 方案 | 成本 | 实时性 | 适用场景 |
|:---|:---|:---|:---|
| **RAG** | 低（只需 Embedding） | 高（文档更新即生效） | 知识库问答、文档助手 |
| **微调** | 高（需要 GPU 训练） | 低（每次更新都要重新训练） | 风格定制、领域专用模型 |
| **长上下文** | 中（token 费用高） | 高 | 少量文档，一次性使用 |

**RAG 的完整流程：**

```
离线阶段（只做一次）：
  文档 → 分割成小块 → 向量化（Embedding）→ 存入向量数据库

在线阶段（每次提问）：
  用户问题 → 向量化 → 在向量数据库中搜索相似文档块
           → 把相关文档块 + 问题拼成 prompt → LLM 回答
```

### 5.2 文档加载：PDF、Markdown、网页

LangChain 提供了几十种文档加载器，覆盖常见格式：

```python
# ── 加载 Markdown 文件 ──
from langchain_community.document_loaders import TextLoader

loader = TextLoader("./docs/guide.md", encoding="utf-8")
docs = loader.load()
print(f"加载了 {len(docs)} 个文档")
print(docs[0].page_content[:200])  # 文档内容
print(docs[0].metadata)             # {'source': './docs/guide.md'}

# ── 加载 PDF ──
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("./docs/report.pdf")
docs = loader.load()  # 每页一个 Document 对象
print(f"共 {len(docs)} 页")

# ── 加载网页 ──
from langchain_community.document_loaders import WebBaseLoader

loader = WebBaseLoader("https://docs.python.org/3/tutorial/index.html")
docs = loader.load()

# ── 批量加载目录下的所有文件 ──
from langchain_community.document_loaders import DirectoryLoader

loader = DirectoryLoader("./docs/", glob="**/*.md", show_progress=True)
docs = loader.load()
print(f"加载了 {len(docs)} 个文档")
```

> 💡 每个 `Document` 对象包含两个属性：`page_content`（文本内容）和 `metadata`（来源信息，如文件路径、页码）。metadata 在最终回答时可以用来标注"信息来源"。

### 5.3 文本分割：RecursiveCharacterTextSplitter

一份文档可能有几万字，但 LLM 的 context window 有限（而且塞太多内容效果也不好）。所以需要把文档**切成小块**：

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # 每块最多 500 个字符
    chunk_overlap=50,     # 相邻块重叠 50 个字符（防止语义被截断）
    separators=["\n\n", "\n", "。", "！", "？", " ", ""],  # 分割优先级
)

# 分割文档
chunks = splitter.split_documents(docs)
print(f"原始文档 {len(docs)} 个 → 分割成 {len(chunks)} 个块")
print(f"每块大约 {len(chunks[0].page_content)} 个字符")
```

**分割策略的关键参数：**

```
chunk_size=500, chunk_overlap=50 的效果：

原文：[████████████████████████████████████████████]
块 1：[██████████████]
块 2：        [██████████████]      ← 有 50 字符重叠
块 3：                [██████████████]
```

| 参数 | 建议值 | 说明 |
|:---|:---|:---|
| `chunk_size` | 300~1000 | 太小失去上下文，太大检索不精准 |
| `chunk_overlap` | 50~100 | 防止关键信息在分割边界被截断 |
| `separators` | 按语义优先级 | 优先按段落分，其次按句子，最后按字符 |

> 💡 **分割质量直接影响 RAG 效果**。建议根据你的文档类型调整参数——代码文档用较小的 chunk_size（300），叙事性文档用较大的（800~1000）。

### 5.4 向量存储：Embedding + Chroma/FAISS

分割好的文本块需要转成**向量（数字数组）**，才能做语义搜索。这个过程叫 Embedding。

```python
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# ── Step 1：创建 Embedding 模型 ──
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",  # OpenAI 的嵌入模型
    # 如果用 DeepSeek 或其他提供商，需要对应的 Embedding 类
)

# ── Step 2：把文档块存入向量数据库 ──
vectorstore = Chroma.from_documents(
    documents=chunks,      # 上一步分割好的文档块
    embedding=embeddings,
    persist_directory="./chroma_db",  # 持久化到本地
)
print(f"已存入 {vectorstore._collection.count()} 个向量")

# ── Step 3：语义搜索 ──
results = vectorstore.similarity_search("什么是装饰器？", k=3)
for doc in results:
    print(f"📄 来源: {doc.metadata.get('source', '未知')}")
    print(f"   内容: {doc.page_content[:100]}...")
    print()
```

**Embedding 的工作原理：**

```
文本                          向量（高维数字数组）
"Python 装饰器"    →  [0.12, -0.34, 0.56, ..., 0.78]   768 维
"Python decorator" →  [0.11, -0.33, 0.55, ..., 0.77]   768 维  ← 语义相近，向量也接近！
"今天天气不错"      →  [0.89, 0.23, -0.67, ..., 0.01]   768 维  ← 语义不同，向量差异大

搜索时：把用户问题也转成向量，找最"接近"的文档块
```

**Chroma vs FAISS：**

| 特性 | Chroma | FAISS |
|:---|:---|:---|
| 安装 | `pip install langchain-chroma` | `pip install faiss-cpu` |
| 持久化 | ✅ 内置 | ❌ 需手动 save/load |
| 过滤 | ✅ 支持 metadata 过滤 | ❌ 不支持 |
| 适用场景 | 中小规模（万级文档） | 大规模（百万级文档） |

> 💡 **小项目用 Chroma**（开箱即用，支持持久化和过滤），**大规模生产用 FAISS 或 Milvus**。

### 5.5 检索链：从"搜到"到"回答"

有了向量数据库，就可以构建完整的 RAG 链——**先检索、再回答**：

```python
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

llm = ChatDeepSeek(model="deepseek-chat")

# ── 创建检索器 ──
retriever = vectorstore.as_retriever(
    search_type="similarity",  # 相似度搜索
    search_kwargs={"k": 3},     # 返回最相关的 3 个文档块
)

# ── RAG Prompt 模板 ──
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个知识库助手。请根据以下参考文档回答用户问题。
如果文档中没有相关信息，请明确告知用户"我没有找到相关信息"，不要编造。

参考文档：
{context}"""),
    ("human", "{question}"),
])

# ── 辅助函数：把检索到的文档格式化为字符串 ──
def format_docs(docs):
    return "\n\n---\n\n".join(
        f"【来源：{doc.metadata.get('source', '未知')}】\n{doc.page_content}"
        for doc in docs
    )

# ── 组装 RAG 链 ──
rag_chain = (
    {
        "context": retriever | format_docs,   # 检索 → 格式化
        "question": RunnablePassthrough(),     # 用户问题直接传递
    }
    | rag_prompt
    | llm
    | StrOutputParser()
)

# ── 使用 ──
answer = rag_chain.invoke("Python 装饰器的 @语法糖是怎么工作的？")
print(answer)
# 根据参考文档，@语法糖实际上是 func = decorator(func) 的简写...
```

**RAG 链的数据流：**

```
"装饰器怎么工作？"
       │
       ├──→ retriever.invoke()
       │      → 向量搜索
       │      → 返回 3 个相关文档块
       │      → format_docs() 拼成字符串
       │      → {"context": "文档内容..."}
       │
       ├──→ RunnablePassthrough()
       │      → {"question": "装饰器怎么工作？"}
       │
       ▼
  合并为 {"context": "...", "question": "..."}
       │
       ▼
  rag_prompt → LLM → StrOutputParser → 最终回答
```

### 5.6 实战：基于本地文档的智能问答系统

把前面所有步骤串起来，构建一个完整的"本地文档问答系统"：

```python
from langchain_deepseek import ChatDeepSeek
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ════════════════════════════════════════════
# 离线阶段：文档 → 向量数据库（只需运行一次）
# ════════════════════════════════════════════

def build_knowledge_base(docs_dir: str, db_dir: str = "./chroma_db"):
    """构建知识库"""
    # 1. 加载文档
    loader = DirectoryLoader(docs_dir, glob="**/*.md")
    docs = loader.load()
    print(f"📄 加载了 {len(docs)} 个文档")
    
    # 2. 分割
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    print(f"✂️ 分割成 {len(chunks)} 个块")
    
    # 3. 向量化 + 存储
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory=db_dir)
    print(f"💾 已存入向量数据库: {db_dir}")
    return vectorstore

# ════════════════════════════════════════════
# 在线阶段：问答（每次提问调用）
# ════════════════════════════════════════════

def create_qa_chain(vectorstore):
    """创建问答链"""
    llm = ChatDeepSeek(model="deepseek-chat")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """基于以下参考文档回答问题。引用来源时标注文件名。
如果文档中没有相关信息，回答"我没有找到相关信息"。

参考文档：
{context}"""),
        ("human", "{question}"),
    ])
    
    def format_docs(docs):
        return "\n\n---\n\n".join(
            f"【{doc.metadata.get('source', '?')}】\n{doc.page_content}"
            for doc in docs
        )
    
    return (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt | llm | StrOutputParser()
    )

# ════════════════════════════════════════════
# 使用
# ════════════════════════════════════════════

# 首次运行：构建知识库
# vectorstore = build_knowledge_base("./my_docs/")

# 后续运行：加载已有知识库
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

qa = create_qa_chain(vectorstore)
print(qa.invoke("什么是 Python 装饰器？"))
```

**第 5 章核心知识回顾：**

| 步骤 | 组件 | 一句话解释 |
|:---|:---|:---|
| 加载 | `DocumentLoader` | 把文件/网页变成 Document 对象 |
| 分割 | `TextSplitter` | 把长文档切成小块 |
| 向量化 | `Embeddings` | 把文本转成高维数字向量 |
| 存储 | `VectorStore` | 存储向量，支持相似度搜索 |
| 检索 | `Retriever` | 根据问题找到最相关的文档块 |
| 回答 | `LLM + Prompt` | 把文档+问题组合，生成回答 |

---

## 6. Agent：让 LLM 自主决策和使用工具

Chain 是"你定好流程，LLM 按步骤执行"。Agent 则完全不同——**你只给 LLM 一个目标和一堆工具，让它自己决定用什么工具、按什么顺序完成任务**。

### 6.1 从 Chain 到 Agent：从"按剧本演"到"自主决策"

```
Chain（链式调用）：
  你定义：Step1 → Step2 → Step3 → 输出
  LLM 只负责：执行每一步
  类比：流水线工人

Agent（智能体）：
  你定义：目标 + 可用工具
  LLM 自己决定：用什么工具、按什么顺序、何时结束
  类比：独立做事的员工
```

**什么时候用 Agent？**

| 场景 | Chain 还是 Agent？ |
|:---|:---|
| 固定流程（翻译→润色→格式化） | ✅ Chain |
| 需要根据情况选择不同工具 | ✅ Agent |
| 需要多次迭代（搜索→分析→再搜索） | ✅ Agent |
| 用户意图不确定，需要 AI 判断 | ✅ Agent |

### 6.2 Tool：教 LLM 使用工具

在 LangChain 中，Tool 就是**LLM 可以调用的函数**。用 `@tool` 装饰器定义最简单：

```python
from langchain_core.tools import tool

@tool
def multiply(a: int, b: int) -> int:
    """将两个数字相乘。当需要计算乘法时使用此工具。"""
    return a * b

@tool
def get_word_count(text: str) -> int:
    """统计文本中的字符数。"""
    return len(text)

# Tool 对象有这些属性
print(multiply.name)         # multiply
print(multiply.description)  # 将两个数字相乘。当需要计算乘法时使用此工具。
print(multiply.args_schema)  # 参数类型定义（自动从类型注解推断）

# 直接调用
print(multiply.invoke({"a": 6, "b": 7}))  # 42
```

**Tool 的 docstring 极其重要**——LLM 通过它来判断"什么时候该用这个工具"。写得越清晰，Agent 的决策越准确：

```python
# ❌ 差的描述
@tool
def search(query: str) -> str:
    """搜索"""  # LLM 不知道该在什么场景用
    ...

# ✅ 好的描述
@tool
def search_web(query: str) -> str:
    """在互联网上搜索最新信息。当用户问到近期事件、实时数据、
    或你不确定的事实性问题时，使用此工具。"""
    ...
```

### 6.3 ReAct 模式：思考-行动-观察循环

LangChain 的 Agent 默认使用 **ReAct（Reasoning + Acting）** 模式——LLM 在每一步都会经历"思考→行动→观察"的循环：

```
用户问题："北京今天的气温是多少摄氏度？换算成华氏度是多少？"

🧠 思考：我需要先查北京的天气，获取气温，然后做单位换算。
🔧 行动：调用 get_weather("北京") 工具
👁️ 观察：返回结果 → "北京今天 22°C，晴"

🧠 思考：气温是 22°C，我需要换算成华氏度。公式是 F = C × 9/5 + 32
🔧 行动：调用 multiply(22, 9) 工具
👁️ 观察：返回结果 → 198

🧠 思考：198 / 5 + 32 = 71.6°F。我有了最终答案。
💬 回答：北京今天 22°C（约 71.6°F），天气晴朗。
```

**用 LangChain 创建 Agent（v1.0 新 API）：**

```python
from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek

# 创建模型实例
llm = ChatDeepSeek(model="deepseek-chat")

# 创建 Agent（基于 LangGraph 运行时）
agent = create_agent(
    model=llm,  # 传入 ChatModel 实例（推荐），也可用 "deepseek:deepseek-chat" 字符串
    tools=[multiply, get_word_count],
    system_prompt="你是一个有帮助的助手。请使用提供的工具来回答问题。",
)

# 使用（输入格式为 messages 列表）
result = agent.invoke({
    "messages": [{"role": "user", "content": "请计算 123 乘以 456"}]
})
print(result["messages"][-1].content)  # 56088
```

> 💡 **v1.0 重大变化：**
> - **旧 API（已迁移至 `langchain-classic`）**：`create_tool_calling_agent()` + `AgentExecutor`，需要手动定义包含 `agent_scratchpad` 的 Prompt 模板
> - **新 API：`create_agent()`**，只需传 `model`、`tools`、`system_prompt`，底层基于 LangGraph 运行，自动处理工具调用循环
> - **`model` 参数**：推荐传入 ChatModel 实例（方便自定义 temperature 等），也可传 `"deepseek:deepseek-chat"` 字符串

### 6.4 自定义 Tool：让 Agent 调用你的 API

实际项目中，你需要让 Agent 调用自己的业务 API。下面展示如何把任何 Python 函数变成 Agent 可用的工具：

```python
from langchain_core.tools import tool
import httpx

@tool
def search_knowledge_base(query: str) -> str:
    """搜索内部知识库。当用户问到公司产品、内部文档、业务流程相关的问题时使用。"""
    # 调用你自己的 API
    response = httpx.get(
        "http://localhost:8000/api/search",
        params={"q": query, "limit": 3},
    )
    results = response.json()
    return "\n".join(r["content"] for r in results)

@tool
def create_ticket(title: str, description: str, priority: str = "medium") -> str:
    """创建一个工单/任务。当用户要求创建任务、报告问题、提交需求时使用。
    priority 可选值：low, medium, high, urgent
    """
    response = httpx.post(
        "http://localhost:8000/api/tickets",
        json={"title": title, "description": description, "priority": priority},
    )
    ticket = response.json()
    return f"✅ 已创建工单 #{ticket['id']}: {title}"

@tool
def get_current_time() -> str:
    """获取当前时间。当用户问到现在几点、今天日期时使用。"""
    from datetime import datetime
    return datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
```

> 💡 **安全提示**：Agent 能调用你给它的任何工具。在生产环境中，务必对工具的输入做校验、限制权限范围、记录调用日志。不要给 Agent 直接执行 SQL 或 shell 命令的权限。

### 6.5 实战：能搜索 + 计算 + 查天气的智能助手

构建一个综合能力的智能助手——同时拥有搜索、计算、时间查询等多种工具：

```python
from langchain.agents import create_agent
from langchain_core.tools import tool

# ── 定义工具集 ──
@tool
def calculator(expression: str) -> str:
    """计算数学表达式。支持加减乘除、幂运算等。
    例如：'2 + 3 * 4'、'2 ** 10'、'100 / 7'"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"

@tool
def get_current_time() -> str:
    """获取当前日期和时间。"""
    from datetime import datetime
    return datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

@tool
def string_length(text: str) -> int:
    """统计字符串的长度（字符数）。"""
    return len(text)

@tool
def text_to_uppercase(text: str) -> str:
    """将英文文本转换为大写。"""
    return text.upper()

# ── 组装 Agent（v1.0 新 API） ──
tools = [calculator, get_current_time, string_length, text_to_uppercase]

llm = ChatDeepSeek(model="deepseek-chat")

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="""你是一个多功能 AI 助手，拥有以下工具：
- 计算器：数学计算
- 时间查询：获取当前时间
- 字符串工具：统计长度、转大写

请根据用户需求选择合适的工具。如果不需要工具，直接回答即可。""",
)

# ── 测试 ──
# 需要工具的问题
result = agent.invoke({
    "messages": [{"role": "user", "content": "2 的 20 次方是多少？"}]
})
print(result["messages"][-1].content)
# Agent 会调用 calculator("2 ** 20") → 1048576

# 多步骤推理
result = agent.invoke({
    "messages": [{"role": "user", "content": "现在几点了？距离晚上 10 点还有多久？"}]
})
print(result["messages"][-1].content)
# Agent 会先调用 get_current_time()，然后自己计算时差

# 不需要工具的问题
result = agent.invoke({
    "messages": [{"role": "user", "content": "你好，介绍一下你自己"}]
})
print(result["messages"][-1].content)
# Agent 直接回答，不调用任何工具
```


### 6.6 中间件（Middleware）：控制 Agent 的执行流程（v1.0 新增）

v1.0 引入了**中间件系统**，可以在 Agent 执行循环的关键节点插入自定义逻辑。最常用的是 **Human-in-the-Loop（人工审批）**——让 Agent 在调用敏感工具前暂停，等待人工确认：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

# 配置人工审批中间件
hitl = HumanInTheLoopMiddleware(
    interrupt_on={
        "create_ticket": True,      # 创建工单前需要人工确认
        "delete_database": {"allowed_decisions": ["approve", "reject"]},
    }
)

# 创建带中间件的 Agent
agent = create_agent(
    model=ChatDeepSeek(model="deepseek-chat"),
    tools=tools,
    middleware=[hitl],
    checkpointer=InMemorySaver(),  # 中间件需要状态持久化
)
```

**中间件的工作流程：**

```
用户请求 → Agent 决定调用 create_ticket
       → HumanInTheLoopMiddleware 拦截
       → Agent 暂停，等待人工决策
       → 人工选择：approve / edit / reject
       → Agent 继续执行（或放弃该工具调用）
```

> 💡 **中间件不只有 HITL**——你可以用中间件实现：摘要压缩（防止上下文过长）、PII 脱敏（自动移除敏感信息）、成本追踪（统计 token 用量）等。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Agent** | LLM 自主决策用什么工具、按什么顺序完成任务 |
| **Tool** | LLM 可调用的函数，用 `@tool` 定义 |
| **ReAct** | 思考→行动→观察的循环决策模式 |
| **create_agent** | v1.0 统一的 Agent 创建接口，基于 LangGraph 运行时 |
| **docstring** | Tool 的描述决定了 LLM 何时选用该工具 |
| **Middleware** | v1.0 新增的中间件系统，支持人工审批等控制 |

---

## 7. 实战项目：构建一个完整的 AI 知识库助手

前面 6 章学了 LangChain 的所有核心模块，这一章把它们**全部组合起来**，构建一个端到端的 AI 知识库助手——用 FastAPI 做后端，支持文档上传、语义检索、多轮对话、流式响应。

### 7.1 项目架构设计

```
项目结构：

knowledge-assistant/
├── main.py              # FastAPI 入口
├── chains.py            # LangChain 链定义
├── knowledge_base.py    # 知识库管理（加载、分割、向量化）
├── memory_store.py      # 对话记忆管理
├── config.py            # 配置（API Key、模型参数）
├── requirements.txt     # 依赖
└── docs/                # 用户上传的文档目录
```

**系统架构图：**

```
用户（前端/curl/Postman）
      │
      ▼
┌─────────────────────────────────────────────┐
│              FastAPI 后端                     │
├─────────────────────────────────────────────┤
│                                             │
│  POST /upload    → knowledge_base.py        │
│    上传文档 → 分割 → 向量化 → Chroma        │
│                                             │
│  POST /chat      → chains.py               │
│    问题 → 检索文档 → 拼接prompt → LLM       │
│    ↕ memory_store.py（多轮记忆）             │
│    ↕ 流式SSE响应                             │
│                                             │
├─────────────────────────────────────────────┤
│  Chroma（向量数据库）  │  InMemory（记忆存储）│
└─────────────────────────────────────────────┘
```

### 7.2 后端：FastAPI + LangChain 集成

**`config.py` — 配置管理：**

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# 模型配置
LLM_MODEL = "deepseek-chat"
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Embedding 配置
EMBEDDING_MODEL = "text-embedding-3-small"

# 知识库配置
CHROMA_DB_DIR = "./chroma_db"
DOCS_DIR = "./docs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
```

**`main.py` — FastAPI 入口：**

```python
# main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from knowledge_base import KnowledgeBase
from chains import create_rag_chain
from memory_store import MemoryStore

app = FastAPI(title="AI 知识库助手")

# 初始化核心组件
kb = KnowledgeBase()
memory = MemoryStore()

class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档到知识库"""
    content = await file.read()
    file_path = f"./docs/{file.filename}"
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 向量化并存入数据库
    num_chunks = kb.add_document(file_path)
    return {"message": f"✅ 已添加 {file.filename}，生成 {num_chunks} 个向量块"}

@app.post("/chat")
async def chat(req: ChatRequest):
    """对话接口（流式响应）"""
    chain = create_rag_chain(kb.vectorstore, memory.get_history(req.session_id))
    
    async def generate():
        full_response = ""
        async for chunk in chain.astream({"input": req.question}):
            full_response += chunk
            yield chunk
        # 对话结束后保存记忆
        memory.save_message(req.session_id, req.question, full_response)
    
    return StreamingResponse(generate(), media_type="text/plain")

@app.get("/health")
async def health():
    return {"status": "ok", "documents": kb.doc_count}
```

### 7.3 知识库管理：文档上传与向量化

**`knowledge_base.py` — 文档加载 + 分割 + 向量化：**

```python
# knowledge_base.py
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import config

class KnowledgeBase:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
        )
        
        # 加载已有的向量数据库（如果存在的话）
        self.vectorstore = Chroma(
            persist_directory=config.CHROMA_DB_DIR,
            embedding_function=self.embeddings,
        )
    
    def add_document(self, file_path: str) -> int:
        """添加文档到知识库"""
        # 根据文件类型选择加载器
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")
        
        docs = loader.load()
        chunks = self.splitter.split_documents(docs)
        
        # 添加到向量数据库
        self.vectorstore.add_documents(chunks)
        return len(chunks)
    
    @property
    def doc_count(self) -> int:
        return self.vectorstore._collection.count()
```

### 7.4 对话接口：流式响应 + 多轮记忆

**`memory_store.py` — 会话记忆管理：**

```python
# memory_store.py
from langchain_core.messages import HumanMessage, AIMessage

class MemoryStore:
    """简单的内存会话存储"""
    
    def __init__(self, max_history=10):
        self.store = {}           # session_id → messages list
        self.max_history = max_history
    
    def get_history(self, session_id: str) -> list:
        return self.store.get(session_id, [])
    
    def save_message(self, session_id: str, human_msg: str, ai_msg: str):
        if session_id not in self.store:
            self.store[session_id] = []
        
        self.store[session_id].extend([
            HumanMessage(content=human_msg),
            AIMessage(content=ai_msg),
        ])
        
        # 保留最近 N 轮（防止记忆过长）
        if len(self.store[session_id]) > self.max_history * 2:
            self.store[session_id] = self.store[session_id][-self.max_history * 2:]
```

**`chains.py` — RAG + 记忆链：**

```python
# chains.py
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import config

def create_rag_chain(vectorstore, chat_history: list):
    """创建带记忆的 RAG 链"""
    llm = ChatDeepSeek(
        model=config.LLM_MODEL,
        streaming=True,
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    def format_docs(docs):
        return "\n\n---\n\n".join(
            f"【{doc.metadata.get('source', '?')}】\n{doc.page_content}"
            for doc in docs
        )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个智能知识库助手。请基于参考文档回答问题。
如果文档中找不到答案，请坦诚告知。回答时引用文档来源。

参考文档：
{context}"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    
    chain = (
        {
            "context": (lambda x: x["input"]) | retriever | format_docs,
            "chat_history": lambda x: chat_history,
            "input": lambda x: x["input"],
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain
```

**测试 API：**

```bash
# 启动服务
uvicorn main:app --reload

# 上传文档
curl -X POST http://localhost:8000/upload \
  -F "file=@./my_notes/python_guide.md"
# {"message": "✅ 已添加 python_guide.md，生成 42 个向量块"}

# 对话（流式）
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是装饰器？", "session_id": "user_001"}'
# 根据文档，装饰器是一种...（流式逐字返回）
```

### 7.5 部署与优化：生产环境注意事项

```
生产环境 Checklist：

✅ 基础
  □ API Key 用环境变量管理，不硬编码
  □ 添加 CORS 中间件（前端跨域）
  □ 添加 API 认证（Bearer Token / API Key）

✅ 性能
  □ 向量数据库用持久化存储（不要每次重启都重建）
  □ Embedding 调用做缓存（同一文本不重复计算）
  □ 用异步（ainvoke/astream）处理并发请求
  □ 大文件上传用后台任务（BackgroundTask）

✅ 可靠性
  □ LLM 调用加 retry 和 timeout
  □ 添加结构化日志（记录每次问答的输入输出）
  □ 集成 LangSmith 做链路追踪（下一章介绍）

✅ 成本
  □ 监控 token 使用量
  □ 设置每用户/每日的调用限额
  □ 长对话用摘要记忆而非 Buffer 记忆
```

```python
# 示例：添加超时和重试
from langchain_deepseek import ChatDeepSeek

llm = ChatDeepSeek(
    model="deepseek-chat",
    request_timeout=30,       # 30 秒超时
    max_retries=3,            # 最多重试 3 次
)
```

**第 7 章核心知识回顾：**

| 模块 | 技术 | 对应章节 |
|:---|:---|:---|
| 文档上传+向量化 | DocumentLoader + Chroma | 第 5 章 RAG |
| RAG 问答链 | Retriever + Prompt + LLM | 第 5 章 RAG |
| 多轮记忆 | MessageHistory | 第 4 章 Memory |
| 流式响应 | astream + StreamingResponse | 第 3 章 Chain |
| API 服务 | FastAPI | — |

---

## 8. LangChain 生态与进阶

LangChain 不只是一个框架——它背后有一整套生态工具。这一章介绍最重要的几个，以及和其他框架的对比，帮你规划后续的学习方向。

### 8.1 LangSmith：追踪与调试你的 LLM 应用

LLM 应用最头疼的是**调试**——链条长了之后，不知道是哪一步出了问题。LangSmith 是 LangChain 官方的可观测平台：

```python
# 开启 LangSmith 追踪（只需设置环境变量）
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-langsmith-api-key"
os.environ["LANGCHAIN_PROJECT"] = "my-project"

# 之后所有 LangChain 调用都会自动记录到 LangSmith
chain = prompt | llm | parser
result = chain.invoke({"question": "什么是 RAG？"})
# 在 smith.langchain.com 可以看到完整的调用链路
```

**LangSmith 能看到什么：**

| 功能 | 说明 |
|:---|:---|
| **链路追踪** | 每一步的输入、输出、耗时、token 用量 |
| **错误定位** | 哪一步报错了、错误信息是什么 |
| **Prompt 调试** | 查看实际发送给 LLM 的完整 prompt |
| **性能分析** | 每步耗时占比、token 成本统计 |
| **评估测试** | 批量跑测试用例，对比不同 prompt 的效果 |

> 💡 **强烈推荐在开发阶段就接入 LangSmith**——当你的 RAG 回答不准确时，可以看到检索到了哪些文档块、prompt 拼装成什么样子、LLM 是基于什么信息回答的。

### 8.2 LangGraph：Agent 的底层运行时

LangGraph 在 v1.0 中的定位发生了重大变化——它不再只是“可选扩展”，而是 **`create_agent` 的底层运行时**。当你需要更细粒度的控制（多分支、条件循环、人机协作），LangGraph 让你用图（Graph）来定义 Agent 的状态流转：

```python
# pip install langgraph
from langgraph.graph import StateGraph, END
from typing import TypedDict

# ── 定义状态 ──
class AgentState(TypedDict):
    question: str
    search_results: str
    answer: str
    needs_more_info: bool

# ── 定义节点（每个节点是一个处理函数） ──
def search_node(state):
    """搜索知识库"""
    results = retriever.invoke(state["question"])
    return {"search_results": format_docs(results)}

def answer_node(state):
    """基于搜索结果回答"""
    answer = llm.invoke(f"根据以下内容回答：{state['search_results']}\n\n问题：{state['question']}")
    return {"answer": answer.content, "needs_more_info": "不确定" in answer.content}

def refine_node(state):
    """如果答案不确定，进一步搜索"""
    results = retriever.invoke(state["question"] + " 更多细节")
    refined = llm.invoke(f"补充信息：{format_docs(results)}\n原始回答：{state['answer']}")
    return {"answer": refined.content}

# ── 构建图 ──
graph = StateGraph(AgentState)
graph.add_node("search", search_node)
graph.add_node("answer", answer_node)
graph.add_node("refine", refine_node)

graph.set_entry_point("search")
graph.add_edge("search", "answer")

# 条件分支：如果需要更多信息 → refine，否则 → 结束
graph.add_conditional_edges(
    "answer",
    lambda state: "refine" if state["needs_more_info"] else END,
)
graph.add_edge("refine", END)

app = graph.compile()
result = app.invoke({"question": "LangGraph 和 LangChain 有什么区别？"})
```

```
LangGraph 的执行路径：

  search → answer → (需要更多信息?) → refine → END
                   ↘ (已经够了)   → END
```

### 8.3 与其他框架对比：LlamaIndex、Semantic Kernel

| 维度 | LangChain | LlamaIndex | Semantic Kernel |
|:---|:---|:---|:---|
| **定位** | 通用 LLM 应用框架 | RAG 专精框架 | 微软的 AI 编排 SDK |
| **核心优势** | 组件丰富、生态大 | RAG 效果更优 | 与 Azure 深度整合 |
| **编排方式** | LCEL 管道 | Query Engine | Plugin + Planner |
| **Agent 支持** | ✅ 完善 | ✅ 基础 | ✅ 完善 |
| **语言** | Python, JS | Python, JS | Python, C#, Java |
| **学习曲线** | 中等 | 较低 | 中等 |
| **适用场景** | 全类型 LLM 应用 | RAG 为主的应用 | 微软技术栈项目 |

**怎么选？**

- **大部分场景** → LangChain（生态最大、社区最活跃、教程最多）
- **纯 RAG 应用** → LlamaIndex（检索策略更丰富、开箱即用效果好）
- **微软/Azure 技术栈** → Semantic Kernel

> 💡 **它们不是互斥的**——很多项目同时使用 LangChain 做 Agent 编排 + LlamaIndex 做 RAG 引擎。

### 8.4 持续学习路线图

```
你现在的位置（读完本教程）：

✅ 已掌握                              📚 下一步
──────────────────────────────────────────────────
Model I/O（prompt + 输出解析）    →  Prompt Engineering 进阶
with_structured_output       →  自定义 Tool Calling Schema
Chain（LCEL 编排）                →  LangGraph 状态机
Memory（对话记忆）                →  持久化存储（PostgreSQL/Redis）
RAG（检索增强生成）               →  高级 RAG（重排序/混合检索/知识图谱）
Agent（create_agent）             →  多 Agent 协作（CrewAI/AutoGen）
Middleware（中间件）              →  自定义中间件开发
```

**推荐的学习资源：**

| 资源 | 链接 | 说明 |
|:---|:---|:---|
| LangChain 官方文档 | python.langchain.com | 最权威的参考 |
| LangChain Cookbook | github.com/langchain-ai/langchain | 官方示例集 |
| LangSmith | smith.langchain.com | 调试和评估平台 |
| LangGraph 文档 | langchain-ai.github.io/langgraph | 状态机 Agent |
| DeepLearning.AI 课程 | deeplearning.ai | 吴恩达的 LangChain 短课 |

**最后的建议：**

> 💡 **学框架最好的方式是做项目**。从你自己的需求出发——给你的笔记做一个智能搜索、给你的代码仓库做一个文档问答、给你的团队做一个内部知识助手。遇到问题再回来查文档，这比从头到尾读文档有效 10 倍。

> ⚠️ **从旧版迁移？** 如果你的项目还在使用 v0.2/v0.3 的 API（如 `create_tool_calling_agent`、`AgentExecutor`、`ConversationBufferMemory` 等），可以先安装 `pip install langchain-classic` 维持运行，然后逐步迁移到 v1.x 的 `create_agent` + LangGraph 架构。官方提供了详细的迁移指南。

