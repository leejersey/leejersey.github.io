# 消息队列实战（RabbitMQ/Kafka）

> 从原理到生产——涵盖消息队列核心概念、RabbitMQ 与 Kafka 深度实战、消息可靠性保障、死信队列、延迟消息、事件驱动架构、性能调优与运维监控，一套完整的 Python 消息队列工程实践。

---

## 1. 消息队列核心概念

### 1.1 消息队列解决什么问题？

```
消息队列的三大核心价值：

  1. 解耦
     ❌ 订单服务 → 直接调短信服务 + 库存服务 + 积分服务（强耦合）
     ✅ 订单服务 → 发消息 → 短信/库存/积分各自消费（松耦合）

  2. 异步
     ❌ 下单 → 扣库存(50ms) → 发短信(200ms) → 加积分(100ms) = 350ms
     ✅ 下单 → 发消息(5ms) = 5ms（其他异步处理）

  3. 削峰填谷
     ❌ 秒杀 10000 QPS 直接打到数据库 → 崩溃
     ✅ 秒杀请求先入队列 → 消费者按自己能力匀速处理
```

### 1.2 核心概念：Producer / Broker / Consumer

```
消息队列的三个角色：

  Producer（生产者）→ Broker（消息中间件）→ Consumer（消费者）
     发送消息            存储 + 路由            接收 + 处理

  关键概念：
  ┌────────────┬──────────────────────────────────┐
  │ Message    │ 消息体 + 元数据（Header/属性）     │
  │ Queue      │ 消息的存储容器（FIFO）             │
  │ Topic      │ 消息的逻辑分类（Kafka 用语）       │
  │ Exchange   │ 路由器，决定消息去哪个队列（RabbitMQ）│
  │ Offset     │ 消费者在分区中的位置（Kafka）       │
  └────────────┴──────────────────────────────────┘
```

### 1.3 消息模型：点对点 vs 发布订阅

```
点对点（P2P）：一条消息只被一个消费者消费
  Producer → Queue → Consumer A  ✅ 收到
                  ↛ Consumer B  ❌ 收不到
  场景：任务分发（每个任务只需处理一次）

发布订阅（Pub/Sub）：一条消息被多个消费者消费
  Producer → Exchange → Queue A → Consumer A  ✅ 收到
                     → Queue B → Consumer B  ✅ 也收到
  场景：事件广播（下单后通知短信+库存+积分）
```

### 1.4 RabbitMQ vs Kafka：选型指南

| 维度 | RabbitMQ | Kafka |
|:---|:---|:---|
| **定位** | 消息队列（通用） | 分布式日志/流平台 |
| **吞吐量** | 万级 QPS | 百万级 QPS |
| **消息模型** | Exchange + Queue | Topic + Partition |
| **消费方式** | Push（Broker 推给消费者） | Pull（消费者主动拉取） |
| **消息保留** | 消费后删除 | 按时间/大小保留 |
| **消息顺序** | 单队列有序 | 单分区有序 |
| **协议** | AMQP（标准协议） | 自有协议 |
| **适用场景** | 业务消息、RPC、任务队列 | 日志采集、事件流、大数据 |
| **运维复杂度** | 中（管理面板友好） | 高（需要 ZooKeeper/KRaft） |

```
选型口诀：
  业务消息、需要灵活路由 → RabbitMQ
  海量日志、事件流、需要回溯 → Kafka
  不确定 → 先 RabbitMQ，后期再迁
```

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **解耦** | 生产者不需要知道消费者是谁 |
| **异步** | 发完消息就返回，不等处理结果 |
| **削峰** | 队列做缓冲，匀速消费 |
| **选型** | 业务消息→RabbitMQ，事件流→Kafka |

---

## 2. RabbitMQ 快速上手

### 2.1 Docker 快速部署

```yaml
# docker-compose.yml
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"     # AMQP 协议端口
      - "15672:15672"   # 管理面板
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: admin123
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

volumes:
  rabbitmq_data:

# 启动后访问 http://localhost:15672 管理面板
```

### 2.2 核心组件：Exchange / Queue / Binding

```
RabbitMQ 消息流转：

  Producer → Exchange → Binding(routing_key) → Queue → Consumer
              路由器        路由规则              存储      消费

  Exchange：决定消息去哪个队列（不存储消息）
  Queue：   存储消息，等待消费者取走
  Binding：  Exchange 和 Queue 之间的路由规则
  Routing Key：消息的路由标签（类似发件地址）
```

### 2.3 四种 Exchange 类型详解

```
1. Direct（直连）：routing_key 精确匹配
   消息 routing_key="order.created" → 只去绑定了 "order.created" 的队列

2. Topic（主题）：routing_key 模式匹配（* 和 #）
   "order.*"   → 匹配 order.created、order.paid
   "order.#"   → 匹配 order.created、order.item.added
   * = 一个词，# = 零或多个词

3. Fanout（扇出）：广播，忽略 routing_key
   消息 → 发给所有绑定的队列（适合事件广播）

4. Headers（头匹配）：按消息 Header 属性匹配（少用）
```

### 2.4 Python 客户端：aio-pika 异步实战

```python
import aio_pika
import json

# ── 发布消息 ──
async def publish_message(routing_key: str, data: dict):
    connection = await aio_pika.connect_robust("amqp://admin:admin123@localhost/")
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("app_events", aio_pika.ExchangeType.TOPIC,
                                                   durable=True)
        message = aio_pika.Message(
            body=json.dumps(data).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # 持久化
        )
        await exchange.publish(message, routing_key=routing_key)

# ── 消费消息 ──
async def consume_messages():
    connection = await aio_pika.connect_robust("amqp://admin:admin123@localhost/")
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)  # 预取上限

        exchange = await channel.declare_exchange("app_events", aio_pika.ExchangeType.TOPIC,
                                                   durable=True)
        queue = await channel.declare_queue("notification_queue", durable=True)
        await queue.bind(exchange, routing_key="order.*")

        async with queue.iterator() as messages:
            async for message in messages:
                async with message.process():  # 自动 ACK
                    data = json.loads(message.body)
                    print(f"收到: {message.routing_key} → {data}")
```

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Exchange** | 路由器，决定消息去哪 |
| **Direct** | routing_key 精确匹配 |
| **Topic** | 模式匹配，* 一词 # 多词 |
| **Fanout** | 广播，所有绑定队列都收到 |

---

## 3. RabbitMQ 生产级实践

### 3.1 消息确认机制（ACK / NACK / Reject）

```python
# ── 手动 ACK 模式（生产必须用手动 ACK）──
async def consume_with_manual_ack():
    connection = await aio_pika.connect_robust("amqp://admin:admin123@localhost/")
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue("task_queue", durable=True)
        
        async with queue.iterator() as messages:
            async for message in messages:
                try:
                    data = json.loads(message.body)
                    await process_task(data)
                    await message.ack()       # ✅ 处理成功 → 确认
                except RecoverableError:
                    await message.nack(requeue=True)   # 🔄 可恢复 → 重回队列
                except FatalError:
                    await message.reject(requeue=False) # ❌ 不可恢复 → 丢弃(进死信)
```

```
三种确认方式：

  ACK         → 处理成功，消息从队列删除
  NACK        → 处理失败，requeue=True 重回队列头部
  Reject      → 拒绝，requeue=False 进死信队列
```

### 3.2 消息持久化与可靠性保障

```python
# 可靠性三件套：Exchange 持久 + Queue 持久 + Message 持久
exchange = await channel.declare_exchange("events", ExchangeType.TOPIC, durable=True)  # ①
queue = await channel.declare_queue("order_queue", durable=True)                       # ②
message = aio_pika.Message(
    body=data,
    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # ③ 持久化到磁盘
)

# Publisher Confirm（确认消息已到达 Broker）
channel = await connection.channel()
await channel.set_confirm_selects()  # 开启 Publisher Confirm
try:
    await exchange.publish(message, routing_key="order.created")
    # 如果 Broker 未确认，publish 会抛异常
except aio_pika.exceptions.DeliveryError:
    logger.error("消息发送失败，需要重试")
```

### 3.3 死信队列（DLX）：失败消息兜底

```python
# 死信队列：消息被 reject / TTL 过期 / 队列满时，转到指定队列

# 声明死信 Exchange + 死信 Queue
dlx = await channel.declare_exchange("dlx", ExchangeType.DIRECT, durable=True)
dlq = await channel.declare_queue("dead_letters", durable=True)
await dlq.bind(dlx, routing_key="dead")

# 业务队列绑定死信
main_queue = await channel.declare_queue("order_queue", durable=True, arguments={
    "x-dead-letter-exchange": "dlx",           # 死信发到哪个 Exchange
    "x-dead-letter-routing-key": "dead",        # 死信的 routing_key
    "x-max-length": 10000,                      # 队列最大长度（超出进死信）
})

# 消费死信队列（告警 / 人工处理）
async def consume_dead_letters():
    async with dlq.iterator() as messages:
        async for message in messages:
            async with message.process():
                data = json.loads(message.body)
                logger.error(f"死信: {data}")
                await alert_team(data)     # 通知团队
                await save_to_db(data)     # 存库待人工处理
```

### 3.4 延迟消息：订单超时自动取消

```python
# 方式一：TTL + 死信（RabbitMQ 原生）
delay_queue = await channel.declare_queue("delay_30min", durable=True, arguments={
    "x-message-ttl": 1800000,                  # 30 分钟 TTL
    "x-dead-letter-exchange": "app_events",     # 到期后转到业务 Exchange
    "x-dead-letter-routing-key": "order.timeout",
})

# 下单时发到延迟队列
await channel.default_exchange.publish(
    aio_pika.Message(body=json.dumps({"order_id": 123}).encode(),
                     delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
    routing_key="delay_30min",
)

# 30 分钟后，消息自动到达 order.timeout → 消费者检查订单是否已支付
async def handle_order_timeout(data):
    order = await order_repo.get(data["order_id"])
    if order.status == "pending":
        await order_repo.update(order.id, status="cancelled")
        await inventory_service.release(order.product_id, order.quantity)
```

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **手动 ACK** | 处理完才确认，防止消息丢失 |
| **持久化三件套** | Exchange + Queue + Message 都要 durable |
| **死信队列** | reject/过期/超长 → 兜底队列 |
| **延迟消息** | TTL + DLX 实现定时任务 |

---

## 4. Kafka 快速上手

### 4.1 Kafka 架构：Broker / Topic / Partition

```
Kafka 架构：

  Producer → Broker Cluster → Consumer Group
              │
              ├── Topic: "orders"
              │   ├── Partition 0: [msg1, msg4, msg7, ...]
              │   ├── Partition 1: [msg2, msg5, msg8, ...]
              │   └── Partition 2: [msg3, msg6, msg9, ...]
              │
              └── Topic: "users"
                  ├── Partition 0: [...]
                  └── Partition 1: [...]

  关键区别（vs RabbitMQ）：
  - 消息写入分区后不删除（按保留策略留存）
  - 消费者通过 Offset 控制读取位置
  - 可以回溯重新消费历史消息
```

### 4.2 消息分区与顺序性保证

```
分区策略：

  无 Key  → 轮询分配到各分区（负载均衡，无序）
  有 Key  → hash(key) % 分区数（同 Key 同分区，有序）

  例：key=user_id → 同一用户的所有消息在同一分区 → 保证顺序

  ⚠️ 注意：只有"单分区内"是有序的，跨分区无法保证顺序
```

### 4.3 Consumer Group 与负载均衡

```
Consumer Group：一组消费者共同消费一个 Topic

  Topic: orders (3 个分区)
  Consumer Group: order-processors

  情况 1：3 个消费者
    Consumer A → Partition 0
    Consumer B → Partition 1
    Consumer C → Partition 2     ← 完美负载均衡

  情况 2：2 个消费者
    Consumer A → Partition 0, 1  ← A 多分一个
    Consumer B → Partition 2

  情况 3：4 个消费者
    Consumer A → Partition 0
    Consumer B → Partition 1
    Consumer C → Partition 2
    Consumer D → 空闲            ← 消费者 > 分区数，有人闲着

  规则：消费者数 ≤ 分区数，否则浪费
```

### 4.4 Python 客户端：aiokafka 异步实战

```python
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json

# ── 生产者 ──
async def produce_messages():
    producer = AIOKafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda v: json.dumps(v).encode(),
        key_serializer=lambda k: k.encode() if k else None,
    )
    await producer.start()
    try:
        await producer.send_and_wait(
            "orders",
            value={"order_id": 123, "user_id": 456, "amount": 99.9},
            key="user_456",  # 同用户的消息分到同一分区
        )
    finally:
        await producer.stop()

# ── 消费者 ──
async def consume_messages():
    consumer = AIOKafkaConsumer(
        "orders",
        bootstrap_servers="localhost:9092",
        group_id="order-processors",
        value_deserializer=lambda v: json.loads(v),
        auto_offset_reset="earliest",  # 从最早未消费的开始
    )
    await consumer.start()
    try:
        async for msg in consumer:
            print(f"分区{msg.partition} 偏移{msg.offset}: {msg.value}")
            await process_order(msg.value)
    finally:
        await consumer.stop()
```

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Partition** | 分区 = 有序日志，并行消费单位 |
| **Key 分区** | 同 Key 同分区，保证单用户有序 |
| **Consumer Group** | 一组消费者分摊分区，消费者≤分区数 |
| **Offset** | 消费位置指针，可回溯 |

---

## 5. Kafka 生产级实践

### 5.1 Offset 管理：自动提交 vs 手动提交

```python
# ── 自动提交（默认，可能丢消息）──
consumer = AIOKafkaConsumer("orders", group_id="g1",
                            enable_auto_commit=True,
                            auto_commit_interval_ms=5000)  # 每 5 秒自动提交

# ── 手动提交（生产推荐）──
consumer = AIOKafkaConsumer("orders", group_id="g1",
                            enable_auto_commit=False)

async for msg in consumer:
    await process_order(msg.value)
    await consumer.commit()  # 处理完才提交 Offset
```

```
自动提交风险：

  1. 消费者拿到消息 → 自动提交 Offset → 处理异常 → 消息丢失
  2. 消费者拿到消息 → 处理成功 → 没来得及提交 → 重启后重复消费

  手动提交：处理成功后再提交，保证 At-Least-Once
```

### 5.2 消息投递语义：At-Least-Once / Exactly-Once

```
三种投递语义：

  At-Most-Once  ：最多一次（可能丢消息）
    → 先提交 Offset，再处理。处理失败就丢了
  
  At-Least-Once ：至少一次（可能重复，最常用）
    → 先处理，再提交 Offset。重启可能重复处理
    → 解决重复：消费端做幂等（去重表/唯一 ID）
  
  Exactly-Once  ：恰好一次（Kafka 事务）
    → Kafka 0.11+ 支持事务性 Producer + Consumer
    → 性能开销大，通常用 At-Least-Once + 幂等替代
```

### 5.3 数据保留策略与日志压缩

```
保留策略（retention）：

  # 按时间保留（默认 7 天）
  retention.ms=604800000

  # 按大小保留（每分区最大 1GB）
  retention.bytes=1073741824

日志压缩（compaction）：
  # 保留每个 Key 的最新消息，删除旧版本
  cleanup.policy=compact
  
  适用场景：用户状态快照、配置变更
  Key=user_123 → 只保留最新状态
```

### 5.4 Schema Registry：消息格式管理

```python
# 用 Avro Schema 管理消息格式（防止生产者乱改格式导致消费者崩溃）
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

schema_str = """
{
  "type": "record",
  "name": "OrderEvent",
  "fields": [
    {"name": "order_id", "type": "int"},
    {"name": "user_id", "type": "int"},
    {"name": "amount", "type": "float"},
    {"name": "status", "type": "string"}
  ]
}
"""

# Schema Registry 的作用：
# 1. 生产者发送时自动校验格式
# 2. 消费者接收时自动反序列化
# 3. Schema 变更有兼容性检查（向前/向后兼容）
```

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **手动提交** | 处理完才 commit，保证 At-Least-Once |
| **幂等消费** | 消费端去重，解决重复问题 |
| **数据保留** | 按时间（7天）或大小（1GB）保留 |
| **Schema Registry** | 强制消息格式校验，防止格式不兼容 |

---

## 6. 事件驱动架构实战

### 6.1 事件设计规范：命名、版本、Schema

```python
# 事件标准格式
{
    "event_id": "uuid-xxx",                    # 全局唯一 ID
    "event_type": "order.created",             # 领域.动作（过去式）
    "event_version": "1.0",                    # 版本号
    "timestamp": "2025-01-01T12:00:00Z",
    "source": "order-service",                 # 来源服务
    "data": {                                  # 业务数据
        "order_id": 123,
        "user_id": 456,
        "amount": 99.9
    },
    "metadata": {                              # 元数据
        "trace_id": "abc123",
        "correlation_id": "def456"
    }
}

# 命名规范：{领域}.{动作}
# order.created   order.paid   order.cancelled
# user.registered user.updated
# payment.completed payment.failed
```

### 6.2 Outbox 模式：数据库 + 消息的原子性

```python
# 问题：写数据库成功但发消息失败 → 数据不一致
# 解决：Outbox 模式（先存事件表，再异步发消息）

# Step 1: 业务操作 + 写事件表在同一个事务
async def create_order(db: AsyncSession, data: dict):
    async with db.begin():
        order = Order(**data, status="pending")
        db.add(order)
        
        # 事件写入 outbox 表（同一事务）
        outbox = OutboxEvent(
            event_type="order.created",
            payload=json.dumps({"order_id": order.id, "user_id": data["user_id"]}),
            status="pending",
        )
        db.add(outbox)

# Step 2: 后台任务轮询 outbox 表 → 发消息 → 标记已发送
async def publish_outbox_events():
    events = await outbox_repo.get_pending(limit=100)
    for event in events:
        try:
            await mq.publish(event.event_type, json.loads(event.payload))
            await outbox_repo.mark_sent(event.id)
        except Exception:
            logger.error(f"Outbox 发送失败: {event.id}")
```

### 6.3 事件溯源（Event Sourcing）入门

```
传统模式 vs 事件溯源：

  传统：数据库存当前状态
    orders 表: {id:1, status:"paid", amount:99.9}

  事件溯源：数据库存事件序列，当前状态通过回放事件得出
    events 表:
      {order_id:1, type:"created",  data:{amount:99.9&#125;&#125;
      {order_id:1, type:"paid",     data:{payment_id:789&#125;&#125;
      {order_id:1, type:"shipped",  data:{tracking:"SF123"&#125;&#125;
    
    当前状态 = 回放所有事件：created → paid → shipped

  优点：完整审计日志、可回溯、可以从事件重建任何时间点的状态
  缺点：查询复杂（需要投影/快照）、事件存储量大
```

### 6.4 CQRS：读写分离架构

```
CQRS（Command Query Responsibility Segregation）：

  命令（写）→ 主库 → 发事件 → 更新读模型
  查询（读）→ 读库（针对查询优化的数据结构）

  写端：event_store（事件表）
  读端：order_view（物化视图，按查询需求优化）

  实际应用：
  - 写端用 PostgreSQL（事务一致性）
  - 读端用 Elasticsearch（全文搜索）或 Redis（快速查询）
  - 通过消息队列同步读写模型
```

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **事件规范** | event_type + version + data + metadata |
| **Outbox** | 事件写 DB 事务 → 后台轮询发 MQ |
| **Event Sourcing** | 存事件序列，回放得状态 |
| **CQRS** | 写端存事件，读端物化视图 |

---

## 7. 常用消息模式

### 7.1 重试与退避策略

```python
async def consume_with_retry(message, max_retries: int = 3):
    """消费失败自动重试（利用消息 Header 记录重试次数）"""
    retry_count = int(message.headers.get("x-retry-count", 0))
    
    try:
        await process(json.loads(message.body))
        await message.ack()
    except Exception as e:
        if retry_count < max_retries:
            # 重新发布，带上重试次数
            new_msg = aio_pika.Message(
                body=message.body,
                headers={"x-retry-count": str(retry_count + 1)},
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            delay = 2 ** retry_count  # 指数退避：1s, 2s, 4s
            await asyncio.sleep(delay)
            await exchange.publish(new_msg, routing_key=message.routing_key)
            await message.ack()
        else:
            # 超过重试上限 → 进死信
            await message.reject(requeue=False)
```

### 7.2 顺序消息：如何保证消费顺序

```
RabbitMQ 保证顺序：
  ✅ 单队列 + 单消费者 → 天然有序
  ❌ 单队列 + 多消费者 → 不保证（并发处理乱序）
  解决：相同业务 ID 的消息发到同一队列

Kafka 保证顺序：
  ✅ 同 Key → 同 Partition → 单分区内有序
  关键：按业务 ID（user_id/order_id）做 Key
```

### 7.3 广播模式：一条消息多个消费者

```python
# RabbitMQ: Fanout Exchange
exchange = await channel.declare_exchange("broadcast", ExchangeType.FANOUT)

# 每个消费者声明自己的独占队列
queue_sms = await channel.declare_queue("", exclusive=True)     # 短信服务
queue_email = await channel.declare_queue("", exclusive=True)   # 邮件服务
queue_stats = await channel.declare_queue("", exclusive=True)   # 统计服务

await queue_sms.bind(exchange)
await queue_email.bind(exchange)
await queue_stats.bind(exchange)

# 发一条消息 → 三个队列都收到
await exchange.publish(message, routing_key="")
```

### 7.4 请求-响应模式（RPC over MQ）

```python
import uuid

async def rpc_call(routing_key: str, data: dict, timeout: float = 10.0) -> dict:
    """通过 MQ 实现 RPC 调用"""
    correlation_id = str(uuid.uuid4())
    
    # 创建临时回复队列
    callback_queue = await channel.declare_queue("", exclusive=True, auto_delete=True)
    
    # 发送请求
    await exchange.publish(
        aio_pika.Message(
            body=json.dumps(data).encode(),
            correlation_id=correlation_id,
            reply_to=callback_queue.name,
        ),
        routing_key=routing_key,
    )
    
    # 等待响应
    async with callback_queue.iterator() as messages:
        async for message in messages:
            if message.correlation_id == correlation_id:
                await message.ack()
                return json.loads(message.body)
```

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **重试退避** | Header 计数 + 指数退避 + 超限进死信 |
| **顺序消息** | Kafka 用 Key 分区、RabbitMQ 用单消费者 |
| **广播** | Fanout Exchange + 独占队列 |
| **RPC** | reply_to + correlation_id 实现请求-响应 |

---

## 8. 与 FastAPI 集成

### 8.1 FastAPI 生命周期管理消息连接

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时建立 MQ 连接
    app.state.mq_connection = await aio_pika.connect_robust("amqp://admin:admin123@rabbitmq/")
    app.state.mq_channel = await app.state.mq_connection.channel()
    app.state.exchange = await app.state.mq_channel.declare_exchange(
        "app_events", ExchangeType.TOPIC, durable=True
    )
    yield
    # 关闭时断开连接
    await app.state.mq_connection.close()

app = FastAPI(lifespan=lifespan)

# 在路由中使用
@app.post("/orders")
async def create_order(data: OrderCreate, request: Request):
    order = await order_service.create(data)
    await request.app.state.exchange.publish(
        aio_pika.Message(body=json.dumps({"order_id": order.id}).encode()),
        routing_key="order.created",
    )
    return order
```

### 8.2 后台 Consumer 进程架构

```python
# consumer.py（独立进程，不在 FastAPI 里运行）
import asyncio

async def main():
    connection = await aio_pika.connect_robust("amqp://admin:admin123@rabbitmq/")
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=20)
    
    exchange = await channel.declare_exchange("app_events", ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue("order_processor", durable=True)
    await queue.bind(exchange, routing_key="order.*")
    
    print("🎧 Consumer 已启动，等待消息...")
    async with queue.iterator() as messages:
        async for message in messages:
            async with message.process():
                await handle_message(message)

asyncio.run(main())
```

```
部署架构：

  docker-compose.yml:
    api:      FastAPI（只负责发消息）
    consumer: python consumer.py（只负责收消息）
    rabbitmq: RabbitMQ Broker

  api 和 consumer 独立扩缩容
```

### 8.3 Celery vs 直接消费：选哪个？

| 维度 | Celery | 直接消费 |
|:---|:---|:---|
| **复杂度** | 高（需要 Worker 管理） | 低（自己写循环） |
| **重试** | 内置（max_retries） | 需自己实现 |
| **任务路由** | 内置（queue 参数） | 需自己路由 |
| **定时任务** | 内置（Beat） | 需要额外工具 |
| **适用** | 异步任务（发邮件/生成报告） | 事件消费（订单处理/数据同步） |

```
选型建议：
  需要任务调度 + 重试 + 定时 → Celery
  只需要事件消费 → 直接消费更轻量
```

### 8.4 消息驱动的 WebSocket 实时推送

```python
# Consumer 收到消息 → 通过 WebSocket 推给前端
async def handle_order_status(data: dict):
    order_id = data["order_id"]
    status = data["status"]
    user_id = data["user_id"]
    
    # 推送给对应用户
    await ws_manager.send_to(str(user_id), {
        "type": "order_status",
        "order_id": order_id,
        "status": status,
    })
```

**第 8 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Lifespan** | FastAPI 启动/关闭时管理 MQ 连接 |
| **独立进程** | Consumer 独立于 API，各自扩缩容 |
| **Celery** | 适合任务调度，直接消费适合事件消费 |
| **WS 推送** | MQ Consumer → WebSocket → 前端实时通知 |

---

## 9. 监控与运维

### 9.1 RabbitMQ Management 监控面板

```
Management UI（:15672）关注的核心指标：

  队列层面：
  ┌────────────────┬──────────────────────────────┐
  │ Messages Ready │ 待消费消息数（堆积量）         │
  │ Consumers      │ 消费者数量                    │
  │ Publish Rate   │ 发送速率（msg/s）             │
  │ Deliver Rate   │ 消费速率（msg/s）             │
  │ Ack Rate       │ 确认速率                      │
  │ Unacked        │ 未确认消息（消费者在处理中）    │
  └────────────────┴──────────────────────────────┘

  告警阈值（参考）：
  - Messages Ready > 10000 → 消费者处理不过来
  - Unacked > 100 → 消费者可能卡住
  - 发送速率 >> 消费速率 → 需要扩消费者
```

### 9.2 Kafka 监控：Kafka UI / Burrow

```yaml
# Kafka UI（推荐）
services:
  kafka-ui:
    image: provectuslabs/kafka-ui
    ports: ["8080:8080"]
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
```

```
Kafka 核心监控指标：

  Consumer Lag（消费延迟）= 最新 Offset - 消费者 Offset
  → Lag 持续增大 = 消费跟不上生产

  Partition 分布：是否均匀、有无热点分区
  ISR（In-Sync Replicas）：副本是否同步
```

### 9.3 Prometheus 指标采集与告警

::: v-pre
```yaml
# RabbitMQ Prometheus 插件
rabbitmq-plugins enable rabbitmq_prometheus
# 访问 :15692/metrics

# 告警规则
groups:
  - name: mq_alerts
    rules:
      - alert: QueueMessagePileup
        expr: rabbitmq_queue_messages_ready > 10000
        for: 5m
        annotations:
          summary: "队列 &#123;&#123; $labels.queue &#125;&#125; 消息堆积 &#123;&#123; $value &#125;&#125;"
      
      - alert: KafkaConsumerLag
        expr: kafka_consumer_group_lag > 50000
        for: 5m
        annotations:
          summary: "消费组 &#123;&#123; $labels.group &#125;&#125; 延迟 &#123;&#123; $value &#125;&#125;"
```
:::

### 9.4 容量规划与性能调优

```
RabbitMQ 调优：
  - prefetch_count：10-50（太小浪费网络，太大占内存）
  - 持久化 vs 非持久化：非关键消息可以不持久化（快 10x）
  - 惰性队列（lazy queue）：消息直接写磁盘，适合堆积场景

Kafka 调优：
  - 分区数 = 期望吞吐 / 单分区吞吐（通常 3-12 个）
  - batch.size：16KB-64KB（批量发送减少网络开销）
  - linger.ms：5-10ms（等待凑批，牺牲延迟换吞吐）
  - compression.type：lz4（压缩率和速度的平衡）
```

**第 9 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **堆积监控** | RabbitMQ: Messages Ready, Kafka: Consumer Lag |
| **Prometheus** | 采集 MQ 指标 + 告警规则 |
| **prefetch** | RabbitMQ 预取 10-50 |
| **批量发送** | Kafka batch.size + linger.ms 换吞吐 |

---

## 10. 实战案例：电商订单事件系统

### 10.1 系统架构设计

```
事件驱动的电商架构：

  用户下单 → 订单服务
                │
          发布 "order.created"
                │
    ┌───────────┼───────────┬───────────┐
    ↓           ↓           ↓           ↓
  库存服务   支付服务    通知服务    分析服务
  (扣库存)   (创建支付)  (发短信)   (记统计)
    │           │
  "inventory   "payment
   .reserved"   .completed"
    │           │
    └───────────┘
          ↓
    订单服务（更新状态 → paid）
```

### 10.2 事件定义与消息流转

```python
# 事件类型定义
EVENTS = {
    "order.created":       {"order_id", "user_id", "product_id", "quantity", "amount"},
    "inventory.reserved":  {"order_id", "product_id", "quantity"},
    "inventory.failed":    {"order_id", "reason"},
    "payment.completed":   {"order_id", "payment_id", "amount"},
    "payment.failed":      {"order_id", "reason"},
    "order.paid":          {"order_id"},
    "order.cancelled":     {"order_id", "reason"},
}

# 消息流转（RabbitMQ Topic Exchange）
# order.created   → inventory_queue（库存服务监听）
# order.created   → notification_queue（通知服务监听）
# inventory.*     → order_saga_queue（订单 Saga 监听）
# payment.*       → order_saga_queue（订单 Saga 监听）
```

### 10.3 核心服务实现

```python
# 库存服务消费者
async def handle_order_created(data: dict):
    try:
        await inventory_repo.reserve(data["product_id"], data["quantity"])
        await publish("inventory.reserved", {
            "order_id": data["order_id"],
            "product_id": data["product_id"],
        })
    except InsufficientStock:
        await publish("inventory.failed", {
            "order_id": data["order_id"],
            "reason": "库存不足",
        })

# 订单 Saga 消费者
async def handle_saga_event(event_type: str, data: dict):
    if event_type == "inventory.reserved":
        await payment_service.create_payment(data["order_id"])
    
    elif event_type == "payment.completed":
        await order_repo.update(data["order_id"], status="paid")
        await publish("order.paid", {"order_id": data["order_id"]})
    
    elif event_type in ("inventory.failed", "payment.failed"):
        await order_repo.update(data["order_id"], status="cancelled")
        if event_type == "payment.failed":
            await inventory_service.release(data["order_id"])  # 补偿
```

### 10.4 故障恢复与消息补偿

```python
# 定时对账任务：修复不一致数据
async def reconcile_orders():
    """每小时检查一次：pending 超过 30 分钟的订单"""
    stale_orders = await order_repo.list(
        status="pending",
        created_before=datetime.utcnow() - timedelta(minutes=30),
    )
    for order in stale_orders:
        logger.warning(f"超时订单: {order.id}")
        await order_repo.update(order.id, status="cancelled")
        await publish("order.cancelled", {
            "order_id": order.id,
            "reason": "超时未完成",
        })
```

**第 10 章核心知识回顾：**

| 阶段 | 做了什么 |
|:---|:---|
| **架构** | 事件驱动，4 服务通过 MQ 松耦合 |
| **事件流** | order.created → inventory/payment → order.paid |
| **Saga** | 按事件类型分支处理 + 失败补偿 |
| **对账** | 定时扫描超时订单，兜底保一致性 |

---

## 附录

### A. RabbitMQ vs Kafka 特性对照表

| 特性 | RabbitMQ | Kafka |
|:---|:---|:---|
| 消息模型 | Exchange + Queue | Topic + Partition |
| 消费方式 | Push | Pull |
| 消息保留 | 消费即删 | 按策略保留（可回溯） |
| 消息顺序 | 单队列有序 | 单分区有序 |
| 吞吐量 | ~30K msg/s | ~1M msg/s |
| 延迟 | 微秒级 | 毫秒级 |
| 协议 | AMQP | 自有 |
| 路由能力 | 强（4 种 Exchange） | 弱（按 Key 分区） |
| 死信队列 | 原生支持 | 需自己实现 |
| 延迟消息 | TTL+DLX / 插件 | 需自己实现 |
| 管理面板 | 自带 Management | Kafka UI（第三方） |
| Python 客户端 | aio-pika | aiokafka |

### B. 消息队列选型决策树

```
你的场景是什么？

  ├─ 业务消息（订单/支付/通知）
  │   ├─ 需要灵活路由（Topic/Header 匹配）→ RabbitMQ
  │   ├─ 需要延迟消息 → RabbitMQ
  │   └─ 需要消息确认（ACK/NACK）→ RabbitMQ
  │
  ├─ 事件流 / 日志采集
  │   ├─ 需要消息回溯 → Kafka
  │   ├─ 吞吐量 > 10 万/秒 → Kafka
  │   └─ 需要长期存储（天/周/月）→ Kafka
  │
  ├─ 任务队列（异步任务分发）
  │   └─ Python 生态 → Celery + RabbitMQ/Redis
  │
  └─ 不确定 → 先 RabbitMQ，够用就不换
```

### C. 常见问题与排查手册

| 问题 | 现象 | 排查 |
|:---|:---|:---|
| **消息丢失** | 消费者没收到消息 | 检查持久化三件套 + Publisher Confirm |
| **消息堆积** | Ready 数持续增长 | 扩消费者 / 提高 prefetch / 检查处理逻辑 |
| **重复消费** | 同一消息处理两次 | 消费端做幂等（去重表/唯一 ID） |
| **消费者卡死** | Unacked 持续增长 | 检查处理逻辑是否有死循环/长阻塞 |
| **连接断开** | ConnectionReset | 使用 connect_robust + 心跳 |
| **顺序错乱** | 消息处理顺序不对 | RabbitMQ 单消费者 / Kafka 同 Key 同分区 |
| **Kafka Lag 增大** | 消费跟不上 | 增加分区 + 增加消费者 |
| **RabbitMQ OOM** | Broker 内存耗尽 | 设置队列最大长度 + 惰性队列 |
