# CLI 工具开发指南

> 从 `argparse` 的原始体验到 Typer + Rich 的现代化开发——用 Python 构建专业级命令行工具，从第一行代码到发布 PyPI。

---

## 1. 为什么要学 CLI 开发？

作为开发者，你每天都在和 CLI 打交道——`git commit`、`docker build`、`pip install`、`npm run dev`。这些工具如此自然地融入了你的工作流，以至于你可能从未想过：**它们是怎么做出来的？我能不能也造一个？**

答案是：能，而且比你想象的简单得多。

### 1.1 CLI 工具的应用场景

CLI（Command-Line Interface，命令行界面）工具无处不在。让我们先看看你已经在用的那些：

```
你每天都在用的 CLI 工具：

开发工具      git, docker, kubectl, npm, pip, uv
运维脚本      部署脚本、日志分析、定时任务
数据处理      csv 清洗、批量文件重命名、格式转换
AI 工程      模型训练脚本、数据标注工具、评测管线
效率工具      todo 管理、时间追踪、代码统计
```

**为什么 CLI 而不是 GUI 或 Web？** 这不是非此即彼的选择，而是各有适用场景：

| 维度 | CLI | GUI / Web |
|:---|:---|:---|
| **自动化** | ✅ 天然支持脚本编排和 CI/CD | ❌ 需要额外的自动化工具 |
| **可组合性** | ✅ 管道 `\|`、重定向 `>`、链式调用 | ❌ 各应用之间难以组合 |
| **资源消耗** | ✅ 几乎为零，SSH 远程可用 | ❌ 需要渲染引擎、浏览器 |
| **开发速度** | ✅ 一个 Python 文件即可起步 | ❌ 需要前端框架、UI 设计 |
| **用户门槛** | ❌ 需要记命令，学习曲线较陡 | ✅ 所见即所得，直觉操作 |
| **复杂交互** | ❌ 不适合多步表单、图表展示 | ✅ 拖拽、可视化、实时反馈 |

> 💡 **经验法则**：如果你的用户是开发者、运维人员或数据工程师，CLI 几乎总是最佳选择。如果用户是非技术人员，GUI/Web 才更合适。

**CLI 的 Unix 哲学**：一个工具只做一件事，做好它，然后通过管道与其他工具组合。这种设计让 CLI 工具天然具备可组合性：

```bash
# 统计 Python 项目中各文件的代码行数，按行数排序
find . -name "*.py" | xargs wc -l | sort -n

# 从日志中提取错误信息，去重后发送通知
cat app.log | grep "ERROR" | sort -u | mail -s "错误汇总" dev@team.com

# 你自己的 CLI 工具也可以融入这个管道！
my-tool export --format csv | python analyze.py | my-tool report
```

### 1.2 技术栈选型：argparse → Click → Typer

Python 构建 CLI 工具有三个主流方案。它们不是竞争关系，而是一条**渐进式的演进路线**：

```
演进时间线：

2003 ──── argparse（标准库）
              │  手动定义参数、子命令
              │  零依赖，但代码冗长
              ▼
2014 ──── Click（Pallets 团队）
              │  装饰器驱动，代码更优雅
              │  Flask 作者出品，生态成熟
              ▼
2020 ──── Typer（FastAPI 作者）
              │  类型注解驱动，零样板代码
              │  底层基于 Click，兼容其生态
              ▼
2024+ ─── Typer + Rich（现代标配）
              │  美观的终端输出 + 类型安全的参数解析
              └  当前最佳实践
```

让我们用**同一个功能**来对比三者的代码风格——一个接收名字和次数的问候命令：

```python
# ════════════════════════════════════════════
# argparse —— 手动声明一切
# ════════════════════════════════════════════
import argparse

parser = argparse.ArgumentParser(description="问候工具")
parser.add_argument("name", help="要问候的人")
parser.add_argument("--count", "-c", type=int, default=1, help="问候次数")
args = parser.parse_args()

for _ in range(args.count):
    print(f"Hello, {args.name}!")
```

```python
# ════════════════════════════════════════════
# Click —— 装饰器声明参数
# ════════════════════════════════════════════
import click

@click.command()
@click.argument("name")
@click.option("--count", "-c", default=1, help="问候次数")
def greet(name: str, count: int):
    """问候工具"""
    for _ in range(count):
        click.echo(f"Hello, {name}!")

greet()
```

```python
# ════════════════════════════════════════════
# Typer —— 类型注解即参数
# ════════════════════════════════════════════
import typer

def greet(name: str, count: int = typer.Option(1, "--count", "-c", help="问候次数")):
    """问候工具"""
    for _ in range(count):
        print(f"Hello, {name}!")

typer.run(greet)
```

**三者对比速查：**

| 维度 | argparse | Click | Typer |
|:---|:---|:---|:---|
| **参数声明方式** | 手动 `add_argument` | 装饰器 `@click.option` | 函数签名 + 类型注解 |
| **代码量** | 多 | 中 | 少 |
| **类型安全** | ❌ 运行时才发现 | ⚠️ 部分支持 | ✅ 编辑器实时检查 |
| **自动补全** | ❌ 需手动实现 | ⚠️ 需额外配置 | ✅ 内置支持 |
| **学习曲线** | 中（API 繁琐） | 中（装饰器概念） | 低（写函数就行） |
| **外部依赖** | 无（标准库） | click | typer + click |
| **适用场景** | 零依赖脚本 | 复杂企业级 CLI | 现代 Python 项目 |

> 💡 **本文的选择**：我们会先用 argparse 理解底层原理（第 3 章），再学 Click 掌握装饰器模式（第 4 章），最终以 **Typer + Rich** 作为主力工具完成实战项目。这条路线让你既懂原理，又会用最现代的工具。

### 1.3 本文的学习路线与最终成果

本文的章节安排遵循一条清晰的路线——**从原理到实战，从基础到发布**：

```
学习路线图：

第 1-2 章    准备阶段
  ├── 理解 CLI 的价值和技术栈
  └── 搭建现代化开发环境（uv + pyproject.toml）

第 3-5 章    核心技能
  ├── argparse → 理解底层原理
  ├── Click    → 掌握装饰器模式
  └── Typer    → 用现代方式写 CLI

第 6 章      输出美化
  └── Rich     → 表格、进度条、语法高亮

第 7 章      实战项目 ⭐
  └── 从零构建一个完整的任务管理 CLI

第 8-9 章    工程化
  ├── 测试     → CliRunner + 业务逻辑分离
  └── 发布     → PyPI + pipx + GitHub Actions

第 10 章     进阶
  └── Shell 补全、插件机制、设计原则
```

**你将获得的最终成果**：一个可以通过 `pip install` 安装、`pipx` 全局使用的完整 CLI 工具，具备：

- ✅ 多级子命令（`task add`、`task list`、`task done`）
- ✅ Rich 美化的表格和进度条输出
- ✅ TOML 配置文件支持
- ✅ 完善的错误处理和用户提示
- ✅ 自动化测试覆盖
- ✅ PyPI 可发布的标准包结构

> 💡 **前置知识**：本文假设你熟悉 Python 基础语法（函数、类、类型注解）。如果你还不熟悉装饰器，建议先阅读 [Python 装饰器与元编程](Python 装饰器与元编程) 的第 1-2 章。

**第 1 章知识回顾：**

| 概念 | 一句话总结 |
|:---|:---|
| **CLI 的价值** | 自动化、可组合、零资源消耗，开发者的首选界面 |
| **Unix 哲学** | 一个工具做一件事，通过管道组合 |
| **技术栈演进** | argparse → Click → Typer，从手动到自动 |
| **本文主线** | Typer + Rich，现代 Python CLI 的最佳实践 |

---

## 2. 环境搭建与项目初始化

在写第一行 CLI 代码之前，我们先把"地基"打好。好的项目结构和工具链选择，决定了你后面的开发体验是丝滑还是折腾。

这一章会用到 **uv**——2024 年以来 Python 社区最受欢迎的项目管理工具。如果你还在用 `pip + venv + requirements.txt` 的组合，是时候升级了。

### 2.1 用 uv 初始化项目

**uv** 是 Astral 团队（Ruff 的作者）用 Rust 开发的 Python 包管理器，速度比 pip 快 10-100 倍，而且集成了虚拟环境管理、依赖锁定、Python 版本管理等功能。

#### 安装 uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或者用 Homebrew
brew install uv

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 验证安装
uv --version
# uv 0.6.x
```

#### 创建 CLI 项目

```bash
# 创建项目（自动初始化 pyproject.toml + .venv + src 目录）
uv init my-cli-tool
cd my-cli-tool

# 查看生成的文件结构
tree .
# .
# ├── .python-version      ← Python 版本锁定
# ├── README.md
# ├── pyproject.toml        ← 项目配置（核心！）
# └── src/
#     └── my_cli_tool/
#         └── __init__.py
```

#### 添加依赖

```bash
# 添加核心依赖
uv add typer rich

# 添加开发依赖（不会被打包到发布版本中）
uv add --dev pytest ruff

# 查看已安装的依赖
uv pip list
```

**uv vs 传统方案对比：**

| 操作 | 传统方案 | uv |
|:---|:---|:---|
| 创建虚拟环境 | `python -m venv .venv` | `uv init`（自动创建） |
| 安装依赖 | `pip install typer` | `uv add typer` |
| 锁定版本 | `pip freeze > requirements.txt` | 自动生成 `uv.lock` |
| 运行脚本 | `source .venv/bin/activate && python` | `uv run python` |
| 安装速度 | 慢（秒级） | 快（毫秒级） |

> 💡 **为什么选 uv？** 它是一个工具解决了 pip、venv、pip-tools、pyenv 四个工具的问题。2026 年的新项目，uv 是事实标准。

### 2.2 pyproject.toml 全解析

`pyproject.toml` 是现代 Python 项目的**唯一配置文件**（PEP 621），取代了过去的 `setup.py`、`setup.cfg`、`requirements.txt` 三件套。对于 CLI 项目，有几个关键配置需要特别理解。

下面是一个完整的 CLI 项目配置，我们逐段拆解：

```toml
# ════════════════════════════════════════════
# pyproject.toml —— CLI 项目完整配置
# ════════════════════════════════════════════

# ── 构建系统 ──────────────────────────────────
[build-system]
requires = ["hatchling"]           # 构建后端（也可以用 setuptools）
build-backend = "hatchling.build"  # 告诉 pip/uv 用什么来打包

# ── 项目元信息 ────────────────────────────────
[project]
name = "my-cli-tool"               # 包名（PyPI 上的名字）
version = "0.1.0"                  # 语义化版本号
description = "一个实用的任务管理 CLI 工具"
readme = "README.md"
requires-python = ">=3.10"         # 最低 Python 版本
license = { text = "MIT" }
authors = [
    { name = "Your Name", email = "you@example.com" },
]

# 运行时依赖（用户安装你的包时会自动安装这些）
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
]

# ── CLI 入口点（最重要！）─────────────────────
[project.scripts]
my-tool = "my_cli_tool.main:app"
#  ↑          ↑              ↑
#  │          │              └── 入口函数/对象
#  │          └── Python 包路径（src/my_cli_tool/main.py）
#  └── 用户在终端输入的命令名

# ── 开发依赖 ──────────────────────────────────
[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.8.0",
]

# ── 工具配置 ──────────────────────────────────
[tool.ruff]
line-length = 100
target-version = "py310"
```

**`[project.scripts]` 是 CLI 项目的灵魂**——它告诉 Python 包管理器："当用户安装这个包时，请生成一个叫 `my-tool` 的可执行命令，它实际上会调用 `my_cli_tool.main` 模块里的 `app` 对象。"

```
安装后的效果：

$ pip install my-cli-tool
$ my-tool --help        ← 这个命令就可以用了！
$ which my-tool
/Users/you/.local/bin/my-tool   ← 自动生成的可执行文件
```

**脱糖理解**——`[project.scripts]` 的底层机制：

```python
# 当你执行 my-tool 时，Python 实际上执行的是：
import sys
from my_cli_tool.main import app

sys.exit(app())
```

> 💡 **重要区分**：`[project.scripts]` 定义的是**命令行入口点**，不要和 `[tool.xxx]` 混淆。前者是给用户用的命令，后者是给开发工具（Ruff、pytest）的配置。

### 2.3 项目目录结构：src layout 最佳实践

Python 项目有两种常见的目录结构：**flat layout**（包直接放在根目录）和 **src layout**（包放在 `src/` 目录下）。现代最佳实践推荐 **src layout**。

```
为什么 src layout 更好？

flat layout 的坑：
  my-cli-tool/
  ├── my_cli_tool/        ← 直接在根目录
  │   └── main.py
  └── tests/
      └── test_main.py    ← import my_cli_tool 时
                             可能导入的是本地目录而不是安装的包！

src layout 的安全：
  my-cli-tool/
  ├── src/
  │   └── my_cli_tool/    ← 放在 src/ 下
  │       └── main.py
  └── tests/
      └── test_main.py    ← import my_cli_tool 时
                             一定导入的是安装的包（✅ 安全）
```

下面是一个**完整的 CLI 项目目录结构**，后续章节的实战项目都会遵循这个结构：

```
my-cli-tool/
├── .python-version           ← Python 版本（3.12）
├── pyproject.toml            ← 项目配置（唯一真理）
├── uv.lock                   ← 依赖锁定文件（自动生成）
├── README.md                 ← 项目说明
├── LICENSE                   ← 开源协议
│
├── src/                      ← 源码目录
│   └── my_cli_tool/          ← Python 包
│       ├── __init__.py       ← 包初始化（可以放版本号）
│       ├── main.py           ← CLI 入口（Typer app 定义）
│       ├── commands/          ← 子命令模块
│       │   ├── __init__.py
│       │   ├── add.py        ← task add 命令
│       │   ├── list.py       ← task list 命令
│       │   └── done.py       ← task done 命令
│       ├── core/              ← 业务逻辑（与 CLI 无关）
│       │   ├── __init__.py
│       │   ├── models.py     ← 数据模型
│       │   └── storage.py    ← 持久化层
│       └── utils/             ← 工具函数
│           ├── __init__.py
│           └── console.py    ← Rich 输出封装
│
└── tests/                    ← 测试目录
    ├── __init__.py
    ├── test_commands.py      ← CLI 命令测试
    └── test_core.py          ← 业务逻辑测试
```

**关键设计原则**：

```
CLI 层（main.py + commands/）
  │  只负责：参数解析、输出格式化、错误展示
  │  不包含：业务逻辑
  ▼
业务逻辑层（core/）
  │  只负责：数据处理、存储操作、核心算法
  │  不依赖：typer、rich、任何 CLI 相关的库
  ▼
好处：
  ✅ 业务逻辑可以被 Web API、脚本、测试直接复用
  ✅ CLI 层只是业务逻辑的一个"皮肤"
  ✅ 测试可以绕过 CLI 直接测业务逻辑
```

#### 开发模式安装

项目搭建完成后，用开发模式安装，这样你修改代码后立即生效，不需要重新安装：

```bash
# 开发模式安装（推荐用 uv）
uv sync

# 或者传统方式
pip install -e .

# 验证：命令已经可以用了
my-tool --help
```

> 💡 **`-e` 是 editable 的缩写**，它创建的是一个"软链接"而不是"拷贝"。你修改 `src/` 下的代码后，再运行 `my-tool` 就能看到最新的效果，不需要重新执行 `pip install`。

**第 2 章知识回顾：**

| 概念 | 一句话总结 |
|:---|:---|
| **uv** | 用 Rust 写的 Python 包管理器，一个工具替代 pip + venv + pyenv |
| **pyproject.toml** | 现代 Python 项目的唯一配置文件，取代 setup.py |
| **`[project.scripts]`** | CLI 入口点配置，让包安装后自动生成可执行命令 |
| **src layout** | 源码放在 `src/` 下，防止本地目录污染导入 |
| **业务逻辑分离** | CLI 层只做参数解析和输出，业务逻辑放在 `core/` 中 |

---

## 3. argparse 速通：理解底层原理

为什么要学一个"过时"的工具？因为 **Click 和 Typer 底层解决的都是同一个问题**——把用户在终端输入的字符串，解析成 Python 能用的数据。理解 argparse 的工作方式，能让你在用高级框架时知其所以然。

这一章刻意保持精简——我们不追求 argparse 的每个细节，而是抓住**核心概念**，为后面的 Click 和 Typer 打基础。

### 3.1 第一个 argparse 程序

argparse 是 Python 标准库自带的命令行解析模块，零依赖，开箱即用。

```python
# greet.py —— 你的第一个 CLI 程序
import argparse

# 1. 创建解析器
parser = argparse.ArgumentParser(
    description="一个简单的问候工具"
)

# 2. 添加参数
parser.add_argument("name", help="要问候的人的名字")

# 3. 解析命令行输入
args = parser.parse_args()

# 4. 使用解析后的参数
print(f"Hello, {args.name}!")
```

运行效果：

```bash
$ python greet.py Alice
Hello, Alice!

$ python greet.py --help
usage: greet.py [-h] name

一个简单的问候工具

positional arguments:
  name        要问候的人的名字

options:
  -h, --help  show this help message and exit

$ python greet.py
usage: greet.py [-h] name
greet.py: error: the following arguments are required: name
```

**argparse 的工作流程：**

```
用户输入                    argparse 内部                    你的代码
─────────                 ──────────────                  ─────────
"Alice"          →        解析 sys.argv             →     args.name = "Alice"
"--help"         →        打印帮助文档并退出         →     （不会执行到你的代码）
（什么都不输入）   →        报错并提示用法             →     （不会执行到你的代码）
```

> 💡 **`sys.argv` 是一切的起点**。当你在终端输入 `python greet.py Alice` 时，Python 会把 `["greet.py", "Alice"]` 存入 `sys.argv`。argparse 的全部工作就是把这个字符串列表解析成有意义的数据。

### 3.2 参数类型：位置参数、可选参数、布尔标志

argparse 的参数分为三种，理解它们的区别是使用任何 CLI 框架的基础：

```python
# file_tool.py —— 三种参数类型演示
import argparse

parser = argparse.ArgumentParser(description="文件处理工具")

# ── 位置参数（Positional Argument）──────────────
# 必填，按顺序传入，不需要 -- 前缀
parser.add_argument("source", help="源文件路径")
parser.add_argument("dest", help="目标文件路径")

# ── 可选参数（Optional Argument）───────────────
# 非必填，用 -- 前缀，可以有默认值
parser.add_argument(
    "--format", "-f",           # 长名 + 短名
    type=str,                   # 参数类型（自动转换）
    default="json",             # 默认值
    choices=["json", "csv", "yaml"],  # 限制可选值
    help="输出格式（默认: json）"
)
parser.add_argument(
    "--count", "-c",
    type=int,                   # 自动把字符串转为整数
    default=1,
    help="处理次数"
)

# ── 布尔标志（Flag）──────────────────────────
# 不需要值，出现即为 True
parser.add_argument(
    "--verbose", "-v",
    action="store_true",        # 出现 → True，不出现 → False
    help="显示详细输出"
)
parser.add_argument(
    "--no-color",
    action="store_true",
    help="禁用彩色输出"
)

args = parser.parse_args()
print(f"源文件: {args.source}")
print(f"目标: {args.dest}")
print(f"格式: {args.format}")
print(f"次数: {args.count}")
print(f"详细模式: {args.verbose}")
print(f"无颜色: {args.no_color}")
```

运行示例：

```bash
# 位置参数必须按顺序提供
$ python file_tool.py input.txt output.txt
源文件: input.txt   目标: output.txt   格式: json   次数: 1

# 可选参数可以任意顺序
$ python file_tool.py input.txt output.txt -f csv --count 3 -v
源文件: input.txt   格式: csv   次数: 3   详细模式: True

# 错误的 choices 会被自动拦截
$ python file_tool.py input.txt output.txt -f xml
error: argument --format/-f: invalid choice: 'xml' (choose from 'json', 'csv', 'yaml')
```

**三种参数类型速查：**

| 类型 | 语法 | 是否必填 | 示例 |
|:---|:---|:---|:---|
| **位置参数** | `add_argument("name")` | ✅ 必填 | `tool input.txt` |
| **可选参数** | `add_argument("--name")` | ❌ 可选 | `tool --format csv` |
| **布尔标志** | `add_argument("--verbose", action="store_true")` | ❌ 可选 | `tool -v` |

> 💡 **这三种参数类型是所有 CLI 框架的通用概念**。Click 用装饰器 `@click.argument` / `@click.option` 来区分，Typer 用函数参数的有无默认值来区分。名字不同，本质相同。

### 3.3 子命令：构建多命令 CLI

真实的 CLI 工具很少只有一个命令。`git` 有 `commit`、`push`、`pull`；`docker` 有 `build`、`run`、`stop`。这种"一个主命令下有多个子命令"的模式，argparse 通过 **subparsers** 实现。

```python
# task.py —— 多子命令的任务管理工具
import argparse

# 主解析器
parser = argparse.ArgumentParser(description="任务管理工具")
subparsers = parser.add_subparsers(dest="command", help="可用命令")

# ── 子命令: add ──────────────────────────────
add_parser = subparsers.add_parser("add", help="添加新任务")
add_parser.add_argument("title", help="任务标题")
add_parser.add_argument("--priority", "-p", default="medium",
                        choices=["low", "medium", "high"],
                        help="优先级")

# ── 子命令: list ─────────────────────────────
list_parser = subparsers.add_parser("list", help="列出所有任务")
list_parser.add_argument("--status", "-s", default="all",
                         choices=["all", "todo", "done"],
                         help="按状态过滤")

# ── 子命令: done ─────────────────────────────
done_parser = subparsers.add_parser("done", help="标记任务完成")
done_parser.add_argument("task_id", type=int, help="任务 ID")

# 解析并分发
args = parser.parse_args()

if args.command == "add":
    print(f"✅ 添加任务: {args.title} (优先级: {args.priority})")
elif args.command == "list":
    print(f"📋 列出任务 (状态: {args.status})")
elif args.command == "done":
    print(f"🎉 完成任务 #{args.task_id}")
else:
    parser.print_help()  # 没输入子命令时显示帮助
```

运行效果：

```bash
$ python task.py add "写技术文章" -p high
✅ 添加任务: 写技术文章 (优先级: high)

$ python task.py list --status todo
📋 列出任务 (状态: todo)

$ python task.py done 3
🎉 完成任务 #3

$ python task.py --help
usage: task.py [-h] {add,list,done} ...

任务管理工具

positional arguments:
  {add,list,done}  可用命令
    add            添加新任务
    list           列出所有任务
    done           标记任务完成
```

注意看这段代码——为了实现 3 个子命令，我们写了将近 **30 行的参数声明代码**，还需要手动用 `if/elif` 做命令分发。这就引出了下一节的话题。

### 3.4 argparse 的痛点与局限

用 argparse 写完上面的例子后，你大概已经感受到了几个明显的**痛点**：

**痛点 1：参数声明与业务逻辑分离**

```python
# argparse 的问题：声明参数的地方和使用参数的地方完全分开
parser.add_argument("--count", type=int, default=1)  # 在这里声明
# ... 中间可能隔了几十行 ...
args = parser.parse_args()
for _ in range(args.count):                          # 在这里使用
    ...
# → 改参数名时需要改两个地方，容易遗漏
```

**痛点 2：子命令分发需要手动 if/elif**

```python
# 每加一个子命令，就要多一个 elif 分支
if args.command == "add":
    handle_add(args)
elif args.command == "list":
    handle_list(args)
elif args.command == "done":
    handle_done(args)
elif args.command == "delete":      # 新加的
    handle_delete(args)
elif args.command == "edit":        # 又新加的
    handle_edit(args)
# → 命令越多越难维护，容易忘记添加分支
```

**痛点 3：没有类型安全**

```python
# argparse 返回的是 Namespace 对象，IDE 不知道里面有什么属性
args = parser.parse_args()
args.naem  # ← 拼写错误，IDE 不会报错，运行时才 AttributeError
```

**痛点 4：测试困难**

```python
# argparse 直接读取 sys.argv，测试时需要 mock
# 没有内置的测试工具
```

**argparse vs 我们需要的：**

| 需求 | argparse | 理想状态 |
|:---|:---|:---|
| 参数声明在函数签名上 | ❌ 分离的 | ✅ 声明即使用 |
| 自动命令分发 | ❌ 手动 if/elif | ✅ 函数即命令 |
| IDE 类型提示 | ❌ Namespace 无类型 | ✅ 类型注解 |
| 测试工具 | ❌ 无 | ✅ 内置 CliRunner |
| 输出美化 | ❌ 纯 print | ✅ Rich 集成 |

> 💡 **argparse 并不是"不好"**——对于简单的一次性脚本、或者不能引入外部依赖的场景，它仍然是正确的选择。但对于需要长期维护的 CLI 项目，我们需要更好的工具。下一章，Click 登场。

**第 3 章知识回顾：**

| 概念 | 一句话总结 |
|:---|:---|
| **sys.argv** | CLI 参数的底层来源，所有框架最终都在解析它 |
| **位置参数** | 必填，按顺序传入，如 `tool input.txt` |
| **可选参数** | 用 `--` 前缀，有默认值，如 `tool --format csv` |
| **布尔标志** | 出现即为 True，如 `tool --verbose` |
| **子命令** | 多命令模式，如 `git commit`、`docker build` |
| **argparse 的局限** | 代码冗长、声明与使用分离、无类型安全 |

---

## 4. Click 框架：装饰器驱动的 CLI

Click（Command Line Interface Creation Kit）由 Flask 作者 Armin Ronacher 创建，是 Python 生态中最成熟的 CLI 框架。它的核心理念是：**用装饰器声明参数，用函数处理逻辑**——声明和使用在同一个地方，彻底解决了 argparse 的"两地分居"问题。

> 💡 **为什么要学 Click？** 虽然本文最终推荐 Typer，但 Typer 的底层就是 Click。理解 Click 的设计，能让你在 Typer 遇到复杂场景时知道如何回退到 Click 的能力。

### 4.1 Click 核心概念：装饰器即声明

Click 的设计可以用一句话概括：**一个函数 = 一个命令，装饰器 = 参数声明**。

```python
import click

@click.command()                                    # ← 声明这是一个命令
@click.argument("name")                             # ← 位置参数
@click.option("--count", "-c", default=1, help="问候次数")  # ← 可选参数
@click.option("--shout/--no-shout", default=False)  # ← 布尔开关
def greet(name: str, count: int, shout: bool):
    """一个简单的问候工具。"""                          # ← docstring 自动变成帮助文本
    message = f"Hello, {name}!"
    if shout:
        message = message.upper()
    for _ in range(count):
        click.echo(message)                          # ← click.echo 替代 print

if __name__ == "__main__":
    greet()
```

**对比 argparse，Click 解决了什么？**

```
argparse 的写法：
  1. 创建 parser
  2. 逐个添加参数（与函数分离）
  3. 调用 parse_args()
  4. 手动从 args 对象取值

Click 的写法：
  1. 写一个函数
  2. 用装饰器声明参数（与函数绑定）
  3. 直接调用函数 ← 就这样，没了

  参数声明 ═══ 就在函数上面
  参数使用 ═══ 就是函数参数
  帮助文本 ═══ 就是 docstring
```

**`click.echo()` vs `print()`**：Click 推荐用 `click.echo()` 替代 `print()`，因为它能正确处理不同操作系统的编码问题（尤其是 Windows 的 Unicode 坑）。不过在现代 Python 3.10+ 环境中，直接用 `print()` 通常也没问题。

### 4.2 参数与选项：类型、默认值、校验

Click 区分两种输入：**Argument**（位置参数）和 **Option**（可选参数）。它们的行为差异很大：

| 特性 | `@click.argument` | `@click.option` |
|:---|:---|:---|
| 是否必填 | ✅ 默认必填 | ❌ 默认可选 |
| 前缀 | 无 | `--name` 或 `-n` |
| 帮助文本 | 不显示在 `--help` 中 | ✅ 显示在 `--help` 中 |
| 适用场景 | 主要操作对象（文件路径等） | 修饰行为的选项 |

#### Click 内置类型

Click 提供了比 argparse 更丰富的参数类型：

```python
import click
from pathlib import Path

@click.command()
@click.argument("input_file", type=click.Path(exists=True))  # 文件必须存在
@click.argument("output_dir", type=click.Path(file_okay=False))  # 必须是目录
@click.option("--count", type=click.IntRange(1, 100), default=1,
              help="处理次数（1-100）")
@click.option("--level", type=click.Choice(["debug", "info", "error"]),
              default="info", help="日志级别")
@click.option("--ratio", type=click.FloatRange(0.0, 1.0), default=0.5,
              help="采样比例（0.0-1.0）")
@click.option("--password", prompt=True, hide_input=True,
              help="密码（交互式输入，不回显）")
def process(input_file, output_dir, count, level, ratio, password):
    """处理文件的 CLI 工具。"""
    click.echo(f"输入: {input_file}")
    click.echo(f"输出目录: {output_dir}")
    click.echo(f"次数: {count}, 级别: {level}, 比例: {ratio}")
```

**常用类型速查：**

| 类型 | 说明 | 示例 |
|:---|:---|:---|
| `click.STRING` | 字符串（默认） | `"hello"` |
| `click.INT` | 整数 | `42` |
| `click.FLOAT` | 浮点数 | `3.14` |
| `click.BOOL` | 布尔值 | `true/false` |
| `click.Path(exists=True)` | 路径（可校验存在性） | `/path/to/file` |
| `click.Choice(["a", "b"])` | 枚举选择 | `a` 或 `b` |
| `click.IntRange(1, 100)` | 整数范围 | `1` 到 `100` |
| `click.DateTime()` | 日期时间 | `"2025-01-01"` |

#### 从环境变量读取参数

Click 支持从环境变量自动读取参数值——这在 Docker 和 CI/CD 环境中非常实用：

```python
@click.command()
@click.option("--api-key", envvar="MY_API_KEY",     # 先读环境变量
              help="API 密钥（可通过 MY_API_KEY 环境变量设置）")
@click.option("--debug", envvar="MY_DEBUG", is_flag=True,
              help="调试模式")
def run(api_key, debug):
    """启动服务。"""
    click.echo(f"API Key: {api_key}")
    click.echo(f"Debug: {debug}")

# 使用：
# $ export MY_API_KEY=sk-xxx
# $ python app.py          ← 自动读取环境变量
# $ python app.py --api-key sk-yyy  ← 命令行参数优先级更高
```

### 4.3 命令组与子命令

还记得第 3 章 argparse 的子命令需要手动 `if/elif` 分发吗？Click 用 **`@click.group()`** 彻底解决了这个问题——**每个子命令就是一个独立的函数，注册到 group 上就行**。

```python
import click

# ── 定义命令组 ────────────────────────────────
@click.group()
@click.version_option(version="0.1.0")
def cli():
    """📋 任务管理工具 —— 管理你的日常任务。"""
    pass  # group 本身不执行逻辑，只是子命令的容器

# ── 子命令: add ──────────────────────────────
@cli.command()
@click.argument("title")
@click.option("--priority", "-p",
              type=click.Choice(["low", "medium", "high"]),
              default="medium", help="任务优先级")
def add(title: str, priority: str):
    """添加一个新任务。"""
    click.echo(f"✅ 添加任务: {title} (优先级: {priority})")

# ── 子命令: list ─────────────────────────────
@cli.command("list")  # 命令名可以和函数名不同
@click.option("--status", "-s",
              type=click.Choice(["all", "todo", "done"]),
              default="all", help="按状态过滤")
def list_tasks(status: str):
    """列出所有任务。"""
    click.echo(f"📋 列出任务 (状态: {status})")

# ── 子命令: done ─────────────────────────────
@cli.command()
@click.argument("task_id", type=int)
def done(task_id: int):
    """标记任务为已完成。"""
    click.echo(f"🎉 完成任务 #{task_id}")

if __name__ == "__main__":
    cli()
```

**对比 argparse 的子命令实现：**

```
argparse（第 3 章）：                    Click：
  parser = ArgumentParser()              @click.group()
  subparsers = parser.add_subparsers()   def cli(): pass
  add_parser = subparsers.add_parser()
  add_parser.add_argument(...)           @cli.command()
  ...                                    def add(title, priority):
  args = parser.parse_args()                 ...
  if args.command == "add":
      handle_add(args)                   ← 不需要 if/elif！
  elif args.command == "list":               Click 自动分发
      handle_list(args)
```

运行效果完全一致：

```bash
$ python task.py add "学 Click" -p high
✅ 添加任务: 学 Click (优先级: high)

$ python task.py list -s todo
📋 列出任务 (状态: todo)

$ python task.py --help
Usage: task.py [OPTIONS] COMMAND [ARGS]...

  📋 任务管理工具 —— 管理你的日常任务。

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  add   添加一个新任务。
  done  标记任务为已完成。
  list  列出所有任务。
```

> 💡 **函数名即命令名**。`@cli.command()` 装饰的函数名 `add` 自动变成子命令名。如果你想让命令名和函数名不同（比如避免和 Python 内置函数 `list` 冲突），可以用 `@cli.command("list")` 显式指定。

### 4.4 Click 上下文与参数传递

当你有多个子命令，且它们需要共享一些**全局配置**（比如 debug 模式、输出格式）时，Click 提供了 **Context（上下文）** 机制来在父命令和子命令之间传递数据。

```python
import click

@click.group()
@click.option("--debug/--no-debug", default=False, help="调试模式")
@click.option("--output", "-o", type=click.Choice(["text", "json"]),
              default="text", help="输出格式")
@click.pass_context                      # ← 把 Context 对象传给函数
def cli(ctx, debug, output):
    """任务管理工具（支持全局选项）。"""
    # ctx.ensure_object(dict) 确保 ctx.obj 是一个字典
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug             # 存入上下文
    ctx.obj["output"] = output

@cli.command()
@click.argument("title")
@click.pass_context                      # ← 子命令也可以拿到 Context
def add(ctx, title):
    """添加任务。"""
    if ctx.obj["debug"]:
        click.echo(f"[DEBUG] 输出格式: {ctx.obj['output']}")
    click.echo(f"✅ 添加: {title}")

@cli.command("list")
@click.pass_context
def list_tasks(ctx):
    """列出任务。"""
    if ctx.obj["output"] == "json":
        click.echo('{"tasks": []}')
    else:
        click.echo("📋 暂无任务")
```

```bash
# 全局选项在子命令之前传入
$ python task.py --debug add "学习 Context"
[DEBUG] 输出格式: text
✅ 添加: 学习 Context

$ python task.py --output json list
{"tasks": []}
```

**上下文的数据流向：**

```
cli(ctx)                    ← 父命令接收全局选项，存入 ctx.obj
  │
  ├── add(ctx, title)       ← 子命令通过 ctx.obj 读取全局配置
  ├── list_tasks(ctx)       ← 同上
  └── done(ctx, task_id)    ← 同上
```

> 💡 **Context 是 Click 独有的概念**，Typer 对它做了简化——用 `typer.Context` 和回调函数替代，我们在第 5 章会讲到。如果你的 CLI 不需要在父子命令间传递数据，可以完全忽略 Context。

**第 4 章知识回顾：**

| 概念 | 一句话总结 |
|:---|:---|
| **装饰器即声明** | 一个函数 = 一个命令，装饰器 = 参数声明 |
| **Argument vs Option** | Argument 是位置参数（必填），Option 是可选参数（有 `--` 前缀） |
| **内置类型** | Path、Choice、IntRange 等，比 argparse 的 `type=int` 更强大 |
| **@click.group()** | 命令组，子命令自动注册和分发，不再需要 if/elif |
| **Context** | 父子命令间共享全局配置的机制 |
| **envvar** | 参数可以从环境变量读取，适合 Docker/CI 场景 |

---

## 5. Typer 框架：类型注解驱动的现代 CLI

终于到了本文的主角。**Typer** 由 FastAPI 作者 Sebastián Ramírez 创建，设计哲学与 FastAPI 一脉相承：**用 Python 类型注解来声明一切**。如果你用过 FastAPI，Typer 会让你感到无比亲切——写一个普通的 Python 函数，加上类型注解，它就自动变成一个完整的 CLI 命令。

### 5.1 Typer 的设计理念：类型注解即一切

**Typer 和 Click 的关系**：Typer 不是 Click 的替代品，而是 Click 的**高级封装**。每一个 Typer 应用最终都会被翻译成 Click 命令。

```
Typer 的架构：

你写的代码（类型注解）
      │
      ▼
Typer（翻译层）
      │  把类型注解翻译成 Click 装饰器
      ▼
Click（执行层）
      │  实际的参数解析和命令执行
      ▼
终端输出
```

**核心理念对比：**

```python
# ════════════════════════════════════════════
# Click：装饰器声明参数
# ════════════════════════════════════════════
@click.command()
@click.argument("name")
@click.option("--age", type=int, default=0, help="年龄")
@click.option("--active/--no-active", default=True)
def greet(name: str, age: int, active: bool):
    ...

# ════════════════════════════════════════════
# Typer：类型注解声明参数（同样的功能！）
# ════════════════════════════════════════════
def greet(name: str, age: int = 0, active: bool = True):
    ...
```

看到区别了吗？Typer 把 Click 需要的**4 行装饰器**压缩成了**函数签名本身**：

| 信息 | Click 的写法 | Typer 的写法 |
|:---|:---|:---|
| 这是一个命令 | `@click.command()` | 自动识别 |
| `name` 是位置参数 | `@click.argument("name")` | 无默认值 → 自动推断为 Argument |
| `age` 是可选参数 | `@click.option("--age", type=int)` | 有默认值 → 自动推断为 Option |
| `active` 是布尔开关 | `@click.option("--active/--no-active")` | 类型是 `bool` → 自动生成开关 |

> 💡 **Typer 的推断规则极其简单**：有默认值 → Option（可选参数），无默认值 → Argument（位置参数）。类型注解决定参数类型。就这两条规则，覆盖 90% 的场景。

### 5.2 从函数签名到命令行接口

Typer 有两种使用方式：**简单模式**（单命令）和 **App 模式**（多命令）。

#### 简单模式：`typer.run()`

最快的起步方式——一个函数就是一个完整的 CLI：

```python
# hello.py
import typer

def main(
    name: str,
    count: int = typer.Option(1, "--count", "-c", help="问候次数"),
    uppercase: bool = typer.Option(False, "--upper", "-u", help="大写输出"),
):
    """一个友好的问候工具。"""
    message = f"Hello, {name}!"
    if uppercase:
        message = message.upper()
    for _ in range(count):
        print(message)

if __name__ == "__main__":
    typer.run(main)
```

```bash
$ python hello.py Alice
Hello, Alice!

$ python hello.py Alice -c 3 -u
HELLO, ALICE!
HELLO, ALICE!
HELLO, ALICE!

$ python hello.py --help
Usage: hello.py [OPTIONS] NAME

  一个友好的问候工具。

Arguments:
  NAME  [required]

Options:
  -c, --count INTEGER  问候次数  [default: 1]
  -u, --upper          大写输出  [default: False]
  --help               Show this message and exit.
```

#### App 模式：`typer.Typer()`

当你需要多个子命令时，用 App 模式：

```python
# main.py
import typer

app = typer.Typer(help="📋 任务管理工具")

@app.command()
def add(
    title: str,
    priority: str = typer.Option("medium", "--priority", "-p", help="优先级"),
):
    """添加一个新任务。"""
    print(f"✅ 添加: {title} (优先级: {priority})")

@app.command()
def done(task_id: int):
    """标记任务完成。"""
    print(f"🎉 完成任务 #{task_id}")

if __name__ == "__main__":
    app()
```

#### 使用 `Annotated` 语法（推荐）

Python 3.9+ 引入的 `Annotated` 类型是 Typer 的推荐写法——把参数元数据写在类型注解里，函数签名更干净：

```python
from typing import Annotated
import typer

app = typer.Typer()

@app.command()
def add(
    title: str,
    priority: Annotated[str, typer.Option("--priority", "-p",
                                          help="优先级")] = "medium",
    urgent: Annotated[bool, typer.Option("--urgent",
                                         help="标记为紧急")] = False,
):
    """添加任务。"""
    flag = "🔴" if urgent else "🟢"
    print(f"{flag} 添加: {title} (优先级: {priority})")
```

**两种写法等价，选择 `Annotated` 的好处是**：默认值和参数元数据分离，代码更清晰，IDE 提示更好。

### 5.3 参数校验与枚举类型

Typer 的杀手锏之一是**用 Python 原生类型来做参数校验**。你不需要记忆 Click 的 `click.Choice`、`click.IntRange` 等 API——直接用 Python 的 `Enum`、`Path` 就行。

#### 用 Enum 限制可选值

```python
from enum import Enum
from typing import Annotated
import typer

class Priority(str, Enum):
    """任务优先级（继承 str 让 Typer 正确处理）"""
    low = "low"
    medium = "medium"
    high = "high"

class OutputFormat(str, Enum):
    text = "text"
    json = "json"
    csv = "csv"

app = typer.Typer()

@app.command()
def add(
    title: str,
    priority: Annotated[Priority, typer.Option(
        "--priority", "-p", help="任务优先级"
    )] = Priority.medium,
    output: Annotated[OutputFormat, typer.Option(
        "--output", "-o", help="输出格式"
    )] = OutputFormat.text,
):
    """添加任务（使用 Enum 校验参数）。"""
    print(f"✅ {title} | 优先级: {priority.value} | 格式: {output.value}")
```

```bash
$ python task.py add "写文章" -p high -o json
✅ 写文章 | 优先级: high | 格式: json

$ python task.py add "写文章" -p urgent
Error: Invalid value for '-p': 'urgent' is not one of 'low', 'medium', 'high'.
```

**Enum 的优势**：相比 Click 的 `choices=["low", "medium", "high"]` 字符串列表，Enum 是有类型的——IDE 能自动补全枚举值，拼写错误在编辑器中就能被发现。

#### 用 Path 校验文件路径

```python
from pathlib import Path
from typing import Annotated
import typer

@typer.command()
def convert(
    input_file: Annotated[Path, typer.Argument(
        exists=True,            # 文件必须存在
        readable=True,          # 文件必须可读
        help="输入文件"
    )],
    output_dir: Annotated[Path, typer.Option(
        "--output", "-o",
        file_okay=False,        # 必须是目录
        resolve_path=True,      # 解析为绝对路径
        help="输出目录"
    )] = Path("./output"),
):
    """文件格式转换工具。"""
    print(f"输入: {input_file}")
    print(f"输出: {output_dir}")
    # input_file 和 output_dir 已经是 Path 对象，可以直接用
    print(f"文件大小: {input_file.stat().st_size} bytes")
```

> 💡 **Typer 自动把路径字符串转为 `Path` 对象**，你在函数内部直接用 `pathlib` 的 API（如 `.stat()`、`.read_text()`），不需要手动转换。

### 5.4 命令组与多级子命令

Typer 的命令组和 Click 类似——每个 `@app.command()` 自动注册为子命令。但 Typer 还支持**多级嵌套**，通过 `app.add_typer()` 实现。

```python
# main.py —— 多级子命令演示
import typer

# ── 主 app ────────────────────────────────────
app = typer.Typer(help="📋 项目管理工具")

# ── 一级子命令组: task ────────────────────────
task_app = typer.Typer(help="任务管理")
app.add_typer(task_app, name="task")

@task_app.command("add")
def task_add(title: str):
    """添加任务。"""
    print(f"✅ 添加任务: {title}")

@task_app.command("list")
def task_list():
    """列出任务。"""
    print("📋 任务列表...")

# ── 一级子命令组: config ──────────────────────
config_app = typer.Typer(help="配置管理")
app.add_typer(config_app, name="config")

@config_app.command("show")
def config_show():
    """显示当前配置。"""
    print("⚙️ 当前配置...")

@config_app.command("set")
def config_set(key: str, value: str):
    """设置配置项。"""
    print(f"⚙️ 设置 {key} = {value}")

if __name__ == "__main__":
    app()
```

```bash
# 多级子命令的使用方式
$ python main.py task add "写文章"
✅ 添加任务: 写文章

$ python main.py config set theme dark
⚙️ 设置 theme = dark

$ python main.py --help
Usage: main.py [OPTIONS] COMMAND [ARGS]...

  📋 项目管理工具

Commands:
  config  配置管理
  task    任务管理

$ python main.py task --help
Usage: main.py task [OPTIONS] COMMAND [ARGS]...

  任务管理

Commands:
  add   添加任务。
  list  列出任务。
```

**命令层级结构：**

```
app（主命令）
  ├── task（子命令组）
  │   ├── add     → task_add()
  │   └── list    → task_list()
  └── config（子命令组）
      ├── show    → config_show()
      └── set     → config_set()
```

> 💡 **实际项目中的组织方式**：每个子命令组放在独立的文件中（如 `commands/task.py`、`commands/config.py`），在 `main.py` 中通过 `app.add_typer()` 组装。这和第 2 章的项目结构设计完全对应。

### 5.5 回调函数与全局选项

还记得第 4 章 Click 用 `@click.pass_context` 传递全局配置吗？Typer 用**回调函数 (callback)** 提供了更简洁的方案。

```python
from typing import Annotated, Optional
import typer

app = typer.Typer()

# ── 全局选项通过回调函数处理 ─────────────────
@app.callback()
def main(
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="详细输出"
    )] = False,
    config: Annotated[Optional[str], typer.Option(
        "--config", "-c", help="配置文件路径"
    )] = None,
):
    """📋 任务管理工具 —— 一个现代化的 CLI 任务管理器。"""
    # 回调函数在任何子命令之前执行
    if verbose:
        print("[VERBOSE] 详细模式已开启")
    if config:
        print(f"[CONFIG] 使用配置文件: {config}")

@app.command()
def add(title: str):
    """添加任务。"""
    print(f"✅ 添加: {title}")

@app.command()
def list():
    """列出任务。"""
    print("📋 任务列表...")
```

```bash
# 全局选项在子命令之前
$ python task.py -v add "写文章"
[VERBOSE] 详细模式已开启
✅ 添加: 写文章

$ python task.py --config ./my.toml list
[CONFIG] 使用配置文件: ./my.toml
📋 任务列表...

# --help 会显示全局选项
$ python task.py --help
Usage: task.py [OPTIONS] COMMAND [ARGS]...

  📋 任务管理工具 —— 一个现代化的 CLI 任务管理器。

Options:
  -v, --verbose        详细输出
  -c, --config TEXT    配置文件路径
  --help               Show this message and exit.

Commands:
  add   添加任务。
  list  列出任务。
```

**回调函数的执行顺序：**

```
用户输入: my-tool -v add "写文章"
                  │         │
                  ▼         ▼
            main(verbose=True)    ← @app.callback() 先执行
                  │
                  ▼
            add(title="写文章")   ← @app.command() 后执行
```

> 💡 **`@app.callback()` 还有一个作用**：它的 docstring 会成为整个 CLI 工具的帮助文本。如果你不需要全局选项，只想设置帮助文本，可以直接在 `typer.Typer(help="...")` 中传入。

**第 5 章知识回顾：**

| 概念 | 一句话总结 |
|:---|:---|
| **Typer 核心规则** | 无默认值 → Argument，有默认值 → Option，类型注解 → 自动转换 |
| **typer.run()** | 单命令快速模式，一个函数即一个 CLI |
| **typer.Typer()** | App 模式，支持多子命令 |
| **Annotated 语法** | 推荐写法，把参数元数据和默认值分离 |
| **Enum 校验** | 用 Python 枚举替代字符串列表，IDE 可补全 |
| **add_typer()** | 多级命令组嵌套，适合大型 CLI 项目 |
| **@app.callback()** | 全局选项处理，替代 Click 的 Context 传参 |

---

## 6. Rich 美化输出：让终端焕然一新

到目前为止，我们的 CLI 输出还是朴素的 `print()`。是时候给终端加点"特效"了。

**Rich** 是 Python 生态中最受欢迎的终端美化库，能让你的 CLI 输出从"黑白命令行"变成"彩色仪表盘"。表格、进度条、语法高亮、面板、树形结构——Rich 几乎把 Web UI 的视觉效果搬到了终端里。

### 6.1 Console 对象与样式文本

`Console` 是 Rich 的核心对象，用它替代 `print()` 来输出内容：

```python
from rich.console import Console

console = Console()

# ── 基础样式 ──────────────────────────────────
console.print("普通文本")
console.print("[bold]粗体文本[/bold]")
console.print("[italic red]红色斜体[/italic red]")
console.print("[bold green]✅ 操作成功[/bold green]")
console.print("[bold red]❌ 操作失败[/bold red]")
console.print("[yellow]⚠️ 警告信息[/yellow]")

# ── 组合样式 ──────────────────────────────────
console.print("[bold blue on white] 蓝色粗体白底 [/bold blue on white]")
console.print("[link=https://typer.tiangolo.com]点击访问 Typer 文档[/link]")

# ── 使用 emoji ────────────────────────────────
console.print(":rocket: 部署成功！")       # 🚀 部署成功！
console.print(":warning: 请注意！")        # ⚠️ 请注意！
```

**Rich 的标记语法类似 HTML**，用 `[样式]文本[/样式]` 的格式。常用样式：

| 标记 | 效果 | 示例 |
|:---|:---|:---|
| `[bold]` | 粗体 | `[bold]重要[/bold]` |
| `[italic]` | 斜体 | `[italic]强调[/italic]` |
| `[red]` / `[green]` / `[blue]` | 颜色 | `[red]错误[/red]` |
| `[dim]` | 暗淡 | `[dim]次要信息[/dim]` |
| `[strike]` | 删除线 | `[strike]已完成[/strike]` |
| `[underline]` | 下划线 | `[underline]链接[/underline]` |
| `[on red]` | 背景色 | `[on red]高亮[/on red]` |

#### 封装项目专用的 Console

在实际项目中，建议封装一个统一的输出工具：

```python
# utils/console.py
from rich.console import Console

console = Console()

def success(message: str):
    """输出成功信息。"""
    console.print(f"[bold green]✅ {message}[/bold green]")

def error(message: str):
    """输出错误信息。"""
    console.print(f"[bold red]❌ {message}[/bold red]")

def warning(message: str):
    """输出警告信息。"""
    console.print(f"[yellow]⚠️  {message}[/yellow]")

def info(message: str):
    """输出提示信息。"""
    console.print(f"[dim]ℹ️  {message}[/dim]")
```

```python
# 在命令中使用
from utils.console import success, error

def add(title: str):
    try:
        # ... 业务逻辑 ...
        success(f"任务已添加: {title}")
    except Exception as e:
        error(f"添加失败: {e}")
```

> 💡 **全局只创建一个 `Console` 实例**。多次创建会导致样式不一致，且无法正确处理终端宽度计算。

### 6.2 表格、面板与树形展示

CLI 工具经常需要展示结构化数据。Rich 提供了三个核心组件：**Table（表格）**、**Panel（面板）** 和 **Tree（树形结构）**。

#### Table：展示列表数据

```python
from rich.console import Console
from rich.table import Table

console = Console()

def show_tasks():
    """展示任务列表（Rich 表格）。"""
    table = Table(title="📋 任务列表", show_lines=True)

    # 定义列（可以设置样式和对齐方式）
    table.add_column("ID", style="dim", width=4, justify="right")
    table.add_column("任务", style="bold")
    table.add_column("优先级", justify="center")
    table.add_column("状态", justify="center")

    # 添加行（优先级用不同颜色）
    table.add_row("1", "完成 CLI 教程", "[red]high[/red]", "🔴 进行中")
    table.add_row("2", "写单元测试", "[yellow]medium[/yellow]", "⭕ 待办")
    table.add_row("3", "更新 README", "[green]low[/green]", "✅ 已完成")
    table.add_row("4", "发布到 PyPI", "[red]high[/red]", "⭕ 待办")

    console.print(table)

show_tasks()
```

#### Panel：突出显示重要信息

```python
from rich.panel import Panel

# 简单面板
console.print(Panel("任务已成功添加！", title="✅ 成功", border_style="green"))

# 带副标题的面板
console.print(Panel(
    "[bold]my-cli-tool[/bold] v0.1.0\n"
    "一个现代化的任务管理 CLI 工具\n\n"
    "使用 [cyan]my-tool --help[/cyan] 查看帮助",
    title="关于",
    subtitle="MIT License",
    border_style="blue",
))
```

#### Tree：展示层级结构

```python
from rich.tree import Tree

tree = Tree("📁 my-cli-tool")
src = tree.add("📁 src")
pkg = src.add("📁 my_cli_tool")
pkg.add("📄 main.py")
pkg.add("📄 __init__.py")
commands = pkg.add("📁 commands")
commands.add("📄 add.py")
commands.add("📄 list.py")
core = pkg.add("📁 core")
core.add("📄 models.py")
core.add("📄 storage.py")
tests = tree.add("📁 tests")
tests.add("📄 test_commands.py")
tree.add("📄 pyproject.toml")

console.print(tree)
```

> 💡 **Table 是 CLI 工具中使用频率最高的 Rich 组件**。当你需要展示任务列表、配置信息、依赖关系时，一个漂亮的表格远比 `print()` 的纯文本输出更清晰。

### 6.3 进度条与 Spinner

CLI 工具经常需要执行耗时操作（下载、处理大文件、API 调用）。没有进度反馈的话，用户会以为程序卡死了。Rich 提供了两种方案：**Progress（进度条）** 和 **Status（Spinner 旋转器）**。

#### Progress：已知总量的任务

```python
import time
from rich.progress import Progress

with Progress() as progress:
    # 创建多个并行任务（每个有独立的进度条）
    download = progress.add_task("[cyan]下载文件...", total=100)
    process = progress.add_task("[green]处理数据...", total=200)

    while not progress.finished:
        progress.update(download, advance=2)
        progress.update(process, advance=1)
        time.sleep(0.02)
```

#### Status：未知时长的任务

```python
from rich.console import Console

console = Console()

with console.status("[bold green]正在连接服务器...") as status:
    time.sleep(1)
    status.update("[bold green]正在获取数据...")
    time.sleep(1)
    status.update("[bold green]正在解析结果...")
    time.sleep(1)

console.print("[bold green]✅ 完成！")
```

#### 在 CLI 命令中使用

```python
import typer
from rich.progress import track

app = typer.Typer()

@app.command()
def process(
    input_file: str,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """处理文件（带进度条）。"""
    items = range(100)  # 模拟 100 个待处理项

    # track() 是最简洁的进度条用法
    for item in track(items, description="处理中..."):
        time.sleep(0.02)  # 模拟处理

    success("处理完成！")
```

> 💡 **`track()` 是最推荐的进度条用法**——只需要把 `for item in items` 改成 `for item in track(items)`，一行代码加上进度条。

### 6.4 语法高亮与 Markdown 渲染

Rich 可以在终端中渲染**代码高亮**和 **Markdown 文档**——非常适合用于 CLI 工具的帮助信息和调试输出。

#### 语法高亮

```python
from rich.console import Console
from rich.syntax import Syntax

console = Console()

code = '''
def fibonacci(n: int) -> int:
    """计算第 n 个斐波那契数。"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(10))  # 55
'''

# 渲染带语法高亮的代码
syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
console.print(syntax)
```

#### Markdown 渲染

```python
from rich.markdown import Markdown

doc = """
# 任务管理工具

## 快速开始

1. 安装: `pip install my-cli-tool`
2. 添加任务: `my-tool add "写文章"`
3. 查看列表: `my-tool list`

## 配置

| 选项 | 默认值 | 说明 |
|------|--------|------|
| theme | dark | 主题颜色 |
| format | text | 输出格式 |

> **提示**: 使用 `--help` 查看所有选项。
"""

console.print(Markdown(doc))
```

> 💡 **实用场景**：当用户执行 `my-tool help` 或 `my-tool docs` 时，直接在终端渲染 README.md 的内容，比打印纯文本体验好得多。

### 6.5 Rich + Typer 深度集成

好消息：Typer 从 0.9.0 版本开始**内置了 Rich 支持**。你只需要安装 `typer[all]`（或者同时安装 `typer` 和 `rich`），就能自动获得美化的帮助信息和错误提示。

#### 自动美化的帮助信息

```python
import typer

app = typer.Typer(rich_markup_mode="rich")  # ← 开启 Rich 标记

@app.command()
def deploy(
    env: str = typer.Option(..., help="部署环境 [bold red]（必填）[/bold red]"),
    force: bool = typer.Option(False, help="[yellow]跳过确认直接部署[/yellow]"),
    workers: int = typer.Option(4, help="工作进程数 [dim](默认: 4)[/dim]"),
):
    """🚀 [bold green]部署应用到指定环境[/bold green]

    支持的环境：
    - [cyan]dev[/cyan]: 开发环境
    - [yellow]staging[/yellow]: 预发布环境
    - [red]prod[/red]: 生产环境
    """
    print(f"部署到 {env}，workers={workers}, force={force}")
```

#### 用 Rich 美化错误输出

```python
import typer
from rich.console import Console

console = Console(stderr=True)  # 错误输出到 stderr

app = typer.Typer()

@app.command()
def process(file_path: str):
    """处理文件。"""
    try:
        with open(file_path) as f:
            data = f.read()
        # ... 处理逻辑 ...
    except FileNotFoundError:
        console.print(f"[bold red]❌ 文件不存在: {file_path}[/bold red]")
        raise typer.Exit(code=1)
    except PermissionError:
        console.print(f"[bold red]❌ 权限不足: {file_path}[/bold red]")
        raise typer.Exit(code=1)
```

**`typer.Exit` vs `sys.exit`**：在 Typer 命令中，用 `typer.Exit(code=1)` 替代 `sys.exit(1)`。前者能被 Typer 正确捕获，不会打印异常堆栈。

#### 确认提示和交互

```python
import typer

@app.command()
def delete(task_id: int):
    """删除任务。"""
    # Typer 内置的确认提示
    confirmed = typer.confirm(f"确定删除任务 #{task_id}?")
    if not confirmed:
        print("已取消")
        raise typer.Abort()
    print(f"🗑️ 已删除任务 #{task_id}")
```

```bash
$ my-tool delete 3
确定删除任务 #3? [y/N]: y
🗑️ 已删除任务 #3

$ my-tool delete 3
确定删除任务 #3? [y/N]: n
已取消
Aborted.
```

**第 6 章知识回顾：**

| 组件 | 用途 | 一句话用法 |
|:---|:---|:---|
| **Console** | 替代 print，支持样式标记 | `console.print("[bold red]错误[/]")` |
| **Table** | 展示列表/表格数据 | `table.add_column()` + `table.add_row()` |
| **Panel** | 突出显示重要信息 | `Panel("内容", title="标题")` |
| **Tree** | 展示层级/目录结构 | `tree.add("子节点")` |
| **Progress** | 已知总量的进度条 | `for item in track(items)` |
| **Status** | 未知时长的 Spinner | `with console.status("加载中...")` |
| **Syntax** | 代码语法高亮 | `Syntax(code, "python")` |
| **rich_markup_mode** | Typer 帮助文本美化 | `Typer(rich_markup_mode="rich")` |

---

## 7. 实战项目：构建一个完整的 CLI 工具

前 6 章学了一堆零件，现在是**组装**的时候了。这一章我们从零构建一个名为 **taskr** 的任务管理 CLI 工具，集成前面学过的所有技能：Typer 命令、Rich 输出、TOML 配置、错误处理、数据持久化。

### 7.1 需求分析与架构设计

#### 功能需求

```
taskr —— 一个终端任务管理工具

核心命令：
  taskr add "任务标题" [-p high/medium/low]    添加任务
  taskr list [-s todo/done/all] [--json]       列出任务（Rich 表格）
  taskr done <ID>                              标记完成
  taskr delete <ID>                            删除任务
  taskr stats                                  统计概览

全局选项：
  --verbose / -v                               详细输出
  --config <path>                              指定配置文件
  --version                                    显示版本号
```

#### 项目结构

```
taskr/
├── pyproject.toml
├── src/
│   └── taskr/
│       ├── __init__.py          # __version__ = "0.1.0"
│       ├── main.py              # Typer app 入口 + 全局选项
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── add.py           # add 命令
│       │   ├── list.py          # list 命令
│       │   ├── done.py          # done 命令
│       │   ├── delete.py        # delete 命令
│       │   └── stats.py         # stats 命令
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py        # Task 数据模型
│       │   ├── storage.py       # JSON 持久化层
│       │   └── config.py        # TOML 配置管理
│       └── utils/
│           ├── __init__.py
│           └── console.py       # Rich 输出封装
└── tests/
```

#### 架构分层

```
┌─────────────────────────────────────────┐
│  CLI 层（main.py + commands/）           │
│  职责：参数解析 → 调用业务逻辑 → 格式化输出 │
│  依赖：typer, rich                       │
├─────────────────────────────────────────┤
│  业务逻辑层（core/）                      │
│  职责：数据验证 → CRUD 操作 → 配置管理     │
│  依赖：纯 Python（不依赖 typer/rich）      │
├─────────────────────────────────────────┤
│  存储层（core/storage.py）               │
│  职责：JSON 文件读写                      │
│  依赖：json, pathlib                     │
└─────────────────────────────────────────┘
```

> 💡 **为什么 core 层不依赖 typer/rich？** 因为这样你的业务逻辑可以被任何"前端"复用——CLI、Web API、测试脚本都能直接调用 `core.storage.add_task()`，而不需要通过终端命令。

### 7.2 核心命令实现：增删改查

我们先搭建数据模型和 CLI 入口，再逐个实现命令。

#### 数据模型：`core/models.py`

```python
# src/taskr/core/models.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Status(str, Enum):
    todo = "todo"
    done = "done"

@dataclass
class Task:
    """任务数据模型。"""
    id: int
    title: str
    priority: Priority = Priority.medium
    status: Status = Status.todo
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data["id"],
            title=data["title"],
            priority=Priority(data["priority"]),
            status=Status(data["status"]),
            created_at=data["created_at"],
            completed_at=data.get("completed_at"),
        )
```

#### CLI 入口：`main.py`

```python
# src/taskr/main.py
from typing import Annotated, Optional
import typer
from taskr import __version__

app = typer.Typer(
    name="taskr",
    help="📋 taskr —— 一个现代化的终端任务管理工具",
    rich_markup_mode="rich",
)

@app.callback()
def main(
    version: Annotated[bool, typer.Option(
        "--version", "-V", help="显示版本号", is_eager=True
    )] = False,
):
    """taskr 全局选项。"""
    if version:
        print(f"taskr {__version__}")
        raise typer.Exit()

# 注册子命令（从 commands 模块导入）
from taskr.commands import add, list_cmd, done, delete, stats
```

#### add 命令

```python
# src/taskr/commands/add.py
from typing import Annotated
import typer
from taskr.core.models import Priority
from taskr.core.storage import TaskStorage
from taskr.utils.console import success

def register(app: typer.Typer):
    @app.command()
    def add(
        title: str,
        priority: Annotated[Priority, typer.Option(
            "--priority", "-p", help="任务优先级"
        )] = Priority.medium,
    ):
        """添加一个新任务。"""
        storage = TaskStorage()
        task = storage.add(title=title, priority=priority)
        success(f"任务已添加: #{task.id} {task.title} (优先级: {priority.value})")
```

#### list 命令

```python
# src/taskr/commands/list_cmd.py
from typing import Annotated, Optional
import json
import typer
from rich.console import Console
from rich.table import Table
from taskr.core.models import Status
from taskr.core.storage import TaskStorage

console = Console()

# 优先级颜色映射
PRIORITY_COLORS = {"high": "red", "medium": "yellow", "low": "green"}
STATUS_ICONS = {"todo": "⭕", "done": "✅"}

def register(app: typer.Typer):
    @app.command("list")
    def list_tasks(
        status: Annotated[Optional[Status], typer.Option(
            "--status", "-s", help="按状态过滤"
        )] = None,
        as_json: Annotated[bool, typer.Option(
            "--json", help="JSON 格式输出"
        )] = False,
    ):
        """列出所有任务。"""
        storage = TaskStorage()
        tasks = storage.list(status=status)

        if not tasks:
            console.print("[dim]暂无任务，使用 [cyan]taskr add[/cyan] 添加第一个任务[/dim]")
            return

        # JSON 输出（适合管道和脚本）
        if as_json:
            print(json.dumps([t.to_dict() for t in tasks], ensure_ascii=False, indent=2))
            return

        # Rich 表格输出
        table = Table(title=f"📋 任务列表 ({len(tasks)} 项)", show_lines=True)
        table.add_column("ID", style="dim", width=4, justify="right")
        table.add_column("任务", style="bold", min_width=20)
        table.add_column("优先级", justify="center", width=8)
        table.add_column("状态", justify="center", width=6)
        table.add_column("创建时间", style="dim", width=12)

        for task in tasks:
            color = PRIORITY_COLORS.get(task.priority.value, "white")
            icon = STATUS_ICONS.get(task.status.value, "❓")
            date_str = task.created_at[:10]  # 只取日期部分
            table.add_row(
                str(task.id),
                task.title,
                f"[{color}]{task.priority.value}[/{color}]",
                icon,
                date_str,
            )

        console.print(table)
```

> 💡 **`--json` 选项是 CLI 设计最佳实践**——让你的工具既能给人看（Rich 表格），又能给机器用（JSON 输出），适合在脚本和 CI/CD 管道中使用。

### 7.3 配置文件管理（TOML）

CLI 工具通常需要一些持久化的配置（数据存储路径、默认优先级、输出格式等）。Python 3.11+ 内置了 `tomllib` 模块，TOML 是当下 Python 生态的标准配置格式。

#### 配置文件结构

```toml
# ~/.config/taskr/config.toml
[general]
default_priority = "medium"    # 默认优先级
data_dir = "~/.local/share/taskr"  # 数据存储目录

[display]
date_format = "%Y-%m-%d"      # 日期显示格式
show_completed = true          # 列表是否显示已完成任务
color_theme = "default"        # 颜色主题
```

#### 配置管理模块

```python
# src/taskr/core/config.py
import tomllib
from dataclasses import dataclass
from pathlib import Path

# 默认配置目录遵循 XDG 规范
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "taskr"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.toml"

@dataclass
class TaskrConfig:
    """taskr 配置。"""
    default_priority: str = "medium"
    data_dir: Path = Path.home() / ".local" / "share" / "taskr"
    date_format: str = "%Y-%m-%d"
    show_completed: bool = True

    @classmethod
    def load(cls, config_path: Path | None = None) -> "TaskrConfig":
        """加载配置文件，不存在则使用默认值。"""
        path = config_path or DEFAULT_CONFIG_FILE

        if not path.exists():
            return cls()  # 使用全部默认值

        with open(path, "rb") as f:
            data = tomllib.load(f)

        general = data.get("general", {})
        display = data.get("display", {})

        return cls(
            default_priority=general.get("default_priority", "medium"),
            data_dir=Path(general.get("data_dir", str(cls.data_dir))).expanduser(),
            date_format=display.get("date_format", "%Y-%m-%d"),
            show_completed=display.get("show_completed", True),
        )

    def ensure_dirs(self):
        """确保数据目录存在。"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
```

#### 在命令中使用配置

```python
# 在 main.py 的 callback 中加载配置
@app.callback()
def main(
    config: Annotated[Optional[Path], typer.Option(
        "--config", "-c", help="配置文件路径"
    )] = None,
):
    """taskr 全局选项。"""
    # 加载配置并存入 Typer 上下文
    cfg = TaskrConfig.load(config)
    cfg.ensure_dirs()
    # 后续命令可以通过 TaskrConfig.load() 获取配置
```

> 💡 **遵循 XDG 基目录规范**：配置放 `~/.config/appname/`，数据放 `~/.local/share/appname/`。这不是强制的，但是 Linux/macOS 社区的最佳实践，让你的工具看起来更专业。

### 7.4 错误处理与用户友好提示

CLI 工具的错误处理有一个核心原则：**永远不要给用户看 Python 堆栈**。用户不需要知道 `FileNotFoundError` 和 `Traceback`，他们只需要知道"哪里出了问题"和"怎么修"。

#### 自定义异常

```python
# src/taskr/core/exceptions.py

class TaskrError(Exception):
    """taskr 基础异常。"""
    pass

class TaskNotFoundError(TaskrError):
    """任务不存在。"""
    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"任务 #{task_id} 不存在")

class StorageError(TaskrError):
    """存储层异常。"""
    pass
```

#### 在命令中优雅地处理错误

```python
# src/taskr/commands/done.py
import typer
from taskr.core.storage import TaskStorage
from taskr.core.exceptions import TaskNotFoundError
from taskr.utils.console import success, error

def register(app: typer.Typer):
    @app.command()
    def done(task_id: int):
        """标记任务为已完成。"""
        storage = TaskStorage()
        try:
            task = storage.complete(task_id)
            success(f"任务已完成: #{task.id} {task.title}")
        except TaskNotFoundError:
            error(f"任务 #{task_id} 不存在，请用 taskr list 查看可用任务")
            raise typer.Exit(code=1)
```

#### 全局异常处理器

对于未预料到的异常，可以在 app 层面统一捕获：

```python
# src/taskr/main.py
import typer
from rich.console import Console

err_console = Console(stderr=True)

def main():
    try:
        app()
    except Exception as e:
        err_console.print(f"[bold red]❌ 未知错误: {e}[/bold red]")
        err_console.print("[dim]请使用 --verbose 查看详细信息，或提交 Issue[/dim]")
        raise typer.Exit(code=1)
```

**错误提示的设计原则：**

```
❌ 坏的错误提示：
  Traceback (most recent call last):
    File "/usr/lib/python3.12/json/decoder.py", line 355, in raw_decode
      raise JSONDecodeError("Expecting value", s, err.value) from None
  json.decoder.JSONDecodeError: Expecting value: line 1 column 1

✅ 好的错误提示：
  ❌ 数据文件损坏: ~/.local/share/taskr/tasks.json
  💡 尝试运行 taskr repair 修复，或删除该文件重新开始
```

> 💡 **好的错误提示 = 说清楚问题 + 给出解决方案**。用户看到错误后应该知道下一步该做什么，而不是一脸茫然。

### 7.5 数据持久化（SQLite/JSON）

对于 taskr 这种轻量级 CLI 工具，**JSON 文件**是最合适的存储方案——人类可读、零依赖、调试方便。更复杂的场景（如多用户、并发写入）才需要上 SQLite。

#### JSON 存储层

```python
# src/taskr/core/storage.py
import json
from datetime import datetime
from pathlib import Path
from taskr.core.models import Task, Priority, Status
from taskr.core.exceptions import TaskNotFoundError, StorageError

DEFAULT_DATA_FILE = Path.home() / ".local" / "share" / "taskr" / "tasks.json"

class TaskStorage:
    """基于 JSON 文件的任务存储。"""

    def __init__(self, data_file: Path | None = None):
        self.data_file = data_file or DEFAULT_DATA_FILE
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[Task]:
        """从文件加载所有任务。"""
        if not self.data_file.exists():
            return []
        try:
            data = json.loads(self.data_file.read_text(encoding="utf-8"))
            return [Task.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError) as e:
            raise StorageError(f"数据文件损坏: {self.data_file}") from e

    def _save(self, tasks: list[Task]):
        """保存所有任务到文件。"""
        data = [task.to_dict() for task in tasks]
        self.data_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _next_id(self, tasks: list[Task]) -> int:
        """生成下一个任务 ID。"""
        return max((t.id for t in tasks), default=0) + 1

    def add(self, title: str, priority: Priority = Priority.medium) -> Task:
        """添加任务。"""
        tasks = self._load()
        task = Task(id=self._next_id(tasks), title=title, priority=priority)
        tasks.append(task)
        self._save(tasks)
        return task

    def list(self, status: Status | None = None) -> list[Task]:
        """列出任务，可按状态过滤。"""
        tasks = self._load()
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def complete(self, task_id: int) -> Task:
        """标记任务完成。"""
        tasks = self._load()
        for task in tasks:
            if task.id == task_id:
                task.status = Status.done
                task.completed_at = datetime.now().isoformat()
                self._save(tasks)
                return task
        raise TaskNotFoundError(task_id)

    def delete(self, task_id: int) -> Task:
        """删除任务。"""
        tasks = self._load()
        for i, task in enumerate(tasks):
            if task.id == task_id:
                deleted = tasks.pop(i)
                self._save(tasks)
                return deleted
        raise TaskNotFoundError(task_id)

    def stats(self) -> dict:
        """统计任务概况。"""
        tasks = self._load()
        return {
            "total": len(tasks),
            "todo": sum(1 for t in tasks if t.status == Status.todo),
            "done": sum(1 for t in tasks if t.status == Status.done),
            "high": sum(1 for t in tasks if t.priority == Priority.high),
        }
```

**存储层设计要点：**

```
为什么不直接用 SQLite？

JSON 文件：
  ✅ 零依赖（标准库 json）
  ✅ 人类可读（可以手动编辑）
  ✅ 调试方便（cat tasks.json 就能看）
  ❌ 不支持并发写入
  ❌ 大数据量性能差

SQLite：
  ✅ 支持并发（WAL 模式）
  ✅ 大数据量性能好
  ✅ 支持复杂查询
  ❌ 二进制文件，不可直接阅读

结论：几百条任务 → JSON 足够
      上万条数据 → 考虑 SQLite
```

> 💡 **存储层完全隔离**——命令层通过 `TaskStorage` 的方法操作数据，不关心底层是 JSON 还是 SQLite。如果将来要换存储方案，只需替换 `storage.py`，其他代码一行不改。

**第 7 章知识回顾：**

| 模块 | 职责 | 关键设计 |
|:---|:---|:---|
| **models.py** | 数据模型定义 | dataclass + Enum，序列化/反序列化 |
| **main.py** | CLI 入口 + 全局选项 | callback + add_typer 组装命令 |
| **commands/** | 各子命令实现 | 调用 core 层，格式化输出 |
| **config.py** | TOML 配置管理 | XDG 规范，默认值兜底 |
| **exceptions.py** | 自定义异常 | 用户友好提示，不暴露堆栈 |
| **storage.py** | JSON 持久化 | 读写隔离，ID 自增 |
| **console.py** | Rich 输出封装 | success/error/warning/info |

---

## 8. 测试与质量保障

CLI 工具的测试比 Web 应用简单得多——输入是字符串（命令行参数），输出也是字符串（终端文本），加上一个退出码。掌握正确的测试策略，能让你的 CLI 工具在重构时保持信心。

### 8.1 使用 CliRunner 测试命令行

Typer 内置了 `CliRunner`（继承自 Click），可以在测试中**模拟终端调用**，不需要真正启动进程：

```python
# tests/test_commands.py
import pytest
from typer.testing import CliRunner
from taskr.main import app

runner = CliRunner()

class TestAddCommand:
    """测试 add 命令。"""

    def test_add_task(self):
        """添加任务应该成功。"""
        result = runner.invoke(app, ["add", "写测试"])
        assert result.exit_code == 0
        assert "任务已添加" in result.output
        assert "写测试" in result.output

    def test_add_with_priority(self):
        """添加任务时可以指定优先级。"""
        result = runner.invoke(app, ["add", "紧急任务", "-p", "high"])
        assert result.exit_code == 0
        assert "high" in result.output

    def test_add_invalid_priority(self):
        """无效的优先级应该报错。"""
        result = runner.invoke(app, ["add", "任务", "-p", "urgent"])
        assert result.exit_code != 0
        assert "Invalid value" in result.output

class TestListCommand:
    """测试 list 命令。"""

    def test_list_empty(self):
        """空列表应该提示用户。"""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "暂无任务" in result.output

    def test_list_json_output(self):
        """--json 应该输出 JSON 格式。"""
        runner.invoke(app, ["add", "测试任务"])
        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert isinstance(data, list)

class TestDoneCommand:
    """测试 done 命令。"""

    def test_done_nonexistent_task(self):
        """完成不存在的任务应该报错。"""
        result = runner.invoke(app, ["done", "999"])
        assert result.exit_code == 1
        assert "不存在" in result.output
```

**CliRunner 的关键属性：**

| 属性 | 说明 | 示例 |
|:---|:---|:---|
| `result.exit_code` | 退出码（0 = 成功） | `assert result.exit_code == 0` |
| `result.output` | 标准输出文本 | `assert "成功" in result.output` |
| `result.exception` | 未捕获的异常 | `assert result.exception is None` |

#### 使用 pytest fixtures 隔离测试数据

```python
# tests/conftest.py
import pytest
from pathlib import Path
import tempfile

@pytest.fixture(autouse=True)
def temp_data_dir(monkeypatch, tmp_path):
    """每个测试用例使用独立的临时数据目录。"""
    data_file = tmp_path / "tasks.json"
    monkeypatch.setattr(
        "taskr.core.storage.DEFAULT_DATA_FILE", data_file
    )
    return tmp_path
```

> 💡 **`autouse=True` 让这个 fixture 自动应用到所有测试**——每个测试函数都在干净的临时目录中运行，不会互相污染数据。

### 8.2 单元测试：业务逻辑与 CLI 层分离

还记得第 7 章我们刻意把业务逻辑放在 `core/` 层吗？现在收获回报——**直接测 core 层，不需要经过 CLI**：

```python
# tests/test_storage.py
import pytest
from pathlib import Path
from taskr.core.storage import TaskStorage
from taskr.core.models import Priority, Status
from taskr.core.exceptions import TaskNotFoundError

@pytest.fixture
def storage(tmp_path):
    """创建使用临时文件的 Storage 实例。"""
    return TaskStorage(data_file=tmp_path / "test_tasks.json")

class TestTaskStorage:
    """测试存储层。"""

    def test_add_and_list(self, storage):
        """添加后能列出任务。"""
        task = storage.add("测试任务", Priority.high)
        assert task.id == 1
        assert task.title == "测试任务"
        assert task.priority == Priority.high

        tasks = storage.list()
        assert len(tasks) == 1
        assert tasks[0].title == "测试任务"

    def test_complete_task(self, storage):
        """完成任务应更新状态。"""
        storage.add("待完成")
        task = storage.complete(1)
        assert task.status == Status.done
        assert task.completed_at is not None

    def test_complete_nonexistent(self, storage):
        """完成不存在的任务应抛出异常。"""
        with pytest.raises(TaskNotFoundError):
            storage.complete(999)

    def test_delete_task(self, storage):
        """删除任务后列表应减少。"""
        storage.add("任务 1")
        storage.add("任务 2")
        storage.delete(1)
        tasks = storage.list()
        assert len(tasks) == 1
        assert tasks[0].title == "任务 2"

    def test_filter_by_status(self, storage):
        """按状态过滤任务。"""
        storage.add("任务 A")
        storage.add("任务 B")
        storage.complete(1)

        todo = storage.list(status=Status.todo)
        done = storage.list(status=Status.done)
        assert len(todo) == 1
        assert len(done) == 1

    def test_stats(self, storage):
        """统计应该正确计数。"""
        storage.add("普通任务")
        storage.add("紧急任务", Priority.high)
        storage.complete(1)

        stats = storage.stats()
        assert stats["total"] == 2
        assert stats["todo"] == 1
        assert stats["done"] == 1
        assert stats["high"] == 1
```

**测试分层策略：**

```
测试金字塔（CLI 项目版）：

         ┌──────────────┐
         │  CLI 端到端   │  ← 少量：验证参数解析和输出格式
         │  (CliRunner)  │     test_commands.py
         ├──────────────┤
         │  业务逻辑     │  ← 大量：验证 CRUD、边界条件
         │  (core 层)    │     test_storage.py, test_models.py
         ├──────────────┤
         │  数据模型     │  ← 中量：验证序列化/反序列化
         │  (models)     │     test_models.py
         └──────────────┘

原则：越底层的测试越多，越快，越稳定
```

> 💡 **为什么不全用 CliRunner 测？** 因为 CliRunner 测试涉及参数解析、输出格式化等环节，速度较慢且错误定位困难。直接测 `TaskStorage`，一个断言失败就能精确定位问题。

### 8.3 Ruff 代码规范与类型检查

测试保证功能正确，**Ruff** 和 **类型检查** 保证代码质量。

#### Ruff：极速 Python Linter + Formatter

Ruff 用 Rust 编写，一个工具替代 Flake8 + isort + Black，速度快 10-100 倍：

```toml
# pyproject.toml 中的 Ruff 配置
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = [
    "E",    # pycodestyle 错误
    "W",    # pycodestyle 警告
    "F",    # pyflakes
    "I",    # isort（导入排序）
    "UP",   # pyupgrade（语法升级）
    "B",    # flake8-bugbear（常见 Bug）
    "SIM",  # flake8-simplify（简化代码）
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

```bash
# 常用命令
$ ruff check .              # 检查代码问题
$ ruff check . --fix        # 自动修复可修复的问题
$ ruff format .             # 格式化代码
$ ruff format . --check     # 检查是否需要格式化（CI 用）
```

#### 类型检查：pyright / mypy

Typer 的一大优势是**类型注解天然存在**，加上类型检查器就能提前发现错误：

```toml
# pyproject.toml
[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "basic"
```

```bash
# 运行类型检查
$ pyright src/
```

#### 一键运行全部检查

在 `pyproject.toml` 中配置测试命令：

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

```bash
# 完整的质量检查流程
$ ruff check .            # 1. Lint 检查
$ ruff format . --check   # 2. 格式检查
$ pyright src/            # 3. 类型检查
$ pytest                  # 4. 运行测试

# 或者用一行脚本搞定
$ ruff check . && ruff format . --check && pytest
```

**第 8 章知识回顾：**

| 工具/策略 | 用途 | 一句话总结 |
|:---|:---|:---|
| **CliRunner** | CLI 端到端测试 | 模拟终端调用，检查 exit_code 和 output |
| **pytest fixtures** | 测试数据隔离 | tmp_path + monkeypatch，每个测试独立干净 |
| **core 层单元测试** | 业务逻辑测试 | 直接调用 Storage 方法，不经过 CLI |
| **测试金字塔** | 测试分层策略 | 底层多、快、稳；顶层少、慢、全 |
| **Ruff** | Lint + 格式化 | 一个工具替代 Flake8 + isort + Black |
| **pyright** | 类型检查 | 配合 Typer 的类型注解，提前发现错误 |

---

## 9. 打包与分发

你的 CLI 工具写好了，测试通过了——现在要让全世界的人都能用上它。这一章覆盖从"一个本地项目"到"全球任何人都能 `pip install` 的 CLI 工具"的完整流程。

### 9.1 entry_points：让包变成命令

第 2 章我们简单提过 `[project.scripts]`，这里深入理解它的工作原理：

```toml
# pyproject.toml
[project]
name = "taskr"
version = "0.1.0"
description = "一个现代化的终端任务管理工具"
requires-python = ">=3.12"
dependencies = [
    "typer[all]>=0.12.0",
    "rich>=13.0.0",
]

[project.scripts]
taskr = "taskr.main:app"
```

**`taskr = "taskr.main:app"` 的含义：**

```
taskr = "taskr.main:app"
  │         │       │
  │         │       └── app 是 main.py 中的 Typer() 实例
  │         └────────── taskr.main 是 Python 模块路径
  └──────────────────── taskr 是终端命令名

安装后，pip/uv 会在虚拟环境的 bin/ 目录下
生成一个名为 taskr 的可执行脚本：

#!/path/to/python
from taskr.main import app
app()
```

#### 多入口点

一个包可以提供多个命令：

```toml
[project.scripts]
taskr = "taskr.main:app"             # 主命令
taskr-migrate = "taskr.migrate:app"  # 数据迁移工具（仅开发者使用）
```

### 9.2 构建与本地测试

#### 构建分发包

```bash
# 安装构建工具
$ uv pip install build

# 构建 sdist（源码包）和 wheel（二进制包）
$ python -m build

# 构建产物在 dist/ 目录下
dist/
├── taskr-0.1.0.tar.gz      ← sdist（源码压缩包）
└── taskr-0.1.0-py3-none-any.whl  ← wheel（安装包）
```

**sdist vs wheel：**

| 格式 | 说明 | 安装速度 |
|:---|:---|:---|
| **sdist** (.tar.gz) | 源码压缩包，安装时需要执行构建步骤 | 🐢 慢 |
| **wheel** (.whl) | 预构建的二进制包，解压即安装 | 🚀 快 |

> 💡 **发布时应该同时上传 sdist 和 wheel**。wheel 用于快速安装，sdist 作为保底（某些平台可能没有对应的 wheel）。

#### 本地验证

发布前，先在本地验证安装包是否正常：

```bash
# 创建一个干净的虚拟环境来测试
$ python -m venv /tmp/test-taskr
$ source /tmp/test-taskr/bin/activate

# 从本地 wheel 安装
$ pip install dist/taskr-0.1.0-py3-none-any.whl

# 验证命令是否可用
$ taskr --version
taskr 0.1.0

$ taskr --help
$ taskr add "测试安装"
$ taskr list

# 测试通过后，清理环境
$ deactivate
```

### 9.3 发布到 PyPI

PyPI（Python Package Index）是 Python 的官方包仓库，`pip install` 默认从这里下载。

#### 发布前准备

```bash
# 1. 注册 PyPI 账号
#    访问 https://pypi.org/account/register/

# 2. 创建 API Token（推荐，比密码安全）
#    访问 https://pypi.org/manage/account/token/
#    保存 token，格式：pypi-xxxxxxxxxxxx

# 3. 安装上传工具
$ uv pip install twine
```

#### 先在 TestPyPI 上测试

**强烈建议**先发布到 TestPyPI 验证一切正常，再发布到正式 PyPI：

```bash
# 上传到 TestPyPI（测试仓库）
$ twine upload --repository testpypi dist/*

# 从 TestPyPI 安装测试
$ pip install --index-url https://test.pypi.org/simple/ taskr

# 验证安装正常
$ taskr --version
```

#### 正式发布

```bash
# 上传到正式 PyPI
$ twine upload dist/*

# 输入 API Token（用户名填 __token__）
# Username: __token__
# Password: pypi-xxxxxxxxxxxx（你的 API Token）

# 发布成功！全世界都能安装了
$ pip install taskr
```

**发布 checklist：**

```
发布前必做：
  ☐ 版本号已更新（pyproject.toml 和 __init__.py）
  ☐ CHANGELOG 已更新
  ☐ 所有测试通过（pytest + ruff）
  ☐ README 已更新
  ☐ 在 TestPyPI 验证过
  ☐ Git tag 已打（git tag v0.1.0）
```

> 💡 **包名在 PyPI 上是全局唯一的**。如果 `taskr` 被占用了，你需要改名（比如 `taskr-cli`）。发布前先在 pypi.org 上搜索确认。

### 9.4 用 pipx 安装 CLI 工具

`pipx` 是专门为 **CLI 工具**设计的安装方式——它会为每个工具创建独立的虚拟环境，避免依赖冲突：

```bash
# 安装 pipx
$ pip install pipx
$ pipx ensurepath  # 确保 pipx 的 bin 目录在 PATH 中

# 安装 CLI 工具（每个工具有独立的虚拟环境）
$ pipx install taskr

# 直接使用（全局可用，不需要激活任何虚拟环境）
$ taskr --version
$ taskr add "Hello pipx!"

# 升级
$ pipx upgrade taskr

# 卸载
$ pipx uninstall taskr
```

**pip vs pipx 安装 CLI 工具：**

```
pip install taskr：
  ├── 安装到当前虚拟环境（或全局 Python）
  ├── 可能和其他包的依赖冲突
  └── 退出虚拟环境后命令就不能用了

pipx install taskr：
  ├── 自动创建独立的虚拟环境
  ├── 依赖完全隔离
  └── 命令全局可用（任何时候都能用）
```

> 💡 **在 README 中推荐 pipx 安装方式**。对于 CLI 工具的用户来说，`pipx install taskr` 比 `pip install taskr` 更安全、更省心。

### 9.5 GitHub Actions 自动发布流水线

手动发布容易出错。用 GitHub Actions 实现"打 tag → 自动测试 → 自动发布"的全自动流水线：

```yaml
# .github/workflows/publish.yml
name: 发布到 PyPI

on:
  push:
    tags:
      - "v*"  # 当推送 v 开头的 tag 时触发（如 v0.1.0）

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install uv
      - run: uv sync --dev
      - run: uv run ruff check .
      - run: uv run pytest

  publish:
    needs: test  # 测试通过后才发布
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # PyPI Trusted Publisher 需要
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
        # 使用 Trusted Publisher，不需要 API Token
```

**发布工作流：**

```
开发者操作：
  $ git tag v0.1.0
  $ git push origin v0.1.0

自动触发：
  GitHub Actions
    ├── test:     ruff check → pytest
    ├── build:    python -m build
    └── publish:  twine upload → PyPI

用户安装：
  $ pipx install taskr
```

> 💡 **Trusted Publisher** 是 PyPI 2023 年推出的新特性——在 PyPI 上配置 GitHub 仓库后，GitHub Actions 可以不需要 API Token 直接发布。更安全，推荐使用。

**第 9 章知识回顾：**

| 步骤 | 工具/命令 | 一句话总结 |
|:---|:---|:---|
| **入口点配置** | `[project.scripts]` | 把 Python 函数映射为终端命令 |
| **构建** | `python -m build` | 生成 sdist + wheel 两种分发格式 |
| **本地验证** | 临时虚拟环境 + pip install | 发布前在干净环境中测试安装 |
| **发布** | `twine upload dist/*` | 上传到 PyPI（先 TestPyPI 再正式） |
| **用户安装** | `pipx install` | 独立虚拟环境，全局命令，推荐方式 |
| **自动发布** | GitHub Actions | 打 tag 自动触发测试和发布 |

---

## 10. 进阶技巧与最佳实践

恭喜你已经掌握了构建专业 CLI 工具的全部核心技能。这最后一章收录了一些**锦上添花的进阶技巧**和经过实战检验的**设计原则**，让你的 CLI 工具从"能用"升级到"好用"。

### 10.1 Shell 自动补全

Typer 内置了 Shell 自动补全支持——用户按 Tab 键就能自动补全命令名和参数值：

```bash
# 安装 Bash 自动补全
$ taskr --install-completion bash
# → 会写入 ~/.bash_completions/taskr.sh

# 安装 Zsh 自动补全（macOS 默认 Shell）
$ taskr --install-completion zsh

# 安装 Fish 自动补全
$ taskr --install-completion fish

# 安装后重启 Shell 或 source 配置文件
$ source ~/.zshrc
```

安装完成后：

```bash
$ taskr <TAB>
add    list    done    delete    stats

$ taskr add --priority <TAB>
low    medium    high

$ taskr list --status <TAB>
all    todo    done
```

**自定义补全逻辑**：对于动态值（如任务 ID），可以提供自定义补全函数：

```python
import typer

def complete_task_id(incomplete: str) -> list[str]:
    """动态补全任务 ID。"""
    storage = TaskStorage()
    tasks = storage.list()
    return [str(t.id) for t in tasks if str(t.id).startswith(incomplete)]

@app.command()
def done(
    task_id: int = typer.Argument(..., autocompletion=complete_task_id),
):
    """标记任务完成。"""
    ...
```

> 💡 **自动补全是 CLI 工具用户体验的分水岭**。有了它，用户不需要记命令——按 Tab 就行。Typer 几乎零成本就能获得这个能力。

### 10.2 交互式输入与确认提示

有些操作需要用户交互——输入密码、选择选项、确认危险操作：

```python
import typer

@app.command()
def init():
    """交互式初始化项目。"""
    # 文本输入
    name = typer.prompt("项目名称")

    # 带默认值的输入
    version = typer.prompt("初始版本号", default="0.1.0")

    # 密码输入（不回显）
    token = typer.prompt("API Token", hide_input=True)

    # 确认提示（y/N）
    if typer.confirm(f"确认创建项目 '{name}' v{version}?"):
        print(f"✅ 项目 {name} 已创建")
    else:
        print("已取消")
        raise typer.Abort()
```

```bash
$ taskr init
项目名称: my-tool
初始版本号 [0.1.0]: 1.0.0
API Token: ********
确认创建项目 'my-tool' v1.0.0? [y/N]: y
✅ 项目 my-tool 已创建
```

**设计原则**：交互式输入适合**一次性的初始化操作**。日常重复使用的命令应该用命令行参数，方便脚本调用和自动化。

### 10.3 环境变量与 Pydantic Settings

对于需要 API Key、数据库连接等敏感配置的 CLI 工具，**环境变量**是最佳实践。配合 `pydantic-settings`，可以自动从环境变量、`.env` 文件和命令行参数中加载配置：

```python
# src/taskr/core/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """应用设置（自动从环境变量加载）。"""
    model_config = SettingsConfigDict(
        env_prefix="TASKR_",       # 环境变量前缀
        env_file=".env",           # 支持 .env 文件
    )

    api_key: str = ""              # TASKR_API_KEY
    database_url: str = "sqlite:///tasks.db"  # TASKR_DATABASE_URL
    debug: bool = False            # TASKR_DEBUG
    max_tasks: int = 1000          # TASKR_MAX_TASKS
```

```bash
# 方式 1：环境变量
$ export TASKR_API_KEY=sk-xxxxx
$ export TASKR_DEBUG=true
$ taskr list

# 方式 2：.env 文件（推荐开发环境使用）
$ cat .env
TASKR_API_KEY=sk-xxxxx
TASKR_DEBUG=true

# 方式 3：命令行参数优先级最高（覆盖环境变量）
$ taskr --api-key sk-yyyyy list
```

**配置优先级：** 命令行参数 > 环境变量 > `.env` 文件 > 默认值

> 💡 **永远不要把 API Key 硬编码或提交到 Git**。在 README 中告诉用户用环境变量或 `.env` 文件，并在 `.gitignore` 中加入 `.env`。

### 10.4 插件机制设计

当 CLI 工具变大，你可能希望允许第三方开发者扩展功能。Python 的 **entry_points** 提供了一个优雅的插件发现机制：

```toml
# 主项目 pyproject.toml —— 定义插件接口
[project.entry-points."taskr.plugins"]
# 内置插件
builtin = "taskr.plugins.builtin:register"
```

```toml
# 第三方插件的 pyproject.toml
[project.entry-points."taskr.plugins"]
jira = "taskr_jira:register"  # 第三方 Jira 集成插件
```

```python
# src/taskr/plugins/loader.py
from importlib.metadata import entry_points

def load_plugins(app):
    """自动发现并加载所有已安装的插件。"""
    plugins = entry_points(group="taskr.plugins")
    for plugin in plugins:
        register_func = plugin.load()  # 加载插件的 register 函数
        register_func(app)             # 把插件的命令注册到 app
        print(f"[dim]已加载插件: {plugin.name}[/dim]")
```

```python
# 第三方插件示例：taskr-jira/src/taskr_jira/__init__.py
import typer

def register(app: typer.Typer):
    """注册 Jira 集成命令。"""
    jira_app = typer.Typer(help="Jira 集成")
    app.add_typer(jira_app, name="jira")

    @jira_app.command()
    def sync():
        """同步任务到 Jira。"""
        print("🔄 正在同步到 Jira...")
```

安装插件后，命令自动出现：

```bash
$ pip install taskr-jira
$ taskr jira sync
🔄 正在同步到 Jira...
```

> 💡 **插件机制适合大型 CLI 项目**（如 pytest、pip）。小工具不需要这个复杂度。

### 10.5 CLI 设计原则速查表

最后，整理一份经过实战验证的 **CLI 设计原则**，可以贴在工位上随时参考：

**命令设计：**

| 原则 | ✅ 好的 | ❌ 坏的 |
|:---|:---|:---|
| 命令名用动词 | `taskr add` / `taskr delete` | `taskr task` / `taskr new-task` |
| 操作对象用名词 | `git commit` / `docker build` | `git doing` / `docker making` |
| 短选项用单字母 | `-v` / `-f` / `-o` | `-vb` / `-fmt` |
| 长选项用连字符 | `--output-dir` | `--outputDir` / `--output_dir` |
| 必须有 `--help` | 自动生成 | 需要用户猜 |
| 必须有 `--version` | `taskr --version` | 用户不知道版本号 |

**输出设计：**

| 原则 | 说明 |
|:---|:---|
| **成功静默，失败大声** | 正常操作少输出，错误时详细提示 |
| **支持 `--json`** | 人看表格，机器读 JSON |
| **支持 `--quiet`** | 安静模式，只输出结果，不输出装饰 |
| **错误输出到 stderr** | `Console(stderr=True)`，不污染 stdout |
| **退出码有意义** | 0 = 成功，1 = 通用错误，2 = 用法错误 |

**交互设计：**

| 原则 | 说明 |
|:---|:---|
| **危险操作要确认** | `taskr delete` 应该先 `confirm()` |
| **可以跳过确认** | 提供 `--yes` / `--force` 选项 |
| **交互可脚本化** | 所有交互式输入都能通过参数传入 |

> 💡 **一句话总结 CLI 设计的核心：让简单的事情简单，让复杂的事情可能。**

**第 10 章知识回顾：**

| 技巧 | 一句话总结 |
|:---|:---|
| **Shell 自动补全** | `--install-completion` 一键安装，Tab 补全命令 |
| **交互式输入** | `typer.prompt()` + `typer.confirm()` 处理敏感输入 |
| **Pydantic Settings** | 环境变量 + .env 文件 + 命令行参数自动融合 |
| **插件机制** | entry_points 发现 + register 函数注册 |
| **设计原则** | 成功静默、支持 JSON、退出码有意义 |

---

## 附录

### A. Click vs Typer vs argparse 对比速查表

| 特性 | argparse | Click | Typer |
|:---|:---|:---|:---|
| **类型** | 标准库 | 第三方库 | 第三方库（基于 Click） |
| **参数声明** | `add_argument()` | `@click.option()` 装饰器 | 函数类型注解 |
| **子命令** | subparsers + if/elif | `@click.group()` | `app.add_typer()` |
| **类型安全** | ❌ Namespace | ❌ 无类型提示 | ✅ 完整类型注解 |
| **自动帮助** | ✅ 基础 | ✅ 较好 | ✅ 最佳（Rich 美化） |
| **测试工具** | ❌ 无 | ✅ CliRunner | ✅ CliRunner |
| **Shell 补全** | ❌ 无 | ✅ 需配置 | ✅ 内置 |
| **学习曲线** | 中等 | 中等 | 低（会写函数就行） |
| **适用场景** | 简单脚本/零依赖 | 成熟项目/需要底层控制 | 新项目/追求开发效率 |

### B. 常用第三方库推荐

| 库 | 用途 | 安装 |
|:---|:---|:---|
| **typer** | CLI 框架 | `uv add typer[all]` |
| **rich** | 终端美化 | `uv add rich` |
| **click** | CLI 框架（Typer 底层） | `uv add click` |
| **pydantic-settings** | 配置管理 | `uv add pydantic-settings` |
| **httpx** | HTTP 客户端 | `uv add httpx` |
| **shellingham** | Shell 检测 | `uv add shellingham` |
| **pytest** | 测试框架 | `uv add --dev pytest` |
| **ruff** | Lint + 格式化 | `uv add --dev ruff` |
| **pyright** | 类型检查 | `uv add --dev pyright` |

### C. 参考资源

- **Typer 官方文档**：https://typer.tiangolo.com
- **Click 官方文档**：https://click.palletsprojects.com
- **Rich 官方文档**：https://rich.readthedocs.io
- **uv 官方文档**：https://docs.astral.sh/uv
- **Python 打包用户指南**：https://packaging.python.org
- **PyPI**：https://pypi.org
- **CLIG（CLI 设计指南）**：https://clig.dev
- **12 Factor CLI Apps**：https://medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46
