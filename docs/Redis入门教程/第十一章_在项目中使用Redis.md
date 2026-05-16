# 第十一章 在项目中使用 Redis

前面章节主要用 **redis-cli** 或桌面工具操作 Redis。实际开发里，应用会通过各语言的客户端库连接 Redis，完成缓存、会话、计数等任务。本章用三种常见技术栈给出**最小可运行**的「连接 → 读写」示例，并汇总跨语言的通用注意点。

> **前置条件**：本机或远程已启动 Redis（默认 `127.0.0.1:6379`），且防火墙/安全组允许访问。

---

## 11.1 Java —— Spring Boot 整合 Redis

### 依赖引入

在 `pom.xml` 中加入（版本由 Spring Boot 的 BOM 管理，一般无需手写版本号）：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

### application.yml 配置

```yaml
spring:
  data:
    redis:
      host: 127.0.0.1
      port: 6379
      # password: your-password   # 有密码时取消注释
      database: 0
      timeout: 2000ms
```

### RedisTemplate 基本用法

Spring 会注入 `RedisTemplate<String, Object>`（或 `StringRedisTemplate` 专管字符串）。常用 API：

| 方法 | 含义 |
|------|------|
| `opsForValue()` | 字符串 / 简单对象（常用缓存） |
| `opsForHash()` | Hash |
| `opsForList()` | List |
| `opsForSet()` | Set |
| `opsForZSet()` | 有序集合 |

### 示例：缓存用户信息

```java
@Service
public class UserCacheService {

    private final RedisTemplate<String, Object> redisTemplate;

    public UserCacheService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    private static final String KEY_USER = "app:user:%d";

    public void cacheUser(Long id, String json) {
        redisTemplate.opsForValue().set(String.format(KEY_USER, id), json, 10, TimeUnit.MINUTES);
    }

    public String getUser(Long id) {
        Object v = redisTemplate.opsForValue().get(String.format(KEY_USER, id));
        return v == null ? null : v.toString();
    }
}
```

> 若希望 **Value 全是 String**，可改用 `StringRedisTemplate`，省去自定义序列化的心智负担。

---

## 11.2 Python —— redis-py 快速上手

### 安装

```bash
pip install redis
```

### 连接与基本操作

```python
import redis

r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)

r.set("app:demo:name", "alice", ex=60)
print(r.get("app:demo:name"))

r.hset("app:demo:user:1", mapping={"name": "bob", "age": "20"})
print(r.hgetall("app:demo:user:1"))
```

`decode_responses=True` 表示返回 **str**；若要与二进制协议或自定义编码配合，可设为 `False`。

### 连接池

高并发下应复用连接，避免每次请求新建 TCP 连接：

```python
import redis

pool = redis.ConnectionPool(host="127.0.0.1", port=6379, db=0, max_connections=50, decode_responses=True)
r = redis.Redis(connection_pool=pool)

r.set("app:pool:test", "ok")
```

---

## 11.3 Node.js —— ioredis 基本用法

### 安装

```bash
npm install ioredis
```

### 连接与基本操作

```javascript
const Redis = require("ioredis");

const redis = new Redis({
  host: "127.0.0.1",
  port: 6379,
  db: 0,
  // password: "your-password",
  lazyConnect: false,
});

async function main() {
  await redis.set("app:demo:counter", "1", "EX", 60);
  const v = await redis.get("app:demo:counter");
  console.log(v);

  await redis.hset("app:demo:user:1", "name", "carol");
  const h = await redis.hgetall("app:demo:user:1");
  console.log(h);

  redis.disconnect();
}

main().catch(console.error);
```

ioredis 内置**连接池式**的复用（单实例多命令共享连接），一般一个进程保持一个 `Redis` 实例即可。

---

## 11.4 通用注意事项

### 连接池配置

| 场景 | 建议 |
|------|------|
| Web 多线程 / 多协程 | 使用客户端提供的 Pool，限制 `max_connections`，避免打满 Redis `maxclients` |
| 短时脚本 | 可单连接，但要注意关闭或复用 |
| 云 Redis | 按厂商文档设置超时、TLS、集群模式（如 Redis Cluster 需集群客户端） |

### 序列化：JSON vs 二进制

| 方式 | 优点 | 缺点 |
|------|------|------|
| JSON 字符串 | 可读、跨语言、易调试 | 体积偏大，类型需约定 |
| 二进制（如 MessagePack、JDK 序列化） | 体积小、速度快 | 调试不便，跨语言需统一协议 |

**建议**：对外缓存、多语言服务优先 **JSON + UTF-8**；内部极致性能场景再考虑二进制。

### Key 命名规范在代码中的落地

- 使用**常量或格式化模板**，避免魔法字符串散落各处，例如：`app:user:%s`、`app:session:%s`。
- 统一**前缀**（如 `app:`）便于按模式运维与隔离环境（测试/生产可用不同前缀或不同 `database` 索引，但集群模式下多 DB 不可用，需用前缀区分）。

### 异常处理与超时设置

- 为连接、读写设置**合理超时**，避免线程/协程被慢 Redis 拖死。
- **缓存应允许失败**：Redis 不可用时，可降级查数据库或直接报错（按业务定），不要假设 Redis 永远可用。
- 生产环境记录失败原因（超时、连接拒绝、OOM 等），便于与监控告警联动。

---

## 本章小结

| 小节 | 要点 |
|------|------|
| 11.1 Spring Boot | `spring-boot-starter-data-redis` + `application.yml`；`RedisTemplate` 的 `opsForValue` / `opsForHash` |
| 11.2 Python | `pip install redis`；`Redis` + `ConnectionPool`；`decode_responses` 与过期 `ex` |
| 11.3 Node.js | `ioredis` 单例连接；`set`/`get`/`hset`/`hgetall` 的 async 用法 |
| 11.4 通用 | 连接池、序列化策略、Key 模板化、超时与降级 |

完成本章后，你应能在三种栈里各自跑通**连接 Redis → 写入 → 读取**，并知道上线前要在配置与规范上补齐哪些坑。

---

## 下一章预告

**第十二章：总结与学习路线** 将回顾全书核心概念（数据结构、持久化、内存与淘汰、事务与管道、实战场景），并给出进阶方向（集群、哨兵、缓存设计模式、可观测性等）与推荐练习，帮助你把入门知识串成一条可持续深入的学习路径。
