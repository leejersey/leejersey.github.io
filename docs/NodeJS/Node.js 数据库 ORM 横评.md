# Node.js 数据库 ORM 横评

> Prisma vs Drizzle vs TypeORM vs Kysely——从类型安全、性能、DX 到生产实战，帮你选出最适合的 ORM。

---

## 1. 为什么需要 ORM：原始 SQL 的痛点

### 1.1 原始 SQL 的三大痛点

```typescript
import pg from 'pg';
const pool = new pg.Pool();

// ❌ 痛点 1：SQL 注入风险
const name = "'; DROP TABLE users; --";
const result = await pool.query(`SELECT * FROM users WHERE name = '${name}'`); // 💥

// ✅ 参数化查询可以防注入，但...
const result2 = await pool.query('SELECT * FROM users WHERE name = $1', [name]);

// ❌ 痛点 2：返回值没有类型
const rows = result2.rows;  // any[] ← 你不知道有哪些字段

// ❌ 痛点 3：表结构变了，SQL 不会报错
// 把 email 字段删了，但 SQL 里还在查 email
// → 运行时才炸，TypeScript 帮不了你
```

```
原始 SQL 的问题总结：

  1. 类型不安全    → 返回 any[]，字段改了编译不报错
  2. SQL 字符串拼接 → 容易注入、IDE 无提示
  3. 迁移靠手动     → DDL 脚本管理混乱
  4. 关联查询繁琐   → 多表 JOIN 手写 + 手动映射对象
```

### 1.2 ORM 的四种风格

```
四种 ORM 风格：

  ┌─────────────────┬──────────────┬─────────────────┐
  │ 风格            │ 代表          │ 特点             │
  ├─────────────────┼──────────────┼─────────────────┤
  │ Active Record   │ TypeORM      │ 模型自带增删改查  │
  │ Data Mapper     │ TypeORM      │ 模型与数据库解耦  │
  │ Schema-first    │ Prisma       │ DSL 定义，生成代码│
  │ Query Builder   │ Kysely/Drizzle│ 接近 SQL，类型安全│
  └─────────────────┴──────────────┴─────────────────┘

  抽象程度：高 ←──────────────────────→ 低
            Active Record → Data Mapper → Schema-first → Query Builder
            
  SQL 控制力：低 ←──────────────────────→ 高
```

### 1.3 四大选手登场

| | Prisma | Drizzle | TypeORM | Kysely |
|---|---|---|---|---|
| **首发** | 2019 | 2022 | 2016 | 2021 |
| **风格** | Schema-first | Query Builder | Active Record / Data Mapper | Query Builder |
| **Schema 定义** | `.prisma` DSL | TypeScript | 装饰器 / Entity | TypeScript 接口 |
| **类型安全** | ✅ 生成类型 | ✅ 推断类型 | ⚠️ 部分 | ✅ 推断类型 |
| **运行时依赖** | Rust 引擎 | 零依赖 | 较重 | 零依赖 |
| **npm 周下载** | ~380 万 | ~120 万 | ~200 万 | ~50 万 |
| **定位** | 全功能 ORM | 轻量 SQL 工具 | 企业级 ORM | 纯类型安全查询 |

---

## 2. Prisma：Schema-first 的代表

### 2.1 Schema 定义与代码生成

```bash
npm install prisma @prisma/client
npx prisma init
```

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  posts     Post[]
  createdAt DateTime @default(now())
}

model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  published Boolean  @default(false)
  author    User     @relation(fields: [authorId], references: [id])
  authorId  Int
  tags      Tag[]
}

model Tag {
  id    Int    @id @default(autoincrement())
  name  String @unique
  posts Post[]
}
```

```bash
# 生成 Prisma Client（类型安全的 CRUD API）
npx prisma generate
# → node_modules/.prisma/client/  ← 生成的类型 + 运行时

# 同步数据库
npx prisma db push       # 开发：直接同步（不生成迁移文件）
npx prisma migrate dev   # 正式：生成迁移 SQL
```

```
Prisma 的工作流：

  schema.prisma → prisma generate → PrismaClient（类型安全）
       ↓
  prisma migrate → SQL 迁移文件 → 数据库
```

### 2.2 CRUD 与关联查询

```typescript
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

// 创建
const user = await prisma.user.create({
  data: {
    email: 'alice@example.com',
    name: 'Alice',
    posts: {
      create: [
        { title: '第一篇', content: 'Hello World' },
        { title: '第二篇', content: 'Prisma 真好用' },
      ],
    },
  },
  include: { posts: true },  // 返回关联数据
});
// user.posts ← 类型安全，IDE 有完整提示

// 查询（含嵌套过滤）
const posts = await prisma.post.findMany({
  where: {
    author: { email: { contains: '@example.com' } },
    published: true,
  },
  include: { author: true, tags: true },
  orderBy: { createdAt: 'desc' },
  take: 10,
});

// 更新
await prisma.user.update({
  where: { email: 'alice@example.com' },
  data: { name: 'Alice Updated' },
});

// 删除
await prisma.post.deleteMany({
  where: { published: false },
});
```

### 2.3 Prisma Migrate 迁移管理

```bash
# 创建迁移
npx prisma migrate dev --name add_avatar_field
# → prisma/migrations/20260510_add_avatar_field/migration.sql

# 生产环境应用迁移
npx prisma migrate deploy

# 查看迁移状态
npx prisma migrate status
```

### 2.4 优缺点分析

| ✅ 优点 | ❌ 缺点 |
|---|---|
| Schema DSL 简洁直观 | 必须学新的 DSL 语言 |
| 生成的 API 类型极其精确 | Rust 引擎启动有冷启动开销 |
| Prisma Studio GUI 管理工具 | 复杂查询（子查询/Window）受限 |
| 迁移管理完善 | 包体积大（~15MB Rust 二进制） |
| 文档和社区最成熟 | 不能直接写 SQL（需用 `$queryRaw`） |

> 💡 **适合**：全栈项目、Next.js/Remix 应用、团队协作（Schema 即文档）。

---

## 3. Drizzle：SQL-like 的类型安全

### 3.1 TypeScript Schema 定义

```bash
npm install drizzle-orm pg
npm install -D drizzle-kit @types/pg
```

```typescript
// src/db/schema.ts
import { pgTable, serial, text, boolean, integer, timestamp } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: timestamp('created_at').defaultNow(),
});

export const posts = pgTable('posts', {
  id: serial('id').primaryKey(),
  title: text('title').notNull(),
  content: text('content'),
  published: boolean('published').default(false),
  authorId: integer('author_id').references(() => users.id),
});

export const tags = pgTable('tags', {
  id: serial('id').primaryKey(),
  name: text('name').notNull().unique(),
});

// 关系定义
export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one, many }) => ({
  author: one(users, { fields: [posts.authorId], references: [users.id] }),
  tags: many(tags),
}));
```

> 💡 **关键区别**：Schema 就是 TypeScript，不需要学新 DSL，不需要代码生成。

### 3.2 SQL-like 查询 API

```typescript
import { drizzle } from 'drizzle-orm/node-postgres';
import { eq, and, like, desc } from 'drizzle-orm';
import * as schema from './schema';
import pg from 'pg';

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
const db = drizzle(pool, { schema });

// 创建
const [user] = await db.insert(schema.users).values({
  email: 'alice@example.com',
  name: 'Alice',
}).returning();

await db.insert(schema.posts).values([
  { title: '第一篇', content: 'Hello', authorId: user.id },
  { title: '第二篇', content: 'Drizzle', authorId: user.id },
]);

// 查询（SQL 风格——像写 SELECT ... WHERE ... ORDER BY）
const posts = await db
  .select()
  .from(schema.posts)
  .where(and(
    eq(schema.posts.published, true),
    like(schema.posts.title, '%Drizzle%'),
  ))
  .orderBy(desc(schema.posts.createdAt))
  .limit(10);

// 关联查询（Relational API）
const usersWithPosts = await db.query.users.findMany({
  with: { posts: true },
  where: eq(schema.users.email, 'alice@example.com'),
});

// 更新
await db.update(schema.users)
  .set({ name: 'Alice Updated' })
  .where(eq(schema.users.email, 'alice@example.com'));

// 删除
await db.delete(schema.posts)
  .where(eq(schema.posts.published, false));

// 复杂 JOIN
const result = await db
  .select({
    userName: schema.users.name,
    postTitle: schema.posts.title,
  })
  .from(schema.users)
  .innerJoin(schema.posts, eq(schema.users.id, schema.posts.authorId))
  .where(eq(schema.posts.published, true));
```

### 3.3 drizzle-kit 迁移与 push

```typescript
// drizzle.config.ts
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  schema: './src/db/schema.ts',
  out: './drizzle',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
```

```bash
# 开发：直接推到数据库（不生成迁移文件）
npx drizzle-kit push

# 正式：生成迁移 SQL
npx drizzle-kit generate
npx drizzle-kit migrate

# 可视化管理
npx drizzle-kit studio  # 浏览器 GUI
```

### 3.4 优缺点分析

| ✅ 优点 | ❌ 缺点 |
|---|---|
| Schema 就是 TypeScript | 社区和文档比 Prisma 年轻 |
| 零运行时依赖（极轻量） | 关系 API 不如 Prisma 直观 |
| SQL-like API 学习成本低 | 类型推断偶有复杂泛型问题 |
| 无代码生成，编辑器即时反馈 | 生态插件少于 Prisma |
| 支持所有 SQL 特性（子查询等） | Monorepo 配置稍复杂 |

> 💡 **适合**：喜欢 SQL 的开发者、追求极致性能和轻量、Serverless/Edge 环境。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Prisma | Schema DSL → 生成代码 → 类型精确，但 Rust 引擎重 |
| Drizzle | TypeScript Schema → SQL-like API → 零依赖轻量 |
| 风格差异 | Prisma 像"黑盒 ORM"，Drizzle 像"类型安全的 SQL" |
| 迁移 | Prisma `migrate dev` / Drizzle `drizzle-kit generate` |

> **下一章**：TypeORM 传统派与 Kysely 纯 Query Builder。

---

## 4. TypeORM：传统 Active Record / Data Mapper

### 4.1 装饰器定义 Entity

```bash
npm install typeorm reflect-metadata pg
```

```typescript
// src/entity/User.ts
import { Entity, PrimaryGeneratedColumn, Column, OneToMany, CreateDateColumn } from 'typeorm';
import { Post } from './Post';

@Entity()
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  email: string;

  @Column({ nullable: true })
  name: string;

  @OneToMany(() => Post, (post) => post.author)
  posts: Post[];

  @CreateDateColumn()
  createdAt: Date;
}
```

```typescript
// src/entity/Post.ts
import { Entity, PrimaryGeneratedColumn, Column, ManyToOne, ManyToMany, JoinTable } from 'typeorm';
import { User } from './User';
import { Tag } from './Tag';

@Entity()
export class Post {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  title: string;

  @Column({ nullable: true })
  content: string;

  @Column({ default: false })
  published: boolean;

  @ManyToOne(() => User, (user) => user.posts)
  author: User;

  @ManyToMany(() => Tag)
  @JoinTable()
  tags: Tag[];
}
```

```typescript
// 数据源配置
import { DataSource } from 'typeorm';

export const AppDataSource = new DataSource({
  type: 'postgres',
  url: process.env.DATABASE_URL,
  entities: [User, Post, Tag],
  synchronize: true,  // 开发用，生产禁用
  logging: true,
});

await AppDataSource.initialize();
```

### 4.2 Repository 与 QueryBuilder

```typescript
const userRepo = AppDataSource.getRepository(User);
const postRepo = AppDataSource.getRepository(Post);

// 创建
const user = userRepo.create({
  email: 'alice@example.com',
  name: 'Alice',
});
await userRepo.save(user);

const post = postRepo.create({
  title: '第一篇',
  content: 'Hello',
  author: user,
});
await postRepo.save(post);

// 查询
const users = await userRepo.find({
  where: { email: 'alice@example.com' },
  relations: { posts: true },
});

// QueryBuilder（复杂查询）
const posts = await postRepo
  .createQueryBuilder('post')
  .leftJoinAndSelect('post.author', 'author')
  .leftJoinAndSelect('post.tags', 'tag')
  .where('post.published = :published', { published: true })
  .andWhere('author.email LIKE :email', { email: '%@example.com' })
  .orderBy('post.createdAt', 'DESC')
  .take(10)
  .getMany();

// 更新
await userRepo.update(
  { email: 'alice@example.com' },
  { name: 'Alice Updated' },
);

// 删除
await postRepo.delete({ published: false });
```

### 4.3 迁移管理

```bash
# 生成迁移
npx typeorm migration:generate src/migrations/AddAvatar -d src/data-source.ts

# 运行迁移
npx typeorm migration:run -d src/data-source.ts

# 回滚
npx typeorm migration:revert -d src/data-source.ts
```

### 4.4 优缺点分析

| ✅ 优点 | ❌ 缺点 |
|---|---|
| 装饰器语法符合 Java/C# 开发者习惯 | 类型安全较弱（很多 `any`） |
| 同时支持 Active Record 和 Data Mapper | 装饰器依赖 `reflect-metadata` |
| QueryBuilder 灵活强大 | 包体积大、依赖多 |
| NestJS 官方集成 | 维护速度慢，Issue 积压多 |
| 支持多种数据库 | 文档和错误信息不够清晰 |

> 💡 **适合**：NestJS 项目（官方集成）、有 Java/Spring 背景的团队、已有项目不想迁移。

---

## 5. Kysely：纯 Query Builder

### 5.1 类型定义与 Query Builder

```bash
npm install kysely pg
```

Kysely 不管 Schema 定义——你只需提供 TypeScript 接口：

```typescript
// src/db/types.ts
import { Generated, Insertable, Selectable, Updateable } from 'kysely';

export interface Database {
  users: UsersTable;
  posts: PostsTable;
  tags: TagsTable;
}

interface UsersTable {
  id: Generated<number>;
  email: string;
  name: string | null;
  created_at: Generated<Date>;
}

interface PostsTable {
  id: Generated<number>;
  title: string;
  content: string | null;
  published: Generated<boolean>;
  author_id: number;
}

interface TagsTable {
  id: Generated<number>;
  name: string;
}

// 导出工具类型
export type User = Selectable<UsersTable>;
export type NewUser = Insertable<UsersTable>;
export type UserUpdate = Updateable<UsersTable>;
```

```typescript
// src/db/index.ts
import { Kysely, PostgresDialect } from 'kysely';
import pg from 'pg';
import type { Database } from './types';

export const db = new Kysely<Database>({
  dialect: new PostgresDialect({
    pool: new pg.Pool({ connectionString: process.env.DATABASE_URL }),
  }),
});
```

```typescript
// CRUD（每一步都有完整类型提示）
// 创建
const user = await db
  .insertInto('users')
  .values({ email: 'alice@example.com', name: 'Alice' })
  .returningAll()
  .executeTakeFirstOrThrow();

await db
  .insertInto('posts')
  .values([
    { title: '第一篇', content: 'Hello', author_id: user.id },
    { title: '第二篇', content: 'Kysely', author_id: user.id },
  ])
  .execute();

// 查询
const posts = await db
  .selectFrom('posts')
  .selectAll()
  .where('published', '=', true)
  .where('title', 'like', '%Kysely%')
  .orderBy('created_at', 'desc')
  .limit(10)
  .execute();
// posts 类型自动推断为 Post[]

// 更新
await db
  .updateTable('users')
  .set({ name: 'Alice Updated' })
  .where('email', '=', 'alice@example.com')
  .execute();

// 删除
await db
  .deleteFrom('posts')
  .where('published', '=', false)
  .execute();
```

### 5.2 复杂查询与事务

```typescript
// JOIN 查询
const result = await db
  .selectFrom('users')
  .innerJoin('posts', 'users.id', 'posts.author_id')
  .select(['users.name as userName', 'posts.title as postTitle'])
  .where('posts.published', '=', true)
  .execute();

// 子查询
const activeUsers = await db
  .selectFrom('users')
  .selectAll()
  .where('id', 'in',
    db.selectFrom('posts')
      .select('author_id')
      .where('published', '=', true)
  )
  .execute();

// 事务
await db.transaction().execute(async (trx) => {
  const user = await trx
    .insertInto('users')
    .values({ email: 'bob@example.com', name: 'Bob' })
    .returningAll()
    .executeTakeFirstOrThrow();

  await trx
    .insertInto('posts')
    .values({ title: 'Bob 的文章', author_id: user.id })
    .execute();
});
```

### 5.3 优缺点分析

| ✅ 优点 | ❌ 缺点 |
|---|---|
| 100% 类型安全，零 `any` | 没有关联查询抽象（手写 JOIN） |
| 零运行时依赖 | 没有内置迁移工具 |
| 完全控制 SQL（子查询/Window/CTE） | 没有 Schema 定义（需手写接口） |
| 极致轻量（~10KB） | 学习曲线：需要熟悉 SQL |
| 适合已有数据库（introspect） | 生态较小 |

> 💡 **适合**：已有数据库反向接入、DBA 团队、需要极致 SQL 控制、不想要 ORM 抽象的项目。

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| TypeORM | 装饰器定义、Repository + QueryBuilder、NestJS 官方集成 |
| Kysely | 纯 TS 接口定义、类型安全 SQL Builder、零抽象零依赖 |
| 风格差异 | TypeORM 像 Java ORM，Kysely 像"带类型的 SQL" |

> **下一章**：六大维度横向对比——类型安全 / 性能 / DX / 迁移 / 生态 / 综合评分。

---

## 6. 横向对比：六大维度评测

### 6.1 类型安全

| | Prisma | Drizzle | TypeORM | Kysely |
|---|---|---|---|---|
| **Schema→类型** | 生成（精确） | 推断（精确） | 装饰器（部分） | 手写接口（精确） |
| **查询结果类型** | ✅ 精确到 include 字段 | ✅ 精确 | ⚠️ 关联字段可能 `undefined` | ✅ 精确 |
| **错误字段编译报错** | ✅ | ✅ | ❌ 很多 `any` | ✅ |
| **评分** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 6.2 查询性能

```
性能对比（简化基准，1000 次单行查询，PostgreSQL）：

  原始 pg 驱动:  ~1.0x（基准）
  Kysely:        ~1.05x（几乎无开销）
  Drizzle:       ~1.1x
  TypeORM:       ~1.5x
  Prisma:        ~1.8x（Rust 引擎序列化开销）

  Prisma 的开销来自：
  1. JS → Rust 引擎 → 数据库（多一层）
  2. 查询结果从 Rust 序列化回 JS
  3. 冷启动时加载 Rust 二进制（~200ms）
```

| | Prisma | Drizzle | TypeORM | Kysely |
|---|---|---|---|---|
| **运行时开销** | 高（Rust 中间层） | 极低 | 中 | 极低 |
| **冷启动** | 慢（~200ms） | 快 | 中 | 快 |
| **包大小** | ~15MB | ~100KB | ~2MB | ~10KB |
| **评分** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 6.3 开发体验（DX）

| | Prisma | Drizzle | TypeORM | Kysely |
|---|---|---|---|---|
| **上手难度** | 低（DSL 直观） | 中（需懂 SQL） | 低（像 Java ORM） | 中高（纯 SQL 思维） |
| **IDE 提示** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **代码生成** | 需要 | 不需要 | 不需要 | 不需要 |
| **GUI 工具** | Prisma Studio | Drizzle Studio | 无 | 无 |
| **评分** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

### 6.4 迁移管理

| | Prisma | Drizzle | TypeORM | Kysely |
|---|---|---|---|---|
| **方式** | prisma migrate | drizzle-kit | typeorm migration | 无内置 |
| **自动生成 SQL** | ✅ | ✅ | ✅ | ❌ |
| **可视化 diff** | ✅ | ✅ | ❌ | ❌ |
| **回滚** | ❌（需手动） | ❌ | ✅ | ❌ |
| **评分** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

### 6.5 生态与框架集成

| | Prisma | Drizzle | TypeORM | Kysely |
|---|---|---|---|---|
| **Next.js** | ✅ 官方推荐 | ✅ 热门 | ⚠️ 可用 | ⚠️ 可用 |
| **NestJS** | ✅ 有适配器 | ⚠️ 社区 | ✅ 官方集成 | ⚠️ 社区 |
| **Hono/Fastify** | ✅ | ✅ | ✅ | ✅ |
| **Edge/Serverless** | ⚠️ 需 Data Proxy | ✅ 原生支持 | ❌ 太重 | ✅ 原生支持 |
| **评分** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

### 6.6 综合评分与选型指南

| 维度 | Prisma | Drizzle | TypeORM | Kysely |
|---|---|---|---|---|
| 类型安全 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 性能 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| DX | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 迁移 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 生态 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **总分** | **22/25** | **22/25** | **16/25** | **19/25** |

---

## 7. 实战对比：同一需求四种实现

### 7.1 数据模型设计

业务需求：用户发表文章，文章有标签，实现分页查询。

```
users (1) ──→ (N) posts (M) ←──→ (N) tags

查询需求：
  1. 创建用户 + 文章（事务）
  2. 分页查询已发布文章（含作者信息）
  3. 按标签筛选文章
```

### 7.2 CRUD 实现对比

**创建用户 + 文章（事务）**：

```typescript
// ── Prisma ──
const user = await prisma.user.create({
  data: {
    email: 'alice@example.com',
    name: 'Alice',
    posts: { create: { title: '文章1', published: true } },
  },
  include: { posts: true },
});

// ── Drizzle ──
const user = await db.transaction(async (tx) => {
  const [u] = await tx.insert(users).values({
    email: 'alice@example.com', name: 'Alice',
  }).returning();
  await tx.insert(posts).values({
    title: '文章1', published: true, authorId: u.id,
  });
  return u;
});

// ── TypeORM ──
await AppDataSource.transaction(async (manager) => {
  const user = manager.create(User, {
    email: 'alice@example.com', name: 'Alice',
  });
  await manager.save(user);
  const post = manager.create(Post, {
    title: '文章1', published: true, author: user,
  });
  await manager.save(post);
});

// ── Kysely ──
await db.transaction().execute(async (trx) => {
  const user = await trx.insertInto('users')
    .values({ email: 'alice@example.com', name: 'Alice' })
    .returningAll().executeTakeFirstOrThrow();
  await trx.insertInto('posts')
    .values({ title: '文章1', published: true, author_id: user.id })
    .execute();
});
```

**分页查询已发布文章**：

```typescript
// ── Prisma ──
const posts = await prisma.post.findMany({
  where: { published: true },
  include: { author: { select: { name: true, email: true } } },
  orderBy: { createdAt: 'desc' },
  skip: (page - 1) * pageSize,
  take: pageSize,
});

// ── Drizzle ──
const result = await db
  .select({
    id: schema.posts.id,
    title: schema.posts.title,
    authorName: schema.users.name,
    authorEmail: schema.users.email,
  })
  .from(schema.posts)
  .innerJoin(schema.users, eq(schema.users.id, schema.posts.authorId))
  .where(eq(schema.posts.published, true))
  .orderBy(desc(schema.posts.createdAt))
  .offset((page - 1) * pageSize)
  .limit(pageSize);

// ── TypeORM ──
const posts = await postRepo.createQueryBuilder('post')
  .leftJoinAndSelect('post.author', 'author')
  .where('post.published = :published', { published: true })
  .orderBy('post.createdAt', 'DESC')
  .skip((page - 1) * pageSize)
  .take(pageSize)
  .getMany();

// ── Kysely ──
const posts = await db
  .selectFrom('posts')
  .innerJoin('users', 'users.id', 'posts.author_id')
  .select(['posts.id', 'posts.title', 'users.name as authorName'])
  .where('posts.published', '=', true)
  .orderBy('posts.created_at', 'desc')
  .offset((page - 1) * pageSize)
  .limit(pageSize)
  .execute();
```

### 7.3 复杂查询与事务对比

**按标签筛选 + 统计**：

```typescript
// ── Prisma ──
const tagStats = await prisma.tag.findMany({
  select: {
    name: true,
    _count: { select: { posts: true } },
  },
  orderBy: { posts: { _count: 'desc' } },
});

// ── Drizzle ──（SQL 更灵活）
const tagStats = await db
  .select({
    tagName: schema.tags.name,
    postCount: sql<number>`count(*)`.as('post_count'),
  })
  .from(schema.tags)
  .innerJoin(postsToTags, eq(schema.tags.id, postsToTags.tagId))
  .groupBy(schema.tags.name)
  .orderBy(sql`count(*) desc`);

// ── TypeORM ──
const tagStats = await tagRepo.createQueryBuilder('tag')
  .loadRelationCountAndMap('tag.postCount', 'tag.posts')
  .orderBy('tag.postCount', 'DESC')
  .getMany();

// ── Kysely ──（最接近原始 SQL）
const tagStats = await db
  .selectFrom('tags')
  .innerJoin('posts_tags', 'tags.id', 'posts_tags.tag_id')
  .select(['tags.name', db.fn.count('posts_tags.post_id').as('post_count')])
  .groupBy('tags.name')
  .orderBy('post_count', 'desc')
  .execute();
```

### 7.4 选型决策树

```
你的项目是什么场景？

  ┌─ 全栈应用（Next.js/Remix）
  │   └─ 团队不熟 SQL？ → Prisma ✅
  │   └─ 追求性能/轻量？ → Drizzle ✅
  │
  ├─ NestJS 企业项目
  │   └─ 团队有 Java 背景？ → TypeORM ✅
  │   └─ 新项目追求类型安全？ → Prisma 或 Drizzle ✅
  │
  ├─ Serverless / Edge
  │   └─ → Drizzle ✅ 或 Kysely ✅（零依赖轻量）
  │
  ├─ 已有数据库，需要接入
  │   └─ → Kysely ✅（introspect + 纯 Query Builder）
  │
  └─ 需要极致 SQL 控制
      └─ → Kysely ✅ 或 Drizzle ✅
```

**一句话选型**：

| 场景 | 推荐 |
|---|---|
| **"我不想写 SQL"** | Prisma |
| **"我喜欢 SQL 但要类型安全"** | Drizzle |
| **"我用 NestJS"** | TypeORM（或 Prisma） |
| **"我要最轻最快"** | Kysely |
| **"2024+ 新项目"** | Drizzle 或 Prisma |

---

## 全书总结

```
┌─────────────────────────────────────────────────────────────┐
│        Node.js 数据库 ORM 横评 · 知识地图                     │
│                                                              │
│  Ch.1  为什么要 ORM   原始 SQL 痛点 / 四种风格               │
│  Ch.2  Prisma        Schema DSL / 代码生成 / Migrate         │
│  Ch.3  Drizzle       TS Schema / SQL-like API / 零依赖       │
│  Ch.4  TypeORM       装饰器 / Repository / QueryBuilder      │
│  Ch.5  Kysely        纯 Query Builder / 类型推断 / 极致轻量  │
│  Ch.6  六维横评       类型安全·性能·DX·迁移·生态·综合评分     │
│  Ch.7  实战对比       同一需求四种实现 / 选型决策树            │
│                                                              │
│  7 章 24 节，四大 ORM 全面对比，找到最适合你的。              │
└─────────────────────────────────────────────────────────────┘
```

> 🎉 **核心结论**：Prisma DX 最好但偏重，Drizzle 轻量且类型安全，TypeORM 适合 NestJS，Kysely 是 SQL 极客首选。
