# 第二章 五大数据类型的 Python 操作

> 本章目标：掌握 String / Hash / List / Set / Sorted Set 在 Python 中的完整操作，每种类型配一个真实业务场景。

---

## 2.1 String：缓存、计数器、分布式 ID

String 是 Redis 最基础的类型——Key 对应一个字符串值。但它能做的远不止"存个字符串"。

### 基本读写

```python
import redis

r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)

# SET / GET
r.set("user:1001:name", "张三")
print(r.get("user:1001:name"))  # '张三'

# 设置过期时间（秒）
r.set("cache:token:abc", "user_1001", ex=3600)  # 1 小时后过期

# 也可以用毫秒
r.set("cache:token:def", "user_1002", px=60000)  # 60 秒

# SETEX 等效写法
r.setex("cache:session:xyz", 1800, "session_data")  # 30 分钟
```

### 不存在才写入（SETNX）

```python
# 只有 key 不存在时才设置，返回 True/False
result = r.setnx("lock:order:1001", "locked")
print(result)  # True（首次）/ False（已存在）

# SET 带 NX 参数（更常用，可以同时设过期时间）
result = r.set("lock:order:1002", "locked", nx=True, ex=30)
print(result)  # True 或 None
```

### 计数器：INCR / DECR

```python
# 文章阅读量
r.set("article:2001:views", 0)
r.incr("article:2001:views")       # 1
r.incr("article:2001:views")       # 2
r.incrby("article:2001:views", 10) # 12
r.decr("article:2001:views")       # 11

print(r.get("article:2001:views"))  # '11'

# 浮点数
r.set("product:price", "9.99")
r.incrbyfloat("product:price", 0.01)  # '10.0'
```

> 💡 `INCR` 是原子操作——即使 100 个并发请求同时 `INCR`，计数也不会出错。这就是为什么 Redis 计数器比数据库 `UPDATE count = count + 1` 更适合高并发场景。

### 批量操作：MSET / MGET

```python
# 一次写多个
r.mset({
    "config:site_name": "我的网站",
    "config:version": "2.0",
    "config:max_upload": "10MB",
})

# 一次读多个
values = r.mget("config:site_name", "config:version", "config:max_upload")
print(values)  # ['我的网站', '2.0', '10MB']
```

### 场景实战：JSON 对象缓存

```python
import json

def cache_user(r: redis.Redis, user_id: int, user_data: dict, ttl: int = 3600):
    """缓存用户信息（JSON 序列化）"""
    key = f"cache:user:{user_id}"
    r.set(key, json.dumps(user_data, ensure_ascii=False), ex=ttl)

def get_cached_user(r: redis.Redis, user_id: int) -> dict | None:
    """读取缓存的用户信息"""
    key = f"cache:user:{user_id}"
    data = r.get(key)
    return json.loads(data) if data else None

# 使用
cache_user(r, 1001, {"name": "张三", "age": 28, "role": "admin"})
user = get_cached_user(r, 1001)
print(user)  # {'name': '张三', 'age': 28, 'role': 'admin'}
```

---

## 2.2 Hash：用户对象、配置存储

Hash 类型可以理解为 **Key 下面挂了一个小字典**——适合存储对象的多个字段，比把整个 JSON 序列化成 String 更灵活。

```
Redis Hash 结构：
┌─────────────────────────────────────┐
│  Key: "user:1001"                   │
│  ┌──────────┬───────────────┐       │
│  │  Field   │  Value        │       │
│  ├──────────┼───────────────┤       │
│  │  name    │  "张三"        │       │
│  │  age     │  "28"         │       │
│  │  email   │  "z@test.com" │       │
│  └──────────┴───────────────┘       │
└─────────────────────────────────────┘
```

### 基本操作

```python
# 写入单个字段
r.hset("user:1001", "name", "张三")

# 写入多个字段
r.hset("user:1001", mapping={
    "age": "28",
    "email": "zhangsan@test.com",
    "role": "admin",
})

# 读取单个字段
name = r.hget("user:1001", "name")
print(name)  # '张三'

# 读取多个字段
values = r.hmget("user:1001", "name", "age", "role")
print(values)  # ['张三', '28', 'admin']

# 读取全部字段
all_fields = r.hgetall("user:1001")
print(all_fields)  # {'name': '张三', 'age': '28', 'email': 'zhangsan@test.com', 'role': 'admin'}
```

### 字段级操作

```python
# 判断字段是否存在
r.hexists("user:1001", "email")  # True

# 删除字段
r.hdel("user:1001", "email")

# 字段计数
r.hlen("user:1001")  # 3

# 获取所有字段名
r.hkeys("user:1001")  # ['name', 'age', 'role']

# 字段自增（适合计数类字段）
r.hincrby("user:1001", "login_count", 1)
```

### Hash vs String：什么时候用哪个？

| | String (JSON) | Hash |
|---|---|---|
| **存储方式** | 整个对象序列化为一个字符串 | 每个字段独立存储 |
| **读取部分字段** | ❌ 必须读取整个 JSON，再解析 | ✅ `HGET` 只读一个字段 |
| **修改单个字段** | ❌ 读→改→写回整个 JSON | ✅ `HSET` 直接改一个字段 |
| **字段数值自增** | ❌ 需要读→解析→加→写回 | ✅ `HINCRBY` 原子操作 |
| **复杂嵌套** | ✅ JSON 支持嵌套结构 | ❌ Value 只能是字符串 |
| **过期控制** | ✅ 整个 Key 设 TTL | ⚠️ 只能整个 Key 过期，不能单个字段 |

> 📌 **经验法则**：字段扁平、需要频繁修改单个字段 → Hash；结构复杂、嵌套多层 → String + JSON。

### 场景实战：购物车

```python
def add_to_cart(r: redis.Redis, user_id: int, product_id: int, quantity: int = 1):
    """添加商品到购物车"""
    key = f"cart:{user_id}"
    r.hincrby(key, str(product_id), quantity)
    r.expire(key, 7 * 24 * 3600)  # 7 天过期

def get_cart(r: redis.Redis, user_id: int) -> dict:
    """获取购物车全部商品"""
    key = f"cart:{user_id}"
    cart = r.hgetall(key)
    return {int(pid): int(qty) for pid, qty in cart.items()}

def remove_from_cart(r: redis.Redis, user_id: int, product_id: int):
    """移除商品"""
    r.hdel(f"cart:{user_id}", str(product_id))

# 使用
add_to_cart(r, 1001, 5001, 2)   # 商品 5001 x 2
add_to_cart(r, 1001, 5002, 1)   # 商品 5002 x 1
add_to_cart(r, 1001, 5001, 1)   # 商品 5001 再加 1，变成 3

print(get_cart(r, 1001))  # {5001: 3, 5002: 1}
```

---

## 2.3 List：消息队列、最新动态

List 是双向链表，支持从两端插入和弹出，天然适合做**队列**和**栈**。

### 基本操作

```python
# 从左端插入（头部）
r.lpush("queue:tasks", "task_1", "task_2", "task_3")
# 结果：task_3, task_2, task_1（后插的在前面）

# 从右端插入（尾部）
r.rpush("queue:tasks", "task_4")
# 结果：task_3, task_2, task_1, task_4

# 查看列表长度
print(r.llen("queue:tasks"))  # 4

# 查看列表内容（0 到 -1 表示全部）
print(r.lrange("queue:tasks", 0, -1))
# ['task_3', 'task_2', 'task_1', 'task_4']

# 从左端弹出（消费）
task = r.lpop("queue:tasks")
print(task)  # 'task_3'

# 从右端弹出
task = r.rpop("queue:tasks")
print(task)  # 'task_4'
```

### 阻塞弹出：BLPOP / BRPOP

普通的 `LPOP` 在列表为空时返回 `None`。如果你想"等到有数据再返回"，用阻塞版本：

```python
# 阻塞等待，最多等 10 秒
# 返回 (key, value) 元组，超时返回 None
result = r.blpop("queue:tasks", timeout=10)
if result:
    key, value = result
    print(f"从 {key} 拿到: {value}")
else:
    print("等待超时，没有新任务")
```

### 场景实战：最新动态 Feed

```python
def publish_post(r: redis.Redis, user_id: int, post_id: int):
    """发布动态，追加到用户的 Feed"""
    key = f"feed:{user_id}"
    r.lpush(key, post_id)
    r.ltrim(key, 0, 99)  # 只保留最新 100 条

def get_feed(r: redis.Redis, user_id: int, page: int = 1, size: int = 10) -> list:
    """获取动态列表（分页）"""
    key = f"feed:{user_id}"
    start = (page - 1) * size
    end = start + size - 1
    return r.lrange(key, start, end)

# 使用
for i in range(1, 21):
    publish_post(r, 1001, i)

page1 = get_feed(r, 1001, page=1, size=5)
print(page1)  # ['20', '19', '18', '17', '16']

page2 = get_feed(r, 1001, page=2, size=5)
print(page2)  # ['15', '14', '13', '12', '11']
```

> 💡 `LTRIM` 是保持列表不无限增长的关键——每次插入后截断，保证内存可控。

---

## 2.4 Set 与 Sorted Set：标签系统、排行榜

### Set：无序不重复集合

```python
# 添加元素
r.sadd("tags:article:2001", "python", "redis", "后端")
r.sadd("tags:article:2002", "python", "fastapi", "异步")

# 查看成员
print(r.smembers("tags:article:2001"))  # {'python', 'redis', '后端'}

# 成员数量
print(r.scard("tags:article:2001"))  # 3

# 判断是否存在
print(r.sismember("tags:article:2001", "python"))  # True
print(r.sismember("tags:article:2001", "java"))    # False

# 删除成员
r.srem("tags:article:2001", "后端")
```

### Set 的集合运算

这是 Set 最强大的能力——交集、并集、差集：

```python
# 两篇文章的共同标签（交集）
common = r.sinter("tags:article:2001", "tags:article:2002")
print(common)  # {'python'}

# 两篇文章的所有标签（并集）
all_tags = r.sunion("tags:article:2001", "tags:article:2002")
print(all_tags)  # {'python', 'redis', 'fastapi', '异步'}

# 文章 2001 有但 2002 没有的标签（差集）
diff = r.sdiff("tags:article:2001", "tags:article:2002")
print(diff)  # {'redis'}
```

### 场景实战：共同关注

```python
def follow(r: redis.Redis, user_id: int, target_id: int):
    """关注"""
    r.sadd(f"following:{user_id}", target_id)
    r.sadd(f"followers:{target_id}", user_id)

def get_mutual_follows(r: redis.Redis, user_a: int, user_b: int) -> set:
    """共同关注"""
    return r.sinter(f"following:{user_a}", f"following:{user_b}")

# A 关注了 X, Y, Z
follow(r, 1001, 2001)
follow(r, 1001, 2002)
follow(r, 1001, 2003)

# B 关注了 Y, Z, W
follow(r, 1002, 2002)
follow(r, 1002, 2003)
follow(r, 1002, 2004)

mutual = get_mutual_follows(r, 1001, 1002)
print(mutual)  # {'2002', '2003'}
```

### Sorted Set（ZSet）：有序集合

每个成员都有一个分数（score），Redis 自动按分数排序。**天然的排行榜数据结构。**

```python
# 添加成员（score, member）
r.zadd("rank:game", {"alice": 1500, "bob": 1200, "carol": 1800, "dave": 900})

# 按分数从高到低排名（前 3 名）
top3 = r.zrevrange("rank:game", 0, 2, withscores=True)
print(top3)  # [('carol', 1800.0), ('alice', 1500.0), ('bob', 1200.0)]

# 按分数从低到高
bottom = r.zrange("rank:game", 0, 1, withscores=True)
print(bottom)  # [('dave', 900.0), ('bob', 1200.0)]

# 查看某人的排名（从 0 开始，zrevrank = 倒序排名）
print(r.zrevrank("rank:game", "alice"))  # 1（第 2 名，从 0 开始）

# 查看某人的分数
print(r.zscore("rank:game", "carol"))  # 1800.0

# 加分
r.zincrby("rank:game", 500, "bob")  # bob: 1200 + 500 = 1700

# 获取分数在某个范围内的成员
mid_range = r.zrangebyscore("rank:game", 1000, 1600, withscores=True)
print(mid_range)  # bob=1500 范围内的成员
```

### 场景实战：热搜排行榜

```python
import time

def record_search(r: redis.Redis, keyword: str):
    """记录一次搜索"""
    key = f"hot:search:{time.strftime('%Y%m%d')}"
    r.zincrby(key, 1, keyword)
    r.expire(key, 2 * 24 * 3600)  # 保留 2 天

def get_hot_searches(r: redis.Redis, top_n: int = 10) -> list:
    """获取今日热搜 Top N"""
    key = f"hot:search:{time.strftime('%Y%m%d')}"
    return r.zrevrange(key, 0, top_n - 1, withscores=True)

# 模拟搜索
for _ in range(50): record_search(r, "Python 教程")
for _ in range(30): record_search(r, "Redis 入门")
for _ in range(80): record_search(r, "ChatGPT")
for _ in range(20): record_search(r, "FastAPI")

hot = get_hot_searches(r, top_n=3)
for rank, (keyword, score) in enumerate(hot, 1):
    print(f"#{rank} {keyword} ({int(score)} 次)")
# #1 ChatGPT (80 次)
# #2 Python 教程 (50 次)
# #3 Redis 入门 (30 次)
```

---

## 本章小结

| 类型 | Python 核心方法 | 典型场景 |
|------|-----------------|----------|
| **String** | `set/get/incr/mset/mget` | 缓存、计数器、分布式 ID |
| **Hash** | `hset/hget/hgetall/hincrby` | 用户对象、购物车、配置 |
| **List** | `lpush/rpush/lpop/blpop/lrange` | 消息队列、最新动态 Feed |
| **Set** | `sadd/smembers/sinter/sunion` | 标签、共同关注、去重 |
| **Sorted Set** | `zadd/zrevrange/zincrby/zrevrank` | 排行榜、热搜、延迟队列 |

> **下一章预告**：Pipeline、事务与 Lua 脚本——一次网络往返搞定多个操作，批量性能提升 10 倍。
