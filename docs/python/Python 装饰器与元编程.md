# Python 装饰器与元编程

> 从 `@property` 背后的魔法到自己手写 ORM 框架——用最直觉的方式搞懂装饰器、描述符、元类，真正理解「Python 是如何构建自己」的。

---

## 1. 装饰器的本质：函数即对象

在 Python 社区有句老话：**"一切皆对象"**。数字是对象、字符串是对象、列表是对象——**函数也是对象**。理解这一点，是搞懂装饰器的第一步，也是理解整个 Python 元编程体系的地基。

### 1.1 一切皆对象：函数也不例外

在 C/Java 里，函数就是函数，数据就是数据，两者泾渭分明。但在 Python 中，函数和整数 `42`、字符串 `"hello"` 没有本质区别——它们都是**对象**，都有类型、有属性、可以被赋值给变量、可以作为参数传递。

```python
def greet(name):
    """一个普通的问候函数"""
    return f"Hello, {name}!"

# 函数是对象，有类型
print(type(greet))       # <class 'function'>

# 函数是对象，有属性
print(greet.__name__)    # 'greet'
print(greet.__doc__)     # '一个普通的问候函数'

# 函数可以赋值给变量（像赋值整数一样自然）
say_hi = greet           # 没有括号！赋值的是函数对象本身，不是调用结果
print(say_hi("World"))   # Hello, World!

# 函数可以放进列表、字典
operations = [greet, len, print]
for op in operations:
    print(op.__name__, type(op))
# greet <class 'function'>
# len <class 'builtin_function_or_method'>
# print <class 'builtin_function_or_method'>
```

**关键区别：`greet` vs `greet()`**

```
greet       → 函数对象本身（一个"东西"）
greet()     → 调用函数，执行代码，拿到返回值

类比：
greet       → 菜谱（一张纸）
greet()     → 按菜谱做菜（执行动作）
```

> 💡 **为什么这很重要？** 因为装饰器的核心操作就是：接收一个函数对象，返回一个新的函数对象。如果函数不是对象，这整件事就无从谈起。

### 1.2 高阶函数与闭包

既然函数是对象，那自然可以做两件事：
1. **作为参数**传给另一个函数
2. **作为返回值**从另一个函数返回

能做到这两件事中任意一件的函数，就叫**高阶函数 (Higher-Order Function)**。

#### 函数作为参数

```python
def apply(func, value):
    """接收一个函数和一个值，把函数应用到值上"""
    return func(value)

# 传入不同的函数，得到不同的结果
print(apply(abs, -42))        # 42
print(apply(str.upper, "hi")) # HI
print(apply(len, [1, 2, 3]))  # 3
```

Python 内置的 `map()`、`filter()`、`sorted()` 都是高阶函数——它们接收一个函数作为参数来决定"怎么做"：

```python
# sorted 接收 key 函数来决定排序规则
names = ["Alice", "bob", "Charlie"]
print(sorted(names, key=str.lower))  # ['Alice', 'bob', 'Charlie']

# map 把函数应用到每个元素上
print(list(map(len, names)))         # [5, 3, 7]
```

#### 函数作为返回值 → 闭包诞生

当一个函数**返回另一个函数**，并且返回的函数**引用了外层函数的变量**，就形成了**闭包 (Closure)**。

```python
def make_multiplier(factor):
    """返回一个乘法函数（闭包）"""
    def multiplier(x):
        return x * factor  # 引用了外层的 factor 变量
    return multiplier      # 返回函数对象，不是调用结果

# 创建两个不同的乘法器
double = make_multiplier(2)   # factor=2 被"记住"了
triple = make_multiplier(3)   # factor=3 被"记住"了

print(double(5))   # 10
print(triple(5))   # 15
print(double(10))  # 20
```

**闭包的"记忆"机制：**

```
make_multiplier(2) 执行完毕后：
  - make_multiplier 的局部变量 factor=2 本应销毁
  - 但是 multiplier 函数引用了 factor
  - Python 把 factor 打包进了 multiplier 的 __closure__ 属性
  - 所以 factor=2 一直被"记住"，不会被回收
```

你可以亲手验证这个"记忆"：

```python
print(double.__closure__)           # (<cell at 0x...: int object at 0x...>,)
print(double.__closure__[0].cell_contents)  # 2 ← factor 的值被存在这里
print(triple.__closure__[0].cell_contents)  # 3
```

> 💡 **闭包 = 函数 + 它引用的外层变量**。理解闭包，就理解了装饰器的 90%——因为装饰器本质上就是一个返回闭包的高阶函数。

| 概念 | 说明 | 示例 |
|:---|:---|:---|
| **一等公民** | 函数可以赋值、传参、返回 | `say_hi = greet` |
| **高阶函数** | 接收或返回函数的函数 | `sorted(key=len)` |
| **闭包** | 内层函数 + 对外层变量的引用 | `make_multiplier(2)` 返回的 `multiplier` |

### 1.3 手搓第一个装饰器：从闭包到 @

有了闭包的基础，装饰器就水到渠成了。**装饰器 = 一个接收函数、返回新函数的高阶函数。**

假设你有一堆函数，想在每个函数执行前后打印日志。最笨的办法是每个函数里都加 `print`，但这违反了 DRY 原则（Don't Repeat Yourself）。更优雅的做法是——写一个装饰器。

```python
def log_calls(func):
    """
    装饰器：在函数执行前后打印日志
    
    参数：func — 被装饰的原始函数（一个函数对象）
    返回：wrapper — 一个包装后的新函数（闭包）
    """
    def wrapper(*args, **kwargs):
        print(f"📥 调用 {func.__name__}，参数: args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)  # 调用原始函数
        print(f"📤 {func.__name__} 返回: {result}")
        return result
    return wrapper  # 返回包装后的函数

# ──────────────────────────────────────────
# 手动使用装饰器（不用 @ 语法糖）
# ──────────────────────────────────────────
def add(a, b):
    return a + b

add = log_calls(add)  # 关键！把原函数替换成"包装版"

add(3, 5)
# 📥 调用 add，参数: args=(3, 5), kwargs={}
# 📤 add 返回: 8
```

**拆解执行过程：**

```
1. log_calls(add) 被调用
   - func = add（原始函数被"记住"在闭包里）
   - 返回 wrapper 函数

2. add = log_calls(add)
   - 变量名 add 现在指向 wrapper（不再是原始 add）

3. add(3, 5) 实际上调用的是 wrapper(3, 5)
   - wrapper 先打印日志
   - 然后调用 func(3, 5)（也就是原始的 add）
   - 再打印返回值
   - 最后把结果返回
```

**注意 `*args, **kwargs` 的作用**：让 `wrapper` 能接受任意参数，这样不管被装饰的函数签名是什么，装饰器都能通用。

```python
# 同一个装饰器，用在不同签名的函数上
@log_calls
def greet(name):
    return f"Hello, {name}!"

@log_calls
def power(base, exp, mod=None):
    return pow(base, exp, mod)

greet("Python")
# 📥 调用 greet，参数: args=('Python',), kwargs={}
# 📤 greet 返回: Hello, Python!

power(2, 10, mod=1000)
# 📥 调用 power，参数: args=(2, 10), kwargs={'mod': 1000}
# 📤 power 返回: 24
```

> 💡 **装饰器的核心模式就三步**：① 接收原函数 → ② 在闭包里增强功能 → ③ 返回新函数。后面所有花哨的装饰器都是这个模式的变体。

### 1.4 @语法糖的脱糖过程

上一节你已经用过 `@log_calls` 了。现在让我们彻底搞清楚 `@` 到底做了什么——它只是一个**语法糖 (Syntactic Sugar)**，Python 解释器会把它翻译成完全等价的代码。

**脱糖规则（记住这一个就够了）：**

```python
# ════════════════════════════════════════════
# @ 语法糖写法
# ════════════════════════════════════════════
@decorator
def func():
    pass

# ════════════════════════════════════════════
# 等价的"脱糖"写法（Python 解释器实际执行的）
# ════════════════════════════════════════════
def func():
    pass
func = decorator(func)  # 就这么简单！
```

**重点理解**：`@decorator` 放在函数定义上面，意思就是——定义完函数后，立刻把函数传给 `decorator`，然后用返回值**覆盖**原来的函数名。

让我们用实际代码验证这个"脱糖"过程：

```python
def uppercase(func):
    """装饰器：把函数的字符串返回值变为大写"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, str):
            return result.upper()
        return result
    return wrapper

# 写法一：@ 语法糖
@uppercase
def greet_v1(name):
    return f"hello, {name}"

# 写法二：手动调用（完全等价）
def greet_v2(name):
    return f"hello, {name}"
greet_v2 = uppercase(greet_v2)

# 两种写法结果完全一样
print(greet_v1("python"))  # HELLO, PYTHON
print(greet_v2("python"))  # HELLO, PYTHON
```

**多个装饰器叠加的脱糖：**

```python
@decorator_a
@decorator_b
@decorator_c
def func():
    pass

# 脱糖后（注意顺序：从下往上包装）：
func = decorator_a(decorator_b(decorator_c(func)))
```

这就像套娃：先用 `decorator_c` 包一层，再用 `decorator_b` 包一层，最后用 `decorator_a` 包最外面一层。**执行时从外往里调用，定义时从下往上包装。**

```
包装顺序（定义时）：   c → b → a（从下往上）
执行顺序（调用时）：   a → b → c → 原函数 → c → b → a（从外往里，再从里往外）
```

> 💡 **记住一句话**：`@` 不是什么神秘的语法，它就是 `func = decorator(func)` 的简写。搞懂这一点，你就不再会对任何装饰器感到困惑——不管它看起来多复杂，本质都是「用一个函数处理另一个函数」。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **函数是对象** | 函数可以赋值、传参、作为返回值，和整数没区别 |
| **高阶函数** | 接收函数作为参数，或返回函数的函数 |
| **闭包** | 内层函数 + 它"记住"的外层变量 |
| **装饰器** | 接收一个函数，返回一个增强版函数的高阶函数 |
| **@ 语法糖** | `@dec` 就是 `func = dec(func)` 的简写 |

---

## 2. 装饰器实战：从玩具到生产级

上一章你已经能写出一个基本的装饰器了。但那还只是"玩具级"——在真实项目中使用装饰器，有几个**必须解决的问题**：被装饰函数的身份丢失、如何给装饰器传参数、如何用类来实现装饰器。解决了这些，你的装饰器才算"生产可用"。

### 2.1 functools.wraps：保护被装饰函数的身份

回顾上一章的 `log_calls` 装饰器，它有一个**隐藏 bug**：

```python
def log_calls(func):
    def wrapper(*args, **kwargs):
        print(f"📥 调用 {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log_calls
def add(a, b):
    """两数相加"""
    return a + b

# 问题来了：
print(add.__name__)  # 'wrapper' ← 不是 'add'！
print(add.__doc__)   # None     ← 文档字符串丢了！
help(add)            # Help on function wrapper... ← 完全乱了
```

**原因很简单**：`@log_calls` 之后，`add` 这个变量指向的是 `wrapper` 函数。`wrapper` 的 `__name__` 当然是 `'wrapper'`，它不知道自己是 `add` 的替身。

**解决方案：`functools.wraps`**

```python
import functools

def log_calls(func):
    @functools.wraps(func)  # ← 这一行解决所有问题
    def wrapper(*args, **kwargs):
        print(f"📥 调用 {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log_calls
def add(a, b):
    """两数相加"""
    return a + b

print(add.__name__)  # 'add'    ✅ 身份恢复了
print(add.__doc__)   # '两数相加' ✅ 文档也在
```

**`functools.wraps(func)` 做了什么？** 它把原函数 `func` 的这些属性复制到 `wrapper` 上：

| 属性 | 说明 |
|:---|:---|
| `__name__` | 函数名 |
| `__doc__` | 文档字符串 |
| `__module__` | 所属模块 |
| `__qualname__` | 完整限定名 |
| `__annotations__` | 类型注解 |
| `__dict__` | 自定义属性 |
| `__wrapped__` | **指向原始函数**（可以绕过装饰器直接调用） |

最后一个 `__wrapped__` 特别有用——它让你随时可以访问"未装饰"的原始函数：

```python
# 通过 __wrapped__ 直接调用原始函数（跳过装饰器）
print(add.__wrapped__(3, 5))  # 8（没有日志输出）
```

> 💡 **铁律：每个装饰器的 wrapper 函数上面都要加 `@functools.wraps(func)`。** 这不是可选的，这是必须的。不加它，调试、文档生成、测试框架全会出问题。

### 2.2 带参数的装饰器（三层嵌套）

到目前为止，我们的装饰器都是"一刀切"——要么打日志，要么不打。但如果你想**控制装饰器的行为**呢？比如：

```python
@retry(max_attempts=3, delay=1.0)   # 重试 3 次，每次间隔 1 秒
def fetch_data():
    ...

@cache(ttl=300)                      # 缓存 5 分钟
def get_user(user_id):
    ...
```

这就需要**带参数的装饰器**——它的结构是**三层嵌套函数**。

先看代码，再分析为什么要三层：

```python
import functools
import time

def retry(max_attempts=3, delay=1.0):
    """
    带参数的重试装饰器
    
    第 1 层：接收装饰器参数（max_attempts, delay）
    第 2 层：接收被装饰的函数（func）
    第 3 层：接收函数调用时的参数（*args, **kwargs）
    """
    def decorator(func):                    # 第 2 层
        @functools.wraps(func)
        def wrapper(*args, **kwargs):       # 第 3 层
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        print(f"⚠️ {func.__name__} 第{attempt}次失败: {e}")
                        print(f"   {delay}秒后重试...")
                        time.sleep(delay)
            raise last_exception            # 全部失败，抛出最后的异常
        return wrapper
    return decorator                        # 第 1 层返回「真正的装饰器」

# 使用
@retry(max_attempts=3, delay=0.5)
def unreliable_api():
    """模拟一个不稳定的 API"""
    import random
    if random.random() < 0.7:  # 70% 概率失败
        raise ConnectionError("网络不稳定")
    return "成功！"

print(unreliable_api())
```

**为什么是三层？脱糖分析：**

```python
# 这一行：
@retry(max_attempts=3, delay=0.5)
def unreliable_api():
    ...

# 脱糖后等价于：
def unreliable_api():
    ...
unreliable_api = retry(max_attempts=3, delay=0.5)(unreliable_api)

# 拆成两步理解：
step1 = retry(max_attempts=3, delay=0.5)  # 返回 decorator 函数
step2 = step1(unreliable_api)              # 返回 wrapper 函数
unreliable_api = step2                     # 用 wrapper 替换原函数
```

```
三层嵌套的角色分工：

retry(max_attempts=3)     → 第 1 层：接收「配置参数」，返回装饰器
  └─ decorator(func)      → 第 2 层：接收「被装饰的函数」，返回包装函数
      └─ wrapper(*args)   → 第 3 层：接收「函数调用参数」，执行增强逻辑
```

> 💡 **记忆口诀**：无参装饰器两层嵌套（接收函数 → 返回包装），有参装饰器三层嵌套（接收参数 → 接收函数 → 返回包装）。三层看着吓人，但每一层的职责是清晰的。

### 2.3 用类实现装饰器

除了用函数写装饰器，你还可以**用类来写**。核心机制是 `__call__` 魔术方法——让一个类的实例可以像函数一样被调用。

```python
class CountCalls:
    """
    用类实现的装饰器：统计函数被调用了多少次
    
    为什么用类？因为需要维护状态（调用次数），
    用类比用闭包更清晰、更易扩展。
    """
    def __init__(self, func):
        functools.update_wrapper(self, func)  # 等价于 @functools.wraps
        self.func = func
        self.call_count = 0   # 状态：调用次数
    
    def __call__(self, *args, **kwargs):
        """实例被当作函数调用时触发"""
        self.call_count += 1
        print(f"📊 {self.func.__name__} 已被调用 {self.call_count} 次")
        return self.func(*args, **kwargs)

@CountCalls
def say_hello(name):
    return f"Hello, {name}!"

say_hello("Alice")   # 📊 say_hello 已被调用 1 次
say_hello("Bob")     # 📊 say_hello 已被调用 2 次
say_hello("Charlie") # 📊 say_hello 已被调用 3 次

# 随时可以查看调用次数
print(f"总共调用了 {say_hello.call_count} 次")  # 3
```

**脱糖过程**：`@CountCalls` 等价于 `say_hello = CountCalls(say_hello)`。所以 `say_hello` 现在是一个 `CountCalls` 实例，调用 `say_hello("Alice")` 实际上触发的是 `CountCalls.__call__("Alice")`。

**带参数的类装饰器怎么写？**

```python
import functools

class Retry:
    """带参数的类装饰器"""
    def __init__(self, max_attempts=3, delay=1.0):
        # __init__ 接收装饰器参数（不是 func！）
        self.max_attempts = max_attempts
        self.delay = delay
    
    def __call__(self, func):
        # __call__ 接收被装饰的函数
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            for attempt in range(1, self.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == self.max_attempts:
                        raise
                    time.sleep(self.delay)
        return wrapper

@Retry(max_attempts=5, delay=0.5)  # 创建 Retry 实例 → 调用实例的 __call__
def fetch_data():
    ...
```

**函数装饰器 vs 类装饰器选择指南：**

| 场景 | 推荐方式 | 理由 |
|:---|:---|:---|
| 简单的前后增强（日志、计时） | 函数装饰器 | 代码更简洁 |
| 需要维护状态（计数、缓存） | 类装饰器 | 状态管理更清晰 |
| 需要暴露额外方法/属性 | 类装饰器 | 类天然支持方法和属性 |
| 带参数的装饰器 | 都行 | 函数用三层嵌套，类用 `__init__` + `__call__` |

### 2.4 实战案例：计时器、重试、缓存、权限检查

下面给出四个在真实项目中**高频使用**的装饰器模板，你可以直接复制到自己的项目中。

#### ⏱️ 计时器装饰器

```python
import functools
import time

def timer(func):
    """测量函数执行时间"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"⏱️ {func.__name__} 耗时 {elapsed:.4f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1.5)
    return "done"

slow_function()  # ⏱️ slow_function 耗时 1.5012s
```

#### 🔄 缓存装饰器（带过期时间）

```python
import functools
import time

def cache(ttl=60):
    """
    带过期时间的缓存装饰器
    ttl: 缓存存活时间（秒）
    """
    def decorator(func):
        _cache = {}  # {参数组合: (结果, 过期时间)}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 用参数作为缓存的 key
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            
            # 检查缓存是否存在且未过期
            if key in _cache:
                result, expire_at = _cache[key]
                if now < expire_at:
                    print(f"💾 命中缓存: {func.__name__}")
                    return result
            
            # 未命中 → 执行函数并缓存结果
            result = func(*args, **kwargs)
            _cache[key] = (result, now + ttl)
            return result
        
        # 暴露清除缓存的方法
        wrapper.clear_cache = lambda: _cache.clear()
        return wrapper
    return decorator

@cache(ttl=300)  # 缓存 5 分钟
def get_user_profile(user_id):
    """模拟耗时的数据库查询"""
    print(f"🔍 查询数据库: user_id={user_id}")
    return {"id": user_id, "name": "Alice"}

get_user_profile(42)  # 🔍 查询数据库（首次查询）
get_user_profile(42)  # 💾 命中缓存（第二次直接返回）
get_user_profile.clear_cache()  # 手动清除缓存
```

> 💡 实际项目中，简单缓存可以直接用 `@functools.lru_cache(maxsize=128)` 或 Python 3.9+ 的 `@functools.cache`。上面的实现是为了演示缓存装饰器的原理，以及如何添加 TTL 过期机制。

#### 🔐 权限检查装饰器

```python
import functools

def require_role(*allowed_roles):
    """
    权限检查装饰器（常用于 Web 框架）
    
    用法: @require_role("admin", "editor")
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(user, *args, **kwargs):
            if user.get("role") not in allowed_roles:
                raise PermissionError(
                    f"🚫 权限不足: {user.get('role')} 不在 {allowed_roles} 中"
                )
            return func(user, *args, **kwargs)
        return wrapper
    return decorator

@require_role("admin", "editor")
def delete_post(user, post_id):
    print(f"🗑️ {user['name']} 删除了文章 {post_id}")

admin = {"name": "Alice", "role": "admin"}
viewer = {"name": "Bob", "role": "viewer"}

delete_post(admin, 42)   # 🗑️ Alice 删除了文章 42
delete_post(viewer, 42)  # PermissionError: 🚫 权限不足
```

**第 2 章核心模式速查表：**

| 模式 | 结构 | 使用场景 |
|:---|:---|:---|
| 基础装饰器 | 两层嵌套 + `@wraps` | 日志、计时、权限 |
| 带参数装饰器 | 三层嵌套 | 可配置的重试、缓存、限流 |
| 类装饰器 | `__init__` + `__call__` | 需要维护状态（计数器、连接池） |
| `@functools.wraps` | 必须在 wrapper 上添加 | 保持函数身份、支持 `__wrapped__` |

---

## 3. 装饰器进阶：多层叠加与装饰器工厂

在真实项目中，你经常会看到多个装饰器叠加在一个函数上。理解它们的执行顺序至关重要，否则你会在调试时抓狂。这一章还会介绍"装饰器工厂"模式——动态生成装饰器的高级技巧。

### 3.1 多层装饰器的执行顺序：由下往上包装

在第 1 章我们简单提过多层装饰器的脱糖。现在用一个可视化的例子来**彻底搞清楚**执行顺序。

```python
import functools

def decorator_a(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("  → 进入 A")
        result = func(*args, **kwargs)
        print("  ← 离开 A")
        return result
    print(f"🔧 A 包装了 {func.__name__}")
    return wrapper

def decorator_b(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("  → 进入 B")
        result = func(*args, **kwargs)
        print("  ← 离开 B")
        return result
    print(f"🔧 B 包装了 {func.__name__}")
    return wrapper

def decorator_c(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("  → 进入 C")
        result = func(*args, **kwargs)
        print("  ← 离开 C")
        return result
    print(f"🔧 C 包装了 {func.__name__}")
    return wrapper

@decorator_a
@decorator_b
@decorator_c
def hello():
    print("  ★ 执行 hello")
```

**定义阶段输出（包装顺序）：**

```
🔧 C 包装了 hello        ← 最靠近 def 的先执行
🔧 B 包装了 wrapper       ← B 包装的是 C 返回的 wrapper
🔧 A 包装了 wrapper       ← A 包装的是 B 返回的 wrapper
```

**调用阶段输出：**

```python
hello()
```

```
  → 进入 A                ← 最外层先执行
  → 进入 B
  → 进入 C
  ★ 执行 hello            ← 原始函数
  ← 离开 C                ← 从里往外返回
  ← 离开 B
  ← 离开 A
```

**用一张图理解：**

```
包装顺序（定义时，从下往上）：
┌─────────────────────────────┐
│  @decorator_a               │ ← 第 3 步：最外层
│  ┌─────────────────────┐    │
│  │  @decorator_b        │    │ ← 第 2 步：中间层
│  │  ┌──────────────┐    │    │
│  │  │  @decorator_c  │    │    │ ← 第 1 步：最内层
│  │  │  def hello()   │    │    │
│  │  └──────────────┘    │    │
│  └─────────────────────┘    │
└─────────────────────────────┘

调用顺序（执行时，从外往里，再从里往外）：
A → B → C → hello() → C → B → A
```

> 💡 **类比俄罗斯套娃**：最先包上去的（C）离原函数最近，最后包上去的（A）在最外面。调用时先碰到最外面的 A，一层层拆到最里面的原函数。

### 3.2 装饰器工厂：动态生成装饰器

有时候你需要根据不同的**运行时条件**来决定应用哪种装饰行为。这时可以写一个"工厂函数"来动态生成装饰器。

```python
import functools
import time
import logging

def create_logger_decorator(level="info", include_args=True, include_time=True):
    """
    装饰器工厂：根据参数动态生成不同配置的日志装饰器
    
    - level: 日志级别（"info" / "debug" / "warning"）
    - include_args: 是否记录函数参数
    - include_time: 是否记录执行时间
    """
    # 根据 level 选择 logging 方法
    log_func = getattr(logging, level, logging.info)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 构建日志信息
            msg_parts = [f"调用 {func.__name__}"]
            
            if include_args:
                msg_parts.append(f"参数: {args}, {kwargs}")
            
            start = time.perf_counter() if include_time else None
            
            result = func(*args, **kwargs)
            
            if include_time:
                elapsed = time.perf_counter() - start
                msg_parts.append(f"耗时: {elapsed:.4f}s")
            
            log_func(" | ".join(msg_parts))
            return result
        return wrapper
    return decorator

# ──────────────────────────────────────────
# 根据不同场景，生成不同配置的装饰器
# ──────────────────────────────────────────

# 开发环境：详细日志
dev_log = create_logger_decorator(level="debug", include_args=True, include_time=True)

# 生产环境：简洁日志
prod_log = create_logger_decorator(level="info", include_args=False, include_time=True)

@dev_log
def process_data(data):
    time.sleep(0.1)
    return len(data)

@prod_log
def handle_request(path):
    time.sleep(0.05)
    return 200
```

**另一个实用模式——根据环境变量决定是否启用装饰器：**

```python
import os
import functools

def conditional_decorator(decorator, condition):
    """
    条件装饰器工厂：只在条件为真时应用装饰器
    
    用法: @conditional_decorator(timer, os.getenv("DEBUG"))
    """
    def factory(func):
        if condition:
            return decorator(func)  # 条件为真 → 应用装饰器
        return func                 # 条件为假 → 返回原函数，啥都不做
    return factory

# 只在 DEBUG 模式下启用计时
@conditional_decorator(timer, os.getenv("DEBUG") == "1")
def api_handler():
    pass
```

> 💡 **装饰器工厂的核心价值**：把装饰器的"配置"和"逻辑"分离。同一套增强逻辑，通过不同的参数组合，可以生成适用于不同场景的装饰器，避免写大量重复代码。

### 3.3 实战案例：类型检查装饰器 + 参数校验

Python 的类型注解（Type Hints）默认是"摆设"——解释器不会真正检查传入的类型。但你可以用装饰器在**运行时**强制检查。

```python
import functools
import inspect

def type_check(func):
    """
    运行时类型检查装饰器
    
    根据函数的类型注解，在调用时自动校验参数类型。
    不符合注解的参数会立即抛出 TypeError。
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 获取函数签名和类型注解
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()  # 填充默认值
        
        for param_name, value in bound.arguments.items():
            # 检查参数是否有类型注解
            annotation = func.__annotations__.get(param_name)
            if annotation and not isinstance(value, annotation):
                raise TypeError(
                    f"参数 '{param_name}' 期望 {annotation.__name__}，"
                    f"实际收到 {type(value).__name__}: {value!r}"
                )
        
        # 执行原函数
        result = func(*args, **kwargs)
        
        # 检查返回值类型
        return_annotation = func.__annotations__.get("return")
        if return_annotation and not isinstance(result, return_annotation):
            raise TypeError(
                f"返回值期望 {return_annotation.__name__}，"
                f"实际是 {type(result).__name__}: {result!r}"
            )
        
        return result
    return wrapper

# ──────────────────────────────────────────
# 使用示例
# ──────────────────────────────────────────
@type_check
def create_user(name: str, age: int, email: str = "none") -> dict:
    return {"name": name, "age": age, "email": email}

# ✅ 正常调用
print(create_user("Alice", 25))
# {'name': 'Alice', 'age': 25, 'email': 'none'}

# ❌ 类型错误 → 立即报错
create_user("Alice", "二十五")
# TypeError: 参数 'age' 期望 int，实际收到 str: '二十五'

create_user(123, 25)
# TypeError: 参数 'name' 期望 str，实际收到 int: 123
```

**这个装饰器的关键知识点：**

| 技术点 | 说明 |
|:---|:---|
| `inspect.signature()` | 获取函数的完整签名（参数名、默认值、注解） |
| `sig.bind()` | 把实际传入的 `*args, **kwargs` 绑定到具名参数上 |
| `__annotations__` | 类型注解字典，如 `{'name': str, 'age': int, 'return': dict}` |
| `apply_defaults()` | 填充用户没传的默认值参数 |

> 💡 **生产建议**：这个装饰器适合在开发/测试阶段使用。在生产环境中，推荐用 Pydantic 做数据校验——它不仅检查类型，还会自动做类型转换（比如字符串 `"25"` 自动转成 int `25`）。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **多层装饰器** | 定义时从下往上包装，调用时从外往里执行 |
| **装饰器工厂** | 用函数生成装饰器，实现配置与逻辑分离 |
| **条件装饰器** | 根据运行时条件决定是否真正应用装饰 |
| **类型检查装饰器** | 利用 `inspect` + `__annotations__` 实现运行时校验 |

---

## 4. 描述符协议：@property 背后的魔法

前三章我们搞定了装饰器。现在进入元编程的第一个核心机制——**描述符 (Descriptor)**。你每天都在用它，只是不知道而已：`@property`、`@staticmethod`、`@classmethod`，底层都是描述符。

### 4.1 从 @property 的困惑说起

你一定写过这样的代码：

```python
class Circle:
    def __init__(self, radius):
        self._radius = radius
    
    @property
    def radius(self):
        """获取半径"""
        return self._radius
    
    @radius.setter
    def radius(self, value):
        """设置半径（带校验）"""
        if value < 0:
            raise ValueError("半径不能为负")
        self._radius = value
    
    @property
    def area(self):
        """面积（只读，自动计算）"""
        import math
        return math.pi * self._radius ** 2

c = Circle(5)
print(c.radius)    # 5     ← 明明是方法，为什么不用加 () ？
print(c.area)      # 78.54 ← 这也是方法啊，怎么像属性一样访问？
c.radius = 10      # ← 赋值操作怎么触发了一个函数？
c.radius = -1      # ValueError: 半径不能为负 ← 赋值还能校验？
```

**三个困惑：**
1. `radius` 明明是用 `def` 定义的方法，为什么访问时不用加 `()`？
2. 对 `radius` 赋值（`c.radius = 10`）怎么会触发一段 Python 代码？
3. `@property` 到底做了什么，让"方法"表现得像"属性"？

答案就是：**描述符协议**。`property` 是一个实现了描述符协议的类，而 Python 在属性访问时会自动检测并调用描述符。

### 4.2 描述符协议三剑客：__get__、__set__、__delete__

描述符协议非常简单——只要一个类实现了以下三个方法中的**任意一个**，它的实例就是一个描述符：

```python
class MyDescriptor:
    def __get__(self, obj, objtype=None):
        """当通过 obj.attr 访问时调用"""
        pass
    
    def __set__(self, obj, value):
        """当通过 obj.attr = value 赋值时调用"""
        pass
    
    def __delete__(self, obj):
        """当通过 del obj.attr 删除时调用"""
        pass
```

**参数含义：**

| 参数 | 说明 | 示例 |
|:---|:---|:---|
| `self` | 描述符实例本身 | `MyDescriptor()` 对象 |
| `obj` | 拥有这个描述符的实例 | `c`（Circle 实例） |
| `objtype` | 拥有这个描述符的类 | `Circle` 类本身 |
| `value` | 被赋的值 | `10`（`c.radius = 10` 中的 10） |

先用一个最简单的例子感受它的运行机制：

```python
class Verbose:
    """一个会"说话"的描述符——每次被访问/赋值/删除都打印日志"""
    
    def __init__(self, name):
        self.name = name
        self.value = None
    
    def __get__(self, obj, objtype=None):
        print(f"📖 读取 {self.name} → {self.value}")
        return self.value
    
    def __set__(self, obj, value):
        print(f"✏️ 设置 {self.name} = {value}")
        self.value = value
    
    def __delete__(self, obj):
        print(f"🗑️ 删除 {self.name}")
        self.value = None

class User:
    # Verbose() 实例作为类属性 → 它是一个描述符
    name = Verbose("name")
    age = Verbose("age")

u = User()
u.name = "Alice"     # ✏️ 设置 name = Alice
u.age = 25           # ✏️ 设置 age = 25
print(u.name)        # 📖 读取 name → Alice
del u.age            # 🗑️ 删除 age
```

**关键点**：描述符必须作为**类属性**（不是实例属性）定义才能触发协议。这是因为 Python 只在类的 `__dict__` 中查找描述符，不会在实例的 `__dict__` 中找。

```
描述符触发条件：
1. 描述符对象必须定义在类上（class 层级）    ✅ User.name = Verbose("name")
2. 不能定义在 __init__ 里（实例层级）        ❌ self.name = Verbose("name")
```

> 💡 **一句话总结**：描述符就是一个实现了 `__get__`/`__set__`/`__delete__` 的对象。当它作为类属性存在时，Python 会在属性访问时自动调用这些方法，而不是直接返回描述符对象本身。

### 4.3 数据描述符 vs 非数据描述符

Python 把描述符分为两类，它们在属性查找时的**优先级不同**：

| 类型 | 定义 | 优先级 |
|:---|:---|:---|
| **数据描述符** | 同时实现了 `__get__` 和 `__set__`（或 `__delete__`） | **最高** —— 优先于实例 `__dict__` |
| **非数据描述符** | 只实现了 `__get__`，没有 `__set__` | **低于实例 `__dict__`** |

这个优先级差异是很多"诡异 bug"的根源。用代码来验证：

```python
class DataDesc:
    """数据描述符（有 __get__ 和 __set__）"""
    def __get__(self, obj, objtype=None):
        print("  DataDesc.__get__ 被调用")
        return "来自数据描述符"
    
    def __set__(self, obj, value):
        print(f"  DataDesc.__set__ 被调用: {value}")

class NonDataDesc:
    """非数据描述符（只有 __get__）"""
    def __get__(self, obj, objtype=None):
        print("  NonDataDesc.__get__ 被调用")
        return "来自非数据描述符"

class MyClass:
    data_attr = DataDesc()        # 数据描述符
    non_data_attr = NonDataDesc() # 非数据描述符

obj = MyClass()

# ── 测试数据描述符 ──
print("1. 访问 data_attr:")
print(f"   → {obj.data_attr}")
#   DataDesc.__get__ 被调用
#   → 来自数据描述符

# 试图用实例 __dict__ 覆盖数据描述符
obj.__dict__["data_attr"] = "实例值"
print("2. 覆盖后再访问 data_attr:")
print(f"   → {obj.data_attr}")
#   DataDesc.__get__ 被调用
#   → 来自数据描述符          ← 数据描述符赢了！实例值被无视

# ── 测试非数据描述符 ──
print("3. 访问 non_data_attr:")
print(f"   → {obj.non_data_attr}")
#   NonDataDesc.__get__ 被调用
#   → 来自非数据描述符

# 用实例 __dict__ 覆盖非数据描述符
obj.__dict__["non_data_attr"] = "实例值"
print("4. 覆盖后再访问 non_data_attr:")
print(f"   → {obj.non_data_attr}")
#   → 实例值                  ← 实例值赢了！非数据描述符被跳过
```

**Python 属性查找的完整顺序：**

```
obj.attr 时，Python 的查找顺序是：

1️⃣ 类（及父类）的 __dict__ 中找到 数据描述符？ → 调用 __get__
2️⃣ 实例的 __dict__ 中找到同名属性？           → 直接返回
3️⃣ 类（及父类）的 __dict__ 中找到 非数据描述符？→ 调用 __get__
4️⃣ 都没找到？                                → 触发 __getattr__（如果定义了）
5️⃣ 还没有？                                  → 抛出 AttributeError
```

> 💡 **为什么 `@property` 能"拦截"赋值？** 因为 `property` 同时实现了 `__get__` 和 `__set__`，它是数据描述符，优先级高于实例 `__dict__`。所以 `obj.prop = value` 不会直接写入 `__dict__`，而是触发 `property.__set__`。

### 4.4 手写一个 property：揭开魔法的面纱

既然 `property` 就是一个描述符，那我们能不能**自己用 Python 重写一个**？当然可以！下面的 `MyProperty` 实现了 `property` 的核心功能：

```python
class MyProperty:
    """
    手写 property —— 用描述符协议实现
    
    实际上 CPython 的 property 是用 C 写的，
    但逻辑和这里完全一样。
    """
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget      # getter 函数
        self.fset = fset      # setter 函数
        self.fdel = fdel      # deleter 函数
        self.__doc__ = doc or (fget.__doc__ if fget else None)
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self       # 通过类访问（Circle.radius）返回描述符本身
        if self.fget is None:
            raise AttributeError("不可读的属性")
        return self.fget(obj) # 调用 getter：fget(circle_instance)
    
    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("不可写的属性")
        self.fset(obj, value) # 调用 setter：fset(circle_instance, value)
    
    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("不可删的属性")
        self.fdel(obj)        # 调用 deleter
    
    # 用于 @prop.setter 语法的装饰器方法
    def setter(self, fset):
        return type(self)(self.fget, fset, self.fdel, self.__doc__)
    
    def deleter(self, fdel):
        return type(self)(self.fget, self.fset, fdel, self.__doc__)

# ──────────────────────────────────────────
# 用 MyProperty 替代内置 property，效果完全一样
# ──────────────────────────────────────────
class Circle:
    def __init__(self, radius):
        self._radius = radius
    
    @MyProperty                    # 等价于 radius = MyProperty(radius_getter)
    def radius(self):
        return self._radius
    
    @radius.setter                 # 等价于 radius = radius.setter(radius_setter)
    def radius(self, value):
        if value < 0:
            raise ValueError("半径不能为负")
        self._radius = value

c = Circle(5)
print(c.radius)      # 5 ← 触发 MyProperty.__get__ → fget(c)
c.radius = 10        # ← 触发 MyProperty.__set__ → fset(c, 10)
print(c.radius)      # 10
```

**`@property` 的脱糖过程，现在你能完全理解了：**

```python
# 这段代码：
class Circle:
    @property
    def radius(self):
        return self._radius

# 等价于：
class Circle:
    def radius(self):
        return self._radius
    radius = property(radius)  # radius 变成了一个 property 描述符对象

# 当你写 c.radius 时：
# Python 发现 Circle.radius 是数据描述符
# → 调用 Circle.radius.__get__(c, Circle)
# → 调用 fget(c)
# → 调用原始的 radius(c)
# → 返回 c._radius
```

> 💡 **这就是所有"魔法"的底层**：Python 的属性访问不是简单地查字典，而是有一套精密的描述符查找机制。`property`、`classmethod`、`staticmethod`，甚至普通的方法绑定，都是描述符在起作用。

### 4.5 实战案例：字段校验描述符

`property` 的一个痛点是：如果你有很多字段需要校验，每个字段都要写一套 getter/setter，代码会非常冗余。**描述符可以优雅地解决这个问题**——写一次，到处复用。

```python
class Validated:
    """
    通用字段校验描述符
    
    用法：在类中定义 name = Validated(str, min_length=1)
    所有对 name 的赋值都会自动校验
    """
    def __init__(self, expected_type, *, min_val=None, max_val=None, 
                 min_length=None, max_length=None):
        self.expected_type = expected_type
        self.min_val = min_val
        self.max_val = max_val
        self.min_length = min_length
        self.max_length = max_length
        self.attr_name = None  # 由 __set_name__ 自动注入（第 5 章会讲）
    
    def __set_name__(self, owner, name):
        """Python 3.6+ 自动调用，告诉描述符它的属性名"""
        self.attr_name = name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.attr_name)
    
    def __set__(self, obj, value):
        # 类型检查
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"'{self.attr_name}' 期望 {self.expected_type.__name__}，"
                f"实际是 {type(value).__name__}"
            )
        
        # 数值范围检查
        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"'{self.attr_name}' 不能小于 {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"'{self.attr_name}' 不能大于 {self.max_val}")
        
        # 长度检查（用于字符串、列表等）
        if self.min_length is not None and len(value) < self.min_length:
            raise ValueError(f"'{self.attr_name}' 长度不能少于 {self.min_length}")
        if self.max_length is not None and len(value) > self.max_length:
            raise ValueError(f"'{self.attr_name}' 长度不能超过 {self.max_length}")
        
        obj.__dict__[self.attr_name] = value  # 存入实例的 __dict__

# ──────────────────────────────────────────
# 使用：像声明式配置一样定义字段约束
# ──────────────────────────────────────────
class User:
    name = Validated(str, min_length=1, max_length=50)
    age = Validated(int, min_val=0, max_val=200)
    email = Validated(str, min_length=5)

# ✅ 正常创建
u = User()
u.name = "Alice"
u.age = 25
u.email = "alice@example.com"

# ❌ 校验失败 → 立刻报错
u.name = ""           # ValueError: 'name' 长度不能少于 1
u.age = -5            # ValueError: 'age' 不能小于 0
u.age = "二十五"       # TypeError: 'age' 期望 int，实际是 str
u.email = "abc"       # ValueError: 'email' 长度不能少于 5
```

**对比 `@property` 写法的优势：**

```python
# 用 @property 要为每个字段重复写 getter/setter（15行 × N个字段）
# 用描述符只需一行声明：
class User:
    name = Validated(str, min_length=1, max_length=50)   # 一行搞定
    age = Validated(int, min_val=0, max_val=200)         # 一行搞定
    email = Validated(str, min_length=5)                  # 一行搞定
```

> 💡 **描述符 vs property 的选择**：如果只有 1-2 个属性需要特殊行为（计算属性、惰性加载），用 `@property`。如果有很多字段需要**相同类型的校验/转换**逻辑，用自定义描述符——写一次，复用 N 次。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **描述符** | 实现了 `__get__`/`__set__`/`__delete__` 的对象 |
| **数据描述符** | 实现了 `__get__` + `__set__`，优先级高于实例 `__dict__` |
| **非数据描述符** | 只有 `__get__`，优先级低于实例 `__dict__` |
| **property 本质** | 一个同时实现了三个描述符方法的类 |
| **自定义描述符** | 可复用的字段行为，一次定义、多处使用 |

---

## 5. __init_subclass__ 与 __set_name__：轻量元编程

很多人一提到"元编程"就想到"元类"——然后被吓退了。其实 Python 3.6+ 提供了两个**轻量级钩子**，能在不动用元类的前提下，实现大部分"在类创建时做文章"的需求。

### 5.1 __init_subclass__：在子类创建时自动执行逻辑

`__init_subclass__` 是一个**父类钩子**：每当有新的子类被定义时，Python 会自动调用父类的 `__init_subclass__` 方法。

```python
class Animal:
    """基类：会自动记录所有子类"""
    _registry = []
    
    def __init_subclass__(cls, sound=None, **kwargs):
        """
        每当 Animal 被继承时，Python 自动调用这个方法
        
        参数：
        - cls: 新创建的子类（不是 Animal 本身！）
        - sound: 可以通过 class Dog(Animal, sound="汪汪") 传入
        - **kwargs: 传递给 super().__init_subclass__
        """
        super().__init_subclass__(**kwargs)
        cls.sound = sound or "..."
        Animal._registry.append(cls)
        print(f"🐾 注册新动物: {cls.__name__}（叫声: {cls.sound}）")

# 定义子类时，__init_subclass__ 自动触发
class Dog(Animal, sound="汪汪"):
    pass
# 🐾 注册新动物: Dog（叫声: 汪汪）

class Cat(Animal, sound="喵喵"):
    pass
# 🐾 注册新动物: Cat（叫声: 喵喵）

class Fish(Animal):
    pass
# 🐾 注册新动物: Fish（叫声: ...）

# 查看注册表
print(Animal._registry)
# [<class 'Dog'>, <class 'Cat'>, <class 'Fish'>]

# 子类自动获得了 sound 属性
print(Dog.sound)   # 汪汪
print(Cat.sound)   # 喵喵
```

**关键点：**

```
__init_subclass__ 的触发时机：

class Dog(Animal, sound="汪汪"):   ← 定义这一行时就自动调用
    pass                            ← 不需要实例化，不需要手动注册

谁调用？   Python 解释器自动调用
调用谁的？ 父类（Animal）的 __init_subclass__
参数 cls？ 新定义的子类（Dog）
```

> 💡 **经典用途**：插件注册、序列化器注册、处理器注册——任何"继承即注册"的场景。以前实现这种功能必须用元类，现在一个 `__init_subclass__` 就够了。

### 5.2 __set_name__：让描述符知道自己叫什么名字

在第 4 章的 `Validated` 描述符里，你已经见过 `__set_name__` 了。现在让我们深入理解它。

**问题**：描述符在定义时，不知道自己被赋给了什么属性名。

```python
class Validated:
    def __init__(self):
        self.attr_name = ???  # 我怎么知道我叫 "name" 还是 "age"？

class User:
    name = Validated()  # Validated 实例不知道自己对应的属性名是 "name"
    age = Validated()   # 也不知道自己对应的是 "age"
```

在 Python 3.6 之前，解决方案很笨——要求用户**手动传入属性名**：

```python
class User:
    name = Validated("name")  # 手动传入字符串"name"，丑陋且容易出错
    age = Validated("age")    # 如果改了变量名忘改字符串就 bug 了
```

**`__set_name__` 优雅地解决了这个问题：**

```python
class Validated:
    def __set_name__(self, owner, name):
        """
        Python 在类创建时自动调用
        
        参数：
        - owner: 拥有这个描述符的类（User）
        - name: 描述符被赋值的属性名（"name" 或 "age"）
        """
        self.attr_name = name
        self.owner = owner
        print(f"📌 {owner.__name__}.{name} 绑定到了 Validated 描述符")
    
    def __set__(self, obj, value):
        print(f"✏️ 设置 {self.attr_name} = {value}")
        obj.__dict__[self.attr_name] = value
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.attr_name)

class User:
    name = Validated()   # 📌 User.name 绑定到了 Validated 描述符
    age = Validated()    # 📌 User.age 绑定到了 Validated 描述符
    # ↑ 定义类的时候就自动调用了 __set_name__，不需要手动传名字
```

**`__set_name__` 的触发时机：**

```
class User:                    ← 类定义开始
    name = Validated()         ← 创建 Validated 实例
    age = Validated()          ← 创建 Validated 实例
                               ← 类定义结束
                               ← Python 自动遍历所有类属性
                               ← 发现 name 有 __set_name__ → 调用 name.__set_name__(User, "name")
                               ← 发现 age 有 __set_name__ → 调用 age.__set_name__(User, "age")
```

> 💡 **`__set_name__` 不仅用于描述符**。任何定义了 `__set_name__` 的对象，只要被赋值为类属性，Python 就会自动调用它。这是一个通用的"类创建时钩子"。

### 5.3 实战案例：插件注册系统

现在把 `__init_subclass__` 和 `__set_name__` 结合起来，构建一个**真实可用的插件系统**——新增插件只需继承基类，无需修改任何注册代码。

```python
class FileHandler:
    """
    文件处理器基类
    
    插件系统：继承此类并指定 extensions 参数，
    即可自动注册为对应文件类型的处理器。
    """
    _handlers = {}  # {".txt": TextHandler, ".csv": CsvHandler, ...}
    
    def __init_subclass__(cls, extensions=(), **kwargs):
        super().__init_subclass__(**kwargs)
        for ext in extensions:
            FileHandler._handlers[ext] = cls
            print(f"📂 注册处理器: {ext} → {cls.__name__}")
    
    def process(self, filepath):
        raise NotImplementedError("子类必须实现 process 方法")
    
    @classmethod
    def get_handler(cls, filepath):
        """根据文件扩展名自动选择处理器"""
        import os
        ext = os.path.splitext(filepath)[1].lower()
        handler_class = cls._handlers.get(ext)
        if handler_class is None:
            raise ValueError(f"不支持的文件类型: {ext}")
        return handler_class()

# ──────────────────────────────────────────
# 定义插件：只需继承 + 指定 extensions
# ──────────────────────────────────────────
class TextHandler(FileHandler, extensions=[".txt", ".log"]):
    def process(self, filepath):
        return f"📄 读取文本文件: {filepath}"

class CsvHandler(FileHandler, extensions=[".csv"]):
    def process(self, filepath):
        return f"📊 解析 CSV 文件: {filepath}"

class JsonHandler(FileHandler, extensions=[".json", ".jsonl"]):
    def process(self, filepath):
        return f"🔧 解析 JSON 文件: {filepath}"

# 输出：
# 📂 注册处理器: .txt → TextHandler
# 📂 注册处理器: .log → TextHandler
# 📂 注册处理器: .csv → CsvHandler
# 📂 注册处理器: .json → JsonHandler
# 📂 注册处理器: .jsonl → JsonHandler

# ──────────────────────────────────────────
# 使用：根据文件类型自动分发
# ──────────────────────────────────────────
handler = FileHandler.get_handler("data.csv")
print(handler.process("data.csv"))
# 📊 解析 CSV 文件: data.csv

handler = FileHandler.get_handler("config.json")
print(handler.process("config.json"))
# 🔧 解析 JSON 文件: config.json

# 查看所有已注册的处理器
print(FileHandler._handlers)
# {'.txt': TextHandler, '.log': TextHandler, '.csv': CsvHandler, ...}
```

**这个插件系统的优势：**

```
传统做法（手动注册）：
  handlers = {}
  handlers[".txt"] = TextHandler     ← 每增加一个插件
  handlers[".csv"] = CsvHandler     ← 就要改这里
  handlers[".json"] = JsonHandler   ← 改漏了就 bug

__init_subclass__ 做法（自动注册）：
  class NewHandler(FileHandler, extensions=[".xml"]):  ← 只需继承
      def process(self, filepath): ...                  ← 写业务逻辑
  # 完了！不需要改任何注册代码！
```

> 💡 **这就是"开闭原则"（Open-Closed Principle）的体现**：系统对扩展开放（加新插件只需添加子类），对修改关闭（不需要改现有代码）。Django REST Framework 的序列化器、FastAPI 的依赖注入，很多框架都用类似的模式。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **`__init_subclass__`** | 父类钩子，子类被定义时自动触发 |
| **`__set_name__`** | 类属性钩子，告诉对象它被赋值给了哪个属性名 |
| **插件注册** | 继承即注册，无需手动维护注册表 |
| **vs 元类** | 这两个钩子能解决 80% 的"类创建时定制"需求，比元类简单得多 |

---

## 6. 元类 (Metaclass)：控制类的创建过程

终于来到了 Python 元编程的"终极 Boss"——**元类**。元类这个概念之所以让人害怕，是因为它涉及一个很绕的思维跳跃：**类本身也是一个对象**，而元类就是"创建类的类"。

别慌，我们一步步来。

### 6.1 type()：不只是查类型，还能创建类

你一定用过 `type()` 来查看对象的类型：

```python
print(type(42))        # <class 'int'>
print(type("hello"))   # <class 'str'>
print(type([1, 2]))    # <class 'list'>
```

但 `type()` 还有一个**鲜为人知的用法**——它可以直接**创建类**：

```python
# ════════════════════════════════════════════
# 用 class 语法创建类（你熟悉的写法）
# ════════════════════════════════════════════
class Dog:
    species = "犬科"
    
    def bark(self):
        return "汪汪！"

# ════════════════════════════════════════════
# 用 type() 创建完全等价的类（Python 底层实际做的事）
# ════════════════════════════════════════════
def bark(self):
    return "汪汪！"

Dog2 = type(
    "Dog2",                    # 第 1 个参数：类名
    (object,),                 # 第 2 个参数：父类元组
    {"species": "犬科", "bark": bark}  # 第 3 个参数：类的属性和方法
)

# 两种方式创建的类完全等价
d1 = Dog()
d2 = Dog2()
print(d1.bark())       # 汪汪！
print(d2.bark())       # 汪汪！
print(d1.species)      # 犬科
print(d2.species)      # 犬科
```

**关键认知跳跃：**

```
普通对象是类的实例：
  d = Dog()         → d 是 Dog 的实例
  type(d)           → <class 'Dog'>

类本身是 type 的实例：
  type(Dog)         → <class 'type'>
  type(int)         → <class 'type'>
  type(str)         → <class 'type'>

所以：type 是「类的类」—— 也就是「元类」！
```

```
实例关系链：

d (Dog实例)  ──是实例──▶  Dog (类)  ──是实例──▶  type (元类)
42 (int实例)  ──是实例──▶  int (类)  ──是实例──▶  type (元类)
```

> 💡 **一句话**：`type` 是 Python 中所有类的默认元类。当你写 `class Dog:` 时，Python 在底层调用 `type("Dog", (object,), {...})` 来创建 `Dog` 这个类对象。

### 6.2 元类的运行机制：__new__ 与 __init__

既然 `type` 是默认元类，那我们可以**继承 `type`** 来自定义元类，从而控制"类是怎么被创建的"。

```python
class MyMeta(type):
    """
    自定义元类
    
    __new__: 创建类对象（在类还不存在时调用）
    __init__: 初始化类对象（类已创建，做后续设置）
    """
    def __new__(mcs, name, bases, namespace):
        """
        参数：
        - mcs: 元类本身（MyMeta）
        - name: 类名（如 "User"）
        - bases: 父类元组（如 (object,)）
        - namespace: 类的命名空间字典（所有属性和方法）
        """
        print(f"🔨 __new__: 正在创建类 '{name}'")
        print(f"   父类: {bases}")
        print(f"   属性: {list(namespace.keys())}")
        
        # 调用 type.__new__ 来真正创建类对象
        cls = super().__new__(mcs, name, bases, namespace)
        return cls
    
    def __init__(cls, name, bases, namespace):
        print(f"⚙️ __init__: 初始化类 '{name}'")
        super().__init__(name, bases, namespace)

# 使用自定义元类
class User(metaclass=MyMeta):
    name = "default"
    
    def greet(self):
        return f"Hello, {self.name}"

# 输出（在定义 class 的时候就触发了！）：
# 🔨 __new__: 正在创建类 'User'
#    父类: (<class 'object'>,)
#    属性: ['__module__', '__qualname__', 'name', 'greet']
# ⚙️ __init__: 初始化类 'User'
```

**`__new__` vs `__init__` 在元类中的区别：**

| 方法 | 调用时机 | 职责 | 能做什么 |
|:---|:---|:---|:---|
| `__new__` | 类对象**创建之前** | 创建并返回类对象 | 修改类名、父类、添加/删除属性 |
| `__init__` | 类对象**创建之后** | 对已创建的类做设置 | 注册类、添加属性、校验结构 |

**一个实用的元类例子——自动给所有方法添加日志：**

```python
import functools

class AutoLogMeta(type):
    """元类：自动给类的所有方法包装日志装饰器"""
    
    def __new__(mcs, name, bases, namespace):
        # 遍历命名空间，找到所有可调用的属性（方法）
        for attr_name, attr_value in namespace.items():
            if callable(attr_value) and not attr_name.startswith("_"):
                # 用日志装饰器包装
                namespace[attr_name] = mcs._add_log(attr_value)
        
        return super().__new__(mcs, name, bases, namespace)
    
    @staticmethod
    def _add_log(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"📝 调用 {func.__name__}")
            return func(*args, **kwargs)
        return wrapper

class UserService(metaclass=AutoLogMeta):
    def create_user(self, name):
        return f"创建用户: {name}"
    
    def delete_user(self, user_id):
        return f"删除用户: {user_id}"

svc = UserService()
svc.create_user("Alice")   # 📝 调用 create_user
svc.delete_user(42)        # 📝 调用 delete_user
# 所有公开方法自动有了日志，一行装饰器都不用写！
```

> 💡 **元类执行时机是类定义时，不是实例化时。** `class User(metaclass=MyMeta):` 这一行执行完，元类的 `__new__` 和 `__init__` 就已经运行完毕了。后续创建 `User()` 实例时，元类不再参与。

### 6.3 __prepare__：控制类的命名空间

在 Python 中，`class` 语句的主体会被执行成一个字典——这个字典就是类的**命名空间 (namespace)**。默认情况下，这个字典就是普通的 `dict`。

`__prepare__` 方法让你可以**替换这个字典**，从而控制类的属性被存储的方式。

```python
from collections import OrderedDict

class OrderedMeta(type):
    """元类：保留类属性的定义顺序"""
    
    @classmethod
    def __prepare__(mcs, name, bases):
        """
        在类体执行之前调用，返回一个用作命名空间的字典
        
        默认返回 dict()，我们换成 OrderedDict()
        来记录属性的定义顺序
        """
        print(f"📋 __prepare__: 为 '{name}' 准备命名空间")
        return OrderedDict()
    
    def __new__(mcs, name, bases, namespace):
        # namespace 现在是 OrderedDict，保留了定义顺序
        cls = super().__new__(mcs, name, bases, dict(namespace))
        cls._field_order = [
            key for key in namespace 
            if not key.startswith("_")
        ]
        return cls

class Config(metaclass=OrderedMeta):
    host = "localhost"
    port = 8080
    debug = True
    database = "mydb"

# 属性按定义顺序输出
print(Config._field_order)
# ['host', 'port', 'debug', 'database'] ← 保持了定义顺序
```

> 💡 **实际上**，Python 3.7+ 的普通 `dict` 已经默认保持插入顺序了。`__prepare__` 更大的价值在于你可以返回一个**自定义的字典子类**，在属性被定义时做拦截、校验、转换等操作。例如 Django 的 Model 用类似机制来保持字段定义顺序。

### 6.4 实战案例：手写一个简易 ORM

现在综合运用元类 + 描述符，来实现一个**极简版 ORM**——像 Django Model 那样，用声明式语法定义数据库表结构。

```python
# ──────────────────────────────────────────
# Step 1：定义字段描述符
# ──────────────────────────────────────────
class Field:
    """ORM 字段基类"""
    def __init__(self, column_type):
        self.column_type = column_type
        self.name = None  # 由 __set_name__ 自动注入
    
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.name)
    
    def __set__(self, obj, value):
        obj.__dict__[self.name] = value
    
    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.name}' {self.column_type}>"

class StringField(Field):
    def __init__(self, max_length=255):
        super().__init__(f"VARCHAR({max_length})")

class IntegerField(Field):
    def __init__(self):
        super().__init__("INTEGER")

class BooleanField(Field):
    def __init__(self):
        super().__init__("BOOLEAN")

# ──────────────────────────────────────────
# Step 2：定义元类，自动收集字段并生成 SQL
# ──────────────────────────────────────────
class ModelMeta(type):
    """ORM 元类：自动收集 Field 字段，生成建表 SQL"""
    
    def __new__(mcs, name, bases, namespace):
        # 跳过基类 Model 本身
        if name == "Model":
            return super().__new__(mcs, name, bases, namespace)
        
        # 收集所有 Field 类型的属性
        fields = {}
        for key, value in namespace.items():
            if isinstance(value, Field):
                fields[key] = value
        
        # 把字段信息存到类上
        namespace["_fields"] = fields
        namespace["_table_name"] = namespace.get("_table_name", name.lower())
        
        cls = super().__new__(mcs, name, bases, namespace)
        print(f"🗄️ 注册 Model: {name}（表名: {cls._table_name}，字段: {list(fields.keys())}）")
        return cls

# ──────────────────────────────────────────
# Step 3：定义 Model 基类
# ──────────────────────────────────────────
class Model(metaclass=ModelMeta):
    """ORM 基类：所有模型继承此类"""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key in self._fields:
                setattr(self, key, value)
            else:
                raise AttributeError(f"'{type(self).__name__}' 没有字段 '{key}'")
    
    @classmethod
    def create_table_sql(cls):
        """生成建表 SQL"""
        columns = [f"  {name} {field.column_type}" for name, field in cls._fields.items()]
        columns_str = ",\n".join(columns)
        return f"CREATE TABLE {cls._table_name} (\n  id INTEGER PRIMARY KEY,\n{columns_str}\n);"
    
    def insert_sql(self):
        """生成插入 SQL"""
        fields = []
        values = []
        for name in self._fields:
            value = getattr(self, name, None)
            if value is not None:
                fields.append(name)
                values.append(repr(value))
        
        fields_str = ", ".join(fields)
        values_str = ", ".join(values)
        return f"INSERT INTO {self._table_name} ({fields_str}) VALUES ({values_str});"
    
    def __repr__(self):
        attrs = ", ".join(f"{k}={getattr(self, k, None)!r}" for k in self._fields)
        return f"{type(self).__name__}({attrs})"
```

**使用效果——像 Django 一样声明式定义模型：**

```python
class User(Model):
    _table_name = "users"
    name = StringField(max_length=100)
    age = IntegerField()
    is_active = BooleanField()

class Post(Model):
    title = StringField(max_length=200)
    content = StringField(max_length=5000)

# 🗄️ 注册 Model: User（表名: users，字段: ['name', 'age', 'is_active']）
# 🗄️ 注册 Model: Post（表名: post，字段: ['title', 'content']）

# 生成建表 SQL
print(User.create_table_sql())
# CREATE TABLE users (
#   id INTEGER PRIMARY KEY,
#   name VARCHAR(100),
#   age INTEGER,
#   is_active BOOLEAN
# );

# 创建实例并生成插入 SQL
u = User(name="Alice", age=25, is_active=True)
print(u)            # User(name='Alice', age=25, is_active=True)
print(u.insert_sql())
# INSERT INTO users (name, age, is_active) VALUES ('Alice', 25, True);
```

> 💡 **这就是 Django ORM、SQLAlchemy 等框架的核心思路**：用元类自动收集声明在类上的字段，用描述符控制属性访问行为，把"声明式代码"翻译成"命令式 SQL"。真正的 ORM 还多了连接池、事务、查询构建器等，但骨架就是这个。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **`type`** | Python 中所有类的默认元类，`class Foo:` 底层是 `type("Foo", ...)` |
| **`__new__`** | 元类中创建类对象的方法，可修改类名/父类/属性 |
| **`__init__`** | 元类中初始化类对象的方法，用于注册、校验 |
| **`__prepare__`** | 在类体执行前返回自定义命名空间字典 |
| **元类执行时机** | 类定义时（不是实例化时） |

---

## 7. 综合实战：从零构建一个声明式验证框架

前面六章分别学了装饰器、描述符、`__init_subclass__`、元类。这一章把它们**全部串起来**，构建一个类似 Pydantic 的数据验证框架——从零开始，一步步搭建。

### 7.1 目标：像 Pydantic 一样优雅地定义数据模型

我们的目标是让用户写出这样的代码：

```python
@serializable
class UserProfile(Schema):
    name = String(min_length=1, max_length=50)
    age = Integer(min_val=0, max_val=200)
    email = String(min_length=5)
    is_vip = Boolean(default=False)

# ✅ 创建实例（自动校验）
user = UserProfile(name="Alice", age=25, email="alice@test.com")

# ✅ 自动生成 __repr__
print(user)  # UserProfile(name='Alice', age=25, email='alice@test.com', is_vip=False)

# ✅ 序列化为字典
print(user.to_dict())  # {'name': 'Alice', 'age': 25, 'email': 'alice@test.com', 'is_vip': False}

# ✅ 从字典反序列化
user2 = UserProfile.from_dict({'name': 'Bob', 'age': 30, 'email': 'bob@test.com'})

# ❌ 校验失败 → 报错
UserProfile(name="", age=25, email="alice@test.com")
# ValueError: 'name' 长度不能少于 1
```

**需要用到的技术：**

| 功能 | 技术 | 章节回顾 |
|:---|:---|:---|
| 字段声明 + 自动校验 | 描述符（`__get__`/`__set__`/`__set_name__`） | 第 4、5 章 |
| 自动收集字段 + 生成 `__init__` | `__init_subclass__` 或元类 | 第 5、6 章 |
| 添加序列化能力 | 装饰器 | 第 2 章 |

### 7.2 Step 1：用描述符实现字段验证

首先构建字段描述符体系——每种数据类型对应一个描述符类：

```python
class FieldBase:
    """字段描述符基类"""
    
    def __init__(self, *, default=None, required=True):
        self.default = default
        self.required = required
        self.attr_name = None
    
    def __set_name__(self, owner, name):
        self.attr_name = name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.attr_name, self.default)
    
    def __set__(self, obj, value):
        # 允许 None 值（如果字段非必填）
        if value is None and not self.required:
            obj.__dict__[self.attr_name] = self.default
            return
        
        # 调用子类的校验方法
        self.validate(value)
        obj.__dict__[self.attr_name] = value
    
    def validate(self, value):
        """子类实现具体校验逻辑"""
        raise NotImplementedError


class String(FieldBase):
    """字符串字段"""
    def __init__(self, *, min_length=0, max_length=None, **kwargs):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value):
        if not isinstance(value, str):
            raise TypeError(f"'{self.attr_name}' 期望 str，收到 {type(value).__name__}")
        if len(value) < self.min_length:
            raise ValueError(f"'{self.attr_name}' 长度不能少于 {self.min_length}")
        if self.max_length and len(value) > self.max_length:
            raise ValueError(f"'{self.attr_name}' 长度不能超过 {self.max_length}")


class Integer(FieldBase):
    """整数字段"""
    def __init__(self, *, min_val=None, max_val=None, **kwargs):
        super().__init__(**kwargs)
        self.min_val = min_val
        self.max_val = max_val
    
    def validate(self, value):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"'{self.attr_name}' 期望 int，收到 {type(value).__name__}")
        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"'{self.attr_name}' 不能小于 {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"'{self.attr_name}' 不能大于 {self.max_val}")


class Boolean(FieldBase):
    """布尔字段"""
    def __init__(self, **kwargs):
        kwargs.setdefault("default", False)
        super().__init__(**kwargs)
    
    def validate(self, value):
        if not isinstance(value, bool):
            raise TypeError(f"'{self.attr_name}' 期望 bool，收到 {type(value).__name__}")
```

> 💡 每个字段类只需实现 `validate()` 方法，校验逻辑集中在一处。新增字段类型（如 `Float`、`List`、`Email`）只需继承 `FieldBase` 并实现 `validate()`。

### 7.3 Step 2：用元类自动收集字段

有了字段描述符，我们需要一个机制来**自动收集类中定义了哪些字段**，并据此生成 `__init__` 和 `__repr__` 方法。这里用 `__init_subclass__` 就够了（不必动用元类）：

```python
class Schema:
    """
    验证框架的基类
    
    所有数据模型继承此类，自动获得：
    - 字段自动收集
    - __init__ 自动生成
    - __repr__ 自动生成
    """
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        # 收集所有 FieldBase 类型的类属性
        fields = {}
        for name, value in cls.__dict__.items():
            if isinstance(value, FieldBase):
                fields[name] = value
        
        cls._fields = fields
    
    def __init__(self, **kwargs):
        # 遍历所有字段，赋值或使用默认值
        for name, field in self._fields.items():
            if name in kwargs:
                setattr(self, name, kwargs[name])  # 触发描述符的 __set__ → 校验
            elif field.default is not None:
                setattr(self, name, field.default)
            elif field.required:
                raise ValueError(f"缺少必需字段: '{name}'")
        
        # 检查是否传入了未知字段
        unknown = set(kwargs) - set(self._fields)
        if unknown:
            raise AttributeError(f"未知字段: {unknown}")
    
    def __repr__(self):
        attrs = ", ".join(
            f"{name}={getattr(self, name)!r}" 
            for name in self._fields
        )
        return f"{type(self).__name__}({attrs})"
```

**测试一下：**

```python
class User(Schema):
    name = String(min_length=1)
    age = Integer(min_val=0)

# ✅ 正常创建
u = User(name="Alice", age=25)
print(u)  # User(name='Alice', age=25)

# ❌ 缺少必需字段
User(name="Alice")      # ValueError: 缺少必需字段: 'age'

# ❌ 校验失败
User(name="", age=25)   # ValueError: 'name' 长度不能少于 1

# ❌ 未知字段
User(name="A", age=25, foo="bar")  # AttributeError: 未知字段: {'foo'}
```

### 7.4 Step 3：用装饰器添加序列化能力

最后一块拼图——用装饰器给任何 Schema 子类添加 `to_dict()` 和 `from_dict()` 方法：

```python
def serializable(cls):
    """
    装饰器：为 Schema 子类添加序列化/反序列化能力
    
    用法：@serializable
    """
    def to_dict(self):
        """实例 → 字典"""
        return {
            name: getattr(self, name) 
            for name in self._fields
        }
    
    @classmethod
    def from_dict(klass, data):
        """字典 → 实例"""
        return klass(**data)
    
    def to_json(self):
        """实例 → JSON 字符串"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_json(klass, json_str):
        """JSON 字符串 → 实例"""
        import json
        return klass.from_dict(json.loads(json_str))
    
    # 把方法注入到类上
    cls.to_dict = to_dict
    cls.from_dict = from_dict
    cls.to_json = to_json
    cls.from_json = from_json
    
    return cls
```

> 💡 **为什么用装饰器而不是直接写在 Schema 里？** 因为序列化是**可选能力**——有些模型可能不需要序列化（比如纯内部使用的配置对象）。用装饰器可以选择性地添加，符合"组合优于继承"的原则。

### 7.5 完整代码与测试

三个模块组装完毕，来看完整的使用效果：

```python
# ──────────────────────────────────────────
# 定义数据模型（用户只需要写这部分）
# ──────────────────────────────────────────
@serializable
class UserProfile(Schema):
    name = String(min_length=1, max_length=50)
    age = Integer(min_val=0, max_val=200)
    email = String(min_length=5)
    is_vip = Boolean(default=False, required=False)

@serializable
class Product(Schema):
    title = String(min_length=1, max_length=200)
    price = Integer(min_val=0)
    in_stock = Boolean(default=True, required=False)
```

```python
# ──────────────────────────────────────────
# 测试：创建、校验、序列化
# ──────────────────────────────────────────

# ✅ 正常创建
user = UserProfile(name="Alice", age=25, email="alice@example.com")
print(user)
# UserProfile(name='Alice', age=25, email='alice@example.com', is_vip=False)

# ✅ 序列化为字典
print(user.to_dict())
# {'name': 'Alice', 'age': 25, 'email': 'alice@example.com', 'is_vip': False}

# ✅ 序列化为 JSON
print(user.to_json())
# {"name": "Alice", "age": 25, "email": "alice@example.com", "is_vip": false}

# ✅ 从字典反序列化
data = {"name": "Bob", "age": 30, "email": "bob@test.com", "is_vip": True}
user2 = UserProfile.from_dict(data)
print(user2)
# UserProfile(name='Bob', age=30, email='bob@test.com', is_vip=True)

# ✅ 从 JSON 反序列化
user3 = UserProfile.from_json('{"name":"Charlie","age":35,"email":"c@test.com"}')
print(user3)
# UserProfile(name='Charlie', age=35, email='c@test.com', is_vip=False)
```

```python
# ──────────────────────────────────────────
# 测试：校验失败的情况
# ──────────────────────────────────────────

# ❌ 类型错误
UserProfile(name=123, age=25, email="a@b.com")
# TypeError: 'name' 期望 str，收到 int

# ❌ 值域错误
UserProfile(name="Alice", age=-1, email="a@b.com")
# ValueError: 'age' 不能小于 0

# ❌ 长度错误
UserProfile(name="", age=25, email="a@b.com")
# ValueError: 'name' 长度不能少于 1

# ❌ 缺少必需字段
UserProfile(name="Alice")
# ValueError: 缺少必需字段: 'age'
```

**架构回顾——三层技术如何协作：**

```
@serializable                    ← 装饰器层：注入 to_dict/from_dict/to_json/from_json
class UserProfile(Schema):       ← Schema 基类层：__init_subclass__ 收集字段 + __init__/__repr__
    name = String(min_length=1)  ← 描述符层：__set__ 时自动校验
    age = Integer(min_val=0)     ← 描述符层：类型+范围校验
```

| 技术 | 职责 | 执行时机 |
|:---|:---|:---|
| **描述符** (`FieldBase`) | 字段校验（类型、范围、长度） | 每次 `obj.field = value` 赋值时 |
| **`__init_subclass__`** | 收集字段、生成 `__init__`/`__repr__` | 类定义时 |
| **装饰器** (`@serializable`) | 添加序列化/反序列化能力 | 类定义时 |

> 💡 **对比 Pydantic**：我们用 ~80 行代码实现了 Pydantic 的核心功能（字段校验 + 序列化）。真正的 Pydantic 还多了：嵌套模型、自定义验证器、JSON Schema 生成、性能优化（Rust 核心）等。但底层设计思路是一样的——**声明式定义，运行时校验**。

---

## 8. 最佳实践与反模式

元编程很强大，但也很容易**用力过猛**。这一章帮你建立正确的判断标准：什么时候该用，什么时候不该用，以及哪些常见写法是"反模式"。

### 8.1 装饰器的适用场景与过度使用

**✅ 适合用装饰器的场景（横切关注点）：**

| 场景 | 示例 | 理由 |
|:---|:---|:---|
| 日志记录 | `@log_calls` | 和业务逻辑无关，但每个函数都需要 |
| 性能监控 | `@timer`、`@profile` | 测量执行时间，不侵入业务代码 |
| 缓存 | `@cache`、`@lru_cache` | 通用优化策略 |
| 重试机制 | `@retry(max_attempts=3)` | 网络请求、API 调用的通用容错 |
| 权限检查 | `@require_role("admin")` | Web 框架中的常见模式 |
| 输入校验 | `@type_check` | 运行时类型检查 |

**❌ 不适合用装饰器的场景：**

```python
# 反模式 1：装饰器里塞了太多业务逻辑
@validate_input
@check_permissions
@rate_limit
@cache_result
@log_calls
@transform_output
def get_user(user_id):   # 原函数只有一行，但有 6 个装饰器
    return db.get(user_id)
# 问题：调试时看不到 get_user 的真实行为，调用栈全是 wrapper

# 反模式 2：装饰器改变了函数的语义
def must_return_list(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return [result]         # 把返回值偷偷包成列表
    return wrapper

@must_return_list
def get_name():
    return "Alice"

print(get_name())  # ['Alice']  ← 调用者不知道返回类型被改了！
```

> 💡 **经验法则**：装饰器应该是**透明的增强**——加了装饰器，函数的输入输出语义不变，只是多了"副作用"（日志、缓存、校验）。如果装饰器改变了函数的返回值类型或核心行为，那就不该用装饰器。

### 8.2 元类 vs __init_subclass__：如何选择

这是最常见的选择困难症。用一个决策流程图来解决：

```
你需要在"类被定义时"做一些事情？
│
├── 只需要在子类定义时执行逻辑（注册、校验、注入属性）？
│   └── ✅ 用 __init_subclass__（简单、清晰、够用）
│
├── 需要修改类的创建过程（改类名、改父类、替换方法）？
│   └── ✅ 用元类 __new__
│
├── 需要控制类体的命名空间（自定义字典）？
│   └── ✅ 用元类 __prepare__
│
├── 需要让描述符知道自己的属性名？
│   └── ✅ 用 __set_name__（不需要元类）
│
└── 不确定？
    └── ✅ 先用 __init_subclass__，不够再升级到元类
```

**实际项目中的分布：**

| 技术 | 使用频率 | 典型场景 |
|:---|:---|:---|
| 装饰器 | ⭐⭐⭐⭐⭐ 非常高 | 日志、缓存、权限、路由 |
| 描述符 | ⭐⭐⭐ 中等 | ORM 字段、数据校验、惰性属性 |
| `__init_subclass__` | ⭐⭐ 偶尔 | 插件注册、子类校验 |
| `__set_name__` | ⭐⭐ 偶尔 | 配合描述符使用 |
| 元类 | ⭐ 很少 | 框架开发（ORM、序列化框架、API 框架） |

> 💡 **Tim Peters（Python 之禅作者）说过**："元类的应用场景比大多数人想象的要少 99%。" 在你写 `metaclass=` 之前，先问自己：`__init_subclass__` 能不能解决？

### 8.3 可读性 vs 灵活性：Python 之禅的平衡

Python 之禅（`import this`）有两句经典格言，恰好可以指导元编程的使用：

```
Explicit is better than implicit.       — 显式优于隐式
Simple is better than complex.          — 简单优于复杂
```

**元编程的最大风险就是"隐式"**——代码的行为不是写在你看到的地方，而是藏在装饰器、描述符、元类里。

```python
# ──────────────────────────────────────────
# 例子：哪个版本更好？
# ──────────────────────────────────────────

# 版本 A：用元类自动注入方法（隐式）
class User(metaclass=AutoMethodMeta):
    name: str
    age: int
    # 读代码的人：__init__ 在哪？to_dict 在哪？什么魔法？

# 版本 B：用 dataclass（显式）
from dataclasses import dataclass, asdict

@dataclass
class User:
    name: str
    age: int
    # 读代码的人：哦，dataclass 会生成 __init__、__repr__，这是标准库的东西

# 版本 C：手动写（最显式）
class User:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    # 读代码的人：一目了然
```

**选择标准：**

| 指标 | 手动写 | dataclass/标准库 | 自定义元编程 |
|:---|:---|:---|:---|
| 可读性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| 代码量 | 多 | 少 | 最少 |
| 灵活性 | 高 | 中 | 最高 |
| 新人友好度 | 高 | 高 | 低 |
| 适用场景 | 少量类 | 大部分场景 | 框架开发 |

> 💡 **黄金法则**：优先使用标准库工具（`dataclass`、`property`、`functools.wraps`）。只有当标准工具无法满足需求时，才考虑自定义元编程。写给自己看的代码可以炫技，写给团队看的代码要**让新人能读懂**。

### 8.4 常见反模式集锦

#### ❌ 反模式 1：忘记 `@functools.wraps`

```python
# 错误 ——  wrapper 丢失了原函数信息
def my_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper  # wrapper.__name__ == 'wrapper'，不是原函数名

# 正确
def my_decorator(func):
    @functools.wraps(func)  # ← 永远加上这一行
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

#### ❌ 反模式 2：在描述符的 `__set__` 里存值到 `self` 而不是 `obj`

```python
# 错误 —— 所有实例共享同一个值！
class BadField:
    def __set__(self, obj, value):
        self.value = value     # ← 存到描述符实例上，所有对象共享！
    def __get__(self, obj, objtype=None):
        return self.value

# 正确 —— 值存到每个实例的 __dict__ 里
class GoodField:
    def __set_name__(self, owner, name):
        self.name = name
    def __set__(self, obj, value):
        obj.__dict__[self.name] = value   # ← 存到实例的 __dict__
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.name)
```

#### ❌ 反模式 3：元类冲突

```python
# 如果两个父类使用不同的元类，Python 会报错
class MetaA(type): pass
class MetaB(type): pass

class A(metaclass=MetaA): pass
class B(metaclass=MetaB): pass

class C(A, B): pass  # TypeError: metaclass conflict!

# 解决方案：让 MetaB 继承 MetaA，或使用 __init_subclass__ 代替元类
```

#### ❌ 反模式 4：装饰器不处理异常

```python
# 错误 —— 装饰器吞掉了异常，调用者不知道出错了
def silent_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            pass          # ← 异常被吞掉了！静默失败是最难调试的 bug
    return wrapper

# 正确 —— 至少要记录日志
def log_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"❌ {func.__name__} 出错: {e}")
            raise         # ← 记录后重新抛出，让调用者决定怎么处理
    return wrapper
```

---

**全文知识体系总图：**

```
Python 装饰器与元编程 —— 从入门到精通

📦 函数是对象
  └─ 高阶函数 → 闭包 → 装饰器

🎀 装饰器
  ├─ 基础：@语法糖 = func = decorator(func)
  ├─ 进阶：functools.wraps / 带参装饰器 / 类装饰器
  └─ 实战：计时器 / 缓存 / 重试 / 权限

🔗 描述符
  ├─ 协议：__get__ / __set__ / __delete__
  ├─ 数据 vs 非数据描述符（优先级）
  └─ 实战：property 本质 / 字段校验

🪝 轻量钩子
  ├─ __init_subclass__：继承即注册
  └─ __set_name__：自动注入属性名

🧬 元类
  ├─ type()：类的类
  ├─ __new__ / __init__ / __prepare__
  └─ 实战：简易 ORM

🏗️ 综合实战
  └─ 声明式验证框架 = 描述符 + __init_subclass__ + 装饰器
```
