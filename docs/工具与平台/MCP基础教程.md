# MCP 基础教程 (Model Context Protocol)

> 📅 创建时间：2026-02-07
> 🏷️ 标签：#AI #MCP #开发 #协议

---

## 一、什么是 MCP？

**MCP（Model Context Protocol，模型上下文协议）** 是由 Anthropic 于 2024 年 11 月推出的开放标准和开源框架。它旨在标准化 AI 系统（如大语言模型 LLM）与外部工具、系统和数据源的集成方式。

> 💡 **简单理解**：MCP 就像一个"万能适配器"，让 AI 应用（如 Claude、ChatGPT）可以安全地连接数据库、API、文件系统和各种业务工具。

### 核心价值

| 特性 | 说明 |
|------|------|
| 🔌 **通用接口** | 统一的方式读取文件、执行函数、处理上下文 |
| 🔒 **安全连接** | 双向加密，保护数据传输 |
| 🔄 **标准化** | 不同 AI 和工具之间的通用语言 |
| 🚀 **可扩展** | 轻松添加新的工具和数据源 |

---

## 二、谁在使用 MCP？

MCP 已获得广泛采用：

### AI 厂商
- **Anthropic** (Claude)
- **OpenAI** (ChatGPT)
- **Google DeepMind**

### 开发工具
- Cursor
- Replit
- Sourcegraph
- JetBrains 系列

### 应用平台
- Claude Desktop
- Figma
- Zapier
- Playwright

---

## 三、MCP 架构

MCP 的架构由三个核心组件组成：

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Host     │────▶│   Client    │────▶│   Server    │
│   (宿主)     │     │   (客户端)   │     │   (服务器)   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
  AI 应用程序          建立连接            提供工具/资源
  (如 Claude)        管理通信              数据源接口
```

### 工作流程

1. **Host（宿主）** 根据配置为每个 Server 启动一个 Client
2. **Client（客户端）** 连接到 Server 并获取可用的工具、资源和提示
3. **Server（服务器）** 提供具体的功能接口（如数据库查询、文件操作等）

---

## 四、快速开始

### 4.1 安装 SDK

根据你的开发语言选择对应的 SDK：

#### Python
```bash
pip install modelcontext
```

#### TypeScript / JavaScript
```bash
npm install @modelcontext/sdk
```

#### C# (.NET)
```bash
Install-Package ModelContext.SDK
```

#### Java (Maven)
```xml
<dependency>
    <groupId>io.modelcontext</groupId>
    <artifactId>mcp-sdk</artifactId>
    <version>latest</version>
</dependency>
```

### 4.2 官方 SDK 列表

| 语言 | 维护方 |
|------|--------|
| Python | Anthropic 官方 |
| TypeScript | Anthropic 官方 |
| C# | Microsoft 协作维护 |
| Kotlin | JetBrains 协作维护 |
| Ruby | Shopify 协作维护 |

---

## 五、创建第一个 MCP Server

以下是一个简单的 Python MCP Server 示例：

```python
from modelcontext import Server, Tool

# 创建服务器实例
server = Server("my-first-server")

# 定义一个工具
@server.tool("greet")
def greet(name: str) -> str:
    """向用户问好"""
    return f"你好，{name}！欢迎使用 MCP！"

# 定义另一个工具
@server.tool("calculate")
def calculate(a: int, b: int, operation: str) -> int:
    """执行简单计算"""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return a // b
    else:
        raise ValueError(f"未知操作: {operation}")

# 启动服务器
if __name__ == "__main__":
    server.run()
```

### TypeScript 版本

```typescript
import { Server, Tool } from "@modelcontext/sdk";

const server = new Server("my-first-server");

// 注册工具
server.registerTool({
  name: "greet",
  description: "向用户问好",
  parameters: {
    name: { type: "string", description: "用户名称" }
  },
  handler: async ({ name }) => {
    return `你好，${name}！欢迎使用 MCP！`;
  }
});

server.start();
```

---

## 六、MCP 核心概念

### 6.1 Tools（工具）

工具是 MCP 的核心功能单元，允许 AI 执行具体操作：

```python
@server.tool("search_database")
def search_database(query: str, limit: int = 10):
    """搜索数据库并返回结果"""
    # 实现搜索逻辑
    results = db.search(query, limit=limit)
    return results
```

### 6.2 Resources（资源）

资源代表可供 AI 访问的数据：

```python
@server.resource("user_profile/{user_id}")
def get_user_profile(user_id: str):
    """获取用户资料"""
    return database.get_user(user_id)
```

### 6.3 Prompts（提示）

预定义的提示模板：

```python
@server.prompt("code_review")
def code_review_prompt(code: str, language: str):
    """代码审查提示模板"""
    return f"""
    请审查以下 {language} 代码：

    ```{language}
    {code}
    ```

    请关注：代码质量、潜在 bug、性能优化建议。
    """
```

---

## 七、配置 MCP Client

在 Claude Desktop 或其他支持 MCP 的应用中配置：

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["path/to/my_server.py"],
      "env": {
        "API_KEY": "your-api-key"
      }
    },
    "database-server": {
      "command": "npx",
      "args": ["@company/db-mcp-server"],
      "env": {
        "DATABASE_URL": "postgresql://..."
      }
    }
  }
}
```

---

## 八、安全注意事项 ⚠️

MCP 设计时考虑了安全性，但仍需注意：

### 安全机制

| 机制 | 说明 |
|------|------|
| **OAuth 2.1** | 身份验证标准 |
| **最小权限原则** | 只授予必要的权限 |
| **人机协作** | 关键操作需要人工确认 |
| **PKCE** | 防止授权码劫持 |

### 潜在风险

1. **提示注入** - 恶意输入可能影响 AI 行为
2. **工具权限滥用** - 组合工具可能导致数据泄露
3. **工具伪装** - 假冒工具可能替换可信工具

### 最佳实践

- ✅ 定期审核已安装的 MCP Server
- ✅ 使用环境变量存储敏感信息
- ✅ 限制工具的访问范围
- ✅ 启用操作日志记录
- ✅ 对敏感操作启用二次确认

---

## 九、实用资源

### 官方资源
- 📖 [官方文档](https://modelcontextprotocol.io)
- 💻 [GitHub 仓库](https://github.com/modelcontextprotocol)
- 📋 [协议规范](https://modelcontextprotocol.io/specification/2025-11-25)

### 学习资源
- 📚 [Neo4j MCP 教程](https://neo4j.com/blog/developer/model-context-protocol/)
- 📖 [Microsoft Learn - MCP](https://learn.microsoft.com/en-us/agent-framework/user-guide/model-context-protocol/)
- 🎓 [MCP 开发者指南 2026](https://publicapis.io/blog/mcp-model-context-protocol-guide)

### 社区
- [MCP GitHub Discussions](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions)
- [Agentic AI Foundation](https://www.linuxfoundation.org) (MCP 现由 Linux 基金会托管)

---

## 十、总结

MCP 是连接 AI 与外部世界的桥梁。通过学习 MCP，你可以：

1. 🔧 为 AI 创建自定义工具
2. 📊 让 AI 访问你的数据库和 API
3. 🔄 实现 AI 工作流自动化
4. 🏗️ 构建更强大的 AI 应用

> **下一步**：尝试创建你的第一个 MCP Server，并将其连接到 Claude Desktop！

---

*本教程基于 MCP 2025-11 规范编写，最后更新：2026-02-07*
