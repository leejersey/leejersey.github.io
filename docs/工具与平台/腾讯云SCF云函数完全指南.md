# 腾讯云 SCF 云函数部署指南

> 从本地开发到生产上线：手把手教你用 Serverless 云函数部署后端服务

---

## 一、SCF 快速认知

### 1.1 一句话理解 SCF

**SCF（Serverless Cloud Function，云函数）** 是腾讯云提供的无服务器执行环境——你只需要上传代码，腾讯云负责一切基础设施。

用一个类比来理解：

> **传统服务器 = 自己买车** → 买车、加油、保养、找停车位，全部自己操心
> **云服务器 CVM = 租车** → 不用买车了，但还得自己开、自己加油
> **云函数 SCF = 打车** → 说目的地就行，司机（腾讯云）负责一切，按里程（运行时间）付费

SCF 的核心价值可以浓缩为三个"不用管"：

- **不用管服务器**：没有 ECS/CVM 实例需要维护，没有操作系统需要打补丁
- **不用管伸缩**：请求量从 0 到 10000 并发，自动扩缩容，无需配置
- **不用管闲置成本**：没有请求时不计费，真正的"用多少付多少"

**什么场景适合用 SCF？**

| 场景 | 适合度 | 说明 |
|---|---|---|
| API 后端服务 | ⭐⭐⭐⭐⭐ | 轻量级 REST/GraphQL API，天然适合 |
| 定时任务 | ⭐⭐⭐⭐⭐ | 替代 crontab，免维护定时执行 |
| 文件处理 | ⭐⭐⭐⭐ | 图片压缩、视频转码、文档解析 |
| Webhook / 回调 | ⭐⭐⭐⭐ | 接收第三方通知，处理后转发 |
| 长连接服务 | ⭐⭐ | WebSocket 有限支持，不是最佳选择 |
| 高性能计算 | ⭐ | 有执行时间和资源限制，不适合 |

### 1.2 事件函数 vs Web 函数（选哪个？）

SCF 支持两种函数类型，理解它们的区别是部署的第一步：

| 对比维度 | 事件函数（Event Function） | Web 函数（Web Function） |
|---|---|---|
| **触发方式** | 由云端事件触发（COS 上传、定时器、消息队列等） | 由 HTTP 请求直接触发 |
| **入口格式** | 固定入口 `main_handler(event, context)` | 原生 Web 框架（Flask / Express / Koa 等） |
| **请求/响应** | 通过 `event` 字典获取参数，返回字典 | 标准 HTTP Request / Response |
| **适用场景** | 后台任务、数据处理、事件响应 | Web API、网站后端、Webhook |
| **迁移成本** | 需要按 SCF 格式改造代码 | **几乎零改造**，现有 Web 项目直接部署 |

**怎么选？一个简单的决策树：**

```
你的代码需要处理 HTTP 请求吗？
├── 是 → 用 Web 函数（推荐 FastAPI / Express）
│       → 优势：代码可本地运行，也可部署到 SCF，不被厂商绑定
└── 否 → 用事件函数
        → 如：定时清理数据、COS 文件上传后自动处理
```

> 💡 **本指南后续的部署实战以 Web 函数为主**，因为它更贴近日常开发场景，且迁移成本最低。

### 1.3 SCF 的计费逻辑（免费额度 + 按量付费）

SCF 的计费由四部分组成，理解它们能帮你准确预估成本：

```
                    SCF 账单构成
 ═══════════════════════════════════════════════
 
  ① 资源使用费      函数内存 × 运行时间 = GB-s
  ② 调用次数费      每次调用计一次
  ③ 外网出流量费    函数返回给公网的数据流量
  ④ 预置并发费      （可选）提前预留的实例闲置费
  
 ═══════════════════════════════════════════════
  前三项：按量付费，用多少算多少
  第四项：只有开启"预置并发"才会产生
```

**免费额度（每月自动发放）：**

| 计费项 | 免费额度 | 大概够用多少？ |
|---|---|---|
| **资源使用** | 40 万 GB-s | 128MB 内存的函数可免费运行 ~89 小时 |
| **调用次数** | 100 万次 | 小型 API 服务一个月绰绰有余 |
| **外网流量** | 无免费额度 | 约 0.80 元/GB，注意控制响应体大小 |

**一个真实场景的费用估算：**

> 假设你部署了一个轻量 API 服务：
> - 每天被调用 5000 次，每次平均运行 200ms，内存配置 256MB
> - 月调用量：5000 × 30 = **15 万次**（在免费额度内 ✅）
> - 月资源用量：0.256GB × 0.2s × 150000 = **7,680 GB-s**（在免费额度内 ✅）
> - **结论：每月 0 元** 💰

对于大多数个人项目和中小型 API 服务，SCF 的免费额度基本够用。超出部分的单价也非常低：资源使用约 0.00011108 元/GB-s，调用次数约 0.0133 元/万次。

---

> **总结**：SCF 是一个"上传代码就能跑"的无服务器平台，Web 函数是部署 Web 应用的首选类型，免费额度对个人项目和小型服务非常友好。理解了这三点，你已经具备了开始部署的基础认知。

## 二、环境准备与工具链

### 2.1 账号注册与实名认证

在使用 SCF 之前，需要完成以下准备：

**① 注册腾讯云账号**

访问 [腾讯云官网](https://cloud.tencent.com/) 注册账号。支持微信扫码、邮箱、QQ 等多种方式。

**② 完成实名认证**

进入 [账号中心 → 实名认证](https://console.cloud.tencent.com/developer)，完成个人或企业认证。

> ⚠️ **未实名认证的账号无法创建云函数**，这是腾讯云的强制要求。

**③ 开通云函数服务**

访问 [云函数控制台](https://console.cloud.tencent.com/scf)，首次进入会提示开通服务并授权。点击同意即可，开通过程免费。

授权的目的是让 SCF 服务能够访问你的其他云资源（如 COS 存储、VPC 网络等），这是正常的服务角色授权。

### 2.2 安装 Serverless CLI（sls）

Serverless CLI 是部署云函数的核心工具，它能让你在本地一键部署代码到腾讯云。

**安装方式（推荐 npm）：**

```bash
# 全局安装 Serverless CLI
npm install -g serverless

# 验证安装
sls --version
# 输出示例：Framework Core: 3.x.x  Plugin: 7.x.x  SDK: 4.x.x
```

**其他安装方式：**

| 方式 | 命令 | 适用场景 |
|---|---|---|
| **npm（推荐）** | `npm install -g serverless` | 已有 Node.js 环境 |
| **二进制下载** | 从 GitHub Releases 下载 | 不想装 Node.js |
| **腾讯云独立版** | `npm install -g serverless-cloud-framework` | 只用腾讯云（更轻量） |

> 💡 如果你只用腾讯云，`serverless-cloud-framework`（命令缩写 `scf`）是更轻量的选择。但 `serverless` 支持多云，通用性更强。

**前置依赖：**

```bash
# 确保 Node.js >= 14.x
node --version

# 如果没有 Node.js，推荐用 nvm 安装
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

### 2.3 配置腾讯云凭证（SecretId / SecretKey）

Serverless CLI 需要你的腾讯云 API 密钥才能操作云资源。

**① 获取密钥**

进入 [API 密钥管理页面](https://console.cloud.tencent.com/cam/capi)，点击「新建密钥」，获取 `SecretId` 和 `SecretKey`。

> ⚠️ **SecretKey 只在创建时显示一次**，务必立即保存。如果丢失，只能删除旧密钥重新创建。

**② 配置方式（三选一）**

| 方式 | 命令 / 操作 | 特点 |
|---|---|---|
| **扫码登录（推荐）** | `sls login` → 微信扫码 | 最简单，适合个人开发 |
| **环境变量** | 设置 `TENCENT_SECRET_ID` 和 `TENCENT_SECRET_KEY` | 适合 CI/CD 环境 |
| **配置文件** | 在项目根目录创建 `.env` 文件 | 适合多项目管理 |

**方式一：扫码登录（最快上手）**

```bash
# 运行后会弹出二维码，微信扫码授权即可
sls login
```

**方式二：环境变量（推荐用于 CI/CD）**

```bash
# 写入 shell 配置文件（如 ~/.zshrc 或 ~/.bashrc）
export TENCENT_SECRET_ID="你的SecretId"
export TENCENT_SECRET_KEY="你的SecretKey"

# 使配置生效
source ~/.zshrc
```

**方式三：项目级 `.env` 文件**

```bash
# 在项目根目录创建 .env 文件
cat > .env << EOF
TENCENT_SECRET_ID=你的SecretId
TENCENT_SECRET_KEY=你的SecretKey
EOF
```

> ⚠️ **安全提醒**：务必将 `.env` 加入 `.gitignore`，绝对不要将密钥提交到 Git 仓库。

### 2.4 项目初始化（sls init）

凭证配置完成后，就可以初始化一个云函数项目了。

**快速初始化模板项目：**

```bash
# 查看所有可用模板
sls init --list

# 初始化一个 Python Web 函数模板
sls init scf-python --name my-scf-project

# 进入项目目录
cd my-scf-project
```

**初始化后的目录结构：**

```
my-scf-project/
├── serverless.yml       # 部署配置文件（核心）
├── src/                 # 代码目录
│   ├── app.py           # 主入口文件
│   └── requirements.txt # Python 依赖
└── .env                 # 凭证配置（可选）
```

其中 `serverless.yml` 是最关键的文件，它告诉 Serverless CLI "把什么代码、以什么配置、部署到哪里"。这个文件的详细配置将在第四章展开。

**验证环境是否就绪：**

```bash
# 在项目目录下运行部署（试一下能不能跑通）
sls deploy

# 看到类似以下输出说明环境 OK：
# serverless ⚡framework
# Action: "deploy" - Stage: "dev" - App: "my-scf-project"
# region: ap-guangzhou
# functionName: my-scf-project
# url: https://service-xxxxx-xxxxx.gz.apigw.tencentcs.com
```

> 💡 **如果 `sls deploy` 报权限错误**，回到 2.3 检查凭证配置。如果报网络错误，检查是否需要配置代理。

---

> **总结**：完成本章的四步操作后，你的开发环境就绑定了腾讯云账号，并拥有了从本地一键部署到云端的能力。接下来就可以开始实际部署了——先从控制台试试手感。

## 三、控制台部署（适合快速验证）

控制台部署是最直观的方式——打开浏览器，点几下鼠标，代码就在云端跑起来了。适合快速验证想法、学习 SCF 概念，但不适合正式项目的持续部署。

### 3.1 创建第一个云函数（Hello World）

**操作步骤：**

**① 进入云函数控制台**

访问 [云函数控制台](https://console.cloud.tencent.com/scf/list)，点击「新建」。

**② 填写基本配置**

| 配置项 | 推荐值 | 说明 |
|---|---|---|
| **创建方式** | 从头开始 | 也可以选择模板快速体验 |
| **函数类型** | Web 函数 | 部署 Web 应用选这个 |
| **函数名称** | `hello-scf` | 小写字母 + 连字符，全局唯一 |
| **地域** | 广州（ap-guangzhou） | 选离用户最近的地域 |
| **运行环境** | Python 3.9 | 根据你的技术栈选择 |

**③ 编写入口代码**

选择 Web 函数后，控制台会自动生成一个 `app.py` 模板。替换为以下内容：

```python
# app.py - 最简单的 Web 函数示例
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return {
        "message": "Hello from SCF! 🎉",
        "service": "Tencent Cloud Serverless",
    }

# Web 函数要求：必须监听 9000 端口
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
```

> 💡 **关键细节**：Web 函数必须监听 **9000 端口**，这是 SCF 运行时的固定约定。

**④ 点击「完成」创建函数**

创建完成后会自动跳转到函数详情页。

### 3.2 在线编辑与测试

函数创建后，你可以直接在控制台的在线编辑器中修改和测试代码。

**在线测试方法：**

在函数详情页 → 「函数代码」标签页 → 点击「测试」按钮。

对于 Web 函数，你需要构造一个 HTTP 请求来测试：

```json
{
  "httpMethod": "GET",
  "path": "/",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

**期望输出：**

```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Hello from SCF! 🎉\", \"service\": \"Tencent Cloud Serverless\"}"
}
```

**在线编辑器的局限性：**

| 能力 | 支持情况 | 说明 |
|---|---|---|
| 修改代码 | ✅ | 基础编辑功能 |
| 安装依赖 | ❌ | 无法 `pip install`，需要用 Layer |
| 多文件项目 | ⚠️ | 支持但体验较差 |
| 版本管理 | ❌ | 没有 Git 集成 |
| 团队协作 | ❌ | 无法多人编辑 |

> 💡 **建议**：控制台编辑器只用于快速验证和小修小补。正式开发请使用第四章介绍的 CLI 部署方式。

### 3.3 配置函数 URL（HTTP 访问入口）

函数 URL 是 SCF 提供的 HTTP(S) 访问入口，让你的函数可以通过浏览器或 API 调用访问。

> ⚠️ **重要背景**：腾讯云 API 网关已于 2025 年 6 月停服。函数 URL 是官方推荐的替代方案，功能更简洁、延迟更低。

**配置步骤：**

**① 进入触发管理**

函数详情页 → 「触发管理」标签页 → 点击「创建触发器」。

**② 选择触发类型**

| 配置项 | 值 |
|---|---|
| **触发方式** | 函数 URL |
| **认证类型** | 无认证（开发测试用）/ 签名认证（生产环境） |

**③ 获取访问地址**

创建成功后，你会看到一个类似这样的 URL：

```
https://{function-id}-{appid}.{region}.tencentscf.com
```

**验证访问：**

```bash
# 用 curl 测试你的函数 URL
curl https://your-function-url.tencentscf.com/

# 期望输出：
# {"message": "Hello from SCF! 🎉", "service": "Tencent Cloud Serverless"}
```

**函数 URL vs 已停服的 API 网关：**

| 对比 | 函数 URL | API 网关（已停服） |
|---|---|---|
| **维护方** | 云函数团队直接维护 | 独立团队维护 |
| **稳定性** | 减少中间链路，更稳定 | 中间网关可能故障 |
| **功能** | 基础 HTTP 触发 | 丰富的 API 管理功能 |
| **适用场景** | 大多数 Web 服务 | 需要限流/鉴权/API 生命周期管理 |

> 💡 如果你需要更高级的 API 管理能力（限流、鉴权、灰度发布），可以考虑 **TSE 云原生网关**作为替代。

### 3.4 查看日志与监控

函数部署上线后，日志和监控是排查问题的关键手段。

**① 实时日志**

函数详情页 → 「日志查询」标签页，可以查看每次调用的详细日志：

```
日志内容包含：
├── RequestId      每次调用的唯一标识（排查问题必备）
├── 开始/结束时间   精确到毫秒
├── 运行时长        用于分析性能和成本
├── 内存使用        实际用了多少 MB
├── 返回码         HTTP 状态码
└── 打印输出        代码中 print() 的内容
```

**② 通过代码打印日志**

在 Python 中，直接使用 `print()` 即可输出日志：

```python
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@app.route("/api/data")
def get_data():
    logger.info("收到数据请求")      # 会出现在云端日志中
    logger.warning("数据量较大")     # 带级别的日志更易筛选
    return {"data": "..."}
```

**③ 监控指标**

在 「监控信息」标签页，可以查看以下关键指标：

| 指标 | 含义 | 关注点 |
|---|---|---|
| **调用次数** | 函数被触发的总次数 | 流量是否异常 |
| **运行时间** | 每次调用的耗时 | P95 延迟是否达标 |
| **错误次数** | 调用失败的次数 | 错误率是否可接受 |
| **并发执行数** | 同时运行的实例数 | 是否需要调整并发上限 |
| **内存使用** | 实际使用 vs 配置的内存 | 内存是否配置过大（浪费钱）或过小（OOM） |

> 💡 **建议**：为关键函数配置告警规则。进入 [云监控控制台](https://console.cloud.tencent.com/monitor)，设置当错误率超过阈值时发送微信/短信/邮件通知。

---

> **总结**：控制台部署的完整流程是「创建函数 → 在线编码 → 配置触发器 → 查看日志」。这条路径适合快速验证和学习，但对于正式项目，你需要第四章介绍的 CLI 部署——可版本管理、可自动化、可协作。

## 四、CLI 部署（推荐的标准流程）

CLI 部署是正式项目的标准工作流——代码在本地编写和测试，用一条命令推送到云端。支持版本管理、多环境、团队协作，是生产环境的首选方式。

### 4.1 项目目录结构规范

一个规范的 SCF 项目目录应该长这样：

```
my-scf-project/
├── serverless.yml           # ⭐ 部署配置文件（告诉 CLI 怎么部署）
├── .env                     # 🔒 凭证文件（不要提交到 Git）
├── .gitignore               # 忽略 .env、node_modules 等
├── src/                     # 📂 源代码目录
│   ├── app.py               # 主入口文件
│   ├── routes/              # 路由模块
│   │   ├── __init__.py
│   │   └── api.py
│   ├── services/            # 业务逻辑
│   │   └── user_service.py
│   └── requirements.txt     # Python 依赖清单
└── tests/                   # 测试目录（本地测试用）
    └── test_app.py
```

**关键原则：**

- `serverless.yml` 放在项目根目录
- 业务代码放在 `src/` 目录下，通过配置指定代码路径
- `.env` 必须在 `.gitignore` 中
- 依赖文件（`requirements.txt` 或 `package.json`）放在代码目录内

### 4.2 serverless.yml 配置详解

`serverless.yml` 是整个 CLI 部署的灵魂文件。以下是一个 **Web 函数的完整配置示例**，每个字段都有注释：

```yaml
# serverless.yml - SCF Web 函数部署配置

app: my-web-app                    # 应用名称（用于分组管理）
stage: dev                         # 部署环境：dev / staging / prod
component: scf                     # 使用的组件：scf = 云函数
name: my-api-service               # 实例名称

inputs:
  # ========== 基本配置 ==========
  name: ${name}-${stage}           # 函数名（支持变量引用）
  region: ap-guangzhou             # 部署地域
  type: web                        # 函数类型：web / event
  runtime: Python3.9               # 运行时环境
  src: ./src                       # 代码目录路径

  # ========== 资源配置 ==========
  memorySize: 256                  # 内存大小（MB），影响 CPU 算力和计费
  timeout: 30                      # 超时时间（秒），最大 900s
  
  # ========== 环境变量 ==========
  environment:
    variables:
      DB_HOST: "your-db-host"      # 数据库地址
      ENV: ${stage}                # 当前环境标识

  # ========== 函数 URL ==========
  functionUrl:
    auth: NONE                     # 认证方式：NONE / IAM
    # NONE = 无认证（开发测试）
    # IAM  = 签名认证（生产环境）

  # ========== VPC 配置（可选）==========
  # vpcConfig:
  #   vpcId: vpc-xxxxxxxx
  #   subnetId: subnet-xxxxxxxx

  # ========== Layer 配置（可选）==========
  # layers:
  #   - name: my-dependencies
  #     version: 1
```

**常用配置速查表：**

| 配置项 | 类型 | 说明 | 默认值 |
|---|---|---|---|
| `runtime` | string | 运行时 | — |
| `memorySize` | number | 内存 MB（64-3072） | 128 |
| `timeout` | number | 超时秒数（1-900） | 3 |
| `type` | string | `web` 或 `event` | event |
| `src` | string | 代码目录路径 | `.` |
| `region` | string | 部署地域 | ap-guangzhou |

> 💡 **内存与性能的关系**：SCF 的 CPU 算力与内存成正比。128MB 约等于 0.1 核 CPU，256MB ≈ 0.2 核。如果函数需要较高计算性能，增大内存即可。

### 4.3 一键部署（sls deploy）

有了 `serverless.yml`，部署只需一条命令：

```bash
# 在项目根目录执行
sls deploy
```

**部署过程中发生了什么？**

```
sls deploy 执行流程
═══════════════════════════════════════════════════
 
 ① 读取配置    解析 serverless.yml + .env
 ② 打包代码    将 src/ 目录打包为 zip（自动排除 .git 等）
 ③ 上传代码    将 zip 包上传到腾讯云 COS
 ④ 创建/更新   通过 API 创建或更新云函数
 ⑤ 配置触发器  根据配置创建函数 URL 等触发器
 ⑥ 输出结果    返回函数 URL 和其他部署信息
 
═══════════════════════════════════════════════════
```

**部署成功的典型输出：**

```bash
serverless ⚡framework

Action: "deploy" - Stage: "dev" - App: "my-web-app"

type:         web
functionName: my-api-service-dev
region:       ap-guangzhou
url:          https://xxxxxxxx.gz.tencentscf.com   # ← 你的函数访问地址

Full details: https://serverless.cloud.tencent.com/apps/my-web-app/...

36s › my-api-service › Success
```

**常用部署命令：**

| 命令 | 用途 |
|---|---|
| `sls deploy` | 完整部署（创建/更新函数 + 触发器） |
| `sls deploy --debug` | 显示详细部署日志（排错用） |
| `sls deploy --stage prod` | 部署到指定环境 |
| `sls info` | 查看已部署的函数信息 |
| `sls remove` | 删除已部署的函数（⚠️ 慎用） |

### 4.4 部署验证与回滚

代码部署上去不代表万事大吉——你需要验证它确实在正常工作。

**① 快速验证**

```bash
# 用 curl 访问部署输出的 URL
curl https://your-function-url.tencentscf.com/

# 或者用 sls invoke 直接调用
sls invoke --function my-api-service-dev
```

**② 查看实时日志**

```bash
# 实时查看函数日志（类似 tail -f）
sls log --tail

# 查看最近 10 条调用日志
sls log --count 10
```

**③ 出了问题怎么回滚？**

SCF 本身没有内置的"一键回滚"功能，但你可以通过以下方式实现：

```
回滚策略
───────────────────────────────────────
方式 A：Git 回滚 + 重新部署（推荐）
  git revert HEAD        # 撤销最新提交
  sls deploy             # 重新部署上一个版本

方式 B：使用函数版本
  控制台 → 函数管理 → 版本管理
  → 发布新版本（每次部署前手动发布）
  → 出问题时切回旧版本

方式 C：直接在控制台编辑
  紧急救火时可以在线修改代码
  ⚠️ 事后务必同步到本地 Git
───────────────────────────────────────
```

> 💡 **最佳实践**：结合 CI/CD（第八章），每次部署前自动打 Git Tag，需要回滚时直接部署对应 Tag 的代码。

### 4.5 多环境部署（dev / staging / prod）

真实项目至少需要两套环境——开发环境和生产环境。SCF 通过 `stage` 参数实现环境隔离。

**方式一：命令行指定 stage**

```bash
# 部署到开发环境（默认）
sls deploy --stage dev

# 部署到预发布环境
sls deploy --stage staging

# 部署到生产环境
sls deploy --stage prod
```

每个 stage 会创建独立的云函数实例，互不影响：

```
dev 环境:     my-api-service-dev      → https://dev-xxx.tencentscf.com
staging 环境: my-api-service-staging  → https://staging-xxx.tencentscf.com
prod 环境:    my-api-service-prod     → https://prod-xxx.tencentscf.com
```

**方式二：使用不同的 .env 文件**

```bash
# 项目根目录下创建多个环境配置
.env                 # 默认（dev）
.env.staging         # 预发布环境
.env.prod            # 生产环境
```

```bash
# .env.prod 示例
TENCENT_SECRET_ID=prod_secret_id
TENCENT_SECRET_KEY=prod_secret_key
STAGE=prod
DB_HOST=prod-db.example.com
```

**在 serverless.yml 中引用环境变量：**

```yaml
stage: ${env:STAGE, 'dev'}          # 优先读环境变量，默认 dev

inputs:
  environment:
    variables:
      DB_HOST: ${env:DB_HOST}       # 从 .env 读取
      ENV: ${stage}
```

**多环境部署的核心原则：**

| 原则 | 说明 |
|---|---|
| **环境隔离** | 每个 stage 的函数、触发器完全独立 |
| **配置分离** | 数据库、密钥等配置通过环境变量注入，不硬编码 |
| **代码统一** | 所有环境使用同一份代码，仅配置不同 |
| **权限控制** | 生产环境的密钥使用独立的子账号 |

---

> **总结**：CLI 部署的标准流程是「组织目录 → 编写 serverless.yml → `sls deploy` → 验证 → 多环境管理」。相比控制台部署，CLI 方式可版本管理、可自动化、可多人协作，是生产项目的必选方案。

## 五、实战：部署 Python Web 应用到 SCF

前面几章讲了工具和流程，这一章直接上手——以 FastAPI 为例，完整走一遍从编码到上线的全流程。

### 5.1 编写 Web 函数代码（FastAPI 示例）

**创建项目目录：**

```bash
mkdir fastapi-scf && cd fastapi-scf
mkdir src
```

**编写主入口文件 `src/app.py`：**

```python
# src/app.py - FastAPI Web 函数入口
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="My SCF API", version="1.0.0")

@app.get("/")
async def root():
    """健康检查接口"""
    return {
        "status": "running",
        "service": "FastAPI on Tencent SCF",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/hello/{name}")
async def hello(name: str):
    """带参数的 API 示例"""
    return {"message": f"Hello, {name}! 👋"}

@app.get("/api/info")
async def info():
    """系统信息接口"""
    import platform
    return {
        "python_version": platform.python_version(),
        "system": platform.system(),
        "machine": platform.machine()
    }

# ⭐ 关键：SCF Web 函数必须监听 9000 端口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
```

> 💡 **注意**：这段代码可以直接在本地运行（`python src/app.py`），也可以部署到 SCF——代码完全不需要修改，这就是 Web 函数的优势。

**本地测试：**

```bash
# 先安装依赖
pip install fastapi uvicorn

# 本地运行
python src/app.py

# 另开终端测试
curl http://localhost:9000/
curl http://localhost:9000/api/hello/World
```

### 5.2 处理依赖（requirements.txt + Layer）

SCF 运行环境默认只有 Python 标准库，第三方依赖需要你自己处理。

**① 创建 `src/requirements.txt`：**

```txt
fastapi==0.104.1
uvicorn==0.24.0
```

**② 两种依赖安装方式：**

| 方式 | 适用场景 | 优缺点 |
|---|---|---|
| **随代码打包** | 依赖少且体积小 | 简单直接，但每次部署都要上传 |
| **Layer（层）** | 依赖多或体积大 | 依赖只上传一次，多个函数可共享 |

**方式 A：随代码打包（简单项目推荐）**

```bash
# 在 src/ 目录下安装依赖到本地
cd src
pip install -r requirements.txt -t .

# 目录结构变成：
# src/
# ├── app.py
# ├── requirements.txt
# ├── fastapi/          ← 安装到本地的依赖
# ├── uvicorn/
# └── ...
```

**方式 B：使用 Layer（中大型项目推荐）**

```bash
# 1. 在本地打包依赖
mkdir -p layer/python
pip install -r src/requirements.txt -t layer/python

# 2. 将 layer/ 目录压缩为 zip
cd layer && zip -r ../my-layer.zip . && cd ..

# 3. 在控制台上传 Layer
# 控制台 → 层管理 → 新建层
# 层名称：fastapi-deps
# 运行环境：Python 3.9
# 上传 my-layer.zip

# 4. 在 serverless.yml 中引用（见 5.3 节）
```

**Layer 的工作原理：**

```
函数运行时的文件系统
═══════════════════════════════════════
/var/user/                 ← 你的代码（src/ 目录内容）
/opt/                      ← Layer 解压后的内容
  └── python/              ← Python 会自动搜索这个路径
      ├── fastapi/
      ├── uvicorn/
      └── ...
═══════════════════════════════════════
Python 的 import 会同时搜索 /var/user/ 和 /opt/
所以代码中 import fastapi 可以正常工作
```

> 💡 **Layer 的最大价值**：依赖只需上传一次，后续代码更新时不需要重新上传几十 MB 的依赖包，部署速度大幅提升。

### 5.3 配置 serverless.yml

在项目根目录创建 `serverless.yml`：

```yaml
# serverless.yml - FastAPI 部署配置
app: fastapi-scf
stage: dev
component: scf
name: fastapi-api

inputs:
  name: ${name}-${stage}
  region: ap-guangzhou
  type: web                          # Web 函数
  runtime: Python3.9
  src: ./src                         # 代码目录
  memorySize: 256                    # 256MB 内存
  timeout: 30                        # 30 秒超时

  # 环境变量
  environment:
    variables:
      ENV: ${stage}

  # 函数 URL（HTTP 访问入口）
  functionUrl:
    auth: NONE

  # 如果使用 Layer，取消以下注释
  # layers:
  #   - name: fastapi-deps
  #     version: 1
```

**完整的项目目录应该是这样：**

```
fastapi-scf/
├── serverless.yml        # ← 刚创建的配置文件
├── .env                  # ← 凭证（第二章配置的）
├── .gitignore
└── src/
    ├── app.py            # ← 5.1 节写的代码
    ├── requirements.txt  # ← 5.2 节写的依赖
    ├── fastapi/          # ← pip install -t . 安装的（方式 A）
    └── uvicorn/
```

### 5.4 部署与联调

一切就绪，开始部署：

**① 部署**

```bash
# 在项目根目录执行
sls deploy
```

**成功输出示例：**

```bash
serverless ⚡framework

Action: "deploy" - Stage: "dev" - App: "fastapi-scf"

type:         web
functionName: fastapi-api-dev
region:       ap-guangzhou
url:          https://xxxxxxxx.gz.tencentscf.com

46s › fastapi-api › Success
```

**② 逐个接口验证**

```bash
# 测试根路径
curl https://xxxxxxxx.gz.tencentscf.com/
# → {"status":"running","service":"FastAPI on Tencent SCF","timestamp":"..."}

# 测试带参数的接口
curl https://xxxxxxxx.gz.tencentscf.com/api/hello/张三
# → {"message":"Hello, 张三! 👋"}

# 测试系统信息接口
curl https://xxxxxxxx.gz.tencentscf.com/api/info
# → {"python_version":"3.9.x","system":"Linux","machine":"x86_64"}
```

**③ 常见部署问题排查**

| 报错现象 | 原因 | 解决方案 |
|---|---|---|
| `Module not found` | 依赖没打包进去 | 确认 `pip install -t .` 或 Layer 配置正确 |
| `Port 9000 is not listening` | 入口文件没监听 9000 端口 | 检查 `app.run(port=9000)` |
| `Timeout` | 函数启动超时 | 增大 `timeout` 配置，或减少启动时加载的模块 |
| `Memory exceeded` | 内存不足 | 增大 `memorySize`，从 256 调到 512 |
| `Permission denied` | 凭证配置有误 | 检查 `.env` 中的 SecretId / SecretKey |

### 5.5 绑定自定义域名与 HTTPS

SCF 自动分配的函数 URL 又长又难记。上生产环境前，你大概率需要绑定自己的域名。

**① 准备工作**

| 准备项 | 说明 |
|---|---|
| **已备案的域名** | 国内地域必须完成 ICP 备案 |
| **SSL 证书** | 可在腾讯云免费申请 DV 证书 |

**② 配置步骤**

```
自定义域名绑定流程
───────────────────────────────────────
1. 申请 SSL 证书
   控制台 → SSL 证书 → 免费申请
   → 填写域名 → DNS 验证 → 签发

2. 解析域名（CNAME）
   在你的 DNS 服务商处添加：
   类型: CNAME
   主机: api（或你想要的子域名）
   值:  你的函数 URL 域名部分

3. 绑定到云函数
   函数详情 → 触发管理 → 自定义域名
   → 添加域名 → 选择证书 → 保存
───────────────────────────────────────
```

**③ 验证**

```bash
# 使用自定义域名访问
curl https://api.yourdomain.com/
# → {"status":"running","service":"FastAPI on Tencent SCF",...}

# 验证 HTTPS 证书
curl -vI https://api.yourdomain.com/ 2>&1 | grep "SSL certificate"
```

> 💡 **腾讯云免费 SSL 证书**有效期通常为 1 年，到期前需要手动续期。建议设置日历提醒或使用自动化续期方案。

---

> **总结**：本章完整演示了 FastAPI 项目从编码到上线的全流程——编写代码 → 处理依赖 → 配置部署 → 发布验证 → 绑定域名。这套流程是可复制的模板，换成 Flask、Django 等其他 Python Web 框架也同样适用，只需调整入口文件和依赖即可。

## 六、实战：部署 Node.js API 服务到 SCF

如果你的技术栈是 Node.js，部署流程与 Python 大同小异。本章以 Express 为例快速过一遍。

### 6.1 编写 Web 函数代码（Express 示例）

**创建项目：**

```bash
mkdir express-scf && cd express-scf
mkdir src && cd src
npm init -y
npm install express
```

**编写 `src/app.js`：**

```javascript
// src/app.js - Express Web 函数入口
const express = require('express');
const app = express();

// JSON 解析中间件
app.use(express.json());

// 健康检查
app.get('/', (req, res) => {
  res.json({
    status: 'running',
    service: 'Express on Tencent SCF',
    timestamp: new Date().toISOString()
  });
});

// 带参数的 API
app.get('/api/hello/:name', (req, res) => {
  res.json({ message: `Hello, ${req.params.name}! 👋` });
});

// POST 接口示例
app.post('/api/data', (req, res) => {
  const { title, content } = req.body;
  res.json({
    received: true,
    data: { title, content }
  });
});

// ⭐ 关键：监听 9000 端口
const PORT = 9000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
```

**本地测试：**

```bash
node src/app.js
# 另开终端：
curl http://localhost:9000/
curl http://localhost:9000/api/hello/World
```

### 6.2 处理 node_modules 与 Layer

Node.js 的依赖处理比 Python 更简单——`node_modules` 跟代码放在一起即可。

**方式 A：直接打包 node_modules（小型项目）**

```bash
# node_modules 已经在 src/ 目录下了
# Serverless CLI 部署时会自动打包整个 src/ 目录
```

目录结构：

```
express-scf/
├── serverless.yml
└── src/
    ├── app.js
    ├── package.json
    └── node_modules/     ← 直接包含在代码目录中
        └── express/
```

**方式 B：使用 Layer（推荐，依赖 > 10MB 时）**

```bash
# 1. 打包依赖
mkdir -p layer/nodejs
cp src/package.json layer/nodejs/
cd layer/nodejs && npm install --production && cd ../..

# 2. 压缩上传
cd layer && zip -r ../node-layer.zip . && cd ..

# 3. 控制台 → 层管理 → 新建层 → 上传 zip
```

**Node.js Layer 的路径约定：**

```
/opt/nodejs/node_modules/     ← Layer 中的 node_modules
                                 Node.js 会自动搜索这个路径
```

> 💡 **生产建议**：用 `npm install --production` 只安装生产依赖，避免 devDependencies 增大包体积。

### 6.3 部署与验证

**创建 `serverless.yml`：**

```yaml
# serverless.yml - Express 部署配置
app: express-scf
stage: dev
component: scf
name: express-api

inputs:
  name: ${name}-${stage}
  region: ap-guangzhou
  type: web
  runtime: Nodejs16.13            # Node.js 运行时
  src: ./src
  memorySize: 256
  timeout: 30

  functionUrl:
    auth: NONE

  environment:
    variables:
      NODE_ENV: production
      ENV: ${stage}

  # 使用 Layer 时取消注释
  # layers:
  #   - name: express-deps
  #     version: 1
```

**部署并验证：**

```bash
# 部署
sls deploy

# 验证
curl https://your-url.tencentscf.com/
curl https://your-url.tencentscf.com/api/hello/张三
curl -X POST https://your-url.tencentscf.com/api/data \
  -H "Content-Type: application/json" \
  -d '{"title":"测试","content":"Hello SCF"}'
```

**Python vs Node.js 部署对比速查：**

| 对比项 | Python（FastAPI） | Node.js（Express） |
|---|---|---|
| **入口文件** | `app.py` | `app.js` |
| **依赖管理** | `pip install -t .` | `npm install` |
| **Layer 路径** | `/opt/python/` | `/opt/nodejs/node_modules/` |
| **运行时** | `Python3.9` | `Nodejs16.13` |
| **端口** | 9000 | 9000 |
| **部署配置** | 基本相同 | 基本相同 |

---

> **总结**：Node.js 的部署流程与 Python 高度一致——写代码、处理依赖、配置 YAML、一键部署。掌握了任意一种语言的部署方式，切换到另一种只需改入口文件和运行时配置。

## 七、触发器配置实战

前面几章主要使用函数 URL 处理 HTTP 请求。但 SCF 的能力远不止于此——通过不同类型的触发器，你可以让函数在各种场景下自动执行。

### 7.1 函数 URL 触发器（HTTP 访问，推荐）

函数 URL 在第三章已介绍过基本用法，这里补充 **`serverless.yml` 中的配置方式**：

```yaml
# serverless.yml 中配置函数 URL
inputs:
  functionUrl:
    auth: NONE            # 无认证（开发环境）
    # auth: IAM           # IAM 签名认证（生产环境）
```

**认证类型选择：**

| 认证类型 | 安全级别 | 适用场景 |
|---|---|---|
| **NONE** | 低 | 开发测试、公开 API、Webhook 回调 |
| **IAM** | 高 | 内部服务间调用、敏感数据接口 |

> 💡 **生产环境建议**：即使使用 `NONE` 认证，也应在应用层实现自己的鉴权逻辑（如 JWT Token），不要完全依赖平台认证。

### 7.2 定时触发器（Cron 定时任务）

定时触发器让函数按固定周期自动执行，完美替代传统的 crontab。

**典型用途：**
- 每天清理过期数据
- 每小时同步第三方 API 数据
- 每周生成统计报表
- 定时健康检查

**在 `serverless.yml` 中配置：**

```yaml
inputs:
  type: event                        # 定时触发用事件函数
  runtime: Python3.9
  handler: index.main_handler        # 事件函数需指定 handler
  src: ./src

  events:
    - timer:
        name: daily-cleanup          # 触发器名称
        parameters:
          cronExpression: "0 2 * * *"   # 每天凌晨 2 点执行
          enable: true
          argument: '{"task": "cleanup"}'  # 传给函数的参数（可选）
```

**Cron 表达式速查：**

```
 ┌───── 分（0-59）
 │ ┌───── 时（0-23）
 │ │ ┌───── 日（1-31）
 │ │ │ ┌───── 月（1-12）
 │ │ │ │ ┌───── 周几（0-6，0=周日）
 │ │ │ │ │
 * * * * *
```

| 表达式 | 含义 |
|---|---|
| `0 2 * * *` | 每天凌晨 2:00 |
| `*/5 * * * *` | 每 5 分钟 |
| `0 9 * * 1` | 每周一早上 9:00 |
| `0 0 1 * *` | 每月 1 号零点 |
| `0 */2 * * *` | 每 2 小时 |

**对应的事件函数代码：**

```python
# src/index.py - 定时任务示例
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main_handler(event, context):
    """定时触发器入口"""
    # event 包含触发器传入的参数
    trigger_msg = json.loads(event.get("Message", "{}"))
    task = trigger_msg.get("task", "default")
    
    logger.info(f"定时任务开始执行: {task}")
    
    if task == "cleanup":
        # 执行清理逻辑
        cleaned_count = do_cleanup()
        logger.info(f"清理完成，共清理 {cleaned_count} 条记录")
    
    return {"statusCode": 200, "body": f"Task {task} completed"}

def do_cleanup():
    """模拟清理过期数据"""
    # 实际项目中连接数据库执行清理
    return 42
```

### 7.3 COS 触发器（文件上传自动处理）

COS（对象存储）触发器让函数在文件上传、删除等事件发生时自动执行——非常适合图片处理、文件转换等场景。

**典型用途：**
- 用户上传图片后自动生成缩略图
- 上传 CSV 文件后自动导入数据库
- 上传视频后自动转码

**`serverless.yml` 配置：**

```yaml
inputs:
  type: event
  runtime: Python3.9
  handler: index.main_handler
  src: ./src

  events:
    - cos:
        name: image-upload-trigger
        parameters:
          bucket: my-bucket-1250000000    # COS 存储桶名称
          filter:
            prefix: uploads/              # 只监听 uploads/ 目录
            suffix: .jpg                  # 只监听 .jpg 文件
          events: "cos:ObjectCreated:*"   # 触发事件类型
          enable: true
```

**事件类型说明：**

| 事件 | 含义 |
|---|---|
| `cos:ObjectCreated:*` | 文件创建（上传、复制等） |
| `cos:ObjectCreated:Put` | 仅 Put 上传 |
| `cos:ObjectRemove:*` | 文件删除 |

**处理函数代码示例：**

```python
# src/index.py - COS 触发器：自动处理上传的图片
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main_handler(event, context):
    """COS 文件上传触发"""
    # 从 event 中提取文件信息
    for record in event.get("Records", []):
        cos_info = record["cos"]
        bucket = cos_info["cosBucket"]["name"]
        key = cos_info["cosObject"]["key"]       # 文件路径
        size = cos_info["cosObject"]["size"]      # 文件大小（字节）
        
        logger.info(f"新文件上传: {key}, 大小: {size} bytes")
        
        # 在这里执行你的处理逻辑
        # 例如：生成缩略图、解析文件内容等
        process_file(bucket, key)
    
    return {"statusCode": 200}

def process_file(bucket, key):
    """处理上传的文件"""
    logger.info(f"正在处理: {bucket}/{key}")
    # 实际项目中：下载文件 → 处理 → 上传结果
```

### 7.4 消息队列触发器（异步任务处理）

消息队列触发器让函数消费队列中的消息，适合解耦和异步处理场景。

**支持的消息队列：**

| 队列服务 | 适用场景 |
|---|---|
| **CMQ（消息队列）** | 通用消息队列，简单易用 |
| **CKafka** | 高吞吐场景，日志收集、流数据处理 |
| **TDMQ（Pulsar）** | 多租户、多协议支持 |

**CKafka 触发器配置示例：**

```yaml
inputs:
  type: event
  runtime: Python3.9
  handler: index.main_handler
  src: ./src

  events:
    - ckafka:
        name: order-consumer
        parameters:
          name: ckafka-xxxx             # CKafka 实例 ID
          topic: order-events           # 消费的 Topic
          maxMsgNum: 100                # 单次最大拉取消息数
          offset: latest                # 从最新位置开始消费
          enable: true
```

**消费函数代码示例：**

```python
# src/index.py - CKafka 消息消费
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main_handler(event, context):
    """消费 Kafka 消息"""
    records = event.get("Records", [])
    logger.info(f"收到 {len(records)} 条消息")
    
    for record in records:
        # 解析消息内容
        message = record["Ckafka"]["msgBody"]
        data = json.loads(message)
        
        logger.info(f"处理订单: {data.get('order_id')}")
        # 执行业务逻辑...
    
    return {"statusCode": 200}
```

**触发器选型决策树：**

```
你的函数需要什么时候执行？
├── 收到 HTTP 请求时 → 函数 URL（7.1）
├── 定时执行 → 定时触发器（7.2）
├── 文件上传/删除时 → COS 触发器（7.3）
├── 收到消息时 → 消息队列触发器（7.4）
└── 其他云服务事件 → 查看官方文档支持的触发器列表
```

---

> **总结**：触发器是 SCF 事件驱动架构的核心——函数 URL 处理 HTTP 请求、定时器替代 crontab、COS 触发文件处理、消息队列实现异步解耦。大多数业务场景可以通过这四种触发器的组合来覆盖。

## 八、CI/CD 自动化部署

手动执行 `sls deploy` 只适合个人开发。当团队协作或项目进入生产阶段，你需要自动化部署——代码推送到 Git 后自动触发部署。

### 8.1 GitHub Actions 自动部署

GitHub Actions 是最流行的 CI/CD 方案之一，配置简单且免费额度充足。

**创建 `.github/workflows/deploy.yml`：**

::: v-pre
```yaml
# .github/workflows/deploy.yml
name: Deploy to Tencent SCF

on:
  push:
    branches: [main]        # main 分支推送时触发
  workflow_dispatch:         # 支持手动触发

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      # 1. 拉取代码
      - name: Checkout code
        uses: actions/checkout@v4

      # 2. 安装 Node.js（Serverless CLI 依赖）
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      # 3. 安装 Serverless CLI
      - name: Install Serverless
        run: npm install -g serverless

      # 4. 安装 Python 依赖（如果用随代码打包方式）
      - name: Install Python dependencies
        run: |
          pip install -r src/requirements.txt -t src/

      # 5. 部署到腾讯云
      - name: Deploy
        run: sls deploy --stage $&#123;&#123; github.ref == 'refs/heads/main' && 'prod' || 'dev' &#125;&#125;
        env:
          TENCENT_SECRET_ID: $&#123;&#123; secrets.TENCENT_SECRET_ID &#125;&#125;
          TENCENT_SECRET_KEY: $&#123;&#123; secrets.TENCENT_SECRET_KEY &#125;&#125;
```
:::

**配置 GitHub Secrets：**

```
仓库页面 → Settings → Secrets and variables → Actions → New repository secret

添加两个 Secret：
├── TENCENT_SECRET_ID    = 你的 SecretId
└── TENCENT_SECRET_KEY   = 你的 SecretKey
```

**工作流触发逻辑：**

```
代码推送到 main 分支
       ▼
GitHub Actions 自动触发
       ▼
拉取代码 → 安装依赖 → sls deploy --stage prod
       ▼
部署到腾讯云生产环境 ✅
```

> 💡 **进阶**：可以配置多分支策略——`dev` 分支推送部署到开发环境，`main` 分支推送部署到生产环境。上面的示例已通过三元表达式实现了这个逻辑。

### 8.2 腾讯云 CODING 流水线部署

如果你的代码托管在腾讯云 CODING 上，可以使用 CODING CI 实现部署。

**创建 `Jenkinsfile`（CODING CI 使用 Jenkinsfile 语法）：**

```groovy
pipeline {
  agent any
  
  stages {
    stage('安装依赖') {
      steps {
        sh 'npm install -g serverless'
        sh 'pip install -r src/requirements.txt -t src/'
      }
    }
    
    stage('部署') {
      steps {
        withCredentials([
          string(credentialsId: 'tencent-secret-id', variable: 'TENCENT_SECRET_ID'),
          string(credentialsId: 'tencent-secret-key', variable: 'TENCENT_SECRET_KEY')
        ]) {
          sh 'sls deploy --stage prod'
        }
      }
    }
  }
  
  post {
    success { echo '部署成功 ✅' }
    failure { echo '部署失败 ❌' }
  }
}
```

**GitHub Actions vs CODING CI 对比：**

| 对比项 | GitHub Actions | CODING CI |
|---|---|---|
| **代码托管** | GitHub | 腾讯云 CODING |
| **配置文件** | `.github/workflows/*.yml` | `Jenkinsfile` |
| **免费额度** | 2000 分钟/月（私有仓库） | 根据团队版本而定 |
| **与腾讯云集成** | 需自行配置密钥 | 原生集成，配置更简单 |
| **推荐场景** | 开源项目、个人项目 | 团队项目、企业项目 |

### 8.3 部署脚本编写与环境变量管理

在 CI/CD 流程中，部署脚本和环境变量管理是两个容易踩坑的环节。

**① 通用部署脚本 `scripts/deploy.sh`：**

```bash
#!/bin/bash
# scripts/deploy.sh - 通用部署脚本

set -e  # 出错即停止

STAGE=${1:-dev}  # 默认部署到 dev 环境

echo "🚀 开始部署到 ${STAGE} 环境..."

# 安装依赖
echo "📦 安装 Python 依赖..."
pip install -r src/requirements.txt -t src/ --quiet

# 部署
echo "☁️  部署中..."
sls deploy --stage ${STAGE}

# 打 Git Tag（仅生产环境）
if [ "$STAGE" = "prod" ]; then
  TAG="deploy-$(date +%Y%m%d-%H%M%S)"
  git tag ${TAG}
  git push origin ${TAG}
  echo "🏷️  已创建 Tag: ${TAG}"
fi

echo "✅ 部署完成！"
```

```bash
# 使用方式
chmod +x scripts/deploy.sh
./scripts/deploy.sh dev      # 部署到开发环境
./scripts/deploy.sh prod     # 部署到生产环境
```

**② 环境变量管理最佳实践：**

```
环境变量分层管理
═══════════════════════════════════════════════════

第 1 层：CI/CD 平台 Secrets（最高优先级）
  ├── TENCENT_SECRET_ID      密钥类，绝不写入代码
  └── TENCENT_SECRET_KEY

第 2 层：serverless.yml 中的 ${env:VAR}
  ├── DB_HOST                按环境变化的配置
  ├── REDIS_URL
  └── API_KEY

第 3 层：代码中的默认值
  └── port = os.getenv("PORT", "9000")   兜底默认值

═══════════════════════════════════════════════════
原则：敏感信息 → Secrets；环境差异 → .env；通用默认 → 代码
```

**③ `.gitignore` 必须包含的项：**

```gitignore
# 凭证和环境配置
.env
.env.*

# 依赖目录（如果用随代码打包方式）
src/fastapi/
src/uvicorn/
src/node_modules/

# Serverless 缓存
.serverless/
```

---

> **总结**：CI/CD 自动化部署的核心是「代码即部署」——推送代码自动触发构建和发布。GitHub Actions 适合开源和个人项目，CODING CI 适合腾讯云生态的团队项目。无论选哪个平台，密钥管理和环境变量分层都是必须做好的基础环节。

## 九、生产部署清单

代码能跑和代码能上生产是两码事。本章汇总上线前必须关注的配置项，帮你避开常见踩坑。

### 9.1 上线前 Checklist

每次上线前，逐项检查以下清单：

**🔒 安全类**

| 检查项 | 状态 | 说明 |
|---|---|---|
| `.env` 已加入 `.gitignore` | ☐ | 密钥不能进代码仓库 |
| 生产环境使用独立子账号密钥 | ☐ | 最小权限原则 |
| 函数 URL 认证方式已确认 | ☐ | 敏感接口用 IAM 认证 |
| 应用层鉴权已实现 | ☐ | JWT / API Key 等 |
| 环境变量中无硬编码密码 | ☐ | 通过 Secrets 管理 |

**⚙️ 配置类**

| 检查项 | 状态 | 说明 |
|---|---|---|
| `memorySize` 已根据压测调优 | ☐ | 过大浪费钱，过小 OOM |
| `timeout` 已设置合理值 | ☐ | 太短误杀，太长占资源 |
| 环境变量区分 dev / prod | ☐ | 数据库地址等不能用错 |
| VPC 配置已就绪（如需） | ☐ | 访问内网资源必须配 |
| Layer 版本已固定 | ☐ | 避免依赖意外更新 |

**📊 可观测性**

| 检查项 | 状态 | 说明 |
|---|---|---|
| 日志级别设为 INFO 或 WARNING | ☐ | DEBUG 日志太多会增加成本 |
| 监控告警已配置 | ☐ | 错误率、延迟、并发数 |
| 关键接口有请求日志 | ☐ | 问题排查的基础 |

**🚀 部署类**

| 检查项 | 状态 | 说明 |
|---|---|---|
| CI/CD 流水线已跑通 | ☐ | 手动部署不适合生产 |
| 回滚方案已准备 | ☐ | Git Tag 或函数版本 |
| 已在 staging 环境验证 | ☐ | 不要直接上 prod |

### 9.2 VPC 网络配置（访问数据库等内网资源）

默认情况下，SCF 函数运行在公网环境中，无法直接访问 VPC 内的资源（如云数据库、Redis、ES 等）。如果你的函数需要连接这些内网服务，必须配置 VPC。

**配置方式：**

```yaml
# serverless.yml 中添加 VPC 配置
inputs:
  vpcConfig:
    vpcId: vpc-xxxxxxxx           # VPC ID
    subnetId: subnet-xxxxxxxx     # 子网 ID（必须和数据库在同一可用区）
```

**VPC 配置后的网络拓扑：**

```
                   ┌─────────────────────────┐
                   │      VPC 私有网络         │
                   │                         │
 用户请求 ──▶ SCF 函数 ──────▶ 云数据库 MySQL   │
               │           ──▶ Redis          │
               │           ──▶ ES             │
               │                              │
               └──────────────────────────────┘
               │
               ▼
           公网访问（需配置 NAT 网关）
```

**⚠️ 重要注意事项：**

| 问题 | 说明 |
|---|---|
| **配置 VPC 后无法访问公网** | 需要额外配置 NAT 网关才能访问外部 API |
| **子网选择** | 必须与目标资源在同一可用区 |
| **冷启动变慢** | VPC 模式下冷启动会增加 2-5 秒 |
| **IP 不固定** | 每次函数启动可能获得不同的内网 IP |

> 💡 **如果你的函数既要访问内网资源又要调用外部 API**（比如调用 OpenAI 接口），必须同时配置 VPC 和 NAT 网关，否则外部请求会失败。

### 9.3 并发管理与预置并发

SCF 默认支持自动扩缩容，但在生产环境你可能需要精细控制并发行为。

**并发相关概念：**

```
并发数 = 同一时刻正在运行的函数实例数

例如：
├── 函数平均执行时间：200ms
├── 每秒请求量（QPS）：100
└── 预期并发数 = 100 × 0.2 = 20 个实例同时运行
```

**并发配置：**

| 配置项 | 说明 | 默认值 |
|---|---|---|
| **账号并发上限** | 整个账号下所有函数的总并发 | 300（可申请提升） |
| **函数并发上限** | 单个函数的最大并发 | 等于账号上限 |
| **预置并发** | 提前预热的实例数 | 0（不预留） |

**预置并发——消灭冷启动：**

冷启动是 Serverless 的经典痛点。当一段时间没有请求后，函数实例会被回收，下次请求需要重新创建实例（冷启动），耗时可达 1-5 秒。

```yaml
# serverless.yml 中配置预置并发
inputs:
  provisionedConcurrencyConfig:
    - version: $LATEST
      minCapacity: 2              # 始终保持 2 个实例热备
```

**是否开启预置并发的决策：**

| 场景 | 建议 |
|---|---|
| 接口延迟敏感（< 500ms） | ✅ 开启，预留 2-5 个实例 |
| 内部工具 / 管理后台 | ❌ 不需要，偶尔冷启动可接受 |
| 定时任务 | ❌ 不需要，触发时间固定 |
| 高并发 API（QPS > 100） | ✅ 开启，预留数 = 预期并发数的 50% |

> ⚠️ **预置并发会产生闲置费用**——即使没有请求，预留的实例也在计费。请根据实际业务量权衡。

### 9.4 日志与监控告警配置

生产环境的可观测性至关重要——你不能等用户反馈了才知道有问题。

**① 结构化日志（推荐）**

```python
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@app.get("/api/data")
async def get_data(request):
    # 结构化日志，方便后续检索和分析
    logger.info(json.dumps({
        "action": "get_data",
        "request_id": request.headers.get("x-request-id", ""),
        "user_agent": request.headers.get("user-agent", ""),
        "status": "success"
    }, ensure_ascii=False))
    return {"data": "..."}
```

**② 配置监控告警**

在 [云监控控制台](https://console.cloud.tencent.com/monitor/alarm2/policy) 创建告警策略：

| 告警指标 | 推荐阈值 | 通知方式 |
|---|---|---|
| **错误率** | > 5% 持续 5 分钟 | 微信 + 短信 |
| **P95 延迟** | > 3 秒持续 5 分钟 | 微信 |
| **并发数** | > 账号上限的 80% | 微信 + 邮件 |
| **函数执行失败** | > 10 次/分钟 | 微信 + 短信 |
| **内存使用率** | > 90% | 微信 |

**③ 日志持久化**

SCF 的实时日志默认保留 7 天。如需更长时间保留，建议将日志投递到 CLS（日志服务）：

```yaml
# serverless.yml 中配置日志投递
inputs:
  cls:
    logsetId: xxxxxxxx-xxxx        # CLS 日志集 ID
    topicId: xxxxxxxx-xxxx         # CLS 日志主题 ID
```

### 9.5 常见部署问题排查

以下是实际使用 SCF 时最常遇到的问题和解决方案：

**🔴 部署阶段问题**

| 问题 | 原因 | 解决方案 |
|---|---|---|
| `The appid is unavailable` | 密钥配置错误 | 检查 `.env` 或环境变量中的 SecretId/Key |
| `Code size exceeded` | 代码包超过 500MB 限制 | 用 Layer 分离依赖，或用 `.slsignore` 排除无用文件 |
| `Timeout` in deploy | 上传大文件超时 | 检查网络，尝试 `sls deploy --debug` |
| `YAML parse error` | serverless.yml 格式错误 | 检查缩进、冒号后的空格 |

**🟡 运行阶段问题**

| 问题 | 原因 | 解决方案 |
|---|---|---|
| `Module not found` | 依赖未打包到代码目录 | `pip install -t .` 或检查 Layer 配置 |
| `Port 9000 not listening` | Web 函数没有监听 9000 端口 | 确认 `app.run(port=9000)` |
| `Connection refused`（访问数据库） | 未配置 VPC | 添加 vpcConfig 配置 |
| `Request timeout` | 函数执行超时 | 增大 timeout 或优化代码性能 |
| `Out of memory` | 内存不足 | 增大 memorySize |
| `ECONNREFUSED`（调用外部 API） | VPC 模式下无法访问公网 | 配置 NAT 网关 |

**🟢 性能优化技巧**

```
减少冷启动时间的方法
───────────────────────────────────────
1. 减少包体积
   → 只打包生产依赖
   → 用 .slsignore 排除测试文件、文档等

2. 延迟加载
   → 把重量级的 import 放到函数内部
   → 不在模块顶层做耗时初始化

3. 连接复用
   → 数据库连接放在 handler 外部（全局作用域）
   → 利用实例复用减少重复连接

4. 预置并发
   → 延迟敏感的接口开启预置并发
───────────────────────────────────────
```

**连接复用示例：**

```python
# ✅ 正确：连接放在全局作用域，实例复用时不会重复创建
import pymysql

conn = None

def get_connection():
    global conn
    if conn is None or not conn.open:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
    return conn

# ❌ 错误：每次调用都新建连接
def bad_handler(event, context):
    conn = pymysql.connect(...)  # 每次都新建，浪费时间
```

---

> **总结**：生产部署不仅仅是 `sls deploy` 一条命令的事。安全加固、网络配置、并发管理、监控告警、问题排查——这些环节共同构成了一个可靠的生产环境。建议将 9.1 的 Checklist 打印出来，每次上线前逐项检查。

---

> **全文总结**：本指南以部署流程为主线，从 SCF 的基本概念出发，覆盖了控制台部署、CLI 标准部署、Python/Node.js 实战、触发器配置、CI/CD 自动化，直到生产环境的完整部署清单。掌握这九个章节的内容后，你已经具备了将任何后端应用部署到腾讯云 SCF 的全部技能——把精力放在业务代码上，把基础设施交给云。
