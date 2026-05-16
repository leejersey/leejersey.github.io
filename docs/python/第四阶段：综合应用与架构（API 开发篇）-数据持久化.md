这是一个非常关键的转折点。我们要从“假数据”走向“真持久化”。

既然你的背景是 Node.js (可能熟悉 Prisma 或 TypeORM)，并且你在之前的对话中提到了 **PostgreSQL**，那么在 Python 的 FastAPI 生态中，最现代、最优雅的解决方案是 **SQLModel**。

### **为什么要用 SQLModel？**

- **FastAPI 的亲兄弟**：它们是同一个作者 (Tiangolo) 开发的。
    
- **二合一**：它同时是 **Pydantic 模型** (用于验证数据) 和 **SQLAlchemy 模型** (用于数据库操作)。
    
- **极大减少样板代码**：你不需要像以前那样定义两个类（一个为了 API 验证，一个为了数据库表结构）。
    

---

### **实战项目：构建“文章管理系统”后端**

我们将实现完整的 **CRUD** (增删改查)：

1. **Create**: 存入一篇 AI 生成的文章。
    
2. **Read**: 获取文章列表或单篇详情。
    
3. **Update**: 修改文章内容。
    
4. **Delete**: 删除文章。
    

#### **1. 安装依赖**

我们需要安装 `sqlmodel`。为了演示方便，我们先用 **SQLite** (文件型数据库)，因为它不需要配置服务器，代码跑通后，**只需改一行配置就能无缝切换到 PostgreSQL**。

Bash

```
pip install sqlmodel
```

#### **2. 编写完整代码 (`main.py`)**

为了让你看清全貌，我将所有逻辑放在一个文件中。

Python

```
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

# --- A. 数据库配置部分 ---

# 1. 定义模型 (表结构 + 数据验证)
# table=True 表示这是一个数据库表
class Article(SQLModel, table=True):
    # Field(default=None, primary_key=True) 表示这是主键，且由数据库自动生成
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)  # index=True 表示我们会经常按标题搜索，建立索引
    content: str
    platform: str = "Douyin"
    is_published: bool = False

# 2. 创建数据库连接 (Engine)
# sqlite_url = "sqlite:///./database.db"  # SQLite (本地文件)
# 如果要用 PostgreSQL，只需要把上面那行换成下面这行：
# postgresql_url = "postgresql://user:password@localhost/dbname"
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# connect_args 是 SQLite 特有的配置，Postgres 不需要
engine = create_engine(sqlite_url, echo=True) # echo=True 会打印 SQL 语句，方便调试

# 3. 初始化数据库函数
def create_db_and_tables():
    # 这行代码会自动在数据库中创建表 (如果不存在的话)
    SQLModel.metadata.create_all(engine)

# 4. 依赖注入：获取数据库会话 (Session)
# 类似于 Node.js 中每次请求建立一个 connection
def get_session():
    with Session(engine) as session:
        yield session

# --- B. FastAPI 应用部分 ---

app = FastAPI()

# 在应用启动时创建表
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- C. 接口逻辑 (CRUD) ---

# 1. CREATE: 创建文章
@app.post("/articles/", response_model=Article)
# session: Session = Depends(get_session) 是 FastAPI 的核心魔法
# 它表示：在执行这个函数前，先运行 get_session，把结果赋值给 session 参数
def create_article(article: Article, session: Session = Depends(get_session)):
    session.add(article)    # 标记要添加的对象
    session.commit()        # 真正执行 SQL (INSERT)
    session.refresh(article)# 刷新对象，获取数据库自动生成的 ID
    return article

# 2. READ (List): 获取文章列表
@app.get("/articles/", response_model=List[Article])
def read_articles(
    offset: int = 0, 
    limit: int = Query(default=10, le=100), 
    session: Session = Depends(get_session)
):
    # select(Article) 相当于 SELECT * FROM article
    statement = select(Article).offset(offset).limit(limit)
    articles = session.exec(statement).all()
    return articles

# 3. READ (One): 获取单篇文章
@app.get("/articles/{article_id}", response_model=Article)
def read_article(article_id: int, session: Session = Depends(get_session)):
    article = session.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章未找到")
    return article

# 4. UPDATE: 更新文章
@app.patch("/articles/{article_id}", response_model=Article)
def update_article(article_id: int, article_update: Article, session: Session = Depends(get_session)):
    # 先查出来
    db_article = session.get(Article, article_id)
    if not db_article:
        raise HTTPException(status_code=404, detail="文章未找到")
    
    # 这一步将用户传来的数据 (article_update) 更新到数据库对象 (db_article) 中
    # exclude_unset=True 表示只更新用户传了的字段，没传的字段保持原样
    article_data = article_update.dict(exclude_unset=True)
    for key, value in article_data.items():
        setattr(db_article, key, value)
        
    session.add(db_article)
    session.commit()
    session.refresh(db_article)
    return db_article

# 5. DELETE: 删除文章
@app.delete("/articles/{article_id}")
def delete_article(article_id: int, session: Session = Depends(get_session)):
    article = session.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章未找到")
    
    session.delete(article)
    session.commit()
    return {"ok": True}
```

---

### **核心机制深度解析**

为了让你理解这背后的流程，我们来看一下数据是如何流动的：

1. **Dependency Injection (`Depends`)**:
    
    - 在 Node.js (Express) 中，你可能需要在每个路由里手动写 `const db = await connect(); try { ... } finally { db.close() }`。
        
    - 在 FastAPI 中，`Depends(get_session)` 帮你自动完成了 **连接 -> 给路由使用 -> 自动关闭** 的全过程。代码极其干净。
        
2. **ORM 操作 (session)**:
    
    - `session.add()`: 并不是立即写入数据库，而是把对象加入到“待处理区”。
        
    - `session.commit()`: 这才是真正的 **提交事务**。如果中途报错，它会自动回滚，保证数据一致性。
        
    - `session.refresh()`: 这是一个很有意思的操作。当你 commit 后，数据库可能生成了 ID 或默认值（如 created_at）。`refresh` 会重新从数据库读取这些新值到 Python 对象中。
        

---

### **如何切换到 PostgreSQL？**

因为你已经在做 `content_factory` 项目，肯定不想一直用 SQLite。

1. **安装驱动**: Python 连接 Postgres 需要 `psycopg2` 库。
    
    Bash
    
    ```
    pip install psycopg2-binary
    ```
    
2. **修改 URL**:
    
    打开 `main.py`，找到 `sqlite_url` 那一行，替换为：
    
    Python
    
    ```
    # 格式: postgresql://用户名:密码@地址:端口/数据库名
    database_url = "postgresql://postgres:your_password@localhost:5432/content_factory"
    engine = create_engine(database_url)
    ```
    
    **不需要改动任何 CRUD 代码！** 这就是 ORM 的魅力。
    

---

### **课后实战任务**

你现在已经拥有了一个可以真正存取数据的后端雏形。请尝试完成以下任务：

1. **运行代码**：执行 `uvicorn main:app --reload`。
    
2. **观察文件**：你会发现目录下多了一个 `database.db` 文件，你可以下载一个 "DB Browser for SQLite" 软件查看里面的表结构。
    
3. **增加字段**：
    
    - 给 `Article` 模型增加一个字段 `created_at` (创建时间)。
        
    - _提示_：需要 `from datetime import datetime`，并设置 `default_factory=datetime.utcnow`。
        
    - _注意_：因为 SQLite 不支持直接修改表结构 (Migration)，你需要**删除 `database.db` 文件**让程序重新创建表，或者研究一下 `Alembic` (数据库迁移工具，这是进阶内容)。
        

做完这一步，你的“AI 内容工厂”就有了**记忆**。

接下来，你想学习如何**集成 OpenAI/DeepSeek 的 API** 来真正生成内容，还是想先了解 **如何部署** 这个服务让别人能访问？