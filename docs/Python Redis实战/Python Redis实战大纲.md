# Python Redis 实战教程

> 以 Python 开发者视角，系统掌握 redis-py 同步/异步客户端、FastAPI 集成、缓存/锁/队列/排行榜/限流等常见模式的工程实践。

---

## 1. 环境搭建与基础连接
<!-- 本章要点：安装 Redis 与 redis-py，同步/异步两种连接方式，连接池配置，decode_responses，健康检查 -->

### 1.1 安装 Redis 与 redis-py
### 1.2 同步连接与 decode_responses
### 1.3 连接池：为什么需要、怎么配置
### 1.4 异步连接：redis.asyncio 入门

---

## 2. 五大数据类型的 Python 操作
<!-- 本章要点：String/Hash/List/Set/Sorted Set 的 CRUD，每种类型给出 Python 完整代码 + 真实业务场景映射 -->

### 2.1 String：缓存、计数器、分布式 ID
### 2.2 Hash：用户对象、配置存储
### 2.3 List：消息队列、最新动态
### 2.4 Set 与 Sorted Set：标签系统、排行榜

---

## 3. Pipeline、事务与 Lua 脚本
<!-- 本章要点：Pipeline 批量操作减少网络往返、事务（MULTI/EXEC）、Lua 脚本原子操作、对比三者适用场景 -->

### 3.1 Pipeline：批量操作提升 10x 性能
### 3.2 事务（MULTI/EXEC）：原子性保障
### 3.3 Lua 脚本：自定义原子操作

---

## 4. 缓存模式实战
<!-- 本章要点：Cache-Aside/Read-Through 模式、缓存穿透/雪崩/击穿的 Python 解法、TTL 策略、装饰器封装 -->

### 4.1 Cache-Aside 模式：读写流程完整实现
### 4.2 缓存三大问题：穿透、雪崩、击穿的 Python 解法
### 4.3 用装饰器封装缓存逻辑

---

## 5. 分布式锁
<!-- 本章要点：SETNX 基础锁、过期时间与续约、Redlock 算法、Python 实现、上下文管理器封装 -->

### 5.1 从 SETNX 到生产级分布式锁
### 5.2 锁续约与看门狗机制
### 5.3 用 contextmanager 封装锁

---

## 6. 消息队列与发布订阅
<!-- 本章要点：List 实现简单队列、Pub/Sub 模式、Stream 类型（Redis 5.0+）消费者组、与 Celery/RQ 对比 -->

### 6.1 List 实现简单任务队列
### 6.2 Pub/Sub：实时通知
### 6.3 Redis Stream：带消费者组的可靠队列

---

## 7. 限流与计数器
<!-- 本章要点：固定窗口/滑动窗口/令牌桶三种限流算法的 Redis + Python 实现、API 限流中间件 -->

### 7.1 三种限流算法的 Redis 实现
### 7.2 FastAPI 限流中间件实战

---

## 8. FastAPI + Redis 集成
<!-- 本章要点：生命周期管理、依赖注入、Session 管理、WebSocket + Pub/Sub 实时推送、健康检查端点 -->

### 8.1 FastAPI 生命周期管理 Redis 连接
### 8.2 依赖注入与 Session 管理
### 8.3 WebSocket + Redis Pub/Sub 实时推送

---

## 9. 生产环境最佳实践
<!-- 本章要点：Key 命名规范、内存监控、序列化选型（JSON/msgpack/pickle）、异常处理与降级、日志追踪 -->

### 9.1 Key 命名规范与 TTL 策略
### 9.2 序列化：JSON vs MessagePack vs Pickle
### 9.3 异常处理、超时与降级策略
### 9.4 监控：内存、命中率、慢查询

---

## 10. 综合实战：构建一个带缓存的 API 服务
<!-- 本章要点：把前面所有知识串起来，用 FastAPI + Redis 构建一个完整的 API 服务，包含缓存、限流、分布式锁、排行榜 -->

### 10.1 项目结构与技术选型
### 10.2 实现缓存层 + 限流 + 排行榜
### 10.3 部署与性能调优
