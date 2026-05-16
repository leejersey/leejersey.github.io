抱歉，刚才跑题了。你是对的，我们要专注于 **Playwright 自动化脚本** 本身，而不是把它做成后端服务。

Playwright 是目前最强大的自动化工具（微软出品），它的核心优势是 **快、稳定、自动等待**（不用傻傻地写 `sleep`）。

这是为你准备的 **纯粹的 Playwright 自动化实战教程**。

---

### **第一步：安装与初始化**

除了安装 Python 库，最重要的是下载浏览器内核（Chromium, Firefox, WebKit）。

Bash

```
# 1. 安装库
pip install playwright

# 2. 安装浏览器驱动 (这一步必须做，否则报错)
playwright install
```

---

### **第二步：理解核心概念 (Mental Model)**

Playwright 的层级结构非常清晰，类似洋葱：

1. **Browser (浏览器)**: 对应一个 Chrome/Firefox 进程。
    
2. **Context (上下文)**: **这是关键**。相当于“隐身窗口”。不同 Context 之间 Cookie、缓存完全隔离。
    
3. **Page (页面)**: 浏览器里的一个标签页。
    

---

### **第三步：Hello World (实战脚本)**

我们写一个脚本：打开必应 (Bing)，搜索 "Python Playwright"，并截图保存。

新建 `demo_search.py`:

Python

```
import asyncio
from playwright.async_api import async_playwright

async def main():
    # 使用 async 上下文管理器，自动处理关闭
    async with async_playwright() as p:
        # 1. 启动浏览器
        # headless=False: 有头模式，你可以看到浏览器操作过程（调试必开）
        # headless=True: 无头模式，后台静默运行（生产环境用）
        browser = await p.chromium.launch(headless=False)
        
        # 2. 创建上下文 (隐身模式)
        context = await browser.new_context()
        
        # 3. 新建标签页
        page = await context.new_page()
        
        print("正在打开必应...")
        await page.goto("https://www.bing.com")

        # 4. 定位并输入 (Locators & Actions)
        # Playwright 推荐使用语义化定位 (get_by_...)
        # 意思是：找到那个 placeholder 是 "搜索网页" 的输入框
        # 注意：如果是英文版 Bing，可能是 "Search the web"
        # 为了通用，我们这里用 CSS 选择器定位搜索框 ID
        search_box = page.locator("#sb_form_q") 
        
        await search_box.fill("Python Playwright") # 输入文字
        await search_box.press("Enter")            # 模拟回车键
        
        # 5. 等待结果加载
        # 不需要 sleep! 它会自动等待 id="b_results" 的元素出现
        await page.wait_for_selector("#b_results")
        
        print("搜索完成，正在截图...")
        await page.screenshot(path="result.png")
        
        # 6. 关闭浏览器
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**运行：**

Bash

```
python demo_search.py
```

---

### **第四步：核心定位器 (Locators) —— 必须掌握**

Selenium 只有 `find_element`，但 Playwright 有一套非常现代的定位逻辑。**不要即使去查 XPath，优先用下面这些**：

1. **`page.get_by_role()`** (推荐): 按角色定位。
    
    Python
    
    ```
    await page.get_by_role("button", name="提交").click()
    ```
    
2. **`page.get_by_placeholder()`**: 按输入框提示词。
    
    Python
    
    ```
    await page.get_by_placeholder("请输入账号").fill("admin")
    ```
    
3. **`page.get_by_text()`**: 按可见文本。
    
    Python
    
    ```
    await page.get_by_text("忘记密码？").click()
    ```
    
4. **`page.locator()`**: 万能兜底 (CSS 或 XPath)。
    
    Python
    
    ```
    await page.locator(".class-name").click()
    ```
    

---

### **第五步：进阶实战 —— 抓取动态列表**

**场景**：我们要去一个测试网站，抓取所有商品的 **名称** 和 **价格**。这个页面模拟了动态加载。

新建 `scraper_shop.py`:

Python

```
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 这是一个专门用来练习爬虫的网站
        await page.goto("https://www.saucedemo.com/")
        
        # 1. 登录 (标准流程)
        # 这里的 user-name 和 password 是网站定义的 ID
        await page.locator("#user-name").fill("standard_user")
        await page.locator("#password").fill("secret_sauce")
        await page.locator("#login-button").click()
        
        # 2. 确认登录成功 (等待商品列表出现)
        # 这一步很重要！防止页面还没跳转，你就开始抓数据
        await page.wait_for_selector(".inventory_list")
        
        print("登录成功，开始抓取数据...")
        
        # 3. 抓取列表数据
        # locator 就像一个游标，它现在指向所有的 .inventory_item
        items = page.locator(".inventory_item")
        
        # 获取匹配到的数量
        count = await items.count()
        print(f"当前页面共有 {count} 个商品")
        
        # 遍历每一个商品
        for i in range(count):
            # nth(i) 获取第 i 个元素
            item = items.nth(i)
            
            # 在当前 item 内部继续寻找 (Chaining)
            name = await item.locator(".inventory_item_name").inner_text()
            price = await item.locator(".inventory_item_price").inner_text()
            
            print(f"商品: {name} | 价格: {price}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
```

---

### **第六步：处理复杂的动态场景**

#### **1. 等待特定事件 (Auto-waiting 不够用时)**

有时候点击一个按钮，页面不会刷新，而是发起一个 AJAX 请求。

Python

```
# 点击下一页，并等待网络请求完全结束（比如加载转圈圈消失）
async with page.expect_request("**/api/products**"):
    await page.get_by_text("下一页").click()
```

#### **2. 模拟手机浏览器**

Playwright 可以完美伪装成 iPhone。

Python

```
iphone_12 = p.devices['iPhone 12']
context = await browser.new_context(**iphone_12) # 注入设备参数
```

#### **3. 保存与加载 Cookie (免登录)**

你不想每次跑脚本都重新登录一遍。

Python

```
# 1. 登录成功后，保存状态 (Cookie, LocalStorage)
await context.storage_state(path="auth.json")

# 2. 下次运行时，直接加载状态
context = await browser.new_context(storage_state="auth.json")
```

---

### **终极神器：Codegen (代码录制)**

这是 Playwright 对新手的**最大福利**。如果你不知道怎么定位某个元素，不要猜，让它自己写。

在终端执行：

Bash

```
playwright codegen wikipedia.org
```

1. 浏览器会自动打开。
    
2. 你在浏览器里乱点。
    
3. 旁边的小窗口会自动生成完美的 Python 代码。
    
4. **复制 -> 粘贴 -> 运行**。
    

### **总结**

作为一个开发者，你要掌握的 Playwright 核心动作就这三板斧：

1. **Locate**: 找到元素 (`get_by_role`, `locator`).
    
2. **Action**: 操作元素 (`click`, `fill`).
    
3. **Extract**: 提取数据 (`inner_text`, `get_attribute`).
    

这份教程是否符合你想要的“纯粹自动化”的需求？如果需要针对特定网站（比如有验证码的、或者无限滚动的）的案例，请告诉我。