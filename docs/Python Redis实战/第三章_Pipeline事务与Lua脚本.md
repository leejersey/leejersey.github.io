# 第三章 Pipeline、事务与 Lua 脚本

> 本章目标：掌握三种"批量/原子"操作方式——Pipeline 减少网络往返、事务保证原子执行、Lua 脚本实现自定义原子逻辑。

---

## 3.1 Pipeline：批量操作提升 10x 性能

### 问题：逐条命令的网络开销

每执行一条 Redis 命令，客户端都要经历一次完整的网络往返（RTT）：

```
逐条执行 100 条命令：

客户端 ──SET──→ Redis ──OK──→ 客户端    RTT 1
客户端 ──SET──→ Redis ──OK──→ 客户端    RTT 2
客户端 ──SET──→ Redis ──OK──→ 客户端    RTT 3
...
客户端 ──SET──→ Redis ──OK──→ 客户端    RTT 100

总耗时 ≈ 100 × RTT（假设 RTT = 0.5ms，则 50ms）
```

如果 Redis 在远程服务器（RTT = 2ms），100 条命令就要 **200ms**——大部分时间花在等网络上，而不是 Redis 执行。

### Pipeline：打包发送

Pipeline 把多条命令打包成一次网络请求，一次性发送、一次性接收所有响应：

```
Pipeline 执行 100 条命令：

客户端 ──[SET, SET, SET, ... ×100]──→ Redis
客户端 ←──[OK, OK, OK, ... ×100]────  Redis

总耗时 ≈ 1 × RTT + 100 条命令的执行时间（约 1-2ms）
```

### Python 实现

```python
import redis
import time

r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)

# ── 对比：逐条执行 ──
start = time.time()
for i in range(1000):
    r.set(f"bench:normal:{i}", f"value_{i}")
normal_time = time.time() - start
print(f"逐条执行 1000 次: {normal_time:.3f}s")

# ── 对比：Pipeline 执行 ──
start = time.time()
pipe = r.pipeline()  # 创建 Pipeline
for i in range(1000):
    pipe.set(f"bench:pipe:{i}", f"value_{i}")
pipe.execute()  # 一次性发送并执行
pipe_time = time.time() - start
print(f"Pipeline 1000 次: {pipe_time:.3f}s")

print(f"提速: {normal_time / pipe_time:.1f}x")
```

典型输出（本地 Redis）：

```
逐条执行 1000 次: 0.152s
Pipeline 1000 次: 0.018s
提速: 8.4x
```

远程 Redis 的提速更明显，可达 **20-50x**。

### Pipeline 读取结果

Pipeline 不是"发了就不管"，每条命令的结果都会按顺序返回：

```python
pipe = r.pipeline()
pipe.set("demo:a", "1")
pipe.set("demo:b", "2")
pipe.get("demo:a")
pipe.get("demo:b")
pipe.incr("demo:a")

results = pipe.execute()
print(results)  # [True, True, '1', '2', 2]
#                  SET    SET   GET   GET  INCR
```

### 上下文管理器写法

```python
# 推荐：用 with 自动管理
with r.pipeline() as pipe:
    pipe.set("ctx:key1", "value1")
    pipe.set("ctx:key2", "value2")
    pipe.get("ctx:key1")
    results = pipe.execute()
    print(results)  # [True, True, 'value1']
```

### Pipeline 注意事项

| 注意点 | 说明 |
|--------|------|
| **不是原子的** | Pipeline 只是批量发送，不保证中间不被其他命令插入 |
| **内存** | 一次打包太多命令会占用客户端内存，建议每批 ≤ 10000 条 |
| **错误处理** | 某条命令失败不影响其他命令，需要逐个检查 results |

> ⚠️ **关键区别**：Pipeline ≠ 事务。Pipeline 只优化网络，不保证原子性。需要原子性请用事务或 Lua。

---

## 3.2 事务（MULTI/EXEC）：原子性保障

### 什么是 Redis 事务？

Redis 事务保证一组命令**按顺序、不被中断地执行**。不会出现"执行到一半被其他客户端插队"的情况。

```
MULTI          ← 开始事务
SET key1 val1  ← 命令入队（不立即执行）
SET key2 val2  ← 命令入队
INCR key3      ← 命令入队
EXEC           ← 一次性执行所有入队的命令
```

### Python 实现

```python
# Pipeline 默认就带事务模式
pipe = r.pipeline(transaction=True)  # 默认 True
pipe.set("tx:balance:A", "1000")
pipe.set("tx:balance:B", "500")
pipe.execute()

# 也可以显式用 multi()
pipe = r.pipeline()
pipe.multi()
pipe.decrby("tx:balance:A", 100)  # A 扣 100
pipe.incrby("tx:balance:B", 100)  # B 加 100
results = pipe.execute()
print(results)  # [900, 600]
```

### WATCH：乐观锁

事务的一个常见需求是"先读后写"——但读和写之间，值可能被别人改了。`WATCH` 解决这个问题：

```python
def transfer(r: redis.Redis, from_user: str, to_user: str, amount: int) -> bool:
    """安全转账：用 WATCH 实现乐观锁"""
    key_from = f"tx:balance:{from_user}"
    key_to = f"tx:balance:{to_user}"

    with r.pipeline() as pipe:
        while True:
            try:
                # 监视 key，如果在 EXEC 之前被修改，事务自动失败
                pipe.watch(key_from, key_to)

                # 读取当前余额（此时还不在事务中）
                balance_from = int(pipe.get(key_from) or 0)
                balance_to = int(pipe.get(key_to) or 0)

                if balance_from < amount:
                    pipe.unwatch()
                    print("余额不足")
                    return False

                # 开始事务
                pipe.multi()
                pipe.set(key_from, balance_from - amount)
                pipe.set(key_to, balance_to + amount)
                pipe.execute()  # 如果被 WATCH 的 key 被修改了，这里会抛异常
                return True

            except redis.WatchError:
                # 被其他客户端修改了，重试
                print("冲突，重试...")
                continue

# 初始化余额
r.set("tx:balance:alice", 1000)
r.set("tx:balance:bob", 500)

# 转账
transfer(r, "alice", "bob", 200)
print(r.get("tx:balance:alice"))  # '800'
print(r.get("tx:balance:bob"))    # '700'
```

### Redis 事务的局限性

| 特性 | Redis 事务 | 关系型数据库事务 |
|------|------------|-----------------|
| **原子性** | ✅ 全部执行（但不回滚） | ✅ 全部执行或全部回滚 |
| **隔离性** | ✅ 执行期间不被中断 | ✅ 多种隔离级别 |
| **回滚** | ❌ 不支持 | ✅ 支持 |
| **条件判断** | ❌ 命令入队时不能用结果做判断 | ✅ IF/ELSE 自由 |

> 关键限制：Redis 事务**没有回滚**——如果其中一条命令报错（比如对 String 执行 LPUSH），其他命令仍会执行。需要回滚能力的场景用 Lua 脚本。

---

## 3.3 Lua 脚本：自定义原子操作

### 为什么需要 Lua？

事务的局限在于：**命令入队时无法使用中间结果做判断**。比如"读取余额，如果 >= 100 就扣款"这个逻辑，事务做不了——你不能在 MULTI 里面写 if-else。

Lua 脚本在 Redis 服务端执行，是**完全原子的**，且可以包含任意逻辑：

```
客户端                          Redis 服务端
  │                                │
  │──── EVAL lua_script ──────────→│
  │                                │  ┌──────────────────┐
  │                                │  │ 执行 Lua 脚本     │
  │                                │  │ (读→判断→写)      │
  │                                │  │ 全程原子，不被打断 │
  │                                │  └──────────────────┘
  │←──── 返回结果 ────────────────│
```

### 基本用法

```python
# 最简单的 Lua 脚本
script = "return 'Hello from Lua!'"
result = r.eval(script, 0)  # 0 表示没有 key 参数
print(result)  # 'Hello from Lua!'
```

### 在 Lua 中操作 Redis

Lua 脚本中用 `redis.call()` 执行 Redis 命令：

```python
# Lua 脚本：读取 key 的值并加 10
script = """
local current = redis.call('GET', KEYS[1])
if current then
    local new_val = tonumber(current) + ARGV[1]
    redis.call('SET', KEYS[1], new_val)
    return new_val
else
    redis.call('SET', KEYS[1], ARGV[1])
    return tonumber(ARGV[1])
end
"""

r.set("lua:counter", "100")
result = r.eval(script, 1, "lua:counter", 10)  # 1 个 key，参数为 10
print(result)  # 110
```

参数说明：
- `KEYS[1]`：第一个 key 参数（Lua 下标从 1 开始）
- `ARGV[1]`：第一个附加参数
- `eval(script, numkeys, key1, key2, ..., arg1, arg2, ...)`

### 注册脚本：避免重复传输

每次 `eval` 都会把整个脚本发送给 Redis。对于频繁调用的脚本，用 `register_script` 只传一次：

```python
# 注册脚本（只传一次，后续用 SHA 调用）
lua_incr_if_exists = r.register_script("""
local current = redis.call('GET', KEYS[1])
if current then
    return redis.call('INCRBY', KEYS[1], ARGV[1])
else
    return nil
end
""")

r.set("lua:score", "50")

# 调用已注册的脚本
result = lua_incr_if_exists(keys=["lua:score"], args=[25])
print(result)  # 75

# key 不存在时返回 None
result = lua_incr_if_exists(keys=["lua:nonexist"], args=[25])
print(result)  # None
```

### 场景实战：安全扣库存

```python
# 原子扣库存：检查库存 → 扣减 → 返回结果
deduct_stock = r.register_script("""
local stock = tonumber(redis.call('GET', KEYS[1]))
if stock == nil then
    return -1  -- key 不存在
end
local amount = tonumber(ARGV[1])
if stock < amount then
    return -2  -- 库存不足
end
redis.call('DECRBY', KEYS[1], amount)
return stock - amount  -- 返回剩余库存
""")

# 初始化库存
r.set("stock:product:5001", 10)

# 扣库存
result = deduct_stock(keys=["stock:product:5001"], args=[3])
print(f"剩余库存: {result}")  # 7

result = deduct_stock(keys=["stock:product:5001"], args=[8])
print(f"结果: {result}")  # -2（库存不足）

result = deduct_stock(keys=["stock:product:5001"], args=[5])
print(f"剩余库存: {result}")  # 2
```

### 三者对比

| | Pipeline | 事务 (MULTI/EXEC) | Lua 脚本 |
|---|---|---|---|
| **网络往返** | 1 次 | 1 次 | 1 次 |
| **原子性** | ❌ 不保证 | ✅ 不被插队 | ✅ 完全原子 |
| **条件判断** | ❌ | ❌ 入队时无法判断 | ✅ 任意逻辑 |
| **回滚** | ❌ | ❌ | ❌（但可以自己控制） |
| **性能** | 最快 | 快 | 稍慢（脚本解析） |
| **适合** | 批量无关联操作 | 简单多步原子操作 | 需要条件判断的原子操作 |

> 📌 **选择建议**：
> - 只是想批量提速 → **Pipeline**
> - 多条命令不被中断 → **事务**
> - 需要"读→判断→写"的原子逻辑 → **Lua 脚本**

---

## 本章小结

| 知识点 | 要点 |
|--------|------|
| Pipeline | 批量打包发送，减少网络往返，提速 10x+ |
| 事务 | `pipeline(transaction=True)`，WATCH 实现乐观锁 |
| Lua 脚本 | `eval()` / `register_script()`，服务端原子执行 |
| 三者关系 | Pipeline 优化网络，事务保证不中断，Lua 支持条件逻辑 |
| 扣库存 | 经典 Lua 场景：检查→扣减→返回，全程原子 |

> **下一章预告**：缓存模式实战——Cache-Aside 完整实现、穿透/雪崩/击穿的 Python 解法、用装饰器优雅封装缓存逻辑。
