# AI 代码审查助手实战

> 从 Git Hook 到自动化评论——用 LLM + AST 解析 + Git Diff 构建一套能自动审查代码变更、识别潜在 Bug、提供改进建议、并与 GitHub/GitLab 无缝集成的 AI 代码审查系统。

---

## 1. 为什么需要 AI 代码审查

Code Review 是软件工程中公认的最佳实践——Google 要求每一行代码必须经过至少一个人的 Review 才能合并。但现实是，大多数团队的 Review 流程要么流于形式，要么严重拖慢交付速度。AI 代码审查不是要替代人类 Reviewer，而是当你的"第一道防线"。

### 1.1 人工 Code Review 的三大痛点

```
Code Review 的理想 vs 现实：

  理想状态
  ═══════════════════════════════════════
  • 每个 PR 都被认真审查
  • 逻辑、安全、性能全面覆盖
  • Reviewer 给出深思熟虑的改进建议
  • 24 小时内完成 Review

  现实情况
  ═══════════════════════════════════════
  • 赶 deadline → "LGTM"（Looks Good To Me）
  • 500 行的 PR → 只看了前 50 行
  • Reviewer 累了 → 只检查格式问题
  • 等 3 天才收到第一条评论
```

**痛点 1：效率低，阻塞交付**

| 场景 | 等待时间 | 影响 |
|:---|:---|:---|
| 小团队（< 5 人） | 0.5-1 天 | 勉强可接受 |
| 中型团队（10-30 人） | 1-3 天 | 频繁 Context Switch |
| 跨时区团队 | 1-5 天 | PR 叠加，merge conflict 大增 |

**痛点 2：标准不一致**

同一段代码，不同 Reviewer 的意见可能完全相反。新员工不了解团队规范，老员工有自己的"口味偏好"。

**痛点 3：Review 疲劳**

```
Review 疲劳的恶性循环：

  大 PR（500+ 行修改）
      │
      ▼
  Reviewer 打开 → 看到一屏屏代码 → 内心崩溃
      │
      ▼
  前 100 行认真看 → 第 200 行开始走马观花
      │
      ▼
  关键 Bug 在第 350 行 → 没人看到
      │
      ▼
  "LGTM"，合并 → 线上出 Bug → 事后复盘
```

> 💡 **数据参考**：微软研究院的论文发现，一个 PR 超过 200 行后，Reviewer 发现 Bug 的概率急剧下降。超过 400 行后，Review 基本只剩"看了"的仪式感。

### 1.2 AI 代码审查能做什么、不能做什么

```
AI 代码审查的能力边界：

  ✅ AI 擅长的（交给 AI）
  ═══════════════════════════════════════
  • 常见 Bug 模式检测（空指针、数组越界、资源未释放）
  • 安全漏洞识别（SQL 注入、XSS、硬编码密码）
  • 代码风格统一检查（命名规范、注释缺失）
  • 潜在性能问题（N+1 查询、不必要的循环）
  • 简单的逻辑错误（条件判断遗漏、边界处理）
  • 7×24 不知疲倦，无情绪波动

  ❌ AI 不擅长的（留给人类）
  ═══════════════════════════════════════
  • 业务逻辑正确性（这个折扣计算对不对？）
  • 架构合理性（这个模块应该放在哪一层？）
  • 需求匹配度（代码实现的是不是产品要的？）
  • 团队协作（这个修改会不会影响同事的 PR？）
  • 代码的"味道"（有经验才能闻到的 Code Smell）
```

| 审查维度 | AI 能力 | 人类优势 | 推荐策略 |
|:---|:---|:---|:---|
| Bug 检测 | ⭐⭐⭐⭐ | ⭐⭐⭐ | AI 初筛 + 人类确认 |
| 安全漏洞 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | AI 必查 |
| 代码风格 | ⭐⭐⭐⭐⭐ | ⭐⭐ | 完全交给 AI |
| 性能问题 | ⭐⭐⭐ | ⭐⭐⭐⭐ | AI 标记 + 人类判断 |
| 业务逻辑 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 人类为主 |
| 架构设计 | ⭐ | ⭐⭐⭐⭐⭐ | 完全由人类判断 |

> 💡 **正确的定位**：AI 是你团队的"初级 Reviewer"——它不知疲倦地检查每一行代码，把明显的问题提前拦截。人类 Reviewer 从"满屏找 Bug"变成"确认 AI 的发现 + 关注业务逻辑"。Review 效率提升 2-3 倍。

### 1.3 系统架构总览：从 Git Push 到自动评论

一个完整的 AI 代码审查系统分为**四个阶段**，从 Git 事件触发到评论自动落地：

```
AI 代码审查的完整链路：

  ① 触发                ② 解析               ③ 审查               ④ 输出
  ═══════════          ═══════════          ═══════════          ═══════════
  开发者提交 PR          获取 Diff             LLM 审查             输出结果
      │                    │                    │                    │
      ▼                    ▼                    ▼                    ▼
  ┌─────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐
  │ GitHub   │──→    │ Diff     │──→    │ Review   │──→    │ PR 评论  │
  │ Webhook  │       │ Parser   │       │ Engine   │       │ API 调用 │
  │          │       │          │       │          │       │          │
  │ PR 创建  │       │ 文件过滤  │       │ Prompt   │       │ 行级评论 │
  │ PR 更新  │       │ 分块切割  │       │ 构建     │       │ 总结评论 │
  │ Push     │       │ 上下文    │       │ LLM 调用 │       │ 状态标记 │
  └─────────┘       │ 收集     │       │ 结果解析 │       └──────────┘
                     └──────────┘       └──────────┘
```

| 阶段 | 核心职责 | 本教程对应章节 |
|:---|:---|:---|
| **触发** | 监听 Git 事件，获取 PR/MR 信息 | 第 5 章 |
| **解析** | 解析 Diff、过滤文件、收集上下文 | 第 2-3 章 |
| **审查** | Prompt 工程 + LLM 调用 + 结果分级 | 第 4 章 |
| **输出** | 调用 API 在 PR 中发布评论 | 第 5 章 |

### 1.4 技术选型与依赖安装

```
本教程的技术选型：

  组件              选型                  推荐理由
  ──────────────────────────────────────────────────────────
  Web 框架          FastAPI               接收 Webhook + 提供 API
  LLM               DeepSeek / GPT-4o    DeepSeek 便宜适合初筛，GPT-4o 深度审查
  Git 操作          GitPython / subprocess 解析 Diff、获取文件内容
  AST 解析          ast (Python 内置)     提取函数签名、依赖关系
  GitHub 集成       PyGithub / httpx      API 交互 + Webhook 处理
  结构化输出        Pydantic              Review 结果的类型安全解析
  ──────────────────────────────────────────────────────────
```

**安装依赖：**

```bash
# ── 核心框架 ──
pip install fastapi uvicorn[standard]       # Web 框架
pip install langchain langchain-openai      # LLM 编排

# ── Git 操作 ──
pip install gitpython                        # Python Git 接口
pip install unidiff                           # Unified Diff 解析

# ── 平台集成 ──
pip install PyGithub                         # GitHub API
pip install python-gitlab                    # GitLab API
pip install httpx                            # HTTP 客户端

# ── 工具 ──
pip install python-dotenv pydantic           # 环境变量、数据校验
```

**验证安装：**

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# 验证 LLM
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)
response = llm.invoke("用一句话解释什么是 Code Review")
print(f"✅ LLM 连接成功: {response.content[:60]}")

# 验证 Git 解析
from unidiff import PatchSet
print("✅ unidiff 导入成功")

# 验证 GitHub API
from github import Github
print("✅ PyGithub 导入成功")
```

> 💡 **模型选择策略**：代码审查对模型的代码理解能力要求很高。推荐用 DeepSeek-Coder 或 GPT-4o。DeepSeek-Coder 性价比最高（1/10 的价格，90% 的审查质量），GPT-4o 在复杂逻辑分析上更强。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **三大痛点** | 效率低（等 1-5 天）、标准不一、Review 疲劳 |
| **AI 定位** | "初级 Reviewer"——拦截明显问题，解放人类专注业务 |
| **能力边界** | 擅长 Bug/安全/风格，不擅长业务逻辑/架构设计 |
| **四阶段架构** | 触发 → 解析 → 审查 → 输出 |

---

## 2. Git Diff 解析：理解代码变更

AI 审查代码的第一步不是调 LLM——而是先把代码变更解析成结构化数据。这一章搞定"从一坨 Diff 文本到清晰的变更对象"的全过程。

### 2.1 Git Diff 格式深度解析

先搞懂 `git diff` 输出的每一行代表什么：

```diff
diff --git a/utils/auth.py b/utils/auth.py
index 3a4b5c6..7d8e9f0 100644
--- a/utils/auth.py
+++ b/utils/auth.py
@@ -15,8 +15,10 @@ def verify_token(token: str) -> dict:
     if not token:
         raise ValueError("Token is required")
-    decoded = jwt.decode(token, SECRET_KEY)
+    try:
+        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
+    except jwt.ExpiredSignatureError:
+        raise AuthError("Token has expired")
     return decoded
```

```
Diff 的每一行解读：

  diff --git a/file b/file     → 哪个文件发生了变更
  index 3a4b5c6..7d8e9f0      → 变更前后的 Git blob hash
  --- a/utils/auth.py          → 变更前的文件路径
  +++ b/utils/auth.py          → 变更后的文件路径
  @@ -15,8 +15,10 @@            → Hunk 头：旧文件第15行起8行，新文件第15行起10行
  
  行前缀含义：
  （空格）  上下文行（未修改）
  -         删除的行
  +         新增的行
```

### 2.2 用 Python 解析 Diff：从 patch 到结构化数据

用 `unidiff` 库把 Diff 文本解析为结构化对象：

```python
from dataclasses import dataclass, field
from unidiff import PatchSet

@dataclass
class FileChange:
    """单个文件的变更"""
    path: str                    # 文件路径
    change_type: str             # added / modified / deleted / renamed
    language: str                # 编程语言
    added_lines: list[dict]      # [{"line_no": 15, "content": "..."}]
    removed_lines: list[dict]    # [{"line_no": 10, "content": "..."}]
    context_lines: list[dict]    # 上下文行
    patch_text: str              # 原始 patch 文本

@dataclass
class DiffResult:
    """完整的 Diff 解析结果"""
    files: list[FileChange] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0

class DiffParser:
    """Git Diff 解析器"""
    
    LANG_MAP = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".go": "go", ".java": "java", ".rs": "rust",
        ".rb": "ruby", ".cpp": "cpp", ".c": "c",
    }
    
    def parse(self, diff_text: str) -> DiffResult:
        """解析 Diff 文本"""
        patch = PatchSet(diff_text)
        result = DiffResult()
        
        for patched_file in patch:
            # 判断变更类型
            if patched_file.is_added_file:
                change_type = "added"
            elif patched_file.is_removed_file:
                change_type = "deleted"
            elif patched_file.is_rename:
                change_type = "renamed"
            else:
                change_type = "modified"
            
            # 提取变更行
            added, removed, context = [], [], []
            for hunk in patched_file:
                for line in hunk:
                    entry = {
                        "line_no": line.target_line_no or line.source_line_no,
                        "content": line.value.rstrip("\n"),
                    }
                    if line.is_added:
                        added.append(entry)
                    elif line.is_removed:
                        removed.append(entry)
                    else:
                        context.append(entry)
            
            # 识别语言
            ext = "." + patched_file.path.rsplit(".", 1)[-1] \
                  if "." in patched_file.path else ""
            
            file_change = FileChange(
                path=patched_file.path,
                change_type=change_type,
                language=self.LANG_MAP.get(ext, "unknown"),
                added_lines=added,
                removed_lines=removed,
                context_lines=context,
                patch_text=str(patched_file),
            )
            
            result.files.append(file_change)
            result.total_additions += len(added)
            result.total_deletions += len(removed)
        
        return result

# ── 使用示例 ──
import subprocess

def get_pr_diff(repo_path: str, base: str, head: str) -> str:
    """获取两个分支之间的 Diff"""
    result = subprocess.run(
        ["git", "diff", f"{base}...{head}"],
        cwd=repo_path, capture_output=True, text=True,
    )
    return result.stdout

parser = DiffParser()
diff_text = get_pr_diff("/path/to/repo", "main", "feature/auth")
result = parser.parse(diff_text)

print(f"变更文件: {len(result.files)}")
print(f"新增: +{result.total_additions}, 删除: -{result.total_deletions}")
for f in result.files:
    print(f"  {f.change_type}: {f.path} ({f.language})")
```

> 💡 **为什么用 `unidiff` 而不是手写解析**：Diff 格式看起来简单，但边界 case 很多——二进制文件、文件权限变更、重命名、空文件。`unidiff` 处理好了所有这些情况。

### 2.3 变更分类与过滤：哪些文件需要 Review

不是所有文件都值得 AI Review——`package-lock.json` 变了 3000 行，花钱让 LLM 看一遍毫无意义。

```python
class DiffFilter:
    """Diff 过滤器：过滤不需要 Review 的文件"""
    
    # 跳过的文件模式
    SKIP_PATTERNS = [
        "*.lock", "*.min.js", "*.min.css",   # 锁文件、压缩文件
        "*.pb.go", "*_generated.*",           # 自动生成的代码
        "*.svg", "*.png", "*.jpg",            # 二进制/图片
        "package-lock.json", "yarn.lock",     # 前端依赖锁
        "go.sum", "poetry.lock",              # 后端依赖锁
        "*.md", "*.txt", "*.rst",             # 纯文档
        ".gitignore", ".env.example",         # 配置文件
    ]
    
    # 需要重点 Review 的文件
    HIGH_PRIORITY = [
        "*/auth*", "*/security*",             # 安全相关
        "*/models/*", "*/schemas/*",          # 数据模型
        "*/api/*", "*/routes/*",              # API 接口
        "**/migrations/*",                     # 数据库迁移
    ]
    
    def filter(self, diff: DiffResult) -> list[FileChange]:
        """过滤并优先排序"""
        import fnmatch
        
        reviewable = []
        for f in diff.files:
            # 跳过不需要 Review 的
            skip = any(
                fnmatch.fnmatch(f.path, p) 
                for p in self.SKIP_PATTERNS
            )
            if skip or f.language == "unknown":
                continue
            
            # 标记优先级
            f.priority = "high" if any(
                fnmatch.fnmatch(f.path, p) 
                for p in self.HIGH_PRIORITY
            ) else "normal"
            
            reviewable.append(f)
        
        # 高优先级排前面
        reviewable.sort(key=lambda f: f.priority != "high")
        return reviewable
```

| 文件类型 | 处理方式 | 理由 |
|:---|:---|:---|
| 源代码（.py/.js/.go） | ✅ Review | 核心逻辑 |
| 锁文件（.lock） | ❌ 跳过 | 自动生成，无 Review 价值 |
| 配置文件（.yml/.toml） | ⚠️ 可选 | 可能含安全配置 |
| 测试文件（test_*） | ✅ Review | 测试质量也很重要 |
| 文档（.md） | ❌ 跳过 | 不需要代码审查 |

### 2.4 大 Diff 的智能分块：避免超出 LLM 上下文

一个 PR 改了 2000 行，直接丢给 LLM 会超出上下文窗口。需要按逻辑拆分成小块：

```python
class DiffChunker:
    """把大 Diff 切分成适合 LLM 处理的小块"""
    
    def __init__(self, max_lines_per_chunk: int = 300,
                 max_files_per_chunk: int = 3):
        self.max_lines = max_lines_per_chunk
        self.max_files = max_files_per_chunk
    
    def chunk(self, files: list[FileChange]) -> list[list[FileChange]]:
        """按文件分组，每组不超过限制"""
        chunks = []
        current_chunk = []
        current_lines = 0
        
        for f in files:
            file_lines = len(f.added_lines) + len(f.removed_lines)
            
            # 单个文件超大 → 独立一个 chunk
            if file_lines > self.max_lines:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_lines = 0
                chunks.append([f])  # 大文件单独处理
                continue
            
            # 加入当前 chunk 会超限 → 开新 chunk
            if (current_lines + file_lines > self.max_lines or
                len(current_chunk) >= self.max_files):
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = [f]
                current_lines = file_lines
            else:
                current_chunk.append(f)
                current_lines += file_lines
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

# ── 使用示例 ──
chunker = DiffChunker(max_lines_per_chunk=300)
chunks = chunker.chunk(filtered_files)
print(f"拆分为 {len(chunks)} 个 chunk")
# → "拆分为 4 个 chunk"
# 每个 chunk 独立调用 LLM Review
```

```
分块策略对比：

  策略 1：按文件数分块（简单粗暴）
  ═══════════════════════════════════════
  每 3 个文件一组
  ❌ 问题：3 个大文件 = 1500 行，超出上下文

  策略 2：按行数分块（本教程方案）
  ═══════════════════════════════════════
  每组不超过 300 行变更
  ✅ 保证每次 LLM 调用的输入大小可控

  策略 3：按关联性分块（高级方案）
  ═══════════════════════════════════════
  相关文件放同一组（如 model + schema + test）
  ✅ LLM 能看到完整修改上下文
  ❌ 实现复杂，需要依赖分析
```

> 💡 **为什么 300 行是合理上限**：DeepSeek-Coder 的上下文窗口是 128K token，但代码审查还需要塞入 System Prompt + 审查规则 + 输出格式要求。300 行代码 ≈ 3000-4000 token，给 Prompt 和输出留足空间。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Diff 格式** | `+` 新增、`-` 删除、空格上下文，`@@` 标记位置 |
| **结构化解析** | `unidiff` 库 → FileChange 对象（路径/语言/变更行） |
| **文件过滤** | 跳过锁文件/图片/文档，优先审查安全/API/模型 |
| **智能分块** | 按行数分组（≤ 300 行/组），大文件单独处理 |

---

## 3. 代码理解：让 AI 读懂你的代码

只看 Diff 就 Review，就像只看一段话就评论整篇文章——缺少上下文，判断必然不准。这一章让 AI 理解"代码改了什么"的同时，还理解"代码在做什么"。

### 3.1 为什么只看 Diff 不够：上下文的重要性

```
纯看 Diff 的致命缺陷：

  场景 1：不知道函数签名
  ═══════════════════════════════════════
  Diff 显示：result = process_order(data)
  AI 看到：调用了一个函数。没问题。
  实际上：process_order 的参数类型是 OrderRequest，
         而 data 是 dict → 类型不匹配！
  → 需要知道函数签名才能发现

  场景 2：不知道被谁调用
  ═══════════════════════════════════════
  Diff 显示：函数 calculate_tax() 的返回值从 float 改成 Decimal
  AI 看到：改了返回类型。看起来没问题。
  实际上：有 15 个地方调用了这个函数，全都期望 float
  → 需要知道调用方才能发现 Breaking Change

  场景 3：不知道变量含义
  ═══════════════════════════════════════
  Diff 显示：if status == 3:
  AI 看到：Magic Number，建议用常量。
  实际上：STATUS_COMPLETED = 3 定义在文件开头
  → 需要看完整文件才能避免误报
```

### 3.2 AST 解析：提取函数签名、类结构与依赖

用 Python 内置的 `ast` 模块，从源文件中提取代码结构信息：

```python
import ast
from dataclasses import dataclass

@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    args: list[str]             # 参数列表
    return_type: str | None     # 返回类型注解
    decorators: list[str]       # 装饰器
    line_start: int
    line_end: int
    docstring: str | None

@dataclass
class FileStructure:
    """文件代码结构"""
    imports: list[str]
    classes: list[dict]
    functions: list[FunctionInfo]
    global_vars: list[str]

class CodeAnalyzer:
    """Python 源码分析器"""
    
    def analyze(self, source_code: str) -> FileStructure:
        """分析源码，提取结构信息"""
        tree = ast.parse(source_code)
        
        imports = []
        classes = []
        functions = []
        global_vars = []
        
        for node in ast.walk(tree):
            # 提取 import
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
            
            # 提取函数
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func = FunctionInfo(
                    name=node.name,
                    args=[arg.arg for arg in node.args.args],
                    return_type=ast.unparse(node.returns) 
                                if node.returns else None,
                    decorators=[ast.unparse(d) for d in node.decorator_list],
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    docstring=ast.get_docstring(node),
                )
                functions.append(func)
            
            # 提取类
            elif isinstance(node, ast.ClassDef):
                methods = [
                    n.name for n in node.body 
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                classes.append({
                    "name": node.name,
                    "bases": [ast.unparse(b) for b in node.bases],
                    "methods": methods,
                    "line_start": node.lineno,
                })
        
        return FileStructure(
            imports=imports, classes=classes,
            functions=functions, global_vars=global_vars,
        )

# ── 使用示例 ──
analyzer = CodeAnalyzer()
with open("utils/auth.py") as f:
    structure = analyzer.analyze(f.read())

for func in structure.functions:
    print(f"  {func.name}({', '.join(func.args)}) -> {func.return_type}")
# → verify_token(token: str) -> dict
# → refresh_token(old_token: str) -> str
```

> 💡 **跨语言支持**：Python 用内置 `ast`，JavaScript/TypeScript 可用 `tree-sitter`（有 Python binding），Go 可用 `go/parser`。核心策略相同——提取函数签名、类结构、import 关系。

### 3.3 智能上下文收集：找到变更影响的关键代码

知道了代码结构后，下一步是**找出与变更相关的上下文**——被修改函数的定义、调用方、相关类型：

```python
import subprocess

class ContextCollector:
    """智能上下文收集器"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.analyzer = CodeAnalyzer()
    
    def collect(self, file_change: FileChange) -> dict:
        """为一个文件变更收集上下文"""
        context = {
            "file_structure": None,      # 当前文件结构
            "modified_functions": [],     # 被修改的函数签名
            "callers": [],               # 调用方
            "related_imports": [],       # 相关依赖
        }
        
        # 1. 获取完整文件内容并分析
        full_content = self._get_file_content(file_change.path)
        if full_content and file_change.language == "python":
            structure = self.analyzer.analyze(full_content)
            context["file_structure"] = structure
            
            # 2. 找出被修改的函数
            changed_lines = {l["line_no"] for l in file_change.added_lines}
            changed_lines |= {l["line_no"] for l in file_change.removed_lines}
            
            for func in structure.functions:
                if any(func.line_start <= ln <= func.line_end
                       for ln in changed_lines):
                    context["modified_functions"].append(func)
            
            # 3. 用 grep 找调用方
            for func in context["modified_functions"]:
                callers = self._find_callers(func.name)
                context["callers"].extend(callers)
        
        return context
    
    def _get_file_content(self, path: str) -> str | None:
        """获取文件内容"""
        try:
            result = subprocess.run(
                ["git", "show", f"HEAD:{path}"],
                cwd=self.repo_path, capture_output=True, text=True,
            )
            return result.stdout if result.returncode == 0 else None
        except Exception:
            return None
    
    def _find_callers(self, func_name: str) -> list[dict]:
        """用 grep 搜索函数的调用方"""
        result = subprocess.run(
            ["git", "grep", "-n", f"{func_name}("],
            cwd=self.repo_path, capture_output=True, text=True,
        )
        
        callers = []
        for line in result.stdout.strip().split("\n")[:10]:
            if ":" in line:
                file_path, rest = line.split(":", 1)
                callers.append({"file": file_path, "line": rest.strip()})
        
        return callers
```

| 上下文类型 | 收集方式 | 用途 |
|:---|:---|:---|
| 文件结构 | AST 解析 | 让 AI 了解全局视野 |
| 被修改函数签名 | AST + 行号交叉 | 判断参数/返回值变更 |
| 调用方 | `git grep` | 检测 Breaking Change |
| 相关 import | AST 提取 | 判断依赖是否正确 |

### 3.4 构建 Review Prompt：把代码变成 LLM 能理解的格式

把 Diff + 上下文组装成一个结构清晰的 Prompt 输入：

```python
class ReviewPromptBuilder:
    """构建 LLM Review 用的 Prompt"""
    
    def build(self, file_change: FileChange,
              context: dict) -> str:
        """构建单个文件的 Review Prompt 输入"""
        
        sections = []
        
        # 1. 文件信息
        sections.append(
            f"## 文件: {file_change.path}\n"
            f"语言: {file_change.language}\n"
            f"变更类型: {file_change.change_type}\n"
            f"新增 {len(file_change.added_lines)} 行, "
            f"删除 {len(file_change.removed_lines)} 行"
        )
        
        # 2. 文件结构摘要（帮助 AI 理解全局）
        if context.get("file_structure"):
            structure = context["file_structure"]
            funcs = ", ".join(f.name for f in structure.functions)
            sections.append(
                f"## 文件结构\n"
                f"函数: {funcs}\n"
                f"导入: {', '.join(structure.imports[:10])}"
            )
        
        # 3. 被修改的函数签名
        if context.get("modified_functions"):
            sigs = []
            for f in context["modified_functions"]:
                sig = f"def {f.name}({', '.join(f.args)})"
                if f.return_type:
                    sig += f" -> {f.return_type}"
                if f.docstring:
                    sig += f"\n    '''{f.docstring[:100]}'''"
                sigs.append(sig)
            sections.append(f"## 被修改的函数\n```python\n" +
                          "\n\n".join(sigs) + "\n```")
        
        # 4. Diff 内容（核心）
        sections.append(f"## 代码变更\n```diff\n{file_change.patch_text}\n```")
        
        # 5. 调用方信息
        if context.get("callers"):
            caller_text = "\n".join(
                f"- {c['file']}: {c['line']}" 
                for c in context["callers"][:5]
            )
            sections.append(f"## 调用方\n{caller_text}")
        
        return "\n\n".join(sections)
```

```
最终发给 LLM 的 Prompt 结构：

  ┌────────────────────────────────────────┐
  │  System Prompt（审查规则 + 输出格式）    │  ← 固定
  ├────────────────────────────────────────┤
  │  ## 文件: utils/auth.py                │  ← 文件信息
  │  语言: python, 变更: modified           │
  ├────────────────────────────────────────┤
  │  ## 文件结构                            │  ← 全局视野
  │  函数: verify_token, refresh_token      │
  │  导入: jwt, datetime                    │
  ├────────────────────────────────────────┤
  │  ## 被修改的函数                         │  ← 函数签名
  │  def verify_token(token: str) -> dict   │
  ├────────────────────────────────────────┤
  │  ## 代码变更                            │  ← Diff 核心
  │  ```diff                               │
  │  - decoded = jwt.decode(token, KEY)     │
  │  + try:                                │
  │  +     decoded = jwt.decode(...)        │
  │  ```                                   │
  ├────────────────────────────────────────┤
  │  ## 调用方                              │  ← 影响范围
  │  - api/routes.py: result = verify_...   │
  └────────────────────────────────────────┘
```

> 💡 **上下文的取舍**：给太多上下文，LLM 会迷失在信息海洋里；给太少，它又会误判。经验法则：**文件结构 + 被修改函数签名 + Diff + 前 5 个调用方**，刚好让 AI 有足够信息做判断。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **上下文的重要性** | 纯看 Diff 会漏掉类型不匹配、Breaking Change 等问题 |
| **AST 解析** | `ast` 模块提取函数签名、类结构、import 关系 |
| **上下文收集** | 被修改函数签名 + `git grep` 找调用方 |
| **Prompt 构建** | 文件信息 + 结构摘要 + 函数签名 + Diff + 调用方 |

---

## 4. LLM Review 引擎：核心审查逻辑

前面三章解决了"输入"问题——把代码变更解析成 LLM 能读懂的格式。这一章解决"审查"本身——如何让 LLM 像一个有 10 年经验的高级工程师一样审查代码。

### 4.1 Review Prompt 工程：让 LLM 像高级工程师一样审查

System Prompt 是 AI Review 的灵魂——它决定了审查的深度、维度和输出质量：

```python
REVIEW_SYSTEM_PROMPT = """你是一位拥有 10 年经验的高级软件工程师，正在进行 Code Review。

## 审查原则
1. 只评论**需要修改的问题**，不要夸奖已经写得好的代码
2. 每个问题必须给出**具体的修改建议**，不要只说"建议优化"
3. 区分严重程度：Critical（必须修）> Warning（应该修）> Suggestion（可以修）
4. 不要重复 Linter 能发现的问题（格式、命名风格）
5. 重点关注：逻辑错误、安全漏洞、性能问题、边界条件
6. 如果没有发现问题，就说"LGTM"，不要强行找问题

## 审查维度（按优先级）
1. **正确性**：逻辑是否正确，边界条件是否处理
2. **安全性**：是否有注入、泄露、硬编码密码等
3. **性能**：是否有 N+1 查询、不必要的计算、内存泄漏
4. **可维护性**：命名是否清晰、是否有 Magic Number、函数是否过长
5. **错误处理**：异常是否妥善处理、是否有 bare except

## 输出格式
以 JSON 数组返回，每个元素：
```json
{
    "file": "文件路径",
    "line": 行号,
    "severity": "critical|warning|suggestion",
    "category": "bug|security|performance|style|maintainability",
    "message": "问题描述",
    "suggestion": "具体修改建议（含代码示例）"
}
```
如果没有问题，返回 `[]`。
"""
```

### 4.2 多维度审查：Bug、安全、性能、风格、可维护性

每个维度的审查重点不同——这里列出各维度的典型模式，帮助你理解 AI 会检测什么：

```
五个审查维度的典型检测项：

  🐛 Bug 检测
  ═══════════════════════════════════════
  • 空指针/空值访问（data["key"] 但 data 可能为 None）
  • 数组越界（for i in range(len(arr)+1)）
  • 条件分支遗漏（if/elif 没有 else 兜底）
  • 资源未释放（打开文件/连接但没 close）
  • 并发问题（共享状态没有锁保护）

  🔒 安全漏洞
  ═══════════════════════════════════════
  • SQL 注入（字符串拼接 SQL）
  • 硬编码密钥（SECRET_KEY = "abc123"）
  • 路径遍历（用户输入直接拼文件路径）
  • 不安全的反序列化（pickle.loads 用户数据）
  • SSRF（用户控制的 URL 直接请求）

  ⚡ 性能问题
  ═══════════════════════════════════════
  • N+1 查询（循环中执行数据库查询）
  • 不必要的全表扫描
  • 大列表的重复遍历（应该用 set/dict）
  • 同步阻塞（在 async 中调用同步 IO）
  • 冗余计算（循环内不变的表达式）

  📐 代码风格
  ═══════════════════════════════════════
  • Magic Number（if status == 3）
  • 函数过长（> 50 行应该拆分）
  • 嵌套过深（if 套 if 套 if）
  • 命名不清晰（def f(x, y) 代替 calculate_total）

  🔧 可维护性
  ═══════════════════════════════════════
  • 重复代码（DRY 原则）
  • 缺少错误处理（bare try/except）
  • 耦合过紧（硬编码依赖而非注入）
  • 缺少类型注解
```

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class ReviewEngine:
    """LLM 代码审查引擎"""
    
    def __init__(self, model: str = "deepseek-coder"):
        self.llm = ChatOpenAI(
            model=model, temperature=0,
            base_url="https://api.deepseek.com/v1",
        )
    
    async def review(self, prompt_input: str) -> list[dict]:
        """审查代码，返回问题列表"""
        messages = [
            SystemMessage(content=REVIEW_SYSTEM_PROMPT),
            HumanMessage(content=prompt_input),
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # 解析 JSON 输出
        return self._parse_response(response.content)
    
    def _parse_response(self, content: str) -> list[dict]:
        """解析 LLM 返回的 JSON"""
        import json, re
        
        # 提取 JSON 部分（LLM 可能在前后加了解释文字）
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if not json_match:
            return []
        
        try:
            issues = json.loads(json_match.group())
            # 校验必要字段
            valid = []
            for issue in issues:
                if all(k in issue for k in 
                       ("file", "severity", "message")):
                    valid.append(issue)
            return valid
        except json.JSONDecodeError:
            return []
```

> 💡 **temperature=0 是关键**：代码审查需要严谨和确定性，不要让 LLM "发挥创意"。temperature=0 确保相同输入得到相似输出，减少随机误报。

### 4.3 结构化输出：从自由文本到可操作的 Review 结果

用 Pydantic 定义严格的输出模型，确保 LLM 返回的结果可以直接被程序消费：

```python
from pydantic import BaseModel, Field
from enum import Enum

class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    SUGGESTION = "suggestion"

class Category(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    MAINTAINABILITY = "maintainability"

class ReviewIssue(BaseModel):
    """单个审查问题"""
    file: str = Field(description="文件路径")
    line: int | None = Field(default=None, description="问题所在行号")
    severity: Severity = Field(description="严重程度")
    category: Category = Field(description="问题类别")
    message: str = Field(description="问题描述")
    suggestion: str = Field(description="修改建议，含代码示例")

class ReviewResult(BaseModel):
    """完整审查结果"""
    issues: list[ReviewIssue] = Field(default_factory=list)
    summary: str = Field(default="", description="总结评语")
    
    @property
    def has_critical(self) -> bool:
        return any(i.severity == Severity.CRITICAL for i in self.issues)
    
    @property
    def stats(self) -> dict:
        from collections import Counter
        return dict(Counter(i.severity.value for i in self.issues))
```

```python
# ── ReviewEngine 增强版：使用 Pydantic 解析 ──

class ReviewEngineV2(ReviewEngine):
    """增强版：输出 Pydantic 模型"""
    
    async def review(self, prompt_input: str) -> ReviewResult:
        messages = [
            SystemMessage(content=REVIEW_SYSTEM_PROMPT),
            HumanMessage(content=prompt_input),
        ]
        
        response = await self.llm.ainvoke(messages)
        raw_issues = self._parse_response(response.content)
        
        # 用 Pydantic 校验每个 issue
        valid_issues = []
        for raw in raw_issues:
            try:
                issue = ReviewIssue(**raw)
                valid_issues.append(issue)
            except Exception:
                continue  # 跳过格式不合法的
        
        return ReviewResult(
            issues=valid_issues,
            summary=self._generate_summary(valid_issues),
        )
    
    def _generate_summary(self, issues: list[ReviewIssue]) -> str:
        if not issues:
            return "✅ LGTM! 没有发现需要修改的问题。"
        
        stats = {}
        for i in issues:
            stats[i.severity.value] = stats.get(i.severity.value, 0) + 1
        
        parts = []
        if stats.get("critical"):
            parts.append(f"🔴 {stats['critical']} 个严重问题")
        if stats.get("warning"):
            parts.append(f"🟡 {stats['warning']} 个警告")
        if stats.get("suggestion"):
            parts.append(f"🔵 {stats['suggestion']} 个建议")
        
        return f"发现 {len(issues)} 个问题：" + "、".join(parts)
```

### 4.4 审查结果分级：Critical / Warning / Suggestion

不是所有问题都一样紧急——分级决定了开发者看到评论后的行动优先级：

| 级别 | 含义 | PR 策略 | 示例 |
|:---|:---|:---|:---|
| 🔴 **Critical** | 必须修复 | 阻止合并 | SQL 注入、空指针 crash |
| 🟡 **Warning** | 强烈建议修复 | 建议修再合并 | 缺少错误处理、N+1 查询 |
| 🔵 **Suggestion** | 可以改进 | 不阻止合并 | 命名优化、添加注释 |

```python
class ReviewGatekeeper:
    """Review 门禁：根据审查结果决定 PR 状态"""
    
    def evaluate(self, result: ReviewResult) -> dict:
        """判断 PR 是否可以合并"""
        stats = result.stats
        
        if stats.get("critical", 0) > 0:
            return {
                "status": "changes_requested",
                "can_merge": False,
                "reason": f"发现 {stats['critical']} 个严重问题，必须修复后才能合并",
            }
        
        if stats.get("warning", 0) >= 3:
            return {
                "status": "changes_requested",
                "can_merge": False,
                "reason": f"警告数过多（{stats['warning']}个），建议修复后合并",
            }
        
        return {
            "status": "approved",
            "can_merge": True,
            "reason": "没有阻塞性问题" + (
                f"，但有 {stats.get('suggestion', 0)} 个改进建议"
                if stats.get("suggestion") else ""
            ),
        }
```

```
审查结果的 PR 评论效果：

  ┌──────────────────────────────────────────────┐
  │  🤖 AI Code Review                           │
  │                                               │
  │  发现 4 个问题：🔴 1 个严重 🟡 2 个警告 🔵 1 个建议 │
  │                                               │
  │  🔴 Critical: utils/auth.py:23                │
  │  jwt.decode() 未指定 algorithms 参数           │
  │  → 可能导致算法混淆攻击                        │
  │  建议：jwt.decode(token, KEY, algorithms=["HS256"]) │
  │                                               │
  │  🟡 Warning: services/order.py:45             │
  │  循环中调用 db.query()，存在 N+1 查询问题       │
  │  建议：在循环外一次性查询                       │
  │                                               │
  │  状态：❌ Changes Requested                    │
  └──────────────────────────────────────────────┘
```

> 💡 **分级的核心原则**：宁可漏报 Suggestion，也不要误报 Critical。一旦开发者发现 AI 频繁误报严重问题，就会开始忽略所有 AI Review——这就是失去信任的代价。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **System Prompt** | 角色设定 + 审查维度 + 输出格式 = 审查质量的决定因素 |
| **五个维度** | Bug → 安全 → 性能 → 风格 → 可维护性（按优先级） |
| **结构化输出** | Pydantic 模型校验 + JSON 提取 = 可靠的结果解析 |
| **三级分类** | Critical（阻止合并）/ Warning（建议修）/ Suggestion（参考） |

---

## 5. 与 Git 平台集成：自动化工作流

审查引擎再强大，如果需要手动触发、手动复制结果，开发者就不会用。这一章把 AI Review 直接嵌入开发者的日常工作流——PR 一创建就自动审查，结果自动评论到 PR 上。

### 5.1 GitHub 集成：Webhook 监听 + PR 评论 API

```python
# webhook/github_handler.py
import hmac, hashlib
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

async def verify_signature(request: Request, secret: str):
    """验证 GitHub Webhook 签名"""
    signature = request.headers.get("X-Hub-Signature-256", "")
    body = await request.body()
    expected = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")

@router.post("/webhook/github")
async def handle_github_webhook(request: Request):
    """处理 GitHub Webhook 事件"""
    await verify_signature(request, os.getenv("GITHUB_WEBHOOK_SECRET"))
    
    event = request.headers.get("X-GitHub-Event")
    payload = await request.json()
    
    if event == "pull_request" and \
       payload["action"] in ("opened", "synchronize"):
        # PR 创建或更新 → 触发审查
        pr = payload["pull_request"]
        await review_pull_request(
            repo=payload["repository"]["full_name"],
            pr_number=pr["number"],
            base=pr["base"]["sha"],
            head=pr["head"]["sha"],
        )
    
    return {"status": "ok"}
```

```python
# integrations/github_client.py
from github import Github

class GitHubReviewClient:
    """GitHub PR 评论客户端"""
    
    def __init__(self, token: str):
        self.gh = Github(token)
    
    async def post_review(self, repo_name: str, pr_number: int,
                          result: ReviewResult):
        """把审查结果发布到 PR"""
        repo = self.gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # 1. 发布行级评论（inline comments）
        comments = []
        for issue in result.issues:
            if issue.line:
                comments.append({
                    "path": issue.file,
                    "line": issue.line,
                    "body": self._format_comment(issue),
                })
        
        # 2. 提交 Review（带总结）
        event = "REQUEST_CHANGES" if result.has_critical \
                else "COMMENT"
        
        pr.create_review(
            body=self._format_summary(result),
            event=event,
            comments=comments,
        )
    
    def _format_comment(self, issue: ReviewIssue) -> str:
        """格式化单条评论"""
        icon = {"critical": "🔴", "warning": "🟡", 
                "suggestion": "🔵"}[issue.severity.value]
        
        return (f"{icon} **{issue.severity.value.upper()}** "
                f"| {issue.category.value}\n\n"
                f"{issue.message}\n\n"
                f"**建议：**\n{issue.suggestion}")
    
    def _format_summary(self, result: ReviewResult) -> str:
        """格式化总结评语"""
        return (f"## 🤖 AI Code Review\n\n"
                f"{result.summary}\n\n"
                f"---\n"
                f"*Powered by AI Code Reviewer*")
```

### 5.2 GitLab 集成：MR 事件 + Discussion API

```python
# integrations/gitlab_client.py
import gitlab

class GitLabReviewClient:
    """GitLab MR 评论客户端"""
    
    def __init__(self, url: str, token: str):
        self.gl = gitlab.Gitlab(url, private_token=token)
    
    async def post_review(self, project_id: int, mr_iid: int,
                          result: ReviewResult):
        """把审查结果发布到 MR"""
        project = self.gl.projects.get(project_id)
        mr = project.mergerequests.get(mr_iid)
        
        # GitLab 用 Discussion 实现行级评论
        for issue in result.issues:
            if issue.line:
                mr.discussions.create({
                    "body": self._format_comment(issue),
                    "position": {
                        "position_type": "text",
                        "new_path": issue.file,
                        "new_line": issue.line,
                        "base_sha": mr.diff_refs["base_sha"],
                        "head_sha": mr.diff_refs["head_sha"],
                        "start_sha": mr.diff_refs["start_sha"],
                    }
                })
        
        # 发布总结 Note
        mr.notes.create({"body": self._format_summary(result)})
```

| 对比 | GitHub | GitLab |
|:---|:---|:---|
| 触发事件 | `pull_request` | `merge_request` |
| 行级评论 | `create_review(comments=[])` | `discussions.create(position=)` |
| 总结评论 | Review body | `notes.create()` |
| 状态设置 | `REQUEST_CHANGES` / `APPROVE` | `mr.approve()` / 手动 |
| API 库 | `PyGithub` | `python-gitlab` |

### 5.3 Git Hook 本地审查：pre-commit 与 pre-push

不想等 CI/CD 跑完？用 Git Hook 在本地提交前就做一轮快速审查：

```bash
#!/bin/bash
# .git/hooks/pre-push（需要 chmod +x）

echo "🤖 Running AI Code Review..."

# 获取即将 push 的变更
DIFF=$(git diff origin/main...HEAD)

if [ -z "$DIFF" ]; then
    echo "✅ No changes to review."
    exit 0
fi

# 调用本地 Review 脚本
RESULT=$(python scripts/local_review.py --diff "$DIFF" 2>&1)
EXIT_CODE=$?

echo "$RESULT"

# 有 Critical 问题就阻止 push
if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ AI Review 发现严重问题，请修复后再 push。"
    echo "   使用 git push --no-verify 可以强制跳过。"
    exit 1
fi

echo "✅ AI Review passed."
exit 0
```

```python
# scripts/local_review.py
"""本地 Review 脚本：用于 Git Hook"""
import sys, asyncio

async def main():
    diff_text = sys.stdin.read() if not sys.argv[1:] else sys.argv[2]
    
    parser = DiffParser()
    result = parser.parse(diff_text)
    
    filt = DiffFilter()
    files = filt.filter(result)
    
    if not files:
        print("✅ 没有需要 Review 的代码变更")
        sys.exit(0)
    
    engine = ReviewEngineV2()
    builder = ReviewPromptBuilder()
    
    all_issues = []
    for f in files[:5]:  # 本地模式限制文件数
        prompt = builder.build(f, {})
        review = await engine.review(prompt)
        all_issues.extend(review.issues)
    
    # 输出结果
    for issue in all_issues:
        icon = {"critical": "🔴", "warning": "🟡",
                "suggestion": "🔵"}[issue.severity.value]
        print(f"  {icon} {issue.file}:{issue.line} {issue.message}")
    
    # Critical → 非零退出码 → 阻止 push
    if any(i.severity.value == "critical" for i in all_issues):
        sys.exit(1)

asyncio.run(main())
```

### 5.4 CI/CD 集成：GitHub Actions 完整示例

把 AI Review 做成可复用的 GitHub Action：

```yaml
# .github/workflows/ai-review.yml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  pull-requests: write
  contents: read

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # 需要完整历史来生成 diff

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Get PR diff
        run: |
          git diff ${{ github.event.pull_request.base.sha }}...\
                   ${{ github.event.pull_request.head.sha }} > pr.diff

      - name: Run AI Review
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python scripts/ci_review.py \
            --diff-file pr.diff \
            --repo ${{ github.repository }} \
            --pr ${{ github.event.pull_request.number }}
```

```
三种集成方式对比：

  Git Hook（本地）
  ═══════════════════════════════════════
  ✅ 即时反馈，push 前就拦截
  ❌ 依赖开发者本地环境
  ❌ 可以 --no-verify 跳过
  → 适合个人使用

  Webhook（服务端）
  ═══════════════════════════════════════
  ✅ 完全自动化，无法绕过
  ✅ 支持复杂逻辑（上下文收集、缓存）
  ❌ 需要部署服务器
  → 适合有运维团队的公司

  GitHub Actions（CI/CD）
  ═══════════════════════════════════════
  ✅ 零运维，GitHub 托管
  ✅ 无法绕过
  ❌ 受 Actions 并发限制
  → 最推荐的方式
```

> 💡 **推荐组合**：GitHub Actions（主力，每个 PR 必跑）+ Git Hook（辅助，开发者本地快速反馈）。两者用同一套 Review 引擎，保证审查标准一致。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **GitHub 集成** | Webhook 监听 PR 事件 + `create_review()` 发布行级评论 |
| **GitLab 集成** | MR 事件 + `discussions.create(position=)` 行级评论 |
| **Git Hook** | `pre-push` 脚本在本地拦截，Critical 问题阻止 push |
| **GitHub Actions** | 零运维的 CI/CD 方案，最推荐的集成方式 |

---

## 6. 高级特性：从能用到好用

基础版能跑了，但要让团队真正用起来，还需要解决几个关键问题：不要重复审、要遵守团队规范、误报要少、费用要省。

### 6.1 增量 Review：只审查新增的变更

PR 更新后重新审查，不能把之前已经审过的代码再报一遍：

```python
import hashlib

class IncrementalReviewer:
    """增量审查：只审查新变更"""
    
    def __init__(self):
        self.reviewed_cache: dict[str, set[str]] = {}
    
    def get_new_changes(self, pr_id: str, 
                        files: list[FileChange]) -> list[FileChange]:
        """过滤出未审查过的变更"""
        reviewed = self.reviewed_cache.get(pr_id, set())
        new_files = []
        
        for f in files:
            # 用 patch 内容的 hash 判断是否已审查
            content_hash = hashlib.md5(
                f.patch_text.encode()
            ).hexdigest()
            
            if content_hash not in reviewed:
                new_files.append(f)
                reviewed.add(content_hash)
        
        self.reviewed_cache[pr_id] = reviewed
        return new_files
```

### 6.2 团队规范注入：让 AI 遵守你的编码标准

每个团队有自己的规范——把它注入 Prompt，AI 就变成了"懂你们规矩的 Reviewer"：

```python
# 团队规范配置文件：.ai-review.yml
TEAM_RULES_TEMPLATE = """
## 团队编码规范（额外审查规则）

{rules}

请在审查时，除了通用规则外，还要检查以上团队规范。
违反团队规范的问题标记为 Warning。
"""

def load_team_rules(repo_path: str) -> str:
    """加载团队规范文件"""
    import yaml
    config_path = f"{repo_path}/.ai-review.yml"
    
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        rules = config.get("rules", [])
        return TEAM_RULES_TEMPLATE.format(
            rules="\n".join(f"- {r}" for r in rules)
        )
    except FileNotFoundError:
        return ""  # 没有配置文件就用默认规则
```

```yaml
# .ai-review.yml 示例
rules:
  - "所有 API 接口函数必须有类型注解"
  - "数据库查询必须使用 ORM，禁止裸 SQL"
  - "环境变量必须通过 config.py 访问，不能直接 os.getenv"
  - "日志必须使用 structlog，不能用 print"
  - "所有公开函数必须有 docstring"

skip_patterns:
  - "tests/fixtures/*"
  - "scripts/one_off/*"

severity_override:
  "missing_type_annotation": "warning"
  "missing_docstring": "suggestion"
```

### 6.3 误报过滤与反馈学习：越用越准

开发者标记"这不是问题"后，系统要学会不再报类似问题：

```python
class FeedbackTracker:
    """追踪开发者反馈，减少误报"""
    
    def __init__(self):
        self.dismissed: list[dict] = []  # 被驳回的问题
    
    def record_dismissal(self, issue: ReviewIssue, 
                          reason: str):
        """记录被驳回的问题"""
        self.dismissed.append({
            "pattern": issue.message[:50],
            "category": issue.category.value,
            "file_pattern": issue.file.rsplit("/", 1)[-1],
            "reason": reason,
            "count": 1,
        })
    
    def should_suppress(self, issue: ReviewIssue) -> bool:
        """检查是否应该抑制（相似问题被驳回≥3次）"""
        similar = [
            d for d in self.dismissed
            if d["category"] == issue.category.value
            and self._is_similar(d["pattern"], issue.message)
        ]
        return sum(d["count"] for d in similar) >= 3
    
    def _is_similar(self, a: str, b: str) -> bool:
        """简单相似度判断"""
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        overlap = len(words_a & words_b) / max(len(words_a | words_b), 1)
        return overlap > 0.6
```

### 6.4 成本控制：Token 优化与缓存策略

| 优化手段 | 节省幅度 | 实现方式 |
|:---|:---|:---|
| 文件过滤 | 40-60% | 跳过锁文件、文档、图片 |
| 增量审查 | 30-50% | 只审查新变更，不重复审查 |
| 语义缓存 | 20-30% | 相似 Diff 复用 Review 结果 |
| 模型分级 | 50% | Suggestion 用便宜模型，Critical 用强模型 |
| 上下文精简 | 20% | 只传必要的函数签名，不传整个文件 |

```python
class CostTracker:
    """Token 用量与成本追踪"""
    
    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0.0
    
    def track(self, input_tokens: int, output_tokens: int,
              model: str = "deepseek-coder"):
        """记录一次调用"""
        # DeepSeek-Coder 价格
        prices = {
            "deepseek-coder": {"input": 0.001, "output": 0.002},
            "gpt-4o": {"input": 0.005, "output": 0.015},
        }
        
        price = prices.get(model, prices["deepseek-coder"])
        cost = (input_tokens * price["input"] + 
                output_tokens * price["output"]) / 1000
        
        self.total_tokens += input_tokens + output_tokens
        self.total_cost += cost
```

> 💡 **性价比最优方案**：先用 DeepSeek-Coder 做全面扫描（便宜），发现 Critical 问题时再用 GPT-4o 二次确认（准确）。这样单次 PR Review 成本可以控制在 ¥0.1-0.5。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **增量审查** | 用 patch hash 跳过已审查的变更 |
| **团队规范** | `.ai-review.yml` 注入 Prompt，让 AI 遵守你的规矩 |
| **误报过滤** | 追踪驳回反馈，相似问题被驳回 ≥3 次自动抑制 |
| **成本控制** | 文件过滤 + 增量 + 模型分级，单次 ≤ ¥0.5 |

---

## 7. 评测与质量保障

AI Review 最大的风险是**失去开发者信任**——误报太多，大家就开始无视 AI 的评论。这一章建立评测体系，用数据证明 AI Review 的价值。

### 7.1 Review 质量的核心指标

| 指标 | 公式 | 目标值 | 意义 |
|:---|:---|:---|:---|
| **精确率** | 真问题 / AI 报出的总问题 | > 70% | 误报率要低 |
| **召回率** | AI 发现 / 实际存在的总问题 | > 50% | 别漏掉严重 Bug |
| **Critical 精确率** | 真 Critical / AI 报 Critical | > 85% | 最重要！误报 Critical 会失去信任 |
| **LGTM 准确率** | AI 说 LGTM 且确实没问题 / AI 说 LGTM | > 95% | 别放过有问题的代码 |
| **平均审查时间** | PR 创建到评论发出的时间 | < 3 分钟 | 速度要快 |

### 7.2 构建评测数据集：用已知 Bug 验证 AI 审查

```python
# 评测数据集结构
eval_dataset = [
    {
        "id": "eval_001",
        "description": "SQL 注入漏洞",
        "diff": """
-    query = f"SELECT * FROM users WHERE id = {user_id}"
+    query = f"SELECT * FROM users WHERE id = '{user_input}'"
""",
        "expected_issues": [
            {"severity": "critical", "category": "security",
             "pattern": "SQL injection"},
        ],
    },
    {
        "id": "eval_002",
        "description": "资源未释放",
        "diff": """
+    f = open("data.txt")
+    content = f.read()
+    return process(content)
""",
        "expected_issues": [
            {"severity": "warning", "category": "bug",
             "pattern": "file not closed"},
        ],
    },
    # ... 50-100 条评测用例
]

class ReviewEvaluator:
    """Review 质量评测"""
    
    async def evaluate(self, engine: ReviewEngineV2,
                       dataset: list[dict]) -> dict:
        results = {"tp": 0, "fp": 0, "fn": 0}
        
        for sample in dataset:
            review = await engine.review(sample["diff"])
            
            expected = {e["pattern"] for e in sample["expected_issues"]}
            found = {i.message[:30] for i in review.issues}
            
            # 简化匹配（实际应用中用语义相似度）
            for exp in expected:
                if any(exp.lower() in f.lower() for f in found):
                    results["tp"] += 1
                else:
                    results["fn"] += 1
            
            false_positives = len(review.issues) - results["tp"]
            results["fp"] += max(0, false_positives)
        
        precision = results["tp"] / max(results["tp"] + results["fp"], 1)
        recall = results["tp"] / max(results["tp"] + results["fn"], 1)
        
        return {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(2 * precision * recall / max(precision + recall, 0.001), 3),
        }
```

### 7.3 AI Review vs 人工 Review：对比实验

```
对比实验设计：

  准备：100 个真实 PR（含已知问题）
      │
      ├─→ AI Review → 记录发现的问题
      │
      └─→ 3 位高级工程师 Review → 记录发现的问题
      │
      ▼
  对比结果（典型数据）：

  指标              AI Review    人工 Review
  ──────────────────────────────────────────
  平均耗时          2.3 分钟      45 分钟
  Bug 发现率        62%           78%
  安全漏洞发现率    85%           55%
  风格问题发现率    92%           40%
  误报率            25%           8%
  ──────────────────────────────────────────
  
  结论：AI 在安全和风格上胜出，
       人类在复杂逻辑和业务理解上胜出。
       两者互补效果最好。
```

### 7.4 Prompt 迭代优化的闭环

```
Prompt 优化的迭代流程：

  Step 1：收集 Bad Case
  ═══════════════════════════════════════
  • 误报（AI 说有问题，实际没有）
  • 漏报（AI 没发现，人工发现了）
  每周收集 10-20 条

  Step 2：分析失败模式
  ═══════════════════════════════════════
  误报主要原因：
  • 不理解业务上下文  → 加更多上下文
  • 过度敏感          → 在 Prompt 中加 "不要报" 的例子
  漏报主要原因：
  • 不了解该语言特性  → 加语言专属规则
  • 上下文不够        → 收集更多关联代码

  Step 3：修改 Prompt → 跑评测 → 对比指标
  ═══════════════════════════════════════
  前后对比 precision/recall/F1
  指标提升 → 发布新版本
  指标下降 → 回滚，继续分析
```

> 💡 **关于评测数据集的维护**：最好的评测用例来自真实的 Bug。每次线上出 Bug，把对应的 PR Diff + Bug 信息加入评测集。这样评测集会越来越贴近真实场景。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **核心指标** | 精确率（> 70%）+ Critical 精确率（> 85%）最重要 |
| **评测数据集** | 50-100 条含已知 Bug 的 Diff，持续从线上 Bug 补充 |
| **AI vs 人工** | AI 赢在速度/安全/风格，人工赢在业务逻辑，互补最佳 |
| **Prompt 迭代** | 收集 Bad Case → 分析失败模式 → 改 Prompt → 跑评测 |

---

## 8. 综合实战：从 0 到 1 构建完整系统

把前 7 章的所有模块串联——用 FastAPI + GitHub App 构建完整的 AI Code Review 服务。

### 8.1 系统架构与项目结构

```
ai-code-reviewer/
├── main.py                        # FastAPI 入口
├── config.py                      # 配置管理
├── requirements.txt
├── Dockerfile
│
├── core/
│   ├── diff_parser.py             # Diff 解析（第 2 章）
│   ├── diff_filter.py             # 文件过滤
│   ├── diff_chunker.py            # 分块策略
│   ├── code_analyzer.py           # AST 分析（第 3 章）
│   ├── context_collector.py       # 上下文收集
│   └── prompt_builder.py          # Prompt 构建
│
├── engine/
│   ├── review_engine.py           # LLM 审查（第 4 章）
│   ├── models.py                  # Pydantic 模型
│   └── gatekeeper.py              # 门禁逻辑
│
├── integrations/
│   ├── github_client.py           # GitHub API（第 5 章）
│   ├── gitlab_client.py           # GitLab API
│   └── webhook_handler.py         # Webhook 处理
│
├── advanced/
│   ├── incremental.py             # 增量审查（第 6 章）
│   ├── team_rules.py              # 团队规范
│   ├── feedback.py                # 反馈追踪
│   └── cost_tracker.py            # 成本追踪
│
├── scripts/
│   ├── local_review.py            # 本地 Review 脚本
│   └── ci_review.py               # CI/CD Review 脚本
│
└── .github/workflows/
    └── ai-review.yml              # GitHub Actions
```

### 8.2 实现 Webhook 监听与 Diff 解析

```python
# main.py
from fastapi import FastAPI
from integrations.webhook_handler import router as webhook_router

app = FastAPI(title="AI Code Reviewer")

app.include_router(webhook_router)

@app.on_event("startup")
async def startup():
    """初始化各模块"""
    app.state.review_engine = ReviewEngineV2()
    app.state.diff_parser = DiffParser()
    app.state.diff_filter = DiffFilter()
    app.state.github_client = GitHubReviewClient(
        token=os.getenv("GITHUB_TOKEN")
    )

# ── 核心 Review 流程 ──
async def review_pull_request(repo: str, pr_number: int,
                               base: str, head: str):
    """完整的 PR Review 流程"""
    
    # 1. 获取 Diff
    diff_text = get_pr_diff_via_api(repo, pr_number)
    
    # 2. 解析
    diff_result = app.state.diff_parser.parse(diff_text)
    
    # 3. 过滤
    files = app.state.diff_filter.filter(diff_result)
    
    # 4. 分块
    chunker = DiffChunker()
    chunks = chunker.chunk(files)
    
    # 5. 逐块审查
    all_issues = []
    for chunk in chunks:
        builder = ReviewPromptBuilder()
        for f in chunk:
            context = ContextCollector(repo).collect(f)
            prompt = builder.build(f, context)
            result = await app.state.review_engine.review(prompt)
            all_issues.extend(result.issues)
    
    # 6. 发布评论
    final_result = ReviewResult(issues=all_issues)
    await app.state.github_client.post_review(
        repo, pr_number, final_result
    )
```

### 8.3 实现 LLM Review 引擎与自动评论

```
完整的请求链路：

  GitHub PR 创建
      │
      ▼
  Webhook POST /webhook/github
      │  验证签名 → 解析 payload
      ▼
  获取 PR Diff（GitHub API）
      │
      ▼
  DiffParser.parse()
      │  unified diff → FileChange 列表
      ▼
  DiffFilter.filter()
      │  跳过锁文件/图片 → 优先级排序
      ▼
  DiffChunker.chunk()
      │  按 300 行分组
      ▼
  ReviewEngineV2.review()  ×N 个 chunk
      │  System Prompt + 代码 → LLM → JSON 解析
      ▼
  GitHubReviewClient.post_review()
      │  行级评论 + 总结 + 状态标记
      ▼
  PR 页面出现 AI Review 评论 ✅
```

### 8.4 部署与运维：Docker + 监控 + 日志

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "main:app"]
```

```yaml
# docker-compose.yml
services:
  reviewer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET}
    restart: unless-stopped
    
  # 可选：Redis 缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

> 💡 **生产部署清单**：① HTTPS（用 Nginx 反代 + Let's Encrypt）；② GitHub Webhook 配置（Settings → Webhooks → 填入你的 URL）；③ 日志持久化（挂载 volume 或接 ELK）；④ 健康检查（`/health` 端点）。

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **项目结构** | core（解析）+ engine（审查）+ integrations（集成）+ advanced（高级） |
| **请求链路** | Webhook → Diff → 过滤 → 分块 → LLM Review → 发评论 |
| **部署方案** | Docker + Gunicorn + Nginx，Redis 做缓存 |

---

## 附录：AI 代码审查工程速查手册

### A.1 Review Prompt 模板库（Python / TypeScript / Go）

**Python 专属补充规则：**

```
- 检查 async 函数中是否有同步阻塞调用（如 time.sleep、open）
- f-string 中是否有复杂表达式（应提取为变量）
- 检查 mutable 默认参数（def func(items=[]) 是经典 Bug）
- 使用 with 语句管理文件/连接/锁
- 检查 __init__.py 是否暴露了不该暴露的内部符号
```

**TypeScript 专属补充规则：**

```
- 检查 any 类型的使用（应该尽量避免）
- 检查 null/undefined 是否有安全处理（optional chaining）
- async/await 是否有 try-catch 包裹
- React Hooks 的依赖数组是否完整
- 是否有未处理的 Promise（缺少 await 或 .catch）
```

**Go 专属补充规则：**

```
- 检查 error 是否被忽略（_ = someFunc()）
- defer 是否在正确的位置（循环中的 defer 泄漏）
- goroutine 是否有 panic recover
- context 是否正确传递和取消
- 检查 slice 是否有 nil 判断
```

### A.2 常见误报类型与过滤策略

| 误报类型 | 示例 | 过滤方式 |
|:---|:---|:---|
| 测试代码中的"硬编码" | `password = "test123"` 在测试文件中 | 检测文件路径含 `test` |
| 文档字符串中的"SQL" | docstring 里写了 SQL 示例 | 检测是否在注释/文档中 |
| Mock 数据的"安全问题" | fixtures 中的假数据 | 检测文件路径含 `fixtures` |
| 已有 Linter 覆盖的格式问题 | 缩进、空行 | 在 Prompt 中明确排除 |

### A.3 GitHub / GitLab API 速查

| 操作 | GitHub API | GitLab API |
|:---|:---|:---|
| 获取 PR/MR Diff | `GET /repos/{owner}/{repo}/pulls/{number}` | `GET /projects/{id}/merge_requests/{iid}/changes` |
| 添加行级评论 | `POST /repos/.../pulls/{number}/reviews` | `POST /projects/.../merge_requests/{iid}/discussions` |
| 添加总结评论 | Review body | `POST /projects/.../merge_requests/{iid}/notes` |
| 设置状态 | `event: "REQUEST_CHANGES"` | `POST .../approve` |
| 获取文件内容 | `GET /repos/.../contents/{path}` | `GET /projects/.../repository/files/{path}` |

### A.4 成本估算与优化参考

```
每 100 次 PR Review 的成本估算（DeepSeek-Coder）：

  组件          单价             数量     小计
  ───────────────────────────────────────────
  Diff 解析     免费（本地）     100      ¥0
  AST 分析      免费（本地）     100      ¥0
  LLM Review    ¥0.02/次        300      ¥6.0
  （平均每 PR 3 个 chunk）
  GitHub API    免费             100      ¥0
  服务器        ¥50/月           —        ¥1.7/天
  ───────────────────────────────────────────
  总计                                    ≈ ¥8/100次
  
  单次 PR Review 成本：≈ ¥0.08
  
  对比人工：100 × 30 分钟 × ¥150/小时 = ¥7,500
  AI Review 成本仅为人工的 0.1%
```

