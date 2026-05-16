# AI 写作助手开发实战

> 从零构建一个生产级 AI 写作助手——涵盖需求拆解与架构设计、大纲智能生成、长文分段续写、风格控制与改写、语法纠错与润色、流式输出与实时编辑、人机协作交互设计、效果评估与持续优化，一套完整方案让你的写作助手真正好用。

---

## 1. 需求分析与架构设计

### 1.1 AI 写作助手能做什么：功能全景

```
AI 写作助手的六大核心能力：

  ① 大纲生成 ── 输入主题，自动生成多级文章结构
     "帮我写一篇关于微服务架构的技术博客"
     → 自动生成 8 章大纲，每章含 3-4 个小节

  ② 分段续写 ── 按大纲逐段生成正文内容
     点击某个章节标题 → AI 自动写出该章节的完整内容
     支持上下文连贯：后面的章节能感知前面已写的内容

  ③ 风格控制 ── 切换正式/口语/技术/营销等语气
     同一段内容，一键切换为"严肃学术风"或"轻松口语风"

  ④ 语法纠错 ── 错别字、标点、语病自动修复
     选中段落 → AI 标红错误 → 一键接受修改

  ⑤ 润色改写 ── 扩写、缩写、提升可读性
     "把这段 500 字压缩到 200 字"、"让这段更有文学感"

  ⑥ 人机协作 ── 光标处补全、选中改写、侧边对话
     像 GitHub Copilot 一样，在你写作时实时给出建议
```

### 1.2 用户场景分析：谁在用、怎么用

| 用户类型 | 典型场景 | 核心需求 |
|:---|:---|:---|
| **技术博主** | 写教程/文档 | 大纲生成 + 代码段穿插 + 技术准确性 |
| **内容运营** | 写公众号/营销文案 | 风格控制 + 爆款标题 + SEO 优化 |
| **学术研究** | 写论文/报告 | 文献引用 + 学术风格 + 查重合规 |
| **产品经理** | 写 PRD/周报 | 模板填充 + 结构化输出 |
| **翻译工作者** | 中英互译 + 润色 | 风格保持 + 术语一致性 |

### 1.3 整体架构设计：前端编辑器 + 后端 AI 引擎

```
系统架构：

  ┌──────────────────────────────────────────┐
  │             前端编辑器层                    │
  │  ┌──────────┐  ┌──────────┐  ┌────────┐ │
  │  │ 富文本编辑 │  │ AI 交互面板│  │ Diff 视图│ │
  │  │ (Monaco)  │  │ (侧边栏)  │  │ (改写)  │ │
  │  └──────────┘  └──────────┘  └────────┘ │
  └────────────────┬─────────────────────────┘
                   │ SSE / WebSocket
  ┌────────────────┴─────────────────────────┐
  │             后端 AI 引擎                    │
  │  ┌──────────┐  ┌──────────┐  ┌────────┐ │
  │  │ Prompt 管理│  │ 上下文管理 │  │ 流式处理 │ │
  │  │ (模板库)  │  │ (Token)  │  │ (SSE)  │ │
  │  └──────────┘  └──────────┘  └────────┘ │
  │  ┌──────────┐  ┌──────────┐  ┌────────┐ │
  │  │ 模型路由  │  │ 缓存层    │  │ 审计日志 │ │
  │  └──────────┘  └──────────┘  └────────┘ │
  └────────────────┬─────────────────────────┘
                   │
  ┌────────────────┴─────────────────────────┐
  │            LLM Provider 层                 │
  │  DeepSeek │ Qwen │ GLM │ OpenAI (Fallback)│
  └──────────────────────────────────────────┘
```

### 1.4 技术选型：模型 / 框架 / 编辑器

| 组件 | 推荐选型 | 理由 |
|:---|:---|:---|
| **主力模型** | DeepSeek-V3 | 中文写作效果好、性价比高 |
| **长文档模型** | Qwen-Max (128K) | 超长上下文、中文优化 |
| **后端框架** | FastAPI + SSE | 异步 + 流式天然契合 |
| **前端编辑器** | Monaco Editor | VS Code 同款、生态完善 |
| **富文本框架** | Tiptap / ProseMirror | 可扩展、插件化 |
| **Markdown** | markdown-it | 解析快、插件丰富 |

> 💡 **关键选型原则：写作助手的核心竞争力不在模型，在交互**——用户体验（流式输出速度、Inline 补全的自然度、改写的 Diff 展示）决定产品成败。

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **六大能力** | 大纲生成 + 续写 + 风格 + 纠错 + 润色 + 协作 |
| **架构分层** | 前端编辑器 + 后端 AI 引擎 + LLM Provider |
| **模型选型** | DeepSeek 主力写作 + Qwen 长文档 |
| **竞争力** | 不在模型能力，在交互体验 |

---

## 2. 大纲智能生成：从主题到结构

### 2.1 大纲生成的 Prompt 工程

```python
OUTLINE_PROMPT = """你是一个专业的写作大纲设计师。根据用户提供的主题，生成一份结构清晰的文章大纲。

## 要求
1. 生成 {num_chapters} 个章节，每章 3-4 个小节
2. 章节标题要具体且有吸引力，不要太泛
3. 写作风格：{style}
4. 目标读者：{audience}
5. 文章字数预估：{word_count} 字

## 输出格式
严格按 JSON 格式输出：
{{
  "title": "文章标题",
  "summary": "一句话摘要",
  "chapters": [
    {{
      "title": "章节标题",
      "sections": [
        {{"title": "小节标题", "key_points": ["要点1", "要点2"]}}
      ]
    }}
  ]
}}

## 主题
{topic}

## 补充要求
{extra_requirements}"""
```

```python
class OutlineGenerator:
    """大纲生成器"""
    
    async def generate(self, topic: str, **kwargs) -> dict:
        """生成文章大纲"""
        prompt = OUTLINE_PROMPT.format(
            topic=topic,
            num_chapters=kwargs.get("num_chapters", 8),
            style=kwargs.get("style", "技术教程"),
            audience=kwargs.get("audience", "有经验的开发者"),
            word_count=kwargs.get("word_count", 5000),
            extra_requirements=kwargs.get("extra", ""),
        )
        
        response = await self.llm.chat(
            "deepseek",
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,  # 稍高温度增加创意
        )
        
        return json.loads(response.choices[0].message.content)
```

### 2.2 多级大纲的结构化输出

```python
from pydantic import BaseModel

class Section(BaseModel):
    title: str
    key_points: list[str]
    estimated_words: int = 500

class Chapter(BaseModel):
    title: str
    sections: list[Section]
    
class Outline(BaseModel):
    title: str
    summary: str
    chapters: list[Chapter]
    
    def to_markdown(self) -> str:
        """转成 Markdown 大纲"""
        lines = [f"# {self.title}\n", f"> {self.summary}\n"]
        for i, ch in enumerate(self.chapters, 1):
            lines.append(f"## {i}. {ch.title}\n")
            for j, sec in enumerate(ch.sections, 1):
                lines.append(f"### {i}.{j} {sec.title}")
                for point in sec.key_points:
                    lines.append(f"- {point}")
                lines.append("")
        return "\n".join(lines)
    
    @property
    def total_words(self) -> int:
        return sum(s.estimated_words for ch in self.chapters for s in ch.sections)
```

### 2.3 交互式大纲调整：拖拽 / 增删 / 重排

```python
class OutlineEditor:
    """大纲交互式编辑"""
    
    def __init__(self, outline: Outline):
        self.outline = outline
        self.history = [outline.model_copy(deep=True)]  # 撤销历史
    
    def move_chapter(self, from_idx: int, to_idx: int):
        """拖拽移动章节"""
        ch = self.outline.chapters.pop(from_idx)
        self.outline.chapters.insert(to_idx, ch)
        self._save_history()
    
    def add_chapter(self, title: str, after_idx: int):
        """在指定位置插入新章节"""
        new_ch = Chapter(title=title, sections=[])
        self.outline.chapters.insert(after_idx + 1, new_ch)
        self._save_history()
    
    def delete_chapter(self, idx: int):
        """删除章节"""
        self.outline.chapters.pop(idx)
        self._save_history()
    
    async def expand_chapter(self, idx: int, llm) -> Chapter:
        """AI 自动展开某个章节的小节"""
        ch = self.outline.chapters[idx]
        prompt = f"将以下章节标题展开为 3-4 个小节：{ch.title}"
        # ... 调用 LLM 获取小节列表
    
    def undo(self):
        """撤销上一步操作"""
        if len(self.history) > 1:
            self.history.pop()
            self.outline = self.history[-1].model_copy(deep=True)
```

### 2.4 基于 RAG 的主题研究辅助

```python
class TopicResearcher:
    """在生成大纲前，用 RAG 研究主题"""
    
    async def research(self, topic: str) -> dict:
        """搜索相关资料辅助大纲生成"""
        # 1. 搜索知识库中的相关文档
        related_docs = await self.vector_store.search(topic, top_k=5)
        
        # 2. 搜索网络获取最新信息
        web_results = await self.web_search(topic)
        
        # 3. 汇总研究结果
        context = "\n".join([d.content[:500] for d in related_docs])
        
        prompt = f"""基于以下参考资料，为主题"{topic}"提供写作建议：
{context}

请给出：
1. 该主题的核心知识点（5-8 个）
2. 读者最关心的 3 个问题
3. 推荐的文章结构"""
        
        result = await self.llm.chat("deepseek", [{"role": "user", "content": prompt}])
        return {"research": result.choices[0].message.content, "sources": related_docs}
```

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Prompt 工程** | 用结构化模板 + JSON 输出控制大纲质量 |
| **Pydantic 建模** | 用类型安全的模型定义大纲结构 |
| **交互编辑** | 支持拖拽/增删/撤销的大纲编辑器 |
| **RAG 辅助** | 先研究主题再生成大纲，质量更高 |

---

## 3. 长文分段续写：让 AI 写出完整文章

### 3.1 长文写作的核心挑战：上下文窗口 vs 文章长度

```
长文写作的矛盾：

  一篇 5000 字的文章 ≈ 7000 Token
  一篇 10000 字的技术教程 ≈ 14000 Token
  
  模型上下文窗口：
    DeepSeek-V3 ── 64K Token（够用）
    Qwen-Max ── 128K Token（充裕）
    GPT-4o ── 128K Token（充裕）
  
  但问题不是"放不放得下"，而是：
    ① 上下文太长 → 生成质量下降（Lost in the Middle）
    ② 一次生成全文 → 前后风格不一致
    ③ 一次生成全文 → 用户等待时间太长（30s+）
    ④ 用户需要逐章修改 → 全文生成不灵活

  → 解决方案：分段续写 + 摘要压缩
```

### 3.2 分段续写策略：滑动窗口 + 摘要压缩

```python
class ChapterWriter:
    """分段续写引擎"""
    
    MAX_CONTEXT_TOKENS = 8000  # 给上下文的 Token 预算
    
    async def write_chapter(self, outline: Outline, chapter_idx: int,
                            previous_chapters: list[str]) -> str:
        """写某一章的内容"""
        chapter = outline.chapters[chapter_idx]
        
        # 构建上下文
        context = self._build_context(outline, chapter_idx, previous_chapters)
        
        prompt = f"""你正在写一篇文章《{outline.title}》的第 {chapter_idx+1} 章。

## 全文大纲
{outline.to_markdown()}

## 已写内容摘要
{context}

## 当前要写的章节
{chapter.title}
小节：{', '.join(s.title for s in chapter.sections)}

## 写作要求
1. 按小节逐一展开，每个小节 300-500 字
2. 内容要与前面已写的章节连贯
3. 包含代码示例（如适用）
4. 语气：专业但易懂"""
        
        return await self.llm.chat_stream("deepseek", [
            {"role": "user", "content": prompt}
        ])
    
    def _build_context(self, outline, chapter_idx, previous_chapters) -> str:
        """构建上下文：摘要压缩 + 滑动窗口"""
        if not previous_chapters:
            return "这是第一章，无前文。"
        
        # 策略：最近一章保留全文，更早的章节只保留摘要
        context_parts = []
        
        for i, ch_content in enumerate(previous_chapters):
            if i == chapter_idx - 1:
                # 最近一章：保留完整内容（最多 3000 Token）
                context_parts.append(f"### 第 {i+1} 章（完整）\n{ch_content[:4000]}")
            else:
                # 更早的章节：压缩为摘要
                summary = self._summarize(ch_content)
                context_parts.append(f"### 第 {i+1} 章（摘要）\n{summary}")
        
        return "\n\n".join(context_parts)
```

### 3.3 段落级生成与全文连贯性控制

```python
class CoherenceController:
    """全文连贯性控制"""
    
    def __init__(self):
        self.key_terms = {}     # 核心术语统一
        self.style_guide = ""   # 风格指南
        self.tone_samples = []  # 语气参考
    
    def build_coherence_prompt(self, existing_text: str) -> str:
        """从已有内容中提取风格指南"""
        return f"""分析以下文本的写作风格，提取：
1. 语气特征（正式/口语/混合）
2. 段落平均长度
3. 是否使用列表/表格/代码
4. 人称视角（你/我们/读者）
5. 核心术语列表

文本：
{existing_text[:2000]}

以 JSON 格式返回。"""
    
    async def check_coherence(self, new_text: str, previous_text: str) -> dict:
        """检查新生成的内容是否与前文连贯"""
        prompt = f"""对比以下两段文本的风格一致性：

前文（最后 500 字）：
{previous_text[-500:]}

新内容（前 500 字）：
{new_text[:500]}

检查：语气是否一致？人称是否统一？术语是否前后一致？
回复 JSON：{{"coherent": true/false, "issues": ["..."]}}"""
        
        result = await self.llm.chat("deepseek", [{"role": "user", "content": prompt}])
        return json.loads(result.choices[0].message.content)
```

### 3.4 流式输出：打字机效果的实时体验

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/api/write/chapter")
async def write_chapter_stream(request: WriteRequest):
    """流式输出章节内容"""
    
    async def generate():
        stream = await llm.chat(
            "deepseek",
            messages=request.messages,
            stream=True,
        )
        
        buffer = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            buffer += delta
            
            # 逐字符发送（打字机效果）
            yield f"data: {json.dumps({'content': delta})}\n\n"
            
            # 每段完成时发送段落完成事件
            if "\n\n" in buffer:
                yield f"data: {json.dumps({'event': 'paragraph_complete'})}\n\n"
                buffer = ""
        
        yield f"data: {json.dumps({'event': 'done'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **分段续写** | 按章节逐段生成，不一次生成全文 |
| **摘要压缩** | 远处章节压缩为摘要，近处保留全文 |
| **连贯性检查** | 用 LLM 检查新内容与前文的风格一致性 |
| **流式输出** | SSE 逐字符推送，打字机效果 |

---

## 4. 风格控制与改写：让 AI 的文笔听你的

### 4.1 风格控制的 Prompt 设计模式

```python
# 风格控制的核心：用 System Prompt 定义"人设"
STYLE_SYSTEM_PROMPTS = {
    "formal": """你是一名严谨的技术文档编写者。
    - 使用第三人称或被动语态
    - 避免口语化表达和感叹号
    - 每个论点都需要有依据
    - 段落结构：论点 → 论据 → 结论""",
    
    "casual": """你是一名轻松幽默的技术博主。
    - 使用第二人称"你"直接对话
    - 适当使用比喻和类比帮助理解
    - 可以用 emoji 和感叹号
    - 段落要短，读起来轻松""",
    
    "academic": """你是一名学术论文写作助手。
    - 使用学术用语和规范表达
    - 引用格式遵循 APA/GB 标准
    - 逻辑严密，避免主观判断
    - 段落结构：引言 → 分析 → 总结""",
}
```

### 4.2 预定义风格模板：正式 / 口语 / 技术 / 营销

| 风格 | temperature | 人称 | 段落长度 | 示例特征 |
|:---|:---|:---|:---|:---|
| **正式技术** | 0.3 | 第三人称 | 150-200 字 | 精确、无废话 |
| **口语轻松** | 0.7 | 你 | 50-100 字 | 短句、比喻多 |
| **学术严谨** | 0.2 | 被动语态 | 200-300 字 | 引用、逻辑链 |
| **营销文案** | 0.8 | 你 | 30-80 字 | 煽动性、数字多 |
| **新闻报道** | 0.3 | 第三人称 | 80-150 字 | 倒金字塔结构 |

```python
class StyleConfig:
    """风格配置"""
    name: str
    system_prompt: str
    temperature: float
    max_paragraph_length: int
    
    @classmethod
    def presets(cls) -> dict:
        return {
            "技术教程": cls(name="技术教程", system_prompt=STYLE_SYSTEM_PROMPTS["formal"],
                          temperature=0.3, max_paragraph_length=200),
            "公众号": cls(name="公众号", system_prompt=STYLE_SYSTEM_PROMPTS["casual"],
                        temperature=0.7, max_paragraph_length=100),
            # ...
        }
```

### 4.3 风格迁移：模仿指定作者或文体

```python
class StyleTransfer:
    """风格迁移：让 AI 模仿特定风格"""
    
    async def learn_style(self, sample_text: str) -> str:
        """从样本文本中学习风格"""
        prompt = f"""分析以下文本的写作风格特征：

{sample_text[:2000]}

提取以下风格要素：
1. 句子平均长度（短/中/长）
2. 常用修辞手法
3. 段落结构模式
4. 语气正式度（1-10）
5. 特有的表达习惯
6. 标点使用特点

以 JSON 格式返回风格描述。"""
        
        result = await self.llm.chat("deepseek", [{"role": "user", "content": prompt}])
        return result.choices[0].message.content  # 风格描述
    
    async def transfer(self, content: str, style_description: str) -> str:
        """将内容转换为目标风格"""
        prompt = f"""将以下内容改写为指定风格，保持核心信息不变：

目标风格：
{style_description}

原文：
{content}

请改写："""
        
        result = await self.llm.chat("deepseek", [{"role": "user", "content": prompt}])
        return result.choices[0].message.content
```

### 4.4 一键改写：扩写 / 缩写 / 换风格

```python
class Rewriter:
    """一键改写引擎"""
    
    REWRITE_PROMPTS = {
        "expand": "将以下内容扩写为原文的 2-3 倍长度，补充更多细节和例子：\n{text}",
        "compress": "将以下内容精简为原文的 1/3 长度，保留核心信息：\n{text}",
        "simplify": "将以下内容用更简单的语言重写，让小学生也能看懂：\n{text}",
        "professional": "将以下内容改写为更专业的表达：\n{text}",
        "literary": "将以下内容改写为更有文学性的表达，使用修辞手法：\n{text}",
    }
    
    async def rewrite(self, text: str, mode: str, **kwargs) -> str:
        """一键改写"""
        prompt = self.REWRITE_PROMPTS[mode].format(text=text)
        
        if kwargs.get("keep_structure"):
            prompt += "\n保持原文的段落结构不变。"
        if kwargs.get("target_length"):
            prompt += f"\n目标长度：约 {kwargs['target_length']} 字。"
        
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0.5)
        
        return result.choices[0].message.content
```

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **风格 Prompt** | 用 System Prompt 定义写作人设 |
| **预定义模板** | 正式/口语/学术/营销各有参数配置 |
| **风格迁移** | 从样本提取风格特征再应用到新内容 |
| **一键改写** | 扩写/缩写/简化/专业化等模式 |

---

## 5. 语法纠错与润色：从能读到好读

### 5.1 语法纠错引擎：规则 + LLM 混合方案

```python
class GrammarChecker:
    """语法纠错引擎（规则 + LLM 混合）"""
    
    async def check(self, text: str) -> list[dict]:
        """返回所有修改建议"""
        corrections = []
        
        # Layer 1: 规则引擎（快速，< 10ms）
        corrections.extend(self._rule_check(text))
        
        # Layer 2: LLM 语义检查（准确，~ 500ms）
        llm_corrections = await self._llm_check(text)
        corrections.extend(llm_corrections)
        
        # 去重 + 排序
        return self._deduplicate(corrections)
    
    async def _llm_check(self, text: str) -> list[dict]:
        prompt = f"""检查以下中文文本的语法和表达问题，包括：
1. 错别字和用词不当
2. 标点符号错误
3. 语序不通顺
4. 主谓搭配不当
5. 冗余表达

文本："{text}"

以 JSON 数组返回每处修改建议：
[{{"original": "原文", "corrected": "修正", "reason": "原因", "position": 字符位置}}]"""
        
        result = await self.llm.chat("deepseek", [{"role": "user", "content": prompt}])
        return json.loads(result.choices[0].message.content)
```

### 5.2 中文场景专项：错别字 / 标点 / 语序

```python
class ChineseProofreader:
    """中文专项校验"""
    
    # 常见错别字映射
    TYPO_MAP = {
        "的地得": {
            r"动词\s*的": "动词 地",  # "慢慢的走" → "慢慢地走"
            r"形容词\s*得": None,      # "跑的很快" → "跑得很快"
        },
        "常见混淆": {
            "即使": "既使",  # "既使" 是错的
            "以至于": "以致于",
            "权利": "权力",  # 需根据语境判断
        },
    }
    
    # 标点规则
    PUNCTUATION_RULES = [
        (r"\.{3}", "……"),          # 三个点 → 省略号
        (r"\.\.\.", "……"),         # 同上
        (r'""', '「」'),            # 可选：直角引号
        (r"！{2,}", "！"),          # 多个感叹号 → 一个
        (r"。。。", "……"),          # 句号省略号
    ]
    
    def check_de(self, text: str) -> list[dict]:
        """的地得用法检查（中文高频错误）"""
        issues = []
        # 简化规则：动词前用"地"，形容词后用"得"
        # 实际需要 LLM 辅助判断
        return issues
```

### 5.3 润色策略：简洁化 / 专业化 / 文学化

```python
class Polisher:
    """文本润色引擎"""
    
    POLISH_MODES = {
        "concise": {
            "prompt": "删除冗余词汇和重复表达，让文章更简洁有力。",
            "examples": [
                ("基本上来说", ""),
                ("在某种程度上", ""),
                ("其实说白了就是", "即"),
            ],
        },
        "professional": {
            "prompt": "提升专业度，使用更精确的术语和更规范的表达。",
            "examples": [
                ("搞了一个", "实现了一个"),
                ("差不多", "约"),
                ("整", "实现"),
            ],
        },
        "literary": {
            "prompt": "增加文学性，适当使用修辞手法，让文字更优美。",
            "examples": [],
        },
    }
    
    async def polish(self, text: str, mode: str) -> str:
        config = self.POLISH_MODES[mode]
        prompt = f"""润色以下文本。要求：{config['prompt']}

保持核心含义不变，只改善表达方式。

原文：
{text}

润色后："""
        
        result = await self.llm.chat("deepseek", [{"role": "user", "content": prompt}],
                                      temperature=0.4)
        return result.choices[0].message.content
```

### 5.4 Diff 展示：让用户清晰看到修改了什么

```python
import difflib

class DiffRenderer:
    """Diff 可视化：清晰展示修改内容"""
    
    def generate_diff(self, original: str, modified: str) -> list[dict]:
        """生成逐行 Diff"""
        differ = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            lineterm="",
        )
        
        changes = []
        for line in differ:
            if line.startswith("+") and not line.startswith("+++"):
                changes.append({"type": "add", "content": line[1:]})
            elif line.startswith("-") and not line.startswith("---"):
                changes.append({"type": "remove", "content": line[1:]})
            elif line.startswith(" "):
                changes.append({"type": "unchanged", "content": line[1:]})
        
        return changes
    
    def generate_inline_diff(self, original: str, modified: str) -> str:
        """生成行内 Diff（红删绿增）"""
        matcher = difflib.SequenceMatcher(None, original, modified)
        result = []
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == "equal":
                result.append(original[i1:i2])
            elif op == "replace":
                result.append(f"~~{original[i1:i2]}~~**{modified[j1:j2]}**")
            elif op == "insert":
                result.append(f"**{modified[j1:j2]}**")
            elif op == "delete":
                result.append(f"~~{original[i1:i2]}~~")
        return "".join(result)
```

> 💡 **Diff 展示是写作助手的"信任基石"**——用户不接受黑盒修改，必须清楚地看到 AI 改了哪里、为什么改。红色删除线 + 绿色新增是最直观的方式。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **混合方案** | 规则引擎快速筛 + LLM 精准改 |
| **中文专项** | 的地得、标点、错别字是高频问题 |
| **润色模式** | 简洁化/专业化/文学化三种方向 |
| **Diff 展示** | 红删绿增，让用户看清每处修改 |

---

## 6. 人机协作编辑：AI 是助手不是替代

### 6.1 协作模式设计：建议 / 补全 / 对话三种交互

```
三种人机协作模式：

  ① 建议模式（Suggestion）
     AI 在后台分析，下划线标注可改善的地方
     用户悬停查看建议 → 点击接受/忽略
     → 类似 Word 的语法检查

  ② 补全模式（Completion）
     用户写到一半停顿 → AI 自动续写灰色文本
     按 Tab 接受 / 按 Esc 忽略
     → 类似 GitHub Copilot

  ③ 对话模式（Chat）
     用户在侧边栏与 AI 讨论写作
     "帮我想一个更好的标题"、"这段逻辑对吗？"
     → 类似 ChatGPT 但聚焦当前文档

  选择策略：
    写第一稿 → 补全模式
    修改润色 → 建议模式
    遇到卡壳 → 对话模式
```

### 6.2 Inline 补全：光标处智能续写

```python
class InlineCompletion:
    """光标处智能补全"""
    
    COMPLETION_PROMPT = """你正在帮用户续写一篇文章。
用户目前写到了光标处（用 [CURSOR] 标记），请续写 1-3 句话。

要求：
1. 语气和风格与前文保持一致
2. 内容自然连贯
3. 不要重复前文已有的内容

文章内容：
{before_cursor}[CURSOR]

请直接输出续写内容，不要解释："""

    async def complete(self, document: str, cursor_position: int) -> str:
        """在光标处生成补全"""
        before = document[:cursor_position]
        after = document[cursor_position:]
        
        # 只取光标前 2000 字符作为上下文
        context = before[-2000:]
        
        prompt = self.COMPLETION_PROMPT.format(before_cursor=context)
        
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ], temperature=0.5, max_tokens=200)
        
        completion = result.choices[0].message.content
        
        # 检查补全内容是否与后文冲突
        if after and completion.strip().startswith(after[:20].strip()):
            return ""  # 跳过，避免重复
        
        return completion
    
    async def complete_stream(self, document: str, cursor_position: int):
        """流式补全（用户可以边看边采纳）"""
        # 类似 complete，但用 stream=True
        pass
```

### 6.3 选中改写：选择文本后一键操作

```python
class SelectionActions:
    """选中文本后的操作菜单"""
    
    ACTIONS = {
        "rewrite": "改写这段文字，让表达更好",
        "expand": "将这段话扩展为更详细的内容",
        "compress": "将这段话精简为一句话",
        "explain": "解释这段话的含义",
        "translate_en": "翻译成英文",
        "translate_zh": "翻译成中文",
        "fix_grammar": "修正语法和错别字",
        "add_example": "为这段话补充一个例子",
    }
    
    async def execute(self, selected_text: str, action: str, 
                       context: str = "") -> dict:
        """执行选中文本操作"""
        action_prompt = self.ACTIONS[action]
        
        prompt = f"""用户选中了以下文本，请{action_prompt}。

上下文（选中文本的前后文）：
{context}

选中的文本：
{selected_text}

请直接输出修改后的文本："""
        
        result = await self.llm.chat("deepseek", [
            {"role": "user", "content": prompt}
        ])
        
        modified = result.choices[0].message.content
        diff = DiffRenderer().generate_inline_diff(selected_text, modified)
        
        return {"original": selected_text, "modified": modified, "diff": diff}
```

### 6.4 侧边栏对话：与 AI 讨论写作思路

```python
class WritingChat:
    """侧边栏写作对话"""
    
    SYSTEM_PROMPT = """你是一个写作助手。用户正在写一篇文章，你可以：
1. 帮用户构思写作思路
2. 回答写作相关的问题
3. 建议更好的表达方式
4. 提供相关的素材和数据

当前文档标题：{title}
当前文档内容（前 3000 字）：
{document_preview}

注意：你的建议要结合用户正在写的文档内容。"""

    async def chat(self, user_message: str, document: str, 
                    history: list) -> str:
        """与用户对话"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT.format(
                title=self._extract_title(document),
                document_preview=document[:3000],
            )},
            *history,
            {"role": "user", "content": user_message},
        ]
        
        result = await self.llm.chat("deepseek", messages, stream=True)
        return result
```

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **三种模式** | 建议（标注）、补全（续写）、对话（讨论） |
| **Inline 补全** | 光标处续写 1-3 句，Tab 接受 |
| **选中改写** | 选中文本后弹出操作菜单 |
| **侧边对话** | 带文档上下文的对话，聚焦当前写作 |

---

## 7. 后端工程：API 设计与性能优化

### 7.1 API 设计：RESTful + SSE 流式接口

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# ── API 端点设计 ──
# POST /api/outline/generate     生成大纲
# POST /api/write/chapter        续写章节（流式）
# POST /api/rewrite              改写（流式）
# POST /api/grammar/check        语法检查
# POST /api/complete/inline      Inline 补全
# POST /api/chat                 侧边栏对话（流式）

class WriteRequest(BaseModel):
    document: str           # 当前文档内容
    chapter_idx: int        # 要写的章节索引
    outline: dict           # 大纲结构
    style: str = "formal"   # 风格
    
class RewriteRequest(BaseModel):
    text: str               # 要改写的文本
    mode: str               # expand/compress/simplify/...
    context: str = ""       # 选中文本的上下文

@app.post("/api/write/chapter")
async def write_chapter(req: WriteRequest):
    """流式续写章节"""
    writer = ChapterWriter()
    
    async def stream():
        async for chunk in writer.write_chapter_stream(
            req.outline, req.chapter_idx, req.document
        ):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield f"data: {json.dumps({'event': 'done'})}\n\n"
    
    return StreamingResponse(stream(), media_type="text/event-stream")
```

### 7.2 上下文管理：长文档的 Token 预算分配

```python
class TokenBudgetManager:
    """Token 预算管理"""
    
    MODEL_LIMITS = {
        "deepseek": {"max_tokens": 64000, "output_limit": 8000},
        "qwen-max": {"max_tokens": 128000, "output_limit": 8000},
    }
    
    def allocate(self, task: str, document_length: int) -> dict:
        """根据任务类型分配 Token 预算"""
        budgets = {
            "outline":    {"system": 500, "context": 2000, "output": 3000},
            "write":      {"system": 800, "context": 8000, "output": 4000},
            "rewrite":    {"system": 300, "context": 2000, "output": 2000},
            "grammar":    {"system": 500, "context": 3000, "output": 3000},
            "complete":   {"system": 200, "context": 2000, "output": 200},
            "chat":       {"system": 500, "context": 3000, "output": 2000},
        }
        
        budget = budgets.get(task, budgets["chat"])
        total = sum(budget.values())
        
        return {
            **budget,
            "total": total,
            "model": "qwen-max" if total > 30000 else "deepseek",
        }
    
    def truncate_context(self, text: str, max_tokens: int) -> str:
        """截断上下文到预算内"""
        # 粗略估算：1 Token ≈ 1.5 中文字符
        max_chars = int(max_tokens * 1.5)
        if len(text) <= max_chars:
            return text
        # 保留首尾，截断中间
        half = max_chars // 2
        return text[:half] + "\n...(中间内容省略)...\n" + text[-half:]
```

### 7.3 缓存与去重：相似请求的智能复用

```python
import hashlib

class WritingCache:
    """写作结果缓存"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 小时过期
    
    def _cache_key(self, task: str, content_hash: str) -> str:
        return f"writing:{task}:{content_hash}"
    
    def _hash_content(self, text: str) -> str:
        """计算内容指纹"""
        # 只取前 500 字符做 hash（避免全文 hash 太慢）
        return hashlib.md5(text[:500].encode()).hexdigest()[:12]
    
    async def get_or_generate(self, task: str, text: str, 
                               generator) -> str:
        """缓存命中则返回，否则生成"""
        key = self._cache_key(task, self._hash_content(text))
        
        # 查缓存
        cached = await self.redis.get(key)
        if cached:
            return cached
        
        # 生成
        result = await generator()
        
        # 写缓存（仅缓存非流式结果）
        await self.redis.setex(key, self.ttl, result)
        
        return result
```

### 7.4 并发控制与成本优化

```python
import asyncio

class ConcurrencyManager:
    """并发控制 + 成本优化"""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.daily_cost = 0.0
        self.daily_limit = 50.0  # 每日成本上限 $50
    
    async def execute(self, task, cost_estimate: float):
        """受控执行"""
        # 成本检查
        if self.daily_cost + cost_estimate > self.daily_limit:
            raise HTTPException(429, "今日 AI 调用配额已用完")
        
        # 并发控制
        async with self.semaphore:
            result = await task()
            self.daily_cost += cost_estimate
            return result
```

> 💡 **写作场景的成本特征：高频 + 低单价**——Inline 补全每次只生成几十个 Token，但频率很高（每分钟可能触发 5-10 次），需要用缓存 + 防抖 + 低成本模型控制费用。

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **API 设计** | 6 个端点，写作/改写用 SSE 流式 |
| **Token 预算** | 按任务类型分配 system/context/output 预算 |
| **缓存策略** | 内容指纹 + Redis 缓存，1 小时过期 |
| **成本控制** | 并发限制 + 每日成本上限 + 防抖 |

---

## 8. 实战案例：构建一个 Markdown 写作助手

### 8.1 需求定义：面向技术博客的 Markdown 写作助手

```
产品定义：

  名称 ──── MarkWrite（Markdown AI 写作助手）
  定位 ──── 面向技术博主的 AI 辅助写作工具
  
  核心功能：
    ① 输入主题 → 生成技术教程大纲
    ② 点击章节 → AI 续写该章节内容
    ③ 选中文本 → 一键润色/扩写/缩写
    ④ 实时语法纠错 + 中文专项检查
    ⑤ 支持代码块的 Markdown 输出

  技术栈：
    前端：React + Monaco Editor + TailwindCSS
    后端：FastAPI + SSE
    模型：DeepSeek-V3（主力）+ Qwen-Max（长文）
    缓存：Redis
    部署：Docker Compose
```

### 8.2 核心功能实现：大纲 + 续写 + 润色

```python
# ── main.py：FastAPI 主文件 ──
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MarkWrite API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

# 初始化组件
outline_gen = OutlineGenerator()
chapter_writer = ChapterWriter()
polisher = Polisher()
grammar = GrammarChecker()
completer = InlineCompletion()

@app.post("/api/outline")
async def generate_outline(topic: str, num_chapters: int = 6):
    """生成文章大纲"""
    outline = await outline_gen.generate(topic, num_chapters=num_chapters)
    return outline

@app.post("/api/write")
async def write_chapter(req: WriteRequest):
    """流式续写章节"""
    async def stream():
        async for chunk in chapter_writer.write_chapter_stream(
            req.outline, req.chapter_idx, req.document
        ):
            yield f"data: {json.dumps({'c': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(stream(), media_type="text/event-stream")

@app.post("/api/polish")
async def polish_text(text: str, mode: str = "concise"):
    """润色文本"""
    result = await polisher.polish(text, mode)
    diff = DiffRenderer().generate_inline_diff(text, result)
    return {"original": text, "polished": result, "diff": diff}

@app.post("/api/complete")
async def inline_complete(document: str, cursor_pos: int):
    """光标处补全"""
    completion = await completer.complete(document, cursor_pos)
    return {"completion": completion}
```

### 8.3 编辑器集成：Monaco Editor + AI 插件

```
前端交互设计：

  ┌─────────────────────────────────────────────┐
  │ MarkWrite                          [保存] [导出] │
  ├──────────┬──────────────────────────────────┤
  │ 📋 大纲   │  # AI 写作助手开发实战              │
  │          │                                  │
  │ ▶ 第1章   │  ## 1. 需求分析                    │
  │ ▶ 第2章   │                                  │
  │ ▶ 第3章   │  AI 写作助手的核心在于...|          │
  │ ▶ 第4章   │  ┌──────────────────┐           │
  │          │  │ 💡 续写建议（灰色）  │           │
  │          │  │ 解决用户在创作过程   │           │
  │          │  │ 中遇到的...        │           │
  │          │  │   [Tab 接受]       │           │
  │          │  └──────────────────┘           │
  │          │                                  │
  ├──────────┤  选中文本后弹出：                   │
  │ 💬 AI 对话│  [改写] [扩写] [缩写] [翻译] [纠错]  │
  │          │                                  │
  │ > 帮我想  │  ── Diff 预览 ──                  │
  │   一个更  │  ~~原来的文字~~ **改后的文字**       │
  │   好的标  │  [✓ 接受] [✗ 拒绝]                │
  │   题     │                                  │
  └──────────┴──────────────────────────────────┘
```

### 8.4 效果评估与用户反馈

```
评估指标体系：

  ┌─────────────┬────────────┬──────────────┐
  │ 指标         │ 目标        │ 实际          │
  ├─────────────┼────────────┼──────────────┤
  │ 大纲生成质量  │ > 4.0/5    │ 4.3/5 ✅     │
  │ 续写连贯性    │ > 4.0/5    │ 3.9/5 ⚠️    │
  │ 语法纠错准确率 │ > 90%      │ 92% ✅       │
  │ 润色采纳率    │ > 60%      │ 68% ✅       │
  │ 补全采纳率    │ > 30%      │ 35% ✅       │
  │ 首字延迟     │ < 500ms    │ 380ms ✅     │
  │ 用户满意度    │ > 4.0/5    │ 4.2/5 ✅     │
  └─────────────┴────────────┴──────────────┘
  
  用户反馈 Top 3：
    ✅ "大纲生成很快，省了我构思时间"
    ✅ "选中改写 + Diff 预览太好用了"
    ⚠️ "续写的内容有时候太泛，需要更具体"

  优化方向：
    → 续写加 Few-shot 示例提升具体性
    → 补全加防抖（500ms 停顿后才触发）
    → 缓存热门主题的大纲模板
```

**第 8 章核心知识回顾：**

| 阶段 | 做了什么 |
|:---|:---|
| **需求定义** | 6 大功能 + React/FastAPI/DeepSeek 技术栈 |
| **核心实现** | 4 个 API 端点，覆盖大纲/续写/润色/补全 |
| **编辑器集成** | Monaco Editor + 左侧大纲 + 右侧对话 |
| **效果评估** | 7 个指标，整体满意度 4.2/5 |

---

## 附录

### A. Prompt 模板库：写作场景速查

| 场景 | Prompt 关键句 | temperature |
|:---|:---|:---|
| **生成大纲** | "为主题 X 生成 N 章大纲，JSON 格式" | 0.7 |
| **章节续写** | "你正在写第 N 章，已写摘要如下..." | 0.5 |
| **扩写** | "将以下内容扩写为 2-3 倍，补充细节" | 0.6 |
| **缩写** | "精简为 1/3 长度，保留核心信息" | 0.3 |
| **语法检查** | "检查语法/错别字/标点，返回 JSON 数组" | 0.1 |
| **润色** | "润色以下文本，要求：简洁/专业/文学" | 0.4 |
| **Inline 补全** | "续写 1-3 句，风格与前文一致" | 0.5 |
| **风格迁移** | "分析风格特征 → 应用到新内容" | 0.5 |

### B. 常用写作风格参数配置

```python
STYLE_PRESETS = {
    "技术博客": {
        "temperature": 0.4,
        "system": "你是技术教程作者，语言精炼，包含代码示例",
        "paragraph_length": "100-200 字",
        "features": ["代码块", "表格", "要点列表"],
    },
    "公众号爆款": {
        "temperature": 0.7,
        "system": "你是10万+公众号作者，标题吸引眼球，内容通俗有趣",
        "paragraph_length": "50-80 字",
        "features": ["短句", "emoji", "金句", "数据"],
    },
    "学术论文": {
        "temperature": 0.2,
        "system": "你是学术写作助手，用语严谨，逻辑缜密",
        "paragraph_length": "200-300 字",
        "features": ["引用", "被动语态", "专业术语"],
    },
    "产品文档": {
        "temperature": 0.3,
        "system": "你是产品文档编写者，结构清晰，易于查阅",
        "paragraph_length": "80-150 字",
        "features": ["步骤编号", "注意事项", "截图说明"],
    },
}
```

### C. 评估指标与测试用例

```
写作助手测试用例（30 条核心）：

  大纲生成（5 条）
    □ 主题："微服务架构" → 生成 6-8 章，逻辑递进
    □ 主题："如何学Python" → 生成入门级大纲
    □ 主题模糊："AI" → 要求澄清方向
    □ 指定章节数：3 章 → 严格遵守
    □ 指定风格：口语化 → 大纲标题口语化

  续写（5 条）
    □ 第 1 章续写 → 无需前文上下文
    □ 第 5 章续写 → 与前 4 章保持连贯
    □ 包含代码的续写 → 代码语法正确
    □ 流式输出 → 首字延迟 < 500ms
    □ 超长文档 → Token 预算内完成

  改写（5 条）
    □ 扩写 → 长度增加 2-3 倍
    □ 缩写 → 长度减少 60%+
    □ 简化 → 可读性提升
    □ 专业化 → 术语准确
    □ 风格迁移 → 目标风格匹配

  纠错（5 条）
    □ 错别字 → 正确识别并修正
    □ 的地得 → 正确判断用法
    □ 标点错误 → 修正省略号/引号
    □ 语序 → 识别语序不当
    □ 无错误文本 → 不误报

  交互（10 条）
    □ Inline 补全 → 内容相关、不重复
    □ 选中改写 → 保持上下文连贯
    □ 侧边对话 → 结合文档内容回答
    □ Diff 展示 → 清晰标注修改处
    □ 大纲拖拽 → 正确移动章节
```
