# 什么是单点登录（SSO）与 JWT

> 一次登录，多处通行——理解现代 Web 身份认证的核心机制。

---

## 一、从一个日常场景说起

早上打开电脑，你用 Google 账号登录了 Gmail 查收邮件。然后点开 Google Drive 找一份文档——不需要再登录。接着打开 YouTube 看个视频——还是不需要登录。最后用 Google Calendar 看一眼今天的日程——依然不需要登录。

**一次登录，所有 Google 服务直接畅通。**

这个你每天都在用、但可能从未注意过的体验，就是**单点登录（Single Sign-On，SSO）**。

再想想企业里的场景：一个中等规模的公司，员工每天要用 OA 系统、邮箱、项目管理工具、代码仓库、文档平台……如果每个系统都要单独登录一次，输入用户名和密码，一天下来光登录就得花掉好几分钟，更别提记住每个系统不同的密码了。

没有 SSO 的世界是这样的：

```
用户 → 打开 OA 系统     → 输入账号密码 → 登录 ✅
用户 → 打开邮箱系统      → 输入账号密码 → 登录 ✅
用户 → 打开项目管理工具   → 输入账号密码 → 登录 ✅
用户 → 打开代码仓库      → 输入账号密码 → 登录 ✅
用户 → 打开文档平台      → 输入账号密码 → 登录 ✅
                                    ↑ 5 次登录，5 套密码
```

有了 SSO 之后：

```
用户 → 打开 OA 系统     → 跳转统一登录页 → 输入一次账号密码 → 登录 ✅
用户 → 打开邮箱系统      → 已登录，直接进入 ✅
用户 → 打开项目管理工具   → 已登录，直接进入 ✅
用户 → 打开代码仓库      → 已登录，直接进入 ✅
用户 → 打开文档平台      → 已登录，直接进入 ✅
                                    ↑ 只登录 1 次
```

看起来很简单，对吧？但这里藏着一个关键问题：

> **OA 系统知道你登录了，凭什么邮箱系统也知道？它们是完全不同的应用，运行在不同的服务器上，甚至可能是不同公司开发的——它们之间是怎么"传话"的？**

这就是 SSO 要解决的核心技术问题：**如何在多个独立系统之间，安全可靠地共享"这个用户已经通过身份验证"这个信息。**

而 **JWT（JSON Web Token）** 就是当今最主流的"传话"方式之一——它是一种特殊格式的令牌，能把用户的身份信息打包成一个可验证、防篡改的字符串，在不同系统之间安全地传递。

接下来，我们从 SSO 的基本概念讲起，逐步深入到 JWT 的原理和实现。

---

## 二、单点登录（SSO）是什么

### 1. 定义

**单点登录（Single Sign-On，SSO）** 是一种身份认证机制：用户只需在一个地方登录一次，就能访问所有相互信任的应用系统，无需重复输入凭证。

用一句话概括：

> **一次认证，全局通行。**

反过来，与 SSO 对应的还有一个概念——**单点登出（Single Logout，SLO）**：在任意一个系统中退出登录，所有关联系统同时失效。登录和登出成对出现，才是完整的 SSO 体验。

### 2. SSO 解决了什么痛点

| 痛点 | 没有 SSO | 有了 SSO |
| :--- | :--- | :--- |
| **用户体验** | 每个系统都要登录，频繁输入密码 | 登录一次，畅通所有系统 |
| **密码疲劳** | N 个系统 = 记 N 套密码（或者全用同一个弱密码） | 只需记住一个账号密码 |
| **账号管理** | 员工入职/离职要在每个系统单独开通/注销 | 统一管理，一处操作全局生效 |
| **安全风险** | 密码分散在多个系统，任一泄露即受影响 | 认证集中化，便于统一做安全策略（MFA、风控等） |
| **开发成本** | 每个系统都要自建登录模块 | 接入统一认证中心即可，不必重复造轮子 |

### 3. SSO 的三个核心角色

理解 SSO 的架构，只需要搞清楚三个角色和它们之间的关系：

```
                    ┌──────────────────────┐
                    │     认证中心 (IdP)     │
                    │  Identity Provider   │
                    │                      │
                    │  · 存储用户账号密码    │
                    │  · 验证用户身份       │
                    │  · 签发登录令牌       │
                    └──────────┬───────────┘
                               │
                    信任关系（预先配置）
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │  业务系统 A   │ │  业务系统 B   │ │  业务系统 C   │
     │  (SP)        │ │  (SP)        │ │  (SP)        │
     │  如：OA 系统  │ │  如：邮箱     │ │  如：代码仓库  │
     └──────────────┘ └──────────────┘ └──────────────┘
```

**① 用户（User）**

就是使用系统的人。用户不需要知道 SSO 的存在——他只知道"我登录了一次，其他系统都不需要再登了"。

**② 认证中心（Identity Provider，IdP）**

SSO 架构的**核心枢纽**。所有的用户身份验证都在这里完成。它负责：

- 存储和管理用户的账号、密码（或其他凭证）
- 验证用户身份（你是谁？）
- 登录成功后签发**令牌（Token）**，证明"这个用户已通过验证"
- 维护用户的登录状态

常见的 IdP 实现：企业自建的统一认证中心、Auth0、Keycloak、Okta、微信开放平台等。

**③ 业务系统（Service Provider，SP）**

就是用户实际要使用的应用（OA、邮箱、代码仓库等）。它自身**不做身份验证**，而是：

- 发现用户未登录时，将用户**重定向**到认证中心
- 接收认证中心签发的令牌
- **验证令牌的合法性**（签名是否正确、是否过期等）
- 验证通过后，让用户进入系统

### 4. SSO 的工作流程

把三个角色串起来，一次完整的 SSO 登录流程是这样的：

```
 用户第一次访问系统 A（未登录）
 ═══════════════════════════════════════════════════════════

 ① 用户 → 访问系统 A
 ② 系统 A → 检查：用户没有有效令牌 → 重定向到认证中心
 ③ 认证中心 → 显示登录页面
 ④ 用户 → 输入账号密码
 ⑤ 认证中心 → 验证通过 → 记录登录状态 → 签发令牌
 ⑥ 认证中心 → 携带令牌，重定向回系统 A
 ⑦ 系统 A → 验证令牌有效 → 用户登录成功 ✅


 用户随后访问系统 B（已在认证中心登录过）
 ═══════════════════════════════════════════════════════════

 ① 用户 → 访问系统 B
 ② 系统 B → 检查：用户没有有效令牌 → 重定向到认证中心
 ③ 认证中心 → 检测到用户已登录（有登录状态）
 ④ 认证中心 → 直接签发令牌（无需再次输入密码！）
 ⑤ 认证中心 → 携带令牌，重定向回系统 B
 ⑥ 系统 B → 验证令牌有效 → 用户登录成功 ✅
```

注意关键区别：**第二次访问时，用户在整个过程中没有看到任何登录页面**——认证中心发现你已经登录过了，直接给你签发了新令牌并跳回业务系统。在用户看来，就是"打开系统 B，直接就进去了"。

### 5. 这里的"令牌"到底是什么？

在上面的流程中，"令牌"是整个 SSO 体系的信物——认证中心用它来告诉业务系统："这个人我验过了，身份没问题。"

但令牌具体长什么样？用什么格式？怎么防伪造？业务系统怎么验证它？

这些问题的答案，就是接下来要讲的 **JWT**。

不过在讲 JWT 之前，我们先看看传统的方案——Session + Cookie——是怎么做的，以及它为什么在现代架构中越来越力不从心。

## 三、传统 Session 方案的局限

在 JWT 出现之前，Web 应用最常用的身份验证方案是 **Session + Cookie**。要理解 JWT 的价值，我们先看看这个"老方案"是怎么工作的，以及它在 SSO 场景下为什么越来越吃力。

### 1. Session + Cookie 的基本原理

HTTP 协议本身是**无状态的**——服务器处理完一个请求就"忘了"，下一个请求来的时候它不知道"你是谁"。Session 机制就是为了解决这个问题：

```
 首次登录
 ═══════════════════════════════════════════════════════

 ① 用户 → 发送账号密码到服务器
 ② 服务器 → 验证通过 → 在服务端内存中创建一条 Session 记录
    Session 数据：{ id: "abc123", user: "张三", role: "admin", ... }
 ③ 服务器 → 把 Session ID（"abc123"）通过 Set-Cookie 返回给浏览器
 ④ 浏览器 → 将 Cookie 存储在本地


 后续每次请求
 ═══════════════════════════════════════════════════════

 ① 浏览器 → 自动在请求头中携带 Cookie: session_id=abc123
 ② 服务器 → 用 session_id 查找 Session 记录 → 找到了！→ 知道你是"张三"
 ③ 服务器 → 正常返回数据
```

简单来说：**服务器记住你是谁（Session），浏览器负责带身份证号（Cookie 里的 Session ID）。**

这个方案在单体应用中工作得非常好。但当你想用它来实现 SSO 时，问题就开始出现了。

### 2. 问题一：Cookie 跨域不共享

Cookie 有一个严格的安全限制——**同源策略**：一个域名设置的 Cookie，其他域名无法读取。

```
 OA 系统：   oa.company.com       → 设置了 Cookie: session_id=abc123
 邮箱系统：  mail.company.com     → ❌ 读不到 oa.company.com 的 Cookie
 代码仓库：  git.other-vendor.com → ❌ 完全不同的域名，更读不到
```

你在 OA 系统登录后拿到的 Session Cookie，邮箱系统根本看不到。更别说 Cookie 完全不能跨顶级域名传递——如果你的业务系统分布在 `company.com` 和 `other-vendor.com` 两个域名下，Cookie 方案就彻底失效了。

> **有人会问**：能不能把 Cookie 设置在 `.company.com` 这个父域上，让所有子域共享？
>
> 可以，但只能解决**同一顶级域名**下的子域共享问题。一旦涉及跨域（不同顶级域名），这招就不管用了。而且把 Cookie 暴露给所有子域，本身也增加了安全风险。

### 3. 问题二：服务端 Session 存储与同步

Session 数据存在服务器内存里。单台服务器没问题，但现代应用通常是**多实例部署**（负载均衡）：

```
                    ┌──────────────┐
                    │   负载均衡器   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐  ┌────────┐  ┌────────┐
         │ 服务器 A │  │ 服务器 B │  │ 服务器 C │
         │ Session │  │ Session │  │ Session │
         │  存储   │  │  存储   │  │  存储   │
         └────────┘  └────────┘  └────────┘

 用户在服务器 A 上登录，Session 存在 A 的内存里。
 下一次请求被负载均衡器分配到服务器 B → B 的内存里没有这条 Session → 登录失效！
```

为了解决这个问题，你需要做 **Session 共享**：

| 方案 | 做法 | 代价 |
| :--- | :--- | :--- |
| 粘性会话（Sticky Session） | 负载均衡器把同一用户始终分到同一台服务器 | 负载不均衡，单点故障 |
| Session 复制 | 所有服务器之间同步 Session 数据 | 网络开销大，延迟高 |
| 集中存储（Redis） | 把 Session 存到 Redis 等共享存储中 | 增加外部依赖，Redis 成为单点 |

不管哪种方案，都增加了系统复杂度和运维成本。而且这还只是**一个应用**内部的问题——如果是 SSO 场景下多个独立系统要共享 Session，复杂度会成倍增长。

### 4. 问题三：不适合现代架构

现代 Web 开发的趋势是**前后端分离 + 微服务**：

```
 传统架构（Session 友好）           现代架构（Session 困难）
 ═══════════════════════           ═══════════════════════

 ┌─────────────────┐              ┌──────────┐
 │   单体服务器      │              │  前端 SPA │（React / Vue）
 │  前端 + 后端      │              └─────┬────┘
 │  + Session 存储   │                    │ HTTP API
 └─────────────────┘              ┌──────┴──────────────────┐
                                  │     API 网关             │
 浏览器直接和一个服务器交互，       └──┬─────┬─────┬─────┬───┘
 Session + Cookie 工作得很好。        │     │     │     │
                                  ┌──┴┐ ┌─┴─┐ ┌┴──┐ ┌┴──┐
                                  │用户│ │订单│ │支付│ │消息│
                                  │服务│ │服务│ │服务│ │服务│
                                  └───┘ └───┘ └───┘ └───┘

                                  多个独立服务，
                                  谁来存 Session？谁来查 Session？
```

在微服务架构中：

- **每个服务都是独立进程**，没有共享内存，Session 没地方存
- **前后端分离**后，前端可能部署在 CDN 上，和后端 API 不在同一个域
- **移动端 / 小程序**等客户端根本不支持 Cookie 机制
- 服务之间互相调用时，Session 无法传递

### 5. 小结：我们需要一种新方案

Session + Cookie 的核心问题可以归结为两个字：**有状态**。

- 服务端要**存储** Session 数据 → 带来存储和同步成本
- 客户端要通过 **Cookie** 传递 Session ID → 受同源策略限制

那有没有一种方案，能让"令牌本身就包含了所有需要的信息"，服务端不需要存储任何状态、不依赖 Cookie 传递、任何系统拿到它都能独立验证？

有，这就是 **JWT（JSON Web Token）**——一种**无状态、自包含、可验证**的令牌方案。

## 四、JWT 是什么

### 1. 定义

**JWT（JSON Web Token）** 是一种开放标准（[RFC 7519](https://tools.ietf.org/html/rfc7519)），定义了一种**紧凑且自包含**的方式，用于在各方之间以 JSON 对象的形式安全传递信息。

一句话理解：

> **JWT 是一张"数字身份证"——把用户信息和防伪签名打包成一个字符串，谁拿到它都能独立验证真伪。**

它长这样（一整行字符串，这里为了展示做了换行）：

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
.
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IuW8oOS4iSIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTcxMDAwMDAwMCwiZXhwIjoxNzEwMDAzNjAwfQ
.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

看起来像一堆乱码，但其实有非常清晰的结构。

### 2. 三段式结构：Header.Payload.Signature

JWT 由三部分组成，用 `.`（英文句点）连接：

```
xxxxx.yyyyy.zzzzz
  │      │      │
  │      │      └── 第三部分：Signature（签名）
  │      └───────── 第二部分：Payload（载荷）
  └──────────────── 第一部分：Header（头部）
```

每一部分都是一个 JSON 对象经过 **Base64URL 编码**后的字符串（不是加密！是编码，可以解码还原）。

#### 📌 Part 1：Header（头部）

声明 Token 的类型和签名算法：

```json
{
  "alg": "HS256",    // 签名算法：HMAC SHA-256
  "typ": "JWT"       // 令牌类型：JWT
}
```

常见签名算法：

| 算法 | 类型 | 说明 |
| :--- | :--- | :--- |
| HS256 | 对称加密 | 用同一个密钥签名和验证，简单快速 |
| RS256 | 非对称加密 | 私钥签名、公钥验证，更安全，适合分布式场景 |
| ES256 | 非对称加密 | 椭圆曲线算法，签名更短 |

#### 📌 Part 2：Payload（载荷）

**实际要传递的数据**，包含若干"声明（Claims）"：

```json
{
  "sub": "1234567890",      // Subject：用户 ID
  "name": "张三",            // 自定义字段：用户名
  "role": "admin",          // 自定义字段：角色
  "iat": 1710000000,        // Issued At：签发时间
  "exp": 1710003600         // Expiration：过期时间（1 小时后）
}
```

JWT 标准预定义了一些常用声明（都是可选的）：

| 字段 | 全称 | 说明 |
| :--- | :--- | :--- |
| `iss` | Issuer | 签发者（谁签发的这个 Token） |
| `sub` | Subject | 主体（通常是用户 ID） |
| `aud` | Audience | 接收方（这个 Token 是给谁用的） |
| `exp` | Expiration Time | 过期时间（Unix 时间戳） |
| `iat` | Issued At | 签发时间 |
| `nbf` | Not Before | 生效时间 |
| `jti` | JWT ID | Token 唯一标识（可用于防重放） |

> ⚠️ **重要提醒**：Payload 只是 Base64 编码，**不是加密**！任何人拿到 JWT 都能解码出 Payload 内容。所以**绝对不要在 Payload 里放密码、身份证号等敏感信息**。

#### 📌 Part 3：Signature（签名）

**防篡改的关键**。用 Header 中声明的算法，对前两部分进行签名：

```
Signature = HMAC-SHA256(
    Base64URL(Header) + "." + Base64URL(Payload),
    secret_key    // 只有服务端知道的密钥
)
```

签名的作用：

```
 假设有人想篡改 Payload 中的角色：
 原始：{ "role": "user" }  →  篡改为：{ "role": "admin" }

 ① 篡改 Payload 后，Base64 编码变了
 ② 但篡改者没有 secret_key，无法生成正确的新签名
 ③ 服务端收到后，用 secret_key 重新计算签名
 ④ 计算结果和 Token 中的签名不一致 → 验证失败 ❌ → 拒绝请求
```

**签名保证了：Token 一旦签发，任何修改都会被发现。**

### 3. 代码示例

#### Python 生成与验证 JWT

```python
import jwt
import datetime

SECRET_KEY = "my-secret-key"  # 服务端密钥，绝不能泄露

# ========== 生成 JWT ==========

payload = {
    "sub": "user_001",                # 用户 ID
    "name": "张三",                    # 用户名
    "role": "admin",                  # 角色
    "iat": datetime.datetime.utcnow(),                        # 签发时间
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # 1 小时后过期
}

token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
print(f"生成的 JWT：{token}")
# 输出类似：eyJhbGciOiJIUzI1NiIs...


# ========== 验证 JWT ==========

try:
    decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    print(f"验证成功！用户信息：{decoded}")
    # {'sub': 'user_001', 'name': '张三', 'role': 'admin', ...}
except jwt.ExpiredSignatureError:
    print("Token 已过期！")
except jwt.InvalidTokenError:
    print("Token 无效！")
```

#### Node.js 生成与验证 JWT

```javascript
const jwt = require('jsonwebtoken');

const SECRET_KEY = 'my-secret-key';

// ========== 生成 JWT ==========

const token = jwt.sign(
  { sub: 'user_001', name: '张三', role: 'admin' },
  SECRET_KEY,
  { expiresIn: '1h' }  // 1 小时后过期
);
console.log('生成的 JWT：', token);


// ========== 验证 JWT ==========

try {
  const decoded = jwt.verify(token, SECRET_KEY);
  console.log('验证成功！用户信息：', decoded);
} catch (err) {
  console.log('Token 无效：', err.message);
}
```

### 4. JWT 的三大核心特性

总结 JWT 和传统 Session 的根本区别：

| 特性 | Session | JWT |
| :--- | :--- | :--- |
| **无状态** | ❌ 服务端要存储 Session 数据 | ✅ 服务端不存任何东西，验证签名即可 |
| **自包含** | ❌ Session ID 只是一个引用，数据在服务端 | ✅ Token 本身就包含了用户信息 |
| **可验证** | ❌ 必须回查服务端的 Session 存储 | ✅ 任何持有密钥的服务都能独立验证 |

用一个比喻来理解：

```
Session = 你去银行办业务，银行给你一个排队号（Session ID）。
          每次叫号时，银行要在系统里查你是谁、要办什么业务。
          银行系统挂了，你的号就废了。

JWT     = 你去银行办业务，银行给你一张盖了公章的介绍信（JWT）。
          上面写着你是谁、能办什么业务、有效期到什么时候。
          任何分行拿到这封信，只要验证公章是真的，就知道你是谁。
          不需要回总行查系统。
```

### 5. JWT 到底安不安全？

这是一个常见的困惑。我们拆开来看：

**JWT 保证的是"完整性"，不是"保密性"。**

- ✅ **防篡改**：任何对 Payload 的修改都会导致签名失败
- ✅ **防伪造**：没有密钥就无法生成合法的签名
- ❌ **不防窥视**：Payload 是 Base64 编码，谁都能解码看到内容

所以：

- JWT 适合传递"用户 ID、角色、权限"这类**不算机密但需要可信**的信息
- 绝对不要放"密码、身份证号、银行卡号"等**真正的机密**
- 如果需要保密，可以使用 **JWE（JSON Web Encryption）**，但这是另一个话题了

理解了 JWT 的结构和特性，接下来我们看看它是如何被用来实现单点登录的。

## 五、JWT 如何实现单点登录

### 1. 整体架构：认证中心 + JWT 令牌

在第二节中，我们讲了 SSO 的三个核心角色：**用户、认证中心（IdP）、业务系统（SP）**，也讲了它们之间的协作流程。但当时留了一个问题没回答：

> **认证中心签发的"令牌"到底是什么格式？业务系统怎么验证它？**

现在答案揭晓——**JWT 就是那个令牌**。

把 JWT 填入 SSO 架构，整个体系变成了这样：

```
                    ┌────────────────────────────────┐
                    │        认证中心（IdP）            │
                    │                                │
                    │  · 持有签名密钥（私钥 / Secret）  │
                    │  · 验证用户身份                  │
                    │  · 签发 JWT                     │
                    │  · 维护用户登录状态（Session）     │
                    └───────────────┬────────────────┘
                                    │
                          签发 JWT（含用户信息 + 签名）
                                    │
               ┌────────────────────┼────────────────────┐
               ▼                    ▼                    ▼
      ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
      │  业务系统 A    │    │  业务系统 B    │    │  业务系统 C    │
      │              │    │              │    │              │
      │  持有验证密钥  │    │  持有验证密钥  │    │  持有验证密钥  │
      │  （公钥 /     │    │  （公钥 /     │    │  （公钥 /     │
      │   Secret）    │    │   Secret）    │    │   Secret）    │
      │              │    │              │    │              │
      │  独立验证 JWT  │    │  独立验证 JWT  │    │  独立验证 JWT  │
      │  无需回查 IdP  │    │  无需回查 IdP  │    │  无需回查 IdP  │
      └──────────────┘    └──────────────┘    └──────────────┘
```

和传统 Session 方案相比，核心变化只有一个：

```
 传统方案                              JWT 方案
 ═══════════════════════              ═══════════════════════

 认证中心签发 Session ID               认证中心签发 JWT
       ↓                                    ↓
 业务系统拿到 Session ID               业务系统拿到 JWT
       ↓                                    ↓
 业务系统必须回查认证中心：             业务系统自己验证签名：
 "这个 ID 对应的用户是谁？"            "签名正确 → Token 没被篡改 → 可信"
       ↓                                    ↓
 认证中心返回用户信息                   直接从 Payload 读取用户信息
       ↓                                    ↓
 业务系统才知道用户身份                 业务系统立刻知道用户身份
```

**关键转变：从"我去问认证中心"变成了"我自己就能验"。**

这就是 JWT "无状态"特性在 SSO 中的核心价值——每个业务系统只需要持有一个验证密钥，就能独立判断 JWT 的真伪，不需要与认证中心保持实时通信。

> 💡 **关于密钥的选择**
>
> 在第四节我们提到 JWT 有对称加密（HS256）和非对称加密（RS256）两种签名算法。在 SSO 场景中，**非对称加密（RS256）是更好的选择**：
>
> | 方案 | 签名 | 验证 | 适用场景 |
> | :--- | :--- | :--- | :--- |
> | HS256（对称） | 用 Secret 签名 | 也用同一个 Secret 验证 | 单体应用，业务系统少 |
> | RS256（非对称） | 认证中心用**私钥**签名 | 业务系统用**公钥**验证 | SSO 场景，业务系统多 |
>
> 为什么非对称更好？因为**公钥可以放心分发**——即使被泄露，攻击者也无法伪造 JWT（伪造需要私钥）。而对称密钥一旦泄露给任何一个业务系统，攻击者就能伪造合法的 JWT。

### 2. 完整登录流程（图解）

理解了架构之后，我们用两个场景走一遍完整的 JWT SSO 登录流程。

#### 场景一：用户首次访问系统 A（未登录）

```
 用户                    系统 A                   认证中心（IdP）
  │                       │                          │
  │  ① 访问系统 A 首页     │                          │
  │──────────────────────▶│                          │
  │                       │                          │
  │                       │  ② 检查：没有有效 JWT      │
  │                       │     用户未登录             │
  │                       │                          │
  │  ③ 302 重定向到认证中心 │                          │
  │◀──────────────────────│                          │
  │     redirect_uri=系统A的回调地址                    │
  │                                                  │
  │  ④ 浏览器跳转到认证中心登录页                       │
  │─────────────────────────────────────────────────▶│
  │                                                  │
  │  ⑤ 认证中心显示登录表单                             │
  │◀─────────────────────────────────────────────────│
  │                                                  │
  │  ⑥ 用户输入账号密码，提交                           │
  │─────────────────────────────────────────────────▶│
  │                                                  │
  │                                                  │  ⑦ 验证账号密码
  │                                                  │  ⑧ 验证通过！
  │                                                  │  ⑨ 在认证中心记录登录状态
  │                                                  │     （Session / Cookie）
  │                                                  │  ⑩ 签发 JWT：
  │                                                  │     { sub: "user_001",
  │                                                  │       name: "张三",
  │                                                  │       role: "admin",
  │                                                  │       exp: 1小时后 }
  │                                                  │     + 用私钥签名
  │                                                  │
  │  ⑪ 302 重定向回系统 A（携带 JWT）                   │
  │◀─────────────────────────────────────────────────│
  │     https://a.com/callback?token=eyJhbG...        │
  │                                                  │
  │  ⑫ 浏览器跳转回系统 A   │                          │
  │──────────────────────▶│                          │
  │                       │                          │
  │                       │  ⑬ 从 URL 中提取 JWT      │
  │                       │  ⑭ 用公钥验证签名 → ✅ 有效 │
  │                       │  ⑮ 从 Payload 读取用户信息  │
  │                       │  ⑯ 将 JWT 返回给前端保存    │
  │                       │                          │
  │  ⑰ 登录成功！进入系统 A │                          │
  │◀──────────────────────│                          │
```

注意第 ⑨ 步：**认证中心在自己这里记录了用户的登录状态**。这一步至关重要——正是因为有这个记录，用户接下来访问系统 B 时才不需要再次输入密码。

#### 场景二：用户随后访问系统 B（已在认证中心登录过）

```
 用户                    系统 B                   认证中心（IdP）
  │                       │                          │
  │  ① 访问系统 B 首页     │                          │
  │──────────────────────▶│                          │
  │                       │                          │
  │                       │  ② 检查：没有有效 JWT      │
  │                       │     用户未登录（在系统B）   │
  │                       │                          │
  │  ③ 302 重定向到认证中心 │                          │
  │◀──────────────────────│                          │
  │                                                  │
  │  ④ 浏览器跳转到认证中心 │                          │
  │─────────────────────────────────────────────────▶│
  │     （浏览器自动携带认证中心的 Cookie）              │
  │                                                  │
  │                                                  │  ⑤ 检测到 Cookie
  │                                                  │     → 用户已登录！
  │                                                  │  ⑥ 无需显示登录页
  │                                                  │  ⑦ 直接签发新 JWT
  │                                                  │     （给系统 B 用）
  │                                                  │
  │  ⑧ 302 重定向回系统 B（携带新 JWT）                 │
  │◀─────────────────────────────────────────────────│
  │                                                  │
  │  ⑨ 浏览器跳转回系统 B   │                          │
  │──────────────────────▶│                          │
  │                       │                          │
  │                       │  ⑩ 验证 JWT 签名 → ✅ 有效 │
  │                       │  ⑪ 读取用户信息            │
  │                       │                          │
  │  ⑫ 登录成功！进入系统 B │                          │
  │◀──────────────────────│                          │
  │                       │                          │
  │     整个过程用户没有                                │
  │     看到任何登录页面！                              │
```

#### 关键差异：为什么系统 B 不需要再输密码？

对比两个场景，差别发生在**用户跳转到认证中心**的那一刻：

| 对比项 | 场景一（首次访问系统 A） | 场景二（随后访问系统 B） |
| :--- | :--- | :--- |
| 认证中心是否有登录态 | ❌ 没有 → 要显示登录页 | ✅ 有（场景一留下的）→ 跳过登录页 |
| 用户是否需要输入密码 | ✅ 需要 | ❌ 不需要 |
| 认证中心的操作 | 验证密码 → 记录登录态 → 签发 JWT | 检测到登录态 → 直接签发 JWT |
| 用户感知 | 看到了登录页，输入了密码 | 页面闪了一下，直接进入系统 |

秘密就在于：**认证中心自己维护了一个登录状态**（通常是认证中心域名下的 Cookie/Session）。虽然系统 A 和系统 B 是不同的域名、无法共享 Cookie，但它们都会将用户**重定向到同一个认证中心**。浏览器访问认证中心时，会自动携带认证中心域名下的 Cookie——这就让认证中心能识别出"这个用户之前已经登录过了"。

> 🔑 **一句话总结 SSO 的"魔法"**：
>
> 不同业务系统之间确实无法直接共享登录状态。但它们不需要——它们共享的是**同一个认证中心**，而浏览器与认证中心之间的 Cookie 是天然共通的。认证中心就像一个"中间人"，把"用户已登录"这个事实，通过签发 JWT 的方式"翻译"给每个业务系统。

### 3. Token 怎么传递：从认证中心到业务系统

在上面的流程图中，认证中心签发了 JWT 之后，需要把它"送回"给业务系统。这一步看似简单，实际上有不同的实现方式，各有优劣。

#### 方式一：授权码模式（Authorization Code Flow）—— 推荐

这是**最安全**的方式，也是 OAuth 2.0 / OpenID Connect 中最推荐的标准流程：

```
 用户浏览器                业务系统后端               认证中心
  │                         │                         │
  │  ① 重定向到认证中心      │                         │
  │─────────────────────────────────────────────────▶ │
  │                                                   │
  │  ② 登录成功后，认证中心   │                         │
  │     返回一个"授权码"      │                         │
  │◀───────────────────────────────────────────────── │
  │  redirect: https://a.com/callback?code=abc123     │
  │                                                   │
  │  ③ 浏览器携带授权码       │                         │
  │     跳转到业务系统        │                         │
  │─────────────────────── ▶│                         │
  │                         │                         │
  │                         │  ④ 业务系统用授权码       │
  │                         │     + 自己的 client_secret│
  │                         │     向认证中心换 JWT      │
  │                         │────────────────────────▶│
  │                         │                         │
  │                         │  ⑤ 认证中心验证授权码    │
  │                         │     返回 JWT             │
  │                         │◀────────────────────────│
  │                         │                         │
  │  ⑥ 业务系统将 JWT        │                         │
  │     返回给前端            │                         │
  │◀────────────────────────│                         │
```

**为什么更安全？** 因为 JWT 从来没有出现在浏览器的 URL 中——它是在业务系统后端与认证中心之间通过服务器间通信传递的。即使授权码被截获，没有 `client_secret` 也无法换取 JWT。

#### 方式二：隐式模式（Implicit Flow）—— 简单但不推荐

认证中心直接将 JWT 放在重定向 URL 中返回：

```
 认证中心登录成功后，直接重定向：

 https://a.com/callback#token=eyJhbGciOiJSUzI1NiIs...
                        │
                        └── JWT 直接暴露在 URL 中
```

这种方式更简单，前端可以直接从 URL 中提取 JWT。但**安全性较差**：
- JWT 会出现在浏览器历史记录中
- 可能被 Referer 头泄露给第三方
- 没有 `client_secret` 的保护

> ⚠️ **实践建议**：OAuth 2.1 草案已经**废弃了隐式模式**。新项目应该始终使用授权码模式（配合 PKCE 扩展，更适合纯前端应用）。

#### 为什么不再依赖 Cookie？

回顾第三节提到的 Session 方案的第一个大问题——**Cookie 跨域不共享**。JWT 方案巧妙地绕开了这个限制：

```
 Session 方案                        JWT 方案
 ═══════════════════════             ═══════════════════════

 登录状态靠 Cookie 传递               登录状态靠 JWT 传递
       ↓                                   ↓
 Cookie 受同源策略限制                JWT 不依赖 Cookie
 oa.company.com 的 Cookie            JWT 可以放在：
 mail.company.com 读不到              · URL 参数（临时传递）
       ↓                             · Authorization 请求头
 跨域 = 失败 ❌                       · localStorage / 内存
                                           ↓
                                     跨域 = 没问题 ✅
```

**JWT 作为一个普通的字符串，可以通过任何方式传递**——URL 参数、HTTP Header、请求体……它完全不依赖浏览器的 Cookie 机制，自然也就不受同源策略的限制。这正是 JWT 在 SSO 场景中替代 Session 的第一个关键优势。

### 4. Token 怎么存储：客户端保存策略

JWT 从认证中心传递到业务系统后，最终会到达**用户的浏览器**。前端需要把它保存起来，以便后续每次请求都能携带。

但 Token 存在哪里，直接决定了安全性。存储方式选不好，可能让整个 SSO 系统前功尽弃。

#### 四种常见方案

**① localStorage**

```javascript
// 存储
localStorage.setItem('access_token', jwt);

// 读取
const token = localStorage.getItem('access_token');

// 请求时携带
fetch('/api/data', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

- ✅ 持久存储，页面刷新、关闭浏览器后重新打开都还在
- ✅ 使用简单，API 友好
- ❌ **易受 XSS 攻击**：如果页面存在 XSS 漏洞，攻击者的恶意脚本可以直接用 `localStorage.getItem()` 读走 Token

**② sessionStorage**

```javascript
sessionStorage.setItem('access_token', jwt);
```

- ✅ 标签页级别隔离，关闭标签页即清除
- ✅ 比 localStorage 略安全（窗口关闭即失效）
- ❌ 同样**易受 XSS 攻击**
- ❌ 新开标签页需要重新登录（体验差）

**③ HttpOnly Cookie**

```
// 服务端设置（用户无法通过 JS 操作这个 Cookie）
Set-Cookie: access_token=eyJhbG...; HttpOnly; Secure; SameSite=Strict; Path=/
```

- ✅ **前端 JavaScript 完全无法读取**——XSS 攻击者拿不到 Token
- ✅ 浏览器自动在每次请求中携带
- ❌ 需要处理 **CSRF（跨站请求伪造）** 问题（可用 SameSite 属性缓解）
- ❌ 回到了"Cookie"的老路——跨域场景需要额外配置 CORS

> 💡 注意：这里用 HttpOnly Cookie 存储 JWT，和传统的"Session + Cookie"方案是不同的。传统方案 Cookie 里存的是 Session ID（需要服务端回查），这里存的是**自包含的 JWT**（服务端直接验证签名）。本质上仍然是无状态的。

**④ 内存变量（JavaScript 变量）**

```javascript
// 存在内存中（比如 React 的 state 或全局变量）
let accessToken = null;

function setToken(jwt) { accessToken = jwt; }
function getToken() { return accessToken; }
```

- ✅ **最安全**——不存储在任何持久化介质中，XSS 攻击也难以获取
- ❌ 页面刷新即丢失，用户需要重新走一遍认证流程
- ❌ 适合配合"静默刷新"使用（后面会讲）

#### 方案对比

| 存储方式 | 持久性 | XSS 防护 | CSRF 防护 | 适用场景 |
| :--- | :--- | :--- | :--- | :--- |
| localStorage | ✅ 持久 | ❌ 易被窃取 | ✅ 不自动发送 | 安全要求不高的内部系统 |
| sessionStorage | ⚠️ 标签页级 | ❌ 易被窃取 | ✅ 不自动发送 | 临时性会话 |
| HttpOnly Cookie | ✅ 持久 | ✅ JS 不可读 | ❌ 需额外处理 | 安全要求高的生产环境 |
| 内存变量 | ❌ 刷新丢失 | ✅ 难以窃取 | ✅ 不自动发送 | 高安全场景 + 静默刷新 |

#### 推荐方案

对于大多数生产环境，推荐采用**组合策略**：

```
 推荐方案：HttpOnly Cookie + 内存变量
 ═══════════════════════════════════════════════════

 Access Token  → 存在内存变量中（短期，如 15 分钟）
                  · 每次请求通过 Authorization Header 携带
                  · 页面刷新后丢失，通过 Refresh Token 重新获取

 Refresh Token → 存在 HttpOnly Cookie 中（长期，如 7 天）
                  · JS 不可读，防 XSS
                  · 仅在刷新 Token 时发送给认证中心
                  · 配合 Secure + SameSite 属性
```

这种组合兼顾了安全性和用户体验：Access Token 在内存中最安全，丢失了可以用 HttpOnly Cookie 里的 Refresh Token 静默刷新——用户无感知。

### 5. Token 怎么使用：业务系统如何验证

JWT 存好了，接下来每次用户请求业务系统的 API 时，都需要**携带 JWT** 来证明自己的身份。

#### 携带方式：Authorization Header

业界标准做法是将 JWT 放在 HTTP 请求头的 `Authorization` 字段中：

```
GET /api/user/profile HTTP/1.1
Host: a.company.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
```

`Bearer` 是一种认证方案类型，表示"持有者令牌"——谁持有这个 Token，谁就是合法用户。

#### 验证流程：三步完成

业务系统收到请求后，验证 JWT 只需要三步，**全程不需要与认证中心通信**：

```
 业务系统收到请求
  │
  ▼
 ┌────────────────────────────────────────────┐
 │  第一步：验证签名                            │
 │                                            │
 │  用公钥 / Secret 重新计算签名                │
 │  对比 Token 中的签名                        │
 │                                            │
 │  签名不一致？→ 拒绝！Token 被篡改 ❌          │
 └─────────────────────┬──────────────────────┘
                       │ 签名一致 ✅
                       ▼
 ┌────────────────────────────────────────────┐
 │  第二步：检查有效期                          │
 │                                            │
 │  读取 Payload 中的 exp 字段                  │
 │  和当前时间对比                              │
 │                                            │
 │  已过期？→ 拒绝！Token 失效 ❌               │
 └─────────────────────┬──────────────────────┘
                       │ 未过期 ✅
                       ▼
 ┌────────────────────────────────────────────┐
 │  第三步：提取用户信息                        │
 │                                            │
 │  从 Payload 中读取：                        │
 │  · sub → 用户 ID                           │
 │  · name → 用户名                           │
 │  · role → 角色权限                          │
 │                                            │
 │  验证通过！用户身份确认 ✅                    │
 └────────────────────────────────────────────┘
```

#### 代码示例：业务系统验证中间件

**Node.js（Express）**

```javascript
const jwt = require('jsonwebtoken');
const PUBLIC_KEY = fs.readFileSync('public_key.pem'); // 认证中心公钥

// JWT 验证中间件
function authMiddleware(req, res, next) {
  // 1. 从请求头提取 Token
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: '未提供 Token' });
  }
  const token = authHeader.split(' ')[1];

  try {
    // 2. 验证签名 + 检查过期时间（jwt.verify 自动完成）
    const decoded = jwt.verify(token, PUBLIC_KEY, { algorithms: ['RS256'] });

    // 3. 将用户信息附加到请求对象上
    req.user = {
      id: decoded.sub,       // "user_001"
      name: decoded.name,    // "张三"
      role: decoded.role     // "admin"
    };

    next(); // 验证通过，继续处理请求
  } catch (err) {
    if (err.name === 'TokenExpiredError') {
      return res.status(401).json({ error: 'Token 已过期' });
    }
    return res.status(401).json({ error: 'Token 无效' });
  }
}

// 使用中间件保护 API
app.get('/api/user/profile', authMiddleware, (req, res) => {
  res.json({ message: `欢迎回来，${req.user.name}！` });
});
```

**Python（Flask）**

```python
import jwt
from functools import wraps
from flask import request, jsonify

PUBLIC_KEY = open('public_key.pem').read()

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. 提取 Token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': '未提供 Token'}), 401

        token = auth_header.split(' ')[1]

        try:
            # 2. 验证签名 + 过期时间
            decoded = jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])
            # 3. 附加用户信息
            request.user = decoded
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token 已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token 无效'}), 401

        return f(*args, **kwargs)
    return decorated

@app.route('/api/user/profile')
@auth_required
def profile():
    return jsonify({'message': f'欢迎回来，{request.user["name"]}！'})
```

#### 核心价值：为什么不需要回查认证中心？

回顾第三节提到的 Session 方案的第二个问题——**Session 存储与同步**。JWT 方案彻底消除了这个问题：

```
 Session 方案                         JWT 方案
 ═══════════════════════              ═══════════════════════

 业务系统 A 收到请求                   业务系统 A 收到请求
       ↓                                    ↓
 拿着 Session ID                      拿着 JWT
 去 Redis / 认证中心查询              用本地公钥验证签名
       ↓                                    ↓
 网络请求！有延迟！                     纯计算！微秒级！
 Redis 挂了就挂了！                    无外部依赖！
       ↓                                    ↓
 查到用户信息                          直接读 Payload
       ↓                                    ↓
 处理请求                              处理请求
```

**每个业务系统都是自给自足的**——只要持有公钥，就能独立完成身份验证。不需要共享 Session 存储、不需要 Redis、不需要网络请求。这使得 JWT 天然适合微服务架构和分布式部署。

### 6. Token 刷新机制：Access Token + Refresh Token

#### 矛盾：安全性 vs 用户体验

JWT 签发后就不可修改，唯一的"失效"手段是**过期时间（exp）**。这就产生了一个两难问题：

```
 过期时间设得短（如 15 分钟）          过期时间设得长（如 7 天）
 ═══════════════════════              ═══════════════════════

 ✅ 安全：即使 Token 泄露，             ❌ 不安全：Token 泄露后，
    攻击者只有 15 分钟窗口                 攻击者可以用 7 天

 ❌ 体验差：用户每 15 分钟               ✅ 体验好：用户一周内
    就要重新登录一次                        不需要重新登录
```

怎么办？**鱼与熊掌兼得的方案——双 Token 机制。**

#### 双 Token 机制

不用一个 Token，用两个：

| Token 类型 | 用途 | 有效期 | 存储位置 |
| :--- | :--- | :--- | :--- |
| **Access Token** | 访问业务 API，证明用户身份 | 短（15 分钟~1 小时） | 内存变量 |
| **Refresh Token** | 用来换取新的 Access Token | 长（7 天~30 天） | HttpOnly Cookie |

Access Token 过期了，不需要用户重新登录——前端用 Refresh Token 去认证中心"续命"，拿到一个新的 Access Token，全程用户无感知。

#### 刷新流程

```
 用户浏览器                   业务系统                  认证中心
  │                            │                         │
  │  ① 请求 API（携带 Access Token）                      │
  │───────────────────────────▶│                         │
  │                            │                         │
  │                            │  ② 验证 Access Token     │
  │                            │     → 已过期！❌          │
  │                            │                         │
  │  ③ 返回 401 Unauthorized   │                         │
  │◀───────────────────────────│                         │
  │                            │                         │
  │  ④ 前端检测到 401                                     │
  │     自动发起刷新请求                                    │
  │     （携带 Refresh Token）                              │
  │──────────────────────────────────────────────────────▶│
  │                                                       │
  │                                                       │  ⑤ 验证 Refresh Token
  │                                                       │     → 有效！✅
  │                                                       │  ⑥ 签发新 Access Token
  │                                                       │    （可选：签发新 Refresh Token）
  │                                                       │
  │  ⑦ 返回新的 Access Token                               │
  │◀──────────────────────────────────────────────────────│
  │                                                       │
  │  ⑧ 用新 Access Token 重试原来的请求                     │
  │───────────────────────────▶│                         │
  │                            │                         │
  │                            │  ⑨ 验证通过 ✅            │
  │                            │                         │
  │  ⑩ 返回数据                 │                         │
  │◀───────────────────────────│                         │
  │                                                       │
  │     整个过程用户完全无感知！                               │
```

#### 静默刷新的实现思路

前端可以通过 HTTP 拦截器自动处理 Token 刷新，用户完全无感知：

```javascript
// Axios 拦截器实现静默刷新
let isRefreshing = false;
let pendingRequests = [];  // 刷新期间暂存的请求

axios.interceptors.response.use(
  response => response,   // 正常响应直接返回
  async error => {
    const originalRequest = error.config;

    // 收到 401 且不是刷新请求本身
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (!isRefreshing) {
        isRefreshing = true;

        try {
          // 用 Refresh Token 换新的 Access Token
          const { data } = await axios.post('/auth/refresh', {}, {
            withCredentials: true  // 自动携带 HttpOnly Cookie
          });

          // 更新内存中的 Access Token
          setAccessToken(data.access_token);

          // 重试所有暂存的请求
          pendingRequests.forEach(cb => cb(data.access_token));
          pendingRequests = [];

          // 重试当前请求
          originalRequest.headers['Authorization'] = `Bearer ${data.access_token}`;
          return axios(originalRequest);
        } catch (refreshError) {
          // Refresh Token 也失效了 → 跳转登录页
          window.location.href = '/login';
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      } else {
        // 已经在刷新中，将请求暂存，等刷新完成后重试
        return new Promise(resolve => {
          pendingRequests.push(newToken => {
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
            resolve(axios(originalRequest));
          });
        });
      }
    }

    return Promise.reject(error);
  }
);
```

> 💡 **为什么 Refresh Token 更安全？**
>
> 你可能会问：Refresh Token 的有效期更长，不是更容易被攻击吗？实际上安全性由存储方式保证：
>
> - Refresh Token 存在 **HttpOnly Cookie** 中 → JavaScript 无法读取 → XSS 攻击拿不到
> - Refresh Token **只发送给认证中心**的 `/auth/refresh` 接口 → 不会被业务系统的漏洞暴露
> - 认证中心可以维护一个 Refresh Token **黑名单** → 发现异常立即吊销
> - 每次刷新可以采用 **Refresh Token 轮换（Rotation）** → 旧 Token 用过即废

### 7. 回顾：JWT 如何逐一解决 Session 方案的三大问题

走完了整个流程，我们回到第三节提出的三大问题，看看 JWT 是如何逐一化解的：

| 问题 | Session + Cookie 方案 | JWT 方案 | 对应章节 |
| :--- | :--- | :--- | :--- |
| **① Cookie 跨域不共享** | Cookie 受同源策略限制，跨域名无法传递登录状态 | JWT 是普通字符串，通过 Authorization Header 传递，不受同源策略限制 | 5.3 Token 传递 |
| **② 服务端 Session 存储与同步** | 多实例部署需要共享 Session（Redis / 粘性会话），认证中心成为每次请求的瓶颈 | JWT 自包含用户信息，业务系统用公钥独立验证，无需任何外部存储或网络请求 | 5.5 Token 验证 |
| **③ 不适合现代架构** | 前后端分离、微服务、移动端都不方便使用 Cookie + Session | JWT 是无状态令牌，可在任何客户端（浏览器/App/小程序）和任何服务间传递和验证 | 5.4 + 5.5 |

用一张图总结 JWT SSO 的全貌：

```
 ┌─────────────────────────────────────────────────────────────┐
 │                    JWT SSO 全景图                            │
 ├─────────────────────────────────────────────────────────────┤
 │                                                             │
 │   用户登录一次                                               │
 │       ↓                                                     │
 │   认证中心签发 JWT（私钥签名，含用户信息 + 过期时间）           │
 │       ↓                                                     │
 │   前端保存：Access Token（内存）+ Refresh Token（HttpOnly）   │
 │       ↓                                                     │
 │   访问任意业务系统：Authorization: Bearer <JWT>               │
 │       ↓                                                     │
 │   业务系统独立验证：公钥验签 → 读取用户信息 → 放行              │
 │       ↓                                                     │
 │   Access Token 过期？→ Refresh Token 静默刷新 → 用户无感      │
 │       ↓                                                     │
 │   Refresh Token 也过期？→ 重新登录                            │
 │                                                             │
 └─────────────────────────────────────────────────────────────┘
```

> 🎯 **一句话总结**：
>
> JWT 把"我是谁"这个信息**从服务端的内存里解放出来**，打包成一个可携带、可验证、防篡改的令牌，让每个业务系统都能独立确认用户身份——这就是 JWT 实现单点登录的本质。

## 六、JWT SSO 的优势与风险

任何技术方案都不是银弹。在决定是否采用 JWT 实现 SSO 之前，你需要清楚地了解它的优势和潜在风险。

### 1. 五大优势

| 优势 | 说明 |
| :--- | :--- |
| **无状态，易扩展** | 服务端不存储任何会话数据，新增业务系统只需配置公钥即可接入，水平扩展无压力 |
| **跨域友好** | 不依赖 Cookie，通过 HTTP Header 传递，天然支持跨域、跨平台（Web/App/小程序） |
| **去中心化验证** | 每个业务系统独立验证 JWT，不需要每次请求都回查认证中心，降低了认证中心的压力 |
| **性能优异** | 验证 JWT 是纯粹的密码学计算（微秒级），相比网络请求查询 Session（毫秒级）快了几个数量级 |
| **标准化** | JWT 是开放标准（RFC 7519），各语言都有成熟的库支持，生态完善 |

### 2. 四大风险与应对

#### 风险一：Token 无法主动吊销

这是 JWT 最大的"硬伤"。JWT 一旦签发，在过期之前就是有效的——服务端没有"踢人下线"的能力。

```
 场景：管理员发现某账号被盗，想立即封禁

 Session 方案：删掉服务端的 Session 记录 → 立即失效 ✅
 JWT 方案：   Token 在用户手里，服务端无法销毁 → 直到过期才失效 ❌
```

**应对策略：**

| 策略 | 做法 | 代价 |
| :--- | :--- | :--- |
| 短过期时间 | Access Token 设置 15 分钟过期 | 需要配合 Refresh Token |
| Token 黑名单 | 认证中心维护一个已吊销 Token 的列表，业务系统验证时检查 | 引入了状态，部分牺牲了"无状态"优势 |
| 版本号机制 | 用户表中维护一个 `token_version`，签发 JWT 时写入。修改密码/封禁时递增版本号，验证时对比 | 需要查库，但只需查一个字段 |

#### 风险二：Token 体积较大

JWT 包含了完整的用户信息 + 签名，体积远大于一个 Session ID：

```
 Session ID：  abc123def456        （约 20 字节）
 JWT Token：   eyJhbGciOi...       （通常 500~1000 字节）
```

每次 HTTP 请求都要携带这个 Token，会增加网络传输开销。在移动端弱网环境下尤其需要注意。

**应对策略：**
- Payload 中只放**必要信息**（用户 ID、角色），不要放整个用户资料
- 详细的用户信息让业务系统按需从用户服务获取
- 使用压缩算法或更紧凑的签名算法（如 ES256）

#### 风险三：Payload 信息泄露

第四节讲过，JWT 的 Payload 只是 Base64 编码，**不是加密**。任何人截获 JWT 都能解码看到内容。

```javascript
// 任何人都能这样解码你的 JWT
const payload = JSON.parse(atob('eyJzdWIiOiIxMjM0NTY3ODkwIn0'));
// { "sub": "1234567890", "name": "张三", "role": "admin" }
```

**应对策略：**
- Payload 中**绝不放**密码、身份证号、手机号等敏感信息
- 必须传递敏感信息时，使用 **JWE（JSON Web Encryption）** 加密
- 始终使用 **HTTPS** 传输，防止中间人截获

#### 风险四：密钥管理

整个 JWT 体系的安全性依赖于**密钥不泄露**。私钥泄露 = 攻击者可以伪造任意用户的合法 JWT。

**应对策略：**
- 使用**非对称加密（RS256）**，私钥只在认证中心，公钥可以安全分发
- 密钥存储在**专用的密钥管理服务**（AWS KMS、HashiCorp Vault 等）中
- 定期**轮换密钥**，旧密钥签发的 JWT 自然过期后失效
- 配置多个密钥（JWKS），支持平滑过渡

### 3. 小结：JWT 不是万能的

> ⚠️ **选择 JWT 前请思考**：
>
> - 如果你的系统需要**频繁踢人下线**（如金融系统） → Token 黑名单是必须的，此时 JWT 的"无状态"优势会打折扣
> - 如果你的系统是**单体应用、不涉及跨域** → Session + Redis 可能更简单直接
> - 如果你的系统是**微服务 + 多端 + 跨域** → JWT 是最佳选择

JWT SSO 的本质是一种**折中**：用"无法主动吊销"换取了"无状态、去中心化、跨域友好"。理解了这个折中，你才能在实际项目中做出正确的技术选型。

## 七、实战要点

理论讲完了，当你真正在项目中落地 JWT SSO 时，以下是需要特别注意的关键检查清单。

### 1. 始终使用 HTTPS

JWT 本身不加密，如果在 HTTP 明文传输中被截获，攻击者可以直接使用被盗的 Token。

```
 ❌ http://api.company.com/user   →  Token 在网络中裸奔
 ✅ https://api.company.com/user  →  TLS 加密，即使截获也无法解密
```

**没有 HTTPS 的 JWT 就像没有信封的信件——内容一目了然。**

### 2. 密钥管理规范

| 要点 | 说明 |
| :--- | :--- |
| 使用 RS256 | SSO 场景优先使用非对称加密，私钥只在认证中心 |
| 密钥不入代码 | 通过环境变量或密钥管理服务（Vault / KMS）注入 |
| 定期轮换 | 建议每 90 天轮换一次签名密钥 |
| JWKS 端点 | 认证中心暴露 `/.well-known/jwks.json`，业务系统自动获取最新公钥 |

### 3. Payload 精简设计

```json
// ✅ 推荐：只放必要信息
{
  "sub": "user_001",
  "role": "admin",
  "aud": "system-a",
  "exp": 1710003600,
  "iat": 1710000000,
  "jti": "unique-token-id"
}

// ❌ 不推荐：塞太多东西
{
  "sub": "user_001",
  "name": "张三",
  "email": "zhangsan@company.com",
  "phone": "13800138000",       // 敏感！
  "avatar": "https://...",       // 没必要
  "department": "技术部",
  "permissions": ["read", "write", "delete", "admin", ...]  // 太长
}
```

原则：**Payload 放"身份标识 + 最小权限信息"，其余信息让业务系统按需查询。**

### 4. Token 存储安全

```
 生产环境推荐配置
 ═══════════════════════════════════════════

 Access Token  → 内存变量（JavaScript）
                  有效期：15 分钟
                  传递：Authorization: Bearer <token>

 Refresh Token → HttpOnly + Secure + SameSite=Strict Cookie
                  有效期：7 天
                  传递：仅发往认证中心 /auth/refresh
```

### 5. Token 刷新策略

- ✅ **主动刷新**：在 Access Token 过期前 1~2 分钟就发起刷新（避免用户遭遇 401）
- ✅ **Refresh Token 轮换**：每次刷新签发新的 Refresh Token，旧的立即作废
- ✅ **并发控制**：多个请求同时发现 Token 过期时，只发起一次刷新（参考第五节代码）
- ❌ **不要**用 Access Token 去刷新 Access Token

### 6. Token 吊销方案

根据业务安全级别选择：

```
 安全级别低（内部工具）          安全级别高（金融/支付）
 ═══════════════════════       ═══════════════════════

 短过期时间即可                  短过期 + Token 黑名单
 Access Token: 1h               Access Token: 15min
 不需要主动吊销                  Redis 黑名单 + 版本号机制
                                修改密码时强制失效所有 Token
```

### 7. 单点登出（SLO）

SSO 有登录就要有登出。JWT 的无状态特性让登出变得有些棘手：

```
 用户在系统 A 点击"退出登录"
  │
  ├── ① 清除系统 A 本地的 Token  ← 简单
  │
  ├── ② 通知认证中心销毁登录状态  ← 需要请求认证中心
  │
  └── ③ 通知系统 B、C 也清除 Token ← 最难！
       │
       ├── 方案一：前端频道（BroadcastChannel / iframe）
       │            各系统监听登出事件，主动清除 Token
       │
       ├── 方案二：后端通知（Back-Channel Logout）
       │            认证中心向各业务系统推送登出通知
       │
       └── 方案三：短过期 + 不主动通知
                    Access Token 15 分钟后自然失效
                    Refresh Token 被认证中心拒绝
```

### 8. 监控与告警

上线后别忘了监控：

- 📊 **Token 签发量**：异常暴涨可能意味着刷新风暴或攻击
- 🔍 **验证失败率**：签名失败激增可能意味着密钥泄露或中间人攻击
- ⏰ **刷新频率**：某用户频繁刷新可能是 Token 被盗用（攻击者和正常用户竞争刷新）
- 🌍 **异地登录**：同一 Token 在不同 IP / 地区使用，触发风控

## 八、总结

### 全文知识地图

```
 一、从日常场景说起
  │   Google 一次登录，多处通行 → 引出 SSO 概念
  │
  ▼
 二、单点登录（SSO）是什么
  │   定义 → 痛点 → 三个角色（用户/IdP/SP）→ 工作流程
  │   遗留问题："令牌"到底是什么？
  │
  ▼
 三、传统 Session 方案的局限
  │   三大问题：Cookie 跨域 / Session 存储同步 / 不适合现代架构
  │   结论：需要一种无状态的新方案
  │
  ▼
 四、JWT 是什么
  │   三段式结构（Header.Payload.Signature）
  │   核心特性：无状态、自包含、可验证
  │   代码示例：生成与验证 JWT
  │
  ▼
 五、JWT 如何实现单点登录  ← 核心章节
  │   整体架构 → 完整流程 → Token 传递/存储/验证/刷新
  │   逐一解决 Session 方案的三大问题
  │
  ▼
 六、JWT SSO 的优势与风险
  │   五大优势 vs 四大风险（含应对策略）
  │   本质是"无法主动吊销"换"无状态去中心化"的折中
  │
  ▼
 七、实战要点
  │   8 条关键检查清单：HTTPS / 密钥管理 / 存储安全 / 刷新策略 / SLO / 监控
  │
  ▼
 八、总结 ← 你在这里
```

### 核心概念速查表

| 概念 | 一句话解释 |
| :--- | :--- |
| **SSO** | 一次登录，多处通行 |
| **IdP** | 认证中心，负责验证用户身份并签发令牌 |
| **SP** | 业务系统，接收并验证令牌 |
| **JWT** | 自包含、防篡改的数字身份证（Header.Payload.Signature） |
| **Access Token** | 短期令牌，用于访问业务 API |
| **Refresh Token** | 长期令牌，用于换取新的 Access Token |
| **RS256** | 非对称签名算法，私钥签名 + 公钥验证，适合 SSO |
| **授权码模式** | 最安全的 Token 传递方式，JWT 不暴露在 URL 中 |
| **静默刷新** | Access Token 过期后自动用 Refresh Token 续期，用户无感知 |

### 最后

从 Google 的一次登录畅通所有服务，到企业内部的统一认证中心，SSO 的核心目标始终是：**让用户少输一次密码，让系统多一份安全。**

JWT 用一种优雅的方式实现了这个目标——把用户身份打包成一个可验证的令牌，让每个系统都能独立确认"你是谁"，不需要集中式的状态存储，不受域名的限制。

当然，没有完美的方案。JWT 的"签发即有效"特性既是它最大的优势（无状态），也是它最大的挑战（无法即时吊销）。理解这个折中，根据你的业务场景选择合适的补充策略（短过期 + 黑名单 + Refresh Token 轮换），就能在安全性和用户体验之间找到最佳平衡点。

> 🎯 **记住这句话**：
>
> **SSO 解决的是"登录一次"的问题，JWT 解决的是"怎么证明你登录过"的问题。两者结合，就是现代 Web 身份认证的核心范式。**

---

*全文完。*