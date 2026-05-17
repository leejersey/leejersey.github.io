# Docker 入门教程

> 从零开始理解容器化——用最短的时间建立对 Docker 的完整认知，掌握镜像构建、容器管理、数据持久化、网络通信、Compose 编排到生产部署的全链路技能。

---

## 第一章 Docker 是什么：从"环境地狱"到"一次构建，处处运行"

"在我机器上能跑啊"——这句话是所有部署灾难的起点。你本地用 Python 3.11 开发得好好的，一到服务器变成 Python 3.8，缺了三个系统依赖，折腾两小时才跑起来。下次部署？又挂了，因为忘了上次手动改了什么配置。

Docker 就是为了彻底消灭这类问题而生的：**把代码、依赖、配置、运行时环境全部打包成一个标准化的"集装箱"（容器），在任何机器上都能跑出一模一样的结果。**

### 1.1 为什么需要 Docker："在我机器上能跑"的终极解法

先看一个真实的开发痛点：

```
没有 Docker 的世界：

  开发者本地                         服务器
  ═══════════                       ═══════════
  Python 3.11                       Python 3.8 ❌
  pip install 一堆包               缺少 libffi-dev ❌
  PostgreSQL 16                     PostgreSQL 14 ❌
  .env 里写好了配置                 配置文件忘了同步 ❌
  macOS                             Ubuntu 22.04

  结果：本地跑得好好的 → 服务器不停报错 → 折腾半天

  ═══════════════════════════════════════════════

有了 Docker 的世界：

  开发者本地                         服务器
  ═══════════                       ═══════════
  docker build → 打包成镜像          docker pull → 拉取镜像
  docker push  → 推送到仓库          docker run  → 启动容器
                                    
  环境完全一致 ✅                    跟本地一模一样 ✅

  结果：一次构建，处处运行 🎉
```

Docker 解决的不只是"能不能跑"的问题，而是软件交付的整个链条：

| 痛点 | 没有 Docker | 有了 Docker |
|:---|:---|:---|
| 环境不一致 | "我本地好好的" | 镜像打包一切，到哪都一样 |
| 依赖冲突 | Python 2 和 3 打架，项目 A 要 Redis 6、项目 B 要 Redis 7 | 每个容器独立环境，互不干扰 |
| 部署复杂 | 20 步手动操作，每次都得对着文档敲 | 一条命令 `docker compose up` |
| 新人上手慢 | 配环境配一天，还不一定配得对 | `docker compose up`，5 分钟跑起来 |
| 扩容困难 | 每台新机器装一遍所有依赖 | 拉镜像就能跑，秒级扩容 |

> 💡 **Docker 的本质**：它不是虚拟机，不是云服务，而是一种**标准化的打包与运行方式**。就像集装箱标准化了全球货运——不管运什么货，码头设备都能处理——Docker 标准化了软件交付，不管什么应用，有 Docker 的地方就能跑。

### 1.2 容器 vs 虚拟机：轻量隔离的本质区别

"Docker 是虚拟机吗？"——不是。虽然两者都能实现环境隔离，但技术路线完全不同：

```
虚拟机（VM）的隔离方式：

  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │  App A   │  │  App B   │  │  App C   │
  │  Deps    │  │  Deps    │  │  Deps    │
  │  Guest OS│  │  Guest OS│  │  Guest OS│  ← 每个 VM 都有完整操作系统
  └──────────┘  └──────────┘  └──────────┘
  ═══════════════════════════════════════════
       Hypervisor（VMware / VirtualBox）       ← 虚拟化层
  ═══════════════════════════════════════════
              Host OS（宿主机系统）
  ═══════════════════════════════════════════
                 硬件

  ─────────────────────────────────────────

容器（Container）的隔离方式：

  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │  App A   │  │  App B   │  │  App C   │
  │  Deps    │  │  Deps    │  │  Deps    │  ← 只打包应用+依赖
  └──────────┘  └──────────┘  └──────────┘
  ═══════════════════════════════════════════
        Docker Engine（容器运行时）             ← 共享宿主机内核
  ═══════════════════════════════════════════
              Host OS（宿主机系统）
  ═══════════════════════════════════════════
                 硬件
```

核心区别一目了然：

| 维度 | 虚拟机 | 容器 |
|:---|:---|:---|
| **隔离级别** | 硬件级（完整 OS） | 进程级（共享内核） |
| **启动时间** | 分钟级 | 秒级（甚至毫秒） |
| **磁盘占用** | GB 级（含完整 OS） | MB 级（只有应用+依赖） |
| **性能损耗** | 5-15%（虚拟化层开销） | ≈ 0%（近乎原生性能） |
| **密度** | 一台机器跑 10-20 个 | 一台机器跑几百个 |
| **安全隔离** | 强（完全独立内核） | 较弱（共享内核） |

> 💡 **一句话总结**：虚拟机虚拟的是**硬件**，每个 VM 都是一台"完整的电脑"；容器虚拟的是**操作系统**，每个容器只是一个被隔离的进程。容器更轻、更快、更省资源。

### 1.3 Docker 核心概念三件套：镜像、容器、仓库

理解 Docker 只需要搞清楚三个概念——镜像、容器、仓库。用一个生活化的类比：

```
Docker 核心概念类比：

  镜像（Image）  ≈  蛋糕配方 / 类（Class）
  ═══════════════════════════════════════════
  只读的模板，记录了"怎么构建这个环境"
  包含：操作系统基础层 + 应用代码 + 依赖库 + 配置
  特点：不可修改、可以版本管理、可以分享

  容器（Container）  ≈  做出来的蛋糕 / 实例（Instance）
  ═══════════════════════════════════════════
  从镜像启动的运行实例
  有自己的文件系统、网络、进程空间
  可以创建多个：同一个镜像 → 启动 N 个容器

  仓库（Registry）  ≈  菜谱网站 / GitHub
  ═══════════════════════════════════════════
  存放和分发镜像的地方
  Docker Hub = 官方公共仓库（类似 GitHub）
  也可以搭建私有仓库（阿里云 ACR、自建 Registry）
```

三者的关系用一张图说清楚：

```
镜像 → 容器 → 仓库，三者的工作流：

  ① 编写 Dockerfile（配方）
     │
     ▼
  ② docker build → 构建镜像（Image）
     │                    │
     │  docker run        │  docker push
     ▼                    ▼
  ③ 容器（Container）   ④ 仓库（Registry）
     运行中的实例            存储和分发
     可以有多个              别人可以 pull
```

用代码感受一下这三个概念：

```bash
# 从仓库拉取一个镜像
docker pull python:3.11-slim     # 仓库 → 本地镜像

# 从镜像启动一个容器
docker run -it python:3.11-slim python
# → 进入 Python 交互环境（这就是一个容器）

# 查看本地有哪些镜像
docker images
# REPOSITORY    TAG         SIZE
# python        3.11-slim   153MB

# 查看运行中的容器
docker ps
# CONTAINER ID   IMAGE              STATUS
# a1b2c3d4       python:3.11-slim   Up 2 minutes
```

> 💡 **容器是"用后即弃"的**：容器停止后，内部的修改默认不会保存。如果需要持久化数据，要用 Volume（第六章会详细讲）。这种"不可变"的设计正是 Docker 保证环境一致性的关键。

### 1.4 Docker 的整体架构：Client → Daemon → Registry

Docker 采用经典的**客户端-服务端（C/S）架构**。你在终端敲的 `docker` 命令是客户端，实际干活的是后台的 Docker Daemon：

```
Docker 架构全景：

  你敲的命令                 后台服务                  远程仓库
  ════════════             ════════════             ════════════
  docker build  ──────→                      
  docker run    ──────→  Docker Daemon      ←───→  Docker Hub
  docker pull   ──────→  （dockerd 进程）            阿里云 ACR
  docker push   ──────→                             私有 Registry
       │                      │
       │                 管理一切资源：
       ▼                 ┌────┼────┐
  看到命令输出           │    │    │
                      镜像  容器  网络/卷
```

三个关键组件的职责：

| 组件 | 作用 | 运行位置 |
|:---|:---|:---|
| **Docker Client** | 接收用户命令，发送给 Daemon | 你的终端 |
| **Docker Daemon** | 真正干活——构建镜像、启动容器、管理网络和卷 | 后台进程 |
| **Docker Registry** | 存储和分发镜像 | 云端（Docker Hub）或自建 |

Docker 能实现轻量隔离，底层依赖了 Linux 内核的三大技术：

```
Docker 底层技术（了解即可）：

  Namespace（命名空间）
  ═══════════════════════════════════════════
  让每个容器有自己的进程空间、网络、文件系统
  容器 A 看不到容器 B 的进程

  Cgroup（控制组）
  ═══════════════════════════════════════════
  限制每个容器能用多少 CPU、内存、磁盘 I/O
  防止某个容器吃光所有资源

  Union FS（联合文件系统）
  ═══════════════════════════════════════════
  镜像的分层存储机制
  多个镜像可以共享相同的底层，节省磁盘空间
```

> 💡 **在 Mac/Windows 上，Docker 其实是跑在一个轻量级 Linux 虚拟机里的**（因为容器技术依赖 Linux 内核）。Docker Desktop 和 OrbStack 帮你管理这个虚拟机，你完全感知不到。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Docker** | 标准化的打包与运行方式，一次构建处处运行 |
| **容器 vs VM** | 容器虚拟操作系统（轻、快），VM 虚拟硬件（重、安全） |
| **镜像** | 只读模板，包含代码+依赖+配置，类比 Class |
| **容器** | 镜像的运行实例，可创建多个，类比 Instance |
| **仓库** | 存放和分发镜像的地方，类比 GitHub |
| **架构** | Client → Daemon → Registry，C/S 模式 |

---

## 第二章 安装与第一个容器：Hello Docker

概念讲完了，接下来动手。这一章的目标很简单：**在你的电脑上装好 Docker，成功运行第一个容器**。不管你用 Mac、Linux 还是 Windows，5 分钟内搞定。

### 2.1 各平台安装指南（macOS / Linux / Windows）

#### macOS 安装

Mac 有两种主流选择，推荐先用 Docker Desktop（官方、稳定、图形界面）：

```bash
# ── 方式 1：Docker Desktop（推荐新手） ──
# 下载安装包：https://www.docker.com/products/docker-desktop/
# 或者用 Homebrew：
brew install --cask docker

# 安装后打开 Docker Desktop 应用
# 等右上角的鲸鱼图标不再跳动 → 安装完成

# ── 方式 2：OrbStack（推荐进阶用户，更轻量） ──
brew install --cask orbstack
# 启动后自动配置好 docker 命令，体验和 Docker Desktop 一样
```

#### Linux 安装（Ubuntu / Debian）

Linux 上直接装 Docker Engine，不需要 Desktop：

```bash
# ── 一键安装脚本（官方提供） ──
curl -fsSL https://get.docker.com | sh

# 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER

# ⚠️ 需要退出终端重新登录才生效
# 或者执行：newgrp docker

# ── 验证 ──
docker version
```

```bash
# ── 手动安装（如果一键脚本不可用） ──
# 1. 添加 Docker 官方 GPG 密钥
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc

# 2. 添加 Docker 仓库
echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 3. 安装 Docker Engine
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
```

#### Windows 安装

```bash
# ── 前提：启用 WSL 2 ──
# 1. 以管理员身份打开 PowerShell：
wsl --install
# 重启电脑

# ── 安装 Docker Desktop ──
# 下载：https://www.docker.com/products/docker-desktop/
# 安装时确保勾选 "Use WSL 2 instead of Hyper-V"
# 安装完成后，在 WSL 2 终端中就能用 docker 命令了
```

#### 验证安装（所有平台通用）

```bash
# 查看 Docker 版本
docker version
# Client:
#  Version:    27.x.x
# Server:
#  Version:    27.x.x    ← 看到 Server 版本说明 Daemon 在运行

# 查看系统信息
docker info

# 跑一个测试容器
docker run hello-world
# 看到 "Hello from Docker!" 就说明安装成功 🎉
```

> 💡 **国内镜像加速**：如果拉取镜像很慢，可以配置镜像加速器。Docker Desktop → Settings → Docker Engine，添加 `"registry-mirrors": ["https://mirror.ccs.tencentyun.com"]`。

### 2.2 Docker Desktop vs OrbStack vs Docker Engine：如何选择

三种方案定位不同，根据你的场景选：

```
三种 Docker 运行方案的定位：

  Docker Desktop（官方全家桶）
  ═══════════════════════════════════════════
  GUI + CLI + Kubernetes + Extensions
  适合：初学者、需要图形界面的开发者
  平台：macOS / Windows / Linux

  OrbStack（轻量替代品，Mac 专属）
  ═══════════════════════════════════════════
  比 Docker Desktop 快 2-5 倍、省 50% 内存
  完全兼容 docker / docker compose 命令
  适合：Mac 用户、追求性能的开发者

  Docker Engine（纯命令行）
  ═══════════════════════════════════════════
  没有 GUI，只有 CLI
  适合：Linux 服务器、生产环境、CI/CD
```

| 维度 | Docker Desktop | OrbStack | Docker Engine |
|:---|:---|:---|:---|
| **平台** | Mac / Win / Linux | Mac only | Linux only |
| **GUI** | ✅ 完整图形界面 | ✅ 轻量界面 | ❌ 纯 CLI |
| **资源占用** | 较高（2-4 GB 内存） | 很低（~0.5 GB） | 最低 |
| **启动速度** | 慢（30-60s） | 快（3-5s） | 即时 |
| **兼容性** | 官方维护 | 完全兼容 | 原生 |
| **价格** | 大公司需商业授权 | 个人免费 | 完全免费 |
| **Kubernetes** | ✅ 内置 | ✅ 内置 | ❌ 需单独装 |

> 💡 **我的建议**：Mac 开发用 **OrbStack**（快、省资源）；Windows 开发用 **Docker Desktop**（WSL 2 集成最好）；Linux 服务器用 **Docker Engine**（不需要 GUI）。新手不确定就先装 Docker Desktop，后面再换也很方便。

### 2.3 运行第一个容器：从 hello-world 到 Nginx

Docker 装好了，来跑几个容器感受一下：

```bash
# ── 第 1 个容器：hello-world（验证安装） ──
docker run hello-world
# 输出一大段文字，核心是：
# "Hello from Docker!"
# "This message shows that your installation appears to be working correctly."

# 发生了什么？
# 1. 本地没有 hello-world 镜像 → 自动从 Docker Hub 拉取
# 2. 从镜像创建一个容器
# 3. 容器执行了一个打印文字的程序
# 4. 程序结束，容器自动退出
```

```bash
# ── 第 2 个容器：运行一次性 Python ──
docker run -it python:3.11-slim python -c "print('Hello Docker!')"
# → Hello Docker!

# -it 的含义：
# -i = interactive（保持标准输入打开）
# -t = tty（分配一个伪终端）
# 合起来就是"交互模式"——你可以和容器内的程序互动

# 进入 Python 交互式环境
docker run -it python:3.11-slim python
# >>> 1 + 1
# 2
# >>> exit()   ← 退出后容器也停止了
```

```bash
# ── 第 3 个容器：运行 Nginx Web 服务器 ──
docker run -d -p 8080:80 --name my-nginx nginx
# -d = detach（后台运行，不占用终端）
# -p 8080:80 = 端口映射（宿主机 8080 → 容器 80）
# --name = 给容器起个名字

# 打开浏览器访问 http://localhost:8080
# → 看到 Nginx 欢迎页面 🎉

# 停止并删除容器
docker stop my-nginx
docker rm my-nginx
```

```
docker run 的完整执行流程：

  docker run nginx
       │
       ▼
  ① 本地有 nginx 镜像吗？
       │
  有 ──┤── 没有
       │      │
       │      ▼
       │   从 Docker Hub 拉取（docker pull）
       │      │
       ▼      ▼
  ② 从镜像创建容器
       │
       ▼
  ③ 启动容器（分配网络、文件系统）
       │
       ▼
  ④ 执行 CMD 指定的命令（nginx -g 'daemon off;'）
```

> 💡 **`-d` 和 `-it` 是最常用的两个模式**：长期运行的服务（数据库、Web 服务器）用 `-d` 后台跑；临时调试或交互用 `-it` 前台跑。

### 2.4 Docker CLI 速览：最常用的 10 个命令

先不用全记住，用到的时候来查这张表就行：

**镜像相关：**

| 命令 | 作用 | 示例 |
|:---|:---|:---|
| `docker pull` | 从仓库拉取镜像 | `docker pull python:3.11-slim` |
| `docker images` | 列出本地所有镜像 | `docker images` |
| `docker rmi` | 删除镜像 | `docker rmi python:3.11-slim` |
| `docker build` | 从 Dockerfile 构建镜像 | `docker build -t my-app .` |

**容器相关：**

| 命令 | 作用 | 示例 |
|:---|:---|:---|
| `docker run` | 创建并启动容器 | `docker run -d -p 8080:80 nginx` |
| `docker ps` | 列出运行中的容器 | `docker ps` / `docker ps -a`（含已停止） |
| `docker stop` | 停止容器 | `docker stop my-nginx` |
| `docker rm` | 删除容器 | `docker rm my-nginx` |
| `docker logs` | 查看容器日志 | `docker logs -f my-nginx` |
| `docker exec` | 在运行中的容器内执行命令 | `docker exec -it my-nginx bash` |

**系统清理：**

```bash
# 一键清理所有"悬空"资源（已停止的容器、无用镜像、未使用的网络）
docker system prune

# 带确认地清理一切（包括未使用的 Volume）
docker system prune -a --volumes

# 查看 Docker 占用了多少磁盘空间
docker system df
# TYPE          TOTAL   ACTIVE   SIZE      RECLAIMABLE
# Images        15      3        4.2GB     3.1GB (73%)
# Containers    8       2        120MB     80MB (66%)
# Volumes       5       2        800MB     500MB (62%)
```

> 💡 **养成好习惯**：定期跑 `docker system prune` 清理废弃资源。Docker 镜像和容器积累起来会占用大量磁盘空间。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **安装** | Mac 用 Docker Desktop 或 OrbStack，Linux 用 Docker Engine |
| **docker run** | 拉取镜像 + 创建容器 + 启动，一条命令搞定 |
| **-d** | 后台运行（服务类容器） |
| **-it** | 交互模式（调试、临时命令） |
| **-p** | 端口映射：`宿主机端口:容器端口` |
| **docker ps** | 查看运行中的容器，`-a` 看全部 |

---

## 第三章 镜像详解：理解 Docker 的"安装包"

上一章我们直接 `docker run` 就跑起了容器——但那个镜像是从哪来的？里面有什么？为什么有的镜像 5MB、有的 1.2GB？这一章搞清楚镜像的内部机制，你才能在后面写出高效的 Dockerfile。

### 3.1 镜像的分层存储机制（Union FS）

Docker 镜像**不是一个大文件**，而是由多个**只读层（Layer）**叠加而成的。就像千层蛋糕，每一层做一件事：

```
镜像的分层结构（以 Python 应用为例）：

  ┌─────────────────────────────────┐
  │  Layer 5: COPY . .              │  ← 你的代码（几 KB）
  ├─────────────────────────────────┤
  │  Layer 4: RUN pip install ...   │  ← Python 依赖（几十 MB）
  ├─────────────────────────────────┤
  │  Layer 3: COPY requirements.txt │  ← 依赖清单（几 KB）
  ├─────────────────────────────────┤
  │  Layer 2: WORKDIR /app          │  ← 创建工作目录
  ├─────────────────────────────────┤
  │  Layer 1: FROM python:3.11-slim │  ← 基础镜像（150 MB）
  └─────────────────────────────────┘

  每一层都是只读的！
  Dockerfile 的每条指令 = 新增一层
```

分层设计的好处——**层共享**：

```
层共享：多个镜像可以共用相同的底层

  镜像 A（Python Web）        镜像 B（Python Worker）
  ┌──────────────────┐       ┌──────────────────┐
  │ COPY web代码     │       │ COPY worker代码  │  ← 不同
  ├──────────────────┤       ├──────────────────┤
  │ pip install      │       │ pip install      │  ← 可能不同
  ├──────────────────┤       ├──────────────────┤
  │ python:3.11-slim │  ═══  │ python:3.11-slim │  ← 共享！
  └──────────────────┘       └──────────────────┘

  python:3.11-slim 这一层只在磁盘上存一份
  → 10 个 Python 项目共享同一个基础层，省大量磁盘空间
```

当容器启动时，Docker 会在镜像的只读层上面加一个**可写层（Container Layer）**：

```
容器运行时的层结构：

  ┌─────────────────────────────────┐
  │  Container Layer（可写）         │  ← 容器内的所有修改在这里
  │  创建文件、修改文件、删除文件      │     容器删除后，这层也没了
  ├═════════════════════════════════┤
  │  Layer N: ...                   │
  │  Layer 2: ...                   │  ← 镜像层（只读）
  │  Layer 1: FROM ...              │     不会被容器修改
  └─────────────────────────────────┘
```

> 💡 **这解释了为什么容器是"用后即弃"的**：你在容器里创建的文件、安装的软件，都写在临时的可写层里。容器一删，可写层就没了。要持久化数据，得用 Volume（第六章）。

### 3.2 Docker Hub 与镜像拉取：官方镜像 vs 社区镜像

Docker Hub（hub.docker.com）是 Docker 官方的镜像仓库，类似 GitHub 是代码仓库。大部分镜像你都从这里拉取：

```bash
# 镜像的完整命名格式
# [仓库地址/]用户名/镜像名:标签
# 
# 示例：
# python:3.11-slim         ← 官方镜像（没有用户名前缀）
# nginx:alpine             ← 官方镜像
# bitnami/postgresql:16    ← 社区/公司维护的镜像
# registry.cn-hangzhou.aliyuncs.com/myns/my-app:v1.0  ← 私有仓库

# 拉取镜像
docker pull python:3.11-slim   # 从 Docker Hub 拉取
docker pull nginx               # 不写 tag 默认用 latest
```

官方镜像和社区镜像的区别：

| 类型 | 命名格式 | 维护者 | 可信度 |
|:---|:---|:---|:---|
| **官方镜像** | `镜像名:标签`（无前缀） | Docker 官方团队 | ⭐⭐⭐ 最高 |
| **认证镜像** | `公司名/镜像名` | 经过 Docker 认证的公司 | ⭐⭐ 高 |
| **社区镜像** | `用户名/镜像名` | 个人或社区 | ⭐ 自行判断 |

常用官方基础镜像推荐：

| 镜像 | 大小 | 适用场景 |
|:---|:---|:---|
| `python:3.11-slim` | ~150 MB | Python 项目（推荐） |
| `python:3.11-alpine` | ~50 MB | 极致精简（可能缺库） |
| `node:20-slim` | ~200 MB | Node.js 项目 |
| `golang:1.22` | ~800 MB | Go 编译（配合多阶段构建） |
| `nginx:alpine` | ~40 MB | Web 服务器 / 反向代理 |
| `postgres:16` | ~400 MB | PostgreSQL 数据库 |
| `redis:7-alpine` | ~30 MB | Redis 缓存 |
| `alpine:3.19` | ~7 MB | 最小的 Linux 基础镜像 |
| `ubuntu:22.04` | ~77 MB | 完整 Ubuntu 环境 |

> 💡 **选择基础镜像的原则**：优先用 `slim` 版本（比完整版小 80%，但保留了常用工具）；如果追求极致体积用 `alpine`（但可能缺少一些 C 库，编译某些 Python 包会出问题）；避免用 `latest`（原因见 3.4）。

### 3.3 镜像管理：pull、images、rmi、prune

镜像管理的日常操作：

```bash
# ── 拉取镜像 ──
docker pull python:3.11-slim       # 拉取指定版本
docker pull nginx                   # 不指定 tag → 默认 latest
docker pull python:3.11-slim --platform linux/amd64  # 指定平台

# ── 查看本地镜像 ──
docker images
# REPOSITORY   TAG         IMAGE ID       CREATED        SIZE
# python       3.11-slim   abc123def      2 weeks ago    153MB
# nginx        latest      456789ghi      3 weeks ago    187MB
# redis        7-alpine    jkl012mno      1 month ago    30MB

# 按名称过滤
docker images python        # 只看 python 相关的镜像

# ── 查看镜像的构建历史（每一层做了什么） ──
docker history python:3.11-slim
# IMAGE          CREATED        CREATED BY                          SIZE
# abc123         2 weeks ago    CMD ["python3"]                     0B
# def456         2 weeks ago    RUN pip install ...                 45MB
# ghi789         2 weeks ago    COPY requirements.txt .             1KB
# ...
# 可以看到每一层的指令和大小 → 找出哪层最大

# ── 给镜像打标签 ──
docker tag python:3.11-slim my-python:v1
# 不会复制镜像，只是创建一个新的引用（类似 git tag）

# ── 删除镜像 ──
docker rmi python:3.11-slim          # 删除指定镜像
docker rmi abc123def                  # 用 IMAGE ID 删除
docker rmi $(docker images -q)       # 删除所有镜像（慎用）

# ── 清理无用镜像 ──
docker image prune              # 删除"悬空"镜像（无 tag 的中间层）
docker image prune -a           # 删除所有未被容器使用的镜像
```

```
镜像清理策略：

  docker image prune        → 只清理 <none>:<none> 的悬空镜像
  docker image prune -a     → 清理所有没被容器引用的镜像
  docker system prune       → 清理镜像 + 容器 + 网络（一锅端）
  docker system prune -a    → 以上全部 + 未使用的 Volume
  
  ⚠️ 生产环境慎用 prune -a，会删掉你缓存的基础镜像
```

> 💡 **磁盘空间不够了？** 先跑 `docker system df` 看看哪类资源占用最多，然后针对性清理。大部分情况下 `docker image prune` 就够了。

### 3.4 镜像 Tag 策略：为什么不要用 latest

`latest` 是 Docker 的默认标签——不指定 tag 时自动用 `latest`。但它**不代表"最新版本"**，而且是生产环境的一个大坑：

```
latest 的陷阱：

  今天拉取：docker pull python:latest → Python 3.11
  三个月后：docker pull python:latest → Python 3.12 ❌

  你的 Dockerfile 没改过一行代码
  但重新构建后，基础镜像变了 → 应用可能挂了

  ═══════════════════════════════════════════════

  正确做法：锁定版本号

  ✅ FROM python:3.11-slim     ← 明确版本
  ❌ FROM python:latest         ← 版本不可控
  ❌ FROM python                 ← 等于 python:latest
```

常见 Tag 的含义——看到一个镜像名怎么选版本：

| Tag 格式 | 含义 | 示例 |
|:---|:---|:---|
| `3.11` | 只锁定大版本 | `python:3.11`（会自动更新小版本） |
| `3.11.8` | 锁定完整版本号 | `python:3.11.8`（完全不变） |
| `3.11-slim` | 精简版（去掉开发工具） | 比完整版小 80%，推荐 |
| `3.11-alpine` | 基于 Alpine Linux 的极简版 | 最小，但可能兼容性问题 |
| `3.11-bookworm` | 基于 Debian Bookworm | 指定 Linux 发行版 |
| `latest` | 默认标签 | ⚠️ 不推荐用在生产环境 |

```bash
# 查看一个镜像有哪些可用的 tag
# 方式 1：去 Docker Hub 网页搜索
# https://hub.docker.com/_/python/tags

# 方式 2：命令行（需要安装 skopeo 或用 API）
curl -s "https://hub.docker.com/v2/repositories/library/python/tags?page_size=10" \
  | python -m json.tool | grep name
```

> 💡 **Tag 策略建议**：开发环境用 `大版本-slim`（如 `python:3.11-slim`），享受小版本更新；生产环境用 `完整版本号-slim`（如 `python:3.11.8-slim`），确保构建可复现。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **分层存储** | 镜像 = 多个只读层叠加，每条 Dockerfile 指令是一层 |
| **层共享** | 多个镜像共用相同的底层，省磁盘空间 |
| **可写层** | 容器启动时在镜像上加一层可写层，删容器就没了 |
| **Docker Hub** | 官方镜像仓库，优先用官方镜像 |
| **slim vs alpine** | slim 推荐大多数场景；alpine 最小但可能缺库 |
| **不用 latest** | 锁定版本号，确保构建可复现 |

---

## 第四章 Dockerfile 实战：从零构建自己的镜像

前面三章我们一直在用别人做好的镜像。现在轮到你了——写一个 Dockerfile，把你自己的项目打包成镜像。Dockerfile 就是镜像的"配方"，学会写 Dockerfile 是 Docker 功力的核心。

### 4.1 Dockerfile 指令详解（FROM / COPY / RUN / CMD / ENTRYPOINT）

先看一个完整的、可以直接用于生产的 Dockerfile：

```dockerfile
# ── 一个生产级 Python 项目的 Dockerfile ──

# 基础镜像：选 slim 版（比完整版小 80%）
FROM python:3.11-slim

# 元数据标签（可选但推荐）
LABEL maintainer="you@example.com"
LABEL version="1.0"
LABEL description="我的 FastAPI 应用"

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 设置工作目录（不存在会自动创建）
WORKDIR /app

# 先复制依赖文件（利用缓存，详见 4.2）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再复制源代码
COPY . .

# 暴露端口（文档作用，不实际映射）
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

每条指令的详细说明：

| 指令 | 作用 | 常见坑 |
|:---|:---|:---|
| `FROM` | 指定基础镜像，必须是第一条指令 | 用 `slim` 或 `alpine`，别用 `latest` |
| `LABEL` | 添加元数据（作者、版本等） | 纯文档作用，不影响运行 |
| `ENV` | 设置环境变量 | 会被 `docker run -e` 覆盖 |
| `WORKDIR` | 设置工作目录 | 别用 `RUN cd /app`，不会生效 |
| `COPY` | 复制文件到镜像 | 先复制依赖文件，再复制代码（利用缓存） |
| `ADD` | 类似 COPY，但能自动解压 tar | 除非需要解压，否则用 COPY |
| `RUN` | 执行命令（构建时） | 多条命令用 `&&` 合并，减少层数 |
| `EXPOSE` | 声明端口 | 仅文档，需要 `-p` 才真正映射 |
| `CMD` | 默认启动命令 | 可被 `docker run` 后面的命令覆盖 |
| `ENTRYPOINT` | 固定入口命令 | 不会被覆盖，CMD 的内容作为参数传入 |

**CMD vs ENTRYPOINT**——最容易混淆的两个指令：

```dockerfile
# ── 方式 1：只用 CMD（最常用） ──
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]

# docker run my-app                → 执行 CMD 指定的命令
# docker run my-app python shell   → CMD 被覆盖，执行 python shell

# ── 方式 2：ENTRYPOINT + CMD 组合 ──
ENTRYPOINT ["python"]
CMD ["main.py"]

# docker run my-app           → python main.py
# docker run my-app test.py   → python test.py（CMD 被替换）
# ENTRYPOINT 始终是 python，CMD 是默认参数
```

```bash
# 构建镜像
docker build -t my-app:v1 .
# -t = 给镜像命名和打标签
# .  = 构建上下文（当前目录）

# 从构建好的镜像启动容器
docker run -d -p 8000:8000 my-app:v1
```

> 💡 **exec 格式 vs shell 格式**：`CMD ["uvicorn", "..."]`（exec 格式，推荐）和 `CMD uvicorn ...`（shell 格式）的区别——exec 格式直接执行命令，接收 SIGTERM 信号能优雅关闭；shell 格式会 fork 一个 `/bin/sh -c` 子进程，信号传递可能有问题。

### 4.2 分层缓存：为什么构建顺序很重要

Docker 构建镜像时，每一层都会被缓存。**只要某一层的输入没变，Docker 就直接用缓存，不会重新执行**。这是构建速度的关键：

```
分层缓存机制：

  FROM python:3.11-slim     ← 第 1 层（从 Hub 缓存，秒过）
  COPY requirements.txt .   ← 第 2 层（文件没变 → 用缓存 ✅）
  RUN pip install ...       ← 第 3 层（上一层没变 → 用缓存 ✅）
  COPY . .                  ← 第 4 层（代码改了 → 重新构建 ❌）
  CMD [...]                 ← 第 5 层（上一层变了 → 也要重建 ❌）

  ═══════════════════════════════════════════════
  关键规则：某一层变了，它和后面所有层都要重建！
```

这就是为什么**Dockerfile 的指令顺序很重要**：

```dockerfile
# ── ❌ 错误写法：每次改代码都要重装依赖 ──
FROM python:3.11-slim
WORKDIR /app
COPY . .                           # 代码和依赖清单一起复制
RUN pip install -r requirements.txt # 代码变了 → 这层也要重建
CMD ["uvicorn", "main:app"]

# 改一行代码 → pip install 重新跑一遍 → 构建慢 3 分钟

# ── ✅ 正确写法：先装依赖，再复制代码 ──
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .            # 先复制依赖清单
RUN pip install -r requirements.txt # 依赖没变 → 用缓存，秒过
COPY . .                           # 只有代码变了 → 只重建这层
CMD ["uvicorn", "main:app"]

# 改一行代码 → 只重新 COPY 代码 → 构建快 5 秒
```

另一个优化技巧——**合并 RUN 指令**：

```dockerfile
# ── ❌ 每条 RUN = 一层（3 层） ──
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# ── ✅ 合并成一条 RUN（1 层） ──
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# 好处：层数更少、镜像更小（删除操作和安装在同一层）
```

> 💡 **调试缓存问题**：构建时看到 `CACHED` 就是用了缓存；如果想强制重建所有层，用 `docker build --no-cache -t my-app .`。

### 4.3 多阶段构建：镜像从 1GB 瘦身到 80MB

普通的 Dockerfile，镜像里包含了编译工具、开发依赖、源代码——但运行时只需要编译后的产物。多阶段构建就是**用一个阶段编译，另一个阶段只拿结果**：

```
多阶段构建的思路：

  阶段 1（构建环境）              阶段 2（运行环境）
  ═══════════════               ═══════════════
  完整的编译工具链               最小的基础镜像
  源代码                        只复制编译产物
  开发依赖                       
  
  golang:1.22 = 1.2 GB    →    alpine:3.19 = 7 MB
  
  最终镜像 = 阶段 2 = ~20 MB  🎉
```

```dockerfile
# ── 多阶段构建示例 1：Go 项目 ──

# 阶段 1：编译
FROM golang:1.22 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o server .

# 阶段 2：运行（只包含编译后的二进制文件）
FROM alpine:3.19
RUN apk --no-cache add ca-certificates  # HTTPS 证书
COPY --from=builder /app/server /server
EXPOSE 8080
CMD ["/server"]

# golang:1.22 = 1.2 GB → 最终镜像 < 20 MB
```

```dockerfile
# ── 多阶段构建示例 2：Python 项目 ──

# 阶段 1：安装依赖（包含编译工具）
FROM python:3.11-slim AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 阶段 2：运行（干净的基础镜像 + 已安装的依赖）
FROM python:3.11-slim
WORKDIR /app
COPY --from=deps /install /usr/local
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]

# 去掉编译工具和缓存，省约 200 MB
```

```dockerfile
# ── 多阶段构建示例 3：前端项目（Node.js 构建 + Nginx 托管） ──

# 阶段 1：构建前端资源
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build          # 输出到 /app/dist

# 阶段 2：用 Nginx 托管静态文件
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# node:20-slim = 400 MB → 最终镜像 < 50 MB
```

> 💡 **关键语法**：`COPY --from=builder` 表示从前一个阶段复制文件。`AS builder` 给阶段命名，方便引用。最终镜像只包含最后一个 `FROM` 阶段的内容。

### 4.4 .dockerignore 与镜像安全最佳实践

`.dockerignore` 的作用和 `.gitignore` 一样——告诉 Docker 构建时**哪些文件不要复制到镜像里**：

```bash
# .dockerignore

# 版本控制
.git
.gitignore

# Python 缓存
__pycache__
*.pyc
*.pyo
.venv
venv

# Node.js
node_modules

# IDE
.vscode
.idea

# 环境配置（绝对不能进镜像！）
.env
.env.*
*.secret

# 文档和测试
*.md
tests/
docs/

# Docker 自身配置
Dockerfile
docker-compose*.yml
.dockerignore
```

不写 `.dockerignore` 的后果：

```
没有 .dockerignore：

  COPY . .  会把以下内容全复制进镜像：
  
  .git/          → 30 MB（整个 Git 历史）
  node_modules/  → 200 MB（会在容器内重装的）
  .venv/         → 100 MB（虚拟环境）
  .env           → 包含数据库密码！❌
  
  结果：镜像巨大 + 密码泄露 + 构建缓慢
```

**Dockerfile 安全最佳实践清单**：

| 实践 | 说明 |
|:---|:---|
| ✅ 用 `.dockerignore` 排除 `.env` | 密码、密钥绝不进镜像 |
| ✅ 使用非 root 用户运行 | `RUN useradd -m app && USER app` |
| ✅ 用 `slim` 或 `alpine` 基础镜像 | 减少攻击面 |
| ✅ 定期扫描漏洞 | `docker scout cves` 或 `trivy image` |
| ✅ 锁定基础镜像版本 | 不用 `latest` |
| ❌ 不要在 Dockerfile 中写密码 | 用环境变量或 Docker Secrets |
| ❌ 不要安装不需要的包 | `--no-install-recommends` |

```bash
# 安全扫描（找出镜像中的已知漏洞）
docker scout cves my-app:v1       # Docker Scout（官方内置）
trivy image my-app:v1             # Trivy（开源工具，推荐）
```

> 💡 **黄金法则**：镜像里只包含运行必须的东西——代码、依赖、配置。其他的（开发工具、测试文件、密钥、文档）一律排除。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Dockerfile** | 镜像的"配方"，一行指令一层 |
| **CMD vs ENTRYPOINT** | CMD 可被覆盖（默认命令）；ENTRYPOINT 不可覆盖（固定入口） |
| **分层缓存** | 不常变的放前面，常变的放后面 |
| **多阶段构建** | 构建环境和运行环境分离，镜像缩小 10 倍 |
| **.dockerignore** | 排除不需要的文件，保护密钥安全 |

---

## 第五章 容器生命周期：日常开发必备操作

镜像构建好了，接下来是每天都要用的容器操作——创建、启动、停止、调试、清理。这些命令是你和 Docker 打交道最频繁的部分。

### 5.1 容器生命周期管理：run / stop / start / rm

容器有明确的生命周期状态：

```
容器的状态流转：

  docker create        docker start        docker stop
  ──────────→ Created ──────────→ Running ──────────→ Stopped
                                   │   ↑               │
                                   │   │ docker restart │
                                   │   └───────────────┘
                                   │
                          docker run（= create + start）
                                   
                          docker rm（删除已停止的容器）
                          docker rm -f（强制删除运行中的容器）
```

日常最常用的命令：

::: v-pre
```bash
# ── 创建并启动容器（最常用） ──
docker run -d --name my-app -p 8000:8000 my-app:v1
# -d        = 后台运行（detach）
# --name    = 给容器起名字（否则 Docker 随机生成）
# -p        = 端口映射（宿主机:容器）

# ── 查看容器 ──
docker ps                  # 运行中的容器
docker ps -a               # 所有容器（含已停止的）
docker ps -q               # 只输出容器 ID（方便脚本）
docker ps --format "table &#123;&#123;.Names&#125;&#125;\t&#123;&#123;.Status&#125;&#125;\t&#123;&#123;.Ports&#125;&#125;"
# → 自定义输出格式

# ── 生命周期操作 ──
docker stop my-app         # 优雅停止（发 SIGTERM，等 10 秒后 SIGKILL）
docker start my-app        # 重新启动已停止的容器
docker restart my-app      # 先 stop 再 start
docker kill my-app         # 强制停止（直接 SIGKILL）

# ── 删除容器 ──
docker rm my-app           # 删除已停止的容器
docker rm -f my-app        # 强制删除（即使运行中）

# ── 批量操作 ──
docker stop $(docker ps -q)        # 停止所有运行中的容器
docker rm $(docker ps -aq)         # 删除所有容器
docker container prune             # 清理所有已停止的容器
```
:::

> 💡 **`docker run` 每次都会创建一个新容器**。如果只是想重启之前的容器，用 `docker start my-app`，而不是再 `docker run` 一次（那样会产生第二个容器）。

### 5.2 端口映射与环境变量注入

容器默认是隔离的——外部访问不了容器内的服务。**端口映射**让外部请求能进来，**环境变量**让配置能传进去：

```bash
# ── 端口映射 ──
# 格式：-p 宿主机端口:容器端口

docker run -d -p 8080:80 nginx          # localhost:8080 → 容器:80
docker run -d -p 3000:3000 my-app       # 端口号相同时最简单
docker run -d -p 127.0.0.1:5432:5432 postgres  # 只监听本地（更安全）

# 映射多个端口
docker run -d -p 8080:80 -p 8443:443 nginx

# 随机分配宿主机端口
docker run -d -p 80 nginx               # Docker 自动分配一个端口
docker port my-nginx                     # 查看实际分配的端口
```

```
端口映射原理：

  用户请求                    Docker                    容器
  ════════                   ════════                  ════════
  localhost:8080  ──────→  端口转发规则  ──────→  容器:80
  
  宿主机的 8080 端口         iptables /              Nginx 监听
  接收外部请求               内核转发                 容器内的 80
```

```bash
# ── 环境变量注入 ──

# 方式 1：-e 逐个传入
docker run -d \
  -e DATABASE_URL="postgresql://user:pass@db:5432/mydb" \
  -e REDIS_URL="redis://cache:6379" \
  -e DEBUG=false \
  my-app:v1

# 方式 2：--env-file 从文件批量传入（推荐）
docker run -d --env-file .env my-app:v1

# .env 文件格式：
# DATABASE_URL=postgresql://user:pass@db:5432/mydb
# REDIS_URL=redis://cache:6379
# DEBUG=false

# 方式 3：在 Dockerfile 中用 ENV 设置默认值
# ENV DEBUG=false  ← docker run -e DEBUG=true 可以覆盖

# 进入容器查看环境变量
docker exec my-app env | grep DATABASE
```

> 💡 **敏感信息处理**：不要把密码写在 Dockerfile 的 `ENV` 里（会被 `docker inspect` 看到），用 `--env-file` 或 Docker Secrets 传入。`.env` 文件记得加到 `.gitignore` 和 `.dockerignore` 里。

### 5.3 容器调试三板斧：logs / exec / inspect

容器出问题了？按这个顺序排查——先看日志、再进容器、最后查配置：

```bash
# ── 1. logs：查看容器输出日志 ──
docker logs my-app              # 所有日志
docker logs -f my-app           # 实时跟踪（类似 tail -f），Ctrl+C 退出
docker logs --tail 50 my-app    # 只看最后 50 行
docker logs --since 1h my-app   # 最近 1 小时的日志
docker logs --since 2024-01-01T00:00:00 my-app  # 指定时间之后
docker logs -f --tail 0 my-app  # 从现在开始实时看新日志
```

```bash
# ── 2. exec：进入容器内部 ──
docker exec -it my-app bash     # 进入容器的 shell
docker exec -it my-app sh       # Alpine 镜像没有 bash，用 sh
docker exec my-app cat /app/config.py  # 不进入容器，直接执行命令
docker exec my-app ls -la /app         # 看容器内的文件列表
docker exec my-app pip list            # 看安装了哪些 Python 包
docker exec -it my-app python          # 在容器内启动 Python 交互

# exec 只对运行中的容器有效！已停止的容器用不了
```

::: v-pre
```bash
# ── 3. inspect：查看容器的完整配置信息 ──
docker inspect my-app                  # 输出完整的 JSON 信息（超长）

# 用 --format 提取需要的字段
docker inspect --format '&#123;&#123;.State.Status&#125;&#125;' my-app        # 容器状态
docker inspect --format '&#123;&#123;.NetworkSettings.IPAddress&#125;&#125;' my-app  # 容器 IP
docker inspect --format '&#123;&#123;json .Mounts&#125;&#125;' my-app         # 挂载的卷

# ── 4. stats：实时资源监控 ──
docker stats                    # 所有容器的 CPU/内存/网络 实时数据
docker stats my-app             # 只看一个容器
# CONTAINER   CPU %   MEM USAGE / LIMIT   NET I/O
# my-app      0.5%    128MiB / 4GiB       1.2MB / 500KB
```
:::

```
容器排错流程：

  容器挂了 / 行为异常
       │
       ▼
  ① docker logs my-app
     看到错误信息了吗？
       │
  是 ──┤── 否
       │      │
  修复代码    ▼
  重新部署  ② docker exec -it my-app bash
              能不能进去？文件/配置对不对？
                  │
             是 ──┤── 否（容器已停止）
                  │      │
             检查配置    ▼
             文件      ③ docker inspect my-app
                         看网络/挂载/环境变量
```

> 💡 **容器已经停止了怎么看日志？** `docker logs` 对已停止的容器也有效！只有 `docker exec` 需要容器处于运行状态。

### 5.4 容器资源限制：CPU 与内存控制

默认情况下，容器可以使用宿主机的所有 CPU 和内存——如果一个容器失控了，会拖垮整台机器。资源限制就是给容器加"围栏"：

```bash
# ── 内存限制 ──
docker run -d --memory=512m my-app         # 最多用 512 MB 内存
docker run -d --memory=1g my-app           # 最多用 1 GB
docker run -d --memory=512m --memory-swap=1g my-app  # 内存 512M + swap 512M

# 超出内存限制 → 容器会被 OOM Killer 杀掉

# ── CPU 限制 ──
docker run -d --cpus=1.5 my-app            # 最多用 1.5 个 CPU 核心
docker run -d --cpus=0.5 my-app            # 最多用半个核心
docker run -d --cpu-shares=512 my-app      # 相对权重（默认 1024）

# ── 组合使用 ──
docker run -d \
  --name my-app \
  --memory=512m \
  --cpus=1 \
  --restart=unless-stopped \
  -p 8000:8000 \
  my-app:v1
```

**重启策略**——容器挂了自动拉起来：

| 策略 | 行为 |
|:---|:---|
| `--restart=no` | 默认，不自动重启 |
| `--restart=always` | 无论什么原因停止，都自动重启 |
| `--restart=unless-stopped` | 自动重启，除非手动 stop（推荐） |
| `--restart=on-failure:3` | 只在异常退出时重启，最多重试 3 次 |

> 💡 **生产环境必做**：给每个容器设置 `--memory` 限制和 `--restart=unless-stopped`。前者防止内存泄漏拖垮服务器，后者保证服务自动恢复。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **run vs start** | `run` 创建新容器，`start` 重启已有容器 |
| **-p** | 端口映射：`宿主机:容器` |
| **-e / --env-file** | 环境变量注入，敏感信息用文件传入 |
| **调试三板斧** | logs（看日志）→ exec（进容器）→ inspect（查配置） |
| **资源限制** | `--memory` 限内存，`--cpus` 限 CPU |
| **重启策略** | `unless-stopped` 保证服务自动恢复 |

---

## 第六章 数据持久化：容器删了数据不丢

第三章讲过，容器的文件系统是临时的——容器一删，里面的数据就没了。但数据库的数据、用户上传的文件，肯定不能丢。这一章解决一个核心问题：**怎么让数据活得比容器久**。

### 6.1 为什么需要数据持久化：容器的临时文件系统

先用一个实验感受"数据丢失"的痛：

```bash
# 启动一个容器，在里面创建文件
docker run -it --name test ubuntu bash
root@abc123:/# echo "重要数据" > /data.txt
root@abc123:/# cat /data.txt
# 重要数据
root@abc123:/# exit

# 删除容器
docker rm test

# 再创建一个同名容器
docker run -it --name test ubuntu bash
root@def456:/# cat /data.txt
# cat: /data.txt: No such file or directory  ← 数据没了！
```

```
为什么数据会丢失：

  镜像层（只读）
  ┌──────────────────────┐
  │  ubuntu 基础镜像      │  ← 永远不变
  └──────────────────────┘
  容器层（可写，临时的）
  ┌──────────────────────┐
  │  echo "重要数据" >    │  ← 数据写在这里
  │  /data.txt            │     docker rm → 这层被删除
  └──────────────────────┘

  解决方案：把数据写到容器外面 → Volume / Bind Mount
```

### 6.2 Volume（Docker 管理卷）：数据库数据的正确存法

Volume 是 Docker 管理的存储区域，独立于容器生命周期。**容器删了，Volume 还在**：

```bash
# ── 创建和使用 Volume ──
docker volume create pgdata           # 创建一个命名卷

docker run -d \
  --name postgres \
  -v pgdata:/var/lib/postgresql/data \ # 将 Volume 挂载到容器内路径
  -e POSTGRES_PASSWORD=secret \
  postgres:16

# 容器删了，数据还在！
docker rm -f postgres
docker volume ls                       # pgdata 还在
# DRIVER    VOLUME NAME
# local     pgdata

# 用同一个 Volume 启动新容器 → 数据完整保留
docker run -d \
  --name postgres-new \
  -v pgdata:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret \
  postgres:16
# → 之前的数据库、表、数据全部还在 ✅
```

```bash
# ── Volume 管理命令 ──
docker volume ls                       # 列出所有 Volume
docker volume inspect pgdata           # 查看详情（存储路径等）
docker volume rm pgdata                # 删除 Volume（数据永久丢失！）
docker volume prune                    # 清理所有未使用的 Volume
```

```
Volume 的存储位置：

  Linux:   /var/lib/docker/volumes/pgdata/_data
  Mac:     在 Docker 虚拟机内部（通过 Docker Desktop 管理）
  Windows: 在 WSL 虚拟机内部

  你不需要关心具体路径——Docker 帮你管理
  需要备份时用 docker cp 或挂载到另一个容器
```

> 💡 **Volume 是数据库数据的标准存储方式**。PostgreSQL、MySQL、MongoDB、Redis 的数据目录都应该挂载 Volume。绝对不要把数据库数据存在容器层里。

### 6.3 Bind Mount（绑定挂载）：开发环境代码热重载

Bind Mount 是把**宿主机的一个目录直接映射到容器内**。你在本地改文件，容器里实时生效——这是开发环境的神器：

```bash
# ── 基本用法 ──
docker run -d \
  --name dev-app \
  -v $(pwd)/src:/app/src \      # 宿主机的 src 目录 → 容器的 /app/src
  -v $(pwd)/config:/app/config \
  -p 8000:8000 \
  my-app:v1

# 在宿主机上编辑 src/main.py → 容器内 /app/src/main.py 实时变更
# 配合 FastAPI 的 --reload 或 Node.js 的 nodemon → 代码热重载 🎉
```

```bash
# ── 开发环境的典型用法 ──
docker run -d \
  --name dev-server \
  -v $(pwd)/app:/app/app \          # 挂载代码目录
  -v $(pwd)/.env:/app/.env \        # 挂载配置文件
  -p 8000:8000 \
  my-app:v1 \
  uvicorn app.main:app --host 0.0.0.0 --reload
  #                                   ^^^^^^ 文件变化自动重启

# ── 只读挂载（防止容器修改宿主机文件） ──
docker run -d \
  -v $(pwd)/config:/app/config:ro \   # :ro = read-only
  my-app:v1
```

```
Volume vs Bind Mount 的核心区别：

  Volume（Docker 管理）
  ═══════════════════════════════════════════
  -v pgdata:/var/lib/postgresql/data
       ↑                    ↑
    卷名（不是路径）      容器内路径

  Bind Mount（你管理）
  ═══════════════════════════════════════════
  -v /Users/me/project/src:/app/src
       ↑                      ↑
    宿主机绝对路径          容器内路径

  怎么区分？看冒号前面：
  - 有 / 开头 → Bind Mount（宿主机路径）
  - 没有 /    → Volume（Docker 管理的卷名）
```

> 💡 **Bind Mount 只用于开发环境**。生产环境的代码应该打包在镜像里（`COPY . .`），不要用 Bind Mount 挂载——否则就失去了 Docker "环境一致性"的核心优势。

### 6.4 tmpfs 与三种方式的对比选择

除了 Volume 和 Bind Mount，还有第三种方式——**tmpfs**，数据存在内存里：

```bash
# tmpfs：数据存在内存，容器停止就没了
docker run -d \
  --tmpfs /app/cache \        # 在 /app/cache 挂载一个内存文件系统
  my-app:v1

# 适用场景：临时缓存、敏感数据（不想写入磁盘）
```

三种方式的完整对比：

| 维度 | Volume | Bind Mount | tmpfs |
|:---|:---|:---|:---|
| **管理方** | Docker | 你自己 | 内存 |
| **数据存储位置** | Docker 内部目录 | 宿主机任意目录 | 内存中 |
| **持久化** | ✅ 容器删了数据还在 | ✅ 就是你的本地文件 | ❌ 容器停了就没了 |
| **性能** | 好 | 好（Mac 上略慢） | 最快（内存级） |
| **可移植性** | ✅ 跨环境一致 | ❌ 依赖宿主机路径 | ✅ |
| **适用场景** | 数据库、上传文件 | 开发环境代码挂载 | 临时缓存、密钥 |

```
选择决策树：

  需要持久化数据吗？
       │
  是 ──┤── 否 → tmpfs（内存，用完即丢）
       │
  谁来管理数据？
       │
  Docker ──┤── 我自己
       │          │
    Volume      Bind Mount
  （数据库等）  （开发环境代码挂载）
```

**数据备份小技巧**：

```bash
# 备份 Volume 中的数据（用一个临时容器）
docker run --rm \
  -v pgdata:/source:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/pgdata-backup.tar.gz -C /source .

# 恢复数据
docker run --rm \
  -v pgdata:/target \
  -v $(pwd):/backup \
  alpine tar xzf /backup/pgdata-backup.tar.gz -C /target

# 容器和宿主机之间复制文件
docker cp my-app:/app/data.json ./data.json   # 容器 → 宿主机
docker cp ./config.yaml my-app:/app/config.yaml  # 宿主机 → 容器
```

> 💡 **一句话总结**：数据库用 Volume，开发代码用 Bind Mount，临时数据用 tmpfs。记住这个原则，95% 的场景都够用了。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **容器层是临时的** | 容器删除 → 可写层丢失 → 数据没了 |
| **Volume** | Docker 管理，独立于容器生命周期，数据库首选 |
| **Bind Mount** | 宿主机目录映射到容器，开发环境代码热重载 |
| **tmpfs** | 内存存储，最快但不持久 |
| **docker cp** | 容器和宿主机之间复制文件 |

---

## 第七章 Docker 网络：让容器互相通信

一个真实应用不可能只有一个容器——Web 应用要连数据库，API 要连 Redis。**Docker 网络**就是解决"容器之间怎么互相访问"的问题。

### 7.1 网络模式：bridge / host / none 的区别

Docker 提供三种网络模式：

```
三种网络模式：

  bridge（默认）
  ═══════════════════════════════════════════
  每个容器有自己的 IP 地址
  容器之间通过虚拟网桥通信
  需要 -p 端口映射才能被外部访问
  适用：大部分场景

  host
  ═══════════════════════════════════════════
  容器直接使用宿主机的网络
  不需要端口映射，容器端口 = 宿主机端口
  适用：高性能需求（少一层网络转发）

  none
  ═══════════════════════════════════════════
  容器完全无网络
  适用：安全隔离、批处理任务
```

| 模式 | 隔离性 | 性能 | 端口映射 | 适用场景 |
|:---|:---|:---|:---|:---|
| **bridge** | ✅ 网络隔离 | 好 | 需要 `-p` | 大部分场景（默认） |
| **host** | ❌ 共享宿主机 | 最好 | 不需要 | 高性能服务 |
| **none** | 完全隔离 | — | 无网络 | 安全隔离、纯计算 |

```bash
# bridge 模式（默认）
docker run -d -p 8080:80 nginx

# host 模式
docker run -d --network host nginx
# → 直接访问 localhost:80，不需要 -p

# none 模式
docker run -d --network none alpine sleep infinity
```

### 7.2 自定义网络与 DNS 服务发现

**默认 bridge 网络有一个大坑：不支持 DNS 服务发现**。容器之间只能用 IP 地址互相访问，但 IP 每次重启都会变。解决方案：创建自定义网络。

```bash
# ── 创建自定义网络 ──
docker network create app-net

# ── 把容器加入同一个网络 ──
docker run -d --name db --network app-net postgres:16
docker run -d --name redis --network app-net redis:7-alpine
docker run -d --name web --network app-net -p 8000:8000 my-app:v1

# 自定义网络的魔法：容器名就是主机名！
# web 容器内可以直接用容器名访问：
#   postgresql://user:pass@db:5432/mydb    ← 用 db 而不是 IP
#   redis://redis:6379                      ← 用 redis 而不是 IP
```

```
自定义网络的 DNS 解析：

  docker network create app-net

  ┌──────────────┐
  │    web        │
  │    容器       │───→ db:5432     ──→ 172.19.0.2（自动解析）
  │              │───→ redis:6379  ──→ 172.19.0.3（自动解析）
  └──────────────┘
         │
  ┌──────┴───────┐
  │              │
  ┌──────┐  ┌──────┐
  │  db  │  │redis │
  │ .0.2 │  │ .0.3 │
  └──────┘  └──────┘

  用容器名（db / redis）而不是 IP！
  IP 会变，容器名不变。
```

```bash
# ── 网络管理命令 ──
docker network ls                      # 列出所有网络
docker network inspect app-net         # 查看网络详情（哪些容器在里面）
docker network connect app-net my-app  # 把已运行的容器加入网络
docker network disconnect app-net my-app  # 从网络中移除
docker network rm app-net              # 删除网络
docker network prune                   # 清理所有未使用的网络
```

> 💡 **核心原则：永远不要用默认 bridge 网络**——它不支持 DNS 服务发现。始终创建自定义网络。在 Docker Compose 中，Compose 会自动帮你创建一个自定义网络，所以不用手动操作。

### 7.3 容器互联实战：Web 应用连接数据库

把前面学的串起来——用纯 `docker` 命令搭建一个 FastAPI + PostgreSQL + Redis 的三容器应用：

```bash
# ── Step 1：创建自定义网络 ──
docker network create myapp-net

# ── Step 2：启动数据库 ──
docker run -d \
  --name db \
  --network myapp-net \
  -v pgdata:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=myapp \
  postgres:16

# ── Step 3：启动 Redis ──
docker run -d \
  --name redis \
  --network myapp-net \
  redis:7-alpine

# ── Step 4：启动 Web 应用 ──
docker run -d \
  --name web \
  --network myapp-net \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://postgres:secret@db:5432/myapp" \
  -e REDIS_URL="redis://redis:6379" \
  my-app:v1
#                                         ^^       ^^^^^
#                                      容器名！  容器名！
#                                    不是 IP，不是 localhost
```

```
三容器通信链路：

  用户浏览器
       │
       │  localhost:8000
       ▼
  ┌──────────┐     db:5432      ┌──────────┐
  │   web    │ ──────────────→ │ postgres │
  │  :8000   │                  │  :5432   │
  │          │     redis:6379   └──────────┘
  │          │ ──────────────→ ┌──────────┐
  └──────────┘                  │  redis   │
                                │  :6379   │
                                └──────────┘

  三个容器都在 myapp-net 网络内
  web 用容器名 db / redis 访问其他服务
  只有 web 暴露了端口给外部（-p 8000:8000）
```

```bash
# 验证容器间连通性
docker exec web ping -c 2 db        # web → db 能通
docker exec web ping -c 2 redis     # web → redis 能通

# 验证数据库连接
docker exec web python -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:secret@db:5432/myapp')
print('数据库连接成功！')
conn.close()
"
```

> 💡 **手动管理 3 个容器已经很痛苦了**——要记网络名、卷名、环境变量、启动顺序。这正是下一章 Docker Compose 要解决的问题：用一个 YAML 文件描述一切，一条命令全部拉起。

### 7.4 常见网络问题排查

容器间网络不通时，按这个清单排查：

::: v-pre
```bash
# ── 排查工具箱 ──

# 1. 确认容器在同一个网络
docker network inspect app-net
# → 看 "Containers" 字段，确认目标容器在里面

# 2. 容器内测试连通性
docker exec web ping db               # 能 ping 通吗？
docker exec web curl http://api:8000/health  # 能访问服务吗？

# 3. 查看容器 IP
docker inspect --format '&#123;&#123;.NetworkSettings.Networks&#125;&#125;' web

# 4. 查看端口监听
docker exec web netstat -tlnp         # 容器内在监听哪些端口
docker exec web ss -tlnp              # 同上（netstat 不可用时）
```
:::

**常见问题与解决方案**：

| 问题 | 原因 | 解决 |
|:---|:---|:---|
| 容器间 ping 不通 | 不在同一个 network | `docker network connect` 加入同一网络 |
| DNS 解析失败 | 用了默认 bridge 网络 | 创建自定义网络 |
| Connection refused | 服务没监听 `0.0.0.0` | 改为 `--host 0.0.0.0`（不要用 127.0.0.1） |
| 端口冲突 | 宿主机端口被占用 | 换一个端口 `-p 8001:8000` |
| 从容器访问宿主机服务 | 不知道宿主机 IP | 用 `host.docker.internal`（Docker Desktop）|

```
最常见的坑：服务只监听了 127.0.0.1

  容器内的 127.0.0.1 是容器自己的回环地址
  不是宿主机的 127.0.0.1！

  ❌ uvicorn main:app --host 127.0.0.1   → 外部访问不了
  ✅ uvicorn main:app --host 0.0.0.0     → 所有网络接口都能访问
```

> 💡 **记住一条原则**：容器内的服务必须监听 `0.0.0.0`，而不是 `127.0.0.1` 或 `localhost`。这是新手最常踩的坑。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **bridge** | 默认网络模式，每个容器独立 IP |
| **自定义网络** | 支持 DNS 服务发现，容器名即主机名 |
| **容器名 = 主机名** | 同一网络内用容器名互访，不用 IP |
| **0.0.0.0** | 容器内服务必须监听 `0.0.0.0` |
| **host.docker.internal** | 容器访问宿主机服务的特殊域名 |

---

## 第八章 Docker Compose：一键编排多容器应用

上一章我们手动用 `docker run` 启动了 3 个容器——要敲一堆命令、记一堆参数。Docker Compose 让你用**一个 YAML 文件描述所有容器**，一条命令全部拉起。从这一章开始，你会发现 Compose 是日常开发的真正主力。

### 8.1 从手动 docker run 到 docker compose up

对比一下手动方式和 Compose 方式：

```bash
# ── 手动启动 3 个容器（第 7 章的做法） ──
docker network create myapp-net
docker run -d --name db --network myapp-net \
  -v pgdata:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret postgres:16
docker run -d --name redis --network myapp-net redis:7-alpine
docker run -d --name web --network myapp-net -p 8000:8000 \
  -e DATABASE_URL="postgresql://postgres:secret@db:5432/myapp" \
  my-app:v1

# 停止清理：
docker stop web redis db
docker rm web redis db
docker network rm myapp-net
# 一共 8 条命令，记不住、容易错

# ── Docker Compose（同样效果） ──
docker compose up -d       # 一条命令，全部拉起 🎉
docker compose down        # 一条命令，全部停止+清理
# 2 条命令搞定
```

### 8.2 docker-compose.yml 语法完全指南

一个完整的 `docker-compose.yml` 长这样：

```yaml
# docker-compose.yml
services:
  # ── Web 应用 ──
  web:
    build: .                          # 从当前目录的 Dockerfile 构建
    ports:
      - "8000:8000"                   # 端口映射
    environment:                      # 环境变量
      - DATABASE_URL=postgresql://postgres:secret@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:                       # 启动依赖
      - db
      - redis
    volumes:
      - ./app:/app/app                # 开发环境挂载代码
    restart: unless-stopped           # 自动重启策略

  # ── 数据库 ──
  db:
    image: postgres:16                # 直接用官方镜像
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: myapp
    volumes:
      - pgdata:/var/lib/postgresql/data  # 数据持久化
    ports:
      - "5432:5432"                   # 暴露给本地工具（DBeaver）

  # ── 缓存 ──
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

# ── 命名卷声明 ──
volumes:
  pgdata:
```

关键字速查：

| 关键字 | 作用 | 示例 |
|:---|:---|:---|
| `build` | 从 Dockerfile 构建镜像 | `build: .` 或 `build: ./api` |
| `image` | 使用现成镜像 | `image: postgres:16` |
| `ports` | 端口映射 | `"8000:8000"` |
| `environment` | 环境变量 | 列表或字典格式均可 |
| `volumes` | 挂载卷 | `pgdata:/data` 或 `./code:/app` |
| `depends_on` | 启动依赖顺序 | 先启动 db 再启动 web |
| `restart` | 重启策略 | `always` / `unless-stopped` / `no` |
| `command` | 覆盖 Dockerfile 的 CMD | `command: uvicorn ... --reload` |
| `networks` | 自定义网络 | 默认 Compose 自动创建 |

```bash
# ── Compose 常用命令 ──
docker compose up -d           # 后台启动所有服务
docker compose down            # 停止并删除容器+网络
docker compose down -v         # 同上，还删除 Volume（慎用！）
docker compose ps              # 查看服务状态
docker compose logs -f web     # 实时查看 web 服务日志
docker compose exec web bash   # 进入 web 容器
docker compose build           # 重新构建镜像
docker compose build --no-cache # 无缓存重建
docker compose restart web     # 重启某个服务
docker compose pull            # 拉取最新镜像
```

> 💡 **Compose 自动帮你做了两件事**：① 创建一个自定义网络（所有服务自动加入，支持 DNS 服务发现）；② 给容器起统一前缀的名字（`项目名_服务名_序号`）。你不需要手动 `docker network create`。

### 8.3 环境变量管理：.env 文件与多环境配置

把密码、端口这些可变配置写死在 `docker-compose.yml` 里不好——换个环境就得改。正确做法是用 `.env` 文件集中管理：

```bash
# .env（Compose 自动读取同目录下的 .env 文件）
POSTGRES_PASSWORD=my_secret_password
POSTGRES_DB=myapp
POSTGRES_USER=postgres
APP_PORT=8000
REDIS_VERSION=7-alpine
```

```yaml
# docker-compose.yml 中用 ${} 引用
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}

  web:
    build: .
    ports:
      - "${APP_PORT}:8000"
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}

  redis:
    image: redis:${REDIS_VERSION}
```

**多环境配置**——开发和生产用不同的配置：

```yaml
# ── 方式：Override 文件（推荐） ──

# docker-compose.yml          ← 基础配置（共享）
# docker-compose.override.yml ← 开发环境（自动加载！）
# docker-compose.prod.yml     ← 生产环境（手动指定）
```

```yaml
# docker-compose.override.yml（开发环境，自动覆盖基础配置）
services:
  web:
    volumes:
      - ./app:/app/app              # 挂载代码，热重载
    command: uvicorn app.main:app --host 0.0.0.0 --reload
    environment:
      - DEBUG=true
  db:
    ports:
      - "5432:5432"                 # 暴露端口给本地工具
```

```yaml
# docker-compose.prod.yml（生产环境）
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
    environment:
      - DEBUG=false
    restart: always
```

```bash
# 开发环境（自动加载 override 文件）
docker compose up -d

# 生产环境（手动指定）
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

> 💡 **`.env` 文件绝不能提交到 Git**。在 `.gitignore` 中添加 `.env`，然后提供一个 `.env.example` 作为模板，让别人知道需要哪些变量。

### 8.4 服务依赖与健康检查：确保启动顺序

`depends_on` 只保证容器的**启动顺序**，不保证服务**真正就绪**。数据库容器启动了 ≠ 数据库能接受连接。这是一个经典的坑：

```yaml
# ── ❌ 有坑的写法 ──
services:
  web:
    depends_on:
      - db           # 只保证 db 容器先启动
    # 但 db 容器启动后，PostgreSQL 可能还在初始化
    # → web 连接 db 失败 → 应用崩溃

# ── ✅ 正确的写法：healthcheck + condition ──
services:
  web:
    build: .
    depends_on:
      db:
        condition: service_healthy  # 等 db 健康检查通过才启动 web
      redis:
        condition: service_started  # redis 启动就行，不需要健康检查

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s       # 每 5 秒检查一次
      timeout: 3s        # 超时 3 秒算失败
      retries: 5          # 连续失败 5 次才算不健康
      start_period: 10s   # 启动后等 10 秒再开始检查

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
```

常用服务的 healthcheck 配置：

| 服务 | healthcheck test 命令 |
|:---|:---|
| PostgreSQL | `pg_isready -U postgres` |
| MySQL | `mysqladmin ping -h localhost` |
| Redis | `redis-cli ping` |
| Nginx | `curl -f http://localhost/ \|\| exit 1` |
| 自定义 API | `curl -f http://localhost:8000/health \|\| exit 1` |

```bash
# 查看服务的健康状态
docker compose ps
# NAME   IMAGE         STATUS
# db     postgres:16   Up 30s (healthy)    ← 健康
# redis  redis:7       Up 28s (healthy)
# web    my-app:v1     Up 5s               ← 在 db healthy 后才启动
```

> 💡 **生产环境必做**：所有数据库和关键依赖服务都配 `healthcheck`，Web 服务的 `depends_on` 用 `condition: service_healthy`。这能避免 90% 的"启动时连接失败"问题。

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Compose** | 一个 YAML 描述所有容器，一条命令全部拉起 |
| **services** | 每个服务 = 一个容器（可 build 也可用 image） |
| **.env** | 环境变量集中管理，Compose 自动读取 |
| **override** | `docker-compose.override.yml` 自动覆盖，实现多环境 |
| **healthcheck** | 健康检查 + `condition: service_healthy` = 真正就绪 |

---

## 第九章 实战项目：用 Compose 部署完整 Web 应用

把前面所有知识串起来——搭建一个 **FastAPI + PostgreSQL + Redis + Nginx** 的真实项目，覆盖开发和生产两套环境配置。

### 9.1 项目架构设计：四容器协作链路

```
请求链路：

  用户浏览器
       │
       │  :80 / :443
       ▼
  ┌──────────┐    反向代理     ┌──────────┐
  │  Nginx   │ ──────────→  │ FastAPI  │
  │  :80     │                │ :8000    │
  └──────────┘                │          │
                              │          │──→ PostgreSQL :5432
                              │          │──→ Redis :6379
                              └──────────┘
```

```
项目目录结构：

  my-project/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py              # FastAPI 入口
  │   ├── models.py            # 数据库模型
  │   └── config.py            # 配置（读环境变量）
  ├── nginx/
  │   └── nginx.conf           # Nginx 配置
  ├── Dockerfile               # 开发环境镜像
  ├── Dockerfile.prod          # 生产环境镜像（多阶段构建）
  ├── docker-compose.yml       # 基础配置
  ├── docker-compose.override.yml  # 开发环境覆盖
  ├── docker-compose.prod.yml  # 生产环境覆盖
  ├── requirements.txt
  ├── .env                     # 环境变量（不提交 Git）
  ├── .env.example             # 环境变量模板
  └── .dockerignore
```

### 9.2 开发环境搭建：热重载 + 本地调试

```yaml
# docker-compose.yml（基础配置）
services:
  web:
    build: .
    ports:
      - "${APP_PORT:-8000}:8000"
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 5s
      retries: 5

  redis:
    image: redis:7-alpine

volumes:
  pgdata:
```

```yaml
# docker-compose.override.yml（开发环境，自动加载）
services:
  web:
    volumes:
      - ./app:/app/app                # 代码热重载
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - DEBUG=true

  db:
    ports:
      - "5432:5432"                   # 暴露给 DBeaver 等本地工具

  redis:
    ports:
      - "6379:6379"                   # 暴露给本地调试
```

```bash
# .env
POSTGRES_PASSWORD=dev123
POSTGRES_DB=myapp
POSTGRES_USER=postgres
APP_PORT=8000
```

```bash
# 启动开发环境（一条命令搞定）
docker compose up -d

# 查看状态
docker compose ps
# NAME     IMAGE         STATUS
# db       postgres:16   Up 30s (healthy)
# redis    redis:7       Up 28s
# web      my-app        Up 5s

# 看 web 日志
docker compose logs -f web

# 进入 web 容器调试
docker compose exec web python
```

> 💡 **开发环境的核心**：代码通过 Bind Mount 挂载 + `--reload` 参数 → 改代码后自动重启，不需要重建镜像。数据库和 Redis 端口暴露到本地，方便用 GUI 工具查看。

### 9.3 生产环境配置：多阶段构建 + Nginx 反代

生产环境和开发环境的关键差异：不挂载代码、不暴露内部端口、用 Gunicorn 多进程、加 Nginx 反代。

```dockerfile
# Dockerfile.prod（生产环境专用，多阶段构建）

# 阶段 1：安装依赖
FROM python:3.11-slim AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 阶段 2：运行
FROM python:3.11-slim
WORKDIR /app

# 创建非 root 用户
RUN useradd -m -r appuser

# 复制依赖
COPY --from=deps /install /usr/local

# 复制代码
COPY . .

# 切换到非 root 用户
USER appuser

EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "app.main:app"]
```

```yaml
# docker-compose.prod.yml（生产环境覆盖）
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports: []                         # 不直接暴露，走 Nginx
    volumes: []                       # 不挂载代码
    environment:
      - DEBUG=false
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - web
    restart: always

  db:
    ports: []                         # 不暴露数据库端口

  redis:
    ports: []                         # 不暴露 Redis 端口
```

```nginx
# nginx/nginx.conf
upstream api {
    server web:8000;
}

server {
    listen 80;
    server_name example.com;

    # 请求体大小限制
    client_max_body_size 10M;

    location / {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件（如果有）
    location /static/ {
        alias /app/static/;
        expires 30d;
    }
}
```

```bash
# 启动生产环境
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 查看状态
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

```
开发 vs 生产的关键差异：

  维度          开发环境                    生产环境
  ════════    ════════════              ════════════
  代码        Bind Mount 挂载           COPY 进镜像
  热重载      uvicorn --reload          Gunicorn 多进程
  端口        全部暴露                   只暴露 80/443
  反代        无                        Nginx
  用户        root                      非 root（appuser）
  重启        unless-stopped            always
  DEBUG       true                      false
```

> 💡 **开发环境求方便，生产环境求安全**。代码打包进镜像、非 root 运行、不暴露内部端口、Nginx 反代——这四条是生产部署的最低标准。

### 9.4 数据库迁移与运维常用命令

数据库迁移（Alembic / Django migrate）用 `profiles` 做成按需运行的服务：

```yaml
# 在 docker-compose.yml 中添加迁移服务
services:
  migrate:
    build: .
    command: alembic upgrade head
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    depends_on:
      db:
        condition: service_healthy
    profiles:
      - migrate           # 只在需要时运行，不会被 docker compose up 启动
```

```bash
# ── 数据库迁移 ──
docker compose --profile migrate run --rm migrate
# --profile migrate  → 启用 migrate 服务
# run --rm           → 执行完自动删除容器

# ── 日常运维命令集合 ──

# 启动所有服务
docker compose up -d

# 重启单个服务（代码改了/配置改了）
docker compose restart web

# 代码变了需要重建镜像
docker compose up -d --build web

# 查看所有服务状态
docker compose ps

# 实时看日志
docker compose logs -f              # 所有服务
docker compose logs -f web          # 只看 web
docker compose logs --tail 50 web   # 最后 50 行

# 进入容器
docker compose exec web bash        # 进入 web
docker compose exec db psql -U postgres  # 进入数据库命令行

# 数据库备份
docker compose exec db pg_dump -U postgres myapp > backup.sql

# 数据库恢复
cat backup.sql | docker compose exec -T db psql -U postgres myapp

# 停止所有服务
docker compose down

# 停止并删除数据（慎用！）
docker compose down -v              # -v 同时删除 Volume
```

> 💡 **`profiles` 的妙用**：把一次性任务（迁移、种子数据、测试）放到 `profiles` 里，它们不会被 `docker compose up` 启动，只在需要时手动运行。

**第 9 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **四容器架构** | Nginx + FastAPI + PostgreSQL + Redis |
| **开发环境** | 代码挂载 + `--reload` + 端口全开 |
| **生产环境** | 多阶段构建 + Gunicorn + Nginx 反代 + 非 root |
| **override** | 开发/生产用不同的 override 文件 |
| **profiles** | 按需运行的一次性任务（迁移、备份） |

---

## 第十章 镜像优化与安全加固

前面几章侧重"能用"，这一章关注"用好"——更小的镜像体积、更少的安全漏洞、更规范的生产实践。

### 10.1 镜像瘦身清单：从 5 个维度压缩体积

```
镜像瘦身的 5 个维度：

  ① 基础镜像          python:3.11 (900MB) → python:3.11-slim (150MB)
  ② 多阶段构建        去掉编译工具，只保留运行产物
  ③ 合并 RUN 指令     减少层数，同层删除缓存
  ④ .dockerignore     排除 .git / node_modules / .venv
  ⑤ 清理缓存          pip --no-cache-dir / apt clean
```

```dockerfile
# ── 优化前：~900 MB ──
FROM python:3.11
COPY . .
RUN pip install -r requirements.txt

# ── 优化后：~180 MB ──
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

```bash
# 查看镜像各层大小，找出"胖"层
docker history my-app:v1
# IMAGE     CREATED BY                              SIZE
# abc123    RUN pip install ...                     120MB  ← 最大的层
# def456    COPY . .                                5MB
# ghi789    FROM python:3.11-slim                   150MB

# 对比优化前后
docker images | grep my-app
# my-app   v1-fat    900MB
# my-app   v1-slim   180MB   ← 省了 80%
```

### 10.2 安全扫描：Docker Scout 与 Trivy

```bash
# ── Docker Scout（官方内置，Docker Desktop 自带） ──
docker scout cves my-app:v1
# ✗ HIGH    libssl3 3.0.2-0ubuntu1.12 → 存在 CVE-2024-xxxx
# ✗ MEDIUM  zlib1g 1:1.2.11 → 存在 CVE-2023-xxxx
# ✓ 共发现 3 个高危、5 个中危漏洞

docker scout recommendations my-app:v1
# → 建议升级基础镜像到 python:3.11.8-slim

# ── Trivy（开源工具，推荐） ──
# 安装
brew install trivy                    # Mac
# 或 docker run 方式使用

# 扫描镜像
trivy image my-app:v1
# 输出类似 Scout，但更详细，支持多种输出格式

trivy image --severity HIGH,CRITICAL my-app:v1  # 只看高危
trivy image --format json my-app:v1 > report.json  # JSON 报告
```

> 💡 **建议定期扫描**：在 CI/CD 流程中加入 `trivy image` 步骤，每次构建自动扫描。高危漏洞 → 阻止部署。

### 10.3 非 root 用户运行与文件权限

默认情况下，容器内的进程以 **root** 身份运行——这是一个安全隐患。如果攻击者突破了应用，就拿到了容器的 root 权限：

```dockerfile
# ── 创建非 root 用户并切换 ──
FROM python:3.11-slim
WORKDIR /app

# 创建用户（不带登录 shell，更安全）
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /sbin/nologin appuser

# 安装依赖（还是用 root）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码并设置权限
COPY --chown=appuser:appgroup . .

# 切换到非 root 用户（后续所有操作都以 appuser 身份）
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

```bash
# 验证容器内的用户
docker exec my-app whoami
# appuser  ← 不是 root ✅

docker exec my-app id
# uid=999(appuser) gid=999(appgroup) groups=999(appgroup)
```

### 10.4 Secrets 管理：不把密码写进镜像

```
密码/密钥的错误和正确做法：

  ❌ 写在 Dockerfile 里
     ENV DATABASE_PASSWORD=my_secret    → docker inspect 能看到
     
  ❌ 写在镜像层里
     RUN echo "password" > /app/.env   → docker history 能看到
     
  ✅ 运行时通过环境变量传入
     docker run -e DATABASE_PASSWORD=xxx
     
  ✅ 运行时通过 .env 文件传入
     docker run --env-file .env
     
  ✅ Docker Compose Secrets（生产环境推荐）
```

```yaml
# Docker Compose Secrets 用法
services:
  web:
    build: .
    secrets:
      - db_password
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password

  db:
    image: postgres:16
    secrets:
      - db_password
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt    # 密码存在本地文件
```

> 💡 **安全检查清单**：① 镜像用 `slim`/`alpine` ② 定期 `trivy` 扫描 ③ 非 root 运行 ④ 密码不进镜像 ⑤ `.env` 不提交 Git ⑥ 锁定基础镜像版本。

**第 10 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **镜像瘦身** | slim 基础镜像 + 多阶段构建 + 清理缓存 |
| **安全扫描** | Docker Scout / Trivy，CI 中自动扫描 |
| **非 root** | `RUN useradd` + `USER appuser`，减少攻击面 |
| **Secrets** | 运行时传入密码，绝不写进镜像 |

---

## 第十一章 生产部署与 CI/CD 集成

镜像在本地跑得很好，怎么部署到服务器上？这一章走完从推送镜像到自动化部署的完整流程。

### 11.1 镜像仓库：Docker Hub / 阿里云 ACR / GitHub Packages

```bash
# ── Docker Hub（公开仓库，学习/开源项目） ──
docker login
docker tag my-app:v1 username/my-app:v1
docker push username/my-app:v1

# ── 阿里云 ACR（国内推荐，免费基础版） ──
docker login registry.cn-hangzhou.aliyuncs.com
docker tag my-app:v1 registry.cn-hangzhou.aliyuncs.com/myns/my-app:v1
docker push registry.cn-hangzhou.aliyuncs.com/myns/my-app:v1

# ── GitHub Packages（与代码仓库绑定） ──
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker tag my-app:v1 ghcr.io/username/my-app:v1
docker push ghcr.io/username/my-app:v1
```

| 仓库 | 适用场景 | 费用 | 国内速度 |
|:---|:---|:---|:---|
| Docker Hub | 开源/学习 | 免费（公开） | 慢 |
| 阿里云 ACR | 国内生产 | 免费（基础版） | 快 |
| GitHub Packages | 与 GitHub 集成 | 免费（公开） | 一般 |

### 11.2 服务器部署：拉取镜像 + 启动服务

```bash
# ── 服务器上的操作 ──

# 1. 安装 Docker（Ubuntu）
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. 拉取镜像
docker pull registry.cn-hangzhou.aliyuncs.com/myns/my-app:v1

# 3. 上传 docker-compose.yml 和 .env 到服务器
scp docker-compose.yml docker-compose.prod.yml .env user@server:~/myapp/

# 4. 启动服务
ssh user@server
cd ~/myapp
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 11.3 GitHub Actions 自动化：测试→构建→部署

::: v-pre
```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      # 1. 拉取代码
      - uses: actions/checkout@v4

      # 2. 登录镜像仓库
      - name: Login to Registry
        uses: docker/login-action@v3
        with:
          registry: registry.cn-hangzhou.aliyuncs.com
          username: $&#123;&#123; secrets.REGISTRY_USERNAME &#125;&#125;
          password: $&#123;&#123; secrets.REGISTRY_PASSWORD &#125;&#125;

      # 3. 构建并推送镜像
      - name: Build and Push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: Dockerfile.prod
          push: true
          tags: registry.cn-hangzhou.aliyuncs.com/myns/my-app:$&#123;&#123; github.sha &#125;&#125;

      # 4. 部署到服务器
      - name: Deploy to Server
        uses: appleboy/ssh-action@v1
        with:
          host: $&#123;&#123; secrets.SERVER_HOST &#125;&#125;
          username: $&#123;&#123; secrets.SERVER_USER &#125;&#125;
          key: $&#123;&#123; secrets.SSH_PRIVATE_KEY &#125;&#125;
          script: |
            cd ~/myapp
            docker pull registry.cn-hangzhou.aliyuncs.com/myns/my-app:$&#123;&#123; github.sha &#125;&#125;
            docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
:::

```
CI/CD 自动化流程：

  git push main
       │
       ▼
  GitHub Actions
  ┌─────────────────────────────────┐
  │ ① checkout 代码                 │
  │ ② docker build + push 镜像     │
  │ ③ SSH 到服务器                  │
  │ ④ docker pull + compose up     │
  └─────────────────────────────────┘
       │
       ▼
  服务器自动更新 🎉
```

### 11.4 日志收集与容器监控

```bash
# ── 基础日志查看 ──
docker compose logs -f                 # 实时查看所有服务日志
docker compose logs --since 1h web     # 最近 1 小时

# ── Docker 日志驱动配置 ──
# 在 daemon.json 中配置日志大小限制（防磁盘爆满）
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
# 每个容器日志最大 10MB，保留 3 个文件 → 最多 30MB

# ── 容器资源监控 ──
docker stats                           # 实时 CPU/内存/网络
```

> 💡 **进阶监控**：生产环境建议上 Prometheus + Grafana（指标监控）或 Loki（日志聚合）。但对于小项目，`docker logs` + `docker stats` + 日志大小限制已经够用了。

**第 11 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **镜像仓库** | Docker Hub / 阿里云 ACR，`push` 推送 `pull` 拉取 |
| **服务器部署** | 上传 compose 文件 + 拉取镜像 + `compose up` |
| **CI/CD** | GitHub Actions 自动构建+推送+部署 |
| **日志限制** | `max-size` + `max-file` 防止磁盘爆满 |

---

## 第十二章 总结与进阶路线

恭喜！走完前 11 章，你已经从零掌握了 Docker 的完整知识体系。这一章做一个全局回顾，并指出接下来可以深入的方向。

### 12.1 一张图回顾 Docker 全貌

```
Docker 知识全景图：

  基础概念（第 1-3 章）
  ═══════════════════════════════════════════════
  镜像 → 容器 → 仓库
  分层存储 / Union FS
  容器 vs 虚拟机

  核心技能（第 4-7 章）
  ═══════════════════════════════════════════════
  Dockerfile      构建镜像的配方
  容器管理        run / stop / logs / exec
  数据持久化      Volume / Bind Mount
  网络通信        自定义网络 / DNS 服务发现

  工程实践（第 8-9 章）
  ═══════════════════════════════════════════════
  Docker Compose  多容器编排
  实战项目        FastAPI + PG + Redis + Nginx
  多环境配置      override / .env

  生产化（第 10-11 章）
  ═══════════════════════════════════════════════
  镜像优化        多阶段构建 / 瘦身
  安全加固        非 root / Secrets / 扫描
  CI/CD           GitHub Actions 自动化部署
```

### 12.2 常用命令速查表

**镜像操作：**

| 命令 | 作用 |
|:---|:---|
| `docker build -t name:tag .` | 构建镜像 |
| `docker images` | 列出本地镜像 |
| `docker pull image:tag` | 拉取镜像 |
| `docker push image:tag` | 推送镜像 |
| `docker rmi image` | 删除镜像 |
| `docker image prune` | 清理悬空镜像 |

**容器操作：**

| 命令 | 作用 |
|:---|:---|
| `docker run -d -p 8080:80 --name x image` | 创建并运行容器 |
| `docker ps` / `docker ps -a` | 查看容器 |
| `docker stop x` / `docker start x` | 停止/启动 |
| `docker rm x` / `docker rm -f x` | 删除容器 |
| `docker logs -f x` | 查看日志 |
| `docker exec -it x bash` | 进入容器 |
| `docker inspect x` | 查看详情 |
| `docker stats` | 实时资源监控 |

**Compose 操作：**

| 命令 | 作用 |
|:---|:---|
| `docker compose up -d` | 启动所有服务 |
| `docker compose down` | 停止并清理 |
| `docker compose ps` | 查看服务状态 |
| `docker compose logs -f web` | 看某个服务日志 |
| `docker compose exec web bash` | 进入某个服务 |
| `docker compose build --no-cache` | 无缓存重建 |

**清理操作：**

| 命令 | 作用 |
|:---|:---|
| `docker system df` | 查看磁盘占用 |
| `docker system prune` | 清理所有废弃资源 |
| `docker volume prune` | 清理未使用的卷 |
| `docker container prune` | 清理已停止的容器 |

### 12.3 进阶方向：Kubernetes、Swarm、云原生生态

学完 Docker，接下来的方向：

```
Docker 之后的进阶路线：

  你现在的位置：Docker + Compose（单机编排）
       │
       ├──→ Kubernetes（K8s）⭐ 最主流
       │    容器编排的行业标准
       │    自动扩缩容、滚动更新、服务发现
       │    学习路径：Minikube → Deployment → Service → Ingress
       │
       ├──→ 云原生生态
       │    Helm（K8s 包管理）
       │    Istio（服务网格）
       │    ArgoCD（GitOps 持续部署）
       │
       ├──→ 可观测性
       │    Prometheus + Grafana（指标监控）
       │    Loki（日志聚合）
       │    Jaeger（链路追踪）
       │
       └──→ 云服务容器
            AWS ECS / Fargate
            阿里云 ACK / 函数计算
            Google Cloud Run
```

> 💡 **给初学者的建议**：不要急着学 Kubernetes。先把 Docker + Compose 用到滚瓜烂熟，在真实项目中积累经验。当你的服务需要跨多台机器部署、自动扩缩容时，再上 K8s。

---

## 附录

### A. Dockerfile 指令速查表

| 指令 | 作用 | 示例 |
|:---|:---|:---|
| `FROM` | 基础镜像 | `FROM python:3.11-slim` |
| `WORKDIR` | 工作目录 | `WORKDIR /app` |
| `COPY` | 复制文件 | `COPY . .` |
| `ADD` | 复制+解压 | `ADD app.tar.gz /app` |
| `RUN` | 执行命令（构建时） | `RUN pip install -r requirements.txt` |
| `ENV` | 环境变量 | `ENV DEBUG=false` |
| `ARG` | 构建参数 | `ARG VERSION=1.0` |
| `EXPOSE` | 声明端口 | `EXPOSE 8000` |
| `CMD` | 默认启动命令 | `CMD ["python", "main.py"]` |
| `ENTRYPOINT` | 固定入口 | `ENTRYPOINT ["python"]` |
| `USER` | 切换用户 | `USER appuser` |
| `LABEL` | 元数据标签 | `LABEL version="1.0"` |

### B. docker-compose.yml 常用配置项

```yaml
services:
  service_name:
    image: image:tag           # 使用现成镜像
    build: .                   # 从 Dockerfile 构建
    ports: ["8000:8000"]       # 端口映射
    volumes: ["./src:/app"]    # 挂载卷
    environment:               # 环境变量
      - KEY=value
    env_file: .env             # 从文件读取环境变量
    depends_on:                # 启动依赖
      db:
        condition: service_healthy
    healthcheck:               # 健康检查
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped    # 重启策略
    command: custom command    # 覆盖 CMD
    networks: [app-net]        # 指定网络
    deploy:                    # 资源限制
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
    profiles: [debug]          # 按需启动

volumes:
  volume_name:                 # 声明命名卷

networks:
  app-net:                     # 声明自定义网络
```

### C. Docker 常见问题与排错指南

| 问题 | 原因 | 解决 |
|:---|:---|:---|
| `Cannot connect to Docker daemon` | Docker 没启动 | 启动 Docker Desktop / `systemctl start docker` |
| `port is already allocated` | 端口被占用 | 换端口或 `lsof -i :端口` 找占用进程 |
| `no space left on device` | 磁盘满了 | `docker system prune -a` |
| `permission denied` | 文件权限问题 | `COPY --chown` 或 `chmod` |
| 容器一启动就退出 | CMD 命令执行完了 | 用 `-it` 或让服务前台运行 |
| 拉取镜像超时 | 网络问题 | 配置镜像加速器 |
| `exec format error` | 架构不匹配（ARM vs x86） | `--platform linux/amd64` |

### D. 推荐学习资源与官方文档链接

| 资源 | 链接 |
|:---|:---|
| Docker 官方文档 | https://docs.docker.com |
| Docker Hub | https://hub.docker.com |
| Docker Compose 官方文档 | https://docs.docker.com/compose |
| Dockerfile 最佳实践 | https://docs.docker.com/develop/develop-images/dockerfile_best-practices |
| Play with Docker（在线练习） | https://labs.play-with-docker.com |
| 《Docker — 从入门到实践》 | https://yeasy.gitbook.io/docker_practice |

