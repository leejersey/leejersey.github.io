# PostgreSQL 入门教程

> 目标：用最短的时间建立 PostgreSQL 的整体认知，掌握核心功能与最常用的 SQL 操作。

---

## 第一章 认识 PostgreSQL

### 1.1 PostgreSQL 是什么
- 开源关系型数据库，历史超过 35 年
- 与 MySQL、SQL Server、Oracle 的定位对比
- 核心优势：标准兼容性强、可扩展性高、数据类型丰富、支持 JSON/地理空间

### 1.2 核心概念速览
- 数据库（Database） → 模式（Schema） → 表（Table） → 行/列（Row/Column）
- 客户端-服务端架构：应用通过连接（Connection）与数据库交互
- 事务（Transaction）：保证数据操作的原子性

### 1.3 环境搭建
- 安装 PostgreSQL（Windows / macOS / Linux / Docker 一键启动）
- 认识关键工具：`psql` 命令行、pgAdmin 图形界面
- 第一次连接数据库：`psql -U postgres`

---

## 第二章 数据库与表的基本操作（DDL）

### 2.1 数据库管理
```sql
CREATE DATABASE mydb;          -- 创建数据库
\l                             -- 列出所有数据库（psql）
\c mydb                        -- 切换到 mydb
DROP DATABASE mydb;            -- 删除数据库
```

### 2.2 数据类型一览
| 类别 | 常用类型 | 说明 |
|------|---------|------|
| 整数 | `INTEGER`, `BIGINT`, `SMALLINT` | 最常用的数字类型 |
| 浮点 | `NUMERIC(p,s)`, `REAL` | 精确/近似小数 |
| 文本 | `VARCHAR(n)`, `TEXT` | 变长字符串 |
| 布尔 | `BOOLEAN` | true / false |
| 日期时间 | `DATE`, `TIMESTAMP`, `INTERVAL` | 时间相关 |
| JSON | `JSON`, `JSONB` | 半结构化数据（PostgreSQL 特色） |
| 数组 | `INTEGER[]`, `TEXT[]` | 原生数组支持（PostgreSQL 特色） |
| UUID | `UUID` | 全局唯一标识符 |

### 2.3 创建与修改表
```sql
-- 创建表
CREATE TABLE students (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50) NOT NULL,
    email       VARCHAR(100) UNIQUE,
    age         INTEGER CHECK (age > 0),
    enrolled_at TIMESTAMP DEFAULT NOW()
);

-- 修改表结构
ALTER TABLE students ADD COLUMN score NUMERIC(5,2);
ALTER TABLE students DROP COLUMN score;
ALTER TABLE students RENAME COLUMN name TO full_name;

-- 删除表
DROP TABLE students;
```

### 2.4 约束（Constraints）
- `PRIMARY KEY` — 主键，唯一标识每一行
- `NOT NULL` — 不允许为空
- `UNIQUE` — 值不可重复
- `CHECK` — 自定义校验条件
- `DEFAULT` — 默认值
- `FOREIGN KEY` — 外键，关联另一张表

---

## 第三章 数据增删改（DML）

### 3.1 插入数据
```sql
-- 单行插入
INSERT INTO students (name, email, age)
VALUES ('张三', 'zhangsan@example.com', 20);

-- 多行插入
INSERT INTO students (name, email, age) VALUES
    ('李四', 'lisi@example.com', 22),
    ('王五', 'wangwu@example.com', 21);
```

### 3.2 更新数据
```sql
UPDATE students
SET age = 23
WHERE name = '李四';
```

### 3.3 删除数据
```sql
DELETE FROM students WHERE name = '王五';

-- 清空整张表（速度快，不可回滚）
TRUNCATE TABLE students;
```

---

## 第四章 查询语句（SELECT）— 最核心的部分

### 4.1 基础查询
```sql
SELECT * FROM students;                        -- 查所有列
SELECT name, age FROM students;                -- 查指定列
SELECT DISTINCT age FROM students;             -- 去重
SELECT name AS 姓名, age AS 年龄 FROM students; -- 别名
```

### 4.2 条件过滤（WHERE）
```sql
SELECT * FROM students WHERE age >= 20;
SELECT * FROM students WHERE name LIKE '张%';
SELECT * FROM students WHERE age IN (20, 21, 22);
SELECT * FROM students WHERE age BETWEEN 18 AND 25;
SELECT * FROM students WHERE email IS NOT NULL;
SELECT * FROM students WHERE age > 20 AND name LIKE '李%';
```

### 4.3 排序与分页
```sql
SELECT * FROM students ORDER BY age DESC;              -- 降序
SELECT * FROM students ORDER BY age ASC, name DESC;    -- 多列排序
SELECT * FROM students ORDER BY age LIMIT 10;          -- 取前 10 条
SELECT * FROM students ORDER BY age LIMIT 10 OFFSET 20; -- 跳过 20 条取 10 条
```

### 4.4 聚合函数与分组
```sql
SELECT COUNT(*) FROM students;                          -- 总行数
SELECT AVG(age), MAX(age), MIN(age) FROM students;      -- 平均/最大/最小
SELECT age, COUNT(*) FROM students GROUP BY age;        -- 按年龄分组计数
SELECT age, COUNT(*) FROM students
    GROUP BY age HAVING COUNT(*) > 3;                   -- 分组后过滤
```

### 4.5 多表联查（JOIN）
```sql
-- 准备第二张表
CREATE TABLE courses (
    id          SERIAL PRIMARY KEY,
    student_id  INTEGER REFERENCES students(id),
    course_name VARCHAR(100),
    score       NUMERIC(5,2)
);

-- INNER JOIN：只返回两边都匹配的行
SELECT s.name, c.course_name, c.score
FROM students s
INNER JOIN courses c ON s.id = c.student_id;

-- LEFT JOIN：左表全部保留，右表无匹配则为 NULL
SELECT s.name, c.course_name
FROM students s
LEFT JOIN courses c ON s.id = c.student_id;

-- RIGHT JOIN / FULL OUTER JOIN（了解即可）
```

### 4.6 子查询
```sql
-- WHERE 中的子查询
SELECT * FROM students
WHERE id IN (SELECT student_id FROM courses WHERE score > 90);

-- FROM 中的子查询（派生表）
SELECT avg_score.name, avg_score.avg
FROM (
    SELECT s.name, AVG(c.score) AS avg
    FROM students s JOIN courses c ON s.id = c.student_id
    GROUP BY s.name
) AS avg_score
WHERE avg_score.avg > 80;
```

---

## 第五章 索引与性能基础

### 5.1 什么是索引
- 类比：书的目录，加速查找
- 有索引 vs 无索引的查询速度差异

### 5.2 创建与管理索引
```sql
CREATE INDEX idx_students_name ON students(name);      -- B-Tree 索引（默认）
CREATE INDEX idx_students_age_name ON students(age, name); -- 复合索引
DROP INDEX idx_students_name;
```

### 5.3 用 EXPLAIN 分析查询
```sql
EXPLAIN ANALYZE SELECT * FROM students WHERE name = '张三';
-- 查看是 Seq Scan（全表扫描）还是 Index Scan（索引扫描）
```

### 5.4 索引使用原则
- 频繁出现在 WHERE / JOIN / ORDER BY 中的列适合建索引
- 不要对低基数列（如性别）单独建索引
- 索引不是越多越好，写操作会变慢

---

## 第六章 事务与并发控制

### 6.1 事务的基本用法
```sql
BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE id = 1;
    UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;   -- 提交：两条语句一起生效

-- 出错时回滚
BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE id = 1;
ROLLBACK; -- 撤销：什么都没发生
```

### 6.2 ACID 四大特性（概念了解）
- **A**tomicity（原子性）：要么全做，要么全不做
- **C**onsistency（一致性）：数据始终满足约束
- **I**solation（隔离性）：并发事务互不干扰
- **D**urability（持久性）：提交后数据不丢失

### 6.3 隔离级别（了解即可）
- Read Uncommitted → Read Committed（PostgreSQL 默认） → Repeatable Read → Serializable

---

## 第七章 PostgreSQL 特色功能（快速了解）

### 7.1 JSONB 操作
```sql
CREATE TABLE events (
    id   SERIAL PRIMARY KEY,
    data JSONB
);

INSERT INTO events (data) VALUES ('{"type": "click", "page": "/home", "duration": 3.5}');

SELECT data->>'type' AS event_type FROM events;          -- 提取字段
SELECT * FROM events WHERE data @> '{"type": "click"}';  -- 包含查询
```

### 7.2 CTE（公共表表达式 / WITH 查询）
```sql
WITH top_students AS (
    SELECT s.name, AVG(c.score) AS avg_score
    FROM students s JOIN courses c ON s.id = c.student_id
    GROUP BY s.name
)
SELECT * FROM top_students WHERE avg_score > 85;
```

### 7.3 窗口函数
```sql
SELECT name, score,
       RANK() OVER (ORDER BY score DESC) AS ranking,
       AVG(score) OVER () AS overall_avg
FROM courses c JOIN students s ON c.student_id = s.id;
```

### 7.4 其他值得知道的特性
- **视图（View）**：保存常用查询，像表一样使用
- **存储过程 / 函数（PL/pgSQL）**：在数据库内编写业务逻辑
- **触发器（Trigger）**：在数据变更时自动执行操作
- **分区表（Partitioning）**：海量数据按规则拆分存储
- **全文检索（Full Text Search）**：内置中英文搜索能力
- **扩展（Extension）**：`PostGIS`（地理空间）、`pg_trgm`（模糊匹配）等

---

## 第八章 数据库管理基础

### 8.1 用户与权限
```sql
CREATE USER app_user WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT ON students TO app_user;
REVOKE INSERT ON students FROM app_user;
```

### 8.2 备份与恢复
```bash
pg_dump mydb > backup.sql          # 导出
psql mydb < backup.sql             # 导入
pg_dump -Fc mydb > backup.dump     # 自定义格式（支持并行恢复）
pg_restore -d mydb backup.dump     # 恢复
```

### 8.3 常用运维命令
```sql
SELECT version();                              -- 查看版本
SELECT pg_size_pretty(pg_database_size('mydb')); -- 数据库大小
\dt                                            -- 列出所有表（psql）
\d students                                    -- 查看表结构（psql）
```

---

## 附录 A：SQL 语句执行顺序

> 写 SQL 时的书写顺序与数据库实际执行顺序不同，理解这一点能帮你写出更好的查询。

```
执行顺序：FROM → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT
书写顺序：SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT
```

## 附录 B：psql 常用快捷命令

| 命令 | 作用 |
|------|------|
| `\l` | 列出所有数据库 |
| `\c dbname` | 切换数据库 |
| `\dt` | 列出当前 schema 的所有表 |
| `\d tablename` | 查看表结构 |
| `\di` | 列出所有索引 |
| `\du` | 列出所有用户/角色 |
| `\timing` | 开启/关闭执行时间显示 |
| `\q` | 退出 psql |

## 附录 C：推荐学习路径

```
第一步：安装环境，用 psql 连上数据库                    （第1章）
第二步：建表、插数据、写简单查询                        （第2-4章前半）
第三步：练习 JOIN、子查询、聚合                         （第4章后半）
第四步：理解索引和 EXPLAIN                              （第5章）
第五步：了解事务，能写 BEGIN/COMMIT                      （第6章）
第六步：探索 JSONB、窗口函数等高级特性                   （第7章）
第七步：学习基本的用户权限和备份                         （第8章）
```

---

*建议配合实际操作练习，每章花 30-60 分钟动手敲 SQL，比纯看文档效果好 10 倍。*
