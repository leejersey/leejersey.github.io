# NestJS 企业级应用架构

> Angular 的设计哲学 + Node.js 的运行时能力——NestJS 用 IoC 容器、装饰器和模块系统，让 Node.js 后端开发从"野路子"进入"工程化"。本教程从底层原理到生产实战，带你构建真正可维护的企业级应用。

---

## 1. NestJS 全景：为什么企业选它

Node.js 后端框架经历了从"自由放养"到"工程化约束"的进化——NestJS 就站在这条进化链的最顶端。

### 1.1 从 Express 到 NestJS：Node.js 后端的进化之路

```
Node.js 后端框架进化时间线：

  2010 ── Express ─────── 极简、灵活、无约束
           │               "给你一把刀，怎么切随你"
           │
  2013 ── Koa ──────────── 更现代的中间件（async/await）
           │               但依然没有架构约束
           │
  2016 ── Hapi / Adonis ── 开始引入约定和结构
           │
  2017 ── NestJS ─────── Angular 设计哲学 + Node.js 运行时
           │               IoC 容器 + 装饰器 + 模块系统
           │               "给你一整套建筑规范"
           │
  2023+ ─ Fastify 生态 ── 性能极致，但 NestJS 可选用它做底层
```

Express 的问题不在于它不够好，而在于它**太自由**：

```typescript
// Express 项目的典型困境

// 项目 A 的路由写法
app.get('/users', (req, res) => { /* ... */ });

// 项目 B 的路由写法
router.route('/users').get(controller.getUsers);

// 项目 C 的路由写法
app.use('/api/v1', require('./routes/users'));

// 三个项目、三种风格 → 新人每次换项目都要重新学"架构"
// 没有统一的：
// ❌ 依赖注入机制 → 手动 require，测试困难
// ❌ 模块化标准 → 文件怎么组织全靠个人习惯
// ❌ 中间件分层 → 认证/验证/转换混在一起
// ❌ 错误处理规范 → 每个人的 try-catch 风格不同
```

NestJS 的解法——**用框架级约束消灭架构分歧**：

```typescript
// NestJS 项目：无论谁写的，结构都一样

// Controller → 负责路由和请求/响应
@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}  // 依赖注入

  @Get()
  findAll() {
    return this.userService.findAll();  // 业务逻辑在 Service 中
  }
}

// Service → 负责业务逻辑
@Injectable()
export class UserService {
  constructor(
    @InjectRepository(User) private userRepo: Repository<User>,  // 数据层注入
  ) {}

  findAll() {
    return this.userRepo.find();
  }
}

// Module → 声明依赖关系
@Module({
  controllers: [UserController],
  providers: [UserService],
})
export class UserModule {}

// 任何 NestJS 项目都是这个结构 → 零学习成本切换项目
```

| 维度 | Express | Koa | Fastify | NestJS |
|:---|:---|:---|:---|:---|
| **架构约束** | ❌ 无 | ❌ 无 | ❌ 无 | ✅ 强约束 |
| **依赖注入** | ❌ 手动 | ❌ 手动 | ❌ 手动 | ✅ IoC 容器 |
| **TypeScript** | ⚠️ 可选 | ⚠️ 可选 | ⚠️ 可选 | ✅ 原生 |
| **模块系统** | ❌ 无 | ❌ 无 | ✅ 插件 | ✅ @Module |
| **微服务** | ❌ 自建 | ❌ 自建 | ❌ 自建 | ✅ 内置 |
| **测试友好** | ⚠️ 一般 | ⚠️ 一般 | ⚠️ 一般 | ✅ 极好 |
| **学习曲线** | 低 | 低 | 中 | 高 |
| **适合场景** | 小项目/原型 | 小项目 | 高性能API | 企业级应用 |

> 💡 **NestJS 不是 Express 的替代品**——它默认基于 Express 运行（也可切换为 Fastify）。NestJS 是在 Express 之上加了一层"建筑规范"：IoC 容器、装饰器路由、模块封装、请求管道。

### 1.2 设计哲学：约定优于配置 + 依赖注入

NestJS 的设计哲学可以用三个关键词概括：

```
NestJS 三大设计支柱：

  ┌─────────────────────────────────────────────────────┐
  │                 NestJS 设计哲学                       │
  ├─────────────┬─────────────────┬─────────────────────┤
  │  约定优于配置  │    依赖注入      │   装饰器驱动开发    │
  │             │                 │                     │
  │ Controller  │  IoC 容器自动    │  @Controller()      │
  │ Service     │  管理对象的       │  @Injectable()      │
  │ Module      │  创建、注入、     │  @Module()          │
  │ 三层分离     │  销毁生命周期     │  @Get() @Post()     │
  └─────────────┴─────────────────┴─────────────────────┘
                    ↓
         来自 Angular 的"后端移植"
         + Spring Boot / ASP.NET 的企业级经验
```

**约定优于配置**——你不需要决定"代码放哪里"：

```typescript
// NestJS 约定：每个功能模块的标准结构
// src/user/
//   ├── user.module.ts       ← 模块声明
//   ├── user.controller.ts   ← 路由层（只处理 HTTP）
//   ├── user.service.ts      ← 业务逻辑（可测试的纯逻辑）
//   ├── user.entity.ts       ← 数据库实体
//   ├── dto/
//   │   ├── create-user.dto.ts  ← 创建请求的数据结构
//   │   └── update-user.dto.ts  ← 更新请求的数据结构
//   └── user.controller.spec.ts ← 单元测试

// CLI 一键生成标准结构：
// nest g resource user
// → 自动创建上述所有文件 + CRUD 模板代码
```

**依赖注入**——对象的创建不再是你的事：

```typescript
// ❌ 传统方式：手动创建依赖（紧耦合）
class UserController {
  private service = new UserService(
    new UserRepository(
      new DatabaseConnection('postgres://...')  // 层层嵌套
    )
  );
}

// ✅ NestJS 方式：声明你需要什么，框架给你注入（松耦合）
@Controller('users')
class UserController {
  constructor(
    private readonly userService: UserService,  // 框架自动注入
  ) {}
}
// UserService 的创建、它依赖的 Repository、Database 连接
// → 全部由 IoC 容器自动管理
// → 测试时可以轻松替换为 Mock 实现
```

> 💡 **NestJS 的本质**：它不是一个"更好的 Express"——它是一个**依赖注入框架**，恰好用来写 HTTP 服务。理解这一点，你就理解了它为什么能同时支持 REST API、GraphQL、WebSocket、微服务。

### 1.3 技术栈全景：NestJS 生态一览

```
NestJS 官方生态（@nestjs/* 包）：

  ┌─ 核心 ──────────────────────────────────┐
  │  @nestjs/core          框架核心          │
  │  @nestjs/common        通用装饰器/工具    │
  │  @nestjs/cli           脚手架 CLI         │
  │  @nestjs/testing       测试工具           │
  ├─ HTTP 层 ───────────────────────────────┤
  │  @nestjs/platform-express  Express 适配器 │
  │  @nestjs/platform-fastify  Fastify 适配器 │
  ├─ 数据库 ────────────────────────────────┤
  │  @nestjs/typeorm        TypeORM 集成      │
  │  @nestjs/sequelize      Sequelize 集成    │
  │  @nestjs/mongoose       Mongoose 集成     │
  │  @nestjs/prisma         Prisma 集成       │ ← 社区维护
  ├─ 认证 & 安全 ──────────────────────────┤
  │  @nestjs/passport       Passport 认证     │
  │  @nestjs/jwt            JWT 工具          │
  │  @nestjs/throttler      限流保护          │
  ├─ 微服务 ────────────────────────────────┤
  │  @nestjs/microservices  微服务传输层       │
  │  支持：TCP / Redis / NATS / RabbitMQ     │
  │        Kafka / gRPC / MQTT               │
  ├─ GraphQL & WebSocket ──────────────────┤
  │  @nestjs/graphql        GraphQL 集成      │
  │  @nestjs/websockets     WebSocket 网关    │
  ├─ 工具 ──────────────────────────────────┤
  │  @nestjs/config         配置管理          │
  │  @nestjs/schedule       定时任务          │
  │  @nestjs/cache-manager  缓存管理          │
  │  @nestjs/bull           队列任务          │
  │  @nestjs/terminus       健康检查          │
  │  @nestjs/swagger        API 文档          │
  │  @nestjs/event-emitter  事件发射器        │
  │  @nestjs/cqrs           CQRS 模式        │
  └─────────────────────────────────────────┘
```

| 你需要的能力 | Express 需要 | NestJS 内置/官方包 |
|:---|:---|:---|
| 依赖注入 | 自己实现或用 inversify | ✅ @nestjs/core |
| 参数验证 | express-validator | ✅ class-validator + Pipe |
| API 文档 | swagger-jsdoc 手写注释 | ✅ @nestjs/swagger 自动生成 |
| 认证鉴权 | passport + 手动集成 | ✅ @nestjs/passport |
| 定时任务 | node-cron | ✅ @nestjs/schedule |
| 消息队列 | 自己封装 | ✅ @nestjs/bull |
| 微服务 | 从零搭建 | ✅ @nestjs/microservices |
| 健康检查 | 自己写 /health | ✅ @nestjs/terminus |

### 1.4 Hello World 背后发生了什么

一个最简单的 NestJS 应用：

```typescript
// main.ts — 应用入口
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);  // 一行代码，背后干了 8 件事
  await app.listen(3000);
}
bootstrap();
```

```
NestFactory.create(AppModule) 背后的 8 个步骤：

  1. 创建 IoC 容器（DI Container）
     → 初始化一个空的 Provider 注册表

  2. 扫描 AppModule 的 @Module() 装饰器
     → 读取 imports / controllers / providers / exports

  3. 递归解析模块图（Module Graph）
     → AppModule → UserModule → DatabaseModule → ...
     → 构建完整的依赖拓扑图

  4. 注册所有 Provider 到 IoC 容器
     → 每个 @Injectable() 类 → Token:Class 映射

  5. 实例化所有 Singleton Provider
     → 按依赖顺序创建实例（依赖先创建）
     → 解析构造函数参数 → 注入依赖

  6. 注册所有 Controller 路由
     → 扫描 @Get() / @Post() 等装饰器
     → 生成路由表 → 注册到 Express/Fastify

  7. 绑定全局增强器
     → 全局 Middleware / Guard / Interceptor / Pipe / Filter

  8. 执行生命周期钩子
     → onModuleInit() → onApplicationBootstrap()

  总耗时：通常 100-500ms（取决于模块数量）
```

```typescript
// app.module.ts — 根模块
@Module({
  imports: [UserModule, AuthModule, DatabaseModule],  // 导入子模块
  controllers: [AppController],                        // 注册控制器
  providers: [AppService],                             // 注册服务
})
export class AppModule {}

// app.controller.ts — 控制器
@Controller()
export class AppController {
  constructor(private readonly appService: AppService) {}

  @Get()
  getHello(): string {
    return this.appService.getHello();
  }
}

// 当 GET / 请求到达时的完整流程：
// HTTP Request
//   → Express/Fastify 接收
//   → NestJS 路由匹配（找到 AppController.getHello）
//   → 执行 Middleware
//   → 执行 Guard（检查是否允许访问）
//   → 执行 Interceptor（前置逻辑）
//   → 执行 Pipe（参数验证/转换）
//   → 调用 Controller 方法
//   → 执行 Interceptor（后置逻辑）
//   → 返回 Response
```

> 💡 **关键洞察**：NestJS 的"重"不在运行时——它的运行时性能和纯 Express 几乎一样（差距 < 5%）。它的"重"在启动时：需要扫描装饰器、构建模块图、创建 Provider 实例。但这个启动开销是一次性的，换来的是运行时的零反射开销。

---

## 2. TypeScript 装饰器：NestJS 的元编程基石

NestJS 的一切"魔法"——`@Controller`、`@Injectable`、`@Get`——都建立在 TypeScript 装饰器之上。不理解装饰器，就永远只能"知其然不知其所以然"。

### 2.1 装饰器的本质：元数据 + 反射

装饰器不是什么高深的东西——它就是一个**在类/方法/属性/参数上执行的函数**：

```typescript
// 装饰器的本质：一个函数
// 类装饰器 → 接收构造函数
// 方法装饰器 → 接收 target, key, descriptor
// 属性装饰器 → 接收 target, key
// 参数装饰器 → 接收 target, key, paramIndex

// 最简单的类装饰器
function Log(constructor: Function) {
  console.log(`类 ${constructor.name} 被创建了`);
}

@Log
class UserService {}  // 输出：类 UserService 被创建了
// 等价于：Log(UserService)
```

```
TypeScript 五种装饰器（按执行顺序）：

  1. 参数装饰器（Parameter）  → 最先执行
     function(@Body() body: CreateUserDto)
     
  2. 方法装饰器（Method）     → 其次
     @Get('/:id')
     
  3. 访问器装饰器（Accessor） → 同方法装饰器
     @Transform() get fullName()
     
  4. 属性装饰器（Property）   → 再次
     @Column() name: string
     
  5. 类装饰器（Class）        → 最后执行
     @Controller('users')

  执行顺序口诀：从内到外、从下到上
  → 参数 → 方法 → 属性 → 类
  → 同级别从下往上执行
```

**装饰器工厂**——大多数 NestJS 装饰器都是这种模式：

```typescript
// 装饰器工厂 = 返回装饰器的函数
// 为什么需要工厂？因为要传参数！

// @Get() 的简化实现
function Get(path: string = '') {
  // 返回真正的方法装饰器
  return (target: any, key: string, descriptor: PropertyDescriptor) => {
    // 把路由信息存储为"元数据"
    Reflect.defineMetadata('path', path, target, key);
    Reflect.defineMetadata('method', 'GET', target, key);
  };
}

// @Controller() 的简化实现
function Controller(prefix: string = '') {
  return (constructor: Function) => {
    Reflect.defineMetadata('prefix', prefix, constructor);
  };
}

// 使用
@Controller('users')        // Controller('users')(UserController)
class UserController {
  @Get(':id')               // Get(':id')(UserController.prototype, 'findOne', descriptor)
  findOne() { /* ... */ }
}

// NestJS 启动时：
// 1. 读取 Controller 的 prefix 元数据 → 'users'
// 2. 读取 findOne 的 path 元数据 → ':id'
// 3. 读取 findOne 的 method 元数据 → 'GET'
// 4. 注册路由：GET /users/:id → UserController.findOne
```

> 💡 **装饰器不执行业务逻辑**——它只做一件事：往类/方法/参数上"贴标签"（存储元数据）。真正读取这些标签并执行逻辑的，是 NestJS 的 IoC 容器和路由系统。

### 2.2 reflect-metadata：NestJS 的隐藏引擎

NestJS 的依赖注入之所以能"自动推断类型"，全靠 `reflect-metadata` 这个库：

```typescript
// 问题：NestJS 怎么知道构造函数需要注入什么？
@Injectable()
class UserService {
  constructor(
    private readonly userRepo: UserRepository,  // NestJS 怎么知道这里要注入 UserRepository？
    private readonly logger: LoggerService,     // 怎么知道这里要注入 LoggerService？
  ) {}
}

// 答案：TypeScript 编译器 + reflect-metadata
```

```
reflect-metadata 的工作原理：

  编译前（TypeScript）：
  ┌────────────────────────────────────────┐
  │  @Injectable()                         │
  │  class UserService {                   │
  │    constructor(                         │
  │      private userRepo: UserRepository, │
  │      private logger: LoggerService,    │
  │    ) {}                                │
  │  }                                     │
  └────────────────────────────────────────┘

  编译后（JavaScript + emitDecoratorMetadata: true）：
  ┌────────────────────────────────────────────────────┐
  │  // TypeScript 编译器自动插入的元数据               │
  │  __decorate([                                      │
  │    Injectable(),                                    │
  │    __metadata("design:paramtypes", [               │ ← 关键！
  │      UserRepository,                                │    自动记录构造函数
  │      LoggerService                                  │    参数的类型信息
  │    ])                                               │
  │  ], UserService);                                   │
  └────────────────────────────────────────────────────┘

  NestJS IoC 容器启动时：
  ┌────────────────────────────────────────────────────┐
  │  // 读取编译器存储的类型元数据                       │
  │  const deps = Reflect.getMetadata(                  │
  │    'design:paramtypes',                             │
  │    UserService                                      │
  │  );                                                 │
  │  // deps = [UserRepository, LoggerService]          │
  │  // → 按顺序创建并注入这些依赖                      │
  └────────────────────────────────────────────────────┘
```

三种内置元数据键：

| 元数据键 | 含义 | 使用场景 |
|:---|:---|:---|
| `design:type` | 属性/参数的类型 | 属性装饰器 |
| `design:paramtypes` | 构造函数参数类型列表 | **依赖注入的核心** |
| `design:returntype` | 方法返回值类型 | 方法装饰器 |

```typescript
// 手动读取元数据（理解原理用，实际不需要这样写）
import 'reflect-metadata';

@Injectable()
class OrderService {
  constructor(
    private userService: UserService,
    private paymentService: PaymentService,
  ) {}
}

// 读取构造函数参数类型
const paramTypes = Reflect.getMetadata('design:paramtypes', OrderService);
console.log(paramTypes);
// [Function: UserService, Function: PaymentService]

// 这就是 NestJS IoC 容器做的事情：
// 1. 用 Reflect.getMetadata 读取每个 @Injectable 类的构造函数参数
// 2. 递归创建这些依赖
// 3. 注入到构造函数中
```

```
⚠️ reflect-metadata 的限制（NestJS 的痛点）：

  能推断的类型：
  ✅ 具体的 class（UserService、UserRepository）
  ✅ 原始类型（String、Number、Boolean）
  
  不能推断的类型：
  ❌ interface → 编译后不存在，无法反射
  ❌ 泛型参数 → Repository<User> 编译后变成 Repository
  ❌ 联合类型 → string | number 变成 Object
  ❌ 数组类型 → string[] 变成 Array

  解决方案：用 @Inject(TOKEN) 手动指定
  constructor(@Inject('CONFIG') private config: AppConfig) {}
```

> 💡 **必须启用两个 tsconfig 选项**：`"experimentalDecorators": true` 和 `"emitDecoratorMetadata": true`。少了任何一个，NestJS 的依赖注入都会失效。NestJS CLI 创建的项目默认已配置好。

### 2.3 NestJS 内置装饰器全景：从 @Module 到 @Body

NestJS 提供了几十个内置装饰器，按功能分为 5 大类：

```
NestJS 内置装饰器分类：

  ┌─ 架构装饰器（定义应用结构）──────────────────────┐
  │  @Module()        定义模块                       │
  │  @Controller()    定义控制器                      │
  │  @Injectable()    标记为可注入的 Provider          │
  │  @Global()        标记为全局模块                   │
  └──────────────────────────────────────────────────┘

  ┌─ HTTP 方法装饰器（定义路由）─────────────────────┐
  │  @Get()   @Post()   @Put()   @Patch()   @Delete()│
  │  @Head()  @Options()  @All()                     │
  └──────────────────────────────────────────────────┘

  ┌─ 参数装饰器（提取请求数据）─────────────────────┐
  │  @Param()     路径参数     /users/:id            │
  │  @Query()     查询参数     /users?page=1         │
  │  @Body()      请求体       POST/PUT 的 JSON      │
  │  @Headers()   请求头       Authorization 等      │
  │  @Req()       原始 Request 对象                  │
  │  @Res()       原始 Response 对象                 │
  │  @Ip()        客户端 IP                          │
  │  @Session()   Session 对象                       │
  │  @UploadedFile()  上传的文件                      │
  └──────────────────────────────────────────────────┘

  ┌─ 增强器装饰器（请求管道控制）───────────────────┐
  │  @UseGuards()       绑定 Guard                   │
  │  @UseInterceptors() 绑定 Interceptor             │
  │  @UsePipes()        绑定 Pipe                    │
  │  @UseFilters()      绑定 ExceptionFilter         │
  │  @SetMetadata()     设置自定义元数据              │
  └──────────────────────────────────────────────────┘

  ┌─ 其他装饰器（辅助功能）─────────────────────────┐
  │  @Inject()          手动指定注入 Token            │
  │  @Optional()        标记依赖为可选                │
  │  @HttpCode()        自定义响应状态码              │
  │  @Header()          设置响应头                    │
  │  @Redirect()        重定向                        │
  │  @Render()          渲染模板                      │
  │  @Catch()           指定 Filter 捕获的异常类型    │
  └──────────────────────────────────────────────────┘
```

```typescript
// 一个控制器方法上可能叠加多少装饰器？
@Controller('users')                    // 类装饰器：路由前缀
@UseGuards(JwtAuthGuard)                // 类装饰器：全控制器启用 JWT 认证
export class UserController {
  
  @Post()                               // 方法装饰器：POST 方法
  @HttpCode(201)                        // 方法装饰器：返回 201
  @Header('Cache-Control', 'no-store')  // 方法装饰器：设置响应头
  @UseGuards(RolesGuard)                // 方法装饰器：角色检查
  @SetMetadata('roles', ['admin'])      // 方法装饰器：设置元数据
  @UsePipes(ValidationPipe)             // 方法装饰器：参数验证
  create(
    @Body() createUserDto: CreateUserDto,  // 参数装饰器：提取请求体
    @Headers('x-request-id') reqId: string, // 参数装饰器：提取请求头
  ) {
    // 实际业务逻辑
  }
}

// 看起来"装饰器地狱"？不——这是声明式编程：
// 每个装饰器都清晰表达了一个意图
// 比起 Express 中间件的 app.use() 链条，可读性强得多
```

### 2.4 自定义装饰器实战：@CurrentUser、@Roles、@ApiVersion

NestJS 提供了两种创建自定义装饰器的方式：`createParamDecorator`（参数装饰器）和 `SetMetadata`（元数据装饰器）。

**实战 1：@CurrentUser — 从请求中提取当前用户**

```typescript
// decorators/current-user.decorator.ts
import { createParamDecorator, ExecutionContext } from '@nestjs/common';

// createParamDecorator：创建参数装饰器
// data → 装饰器传入的参数（如 @CurrentUser('email') 中的 'email'）
// ctx  → 执行上下文（可以获取 HTTP Request / WebSocket / gRPC 等）
export const CurrentUser = createParamDecorator(
  (data: string | undefined, ctx: ExecutionContext) => {
    const request = ctx.switchToHttp().getRequest();
    const user = request.user;  // 由 AuthGuard 注入

    // 如果指定了字段名，只返回该字段
    return data ? user?.[data] : user;
  },
);

// 使用
@Controller('profile')
@UseGuards(JwtAuthGuard)
export class ProfileController {
  
  @Get()
  getProfile(@CurrentUser() user: User) {
    return user;  // 完整的用户对象
  }

  @Get('email')
  getEmail(@CurrentUser('email') email: string) {
    return { email };  // 只返回 email 字段
  }
}
```

**实战 2：@Roles — 基于元数据的权限控制**

```typescript
// decorators/roles.decorator.ts
import { SetMetadata } from '@nestjs/common';

export const ROLES_KEY = 'roles';

// SetMetadata：往方法/类上附加元数据
// 稍后在 Guard 中通过 Reflector 读取
export const Roles = (...roles: string[]) => SetMetadata(ROLES_KEY, roles);

// 使用
@Controller('admin')
export class AdminController {
  
  @Post('users')
  @Roles('admin', 'super-admin')  // 只有 admin 和 super-admin 可以访问
  createUser(@Body() dto: CreateUserDto) {
    // ...
  }
}

// 配套的 RolesGuard（在 Guard 中读取元数据）
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    // 用 Reflector 读取 @Roles() 设置的元数据
    const requiredRoles = this.reflector.getAllAndOverride<string[]>(
      ROLES_KEY,
      [context.getHandler(), context.getClass()],  // 方法级 > 类级
    );
    
    if (!requiredRoles) return true;  // 没有设置 @Roles → 放行

    const { user } = context.switchToHttp().getRequest();
    return requiredRoles.some(role => user.roles?.includes(role));
  }
}
```

**实战 3：组合装饰器 — 用 applyDecorators 减少重复**

```typescript
// decorators/api-auth.decorator.ts
import { applyDecorators, UseGuards, SetMetadata } from '@nestjs/common';
import { ApiBearerAuth, ApiUnauthorizedResponse } from '@nestjs/swagger';

// 组合多个装饰器为一个
export function Auth(...roles: string[]) {
  return applyDecorators(
    SetMetadata(ROLES_KEY, roles),
    UseGuards(JwtAuthGuard, RolesGuard),
    ApiBearerAuth(),
    ApiUnauthorizedResponse({ description: '未授权' }),
  );
}

// ❌ 之前：每个方法要写 4 个装饰器
@Post()
@UseGuards(JwtAuthGuard, RolesGuard)
@SetMetadata('roles', ['admin'])
@ApiBearerAuth()
@ApiUnauthorizedResponse({ description: '未授权' })
create() { /* ... */ }

// ✅ 之后：一个装饰器搞定
@Post()
@Auth('admin')
create() { /* ... */ }
```

> 💡 **装饰器设计原则**：装饰器应该是"声明式"的——看到 `@Auth('admin')` 就知道这个路由需要管理员权限，不需要去翻中间件配置。好的装饰器让代码读起来像英语。

---

## 3. IoC 容器与依赖注入：框架的灵魂

如果只能学 NestJS 的一个概念，那就是**依赖注入**——它决定了你的代码是否可测试、可维护、可扩展。

### 3.1 控制反转：从 new 到 @Injectable

```
什么是控制反转（Inversion of Control, IoC）？

  传统方式（你控制依赖）：
  ┌────────────────────────────────────┐
  │  class OrderService {              │
  │    // 我自己决定用什么数据库        │
  │    private db = new MySQL();       │ ← 硬编码依赖
  │    // 我自己决定用什么日志          │
  │    private logger = new Winston(); │ ← 紧耦合
  │  }                                 │
  └────────────────────────────────────┘
  问题：想换成 PostgreSQL？→ 改代码
        想写单元测试？→ 必须连真数据库

  IoC 方式（框架控制依赖）：
  ┌────────────────────────────────────┐
  │  class OrderService {              │
  │    constructor(                     │
  │      private db: Database,         │ ← 我只声明"我需要一个数据库"
  │      private logger: Logger,       │ ← 至于用哪个，框架决定
  │    ) {}                            │
  │  }                                 │
  └────────────────────────────────────┘
  "控制"被"反转"了：
  从 → 我来创建依赖
  到 → 框架给我注入依赖
```

```typescript
// NestJS 中的依赖注入——只需要两步

// 第 1 步：用 @Injectable() 标记一个类为"可注入的 Provider"
@Injectable()
export class UserRepository {
  async findById(id: number): Promise<User> {
    // 数据库查询逻辑
  }
}

// 第 2 步：在构造函数中声明你需要它
@Injectable()
export class UserService {
  constructor(
    private readonly userRepo: UserRepository,  // NestJS 自动注入
  ) {}

  async getUser(id: number) {
    return this.userRepo.findById(id);
  }
}

// 第 3 步（可选）：在 Module 中注册
@Module({
  providers: [UserService, UserRepository],  // 告诉 IoC 容器管理这两个类
  controllers: [UserController],
})
export class UserModule {}

// IoC 容器启动时自动完成：
// 1. 创建 UserRepository 实例
// 2. 创建 UserService 实例，注入 UserRepository
// 3. 创建 UserController 实例，注入 UserService
```

为什么依赖注入让测试变简单？

```typescript
// 单元测试：轻松替换真实依赖为 Mock
describe('UserService', () => {
  let service: UserService;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      providers: [
        UserService,
        {
          provide: UserRepository,
          useValue: {
            // Mock 实现——不需要真数据库
            findById: jest.fn().mockResolvedValue({ id: 1, name: 'Test' }),
          },
        },
      ],
    }).compile();

    service = module.get(UserService);
  });

  it('should return user', async () => {
    const user = await service.getUser(1);
    expect(user.name).toBe('Test');  // 使用 Mock 数据
  });
});
```

> 💡 **@Injectable() 做了什么？** 它并不"注入"任何东西——它只是告诉 TypeScript 编译器"请为这个类生成 `design:paramtypes` 元数据"。没有 @Injectable()，reflect-metadata 不会记录构造函数参数类型，IoC 容器就不知道该注入什么。

### 3.2 Provider 注册与解析：Token → 实例的旅程

IoC 容器的核心是一张 **Token → 实例** 的映射表：

```
IoC 容器的内部结构（简化版）：

  Container = Map<Token, Instance>

  ┌─────────────────────┬──────────────────────────┐
  │  Token（注册键）     │  Instance（实例）          │
  ├─────────────────────┼──────────────────────────┤
  │  UserService        │  new UserService(...)     │
  │  UserRepository     │  new UserRepository(...)  │
  │  'DATABASE_URL'     │  'postgres://...'         │
  │  ConfigService      │  new ConfigService(...)   │
  └─────────────────────┴──────────────────────────┘

  Token 的三种类型：
  1. Class 本身    → 最常用，@Injectable() 类自动用类名作 Token
  2. 字符串        → 'DATABASE_URL'、'APP_CONFIG'
  3. Symbol        → Symbol('CACHE_MANAGER')
```

```typescript
// 标准 Provider 注册——简写 vs 完整写法

// ✅ 简写（日常用这个）
@Module({
  providers: [UserService],
})

// ↑ 等价于 ↓

// ✅ 完整写法（理解原理用）
@Module({
  providers: [
    {
      provide: UserService,    // Token：用 UserService 类本身作为标识
      useClass: UserService,   // 实现：创建 UserService 的实例
    },
  ],
})

// 这就是为什么注入时用"类型"就能匹配：
constructor(private userService: UserService) {}
// TypeScript 编译后：paramtypes = [UserService]
// IoC 容器查找：Container.get(UserService) → 返回实例
```

```
Provider 解析流程（当容器创建 OrderService 时）：

  @Injectable()
  class OrderService {
    constructor(
      private userService: UserService,
      private paymentService: PaymentService,
    ) {}
  }

  解析步骤：
  1. 读取 OrderService 的 design:paramtypes
     → [UserService, PaymentService]
  
  2. 对每个依赖递归解析：
     UserService 是否已创建？
     ├── 是 → 直接返回缓存的实例（Singleton）
     └── 否 → UserService 有哪些依赖？
              → 读取 UserService 的 paramtypes
              → 递归创建...
  
  3. 所有依赖就绪后，创建 OrderService：
     new OrderService(userServiceInstance, paymentServiceInstance)
  
  4. 缓存实例，下次直接返回

  ⚠️ 如果某个 Token 找不到对应的 Provider
     → 抛出 Nest could not resolve dependencies 错误
```

> 💡 **最常见的报错** `Nest can't resolve dependencies of XXX. Please make sure that the argument YYY at index [0] is available`——这意味着你忘了在 Module 的 `providers` 中注册 YYY，或者 YYY 所在的 Module 没有被 `imports` 导入。

### 3.3 四种自定义 Provider：不只是 class

当简写 `providers: [UserService]` 不够用时——你需要自定义 Provider：

```typescript
// 1️⃣ useClass — 替换实现类（策略模式）
// 场景：开发环境用 MockMailService，生产环境用 SendGridMailService

{
  provide: MailService,           // Token：用接口/抽象类
  useClass: process.env.NODE_ENV === 'production'
    ? SendGridMailService         // 生产：真实邮件服务
    : MockMailService,            // 开发：模拟邮件服务
}

// 注入时用抽象类型：
constructor(private mailService: MailService) {}
// 不关心底层实现是 SendGrid 还是 Mock
```

```typescript
// 2️⃣ useValue — 注入常量、配置对象
// 场景：注入配置、Mock 对象、第三方实例

// 注入配置对象
{
  provide: 'APP_CONFIG',
  useValue: {
    port: 3000,
    apiPrefix: '/api/v1',
    rateLimit: { ttl: 60, limit: 100 },
  },
}

// 注入第三方 SDK 实例
{
  provide: 'STRIPE_CLIENT',
  useValue: new Stripe(process.env.STRIPE_SECRET_KEY),
}

// 使用 @Inject() 注入字符串 Token（因为不是 class，无法自动推断）
constructor(
  @Inject('APP_CONFIG') private config: AppConfig,
  @Inject('STRIPE_CLIENT') private stripe: Stripe,
) {}
```

```typescript
// 3️⃣ useFactory — 动态创建（最灵活）
// 场景：依赖其他 Provider、异步初始化、条件创建

// 同步工厂
{
  provide: 'DATABASE_CONNECTION',
  useFactory: (configService: ConfigService) => {
    const dbUrl = configService.get('DATABASE_URL');
    return new DatabaseConnection(dbUrl);
  },
  inject: [ConfigService],  // 声明工厂函数的依赖（按顺序注入）
}

// 异步工厂（返回 Promise）
{
  provide: 'REDIS_CLIENT',
  useFactory: async (configService: ConfigService) => {
    const client = createClient({
      url: configService.get('REDIS_URL'),
    });
    await client.connect();  // 等待连接建立
    return client;
  },
  inject: [ConfigService],
}

// NestJS 会等待 Promise resolve 后才开始注入
```

```typescript
// 4️⃣ useExisting — 别名（指向已有 Provider）
// 场景：一个实现绑定多个 Token

{
  provide: 'AliasedLogger',       // 新 Token
  useExisting: LoggerService,     // 指向已有的 LoggerService
}

// 现在 LoggerService 和 'AliasedLogger' 指向同一个实例
// 常用于向后兼容：旧 Token 指向新实现
```

| Provider 类型 | 使用场景 | 是否支持异步 |
|:---|:---|:---|
| `useClass` | 替换实现、策略模式 | ❌ |
| `useValue` | 常量、配置、Mock | ❌ |
| `useFactory` | 动态创建、异步初始化 | ✅ |
| `useExisting` | 别名、向后兼容 | ❌ |

### 3.4 作用域：Singleton vs Request vs Transient

NestJS 的 Provider 默认是**单例**的——但有时你需要不同的生命周期：

```
三种 Provider 作用域：

  Singleton（默认）：
  ┌──────────────────────────────────────┐
  │  整个应用只创建 1 个实例              │
  │  所有注入点共享同一个对象              │
  │  应用启动时创建，应用关闭时销毁        │
  │                                      │
  │  请求 A ──┐                          │
  │  请求 B ──┼──→ 同一个 UserService 实例│
  │  请求 C ──┘                          │
  └──────────────────────────────────────┘
  适用：无状态服务（绝大多数场景）

  Request：
  ┌──────────────────────────────────────┐
  │  每个 HTTP 请求创建 1 个新实例         │
  │  请求结束后销毁                       │
  │                                      │
  │  请求 A ──→ UserService 实例 #1       │
  │  请求 B ──→ UserService 实例 #2       │
  │  请求 C ──→ UserService 实例 #3       │
  └──────────────────────────────────────┘
  适用：需要请求级状态（如多租户、请求上下文）

  Transient：
  ┌──────────────────────────────────────┐
  │  每次注入都创建 1 个新实例             │
  │  即使在同一个请求中，不同消费者        │
  │  也会拿到不同的实例                   │
  │                                      │
  │  Controller ──→ UserService 实例 #1   │
  │  Guard ────────→ UserService 实例 #2  │
  └──────────────────────────────────────┘
  适用：需要隔离状态的工具类
```

```typescript
// 设置作用域
import { Injectable, Scope } from '@nestjs/common';

// Singleton（默认，不需要显式声明）
@Injectable()
export class UserService {}

// Request 作用域
@Injectable({ scope: Scope.REQUEST })
export class RequestContextService {
  private tenantId: string;

  setTenant(id: string) { this.tenantId = id; }
  getTenant() { return this.tenantId; }
}
// 每个请求有独立的 tenantId，不会串数据

// Transient 作用域
@Injectable({ scope: Scope.TRANSIENT })
export class LoggerService {
  private context: string;

  setContext(name: string) { this.context = name; }
  log(msg: string) { console.log(`[${this.context}] ${msg}`); }
}
// 每个注入点拿到独立实例，context 不会冲突
```

```
⚠️ 作用域的"传染性"：

  如果 ServiceA（Singleton）依赖 ServiceB（Request）
  → ServiceA 也会被"提升"为 Request 作用域！
  → 因为 Singleton 不能持有 Request 级别的引用

  Singleton ← 依赖 ← Request  → 报错或 Singleton 变成 Request
  Singleton ← 依赖 ← Transient → Singleton 变成 Transient

  最佳实践：
  ✅ 99% 的 Provider 用默认 Singleton
  ✅ 只在真正需要请求隔离时用 Request
  ⚠️ Transient 慎用，每次注入都创建新对象，有性能开销
```

### 3.5 循环依赖与 forwardRef：打破死锁

当两个 Provider 互相依赖时，IoC 容器无法决定先创建谁：

```
循环依赖问题：

  UserService 需要 OrderService（获取用户订单）
  OrderService 需要 UserService（验证订单用户）

  创建 UserService → 需要先创建 OrderService
  创建 OrderService → 需要先创建 UserService
  → 死锁！💀
```

```typescript
// ❌ 直接互相依赖 → 报错
@Injectable()
export class UserService {
  constructor(private orderService: OrderService) {}  // 需要 OrderService
}

@Injectable()
export class OrderService {
  constructor(private userService: UserService) {}    // 需要 UserService
}
// Error: A circular dependency has been detected

// ✅ 用 forwardRef 打破循环
@Injectable()
export class UserService {
  constructor(
    @Inject(forwardRef(() => OrderService))  // 延迟解析
    private orderService: OrderService,
  ) {}
}

@Injectable()
export class OrderService {
  constructor(
    @Inject(forwardRef(() => UserService))   // 延迟解析
    private userService: UserService,
  ) {}
}
// forwardRef 告诉容器：先创建一个空引用，稍后再填充
```

```typescript
// 模块级循环依赖也需要 forwardRef
@Module({
  imports: [forwardRef(() => OrderModule)],  // 延迟导入
  providers: [UserService],
  exports: [UserService],
})
export class UserModule {}

@Module({
  imports: [forwardRef(() => UserModule)],   // 延迟导入
  providers: [OrderService],
  exports: [OrderService],
})
export class OrderModule {}
```

```
⚠️ 循环依赖是代码坏味道！forwardRef 是止痛药，不是治疗方案。

  更好的解决方式：
  
  1. 提取共享逻辑到第三个 Service
     UserService ──→ SharedService ←── OrderService
     
  2. 用事件驱动解耦
     UserService ──→ EventEmitter ←── OrderService
     
  3. 重新审视职责划分
     也许 UserService 不应该关心订单？
     → 创建 UserOrderService 聚合层
```

> 💡 **实践原则**：如果你发现自己经常需要 `forwardRef`，说明模块划分有问题。健康的依赖图应该是**有向无环图（DAG）**——依赖方向单一，不形成环路。

---

## 4. Module 系统：应用的骨架

Module 是 NestJS 的组织单元——它决定了哪些 Provider 属于哪个边界，谁能访问谁。理解 Module 就理解了 NestJS 应用的"骨架"。

### 4.1 @Module 解剖：imports/exports/providers/controllers

```
@Module() 的四大属性：

  @Module({
    imports:      [...],  ← 导入其他模块（获取它们 exports 的 Provider）
    controllers:  [...],  ← 注册本模块的控制器（处理 HTTP 请求）
    providers:    [...],  ← 注册本模块的 Provider（Service/Repository 等）
    exports:      [...],  ← 导出 Provider，让其他模块可以使用
  })

  四者的关系：
  ┌─────────────────────────────────────────────┐
  │                 UserModule                   │
  │                                             │
  │  imports: [DatabaseModule]                   │
  │    → 获取 DatabaseModule 导出的 Repository   │
  │                                             │
  │  providers: [UserService]                    │
  │    → UserService 可以注入 Repository          │
  │    → UserService 只在 UserModule 内部可用     │
  │                                             │
  │  controllers: [UserController]               │
  │    → UserController 可以注入 UserService      │
  │                                             │
  │  exports: [UserService]                      │
  │    → 其他模块 import UserModule 后            │
  │    → 可以注入 UserService                    │
  └─────────────────────────────────────────────┘
```

```typescript
// 完整示例：模块间的依赖关系

// database.module.ts — 提供数据库能力
@Module({
  providers: [
    DatabaseService,
    UserRepository,
    OrderRepository,
  ],
  exports: [UserRepository, OrderRepository],  // 导出 Repository
  // 注意：DatabaseService 没有 export → 外部无法访问
})
export class DatabaseModule {}

// user.module.ts — 用户业务模块
@Module({
  imports: [DatabaseModule],     // 导入 → 获得 UserRepository
  controllers: [UserController],
  providers: [UserService],      // UserService 可以注入 UserRepository
  exports: [UserService],        // 导出 → 其他模块可以用 UserService
})
export class UserModule {}

// order.module.ts — 订单业务模块
@Module({
  imports: [
    DatabaseModule,              // 获得 OrderRepository
    UserModule,                  // 获得 UserService（用于验证用户）
  ],
  controllers: [OrderController],
  providers: [OrderService],
})
export class OrderModule {}

// app.module.ts — 根模块（拼装所有模块）
@Module({
  imports: [UserModule, OrderModule],  // 只需导入顶层业务模块
})
export class AppModule {}
```

```
模块图（Module Graph）：

  AppModule
  ├── UserModule
  │   └── DatabaseModule
  └── OrderModule
      ├── DatabaseModule  ← 同一个模块被多次导入？
      └── UserModule          NestJS 自动去重，只实例化一次
```

> 💡 **关键概念**：`providers` 中注册的 Provider 默认只在本模块内可见。要让其他模块使用，必须放入 `exports`。这就是 NestJS 的"**模块封装性**"——像 Java 的 package-private。

### 4.2 模块封装性：为什么 Provider 默认不共享

```
模块封装性规则：

  规则 1：Provider 只在声明它的模块内可见
  ┌─ UserModule ──────────┐  ┌─ OrderModule ─────────┐
  │  providers:            │  │  providers:            │
  │    UserService ✅      │  │    OrderService ✅     │
  │    UserHelper  ✅      │  │                        │
  │                        │  │  想用 UserHelper？     │
  │  exports:              │  │  ❌ 不行！没有 export  │
  │    UserService         │  │                        │
  └────────────────────────┘  └────────────────────────┘

  规则 2：import 一个模块 = 获得它 exports 的 Provider
  规则 3：import 不具有传递性
    A imports B, B imports C
    → A 能用 B 的 exports
    → A 不能用 C 的 exports（除非 B 重导出了 C）
```

```typescript
// 重导出（Re-export）：让 import 具有传递性

@Module({
  imports: [DatabaseModule],
  exports: [DatabaseModule],    // 重导出整个模块！
  // 现在：谁 import CommonModule，就自动获得 DatabaseModule 的 exports
})
export class CommonModule {}

// 效果：
// OrderModule → imports [CommonModule]
// → 自动获得 DatabaseModule 导出的所有 Provider
```

```typescript
// @Global() — 全局模块（慎用）
@Global()  // 标记为全局
@Module({
  providers: [ConfigService, LoggerService],
  exports: [ConfigService, LoggerService],
})
export class CoreModule {}

// 效果：任何模块都可以注入 ConfigService 和 LoggerService
// 不需要在每个模块的 imports 中添加 CoreModule

// ⚠️ @Global 的使用原则：
// ✅ 适合：ConfigService、LoggerService、CacheService（全局基础设施）
// ❌ 不适合：UserService、OrderService（业务模块不应该全局化）
// 原因：滥用 @Global 会破坏模块封装性，变回"全局变量"模式
```

> 💡 **封装性是 NestJS 区别于 Express 的核心优势**——它强制你思考"这个 Service 应该暴露给谁"，而不是所有代码都能随意互相引用。这在大型团队协作中至关重要。

### 4.3 动态模块：forRoot / forRootAsync 模式

静态模块的配置在编译时就确定了。动态模块允许在**导入时传入配置**——这是 NestJS 官方包的标准模式：

```typescript
// 你见过的动态模块用法：
@Module({
  imports: [
    // 静态模块：直接导入
    UserModule,
    
    // 动态模块：调用静态方法，传入配置
    TypeOrmModule.forRoot({          // 同步配置
      type: 'postgres',
      host: 'localhost',
      database: 'myapp',
    }),
    
    ConfigModule.forRoot({           // 同步配置
      isGlobal: true,
      envFilePath: '.env',
    }),
    
    JwtModule.registerAsync({        // 异步配置（依赖其他 Provider）
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        secret: config.get('JWT_SECRET'),
        signOptions: { expiresIn: '1h' },
      }),
    }),
  ],
})
export class AppModule {}
```

```
forRoot vs forFeature vs register 命名约定：

  forRoot()        → 根模块调用，全局配置，只调用一次
                     例：TypeOrmModule.forRoot（数据库连接）
  
  forFeature()     → 子模块调用，注册局部资源
                     例：TypeOrmModule.forFeature（注册 Entity）
  
  register()       → 每次调用都创建新实例
                     例：JwtModule.register（每个模块独立配置）
  
  xxxAsync()       → 异步版本，支持 useFactory 注入其他 Provider
                     例：forRootAsync / registerAsync
```

```typescript
// 自己实现一个动态模块（理解原理）

@Module({})
export class MailModule {
  // forRoot：返回一个动态模块定义
  static forRoot(options: MailOptions): DynamicModule {
    return {
      module: MailModule,           // 必须：指向当前类
      global: options.isGlobal,     // 可选：是否全局
      providers: [
        {
          provide: 'MAIL_OPTIONS',  // 用 useValue 注入配置
          useValue: options,
        },
        MailService,                // 注册 Service
      ],
      exports: [MailService],       // 导出 Service
    };
  }

  // forRootAsync：支持异步配置
  static forRootAsync(options: MailAsyncOptions): DynamicModule {
    return {
      module: MailModule,
      providers: [
        {
          provide: 'MAIL_OPTIONS',
          useFactory: options.useFactory,  // 工厂函数
          inject: options.inject || [],    // 工厂的依赖
        },
        MailService,
      ],
      exports: [MailService],
    };
  }
}

// 使用
@Module({
  imports: [
    MailModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        host: config.get('SMTP_HOST'),
        port: config.get('SMTP_PORT'),
        auth: { user: config.get('SMTP_USER'), pass: config.get('SMTP_PASS') },
      }),
    }),
  ],
})
export class AppModule {}
```

> 💡 **forRoot/forRootAsync 是 NestJS 生态的"标准接口"**——几乎所有官方和社区模块都遵循这个模式。掌握它，你就能看懂任何 NestJS 第三方库的 README。

### 4.4 企业级模块架构：Core / Shared / Feature 三层设计

大型 NestJS 项目的模块应该分为三层：

```
企业级模块三层架构：

  ┌──────────────────────────────────────────────┐
  │                 AppModule（根）               │
  ├──────────────────────────────────────────────┤
  │                                              │
  │  ┌─ Core Module ──────────────────────────┐  │
  │  │  @Global() — 只导入一次，全局可用       │  │
  │  │                                        │  │
  │  │  ConfigModule    配置管理               │  │
  │  │  LoggerModule    日志                   │  │
  │  │  DatabaseModule  数据库连接             │  │
  │  │  AuthModule      认证                   │  │
  │  │  CacheModule     缓存                   │  │
  │  └────────────────────────────────────────┘  │
  │                                              │
  │  ┌─ Shared Module ────────────────────────┐  │
  │  │  需要时 import — 通用工具和组件         │  │
  │  │                                        │  │
  │  │  PaginationHelper   分页工具            │  │
  │  │  FileUploadService  文件上传            │  │
  │  │  MailService        邮件发送            │  │
  │  │  CommonPipes         通用管道            │  │
  │  │  CommonGuards        通用守卫            │  │
  │  └────────────────────────────────────────┘  │
  │                                              │
  │  ┌─ Feature Modules ──────────────────────┐  │
  │  │  各自独立 — 业务领域模块                │  │
  │  │                                        │  │
  │  │  UserModule       用户管理              │  │
  │  │  OrderModule      订单管理              │  │
  │  │  ProductModule    商品管理              │  │
  │  │  PaymentModule    支付模块              │  │
  │  │  NotificationModule 通知模块            │  │
  │  └────────────────────────────────────────┘  │
  └──────────────────────────────────────────────┘
```

```
对应的项目目录结构：

  src/
  ├── main.ts                    应用入口
  ├── app.module.ts              根模块
  │
  ├── core/                      核心模块（全局基建）
  │   ├── core.module.ts
  │   ├── config/
  │   │   └── config.module.ts
  │   ├── database/
  │   │   └── database.module.ts
  │   ├── auth/
  │   │   ├── auth.module.ts
  │   │   ├── guards/
  │   │   └── strategies/
  │   └── logger/
  │       └── logger.module.ts
  │
  ├── shared/                    共享模块（通用工具）
  │   ├── shared.module.ts
  │   ├── decorators/
  │   ├── pipes/
  │   ├── filters/
  │   ├── interceptors/
  │   └── utils/
  │
  └── modules/                   业务模块（按领域划分）
      ├── user/
      │   ├── user.module.ts
      │   ├── user.controller.ts
      │   ├── user.service.ts
      │   ├── entities/
      │   └── dto/
      ├── order/
      │   ├── order.module.ts
      │   └── ...
      └── product/
          ├── product.module.ts
          └── ...
```

| 模块类型 | @Global | 导入频率 | 包含内容 | 原则 |
|:---|:---|:---|:---|:---|
| **Core** | ✅ 是 | 只在 AppModule 导入一次 | 数据库/配置/认证/日志 | 全局基础设施 |
| **Shared** | ❌ 否 | 需要的模块按需导入 | 工具/管道/装饰器 | 无业务逻辑 |
| **Feature** | ❌ 否 | AppModule 导入 | 业务领域 CRUD | 按领域自治 |

> 💡 **模块划分的黄金法则**：Feature Module 之间尽量不要互相依赖。如果 UserModule 和 OrderModule 需要共享逻辑，提取到 Shared Module 或创建一个新的聚合 Service，而不是让两个 Feature Module 互相 import。

---

## 5. Controller 层：请求的入口

Controller 的职责很明确：**接收请求、提取参数、调用 Service、返回响应**——不多也不少。

### 5.1 路由注册：装饰器如何变成路由表

```typescript
// 路由 = @Controller 前缀 + @Method 路径

@Controller('api/v1/users')       // 前缀：/api/v1/users
export class UserController {

  @Get()                           // GET /api/v1/users
  findAll() {}

  @Get(':id')                      // GET /api/v1/users/:id
  findOne(@Param('id') id: string) {}

  @Post()                          // POST /api/v1/users
  create(@Body() dto: CreateUserDto) {}

  @Put(':id')                      // PUT /api/v1/users/:id
  update(@Param('id') id: string, @Body() dto: UpdateUserDto) {}

  @Delete(':id')                   // DELETE /api/v1/users/:id
  remove(@Param('id') id: string) {}
}
```

```
路由匹配规则：

  1. 精确匹配优先于参数匹配
     @Get('active')  → /users/active  ← 先匹配这个
     @Get(':id')     → /users/123     ← 再匹配这个
     ⚠️ 顺序很重要！把精确路由放在参数路由之前

  2. 全局前缀
     // main.ts
     app.setGlobalPrefix('api');
     → 所有路由自动加上 /api 前缀
     → GET /api/users、POST /api/users

  3. 路由通配符
     @Get('ab*cd')   → 匹配 abcd、ab_cd、ab123cd
     @Get('docs/*')  → 匹配 /docs 下所有子路径
```

```typescript
// 控制器的返回值处理

@Controller('users')
export class UserController {

  // 1. 返回对象/数组 → 自动序列化为 JSON
  @Get()
  findAll(): User[] {
    return [{ id: 1, name: 'Alice' }];
    // → 响应：200 OK, Content-Type: application/json
  }

  // 2. 返回 Promise → 自动等待并序列化
  @Get(':id')
  async findOne(@Param('id') id: string): Promise<User> {
    return this.userService.findById(+id);
    // → NestJS 自动 await
  }

  // 3. 返回 Observable → 自动订阅
  @Get('stream')
  findStream(): Observable<User[]> {
    return this.userService.findAllStream();
    // → NestJS 自动 subscribe，取第一个值
  }

  // 4. 自定义状态码
  @Post()
  @HttpCode(201)              // 默认 POST 返回 201
  create(@Body() dto: CreateUserDto) {
    return this.userService.create(dto);
  }

  // 5. 自定义响应头
  @Get('download')
  @Header('Content-Type', 'application/octet-stream')
  download() {
    return this.fileService.getFile();
  }
}
```

> 💡 **Controller 的纪律**：Controller 方法应该是"薄"的——提取参数、调用 Service、返回结果。如果你发现 Controller 里有超过 10 行业务逻辑，说明该提取到 Service 中了。

### 5.2 参数提取：@Param / @Query / @Body / @Headers 全解

```typescript
// 一个请求的所有可提取部分：
// GET /users/42?page=1&limit=10
// Headers: { Authorization: 'Bearer xxx', 'x-request-id': 'abc' }
// Body: { name: 'Alice', email: 'alice@example.com' }

@Controller('users')
export class UserController {

  // @Param — 路径参数
  @Get(':id')
  findOne(
    @Param('id') id: string,            // 提取单个参数：'42'
    // @Param() params: { id: string },  // 提取全部路径参数
  ) {}

  // @Query — 查询参数
  @Get()
  findAll(
    @Query('page') page: string,         // '1'
    @Query('limit') limit: string,       // '10'
    // @Query() query: { page: string, limit: string },  // 提取全部
  ) {}

  // @Body — 请求体
  @Post()
  create(
    @Body() dto: CreateUserDto,          // 完整请求体
    @Body('name') name: string,          // 提取单个字段：'Alice'
  ) {}

  // @Headers — 请求头
  @Get('me')
  getMe(
    @Headers('authorization') auth: string,  // 'Bearer xxx'
    @Headers('x-request-id') reqId: string,  // 'abc'
    // @Headers() headers: Record<string, string>,  // 全部请求头
  ) {}

  // @Ip — 客户端 IP
  @Get('ip')
  getIp(@Ip() ip: string) {}

  // @Req / @Res — 原始请求/响应对象（尽量避免使用）
  @Get('raw')
  raw(@Req() req: Request, @Res() res: Response) {
    // ⚠️ 使用 @Res 后必须手动返回响应
    res.status(200).json({ msg: 'ok' });
    // NestJS 不再自动处理返回值
  }
}
```

| 装饰器 | 提取来源 | 示例 | 注意事项 |
|:---|:---|:---|:---|
| `@Param('key')` | URL 路径参数 | `/users/:id` → `id` | 始终是 string |
| `@Query('key')` | URL 查询参数 | `?page=1` → `page` | 始终是 string |
| `@Body()` | 请求体 | POST/PUT JSON | 配合 DTO 使用 |
| `@Headers('key')` | 请求头 | `Authorization` | key 不区分大小写 |
| `@Ip()` | 客户端 IP | `127.0.0.1` | 注意代理透传 |
| `@Req()` | 原始 Request | Express Request | 破坏平台无关性 |
| `@Res()` | 原始 Response | Express Response | 必须手动返回 |

> 💡 **避免使用 @Req/@Res**——它们绑定了底层平台（Express/Fastify），破坏了 NestJS 的平台无关性。用 @Param/@Query/@Body/@Headers 已经能覆盖 99% 的场景。

### 5.3 DTO 与验证：class-validator + class-transformer

DTO（Data Transfer Object）定义请求数据的"形状"，class-validator 负责验证：

```typescript
// dto/create-user.dto.ts
import {
  IsString, IsEmail, IsOptional, IsInt,
  MinLength, MaxLength, Min, Max,
  IsEnum, ValidateNested, IsArray,
} from 'class-validator';
import { Type } from 'class-transformer';

export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
}

export class AddressDto {
  @IsString()
  city: string;

  @IsString()
  street: string;
}

export class CreateUserDto {
  @IsString()
  @MinLength(2, { message: '用户名至少 2 个字符' })
  @MaxLength(50)
  name: string;

  @IsEmail({}, { message: '请输入有效的邮箱地址' })
  email: string;

  @IsInt()
  @Min(0)
  @Max(150)
  age: number;

  @IsEnum(UserRole)
  @IsOptional()                    // 可选字段
  role?: UserRole;

  @ValidateNested()                // 嵌套对象验证
  @Type(() => AddressDto)          // class-transformer：转换为类实例
  address: AddressDto;

  @IsArray()
  @IsString({ each: true })       // 数组中每个元素都是 string
  @IsOptional()
  tags?: string[];
}
```

```typescript
// main.ts — 全局启用 ValidationPipe
async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  
  app.useGlobalPipes(new ValidationPipe({
    whitelist: true,           // 自动剥离 DTO 中未定义的字段
    forbidNonWhitelisted: true, // 收到未定义字段时报错
    transform: true,            // 自动类型转换（string → number）
    transformOptions: {
      enableImplicitConversion: true,  // @Query('page') page: number → 自动转
    },
  }));
  
  await app.listen(3000);
}

// 请求 POST /users
// Body: { "name": "A", "email": "bad", "hack": "inject" }
// 响应 400：
// {
//   "statusCode": 400,
//   "message": [
//     "用户名至少 2 个字符",
//     "请输入有效的邮箱地址",
//     "property hack should not exist"   ← forbidNonWhitelisted
//   ],
//   "error": "Bad Request"
// }
```

```typescript
// UpdateUserDto — 用 PartialType 自动生成（所有字段变可选）
import { PartialType } from '@nestjs/mapped-types';

export class UpdateUserDto extends PartialType(CreateUserDto) {}
// 等价于 CreateUserDto 的所有字段加上 @IsOptional()

// 其他映射类型：
// PickType(CreateUserDto, ['name', 'email'])   → 只保留指定字段
// OmitType(CreateUserDto, ['age'])             → 排除指定字段
// IntersectionType(CreateUserDto, AddressDto)  → 合并两个 DTO
```

> 💡 **DTO 验证是 NestJS 的第一道防线**——在数据进入 Service 之前就拦截非法输入。`whitelist: true` + `forbidNonWhitelisted: true` 是企业级必开选项，可以防止批量赋值（Mass Assignment）攻击。

### 5.4 版本控制与 Swagger 文档自动生成

**API 版本控制**——NestJS 内置三种策略：

```typescript
// main.ts — 启用版本控制
import { VersioningType } from '@nestjs/common';

app.enableVersioning({
  type: VersioningType.URI,       // URI 版本：/v1/users、/v2/users
  // type: VersioningType.HEADER, // Header 版本：X-API-Version: 1
  // type: VersioningType.MEDIA_TYPE, // Accept: application/json;v=1
  defaultVersion: '1',
});

// controller 中使用
@Controller('users')
@Version('1')                     // 整个控制器使用 v1
export class UserV1Controller {
  @Get()
  findAll() { return 'v1 users'; }
}

@Controller('users')
@Version('2')                     // v2 版本的控制器
export class UserV2Controller {
  @Get()
  findAll() { return 'v2 users with pagination'; }
}

// 单方法版本控制
@Controller('users')
export class UserController {
  @Version('1')
  @Get()
  findAllV1() { return 'v1'; }

  @Version('2')
  @Get()
  findAllV2() { return 'v2'; }
}
```

**Swagger 文档自动生成**——从装饰器直接生成 API 文档：

```typescript
// main.ts — 配置 Swagger
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';

const config = new DocumentBuilder()
  .setTitle('用户管理 API')
  .setDescription('企业级用户管理系统 API 文档')
  .setVersion('1.0')
  .addBearerAuth()                  // 添加 JWT 认证
  .addTag('users', '用户相关接口')
  .build();

const document = SwaggerModule.createDocument(app, config);
SwaggerModule.setup('docs', app, document);  // 访问 /docs 查看文档

// Controller 中添加 Swagger 装饰器
@ApiTags('users')                   // 分组标签
@Controller('users')
export class UserController {

  @Post()
  @ApiOperation({ summary: '创建用户' })
  @ApiBody({ type: CreateUserDto })
  @ApiResponse({ status: 201, description: '创建成功', type: UserEntity })
  @ApiResponse({ status: 400, description: '参数验证失败' })
  @ApiBearerAuth()                  // 标记需要认证
  create(@Body() dto: CreateUserDto) {}
}

// DTO 中添加 Swagger 描述
export class CreateUserDto {
  @ApiProperty({ description: '用户名', example: 'alice', minLength: 2 })
  @IsString()
  @MinLength(2)
  name: string;

  @ApiProperty({ description: '邮箱', example: 'alice@example.com' })
  @IsEmail()
  email: string;

  @ApiPropertyOptional({ description: '角色', enum: UserRole })
  @IsOptional()
  role?: UserRole;
}
```

> 💡 **Swagger CLI 插件可以省掉大部分 @ApiProperty**——在 `nest-cli.json` 中添加 `"plugins": ["@nestjs/swagger"]`，插件会自动从 DTO 的类型和 class-validator 装饰器推断 Swagger 描述，减少 50% 以上的样板代码。

---

## 6. Service 层与 Repository 模式：业务逻辑的归宿

Service 是 NestJS 应用中最"重"的一层——它承载所有业务逻辑，是唯一应该包含 if/else 判断和业务规则的地方。

### 6.1 Service 的职责：不只是"放逻辑的地方"

```
NestJS 分层架构中每层的职责：

  Controller（瘦）         Service（厚）           Repository（薄）
  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
  │ 路由映射      │    │ 业务逻辑          │    │ 数据访问      │
  │ 参数提取      │ →  │ 权限判断          │ →  │ SQL 查询     │
  │ DTO 验证      │    │ 数据组装          │    │ 数据映射      │
  │ 返回响应      │    │ 事务协调          │    │ 缓存查询      │
  │              │    │ 调用外部服务       │    │              │
  └──────────────┘    └──────────────────┘    └──────────────┘
  
  ❌ 不该做的           ❌ 不该做的              ❌ 不该做的
  写业务逻辑           直接处理 HTTP           写业务逻辑
  操作数据库           关心请求/响应格式       处理权限判断
```

```typescript
// ❌ 反模式：Fat Controller（逻辑全堆在控制器里）
@Controller('orders')
export class OrderController {
  @Post()
  async create(@Body() dto: CreateOrderDto, @Req() req) {
    // 检查库存
    const product = await this.productRepo.findOne(dto.productId);
    if (product.stock < dto.quantity) throw new BadRequestException('库存不足');
    
    // 计算价格
    let total = product.price * dto.quantity;
    if (dto.couponCode) {
      const coupon = await this.couponRepo.findOne(dto.couponCode);
      total -= coupon.discount;
    }
    
    // 创建订单
    const order = await this.orderRepo.save({ ...dto, total, userId: req.user.id });
    
    // 发送通知
    await this.mailService.send(req.user.email, '订单创建成功', order);
    
    return order;
    // 问题：这段逻辑无法被其他 Controller/Service 复用
    // 问题：无法独立于 HTTP 进行单元测试
  }
}

// ✅ 正确：Thin Controller + Fat Service
@Controller('orders')
export class OrderController {
  constructor(private readonly orderService: OrderService) {}

  @Post()
  create(@Body() dto: CreateOrderDto, @CurrentUser() user: User) {
    return this.orderService.createOrder(dto, user);  // 一行调用
  }
}

@Injectable()
export class OrderService {
  constructor(
    private readonly orderRepo: OrderRepository,
    private readonly productService: ProductService,
    private readonly couponService: CouponService,
    private readonly mailService: MailService,
  ) {}

  async createOrder(dto: CreateOrderDto, user: User): Promise<Order> {
    // 检查库存
    await this.productService.checkStock(dto.productId, dto.quantity);
    
    // 计算价格
    const total = await this.calculateTotal(dto);
    
    // 创建订单
    const order = await this.orderRepo.create({ ...dto, total, userId: user.id });
    
    // 异步发送通知（不阻塞响应）
    this.mailService.sendOrderConfirmation(user.email, order);
    
    return order;
  }

  private async calculateTotal(dto: CreateOrderDto): Promise<number> {
    // 可复用、可测试的业务逻辑
  }
}
```

> 💡 **判断逻辑该放哪里的法则**：如果这段代码需要被多个 Controller 或其他 Service 调用——放 Service。如果这段代码只跟 HTTP 请求格式有关——放 Controller。如果这段代码只跟数据库查询有关——放 Repository。

### 6.2 Repository 模式：数据访问的抽象层

Repository 模式把数据库操作从 Service 中分离出来——Service 不关心数据来自 PostgreSQL 还是 MongoDB：

```typescript
// ❌ 直接在 Service 中写数据库查询
@Injectable()
export class UserService {
  async findByEmail(email: string) {
    // Service 与 TypeORM 紧耦合
    return this.dataSource.query(
      'SELECT * FROM users WHERE email = $1', [email]
    );
  }
}

// ✅ Repository 模式：数据访问封装在独立层
@Injectable()
export class UserRepository {
  constructor(
    @InjectRepository(UserEntity)
    private readonly repo: Repository<UserEntity>,
  ) {}

  async findByEmail(email: string): Promise<UserEntity | null> {
    return this.repo.findOne({ where: { email } });
  }

  async findActiveUsers(page: number, limit: number): Promise<UserEntity[]> {
    return this.repo.find({
      where: { isActive: true },
      skip: (page - 1) * limit,
      take: limit,
      order: { createdAt: 'DESC' },
    });
  }

  async createWithProfile(data: CreateUserData): Promise<UserEntity> {
    const user = this.repo.create(data);
    return this.repo.save(user);
  }
}

// Service 只依赖 Repository（不知道底层是什么数据库）
@Injectable()
export class UserService {
  constructor(private readonly userRepo: UserRepository) {}

  async register(dto: RegisterDto): Promise<UserEntity> {
    const existing = await this.userRepo.findByEmail(dto.email);
    if (existing) throw new ConflictException('邮箱已注册');
    return this.userRepo.createWithProfile(dto);
  }
}
```

```
Repository 模式的好处：

  1. 可测试性
     测试 Service 时 Mock UserRepository
     → 不需要真数据库

  2. 可替换性
     从 PostgreSQL 换成 MongoDB？
     → 只改 Repository 实现
     → Service 代码零修改

  3. 查询复用
     findActiveUsers、findByEmail
     → 多个 Service 可以复用
     → 复杂查询只写一次

  4. 关注点分离
     Service → 业务规则
     Repository → 数据查询优化
```

> 💡 **并非所有项目都需要自定义 Repository**——简单 CRUD 用 TypeORM 的 `@InjectRepository` 直接在 Service 中操作就够了。当查询逻辑开始复杂（分页、联表、子查询）时，再提取 Repository 层。

### 6.3 ORM 集成实战：TypeORM / Prisma / Drizzle

NestJS 生态中三大主流 ORM 的对比：

```typescript
// 1️⃣ TypeORM — NestJS 官方推荐，装饰器风格

// Entity 定义（装饰器风格，与 NestJS 风格一致）
@Entity('users')
export class UserEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  email: string;

  @Column({ default: true })
  isActive: boolean;

  @OneToMany(() => OrderEntity, (order) => order.user)
  orders: OrderEntity[];

  @CreateDateColumn()
  createdAt: Date;
}

// Module 注册
@Module({
  imports: [
    TypeOrmModule.forRoot({              // 全局数据库连接
      type: 'postgres',
      url: process.env.DATABASE_URL,
      entities: [UserEntity],
      synchronize: false,                // 生产环境必须关闭！
    }),
    TypeOrmModule.forFeature([UserEntity]), // 注册 Entity 到当前模块
  ],
})
```

```typescript
// 2️⃣ Prisma — Schema-first，类型安全极致

// prisma/schema.prisma（独立 Schema 文件）
// model User {
//   id        Int      @id @default(autoincrement())
//   email     String   @unique
//   isActive  Boolean  @default(true)
//   orders    Order[]
//   createdAt DateTime @default(now())
// }

// NestJS 集成
@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit {
  async onModuleInit() {
    await this.$connect();
  }
}

// 使用（类型全自动推导）
@Injectable()
export class UserService {
  constructor(private prisma: PrismaService) {}

  findAll() {
    return this.prisma.user.findMany({
      where: { isActive: true },
      include: { orders: true },  // 类型安全的关联查询
    });
  }
}
```

```typescript
// 3️⃣ Drizzle — SQL-like API，轻量高性能

// schema.ts（TypeScript 定义）
export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  email: varchar('email', { length: 255 }).unique(),
  isActive: boolean('is_active').default(true),
  createdAt: timestamp('created_at').defaultNow(),
});

// 使用（SQL-like 查询构建器）
@Injectable()
export class UserService {
  constructor(@Inject('DRIZZLE') private db: DrizzleDB) {}

  findActive() {
    return this.db.select()
      .from(users)
      .where(eq(users.isActive, true))
      .orderBy(desc(users.createdAt));
  }
}
```

| 维度 | TypeORM | Prisma | Drizzle |
|:---|:---|:---|:---|
| **风格** | 装饰器（Active Record） | Schema 文件 | TypeScript 定义 |
| **NestJS 集成** | ✅ 官方包 | ⚠️ 手动封装 | ⚠️ 手动封装 |
| **类型安全** | ⚠️ 部分 | ✅ 极致 | ✅ 极致 |
| **学习曲线** | 中（Java/C# 开发者熟悉） | 低 | 低（会 SQL 就行） |
| **性能** | 中 | 中 | ✅ 高 |
| **迁移工具** | 内置 | ✅ prisma migrate | drizzle-kit |
| **适合场景** | NestJS 深度集成 | 全栈 TypeScript | SQL 控制需求高 |

### 6.4 事务管理与 CQRS 模式初探

**事务管理**——确保多个数据库操作要么全部成功，要么全部回滚：

```typescript
// TypeORM 事务方式 1：DataSource.transaction
@Injectable()
export class OrderService {
  constructor(private dataSource: DataSource) {}

  async createOrder(dto: CreateOrderDto): Promise<Order> {
    return this.dataSource.transaction(async (manager) => {
      // 所有操作共享同一个事务
      const order = manager.create(OrderEntity, dto);
      await manager.save(order);

      // 扣减库存（同一事务）
      await manager.decrement(ProductEntity, { id: dto.productId }, 'stock', dto.quantity);

      // 创建支付记录（同一事务）
      const payment = manager.create(PaymentEntity, {
        orderId: order.id,
        amount: order.total,
      });
      await manager.save(payment);

      return order;
      // 任何一步失败 → 全部回滚
    });
  }
}

// TypeORM 事务方式 2：QueryRunner（更细粒度控制）
async createOrderWithRunner(dto: CreateOrderDto): Promise<Order> {
  const queryRunner = this.dataSource.createQueryRunner();
  await queryRunner.connect();
  await queryRunner.startTransaction();

  try {
    const order = await queryRunner.manager.save(OrderEntity, dto);
    await queryRunner.manager.decrement(ProductEntity, { id: dto.productId }, 'stock', dto.quantity);
    
    await queryRunner.commitTransaction();  // 提交
    return order;
  } catch (error) {
    await queryRunner.rollbackTransaction(); // 回滚
    throw error;
  } finally {
    await queryRunner.release();             // 释放连接
  }
}
```

**CQRS 模式**——把"读"和"写"分成不同的模型，适合复杂业务：

```
CQRS（Command Query Responsibility Segregation）：

  传统模式：
  Controller → Service → Repository（读写共用一套模型）

  CQRS 模式：
  Controller
  ├── Command（写操作）→ CommandHandler → WriteRepository
  │   CreateOrderCommand → CreateOrderHandler → OrderWriteRepo
  │
  └── Query（读操作）→ QueryHandler → ReadRepository
      GetOrderQuery → GetOrderHandler → OrderReadRepo

  好处：
  ✅ 读模型可以针对查询优化（扁平化、预聚合）
  ✅ 写模型可以包含完整的业务验证
  ✅ 读写可以独立扩展（读多写少 → 读库扩容）
```

```typescript
// NestJS 内置 CQRS 支持（@nestjs/cqrs）

// Command：定义写操作
export class CreateOrderCommand {
  constructor(
    public readonly userId: number,
    public readonly items: OrderItem[],
  ) {}
}

// CommandHandler：处理写操作
@CommandHandler(CreateOrderCommand)
export class CreateOrderHandler implements ICommandHandler<CreateOrderCommand> {
  constructor(private orderRepo: OrderRepository) {}

  async execute(command: CreateOrderCommand): Promise<Order> {
    // 业务逻辑 + 数据写入
    return this.orderRepo.create(command);
  }
}

// Controller 中使用
@Controller('orders')
export class OrderController {
  constructor(private commandBus: CommandBus, private queryBus: QueryBus) {}

  @Post()
  create(@Body() dto: CreateOrderDto, @CurrentUser() user: User) {
    return this.commandBus.execute(new CreateOrderCommand(user.id, dto.items));
  }
}
```

> 💡 **CQRS 不是银弹**——简单 CRUD 应用使用 CQRS 会过度设计。只有当读写模型差异大、业务逻辑复杂、需要事件溯源（Event Sourcing）时，才考虑引入 CQRS。

---

## 7. 请求生命周期：Middleware → Guard → Interceptor → Pipe → Filter

这是 NestJS 最重要的一章——理解请求生命周期，就理解了 NestJS 的整个请求处理架构。

### 7.1 请求生命周期全景：一张图搞懂执行顺序

```
NestJS 请求生命周期（完整流程）：

  ┌─ 请求进入 ──────────────────────────────────────────────┐
  │                                                         │
  │  1. Middleware（全局 → 模块级）                          │
  │     → 最先执行，Express 兼容                            │
  │     → 日志记录、CORS、Cookie 解析                       │
  │                                                         │
  │  2. Guard（全局 → 控制器 → 方法）                       │
  │     → 决定请求是否允许继续                               │
  │     → 认证（JWT 验证）、鉴权（角色检查）                │
  │     → 返回 true/false                                   │
  │                                                         │
  │  3. Interceptor — 前置逻辑（全局 → 控制器 → 方法）      │
  │     → 在 Controller 之前执行                            │
  │     → 日志、缓存检查、请求转换                          │
  │                                                         │
  │  4. Pipe（全局 → 控制器 → 方法 → 参数）                 │
  │     → 参数验证和转换                                     │
  │     → ValidationPipe、ParseIntPipe                      │
  │                                                         │
  │  5. Controller Method（路由处理函数）                    │
  │     → 你写的业务逻辑                                     │
  │                                                         │
  │  6. Interceptor — 后置逻辑（方法 → 控制器 → 全局）      │
  │     → 在 Controller 之后执行（反序）                    │
  │     → 响应转换、超时处理、缓存写入                      │
  │                                                         │
  │  7. ExceptionFilter（方法 → 控制器 → 全局）             │
  │     → 捕获上述任何步骤抛出的异常                        │
  │     → 格式化错误响应                                     │
  │                                                         │
  └─ 响应返回 ──────────────────────────────────────────────┘

  执行顺序口诀：
  去程：Middleware → Guard → Interceptor(前) → Pipe → Controller
  回程：Interceptor(后) → ExceptionFilter（如有异常）
```

### 7.2 Middleware：Express 兼容层

Middleware 是 NestJS 中最"底层"的拦截器——它直接操作 Express/Fastify 的 req/res 对象：

```typescript
// 函数式 Middleware（简单场景）
export function logger(req: Request, res: Response, next: NextFunction) {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();  // 必须调用 next()，否则请求会挂起
}

// 类式 Middleware（可以注入依赖）
@Injectable()
export class LoggerMiddleware implements NestMiddleware {
  constructor(private readonly loggerService: LoggerService) {}

  use(req: Request, res: Response, next: NextFunction) {
    const start = Date.now();
    
    // 响应完成后记录
    res.on('finish', () => {
      const duration = Date.now() - start;
      this.loggerService.log(
        `${req.method} ${req.url} ${res.statusCode} ${duration}ms`
      );
    });
    
    next();
  }
}
```

```typescript
// 在 Module 中注册 Middleware
@Module({})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer
      .apply(LoggerMiddleware, CorsMiddleware)  // 可以链式应用多个
      .exclude(
        { path: 'health', method: RequestMethod.GET },  // 排除健康检查
      )
      .forRoutes('*');  // 应用到所有路由
      // .forRoutes(UserController)  // 或指定控制器
      // .forRoutes({ path: 'users', method: RequestMethod.POST })  // 或指定路由
  }
}

// 全局 Middleware（在 main.ts 中）
app.use(helmet());     // Express 中间件直接可用
app.use(compression());
```

```
Middleware vs Guard/Interceptor：何时用 Middleware？

  ✅ 用 Middleware：
  → 需要 Express 中间件兼容（helmet、compression、morgan）
  → 需要操作原始 req/res 对象
  → 跟 NestJS 路由系统无关的通用处理

  ❌ 不用 Middleware：
  → 需要知道哪个路由、哪个 Controller 在处理（用 Guard）
  → 需要修改响应数据（用 Interceptor）
  → 需要验证参数（用 Pipe）
```

### 7.3 Guard：认证与鉴权的守门员

Guard 决定请求是否"被允许"继续——返回 `true` 放行，返回 `false` 或抛异常则拒绝：

```typescript
// Guard 实现 CanActivate 接口
@Injectable()
export class JwtAuthGuard implements CanActivate {
  constructor(private jwtService: JwtService) {}

  canActivate(context: ExecutionContext): boolean | Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const token = this.extractToken(request);
    
    if (!token) throw new UnauthorizedException('缺少认证令牌');

    try {
      const payload = this.jwtService.verify(token);
      request.user = payload;  // 将用户信息挂载到 request 上
      return true;             // 放行
    } catch {
      throw new UnauthorizedException('令牌无效或已过期');
    }
  }

  private extractToken(request: Request): string | null {
    const [type, token] = request.headers.authorization?.split(' ') ?? [];
    return type === 'Bearer' ? token : null;
  }
}
```

```typescript
// ExecutionContext — Guard 的"上帝视角"
// Guard 比 Middleware 强大之处：它知道请求要去哪里

canActivate(context: ExecutionContext) {
  // 获取请求处理的目标 Controller 类
  const controller = context.getClass();     // UserController

  // 获取请求处理的目标方法
  const handler = context.getHandler();      // findAll

  // 可以读取装饰器设置的元数据（配合 @Roles 等使用）
  const roles = this.reflector.get<string[]>('roles', handler);
  
  // 支持多种协议
  context.switchToHttp();      // HTTP
  context.switchToWs();        // WebSocket
  context.switchToRpc();       // 微服务
}

// 绑定方式
@UseGuards(JwtAuthGuard)              // 方法级 / 控制器级
app.useGlobalGuards(new JwtAuthGuard); // 全局级
```

### 7.4 Interceptor：AOP 切面编程利器

Interceptor 是 NestJS 中最灵活的增强器——它能在请求**前后**都插入逻辑：

```typescript
// Interceptor 的核心：intercept 方法 + CallHandler
@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const method = request.method;
    const url = request.url;
    const start = Date.now();

    console.log(`→ ${method} ${url}`);  // 前置逻辑

    return next.handle().pipe(          // next.handle() = 执行 Controller
      tap((data) => {                   // 后置逻辑（响应成功时）
        const duration = Date.now() - start;
        console.log(`← ${method} ${url} ${duration}ms`);
      }),
    );
  }
}
```

```typescript
// 实战：响应格式统一封装
@Injectable()
export class TransformInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(
      map((data) => ({
        code: 0,
        message: 'success',
        data: data,               // 统一包装为 { code, message, data }
        timestamp: new Date().toISOString(),
      })),
    );
  }
}

// 原始返回：{ id: 1, name: 'Alice' }
// 经过 Interceptor 后：
// { code: 0, message: 'success', data: { id: 1, name: 'Alice' }, timestamp: '...' }
```

```typescript
// 实战：请求超时控制
@Injectable()
export class TimeoutInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(
      timeout(5000),                    // 5 秒超时
      catchError((err) => {
        if (err instanceof TimeoutError) {
          throw new RequestTimeoutException('请求超时');
        }
        throw err;
      }),
    );
  }
}

// 绑定方式（与 Guard 相同）
@UseInterceptors(LoggingInterceptor)     // 方法级 / 控制器级
app.useGlobalInterceptors(new LoggingInterceptor); // 全局
```

### 7.5 Pipe：数据验证与转换管道

Pipe 在参数到达 Controller 方法**之前**执行——负责验证和转换：

```typescript
// NestJS 内置 Pipe（开箱即用）
@Get(':id')
findOne(
  @Param('id', ParseIntPipe) id: number,       // '42' → 42（不是数字则 400）
) {}

@Get()
findAll(
  @Query('active', ParseBoolPipe) active: boolean, // 'true' → true
  @Query('ids', ParseArrayPipe) ids: string[],     // '1,2,3' → ['1','2','3']
) {}

@Get(':uuid')
findByUuid(
  @Param('uuid', ParseUUIDPipe) uuid: string,     // 验证 UUID 格式
) {}

// 带默认值的 Pipe
@Get()
findAll(
  @Query('page', new DefaultValuePipe(1), ParseIntPipe) page: number,
  // 没传 page → 默认 1 → 转为数字
) {}
```

```typescript
// 自定义 Pipe — 文件大小验证
@Injectable()
export class FileSizeValidationPipe implements PipeTransform {
  constructor(private readonly maxSize: number) {}

  transform(value: Express.Multer.File, metadata: ArgumentMetadata) {
    if (value.size > this.maxSize) {
      throw new BadRequestException(
        `文件大小 ${value.size} 超过限制 ${this.maxSize}`
      );
    }
    return value;
  }
}

// 使用
@Post('upload')
@UseInterceptors(FileInterceptor('file'))
upload(
  @UploadedFile(new FileSizeValidationPipe(5 * 1024 * 1024))  // 5MB 限制
  file: Express.Multer.File,
) {}
```

### 7.6 ExceptionFilter：统一异常处理

ExceptionFilter 是请求管道的"兜底网"——捕获任何步骤抛出的异常并格式化响应：

```typescript
// NestJS 内置异常类（自动映射 HTTP 状态码）
throw new BadRequestException('参数错误');        // 400
throw new UnauthorizedException('未认证');        // 401
throw new ForbiddenException('无权限');           // 403
throw new NotFoundException('资源不存在');        // 404
throw new ConflictException('数据冲突');          // 409
throw new InternalServerErrorException('服务器错误'); // 500

// 自定义异常
export class BusinessException extends HttpException {
  constructor(code: string, message: string) {
    super({ code, message }, HttpStatus.BAD_REQUEST);
  }
}
throw new BusinessException('ORDER_001', '库存不足');
```

```typescript
// 自定义全局异常过滤器
@Catch()  // 捕获所有异常（不传参数 = 捕获所有）
export class AllExceptionsFilter implements ExceptionFilter {
  constructor(private readonly logger: LoggerService) {}

  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse();
    const request = ctx.getRequest();

    // 区分 HTTP 异常和未知异常
    const status = exception instanceof HttpException
      ? exception.getStatus()
      : HttpStatus.INTERNAL_SERVER_ERROR;

    const message = exception instanceof HttpException
      ? exception.getResponse()
      : '服务器内部错误';

    // 记录错误日志
    this.logger.error(`${request.method} ${request.url}`, exception);

    // 统一错误响应格式
    response.status(status).json({
      code: status,
      message: typeof message === 'string' ? message : (message as any).message,
      path: request.url,
      timestamp: new Date().toISOString(),
    });
  }
}

// 全局注册
app.useGlobalFilters(new AllExceptionsFilter(logger));
```

五大增强器对比总结：

| 增强器 | 接口 | 核心能力 | 典型用途 |
|:---|:---|:---|:---|
| **Middleware** | NestMiddleware | 操作 req/res | 日志、CORS、压缩 |
| **Guard** | CanActivate | 允许/拒绝请求 | 认证、角色鉴权 |
| **Interceptor** | NestInterceptor | 请求前后切面 | 响应封装、超时、缓存 |
| **Pipe** | PipeTransform | 验证/转换参数 | DTO 验证、类型转换 |
| **Filter** | ExceptionFilter | 捕获异常 | 统一错误格式 |

> 💡 **选择哪个增强器的决策树**：需要操作 req/res 原始对象？→ Middleware。需要决定请求能否继续？→ Guard。需要修改请求或响应数据？→ Interceptor。需要验证/转换参数？→ Pipe。需要处理错误？→ Filter。

---

## 8. 企业级认证与鉴权：从 JWT 到 RBAC

认证（Authentication）= "你是谁"，鉴权（Authorization）= "你能做什么"。这两件事是企业级应用的门槛。

### 8.1 Passport.js 集成：Strategy 模式详解

NestJS 通过 `@nestjs/passport` 集成 Passport.js——500+ 认证策略开箱即用：

```
Passport.js 的 Strategy 模式：

  Passport（统一接口）
  ├── LocalStrategy       用户名 + 密码登录
  ├── JwtStrategy         JWT 令牌验证
  ├── GoogleStrategy      Google OAuth2
  ├── GithubStrategy      GitHub OAuth2
  └── ...                 500+ 策略

  每个 Strategy 只做一件事：
  接收凭证 → 验证 → 返回用户对象（或抛异常）
```

```typescript
// Local Strategy — 用户名密码登录
@Injectable()
export class LocalStrategy extends PassportStrategy(Strategy) {
  constructor(private authService: AuthService) {
    super({ usernameField: 'email' });  // 用 email 代替 username
  }

  // validate 是 Passport 要求实现的方法
  // 返回的对象会被挂载到 request.user
  async validate(email: string, password: string): Promise<User> {
    const user = await this.authService.validateUser(email, password);
    if (!user) throw new UnauthorizedException('邮箱或密码错误');
    return user;
  }
}

// JWT Strategy — 验证已签发的 JWT
@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(private configService: ConfigService) {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: configService.get('JWT_SECRET'),
    });
  }

  // payload 是 JWT 解码后的数据
  async validate(payload: JwtPayload): Promise<User> {
    return { id: payload.sub, email: payload.email, roles: payload.roles };
    // 返回值 → request.user
  }
}
```

### 8.2 JWT 认证全流程：签发 / 验证 / 刷新

```
JWT 双令牌流程：

  登录：
  Client → POST /auth/login (email + password)
  Server → 验证密码 → 签发 accessToken (15分钟) + refreshToken (7天)
  Client ← { accessToken, refreshToken }

  请求 API：
  Client → GET /users (Header: Bearer accessToken)
  Server → JwtStrategy 验证 → 返回数据

  Token 过期后刷新：
  Client → POST /auth/refresh (refreshToken)
  Server → 验证 refreshToken → 签发新 accessToken
  Client ← { accessToken }（refreshToken 不变）
```

```typescript
// auth.service.ts — 完整的认证服务
@Injectable()
export class AuthService {
  constructor(
    private userService: UserService,
    private jwtService: JwtService,
  ) {}

  // 登录：验证密码 → 签发双令牌
  async login(email: string, password: string) {
    const user = await this.validateUser(email, password);

    const payload: JwtPayload = {
      sub: user.id,
      email: user.email,
      roles: user.roles,
    };

    return {
      accessToken: this.jwtService.sign(payload, { expiresIn: '15m' }),
      refreshToken: this.jwtService.sign(
        { sub: user.id, type: 'refresh' },
        { expiresIn: '7d' },
      ),
    };
  }

  // 刷新令牌
  async refresh(refreshToken: string) {
    try {
      const payload = this.jwtService.verify(refreshToken);
      if (payload.type !== 'refresh') throw new Error();

      const user = await this.userService.findById(payload.sub);
      return {
        accessToken: this.jwtService.sign(
          { sub: user.id, email: user.email, roles: user.roles },
          { expiresIn: '15m' },
        ),
      };
    } catch {
      throw new UnauthorizedException('刷新令牌无效');
    }
  }

  // 验证用户名密码
  async validateUser(email: string, password: string): Promise<User> {
    const user = await this.userService.findByEmail(email);
    if (!user) throw new UnauthorizedException('用户不存在');

    const isMatch = await bcrypt.compare(password, user.passwordHash);
    if (!isMatch) throw new UnauthorizedException('密码错误');

    return user;
  }
}
```

> 💡 **生产环境 JWT 最佳实践**：accessToken 有效期 ≤ 15 分钟（减少被盗风险），refreshToken 有效期 7~30 天（存 httpOnly Cookie 更安全）。refreshToken 应该存数据库/Redis，支持吊销。

### 8.3 RBAC 权限系统：@Roles + RolesGuard + Reflector

RBAC（Role-Based Access Control）在 NestJS 中只需三个组件：

```typescript
// 第 1 步：定义角色枚举
export enum Role {
  USER = 'user',
  ADMIN = 'admin',
  SUPER_ADMIN = 'super_admin',
}

// 第 2 步：@Roles 装饰器（在 2.4 中已实现）
export const ROLES_KEY = 'roles';
export const Roles = (...roles: Role[]) => SetMetadata(ROLES_KEY, roles);

// 第 3 步：RolesGuard（在 Guard 中读取元数据）
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    // 读取方法和类上的 @Roles 元数据
    const requiredRoles = this.reflector.getAllAndOverride<Role[]>(
      ROLES_KEY,
      [context.getHandler(), context.getClass()],
    );

    // 没有设置 @Roles → 公开接口，放行
    if (!requiredRoles) return true;

    const { user } = context.switchToHttp().getRequest();
    if (!user) throw new ForbiddenException('用户未认证');

    // 检查用户角色是否匹配
    const hasRole = requiredRoles.some(role => user.roles?.includes(role));
    if (!hasRole) throw new ForbiddenException('权限不足');
    return true;
  }
}

// 使用
@Controller('admin')
@UseGuards(JwtAuthGuard, RolesGuard)  // 先认证，再鉴权
export class AdminController {

  @Get('users')
  @Roles(Role.ADMIN)                  // 只有 admin 能访问
  listUsers() {}

  @Delete('users/:id')
  @Roles(Role.SUPER_ADMIN)            // 只有 super_admin 能删除
  deleteUser() {}

  @Get('dashboard')                    // 没有 @Roles → 所有认证用户可访问
  dashboard() {}
}
```

```
RBAC vs ABAC vs PBAC 权限模型对比：

  RBAC（基于角色）：
  用户 → 角色 → 权限
  简单直接，适合大多数 B2B 应用

  ABAC（基于属性）：
  用户属性 + 资源属性 + 环境属性 → 策略引擎 → 允许/拒绝
  灵活但复杂，适合细粒度权限（如"只能编辑自己部门的数据"）
  → 推荐使用 Casl 库实现

  PBAC（基于策略）：
  AWS IAM 风格的 JSON 策略文档
  最灵活但最复杂
```

### 8.4 OAuth2 第三方登录集成

```typescript
// Google OAuth2 登录
@Injectable()
export class GoogleStrategy extends PassportStrategy(Strategy, 'google') {
  constructor(private configService: ConfigService) {
    super({
      clientID: configService.get('GOOGLE_CLIENT_ID'),
      clientSecret: configService.get('GOOGLE_CLIENT_SECRET'),
      callbackURL: 'http://localhost:3000/auth/google/callback',
      scope: ['email', 'profile'],
    });
  }

  async validate(accessToken: string, refreshToken: string, profile: any) {
    // profile 包含 Google 返回的用户信息
    return {
      email: profile.emails[0].value,
      name: profile.displayName,
      avatar: profile.photos[0].value,
      provider: 'google',
      providerId: profile.id,
    };
  }
}

// Controller 路由
@Controller('auth')
export class AuthController {
  @Get('google')
  @UseGuards(AuthGuard('google'))
  googleLogin() {}  // 自动重定向到 Google 登录页

  @Get('google/callback')
  @UseGuards(AuthGuard('google'))
  googleCallback(@Req() req) {
    // req.user 是 GoogleStrategy.validate 的返回值
    // 查找或创建本地用户 → 签发 JWT
    return this.authService.socialLogin(req.user);
  }
}
```

> 💡 **OAuth2 最佳实践**：社交登录后应该关联到本地用户表（同一个 email 可能通过 Google/GitHub 登录），使用 `provider + providerId` 作为唯一标识，避免重复注册。

---

## 9. 微服务架构：从单体到分布式

NestJS 最强大的能力之一：用**同一套代码风格**写 HTTP API 和微服务——只需切换 Transport 层。

### 9.1 NestJS 微服务抽象：Transport 层设计

```
NestJS 微服务的核心设计：传输层抽象

  你的业务代码（Controller/Service）
  ────────────────────────────────
  NestJS 抽象层（@MessagePattern / @EventPattern）
  ────────────────────────────────
  Transport 传输层（可替换）
  ┌──────┬──────┬──────┬──────┬──────┐
  │ TCP  │Redis │ NATS │ RMQ  │ gRPC │
  └──────┴──────┴──────┴──────┴──────┘

  好处：换 Transport 不改业务代码
  从 TCP 换成 RabbitMQ？只改 main.ts 的配置
```

```typescript
// 创建微服务（main.ts）
import { MicroserviceOptions, Transport } from '@nestjs/microservices';

// 方式 1：纯微服务（不提供 HTTP）
async function bootstrap() {
  const app = await NestFactory.createMicroservice<MicroserviceOptions>(
    AppModule,
    {
      transport: Transport.TCP,       // 传输协议
      options: { host: '0.0.0.0', port: 3001 },
    },
  );
  await app.listen();
}

// 方式 2：Hybrid — 同时提供 HTTP + 微服务（第 9.4 节详述）
async function bootstrap() {
  const app = await NestFactory.create(AppModule);  // HTTP

  app.connectMicroservice<MicroserviceOptions>({     // 微服务
    transport: Transport.RMQ,
    options: {
      urls: ['amqp://localhost:5672'],
      queue: 'orders_queue',
    },
  });

  await app.startAllMicroservices();  // 启动微服务
  await app.listen(3000);            // 启动 HTTP
}
```

### 9.2 消息模式：@MessagePattern vs @EventPattern

NestJS 微服务有两种通信模式：

```
两种消息模式：

  @MessagePattern — 请求/响应模式（同步）
  ┌────────┐  cmd: get_user  ┌────────┐
  │ Client │ ──────────────→ │ Server │
  │        │ ←────────────── │        │
  └────────┘  response: User └────────┘
  → 客户端发送消息，等待服务端返回结果
  → 类似 HTTP 的 Request/Response

  @EventPattern — 事件模式（异步）
  ┌────────┐  event: user_created  ┌────────┐
  │ Client │ ─────────────────────→│ Server │
  │        │  （不等待响应）        │        │
  └────────┘                       └────────┘
  → 客户端发布事件，不等待响应
  → 适合异步任务：发邮件、推送通知、数据同步
```

```typescript
// 服务端：处理消息
@Controller()
export class OrderController {

  // 请求/响应模式 — 同步等待结果
  @MessagePattern({ cmd: 'get_order' })
  async getOrder(data: { orderId: number }) {
    return this.orderService.findById(data.orderId);
    // 返回值自动发送回客户端
  }

  // 事件模式 — 异步处理，无返回值
  @EventPattern('order_created')
  async handleOrderCreated(data: OrderCreatedEvent) {
    // 发送确认邮件、更新库存、通知仓库...
    await this.notificationService.sendOrderEmail(data);
    // 不需要返回值
  }
}

// 客户端：发送消息
@Injectable()
export class OrderClientService {
  constructor(
    @Inject('ORDER_SERVICE') private client: ClientProxy,
  ) {}

  // 请求/响应 — 发送并等待结果
  getOrder(orderId: number): Observable<Order> {
    return this.client.send({ cmd: 'get_order' }, { orderId });
    // .send() 返回 Observable，需要 subscribe 或 lastValueFrom
  }

  // 事件 — 发送后不等待
  notifyOrderCreated(order: Order) {
    this.client.emit('order_created', order);
    // .emit() 触发即忘（fire-and-forget）
  }
}
```

### 9.3 主流传输层实战：Redis / RabbitMQ / gRPC

```typescript
// 1️⃣ Redis Transport — 最简单的发布/订阅
// 服务端
app.connectMicroservice({
  transport: Transport.REDIS,
  options: {
    host: 'localhost',
    port: 6379,
  },
});

// 客户端注册
@Module({
  imports: [
    ClientsModule.register([{
      name: 'REDIS_SERVICE',
      transport: Transport.REDIS,
      options: { host: 'localhost', port: 6379 },
    }]),
  ],
})
// 适合：简单的服务间通信、事件广播
// 局限：消息无持久化，Redis 重启后消息丢失
```

```typescript
// 2️⃣ RabbitMQ Transport — 企业级消息队列
app.connectMicroservice({
  transport: Transport.RMQ,
  options: {
    urls: ['amqp://user:pass@rabbitmq:5672'],
    queue: 'orders_queue',
    queueOptions: {
      durable: true,     // 持久化队列（RabbitMQ 重启不丢失）
    },
    noAck: false,        // 手动确认（处理完才 ACK）
  },
});

// 适合：需要可靠投递、消息持久化、死信队列的场景
```

```typescript
// 3️⃣ gRPC Transport — 高性能 RPC（基于 Protocol Buffers）

// proto/order.proto
// syntax = "proto3";
// package order;
// service OrderService {
//   rpc FindOne (OrderById) returns (Order) {}
// }
// message OrderById { int32 id = 1; }
// message Order { int32 id = 1; string name = 2; }

app.connectMicroservice({
  transport: Transport.GRPC,
  options: {
    package: 'order',
    protoPath: join(__dirname, 'proto/order.proto'),
    url: '0.0.0.0:5000',
  },
});

// Controller 用 @GrpcMethod 替代 @MessagePattern
@Controller()
export class OrderController {
  @GrpcMethod('OrderService', 'FindOne')
  findOne(data: { id: number }): Order {
    return this.orderService.findById(data.id);
  }
}

// 适合：服务间高频 RPC 调用、跨语言通信（Go/Java/Python）
```

| Transport | 协议 | 持久化 | 性能 | 适合场景 |
|:---|:---|:---|:---|:---|
| TCP | 自有协议 | ❌ | 高 | 内网简单通信 |
| Redis | Pub/Sub | ❌ | 高 | 事件广播、缓存失效 |
| RabbitMQ | AMQP | ✅ | 中 | 可靠消息、任务队列 |
| Kafka | 自有协议 | ✅ | 极高 | 日志流、大数据管道 |
| gRPC | HTTP/2 + Protobuf | ❌ | 极高 | 跨语言 RPC、低延迟 |

### 9.4 Hybrid Application：HTTP + 微服务混合架构

实际项目中最常见的模式——同一个 NestJS 应用同时接收 HTTP 请求和微服务消息：

```typescript
// main.ts — Hybrid 应用：HTTP + RabbitMQ + gRPC
async function bootstrap() {
  // 1. 创建 HTTP 应用
  const app = await NestFactory.create(AppModule);

  // 2. 连接 RabbitMQ 微服务（异步事件）
  app.connectMicroservice<MicroserviceOptions>({
    transport: Transport.RMQ,
    options: {
      urls: [process.env.RABBITMQ_URL],
      queue: 'notifications',
    },
  });

  // 3. 连接 gRPC 微服务（内部 RPC）
  app.connectMicroservice<MicroserviceOptions>({
    transport: Transport.GRPC,
    options: {
      package: 'user',
      protoPath: join(__dirname, 'proto/user.proto'),
      url: '0.0.0.0:5000',
    },
  });

  // 4. 启动所有
  await app.startAllMicroservices();  // 启动微服务监听
  await app.listen(3000);            // 启动 HTTP 监听

  // 结果：一个进程同时处理
  // → HTTP: GET/POST /api/users
  // → RabbitMQ: 消费 notifications 队列
  // → gRPC: 响应 UserService RPC 调用
}
```

```
Hybrid 架构适用场景：

  API Gateway：
  ┌──────────────────────────────────────┐
  │        NestJS Hybrid App             │
  │                                      │
  │  HTTP (3000)     → REST API 对外     │
  │  RabbitMQ        → 接收内部事件       │
  │  gRPC (5000)     → 内部服务间 RPC    │
  └──────────────────────────────────────┘

  好处：渐进式微服务化
  → 先写单体 HTTP
  → 业务复杂后加 RabbitMQ 事件
  → 性能要求高的接口改用 gRPC
  → 始终是同一个 NestJS 项目
```

### 9.5 序列化、异常传播与服务发现

```typescript
// 微服务异常传播
// 服务端抛出的异常会通过 Transport 传递给客户端

// 服务端
@MessagePattern({ cmd: 'get_user' })
getUser(data: { id: number }) {
  const user = this.userService.findById(data.id);
  if (!user) throw new RpcException('用户不存在');  // ⚠️ 用 RpcException
  // 不要用 HttpException！微服务不是 HTTP
  return user;
}

// 客户端捕获异常
this.client.send({ cmd: 'get_user' }, { id: 999 }).pipe(
  catchError((err) => {
    // err.message = '用户不存在'
    throw new NotFoundException(err.message);  // 转换为 HTTP 异常
  }),
);
```

> 💡 **微服务渐进策略**：不要一开始就上微服务。先用 NestJS 模块化写好单体，当某个模块需要独立扩展时，再用 `connectMicroservice` 拆分——NestJS 的模块边界天然就是微服务边界。

---

## 10. 测试策略：从单元到端到端

NestJS 的依赖注入天然为测试设计——Mock 任何依赖只需一行配置。

### 10.1 测试金字塔与 NestJS 测试哲学

```
NestJS 测试金字塔：

              ┌─────┐
             │ E2E  │  少量：完整 HTTP 请求链路
            │  测试  │  → Supertest + 真实路由
           ├─────────┤
          │  集成测试  │  适量：模块间协作
         │            │  → 真实 Module + 内存数据库
        ├──────────────┤
       │   单元测试     │  大量：单个 Service/Guard
      │                │  → Mock 所有依赖
     └──────────────────┘

  NestJS 测试哲学：
  DI 让 Mock 变得极其简单
  → 不需要 monkey-patching
  → 不需要 rewire / proxyquire
  → 直接用 useValue 替换 Provider
```

### 10.2 单元测试：Mock 依赖注入的优势

```typescript
// user.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';

describe('UserService', () => {
  let service: UserService;
  let mockRepo: jest.Mocked<UserRepository>;

  beforeEach(async () => {
    // 创建测试模块——用 Mock 替换真实依赖
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UserService,
        {
          provide: UserRepository,
          useValue: {
            findByEmail: jest.fn(),
            create: jest.fn(),
            findById: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get(UserService);
    mockRepo = module.get(UserRepository);
  });

  describe('register', () => {
    it('邮箱已存在时应抛出 ConflictException', async () => {
      mockRepo.findByEmail.mockResolvedValue({ id: 1, email: 'a@b.com' } as any);

      await expect(service.register({ email: 'a@b.com', name: 'test' }))
        .rejects.toThrow(ConflictException);
      
      expect(mockRepo.findByEmail).toHaveBeenCalledWith('a@b.com');
      expect(mockRepo.create).not.toHaveBeenCalled();
    });

    it('新邮箱应成功创建用户', async () => {
      mockRepo.findByEmail.mockResolvedValue(null);
      mockRepo.create.mockResolvedValue({ id: 1, email: 'new@b.com' } as any);

      const result = await service.register({ email: 'new@b.com', name: 'test' });
      expect(result.id).toBe(1);
    });
  });
});
```

### 10.3 集成测试：真实模块 + 内存数据库

```typescript
// user.integration.spec.ts
describe('UserModule (Integration)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const module = await Test.createTestingModule({
      imports: [
        // 真实模块，但用 SQLite 内存数据库替换
        TypeOrmModule.forRoot({
          type: 'sqlite',
          database: ':memory:',
          entities: [UserEntity],
          synchronize: true,
        }),
        UserModule,
      ],
    }).compile();

    app = module.createNestApplication();
    app.useGlobalPipes(new ValidationPipe());
    await app.init();
  });

  afterAll(() => app.close());

  it('完整的创建 → 查询流程', async () => {
    const userService = app.get(UserService);
    const user = await userService.register({
      email: 'test@example.com', name: 'Test',
    });
    const found = await userService.findById(user.id);
    expect(found.email).toBe('test@example.com');
  });
});
```

### 10.4 E2E 测试：Supertest + 完整请求链路

```typescript
// test/app.e2e-spec.ts
describe('AppController (E2E)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const module = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = module.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ whitelist: true }));
    await app.init();
  });

  it('POST /users → 201', () => {
    return request(app.getHttpServer())
      .post('/users')
      .send({ name: 'Alice', email: 'alice@test.com', age: 25 })
      .expect(201)
      .expect((res) => {
        expect(res.body.data.name).toBe('Alice');
      });
  });

  it('POST /users 参数验证失败 → 400', () => {
    return request(app.getHttpServer())
      .post('/users')
      .send({ name: 'A' })  // name 太短，缺少 email
      .expect(400);
  });
});
```

> 💡 **测试策略建议**：Service 层写单元测试（覆盖业务逻辑分支），核心业务流程写集成测试（验证模块协作），关键 API 写 E2E 测试（验证完整请求链路）。目标覆盖率：Service > 80%，Controller 用 E2E 覆盖即可。

---

## 11. 生产部署与可观测性

从开发到生产的跨越——配置隔离、日志收集、健康检查、优雅关闭。

### 11.1 配置管理：@nestjs/config + 多环境隔离

```typescript
// app.module.ts — 配置模块注册
@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,               // 全局可用
      envFilePath: [
        `.env.${process.env.NODE_ENV}`,  // 优先加载环境特定文件
        '.env',                          // 兜底默认
      ],
      validationSchema: Joi.object({     // 环境变量校验
        NODE_ENV: Joi.string().valid('development', 'production', 'test'),
        PORT: Joi.number().default(3000),
        DATABASE_URL: Joi.string().required(),
        JWT_SECRET: Joi.string().min(32).required(),
        REDIS_URL: Joi.string().required(),
      }),
    }),
  ],
})

// 使用
@Injectable()
export class AppService {
  constructor(private config: ConfigService) {}

  getPort(): number {
    return this.config.get<number>('PORT');
  }
}

// 类型安全的配置（推荐）
// config/database.config.ts
export default registerAs('database', () => ({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT, 10) || 5432,
  name: process.env.DB_NAME,
}));

// 注入命名空间配置
constructor(
  @Inject(databaseConfig.KEY)
  private dbConfig: ConfigType<typeof databaseConfig>,
) {}
```

### 11.2 结构化日志：Pino / Winston 集成

```typescript
// 推荐 Pino — 比 Winston 快 5 倍，JSON 输出便于 ELK 采集
import { LoggerModule } from 'nestjs-pino';

@Module({
  imports: [
    LoggerModule.forRoot({
      pinoHttp: {
        level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
        transport: process.env.NODE_ENV !== 'production'
          ? { target: 'pino-pretty' }   // 开发环境美化输出
          : undefined,                   // 生产环境 JSON 输出
        redact: ['req.headers.authorization'],  // 脱敏
      },
    }),
  ],
})

// 生产环境日志输出示例：
// {"level":30,"time":1715000000,"msg":"GET /users 200 12ms","req":{"method":"GET","url":"/users"},"res":{"statusCode":200},"responseTime":12}
// → 直接可被 ELK / Loki / CloudWatch 解析
```

### 11.3 健康检查与 Prometheus 指标暴露

```typescript
// @nestjs/terminus — 健康检查端点
@Controller('health')
export class HealthController {
  constructor(
    private health: HealthCheckService,
    private db: TypeOrmHealthIndicator,
    private redis: MicroserviceHealthIndicator,
    private disk: DiskHealthIndicator,
    private memory: MemoryHealthIndicator,
  ) {}

  @Get()
  @HealthCheck()
  check() {
    return this.health.check([
      () => this.db.pingCheck('database'),           // 数据库连通性
      () => this.memory.checkHeap('memory', 300 * 1024 * 1024),  // 堆内存 < 300MB
      () => this.disk.checkStorage('disk', {
        path: '/', thresholdPercent: 0.9,            // 磁盘使用 < 90%
      }),
    ]);
  }
}
// GET /health → { status: 'ok', info: { database: { status: 'up' } } }
// K8s livenessProbe / readinessProbe 指向此端点
```

### 11.4 Docker 部署与优雅关闭

```dockerfile
# 多阶段构建（生产级 Dockerfile）
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

# 非 root 用户运行（安全最佳实践）
USER node
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

```typescript
// main.ts — 优雅关闭（Graceful Shutdown）
async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // 启用优雅关闭（监听 SIGTERM / SIGINT）
  app.enableShutdownHooks();

  await app.listen(3000);
}

// 在 Service 中响应关闭事件
@Injectable()
export class DatabaseService implements OnModuleDestroy {
  async onModuleDestroy() {
    // 应用关闭时：
    // 1. 停止接收新请求
    // 2. 等待正在处理的请求完成
    // 3. 关闭数据库连接
    await this.connection.close();
    console.log('数据库连接已关闭');
  }
}
```

> 💡 **K8s 部署要点**：`enableShutdownHooks()` + `terminationGracePeriodSeconds: 30`，确保 Pod 被终止时有足够时间完成进行中的请求。健康检查端点配合 `livenessProbe` 和 `readinessProbe` 实现零停机部署。

---

## 12. 企业级项目实战：从零搭建完整工程

用前面 11 章的知识，搭建一个可直接用于生产的 NestJS 项目骨架。

### 12.1 项目脚手架：Monorepo + 分层架构

```bash
# NestJS 官方 CLI 创建 Monorepo
nest new my-enterprise-app
cd my-enterprise-app

# 转换为 Monorepo 模式
nest generate app api-gateway        # HTTP API 服务
nest generate app notification-service  # 通知微服务
nest generate lib common             # 共享库（DTO/Entity/工具）
```

```
Monorepo 目录结构：

  my-enterprise-app/
  ├── apps/
  │   ├── api-gateway/           HTTP API 服务
  │   │   └── src/
  │   │       ├── main.ts
  │   │       └── app.module.ts
  │   └── notification-service/  通知微服务
  │       └── src/
  │           ├── main.ts
  │           └── app.module.ts
  ├── libs/
  │   └── common/                共享库
  │       └── src/
  │           ├── dto/           共享 DTO
  │           ├── entities/      共享 Entity
  │           ├── interfaces/    共享接口
  │           └── utils/         共享工具
  ├── nest-cli.json              Monorepo 配置
  └── tsconfig.json              路径别名
```

### 12.2 核心模块搭建：Auth / Config / Logger / Database

```typescript
// core.module.ts — 一次性注册所有基础设施
@Global()
@Module({
  imports: [
    // 配置管理
    ConfigModule.forRoot({ isGlobal: true, envFilePath: ['.env'] }),

    // 数据库
    TypeOrmModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        type: 'postgres',
        url: config.get('DATABASE_URL'),
        autoLoadEntities: true,   // 自动加载 Entity
        synchronize: false,        // 生产环境关闭！
      }),
    }),

    // JWT 认证
    JwtModule.registerAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        secret: config.get('JWT_SECRET'),
        signOptions: { expiresIn: '15m' },
      }),
    }),

    // 日志
    LoggerModule.forRoot({ pinoHttp: { level: 'info' } }),

    // 缓存
    CacheModule.registerAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        store: redisStore,
        url: config.get('REDIS_URL'),
        ttl: 60,
      }),
    }),
  ],
  providers: [LoggerService, AuthService],
  exports: [LoggerService, AuthService, JwtModule],
})
export class CoreModule {}
```

### 12.3 业务模块模板：CRUD 生成器 + DTO 规范

```bash
# NestJS CLI 一键生成 CRUD 模块
nest generate resource modules/user --no-spec
# 自动生成：
# → user.module.ts
# → user.controller.ts（含完整 CRUD 路由）
# → user.service.ts
# → dto/create-user.dto.ts
# → dto/update-user.dto.ts
# → entities/user.entity.ts
```

```typescript
// 企业级 main.ts 完整配置
async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    bufferLogs: true,  // 缓存启动日志
  });

  // 全局前缀
  app.setGlobalPrefix('api/v1');

  // 全局管道（参数验证）
  app.useGlobalPipes(new ValidationPipe({
    whitelist: true,
    forbidNonWhitelisted: true,
    transform: true,
  }));

  // 全局拦截器（响应格式）
  app.useGlobalInterceptors(new TransformInterceptor());

  // 全局异常过滤器
  app.useGlobalFilters(new AllExceptionsFilter());

  // CORS
  app.enableCors({ origin: process.env.CORS_ORIGIN });

  // 优雅关闭
  app.enableShutdownHooks();

  // Swagger 文档
  const config = new DocumentBuilder()
    .setTitle('Enterprise API')
    .setVersion('1.0')
    .addBearerAuth()
    .build();
  SwaggerModule.setup('docs', app, SwaggerModule.createDocument(app, config));

  // 启动
  const port = process.env.PORT || 3000;
  await app.listen(port);
  console.log(`🚀 Server running on http://localhost:${port}`);
  console.log(`📚 Docs available at http://localhost:${port}/docs`);
}
bootstrap();
```

### 12.4 CI/CD 与最佳实践清单

```
NestJS 企业级最佳实践清单：

  架构
  ✅ 三层模块架构：Core / Shared / Feature
  ✅ Thin Controller + Fat Service
  ✅ Repository 模式封装数据访问
  ✅ DTO 验证 + whitelist 防护

  安全
  ✅ JWT 双令牌（accessToken + refreshToken）
  ✅ RBAC 角色权限控制
  ✅ helmet + CORS + rate-limit
  ✅ 参数验证 + SQL 注入防护（ORM）

  可维护
  ✅ 统一异常格式（AllExceptionsFilter）
  ✅ 统一响应格式（TransformInterceptor）
  ✅ 结构化日志（Pino JSON）
  ✅ 配置校验（Joi）

  部署
  ✅ 多阶段 Docker 构建
  ✅ 健康检查端点
  ✅ 优雅关闭（enableShutdownHooks）
  ✅ 环境变量隔离

  测试
  ✅ 单元测试覆盖 Service 层
  ✅ E2E 测试覆盖关键 API
  ✅ CI 流水线自动运行测试
```

> 💡 **最后的忠告**：NestJS 的强大不在于它的功能多，而在于它**用约定和约束统一了 Node.js 后端的工程标准**。不要试图绕过它的约定——拥抱 Module/Provider/Controller 三件套，你的代码就会自然地变得可测试、可维护、可扩展。
