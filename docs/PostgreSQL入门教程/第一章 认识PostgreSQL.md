# 第一章 认识 PostgreSQL

---

## 1.1 PostgreSQL 是什么

PostgreSQL（发音：post-gres-Q-L）是一款**开源的关系型数据库管理系统**，诞生于 1986 年的加州大学伯克利分校，至今已有近 40 年历史。它是目前世界上功能最强大的开源数据库之一。

简单理解：**数据库就是一个帮你存数据、管数据、查数据的软件。** 你往里面存表格数据，然后用 SQL 语言告诉它"我要什么数据"，它就帮你找出来。

### 主流数据库对比

| 数据库 | 类型 | 一句话特点 |
|--------|------|-----------|
| **PostgreSQL** | 开源 | 功能最全面的开源数据库，标准兼容性最好 |
| MySQL | 开源 | 简单易上手，Web 开发中使用最广泛 |
| SQL Server | 商业 | 微软出品，与 .NET 生态深度集成 |
| Oracle | 商业 | 企业级标杆，功能最完整但价格昂贵 |
| SQLite | 开源 | 嵌入式数据库，无需服务器，适合小型应用 |

### PostgreSQL 的核心优势

- **标准兼容性强**：对 SQL 标准的支持是所有数据库中最好的
- **数据类型丰富**：原生支持 JSON、数组、UUID、地理空间等类型
- **可扩展性高**：可以自定义数据类型、函数、索引方法，甚至编程语言
- **稳定可靠**：ACID 完全兼容，数据一致性保障极强
- **完全免费**：没有任何商业限制，可自由使用于生产环境

> **什么时候选 PostgreSQL？**
> 如果你不确定选哪个数据库，选 PostgreSQL 基本不会错。它能覆盖从个人小项目到大型企业系统的几乎所有场景。

---

## 1.2 核心概念速览

在动手操作之前，先建立几个关键概念。不需要死记，后面实操时自然会理解。

### 数据的组织层次

PostgreSQL 中的数据按以下层级组织：

```
PostgreSQL 服务器（Server）
 └── 数据库（Database）        ← 一个服务器可以有多个数据库
      └── 模式（Schema）       ← 一个数据库可以有多个模式，默认是 public
           └── 表（Table）     ← 数据存储的核心单位
                ├── 列（Column）← 定义数据的"字段"，比如姓名、年龄
                └── 行（Row）   ← 每一条具体的数据记录
```

**用生活来类比：**

| 概念 | 类比 |
|------|------|
| 服务器 | 一整栋档案馆 |
| 数据库 | 档案馆里的一个房间 |
| 模式 | 房间里的一个柜子 |
| 表 | 柜子里的一份表格 |
| 列 | 表格的表头（姓名、年龄、成绩…） |
| 行 | 表格里的一行记录 |

### 客户端-服务端架构

PostgreSQL 采用典型的**客户端-服务端（C/S）架构**：

```
┌──────────────┐         网络连接          ┌──────────────────┐
│   客户端      │  ───── SQL 语句 ──────▶  │  PostgreSQL 服务端 │
│  (psql /     │  ◀──── 查询结果 ──────   │  （存储和处理数据） │
│   pgAdmin /  │                          │                  │
│   你的应用)   │                          │  默认端口：5432    │
└──────────────┘                          └──────────────────┘
```

- **服务端**：在后台持续运行，负责存储数据、执行 SQL、管理权限
- **客户端**：你用来发送 SQL 命令的工具，可以是命令行（psql）、图形界面（pgAdmin）、或你写的程序代码

### 什么是 SQL

SQL（Structured Query Language，结构化查询语言）是和数据库沟通的语言。它分为几大类：

| 类别 | 全称 | 做什么 | 典型语句 |
|------|------|--------|---------|
| **DDL** | Data Definition Language | 定义数据结构 | `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE` |
| **DML** | Data Manipulation Language | 操作数据 | `INSERT`, `UPDATE`, `DELETE`, `SELECT` |
| **DCL** | Data Control Language | 控制权限 | `GRANT`, `REVOKE` |
| **TCL** | Transaction Control Language | 管理事务 | `BEGIN`, `COMMIT`, `ROLLBACK` |

其中 `SELECT` 查询是日常使用频率最高的，本教程会在第四章重点讲解。

### 什么是事务

**事务（Transaction）** 是数据库操作的基本单位，简单理解就是"一组操作要么全部成功，要么全部失败"。

经典例子——银行转账：
1. 从 A 账户扣 100 元
2. 给 B 账户加 100 元

这两步必须同时成功或同时失败。如果第 1 步成功了、第 2 步失败了，钱就凭空消失了。事务就是解决这个问题的机制，第六章会详细介绍。

---

## 1.3 环境搭建

### 方式一：Docker 一键启动（推荐）

如果你已经安装了 Docker，这是最快的方式，一行命令搞定：

```bash
docker run --name my-postgres \
  -e POSTGRES_PASSWORD=123456 \
  -p 5432:5432 \
  -d postgres:16
```

参数说明：
- `--name my-postgres`：给容器取个名字
- `-e POSTGRES_PASSWORD=123456`：设置超级用户 postgres 的密码
- `-p 5432:5432`：把容器的 5432 端口映射到本机
- `-d postgres:16`：使用 PostgreSQL 16 版本镜像，后台运行

启动后连接：

```bash
docker exec -it my-postgres psql -U postgres
```

### 方式二：直接安装

**Windows：**
1. 访问 https://www.postgresql.org/download/windows/
2. 下载 EDB 安装包，一路 Next
3. 安装过程中会让你设置 postgres 用户的密码，记住它
4. 安装完成后，在开始菜单找到 **SQL Shell (psql)** 打开即可

**macOS：**
```bash
# 使用 Homebrew
brew install postgresql@16
brew services start postgresql@16
```

**Linux (Ubuntu/Debian)：**
```bash
sudo apt update
sudo apt install postgresql postgresql-client
sudo systemctl start postgresql
```

### 认识两个关键工具

#### psql — 命令行工具

`psql` 是 PostgreSQL 自带的命令行客户端，轻量高效，是日常操作的首选工具。

```bash
# 连接到数据库
psql -U postgres -h localhost -p 5432

# 连接成功后你会看到这样的提示符：
postgres=#
```

在 `postgres=#` 提示符下，你可以输入 SQL 语句，也可以使用 psql 专属的反斜杠命令：

```
postgres=# \l              -- 列出所有数据库
postgres=# \c mydb         -- 切换到 mydb 数据库
postgres=# \dt             -- 列出当前数据库的所有表
postgres=# \d students     -- 查看 students 表的结构
postgres=# \q              -- 退出 psql
```

> **注意**：SQL 语句需要以分号 `;` 结尾，反斜杠命令不需要。

#### pgAdmin — 图形界面工具

如果你更习惯图形化操作，pgAdmin 是官方推荐的 GUI 工具：
- Windows 安装 PostgreSQL 时通常会自带
- 也可以单独从 https://www.pgadmin.org/ 下载
- 提供可视化的表结构管理、SQL 编辑器、查询结果展示

**对于本教程，建议以 psql 为主**，因为命令行操作更能帮你理解 SQL 本身。

---

## 1.4 第一次动手：验证环境

安装完成后，跟着下面的步骤验证一切正常。

### 第一步：连接到 PostgreSQL

```bash
psql -U postgres
```

输入密码后，看到 `postgres=#` 提示符就说明连接成功了。

### 第二步：查看版本

```sql
SELECT version();
```

输出类似：

```
                          version
------------------------------------------------------------
 PostgreSQL 16.x on x86_64-pc-linux-gnu, compiled by gcc...
```

### 第三步：创建一个测试数据库

```sql
CREATE DATABASE tutorial;
```

### 第四步：切换到测试数据库

```
\c tutorial
```

看到提示 `You are now connected to database "tutorial"` 就成功了。

### 第五步：创建第一张表并插入数据

```sql
CREATE TABLE hello (
    id    SERIAL PRIMARY KEY,
    message TEXT
);

INSERT INTO hello (message) VALUES ('你好，PostgreSQL！');

SELECT * FROM hello;
```

如果看到以下输出，恭喜你，环境搭建成功！

```
 id |      message
----+-------------------
  1 | 你好，PostgreSQL！
(1 row)
```

### 第六步：清理（可选）

```sql
DROP TABLE hello;      -- 删除表
\c postgres            -- 切回默认数据库
DROP DATABASE tutorial; -- 删除测试数据库
```

---

## 本章小结

| 你应该知道的 | 内容 |
|-------------|------|
| PostgreSQL 是什么 | 开源关系型数据库，功能全面，免费可商用 |
| 数据组织层次 | 服务器 → 数据库 → 模式 → 表 → 行/列 |
| 架构模型 | 客户端-服务端，默认端口 5432 |
| SQL 四大类 | DDL（定义结构）、DML（操作数据）、DCL（权限控制）、TCL（事务管理） |
| 关键工具 | psql（命令行）、pgAdmin（图形界面） |
| 下一步 | 第二章将学习如何创建数据库和表，以及各种数据类型 |

---

*下一章：[第二章 数据库与表的基本操作（DDL）]()*
