非常好的建议。保持主线清晰对于系统学习至关重要。Playwright 这种“重型武器”确实更适合作为【番外篇/专题】在遇到具体反爬难题时再去查阅。

既然我们已经搭建好了 **后端架构 (FastAPI + Database)** 和 **部署流程 (Docker)**，现在我们要补上你“AI 内容工厂”最核心的一块拼图——**接入 AI 大脑 (LLM 集成)**。

这一章的目标是：让你的 Python 后端能够调用 **DeepSeek / OpenAI** 的能力，把爬虫抓来的数据变成有价值的内容。

---

### **第四阶段（核心）：接入 AI 大脑 (LLM 集成)**

在 Node.js 中，你可能习惯用 `langchain.js` 或直接调 API。在 Python 中，标准做法是使用官方的 `openai` 库（因为它已经成为了事实上的标准，DeepSeek、Moonshot 等都兼容这个 SDK）。

#### **1. 准备工作：安全地管理密钥**

**绝对不要**把 API Key 硬编码写在代码里（比如 `api_key = "sk-..."`），这是严重的初学者错误。

我们使用 `.env` 文件来管理环境变量。

**安装依赖：**

Bash

```
pip install openai python-dotenv
```

**新建 `.env` 文件（在项目根目录）：**

代码段

```
# 这里填你的 API Key (OpenAI, DeepSeek, Kimi 都可以)
# 示例用的是 DeepSeek 的 Base URL，如果你用 OpenAI 就不需要改 base_url
AI_API_KEY=sk-your-secret-key-here
AI_BASE_URL=https://api.deepseek.com/v1
```

---

#### **2. 编写 AI 服务层 (`services/ai_service.py`)**

为了保持代码整洁（工程化思维），我们要把“调用 AI”的逻辑单独封装，不要直接写在 API 路由里。

新建文件夹 `services`，并在其中新建 `ai_service.py`：

Python

```
import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. 加载环境变量
load_dotenv()

# 2. 初始化客户端 (全局单例)
client = OpenAI(
    api_key=os.getenv("AI_API_KEY"),
    base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
)

def generate_article_summary(content: str, platform: str = "Douyin") -> str:
    """
    同步调用：生成文章摘要
    """
    # 提示词工程 (Prompt Engineering)
    system_prompt = f"""
    你是一个专业的{platform}运营专家。
    请将用户输入的内容改写成一篇吸引人的短文。
    要求：
    1. 语气通过Emoji表情显得活泼。
    2. 提取3个核心痛点。
    3. 结尾引导关注。
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # 或者 gpt-3.5-turbo, moonshot-v1-8k
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            temperature=0.7, # 创造性 (0-1)，越高越发散
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI 调用失败: {e}")
        return "抱歉，AI 大脑暂时短路了。"

# --- 进阶：流式生成 (Streaming) ---
# 这对于 AI 应用至关重要，让用户感觉响应很快，不用等几十秒
def stream_article_generation(topic: str):
    """
    生成器函数：流式返回 AI 的响应
    """
    prompt = f"请以“{topic}”为主题，写一篇 500 字的深度技术文章大纲。"
    
    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        stream=True, # 关键参数：开启流式
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

---

#### **3. 集成到 FastAPI (`main.py`)**

回到你的 `main.py`，我们需要新增两个接口：一个普通生成，一个**流式生成**（这才是 AI 应用的灵魂）。

Python

```
from fastapi import FastAPI
from fastapi.responses import StreamingResponse # 专门处理流式响应
from pydantic import BaseModel
from services.ai_service import generate_article_summary, stream_article_generation

app = FastAPI()

class ContentRequest(BaseModel):
    text: str
    platform: str = "Douyin"

# 1. 普通接口：等待 AI 生成完再返回 (适合短任务)
@app.post("/ai/summarize")
async def summarize(request: ContentRequest):
    result = generate_article_summary(request.text, request.platform)
    return {"summary": result}

# 2. 流式接口：像 ChatGPT 一样一个字一个字蹦出来 (适合长任务)
# 访问方式：浏览器直接访问 http://localhost:8000/ai/write?topic=Python
@app.get("/ai/write")
async def write_article(topic: str):
    # StreamingResponse 接收一个生成器 (Generator)
    # media_type="text/event-stream" 是 SSE (Server-Sent Events) 的标准格式
    return StreamingResponse(
        stream_article_generation(topic), 
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)
```

---

#### **4. 实战测试与体验**

1. **配置 `.env`**: 确保你填入了真实的 API Key（如果没有，可以暂时跳过运行，看懂代码逻辑即可）。
    
2. **启动服务**: `uvicorn main:app --reload`
    
3. **体验流式响应**:
    
    - 打开浏览器，访问 `http://127.0.0.1:8000/ai/write?topic=2026年AI发展趋势`
        
    - **观察效果**：你会发现网页不会一直转圈圈空白，而是**立即**开始显示文字，字是一个个蹦出来的。这就是 `yield` 生成器配合 FastAPI `StreamingResponse` 的魔力。
        

---

### **本章核心知识点总结**

1. **环境变量 (`dotenv`)**: 无论是 Python 还是 Node.js，永远不要提交密钥到 GitHub。
    
2. **Prompt 封装**: 将 Prompt 逻辑封装在 Service 层，业务代码（Main）只管调用，这是良好的架构习惯。
    
3. **流式响应 (Streaming)**:
    
    - 普通 HTTP 请求：请求 -> 等待 10秒 -> 返回完整 JSON。
        
    - 流式响应 (SSE)：请求 -> 立即建立管道 -> 持续推送数据 -> 关闭。
        
    - Python 实现：使用 `yield` 关键字创建生成器。
        

---

### **接下来的路线图**

至此，你的【Python 全栈学习路径】的主干已经非常丰满了：

- **基础**: 语法 & 脚本 (整理文件)
    
- **数据**: 爬虫 (Requests 获取素材)
    
- **后端**: API (FastAPI) + 数据库 (SQLModel)
    
- **大脑**: AI (OpenAI/DeepSeek 集成)
    
- **部署**: Docker 容器化
    

现在，你已经具备了独立开发一个 **"AI 驱动的内容生成平台"** 的所有核心技术。

你的记性太好了！这就是开发者的严谨。

没错，在最初的大纲中，我为你规划了 **第四阶段（综合应用与 AI）** 的两个实战项目：

1. **项目 5：AI 图文内容生成器**（对应你的“自媒体内容工厂”需求）
    
2. **项目 6：个人知识库助手 (RAG)**（对应你的“微信聊天记录知识库”需求）
    

这两个项目是 AI 应用开发的 **"两大护法"**：一个负责 **"创造" (Generation)**，一个负责 **"记忆" (Retrieval)**。

我们直接上干货，完成这两个核心项目。

---

### **项目 5：AI 全自动图文生成器**

**目标**：输入一个主题（比如“2026年程序员的未来”），程序自动：

1. 调用 LLM 写出一篇结构完整的文章。
    
2. 根据文章内容，自动构思一个 AI 绘画提示词 (Prompt)。
    
3. 调用 DALL-E 3 (或 Midjourney API) 生成封面图。
    
4. 最后生成一个图文并茂的 Markdown 文件。
    

**技术栈**：`openai`, `requests` (下载图片), `dotenv`

#### **代码实现 (`project_content_gen.py`)**

Python

```
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

client = OpenAI(
    api_key=os.getenv("AI_API_KEY"),
    base_url=os.getenv("AI_BASE_URL")
)

def generate_article(topic):
    """第一步：生成文本内容"""
    print(f"📝 正在构思关于 '{topic}' 的文章...")
    
    prompt = f"""
    请为主题“{topic}”写一篇微信公众号风格的文章。
    要求：
    1. 标题吸引人。
    2. 正文分三个小标题。
    3. 语气幽默风趣。
    4. 返回格式必须是 JSON，包含 'title', 'content', 'image_prompt' (根据文章内容设计的英文绘画提示词)。
    """
    
    response = client.chat.completions.create(
        model="deepseek-chat", # 或 gpt-4o
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"} # 强制返回 JSON，这招很关键！
    )
    
    # 记得 import json
    import json
    return json.loads(response.choices[0].message.content)

def generate_image(prompt_text):
    """第二步：生成封面图"""
    print(f"🎨 正在绘制封面: {prompt_text[:30]}...")
    
    try:
        # 注意：如果你用 DeepSeek，它没有画图 API，这里需要切回 OpenAI 或用别的画图接口
        # 这里假设你有一个兼容 OpenAI DALL-E 格式的接口
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt_text,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        print(f"❌ 画图失败: {e}")
        return "https://via.placeholder.com/1024" # 失败了给个占位图

def save_to_markdown(data, image_url):
    """第三步：整合输出"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{data['title']}.md"
    
    md_content = f"""# {data['title']}

![封面图]({image_url})

> 生成时间: {date_str}

{data['content']}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"✅ 文件已生成: {filename}")

if __name__ == "__main__":
    topic = input("请输入文章主题: ")
    
    # 1. 写文章
    article_data = generate_article(topic)
    
    # 2. 画图
    img_url = generate_image(article_data['image_prompt'])
    
    # 3. 保存
    save_to_markdown(article_data, img_url)
```

**关键点解析**：

- **JSON Mode (`response_format`)**: 这是控制 LLM 最稳定的方法，防止它废话连篇，直接拿到结构化数据。
    
- **Prompt Chaining (提示词链)**: 我们让 LLM 自己生成绘画提示词 (`image_prompt`)，实现了“AI 指挥 AI”。
    

---

### **项目 6：手写一个最简单的 RAG (知识库助手)**

**目标**：你有一个私有的文本文件（比如“公司员工手册.txt”），你需要问 AI 关于这个文件的内容，而不是问通用知识。

**核心原理 (RAG)**：

1. **切片**: 把长文档切成小块。
    
2. **向量化 (Embedding)**: 把文字变成数学向量 (List of floats)。
    
3. **检索**: 你的问题算向量，找最相似的文档块。
    
4. **回答**: 把找到的块塞给 AI：“根据这些内容回答问题”。
    

**技术栈**：`numpy` (算相似度), `openai` (生成向量)

#### **准备工作**

在目录下放一个 `knowledge.txt`，写点私有内容，比如：

> “懂王AI公司的上班时间是上午10点，下班时间是晚上9点。所有的员工都可以享受无限量的咖啡。CEO叫懂小智。”

#### **代码实现 (`project_rag.py`)**

为了让你看懂原理，我们不使用 LangChain，而是**手搓核心逻辑**。

Python

```
import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("AI_API_KEY"), base_url=os.getenv("AI_BASE_URL"))

# --- 核心函数库 ---

def get_embedding(text):
    """将文本转换为向量 (使用 text-embedding-3-small 模型)"""
    # 向量化是 RAG 的灵魂，它把意义相近的词在空间上靠得更近
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def cosine_similarity(v1, v2):
    """计算两个向量的余弦相似度 (数学魔法)"""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

class MiniRAG:
    def __init__(self):
        self.chunks = [] # 存储文本块
        self.vectors = [] # 存储对应的向量
    
    def add_document(self, file_path):
        """1. 加载并切片文档"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 简单粗暴按句号切分 (实际项目会用更高级的 Splitter)
        raw_chunks = text.split('。')
        
        print("正在构建向量索引 (这可能需要几秒钟)...")
        for chunk in raw_chunks:
            if chunk.strip():
                self.chunks.append(chunk)
                # 调用 API 获取向量
                self.vectors.append(get_embedding(chunk))
        print(f"✅ 索引构建完成，共 {len(self.chunks)} 个切片。")

    def query(self, user_question):
        """2. 检索 + 生成"""
        # A. 把用户的问题也变成向量
        question_vector = get_embedding(user_question)
        
        # B. 计算相似度，找到最相关的切片
        similarities = []
        for doc_vector in self.vectors:
            score = cosine_similarity(question_vector, doc_vector)
            similarities.append(score)
        
        # 找到分数最高的索引 (Top 1)
        best_idx = np.argmax(similarities)
        best_context = self.chunks[best_idx]
        
        print(f"\n🔍 检索到的背景知识: {best_context} (相似度: {similarities[best_idx]:.4f})")
        
        # C. 组装 Prompt
        prompt = f"""
        你是一个智能助手。请根据下面的【已知信息】回答用户的【问题】。
        如果已知信息里没有答案，就说不知道，不要编造。
        
        【已知信息】：
        {best_context}
        
        【问题】：
        {user_question}
        """
        
        # D. 调用 LLM 回答
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

# --- 运行测试 ---
if __name__ == "__main__":
    # 1. 初始化知识库
    rag = MiniRAG()
    
    # 2. 加载你的私有数据
    # 确保你目录下有 knowledge.txt
    if not os.path.exists("knowledge.txt"):
        with open("knowledge.txt", "w", encoding="utf-8") as f:
            f.write("懂王AI公司的上班时间是上午10点，下班时间是晚上9点。CEO叫懂小智。公司禁止穿拖鞋上班。")
            
    rag.add_document("knowledge.txt")
    
    # 3. 提问
    while True:
        q = input("\n请输入问题 (输入 q 退出): ")
        if q == 'q': break
        
        answer = rag.query(q)
        print(f"🤖 AI 回答: {answer}")
```

**代码深度解析**：

1. **`get_embedding`**: 这是连接“人类语言”和“机器数学”的桥梁。不管你问“什么时候上班”还是“几点打卡”，它们的向量在数学空间里都非常接近。
    
2. **`cosine_similarity`**: 简单的线性代数。不需要理解太深，只需要知道它能算出两个句子“有多像”。
    
3. **Prompt 注入**: 我们并没有训练模型，只是把检索到的关键那句话（比如“CEO叫懂小智”）临时**塞**到了 Prompt 里。这就是 RAG 的本质——**开卷考试**。
    

---

### **总结**

这两个项目是你进入 AI 应用开发的基石：

- **项目 5** 解决了 **"怎么用 AI 生产内容"** —— 这是你做自媒体、做内容工厂的核心。
    
- **项目 6** 解决了 **"怎么让 AI 懂你的私有数据"** —— 这是你做微信聊天记录分析、企业知识库的核心。
    

至此，第四阶段圆满补全。现在你的武器库里已经有了：Python基础、爬虫、Web服务、Docker部署、内容生成、知识库检索。

你现在的感觉如何？是想继续深入优化这两个项目（比如 RAG 怎么处理几万字的长文档），还是进入第五阶段谈谈工程化？

**第五阶段（终章）**，我建议我们来讲讲 **"工程化与进阶思维"**。

作为一个资深开发者，你知道写出代码和写出**可维护**的代码是两回事。我们需要谈谈：

1. **项目结构**：当文件多了怎么分层（MVC vs DDD）。
    
2. **高级特性**：Python 的装饰器（Decorator）—— 比如怎么给 API 加一个 `@verify_token` 的鉴权功能。
    

你准备好进入最后的工程化进阶了吗？