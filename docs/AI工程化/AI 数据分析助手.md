# AI 数据分析助手

> 从零构建一个对话式数据分析助手——涵盖自然语言转 SQL、数据库 Schema 感知、安全查询执行、LLM 驱动的图表自动生成、数据洞察总结、多轮分析对话、Pandas/DataFrame 集成，一套完整方案让非技术用户也能用自然语言玩转数据。

---

## 1. 产品定义与架构设计

### 1.1 AI 数据分析助手能做什么：从问题到洞察

```
AI 数据分析助手的核心价值——让不会写 SQL 的人也能分析数据：

  用户："上个月各渠道的销售额是多少？"
    │
    ▼
  ┌──────────────┐
  │ 自然语言理解   │  识别意图：查询销售额 + 按渠道分组 + 时间范围
  └──────┬───────┘
         │
  ┌──────────────┐
  │ 生成 SQL      │  SELECT channel, SUM(amount) FROM orders 
  │              │  WHERE date >= '2025-03-01' GROUP BY channel
  └──────┬───────┘
         │
  ┌──────────────┐
  │ 执行 + 返回   │  直连数据库执行，返回结果集
  └──────┬───────┘
         │
  ┌──────────────┐
  │ 自动图表      │  检测到分类数据 → 生成柱状图
  └──────┬───────┘
         │
  ┌──────────────┐
  │ 数据洞察      │  "天猫渠道环比增长 23%，抖音渠道下降 15%"
  └──────────────┘
```

### 1.2 用户场景：运营 / 产品 / 管理层的分析需求

| 角色 | 典型问题 | 分析复杂度 |
|:---|:---|:---|
| **运营** | "昨天各渠道的 GMV 是多少？" | ⭐ 单表聚合 |
| **运营** | "复购率最高的 Top 10 商品是什么？" | ⭐⭐ 多表 JOIN |
| **产品** | "新用户 7 日留存率趋势如何？" | ⭐⭐⭐ 窗口函数 |
| **管理层** | "各部门人效环比变化？" | ⭐⭐ 聚合+对比 |
| **财务** | "本季度毛利率与预算差异？" | ⭐⭐ 计算字段 |

### 1.3 整体架构：自然语言 → SQL → 执行 → 可视化 → 洞察

```
系统架构：

  用户（浏览器 / 飞书 / 钉钉）
    │
    ▼
  ┌──────────────────────────────────────┐
  │            API 网关层                  │
  │  认证 │ 限流 │ 日志 │ 权限            │
  └──────────────┬───────────────────────┘
                 │
  ┌──────────────┴───────────────────────┐
  │            AI 分析引擎                 │
  │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
  │  │意图识别  │ │Text2SQL │ │图表生成 │ │
  │  └─────────┘ └─────────┘ └────────┘ │
  │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
  │  │洞察分析  │ │对话管理  │ │报告生成 │ │
  │  └─────────┘ └─────────┘ └────────┘ │
  └──────┬────────────┬──────────────────┘
         │            │
  ┌──────┴──────┐  ┌──┴──────────────────┐
  │  LLM 层     │  │   数据层             │
  │  DeepSeek   │  │  PostgreSQL / MySQL  │
  │  Qwen       │  │  ClickHouse / CSV    │
  └─────────────┘  └─────────────────────┘
```

### 1.4 技术选型与安全边界

| 组件 | 选型 | 理由 |
|:---|:---|:---|
| **主力模型** | DeepSeek-V3 | SQL 生成准确率高、便宜 |
| **备用模型** | Qwen-Max | 长上下文（128K）处理大 Schema |
| **后端** | FastAPI | 异步 + 流式 |
| **数据库连接** | SQLAlchemy | 多数据库统一接口 |
| **图表** | Matplotlib + ECharts | 后端生图 + 前端交互 |
| **沙箱** | Docker / RestrictedPython | Pandas 代码安全执行 |

> 💡 **安全是第一原则**——数据分析助手直连生产数据库，必须做到：只读连接、SQL 白名单、超时限制、行数限制。一条 `DELETE` 就可能造成灾难。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **核心链路** | 自然语言 → SQL → 执行 → 图表 → 洞察 |
| **用户画像** | 运营/产品/管理层，不会写 SQL 的人 |
| **架构** | API 网关 + AI 引擎 + LLM + 数据层 |
| **安全红线** | 只读、超时、行数限制、SQL 白名单 |

---

## 2. 自然语言转 SQL：让 LLM 读懂你的数据库

### 2.1 Text-to-SQL 的 Prompt 工程

```python
TEXT2SQL_PROMPT = """你是一个 SQL 专家。根据用户问题和数据库 Schema 生成 SQL 查询。

## 数据库类型
{db_type}

## 数据库 Schema
{schema}

## 业务术语表
{glossary}

## 规则
1. 只生成 SELECT 语句，禁止 INSERT/UPDATE/DELETE/DROP
2. 必须使用表的实际字段名，不能编造字段
3. 时间字段的格式：{date_format}
4. 使用中文别名让结果易读（AS "销售额"）
5. 大表查询必须加 LIMIT（默认 1000）
6. 如果问题不明确，返回 JSON：{{"unclear": true, "clarification": "需要澄清的问题"}}

## 用户问题
{question}

只输出 SQL，不要解释："""

class Text2SQL:
    """自然语言转 SQL"""
    
    async def generate(self, question: str, schema: str, **kwargs) -> dict:
        prompt = TEXT2SQL_PROMPT.format(
            question=question,
            schema=schema,
            db_type=kwargs.get("db_type", "PostgreSQL"),
            glossary=kwargs.get("glossary", "无"),
            date_format=kwargs.get("date_format", "YYYY-MM-DD"),
        )
        
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0)  # 零温度确保确定性
        
        sql = result.choices[0].message.content.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        return {"sql": sql, "tokens": result.usage.total_tokens}
```

### 2.2 数据库 Schema 自动发现与注入

```python
from sqlalchemy import inspect

class SchemaDiscovery:
    """自动发现数据库 Schema"""
    
    def __init__(self, engine):
        self.inspector = inspect(engine)
    
    def get_schema_prompt(self, tables: list[str] = None) -> str:
        """生成 Schema 描述文本"""
        if not tables:
            tables = self.inspector.get_table_names()
        
        schema_parts = []
        for table in tables:
            columns = self.inspector.get_columns(table)
            pk = self.inspector.get_pk_constraint(table)
            fks = self.inspector.get_foreign_keys(table)
            
            col_defs = []
            for col in columns:
                col_str = f"  {col['name']} {col['type']}"
                if col['name'] in (pk.get('constrained_columns') or []):
                    col_str += " PRIMARY KEY"
                col_defs.append(col_str)
            
            # 外键关系
            fk_defs = []
            for fk in fks:
                fk_defs.append(
                    f"  FOREIGN KEY ({','.join(fk['constrained_columns'])}) "
                    f"REFERENCES {fk['referred_table']}({','.join(fk['referred_columns'])})"
                )
            
            schema_parts.append(
                f"CREATE TABLE {table} (\n" + 
                ",\n".join(col_defs + fk_defs) + "\n);"
            )
        
        return "\n\n".join(schema_parts)
    
    def get_sample_data(self, table: str, limit: int = 3) -> str:
        """获取示例数据帮助 LLM 理解字段含义"""
        rows = self.engine.execute(f"SELECT * FROM {table} LIMIT {limit}")
        return str([dict(r) for r in rows])
```

### 2.3 复杂查询处理：多表 JOIN / 子查询 / 聚合

```python
# ── 业务术语表：让 LLM 理解"黑话" ──
GLOSSARY = """
- GMV = 总交易额 = SUM(order_amount)
- 复购率 = 购买 2 次以上的用户数 / 总用户数
- DAU = 日活跃用户 = COUNT(DISTINCT user_id) WHERE date = today
- 留存率 = 第 N 天仍活跃的用户 / 第 0 天的新用户
- ROI = 收入 / 投放成本
- 客单价 = GMV / 订单数
"""

# ── 复杂查询的 Few-shot 示例 ──
FEW_SHOT_EXAMPLES = [
    {
        "question": "上月各渠道的复购率",
        "sql": """SELECT channel, 
  COUNT(CASE WHEN order_count >= 2 THEN 1 END)::float / COUNT(*) AS "复购率"
FROM (
  SELECT user_id, channel, COUNT(*) as order_count
  FROM orders WHERE date >= '2025-03-01' AND date < '2025-04-01'
  GROUP BY user_id, channel
) t
GROUP BY channel""",
    },
    {
        "question": "新用户 7 日留存率",
        "sql": """SELECT register_date, 
  COUNT(DISTINCT CASE WHEN active_date = register_date + 7 THEN user_id END)::float
  / COUNT(DISTINCT user_id) AS "7日留存率"
FROM user_activity
GROUP BY register_date
ORDER BY register_date DESC LIMIT 30""",
    },
]
```

### 2.4 SQL 安全校验：防注入与只读限制

```python
import sqlparse

class SQLValidator:
    """SQL 安全校验"""
    
    BLOCKED_KEYWORDS = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
        "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE",
    }
    
    def validate(self, sql: str) -> dict:
        """校验 SQL 是否安全"""
        parsed = sqlparse.parse(sql)
        
        for stmt in parsed:
            # 检查语句类型
            stmt_type = stmt.get_type()
            if stmt_type and stmt_type.upper() != "SELECT":
                return {"safe": False, "reason": f"禁止 {stmt_type} 操作"}
            
            # 检查危险关键词
            tokens = [t.ttype and t.value.upper() for t in stmt.flatten()]
            for kw in self.BLOCKED_KEYWORDS:
                if kw in str(sql).upper():
                    return {"safe": False, "reason": f"包含危险关键词: {kw}"}
        
        # 检查是否有 LIMIT
        if "LIMIT" not in sql.upper():
            sql += " LIMIT 1000"
        
        return {"safe": True, "sql": sql}
```

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Prompt 工程** | Schema + 术语表 + 规则 + Few-shot = 高质量 SQL |
| **Schema 注入** | 自动发现表结构 + 外键 + 示例数据 |
| **术语表** | GMV/复购率/留存率等业务概念的 SQL 翻译 |
| **安全校验** | sqlparse 解析 + 关键词黑名单 + 强制 LIMIT |

---

## 3. 查询执行与结果处理

### 3.1 安全执行引擎：只读连接 + 超时 + 行数限制

```python
from sqlalchemy import create_engine, text
import asyncio

class SafeQueryExecutor:
    """安全查询执行器"""
    
    def __init__(self, connection_url: str):
        # 关键：使用只读账号连接
        self.engine = create_engine(
            connection_url,
            pool_size=5,
            max_overflow=0,
            execution_options={"isolation_level": "AUTOCOMMIT"},
        )
        self.validator = SQLValidator()
        self.max_rows = 5000
        self.timeout = 30  # 秒
    
    async def execute(self, sql: str) -> dict:
        """安全执行 SQL"""
        # Step 1: 安全校验
        check = self.validator.validate(sql)
        if not check["safe"]:
            return {"success": False, "error": check["reason"]}
        
        sql = check["sql"]  # 可能已加 LIMIT
        
        # Step 2: 超时执行
        try:
            result = await asyncio.wait_for(
                self._run(sql), timeout=self.timeout
            )
        except asyncio.TimeoutError:
            return {"success": False, "error": f"查询超时（{self.timeout}秒）"}
        except Exception as e:
            return {"success": False, "error": str(e), "sql": sql}
        
        return {"success": True, **result}
    
    async def _run(self, sql: str) -> dict:
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql))
            columns = list(rows.keys())
            data = [dict(zip(columns, row)) for row in rows.fetchmany(self.max_rows)]
            
            return {
                "columns": columns,
                "data": data,
                "row_count": len(data),
                "truncated": len(data) >= self.max_rows,
            }
```

### 3.2 结果集处理：大表分页 / 采样 / 摘要

```python
class ResultProcessor:
    """查询结果处理"""
    
    def process(self, result: dict) -> dict:
        """处理查询结果，为可视化和洞察做准备"""
        data = result["data"]
        columns = result["columns"]
        
        # 分析列类型
        col_types = {}
        for col in columns:
            sample = [r[col] for r in data[:10] if r[col] is not None]
            col_types[col] = self._infer_type(sample)
        
        # 生成统计摘要
        summary = self._generate_summary(data, col_types)
        
        return {
            **result,
            "col_types": col_types,    # {"date": "datetime", "amount": "numeric", ...}
            "summary": summary,
            "preview": data[:20],      # 前 20 行预览
        }
    
    def _infer_type(self, sample: list) -> str:
        """推断列类型"""
        if not sample:
            return "unknown"
        first = sample[0]
        if isinstance(first, (int, float)):
            return "numeric"
        if isinstance(first, str) and self._is_date(first):
            return "datetime"
        return "categorical"
    
    def _generate_summary(self, data: list, col_types: dict) -> dict:
        """生成统计摘要"""
        summary = {}
        for col, dtype in col_types.items():
            values = [r[col] for r in data if r[col] is not None]
            if dtype == "numeric" and values:
                summary[col] = {
                    "min": min(values), "max": max(values),
                    "avg": sum(values) / len(values),
                    "count": len(values),
                }
            elif dtype == "categorical":
                from collections import Counter
                summary[col] = {"unique": len(set(values)), "top3": Counter(values).most_common(3)}
        return summary
```

### 3.3 数据类型适配：日期 / 数值 / 枚举的智能处理

```python
class TypeAdapter:
    """数据类型智能适配"""
    
    def adapt_for_chart(self, data: list, col_types: dict) -> list:
        """将查询结果适配为图表友好格式"""
        adapted = []
        for row in data:
            new_row = {}
            for col, val in row.items():
                dtype = col_types.get(col, "unknown")
                if dtype == "datetime" and isinstance(val, str):
                    new_row[col] = val[:10]  # 只保留日期部分
                elif dtype == "numeric" and val is not None:
                    new_row[col] = round(float(val), 2)  # 保留两位小数
                else:
                    new_row[col] = val
            adapted.append(new_row)
        return adapted
```

### 3.4 错误处理与自动修复：SQL 执行失败怎么办

```python
class SQLAutoFixer:
    """SQL 执行失败时自动修复"""
    
    MAX_RETRIES = 2
    
    async def execute_with_retry(self, question: str, schema: str,
                                   executor: SafeQueryExecutor) -> dict:
        """执行 SQL，失败时自动修复重试"""
        sql_gen = Text2SQL()
        
        # 第一次生成
        sql_result = await sql_gen.generate(question, schema)
        sql = sql_result["sql"]
        
        for attempt in range(self.MAX_RETRIES + 1):
            result = await executor.execute(sql)
            
            if result["success"]:
                return {**result, "sql": sql, "attempts": attempt + 1}
            
            if attempt < self.MAX_RETRIES:
                # 将错误信息反馈给 LLM 修复
                sql = await self._fix_sql(question, sql, result["error"], schema)
        
        return {"success": False, "error": "多次修复失败", "last_sql": sql}
    
    async def _fix_sql(self, question: str, failed_sql: str,
                        error: str, schema: str) -> str:
        """让 LLM 修复失败的 SQL"""
        prompt = f"""以下 SQL 执行报错，请修复：

原始问题：{question}
失败的 SQL：{failed_sql}
错误信息：{error}
数据库 Schema：{schema}

修复后的 SQL："""
        
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0)
        
        return result.choices[0].message.content.strip()
```

> 💡 **自动修复是用户体验的关键**——LLM 生成的 SQL 不可能 100% 正确，但把错误信息反馈给 LLM 再修一次，成功率从 70% 提升到 90%+。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **安全执行** | 只读连接 + 超时 30s + 最多 5000 行 |
| **结果处理** | 自动推断类型 + 统计摘要 + 前 20 行预览 |
| **类型适配** | 日期截断、数值保留两位、枚举统计 |
| **自动修复** | 错误反馈给 LLM 重试，最多 2 次 |

---

## 4. 智能图表生成：让数据说话

### 4.1 图表类型自动推荐：柱状 / 折线 / 饼图 / 散点

```python
class ChartRecommender:
    """根据数据特征自动推荐图表类型"""
    
    RULES = {
        # (x_type, y_type, 数据行数) → 图表类型
        ("categorical", "numeric", "few"):    "bar",       # 类别 vs 数值，少量 → 柱状
        ("categorical", "numeric", "many"):   "bar_h",     # 类别 vs 数值，大量 → 横向柱状
        ("datetime", "numeric", "any"):       "line",      # 时间 vs 数值 → 折线
        ("categorical", "numeric", "pie"):    "pie",       # 类别 vs 比例 → 饼图
        ("numeric", "numeric", "any"):        "scatter",   # 数值 vs 数值 → 散点
    }
    
    def recommend(self, col_types: dict, data: list) -> dict:
        """推荐图表类型"""
        cols = list(col_types.items())
        if len(cols) < 2:
            return {"chart": "table", "reason": "只有一列数据，展示为表格"}
        
        x_col, x_type = cols[0]
        y_col, y_type = cols[1]
        row_count = len(data)
        
        # 特殊判断：如果只有少量类别且 y 是占比 → 饼图
        if x_type == "categorical" and row_count <= 8:
            y_values = [r[y_col] for r in data if r[y_col]]
            if all(0 <= v <= 1 for v in y_values) or sum(y_values) > 0:
                return {"chart": "pie", "x": x_col, "y": y_col}
        
        size = "few" if row_count <= 15 else "many"
        chart = self.RULES.get((x_type, y_type, size), 
                self.RULES.get((x_type, y_type, "any"), "table"))
        
        return {"chart": chart, "x": x_col, "y": y_col}
```

### 4.2 LLM 驱动的 Matplotlib/ECharts 代码生成

```python
CHART_PROMPT = """根据以下数据生成 Python Matplotlib 图表代码。

## 数据
{data_preview}

## 图表类型
{chart_type}

## 要求
1. 使用中文标签
2. 配色方案：{color_scheme}
3. 添加数值标注
4. 图表尺寸 (10, 6)
5. 保存为 PNG：plt.savefig('{output_path}', dpi=150, bbox_inches='tight')

只输出可直接执行的 Python 代码："""

class ChartGenerator:
    """图表生成器"""
    
    async def generate(self, data: list, chart_config: dict,
                        output_path: str) -> str:
        """生成图表代码并执行"""
        # 数据预览（给 LLM 看前 10 行）
        preview = json.dumps(data[:10], ensure_ascii=False, indent=2)
        
        prompt = CHART_PROMPT.format(
            data_preview=preview,
            chart_type=chart_config["chart"],
            color_scheme="商务蓝灰",
            output_path=output_path,
        )
        
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0)
        
        code = result.choices[0].message.content
        code = code.replace("```python", "").replace("```", "").strip()
        
        # 安全执行
        exec(code, {"__builtins__": {}}, {
            "plt": __import__("matplotlib.pyplot"),
            "json": json, "data": data,
        })
        
        return output_path
```

### 4.3 图表美化：配色 / 标注 / 响应式

```python
# ── 预设配色方案 ──
COLOR_SCHEMES = {
    "商务蓝灰": ["#3B82F6", "#6B7280", "#10B981", "#F59E0B", "#EF4444"],
    "科技紫蓝": ["#8B5CF6", "#3B82F6", "#06B6D4", "#6366F1", "#A855F7"],
    "清新绿色": ["#10B981", "#34D399", "#6EE7B7", "#059669", "#047857"],
    "数据橙红": ["#F97316", "#EF4444", "#F59E0B", "#DC2626", "#EA580C"],
}

# ── 图表模板（减少 LLM 输出量）──
CHART_TEMPLATES = {
    "bar": """
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x_data, y_data, color=colors)
for i, v in enumerate(y_data):
    ax.text(i, v + max(y_data)*0.02, f'{{v:,.0f}}', ha='center')
ax.set_title(title)
ax.set_xlabel(x_label)
ax.set_ylabel(y_label)
plt.tight_layout()
plt.savefig(output_path, dpi=150)""",
}
```

### 4.4 前端集成：从后端图片到前端交互式图表

```python
# ── 返回 ECharts 配置（前端渲染交互式图表）──
class EChartsGenerator:
    """生成 ECharts 配置 JSON"""
    
    async def generate_option(self, data: list, chart_config: dict) -> dict:
        """生成 ECharts option"""
        x_col, y_col = chart_config["x"], chart_config["y"]
        chart_type = chart_config["chart"]
        
        x_data = [str(r[x_col]) for r in data]
        y_data = [r[y_col] for r in data]
        
        if chart_type == "bar":
            return {
                "title": {"text": f"{y_col} by {x_col}"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": x_data},
                "yAxis": {"type": "value"},
                "series": [{"type": "bar", "data": y_data,
                            "itemStyle": {"color": "#3B82F6"}}],
            }
        elif chart_type == "line":
            return {
                "title": {"text": f"{y_col} 趋势"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": x_data},
                "yAxis": {"type": "value"},
                "series": [{"type": "line", "data": y_data, "smooth": True}],
            }
        elif chart_type == "pie":
            return {
                "title": {"text": f"{y_col} 分布"},
                "tooltip": {"trigger": "item"},
                "series": [{"type": "pie", "radius": "60%",
                    "data": [{"name": x, "value": y} for x, y in zip(x_data, y_data)]}],
            }

# API 端点返回两种格式
@app.post("/api/chart")
async def create_chart(req: ChartRequest):
    return {
        "image_url": "/static/charts/xxx.png",       # 后端 Matplotlib 图片
        "echarts_option": echarts_gen.generate(data),  # 前端 ECharts 配置
    }
```

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **自动推荐** | 根据 x/y 列类型 + 行数自动选柱/线/饼/散点 |
| **代码生成** | LLM 生成 Matplotlib 代码 + 安全执行 |
| **双轨输出** | 后端 PNG 图片 + 前端 ECharts 交互配置 |
| **美化** | 预设配色方案 + 数值标注 + 中文字体 |

---

## 5. 数据洞察与自动总结

### 5.1 数据洞察生成：趋势 / 异常 / 对比 / 排名

```python
class InsightEngine:
    """数据洞察引擎"""
    
    INSIGHT_TYPES = {
        "trend":    "趋势分析：数据随时间的变化方向",
        "anomaly":  "异常检测：明显偏离正常范围的值",
        "compare":  "对比分析：不同维度之间的差异",
        "ranking":  "排名分析：Top/Bottom N 的表现",
        "composition": "构成分析：各部分占总体的比例",
    }
    
    def detect_insight_type(self, col_types: dict, data: list) -> list[str]:
        """根据数据特征判断适合哪种洞察"""
        types = []
        has_datetime = any(v == "datetime" for v in col_types.values())
        has_categorical = any(v == "categorical" for v in col_types.values())
        has_numeric = any(v == "numeric" for v in col_types.values())
        
        if has_datetime and has_numeric:
            types.append("trend")
        if has_categorical and has_numeric:
            types.extend(["compare", "ranking", "composition"])
        if has_numeric:
            types.append("anomaly")
        
        return types
```

### 5.2 洞察的 Prompt 设计：让 LLM 像分析师一样思考

```python
INSIGHT_PROMPT = """你是一名资深数据分析师。根据以下查询结果，给出 3-5 条关键洞察。

## 用户问题
{question}

## 查询 SQL
{sql}

## 查询结果（前 20 行）
{data_preview}

## 统计摘要
{summary}

## 要求
1. 每条洞察用一句话总结，附上具体数字
2. 指出趋势方向（上升/下降/平稳）
3. 标注异常值和原因猜测
4. 给出 1-2 条可执行的建议
5. 不要编造数据中没有的信息

## 输出格式
📊 **洞察 1**：...
📊 **洞察 2**：...
💡 **建议**：..."""

class InsightGenerator:
    async def generate(self, question: str, sql: str, result: dict) -> str:
        prompt = INSIGHT_PROMPT.format(
            question=question,
            sql=sql,
            data_preview=json.dumps(result["preview"], ensure_ascii=False),
            summary=json.dumps(result["summary"], ensure_ascii=False),
        )
        
        resp = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0.3)
        
        return resp.choices[0].message.content
```

### 5.3 自动报告生成：从数据到 Markdown 报告

```python
class ReportGenerator:
    """自动生成分析报告"""
    
    REPORT_TEMPLATE = """# {title}

> 生成时间：{timestamp} | 数据范围：{date_range}

## 📋 分析概要
{summary}

## 📊 核心指标
{metrics_table}

## 📈 图表
{charts}

## 💡 关键洞察
{insights}

## 🎯 建议
{recommendations}

---
*本报告由 AI 数据分析助手自动生成，数据基于 {data_source}*
"""
    
    async def generate(self, queries: list[dict]) -> str:
        """根据多个查询结果生成完整报告"""
        sections = []
        for q in queries:
            insight = await self.insight_gen.generate(
                q["question"], q["sql"], q["result"]
            )
            sections.append({"question": q["question"], "insight": insight})
        
        # 组装报告
        return self.REPORT_TEMPLATE.format(
            title=queries[0]["question"],
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            # ... 填充各部分
        )
```

### 5.4 洞察的可信度：避免 LLM 编造数据

```python
class InsightValidator:
    """洞察验证：防止 LLM 编造数字"""
    
    def validate(self, insight: str, actual_data: dict) -> dict:
        """检查洞察中的数字是否与实际数据一致"""
        import re
        
        # 提取洞察中的数字
        numbers_in_insight = re.findall(r'[\d,]+\.?\d*%?', insight)
        
        # 提取实际数据中的数字
        actual_numbers = set()
        for row in actual_data.get("data", []):
            for v in row.values():
                if isinstance(v, (int, float)):
                    actual_numbers.add(str(round(v, 2)))
        
        # 检查每个数字是否能在数据中找到来源
        unverified = []
        for num in numbers_in_insight:
            clean = num.replace(",", "").replace("%", "")
            if clean not in actual_numbers:
                unverified.append(num)
        
        return {
            "verified": len(unverified) == 0,
            "unverified_numbers": unverified,
            "warning": "以下数字未在查询结果中找到来源" if unverified else None,
        }
```

> 💡 **"不要编造"是最重要的 Prompt 规则**——LLM 天生喜欢"补全"，在数据分析场景下可能编造不存在的数字。必须在 Prompt 中明确"只使用查询结果中的数据"，并在后处理中验证。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **洞察类型** | 趋势/异常/对比/排名/构成 5 种模式 |
| **Prompt 设计** | 数据+统计摘要+格式要求 = 高质量洞察 |
| **自动报告** | Markdown 模板 + 多查询聚合 |
| **可信度** | 验证洞察中的数字是否来自实际数据 |

---

## 6. 多轮对话与上下文管理

### 6.1 多轮对话设计：追问 / 钻取 / 条件修改

```
多轮对话典型场景：

  第 1 轮：  "上月各渠道 GMV"
  → SQL: SELECT channel, SUM(amount) FROM orders WHERE ... GROUP BY channel
  → 结果：天猫 120万, 抖音 80万, 京东 60万

  第 2 轮（追问）：  "抖音的数据拆解到每周看看"
  → AI 识别：基于上一轮的"抖音"做时间粒度钻取
  → SQL: SELECT date_trunc('week', date), SUM(amount) FROM orders 
         WHERE channel = '抖音' AND ... GROUP BY 1

  第 3 轮（条件修改）：  "加上去年同期对比"
  → AI 识别：保持抖音+每周维度，增加去年同期
  → SQL: 当前月 UNION ALL 去年同期

  第 4 轮（切换）：  "看看退款率最高的商品"
  → AI 识别：全新查询，不依赖上文
```

### 6.2 对话上下文管理：SQL 历史 + 结果缓存

```python
class ConversationContext:
    """对话上下文管理"""
    
    def __init__(self):
        self.history = []  # 对话历史
        self.sql_history = []  # SQL 历史
        self.result_cache = {}  # 结果缓存
    
    def add_turn(self, question: str, sql: str, result: dict):
        """记录一轮对话"""
        turn = {
            "question": question,
            "sql": sql,
            "columns": result.get("columns", []),
            "row_count": result.get("row_count", 0),
            "summary": result.get("summary", {}),
        }
        self.history.append(turn)
        self.sql_history.append(sql)
        self.result_cache[sql] = result
    
    def build_context_prompt(self) -> str:
        """构建上下文 Prompt"""
        if not self.history:
            return "无历史对话。"
        
        context = "## 对话历史（最近 3 轮）\n"
        for turn in self.history[-3:]:
            context += f"用户：{turn['question']}\n"
            context += f"SQL：{turn['sql']}\n"
            context += f"结果：{turn['row_count']} 行，列={turn['columns']}\n\n"
        
        return context
```

### 6.3 意图识别：查询 / 可视化 / 洞察 / 导出

```python
class IntentClassifier:
    """意图分类器"""
    
    INTENT_PROMPT = """判断用户问题的意图类型。

意图类型：
- query: 需要查询数据库（生成新 SQL）
- drilldown: 基于上一次查询做钻取/追问
- visualize: 要求生成图表
- insight: 要求分析洞察/总结
- export: 要求导出数据/报告
- clarify: 问题不明确，需要澄清

对话历史：
{context}

用户问题：{question}

回复 JSON：{{"intent": "类型", "references_previous": true/false}}"""

    async def classify(self, question: str, context: str) -> dict:
        prompt = self.INTENT_PROMPT.format(question=question, context=context)
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0)
        return json.loads(result.choices[0].message.content)
```

### 6.4 模糊查询处理：用户说不清楚怎么办

```python
class ClarificationHandler:
    """模糊查询澄清"""
    
    async def handle(self, question: str, schema: str) -> dict:
        """处理模糊问题"""
        prompt = f"""用户问了一个模糊的数据问题，请判断需要澄清什么。

数据库 Schema：{schema}
用户问题：{question}

回复 JSON：
{{
  "needs_clarification": true/false,
  "clarification_questions": [
    "你想看哪个时间范围的数据？",
    "GMV 是指订单金额还是实际支付金额？"
  ],
  "assumptions": [
    "默认查看最近 30 天",
    "默认 GMV = 实际支付金额"
  ],
  "can_proceed_with_defaults": true/false
}}"""
        
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0)
        
        return json.loads(result.choices[0].message.content)
```

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **多轮场景** | 追问/钻取/条件修改/全新查询 |
| **上下文管理** | 最近 3 轮历史 + SQL 缓存 |
| **意图识别** | 查询/钻取/可视化/洞察/导出/澄清 |
| **模糊处理** | 先给默认假设，可带假设执行 |

---

## 7. Pandas 集成与 DataFrame 分析

### 7.1 文件上传与 DataFrame 加载

```python
import pandas as pd

class FileLoader:
    """文件上传 → DataFrame"""
    
    SUPPORTED = {".csv", ".xlsx", ".xls", ".json", ".parquet"}
    MAX_SIZE = 50 * 1024 * 1024  # 50MB
    
    async def load(self, file) -> dict:
        """加载上传的文件为 DataFrame"""
        ext = Path(file.filename).suffix.lower()
        if ext not in self.SUPPORTED:
            raise ValueError(f"不支持的文件格式: {ext}")
        
        content = await file.read()
        if len(content) > self.MAX_SIZE:
            raise ValueError(f"文件过大，最大 50MB")
        
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(content))
        elif ext == ".json":
            df = pd.read_json(io.BytesIO(content))
        elif ext == ".parquet":
            df = pd.read_parquet(io.BytesIO(content))
        
        # 生成 Schema 描述
        schema = self._describe_df(df)
        
        return {"df": df, "schema": schema, "shape": df.shape}
    
    def _describe_df(self, df: pd.DataFrame) -> str:
        """生成 DataFrame Schema 描述"""
        lines = [f"DataFrame: {df.shape[0]} 行 × {df.shape[1]} 列\n"]
        for col in df.columns:
            dtype = str(df[col].dtype)
            sample = str(df[col].dropna().head(3).tolist())
            lines.append(f"  {col} ({dtype}): 示例 {sample}")
        return "\n".join(lines)
```

### 7.2 自然语言转 Pandas 代码

```python
PANDAS_PROMPT = """根据用户问题生成 Pandas 代码来分析 DataFrame。

## DataFrame 信息
{schema}

## 变量名
DataFrame 变量名为 `df`

## 规则
1. 只使用 pandas、numpy 基础操作
2. 结果赋值给变量 `result`
3. 如果需要图表，用 matplotlib 绘制并保存到 `{output_path}`
4. 不要使用 exec、eval、os、subprocess
5. 不要读写文件系统（除了保存图表）

## 用户问题
{question}

只输出 Python 代码："""

class PandasCodeGen:
    async def generate(self, question: str, schema: str) -> str:
        prompt = PANDAS_PROMPT.format(
            question=question, schema=schema,
            output_path="/tmp/chart.png",
        )
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0)
        
        code = result.choices[0].message.content
        return code.replace("```python", "").replace("```", "").strip()
```

### 7.3 安全沙箱执行：限制 Pandas 代码能力

```python
class PandasSandbox:
    """安全执行 Pandas 代码"""
    
    ALLOWED_MODULES = {"pandas", "numpy", "matplotlib", "datetime"}
    BLOCKED_BUILTINS = {"exec", "eval", "compile", "__import__", "open",
                         "input", "breakpoint", "exit", "quit"}
    
    def execute(self, code: str, df: pd.DataFrame) -> dict:
        """在受限环境中执行 Pandas 代码"""
        # 静态检查
        check = self._static_check(code)
        if not check["safe"]:
            return {"success": False, "error": check["reason"]}
        
        # 构建受限的执行环境
        safe_globals = {
            "__builtins__": {k: v for k, v in __builtins__.__dict__.items()
                            if k not in self.BLOCKED_BUILTINS},
            "pd": pd,
            "np": __import__("numpy"),
            "plt": __import__("matplotlib.pyplot"),
            "df": df.copy(),  # 用副本避免修改原数据
        }
        
        local_vars = {}
        
        try:
            exec(code, safe_globals, local_vars)
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        result = local_vars.get("result", None)
        
        if isinstance(result, pd.DataFrame):
            return {"success": True, "data": result.head(100).to_dict("records"),
                    "shape": result.shape}
        elif isinstance(result, pd.Series):
            return {"success": True, "data": result.head(100).to_dict()}
        else:
            return {"success": True, "data": str(result)}
    
    def _static_check(self, code: str) -> dict:
        """静态代码安全检查"""
        import ast
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"safe": False, "reason": f"语法错误: {e}"}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.ALLOWED_MODULES:
                        return {"safe": False, "reason": f"禁止导入: {alias.name}"}
        
        return {"safe": True}
```

### 7.4 SQL vs Pandas：什么时候用什么

| 场景 | 推荐 | 原因 |
|:---|:---|:---|
| 连接数据库查询 | **SQL** | 直接在数据库执行，速度快 |
| CSV/Excel 分析 | **Pandas** | 文件已在内存，不需要入库 |
| 多表 JOIN | **SQL** | 数据库优化器更擅长 |
| 复杂计算 | **Pandas** | 灵活度高，支持自定义函数 |
| 大数据量 (> 100万行) | **SQL** | 避免内存溢出 |
| 数据清洗 | **Pandas** | 缺失值/类型转换更方便 |

> 💡 **优先 SQL，Pandas 做补充**——有数据库就用 SQL（性能好、不传数据），CSV/Excel 上传的用 Pandas。两者通过统一的意图识别自动路由。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **文件加载** | CSV/Excel/JSON/Parquet → DataFrame |
| **代码生成** | NL → Pandas 代码，结果赋给 result |
| **安全沙箱** | 白名单模块 + 禁止危险内建函数 + 静态检查 |
| **路由策略** | 有库用 SQL，文件用 Pandas |

---

## 8. 实战案例：电商数据分析助手

### 8.1 需求定义：电商运营的 5 大核心分析场景

```
电商数据分析 Top 5 场景：

  ① 销售概览 ── "今天/本周/本月的 GMV、订单量、客单价"
  ② 渠道分析 ── "各渠道的销售额、转化率、ROI"
  ③ 商品分析 ── "畅销/滞销商品 Top 10、品类占比"
  ④ 用户分析 ── "新老用户比例、复购率、留存率"
  ⑤ 趋势异常 ── "本周 GMV 下降原因？哪个渠道掉了？"

  对应的 SQL 难度：
    场景①：⭐ 单表聚合
    场景②：⭐⭐ 多表 JOIN + 分组
    场景③：⭐⭐ 排序 + 比例计算
    场景④：⭐⭐⭐ 窗口函数 + 子查询
    场景⑤：⭐⭐⭐ 环比计算 + 下钻
```

### 8.2 数据库设计与 Schema 配置

```sql
-- 电商核心表结构（PostgreSQL）
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  nickname VARCHAR(50),
  phone VARCHAR(20),
  register_date DATE,
  channel VARCHAR(30)  -- 注册渠道
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  order_date TIMESTAMP,
  amount DECIMAL(10,2),     -- 订单金额
  status VARCHAR(20),        -- paid/refunded/cancelled
  channel VARCHAR(30),       -- 成交渠道
  coupon_amount DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE order_items (
  id SERIAL PRIMARY KEY,
  order_id INT REFERENCES orders(id),
  product_id INT REFERENCES products(id),
  quantity INT,
  price DECIMAL(10,2)
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  category VARCHAR(50),
  brand VARCHAR(50),
  cost DECIMAL(10,2)
);
```

### 8.3 核心功能演示：从提问到图表

```python
class EcommerceAnalyst:
    """电商分析助手：完整链路"""
    
    async def analyze(self, question: str, session_id: str) -> dict:
        """一个问题的完整处理流程"""
        ctx = self.sessions[session_id]
        
        # 1. 意图识别
        intent = await self.classifier.classify(question, ctx.build_context_prompt())
        
        # 2. 生成 SQL
        if intent["intent"] in ("query", "drilldown"):
            sql_result = await self.text2sql.generate(
                question, self.schema,
                glossary=GLOSSARY,
                context=ctx.build_context_prompt() if intent["references_previous"] else "",
            )
            sql = sql_result["sql"]
            
            # 3. 安全执行
            result = await self.executor.execute(sql)
            if not result["success"]:
                # 自动修复
                result = await self.fixer.execute_with_retry(question, self.schema, self.executor)
            
            # 4. 结果处理
            processed = self.processor.process(result)
            
            # 5. 图表生成
            chart_config = self.chart_recommender.recommend(processed["col_types"], processed["data"])
            echarts = await self.echarts_gen.generate_option(processed["data"], chart_config)
            
            # 6. 洞察生成
            insight = await self.insight_gen.generate(question, sql, processed)
            
            # 7. 更新上下文
            ctx.add_turn(question, sql, processed)
            
            return {
                "sql": sql,
                "data": processed["preview"],
                "chart": echarts,
                "insight": insight,
                "row_count": processed["row_count"],
            }

# 使用示例
analyst = EcommerceAnalyst(db_url="postgresql://readonly:***@db:5432/ecommerce")

# 第 1 轮
r1 = await analyst.analyze("本月各渠道 GMV", session_id="s1")
# → SQL: SELECT channel, SUM(amount) AS "GMV" FROM orders WHERE ...
# → 柱状图 + 洞察："天猫占比 45%，环比增长 12%"

# 第 2 轮（追问）
r2 = await analyst.analyze("天猫的日趋势怎么样", session_id="s1")
# → SQL: SELECT DATE(order_date), SUM(amount) FROM orders WHERE channel='天猫' ...
# → 折线图 + 洞察："周末交易量明显高于工作日"
```

### 8.4 效果评估与优化方向

```
评估结果（100 条测试问题）：

  ┌──────────────┬──────────┬──────────┐
  │ 指标          │ 目标      │ 实际      │
  ├──────────────┼──────────┼──────────┤
  │ SQL 生成准确率 │ > 80%    │ 85% ✅   │
  │ SQL 执行成功率 │ > 90%    │ 93% ✅   │
  │ 自动修复成功率 │ > 70%    │ 78% ✅   │
  │ 图表类型正确率 │ > 85%    │ 89% ✅   │
  │ 洞察有用性     │ > 3.5/5  │ 3.8 ✅   │
  │ 平均响应时间   │ < 5s     │ 3.2s ✅  │
  │ 多轮理解准确率 │ > 75%    │ 72% ⚠️  │
  └──────────────┴──────────┴──────────┘

  常见失败原因：
    ⚠️ 复杂窗口函数 SQL → 加 Few-shot 示例
    ⚠️ 模糊时间范围 → 加默认假设机制
    ⚠️ 多轮追问丢上下文 → 增加历史轮数

  优化方向：
    → Schema 增加列注释和枚举值
    → 高频问题模板缓存
    → 复杂查询拆分为多步骤
```

**第 8 章核心知识回顾：**

| 阶段 | 做了什么 |
|:---|:---|
| **场景定义** | 5 大电商分析场景，⭐~⭐⭐⭐ 难度 |
| **Schema 配置** | 4 张核心表 + 外键关系 |
| **完整链路** | 意图→SQL→执行→图表→洞察→上下文 |
| **效果** | SQL 准确率 85%，整体可用 |

---

## 附录

### A. Text-to-SQL Prompt 模板库

| 场景 | Prompt 关键片段 | temperature |
|:---|:---|:---|
| **简单聚合** | "只生成 SELECT，加中文别名" | 0 |
| **多表 JOIN** | Schema + 外键关系 + 示例数据 | 0 |
| **窗口函数** | Few-shot 示例 + 具体语法提示 | 0 |
| **环比计算** | 明确日期格式 + LAG 函数示例 | 0 |
| **追问钻取** | 对话历史 + 上一条 SQL | 0 |
| **模糊问题** | 要求返回 clarification JSON | 0 |

### B. 常用图表类型选择指南

```
图表选择决策树：

  数据维度？
  ├── 1 个维度（单列数值）
  │   └── 单个数字 → 大数卡片 / KPI
  │
  ├── 2 个维度
  │   ├── 类别 × 数值
  │   │   ├── ≤ 8 个类别 → 柱状图 / 饼图
  │   │   └── > 8 个类别 → 横向柱状图 / Top N
  │   │
  │   ├── 时间 × 数值 → 折线图
  │   └── 数值 × 数值 → 散点图
  │
  └── 3+ 个维度
      ├── 类别 × 类别 × 数值 → 分组柱状图
      ├── 时间 × 分组 × 数值 → 多折线图
      └── 地理 × 数值 → 地图
```

### C. 数据分析常见问题与 SQL 模式

| 问题类型 | SQL 模式 | 示例 |
|:---|:---|:---|
| **总量统计** | `SUM/COUNT + WHERE` | 本月 GMV |
| **Top N** | `ORDER BY ... LIMIT N` | 销量 Top 10 |
| **占比分析** | `SUM(x) / SUM(total)` | 各渠道占比 |
| **环比** | `LAG() OVER (ORDER BY)` | GMV 周环比 |
| **同比** | `JOIN 去年同期` | 同比增长率 |
| **留存** | `窗口函数 + CASE WHEN` | 7 日留存 |
| **复购率** | `子查询 + COUNT >= 2` | 月复购率 |
| **漏斗** | `多步骤 COUNT DISTINCT` | 注册→下单转化 |
| **RFM** | `NTILE() 分组` | 用户价值分层 |
| **异常检测** | `AVG ± 2*STDDEV` | 突增突降预警 |
