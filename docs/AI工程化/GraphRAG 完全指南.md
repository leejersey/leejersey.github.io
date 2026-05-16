# GraphRAG 完全指南：用知识图谱让 RAG 真正理解你的数据

> 当标准 RAG 只能"关键词匹配"时，GraphRAG 用知识图谱让 AI 学会"连线推理"——从实体关系中发现标准检索永远找不到的答案。

---

## 1. 为什么标准 RAG 不够用

你搭了一个 RAG 系统，把公司的内部文档全部切片、向量化、塞进了 Milvus。老板问"我们华东区最大的客户是谁？"——秒答。老板又问"华东区最大的客户和我们的合作历史中，哪些项目涉及了第三方供应商？"——系统沉默了三秒，然后吐出一段看起来很像回答但完全答非所问的废话。

**你的 RAG 系统不是"笨"，是"瞎"。** 它看得到一个个文档片段，但看不到片段之间的关系。就像一个图书管理员能帮你找到任何一本书，但你问他"这两本书的作者是什么关系"，他只能茫然地看着你。

### 1.1 标准 RAG 的工作流回顾

先快速回顾一下标准 RAG 的三步走：

```
标准 RAG 工作流：

  ① 索引阶段（离线）
     文档 → 分块（Chunking）→ Embedding → 存入向量数据库

  ② 检索阶段（在线）
     用户提问 → 问题 Embedding → 向量相似度搜索 → 返回 Top-K 片段

  ③ 生成阶段
     Top-K 片段 + 用户问题 → 喂给 LLM → 生成回答
```

这套流程在**局部事实查询**上表现出色——"我们的退款政策是什么？""张三的工号是多少？"向量检索能精准找到包含答案的那个片段，LLM 生成的回答也很到位。

但问题来了：现实中的问题，远不止"查一个事实"这么简单。

### 1.2 三类必败场景：多跳推理、全局摘要、关系发现

**场景一：多跳推理（Multi-hop Reasoning）**

> 问题："张三的直属领导是谁？他的领导负责过哪些失败的项目？"

这个问题需要两跳：先找到张三的领导（文档 A），再找到那个领导的项目记录（文档 B）。标准 RAG 的 Top-K 检索只会根据"张三"和"领导"去找最相似的片段——很可能找到了张三的个人简介（包含领导姓名），但找不到领导的项目记录，因为那个文档和问题的向量相似度太低了。

**场景二：全局摘要（Global Summarization）**

> 问题："过去一年里，我们的技术团队主要在关注哪些方向？"

这类问题没有一个"正确的片段"可以检索到。答案散落在几百份周报、会议纪要、OKR 文档里。标准 RAG 只能从 Top-K 个片段中拼凑出一个局部的、可能有偏差的回答。它没有"全局视角"。

**场景三：关系发现（Relationship Discovery）**

> 问题："哪些客户同时和我们的销售团队、技术团队有过对接？"

这是一个**关系查询**——不是在找某个事实，而是在找实体之间的连接模式。向量检索对此完全无能为力，因为它只看文本相似度，不理解"对接"这个关系在不同文档之间的结构。

| 场景 | 标准 RAG 表现 | 失败原因 |
|------|-------------|---------|
| 多跳推理 | ❌ 找到第一跳，丢了第二跳 | Top-K 只按相似度排序，不考虑推理链 |
| 全局摘要 | ⚠️ 片面的、有偏差的总结 | 只看 K 个片段，无法覆盖全局 |
| 关系发现 | ❌ 完全答不上来 | 向量空间没有"关系"的概念 |
### 1.3 问题的根源：向量相似度 ≠ 语义关联

这三类失败不是偶然的——它们有一个共同的根源：**向量相似度衡量的是"文本像不像"，而不是"语义上有没有关联"。**

```
向量检索的本质：

  Query: "张三的领导负责过哪些失败的项目？"
  
  ✅ 高相似度（但答不对）：
     "张三是技术部的资深工程师，2023 年入职。"     → cos_sim = 0.87
  
  ❌ 低相似度（但恰好是答案）：
     "项目 Alpha 在 2024Q2 延期交付，负责人是李四。"  → cos_sim = 0.31
```

向量检索不知道"张三的领导"就是"李四"——因为这个关系存在于另一个文档片段里。两个片段在向量空间中可能相距甚远，但在**语义图谱**中，它们只隔了一条边。

这就是 GraphRAG 要解决的问题：**不是让检索更快或更准，而是让检索"看到"文档之间的结构化关系。**

> 💡 **核心洞察：** 标准 RAG 把文档当作一堆独立的积木块——它能帮你找到某一块积木，但不知道积木之间怎么拼。GraphRAG 把文档变成一张网——节点是实体，边是关系，沿着网你能"走"到标准检索永远到不了的地方。

---

## 2. GraphRAG 是什么：从向量到图谱的范式转换

上一章我们看到了标准 RAG 的三个系统性盲区。现在的问题是：**怎么修？**

答案不是"用更好的 Embedding 模型"或"把 Top-K 调大一点"——这些都是在向量检索的框架内做优化，治标不治本。真正的解法是**换一种数据结构**来表示知识：从"一堆独立的文本片段"变成"一张实体关系网"。

### 2.1 一句话定义：Graph + RAG

**GraphRAG = 知识图谱（Knowledge Graph）+ 检索增强生成（RAG）。**

把这个等式拆开：

- **Graph**：用知识图谱来组织数据——实体是**节点**（人、公司、项目、概念），实体之间的联系是**边**（领导、合作、参与、属于）
- **RAG**：检索相关上下文，送给 LLM 生成回答——这一步和标准 RAG 一样

区别在于**检索的对象变了**：标准 RAG 检索的是"和问题最像的文本片段"，GraphRAG 检索的是"和问题相关的实体及其关系网络"。

打个比方：
- 标准 RAG 像**百度搜索**——你输入关键词，它给你最相关的网页列表
- GraphRAG 像**百度百科的知识卡片**——你搜"张三"，它不仅给你张三的介绍，还自动展示张三的领导、同事、参与的项目、所在的公司，以及这些实体之间的关系

### 2.2 核心架构对比：向量检索 vs 图遍历

把两套架构放在一起看，差异一目了然：

```
标准 RAG：
  文档 → 分块 → Embedding → 向量数据库
                                  ↓
  用户提问 → Embedding → 向量相似度搜索 → Top-K 片段 → LLM → 回答

GraphRAG：
  文档 → 分块 → LLM 提取实体/关系 → 知识图谱 → 社区检测 → 社区摘要
                                        ↓
  用户提问 → 实体识别 → 图遍历/社区匹配 → 相关子图 → LLM → 回答
```

关键差异：

| 维度 | 标准 RAG | GraphRAG |
|------|---------|----------|
| 数据结构 | 向量空间（高维浮点数） | 知识图谱（节点 + 边） |
| 索引方式 | Embedding（便宜、快） | LLM 提取实体/关系（贵、慢） |
| 检索方式 | 余弦相似度 Top-K | 图遍历 + 社区摘要匹配 |
| 多跳能力 | ❌ 无 | ✅ 沿边自然遍历 |
| 全局视角 | ❌ 无 | ✅ 社区摘要提供层级视图 |
| 索引成本 | 低（1x） | 高（10-100x Token 消耗） |
| 查询延迟 | 毫秒级 | 秒级（图遍历 + LLM 调用） |
| 可解释性 | 弱（"因为这个片段最相似"） | 强（"通过 A→B→C 的关系路径"） |

一句话总结：**标准 RAG 是"搜"，GraphRAG 是"连"。** 搜只能找到孤立的点，连能沿着线走到更远的地方。
### 2.3 GraphRAG 的前世今生：从微软论文到开源生态

GraphRAG 不是凭空冒出来的。它站在两个巨人的肩膀上：

**知识图谱（Knowledge Graph）：** Google 在 2012 年发布 Knowledge Graph，用结构化的实体关系网增强搜索结果。你在 Google 搜"爱因斯坦"时右边弹出的信息卡片——出生日期、国籍、代表作——就是知识图谱的产物。

**RAG（Retrieval-Augmented Generation）：** Meta 在 2020 年发表 RAG 论文，提出"先检索后生成"的范式，解决 LLM 知识过时和幻觉的问题。

**GraphRAG 的时间线：**

| 时间 | 事件 | 意义 |
|------|------|------|
| 2012 | Google Knowledge Graph | 知识图谱概念进入主流 |
| 2020 | Meta RAG 论文 | "先检索后生成"范式确立 |
| 2024.02 | 微软发表 GraphRAG 论文 | 提出"图谱 + RAG"的系统化架构 |
| 2024.07 | 微软开源 `graphrag` | 提供参考实现，社区开始跟进 |
| 2024-2025 | LlamaIndex/LangChain 集成 | PropertyGraphIndex 等工具链成熟 |
| 2025-2026 | Nano-GraphRAG、LightRAG 等 | 轻量级替代方案涌现，降低门槛 |

**当前主要开源实现：**

- **[Microsoft GraphRAG](https://github.com/microsoft/graphrag)**：官方参考实现，功能完整但较重
- **[LlamaIndex PropertyGraphIndex](https://docs.llamaindex.ai/)**：灵活的图谱集成框架
- **[Nano-GraphRAG](https://github.com/gusye1234/nano-graphrag)**：轻量实现，适合学习和快速原型
- **[LightRAG](https://github.com/HKUDS/LightRAG)**：简化版 GraphRAG，降低索引成本

> 💡 **核心认知：** GraphRAG 不是一个"工具"，而是一种**架构范式**——用图谱结构替代向量空间来组织知识。具体用哪个工具、哪个数据库，是实现细节。理解范式比记住 API 重要得多。

---

## 3. 知识图谱基础：节点、边和三元组

如果你之前没接触过知识图谱，别担心——它的核心思想比你想的简单得多。本章为没有图谱背景的读者"补课"，已有基础的可以跳到第 4 章。

### 3.1 什么是知识图谱：实体、关系、属性

知识图谱本质上就是一张**网**，由三个元素组成：

```
知识图谱的三个核心元素：

  ● 节点（Node / Entity）—— 一个"东西"
    例：张三、华为、项目 Alpha、Python

  ── 边（Edge / Relationship）—— 两个东西之间的联系
    例：张三 —[就职于]→ 华为
        张三 —[参与]→ 项目 Alpha

  {} 属性（Property）—— 附着在节点或边上的额外信息
    例：张三 {职级: P7, 入职日期: 2023-03}
        就职于 {部门: 云计算BU}
```

用一个具体的例子来感受：

```
                    ┌──────────┐
          就职于     │   华为    │
    ┌─────────────▶│ {行业:科技}│
    │              └──────────┘
┌───┴───┐                          ┌───────────┐
│ 张三   │────── 参与 ─────────────▶│ 项目 Alpha │
│{P7}   │                          │{状态:延期} │
└───┬───┘                          └───────────┘
    │              ┌──────────┐
    └── 汇报给 ───▶│   李四    │
                   │{P9, 总监}│
                   └──────────┘
```

这张图包含了 4 个节点（张三、华为、项目 Alpha、李四）和 3 条边（就职于、参与、汇报给）。每个节点和边都可以带属性。

**和关系型数据库的区别：** 关系型数据库也能存这些数据，但你需要写复杂的 JOIN 查询。图数据库天生就是为"沿着关系走"设计的——"张三的领导参与过哪些项目？"在图数据库里只需要两步遍历，在关系型数据库里可能需要三四个 JOIN。

### 3.2 三元组结构：Subject → Predicate → Object

知识图谱的**最小信息单元**是**三元组（Triple）**——一条边连接两个节点：

```
三元组 = (主语 Subject, 谓语 Predicate, 宾语 Object)

例子：
  (张三, 就职于, 华为)
  (张三, 参与, 项目Alpha)
  (张三, 汇报给, 李四)
  (李四, 负责, 项目Alpha)
  (华为, 行业, 科技)
```

每条三元组就是一个独立的事实。整个知识图谱就是大量三元组的集合。这也是 GraphRAG 索引阶段的核心输出——LLM 从文档中提取出一条条三元组，汇总成图谱。

**为什么三元组这么重要？** 因为它让知识变得**可组合**：

```
问题："张三的领导负责过哪些项目？"

推理过程（沿三元组链）：
  (张三, 汇报给, 李四)     → 张三的领导是李四
  (李四, 负责, 项目Alpha)   → 李四负责项目 Alpha
  
  答案：项目 Alpha
```

这就是标准 RAG 做不到的**多跳推理**——每一跳就是沿一条三元组走一步。图谱有多少边，理论上你就能走多远。
### 3.3 图数据库入门：Neo4j 和 Cypher 查询语言

知识图谱需要一个"家"来存储——这就是**图数据库**。最流行的选择是 **Neo4j**，它用一种叫 **Cypher** 的查询语言来操作图谱。

```cypher
// 创建节点
CREATE (zhangsan:Person {name: "张三", level: "P7"})
CREATE (lisi:Person {name: "李四", level: "P9"})
CREATE (huawei:Company {name: "华为", industry: "科技"})
CREATE (alpha:Project {name: "项目Alpha", status: "延期"})

// 创建关系（边）
CREATE (zhangsan)-[:WORKS_AT {department: "云计算BU"}]->(huawei)
CREATE (zhangsan)-[:REPORTS_TO]->(lisi)
CREATE (zhangsan)-[:PARTICIPATES]->(alpha)
CREATE (lisi)-[:LEADS]->(alpha)
```

查询的魅力在于"沿着关系走"：

```cypher
// 一跳查询：张三的领导是谁？
MATCH (p:Person {name: "张三"})-[:REPORTS_TO]->(leader)
RETURN leader.name
// → 李四

// 两跳查询：张三的领导负责哪些项目？
MATCH (p:Person {name: "张三"})-[:REPORTS_TO]->(leader)-[:LEADS]->(project)
RETURN project.name, project.status
// → 项目Alpha, 延期

// 关系发现：哪些人同时和华为、项目Alpha有关联？
MATCH (p:Person)-[:WORKS_AT]->(c:Company {name: "华为"}),
      (p)-[:PARTICIPATES]->(proj:Project {name: "项目Alpha"})
RETURN p.name
// → 张三
```

注意上面的两跳查询——**这正是第 1 章中标准 RAG 答不上来的问题**，在图数据库里只需要一行 Cypher。

> 💡 **要点：** 你不需要成为 Neo4j 专家才能用 GraphRAG。在微软的 GraphRAG 实现中，图谱存储在 Parquet 文件里，不需要额外的图数据库。但理解图的概念（节点、边、遍历）是理解 GraphRAG 工作原理的前提。

---

## 4. GraphRAG 索引管线：从文档到图谱

索引管线是 GraphRAG 最核心也最"重"的部分——它决定了你的知识图谱质量，而图谱质量直接决定了查询结果的好坏。**垃圾进，垃圾出。**

整个索引管线分五步：

```
索引管线全景：

  文档 → ① 分块 → ② LLM提取实体/关系 → ③ 实体消歧合并
                                              ↓
         ⑤ 社区摘要 ← ④ 社区检测(Leiden) ← 知识图谱
```

### 4.1 文档分块策略：和标准 RAG 有什么不同

GraphRAG 的分块和标准 RAG 有一个关键区别：**块不能太小。**

标准 RAG 倾向于小块（200-500 token），因为小块的 Embedding 更精准。但 GraphRAG 需要 LLM 从每个块中提取实体和关系——如果块太小，LLM 看不到足够的上下文来理解实体之间的关系。

| 策略 | 标准 RAG 推荐 | GraphRAG 推荐 |
|------|-------------|-------------|
| 块大小 | 200-500 token | 600-1200 token |
| 重叠 | 50-100 token | 100-200 token（更大重叠保留跨块关系） |
| 分块方式 | 按句子/段落 | 按段落/小节（保持语义完整性） |

微软 GraphRAG 默认使用 300 token 的块大小，但实践中很多人发现 **600-1200 token** 效果更好——给 LLM 足够的"视野"来发现实体关系。

### 4.2 LLM 实体与关系提取：Prompt 工程的关键

这是整个管线**最贵也最关键**的一步：让 LLM 从每个文本块中提取出实体和关系。

核心 Prompt 的结构大致如下：

```
系统提示：
  你是一个信息提取助手。从以下文本中提取所有实体和它们之间的关系。
  
  实体类型：PERSON, ORGANIZATION, PROJECT, TECHNOLOGY, LOCATION
  关系类型：WORKS_AT, REPORTS_TO, PARTICIPATES, USES, LOCATED_IN
  
  输出格式（JSON）：
  {
    "entities": [
      {"name": "张三", "type": "PERSON", "description": "P7级工程师"}
    ],
    "relationships": [
      {"source": "张三", "target": "华为", "type": "WORKS_AT", 
       "description": "就职于云计算BU"}
    ]
  }

用户输入：
  <待提取的文本块>
```

**常见的坑：**

- **实体类型定义太宽泛**：如果你只定义了"ENTITY"一个类型，LLM 会把什么都提取出来，噪音太大。定义 5-8 个具体类型效果最好
- **遗漏隐含关系**：文本说"张三在华为做了三年"，LLM 可能只提取了 `(张三, WORKS_AT, 华为)` 而遗漏了时间属性。需要在 Prompt 中明确要求提取属性
- **过度提取**：LLM 可能把形容词、动词都当成实体。需要明确告诉它"只提取名词性实体"

> ⚠️ **成本警告：** 每个文本块都要调用一次 LLM。如果你有 1000 个块，就是 1000 次 API 调用。这就是 GraphRAG 索引成本高 10-100x 的原因。

### 4.3 实体消歧与合并：让"张三"和"Mr. Zhang"变成同一个节点

从不同文档块提取出来的实体，经常会出现**同一个东西有多种叫法**的问题：

```
文档 A → 提取出：(张三, WORKS_AT, 华为)
文档 B → 提取出：(Mr. Zhang, LEADS, 项目Alpha)
文档 C → 提取出：(张三同学, PARTICIPATES, 技术峰会)

问题：这三个是同一个人吗？
```

如果不做实体消歧，你的图谱里会出现三个"不同的"张三节点，多跳推理就断了。

**主要消歧策略：**

| 策略 | 方法 | 适用场景 |
|------|------|---------|
| 字符串匹配 | 编辑距离、模糊匹配 | 简单的名称变体（"华为" vs "华为技术"） |
| LLM 辅助判断 | 把候选实体对喂给 LLM 判断是否相同 | 复杂的跨语言/跨称呼变体 |
| Embedding 相似度 | 对实体描述做 Embedding，高相似度的合并 | 大规模自动化合并 |
| 规则引擎 | 自定义规则（如"同一段落中的同名实体一定相同"） | 领域特定的消歧 |

微软 GraphRAG 采用的是 **LLM 辅助 + 描述合并** 的策略：当两个实体名称相似时，把它们的描述拼在一起让 LLM 判断是否该合并，如果合并则生成一个统一的描述。
### 4.4 社区检测：Leiden 算法与层级聚类

有了知识图谱之后，下一步是**发现图谱中的"社区"**——一组紧密关联的实体。这是 GraphRAG 支持全局摘要查询的关键。

```
社区检测的直觉：

  想象你有一张公司的人际关系图。你会发现：
  - 销售部的人之间关系很密（经常一起开会、合作项目）
  - 技术部的人之间也很密
  - 但销售部和技术部之间关系较疏（偶尔跨部门协作）

  社区检测算法能自动发现这种"内部紧密、外部稀疏"的分组。
```

微软 GraphRAG 使用的是 **Leiden 算法**——一种比经典 Louvain 算法更快、更准确的社区检测方法。它的输出是**层级结构**：

```
层级 0（最细粒度）：
  社区 A：张三、李四、项目Alpha    ← 同一个项目组
  社区 B：王五、赵六、项目Beta     ← 另一个项目组
  社区 C：CTO办公室、战略部、OKR   ← 管理层

层级 1（中等粒度）：
  社区 X：社区A + 社区B            ← 整个技术部
  社区 Y：社区C                    ← 管理层

层级 2（最粗粒度）：
  社区 Z：社区X + 社区Y            ← 整个公司
```

不同层级的社区适合回答不同粒度的问题——这就是 Global Search 的基础。
### 4.5 社区摘要生成：全局理解的基础

最后一步：**对每个社区，用 LLM 生成一段摘要。**

```
社区 A（张三、李四、项目Alpha）的摘要：

  "该社区围绕项目 Alpha 展开。张三（P7 工程师）是主要参与者，
   向李四（P9 总监）汇报。项目当前状态为延期，主要风险是
   第三方供应商交付不及时。"
```

这些社区摘要就是 Global Search 的"原材料"。当用户问"我们公司现在面临哪些主要风险？"时，GraphRAG 不需要遍历所有文档——它只需要汇聚各社区摘要中关于"风险"的信息。

**社区摘要的层级对应不同粒度的回答：**

| 层级 | 摘要粒度 | 适合回答的问题 |
|------|---------|-------------|
| 层级 0 | 单个项目组/功能模块 | "项目 Alpha 的进展如何？" |
| 层级 1 | 部门/业务线 | "技术部今年的重点方向？" |
| 层级 2 | 整个组织 | "公司面临的主要风险有哪些？" |

> 💡 **核心要点：** 索引管线的五步——分块、提取、消歧、聚类、摘要——每一步都很重要，任何一步出错都会传导到最终的查询质量。**图谱质量是 GraphRAG 的生命线，值得花 80% 的时间来优化。**

---

## 5. GraphRAG 查询管线：Local Search 与 Global Search

索引管线建好了图谱和社区摘要，现在的问题是：**用户问了一个问题，怎么从图谱里找到答案？**

GraphRAG 提供两种搜索模式，各有所长：

| 模式 | 适合的问题类型 | 检索方式 |
|------|-------------|---------|
| Local Search | 具体的、有明确实体的问题 | 从实体出发，沿边扩展 |
| Global Search | 全局性、摘要性的问题 | 遍历社区摘要层级 |

### 5.1 Local Search：从实体出发，沿边探索

Local Search 适合回答**有明确实体指向**的问题，比如"张三参与过哪些项目？""项目 Alpha 涉及哪些技术？"

工作流程：

```
Local Search 流程：

  用户问题："张三的领导负责过哪些延期的项目？"
           ↓
  ① 实体识别：从问题中提取关键实体 → "张三"
           ↓
  ② 子图提取：以"张三"为起点，沿边向外扩展 N 跳
     张三 —[汇报给]→ 李四 —[负责]→ 项目Alpha {状态:延期}
     张三 —[就职于]→ 华为
     张三 —[参与]→ 项目Beta {状态:完成}
           ↓
  ③ 上下文构建：将子图中的实体、关系、属性序列化为文本
           ↓
  ④ LLM 生成：子图文本 + 原始问题 → LLM → 回答
     "李四负责的项目 Alpha 目前处于延期状态。"
```

**关键参数：** `N`（扩展跳数）决定了检索的"视野"。N=1 只看直接关联，N=2 看两步之内的所有实体。N 越大上下文越多，但也越可能引入噪音。实践中 **N=2** 是常用起点。

### 5.2 Global Search：社区摘要的层级汇聚

Global Search 适合回答**没有明确实体指向、需要全局视角**的问题，比如"我们公司面临的主要风险有哪些？""这个数据集的核心主题是什么？"

工作流程：

```
Global Search 流程：

  用户问题："过去一年，技术团队主要在关注哪些方向？"
           ↓
  ① 选择社区层级：根据问题粒度选择合适层级
     → 这是部门级问题，选层级 1
           ↓
  ② Map 阶段：将问题发送给该层级的每个社区摘要
     社区 X 摘要 + 问题 → LLM → 局部回答 1
     社区 Y 摘要 + 问题 → LLM → 局部回答 2
     社区 Z 摘要 + 问题 → LLM → 局部回答 3
           ↓
  ③ Reduce 阶段：汇聚所有局部回答
     局部回答 1 + 2 + 3 → LLM → 最终回答
     "技术团队过去一年主要关注三个方向：
      1. 云原生迁移（项目Alpha、Beta）
      2. AI 应用落地（项目Gamma）
      3. 安全合规（项目Delta）"
```

Global Search 本质上是一个 **Map-Reduce** 过程：先把问题"广播"给所有社区摘要（Map），再把各社区的局部回答汇总成一个全局回答（Reduce）。

> ⚠️ **延迟警告：** Global Search 需要对每个社区摘要都调用一次 LLM（Map 阶段），然后再调用一次 LLM（Reduce 阶段）。如果有 50 个社区，就是 51 次 LLM 调用。延迟和成本都远高于 Local Search。

### 5.3 混合检索：图谱 + 向量的最佳组合

一个实用的经验是：**不要在 GraphRAG 和标准 RAG 之间二选一，把它们组合起来。**

图谱检索擅长结构化推理，但可能遗漏没有被提取为实体的细节。向量检索擅长找到语义相关的原始文本，但看不到实体关系。两者互补：

```
混合检索策略：

  用户问题
    ├── 路径 A：图谱检索
    │   → 相关实体 + 关系 + 社区摘要
    │
    └── 路径 B：向量检索
        → Top-K 相关文本片段
    
    合并上下文
        ↓
    LLM 生成（图谱上下文 + 文本片段 + 问题）
        ↓
    最终回答
```

这种方式在实践中效果最好——图谱提供"骨架"（实体关系），向量提供"血肉"（原始文本细节）。微软的 GraphRAG Local Search 实际上已经内置了这种混合模式：它在图遍历的基础上，还会检索与相关实体关联的原始文本块。
### 5.4 查询路由：什么问题用什么搜索

实际生产中，你需要一个**查询路由器**来自动判断用什么搜索模式：

```
查询路由决策树：

  用户问题
    │
    ├── 问题中包含具体实体名称？
    │   ├── 是 → Local Search
    │   │       "张三参与过哪些项目？"
    │   │       "项目Alpha的当前状态？"
    │   │
    │   └── 否 → 继续判断
    │
    ├── 问题是全局性/摘要性的？
    │   ├── 是 → Global Search
    │   │       "公司面临的主要风险有哪些？"
    │   │       "这些文档的核心主题是什么？"
    │   │
    │   └── 否 → 继续判断
    │
    └── 其他情况 → 混合检索（图谱 + 向量）
                    "如何提升项目交付效率？"
```

路由器的实现可以很简单——用 LLM 做分类：

```python
ROUTER_PROMPT = """
判断以下问题应该使用哪种搜索模式：
- LOCAL：问题涉及具体的人、项目、组织等实体
- GLOBAL：问题需要全局视角或整体摘要
- HYBRID：其他情况

问题：{query}
模式：
"""
```

> 💡 **实用建议：** 如果你刚开始用 GraphRAG，不确定该用哪种模式，**默认用 Local Search + 向量检索的混合模式**。它覆盖面最广，虽然不是每种问题的最优解，但很少会完全答不上来。Global Search 只在明确需要全局摘要时再启用。

---

## 6. 微软 GraphRAG 实战：从安装到跑通

理论讲完了，现在**撸起袖子干**。本章手把手带你用微软开源的 `graphrag` 库跑通一个完整的 GraphRAG 管线——从安装到建索引到查询出结果。

### 6.1 环境搭建与依赖安装

```bash
# 1. 创建虚拟环境（推荐 Python 3.10+）
python -m venv graphrag-env
source graphrag-env/bin/activate  # macOS/Linux

# 2. 安装 graphrag
pip install graphrag

# 3. 创建项目目录
mkdir my-graphrag-project && cd my-graphrag-project

# 4. 初始化项目（自动生成配置文件和目录结构）
graphrag init --root ./
```

初始化后的目录结构：

```
my-graphrag-project/
├── settings.yaml          ← 核心配置文件
├── .env                   ← API 密钥（GRAPHRAG_API_KEY）
├── input/                 ← 放你的源文档（.txt）
└── output/                ← 索引输出（图谱、社区摘要等）
```

> ⚠️ **前置条件：** 你需要一个 OpenAI API Key（或兼容 API 的本地模型端点）。索引阶段会大量调用 LLM，请确保账户有足够余额。

### 6.2 配置文件详解：settings.yaml 关键字段

`settings.yaml` 是整个管线的控制中心。以下是最关键的字段：

```yaml
# LLM 配置
llm:
  api_key: ${GRAPHRAG_API_KEY}        # 从 .env 读取
  model: gpt-4o-mini                   # 推荐：性价比最高
  # model: gpt-4o                      # 更好的提取质量，但更贵
  max_tokens: 4096
  temperature: 0                       # 提取任务用 0，确保一致性

# Embedding 配置
embeddings:
  llm:
    model: text-embedding-3-small      # 用于向量检索部分

# 分块配置
chunks:
  size: 1200                           # 推荐 600-1200
  overlap: 100                         # 重叠 token 数

# 实体提取配置
entity_extraction:
  max_gleanings: 1                     # 对每个块额外提取的轮数（0=只提取一次）
  entity_types:                        # 自定义实体类型
    - PERSON
    - ORGANIZATION  
    - PROJECT
    - TECHNOLOGY
    - LOCATION

# 社区检测
community_reports:
  max_length: 1500                     # 每个社区摘要的最大 token 数
```

**最重要的三个调参点：**

| 参数 | 作用 | 建议 |
|------|------|------|
| `chunks.size` | 分块大小 | 600-1200，太小提取不到关系 |
| `entity_types` | 实体类型列表 | 5-8 个具体类型，不要用泛化的"ENTITY" |
| `llm.model` | 提取用的模型 | gpt-4o-mini 性价比最高，预算充足用 gpt-4o |

### 6.3 索引构建实战：从文档到知识图谱

准备好文档后，一行命令启动索引构建：

```bash
# 1. 把你的文档放入 input/ 目录（支持 .txt 格式）
# 如果是 PDF，先用工具转成 txt：
# pip install pymupdf
# python -c "import fitz; doc=fitz.open('my.pdf'); open('input/my.txt','w').write(''.join([p.get_text() for p in doc]))"

# 2. 配置 API Key
echo "GRAPHRAG_API_KEY=sk-your-key-here" > .env

# 3. 启动索引构建（这一步最耗时，取决于文档量）
graphrag index --root ./
```

索引完成后，`output/` 目录会生成一系列 Parquet 文件：

```
output/
├── create_final_entities.parquet      ← 所有提取的实体
├── create_final_relationships.parquet ← 所有提取的关系
├── create_final_communities.parquet   ← 社区检测结果
├── create_final_community_reports.parquet ← 社区摘要
├── create_final_text_units.parquet    ← 原始文本块
└── create_final_nodes.parquet         ← 图谱节点
```

**快速检查索引质量：**

```python
import pandas as pd

# 查看提取了多少实体
entities = pd.read_parquet("output/create_final_entities.parquet")
print(f"实体数量: {len(entities)}")
print(entities["title", "type", "description"]("title", "type", "description").head(10))

# 查看提取了多少关系
rels = pd.read_parquet("output/create_final_relationships.parquet")
print(f"关系数量: {len(rels)}")
print(rels["source", "target", "description"]("source", "target", "description").head(10))

# 查看社区数量
communities = pd.read_parquet("output/create_final_community_reports.parquet")
print(f"社区数量: {len(communities)}")
```

> ⚠️ **成本参考：** 对于约 50 页文档（~25,000 token），使用 gpt-4o-mini 索引一次大约花费 $0.5-2。使用 gpt-4o 大约 $5-15。文档越多越贵，呈线性增长。
### 6.4 Local Search 与 Global Search 查询实战

索引建好后，用 CLI 直接查询：

```bash
# Local Search（适合有具体实体的问题）
graphrag query --root ./ \
  --method local \
  --query "张三参与过哪些项目？这些项目的当前状态如何？"

# Global Search（适合全局性问题）
graphrag query --root ./ \
  --method global \
  --query "这些文档涉及的主要业务方向有哪些？"
```

也可以用 Python API 实现更灵活的控制：

```python
import asyncio
from graphrag.query.cli import run_local_search, run_global_search

# Local Search
async def local_query():
    result = await run_local_search(
        root_dir="./",
        query="张三的领导是谁？他负责哪些项目？",
        community_level=2,
        response_type="multiple paragraphs"
    )
    print(result)

# Global Search  
async def global_query():
    result = await run_global_search(
        root_dir="./",
        query="总结这些文档中提到的所有技术栈",
        community_level=1,
        response_type="multiple paragraphs"
    )
    print(result)

asyncio.run(local_query())
```

**两种查询的效果对比：**

| 问题 | Local Search | Global Search |
|------|-------------|---------------|
| "张三参与了什么项目？" | ✅ 精准（沿图谱走） | ⚠️ 可能遗漏（需命中社区） |
| "公司面临哪些风险？" | ⚠️ 只看到局部 | ✅ 汇聚全局视角 |
| 延迟 | 快（秒级） | 慢（十秒级） |
| 成本 | 低（1-2 次 LLM 调用） | 高（N+1 次 LLM 调用） |
### 6.5 可视化：用 Neo4j 或 Gephi 看你的知识图谱

建好的图谱藏在 Parquet 文件里看不见摸不着。把它可视化出来，能直观验证图谱质量。

**方法一：导入 Neo4j（推荐）**

```python
import pandas as pd
from neo4j import GraphDatabase

# 读取实体和关系
entities = pd.read_parquet("output/create_final_entities.parquet")
rels = pd.read_parquet("output/create_final_relationships.parquet")

# 连接 Neo4j（先用 Docker 启动一个实例）
# docker run -d -p 7474:7474 -p 7687:7687 neo4j:latest
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    # 导入实体
    for _, e in entities.iterrows():
        session.run(
            "MERGE (n:Entity {name: $name}) SET n.type=$type, n.desc=$desc",
            name=e["title"], type=e["type"], desc=e.get("description","")
        )
    # 导入关系
    for _, r in rels.iterrows():
        session.run(
            """MATCH (a:Entity {name:$src}), (b:Entity {name:$tgt})
               MERGE (a)-[:RELATES {desc:$desc}]->(b)""",
            src=r["source"], tgt=r["target"], desc=r.get("description","")
        )
```

导入后打开 `http://localhost:7474`，在 Neo4j Browser 中执行 `MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100` 就能看到交互式的图谱可视化。

**方法二：用 Gephi 做静态可视化**

适合生成用于报告的高质量图谱图片。将实体和关系导出为 CSV，在 Gephi 中导入后用 Force Atlas 2 布局算法自动排列。

> 💡 **实用经验：** 可视化不只是"好看"——它是验证图谱质量最快的方式。如果你看到大量孤立节点（没有边连接），说明实体提取或消歧有问题。如果看到一个超大的"中心节点"连着几百条边，可能是实体类型太宽泛导致的。

---

## 7. LlamaIndex + Neo4j 方案：PropertyGraphIndex 实战

微软 GraphRAG 是"全家桶"——开箱即用但灵活度有限。如果你需要**更细粒度的控制**（自定义提取逻辑、接入已有的 Neo4j 数据库、和其他 RAG 组件混搭），LlamaIndex 的 PropertyGraphIndex 是更好的选择。

### 7.1 LlamaIndex PropertyGraphIndex 架构

```
LlamaIndex 方案 vs 微软方案：

  微软 GraphRAG：一体化管线，Parquet 存储，CLI 驱动
  LlamaIndex：  模块化组件，可插拔存储（Neo4j/Nebula/内存），API 驱动
```

核心区别：LlamaIndex 把 GraphRAG 拆成了**可替换的模块**——你可以单独替换实体提取器、图存储、检索策略中的任何一个，而不需要 fork 整个项目。

### 7.2 Neo4j 图数据库搭建与连接

```bash
# 用 Docker 一键启动 Neo4j
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  -v neo4j-data:/data \
  neo4j:5-community
```

```python
# LlamaIndex 连接 Neo4j
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

graph_store = Neo4jPropertyGraphStore(
    username="neo4j",
    password="your-password",
    url="bolt://localhost:7687",
    database="neo4j"
)
```

### 7.3 自定义实体提取器

LlamaIndex 允许你完全自定义提取逻辑——这在特定领域（医疗、法律、金融）特别有用：

```python
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor

# 定义领域特定的实体和关系类型
extractor = SchemaLLMPathExtractor(
    llm=llm,
    possible_entities=["EMPLOYEE", "DEPARTMENT", "PROJECT", "TECHNOLOGY"],
    possible_relations=["WORKS_IN", "MANAGES", "USES", "DEPENDS_ON"],
    strict=True  # 只允许定义的类型，拒绝"野生"实体
)
```

`strict=True` 是关键——它防止 LLM "发挥创意"提取出你不需要的实体类型，大幅降低噪音。

### 7.4 图谱检索与生成的完整管线

把上面的组件组装成完整管线：

```python
from llama_index.core import SimpleDirectoryReader, PropertyGraphIndex

# 1. 加载文档
documents = SimpleDirectoryReader("./data").load_data()

# 2. 构建图谱索引（自动提取实体/关系并存入 Neo4j）
index = PropertyGraphIndex.from_documents(
    documents,
    llm=llm,
    embed_model=embed_model,
    kg_extractors=[extractor],
    property_graph_store=graph_store,
    show_progress=True
)

# 3. 查询
query_engine = index.as_query_engine(
    include_text=True,       # 混合检索：图谱 + 原始文本
    similarity_top_k=5
)

response = query_engine.query("张三的领导负责过哪些延期的项目？")
print(response)
```

> 💡 **选择建议：** 如果你只想快速验证 GraphRAG 效果 → 用微软 GraphRAG。如果你要在生产环境中集成、需要自定义或已有 Neo4j → 用 LlamaIndex。两者都能完成同样的任务，区别在灵活度和上手难度。

---

## 8. 性能优化与成本控制

GraphRAG 最大的痛点就两个字：**贵**和**慢**。本章专治这两个病。

### 8.1 索引成本分析：Token 消耗与时间开销

```
成本公式（粗算）：

  索引成本 ≈ 文档块数 × 每块提取的 Token 消耗 × 模型单价
           + 社区数 × 摘要 Token 消耗 × 模型单价

  实际参考（50 页文档，~100 个块）：
  ┌──────────────┬──────────┬──────────┐
  │ 模型          │ 索引成本  │ 索引时间  │
  ├──────────────┼──────────┼──────────┤
  │ gpt-4o       │ $5-15    │ 15-30 分钟│
  │ gpt-4o-mini  │ $0.5-2   │ 10-20 分钟│
  │ 本地 Qwen2.5 │ $0（电费）│ 30-60 分钟│
  └──────────────┴──────────┴──────────┘
```

### 8.2 增量索引：文档更新时不用全量重建

全量重建索引是最大的成本黑洞。微软 GraphRAG 已支持增量索引（`graphrag update`），只处理新增和修改的文档：

```bash
# 增量更新（只处理 input/ 中新增/修改的文件）
graphrag update --root ./
```

如果你用的框架不支持原生增量更新，也可以手动实现：只对新文档提取实体/关系，与现有图谱合并，然后重新跑社区检测和摘要。

### 8.3 本地模型替代：用 Ollama/vLLM 降低成本

把 API 调用换成本地模型，索引成本直接**降为 0**（只付电费）：

```yaml
# settings.yaml 配置本地模型
llm:
  api_base: http://localhost:11434/v1   # Ollama 端点
  model: qwen2.5:14b                    # 或 llama3.1:70b
  api_key: ollama                       # Ollama 不需要真实 key
```

```bash
# 先启动 Ollama 并拉取模型
ollama serve
ollama pull qwen2.5:14b
```

**质量 vs 成本的权衡：**

| 方案 | 提取质量 | 索引成本 | 适用场景 |
|------|---------|---------|---------|
| gpt-4o | ⭐⭐⭐⭐⭐ | $$$ | 生产环境、高质量要求 |
| gpt-4o-mini | ⭐⭐⭐⭐ | $ | 多数场景的最佳性价比 |
| Qwen2.5-14B | ⭐⭐⭐ | 免费 | 开发测试、成本敏感 |
| Llama3.1-70B | ⭐⭐⭐⭐ | 免费 | 有 GPU 的团队 |

### 8.4 缓存与预计算：加速查询响应

查询延迟的优化策略：

- **社区摘要缓存**：Global Search 的 Map 阶段结果可以缓存——同一个社区对相似问题的局部回答不会变化太大
- **实体 Embedding 预计算**：提前计算所有实体描述的 Embedding，查询时直接做向量匹配找起始实体
- **热点子图预加载**：把高频访问的实体（如核心人物、重点项目）的子图预加载到内存

> 💡 **80/20 法则：** 索引阶段换 gpt-4o-mini 就能省 80% 的钱。查询阶段加上实体 Embedding 预计算就能省 80% 的延迟。不要过度优化。

---

## 9. GraphRAG vs 标准 RAG：何时用哪个

这是最实用的一章——帮你做**选型决策**，避免为了用 GraphRAG 而用 GraphRAG。

### 9.1 决策矩阵：复杂度、成本、效果三角

```
决策三角：

        效果（回答质量）
           ▲
          / \
         /   \        GraphRAG 在右上角——
        /     \       效果好但成本高、复杂度高
       /       \
      /    ★    \     标准 RAG 在左下角——
     /  GraphRAG \    简单便宜，效果够用
    /             \
   ────────────────▶ 成本
  复杂度
```

### 9.2 适合 GraphRAG 的典型场景

| 场景 | 为什么适合 | 示例 |
|------|----------|------|
| 企业知识管理 | 人员、部门、项目之间关系密集 | "谁负责过类似的项目？" |
| 法律/合规分析 | 法规、案例、条款之间有复杂引用关系 | "这条法规影响哪些业务？" |
| 医疗知识库 | 疾病、症状、药物之间多对多关系 | "这个药和哪些药有禁忌？" |
| 学术文献分析 | 论文、作者、引用构成天然图谱 | "这个领域的关键贡献者？" |
| 供应链管理 | 供应商、零件、产品的依赖关系 | "这个零件断供影响哪些产品？" |

### 9.3 不适合 GraphRAG 的场景：杀鸡别用牛刀

| 场景 | 为什么不适合 | 用什么替代 |
|------|------------|----------|
| 简单 FAQ 问答 | 答案就在一个片段里，不需要推理 | 标准 RAG |
| 实时数据查询 | 数据频繁变化，图谱来不及更新 | 直接查数据库 |
| 文档量极小 | 10 页文档建图谱大材小用 | 直接塞进 prompt |
| 预算极有限 | 索引成本不可接受 | 标准 RAG + 好的分块策略 |

### 9.4 混合架构：GraphRAG + 标准 RAG 的互补方案

最务实的方案往往是**两者都用**：

```
混合架构：

  知识库
    ├── 结构化/关系密集的部分 → GraphRAG 索引
    │   （人员关系、项目依赖、组织架构…）
    │
    └── 非结构化/细节丰富的部分 → 标准 RAG 索引
        （操作手册、技术文档、FAQ…）

  查询路由器
    ├── 关系类问题 → GraphRAG
    ├── 全局摘要类 → GraphRAG (Global Search)
    └── 事实查询类 → 标准 RAG
```

> 💡 **一句话决策：** 如果你的问题可以用"在哪个文档的第几页"来回答 → 标准 RAG。如果你的问题需要"连接多个文档中的信息"才能回答 → GraphRAG。

---

## 10. 生产部署与最佳实践

把 GraphRAG 从 Demo 推到生产，需要解决三个核心问题：**图谱质量怎么保证、怎么持续改进、怎么和现有系统集成。**

### 10.1 图谱质量监控：实体准确率和关系覆盖率

图谱质量需要**量化监控**，不能靠"看起来差不多"：

| 指标 | 计算方式 | 健康阈值 |
|------|---------|---------|
| 实体准确率 | 抽样 100 个实体，人工判断正确比例 | > 85% |
| 关系覆盖率 | 抽取 50 个已知关系，检查图谱是否包含 | > 70% |
| 孤立节点比例 | 无边连接的节点数 / 总节点数 | < 15% |
| 重复实体率 | 消歧后仍存在的重复 / 总实体数 | < 5% |

```python
# 自动化质量检查脚本
entities = pd.read_parquet("output/create_final_entities.parquet")
rels = pd.read_parquet("output/create_final_relationships.parquet")

# 孤立节点检测
connected = set(rels["source"].tolist() + rels["target"].tolist())
isolated = entities[~entities["title"].isin(connected)]
print(f"孤立节点比例: {len(isolated)/len(entities)*100:.1f}%")
```

### 10.2 实体提取的持续优化：反馈闭环

图谱质量不是"建好就完了"——需要**持续迭代**：

1. **收集错误案例**：记录查询失败的 case，分析是提取遗漏还是消歧错误
2. **优化提取 Prompt**：根据错误案例调整实体类型定义和提取指令
3. **补充领域词典**：为领域术语建立同义词表，提升消歧准确率
4. **定期重建**：每月全量重建一次，吸收 Prompt 优化的成果

### 10.3 与现有 RAG 系统的集成策略

如果你已有一个标准 RAG 系统，不需要推倒重来：

```
渐进式集成路径：

  阶段 1：在现有 RAG 旁边加一个 GraphRAG 索引
          → 只用于关系类查询，其他查询走原有管线

  阶段 2：加入查询路由器
          → 自动判断用 GraphRAG 还是标准 RAG

  阶段 3：混合检索
          → 同时走两条路径，合并上下文给 LLM
```

### 10.4 前沿方向：Agentic GraphRAG 与自进化图谱

**Agentic GraphRAG：** 让 AI Agent 在推理过程中**动态扩展图谱**——遇到图谱中没有的实体时，自动从外部数据源提取并补充。图谱从"静态索引"变成"活的知识网络"。

**自进化图谱：** 用户的查询记录本身就包含知识——"A 和 B 有什么关系？"暗示了用户认为 A 和 B 之间存在关联。系统可以利用这些查询信号来发现和补充图谱中缺失的关系。

> 💡 **核心原则：** GraphRAG 在生产中的价值不在于"一次建好"，而在于**持续迭代**——图谱质量的每一次提升，都直接转化为回答质量的提升。

---

## 11. 延伸阅读与参考资料

### 11.1 核心论文与官方文档

| 文献 | 核心贡献 |
|------|---------|
| [From Local to Global: A Graph RAG Approach - Microsoft (2024)](https://arxiv.org/abs/2404.16130) | GraphRAG 原始论文，提出 Local/Global Search 和社区摘要 |
| [Retrieval-Augmented Generation for Knowledge-Intensive NLP - Meta (2020)](https://arxiv.org/abs/2005.11401) | RAG 范式的奠基论文 |
| [Google Knowledge Graph (2012)](https://blog.google/products/search/introducing-knowledge-graph-things-not/) | 知识图谱概念进入主流 |
| [Community Detection: Leiden Algorithm - Traag et al. (2019)](https://www.nature.com/articles/s41598-019-41695-z) | Leiden 社区检测算法 |

### 11.2 开源项目与工具链

| 项目 | 用途 | 链接 |
|------|------|------|
| Microsoft GraphRAG | 官方参考实现 | [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag) |
| LlamaIndex | 模块化 RAG/GraphRAG 框架 | [llamaindex.ai](https://www.llamaindex.ai/) |
| Nano-GraphRAG | 轻量级 GraphRAG 实现 | [github.com/gusye1234/nano-graphrag](https://github.com/gusye1234/nano-graphrag) |
| LightRAG | 简化版 GraphRAG | [github.com/HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) |
| Neo4j | 图数据库 | [neo4j.com](https://neo4j.com/) |
| Gephi | 图谱可视化 | [gephi.org](https://gephi.org/) |
| Ollama | 本地模型运行 | [ollama.ai](https://ollama.ai/) |

### 11.3 社区资源与进阶教程

- [GraphRAG Accelerator - Microsoft](https://github.com/Azure-Samples/graphrag-accelerator)：Azure 上的 GraphRAG 部署加速器
- [LlamaIndex Property Graph Guide](https://docs.llamaindex.ai/en/stable/examples/property_graph/)：官方 PropertyGraphIndex 教程
- [Neo4j GenAI Ecosystem](https://neo4j.com/labs/genai-ecosystem/)：Neo4j 的 AI 生态集成
- [GraphRAG 中文社区](https://github.com/topics/graphrag)：GitHub 上的 GraphRAG 相关项目汇总

---

> **全书完。**
>
> GraphRAG 的核心就一句话：**把文档从"一堆碎片"变成"一张网"，让 AI 不仅能"搜"到答案，更能"连"出答案。**
>
> 从今天开始：先用标准 RAG 解决 80% 的问题，再用 GraphRAG 攻克剩下 20% 的硬骨头。四个文件起步——`settings.yaml`、你的文档、一个 API Key、一行 `graphrag index` 命令。
>
> 祝你的知识图谱越连越密。 🕸️
