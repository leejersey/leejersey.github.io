# 第四章 查询语句（SELECT）— 最核心的部分

> SELECT 是 SQL 中使用频率最高的语句，也是数据分析的核心武器。本章内容较多，建议边看边敲。

---

## 前置说明

本章所有示例基于第三章实战练习中插入的数据。如果你的表中没有数据，请先执行第三章 3.5 节的插入语句。

当前数据概况：
- `students` 表：张三、李四、王五、赵六、孙七（5 个学生）
- `courses` 表：每人 1~2 门课程和成绩

---

## 4.1 基础查询

### 查所有列

```sql
SELECT * FROM students;
```

`*` 代表所有列。简单直接，但在生产环境中建议明确指定列名。

### 查指定列

```sql
SELECT name, age FROM students;
```

只返回你需要的列，效率更高，可读性更好。

### 去重（DISTINCT）

```sql
SELECT DISTINCT age FROM students;
```

返回所有不重复的年龄值。

### 别名（AS）

```sql
SELECT name AS 姓名, age AS 年龄 FROM students;
```

给列取一个更易读的名字。`AS` 可以省略，但为了可读性建议保留。

表也可以起别名（在 JOIN 中特别有用）：

```sql
SELECT s.name, s.age FROM students AS s;
-- 或省略 AS
SELECT s.name, s.age FROM students s;
```

### 计算列

```sql
SELECT name, age, age + 10 AS age_in_10_years FROM students;
```

你可以在 SELECT 中进行计算，结果作为一个虚拟列返回。

### 字符串拼接

```sql
SELECT name || ' (' || email || ')' AS contact FROM students;
```

PostgreSQL 用 `||` 拼接字符串。

---

## 4.2 条件过滤（WHERE）

WHERE 决定了"查哪些行"。

### 比较运算符

```sql
SELECT * FROM students WHERE age = 20;     -- 等于
SELECT * FROM students WHERE age != 20;    -- 不等于（也可以用 <>）
SELECT * FROM students WHERE age > 21;     -- 大于
SELECT * FROM students WHERE age >= 21;    -- 大于等于
SELECT * FROM students WHERE age < 22;     -- 小于
SELECT * FROM students WHERE age <= 22;    -- 小于等于
```

### BETWEEN — 范围

```sql
SELECT * FROM students WHERE age BETWEEN 20 AND 22;
-- 等价于 WHERE age >= 20 AND age <= 22（包含两端）
```

### IN — 多值匹配

```sql
SELECT * FROM students WHERE age IN (20, 22, 24);
-- 等价于 WHERE age = 20 OR age = 22 OR age = 24
```

### LIKE — 模糊匹配

```sql
SELECT * FROM students WHERE name LIKE '张%';    -- 以"张"开头
SELECT * FROM students WHERE name LIKE '%四';     -- 以"四"结尾
SELECT * FROM students WHERE email LIKE '%example%'; -- 包含"example"
```

通配符说明：
- `%`：匹配任意数量的任意字符
- `_`：匹配恰好一个任意字符

```sql
SELECT * FROM students WHERE name LIKE '_四';    -- 名字是两个字，第二个字是"四"
```

> PostgreSQL 还支持 `ILIKE`，不区分大小写的模糊匹配。

### IS NULL / IS NOT NULL

```sql
SELECT * FROM students WHERE email IS NULL;       -- 邮箱为空
SELECT * FROM students WHERE email IS NOT NULL;   -- 邮箱不为空
```

> **注意**：不能用 `= NULL` 或 `!= NULL`，必须用 `IS NULL` / `IS NOT NULL`。因为在 SQL 中 `NULL` 表示"未知"，任何与 NULL 的比较结果都是 NULL（既不是 true 也不是 false）。

### 逻辑运算符（AND / OR / NOT）

```sql
-- AND：所有条件同时满足
SELECT * FROM students WHERE age > 20 AND name LIKE '李%';

-- OR：任一条件满足即可
SELECT * FROM students WHERE age = 20 OR age = 23;

-- NOT：取反
SELECT * FROM students WHERE NOT age = 20;

-- 组合使用时，用括号明确优先级
SELECT * FROM students
WHERE (age > 20 OR name LIKE '张%') AND email IS NOT NULL;
```

---

## 4.3 排序（ORDER BY）

### 基本排序

```sql
SELECT * FROM students ORDER BY age;           -- 升序（默认）
SELECT * FROM students ORDER BY age ASC;       -- 显式指定升序
SELECT * FROM students ORDER BY age DESC;      -- 降序
```

### 多列排序

```sql
SELECT * FROM students ORDER BY age DESC, name ASC;
-- 先按年龄从大到小，年龄相同的按姓名从小到大
```

### NULL 的排序位置

```sql
SELECT * FROM students ORDER BY email ASC NULLS FIRST;   -- NULL 排最前
SELECT * FROM students ORDER BY email ASC NULLS LAST;    -- NULL 排最后（默认）
```

---

## 4.4 分页（LIMIT / OFFSET）

### 取前 N 条

```sql
SELECT * FROM students ORDER BY age LIMIT 3;
-- 返回年龄最小的 3 个学生
```

### 跳过 N 条再取 M 条

```sql
SELECT * FROM students ORDER BY id LIMIT 10 OFFSET 20;
-- 跳过前 20 条，取接下来的 10 条（第 21~30 条）
```

这是实现**分页**的经典方式：
- 第 1 页：`LIMIT 10 OFFSET 0`
- 第 2 页：`LIMIT 10 OFFSET 10`
- 第 3 页：`LIMIT 10 OFFSET 20`
- 第 N 页：`LIMIT 10 OFFSET (N-1)*10`

> **注意**：`OFFSET` 大了之后性能会下降，因为数据库仍然要扫描被跳过的行。大数据量的分页推荐使用"游标分页"（基于 WHERE + 上一页最后一行的 ID）。

---

## 4.5 聚合函数

聚合函数对一组行进行计算，返回单个值。

### 常用聚合函数

| 函数 | 作用 | 示例 |
|------|------|------|
| `COUNT(*)` | 计算行数 | `SELECT COUNT(*) FROM students` |
| `COUNT(列)` | 计算非 NULL 的行数 | `SELECT COUNT(email) FROM students` |
| `SUM(列)` | 求和 | `SELECT SUM(score) FROM courses` |
| `AVG(列)` | 平均值 | `SELECT AVG(score) FROM courses` |
| `MAX(列)` | 最大值 | `SELECT MAX(score) FROM courses` |
| `MIN(列)` | 最小值 | `SELECT MIN(age) FROM students` |

```sql
SELECT
    COUNT(*) AS 总人数,
    AVG(age) AS 平均年龄,
    MAX(age) AS 最大年龄,
    MIN(age) AS 最小年龄
FROM students;
```

---

## 4.6 分组（GROUP BY）

GROUP BY 把相同值的行分成一组，然后对每组分别使用聚合函数。

### 基本用法

```sql
-- 每个年龄有多少人
SELECT age, COUNT(*) AS 人数
FROM students
GROUP BY age;
```

输出类似：

```
 age | 人数
-----+-----
  20 |   2
  21 |   1
  22 |   1
  23 |   1
```

### 多列分组

```sql
-- 每门课的平均分
SELECT course_name, AVG(score) AS avg_score
FROM courses
GROUP BY course_name;
```

### HAVING — 过滤分组结果

`WHERE` 在分组前过滤行，`HAVING` 在分组后过滤组。

```sql
-- 平均分超过 85 的课程
SELECT course_name, AVG(score) AS avg_score
FROM courses
GROUP BY course_name
HAVING AVG(score) > 85;
```

**WHERE vs HAVING 对比**：

```sql
-- WHERE：在分组前过滤（过滤"行"）
SELECT course_name, AVG(score)
FROM courses
WHERE score > 60         -- 先排除不及格的成绩
GROUP BY course_name;

-- HAVING：在分组后过滤（过滤"组"）
SELECT course_name, AVG(score)
FROM courses
GROUP BY course_name
HAVING AVG(score) > 85;  -- 只保留平均分 > 85 的课程

-- 两者可以同时使用
SELECT course_name, AVG(score) AS avg_score
FROM courses
WHERE score >= 60
GROUP BY course_name
HAVING AVG(score) > 80;
```

---

## 4.7 多表联查（JOIN）

现实世界的数据分散在多张表中。JOIN 让你把它们关联起来一起查询。

### 理解 JOIN 的思路

假设要查"每个学生选了什么课、考了多少分"。数据分布在两张表中：

```
students 表                    courses 表
+----+------+                 +----+------------+----------+-------+
| id | name |                 | id | student_id | course   | score |
+----+------+                 +----+------------+----------+-------+
|  1 | 张三 |                 |  1 |     1      | 数据库   |  85.5 |
|  2 | 李四 |                 |  2 |     1      | 操作系统 |  90.0 |
|  3 | 王五 |                 |  3 |     2      | 数据库   |  78.0 |
+----+------+                 +----+------------+----------+-------+
```

通过 `students.id = courses.student_id` 把两张表"拼"起来。

### INNER JOIN（内连接）

**只返回两边都有匹配的行。**

```sql
SELECT s.name, c.course_name, c.score
FROM students s
INNER JOIN courses c ON s.id = c.student_id;
```

结果：

```
 name | course_name | score
------+-------------+-------
 张三 | 数据库原理   | 85.5
 张三 | 操作系统     | 90.0
 李四 | 数据库原理   | 78.0
 ...
```

`INNER` 可以省略，`JOIN` 默认就是内连接。

### LEFT JOIN（左连接）

**左表所有行都保留，右表没有匹配的地方填 NULL。**

```sql
SELECT s.name, c.course_name, c.score
FROM students s
LEFT JOIN courses c ON s.id = c.student_id;
```

如果某个学生没有选课记录，他的名字仍然会出现，课程名和分数为 NULL。

这是最常用的 JOIN 类型——"查所有学生，顺便看看有没有选课"。

### RIGHT JOIN（右连接）

和 LEFT JOIN 相反——**右表所有行保留**。实际中很少用，因为交换表的顺序用 LEFT JOIN 就能实现相同效果。

### FULL OUTER JOIN（全外连接）

**两边都保留**，没有匹配的地方填 NULL。适用于需要看到"两边都有哪些不匹配"的场景。

```sql
SELECT s.name, c.course_name
FROM students s
FULL OUTER JOIN courses c ON s.id = c.student_id;
```

### JOIN 类型速查图

```
         INNER JOIN              LEFT JOIN
     ┌───────────────┐      ┌───────────────┐
     │   ┌───┐       │      │ ┌─────┐       │
     │   │ A ∩ B │    │      │ │  A  │∩ B│   │
     │   └───┘       │      │ └─────┘       │
     └───────────────┘      └───────────────┘
      只有交集                 A 全部 + 交集

         RIGHT JOIN           FULL OUTER JOIN
     ┌───────────────┐      ┌───────────────┐
     │       ┌─────┐ │      │ ┌─────────────┐│
     │    │A ∩│  B  │ │      │ │  A  ∪  B   ││
     │       └─────┘ │      │ └─────────────┘│
     └───────────────┘      └───────────────┘
      B 全部 + 交集            A 和 B 的并集
```

### 多表 JOIN

可以连续 JOIN 多张表：

```sql
SELECT s.name, c.course_name, c.score, t.teacher_name
FROM students s
JOIN courses c ON s.id = c.student_id
JOIN teachers t ON c.teacher_id = t.id;
```

---

## 4.8 子查询

子查询就是"SQL 里面嵌套 SQL"。外层查询依赖内层查询的结果。

### WHERE 中的子查询

```sql
-- 查询"选了数据库原理"的学生信息
SELECT * FROM students
WHERE id IN (
    SELECT student_id FROM courses WHERE course_name = '数据库原理'
);
```

思路：先用子查询找到选了数据库原理的 `student_id` 列表，再在外层查询中用 `IN` 筛选。

### 标量子查询（返回单个值）

```sql
-- 查询年龄高于平均年龄的学生
SELECT * FROM students
WHERE age > (SELECT AVG(age) FROM students);
```

### EXISTS 子查询

```sql
-- 查询至少选了一门课的学生
SELECT * FROM students s
WHERE EXISTS (
    SELECT 1 FROM courses c WHERE c.student_id = s.id
);
```

`EXISTS` 只关心子查询有没有结果，不关心返回什么——如果子查询至少返回一行，结果为 true。

### FROM 中的子查询（派生表）

```sql
-- 查询每个学生的平均分，再筛选平均分 > 80 的
SELECT sub.name, sub.avg_score
FROM (
    SELECT s.name, AVG(c.score) AS avg_score
    FROM students s
    JOIN courses c ON s.id = c.student_id
    GROUP BY s.name
) AS sub
WHERE sub.avg_score > 80;
```

> **提示**：FROM 中的子查询必须有别名（这里是 `sub`）。

---

## 4.9 SQL 的书写顺序 vs 执行顺序

这是一个非常重要的概念。我们写 SQL 的顺序和数据库实际执行的顺序是不同的：

```
书写顺序                         执行顺序
──────                          ──────
SELECT   ← 5                   FROM     ← 1（确定数据来源）
FROM     ← 1                   WHERE    ← 2（过滤行）
WHERE    ← 2                   GROUP BY ← 3（分组）
GROUP BY ← 3                   HAVING   ← 4（过滤分组）
HAVING   ← 4                   SELECT   ← 5（选择列、计算）
ORDER BY ← 6                   ORDER BY ← 6（排序）
LIMIT    ← 7                   LIMIT    ← 7（限制行数）
```

**理解这个顺序的实际意义**：

- 在 `WHERE` 中不能使用 `SELECT` 里定义的别名（因为 WHERE 先于 SELECT 执行）
- 在 `HAVING` 中可以使用聚合函数（因为 GROUP BY 在 HAVING 之前执行）
- `ORDER BY` 中可以使用 `SELECT` 中的别名（因为 ORDER BY 在 SELECT 之后执行）

```sql
-- 错误：WHERE 中不能用 SELECT 定义的别名
SELECT age, COUNT(*) AS cnt FROM students
GROUP BY age
WHERE cnt > 1;    -- ✗ ERROR

-- 正确：用 HAVING
SELECT age, COUNT(*) AS cnt FROM students
GROUP BY age
HAVING COUNT(*) > 1;  -- ✓

-- 正确：ORDER BY 中可以用别名
SELECT age, COUNT(*) AS cnt FROM students
GROUP BY age
ORDER BY cnt DESC;    -- ✓
```

---

## 4.10 实战练习

```sql
-- 1. 基础查询：查看所有学生的姓名和邮箱
SELECT name, email FROM students;

-- 2. 条件查询：查找年龄 20~22 岁的学生
SELECT * FROM students WHERE age BETWEEN 20 AND 22;

-- 3. 模糊查询：查找邮箱包含"example"的学生
SELECT * FROM students WHERE email LIKE '%example%';

-- 4. 排序分页：按年龄降序，取前 3 条
SELECT * FROM students ORDER BY age DESC LIMIT 3;

-- 5. 聚合查询：每门课的最高分、最低分、平均分
SELECT
    course_name,
    MAX(score) AS 最高分,
    MIN(score) AS 最低分,
    ROUND(AVG(score), 1) AS 平均分,
    COUNT(*) AS 选课人数
FROM courses
GROUP BY course_name
ORDER BY 平均分 DESC;

-- 6. JOIN 查询：查看每个学生的选课和成绩
SELECT s.name, c.course_name, c.score
FROM students s
LEFT JOIN courses c ON s.id = c.student_id
ORDER BY s.name, c.score DESC;

-- 7. 子查询：查找成绩高于全班平均分的选课记录
SELECT s.name, c.course_name, c.score
FROM students s
JOIN courses c ON s.id = c.student_id
WHERE c.score > (SELECT AVG(score) FROM courses);

-- 8. 综合查询：找出每个学生的最高成绩，且只显示最高成绩 > 85 的
SELECT s.name, MAX(c.score) AS best_score
FROM students s
JOIN courses c ON s.id = c.student_id
GROUP BY s.name
HAVING MAX(c.score) > 85
ORDER BY best_score DESC;
```

---

## 本章小结

| 知识点 | 关键语法 |
|--------|---------|
| 基础查询 | `SELECT 列 FROM 表` |
| 条件过滤 | `WHERE`、`BETWEEN`、`IN`、`LIKE`、`IS NULL`、`AND/OR/NOT` |
| 排序 | `ORDER BY 列 ASC/DESC` |
| 分页 | `LIMIT n OFFSET m` |
| 聚合 | `COUNT`、`SUM`、`AVG`、`MAX`、`MIN` |
| 分组 | `GROUP BY` + `HAVING` |
| 多表联查 | `INNER JOIN`、`LEFT JOIN`、`RIGHT JOIN`、`FULL OUTER JOIN` |
| 子查询 | `WHERE ... IN (SELECT ...)`、`EXISTS`、FROM 子查询 |
| 执行顺序 | FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT |

> **本章是整个教程的核心**。如果你时间有限，把这一章练熟就够应付大多数日常工作了。

---

*下一章：[第五章 索引与性能基础]()*
