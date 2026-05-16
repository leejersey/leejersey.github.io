# MCP 协议开发实战

> 从零构建你的第一个 MCP Server，让 AI 成为万能工具人。

---

## 1. MCP 是什么 —— AI 世界的 USB-C
<!-- 要点：MCP 协议的诞生背景、解决的核心问题（N×M → N+M）、"AI 的 USB-C" 类比、与传统 API/Function Calling 的区别 -->

### 1.1 从碎片化到标准化：为什么需要 MCP
### 1.2 MCP vs Function Calling vs Plugin —— 关键区别
### 1.3 谁在用 MCP？生态现状一览

---

## 2. MCP 架构解剖 —— Host、Client、Server
<!-- 要点：三层架构详解、JSON-RPC 2.0 通信协议、Transport 层（STDIO / HTTP+SSE）、完整的消息流转路径图 -->

### 2.1 Host / Client / Server 三角关系
### 2.2 JSON-RPC 2.0：MCP 的通信语言
### 2.3 Transport 层：STDIO vs HTTP+SSE

---

## 3. MCP 的三大原语 —— Tools、Resources、Prompts
<!-- 要点：三大原语的定义与区别、Tools（LLM 调用）、Resources（LLM 读取的上下文）、Prompts（可复用的提示模板）、何时用哪个 -->

### 3.1 Tools：让 AI 执行动作
### 3.2 Resources：给 AI 喂数据
### 3.3 Prompts：可复用的提示模板
### 3.4 三者的选型指南

---

## 4. 环境搭建与第一个 MCP Server（Python）
<!-- 要点：Python SDK 安装、项目结构、用 FastMCP 快速创建 Server、定义第一个 Tool、用 MCP Inspector 调试、连接 Claude Desktop -->

### 4.1 安装 Python MCP SDK
### 4.2 Hello MCP：5 分钟写一个天气查询 Server
### 4.3 用 MCP Inspector 调试
### 4.4 连接 Claude Desktop / Cursor

---

## 5. 深入 Tools —— 参数校验、异步、错误处理
<!-- 要点：@mcp.tool 装饰器详解、Pydantic 参数类型校验、异步工具函数、错误处理与用户友好提示、Tool 调用的完整生命周期 -->

### 5.1 @mcp.tool 装饰器全解析
### 5.2 参数校验与类型安全
### 5.3 异步工具与错误处理
### 5.4 实战：数据库查询工具

---

## 6. 深入 Resources —— 文件、数据库、API 数据源
<!-- 要点：@mcp.resource 定义与 URI 模板、静态 vs 动态 Resource、Resource 模板（参数化 URI）、实战：暴露文件系统和数据库表 -->

### 6.1 Resource 定义与 URI 规范
### 6.2 静态 Resource vs Resource 模板
### 6.3 实战：暴露本地文件和 SQLite 数据表

---

## 7. 深入 Prompts —— 可复用的提示工程
<!-- 要点：@mcp.prompt 装饰器、带参数的 Prompt 模板、多步骤 Prompt（返回消息列表）、Prompt 与 Tools/Resources 的组合使用 -->

### 7.1 定义 Prompt 模板
### 7.2 参数化 Prompt 与多轮消息
### 7.3 Prompts + Tools + Resources 的组合模式

---

## 8. TypeScript SDK —— 用 Node.js 构建 MCP Server
<!-- 要点：TypeScript SDK 安装与项目初始化、Zod schema 定义参数、TS 版本的 Tool/Resource/Prompt 写法对比、与 Python 版的异同 -->

### 8.1 TypeScript SDK 快速上手
### 8.2 用 Zod 定义类型安全的参数
### 8.3 Python vs TypeScript：选型建议

---

## 9. 实战项目：构建一个 GitHub 代码分析 MCP Server
<!-- 要点：综合项目，结合 Tools + Resources + Prompts。功能：查仓库信息、读文件内容、分析代码质量。完整代码 + 部署到 Claude Desktop -->

### 9.1 项目设计与架构
### 9.2 实现 Tools：仓库查询与文件读取
### 9.3 实现 Resources：暴露仓库结构
### 9.4 实现 Prompts：代码审查模板
### 9.5 完整集成与运行演示

---

## 10. 生产部署与安全
<!-- 要点：远程部署（HTTP+SSE Transport）、Docker 容器化、认证与授权、输入验证与安全边界、日志与监控 -->

### 10.1 从 STDIO 到 HTTP+SSE：远程部署
### 10.2 Docker 容器化部署
### 10.3 认证、授权与安全最佳实践
### 10.4 日志、监控与故障排查

---

## 附录

### A. MCP API 速查表（Python SDK）
### B. MCP API 速查表（TypeScript SDK）
### C. 常见报错与解决方案
### D. 推荐学习资源与社区
