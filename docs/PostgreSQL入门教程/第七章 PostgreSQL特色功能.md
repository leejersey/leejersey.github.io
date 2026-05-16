# 第七章 PostgreSQL 特色功能

> 这一章介绍 PostgreSQL 区别于其他数据库的"看家本领"。这些功能不需要全部掌握，但知道它们的存在，能让你在遇到相关需求时找到正确的方向。

---

## 7.1 JSONB — 在关系型数据库中存储半结构化数据

### 为什么用 JSONB

有些数据没有固定结构——比如用户配置、日志事件、API 返回值。把它们硬塞进固定的列中既麻烦又不灵活。

PostgreSQL 的 JSONB 类型让你**在关系型数据库中原生存储和查询 JSON 数据**，兼顾了灵活性和查询能力。

> JSON vs JSONB：`JSON` 存原始文本，`JSONB` 存解析后的二进制格式。**始终用 JSONB**——它更快，支持索引。

### 基本操作

```sql
CREATE TABLE events (
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_type VARCHAR(50),
    data       JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO events (event_type, data) VALUES
    ('click', '{"page": "/home", "button": "signup", "duration": 3.5}'),
    ('click', '{"page": "/pricing", "button": "buy", "duration": 1.2}'),
    ('pageview', '{"page": "/home", "referrer": "google.com"}'),
    ('error', '{"code": 500, "message": "Internal Server Error", "stack": ["app.js:12", "router.js:45"]}');
```

### 提取 JSON 字段

```sql
-- -> 返回 JSON 类型
SELECT data->'page' FROM events;           -- 返回 "/home"（带引号的 JSON 字符串）

-- ->> 返回文本类型
SELECT data->>'page' FROM events;          -- 返回 /home（纯文本）

-- 嵌套提取
SELECT data->'stack'->>0 FROM events WHERE event_type = 'error';  -- 返回 app.js:12

-- 提取数值（需要类型转换）
SELECT (data->>'duration')::NUMERIC FROM events WHERE event_type = 'click';
```

**`->` vs `->>` 的区别**：

| 操作符 | 返回类型 | 用途 |
|--------|---------|------|
| `->` | JSON | 继续链式提取、存回 JSON 列 |
| `->>` | TEXT | 用于显示、比较、WHERE 条件 |

### 查询 JSON 数据

```sql
-- 包含查询：data 中包含 {"page": "/home"}
SELECT * FROM events WHERE data @> '{"page": "/home"}';

-- 键存在查询：data 中有 "referrer" 这个键
SELECT * FROM events WHERE data ? 'referrer';

-- 条件查询（提取字段后比较）
SELECT * FROM events WHERE data->>'page' = '/pricing';
SELECT * FROM events WHERE (data->>'duration')::NUMERIC > 2.0;
```

### 修改 JSON 数据

```sql
-- 添加/修改字段
UPDATE events SET data = data || '{"browser": "Chrome"}'
WHERE id = 1;

-- 删除字段
UPDATE events SET data = data - 'browser'
WHERE id = 1;
```

### 为 JSONB 建索引

```sql
-- GIN 索引：加速 @>、?、?| 等操作
CREATE INDEX idx_events_data ON events USING GIN (data);

-- 针对特定字段的索引
CREATE INDEX idx_events_page ON events ((data->>'page'));
```

---

## 7.2 CTE — 公共表表达式（WITH 查询）

CTE（Common Table Expression）让你**给子查询起名字**，然后在主查询中引用，代码更清晰、更易读。

### 基本语法

```sql
-- 不用 CTE 的写法（嵌套子查询，难读）
SELECT sub.name, sub.avg_score
FROM (
    SELECT s.name, AVG(c.score) AS avg_score
    FROM students s JOIN courses c ON s.id = c.student_id
    GROUP BY s.name
) AS sub
WHERE sub.avg_score > 80;

-- 用 CTE 的写法（清晰）
WITH student_avg AS (
    SELECT s.name, AVG(c.score) AS avg_score
    FROM students s
    JOIN courses c ON s.id = c.student_id
    GROUP BY s.name
)
SELECT name, avg_score
FROM student_avg
WHERE avg_score > 80;
```

两种写法结果完全相同，但 CTE 版本更容易理解。

### 多个 CTE

```sql
WITH
    -- CTE 1：每个学生的平均分
    student_avg AS (
        SELECT student_id, AVG(score) AS avg_score
        FROM courses
        GROUP BY student_id
    ),
    -- CTE 2：全班平均分
    class_avg AS (
        SELECT AVG(score) AS overall_avg FROM courses
    )
SELECT s.name, sa.avg_score, ca.overall_avg,
       CASE WHEN sa.avg_score > ca.overall_avg THEN '高于平均' ELSE '低于平均' END AS 评价
FROM students s
JOIN student_avg sa ON s.id = sa.student_id
CROSS JOIN class_avg ca;
```

### 递归 CTE（了解）

CTE 还能递归，适合处理树形结构（如组织架构、评论回复链）：

```sql
-- 示例：生成数字 1 到 10
WITH RECURSIVE numbers AS (
    SELECT 1 AS n              -- 初始条件
    UNION ALL
    SELECT n + 1 FROM numbers WHERE n < 10  -- 递归条件
)
SELECT n FROM numbers;
```

---

## 7.3 窗口函数

窗口函数是 SQL 中最强大的分析工具之一。它可以**在不合并行的情况下进行聚合计算**。

### GROUP BY vs 窗口函数的区别

```sql
-- GROUP BY：5 行变成 2 行（分组合并）
SELECT course_name, AVG(score) FROM courses GROUP BY course_name;

-- 窗口函数：5 行还是 5 行（每行多一列聚合值）
SELECT course_name, score, AVG(score) OVER (PARTITION BY course_name) AS course_avg
FROM courses;
```

窗口函数的结果：

```
 course_name | score | course_avg
-------------+-------+------------
 数据库原理   | 85.5  | 86.17
 数据库原理   | 78.0  | 86.17
 数据库原理   | 95.0  | 86.17
 操作系统     | 90.0  | 86.83
 操作系统     | 88.0  | 86.83
 ...
```

每一行都保留了，同时多了一列"该课程的平均分"。

### 基本语法

```sql
函数名() OVER (
    PARTITION BY 分组列    -- 按什么分组（可选）
    ORDER BY 排序列        -- 按什么排序（可选）
)
```

### 常用窗口函数

#### 排名函数

```sql
SELECT s.name, c.course_name, c.score,
    ROW_NUMBER() OVER (ORDER BY c.score DESC) AS 序号,
    RANK()       OVER (ORDER BY c.score DESC) AS 排名,
    DENSE_RANK() OVER (ORDER BY c.score DESC) AS 密集排名
FROM students s
JOIN courses c ON s.id = c.student_id;
```

| 函数 | 遇到并列时 |
|------|-----------|
| `ROW_NUMBER()` | 不并列，强制按行编号：1, 2, 3, 4 |
| `RANK()` | 并列后跳号：1, 1, 3, 4 |
| `DENSE_RANK()` | 并列不跳号：1, 1, 2, 3 |

#### 分区内排名

```sql
-- 每门课内部的成绩排名
SELECT s.name, c.course_name, c.score,
    RANK() OVER (PARTITION BY c.course_name ORDER BY c.score DESC) AS 课内排名
FROM students s
JOIN courses c ON s.id = c.student_id;
```

`PARTITION BY c.course_name` 表示在每门课内部各自排名。

#### 聚合窗口函数

```sql
SELECT s.name, c.course_name, c.score,
    AVG(c.score) OVER () AS 全班平均,
    AVG(c.score) OVER (PARTITION BY c.course_name) AS 课程平均,
    c.score - AVG(c.score) OVER (PARTITION BY c.course_name) AS 与课程平均差距
FROM students s
JOIN courses c ON s.id = c.student_id;
```

#### LAG / LEAD — 前后行对比

```sql
-- 查看每次考试与上一次的分差
SELECT s.name, c.course_name, c.score,
    LAG(c.score) OVER (PARTITION BY s.id ORDER BY c.id) AS 上次成绩,
    c.score - LAG(c.score) OVER (PARTITION BY s.id ORDER BY c.id) AS 进步分数
FROM students s
JOIN courses c ON s.id = c.student_id;
```

| 函数 | 作用 |
|------|------|
| `LAG(列, n)` | 取前 n 行的值（默认 n=1） |
| `LEAD(列, n)` | 取后 n 行的值（默认 n=1） |

---

## 7.4 视图（View）

视图是一条保存好的查询语句，使用时就像一张表一样。

```sql
-- 创建视图
CREATE VIEW student_scores AS
SELECT s.name, c.course_name, c.score
FROM students s
JOIN courses c ON s.id = c.student_id;

-- 使用视图（就像查表一样）
SELECT * FROM student_scores WHERE score > 85;

-- 删除视图
DROP VIEW student_scores;
```

视图的好处：
- 简化复杂查询——常用的 JOIN 封装成视图，一次定义到处用
- 权限控制——可以只给用户访问视图而不暴露底层表
- 逻辑抽象——业务逻辑变更时只改视图定义，使用者不受影响

---

## 7.5 存储函数（PL/pgSQL 简介）

PostgreSQL 允许在数据库内部编写函数，使用的语言叫 **PL/pgSQL**。

```sql
-- 创建函数：根据分数返回等级
CREATE FUNCTION score_grade(s NUMERIC) RETURNS TEXT AS $$
BEGIN
    IF s >= 90 THEN RETURN '优秀';
    ELSIF s >= 80 THEN RETURN '良好';
    ELSIF s >= 60 THEN RETURN '及格';
    ELSE RETURN '不及格';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 使用函数
SELECT s.name, c.course_name, c.score, score_grade(c.score) AS 等级
FROM students s
JOIN courses c ON s.id = c.student_id;
```

输出：

```
 name | course_name | score | 等级
------+-------------+-------+------
 张三 | 数据库原理   | 85.5  | 良好
 张三 | 操作系统     | 90.0  | 优秀
 李四 | 数据库原理   | 78.0  | 及格
 ...
```

```sql
-- 删除函数
DROP FUNCTION score_grade;
```

> 入门阶段了解即可。复杂业务逻辑建议在应用层处理，数据库函数适合封装简单、高频的计算。

---

## 7.6 其他值得知道的特性

以下功能不展开讲解，但你应该知道 PostgreSQL 有这些能力：

### 触发器（Trigger）

在数据变更时自动执行操作。比如：每次更新记录时自动更新 `updated_at` 字段。

```sql
-- 示意（简化版）
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();
```

### 分区表（Partitioning）

把一张大表按规则拆分成多个小表，查询时自动路由到对应分区，提升大数据量下的性能。

```sql
-- 按时间范围分区
CREATE TABLE logs (
    id         BIGINT,
    message    TEXT,
    created_at DATE
) PARTITION BY RANGE (created_at);

CREATE TABLE logs_2025 PARTITION OF logs FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE logs_2026 PARTITION OF logs FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
```

### 全文检索（Full Text Search）

PostgreSQL 内置全文搜索功能，不需要额外安装 Elasticsearch 等工具：

```sql
SELECT * FROM articles
WHERE to_tsvector('english', content) @@ to_tsquery('database & performance');
```

### 扩展（Extension）

PostgreSQL 的"插件系统"，常用扩展：

| 扩展 | 功能 |
|------|------|
| `PostGIS` | 地理空间数据处理 |
| `pg_trgm` | 模糊匹配、相似度搜索 |
| `uuid-ossp` | UUID 生成 |
| `pgcrypto` | 加密函数 |
| `pg_stat_statements` | SQL 性能统计 |

```sql
-- 安装扩展
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 使用扩展功能：模糊搜索
SELECT * FROM students WHERE name % '张三';  -- 相似度匹配
```

---

## 本章小结

| 特色功能 | 一句话描述 | 掌握优先级 |
|---------|-----------|-----------|
| JSONB | 在关系库中存储和查询 JSON | 高（现代应用常用） |
| CTE（WITH） | 给子查询命名，提升可读性 | 高（日常写 SQL 很有用） |
| 窗口函数 | 不合并行的聚合计算，排名/对比利器 | 高（数据分析必备） |
| 视图（View） | 把常用查询封装成"虚拟表" | 中 |
| 存储函数 | 数据库内编写逻辑函数 | 低（入门了解） |
| 触发器/分区/全文检索/扩展 | 知道有这些能力即可 | 低（按需学习） |

---

*下一章：[第八章 数据库管理基础]()*
