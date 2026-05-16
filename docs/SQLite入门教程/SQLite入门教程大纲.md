# SQLite 入门教程

> **目标**：用最短的时间建立对 SQLite 的整体认知，掌握核心功能与典型使用场景，学会在项目中正确使用这个「最广泛部署的数据库引擎」。

---

## 第一章 认识 SQLite
<!-- 简述本章要点：介绍 SQLite 的定位、特点、适用场景，与其他数据库的对比 -->

### 1.1 SQLite 是什么 —— 一句话理解
### 1.2 SQLite 的设计哲学：零配置、无服务器、单文件
### 1.3 SQLite 能解决什么问题（嵌入式应用、移动端、本地缓存、原型开发……）
### 1.4 SQLite vs MySQL / PostgreSQL —— 什么时候该用 SQLite
### 1.5 SQLite 的整体架构概览（虚拟机、B-Tree、Pager、OS 接口）

---

## 第二章 快速安装与第一条命令
<!-- 简述本章要点：最低成本把 SQLite 跑起来，熟悉命令行工具 -->

### 2.1 安装 SQLite（macOS / Linux / Windows）
### 2.2 sqlite3 命令行工具入门
### 2.3 点命令（Dot Commands）速览
### 2.4 可视化工具推荐（DB Browser for SQLite / SQLiteStudio）

---

## 第三章 数据库与表的基本操作（DDL）
<!-- 简述本章要点：建库建表、数据类型、约束 -->

### 3.1 创建与管理数据库（就是一个文件）
### 3.2 SQLite 的类型系统 —— 类型亲和性（Type Affinity）
### 3.3 创建与修改表（CREATE TABLE / ALTER TABLE）
### 3.4 约束（PRIMARY KEY / NOT NULL / UNIQUE / CHECK / FOREIGN KEY）

---

## 第四章 数据增删改（DML）
<!-- 简述本章要点：INSERT / UPDATE / DELETE 的各种用法 -->

### 4.1 插入数据（单行 / 多行 / INSERT OR REPLACE / INSERT OR IGNORE）
### 4.2 更新数据（UPDATE ... SET ... WHERE）
### 4.3 删除数据（DELETE / 清空表的正确方式）
### 4.4 UPSERT —— INSERT ... ON CONFLICT（SQLite 3.24+）

---

## 第五章 查询语句（SELECT）— 最核心的部分
<!-- 简述本章要点：从基础查询到多表联查，覆盖日常 90% 的查询需求 -->

### 5.1 基础查询与别名
### 5.2 条件过滤（WHERE / LIKE / GLOB / IN / BETWEEN）
### 5.3 排序与分页（ORDER BY / LIMIT / OFFSET）
### 5.4 聚合函数与分组（COUNT / AVG / SUM / GROUP BY / HAVING）
### 5.5 多表联查（INNER JOIN / LEFT JOIN / CROSS JOIN）
### 5.6 子查询与 CTE（WITH 语句）

---

## 第六章 索引与查询优化
<!-- 简述本章要点：理解索引原理，用 EXPLAIN 分析查询性能 -->

### 6.1 什么是索引 —— 类比与原理
### 6.2 创建与管理索引（CREATE INDEX / UNIQUE INDEX / 复合索引）
### 6.3 用 EXPLAIN QUERY PLAN 分析查询
### 6.4 索引使用原则与常见陷阱

---

## 第七章 事务与数据安全
<!-- 简述本章要点：事务基本用法、WAL 模式、并发控制 -->

### 7.1 事务的基本用法（BEGIN / COMMIT / ROLLBACK）
### 7.2 ACID 在 SQLite 中的体现
### 7.3 日志模式：DELETE vs WAL（Write-Ahead Logging）
### 7.4 并发控制与锁机制（数据库级锁 vs WAL 并发读写）

---

## 第八章 SQLite 特色功能
<!-- 简述本章要点：SQLite 独有的或特别好用的功能 -->

### 8.1 JSON 支持（json_extract / json_each / json_set）
### 8.2 全文搜索（FTS5）
### 8.3 窗口函数（ROW_NUMBER / RANK / LAG / LEAD）
### 8.4 生成列（Generated Columns）
### 8.5 STRICT 表（SQLite 3.37+）—— 强制类型检查

---

## 第九章 在项目中使用 SQLite
<!-- 简述本章要点：各语言的 SQLite 库与最佳实践 -->

### 9.1 Python —— sqlite3 标准库 + 进阶用法
### 9.2 Node.js —— better-sqlite3 / sql.js
### 9.3 Go —— mattn/go-sqlite3 / modernc.org/sqlite
### 9.4 连接管理、参数化查询与安全注意事项
### 9.5 ORM 集成（SQLAlchemy / Prisma / GORM）

---

## 第十章 数据库管理与运维
<!-- 简述本章要点：备份、压缩、迁移等日常运维操作 -->

### 10.1 备份策略（.backup 命令 / 文件复制 / VACUUM INTO）
### 10.2 数据库压缩与整理（VACUUM / auto_vacuum）
### 10.3 数据导入导出（CSV / SQL dump / .import）
### 10.4 数据库修复与完整性检查（PRAGMA integrity_check）

---

## 第十一章 总结与进阶方向
<!-- 简述本章要点：回顾全貌，指引后续学习方向 -->

### 11.1 一张图回顾 SQLite 全貌
### 11.2 核心知识点速查表
### 11.3 进阶方向指引：Litestream 实时复制、LiteFS 分布式、LibSQL / Turso 云端方案

---

## 附录

- A. 常用 SQL 语句速查表
- B. 常用 PRAGMA 配置说明
- C. SQLite 内置函数参考
- D. 推荐学习资源与官方文档链接
