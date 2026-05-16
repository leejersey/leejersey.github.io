# PostgreSQL 基础教程

> 从零掌握 PostgreSQL——从安装配置到 SQL 核心语法，覆盖建库建表、CRUD 操作、索引优化、事务控制、JSON 支持与 Python 集成，面向后端开发者的实战指南。

---

## 1. PostgreSQL 入门：为什么选它

PostgreSQL（简称 PG）是全球最先进的开源关系数据库——不是自封的，是社区公认的。它在功能丰富度上碾压 MySQL，在稳定性上媲美 Oracle，而且完全免费。

### 1.1 PostgreSQL vs MySQL：后端开发者的数据库选择

| 特性 | PostgreSQL | MySQL |
|:---|:---|:---|
| 标准兼容 | ✅ 最接近 SQL 标准 | ⚠️ 有不少方言 |
| JSON 支持 | ✅ JSONB（带索引） | ⚠️ 基础 JSON |
| 全文搜索 | ✅ 内置 tsvector | ❌ 需要插件 |
| 数组/范围类型 | ✅ 原生支持 | ❌ 不支持 |
| 事务隔离 | ✅ 真正的 MVCC | ⚠️ 依赖引擎 |
| 扩展生态 | ✅ PostGIS/pgvector | ⚠️ 较少 |
| 性能 | 复杂查询强 | 简单读取强 |
| 学习曲线 | ⭐⭐⭐ | ⭐⭐ |

> 💡 **选择建议**：新项目直接选 PostgreSQL。它能做 MySQL 能做的一切，还能做 MySQL 做不了的（JSONB、全文搜索、向量检索）。

### 1.2 核心特性：ACID、MVCC、JSON、全文搜索

```
PostgreSQL 的核心特性：

  🔒 ACID 事务
  ═══════════════════════════════════════
  原子性 + 一致性 + 隔离性 + 持久性
  金融级数据安全保障

  🔄 MVCC（多版本并发控制）
  ═══════════════════════════════════════
  读不阻塞写，写不阻塞读
  高并发场景性能优秀

  📦 JSONB
  ═══════════════════════════════════════
  关系数据库里存 NoSQL 数据
  支持索引，查询速度快

  🔍 全文搜索
  ═══════════════════════════════════════
  内置分词+搜索，简单场景不用 ES

  🧩 扩展生态
  ═══════════════════════════════════════
  PostGIS（地理信息）、pgvector（向量检索）
  TimescaleDB（时序数据）
```

### 1.3 安装 PostgreSQL：Docker 一行命令搞定

```bash
# ── 方式 1：Docker（推荐） ──
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=myapp \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16

# ── 方式 2：Mac ──
brew install postgresql@16
brew services start postgresql@16

# ── 方式 3：Ubuntu ──
sudo apt install postgresql-16
sudo systemctl start postgresql
```

### 1.4 连接工具：psql、DBeaver、DataGrip

```bash
# ── psql 命令行 ──
psql -h localhost -U postgres -d myapp
# 或 Docker 容器内
docker exec -it postgres psql -U postgres

# psql 常用快捷命令
\l          # 列出所有数据库
\c myapp    # 切换数据库
\dt         # 列出当前库的所有表
\d users    # 查看 users 表结构
\q          # 退出
```

| 工具 | 类型 | 推荐度 | 说明 |
|:---|:---|:---|:---|
| psql | 命令行 | ⭐⭐⭐ | 轻量、SSH 友好 |
| DBeaver | GUI（免费） | ⭐⭐⭐⭐ | 功能全、跨平台 |
| DataGrip | GUI（付费） | ⭐⭐⭐⭐⭐ | JetBrains 出品 |
| pgAdmin | Web GUI | ⭐⭐ | 官方工具，略重 |

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **PostgreSQL** | 最先进的开源关系数据库，功能碾压 MySQL |
| **JSONB** | 关系库里存 NoSQL 数据，带索引 |
| **Docker 安装** | `docker run postgres:16` 一行搞定 |
| **psql** | 命令行客户端，`\dt` `\d` `\l` 是高频命令 |

---

## 2. SQL 基础：建库建表与数据类型

### 2.1 建库建表：CREATE DATABASE / TABLE

```sql
-- 创建数据库
CREATE DATABASE myapp;

-- 创建用户表
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,        -- 自增主键
    username    VARCHAR(50) UNIQUE NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    avatar_url  TEXT,
    bio         TEXT DEFAULT '',
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 创建文章表（关联 users）
CREATE TABLE posts (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    content     TEXT NOT NULL,
    tags        TEXT[] DEFAULT '{}',        -- 数组类型
    metadata    JSONB DEFAULT '{}',         -- JSONB 类型
    view_count  INTEGER DEFAULT 0,
    published   BOOLEAN DEFAULT false,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.2 数据类型完全指南：从 INT 到 JSONB

| 类别 | 类型 | 说明 | 示例 |
|:---|:---|:---|:---|
| 整数 | `INTEGER` | 32 位整数 | 年龄、计数 |
| 整数 | `BIGINT` | 64 位整数 | ID、大数字 |
| 自增 | `SERIAL` | 自增整数 | 主键 |
| 小数 | `NUMERIC(10,2)` | 精确小数 | 金额 ¥99.99 |
| 浮点 | `DOUBLE PRECISION` | 近似小数 | 科学计算 |
| 文本 | `VARCHAR(N)` | 限长文本 | 用户名（50字） |
| 文本 | `TEXT` | 无限长文本 | 文章内容 |
| 布尔 | `BOOLEAN` | true/false | 是否激活 |
| 时间 | `TIMESTAMPTZ` | 带时区时间戳 | 创建时间 |
| 时间 | `DATE` | 日期 | 生日 |
| JSON | `JSONB` | 二进制 JSON | 元数据、配置 |
| 数组 | `TEXT[]` | 文本数组 | 标签 |
| UUID | `UUID` | 全局唯一 ID | 分布式主键 |

> 💡 **选型建议**：金额用 `NUMERIC` 不用 `FLOAT`（精度问题）；时间用 `TIMESTAMPTZ` 不用 `TIMESTAMP`（时区问题）；ID 推荐 `BIGSERIAL` 或 `UUID`。

### 2.3 约束：主键、外键、唯一、非空、检查

```sql
CREATE TABLE products (
    id          SERIAL PRIMARY KEY,                    -- 主键
    name        VARCHAR(100) NOT NULL,                 -- 非空
    sku         VARCHAR(50) UNIQUE,                    -- 唯一
    price       NUMERIC(10,2) CHECK (price > 0),       -- 检查约束
    category_id INTEGER REFERENCES categories(id),     -- 外键
    
    -- 联合唯一约束
    UNIQUE (name, category_id)
);
```

| 约束 | 语法 | 作用 |
|:---|:---|:---|
| PRIMARY KEY | `id SERIAL PRIMARY KEY` | 唯一标识每一行 |
| NOT NULL | `name VARCHAR(100) NOT NULL` | 不允许空值 |
| UNIQUE | `email VARCHAR(100) UNIQUE` | 不允许重复 |
| CHECK | `CHECK (price > 0)` | 自定义校验规则 |
| FOREIGN KEY | `REFERENCES users(id)` | 关联其他表 |
| DEFAULT | `DEFAULT NOW()` | 默认值 |

### 2.4 修改表结构：ALTER TABLE

```sql
-- 添加列
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- 删除列
ALTER TABLE users DROP COLUMN phone;

-- 修改列类型
ALTER TABLE users ALTER COLUMN bio TYPE VARCHAR(500);

-- 添加约束
ALTER TABLE users ADD CONSTRAINT email_check CHECK (email LIKE '%@%');

-- 重命名列
ALTER TABLE users RENAME COLUMN bio TO biography;

-- 重命名表
ALTER TABLE users RENAME TO app_users;
```

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **CREATE TABLE** | 建表时同时定义字段+类型+约束 |
| **数据类型** | 金额用 NUMERIC，时间用 TIMESTAMPTZ，ID 用 BIGSERIAL |
| **约束** | PK/UNIQUE/NOT NULL/CHECK/FK 保障数据完整性 |
| **ALTER TABLE** | 修改表结构，生产环境要小心锁表 |

---

## 3. CRUD 操作：增删改查核心语法

### 3.1 INSERT：单行插入、批量插入与 UPSERT

```sql
-- 单行插入
INSERT INTO users (username, email, password)
VALUES ('alice', 'alice@example.com', 'hashed_password');

-- 批量插入
INSERT INTO users (username, email, password) VALUES
    ('bob', 'bob@example.com', 'hash1'),
    ('charlie', 'charlie@example.com', 'hash2'),
    ('diana', 'diana@example.com', 'hash3');

-- UPSERT（插入或更新，冲突时更新）
INSERT INTO users (username, email, password)
VALUES ('alice', 'alice@new.com', 'new_hash')
ON CONFLICT (username) 
DO UPDATE SET email = EXCLUDED.email, updated_at = NOW();
-- EXCLUDED 指的是"被拒绝的新行"
```

### 3.2 SELECT：查询的艺术（WHERE / ORDER BY / LIMIT）

```sql
-- 基础查询
SELECT id, username, email FROM users WHERE is_active = true;

-- 模糊查询
SELECT * FROM users WHERE username LIKE 'a%';      -- 以 a 开头
SELECT * FROM users WHERE username ILIKE '%alice%'; -- 不区分大小写

-- 范围查询
SELECT * FROM posts WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31';
SELECT * FROM posts WHERE view_count IN (100, 200, 300);

-- 排序 + 分页
SELECT * FROM posts
WHERE published = true
ORDER BY created_at DESC          -- 最新的在前
LIMIT 20 OFFSET 40;              -- 第 3 页（每页 20 条）

-- NULL 处理
SELECT * FROM users WHERE avatar_url IS NOT NULL;
SELECT COALESCE(avatar_url, '/default.png') AS avatar FROM users;
```

### 3.3 UPDATE 与 DELETE：安全地修改和删除数据

```sql
-- 条件更新
UPDATE users SET is_active = false WHERE id = 5;

-- 批量更新
UPDATE posts SET view_count = view_count + 1 WHERE id = 42;

-- 条件删除
DELETE FROM posts WHERE published = false AND created_at < '2024-01-01';

-- 清空表（比 DELETE 快，不可回滚）
TRUNCATE TABLE logs;
```

> 💡 **安全原则**：UPDATE 和 DELETE 永远带 WHERE。没有 WHERE 的 UPDATE/DELETE 会修改/删除全表。生产环境先 SELECT 确认再 UPDATE。

### 3.4 RETURNING 子句：写入即返回

```sql
-- 插入后返回生成的 ID
INSERT INTO users (username, email, password)
VALUES ('eve', 'eve@example.com', 'hash')
RETURNING id, created_at;

-- 更新后返回修改的行
UPDATE users SET is_active = false WHERE id = 5
RETURNING id, username, is_active;

-- 删除后返回被删除的行
DELETE FROM posts WHERE id = 10
RETURNING *;
```

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **UPSERT** | `ON CONFLICT DO UPDATE` 插入或更新 |
| **ILIKE** | 不区分大小写的 LIKE |
| **COALESCE** | NULL 值的默认值处理 |
| **RETURNING** | INSERT/UPDATE/DELETE 后直接返回结果 |

---

## 4. 查询进阶：JOIN、聚合与子查询

### 4.1 JOIN 详解：INNER / LEFT / RIGHT / FULL

```sql
-- INNER JOIN（只返回匹配的行）
SELECT u.username, p.title
FROM users u
INNER JOIN posts p ON u.id = p.user_id;

-- LEFT JOIN（左表全部 + 右表匹配的）
SELECT u.username, COUNT(p.id) AS post_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id;
-- 没发过文章的用户也会出现，post_count = 0

-- 多表 JOIN
SELECT u.username, p.title, c.name AS category
FROM users u
JOIN posts p ON u.id = p.user_id
JOIN categories c ON p.category_id = c.id
WHERE p.published = true;
```

### 4.2 聚合函数：COUNT、SUM、AVG 与 GROUP BY

```sql
-- 基础聚合
SELECT COUNT(*) AS total_users FROM users;
SELECT AVG(view_count) AS avg_views FROM posts WHERE published = true;

-- GROUP BY 分组统计
SELECT user_id, COUNT(*) AS post_count, SUM(view_count) AS total_views
FROM posts
GROUP BY user_id
HAVING COUNT(*) > 5              -- 只看发了 5 篇以上的用户
ORDER BY total_views DESC;
```

### 4.3 子查询与 CTE（WITH 语句）

```sql
-- 子查询
SELECT * FROM users
WHERE id IN (SELECT user_id FROM posts WHERE view_count > 1000);

-- CTE（推荐，可读性更好）
WITH popular_authors AS (
    SELECT user_id, COUNT(*) AS post_count
    FROM posts
    WHERE view_count > 1000
    GROUP BY user_id
)
SELECT u.username, pa.post_count
FROM users u
JOIN popular_authors pa ON u.id = pa.user_id
ORDER BY pa.post_count DESC;
```

### 4.4 窗口函数：ROW_NUMBER、RANK、LAG

```sql
-- ROW_NUMBER：每个用户的文章按浏览量排名
SELECT title, view_count,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY view_count DESC) AS rank
FROM posts;

-- 累计求和
SELECT created_at::date AS day,
    COUNT(*) AS daily_count,
    SUM(COUNT(*)) OVER (ORDER BY created_at::date) AS cumulative
FROM users
GROUP BY day;

-- LAG/LEAD：跟前一天对比
SELECT date, revenue,
    revenue - LAG(revenue) OVER (ORDER BY date) AS growth
FROM daily_stats;
```

> 💡 **窗口函数 vs GROUP BY**：GROUP BY 聚合后结果行数减少；窗口函数在每一行上计算，行数不变。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **LEFT JOIN** | 左表全部保留，右表没匹配的填 NULL |
| **HAVING** | GROUP BY 后的条件过滤 |
| **CTE** | `WITH ... AS` 提高子查询可读性 |
| **窗口函数** | `OVER (PARTITION BY ... ORDER BY ...)` 不减少行数 |

---

## 5. 索引与性能优化

### 5.1 索引原理：为什么查询能从 1 秒变 1 毫秒

```
没有索引 vs 有索引：

  SELECT * FROM users WHERE email = 'alice@example.com'

  没有索引：
  ═══════════════════════════════════════
  全表扫描（Seq Scan）→ 逐行比对
  100 万行 → 扫描 100 万次
  耗时：~1 秒

  有索引：
  ═══════════════════════════════════════
  索引查找（Index Scan）→ B-Tree 二分查找
  100 万行 → 查找 ~20 次（log₂(1000000) ≈ 20）
  耗时：~1 毫秒
```

### 5.2 CREATE INDEX 与索引类型：B-Tree / GIN / GiST

```sql
-- 基础索引（B-Tree，默认）
CREATE INDEX idx_users_email ON users(email);

-- 唯一索引
CREATE UNIQUE INDEX idx_users_username ON users(username);

-- 复合索引
CREATE INDEX idx_posts_user_date ON posts(user_id, created_at DESC);

-- JSONB 索引（GIN）
CREATE INDEX idx_posts_metadata ON posts USING GIN (metadata);

-- 全文搜索索引
CREATE INDEX idx_posts_search ON posts USING GIN (to_tsvector('english', title || ' ' || content));

-- 部分索引（只索引一部分数据）
CREATE INDEX idx_active_users ON users(email) WHERE is_active = true;
```

| 索引类型 | 适用场景 | 示例 |
|:---|:---|:---|
| B-Tree | 等值/范围/排序 | `WHERE email = ?`, `ORDER BY` |
| GIN | JSONB / 数组 / 全文搜索 | `metadata @> '{"key": "v"}'` |
| GiST | 几何/范围/全文 | PostGIS 地理查询 |
| BRIN | 时序数据（大表） | `WHERE created_at > ?` |

### 5.3 EXPLAIN ANALYZE：读懂查询计划

```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'alice@example.com';

-- 输出：
-- Index Scan using idx_users_email on users  (cost=0.42..8.44 rows=1 width=128)
--   (actual time=0.015..0.016 rows=1 loops=1)
-- Planning Time: 0.073 ms
-- Execution Time: 0.031 ms
```

```
查询计划中的关键指标：

  Seq Scan      → 全表扫描（可能需要加索引）
  Index Scan    → 用了索引（好 ✅）
  Bitmap Scan   → 用了索引，批量读取（好 ✅）
  cost          → 估算成本（越小越好）
  actual time   → 实际耗时（毫秒）
  rows          → 返回行数
```

### 5.4 索引优化实战：常见误区与最佳实践

| 误区 | 正确做法 |
|:---|:---|
| 给每列都加索引 | 只给 WHERE/JOIN/ORDER BY 用到的列加 |
| 忘记复合索引顺序 | 高选择性的列放前面 |
| 不用 EXPLAIN | 改完必须 EXPLAIN ANALYZE 验证 |
| 重复索引 | `(a, b)` 的复合索引已经覆盖了 `(a)` 的查询 |

> 💡 **索引不是免费的**——每个索引都会增加写入开销（INSERT/UPDATE 变慢）和存储占用。关键是只索引真正需要的列。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **B-Tree** | 默认索引，适合等值和范围查询 |
| **GIN** | 适合 JSONB、数组、全文搜索 |
| **EXPLAIN ANALYZE** | 看 Seq Scan 还是 Index Scan |
| **部分索引** | `WHERE is_active = true` 只索引需要的行 |

---

## 6. 事务与并发控制

### 6.1 事务基础：BEGIN / COMMIT / ROLLBACK

```sql
-- 转账场景：从 A 扣款 100 元，给 B 加 100 元
BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;
    UPDATE accounts SET balance = balance + 100 WHERE user_id = 2;
COMMIT;

-- 如果中间出错，自动回滚
BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;
    -- 假设这里出错了
ROLLBACK;  -- 第一条 UPDATE 也被撤销
```

### 6.2 隔离级别：读已提交 vs 可重复读 vs 串行化

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 性能 |
|:---|:---|:---|:---|:---|
| Read Committed（默认） | ❌ | ⚠️ 可能 | ⚠️ 可能 | 最好 |
| Repeatable Read | ❌ | ❌ | ❌ | 好 |
| Serializable | ❌ | ❌ | ❌ | 最差 |

```sql
-- 设置隔离级别
BEGIN ISOLATION LEVEL REPEATABLE READ;
    SELECT * FROM accounts WHERE user_id = 1;
    -- 在这个事务内，看到的数据不会被其他事务改变
COMMIT;
```

### 6.3 MVCC：PostgreSQL 的并发魔法

```
MVCC 原理：

  事务 A（读）     事务 B（写）
  ──────────      ──────────
  BEGIN           BEGIN
  SELECT balance  
    → 看到 1000                 
                  UPDATE balance = 900
                  COMMIT
  SELECT balance  
    → 仍然看到 1000（快照隔离）
  COMMIT
  
  事务 A 始终看到自己开始时的快照
  读不阻塞写，写不阻塞读 ✅
```

### 6.4 锁机制：乐观锁、悲观锁与死锁处理

```sql
-- 悲观锁：SELECT FOR UPDATE（锁住行）
BEGIN;
    SELECT * FROM accounts WHERE user_id = 1 FOR UPDATE;
    -- 其他事务要修改这行会等待
    UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;
COMMIT;

-- 乐观锁：用版本号
UPDATE products SET stock = stock - 1, version = version + 1
WHERE id = 42 AND version = 3;
-- 如果 version 已经不是 3，说明被别人改过，更新 0 行
```

> 💡 **死锁处理**：PostgreSQL 自动检测死锁（默认 1 秒超时），会中止其中一个事务。预防死锁的方法：按固定顺序获取锁。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **事务** | BEGIN → 操作 → COMMIT/ROLLBACK，保证原子性 |
| **Read Committed** | 默认隔离级别，每条语句看到最新提交的数据 |
| **MVCC** | 读写不互斥，每个事务看到自己的快照 |
| **FOR UPDATE** | 悲观锁，锁住行直到事务结束 |

---

## 7. PostgreSQL 高级特性

### 7.1 JSONB：在关系数据库里存 NoSQL 数据

```sql
-- 插入 JSONB 数据
INSERT INTO posts (title, content, metadata) VALUES
('My Post', 'Content...', '{"category": "tech", "reading_time": 5, "tags": ["python", "sql"]}');

-- 查询 JSONB 字段
SELECT title, metadata->>'category' AS category     -- 取文本值
FROM posts WHERE metadata->>'category' = 'tech';

SELECT title FROM posts
WHERE metadata @> '{"tags": ["python"]}';            -- 包含检查

-- 更新 JSONB 中的某个键
UPDATE posts SET metadata = metadata || '{"featured": true}'
WHERE id = 1;

-- 删除 JSONB 中的某个键
UPDATE posts SET metadata = metadata - 'featured'
WHERE id = 1;
```

| 操作符 | 含义 | 示例 |
|:---|:---|:---|
| `->` | 取 JSON 对象（返回 JSON） | `metadata->'tags'` |
| `->>` | 取 JSON 值（返回文本） | `metadata->>'category'` |
| `@>` | 包含 | `metadata @> '{"key": "v"}'` |
| `?` | 键是否存在 | `metadata ? 'category'` |
| `||` | 合并 | `metadata || '{"new": true}'` |
| `-` | 删除键 | `metadata - 'key'` |

### 7.2 数组类型：一个字段存多个值

```sql
-- 插入数组
INSERT INTO posts (title, content, tags)
VALUES ('Post', 'Content', ARRAY['python', 'docker', 'postgres']);

-- 查询包含某个元素的数组
SELECT * FROM posts WHERE 'python' = ANY(tags);

-- 数组操作
SELECT array_length(tags, 1) AS tag_count FROM posts;
SELECT unnest(tags) AS tag FROM posts WHERE id = 1;  -- 展开数组
```

### 7.3 全文搜索：不用 Elasticsearch 也能搜

```sql
-- 基础全文搜索
SELECT title, ts_rank(
    to_tsvector('english', title || ' ' || content),
    to_tsquery('english', 'python & docker')
) AS relevance
FROM posts
WHERE to_tsvector('english', title || ' ' || content) 
    @@ to_tsquery('english', 'python & docker')
ORDER BY relevance DESC;

-- 给搜索加索引（必须，否则很慢）
CREATE INDEX idx_posts_fts ON posts 
USING GIN (to_tsvector('english', title || ' ' || content));
```

### 7.4 物化视图与生成列

```sql
-- 物化视图（预计算的查询结果，定期刷新）
CREATE MATERIALIZED VIEW user_stats AS
SELECT u.id, u.username,
    COUNT(p.id) AS post_count,
    COALESCE(SUM(p.view_count), 0) AS total_views
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id;

-- 刷新物化视图
REFRESH MATERIALIZED VIEW CONCURRENTLY user_stats;

-- 生成列（自动计算）
ALTER TABLE posts ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (to_tsvector('english', title || ' ' || content)) STORED;
```

> 💡 **JSONB vs 单独建表**：数据结构固定 → 建表；结构不确定或经常变化 → JSONB。JSONB 配合 GIN 索引，查询速度跟普通字段差不多。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **JSONB** | `->>`取值 + `@>` 包含检查 + GIN 索引 |
| **数组** | `ANY()` 查包含 + `unnest()` 展开 |
| **全文搜索** | `tsvector` + `tsquery` + GIN 索引 |
| **物化视图** | 预计算结果，用 `REFRESH` 更新 |

---

## 8. Python 集成：SQLAlchemy + asyncpg

### 8.1 psycopg：Python 连接 PostgreSQL 的标准库

```python
import psycopg  # psycopg3

# 连接数据库
conn = psycopg.connect("postgresql://postgres:password@localhost:5432/myapp")

# 查询
with conn.cursor() as cur:
    cur.execute("SELECT id, username FROM users WHERE is_active = %s", [True])
    rows = cur.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Username: {row[1]}")

# 插入（参数化查询，防 SQL 注入）
with conn.cursor() as cur:
    cur.execute(
        "INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id",
        ["alice", "alice@example.com", "hashed_password"]
    )
    new_id = cur.fetchone()[0]
    conn.commit()

conn.close()
```

### 8.2 SQLAlchemy ORM：用 Python 类操作数据库

```python
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

# 定义模型
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 连接
engine = create_engine("postgresql://postgres:password@localhost:5432/myapp")
Session = sessionmaker(bind=engine)

# CRUD 操作
with Session() as session:
    # 插入
    user = User(username="alice", email="alice@example.com")
    session.add(user)
    session.commit()
    
    # 查询
    users = session.query(User).filter(User.is_active == True).all()
    
    # 更新
    user.username = "alice_new"
    session.commit()
    
    # 删除
    session.delete(user)
    session.commit()
```

### 8.3 asyncpg：异步高性能数据库操作

```python
import asyncpg
import asyncio

async def main():
    # 连接池
    pool = await asyncpg.create_pool(
        "postgresql://postgres:password@localhost:5432/myapp",
        min_size=5, max_size=20
    )
    
    async with pool.acquire() as conn:
        # 查询
        rows = await conn.fetch("SELECT * FROM users WHERE is_active = $1", True)
        for row in rows:
            print(dict(row))
        
        # 插入
        new_id = await conn.fetchval(
            "INSERT INTO users (username, email, password) VALUES ($1, $2, $3) RETURNING id",
            "bob", "bob@example.com", "hashed"
        )
    
    await pool.close()

asyncio.run(main())
```

### 8.4 Alembic 数据库迁移：版本化管理表结构

```bash
# 安装
pip install alembic

# 初始化
alembic init migrations

# 生成迁移脚本
alembic revision --autogenerate -m "add phone column to users"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

```python
# migrations/versions/001_add_phone.py（自动生成）
def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(20)))

def downgrade():
    op.drop_column('users', 'phone')
```

> 💡 **黄金法则**：永远用 Alembic 管理表结构变更，不要手动跑 `ALTER TABLE`。迁移脚本提交到 Git，团队成员 `alembic upgrade head` 就能同步表结构。

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **psycopg** | Python 连 PG 的标准库，`%s` 参数化防注入 |
| **SQLAlchemy** | ORM，用 Python 类操作数据库 |
| **asyncpg** | 异步连接池，FastAPI 项目首选 |
| **Alembic** | 数据库迁移工具，版本化管理表结构 |

---

## 附录：PostgreSQL 速查手册

### A.1 SQL 语法速查

```sql
-- 建表
CREATE TABLE t (id SERIAL PRIMARY KEY, name TEXT NOT NULL);

-- 增
INSERT INTO t (name) VALUES ('x') RETURNING id;

-- 查
SELECT * FROM t WHERE name = 'x' ORDER BY id LIMIT 10;

-- 改
UPDATE t SET name = 'y' WHERE id = 1 RETURNING *;

-- 删
DELETE FROM t WHERE id = 1 RETURNING *;

-- 索引
CREATE INDEX idx_name ON t(name);

-- 事务
BEGIN; UPDATE ...; COMMIT;
```

### A.2 数据类型与函数速查

| 函数 | 说明 | 示例 |
|:---|:---|:---|
| `NOW()` | 当前时间 | `DEFAULT NOW()` |
| `COALESCE(a, b)` | a 为 NULL 则返回 b | 默认值处理 |
| `CONCAT()` | 字符串拼接 | `CONCAT(first, ' ', last)` |
| `LENGTH()` | 字符串长度 | `WHERE LENGTH(name) > 3` |
| `UPPER/LOWER` | 大小写转换 | `UPPER(email)` |
| `DATE_TRUNC()` | 时间截断 | `DATE_TRUNC('day', ts)` |
| `AGE()` | 时间差 | `AGE(NOW(), created_at)` |
| `ARRAY_AGG()` | 聚合为数组 | `ARRAY_AGG(tag)` |
| `JSON_AGG()` | 聚合为 JSON | `JSON_AGG(row)` |

### A.3 psql 命令速查

| 命令 | 说明 |
|:---|:---|
| `\l` | 列出所有数据库 |
| `\c dbname` | 切换数据库 |
| `\dt` | 列出所有表 |
| `\d tablename` | 查看表结构 |
| `\di` | 列出所有索引 |
| `\du` | 列出所有用户 |
| `\timing` | 开启查询耗时显示 |
| `\x` | 切换扩展显示模式 |
| `\q` | 退出 |

### A.4 运维常用查询（连接数 / 慢查询 / 表大小）

```sql
-- 当前连接数
SELECT count(*) FROM pg_stat_activity;

-- 活跃查询（找慢查询）
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY duration DESC;

-- 表大小排行
SELECT relname AS table, pg_size_pretty(pg_total_relation_size(relid)) AS size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 10;

-- 索引使用率（未使用的索引可以删掉）
SELECT indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- 终止慢查询
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE duration > interval '5 minutes';
```
