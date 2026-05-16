# AI 应用的流式输出全链路

> 从 LLM 的第一个 Token 到用户屏幕上的逐字渲染——拆解流式输出的每一层。

---

## 1. 为什么流式输出是 AI 应用的标配
<!-- 要点：非流式 vs 流式的用户体验对比、Time to First Token（TTFT）概念、ChatGPT/Claude 的交互启示、流式输出的心理学（进度感知） -->

### 1.1 一个对比实验：等待 vs 逐字呈现
### 1.2 TTFT——衡量流式输出的核心指标
### 1.3 不只是快：流式输出的产品价值

---

## 2. LLM 的 Token 生成机制——流式的起点
<!-- 要点：自回归解码（Autoregressive Decoding）原理、为什么 LLM 天然就是"一个一个吐 Token"、Token ≠ 字 的编码细节、生成速度的影响因素 -->

### 2.1 自回归解码：一次只生成一个 Token
### 2.2 Token 编码：一个汉字可能是 1-3 个 Token
### 2.3 生成速度的影响因素

---

## 3. 流式传输协议——SSE、WebSocket、gRPC
<!-- 要点：三种主流流式传输协议的原理与对比、SSE（Server-Sent Events）详解、WebSocket 双向通信、gRPC 流式 RPC、AI 应用该选哪个 -->

### 3.1 SSE：最简单的服务器推送
### 3.2 WebSocket：双向实时通信
### 3.3 gRPC Streaming：高性能 RPC 流
### 3.4 三者对比与选型指南

---

## 4. LLM 提供商的流式 API——OpenAI / Anthropic / 开源
<!-- 要点：OpenAI stream=True 的 chunk 格式、Anthropic Messages Stream 事件类型、开源模型（vLLM/Ollama）的流式输出、统一封装多个提供商的流式接口 -->

### 4.1 OpenAI 流式 API 详解
### 4.2 Anthropic Claude 流式 API 详解
### 4.3 开源模型的流式输出（vLLM / Ollama）
### 4.4 统一封装：多提供商流式适配层

---

## 5. 后端流式中转——FastAPI / Node.js 实现
<!-- 要点：为什么需要后端中转（隐藏 API Key、加业务逻辑）、FastAPI StreamingResponse + asyncio.Queue、Node.js ReadableStream、流式中转的错误处理与超时 -->

### 5.1 为什么不能前端直连 LLM API
### 5.2 FastAPI 流式中转实战（Python）
### 5.3 Express / Next.js 流式中转实战（Node.js）
### 5.4 流式中转的错误处理与优雅降级

---

## 6. 前端流式渲染——从字节流到用户看到的文字
<!-- 要点：Fetch API + ReadableStream 解析 SSE、EventSource API、逐字渲染 vs 逐块渲染、流式 Markdown 增量解析与渲染、React/Vue 中的状态管理 -->

### 6.1 Fetch + ReadableStream：手动解析 SSE
### 6.2 EventSource API：浏览器原生方案
### 6.3 流式 Markdown 渲染的难点与方案
### 6.4 React 中的流式状态管理

---

## 7. 实战：构建一个完整的流式聊天应用
<!-- 要点：全栈实战项目，串联前 6 章知识。OpenAI API → FastAPI 中转 → React 前端。完整代码 + 运行演示 -->

### 7.1 项目架构与技术选型
### 7.2 后端：FastAPI 流式聊天 API
### 7.3 前端：React 流式聊天界面
### 7.4 完整运行演示

---

## 8. 生产级优化——延迟、错误、成本
<!-- 要点：TTFT 优化策略、流式连接断线重连、Token 用量监控与成本控制、并发流式请求的背压处理、缓存与预生成 -->

### 8.1 TTFT 优化：从请求到第一个 Token
### 8.2 断线重连与错误恢复
### 8.3 并发与背压控制
### 8.4 成本监控与流式计费

---

## 附录

### A. 流式输出 API 速查表
### B. 常见问题与排查
### C. 推荐工具与库
