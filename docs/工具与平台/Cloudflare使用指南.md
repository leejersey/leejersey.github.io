# Cloudflare 使用指南：从域名到部署的完整实战

> 面向独立开发者和小团队，系统掌握 Cloudflare 免费层核心能力——域名管理、DNS、CDN 加速、SSL 证书、Workers 边缘计算、Pages 前端部署、R2 对象存储、安全防护。

---

## 1. Cloudflare 全景认知

很多人第一次听到 Cloudflare 是因为"CDN 加速"或者"免费 SSL 证书"。但 Cloudflare 早已不只是一个 CDN——它是一个**覆盖了域名、DNS、安全、计算、存储、部署的全栈云平台**，而且免费层的能力强到离谱。

### 1.1 Cloudflare 不只是 CDN：产品矩阵一览

Cloudflare 的产品线可以分为以下几个大类：

```
┌─────────────────────────────────────────────────────┐
│                  Cloudflare 产品矩阵                  │
├───────────────┬─────────────────────────────────────┤
│  基础设施      │ DNS、域名注册（Registrar）            │
│  安全防护      │ DDoS 防护、WAF、Bot 管理、SSL/TLS    │
│  性能加速      │ CDN 缓存、Argo、图片优化              │
│  边缘计算      │ Workers（无服务器函数）、Durable Objects│
│  前端部署      │ Pages（类似 Vercel）                  │
│  存储服务      │ R2（对象存储）、KV（键值存储）、D1（数据库）│
│  零信任安全    │ Access、Tunnel、WARP                  │
└───────────────┴─────────────────────────────────────┘
```

**和其他云服务商的定位对比：**

| 能力 | Cloudflare | AWS | Vercel |
|---|---|---|---|
| CDN + 安全 | ✅ 核心强项，免费 | CloudFront（付费） | 内置但功能少 |
| 边缘计算 | Workers（免费 10 万次/天）| Lambda@Edge（贵）| Edge Functions |
| 前端部署 | Pages（免费无限带宽）| Amplify | ✅ 核心强项 |
| 对象存储 | R2（零出站费）| S3（出站收费）| ❌ 无 |
| 域名注册 | ✅ 成本价，不赚差价 | Route 53（贵）| ❌ 无 |
| 数据库 | D1（SQLite 边缘版，Beta）| DynamoDB / RDS | ❌ 无 |

> 💡 **Cloudflare 的独特定位**：它不是一个传统的云服务器提供商（不提供 VPS/EC2），而是一个**边缘网络平台**——你的代码和内容跑在全球 300+ 个边缘节点上，离用户最近。

### 1.2 免费层 vs 付费层：独立开发者能白嫖到什么程度

Cloudflare 的免费层在业界出了名的慷慨。以下是免费层的核心能力：

| 产品 | 免费额度 | 付费起步价 |
|---|---|---|
| **DNS 管理** | ✅ 完全免费，无限查询 | — |
| **CDN 缓存** | ✅ 免费，无限带宽 | — |
| **DDoS 防护** | ✅ 免费，自动缓解 | — |
| **SSL 证书** | ✅ 免费自动签发 | — |
| **Workers** | 10 万次请求/天 | $5/月（1000 万次） |
| **Pages** | 无限站点、无限带宽、500 次构建/月 | $20/月（5000 次构建） |
| **R2 存储** | 10 GB 存储 + 100 万次 A 类操作/月 | $0.015/GB/月 |
| **KV 存储** | 10 万次读取/天 | $5/月 |
| **WAF 规则** | 5 条自定义规则 | $20/月（更多规则） |

```
免费层能做到的事：
  ✅ 托管一个域名，DNS + CDN + HTTPS 全免费
  ✅ 部署前端项目（React/Vue/Next.js），无限带宽
  ✅ 用 Workers 跑轻量级后端 API（每天 10 万次请求）
  ✅ 用 R2 存 10GB 文件（图片、文档等）
  ✅ 自动 DDoS 防护 + 基础 WAF 安全
```

> 💡 对于个人项目和小型 SaaS，**免费层足够用**。绝大多数独立开发者永远不会超出免费额度。

### 1.3 核心概念：代理（Proxy）、边缘网络、PoP 节点

在深入使用 Cloudflare 之前，理解三个核心概念会让后续内容事半功倍。

#### 反向代理（Reverse Proxy）

Cloudflare 的核心工作模式是**反向代理**——它站在用户和你的服务器之间：

```
没有 Cloudflare：
  用户 ──────────────────→ 你的服务器（源站）
                           IP: 1.2.3.4（暴露）

使用 Cloudflare 后：
  用户 ──→ Cloudflare 边缘节点 ──→ 你的服务器（源站）
           ↑ 代理层                  IP: 被隐藏
           │
           ├─ 缓存静态资源（不回源）
           ├─ 过滤恶意请求（WAF/DDoS）
           ├─ 自动加 SSL 证书
           └─ 就近响应（CDN 加速）
```

用户访问的实际上是 Cloudflare 的节点，而不是你的真实服务器。这带来三个好处：**安全**（隐藏源站 IP）、**性能**（CDN 缓存）、**可靠**（DDoS 防护）。

#### 边缘网络与 PoP 节点

Cloudflare 在全球 300+ 个城市部署了**PoP（Point of Presence，接入点）**节点：

```
用户在北京 → 命中 Cloudflare 北京节点 → 直接返回缓存内容（快）
用户在纽约 → 命中 Cloudflare 纽约节点 → 直接返回缓存内容（快）

传统方式：
用户在北京 → 跨太平洋 → 你在美国的服务器 → 再跨太平洋回来（慢）
```

**边缘计算**（Workers）更进一步：你的代码直接运行在这些 PoP 节点上，不需要传统的中心化服务器。

#### 橙色云 vs 灰色云（代理 vs 仅 DNS）

在 Cloudflare 的 DNS 管理中，每条记录旁边有一个云朵图标：

```
☁️ 橙色（Proxied）  → 流量经过 Cloudflare 代理
                      ✅ 享受 CDN / WAF / DDoS / SSL 等全部功能
                      ✅ 隐藏源站 IP

☁️ 灰色（DNS Only） → 流量直连你的服务器
                      ❌ 不经过 Cloudflare，没有任何额外功能
                      ❌ 暴露源站 IP
```

> 💡 **默认开启橙色云**。只有在特殊场景（如邮件服务器 MX 记录、需要直连的 SSH）才用灰色云。

---

## 2. 账号注册与域名接入

使用 Cloudflare 的第一步是注册账号并把你的域名接入。这个过程不复杂，但有几个关键步骤容易踩坑——尤其是**更换 Nameserver**。

### 2.1 注册账号与控制台导览

#### 注册流程

1. 访问 [dash.cloudflare.com](https://dash.cloudflare.com/sign-up)
2. 输入邮箱和密码，完成注册
3. 验证邮箱（必须，否则部分功能受限）

> 💡 建议用**个人常用邮箱**注册，不要用临时邮箱。Cloudflare 的账号安全策略很严格，换邮箱和找回密码比较麻烦。注册后建议立即开启**双因素认证（2FA）**。

#### 控制台首页

注册完成后进入控制台（Dashboard），你会看到一个空的站点列表。首页的核心区域：

```
┌─────────────────────────────────────────────┐
│  Cloudflare Dashboard                        │
├─────────────────────────────────────────────┤
│                                              │
│  + Add a site          ← 添加站点的入口      │
│                                              │
│  ┌─────────────┐  ┌─────────────┐           │
│  │ example.com  │  │ myapp.dev   │           │
│  │ Active ✅    │  │ Active ✅    │           │
│  └─────────────┘  └─────────────┘           │
│                                              │
│  左侧栏：Workers / Pages / R2 等产品入口    │
│  右上角：账号设置、API Token 管理            │
└─────────────────────────────────────────────┘
```

### 2.2 添加站点：将已有域名接入 Cloudflare

这是最常见的场景——你已经在阿里云/腾讯云/Namecheap/GoDaddy 等平台注册了域名，现在要把它接入 Cloudflare。

#### 完整步骤

**Step 1：点击 "Add a site"，输入域名**

```
输入：example.com（不带 www，不带 https://）
```

**Step 2：选择套餐（选 Free）**

Cloudflare 会让你选套餐，直接选最下面的 **Free**，然后点 Continue。

**Step 3：Cloudflare 自动扫描 DNS 记录**

Cloudflare 会自动扫描你域名的现有 DNS 记录并导入。**仔细检查这一步**：

```
⚠️ 检查清单：
  ✅ A 记录（指向服务器 IP）是否正确导入
  ✅ CNAME 记录（如 www → example.com）是否存在
  ✅ MX 记录（邮箱服务）是否正确
  ✅ TXT 记录（SPF/DKIM 等邮件验证）是否正确

  ❌ 如果有遗漏，手动添加！DNS 记录丢失会导致网站或邮箱不可用
```

**Step 4：更换 Nameserver（最关键的一步）**

Cloudflare 会给你两个 Nameserver 地址，类似：

```
adam.ns.cloudflare.com
bella.ns.cloudflare.com
```

你需要去**域名注册商**（购买域名的地方）修改 Nameserver：

```
以阿里云为例：
  1. 登录阿里云域名控制台
  2. 找到你的域名 → 点击"管理"
  3. 找到"DNS 修改" → "修改 DNS 服务器"
  4. 删除原有的 DNS 服务器（如 dns1.hichina.com）
  5. 填入 Cloudflare 给的两个 Nameserver
  6. 保存

其他注册商操作类似，核心就是：
  把 DNS 服务器从 "原来的" 改成 "Cloudflare 给的"
```

**Step 5：等待生效**

Nameserver 更换后，需要等待全球 DNS 传播。通常：

| 时间 | 状态 |
|---|---|
| 几分钟 ~ 1 小时 | 大部分情况下生效 |
| 最长 24-48 小时 | 极端情况（部分 DNS 缓存较久） |

Cloudflare 会发邮件通知你站点是否激活成功。你也可以在控制台看到状态从 "Pending" 变成 "Active"。

> ⚠️ **Nameserver 更换期间网站仍然可以访问**，不会中断服务。因为 Cloudflare 已经导入了你原来的 DNS 记录。

### 2.3 在 Cloudflare 直接注册/转入域名（Registrar）

除了接入已有域名，Cloudflare 也可以直接**注册新域名**或**从其他注册商转入域名**。

#### 为什么在 Cloudflare 注册域名？

```
核心优势：成本价注册，不赚差价

其他注册商：
  .com 域名第一年 ¥9（促销）→ 续费 ¥69/年 → 第三年涨到 ¥79/年

Cloudflare Registrar：
  .com 域名 $9.15/年（≈ ¥65）→ 续费同样 $9.15/年 → 永远同价
  这就是 ICANN 的批发价，Cloudflare 不加任何利润
```

#### 注册新域名

控制台左侧栏 → **Domain Registration** → **Register Domain** → 搜索并购买。

#### 转入已有域名

条件：域名注册超过 60 天、已解锁、获取了转移码（EPP Code / Auth Code）。

```
步骤：
  1. 控制台 → Domain Registration → Transfer Domain
  2. 输入域名
  3. 填入从原注册商获取的转移码
  4. 支付一年续费费用（按成本价）
  5. 等待转移完成（通常 5-7 天）
```

> 💡 转入后 Nameserver 自动就是 Cloudflare 的，不需要再手动修改。

### 2.4 控制台核心功能区速览

当你的域名激活后，点击域名进入管理页面，左侧栏是所有功能入口：

| 功能区 | 作用 | 对应章节 |
|---|---|---|
| **Overview** | 站点概况、流量统计 | — |
| **DNS** | DNS 记录管理 | 第 3 章 |
| **SSL/TLS** | 证书和加密模式 | 第 4 章 |
| **Caching** | 缓存配置 | 第 5 章 |
| **Speed** | 性能优化选项 | 第 5 章 |
| **Security** | WAF、DDoS、Bot 管理 | 第 9 章 |
| **Rules** | 页面规则、缓存规则、重定向 | 第 5 章 |
| **Workers** | 边缘计算函数 | 第 7 章 |
| **Pages** | 前端项目部署 | 第 6 章 |
| **R2** | 对象存储 | 第 8 章 |

> 💡 不需要一次看完所有功能。按照本指南的顺序，遇到时再深入学习对应模块。

---

## 3. DNS 管理

域名接入 Cloudflare 后，DNS 管理就是你最常用的功能。所有的"域名指向哪里"都在这里配置。

### 3.1 DNS 基础回顾：A / CNAME / MX / TXT 都是什么

DNS（Domain Name System）的作用是把**人类能记住的域名**翻译成**机器需要的 IP 地址**。不同类型的 DNS 记录负责不同的事：

| 记录类型 | 作用 | 典型场景 | 示例 |
|---|---|---|---|
| **A** | 域名 → IPv4 地址 | 网站指向服务器 | `example.com → 1.2.3.4` |
| **AAAA** | 域名 → IPv6 地址 | IPv6 网站 | `example.com → 2001:db8::1` |
| **CNAME** | 域名 → 另一个域名 | www 跳转、CDN | `www → example.com` |
| **MX** | 邮件服务器指向 | 企业邮箱 | `example.com → mail.example.com` |
| **TXT** | 存储文本信息 | 域名验证、SPF 邮件防伪 | `v=spf1 include:...` |
| **NS** | 指定 DNS 服务器 | 已被 Cloudflare 接管 | `adam.ns.cloudflare.com` |
| **SRV** | 服务发现 | 特殊协议（如 SIP） | 较少用 |

**在 Cloudflare 中添加 DNS 记录：**

```
控制台 → 你的域名 → DNS → Records → + Add Record

填写：
  Type:    A（或 CNAME 等）
  Name:    @（代表根域名）或 www / api / blog 等子域名
  Content: 1.2.3.4（IP 地址或目标域名）
  Proxy:   ☁️ 橙色（推荐）或 灰色
  TTL:     Auto（代理模式下自动管理）
```

> 💡 **Name 填 `@` 表示根域名本身**（如 `example.com`）。填 `www` 表示 `www.example.com`，填 `api` 表示 `api.example.com`。

### 3.2 橙色云☁️ vs 灰色云：代理模式详解

第 1 章简单提到了橙色云和灰色云的区别。这里详细展开——这是 Cloudflare DNS 中**最重要的决策点**。

#### 详细对比

| | ☁️ 橙色（Proxied） | ☁️ 灰色（DNS Only） |
|---|---|---|
| **流量路径** | 用户 → CF 节点 → 源站 | 用户 → 直连源站 |
| **CDN 缓存** | ✅ 有 | ❌ 无 |
| **DDoS 防护** | ✅ 有 | ❌ 无 |
| **WAF 规则** | ✅ 有 | ❌ 无 |
| **SSL 证书** | ✅ CF 自动签发 | ❌ 需自行配置 |
| **源站 IP** | ✅ 隐藏 | ❌ 暴露 |
| **支持的端口** | 仅 HTTP/HTTPS 标准端口 | 所有端口 |
| **支持的协议** | HTTP / HTTPS / WebSocket | 任意协议（SSH、FTP 等） |

#### 什么时候必须用灰色云？

```
必须用灰色云的场景：
  ❌ MX 记录（邮件服务器）     → 邮件协议不走 HTTP
  ❌ SSH 直连（22 端口）       → Cloudflare 不代理 22 端口
  ❌ FTP 服务                  → 非 HTTP 协议
  ❌ 游戏服务器                → 自定义 TCP/UDP 端口
  ❌ 某些需要获取真实客户端 IP 的服务

其他场景一律用橙色云 ✅
```

#### 常见误区

```
❌ 误区："我的网站不需要 CDN，所以用灰色云"
✅ 正确：橙色云不只是 CDN，还包括安全防护和 SSL。即使不需要缓存，也应该用橙色云

❌ 误区："开了橙色云网站变慢了"
✅ 正确：如果服务器在国内且用户也在国内，走 Cloudflare 反而多了一跳。
         但安全收益通常大于微小的延迟增加
```

> 💡 **如果你的服务器在中国大陆、用户也在大陆**，橙色云可能增加延迟（因为 Cloudflare 在大陆没有节点）。这种情况下可以考虑灰色云 + 国内 CDN 的组合。

### 3.3 常见 DNS 配置实战

#### 场景 1：网站指向服务器

你有一台服务器 IP 是 `43.136.43.80`，要让 `example.com` 和 `www.example.com` 都指向它：

| Type | Name | Content | Proxy |
|---|---|---|---|
| A | `@` | `43.136.43.80` | ☁️ 橙色 |
| CNAME | `www` | `example.com` | ☁️ 橙色 |

> 💡 `www` 用 CNAME 指向根域名，而不是再写一条 A 记录。这样改 IP 时只需改一处。

#### 场景 2：API 子域名指向不同的服务器

前端部署在 Pages 上，后端 API 在另一台服务器：

| Type | Name | Content | Proxy |
|---|---|---|---|
| CNAME | `@` | `your-project.pages.dev` | ☁️ 橙色 |
| A | `api` | `43.136.43.80` | ☁️ 橙色 |

这样 `example.com` 走前端，`api.example.com` 走后端。

#### 场景 3：配置企业邮箱（如腾讯企业邮 / Google Workspace）

邮件服务需要 MX 记录，**必须用灰色云**：

| Type | Name | Content | Priority | Proxy |
|---|---|---|---|---|
| MX | `@` | `mx1.qq.com` | 5 | ☁️ 灰色 |
| MX | `@` | `mx2.qq.com` | 10 | ☁️ 灰色 |
| TXT | `@` | `v=spf1 include:spf.mail.qq.com ~all` | — | ☁️ 灰色 |

> ⚠️ MX 和 SPF（TXT）记录**不能开橙色云**，否则邮件收发会失败。

#### 场景 4：域名验证（Let's Encrypt / Google Search Console）

很多服务需要你证明"这个域名是你的"，通常要添加一条 TXT 记录：

| Type | Name | Content | Proxy |
|---|---|---|---|
| TXT | `@` | `google-site-verification=xxxx...` | ☁️ 灰色 |
| TXT | `_acme-challenge` | `yyy...` | ☁️ 灰色 |

#### 场景 5：重定向 www 到裸域（或反过来）

想让 `www.example.com` 自动跳转到 `example.com`？可以用 Cloudflare 的 **Redirect Rules**：

```
控制台 → Rules → Redirect Rules → Create Rule

条件：Hostname equals www.example.com
动作：Dynamic Redirect
  URL: concat("https://example.com", http.request.uri.path)
  Status Code: 301（永久重定向）
```

#### 场景 6：Cloudflare Pages 自定义域名

部署在 Pages 上的项目，绑定自定义域名：

| Type | Name | Content | Proxy |
|---|---|---|---|
| CNAME | `@` | `your-project.pages.dev` | ☁️ 橙色 |
| CNAME | `www` | `your-project.pages.dev` | ☁️ 橙色 |

> 💡 Pages 绑定自定义域名后，Cloudflare 会**自动签发 SSL 证书**，不需要手动配置。

### 3.4 子域名管理与通配符记录

#### 子域名命名规范

常见的子域名命名约定：

| 子域名 | 用途 |
|---|---|
| `www` | 网站主页（传统） |
| `api` | 后端 API 接口 |
| `app` | Web 应用 |
| `admin` | 管理后台 |
| `blog` | 博客 |
| `docs` | 文档站 |
| `staging` / `dev` | 测试/开发环境 |
| `cdn` / `static` | 静态资源 |

#### 通配符记录（Wildcard）

用 `*` 匹配**所有未单独配置的子域名**：

| Type | Name | Content | Proxy |
|---|---|---|---|
| A | `*` | `43.136.43.80` | ☁️ 灰色 |

```
通配符效果：
  api.example.com      → 有单独的 A 记录 → 走单独配置
  blog.example.com     → 没有单独配置 → 命中通配符 → 43.136.43.80
  anything.example.com → 没有单独配置 → 命中通配符 → 43.136.43.80
```

> ⚠️ **免费层的通配符记录不能开橙色云**（只能灰色）。需要橙色云代理通配符子域名，要升级到企业版或使用 Advanced Certificate Manager（$10/月）。

#### 多级子域名

Cloudflare 免费层**只支持一级子域名的代理**：

```
✅ api.example.com        → 一级子域名，可以开橙色云
❌ v2.api.example.com     → 二级子域名，免费层不能开橙色云

解决方案：
  1. 用短横线代替多级：v2-api.example.com ✅
  2. 升级到 Advanced Certificate Manager
```

---

## 4. SSL/TLS 证书与 HTTPS

HTTPS 不再是可选项——浏览器会把 HTTP 网站标记为"不安全"，搜索引擎也会降权。好消息是，Cloudflare 让 HTTPS 变成了**零配置**——但前提是你选对了 SSL 模式。

### 4.1 四种 SSL 模式：Off / Flexible / Full / Full (Strict)

这是 Cloudflare 最容易配错的设置，选错会导致**重定向循环**或**安全漏洞**。

```
控制台 → 你的域名 → SSL/TLS → Overview → 选择模式
```

#### 四种模式图解

```
1. Off（关闭）
   用户 ──HTTP──→ Cloudflare ──HTTP──→ 源站
   ❌ 完全不加密，不推荐

2. Flexible（灵活）
   用户 ──HTTPS──→ Cloudflare ──HTTP──→ 源站
   ⚠️ 前半段加密，后半段明文！源站不需要证书
   ⚠️ 有安全风险：CF 到源站这段可被窃听

3. Full（完全）
   用户 ──HTTPS──→ Cloudflare ──HTTPS──→ 源站
   ✅ 全程加密，但源站证书可以是自签名的（不验证有效性）

4. Full (Strict)（完全严格）  ← 推荐 ✅
   用户 ──HTTPS──→ Cloudflare ──HTTPS──→ 源站
   ✅ 全程加密 + 验证源站证书必须有效（CA 签发或 CF Origin 证书）
```

#### 怎么选？

| 你的源站情况 | 推荐模式 |
|---|---|
| 源站没有 SSL 证书（如纯 HTTP 的服务器） | Flexible（过渡用） |
| 源站有自签名证书 | Full |
| 源站有 CA 颁发的证书或 Cloudflare Origin 证书 | **Full (Strict)** ✅ |
| 使用 Cloudflare Pages / Workers（无源站） | 不需要配置，自动处理 |

> ⚠️ **Flexible 模式的陷阱**：如果你的源站配置了"强制 HTTPS 跳转"（如 Nginx 的 `return 301 https://`），同时 Cloudflare 用 Flexible 模式（CF 到源站走 HTTP），就会触发**无限重定向循环**——这是新手最常踩的坑。

### 4.2 自动 HTTPS：Edge Certificate 与 Universal SSL

Cloudflare 免费自动签发 SSL 证书，你**不需要手动申请**。

#### Edge Certificate（边缘证书）

这是用户浏览器看到的证书——由 Cloudflare 自动签发和续期：

```
证书信息：
  签发者：Google Trust Services（或 Let's Encrypt / DigiCert）
  覆盖：example.com + *.example.com（一级通配符）
  有效期：90 天，自动续期
  费用：免费 ✅
```

你不需要做任何操作，只要域名状态是 Active 且开了橙色云，证书就会自动生效。

#### Universal SSL

Universal SSL 是 Cloudflare 免费层的默认 Edge Certificate 方案。特点：

```
✅ 自动签发，无需配置
✅ 覆盖根域名 + 所有一级子域名（*.example.com）
✅ 自动续期
❌ 不覆盖二级子域名（如 a.b.example.com）
❌ 新站点可能需要等 15 分钟 ~ 24 小时才签发完成
```

> 💡 如果刚接入域名后访问显示"SSL 证书错误"，通常等几分钟就好了。可以在 `SSL/TLS → Edge Certificates` 页面查看证书状态。

### 4.3 Origin Certificate：保护源站到 Cloudflare 的连接

Edge Certificate 保护的是"用户 → Cloudflare"这段。要保护"Cloudflare → 源站"这段，需要在源站安装证书。

#### 最简单的方案：Cloudflare Origin Certificate

Cloudflare 提供免费的 Origin Certificate（源站证书），**只被 Cloudflare 信任**：

```
控制台 → SSL/TLS → Origin Server → Create Certificate

选项：
  Private Key Type: RSA (2048)
  Hostnames: example.com, *.example.com
  Certificate Validity: 15 years（最长 15 年，推荐）
```

生成后会得到两个文件：
- **Origin Certificate**（公钥）：`origin-cert.pem`
- **Private Key**（私钥）：`origin-key.pem`

#### 在 Nginx 上安装

```nginx
server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate     /etc/ssl/origin-cert.pem;
    ssl_certificate_key /etc/ssl/origin-key.pem;

    # ... 其他配置
}
```

安装完成后，将 SSL 模式切换为 **Full (Strict)** ✅

```
为什么用 Origin Certificate 而不是 Let's Encrypt？
  ✅ 有效期最长 15 年（Let's Encrypt 只有 90 天）
  ✅ 不需要配置自动续期
  ✅ 配合 Full (Strict) 模式，安全性最高
  ❌ 只被 Cloudflare 信任——如果关掉橙色云，浏览器会报证书错误
```

> 💡 **推荐组合**：Cloudflare Origin Certificate + Full (Strict) 模式。这是最简单、最安全、最省心的方案。

### 4.4 强制 HTTPS + HSTS 配置

#### 强制 HTTPS（Always Use HTTPS）

让所有 HTTP 请求自动跳转到 HTTPS：

```
控制台 → SSL/TLS → Edge Certificates → Always Use HTTPS → 开启 ✅
```

开启后，访问 `http://example.com` 会自动 301 跳转到 `https://example.com`。

> 💡 这个功能替代了 Nginx 里写 `return 301 https://$host$request_uri;` 的操作。在 Cloudflare 层面做跳转更高效。

#### HSTS（HTTP Strict Transport Security）

HSTS 告诉浏览器："以后访问这个域名，**永远用 HTTPS**，即使用户手动输入 http:// 也直接走 HTTPS"。

```
控制台 → SSL/TLS → Edge Certificates → HTTP Strict Transport Security (HSTS) → Enable

推荐配置：
  Status: On
  Max-Age: 6 months（15552000 秒）
  Include subdomains: On
  No-Sniff: On
```

```
HSTS 工作流程：
  第一次访问：服务器返回 HSTS 头 → 浏览器记住
  后续访问：浏览器自动将 http:// 改成 https://（不发出 HTTP 请求）

  对比 Always Use HTTPS：
    Always Use HTTPS: http 请求到达 CF → CF 返回 301 → 浏览器再请求 https
    HSTS:             浏览器直接请求 https（少了一次 HTTP 往返）
```

> ⚠️ **HSTS 开启后很难撤销**。浏览器会在 Max-Age 时间内强制 HTTPS，如果你的 HTTPS 配置出问题，用户将无法访问网站。确认 SSL 配置稳定后再开启。

### 4.5 常见 SSL 报错排查（重定向循环、混合内容）

#### 问题 1：ERR_TOO_MANY_REDIRECTS（重定向循环）

**最常见的原因：SSL 模式设为 Flexible + 源站强制 HTTPS**

```
循环过程：
  1. 用户访问 https://example.com
  2. Cloudflare（Flexible 模式）用 HTTP 请求源站
  3. 源站收到 HTTP 请求 → 返回 301 跳转到 https://
  4. Cloudflare 再次用 HTTP 请求源站
  5. 源站再次返回 301 ...（无限循环）

解决方案：
  ✅ 方案 A：将 SSL 模式改为 Full 或 Full (Strict)（推荐）
  ✅ 方案 B：关闭源站的强制 HTTPS 跳转（不推荐）
```

#### 问题 2：Mixed Content（混合内容警告）

页面通过 HTTPS 加载，但其中引用了 HTTP 的资源（图片、JS、CSS）：

```
解决方案：
  1. 控制台 → SSL/TLS → Edge Certificates → Automatic HTTPS Rewrites → 开启
     Cloudflare 会自动将页面中的 http:// 链接改为 https://

  2. 检查代码中是否硬编码了 http:// 开头的资源链接
     ❌ <img src="http://example.com/logo.png">
     ✅ <img src="https://example.com/logo.png">
     ✅ <img src="//example.com/logo.png">（协议自适应）
```

#### 问题 3：SSL 证书未生效（显示 Cloudflare 错误页面）

```
可能原因：
  1. 刚接入域名，证书还在签发中 → 等 15 分钟再试
  2. Nameserver 还没生效 → 等待 DNS 传播
  3. 域名被 Cloudflare 暂停 → 检查账号状态
  4. 使用了二级子域名但没有对应证书 → 免费层不支持

排查命令：
  curl -vI https://example.com 2>&1 | grep -i "ssl\|cert\|issuer"
```

#### 问题 4：源站证书过期

```
如果用的是 Let's Encrypt 证书（90 天）且续期失败：
  → 切换到 Cloudflare Origin Certificate（15 年有效期）
  → 参考 4.3 节安装即可
```

---

## 5. CDN 缓存与性能优化

Cloudflare 的 CDN 是免费且无限带宽的——它会在全球 300+ 个边缘节点缓存你的静态资源，让用户就近获取内容。理解缓存机制，能让你的网站速度提升数倍。

### 5.1 Cloudflare 缓存机制：什么会被缓存、缓存多久

#### 默认缓存规则

Cloudflare **默认只缓存静态资源**，不缓存 HTML：

| 文件类型 | 是否默认缓存 | 说明 |
|---|---|---|
| `.js` `.css` | ✅ 缓存 | 前端打包产物 |
| `.png` `.jpg` `.gif` `.webp` `.svg` | ✅ 缓存 | 图片资源 |
| `.woff2` `.ttf` | ✅ 缓存 | 字体文件 |
| `.pdf` `.zip` | ✅ 缓存 | 下载文件 |
| `.html` | ❌ 不缓存 | 页面内容可能动态变化 |
| API 响应（`/api/*`） | ❌ 不缓存 | 数据是动态的 |

#### 缓存状态（cf-cache-status 头）

通过浏览器开发者工具的 Network 面板，查看响应头 `cf-cache-status`：

```
cf-cache-status: HIT      → 缓存命中，直接从边缘节点返回（最快）
cf-cache-status: MISS     → 未命中，回源获取并缓存
cf-cache-status: EXPIRED  → 缓存已过期，重新回源
cf-cache-status: DYNAMIC  → 动态内容，不缓存
cf-cache-status: BYPASS   → 被规则跳过，不缓存
```

#### 缓存时间（TTL）

缓存多久由**源站的 Cache-Control 头**和**Cloudflare 的 Edge Cache TTL** 共同决定：

```
优先级：
  Cloudflare Cache Rules（最高）
  > 源站 Cache-Control / Expires 头
  > Cloudflare 默认 TTL

默认 TTL 参考：
  免费层：遵循源站的 Cache-Control 头
  如果源站没有设置：Cloudflare 默认缓存 2 小时
```

### 5.2 Cache Rules：精细化缓存控制

Cache Rules 是 Cloudflare 推荐的新一代缓存控制方式（替代旧版 Page Rules 中的缓存功能）。

```
控制台 → 你的域名 → Caching → Cache Rules → Create Rule
```

#### 常用规则示例

**规则 1：缓存 HTML 页面（静态站点适用）**

```
条件：URI Path contains "/"  AND  URI Path does not contain "/api/"
动作：
  Cache eligibility: Eligible for cache
  Edge TTL: Override origin → 1 day
  Browser TTL: Override origin → 4 hours
```

**规则 2：API 接口不缓存**

```
条件：URI Path starts with "/api/"
动作：
  Cache eligibility: Bypass cache
```

**规则 3：静态资源长期缓存**

```
条件：URI Path matches ".*\.(js|css|png|jpg|webp|woff2)$"
动作：
  Edge TTL: Override origin → 30 days
  Browser TTL: Override origin → 7 days
```

> 💡 免费层有 **5 条 Cache Rules**。合理利用条件组合，5 条通常够用。

#### Edge TTL vs Browser TTL

```
Edge TTL:    内容在 Cloudflare 边缘节点上缓存多久
Browser TTL: 告诉浏览器缓存多久（对应 Cache-Control: max-age）

推荐策略：
  Edge TTL > Browser TTL
  这样即使 Cloudflare 缓存未过期，浏览器也会定期检查更新
```

### 5.3 Page Rules 实战（重定向、缓存级别、安全级别）

Page Rules 是 Cloudflare 的"瑞士军刀"——用 URL 模式匹配，对不同路径应用不同配置。免费层有 **3 条 Page Rules**。

```
控制台 → 你的域名 → Rules → Page Rules → Create Page Rule
```

#### 常用 Page Rules

**规则 1：www 跳转到裸域**

```
URL 匹配：www.example.com/*
设置：Forwarding URL → 301 Permanent Redirect
目标：https://example.com/$1
```

**规则 2：特定路径提升缓存级别**

```
URL 匹配：example.com/static/*
设置：Cache Level → Cache Everything
      Edge Cache TTL → a month
```

**规则 3：后台路径关闭缓存 + 提升安全**

```
URL 匹配：example.com/admin/*
设置：Cache Level → Bypass
      Security Level → High
      Browser Integrity Check → On
```

> ⚠️ **Page Rules 正在被新功能替代**。Cloudflare 推荐用 Cache Rules（第 5.2 节）管理缓存，用 Redirect Rules 管理跳转。但 Page Rules 仍然有效，适合简单场景。

### 5.4 Speed 优化：Minify / Brotli / Early Hints / Rocket Loader

Cloudflare 提供了一系列免费的性能优化功能，大部分只需要点一下开关。

```
控制台 → 你的域名 → Speed → Optimization
```

| 功能 | 作用 | 推荐 |
|---|---|---|
| **Auto Minify** | 压缩 JS / CSS / HTML，去掉空格和注释 | ✅ 全部开启 |
| **Brotli** | 更高效的压缩算法（比 gzip 小 15-20%） | ✅ 开启 |
| **Early Hints** | 在 HTML 返回前就告诉浏览器预加载关键资源 | ✅ 开启 |
| **HTTP/2** | 多路复用，减少连接开销 | ✅ 默认开启 |
| **HTTP/3（QUIC）** | 更快的传输协议 | ✅ 开启 |
| **Rocket Loader** | 异步加载 JS，加快页面渲染 | ⚠️ 谨慎 |
| **Mirage** | 图片延迟加载（仅 Pro 版） | 免费层无 |
| **Polish** | 图片压缩优化（仅 Pro 版） | 免费层无 |

> ⚠️ **Rocket Loader 可能导致 JS 执行顺序问题**。如果开启后页面交互异常（按钮不响应、组件不渲染），立即关闭。React/Vue 等 SPA 框架通常不建议开启。

#### 一键优化建议

```
免费层推荐配置：
  ✅ Auto Minify: JS + CSS + HTML 全开
  ✅ Brotli: On
  ✅ Early Hints: On
  ✅ HTTP/2: On（默认）
  ✅ HTTP/3: On
  ⚠️ Rocket Loader: Off（SPA 项目关闭）
```

### 5.5 清除缓存（Purge）的正确姿势

更新了网站内容但用户看到的还是旧版？需要清除 Cloudflare 的缓存。

```
控制台 → 你的域名 → Caching → Configuration → Purge Cache
```

#### 三种清除方式

| 方式 | 适用场景 | 操作 |
|---|---|---|
| **Purge Everything** | 大版本更新、紧急修复 | 清除所有缓存（简单粗暴） |
| **Purge by URL** | 修改了某个特定文件 | 输入具体 URL，只清除该文件的缓存 |
| **Purge by Prefix** | 修改了某个目录下的文件 | 输入路径前缀，如 `example.com/static/` |

#### 用 API 清除缓存（自动化）

部署脚本中自动清除缓存：

```bash
# Purge Everything
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/purge_cache" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'

# Purge 指定 URL
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/purge_cache" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"files":["https://example.com/style.css","https://example.com/app.js"]}'
```

> 💡 **ZONE_ID** 在控制台 → 你的域名 → Overview 页面右侧。**API Token** 在 My Profile → API Tokens 中创建。

#### 减少手动清缓存的技巧

```
技巧 1：文件名加 Hash（前端打包默认做了）
  app.abc123.js → 文件内容变了，Hash 变了，URL 变了 → 自动是新缓存

技巧 2：HTML 不缓存或短 TTL
  HTML 文件引用了带 Hash 的 JS/CSS，只要 HTML 不被缓存
  → 用户每次拿到最新的 HTML → 自动加载最新的 JS/CSS

技巧 3：部署流程中加入 Purge API 调用
  CI/CD 部署完成后 → 自动调用 Purge Everything → 用户立即看到新版本
```

---

## 6. Cloudflare Pages：前端项目零配置部署

Cloudflare Pages 是一个**前端静态站点托管平台**，类似 Vercel 和 Netlify。连接 Git 仓库后，每次 push 代码自动构建部署——免费、无限带宽、全球 CDN。

### 6.1 Pages vs Vercel vs Netlify：静态托管方案对比

| | Cloudflare Pages | Vercel | Netlify |
|---|---|---|---|
| **免费带宽** | ✅ 无限 | 100 GB/月 | 100 GB/月 |
| **免费构建次数** | 500 次/月 | 6000 分钟/月 | 300 分钟/月 |
| **构建速度** | 中等 | ✅ 快 | 中等 |
| **SSR/SSG 支持** | Next.js / Nuxt / Astro | ✅ Next.js 原生 | 一般 |
| **边缘函数** | Workers（强大） | Edge Functions | Edge Functions |
| **CDN 节点** | 300+ | ~70 | ~30+ |
| **配套服务** | R2、KV、D1、DNS、安全 | 少 | 少 |
| **适合** | 全栈生态整合 | Next.js 项目 | 简单静态站 |

```
选型建议：
  用 Next.js 且追求最佳 DX         → Vercel
  需要 CDN + 安全 + 存储 + 计算一站式 → Cloudflare Pages ✅
  简单的静态博客                    → 三者都行
```

### 6.2 实战：部署一个 React/Vite 项目到 Pages

#### 方式 1：通过 Git 集成（推荐）

**Step 1：代码推送到 GitHub / GitLab**

确保你的项目已经推送到远程仓库。

**Step 2：创建 Pages 项目**

```
控制台 → Workers & Pages → Create application → Pages → Connect to Git

选择：
  GitHub / GitLab → 授权 → 选择仓库 → 选择分支（通常 main）
```

**Step 3：配置构建设置**

Cloudflare 会自动识别框架并预填配置。常用框架的设置：

| 框架 | Build command | Build output directory |
|---|---|---|
| Vite (React) | `npm run build` | `dist` |
| Create React App | `npm run build` | `build` |
| Next.js (Static) | `npx next build` | `.next` |
| Vue (Vite) | `npm run build` | `dist` |
| Astro | `npm run build` | `dist` |

**Step 4：点击 Save and Deploy**

Cloudflare 会自动：安装依赖 → 构建项目 → 部署到全球 CDN。

首次部署完成后，你会得到一个 `https://your-project.pages.dev` 的地址。

#### 方式 2：通过 Wrangler CLI 直接上传

不需要 Git，直接把构建产物上传：

```bash
# 安装 Wrangler
npm install -g wrangler

# 登录
wrangler login

# 先在本地构建
npm run build

# 部署（dist 是构建输出目录）
wrangler pages deploy dist --project-name=my-app
```

> 💡 CLI 方式适合 CI/CD 自定义流程，或者不方便连接 Git 的场景。

### 6.3 自定义域名绑定

默认的 `*.pages.dev` 域名虽然能用，但不够专业。绑定自定义域名只需两步：

**Step 1：在 Pages 项目设置中添加域名**

```
Pages 项目 → Custom domains → Set up a custom domain
输入：example.com（或 app.example.com 等子域名）
```

**Step 2：Cloudflare 自动配置 DNS**

如果域名已经在 Cloudflare 管理，DNS 记录会**自动添加**：

```
自动创建的 DNS 记录：
  Type:    CNAME
  Name:    @ (或你填的子域名)
  Content: your-project.pages.dev
  Proxy:   ☁️ 橙色
```

如果域名不在 Cloudflare 管理，需要手动去域名注册商添加 CNAME 记录。

> 💡 SSL 证书也是自动签发的，绑定完域名后 HTTPS 直接可用，不需要任何额外配置。

### 6.4 预览部署（Preview Deployment）与分支策略

Pages 最实用的功能之一——每个 Pull Request / 非主分支的 push 都会生成一个独立的**预览 URL**。

#### 工作流程

```
你的 Git 分支策略：
  main 分支         → 推送后自动部署到生产环境（production）
  feature-xxx 分支  → 推送后自动部署到预览环境（preview）

生产 URL:  https://your-project.pages.dev
预览 URL:  https://abc123.your-project.pages.dev（每次构建不同）
```

#### 典型工作流

```
1. 创建功能分支
   git checkout -b feature-new-ui

2. 开发、提交、推送
   git push origin feature-new-ui

3. Cloudflare 自动构建预览版本
   → 生成 https://xyz789.your-project.pages.dev

4. 分享给团队或产品经理在线预览
   → 确认没问题后合并到 main

5. main 分支触发生产部署
   → 用户访问的 https://your-project.pages.dev 更新
```

> 💡 预览部署 + PR 审核 = 零风险上线。每个改动都能在独立环境中验证。

#### 配置分支过滤

默认所有分支都会触发构建。如果想只构建特定分支：

```
Pages 项目 → Settings → Builds & deployments → Branch deployments

可选：
  - All branches（所有分支都构建）
  - None（只构建生产分支）
  - Custom branches（指定分支名或通配符）
```

### 6.5 环境变量与构建配置

#### 环境变量

前端项目经常需要环境变量（如 API 地址、Feature Flag）：

```
Pages 项目 → Settings → Environment variables → Add variable

例子：
  变量名：VITE_API_URL
  Production 值：https://api.example.com
  Preview 值：https://api-staging.example.com
```

注意区分 **Production** 和 **Preview** 的值——这样预览环境会自动连接测试后端。

> ⚠️ **Vite 项目的环境变量必须以 `VITE_` 开头**才能在前端代码中访问。Create React App 是 `REACT_APP_` 前缀。这是框架的要求，不是 Cloudflare 的限制。

#### 构建配置进阶

```
Pages 项目 → Settings → Builds & deployments

可配置项：
  Build command:          npm run build
  Build output directory: dist
  Root directory:         /（如果是 Monorepo，可以指定子目录）
  Node.js version:        通过环境变量 NODE_VERSION=18 指定
```

**指定 Node.js 版本（常见需求）：**

```
环境变量中添加：
  NODE_VERSION = 18
  或
  NODE_VERSION = 20
```

**Monorepo 支持：**

```
如果项目结构是：
  ├── apps/
  │   ├── web/          ← 前端项目
  │   └── api/
  └── packages/

设置 Root directory 为：apps/web
Build command 改为：cd ../.. && npm install && cd apps/web && npm run build
（或使用 Turborepo / pnpm workspace 的构建命令）
```

---

## 7. Cloudflare Workers：边缘计算入门

Workers 是 Cloudflare 最强大的产品之一——它让你的代码运行在全球 300+ 个边缘节点上，不需要传统服务器。可以用它做 API、请求转发、数据处理等轻量级后端逻辑。

### 7.1 Workers 核心概念：V8 Isolate、冷启动、免费额度

#### 什么是 Workers？

```
传统后端：
  你的代码运行在一台（或几台）服务器上
  用户请求 → 跨越网络 → 到达服务器 → 处理 → 返回结果

Workers：
  你的代码运行在全球 300+ 个边缘节点上
  用户请求 → 到达最近的节点 → 就地处理 → 返回结果（极快）
```

#### V8 Isolate（隔离环境）

Workers 不是运行在 Docker 容器或虚拟机中，而是使用 **V8 Isolate**（Chrome 浏览器的 JavaScript 引擎）：

```
传统 Serverless（如 AWS Lambda）：
  冷启动：启动容器 + 加载运行时 → 几百毫秒 ~ 几秒

Workers（V8 Isolate）：
  冷启动：启动隔离环境 → < 5 毫秒 ← 几乎无感知
```

**代价**：Workers 不是完整的 Node.js 环境，不能用 `fs`（文件系统）、`child_process`（子进程）等 Node.js 原生模块。

#### 免费额度

| 指标 | 免费层 | 付费版（$5/月） |
|---|---|---|
| 请求数 | **10 万次/天** | 1000 万次/月 |
| CPU 时间 | 10 ms/请求 | 50 ms/请求 |
| Worker 数量 | 无限 | 无限 |
| 脚本大小 | 1 MB | 10 MB |
| KV 读取 | 10 万次/天 | 1000 万次/月 |

> 💡 10 万次/天对于个人项目绰绰有余。按 30 天算就是**月 300 万次免费请求**。

### 7.2 Wrangler CLI 安装与项目初始化

Wrangler 是 Cloudflare 官方的 CLI 工具，用来开发、测试、部署 Workers。

#### 安装

```bash
# 全局安装
npm install -g wrangler

# 验证安装
wrangler --version

# 登录 Cloudflare 账号
wrangler login
# 浏览器会打开授权页面，点击 Allow
```

#### 创建项目

```bash
# 创建新 Worker 项目
wrangler init my-worker

# 选项（推荐）：
#   Would you like to use TypeScript? → Yes
#   Would you like to create a Worker? → Yes (Fetch handler)
```

生成的项目结构：

```
my-worker/
├── src/
│   └── index.ts       ← Worker 代码
├── wrangler.toml      ← 配置文件
├── package.json
└── tsconfig.json
```

#### wrangler.toml 核心配置

```toml
name = "my-worker"           # Worker 名称
main = "src/index.ts"        # 入口文件
compatibility_date = "2024-01-01"  # API 兼容日期

# 绑定 KV 存储（可选）
# [kv_namespaces](kv_namespaces)
# binding = "MY_KV"
# id = "xxx"
```

### 7.3 第一个 Worker：Hello World API

#### 最简代码

```typescript
// src/index.ts
export default {
  async fetch(request: Request): Promise<Response> {
    return new Response("Hello from Cloudflare Workers!", {
      headers: { "Content-Type": "text/plain" },
    });
  },
};
```

#### 本地开发

```bash
# 启动本地开发服务器（支持热重载）
wrangler dev

# 输出：
# Ready on http://localhost:8787
# 浏览器打开即可看到 "Hello from Cloudflare Workers!"
```

#### 部署上线

```bash
wrangler deploy

# 输出：
# Published my-worker (xxx)
#   https://my-worker.your-subdomain.workers.dev
```

#### 进阶：处理不同路径和方法

```typescript
export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    // 路由分发
    if (url.pathname === "/api/hello") {
      return Response.json({ message: "Hello!", time: new Date().toISOString() });
    }

    if (url.pathname === "/api/echo" && request.method === "POST") {
      const body = await request.json();
      return Response.json({ echo: body });
    }

    // 404 处理
    return new Response("Not Found", { status: 404 });
  },
};
```

> 💡 Workers 使用标准的 **Web API**（`Request`、`Response`、`fetch`），和浏览器中的写法几乎一样。如果你学过前端的 `fetch`，写 Worker 会非常自然。

### 7.4 实战：用 Worker 做 API 代理 / CORS 代理 / 请求转发

#### 场景 1：API 代理（隐藏后端地址和密钥）

前端直接调用第三方 API 会暴露 API Key。用 Worker 做代理层：

```typescript
export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/ai")) {
      // 转发到真实的 AI API，附加密钥
      const targetUrl = "https://api.openai.com/v1/chat/completions";
      const response = await fetch(targetUrl, {
        method: request.method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${env.OPENAI_API_KEY}`,  // 密钥存在环境变量中
        },
        body: request.body,
      });
      return response;
    }

    return new Response("Not Found", { status: 404 });
  },
};
```

#### 场景 2：CORS 代理（解决跨域问题）

前端开发时经常遇到跨域限制。用 Worker 做通用 CORS 代理：

```typescript
export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const targetUrl = url.searchParams.get("url");

    if (!targetUrl) {
      return new Response("用法：?url=https://example.com/api", { status: 400 });
    }

    const response = await fetch(targetUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });

    // 添加 CORS 头
    const newResponse = new Response(response.body, response);
    newResponse.headers.set("Access-Control-Allow-Origin", "*");
    newResponse.headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    return newResponse;
  },
};
```

#### 场景 3：请求转发 + 路径改写

把 `api.example.com/v2/*` 转发到内部服务器的不同端口：

```typescript
export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    
    // /v2/users → 内部服务 http://internal:3001/users
    if (url.pathname.startsWith("/v2/")) {
      const path = url.pathname.replace("/v2/", "/");
      return fetch(`http://internal-server:3001${path}`, {
        method: request.method,
        headers: request.headers,
        body: request.body,
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};
```

### 7.5 Workers 路由与自定义域名绑定

默认 Worker 的地址是 `your-worker.your-subdomain.workers.dev`。可以绑定到自定义域名。

#### 方式 1：Custom Domain（推荐）

```
控制台 → Workers & Pages → 你的 Worker → Settings → Triggers → Custom Domains
添加：api.example.com
```

Cloudflare 会自动创建 DNS 记录并签发 SSL 证书。

#### 方式 2：Route 路由匹配

让 Worker 只处理特定路径的请求：

```
控制台 → Workers & Pages → 你的 Worker → Settings → Triggers → Routes
添加：example.com/api/*
```

```
路由匹配规则：
  example.com/api/*     → 匹配 /api/ 下所有路径
  *.example.com/api/*   → 匹配所有子域名的 /api/ 路径
  example.com/*         → 匹配所有路径（慎用，会拦截整个站点）
```

> 💡 **Custom Domain vs Route 的区别**：Custom Domain 是独立域名（如 `api.example.com`），Route 是在已有域名上匹配特定路径（如 `example.com/api/*`）。

### 7.6 KV 存储：Workers 的键值数据库

Workers 本身是无状态的——每次请求结束，内存就清空了。如果需要**持久化存储数据**，可以用 KV（Key-Value）存储。

#### 创建 KV Namespace

```bash
# 用 Wrangler 创建
wrangler kv namespace create "MY_STORE"

# 输出类似：
# Add the following to your wrangler.toml:
# [kv_namespaces](kv_namespaces)
# binding = "MY_STORE"
# id = "abc123..."
```

将输出的配置加到 `wrangler.toml`。

#### 在 Worker 中使用 KV

```typescript
interface Env {
  MY_STORE: KVNamespace;  // 类型声明
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // 写入
    if (url.pathname === "/set") {
      const key = url.searchParams.get("key")!;
      const value = url.searchParams.get("value")!;
      await env.MY_STORE.put(key, value);
      return Response.json({ status: "saved", key, value });
    }

    // 读取
    if (url.pathname === "/get") {
      const key = url.searchParams.get("key")!;
      const value = await env.MY_STORE.get(key);
      return Response.json({ key, value });
    }

    // 删除
    if (url.pathname === "/delete") {
      const key = url.searchParams.get("key")!;
      await env.MY_STORE.delete(key);
      return Response.json({ status: "deleted", key });
    }

    return new Response("KV Demo: /set?key=x&value=y | /get?key=x | /delete?key=x");
  },
};
```

#### KV 的特性和限制

```
✅ 全球分布式，读取速度极快（边缘缓存）
✅ 免费层：10 万次读 + 1000 次写 / 天
✅ 单个值最大 25 MB
✅ 支持设置过期时间（TTL）

⚠️ 最终一致性（写入后全球同步需要 ~60 秒）
⚠️ 不适合高频写入（每秒写入有限制）
⚠️ 不是关系型数据库，不支持查询/索引
```

> 💡 KV 适合**读多写少**的场景：配置存储、URL 短链映射、缓存数据、Feature Flag。需要复杂查询用 D1（Cloudflare 的 SQLite 数据库）。

### 7.7 Workers 的局限与适用场景

#### 不适合 Workers 的场景

```
❌ 长时间运行的任务（CPU 限制 10-50ms/请求）
❌ 需要 Node.js 原生模块（fs、net、child_process 等）
❌ 大量计算密集型任务（图片处理、视频转码）
❌ 需要持久连接的服务（长期 WebSocket 需要 Durable Objects）
❌ 需要完整数据库（复杂 SQL 查询、事务）
```

#### 适合 Workers 的场景

```
✅ API 网关 / 请求代理 / 转发
✅ 认证和鉴权（JWT 验证、API Key 校验）
✅ A/B 测试（在边缘决定返回哪个版本）
✅ 请求/响应改写（添加 Header、修改 Body）
✅ 短链服务（KV 存储映射关系）
✅ 边缘缓存控制（自定义缓存逻辑）
✅ Webhook 接收和分发
✅ 简单的 REST API（配合 KV / D1）
```

#### Workers vs 传统服务器的选型

| | Workers | 传统服务器（VPS / Cloud Run） |
|---|---|---|
| **延迟** | ✅ 极低（边缘就近） | 取决于服务器位置 |
| **运维** | ✅ 零运维 | 需要维护服务器 |
| **成本** | ✅ 免费层很慷慨 | 最低 $5-10/月 |
| **灵活性** | ❌ 受限（非完整 Node.js）| ✅ 完全自由 |
| **持久化** | KV / D1（有限） | ✅ 任何数据库 |
| **适合** | 轻量级 API、边缘逻辑 | 复杂后端、长任务 |

> 💡 **最佳实践**：Workers 做边缘层（代理、鉴权、缓存），传统服务器做核心业务逻辑。两者组合使用效果最好。

---

## 8. R2 对象存储

R2 是 Cloudflare 的对象存储服务——和 AWS S3 功能类似，但有一个杀手级优势：**零出站费用**。上传收费，存储收费，但用户下载文件**不收钱**。

### 8.1 R2 vs S3 vs OSS：零出站费用的对象存储

| | Cloudflare R2 | AWS S3 | 阿里云 OSS |
|---|---|---|---|
| **存储费用** | $0.015/GB/月 | $0.023/GB/月 | ¥0.12/GB/月 |
| **出站流量** | ✅ **$0（免费）** | $0.09/GB | ¥0.25-0.50/GB |
| **免费层** | 10 GB 存储 | 5 GB（12 个月） | 无 |
| **API 兼容** | S3 兼容 ✅ | 原生 | 非标准 |
| **全球分布** | 自动（边缘缓存） | 需选区域 | 需选区域 |

```
出站费用对比（假设存了 100 GB，每月被下载 1 TB）：

AWS S3:   存储 $2.3 + 出站 $92 = $94.3/月
R2:       存储 $1.5 + 出站 $0  = $1.5/月  ← 省了 98%
```

> 💡 如果你的应用有大量**文件下载**（图片、视频、文档），R2 比 S3 便宜一个数量级。

### 8.2 创建 Bucket 与基本操作

#### 通过控制台创建

```
控制台 → R2 → Create bucket

填写：
  Bucket name: my-files（全局唯一）
  Location: Automatic（推荐，自动选择最近的区域）
```

#### 通过 Wrangler CLI 操作

```bash
# 创建 Bucket
wrangler r2 bucket create my-files

# 上传文件
wrangler r2 object put my-files/images/logo.png --file=./logo.png

# 下载文件
wrangler r2 object get my-files/images/logo.png --file=./downloaded-logo.png

# 删除文件
wrangler r2 object delete my-files/images/logo.png

# 列出 Bucket 中的文件
wrangler r2 object list my-files
```

#### 通过控制台上传

控制台 → R2 → 你的 Bucket → Upload，可以直接拖拽文件上传。适合少量文件的手动管理。

### 8.3 通过 Workers 或公共 URL 访问 R2 文件

R2 的文件默认是**私有的**，需要通过以下方式对外提供访问。

#### 方式 1：开启公共访问（最简单）

```
控制台 → R2 → 你的 Bucket → Settings → Public access

选项 A：R2.dev 子域名
  开启后获得：https://pub-xxx.r2.dev
  文件访问：https://pub-xxx.r2.dev/images/logo.png

选项 B：自定义域名（推荐）
  添加：files.example.com
  文件访问：https://files.example.com/images/logo.png
```

> 💡 自定义域名会自动经过 Cloudflare CDN 缓存，访问速度更快。

#### 方式 2：通过 Worker 访问（可控制权限）

将 R2 绑定到 Worker，实现自定义的访问逻辑：

```toml
# wrangler.toml
[r2_buckets](r2_buckets)
binding = "MY_BUCKET"
bucket_name = "my-files"
```

```typescript
interface Env {
  MY_BUCKET: R2Bucket;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const key = url.pathname.slice(1);  // 去掉开头的 /

    // 获取文件
    const object = await env.MY_BUCKET.get(key);
    if (!object) {
      return new Response("File not found", { status: 404 });
    }

    return new Response(object.body, {
      headers: {
        "Content-Type": object.httpMetadata?.contentType || "application/octet-stream",
        "Cache-Control": "public, max-age=86400",  // 缓存 1 天
      },
    });
  },
};
```

### 8.4 实战：用 R2 搭建个人图床

结合 Worker + R2，搭建一个支持上传和访问的简易图床：

```typescript
interface Env {
  MY_BUCKET: R2Bucket;
  AUTH_TOKEN: string;  // 上传鉴权令牌（环境变量）
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // 上传图片：PUT /upload/filename.png
    if (request.method === "PUT" && url.pathname.startsWith("/upload/")) {
      // 简单鉴权
      if (request.headers.get("Authorization") !== `Bearer ${env.AUTH_TOKEN}`) {
        return new Response("Unauthorized", { status: 401 });
      }

      const key = url.pathname.replace("/upload/", "");
      await env.MY_BUCKET.put(key, request.body, {
        httpMetadata: { contentType: request.headers.get("Content-Type") || "image/png" },
      });

      return Response.json({
        url: `https://img.example.com/${key}`,
        message: "上传成功",
      });
    }

    // 访问图片：GET /filename.png
    if (request.method === "GET") {
      const key = url.pathname.slice(1);
      if (!key) return new Response("图床服务运行中", { status: 200 });

      const object = await env.MY_BUCKET.get(key);
      if (!object) return new Response("图片不存在", { status: 404 });

      return new Response(object.body, {
        headers: {
          "Content-Type": object.httpMetadata?.contentType || "image/png",
          "Cache-Control": "public, max-age=2592000",  // 缓存 30 天
        },
      });
    }

    return new Response("Method Not Allowed", { status: 405 });
  },
};
```

**上传测试：**

```bash
curl -X PUT "https://img.example.com/upload/avatar.png" \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: image/png" \
  --data-binary @avatar.png
```

### 8.5 S3 兼容 API：用现有 SDK 操作 R2

R2 兼容 S3 API，你可以用 **AWS SDK** 或任何 S3 客户端操作 R2。

#### 获取 API 凭证

```
控制台 → R2 → Manage R2 API Tokens → Create API token

权限：Object Read & Write
获得：
  Access Key ID:     xxx
  Secret Access Key: yyy
  Endpoint:          https://ACCOUNT_ID.r2.cloudflarestorage.com
```

#### 用 Python boto3 操作

```python
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="https://ACCOUNT_ID.r2.cloudflarestorage.com",
    aws_access_key_id="xxx",
    aws_secret_access_key="yyy",
    region_name="auto",
)

# 上传
s3.upload_file("local-file.png", "my-files", "images/photo.png")

# 下载
s3.download_file("my-files", "images/photo.png", "downloaded.png")

# 列出文件
response = s3.list_objects_v2(Bucket="my-files", Prefix="images/")
for obj in response.get("Contents", []):
    print(obj["Key"], obj["Size"])
```

#### 用 rclone 批量同步

```bash
# 配置 rclone（~/.config/rclone/rclone.conf）
# [r2]
# type = s3
# provider = Cloudflare
# access_key_id = xxx
# secret_access_key = yyy
# endpoint = https://ACCOUNT_ID.r2.cloudflarestorage.com

# 同步本地文件夹到 R2
rclone sync ./my-images r2:my-files/images/

# 列出文件
rclone ls r2:my-files/
```

> 💡 因为兼容 S3 API，几乎所有支持 S3 的工具（备份软件、CMS、图片处理服务）都可以直接对接 R2，只需修改 Endpoint。

---

## 9. 安全防护

Cloudflare 最初就是做安全起家的。即使是免费层，也提供了相当强的安全能力——DDoS 防护、WAF、IP 封锁等，很多中小企业花钱买都买不到这种级别的防护。

### 9.1 免费层安全能力概览

| 功能 | 免费层 | 说明 |
|---|---|---|
| **DDoS 防护** | ✅ 无限，自动缓解 | 无需配置，永远在线 |
| **托管 WAF 规则** | ✅ 基础规则集 | Cloudflare 维护的安全规则 |
| **自定义 WAF 规则** | 5 条 | 自定义过滤逻辑 |
| **IP Access Rules** | ✅ 无限 | 按 IP / 国家封锁 |
| **Bot Fight Mode** | ✅ 基础版 | 自动识别恶意爬虫 |
| **Under Attack Mode** | ✅ | 紧急防护模式 |
| **Rate Limiting** | 1 条（含 10K 请求） | 速率限制规则 |
| **Security Level** | ✅ 可调节 | 5 档安全等级 |

### 9.2 WAF 规则：防止常见攻击（SQL 注入、XSS）

#### 托管规则（自动生效）

```
控制台 → Security → WAF → Managed rules

Cloudflare 免费层默认启用基础防护规则：
  ✅ 防止已知漏洞利用
  ✅ 拦截恶意 Bot
  ✅ 阻止常见攻击向量
```

#### 自定义 WAF 规则（5 条免费）

```
控制台 → Security → WAF → Custom rules → Create rule
```

**规则 1：封锁特定 User-Agent**

```
条件：http.user_agent contains "sqlmap"
     OR http.user_agent contains "nikto"
动作：Block
```

**规则 2：保护管理后台**

```
条件：http.request.uri.path starts with "/admin"
     AND ip.src NOT IN {你的IP}
动作：Block
```

**规则 3：防止 API 滥用（只允许 JSON 请求）**

```
条件：http.request.uri.path starts with "/api/"
     AND NOT http.request.headers["content-type"] contains "application/json"
     AND http.request.method in {"POST" "PUT" "PATCH"}
动作：Block
```

### 9.3 DDoS 防护：自动缓解与 Under Attack 模式

#### 自动 DDoS 防护

Cloudflare 的 DDoS 防护是**永远在线、自动生效**的，不需要任何配置：

```
检测到异常流量 → 自动启动缓解 → 攻击结束自动恢复

能防护的攻击类型：
  ✅ L3/L4 网络层攻击（SYN Flood、UDP Flood 等）
  ✅ L7 应用层攻击（HTTP Flood、Slowloris 等）
  ✅ DNS 放大攻击
```

#### Under Attack 模式（紧急防护）

正在被大规模攻击时，手动开启更严格的防护：

```
控制台 → Overview → Under Attack Mode → On

效果：
  每个访客都需要通过 5 秒的 JS Challenge（验证页面）
  能有效过滤大量恶意请求

⚠️ 正常用户也会看到"请等待 5 秒"的页面
→ 攻击结束后记得关闭
```

#### Security Level（安全等级）

```
控制台 → Security → Settings → Security Level

5 档等级：
  Off           → 不做任何检查
  Essentially Off → 仅拦截最明显的威胁
  Low           → 宽松检查
  Medium        → 默认值（推荐）
  High          → 严格检查（可能误伤正常用户）
  I'm Under Attack → 最严格（等同于 Under Attack Mode）
```

### 9.4 IP Access Rules / 国家/地区封锁

#### IP 访问规则

```
控制台 → Security → WAF → Tools → IP Access Rules

操作：
  Block:     封锁特定 IP
  Challenge: 要求完成验证（如 Turnstile）
  Allow:     白名单放行
  
范围：
  单个 IP:    1.2.3.4
  IP 段:      1.2.3.0/24
  国家/地区:  CN / US / RU 等
  ASN:        AS12345
```

#### 实用场景

```
场景 1：封锁恶意 IP
  IP: 1.2.3.4 → Block

场景 2：封锁特定国家的访问
  Country: RU → Block（如果你的服务不面向俄罗斯用户）

场景 3：白名单你自己的服务器 IP
  IP: 43.136.43.80 → Allow（防止误拦截源站回调）
```

### 9.5 Rate Limiting：API 速率限制

防止 API 被暴力请求或恶意刷接口。

```
控制台 → Security → WAF → Rate limiting rules → Create rule
```

**示例：限制 API 请求频率**

```
条件：URI Path starts with "/api/"
速率：每分钟超过 60 次请求（按 IP 统计）
动作：Block（持续 60 秒）
```

**示例：限制登录接口防止暴力破解**

```
条件：URI Path equals "/api/login"
     AND Method equals "POST"
速率：每 10 分钟超过 5 次请求（按 IP 统计）
动作：Block（持续 30 分钟）
```

> 💡 免费层只有 **1 条 Rate Limiting 规则**（含 10,000 次匹配请求/月）。优先保护最关键的接口（如登录、注册、支付）。

---

## 10. 实战场景集锦

前面 9 章讲了 Cloudflare 各个产品的独立用法。本章把它们组合起来，给出常见部署场景的完整配置清单。

### 10.1 场景 A：个人博客部署（Pages + 自定义域名 + HTTPS）

```
技术栈：Astro / Hugo / VitePress 等静态生成器

配置清单：
  ┌─────────────────────────────────────────────┐
  │ 1. 代码推送到 GitHub                         │
  │ 2. Pages 连接 GitHub 仓库，自动构建部署       │
  │ 3. 绑定自定义域名 blog.example.com            │
  │    → DNS 自动添加 CNAME                       │
  │    → SSL 证书自动签发                         │
  │ 4. 开启 Speed 优化                            │
  │    → Auto Minify: 全开                        │
  │    → Brotli: On                               │
  │    → Early Hints: On                          │
  │ 5. 配置缓存                                   │
  │    → Cache Rule: 静态资源 Edge TTL 30 天       │
  │ 6. 安全                                       │
  │    → Always Use HTTPS: On                     │
  │    → Bot Fight Mode: On                       │
  └─────────────────────────────────────────────┘

总费用：$0（完全免费）
```

### 10.2 场景 B：FastAPI 后端 + Workers 做 API 网关

```
架构：
  用户 → api.example.com → Workers（鉴权/限流/缓存）→ 源站 FastAPI

配置清单：
  1. 源站（VPS）部署 FastAPI + Nginx
     → 安装 Origin Certificate（15 年）
     → Nginx 监听 443 端口

  2. DNS 配置
     → A 记录：api.example.com → 源站 IP（橙色云）

  3. SSL 模式
     → Full (Strict)

  4. Worker 做 API 网关
     → Route: api.example.com/v1/*
     → 功能：JWT 验证、请求日志、CORS 处理

  5. 安全规则
     → WAF: 封锁 sqlmap/nikto User-Agent
     → Rate Limiting: /v1/auth/* 每 10 分钟 5 次
     → IP 白名单：源站自身 IP

  6. 缓存
     → Cache Rule: /v1/public/* 缓存 1 小时
     → Cache Rule: /v1/auth/* 不缓存
```

### 10.3 场景 C：全栈 AI 应用的 CDN + 安全防护配置

```
架构：
  前端（Pages）+ 后端（VPS）+ AI API（第三方）

  example.com       → Pages（React 前端）
  api.example.com   → VPS（FastAPI 后端）
  img.example.com   → R2（用户上传的文件）

配置清单：
  1. 前端
     → Pages 部署 React，绑定 example.com
     → 环境变量：VITE_API_URL=https://api.example.com

  2. 后端
     → DNS A 记录：api.example.com → VPS IP（橙色云）
     → SSL: Full (Strict) + Origin Certificate
     → Worker 代理 AI API 调用（隐藏 OPENAI_API_KEY）

  3. 文件存储
     → R2 Bucket：user-uploads
     → 公共访问绑定 img.example.com
     → 上传通过后端 API（用 S3 SDK 写入 R2）

  4. 安全
     → WAF: 保护 /api/admin/* 只允许管理员 IP
     → Rate Limiting: /api/chat 每分钟 20 次
     → Always Use HTTPS: On
     → HSTS: On
```

### 10.4 场景 D：多域名管理与子域分配策略

```
一个 Cloudflare 账号管理多个项目：

主域名：example.com
  ├── example.com          → Pages（官网/营销站）
  ├── app.example.com      → Pages（Web 应用）
  ├── api.example.com      → VPS（后端 API）
  ├── admin.example.com    → Pages（管理后台，WAF 保护）
  ├── img.example.com      → R2（图片/文件）
  ├── docs.example.com     → Pages（文档站）
  └── staging.example.com  → Pages Preview（测试环境）

安全策略：
  全局：Bot Fight Mode On, Security Level Medium
  admin.*：WAF 规则限制 IP + High Security Level
  api.*：Rate Limiting + CORS Worker
  
DNS 记录总览：
  | Name    | Type  | Content              | Proxy |
  |---------|-------|----------------------|-------|
  | @       | CNAME | site.pages.dev       | ☁️    |
  | app     | CNAME | webapp.pages.dev     | ☁️    |
  | api     | A     | 43.136.43.80         | ☁️    |
  | admin   | CNAME | admin-panel.pages.dev| ☁️    |
  | img     | CNAME | (R2 custom domain)   | ☁️    |
  | docs    | CNAME | docs-site.pages.dev  | ☁️    |
  | @       | MX    | mx1.qq.com           | 灰色  |
```

---

## 11. 常见问题与排错手册

使用 Cloudflare 过程中最常遇到的问题汇总。遇到问题先来这里查。

### 11.1 DNS 不生效 / 传播延迟

```
症状：修改了 DNS 记录，但访问还是走旧地址

排查步骤：
  1. 确认 Nameserver 已生效
     → 终端运行：dig example.com NS
     → 应该返回 xxx.ns.cloudflare.com

  2. 检查 DNS 记录是否正确
     → 控制台 → DNS → Records → 确认 IP 和代理模式

  3. 清除本地 DNS 缓存
     → Mac:    sudo dscacheutil -flushcache
     → Windows: ipconfig /flushdns

  4. 检查全球传播状态
     → 访问 https://www.whatsmydns.net 查询

  5. 等待时间
     → 通常 5 分钟内生效
     → 极端情况需要 24-48 小时
     → 降低 TTL 可以加快后续变更的传播速度
```

### 11.2 SSL 重定向循环（ERR_TOO_MANY_REDIRECTS）

```
最常见原因（90% 的情况）：
  SSL 模式设为 Flexible + 源站配置了强制 HTTPS

解决方案（二选一）：
  ✅ 方案 A（推荐）：
     → SSL 模式改为 Full 或 Full (Strict)
     → 源站安装 Origin Certificate（参考第 4.3 节）

  ✅ 方案 B：
     → 关闭源站 Nginx 中的强制 HTTPS 跳转
     → 让 Cloudflare 的 Always Use HTTPS 来做跳转

快速验证：
  → 临时将 SSL 模式切换为 Full
  → 如果问题消失，说明确实是 Flexible 模式的问题
```

### 11.3 缓存导致更新不生效

```
症状：更新了网站内容/代码，但用户看到的还是旧版本

排查步骤：
  1. 确认是 Cloudflare 缓存问题
     → 浏览器打开开发者工具 → Network 面板
     → 查看 cf-cache-status 头
     → 如果是 HIT → 说明返回的是 Cloudflare 缓存

  2. 手动清除缓存
     → 控制台 → Caching → Purge Everything

  3. 如果清完还没更新
     → 可能是浏览器本地缓存 → Ctrl+Shift+R（强制刷新）
     → 或者是 Service Worker 缓存 → 清除浏览器站点数据

  4. 长期解决
     → 前端打包产物使用 Hash 文件名（Vite 默认做了）
     → HTML 文件设置短 TTL 或不缓存
     → 部署脚本中加入 Purge API 调用
```

### 11.4 Workers 部署失败排查

```
常见错误及解决：

错误 1：wrangler deploy 报 authentication error
  → wrangler login 重新登录
  → 检查 API Token 是否过期

错误 2：Script too large（脚本超过大小限制）
  → 免费层限制 1 MB
  → 检查是否引入了过大的 npm 包
  → 用 bundleAnalyzer 分析打包体积

错误 3：Worker threw exception（运行时错误）
  → 控制台 → Workers → 你的 Worker → Logs → Real-time
  → 查看详细错误堆栈
  → 本地用 wrangler dev 调试

错误 4：Subrequest limit exceeded（子请求超限）
  → 每个 Worker 执行最多发起 50 个子请求（fetch）
  → 优化逻辑，减少不必要的 fetch 调用

错误 5：CPU time limit exceeded（CPU 超时）
  → 免费层每次请求 CPU 时间 ≤ 10ms
  → 避免复杂计算，考虑升级到付费版（50ms）
```

### 11.5 源站暴露 IP 的安全风险与防护

```
风险：如果攻击者知道了你源站的真实 IP，可以绕过 Cloudflare 直接攻击

IP 可能泄露的途径：
  ❌ 历史 DNS 记录（切换到 Cloudflare 之前的 A 记录被记录）
  ❌ 邮件头（MX 记录指向的服务器暴露了 IP）
  ❌ 子域名没开橙色云（灰色云暴露 IP）
  ❌ SSL 证书信息（证书中包含服务器信息）
  ❌ 代码中硬编码了服务器 IP

防护措施：
  ✅ 1. 所有 HTTP 子域名都开橙色云
  ✅ 2. 源站防火墙只允许 Cloudflare 的 IP 段访问
        → https://www.cloudflare.com/ips/ 获取 IP 列表
        → iptables 或安全组中只放行这些 IP
  ✅ 3. 换一个新 IP（如果旧 IP 已泄露）
  ✅ 4. 邮件服务使用不同的 IP 或第三方邮件服务
  ✅ 5. 使用 Cloudflare Tunnel（终极方案）
        → 不暴露任何端口，通过隧道连接
        → 源站不需要公网 IP
```

> 💡 **Cloudflare Tunnel 是最安全的方案**——源站不需要打开任何端口，Cloudflare 通过加密隧道主动连接你的服务器。免费层即可使用。
