---
title: "项目中涉及的immutable方法总结"
date: 2020-05-13
---

#### fromJS

它的功能是将 JS 对象转换为 immutable 对象。

```javascript
import {fromJS} from 'immutable';
const immutableState = fromJS ({
    count: 0
});
```

大家以后会经常在 redux 的 reducer 文件中看到这个 api, 是 immutable 库当中导出的方法。

#### toJS

和 fromJS 功能刚好相反，用来将 immutable 对象转换为 JS 对象。但是值得注意的是，这个方法并没有在 immutable 库中直接导出，而是需要让 immutable 对象调用。比如:

```javascript
const jsObj = immutableState.toJS ();
```

#### get/getIn

用来获取 immutable 对象属性。通过与 JS 对象的对比来体会一下：

```javascript
//JS 对象
let jsObj = {a: 1};
let res = jsObj.a;
//immutable 对象
let immutableObj = fromJS (jsObj);
let res = immutableObj.get ('a');
//JS 对象
let jsObj = {a: {b: 1}};
let res = jsObj.a.b;
//immutable 对象
let immutableObj = fromJS (jsObj);
let res = immutableObj.getIn (['a', 'b']);// 注意传入的是一个数组
```

#### set

用来对 immutable 对象的属性赋值。

```javascript
let immutableObj = fromJS ({a: 1});
immutableObj.set ('a', 2);
```

#### merge

新数据与旧数据对比，旧数据中不存在的属性直接添加，旧数据中已存在的属性用新数据中的覆盖。

```javascript
let immutableObj = fromJS ({a: 1});
immutableObj.merge ({
    a: 2,
    b: 3
});// 修改了 a 属性，增加了 b 属性
```