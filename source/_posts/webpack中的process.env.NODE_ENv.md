---
title: "webpack中的process.env.NODE_ENv"
date: 2019-07-03
---

### 什么是process.env.NODE_ENV

在node中，有全局变量process表示的是当前的node进程。process.env包含着关于系统环境的信息。但是process.env中并不存在NODE_ENV这个东西。NODE_ENV是用户一个自定义的变量，在webpack中它的用途是判断生产环境或开发环境的依据的。

Package.json配置

```js
"scripts": {
  "dev": "NODE_ENV=development webpack-dev-server --progress --colors --devtool cheap-module-eval-source-map --hot --inline",
  "build": "NODE_ENV=production webpack --progress --colors --devtool cheap-module-source-map",
  "build:dll": "webpack --config webpack.dll.config.js"
},
```

如上打包命令，在dev打包命令上，前面加上了 NODE_ENV=development 命令，在build打包命令上前面加上了 NODE_ENV=production，因此继续查看代码结果变为如下：

```js
console.log('Running App version ' + VERSION); // 打印 Running App version 5fa3b9
console.log(PRODUCTION); // 打印 true
console.log(process.env); // 打印 { NODE_ENV: 'development' }
```

### 理解 cross-env

**1. 什么是cross-env呢？**
它是运行跨平台设置和使用环境变量的脚本。

**2. 它的作用是啥？**

当我们使用 NODE_ENV = production 来设置环境变量的时候，大多数windows命令会提示将会阻塞或者异常，或者，windows不支持NODE_ENV=development的这样的设置方式，会报错。因此 cross-env 出现了。我们就可以使用 cross-env命令，这样我们就不必担心平台设置或使用环境变量了。也就是说 cross-env 能够提供一个设置环境变量的scripts，这样我们就能够以unix方式设置环境变量，然而在windows上也能够兼容的。

要使用该命令的话，我们首先需要在我们的项目中进行安装该命令，安装方式如下：

```
npm install --save-dev cross-env
```

然后在package.json中的scripts命令如下如下：

```
"scripts": {
  "dev": "cross-env NODE_ENV=development webpack-dev-server --progress --colors --devtool cheap-module-eval-source-map --hot --inline",
  "build": "cross-env NODE_ENV=production webpack --progress --colors --devtool cheap-module-source-map",
  "build:dll": "webpack --config webpack.dll.config.js"
}
```