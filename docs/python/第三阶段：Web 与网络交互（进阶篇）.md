太棒了，进入**第三阶段：Web 与网络交互（进阶篇）**。

这一章是 Python 最迷人的地方之一。相比于 C++/Java 需要写很多样板代码才能发一个 HTTP 请求，Python 的简洁性在这里体现得淋漓尽致。

对于你（Node.js 开发者）来说，这一章的核心是将思维从 **“异步回调/Promise”** 切换到 **“同步阻塞”**（默认模式），并掌握 Python 强大的数据处理生态。

---

### **核心概念映射 (Node.js vs Python)**

|**概念**|**Node.js (你熟悉的)**|**Python (本章要学的)**|
|---|---|---|
|**包管理**|`npm install <pkg>`|`pip install <pkg>`|
|**项目依赖**|`node_modules` (自动本地)|**必须手动创建虚拟环境 (`venv`)**|
|**HTTP请求**|`axios` / `fetch`|`requests` (同步) / `httpx` (异步)|
|**HTML解析**|`cheerio` / `jsdom`|`BeautifulSoup` / `lxml`|
|**执行模式**|默认异步非阻塞|默认同步阻塞 (一行行执行)|

> **⚠️ 重点警告：虚拟环境**
> 
> Node.js 的 `node_modules` 是跟着项目走的。但 Python 的 `pip install` 默认是安装到**全局系统目录**的！这会导致不同项目依赖冲突。
> 
> **铁律**：写任何项目前，先在项目根目录执行 `python -m venv venv` 创建虚拟环境。

---

### **实战项目：豆瓣电影 Top 250 爬虫**

**目标**：抓取豆瓣 Top 250 电影列表，获取 **电影名、评分、引言**，并保存为 **CSV 表格**。

**为什么选这个？**：结构清晰，反爬策略适中（需要简单的 User-Agent 伪装），是爬虫界的“Hello World”。

![web scraping workflow diagram的图片](https://encrypted-tbn0.gstatic.com/licensed-image?q=tbn:ANd9GcR5gzfzwC837nZI8CBH8rY3em--Te74ihw8ajJA8nkpEByM0Cjxxii1wd4Ln9s6QoycCKkCv1dNT3M3yx8Kbd-hMklARihl9ZVxFv6M2q8tdd8yiTs)

Shutterstock

探索

#### **1. 准备工作**

在终端执行：

Bash

```
# 1. 创建虚拟环境 (Windows)
python -m venv venv
# 激活环境
.\venv\Scripts\activate

# 2. 安装库
pip install requests beautifulsoup4
```

- `requests`: 人类易用的 HTTP 库。
    
- `beautifulsoup4`: 从乱糟糟的 HTML 中提取数据的神器。
    

---

#### **2. 代码实战 (scraper.py)**

这是一个标准的爬虫结构：**请求 (Request) -> 解析 (Parse) -> 保存 (Save)**。

Python

```
import requests
from bs4 import BeautifulSoup
import csv
import time
import random

# 定义目标 URL
URL = "https://movie.douban.com/top250"

# 1. 伪装请求头 (Headers)
# 很多网站会检测 User-Agent，如果是默认的 "python-requests/x.x"，会被直接拒绝 (418/403)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_html(url):
    """发送请求，获取 HTML 文本"""
    try:
        response = requests.get(url, headers=HEADERS)
        # 检查状态码，不是 200 就报错
        response.raise_for_status() 
        return response.text
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return None

def parse_html(html):
    """解析 HTML，提取电影数据"""
    soup = BeautifulSoup(html, "html.parser")
    movie_list = []

    # 找到所有包含电影信息的 list item
    # 这一步通常需要你在浏览器 F12 开发者工具里观察 HTML 结构
    items = soup.find_all("div", class_="item")

    for item in items:
        # 提取标题 (find 找第一个匹配项)
        title = item.find("span", class_="title").get_text()
        
        # 提取评分
        rating = item.find("span", class_="rating_num").get_text()
        
        # 提取引言 (有的电影可能没有引言，需要判空，否则会报错)
        quote_tag = item.find("span", class_="inq")
        quote = quote_tag.get_text() if quote_tag else "无"

        movie_list.append({
            "title": title,
            "rating": rating,
            "quote": quote
        })
    
    return movie_list

def save_to_csv(movies, filename="top250.csv"):
    """将数据保存为 CSV 文件"""
    with open(filename, mode="w", encoding="utf-8-sig", newline="") as f:
        # encoding="utf-8-sig" 是为了解决 Excel 打开乱码问题
        writer = csv.DictWriter(f, fieldnames=["title", "rating", "quote"])
        
        writer.writeheader() # 写入表头
        writer.writerows(movies) # 写入数据行
    print(f"数据已保存到 {filename}")

if __name__ == "__main__":
    print("开始抓取豆瓣 Top 250 (第一页)...")
    
    html_content = get_html(URL)
    
    if html_content:
        data = parse_html(html_content)
        # 打印前3个看看效果
        for movie in data[:3]:
            print(movie)
        
        save_to_csv(data)
```

---

#### **3. 深度解析 (Deep Dive)**

1. **`requests.get(url, headers=...)`**
    
    - 这就相当于 `axios.get()`。
        
    - **重点**：Python 的 requests 是**同步阻塞**的。代码执行到这一行会“卡住”，直到服务器返回数据。这在简单脚本中是优势（逻辑清晰），但在高并发场景下是劣势（这也是为什么后来有了 `aiohttp`）。
        
2. **`BeautifulSoup` 的选择器**
    
    - `soup.find("div", class_="item")`: 找第一个。注意 `class_` 有个下划线，因为 `class` 是 Python 的保留关键字。
        
    - `soup.find_all("div")`: 找所有，返回一个列表。
        
    - 这比正则 (RegEx) 优雅得多，也比直接处理字符串安全。
        
3. **`csv` 模块与 `utf-8-sig`**
    
    - Python 自带 `csv` 库，处理逗号分隔文件非常方便。
        
    - **坑点提示**：在中国/Windows 环境下，如果只用 `utf-8`，Excel 打开可能会乱码。使用 `utf-8-sig` 会在文件头写入 BOM (Byte Order Mark)，Excel 就能自动识别了。
        

---

### **进阶挑战 (Homework)**

现在的代码只能抓取第一页（前25部电影）。

**你的任务：**

改造 `main` 函数，使其能够抓取 **前 10 页**（共250部电影）。

**提示：**

1. **观察 URL 规律**：
    
    - 第 1 页: `?start=0`
        
    - 第 2 页: `?start=25`
        
    - 第 3 页: `?start=50`
        
2. **循环**：使用 `for` 循环构造 URL。
    
3. **礼貌爬虫 (Politeness)**：不要像 DDoS 攻击一样狂发请求。在每次循环末尾加上 `time.sleep(random.uniform(1, 3))`，随机休眠 1-3 秒，模拟人类行为。
    

**思考题**：如果网页是动态加载的（比如像 Twitter/X 那样往下滑动才加载新内容），这种 `requests` 方法还能用吗？（答案是不能，需要用到 Selenium 或 Playwright，这是爬虫的高阶内容）。

完成这个作业，你就拥有了“获取互联网数据”的能力。下一章（第四章），我们将进入 **API 开发**，让你不仅能“拿”数据，还能“提供”数据。

你想先做这个作业，还是直接看第四章（API 开发）的大纲？