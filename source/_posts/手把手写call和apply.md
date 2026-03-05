---
title: "手把手写call和apply"
date: 2020-09-16
---

## call

call的作用绑定this和参数，并且执行函数。调用如下：

```
function.call(thisArg, arg1, arg2, ...)
```

实现思路命名为mycall，接受第一个参数thisArg是目标函数执行时的this的值，从第二个可选参数arg1开始的其他参数将作为目标函数执行时的参数。

```javascript
Function.prototype.myCall = function() {
  // 第一个参数是绑定的this
  var thisArg = arguments[0];
  // 接着要判断是不是严格模式
  var isStrict = (function(){return this === undefined}())
  if (!isStrict) {
    // 如果在非严格模式下，thisArg的值是null或undefined，需要将thisArg置为全局对象
    // 如果是其他原始值，需要通过构造函数包装成对象
      var thisArgType = typeof thisArg
      if (thisArgType === 'number') {
       thisArg = new Number(thisArg)
      } else if (thisArgType === 'string') {
        thisArg = new String(thisArg)
      } else if (thisArgType === 'boolean') {
        thisArg = new Boolean(thisArg)
      }
  }
  // 截取从索引1开始的剩余参数
  var invokeParams = [...arguments].slice(1);
  // 接下来要调用目标函数，那么如何获取到目标函数呢？
  // 实际上this就是目标函数，因为myCall是作为一个方法被调用的，this当然指向调用对象，而这个对象就是目标函数
  // 这里做这么一个赋值过程，是为了让语义更清晰一点
  var invokeFunc = this;
  // 此时如果thisArg对象仍然是null或undefined，那么说明是在严格模式下，并且没有指定第一个参数或者第一个参数的值本身就是null或undefined，此时将目标函数当成普通函数执行并返回其结果即可
  if (thisArg === null || thisArg === undefined) {
    return invokeFunc(...invokeParams)
  }
  // 否则，让目标函数成为thisArg对象的成员方法，然后调用它
  // 直观上来看，可以直接把目标函数赋值给对象属性，比如func属性，但是可能func属性本身就存在于thisArg对象上
  // 所以，为了防止覆盖掉thisArg对象的原有属性，必须创建一个唯一的属性名，可以用Symbol实现，如果环境不支持Symbol，可以通过uuid算法来构造一个唯一值。
  var uniquePropName = Symbol(thisArg)
  thisArg[uniquePropName] = invokeFunc
  // 返回目标函数执行的结果
  return thisArg[uniquePropName](...invokeParams)
}
```

## apply

- myApply接受的第二个参数是数组形式。
- 要考虑实际调用时不传第二个参数或者第二个参数不是数组的情况。

```javascript
Function.prototype.myApply = function(thisArg, params) {
  var isStrict = (function(){return this === undefined}())
  if (!isStrict) {
    var thisArgType = typeof thisArg
    if (thisArgType === 'number') {
     thisArg = new Number(thisArg)
    } else if (thisArgType === 'string') {
      thisArg = new String(thisArg)
    } else if (thisArgType === 'boolean') {
      thisArg = new Boolean(thisArg)
    }
  }
  var invokeFunc = this;
  // 处理第二个参数
  var invokeParams = Array.isArray(params) ? params : [];
  if (thisArg === null || thisArg === undefined) {
    return invokeFunc(...invokeParams)
  }
  var uniquePropName = Symbol(thisArg)
  thisArg[uniquePropName] = invokeFunc
  return thisArg[uniquePropName](...invokeParams)
}
```