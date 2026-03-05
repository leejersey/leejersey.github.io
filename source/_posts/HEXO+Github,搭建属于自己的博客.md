---
title: "HEXO+Github,搭建属于自己的博客"
date: 2017-10-17
---

转：[http://baixin.io/2015/08/HEXO%E6%90%AD%E5%BB%BA%E4%B8%AA%E4%BA%BA%E5%8D%9A%E5%AE%A2/](http://baixin.io/2015/08/HEXO%E6%90%AD%E5%BB%BA%E4%B8%AA%E4%BA%BA%E5%8D%9A%E5%AE%A2/)

## 配置环境

安装Node（必须）

作用：用来生成静态页面的 到Node.js官网下载相应平台的最新版本，一路安装即可。

## 安装Git（必须）

作用：把本地的hexo内容提交到github上去. 安装Xcode就自带有Git，我就不多说了。

## 申请GitHub（必须）

作用：是用来做博客的远程创库、域名、服务器之类的，怎么与本地hexo建立连接等下讲。 github账号我也不再啰嗦了,没有的话直接申请就行了，跟一般的注册账号差不多，SSH Keys，看你自己了，可以不配制，不配置的话以后每次对自己的博客有改动提交的时候就要手动输入账号密码，配置了就不需要了，怎么配置我就不多说了，网上有很多教程。

## 正式安装HEXO

Node和Git都安装好后，可执行如下命令安装hexo：

`$ sudo npm install -g hexo`

初始化

创建一个文件夹，如：Blog，cd到Blog里执行hexo init的。命令：

`hexo init`

好啦，至此，全部安装工作已经完成！

生成静态页面

继续再Blog目录下执行如下命令，生成静态页面

`hexo generate （hexo g  也可以）`

本地启动

启动本地服务，进行文章预览调试，命令：

`hexo server`

浏览器输入[http://localhost:4000](http://localhost:4000) 我不知道你们能不能，反正我不能，因为我还有环境没配置好

## 常见的HEXO配置错误：

ERROR Plugin load failed: hexo-server

原因： Besides, utilities are separated into a standalone module. hexo.util is not reachable anymore.

解决方法，执行命令：$ sudo npm install hexo-server

执行命令hexo server，提示：Usage: hexo ….

原因：我认为是没有生成本地服务

解决方法，执行命令：$ npm install hexo-server –save

提示：hexo-server@0.1.2 node_modules/hexo-server
…. 

表示成功了[参考](https://hexo.io/zh-cn/docs/server.html)

这个时候再执行：

`$ hexo-server`

得到:

`INFO Hexo is running at http://0.0.0.0:4000/. Press Ctrl+C to stop.`

这个时候再点击[http://0.0.0.0:4000，正常情况下应该是最原始的画面，但是我看到的是：](http://0.0.0.0:4000，正常情况下应该是最原始的画面，但是我看到的是：) 白板和Cannot GET / 几个字 原因： 由于2.6以后就更新了，我们需要手动配置些东西，我们需要输入下面三行命令：

`npm install hexo-renderer-ejs --save`

`npm install hexo-renderer-stylus --save`

`npm install hexo-renderer-marked --save`

这个时候再重新生成静态文件，命令：

`hexo generate （或hexo g）`

启动本地服务器：

`hexo server （或hexo s）`

再点击网址[http://0.0.0.0:4000](http://0.0.0.0:4000) OK终于可以看到属于你自己的blog啦，?，虽然很简陋，但好歹有了一个属于自己的小窝了。参考链接，本地已经简单的设置好了，但是现在域名和服务器都是基于自己的电脑，接下来需要跟github进行关联。

## 配置Github

建立Repository

建立与你用户名对应的仓库，仓库名必须为【your_user_name.github.io】，固定写法 然后建立关联，我的Blog在本地/Users/leopard/Blog，Blog是我之前建的东西也全在这里面，有：

Blog
　｜
　｜－－ _config.yml
　｜－－ node_modules
　｜－－ public
　｜－－ source
　｜－－ db.json
　｜－－ package.json
　｜－－ scaffolds
　｜－－ themes 　　　　　 　　　
现在我们需要_config.yml文件，来建立关联，命令：

`vim _config.yml`

翻到最下面，改成我这样子的，注意： : 后面要有空格

```
deploy:
  type: git
  repository: https://github.com/leejersey/leejersey.github.io.git
  branch: master
```

执行如下命令才能使用git部署

`npm install hexo-deployer-git --save`

网上会有很多说法，有的type是github, 还有repository 最后面的后缀也不一样，是github.com.git，我也踩了很多坑，我现在的版本是hexo: 3.1.1，执行命令hexo -vsersion就出来了,貌似3.0后全部改成我上面这种格式了。 忘了说了，我没用SSH Keys如果你用了SSH Keys的话直接在github里复制SSH的就行了，总共就两种协议，相信你懂的。 然后，执行配置命令：

`hexo deploy`

　然后再浏览器中输入[http://leejersey.github.io/就行了，我的](http://leejersey.github.io/就行了，我的) github 的账户叫 leejersey ,把这个改成你 github 的账户名就行了

## 部署步骤

每次部署的步骤，可按以下三步来进行。

```
hexo clean
hexo generate
hexo deploy
```

## 一些常用命令：

```
hexo new "postName" #新建文章

hexo new page "pageName" #新建页面

hexo generate #生成静态页面至public目录

hexo server #开启预览访问端口（默认端口4000，&apos;ctrl + c&apos;关闭server）

hexo deploy #将.deploy目录部署到GitHub

hexo help  #查看帮助

hexo version  #查看Hexo的版本
```

这里有大量的主题列表使用方法里面 都有详细的介绍，我就不多说了。 

```
　Cover - A chic theme with facebook-like cover photo 
　Oishi - A white theme based on Landscape plus and Writing. 
　Sidebar - Another theme based on Light with a simple sidebar 
　TKL - A responsive design theme for Hexo. 一个设计优雅的响应式主题 
　Tinnypp - A clean, simple theme based on Tinny 
　Writing - A small and simple hexo theme based on Light 
　Yilia - Responsive and simple style 优雅简洁响应式主题，我用得就是这个。
　Pacman voidy - A theme with dynamic tagcloud and dynamic snow
```

## 一些基本路径

　文章在 source/_posts，编辑器可以用 Sublime，支持 markdown 语法。如果想修改头像可以直接在主题的 _config.yml 文件里面修改，友情链接，之类的都在这里，修改名字在 public/index.html 里修改，开始打理你的博客吧，有什么问题或者建议，都可以提出来，我会继续完善的。

Markdown语法参考链接: 作业部落

## Q&A

问：如何让文章想只显示一部分和一个 阅读全文 的按钮？ 

答：在文章中加一个  ，  后面的内容就不会显示出来了。

问：本地部署成功了，也能预览效果，但使用 username.github.io 访问，出现 404 . 

答：首先确认 hexo d 命令执行是否报错，如果没有报错，再查看一下你的 github 的 username.github.io 仓库，你的博客是否已经成功提交了，你的 github 邮箱也要通过验证才行。