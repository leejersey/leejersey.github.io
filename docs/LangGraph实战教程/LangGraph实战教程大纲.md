# LangGraph 实战教程

> **目标**：从零掌握 LangGraph 的核心概念与实战用法，学会构建有状态、可中断、可恢复的 AI Agent 和多智能体系统。

---

## 第一章 认识 LangGraph
<!-- 简述本章要点：LangGraph 是什么、解决什么问题、与 LangChain 的关系、核心思想 -->

### 1.1 LangGraph 是什么 —— 一句话理解
### 1.2 为什么需要 LangGraph（线性 Chain 的局限 → 图结构的优势）
### 1.3 LangGraph vs LangChain vs AutoGen vs CrewAI —— 框架定位对比
### 1.4 LangGraph 的核心三要素：State / Node / Edge
### 1.5 整体架构概览（StateGraph → 编译 → 执行 → 持久化）

---

## 第二章 环境搭建与第一个 Graph
<!-- 简述本章要点：安装、配置 API Key、构建并运行第一个最简单的 Graph -->

### 2.1 安装 LangGraph 及相关依赖
### 2.2 配置 LLM（DeepSeek / 本地模型）
### 2.3 Hello Graph：构建第一个两节点图
### 2.4 可视化你的 Graph（Mermaid 图 / LangSmith）

---

## 第三章 State —— 图的共享记忆
<!-- 简述本章要点：State 的定义、TypedDict vs Pydantic、Reducer 机制 -->

### 3.1 什么是 State —— Graph 的"全局变量"
### 3.2 用 TypedDict 定义 State
### 3.3 Reducer：消息追加而非覆盖（Annotated + operator.add）
### 3.4 用 Pydantic 定义 State（类型校验 + 默认值）
### 3.5 MessagesState —— 对话场景的现成方案

---

## 第四章 Node 与 Edge —— 图的骨架
<!-- 简述本章要点：节点函数、普通边、条件边、路由函数 -->

### 4.1 Node：就是一个普通 Python 函数
### 4.2 Edge：节点之间的连线
### 4.3 条件边（Conditional Edge）—— 让 Agent 做决策
### 4.4 START 和 END：入口与出口
### 4.5 实战：构建一个带分支的问答路由器

---

## 第五章 Tool Calling —— 让 Agent 使用工具
<!-- 简述本章要点：工具定义、ToolNode、ReAct 循环 -->

### 5.1 定义工具（@tool 装饰器）
### 5.2 ToolNode —— 自动执行工具调用
### 5.3 ReAct 模式：思考 → 调用工具 → 观察 → 再思考
### 5.4 实战：构建一个能搜索网页 + 做数学计算的 Agent
### 5.5 工具错误处理与重试策略

---

## 第六章 持久化与检查点
<!-- 简述本章要点：MemorySaver、SQLite/PostgreSQL 持久化、对话历史管理 -->

### 6.1 为什么需要持久化 —— Agent 也需要"存档"
### 6.2 MemorySaver：最简单的内存检查点
### 6.3 SqliteSaver / PostgresSaver：生产级持久化
### 6.4 thread_id：多轮对话的会话管理
### 6.5 查看和回溯历史状态（get_state / get_state_history）

---

## 第七章 Human-in-the-Loop —— 人机协作
<!-- 简述本章要点：interrupt、人工审批、修改状态后恢复 -->

### 7.1 什么是 Human-in-the-Loop（人在回路中）
### 7.2 interrupt_before / interrupt_after —— 暂停执行
### 7.3 实战：工具调用前的人工审批
### 7.4 修改 State 后恢复执行（update_state）
### 7.5 动态断点：根据条件决定是否中断

---

## 第八章 子图与多智能体协作
<!-- 简述本章要点：SubGraph、Supervisor 模式、Handoff 模式 -->

### 8.1 子图（Subgraph）—— 图中嵌套图
### 8.2 Supervisor 模式 —— 一个"经理"调度多个"员工"
### 8.3 Handoff 模式 —— Agent 之间的任务交接
### 8.4 实战：构建一个研究 + 写作的双 Agent 系统
### 8.5 多智能体的 State 共享与隔离

---

## 第九章 Streaming —— 流式输出
<!-- 简述本章要点：流式Token、流式事件、实时展示Agent思考过程 -->

### 9.1 为什么需要 Streaming（用户体验 + 长任务监控）
### 9.2 stream_mode = "values" / "updates" / "messages"
### 9.3 astream_events —— 细粒度事件流
### 9.4 实战：在终端实时展示 Agent 的思考过程
### 9.5 与 Web 前端集成（FastAPI + SSE）

---

## 第十章 实战项目：自纠错 RAG Agent
<!-- 简述本章要点：从零构建一个完整的 Agentic RAG 系统 -->

### 10.1 项目目标与架构设计
### 10.2 构建检索节点（向量数据库 + Embedding）
### 10.3 构建评估节点（判断检索结果是否相关）
### 10.4 构建生成节点（基于上下文生成回答）
### 10.5 构建自纠错循环（不相关 → 重写查询 → 重新检索）
### 10.6 整合与测试

---

## 第十一章 生产部署与最佳实践
<!-- 简述本章要点：LangGraph Platform、错误处理、可观测性、性能优化 -->

### 11.1 LangGraph Platform / LangGraph Cloud 简介
### 11.2 错误处理与容错（节点重试、Fallback）
### 11.3 可观测性：LangSmith 集成（Trace / Debug / Monitor）
### 11.4 性能优化（节点缓存、并行执行、Deferred Nodes）
### 11.5 安全实践（Prompt 注入防护、工具权限控制）

---

## 附录

- A. LangGraph 常用 API 速查表
- B. State / Node / Edge 设计模式参考
- C. 常见错误与解决方案
- D. 推荐学习资源与官方文档链接
