# 0 基础 AI 应用开发实战课程

> 从零开始，用 AI 编程工具学全栈，用全栈知识做 AI 应用——面向完全零基础学员的系统化课程。

---

## 1. AI 应用开发全景图

很多人听到"AI 开发"，脑子里浮现的是训练神经网络、调参炼丹、跑 GPU 集群。但在 2025 年，**绝大多数 AI 应用开发者不需要训练任何模型**。你要做的事情，更接近于"调用 AI 的能力，构建解决真实问题的产品"。

本章的目标是帮你建立一个正确的心智模型：AI 应用开发到底在做什么？需要哪些技术？和传统开发有什么区别？

---

### 1.1 2025 年 AI 应用到底在做什么

#### 一个关键认知：你不需要训练模型

先看一组对比：

| | AI 研究员 / 算法工程师 | AI 应用开发者（本课程目标） |
|---|---|---|
| **核心工作** | 设计模型架构、训练模型、优化算法 | 调用模型 API、构建产品、解决业务问题 |
| **技术栈** | PyTorch、CUDA、分布式训练 | Python、FastAPI、React、LLM API |
| **硬件需求** | 多卡 GPU 集群 | 一台普通电脑 |
| **学习周期** | 数年（需数学/统计基础） | 数月（本课程的目标） |
| **类比** | 发动机工程师 | 汽车驾驶员 + 改装师 |

大模型时代的 AI 应用开发，本质上是：

```
把大模型的"智能"能力，通过 API 接入到你的产品中，
配合前端界面、后端逻辑、数据库存储，
构建一个用户可以使用的完整应用。
```

你不需要理解 Transformer 的每一个数学公式，就像你不需要理解发动机的热力学原理也能开好一辆车。

#### 真实 AI 应用长什么样？

让我们拆解几个你每天都在用的 AI 产品，看看它们的技术架构有多"简单"：

**案例 1：AI 聊天助手（如 ChatGPT、豆包）**

```
用户输入文字 → 前端发送请求 → 后端调用 LLM API → 流式返回文字 → 前端逐字显示
```

核心技术：前端（聊天界面）+ 后端（API 转发）+ LLM API 调用 + 流式输出

**案例 2：AI 客服（基于企业知识库）**

```
用户提问 → 后端从知识库检索相关文档 → 把文档 + 问题一起发给 LLM → LLM 基于文档生成回答
```

核心技术：前端 + 后端 + 数据库 + RAG（检索增强生成）+ LLM API

**案例 3：AI 写作助手（如 Notion AI）**

```
用户选中文字 → 发送"帮我润色/翻译/扩写"指令 → 后端组装 Prompt → 调用 LLM → 返回结果替换原文
```

核心技术：前端（编辑器集成）+ 后端 + Prompt Engineering + LLM API

**案例 4：AI 自动化 Agent（如自动填表、自动调研）**

```
用户下达目标 → Agent 自主规划步骤 → 循环执行：调用工具 → 观察结果 → 决定下一步 → 输出最终结果
```

核心技术：前端 + 后端 + Function Calling + Agent 循环 + 多个外部 API

#### 发现规律了吗？

从这四个案例中，你会发现 AI 应用开发的**通用公式**：

```
AI 应用 = 前端界面 + 后端逻辑 + 数据存储 + LLM 能力
```

其中：
- ✅ **前端界面**：用户和 AI 交互的窗口（聊天框、表单、编辑器……）
- ✅ **后端逻辑**：接收请求、组装 Prompt、调用 API、处理结果
- ✅ **数据存储**：保存用户数据、对话记录、知识库文档
- ✅ **LLM 能力**：通过 API 调用大模型，获得"智能"输出

这四个部分，就是本课程接下来要教你的全部内容。

#### 和传统 Web 开发的区别

如果你了解过传统 Web 开发，AI 应用开发只是在其基础上多了一层"AI 能力"：

```
传统 Web 应用:
  前端 → 后端 → 数据库
  （所有逻辑都是人写的规则）

AI 应用:
  前端 → 后端 → 数据库
                ↓
           LLM API（AI 提供"智能"决策）
```

| 能力 | 传统 Web 开发 | AI 应用开发 |
|---|---|---|
| 文本生成 | ❌ 需要人工编写模板 | ✅ LLM 自动生成 |
| 语义理解 | ❌ 只能关键词匹配 | ✅ 理解用户意图 |
| 知识问答 | ❌ 需要构建规则引擎 | ✅ RAG + LLM |
| 自动化决策 | ❌ 硬编码 if-else | ✅ Agent 自主规划 |
| 多语言翻译 | ❌ 依赖翻译 API | ✅ LLM 原生支持 |

**结论**：AI 应用开发 = 传统全栈开发 + AI 能力集成。所以本课程的前半部分教你全栈基础，后半部分教你 AI 集成。两者缺一不可。

### 1.2 一个 AI 应用的完整技术栈拆解

上一节我们说了 AI 应用 = 前端 + 后端 + 数据库 + LLM 能力。这一节我们把每一层拆开，看看具体用到哪些技术，以及它们在本课程中对应哪些章节。

#### 技术栈全景图

```
┌─────────────────────────────────────────────────┐
│                    用户浏览器                      │
├─────────────────────────────────────────────────┤
│  前端层（用户看到的界面）                            │
│  HTML + CSS + JavaScript + React                │
│  课程章节：第 4-7 章                               │
├─────────────────────────────────────────────────┤
│  后端层（服务器端逻辑）                              │
│  Python + FastAPI                               │
│  课程章节：第 8-9 章                               │
├─────────────────────────────────────────────────┤
│  数据层（数据持久化）                                │
│  SQLite / PostgreSQL + 向量数据库                  │
│  课程章节：第 10 章                                │
├─────────────────────────────────────────────────┤
│  AI 能力层（大模型集成）                             │
│  LLM API + Prompt + RAG + Agent                 │
│  课程章节：第 12-16 章                              │
└─────────────────────────────────────────────────┘
```

#### 各层职责详解

**前端层：用户和 AI 交互的窗口**

| 技术 | 作用 | 本课程章节 |
|---|---|---|
| HTML | 页面结构（按钮、输入框、文字） | 第 4 章 |
| CSS | 页面样式（颜色、布局、动画） | 第 4 章 |
| JavaScript | 页面逻辑（点击事件、数据请求） | 第 5 章 |
| React | 组件化开发框架（高效构建复杂界面） | 第 6 章 |

前端负责的典型功能：聊天气泡界面、打字机效果、Markdown 渲染、文件上传。

**后端层：接收请求、处理逻辑、调用 AI**

| 技术 | 作用 | 本课程章节 |
|---|---|---|
| Python | 后端编程语言 | 第 8 章 |
| FastAPI | Web 框架（定义 API 接口） | 第 9 章 |
| Pydantic | 数据校验（确保请求参数正确） | 第 9 章 |

后端负责的典型功能：接收前端请求、组装 Prompt、调用 LLM API、管理对话历史、流式转发。

**数据层：保存一切需要持久化的信息**

| 技术 | 作用 | 本课程章节 |
|---|---|---|
| SQLite | 轻量级关系数据库（用户、对话记录） | 第 10 章 |
| 向量数据库 | 存储文档向量（RAG 检索用） | 第 14 章 |

**AI 能力层：让应用"智能"起来**

| 技术 | 作用 | 本课程章节 |
|---|---|---|
| LLM API | 调用大模型生成文本 | 第 12 章 |
| Prompt Engineering | 设计精准的指令让 AI 输出高质量结果 | 第 12 章 |
| 对话管理 | 让 AI "记住"上下文 | 第 13 章 |
| RAG | 让 AI 基于你的私有文档回答问题 | 第 14 章 |
| Function Calling | 让 AI 调用外部工具（搜索、查数据库） | 第 15 章 |
| Agent | 让 AI 自主规划和执行复杂任务 | 第 16 章 |

#### 一个请求的完整生命周期

以"用户问 AI 客服一个产品问题"为例，完整的数据流是这样的：

```
1. 用户在聊天框输入问题，点击发送
   └→ 前端（React）通过 HTTP 请求发送到后端

2. 后端（FastAPI）接收请求
   └→ 从数据库查询该用户的对话历史

3. 后端从向量数据库检索相关产品文档（RAG）
   └→ 把"对话历史 + 检索到的文档 + 用户问题"组装成 Prompt

4. 后端调用 LLM API，传入组装好的 Prompt
   └→ LLM 返回流式响应（一个字一个字地返回）

5. 后端通过 SSE 把流式响应转发给前端
   └→ 同时把 AI 的回答存入数据库

6. 前端接收流式数据，逐字渲染到聊天气泡中
   └→ 用户看到 AI 的回答"打字"出来
```

**这就是本课程的终极目标**：学完之后，你能独立实现上面这个完整链路的每一步。

### 1.3 AI 编程工具（Cursor/Windsurf）入门

在这门课程中，你不会独自面对一个空白的代码编辑器——你有一个 AI 搭档。**AI 编程工具**是 2024-2025 年最大的开发效率革命，它让"不会编程的人也能写代码"变成了现实。

#### 什么是 AI 编程工具？

AI 编程工具就是一个**内置了 AI 助手的代码编辑器**。你可以用自然语言描述你想要的功能，AI 帮你生成代码。

```
传统编程方式:
  你 → 思考逻辑 → 手写代码 → 调试 → 修改 → 完成

AI 辅助编程方式:
  你 → 用自然语言描述需求 → AI 生成代码 → 你审核/修改 → 完成
```

**主流工具对比：**

| 工具 | 特点 | 价格 | 推荐度 |
|---|---|---|---|
| **Cursor** | 功能最强，支持多模型，社区活跃 | 免费版可用 / $20/月 Pro | ⭐⭐⭐⭐⭐ |
| **Windsurf** | 界面好看，上手简单，自动补全优秀 | 免费版可用 / $15/月 Pro | ⭐⭐⭐⭐ |
| **GitHub Copilot** | VS Code 插件，老牌工具 | $10/月 | ⭐⭐⭐⭐ |

本课程推荐使用 **Cursor**（功能最全，学习资源最多），但使用其他工具不影响学习。

#### AI 编程的三种交互方式

**1. Chat（对话模式）：最常用**

在侧边栏和 AI 对话，描述你想要的功能，AI 生成完整代码：

```
你：帮我写一个 Python 函数，接收一个 URL 列表，并发请求每个 URL，返回所有响应的状态码

AI：好的，这是实现代码...（生成完整的 async 函数）
```

**2. Inline Edit（行内编辑）：精确修改**

选中一段代码，按快捷键，告诉 AI 怎么改：

```
你选中代码，输入：把这个函数改成异步的，加上错误处理和超时机制

AI：直接在原位修改代码
```

**3. Autocomplete（自动补全）：随手就来**

你写了一行代码的开头，AI 自动补全后续内容：

```
你输入：def calculate_total_price(items
AI 自动补全：, tax_rate=0.08):
               total = sum(item['price'] * item['quantity'] for item in items)
               return total * (1 + tax_rate)
```

#### 正确姿势：AI 编程不是"抄作业"

很多初学者犯的错误是把 AI 当成"代码生成器"——让它生成代码后直接复制粘贴，完全不理解代码在做什么。

**正确的使用姿势：**

- ✅ **AI 写，你审**：AI 生成代码后，逐行阅读，理解逻辑
- ✅ **不懂就问**：看不懂某行代码？直接问 AI "这行是什么意思"
- ✅ **渐进式学习**：先让 AI 写，你看懂后尝试自己改，最终自己写
- ❌ **不要盲目信任**：AI 也会犯错，生成的代码需要你验证
- ❌ **不要跳过理解**：不理解的代码 = 不属于你的能力

### 1.4 实战：用 AI 工具 10 分钟生成并运行你的第一个程序

理论讲完了，现在动手。这个实战的目标很简单：**让你在 10 分钟内体验"用自然语言写出可运行的程序"的感觉**。

#### 准备工作

1. 下载并安装 [Cursor](https://cursor.sh)（免费版即可）
2. 打开 Cursor，新建一个文件夹作为工作区

#### Step 1：用对话生成一个完整程序

按 `Cmd+L`（Mac）或 `Ctrl+L`（Windows）打开 AI 对话框，输入以下指令：

```
帮我写一个 Python 程序：
- 用户输入一个城市名
- 程序输出这个城市的趣味冷知识（你编造 3 条即可）
- 输出要有颜色和格式
```

AI 会生成类似这样的代码：

```python
def city_facts(city: str):
    """生成城市趣味冷知识"""
    facts = {
        "北京": [
            "🏛️ 北京的胡同总长度加起来超过 3000 公里，比北京到广州还远",
            "🦆 全聚德烤鸭店自 1864 年开业以来，已经烤了超过 2 亿只鸭子",
            "🚇 北京地铁每天运送约 1000 万人次，相当于搬运一个瑞典的人口"
        ],
        "上海": [
            "🏗️ 上海的摩天大楼数量超过纽约，排名全球第一",
            "🥟 上海人每年消费的小笼包可以绕地球一圈",
            "🌉 上海拥有超过 400 座桥梁，是一座真正的'桥城'"
        ]
    }

    print(f"\n{'='*40}")
    print(f"  🌍 {city} 趣味冷知识")
    print(f"{'='*40}\n")

    city_data = facts.get(city, None)
    if city_data:
        for i, fact in enumerate(city_data, 1):
            print(f"  {i}. {fact}\n")
    else:
        print(f"  暂时没有 {city} 的冷知识，试试输入 '北京' 或 '上海'")

    print(f"{'='*40}")

if __name__ == "__main__":
    city = input("请输入一个城市名：")
    city_facts(city)
```

#### Step 2：运行程序

在 Cursor 的终端中（按 `` Ctrl+` `` 打开终端），运行：

```bash
python city_facts.py
```

输入"北京"，你会看到格式化的输出——**这是你的第一个程序！**

#### Step 3：用自然语言迭代改进

现在体验 AI 编程最强大的能力——**用自然语言修改代码**：

```
请求 1：把城市数据改成从豆包 API 实时生成，而不是硬编码
请求 2：加一个循环，让用户可以连续查询多个城市，输入 'quit' 退出
请求 3：把结果保存到一个 txt 文件中
```

每次你提出一个修改，AI 都会帮你更新代码。你只需要审核、理解、运行。

#### 本章小结

```
✅ 你已经理解了：
  • AI 应用开发 ≠ 训练模型，而是调用 API + 构建产品
  • AI 应用 = 前端 + 后端 + 数据库 + LLM 能力
  • AI 编程工具让你用自然语言就能写代码
  • 正确姿势：AI 写 → 你审 → 你理解 → 你改进

🎯 下一章你将学习：
  • 搭建完整的开发环境（终端、Node.js、Python）
  • 为后续所有实战项目做好准备
```

---

## 2. 开发环境搭建

工欲善其事，必先利其器。在写任何代码之前，你需要把开发环境准备好。本章会教你搭建一个完整的开发环境，确保后续所有章节的实战都能顺利进行。

---

### 2.1 终端与命令行基础操作

#### 什么是终端？

终端（Terminal）就是一个**用文字和电脑对话的窗口**。你在里面输入命令，电脑执行并返回结果。

```
你平时的操作方式：
  双击文件夹打开 → 拖拽文件 → 点击按钮

命令行方式：
  输入 "ls" → 列出文件
  输入 "cd projects" → 进入 projects 文件夹
  输入 "mkdir my-app" → 创建 my-app 文件夹
```

为什么开发者都用命令行？因为很多开发工具（npm、pip、git、python）都通过命令行操作，没有图形界面。

#### 打开终端

| 操作系统 | 打开方式 |
|---|---|
| **Mac** | `Cmd + 空格` 搜索 "Terminal"，或在 Cursor 中按 `` Ctrl+` `` |
| **Windows** | 搜索 "PowerShell"，或安装 Windows Terminal |

> 提示：在 Cursor 编辑器中，按 `` Ctrl+` `` 可以直接打开内置终端，这是最常用的方式。

#### 必会命令速查表

你不需要记住所有命令，只需要掌握以下 10 个就够应付 90% 的场景：

**文件和目录操作：**

| 命令 | 作用 | 示例 |
|---|---|---|
| `pwd` | 显示当前所在的目录路径 | `pwd` → `/Users/you/projects` |
| `ls` | 列出当前目录下的文件 | `ls` → `index.html  style.css  app.js` |
| `cd` | 进入某个目录 | `cd my-project` |
| `cd ..` | 返回上一级目录 | `cd ..` |
| `mkdir` | 创建新文件夹 | `mkdir my-app` |
| `touch` | 创建新文件（Mac/Linux） | `touch index.html` |
| `rm` | 删除文件 | `rm old-file.txt` |
| `rm -rf` | 删除文件夹及其内容 | `rm -rf old-project`（⚠️ 谨慎使用） |

**程序运行相关：**

| 命令 | 作用 | 示例 |
|---|---|---|
| `python` | 运行 Python 文件 | `python app.py` |
| `node` | 运行 JavaScript 文件 | `node server.js` |
| `Ctrl+C` | 强制停止正在运行的程序 | 按 `Ctrl+C` 停止服务器 |

#### 路径的概念

路径是文件在电脑中的"地址"，理解路径就不会迷路：

```
绝对路径（从根目录开始的完整地址）：
  Mac:     /Users/you/projects/my-app/index.html
  Windows: C:\Users\you\projects\my-app\index.html

相对路径（从当前位置出发）：
  ./          → 当前目录
  ../         → 上一级目录
  ./src/      → 当前目录下的 src 文件夹
  ../../      → 上两级目录
```

#### 实践练习

打开终端，跟着做一遍：

```bash
# 1. 查看当前目录
pwd

# 2. 创建一个课程专用文件夹
mkdir ai-course
cd ai-course

# 3. 创建一个子文件夹和文件
mkdir chapter-01
cd chapter-01
touch hello.py

# 4. 查看文件列表
ls

# 5. 返回上一级
cd ..
pwd
```

如果你能顺利完成这些操作，终端基础就够了。后续遇到新命令，随时问 AI。

### 2.2 Node.js + Python 环境安装与配置

本课程前端用 JavaScript（需要 Node.js），后端用 Python。两个都要装。

#### 为什么需要 Node.js？

Node.js 不是一门语言，它是**让 JavaScript 能在电脑上运行的运行环境**。你写的 React 前端项目需要 Node.js 来启动开发服务器、安装依赖包。

#### 为什么需要 Python？

Python 是本课程后端和 AI 集成的主力语言。调用 LLM API、写 FastAPI 后端、操作数据库，都用 Python。

#### 安装 Node.js

**Mac：**

```bash
# 方式 1：直接去官网下载安装包（推荐新手）
# 访问 https://nodejs.org，下载 LTS（长期支持）版本，双击安装

# 方式 2：使用 Homebrew（如果你已经安装了 Homebrew）
brew install node
```

**Windows：**

```bash
# 去官网 https://nodejs.org 下载 LTS 版本
# 双击安装包，一路 Next 即可
```

**验证安装成功：**

```bash
node --version    # 应该输出类似 v20.x.x
npm --version     # 应该输出类似 10.x.x
```

#### 安装 Python

**Mac：**

```bash
# Mac 自带 Python，但版本可能太旧
# 推荐使用 Homebrew 安装最新版
brew install python

# 或者去官网下载：https://www.python.org/downloads/
```

**Windows：**

```bash
# 去官网 https://www.python.org/downloads/ 下载
# ⚠️ 安装时一定要勾选 "Add Python to PATH"（非常重要！）
```

**验证安装成功：**

```bash
python3 --version   # Mac，应该输出类似 Python 3.12.x
python --version    # Windows，应该输出类似 Python 3.12.x
pip --version       # 应该输出 pip 的版本号
```

> ⚠️ Mac 用户注意：系统自带的 `python` 可能指向旧版 Python 2，请始终使用 `python3` 命令。

#### 常见问题排查

| 问题 | 原因 | 解决方案 |
|---|---|---|
| `node: command not found` | Node.js 未安装或未加入 PATH | 重新安装，确保安装完重启终端 |
| `python: command not found` | Python 未安装或未加入 PATH | Windows：重装时勾选 "Add to PATH" |
| `pip: command not found` | pip 未随 Python 安装 | 运行 `python -m ensurepip --upgrade` |

遇到搞不定的问题？把错误信息复制给 Cursor 的 AI，它能帮你诊断。

### 2.3 包管理器：npm 与 pip

#### 什么是包管理器？

写代码时，你不需要所有功能都自己从头写。别人已经写好了很多现成的"代码包"（也叫库/依赖），你只需要安装就能使用。**包管理器**就是帮你安装、管理这些代码包的工具。

```
类比：
  包管理器 = 手机上的 App Store
  代码包   = App
  npm/pip  = 帮你下载、安装、更新、卸载这些 App
```

#### npm：JavaScript 的包管理器

npm 随 Node.js 一起安装，用于管理前端项目的依赖。

**常用命令：**

```bash
# 初始化一个新项目（会生成 package.json）
npm init -y

# 安装一个包（例如 axios，用于发 HTTP 请求）
npm install axios

# 安装开发依赖（只在开发时用，如代码检查工具）
npm install --save-dev eslint

# 根据 package.json 安装所有依赖（克隆别人项目后用）
npm install

# 运行项目的启动脚本
npm run dev

# 卸载一个包
npm uninstall axios
```

**核心文件说明：**

| 文件 | 作用 |
|---|---|
| `package.json` | 项目配置文件，记录了项目用了哪些包 |
| `node_modules/` | 存放所有已安装的包（自动生成，不要手动修改） |
| `package-lock.json` | 锁定包的精确版本号（自动生成） |

> ⚠️ `node_modules` 文件夹通常很大（几百 MB），**不要**提交到 Git 仓库。

#### pip：Python 的包管理器

pip 随 Python 一起安装，用于管理后端项目的依赖。

**常用命令：**

```bash
# 安装一个包（例如 fastapi）
pip install fastapi

# 安装指定版本
pip install fastapi==0.110.0

# 一次性安装多个包（从依赖清单文件）
pip install -r requirements.txt

# 查看已安装的包
pip list

# 导出当前环境的所有依赖到文件
pip freeze > requirements.txt

# 卸载一个包
pip uninstall fastapi
```

**核心文件说明：**

| 文件 | 作用 |
|---|---|
| `requirements.txt` | 依赖清单，记录项目需要哪些包（手动维护） |
| `venv/` | 虚拟环境文件夹（第 8 章会详细讲） |

#### npm vs pip 对照表

| | npm（JavaScript） | pip（Python） |
|---|---|---|
| **安装包** | `npm install axios` | `pip install requests` |
| **依赖文件** | `package.json` | `requirements.txt` |
| **安装全部依赖** | `npm install` | `pip install -r requirements.txt` |
| **运行项目** | `npm run dev` | `python app.py` |
| **包存放位置** | `node_modules/` | 系统全局或 `venv/` |

#### 本章小结

```
✅ 你已经掌握了：
  • 终端基础操作：cd、ls、mkdir、pwd 等核心命令
  • Node.js 和 Python 的安装与验证
  • npm 和 pip 的基本用法

🎯 下一章你将学习：
  • Git 版本管理——让你的代码有"后悔药"
```

---

## 3. Git 版本管理

写代码最怕什么？改坏了回不去。Git 就是你的代码"时光机"——每次修改都可以记录快照，随时回到过去的任何一个版本。它也是多人协作开发的基础工具，几乎所有开发者都在用。

---

### 3.1 为什么需要版本管理

#### 没有版本管理的痛苦

如果你写过毕业论文，你一定经历过这样的场景：

```
论文_初稿.docx
论文_修改版.docx
论文_修改版2.docx
论文_最终版.docx
论文_最终版_真的最终.docx
论文_打死不改版.docx
论文_导师又让改版.docx
```

写代码也是一样。如果没有版本管理：
- ❌ 改了一堆代码，发现改错了，回不去了
- ❌ 不敢大胆尝试新功能，怕把现有代码搞坏
- ❌ 多人同时修改同一个文件，互相覆盖
- ❌ 不知道什么时候引入了 Bug，无法定位

#### 有了 Git 之后

- ✅ 每次修改自动记录，一键回到任意历史版本
- ✅ 创建"分支"大胆实验，失败了直接删除，不影响主线
- ✅ 多人协作，各写各的，最后自动合并
- ✅ 每次提交都有记录，可以追溯任何一行代码的修改历史

---

### 3.2 Git 核心概念：仓库、暂存区、提交

Git 有三个核心概念，理解了它们就理解了 Git 的 80%：

#### 三个区域

```
┌─────────────┐    git add    ┌─────────────┐   git commit   ┌─────────────┐
│  工作区       │ ──────────→ │  暂存区       │ ──────────→  │  仓库         │
│ Working Dir  │             │ Staging Area │               │ Repository  │
│              │             │              │               │             │
│ 你正在编辑的  │             │ 准备好要提交的 │               │ 已保存的历史  │
│ 文件          │             │ 修改          │               │ 快照         │
└─────────────┘             └─────────────┘               └─────────────┘
```

**用快递类比：**

| Git 概念 | 快递类比 |
|---|---|
| **工作区** | 你的办公桌（正在修改文件的地方） |
| **暂存区** | 快递打包台（选好了要寄的东西，但还没发出） |
| **提交（Commit）** | 寄出快递（打包完成，记录在案，不可修改） |
| **仓库（Repository）** | 快递公司的仓库（所有历史包裹的记录） |

#### 工作流程

简单来说，Git 的日常工作流程就三步：

```
1. 修改文件（在工作区编辑代码）
2. git add（把修改放入暂存区："这些改动我确认要保存"）
3. git commit（提交到仓库："生成一个历史快照"）
```

每一次 `commit` 就像给代码拍了一张照片，你可以随时翻看、回到任何一张"照片"的状态。

#### Commit 是什么样的？

每个 Commit 包含以下信息：

```
commit 8a3b2f1e（唯一 ID，一串哈希值）
Author: 你的名字 <your@email.com>
Date:   2025-06-15 14:30:00

    feat: 添加用户登录功能    ← 你写的提交信息

    修改了以下文件：
    - src/auth.py（新增）
    - src/app.py（修改了 3 行）
```

> 💡 好的提交信息应该说清楚"改了什么"，而不是"改了代码"。

### 3.3 常用命令：init、add、commit、log、diff

#### 初始化仓库

```bash
# 在项目文件夹中初始化 Git 仓库
cd my-project
git init
# 输出：Initialized empty Git repository in /your/path/my-project/.git/
```

执行后，文件夹里会多出一个隐藏的 `.git` 目录——这就是 Git 的"数据库"，所有版本记录都存在这里。

#### 首次配置（只需做一次）

```bash
# 告诉 Git 你是谁（提交记录会显示这些信息）
git config --global user.name "你的名字"
git config --global user.email "your@email.com"
```

#### 日常三板斧：status → add → commit

**第一步：查看状态**

```bash
git status
```

这是你最常用的命令，它告诉你：哪些文件被修改了、哪些是新文件、哪些已经在暂存区。

```
输出示例：
  Changes not staged for commit:
    modified:   app.py          ← 修改了但还没 add

  Untracked files:
    utils.py                    ← 新文件，Git 还不知道它的存在
```

**第二步：添加到暂存区**

```bash
# 添加单个文件
git add app.py

# 添加所有修改过的文件（最常用）
git add .

# 添加某个文件夹下的所有文件
git add src/
```

**第三步：提交**

```bash
# 提交暂存区的所有内容，并写一条提交信息
git commit -m "feat: 添加用户注册功能"
```

**提交信息的写法建议：**

| 前缀 | 含义 | 示例 |
|---|---|---|
| `feat:` | 新功能 | `feat: 添加聊天界面` |
| `fix:` | 修复 Bug | `fix: 修复登录失败的问题` |
| `docs:` | 文档修改 | `docs: 更新 README` |
| `style:` | 样式调整 | `style: 调整按钮颜色` |
| `refactor:` | 重构代码 | `refactor: 简化数据处理逻辑` |

#### 查看历史记录

```bash
# 查看提交历史
git log

# 查看简洁版历史（推荐）
git log --oneline

# 输出示例：
# 8a3b2f1 feat: 添加用户注册功能
# 3c4d5e6 fix: 修复首页加载慢的问题
# 1a2b3c4 feat: 初始化项目
```

#### 查看修改内容

```bash
# 查看工作区和上次提交的差异
git diff

# 查看暂存区和上次提交的差异
git diff --staged
```

#### 撤销操作（后悔药）

```bash
# 撤销工作区的修改（还没 add 的文件，恢复到上次提交的状态）
git checkout -- app.py

# 把文件从暂存区移出（已经 add 但还没 commit）
git reset HEAD app.py

# 回到某个历史版本（谨慎使用）
git reset --hard 8a3b2f1
```

### 3.4 远程仓库：GitHub、push、pull、clone

到目前为止，你的 Git 仓库只存在于自己电脑上。**远程仓库**让你把代码同步到云端，这样可以备份代码、多设备同步、和别人协作。

#### Git vs GitHub

```
Git    = 版本管理工具（在你电脑上运行）
GitHub = 云端代码托管平台（存放远程仓库的网站）
```

类比：Git 是相机，GitHub 是相册云空间。你用 Git 拍照（commit），用 GitHub 上传到云端（push）。

#### 基本操作流程

```
本地仓库                      GitHub 远程仓库
┌─────────┐    git push     ┌─────────────────┐
│ 你的电脑  │ ──────────→   │ github.com/你/项目 │
│          │               │                  │
│          │ ←──────────   │                  │
└─────────┘    git pull     └─────────────────┘
```

#### 常用命令

```bash
# 1. 克隆别人的项目到本地（下载 + 自动初始化 Git）
git clone https://github.com/username/project.git

# 2. 关联远程仓库（本地已有项目时使用）
git remote add origin https://github.com/你/项目名.git

# 3. 推送代码到远程（把本地提交同步到 GitHub）
git push origin main

# 4. 拉取远程最新代码（把 GitHub 上的更新同步到本地）
git pull origin main
```

#### 第一次推送到 GitHub 的完整步骤

```bash
# 1. 在 GitHub 上创建一个新仓库（网页操作）
# 2. 在本地项目中执行：
git remote add origin https://github.com/你的用户名/你的仓库名.git
git branch -M main
git push -u origin main
# 之后每次推送只需要：git push
```

#### .gitignore：告诉 Git 忽略哪些文件

有些文件不应该提交到 GitHub（如密码、大文件、依赖包）：

```bash
# 创建 .gitignore 文件
touch .gitignore
```

常见的 .gitignore 内容：

```
# 依赖包（太大，不需要提交）
node_modules/
venv/
__pycache__/

# 环境变量（含密码、API Key）
.env

# 编辑器配置
.vscode/
.idea/

# 系统文件
.DS_Store
```

### 3.5 分支基础：branch、merge、解决冲突

分支是 Git 最强大的功能之一。它让你可以**在不影响主线代码的情况下，开发新功能或修复 Bug**。

#### 什么是分支？

```
main 分支（主线）：
  A ── B ── C ── D ── E      ← 稳定的代码

feature 分支（功能分支）：
                ├── F ── G    ← 你正在开发的新功能
                │
                （开发完成后合并回 main）
```

类比：`main` 是一本书的正式版，分支是你的草稿纸。你在草稿纸上随便写，写好了再合并到正式版。

#### 常用命令

```bash
# 查看所有分支（*号标记当前分支）
git branch

# 创建新分支
git branch feature-login

# 切换到新分支
git checkout feature-login
# 或者用新语法：
git switch feature-login

# 创建并切换（一步完成，最常用）
git checkout -b feature-login

# 合并分支（先切回 main，再把 feature 合进来）
git checkout main
git merge feature-login

# 删除已合并的分支（清理）
git branch -d feature-login
```

#### 实际开发中的分支流程

```
1. 要开发新功能 → 从 main 创建分支
   git checkout -b feature-chat

2. 在分支上写代码、提交
   git add .
   git commit -m "feat: 添加聊天界面"

3. 开发完成 → 切回 main → 合并
   git checkout main
   git merge feature-chat

4. 清理分支
   git branch -d feature-chat
```

#### 合并冲突

当两个分支修改了**同一个文件的同一行**，Git 无法自动合并，就会产生冲突：

```
<<<<<<< HEAD
这是 main 分支的内容
=======
这是 feature 分支的内容
>>>>>>> feature-login
```

**解决方法：**
1. 打开冲突文件，手动选择保留哪个版本（或合并两者）
2. 删除 `<<<<<<<`、`=======`、`>>>>>>>` 标记
3. `git add .` + `git commit` 完成合并

> 💡 在 Cursor 中，冲突文件会高亮显示，你可以点击按钮选择"保留当前"或"保留传入"，非常方便。

### 3.6 实战：用 Git 管理你的第一个项目

跟着下面的步骤，完整走一遍 Git 工作流：

```bash
# === 第一步：创建项目并初始化 Git ===
mkdir my-first-git-project
cd my-first-git-project
git init

# === 第二步：创建文件并提交 ===
echo "# 我的第一个 Git 项目" > README.md
git add .
git commit -m "feat: 初始化项目，添加 README"

# === 第三步：创建 .gitignore ===
echo "node_modules/" > .gitignore
echo ".env" >> .gitignore
git add .
git commit -m "chore: 添加 .gitignore"

# === 第四步：创建分支开发新功能 ===
git checkout -b feature-hello
echo "print('Hello, AI!')" > hello.py
git add .
git commit -m "feat: 添加 hello.py"

# === 第五步：合并回主分支 ===
git checkout main
git merge feature-hello
git branch -d feature-hello

# === 第六步：查看完整历史 ===
git log --oneline
# 输出类似：
# 3f2a1b0 feat: 添加 hello.py
# 8c7d6e5 chore: 添加 .gitignore
# 1a2b3c4 feat: 初始化项目，添加 README
```

恭喜！你已经完成了一个完整的 Git 工作流。

#### Git 命令速查表

```
初始化    git init
查看状态  git status
添加文件  git add .
提交      git commit -m "信息"
查看历史  git log --oneline
查看差异  git diff
创建分支  git checkout -b 分支名
切换分支  git checkout 分支名
合并分支  git merge 分支名
推送      git push origin main
拉取      git pull origin main
克隆      git clone 仓库地址
```

#### 本章小结

```
✅ 你已经掌握了：
  • 版本管理的意义：代码时光机 + 协作基础
  • Git 三个区域：工作区 → 暂存区 → 仓库
  • 日常三板斧：status → add → commit
  • 远程协作：push / pull / clone + GitHub
  • 分支开发：创建 → 开发 → 合并 → 清理

🎯 下一章你将学习：
  • HTML + CSS，开始构建用户看到的界面
```

---

## 4. HTML + CSS：搭建页面骨架

前面几章都在"幕后"操作——终端、Git、环境。从本章开始，你终于要做**用户能看到的东西**了。HTML 定义页面的内容和结构，CSS 定义页面的样式和布局。两者配合，就能构建出一个完整的网页界面。

---

### 4.1 HTML 核心：结构、表单、语义化标签

#### HTML 是什么？

HTML（HyperText Markup Language）是一种**标记语言**，用"标签"来描述网页的结构。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>我的第一个网页</title>
</head>
<body>
    <h1>Hello, AI 世界！</h1>
    <p>这是我的第一个网页。</p>
</body>
</html>
```

把这段代码保存为 `index.html`，用浏览器打开，你就看到一个网页了。

#### 核心标签速查

**文本类：**

| 标签 | 用途 | 示例 |
|---|---|---|
| `<h1>` ~ `<h6>` | 标题（h1 最大，h6 最小） | `<h1>大标题</h1>` |
| `<p>` | 段落 | `<p>一段文字</p>` |
| `<span>` | 行内文字（不换行） | `<span>高亮</span>` |
| `<a>` | 链接 | `<a href="https://...">点击</a>` |
| `<strong>` | 加粗 | `<strong>重要</strong>` |

**容器类：**

| 标签 | 用途 |
|---|---|
| `<div>` | 通用容器（最常用，用于布局分组） |
| `<header>` | 页面/区块的头部 |
| `<nav>` | 导航栏 |
| `<main>` | 页面主要内容 |
| `<footer>` | 页面/区块的底部 |
| `<section>` | 内容分区 |

**多媒体：**

| 标签 | 用途 | 示例 |
|---|---|---|
| `<img>` | 图片 | `<img src="photo.jpg" alt="描述">` |
| `<video>` | 视频 | `<video src="demo.mp4" controls>` |

**列表：**

```html
<!-- 无序列表 -->
<ul>
    <li>功能一</li>
    <li>功能二</li>
</ul>

<!-- 有序列表 -->
<ol>
    <li>第一步</li>
    <li>第二步</li>
</ol>
```

#### 表单：用户交互的核心

AI 应用中，用户通过表单和 AI 交互（输入框、按钮、文件上传）：

```html
<form>
    <!-- 文本输入框 -->
    <input type="text" placeholder="请输入你的问题...">
    
    <!-- 密码框 -->
    <input type="password" placeholder="请输入密码">
    
    <!-- 多行文本框 -->
    <textarea rows="4" placeholder="输入详细描述..."></textarea>
    
    <!-- 下拉选择 -->
    <select>
        <option value="gpt4">GPT-4</option>
        <option value="claude">Claude</option>
    </select>
    
    <!-- 文件上传 -->
    <input type="file" accept=".pdf,.txt">
    
    <!-- 提交按钮 -->
    <button type="submit">发送</button>
</form>
```

#### 语义化：为什么不全用 div？

```html
<!-- ❌ 全用 div，看不出结构 -->
<div>
    <div>导航</div>
    <div>内容</div>
    <div>底部</div>
</div>

<!-- ✅ 语义化标签，结构清晰 -->
<header>导航</header>
<main>内容</main>
<footer>底部</footer>
```

语义化的好处：代码更易读、搜索引擎更容易理解、对无障碍访问友好。

### 4.2 CSS 基础：盒模型、选择器、常用属性

#### CSS 是什么？

CSS（Cascading Style Sheets）控制网页的**视觉表现**——颜色、大小、位置、动画等。HTML 是骨架，CSS 是皮肤和衣服。

**三种使用方式：**

```html
<!-- 1. 行内样式（不推荐，难以维护） -->
<h1 style="color: blue;">标题</h1>

<!-- 2. 内部样式表 -->
<style>
    h1 { color: blue; }
</style>

<!-- 3. 外部样式表（推荐，本课程使用） -->
<link rel="stylesheet" href="style.css">
```

#### 选择器：选中你要装扮的元素

```css
/* 标签选择器：选中所有 <p> 标签 */
p { color: gray; }

/* 类选择器：选中 class="highlight" 的元素（最常用） */
.highlight { background-color: yellow; }

/* ID 选择器：选中 id="title" 的元素 */
#title { font-size: 24px; }

/* 后代选择器：选中 .card 里面的 p */
.card p { margin: 10px; }

/* 伪类：鼠标悬停时的样式 */
button:hover { background-color: #0056b3; }
```

#### 盒模型：每个元素都是一个"盒子"

这是 CSS 最重要的概念。每个 HTML 元素都由四层组成：

```
┌───────────────────────────────────┐
│            margin（外边距）         │
│  ┌─────────────────────────────┐  │
│  │       border（边框）          │  │
│  │  ┌───────────────────────┐  │  │
│  │  │    padding（内边距）     │  │  │
│  │  │  ┌─────────────────┐  │  │  │
│  │  │  │   content（内容）  │  │  │  │
│  │  │  │   你的文字/图片    │  │  │  │
│  │  │  └─────────────────┘  │  │  │
│  │  └───────────────────────┘  │  │
│  └─────────────────────────────┘  │
└───────────────────────────────────┘
```

```css
.card {
    width: 300px;          /* 内容区宽度 */
    padding: 20px;         /* 内边距：内容和边框之间的距离 */
    border: 1px solid #ddd; /* 边框 */
    margin: 16px;          /* 外边距：盒子和其他元素之间的距离 */
    
    /* 推荐：让 width 包含 padding 和 border */
    box-sizing: border-box;
}
```

#### 常用属性速查

**文字相关：**

```css
.text {
    color: #333;                /* 文字颜色 */
    font-size: 16px;            /* 字号 */
    font-weight: bold;          /* 粗细：normal / bold / 600 */
    line-height: 1.6;           /* 行高 */
    text-align: center;         /* 对齐：left / center / right */
    text-decoration: none;      /* 去掉下划线 */
}
```

**背景和边框：**

```css
.box {
    background-color: #f5f5f5;  /* 背景色 */
    border: 1px solid #ddd;     /* 边框 */
    border-radius: 8px;         /* 圆角 */
    box-shadow: 0 2px 8px rgba(0,0,0,0.1); /* 阴影 */
}
```

**尺寸和间距：**

```css
.container {
    width: 100%;       /* 宽度：像素 / 百分比 / auto */
    max-width: 800px;  /* 最大宽度 */
    height: auto;      /* 高度 */
    padding: 20px;     /* 内边距 */
    margin: 0 auto;    /* 外边距，0 auto = 水平居中 */
}
```

### 4.3 Flex 布局与响应式设计

传统 CSS 布局（float）非常痛苦。**Flexbox** 是现代 CSS 的布局神器，掌握它就能轻松实现各种布局。

#### Flex 布局核心

```css
/* 只需一行就能开启 Flex 布局 */
.container {
    display: flex;
}
```

开启后，容器内的子元素自动变成"弹性项目"，默认横向排列。

#### 关键属性

**容器（父元素）属性：**

```css
.container {
    display: flex;
    
    /* 排列方向 */
    flex-direction: row;        /* 横排（默认） */
    flex-direction: column;     /* 竖排 */
    
    /* 主轴对齐（横向如何分布） */
    justify-content: flex-start;   /* 靠左 */
    justify-content: center;       /* 居中 */
    justify-content: space-between; /* 两端对齐，中间等距 */
    
    /* 交叉轴对齐（纵向如何对齐） */
    align-items: center;        /* 垂直居中 */
    align-items: flex-start;    /* 靠上 */
    
    /* 换行 */
    flex-wrap: wrap;            /* 放不下时自动换行 */
    
    /* 子元素间距 */
    gap: 16px;                  /* 子元素之间的间距 */
}
```

#### 最常用的布局模式

**水平 + 垂直居中（面试高频题）：**

```css
.center-box {
    display: flex;
    justify-content: center;  /* 水平居中 */
    align-items: center;      /* 垂直居中 */
    height: 100vh;            /* 全屏高度 */
}
```

**导航栏布局（左 Logo，右菜单）：**

```css
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
}
```

**卡片网格布局：**

```css
.card-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}
.card {
    flex: 1 1 300px;  /* 最小 300px 宽，自动伸缩 */
}
```

#### 响应式设计：适配不同屏幕

用 **Media Query** 根据屏幕宽度应用不同的样式：

```css
/* 默认样式（移动端优先） */
.container {
    padding: 10px;
}

/* 屏幕宽度 >= 768px 时（平板） */
@media (min-width: 768px) {
    .container {
        padding: 20px;
        max-width: 720px;
    }
}

/* 屏幕宽度 >= 1024px 时（桌面） */
@media (min-width: 1024px) {
    .container {
        padding: 40px;
        max-width: 960px;
    }
}
```

**常用断点：**

| 断点 | 设备 |
|---|---|
| `< 768px` | 手机 |
| `768px ~ 1024px` | 平板 |
| `> 1024px` | 桌面电脑 |

### 4.4 实战：用 AI 辅助做一个 AI 产品落地页

现在把学到的 HTML + CSS 知识综合运用。我们要做一个**AI 产品的落地页**，而且会用 AI 编程工具来加速开发。

#### 目标效果

一个简洁的产品介绍页，包含：
- 顶部导航栏
- 主标题 + 副标题 + CTA 按钮
- 三个功能特性卡片
- 底部 Footer

#### Step 1：创建项目文件

```bash
mkdir ai-landing-page
cd ai-landing-page
touch index.html style.css
```

#### Step 2：用 AI 生成基础结构

在 Cursor 中打开 `index.html`，用 AI 对话生成：

```
帮我写一个 AI 聊天产品的落地页 HTML：
- 顶部导航栏（Logo + 导航链接）
- Hero 区域（大标题 + 副标题 + "开始使用" 按钮）
- 三个功能特性卡片（智能对话、知识库问答、多语言翻译）
- 底部 Footer
- 引入 style.css
```

#### Step 3：用 AI 生成样式

打开 `style.css`，继续用 AI：

```
帮我写这个落地页的 CSS：
- 使用 Flexbox 布局
- 现代风格，深色导航栏，白色背景
- Hero 区域居中，渐变背景
- 卡片有圆角和阴影
- 按钮有 hover 效果
- 响应式适配手机端
```

#### Step 4：迭代优化

用自然语言继续调整：

```
把 Hero 区域的背景改成从蓝色到紫色的渐变
卡片加上图标 emoji
按钮加一个 hover 时放大的动画效果
手机端卡片改成竖排
```

每一次修改，你都在加深对 HTML 和 CSS 的理解。AI 帮你写代码，你负责理解和审核。

#### 本章小结

```
✅ 你已经掌握了：
  • HTML 核心标签：文本、容器、表单、列表、多媒体
  • CSS 基础：选择器、盒模型、常用属性
  • Flex 布局：现代网页布局的核心方法
  • 响应式设计：Media Query 适配不同屏幕
  • AI 辅助前端开发：用自然语言生成和迭代页面

🎯 下一章你将学习：
  • JavaScript，让页面从"静态展示"变成"动态交互"
```

---

## 5. JavaScript 基础

HTML 是骨架，CSS 是皮肤，JavaScript 是**大脑和肌肉**——它让页面能"思考"和"行动"。点击按钮触发操作、表单验证、向后端发请求拿数据、实时更新页面内容……这些全靠 JavaScript。

---

### 5.1 变量、函数、条件、循环、数组、对象

#### 变量：存放数据的盒子

```javascript
// let：可以修改的变量（最常用）
let userName = "小明";
userName = "小红";  // ✅ 可以修改

// const：常量，声明后不能修改
const API_KEY = "sk-xxxxx";
// API_KEY = "new-key";  // ❌ 报错

// 数据类型
let name = "张三";       // 字符串（String）
let age = 25;            // 数字（Number）
let isStudent = true;    // 布尔值（Boolean）
let data = null;         // 空值
let result = undefined;  // 未定义
```

> 💡 用 `let` 和 `const` 就够了，不要用旧语法 `var`。

#### 函数：可复用的代码块

```javascript
// 普通函数
function greet(name) {
    return `你好，${name}！`;
}

// 箭头函数（更简洁，本课程推荐）
const greet = (name) => {
    return `你好，${name}！`;
};

// 单行箭头函数（省略 return）
const double = (n) => n * 2;

// 调用函数
console.log(greet("AI"));    // 输出：你好，AI！
console.log(double(5));      // 输出：10
```

#### 条件判断

```javascript
const score = 85;

if (score >= 90) {
    console.log("优秀");
} else if (score >= 60) {
    console.log("及格");
} else {
    console.log("不及格");
}

// 三元表达式（简洁写法）
const result = score >= 60 ? "及格" : "不及格";
```

#### 循环

```javascript
// for 循环
for (let i = 0; i < 5; i++) {
    console.log(`第 ${i + 1} 次`);
}

// 遍历数组（最常用）
const fruits = ["苹果", "香蕉", "橙子"];
fruits.forEach((fruit, index) => {
    console.log(`${index + 1}. ${fruit}`);
});
```

#### 数组：有序的数据集合

```javascript
const messages = ["你好", "今天天气怎么样", "谢谢"];

// 常用操作
messages.push("再见");           // 末尾添加
messages.length;                 // 长度：4
messages[0];                     // 取第一个："你好"

// 数组方法（非常重要，React 中大量使用）
const nums = [1, 2, 3, 4, 5];

// map：对每个元素执行操作，返回新数组
const doubled = nums.map(n => n * 2);       // [2, 4, 6, 8, 10]

// filter：过滤，保留满足条件的元素
const big = nums.filter(n => n > 3);        // [4, 5]

// find：找到第一个满足条件的元素
const found = nums.find(n => n === 3);      // 3
```

#### 对象：键值对的集合

```javascript
const user = {
    name: "张三",
    age: 25,
    role: "developer"
};

// 取值
console.log(user.name);       // "张三"
console.log(user["age"]);     // 25

// 解构赋值（从对象中快速取值，非常常用）
const { name, age } = user;
console.log(name);            // "张三"
```

---

### 5.2 DOM 操作：让页面"动起来"

DOM（Document Object Model）是 JavaScript 操作 HTML 页面的接口。通过 DOM，你可以用 JS 修改页面上的任何元素。

#### 获取元素

```javascript
// 通过 ID 获取（返回单个元素）
const title = document.getElementById("title");

// 通过选择器获取（最灵活，推荐）
const button = document.querySelector(".submit-btn");
const allCards = document.querySelectorAll(".card");
```

#### 修改内容和样式

```javascript
// 修改文字内容
title.textContent = "新标题";

// 修改 HTML 内容
title.innerHTML = "<strong>加粗标题</strong>";

// 修改样式
title.style.color = "blue";
title.style.fontSize = "24px";

// 添加 / 移除 CSS 类名（推荐方式）
button.classList.add("active");
button.classList.remove("hidden");
button.classList.toggle("selected");  // 有则移除，无则添加
```

#### 创建和插入元素

```javascript
// 创建新元素
const newMessage = document.createElement("div");
newMessage.textContent = "AI 的回复内容";
newMessage.classList.add("message", "ai-message");

// 插入到页面中
const chatBox = document.querySelector(".chat-box");
chatBox.appendChild(newMessage);  // 添加到末尾
```

> 💡 DOM 操作是理解 React 的基础。React 本质上是帮你更高效地管理 DOM，但底层原理是一样的。

### 5.3 事件处理与表单交互

用户和页面的一切交互都通过**事件**实现：点击、输入、提交、滚动……

#### 添加事件监听

```javascript
const button = document.querySelector("#send-btn");

// 点击事件
button.addEventListener("click", () => {
    console.log("按钮被点击了！");
});

// 常用事件类型
// click      - 点击
// input      - 输入框内容变化
// submit     - 表单提交
// keydown    - 按下键盘
// mouseover  - 鼠标悬停
// scroll     - 页面滚动
```

#### 获取输入框的值

```javascript
const input = document.querySelector("#user-input");

// 实时获取输入内容
input.addEventListener("input", (event) => {
    console.log("用户输入了：", event.target.value);
});

// 按回车时获取
input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        console.log("用户提交了：", input.value);
        input.value = "";  // 清空输入框
    }
});
```

#### 表单提交

```javascript
const form = document.querySelector("#chat-form");

form.addEventListener("submit", (event) => {
    event.preventDefault();  // ⚠️ 阻止默认刷新行为（非常重要）
    
    const input = document.querySelector("#message-input");
    const message = input.value.trim();
    
    if (message) {
        console.log("发送消息：", message);
        // 后续：调用后端 API 发送消息
        input.value = "";
    }
});
```

> ⚠️ `event.preventDefault()` 是关键——如果不加，表单提交时浏览器会刷新页面，你的 JS 逻辑就白跑了。

### 5.4 异步编程：回调 → Promise → async/await

这是 JavaScript 中最重要也是初学者最容易困惑的概念。但你必须理解它，因为**调用 AI API 就是异步操作**。

#### 为什么需要异步？

```javascript
// 假设调用 AI API 需要 3 秒
// ❌ 同步方式：页面冻住 3 秒，用户什么都干不了
const response = callAI("你好");  // 卡住 3 秒
console.log(response);

// ✅ 异步方式：发出请求后继续执行，等结果回来再处理
callAI("你好").then(response => {
    console.log(response);  // 3 秒后才执行
});
console.log("请求已发出，继续做别的");  // 立即执行
```

类比：同步 = 打电话等对方接（干等）；异步 = 发微信等对方回复（先做别的事）。

#### fetch：向后端发请求

`fetch` 是浏览器内置的请求函数，你会在 AI 应用中大量使用它：

```javascript
// GET 请求（获取数据）
fetch("https://api.example.com/data")
    .then(response => response.json())   // 把响应转为 JSON
    .then(data => console.log(data))     // 使用数据
    .catch(error => console.error(error)); // 处理错误
```

#### async/await：更优雅的异步写法

`.then` 链太长会很难读，`async/await` 让异步代码看起来像同步：

```javascript
// 用 async/await 改写（推荐，本课程统一使用）
const fetchData = async () => {
    try {
        const response = await fetch("https://api.example.com/data");
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error("请求失败：", error);
    }
};

fetchData();
```

**关键规则：**
- `await` 只能在 `async` 函数里使用
- `await` 会"等待"异步操作完成，再执行下一行
- 用 `try/catch` 处理错误

#### 实际场景：调用 AI API

```javascript
const askAI = async (question) => {
    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: question })
        });
        
        const data = await response.json();
        return data.reply;
    } catch (error) {
        console.error("AI 请求失败：", error);
        return "抱歉，出错了";
    }
};

// 使用
const reply = await askAI("今天天气怎么样？");
console.log("AI 说：", reply);
```

> 💡 记住这个模式：`fetch` + `await` + `try/catch`。后续课程中调用 LLM API、请求后端数据，都是这个套路。

### 5.5 实战：做一个带验证和交互的动态表单

综合运用本章知识，做一个**用户注册表单**——包含输入验证、实时反馈、动态交互。

#### 完整代码

**HTML（index.html）：**

```html
<form id="register-form">
    <div class="form-group">
        <label>用户名</label>
        <input type="text" id="username" placeholder="请输入用户名">
        <span class="error" id="username-error"></span>
    </div>
    <div class="form-group">
        <label>邮箱</label>
        <input type="email" id="email" placeholder="请输入邮箱">
        <span class="error" id="email-error"></span>
    </div>
    <div class="form-group">
        <label>密码</label>
        <input type="password" id="password" placeholder="至少 6 位">
        <span class="error" id="password-error"></span>
    </div>
    <button type="submit" id="submit-btn" disabled>注册</button>
</form>
<div id="result"></div>
```

**JavaScript（app.js）：**

```javascript
const form = document.querySelector("#register-form");
const usernameInput = document.querySelector("#username");
const emailInput = document.querySelector("#email");
const passwordInput = document.querySelector("#password");
const submitBtn = document.querySelector("#submit-btn");

// 实时验证：输入时检查
usernameInput.addEventListener("input", () => {
    const error = document.querySelector("#username-error");
    if (usernameInput.value.length < 2) {
        error.textContent = "用户名至少 2 个字符";
    } else {
        error.textContent = "";
    }
    checkFormValid();
});

emailInput.addEventListener("input", () => {
    const error = document.querySelector("#email-error");
    if (!emailInput.value.includes("@")) {
        error.textContent = "请输入有效的邮箱";
    } else {
        error.textContent = "";
    }
    checkFormValid();
});

passwordInput.addEventListener("input", () => {
    const error = document.querySelector("#password-error");
    if (passwordInput.value.length < 6) {
        error.textContent = "密码至少 6 位";
    } else {
        error.textContent = "";
    }
    checkFormValid();
});

// 检查表单是否完整，控制按钮状态
const checkFormValid = () => {
    const isValid = usernameInput.value.length >= 2
        && emailInput.value.includes("@")
        && passwordInput.value.length >= 6;
    submitBtn.disabled = !isValid;
};

// 提交表单
form.addEventListener("submit", async (event) => {
    event.preventDefault();
    
    const result = document.querySelector("#result");
    result.textContent = "注册中...";
    
    // 模拟调用后端 API（后续课程会换成真实接口）
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    result.textContent = `✅ 注册成功！欢迎，${usernameInput.value}`;
    form.reset();
    submitBtn.disabled = true;
});
```

这个实战综合运用了：变量、函数、条件判断、DOM 操作、事件监听、异步等所有本章知识点。

#### 本章小结

```
✅ 你已经掌握了：
  • JS 核心语法：变量、函数、条件、循环、数组、对象
  • DOM 操作：获取元素、修改内容/样式、创建元素
  • 事件处理：click、input、submit、preventDefault
  • 异步编程：fetch + async/await + try/catch
  • 综合实战：带验证的动态表单

🎯 下一章你将学习：
  • React 框架——用组件化思维高效构建复杂界面
```

---

## 6. React 框架入门

上一章你用原生 JS 操作 DOM——手动获取元素、手动修改内容、手动管理状态。当页面变复杂时，这种方式会变得极其痛苦。**React** 的核心思想是：你只需要描述"界面应该长什么样"，React 自动帮你更新 DOM。

---

### 6.1 为什么需要框架：组件化思维

#### 原生 JS 的痛苦

假设你要做一个聊天界面，有 100 条消息。每来一条新消息，你需要：

```javascript
// 原生 JS：手动操作 DOM，代码又臭又长
const div = document.createElement("div");
div.classList.add("message");
div.innerHTML = `<span class="name">${name}</span><p>${text}</p>`;
chatBox.appendChild(div);
// 还要处理滚动、更新计数、管理状态......
```

当界面变复杂，你会陷入"DOM 操作地狱"——到处都是 `querySelector` 和 `innerHTML`，可读性和可维护性极差。

#### React 的思路：组件化

React 把界面拆成一个个**组件**（Component），每个组件是一个独立、可复用的"UI 积木"：

```
聊天界面
├── ChatHeader（顶部栏）
├── MessageList（消息列表）
│   ├── Message（单条消息）
│   ├── Message
│   └── Message
└── ChatInput（输入框 + 发送按钮）
```

每个组件只关心自己的事情，互不干扰，可以独立开发和复用。

---

### 6.2 JSX、组件、Props 与 State

#### JSX：在 JS 里写 HTML

React 用一种叫 **JSX** 的语法，让你在 JavaScript 里直接写 HTML：

```jsx
// 这不是字符串，是 JSX！
const element = <h1>Hello, React!</h1>;

// 可以嵌入 JS 表达式（用花括号 {}）
const name = "AI 助手";
const greeting = <h1>你好，{name}！</h1>;

// 可以嵌套
const card = (
    <div className="card">
        <h2>{name}</h2>
        <p>欢迎使用</p>
    </div>
);
```

> 注意：JSX 中用 `className` 代替 HTML 的 `class`（因为 `class` 是 JS 关键字）。

#### 函数组件：React 组件就是函数

```jsx
// 最简单的组件：一个返回 JSX 的函数
function Welcome() {
    return <h1>欢迎来到 AI 世界</h1>;
}

// 箭头函数写法（推荐）
const Welcome = () => {
    return <h1>欢迎来到 AI 世界</h1>;
};

// 使用组件（像 HTML 标签一样使用）
<Welcome />
```

#### Props：从外部传入数据

Props 是组件的"输入参数"，让组件可以复用：

```jsx
// 定义：接收 props
const Message = ({ sender, text }) => {
    return (
        <div className="message">
            <strong>{sender}</strong>
            <p>{text}</p>
        </div>
    );
};

// 使用：传入不同的 props，渲染不同的内容
<Message sender="用户" text="今天天气怎么样？" />
<Message sender="AI" text="今天北京晴，25°C，适合出行。" />
```

#### State：组件内部的"记忆"

State 是组件自己的数据，当 State 变化时，React 自动重新渲染界面：

```jsx
import { useState } from "react";

const Counter = () => {
    // useState 返回 [当前值, 修改函数]
    const [count, setCount] = useState(0);
    
    return (
        <div>
            <p>你点击了 {count} 次</p>
            <button onClick={() => setCount(count + 1)}>
                点击 +1
            </button>
        </div>
    );
};
```

**关键理解：**
- `count` 是当前状态值
- `setCount` 是修改状态的函数
- 调用 `setCount` 后，React **自动重新渲染**组件——你不需要手动操作 DOM！

#### Props vs State 对比

| | Props | State |
|---|---|---|
| **来源** | 父组件传入 | 组件自己管理 |
| **可修改** | ❌ 只读 | ✅ 通过 setState 修改 |
| **用途** | 配置组件的显示内容 | 管理组件的交互状态 |
| **类比** | 函数的参数 | 函数内部的变量 |

### 6.3 常用 Hooks：useState、useEffect

Hooks 是 React 的核心 API，让函数组件拥有状态和副作用能力。你只需要掌握两个就够应付 90% 的场景。

#### useState 进阶用法

```jsx
// 管理多个状态
const ChatInput = () => {
    const [message, setMessage] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    
    const handleSend = async () => {
        setIsLoading(true);           // 开始加载
        await sendToAPI(message);     // 调用后端
        setMessage("");               // 清空输入
        setIsLoading(false);          // 结束加载
    };
    
    return (
        <div>
            <input 
                value={message} 
                onChange={(e) => setMessage(e.target.value)}
                disabled={isLoading}
            />
            <button onClick={handleSend} disabled={isLoading}>
                {isLoading ? "发送中..." : "发送"}
            </button>
        </div>
    );
};
```

#### useEffect：处理"副作用"

组件渲染之外的操作叫"副作用"：请求数据、设置定时器、操作 DOM 等。

```jsx
import { useState, useEffect } from "react";

const UserProfile = ({ userId }) => {
    const [user, setUser] = useState(null);
    
    // 组件加载时请求数据
    useEffect(() => {
        const fetchUser = async () => {
            const res = await fetch(`/api/users/${userId}`);
            const data = await res.json();
            setUser(data);
        };
        fetchUser();
    }, [userId]);  // 依赖数组：userId 变化时重新执行
    
    if (!user) return <p>加载中...</p>;
    return <p>用户名：{user.name}</p>;
};
```

**依赖数组的三种情况：**

```jsx
// 1. 空数组 []：只在组件首次加载时执行一次
useEffect(() => { fetchData(); }, []);

// 2. 有依赖 [userId]：依赖变化时重新执行
useEffect(() => { fetchUser(userId); }, [userId]);

// 3. 不传数组：每次渲染都执行（少用）
useEffect(() => { console.log("每次渲染都执行"); });
```

> 💡 记住：`useState` 管数据，`useEffect` 管副作用。其他 Hooks 后面遇到再学。

### 6.4 条件渲染、列表渲染、事件处理

这三个技巧在 React 开发中无处不在。

#### 条件渲染：根据状态显示不同内容

```jsx
const ChatMessage = ({ isLoading, reply }) => {
    // 方式 1：三元表达式（最常用）
    return (
        <div>
            {isLoading ? <p>AI 思考中...</p> : <p>{reply}</p>}
        </div>
    );
};

// 方式 2：&& 短路（只有条件为 true 才渲染）
const Notification = ({ count }) => {
    return (
        <div>
            {count > 0 && <span className="badge">{count}</span>}
        </div>
    );
};
```

#### 列表渲染：用 map 把数组变成组件列表

```jsx
const MessageList = ({ messages }) => {
    return (
        <div className="message-list">
            {messages.map((msg, index) => (
                <div key={index} className={`message ${msg.role}`}>
                    <strong>{msg.role === "user" ? "你" : "AI"}</strong>
                    <p>{msg.content}</p>
                </div>
            ))}
        </div>
    );
};

// 使用
const messages = [
    { role: "user", content: "你好" },
    { role: "ai", content: "你好！有什么可以帮你的？" },
];
<MessageList messages={messages} />
```

> ⚠️ 列表渲染必须给每个元素加 `key` 属性，React 用它来高效更新 DOM。

#### 事件处理：React 中的写法

```jsx
const ChatInput = () => {
    const [input, setInput] = useState("");
    
    // 事件处理函数
    const handleSubmit = (e) => {
        e.preventDefault();
        if (input.trim()) {
            console.log("发送：", input);
            setInput("");
        }
    };
    
    return (
        <form onSubmit={handleSubmit}>
            <input 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="输入消息..."
            />
            <button type="submit">发送</button>
        </form>
    );
};
```

**React 事件 vs 原生事件对比：**

| | 原生 JS | React |
|---|---|---|
| 绑定方式 | `addEventListener` | `onClick={handler}` |
| 事件名 | `onclick`（小写） | `onClick`（驼峰） |
| 阻止默认 | `event.preventDefault()` | 同样 `e.preventDefault()` |

### 6.5 实战：用 React 做一个聊天气泡界面

综合本章所有知识，做一个最贴近 AI 应用的组件——**聊天界面**。

#### 完整代码：App.jsx

```jsx
import { useState } from "react";

// 单条消息组件
const Message = ({ role, content }) => (
    <div className={`message ${role}`}>
        <div className="avatar">{role === "user" ? "👤" : "🤖"}</div>
        <div className="bubble">
            <p>{content}</p>
        </div>
    </div>
);

// 主应用
const App = () => {
    const [messages, setMessages] = useState([
        { role: "ai", content: "你好！我是 AI 助手，有什么可以帮你的？" }
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    
    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;
        
        // 1. 添加用户消息
        const userMsg = { role: "user", content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        
        // 2. 模拟 AI 回复（后续替换为真实 API）
        setIsLoading(true);
        await new Promise(r => setTimeout(r, 1000));
        const aiMsg = { role: "ai", content: `你说的是："${input}"，我记住了！` };
        setMessages(prev => [...prev, aiMsg]);
        setIsLoading(false);
    };
    
    return (
        <div className="chat-container">
            <header className="chat-header">
                <h1>🤖 AI 聊天助手</h1>
            </header>
            
            <div className="message-list">
                {messages.map((msg, i) => (
                    <Message key={i} role={msg.role} content={msg.content} />
                ))}
                {isLoading && <Message role="ai" content="思考中..." />}
            </div>
            
            <form className="chat-input" onSubmit={handleSend}>
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="输入你的问题..."
                    disabled={isLoading}
                />
                <button type="submit" disabled={isLoading || !input.trim()}>
                    发送
                </button>
            </form>
        </div>
    );
};

export default App;
```

这个组件用到了本章所有知识点：
- ✅ 组件拆分（`Message` + `App`）
- ✅ Props（`role`、`content`）
- ✅ State（`messages`、`input`、`isLoading`）
- ✅ useEffect（后续章节会加上数据请求）
- ✅ 条件渲染（`isLoading && ...`）
- ✅ 列表渲染（`messages.map()`）
- ✅ 事件处理（`onSubmit`、`onChange`）

#### 本章小结

```
✅ 你已经掌握了：
  • 组件化思维：把界面拆成独立、可复用的组件
  • JSX：在 JS 里写 HTML
  • Props：从外部传入数据
  • State：组件内部的响应式数据
  • Hooks：useState 管状态，useEffect 管副作用
  • 条件渲染、列表渲染、事件处理

🎯 下一章你将学习：
  • 前端工程化——用 Vite 搭建真实项目，组织组件和路由
```

---

## 7. 前端工程化

前面你学了 HTML/CSS/JS/React 的基础语法，但真实项目不是一个文件就能搞定的。你需要**项目脚手架**帮你管理编译、热更新、依赖；需要**合理的文件结构**组织几十个组件；需要**路由**让应用有多个页面。这就是前端工程化。

---

### 7.1 Vite 项目搭建与配置

Vite 是当前最流行的前端构建工具，由 Vue 的作者尤雨溪开发，React 项目同样适用。

#### 创建项目

```bash
# 用 Vite 创建一个 React 项目
npm create vite@latest my-ai-app -- --template react

# 进入项目并安装依赖
cd my-ai-app
npm install

# 启动开发服务器
npm run dev
# 浏览器打开 http://localhost:5173 即可看到页面
```

#### 项目文件结构

创建完成后，你会看到这样的目录：

```
my-ai-app/
├── index.html          ← 入口 HTML（只有一个）
├── package.json        ← 项目配置和依赖清单
├── vite.config.js      ← Vite 配置文件
├── public/             ← 静态资源（图标、图片等）
└── src/                ← 源代码（你的代码都在这里）
    ├── main.jsx        ← JS 入口，挂载 React 根组件
    ├── App.jsx         ← 根组件
    ├── App.css         ← 根组件样式
    └── index.css       ← 全局样式
```

#### Vite 的开发体验

- ⚡ **秒级启动**：不需要等几十秒编译
- 🔥 **热更新（HMR）**：修改代码后浏览器自动刷新，不丢失状态
- 📦 **一键打包**：`npm run build` 生成可部署的生产版本

---

### 7.2 组件拆分与项目结构规范

当项目变大后，所有代码塞在一个文件里是灾难。需要按功能拆分组件和文件。

#### 推荐的项目结构

```
src/
├── components/          ← 通用可复用组件
│   ├── Button.jsx
│   ├── Loading.jsx
│   └── Navbar.jsx
├── pages/               ← 页面级组件（每个路由对应一个）
│   ├── HomePage.jsx
│   ├── ChatPage.jsx
│   └── SettingsPage.jsx
├── services/            ← API 请求封装
│   └── api.js
├── hooks/               ← 自定义 Hooks
│   └── useChat.js
├── styles/              ← 样式文件
│   └── global.css
├── App.jsx              ← 根组件（组装路由和布局）
└── main.jsx             ← 入口文件
```

#### 组件拆分原则

```
❌ 一个文件 500 行，什么都塞在里面

✅ 按职责拆分：
  • 一个组件只做一件事
  • 超过 100 行就考虑拆分
  • 被多个地方使用的组件放到 components/
  • 只在一个页面用的组件放到该页面旁边
```

#### 组件导入导出

```jsx
// components/Message.jsx
const Message = ({ role, content }) => (
    <div className={`message ${role}`}>{content}</div>
);
export default Message;

// pages/ChatPage.jsx
import Message from "../components/Message";

const ChatPage = () => (
    <div>
        <Message role="user" content="你好" />
    </div>
);
export default ChatPage;
```

### 7.3 样式方案：CSS Modules 与 Tailwind CSS

React 项目有多种管理样式的方式，各有优缺点。

#### 方案对比

| 方案 | 原理 | 优点 | 缺点 |
|---|---|---|---|
| 普通 CSS | 全局样式文件 | 简单直接 | 容易类名冲突 |
| **CSS Modules** | 每个组件独立样式文件，自动加作用域 | 无冲突，结构清晰 | 文件较多 |
| **Tailwind CSS** | 用预定义的工具类直接写在 HTML 中 | 速度快，不用写 CSS | 标签较长 |

#### CSS Modules（推荐新手使用）

```css
/* Message.module.css */
.message {
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
}
.user {
    background-color: #e3f2fd;
    margin-left: auto;
}
.ai {
    background-color: #f5f5f5;
}
```

```jsx
// Message.jsx
import styles from "./Message.module.css";

const Message = ({ role, content }) => (
    <div className={`${styles.message} ${styles[role]}`}>
        {content}
    </div>
);
```

CSS Modules 自动给类名加后缀（如 `message_abc123`），**彻底避免类名冲突**。

#### Tailwind CSS（适合快速开发）

```jsx
// 不需要写 CSS 文件，样式直接写在 className 中
const Message = ({ role, content }) => (
    <div className={`p-3 rounded-lg mb-2 ${
        role === "user" ? "bg-blue-100 ml-auto" : "bg-gray-100"
    }`}>
        {content}
    </div>
);
```

> 💡 本课程优先使用 CSS Modules（更容易理解），Tailwind CSS 作为选修专题。

### 7.4 路由管理：React Router

React 默认是**单页应用（SPA）**——只有一个 HTML 页面。React Router 让你在一个页面中模拟多页面导航。

#### 安装

```bash
npm install react-router-dom
```

#### 基本用法

```jsx
// App.jsx
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import HomePage from "./pages/HomePage";
import ChatPage from "./pages/ChatPage";
import SettingsPage from "./pages/SettingsPage";

const App = () => (
    <BrowserRouter>
        {/* 导航栏 */}
        <nav>
            <Link to="/">首页</Link>
            <Link to="/chat">聊天</Link>
            <Link to="/settings">设置</Link>
        </nav>
        
        {/* 路由配置：URL 对应的页面 */}
        <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/settings" element={<SettingsPage />} />
        </Routes>
    </BrowserRouter>
);
```

**核心概念：**

| 组件 | 作用 |
|---|---|
| `<BrowserRouter>` | 包裹整个应用，启用路由功能 |
| `<Routes>` | 路由容器，根据 URL 匹配对应页面 |
| `<Route>` | 定义一条路由规则（URL → 组件） |
| `<Link>` | 导航链接（替代 `<a>` 标签，不刷新页面） |

#### 编程式导航

```jsx
import { useNavigate } from "react-router-dom";

const LoginButton = () => {
    const navigate = useNavigate();
    
    const handleLogin = async () => {
        await login();
        navigate("/chat");  // 登录成功后跳转到聊天页
    };
    
    return <button onClick={handleLogin}>登录</button>;
};
```

### 7.5 实战：把聊天界面升级为多页面应用

把第 6 章的聊天界面升级为一个完整的 Vite + React Router 项目。

#### 项目结构

```
my-ai-app/
└── src/
    ├── components/
    │   ├── Navbar.jsx           ← 导航栏
    │   ├── Message.jsx          ← 消息气泡
    │   └── ChatInput.jsx        ← 输入框组件
    ├── pages/
    │   ├── HomePage.jsx         ← 首页（产品介绍）
    │   └── ChatPage.jsx         ← 聊天页（AI 对话）
    ├── styles/
    │   ├── global.css
    │   └── ChatPage.module.css
    ├── App.jsx                  ← 路由配置
    └── main.jsx
```

#### 核心文件

```jsx
// App.jsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import HomePage from "./pages/HomePage";
import ChatPage from "./pages/ChatPage";

const App = () => (
    <BrowserRouter>
        <Navbar />
        <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/chat" element={<ChatPage />} />
        </Routes>
    </BrowserRouter>
);

export default App;
```

现在你拥有了一个具备多页面导航的前端应用。后续章节会给 ChatPage 接入真实的后端 API 和 LLM 能力。

#### 本章小结

```
✅ 你已经掌握了：
  • Vite：秒级启动的现代构建工具
  • 项目结构：components / pages / services 分层组织
  • CSS Modules：组件级样式，无冲突
  • React Router：多页面导航和编程式跳转

🎯 下一章你将学习：
  • Python 基础——为后端开发做准备
```

---

## 8. Python 基础

前面 4 章你学了前端（HTML/CSS/JS/React），现在切换到后端。到这里，你已经具备了**完整的前端技能栈**——能做页面、写交互、建组件、配路由。但前端只是全栈的“一半”，现在开始学另一半——**后端开发**。

Python 是 AI 应用后端的首选语言——语法简洁、生态丰富、AI 库最多。如果你已经学过了 JavaScript，Python 会很容易上手，因为很多概念是相通的。

---

### 8.1 变量、函数、列表、字典、条件与循环

#### Python vs JavaScript 对照表

你已经学过 JS，看对照表就能快速上手 Python：

| 概念 | JavaScript | Python |
|---|---|---|
| 变量 | `let name = "AI"` | `name = "AI"` |
| 常量 | `const PI = 3.14` | `PI = 3.14`（约定大写） |
| 字符串格式化 | `` `Hello, ${name}` `` | `f"Hello, {name}"` |
| 数组/列表 | `[1, 2, 3]` | `[1, 2, 3]` |
| 对象/字典 | `{name: "AI", age: 1}` | `{"name": "AI", "age": 1}` |
| 函数 | `const fn = () => {}` | `def fn():` |
| 条件 | `if (x > 0) {}` | `if x > 0:` |
| 循环 | `for (let i of arr) {}` | `for i in arr:` |
| 打印 | `console.log()` | `print()` |
| 空值 | `null` | `None` |
| 布尔 | `true / false` | `True / False` |

> ⚠️ **从 JS 切到 Python 最容易踩的坑：**

| 坑 | 详细说明 |
|---|---|
| **缩进决定代码块** | Python 用空格缩进代替 JS 的 `{}`。缩进错一格就报错 `IndentationError`。统一用 **4 个空格**，不要混用 Tab |
| **没有分号** | Python **不写分号**。写了不报错但是多余的 |
| **布尔值大写** | `True / False / None`，不是 `true / false / null` |
| **相等判断** | Python 只用 `==`，没有 `===` |
| **决不要写 `{}`** | `if x > 0:` 后面用缩进，不用大括号 |

```python
# ❗ 缩进错误是新手第一大报错来源
def greet():
    print("你好")   # ✅ 4 个空格缩进
  print("再见")     # ❌ 只有 2 个空格，报 IndentationError!
```

> 💡 **Cursor 会自动处理缩进**，但手动编辑时要特别注意。见到 `IndentationError` 就检查空格数量。

#### 变量与数据类型

```python
# Python 不需要 let/const，直接赋值
name = "张三"
age = 25
score = 95.5
is_student = True
data = None

# 字符串格式化（f-string，类似 JS 的模板字符串）
greeting = f"你好，{name}，你今年 {age} 岁"
print(greeting)
```

#### 函数

```python
# 定义函数（用 def，不用花括号，用缩进）
def greet(name, greeting="你好"):
    return f"{greeting}，{name}！"

# 调用
print(greet("AI"))              # 你好，AI！
print(greet("AI", "Hello"))     # Hello，AI！
```

> ⚠️ Python 用**缩进**代替花括号 `{}` 来表示代码块。缩进错了程序会报错。

#### 列表（对应 JS 的数组）

```python
fruits = ["苹果", "香蕉", "橙子"]

fruits.append("西瓜")       # 末尾添加
fruits[0]                    # 取第一个："苹果"
len(fruits)                  # 长度：4

# 列表推导式（Python 的高效写法，对应 JS 的 map）
nums = [1, 2, 3, 4, 5]
doubled = [n * 2 for n in nums]           # [2, 4, 6, 8, 10]
big = [n for n in nums if n > 3]           # [4, 5]
```

#### 字典（对应 JS 的对象）

```python
user = {
    "name": "张三",
    "age": 25,
    "role": "developer"
}

# 取值
user["name"]                 # "张三"
user.get("email", "未设置")   # 不存在时返回默认值

# 遍历
for key, value in user.items():
    print(f"{key}: {value}")
```

#### 条件与循环

```python
# 条件
score = 85
if score >= 90:
    print("优秀")
elif score >= 60:
    print("及格")
else:
    print("不及格")

# for 循环
for i in range(5):
    print(f"第 {i + 1} 次")

# 遍历列表
for fruit in ["苹果", "香蕉", "橙子"]:
    print(fruit)
```

---

### 8.2 进阶语法：类型注解、装饰器与生成器

这一节介绍三个 Python 进阶语法。它们在基础脚本中不常见，但在 **FastAPI 后端开发中是核心基础**——不理解它们，下一章你会看不懂。

#### 类型注解（Type Hints）

Python 是动态类型语言——变量不需要声明类型。但从 Python 3.5 开始，你可以给变量和函数**加上类型标注**：

```python
# 不加类型注解（能跑，但不清楚参数应该传什么）
def greet(name):
    return f"你好，{name}"

# 加上类型注解（一目了然：name 是 str，返回值也是 str）
def greet(name: str) -> str:
    return f"你好，{name}"
```

**语法规则：**

```python
# 变量类型注解
name: str = "张三"
age: int = 25
score: float = 95.5
is_student: bool = True

# 函数参数和返回值
def add(a: int, b: int) -> int:
    return a + b

def get_user(user_id: int) -> dict:
    return {"id": user_id, "name": "张三"}

# 容器类型（list/dict 里面装什么）
names: list[str] = ["张三", "李四"]
scores: dict[str, int] = {"张三": 95, "李四": 88}

# 可选参数
def search(keyword: str, limit: int = 10) -> list[dict]:
    ...
```

> ⚠️ **类型注解不影响运行**。就算你标了 `name: int` 然后传了字符串，Python 也不会报错。类型注解的价值是：让代码更清晰、IDE 自动补全更智能、搭配 Pydantic 可以**自动校验**。

**对照 JavaScript/TypeScript：**

| Python | TypeScript | 说明 |
|---|---|---|
| `name: str` | `name: string` | 变量类型 |
| `def fn(x: int) -> str:` | `function fn(x: number): string` | 函数签名 |
| `list[int]` | `number[]` | 列表/数组 |
| `dict[str, int]` | `Record<string, number>` | 字典/对象 |

#### 装饰器（Decorator）

下一章你会大量看到这种写法：

```python
@app.get("/users")
def get_users():
    return [{"name": "张三"}]
```

**这个 `@` 是什么？** 它叫**装饰器**——给函数"包一层"，在不修改原函数的情况下增加额外功能。

**用类比理解：**

```
装饰器 = 给手机套一个保护壳

手机（原函数）：打电话、发短信
保护壳（装饰器）：不改变手机功能，但增加了防摔保护

@防摔壳
def 手机():
    打电话()
```

**一个简单的装饰器示例：**

```python
import time

def timer(func):
    """计时装饰器：测量函数执行时间"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)  # 执行原函数
        end = time.time()
        print(f"{func.__name__} 耗时 {end - start:.2f} 秒")
        return result
    return wrapper

# 使用装饰器
@timer
def slow_function():
    time.sleep(1)
    print("执行完毕")

slow_function()
# 输出：
# 执行完毕
# slow_function 耗时 1.00 秒
```

**`@timer` 实际上等于：**

```python
# 这两种写法完全等价
@timer
def slow_function():
    ...

# 等价于：
def slow_function():
    ...
slow_function = timer(slow_function)  # 用 timer "包装" 了原函数
```

**在 FastAPI 中的含义：**

```python
@app.get("/users")      # "当有人 GET 访问 /users 时，执行下面这个函数"
def get_users():
    return [...]

@app.post("/chat")       # "当有人 POST 访问 /chat 时，执行下面这个函数"
def chat(request):
    return {...}
```

> 💡 你不需要自己写装饰器，只需要**会用** `@xxx` 语法。理解了"装饰器 = 给函数加功能"这个概念，下一章的 `@app.get()` 就不会再困惑了。

#### 生成器与 `yield`

Python 函数用 `return` 返回结果，**一次性返回，函数结束**。但有时候你需要函数**一点一点地返回数据**——这就是 `yield` 的用途。

```python
# return：一次性返回全部，函数结束
def get_numbers_return():
    return [1, 2, 3, 4, 5]

# yield：每次返回一个，函数"暂停"，等你要下一个时继续
def get_numbers_yield():
    yield 1    # 返回 1，暂停
    yield 2    # 返回 2，暂停
    yield 3    # 返回 3，暂停

# 用 for 循环消费生成器
for n in get_numbers_yield():
    print(n)   # 依次打印 1, 2, 3
```

**`return` vs `yield` 的类比：**

```
return = 一次性把整本书给你（占内存）
yield  = 翻一页给你看一页（省内存）
```

**为什么后端需要 `yield`？两个核心场景：**

```python
# 场景 1：数据库连接管理（第 10 章会用）
def get_db():
    db = connect_database()    # 创建连接
    try:
        yield db               # 把连接"借"给接口函数使用
    finally:
        db.close()             # 接口函数用完后，自动关闭连接

# 场景 2：流式输出（第 12 章会用）
def generate_stream():
    for word in ["你", "好", "世", "界"]:
        yield f"data: {word}\n\n"    # 一个字一个字地发送给前端
```

> 💡 记住两个规则：① 函数里有 `yield` 就变成了"生成器函数"；② 用 `for` 循环或 `next()` 来消费生成器。

#### 字典解包 `**kwargs`

Python 用 `**` 可以把字典"展开"成关键字参数：

```python
user_data = {"name": "张三", "age": 25, "role": "admin"}

# 不用解包：手动一个一个传
User(name=user_data["name"], age=user_data["age"], role=user_data["role"])

# 用 ** 解包：一行搞定
User(**user_data)
# 等价于 User(name="张三", age=25, role="admin")
```

这在后续章节中很常见：

```python
# FastAPI + Pydantic 中的典型用法
new_todo = Todo(id=next_id, **todo.model_dump())
# model_dump() 返回字典 {"title": "学习", "done": false}
# ** 展开后等价于 Todo(id=next_id, title="学习", done=False)
```

#### Python 异步编程速览

你在第 5 章学了 JS 的 `async/await`，Python 也有完全对应的语法：

```python
import asyncio

# JS 写法回顾：
# const fetchData = async () => {
#     const data = await fetch(url);
#     return data;
# };

# Python 对应写法：
async def fetch_data():
    data = await some_async_operation()
    return data
```

**Python vs JS 异步对照：**

| JavaScript | Python | 说明 |
|---|---|---|
| `async function fn()` | `async def fn():` | 定义异步函数 |
| `await promise` | `await coroutine` | 等待异步操作完成 |
| `Promise` | `Coroutine` | 异步对象类型 |

**在 FastAPI 中的使用：**

```python
# 同步接口（简单场景用这个就行）
@app.get("/users")
def get_users():
    return [...]

# 异步接口（需要 await 时用这个）
@app.post("/chat")
async def chat(request: ChatRequest):
    result = await some_async_api_call()
    return {"reply": result}
```

> 💡 FastAPI 同时支持 `def` 和 `async def`。简单场景用普通 `def` 就够了，需要调用异步库（如 `httpx`、`aiohttp`）时用 `async def`。不需要深入学 asyncio 事件循环。

#### 错误处理：try/except

程序运行时可能出错（文件不存在、网络超时、数据格式错误）。`try/except` 让你能“捕捉”错误，而不是让程序崩溃：

```python
# 基本用法（和 JS 的 try/catch 完全对应）
try:
    result = 10 / 0                # 可能出错的代码
except ZeroDivisionError:
    print("不能除以 0！")            # 出错时执行

# 捕捉多种错误
try:
    data = json.loads('{invalid}')
except json.JSONDecodeError:
    print("JSON 格式错误")
except Exception as e:             # 捕捉所有其他错误
    print(f"未知错误：{e}")

# try/except/finally
try:
    f = open("config.json")
    data = json.load(f)
except FileNotFoundError:
    print("文件不存在")
finally:
    print("无论成功失败都执行")    # 清理代码
```

**主动抛出错误（`raise`）：**

```python
# 和 JS 的 throw new Error() 对应
def get_user(user_id: int):
    if user_id < 0:
        raise ValueError("用户 ID 不能为负数")
    return {"id": user_id}

# FastAPI 中用 HTTPException
from fastapi import HTTPException

@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="用户不存在")
    return users[user_id]
```

**Python vs JS 对照：**

| Python | JavaScript | 说明 |
|---|---|---|
| `try:` | `try {` | 尝试执行 |
| `except Error:` | `catch (error) {` | 捕捉错误 |
| `finally:` | `finally {` | 最终清理 |
| `raise ValueError(...)` | `throw new Error(...)` | 主动抛错 |

---

### 8.3 文件读写与 JSON 处理

后端经常需要读写文件（配置文件、日志、数据导出），JSON 是前后端数据交换的通用格式。

#### 文件读写

```python
# 写入文件
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("Hello, AI!\n")
    f.write("这是第二行\n")

# 读取文件
with open("output.txt", "r", encoding="utf-8") as f:
    content = f.read()
    print(content)

# 逐行读取
with open("output.txt", "r", encoding="utf-8") as f:
    for line in f:
        print(line.strip())  # strip() 去掉换行符
```

> 💡 `with open()` 会自动关闭文件，不用手动 `f.close()`。

#### JSON 处理

```python
import json

# Python 字典 → JSON 字符串
user = {"name": "张三", "age": 25}
json_str = json.dumps(user, ensure_ascii=False, indent=2)
print(json_str)

# JSON 字符串 → Python 字典
data = json.loads('{"name": "AI", "version": 4}')
print(data["name"])  # "AI"

# 读写 JSON 文件
with open("config.json", "w", encoding="utf-8") as f:
    json.dump(user, f, ensure_ascii=False, indent=2)

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
    print(config)
```

**JSON 在 AI 应用中的典型用途：**
- API 请求和响应的数据格式
- 配置文件（API Key、模型参数）
- 对话历史的持久化存储

#### Python 的模块导入（import）

上面的例子中你已经用过 `import json`。当项目变大、有多个 `.py` 文件时，你需要理解 Python 怎么找到和引用代码：

```python
# 导入标准库模块
import json                    # 导入整个模块，用 json.loads() 调用
from datetime import datetime  # 只导入模块中的某个东西

# 导入同目录下的自己写的文件
# 假设项目结构：
#   my-project/
#   ├── main.py
#   ├── database.py
#   └── models.py

# 在 main.py 中：
from database import get_db, engine   # 导入 database.py 里的函数/变量
from models import Todo, User         # 导入 models.py 里的类
```

> 💡 Python 通过文件名找模块：`from database import xxx` 就是找同目录下的 `database.py` 文件。后续第 10 章的多文件项目就是这么组织的。

#### 环境变量与 `os.getenv()`

有些敏感信息（如 API Key）不应该写在代码里，而应该放在**环境变量**中。Python 用 `os.getenv()` 读取：

```python
import os

# 读取环境变量
api_key = os.getenv("OPENAI_API_KEY")          # 读取，不存在返回 None
base_url = os.getenv("BASE_URL", "http://localhost:8000")  # 不存在时用默认值

print(api_key)    # 输出环境变量的值
```

```bash
# 在终端设置环境变量
export OPENAI_API_KEY="sk-xxxx"      # Mac / Linux
set OPENAI_API_KEY=sk-xxxx           # Windows

# 或者用 .env 文件（后续章节会详细讲）
```

> 💡 **核心原则**：代码里用 `os.getenv()` 读取，密钥放在环境变量或 `.env` 文件中，`.env` 文件不提交到 Git。

**用 `python-dotenv` 自动加载 `.env` 文件：**

实际项目中不需要手动 `export`，用 `python-dotenv` 可以自动从 `.env` 文件读取：

```bash
# 安装
pip install python-dotenv
```

```python
# 项目根目录创建 .env 文件（不要提交到 Git！）
# .env
# OPENAI_API_KEY=sk-xxxx
# OPENAI_BASE_URL=https://api.example.com/v1

# 在代码中加载
from dotenv import load_dotenv
import os

load_dotenv()  # 自动读取当前目录的 .env 文件

api_key = os.getenv("OPENAI_API_KEY")  # 现在能读到了
```

> 💡 后续第 17 章会用 `pydantic-settings` 替代 `python-dotenv`，提供更强的类型安全配置管理。

### 8.4 虚拟环境与依赖管理（venv / pip）

#### 为什么需要虚拟环境？

假设你有两个项目：项目 A 需要 `fastapi 0.100`，项目 B 需要 `fastapi 0.110`。如果把所有包装在同一个地方，版本就会冲突。

**虚拟环境**给每个项目一个独立的包安装空间，互不干扰。

```
类比：
  没有虚拟环境 = 所有人共用一个书架（书会混乱）
  有虚拟环境   = 每个人有自己的书架（互不干扰）
```

#### 创建和使用虚拟环境

```bash
# 1. 创建虚拟环境（在项目目录下）
python3 -m venv venv

# 2. 激活虚拟环境
# Mac / Linux：
source venv/bin/activate
# Windows：
venv\Scripts\activate

# 激活后终端会显示 (venv) 前缀
# (venv) $ 

# 3. 在虚拟环境中安装包
pip install fastapi uvicorn

# 4. 导出依赖清单
pip freeze > requirements.txt

# 5. 退出虚拟环境
deactivate
```

#### 标准项目初始化流程

每次开始一个新 Python 项目：

```bash
mkdir my-backend
cd my-backend
python3 -m venv venv
source venv/bin/activate
# 安装需要的包...
pip freeze > requirements.txt
```

别人拿到你的项目后：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# 所有依赖就装好了
```

> ⚠️ `venv/` 文件夹要加到 `.gitignore`，不要提交到 Git。

#### 替代方案一：Conda（数据科学首选）

venv + pip 是 Python 官方标配，但在数据科学和 AI 领域，你会频繁遇到另一个工具——**Conda**。

**Conda 和 venv 的核心区别：**

```
venv + pip：
  • Python 官方内置，零安装
  • 只管理 Python 包
  • 适合 Web 开发、后端 API

Conda：
  • 需要额外安装（Miniconda / Anaconda）
  • 能管理 Python 包 + 非 Python 依赖（C 库、CUDA 等）
  • 能管理 Python 版本本身
  • 适合数据科学、机器学习、深度学习
```

**为什么数据科学需要 Conda？** 因为很多科学计算库（NumPy、PyTorch、TensorFlow）依赖底层 C/C++ 库和 CUDA 驱动。用 pip 安装有时会遇到编译错误，而 Conda 直接提供预编译好的二进制包，一行命令就能装好。

**安装 Miniconda（推荐轻量版）：**

```bash
# Mac（Apple Silicon）
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh

# Mac（Intel）
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh

# Windows：下载安装包
# https://docs.conda.io/en/latest/miniconda.html
```

> 💡 **Miniconda vs Anaconda**：Miniconda 只装核心组件（~80MB），Anaconda 预装了 250+ 个数据科学包（~3GB）。新手建议用 Miniconda，需要什么装什么。

**Conda 常用操作：**

```bash
# 1. 创建虚拟环境（可以指定 Python 版本！）
conda create -n my-project python=3.11

# 2. 激活环境
conda activate my-project

# 3. 安装包（优先用 conda，找不到再用 pip）
conda install numpy pandas pytorch
pip install fastapi   # conda 没有的包用 pip 装

# 4. 查看已安装的包
conda list

# 5. 导出环境（类似 requirements.txt）
conda env export > environment.yml

# 6. 从文件还原环境
conda env create -f environment.yml

# 7. 退出环境
conda deactivate

# 8. 删除环境
conda env remove -n my-project
```

**Conda 的 environment.yml 长这样：**

```yaml
name: my-project
channels:
  - defaults
dependencies:
  - python=3.11
  - numpy=1.24
  - pandas=2.0
  - pip:
    - fastapi==0.110.0    # pip 的包放在这里
    - uvicorn==0.29.0
```

> ⚠️ 在 Conda 环境中，**不要混用** `conda install` 和 `pip install` 安装同一个包。优先用 `conda install`，只在 Conda 源里找不到时才用 `pip`。

#### 替代方案二：uv（新一代极速工具）

**uv** 是 2024 年由 Astral 团队（就是做 Ruff 代码检查器的团队）推出的 Python 包管理工具，用 Rust 编写，速度是 pip 的 **10~100 倍**。

```
速度对比（安装 FastAPI + 依赖）：
  pip  ─────────────────── 12 秒
  uv   ── 0.3 秒
  
  就是这么夸张。
```

**安装 uv：**

```bash
# Mac / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows（PowerShell）
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 验证安装
uv --version
```

**uv 作为 pip 替代（最简单的用法）：**

```bash
# 创建虚拟环境
uv venv

# 激活（和 venv 一样）
source .venv/bin/activate    # Mac / Linux
.venv\Scripts\activate       # Windows

# 安装包（语法和 pip 几乎一样，但快 100 倍）
uv pip install fastapi uvicorn
uv pip install -r requirements.txt

# 导出依赖
uv pip freeze > requirements.txt
```

**uv 作为项目管理器（推荐用法）：**

uv 还能像 npm 一样管理整个项目，这是它更强大的用法：

```bash
# 初始化项目（自动创建 pyproject.toml）
uv init my-backend
cd my-backend

# 添加依赖（自动更新 pyproject.toml 和 uv.lock）
uv add fastapi uvicorn
uv add pytest --dev   # 开发依赖

# 运行脚本（自动创建环境、安装依赖）
uv run python main.py
uv run uvicorn main:app --reload

# 同步环境（别人拉取项目后一键还原）
uv sync
```

**uv 生成的 pyproject.toml 长这样：**

```toml
[project]
name = "my-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
]
```

> 💡 `uv run` 是最省心的用法——它会自动检测环境、创建虚拟环境、安装缺失的依赖，然后执行命令。你甚至不需要手动 `source activate`。

#### 三种工具对比总结

| 特性 | venv + pip | Conda | uv |
|---|---|---|---|
| **安装** | Python 自带 | 需装 Miniconda | 需额外安装 |
| **速度** | 一般 | 较慢 | ⚡ 极快（Rust 编写） |
| **Python 版本管理** | ❌ 不支持 | ✅ 支持 | ✅ 支持 |
| **非 Python 依赖** | ❌ 不支持 | ✅ 支持（C库/CUDA） | ❌ 不支持 |
| **锁文件** | ❌ 无 | ❌ 无 | ✅ uv.lock |
| **项目管理** | 手动 | 手动 | ✅ 类似 npm |
| **适合场景** | 通用 Python 开发 | 数据科学 / AI 训练 | 现代 Python 项目 |
| **学习成本** | ⭐ 最低 | ⭐⭐ 中等 | ⭐⭐ 中等 |

**本课程推荐策略：**

```
入门阶段 → venv + pip（零门槛，先跑通流程）
AI 开发  → uv（速度快，现代化项目管理）
数据科学 → Conda（需要 GPU / 科学计算库时切换）
```

> 💡 三种工具不是非此即彼的关系。很多开发者在不同项目中混合使用：Web 项目用 uv，Jupyter 实验用 Conda，临时脚本用 venv。掌握 venv 是基础，其他两个按需学习即可。

### 8.5 面向对象编程（OOP）基础

在前面的章节中，你用函数来组织代码。但当项目变大后，仅靠函数会让代码变得混乱——一堆函数操作一堆变量，谁属于谁分不清楚。**面向对象编程（OOP）** 把"数据"和"操作数据的函数"打包在一起，形成一个**对象**。

```
类比：
  函数式 = 一堆散装工具 + 一堆散装零件（自己记住哪个工具配哪个零件）
  面向对象 = 一个工具箱（工具和零件打包在一起，拿起来就用）
```

> 💡 为什么现在要学 OOP？因为下一章 FastAPI 中的 Pydantic 模型（`class ChatRequest(BaseModel)`）就是 OOP，不理解类和继承你会看不懂。

#### 类与对象：Python vs JavaScript 对照

你在 JS 中已经接触过类（ES6 的 `class`），Python 的概念完全一样：

| 概念 | JavaScript | Python |
|---|---|---|
| 定义类 | `class User {}` | `class User:` |
| 构造函数 | `constructor(name)` | `__init__(self, name)` |
| 实例属性 | `this.name = name` | `self.name = name` |
| 方法 | `greet() {}` | `def greet(self):` |
| 创建实例 | `new User("AI")` | `User("AI")` |
| 继承 | `class Admin extends User` | `class Admin(User)` |

**核心区别：Python 方法第一个参数必须是 `self`**（JS 用 `this` 但不用写参数）。

#### 定义一个类

```python
class User:
    """用户类"""
    
    def __init__(self, name, role="user"):
        """构造函数：创建对象时自动执行"""
        self.name = name       # 实例属性
        self.role = role
        self.messages = []     # 每个用户有自己的消息列表
    
    def send_message(self, content):
        """发送消息"""
        self.messages.append({
            "role": self.role,
            "content": content
        })
        print(f"[{self.name}] {content}")
    
    def get_history(self):
        """获取消息历史"""
        return self.messages

# 创建对象（不需要 new 关键字）
alice = User("Alice", "admin")
bob = User("Bob")

alice.send_message("你好！")        # [Alice] 你好！
bob.send_message("Hi!")             # [Bob] Hi!

print(alice.get_history())          # [{"role": "admin", "content": "你好！"}]
print(bob.get_history())            # [{"role": "user", "content": "Hi!"}]
# 两个对象的消息列表互不干扰
```

**理解 `self`：**

```python
# self 就是"当前这个对象自己"
# 当你调用 alice.send_message("你好") 时
# Python 自动把 alice 传给 self：
#   send_message(alice, "你好")
#                ↑ self    ↑ content

# 所以 self.name 就是 alice.name，即 "Alice"
```

> ⚠️ `self` 只是约定名称（你写成 `this` 也能运行），但**全世界 Python 开发者都用 `self`**，不要改。

#### 继承：复用已有代码

继承让你基于已有的类创建新类，**只写不同的部分**：

```python
class Admin(User):
    """管理员类，继承自 User"""
    
    def __init__(self, name):
        super().__init__(name, role="admin")  # 调用父类构造函数
        self.permissions = ["delete", "ban", "edit"]
    
    def delete_message(self, user, index):
        """管理员专属功能：删除用户消息"""
        if index < len(user.messages):
            removed = user.messages.pop(index)
            print(f"[管理员 {self.name}] 删除了消息：{removed['content']}")

# Admin 拥有 User 的所有方法 + 自己的新方法
admin = Admin("超级管理员")
admin.send_message("大家好")          # 继承的方法，直接能用
admin.delete_message(bob, 0)          # 管理员专属方法
```

**继承关系图：**

```
User（父类 / 基类）
  ├── name, role, messages
  ├── send_message()
  └── get_history()
      │
      ▼ 继承
Admin（子类 / 派生类）
  ├── 拥有 User 的所有属性和方法
  ├── permissions              ← 新增属性
  └── delete_message()          ← 新增方法
```

> 💡 `super().__init__()` 的意思是"先执行父类的构造函数"。这确保父类定义的属性（name、role、messages）被正确初始化。

#### 为什么 FastAPI 要用 OOP？

现在回看第 9 章的 Pydantic 模型，你就能看懂了：

```python
from pydantic import BaseModel

# 这就是继承！ChatRequest 继承了 BaseModel 的数据校验能力
class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-4o"
    temperature: float = 0.7

# BaseModel 提供的能力（你不用自己写）：
request = ChatRequest(message="你好")
print(request.model)              # "gpt-4o"（默认值）
print(request.model_dump())       # {"message": "你好", "model": "gpt-4o", "temperature": 0.7}
```

```
你写的 ChatRequest 只定义了"有哪些字段"
BaseModel（父类）自动提供了：
  ✅ 数据类型校验
  ✅ 默认值处理
  ✅ 序列化（转字典 / JSON）
  ✅ 错误提示

这就是继承的威力——站在巨人的肩膀上。
```

#### 实用技巧：`__str__` 和 `__repr__`

Python 类有一些特殊方法（双下划线方法），最常用的是控制对象的"打印输出"：

```python
class Message:
    def __init__(self, role, content):
        self.role = role
        self.content = content
    
    def __str__(self):
        """print() 时的输出"""
        return f"[{self.role}] {self.content}"
    
    def __repr__(self):
        """调试时的输出（在终端直接输入变量名）"""
        return f"Message(role='{self.role}', content='{self.content[:20]}...')"

msg = Message("user", "请帮我写一段 Python 代码")
print(msg)    # [user] 请帮我写一段 Python 代码
# 在 Python 交互式终端直接输入 msg 回车：
# Message(role='user', content='请帮我写一段 Python 代码...')
```

#### OOP 在 AI 应用中的典型用途

```
在本课程后续章节中，你会不断遇到 OOP：

第 9 章  → Pydantic BaseModel（请求/响应数据模型）
第 11 章 → 自定义异常类（class APIError(Exception)）
第 13 章 → LangChain 的 Tool 类（继承 BaseTool）
第 15 章 → Agent 类的封装（把提示词、工具、记忆打包）

掌握"类、实例、继承"三个概念就够用了，不需要学设计模式。
```

### 8.6 实战：写一个数据处理脚本

综合运用本章知识，写一个实用的 Python 脚本：**读取 JSON 格式的对话记录，统计分析并导出报告**。

```python
import json
from datetime import datetime

# 1. 读取对话记录
with open("chat_history.json", "r", encoding="utf-8") as f:
    chats = json.load(f)

# 示例数据格式：
# [
#     {"role": "user", "content": "你好", "timestamp": "2025-06-15 10:00"},
#     {"role": "ai", "content": "你好！有什么可以帮你的？", "timestamp": "2025-06-15 10:00"},
#     ...
# ]

# 2. 统计分析
total_messages = len(chats)
user_messages = [msg for msg in chats if msg["role"] == "user"]
ai_messages = [msg for msg in chats if msg["role"] == "ai"]

avg_user_length = sum(len(msg["content"]) for msg in user_messages) / len(user_messages)
avg_ai_length = sum(len(msg["content"]) for msg in ai_messages) / len(ai_messages)

# 3. 生成报告
report = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "total_messages": total_messages,
    "user_messages": len(user_messages),
    "ai_messages": len(ai_messages),
    "avg_user_message_length": round(avg_user_length),
    "avg_ai_message_length": round(avg_ai_length),
}

# 4. 输出到终端
print("=" * 40)
print("  📊 对话统计报告")
print("=" * 40)
for key, value in report.items():
    print(f"  {key}: {value}")

# 5. 保存到文件
with open("report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"\n✅ 报告已保存到 report.json")
```

这个脚本综合运用了：变量、列表推导式、字典、f-string、文件读写、JSON 处理。

#### 本章小结

```
✅ 你已经掌握了：
  • Python 核心语法（对照 JS 快速上手）
  • 列表推导式、字典操作
  • 类型注解、装饰器、生成器（yield）、异步（async/await）
  • 错误处理（try/except）、字典解包（**kwargs）
  • 模块导入（import）、环境变量（os.getenv + python-dotenv）
  • 文件读写与 JSON 处理
  • 虚拟环境：venv / Conda / uv 三种工具
  • 面向对象编程：类、实例、继承、特殊方法

🎯 下一章你将学习：
  • 用 FastAPI 构建后端 API——让前端能和后端"对话"
```

---

## 9. 后端开发入门：FastAPI

前端负责"用户看到什么"，后端负责"数据从哪来"。本章你将学会用 Python 的 FastAPI 框架构建后端 API——这是连接前端界面和 AI 能力的关键桥梁。

---

### 9.1 什么是后端？什么是 API？HTTP 基础

#### 前后端的分工

```
用户 ←→ 前端（浏览器）←→ 后端（服务器）←→ 数据库 / AI API
         展示界面              处理逻辑            存储数据
```

- **前端**：用户看到的界面，运行在浏览器里
- **后端**：运行在服务器上的程序，负责接收请求、处理数据、调用 AI、返回结果

#### 什么是 API？

API（Application Programming Interface）就是**前后端之间的"约定"**——前端按照什么格式发请求，后端按照什么格式返回数据。

```
类比：
  前端 = 餐厅顾客（点菜）
  API  = 菜单（规定有什么菜、怎么点、多少钱）
  后端 = 厨房（做菜、出餐）
```

#### HTTP 基础

前后端通过 **HTTP 协议**通信。你需要知道：

**请求方法（动词）：**

| 方法 | 用途 | 示例 |
|---|---|---|
| `GET` | 获取数据 | 获取消息列表 |
| `POST` | 创建数据 | 发送一条新消息 |
| `PUT` | 更新数据 | 修改消息内容 |
| `DELETE` | 删除数据 | 删除一条消息 |

**状态码（后端返回的"信号灯"）：**

| 状态码 | 含义 | 场景 |
|---|---|---|
| `200` | 成功 | 请求正常处理 |
| `201` | 创建成功 | 新增数据成功 |
| `400` | 参数错误 | 前端传了不合法的数据 |
| `404` | 找不到 | 请求的资源不存在 |
| `500` | 服务器内部错误 | 后端代码有 Bug |

---

### 9.2 用 FastAPI 写第一个接口

FastAPI 是 Python 最现代的 Web 框架，速度快、自带文档、语法简洁。

#### 安装

```bash
pip install fastapi uvicorn
```

- `fastapi`：Web 框架本体
- `uvicorn`：运行 FastAPI 的服务器

#### Hello World

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "Hello, AI 世界！"}

@app.get("/greet/{name}")
def greet(name: str):
    return {"message": f"你好，{name}！"}
```

#### 运行

```bash
uvicorn main:app --reload
# --reload：修改代码后自动重启（开发模式）
# 访问 http://localhost:8000
```

#### 自动生成的 API 文档

FastAPI 最棒的功能——启动后访问以下地址：

- `http://localhost:8000/docs`：交互式 API 文档（Swagger UI）
- `http://localhost:8000/redoc`：另一种风格的文档

你可以直接在文档页面测试每个接口，不需要前端！

#### 理解装饰器 @app.get()

```python
@app.get("/users")       # GET 请求 /users
@app.post("/messages")   # POST 请求 /messages
@app.put("/users/{id}")  # PUT 请求 /users/123
@app.delete("/users/{id}") # DELETE 请求 /users/123
```

`@app.get("/path")` 的意思是："当有人用 GET 方法访问 /path 时，执行下面这个函数"。

### 9.3 请求参数、响应体与 Pydantic 数据校验

#### 三种接收参数的方式

```python
from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI()

# 1. 路径参数：写在 URL 路径里
@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}
# 访问：GET /users/42

# 2. 查询参数：写在 URL 的 ? 后面
@app.get("/search")
def search(keyword: str, limit: int = 10):
    return {"keyword": keyword, "limit": limit}
# 访问：GET /search?keyword=AI&limit=5

# 3. 请求体：复杂数据通过 POST 发送（最常用）
class MessageRequest(BaseModel):
    content: str
    model: str = "gpt-4o"

@app.post("/chat")
def chat(request: MessageRequest):
    return {"reply": f"你说的是：{request.content}，使用模型：{request.model}"}
# POST /chat，Body: {"content": "你好", "model": "gpt-4o"}
```

#### Pydantic：自动数据校验

Pydantic 是 FastAPI 的搭档，用来定义数据格式并**自动校验**。如果前端传了不合法的数据，FastAPI 自动返回 422 错误。

```python
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="用户消息，不能为空")
    model: str = Field(default="gpt-4o", description="使用的模型")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(default=1000, ge=1, le=4096, description="最大输出长度")

class ChatResponse(BaseModel):
    reply: str
    model: str
    usage: dict

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # FastAPI 自动校验：
    # - message 不能为空
    # - temperature 必须在 0~2 之间
    # - max_tokens 必须在 1~4096 之间
    return ChatResponse(
        reply=f"收到：{request.message}",
        model=request.model,
        usage={"prompt_tokens": 10, "completion_tokens": 20}
    )
```

**校验失败时的自动错误响应：**

```json
{
    "detail": [
        {
            "loc": ["body", "temperature"],
            "msg": "ensure this value is less than or equal to 2",
            "type": "value_error"
        }
    ]
}
```

你不需要手写任何校验代码，Pydantic 全部帮你搞定。

### 9.4 实战：做一个"待办事项" REST API

综合运用本章知识，构建一个完整的 CRUD（增删改查）API。

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="待办事项 API")

# --- 数据模型 ---
class TodoCreate(BaseModel):
    title: str = Field(min_length=1, description="待办标题")
    done: bool = Field(default=False, description="是否完成")

class Todo(TodoCreate):
    id: int

# --- 临时存储（下一章换成数据库） ---
todos: list[Todo] = []
next_id = 1

# --- 接口 ---

# 查询所有待办
@app.get("/todos", response_model=list[Todo])
def list_todos():
    return todos

# 创建待办
@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(todo: TodoCreate):
    global next_id
    new_todo = Todo(id=next_id, **todo.model_dump())
    todos.append(new_todo)
    next_id += 1
    return new_todo

# 更新待办
@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo: TodoCreate):
    for i, t in enumerate(todos):
        if t.id == todo_id:
            todos[i] = Todo(id=todo_id, **todo.model_dump())
            return todos[i]
    raise HTTPException(status_code=404, detail="待办不存在")

# 删除待办
@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    for i, t in enumerate(todos):
        if t.id == todo_id:
            todos.pop(i)
            return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="待办不存在")
```

运行后访问 `http://localhost:8000/docs`，你就能在交互式文档中测试所有接口。

**这个 API 的问题**：数据存在内存里，服务器重启就丢失了。下一章我们会加上数据库解决这个问题。

#### 本章小结

```
✅ 你已经掌握了：
  • 前后端分工和 API 的概念
  • HTTP 方法（GET/POST/PUT/DELETE）和状态码
  • FastAPI：创建接口、运行服务器、自动文档
  • Pydantic：数据模型定义和自动校验
  • 完整的 CRUD REST API

🎯 下一章你将学习：
  • 数据库——让数据持久化存储，不再"重启丢失"
```

---

## 10. 数据库基础

上一章我们用 FastAPI 做了一个待办事项 API，但有一个致命问题：数据存在 Python 的列表里，服务器一重启就全没了。这就像你在白板上记笔记——擦掉就没有了。**数据库**就是帮你把数据永久保存在硬盘上的工具。

---

### 10.1 内存 vs 持久化：为什么需要数据库

#### 上一章的问题

回顾第 9 章的待办 API：

```python
# 数据存在内存里（Python 列表）
todos: list[Todo] = []
```

这意味着：

| 场景 | 结果 |
|---|---|
| 服务器重启 | ❌ 所有数据丢失 |
| 同时有 1000 个用户访问 | ❌ 数据混在一起，无法区分 |
| 数据量达到 100 万条 | ❌ 内存不够，程序崩溃 |
| 想按条件查询（如"找出已完成的待办"） | ❌ 需要自己写循环和过滤逻辑 |

#### 数据库解决了什么？

```
内存存储：
  程序启动 → 数据存在内存 → 程序关闭 → 数据消失
              （白板笔记）

数据库存储：
  程序启动 → 数据存在硬盘文件 → 程序关闭 → 数据还在
                  （笔记本）
```

数据库的核心价值：

- ✅ **持久化**：数据保存在硬盘，重启不丢失
- ✅ **高效查询**：用 SQL 语言快速查找、过滤、排序
- ✅ **并发安全**：多个用户同时读写也不会冲突
- ✅ **数据完整性**：自动校验数据格式，防止脏数据

#### 数据库的种类

| 类型 | 代表 | 特点 | 本课程使用 |
|---|---|---|---|
| **关系型数据库** | SQLite、PostgreSQL、MySQL | 用表格存数据，有行有列，用 SQL 查询 | ✅ SQLite |
| **向量数据库** | Chroma、Milvus、Pinecone | 存储文本向量，用于语义搜索 | 第 14 章 |
| **文档数据库** | MongoDB | 存储 JSON 格式的文档 | 了解即可 |
| **键值数据库** | Redis | 用 key-value 存储，速度极快 | 了解即可 |

#### 为什么选 SQLite？

| | SQLite | PostgreSQL |
|---|---|---|
| **安装** | ✅ 无需安装，Python 内置 | 需要单独安装服务 |
| **存储** | 一个 `.db` 文件 | 独立数据库服务 |
| **适用场景** | 学习、个人项目、小应用 | 生产环境、高并发 |
| **性能** | 够用（每秒几百次查询） | 高性能（每秒数万次） |

SQLite 是学习数据库的最佳选择——零配置、零安装，一个文件就是一个数据库。等你的应用需要更高性能时，SQL 语法几乎不需要改，只要换个数据库驱动即可。

#### 关系型数据库的核心概念

在开始写 SQL 之前，先理解几个基本概念：

```
关系型数据库 ≈ Excel 表格

数据库（Database）  = 一个 Excel 文件
表（Table）         = Excel 里的一个 Sheet
行（Row）           = Sheet 里的一行数据
列（Column）        = Sheet 里的一列（字段名）
主键（Primary Key） = 每行的唯一编号（如 ID）
```

以聊天应用为例：

```
数据库：chat_app.db
├── users 表
│   ├── id | name    | email
│   ├──  1 | 张三    | zhang@mail.com
│   └──  2 | 李四    | li@mail.com
├── conversations 表
│   ├── id | user_id | title         | created_at
│   ├──  1 |    1    | "AI 问答"     | 2025-06-15
│   └──  2 |    1    | "翻译助手"    | 2025-06-16
└── messages 表
    ├── id | conversation_id | role   | content
    ├──  1 |       1        | user   | "你好"
    └──  2 |       1        |  ai    | "你好！有什么可以帮你？"
```

> 💡 表和表之间通过"外键"关联。比如 `messages.conversation_id` 指向 `conversations.id`，表示"这条消息属于哪个对话"。

### 10.2 SQL 基础：增删改查

SQL（Structured Query Language）是操作关系型数据库的语言。不管你用 SQLite、PostgreSQL 还是 MySQL，SQL 语法基本一致。

#### 创建表（建表）

```sql
-- 创建 todos 表
CREATE TABLE todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 自增主键
    title TEXT NOT NULL,                    -- 标题，不能为空
    done BOOLEAN DEFAULT 0,                -- 是否完成，默认未完成
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 创建时间，自动填入
);
```

**常见数据类型：**

| SQL 类型 | 说明 | 示例 |
|---|---|---|
| `INTEGER` | 整数 | `id`, `age`, `count` |
| `TEXT` | 文本 | `name`, `content`, `email` |
| `REAL` | 浮点数 | `price`, `score` |
| `BOOLEAN` | 布尔值（0/1） | `done`, `is_active` |
| `TIMESTAMP` | 时间戳 | `created_at`, `updated_at` |

#### 增：INSERT

```sql
-- 插入一条数据
INSERT INTO todos (title, done) VALUES ('学习 SQL', 0);

-- 插入多条数据
INSERT INTO todos (title, done) VALUES 
    ('写 FastAPI 后端', 0),
    ('做 React 前端', 0),
    ('部署上线', 0);
```

#### 查：SELECT

```sql
-- 查询所有待办
SELECT * FROM todos;

-- 只查特定列
SELECT id, title FROM todos;

-- 条件查询
SELECT * FROM todos WHERE done = 0;              -- 未完成的
SELECT * FROM todos WHERE title LIKE '%API%';     -- 标题包含 "API" 的

-- 排序
SELECT * FROM todos ORDER BY created_at DESC;     -- 按创建时间倒序

-- 限制数量
SELECT * FROM todos LIMIT 10;                     -- 只取前 10 条

-- 组合条件
SELECT * FROM todos 
WHERE done = 0 
ORDER BY created_at DESC 
LIMIT 5;
```

> 💡 `SELECT` 是你最常用的 SQL 语句。记住模式：`SELECT 列 FROM 表 WHERE 条件 ORDER BY 排序 LIMIT 数量`。

#### 改：UPDATE

```sql
-- 将 id=1 的待办标记为已完成
UPDATE todos SET done = 1 WHERE id = 1;

-- 修改标题
UPDATE todos SET title = '学习 SQL（已完成）' WHERE id = 1;

-- 同时修改多个字段
UPDATE todos SET title = '新标题', done = 1 WHERE id = 2;
```

> ⚠️ **UPDATE 和 DELETE 一定要加 WHERE 条件！** 不加条件会修改/删除所有数据。

#### 删：DELETE

```sql
-- 删除 id=1 的待办
DELETE FROM todos WHERE id = 1;

-- 删除所有已完成的待办
DELETE FROM todos WHERE done = 1;

-- ⚠️ 危险操作：删除所有数据（不要轻易执行）
DELETE FROM todos;
```

#### SQL CRUD 速查表

```
增  INSERT INTO 表 (列1, 列2) VALUES (值1, 值2);
查  SELECT 列 FROM 表 WHERE 条件 ORDER BY 排序 LIMIT 数量;
改  UPDATE 表 SET 列 = 值 WHERE 条件;
删  DELETE FROM 表 WHERE 条件;
建表 CREATE TABLE 表 (列 类型 约束, ...);
删表 DROP TABLE 表;
```

#### 用 SQLite 命令行练习

Python 自带 SQLite，你可以直接在终端练习：

```bash
# 打开（或创建）一个 SQLite 数据库
sqlite3 practice.db
```

```sql
-- 在 sqlite3 命令行中执行：
CREATE TABLE todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done BOOLEAN DEFAULT 0
);

INSERT INTO todos (title) VALUES ('学习 SQL');
INSERT INTO todos (title) VALUES ('写后端 API');
INSERT INTO todos (title) VALUES ('做 React 前端');

SELECT * FROM todos;
-- 输出：
-- 1|学习 SQL|0
-- 2|写后端 API|0
-- 3|做 React 前端|0

UPDATE todos SET done = 1 WHERE id = 1;
SELECT * FROM todos WHERE done = 0;

-- 退出
.quit
```

> 💡 如果觉得命令行不方便，可以用 VS Code 的 SQLite Viewer 插件，图形界面查看 `.db` 文件。

### 10.3 Python 操作数据库（SQLite + SQLAlchemy）

上一节你学会了 SQL 语法，但在实际项目中，你不会在命令行里敲 SQL——而是用 Python 代码来执行 SQL。Python 操作数据库有两种方式：**原生 sqlite3** 和 **ORM（SQLAlchemy）**。

#### 方式一：原生 sqlite3（理解原理）

Python 内置了 `sqlite3` 模块，零安装直接用：

```python
import sqlite3

# 1. 连接数据库（文件不存在会自动创建）
conn = sqlite3.connect("todos.db")
cursor = conn.cursor()

# 2. 创建表
cursor.execute("""
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        done BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# 3. 插入数据（用 ? 占位符防止 SQL 注入）
cursor.execute(
    "INSERT INTO todos (title) VALUES (?)", 
    ("学习数据库",)
)
conn.commit()  # ⚠️ 写操作必须 commit 才会真正保存

# 4. 查询数据
cursor.execute("SELECT * FROM todos WHERE done = 0")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}, 标题: {row[1]}, 完成: {row[2]}")

# 5. 更新数据
cursor.execute("UPDATE todos SET done = 1 WHERE id = ?", (1,))
conn.commit()

# 6. 关闭连接
conn.close()
```

> ⚠️ **SQL 注入攻击**：永远不要用 f-string 拼接 SQL！用 `?` 占位符让数据库自己处理参数。

```python
# ❌ 危险！用户输入可能包含恶意 SQL
cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")

# ✅ 安全！用参数化查询
cursor.execute("SELECT * FROM users WHERE name = ?", (user_input,))
```

#### 方式二：SQLAlchemy ORM（实际开发推荐）

原生 SQL 的问题：你需要手写 SQL 字符串、手动处理数据类型转换、代码可读性差。**ORM（Object-Relational Mapping）** 让你用 Python 对象来操作数据库，不用写 SQL。

```
ORM 的思路：
  数据库的表  ←→ Python 的类
  表里的一行  ←→ 类的一个实例
  表的列      ←→ 类的属性
```

**安装：**

```bash
pip install sqlalchemy
```

**定义模型（Model）：**

```python
# models.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime

# 1. 创建数据库连接
engine = create_engine("sqlite:///todos.db", echo=True)
# echo=True 会在终端打印实际执行的 SQL，方便调试

# 2. 定义基类
class Base(DeclarativeBase):
    pass

# 3. 定义 Todo 模型（对应数据库的 todos 表）
class Todo(Base):
    __tablename__ = "todos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"Todo(id={self.id}, title='{self.title}', done={self.done})"

# 4. 创建表（如果不存在）
Base.metadata.create_all(engine)

# 5. 创建 Session（用于执行数据库操作）
SessionLocal = sessionmaker(bind=engine)
```

**CRUD 操作：**

```python
from models import SessionLocal, Todo

# 创建一个数据库会话
db = SessionLocal()

# --- 增 ---
new_todo = Todo(title="学习 SQLAlchemy")
db.add(new_todo)
db.commit()
db.refresh(new_todo)  # 刷新，获取自动生成的 id
print(new_todo)  # Todo(id=1, title='学习 SQLAlchemy', done=False)

# --- 查 ---
# 查询所有
all_todos = db.query(Todo).all()

# 条件查询
undone = db.query(Todo).filter(Todo.done == False).all()

# 查询单条
todo = db.query(Todo).filter(Todo.id == 1).first()

# 排序 + 分页
recent = db.query(Todo).order_by(Todo.created_at.desc()).limit(5).all()

# --- 改 ---
todo = db.query(Todo).filter(Todo.id == 1).first()
todo.done = True
db.commit()

# --- 删 ---
todo = db.query(Todo).filter(Todo.id == 1).first()
db.delete(todo)
db.commit()

# 关闭会话
db.close()
```

#### 原生 SQL vs ORM 对比

| | 原生 sqlite3 | SQLAlchemy ORM |
|---|---|---|
| **写法** | 手写 SQL 字符串 | 用 Python 对象和方法 |
| **可读性** | 一般（SQL 混在 Python 中） | 好（纯 Python 代码） |
| **安全性** | 需要自己防 SQL 注入 | ORM 自动处理 |
| **数据库切换** | 需要改 SQL 语法 | 只改连接字符串 |
| **适合** | 简单脚本、学习原理 | 实际项目开发 |

> 💡 本课程后续统一使用 SQLAlchemy ORM。理解原理后用 ORM 更高效。

### 10.4 实战：给待办事项 API 加上数据库存储

现在把第 9 章的待办事项 API 从"内存存储"升级到"数据库存储"。这是一个非常典型的重构过程——**业务逻辑不变，只是把数据层从列表换成数据库**。

#### 项目结构

```
todo-api/
├── main.py              ← FastAPI 应用（API 接口）
├── models.py            ← 数据库模型定义
├── database.py          ← 数据库连接配置
├── requirements.txt     ← 依赖清单
└── todos.db             ← SQLite 数据库文件（自动生成）
```

#### Step 1：数据库配置（database.py）

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# SQLite 数据库文件路径
DATABASE_URL = "sqlite:///./todos.db"

# 创建引擎
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# check_same_thread=False 是 SQLite 特有的，允许多线程访问

# 创建 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类
class Base(DeclarativeBase):
    pass

# 数据库依赖（FastAPI 的依赖注入用）
def get_db():
    db = SessionLocal()
    try:
        yield db        # 把 db 会话交给接口函数使用
    finally:
        db.close()      # 接口函数执行完后自动关闭
```

**理解 `get_db()` 和 `Depends`：**

上面的 `get_db()` 用了 `yield`（第 8.2 节讲过）。后面的接口代码中你会看到 `db: Session = Depends(get_db)` 这种写法——这叫**依赖注入**。

```
类比：
  去餐厅吃饭，你不需要自己去厨房拿刀叉
  服务员（FastAPI）自动帮你准备好（Depends）

Depends(get_db) 的意思：
  "FastAPI，每次有请求进来时：
   ① 自动执行 get_db()，创建一个数据库连接
   ② 把连接传给我的接口函数用（yield db）
   ③ 接口函数执行完后，自动关闭连接（finally: db.close()）"
```

你不需要在每个接口里手动写 `db = SessionLocal()` 和 `db.close()`——`Depends` 帮你全自动管理。

#### Step 2：数据模型（models.py）

```python
# models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from database import Base

class Todo(Base):
    __tablename__ = "todos"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
```

#### Step 3：FastAPI 接口（main.py）

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import engine, get_db, Base
from models import Todo

# 启动时创建表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="待办事项 API（数据库版）")

# --- Pydantic 模型（请求/响应格式） ---
class TodoCreate(BaseModel):
    title: str = Field(min_length=1, description="待办标题")
    done: bool = Field(default=False, description="是否完成")

class TodoResponse(BaseModel):
    id: int
    title: str
    done: bool
    created_at: str  # 返回字符串格式的时间
    
    class Config:
        from_attributes = True  # 允许从 ORM 对象自动转换

# --- API 接口 ---

@app.get("/todos", response_model=list[TodoResponse])
def list_todos(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """查询所有待办（支持分页）"""
    todos = db.query(Todo).offset(skip).limit(limit).all()
    return [TodoResponse(
        id=t.id, title=t.title, done=t.done,
        created_at=t.created_at.strftime("%Y-%m-%d %H:%M")
    ) for t in todos]

@app.post("/todos", response_model=TodoResponse, status_code=201)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """创建新待办"""
    new_todo = Todo(title=todo.title, done=todo.done)
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return TodoResponse(
        id=new_todo.id, title=new_todo.title, done=new_todo.done,
        created_at=new_todo.created_at.strftime("%Y-%m-%d %H:%M")
    )

@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: TodoCreate, db: Session = Depends(get_db)):
    """更新待办"""
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="待办不存在")
    db_todo.title = todo.title
    db_todo.done = todo.done
    db.commit()
    db.refresh(db_todo)
    return TodoResponse(
        id=db_todo.id, title=db_todo.title, done=db_todo.done,
        created_at=db_todo.created_at.strftime("%Y-%m-%d %H:%M")
    )

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """删除待办"""
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="待办不存在")
    db.delete(db_todo)
    db.commit()
    return {"message": "删除成功"}
```

#### 对比：升级前 vs 升级后

| | 内存版（第 9 章） | 数据库版（本章） |
|---|---|---|
| **数据存储** | Python 列表 | SQLite 文件 |
| **重启后数据** | ❌ 全部丢失 | ✅ 完好保留 |
| **查询能力** | 自己写循环 | SQL 强大查询 |
| **分页** | 手动切片 | `offset` + `limit` |
| **代码量变化** | — | 增加 `database.py` + `models.py` |

#### 运行并测试

```bash
# 安装依赖
pip install fastapi uvicorn sqlalchemy

# 运行
uvicorn main:app --reload

# 打开浏览器访问 http://localhost:8000/docs 测试
```

在交互式文档中：
1. 用 POST `/todos` 创建几条待办
2. 用 GET `/todos` 查看列表
3. **重启服务器**（`Ctrl+C` 然后重新 `uvicorn`）
4. 再次 GET `/todos`——**数据还在！** 🎉

> 💡 你会发现项目目录下多了一个 `todos.db` 文件，这就是 SQLite 的数据库文件。你可以用 SQLite Viewer 插件打开它，直接看到表和数据。

#### 本章小结

```
✅ 你已经掌握了：
  • 为什么需要数据库：持久化、高效查询、并发安全
  • SQL 四大操作：INSERT、SELECT、UPDATE、DELETE
  • Python 原生 sqlite3 操作（理解原理）
  • SQLAlchemy ORM（实际开发推荐）
  • FastAPI + SQLAlchemy 的集成模式

🎯 下一章你将学习：
  • 前后端联调——让 React 前端和 FastAPI 后端真正连通
```

---

## 11. 前后端联调

到目前为止，你的前端（React）和后端（FastAPI）都是各跑各的——前端有聊天界面但数据是假的，后端有 API 但只能在文档页面测试。本章要做的，就是**让前端和后端真正连通**，完成数据的完整闭环。

---

### 11.1 前端如何调后端：fetch 与 axios

#### 回顾：前端和后端的通信方式

```
浏览器（前端 React）                    服务器（后端 FastAPI）
┌─────────────┐     HTTP 请求         ┌─────────────────┐
│  用户点击     │ ──────────────────→  │  接收请求         │
│  "发送"按钮   │                      │  处理数据         │
│              │  ←──────────────────  │  调用数据库/AI    │
│  显示结果     │     HTTP 响应         │  返回结果         │
└─────────────┘                       └─────────────────┘
```

前端通过 **HTTP 请求**和后端通信。在第 5 章你已经学过 `fetch`，现在要在 React 项目中正式使用它。

#### 方式一：fetch（浏览器内置）

`fetch` 是浏览器原生的请求方法，零安装直接用：

```javascript
// GET 请求：获取待办列表
const fetchTodos = async () => {
    try {
        const response = await fetch("http://localhost:8000/todos");
        const data = await response.json();
        console.log(data);  // [{id: 1, title: "学习", done: false}, ...]
    } catch (error) {
        console.error("请求失败：", error);
    }
};

// POST 请求：创建新待办
const createTodo = async (title) => {
    try {
        const response = await fetch("http://localhost:8000/todos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, done: false })
        });
        const newTodo = await response.json();
        console.log("创建成功：", newTodo);
    } catch (error) {
        console.error("创建失败：", error);
    }
};

// PUT 请求：更新待办
const updateTodo = async (id, title, done) => {
    await fetch(`http://localhost:8000/todos/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, done })
    });
};

// DELETE 请求：删除待办
const deleteTodo = async (id) => {
    await fetch(`http://localhost:8000/todos/${id}`, {
        method: "DELETE"
    });
};
```

#### 方式二：axios（第三方库，更方便）

axios 是最流行的 HTTP 请求库，语法比 fetch 更简洁：

```bash
npm install axios
```

```javascript
import axios from "axios";

// GET 请求
const fetchTodos = async () => {
    const { data } = await axios.get("http://localhost:8000/todos");
    return data;  // axios 自动解析 JSON，不需要 .json()
};

// POST 请求
const createTodo = async (title) => {
    const { data } = await axios.post("http://localhost:8000/todos", {
        title,
        done: false
    });
    return data;  // 不需要手动设置 Content-Type
};

// PUT 请求
const updateTodo = async (id, title, done) => {
    await axios.put(`http://localhost:8000/todos/${id}`, { title, done });
};

// DELETE 请求
const deleteTodo = async (id) => {
    await axios.delete(`http://localhost:8000/todos/${id}`);
};
```

#### fetch vs axios 对比

| | fetch | axios |
|---|---|---|
| **安装** | ✅ 无需安装，浏览器内置 | 需要 `npm install axios` |
| **JSON 解析** | 需要手动 `.json()` | ✅ 自动解析 |
| **错误处理** | 只在网络错误时 reject | ✅ 非 2xx 状态码也会 reject |
| **请求拦截** | ❌ 不支持 | ✅ 支持（加 Token、统一错误处理） |
| **代码简洁度** | 一般 | ✅ 更简洁 |

> 💡 本课程两种都会用。简单项目用 fetch 即可；正式项目推荐 axios。

#### 封装 API 请求（推荐做法）

实际项目中，不要在每个组件里直接写请求地址。把所有 API 请求封装到一个文件里：

```javascript
// src/services/api.js
import axios from "axios";

const API_BASE = "http://localhost:8000";

const api = axios.create({
    baseURL: API_BASE,
    timeout: 10000,  // 10 秒超时
});

// 待办相关 API
export const todoAPI = {
    getAll: () => api.get("/todos"),
    create: (title) => api.post("/todos", { title, done: false }),
    update: (id, data) => api.put(`/todos/${id}`, data),
    delete: (id) => api.delete(`/todos/${id}`),
};
```

```jsx
// 在组件中使用
import { todoAPI } from "../services/api";

const TodoPage = () => {
    const [todos, setTodos] = useState([]);
    
    useEffect(() => {
        todoAPI.getAll().then(res => setTodos(res.data));
    }, []);
    
    const handleAdd = async (title) => {
        const { data } = await todoAPI.create(title);
        setTodos(prev => [...prev, data]);
    };
    
    // ...
};
```

这样做的好处：
- ✅ API 地址只写一次（改后端地址只改一处）
- ✅ 可以统一添加 Token、错误处理
- ✅ 组件代码更干净

### 11.2 跨域问题（CORS）与解决方案

当你第一次从 React 前端请求 FastAPI 后端时，大概率会遇到这个错误：

```
Access to fetch at 'http://localhost:8000/todos' from origin 'http://localhost:5173' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present 
on the requested resource.
```

别慌，这是前后端联调中**最经典的坑**，几乎所有新手都会遇到。

#### 什么是跨域？

浏览器有一个安全机制叫**同源策略**：只允许网页向"同源"的服务器发请求。"同源"指的是**协议 + 域名 + 端口**完全一致。

```
前端地址：http://localhost:5173    ← Vite 开发服务器
后端地址：http://localhost:8000    ← FastAPI 服务器

端口不同（5173 ≠ 8000）→ 不同源 → 浏览器拒绝请求
```

| 前端地址 | 后端地址 | 是否同源 |
|---|---|---|
| `http://localhost:5173` | `http://localhost:8000` | ❌ 端口不同 |
| `http://myapp.com` | `http://api.myapp.com` | ❌ 域名不同 |
| `http://myapp.com` | `https://myapp.com` | ❌ 协议不同 |
| `http://localhost:8000` | `http://localhost:8000` | ✅ 完全相同 |

#### 解决方案：在后端配置 CORS

**CORS（Cross-Origin Resource Sharing）** 是一种标准机制——后端明确告诉浏览器"我允许来自哪些地址的请求"。

FastAPI 配置 CORS 非常简单，加 3 行代码：

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 配置 CORS（关键代码）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 允许的前端地址
    allow_credentials=True,
    allow_methods=["*"],    # 允许所有 HTTP 方法
    allow_headers=["*"],    # 允许所有请求头
)

# 你的接口定义...
@app.get("/todos")
def list_todos():
    # ...
```

**参数解释：**

| 参数 | 含义 | 推荐值 |
|---|---|---|
| `allow_origins` | 允许的前端地址列表 | 开发时 `["*"]`，生产时指定具体域名 |
| `allow_methods` | 允许的 HTTP 方法 | `["*"]`（允许 GET/POST/PUT/DELETE） |
| `allow_headers` | 允许的请求头 | `["*"]` |
| `allow_credentials` | 是否允许携带 Cookie | `True` |

> ⚠️ 生产环境**不要**用 `allow_origins=["*"]`，应该明确列出你的前端域名，比如 `["https://myapp.com"]`。`*` 意味着任何网站都能调你的 API。

#### 加上 CORS 后的完整后端代码

```python
# main.py（在第 10 章代码基础上加 CORS）
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from models import Todo

Base.metadata.create_all(bind=engine)

app = FastAPI(title="待办事项 API")

# ✅ CORS 配置（加上这段就能解决跨域问题）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite 默认端口
        "http://localhost:3000",   # 备用端口
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 后面的接口代码不变...
```

重启后端后，前端的请求就不会再被浏览器拦截了。

> 💡 **记住这个口诀**：跨域问题是浏览器的安全限制，解决方案在后端配置。前端不需要改任何代码。

### 11.3 前后端数据流全链路拆解

学会了发请求和解决跨域，现在需要建立一个**完整的心智模型**——一次前后端交互到底经历了哪些步骤？理解这个链路，debug 时才能快速定位问题出在哪一环。

#### 一次"创建待办"的完整链路

以用户点击"添加待办"按钮为例：

```
┌──────────────────────────────────────────────────────────┐
│  ① 用户操作                                               │
│  用户在输入框输入 "学习 React"，点击 "添加" 按钮              │
└───────────────────────┬──────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│  ② React 事件函数                                         │
│  handleAdd 函数被调用                                      │
│  → 构造请求数据：{ title: "学习 React", done: false }       │
│  → 调用 todoAPI.create("学习 React")                      │
└───────────────────────┬──────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│  ③ HTTP 请求（axios / fetch）                              │
│  POST http://localhost:8000/todos                         │
│  Headers: { Content-Type: application/json }              │
│  Body: { "title": "学习 React", "done": false }           │
└───────────────────────┬──────────────────────────────────┘
                        ↓ （网络传输）
┌──────────────────────────────────────────────────────────┐
│  ④ FastAPI 接收请求                                        │
│  → 路由匹配：POST /todos → create_todo 函数               │
│  → Pydantic 校验请求数据                                   │
│  → 创建 Todo 对象                                         │
└───────────────────────┬──────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│  ⑤ 数据库操作                                              │
│  → db.add(new_todo)                                       │
│  → db.commit()                                            │
│  → SQLite 执行: INSERT INTO todos (title, done) VALUES ... │
└───────────────────────┬──────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│  ⑥ 后端返回响应                                            │
│  HTTP 201 Created                                         │
│  Body: { "id": 4, "title": "学习 React", "done": false,   │
│          "created_at": "2025-06-15 14:30" }                │
└───────────────────────┬──────────────────────────────────┘
                        ↓ （网络传输）
┌──────────────────────────────────────────────────────────┐
│  ⑦ React 处理响应                                          │
│  → 接收返回的数据                                           │
│  → setTodos(prev => [...prev, data])  更新状态             │
│  → React 自动重新渲染，页面显示新的待办                       │
└──────────────────────────────────────────────────────────┘
```

#### Debug 定位指南

当联调出了问题，按这个链路逐步排查：

| 出错步骤 | 表现 | 排查方法 |
|---|---|---|
| ③ 请求没发出 | 浏览器控制台无网络请求 | 检查事件函数是否被调用了 |
| ③ CORS 错误 | 控制台红色跨域报错 | 检查后端 CORS 配置 |
| ④ 404 Not Found | 返回 404 | 检查请求的 URL 和方法是否匹配 |
| ④ 422 Unprocessable | 返回 422 | 请求参数格式不对，检查 body |
| ⑤ 500 服务器错误 | 返回 500 | 检查后端终端的错误日志 |
| ⑦ 数据没显示 | 请求成功但页面没变 | 检查 setState 是否正确调用 |

> 💡 **最重要的 Debug 工具**：浏览器开发者工具（`F12`）→ Network 标签页。你可以看到每一个请求的 URL、请求头、请求体、响应状态码、响应数据——一目了然。

### 11.4 接口调试：浏览器 DevTools 与 API 测试工具

在前后端联调时，你需要工具来**独立测试后端接口**——不依赖前端界面，直接发请求验证后端是否工作正常。

#### 工具一：浏览器开发者工具（最常用）

按 `F12` 打开，切到 **Network** 标签页：

```
开发者工具 → Network 标签页

你能看到的信息：
┌────────────────────────────────────────────────┐
│  Name           Method   Status   Time         │
│  todos          GET      200      45ms         │
│  todos          POST     201      120ms        │
│  todos/3        DELETE   200      30ms         │
└────────────────────────────────────────────────┘

点击某个请求，可以看到：
• Headers：请求头、响应头
• Payload：请求体（你发了什么数据）
• Response：响应体（后端返回了什么数据）
• Timing：耗时分析
```

**常用场景：**
- 检查请求是否发出去了
- 查看请求参数是否正确
- 查看后端返回的数据格式
- 查看状态码（200/404/500...）

#### 工具二：FastAPI 自带文档（推荐新手使用）

启动后端后访问 `http://localhost:8000/docs`，FastAPI 自动生成的交互式文档可以直接测试每个接口：

```
1. 找到你要测试的接口（如 POST /todos）
2. 点击 "Try it out" 按钮
3. 在 Request body 中填入 JSON 数据
4. 点击 "Execute"
5. 下方立即显示响应结果
```

这是最方便的后端测试方式——零安装、零配置。

#### 工具三：Thunder Client（VS Code 插件）

如果你更喜欢在编辑器中测试 API：

```
1. 在 VS Code / Cursor 中搜索安装 "Thunder Client" 插件
2. 点击左侧闪电图标打开
3. 新建请求，填入 URL 和参数
4. 点击 Send，查看响应
```

**Thunder Client vs FastAPI 文档对比：**

| | FastAPI /docs | Thunder Client |
|---|---|---|
| 安装 | ✅ 不需要 | 需要装 VS Code 插件 |
| 自动识别接口 | ✅ 自动列出所有接口 | 需要手动输入 URL |
| 保存请求历史 | ❌ 刷新页面就没了 | ✅ 可以保存请求集合 |
| 适合 | 快速测试单个接口 | 管理复杂项目的多个 API |

> 💡 建议：开发初期用 FastAPI `/docs` 快速验证；项目变大后用 Thunder Client 管理所有接口。

### 11.5 实战：React + FastAPI 完成完整的待办应用

终于到了激动人心的时刻——把前面所有章节学到的东西串起来，做一个**前后端完全打通的真·全栈应用**。

#### 项目全景

```
项目根目录/
├── backend/                 ← 后端（第 9-10 章的代码）
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   └── todos.db
└── frontend/                ← 前端（第 6-7 章的代码）
    └── src/
        ├── services/
        │   └── api.js       ← API 请求封装
        ├── components/
        │   └── TodoItem.jsx ← 单条待办组件
        ├── pages/
        │   └── TodoPage.jsx ← 待办页面
        └── App.jsx
```

#### Step 1：启动后端

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
# 后端运行在 http://localhost:8000
```

确保后端已配置 CORS（参考 11.2 节）。

#### Step 2：创建前端 API 封装

```javascript
// frontend/src/services/api.js
const API_BASE = "http://localhost:8000";

export const todoAPI = {
    getAll: async () => {
        const res = await fetch(`${API_BASE}/todos`);
        return res.json();
    },
    
    create: async (title) => {
        const res = await fetch(`${API_BASE}/todos`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, done: false })
        });
        return res.json();
    },
    
    update: async (id, data) => {
        const res = await fetch(`${API_BASE}/todos/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        return res.json();
    },
    
    delete: async (id) => {
        await fetch(`${API_BASE}/todos/${id}`, { method: "DELETE" });
    }
};
```

#### Step 3：待办列表页面

```jsx
// frontend/src/pages/TodoPage.jsx
import { useState, useEffect } from "react";
import { todoAPI } from "../services/api";

const TodoPage = () => {
    const [todos, setTodos] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(true);
    
    // 页面加载时获取待办列表
    useEffect(() => {
        todoAPI.getAll()
            .then(data => setTodos(data))
            .finally(() => setLoading(false));
    }, []);
    
    // 添加待办
    const handleAdd = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;
        
        const newTodo = await todoAPI.create(input);
        setTodos(prev => [...prev, newTodo]);
        setInput("");
    };
    
    // 切换完成状态
    const handleToggle = async (todo) => {
        const updated = await todoAPI.update(todo.id, {
            title: todo.title,
            done: !todo.done
        });
        setTodos(prev => prev.map(t => t.id === todo.id ? updated : t));
    };
    
    // 删除待办
    const handleDelete = async (id) => {
        await todoAPI.delete(id);
        setTodos(prev => prev.filter(t => t.id !== id));
    };
    
    if (loading) return <p>加载中...</p>;
    
    return (
        <div className="todo-container">
            <h1>📝 待办事项</h1>
            
            {/* 添加表单 */}
            <form onSubmit={handleAdd} className="todo-form">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="输入新的待办..."
                />
                <button type="submit">添加</button>
            </form>
            
            {/* 待办列表 */}
            <ul className="todo-list">
                {todos.map(todo => (
                    <li key={todo.id} className={todo.done ? "done" : ""}>
                        <span onClick={() => handleToggle(todo)}>
                            {todo.done ? "✅" : "⬜"} {todo.title}
                        </span>
                        <button onClick={() => handleDelete(todo.id)}>🗑️</button>
                    </li>
                ))}
            </ul>
            
            {todos.length === 0 && <p className="empty">还没有待办，添加一个吧！</p>}
        </div>
    );
};

export default TodoPage;
```

#### Step 4：启动前端

```bash
cd frontend
npm run dev
# 前端运行在 http://localhost:5173
```

打开浏览器访问 `http://localhost:5173`，你会看到：
1. 页面自动从后端加载待办列表
2. 输入文字点"添加"，数据写入数据库
3. 点击待办可以切换完成状态
4. 点 🗑️ 可以删除
5. **刷新页面，数据不丢失**——因为数据存在数据库里！

#### 你刚刚完成了什么？

```
前端（React）                    后端（FastAPI）              数据库（SQLite）
┌──────────┐    HTTP 请求        ┌──────────┐    SQL 操作     ┌──────────┐
│ 用户界面   │ ──────────────→   │ API 接口  │ ────────────→ │ todos 表  │
│ 状态管理   │ ←──────────────   │ 数据校验  │ ←────────────  │ 持久存储  │
│ 事件处理   │    HTTP 响应      │ CORS 配置 │    查询结果    │          │
└──────────┘                    └──────────┘               └──────────┘
```

**这就是一个标准的全栈应用！** 从这里开始，你只需要把"待办事项"替换成"AI 对话"，就是一个 AI 应用的雏形了。

#### 本章小结

```
✅ 你已经掌握了：
  • 前端发送 HTTP 请求：fetch 和 axios 的用法
  • API 请求封装：统一管理后端地址和请求逻辑
  • CORS 跨域问题：原因理解 + FastAPI 一行配置解决
  • 前后端数据流：从用户操作到数据库的完整链路
  • 接口调试：浏览器 Network、FastAPI /docs、Thunder Client
  • 全栈实战：React + FastAPI + SQLite 完整应用

🎯 下一章你将学习：
  • LLM API 调用与 Prompt Engineering——让你的应用拥有"AI 大脑"
```

---

## 12. LLM API 调用与 Prompt Engineering

终于来到了这门课程最核心的部分——**调用大模型 API**。

回看一下你的进度：前 11 章你学了完整的全栈开发技能（前端 React + 后端 FastAPI + 数据库 SQLite + 前后端联调），你已经能独立做出一个完整的 Web 应用了。现在，是时候给你的应用装上"AI 大脑"了——接下来的章节将把你从一个"全栈开发者"升级为"AI 应用开发者"。

本章你将学会调用 LLM API、理解关键参数、实现流式输出、以及最重要的——**Prompt Engineering**。

---

### 12.1 第一次调用大模型 API

#### 什么是大模型 API？

大模型 API 其实就是一个普通的 HTTP 接口——你发一段文字过去（Prompt），它返回 AI 生成的文字（Completion）。本质上和你调用第 9 章的待办 API 没有区别。

```
你的应用                              大模型服务商
┌──────────┐   POST /chat/completions  ┌──────────────┐
│ 发送 Prompt│ ──────────────────────→  │ GPT-4 / 豆包   │
│           │                          │ 处理文字        │
│ 接收回复   │ ←──────────────────────  │ 返回 AI 回复    │
└──────────┘   JSON 响应               └──────────────┘
```

#### API Key：你的"通行证"

调用大模型 API 需要一个 **API Key**（密钥），用来标识你的身份和计费。

**获取 API Key 的方式：**

| 平台 | 获取方式 | 特点 |
|---|---|---|
| **OpenAI** | [platform.openai.com](https://platform.openai.com) | 全球最强模型，需要海外支付方式 |
| **豆包（火山引擎）** | [console.volcengine.com](https://console.volcengine.com) | 国内首选，无需翻墙，价格便宜 |
| **DeepSeek** | [platform.deepseek.com](https://platform.deepseek.com) | 国产开源模型，性价比极高 |
| **阿里通义千问** | [dashscope.aliyun.com](https://dashscope.aliyun.com) | 阿里云平台，企业常用 |

> 💡 **好消息**：几乎所有国内大模型平台都兼容 OpenAI 的 API 格式。你只需要换一下 API 地址和 Key，代码几乎不用改。

#### 安装 OpenAI SDK

```bash
pip install openai
```

这个库不只支持 OpenAI，任何兼容 OpenAI 格式的 API 都能用（豆包、DeepSeek、通义千问等）。

#### 第一次调用

```python
from openai import OpenAI

# 创建客户端（以豆包为例）
client = OpenAI(
    api_key="your-api-key-here",           # 你的 API Key
    base_url="https://ark.cn-beijing.volces.com/api/v3"  # 豆包的 API 地址
)

# 如果用 OpenAI 官方：
# client = OpenAI(api_key="sk-xxxxx")  # 不需要 base_url

# 发送请求
response = client.chat.completions.create(
    model="doubao-pro-32k",     # 模型名称
    messages=[
        {"role": "user", "content": "用一句话解释什么是 API"}
    ]
)

# 获取 AI 的回复
print(response.choices[0].message.content)
# 输出类似：API 就是两个程序之间约定好的"对话接口"，一方发请求，另一方返回数据。
```

#### 消息格式：messages 数组

大模型 API 的核心输入是一个 **messages 数组**，每条消息有两个字段：

```python
messages = [
    {"role": "system", "content": "你是一个专业的翻译助手"},     # 系统指令
    {"role": "user", "content": "把'Hello World'翻译成中文"},    # 用户输入
    {"role": "assistant", "content": "你好，世界"},              # AI 的回复
    {"role": "user", "content": "翻译成日语呢？"},              # 用户追问
]
```

**三种角色：**

| 角色 | 含义 | 作用 |
|---|---|---|
| `system` | 系统指令 | 设定 AI 的身份、行为规则（只在开头出现一次） |
| `user` | 用户消息 | 用户说的话 |
| `assistant` | AI 回复 | AI 之前的回复（用于多轮对话） |

> ⚠️ **API Key 安全**：永远不要把 API Key 写在前端代码里！应该放在后端的环境变量中。

```python
# ❌ 危险：API Key 写在代码里
client = OpenAI(api_key="sk-1234567890")

# ✅ 安全：从环境变量读取
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

```bash
# 在终端设置环境变量（或写在 .env 文件中）
export OPENAI_API_KEY="your-api-key-here"
```

### 12.2 核心参数解析：model、temperature、max_tokens

调用 API 时，除了 `messages`，还有几个关键参数直接影响 AI 的输出质量。理解它们，才能让 AI 按你的预期工作。

#### 完整参数示例

```python
response = client.chat.completions.create(
    model="doubao-pro-32k",        # 使用哪个模型
    messages=[...],                 # 对话内容
    temperature=0.7,                # 创造性（0~2）
    max_tokens=1000,                # 最大输出长度
    top_p=0.9,                      # 核采样（通常不需要调）
    stream=False,                   # 是否流式输出（下一节详讲）
)
```

#### model：选哪个模型

不同模型能力不同、价格不同，按需选择：

| 模型 | 能力 | 速度 | 价格 | 适用场景 |
|---|---|---|---|---|
| `gpt-4o` | ⭐⭐⭐⭐⭐ | 中 | 贵 | 复杂推理、高质量生成 |
| `gpt-4o-mini` | ⭐⭐⭐⭐ | 快 | 便宜 | 日常任务、性价比之选 |
| `doubao-pro-32k` | ⭐⭐⭐⭐ | 快 | 便宜 | 国内项目首选 |
| `deepseek-chat` | ⭐⭐⭐⭐ | 快 | 极便宜 | 代码生成、推理任务 |

> 💡 **实际建议**：开发阶段用便宜的模型（`gpt-4o-mini` / `doubao-pro`），效果不够好再换贵的。

#### temperature：控制"创造性"

`temperature` 是最重要的参数，控制 AI 输出的随机性：

```
temperature = 0.0  →  确定性最高，每次输出几乎一样（适合翻译、提取）
temperature = 0.7  →  适度创造性（推荐默认值）
temperature = 1.5  →  非常随机，可能出现意想不到的内容（适合创意写作）
```

**不同场景的推荐值：**

| 场景 | 推荐 temperature | 原因 |
|---|---|---|
| 翻译 | 0.0 ~ 0.3 | 翻译结果应该稳定、准确 |
| 知识问答 | 0.3 ~ 0.5 | 事实性回答要准确 |
| 聊天对话 | 0.7 ~ 0.9 | 自然对话需要一些变化 |
| 创意写作 | 1.0 ~ 1.5 | 需要多样性和创造力 |
| 代码生成 | 0.0 ~ 0.3 | 代码要严谨、可执行 |

```python
# 翻译场景：temperature 低
response = client.chat.completions.create(
    model="doubao-pro-32k",
    messages=[{"role": "user", "content": "翻译：Hello World"}],
    temperature=0.1    # 几乎不随机
)

# 写故事：temperature 高
response = client.chat.completions.create(
    model="doubao-pro-32k",
    messages=[{"role": "user", "content": "写一个关于 AI 的短故事"}],
    temperature=1.2    # 充分发挥创造力
)
```

#### max_tokens：控制输出长度

`max_tokens` 限制 AI 最多输出多少个 Token（大约 1 个中文字 ≈ 1~2 个 Token）。

```python
# 限制短回复
response = client.chat.completions.create(
    model="doubao-pro-32k",
    messages=[{"role": "user", "content": "用一句话总结 Python 的特点"}],
    max_tokens=100     # 最多输出约 50~100 个汉字
)

# 允许长回复
response = client.chat.completions.create(
    model="doubao-pro-32k",
    messages=[{"role": "user", "content": "写一篇 Python 入门教程"}],
    max_tokens=4096    # 允许长篇输出
)
```

> ⚠️ Token 是有成本的——输入和输出的 Token 数量决定了你要付多少钱。`max_tokens` 设得越大，潜在花费越高。

#### 理解 Token 和计费

```
Token ≈ 语言的最小单元
  英文：1 个单词 ≈ 1~2 个 Token
  中文：1 个汉字 ≈ 1~2 个 Token

计费公式：
  费用 = (输入 Token 数 × 输入单价) + (输出 Token 数 × 输出单价)
```

**查看实际消耗：**

```python
response = client.chat.completions.create(...)

# 查看 Token 消耗
print(response.usage)
# CompletionUsage(prompt_tokens=25, completion_tokens=48, total_tokens=73)
# 输入用了 25 个 Token，输出用了 48 个，总共 73 个
```

### 12.3 流式输出（SSE）：实现打字机效果

你用 ChatGPT 时看到的"逐字打出"效果，不是前端动画——而是后端**真的在一个字一个字地返回数据**。这就是流式输出。

#### 为什么需要流式输出？

```
非流式（一次性返回）：
  用户发送问题 → 等待 3~10 秒 → 一次性显示完整回答
  用户感受：😐 漫长的空白等待

流式（逐字返回）：
  用户发送问题 → 0.5 秒后开始显示 → 文字逐渐"打"出来
  用户感受：😊 AI 在"思考并说话"，体验好很多
```

#### 后端：Python 流式调用

只需要加一个参数 `stream=True`：

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

# 流式调用
stream = client.chat.completions.create(
    model="doubao-pro-32k",
    messages=[{"role": "user", "content": "写一首关于编程的诗"}],
    stream=True       # ← 开启流式
)

# 逐块接收
for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)  # 逐字打印，不换行
```

运行后你会看到文字一个一个"蹦"出来，而不是一次全出来。

#### 后端：FastAPI 流式接口

用 FastAPI 的 `StreamingResponse` 把流式数据转发给前端：

```python
# main.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    def generate():
        stream = client.chat.completions.create(
            model="doubao-pro-32k",
            messages=[
                {"role": "system", "content": "你是一个有用的 AI 助手"},
                {"role": "user", "content": request.message}
            ],
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {content}\n\n"   # SSE 格式
        yield "data: [DONE]\n\n"               # 结束标记
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"         # SSE 协议
    )
```

#### 前端：接收流式数据

```javascript
// 前端接收 SSE 流式响应
const sendMessage = async (message) => {
    const response = await fetch("http://localhost:8000/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let aiReply = "";
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const text = decoder.decode(value);
        // 解析 SSE 格式：每行以 "data: " 开头
        const lines = text.split("\n").filter(line => line.startsWith("data: "));
        
        for (const line of lines) {
            const content = line.replace("data: ", "");
            if (content === "[DONE]") break;
            
            aiReply += content;
            // 更新 React 状态，实现逐字显示
            setReply(aiReply);
        }
    }
};
```

#### 流式 vs 非流式对比

| | 非流式 | 流式 |
|---|---|---|
| **用户体验** | 长时间等待后一次性显示 | 逐字"打"出来，感觉更快 |
| **首字时间** | 等全部生成完 | 约 0.5 秒就开始显示 |
| **适用场景** | 短回复、后台处理 | 聊天界面、实时交互 |
| **实现复杂度** | 简单 | 稍复杂（需要处理 SSE） |

> 💡 **实际开发建议**：面向用户的聊天界面一定要用流式输出，后台数据处理用非流式更简单。

### 12.4 Prompt Engineering：让 AI 精准输出的技术

Prompt Engineering（提示词工程）是 AI 应用开发中**投入产出比最高的技能**。同样的模型，好的 Prompt 和差的 Prompt，输出质量天差地别。

#### 差 Prompt vs 好 Prompt

```python
# ❌ 差 Prompt：模糊、没约束
messages = [{"role": "user", "content": "帮我翻译一下"}]
# AI：翻译什么？请提供需要翻译的内容。

# ✅ 好 Prompt：角色 + 任务 + 格式 + 约束
messages = [
    {"role": "system", "content": """你是一个专业的中英翻译助手。
规则：
- 用户输入中文时，翻译成英文
- 用户输入英文时，翻译成中文
- 只输出翻译结果，不要解释
- 保持原文的语气和风格"""},
    {"role": "user", "content": "这个功能太赞了！"}
]
# AI：This feature is awesome!
```

#### 结构化 Prompt 的六大要素

一个高质量的 Prompt 通常包含以下要素（不需要全部使用，按需组合）：

```
┌─────────────────────────────────────────────┐
│  ① 角色（Role）    → 你是谁？                 │
│  ② 任务（Task）    → 要做什么？               │
│  ③ 格式（Format）  → 输出什么格式？            │
│  ④ 约束（Rules）   → 不能做什么？能做什么？     │
│  ⑤ 示例（Few-shot）→ 给几个参考案例            │
│  ⑥ 思维链（CoT）   → 让 AI 分步思考           │
└─────────────────────────────────────────────┘
```

#### ① 角色（Role）

告诉 AI 它是谁，决定了它的"人格"和专业领域：

```python
# 通用助手
{"role": "system", "content": "你是一个有用的 AI 助手"}

# 专业角色
{"role": "system", "content": "你是一位资深的 Python 后端工程师，有 10 年经验"}

# 特定风格
{"role": "system", "content": "你是一个面向初学者的编程导师，解释要通俗易懂，多用类比"}
```

#### ② 任务（Task）

清晰描述 AI 需要完成什么：

```python
# ❌ 模糊任务
"帮我处理一下这段文字"

# ✅ 清晰任务
"将以下中文产品描述翻译成英文，适合在 Amazon 商品页面展示，语气要专业但不生硬"
```

#### ③ 格式（Format）

指定输出的格式，AI 会严格遵守：

```python
system_prompt = """你是一个数据提取助手。
从用户提供的文本中提取关键信息，按以下 JSON 格式输出：

{
    "name": "姓名",
    "age": 年龄（数字）,
    "skills": ["技能1", "技能2"]
}

只输出 JSON，不要添加任何其他文字。"""
```

> 💡 要求 AI 输出 JSON 是非常实用的技巧——结构化数据可以直接被程序解析和使用。

#### ④ 约束（Rules）

设定边界，告诉 AI 什么能做、什么不能做：

```python
system_prompt = """你是一个客服助手。

规则：
- 只回答和产品相关的问题
- 如果用户的问题和产品无关，礼貌地引导回产品话题
- 不要编造产品信息，不确定的说"我不太确定，建议您联系人工客服"
- 回复长度控制在 100 字以内
- 使用友好、专业的语气"""
```

#### ⑤ Few-shot：给几个示例

Few-shot 是最强大的 Prompt 技巧之一——通过提供几个"输入→输出"的示例，让 AI 准确理解你的意图：

```python
messages = [
    {"role": "system", "content": "你是一个商品分类助手"},
    
    # 示例 1
    {"role": "user", "content": "iPhone 15 Pro Max"},
    {"role": "assistant", "content": "分类：电子产品 > 手机"},
    
    # 示例 2
    {"role": "user", "content": "耐克 Air Max 跑鞋"},
    {"role": "assistant", "content": "分类：服饰 > 运动鞋"},
    
    # 示例 3
    {"role": "user", "content": "雅诗兰黛小棕瓶精华"},
    {"role": "assistant", "content": "分类：美妆 > 护肤品"},
    
    # 实际输入
    {"role": "user", "content": "索尼 WH-1000XM5 降噪耳机"},
]
# AI 会学习示例的模式，输出：分类：电子产品 > 耳机
```

**Few-shot 的数量推荐：**
- 简单任务：2~3 个示例
- 复杂任务：3~5 个示例
- 示例要覆盖不同的情况和边界

#### ⑥ CoT（Chain of Thought）：让 AI 分步思考

对于需要推理的复杂问题，让 AI "先思考、再回答"能显著提升准确率：

```python
# ❌ 直接问，容易出错
{"role": "user", "content": "小明有 15 个苹果，给了小红 3 个，又买了 8 个，吃了 2 个，还剩几个？"}

# ✅ 要求分步推理
{"role": "user", "content": """小明有 15 个苹果，给了小红 3 个，又买了 8 个，吃了 2 个，还剩几个？

请一步一步思考，先列出每一步的计算过程，最后给出答案。"""}
```

AI 的分步回答会更准确：

```
1. 初始：15 个
2. 给了小红 3 个：15 - 3 = 12 个
3. 又买了 8 个：12 + 8 = 20 个
4. 吃了 2 个：20 - 2 = 18 个

答案：还剩 18 个苹果。
```

#### Prompt 模板：通用公式

```python
system_prompt = """
# 角色
你是{角色描述}。

# 任务
{具体任务说明}

# 输出格式
{期望的格式}

# 规则
- {规则1}
- {规则2}
- {规则3}

# 示例（可选）
输入：{示例输入}
输出：{示例输出}
"""
```

> 💡 **Prompt 是需要迭代的**。写完第一版后，测试效果，根据 AI 的实际输出不断调整。好的 Prompt 往往是改出来的，不是一次写好的。

### 12.5 实战：做一个"AI 翻译助手"（前后端完整）

综合本章所有知识，做一个真正能用的 AI 应用——**中英互译助手**。

#### 后端：翻译 API

```python
# main.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI(title="AI 翻译助手")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
)

SYSTEM_PROMPT = """你是一个专业的翻译助手。

规则：
- 用户输入中文时，翻译成地道的英文
- 用户输入英文时，翻译成自然的中文
- 只输出翻译结果，不要添加解释、注释或其他文字
- 保持原文的语气、风格和格式
- 如果原文包含专业术语，翻译后在括号中标注原文"""

class TranslateRequest(BaseModel):
    text: str

# 非流式版本（简单）
@app.post("/translate")
def translate(request: TranslateRequest):
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request.text}
        ],
        temperature=0.1    # 翻译要稳定
    )
    return {
        "result": response.choices[0].message.content,
        "tokens": response.usage.total_tokens
    }

# 流式版本（用户体验更好）
@app.post("/translate/stream")
def translate_stream(request: TranslateRequest):
    def generate():
        stream = client.chat.completions.create(
            model="doubao-pro-32k",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.text}
            ],
            temperature=0.1,
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {content}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

#### 前端：翻译界面

```jsx
// TranslatePage.jsx
import { useState } from "react";

const TranslatePage = () => {
    const [input, setInput] = useState("");
    const [result, setResult] = useState("");
    const [loading, setLoading] = useState(false);
    
    const handleTranslate = async () => {
        if (!input.trim()) return;
        setResult("");
        setLoading(true);
        
        try {
            // 使用流式接口
            const response = await fetch("http://localhost:8000/translate/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: input })
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let translated = "";
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const text = decoder.decode(value);
                const lines = text.split("\n").filter(l => l.startsWith("data: "));
                for (const line of lines) {
                    const content = line.replace("data: ", "");
                    if (content === "[DONE]") break;
                    translated += content;
                    setResult(translated);
                }
            }
        } catch (error) {
            setResult("翻译失败，请检查后端是否运行");
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div className="translate-container">
            <h1>🌐 AI 翻译助手</h1>
            <p className="subtitle">输入中文自动翻译成英文，输入英文自动翻译成中文</p>
            
            <div className="translate-panels">
                <div className="panel">
                    <h3>原文</h3>
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="在这里输入要翻译的文字..."
                        rows={8}
                    />
                </div>
                <div className="panel">
                    <h3>译文</h3>
                    <div className="result-box">
                        {result || (loading ? "翻译中..." : "译文将显示在这里")}
                    </div>
                </div>
            </div>
            
            <button onClick={handleTranslate} disabled={loading || !input.trim()}>
                {loading ? "翻译中..." : "翻译"}
            </button>
        </div>
    );
};

export default TranslatePage;
```

#### 运行测试

```bash
# 后端（设置环境变量后启动）
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
uvicorn main:app --reload

# 前端
npm run dev
```

输入"React 是一个用于构建用户界面的 JavaScript 库"，你会看到翻译结果逐字"打"出来：

```
React is a JavaScript library for building user interfaces.
```

**恭喜！你刚刚做出了自己的第一个 AI 应用！** 🎉

#### 本章小结

```
✅ 你已经掌握了：
  • 大模型 API 调用：OpenAI SDK、API Key、messages 格式
  • 核心参数：model（选模型）、temperature（控创造性）、max_tokens（控长度）
  • 流式输出：后端 StreamingResponse + 前端 ReadableStream
  • Prompt Engineering 六大要素：角色、任务、格式、约束、Few-shot、CoT
  • 完整实战：AI 翻译助手（前后端 + 流式输出 + Prompt 设计）

🎯 下一章你将学习：
  • 对话管理与上下文工程——让 AI "记住"之前的对话
```

---

## 13. 对话管理与上下文工程

上一章你学会了调用 LLM API，但你会发现一个问题：**AI 不记得之前说过什么**。你说"我叫张三"，下一轮问"我叫什么"，AI 一脸茫然。这不是 AI 笨——而是 API 的工作方式决定的。本章教你如何让 AI 拥有"记忆"。

---

### 13.1 为什么 AI "记不住"：无状态 API 的本质

#### 一个实验

```python
# 第一次调用
response1 = client.chat.completions.create(
    model="doubao-pro-32k",
    messages=[{"role": "user", "content": "我叫张三，请记住我的名字"}]
)
print(response1.choices[0].message.content)
# AI：好的，张三，我记住了！

# 第二次调用
response2 = client.chat.completions.create(
    model="doubao-pro-32k",
    messages=[{"role": "user", "content": "我叫什么名字？"}]
)
print(response2.choices[0].message.content)
# AI：抱歉，您还没有告诉我您的名字呢。
```

**为什么？** 因为每次 API 调用都是**完全独立**的。AI 不会自动保存之前的对话。

#### 无状态的本质

```
你以为的 AI：
  有一个"大脑"，能记住和你的所有对话
  
实际的 AI API：
  每次调用都是一张白纸，完全不知道之前发生了什么
  唯一的"记忆"来源 = 你在 messages 里传了什么
```

这就像一个**失忆症患者**——每次见面都不认识你。唯一的解决办法：每次见面时，先把之前的对话记录念给他听。

#### 解决方案：把对话历史传给 AI

```python
# ✅ 正确做法：把完整对话历史放在 messages 里
response = client.chat.completions.create(
    model="doubao-pro-32k",
    messages=[
        {"role": "user", "content": "我叫张三"},
        {"role": "assistant", "content": "好的，张三，你好！我记住了。"},  # 上一轮 AI 的回复
        {"role": "user", "content": "我叫什么名字？"}                    # 本轮问题
    ]
)
print(response.choices[0].message.content)
# AI：你叫张三！
```

**核心原理：AI 的"记忆" = 你在 messages 数组里传入的对话历史。**

#### 这带来了两个问题

```
问题 1：对话越来越长，Token 消耗越来越大
  第 1 轮：发送 50 Token
  第 10 轮：发送 500 Token（因为要带上前 9 轮的历史）
  第 100 轮：发送 5000 Token → 💸 成本爆炸 + 超出模型上下文窗口

问题 2：对话历史存在哪？
  前端？刷新页面就没了
  后端内存？重启服务就没了
  → 需要存数据库
```

这两个问题就是本章后续要解决的。

### 13.2 对话历史管理策略：消息列表、滑动窗口、摘要压缩

对话越来越长怎么办？三种策略，从简单到高级。

#### 策略一：完整消息列表（最简单）

把所有对话历史全部传给 AI：

```python
# 用一个列表保存所有对话
conversation = [
    {"role": "system", "content": "你是一个有用的 AI 助手"}
]

def chat(user_message):
    # 1. 把用户消息加入历史
    conversation.append({"role": "user", "content": user_message})
    
    # 2. 把完整历史发给 AI
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=conversation
    )
    
    # 3. 把 AI 回复也加入历史
    ai_reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": ai_reply})
    
    return ai_reply

# 使用
print(chat("我叫张三"))        # AI 知道你叫张三
print(chat("我叫什么？"))      # AI 记得你叫张三
print(chat("我们聊了几轮了？"))  # AI 知道已经聊了 3 轮
```

**优点**：简单，AI 拥有完整记忆
**缺点**：对话太长会超出上下文窗口 + 成本爆炸

#### 策略二：滑动窗口（推荐）

只保留最近 N 轮对话，丢弃更早的：

```python
MAX_HISTORY = 20  # 最多保留最近 20 条消息

def chat_with_window(user_message):
    conversation.append({"role": "user", "content": user_message})
    
    # 只取最近 N 条（但 system 消息始终保留）
    system_msg = conversation[0]  # system 消息
    recent_msgs = conversation[1:][-MAX_HISTORY:]  # 最近的对话
    messages_to_send = [system_msg] + recent_msgs
    
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=messages_to_send
    )
    
    ai_reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": ai_reply})
    return ai_reply
```

```
对话历史（假设 MAX_HISTORY = 6）：

完整历史：[sys, u1, a1, u2, a2, u3, a3, u4, a4, u5, a5]
                                              ↑ 窗口起点
发送给 AI：[sys, u3, a3, u4, a4, u5, a5]
                 ← 只发最近 6 条 →
```

**优点**：成本可控，不会超出上下文窗口
**缺点**：AI 会"忘记"早期对话

#### 策略三：摘要压缩（高级）

把早期对话压缩成一段摘要，既节省 Token 又保留关键信息：

```python
def compress_history(messages):
    """用 AI 把长对话压缩成一段摘要"""
    summary_prompt = f"""请将以下对话总结为一段简短的摘要，保留关键信息（用户姓名、偏好、讨论主题等）：

{format_messages(messages)}

摘要："""
    
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=[{"role": "user", "content": summary_prompt}],
        max_tokens=200
    )
    return response.choices[0].message.content

def chat_with_summary(user_message):
    conversation.append({"role": "user", "content": user_message})
    
    # 如果历史超过 30 条，压缩前面的部分
    if len(conversation) > 30:
        old_messages = conversation[1:20]      # 取早期 20 条
        summary = compress_history(old_messages)
        
        # 用摘要替换早期对话
        conversation[1:20] = [
            {"role": "system", "content": f"前期对话摘要：{summary}"}
        ]
    
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=conversation
    )
    
    ai_reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": ai_reply})
    return ai_reply
```

```
压缩前：[sys, u1, a1, u2, a2, ..., u15, a15, u16, a16, ..., u20, a20]
                ← 20 条早期对话 →          ← 最近对话 →

压缩后：[sys, summary("用户张三，讨论了..."), u16, a16, ..., u20, a20]
              ← 1 条摘要（~50 Token） →    ← 最近对话 →
```

#### 三种策略对比

| | 完整列表 | 滑动窗口 | 摘要压缩 |
|---|---|---|---|
| **复杂度** | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Token 成本** | 高（持续增长） | 低（固定上限） | 中（额外压缩调用） |
| **记忆完整性** | ✅ 完整 | ❌ 忘记早期 | ✅ 保留关键信息 |
| **适用场景** | 短对话（<20 轮） | 日常聊天 | 长时间会话 |
| **推荐度** | 入门使用 | ⭐⭐⭐⭐⭐ | 高级场景 |

> 💡 **实际建议**：大多数项目用滑动窗口就够了。如果需要 AI 记住用户的长期偏好，可以用摘要压缩或单独维护一份"用户画像"。

### 13.3 Context Engineering：上下文组装的艺术

上一节解决了"记忆长度"的问题，这一节解决"记忆质量"的问题。**Context Engineering（上下文工程）** 是指：如何精心组装发送给 AI 的 messages，让 AI 在有限的上下文窗口内获得最有效的信息。

#### messages 的组装顺序

一个精心设计的 messages 数组应该这样组装：

```python
messages = [
    # ① System Prompt：身份 + 规则（始终第一条）
    {"role": "system", "content": system_prompt},
    
    # ② 长期记忆：用户画像、偏好（如果有的话）
    {"role": "system", "content": f"用户信息：{user_profile}"},
    
    # ③ 外部知识：RAG 检索到的文档（第 14 章会讲）
    {"role": "system", "content": f"参考资料：{retrieved_docs}"},
    
    # ④ 对话历史摘要：早期对话的压缩
    {"role": "system", "content": f"前期摘要：{summary}"},
    
    # ⑤ 最近对话历史：滑动窗口内的完整对话
    *recent_messages,
    
    # ⑥ 当前用户输入
    {"role": "user", "content": current_input},
]
```

```
上下文窗口的"寸土寸金"原则：

┌────────────────────────────────────────┐
│  System Prompt（身份 + 规则）     ~200 Token│
│  用户画像                         ~50 Token│
│  检索到的文档                     ~500 Token│
│  对话摘要                         ~100 Token│
│  最近 10 轮对话                   ~800 Token│
│  当前用户输入                      ~50 Token│
│  ─────────────────────────────           │
│  总计                          ~1700 Token│
│  剩余给 AI 生成回复              ~2300 Token│
└────────────────────────────────────────┘
```

#### 实际的上下文组装函数

```python
def build_messages(
    user_input: str,
    conversation_history: list,
    system_prompt: str,
    user_profile: str = None,
    max_history: int = 20
) -> list:
    """组装发送给 LLM 的 messages 数组"""
    messages = []
    
    # ① System Prompt
    messages.append({"role": "system", "content": system_prompt})
    
    # ② 用户画像（可选）
    if user_profile:
        messages.append({
            "role": "system", 
            "content": f"当前用户信息：{user_profile}"
        })
    
    # ③ 最近对话历史（滑动窗口）
    recent = conversation_history[-max_history:]
    messages.extend(recent)
    
    # ④ 当前用户输入
    messages.append({"role": "user", "content": user_input})
    
    return messages
```

#### 不同应用场景的上下文设计

**场景 1：AI 客服**

```python
system_prompt = """# 角色
你是XX公司的智能客服。

# 可用信息
{product_catalog}        ← 产品信息动态注入
{faq_database}           ← 常见问题动态注入

# 规则
- 基于提供的产品信息和 FAQ 回答
- 不知道的说"我帮您转接人工客服"
"""
```

**场景 2：编程助手**

```python
system_prompt = """# 角色
你是一个 Python 编程助手。

# 当前项目上下文
项目类型：FastAPI 后端
使用的库：{installed_packages}   ← 动态注入
当前文件：{current_file_content} ← 动态注入

# 规则
- 代码要能直接运行
- 使用项目中已安装的库
"""
```

> 💡 **Context Engineering 的核心思想**：AI 的输出质量取决于你给它的输入质量。在有限的"注意力"（上下文窗口）内，放入最有价值的信息。

### 13.4 会话存储：用数据库保存对话记录

对话历史不能只存在内存里——用户刷新页面或服务器重启就全没了。和第 10 章一样，我们用数据库持久化存储。

#### 数据库模型设计

```python
# models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# 会话表（一个用户可以有多个会话）
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, default="新对话")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联：一个会话有多条消息
    messages = relationship("Message", back_populates="conversation")

# 消息表
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String, nullable=False)     # "user" / "assistant" / "system"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    conversation = relationship("Conversation", back_populates="messages")
```

#### API 接口设计

```python
# main.py（关键接口）

# 创建新会话
@app.post("/conversations")
def create_conversation(db: Session = Depends(get_db)):
    conv = Conversation(title="新对话")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {"id": conv.id, "title": conv.title}

# 获取会话的消息历史
@app.get("/conversations/{conv_id}/messages")
def get_messages(conv_id: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.created_at).all()
    return [{"role": m.role, "content": m.content} for m in messages]

# 发送消息并获取 AI 回复
@app.post("/conversations/{conv_id}/chat")
def chat(conv_id: int, request: ChatRequest, db: Session = Depends(get_db)):
    # 1. 保存用户消息
    user_msg = Message(
        conversation_id=conv_id, 
        role="user", 
        content=request.message
    )
    db.add(user_msg)
    db.commit()
    
    # 2. 加载对话历史（滑动窗口）
    history = db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.created_at).all()
    
    messages = build_messages(
        user_input=request.message,
        conversation_history=[
            {"role": m.role, "content": m.content} for m in history[:-1]
        ],
        system_prompt="你是一个有用的 AI 助手"
    )
    
    # 3. 调用 LLM
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=messages
    )
    ai_reply = response.choices[0].message.content
    
    # 4. 保存 AI 回复
    ai_msg = Message(
        conversation_id=conv_id, 
        role="assistant", 
        content=ai_reply
    )
    db.add(ai_msg)
    db.commit()
    
    return {"reply": ai_reply}
```

#### 数据流

```
用户发消息 → 保存到 messages 表
          → 从数据库加载该会话的对话历史
          → 组装 messages 数组
          → 调用 LLM API
          → 保存 AI 回复到 messages 表
          → 返回给前端
```

这样即使用户关闭浏览器、服务器重启，对话历史都不会丢失。

### 13.5 实战：做一个有"记忆"和"人格"的 AI 聊天机器人

综合本章所有知识，做一个有独特人格、能记住对话历史的聊天机器人。

#### 核心后端代码

```python
# chat_service.py — 聊天服务（核心逻辑）
from openai import OpenAI
from sqlalchemy.orm import Session
from models import Conversation, Message
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# 定义 AI 人格
PERSONA = """# 角色
你是"小智"，一个热情、博学的 AI 伙伴。

# 性格特点
- 说话风格活泼有趣，偶尔用 emoji
- 喜欢用类比解释复杂概念
- 对用户的问题充满好奇，会追问细节
- 记住用户提到的信息（名字、偏好等），在后续对话中自然引用

# 规则
- 回复控制在 200 字以内（除非用户要求详细解释）
- 不确定的事情不要编造，如实说"这个我不太确定"
- 保持友好和鼓励的态度"""

MAX_HISTORY = 20  # 滑动窗口大小

def chat_with_memory(
    conv_id: int, 
    user_input: str, 
    db: Session
) -> str:
    """带记忆的聊天函数"""
    
    # 1. 保存用户消息
    db.add(Message(conversation_id=conv_id, role="user", content=user_input))
    db.commit()
    
    # 2. 加载对话历史
    all_messages = db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.created_at).all()
    
    # 3. 组装上下文（滑动窗口）
    history = [{"role": m.role, "content": m.content} for m in all_messages]
    recent = history[-MAX_HISTORY:]
    
    messages = [
        {"role": "system", "content": PERSONA},
        *recent
    ]
    
    # 4. 调用 LLM
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=messages,
        temperature=0.8  # 聊天需要一些创造性
    )
    ai_reply = response.choices[0].message.content
    
    # 5. 保存 AI 回复
    db.add(Message(conversation_id=conv_id, role="assistant", content=ai_reply))
    db.commit()
    
    # 6. 自动生成会话标题（第一轮对话时）
    if len(all_messages) == 1:
        title = user_input[:20] + ("..." if len(user_input) > 20 else "")
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        conv.title = title
        db.commit()
    
    return ai_reply
```

#### 前端：多会话聊天界面

```jsx
// ChatPage.jsx — 核心结构
const ChatPage = () => {
    const [conversations, setConversations] = useState([]);  // 会话列表
    const [currentConvId, setCurrentConvId] = useState(null); // 当前会话
    const [messages, setMessages] = useState([]);              // 当前消息
    const [input, setInput] = useState("");
    
    // 创建新会话
    const handleNewChat = async () => {
        const res = await fetch("http://localhost:8000/conversations", {
            method: "POST"
        });
        const conv = await res.json();
        setConversations(prev => [conv, ...prev]);
        setCurrentConvId(conv.id);
        setMessages([]);
    };
    
    // 切换会话时加载历史
    const handleSelectConv = async (convId) => {
        setCurrentConvId(convId);
        const res = await fetch(
            `http://localhost:8000/conversations/${convId}/messages`
        );
        const data = await res.json();
        setMessages(data);
    };
    
    // 发送消息
    const handleSend = async () => {
        if (!input.trim() || !currentConvId) return;
        
        // 先在界面显示用户消息
        setMessages(prev => [...prev, { role: "user", content: input }]);
        const userInput = input;
        setInput("");
        
        // 发送到后端
        const res = await fetch(
            `http://localhost:8000/conversations/${currentConvId}/chat`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userInput })
            }
        );
        const { reply } = await res.json();
        setMessages(prev => [...prev, { role: "assistant", content: reply }]);
    };
    
    return (
        <div className="chat-app">
            {/* 左侧：会话列表 */}
            <aside className="sidebar">
                <button onClick={handleNewChat}>+ 新对话</button>
                {conversations.map(conv => (
                    <div key={conv.id} onClick={() => handleSelectConv(conv.id)}>
                        {conv.title}
                    </div>
                ))}
            </aside>
            
            {/* 右侧：聊天区域 */}
            <main className="chat-main">
                <div className="message-list">
                    {messages.map((msg, i) => (
                        <div key={i} className={`message ${msg.role}`}>
                            {msg.role === "assistant" ? "🤖" : "👤"} {msg.content}
                        </div>
                    ))}
                </div>
                <form onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
                    <input value={input} onChange={e => setInput(e.target.value)} />
                    <button type="submit">发送</button>
                </form>
            </main>
        </div>
    );
};
```

#### 测试对话效果

```
你：我叫小明，是一个大二学生，正在学编程
小智：小明你好！大二就开始学编程，太棒了 👍 你现在在学什么语言呀？

你：在学 Python
小智：Python 是个很棒的选择！🐍 小明，大二学 Python 正是时候。
     你是通过什么途径在学呢？网课还是学校课程？

你：你还记得我叫什么吗？
小智：当然记得呀，你是小明，大二学生，正在学 Python 呢！😄
     学得怎么样了？有遇到什么困难吗？
```

AI 不仅记住了你的名字，还记住了你的身份和正在学的内容——这就是对话管理的力量。

#### 本章小结

```
✅ 你已经掌握了：
  • 无状态 API 的本质：AI 的记忆来自 messages 数组
  • 三种历史管理策略：完整列表、滑动窗口、摘要压缩
  • Context Engineering：精心组装上下文的方法论
  • 会话存储：用数据库持久化对话记录
  • 多会话管理：创建、切换、加载历史

🎯 下一章你将学习：
  • RAG——让 AI 基于你的私有文档回答问题
```

---

## 14. RAG：给 AI 装上知识库

大模型很聪明，但它有一个致命的短板：**它不知道你的数据**。你公司的产品文档、内部 Wiki、客户资料——这些 AI 统统没见过。RAG（Retrieval-Augmented Generation，检索增强生成）就是解决这个问题的核心技术，也是当前 AI 应用中使用最广泛的架构之一。

---

### 14.1 问题场景：AI 不知道你的私有数据怎么办

#### 大模型的知识边界

```python
# 问公开知识 → AI 回答得很好
response = client.chat.completions.create(
    model="doubao-pro-32k",
    messages=[{"role": "user", "content": "Python 的 for 循环怎么用？"}]
)
# ✅ AI 能回答（训练数据中有大量 Python 教程）

# 问你公司的私有信息 → AI 一脸茫然
response = client.chat.completions.create(
    model="doubao-pro-32k",
    messages=[{"role": "user", "content": "我们公司的退货政策是什么？"}]
)
# ❌ AI 不知道（它从没见过你公司的文档）
```

#### 三种让 AI "知道"你的数据的方式

| 方式 | 原理 | 优点 | 缺点 |
|---|---|---|---|
| **微调（Fine-tuning）** | 用你的数据重新训练模型 | 效果深入 | 成本高、周期长、需要大量数据 |
| **直接塞进 Prompt** | 把文档内容放在 messages 里 | 简单直接 | 文档太大塞不下（上下文窗口有限） |
| **RAG** | 先检索相关内容，再塞进 Prompt | ✅ 灵活、低成本、可随时更新 | 需要搭建检索系统 |

#### 为什么 RAG 是最优解？

```
微调：把整本书"背"给 AI（成本高，更新慢）
直接塞 Prompt：把整本书"念"给 AI（塞不下）
RAG：用户问什么，就从书里"翻"到相关的页，念给 AI（高效！）
```

```
RAG 的核心思路：
  用户提问 → 从知识库中检索最相关的文档片段 → 把片段塞进 Prompt → AI 基于这些片段生成回答

用户："你们的退货政策是什么？"
                ↓
检索知识库 → 找到《退货政策.pdf》的第 3 段
                ↓
发给 AI："基于以下资料回答用户问题：
         资料：本公司支持 7 天无理由退货，需保持商品完好...
         问题：你们的退货政策是什么？"
                ↓
AI："根据我们的政策，您可以在收到商品 7 天内无理由退货，
     前提是商品保持完好..."
```

### 14.2 RAG 架构拆解：从文档到答案的完整链路

RAG 分为两个阶段：**索引阶段**（离线准备知识库）和**查询阶段**（在线回答问题）。

#### 全景图

```
═══════════════════ 索引阶段（离线，只做一次） ═══════════════════

  原始文档           分块              向量化             存储
┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌──────────┐
│ PDF/TXT  │ →  │ 切成小段  │ →  │ Embedding 模型│ →  │ 向量数据库 │
│ Markdown │    │ 每段200字 │    │ 文字→数字向量  │    │ Chroma    │
│ Word     │    │          │    │              │    │          │
└──────────┘    └──────────┘    └──────────────┘    └──────────┘

═══════════════════ 查询阶段（在线，每次提问） ═══════════════════

  用户提问         向量化          语义检索         组装 Prompt      生成回答
┌──────────┐   ┌─────────┐   ┌──────────┐   ┌──────────────┐   ┌────────┐
│ "退货政策 │ → │ Embedding│ → │ 在向量库中│ → │ system + 文档 │ → │ LLM    │
│  是什么？"│   │ 问题→向量│   │ 找最相似的│   │ + 用户问题    │   │ 生成回答│
└──────────┘   └─────────┘   │ 文档片段  │   └──────────────┘   └────────┘
                             └──────────┘
```

#### 索引阶段详解

**Step 1：加载文档**

```python
# 读取不同格式的文档
documents = []

# 读取 txt 文件
with open("产品手册.txt", "r", encoding="utf-8") as f:
    documents.append(f.read())

# 读取多个文件
import os
for filename in os.listdir("./docs"):
    with open(f"./docs/{filename}", "r", encoding="utf-8") as f:
        documents.append(f.read())
```

**Step 2：分块（Chunking）**

文档太长塞不进上下文窗口，需要切成小块：

```python
def split_text(text, chunk_size=500, overlap=50):
    """将长文本分割成小块"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap  # 有重叠，避免切断句子
    return chunks

# 示例
text = "这是一篇很长的产品文档..."  # 假设 5000 字
chunks = split_text(text, chunk_size=500, overlap=50)
# 得到约 11 个文本块，每块约 500 字
```

**分块策略的选择：**

| 策略 | chunk_size | 适用场景 |
|---|---|---|
| 小块（200~300 字） | 精确检索，适合 FAQ 类文档 | 问答系统 |
| 中块（500~800 字） | 平衡精确度和上下文 | 通用场景（推荐） |
| 大块（1000~2000 字） | 保留更多上下文 | 长篇分析 |

> 💡 `overlap`（重叠）很重要——如果刚好在关键信息中间切断了，重叠可以保证至少一个块包含完整信息。

**Step 3 & 4（Embedding + 存储）在后续章节详讲。**

#### 查询阶段详解

```python
def rag_query(user_question, retrieved_docs):
    """RAG 查询：把检索到的文档注入 Prompt"""
    
    # 把多个文档片段拼接
    context = "\n\n---\n\n".join(retrieved_docs)
    
    messages = [
        {"role": "system", "content": f"""你是一个专业的知识库问答助手。

请严格基于以下参考资料回答用户的问题。
如果参考资料中没有相关信息，请如实说"根据现有资料，我无法回答这个问题"。
不要编造任何不在参考资料中的内容。

参考资料：
{context}"""},
        {"role": "user", "content": user_question}
    ]
    
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=messages,
        temperature=0.3  # 知识问答要准确
    )
    return response.choices[0].message.content
```

### 14.3 Embedding 原理：把文字变成"坐标"

RAG 的核心魔法在于**语义检索**——不是关键词匹配，而是理解意思。这靠的就是 Embedding。

#### 什么是 Embedding？

Embedding 就是把一段文字变成一组数字（向量），这组数字代表了这段文字的"语义坐标"。

```
"我喜欢吃苹果"  → [0.12, -0.34, 0.78, 0.45, ...]  （一组浮点数）
"我爱吃水果"    → [0.13, -0.32, 0.76, 0.44, ...]  （和上面很接近！）
"今天天气不错"  → [0.89, 0.12, -0.45, 0.23, ...]  （和上面差很远）
```

**关键点**：意思相近的文字，Embedding 向量也相近。

#### 用类比理解

```
把文字放到一个"意义空间"的坐标系中：

                  食物相关
                    ↑
    "苹果好吃" ●   ● "水果很甜"
                  ●  "我喜欢芒果"
                    |
  ──────────────────┼──────────────────→ 科技相关
                    |
        "下雨了" ●  |         ● "Python 很好用"
                    |    ● "学习编程"
                  天气相关

语义相近的文字 → 在坐标系中距离近
语义不同的文字 → 在坐标系中距离远
```

#### 调用 Embedding API

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-key",
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

# 把文字转成向量
response = client.embeddings.create(
    model="doubao-embedding",     # Embedding 模型
    input=["我喜欢吃苹果", "我爱吃水果", "今天天气不错"]
)

# 获取向量
vec1 = response.data[0].embedding  # "我喜欢吃苹果" 的向量
vec2 = response.data[1].embedding  # "我爱吃水果" 的向量
vec3 = response.data[2].embedding  # "今天天气不错" 的向量

print(f"向量维度：{len(vec1)}")  # 通常是 1024 或 1536 维
```

#### 计算语义相似度

两个向量越接近（余弦相似度越高），两段文字的意思越接近：

```python
import numpy as np

def cosine_similarity(vec_a, vec_b):
    """计算两个向量的余弦相似度（-1~1，越大越相似）"""
    a = np.array(vec_a)
    b = np.array(vec_b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 计算相似度
sim_12 = cosine_similarity(vec1, vec2)  # "苹果" vs "水果"
sim_13 = cosine_similarity(vec1, vec3)  # "苹果" vs "天气"

print(f"苹果 vs 水果：{sim_12:.4f}")    # 约 0.92（非常相似）
print(f"苹果 vs 天气：{sim_13:.4f}")    # 约 0.31（不太相关）
```

#### 关键词匹配 vs 语义检索

| | 关键词匹配 | 语义检索（Embedding） |
|---|---|---|
| 搜"退货" → 文档写"退货" | ✅ 匹配到 | ✅ 匹配到 |
| 搜"怎么退东西" → 文档写"退货" | ❌ 关键词不同 | ✅ 理解意思相近 |
| 搜"换货政策" → 文档写"退货退款" | ❌ 关键词不同 | ✅ 理解语义相关 |

> 💡 这就是 RAG 用 Embedding 而不用关键词搜索的原因——**用户的提问方式和文档的表述方式往往不同**，但 Embedding 能捕捉到它们的语义关联。

### 14.4 向量数据库入门（Chroma）

向量数据库是专门用来存储和检索 Embedding 向量的数据库。你可以把它理解为"语义搜索引擎"——存入文档向量后，给它一个问题向量，它能快速找到最相似的文档。

#### 为什么不用普通数据库？

```
普通数据库（SQLite）：
  SELECT * FROM docs WHERE content LIKE '%退货%'
  → 只能关键词匹配，搜不到"怎么退东西"

向量数据库（Chroma）：
  query(embedding("怎么退东西"))
  → 语义检索，能找到写"退货政策"的文档
```

#### Chroma：最适合入门的向量数据库

Chroma 是一个轻量级的向量数据库，类似于向量领域的 SQLite——零配置、零安装服务。

```bash
pip install chromadb
```

#### 完整示例：存入文档 + 语义检索

```python
import chromadb
from openai import OpenAI
import os

# 1. 初始化向量数据库
chroma_client = chromadb.PersistentClient(path="./chroma_db")  # 持久化存储
collection = chroma_client.get_or_create_collection(name="my_knowledge_base")

# 2. 初始化 Embedding 客户端
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def get_embedding(texts):
    """批量获取文本的 Embedding 向量"""
    response = openai_client.embeddings.create(
        model="doubao-embedding",
        input=texts
    )
    return [item.embedding for item in response.data]

# ═══════════════ 索引阶段：存入文档 ═══════════════

documents = [
    "本公司支持 7 天无理由退货，商品需保持完好，附带原始包装和发票。",
    "退款将在收到退货商品后 3 个工作日内原路退回。",
    "如商品存在质量问题，可在 30 天内申请换货，运费由本公司承担。",
    "会员用户享受免费上门取件退货服务，非会员需自行寄回。",
    "以下商品不支持退货：定制商品、食品、贴身衣物。",
]

# 生成向量并存入 Chroma
embeddings = get_embedding(documents)
collection.add(
    ids=[f"doc_{i}" for i in range(len(documents))],
    embeddings=embeddings,
    documents=documents,
    metadatas=[{"source": "退货政策.pdf"} for _ in documents]
)

print(f"已存入 {collection.count()} 个文档片段")

# ═══════════════ 查询阶段：语义检索 ═══════════════

def search(query, top_k=3):
    """语义检索：找到最相关的 top_k 个文档片段"""
    query_embedding = get_embedding([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results["documents"][0]  # 返回最相关的文档列表

# 测试检索
results = search("怎么退东西？")
for i, doc in enumerate(results):
    print(f"相关度 #{i+1}：{doc}")
```

输出（按相关度排序）：

```
相关度 #1：本公司支持 7 天无理由退货，商品需保持完好...
相关度 #2：退款将在收到退货商品后 3 个工作日内原路退回。
相关度 #3：会员用户享受免费上门取件退货服务...
```

注意：用户问的是"怎么退东西"，文档里写的是"退货"——关键词不同，但语义检索精准找到了！

#### 向量数据库选型

| | Chroma | Milvus | Pinecone |
|---|---|---|---|
| **定位** | 轻量级，适合学习和小项目 | 企业级，高性能 | 云服务，全托管 |
| **安装** | `pip install chromadb` | Docker 部署 | 无需安装（SaaS） |
| **数据量** | 几万~几十万条 | 数百万~数亿条 | 数百万条 |
| **适合** | 本课程、个人项目 | 生产环境 | 快速上线 |

> 💡 本课程使用 Chroma。当你的应用需要处理大规模数据时，再切换到 Milvus 或 Pinecone。

### 14.5 实战：做一个"AI 文档问答系统"

把本章所有知识串起来，做一个完整的 RAG 应用——上传文档后，AI 能根据文档内容回答问题。

#### 完整后端代码

```python
# rag_service.py — RAG 核心服务
import chromadb
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

chroma = chromadb.PersistentClient(path="./chroma_db")
collection = chroma.get_or_create_collection("knowledge_base")

def get_embedding(texts):
    response = client.embeddings.create(model="doubao-embedding", input=texts)
    return [item.embedding for item in response.data]

def split_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

# ═══════ 索引：导入文档 ═══════

def ingest_document(filename, content):
    """将文档分块、向量化、存入向量数据库"""
    chunks = split_text(content)
    embeddings = get_embedding(chunks)
    
    ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas
    )
    return len(chunks)

# ═══════ 检索 + 生成 ═══════

def ask(question, top_k=3):
    """RAG 问答：检索相关文档 → 生成回答"""
    # 1. 检索
    query_embedding = get_embedding([question])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    retrieved_docs = results["documents"][0]
    sources = results["metadatas"][0]
    
    # 2. 组装 Prompt
    context = "\n\n---\n\n".join(retrieved_docs)
    messages = [
        {"role": "system", "content": f"""你是一个知识库问答助手。

请严格基于以下参考资料回答用户问题：
- 如果资料中有答案，请准确回答并标注来源
- 如果资料中没有相关信息，说"根据现有资料，我无法回答"
- 不要编造资料中没有的内容

参考资料：
{context}"""},
        {"role": "user", "content": question}
    ]
    
    # 3. 生成回答
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=messages,
        temperature=0.3
    )
    
    return {
        "answer": response.choices[0].message.content,
        "sources": [s["source"] for s in sources]
    }
```

#### FastAPI 接口

```python
# main.py
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from rag_service import ingest_document, ask

app = FastAPI(title="AI 文档问答系统")

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档到知识库"""
    content = (await file.read()).decode("utf-8")
    chunk_count = ingest_document(file.filename, content)
    return {"message": f"成功导入 {file.filename}，分成 {chunk_count} 个片段"}

class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
def ask_question(request: QuestionRequest):
    """向知识库提问"""
    result = ask(request.question)
    return result
```

#### 测试流程

```bash
# 1. 启动服务
uvicorn main:app --reload

# 2. 上传文档（用 curl 或 FastAPI /docs 页面）
curl -X POST "http://localhost:8000/upload" \
     -F "file=@产品手册.txt"
# 返回：{"message": "成功导入 产品手册.txt，分成 12 个片段"}

# 3. 提问
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "怎么退东西？"}'
# 返回：
# {
#   "answer": "根据退货政策，您可以在收到商品 7 天内无理由退货...",
#   "sources": ["产品手册.txt"]
# }
```

#### 本章小结

```
✅ 你已经掌握了：
  • RAG 的核心思路：检索 → 注入 Prompt → 生成
  • 文档处理：加载文件 + 分块（Chunking）策略
  • Embedding 原理：文字 → 向量，语义相似度计算
  • 向量数据库：Chroma 的存储和检索操作
  • 完整 RAG 应用：上传文档 → 语义检索 → AI 回答

🎯 下一章你将学习：
  • Function Calling——让 AI 不只会"说话"，还能"做事"
```

---

## 15. Function Calling 与工具使用

前面几章的 AI 只会"说话"——你问它天气，它只能编一个答案；你让它查数据库，它做不到。**Function Calling（函数调用）** 让 AI 拥有了"做事"的能力：它告诉你"我需要调用天气 API"，你的代码执行后把结果返回给它，它再基于真实数据生成回答。

---

### 15.1 为什么 AI 需要工具：从对话到行动

#### AI 的局限性

```python
# AI 回答天气 → 它在编造！
response = client.chat.completions.create(
    model="doubao-pro-32k",
    messages=[{"role": "user", "content": "北京今天天气怎么样？"}]
)
# AI：北京今天晴，气温 25°C...
# ❌ 这是编的！AI 不联网，不知道实时天气
```

AI 大模型的本质是"文本生成"，它不能：
- ❌ 访问互联网获取实时信息
- ❌ 执行代码
- ❌ 操作数据库
- ❌ 调用第三方 API
- ❌ 发送邮件、下单、转账

#### Function Calling 的思路

不是让 AI 直接做这些事，而是让 AI 告诉你"我需要调用什么工具"，**你的代码负责执行**：

```
传统 AI：
  用户 → AI → 编造一个答案

Function Calling：
  用户 → AI → "我需要调用 get_weather('北京') 这个工具"
                                ↓
              你的代码执行 get_weather('北京')
                                ↓
              返回真实数据：{"temp": 28, "weather": "多云"}
                                ↓
              AI 基于真实数据 → "北京今天多云，气温 28°C"
```

```
AI 的角色变了：
  之前：AI 是"回答者"（只会说）
  现在：AI 是"决策者"（判断需要什么工具，由你的代码执行）
```

> 💡 **类比**：AI 像一个聪明的经理——它知道该做什么，但具体动手的事交给员工（你的代码）。

### 15.2 用 JSON Schema 定义工具签名

要让 AI 知道有哪些工具可用，你需要用 **JSON Schema** 格式描述每个工具——名字是什么、干什么用、需要什么参数。

#### 定义一个天气查询工具

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",                    # 工具名称
            "description": "查询指定城市的实时天气",    # 工具描述（AI 靠这个判断何时使用）
            "parameters": {                           # 参数定义
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如：北京、上海"
                    }
                },
                "required": ["city"]                  # 必填参数
            }
        }
    }
]
```

#### 定义多个工具

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的实时天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_todos",
            "description": "搜索待办事项列表，支持按关键词和完成状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词"},
                    "done": {"type": "boolean", "description": "是否已完成，不传则搜索全部"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "发送电子邮件",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "收件人地址"},
                    "subject": {"type": "string", "description": "邮件标题"},
                    "body": {"type": "string", "description": "邮件正文"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    }
]
```

> 💡 **description 非常重要**——AI 是根据 description 来判断何时该调用这个工具的。写得越清晰，AI 的工具选择就越准确。

### 15.3 执行流程：LLM 选工具 → 你执行 → 结果返回

Function Calling 的完整流程分三步：

```
Step 1：发送消息 + 工具列表给 AI
Step 2：AI 返回"我要调用 xxx 工具"（不是直接回答）
Step 3：你的代码执行工具，把结果返回给 AI
Step 4：AI 基于真实结果，生成最终回答
```

#### 完整代码

```python
import json
from openai import OpenAI

client = OpenAI(
    api_key="your-key",
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

# ═══════ Step 1：定义工具 ═══════

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的实时天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    }
]

# ═══════ Step 2：定义工具的实际实现 ═══════

def get_weather(city: str) -> dict:
    """模拟天气 API（实际项目中调用真实 API）"""
    weather_data = {
        "北京": {"temp": 28, "weather": "多云", "humidity": 45},
        "上海": {"temp": 32, "weather": "晴", "humidity": 60},
        "广州": {"temp": 35, "weather": "雷阵雨", "humidity": 80},
    }
    return weather_data.get(city, {"error": f"暂无{city}的天气数据"})

# 工具名 → 实际函数 的映射
tool_functions = {
    "get_weather": get_weather,
}

# ═══════ Step 3：完整调用流程 ═══════

def chat_with_tools(user_message):
    messages = [
        {"role": "system", "content": "你是一个有用的助手，可以查询天气信息。"},
        {"role": "user", "content": user_message}
    ]
    
    # 第一次调用：AI 决定是否需要工具
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=messages,
        tools=tools,            # ← 传入工具列表
        tool_choice="auto"      # auto: AI 自己决定要不要用工具
    )
    
    reply = response.choices[0].message
    
    # 如果 AI 不需要工具，直接返回回答
    if not reply.tool_calls:
        return reply.content
    
    # 如果 AI 需要工具，执行工具调用
    messages.append(reply)  # 把 AI 的工具调用请求加入历史
    
    for tool_call in reply.tool_calls:
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)
        
        print(f"🔧 AI 决定调用工具：{func_name}({func_args})")
        
        # 执行对应的函数
        result = tool_functions[func_name](**func_args)
        
        # 把工具执行结果返回给 AI
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False)
        })
    
    # 第二次调用：AI 基于工具结果生成最终回答
    final_response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=messages
    )
    
    return final_response.choices[0].message.content

# ═══════ 测试 ═══════

# 需要工具的问题
print(chat_with_tools("北京今天天气怎么样？"))
# 🔧 AI 决定调用工具：get_weather({'city': '北京'})
# AI：北京今天多云，气温 28°C，湿度 45%。

# 不需要工具的问题
print(chat_with_tools("你好，你是谁？"))
# AI：你好！我是你的 AI 助手...（没有调用任何工具）
```

#### 流程图

```
用户："北京天气怎么样？"
        ↓
AI 分析："这个问题需要查天气，我有 get_weather 工具"
        ↓
AI 返回：tool_calls: [{name: "get_weather", args: {city: "北京"}}]
        ↓
你的代码执行：get_weather("北京") → {temp: 28, weather: "多云"}
        ↓
把结果发回给 AI：role: "tool", content: {temp: 28, weather: "多云"}
        ↓
AI 生成最终回答："北京今天多云，气温 28°C"
```

> ⚠️ **安全提醒**：AI 选择调用什么工具，但**你的代码负责执行**。一定要验证 AI 传回的参数是否合理，尤其是涉及数据库操作或外部 API 时。

### 15.4 MCP 协议：工具调用的标准化趋势

你可能已经注意到了一个问题：如果我有 10 个工具，就要写 10 份 JSON Schema；如果换了一个模型平台，工具定义格式可能不一样。**MCP（Model Context Protocol）** 就是为了解决这个问题而出现的标准协议。

#### 什么是 MCP？

```
没有 MCP：
  每个 AI 应用各自定义工具格式 → 工具不能复用
  
  应用 A：自己定义天气工具、邮件工具
  应用 B：重新定义天气工具、邮件工具（不兼容）

有了 MCP：
  工具提供方实现 MCP 标准 → 任何 AI 应用都能直接使用

  MCP 天气服务 → 应用 A 直接用 ✅
                → 应用 B 直接用 ✅
                → 应用 C 直接用 ✅
```

#### MCP 的核心思路

```
MCP 的角色：
  AI 应用（Client）←→ MCP 协议 ←→ 工具服务（Server）

类比：
  USB 标准出现之前：每个设备用不同的接口
  USB 标准出现之后：所有设备用同一种接口
  
  MCP 就是 AI 工具世界的"USB 标准"
```

#### 目前的应用

MCP 目前主要被 Cursor、Claude Desktop 等 AI 编程工具使用。社区已经有大量现成的 MCP Server：

| MCP Server | 功能 |
|---|---|
| `mcp-server-filesystem` | 文件系统操作（读写文件） |
| `mcp-server-github` | GitHub API（查 Issue、创建 PR） |
| `mcp-server-sqlite` | SQLite 数据库操作 |
| `mcp-server-fetch` | HTTP 请求（访问网页） |

> 💡 MCP 还处于早期阶段，但标准化是大趋势。理解 Function Calling 的原理后，适配 MCP 会非常容易。本课程重点在原理，不深入 MCP 的具体实现。

### 15.5 实战：多工具 AI 助手

做一个拥有多种能力的 AI 助手——能查天气、搜待办、做数学计算。

#### 完整代码

```python
# multi_tool_agent.py
import json
import math
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# ═══════ 工具实现 ═══════

def get_weather(city: str) -> dict:
    """查询天气"""
    data = {
        "北京": {"temp": 28, "weather": "多云"},
        "上海": {"temp": 32, "weather": "晴"},
    }
    return data.get(city, {"error": f"暂无{city}的数据"})

def search_todos(keyword: str = "", done: bool = None) -> list:
    """搜索待办（模拟数据库查询）"""
    todos = [
        {"id": 1, "title": "学习 Python", "done": True},
        {"id": 2, "title": "学习 React", "done": False},
        {"id": 3, "title": "写毕业项目", "done": False},
        {"id": 4, "title": "复习数据库", "done": True},
    ]
    results = todos
    if keyword:
        results = [t for t in results if keyword in t["title"]]
    if done is not None:
        results = [t for t in results if t["done"] == done]
    return results

def calculator(expression: str) -> dict:
    """安全的数学计算"""
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return {"error": "不支持的表达式"}
        result = eval(expression)
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e)}

# ═══════ 工具定义 ═══════

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询城市实时天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_todos",
            "description": "搜索待办事项，支持关键词和完成状态筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词"},
                    "done": {"type": "boolean", "description": "完成状态筛选"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "数学计算，支持加减乘除和括号",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式，如 (1+2)*3"}
                },
                "required": ["expression"]
            }
        }
    }
]

tool_map = {
    "get_weather": get_weather,
    "search_todos": search_todos,
    "calculator": calculator,
}

# ═══════ 通用 Function Calling 处理器 ═══════

def smart_chat(user_message):
    messages = [
        {"role": "system", "content": "你是一个智能助手，可以查天气、搜索待办事项、做数学计算。"},
        {"role": "user", "content": user_message}
    ]
    
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    reply = response.choices[0].message
    
    if not reply.tool_calls:
        return reply.content
    
    messages.append(reply)
    
    for tool_call in reply.tool_calls:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        print(f"  🔧 调用：{name}({args})")
        
        result = tool_map[name](**args)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False)
        })
    
    final = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=messages
    )
    return final.choices[0].message.content

# ═══════ 测试 ═══════

print("用户：北京天气怎么样？")
print(f"AI：{smart_chat('北京天气怎么样？')}\n")

print("用户：我还有哪些待办没完成？")
print(f"AI：{smart_chat('我还有哪些待办没完成？')}\n")

print("用户：帮我算一下 (15 + 27) * 3.5")
print(f"AI：{smart_chat('帮我算一下 (15 + 27) * 3.5')}\n")

print("用户：你好呀")
print(f"AI：{smart_chat('你好呀')}")
```

#### 运行效果

```
用户：北京天气怎么样？
  🔧 调用：get_weather({'city': '北京'})
AI：北京今天多云，气温 28°C。

用户：我还有哪些待办没完成？
  🔧 调用：search_todos({'done': False})
AI：你还有 2 条待办未完成：1）学习 React  2）写毕业项目

用户：帮我算一下 (15 + 27) * 3.5
  🔧 调用：calculator({'expression': '(15 + 27) * 3.5'})
AI：(15 + 27) × 3.5 = 147.0

用户：你好呀
AI：你好！有什么我能帮你的吗？（没有调用工具）
```

AI 自动判断了什么时候需要工具、需要哪个工具——这就是 Function Calling 的威力。

#### 本章小结

```
✅ 你已经掌握了：
  • Function Calling 的核心思路：AI 决策 + 你的代码执行
  • 用 JSON Schema 定义工具签名
  • 完整执行流程：两次 LLM 调用 + 中间工具执行
  • MCP 协议：工具标准化的趋势
  • 多工具 AI 助手实战

🎯 下一章你将学习：
  • AI Agent——让 AI 不只调用一次工具，而是自主循环决策
```

---

## 16. AI Agent：让 AI 自主决策

上一章的 Function Calling 只调用一次工具就结束了。但很多任务需要**多步操作**——比如"帮我调研一下 Python Web 框架"，AI 需要先搜索、再整理、再总结，循环多次。**Agent（智能体）** 就是能自主循环决策的 AI——它会思考下一步该做什么、执行、观察结果、再决定下一步，直到任务完成。

---

### 16.1 什么是 Agent：循环决策 + 自主规划

#### Function Calling vs Agent

```
Function Calling（上一章）：
  用户提问 → AI 调用 1 个工具 → 返回结果 → 结束
  一次性的，用户驱动

Agent：
  用户提出任务 → AI 思考 → 调用工具 → 观察结果 → 再思考 → 再调用 → ... → 完成任务
  循环的，AI 自主驱动
```

#### Agent 的核心特征

```
┌──────────────────────────────────────────────┐
│  Agent = LLM（大脑） + Tools（手脚） + Loop（循环）│
└──────────────────────────────────────────────┘

• LLM（大脑）：理解任务、制定计划、做决策
• Tools（手脚）：执行具体操作（搜索、查数据库、调 API...）
• Loop（循环）：不断"思考→行动→观察"直到任务完成
```

#### 一个直观的例子

用户："帮我调研一下国内主流的大模型 API 平台，比较它们的价格和特点"

```
Agent 的执行过程：

轮次 1：
  💭 思考：我需要先搜索国内大模型平台有哪些
  🔧 行动：search("国内大模型 API 平台")
  👀 观察：搜到了豆包、DeepSeek、通义千问、文心一言...

轮次 2：
  💭 思考：找到了几个平台，我需要查具体价格
  🔧 行动：search("豆包 API 价格")
  👀 观察：豆包 pro 模型每百万 Token 0.8 元...

轮次 3：
  💭 思考：再查下 DeepSeek 的价格
  🔧 行动：search("DeepSeek API 价格")
  👀 观察：DeepSeek V3 每百万 Token 1 元...

轮次 4：
  💭 思考：信息够了，可以整理成报告了
  🔧 行动：生成对比报告
  ✅ 完成：输出结构化的对比分析
```

**关键区别**：用户只说了一句话，Agent 自己决定了需要搜索 3 次、最后整理。整个过程无需人工干预。

### 16.2 ReAct 模式：思考 → 行动 → 观察 → 再思考

ReAct（Reasoning + Acting）是目前最主流的 Agent 模式。核心思想：让 AI 在每一步都显式地"思考"，而不是直接行动。

```
ReAct 循环：

  ┌─→ Thought（思考）："我需要做什么？"
  │         ↓
  │   Action（行动）：调用某个工具
  │         ↓
  │   Observation（观察）：查看工具返回的结果
  │         ↓
  │   判断：任务完成了吗？
  │     ├─ 没完成 → 回到 Thought ────┐
  │     └─ 完成了 → 输出最终答案      │
  └───────────────────────────────────┘
```

### 16.3 手写 Agent 核心循环（不依赖框架，理解原理）

不用任何框架，用纯 Python + OpenAI SDK 实现一个 Agent。理解了这个，以后用任何 Agent 框架都能举一反三。

#### 核心代码（约 60 行）

```python
# simple_agent.py
import json
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# ═══════ 工具定义和实现 ═══════

def search(query: str) -> str:
    """模拟搜索（实际项目中调用搜索引擎 API）"""
    mock_results = {
        "Python Web 框架": "主流框架有：Flask（轻量）、Django（全栈）、FastAPI（高性能+异步）",
        "FastAPI 优点": "高性能、自动文档、类型提示、异步支持、学习曲线低",
        "Django 优点": "功能齐全、admin 后台、ORM、模板引擎、社区庞大",
    }
    for key, value in mock_results.items():
        if key in query:
            return value
    return f"搜索 '{query}' 的结果：暂无相关信息"

def finish(answer: str) -> str:
    """完成任务，输出最终答案"""
    return answer

tools = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "搜索互联网信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "任务完成时调用，输出最终答案给用户",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string", "description": "最终答案"}
                },
                "required": ["answer"]
            }
        }
    }
]

tool_map = {"search": search, "finish": finish}

# ═══════ Agent 核心循环 ═══════

def run_agent(task: str, max_steps: int = 10):
    """Agent 主循环"""
    print(f"📋 任务：{task}\n")
    
    messages = [
        {"role": "system", "content": """你是一个智能调研助手。
你可以使用 search 工具搜索信息，使用 finish 工具输出最终答案。

工作流程：
1. 分析任务，决定需要搜索什么
2. 搜索信息，分析结果
3. 如果信息不够，继续搜索
4. 信息充分后，调用 finish 输出结构化的答案"""},
        {"role": "user", "content": task}
    ]
    
    for step in range(max_steps):
        print(f"--- 步骤 {step + 1} ---")
        
        # AI 决策
        response = client.chat.completions.create(
            model="doubao-pro-32k",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        reply = response.choices[0].message
        
        # 如果 AI 直接回复（没有调用工具）
        if not reply.tool_calls:
            print(f"💬 AI 直接回复：{reply.content}")
            return reply.content
        
        messages.append(reply)
        
        # 执行每个工具调用
        for tool_call in reply.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            print(f"  🔧 调用：{name}({args})")
            result = tool_map[name](**args)
            print(f"  📄 结果：{result[:100]}...")
            
            # 如果调用了 finish，任务结束
            if name == "finish":
                print(f"\n✅ 任务完成！")
                return result
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
    
    print("⚠️ 达到最大步骤数，强制结束")
    return "任务未能在限定步骤内完成"

# ═══════ 运行 ═══════

result = run_agent("帮我对比一下 Python 的 FastAPI 和 Django 框架")
print(f"\n最终答案：\n{result}")
```

#### 运行效果

```
📋 任务：帮我对比一下 Python 的 FastAPI 和 Django 框架

--- 步骤 1 ---
  🔧 调用：search({'query': 'Python Web 框架'})
  📄 结果：主流框架有：Flask（轻量）、Django（全栈）、FastAPI（高性能+异步）...

--- 步骤 2 ---
  🔧 调用：search({'query': 'FastAPI 优点'})
  📄 结果：高性能、自动文档、类型提示、异步支持、学习曲线低...

--- 步骤 3 ---
  🔧 调用：search({'query': 'Django 优点'})
  📄 结果：功能齐全、admin 后台、ORM、模板引擎、社区庞大...

--- 步骤 4 ---
  🔧 调用：finish({'answer': 'FastAPI vs Django 对比：...'})

✅ 任务完成！
```

**注意这个循环**：AI 自己决定搜索 3 次（每次不同关键词），最后自己判断"信息够了"并调用 finish。这就是 Agent 的核心——**自主循环决策**。

> 💡 **max_steps 是安全阀**——防止 AI 陷入无限循环。实际项目中还需要加入成本限制（最大 Token 消耗）。

### 16.4 多 Agent 协作简介

一个 Agent 能力有限，多个 Agent 协作可以完成更复杂的任务。

#### 多 Agent 架构模式

```
模式 1：管理者+专家 模式
┌────────────┐
│ 管理者 Agent │  ← 接收任务，分配给专家
└─────┬──────┘
      ├──→ 搜索专家 Agent（负责搜索信息）
      ├──→ 分析专家 Agent（负责数据分析）
      └──→ 写作专家 Agent（负责生成报告）

模式 2：流水线 模式
  Agent A（收集数据）→ Agent B（分析数据）→ Agent C（生成报告）

模式 3：辩论 模式
  Agent A（正方观点）←→ Agent B（反方观点）→ 裁判 Agent（综合结论）
```

#### 简单的双 Agent 示例

```python
def research_agent(topic):
    """调研 Agent：负责搜索和收集信息"""
    return run_agent(f"搜索并收集关于 {topic} 的详细信息")

def writer_agent(research_data):
    """写作 Agent：负责整理成文章"""
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=[
            {"role": "system", "content": "你是一个专业的技术文章作者"},
            {"role": "user", "content": f"根据以下调研资料，写一篇结构清晰的文章：\n{research_data}"}
        ]
    )
    return response.choices[0].message.content

# 两个 Agent 协作
data = research_agent("FastAPI 框架")   # Agent A：调研
article = writer_agent(data)            # Agent B：写文章
print(article)
```

> 💡 多 Agent 是进阶话题。入门阶段先掌握单 Agent 的核心循环，后续可以探索 LangGraph、CrewAI 等多 Agent 框架。

### 16.5 实战总结与 Agent 设计原则

经过本章的学习，你已经能手写一个 Agent 了。最后总结几条实践中的关键原则：

#### Agent 设计的核心原则

```
1. 明确退出条件
   Agent 必须有明确的"完成"标志（如 finish 工具），否则会陷入无限循环

2. 设置安全边界
   - max_steps：最大循环次数
   - max_tokens：最大 Token 消耗
   - timeout：最大运行时间

3. System Prompt 是灵魂
   好的 System Prompt 能让 Agent 决策更精准，差的会让它反复无意义地调用工具

4. 工具粒度要合适
   - 太粗：一个万能工具 → AI 不知道怎么精确使用
   - 太细：几十个小工具 → AI 选择困难
   - 推荐：5~10 个职责清晰的工具

5. 日志和可观测性
   Agent 的多步操作必须有完整日志，方便调试和优化
```

#### 本章小结

```
✅ 你已经掌握了：
  • Agent 的核心概念：LLM + Tools + Loop
  • ReAct 模式：思考 → 行动 → 观察 → 循环
  • 手写 Agent 核心循环（60 行代码，不依赖框架）
  • 多 Agent 协作的基本模式
  • Agent 设计的实践原则

🎯 下一章你将学习：
  • 全栈项目架构与安全——让你的 AI 应用安全可靠地运行
```

---

## 17. 全栈项目架构与安全

到这里，你的 AI 应用功能已经很完整了——能聊天、能记忆、能检索知识库、能调用工具、能自主规划。但"能跑"和"能上线"之间还有一段距离：项目结构怎么组织？配置怎么管理？出错了怎么排查？API Key 怎么保护？

本章解决这些"让项目从 demo 变成产品"的工程化问题。

---

### 17.1 项目结构规范：前后端分离架构

#### 推荐的项目结构

```
my-ai-app/
├── backend/                    ← Python 后端
│   ├── main.py                 ← FastAPI 入口
│   ├── config.py               ← 配置管理
│   ├── models.py               ← 数据库模型
│   ├── database.py             ← 数据库配置
│   ├── services/               ← 业务逻辑
│   │   ├── chat_service.py     ← 聊天服务
│   │   ├── rag_service.py      ← RAG 服务
│   │   └── agent_service.py    ← Agent 服务
│   ├── routers/                ← API 路由
│   │   ├── chat.py
│   │   └── knowledge.py
│   ├── requirements.txt        ← Python 依赖
│   └── .env                    ← 环境变量（不提交到 Git！）
│
├── frontend/                   ← React 前端
│   ├── src/
│   │   ├── services/api.js     ← API 请求封装
│   │   ├── pages/              ← 页面组件
│   │   ├── components/         ← 通用组件
│   │   └── App.jsx
│   └── package.json
│
├── .gitignore                  ← Git 忽略文件
└── README.md                   ← 项目说明
```

### 17.2 环境变量管理与多环境配置

**永远不要把密钥写在代码里**，用 `.env` 文件管理：

```bash
# backend/.env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DATABASE_URL=sqlite:///./app.db
CORS_ORIGINS=http://localhost:5173
```

```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    openai_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    database_url: str = "sqlite:///./app.db"
    cors_origins: str = "http://localhost:5173"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

```gitignore
# .gitignore —— 这些文件绝对不能提交到 Git
.env
*.db
__pycache__/
node_modules/
```

> ⚠️ **最重要的安全规则**：`.env` 文件必须加入 `.gitignore`。一旦 API Key 提交到 GitHub，可能在几分钟内被扫描盗用。

### 17.3 错误处理、日志与监控

```python
# main.py — 全局错误处理
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"请求 {request.url} 出错：{exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "服务器内部错误，请稍后重试"}
    )

# 在业务代码中使用
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        result = chat_service.chat(request.message)
        return {"reply": result}
    except Exception as e:
        logger.error(f"聊天接口错误：{e}")
        raise
```

### 17.4 API Key 安全：后端代理、限流、成本控制

```
核心原则：前端永远不接触 API Key

❌ 错误：前端直接调用大模型 API（API Key 暴露在浏览器中）
✅ 正确：前端 → 你的后端 → 大模型 API（API Key 只在后端）
```

**简单的限流实现：**

```python
from fastapi import HTTPException
from collections import defaultdict
from time import time

# 简单的内存限流器
request_counts = defaultdict(list)

def rate_limit(user_id: str, max_requests: int = 20, window: int = 3600):
    """限制每个用户每小时最多 20 次请求"""
    now = time()
    request_counts[user_id] = [t for t in request_counts[user_id] if now - t < window]
    
    if len(request_counts[user_id]) >= max_requests:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    
    request_counts[user_id].append(now)
```

#### 本章小结

```
✅ 你已经掌握了：
  • 前后端分离的项目结构规范
  • 用 .env + pydantic 管理环境变量
  • 全局错误处理和日志记录
  • API Key 安全：后端代理 + 限流

🎯 下一章你将学习：
  • 把你的应用部署到公网，让别人也能访问
```

---

## 18. 部署上线

你的应用在本地跑得很好，但别人访问不了——因为它只在你的电脑上运行。本章教你把前端和后端分别部署到云服务器上，让全世界都能访问你的 AI 应用。

---

### 18.1 前端部署：Vercel

Vercel 是最适合部署前端项目的平台——免费、快速、Git 推送自动部署。

```
部署流程（3 分钟完成）：

1. 把代码推送到 GitHub
2. 注册 Vercel 账号（vercel.com），用 GitHub 登录
3. 点击 "Import Project"，选择你的前端仓库
4. Vercel 自动检测到 Vite/React 项目，点击 "Deploy"
5. 部署完成，获得一个公网地址：https://your-app.vercel.app
```

> 💡 每次你 `git push`，Vercel 会自动重新部署。这就是 CI/CD（持续集成/持续部署）。

### 18.2 后端部署：Railway / Docker

#### 方式一：Railway（最简单，推荐新手）

Railway 类似后端版的 Vercel——连接 GitHub 仓库即可部署。

```
1. 注册 Railway 账号（railway.app）
2. 新建项目 → 从 GitHub 导入后端仓库
3. 设置环境变量（OPENAI_API_KEY 等）
4. Railway 自动检测 Python 项目并部署
5. 获得后端地址：https://your-api.railway.app
```

在 `backend/` 根目录需要一个 `Procfile`：

```
# Procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 方式二：Docker（进阶，实际工作中最常用）

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 构建并运行
docker build -t my-ai-app .
docker run -p 8000:8000 --env-file .env my-ai-app
```

### 18.3 数据库托管方案

本地开发用 SQLite 文件没问题，但生产环境推荐用云数据库：

| 方案 | 适合 | 特点 |
|---|---|---|
| SQLite（本地文件） | 个人项目、学习 | 零配置，但不支持并发 |
| Railway PostgreSQL | 小型项目 | Railway 内置，一键创建 |
| Supabase | 中型项目 | 免费 PostgreSQL + 管理界面 |
| 阿里云 RDS | 生产环境 | 企业级，高可用 |

> 💡 从 SQLite 迁移到 PostgreSQL，只需要改一行连接字符串——这就是用 SQLAlchemy ORM 的好处。

### 18.4 部署后的关键配置

部署后需要更新几个配置：

```python
# 1. 后端 CORS：允许你的 Vercel 域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",              # 本地开发
        "https://your-app.vercel.app",        # 生产环境
    ],
)

# 2. 前端 API 地址：指向部署后的后端
# frontend/src/services/api.js
const API_BASE = import.meta.env.PROD 
    ? "https://your-api.railway.app"    // 生产环境
    : "http://localhost:8000";          // 本地开发
```

### 18.5 实战：部署清单

```
部署前检查清单：
  □ .env 已加入 .gitignore
  □ requirements.txt 包含所有依赖
  □ 后端 CORS 配置了生产域名
  □ 前端 API 地址配置了生产后端地址
  □ 数据库已迁移或使用云数据库
  □ 环境变量已在部署平台设置
```

#### 本章小结

```
✅ 你已经掌握了：
  • 前端部署：Vercel + GitHub 自动部署
  • 后端部署：Railway（简单）/ Docker（进阶）
  • 数据库托管：SQLite → PostgreSQL 的平滑迁移
  • 部署配置：CORS、环境变量、API 地址

🎯 下一章（最后一章）：
  • 毕业项目——综合运用所有知识，做一个完整的 AI 应用
```

---

## 19. 毕业项目：从 0 到 1 构建完整 AI 应用

这是本课程的最后一章。你将综合运用前 18 章学到的所有技能——前端、后端、数据库、LLM API、RAG、Agent、部署——独立完成一个完整的 AI 应用。

---

### 19.1 选题指导：什么样的 AI 应用有价值

#### 推荐选题方向

| 项目 | 核心技术 | 难度 |
|---|---|---|
| **AI 聊天机器人** | LLM API + 对话管理 + 人格设定 | ⭐⭐ |
| **AI 写作助手** | LLM API + Prompt Engineering + 流式输出 | ⭐⭐ |
| **智能客服系统** | RAG + 知识库 + 多轮对话 | ⭐⭐⭐ |
| **AI 文档问答** | RAG + 文档上传 + Embedding | ⭐⭐⭐ |
| **AI 学习陪练** | LLM + 对话管理 + 评估反馈 | ⭐⭐⭐ |
| **AI 调研助手** | Agent + 搜索工具 + 报告生成 | ⭐⭐⭐⭐ |
| **个人知识管理** | RAG + Agent + 笔记整合 | ⭐⭐⭐⭐ |

#### 选题原则

```
好的毕业项目：
  ✅ 解决一个你自己遇到过的真实问题
  ✅ 综合运用至少 3 个核心模块（LLM/RAG/Agent）
  ✅ 有完整的前后端交互
  ✅ 能部署上线，让别人也能用

避免：
  ❌ 只是调一下 API 就完了（太简单）
  ❌ 功能太庞大做不完（贪多嚼不烂）
```

### 19.2 架构设计：画出你的应用架构图

开始写代码之前，先画清楚架构：

```
通用 AI 应用架构模板：

用户
  ↓
┌──────────────────────────────────┐
│        前端（React + Vite）        │
│  聊天界面 / 文档上传 / 结果展示     │
└──────────────┬───────────────────┘
               ↓ HTTP API
┌──────────────────────────────────┐
│        后端（FastAPI）             │
│  ┌───────┐ ┌─────┐ ┌─────────┐  │
│  │聊天服务│ │RAG  │ │Agent    │  │
│  │       │ │服务 │ │服务     │  │
│  └───┬───┘ └──┬──┘ └────┬────┘  │
│      └────────┼─────────┘       │
│               ↓                  │
│         LLM API（豆包/GPT）       │
└──────────────┬───────────────────┘
               ↓
┌──────────────────────────────────┐
│           数据存储                 │
│  SQLite（对话）  Chroma（向量）    │
└──────────────────────────────────┘
```

### 19.3 开发流程建议

```
推荐的开发顺序（每步都能运行和测试）：

Step 1：搭建后端骨架
  • FastAPI + 数据库 + 基础 API
  • 测试：用 /docs 验证接口

Step 2：实现核心 AI 功能
  • LLM 调用 + Prompt 设计
  • 如果用 RAG：搭建知识库
  • 如果用 Agent：实现工具和循环
  • 测试：用脚本或 /docs 测试

Step 3：搭建前端界面
  • React 页面 + API 对接
  • 实现流式输出的打字机效果
  • 测试：前后端联调

Step 4：完善和优化
  • 错误处理 + 日志
  • 安全配置（.env、CORS）
  • 优化 Prompt、调整参数

Step 5：部署上线
  • 前端 → Vercel
  • 后端 → Railway
  • 设置环境变量
```

> 💡 **用 Cursor 加速开发**：整个过程中，充分利用 Cursor 的 AI 能力——让它帮你写代码、调试 Bug、优化 Prompt。这就是"用 AI 开发 AI 应用"。

### 19.4 课程回顾与展望

#### 你学到了什么

```
基础篇（第 1-5 章）
  ✅ 开发环境搭建（Cursor + Python + Node.js）
  ✅ Python 基础 + JavaScript 基础
  ✅ HTML/CSS/JS 前端基础

全栈篇（第 6-11 章）
  ✅ React 组件化开发
  ✅ FastAPI 后端 API 开发
  ✅ 数据库基础（SQL + SQLAlchemy）
  ✅ 前后端联调（CORS、数据流）

AI 核心篇（第 12-16 章）
  ✅ LLM API 调用 + Prompt Engineering
  ✅ 对话管理 + Context Engineering
  ✅ RAG 知识库（Embedding + 向量数据库）
  ✅ Function Calling 工具调用
  ✅ AI Agent 自主决策

工程化篇（第 17-19 章）
  ✅ 项目架构 + 安全实践
  ✅ 部署上线
  ✅ 毕业项目
```

#### 继续学习的方向

```
你现在的能力：能独立开发和部署一个完整的 AI 应用

下一步可以深入：
  🔹 更强的 AI 能力：多模态（图片/语音）、Agent 框架（LangGraph）
  🔹 更好的工程实践：Docker、Kubernetes、微服务
  🔹 更深的 AI 理解：模型微调、训练原理、论文阅读
  🔹 更广的应用场景：AI + 电商、AI + 教育、AI + 医疗
```

**恭喜你完成了这门课程！🎉**

从零开始，你已经掌握了 AI 应用开发的完整技能栈。这不是终点，而是起点——现在的你已经有能力把自己的想法变成一个真正可用的 AI 应用了。

去创造吧。

---

# 专题模块（选修）

> 以下专题不影响主线学习流程，学员可在完成主线课程后按需选学，也可穿插在相关章节之后学习。

---

## 专题 A：TypeScript 基础

> 📌 建议学习时机：完成第 7 章（React）之后

JavaScript 的灵活性是双刃剑——变量可以是任何类型，拼错属性名也不会报错，直到运行时才崩溃。TypeScript 给 JavaScript 加上了**类型系统**，让你在写代码的时候就发现错误。

---

### A.1 为什么需要 TypeScript：类型安全的价值

```javascript
// JavaScript：运行时才发现错误
function greet(user) {
    return "Hello, " + user.name.toUpperCase();
}
greet({ nme: "张三" });  // 拼错了 name → 运行时崩溃：Cannot read property 'toUpperCase' of undefined
```

```typescript
// TypeScript：写代码时就报错
interface User {
    name: string;
    age: number;
}

function greet(user: User): string {
    return "Hello, " + user.name.toUpperCase();
}
greet({ nme: "张三" });  // ❌ 编辑器立刻标红：'nme' does not exist in type 'User'
```

### A.2 基础类型、接口、泛型

```typescript
// ═══════ 基础类型 ═══════
let name: string = "张三";
let age: number = 25;
let isStudent: boolean = true;
let skills: string[] = ["Python", "React"];

// ═══════ 接口（Interface）═══════
interface Message {
    role: "user" | "assistant" | "system";  // 联合类型：只能是这三个值
    content: string;
    timestamp?: number;   // ? 表示可选属性
}

const msg: Message = { role: "user", content: "你好" };

// ═══════ 泛型（Generics）═══════
// 一个通用的 API 响应类型
interface ApiResponse<T> {
    code: number;
    data: T;
    message: string;
}

// 用的时候指定 T 是什么
type ChatResponse = ApiResponse<{ reply: string }>;
type TodoResponse = ApiResponse<{ id: number; title: string }[]>;
```

### A.3 在 React 项目中使用 TypeScript

```typescript
// ═══════ 组件 Props 类型 ═══════
interface ChatMessageProps {
    role: "user" | "assistant";
    content: string;
    timestamp: number;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ role, content, timestamp }) => {
    return (
        <div className={`message ${role}`}>
            <p>{content}</p>
            <span>{new Date(timestamp).toLocaleTimeString()}</span>
        </div>
    );
};

// ═══════ State 类型 ═══════
const [messages, setMessages] = useState<Message[]>([]);
const [loading, setLoading] = useState<boolean>(false);

// ═══════ 事件类型 ═══════
const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // ...
};

const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
};
```

### A.4 实战：用 TS 重构聊天界面

```bash
# 新建 TypeScript React 项目
npx -y create-vite@latest my-chat-app -- --template react-ts
```

关键改动：文件从 `.jsx` 改为 `.tsx`，给 Props 和 State 加上类型定义。TypeScript 不会改变运行逻辑，但让代码更安全、IDE 提示更智能。

> 💡 **建议**：新项目直接用 TypeScript 开始。Cursor 的 AI 对 TypeScript 项目的代码补全更精准。

---

## 专题 B：用户认证与权限

> 📌 建议学习时机：完成第 11 章（前后端联调）之后

你的应用目前所有人都能访问、所有数据共享。要成为一个真正可用的产品，需要用户系统——注册、登录、每个用户只能看自己的数据。

---

### B.1 认证 vs 授权：核心概念

```
认证（Authentication）= 你是谁？
  → 登录过程：用户名 + 密码 → 验证身份

授权（Authorization）= 你能干什么？
  → 权限检查：这个用户能不能删除这条数据？
```

### B.2 JWT 原理与实现

JWT（JSON Web Token）是目前最主流的无状态认证方案：

```
登录流程：
  用户发送 用户名+密码 → 服务器验证 → 返回一个 JWT Token
  
后续请求：
  用户每次请求带上 Token → 服务器验证 Token 有效性 → 允许访问
```

```python
# 生成和验证 JWT
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"

def create_token(user_id: int) -> str:
    """生成 JWT Token"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)  # 24 小时过期
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> dict:
    """验证 JWT Token"""
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

### B.3 FastAPI 实现登录注册 API

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

# 注册
@app.post("/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    hashed = hash_password(password)  # 密码加密存储
    user = User(username=username, password=hashed)
    db.add(user)
    db.commit()
    return {"message": "注册成功"}

# 登录
@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(user.id)
    return {"token": token}

# 需要登录才能访问的接口
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """从 Token 中解析当前用户"""
    payload = verify_token(credentials.credentials)
    return payload["user_id"]

@app.get("/my/conversations")
def my_conversations(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Conversation).filter(Conversation.user_id == user_id).all()
```

### B.4 前端登录状态管理

```javascript
// 登录后保存 Token
const login = async (username, password) => {
    const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });
    const { token } = await res.json();
    localStorage.setItem("token", token);
};

// 每次请求带上 Token
const fetchWithAuth = (url, options = {}) => {
    const token = localStorage.getItem("token");
    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            "Authorization": `Bearer ${token}`
        }
    });
};
```

> 💡 有了用户系统，你的 AI 应用就能实现"每个用户有独立的对话记录和知识库"。

---

## 专题 C：多模态 AI（视觉与语音）

> 📌 建议学习时机：完成第 16 章（Agent）之后

AI 不只能处理文字。现代大模型已经能"看图"、"画图"、"听话"、"说话"。掌握多模态 API，你的应用能力边界将大幅扩展。

---

### C.1 Vision API：让 AI 看懂图片

```python
# 发送图片给 AI，让它描述图片内容
response = client.chat.completions.create(
    model="doubao-pro-32k",  # 需要支持视觉的模型
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "这张图片里有什么？"},
                {"type": "image_url", "image_url": {"url": "https://example.com/photo.jpg"}}
            ]
        }
    ]
)
print(response.choices[0].message.content)
# AI：这张图片显示了一只橘色的猫坐在窗台上，窗外是城市夜景...
```

应用场景：拍照翻译、图片内容审核、商品图自动生成描述。

### C.2 图片生成：DALL-E API

```python
# 用文字描述生成图片
response = client.images.generate(
    model="dall-e-3",
    prompt="一只戴着眼镜在写代码的猫，赛博朋克风格，高清",
    size="1024x1024",
    n=1
)
image_url = response.data[0].url
print(f"生成的图片：{image_url}")
```

### C.3 语音识别与语音合成

```python
# 语音识别（语音 → 文字）
with open("recording.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
print(transcript.text)  # "你好，帮我查一下明天的天气"

# 语音合成（文字 → 语音）
response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="你好！明天北京晴天，气温28度。"
)
with open("reply.mp3", "wb") as f:
    f.write(response.content)
```

### C.4 实战思路：拍照问 AI

```
用户拍照 → 前端上传图片 → 后端发送给 Vision API → AI 分析图片内容 → 返回回答
         → 前端用 TTS 播放回答（可选）
```

> 💡 多模态让 AI 应用从"打字聊天"进化到"拍照问答"和"语音对话"，大幅降低用户使用门槛。

---

## 专题 D：Docker 容器化入门

> 📌 建议学习时机：完成第 18 章（部署）之后

Docker 解决了"在我电脑上能跑"的经典问题——把应用和所有依赖打包成一个标准化的容器，在任何地方都能一致运行。

---

### D.1 为什么需要 Docker

```
没有 Docker：
  "我本地 Python 3.11 能跑" → 服务器是 Python 3.9，跑不了
  "我装了 SQLite 3.40" → 服务器版本不一样，SQL 语法不兼容

有了 Docker：
  把 Python 3.11 + 所有依赖 + 你的代码 打包成一个"容器"
  → 在任何服务器上都能一模一样地运行
```

### D.2 核心概念

```
镜像（Image）= 应用的"安装包"
  包含操作系统 + 依赖 + 你的代码
  
容器（Container）= 运行中的镜像
  镜像的一个实例，类似"安装好的程序正在运行"

Dockerfile = 构建镜像的"说明书"
  一步步描述如何搭建环境和打包应用
```

### D.3 编写 Dockerfile 打包 FastAPI 应用

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim           # 基于 Python 3.11 镜像
WORKDIR /app                    # 设置工作目录
COPY requirements.txt .         # 先复制依赖文件
RUN pip install -r requirements.txt  # 安装依赖
COPY . .                        # 再复制代码
EXPOSE 8000                     # 声明端口
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 构建镜像
docker build -t my-ai-backend .

# 运行容器
docker run -d -p 8000:8000 --env-file .env --name ai-backend my-ai-backend

# 查看运行状态
docker ps
```

### D.4 Docker Compose：一键启动全部服务

```yaml
# docker-compose.yml
version: "3.8"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - ./data:/app/data      # 数据持久化

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

```bash
# 一键启动前端 + 后端
docker compose up -d

# 一键停止
docker compose down
```

> 💡 Docker Compose 让你用一条命令启动整个应用栈。这在团队协作和生产部署中极其实用。

---

## 专题 E：自动化测试入门

> 📌 建议学习时机：完成第 17 章（全栈架构）之后

手动测试每次都要自己点、自己试，改了一处代码可能破坏另一处功能。自动化测试让机器帮你检查——你改完代码，运行一条命令就知道有没有破坏已有功能。

---

### E.1 为什么需要测试

```
没有测试：
  改了对话管理的代码 → 手动测试聊天功能 → 没发现 RAG 也坏了 → 上线后用户报 Bug

有了测试：
  改了对话管理的代码 → 运行 pytest → 2 秒后告诉你 RAG 的测试挂了
  → 上线前就发现并修复
```

### E.2 Python 单元测试（pytest）

```bash
pip install pytest
```

```python
# tests/test_rag.py
from rag_service import split_text

def test_split_text_basic():
    """测试文本分块"""
    text = "a" * 1000
    chunks = split_text(text, chunk_size=500, overlap=50)
    assert len(chunks) >= 2
    assert len(chunks[0]) == 500

def test_split_text_short():
    """短文本不应该被分割"""
    text = "Hello World"
    chunks = split_text(text, chunk_size=500)
    assert len(chunks) == 1
    assert chunks[0] == "Hello World"

def test_split_text_overlap():
    """测试重叠部分"""
    text = "a" * 200
    chunks = split_text(text, chunk_size=100, overlap=20)
    # 第二个块的开头应该和第一个块的结尾有重叠
    assert chunks[0][-20:] == chunks[1][:20]
```

```bash
# 运行测试
pytest tests/ -v
# ✅ test_split_text_basic PASSED
# ✅ test_split_text_short PASSED
# ✅ test_split_text_overlap PASSED
```

### E.3 API 接口测试

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_conversation():
    response = client.post("/conversations")
    assert response.status_code == 200
    assert "id" in response.json()

def test_translate():
    response = client.post("/translate", json={"text": "Hello"})
    assert response.status_code == 200
    assert "result" in response.json()
```

> 💡 **测试越早写越好**。每次新增功能后补上测试，长期来看能节省大量调试时间。

---

## 专题 F：AI 应用评估与优化

> 📌 建议学习时机：完成第 14 章（RAG）和第 16 章（Agent）之后

AI 应用上线后，怎么知道效果好不好？怎么持续优化？"感觉挺好的"不够——需要系统化的评估方法。

---

### F.1 Prompt 效果评估

```python
# 构建测试集
test_cases = [
    {"input": "Hello", "expected_output": "你好"},
    {"input": "Thank you", "expected_output": "谢谢"},
    {"input": "Good morning", "expected_output": "早上好"},
]

# 跑测试，统计准确率
correct = 0
for case in test_cases:
    result = translate(case["input"])
    if case["expected_output"] in result:
        correct += 1
        
accuracy = correct / len(test_cases)
print(f"翻译准确率：{accuracy:.1%}")  # 翻译准确率：90.0%
```

### F.2 RAG 检索质量评估

```
RAG 效果不好时，先定位是哪个环节出了问题：

检索质量差？ → 检索到的文档和问题不相关
  → 优化分块策略、换更好的 Embedding 模型

生成质量差？ → 检索到了正确文档，但 AI 回答不好
  → 优化 System Prompt、调整 temperature
```

```python
# 检索质量评估
def evaluate_retrieval(test_queries, expected_sources):
    """评估检索是否找到了正确的文档"""
    hits = 0
    for query, expected in zip(test_queries, expected_sources):
        results = search(query, top_k=3)
        if expected in str(results):
            hits += 1
    return hits / len(test_queries)
```

### F.3 Token 成本监控

```python
# 在每次调用后记录成本
import logging

def chat_with_cost_tracking(message):
    response = client.chat.completions.create(
        model="doubao-pro-32k",
        messages=[{"role": "user", "content": message}]
    )
    
    # 记录 Token 使用量
    usage = response.usage
    logging.info(f"Token 使用：输入={usage.prompt_tokens}, 输出={usage.completion_tokens}, 总计={usage.total_tokens}")
    
    return response.choices[0].message.content
```

```
优化成本的方法：
  • 缩短 System Prompt（减少每次的固定开销）
  • 滑动窗口限制对话历史长度
  • 简单问题用小模型，复杂问题用大模型（模型路由）
  • 缓存常见问题的回答
```

### F.4 A/B 测试思路

```
A/B 测试：同时运行两个版本，看哪个效果更好

版本 A：temperature=0.3 的 Prompt
版本 B：temperature=0.7 的 Prompt

50% 用户看到 A，50% 用户看到 B
→ 比较哪个版本的用户满意度更高
```

> 💡 AI 应用的优化是一个持续过程。上线只是开始，根据用户反馈和数据不断迭代 Prompt 和参数才是关键。

---

## 专题 G：状态管理进阶

> 📌 建议学习时机：完成第 7 章（React）和第 13 章（对话管理）之后

当你的 React 应用变复杂——多个页面要共享用户登录状态、聊天记录、主题设置——props 一层层传下去就变成了噩梦。全局状态管理解决这个问题。

---

### G.1 为什么需要全局状态管理

```
Props 传递的问题（"Props Drilling"）：

App → Layout → Sidebar → ChatList → ChatItem
                                       ↑
                                    需要 user 信息
要从 App 一层层传下来 → 中间的组件根本不用 user，却被迫接收和转发

全局状态管理：
  任何组件都能直接读取和修改全局状态，不需要通过 props 传递
```

### G.2 Context API：React 内置方案

```jsx
import { createContext, useContext, useState } from "react";

// 1. 创建 Context
const UserContext = createContext(null);

// 2. Provider 包裹应用
function App() {
    const [user, setUser] = useState(null);
    
    return (
        <UserContext.Provider value={{ user, setUser }}>
            <Layout />
        </UserContext.Provider>
    );
}

// 3. 任何子组件直接使用
function ChatHeader() {
    const { user } = useContext(UserContext);
    return <h2>欢迎，{user?.name || "游客"}</h2>;
}
```

**Context API 的局限**：适合简单场景（主题、语言、用户信息）。状态多了之后代码会很乱，且每次状态变化会触发所有消费组件重渲染。

### G.3 Zustand：轻量级状态管理（推荐）

Zustand 是目前 React 社区最流行的轻量状态管理库——API 极简，性能优秀。

```bash
npm install zustand
```

```jsx
// stores/useChatStore.js
import { create } from "zustand";

const useChatStore = create((set, get) => ({
    // ═══════ 状态 ═══════
    conversations: [],
    currentConvId: null,
    messages: [],
    loading: false,
    
    // ═══════ 操作 ═══════
    setCurrentConv: (convId) => set({ currentConvId: convId }),
    
    addMessage: (message) => set((state) => ({
        messages: [...state.messages, message]
    })),
    
    sendMessage: async (text) => {
        const { currentConvId, addMessage } = get();
        
        // 添加用户消息
        addMessage({ role: "user", content: text });
        set({ loading: true });
        
        // 调用 API
        const res = await fetch(`/conversations/${currentConvId}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });
        const { reply } = await res.json();
        
        // 添加 AI 回复
        addMessage({ role: "assistant", content: reply });
        set({ loading: false });
    },
}));

export default useChatStore;
```

```jsx
// 在任何组件中使用（不需要 Provider！）
function ChatInput() {
    const [input, setInput] = useState("");
    const { sendMessage, loading } = useChatStore();
    
    const handleSubmit = () => {
        sendMessage(input);
        setInput("");
    };
    
    return (
        <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
            <input value={input} onChange={e => setInput(e.target.value)} />
            <button disabled={loading}>{loading ? "发送中..." : "发送"}</button>
        </form>
    );
}

function MessageList() {
    const messages = useChatStore(state => state.messages);  // 只订阅 messages
    
    return (
        <div>
            {messages.map((msg, i) => (
                <div key={i} className={msg.role}>{msg.content}</div>
            ))}
        </div>
    );
}
```

### G.4 Zustand vs 其他方案

| | Context API | Zustand | Redux |
|---|---|---|---|
| **复杂度** | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **性能** | 一般 | ✅ 精确更新 | ✅ 精确更新 |
| **代码量** | 少 | 少 | 多（样板代码多） |
| **适合** | 简单共享 | 中小型项目（推荐） | 大型企业项目 |
| **学习成本** | 零 | 极低 | 较高 |

> 💡 **推荐方案**：简单状态用 Context API，复杂状态用 Zustand。Redux 除非团队已有规范，否则新项目不推荐。

---

## 专题 H：Markdown 渲染与代码高亮

AI 聊天应用的回复通常包含 Markdown 格式（标题、列表、代码块、表格）。如果直接显示原始文本，用户体验很差。本专题教你在 React 中渲染 Markdown 并高亮代码。

### 为什么需要 Markdown 渲染？

```
AI 原始回复（纯文本）：
  ## 安装步骤\n1. 运行 `pip install fastapi`\n2. 创建 main.py\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n```

渲染后效果：
  ┌─────────────────────────────┐
  │ 安装步骤                     │  ← h2 标题
  │ 1. 运行 pip install fastapi  │  ← 有序列表 + 行内代码
  │ 2. 创建 main.py              │
  │ ┌─────────────────────────┐  │
  │ │ from fastapi import ... │  │  ← 语法高亮代码块
  │ └─────────────────────────┘  │
  └─────────────────────────────┘
```

### 安装依赖

```bash
npm install react-markdown remark-gfm rehype-highlight highlight.js
```

| 包 | 作用 |
|---|---|
| `react-markdown` | 将 Markdown 文本渲染为 React 组件 |
| `remark-gfm` | 支持 GitHub 风格 Markdown（表格、任务列表、删除线） |
| `rehype-highlight` | 代码语法高亮 |
| `highlight.js` | 高亮主题样式 |

### 基本用法

```jsx
// components/MarkdownRenderer.jsx
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';  // 代码高亮主题

const MarkdownRenderer = ({ content }) => (
    <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
    >
        {content}
    </ReactMarkdown>
);

export default MarkdownRenderer;
```

### 在聊天组件中使用

```jsx
// 修改 Message 组件
import MarkdownRenderer from './MarkdownRenderer';

const Message = ({ role, content }) => (
    <div className={`message ${role}`}>
        <div className="avatar">{role === "user" ? "👤" : "🤖"}</div>
        <div className="bubble">
            {role === "ai"
                ? <MarkdownRenderer content={content} />  // AI 回复用 Markdown 渲染
                : <p>{content}</p>                         // 用户消息用纯文本
            }
        </div>
    </div>
);
```

### 样式美化

```css
/* 给 Markdown 内容加样式 */
.bubble pre {
    background: #1e1e1e;
    border-radius: 8px;
    padding: 16px;
    overflow-x: auto;
}

.bubble code {
    font-family: 'Fira Code', monospace;
    font-size: 14px;
}

.bubble table {
    border-collapse: collapse;
    width: 100%;
}

.bubble th, .bubble td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}
```

> 💡 这个功能虽然不复杂，但对用户体验影响巨大——几乎所有 AI 聊天产品都会做 Markdown 渲染。

---

## 专题 I：LangChain / LangGraph 入门

第 16 章你用纯 Python 手写了 Agent 核心循环（~60 行代码）。在实际项目中，当 Agent 变复杂时，可以用**框架**来简化开发。LangChain 和 LangGraph 是目前最流行的 AI 应用开发框架。

### LangChain vs 手写 vs LangGraph

| | 手写（第 16 章） | LangChain | LangGraph |
|---|---|---|---|
| **复杂度** | 简单直接 | 中等 | 较高 |
| **适用** | 理解原理、简单 Agent | 链式调用、RAG 管道 | 复杂多步骤 Agent |
| **优点** | 完全可控，无依赖 | 生态丰富，组件多 | 状态机，可视化流程 |
| **缺点** | 复杂场景代码量大 | 抽象层多，调试难 | 学习曲线陡 |

### LangChain 核心概念

```python
# 安装
# pip install langchain langchain-openai

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 1. 创建 LLM 实例（和你手写的 OpenAI client 对应）
llm = ChatOpenAI(
    model="doubao-pro-32k",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# 2. 直接调用（最简单的用法）
messages = [
    SystemMessage(content="你是一个翻译助手"),
    HumanMessage(content="把'Hello World'翻译成中文")
]
response = llm.invoke(messages)
print(response.content)  # "你好世界"
```

### LangChain 的 Chain（链）

把多个步骤串联起来：

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 定义 Prompt 模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}"),
    ("user", "{input}")
])

# 用 | 管道符串联：模板 → LLM → 输出解析
chain = prompt | llm | StrOutputParser()

# 调用
result = chain.invoke({"role": "Python 教师", "input": "解释什么是装饰器"})
print(result)
```

### LangGraph 简介

LangGraph 是 LangChain 团队出的**图状态机框架**，适合复杂 Agent：

```python
# LangGraph 的核心思想：
# 把 Agent 的执行流程定义为一个有向图

#  ┌─────────┐     ┌──────────┐     ┌─────────┐
#  │  开始    │ ──→ │  AI 决策  │ ──→ │  工具    │
#  └─────────┘     └──────────┘     └─────────┘
#                       ↑                │
#                       └────────────────┘  ← 循环
#                       │
#                       ↓
#                  ┌─────────┐
#                  │  结束    │
#                  └─────────┘
```

### 选型建议

```
你的项目适合用什么？

简单的 LLM 调用 / 对话  →  直接用 OpenAI SDK（第 12 章的方式）
需要 RAG 管道            →  考虑 LangChain
复杂多步骤 Agent         →  考虑 LangGraph
学习和理解原理           →  手写（第 16 章的方式）
```

> 💡 **先理解原理，再用框架**。第 16 章手写的 60 行 Agent 循环就是 LangGraph 的底层逻辑。理解了原理，用任何框架都能举一反三。

---

## 专题 J：Cursor 高效使用指南

第 1 章简单介绍了 Cursor 的三种交互方式。随着你的编程能力提升，Cursor 有很多进阶技巧可以大幅提升开发效率。

### Rules 文件：让 AI 了解你的项目

在项目根目录创建 `.cursorrules` 文件，告诉 AI 你的项目背景：

```
# .cursorrules
你正在开发一个 AI 聊天应用。

技术栈：
- 前端：React + Vite + CSS Modules
- 后端：Python + FastAPI + SQLAlchemy
- AI：OpenAI SDK 协议（兼容豆包 API）
- 数据库：SQLite（开发）/ PostgreSQL（生产）

代码规范：
- Python 使用类型注解
- React 使用函数组件 + Hooks
- API 返回统一用 Pydantic BaseModel
- 所有 API Key 通过环境变量读取
```

有了这个文件，AI 生成的代码会自动符合你的项目规范。

### @ 引用：精确指定上下文

```
@文件名      → 引用特定文件内容作为上下文
@文件夹名    → 引用整个文件夹
@Web         → 让 AI 搜索互联网
@Docs        → 引用官方文档
@Codebase    → 搜索整个代码库
```

**使用场景：**

```
❌ 模糊提问："帮我加一个功能"
✅ 精确提问："参考 @ChatPage.jsx 的代码风格，帮我新建一个 SettingsPage.jsx"

❌ "这个报错怎么修"
✅ "@main.py 运行时报 ImportError: No module named 'database'，帮我检查 import 路径"
```

### Composer 模式：多文件同时编辑

当你需要同时修改多个文件时（如加一个新功能需要改前端 + 后端 + 数据库），用 Composer 模式：

```
快捷键：Cmd+I（Mac）/ Ctrl+I（Windows）

示例指令：
"给聊天应用添加'收藏消息'功能：
 1. 后端 @main.py 加一个 POST /api/favorites 接口
 2. 数据库 @models.py 加一个 Favorite 模型
 3. 前端 @Message.jsx 加一个收藏按钮"
```

### 高效使用的核心原则

```
1. 上下文越精确，AI 输出越好
   → 用 @ 引用相关文件，而不是让 AI 猜

2. 分步提需求，不要一次性写太多
   → "先帮我做后端接口" → 确认没问题 → "再帮我做前端页面"

3. 每次 AI 生成的代码，花 30 秒快速审核
   → 重点看：逻辑是否正确、是否遗漏错误处理、命名是否合理

4. 善用 Cmd+Z（撤销）
   → AI 改坏了？直接撤销，不要手动修复
```

> 💡 Cursor 的核心价值不是"帮你写代码"，而是"让你把精力集中在设计和思考上"。你负责**想清楚要做什么**，AI 负责**快速实现**。

---

# 课程结语

```
从第 1 章到这里，你完成了一段完整的旅程：

  零基础 → 搭建开发环境 → 学会前端和后端 → 连接数据库
  → 调用大模型 API → 实现对话管理 → 搭建知识库（RAG）
  → 让 AI 使用工具 → 构建 AI Agent → 部署上线

你不再是一个"会用 AI 工具的人"，
而是一个"能创造 AI 工具的人"。

这就是这门课程最大的价值。
```
