# Kubernetes 入门实战

> 从 Docker Compose 到 K8s——理解 Pod/Service/Deployment 核心概念、用 YAML 部署真实应用、掌握 Helm Chart 和日常运维命令，为后端开发者构建一条从"会用 Docker"到"能上 K8s"的完整路径。

---

## 1. 为什么需要 Kubernetes

如果你已经在用 Docker Compose 部署项目，一切看起来挺好的——`docker-compose up -d` 一键启动，`docker-compose logs` 看日志，开发环境舒适得不行。那为什么还要折腾 Kubernetes？

这一章回答这个问题：Docker 单机编排的天花板在哪里，Kubernetes 解决了什么 Docker 解决不了的问题。

### 1.1 Docker 单机的天花板：从 docker-compose up 开始说起

```
你的 docker-compose.yml 大概长这样：

  version: '3.8'
  services:
    web:
      image: myapp:latest
      ports: ["8000:8000"]
      depends_on: [db, redis]
    db:
      image: postgres:15
      volumes: [pgdata:/var/lib/postgresql/data]
    redis:
      image: redis:7
  volumes:
    pgdata:
```

开发环境完美。但当你说"我要上生产"，问题来了：

```
Docker Compose 在生产环境的五大局限：

  ❌ 问题 1：扩容靠手动
  ═══════════════════════════════════
  流量暴涨，web 需要从 1 个变成 5 个
  → docker-compose up --scale web=5
  → 但谁来做负载均衡？你得自己加 Nginx
  → 流量降了呢？又得手动 scale down
  → 凌晨 3 点流量暴涨？没人操作就挂了
  
  ❌ 问题 2：容器挂了没人管
  ═══════════════════════════════════
  web 容器 OOM 被杀了
  → docker-compose 的 restart: always 会重启
  → 但如果反复崩溃呢？一直重启一直崩，没有退避策略
  → 也没法自动把流量从坏容器切走
  
  ❌ 问题 3：服务发现是硬编码的
  ═══════════════════════════════════
  web 连 db 用的是 "db:5432"（容器名）
  → 只在同一台机器同一个 docker network 里有效
  → 跨机器部署？服务发现完全失效
  
  ❌ 问题 4：更新要停服
  ═══════════════════════════════════
  发布新版本：docker-compose pull && docker-compose up -d
  → 旧容器停了，新容器还没启动 → 短暂的停服窗口
  → 新版有 bug？手动回滚，又一次停服
  → 没有"滚动更新"——不能一个一个换
  
  ❌ 问题 5：只能在一台机器上
  ═══════════════════════════════════
  Docker Compose 只管一台机器上的容器
  → 一台机器的 CPU/内存总有上限
  → 机器宕机 → 所有服务全挂
  → 无法利用多台机器的资源
```

> 💡 **一句话总结**：Docker Compose 是"单机编排工具"——它管理一台机器上的容器启停和网络。而生产环境需要的是"集群编排"——跨多台机器调度、自动扩缩容、自愈、零停机更新。这就是 Kubernetes 的领域。

### 1.2 容器编排要解决的四个核心问题

把 1.1 的问题抽象一下，任何容器编排系统都要解决这四件事：

```
四大核心问题：

  1. 调度（Scheduling）
  ═══════════════════════════════════
  问题：有 10 台机器、50 个容器，谁跑在哪台机器上？
  Docker：你自己决定（ssh 到每台机器手动 docker run）
  K8s  ：Scheduler 自动选择——哪台机器 CPU 空闲就放哪台
  
  2. 服务发现与负载均衡（Service Discovery）
  ═══════════════════════════════════
  问题：web 有 5 个副本，请求怎么均匀分到 5 个上面？
  Docker：自己搭 Nginx + 手动维护 upstream 列表
  K8s  ：Service 自动负载均衡，Pod 加了/减了自动更新
  
  3. 自愈（Self-healing）
  ═══════════════════════════════════
  问题：某个容器 crash 了/某台机器挂了，怎么办？
  Docker：restart: always（只管重启，不管迁移）
  K8s  ：自动重启 + 自动迁移到健康节点 + 健康检查 + 退避策略
  
  4. 声明式管理（Declarative）
  ═══════════════════════════════════
  问题：我想要 5 个 web 副本、每个 512MB 内存
  Docker：你一步一步执行命令来实现（命令式）
  K8s  ：你写 YAML 描述"我要什么"，K8s 负责"怎么做到"
       → 当前只有 3 个副本？K8s 自动再创建 2 个
       → 有一个挂了变成 4 个？K8s 自动补到 5 个
```

> 💡 **声明式 vs 命令式**——这是理解 K8s 哲学的关键。你不是告诉 K8s "创建一个容器"（命令式），而是告诉它"我希望有 5 个副本在运行"（声明式）。K8s 会持续调谐（reconcile），确保现实状态匹配你的期望状态。
### 1.3 Kubernetes 的核心承诺：声明式、自愈、水平扩展

```
Kubernetes 的三大核心承诺：

  承诺 1：声明式——你说"要什么"，它来"怎么做"
  ═══════════════════════════════════
  你写一份 YAML：
    我要 3 个 web 副本
    每个需要 256MB 内存
    对外暴露 80 端口
  
  K8s 的工作：
    → 选择合适的节点创建 3 个 Pod
    → 配置网络让它们可被访问
    → 如果有一个挂了，自动再创建一个（保持 3 个）
  
  
  承诺 2：自愈——出了问题自动修复
  ═══════════════════════════════════
  → 容器 crash → 自动重启（带指数退避）
  → 健康检查失败 → 自动从负载均衡移除
  → 节点宕机 → 自动把 Pod 迁移到其他节点
  → 不需要人值守，凌晨 3 点也能自动恢复
  
  
  承诺 3：水平扩展——弹性伸缩
  ═══════════════════════════════════
  → 手动：kubectl scale deployment web --replicas=10
  → 自动：HPA 根据 CPU/内存使用率自动扩缩
  → 扩容不需要改代码、不需要改配置
  → 从 1 个副本扩到 100 个，命令一样简单
```

**K8s vs Docker Compose vs Docker Swarm：**

| 能力 | Docker Compose | Docker Swarm | Kubernetes |
|:---|:---|:---|:---|
| **定位** | 单机开发编排 | 简单集群编排 | 生产级集群编排 |
| **多机器** | ❌ 单机 | ✅ 多节点 | ✅ 多节点 |
| **自愈** | restart 重启 | ✅ 基本 | ✅ 高级（迁移+退避） |
| **服务发现** | 容器名（单机） | ✅ DNS | ✅ DNS + 负载均衡 |
| **滚动更新** | ❌ | ✅ 基本 | ✅ 高级（金丝雀、蓝绿） |
| **生态** | 简单 | 较少 | 极丰富（Helm/Istio/Argo） |
| **学习曲线** | 低 | 中 | 高 |
| **适用场景** | 开发/测试 | 小规模生产 | 中大规模生产 |

> 💡 **务实建议**：不是所有项目都需要 K8s。如果你的项目只有 2-3 个服务、流量可预测、一台机器够用，Docker Compose + 一台好服务器已经足够。当你需要多机器、自动扩缩容、零停机部署时，再考虑 K8s。不要为了"技术新潮"而上 K8s——它的复杂度是真实的。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Docker Compose** | 单机编排工具，不支持多机器、自动扩缩、零停机更新 |
| **容器编排** | 调度 + 服务发现 + 自愈 + 声明式管理 |
| **声明式** | 描述期望状态，K8s 自动调谐到目标，核心哲学 |
| **自愈** | 容器崩溃自动重启，节点宕机自动迁移 Pod |
| **何时上 K8s** | 需要多机器 + 弹性扩缩 + 零停机部署时再上 |

---

## 2. Kubernetes 架构全景

在动手写 YAML 之前，先花 5 分钟理解 K8s 集群的"组织架构"。不需要记住每个组件的实现细节，只需要知道**谁负责什么**——这样出了问题你知道该看哪里的日志。

### 2.1 Control Plane：大脑与决策层

Control Plane（控制平面）是 K8s 的大脑，负责做决策。它通常运行在专门的 Master 节点上。

```
Control Plane 的四大组件：

  API Server（kube-apiserver）
  ═══════════════════════════════════
  → K8s 的"前台"——所有请求都经过它
  → kubectl 命令 → 发给 API Server → 写入 etcd
  → 其他组件也通过 API Server 通信（不直接互相调用）
  → 类比：公司的前台 + 内部通讯系统
  
  etcd
  ═══════════════════════════════════
  → 分布式键值存储，K8s 的"数据库"
  → 存储所有集群状态：Pod 列表、Service 配置、Secret...
  → 唯一的数据源（Single Source of Truth）
  → 类比：公司的档案室——所有决策记录都在这里
  → ⚠️ etcd 挂了 = 整个集群失忆，必须做备份！
  
  Scheduler（kube-scheduler）
  ═══════════════════════════════════
  → 负责决定"新 Pod 跑在哪个节点上"
  → 考虑因素：节点剩余资源、亲和性规则、污点容忍
  → 只做决策，不执行——决定后告诉 kubelet 去创建
  → 类比：HR 分配工位——考虑位置、团队、资源
  
  Controller Manager（kube-controller-manager）
  ═══════════════════════════════════
  → 一堆控制器的集合，每个控制器负责一类资源
  → Deployment Controller：保证副本数 = 期望数
  → Node Controller：检测节点是否健康
  → Job Controller：管理一次性任务
  → 类比：公司的各个部门经理——各管一摊事
  → 核心工作：观察现状 → 对比期望 → 调谐（reconcile）
```

> 💡 **"调谐循环"（Reconcile Loop）** 是 K8s 最核心的设计模式：每个 Controller 不断做三件事——① 观察当前状态 ② 对比期望状态 ③ 采取行动消除差异。整个 K8s 就是一堆调谐循环组成的。

### 2.2 Worker Node：干活的工人

Worker Node 是真正运行你的应用容器的机器。每个 Worker Node 上有三个关键组件：

```
Worker Node 的三大组件：

  kubelet
  ═══════════════════════════════════
  → 每个 Node 上的"代理人"
  → 监听 API Server 的指令：要在本节点上创建什么 Pod
  → 调用容器运行时来启动/停止容器
  → 定期向 API Server 汇报节点状态和 Pod 健康状况
  → 类比：工厂的车间主任——接收总部指令，管理本车间工人
  
  kube-proxy
  ═══════════════════════════════════
  → 负责网络规则：让 Service 的虚拟 IP 能正确路由到 Pod
  → 维护 iptables / IPVS 规则
  → 当 Pod 增减时自动更新路由表
  → 类比：公司的网络管理员——确保电话拨到分机号能接通
  
  容器运行时（Container Runtime）
  ═══════════════════════════════════
  → 真正创建和运行容器的程序
  → 最常见：containerd（Docker 的底层也用它）
  → K8s 从 1.24 起不再直接支持 Docker，但 containerd 兼容
  → 类比：工厂的机器——kubelet 说"启动"，它就干活
```

```
一个 Pod 的创建过程——各组件协作流程：

  1. 你执行 kubectl apply -f deployment.yaml
  2. kubectl → API Server：请创建一个 Deployment
  3. API Server → etcd：存储这个 Deployment 的期望状态
  4. Controller Manager 发现：期望 3 副本，当前 0 副本
  5. Controller Manager → API Server：请创建 3 个 Pod
  6. Scheduler 发现 3 个未调度的 Pod
  7. Scheduler → API Server：Pod-1 去 Node-A，Pod-2 去 Node-B...
  8. Node-A 上的 kubelet 收到通知：你要运行 Pod-1
  9. kubelet → containerd：创建并启动容器
  10. kubelet → API Server：Pod-1 状态 = Running ✅
```
### 2.3 一张图理解 K8s 架构

```
K8s 集群全景图：

  ┌─────────────────────────────────────────────────┐
  │                Control Plane (Master)            │
  │                                                  │
  │  ┌──────────┐  ┌──────┐  ┌───────────┐  ┌─────┐│
  │  │API Server│  │ etcd │  │ Scheduler │  │ CM  ││
  │  │（入口）  │  │(存储)│  │ (调度)    │  │(调谐)││
  │  └────┬─────┘  └──────┘  └───────────┘  └─────┘│
  └───────┼─────────────────────────────────────────┘
          │  API 调用
  ┌───────┼──────────────────────────────────────────┐
  │       ▼       Worker Node A                      │
  │  ┌─────────┐  ┌───────────┐  ┌────────────────┐ │
  │  │ kubelet │  │kube-proxy │  │  containerd    │ │
  │  └────┬────┘  └───────────┘  └───────┬────────┘ │
  │       │                              │           │
  │  ┌────▼────┐  ┌──────────┐  ┌───────▼────────┐ │
  │  │  Pod A  │  │  Pod B   │  │    Pod C       │ │
  │  │(web:v2) │  │(web:v2)  │  │  (redis)       │ │
  │  └─────────┘  └──────────┘  └────────────────┘ │
  └──────────────────────────────────────────────────┘
  ┌──────────────────────────────────────────────────┐
  │              Worker Node B                       │
  │  ┌─────────┐  ┌───────────┐  ┌────────────────┐ │
  │  │ kubelet │  │kube-proxy │  │  containerd    │ │
  │  └────┬────┘  └───────────┘  └───────┬────────┘ │
  │       │                              │           │
  │  ┌────▼────┐  ┌──────────┐                      │
  │  │  Pod D  │  │  Pod E   │                      │
  │  │(web:v2) │  │(postgres)│                      │
  │  └─────────┘  └──────────┘                      │
  └──────────────────────────────────────────────────┘
```

**组件速查表（一句话版）：**

| 组件 | 在哪 | 一句话职责 |
|:---|:---|:---|
| **API Server** | Master | 所有请求的入口，组件间通信的中枢 |
| **etcd** | Master | 存储集群所有状态的分布式数据库 |
| **Scheduler** | Master | 决定 Pod 跑在哪个 Node 上 |
| **Controller Manager** | Master | 一堆控制器，持续调谐期望状态 = 实际状态 |
| **kubelet** | 每个 Node | 接收指令、管理本节点上的 Pod |
| **kube-proxy** | 每个 Node | 维护网络规则，让 Service IP 能到达 Pod |
| **containerd** | 每个 Node | 真正创建和运行容器的运行时 |

**本地练习环境推荐：**

| 工具 | 安装复杂度 | 推荐场景 |
|:---|:---|:---|
| **Docker Desktop** | 最低（勾选 K8s） | Mac/Windows 首选 |
| **Minikube** | 低 | 需要更多配置控制时 |
| **kind** | 低 | CI/CD 和自动化测试 |

> 💡 **开发者不需要自己搭 Control Plane**。用 Docker Desktop 开启 K8s 支持，或者用 `minikube start`，一个命令就有一个完整的本地集群。生产环境通常用云厂商的托管 K8s（EKS/GKE/AKS），Control Plane 由云厂商运维。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Control Plane** | 大脑：API Server（入口）+ etcd（存储）+ Scheduler（调度）+ CM（调谐） |
| **Worker Node** | 干活：kubelet（代理）+ kube-proxy（网络）+ containerd（运行时） |
| **调谐循环** | 观察现状 → 对比期望 → 消除差异，K8s 的核心设计模式 |
| **API Server 中枢** | 所有组件通过 API Server 通信，不直接互调 |
| **本地练习** | Docker Desktop 开启 K8s 最简单 |

---

## 3. 核心资源对象：Pod、Deployment、Service

K8s 里最重要的三个概念——理解它们的关系，你就能部署 90% 的应用。一句话概括：**Pod 是运行单元，Deployment 管理 Pod，Service 暴露 Pod**。

### 3.1 Pod：最小调度单元（不是容器！）

```
Pod 和容器的关系：

  ┌──────────── Pod ────────────┐
  │                              │
  │  ┌──────────┐ ┌──────────┐  │
  │  │ 容器 A   │ │ 容器 B   │  │  ← 一个 Pod 里可以有多个容器
  │  │ (web app)│ │ (sidecar)│  │
  │  └──────────┘ └──────────┘  │
  │                              │
  │  共享：                       │
  │  → 网络命名空间（同一个 IP）  │
  │  → 存储卷（可以读写同一目录） │
  │  → 生命周期（一起创建一起销毁）│
  └──────────────────────────────┘
  
  关键理解：
  → Pod 是 K8s 调度的最小单位（不是容器！）
  → 大多数时候 1 个 Pod = 1 个容器（单容器 Pod）
  → 多容器 Pod 是高级用法（Sidecar 模式），后面讲
```

**最简单的 Pod YAML：**

```yaml
# pod-example.yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-web          # Pod 名称
  labels:
    app: web             # 标签（Service 用它找到这个 Pod）
spec:
  containers:
    - name: web          # 容器名
      image: nginx:1.25  # 镜像
      ports:
        - containerPort: 80  # 容器内监听的端口
```

```bash
# 创建 Pod
kubectl apply -f pod-example.yaml

# 查看 Pod 状态
kubectl get pods
# NAME     READY   STATUS    RESTARTS   AGE
# my-web   1/1     Running   0          10s

# 查看 Pod 详情
kubectl describe pod my-web
```

> 💡 **你几乎不会直接创建 Pod**。就像你不会直接 `docker run` 来部署生产应用一样——你用 Deployment 来管理 Pod。直接创建的 Pod 没有自愈能力，挂了就没了。Deployment 才能保证"挂了自动重建"。

### 3.2 Deployment：管理 Pod 的生命周期

Deployment 是你在 K8s 中最常用的资源——它管理一组 Pod 的副本数、更新策略和回滚。

```
Deployment → ReplicaSet → Pod 的层级关系：

  Deployment（你写的 YAML）
       │ 管理
       ▼
  ReplicaSet（K8s 自动创建）
       │ 管理
       ▼
  Pod × N（按 replicas 数量创建）
  
  → 你只需关心 Deployment
  → ReplicaSet 是中间层，通常不需要直接操作
  → 滚动更新时，Deployment 创建新 ReplicaSet，逐步替换旧的
```

**Deployment YAML 完整示例：**

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3                    # 期望副本数
  selector:
    matchLabels:
      app: web                   # 用 Label 选择管理哪些 Pod
  template:                      # Pod 模板（下面就是 Pod 的定义）
    metadata:
      labels:
        app: web                 # 🔥 必须和 selector.matchLabels 一致
    spec:
      containers:
        - name: web
          image: myapp:v1
          ports:
            - containerPort: 8000
          resources:             # 资源限制（第 10 章详讲）
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
```

```bash
# 部署
kubectl apply -f deployment.yaml

# 查看 Deployment 状态
kubectl get deployments
# NAME      READY   UP-TO-DATE   AVAILABLE   AGE
# web-app   3/3     3            3           30s

# 扩容到 5 个副本
kubectl scale deployment web-app --replicas=5

# 更新镜像版本（触发滚动更新）
kubectl set image deployment/web-app web=myapp:v2

# 查看滚动更新进度
kubectl rollout status deployment/web-app

# 回滚到上一个版本
kubectl rollout undo deployment/web-app
```

> 💡 **Label 是 K8s 的"胶水"**。Deployment 通过 `selector.matchLabels` 找到它管理的 Pod，Service 也通过 Label 找到要转发流量的 Pod。`app: web` 这个 Label 把 Deployment、Pod、Service 串联起来。
### 3.3 Service：稳定的网络入口与服务发现

Pod 的 IP 是不稳定的——Pod 重建后 IP 就变了。Service 提供一个**不变的虚拟 IP（ClusterIP）**，自动把流量转发到后面的 Pod。

```
为什么需要 Service？

  没有 Service 的世界：
  ═══════════════════════════════════
  web 容器要连 db，直连 Pod IP：10.244.1.5
  → db Pod 重建了 → 新 IP 变成 10.244.2.8
  → web 还在连 10.244.1.5 → 连接失败 ❌
  
  有 Service 的世界：
  ═══════════════════════════════════
  web 容器连 db-service：10.96.0.100（永远不变）
  → db Pod 重建了 → Service 自动更新后端列表
  → web 连的还是 10.96.0.100 → 正常工作 ✅
  → 也可以用 DNS 名：db-service.default.svc.cluster.local
```

**Service YAML 示例：**

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web              # 🔥 找到所有 label 为 app=web 的 Pod
  ports:
    - port: 80            # Service 暴露的端口
      targetPort: 8000    # 转发到 Pod 的端口
  type: ClusterIP         # 默认类型：只在集群内可访问
```

**三种 Service 类型：**

| 类型 | 可访问范围 | 使用场景 |
|:---|:---|:---|
| **ClusterIP** | 集群内部 | 数据库、Redis 等内部服务（默认） |
| **NodePort** | 集群外（通过节点 IP:端口） | 开发测试、小规模暴露 |
| **LoadBalancer** | 互联网（云厂商提供外部 IP） | 生产环境面向用户的服务 |

```
三种类型的流量路径：

  ClusterIP（只在集群内）：
  Pod-A ──▶ web-service:80 ──▶ Pod-B (app=web)
  
  NodePort（节点 IP + 端口）：
  外部请求 ──▶ NodeIP:30080 ──▶ web-service:80 ──▶ Pod-B
  
  LoadBalancer（云厂商负载均衡器）：
  互联网 ──▶ 外部IP:80 ──▶ NodePort ──▶ Service ──▶ Pod-B
```

> 💡 **在集群内，直接用 Service 的 DNS 名访问**：`http://web-service` 或 `http://web-service.default.svc.cluster.local`。这和 Docker Compose 里用容器名访问（`http://db:5432`）很像——K8s 的 DNS 解析做了同样的事，而且跨节点也有效。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Pod** | 最小调度单元，通常 1 Pod = 1 容器，共享网络和存储 |
| **Deployment** | 管理 Pod 的副本数、滚动更新和回滚 |
| **ReplicaSet** | Deployment 自动创建的中间层，通常不直接操作 |
| **Service** | 给一组 Pod 提供不变的 IP 和 DNS 名，自动负载均衡 |
| **Label + Selector** | K8s 的"胶水"——Deployment/Service 通过 Label 找到 Pod |

---

## 4. 配置管理：ConfigMap、Secret、环境变量

Docker 时代你可能习惯把数据库地址写在 `.env` 文件里，或者直接硬编码在 `docker-compose.yml` 中。K8s 提供了更规范的配置管理方案——ConfigMap 和 Secret。

### 4.1 配置外置原则：为什么不把配置写进镜像

```
把配置写进镜像的三个坏处：

  ❌ 环境绑定
  ═══════════════════════════════════
  镜像里写了 DB_HOST=prod-db.company.com
  → 这个镜像只能在生产环境用
  → 测试环境要改配置？重新 build 一个镜像
  → 一个配置改了 = 重新构建 + 重新推送 + 重新部署
  
  ❌ 安全风险
  ═══════════════════════════════════
  镜像里包含数据库密码
  → 任何能 pull 这个镜像的人都能看到密码
  → 密码推到了 Docker Hub？恭喜你，全世界都知道了
  
  ❌ 无法动态更新
  ═══════════════════════════════════
  改个日志级别从 INFO 到 DEBUG
  → 要重新 build 镜像、重新部署
  → 应该能不重启就生效才对
```

**12-Factor App 原则**：配置应该通过环境变量注入，镜像应该在所有环境中是同一个。

```
K8s 的配置管理方案：

  ┌─────────────────────────────────────────┐
  │              同一个镜像 myapp:v1         │
  └───────────────────┬─────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
     开发环境      测试环境      生产环境
   ConfigMap:     ConfigMap:    ConfigMap:
   DB=dev-db     DB=test-db    DB=prod-db
   DEBUG=true    DEBUG=true    DEBUG=false
   
  → 同一个镜像 + 不同的 ConfigMap = 不同的行为
  → 配置和代码完全解耦
```

### 4.2 ConfigMap：非敏感配置的管理

ConfigMap 存储非敏感的键值对配置（数据库地址、日志级别、功能开关等）。

**创建 ConfigMap：**

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
  LOG_LEVEL: "INFO"
  # 也可以存整个配置文件
  app.conf: |
    [server]
    host = 0.0.0.0
    port = 8000
    workers = 4
```

```bash
# 也可以命令行创建
kubectl create configmap app-config \
  --from-literal=DATABASE_HOST=postgres-service \
  --from-literal=LOG_LEVEL=INFO

# 或从文件创建
kubectl create configmap nginx-config --from-file=nginx.conf
```

**使用方式 1：注入为环境变量**

```yaml
# 在 Deployment 的 Pod 模板中使用
spec:
  containers:
    - name: web
      image: myapp:v1
      envFrom:                    # 把整个 ConfigMap 导入为环境变量
        - configMapRef:
            name: app-config
      # 或者只导入特定 key
      env:
        - name: DB_HOST           # 环境变量名
          valueFrom:
            configMapKeyRef:
              name: app-config    # ConfigMap 名
              key: DATABASE_HOST  # 取哪个 key
```

**使用方式 2：挂载为文件**

```yaml
spec:
  containers:
    - name: web
      image: myapp:v1
      volumeMounts:
        - name: config-volume
          mountPath: /etc/app/     # 挂载到容器的这个目录
  volumes:
    - name: config-volume
      configMap:
        name: app-config          # 每个 key 变成一个文件
```

| 方式 | 适用场景 | 更新生效 |
|:---|:---|:---|
| **环境变量** | 简单键值对（DB_HOST、LOG_LEVEL） | 需重启 Pod |
| **文件挂载** | 配置文件（nginx.conf、app.yaml） | 自动更新（约 1 分钟） |
### 4.3 Secret：敏感信息的存储与使用

Secret 和 ConfigMap 结构一样，但专门用于存储敏感数据（密码、API Key、TLS 证书）。

**创建 Secret：**

```bash
# 命令行创建（推荐，自动 Base64 编码）
kubectl create secret generic db-credentials \
  --from-literal=DB_PASSWORD=my_secret_123 \
  --from-literal=DB_USER=admin
```

```yaml
# 或用 YAML（需要手动 Base64 编码）
# echo -n 'my_secret_123' | base64  →  bXlfc2VjcmV0XzEyMw==
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  DB_PASSWORD: bXlfc2VjcmV0XzEyMw==    # Base64 编码后的值
  DB_USER: YWRtaW4=
```

**在 Pod 中使用 Secret：**

```yaml
spec:
  containers:
    - name: web
      image: myapp:v1
      env:
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: DB_PASSWORD
```

**ConfigMap vs Secret 对比：**

| 特性 | ConfigMap | Secret |
|:---|:---|:---|
| **存储内容** | 非敏感配置 | 密码、API Key、证书 |
| **编码** | 明文 | Base64（不是加密！） |
| **etcd 存储** | 明文 | 可配置加密存储 |
| **大小限制** | 1MB | 1MB |
| **使用方式** | 环境变量 / 文件挂载 | 环境变量 / 文件挂载 |

> 💡 **Secret 的 Base64 不是加密！** Base64 只是编码，`echo bXlfc2VjcmV0XzEyMw== | base64 -d` 就能解码。真正的安全靠：① 启用 etcd 加密（EncryptionConfiguration）② RBAC 限制谁能读 Secret ③ 用外部密钥管理（Vault/AWS Secrets Manager）。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **配置外置** | 同一个镜像 + 不同 ConfigMap = 不同环境，镜像不含配置 |
| **ConfigMap** | 存非敏感键值对，可注入为环境变量或挂载为文件 |
| **Secret** | 存敏感信息，Base64 编码（不是加密），需配合 RBAC |
| **环境变量 vs 文件** | 键值对用环境变量，配置文件用挂载 |
| **文件挂载自动更新** | ConfigMap 文件挂载 ~1 分钟自动刷新，环境变量需重启 Pod |

---

## 5. 存储与持久化：Volume、PV、PVC

容器天生是"用完就扔"的——Pod 重建后里面的文件全部丢失。对于无状态的 Web 应用没问题，但数据库、文件上传这些有状态服务怎么办？

### 5.1 为什么容器需要持久化存储

```
容器的文件系统问题：

  ═══════════════════════════════════
  容器启动 → 写数据到 /var/lib/postgresql/data
  Pod 重建（更新/扩容/节点迁移）
  新容器启动 → /var/lib/postgresql/data 是空的！
  → 所有数据丢失 ❌
  
  原因：容器的文件系统是"临时存储层"（ephemeral）
  → 容器删除 = 文件系统删除
  → 和 Docker 一样的问题（不挂 Volume 数据就丢）
```

**K8s Volume 类型概览：**

| 类型 | 生命周期 | 使用场景 |
|:---|:---|:---|
| **emptyDir** | 与 Pod 相同（Pod 删除就没了） | Pod 内多容器共享临时文件 |
| **hostPath** | 节点本地路径 | 开发测试（⚠️ 绑定特定节点） |
| **PV/PVC** | 独立于 Pod | ✅ 生产环境数据库等持久化需求 |

```
各类型适用场景：

  emptyDir：Pod 内多容器传文件
  ═══════════════════════════════════
  Pod {
    容器 A → 写日志到 /shared/logs
    容器 B → 读 /shared/logs 做分析  ← 共享 emptyDir
  }
  → Pod 删了，数据就没了（通常没关系）
  
  hostPath：绑定节点目录（慎用！）
  ═══════════════════════════════════
  容器 → /data → 节点的 /mnt/data
  → 数据在节点上，Pod 重建后还在
  → 但！Pod 迁移到其他节点，数据就不见了
  → 只适合开发测试，生产环境别用
  
  PV / PVC：真正的持久化（推荐）
  ═══════════════════════════════════
  独立于 Pod 和节点的外部存储
  → 云盘（AWS EBS / 阿里云盘）
  → 网络文件系统（NFS）
  → Pod 迁移到任何节点都能挂载
```

> 💡 **经验法则**：无状态服务（Web API）→ 不需要 Volume。有状态服务（数据库、文件存储）→ 必须用 PV/PVC。

### 5.2 PV 与 PVC：存储的"供需对接"

PV 和 PVC 是 K8s 存储的核心概念——用"房东与租客"的模型来理解：

```
PV / PVC 的关系：

  PV（PersistentVolume）= 房东提供的房间
  ═══════════════════════════════════
  → 管理员（或 StorageClass）创建
  → 代表一块真实的存储（云盘、NFS、本地盘）
  → 定义：大小、访问模式、回收策略
  
  PVC（PersistentVolumeClaim）= 租客的需求
  ═══════════════════════════════════  
  → 开发者创建
  → 描述"我需要多大的存储"
  → K8s 自动匹配合适的 PV（绑定）
  
  绑定流程：
  开发者写 PVC → K8s 找到匹配的 PV → 绑定 → Pod 使用
  
  为什么要分离？
  → 存储的管理（PV）和使用（PVC）解耦
  → 开发者不需要关心底层存储是 AWS EBS 还是 NFS
```

**手动创建 PV + PVC：**

```yaml
# pv.yaml - 管理员创建（或用 StorageClass 自动创建）
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pg-pv
spec:
  capacity:
    storage: 10Gi              # 存储大小
  accessModes:
    - ReadWriteOnce            # 只能被一个 Node 读写
  hostPath:                    # 本地开发用 hostPath
    path: /mnt/data/postgres
---
# pvc.yaml - 开发者创建
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pg-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi            # 我需要 10Gi
  # K8s 自动找到 >= 10Gi 的 PV 并绑定
```

**更推荐：StorageClass 动态供给（生产环境用）**

```yaml
# 使用 StorageClass，不需要手动创建 PV
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pg-pvc
spec:
  storageClassName: standard   # 引用 StorageClass
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
# → K8s 自动创建 PV（云盘）并绑定，无需管理员干预
```

> 💡 **生产环境用 StorageClass 动态供给**，不要手动创建 PV。云厂商的托管 K8s（EKS/GKE）都预装了 StorageClass，写个 PVC 就自动创建云盘。
### 5.3 实战：给 PostgreSQL 挂载持久卷

把前面学的串起来——完整的 PostgreSQL 部署（Deployment + PVC + Service + Secret）：

```yaml
# postgres-all.yaml - 完整的 PostgreSQL K8s 部署

# 1. Secret：数据库密码
apiVersion: v1
kind: Secret
metadata:
  name: pg-secret
type: Opaque
data:
  POSTGRES_PASSWORD: cGFzc3dvcmQxMjM=   # password123
---
# 2. PVC：持久存储
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pg-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
# 3. Deployment：数据库 Pod
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1                    # 数据库通常只需 1 副本
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:15
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: pg-secret
                  key: POSTGRES_PASSWORD
          volumeMounts:
            - name: pg-data
              mountPath: /var/lib/postgresql/data
      volumes:
        - name: pg-data
          persistentVolumeClaim:
            claimName: pg-pvc    # 引用上面的 PVC
---
# 4. Service：内部访问
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
  type: ClusterIP               # 内部服务，不对外暴露
```

```bash
# 一键部署
kubectl apply -f postgres-all.yaml

# 验证
kubectl get pods,pvc,svc
# NAME                          READY   STATUS    RESTARTS   AGE
# pod/postgres-xxx              1/1     Running   0          30s
# 
# NAME                     STATUS   VOLUME   CAPACITY   ACCESS
# pvc/pg-pvc               Bound    pv-xxx   5Gi        RWO
# 
# NAME                       TYPE        CLUSTER-IP     PORT(S)
# service/postgres-service   ClusterIP   10.96.0.105    5432/TCP

# Web 应用连接数据库：postgres-service:5432
```

> 💡 **docker-compose 对照**：`volumes: [pgdata:/var/lib/postgresql/data]` 变成了 PVC + volumeMount，`environment: POSTGRES_PASSWORD` 变成了 Secret + env.valueFrom。结构不同，但逻辑完全一样。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **emptyDir** | Pod 内临时共享存储，Pod 删了就没了 |
| **hostPath** | 绑定节点目录，Pod 迁移数据就丢了，只适合开发 |
| **PV** | 管理员定义的存储资源（"有一块 10G 的盘"） |
| **PVC** | 开发者的存储申请（"我要 10G"），K8s 自动匹配 PV |
| **StorageClass** | 动态供给，写 PVC 自动创建云盘，生产环境推荐 |

---

## 6. 网络与 Ingress：从集群内到集群外

第 3 章讲了 Service 的基本概念，这章深入网络——K8s 的网络模型怎么工作、流量怎么从互联网一路到达你的 Pod。

### 6.1 K8s 网络模型：每个 Pod 都有 IP

```
K8s 网络的三大规则：

  规则 1：每个 Pod 有自己的 IP
  ═══════════════════════════════════
  → 不共享、不冲突
  → Pod-A: 10.244.1.5    Pod-B: 10.244.2.8
  → 和虚拟机一样——每个 Pod 就像一台独立的机器
  
  规则 2：所有 Pod 可以直接通信
  ═══════════════════════════════════
  → 不管在同一个 Node 还是不同 Node
  → Pod-A (Node-1) 可以直接 ping Pod-B (Node-2)
  → 没有 NAT 翻译，源 IP 就是 Pod IP
  
  规则 3：所有 Node 可以和所有 Pod 通信
  ═══════════════════════════════════
  → Node 上的进程可以直接访问任意 Pod IP
```

```
和 Docker 默认网络的对比：

  Docker 默认（bridge 模式）：
  ═══════════════════════════════════
  → 每个容器有自己的 IP（172.17.x.x）
  → 但只在同一台机器的同一个 bridge 网络内有效
  → 跨机器的容器无法直接通信
  → 对外需要端口映射（-p 8000:8000）
  
  K8s 网络：
  ═══════════════════════════════════
  → 每个 Pod 有集群范围的唯一 IP（10.244.x.x）
  → 跨 Node 也能直接通信（CNI 插件实现）
  → 不需要端口映射，Pod 直接用自己的端口
  → 通过 Service / Ingress 对外暴露
```

> 💡 **CNI 插件**（Container Network Interface）负责实现"所有 Pod 互通"。常见的有 Calico、Flannel、Cilium。云厂商托管 K8s 通常预装好了，你不需要操心选择。

### 6.2 Service 类型详解：流量怎么进来

第 3 章简单介绍过 Service 类型，这里深入每种类型的流量路径：

```
三种 Service 类型的完整流量路径：

  ① ClusterIP（默认）：只在集群内可访问
  ═══════════════════════════════════
  Pod-A ──▶ web-svc:80 ──▶ [kube-proxy 路由] ──▶ Pod-B
                 │
           ClusterIP: 10.96.0.100
           只存在于集群内部的虚拟 IP
  
  ② NodePort：在 ClusterIP 基础上，每个 Node 开一个端口
  ═══════════════════════════════════
  外部 ──▶ 任意NodeIP:30080 ──▶ ClusterIP:80 ──▶ Pod-B
  
  → 端口范围：30000-32767
  → 所有 Node 都监听这个端口（即使 Pod 不在这个 Node 上）
  → 适合开发测试，生产环境不推荐（端口不美观、无 HTTPS）
  
  ③ LoadBalancer：在 NodePort 基础上，云厂商提供外部 IP
  ═══════════════════════════════════
  互联网 ──▶ 外部IP:80 ──▶ NodePort ──▶ ClusterIP ──▶ Pod-B
                │
          云厂商自动创建负载均衡器（ALB/CLB）
          分配公网 IP，自带健康检查
```

**NodePort YAML 示例：**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - port: 80              # ClusterIP 端口
      targetPort: 8000      # Pod 端口
      nodePort: 30080       # Node 端口（可选，不填自动分配）
```

| 类型 | 适用场景 | 需要 | 缺点 |
|:---|:---|:---|:---|
| **ClusterIP** | 内部服务（DB/Redis/微服务间调用） | 无 | 外部无法访问 |
| **NodePort** | 开发测试、临时暴露 | 知道 Node IP | 端口丑（30000+），无 TLS |
| **LoadBalancer** | 生产环境面向用户 | 云厂商支持 | 每个 Service 一个 LB，费用高 |

> 💡 **LoadBalancer 的问题**：每个 Service 创建一个云负载均衡器，10 个 Service = 10 个 LB = 10 份钱。解决方案就是下面要讲的 **Ingress**——一个入口，路由到多个 Service。
### 6.3 Ingress：HTTP 路由与域名管理

Ingress 是 K8s 的"统一入口"——一个负载均衡器 + 路径/域名路由，取代多个 LoadBalancer Service。

```
没有 Ingress：每个 Service 一个 LB
═══════════════════════════════════
api.example.com  → LoadBalancer → api-service
web.example.com  → LoadBalancer → web-service
admin.example.com → LoadBalancer → admin-service
→ 3 个 LB = 3 份钱 💸

有 Ingress：一个入口，路由到多个 Service
═══════════════════════════════════
                 ┌──▶ api-service    (/api/*)
互联网 ──▶ Ingress ──▶ web-service    (/)
                 └──▶ admin-service  (/admin/*)
→ 1 个 LB = 1 份钱 ✅
```

**安装 Nginx Ingress Controller：**

```bash
# 安装 Nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.0/deploy/static/provider/cloud/deploy.yaml

# 验证
kubectl get pods -n ingress-nginx
```

**Ingress YAML 示例（路径路由 + TLS）：**

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  tls:                            # HTTPS 配置
    - hosts:
        - example.com
      secretName: tls-secret      # TLS 证书（Secret 类型）
  rules:
    - host: example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 80
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web-service
                port:
                  number: 80
```

```bash
# 创建 TLS Secret
kubectl create secret tls tls-secret \
  --cert=fullchain.pem \
  --key=privkey.pem
```

> 💡 **cert-manager** 可以自动申请和续期 Let's Encrypt 证书。安装后只需在 Ingress 加一行 annotation：`cert-manager.io/cluster-issuer: letsencrypt-prod`，就能自动管理 HTTPS 证书，不用手动操作。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Pod 网络** | 每个 Pod 一个 IP，集群内所有 Pod 可直接通信 |
| **CNI 插件** | Calico/Flannel/Cilium，实现跨节点 Pod 通信 |
| **NodePort** | 每个 Node 开端口（30000+），开发测试用 |
| **LoadBalancer** | 云厂商提供外部 IP，生产环境用但每个 Service 一个 LB |
| **Ingress** | 一个入口路由到多个 Service，支持路径/域名路由 + TLS |

---

## 7. 实战：从 Docker Compose 迁移到 K8s

这是全书最核心的章节——把一个真实的 `docker-compose.yml` 逐项翻译成 K8s YAML。如果你已经会写 Docker Compose，这一章让你自然过渡到 K8s。

### 7.1 案例介绍：FastAPI + PostgreSQL + Redis 三件套

**起点：你熟悉的 docker-compose.yml**

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    image: myapp:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://admin:password123@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=password123
      - POSTGRES_DB=mydb
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  pgdata:
```

**Docker Compose → K8s 概念映射：**

| Docker Compose | K8s 资源 | 说明 |
|:---|:---|:---|
| `services.web` | Deployment + Service | Pod 定义 + 网络暴露 |
| `image:` | `spec.containers.image` | 完全相同 |
| `ports:` | Service + containerPort | 端口映射变成 Service |
| `environment:` | ConfigMap / Secret + env | 配置外置 |
| `depends_on:` | 不需要 | K8s 用 Service DNS 自动发现 |
| `volumes:` | PVC + volumeMounts | 持久存储 |

> 💡 **`depends_on` 不需要翻译**。Docker Compose 的 `depends_on` 控制启动顺序，但 K8s 不需要——服务通过 Service DNS 发现，Pod 启动顺序不重要。Web 应用在 DB 没就绪时会连接失败并重试，K8s 的自愈机制会处理好。

### 7.2 docker-compose.yml → K8s YAML 逐项翻译

按依赖顺序翻译：**配置 → 数据库 → 缓存 → Web 应用**。

**Step 1：配置和密钥（对应 `environment:`）**

```yaml
# k8s/01-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "mydb"
  REDIS_URL: "redis://redis-service:6379"
---
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  POSTGRES_USER: YWRtaW4=               # admin
  POSTGRES_PASSWORD: cGFzc3dvcmQxMjM=   # password123
```

**Step 2：PostgreSQL（对应 `services.db`）**

```yaml
# k8s/02-postgres.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pg-pvc
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 5Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels: { app: postgres }
  template:
    metadata:
      labels: { app: postgres }
    spec:
      containers:
        - name: postgres
          image: postgres:15
          ports: [{ containerPort: 5432 }]
          envFrom:
            - secretRef: { name: db-secret }
          env:
            - name: POSTGRES_DB
              valueFrom:
                configMapKeyRef: { name: app-config, key: DATABASE_NAME }
          volumeMounts:
            - name: pg-data
              mountPath: /var/lib/postgresql/data
      volumes:
        - name: pg-data
          persistentVolumeClaim: { claimName: pg-pvc }
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
spec:
  selector: { app: postgres }
  ports: [{ port: 5432, targetPort: 5432 }]
```

**Step 3：Redis（对应 `services.redis`）**

```yaml
# k8s/03-redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels: { app: redis }
  template:
    metadata:
      labels: { app: redis }
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports: [{ containerPort: 6379 }]
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
spec:
  selector: { app: redis }
  ports: [{ port: 6379, targetPort: 6379 }]
```

**Step 4：Web 应用（对应 `services.web`）**

```yaml
# k8s/04-web.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3                    # 比 Docker Compose 多了：3 副本！
  selector:
    matchLabels: { app: web }
  template:
    metadata:
      labels: { app: web }
    spec:
      containers:
        - name: web
          image: myapp:latest
          ports: [{ containerPort: 8000 }]
          envFrom:
            - configMapRef: { name: app-config }
          env:
            - name: DATABASE_URL
              value: "postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres-service:5432/mydb"
          envFrom:
            - secretRef: { name: db-secret }
---
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: NodePort               # 开发用 NodePort，生产用 Ingress
  selector: { app: web }
  ports:
    - port: 80
      targetPort: 8000
      nodePort: 30080
```
### 7.3 一键部署与验证

```bash
# 文件结构
# k8s/
# ├── 01-config.yaml      (ConfigMap + Secret)
# ├── 02-postgres.yaml    (PVC + Deployment + Service)
# ├── 03-redis.yaml       (Deployment + Service)
# └── 04-web.yaml         (Deployment + Service)

# 一键部署（按文件名顺序）
kubectl apply -f k8s/

# 等待所有 Pod 就绪
kubectl get pods -w
# NAME                       READY   STATUS    RESTARTS   AGE
# postgres-xxx               1/1     Running   0          45s
# redis-xxx                  1/1     Running   0          45s
# web-app-xxx                1/1     Running   0          45s
# web-app-yyy                1/1     Running   0          45s
# web-app-zzz                1/1     Running   0          45s

# 验证服务
kubectl get svc
# NAME               TYPE        CLUSTER-IP      PORT(S)
# postgres-service   ClusterIP   10.96.0.105     5432/TCP
# redis-service      ClusterIP   10.96.0.106     6379/TCP
# web-service        NodePort    10.96.0.107     80:30080/TCP

# 访问应用
curl http://localhost:30080
```

**Docker Compose vs K8s 终极对照：**

| 操作 | Docker Compose | Kubernetes |
|:---|:---|:---|
| 启动 | `docker-compose up -d` | `kubectl apply -f k8s/` |
| 查看状态 | `docker-compose ps` | `kubectl get pods` |
| 查看日志 | `docker-compose logs web` | `kubectl logs deploy/web-app` |
| 扩容 | `--scale web=3`（无负载均衡） | `kubectl scale deploy web-app --replicas=5` |
| 更新 | `docker-compose pull && up -d` | `kubectl set image deploy/web-app web=myapp:v2` |
| 停止 | `docker-compose down` | `kubectl delete -f k8s/` |
| 进入容器 | `docker-compose exec web bash` | `kubectl exec -it deploy/web-app -- bash` |

> 💡 **迁移后你获得了什么？** 相比 Docker Compose：① 3 个 Web 副本 + 自动负载均衡 ② Pod 挂了自动重建 ③ `kubectl set image` 滚动更新零停服 ④ 随时扩到 100 个副本。代价是 YAML 多了不少——这就是下一章 Helm 要解决的问题。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **迁移顺序** | 配置 → 数据库 → 缓存 → Web 应用，按依赖从底向上 |
| **environment → ConfigMap/Secret** | 明文配置用 ConfigMap，密码用 Secret |
| **volumes → PVC** | Docker named volume 变成 PersistentVolumeClaim |
| **ports → Service** | 端口映射变成 Service（ClusterIP/NodePort） |
| **depends_on → 不需要** | K8s 用 Service DNS 自动发现，无需控制启动顺序 |

---

## 8. Helm：K8s 的包管理器

第 7 章迁移完你可能发现了——一个简单的三服务应用就写了 4 个 YAML 文件、200+ 行。更痛苦的是：开发、测试、生产三个环境只有几个值不同，却要维护三份几乎一样的 YAML。Helm 就是来解决这个问题的。

### 8.1 YAML 地狱：为什么需要 Helm

```
没有 Helm 的痛苦：

  ❌ 问题 1：YAML 太多
  ═══════════════════════════════════
  一个应用 = ConfigMap + Secret + PVC + Deployment + Service
  → 5 个资源 × N 个服务 = 几十个 YAML 文件
  → 改个镜像版本要找到正确的文件和位置
  
  ❌ 问题 2：环境差异管理
  ═══════════════════════════════════
  开发：replicas: 1, image: myapp:dev
  测试：replicas: 2, image: myapp:test
  生产：replicas: 5, image: myapp:v2.1.0
  → 三份几乎一样的 YAML，只有几个值不同
  → 改一处忘改别处 = 线上事故
  
  ❌ 问题 3：没有版本管理
  ═══════════════════════════════════
  上线后发现 bug 要回滚
  → kubectl apply 的哪个版本？YAML 没有版本概念
  → 只能手动找 Git 历史，改回来，再 apply
```

**Helm 是什么？**

```
一句话：Helm 是 K8s 的 apt / brew / npm

  apt install nginx     →  安装 Nginx（帮你处理依赖和配置）
  helm install my-db bitnami/postgresql  →  在 K8s 里安装 PostgreSQL

  核心概念：
  ═══════════════════════════════════
  Chart      = 一个"安装包"（模板化的 YAML 集合）
  Release    = 一次安装（同一个 Chart 可以装多次）
  Repository = Chart 仓库（类似 apt source / npm registry）
  values.yaml = 配置参数（不同环境用不同的 values）
```

| 概念 | 类比 | 说明 |
|:---|:---|:---|
| **Chart** | npm package | 模板化的 K8s YAML 集合 |
| **Release** | npm install 的结果 | 一次具体的部署实例 |
| **values.yaml** | .env 文件 | 可配置的参数（replicas, image 等） |
| **Repository** | npm registry | Chart 的存储和共享平台 |

### 8.2 Chart 结构与 values.yaml 参数化

```
Chart 的目录结构：

  mychart/
  ├── Chart.yaml              # Chart 元信息（名称、版本）
  ├── values.yaml             # 默认参数值
  ├── templates/              # K8s YAML 模板
  │   ├── deployment.yaml     # Deployment 模板
  │   ├── service.yaml        # Service 模板
  │   ├── configmap.yaml      # ConfigMap 模板
  │   └── _helpers.tpl        # 公共模板函数
  └── charts/                 # 子 Chart（依赖）
```

**values.yaml（参数化配置）：**

```yaml
# values.yaml - 默认值
replicaCount: 1
image:
  repository: myapp
  tag: latest
service:
  type: ClusterIP
  port: 80
database:
  host: postgres-service
  port: 5432
```

**模板示例（用 `<span v-pre>&#123;&#123;  .Values.xxx  &#125;&#125;</span>` 引用参数）：**

::: v-pre
```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: &#123;&#123; .Release.Name &#125;&#125;-web    # Release 名称 + 后缀
spec:
  replicas: &#123;&#123; .Values.replicaCount &#125;&#125;
  selector:
    matchLabels:
      app: &#123;&#123; .Release.Name &#125;&#125;
  template:
    metadata:
      labels:
        app: &#123;&#123; .Release.Name &#125;&#125;
    spec:
      containers:
        - name: web
          image: "&#123;&#123; .Values.image.repository &#125;&#125;:&#123;&#123; .Values.image.tag &#125;&#125;"
          ports:
            - containerPort: 8000
```
:::

**多环境部署：**

```bash
# 开发环境（用默认 values.yaml）
helm install my-app ./mychart

# 生产环境（用 values-prod.yaml 覆盖）
helm install my-app ./mychart -f values-prod.yaml

# 或直接命令行覆盖单个值
helm install my-app ./mychart --set replicaCount=5 --set image.tag=v2.1.0
```

**Helm 常用命令：**

| 命令 | 功能 |
|:---|:---|
| `helm install <名称> <chart>` | 安装 Chart |
| `helm upgrade <名称> <chart>` | 升级（更新配置或版本） |
| `helm rollback <名称> <版本号>` | 回滚到指定版本 |
| `helm list` | 查看所有 Release |
| `helm history <名称>` | 查看 Release 历史版本 |
| `helm uninstall <名称>` | 卸载 |
| `helm template <chart>` | 只渲染模板不安装（调试用） |

> 💡 **`helm template` 是调试神器**——它只渲染 YAML 输出到终端，不真正部署。写完模板先 `helm template` 看看生成的 YAML 对不对，再 `helm install`。
### 8.3 实战：用 Helm 部署 PostgreSQL 和 Redis

不用自己写 YAML——社区已经有现成的 Chart。**Bitnami** 是最大的社区 Chart 仓库。

```bash
# 安装 Helm（Mac）
brew install helm

# 添加 Bitnami 仓库
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 一条命令部署 PostgreSQL！
helm install my-db bitnami/postgresql \
  --set auth.postgresPassword=password123 \
  --set auth.database=mydb \
  --set primary.persistence.size=5Gi

# 一条命令部署 Redis！
helm install my-cache bitnami/redis \
  --set auth.enabled=false \
  --set master.persistence.size=1Gi
```

```bash
# 查看部署的 Release
helm list
# NAME       NAMESPACE   REVISION   UPDATED                   STATUS     CHART
# my-db      default     1          2026-04-12 08:00:00       deployed   postgresql-15.x
# my-cache   default     1          2026-04-12 08:00:30       deployed   redis-19.x

# 升级（改参数）
helm upgrade my-db bitnami/postgresql \
  --set primary.persistence.size=20Gi

# 回滚到上一个版本
helm rollback my-db 1

# 查看历史
helm history my-db
# REVISION   UPDATED                    STATUS       DESCRIPTION
# 1          2026-04-12 08:00:00        superseded   Install complete
# 2          2026-04-12 09:00:00        deployed     Upgrade complete
```

**对比：手写 YAML vs Helm**

| 方面 | 手写 YAML | Helm Chart |
|:---|:---|:---|
| PostgreSQL 部署 | 80+ 行 YAML | 1 条命令 |
| 参数修改 | 找文件、改 YAML、apply | `--set` 或改 values.yaml |
| 版本管理 | 靠 Git | Helm 自带版本号 + 回滚 |
| 回滚 | 手动找旧 YAML | `helm rollback` |
| 生产级配置 | 自己写（容易遗漏） | 社区 Chart 已考虑（备份、HA、监控） |

> 💡 **务实建议**：中间件（数据库、Redis、消息队列）用社区 Chart 部署——它们经过了大量生产验证。你自己的业务应用才需要写自定义 Chart。不要重复造轮子。

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **YAML 地狱** | 文件多、环境差异靠复制、回滚靠 Git 考古 |
| **Chart** | 模板化的 YAML 集合，一个"K8s 安装包" |
| **values.yaml** | Chart 的参数文件，不同环境用不同 values |
| **helm template** | 只渲染不部署，调试利器 |
| **社区 Chart** | Bitnami 等提供的中间件 Chart，一条命令部署 |

---

## 9. 日常运维：调试、扩缩容、滚动更新

K8s 部署好了，日常最花时间的是运维——查日志、排故障、扩缩容、发版回滚。这章是你的"K8s 运维手册"。

### 9.1 kubectl 速查：20 个最常用命令

**查看资源：**

| 命令 | 功能 |
|:---|:---|
| `kubectl get pods` | 查看所有 Pod |
| `kubectl get pods -o wide` | 查看 Pod + 所在节点、IP |
| `kubectl get all` | 查看所有资源（Pod/Service/Deployment） |
| `kubectl get pods -w` | 实时监听 Pod 状态变化 |
| `kubectl get pods -n kube-system` | 查看指定命名空间的 Pod |

**调试排查：**

| 命令 | 功能 |
|:---|:---|
| `kubectl logs <pod名>` | 查看 Pod 日志 |
| `kubectl logs <pod名> -f` | 实时跟踪日志（tail -f） |
| `kubectl logs <pod名> --previous` | 查看崩溃前的日志 |
| `kubectl describe pod <pod名>` | 查看 Pod 详情和事件 |
| `kubectl exec -it <pod名> -- bash` | 进入 Pod 执行命令 |
| `kubectl get events --sort-by='.lastTimestamp'` | 查看集群事件（按时间排序） |

**操作管理：**

| 命令 | 功能 |
|:---|:---|
| `kubectl apply -f <文件>` | 创建/更新资源 |
| `kubectl delete -f <文件>` | 删除资源 |
| `kubectl scale deploy <名> --replicas=N` | 扩缩容 |
| `kubectl set image deploy/<名> <容器>=<镜像>` | 更新镜像 |
| `kubectl rollout status deploy/<名>` | 查看滚动更新进度 |
| `kubectl rollout undo deploy/<名>` | 回滚 |
| `kubectl port-forward svc/<名> 8080:80` | 端口转发到本地 |

**快捷技巧：**

```bash
# 缩写：pod=po, service=svc, deployment=deploy
kubectl get po         # 等于 kubectl get pods
kubectl get svc        # 等于 kubectl get services
kubectl get deploy     # 等于 kubectl get deployments

# 设置别名（加到 ~/.zshrc）
alias k=kubectl
alias kgp='kubectl get pods'
alias kl='kubectl logs'
```

### 9.2 故障排查：Pod 起不来怎么办

```
Pod 排查决策树：

  kubectl get pods → 看 STATUS 列
       │
       ├── ImagePullBackOff
       │   → 镜像拉不下来
       │   → 检查：镜像名拼错？私有仓库没配 imagePullSecret？网络问题？
       │   → kubectl describe pod <名> → 看 Events 里的错误信息
       │
       ├── CrashLoopBackOff
       │   → 容器启动后立即崩溃，反复重启
       │   → kubectl logs <名> --previous → 看崩溃前的日志
       │   → 常见原因：启动命令错误、缺少环境变量、数据库连不上
       │
       ├── Pending
       │   → Pod 还没被调度到节点上
       │   → kubectl describe pod <名> → 看 Events
       │   → 常见原因：节点资源不足、PVC 未绑定、节点有污点
       │
       ├── CreateContainerConfigError
       │   → 容器配置有误
       │   → 常见原因：引用的 ConfigMap/Secret 不存在
       │   → kubectl describe pod <名> → 看具体哪个 ConfigMap 找不到
       │
       └── Running 但服务不正常
           → Pod 在跑但请求失败
           → kubectl logs <名> -f → 看实时日志
           → kubectl exec -it <名> -- curl localhost:8000/health
           → 检查 Service selector 是否匹配 Pod label
```

**排查三板斧（按顺序执行）：**

```bash
# 第一步：看 Pod 状态
kubectl get pods
# STATUS 不是 Running？往下查

# 第二步：看 Pod 事件
kubectl describe pod <pod名>
# 滚到最下面的 Events 部分 → 错误原因在这里

# 第三步：看容器日志
kubectl logs <pod名>
kubectl logs <pod名> --previous   # 如果容器已崩溃
```

> 💡 **90% 的问题用 `describe` + `logs` 就能定位**。`describe` 告诉你"K8s 层面出了什么问题"（调度失败、拉镜像失败），`logs` 告诉你"应用层面出了什么问题"（启动报错、连不上数据库）。
### 9.3 扩缩容与滚动更新

**手动扩缩容：**

```bash
# 扩容到 5 个副本
kubectl scale deployment web-app --replicas=5

# 缩容到 2 个副本
kubectl scale deployment web-app --replicas=2
```

**自动扩缩容（HPA - Horizontal Pod Autoscaler）：**

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2               # 最少 2 个
  maxReplicas: 10              # 最多 10 个
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70  # CPU 使用率 > 70% 就扩容
```

```bash
# 或命令行快速创建
kubectl autoscale deployment web-app --min=2 --max=10 --cpu-percent=70

# 查看 HPA 状态
kubectl get hpa
# NAME      REFERENCE        TARGETS   MINPODS   MAXPODS   REPLICAS
# web-hpa   Deployment/web   45%/70%   2         10        3
```

**滚动更新（零停机发版）：**

```bash
# 更新镜像 → 自动触发滚动更新
kubectl set image deployment/web-app web=myapp:v2

# 查看进度
kubectl rollout status deployment/web-app
# Waiting for deployment "web-app" rollout to finish:
# 2 out of 3 new replicas have been updated...
# deployment "web-app" successfully rolled out

# 回滚到上一个版本
kubectl rollout undo deployment/web-app

# 回滚到指定版本
kubectl rollout undo deployment/web-app --to-revision=2

# 查看历史
kubectl rollout history deployment/web-app
```

```
滚动更新过程（默认策略）：

  maxSurge: 25%        → 更新时最多多出 25% 的 Pod
  maxUnavailable: 25%  → 更新时最多有 25% 的 Pod 不可用

  3 副本的更新过程：
  ═══════════════════════════════════
  Step 1: 创建 1 个新 Pod (v2)      → 总共 4 个 Pod (3×v1 + 1×v2)
  Step 2: 新 Pod Ready → 删 1 个旧  → 总共 3 个 Pod (2×v1 + 1×v2)
  Step 3: 创建 1 个新 Pod (v2)      → 总共 4 个 Pod (2×v1 + 2×v2)
  Step 4: 新 Pod Ready → 删 1 个旧  → 总共 3 个 Pod (1×v1 + 2×v2)
  Step 5: 重复...                   → 总共 3 个 Pod (0×v1 + 3×v2) ✅
```

> 💡 **HPA 前提**：Pod 必须设置 `resources.requests`（第 10 章），否则 HPA 无法计算 CPU 使用百分比。

**第 9 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **排查三板斧** | get pods → describe pod → logs，解决 90% 问题 |
| **CrashLoopBackOff** | 容器反复崩溃，用 `logs --previous` 看崩溃前日志 |
| **HPA** | 根据 CPU/内存自动扩缩 Pod 数量 |
| **滚动更新** | 逐步替换旧 Pod，全程不停服 |
| **kubectl 别名** | `alias k=kubectl`，日常效率翻倍 |

---

## 10. 生产环境最佳实践

能 `kubectl apply` 启动 Pod 不代表能上生产。生产环境需要健康检查、资源限制、安全隔离等一系列"防护网"。这章是你的"上线前检查清单"。

### 10.1 健康检查：Liveness、Readiness、Startup Probe

```
三种 Probe 的区别：

  Liveness Probe（存活检查）
  ═══════════════════════════════════
  问题：容器还活着吗？
  失败后果：K8s 杀掉容器并重启
  场景：应用死锁、无限循环、卡住不响应
  
  Readiness Probe（就绪检查）
  ═══════════════════════════════════
  问题：容器准备好接收流量了吗？
  失败后果：从 Service 的负载均衡中移除（不杀不重启）
  场景：应用还在启动、正在预热缓存、临时过载
  
  Startup Probe（启动检查）
  ═══════════════════════════════════
  问题：容器启动完成了吗？
  失败后果：K8s 杀掉容器并重启
  场景：启动特别慢的应用（加载大模型/预热数据）
  → 启动成功后才开始 Liveness 和 Readiness 检查
```

**完整 YAML 示例：**

```yaml
spec:
  containers:
    - name: web
      image: myapp:v1
      ports: [{ containerPort: 8000 }]
      
      # 存活检查：每 10 秒检查一次 /health
      livenessProbe:
        httpGet:
          path: /health
          port: 8000
        initialDelaySeconds: 15    # 启动后 15 秒开始检查
        periodSeconds: 10          # 每 10 秒检查一次
        failureThreshold: 3        # 连续 3 次失败 → 重启容器
      
      # 就绪检查：每 5 秒检查一次 /ready
      readinessProbe:
        httpGet:
          path: /ready
          port: 8000
        initialDelaySeconds: 5
        periodSeconds: 5
        failureThreshold: 3        # 连续 3 次失败 → 从 Service 移除
      
      # 启动检查：给慢启动应用足够的时间
      startupProbe:
        httpGet:
          path: /health
          port: 8000
        failureThreshold: 30       # 30 × 10 = 300 秒的启动时间
        periodSeconds: 10
```

| Probe | 失败后果 | 典型路径 | 必须配？ |
|:---|:---|:---|:---|
| **Liveness** | 重启容器 | `/health` | ✅ 强烈推荐 |
| **Readiness** | 移出负载均衡 | `/ready` | ✅ 强烈推荐 |
| **Startup** | 重启容器 | `/health` | 慢启动应用才需要 |

> 💡 **常见错误**：只配 Liveness 不配 Readiness → 容器启动中就收到流量 → 用户看到 502。一定要同时配！Readiness 在滚动更新时尤其重要——新 Pod 没 Ready 前不会接收流量。

### 10.2 资源管理：Requests、Limits 与 OOM 防护

```
Requests 和 Limits 的区别：

  Requests（请求）= "我至少需要这些资源"
  ═══════════════════════════════════
  → Scheduler 根据 Requests 决定把 Pod 调度到哪个 Node
  → 保证 Pod 至少能用到这些资源
  → 设太高 → 浪费资源（Node 明明有空间，Scheduler 认为没有）
  → 设太低 → 可能影响性能
  
  Limits（限制）= "你最多只能用这些"
  ═══════════════════════════════════
  → CPU 超限 → 被限速（throttle），不会被杀
  → 内存超限 → OOM Kill！容器被杀并重启
  → 设太高 → 一个 Pod 抢占所有资源
  → 不设 → 一个 Pod 可能吃掉整个 Node 的内存
```

**YAML 示例：**

```yaml
spec:
  containers:
    - name: web
      image: myapp:v1
      resources:
        requests:
          cpu: "100m"          # 100 毫核 = 0.1 核
          memory: "128Mi"      # 128 MiB
        limits:
          cpu: "500m"          # 最多用 0.5 核
          memory: "256Mi"      # 最多用 256 MiB（超了就 OOM Kill）
```

**资源单位说明：**

| 单位 | 含义 | 例子 |
|:---|:---|:---|
| `1` (CPU) | 1 个 vCPU 核心 | `cpu: "1"` = 独占 1 核 |
| `100m` (CPU) | 100 毫核 = 0.1 核 | 轻量级 Web 应用够用 |
| `Mi` (内存) | MiB（1024 × 1024 字节） | `128Mi` = 128 MiB |
| `Gi` (内存) | GiB | `1Gi` = 1 GiB |

```
不配 Requests/Limits 的后果：

  ═══════════════════════════════════
  Pod-A（没设 Limits）内存泄漏 → 吃掉 Node 全部内存
  → Node 上其他 Pod 全部被 OOM Kill
  → 连锁反应：多个服务同时挂掉
  → 运维人员凌晨 3 点被叫起来 😱
  
  所以：生产环境必须设 Requests 和 Limits！
```

> 💡 **推荐策略**：Requests 设为应用正常运行的资源量，Limits 设为 Requests 的 1.5-2 倍。先不设 Limits 跑一段时间，用 `kubectl top pods` 观察实际使用量，再据此设置。
### 10.3 生产部署清单：从开发到上线的 10 个检查项

每次上线前跑一遍这个清单：

| # | 检查项 | 确认问题 | 对应章节 |
|:---|:---|:---|:---|
| 1 | **镜像标签** | 使用了具体版本号（v2.1.0），不是 latest？ | 第 3 章 |
| 2 | **Replicas** | 至少 2 个副本（避免单点故障）？ | 第 3 章 |
| 3 | **Resources** | 设置了 requests 和 limits？ | 第 10 章 |
| 4 | **Liveness Probe** | 配置了存活检查？ | 第 10 章 |
| 5 | **Readiness Probe** | 配置了就绪检查？ | 第 10 章 |
| 6 | **ConfigMap/Secret** | 配置外置，没有硬编码在镜像里？ | 第 4 章 |
| 7 | **PVC** | 有状态服务挂载了持久卷？ | 第 5 章 |
| 8 | **Ingress + TLS** | HTTPS 证书配置正确？ | 第 6 章 |
| 9 | **HPA** | Web 服务配置了自动扩缩容？ | 第 9 章 |
| 10 | **回滚计划** | 知道怎么回滚（helm rollback / kubectl rollout undo）？ | 第 8/9 章 |

**Namespace 隔离（附加建议）：**

```bash
# 不同环境用不同 Namespace
kubectl create namespace dev
kubectl create namespace staging
kubectl create namespace production

# 部署到指定 Namespace
kubectl apply -f k8s/ -n production

# 默认 Namespace 设为 production
kubectl config set-context --current --namespace=production
```

> 💡 **永远不要用 `latest` 标签上生产**。`latest` 不是一个固定版本——今天是 v2.1，明天可能变成 v2.2。用具体的版本号（`myapp:v2.1.0`）或 Git commit SHA（`myapp:abc1234`），确保每次部署的都是你测试过的那个版本。

**第 10 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Liveness Probe** | 检测容器是否存活，失败则重启 |
| **Readiness Probe** | 检测容器是否就绪，失败则移出负载均衡 |
| **Requests** | Pod 的最低资源保证，影响调度决策 |
| **Limits** | Pod 的资源上限，内存超限 = OOM Kill |
| **latest 标签** | 永远不要用在生产环境，用具体版本号 |

---

## 全书总结

恭喜你读到这里！回顾一下从 Docker Compose 到 K8s 的完整路径：

```
你的 K8s 知识体系：

  第 1 章  为什么需要 K8s ─── Docker 单机局限 → K8s 核心承诺
  第 2 章  架构全景 ─────── Control Plane + Worker Node
  第 3 章  核心三件套 ───── Pod + Deployment + Service
  第 4 章  配置管理 ─────── ConfigMap + Secret
  第 5 章  存储持久化 ───── PV + PVC + StorageClass
  第 6 章  网络与入口 ───── Service 类型 + Ingress
  第 7 章  迁移实战 ─────── docker-compose → K8s YAML（全书核心）
  第 8 章  Helm ──────── Chart + values.yaml + 社区 Chart
  第 9 章  日常运维 ─────── kubectl 速查 + 排障 + 扩缩容
  第 10 章 生产实践 ─────── Probe + Resources + 上线清单
```

**K8s 的核心思维模型——记住这三条就够了：**

1. **声明式**：你写"我要什么"（YAML），K8s 负责"怎么做到"
2. **调谐循环**：Controller 不断把现实状态拉向期望状态
3. **Label 是胶水**：Deployment 找 Pod、Service 找 Pod、全靠 Label

剩下的，就是在实践中反复使用这些概念，直到它们变成你的肌肉记忆。祝你 K8s 之旅顺利！🚀
