---
title: "Object.prototype.toString.call()方法"
date: 2018-12-10
---

使用Object.prototype上的原生toString()方法判断数据类型，使用方法如下：
**Object.prototype.toString.call(value)** 

1. 
2. 

```javascript
// 函数类型 
Function fn(){console.log(“test”);} 
Object.prototype.toString.call[^1];//”[object Function]()” 
// 日期类型 
var date = new Date(); 
Object.prototype.toString.call(date);//”[object Date]()” 
// 数组类型 
var arr = [1,2,3](); 
Object.prototype.toString.call(arr);//”[object Array]()” 
// 正则表达式 
var reg = /[hbc]()at/gi; 
Object.prototype.toString.call(arr);//”[object Array]()” 
// 自定义类型 
function Person(name, age) { 
this.name = name; 
this.age = age; 
} 
var person = new Person("Rose", 18); 
Object.prototype.toString.call(arr); //”[object Object]()” 
// 很明显这种方法不能准确判断person是Person类的实例，而只能用instanceof 操作符来进行判断，如下所示： 
console.log(person instanceof Person);//输出结果为true
```

1. 

```javascript
var isNativeJSON = window.JSON && Object.prototype.toString.call(JSON); 
console.log(isNativeJSON);//输出结果为”[object JSON]()”说明JSON是原生的，否则不是；
```

注意：Object.prototype.toString()本身是允许被修改的，而我们目前所讨论的关于Object.prototype.toString()这个方法的应用都是假设toString()方法未被修改为前提的。