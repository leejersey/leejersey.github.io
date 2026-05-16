# AI 应用开发完整学习指南

> **版本**：v2.1 | **更新日期**：2026-05-03 | **总学时**：约 20-30 周（核心路径）
>
> **目标受众**：有一定编程基础（Python/JavaScript），希望系统掌握 AI 应用开发全链路的开发者
>
> **前置要求**：基本的编程能力、命令行操作、Git 使用经验
>
> **学完你能**：独立开发包含 RAG、Agent、多模态能力的生产级 AI 应用，并完成部署上线

---

::: info
本大纲分为「**核心路径**」和「**进阶路径**」。标注 ⭐ 的章节为核心路径（必修），其余为进阶内容（可按需选学）。
核心路径约 14-18 周，完整路径约 20-30 周。
:::


---

## 一、基础知识储备

### 1.1 编程语言

→ [1.1 编程语言](1.1 编程语言)

- **Python 核心**（4-5 周）：变量/控制流/OOP → 装饰器/生成器/async-await → 类型提示
- **Web 开发**（2-3 周）：FastAPI 路由/Pydantic/依赖注入/流式响应/数据库集成
- **前端基础**（2-3 周）：HTML/CSS/JS → React 组件/Hooks → AI 聊天界面实战

### 1.2 机器学习基础

→ [1.2 机器学习基础](1.2 机器学习基础)

- **ML 概述**（1 周）：监督/无监督/强化学习、应用场景
- **常见算法**（2-3 周）：线性回归、决策树、SVM、神经网络
- **训练流程**（1-2 周）：数据准备 → 特征工程 → 训练 → 评估 → 部署
- **关键概念**（1-2 周）：过拟合/欠拟合、正则化、交叉验证

### 1.3 深度学习基础

→ [1.3 深度学习基础](1.3 深度学习基础)

- **神经网络原理**（2-3 周）：前向传播/反向传播/优化器/正则化
- **CNN**（2-3 周）：卷积/池化/经典架构（ResNet/EfficientNet）
- **RNN/LSTM**（2 周）：序列模型/门控机制/Bi-LSTM
- **Transformer** ⭐（3-4 周）：Self-Attention/Multi-Head/位置编码 — LLM 的基石
- **深度学习框架**（2-3 周）：PyTorch / TensorFlow

---

## 二、大语言模型（LLM）核心

### 2.1 LLM 基本原理

→ [2.1 LLM 基本原理](2.1 LLM 基本原理)

- **LLM 概述** ⭐（1 周）：发展历程、核心能力、局限性
- **Transformer 深入**（2-3 周）：编码器/解码器、KV Cache、MoE 架构
- **预训练与微调**（2-3 周）：预训练范式、SFT、RLHF/DPO
- **Tokenization**（1-2 周）：BPE/WordPiece/SentencePiece、词表设计
- **上下文窗口**（1-2 周）：位置编码扩展、长上下文处理策略

### 2.2 主流大模型

→ [2.2 主流大模型](2.2 主流大模型)

- **闭源模型** ⭐（1 周）：GPT-5 / Claude Opus 4.6 / Gemini 3 Pro / DeepSeek
- **开源模型**（2 周）：LLaMA / Qwen / DeepSeek-R1 / Phi
- **模型选型** ⭐（1 周）：按场景选型矩阵（国内 🇨🇳 / 国际 🌍 双方案）
- **多模型路由**：生产环境的动态选型策略

### 2.3 模型微调

→ [2.3 模型微调](2.3 模型微调)

- **微调策略**（1 周）：全参数 vs LoRA vs QLoRA、选择依据
- **数据集准备**（1-2 周）：标注格式、质量控制、数据增强
- **微调工具** ⭐（2-3 周）：LLaMA-Factory / Axolotl / HuggingFace PEFT
- **训练基础设施**（1-2 周）：GPU 选择、分布式训练、混合精度
- **模型评估**（1 周）：Benchmark / 人工评估 / LLM-as-Judge

### 2.4 模型部署与推理

→ [2.4 模型部署与推理](2.4 模型部署与推理)  |  [模型部署实战教程](模型部署实战教程)

- **推理优化**：量化（GPTQ/AWQ/GGUF）、KV Cache、连续批处理
- **部署框架** ⭐：vLLM / Ollama / llama.cpp / TGI
- **本地 vs 云端**：成本/性能/安全对比
- **性能监控**：吞吐量、延迟、GPU 利用率

---

## 三、Prompt 工程

### 3.1 Prompt 设计原则

→ [3.1 Prompt 设计原则](3.1 Prompt 设计原则)

- **基础原则** ⭐：角色设定、任务描述、格式要求、上下文提供
- **System Prompt 设计**：系统指令模板、安全边界设定
- **输出控制**：JSON 输出、Structured Output、格式约束
- **常见错误与最佳实践**

### 3.2 高级 Prompt 技术

→ [3.2 高级 Prompt 技术](3.2 高级 Prompt 技术)

- **Few-shot Learning** ⭐：示例选择策略、动态 Few-shot
- **Chain-of-Thought** ⭐：思维链推理、Zero-shot CoT
- **Self-Consistency**：多路径推理、投票机制
- **Tree of Thoughts**：树状搜索、复杂问题分解
- **Prompt 模板设计**：结构化模板、变量注入
- **A/B 测试与迭代优化**

### 3.3 结构化输出 ⭐

→ [3.3 结构化输出](3.3 结构化输出)

- **JSON Mode / Structured Outputs**：OpenAI 原生结构化输出
- **Instructor 库** ⭐：多模型通用、自动重试、Pydantic 校验
- **高级技巧**：枚举约束 / 嵌套结构 / 流式结构化输出
- **典型场景**：信息提取 / 分类 / 内容审核 / Agent 工具参数

---

## 四、RAG 检索增强生成

### 4.1 RAG 核心架构

→ [4.1 RAG 核心架构](4.1 RAG 核心架构)

- **RAG 原理** ⭐：检索→增强→生成的完整流程
- **核心组件**：文档加载器 / 分块器 / Embedding / 向量数据库 / LLM
- **评估指标**：Recall@K / MRR / Faithfulness / Relevancy
- **常见问题与优化技巧**

### 4.2 向量数据库

→ [4.2 向量数据库](4.2 向量数据库)  |  [向量数据库实战（完整教程）](../向量数据库实战/向量数据库实战大纲)

- **Embedding 模型选型** ⭐：OpenAI / BGE / Cohere、维度与性能
- **向量数据库选型** ⭐：pgvector vs Chroma vs Milvus
- **相似度检索**：余弦距离 / 欧氏距离 / HNSW / IVFFlat
- **性能优化**：索引调优、批量写入、缓存策略

### 4.3 文档处理

→ [4.3 文档处理](4.3 文档处理)

- **文档解析**：PDF / Markdown / HTML / 代码文件
- **分块策略** ⭐：递归字符 / 语义分块 / 按结构分块 / Parent Document
- **元数据提取**：标题/来源/时间戳 → 过滤检索
- **高级技巧**：OCR、表格提取、多模态文档

### 4.4 高级 RAG 技术

→ [4.4 高级 RAG 技术](4.4 高级 RAG 技术)

- **查询优化**：Query Rewriting / HyDE / 多查询扩展
- **检索优化**：混合检索（Dense + Sparse）/ Reranker
- **生成优化**：引用溯源 / 幻觉检测 / 自适应 RAG
- **RAG 评估**：RAGAS 框架、端到端评测

### 4.5 数据工程与 ETL

→ [4.5 数据工程与 ETL](4.5 数据工程与 ETL)

- **数据采集**：多源接入（文件 / 数据库 / API / 爬虫）
- **数据清洗**：文本标准化 / PII 脱敏 / 元数据提取
- **质量检查**：空值 / 重复 / 编码 / 长度自动校验
- **ETL Pipeline 实战**：采集 → 清洗 → 质量检查 → 入库

---

## 五、AI Agent（智能体）

### 5.1 Agent 基础概念

→ [5.1 Agent 基础概念](5.1 Agent 基础概念)

- **什么是 Agent** ⭐：LLM + 记忆 + 工具 + 规划
- **四大核心组件**：大脑（LLM）/ 记忆 / 工具 / 规划器
- **ReAct 模式** ⭐：Thought → Action → Observation 循环
- **单 Agent vs 多 Agent 协作**

### 5.2 Agent 开发框架

→ [5.2 Agent 开发框架](5.2 Agent 开发框架)

- **框架对比** ⭐：LangChain / LangGraph / CrewAI / AutoGen / Dify
- **LangChain Agent** ⭐：工具定义 / Agent 创建 / 执行链
- **LangGraph** ⭐：状态图 / 条件分支 / 人机协作（Human-in-the-loop）
- **CrewAI**：角色化多 Agent 协作

### 5.3 工具使用（Function Calling / MCP）

→ [5.3 工具使用（Function Calling）](5.3 工具使用（Function Calling）)

- **OpenAI Function Calling** ⭐：工具定义 / 参数生成 / 多工具并行
- **自定义工具开发**：API 调用 / 数据库查询 / 文件操作
- **MCP 协议** ⭐：Server/Client 架构 / `mcp` SDK / Claude Desktop 集成
- **Function Calling vs Tool Call vs MCP 辨析**
- **工具设计最佳实践**

### 5.4 记忆与状态管理

→ [5.4 记忆与状态管理](5.4 记忆与状态管理)

- **记忆类型**：短期（对话历史）/ 长期（向量存储）/ 工作记忆
- **对话历史管理**：滑动窗口 / 摘要压缩 / Token 预算控制
- **持久化存储**：Redis / PostgreSQL / 向量数据库
- **LangGraph 状态管理**：TypedDict / Checkpointer

### 5.5 Agent 规划与执行

→ [5.5 Agent 规划与执行](5.5 Agent 规划与执行)

- **规划策略**：Task Decomposition / Plan-and-Execute / 自适应规划
- **执行引擎**：顺序执行 / 并行执行 / 条件分支
- **错误恢复**：重试机制 / Fallback 策略 / 人工干预
- **评估与调试**：Agent 日志 / 轨迹分析 / 性能基准

### 5.6 Agent 架构设计

→ [5.6 Agent 架构设计](5.6 Agent 架构设计)

- **六大架构模式**：单 Agent / Supervisor / Hierarchical / Swarm / Map-Reduce / Reflection
- **架构选型指南**：按任务类型选择最佳拓扑
- **可靠性工程**：工具调用防护 / 循环保护 / Human-in-the-Loop
- **Agentic RAG**：Agent 驱动的自适应检索策略

---

## 六、多模态应用

### 6.1 视觉模型

→ [6.1 视觉模型](6.1 视觉模型)

- **图像理解**：GPT-5 Vision / Gemini Pro Vision / Qwen-VL
- **图像生成**：DALL-E / Stable Diffusion / Midjourney API
- **应用场景**：商品识别、文档 OCR、医疗影像分析

### 6.2 语音模型

→ [6.2 语音模型](6.2 语音模型)

- **语音识别（ASR）**：Whisper / 讯飞 / Azure Speech
- **语音合成（TTS）**：OpenAI TTS / Edge TTS / VITS
- **实时对话**：GPT-5 Realtime API / WebSocket 流式处理

### 6.3 视频生成

→ [6.3 视频生成](6.3 视频生成)

- **视频生成模型**：Sora / Runway / Pika
- **视频理解**：Gemini 3 Pro（原生视频输入）
- **应用开发**：短视频生成管线、视频内容分析

---

## 七、工程化实践与部署

### 7.1 API 服务设计 ⭐

→ [7.1 API 服务设计](7.1 API 服务设计)

- LLM 应用架构模式（同步 / 异步任务 / 流式 SSE）
- 流式输出（SSE / WebSocket 双向对话）
- 限流、重试与降级策略（SlowAPI + tenacity + Fallback Chain）
- 多模型路由与负载均衡（规则路由 + 语义缓存）
- 综合实战：生产级 LLM 服务（认证 + 限流 + 路由 + 流式 + 监控）


### 7.2 安全与内容审核 ⭐

→ [7.2 安全与内容审核](7.2 安全与内容审核)

- 用户数据隐私保护（PII 脱敏、对话隔离）
- Prompt 注入防护（多层防御、输入过滤、越狱检测）
- 内容安全审核（敏感词 + 分类模型 + OpenAI Moderation）
- AI 伦理与合规（GDPR、《个人信息保护法》、《生成式 AI 管理办法》）


### 7.3 性能优化 ⭐

→ [7.3 性能优化](7.3 性能优化)

- 缓存策略（精确匹配 → 语义缓存 → Prompt 前缀缓存 三级架构）
- 并发与异步处理（asyncio + 信号量 + 批处理）
- Token 用量优化与成本控制（Prompt 压缩、模型降级、预算告警）
- 监控与可观测性（LangSmith / Langfuse / 自定义指标）


### 7.4 部署上线

→ [7.4 部署上线](7.4 部署上线)

- Docker 容器化（Dockerfile 最佳实践、多阶段构建）
- Docker Compose 三容器编排（Nginx + FastAPI + PostgreSQL/pgvector）
- 环境变量与密钥管理（pydantic-settings）
- CI/CD 自动部署（GitHub Actions / Webhook）
- 日志与监控（结构化日志、健康检查）
- 部署检查清单

### 7.5 前端交互设计

→ [7.5 前端交互设计](7.5 前端交互设计)

- 对话式 UI 设计（消息列表 / 气泡 / 头像 / 操作按钮）
- 流式打字效果实现（SSE 解析 + 逐字渲染）
- Markdown 与代码高亮渲染（react-markdown + highlight.js）
- 文件上传与多模态输入（图片/PDF + 拖拽上传）
- 综合实战：完整 Chat 应用前端

### 7.6 AI 应用测试

→ [7.6 AI 应用测试](7.6 AI 应用测试)

- **测试金字塔**：单元测试 / 集成测试 / 端到端测试
- **LLM 输出评估**：DeepEval + LLM-as-Judge
- **Prompt 回归测试**：关键词检查 / 长度约束 / 安全测试
- **CI/CD 集成**：GitHub Actions 自动化评估

### 7.7 成本控制

→ [7.7 成本控制](7.7 成本控制)

- **模型选型降本**：按任务复杂度自动选模型
- **Token 优化**：Prompt 压缩 / 上下文裁剪
- **缓存策略**：精确缓存 + API 侧前缀缓存
- **监控预警**：日预算 / Token 追踪 / 超支告警

---

## 八、实战项目

### 8.1 AI 聊天应用 ⭐

→ [8.1 AI 聊天应用](8.1 AI 聊天应用)

- 意图识别 → RAG 知识库 → 工具调用 → 多轮对话 → 流式输出
- 技术栈：FastAPI + OpenAI + pgvector
- 完整服务入口代码（可直接运行）

### 8.2 知识库问答系统（RAG）⭐

→ [8.2 知识库问答系统](8.2 知识库问答系统)

- 多格式文档解析（PDF/Markdown/HTML/代码）
- 智能分块 → 混合检索 + Reranker → 引用溯源生成
- 技术栈：LangChain + pgvector/Milvus + FastAPI
- 完整系统实现（可直接部署）

### 8.3 AI Agent 助手

→ [8.3 AI Agent 助手](8.3 AI Agent 助手)

- Agent 自动化编码（Plan → Execute → Auto-fix 循环）
- 数据分析自动化 + 多 Agent 协作 + RPA 集成
- 技术栈：LangGraph + MCP + FastAPI
- 统一编排与可观测性

### 8.4 多模态应用

→ [8.4 多模态应用](8.4 多模态应用)

- 结构化长文/报告/PPT 生成（大纲→逐章→整合）
- 多模态内容创作（文本+图像+语音联合生成）
- 写作风格迁移与一致性控制
- FastAPI 流式输出服务

### 8.5 数据分析 Agent

→ [8.5 数据分析 Agent](8.5 数据分析 Agent)

- 代码生成与补全 / 代码审查与解释
- 自然语言转 SQL（Text-to-SQL）
- Agent 自动化编码（Plan → Execute → Auto-fix）
- FastAPI 完整服务实现

---

## 九、前沿方向与持续学习

### 9.1 MCP 与 A2A 协议

→ [9.1 MCP 与 A2A](9.1 MCP 与 A2A)

- **MCP**：Agent ↔ 工具/数据的标准接口（纵向连接）
- **A2A**：Agent ↔ Agent 的通信协议（横向连接，Google 发起）
- MCP Server 开发实战 + Claude Desktop/Cursor 集成
- A2A Agent Card + 跨框架 Agent 协作
- 两者互补，构成 Agent 生态基础设施

### 9.2 推理模型（Slow Thinking）

→ [9.2 推理模型](9.2 推理模型)

- 快思考 vs 慢思考对比 + 主流推理模型矩阵
- OpenAI o3 / DeepSeek-R1 / Qwen3 混合思考实战代码
- 生产实践：混合路由策略（按复杂度自动选模型）
- 对应用开发的 4 大影响（Prompt/成本/超时/流式输出）

### 9.3 代码生成与 AI IDE

→ [9.3 代码生成与 AI IDE](9.3 代码生成与 AI IDE)

- 主流工具对比（Cursor / Copilot / Windsurf / Claude Code）
- AI-First 开发范式（自然语言驱动 + 对话式迭代）
- Cursor 深度指南（Agent 模式 + .cursorrules 规范）
- Claude Code CLI Agent + MCP 集成

### 9.4 AI 搜索

→ [9.4 AI 搜索](9.4 AI 搜索)

- AI 搜索 vs 传统搜索 vs RAG 三方对比
- 主流产品（Perplexity / SearchGPT / Kimi 搜索）
- 集成方式：OpenAI Web Search / Perplexity API / 自建搜索
- RAG + AI 搜索混合检索实战

### 9.5 个性化与微调生态

→ [9.5 个性化与微调生态](9.5 个性化与微调生态)

- 合成数据生成（GPT-4o 批量生成 + 质量过滤 + 格式导出）
- LoRA 微调实战（LLaMA-Factory 完整配置）
- 评估与迭代（LLM-as-Judge + 闭环流程）
- LoRA 即服务（vLLM 多 LoRA 热切换部署）

### 9.6 AI 安全与对齐

→ [9.6 AI 安全与对齐](9.6 AI 安全与对齐)

- 安全四层体系（模型→应用→内容→合规）
- 模型对齐技术（RLHF / DPO / Constitutional AI）
- 红队测试自动化（攻击向量 + 自动化脚本）
- AI 内容标识与 C2PA 水印
- 中国 + 国际法规合规清单

### 9.7 AI 基础设施（LLMOps）

→ [9.7 AI 基础设施](9.7 AI 基础设施)

- **AI 网关**：LiteLLM 统一接口 + Fallback 容错链 + Proxy 部署
- **可观测性**：LangSmith / Langfuse — 调用链路追踪
- **Prompt Caching**：前缀缓存节省 50-90% 成本
- **评估系统**：RAGAS（RAG 评估）+ DeepEval（通用评估）
- 团队规模选型指南

---

## 学习路径建议

### ⭐ 核心路径（14-18 周）— 快速上手 AI 应用开发

适合有编程基础的开发者，聚焦「会用」，快速产出 AI 应用。

```
阶段零（1天）：环境搭建 + 5分钟体验 API 调用
    ↓
阶段一（1-2周）：Python 核心 + FastAPI 基础（1.1 精选）
    ↓
阶段二（2-3周）：LLM 概念 + Prompt 工程（2.1 概述 + 3.1-3.2）⭐
    ↓
阶段三（3-4周）：RAG 系统开发（4.1-4.4）⭐
    ↓
阶段四（3-4周）：Agent 开发 + Function Calling + MCP（5.1-5.3）⭐
    ↓
阶段五（2-3周）：工程化实践 + 部署上线（7.1-7.4 精选）⭐
    ↓
阶段六（2-3周）：项目实战（选一个完整项目）
```

### 完整路径（20-30 周）— 系统掌握全链路

在核心路径基础上，深入理论和进阶主题：

```
+ ML/DL 基础（1.2-1.3，重点 Transformer）：2-3 周
+ 模型微调（2.3 LoRA/QLoRA 实战）：2-3 周
+ 模型部署（2.4 vLLM/Ollama）：2-3 周
+ 多模态应用（6.1-6.3）：2-3 周
+ Agent 进阶（5.4-5.6 记忆/规划/架构）：2-3 周
+ 前沿方向（9.x MCP/A2A/推理模型）：持续跟踪
```

::: tip
全程使用 **AI 编程工具**（Cursor / Copilot）辅助学习和实践，可大幅提升效率。
每学完一个章节，用 AI 辅助做一个 Mini 项目巩固所学。
:::


---

## 推荐资源

| 类型 | 资源 | 说明 |
|------|------|------|
| 课程 | [吴恩达 AI 系列](https://www.deeplearning.ai/) | Prompt 工程、LangChain、RAG 等系统课程 |
| 课程 | [李宏毅机器学习](https://speech.ee.ntu.edu.tw/~hylee/ml/2023-spring.php) | 中文深度学习入门首选 |
| 文档 | [OpenAI API 文档](https://platform.openai.com/docs) | API 调用与最佳实践 |
| 文档 | [LangChain 官方文档](https://docs.langchain.com/) | Agent 与链式开发 |
| 文档 | [MCP 官方文档](https://modelcontextprotocol.io/) | Agent 工具标准协议 |
| 社区 | [Hugging Face](https://huggingface.co/) | 模型与数据集中心 |
| 榜单 | [Chatbot Arena](https://chat.lmsys.org/) | 模型实力实时对战排名 |
| 实战 | [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) | 开源模型微调一站式平台 |
| 平台 | [Dify](https://dify.ai/) | 低代码 AI 应用构建 |
| 工具 | [Cursor](https://cursor.com/) | AI-native IDE，推荐全程使用 |
| 工具 | [Ollama](https://ollama.com/) | 本地模型运行，开发必备 |
