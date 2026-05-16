部署 Python Web 服务（尤其是 FastAPI）目前业界最标准、最“现代化”的方案是 **Docker + Docker Compose**。

对于你（熟悉 Node.js）来说，这就像是把 `npm start` 封装进了一个“集装箱”，无论丢到阿里云、AWS 还是腾讯云，它都能一键运行，彻底解决“我的电脑上能跑，服务器上跑不起来”的问题。

---

### **部署架构图**

我们将采用 **Nginx (反向代理) -> Docker (应用容器) -> PostgreSQL (数据库)** 的架构。

---

### **第一步：项目容器化 (Dockerization)**

在你的项目根目录下（也就是 `main.py` 所在的文件夹），我们需要创建两个核心文件。

#### **1. 生成依赖列表 (`requirements.txt`)**

Python 不像 Node.js 会自动把依赖写进 `package.json`。你需要手动生成：

Bash

```
pip freeze > requirements.txt
```

_检查一下文件内容，确保 `fastapi`, `uvicorn`, `sqlmodel`, `psycopg2-binary` 等都在里面。_

#### **2. 编写 `Dockerfile`**

这就相当于告诉 Docker：“如何构建我的应用镜像”。

Dockerfile

```
# 1. 使用官方轻量级 Python 镜像
FROM python:3.10-slim

# 2. 设置工作目录 (相当于 cd /app)
WORKDIR /app

# 3. 复制依赖文件并安装 (利用 Docker 缓存层)
COPY requirements.txt .

# 换源提示：如果在国内服务器部署，可以加上 -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir -r requirements.txt

# 4. 复制项目所有代码到容器
COPY . .

# 5. 暴露端口 (仅作声明，实际需要在运行时映射)
EXPOSE 8000

# 6. 启动命令
# host 0.0.0.0 是必须的，否则外部无法访问容器
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### **第二步：编排服务 (Docker Compose)**

因为你在这个项目中需要 **API 服务** 和 **PostgreSQL 数据库** 配合工作。如果手动一个个启动容器太麻烦了，我们用 `docker-compose.yml` 来编排它们。

在项目根目录创建 `docker-compose.yml`：

YAML

```
version: '3.8'

services:
  # 服务 1: 你的 FastAPI 应用
  web:
    build: .
    container_name: content_factory_api
    ports:
      - "8000:8000"  # 映射 宿主机端口:容器端口
    environment:
      # ⚠️ 注意：在 Docker 内部，访问数据库不能用 localhost，要用服务名 "db"
      - DATABASE_URL=postgresql://postgres:mysecretpassword@db:5432/content_factory
    depends_on:
      - db
    restart: always

  # 服务 2: PostgreSQL 数据库
  db:
    image: postgres:15
    container_name: content_factory_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: mysecretpassword
      POSTGRES_DB: content_factory
    volumes:
      # 数据持久化：把数据库文件映射到宿主机，防止容器删除后数据丢失
      - postgres_data:/var/lib/postgresql/data
    restart: always

volumes:
  postgres_data:
```

> **⚠️ 关键修改**：
> 
> 记得去你的 `main.py` 里，把数据库连接代码改成从环境变量读取：
> 
> Python
> 
> ```
> import os
> # 如果环境变量没设置，就用默认值 (本地开发用)
> DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")
> engine = create_engine(DATABASE_URL)
> ```

---

### **第三步：服务器实战操作**

假设你已经买了一台云服务器（阿里云/腾讯云/AWS），操作系统选 **Ubuntu 22.04 LTS** (推荐)。

#### **1. 连接服务器**

打开终端（Windows 用 PowerShell 或 Git Bash）：

Bash

```
ssh root@你的服务器IP
```

#### **2. 安装 Docker**

在服务器上依次执行（只需要做一次）：

Bash

```
# 更新软件源
apt update

# 安装 Docker
apt install docker.io docker-compose-plugin -y

# 启动 Docker 并设置开机自启
systemctl start docker
systemctl enable docker
```

#### **3. 上传代码**

你有两个选择：

- **Git (推荐)**: 把你的代码推送到 GitHub/Gitee，然后在服务器上 `git clone`。
    
- **SCP (简单粗暴)**: 直接把本地文件夹传上去。
    
    Bash
    
    ```
    # 在你本地电脑执行
    scp -r ./你的项目文件夹 root@服务器IP:/root/
    ```
    

---

### **第四步：启动服务**

进入你的项目目录，见证奇迹：

Bash

```
# -d 表示后台运行 (Detached mode)
docker compose up -d --build
```

**查看状态：**

Bash

```
docker compose ps
```

如果看到 State 是 `Up`，说明部署成功！

**查看日志（如果有报错）：**

Bash

```
docker compose logs -f web
```

此时，你访问 `http://你的服务器IP:8000/docs`，应该就能看到 Swagger 文档了！

---

### **第五步：配置 Nginx (生产环境必备)**

直接用 `IP:8000` 访问既不专业也不安全。我们需要用 Nginx 把端口转发到 80 (HTTP) 或 443 (HTTPS)，并绑定域名。

**1. 安装 Nginx**

Bash

```
apt install nginx -y
```

**2. 编写配置文件**

新建一个配置文件：

Bash

```
nano /etc/nginx/sites-available/fastapi_app
```

写入以下内容（把 `your_domain.com` 换成你的域名或服务器IP）：

Nginx

```
server {
    listen 80;
    server_name your_domain.com;  # 你的域名

    location / {
        proxy_pass http://127.0.0.1:8000;  # 转发到 Docker 的 8000 端口
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**3. 激活并重启**

Bash

```
# 创建软链接
ln -s /etc/nginx/sites-available/fastapi_app /etc/nginx/sites-enabled/

# 测试配置是否正确
nginx -t

# 重启 Nginx
systemctl restart nginx
```

现在，你直接访问 `http://你的域名` (不用输 :8000) 就能看到你的 API 了。

---

### **给你的“开发者作业”**

你现在已经完成了**从 0 到 1 的后端架构搭建**：

Python 代码 -> 数据库存储 -> Docker 容器化 -> 云服务器部署。

接下来的挑战：

1. **自动化部署 (CI/CD)**：这在团队开发中很重要。试着研究 **GitHub Actions**，如何实现“我一 push 代码，服务器自动拉取并重启 Docker”。
    
2. **安全性**：现在的数据库密码是写在 `docker-compose.yml` 里的，这不安全。试着研究如何使用 `.env` 文件来管理环境变量。
    

至此，你的 **Python 基础与后端架构** 学习已经形成闭环。

**最终问题**：你是想现在去试着部署一下，还是我们继续回到代码层面，深入 **AI Agent 开发**（如何让这个后端真正具备“智能”）？