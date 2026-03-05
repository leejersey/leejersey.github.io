---
title: "理解ES6 高阶箭头函数"
date: 2018-12-28
---

## 什么是高阶函数

定义：

- 接受1个或多个函数作为参数
- 返回函数类型

常规ES6箭头函数用法：(返回值类型)

```javascript
const square = x => x * x;
```

高阶写法：

```javascript
const add = x => y => y+x;
```

## 理解语法

ES5实现高阶函数，也叫柯里化：

```javascript
function add(x){
  return function(y){
    return y + x;
  };
}

var addTwo = add(2);
addTwo(3);          // => 5
add(10)(11);        // => 21
```

add函数接受x，返回一个函数接受y返回y＋x。如何用箭头函数实现同样功能呢？我们知道：

- 箭头函数体是表达式，并且
- 箭头函数隐式返回表达式

所以为了实现高阶函数，我们可以使箭头函数的函数体为另一个箭头函数：

```javascript
const add = x => y => y + x;
```

### 应用

```javascript
const has = p => o => o.hasOwnProperty(p);
const sortBy = p => (a, b) => a[p] > b[p];

let result;
let users = [
  { name: 'Qian', age: 27, pets : ['Bao'], title : 'Consultant' },
  { name: 'Zeynep', age: 19, pets : ['Civelek', 'Muazzam'] },
  { name: 'Yael', age: 52, title : 'VP of Engineering'}
];

result = users
  .filter(has('pets'))
  .sort(sortBy('age'));
```

## 优势

- 减少代码重复
- 提高代码重用性
- 更容易阅读的代码

## redux中compose函数

```javascript
export default function compose(...funcs) {
  if (funcs.length === 0) {
    return arg => arg
  }

  if (funcs.length === 1) {
    return funcs[0]
  }

  return funcs.reduce((a, b) => (...args) => a(b(...args)))
}
```

等价：

```javascript
function compose(...funcs){
	return funcs.reduce((a, b) => {
		return (...args) => {
			return a(b(...args))
		}
	})
}
```

### 参考

1.