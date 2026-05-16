# 腾讯云 SCF Demo 部署实战

> 最小成本验证腾讯云云函数，为后续项目迁移（React + Python + PostgreSQL）探路。

---

## 1. 前置准备

### 1.1 已完成

- [x] 腾讯云账号注册 + 实名认证
- [x] 开通云函数服务（控制台：https://console.cloud.tencent.com/scf）
- [x] **开通 CLS 日志服务**（控制台：https://console.cloud.tencent.com/cls/overview）
- [x] 领取免费套餐（个人高级版，0 元/月）
- [x] 安装腾讯云专用 CLI：`npm install -g serverless-cloud-framework`

> ⚠️ **CLI 区分**：`serverless`（sls）是 v4 国际版，不兼容腾讯云组件。腾讯云部署必须用 `serverless-cloud-framework`（命令缩写 `scf`）。

> ⚠️ **CLS 必须开通**：SCF 云函数会自动将日志写入 CLS，不开通会报错 `CLS service is unregistered`。CLS 开通免费（每月 5GB 免费额度）。

### 1.2 登录授权

```bash
# 微信扫码授权（首次需要）
scf login
```

扫码后终端显示 `Login Successful` 即可。

---

## 2. Demo 项目结构

项目位置：`scf-demo/`

```
scf-demo/
├── serverless.yml    # 部署配置
├── index.py          # 函数入口（3 个 API 端点）
└── .slsignore        # 部署忽略文件
```

### 2.1 部署配置 serverless.yml

```yaml
app: scf-demo
component: scf
name: scf-demo-api

inputs:
  name: scf-demo-api
  src: ./
  handler: index.main_handler
  runtime: Python3.9
  region: ap-guangzhou
  memorySize: 128          # 最小内存，省钱
  timeout: 30              # AI 场景可调大到 300

  environment:
    variables:
      ENV: production

  functionUrl:
    enable: true
    auth:
      type: NONE           # Demo 用，无认证
```

### 2.2 函数代码 index.py

提供 3 个测试端点：

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/health` | GET | 健康检查，测冷启动延迟 |
| `/api/hello?name=xx` | GET/POST | Hello World，验证参数传递 |
| `/api/cost-test` | GET | 模拟 AI 耗时请求（2s），测费用 |

---

## 3. 部署步骤

### 步骤 1：部署到腾讯云

```bash
cd scf-demo
scf deploy
```

首次部署约 30-60 秒，成功后输出函数名和配置信息。

> ⚠️ `serverless.yml` 中的 `functionUrl` 配置**不会自动生效**，需要手动在控制台创建。

### 步骤 1.5：创建函数 URL（手动）

`scf deploy` 只创建函数本身，不会自动创建 HTTP 访问入口。需要手动开启：

1. 打开 [云函数控制台](https://console.cloud.tencent.com/scf/list) → 找到 `scf-demo-api` → 点进去
2. 左侧菜单点「**函数 URL**」
3. 点「**新建函数 URL**」
4. 配置：

| 配置项 | 选择 | 说明 |
|--------|------|------|
| 公网访问 | ✅ 启用 | 必须勾选，否则外网无法访问 |
| 内网访问 | ☐ 不勾 | Demo 不需要 |
| CORS | ☐ 不勾 | 代码里已处理 |
| 授权类型 | 开放 | Demo 用，无认证 |
| 参数兼容 | ✅ 启用 | 兼容 API 网关参数格式 |

5. 点「确定」→ 页面显示函数 URL 地址

> 📝 拿到的 URL 格式：`https://xxxxxxxx-xxxxxxxxxx.gz.tencentscf.com`

### 步骤 2：测试函数

```bash
# 替换为你的实际 URL
export SCF_URL="https://你的函数URL"

# 1. 健康检查
curl $SCF_URL/api/health
# → {"status":"ok","message":"SCF 运行正常 🎉"}

# 2. Hello World（GET）
curl "$SCF_URL/api/hello?name=摩羯"
# → {"message":"你好，摩羯！","request_id":"...","memory_limit":128}

# 3. Hello World（POST）
curl -X POST $SCF_URL/api/hello \
  -H "Content-Type: application/json" \
  -d '{"name": "摩羯"}'

# 4. 模拟 AI 耗时请求
curl $SCF_URL/api/cost-test
# → {"message":"模拟 AI 推理完成","duration_ms":2001,"cost_estimate":"0.2500 GBs"}
```

### 步骤 3：验证费用

```bash
# 查看实时日志
scf logs --tail
```

去控制台查看费用：https://console.cloud.tencent.com/scf/list

#### 费用计算公式

```
每次调用费用 = 内存(GB) × 运行时间(s) × 单价(¥0.00011108/GBs)

示例：
  /api/health（128MB, 50ms）：0.125 × 0.05 × 0.00011108 ≈ ¥0.0000007（可忽略）
  /api/cost-test（128MB, 2s）：0.125 × 2 × 0.00011108 ≈ ¥0.000028
  
  1 万次 AI 请求（2s/次）的费用：0.000028 × 10000 ≈ ¥0.28
  → 几乎免费
```

### 步骤 4：测完清理

```bash
# 删除函数（不再产生费用）
scf remove
```

---

## 4. 关键发现记录

部署后在这里记录实测数据，用于决策正式迁移方案：

| 测试项 | 预期 | 实测结果 |
|--------|------|----------|
| 冷启动延迟 | 200-500ms | ⬜ 待测 |
| 热启动延迟 | <50ms | ⬜ 待测 |
| `/api/cost-test` 耗时 | ~2000ms | ⬜ 待测 |
| 当月费用 | ¥0 | ⬜ 待测 |
| 部署流程体验 | - | ⬜ 待测 |

---

## 5. 正式迁移方案（验证通过后）

### 目标架构

```
React 前端              Python+AI 后端             数据库
┌──────────────┐      ┌──────────────────┐     ┌──────────────┐
│  COS 静态托管  │      │  SCF / 轻量服务器  │     │ TDSQL-C      │
│  + CDN 加速   │ ←→  │  FastAPI + OpenAI │ ←→  │ PostgreSQL   │
└──────────────┘      └──────────────────┘     └──────────────┘
```

### 需要开通的服务

| 服务 | 用途 | 预估月费 |
|------|------|----------|
| SCF 云函数 | Python 后端 | ¥0-50 |
| COS + CDN | React 前端托管 | ¥5-20 |
| TDSQL-C Serverless | PostgreSQL | ¥30-100+ |
| **总计** | | **¥35-170/月** |

### ⚠️ 迁移前要确认的问题

1. **流式输出**：SCF 是否支持 SSE 长连接？如果不支持 → 改用轻量应用服务器
2. **冷启动**：AI 模型加载的冷启动是否可接受？
3. **数据库连接**：SCF 并发时 PostgreSQL 连接数是否够用？
4. **外网流量**：免费 2GB 是否够用？

---

**验证完成后，根据实测数据决定：SCF 还是轻量应用服务器。**
