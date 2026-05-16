# 构建个人 AI 助理

> 从零搭建一个真正有用的个人 AI 助理——日程管理、邮件摘要、知识库问答、多工具编排，用 LangGraph + Function Calling 构建一个"记得住你、帮得了忙"的全能 Agent。

---

## 1. 个人 AI 助理的产品定义与架构设计

每天早上你醒来，面对的是：38 封未读邮件、5 个待办事项、3 个日历冲突、散落在 Notion / Obsidian / 微信收藏里的 N 条碎片信息。你需要一个助理帮你处理这些——但 Siri 连"帮我看看今天有什么重要邮件"都做不好。所以，我们自己造一个。

### 1.1 为什么要自己构建 AI 助理

先看看市面上的"AI 助理"都在什么段位：

```
现有 AI 助理的能力边界：

  Siri / 小爱同学
  ═══════════════════════════════════════
  ✅ 设闹钟、打电话、查天气
  ❌ 不能读邮件、不能总结文档、不能跨应用操作
  ❌ 不支持自定义工具、没有记忆

  ChatGPT / Claude
  ═══════════════════════════════════════
  ✅ 强大的语言理解和生成
  ✅ 支持简单的 Function Calling
  ❌ 不能连你的日历、邮箱、知识库
  ❌ 跨会话记忆有限（ChatGPT 的 Memory 只是简单存 fact）
  ❌ 不能主动推送（你不问它不说）

  Dify / Coze / GPTs
  ═══════════════════════════════════════
  ✅ 可视化搭建、支持工具接入
  ⚠️ 定制深度有限（受平台约束）
  ❌ 数据在别人的服务器上（隐私风险）
  ❌ 复杂编排能力不足（多工具链式调用）

  自建 AI 助理 ⭐
  ═══════════════════════════════════════
  ✅ 完全自定义工具和工作流
  ✅ 数据 100% 本地（笔记、邮件、日历）
  ✅ 深度集成个人工具链（Obsidian / Gmail / GitHub）
  ✅ 记忆系统可按需设计
  ✅ 可以主动推送（定时任务 + 事件监听）
```

| 维度 | Siri | ChatGPT | Coze/Dify | 自建方案 |
|:---|:---|:---|:---|:---|
| **理解能力** | 弱 | 强 | 强 | 强 |
| **工具接入** | 仅系统内 | 有限 | 中等 | 无限制 |
| **数据隐私** | Apple 服务器 | OpenAI 服务器 | 第三方平台 | 100% 本地 |
| **个性化** | 几乎没有 | Memory（简单） | 变量/知识库 | 完全自定义 |
| **主动推送** | 有限 | 不支持 | Webhook | 完全自定义 |
| **开发成本** | 0 | 0 | 低 | 中等 |

自建的核心优势可以总结为三个词：**可控、可连、可主动**。

```
自建 AI 助理的三大核心优势：

  ① 可控 ─── 数据和行为完全由你决定
     │         邮件内容不会发到第三方服务器
     │         LLM 选择自由（DeepSeek / GPT / 本地模型）
     │
  ② 可连 ─── 深度接入你的私有工具链
     │         Obsidian 笔记、Gmail 邮箱、Google Calendar
     │         GitHub Issues、Jira、数据库……
     │
  ③ 可主动 ── 不等你问，主动为你工作
               每天早上 8 点推送今日日程摘要
               重要邮件到达时立即通知
               周五下午自动生成周报初稿
```

> 💡 **"自建"不意味着"从零写 LLM"**——我们只需要编排好调用链。LLM 用现成的（DeepSeek / GPT-4o），工具 API 也是现成的（Google Calendar / Gmail），我们要做的是：**用 LangGraph 把它们编排成一个能理解你需求、自动选择工具、记住你偏好的 Agent**。

### 1.2 MVP 功能清单：从"能用"到"好用"

一口气想做"全能助理"一定会烂尾。我们分三个阶段来规划：

```
三阶段功能规划：

  Phase 1：MVP（1-2 周）
  ═══════════════════════════════════════
  ✅ 自然语言对话（核心 Agent 循环）
  ✅ 日程查询与创建（Google Calendar）
  ✅ 邮件摘要（Gmail 最近 N 封）
  ✅ 知识库问答（Obsidian 笔记 RAG）
  ✅ CLI 交互界面
  
  Phase 2：好用（3-4 周）
  ═══════════════════════════════════════
  ✅ 多工具链式调用（"查日程 → 发现冲突 → 建议调整"）
  ✅ 用户画像与偏好记忆
  ✅ 跨会话记忆（记住你上次聊了什么）
  ✅ Web UI 界面
  ✅ 定时任务（晨间日报、周报）
  
  Phase 3：智能化（5-8 周）
  ═══════════════════════════════════════
  ✅ 主动推送（重要邮件通知、日程提醒）
  ✅ 语音交互（Whisper + TTS）
  ✅ 微信 / Telegram Bot
  ✅ 多 Agent 协作
  ✅ 与 GitHub / Jira 集成
```

本文覆盖 Phase 1 + Phase 2 的完整实现，Phase 3 在第 10 章做展望。

每个功能对应的技术实现一览：

| 功能 | 工具/API | LLM 角色 | 本章 |
|:---|:---|:---|:---|
| 日程管理 | Google Calendar API | 自然语言 → 结构化参数 | 第 3 章 |
| 邮件摘要 | Gmail API / IMAP | 批量邮件 → 摘要 + 分类 | 第 4 章 |
| 知识库问答 | ChromaDB + Embedding | RAG 检索 + 生成 | 第 5 章 |
| 工具编排 | Function Calling | 意图识别 + 工具调用 | 第 6 章 |
| 记忆系统 | SQLite + 向量库 | 用户画像抽取 | 第 7 章 |
| 定时任务 | APScheduler | 自动生成日报/周报 | 第 9 章 |

> 💡 **MVP 的核心标准：你愿不愿意每天用它**。如果你做了一个"能查日程但要手动输入 JSON 参数"的助理，那不叫 MVP，叫 API Wrapper。真正的 MVP 是你说"我明天有什么安排"，它给你一个清晰的列表——**自然语言进，结构化出**。
### 1.3 系统架构：四层模型与数据流全景

整个 AI 助理由四层构成，每层职责清晰：

```
个人 AI 助理的四层架构：

  ┌───────────────────────────────────────────────────┐
  │                 接口层 (Interface)                  │
  │  CLI / Web UI / Telegram Bot / 语音 / 微信          │
  └─────────────────────┬─────────────────────────────┘
                        │ 用户输入 / 响应输出
                        ▼
  ┌───────────────────────────────────────────────────┐
  │              Agent 核心层 (Brain)                   │
  │                                                    │
  │  ┌──────────────────────────────────────────────┐  │
  │  │  LangGraph 状态图                             │  │
  │  │  ┌────────┐   ┌─────────┐   ┌────────────┐  │  │
  │  │  │意图路由 │──▶│工具调用  │──▶│响应生成     │  │  │
  │  │  └────────┘   └─────────┘   └────────────┘  │  │
  │  └──────────────────────────────────────────────┘  │
  │                                                    │
  │  LLM: DeepSeek V3 / GPT-4o / 本地 Qwen             │
  └────────┬──────────────────────┬────────────────────┘
           │                      │
     ┌─────▼──────┐        ┌─────▼──────┐
     │  工具层     │        │  记忆层     │
     │ (Tools)     │        │ (Memory)    │
     ├─────────────┤        ├─────────────┤
     │ 📅 日历     │        │ 🧠 短期记忆 │
     │ 📧 邮件     │        │   (对话历史) │
     │ 📚 知识库   │        │ 💾 长期记忆 │
     │ 🔍 搜索     │        │   (用户画像) │
     │ 📝 笔记     │        │ 🗄️ 向量库   │
     └─────────────┘        └─────────────┘
```

技术选型全景：

| 层级 | 组件 | 推荐技术 | 备选方案 |
|:---|:---|:---|:---|
| **接口层** | CLI | Rich + Typer | Click |
| | Web UI | Gradio | Streamlit / React |
| | Bot | python-telegram-bot | itchat（微信） |
| **核心层** | Agent 框架 | LangGraph | LangChain AgentExecutor |
| | LLM | DeepSeek V3 | GPT-4o / Qwen |
| | Function Calling | OpenAI 兼容格式 | 手写 ReAct |
| **工具层** | 日历 | Google Calendar API | CalDAV |
| | 邮件 | Gmail API | IMAP |
| | 知识库 | ChromaDB + BGE | pgvector |
| **记忆层** | 短期记忆 | LangGraph Checkpointer | Redis |
| | 长期记忆 | SQLite + 向量检索 | PostgreSQL |
| | 用户画像 | LLM 抽取 + JSON 存储 | Mem0 |

```
一次完整的请求数据流：

  用户："我明天下午有空吗？帮我约个牙医"
    │
    ▼ 接口层
  解析用户输入，传入 Agent
    │
    ▼ Agent 核心层
  ① 意图识别："查日程" + "创建事件"（链式调用）
  ② 检索记忆："用户偏好下午 2 点后的时间段"
    │
    ▼ 工具层
  ③ 调用 Google Calendar → 查明天下午日程
  ④ 找到空闲时段：14:00-17:00
  ⑤ 创建事件："牙医预约" 15:00-16:00
    │
    ▼ Agent 核心层
  ⑥ 组合结果，生成自然语言回复
  ⑦ 更新记忆：记录"用户有牙医预约"
    │
    ▼ 接口层
  "你明天下午 2 点到 5 点都空。我帮你在 3 点
   预约了牙医，已添加到日历 📅"
```

> 💡 **核心层和工具层解耦**是关键设计——新增一个工具（比如"查快递"）只需要：① 写一个工具函数，② 注册到 Agent 的工具列表。不需要改核心层的任何代码。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **自建优势** | 可控（数据本地）、可连（私有工具链）、可主动（定时推送） |
| **三阶段规划** | MVP（对话+3 工具）→ 好用（记忆+定时）→ 智能化（多 Agent+主动推送） |
| **四层架构** | 接口层 → Agent 核心层 → 工具层 + 记忆层 |
| **解耦设计** | 新增工具只需写函数+注册，不改核心层 |
| **技术选型** | LangGraph + DeepSeek V3 + Google APIs + ChromaDB + SQLite |

---

## 2. Agent 核心：LangGraph 状态图与对话管理

Agent 核心层是整个助理的"大脑"——接收用户输入，判断该做什么（直接回答？调工具？追问？），执行动作，生成响应。我们用 LangGraph 的状态图来实现这个循环。

### 2.1 Agent 主循环：从输入到响应的状态图

一个个人 AI 助理的核心循环比"问答机器人"复杂得多——它需要：判断意图、选择工具、执行工具、根据结果二次推理、更新记忆。用 LangGraph 的状态图来表达：

```
Agent 主循环状态图：

  START
    │
    ▼
  ┌──────────────┐
  │  load_memory │ ← 加载用户画像 + 历史记忆
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │   chatbot    │ ← LLM 推理（带 function calling）
  └──────┬───────┘
         │
         ▼
  ┌──────────────────┐
  │  route_response  │ ← 检查 LLM 输出
  │                  │
  │  有 tool_calls?  │
  │  ├── YES ────────┼──▶ tools 节点
  │  └── NO  ────────┼──▶ save_memory → END
  └──────────────────┘
         │ YES
         ▼
  ┌──────────────┐
  │    tools     │ ← 执行工具调用
  └──────┬───────┘
         │
         └──▶ 回到 chatbot（LLM 看到工具结果，继续推理）
```

**核心代码实现：**

```python
"""个人 AI 助理 Agent 核心"""
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

# 导入我们后面会实现的工具
from tools.calendar_tools import query_calendar, create_event
from tools.email_tools import get_recent_emails, summarize_emails
from tools.knowledge_tools import search_knowledge_base

# 注册所有工具
ALL_TOOLS = [
    query_calendar,
    create_event,
    get_recent_emails,
    summarize_emails,
    search_knowledge_base,
]

# 初始化 LLM（绑定工具）
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    temperature=0.3,
).bind_tools(ALL_TOOLS)

SYSTEM_PROMPT = """你是用户的个人 AI 助理。你的职责是：
1. 管理用户日程（查询、创建日历事件）
2. 处理邮件（摘要、分类、回复建议）
3. 回答用户笔记/知识库中的问题
4. 记住用户的偏好和习惯

规则：
- 优先使用工具获取真实数据，不要编造
- 时间相关问题必须调用日历工具
- 邮件相关问题必须调用邮件工具
- 知识/笔记问题调用知识库搜索
- 闲聊或通用问题直接回答，不调工具
"""

# Agent 核心节点
async def chatbot(state: AgentState) -> dict:
    """LLM 推理节点"""
    messages = state["messages"]
    
    # 注入 System Prompt + 用户画像
    system = SYSTEM_PROMPT
    profile = state.get("user_profile", "")
    if profile:
        system += f"\n\n用户信息：\n{profile}"
    
    full_messages = [SystemMessage(content=system)] + messages
    response = await llm.ainvoke(full_messages)
    return {"messages": [response]}

# 路由函数
def route_response(state: AgentState) -> str:
    """判断 LLM 是否要调用工具"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "save_memory"

# 组装状态图
def build_agent():
    graph = StateGraph(AgentState)
    
    graph.add_node("load_memory", load_memory)
    graph.add_node("chatbot", chatbot)
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    graph.add_node("save_memory", save_memory)
    
    graph.add_edge(START, "load_memory")
    graph.add_edge("load_memory", "chatbot")
    graph.add_conditional_edges("chatbot", route_response)
    graph.add_edge("tools", "chatbot")  # 工具执行后回到 LLM
    graph.add_edge("save_memory", END)
    
    # SQLite 持久化（跨会话保存状态）
    checkpointer = AsyncSqliteSaver.from_conn_string("assistant.db")
    return graph.compile(checkpointer=checkpointer)
```

```
关键设计：tools → chatbot 的循环

  用户："帮我查一下明天的日程，然后取消下午 3 点的会"
  
  第 1 轮 LLM → tool_calls: [query_calendar(date="明天")]
  tools 执行 → 返回日程列表
  
  第 2 轮 LLM → 看到日程列表，找到 3 点的会
             → tool_calls: [delete_event(event_id="xxx")]
  tools 执行 → 返回 "已取消"
  
  第 3 轮 LLM → 没有 tool_calls
             → 生成响应："已查到你明天的日程，3 点的 XX 会议已取消 ✅"
  
  这就是 "ReAct 循环"：推理 → 行动 → 观察 → 推理 → ...
```

> 💡 **`ToolNode` 是 LangGraph 的内置工具执行节点**——它自动解析 `tool_calls`、调用对应函数、把结果包装成 `ToolMessage` 返回。你不需要手写任何工具调度代码。

### 2.2 State 设计：消息、用户画像与工具结果

LangGraph 的 State 是 Agent 的"工作记忆"——在整个请求处理过程中，所有节点共享、读写的数据结构。

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """Agent 状态定义"""
    
    # ① 对话消息（核心）
    # add_messages 自动处理追加和删除
    messages: Annotated[list, add_messages]
    
    # ② 用户画像（从记忆层加载）
    user_profile: str  # "姓名: 张三，职业: 后端开发，偏好: Python"
    
    # ③ 当前会话 ID（用于区分多用户）
    user_id: str
    
    # ④ 本轮对话是否需要保存新记忆
    should_save_memory: bool
```

```
State 中各字段的生命周期：

  messages
  ═══════════════════════════════════════
  来源：用户输入 + LLM 回复 + 工具结果
  生命周期：被 Checkpointer 持久化到 SQLite
  由谁写入：chatbot 节点、tools 节点
  由谁读取：所有节点

  user_profile
  ═══════════════════════════════════════
  来源：load_memory 节点从长期记忆中加载
  内容示例：
    "姓名: 张三
     职业: 后端开发
     技术栈: Python, FastAPI, PostgreSQL
     偏好: 喜欢简洁的代码风格
     常用工具: VS Code, Obsidian"
  由谁写入：load_memory、save_memory
  由谁读取：chatbot 节点（注入到 System Prompt）
```

**记忆加载与保存节点：**

```python
import json
from pathlib import Path

MEMORY_DIR = Path("./memory")

async def load_memory(state: AgentState) -> dict:
    """加载用户画像（从本地 JSON 文件）"""
    user_id = state.get("user_id", "default")
    profile_path = MEMORY_DIR / f"{user_id}_profile.json"
    
    if profile_path.exists():
        profile = json.loads(profile_path.read_text())
        return {"user_profile": profile.get("summary", "")}
    
    return {"user_profile": ""}

async def save_memory(state: AgentState) -> dict:
    """保存对话中发现的新信息到用户画像"""
    # 这里简化处理，第 7 章会实现完整的记忆抽取
    return {}
```

> 💡 **`add_messages` 的妙处**：它不是简单的 list.append，而是智能合并——支持 `RemoveMessage`（删除特定消息）、自动去重（相同 ID 的消息只保留最新版本）。这让 LangGraph 的消息管理比手动操作 list 可靠得多。
### 2.3 意图路由：直接回答 / 工具调用 / 追问澄清

LLM 的 Function Calling 已经帮我们做了大部分意图路由——它会自动判断是否需要调用工具。但有些边界情况需要我们额外处理：

```
意图路由的三种分支：

  用户输入
    │
    ▼ LLM 推理
  ┌──────────────────────────────────────┐
  │                                      │
  │  分支 1：直接回答                     │
  │  ────────────────────────            │
  │  "你好" → "你好！有什么需要帮忙的？"     │
  │  "Python 的 GIL 是什么" → 直接解释     │
  │  → 没有 tool_calls → save_memory → END│
  │                                      │
  │  分支 2：工具调用                     │
  │  ────────────────────────            │
  │  "明天有什么安排" → query_calendar()   │
  │  "帮我看看邮件" → get_recent_emails()  │
  │  → 有 tool_calls → tools → chatbot    │
  │                                      │
  │  分支 3：追问澄清                     │
  │  ────────────────────────            │
  │  "帮我发邮件" → "请问发给谁？内容是？"  │
  │  "创建日程" → "请告诉我时间和主题"      │
  │  → 没有 tool_calls（缺少必要参数）     │
  │  → 直接返回追问回复 → END              │
  └──────────────────────────────────────┘
```

这三个分支不需要我们写 if-else 路由逻辑——**全部由 LLM 的 Function Calling 自动决策**。关键是 System Prompt 要写好：

```python
# System Prompt 中的路由指令（已包含在 SYSTEM_PROMPT 中）
"""
规则：
- 时间相关问题必须调用日历工具 → LLM 自动路由到分支 2
- 闲聊或通用问题直接回答 → LLM 自动路由到分支 1
- 参数不足时追问用户 → LLM 自动路由到分支 3
"""
```

**完整运行示例：**

```python
async def main():
    agent = build_agent()
    
    # 配置（thread_id 用于标识会话，user_id 标识用户）
    config = {
        "configurable": {
            "thread_id": "session_001",
            "user_id": "zhangsan",
        }
    }
    
    # 第 1 轮：闲聊（直接回答）
    result = await agent.ainvoke(
        {"messages": [("user", "你好呀")]},
        config=config,
    )
    print(result["messages"][-1].content)
    # → "你好！我是你的 AI 助理，可以帮你管理日程、查看邮件、检索笔记。有什么需要？"
    
    # 第 2 轮：查日程（工具调用）
    result = await agent.ainvoke(
        {"messages": [("user", "明天有什么安排？")]},
        config=config,
    )
    print(result["messages"][-1].content)
    # → "你明天有 3 个安排：
    #    09:00 团队站会
    #    14:00 产品评审
    #    16:00 和客户开会"
    
    # 第 3 轮：追问（参数不足）
    result = await agent.ainvoke(
        {"messages": [("user", "帮我加个日程")]},
        config=config,
    )
    print(result["messages"][-1].content)
    # → "好的，请告诉我：1. 什么时间？ 2. 日程主题是什么？"

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

> 💡 **为什么不手写意图分类器？** 因为 Function Calling 本质上就是一个"带结构化输出的意图分类器"。LLM 看到工具列表后，会自动判断哪个工具匹配用户意图。手写规则或训练分类器都不如直接用 Function Calling 灵活——新增工具不用改路由代码。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **状态图** | load_memory → chatbot → route → tools/save_memory 的循环 |
| **ReAct 循环** | 推理→行动→观察→推理，tools 执行后回到 chatbot 继续推理 |
| **AgentState** | messages + user_profile + user_id，共享的工作记忆 |
| **ToolNode** | LangGraph 内置的工具执行器，自动解析和调用 |
| **意图路由** | 完全依赖 Function Calling 自动决策，不写 if-else |
| **Checkpointer** | SQLite 持久化，自动保存/恢复会话状态 |

---

## 3. 工具层实现（一）：日程管理与提醒

日程管理是个人助理的第一个"杀手级功能"——每天都要用。你对助理说"我明天下午有什么安排"，它查 Google Calendar 后给你一个清晰的列表；你说"帮我在周五下午 3 点加个产品评审"，它自动创建事件。这就是 **自然语言 → API 调用** 的核心场景。

### 3.1 日历 API 集成：Google Calendar 与 CalDAV

```
两种日历接入方案：

  Google Calendar API ⭐ 推荐
  ═══════════════════════════════════════
  • 官方 Python SDK（google-api-python-client）
  • OAuth 2.0 认证（首次需要浏览器授权）
  • 功能完整：CRUD、搜索、提醒、重复事件
  • 免费额度：每天 100 万次调用
  
  CalDAV（通用协议）
  ═══════════════════════════════════════
  • 标准协议，支持所有日历系统（Apple / Nextcloud）
  • Python 库：caldav
  • 适合不用 Google 的用户
  • 功能较基础，需要自己解析 iCalendar 格式
```

**Google Calendar 工具实现：**

```python
"""日历工具：用 LangChain @tool 装饰器注册"""
from langchain_core.tools import tool
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json

def _get_calendar_service():
    """获取 Google Calendar API 服务"""
    creds = Credentials.from_authorized_user_file(
        "credentials/token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    return build("calendar", "v3", credentials=creds)

@tool
def query_calendar(
    start_date: str,
    end_date: str | None = None,
) -> str:
    """查询指定日期范围的日程安排。

    Args:
        start_date: 开始日期，格式 YYYY-MM-DD，如 "2026-04-11"
        end_date: 结束日期（可选），不传则只查当天
    """
    service = _get_calendar_service()
    
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date) if end_date else start
    end = end.replace(hour=23, minute=59, second=59)
    
    events_result = service.events().list(
        calendarId="primary",
        timeMin=start.isoformat() + "Z",
        timeMax=end.isoformat() + "Z",
        singleEvents=True,
        orderBy="startTime",
        maxResults=20,
    ).execute()
    
    events = events_result.get("items", [])
    
    if not events:
        return f"{start_date} 没有安排，全天空闲。"
    
    result = []
    for event in events:
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        summary = event.get("summary", "（无标题）")
        result.append(f"• {start_time[:16]} - {summary}")
    
    return f"找到 {len(events)} 个日程：\n" + "\n".join(result)

@tool
def create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
) -> str:
    """在日历中创建新事件。

    Args:
        summary: 事件标题，如 "产品评审会"
        start_time: 开始时间，格式 YYYY-MM-DDTHH:MM:SS，如 "2026-04-11T15:00:00"
        end_time: 结束时间，格式同上
        description: 事件描述（可选）
    """
    service = _get_calendar_service()
    
    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_time, "timeZone": "Asia/Shanghai"},
        "end": {"dateTime": end_time, "timeZone": "Asia/Shanghai"},
    }
    
    created = service.events().insert(
        calendarId="primary", body=event
    ).execute()
    
    return f"✅ 已创建日程：{summary}（{start_time[:16]} ~ {end_time[:16]}）"
```

| 关键设计 | 说明 |
|:---|:---|
| `@tool` 装饰器 | LangChain 自动生成 JSON Schema，LLM 能"看到"参数定义 |
| Docstring | 既是给开发者看的文档，也是给 LLM 看的工具说明 |
| 返回 str | 工具结果以文本形式返回 LLM，LLM 再组织成自然语言回复 |
| 时间格式 | 用 ISO 8601 标准格式，LLM 最容易正确生成 |

> 💡 **OAuth 2.0 首次授权**：第一次运行需要在浏览器中登录 Google 授权。授权后 token 保存在本地 `token.json`，后续调用直接使用。具体流程参考 [Google Calendar API Quickstart](https://developers.google.com/calendar/api/quickstart/python)。

### 3.2 自然语言日程解析：从口语到结构化事件

用户不会说"创建事件，start_time=2026-04-12T15:00:00"——他会说"**明天下午 3 点开产品会**"。把口语转成结构化 API 参数，是 Function Calling 的核心价值。

```
LLM 自动完成的解析过程：

  用户输入："后天下午 3 点到 4 点半开产品评审"
        │
        ▼ LLM 推理（Function Calling）
  
  自动解析结果：
  ═══════════════════════════════════════
  tool: create_event
  args:
    summary: "产品评审"
    start_time: "2026-04-13T15:00:00"    ← "后天下午 3 点"
    end_time:   "2026-04-13T16:30:00"    ← "4 点半"
    description: ""
  
  LLM 自动完成了：
  • "后天" → 当前日期 + 2 天
  • "下午 3 点" → 15:00:00
  • "4 点半" → 16:30:00
  • "产品评审" → summary 字段
```

但 LLM 解析时间有一个坑——**它不一定知道"今天"是几号**。解决办法是在 System Prompt 中注入当前时间：

```python
from datetime import datetime

def get_system_prompt() -> str:
    """动态生成 System Prompt（注入当前时间）"""
    now = datetime.now()
    time_context = (
        f"当前时间：{now.strftime('%Y-%m-%d %H:%M')}，"
        f"星期{['一','二','三','四','五','六','日'][now.weekday()]}。"
    )
    
    return f"""{SYSTEM_PROMPT}

{time_context}

处理日程时：
- "今天" = {now.strftime('%Y-%m-%d')}
- "明天" = {(now + timedelta(days=1)).strftime('%Y-%m-%d')}
- "后天" = {(now + timedelta(days=2)).strftime('%Y-%m-%d')}
- "这周五" = 本周五的日期
- 不确定的时间必须追问用户，不要猜测
"""
```

常见口语时间表达的解析测试：

| 用户说的 | LLM 应该解析为 | 注意点 |
|:---|:---|:---|
| "明天上午 10 点" | 2026-04-12T10:00:00 | ✅ 简单情况 |
| "下周三下午" | 2026-04-16T14:00:00 | ⚠️ "下午"没具体时间，默认 14:00 |
| "周末" | 需追问 | ❌ 周六还是周日？上午还是下午？ |
| "过两个小时" | 当前时间 + 2h | ⚠️ 需要知道当前时间 |
| "下个月初" | 需追问 | ❌ 1 号？还是第一个工作日？ |

> 💡 **不确定就追问，不要猜**：在 System Prompt 里明确写"不确定的时间必须追问用户"。LLM 猜错时间比问一句话的代价大得多——用户发现"帮我约在了错误的时间"会很愤怒。
### 3.3 智能提醒与冲突检测

创建日程时自动检测是否和现有日程冲突，是助理比手动操作更智能的体现。

```python
@tool
def create_event_smart(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
) -> str:
    """智能创建日历事件（自动检测冲突）。

    Args:
        summary: 事件标题
        start_time: 开始时间，格式 YYYY-MM-DDTHH:MM:SS
        end_time: 结束时间，格式同上
        description: 事件描述（可选）
    """
    service = _get_calendar_service()
    
    # 先检查该时间段是否有冲突
    existing = service.events().list(
        calendarId="primary",
        timeMin=start_time + "+08:00",
        timeMax=end_time + "+08:00",
        singleEvents=True,
    ).execute().get("items", [])
    
    if existing:
        conflicts = [e.get("summary", "无标题") for e in existing]
        return (
            f"⚠️ 时间冲突！{start_time[:16]} ~ {end_time[:16]} "
            f"已有日程：{', '.join(conflicts)}。\n"
            f"是否仍要创建？或者需要我建议其他时间段？"
        )
    
    # 无冲突，直接创建
    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_time, "timeZone": "Asia/Shanghai"},
        "end": {"dateTime": end_time, "timeZone": "Asia/Shanghai"},
        "reminders": {"useDefault": False, "overrides": [
            {"method": "popup", "minutes": 15},  # 提前 15 分钟弹窗
        ]},
    }
    
    service.events().insert(calendarId="primary", body=event).execute()
    return f"✅ 已创建日程：{summary}（{start_time[:16]} ~ {end_time[:16]}），已设置 15 分钟提前提醒。"
```

```
冲突检测的工作流：

  用户："帮我在明天 2:30 加个牙医预约"
    │
    ▼ LLM 调用 create_event_smart()
  
  检查 14:30-15:30 是否有事件
    │
    ├── 无冲突 → 创建事件 → "✅ 已创建"
    │
    └── 有冲突 → 返回冲突信息
                  │
                  ▼ LLM 看到冲突信息
                "⚠️ 那个时间有产品评审。
                 要不改到 4 点？或者我帮你挪产品评审？"
```

**定时提醒（晨间日报）：**

```python
"""定时任务：每天早上推送今日日程"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

async def morning_briefing():
    """晨间日报：今日日程 + 重要邮件摘要"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 查今日日程
    schedule = query_calendar.invoke({"start_date": today})
    
    # 组装日报
    briefing = f"🌅 早安！今天是 {today}\n\n📅 今日日程：\n{schedule}"
    
    # 通过配置的渠道推送（Telegram / 邮件 / 终端）
    await send_notification(briefing)

# 每天早上 8:00 执行
scheduler.add_job(
    morning_briefing,
    CronTrigger(hour=8, minute=0),
    id="morning_briefing",
)
scheduler.start()
```

> 💡 **APScheduler vs crontab**：APScheduler 是 Python 原生的定时任务库，和 Agent 代码在同一进程里，可以直接调用工具函数。crontab 则需要单独启动一个脚本。对于个人助理场景，APScheduler 更方便。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **`@tool` 装饰器** | 自动生成 JSON Schema，LLM 看 Docstring 理解工具用途 |
| **OAuth 2.0** | 首次浏览器授权，token 本地保存，后续自动刷新 |
| **时间注入** | System Prompt 动态注入当前日期，解决"今天是几号"的问题 |
| **冲突检测** | 创建事件前先查询同时段日程，有冲突返回建议 |
| **晨间日报** | APScheduler 定时触发，自动推送今日日程摘要 |

---

## 4. 工具层实现（二）：邮件摘要与智能回复

"帮我看看今天有什么重要邮件"——这句话如果能让 AI 助理执行，每天至少省你 15 分钟。邮件工具的核心价值是：**从几十封邮件中快速提取"需要你关注的 3-5 件事"**。

### 4.1 邮件接入：Gmail API 与 IMAP 方案对比

```
两种邮件接入方案：

  Gmail API ⭐ 推荐（用 Gmail 的话）
  ═══════════════════════════════════════
  • OAuth 2.0 认证
  • 支持搜索、标签、线程、草稿
  • 可以读邮件、发邮件、创建草稿
  • Python SDK：google-api-python-client
  
  IMAP（通用协议）
  ═══════════════════════════════════════
  • 标准协议，支持所有邮箱（QQ / 163 / 企业邮箱）
  • Python 内置：imaplib + email
  • 只能读取，功能有限
  • 需要开启 IMAP 访问和应用专用密码
```

**Gmail API 邮件获取工具：**

```python
"""邮件工具"""
from langchain_core.tools import tool
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
from email.mime.text import MIMEText

def _get_gmail_service():
    creds = Credentials.from_authorized_user_file(
        "credentials/gmail_token.json",
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
    )
    return build("gmail", "v1", credentials=creds)

@tool
def get_recent_emails(
    max_results: int = 10,
    query: str = "is:unread",
) -> str:
    """获取最近的邮件列表。

    Args:
        max_results: 返回的邮件数量，默认 10
        query: Gmail 搜索语法，默认只看未读。
               示例："is:unread"、"from:boss@company.com"、
               "subject:周报"、"newer_than:1d"
    """
    service = _get_gmail_service()
    
    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results,
    ).execute()
    
    messages = results.get("messages", [])
    if not messages:
        return "📭 没有找到符合条件的邮件。"
    
    email_list = []
    for msg_meta in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_meta["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        snippet = msg.get("snippet", "")[:100]
        
        email_list.append(
            f"• 发件人: {headers.get('From', '未知')}\n"
            f"  主题: {headers.get('Subject', '无主题')}\n"
            f"  预览: {snippet}..."
        )
    
    return f"找到 {len(messages)} 封邮件：\n\n" + "\n\n".join(email_list)
```

| 对比维度 | Gmail API | IMAP |
|:---|:---|:---|
| **认证方式** | OAuth 2.0 | 用户名+应用密码 |
| **搜索能力** | 强（Gmail 搜索语法） | 弱（IMAP SEARCH 命令） |
| **发邮件** | ✅ | ❌（需要 SMTP） |
| **创建草稿** | ✅ | ❌ |
| **适用邮箱** | 仅 Gmail | 所有邮箱 |

> 💡 **`format="metadata"` 而非 `format="full"`**：获取邮件列表时只要元数据（发件人、主题），不要正文。正文可能很大（HTML + 附件），获取列表时拉全文会很慢且浪费 Token。需要看正文时再单独获取。

### 4.2 邮件智能摘要：批量处理与优先级排序

拿到邮件列表后，核心价值是让 LLM **批量分析→分类→排序→生成摘要**。

```python
@tool
def summarize_emails(
    query: str = "is:unread newer_than:1d",
    max_results: int = 15,
) -> str:
    """智能分析并摘要邮件，按重要性分类。

    Args:
        query: Gmail 搜索语法，默认查最近 1 天的未读邮件
        max_results: 最多分析几封邮件
    """
    service = _get_gmail_service()
    
    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results,
    ).execute()
    
    messages = results.get("messages", [])
    if not messages:
        return "📭 没有符合条件的邮件。"
    
    # 获取每封邮件的关键信息（发件人 + 主题 + 预览）
    email_data = []
    for msg_meta in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_meta["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        email_data.append({
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "snippet": msg.get("snippet", "")[:200],
            "date": headers.get("Date", ""),
        })
    
    # 用 LLM 批量分析（这里返回原始数据，让 Agent 的 LLM 统一分析）
    formatted = "\n".join(
        f"[{i+1}] 发件人: {e['from']}\n"
        f"    主题: {e['subject']}\n"
        f"    预览: {e['snippet']}\n"
        for i, e in enumerate(email_data)
    )
    
    return (
        f"共 {len(email_data)} 封邮件，请分析并按重要性分类：\n\n"
        f"{formatted}\n\n"
        f"请按以下格式分类：\n"
        f"🔴 需要立即处理：...\n"
        f"🟡 需要关注：...\n"
        f"⚪ 可以忽略：..."
    )
```

```
邮件摘要的工作流：

  用户："帮我看看今天有什么重要邮件"
    │
    ▼ LLM 调用 summarize_emails(query="newer_than:1d")
    │
    ▼ 工具返回 15 封邮件的元数据
    │
    ▼ LLM 二次推理（分类 + 摘要）
    │
    ▼ 最终回复：
  
  "你今天有 15 封邮件，我帮你分类了：
  
   🔴 需要立即处理（2 封）：
   1. 老板发来的：Q2 OKR 截止明天，需要你提交
   2. HR 部门：请假审批需要你签字
   
   🟡 需要关注（3 封）：
   3. 产品经理：下周功能需求评审邀请
   4. GitHub：你的 PR 收到 Review 意见
   5. 客户反馈：某个 Bug 报告
   
   ⚪ 可以忽略（10 封）：
   营销推送、订阅通知等"
```

> 💡 **让 Agent LLM 做分类而非工具内部调 LLM**：工具只负责拿数据，分类和摘要交给 Agent 核心的 LLM。这样做有两个好处：① 工具保持纯粹（获取数据），② Agent 可以结合用户画像（比如"老板的邮件永远标为重要"）做更准确的分类。
### 4.3 回复草稿生成与安全边界

AI 帮你写回复是高阶功能——但**绝对不能自动发送**。安全边界要清晰。

```python
@tool
def draft_reply(
    email_subject: str,
    reply_intent: str,
    tone: str = "professional",
) -> str:
    """为指定邮件生成回复草稿（不会自动发送）。

    Args:
        email_subject: 要回复的邮件主题（用于查找原始邮件）
        reply_intent: 回复的大意，如 "同意方案B" "请求延期一周"
        tone: 语气风格，可选 professional / casual / formal
    """
    # 这里只生成草稿文本，交给 Agent LLM 组织
    return (
        f"请为以下邮件生成回复草稿：\n"
        f"原始主题：{email_subject}\n"
        f"回复意图：{reply_intent}\n"
        f"语气：{tone}\n\n"
        f"⚠️ 这只是草稿，需要用户确认后才会发送。"
    )
```

```
安全边界设计（铁律）：

  ┌──────────────────────────────────────┐
  │  ✅ AI 可以做的：                      │
  │  • 读取邮件列表和内容                   │
  │  • 分析和摘要邮件                       │
  │  • 生成回复草稿                         │
  │  • 标记邮件为已读/加星标                 │
  ├──────────────────────────────────────┤
  │  ❌ AI 绝不能自动做的：                  │
  │  • 发送邮件（必须用户确认）              │
  │  • 删除邮件                             │
  │  • 转发邮件给其他人                     │
  │  • 修改邮件过滤规则                     │
  ├──────────────────────────────────────┤
  │  🔒 隐私保护：                          │
  │  • 邮件内容只在本地处理                  │
  │  • 不把邮件正文存入长期记忆              │
  │  • 调用 LLM 时脱敏（去掉敏感附件信息）   │
  └──────────────────────────────────────┘
```

实现"用户确认后再发送"的交互流程：

```python
# Agent 生成草稿后的对话
"""
AI: 我为你生成了回复草稿：

"张总好，
 方案 B 我们团队评估后没有问题，可以按计划推进。
 下周一我会安排团队开始开发。
 祝好，李明"

需要我发送这封回复吗？你也可以修改后再发送。

用户: 发送吧

AI: ✅ 回复已发送给 张总 (zhang@company.com)
"""
```

> 💡 **为什么"可以帮你写但不能帮你发"是铁律**？因为一封错误的自动邮件可能造成不可挽回的后果（发给错误的人、不当的措辞、泄露敏感信息）。草稿是安全的——最坏情况就是用户看一眼说"不对"然后改掉。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Gmail API** | OAuth 认证，支持搜索/读取/草稿/发送，推荐用 metadata 格式 |
| **IMAP** | 通用协议，适配 QQ/163/企业邮箱，只能读不能发 |
| **摘要策略** | 工具取数据，Agent LLM 做分类摘要（可结合用户画像） |
| **三级分类** | 🔴 立即处理 / 🟡 需要关注 / ⚪ 可以忽略 |
| **安全边界** | 可读可写草稿，但绝不自动发送/删除/转发 |

---

## 5. 工具层实现（三）：个人知识库问答

你的 Obsidian 笔记里有 300 篇文章、读书笔记、会议记录，但你从来记不住"之前那个 Redis 持久化的结论写在哪"。知识库问答就是解决这个问题——让 AI 帮你"翻笔记"。

### 5.1 文档导入与解析：Markdown / PDF / 网页

```
支持的文档格式和解析策略：

  Markdown（Obsidian / 本地笔记）⭐ 主力
  ═══════════════════════════════════════
  • 按标题层级分块（## 为分割点）
  • 保留标题作为 metadata（检索时知道"来自哪个章节"）
  • 每块 300-500 字，太短语义不完整，太长检索粒度粗

  PDF（技术文档 / 论文）
  ═══════════════════════════════════════
  • 用 PyMuPDF 或 pdfplumber 提取文本
  • 按段落分块，保留页码信息
  • 表格和公式可能提取效果差

  网页（收藏的技术文章）
  ═══════════════════════════════════════
  • 用 trafilatura / BeautifulSoup 提取正文
  • 去除导航栏、广告等噪声
  • 保留 URL 作为 metadata
```

**Obsidian 笔记加载与分块：**

```python
"""知识库文档加载与分块"""
from pathlib import Path
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader

def load_obsidian_vault(vault_path: str) -> list[dict]:
    """加载 Obsidian vault 中的所有 Markdown 文件"""
    
    # 按 Markdown 标题层级分块
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "title"),
            ("##", "section"),
            ("###", "subsection"),
        ],
    )
    
    documents = []
    vault = Path(vault_path)
    
    for md_file in vault.rglob("*.md"):
        # 跳过模板和配置文件
        if ".obsidian" in str(md_file) or ".trash" in str(md_file):
            continue
        
        content = md_file.read_text(encoding="utf-8")
        chunks = splitter.split_text(content)
        
        for chunk in chunks:
            documents.append({
                "content": chunk.page_content,
                "metadata": {
                    "source": str(md_file.relative_to(vault)),
                    "title": chunk.metadata.get("title", ""),
                    "section": chunk.metadata.get("section", ""),
                },
            })
    
    return documents
```

| 分块参数 | 推荐值 | 理由 |
|:---|:---|:---|
| 分块粒度 | `##` 级别 | 一个 `##` 往往是一个完整知识点 |
| 块大小 | 300-500 字 | 太小丢失上下文，太大浪费 Token |
| 重叠 | 50 字 | 防止信息被切断在边界 |
| metadata | 文件名+标题 | 检索后能告诉用户"来自哪篇文章" |

> 💡 **为什么用 `MarkdownHeaderTextSplitter` 而非按字数切**：Markdown 文章有天然的结构（标题层级），按标题分块能保证每个块是一个语义完整的段落。按字数切会把一个知识点切成两半，降低检索质量。

### 5.2 向量存储与 RAG 问答

文档分块后，需要向量化存储并提供检索能力。我们用 ChromaDB（轻量本地向量库）+ BGE 嵌入模型。

```python
"""向量知识库：索引构建与搜索"""
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# 使用 BGE 中文嵌入模型
embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-zh-v1.5",
)

# 初始化 ChromaDB（本地持久化）
client = chromadb.PersistentClient(path="./knowledge_db")
collection = client.get_or_create_collection(
    name="personal_notes",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"},  # 余弦相似度
)

def build_index(documents: list[dict]):
    """构建向量索引（首次加载或更新时调用）"""
    collection.add(
        documents=[d["content"] for d in documents],
        metadatas=[d["metadata"] for d in documents],
        ids=[f"doc_{i}" for i in range(len(documents))],
    )
    print(f"✅ 已索引 {len(documents)} 个文档块")
```

**注册为 Agent 工具：**

```python
@tool
def search_knowledge_base(query: str, n_results: int = 5) -> str:
    """在个人知识库中搜索相关内容。

    Args:
        query: 搜索问题，如 "Redis 持久化策略" "FastAPI 依赖注入"
        n_results: 返回的结果数量，默认 5
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )
    
    if not results["documents"][0]:
        return "📚 知识库中没有找到相关内容。"
    
    formatted = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        source = meta.get("source", "未知")
        section = meta.get("section", "")
        header = f"📄 {source}"
        if section:
            header += f" > {section}"
        formatted.append(f"{header}\n{doc[:300]}...")
    
    return "找到以下相关内容：\n\n" + "\n\n---\n\n".join(formatted)
```

```
RAG 问答的完整流程：

  用户："Redis 的 RDB 和 AOF 有什么区别？"
    │
    ▼ LLM 判断意图 → 调用 search_knowledge_base()
    │
    ▼ ChromaDB 向量检索
  查询向量 ──→ 余弦相似度匹配 ──→ Top 5 结果
    │
    ▼ 工具返回检索结果
  📄 Redis入门教程/第5章.md > 持久化策略
  "RDB 是快照方式，将内存数据定期写入磁盘..."
  
  📄 后端工程/缓存设计.md > Redis 持久化
  "AOF 记录每一条写操作命令..."
    │
    ▼ LLM 结合检索结果生成回答
  
  "根据你的笔记，RDB 和 AOF 的区别是：
   - RDB：快照方式，定期全量备份...
   - AOF：日志方式，记录每条写操作...
   
   📎 来源：Redis入门教程/第5章.md"
```

> 💡 **ChromaDB vs pgvector vs Milvus**：个人知识库通常几千到几万个文档块，ChromaDB（本地嵌入式）完全够用，零配置、纯 Python。超过 100 万级别再考虑 Milvus。
### 5.3 引用溯源：让回答"有据可查"

知识库问答最怕"编答案"——用户问的是你笔记里的内容，AI 却在胡编。引用溯源让每个回答都标注来源。

在 System Prompt 中加入引用要求：

```python
KNOWLEDGE_INSTRUCTION = """
当使用知识库搜索结果回答问题时：
1. 只基于搜索到的内容回答，不要编造
2. 如果搜索结果不足以回答，如实说"笔记中没有找到相关内容"
3. 在回答末尾标注来源文件，格式：
   📎 来源：[文件名] > [章节名]
4. 如果多个来源，逐一列出
"""
```

```
引用溯源的效果对比：

  ❌ 没有引用溯源：
  ═══════════════════════════════════════
  "Redis 的 RDB 持久化是通过 fork 子进程
   将内存数据写入磁盘的快照方式..."
  
  → 用户不确定：这是 AI 编的还是我笔记里写的？
  → 无法验证，不敢信

  ✅ 有引用溯源：
  ═══════════════════════════════════════
  "Redis 的 RDB 持久化是通过 fork 子进程
   将内存数据写入磁盘的快照方式...
   
   📎 来源：
   • Redis入门教程/第5章.md > 5.2 RDB 持久化
   • 后端工程/缓存架构.md > Redis 持久化对比"
  
  → 用户可以直接点开文件验证
  → 建立信任：AI 不是在编，是真的在"翻笔记"
```

**增量更新策略（笔记修改后同步索引）：**

```python
import hashlib

def sync_index(vault_path: str):
    """增量同步：只重新索引修改过的文件"""
    documents = load_obsidian_vault(vault_path)
    
    for doc in documents:
        content_hash = hashlib.md5(
            doc["content"].encode()
        ).hexdigest()
        doc_id = f"{doc['metadata']['source']}_{content_hash[:8]}"
        
        # ChromaDB 的 upsert：存在则更新，不存在则插入
        collection.upsert(
            documents=[doc["content"]],
            metadatas=[doc["metadata"]],
            ids=[doc_id],
        )
    
    print(f"🔄 同步完成，共 {len(documents)} 个文档块")
```

> 💡 **增量更新用 content hash 做 ID**：内容变了 hash 就变，会创建新的向量条目；内容没变就跳过。这比"全删全建"高效得多，适合 Obsidian 日常编辑场景。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **标题分块** | 用 `MarkdownHeaderTextSplitter`，保持语义完整性 |
| **向量存储** | ChromaDB 本地持久化 + BGE 中文嵌入模型 |
| **RAG 流程** | 用户问题 → 向量检索 → Top K 结果 → LLM 生成回答 |
| **引用溯源** | 回答末尾标注来源文件和章节，用户可验证 |
| **增量更新** | content hash 做 ID，upsert 只更新修改过的内容 |

---

## 6. 工具编排：Function Calling 与多工具协作

前面三章分别实现了日历、邮件、知识库三个工具。但真正的助理不只是"一次调一个工具"——用户说"**查一下明天的安排，如果下午有空帮我回复张总的邮件说可以开会**"，这需要链式调用多个工具。本章讲解 Function Calling 的底层机制和多工具编排策略。

### 6.1 工具定义与注册：标准化的 JSON Schema

LLM 怎么知道有哪些工具可用？答案是：**你把工具列表以 JSON Schema 格式发送给 LLM，LLM 在推理时决定是否调用**。

```
Function Calling 的工作机制：

  开发者 → 注册工具列表（JSON Schema）
  ═══════════════════════════════════════
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "query_calendar",
        "description": "查询指定日期的日程安排",
        "parameters": {
          "type": "object",
          "properties": {
            "start_date": {
              "type": "string",
              "description": "开始日期，格式 YYYY-MM-DD"
            }
          },
          "required": ["start_date"]
        }
      }
    }
  ]
  
  LLM → 推理后决定是否调用
  ═══════════════════════════════════════
  用户说 "明天有什么安排"
  LLM 输出：
  {
    "tool_calls": [{
      "function": {
        "name": "query_calendar",
        "arguments": "{\"start_date\": \"2026-04-12\"}"
      }
    }]
  }
  
  你的代码 → 解析 tool_calls → 调用函数 → 结果返回 LLM
```

在 LangChain 中，`@tool` 装饰器自动把 Python 函数转成 JSON Schema：

```python
from langchain_core.tools import tool

# 你写的 Python 函数
@tool
def query_calendar(start_date: str, end_date: str | None = None) -> str:
    """查询指定日期范围的日程安排。

    Args:
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期（可选），不传则只查当天
    """
    ...

# LangChain 自动生成的 JSON Schema（你不需要手写）
print(query_calendar.tool_call_schema.schema())
# {
#   "title": "query_calendar",
#   "description": "查询指定日期范围的日程安排。",
#   "properties": {
#     "start_date": {"type": "string", "description": "开始日期..."},
#     "end_date": {"type": "string", "description": "结束日期..."}
#   },
#   "required": ["start_date"]
# }
```

| 影响 LLM 工具选择的要素 | 重要性 | 说明 |
|:---|:---|:---|
| **函数名** | ⭐⭐⭐ | 要语义清晰：`query_calendar` > `get_data` |
| **description** | ⭐⭐⭐ | LLM 根据描述决定是否调用，越清楚越好 |
| **参数描述** | ⭐⭐ | 告诉 LLM 每个参数该传什么格式 |
| **参数类型** | ⭐⭐ | str/int/bool，LLM 会严格遵守 |
| **required** | ⭐ | 区分必填和选填参数 |

> 💡 **`@tool` 的 Docstring 就是 description**——它会被直接发送给 LLM。所以 Docstring 不只是给开发者看的注释，而是影响 AI 行为的关键指令。写得模糊 = LLM 调错工具。

### 6.2 多工具编排：并行调用与链式推理

LLM 的 Function Calling 支持三种调用模式——**单工具、并行、链式**，复杂度递增：

```
三种工具调用模式：

  ① 单工具调用
  ═══════════════════════════════════════
  用户："明天有什么安排"
  LLM → tool_calls: [query_calendar()]
  → 1 次工具调用，1 次 LLM 推理

  ② 并行调用（Parallel Tool Calls）
  ═══════════════════════════════════════
  用户："帮我看看明天的安排和最近的邮件"
  LLM → tool_calls: [
    query_calendar(date="2026-04-12"),
    get_recent_emails(max_results=5),
  ]
  → 2 个工具同时执行，结果一起返回 LLM
  → 只需 1 轮 tool 调用

  ③ 链式调用（Sequential / Chained）
  ═══════════════════════════════════════
  用户："查明天下午有没有空，有空的话帮我约牙医"
  
  第 1 轮 LLM → tool_calls: [query_calendar()]
  工具返回：下午 2-5 点空闲
  
  第 2 轮 LLM → 看到结果，决定创建事件
  → tool_calls: [create_event(summary="牙医", ...)]
  
  第 3 轮 LLM → 没有 tool_calls，生成最终回复
  → 需要多轮 ReAct 循环
```

**ToolNode 自动处理并行调用：**

```python
from langgraph.prebuilt import ToolNode

# ToolNode 天然支持并行调用
# 当 LLM 返回多个 tool_calls 时，自动并行执行
tool_node = ToolNode(ALL_TOOLS)

# 假设 LLM 返回了 2 个 tool_calls：
# tool_calls = [
#     {"name": "query_calendar", "args": {...}},
#     {"name": "get_recent_emails", "args": {...}},
# ]
# ToolNode 会同时执行两个工具，收集两个结果
# 返回 2 条 ToolMessage
```

```
链式调用的完整流程示例：

  用户："查明天的安排，如果下午 3 点有空，
        帮我创建一个产品评审会"
    │
    ▼ 第 1 轮 LLM
  tool_calls: [query_calendar(start_date="2026-04-12")]
    │
    ▼ tools 执行 → 返回日程列表
  "找到 2 个日程：09:00 站会, 14:00 周会"
    │
    ▼ 第 2 轮 LLM（看到日程列表）
  推理："下午 3 点没有安排，可以创建"
  tool_calls: [create_event_smart(
    summary="产品评审会",
    start_time="2026-04-12T15:00:00",
    end_time="2026-04-12T16:00:00"
  )]
    │
    ▼ tools 执行 → "✅ 已创建"
    │
    ▼ 第 3 轮 LLM（看到创建结果）
  "明天的安排：
   09:00 站会
   14:00 周会
   15:00 产品评审会 ← 刚帮你创建
   
   下午 3 点已经安排了产品评审会 ✅"
```

> 💡 **链式调用不需要写编排逻辑**——LangGraph 的 `tools → chatbot` 循环天然支持。LLM 看到上一步工具结果后自行决定下一步。这就是 ReAct 模式的威力：推理能力让 LLM 成为自己的"编排器"。
### 6.3 工具调用的错误处理与降级

工具调用在生产环境一定会出错——API 超时、认证过期、参数解析失败。关键是**让 LLM 看到错误信息后能优雅地处理**。

```python
from langgraph.prebuilt import ToolNode

class SafeToolNode(ToolNode):
    """增强版工具节点：捕获异常并返回友好的错误信息"""
    
    async def _run_tool(self, tool_call, tools):
        try:
            return await super()._run_tool(tool_call, tools)
        except Exception as e:
            # 把异常信息包装成 ToolMessage 返回给 LLM
            error_msg = f"⚠️ 工具执行失败：{type(e).__name__}: {str(e)}"
            return ToolMessage(
                content=error_msg,
                tool_call_id=tool_call["id"],
            )
```

```
错误处理的三层策略：

  第 1 层：工具内部重试
  ═══════════════════════════════════════
  API 调用失败时，工具内部自动重试 2-3 次
  适用于：网络抖动、临时超时
  
  @tool
  def query_calendar(...):
      for attempt in range(3):
          try:
              return _do_query(...)
          except HttpError:
              if attempt == 2: raise
              await asyncio.sleep(1)

  第 2 层：LLM 自主降级
  ═══════════════════════════════════════
  工具彻底失败后，LLM 看到错误信息，自行决策
  
  工具返回："⚠️ Google Calendar API 不可用"
  LLM 推理："日历服务暂时不可用，我无法查询
            你的日程。你可以稍后再试，或者告诉我
            你明天的安排，我帮你记下来。"

  第 3 层：兜底回复
  ═══════════════════════════════════════
  如果 LLM 自己也出了问题（token 限制等）
  
  try:
      result = await agent.ainvoke(...)
  except Exception:
      return "抱歉，系统出了点问题，请稍后再试。"
```

**工具执行超时保护：**

```python
import asyncio

async def run_with_timeout(tool_fn, args, timeout=30):
    """给工具调用加超时保护"""
    try:
        return await asyncio.wait_for(
            tool_fn.ainvoke(args),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        return f"⚠️ 工具 {tool_fn.name} 执行超时（{timeout}s），已跳过。"
```

| 错误类型 | 处理策略 | 示例 |
|:---|:---|:---|
| 网络超时 | 工具内重试 3 次 | Google API 暂时不可达 |
| 认证过期 | 返回错误信息，提示用户重新授权 | OAuth token 过期 |
| 参数错误 | LLM 看到错误后自动修正参数重试 | 日期格式不对 |
| 服务不可用 | LLM 用自身知识兜底或建议替代方案 | Gmail API 宕机 |

> 💡 **让 LLM 看到错误是关键设计**——不要在代码里静默吞掉异常。把错误信息作为 ToolMessage 返回给 LLM，LLM 有足够的推理能力来决定：重试、换工具、还是告诉用户"这个功能暂时不可用"。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **JSON Schema** | `@tool` 自动生成，Docstring 是给 LLM 看的工具说明 |
| **并行调用** | LLM 一次返回多个 tool_calls，ToolNode 自动并行执行 |
| **链式调用** | ReAct 循环自动支持，LLM 基于工具结果决定下一步 |
| **错误处理** | 三层策略：工具重试→LLM 降级→兜底回复 |
| **超时保护** | asyncio.wait_for 防止工具阻塞整个 Agent |

---

## 7. 记忆系统：让助理真正"了解"你

没有记忆的助理，每次对话都像第一次见面。你说了十遍"我用 Python"，它第十一次还问"你用什么语言"。本章实现两种关键记忆：**用户画像（你是谁）** 和 **跨会话历史（之前聊了什么）**。

### 7.1 用户画像自动提取与持久化

用户画像不需要手动填表——让 LLM 从对话中**自动抽取**。

```
用户画像自动提取流程：

  对话进行中...
  ═══════════════════════════════════════
  用户："我是做后端的，主要用 Python 和 FastAPI"
  用户："我们公司用 PostgreSQL 和 Redis"
  用户："我比较喜欢简洁的代码风格"
    │
    ▼ 每轮对话结束后，后台异步提取
  
  LLM 提取 prompt：
  "从以下对话中提取用户信息（姓名、职业、
   技术栈、偏好、项目等），输出为 JSON"
    │
    ▼ 提取结果
  {
    "occupation": "后端开发",
    "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis"],
    "preferences": ["简洁的代码风格"],
    "projects": []
  }
    │
    ▼ 与已有画像合并 → 持久化到本地 JSON
```

```python
"""用户画像自动提取与管理"""
from langchain_openai import ChatOpenAI
import json
from pathlib import Path

EXTRACT_PROMPT = """请从以下对话中提取用户的个人信息。只提取明确提到的信息，不要猜测。

对话内容：
{conversation}

已有画像：
{existing_profile}

请输出更新后的 JSON 格式画像，包含以下字段（没有的留空）：
- name: 姓名
- occupation: 职业
- tech_stack: 技术栈列表
- preferences: 偏好和习惯
- projects: 正在做的项目
- important_contacts: 重要联系人（如老板、同事名字）

只输出 JSON，不需要解释。"""

class UserProfileManager:
    """用户画像管理器"""
    
    def __init__(self, storage_dir: str = "./memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.llm = ChatOpenAI(model="deepseek-chat", temperature=0)
    
    def load(self, user_id: str) -> dict:
        """加载用户画像"""
        path = self.storage_dir / f"{user_id}_profile.json"
        if path.exists():
            return json.loads(path.read_text())
        return {}
    
    def save(self, user_id: str, profile: dict):
        """保存用户画像"""
        path = self.storage_dir / f"{user_id}_profile.json"
        path.write_text(json.dumps(profile, ensure_ascii=False, indent=2))
    
    async def extract_and_update(
        self, user_id: str, messages: list
    ) -> dict:
        """从对话中提取新信息并更新画像"""
        existing = self.load(user_id)
        
        # 只取最近几轮对话用于提取（不需要全部历史）
        recent = messages[-6:]  # 最近 3 轮
        conversation = "\n".join(
            f"{m.type}: {m.content}" for m in recent
            if hasattr(m, "content") and m.content
        )
        
        # 如果对话太短，可能没有值得提取的信息
        if len(conversation) < 50:
            return existing
        
        response = await self.llm.ainvoke(
            EXTRACT_PROMPT.format(
                conversation=conversation,
                existing_profile=json.dumps(existing, ensure_ascii=False),
            )
        )
        
        try:
            updated = json.loads(response.content)
            self.save(user_id, updated)
            return updated
        except json.JSONDecodeError:
            return existing  # 提取失败，保持原样

    def to_prompt_text(self, profile: dict) -> str:
        """将画像转为可注入 System Prompt 的文本"""
        if not profile:
            return ""
        
        lines = []
        if profile.get("name"):
            lines.append(f"姓名：{profile['name']}")
        if profile.get("occupation"):
            lines.append(f"职业：{profile['occupation']}")
        if profile.get("tech_stack"):
            lines.append(f"技术栈：{', '.join(profile['tech_stack'])}")
        if profile.get("preferences"):
            lines.append(f"偏好：{', '.join(profile['preferences'])}")
        
        return "\n".join(lines)
```

> 💡 **提取用小模型（DeepSeek V3 / GPT-4o-mini）异步执行**——画像提取不在用户等待的关键路径上，可以在回复用户后后台执行。一次提取成本约 $0.001，但带来的"记住用户"体验价值巨大。

### 7.2 跨会话记忆：Checkpointer + 语义检索

LangGraph 的 Checkpointer 天然支持跨会话状态持久化——同一个 `thread_id` 的对话，关闭后再打开，之前的 messages 全部恢复。

```
Checkpointer 的工作方式：

  会话 A（thread_id = "session_001"）
  ═══════════════════════════════════════
  第 1 轮: user: "我叫张三"
           ai: "你好张三！"
  第 2 轮: user: "帮我查明天日程"
           ai: "你明天有 3 个安排..."
  
  ← 用户关闭应用 →
  
  会话 B（同一个 thread_id = "session_001"）
  ═══════════════════════════════════════
  第 3 轮: user: "上次帮我查的日程里有什么？"
           ai: "上次查到你明天有 3 个安排：
                09:00 站会, 14:00 周会..."
  
  ← Checkpointer 自动恢复了之前的 messages →
```

但 Checkpointer 只保存**单个会话**的状态。如果用户开了新会话（新的 `thread_id`），就看不到旧会话的内容了。这时候需要**语义检索跨会话记忆**：

```python
"""跨会话记忆检索"""
from langchain_core.tools import tool

# 用 ChromaDB 存储历史会话摘要
memory_collection = client.get_or_create_collection(
    name="conversation_memories",
    embedding_function=embedding_fn,
)

async def save_session_summary(
    user_id: str,
    thread_id: str, 
    messages: list,
):
    """会话结束时，保存会话摘要到向量库"""
    # 用 LLM 生成会话摘要
    conversation = "\n".join(
        f"{m.type}: {m.content}" for m in messages
        if hasattr(m, "content") and m.content
    )
    
    summary_llm = ChatOpenAI(model="deepseek-chat", temperature=0)
    summary = await summary_llm.ainvoke(
        f"请用 2-3 句话总结这段对话的要点：\n{conversation}"
    )
    
    # 存入向量库
    memory_collection.add(
        documents=[summary.content],
        metadatas=[{
            "user_id": user_id,
            "thread_id": thread_id,
            "timestamp": datetime.now().isoformat(),
        }],
        ids=[f"mem_{thread_id}"],
    )

@tool
def recall_past_conversations(query: str) -> str:
    """回忆之前的对话内容。当用户提到"上次""之前""我们讨论过"时使用。

    Args:
        query: 要回忆的内容，如 "上次讨论的数据库方案"
    """
    results = memory_collection.query(
        query_texts=[query],
        n_results=3,
    )
    
    if not results["documents"][0]:
        return "没有找到相关的历史对话记录。"
    
    formatted = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        time = meta.get("timestamp", "")[:10]
        formatted.append(f"📝 {time}：{doc}")
    
    return "找到以下相关的历史对话：\n\n" + "\n\n".join(formatted)
```

```
短期 vs 长期记忆的协同：

  ┌─────────────────────────────────────────┐
  │  短期记忆（Working Memory）               │
  │  ── Checkpointer 自动管理                 │
  │  ── 当前会话的完整 messages               │
  │  ── 包含用户画像（注入 System Prompt）     │
  ├─────────────────────────────────────────┤
  │  长期记忆（跨会话）                        │
  │  ── 会话摘要存入 ChromaDB                 │
  │  ── 用户画像存入本地 JSON                  │
  │  ── 通过 recall_past_conversations 工具    │
  │     按语义检索历史记忆                     │
  └─────────────────────────────────────────┘
```

> 💡 **记忆是工具而非魔法**——跨会话记忆本质上就是一个向量检索工具。用户说"我们之前讨论过的方案"，LLM 调用 `recall_past_conversations` 搜索历史，和调 Google Calendar 没本质区别。
### 7.3 隐私优先：本地存储与数据加密

个人 AI 助理处理的是你最敏感的数据——邮件、日程、笔记、个人偏好。隐私保护不是可选的，是必须的。

```
隐私保护策略（三层防线）：

  第 1 层：数据本地化
  ═══════════════════════════════════════
  • 所有记忆数据存本地（SQLite / JSON / ChromaDB）
  • 不使用云端 Memory 服务（如 ChatGPT Memory）
  • 向量库存在 ./knowledge_db，不上传

  第 2 层：传输最小化
  ═══════════════════════════════════════
  • 邮件只发送摘要给 LLM，不发正文全文
  • 日程只发标题和时间，不发参会人详情
  • 知识库 RAG 只发送 Top K 片段，不发全文

  第 3 层：敏感数据脱敏
  ═══════════════════════════════════════
  • 发送给 LLM 前，自动替换手机号、身份证号
  • 用户画像中不存储密码、token 等凭证
  • 支持对特定文件夹标记"不纳入知识库"
```

**本地数据加密（可选）：**

```python
"""记忆数据加密存储"""
from cryptography.fernet import Fernet
from pathlib import Path

class EncryptedStorage:
    """加密的本地存储"""
    
    def __init__(self, key_path: str = "./memory/.secret_key"):
        key_path = Path(key_path)
        if key_path.exists():
            self.key = key_path.read_bytes()
        else:
            self.key = Fernet.generate_key()
            key_path.parent.mkdir(exist_ok=True)
            key_path.write_bytes(self.key)
        
        self.cipher = Fernet(self.key)
    
    def encrypt_and_save(self, data: str, filepath: str):
        """加密后保存"""
        encrypted = self.cipher.encrypt(data.encode())
        Path(filepath).write_bytes(encrypted)
    
    def load_and_decrypt(self, filepath: str) -> str:
        """加载并解密"""
        encrypted = Path(filepath).read_bytes()
        return self.cipher.decrypt(encrypted).decode()
```

| 数据类型 | 是否加密 | 存储位置 | 说明 |
|:---|:---|:---|:---|
| 用户画像 | 推荐加密 | `./memory/{user_id}_profile.json` | 包含个人信息 |
| 会话历史 | 可选加密 | `assistant.db`（SQLite） | Checkpointer 管理 |
| 知识库索引 | 不加密 | `./knowledge_db/` | 源文件已在本地 |
| API 凭证 | 必须加密 | `./credentials/` | OAuth tokens |

> 💡 **使用本地/私有 LLM 是终极隐私方案**——如果你对发送数据给 OpenAI/DeepSeek 有顾虑，可以用 Ollama 本地部署 Qwen-2.5 或 Llama 3。对于工具调用场景，7B-14B 的模型就够用了，在 Apple Silicon Mac 上推理速度也不错。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **用户画像** | LLM 从对话中自动提取，JSON 格式持久化，注入 System Prompt |
| **Checkpointer** | 自动保存/恢复单个会话的完整状态（messages + state） |
| **跨会话记忆** | 会话摘要存入向量库，通过工具按语义检索 |
| **三层隐私** | 数据本地化 + 传输最小化 + 敏感数据脱敏 |
| **加密存储** | Fernet 对称加密保护用户画像和 API 凭证 |

---

## 8. 接口层：多端接入与交互体验

Agent 核心和工具层都搞定了，但用户总不能每次打开 Python REPL 来跟助理对话。接口层决定"用户在哪里、怎么和助理交互"——从最快验证的 CLI，到随身携带的 Telegram Bot。

### 8.1 CLI 与 Web UI：快速搭建交互界面

**CLI 交互（5 分钟搞定，开发阶段必备）：**

```python
"""CLI 交互入口"""
import asyncio
from rich.console import Console
from rich.markdown import Markdown

console = Console()

async def cli_chat():
    agent = build_agent()
    config = {"configurable": {"thread_id": "cli_session", "user_id": "me"}}
    
    console.print("[bold green]🤖 AI 助理已就绪！[/]输入 'quit' 退出\n")
    
    while True:
        user_input = console.input("[bold cyan]你：[/] ")
        if user_input.lower() in ("quit", "exit", "q"):
            break
        
        result = await agent.ainvoke(
            {"messages": [("user", user_input)]},
            config=config,
        )
        
        reply = result["messages"][-1].content
        console.print(f"\n[bold yellow]🤖：[/]")
        console.print(Markdown(reply))
        console.print()

if __name__ == "__main__":
    asyncio.run(cli_chat())
```

**Gradio Web UI（10 分钟搞定，可分享）：**

```python
"""Gradio Web 界面"""
import gradio as gr

agent = build_agent()

async def chat_fn(message: str, history: list):
    """Gradio 聊天回调"""
    config = {"configurable": {"thread_id": "web_session", "user_id": "me"}}
    
    result = await agent.ainvoke(
        {"messages": [("user", message)]},
        config=config,
    )
    
    return result["messages"][-1].content

demo = gr.ChatInterface(
    fn=chat_fn,
    title="🤖 个人 AI 助理",
    description="管理日程、查看邮件、搜索知识库",
    examples=[
        "明天有什么安排？",
        "帮我看看最近的邮件",
        "Redis 的持久化策略有哪些？",
    ],
    type="messages",
)

demo.launch(server_port=7860, share=False)
```

| 方案 | 搭建时间 | 适用场景 | 特点 |
|:---|:---|:---|:---|
| **CLI** | 5 分钟 | 开发调试 | 零依赖、最快验证 |
| **Gradio** | 10 分钟 | 个人使用、展示 | 美观、支持 Markdown、一键分享 |
| **Streamlit** | 15 分钟 | 个人使用 | 更灵活的布局 |
| **React** | 数天 | 生产级产品 | 完全自定义，需要全栈开发 |

> 💡 **MVP 阶段用 Gradio，够了**。不要在 UI 上花太多时间——先确保 Agent 核心跑通。等你每天真的在用这个助理了，再考虑做 React 前端。

### 8.2 即时通讯接入：微信 / Telegram Bot

让助理随身可用的最佳方案是接入即时通讯。Telegram Bot 是最推荐的——官方 API 完善、不会被封号、支持 Markdown 消息格式。

```python
"""Telegram Bot 接入"""
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes,
)

TELEGRAM_TOKEN = "your-bot-token"  # 从 @BotFather 获取

# 初始化 Agent
agent = build_agent()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    await update.message.reply_text(
        "🤖 你好！我是你的 AI 助理。\n\n"
        "我可以帮你：\n"
        "📅 管理日程（查询/创建）\n"
        "📧 查看邮件摘要\n"
        "📚 搜索你的知识库\n\n"
        "直接说你想做什么就行！"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户消息"""
    user_id = str(update.effective_user.id)
    user_msg = update.message.text
    
    # 显示"正在输入"
    await update.message.chat.send_action("typing")
    
    config = {
        "configurable": {
            "thread_id": f"tg_{user_id}",
            "user_id": user_id,
        }
    }
    
    result = await agent.ainvoke(
        {"messages": [("user", user_msg)]},
        config=config,
    )
    
    reply = result["messages"][-1].content
    
    # Telegram 支持 Markdown 格式
    await update.message.reply_text(
        reply, parse_mode="Markdown"
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling()
```

```
为什么推荐 Telegram 而非微信：

  Telegram Bot ⭐
  ═══════════════════════════════════════
  ✅ 官方 Bot API，稳定可靠
  ✅ 支持 Markdown / HTML 消息
  ✅ 支持 Inline Keyboard（按钮交互）
  ✅ 不会被封号
  ✅ 可发送文件、图片

  微信 Bot ⚠️
  ═══════════════════════════════════════
  ⚠️ 无官方 Bot API
  ⚠️ 依赖第三方库（itchat / wechaty）
  ⚠️ 账号有被封风险
  ⚠️ Web 协议不稳定
  ✅ 用户基数大（国内场景刚需）
```

> 💡 **每个用户独立的 `thread_id`**：用 `tg_{user_id}` 作为 thread_id，这样不同 Telegram 用户的对话互不影响，每个人有自己独立的会话历史和记忆。
### 8.3 语音交互：Whisper 输入 + TTS 输出

语音是最自然的交互方式——开车时、做饭时、不想打字时。用 Whisper 做语音转文字（STT），用火山引擎 / OpenAI 做文字转语音（TTS）。

```python
"""语音交互模块"""
import openai
from pathlib import Path
import tempfile

async def speech_to_text(audio_path: str) -> str:
    """语音转文字（使用 OpenAI Whisper API）"""
    client = openai.AsyncOpenAI()
    
    with open(audio_path, "rb") as f:
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="zh",  # 指定中文提高准确率
        )
    
    return transcript.text

async def text_to_speech(text: str, output_path: str = None) -> str:
    """文字转语音（使用 OpenAI TTS）"""
    client = openai.AsyncOpenAI()
    
    if not output_path:
        output_path = tempfile.mktemp(suffix=".mp3")
    
    response = await client.audio.speech.create(
        model="tts-1",
        voice="nova",       # 可选：alloy, echo, fable, onyx, nova, shimmer
        input=text,
        speed=1.1,           # 稍快一点更自然
    )
    
    response.stream_to_file(output_path)
    return output_path
```

```
语音交互的完整流程：

  🎤 用户说话
    │
    ▼ Whisper STT
  "帮我看看明天有什么安排"（文字）
    │
    ▼ Agent 处理（和文字输入一样）
  "你明天有 3 个安排：..."
    │
    ▼ TTS 合成
  🔊 播放语音回复

  延迟分析：
  ═══════════════════════════════════════
  STT（Whisper）：~1-2 秒（取决于音频长度）
  Agent 推理：   ~2-5 秒（含工具调用）
  TTS 合成：     ~1-2 秒
  总延迟：       ~4-9 秒
  
  ⚠️ 对实时对话来说偏慢
  → 可用 Whisper 本地部署（faster-whisper）降低 STT 延迟
  → TTS 可用流式合成，边生成边播放
```

| 方案 | STT 延迟 | 成本 | 适用场景 |
|:---|:---|:---|:---|
| Whisper API（云端） | 1-2s | $0.006/分钟 | 快速集成 |
| faster-whisper（本地） | 0.3-1s | 免费 | 低延迟需求 |
| 阿里云 ASR | 实时 | 按量计费 | 中文优化 |

> 💡 **语音交互是"锦上添花"而非"雪中送炭"**——大部分场景下文字交互就够了。只在特定场景（开车通勤、做饭时）语音才有优势。建议先做好文字交互，语音作为 Phase 3 功能。

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **CLI** | Rich + asyncio，5 分钟搞定，开发调试首选 |
| **Gradio** | 10 分钟搭建 Web 聊天界面，支持 Markdown |
| **Telegram Bot** | 官方 API 稳定，用 thread_id 隔离用户 |
| **Whisper STT** | 语音转文字，云端或本地部署 |
| **TTS** | 文字转语音，OpenAI / 火山引擎 |

---

## 9. 生产部署与运维

助理开发完了，怎么让它 7×24 小时运行？Docker 打包、定时任务、成本控制、日志监控——这些是从"本地跑着玩"到"每天依赖它工作"的关键一步。

### 9.1 Docker 一键部署与定时任务

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码和配置
COPY . .

# 创建数据目录
RUN mkdir -p /app/memory /app/knowledge_db /app/credentials

# 暴露 Gradio 端口
EXPOSE 7860

CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: "3.8"

services:
  assistant:
    build: .
    ports:
      - "7860:7860"
    volumes:
      # 持久化数据（记忆、知识库、凭证）
      - ./data/memory:/app/memory
      - ./data/knowledge_db:/app/knowledge_db
      - ./data/credentials:/app/credentials
      - ./data/assistant.db:/app/assistant.db
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    restart: unless-stopped
```

```
部署架构：

  ┌─────────────────────────────────────┐
  │  Docker Container                    │
  │                                      │
  │  ┌──────────┐  ┌─────────────────┐  │
  │  │ Agent    │  │ APScheduler     │  │
  │  │ (Gradio) │  │ (定时任务)       │  │
  │  └──────────┘  └─────────────────┘  │
  │  ┌──────────┐  ┌─────────────────┐  │
  │  │ TG Bot   │  │ ChromaDB        │  │
  │  │ (polling)│  │ (知识库)         │  │
  │  └──────────┘  └─────────────────┘  │
  │                                      │
  │  Volume Mounts:                      │
  │  ./data/memory ← 用户画像            │
  │  ./data/knowledge_db ← 向量索引      │
  │  ./data/assistant.db ← 会话历史      │
  └─────────────────────────────────────┘
```

**定时任务配置（晨间日报 + 周报）：**

```python
"""定时任务入口"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

# 每天早上 8:00 推送日报
scheduler.add_job(
    morning_briefing,
    CronTrigger(hour=8, minute=0),
    id="morning_briefing",
)

# 每周五下午 5:00 生成周报
scheduler.add_job(
    weekly_report,
    CronTrigger(day_of_week="fri", hour=17, minute=0),
    id="weekly_report",
)

# 每 6 小时同步一次知识库索引
scheduler.add_job(
    lambda: sync_index("/path/to/obsidian/vault"),
    CronTrigger(hour="*/6"),
    id="sync_knowledge",
)
```

> 💡 **Volume 挂载是关键**——不要把数据存在容器内部。容器重建后数据会丢失。记忆、知识库、凭证全部 mount 到宿主机的 `./data/` 目录。

### 9.2 成本控制：本地模型与云端 API 的混合策略

个人助理如果每天花 $5 调 API，一个月 $150，大部分人接受不了。混合策略可以把成本压到 **$10-30/月**。

```
混合模型策略：

  ┌──────────────────────────────────────┐
  │  任务分级 → 模型选择                    │
  │                                      │
  │  简单任务（70%）→ 本地模型 / 小模型     │
  │  ──────────────────────────────       │
  │  • 日程解析（时间提取）                 │
  │  • 邮件分类（重要/不重要）              │
  │  • 用户画像提取                        │
  │  • 对话摘要压缩                        │
  │  → Qwen-2.5-7B（Ollama）或 deepseek-chat │
  │                                      │
  │  复杂任务（30%）→ 大模型               │
  │  ──────────────────────────────       │
  │  • 多工具链式推理                      │
  │  • 知识库问答（需要高质量理解）          │
  │  • 邮件回复草稿生成                    │
  │  → GPT-4o / DeepSeek V3               │
  └──────────────────────────────────────┘
```

```python
"""多模型路由"""
from langchain_openai import ChatOpenAI

# 轻量模型（用于简单任务）
light_llm = ChatOpenAI(
    model="deepseek-chat",          # DeepSeek V3，极便宜
    base_url="https://api.deepseek.com",
    temperature=0.3,
)

# 重量模型（用于复杂任务）
heavy_llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.3,
)

# 本地模型（零成本）
local_llm = ChatOpenAI(
    model="qwen2.5:7b",
    base_url="http://localhost:11434/v1",  # Ollama
    temperature=0.3,
)
```

月度成本估算（日均 20 次交互）：

| 策略 | 月成本 | 质量 | 延迟 |
|:---|:---|:---|:---|
| 全部 GPT-4o | ~$50-100 | ⭐⭐⭐ | 2-5s |
| 全部 DeepSeek V3 | ~$5-15 | ⭐⭐⭐ | 1-3s |
| 混合（7:3 本地:云端） | ~$3-8 | ⭐⭐ | 1-5s |
| 全部本地（Ollama） | $0 | ⭐⭐ | 3-10s |

> 💡 **DeepSeek V3 是个人项目的性价比之王**——能力接近 GPT-4o，价格只有 1/10。如果你不在意隐私（数据发到 DeepSeek 服务器），全部用 DeepSeek V3 是最佳选择。
### 9.3 监控、日志与安全加固

个人项目不需要 Prometheus + Grafana 那套重量级监控。用结构化日志 + 简单的错误通知就够了。

```python
"""结构化日志配置"""
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "time": datetime.now().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "tool_name"):
            log_data["tool_name"] = record.tool_name
        if record.exc_info:
            log_data["error"] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)

# 配置
handler = logging.FileHandler("assistant.log")
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("assistant")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# 使用
logger.info("工具调用", extra={"tool_name": "query_calendar", "user_id": "me"})
logger.error("API 调用失败", exc_info=True)
```

```
安全加固清单：

  ✅ API Key 管理
  ═══════════════════════════════════════
  • 用 .env 文件 + dotenv 加载
  • 绝不硬编码在代码中
  • Docker 通过 environment 变量传入
  • .env 加入 .gitignore

  ✅ OAuth Token 保护
  ═══════════════════════════════════════
  • token.json 存在 credentials 目录
  • chmod 600 限制读取权限
  • 定期刷新，过期自动重新授权

  ✅ 输入验证
  ═══════════════════════════════════════
  • 限制单次消息长度（防止 Token 注入）
  • 限制工具调用频率
  • Telegram Bot 可设白名单（只允许你的 user_id）
```

```python
"""Telegram Bot 白名单（只允许自己使用）"""
ALLOWED_USERS = {123456789}  # 你的 Telegram user_id

async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("⛔ 未授权的用户")
        return
    # 继续正常处理...
```

> 💡 **个人助理的安全重点是"防止别人用"而非"防止攻击"**——设置白名单、保护好 API Key 和 OAuth Token，对于个人使用场景就够了。

**第 9 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Docker 部署** | Dockerfile + docker-compose，Volume 挂载持久化数据 |
| **定时任务** | APScheduler 晨间日报 + 周报 + 知识库同步 |
| **混合模型** | 简单任务用小模型/本地模型，复杂任务用大模型 |
| **成本控制** | 全用 DeepSeek V3 月成本 $5-15，性价比最优 |
| **安全加固** | .env 管 Key，白名单限用户，chmod 限权限 |

---

## 10. 进阶演进：从助理到 Agent 系统

前面 9 章搭建了一个功能完整的个人 AI 助理。但它还有进化空间——从"一个全能 Agent"拆分为"多个专业 Agent 协作"，从"你问它答"进化为"它主动帮你"。这是 Phase 3 的方向。

### 10.1 多 Agent 协作：专业分工与任务路由

当工具越来越多（10+ 个），单个 Agent 的 System Prompt 会变得臃肿，工具选择准确率会下降。解决方案：**拆分成多个专业 Agent，由路由 Agent 分发任务**。

```
多 Agent 协作架构：

  用户输入
    │
    ▼
  ┌─────────────────────┐
  │  Router Agent       │ ← 只做意图分类，不调工具
  │  "这是日程问题？     │
  │   邮件问题？         │
  │   知识库问题？       │
  │   还是闲聊？"        │
  └──────┬──────────────┘
         │
    ┌────┼────────┬───────────┐
    ▼    ▼        ▼           ▼
  ┌────┐ ┌────┐ ┌──────┐ ┌──────┐
  │日程│ │邮件│ │知识库│ │通用  │
  │Agent│ │Agent│ │Agent │ │Agent │
  │    │ │    │ │      │ │      │
  │查日程│ │查邮件│ │RAG   │ │闲聊  │
  │创日程│ │摘要 │ │搜索  │ │      │
  │提醒 │ │回复 │ │引用  │ │      │
  └────┘ └────┘ └──────┘ └──────┘
```

```python
"""多 Agent 架构（概念代码）"""
from langgraph.graph import StateGraph, START, END

# 路由 Agent：判断意图
async def router(state: AgentState) -> dict:
    """分析用户意图，决定交给哪个专业 Agent"""
    router_llm = ChatOpenAI(model="deepseek-chat", temperature=0)
    
    response = await router_llm.ainvoke(
        f"分析以下用户消息的意图，只输出一个类别：\n"
        f"calendar / email / knowledge / general\n\n"
        f"消息：{state['messages'][-1].content}"
    )
    
    return {"intent": response.content.strip()}

def route_to_agent(state: AgentState) -> str:
    """根据意图路由到对应 Agent"""
    intent = state.get("intent", "general")
    return {
        "calendar": "calendar_agent",
        "email": "email_agent",
        "knowledge": "knowledge_agent",
    }.get(intent, "general_agent")

# 组装
graph = StateGraph(AgentState)
graph.add_node("router", router)
graph.add_node("calendar_agent", calendar_agent)
graph.add_node("email_agent", email_agent)
graph.add_node("knowledge_agent", knowledge_agent)
graph.add_node("general_agent", general_agent)

graph.add_edge(START, "router")
graph.add_conditional_edges("router", route_to_agent)
# 所有子 Agent → END
```

| 架构 | 优点 | 缺点 | 适用 |
|:---|:---|:---|:---|
| **单 Agent** | 简单、上下文共享 | 工具多了不精准 | 工具 < 8 个 |
| **多 Agent** | 专业分工、Prompt 精简 | 路由有开销、跨 Agent 通信 | 工具 > 8 个 |

> 💡 **不要过早拆分**——MVP 阶段一个 Agent + 5-6 个工具就够了。等你发现"日程和邮件的 Prompt 互相干扰导致调错工具"时，再考虑拆分。

### 10.2 主动式助理：从"被动回答"到"主动推送"

当前的助理是"你问它答"。真正有价值的助理应该**不等你问，主动为你工作**。

```
主动式助理的三种触发方式：

  ① 定时触发（Time-based）
  ═══════════════════════════════════════
  • 每天 8:00 → 推送今日日程 + 重要邮件摘要
  • 每周五 17:00 → 自动生成周报初稿
  • 每天 22:00 → 推送明日日程预告

  ② 事件触发（Event-based）
  ═══════════════════════════════════════
  • 收到老板的邮件 → 立即推送通知
  • 日历事件创建 → 15 分钟前提醒
  • GitHub PR 被 Review → 推送 Review 意见摘要

  ③ 条件触发（Condition-based）
  ═══════════════════════════════════════
  • 检测到明天有 3 个会议连续排满 → 建议调整
  • 本周待办超过 10 个未完成 → 提醒优先排序
  • 知识库更新了新文章 → 推送摘要
```

```python
"""事件驱动的主动推送"""

async def check_important_emails():
    """定时检查重要邮件（每 30 分钟执行一次）"""
    emails = get_recent_emails.invoke({
        "query": "is:unread newer_than:30m",
        "max_results": 5,
    })
    
    if "没有找到" in emails:
        return
    
    # 用 LLM 判断是否需要立即通知
    llm = ChatOpenAI(model="deepseek-chat", temperature=0)
    analysis = await llm.ainvoke(
        f"以下邮件中有需要立即处理的吗？只回答 YES 或 NO\n{emails}"
    )
    
    if "YES" in analysis.content.upper():
        await send_notification(f"📧 你有重要邮件需要处理：\n{emails}")

# 每 30 分钟检查一次
scheduler.add_job(
    check_important_emails,
    CronTrigger(minute="*/30"),
    id="check_emails",
)
```

> 💡 **主动推送的关键是"不打扰"**——推送太频繁用户会关掉通知。把推送分为三个等级：🔴 立即推送（老板邮件）、🟡 汇总推送（每日日报）、⚪ 不推送（常规信息）。
### 10.3 未来展望：个人 AI 助理的演进方向

个人 AI 助理的未来不是"更好的聊天机器人"，而是**真正的数字员工**。

```
个人 AI 助理的演进路线图：

  2024-2025：工具调用时代 ← 我们现在在这里
  ═══════════════════════════════════════
  • Function Calling + ReAct 循环
  • 单 Agent + 多工具
  • 被动响应为主
  • 文字交互为主

  2025-2026：Agent 协作时代
  ═══════════════════════════════════════
  • 多 Agent 专业分工
  • 主动式推送和预判
  • 语音交互常态化
  • Computer Use（操作你的电脑）
  • MCP 协议（标准化工具接入）

  2026-2027：自主代理时代
  ═══════════════════════════════════════
  • 长期规划与自主执行
  • "帮我完成这个项目的第一版"
  • 跨应用操作（浏览器 + 本地应用）
  • 个人知识图谱自动构建
  • 从"助理"到"数字分身"
```

**值得关注的技术方向：**

| 技术 | 影响 | 当前状态 |
|:---|:---|:---|
| **MCP 协议** | 工具接入标准化，一次开发到处可用 | 🟢 已可用 |
| **Computer Use** | AI 直接操控桌面应用 | 🟡 早期阶段 |
| **Gemini 2.5 Pro** | 100 万 Token 上下文，减少记忆系统复杂度 | 🟢 已可用 |
| **本地大模型** | 隐私保护 + 零成本 | 🟢 7B-70B 可用 |
| **多模态** | 语音/图片/视频输入输出 | 🟡 部分可用 |

> 💡 **最好的个人 AI 助理是你真正每天在用的那个**——不要追求完美架构，先做一个能管日程和邮件的 MVP，每天用起来。你会在使用过程中自然发现最需要的下一个功能是什么。

**第 10 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **多 Agent** | Router Agent + 专业 Agent，工具 > 8 个时考虑拆分 |
| **主动推送** | 定时/事件/条件三种触发方式，关键是"不打扰" |
| **三级推送** | 🔴 立即 / 🟡 汇总 / ⚪ 静默 |
| **MCP 协议** | 工具接入的标准化协议，一次开发到处可用 |
| **演进路线** | 工具调用 → Agent 协作 → 自主代理 |
