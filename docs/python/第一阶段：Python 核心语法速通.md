这是一个为**开发者背景**（考虑到你之前的Node.js经验）定制的 Python 第一阶段“**语法速通**”教程。

我们将跳过编程基础概念（如什么是变量），直接切入 Python 的核心语法特性。Python 的哲学是 **"Explicit is better than implicit"**（明了胜于晦涩）。

---

### 

#### **0. 环境与核心习惯**

- **解释器**：Python 是解释型语言，代码逐行执行。
    
- **缩进（Indentation）**：**这是 Python 的灵魂**。Python **没有** `{}` 来包裹代码块，完全依靠缩进（通常是 4 个空格）来表示层级关系。缩进错误会直接导致 `IndentationError`。
    
- **注释**：单行用 `#`，多行用 `''' ... '''` 或 `""" ... """`。
    

---

#### **1. 变量与基础数据类型**

Python 是**动态强类型**语言。不需要声明类型（如 `var` 或 `int`），但类型检查严格（比如不能直接让字符串和数字相加）。

**代码实例：**

Python

```Python
# 1. 变量赋值 (不需要 let/const/var)
name = "Gemini"      # 字符串 (String)
age = 2           # 整数 (Integer)
rating = 4.9      # 浮点数 (Float)
is_active = True  # 布尔值 (Boolean, 注意首字母大写!)

# 2. 字符串格式化 (f-string) - 现代 Python 必备，类似 JS 的 `template literals`
print(f"Name: {name}, Age: {age}") 

# 3. 类型转换
price_str = "100"
price_int = int(price_str)  # 转整数
print(price_int + 50)       # 输出 150
# print(price_str + 50)     # ❌ 报错：TypeError
```

---

#### **2. 核心数据结构：列表 (List) 与 字典 (Dictionary)**

这两个是 Python 的左膀右臂。

**A. 列表 (List)**

类似 JS 的 Array，但功能更强大，特别是**切片 (Slicing)**。

Python

```Python
# 定义列表
tech_stack = ["Python", "Java", "Go", "Node.js", "Rust"]

# 1. 基础操作
print(tech_stack[0])      # 索引：'Python'
print(tech_stack[-1])     # 负索引（倒数第一个）：'Rust' (这是 Python 特色)
tech_stack.append("C++")  # 追加元素

# 2. 切片 (Slicing) - [start:end:step] (左闭右开)
print(tech_stack[1:3])    # ['Java', 'Go'] (取索引1到2，不包含3)
print(tech_stack[:2])     # ['Python', 'Java'] (从头取到索引2)
print(tech_stack[::2])    # ['Python', 'Go', 'Rust'] (步长为2，隔一个取一个)

# 3. 常用方法
len(tech_stack)           # 获取长度
"Go" in tech_stack        # 判断是否存在 (返回 True)
```

**B. 字典 (Dictionary)**

类似 JS 的 Object 或 Java 的 Map。键值对存储。

Python

```Python
# 定义字典
user_profile = {
    "id": 101,
    "name": "Alex",
    "skills": ["Python", "AI"]
}

# 1. 访问与修改
print(user_profile["name"])  # 'Alex'
user_profile["role"] = "Admin" # 新增或修改键值对

# 2. 安全获取 (推荐)
# 如果 key 不存在，user_profile["email"] 会报错，用 .get() 则返回 None
email = user_profile.get("email", "default@example.com") 

# 3. 常用方法
keys = user_profile.keys()      # 获取所有键
values = user_profile.values()  # 获取所有值
```

---

#### **3. 控制流 (Control Flow)**

注意冒号 `:` 和缩进。

**A. 条件判断 (If/Elif/Else)**

Python

```Python
score = 85

if score >= 90:
    print("优秀")
elif score >= 60:  # 注意是 elif，不是 else if
    print("及格")
else:
    print("不及格")
```

**B. 循环 (Loop)**

Python 的 `for` 循环通常用于**遍历**（List, Dict, String），而不是像 C 语言那样数数。

Python

```Python
# 1. 遍历列表
fruits = ["Apple", "Banana", "Cherry"]
for fruit in fruits:
    print(f"I like {fruit}")

# 2. 遍历数字范围 (0 到 4)
for i in range(5): 
    print(i)

# 3. while 循环
count = 3
while count > 0:
    print(count)
    count -= 1
```

---

#### **4. 函数 (Functions)**

使用 `def` 关键字。

Python

```Python
# 定义函数
def calculate_total(price, tax_rate=0.1): # tax_rate 是默认参数
    """
    这是一个文档字符串 (Docstring)，用于解释函数功能。
    计算含税总价。
    """
    total = price * (1 + tax_rate)
    return total

# 调用
print(calculate_total(100))        # 使用默认税率: 110.0
print(calculate_total(100, 0.2))   # 覆盖默认税率: 120.0

# 关键字参数 (可以让代码更清晰)
print(calculate_total(tax_rate=0.05, price=200)) 
```

---

#### **5. 模块化 (Import)**

Python 拥有庞大的标准库和第三方库（PyPI）。

Python

```Python
# 方式 1: 导入整个模块
import math
print(math.sqrt(16))

# 方式 2: 导入特定函数 (推荐，如果只用几个函数)
from datetime import datetime
print(datetime.now())

# 方式 3: 给模块起别名 (数据分析常用)
# import pandas as pd 
# import numpy as np
```

---

### **📝 第一阶段实战作业：简单的“待办事项管理器”**

请尝试在你的编辑器中编写以下代码，并运行它。这将串联起变量、列表、循环、输入输出和条件判断。

**目标**：创建一个脚本，允许用户输入任务，输入 'q' 退出，最后打印所有任务。

**参考代码（先试着自己写，再看答案）：**

Python

```Python
def main():
    print("--- 简易待办事项 (Todo List) ---")
    todos = []  # 初始化空列表

    while True:
        # input() 获取用户输入，始终返回字符串
        task = input("请输入任务 (输入 'q' 退出): ")

        if task == 'q':
            break  # 跳出循环
        
        if task == '':
            print("任务不能为空！")
            continue # 跳过本次循环，重新开始

        todos.append(task)
        print(f"已添加: {task}")

    # 循环结束后，打印清单
    print("\n--- 你的任务清单 ---")
    # enumerate 可以同时获得 索引(index) 和 内容(item)
    for index, item in enumerate(todos, start=1):
        print(f"{index}. {item}")

# 这是一个常见的入口判断，虽然不强制，但建议养成习惯
if __name__ == "__main__":
    main()
```

### **下一步建议**

1. **安装环境**：确保你电脑上安装了 Python (建议安装 Anaconda 或直接官网下载 Python 3.x)。
    
2. **运行代码**：把上面的“实战作业”保存为 `todo.py`，在终端运行 `python todo.py`。
    
3. **搞懂切片**：特别是列表的 `[:]` 操作，这在以后处理数据（如 AI 的 Tensor）时非常重要。
    

当你把这个 `todo.py` 跑通并理解后，告诉我，我们就可以进入**第二阶段：文件整理神器（实战篇）**了。