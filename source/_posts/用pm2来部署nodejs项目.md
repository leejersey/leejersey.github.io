---
title: "用pm2来部署nodejs项目"
date: 2019-01-10
---

## 什么是pm2

#### 简介

PM2是node进程管理工具，可以利用它来简化很多node应用管理的繁琐任务，如性能监控、自动重启、负载均衡等，而且使用非常简单。

#### 安装

`npm install pm2 -g`

#### 用法

最简单的启用一个应用:  `pm2 start app.js` 

停止：`pm2 stop app_name|app_id` 

删除：`pm2 delete app_name|app_id` 

重启：`pm2 restart app_name|app_id` 

停止所有：`pm2 stop all` 

查看所有的进程：`pm2 list` 

查看所有的进程状态：`pm2 status` 

查看某一个进程的信息：`pm2 describe app_name|app_id`

#### 参数说明

- `--watch`：监听应用目录源码的变化，一旦发生变化，自动重启。如果要精确监听、不见听的目录，最好通过配置文件
- `-i --instances`：启用多少个实例，可用于负载均衡。如果`-i 0`或者`-i max`，则根据当前机器核数确定实例数目，可以弥补node.js缺陷
- `--ignore-watch`：排除监听的目录/文件，可以是特定的文件名，也可以是正则。比如`--ignore-watch="test node_modules "some scripts"` 
- `-n --name`：应用的名称。查看应用信息的时候可以用到
- `-o --output <path>`：标准输出日志文件的路径，有默认路径
- `-e --error <path>`：错误输出日志文件的路径，有默认路径
- `--interpreter <interpreter>`：the interpreter pm2 should use for executing app (bash, python…)。比如你用的coffee script来编写应用

**完整参数命令：** `pm2 start index.js --watch -i 2`

#### 使用配置文件

```js
pm2 init
```

生成配置文件ecosystem.config.js

#### 常规配置文件

```js
module.exports = {
  apps : [{
    name: "app",
    script: "./app.js",
    env: {
      NODE_ENV: "development",
    },
    env_production: {
      NODE_ENV: "production",
    }
  }]
}
```

#### 部署配置文件

```js
module.exports = {
  apps: [{}, {}],
  deploy: {
    production: {},
    staging: {},
    development: {}
  }
}
```

配置参数

| Entry name | Description | Type | Default |
| --- | --- | --- | --- |
| key | SSH key path | String | $HOME/.ssh |
| user | SSH user | String |  |
| host | SSH host | [String] |  |
| ssh_options | SSH options with no command-line flag, see ‘man ssh’ | String or [String] |  |
| ref | GIT remote/branch | String |  |
| repo | GIT remote | String |  |
| path | path in the server | String |  |
| pre-setup | Pre-setup command or path to a script on your local machine | String |  |
| post-setup | Post-setup commands or path to a script on the host machine | String |  |
| pre-deploy-local | pre-deploy action | String |  |
| post-deploy | post-deploy action | String |

运行

```
pm2 start /path/to/ecosystem.config.js
```

文档地址：[https://pm2.io/doc/en/runtime/overview/](https://pm2.io/doc/en/runtime/overview/)

参考：[https://pm2.io/doc/en/runtime/reference/ecosystem-file/](https://pm2.io/doc/en/runtime/reference/ecosystem-file/)