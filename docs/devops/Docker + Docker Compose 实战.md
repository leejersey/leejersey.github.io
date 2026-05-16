# Docker + Docker Compose 实战

> 从零开始掌握容器化——用 Docker 构建可复现的开发环境，用 Docker Compose 编排多容器应用，覆盖镜像构建、网络配置、数据持久化、生产部署与 CI/CD 集成的完整工程实践。

---

## 1. Docker 核心概念：从"在我机器上能跑"到"在哪都能跑"

"在我机器上明明是好的啊"——这句话是所有部署灾难的起点。Docker 用容器技术彻底解决了环境不一致的问题：你的代码、依赖、配置、运行时全部打包成一个镜像，在哪都能跑出一模一样的结果。

### 1.1 为什么需要 Docker：告别"环境问题"

```
没有 Docker 的部署流程：

  开发者："我本地跑得好好的"
      │  Python 3.11 + pip install 一堆包
      ▼
  运维："服务器上起不来"
      │  Python 3.8 + 缺少系统依赖
      ▼
  折腾半天："终于跑起来了"
      │  手动改了 5 个配置文件
      ▼
  下次部署："又挂了"
      │  忘了上次改了什么
      ▼
  🔥

  ═══════════════════════════════════════

有了 Docker 的部署流程：

  开发者：docker build → docker push
      │
      ▼
  服务器：docker pull → docker run
      │
      ▼
  ✅ 完事，跟本地一模一样
```

| 痛点 | 没有 Docker | 有了 Docker |
|:---|:---|:---|
| 环境不一致 | "我本地好好的" | 镜像打包一切，到哪都一样 |
| 依赖冲突 | Python 2 和 3 打架 | 每个容器独立环境 |
| 部署复杂 | 20 步手动操作 | 一条命令 `docker compose up` |
| 扩容困难 | 每台机器装一遍 | 拉镜像就能跑 |

### 1.2 核心概念三件套：镜像、容器、仓库

```
Docker 核心概念的类比：

  镜像（Image）  ≈  软件安装包 / 类（Class）
  ═══════════════════════════════════════
  只读的模板，包含代码+依赖+配置
  可以分享、存储、版本管理

  容器（Container）  ≈  运行中的程序 / 实例（Instance）
  ═══════════════════════════════════════
  从镜像启动的运行实例
  有自己的文件系统、网络、进程空间
  可以启动、停止、删除

  仓库（Registry）  ≈  应用商店 / GitHub
  ═══════════════════════════════════════
  存放镜像的地方
  Docker Hub = 官方公共仓库
  也可以搭私有仓库
```

### 1.3 Docker 架构：Client → Daemon → Registry

```
Docker 架构：

  你的终端                Docker 引擎              镜像仓库
  ════════              ════════════            ════════════
  docker build ──→  Docker Daemon  ←──→  Docker Hub
  docker run   ──→  （dockerd）           阿里云 ACR
  docker pull  ──→                        私有 Registry
       │                  │
       │              管理容器/镜像/网络/卷
       ▼                  │
  看到命令输出         ┌───┴───┐
                      容器1  容器2  ...
```

### 1.4 安装与验证：Hello World

```bash
# ── Mac ──
brew install --cask docker
# 或者下载 Docker Desktop：https://docker.com

# ── Ubuntu ──
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER  # 免 sudo

# ── 验证安装 ──
docker version          # 查看版本
docker info             # 查看系统信息
docker run hello-world  # 运行第一个容器 🎉
```

```bash
# 第一个有用的容器：运行一次性 Python
docker run -it python:3.11 python -c "print('Hello Docker!')"
# → Hello Docker!

# 运行一个 Nginx 服务器
docker run -d -p 8080:80 nginx
# → 浏览器打开 http://localhost:8080 看到 Nginx 欢迎页
```

> 💡 **Docker Desktop vs Docker Engine**：Mac/Windows 用 Docker Desktop（图形界面+虚拟机）。Linux 服务器直接装 Docker Engine（更轻量）。功能完全一样。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Docker** | 把代码+依赖+配置打包成镜像，在哪都能跑 |
| **镜像** | 只读模板，类比 Class |
| **容器** | 镜像的运行实例，类比 Instance |
| **仓库** | 存放镜像的地方，类比 GitHub |

---

## 2. 镜像构建：Dockerfile 从入门到生产级

Dockerfile 就是镜像的"配方"——一行行指令，告诉 Docker 怎么把你的代码打包成镜像。写好 Dockerfile 是 Docker 功力的核心。

### 2.1 Dockerfile 指令详解与最佳实践

```dockerfile
# ── 一个生产级 Python 项目的 Dockerfile ──

# 基础镜像：选 slim 版（比完整版小 80%）
FROM python:3.11-slim

# 元数据（可选但推荐）
LABEL maintainer="you@example.com"
LABEL version="1.0"

# 设置工作目录
WORKDIR /app

# 先复制依赖文件（利用缓存，详见 2.2）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再复制源代码
COPY . .

# 暴露端口（文档作用，不实际映射）
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| 指令 | 作用 | 常见坑 |
|:---|:---|:---|
| `FROM` | 基础镜像 | 用 `slim` 或 `alpine`，别用 `latest` |
| `WORKDIR` | 设置工作目录 | 别用 `RUN cd`，不生效 |
| `COPY` | 复制文件到镜像 | 先复制依赖文件，再复制代码 |
| `RUN` | 执行命令 | 多条合并用 `&&`，减少层数 |
| `ENV` | 设置环境变量 | 会被 `docker run -e` 覆盖 |
| `EXPOSE` | 声明端口 | 仅文档，需要 `-p` 才真正映射 |
| `CMD` | 默认启动命令 | 可被 `docker run` 后面的命令覆盖 |
| `ENTRYPOINT` | 固定入口 | 不可被覆盖，`CMD` 作为参数 |

### 2.2 分层缓存：理解构建为什么快、为什么慢

```
Docker 构建的分层缓存机制：

  Dockerfile 的每条指令 = 一层（Layer）

  FROM python:3.11-slim    ← 第 1 层（从 Hub 拉取，缓存）
  COPY requirements.txt .  ← 第 2 层（文件没变 → 用缓存）
  RUN pip install ...      ← 第 3 层（上一层没变 → 用缓存 ✅）
  COPY . .                 ← 第 4 层（代码改了 → 重新构建 ❌）
  CMD [...]                ← 第 5 层（重新构建）

  关键规则：某一层变了，它和后面所有层都要重建！

  ═══════════════════════════════════════

  所以要把「不常变的」放前面，「常变的」放后面：
  ✅ 先 COPY requirements.txt → 再 COPY . .
  ❌ 直接 COPY . . → 每次改代码都要重装依赖
```

### 2.3 多阶段构建：从 1.2GB 到 80MB

```dockerfile
# ── 多阶段构建示例（Go 项目） ──

# 阶段 1：构建
FROM golang:1.21 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o server .

# 阶段 2：运行（只包含编译后的二进制）
FROM alpine:3.18
COPY --from=builder /app/server /server
EXPOSE 8080
CMD ["/server"]

# 结果：golang 镜像 1.2GB → 最终镜像 < 20MB
```

```dockerfile
# ── 多阶段构建（Python 项目） ──

# 阶段 1：安装依赖
FROM python:3.11-slim AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 阶段 2：运行
FROM python:3.11-slim
WORKDIR /app
COPY --from=deps /install /usr/local
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]

# Python 用多阶段构建主要是去掉编译工具，省约 200MB
```

### 2.4 .dockerignore 与镜像安全扫描

```bash
# .dockerignore（类似 .gitignore）
.git
.venv
__pycache__
*.pyc
node_modules
.env
*.md
tests/
.docker/
```

```bash
# 镜像安全扫描
docker scout cves my-app:latest       # Docker Scout（官方）
trivy image my-app:latest             # Trivy（开源，推荐）
```

> 💡 **黄金法则**：生产镜像用 `slim` 或 `alpine` 基础镜像、非 root 用户运行、不包含 `.env` 和 secrets、定期扫描漏洞。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Dockerfile** | 镜像的"配方"，一行指令一层 |
| **分层缓存** | 不常变的放前面，常变的放后面 |
| **多阶段构建** | 构建环境和运行环境分离，镜像缩小 10 倍 |
| **.dockerignore** | 排除不需要的文件，加速构建+减小体积 |

---

## 3. 容器操作：日常开发的必备技能

镜像构建好了，接下来是每天都要用的容器操作——启动、停止、调试、挂数据卷。

### 3.1 容器生命周期：run / stop / rm / restart

```bash
# ── 创建并启动容器 ──
docker run -d --name my-app -p 8000:8000 my-app:latest
# -d = 后台运行    --name = 起名字    -p = 端口映射

# ── 查看运行中的容器 ──
docker ps                  # 运行中的
docker ps -a               # 所有（含已停止的）

# ── 停止 / 启动 / 重启 ──
docker stop my-app         # 优雅停止（发 SIGTERM）
docker start my-app        # 重新启动
docker restart my-app      # 先停后启

# ── 删除容器 ──
docker rm my-app           # 删除已停止的容器
docker rm -f my-app        # 强制删除（即使运行中）

# ── 清理所有已停止的容器 ──
docker container prune     # 一键清理
```

### 3.2 端口映射与环境变量注入

```bash
# 端口映射：-p 宿主机端口:容器端口
docker run -d -p 3000:80 nginx        # localhost:3000 → 容器:80
docker run -d -p 127.0.0.1:3000:80 nginx  # 只监听本地

# 环境变量注入
docker run -d \
  -e DATABASE_URL="postgresql://user:pass@db:5432/mydb" \
  -e REDIS_URL="redis://cache:6379" \
  -e DEBUG=false \
  my-app:latest

# 从文件批量注入
docker run --env-file .env my-app:latest
```

### 3.3 数据持久化：Volume 与 Bind Mount

```bash
# ── 方式 1：Volume（Docker 管理，推荐） ──
docker volume create pgdata
docker run -d \
  --name postgres \
  -v pgdata:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret \
  postgres:16

# 容器删了，数据还在！
docker rm -f postgres
docker volume ls  # pgdata 还在

# ── 方式 2：Bind Mount（挂载宿主机目录） ──
docker run -d \
  -v $(pwd)/src:/app/src \    # 宿主机目录:容器目录
  -v $(pwd)/data:/app/data \
  my-app:latest

# 适合开发环境：修改本地文件 → 容器内实时生效
```

| 类型 | 管理方 | 适用场景 | 持久化 |
|:---|:---|:---|:---|
| Volume | Docker | 数据库、上传文件 | ✅ 容器删了数据还在 |
| Bind Mount | 你自己 | 开发环境代码热重载 | ✅ 就是你的本地文件 |
| tmpfs | 内存 | 临时缓存 | ❌ 容器停了就没了 |

### 3.4 容器调试：exec、logs、inspect 三板斧

```bash
# ── 1. exec：进入容器内部 ──
docker exec -it my-app bash     # 进入容器的 shell
docker exec -it my-app sh       # Alpine 没有 bash，用 sh
docker exec my-app cat /app/config.py  # 不进入，直接执行命令

# ── 2. logs：查看日志 ──
docker logs my-app              # 所有日志
docker logs -f my-app           # 实时跟踪（类似 tail -f）
docker logs --tail 50 my-app    # 最后 50 行
docker logs --since 1h my-app   # 最近 1 小时

# ── 3. inspect：查看容器详情 ──
docker inspect my-app           # 完整 JSON 信息
docker inspect --format '{{.NetworkSettings.IPAddress}}' my-app  # 只看 IP
docker stats                    # 实时资源使用（CPU/内存/网络）
```

> 💡 **容器排错流程**：先 `docker logs` 看错误 → 再 `docker exec` 进去检查文件/配置 → 最后 `docker inspect` 看网络/挂载是否正确。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **生命周期** | run → stop → start → rm，`-d` 后台运行 |
| **端口映射** | `-p 宿主机:容器`，`--env-file` 批量注入变量 |
| **Volume** | Docker 管理的持久化，删容器不丢数据 |
| **调试三板斧** | logs（看日志）→ exec（进容器）→ inspect（看详情） |

---

## 4. Docker 网络：让容器互相通信

多个容器之间需要互相访问——Web 应用要连数据库，API 要连 Redis。Docker 网络就是解决容器间通信的。

### 4.1 网络模式：bridge、host、none 的区别

| 模式 | 隔离性 | 性能 | 适用场景 |
|:---|:---|:---|:---|
| **bridge**（默认） | ✅ 网络隔离 | 好 | 大部分场景 |
| **host** | ❌ 共享宿主机网络 | 最好 | 高性能需求 |
| **none** | 完全隔离 | — | 安全隔离、批处理 |

```bash
# 默认 bridge
docker run -d --name web nginx

# host 模式（容器直接用宿主机端口）
docker run -d --network host nginx
# → 直接访问 localhost:80，不需要 -p

# none 模式（完全无网络）
docker run -d --network none alpine sleep infinity
```

### 4.2 自定义网络与容器互联

```bash
# ── 创建自定义网络 ──
docker network create my-network

# ── 容器加入同一网络 ──
docker run -d --name db --network my-network postgres:16
docker run -d --name web --network my-network my-app:latest

# web 容器中可以直接用容器名访问 db：
# postgresql://user:pass@db:5432/mydb
#                        ^^
#                   容器名就是主机名！
```

### 4.3 DNS 服务发现：用容器名替代 IP

```
自定义网络的 DNS 解析：

  docker network create app-net
  
  ┌─────────────┐    ┌─────────────┐
  │   web        │    │   db         │
  │   容器       │───→│   容器       │
  │              │    │              │
  │ db:5432      │    │ 172.19.0.3   │
  │ redis:6379   │    └─────────────┘
  │              │    ┌─────────────┐
  │              │───→│   redis      │
  └─────────────┘    │   容器       │
                     │ 172.19.0.4   │
                     └─────────────┘
  
  用容器名（db/redis）而不是 IP 地址！
  IP 会变，容器名不变。
```

### 4.4 常见网络问题排查

```bash
# 查看网络列表
docker network ls

# 查看某个网络的详情（哪些容器在里面）
docker network inspect my-network

# 容器内测试网络连通性
docker exec web ping db
docker exec web curl http://api:8000/health

# 常见问题：
# ❌ 容器间 ping 不通 → 不在同一个 network
# ❌ 连接 refused   → 服务没有监听 0.0.0.0
# ❌ DNS 解析失败   → 用了默认 bridge（不支持 DNS）
```

> 💡 **关键原则**：不要用默认的 bridge 网络——它不支持 DNS 服务发现。始终创建自定义网络。在 Docker Compose 中，这是自动帮你做的。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **bridge** | 默认模式，隔离好，大部分场景用这个 |
| **自定义网络** | 必须用自定义网络才有 DNS 服务发现 |
| **容器名即主机名** | 同一网络内，用容器名替代 IP 地址 |
| **排查** | `docker network inspect` + `exec ping/curl` |

---

## 5. Docker Compose：多容器编排利器

手动 `docker run` 一个个启动容器？3 个还行，10 个就崩溃了。Docker Compose 让你用一个 YAML 文件描述所有容器，一条命令全部拉起。

### 5.1 从手动 docker run 到 docker compose up

```bash
# ── 手动启动 3 个容器（痛苦版） ──
docker network create myapp
docker run -d --name db --network myapp -e POSTGRES_PASSWORD=secret postgres:16
docker run -d --name redis --network myapp redis:7-alpine
docker run -d --name web --network myapp -p 8000:8000 \
  -e DATABASE_URL="postgresql://postgres:secret@db:5432/postgres" \
  -e REDIS_URL="redis://redis:6379" my-app:latest

# ── Docker Compose（幸福版） ──
docker compose up -d       # 一条命令，全部启动 🎉
docker compose down        # 一条命令，全部停止+清理
```

### 5.2 docker-compose.yml 语法完全指南

```yaml
# docker-compose.yml
services:
  # ── Web 应用 ──
  web:
    build: .                          # 从当前目录的 Dockerfile 构建
    ports:
      - "8000:8000"                   # 端口映射
    environment:
      - DATABASE_URL=postgresql://postgres:secret@db:5432/postgres
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./src:/app/src                # 开发环境挂载代码
    restart: unless-stopped           # 自动重启

  # ── 数据库 ──
  db:
    image: postgres:16                # 直接用官方镜像
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: myapp
    volumes:
      - pgdata:/var/lib/postgresql/data  # 数据持久化
    ports:
      - "5432:5432"

  # ── 缓存 ──
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

# ── 命名卷声明 ──
volumes:
  pgdata:
```

| 关键字 | 作用 | 示例 |
|:---|:---|:---|
| `build` | 从 Dockerfile 构建 | `build: .` 或 `build: ./api` |
| `image` | 使用现成镜像 | `image: postgres:16` |
| `ports` | 端口映射 | `"8000:8000"` |
| `environment` | 环境变量 | 列表或字典格式 |
| `volumes` | 挂载卷 | `pgdata:/data` 或 `./code:/app` |
| `depends_on` | 启动依赖 | 先启动 db 再启动 web |
| `restart` | 重启策略 | `always` / `unless-stopped` / `no` |
| `networks` | 自定义网络 | 默认自动创建 |

### 5.3 环境变量管理：.env 文件与多环境配置

```bash
# .env（docker compose 自动读取）
POSTGRES_PASSWORD=my_secret_password
POSTGRES_DB=myapp
APP_PORT=8000
```

```yaml
# docker-compose.yml 中引用
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
  web:
    ports:
      - "${APP_PORT}:8000"
```

```yaml
# ── 多环境配置（override 模式） ──

# docker-compose.yml        ← 基础配置（共享）
# docker-compose.override.yml  ← 开发环境（自动加载）
# docker-compose.prod.yml   ← 生产环境（手动指定）

# 开发环境（默认加载 override）
docker compose up -d

# 生产环境
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 5.4 服务依赖与启动顺序控制

```yaml
services:
  web:
    depends_on:
      db:
        condition: service_healthy  # 等 db 健康检查通过
      redis:
        condition: service_started  # 等 redis 启动就行

  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5
```

> 💡 **`depends_on` 只管启动顺序，不管服务是否"就绪"**。数据库容器启动了不代表能接受连接——必须配合 `healthcheck` + `condition: service_healthy` 才能确保真正就绪。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Compose** | 一个 YAML 描述所有容器，一条命令全部拉起 |
| **services** | 每个服务 = 一个容器（可 build 也可用 image） |
| **.env** | 环境变量集中管理，Compose 自动读取 |
| **healthcheck** | 健康检查 + `condition: service_healthy` = 真正就绪 |

---

## 6. 实战：用 Compose 编排完整的 Web 应用

把第 5 章的理论用起来——搭建一个 FastAPI + PostgreSQL + Redis + Nginx 的真实项目。

### 6.1 项目架构：FastAPI + PostgreSQL + Redis + Nginx

```
请求链路：

  用户 → :80 → Nginx → :8000 → FastAPI → PostgreSQL
                                       → Redis

  ┌──────────┐    ┌──────────┐    ┌──────────┐
  │  Nginx   │───→│ FastAPI  │───→│ Postgres │
  │  :80     │    │ :8000    │    │ :5432    │
  └──────────┘    │          │    └──────────┘
                  │          │    ┌──────────┐
                  │          │───→│  Redis   │
                  └──────────┘    │ :6379    │
                                  └──────────┘
```

### 6.2 开发环境：热重载 + 本地调试

```yaml
# docker-compose.yml（开发环境）
services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app                # 代码热重载
    environment:
      - DATABASE_URL=postgresql://postgres:dev123@db:5432/myapp
      - REDIS_URL=redis://redis:6379
      - DEBUG=true
    command: uvicorn app.main:app --host 0.0.0.0 --reload
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: dev123
      POSTGRES_DB: myapp
    ports:
      - "5432:5432"                   # 暴露给本地工具（DBeaver）
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

### 6.3 生产环境：多阶段构建 + Nginx 反代

```yaml
# docker-compose.prod.yml（生产环境 override）
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod     # 多阶段构建
    ports: []                          # 不暴露，走 Nginx
    volumes: []                        # 不挂载代码
    environment:
      - DEBUG=false
    command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - web
```

```nginx
# nginx/nginx.conf
upstream api {
    server web:8000;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 6.4 数据库迁移与数据初始化

```yaml
# 在 docker-compose.yml 中加一个一次性迁移服务
services:
  migrate:
    build: .
    command: alembic upgrade head
    environment:
      - DATABASE_URL=postgresql://postgres:dev123@db:5432/myapp
    depends_on:
      db:
        condition: service_healthy
    profiles:
      - migrate           # 只在需要时运行
```

```bash
# 运行迁移
docker compose --profile migrate run --rm migrate

# 常用 Compose 命令
docker compose up -d           # 启动所有服务
docker compose down            # 停止并删除
docker compose logs -f web     # 看 web 服务日志
docker compose exec web bash   # 进入 web 容器
docker compose build --no-cache # 重新构建镜像
docker compose ps              # 查看服务状态
```

> 💡 **开发 vs 生产的关键差异**：开发环境挂载代码+暴露所有端口+开 DEBUG；生产环境多阶段构建+Nginx 反代+关 DEBUG+不暴露内部端口。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **四容器编排** | Nginx + FastAPI + PostgreSQL + Redis |
| **开发环境** | 代码挂载 + `--reload` + 端口全开 |
| **生产环境** | 多阶段构建 + Gunicorn + Nginx 反代 |
| **数据库迁移** | `profiles` 实现按需运行 |

---

## 7. 生产部署：从本地到服务器

镜像在本地跑得很好，怎么部署到服务器上？这一章走完从推送镜像到自动化部署的完整流程。

### 7.1 镜像仓库：Docker Hub 与私有 Registry

```bash
# ── Docker Hub（公开仓库） ──
docker login
docker tag my-app:latest username/my-app:v1.0
docker push username/my-app:v1.0

# ── 阿里云 ACR（国内推荐） ──
docker login registry.cn-hangzhou.aliyuncs.com
docker tag my-app:latest registry.cn-hangzhou.aliyuncs.com/myns/my-app:v1.0
docker push registry.cn-hangzhou.aliyuncs.com/myns/my-app:v1.0
```

| 仓库 | 适用场景 | 费用 |
|:---|:---|:---|
| Docker Hub | 开源项目 / 个人学习 | 免费（公开）|
| 阿里云 ACR | 国内生产环境 | 免费（基础版）|
| GitHub Packages | 与 GitHub 集成 | 免费（公开）|
| 私有 Registry | 完全自主控制 | 自建服务器 |

### 7.2 服务器部署：拉取镜像 + 启动服务

```bash
# ── 服务器上的操作 ──

# 1. 安装 Docker
curl -fsSL https://get.docker.com | sh

# 2. 拉取镜像
docker compose pull

# 3. 启动服务
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. 查看状态
docker compose ps
docker compose logs -f
```

### 7.3 健康检查与自动重启策略

```yaml
services:
  web:
    restart: unless-stopped    # 崩溃自动重启
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s        # 启动后等 40s 再开始检查
```

```bash
# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' web
# → healthy / unhealthy / starting
```

### 7.4 CI/CD 集成：GitHub Actions 自动构建部署

```yaml
# .github/workflows/deploy.yml
name: Build & Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_TOKEN }}

      - name: Build and Push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: username/my-app:${{ github.sha }}

      - name: Deploy to Server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/my-app
            docker compose pull
            docker compose up -d
```

> 💡 **部署策略**：push 到 main → GitHub Actions 自动构建镜像 → 推送到仓库 → SSH 到服务器 → 拉取新镜像 → 重启服务。全程无需手动操作。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **镜像推送** | `docker tag` + `docker push` 到 Hub / ACR |
| **健康检查** | `healthcheck` + `restart: unless-stopped` = 自愈 |
| **CI/CD** | push → 构建 → 推送 → SSH 部署，全自动 |

---

## 8. 进阶技巧与疑难排查

这一章是"踩坑精华"——生产环境真正会遇到的问题和优化技巧。

### 8.1 镜像瘦身：Alpine、distroless 与 slim

| 基础镜像 | 大小 | 包管理 | 适用场景 |
|:---|:---|:---|:---|
| `python:3.11` | ~900MB | apt (全) | 不推荐生产 |
| `python:3.11-slim` | ~120MB | apt (精简) | **推荐** |
| `python:3.11-alpine` | ~50MB | apk | 有些包编译不过 |
| `gcr.io/distroless/python3` | ~30MB | 无 | 极致安全 |

```bash
# 查看镜像大小
docker images --format "{{.Repository}}:{{.Tag}} {{.Size}}"

# 查看镜像每层大小（找出哪层最大）
docker history my-app:latest
```

### 8.2 构建加速：BuildKit 与缓存挂载

```bash
# 启用 BuildKit（更快、更多功能）
export DOCKER_BUILDKIT=1
docker build .

# 或在 docker-compose.yml 中
# 已经是默认行为（Docker Compose v2+）
```

```dockerfile
# 缓存挂载：pip 缓存不会每次重下
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### 8.3 安全最佳实践：非 root、只读、secrets

```dockerfile
# ── 非 root 用户运行 ──
FROM python:3.11-slim
RUN useradd -m appuser
WORKDIR /app
COPY --chown=appuser:appuser . .
USER appuser
CMD ["uvicorn", "main:app"]

# 容器内进程以 appuser 身份运行
# 即使容器被攻破，也没有 root 权限
```

```yaml
# docker-compose.yml 中的安全配置
services:
  web:
    read_only: true             # 只读文件系统
    tmpfs:
      - /tmp                    # 只有 /tmp 可写
    security_opt:
      - no-new-privileges:true  # 禁止提权
```

### 8.4 疑难排查清单：20 个常见问题与解决方案

| # | 问题 | 原因 | 解决 |
|:---|:---|:---|:---|
| 1 | 端口被占用 | 宿主机端口冲突 | 改 `-p` 的左边端口 |
| 2 | 找不到镜像 | 没 build 或 tag 错 | `docker build -t name .` |
| 3 | 容器秒退 | CMD 执行完就退出了 | 用前台进程（不要 `&`） |
| 4 | 权限拒绝 | 文件属于 root | `COPY --chown` 或 `chmod` |
| 5 | 容器间连不通 | 不在同一网络 | 创建自定义网络 |
| 6 | DNS 解析失败 | 用了默认 bridge | 用自定义网络 |
| 7 | pip 安装慢 | 默认源在海外 | `-i https://pypi.tuna.tsinghua.edu.cn/simple` |
| 8 | 磁盘满 | 旧镜像/容器堆积 | `docker system prune -a` |
| 9 | 构建缓存失效 | COPY 顺序不对 | 先 COPY 依赖文件 |
| 10 | Volume 数据丢失 | 用了匿名卷 | 用命名卷 |

> 💡 **万能排查命令**：`docker logs` 看日志 → `docker exec` 进容器 → `docker inspect` 看配置 → `docker system df` 看磁盘 → `docker network inspect` 看网络。

---

## 附录：Docker 命令速查手册

### A.1 Docker CLI 命令速查

```bash
# ── 镜像操作 ──
docker build -t name:tag .     # 构建镜像
docker images                  # 列出镜像
docker rmi image_name          # 删除镜像
docker pull image:tag          # 拉取镜像
docker push image:tag          # 推送镜像

# ── 容器操作 ──
docker run -d --name x image   # 创建+启动
docker ps / docker ps -a       # 查看容器
docker stop / start / restart  # 生命周期
docker rm / docker rm -f       # 删除
docker exec -it x bash         # 进入容器
docker logs -f x               # 查看日志

# ── 清理 ──
docker system prune -a         # 清理所有未使用资源
docker volume prune            # 清理未使用卷
docker image prune             # 清理悬空镜像
```

### A.2 Dockerfile 指令速查

| 指令 | 语法 | 说明 |
|:---|:---|:---|
| `FROM` | `FROM image:tag` | 基础镜像 |
| `WORKDIR` | `WORKDIR /app` | 工作目录 |
| `COPY` | `COPY src dest` | 复制文件 |
| `RUN` | `RUN command` | 执行命令（构建时） |
| `ENV` | `ENV KEY=value` | 环境变量 |
| `EXPOSE` | `EXPOSE 8000` | 声明端口 |
| `CMD` | `CMD ["cmd"]` | 默认命令（可覆盖） |
| `ENTRYPOINT` | `ENTRYPOINT ["cmd"]` | 入口命令（不可覆盖） |
| `USER` | `USER appuser` | 运行用户 |
| `HEALTHCHECK` | `HEALTHCHECK CMD curl ...` | 健康检查 |

### A.3 docker-compose.yml 关键字速查

| 关键字 | 说明 | 示例 |
|:---|:---|:---|
| `services` | 服务定义 | 每个服务一个容器 |
| `build` | 构建配置 | `build: .` |
| `image` | 使用镜像 | `image: nginx:alpine` |
| `ports` | 端口映射 | `"8000:8000"` |
| `volumes` | 数据卷 | `pgdata:/data` |
| `environment` | 环境变量 | `KEY: value` |
| `depends_on` | 依赖关系 | `condition: service_healthy` |
| `restart` | 重启策略 | `unless-stopped` |
| `healthcheck` | 健康检查 | `test: curl -f ...` |
| `profiles` | 条件启动 | `profiles: [debug]` |
| `networks` | 网络 | 默认自动创建 |
| `command` | 覆盖 CMD | `command: python app.py` |

### A.4 常用 Docker 镜像推荐

| 用途 | 镜像 | 说明 |
|:---|:---|:---|
| Python | `python:3.11-slim` | 生产推荐 |
| Node.js | `node:20-slim` | 生产推荐 |
| Nginx | `nginx:alpine` | 反向代理 |
| PostgreSQL | `postgres:16` | 关系数据库 |
| Redis | `redis:7-alpine` | 缓存/消息队列 |
| MySQL | `mysql:8` | 关系数据库 |
| MongoDB | `mongo:7` | 文档数据库 |
| Milvus | `milvusdb/milvus` | 向量数据库 |

