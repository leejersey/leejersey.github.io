---
title: "Mongodb数据库操作"
date: 2017-10-19
---

# Mongodb 数据库操作

### 启动 Mongodb

```
mkdir -p data/db
mongod --dbpath=./data/db
```

### 开启 Mongo Shell

```
$ mongo
```

### 创建一个数据库

```
$ use digicity-express-api
```

数据库是 mongodb 中的顶级存储单位，之下一级就是 **集合** 。

### 创建一个集合

```
$ db.createCollection(‘posts’)
```

### 插入数据记录

一个集合（例如，posts ），里面可以插入多个数据记录。

```
$ db.posts.insert({title: &apos;myTitle&apos;, content: &apos;myContent&apos;})
```

### 查看集合中的所有记录

```
$ db.posts.find()
```

### Hello Ada

![](https://github.com/happypeter/digicity-express-api/blob/master/doc/img/001-ada.png?raw=true)

### 修改一条记录（了解内容）

```
db.posts.update({_id: ObjectId(&apos;xxx&apos;)}, {$set: {title: &apos;mongodb&apos;}})
```

### 删除一条记录

```
db.posts.remove({_id: ObjectId(&apos;xxx&apos;)})
```

### 删除 posts 集合中的所有记录

```
db.posts.remove({})
```

### 删除数据库

假设我们的数据库叫做 digicity-express-api

```
use digicity-express-api
db.dropDatabase()
```

### 为什么叫记录电子版笔记？

第一个原因，使用 markdown 格式美观

> Beauty is your ablity to tame complexity

第二个原因，便于更新

第三个原因，有 git/github 控制，永远不会丢失

第四个原因，便于搜索。

# 用 JS 代碼操作 mongodb

我們主要基於一個 JS 庫的幫助，[Mongoose](http://mongoosejs.com/) ，它可以
作為一個 npm 的包來安裝。

解釋一下，一個 **JS 庫** 就是一組 **JS 接口** 的集合。庫，英文對應 library 。

![](https://github.com/happypeter/digicity-express-api/blob/master/doc/img/002-mongoose.png?raw=true)

下面我们来动手做一个 express+mongoose 的小 demo 。

### 先写一个最简单的 express 程序

index.js 如下：

```
var express = require(&apos;express&apos;);
var app = express();

// 下面这个就是路由代码
app.post(&apos;/posts&apos;, function(req, res){
  console.log(&apos;hello&apos;);
});

app.listen(3000, function(){
  console.log(&apos;running on port 3000.....&apos;);
});
```

相应的 curl 测试命令是

```
curl --request POST localhost:3000/posts
```

如果可以在运行 `node index.js` 的位置看到 `hello` 表示我们这一步胜利完成。

![](https://github.com/happypeter/digicity-express-api/blob/master/doc/img/003-curl.png?raw=true)

### 安装 mongoose

作为一个 npm 包进行安装，[link](https://www.npmjs.com/package/mongoose)

```
npm install --save mongoose
```

### 在 js 代码中导入 mongoose

```
var mongoose = require(&apos;mongoose&apos;);
```

### 进行数据库的连接

```
mongoose.connect(&apos;mongodb://localhost:27017/digicity-express-api&apos;);
```

mongoose.connect 接口用来连接我们系统上安装的 mongodb 数据库。

如何定位数据库的所在位置？

- 一种逻辑上可行的方案，就是用数据存储的文件夹的位置（比如我们前面采用的 data/db 文件夹），但是实际上 Mongodb 有其他方法
- mongodb 的软件，运行起来类似一个网站，用链接来访问。（ mongodb://localhost:27017 ）

但是，链接之后，要跟上具体的数据库名字。我们每次链接，都是链接到一个数据库。比如我们这里，
就是 digicity-express-api （一般与项目名同名）。

如何验证链接成功呢？用下面的代码

```
var db = mongoose.connection;
db.on(&apos;error&apos;, console.log);
db.once(&apos;open&apos;, function() {
  console.log(&apos; success!&apos;)
});
```

看到 `success` 字样表示链接成功。

### 定义数据的概要 Schema

数据天然的具有一定的结构，比如，人员名单中，自然的会涉及姓名，年龄，籍贯等信息。
在 mongodb 这里，一个人员的信息会被作为一条记录来保存。所有信息的类型会对应成字段名，
由于是跟计算机打交道，每个字段还要涉及它的数据类型（ num，string …) 。

那么 Schema 就是用来规定一个记录的各个字段的，字段名+数据类型的。

```
var Schema = mongoose.Schema;

var PostSchema = new Schema(
  {
    title: String,
    content: String
  }
);
```

上面的代码，规定出了我们的记录能够保存哪些数据。

### 创建数据模型 model

数据库的结构是，一个数据库，里面会包含多个集合，一个集合会包含多条数据记录。

那么现在，我们数据要往哪个数据库中存？这个问题通过前面的 `mongoose.connect(xxx)` 的语句指定了。

但是数据要保存到哪个集合还没有指定。所有我们的 model 创建语句如下：

```
var Post = mongoose.model(&apos;Post&apos;, PostSchema);
```

上面 `.model()` 的第一个参数，`Post` 就为我们指定了集合的名字，会对应数据库中的 posts 这个集合。第二个参数是数据 schema ，就是前面我们定义的。

到这里，所有数据存储的基础设施全部就绪。

### 实例化 model 得到数据对象

现在我们要把实际要存储的数据，放到一个 model 的实例（对象）之中了。

```
var post = new Post({title:"myTitle", content: "myConent"})
```

### 对象之上呼叫 save()

这样可以把数据保存到数据库中。

```
post.save(function(){
  console.log(&apos;saved&apos;);
});
```