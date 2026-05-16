# 第九章 在项目中使用 SQLite

---

## 9.1 Python —— sqlite3 标准库

Python 内置了 `sqlite3` 模块，不需要安装任何第三方库就能使用 SQLite。

### 基础用法：连接、执行、关闭

```python
import sqlite3

# 连接数据库（文件不存在则自动创建）
conn = sqlite3.connect('my_app.db')

# 创建游标
cursor = conn.cursor()

# 执行 SQL
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT NOT NULL,
        email TEXT UNIQUE,
        age   INTEGER
    )
''')

# 插入数据
cursor.execute(
    'INSERT INTO users (name, email, age) VALUES (?, ?, ?)',
    ('张三', 'zhangsan@test.com', 25)
)

# 提交事务
conn.commit()

# 查询数据
cursor.execute('SELECT * FROM users')
rows = cursor.fetchall()
for row in rows:
    print(row)  # (1, '张三', 'zhangsan@test.com', 25)

# 关闭连接
conn.close()
```

### 推荐写法：使用 with 语句

```python
import sqlite3

# with 语句自动管理事务：正常退出 → commit，异常退出 → rollback
with sqlite3.connect('my_app.db') as conn:
    conn.execute('INSERT INTO users (name, email, age) VALUES (?, ?, ?)',
                 ('李四', 'lisi@test.com', 30))
    # 不需要手动 commit，with 块结束时自动提交
```

### 查询结果作为字典

```python
import sqlite3

conn = sqlite3.connect('my_app.db')
conn.row_factory = sqlite3.Row  # 关键：设置行工厂

cursor = conn.execute('SELECT * FROM users WHERE id = ?', (1,))
user = cursor.fetchone()

# 现在可以用列名访问
print(user['name'])   # 张三
print(user['email'])  # zhangsan@test.com
```

### 批量操作

```python
import sqlite3

users = [
    ('王五', 'wangwu@test.com', 22),
    ('赵六', 'zhaoliu@test.com', 28),
    ('孙七', 'sunqi@test.com', 35),
]

with sqlite3.connect('my_app.db') as conn:
    # executemany：一次插入多行
    conn.executemany(
        'INSERT INTO users (name, email, age) VALUES (?, ?, ?)',
        users
    )
```

### 推荐的连接初始化配置

```python
import sqlite3

def get_connection(db_path: str) -> sqlite3.Connection:
    """创建一个配置良好的 SQLite 连接"""
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row

    # 推荐的 PRAGMA 配置
    conn.execute('PRAGMA journal_mode=WAL')        # WAL 模式
    conn.execute('PRAGMA synchronous=NORMAL')      # 平衡安全与性能
    conn.execute('PRAGMA foreign_keys=ON')         # 启用外键
    conn.execute('PRAGMA busy_timeout=5000')       # 锁等待 5 秒
    conn.execute('PRAGMA cache_size=-64000')       # 64 MB 缓存

    return conn

# 使用
conn = get_connection('my_app.db')
```

> **重要提醒**：`?` 占位符是防止 SQL 注入的关键。**永远不要**用 f-string 或 `%` 拼接 SQL 参数！

---

## 9.2 Node.js —— better-sqlite3

Node.js 中最推荐的 SQLite 库是 `better-sqlite3`——它是**同步 API**（对 SQLite 来说同步更合理，因为是本地文件操作），性能远超异步方案。

### 安装

```bash
npm install better-sqlite3
```

### 基础用法

```javascript
const Database = require('better-sqlite3');

// 打开数据库
const db = new Database('my_app.db');

// 推荐的 PRAGMA 配置
db.pragma('journal_mode = WAL');
db.pragma('synchronous = NORMAL');
db.pragma('foreign_keys = ON');
db.pragma('busy_timeout = 5000');

// 建表
db.exec(`
    CREATE TABLE IF NOT EXISTS users (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT NOT NULL,
        email TEXT UNIQUE,
        age   INTEGER
    )
`);

// 插入数据（使用 prepared statement）
const insert = db.prepare(
    'INSERT INTO users (name, email, age) VALUES (?, ?, ?)'
);
insert.run('张三', 'zhangsan@test.com', 25);

// 查询单行
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(1);
console.log(user);
// { id: 1, name: '张三', email: 'zhangsan@test.com', age: 25 }

// 查询多行
const users = db.prepare('SELECT * FROM users WHERE age > ?').all(20);
console.log(users);

// 关闭
db.close();
```

### 命名参数

```javascript
const insert = db.prepare(
    'INSERT INTO users (name, email, age) VALUES (@name, @email, @age)'
);

insert.run({ name: '李四', email: 'lisi@test.com', age: 30 });
```

### 事务（批量操作必用）

```javascript
// better-sqlite3 的 transaction() 会自动 BEGIN/COMMIT/ROLLBACK
const insertMany = db.transaction((users) => {
    const insert = db.prepare(
        'INSERT INTO users (name, email, age) VALUES (?, ?, ?)'
    );
    for (const user of users) {
        insert.run(user.name, user.email, user.age);
    }
});

// 一次性插入 1000 条，自动包在事务里
insertMany([
    { name: '王五', email: 'wangwu@test.com', age: 22 },
    { name: '赵六', email: 'zhaoliu@test.com', age: 28 },
    // ... 更多数据
]);
```

### 另一个选择：sql.js（纯 JavaScript 实现）

```
better-sqlite3  → 原生 C 绑定，性能最好，但需要编译
sql.js          → SQLite 编译为 WebAssembly，纯 JS，无需编译
                  适合：Electron、浏览器、不能装原生依赖的环境
```

```javascript
// sql.js 示例
const initSqlJs = require('sql.js');

async function main() {
    const SQL = await initSqlJs();
    const db = new SQL.Database();

    db.run('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)');
    db.run('INSERT INTO test VALUES (1, "hello")');

    const result = db.exec('SELECT * FROM test');
    console.log(result);

    // 导出为二进制（可保存到文件）
    const data = db.export();
    const buffer = Buffer.from(data);
    require('fs').writeFileSync('database.db', buffer);
}

main();
```

---

## 9.3 Go —— go-sqlite3

Go 语言有两个主流 SQLite 库：

| 库 | 特点 | 适合场景 |
|-----|------|---------|
| `mattn/go-sqlite3` | CGo 绑定，性能好 | 可以安装 C 编译器的环境 |
| `modernc.org/sqlite` | 纯 Go 实现，无 CGo | 交叉编译、不想装 C 编译器 |

### 安装

```bash
# CGo 方案（需要 GCC）
go get github.com/mattn/go-sqlite3

# 纯 Go 方案（无 CGo 依赖）
go get modernc.org/sqlite
```

### 基础用法（database/sql 标准接口）

两个库都兼容 Go 标准库的 `database/sql` 接口，代码几乎一样：

```go
package main

import (
    "database/sql"
    "fmt"
    "log"

    _ "github.com/mattn/go-sqlite3"  // CGo 方案
    // _ "modernc.org/sqlite"        // 纯 Go 方案（取消注释切换）
)

func main() {
    // 打开数据库
    db, err := sql.Open("sqlite3", "my_app.db")
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    // 推荐的 PRAGMA 配置
    db.Exec("PRAGMA journal_mode=WAL")
    db.Exec("PRAGMA synchronous=NORMAL")
    db.Exec("PRAGMA foreign_keys=ON")
    db.Exec("PRAGMA busy_timeout=5000")

    // 建表
    db.Exec(`
        CREATE TABLE IF NOT EXISTS users (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            email TEXT UNIQUE,
            age   INTEGER
        )
    `)

    // 插入（参数化查询）
    result, err := db.Exec(
        "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
        "张三", "zhangsan@test.com", 25,
    )
    if err != nil {
        log.Fatal(err)
    }
    id, _ := result.LastInsertId()
    fmt.Println("插入成功，ID:", id)

    // 查询单行
    var name string
    var age int
    err = db.QueryRow("SELECT name, age FROM users WHERE id = ?", 1).
        Scan(&name, &age)
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("姓名: %s, 年龄: %d\n", name, age)

    // 查询多行
    rows, err := db.Query("SELECT id, name, age FROM users")
    if err != nil {
        log.Fatal(err)
    }
    defer rows.Close()

    for rows.Next() {
        var id int
        var name string
        var age int
        rows.Scan(&id, &name, &age)
        fmt.Printf("  %d: %s (%d 岁)\n", id, name, age)
    }
}
```

### 事务操作

```go
tx, err := db.Begin()
if err != nil {
    log.Fatal(err)
}

stmt, _ := tx.Prepare("INSERT INTO users (name, email, age) VALUES (?, ?, ?)")
defer stmt.Close()

stmt.Exec("李四", "lisi@test.com", 30)
stmt.Exec("王五", "wangwu@test.com", 22)

// 提交事务
if err := tx.Commit(); err != nil {
    tx.Rollback()
    log.Fatal(err)
}
```

---

## 9.4 连接管理与安全注意事项

### SQL 注入 —— 最常见的安全漏洞

```
❌ 危险写法：拼接用户输入

  username = "admin'; DROP TABLE users; --"

  query = f"SELECT * FROM users WHERE name = '{username}'"
  → SELECT * FROM users WHERE name = 'admin'; DROP TABLE users; --'
  → 表被删了！

✅ 安全写法：参数化查询

  query = "SELECT * FROM users WHERE name = ?"
  cursor.execute(query, (username,))
  → SQLite 把 username 当作纯粹的字符串值处理
  → 无论输入什么，都不会被当作 SQL 语句执行
```

各语言的参数化查询语法：

| 语言 | 占位符 | 示例 |
|------|--------|------|
| Python | `?` | `cursor.execute('... WHERE id = ?', (1,))` |
| Node.js | `?` 或 `@name` | `stmt.get(1)` 或 `stmt.get({ name: '...' })` |
| Go | `?` | `db.Query('... WHERE id = ?', 1)` |
| Java | `?` | `ps.setInt(1, id)` |

### 连接管理最佳实践

```
┌─────────────────────────────────────────────────┐
│         SQLite 连接管理指南                       │
│                                                 │
│  1. 单线程应用：一个连接用到底                    │
│                                                 │
│  2. 多线程应用：                                 │
│     - 读操作：可以多个连接并行                    │
│     - 写操作：共用一个连接（或加锁串行写）        │
│     - 设置 WAL 模式减少冲突                      │
│                                                 │
│  3. Web 应用（多请求并发）：                      │
│     - 连接池大小：读连接 = CPU 核心数            │
│     - 写连接：只用 1 个                          │
│     - 始终启用 WAL + busy_timeout               │
│                                                 │
│  4. 用完一定要关闭连接！                          │
│     - Python: conn.close() 或 with 语句          │
│     - Node.js: db.close()                       │
│     - Go: defer db.Close()                      │
└─────────────────────────────────────────────────┘
```

### 错误处理模式

```python
# Python：完整的错误处理示例
import sqlite3

try:
    with sqlite3.connect('my_app.db') as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA foreign_keys=ON')

        conn.execute(
            'INSERT INTO users (name, email) VALUES (?, ?)',
            ('张三', 'zhangsan@test.com')
        )

except sqlite3.IntegrityError as e:
    print(f"约束冲突：{e}")  # UNIQUE 或 NOT NULL 等

except sqlite3.OperationalError as e:
    if "locked" in str(e):
        print("数据库被锁定，稍后重试")
    else:
        print(f"操作错误：{e}")

except sqlite3.DatabaseError as e:
    print(f"数据库错误：{e}")
```

### 数据库文件安全

```
┌─────────────────────────────────────────────────┐
│          数据库文件安全清单                        │
│                                                 │
│  ✅ 设置合适的文件权限（如 chmod 600）            │
│  ✅ 不要把 .db 文件放在 Web 可访问的目录          │
│  ✅ 定期备份（cp 或 .dump 命令）                  │
│  ✅ 在 .gitignore 中排除 .db 文件                │
│  ✅ 使用 PRAGMA integrity_check 定期检查         │
│  ❌ 不要通过网络文件系统（NFS）访问               │
│  ❌ 不要多个程序同时以写模式打开同一个文件         │
└─────────────────────────────────────────────────┘
```

---

## 9.5 ORM 集成

ORM（Object-Relational Mapping）让你用面向对象的方式操作数据库，不需要手写 SQL。主流 ORM 都对 SQLite 有很好的支持。

### Python —— SQLAlchemy

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, Session

# 连接 SQLite
engine = create_engine('sqlite:///my_app.db', echo=False)
Base = declarative_base()

# 定义模型
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    age = Column(Integer)

# 建表
Base.metadata.create_all(engine)

# CRUD 操作
with Session(engine) as session:
    # 插入
    user = User(name='张三', email='zhangsan@test.com', age=25)
    session.add(user)
    session.commit()

    # 查询
    users = session.query(User).filter(User.age > 20).all()
    for u in users:
        print(f'{u.name} - {u.email}')

    # 更新
    user.age = 26
    session.commit()

    # 删除
    session.delete(user)
    session.commit()
```

### Node.js —— Prisma

```javascript
// schema.prisma
// datasource db {
//   provider = "sqlite"
//   url      = "file:./my_app.db"
// }
//
// model User {
//   id    Int     @id @default(autoincrement())
//   name  String
//   email String  @unique
//   age   Int?
// }

// 使用 Prisma Client
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
    // 插入
    const user = await prisma.user.create({
        data: { name: '张三', email: 'zhangsan@test.com', age: 25 }
    });

    // 查询
    const users = await prisma.user.findMany({
        where: { age: { gt: 20 } }
    });

    // 更新
    await prisma.user.update({
        where: { id: 1 },
        data: { age: 26 }
    });

    // UPSERT
    await prisma.user.upsert({
        where: { email: 'zhangsan@test.com' },
        update: { age: 27 },
        create: { name: '张三', email: 'zhangsan@test.com', age: 27 }
    });
}

main();
```

### Go —— GORM

```go
package main

import (
    "fmt"
    "gorm.io/driver/sqlite"
    "gorm.io/gorm"
)

type User struct {
    ID    uint   `gorm:"primaryKey"`
    Name  string `gorm:"not null"`
    Email string `gorm:"unique"`
    Age   int
}

func main() {
    db, _ := gorm.Open(sqlite.Open("my_app.db"), &gorm.Config{})

    // 自动建表 / 迁移
    db.AutoMigrate(&User{})

    // 插入
    db.Create(&User{Name: "张三", Email: "zhangsan@test.com", Age: 25})

    // 查询
    var users []User
    db.Where("age > ?", 20).Find(&users)
    for _, u := range users {
        fmt.Printf("%s - %s\n", u.Name, u.Email)
    }

    // 更新
    db.Model(&User{}).Where("id = ?", 1).Update("age", 26)

    // 删除
    db.Delete(&User{}, 1)
}
```

### ORM vs 原生 SQL —— 怎么选？

| 维度 | ORM | 原生 SQL |
|------|-----|---------|
| 开发速度 | ⭐⭐⭐ 快（少写代码） | ⭐⭐ 需要手写 SQL |
| 学习成本 | 需要学 ORM API | 只需会 SQL |
| 性能 | 有一定开销 | 性能最优 |
| 复杂查询 | 复杂 JOIN / CTE 时 ORM 表达力有限 | 任何复杂度都能搞定 |
| 数据库迁移 | 内置迁移工具 | 需要手动管理 |
| 可读性 | 代码即文档 | SQL 可读性高 |

> **实际建议**：简单 CRUD 用 ORM 提升效率；复杂查询和性能敏感场景用原生 SQL。两者可以混用——ORM 通常提供执行原始 SQL 的接口。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Python | `sqlite3` 标准库内置；`?` 参数化；`with` 管理事务；`Row` 工厂 |
| Node.js | `better-sqlite3` 同步 API；`transaction()` 包裹批量操作；`sql.js` 纯 JS 方案 |
| Go | `mattn/go-sqlite3`（CGo）或 `modernc.org/sqlite`（纯 Go）；`database/sql` 标准接口 |
| SQL 注入 | **永远用参数化查询**，不拼接用户输入 |
| 连接管理 | 写连接用单个；读可并行；WAL + busy_timeout |
| ORM | SQLAlchemy / Prisma / GORM，简单 CRUD 用 ORM，复杂查询用原生 SQL |

> **下一章预告**：掌握 SQLite 的运维技巧——备份策略、数据库修复、VACUUM 瘦身、性能监控与调优。


