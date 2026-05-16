# 第五章 查询语句（SELECT）— 最核心的部分

---

## 5.1 基础查询与别名

### 查询所有列

```sql
SELECT * FROM users;
```

> **生产环境建议**：尽量避免 `SELECT *`，明确写出需要的列名。好处是减少数据传输量，而且表结构变化时代码不容易出意外。

### 查询指定列

```sql
SELECT name, age FROM users;
```

### 去重（DISTINCT）

```sql
-- 列出所有不重复的城市
SELECT DISTINCT city FROM users;

-- 多列去重：name + city 组合不重复
SELECT DISTINCT name, city FROM users;
```

### 别名（AS）

```sql
-- 列别名
SELECT name AS 姓名, age AS 年龄 FROM users;

-- 表别名（在 JOIN 时特别有用）
SELECT u.name, o.amount
FROM users AS u
JOIN orders AS o ON u.id = o.user_id;

-- AS 可以省略（但不推荐，可读性差）
SELECT name 姓名, age 年龄 FROM users;
```

### 计算列

```sql
-- 直接在 SELECT 中做计算
SELECT name, price, quantity, price * quantity AS total
FROM order_items;

-- 字符串拼接（用 || 运算符）
SELECT first_name || ' ' || last_name AS full_name FROM users;
```

---

## 5.2 条件过滤（WHERE）

WHERE 子句是查询中最常用的部分——决定**哪些行**会出现在结果中。

### 比较运算符

```sql
SELECT * FROM users WHERE age = 25;       -- 等于
SELECT * FROM users WHERE age != 25;      -- 不等于（也可写 <>）
SELECT * FROM users WHERE age > 25;       -- 大于
SELECT * FROM users WHERE age >= 25;      -- 大于等于
SELECT * FROM users WHERE age < 25;       -- 小于
SELECT * FROM users WHERE age <= 25;      -- 小于等于
```

### 逻辑运算符（AND / OR / NOT）

```sql
-- AND：多个条件同时满足
SELECT * FROM users WHERE age > 20 AND city = '北京';

-- OR：满足任一条件
SELECT * FROM users WHERE city = '北京' OR city = '上海';

-- NOT：取反
SELECT * FROM users WHERE NOT age > 30;

-- 组合使用（注意用括号明确优先级）
SELECT * FROM users
WHERE (city = '北京' OR city = '上海') AND age > 25;
```

### LIKE —— 模糊匹配

```sql
SELECT * FROM users WHERE name LIKE '张%';    -- 以"张"开头
SELECT * FROM users WHERE name LIKE '%三';    -- 以"三"结尾
SELECT * FROM users WHERE name LIKE '%明%';   -- 包含"明"
SELECT * FROM users WHERE email LIKE '%@gmail.com';  -- Gmail 用户
```

| 通配符 | 含义 | 示例 |
|--------|------|------|
| `%` | 匹配任意数量的任意字符 | `'张%'` 匹配 "张三"、"张三丰" |
| `_` | 匹配恰好一个任意字符 | `'张_'` 匹配 "张三"，不匹配 "张三丰" |

> **注意**：SQLite 的 LIKE 默认对 ASCII 字母**不区分大小写**，但对 Unicode 字符（如中文）区分大小写。

### GLOB —— 类 Unix 风格的模式匹配

```sql
SELECT * FROM files WHERE name GLOB '*.txt';   -- 以 .txt 结尾
SELECT * FROM files WHERE name GLOB '[abc]*';  -- 以 a、b 或 c 开头
SELECT * FROM files WHERE name GLOB '[0-9]*';  -- 以数字开头
```

| 通配符 | 含义 |
|--------|------|
| `*` | 匹配任意数量的任意字符（类似 LIKE 的 `%`） |
| `?` | 匹配恰好一个任意字符（类似 LIKE 的 `_`） |
| `[abc]` | 匹配方括号内的任一字符 |
| `[a-z]` | 匹配范围内的任一字符 |

> **LIKE vs GLOB**：LIKE 大小写不敏感（ASCII），GLOB **大小写敏感**。

### IN —— 列表匹配

```sql
-- 匹配多个离散值
SELECT * FROM users WHERE city IN ('北京', '上海', '广州', '深圳');

-- 等效于多个 OR
SELECT * FROM users
WHERE city = '北京' OR city = '上海' OR city = '广州' OR city = '深圳';

-- 配合子查询
SELECT * FROM users
WHERE id IN (SELECT user_id FROM orders WHERE amount > 1000);
```

### BETWEEN —— 范围匹配

```sql
-- 包含两端（闭区间）
SELECT * FROM users WHERE age BETWEEN 18 AND 30;
-- 等效于：WHERE age >= 18 AND age <= 30

-- 日期范围
SELECT * FROM orders
WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31';
```

### IS NULL / IS NOT NULL

```sql
SELECT * FROM users WHERE email IS NULL;       -- 没有填邮箱的用户
SELECT * FROM users WHERE email IS NOT NULL;   -- 填了邮箱的用户
```

> **注意**：不能写 `WHERE email = NULL`，在 SQL 中 `NULL = NULL` 的结果是 `NULL`（不是 `TRUE`），只有 `IS NULL` 才能正确判断。

---

## 5.3 排序与分页（ORDER BY / LIMIT / OFFSET）

### 排序（ORDER BY）

```sql
-- 默认升序（ASC）
SELECT * FROM users ORDER BY age;         -- 年龄从小到大
SELECT * FROM users ORDER BY age ASC;     -- 同上，显式写 ASC

-- 降序（DESC）
SELECT * FROM users ORDER BY age DESC;    -- 年龄从大到小

-- 多列排序
SELECT * FROM users ORDER BY city ASC, age DESC;
-- 先按城市字母序升序，同一城市内按年龄降序
```

### NULLS FIRST / NULLS LAST（SQLite 3.30+）

```sql
-- NULL 值排在最前面
SELECT * FROM users ORDER BY email NULLS FIRST;

-- NULL 值排在最后面
SELECT * FROM users ORDER BY email NULLS LAST;
```

> **默认行为**：SQLite 默认把 NULL 视为小于任何值，所以升序时 NULL 在最前，降序时 NULL 在最后。

### 分页（LIMIT / OFFSET）

```sql
-- 取前 10 条
SELECT * FROM users LIMIT 10;

-- 跳过前 20 条，取接下来的 10 条（第 3 页，每页 10 条）
SELECT * FROM users LIMIT 10 OFFSET 20;

-- 另一种写法（LIMIT offset, count）
SELECT * FROM users LIMIT 20, 10;  -- 等效于 LIMIT 10 OFFSET 20
```

```
分页查询的典型模式：

  第 1 页：LIMIT 10 OFFSET 0    → 第 1~10 条
  第 2 页：LIMIT 10 OFFSET 10   → 第 11~20 条
  第 3 页：LIMIT 10 OFFSET 20   → 第 21~30 条
  ...
  第 N 页：LIMIT 10 OFFSET (N-1)*10
```

> **性能提醒**：当 OFFSET 很大时（比如 `OFFSET 100000`），SQLite 仍然需要扫描并跳过前 10 万行。对于大数据量的深分页，推荐用**游标分页**（基于上一页最后一条记录的 id）：

```sql
-- 游标分页（推荐，适合大数据量）
-- 假设上一页最后一条的 id 是 1000
SELECT * FROM users WHERE id > 1000 ORDER BY id LIMIT 10;
```

---

## 5.4 聚合函数与分组

### 常用聚合函数

```sql
SELECT COUNT(*) FROM users;                      -- 总行数
SELECT COUNT(email) FROM users;                  -- email 非 NULL 的行数
SELECT COUNT(DISTINCT city) FROM users;          -- 不重复的城市数量

SELECT SUM(amount) FROM orders;                  -- 总金额
SELECT AVG(age) FROM users;                      -- 平均年龄
SELECT MAX(price) FROM products;                 -- 最高价
SELECT MIN(price) FROM products;                 -- 最低价
```

| 函数 | 作用 | NULL 处理 |
|------|------|----------|
| `COUNT(*)` | 计算总行数 | 包含 NULL 行 |
| `COUNT(列名)` | 计算该列非 NULL 的行数 | 忽略 NULL |
| `SUM(列名)` | 求和 | 忽略 NULL |
| `AVG(列名)` | 求平均值 | 忽略 NULL |
| `MAX(列名)` | 最大值 | 忽略 NULL |
| `MIN(列名)` | 最小值 | 忽略 NULL |
| `GROUP_CONCAT(列名)` | 拼接为逗号分隔的字符串 | 忽略 NULL |

### 分组（GROUP BY）

```sql
-- 按城市分组，统计每个城市的用户数
SELECT city, COUNT(*) AS user_count
FROM users
GROUP BY city;

-- 按城市分组，统计每个城市的平均年龄
SELECT city, AVG(age) AS avg_age, COUNT(*) AS total
FROM users
GROUP BY city;
```

```
GROUP BY 的执行逻辑：

  原始数据                    分组结果
  ┌──────┬──────┐            ┌──────┬───────────┐
  │ city │ age  │            │ city │ COUNT(*)  │
  ├──────┼──────┤            ├──────┼───────────┤
  │ 北京 │ 25   │  ──┐      │ 北京 │ 2         │
  │ 上海 │ 30   │  ──┼──→   │ 上海 │ 2         │
  │ 北京 │ 28   │  ──┘      │ 广州 │ 1         │
  │ 上海 │ 22   │            └──────┴───────────┘
  │ 广州 │ 35   │
  └──────┴──────┘
```

### 分组后过滤（HAVING）

`WHERE` 在**分组前**过滤行，`HAVING` 在**分组后**过滤组：

```sql
-- 找出用户数 > 10 的城市
SELECT city, COUNT(*) AS user_count
FROM users
GROUP BY city
HAVING user_count > 10;

-- WHERE + HAVING 组合
SELECT city, AVG(age) AS avg_age
FROM users
WHERE age > 18            -- 先过滤：只统计成年用户
GROUP BY city
HAVING avg_age > 25;      -- 再过滤：只要平均年龄 > 25 的城市
```

```
SQL 执行顺序：

  FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT

  WHERE  过滤的是「原始行」  → 分组前  → 不能用聚合函数
  HAVING 过滤的是「分组结果」 → 分组后  → 可以用聚合函数
```

### GROUP_CONCAT —— 拼接分组内的值

```sql
-- 列出每个部门的所有员工姓名
SELECT dept, GROUP_CONCAT(name, '、') AS members
FROM employees
GROUP BY dept;

-- 结果示例：
-- 技术部 | 张三、李四、王五
-- 市场部 | 赵六、孙七
```

---

## 5.5 多表联查（JOIN）

真实项目中，数据分散在多张表里。JOIN 就是把它们"拼"在一起查询。

### 准备测试数据

```sql
CREATE TABLE students (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age  INTEGER
);

CREATE TABLE courses (
    id         INTEGER PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    course     TEXT NOT NULL,
    score      INTEGER
);

INSERT INTO students VALUES (1, '张三', 20), (2, '李四', 22), (3, '王五', 21);
INSERT INTO courses VALUES (1, 1, '数学', 85), (2, 1, '英语', 90),
                           (3, 2, '数学', 78), (4, 2, '物理', 92);
-- 注意：王五（id=3）没有选课记录
```

### INNER JOIN —— 只返回两边都匹配的行

```sql
SELECT s.name, c.course, c.score
FROM students s
INNER JOIN courses c ON s.id = c.student_id;
```

```
结果（王五没有选课记录，不出现）：
  张三 | 数学 | 85
  张三 | 英语 | 90
  李四 | 数学 | 78
  李四 | 物理 | 92
```

```
INNER JOIN 图示：

  students          courses
  ┌────┬─────┐     ┌────┬─────┬──────┐
  │ id │name │     │ id │s_id │course│
  ├────┼─────┤     ├────┼─────┼──────┤
  │ 1  │张三 │──┐  │ 1  │ 1   │数学  │
  │ 2  │李四 │──┼──│ 2  │ 1   │英语  │
  │ 3  │王五 │✗ │  │ 3  │ 2   │数学  │
  └────┴─────┘  └──│ 4  │ 2   │物理  │
                   └────┴─────┴──────┘

  ✗ 王五没有匹配行 → 不出现在结果中
```

### LEFT JOIN —— 左表全保留，右表无匹配则为 NULL

```sql
SELECT s.name, c.course, c.score
FROM students s
LEFT JOIN courses c ON s.id = c.student_id;
```

```
结果（王五出现了，但选课信息为 NULL）：
  张三 | 数学   | 85
  张三 | 英语   | 90
  李四 | 数学   | 78
  李四 | 物理   | 92
  王五 | [NULL] | [NULL]   ← LEFT JOIN 保留了左表的所有行
```

### 用 LEFT JOIN 找"没有 XX 的记录"

```sql
-- 找出没有选课的学生
SELECT s.name
FROM students s
LEFT JOIN courses c ON s.id = c.student_id
WHERE c.id IS NULL;
-- 结果：王五
```

> **技巧**：`LEFT JOIN` + `WHERE right_table.column IS NULL` 是查找"不存在关联"的经典模式。

### CROSS JOIN —— 笛卡尔积

返回两张表的所有可能组合（行数 = 左表行数 × 右表行数）：

```sql
-- 生成所有学生 × 所有课程的组合（用于生成排课表等场景）
SELECT s.name, c.course
FROM students s
CROSS JOIN (SELECT DISTINCT course FROM courses) c;
```

> **注意**：CROSS JOIN 不需要 ON 子句。行数可能爆炸增长，使用时要谨慎。

### 自连接（Self Join）

表和自己 JOIN，常用于处理层级关系：

```sql
CREATE TABLE employees (
    id         INTEGER PRIMARY KEY,
    name       TEXT,
    manager_id INTEGER REFERENCES employees(id)
);

INSERT INTO employees VALUES (1, '老板', NULL),
                             (2, '张经理', 1),
                             (3, '李员工', 2);

-- 查询每个员工和他的上级
SELECT e.name AS 员工, m.name AS 上级
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;

-- 结果：
-- 老板    | [NULL]
-- 张经理  | 老板
-- 李员工  | 张经理
```

### 多表 JOIN

```sql
-- 三表联查：学生 + 选课 + 成绩等级
SELECT s.name, c.course, c.score,
       CASE
           WHEN c.score >= 90 THEN '优秀'
           WHEN c.score >= 80 THEN '良好'
           WHEN c.score >= 60 THEN '及格'
           ELSE '不及格'
       END AS grade
FROM students s
INNER JOIN courses c ON s.id = c.student_id
ORDER BY s.name, c.course;
```

---

## 5.6 子查询与 CTE（WITH 语句）

### WHERE 子查询

子查询可以嵌套在 WHERE 中，作为条件的一部分：

```sql
-- 找出选了"数学"课的学生
SELECT * FROM students
WHERE id IN (SELECT student_id FROM courses WHERE course = '数学');

-- 找出年龄大于平均年龄的用户
SELECT * FROM users WHERE age > (SELECT AVG(age) FROM users);
```

### FROM 子查询（派生表）

子查询也可以放在 FROM 中，作为一张"临时表"使用：

```sql
-- 先算出每个学生的平均分，再筛选平均分 > 85 的
SELECT sub.name, sub.avg_score
FROM (
    SELECT s.name, AVG(c.score) AS avg_score
    FROM students s
    JOIN courses c ON s.id = c.student_id
    GROUP BY s.name
) AS sub
WHERE sub.avg_score > 85;
```

### EXISTS / NOT EXISTS

`EXISTS` 检查子查询是否返回了至少一行。比 `IN` 在某些场景下性能更好：

```sql
-- 找出至少选了一门课的学生
SELECT * FROM students s
WHERE EXISTS (
    SELECT 1 FROM courses c WHERE c.student_id = s.id
);

-- 找出没有选任何课的学生（等效于前面的 LEFT JOIN + IS NULL）
SELECT * FROM students s
WHERE NOT EXISTS (
    SELECT 1 FROM courses c WHERE c.student_id = s.id
);
```

```
IN vs EXISTS 选择建议：

  子查询结果集很小  → IN 更直观
  子查询结果集很大  → EXISTS 通常更快（可以提前终止）
  需要关联外部表    → EXISTS（相关子查询）
```

### CTE —— 公共表表达式（WITH 语句）

CTE 让你把复杂查询拆成多个命名步骤，大幅提升可读性：

```sql
-- 不用 CTE（一坨嵌套，难读）
SELECT name, avg_score FROM (
    SELECT s.name, AVG(c.score) AS avg_score
    FROM students s JOIN courses c ON s.id = c.student_id
    GROUP BY s.name
) WHERE avg_score > 85;

-- 用 CTE（清晰分步）
WITH student_avg AS (
    SELECT s.name, AVG(c.score) AS avg_score
    FROM students s
    JOIN courses c ON s.id = c.student_id
    GROUP BY s.name
)
SELECT name, avg_score
FROM student_avg
WHERE avg_score > 85;
```

### 多个 CTE 串联

```sql
WITH
-- 第一步：算每个学生的总成绩
score_sum AS (
    SELECT student_id, SUM(score) AS total
    FROM courses
    GROUP BY student_id
),
-- 第二步：算每个学生的选课数
course_count AS (
    SELECT student_id, COUNT(*) AS num_courses
    FROM courses
    GROUP BY student_id
)
-- 第三步：合并两步结果
SELECT s.name, ss.total, cc.num_courses,
       ROUND(1.0 * ss.total / cc.num_courses, 1) AS avg_score
FROM students s
JOIN score_sum ss ON s.id = ss.student_id
JOIN course_count cc ON s.id = cc.student_id
ORDER BY avg_score DESC;
```

> **CTE 的好处**：给"中间结果"起名字，让 SQL 像写文章一样层层递进，而不是像俄罗斯套娃一样层层嵌套。

### 递归 CTE（了解即可）

递归 CTE 可以处理**层级/树形结构**数据：

```sql
-- 递归查询：从"老板"开始，找出整个组织层级
WITH RECURSIVE org_tree AS (
    -- 起始行：没有上级的人（老板）
    SELECT id, name, manager_id, 0 AS level
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    -- 递归步：找出每一级的下属
    SELECT e.id, e.name, e.manager_id, t.level + 1
    FROM employees e
    JOIN org_tree t ON e.manager_id = t.id
)
SELECT name, level,
       CASE level
           WHEN 0 THEN '老板'
           WHEN 1 THEN '├── 总监'
           WHEN 2 THEN '│   ├── 经理'
           ELSE '│   │   ├── 员工'
       END AS position
FROM org_tree
ORDER BY level;
```

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| 基础查询 | `SELECT` 列 / `DISTINCT` 去重 / `AS` 别名 / 计算列 |
| 条件过滤 | `WHERE` + 比较 / `AND` `OR` / `LIKE` `GLOB` / `IN` / `BETWEEN` / `IS NULL` |
| 排序分页 | `ORDER BY` + `LIMIT` / `OFFSET`；大数据推荐游标分页 |
| 聚合分组 | `COUNT` `SUM` `AVG` `MAX` `MIN` + `GROUP BY` + `HAVING` |
| JOIN | `INNER JOIN`（交集）/ `LEFT JOIN`（左全保留）/ `CROSS JOIN`（笛卡尔积）/ 自连接 |
| 子查询 | `WHERE IN` / `FROM` 派生表 / `EXISTS` |
| CTE | `WITH ... AS` 命名中间结果；递归 CTE 处理树形数据 |

```
再次回顾 SQL 执行顺序（写查询时心里默念）：

  FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT
```

> **下一章预告**：学习索引与查询优化——如何用 `CREATE INDEX` 和 `EXPLAIN QUERY PLAN` 让你的查询快 100 倍。


