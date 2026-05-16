# MCP 协议开发实战

> 从零构建你的第一个 MCP Server，让 AI 成为万能工具人。

---

## 7. 深入 Prompts —— 可复用的提示工程

三大原语中，Tool 和 Resource 都讲完了。最后一个——Prompt，可能是最容易被低估的原语。

很多人觉得"不就是一段提示词嘛，我直接在对话框里打不就行了？"但当你的团队要用 AI 做代码审查、生成测试用例、写文档……每个人每次都手打提示词，质量参差不齐、效率极低。MCP Prompt 就是来解决这个问题的：**把最佳实践的提示词标准化、参数化、一键复用**。

---

### 7.1 定义 Prompt 模板

### @mcp.prompt 装饰器

用 `@mcp.prompt()` 定义一个 Prompt 模板：

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("提示模板库")

@mcp.prompt()
def code_review(code: str, language: str = "python") -> str:
    """对代码进行专业审查，给出改进建议。

    Args:
        code: 要审查的代码
        language: 编程语言，默认 python
    """
    return f"""你是一位资深的 {language} 开发专家。请审查以下代码，从以下维度给出具体的改进建议：

1. **代码质量**：命名规范、可读性、代码组织
2. **性能**：是否有性能瓶颈或不必要的消耗
3. **安全性**：是否有安全漏洞或风险
4. **错误处理**：异常处理是否完善
5. **最佳实践**：是否符合 {language} 社区的惯用模式

对每个问题，请给出：
- 问题描述
- 问题所在的代码行
- 改进建议和示例代码

待审查代码：

```{language}
{code}
```"""
```

```
对比三大原语的装饰器：

  @mcp.tool()                    → 不需要参数
  @mcp.resource("uri://...")     → 需要 URI
  @mcp.prompt()                  → 不需要参数（和 tool 一样）

  提取规则也相同：
    函数名 → Prompt 名称
    docstring 第一行 → 描述
    函数参数 → Prompt 的 arguments
```

### 自动提取机制

| 来源 | 提取内容 | 协议字段 |
|------|---------|---------|
| 函数名 `code_review` | Prompt 名称 | `name` |
| docstring 第一行 | 描述 | `description` |
| 函数参数 `code: str` | 参数定义 | `arguments[].name` |
| docstring Args 部分 | 参数描述 | `arguments[].description` |
| 有无默认值 | 是否必填 | `arguments[].required` |

上面的 `code_review` 函数会生成这样的协议定义：

```json
{
  "name": "code_review",
  "description": "对代码进行专业审查，给出改进建议。",
  "arguments": [
    {
      "name": "code",
      "description": "要审查的代码",
      "required": true
    },
    {
      "name": "language",
      "description": "编程语言，默认 python",
      "required": false
    }
  ]
}
```

### 返回值类型

Prompt 函数的返回值决定了发送给 AI 的消息内容：

```python
# ① 返回字符串 → 自动包装为单条 user 消息
@mcp.prompt()
def simple_prompt(topic: str) -> str:
    return f"请详细解释 {topic} 的工作原理"
# 协议层：messages: [{role: "user", content: {type: "text", text: "..."}}]

# ② 返回 Message 列表 → 多轮消息（下一节详讲）
@mcp.prompt()
def multi_turn(topic: str) -> list[Message]:
    return [
        UserMessage("请解释 {topic}"),
        AssistantMessage("好的，让我来解释..."),
        UserMessage("能再深入一些吗？"),
    ]
```

> **大多数场景**：返回 `str` 就够了。只有需要构造多轮对话或设置系统提示时，才需要返回 `Message` 列表。

### 在 Host 中使用 Prompt

用户如何触发一个 Prompt？取决于 Host 的实现：

```
不同 Host 中 Prompt 的触发方式：

  Claude Desktop：
    → 在对话框输入 / 或点击 📎 按钮
    → 从列表中选择 Prompt
    → 填入参数 → 发送

  Cursor / Cline：
    → 通常集成在 AI 对话侧边栏
    → 选择 Prompt → 填参数 → 执行

  自定义 Agent：
    → 开发者在代码中调用 prompts/get
    → 拿到消息列表后发给 AI 模型
```

> **和 Tool 的关键区别**：Tool 是 AI 自己决定调用的；Prompt 是**用户主动选择**的。AI 不会自发使用某个 Prompt，必须用户（或应用）触发。

---

### 7.2 参数化 Prompt 与多轮消息

上一节我们用 `return str` 创建了简单的 Prompt。但 MCP Prompt 的真正威力在于：**多轮消息**和**嵌入 Resource**。

### 多消息 Prompt

返回一个消息列表，可以构造复杂的对话预设：

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import UserMessage, AssistantMessage

mcp = FastMCP("高级提示模板")

@mcp.prompt()
def debug_helper(error_message: str, language: str = "python") -> list:
    """帮助分析和解决代码错误。

    Args:
        error_message: 完整的错误信息（包括 traceback）
        language: 编程语言
    """
    return [
        UserMessage(f"""你是一位 {language} 调试专家。我遇到了以下错误，请帮我分析：

```
{error_message}
```

请按以下步骤分析：
1. 这个错误的含义是什么？
2. 最可能的原因是什么？
3. 怎么修复？给出具体代码
4. 怎么避免将来再次出现这个错误？"""),
    ]
```

```
为什么用 Message 列表而不是纯字符串？

  返回 str：
    → 生成 1 条 user 消息
    → 简单场景够用

  返回 [UserMessage(...)]:
    → 也是 1 条 user 消息，但更明确
    → 可以混合多种角色

  返回 [UserMessage(...), AssistantMessage(...)]:
    → 构造多轮预设对话
    → 可以"预热"AI 的回答风格
```

### 用多轮消息"预热"AI

一个高级技巧：用预设的 assistant 回复来"引导"AI 的输出风格：

```python
@mcp.prompt()
def structured_analysis(topic: str) -> list:
    """对给定主题进行结构化分析报告。

    Args:
        topic: 要分析的主题
    """
    return [
        UserMessage(
            f"请对「{topic}」进行深度分析。"
            "要求使用结构化的格式输出。"
        ),
        AssistantMessage(
            "好的，我会按照以下结构来分析：\n\n"
            "## 1. 概述\n"
            "## 2. 核心要点\n"
            "## 3. 优缺点分析\n"
            "## 4. 实际应用场景\n"
            "## 5. 总结与建议\n\n"
            "让我开始分析：\n\n"
            "## 1. 概述\n\n"
        ),
    ]
```

```
"预热"的效果：

  没有预热：
    AI 可能用任意格式回答——有时分条列举，有时写长段文字

  有预热（assistant 消息铺垫格式）：
    AI 会接续 assistant 消息的风格继续输出
    → 保证了输出的结构一致性
    → 特别适合生成报告、文档、模板化内容
```

### 嵌入 Resource

Prompt 的消息中可以直接引用 MCP Resource——这是 Prompt 最强大的特性之一：

```python
from mcp.server.fastmcp.prompts import UserMessage
from mcp.types import TextContent, EmbeddedResource, ResourceContents

@mcp.prompt()
def review_file(filepath: str) -> list:
    """审查项目中的指定文件。

    Args:
        filepath: 要审查的文件路径，如 'src/main.py'
    """
    # 读取文件内容
    with open(filepath, "r") as f:
        code = f.read()

    return [
        UserMessage(
            content=[
                TextContent(
                    type="text",
                    text="请审查以下代码文件，给出改进建议："
                ),
                EmbeddedResource(
                    type="resource",
                    resource=ResourceContents(
                        uri=f"file://project/{filepath}",
                        mimeType="text/x-python",
                        text=code
                    )
                ),
            ]
        ),
    ]
```

```
嵌入 Resource 的好处：

  ① 自动注入数据
     → 用户选择 Prompt 时，文件内容自动加载
     → 不需要用户手动复制粘贴代码

  ② 保留元数据
     → 嵌入的 Resource 带有 URI 和 mimeType
     → AI 知道这是一个 Python 文件，会按相应标准审查

  ③ 与 Resource 系统联动
     → 如果 Resource 有变更通知，嵌入的内容可以保持最新
```

### 实用 Prompt 模板集

下面是一些你可以直接使用的实用 Prompt 模板：

```python
# ═══════════════════════════════════════════
# 翻译模板
# ═══════════════════════════════════════════

@mcp.prompt()
def translate(
    text: str,
    target_language: str = "英语",
    style: str = "专业"
) -> str:
    """翻译文本，保持原文风格。

    Args:
        text: 要翻译的文本
        target_language: 目标语言，如 '英语'、'日语'、'韩语'
        style: 翻译风格：'专业'、'口语化'、'文学'
    """
    return f"""请将以下文本翻译为{target_language}。

翻译要求：
- 风格：{style}
- 保持原文的语气和格式
- 专业术语使用该领域的标准译法
- 如有不确定的翻译，在括号中给出原文

原文：
{text}"""

# ═══════════════════════════════════════════
# 单元测试生成模板
# ═══════════════════════════════════════════

@mcp.prompt()
def generate_tests(
    code: str,
    framework: str = "pytest",
    coverage: str = "全面"
) -> str:
    """为代码生成单元测试。

    Args:
        code: 要测试的代码
        framework: 测试框架，如 'pytest'、'unittest'
        coverage: 覆盖程度：'基础'（正常路径）或 '全面'（含边界和异常）
    """
    return f"""请为以下代码生成 {framework} 单元测试。

覆盖要求：{coverage}
- 基础：核心功能的正常路径
- 全面：正常路径 + 边界条件 + 异常处理 + 类型错误

请确保：
1. 每个测试函数有清晰的命名（test_功能_场景）
2. 使用 AAA 模式（Arrange-Act-Assert）
3. 包含必要的 mock/fixture
4. 添加中文注释说明测试意图

待测试的代码：

```python
{code}
```"""

# ═══════════════════════════════════════════
# Git Commit 消息生成模板
# ═══════════════════════════════════════════

@mcp.prompt()
def commit_message(diff: str) -> str:
    """根据代码变更生成规范的 Git Commit 消息。

    Args:
        diff: git diff 的输出内容
    """
    return f"""请根据以下 git diff 生成一条规范的 Commit 消息。

格式要求（Conventional Commits）：
  <type>(<scope>): <subject>
  
  <body>

type 可选值：feat / fix / docs / style / refactor / test / chore
scope：改动涉及的模块
subject：一句话描述（不超过 50 字符）
body：详细描述变更原因和内容

Diff 内容：
```diff
{diff}
```"""
```

> **实操建议**：把你团队常用的 prompt 都做成 MCP Prompt 模板。一次投入，持续收益——每个团队成员都能一键使用最佳实践的提示词。

---

### 7.3 Prompts + Tools + Resources 的组合模式

三大原语各自有用，但组合起来才是 MCP Server 的完整形态。我们用一个完整的实战案例，展示三者如何协作。

### 实战：代码质量助手 MCP Server

```python
# quality_server.py —— 代码质量助手
# 结合 Tool + Resource + Prompt 的完整示例
import os
import json
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import UserMessage

mcp = FastMCP("代码质量助手")

PROJECT_DIR = "./my-project"

# ═══════════════════════════════════════════
# Resource：提供上下文数据
# ═══════════════════════════════════════════

@mcp.resource("project://structure")
def project_structure() -> str:
    """项目文件结构"""
    result = []
    for root, dirs, files in os.walk(PROJECT_DIR):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.endswith(('.py', '.js', '.ts')):
                path = os.path.join(root, f).replace(PROJECT_DIR, '')
                result.append(path)
    return "\n".join(sorted(result))

@mcp.resource("file://src/{filepath}")
def read_source(filepath: str) -> str:
    """读取源代码文件"""
    full_path = os.path.join(PROJECT_DIR, filepath)
    with open(full_path, "r") as f:
        return f.read()

# ═══════════════════════════════════════════
# Tool：执行操作
# ═══════════════════════════════════════════

@mcp.tool()
def count_lines(filepath: str) -> str:
    """统计文件的代码行数（不含空行和注释）。

    Args:
        filepath: 文件路径
    """
    full_path = os.path.join(PROJECT_DIR, filepath)
    with open(full_path, "r") as f:
        lines = f.readlines()

    total = len(lines)
    blank = sum(1 for l in lines if not l.strip())
    comment = sum(1 for l in lines if l.strip().startswith('#'))
    code = total - blank - comment

    return (
        f"📊 文件：{filepath}\n"
        f"  总行数：{total}\n"
        f"  代码行：{code}\n"
        f"  空白行：{blank}\n"
        f"  注释行：{comment}"
    )

@mcp.tool()
def find_todos(filepath: str = "") -> str:
    """查找代码中的 TODO 和 FIXME 注释。

    Args:
        filepath: 文件路径（为空则搜索整个项目）
    """
    results = []
    search_dir = os.path.join(PROJECT_DIR, filepath) if filepath else PROJECT_DIR

    for root, _, files in os.walk(search_dir):
        for f in files:
            if not f.endswith('.py'):
                continue
            fpath = os.path.join(root, f)
            with open(fpath, "r") as file:
                for i, line in enumerate(file, 1):
                    if "TODO" in line or "FIXME" in line:
                        rel_path = fpath.replace(PROJECT_DIR, '')
                        results.append(f"  {rel_path}:{i} → {line.strip()}")

    if not results:
        return "✅ 没有找到 TODO/FIXME 注释"
    return f"📋 找到 {len(results)} 个 TODO/FIXME：\n\n" + "\n".join(results)

# ═══════════════════════════════════════════
# Prompt：标准化的提示模板
# ═══════════════════════════════════════════

@mcp.prompt()
def full_review(filepath: str) -> list:
    """对文件进行全面代码审查（含代码内容和项目结构上下文）。

    Args:
        filepath: 要审查的文件路径
    """
    # 读取文件内容
    full_path = os.path.join(PROJECT_DIR, filepath)
    with open(full_path, "r") as f:
        code = f.read()

    return [
        UserMessage(f"""请对以下 Python 文件进行全面审查。

📁 文件路径：{filepath}

```python
{code}
```

请从以下维度逐一审查，每个维度给出评分（1-5 星）和改进建议：

| 维度 | 评分 | 发现的问题 | 改进建议 |
|------|------|-----------|---------|

审查维度：
1. ⭐ 代码风格与命名
2. ⭐ 函数设计与解耦
3. ⭐ 错误处理
4. ⭐ 性能与效率
5. ⭐ 安全性
6. ⭐ 可测试性
7. ⭐ 文档与注释

最后给出总评和最优先需要修改的 3 个问题。"""),
    ]

@mcp.prompt()
def refactor_plan(filepath: str, goal: str = "提高可读性") -> str:
    """生成代码重构方案。

    Args:
        filepath: 要重构的文件路径
        goal: 重构目标，如 '提高可读性'、'提升性能'、'增加可测试性'
    """
    full_path = os.path.join(PROJECT_DIR, filepath)
    with open(full_path, "r") as f:
        code = f.read()

    return f"""请为以下代码制定重构方案。

重构目标：{goal}

当前代码：
```python
{code}
```

请输出：
1. 当前代码的主要问题分析
2. 重构思路和步骤
3. 重构后的完整代码
4. 重构前后的对比说明"""

if __name__ == "__main__":
    mcp.run()
```

### 三者如何协作

```
代码质量助手的使用流程：

  ┌──────────────────────────────────────────────────┐
  │                    用户视角                        │
  ├──────────────────────────────────────────────────┤
  │                                                    │
  │  ① 了解项目                                       │
  │     → Resource: project://structure               │
  │     → AI 看到项目有哪些文件                        │
  │                                                    │
  │  ② 查看具体文件                                    │
  │     → Resource: file://src/main.py                │
  │     → AI 看到代码内容                              │
  │                                                    │
  │  ③ 一键审查                                        │
  │     → Prompt: full_review(filepath="main.py")     │
  │     → AI 收到标准化的审查模板 + 代码内容            │
  │     → 输出结构化的审查报告                          │
  │                                                    │
  │  ④ 量化分析                                        │
  │     → Tool: count_lines("main.py")                │
  │     → Tool: find_todos()                          │
  │     → AI 拿到具体数据辅助决策                      │
  │                                                    │
  │  ⑤ 重构方案                                        │
  │     → Prompt: refactor_plan("main.py", "提升性能") │
  │     → AI 输出完整的重构方案                         │
  │                                                    │
  └──────────────────────────────────────────────────┘
```

### 设计原则总结

```
三大原语的职责划分：

  Resource = 上下文窗口
    → 让 AI 看到需要的数据
    → 被动提供，不执行操作
    → 设计时想："AI 需要看到什么？"

  Tool = 操作接口
    → 让 AI 执行具体操作
    → AI 自主判断何时调用
    → 设计时想："AI 需要做什么？"

  Prompt = 标准工作流
    → 给 AI 一个角色和任务
    → 用户主动触发
    → 设计时想："什么任务需要标准化？"

  组合黄金法则：
    ✅ Resource 提供数据 → Prompt 设定任务 → Tool 执行操作
    ✅ 不要把所有功能都塞进 Tool
    ✅ 不要用 Tool 做 Resource 该做的事（提供静态数据）
    ✅ 不要跳过 Prompt 让用户每次手打复杂提示词
```

> **一句话总结**：Resource 让 AI "看得见"，Tool 让 AI "做得到"，Prompt 让 AI "做得好"。三者协作，才是一个完整的 MCP Server。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| @mcp.prompt() | 从函数名→名称、docstring→描述、参数→arguments |
| 返回 str | 生成单条 user 消息，简单场景够用 |
| 返回 Message 列表 | 构造多轮预设对话，可"预热"AI 输出风格 |
| AssistantMessage | 预设 AI 回复，引导后续输出的格式和风格 |
| 嵌入 Resource | 在 Prompt 消息中注入文件/数据，自动加载 |
| 用户触发 | Prompt 由用户选择使用，AI 不自动调用 |
| 实用模板 | 翻译、代码审查、单元测试、Commit 消息 |
| 三者组合 | Resource 给上下文 + Prompt 定任务 + Tool 做操作 |
| 设计原则 | 各司其职，不要把所有功能都塞进 Tool |

> **下一章预告**：TypeScript SDK —— 用 Node.js 构建 MCP Server。如果你是前端开发者或偏好 TypeScript，下一章将展示如何用 TS SDK + Zod 来定义类型安全的 MCP Server，并对比 Python 和 TypeScript 两种方案的异同。

