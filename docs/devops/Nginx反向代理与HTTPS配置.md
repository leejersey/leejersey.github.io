# Nginx 反向代理与 HTTPS 配置

> 从零开始掌握 Nginx：反向代理、负载均衡、SSL/TLS 证书配置、安全加固——覆盖开发到生产环境的完整实践。

---

## 1. Nginx 基础：安装与核心概念

Nginx（发音 "engine-x"）是全球最流行的 Web 服务器和反向代理服务器，以高并发、低内存著称。全世界超过 30% 的网站在使用它。

> 💡 **本章目标**：安装 Nginx、理解进程模型和配置语法，能用命令行管理 Nginx 的生命周期。

### 1.1 安装 Nginx（Ubuntu/macOS/Docker）

**Ubuntu / Debian：**

```bash
sudo apt update
sudo apt install nginx -y

# 验证安装
nginx -v
# nginx version: nginx/1.24.0

# 启动并设置开机自启
sudo systemctl start nginx
sudo systemctl enable nginx

# 浏览器访问 http://服务器IP → 看到 "Welcome to nginx!" 页面
```

**macOS（Homebrew）：**

```bash
brew install nginx

# 启动
brew services start nginx

# 默认端口 8080（macOS 的 80 端口需要 root 权限）
# 浏览器访问 http://localhost:8080
```

**Docker（推荐用于本地测试）：**

```bash
# 一行命令跑起来
docker run -d -p 80:80 --name nginx nginx:alpine

# 挂载自定义配置和静态文件
docker run -d -p 80:80 \
  -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v $(pwd)/html:/usr/share/nginx/html:ro \
  --name nginx nginx:alpine
```

**安装后的默认目录（Ubuntu）：**

| 路径 | 说明 |
|:---|:---|
| `/etc/nginx/nginx.conf` | 主配置文件 |
| `/etc/nginx/conf.d/` | 自定义站点配置目录 |
| `/etc/nginx/sites-available/` | 可用站点配置 |
| `/etc/nginx/sites-enabled/` | 已启用站点（符号链接） |
| `/usr/share/nginx/html/` | 默认静态文件目录 |
| `/var/log/nginx/` | 日志目录（access.log / error.log） |

### 1.2 核心概念：Master-Worker 进程模型

Nginx 采用**一个 Master 进程 + 多个 Worker 进程**的架构：

```
                    ┌──────────────┐
                    │  Master 进程  │  ← 读取配置、管理 Worker
                    └──────┬───────┘
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Worker 1 │ │ Worker 2 │ │ Worker 3 │  ← 处理请求（事件驱动）
        └──────────┘ └──────────┘ └──────────┘
```

**Master 进程**：读取配置文件、启动/停止 Worker、监听信号（reload/stop）。不处理请求。

**Worker 进程**：实际处理客户端请求。每个 Worker 使用**事件驱动**（epoll/kqueue），一个 Worker 可以同时处理数千个并发连接——这就是 Nginx 高并发的秘密。

```nginx
# nginx.conf
worker_processes auto;  # 建议设为 auto（自动等于 CPU 核心数）
```

> 💡 **为什么不用多线程？** 线程切换有开销。Nginx 的 Worker 用事件驱动（非阻塞 I/O），单进程就能处理海量并发，比"一个请求一个线程"的模型高效得多。

### 1.3 配置文件结构：main → events → http → server → location

Nginx 的配置文件是**嵌套的块结构**，理解层级关系是一切配置的基础：

```nginx
# /etc/nginx/nginx.conf — 完整结构示例

# -------- main 上下文（全局配置）--------
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /run/nginx.pid;

# -------- events 上下文（连接配置）--------
events {
    worker_connections 1024;    # 每个 Worker 最多处理 1024 个并发连接
    multi_accept on;            # 一次接受多个连接
}

# -------- http 上下文（HTTP 服务配置）--------
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;

    # -------- server 上下文（虚拟主机 = 一个网站）--------
    server {
        listen 80;
        server_name example.com;

        # -------- location 上下文（URL 路径匹配）--------
        location / {
            root /var/www/html;
            index index.html;
        }

        location /api/ {
            proxy_pass http://localhost:3000;
        }
    }

    # 可以有多个 server 块（多个网站）
    server {
        listen 80;
        server_name blog.example.com;
        # ...
    }

    # 引入其他配置文件
    include /etc/nginx/conf.d/*.conf;
}
```

**层级关系速记：**

```
main          → 全局设置（worker 数量、日志、PID）
├── events    → 连接处理（并发连接数）
└── http      → HTTP 服务总配置
    ├── server    → 一个虚拟主机（一个域名/网站）
    │   ├── location /       → 匹配 URL 路径 /
    │   └── location /api/   → 匹配 URL 路径 /api/
    └── server    → 另一个虚拟主机
```

> 💡 **实际项目中的惯例**：主配置 `nginx.conf` 只写全局配置，每个网站单独一个文件放在 `conf.d/` 目录下（如 `conf.d/mysite.conf`），通过 `include` 引入。

### 1.4 常用命令：启动、停止、重载、测试配置

**核心命令速查：**

```bash
# 测试配置是否正确（改完配置必须先测试！）
sudo nginx -t
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# 重新加载配置（不中断正在处理的请求）
sudo nginx -s reload

# 快速停止
sudo nginx -s stop

# 优雅停止（等现有请求处理完再退出）
sudo nginx -s quit

# 查看 Nginx 进程
ps aux | grep nginx
```

**systemctl 方式（Ubuntu/CentOS）：**

```bash
sudo systemctl start nginx      # 启动
sudo systemctl stop nginx       # 停止
sudo systemctl restart nginx    # 重启（会中断连接，慎用）
sudo systemctl reload nginx     # 重载配置（推荐）
sudo systemctl status nginx     # 查看状态
sudo systemctl enable nginx     # 开机自启
```

> 💡 **修改配置的标准流程**：`编辑配置` → `nginx -t 测试` → `nginx -s reload 重载`。永远不要跳过 `nginx -t`，否则一个语法错误就可能让整个网站宕机。

---

## 2. 静态文件服务与虚拟主机

Nginx 最基本的能力就是托管静态文件——在你上反向代理之前，先把这个搞明白。

### 2.1 托管静态网站：root vs alias

**最简单的静态网站：**

```nginx
# /etc/nginx/conf.d/mysite.conf
server {
    listen 80;
    server_name example.com;

    root /var/www/mysite;    # 静态文件的根目录
    index index.html;

    location / {
        try_files $uri $uri/ =404;  # 找文件 → 找目录 → 返回 404
    }
}
```

**`root` vs `alias` — 最常搞混的两个指令：**

```nginx
# root：把 location 路径拼接到 root 后面
location /images/ {
    root /var/www;
}
# 请求 /images/logo.png → 查找 /var/www/images/logo.png
#                                     ▲ location 路径被拼上去了

# alias：用 alias 路径完全替换 location 路径
location /images/ {
    alias /var/www/static/;
}
# 请求 /images/logo.png → 查找 /var/www/static/logo.png
#                                     ▲ location 路径被替换掉了
```

| 指令 | 行为 | 适用场景 |
|:---|:---|:---|
| `root` | URL 路径**拼接**到 root 后面 | 文件目录结构和 URL 结构一致 |
| `alias` | URL 路径**替换**为 alias 路径 | 文件目录结构和 URL 结构不一致 |

> 💡 **常见坑**：`alias` 后面的路径必须以 `/` 结尾，否则路径拼接会出错。

### 2.2 虚拟主机：单台服务器多域名（server_name）

一台服务器可以通过 `server_name` 托管多个网站——Nginx 根据请求的 `Host` 头来决定用哪个 `server` 块。

```nginx
# 主站
server {
    listen 80;
    server_name example.com www.example.com;
    root /var/www/main;
}

# 博客子域名
server {
    listen 80;
    server_name blog.example.com;
    root /var/www/blog;
}

# API 子域名 → 反向代理到后端
server {
    listen 80;
    server_name api.example.com;
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

**`server_name` 的匹配规则（优先级从高到低）：**

| 类型 | 示例 | 说明 |
|:---|:---|:---|
| 精确匹配 | `server_name example.com;` | 最高优先级 |
| 前缀通配符 | `server_name *.example.com;` | 匹配所有子域名 |
| 后缀通配符 | `server_name example.*;` | 匹配所有顶级域 |
| 正则匹配 | `server_name ~^(.+)\.example\.com$;` | 最灵活但最慢 |

**兜底配置——`default_server`：**

```nginx
# 当没有任何 server_name 匹配时，走这个（比如直接用 IP 访问）
server {
    listen 80 default_server;
    server_name _;           # _ 是约定的"不匹配任何域名"的写法
    return 444;              # 直接关闭连接（防止 IP 直接访问）
}
```

### 2.3 默认页面、目录浏览、自定义错误页

**默认页面——`index` 指令：**

```nginx
server {
    listen 80;
    server_name example.com;
    root /var/www/mysite;

    # 按顺序查找：index.html → index.htm
    index index.html index.htm;
}
```

**目录浏览——`autoindex`（文件下载服务器常用）：**

```nginx
location /downloads/ {
    alias /var/www/files/;
    autoindex on;               # 开启目录浏览
    autoindex_exact_size off;   # 显示人类可读的文件大小（KB/MB）
    autoindex_localtime on;     # 显示本地时间而非 GMT
}
```

**自定义错误页——`error_page`：**

```nginx
server {
    listen 80;
    server_name example.com;
    root /var/www/mysite;

    # 自定义 404 和 50x 错误页面
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;

    # 错误页面的位置
    location = /404.html {
        root /var/www/error-pages;
        internal;    # 只能内部重定向访问，不能直接通过 URL 访问
    }

    location = /50x.html {
        root /var/www/error-pages;
        internal;
    }
}
```

> 💡 **`internal` 关键字**确保用户不能通过 `http://example.com/404.html` 直接访问错误页面，只有 Nginx 内部触发错误时才会显示。

---

## 3. 反向代理：核心原理与配置

**反向代理是 Nginx 最重要的功能**——让 Nginx 接收请求，转发给后端应用（Node.js、Python、Go 等），再把响应返回给客户端。

### 3.1 什么是反向代理？正向代理 vs 反向代理

```
正向代理（如 VPN、科学上网）：
  客户端 → [代理服务器] → 目标服务器
  ▲ 客户端知道代理的存在，主动配置代理
  ▲ 隐藏客户端身份

反向代理（如 Nginx）：
  客户端 → [Nginx] → 后端服务器
  ▲ 客户端不知道后端的存在，以为在和 Nginx 通信
  ▲ 隐藏后端服务器身份
```

**反向代理的作用：**

| 作用 | 说明 |
|:---|:---|
| 隐藏后端 | 客户端只知道 Nginx 的 IP，不知道后端在哪 |
| 负载均衡 | 分发请求到多台后端 |
| SSL 终止 | Nginx 处理 HTTPS，后端只需处理 HTTP |
| 缓存加速 | Nginx 缓存静态资源，减轻后端压力 |
| 统一入口 | 多个微服务共用一个域名，按路径分发 |

### 3.2 proxy_pass 基本配置：代理到后端应用

**最基础的反向代理：**

```nginx
server {
    listen 80;
    server_name example.com;

    # 所有请求都转发到后端的 3000 端口
    location / {
        proxy_pass http://localhost:3000;
    }
}
```

**按路径分发到不同后端：**

```nginx
server {
    listen 80;
    server_name example.com;

    # 前端：Next.js（3000 端口）
    location / {
        proxy_pass http://localhost:3000;
    }

    # API：FastAPI（8000 端口）
    location /api/ {
        proxy_pass http://localhost:8000;
    }

    # 管理后台：独立应用（3001 端口）
    location /admin/ {
        proxy_pass http://localhost:3001;
    }
}
```

**⚠️ `proxy_pass` 末尾有没有 `/` 的区别：**

```nginx
# 不带 /：location 路径会拼接到后端 URL
location /api/ {
    proxy_pass http://localhost:8000;
}
# 请求 /api/users → 后端收到 /api/users

# 带 /：location 路径会被替换掉
location /api/ {
    proxy_pass http://localhost:8000/;
}
# 请求 /api/users → 后端收到 /users（/api/ 被去掉了）
```

> 💡 **实际项目中**：如果后端应用的路由没有 `/api/` 前缀，就用带 `/` 的写法去掉前缀。如果后端也定义了 `/api/` 路由，就不带 `/`。

### 3.3 请求头转发：Host、X-Real-IP、X-Forwarded-For

经过 Nginx 代理后，后端收到的请求会丢失原始客户端信息。需要手动转发关键 Headers。

**标准代理头配置模板（几乎每个项目都要用）：**

```nginx
location / {
    proxy_pass http://localhost:3000;

    # ---- 必须配置的代理头 ----
    proxy_set_header Host $host;                    # 原始域名
    proxy_set_header X-Real-IP $remote_addr;        # 客户端真实 IP
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;  # 完整的代理链 IP
    proxy_set_header X-Forwarded-Proto $scheme;     # 原始协议（http/https）
}
```

**每个 Header 的作用：**

| Header | 不设置时后端收到的 | 设置后后端收到的 |
|:---|:---|:---|
| `Host` | `localhost:3000`（代理目标地址） | `example.com`（用户访问的域名） |
| `X-Real-IP` | 无此头 | `203.0.113.50`（客户端 IP） |
| `X-Forwarded-For` | 无此头 | `203.0.113.50, 10.0.0.1`（代理链） |
| `X-Forwarded-Proto` | 无此头 | `https`（原始协议） |

> 💡 **为什么 `X-Forwarded-Proto` 很重要？** 如果 Nginx 负责 SSL 终止（HTTPS），后端收到的是 HTTP 请求。没有这个头，后端就不知道用户实际用的是 HTTPS，生成的链接可能是 `http://` 开头的。

**推荐做法——抽成公共文件复用：**

```nginx
# /etc/nginx/proxy_params（公共代理头）
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

```nginx
# 在各站点配置中直接引入
location / {
    proxy_pass http://localhost:3000;
    include proxy_params;    # ← 一行搞定
}
```

### 3.4 代理 WebSocket 连接

WebSocket 需要从 HTTP 协议**升级**（Upgrade），Nginx 需要特殊配置才能正确代理。

```nginx
# WebSocket 代理配置
location /ws/ {
    proxy_pass http://localhost:3000;
    proxy_http_version 1.1;                        # WebSocket 需要 HTTP/1.1
    proxy_set_header Upgrade $http_upgrade;        # 传递 Upgrade 头
    proxy_set_header Connection "upgrade";         # 告诉代理保持连接
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    # WebSocket 连接可能长时间空闲，增大超时
    proxy_read_timeout 86400s;    # 24 小时
    proxy_send_timeout 86400s;
}
```

**同时支持 HTTP 和 WebSocket 的通用方案：**

```nginx
# 用 map 动态判断是否是 WebSocket 请求
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;  # ← 动态值
        include proxy_params;
    }
}
```

> 💡 **Socket.io 使用者注意**：Socket.io 默认先用 HTTP 轮询再升级到 WebSocket。上面的 `map` 方案可以同时处理两种情况。

### 3.5 代理缓冲与超时控制

**代理缓冲（Buffering）：**

Nginx 默认会把后端的响应先**缓冲到内存/磁盘**，再一次性发给客户端。这对大多数场景是好的，但对 SSE（Server-Sent Events）等流式响应需要关闭。

```nginx
location / {
    proxy_pass http://localhost:3000;

    # 默认行为：开启缓冲（适合普通 API）
    proxy_buffering on;
    proxy_buffer_size 4k;          # 响应头缓冲区
    proxy_buffers 8 4k;            # 响应体缓冲区（8 个 4KB 块）
}

location /api/stream/ {
    proxy_pass http://localhost:3000;

    # SSE / 流式响应：关闭缓冲
    proxy_buffering off;           # ← 数据直接透传给客户端
    proxy_cache off;
}
```

**超时参数：**

```nginx
location / {
    proxy_pass http://localhost:3000;

    proxy_connect_timeout 5s;     # 连接后端的超时（默认 60s，太长了）
    proxy_read_timeout 60s;       # 等待后端响应的超时
    proxy_send_timeout 60s;       # 向后端发送请求的超时
}
```

| 超时参数 | 含义 | 建议值 |
|:---|:---|:---|
| `proxy_connect_timeout` | 和后端建立 TCP 连接的超时 | 5-10s |
| `proxy_read_timeout` | 等待后端返回内容的超时 | 60s（长任务可加大） |
| `proxy_send_timeout` | 向后端发送数据的超时 | 60s |

**大文件上传——调大 `client_max_body_size`：**

```nginx
server {
    # 默认只允许 1MB 的请求体，上传大文件会报 413 错误
    client_max_body_size 100m;   # 允许上传 100MB 的文件
}
```

> 💡 **413 Request Entity Too Large** 是最常见的 Nginx 错误之一。如果用户上传文件报 413，第一反应就是加大 `client_max_body_size`。

---

## 4. 负载均衡：多后端分流

当一台后端扛不住流量时，就需要多台后端来分担。Nginx 的 `upstream` 模块让负载均衡变得极其简单。

### 4.1 upstream 配置与负载均衡算法

**基本配置：**

```nginx
# 定义一组后端服务器
upstream backend {
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
    server 10.0.0.3:3000;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://backend;    # ← 引用 upstream 名称
        include proxy_params;
    }
}
```

**四种负载均衡算法：**

```nginx
# 1. 轮询（默认）— 依次分发
upstream backend {
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
    # 请求 1 → .1，请求 2 → .2，请求 3 → .1 ...
}

# 2. 权重 — 按比例分发（性能好的机器分更多）
upstream backend {
    server 10.0.0.1:3000 weight=3;    # 60% 的请求
    server 10.0.0.2:3000 weight=2;    # 40% 的请求
}

# 3. IP Hash — 同一 IP 始终打到同一后端（解决 Session 问题）
upstream backend {
    ip_hash;
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
}

# 4. Least Connections — 分发到当前连接数最少的后端
upstream backend {
    least_conn;
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
}
```

| 算法 | 适用场景 | 特点 |
|:---|:---|:---|
| 轮询 | 后端性能一致 | 最简单，默认选择 |
| 权重 | 后端性能不一致 | 性能好的机器分更多流量 |
| IP Hash | 需要 Session 保持 | 同一用户始终到同一后端 |
| Least Conn | 请求处理时间差异大 | 避免慢请求堆积在同一后端 |

### 4.2 健康检查与故障转移

Nginx 开源版支持**被动健康检查**——当请求后端失败时，自动标记为不可用。

```nginx
upstream backend {
    server 10.0.0.1:3000 max_fails=3 fail_timeout=30s;
    server 10.0.0.2:3000 max_fails=3 fail_timeout=30s;
    server 10.0.0.3:3000 backup;    # 备用：只有其他全挂了才启用
}
```

**参数说明：**

| 参数 | 含义 | 默认值 |
|:---|:---|:---|
| `max_fails` | 连续失败多少次标记为不可用 | 1 |
| `fail_timeout` | 标记不可用后，多久再重试 | 10s |
| `backup` | 备用节点，只有其他节点全部不可用时才启用 | — |
| `down` | 永久标记为下线（手动维护时使用） | — |

```nginx
# 配合 proxy_next_upstream：请求失败时自动尝试下一个后端
location / {
    proxy_pass http://backend;
    proxy_next_upstream error timeout http_502 http_503;
    proxy_next_upstream_tries 2;    # 最多重试 2 次
}
```

> 💡 **Nginx Plus（付费版）** 支持主动健康检查——定期向后端发请求探测存活状态，不需要等用户请求失败。开源版需要用第三方模块（如 `ngx_http_healthcheck_module`）实现。

### 4.3 Session 保持策略

多后端场景下，用户的 Session 可能存在后端 A 的内存中，下一个请求被转发到后端 B 就找不到 Session 了。

**三种解决方案：**

```
方案 1：ip_hash（最简单）
  → 同一 IP 始终路由到同一后端
  → 缺点：CDN/代理后面所有用户可能共享 IP

方案 2：sticky cookie（Nginx Plus）
  → 第一次请求时 Nginx 设置一个 cookie 标识后端
  → 后续请求根据 cookie 路由
  → 缺点：需要 Nginx Plus 付费版

方案 3：共享 Session 存储（推荐 ✅）
  → Session 存到 Redis/数据库，所有后端共享
  → 任何后端都能读取 Session，不依赖路由策略
  → 这是生产环境的标准做法
```

| 方案 | 复杂度 | 可靠性 | 适用场景 |
|:---|:---|:---|:---|
| `ip_hash` | 低 | 中 | 小项目快速解决 |
| Sticky Cookie | 中 | 高 | Nginx Plus 用户 |
| Redis Session | 中 | 高 | 生产环境推荐 |

> 💡 **现代应用的趋势**：用 JWT（无状态 Token）完全替代 Session。后端不需要存储会话状态，天然支持多后端，不需要任何 Session 保持策略。

---

## 5. HTTPS 配置：SSL/TLS 证书

2024 年，没有 HTTPS 的网站浏览器会直接标记为"不安全"。HTTPS 不再是可选项，而是**必须**。

### 5.1 HTTPS 原理：TLS 握手、证书链、加密套件

**TLS 握手过程（简化版）：**

```
客户端                                         服务器（Nginx）
   │                                              │
   │── 1. ClientHello（支持的协议版本、密码套件）──→│
   │                                              │
   │←─ 2. ServerHello + 证书（包含公钥）──────────│
   │                                              │
   │── 3. 用公钥加密"预主密钥"发给服务器 ──────→│
   │                                              │
   │   双方用预主密钥推导出"会话密钥"              │
   │                                              │
   │←→ 4. 用会话密钥对称加密通信（高效）────────→│
```

**证书链：** 浏览器信任的 CA（证书颁发机构）→ 中间证书 → 你的网站证书。三者形成信任链，缺一不可。

**关键术语速查：**

| 术语 | 含义 |
|:---|:---|
| SSL | 过时的加密协议（SSL 3.0 已有漏洞，不要用） |
| TLS | SSL 的继任者（TLS 1.2 / 1.3 是当前标准） |
| 证书（cert） | `.pem` / `.crt` 文件，包含域名和公钥 |
| 私钥（key） | `.key` 文件，绝对不能泄露 |
| CA | 颁发证书的权威机构（Let's Encrypt 是免费 CA） |
| 加密套件 | 加密算法的组合（如 `ECDHE-RSA-AES256-GCM-SHA384`） |

### 5.2 Let's Encrypt 免费证书申请（Certbot 自动化）

Let's Encrypt 是免费、自动化的证书颁发机构。**Certbot** 是最常用的客户端工具。

**安装 Certbot：**

```bash
# Ubuntu
sudo apt install certbot python3-certbot-nginx -y
```

**一键申请证书 + 自动配置 Nginx：**

```bash
# Certbot 会自动修改 Nginx 配置，加上 SSL 相关指令
sudo certbot --nginx -d example.com -d www.example.com

# 交互流程：
# 1. 输入邮箱（用于续期通知）
# 2. 同意服务条款
# 3. 选择是否重定向 HTTP → HTTPS（选 2 自动重定向）
```

**Certbot 做了什么：**

```
1. 向 Let's Encrypt 证明你拥有这个域名（HTTP-01 挑战）
2. 下载证书文件到 /etc/letsencrypt/live/example.com/
3. 自动修改 Nginx 配置，添加 SSL 指令
4. 重载 Nginx
```

**证书文件位置：**

| 文件 | 路径 | 说明 |
|:---|:---|:---|
| 证书 | `/etc/letsencrypt/live/example.com/fullchain.pem` | 网站证书 + 中间证书 |
| 私钥 | `/etc/letsencrypt/live/example.com/privkey.pem` | 私钥（chmod 600） |

> 💡 **Let's Encrypt 证书有效期 90 天**，Certbot 安装时会自动设置定时续期任务。第 5.5 节详细介绍。

### 5.3 Nginx SSL 配置详解：证书路径、协议版本、密码套件

**生产级 HTTPS 配置模板：**

```nginx
server {
    listen 443 ssl http2;         # 同时启用 SSL 和 HTTP/2
    server_name example.com;

    # ---- 证书文件 ----
    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # ---- 协议版本（只允许 TLS 1.2 和 1.3）----
    ssl_protocols TLSv1.2 TLSv1.3;

    # ---- 加密套件（优先使用服务端的偏好）----
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';

    # ---- SSL Session 复用（减少握手开销）----
    ssl_session_cache shared:SSL:10m;   # 10MB 共享缓存
    ssl_session_timeout 1d;             # Session 有效期 1 天
    ssl_session_tickets off;            # 关闭 Session Tickets（更安全）

    # ---- OCSP Stapling（加速证书验证）----
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;

    # ---- 网站配置 ----
    root /var/www/mysite;
    location / {
        try_files $uri $uri/ =404;
    }
}
```

**各配置项解释：**

| 配置 | 作用 | 推荐值 |
|:---|:---|:---|
| `ssl_protocols` | 允许的 TLS 版本 | `TLSv1.2 TLSv1.3`（禁用旧版本） |
| `ssl_prefer_server_ciphers` | 优先使用服务端选择的加密套件 | `on` |
| `ssl_session_cache` | 缓存 TLS Session，避免重复握手 | `shared:SSL:10m` |
| `ssl_stapling` | Nginx 替客户端查验证书状态 | `on`（加速 HTTPS 连接） |
| `http2` | 启用 HTTP/2 多路复用 | 始终开启（需要 HTTPS） |

> 💡 **TLS 1.3** 比 1.2 更快（握手从 2 次往返减少到 1 次）、更安全。现代浏览器都支持 TLS 1.3。

### 5.4 HTTP 自动跳转 HTTPS（301 重定向）

用户可能直接输入 `http://example.com` 访问你的网站，需要自动跳转到 HTTPS：

**标准做法——独立的 80 端口 server 块：**

```nginx
# HTTP → HTTPS 重定向（80 端口）
server {
    listen 80;
    server_name example.com www.example.com;

    # 所有 HTTP 请求 301 重定向到 HTTPS
    return 301 https://$host$request_uri;
}

# HTTPS 主配置（443 端口）
server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # ... 其他 SSL 配置和网站配置
}
```

**www 跳转到裸域名（或反过来）：**

```nginx
# www.example.com → example.com
server {
    listen 443 ssl http2;
    server_name www.example.com;
    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    return 301 https://example.com$request_uri;
}
```

> 💡 **用 `return 301` 而不是 `rewrite`**。`return` 更高效（不需要正则匹配），而且 301 告诉搜索引擎"永久跳转"，有利于 SEO。

### 5.5 证书自动续期与监控

Let's Encrypt 证书有效期只有 90 天，**必须**设置自动续期。

**Certbot 自动续期（通常安装时已自动配置）：**

```bash
# 检查定时任务是否已设置
sudo systemctl list-timers | grep certbot

# 如果没有，手动添加 cron 任务
sudo crontab -e
# 每天凌晨 2 点检查续期（只有到期前 30 天才会实际续期）
0 2 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

**手动测试续期流程：**

```bash
# 模拟续期（不会真的续期，只是测试流程是否正确）
sudo certbot renew --dry-run

# 输出 "Congratulations, all simulated renewals succeeded" 表示 OK
```

**证书过期监控：**

```bash
# 查看证书到期时间
sudo certbot certificates

# 输出：
# Certificate Name: example.com
# Expiry Date: 2024-06-15 (VALID: 62 days)
```

```bash
# 一行命令检查证书到期天数（可放到监控脚本中）
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates
```

> 💡 **证书过期是最常见的线上事故之一**。建议在监控系统（Uptime Robot / Prometheus）中加上 SSL 证书到期检查，提前 14 天报警。

---

## 6. 安全加固与性能优化

HTTPS 只是安全的第一步。生产环境还需要安全头、限流、压缩等配置来抵御攻击和提升性能。

### 6.1 安全 Headers：HSTS、X-Frame-Options、CSP、X-Content-Type-Options

**生产级安全头模板：**

```nginx
server {
    # ... SSL 配置 ...

    # HSTS — 强制浏览器只用 HTTPS 访问（包含子域名）
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 防止被嵌入 iframe（防点击劫持）
    add_header X-Frame-Options "SAMEORIGIN" always;

    # 防止浏览器猜测文件类型（防 MIME 嗅探攻击）
    add_header X-Content-Type-Options "nosniff" always;

    # XSS 过滤
    add_header X-XSS-Protection "1; mode=block" always;

    # 控制 Referrer 信息泄露
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # CSP — 内容安全策略（限制脚本/样式/图片的加载来源）
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;" always;
}
```

| Header | 防御什么 | 推荐值 |
|:---|:---|:---|
| `Strict-Transport-Security` | SSL 剥离攻击 | `max-age=31536000` |
| `X-Frame-Options` | 点击劫持 | `SAMEORIGIN` |
| `X-Content-Type-Options` | MIME 嗅探 | `nosniff` |
| `Content-Security-Policy` | XSS、数据注入 | 按需定制 |

### 6.2 限流与限速：limit_req / limit_conn

防止恶意请求、暴力破解、CC 攻击。

**请求速率限制（`limit_req`）：**

```nginx
# 在 http 块中定义限流区域
http {
    # 每个 IP 每秒最多 10 个请求，共享内存 10MB
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
}

server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        # burst=20：允许突发 20 个请求（排队）
        # nodelay：突发请求不排队，直接处理

        proxy_pass http://localhost:8000;
    }
}
```

**并发连接限制（`limit_conn`）：**

```nginx
http {
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;
}

server {
    location /downloads/ {
        limit_conn conn_limit 5;    # 每个 IP 最多 5 个并发连接
        limit_rate 500k;            # 每个连接限速 500KB/s
    }
}
```

> 💡 **限流触发时默认返回 503**。可以自定义：`limit_req_status 429;`（429 = Too Many Requests，语义更准确）。

### 6.3 IP 黑白名单：allow / deny

**保护管理后台——只允许公司 IP 访问：**

```nginx
location /admin/ {
    allow 203.0.113.0/24;     # 公司网络
    allow 10.0.0.0/8;          # 内网
    deny all;                  # 拒绝其他所有 IP

    proxy_pass http://localhost:3001;
}
```

**屏蔽已知恶意 IP：**

```nginx
# /etc/nginx/conf.d/blocklist.conf
deny 45.33.32.0/24;
deny 198.51.100.0/24;
# ... 更多恶意 IP
```

```nginx
# 在 server 或 http 块中引入
include /etc/nginx/conf.d/blocklist.conf;
```

> 💡 **执行顺序**：`allow` 和 `deny` 按配置顺序依次匹配，**第一个匹配的规则生效**。所以白名单写法是 `allow` 放前面、`deny all` 放最后。

### 6.4 Gzip / Brotli 压缩

压缩可以减少 60-80% 的传输体积，**显著加快页面加载速度**。

```nginx
http {
    # ---- Gzip 压缩 ----
    gzip on;
    gzip_vary on;                    # 告诉 CDN 区分压缩/未压缩版本
    gzip_min_length 1024;            # 小于 1KB 的不压缩（压缩后可能更大）
    gzip_comp_level 5;               # 压缩级别 1-9（5 是性价比最高的）
    gzip_types
        text/plain
        text/css
        text/javascript
        application/javascript
        application/json
        application/xml
        image/svg+xml;
    gzip_proxied any;                # 代理请求也压缩
}
```

| 参数 | 推荐值 | 说明 |
|:---|:---|:---|
| `gzip_comp_level` | 5 | 1-3 太低、7-9 CPU 开销大但效果提升小 |
| `gzip_min_length` | 1024 | 小文件不值得压缩 |
| `gzip_types` | 见上方 | **不要**压缩图片/视频（已经压缩过了） |

> 💡 **Brotli** 比 Gzip 压缩率更高（约提升 15-25%），但需要编译安装 `ngx_brotli` 模块。如果用 Cloudflare CDN，它会自动帮你做 Brotli。

### 6.5 静态资源缓存：expires / Cache-Control

让浏览器缓存 JS/CSS/图片等静态资源，**减少重复下载**。

```nginx
server {
    # 图片/字体：缓存 1 年（文件名带 hash 的前提下）
    location ~* \.(jpg|jpeg|png|gif|webp|svg|ico|woff2|woff|ttf)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;    # 静态文件不记日志（减少磁盘 IO）
    }

    # JS/CSS：缓存 30 天
    location ~* \.(js|css)$ {
        expires 30d;
        add_header Cache-Control "public";
    }

    # HTML：不缓存（保证用户看到最新内容）
    location ~* \.html$ {
        expires -1;
        add_header Cache-Control "no-cache";
    }
}
```

| 文件类型 | 缓存策略 | 说明 |
|:---|:---|:---|
| 图片/字体 | `expires 1y + immutable` | 文件名带 hash 可长期缓存 |
| JS/CSS | `expires 30d` | 构建工具通常会生成 hash 文件名 |
| HTML | `no-cache` | 每次请求都检查是否有更新 |
| API 响应 | `no-store` | 动态数据不缓存 |

> 💡 **`immutable` 关键字**告诉浏览器"这个文件永远不会变"——连 304 协商缓存的请求都省了。前提是你的构建工具（Webpack/Vite）会在文件名中加 hash（如 `main.a1b2c3.js`）。

---

## 7. 实战场景：常见部署架构

把前面学到的所有知识串起来——反向代理 + HTTPS + 安全头 + 压缩 + 缓存，形成完整的生产配置。

### 7.1 Nginx + Next.js（Node.js）部署

```nginx
# /etc/nginx/conf.d/nextjs.conf
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    # SSL
    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # 压缩
    gzip on;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;
    gzip_min_length 1024;

    # Next.js 静态资源（_next/static 路径带 hash，长期缓存）
    location /_next/static/ {
        proxy_pass http://localhost:3000;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # 其他所有请求转发给 Next.js
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    client_max_body_size 50m;
}
```

### 7.2 Nginx + FastAPI（Python）部署

```nginx
# /etc/nginx/conf.d/fastapi.conf
upstream fastapi_app {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;    # 多个 Uvicorn worker
}

server {
    listen 80;
    server_name api.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate     /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # 安全头
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # API 请求
    location / {
        proxy_pass http://fastapi_app;
        include proxy_params;

        # 文件上传限制
        client_max_body_size 100m;
    }

    # SSE 流式响应（AI 聊天等场景）
    location /api/stream/ {
        proxy_pass http://fastapi_app;
        include proxy_params;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }

    # 静态文件（FastAPI 挂载的 /static 目录）
    location /static/ {
        alias /var/www/fastapi/static/;
        expires 30d;
        access_log off;
    }
}
```

### 7.3 Nginx + Docker Compose 多服务架构

在 Docker 环境中，Nginx 也运行在容器里，通过**容器名**访问后端服务。

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend

  frontend:
    build: ./frontend
    expose:
      - "3000"    # 只在 Docker 网络内部暴露，不映射到宿主机

  backend:
    build: ./backend
    expose:
      - "8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/mydb
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

```nginx
# nginx/conf.d/default.conf
# 注意：用容器名（frontend/backend）代替 localhost
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://frontend:3000;    # ← Docker 容器名
        include /etc/nginx/proxy_params;
    }

    location /api/ {
        proxy_pass http://backend:8000;     # ← Docker 容器名
        include /etc/nginx/proxy_params;
    }
}
```

> 💡 **Docker 网络中用容器名代替 IP**。Docker Compose 默认创建一个内部网络，所有服务通过容器名互相访问。

### 7.4 多域名 + 多应用的统一入口配置

一台 Nginx 同时管理多个域名和多个应用——这是最常见的实际场景。

```
一台服务器，一个 Nginx：
  example.com         → Next.js（3000 端口）
  api.example.com     → FastAPI（8000 端口）
  admin.example.com   → 管理后台（3001 端口）
  blog.example.com    → 静态博客（文件目录）
```

**文件组织：**

```
/etc/nginx/
├── nginx.conf                     # 主配置（全局 Gzip、日志格式）
├── proxy_params                   # 公共代理头
└── conf.d/
    ├── example.com.conf           # 主站
    ├── api.example.com.conf       # API
    ├── admin.example.com.conf     # 管理后台
    └── blog.example.com.conf      # 博客
```

```nginx
# /etc/nginx/conf.d/admin.example.com.conf
server {
    listen 443 ssl http2;
    server_name admin.example.com;

    ssl_certificate     /etc/letsencrypt/live/admin.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.example.com/privkey.pem;

    # 管理后台——限制 IP 访问
    allow 203.0.113.0/24;
    deny all;

    location / {
        proxy_pass http://localhost:3001;
        include proxy_params;
    }
}
```

> 💡 **通配符证书**可以一个证书覆盖所有子域名：`certbot --nginx -d example.com -d *.example.com`，需要用 DNS-01 验证方式。

---

## 8. 运维与排错

配完了不等于万事大吉。出问题时，快速定位和修复才是真本事。

### 8.1 日志分析：access.log / error.log

**日志位置和格式：**

```bash
# 默认路径
/var/log/nginx/access.log    # 访问日志（每个请求一行）
/var/log/nginx/error.log     # 错误日志（配置错误、后端超时等）
```

**自定义日志格式（推荐）：**

```nginx
http {
    log_format main '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    '$request_time $upstream_response_time';

    access_log /var/log/nginx/access.log main;
}
# $request_time = 从收到请求到返回响应的总时间
# $upstream_response_time = 后端处理时间（排查慢请求必备）
```

**常用日志分析命令：**

```bash
# 查看实时日志
tail -f /var/log/nginx/access.log

# 统计各状态码数量
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# 找出最慢的 10 个请求
awk '{print $NF, $7}' access.log | sort -rn | head -10

# 统计每个 IP 的请求数（排查 CC 攻击）
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -20
```

### 8.2 常见错误排查：502/504/413/403

| 错误码 | 含义 | 常见原因 | 解决方案 |
|:---|:---|:---|:---|
| **502** | Bad Gateway | 后端服务没启动 / 崩溃 | 检查后端进程：`systemctl status xxx` |
| **504** | Gateway Timeout | 后端处理太慢 | 加大 `proxy_read_timeout` |
| **413** | Request Entity Too Large | 上传文件超限 | 加大 `client_max_body_size` |
| **403** | Forbidden | 文件权限不足 / IP 被 deny | 检查 `allow/deny` 和文件权限 |
| **499** | Client Closed Request | 客户端主动断开 | 检查是否超时后用户放弃 |

**502 排查清单：**

```bash
# 1. 后端进程在运行吗？
systemctl status your-app
# 或
docker ps

# 2. 端口在监听吗？
ss -tlnp | grep 3000

# 3. Nginx 能连上后端吗？
curl -I http://localhost:3000

# 4. 查看 error.log 的具体错误
tail -20 /var/log/nginx/error.log
```

### 8.3 配置调试技巧与在线检测工具

**调试命令：**

```bash
# 测试配置语法（必须养成习惯！）
sudo nginx -t

# 查看完整的生效配置（包含所有 include 的文件）
sudo nginx -T

# 查看编译的模块列表
nginx -V 2>&1 | tr ' ' '\n' | grep module
```

**在线检测工具：**

| 工具 | 用途 | 地址 |
|:---|:---|:---|
| SSL Labs | SSL/TLS 安全评分 | ssllabs.com/ssltest |
| SecurityHeaders | 安全头检测 | securityheaders.com |
| HTTP/2 Test | 检测 HTTP/2 是否生效 | tools.keycdn.com/http2-test |
| PageSpeed Insights | 整体性能评估 | pagespeed.web.dev |

> 💡 **目标**：SSL Labs 评分达到 **A+**（需要正确配置 HSTS + TLS 1.2/1.3 + 强加密套件）。SecurityHeaders 评分达到 **A**。

### 8.4 Nginx 平滑升级与零停机部署

**`reload` 的原理——为什么不会中断请求：**

```
nginx -s reload 执行流程：
  1. Master 进程读取新配置
  2. 配置验证通过 → 启动新的 Worker 进程
  3. 旧 Worker 进程停止接受新请求
  4. 旧 Worker 处理完当前请求后退出
  → 全程无中断！
```

**二进制热升级（升级 Nginx 版本）：**

```bash
# 1. 下载并编译新版本 Nginx
# 2. 用新的二进制文件替换旧的
sudo cp /usr/sbin/nginx /usr/sbin/nginx.old
sudo cp objs/nginx /usr/sbin/nginx

# 3. 发送 USR2 信号——启动新版本的 Master
sudo kill -USR2 $(cat /run/nginx.pid)

# 4. 现在新旧 Master 共存，确认新版本正常后
sudo kill -QUIT $(cat /run/nginx.pid.oldbin)

# 5. 如果新版本有问题，回滚
sudo kill -HUP $(cat /run/nginx.pid.oldbin)
sudo kill -QUIT $(cat /run/nginx.pid)
```

**更简单的方式——用包管理器升级：**

```bash
# Ubuntu
sudo apt update && sudo apt upgrade nginx

# 包管理器会自动处理 reload，通常不会中断服务
```

> 💡 **生产环境黄金法则**：永远用 `reload` 而不是 `restart`。`restart` 会先停止再启动，中间有几秒的服务中断。`reload` 是热加载，零中断。
