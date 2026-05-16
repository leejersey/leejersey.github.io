# Agentic Coding 完全指南：从"写代码"到"指挥 AI 写代码"

> 2025 年，软件工程的范式正在发生根本性转变：开发者从"写代码的人"变成"指挥 AI 写代码的人"。这不是效率的量变，而是工作方式的质变。本指南将带你理解这场变革的全貌，掌握 Agentic Coding 的核心技能。

---

## 1. 范式转换：从 Copilot 到 Coding Agent

### 1.1 三次范式迭代：手写代码 → AI 补全 → AI Agent

```
软件开发的三次范式：

  第一代（~2021）：手写代码
    开发者写每一行代码
    工具只提供语法高亮和 IntelliSense
    
  第二代（2021-2024）：AI 补全
    Copilot/Codeium 提供行级/块级补全
    开发者写框架，AI 填充细节
    → 效率提升 30-50%，但本质还是"你在写代码"

  第三代（2025-）：Coding Agent
    开发者描述需求，Agent 自主完成
    规划 → 编码 → 测试 → 修复，全链路自动化
    → 不是效率提升，而是工作方式的根本改变
```

### 1.2 什么是 Agentic Coding：Agent 自主规划-编码-测试-修复

Agentic Coding 的核心特征——**Agent 能自主完成一个完整的编码任务**，而不是辅助你完成：

| 维度 | AI 补全（Copilot） | Agentic Coding |
|------|-------------------|----------------|
| 工作单元 | 一行/一块代码 | 一个完整功能/修复 |
| 主导权 | 人类主导，AI 辅助 | AI 主导，人类审查 |
| 上下文 | 当前文件 | 整个代码库 |
| 工具使用 | 无 | 文件系统/终端/搜索/浏览器 |
| 自我修复 | 不会 | 运行测试→发现错误→自动修复 |
| 类比 | 打字时的自动纠错 | 一个远程实习生 |

### 1.3 开发者的新角色：从码农到"AI 工程总监"

```
角色转变：

  旧模式：
    产品经理 → 需求文档 → 你写代码 → 你测试 → 你部署
    
  新模式：
    产品经理 → 需求文档 → 你设计约束 → Agent 写代码
                         → 你审查代码 → Agent 修复问题
                         → 你验收结果 → Agent 部署

  你的新核心技能：
  ① 上下文工程（Context Engineering）— 给 Agent 正确的信息
  ② 约束设计（Harness Engineering）— 给 Agent 安全的边界
  ③ 结果验证 — 确保 Agent 做对了
```

> 💡 **关键认知：** Agentic Coding 不是"更快地写代码"，而是"不再写代码"。你的价值从"写出正确的代码"转移到"定义什么是正确的"——这是架构师的工作，不是码农的工作。

---

## 2. 三大 Coding Agent 深度对比

2025-2026 年，三个产品定义了 Agentic Coding 的格局。它们不是"哪个更好"的关系，而是**三种不同的设计哲学**。

### 2.1 Claude Code：终端原生、深度自主

```
Claude Code 的设计哲学：

  "我就活在你的终端里。你告诉我做什么，我自己搞定。"
  
  核心特征：
  - 终端 CLI 原生，无 GUI 依赖
  - 直接操作你的本地文件系统和终端
  - 深度代码库理解（整个 repo 级别的上下文）
  - 自主多步执行：规划 → 编码 → 运行测试 → 修复 → 提交
  - CLAUDE.md 持久化项目记忆
  
  杀手级场景：
  - 大规模跨文件重构
  - 复杂 Bug 调试（Agent 会自己加日志、运行、分析）
  - 从零搭建项目脚手架
```

### 2.2 OpenAI Codex：云端沙箱、异步委派

```
Codex 的设计哲学：

  "把任务交给我，你去忙别的。我在云端做完了通知你。"
  
  核心特征：
  - 云端沙箱隔离执行（不在你本地跑）
  - 异步任务模式（后台执行，完成后通知）
  - 多任务并行（同时处理多个 PR）
  - 与 ChatGPT/GitHub 深度集成
  
  杀手级场景：
  - 批量处理多个 Issue
  - 长时间运行的代码生成任务
  - 不想给 Agent 本地权限时的安全选择
```

### 2.3 Cursor Agent：IDE 原生、人机协同

```
Cursor 的设计哲学：

  "我就是你的编辑器。你在我里面写代码，我在旁边帮你。"
  
  核心特征：
  - VS Code 深度 Fork，全功能 IDE
  - 可视化 Diff 审查（看到每一行改了什么）
  - 多模型灵活切换（Claude/GPT/Gemini）
  - Agent 模式 + Tab 补全模式无缝切换
  
  杀手级场景：
  - 日常功能开发（边写边审查）
  - 需要可视化 Diff 的场景
  - 习惯 VS Code 生态的开发者
```

### 2.4 三者对比：选型决策矩阵

| 维度 | Claude Code | OpenAI Codex | Cursor Agent |
|------|------------|-------------|-------------|
| 形态 | 终端 CLI | 云端 App + CLI | AI-Native IDE |
| 执行环境 | 本地终端 | 云端沙箱 | 本地 IDE |
| 自主程度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 人机协同 | 中（确认式） | 低（异步式） | 高（实时式） |
| 代码库理解 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 安全隔离 | 低（本地执行） | 高（云端沙箱） | 低（本地执行） |
| 适合谁 | 终端极客 | 任务委派者 | IDE 用户 |

> 💡 **选型建议：** 三个工具不是互斥的。最高效的工作流是——**日常功能用 Cursor**（边写边审），**复杂重构用 Claude Code**（全权委派），**批量任务用 Codex**（后台并行）。

---

## 3. Coding Agent 的核心架构

不管是 Claude Code、Codex 还是 Cursor——它们底层共享**同一套架构模式**。理解这个架构，你就理解了所有 Coding Agent 的运作方式。

### 3.1 Agentic Loop：计划→执行→验证的无限循环

每个 Coding Agent 的核心都是一个 **while(true) 循环**：

```python
# Coding Agent 的核心伪代码
def agentic_loop(task: str, context: CodebaseContext):
    plan = llm.think(f"任务: {task}, 上下文: {context}")
    
    while not task_complete:
        # Step 1: 决定下一步行动
        action = llm.decide_next_action(plan, context)
        
        # Step 2: 执行行动（调用工具）
        if action.type == "edit_file":
            result = tools.edit_file(action.path, action.changes)
        elif action.type == "run_command":
            result = tools.run_terminal(action.command)
        elif action.type == "search_code":
            result = tools.grep(action.query)
        
        # Step 3: 验证结果
        test_result = tools.run_tests()
        if test_result.failed:
            context.add(f"测试失败: {test_result.errors}")
            continue  # 回到 Step 1，自动修复
        
        # Step 4: 更新上下文，决定是否完成
        context.add(result)
        task_complete = llm.evaluate("任务是否完成？", context)
```

```
Agentic Loop 的关键特征：

  ① 自我驱动 — 不需要人类逐步指令
  ② 工具调用 — 不只是生成文本，而是执行操作
  ③ 自我修复 — 测试失败会自动重试
  ④ 收敛判断 — 知道什么时候该停下来
```

### 3.2 工具系统：文件编辑、终端命令、Web 搜索

Coding Agent 的"手"——它通过工具与真实世界交互：

| 工具类别 | 具体工具 | 作用 |
|---------|---------|------|
| 文件操作 | read_file, write_file, list_dir | 读写代码文件 |
| 终端命令 | bash, shell | 运行测试、安装依赖、git 操作 |
| 代码搜索 | grep, find, semantic_search | 在代码库中定位相关代码 |
| Web 搜索 | search, fetch_url | 查文档、查 API、查 Stack Overflow |
| 浏览器 | browser, screenshot | 查看 UI 效果、调试前端 |
| MCP 工具 | 自定义 MCP Server | 连接数据库、内部 API 等 |

### 3.3 上下文窗口管理：看多少决定做多好

Agent 的"大脑"有容量限制——上下文窗口（128K-200K tokens）。管理它的策略：

```
上下文管理策略：

  ┌────────────────────────────────────────┐
  │           上下文窗口（200K tokens）      │
  │                                        │
  │  [系统提示] ← 固定，不压缩              │
  │  [CLAUDE.md] ← 项目级持久规则           │
  │  [当前任务] ← 用户的需求描述             │
  │  [相关代码] ← Agent 主动搜索的文件       │
  │  [执行历史] ← 之前的操作和结果           │
  │  [工具结果] ← 最近的测试/命令输出        │
  │                                        │
  │  当窗口快满时：                          │
  │  → 压缩早期执行历史                     │
  │  → 只保留关键结论，丢弃中间过程          │
  │  → 这就是为什么长会话 Agent 会"变笨"     │
  └────────────────────────────────────────┘
```

### 3.4 安全边界：Hooks 与权限控制

Agent 能操作你的文件系统和终端——**安全边界至关重要**：

```
安全边界的三层防线：

  Layer 1: 权限模式
    - 询问模式（默认）: 每个操作都要人类确认
    - 自动模式: Agent 自主执行，但有黑名单
    - YOLO 模式: 全自动，仅限可信环境
    
  Layer 2: Hooks（确定性拦截）
    - PreToolUse: 在工具执行前拦截检查
      → 阻止删除 .env 文件
      → 阻止执行 rm -rf 命令
    - PostToolUse: 在工具执行后审查结果
      → 检查生成代码是否包含密钥
    
  Layer 3: 文件系统限制
    - .claudeignore: 禁止 Agent 读取的文件
    - 工作目录限制: Agent 只能在项目目录内操作
```

> 💡 **核心理解：** Coding Agent = Agentic Loop + 工具系统 + 上下文管理 + 安全边界。四个模块缺一不可。模型只是 Loop 里的决策引擎，真正决定 Agent 质量的是**周围的工程化设计**。

---

## 4. 上下文工程：Agentic Coding 的核心竞争力

2025 年之前，大家拼的是 Prompt Engineering——"怎么写提示词"。2025 年之后，核心技能变成了 **Context Engineering**——"怎么设计 Agent 看到的整个信息环境"。

### 4.1 从 Prompt Engineering 到 Context Engineering

```
Prompt Engineering vs Context Engineering：

  Prompt Engineering（旧）：
    "你是一个 Python 专家，请帮我重构这个函数..."
    → 一次性提示，Agent 只知道你这句话告诉它的内容
    
  Context Engineering（新）：
    项目规则（CLAUDE.md）+ 代码库索引 + Git 历史
    + 依赖信息 + 架构文档 + 团队规范 + 当前任务
    → Agent 拥有一个资深工程师级别的项目理解
```

| 维度 | Prompt Engineering | Context Engineering |
|------|-------------------|-------------------|
| 对象 | 单次对话 | 整个信息生态 |
| 持久性 | 每次重写 | 持久化、可复用 |
| 复杂度 | 一段文本 | 多层配置 + 代码索引 |
| 效果上限 | 取决于你描述得多好 | 取决于 Agent 能看到多少 |

### 4.2 CLAUDE.md / AGENTS.md 的设计规范

CLAUDE.md 是你的 Agent 的"项目大脑"——它持久化存储在项目根目录，每次 Agent 启动都会读取：

```markdown
# CLAUDE.md 模板

## 项目概览
- 这是一个 FastAPI + React 的全栈项目
- 后端在 /server，前端在 /client
- 数据库使用 PostgreSQL + pgvector

## 技术栈
- Python 3.12, FastAPI 0.115, SQLAlchemy 2.0
- React 19, TypeScript 5.5, Vite 6
- Docker Compose 用于本地开发

## 代码规范
- 后端遵循 PEP 8，使用 ruff 格式化
- 前端使用 ESLint + Prettier
- 所有函数必须有类型注解
- 组件文件不超过 200 行

## 硬性约束（绝对不要违反）
- 绝不直接提交到 main 分支
- 绝不删除已有的测试用例
- 绝不在代码中硬编码 API Key
- 修改数据库 schema 前必须先备份

## 测试规范
- 后端修改后运行: pytest tests/ -v
- 前端修改后运行: npm run test
- 提交前运行: npm run lint && ruff check

## 常见错误提醒
- pgvector 的 HNSW 索引在事务内创建会锁表
- React 19 的 useEffect 在 Strict Mode 下会执行两次
```

### 4.3 上下文的三层架构：全局→项目→会话

```
上下文三层架构：

  ┌────────────────────────────────────────────┐
  │  Layer 1: 全局上下文                        │
  │  位置: ~/.claude/CLAUDE.md                  │
  │  内容: 你的个人偏好、通用规则                 │
  │  例: "永远用中文回复" "偏好函数式编程"        │
  └──────────────────┬───────────────────────────┘
                     │ 继承
  ┌──────────────────▼───────────────────────────┐
  │  Layer 2: 项目上下文                          │
  │  位置: 项目根目录/CLAUDE.md                   │
  │  内容: 技术栈、架构规范、硬性约束              │
  │  例: 上面的完整模板                           │
  │                                              │
  │  子目录也可以有自己的 CLAUDE.md：              │
  │  /server/CLAUDE.md → "后端特有规则"           │
  │  /client/CLAUDE.md → "前端特有规则"           │
  └──────────────────┬───────────────────────────┘
                     │ 继承
  ┌──────────────────▼───────────────────────────┐
  │  Layer 3: 会话上下文                          │
  │  位置: 当前对话                               │
  │  内容: 具体的任务描述和中间结果                 │
  │  例: "修复登录页面的验证 Bug"                  │
  │  生命周期: 会话结束即消失                      │
  └──────────────────────────────────────────────┘
```

### 4.4 上下文污染与塌缩：为什么 Agent 会"越做越差"

长时间使用 Agent 后，你会发现它"变笨了"。原因有两个：

**上下文污染（Context Poisoning）：**
```
错误信息混入上下文 → Agent 基于错误信息做决策 → 产生更多错误

  例: 你让 Agent 试了方案 A（失败），然后试方案 B（成功）。
  但方案 A 的错误信息还在上下文里，Agent 可能会
  把方案 A 的思路混入后续代码。

  解决: 切换到新方案时，用 /clear 清理上下文
```

**上下文塌缩（Context Collapse）：**
```
上下文窗口满了 → 早期重要信息被压缩/丢弃 → Agent 失忆

  例: 你在对话开头说了"这个项目用的是 SQLAlchemy 2.0"
  但对话 50 轮后，这个信息被压缩掉了，
  Agent 开始生成 SQLAlchemy 1.x 的代码。

  解决: 把关键信息放在 CLAUDE.md 里（它永远不会被压缩）
```

> 💡 **黄金法则：** 会变的信息放对话里，不变的信息放 CLAUDE.md。对话是短期记忆，CLAUDE.md 是长期记忆。

---

## 5. Harness Engineering：给 Coding Agent 上约束

> 更深入的 Harness Engineering 内容，参见 [Harness Engineering 完全指南](Harness Engineering 完全指南)。本章聚焦 Harness 在 Agentic Coding 场景下的具体应用。

### 5.1 为什么需要 Harness：模型是商品，约束是护城河

```
一个关键认知转变：

  旧思路: "我要找最强的 AI 模型"
    → Claude 4 比 Claude 3.5 更聪明？换模型！
    → 效果不好？等下一代模型！
    
  新思路: "我要设计最好的约束系统"
    → 同样的模型，加上好的 Harness，效果天壤之别
    → 约束系统是你自己的，模型是别人的
    → 模型会被替代，约束不会
    
  这就是 Harness Engineering 的核心：
  模型是引擎，Harness 是方向盘 + 刹车 + 安全带。
  引擎再强，没有方向盘也只会原地打转。
```

### 5.2 约束设计四要素：预算/权限/审查/回滚

| 要素 | 约束什么 | 具体做法 |
|------|---------|---------|
| **预算** | Token 消耗和时间 | 设置单次任务最大 Token 数、超时自动中断 |
| **权限** | 文件和命令 | .claudeignore 禁止读敏感文件、命令黑名单 |
| **审查** | 代码质量 | 修改后自动运行 linter + 测试 |
| **回滚** | 错误恢复 | 每步操作前 git stash、失败后自动回滚 |

```
权限约束示例（.claudeignore）：

  # 禁止 Agent 读取
  .env
  .env.*
  secrets/
  credentials/
  
  # 禁止 Agent 修改
  # （通过 Hooks 的 PreToolUse 实现）
  package-lock.json  → "不要修改锁文件"
  migrations/        → "不要修改已执行的迁移"
  vendor/            → "不要修改第三方代码"
```

### 5.3 反馈循环：强制 Agent 自我验证

```
反馈循环设计：

  Agent 修改代码
    ↓
  自动运行 ruff check（格式检查）
    ↓ 失败？→ Agent 自动修复格式
  自动运行 pytest（单元测试）
    ↓ 失败？→ Agent 分析错误并修复
  自动运行 mypy（类型检查）
    ↓ 失败？→ Agent 修复类型注解
    ↓
  全部通过 → 标记任务完成
```

在 CLAUDE.md 中强制反馈循环：
```markdown
## 工作流规则
- 每次修改 Python 文件后，必须运行 pytest
- 每次修改 TypeScript 文件后，必须运行 tsc --noEmit
- 如果测试失败，修复后必须再次运行确认通过
- 不要跳过测试直接提交
```

### 5.4 失败策略：不要重新 Prompt，要更新规则

```
面对 Agent 反复犯的错误：

  ❌ 错误做法：
     "你又用了 SQLAlchemy 1.x 的语法！用 2.0 的！"
     → 下次 Agent 可能还会犯
     
  ✅ 正确做法：
     在 CLAUDE.md 中加一条规则：
     "SQLAlchemy 必须使用 2.0 风格：
      - 用 select(User) 而不是 session.query(User)
      - 用 session.execute() 而不是 session.query()"
     → Agent 永远不会再犯这个错误
```

> 💡 **Harness 迭代法则：** 每当你纠正 Agent 同一个错误第二次，立刻把纠正写进 CLAUDE.md。这样你的约束系统会随时间**越来越强**——这就是为什么用同一个工具三个月的开发者，效率远超用了一周的。

---

## 6. Vibe Coding 工作流：实战方法论

"Vibe Coding"不是"随便让 AI 写代码"——它是一套**经过验证的迭代方法论**。用对了事半功倍，用错了灾难性返工。

### 6.1 Plan-Act-Verify：三步循环法

```
每个任务都遵循这个循环：

  ┌──────────┐
  │  Plan    │ ← "先出方案，不要写代码"
  │  规划     │    让 Agent 列出将要修改的文件和步骤
  └────┬─────┘    你审核方案，确认方向正确
       ↓
  ┌────┴─────┐
  │  Act     │ ← "按方案执行"
  │  执行     │    Agent 编写代码、修改文件
  └────┬─────┘
       ↓
  ┌────┴─────┐
  │  Verify  │ ← "运行测试，确认结果"
  │  验证     │    运行测试、检查 Diff、验收效果
  └────┬─────┘
       ↓
  通过 → 提交
  失败 → 回到 Plan，调整方案
```

**关键 Prompt 模板：**
```
Plan 阶段: "我要实现 X 功能。请先列出你的实现方案，
            包括要修改哪些文件、每个文件改什么。
            不要写代码，只给方案。等我确认后再开始。"

Act 阶段:  "方案 LGTM，开始实现。"

Verify 阶段: "运行 pytest 和 ruff check，确认所有测试通过。"
```

### 6.2 单任务会话原则：每次只做一件事

```
每次会话只做一件事的原因：

  ✅ 好的做法：
     会话 1: "修复登录页面的表单验证 Bug"
     会话 2: "给用户模块添加邮箱验证功能"
     会话 3: "重构数据库连接池配置"
     → 每个会话独立、聚焦、可回滚

  ❌ 差的做法：
     "修复登录 Bug，顺便加个邮箱验证，
      还有数据库连接池也改一下"
     → 上下文混乱、难以回滚、错误相互影响
```

### 6.3 增量式 Prompt：分层下达指令

```
不要一次给完所有需求：

  ❌ 一次性大 Prompt：
     "帮我实现一个完整的用户认证系统，
      包括注册、登录、密码重置、OAuth、
      JWT Token 管理、角色权限、邮箱验证..."
     → Agent 容易漏掉细节、架构混乱

  ✅ 增量式分层：
     Layer 1: "先实现基础的用户注册和登录 API"
              → 审查、通过、提交
     Layer 2: "在现有基础上添加 JWT Token 管理"
              → 审查、通过、提交
     Layer 3: "添加密码重置功能"
              → 审查、通过、提交
     Layer 4: "添加 OAuth 第三方登录"
              → 审查、通过、提交
     → 每层独立验证，问题早发现
```

### 6.4 激进式版本控制：Git 是你的安全网

```
Git 工作流 for Vibe Coding：

  # 每个任务开始前
  git checkout -b feature/xxx

  # 每个 Plan-Act-Verify 循环完成后
  git add -A && git commit -m "feat: xxx"

  # Agent 走偏了？不要试图修复
  git reset --hard HEAD~1  # 回退到上一个好的状态
  # 然后用不同的 Prompt 重新开始

  # 大任务分多个小 commit
  # 这样你可以精确回退到任何一个中间状态
```

> 💡 **Vibe Coding 的黄金法则：** 频繁提交 > 完美提交。宁可有 10 个小 commit，也不要 1 个大 commit。因为你随时可能需要回退，而 `git reset --hard` 是你最好的"Ctrl+Z"。

---

## 7. 实战场景：从简单到复杂

五个递进式场景，展示 Agentic Coding 在不同复杂度下的工作方式。

### 7.1 场景一：Bug 修复（5 分钟任务）

```
Prompt 示例：

  "用户反馈登录页面提交后出现 500 错误。
   错误日志显示 'AttributeError: NoneType has no attribute email'
   在 server/auth/login.py 第 42 行。
   请定位并修复这个 Bug，然后运行 pytest tests/auth/ 确认。"

Agent 执行流程：
  ① 读取 server/auth/login.py → 定位第 42 行
  ② 分析: user = get_user(email) 可能返回 None
  ③ 添加 None 检查: if not user: raise HTTPException(404)
  ④ 运行 pytest tests/auth/ → 发现需要补一个测试
  ⑤ 添加 test_login_nonexistent_user 测试用例
  ⑥ 再次运行 pytest → 全部通过 ✅
```

### 7.2 场景二：功能开发（30 分钟任务）

```
Prompt 示例（增量式）：

  Step 1: "给用户模块添加一个 'forgot password' API 端点。
           POST /api/auth/forgot-password
           接收 email，生成重置 token，发送邮件。
           先出方案，不要写代码。"

  Step 2: "方案 LGTM。实现它。"

  Step 3: "写 3 个测试用例覆盖：
           正常流程、无效邮箱、token 过期。
           运行 pytest 确认通过。"

Agent 执行流程：
  ① Plan: 列出要创建/修改的文件清单
  ② Act: 创建 endpoint、service、email 模板
  ③ Verify: 运行测试，修复发现的问题
  ④ 完成 → git commit
```

### 7.3 场景三：大规模重构（多文件变更）

```
Prompt 示例：

  "把整个项目的数据库访问层从 SQLAlchemy 1.x 风格
   迁移到 SQLAlchemy 2.0 风格。具体要求：
   - session.query(Model) → select(Model) + session.execute()
   - Model.query → 不再使用
   - 保持所有现有测试通过

   先扫描所有需要改的文件，列出清单。
   然后逐文件修改，每改一个文件运行一次测试。"

关键技巧：
  ① 让 Agent 先扫描再动手（避免遗漏）
  ② 逐文件修改 + 逐文件测试（避免雪崩）
  ③ 每个文件改完 commit 一次（方便回滚）
```

### 7.4 场景四：测试生成（TDD 驱动）

```
Prompt 示例：

  "server/services/payment.py 目前没有测试。
   请分析这个文件的所有公共方法，为每个方法
   编写至少 3 个测试用例（正常、边界、异常）。
   使用 pytest + 必要的 mock。
   运行测试确认全部通过。"

Agent 擅长测试生成的原因：
  - 可以系统性地覆盖每个分支
  - 能自动 mock 外部依赖
  - 测试代码模式性强，Agent 准确率高
  - 这是 Agentic Coding 的最佳入门场景
```

### 7.5 场景五：跨服务架构变更（多 Agent 协作）

```
场景描述：

  你有一个微服务架构：
  - user-service（Python/FastAPI）
  - order-service（Node/Express）
  - notification-service（Python/FastAPI）
  
  需求：给用户添加 "phone" 字段，需要：
  ① user-service: 修改 model + API + 迁移
  ② order-service: 调用 user API 时传递 phone
  ③ notification-service: 支持短信通知渠道

多 Agent 协作方式：
  Agent 1（Claude Code）: 处理 user-service 的改动
  Agent 2（Cursor）: 处理 order-service 的改动
  Agent 3（Claude Code）: 处理 notification-service 的改动
  
  人类的角色：
  - 定义接口契约（phone 字段的格式、API 的变化）
  - 审查每个 Agent 的 PR
  - 确保三个服务的改动兼容
```

> 💡 **场景选择建议：** 刚开始用 Agentic Coding？从**测试生成**（7.4）开始——风险最低、成功率最高、效果最直观。

---

## 8. 团队协作：Agentic Coding 的组织实践

个人用 Agent 很爽，但团队呢？Agent 的知识怎么共享？Code Review 流程怎么变？

### 8.1 共享配置：团队级 CLAUDE.md 管理

```
团队级配置管理：

  项目根目录/
  ├── CLAUDE.md              ← 团队共享规则（提交到 Git）
  ├── .claude/
  │   ├── settings.json      ← 项目级 Agent 设置
  │   └── hooks/             ← 共享的安全 Hooks
  ├── server/
  │   └── CLAUDE.md          ← 后端团队特有规则
  └── client/
      └── CLAUDE.md          ← 前端团队特有规则

  原则：
  ✅ CLAUDE.md 提交到 Git（团队共享）
  ❌ 个人偏好放 ~/.claude/CLAUDE.md（不提交）
```

### 8.2 Code Review 的变化：审查 AI 代码的方法论

```
审查 AI 代码的检查清单：

  □ 架构合理性
    AI 倾向于"能跑就行"，检查是否符合项目架构

  □ 过度工程化
    AI 容易生成"比需要更复杂"的代码
    → 问自己：这里真的需要一个抽象基类吗？

  □ 安全漏洞
    AI 可能忽略 SQL 注入、XSS、路径遍历
    → 重点检查用户输入的处理

  □ 边界条件
    AI 容易遗漏 None/空列表/并发等边界
    → 重点检查 if/else 分支完整性

  □ 依赖引入
    AI 可能引入不必要的新依赖
    → 检查 package.json/requirements.txt 的 diff
```

### 8.3 知识沉淀：把纠错经验变成约束规则

```
知识沉淀闭环：

  发现问题 → 纠正 Agent → 写进 CLAUDE.md → 团队共享
  
  示例流程：
  ① 你在 Code Review 中发现 Agent 用了 console.log 调试
  ② 你纠正它："用 logger.debug 而不是 console.log"
  ③ 你加到 CLAUDE.md：
     "禁止使用 console.log，统一使用 logger 模块"
  ④ 提交到 Git → 全团队的 Agent 都遵守这条规则
  
  三个月后：
  团队的 CLAUDE.md 积累了 50+ 条规则
  = 一份活的编码规范 = Agent 越来越懂你的项目
```

### 8.4 效率度量：如何量化 Agent 的贡献

| 指标 | 衡量方式 | 目标 |
|------|---------|------|
| Agent 代码占比 | git log 分析 AI commit | 观察趋势 |
| 首次通过率 | Agent PR 的 Review 通过率 | > 70% |
| 修复循环次数 | Agent 自我修复的平均轮数 | < 3 轮 |
| 任务完成时间 | 从任务下发到 PR 合并 | 持续下降 |
| 回滚率 | Agent PR 上线后回滚的比例 | < 5% |

> 💡 **团队建议：** 每两周回顾一次 CLAUDE.md，删除过时规则、合并重复规则。一个臃肿的 CLAUDE.md 反而会降低 Agent 性能——保持精练。

---

## 9. 安全与风险

Agentic Coding 带来了巨大的生产力提升，但也引入了**新的风险维度**。

### 9.1 代码质量风险：AI 生成代码的常见陷阱

| 陷阱 | 表现 | 防范 |
|------|------|------|
| **"能跑就行"代码** | 缺少错误处理、日志、文档 | CLAUDE.md 强制规范 |
| **过度抽象** | 不必要的设计模式和抽象层 | Review 时简化 |
| **幻觉依赖** | 引用不存在的 API 或参数 | 强制运行测试验证 |
| **版本过时** | 使用已弃用的库版本/语法 | CLAUDE.md 标注版本 |
| **复制粘贴** | 重复代码而非复用 | Review 检查 DRY |

### 9.2 安全漏洞：Agent 可能引入的攻击面

```
高危漏洞模式：

  ① SQL 注入
     Agent 可能生成: f"SELECT * FROM users WHERE id = {user_id}"
     而不是: session.execute(select(User).where(User.id == user_id))

  ② 路径遍历
     Agent 可能接受: file_path = request.args["path"]
     而不验证路径是否在允许范围内

  ③ 密钥泄露
     Agent 可能在代码中硬编码 API Key
     或在日志中打印敏感信息

  ④ 依赖投毒
     Agent 可能安装拼写相近的恶意包
     如 requets 而不是 requests

  防范：在 Hooks 中加入安全扫描
  PostToolUse → 自动运行 bandit/semgrep 安全检查
```

### 9.3 知识产权：训练数据的版权灰色地带

| 风险 | 说明 | 建议 |
|------|------|------|
| 代码版权 | Agent 可能生成与训练数据高度相似的代码 | 关键模块人工审查 |
| 许可证合规 | 引入依赖时可能忽略 License 兼容性 | 自动化 License 检查 |
| 商业机密 | 你的代码可能被发送到云端 | 使用本地模型或企业版 |

### 9.4 技能退化：如何避免"忘了怎么写代码"

```
保持技能的策略：

  ✅ 做法：
  - 定期做无 AI 的 Coding Challenge
  - 审查每一行 Agent 代码（理解它做了什么）
  - 手写核心算法和架构代码
  - Agent 是你的"快速实习生"，你是"Tech Lead"

  ❌ 避免：
  - 不看代码直接 Accept All
  - 完全不理解 Agent 的实现方式
  - 遇到问题只会"重新 Prompt"而不能手动修
```

> 💡 **风险管理原则：** Agent 生成的代码 = 实习生写的代码。你会让实习生的代码不经 Review 直接上线吗？同样的标准适用于 Agent。

---

## 10. 未来展望与学习路径

### 10.1 多 Agent 编排：专业化的 Agent 团队

```
2026 年的 Coding Agent 趋势：

  从"一个全能 Agent"到"一个专业 Agent 团队"：
  
  ┌──────────────────────────────────────────┐
  │  编排器 Agent（项目经理）                   │
  │  → 分解任务、分配给专业 Agent              │
  └─────┬──────────┬──────────┬──────────────┘
        ↓          ↓          ↓
  ┌─────┴────┐ ┌──┴─────┐ ┌──┴─────┐
  │代码 Agent│ │测试Agent│ │安全Agent│
  │ 写代码    │ │ 写测试   │ │ 安全审查 │
  └──────────┘ └────────┘ └────────┘
        ↓          ↓          ↓
  ┌─────┴──────────┴──────────┴──────────────┐
  │  审查 Agent（Critic）                      │
  │  → 审查所有 Agent 的产出，确保一致性        │
  └──────────────────────────────────────────┘
```

### 10.2 自我进化的 Agent：从执行者到学习者

```
Agent 的三个进化阶段：

  当前（2025）：执行者
    → 你告诉它做什么，它做什么
    
  近期（2026）：学习者
    → Agent 从过去的错误中学习
    → 自动更新 CLAUDE.md
    → 记住你的偏好和代码风格
    
  未来（2027+）：协作者
    → Agent 主动提出改进建议
    → 自动发现代码债务并修复
    → 参与架构设计讨论
```

### 10.3 开发者技能重塑：你该学什么、放弃什么

| 优先级提升的技能 | 优先级下降的技能 |
|---------------|---------------|
| 系统架构设计 | 背诵 API 语法 |
| 上下文工程（Context Engineering） | 手写样板代码 |
| 约束设计（Harness Engineering） | 记忆框架细节 |
| 代码审查能力 | 手动调试技巧 |
| 产品思维和需求分析 | 追求打字速度 |
| 安全意识 | 手写测试用例 |

### 10.4 延伸阅读与参考资料

**工具官方文档：**
- [Claude Code 文档](https://docs.anthropic.com/en/docs/claude-code)
- [OpenAI Codex](https://openai.com/codex/)
- [Cursor 文档](https://docs.cursor.com/)

**关联教程：**
- [Harness Engineering 完全指南](Harness Engineering 完全指南) — Harness 设计的完整深度教程
- [AI 编程助手原理剖析](AI 编程助手原理剖析) — Copilot/Cursor 的底层原理
- [DeepAgent 完全指南](DeepAgent 完全指南) — 深度推理 Agent 的架构设计

**推荐阅读：**
- [Context Engineering for AI Agents](https://augmentcode.com/blog/context-engineering) — Augment 团队的上下文工程总结
- [Anthropic: Building Effective Agents](https://docs.anthropic.com/en/docs/build-with-claude/agent) — Claude 官方的 Agent 设计指南
- [SWE-bench](https://www.swebench.com/) — 衡量 Coding Agent 能力的行业基准

---

> **全书完。**
>
> Agentic Coding 的本质就三句话：
> - **上下文决定质量**——CLAUDE.md 是你最重要的文件
> - **约束决定可靠性**——Harness 比模型更重要
> - **验证决定安全性**——Agent 写的每一行代码都需要通过测试
>
> 你不需要成为 AI 专家才能用好 Coding Agent。你需要的是——**成为一个优秀的工程总监**：定义清晰的目标、设计合理的约束、严格审查结果。
>
> 欢迎来到 Agentic Coding 时代。🚀
