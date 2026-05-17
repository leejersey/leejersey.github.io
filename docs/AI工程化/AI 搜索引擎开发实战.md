# AI 搜索引擎开发实战

> 从零构建类 Perplexity 的 AI 搜索引擎——联网搜索 + 网页内容提取 + RAG 增强 + 大模型答案生成 + 引用溯源，用 Python 实现一个能"上网查资料再回答"的智能搜索助手。

---

## 1. AI 搜索引擎核心原理：从传统搜索到 AI 搜索

### 1.1 传统搜索 vs AI 搜索：返回链接 vs 直接给答案

```
传统搜索 vs AI 搜索：

  传统搜索（Google）
  ═══════════════════════════════════════
  用户提问 → 返回 10 个链接
  用户需要自己点开、阅读、总结
  优点：信息全、来源广
  缺点：需要人工筛选和总结

  AI 搜索（Perplexity）
  ═══════════════════════════════════════
  用户提问 → 联网搜索 → 阅读网页 → 生成答案
  直接给出带引用的结构化回答
  优点：省时、直接、有出处
  缺点：可能遗漏信息、依赖 LLM 质量
```

### 1.2 Perplexity 架构拆解：它是怎么做的

```
Perplexity 的核心架构：

  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ 1. 查询改写│───→│ 2. 联网搜索│───→│ 3. 网页抓取│
  │ 优化搜索词 │     │ 多个搜索源 │     │ 提取正文   │
  └──────────┘     └──────────┘     └──────────┘
                                          │
  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ 6. 引用标注│←───│ 5. 答案生成│←───│ 4. RAG 组装│
  │ [1][2][3] │     │ 流式输出   │     │ Context   │
  └──────────┘     └──────────┘     └──────────┘
```

### 1.3 核心流程：查询 → 搜索 → 提取 → 生成 → 引用

| 步骤 | 做什么 | 用什么 |
|:---|:---|:---|
| 查询改写 | 将用户问题转为搜索友好的关键词 | LLM |
| 联网搜索 | 调用搜索 API 拿到 URL 和摘要 | Tavily / Bing API |
| 网页抓取 | 抓取 URL 内容，提取正文 | httpx + Trafilatura |
| RAG 组装 | 将多个网页内容塞进 Context | 分块 + 截断 |
| 答案生成 | 基于搜索结果生成回答 | GPT-4o / Claude |
| 引用标注 | 每句话标注来源 `[1][2]` | Prompt 指令 |

### 1.4 技术栈选型：Python + FastAPI + LLM

```
推荐技术栈：

  后端框架:  FastAPI（异步、SSE 支持）
  搜索 API:  Tavily（为 AI 应用设计的搜索 API）
  网页抓取:  httpx + Trafilatura
  大模型:    OpenAI GPT-4o / Claude 3.5 Sonnet
  流式输出:  Server-Sent Events (SSE)
  缓存:      Redis（搜索结果缓存）
```

**第 1 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **AI 搜索** | 联网搜索 + LLM 生成 = 直接给答案 |
| **6 步流程** | 改写→搜索→抓取→组装→生成→引用 |
| **Tavily** | 专为 AI 应用设计的搜索 API |

---

## 2. 联网搜索：接入搜索引擎 API

### 2.1 搜索 API 选型：Google / Bing / Tavily / SerpAPI

| API | 价格 | 特点 | 推荐度 |
|:---|:---|:---|:---|
| Tavily | 免费 1000 次/月 | 专为 AI 设计，直接返回干净内容 | ⭐⭐⭐⭐⭐ |
| Bing Search | $3/1000 次 | 微软官方，结果全面 | ⭐⭐⭐⭐ |
| SerpAPI | $50/月起 | 支持多种搜索引擎 | ⭐⭐⭐ |
| Google CSE | 免费 100 次/天 | 免费额度少 | ⭐⭐ |

### 2.2 Tavily 实战：最适合 AI 应用的搜索 API

```python
from tavily import TavilyClient
import os

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# 基础搜索
results = client.search(
    query="Python asyncio 最佳实践 2024",
    search_depth="advanced",       # basic 或 advanced（更深度）
    max_results=5,
    include_raw_content=True,      # 包含网页原始内容
)

for r in results["results"]:
    print(f"📄 {r['title']}")
    print(f"   URL: {r['url']}")
    print(f"   摘要: {r['content'][:100]}...")
    print(f"   相关度: {r['score']}")
```

```python
# 不用 SDK，直接用 httpx
import httpx

async def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": os.getenv("TAVILY_API_KEY"),
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_raw_content": True,
            },
            timeout=30,
        )
        data = resp.json()
        return data.get("results", [])
```

### 2.3 查询改写：让搜索结果更精准

```python
async def rewrite_query(user_question: str, chat_history: list = None) -> str:
    """用 LLM 将用户问题改写为搜索引擎友好的查询"""
    
    prompt = f"""将用户问题改写为适合搜索引擎的查询关键词。

规则：
- 提取核心关键词，去掉口语化表达
- 如果有时间要求，加上年份
- 输出纯关键词，不要完整句子

用户问题：{user_question}
搜索关键词："""
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",       # 用小模型就够了
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50,
    )
    return response.choices[0].message.content.strip()

# 示例
# "Python 的异步编程怎么学比较好？" → "Python asyncio 异步编程 教程 2024"
# "怎么用 Docker 部署 FastAPI？"   → "Docker FastAPI 部署 docker-compose"
```

### 2.4 搜索结果去重与排序

```python
from urllib.parse import urlparse

def deduplicate_results(results: list[dict]) -> list[dict]:
    """去重：同一域名只保留得分最高的结果"""
    seen_domains = {}
    for r in sorted(results, key=lambda x: x.get("score", 0), reverse=True):
        domain = urlparse(r["url"]).netloc
        if domain not in seen_domains:
            seen_domains[domain] = r
    return list(seen_domains.values())

def filter_results(results: list[dict], min_score: float = 0.5) -> list[dict]:
    """过滤低质量结果"""
    return [r for r in results if r.get("score", 0) >= min_score]
```

> 💡 **查询改写是 AI 搜索质量的关键**——直接拿用户的口语化问题去搜，结果往往不好。用小模型（GPT-4o-mini）做改写，成本极低但效果显著。

**第 2 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Tavily** | AI 搜索首选，直接返回干净内容 |
| **查询改写** | 口语问题→搜索关键词，用 GPT-4o-mini |
| **去重** | 同域名保留最高分结果 |

---

## 3. 网页内容提取：从 URL 到干净文本

### 3.1 网页抓取：httpx + 异步并发

```python
import httpx

async def fetch_page(url: str, timeout: int = 15) -> str | None:
    """抓取单个网页"""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AISearchBot/1.0)",
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        print(f"抓取失败 {url}: {e}")
        return None
```

### 3.2 HTML 转干净文本：Trafilatura 一键提取正文

```python
import trafilatura

def extract_content(html: str, url: str = None) -> dict | None:
    """从 HTML 中提取正文、标题"""
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_precision=True,         # 宁可少提取，也别提取到广告
    )
    if not text or len(text) < 100:   # 太短的内容没价值
        return None
    
    metadata = trafilatura.extract_metadata(html)
    return {
        "content": text,
        "title": metadata.title if metadata else "",
        "url": url,
    }
```

### 3.3 内容清洗：去噪声保留核心信息

```python
import re

def clean_content(text: str, max_length: int = 3000) -> str:
    """清洗提取的文本"""
    # 去掉连续空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 去掉多余空格
    text = re.sub(r' {2,}', ' ', text)
    # 去掉常见噪声
    noise_patterns = [
        r'Cookie.*?Policy',
        r'Subscribe.*?newsletter',
        r'Advertisement',
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    # 截断过长内容
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text.strip()
```

### 3.4 并发抓取：同时处理 10 个网页

```python
import asyncio

async def fetch_and_extract_all(urls: list[str], max_concurrent: int = 10) -> list[dict]:
    """并发抓取多个网页并提取内容"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_one(url: str) -> dict | None:
        async with semaphore:
            html = await fetch_page(url)
            if not html:
                return None
            result = extract_content(html, url)
            if result:
                result["content"] = clean_content(result["content"])
            return result
    
    tasks = [process_one(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]

# 使用
urls = [r["url"] for r in search_results]
pages = await fetch_and_extract_all(urls)
# 10 个网页并发抓取，通常 2-3 秒完成
```

> 💡 **Tavily 的 `include_raw_content=True` 已经帮你做了抓取和提取**——如果用 Tavily，可以跳过手动抓取。但了解手动实现的方法，在用 Bing API 等不提供内容的搜索 API 时很重要。

**第 3 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **Trafilatura** | 从 HTML 提取正文，自动去广告导航 |
| **并发抓取** | Semaphore 限流 + asyncio.gather 并行 |
| **内容截断** | 每个网页最多 3000 字，避免 Context 爆炸 |

---

## 4. RAG 增强：将搜索结果喂给大模型

### 4.1 搜索结果分块与截断策略

```python
def prepare_sources(pages: list[dict], max_total: int = 12000) -> list[dict]:
    """准备搜索结果作为 Context，控制总长度"""
    sources = []
    total_length = 0
    
    for i, page in enumerate(pages):
        content = page["content"]
        remaining = max_total - total_length
        
        if remaining <= 0:
            break
        
        # 截断单个来源
        if len(content) > remaining:
            content = content[:remaining] + "..."
        
        sources.append({
            "index": i + 1,
            "title": page["title"],
            "url": page["url"],
            "content": content,
        })
        total_length += len(content)
    
    return sources
```

### 4.2 Context 组装：把多个网页塞进 Prompt

```python
def build_context(sources: list[dict]) -> str:
    """将搜索结果组装为 Context 文本"""
    context_parts = []
    for s in sources:
        context_parts.append(
            f"[来源 {s['index']}] {s['title']}\n"
            f"URL: {s['url']}\n"
            f"内容:\n{s['content']}\n"
        )
    return "\n---\n".join(context_parts)
```

### 4.3 相关性排序：优先使用最相关的内容

::: v-pre
```python
async def rerank_sources(query: str, sources: list[dict]) -> list[dict]:
    """用 LLM 对搜索结果进行相关性重排"""
    
    prompt = f"""对以下搜索结果按与问题的相关性打分（1-10 分）。
    
问题：{query}

搜索结果：
{chr(10).join(f"[{s['index']}] {s['title']}: {s['content'][:200]}" for s in sources)}

按 JSON 格式输出：[&#123;&#123;"index": 1, "score": 8&#125;&#125;, ...]"""
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    
    scores = json.loads(response.choices[0].message.content)
    # 按分数重新排序
    score_map = {s["index"]: s["score"] for s in scores}
    return sorted(sources, key=lambda s: score_map.get(s["index"], 0), reverse=True)
```
:::

### 4.4 Prompt 设计：基于证据回答 + 引用标注

```python
SEARCH_ANSWER_PROMPT = """你是一个 AI 搜索助手。基于提供的搜索结果回答用户问题。

规则：
1. 只使用搜索结果中的信息回答，不要编造
2. 每个关键论述后用 [1][2] 标注来源编号
3. 如果搜索结果无法回答，明确说"搜索结果中未找到相关信息"
4. 用中文回答，条理清晰
5. 如果有多个来源给出不同信息，都列出来并说明差异

搜索结果：
{context}

用户问题：{question}"""
```

> 💡 **Prompt 中的引用规则是 AI 搜索的灵魂**——没有引用标注，AI 搜索就退化成了"联网聊天"，用户无法验证信息的真实性。

**第 4 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **长度控制** | 总 Context 控制在 12000 字以内 |
| **Rerank** | 用小模型对搜索结果重排，最相关的放前面 |
| **引用标注** | `[1][2]` 让每句话都有出处 |

---

## 5. 答案生成与引用溯源

### 5.1 流式答案生成：边搜边答的体验

```python
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def generate_answer_stream(question: str, sources: list[dict]):
    """流式生成答案"""
    context = build_context(sources)
    prompt = SEARCH_ANSWER_PROMPT.format(context=context, question=question)
    
    stream = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        temperature=0.1,           # 低温度，更忠实于搜索结果
    )
    
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
```

### 5.2 内联引用标注：让每句话都有出处

```python
import re

def parse_citations(answer: str, sources: list[dict]) -> dict:
    """解析答案中的引用标注"""
    # 提取所有引用编号 [1], [2], [1][3]
    citation_pattern = r'\[(\d+)\]'
    cited_indices = set(int(m) for m in re.findall(citation_pattern, answer))
    
    # 构建引用列表
    citations = []
    for idx in sorted(cited_indices):
        source = next((s for s in sources if s["index"] == idx), None)
        if source:
            citations.append({
                "index": idx,
                "title": source["title"],
                "url": source["url"],
                "snippet": source["content"][:150] + "...",
            })
    
    return {"answer": answer, "citations": citations}
```

### 5.3 引用来源卡片：展示标题、URL 和摘要

```python
def format_sources_display(citations: list[dict]) -> str:
    """格式化引用来源展示"""
    lines = ["\n---\n📚 **参考来源：**\n"]
    for c in citations:
        lines.append(f"[{c['index']}] [{c['title']}]({c['url']})")
        lines.append(f"   {c['snippet']}\n")
    return "\n".join(lines)
```

### 5.4 答案质量控制：防幻觉、防过时信息

| 策略 | 实现方式 |
|:---|:---|
| 低温度 | `temperature=0.1` 减少创造性 |
| 强制引用 | Prompt 中要求每个论述标注来源 |
| 无答案检测 | 搜索结果无关时明确告知用户 |
| 时效标注 | 显示来源的发布日期 |
| 多源交叉 | 多个来源说同一件事 → 可信度高 |

> 💡 **AI 搜索的质量核心是"忠实于搜索结果"**——`temperature=0.1` + 强制引用规则 + 无答案检测，三者缺一不可。

**第 5 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **流式生成** | 边搜边答，用户体验好 |
| **引用解析** | 正则提取 `[1][2]`，关联到来源 |
| **防幻觉** | 低温度 + 强制引用 + 无答案检测 |

---

## 6. 追问与多轮对话

### 6.1 追问检测：需要重新搜索吗？

```python
async def need_new_search(question: str, history: list[dict], sources: list[dict]) -> bool:
    """判断追问是否需要重新搜索"""
    prompt = f"""根据对话历史和已有搜索结果，判断用户的新问题是否需要重新搜索。

已有搜索结果的主题：{', '.join(s['title'] for s in sources[:3])}

对话历史：
{chr(10).join(f"{m['role']}: {m['content'][:100]}" for m in history[-4:])}

用户新问题：{question}

回答 YES（需要重新搜索）或 NO（已有信息足够回答）。"""
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=5,
    )
    return "YES" in response.choices[0].message.content.upper()
```

### 6.2 对话历史管理：多轮搜索的上下文

```python
class SearchSession:
    """管理一次搜索会话的多轮对话"""
    
    def __init__(self):
        self.history: list[dict] = []
        self.all_sources: list[dict] = []  # 累积所有搜索结果
    
    async def ask(self, question: str) -> str:
        # 判断是否需要新搜索
        if not self.all_sources or await need_new_search(question, self.history, self.all_sources):
            # 执行新搜索
            query = await rewrite_query(question, self.history)
            results = await tavily_search(query)
            new_sources = prepare_sources(results)
            self.all_sources.extend(new_sources)
        
        # 用所有累积的搜索结果生成答案
        answer = await generate_answer(question, self.all_sources, self.history)
        
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": answer})
        
        return answer
```

### 6.3 相关问题推荐：自动生成追问建议

```python
async def suggest_followups(question: str, answer: str) -> list[str]:
    """基于问答生成追问建议"""
    prompt = f"""基于以下问答，生成 3 个用户可能想继续追问的问题。

问题：{question}
回答：{answer[:500]}

要求：
- 问题要有价值，不是简单重复
- 从不同角度提问
- 用中文

输出格式（每行一个）："""
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    
    lines = response.choices[0].message.content.strip().split("\n")
    return [line.strip().lstrip("0123456789.-) ") for line in lines if line.strip()][:3]
```

### 6.4 搜索结果缓存：避免重复搜索

```python
import hashlib
import json
from functools import lru_cache

# 简单内存缓存
_search_cache: dict[str, list[dict]] = {}

async def cached_search(query: str, max_results: int = 5) -> list[dict]:
    cache_key = hashlib.md5(query.encode()).hexdigest()
    
    if cache_key in _search_cache:
        return _search_cache[cache_key]
    
    results = await tavily_search(query, max_results)
    _search_cache[cache_key] = results
    return results
```

> 💡 **追问不一定需要重新搜索**——"解释一下第三点"这种追问用已有结果就能回答。用小模型判断是否需要新搜索，节省 API 调用。

**第 6 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **追问检测** | 小模型判断 YES/NO，决定是否重新搜索 |
| **累积来源** | 多轮搜索结果合并，信息越来越丰富 |
| **推荐追问** | 自动生成 3 个有价值的追问建议 |

---

## 7. 完整实现：FastAPI + 前端 Demo

### 7.1 后端 API 设计：SSE 流式搜索接口

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

app = FastAPI()

class SearchRequest(BaseModel):
    query: str
    session_id: str | None = None

@app.post("/api/search")
async def search(req: SearchRequest):
    """SSE 流式搜索接口"""
    async def event_stream():
        # 1. 查询改写
        yield f"data: {json.dumps({'type': 'status', 'message': '正在分析问题...'})}\n\n"
        search_query = await rewrite_query(req.query)
        
        # 2. 联网搜索
        yield f"data: {json.dumps({'type': 'status', 'message': '正在搜索...'})}\n\n"
        results = await tavily_search(search_query)
        
        # 3. 发送搜索结果来源
        sources = prepare_sources(results)
        yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"
        
        # 4. 流式生成答案
        yield f"data: {json.dumps({'type': 'status', 'message': '正在生成答案...'})}\n\n"
        async for chunk in generate_answer_stream(req.query, sources):
            yield f"data: {json.dumps({'type': 'answer', 'content': chunk})}\n\n"
        
        # 5. 推荐追问
        # （收集完整答案后生成）
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### 7.2 完整流水线：从用户提问到最终答案

```python
async def search_pipeline(question: str) -> dict:
    """完整的搜索流水线（非流式版本）"""
    
    # Step 1: 查询改写
    search_query = await rewrite_query(question)
    
    # Step 2: 联网搜索
    results = await tavily_search(search_query, max_results=8)
    results = deduplicate_results(results)
    
    # Step 3: 内容提取（如果 Tavily 没返回内容）
    urls_without_content = [r["url"] for r in results if not r.get("raw_content")]
    if urls_without_content:
        pages = await fetch_and_extract_all(urls_without_content)
        # 合并内容...
    
    # Step 4: 准备 Context
    sources = prepare_sources(results)
    
    # Step 5: 生成答案
    answer = await generate_answer(question, sources)
    
    # Step 6: 解析引用
    result = parse_citations(answer, sources)
    
    # Step 7: 推荐追问
    followups = await suggest_followups(question, answer)
    result["followups"] = followups
    
    return result
```

### 7.3 前端 Demo：极简搜索界面

```html
<!DOCTYPE html>
<html>
<head>
    <title>AI 搜索</title>
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 0 auto; padding: 20px; }
        #answer { white-space: pre-wrap; line-height: 1.8; }
        .source { background: #f5f5f5; padding: 10px; margin: 5px 0; border-radius: 8px; }
    </style>
</head>
<body>
    <h1>🔍 AI 搜索</h1>
    <input id="query" placeholder="输入你的问题..." style="width: 100%; padding: 12px; font-size: 16px;">
    <button onclick="search()">搜索</button>
    <div id="status"></div>
    <div id="answer"></div>
    <div id="sources"></div>

    <script>
    async function search() {
        const query = document.getElementById('query').value;
        const answerDiv = document.getElementById('answer');
        answerDiv.textContent = '';
        
        const resp = await fetch('/api/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query}),
        });
        
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            const lines = decoder.decode(value).split('\n');
            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'answer') {
                    answerDiv.textContent += data.content;
                } else if (data.type === 'status') {
                    document.getElementById('status').textContent = data.message;
                }
            }
        }
    }
    </script>
</body>
</html>
```

### 7.4 性能优化：并行搜索 + 流式生成

```python
import asyncio

async def optimized_search(question: str):
    """优化：搜索和改写并行"""
    # 同时执行查询改写和直接搜索
    rewrite_task = rewrite_query(question)
    direct_task = tavily_search(question, max_results=3)
    
    rewritten_query, direct_results = await asyncio.gather(rewrite_task, direct_task)
    
    # 用改写后的查询再搜一次
    rewrite_results = await tavily_search(rewritten_query, max_results=5)
    
    # 合并去重
    all_results = deduplicate_results(direct_results + rewrite_results)
    return all_results
```

**第 7 章核心知识回顾：**

| 概念 | 一句话解释 |
|:---|:---|
| **SSE 接口** | `/api/search` 流式返回状态/来源/答案 |
| **事件类型** | status/sources/answer/done 四类事件 |
| **并行优化** | 改写和直接搜索同时进行 |

---

## 8. 进阶：Pro 搜索与深度研究

### 8.1 Pro 搜索：多次搜索 + 交叉验证

```python
async def pro_search(question: str) -> dict:
    """Pro 模式：从多个角度搜索，交叉验证"""
    
    # 1. 生成多个搜索角度
    angles = await generate_search_angles(question)
    # ["Python asyncio 性能优化", "asyncio vs threading 对比", "asyncio 生产最佳实践"]
    
    # 2. 并行搜索所有角度
    all_results = []
    tasks = [tavily_search(angle, max_results=3) for angle in angles]
    results_list = await asyncio.gather(*tasks)
    for results in results_list:
        all_results.extend(results)
    
    # 3. 去重 + Rerank
    all_results = deduplicate_results(all_results)
    sources = prepare_sources(all_results, max_total=20000)
    sources = await rerank_sources(question, sources)
    
    # 4. 生成综合答案
    answer = await generate_answer(question, sources[:8])
    return parse_citations(answer, sources)
```

### 8.2 深度研究模式：多步推理生成报告

```python
async def deep_research(question: str) -> str:
    """深度研究：多步搜索 + 长报告生成"""
    
    # 1. 生成研究大纲
    outline = await generate_research_outline(question)
    # ["1. 背景介绍", "2. 技术原理", "3. 实践案例", "4. 对比分析"]
    
    # 2. 逐个章节搜索+生成
    report_parts = []
    for section in outline:
        query = f"{question} {section}"
        results = await tavily_search(query, max_results=5)
        sources = prepare_sources(results)
        section_content = await generate_section(section, sources)
        report_parts.append(section_content)
    
    # 3. 整合为完整报告
    report = await synthesize_report(question, report_parts)
    return report
```

### 8.3 混合搜索：本地知识库 + 联网搜索

```python
async def hybrid_search(question: str, local_db=None) -> dict:
    """混合搜索：优先查本地，不够再联网"""
    
    # 1. 先查本地知识库
    local_results = await local_db.search(question, top_k=3) if local_db else []
    
    # 2. 判断本地结果是否足够
    if local_results and max(r["score"] for r in local_results) > 0.85:
        sources = prepare_sources(local_results)
        answer = await generate_answer(question, sources)
        return {"answer": answer, "source_type": "local"}
    
    # 3. 不够就联网搜索
    web_results = await tavily_search(question)
    all_results = local_results + web_results
    sources = prepare_sources(all_results)
    answer = await generate_answer(question, sources)
    return {"answer": answer, "source_type": "hybrid"}
```

### 8.4 搜索质量评测与持续优化

| 评测维度 | 指标 | 方法 |
|:---|:---|:---|
| 答案准确性 | 事实正确率 | 人工标注 + LLM 评测 |
| 引用质量 | 引用覆盖率 | 每个关键论述是否都有引用 |
| 搜索相关性 | NDCG | 搜索结果与问题的相关度排序 |
| 响应速度 | P95 延迟 | 从提问到第一个字输出的时间 |
| 用户满意度 | 点赞/踩 | 用户反馈收集 |

---

## 附录：AI 搜索引擎速查手册

### A.1 搜索 API 对比表

| API | 月免费额度 | 返回内容 | 延迟 | 推荐场景 |
|:---|:---|:---|:---|:---|
| Tavily | 1000 次 | 摘要+正文 | ~2s | AI 应用首选 |
| Bing API | 1000 次 | 摘要+URL | ~1s | 需要自己抓取 |
| SerpAPI | 100 次 | 搜索结果页 | ~3s | 多引擎支持 |
| Google CSE | 100 次/天 | 摘要+URL | ~1s | 免费但额度少 |

### A.2 网页内容提取工具对比

| 工具 | 特点 | 安装 |
|:---|:---|:---|
| Trafilatura | 精准提取正文，推荐 | `pip install trafilatura` |
| BeautifulSoup | 通用 HTML 解析 | `pip install beautifulsoup4` |
| newspaper3k | 新闻文章提取 | `pip install newspaper3k` |
| readability-lxml | Mozilla 的算法移植 | `pip install readability-lxml` |

### A.3 核心 Prompt 模板

```python
# 查询改写 Prompt
REWRITE_PROMPT = "将用户问题改写为搜索引擎友好的关键词..."

# 答案生成 Prompt
ANSWER_PROMPT = "基于搜索结果回答，每个论述标注引用 [1][2]..."

# 追问检测 Prompt
FOLLOWUP_PROMPT = "判断追问是否需要重新搜索，回答 YES/NO..."

# 追问推荐 Prompt
SUGGEST_PROMPT = "生成 3 个有价值的追问建议..."
```

### A.4 完整架构图与数据流

```
完整数据流：

  用户提问
    │
    ├─→ 查询改写（GPT-4o-mini）
    │     │
    │     ├─→ Tavily 搜索 ─→ 搜索结果(URL+摘要+正文)
    │     │                      │
    │     │                      ├─→ 去重 + 过滤
    │     │                      │
    │     │                      ├─→ Rerank（可选）
    │     │                      │
    │     │                      ├─→ Context 组装
    │     │                           │
    │     │                           ├─→ 答案生成（GPT-4o 流式）
    │     │                                 │
    │     │                                 ├─→ 引用解析
    │     │                                 │
    │     │                                 ├─→ 来源卡片
    │     │                                 │
    │     │                                 └─→ 追问推荐
    │
    └─→ SSE 流式返回前端
```
