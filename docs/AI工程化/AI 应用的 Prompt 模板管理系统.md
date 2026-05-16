# AI 应用的 Prompt 模板管理系统

> 当你的 AI 应用有几十上百个 Prompt 时，硬编码在代码里就是灾难。本教程教你构建一套工程化的 Prompt 管理体系——版本控制、A/B 测试、效果评估、动态加载，让 Prompt 像代码一样可维护。

---

## 1. 为什么需要 Prompt 管理？

你的第一个 AI 应用可能只有 1-2 个 Prompt，写在代码里没什么问题。但当 Prompt 数量增长到几十个、需要频繁迭代、多人协作时——硬编码就是一场灾难。

### 1.1 硬编码 Prompt 的五大痛点

```python
# ❌ 典型的硬编码现状
def analyze_sentiment(text):
    response = llm.invoke(f"""你是一个情感分析专家。
请分析以下文本的情感倾向，返回 JSON 格式：
{{"sentiment": "positive/negative/neutral", "confidence": 0.0-1.0}}

文本：{text}""")
    return response

# 痛点 1：散落在代码各处，找不到
# → 20 个文件里有 40 个 prompt，改一个要全局搜索

# 痛点 2：无法追溯历史版本
# → "上周那版 prompt 效果更好，但我已经改掉了"

# 痛点 3：无法做 A/B 测试
# → "新 prompt 到底好不好？凭感觉？"

# 痛点 4：开发/测试/生产不一致
# → 开发环境用便宜模型+简短 prompt，上线后效果差

# 痛点 5：多人协作冲突
# → 产品经理改了 prompt，开发不知道，部署后出 bug
```

### 1.2 Prompt 是 AI 应用的"源代码"

```
传统软件：
  代码（Java/Python）决定了程序的行为
  → 代码有版本控制、Code Review、CI/CD

AI 应用：
  Prompt 决定了 LLM 的行为
  → 但 Prompt 通常没有版本控制、没有 Review、没有测试

结论：Prompt 应该像代码一样被管理！
```

| 传统代码管理 | Prompt 管理（应该做到） |
|:---|:---|
| Git 版本控制 | Prompt 版本控制 |
| Code Review | Prompt Review |
| 单元测试 | 效果评估（Golden Set） |
| A/B 测试 | Prompt A/B 测试 |
| 环境隔离（dev/prod） | Prompt 多环境管理 |
| 配置中心 | Prompt 动态加载 |

### 1.3 一个好的 Prompt 管理系统长什么样？

```
理想的 Prompt 管理系统：

📝 模板化：Prompt 与代码分离，用模板引擎管理变量
📦 版本化：每次修改都有记录，随时可回滚
🔄 动态化：不重启服务就能切换 Prompt
🧪 可测试：自动评估 Prompt 效果，A/B 对比
📊 可观测：监控每个 Prompt 的调用量、成功率、成本
👥 协作性：多人可以安全地修改和 Review Prompt
```

> 💡 **本教程的目标**：带你从零构建这样一个系统。不依赖任何付费 SaaS，全部用 Python 实现。

---

## 2. Prompt 模板设计：从字符串到结构化模板

把 Prompt 从代码里抽出来的第一步——用**模板引擎**管理变量，用**类型系统**保证安全。

### 2.1 从 f-string 到 Jinja2 模板引擎

```python
# ❌ Level 0：f-string 硬编码
prompt = f"你是{role}，请{task}，输入：{user_input}"

# ✅ Level 1：Jinja2 模板（Prompt 与代码分离）
from jinja2 import Template

template_str = """你是一个{{ role }}。

请完成以下任务：{{ task }}

{% if examples %}
以下是一些示例：
{% for ex in examples %}
输入：{{ ex.input }}
输出：{{ ex.output }}
{% endfor %}
{% endif %}

用户输入：{{ user_input }}"""

template = Template(template_str)
prompt = template.render(
    role="情感分析专家",
    task="分析文本的情感倾向",
    examples=[
        {"input": "今天真开心", "output": "positive"},
        {"input": "太失望了", "output": "negative"},
    ],
    user_input="这个产品不错",
)
```

**为什么用 Jinja2 而不是 f-string？**

| 特性 | f-string | Jinja2 |
|:---|:---|:---|
| 条件渲染 | ❌ | ✅ `{% if %}` |
| 循环 | ❌ | ✅ `{% for %}` |
| 模板继承 | ❌ | ✅ `{% extends %}` |
| 与代码分离 | ❌ | ✅ 从文件加载 |
| 安全性 | ❌ 可注入 | ✅ 自动转义 |

### 2.2 变量定义与类型校验（Pydantic）

Prompt 模板的变量必须有明确的**类型定义**——否则传错参数只有运行时才发现：

```python
from pydantic import BaseModel, Field
from typing import Optional
from jinja2 import Template

class SentimentPromptVars(BaseModel):
    """情感分析 Prompt 的变量定义"""
    role: str = Field(default="情感分析专家", description="AI 角色")
    user_input: str = Field(..., description="要分析的文本", min_length=1)
    output_format: str = Field(default="json", description="输出格式：json/text")
    examples: Optional[list[dict]] = Field(default=None, description="Few-shot 示例")

# 使用时：类型不对会立刻报错
vars = SentimentPromptVars(user_input="这个产品不错")  # ✅
vars = SentimentPromptVars(user_input="")               # ❌ ValidationError: min_length
vars = SentimentPromptVars()                             # ❌ ValidationError: user_input required
```

### 2.3 模板组合与继承：System + User + Few-shot

实际的 Prompt 通常由多个部分组成，可以定义**可复用的组件**：

```python
# ── 基础组件 ──
SYSTEM_BASE = """你是一个{{ role }}。
你的回答风格：{{ style | default('专业、简洁') }}
输出格式：{{ output_format | default('纯文本') }}"""

FEW_SHOT_BLOCK = """{% if examples %}
以下是一些示例，请参考格式：
{% for ex in examples %}
---
输入：{{ ex.input }}
输出：{{ ex.output }}
{% endfor %}
---
{% endif %}"""

USER_INPUT_BLOCK = """请处理以下内容：
{{ user_input }}"""

# ── 组合成完整 Prompt ──
SENTIMENT_PROMPT = f"""{SYSTEM_BASE}

{FEW_SHOT_BLOCK}

{USER_INPUT_BLOCK}"""
```

### 2.4 实操：构建一个类型安全的 PromptTemplate 类

把前面的思路封装成一个通用的 `PromptTemplate` 类：

```python
from pydantic import BaseModel
from jinja2 import Template, Environment, FileSystemLoader
from typing import Type, Any
import yaml

class PromptTemplate:
    """类型安全的 Prompt 模板"""
    
    def __init__(
        self,
        name: str,
        template: str,
        variables_schema: Type[BaseModel],
        metadata: dict | None = None,
    ):
        self.name = name
        self.template = Template(template)
        self.variables_schema = variables_schema
        self.metadata = metadata or {}
    
    def render(self, **kwargs) -> str:
        """渲染模板（自动做类型校验）"""
        # 校验变量类型
        validated = self.variables_schema(**kwargs)
        # 渲染模板
        return self.template.render(**validated.model_dump())
    
    @classmethod
    def from_yaml(cls, path: str, variables_schema: Type[BaseModel]) -> "PromptTemplate":
        """从 YAML 文件加载"""
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return cls(
            name=config["name"],
            template=config["template"],
            variables_schema=variables_schema,
            metadata=config.get("metadata", {}),
        )

# ── 使用 ──
sentiment_template = PromptTemplate(
    name="sentiment_analysis",
    template=SENTIMENT_PROMPT,
    variables_schema=SentimentPromptVars,
    metadata={"version": "1.2.0", "author": "team-ai"},
)

prompt = sentiment_template.render(user_input="这个产品质量很好，值得推荐！")
print(prompt)
```

> 💡 **核心收获**：Prompt 不再是散落在代码里的字符串——它是一个有名字、有版本、有类型校验的**一等对象**。

---

## 3. 版本控制：让每一版 Prompt 都可追溯

Prompt 的每一次修改都可能影响 AI 的输出质量。你需要知道**谁、什么时候、改了什么、为什么改**。

### 3.1 Prompt 的文件组织规范

```yaml
# prompts/sentiment_analysis/v1.2.0.yaml

name: sentiment_analysis
version: "1.2.0"
author: "alice"
created_at: "2024-03-15"
description: "情感分析 Prompt，支持中英文"

metadata:
  model: "deepseek-chat"
  temperature: 0.3
  max_tokens: 256
  tags: ["nlp", "sentiment", "production"]

template: |
  你是一个情感分析专家。
  
  请分析以下文本的情感倾向，返回 JSON 格式：
  {"sentiment": "positive/negative/neutral", "confidence": 0.0-1.0, "reason": "简短原因"}
  
  {% if examples %}
  参考示例：
  {% for ex in examples %}
  输入：{{ ex.input }} → 输出：{{ ex.output }}
  {% endfor %}
  {% endif %}
  
  文本：{{ user_input }}

variables:
  - name: user_input
    type: string
    required: true
    description: "要分析的文本"
  - name: examples
    type: list
    required: false
    description: "Few-shot 示例"
```

### 3.2 用 Git 管理 Prompt 版本

```bash
# 推荐的项目结构
my-ai-app/
├── src/                    # 应用代码
├── prompts/                # Prompt 模板（独立目录！）
│   ├── sentiment/
│   │   ├── v1.0.0.yaml
│   │   ├── v1.1.0.yaml
│   │   └── v1.2.0.yaml    # 当前生产版本
│   ├── summarize/
│   │   ├── v1.0.0.yaml
│   │   └── v2.0.0.yaml
│   └── customer_service/
│       └── v1.0.0.yaml
├── tests/
│   └── test_prompts/       # Prompt 的测试用例
│       ├── test_sentiment.py
│       └── golden_set/     # 标准评测数据集
└── prompt_config.yaml      # 各环境使用哪个版本
```

```bash
# Git 操作示例
git add prompts/sentiment/v1.2.0.yaml
git commit -m "feat(prompt): sentiment v1.2.0 - 增加 reason 字段输出"
git tag prompt-sentiment-v1.2.0
```

### 3.3 语义化版本 + 变更日志

对 Prompt 使用和代码一样的语义化版本：

```
版本号规则：MAJOR.MINOR.PATCH

MAJOR（主版本）：输出格式变化、角色重新定义
  v1.0 → v2.0: 输出从纯文本改成 JSON

MINOR（次版本）：功能增加、效果优化
  v1.1 → v1.2: 增加 Few-shot 示例、优化措辞

PATCH（补丁）：措辞微调、修复 typo
  v1.2.0 → v1.2.1: 修复"分折"→"分析"
```

```yaml
# prompts/sentiment/CHANGELOG.yaml
changelog:
  - version: "1.2.0"
    date: "2024-03-15"
    author: "alice"
    changes: "增加 reason 字段，要求模型给出判断理由"
    impact: "输出 JSON 多了一个字段，需要下游适配"
    
  - version: "1.1.0"
    date: "2024-03-10"
    author: "bob"
    changes: "增加 Few-shot 示例支持"
    impact: "效果提升约 15%（基于 Golden Set 评估）"
```

### 3.4 实操：设计一套 Prompt 目录结构

```python
import yaml
from pathlib import Path

class PromptRegistry:
    """Prompt 注册中心：管理所有 Prompt 的加载和版本"""
    
    def __init__(self, prompts_dir: str = "./prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._cache = {}
    
    def get(self, name: str, version: str = "latest") -> dict:
        """获取指定版本的 Prompt"""
        prompt_dir = self.prompts_dir / name
        
        if version == "latest":
            # 找最新版本
            versions = sorted(prompt_dir.glob("v*.yaml"))
            if not versions:
                raise FileNotFoundError(f"No prompts found for '{name}'")
            path = versions[-1]
        else:
            path = prompt_dir / f"v{version}.yaml"
        
        if not path.exists():
            raise FileNotFoundError(f"Prompt '{name}' v{version} not found")
        
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def list_versions(self, name: str) -> list[str]:
        """列出某个 Prompt 的所有版本"""
        prompt_dir = self.prompts_dir / name
        return sorted([f.stem for f in prompt_dir.glob("v*.yaml")])

# 使用
registry = PromptRegistry("./prompts")
prompt = registry.get("sentiment", version="1.2.0")
print(f"加载 Prompt: {prompt['name']} v{prompt['version']}")
print(f"所有版本: {registry.list_versions('sentiment')}")
```

> 💡 **核心原则**：Prompt 的每一次修改都要留痕。三个月后当你需要回滚时，会感谢自己的。

---

## 4. 动态加载：运行时切换 Prompt

生产环境中，你不可能每次改 Prompt 都重新部署。**动态加载**让你不重启服务就能切换 Prompt。

### 4.1 从文件系统加载（YAML/JSON）

```python
import yaml
from pathlib import Path
from jinja2 import Template

class FilePromptLoader:
    """从文件系统加载 Prompt"""
    
    def __init__(self, base_dir: str = "./prompts"):
        self.base_dir = Path(base_dir)
    
    def load(self, name: str, version: str = "latest") -> dict:
        prompt_dir = self.base_dir / name
        
        if version == "latest":
            files = sorted(prompt_dir.glob("v*.yaml"))
            path = files[-1] if files else None
        else:
            path = prompt_dir / f"v{version}.yaml"
        
        if not path or not path.exists():
            raise FileNotFoundError(f"{name} v{version}")
        
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        return {
            "name": config["name"],
            "version": config["version"],
            "template": Template(config["template"]),
            "metadata": config.get("metadata", {}),
        }

loader = FilePromptLoader()
prompt = loader.load("sentiment", "1.2.0")
result = prompt["template"].render(user_input="这个产品不错")
```

### 4.2 从数据库加载（SQLite/PostgreSQL）

当 Prompt 数量很多、需要通过后台管理界面编辑时，用数据库更方便：

```python
import sqlite3
from datetime import datetime

class DBPromptStore:
    """数据库 Prompt 存储"""
    
    def __init__(self, db_path: str = "prompts.db"):
        self.conn = sqlite3.connect(db_path)
        self._init_db()
    
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                template TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                UNIQUE(name, version)
            )
        """)
        self.conn.commit()
    
    def save(self, name: str, version: str, template: str, **kwargs):
        self.conn.execute(
            "INSERT INTO prompts (name, version, template, created_by) VALUES (?, ?, ?, ?)",
            (name, version, template, kwargs.get("author", "system")),
        )
        self.conn.commit()
    
    def get_active(self, name: str) -> dict | None:
        """获取当前激活版本"""
        row = self.conn.execute(
            "SELECT * FROM prompts WHERE name=? AND is_active=1", (name,)
        ).fetchone()
        return self._row_to_dict(row) if row else None
    
    def activate(self, name: str, version: str):
        """激活指定版本（同时停用其他版本）"""
        self.conn.execute("UPDATE prompts SET is_active=0 WHERE name=?", (name,))
        self.conn.execute(
            "UPDATE prompts SET is_active=1 WHERE name=? AND version=?",
            (name, version),
        )
        self.conn.commit()
```

### 4.3 热更新：不重启服务就切换 Prompt

```python
import time
import threading

class HotReloadPromptManager:
    """支持热更新的 Prompt 管理器"""
    
    def __init__(self, store: DBPromptStore, reload_interval: int = 60):
        self._store = store
        self._cache = {}
        self._reload_interval = reload_interval
        self._start_auto_reload()
    
    def get(self, name: str) -> dict:
        """获取 Prompt（优先从缓存读取）"""
        if name not in self._cache:
            self._cache[name] = self._store.get_active(name)
        return self._cache[name]
    
    def _reload(self):
        """定期从数据库刷新缓存"""
        while True:
            time.sleep(self._reload_interval)
            self._cache.clear()  # 清空缓存，下次访问时从 DB 重新加载
            print(f"[{time.strftime('%H:%M:%S')}] Prompt 缓存已刷新")
    
    def _start_auto_reload(self):
        thread = threading.Thread(target=self._reload, daemon=True)
        thread.start()

# 使用：修改数据库中的 Prompt → 最多等 60 秒自动生效
manager = HotReloadPromptManager(store, reload_interval=60)
```

### 4.4 多环境管理：dev / staging / production

```yaml
# prompt_config.yaml — 配置各环境使用的 Prompt 版本

environments:
  development:
    sentiment: "latest"          # 开发环境用最新版
    summarize: "latest"
    customer_service: "latest"
  
  staging:
    sentiment: "1.2.0"           # 预发布环境用指定版本
    summarize: "2.0.0"
    customer_service: "1.0.0"
  
  production:
    sentiment: "1.1.0"           # 生产环境用经过验证的版本
    summarize: "1.5.0"
    customer_service: "1.0.0"
```

```python
import os

class EnvPromptManager:
    """根据环境加载对应版本的 Prompt"""
    
    def __init__(self, config_path: str = "prompt_config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.env = os.getenv("APP_ENV", "development")
        self.loader = FilePromptLoader()
    
    def get(self, name: str) -> dict:
        version = self.config["environments"][self.env].get(name, "latest")
        return self.loader.load(name, version)

# 不同环境自动加载不同版本
# APP_ENV=production → sentiment v1.1.0
# APP_ENV=development → sentiment latest
```

> 💡 **生产环境铁律**：永远锁定版本号，不要用 `latest`。确保每次部署用的 Prompt 是完全可预测的。

---

## 5. A/B 测试：科学地优化 Prompt

"新 Prompt 效果好不好？"——别凭感觉，用数据说话。

### 5.1 为什么 Prompt 需要 A/B 测试？

```
没有 A/B 测试的 Prompt 迭代：

产品经理：  "我觉得新 Prompt 更好"
开发：      "我觉得旧的更好"
老板：      "到底哪个好？"
所有人：    "...不知道" 🤷

有 A/B 测试的 Prompt 迭代：

数据显示：  新 Prompt 准确率 92% vs 旧版 85%，p < 0.05
所有人：    "上新版！" ✅
```

### 5.2 A/B 测试框架设计

```python
import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ABExperiment:
    """一个 A/B 测试实验"""
    name: str
    prompt_a: dict        # 控制组（当前版本）
    prompt_b: dict        # 实验组（新版本）
    traffic_ratio: float = 0.5  # B 组流量占比
    start_time: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    results: dict = field(default_factory=lambda: {"a": [], "b": []})

class ABTestManager:
    """Prompt A/B 测试管理器"""
    
    def __init__(self):
        self.experiments = {}
    
    def create_experiment(self, name: str, prompt_a: dict, prompt_b: dict,
                          traffic_ratio: float = 0.5) -> ABExperiment:
        exp = ABExperiment(
            name=name, prompt_a=prompt_a, prompt_b=prompt_b,
            traffic_ratio=traffic_ratio,
        )
        self.experiments[name] = exp
        return exp
    
    def get_prompt(self, experiment_name: str, user_id: str) -> tuple[str, dict]:
        """根据用户 ID 分配 Prompt，返回 (组名, prompt)"""
        exp = self.experiments[experiment_name]
        if not exp.is_active:
            return "a", exp.prompt_a
        
        # 用 user_id 的哈希值做确定性分组（同一用户始终在同一组）
        hash_val = int(hashlib.md5(f"{experiment_name}:{user_id}".encode()).hexdigest(), 16)
        group = "b" if (hash_val % 100) < (exp.traffic_ratio * 100) else "a"
        
        return group, exp.prompt_a if group == "a" else exp.prompt_b
    
    def record_result(self, experiment_name: str, group: str, score: float):
        """记录测试结果"""
        self.experiments[experiment_name].results[group].append(score)
```

### 5.3 流量分配与用户分组

```
流量分配策略：

1. 固定比例分流（推荐）
   A: 50% | B: 50%  ← 标准做法
   A: 90% | B: 10%  ← 谨慎测试（新 Prompt 风险高时）

2. 基于用户 ID 的确定性分组
   user_123 → 永远在 A 组
   user_456 → 永远在 B 组
   → 保证同一用户体验一致

3. 逐步放量
   第 1 天：A:95% B:5%   观察有无严重问题
   第 3 天：A:80% B:20%  扩大样本量
   第 7 天：A:50% B:50%  正式对比
```

### 5.4 实操：构建一个 Prompt A/B 测试系统

```python
from statistics import mean

# ── 创建实验 ──
ab_manager = ABTestManager()

ab_manager.create_experiment(
    name="sentiment_v1.1_vs_v1.2",
    prompt_a={"version": "1.1.0", "template": "...旧版 prompt..."},
    prompt_b={"version": "1.2.0", "template": "...新版 prompt（加了 reason 字段）..."},
    traffic_ratio=0.5,
)

# ── 业务代码中使用 ──
def analyze_sentiment(user_id: str, text: str):
    group, prompt = ab_manager.get_prompt("sentiment_v1.1_vs_v1.2", user_id)
    
    # 调用 LLM
    result = llm.invoke(prompt["template"].replace("{{ user_input }}", text))
    
    # 评分（可以是自动评分或人工评分）
    score = auto_evaluate(text, result)  # 返回 0-1 的分数
    ab_manager.record_result("sentiment_v1.1_vs_v1.2", group, score)
    
    return result

# ── 查看实验结果 ──
def get_experiment_report(name: str):
    exp = ab_manager.experiments[name]
    a_scores = exp.results["a"]
    b_scores = exp.results["b"]
    
    print(f"实验: {name}")
    print(f"A 组 ({exp.prompt_a['version']}): {len(a_scores)} 样本, 平均分 {mean(a_scores):.3f}")
    print(f"B 组 ({exp.prompt_b['version']}): {len(b_scores)} 样本, 平均分 {mean(b_scores):.3f}")
    
    # 简单的统计检验
    from scipy import stats
    t_stat, p_value = stats.ttest_ind(a_scores, b_scores)
    print(f"p-value: {p_value:.4f} ({'显著' if p_value < 0.05 else '不显著'})")
```

> 💡 **实用建议**：至少收集 100+ 样本再做结论。样本太少的 A/B 测试结果不可信。

---

## 6. 效果评估：量化 Prompt 的好坏

A/B 测试告诉你"哪个更好"，但**效果评估**告诉你"到底好到什么程度"。

### 6.1 评估维度：准确性、一致性、安全性、成本

| 维度 | 衡量什么 | 评估方法 |
|:---|:---|:---|
| **准确性** | 回答是否正确 | Golden Set 对比 |
| **一致性** | 同类问题回答风格是否统一 | 批量测试 + 人工检查 |
| **格式合规** | 是否按要求的格式输出（JSON等） | 正则/Schema 校验 |
| **安全性** | 是否拒绝不当请求 | 对抗测试样本 |
| **成本** | Token 用量和延迟 | API 日志统计 |
| **用户满意度** | 用户反馈（点赞/点踩） | 线上埋点 |

### 6.2 构建标准评估数据集（Golden Set）

```python
# golden_set/sentiment.json — 标准评测数据集
golden_set = [
    {
        "input": "这个手机拍照效果非常好，画质清晰",
        "expected": {"sentiment": "positive", "confidence_min": 0.8},
        "category": "product_review",
    },
    {
        "input": "快递太慢了，等了一个星期",
        "expected": {"sentiment": "negative", "confidence_min": 0.7},
        "category": "logistics",
    },
    {
        "input": "还行吧，一般般",
        "expected": {"sentiment": "neutral", "confidence_min": 0.5},
        "category": "ambiguous",
    },
    {
        "input": "价格便宜但质量差",
        "expected": {"sentiment": "negative", "confidence_min": 0.6},
        "category": "mixed",  # 混合情感，更考验模型
    },
    # ... 至少准备 50~100 条
]
```

**Golden Set 的构建原则：**

```
✅ 覆盖各种场景（正面/负面/中性/混合/边界情况）
✅ 包含"陷阱"样本（容易判错的case）
✅ 有标准答案供自动对比
✅ 定期更新（业务变化时）
```

### 6.3 自动评测流水线：批量跑 + 自动打分

```python
import json
from dataclasses import dataclass

@dataclass
class EvalResult:
    total: int = 0
    correct: int = 0
    format_valid: int = 0
    errors: list = None
    
    def __post_init__(self):
        self.errors = self.errors or []
    
    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0
    
    @property
    def format_rate(self) -> float:
        return self.format_valid / self.total if self.total else 0

class PromptEvaluator:
    """Prompt 自动评测器"""
    
    def __init__(self, llm, prompt_template):
        self.llm = llm
        self.prompt_template = prompt_template
    
    def evaluate(self, golden_set: list[dict]) -> EvalResult:
        result = EvalResult()
        
        for item in golden_set:
            result.total += 1
            
            # 用 Prompt 模板生成请求
            prompt = self.prompt_template.render(user_input=item["input"])
            response = self.llm.invoke(prompt)
            
            # 检查格式是否合规
            try:
                parsed = json.loads(response)
                result.format_valid += 1
            except json.JSONDecodeError:
                result.errors.append({"input": item["input"], "error": "JSON 解析失败"})
                continue
            
            # 检查准确性
            expected = item["expected"]
            if parsed.get("sentiment") == expected["sentiment"]:
                result.correct += 1
            else:
                result.errors.append({
                    "input": item["input"],
                    "expected": expected["sentiment"],
                    "got": parsed.get("sentiment"),
                })
        
        return result

# ── 运行评测 ──
evaluator = PromptEvaluator(llm, sentiment_template)
result = evaluator.evaluate(golden_set)
print(f"准确率: {result.accuracy:.1%}")
print(f"格式合规率: {result.format_rate:.1%}")
print(f"错误样本: {len(result.errors)}")
```

### 6.4 LLM-as-Judge：用大模型评估大模型

对于没有标准答案的开放式任务（如客服回复质量），可以用更强的模型来做评委：

```python
JUDGE_PROMPT = """你是一个严格的质量评审专家。请对以下 AI 回复评分。

用户问题：{question}
AI 回复：{answer}

评分标准（每项 1-5 分）：
1. 准确性：回答是否正确、有无事实错误
2. 完整性：是否覆盖了问题的所有方面
3. 友好度：语气是否专业友好
4. 简洁性：是否简洁不啰嗦

请严格按以下 JSON 格式返回：
{{"accuracy": 1-5, "completeness": 1-5, "friendliness": 1-5, "conciseness": 1-5, "overall": 1-5, "comment": "简短评价"}}"""

def llm_judge(question: str, answer: str, judge_llm) -> dict:
    prompt = JUDGE_PROMPT.format(question=question, answer=answer)
    response = judge_llm.invoke(prompt)
    return json.loads(response)

# 批量评测
scores = []
for item in test_cases:
    score = llm_judge(item["question"], item["answer"], gpt4)
    scores.append(score)

avg_overall = sum(s["overall"] for s in scores) / len(scores)
print(f"综合评分: {avg_overall:.1f}/5.0")
```

> 💡 **LLM-as-Judge 的局限性**：评委模型也会犯错，不能完全替代人工。建议用它做初筛（排除明显差的），最终决策仍需人工抽查。

---

## 7. 实战：构建完整的 Prompt 管理平台

把前面所有组件串起来，用 FastAPI 构建一个可以直接用的 Prompt 管理后端。

### 7.1 系统架构设计

```
系统架构：

┌────────────────────────────────────────────────┐
│                 FastAPI 后端                     │
│                                                │
│  /prompts      → CRUD + 版本管理                │
│  /experiments  → A/B 测试管理                    │
│  /evaluate     → 效果评估                       │
│  /render       → 渲染 Prompt（供业务服务调用）    │
│                                                │
├───────────┬───────────┬────────────────────────│
│  SQLite   │  YAML     │  Cache (dict/Redis)    │
│  (元数据)  │  (模板)   │  (热缓存)              │
└───────────┴───────────┴────────────────────────┘
```

```bash
# 项目结构
prompt-manager/
├── app/
│   ├── main.py           # FastAPI 入口
│   ├── models.py          # Pydantic 数据模型
│   ├── store.py           # 数据存储层
│   ├── router_prompts.py  # Prompt CRUD 路由
│   ├── router_ab.py       # A/B 测试路由
│   └── router_eval.py     # 评估路由
├── prompts/               # Prompt 模板文件
├── requirements.txt
└── prompt_config.yaml
```

### 7.2 Prompt CRUD API

```python
# app/models.py
from pydantic import BaseModel, Field
from datetime import datetime

class PromptCreate(BaseModel):
    name: str = Field(..., description="Prompt 名称", examples=["sentiment"])
    version: str = Field(..., description="版本号", examples=["1.2.0"])
    template: str = Field(..., description="Prompt 模板内容")
    model: str = Field(default="deepseek-chat", description="推荐模型")
    temperature: float = Field(default=0.7)
    author: str = Field(default="system")

class PromptResponse(BaseModel):
    id: int
    name: str
    version: str
    template: str
    is_active: bool
    created_at: datetime
```

```python
# app/router_prompts.py
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/prompts", tags=["Prompt 管理"])

@router.post("/", response_model=PromptResponse)
async def create_prompt(data: PromptCreate):
    """创建新版本的 Prompt"""
    prompt_id = store.save(
        name=data.name, version=data.version,
        template=data.template, author=data.author,
    )
    return store.get_by_id(prompt_id)

@router.get("/{name}/versions")
async def list_versions(name: str):
    """列出某个 Prompt 的所有版本"""
    return store.list_versions(name)

@router.get("/{name}/active")
async def get_active(name: str):
    """获取当前激活版本"""
    prompt = store.get_active(name)
    if not prompt:
        raise HTTPException(404, f"No active prompt for '{name}'")
    return prompt

@router.post("/{name}/activate/{version}")
async def activate_version(name: str, version: str):
    """激活指定版本"""
    store.activate(name, version)
    return {"message": f"{name} v{version} 已激活"}

@router.post("/render")
async def render_prompt(name: str, variables: dict):
    """渲染 Prompt 模板（供业务服务调用）"""
    prompt = store.get_active(name)
    template = Template(prompt["template"])
    return {"rendered": template.render(**variables)}
```

### 7.3 版本对比与回滚

```python
@router.get("/{name}/diff")
async def diff_versions(name: str, v1: str, v2: str):
    """对比两个版本的 Prompt 差异"""
    import difflib
    
    p1 = store.get(name, v1)
    p2 = store.get(name, v2)
    
    diff = list(difflib.unified_diff(
        p1["template"].splitlines(keepends=True),
        p2["template"].splitlines(keepends=True),
        fromfile=f"{name} v{v1}",
        tofile=f"{name} v{v2}",
    ))
    
    return {
        "from_version": v1,
        "to_version": v2,
        "diff": "".join(diff),
        "has_changes": len(diff) > 0,
    }

@router.post("/{name}/rollback/{version}")
async def rollback(name: str, version: str):
    """回滚到指定版本"""
    store.activate(name, version)
    return {"message": f"已回滚到 {name} v{version}"}
```

### 7.4 A/B 测试控制台

```python
# app/router_ab.py
from fastapi import APIRouter

router = APIRouter(prefix="/experiments", tags=["A/B 测试"])

@router.post("/")
async def create_experiment(name: str, prompt_a_version: str,
                            prompt_b_version: str, traffic_ratio: float = 0.5):
    """创建 A/B 测试实验"""
    ab_manager.create_experiment(
        name=name,
        prompt_a=store.get("sentiment", prompt_a_version),
        prompt_b=store.get("sentiment", prompt_b_version),
        traffic_ratio=traffic_ratio,
    )
    return {"message": f"实验 '{name}' 已创建"}

@router.get("/{name}/assign")
async def assign_group(name: str, user_id: str):
    """为用户分配实验组"""
    group, prompt = ab_manager.get_prompt(name, user_id)
    return {"group": group, "version": prompt["version"]}

@router.get("/{name}/report")
async def get_report(name: str):
    """获取实验报告"""
    exp = ab_manager.experiments[name]
    return {
        "name": name,
        "a_samples": len(exp.results["a"]),
        "b_samples": len(exp.results["b"]),
        "a_avg_score": mean(exp.results["a"]) if exp.results["a"] else 0,
        "b_avg_score": mean(exp.results["b"]) if exp.results["b"] else 0,
    }
```

### 7.5 与 LangChain 集成

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import httpx

class ManagedPrompt:
    """从 Prompt 管理平台加载模板，与 LangChain 集成"""
    
    def __init__(self, manager_url: str = "http://localhost:8000"):
        self.base_url = manager_url
    
    def get_chain(self, prompt_name: str, **llm_kwargs):
        """获取一个 LangChain Chain"""
        # 从管理平台获取当前激活的 Prompt
        resp = httpx.get(f"{self.base_url}/prompts/{prompt_name}/active")
        prompt_data = resp.json()
        
        # 构建 LangChain 组件
        prompt = ChatPromptTemplate.from_template(prompt_data["template"])
        llm = ChatOpenAI(
            model=prompt_data.get("model", "deepseek-chat"),
            temperature=prompt_data.get("temperature", 0.7),
            **llm_kwargs,
        )
        
        return prompt | llm

# ── 使用 ──
managed = ManagedPrompt()
chain = managed.get_chain("sentiment")
result = chain.invoke({"user_input": "这个产品不错"})

# Prompt 在管理平台上更新后 → 下次调用自动使用新版
```

> 💡 **核心价值**：业务代码不再硬编码 Prompt——它只知道 Prompt 的名字，具体内容由管理平台动态提供。

---

## 8. 最佳实践与团队协作

最后一章汇总团队协作中的实用规范和工具推荐。

### 8.1 Prompt 编写规范（团队 Style Guide）

```markdown
# Prompt 编写规范 v1.0

## 结构规范
- 每个 Prompt 必须包含：角色定义、任务描述、输出格式
- 使用 Jinja2 模板语法，不允许 f-string
- 变量用 {{ variable_name }} 格式，不要用 {variable_name}

## 命名规范
- Prompt 名称用小写 + 下划线：sentiment_analysis, text_summarize
- 版本号遵循 SemVer：MAJOR.MINOR.PATCH

## 内容规范
- 角色描述要具体："你是一个有 5 年经验的情感分析师" > "你是 AI"
- 输出格式要给出完整示例，不要只说"返回 JSON"
- Few-shot 示例至少 2 个，覆盖正/反两种情况
- 禁止在 Prompt 中包含敏感信息（API Key、内部系统地址）

## 必填元数据
- name, version, author, created_at, description
- metadata.model：推荐使用的模型
- metadata.temperature：推荐的温度参数
```

### 8.2 Prompt 的 Code Review 流程

```
Prompt Review Checklist：

提交者自查：
  □ 模板语法正确（Jinja2 无报错）
  □ 变量 Schema 已定义（Pydantic）
  □ Golden Set 评测通过（准确率 ≥ 阈值）
  □ 版本号和 CHANGELOG 已更新
  □ 无敏感信息泄露

Reviewer 检查：
  □ Prompt 逻辑清晰，无歧义
  □ 输出格式定义明确
  □ 与现有 Prompt 风格一致
  □ 边界情况已覆盖
  □ 成本评估（token 用量是否合理）
```

```bash
# Git 工作流
git checkout -b prompt/sentiment-v1.2.0
# 修改 Prompt + 跑评测
python -m pytest tests/test_prompts/
git add prompts/ tests/
git commit -m "feat(prompt): sentiment v1.2.0 - 增加 reason 字段"
# 提交 PR → Code Review → 合并 → 自动部署
```

### 8.3 生产环境监控与告警

```python
import time
import logging
from functools import wraps

logger = logging.getLogger("prompt_monitor")

def monitor_prompt(prompt_name: str):
    """Prompt 调用监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                latency = time.time() - start
                
                # 记录指标
                logger.info(f"prompt={prompt_name} status=success latency={latency:.2f}s")
                
                # 告警：延迟过高
                if latency > 10:
                    alert(f"⚠️ {prompt_name} 延迟 {latency:.1f}s，超过 10s 阈值")
                
                return result
            except Exception as e:
                latency = time.time() - start
                logger.error(f"prompt={prompt_name} status=error error={e} latency={latency:.2f}s")
                
                # 告警：错误率过高
                alert(f"🚨 {prompt_name} 调用失败: {e}")
                raise
        return wrapper
    return decorator

# 使用
@monitor_prompt("sentiment_analysis")
async def analyze(text: str):
    return await chain.ainvoke({"user_input": text})
```

**需要监控的关键指标：**

| 指标 | 告警阈值 | 说明 |
|:---|:---|:---|
| 错误率 | > 5% | Prompt 格式错误或模型拒绝 |
| P99 延迟 | > 10s | 模型响应太慢 |
| Token 用量 | 超预算 20% | 成本失控 |
| 格式合规率 | < 95% | 模型输出格式不对 |

### 8.4 开源方案对比：LangFuse / PromptLayer / Humanloop

如果不想从零搭建，可以用现成的开源/商业方案：

| 工具 | 类型 | 核心功能 | 推荐场景 |
|:---|:---|:---|:---|
| **LangFuse** | 开源 | 追踪、评估、Prompt 管理 | 首选！可自部署 |
| **PromptLayer** | 商业 | Prompt 版本控制、日志 | 小团队快速上手 |
| **Humanloop** | 商业 | Prompt 优化、评估、协作 | 需要高级评估功能 |
| **LangSmith** | 商业 | 全链路追踪、评测 | LangChain 深度用户 |
| **本教程方案** | 自建 | 完全可控、无依赖 | 定制需求多的团队 |

> 💡 **最后的建议**：不管用哪个方案，核心原则不变——**Prompt 是 AI 应用最重要的资产，必须像管理代码一样管理它**。版本控制、效果评估、A/B 测试，这三件事做好了，你的 AI 应用质量就有了保障。
