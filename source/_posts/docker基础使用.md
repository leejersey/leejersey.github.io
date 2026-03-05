---
title: "docker基础使用"
date: 2020-06-01
---

## docker安装

首先你得安装Docker 和 Docker Compose, 使用 Docker Compose来配置镜像.

### 配置最简单的 Node 环境

一个简单的项目结构如下

```
├── docker-compose.yml
└── index.js
```

```js
// index.js
const http = require('http');

const server = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'text/html');
  res.setHeader('X-Foo', 'bar');
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('ok');
});

server.listen(3000);
```

```yml
# docker-compose.yml

version: "3"
services:
  web:
    image: node:8-alpine
    user: node
    working_dir: /home/node/app
    environment:
      - PORT=3000
    volumes:
      - ./:/home/node/app # 将本地目录映射到容器内
    command: ["node", "index.js"] # 运行命令
    ports:
      - 3000:3000 # 本地端口:容器端口
```

运行命令启动

```shell
$ docker-compose up
```

### Node 的依赖包

现在我们给项目添加依赖Koa，用 Koa 来搭建服务器.

这我们需要把node_modules和package.json打包进镜像

而官方的 node 镜像node:8-alpine是不安装依赖的，需要我们自定义一个镜像

创建一个 Dockerfile

```dockerfile
# Dockerfile
FROM node:8-alpine

# 设置工作目录
WORKDIR /home/node/app

# 把package.json复制进镜像中
COPY ./package.json /home/node/app/package.json

# 在镜像中安装依赖
RUN yarn --production
```

修改 docker-compose.yml

```yml
# docker-compose.yml

version: "3"
services:
  web:
    build:
      context: .
      dockerfile: ./Dockerfile
    user: node
    working_dir: /home/node/app
    environment:
      - PORT=3000
    volumes:
      - ./index.js:/home/node/app/index.js # 将本地目录映射到容器内
    command: ["node", "index.js"] # 运行命令
    ports:
      - 3000:3000 # 本地端口:容器端口
```

目录

```
├── Dockerfile
├── docker-compose.yml
├── index.js
├── package.json
└── yarn.lock
```

运行命令

```
$ docker-compose up
```

### 用 Nginx 反向代理，消除跨域问题

```
# nginx.conf
user nginx;
worker_processes 1;

error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
	worker_connections 1024;
}

http {

	include /etc/nginx/mime.types;
	default_type application/octet-stream;

	log_format main &apos;$remote_addr - $remote_user [$time_local] "$request" &apos;
	&apos;$status $body_bytes_sent "$http_referer" &apos;
	&apos;"$http_user_agent" "$http_x_forwarded_for"&apos;;

	access_log /var/log/nginx/access.log main;

	sendfile on;
	tcp_nopush on;

	gzip on;

	# 定义上游服务器
	upstream api {

		ip_hash;

                # 这里服务器使用 koaserver
                # 其实原理是Docker改写了host, koaserver指向nodejs那个容器的IP
		server koaserver:3000 weight=1;

		keepalive 300;
	}

	server {

		listen 80;
		server_name localhost;

		charset utf-8;

		root   /usr/share/nginx/html;

		# 代理以 api 为前缀的请求
		location ~^/api {
			proxy_pass http://api;
			proxy_set_header X-Forwarded-Proto $scheme;
			proxy_set_header Host $http_host;
			proxy_set_header X-Real-IP $remote_addr;
		}

		error_page 500 502 503 504 /50x.html;

		location = /50x.html {
			root /usr/share/nginx/html;
		}
	}

}
```

```
version: "3"
services:
  nginx_proxy:
    image: nginx:1.13.8-alpine
    restart: always
    working_dir: /home/static
    volumes:
       - ./index.html:/usr/share/nginx/html/index.html
       - ./nginx.conf:/etc/nginx/nginx.conf # 映射 ginx 配置文件
    ports:
      - 3000:80 # 绑定容器的80端口到本的1080端口
    links:
      - web:koaserver # 给它取个别名，叫做 koaserver
  web:
    build:
      context: .
      dockerfile: ./Dockerfile
    user: node
    working_dir: /home/node/app
    environment:
      - PORT=3000
    volumes:
      - ./index.js:/home/node/app/index.js # 将本地目录映射到容器内
    command: ["node", "index.js"] # 运行命令
```

html

```html

  
  
  
  Documenttitle>
head>

  hello html
body>
html>
```

目录

```
├── Dockerfile
├── docker-compose.yml
├── index.html
├── index.js
├── nginx.conf
├── package.json
└── yarn.lock
```

命令

```
$ docker-compose up
```

访问 localhost:3000， 返回 hello html
访问 localhost:3000/api， 返回 hello koa