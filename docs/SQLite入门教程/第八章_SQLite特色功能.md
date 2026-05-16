# 第八章 SQLite 特色功能

---

## 8.1 JSON 支持

SQLite 从 3.9 版本开始内置 JSON 函数支持（默认编译启用），让你可以在关系型数据库中优雅地处理半结构化数据。

### 为什么要在 SQLite 里用 JSON？

```
传统做法：每个属性一列
┌────┬──────┬──────┬───────┐
│ id │ name │ city │ phone │
├────┼──────┼──────┼───────┤
│ 1  │ 张三 │ 北京 │ 138…  │
└────┴──────┴──────┴───────┘
→ 属性固定，加字段要 ALTER TABLE

JSON 做法：灵活属性存 JSON 列
┌────┬──────┬─────────────────────────────────┐
│ id │ name │ profile (JSON)                   │
├────┼──────┼─────────────────────────────────┤
│ 1  │ 张三 │ {"city":"北京","phone":"138…"}    │
│ 2  │ 李四 │ {"city":"上海","tags":["dev"]}    │
└────┴──────┴─────────────────────────────────┘
→ 每行的属性可以不同，无需改表结构
```

### 存储 JSON 数据

```sql
CREATE TABLE events (
    id   INTEGER PRIMARY KEY,
    type TEXT NOT NULL,
    data TEXT  -- 存储 JSON 字符串
);

INSERT INTO events (type, data) VALUES
    ('click', '{"page":"/home","x":120,"y":300}'),
    ('login', '{"user":"zhangsan","ip":"192.168.1.1","device":"iPhone"}'),
    ('order', '{"items":[{"name":"键盘","price":299},{"name":"鼠标","price":99}],"total":398}');
```

### 提取 JSON 字段

```sql
-- json_extract(json, path) —— 提取值（保留 JSON 类型）
SELECT json_extract(data, '$.page') FROM events WHERE type = 'click';
-- 结果：/home

-- 简写形式：-> 和 ->>（SQLite 3.38+）
SELECT data -> '$.page' FROM events WHERE type = 'click';   -- 返回 JSON 值（带引号）
SELECT data ->> '$.page' FROM events WHERE type = 'click';  -- 返回文本值（不带引号）

-- 提取嵌套字段
SELECT data ->> '$.items[0].name' FROM events WHERE type = 'order';
-- 结果：键盘

-- 提取多个字段
SELECT
    data ->> '$.user' AS user,
    data ->> '$.ip' AS ip,
    data ->> '$.device' AS device
FROM events WHERE type = 'login';
```

### 在 WHERE 中过滤 JSON 字段

```sql
-- 找出访问了 /home 页面的点击事件
SELECT * FROM events
WHERE type = 'click' AND data ->> '$.page' = '/home';

-- 找出使用 iPhone 登录的事件
SELECT * FROM events
WHERE data ->> '$.device' = 'iPhone';
```

> **性能提示**：如果频繁按 JSON 字段过滤，可以对表达式建索引：
> ```sql
> CREATE INDEX idx_events_page ON events(json_extract(data, '$.page'))
>     WHERE type = 'click';
> ```

### 修改 JSON 数据

```sql
-- json_set：设置 / 新增字段
UPDATE events
SET data = json_set(data, '$.page', '/about')
WHERE type = 'click';

-- json_insert：只在字段不存在时插入
UPDATE events
SET data = json_insert(data, '$.browser', 'Chrome')
WHERE type = 'click';

-- json_replace：只在字段已存在时替换
UPDATE events
SET data = json_replace(data, '$.ip', '10.0.0.1')
WHERE type = 'login';

-- json_remove：删除字段
UPDATE events
SET data = json_remove(data, '$.device')
WHERE type = 'login';
```

### 遍历 JSON 数组（json_each）

```sql
-- 展开订单中的每个商品
SELECT
    e.id,
    item.value ->> '$.name' AS item_name,
    item.value ->> '$.price' AS item_price
FROM events e, json_each(e.data, '$.items') AS item
WHERE e.type = 'order';

-- 结果：
-- 3 | 键盘 | 299
-- 3 | 鼠标 | 99
```

### 常用 JSON 函数速查

| 函数 | 作用 | 示例 |
|------|------|------|
| `json_extract(j, path)` | 提取值 | `json_extract(data, '$.name')` |
| `->` | 提取为 JSON | `data -> '$.name'` |
| `->>` | 提取为文本 | `data ->> '$.name'` |
| `json_set(j, path, val)` | 设置字段（存在则覆盖） | 见上方示例 |
| `json_insert(j, path, val)` | 插入字段（已存在则跳过） | |
| `json_replace(j, path, val)` | 替换字段（不存在则跳过） | |
| `json_remove(j, path)` | 删除字段 | |
| `json_each(j, path)` | 展开 JSON 数组 | 搭配 `FROM` 使用 |
| `json_type(j, path)` | 返回值的类型 | `'integer'`, `'text'`, `'array'` |
| `json_valid(j)` | 检查是否为合法 JSON | 返回 0 或 1 |
| `json_array(a, b, c)` | 构造 JSON 数组 | `json_array(1, 2, 3)` → `[1,2,3]` |
| `json_object(k, v, ...)` | 构造 JSON 对象 | `json_object('a', 1)` → `{"a":1}` |

---

## 8.2 全文搜索（FTS5）

FTS5（Full-Text Search 5）是 SQLite 内置的全文搜索引擎。它不是简单的 `LIKE '%关键词%'`，而是真正的**倒排索引**——可以在毫秒级内搜索大量文本。

### LIKE vs FTS5

```
LIKE '%关键词%'：
  → 全表扫描，逐行检查
  → 10 万行文档需要 10 万次字符串匹配
  → 慢！而且不支持相关性排序

FTS5 全文搜索：
  → 预先建好倒排索引（词 → 包含该词的文档列表）
  → 搜索时直接查索引，不扫描原文
  → 快！支持相关性排序、高亮、摘要
```

### 创建 FTS5 虚拟表

```sql
-- 创建全文搜索表
CREATE VIRTUAL TABLE articles USING fts5(
    title,
    content,
    author
);

-- 插入数据
INSERT INTO articles (title, content, author) VALUES
    ('SQLite 入门指南', 'SQLite 是一个嵌入式数据库引擎，适合本地应用开发。', '张三'),
    ('Redis 缓存实战', 'Redis 是一个基于内存的键值数据库，常用于缓存场景。', '李四'),
    ('数据库选型指南', 'SQLite 适合嵌入式场景，PostgreSQL 适合复杂查询。', '王五');
```

### 全文搜索查询

```sql
-- 搜索包含 "SQLite" 的文章
SELECT * FROM articles WHERE articles MATCH 'SQLite';

-- 搜索标题包含 "入门" 的文章
SELECT * FROM articles WHERE title MATCH '入门';

-- 搜索同时包含 "数据库" 和 "缓存" 的文章
SELECT * FROM articles WHERE articles MATCH '数据库 AND 缓存';

-- 搜索包含 "数据库" 或 "缓存" 的文章
SELECT * FROM articles WHERE articles MATCH '数据库 OR 缓存';

-- 搜索包含 "SQLite" 但不包含 "Redis" 的文章
SELECT * FROM articles WHERE articles MATCH 'SQLite NOT Redis';
```

### 按相关性排序

```sql
-- bm25() 返回相关性评分（越小越相关）
SELECT title, bm25(articles) AS score
FROM articles
WHERE articles MATCH 'SQLite 数据库'
ORDER BY score;
```

### 高亮与摘要

```sql
-- highlight() —— 高亮匹配词
SELECT highlight(articles, 1, '<b>', '</b>') AS highlighted_content
FROM articles
WHERE articles MATCH 'SQLite';
-- 结果：<b>SQLite</b> 是一个嵌入式数据库引擎...

-- snippet() —— 返回匹配上下文的摘要
SELECT snippet(articles, 1, '<b>', '</b>', '...', 20) AS summary
FROM articles
WHERE articles MATCH '数据库';
```

### FTS5 与普通表配合使用

FTS5 表是虚拟表，不支持一些普通表的特性（如 ALTER TABLE、自定义约束）。常见做法是用**普通表存主数据 + FTS5 表做搜索索引**：

```sql
-- 主数据表
CREATE TABLE docs (
    id      INTEGER PRIMARY KEY,
    title   TEXT,
    content TEXT,
    created TEXT
);

-- FTS5 搜索索引（content 参数指向主表）
CREATE VIRTUAL TABLE docs_fts USING fts5(
    title, content, content=docs, content_rowid=id
);

-- 手动同步数据到 FTS 索引
INSERT INTO docs_fts(rowid, title, content)
SELECT id, title, content FROM docs;

-- 搜索时查 FTS 表，取详情回主表
SELECT d.* FROM docs d
JOIN docs_fts f ON d.id = f.rowid
WHERE docs_fts MATCH 'SQLite'
ORDER BY bm25(docs_fts);
```

> **中文搜索提示**：SQLite 的 FTS5 默认分词器（unicode61）对中文支持有限。如果需要中文全文搜索，可以考虑使用 `simple` 分词器或加载第三方中文分词扩展（如 `simple-tokenizer`）。

---

## 8.3 窗口函数（SQLite 3.25+）

窗口函数可以在**不改变结果行数**的前提下，对相关行做聚合计算。它是 SQL 中最强大的特性之一。

### 窗口函数 vs 聚合函数

```
聚合函数（GROUP BY）：多行变一行
  张三 | 85
  张三 | 90  →  张三 | 87.5（平均分）
  张三 | 88

窗口函数（OVER）：每行都保留，附带计算结果
  张三 | 85 | 87.5（平均分会出现在每一行）
  张三 | 90 | 87.5
  张三 | 88 | 87.5
```

### 基本语法

```sql
函数名(参数) OVER (
    PARTITION BY 分区列    -- 可选：按什么分组
    ORDER BY 排序列        -- 可选：按什么排序
)
```

### ROW_NUMBER / RANK / DENSE_RANK —— 排名函数

```sql
-- 准备数据
CREATE TABLE scores (name TEXT, subject TEXT, score INTEGER);
INSERT INTO scores VALUES
    ('张三', '数学', 90), ('张三', '英语', 85),
    ('李四', '数学', 95), ('李四', '英语', 88),
    ('王五', '数学', 90), ('王五', '英语', 92);

-- 按总分排名
SELECT name, SUM(score) AS total,
    ROW_NUMBER() OVER (ORDER BY SUM(score) DESC) AS row_num,
    RANK()       OVER (ORDER BY SUM(score) DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY SUM(score) DESC) AS dense_rank
FROM scores
GROUP BY name;
```

三种排名函数的区别：

| 函数 | 遇到并列时 | 示例（分数 95, 90, 90, 85） |
|------|-----------|---------------------------|
| `ROW_NUMBER()` | 不并列，各有唯一编号 | 1, 2, 3, 4 |
| `RANK()` | 并列，跳过后续编号 | 1, 2, 2, 4 |
| `DENSE_RANK()` | 并列，不跳过编号 | 1, 2, 2, 3 |

### PARTITION BY —— 分区排名

```sql
-- 每个科目内部排名
SELECT name, subject, score,
    RANK() OVER (PARTITION BY subject ORDER BY score DESC) AS subject_rank
FROM scores;

-- 结果：
-- 李四 | 数学 | 95 | 1
-- 张三 | 数学 | 90 | 2
-- 王五 | 数学 | 90 | 2
-- 王五 | 英语 | 92 | 1
-- 李四 | 英语 | 88 | 2
-- 张三 | 英语 | 85 | 3
```

### LAG / LEAD —— 访问前一行 / 后一行

```sql
-- 每日销售额 & 和前一天的对比
CREATE TABLE daily_sales (date TEXT, amount REAL);
INSERT INTO daily_sales VALUES
    ('2024-01-01', 1000), ('2024-01-02', 1200),
    ('2024-01-03', 900),  ('2024-01-04', 1500);

SELECT date, amount,
    LAG(amount, 1) OVER (ORDER BY date)  AS prev_day,     -- 前一天
    LEAD(amount, 1) OVER (ORDER BY date) AS next_day,     -- 后一天
    amount - LAG(amount, 1) OVER (ORDER BY date) AS diff   -- 环比变化
FROM daily_sales;

-- 结果：
-- 2024-01-01 | 1000 | [NULL] | 1200  | [NULL]
-- 2024-01-02 | 1200 | 1000   | 900   | 200
-- 2024-01-03 | 900  | 1200   | 1500  | -300
-- 2024-01-04 | 1500 | 900    | [NULL] | 600
```

### 累计求和 / 移动平均

```sql
-- 累计销售额
SELECT date, amount,
    SUM(amount) OVER (ORDER BY date) AS running_total
FROM daily_sales;

-- 3 日移动平均
SELECT date, amount,
    AVG(amount) OVER (
        ORDER BY date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3
FROM daily_sales;
```

### 常用窗口函数一览

| 函数 | 作用 |
|------|------|
| `ROW_NUMBER()` | 唯一行号 |
| `RANK()` | 排名（并列跳号） |
| `DENSE_RANK()` | 排名（并列不跳号） |
| `NTILE(n)` | 分成 n 组 |
| `LAG(col, n)` | 前 n 行的值 |
| `LEAD(col, n)` | 后 n 行的值 |
| `FIRST_VALUE(col)` | 窗口中第一行的值 |
| `LAST_VALUE(col)` | 窗口中最后一行的值 |
| `SUM/AVG/COUNT() OVER` | 窗口内聚合 |

---

## 8.4 生成列（Generated Columns，SQLite 3.31+）

生成列是**根据其他列的值自动计算**的列，你不需要手动插入或更新它。

### 两种类型

| 类型 | 关键字 | 存储 | 特点 |
|------|--------|------|------|
| 虚拟列 | `VIRTUAL`（默认） | 不占磁盘空间 | 每次读取时实时计算 |
| 存储列 | `STORED` | 占磁盘空间 | 写入时计算并存储，可建索引 |

### 语法与示例

```sql
CREATE TABLE products (
    id       INTEGER PRIMARY KEY,
    name     TEXT,
    price    REAL,
    quantity INTEGER,
    -- 虚拟生成列：每次查询时计算
    total    REAL GENERATED ALWAYS AS (price * quantity) VIRTUAL,
    -- 存储生成列：写入时计算并存储
    label    TEXT GENERATED ALWAYS AS (name || ' ¥' || price) STORED
);

INSERT INTO products (name, price, quantity) VALUES ('键盘', 299, 10);
INSERT INTO products (name, price, quantity) VALUES ('鼠标', 99, 25);

SELECT * FROM products;
-- 1 | 键盘 | 299 | 10 | 2990 | 键盘 ¥299.0
-- 2 | 鼠标 | 99  | 25 | 2475 | 鼠标 ¥99.0
```

> **注意**：不能手动 INSERT 或 UPDATE 生成列的值，SQLite 会报错。

### 实用场景

**场景一：JSON 字段提取为可索引列**

```sql
CREATE TABLE users (
    id      INTEGER PRIMARY KEY,
    profile TEXT,  -- JSON
    -- 从 JSON 中提取 email，存储并可建索引
    email   TEXT GENERATED ALWAYS AS (json_extract(profile, '$.email')) STORED
);

CREATE INDEX idx_users_email ON users(email);

-- 现在可以高效查询
SELECT * FROM users WHERE email = 'test@test.com';
```

**场景二：全名拼接**

```sql
CREATE TABLE employees (
    id         INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name  TEXT,
    full_name  TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name) VIRTUAL
);
```

**场景三：数据校验标记**

```sql
CREATE TABLE orders (
    id     INTEGER PRIMARY KEY,
    amount REAL,
    tax    REAL,
    total  REAL GENERATED ALWAYS AS (amount + tax) STORED,
    is_big INTEGER GENERATED ALWAYS AS (amount > 1000) VIRTUAL
);
```

---

## 8.5 STRICT 表（SQLite 3.37+）—— 强制类型检查

还记得第三章讲的动态类型吗？SQLite 默认允许任何值存入任何列。STRICT 表就是为了解决这个"宽容"带来的痛点。

### 问题回顾

```sql
-- 普通表：什么都能存，悄无声息
CREATE TABLE users (id INTEGER, name TEXT, age INTEGER);
INSERT INTO users VALUES (1, '张三', 'twenty-five');  -- age 存了文本！没报错！

-- 这在生产环境可能导致难以排查的 bug
SELECT * FROM users WHERE age > 20;
-- 'twenty-five' > 20 的比较结果是什么？可能不是你期望的！
```

### STRICT 表：强制类型

```sql
-- 在表定义最后加 STRICT 关键字
CREATE TABLE users (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age  INTEGER
) STRICT;

INSERT INTO users VALUES (1, '张三', 25);        -- ✅ 正常
INSERT INTO users VALUES (2, '李四', 'twenty');   -- ❌ 报错！
-- Error: cannot store TEXT value in INTEGER column users.age
```

### STRICT 表支持的类型

STRICT 模式下，列类型**必须**是以下之一：

| 类型 | 说明 |
|------|------|
| `INTEGER` | 整数 |
| `REAL` | 浮点数 |
| `TEXT` | 文本 |
| `BLOB` | 二进制数据 |
| `ANY` | 任意类型（保持 SQLite 的灵活性） |

```sql
CREATE TABLE strict_demo (
    id    INTEGER PRIMARY KEY,
    name  TEXT,
    score REAL,
    data  BLOB,
    extra ANY      -- ANY 列接受任何类型，类似普通表的行为
) STRICT;
```

> **注意**：STRICT 表不能用 `VARCHAR(255)`、`BOOLEAN`、`DATETIME` 等类型名——只认上面 5 种。

### 普通表 vs STRICT 表

| 特性 | 普通表 | STRICT 表 |
|------|--------|----------|
| 类型检查 | 不检查，任何值都能存 | 严格检查，类型不匹配则报错 |
| 允许的类型名 | 任意（甚至可以不写） | 只能用 INTEGER/REAL/TEXT/BLOB/ANY |
| `INTEGER PRIMARY KEY` | 允许存 NULL 到 rowid | 不允许存 NULL |
| 兼容性 | 所有 SQLite 版本 | 需要 3.37+（2021 年 11 月） |
| 适合场景 | 灵活性需求高、兼容旧版本 | 数据质量要求高、新项目推荐 |

### STRICT + WITHOUT ROWID

可以同时使用两个表选项：

```sql
CREATE TABLE configs (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
) STRICT, WITHOUT ROWID;

-- WITHOUT ROWID：适合主键不是 INTEGER 的表，节省空间
-- STRICT：确保类型安全
```

> **建议**：新项目如果 SQLite 版本 ≥ 3.37，推荐默认使用 STRICT 表。它能在数据入口就拦截类型错误，避免下游出现莫名其妙的 bug。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| JSON 支持 | `json_extract` / `->` `->>`（3.38+）/ `json_set` / `json_each` |
| JSON 索引 | 对 `json_extract(col, '$.path')` 表达式建索引 |
| FTS5 全文搜索 | `CREATE VIRTUAL TABLE ... USING fts5`；`MATCH` 查询；`bm25()` 排序 |
| 窗口函数 | `ROW_NUMBER` / `RANK` / `LAG` / `LEAD` + `OVER (PARTITION BY ... ORDER BY ...)` |
| 生成列 | `GENERATED ALWAYS AS (表达式) VIRTUAL/STORED`；STORED 列可建索引 |
| STRICT 表 | 强制类型检查，只允许 INTEGER/REAL/TEXT/BLOB/ANY 五种类型 |

> **下一章预告**：学习如何在 Python、Node.js、Go 等编程语言中使用 SQLite——连接管理、参数化查询、ORM 集成。


