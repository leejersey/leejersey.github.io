# MCP 协议开发实战

> 从零构建你的第一个 MCP Server，让 AI 成为万能工具人。

---

## 9. 实战项目：构建一个 GitHub 代码分析 MCP Server

前面 8 章，我们一块一块地学了 MCP 的每个组件。这一章，把它们全部串起来——从零构建一个**能查 GitHub 仓库、读代码文件、分析代码质量**的完整 MCP Server。

---

### 9.1 项目设计与架构

### 功能需求

```
GitHub 代码分析助手——功能清单：

  🔧 Tools（AI 调用的操作）：
    • get_repo_info     → 查询仓库基本信息（star、fork、描述）
    • search_repos      → 搜索 GitHub 仓库
    • get_file_content  → 读取仓库中的指定文件
    • list_repo_files   → 列出仓库的文件结构

  📄 Resources（提供的上下文数据）：
    • github://repos/{owner}/{repo}/readme  → 仓库 README
    • github://repos/{owner}/{repo}/structure → 仓库文件结构

  💬 Prompts（标准化模板）：
    • code_review       → 代码审查模板
    • repo_analysis      → 仓库综合分析模板
```

### 技术架构

```
架构概览：

  ┌───────────────────────────────────────────┐
  │            GitHub MCP Server               │
  │                                             │
  │  ┌─────────┐  ┌──────────┐  ┌──────────┐  │
  │  │  Tools  │  │ Resources│  │ Prompts  │  │
  │  │ 4 个工具 │  │ 2 个资源  │  │ 2 个模板  │  │
  │  └────┬────┘  └────┬─────┘  └────┬─────┘  │
  │       │            │              │         │
  │       └────────────┼──────────────┘         │
  │                    │                         │
  │            ┌───────┴───────┐                │
  │            │  GitHub API   │                │
  │            │  (httpx)      │                │
  │            └───────────────┘                │
  └───────────────────────────────────────────┘
            │
            ↓
  ┌───────────────────┐
  │   GitHub REST API  │
  │   api.github.com   │
  └───────────────────┘
```

### 项目结构

```
github-mcp-server/
├── pyproject.toml          ← 项目配置和依赖
├── server.py               ← 主入口
├── github_client.py        ← GitHub API 封装
└── README.md               ← 项目说明
```

### 依赖安装

```bash
mkdir github-mcp-server && cd github-mcp-server
uv init
uv add "mcp[cli]" httpx
```

### GitHub API 客户端封装

先创建一个简洁的 GitHub API 客户端，供 Tool 和 Resource 调用：

```python
# github_client.py —— GitHub API 封装
import httpx
from typing import Any

GITHUB_API = "https://api.github.com"

class GitHubClient:
    def __init__(self, token: str | None = None):
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"
        self.client = httpx.AsyncClient(
            base_url=GITHUB_API,
            headers=headers,
            timeout=30.0,
        )

    async def get_repo(self, owner: str, repo: str) -> dict:
        """获取仓库信息"""
        resp = await self.client.get(f"/repos/{owner}/{repo}")
        resp.raise_for_status()
        return resp.json()

    async def get_readme(self, owner: str, repo: str) -> str:
        """获取仓库 README 内容"""
        resp = await self.client.get(
            f"/repos/{owner}/{repo}/readme",
            headers={"Accept": "application/vnd.github.raw+json"}
        )
        resp.raise_for_status()
        return resp.text

    async def get_file(self, owner: str, repo: str, path: str) -> str:
        """获取仓库中指定文件的内容"""
        resp = await self.client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            headers={"Accept": "application/vnd.github.raw+json"}
        )
        resp.raise_for_status()
        return resp.text

    async def get_tree(self, owner: str, repo: str) -> list[str]:
        """获取仓库文件树"""
        resp = await self.client.get(
            f"/repos/{owner}/{repo}/git/trees/HEAD",
            params={"recursive": "1"}
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["path"] for item in data.get("tree", [])
                if item["type"] == "blob"]

    async def search_repos(self, query: str, limit: int = 5) -> list[dict]:
        """搜索仓库"""
        resp = await self.client.get(
            "/search/repositories",
            params={"q": query, "per_page": limit, "sort": "stars"}
        )
        resp.raise_for_status()
        return resp.json().get("items", [])
```

> **关于 GitHub Token**：不带 Token 也能用，但有速率限制（60 次/小时）。建议设置环境变量 `GITHUB_TOKEN` 来解除限制（5000 次/小时）。

---

### 9.2 实现 Tools：仓库查询与文件读取

在 `server.py` 中注册 4 个 Tool，全部使用 async 调用 GitHub API：

```python
# server.py —— GitHub 代码分析 MCP Server（Tool 部分）
import os
from mcp.server.fastmcp import FastMCP, Context
from github_client import GitHubClient

mcp = FastMCP("GitHub 代码分析")

# 初始化 GitHub 客户端
github = GitHubClient(token=os.getenv("GITHUB_TOKEN"))

# ═══════════════════════════════════════════
# Tool 1：查询仓库信息
# ═══════════════════════════════════════════

@mcp.tool()
async def get_repo_info(owner: str, repo: str) -> str:
    """查询 GitHub 仓库的基本信息。

    Args:
        owner: 仓库所有者，如 'anthropics'
        repo: 仓库名称，如 'mcp'
    """
    try:
        data = await github.get_repo(owner, repo)
        return (
            f"📦 {data['full_name']}\n"
            f"📝 描述：{data.get('description', '无')}\n"
            f"⭐ Stars：{data['stargazers_count']}\n"
            f"🍴 Forks：{data['forks_count']}\n"
            f"👁️ Watchers：{data['watchers_count']}\n"
            f"🔤 主语言：{data.get('language', '未知')}\n"
            f"📅 创建时间：{data['created_at'][:10]}\n"
            f"🔄 最后更新：{data['updated_at'][:10]}\n"
            f"🔗 链接：{data['html_url']}"
        )
    except Exception as e:
        return f"❌ 查询失败：{str(e)}"

# ═══════════════════════════════════════════
# Tool 2：搜索仓库
# ═══════════════════════════════════════════

@mcp.tool()
async def search_repos(
    query: str,
    limit: int = 5,
    ctx: Context = None
) -> str:
    """搜索 GitHub 仓库，按 star 数排序。

    Args:
        query: 搜索关键词，如 'mcp server python'
        limit: 返回结果数量，默认 5，最大 10
    """
    limit = min(limit, 10)
    if ctx:
        ctx.info(f"搜索仓库：{query}")

    try:
        repos = await github.search_repos(query, limit)
        if not repos:
            return f"没有找到与 '{query}' 相关的仓库"

        result = f"🔍 搜索 '{query}' 的结果（{len(repos)} 个）：\n\n"
        for i, r in enumerate(repos, 1):
            result += (
                f"  {i}. {r['full_name']} ⭐{r['stargazers_count']}\n"
                f"     {r.get('description', '无描述')}\n"
                f"     🔗 {r['html_url']}\n\n"
            )
        return result
    except Exception as e:
        return f"❌ 搜索失败：{str(e)}"

# ═══════════════════════════════════════════
# Tool 3：读取文件内容
# ═══════════════════════════════════════════

@mcp.tool()
async def get_file_content(owner: str, repo: str, path: str) -> str:
    """读取 GitHub 仓库中指定文件的内容。

    Args:
        owner: 仓库所有者
        repo: 仓库名称
        path: 文件路径，如 'src/main.py' 或 'README.md'
    """
    try:
        content = await github.get_file(owner, repo, path)
        # 限制返回内容长度，避免超出上下文窗口
        if len(content) > 10000:
            content = content[:10000] + f"\n\n... （文件太长，已截断。总长度：{len(content)} 字符）"
        return f"📄 {owner}/{repo}/{path}\n\n{content}"
    except Exception as e:
        return f"❌ 读取失败：{str(e)}"

# ═══════════════════════════════════════════
# Tool 4：列出文件结构
# ═══════════════════════════════════════════

@mcp.tool()
async def list_repo_files(
    owner: str,
    repo: str,
    filter_ext: str = ""
) -> str:
    """列出仓库的文件结构。

    Args:
        owner: 仓库所有者
        repo: 仓库名称
        filter_ext: 按扩展名过滤，如 '.py'、'.ts'（为空则列出所有）
    """
    try:
        files = await github.get_tree(owner, repo)

        if filter_ext:
            files = [f for f in files if f.endswith(filter_ext)]

        if not files:
            return f"仓库中没有找到文件" + (f"（过滤：{filter_ext}）" if filter_ext else "")

        result = f"📁 {owner}/{repo} 文件结构"
        if filter_ext:
            result += f"（仅 {filter_ext} 文件）"
        result += f"（共 {len(files)} 个文件）：\n\n"

        for f in files[:100]:  # 最多显示 100 个
            result += f"  {f}\n"

        if len(files) > 100:
            result += f"\n  ... 还有 {len(files) - 100} 个文件未显示"

        return result
    except Exception as e:
        return f"❌ 获取文件列表失败：{str(e)}"
```

```
4 个 Tool 的设计思路：

  get_repo_info   → 快速了解一个仓库的"身份证"
  search_repos    → 发现相关仓库
  get_file_content → 深入阅读具体代码
  list_repo_files  → 了解仓库结构，知道有哪些文件

  这 4 个 Tool 构成了一个完整的"探索"流程：
  搜索 → 了解 → 浏览结构 → 阅读代码
```

---

### 9.3 实现 Resources：暴露仓库结构

继续在 `server.py` 中添加 Resource，让 AI 能被动地"看到"仓库数据：

```python
# ═══════════════════════════════════════════
# Resource 模板：仓库 README
# ═══════════════════════════════════════════

@mcp.resource("github://repos/{owner}/{repo}/readme")
async def repo_readme(owner: str, repo: str) -> str:
    """GitHub 仓库的 README 文档

    Args:
        owner: 仓库所有者
        repo: 仓库名称
    """
    try:
        return await github.get_readme(owner, repo)
    except Exception as e:
        return f"无法获取 README：{str(e)}"

# ═══════════════════════════════════════════
# Resource 模板：仓库文件结构
# ═══════════════════════════════════════════

@mcp.resource("github://repos/{owner}/{repo}/structure")
async def repo_structure(owner: str, repo: str) -> str:
    """GitHub 仓库的完整文件结构

    Args:
        owner: 仓库所有者
        repo: 仓库名称
    """
    try:
        files = await github.get_tree(owner, repo)
        result = f"{owner}/{repo} 文件结构（{len(files)} 个文件）：\n\n"
        for f in files[:200]:
            result += f"{f}\n"
        if len(files) > 200:
            result += f"\n... 还有 {len(files) - 200} 个文件"
        return result
    except Exception as e:
        return f"无法获取文件结构：{str(e)}"
```

```
为什么 README 和文件结构用 Resource 而不是 Tool？

  Resource 的语义是"上下文数据"：
    → README 是了解项目的背景信息
    → 文件结构是浏览代码的导航地图
    → 这些是 AI 做决策前需要"看到"的数据
    → Host 可以自动加载，不需要 AI 主动请求

  Tool 的语义是"主动操作"：
    → get_file_content 是按需读取特定文件
    → search_repos 是主动搜索
    → 需要 AI 判断"我现在应该调用它"
```

---

### 9.4 实现 Prompts：代码审查模板

添加 2 个标准化的 Prompt 模板：

```python
# ═══════════════════════════════════════════
# Prompt 1：代码审查
# ═══════════════════════════════════════════

@mcp.prompt()
async def code_review(
    owner: str,
    repo: str,
    filepath: str,
    focus: str = "全面审查"
) -> str:
    """审查 GitHub 仓库中的指定代码文件。

    Args:
        owner: 仓库所有者
        repo: 仓库名称
        filepath: 要审查的文件路径
        focus: 审查重点，如 '全面审查'、'安全性'、'性能'
    """
    try:
        code = await github.get_file(owner, repo, filepath)
    except Exception as e:
        return f"无法获取文件内容：{str(e)}"

    # 推断语言
    ext_lang = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".go": "Go", ".rs": "Rust", ".java": "Java",
    }
    ext = "." + filepath.rsplit(".", 1)[-1] if "." in filepath else ""
    language = ext_lang.get(ext, "未知语言")

    return f"""请对以下来自 {owner}/{repo} 的 {language} 代码进行审查。

📄 文件：{filepath}
🎯 审查重点：{focus}

```{ext.lstrip('.')}
{code[:8000]}
```

请从以下维度给出评价和具体改进建议：
1. 代码质量与可读性
2. 错误处理与健壮性
3. 性能考量
4. 安全性
5. 最佳实践

对每个问题指出具体代码行，并给出修改后的示例代码。"""

# ═══════════════════════════════════════════
# Prompt 2：仓库综合分析
# ═══════════════════════════════════════════

@mcp.prompt()
async def repo_analysis(owner: str, repo: str) -> str:
    """对 GitHub 仓库进行综合分析报告。

    Args:
        owner: 仓库所有者
        repo: 仓库名称
    """
    try:
        info = await github.get_repo(owner, repo)
        readme = await github.get_readme(owner, repo)
        files = await github.get_tree(owner, repo)
    except Exception as e:
        return f"无法获取仓库数据：{str(e)}"

    # 统计文件类型
    ext_count: dict[str, int] = {}
    for f in files:
        ext = f.rsplit(".", 1)[-1] if "." in f else "无扩展名"
        ext_count[ext] = ext_count.get(ext, 0) + 1
    top_exts = sorted(ext_count.items(), key=lambda x: -x[1])[:10]

    return f"""请对以下 GitHub 仓库进行综合分析，生成一份结构化的分析报告。

📦 仓库：{info['full_name']}
📝 描述：{info.get('description', '无')}
⭐ Stars：{info['stargazers_count']} | 🍴 Forks：{info['forks_count']}
🔤 主语言：{info.get('language', '未知')}
📁 文件数量：{len(files)}

文件类型分布：
{chr(10).join(f'  .{ext}: {count} 个' for ext, count in top_exts)}

README 内容（摘要）：
{readme[:3000]}

请输出以下分析报告：
1. 📌 项目概述（用途、目标用户、核心功能）
2. 🏗️ 技术栈分析（使用的语言、框架、工具）
3. 📁 代码结构评价（组织是否合理、模块划分）
4. 📊 项目健康度（活跃度、文档质量、社区参与）
5. 💡 改进建议（3-5 条具体可行的建议）
6. 🏆 总评（一句话总结）"""
```

---

### 9.5 完整集成与运行演示

前面的代码分散在不同代码块中，这里给出完整的 `server.py` 入口文件——把 Tool、Resource、Prompt 全都集成在一起：

```python
# server.py —— GitHub 代码分析 MCP Server（完整版）
import os
from mcp.server.fastmcp import FastMCP, Context
from github_client import GitHubClient

mcp = FastMCP("GitHub 代码分析")
github = GitHubClient(token=os.getenv("GITHUB_TOKEN"))

# ═══════════════════════════════════════════
# Tools（4 个工具 —— 见 9.2 节的完整实现）
# ═══════════════════════════════════════════

@mcp.tool()
async def get_repo_info(owner: str, repo: str) -> str:
    """查询 GitHub 仓库的基本信息。"""
    # ... 实现见 9.2 节

@mcp.tool()
async def search_repos(query: str, limit: int = 5, ctx: Context = None) -> str:
    """搜索 GitHub 仓库，按 star 数排序。"""
    # ... 实现见 9.2 节

@mcp.tool()
async def get_file_content(owner: str, repo: str, path: str) -> str:
    """读取 GitHub 仓库中指定文件的内容。"""
    # ... 实现见 9.2 节

@mcp.tool()
async def list_repo_files(owner: str, repo: str, filter_ext: str = "") -> str:
    """列出仓库的文件结构。"""
    # ... 实现见 9.2 节

# ═══════════════════════════════════════════
# Resources（2 个资源模板 —— 见 9.3 节）
# ═══════════════════════════════════════════

@mcp.resource("github://repos/{owner}/{repo}/readme")
async def repo_readme(owner: str, repo: str) -> str:
    """GitHub 仓库的 README 文档"""
    # ... 实现见 9.3 节

@mcp.resource("github://repos/{owner}/{repo}/structure")
async def repo_structure(owner: str, repo: str) -> str:
    """GitHub 仓库的完整文件结构"""
    # ... 实现见 9.3 节

# ═══════════════════════════════════════════
# Prompts（2 个模板 —— 见 9.4 节）
# ═══════════════════════════════════════════

@mcp.prompt()
async def code_review(owner: str, repo: str, filepath: str, focus: str = "全面审查") -> str:
    """审查 GitHub 仓库中的指定代码文件。"""
    # ... 实现见 9.4 节

@mcp.prompt()
async def repo_analysis(owner: str, repo: str) -> str:
    """对 GitHub 仓库进行综合分析报告。"""
    # ... 实现见 9.4 节

# ═══════════════════════════════════════════
# 启动入口
# ═══════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()
```

```
完整项目结构（回顾）：

  github-mcp-server/
  ├── pyproject.toml          ← 依赖：mcp[cli]、httpx
  ├── github_client.py        ← GitHub API 封装（9.1 节）
  ├── server.py               ← 上面这个完整文件
  └── README.md

  注册清单：
    🔧 Tools    × 4：get_repo_info / search_repos / get_file_content / list_repo_files
    📄 Resources × 2：github://repos/{owner}/{repo}/readme / structure
    💬 Prompts  × 2：code_review / repo_analysis
```

### 用 MCP Inspector 测试

启动前先用 Inspector 验证所有功能正常：

```bash
# 设置 GitHub Token（可选，建议设置）
export GITHUB_TOKEN="ghp_你的token"

# 用 Inspector 调试
mcp dev server.py
```

在 Inspector 界面中逐项验证：

```
Inspector 测试清单：

  ✅ Tools 页签：
    → get_repo_info(owner="anthropics", repo="mcp")
      期望：返回仓库的 star、fork、描述等信息

    → search_repos(query="mcp server python")
      期望：返回按 star 排序的仓库列表

    → list_repo_files(owner="anthropics", repo="mcp", filter_ext=".py")
      期望：返回仓库中所有 .py 文件

    → get_file_content(owner="anthropics", repo="mcp", path="README.md")
      期望：返回 README 文件内容

  ✅ Resources 页签：
    → 选择 github://repos/anthropics/mcp/readme
      期望：显示仓库 README 内容

    → 选择 github://repos/anthropics/mcp/structure
      期望：显示文件树

  ✅ Prompts 页签：
    → code_review(owner="anthropics", repo="mcp", filepath="README.md")
      期望：生成代码审查提示词

    → repo_analysis(owner="anthropics", repo="mcp")
      期望：生成综合分析提示词
```

### 连接 Claude Desktop

Inspector 测试通过后，配置 Claude Desktop：

```json
{
  "mcpServers": {
    "github-analyzer": {
      "command": "uv",
      "args": ["run", "server.py"],
      "cwd": "/你的路径/github-mcp-server",
      "env": {
        "GITHUB_TOKEN": "ghp_你的token"
      }
    }
  }
}
```

> **注意**：`cwd` 必须指向项目目录，这样 `uv run` 才能找到 `pyproject.toml` 中声明的依赖。`GITHUB_TOKEN` 放在 `env` 中比设置系统环境变量更安全。

### 实际对话演示

连接成功后，和 Claude 的对话就像这样：

```
示例对话 1：探索一个仓库

  👤 你：帮我了解一下 FastAPI 这个项目

  🤖 Claude：
    [调用 get_repo_info(owner="tiangolo", repo="fastapi")]
    [调用 repo_readme → 读取 README]

    FastAPI 是一个现代的高性能 Python Web 框架...
    ⭐ 82,000+ Stars，🍴 7,000+ Forks
    基于 Starlette 和 Pydantic 构建...

  👤 你：它的代码结构是怎样的？

  🤖 Claude：
    [调用 list_repo_files(owner="tiangolo", repo="fastapi", filter_ext=".py")]

    FastAPI 的核心代码位于 fastapi/ 目录下：
    - fastapi/applications.py  → FastAPI 类定义
    - fastapi/routing.py       → 路由系统
    - fastapi/params.py        → 参数处理
    ...
```

```
示例对话 2：审查代码

  👤 你：[选择 code_review Prompt，填入参数]
         owner: anthropics
         repo: mcp
         filepath: src/mcp/server/fastmcp/server.py
         focus: 错误处理

  🤖 Claude：
    [调用 get_file_content 获取代码]
    [按 Prompt 模板进行审查]

    📋 代码审查报告
    📄 文件：src/mcp/server/fastmcp/server.py
    🎯 重点：错误处理

    1. 代码质量：整体良好，函数职责清晰...
    2. 错误处理：建议在第 45 行增加超时处理...
    3. 改进建议：考虑使用自定义异常类...
```

```
示例对话 3：综合分析

  👤 你：[选择 repo_analysis Prompt]
         owner: langchain-ai  repo: langchain

  🤖 Claude：
    [调用 get_repo_info + get_tree + get_readme]
    [生成综合分析报告]

    📌 项目概述：LangChain 是一个用于构建 LLM 应用的框架...
    🏗️ 技术栈：Python、TypeScript 双 SDK...
    📁 代码结构：monorepo 结构，libs/ 下按包划分...
    📊 项目健康度：社区活跃、文档丰富...
    💡 建议：减少核心包体积、改善错误信息...
    🏆 总评：最成熟的 LLM 应用开发框架
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 项目架构 | GitHubClient 封装 API、FastMCP 注册三大原语 |
| Tool 设计 | 4 个工具构成「搜索→了解→浏览→阅读」探索链 |
| Resource 设计 | README 和文件结构作为被动上下文，URI 模板参数化 |
| Prompt 设计 | code_review 和 repo_analysis 两种标准化模板 |
| 工具 vs 资源 | 主动操作用 Tool，背景数据用 Resource |
| Inspector 测试 | 8 项功能逐项验证后再连接 Host |
| Claude Desktop | `cwd` + `env` 配置 GitHub Token |
| 混合能力 | 一次对话中 AI 可以连续调用多个 Tool + Resource |

> **下一章预告**：生产部署与安全 —— 从本地 STDIO 走向远程 HTTP+SSE，用 Docker 容器化，以及认证授权、日志监控等生产级最佳实践。
