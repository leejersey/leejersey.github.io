# Redis 入门教程大纲

> **目标**：用最短的时间建立对 Redis 的整体认知，掌握核心功能与典型使用场景。

---

## 第一章 Redis 是什么

- 1.1 一句话理解 Redis：基于内存的键值数据库
- 1.2 Redis 能解决什么问题（缓存、会话、排行榜、消息队列……）
- 1.3 Redis vs MySQL —— 什么时候该用 Redis
- 1.4 Redis 的整体架构概览（单线程模型、内存 + 持久化）

## 第二章 快速安装与启动

- 2.1 Linux / macOS 安装（源码编译 & 包管理器）
- 2.2 Windows 安装（WSL / Docker）
- 2.3 Docker 一键启动（推荐）
- 2.4 连接 Redis：redis-cli 基本操作
- 2.5 可视化工具推荐（RedisInsight / Another Redis Desktop Manager）

## 第三章 五大基础数据类型

> 这是 Redis 的核心，每种类型用「是什么 → 常用命令 → 典型场景」三步讲清。

- 3.1 String（字符串）
  - SET / GET / INCR / EXPIRE
  - 场景：缓存、计数器、分布式锁
- 3.2 Hash（哈希）
  - HSET / HGET / HGETALL
  - 场景：存储对象（用户信息、商品详情）
- 3.3 List（列表）
  - LPUSH / RPUSH / LPOP / LRANGE
  - 场景：消息队列、最新动态列表
- 3.4 Set（集合）
  - SADD / SMEMBERS / SINTER / SUNION
  - 场景：标签系统、共同好友、去重
- 3.5 Sorted Set（有序集合）
  - ZADD / ZRANGE / ZRANK / ZSCORE
  - 场景：排行榜、延迟队列

## 第四章 三个进阶数据类型（了解即可）

- 4.1 Bitmap —— 签到统计、布隆过滤器基础
- 4.2 HyperLogLog —— 海量数据基数统计（UV 统计）
- 4.3 Stream —— Redis 原生消息队列

## 第五章 Key 管理与过期策略

- 5.1 Key 的命名规范（业务:对象:id）
- 5.2 EXPIRE / TTL / PERSIST —— 给 Key 设置生命周期
- 5.3 过期删除策略：惰性删除 + 定期删除
- 5.4 内存淘汰策略（maxmemory-policy）概览

## 第六章 持久化：数据不丢失的秘密

- 6.1 RDB 快照 —— 定时拍照
- 6.2 AOF 日志 —— 逐条记录
- 6.3 RDB vs AOF 对比与选择建议
- 6.4 混合持久化（Redis 4.0+）

## 第七章 常见应用场景实战

- 7.1 缓存穿透、缓存击穿、缓存雪崩 —— 三大经典问题与解决方案
- 7.2 分布式锁（SETNX + EXPIRE）
- 7.3 Session 共享
- 7.4 接口限流（滑动窗口）

## 第八章 事务与 Lua 脚本

- 8.1 MULTI / EXEC / WATCH —— Redis 事务基础
- 8.2 Redis 事务 ≠ MySQL 事务（不支持回滚）
- 8.3 Lua 脚本 —— 原子性操作的正确姿势

## 第九章 发布/订阅（Pub/Sub）

- 9.1 PUBLISH / SUBSCRIBE 基本用法
- 9.2 适用场景与局限性
- 9.3 与 Stream 的对比

## 第十章 主从复制与高可用

- 10.1 主从复制原理（全量同步 + 增量同步）
- 10.2 哨兵模式（Sentinel）—— 自动故障转移
- 10.3 集群模式（Cluster）—— 数据分片概念
- 10.4 三种部署模式的选择建议

## 第十一章 在项目中使用 Redis

- 11.1 Java —— Spring Boot + Jedis / Lettuce / RedisTemplate
- 11.2 Python —— redis-py 快速上手
- 11.3 Node.js —— ioredis 基本用法
- 11.4 连接池与序列化注意事项

## 第十二章 总结与学习路线

- 12.1 一张图回顾 Redis 全貌（思维导图）
- 12.2 Redis 核心知识点速查表
- 12.3 进阶方向指引：源码阅读、Redis 设计与实现、云服务实践

---

## 附录

- A. 常用命令速查表
- B. redis.conf 关键配置项说明
- C. 推荐学习资源与官方文档链接
