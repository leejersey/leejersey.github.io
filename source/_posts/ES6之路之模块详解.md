---
title: "ES6之路之模块详解"
date: 2018-10-07
---

前言

今日早读文章由蘑菇街@勿忘心安 投稿分享。

> @勿忘心安，蘑菇街前端工程师，相信 w3c，遵从黑客文化，相信自己能改变世界

#### 简介

##### 何为模块

一个模块只不过是一个写在文件中的 JavaScript 代码块。

模块中的函数或变量不可用，除非模块文件导出它们。

简单地说，这些模块可以帮助你在你的模块中编写代码，并且只公开应该被你的代码的其他部分访问的代码部分。

##### 为什么要使用模块

1. 
2. 
3. 

#### 如何使用

##### 导出模块

导出模块所用的命令是 export。

前面也提到一个模块就是一个 javascript 文件，在这个模块中定义的变量，外部是无法获取到的，只有通过 export 导出的变量其他模块才可以用

最简单的导出方式就是在声明的变量、函数、类前面加一个 export

```javascript
// export1.js 
// 导出变量
exportlet name ='桃翁';
// 导出函数
exportfunctionprint(){
    console.log("欢迎前端桃园");
}
// 导出类
exportclassPerson{
    constructor(name){
        this.name = name;
    }
}
// 私有函数
function privateFunction (){
    console.log('我是私有函数，外部访问不了我');
}
```

> **注意**：

1. 
2. 

除了上面那种导出方式，还有另外一种

```javascript
// export2.js
// 导出变量
let name ='桃翁'；
// 导出函数
functionprint(){
    return'欢迎前端桃园';
}
// 导出类
classPerson{
    constructor(name){
        this.name = name;
    }
}
// 私有函数
function privateFunction (){
    return'我是私有函数，外部访问不了我';
}
export{ name,print,Person}
```

上面这种写法导入一组变量，与 export1.js 是等价的。

##### 导入模块

导入的模块可以理解为是生产者（或者服务的提供者），而使用导入的模块的模块就是消费者。

导入模块的命令是 import, import 的基本形式如下：

```javascript
import{ var1, var2 }from'./example.js'
```

import 语句包含两部分：一是导入需要的标识符，二是模块的来源。

> 注意：浏览器中模块来源要以「/」或者 「./」 或者 「../」开头 或者 url 形式，不然会报错。

例如我们导入 export1.js 模块，可以这么导入

```javascript
// import1.js
import{ name,print,Person}from'./export1.js';
console.log(name);// 桃翁
console.log(print());// 欢迎前端桃园
// 报错, 不能定义相同名字变量
let name =2333;
// 报错，不能重新赋值
name ="小猪";
```

可以看到导入绑定(这里不理解绑定，文章后面会解释)时，形式类似于对象解构，但实际上并无关联。

当导入绑定的时候，绑定类似于使用了 const 定义，意味着不能定义相同的变量名，但是没有暂时性死区特性(但是在 深入理解ES6 这本书里面说是有暂时性死区限制，我在 chrome 上测试了的，读者希望也去试下，到底受不受限制)。

```javascript
let name =2333;
```

上面这行代码会报错。

##### 命名空间导入

这种导入方式是把整个生产者模块当做单一对象导入，所有的导出被当做对象的属性。

```javascript
// import2.js
import*asnamespacefrom'./export1.js'
console.log(namespace.name);// 桃翁
console.log(namespace.print());// 欢迎前端桃园
```

#### 重命名导入导出

有时候你并不想导出变量的原名称，需要重新命名,这个时候只需要使用 as 关键字来制定新的名字即可。

##### 重命名导出

```javascript
// export3.js
functionprint(){
    return'欢迎前端桃园';
}
export{printas advertising }
```

##### 导重命名入

拿上面导出的举例子

```javascript
// import3.js
import{ advertising asprint}from'./export3.js'
console.log(typeof advertising);// "undefined"
console.log(print());// 欢迎前端桃园
```

此代码导入 advertising 函数并重命名为了 print ，这意味着此模块中 advertising 标识符不存在了。

##### default 关键字

default 关键字是用来做默认导入导出的。

##### 默认导出

```javascript
// defaultExport.js
// 第一种默认导出方式
exportdefaultfunctionprint(){
    return'欢迎前端桃园';
}
// 第二种默认导出方式
functionprint(){
    return'欢迎前端桃园';
}
exportdefaultprint;
// 第三种默认导出方式
functionprint(){
    return'欢迎前端桃园';
}
export{printasdefault}
```

default 这个关键字在 JS 中具有特殊含义，既可以作为同命名导出，又标明了模块需要使用默认值。

> 注意： 一个模块中只能有一个默认导出。

##### 默认导入

默认导入和一般的导入不同之处就是不需要写大括号了，看起来更简洁。

把上面 defaultExport.js 模块导出的作为例子

```javascript
importprintfrom'./defaultExport.js'
console.log(print());// 欢迎前端桃园
```

那如果既有默认的又有非默认的怎么导入呢？看例子就明白了

```javascript
// defaultImport1.js
let name ='桃翁';
functionprint(){
    return'欢迎前端桃园';
}
export{ name,printasdefault}
// defaultImport2.js
importprint,{ name }from'./defaultImport1.js'
console.log(print());// 欢迎前端桃园
console.log(name);// 桃翁
```

混合导入需要把默认导入的名称放在最前面，然后用逗号和后面非默认导出的分割开。

> 思考了很久是否应该加上进阶内容，本来是想写入门级系列的，但是想了想，还是都写进来吧，入门的看入门前面基础，深入理解的看进阶。

#### 进阶

进阶部分主要介绍 模块的几个特性

- 
静态执行

- 
动态关联

- 
模块不会重复执行

##### 静态执行

所谓静态执行其实就是在编译阶段就需要确定模块的依赖关系，那么就会出现 import 命令会优先于模块其他内容的执行，会提前到编译阶段执行。

```javascript
// static1.js
console.log('佩奇');
import{ nouse }from'./static2.js'
// static2.js
exportfunction nouse(){
    return'我是不需要的';
}
console.log('小猪');
```

可以看到最后输出的应该是「小猪」先输出，而「佩奇」后输出，可以得出虽然 static2.js 在后面引入，但是会被提升到模块的最前面先执行。

这也是我前面所说的不受暂时性死区原因之一，在这里可以写一个例子试试：

```javascript
// static3.js
console.log(nouse());
import{ nouse }from'./static2.js'
// 结果：
// 小猪
// 我是不需要的
```

经检验确实是可以在 import 之前使用导入的绑定。

静态执行还会导致一个问题，那就是不能动态导入模块。

```javascript
// 报错
if(flag){
    import{ nouse }from'./static3.js'
}
// 报错
import{'no'+'use'}from'./static3.js'
```

因为 import 是静态执行的，所以在静态(词法)分析阶段，是没法得到表达式或者变量的值的。

但是为了解决这个问题，因为了 import() 这个函数，这个算扩展内容吧，写太多了我怕没人看完了，后面会有扩展阅读链接。

##### 动态关联

所谓的动态关联，其实就是一种绑定关系, 这是 ES6 非常重要的特性，一定仔细阅读。

在 ES6 的模块中，输出的不是对象的拷贝，不管是引用类型还是基本类型, 都是动态关联模块中的值，。

```javascript
// dynamic1.js
exportlet name ='桃翁';
exportfunction setName(name){
    name = name;
}
// dynamic2.js
import{ name, setName }from'./dynamic1.js'
console.log(name);// 桃翁
setName('不要脸');
console.log(name);// 不要脸
```

奇迹般的发现在 dynamic2.js 模块中可以修改 dynamic1.js 模块里面的值, 并且反应到 name 绑定上（这个是重点，这个反应到了消费者模块）, 所以我们把导入的变量叫做绑定。

在生产者模块导出的变量与消费者模块导入的变量会有一个绑定关系，无论前者或者后者发生改变，都会互相影响。

> 注意区分在一个文件或模块中基本类型的赋值，两者是互不影响的。

##### 模块不会重复执行

这个特性比较好理解，就是如果从一个生产者模块中分别导入绑定，而不是一次性导入，生产者模块不会执行多次。

```javascript
// noRepeat1.js
exportlet name ='桃翁';
exportlet age ='22';
console.log('我正在执行。。。');
// noRepeat2.js
import{ name }from'./noRepeat1.js';
import{ age }from'./noRepeat1.js';
console.log(name);
console.log(age);
// 结果
// 我正在执行。。。
// 桃翁
// 22
```

虽然导入了两次，但是 noRepeat1.js 只有执行一次。若同一个应用（注意是同一个应用不是模块）中导入同一个模块，则那些模块都会使用一个模块实例，意思就是说是一个单例。