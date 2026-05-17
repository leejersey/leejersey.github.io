# GitHub Actions 自动化部署

> 从零掌握 GitHub Actions——用 Workflow 实现代码提交后自动测试、构建 Docker 镜像、推送到镜像仓库、部署到服务器的完整 CI/CD 流水线，覆盖前端/后端/全栈项目的自动化部署实践。

---

## 1. GitHub Actions 核心概念：CI/CD 从手动到自动

代码写完 → 跑测试 → 构建镜像 → 推送仓库 → SSH 到服务器 → 拉镜像 → 重启服务——每次部署都要重复这 7 步。GitHub Actions 让这一切在 `git push` 后自动完成。

### 1.1 为什么需要 CI/CD：告别手动部署

```
没有 CI/CD 的部署流程：

  git push
      │
      ▼ （手动）
  本地跑测试 → 忘了跑 → 线上有 bug 🐛
      │
      ▼ （手动）
  docker build → docker push → SSH → docker pull
      │
      ▼ （半小时后）
  终于部署完了 → 发现推错分支了 😱

  ═══════════════════════════════════════

有了 CI/CD：

  git push
      │
      ▼ （全自动）
  测试 → 构建 → 推送 → 部署
      │
      ▼ （3 分钟后）
  ✅ 部署完成，Slack 收到通知
```

| 概念 | 全称 | 含义 |
|:---|:---|:---|
| **CI** | Continuous Integration | 每次提交自动跑测试，尽早发现问题 |
| **CD** | Continuous Delivery | 自动构建产物（镜像/包），随时可发布 |
| **CD** | Continuous Deployment | 自动部署到生产环境，push 即上线 |

### 1.2 核心概念：Workflow、Job、Step、Action、Runner

```
GitHub Actions 的层级结构：

  Workflow（工作流）
  ├── .github/workflows/deploy.yml     ← 一个 YAML 文件 = 一个 Workflow
  │
  ├── Job 1: test（测试）              ← 一组步骤，跑在一台机器上
  │   ├── Step 1: checkout              ← 一个操作
  │   ├── Step 2: setup-python
  │   ├── Step 3: pip install
  │   └── Step 4: pytest
  │
  ├── Job 2: build（构建）             ← 可以依赖 Job 1
  │   ├── Step 1: checkout
  │   ├── Step 2: docker build
  │   └── Step 3: docker push
  │
  └── Job 3: deploy（部署）            ← 可以依赖 Job 2
      ├── Step 1: SSH 到服务器
      └── Step 2: docker compose up
```

| 概念 | 类比 | 说明 |
|:---|:---|:---|
| **Workflow** | 流水线 | 一个 YAML 文件定义一条流水线 |
| **Job** | 工位 | 跑在独立的虚拟机上，可并行 |
| **Step** | 工序 | Job 内的一个操作，按顺序执行 |
| **Action** | 工具 | 可复用的操作（官方/社区提供） |
| **Runner** | 工人 | 执行 Job 的机器（GitHub 提供或自托管） |

### 1.3 与 Jenkins / GitLab CI 的对比

| 特性 | GitHub Actions | Jenkins | GitLab CI |
|:---|:---|:---|:---|
| 托管方式 | GitHub 托管 | 自建 | GitLab 托管 |
| 配置格式 | YAML | Groovy | YAML |
| 生态 | Marketplace 丰富 | 插件多但杂 | 内置功能全 |
| 免费额度 | 2000 分钟/月 | 无（自建） | 400 分钟/月 |
| 上手难度 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

### 1.4 免费额度与计费规则

```
GitHub Actions 免费额度（公开仓库无限制）：

  私有仓库：
  ──────────────────────────────────
  Free 计划     2,000 分钟/月
  Pro 计划      3,000 分钟/月
  Team 计划    3,000 分钟/月
  Enterprise   50,000 分钟/月
  ──────────────────────────────────

  Runner 计费倍率：
  Linux         1x（最便宜）
  Windows       2x
  macOS         10x（最贵）
```

> 💡 **省钱技巧**：公开仓库完全免费、不限时长。私有仓库尽量用 Linux Runner，一个 Job 跑完所有步骤比拆成多个 Job 更省分钟数。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **CI/CD** | 提交代码后自动测试+构建+部署 |
| **Workflow** | `.github/workflows/xxx.yml` 定义流水线 |
| **Job/Step** | Job = 一台机器，Step = 一个操作 |
| **Runner** | GitHub 提供免费 Linux/Windows/macOS 虚拟机 |

---

## 2. 第一个 Workflow：Hello World 到实用模板

### 2.1 Workflow 文件结构与触发器

```yaml
# .github/workflows/ci.yml
name: CI Pipeline                     # Workflow 名称（显示在 Actions 页面）

on:                                    # 触发条件
  push:
    branches: [main, develop]          # push 到 main/develop 时触发
  pull_request:
    branches: [main]                   # PR 目标为 main 时触发
  schedule:
    - cron: '0 2 * * 1'               # 每周一凌晨 2 点（定时任务）
  workflow_dispatch:                   # 手动触发按钮

jobs:
  hello:
    runs-on: ubuntu-latest             # Runner 类型
    steps:
      - name: Hello World
        run: echo "Hello GitHub Actions! 🎉"
```

| 触发器 | 语法 | 场景 |
|:---|:---|:---|
| `push` | `on: push` | 推送代码时 |
| `pull_request` | `on: pull_request` | PR 创建/更新时 |
| `schedule` | `cron: '...'` | 定时任务 |
| `workflow_dispatch` | 无参数 | 手动触发 |
| `release` | `on: release` | 发布 Release 时 |

### 2.2 YAML 语法详解：on / jobs / steps

```yaml
name: Full Example

on:
  push:
    branches: [main]
    paths:                             # 只在这些路径变化时触发
      - 'src/**'
      - 'Dockerfile'
    paths-ignore:                      # 忽略这些路径
      - '*.md'
      - 'docs/**'

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10                # 超时限制
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4      # 使用官方 Action

      - name: Run command
        run: |                         # 多行命令
          echo "Step 1"
          echo "Step 2"
        env:                           # 步骤级环境变量
          MY_VAR: hello

      - name: Conditional step
        if: github.ref == 'refs/heads/main'  # 条件执行
        run: echo "Only on main branch"
```

### 2.3 矩阵构建：多版本 / 多平台并行测试

::: v-pre
```yaml
jobs:
  test:
    runs-on: $&#123;&#123; matrix.os &#125;&#125;
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.10', '3.11', '3.12']
      fail-fast: false                 # 一个失败不影响其他

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: $&#123;&#123; matrix.python-version &#125;&#125;
      - run: python -m pytest
```
:::

### 2.4 缓存依赖：pip / npm / docker 层缓存

::: v-pre
```yaml
# ── Python pip 缓存 ──
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'                       # 自动缓存 pip

# ── Node npm 缓存 ──
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'

# ── 手动缓存（通用） ──
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-$&#123;&#123; hashFiles('requirements.txt') &#125;&#125;
    restore-keys: pip-
```
:::

> 💡 **缓存的效果**：首次安装 `pip install` 需要 60 秒，缓存命中后只需 5 秒。矩阵构建 6 个组合 × 60 秒 = 6 分钟 → 缓存后 30 秒。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **触发器** | push/PR/定时/手动，控制 Workflow 何时运行 |
| **paths** | 只在特定文件变化时触发，避免无效构建 |
| **矩阵构建** | 多版本多平台并行测试，一次覆盖全部组合 |
| **缓存** | 缓存依赖安装，构建速度提升 10 倍 |

---

## 3. 自动化测试：提交即测试

### 3.1 Python 项目：pytest + 覆盖率

```yaml
name: Python Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:                          # 测试需要的服务
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt
      
      - name: Run tests with coverage
        run: pytest --cov=app --cov-report=xml --cov-report=term
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/testdb
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
```

### 3.2 前端项目：Vitest + ESLint + TypeCheck

```yaml
name: Frontend CI

on: [push, pull_request]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - run: npm ci                    # 比 npm install 更快更稳定
      - run: npm run lint              # ESLint 检查
      - run: npm run typecheck         # TypeScript 类型检查
      - run: npm run test              # Vitest 单元测试
      - run: npm run build             # 确保能构建成功
```

### 3.3 测试覆盖率报告与 PR 评论

::: v-pre
```yaml
      - name: Comment coverage on PR
        if: github.event_name == 'pull_request'
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          message: |
            ## 📊 测试覆盖率报告
            
            | 指标 | 数值 |
            |:---|:---|
            | 覆盖率 | $&#123;&#123; steps.coverage.outputs.total &#125;&#125;% |
            | 测试用例 | $&#123;&#123; steps.test.outputs.total &#125;&#125; 个 |
            | 通过 | ✅ $&#123;&#123; steps.test.outputs.passed &#125;&#125; |
            | 失败 | ❌ $&#123;&#123; steps.test.outputs.failed &#125;&#125; |
```
:::

### 3.4 分支保护：测试不过不许合并

```
设置分支保护规则：

  GitHub → Settings → Branches → Branch protection rules

  Branch name pattern: main
  
  ☑ Require a pull request before merging
  ☑ Require status checks to pass before merging
    → 选择你的 CI Job 名称（如 "test"）
  ☑ Require branches to be up to date before merging
  
  效果：PR 必须通过所有测试才能合并到 main
```

> 💡 **分支保护是 CI 真正发挥价值的关键**——没有强制检查，开发者可以直接跳过测试合并代码。配置了分支保护，测试就不是"建议"而是"强制"。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **services** | 测试中启动 PostgreSQL/Redis 等容器 |
| **覆盖率** | pytest --cov + Codecov 自动生成报告 |
| **PR 评论** | 测试结果自动评论到 PR 上 |
| **分支保护** | 测试不过 → 不允许合并 |

---

## 4. Docker 镜像构建与推送

### 4.1 构建并推送到 Docker Hub

::: v-pre
```yaml
name: Build & Push Docker Image

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: $&#123;&#123; secrets.DOCKER_USERNAME &#125;&#125;
          password: $&#123;&#123; secrets.DOCKER_TOKEN &#125;&#125;

      - name: Build and Push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            username/my-app:latest
            username/my-app:$&#123;&#123; github.sha &#125;&#125;
          cache-from: type=gha            # GitHub Actions 缓存
          cache-to: type=gha,mode=max
```
:::

### 4.2 推送到 GitHub Container Registry（GHCR）

::: v-pre
```yaml
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: $&#123;&#123; github.actor &#125;&#125;
          password: $&#123;&#123; secrets.GITHUB_TOKEN &#125;&#125;  # 自动提供，无需配置

      - name: Build and Push to GHCR
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/$&#123;&#123; github.repository &#125;&#125;:latest
```
:::

> 💡 **GHCR 的优势**：`GITHUB_TOKEN` 自动提供，不需要额外配置 Secret。镜像跟代码在同一个地方管理。

### 4.3 多平台构建：amd64 + arm64

```yaml
      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build multi-platform
        uses: docker/build-push-action@v5
        with:
          push: true
          platforms: linux/amd64,linux/arm64
          tags: username/my-app:latest
```

### 4.4 镜像 Tag 策略：commit SHA / 语义化版本 / latest

| Tag 策略 | 示例 | 适用场景 |
|:---|:---|:---|
| `latest` | `my-app:latest` | 开发/测试环境 |
| Commit SHA | `my-app:a1b2c3d` | 精确回滚 |
| 语义化版本 | `my-app:v1.2.3` | 正式发布 |
| 分支名 | `my-app:develop` | 多分支部署 |

::: v-pre
```yaml
      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: username/my-app
          tags: |
            type=sha
            type=ref,event=branch
            type=semver,pattern=&#123;&#123;version&#125;&#125;
```
:::

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **docker/build-push-action** | 官方 Action，一步完成构建+推送 |
| **GHCR** | GitHub 自带镜像仓库，GITHUB_TOKEN 自动认证 |
| **多平台** | QEMU + Buildx 同时构建 amd64/arm64 |
| **GHA 缓存** | `cache-from: type=gha` 利用 Actions 缓存加速构建 |

---

## 5. 自动部署到服务器

### 5.1 SSH 部署：拉镜像 + docker compose up

::: v-pre
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: build                       # 等构建完成
    
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: $&#123;&#123; secrets.SERVER_HOST &#125;&#125;
          username: $&#123;&#123; secrets.SERVER_USER &#125;&#125;
          key: $&#123;&#123; secrets.SSH_PRIVATE_KEY &#125;&#125;
          script: |
            cd /opt/my-app
            docker compose pull
            docker compose up -d --remove-orphans
            docker image prune -f      # 清理旧镜像
```
:::

### 5.2 部署到云平台：Vercel / Railway / Fly.io

::: v-pre
```yaml
# ── 部署到 Vercel（前端项目） ──
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: $&#123;&#123; secrets.VERCEL_TOKEN &#125;&#125;
          vercel-org-id: $&#123;&#123; secrets.VERCEL_ORG_ID &#125;&#125;
          vercel-project-id: $&#123;&#123; secrets.VERCEL_PROJECT_ID &#125;&#125;
          vercel-args: '--prod'

# ── 部署到 Fly.io ──
      - name: Deploy to Fly.io
        uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: $&#123;&#123; secrets.FLY_API_TOKEN &#125;&#125;
```
:::

### 5.3 零停机部署：蓝绿发布与滚动更新

```bash
# SSH 部署脚本中实现滚动更新
script: |
  cd /opt/my-app
  docker compose pull
  
  # 逐个重启（不是全部停掉再启动）
  docker compose up -d --no-deps --build web
  
  # 等待健康检查通过
  sleep 10
  curl -f http://localhost:8000/health || exit 1
```

### 5.4 多环境部署：staging → production 流水线

::: v-pre
```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging               # 需要在 GitHub 设置环境
    steps:
      - name: Deploy to Staging
        uses: appleboy/ssh-action@v1
        with:
          host: $&#123;&#123; secrets.STAGING_HOST &#125;&#125;
          script: cd /opt/my-app && docker compose up -d

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production            # 可配置"需要审批"
    steps:
      - name: Deploy to Production
        uses: appleboy/ssh-action@v1
        with:
          host: $&#123;&#123; secrets.PROD_HOST &#125;&#125;
          script: cd /opt/my-app && docker compose up -d
```
:::

> 💡 **environment 审批**：在 GitHub → Settings → Environments → production 中设置 "Required reviewers"，部署到生产前需要指定人员点击 Approve。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **SSH 部署** | `appleboy/ssh-action` 远程执行命令 |
| **零停机** | `--no-deps` 逐个重启 + 健康检查 |
| **多环境** | staging → production，production 需审批 |

---

## 6. Secrets、环境变量与安全

### 6.1 Secrets 管理：仓库级 vs 环境级

```
Secrets 的两种级别：

  仓库级 Secrets
  ═══════════════════════════════════════
  Settings → Secrets and variables → Actions
  所有 Workflow 都能用
  适合：DOCKER_TOKEN, SSH_KEY

  环境级 Secrets
  ═══════════════════════════════════════
  Settings → Environments → production → Secrets
  只有指定环境的 Job 能用
  适合：PROD_DATABASE_URL, PROD_API_KEY
```

### 6.2 环境变量与 .env 文件生成

::: v-pre
```yaml
      - name: Create .env file
        run: |
          cat > .env << EOF
          DATABASE_URL=$&#123;&#123; secrets.DATABASE_URL &#125;&#125;
          REDIS_URL=$&#123;&#123; secrets.REDIS_URL &#125;&#125;
          SECRET_KEY=$&#123;&#123; secrets.SECRET_KEY &#125;&#125;
          DEBUG=false
          EOF

      - name: Deploy with .env
        uses: appleboy/ssh-action@v1
        with:
          host: $&#123;&#123; secrets.SERVER_HOST &#125;&#125;
          script: |
            cd /opt/my-app
            docker compose --env-file .env up -d
```
:::

### 6.3 OIDC 无密钥认证（AWS / GCP）

```yaml
# 无需存储 AWS 密钥——用 OIDC 临时凭证
permissions:
  id-token: write
  contents: read

steps:
  - name: Configure AWS Credentials
    uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789:role/github-actions
      aws-region: ap-east-1
```

### 6.4 安全最佳实践：最小权限与审计

| 实践 | 说明 |
|:---|:---|
| 最小权限 Token | `GITHUB_TOKEN` 权限收窄到 `contents: read` |
| Pin Action 版本 | 用 `@v4` 而不是 `@main`，防止供应链攻击 |
| 环境审批 | production 环境需要人工 Approve |
| Secret 轮换 | 定期更新 Token 和密钥 |
| 审计日志 | Settings → Log 查看 Secret 使用记录 |

> 💡 **绝对不要**：在 Workflow 中 `echo $<span v-pre>&#123;&#123;  secrets.XXX  &#125;&#125;</span>`——GitHub 会自动遮掩，但在某些边角情况下可能泄露。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **仓库 vs 环境 Secrets** | 仓库级全局可用，环境级限定 Job |
| **.env 生成** | 在 CI 中动态生成 .env 文件 |
| **OIDC** | 无需存储密钥，用临时凭证认证云服务 |
| **Pin 版本** | Action 用 `@v4` 不用 `@main`，防供应链攻击 |

---

## 7. 实战：三种典型项目的完整 CI/CD

### 7.1 前端项目：React/Vue → 构建 → 部署到 Vercel/Nginx

::: v-pre
```yaml
name: Frontend CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm run lint
      - run: npm run test
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with: { name: dist, path: dist/ }
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: $&#123;&#123; secrets.VERCEL_TOKEN &#125;&#125;
          vercel-args: '--prod'
          vercel-org-id: $&#123;&#123; secrets.VERCEL_ORG_ID &#125;&#125;
          vercel-project-id: $&#123;&#123; secrets.VERCEL_PROJECT_ID &#125;&#125;
```
:::

### 7.2 Python 后端：FastAPI → Docker → 服务器

::: v-pre
```yaml
name: Backend CI/CD

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: test, POSTGRES_DB: testdb }
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11', cache: 'pip' }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest --cov=app
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/testdb

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: $&#123;&#123; github.actor &#125;&#125;
          password: $&#123;&#123; secrets.GITHUB_TOKEN &#125;&#125;

      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/$&#123;&#123; github.repository &#125;&#125;:$&#123;&#123; github.sha &#125;&#125;
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - uses: appleboy/ssh-action@v1
        with:
          host: $&#123;&#123; secrets.SERVER_HOST &#125;&#125;
          username: $&#123;&#123; secrets.SERVER_USER &#125;&#125;
          key: $&#123;&#123; secrets.SSH_PRIVATE_KEY &#125;&#125;
          script: |
            cd /opt/my-api
            docker compose pull
            docker compose up -d
```
:::

### 7.3 全栈项目：前端 + 后端 + 数据库迁移

::: v-pre
```yaml
name: Full Stack CI/CD

on:
  push:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11', cache: 'pip' }
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: cd frontend && npm ci && npm run test

  deploy:
    needs: [test-backend, test-frontend]  # 两个都通过
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: appleboy/ssh-action@v1
        with:
          host: $&#123;&#123; secrets.SERVER_HOST &#125;&#125;
          key: $&#123;&#123; secrets.SSH_PRIVATE_KEY &#125;&#125;
          script: |
            cd /opt/fullstack-app
            git pull origin main
            docker compose build
            docker compose run --rm migrate alembic upgrade head
            docker compose up -d
```
:::

> 💡 **全栈项目的部署顺序**：先跑数据库迁移（`alembic upgrade head`），再重启应用容器。千万别反过来——新代码可能依赖新的数据库字段。

**第 7 章核心知识回顾：**

| 项目类型 | 测试 | 构建 | 部署 |
|:---|:---|:---|:---|
| 前端 | lint + test + build | artifact 上传 | Vercel/Nginx |
| 后端 | pytest + 数据库服务 | Docker 镜像 | SSH 拉镜像 |
| 全栈 | 前后端并行测试 | Docker Compose | 迁移 → 重启 |

---

## 8. 进阶技巧与优化

### 8.1 可复用 Action 与 Composite Action

::: v-pre
```yaml
# .github/actions/setup-python-env/action.yml
name: 'Setup Python Environment'
description: 'Install Python and dependencies'

inputs:
  python-version:
    default: '3.11'

runs:
  using: 'composite'
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: $&#123;&#123; inputs.python-version &#125;&#125;
        cache: 'pip'
    - run: pip install -r requirements.txt
      shell: bash
```
:::

```yaml
# 在 Workflow 中使用
steps:
  - uses: ./.github/actions/setup-python-env
    with:
      python-version: '3.12'
```

### 8.2 自托管 Runner：用自己的服务器跑 CI

```bash
# 在你的服务器上安装 Runner
# GitHub → Settings → Actions → Runners → New self-hosted runner

./config.sh --url https://github.com/user/repo --token XXXXX
./run.sh      # 或 sudo ./svc.sh install && sudo ./svc.sh start
```

```yaml
# Workflow 中使用自托管 Runner
jobs:
  build:
    runs-on: self-hosted       # 替换 ubuntu-latest
```

### 8.3 Workflow 优化：并行、条件跳过、超时控制

::: v-pre
```yaml
# 跳过 CI（commit message 中包含 [skip ci]）
on:
  push:
    branches: [main]

jobs:
  test:
    if: "!contains(github.event.head_commit.message, '[skip ci]')"

# 取消同分支的旧运行（节省资源）
concurrency:
  group: $&#123;&#123; github.workflow &#125;&#125;-$&#123;&#123; github.ref &#125;&#125;
  cancel-in-progress: true
```
:::

### 8.4 通知集成：Slack / 飞书 / 钉钉

::: v-pre
```yaml
      - name: Notify on success
        if: success()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {"text": "✅ 部署成功！$&#123;&#123; github.repository &#125;&#125; @ $&#123;&#123; github.sha &#125;&#125;"}
        env:
          SLACK_WEBHOOK_URL: $&#123;&#123; secrets.SLACK_WEBHOOK &#125;&#125;

      - name: Notify on failure
        if: failure()
        run: |
          curl -X POST $&#123;&#123; secrets.FEISHU_WEBHOOK &#125;&#125; \
            -H 'Content-Type: application/json' \
            -d '{"msg_type":"text","content":{"text":"❌ 部署失败！请检查 GitHub Actions"&#125;&#125;'
```
:::

---

## 附录：GitHub Actions 速查手册

### A.1 触发器（on）速查

| 触发器 | 语法 | 说明 |
|:---|:---|:---|
| push | `on: push` | 推送代码 |
| pull_request | `on: pull_request` | PR 事件 |
| schedule | `cron: '0 2 * * *'` | 定时（UTC） |
| workflow_dispatch | `on: workflow_dispatch` | 手动按钮 |
| release | `on: release` | 发布 Release |
| workflow_call | `on: workflow_call` | 被其他 Workflow 调用 |

### A.2 常用官方/社区 Action 推荐

| Action | 用途 |
|:---|:---|
| `actions/checkout@v4` | 拉取代码 |
| `actions/setup-python@v5` | 安装 Python |
| `actions/setup-node@v4` | 安装 Node.js |
| `actions/cache@v4` | 缓存依赖 |
| `actions/upload-artifact@v4` | 上传构建产物 |
| `docker/build-push-action@v5` | 构建+推送 Docker 镜像 |
| `docker/login-action@v3` | 登录镜像仓库 |
| `appleboy/ssh-action@v1` | SSH 远程执行命令 |
| `codecov/codecov-action@v4` | 上传测试覆盖率 |

### A.3 Workflow YAML 语法速查

| 语法 | 示例 | 说明 |
|:---|:---|:---|
| `runs-on` | `ubuntu-latest` | Runner 类型 |
| `needs` | `needs: [test, lint]` | Job 依赖 |
| `if` | `if: github.ref == 'refs/heads/main'` | 条件执行 |
| `env` | `env: { KEY: value }` | 环境变量 |
| `timeout-minutes` | `timeout-minutes: 10` | 超时限制 |
| `continue-on-error` | `continue-on-error: true` | 失败不阻断 |
| `concurrency` | `group: xxx` | 并发控制 |

### A.4 常见报错与解决方案

| 报错 | 原因 | 解决 |
|:---|:---|:---|
| `permission denied` | GITHUB_TOKEN 权限不足 | 添加 `permissions` 块 |
| `secret not found` | Secret 名称拼错或未配置 | 检查 Settings → Secrets |
| `timeout` | Job 运行太久 | 加 `timeout-minutes` |
| `cache miss` | 缓存 key 不匹配 | 检查 `hashFiles()` 路径 |
| `image not found` | 推送未成功 | 检查 login + tag |

