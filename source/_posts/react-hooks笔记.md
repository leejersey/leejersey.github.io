---
title: "react hooks笔记"
date: 2020-05-13
---

## React hook特性

Hook 是 React 16.8 的新增特性。它可以让你在不编写 class 的情况下使用 state 以及其他的 React 特性。

### useState

使用案例，解构赋值很简单

```javascript
import React, { useState } from 'react';

function Example() {
  // 声明一个叫 "count" 的 state 变量
  const [count, setCount] = useState(0);

  return (
    
      
You clicked {count} times

       setCount(count + 1)}>
        Click me
      
    
  );
}
```

#### 获取上一次的状态

### useEffect

Effect Hook 可以让你在函数组件中执行副作用操作

```javascript
import React, { useState, useEffect } from 'react';

function Example() {
  const [count, setCount] = useState(0);

  // Similar to componentDidMount and componentDidUpdate:
  useEffect(() => {
    // Update the document title using the browser API
    document.title = `You clicked ${count} times`;
  });

  return (
    
      You clicked {count} times

       setCount(count + 1)}>
        Click me
      
    
  );
}
```

> 提示
> 如果你熟悉 React class 的生命周期函数，你可以把 useEffect Hook 看做 componentDidMount，componentDidUpdate 和 componentWillUnmount 这三个函数的组合。

#### effect调用控制

useEffect第二个参数为空：第一次渲染之后和每次组件更新之后，都会执行effect
useEffect第二个参数为[]：只有组件第一次渲染之后会执行effect
useEffect第二个参数为[ count, time ]：组件第一渲染后会执行effect, count或time变化时也会执行effect

#### 清除effect

effect 中返回一个清除函数，组件卸载的时候执行清除操作

```javascript
function FriendStatus(props) {
  // ...
  useEffect(() => {
    // ...
    ChatAPI.subscribeToFriendStatus(props.friend.id, handleStatusChange);
    return () => {
      ChatAPI.unsubscribeFromFriendStatus(props.friend.id, handleStatusChange);
    };
  });
```

## Hook 规则（注意）

只在函数组件内部最顶层使用 Hook
不要在循环，条件或嵌套函数中调用 Hook
只在 React 函数组件中调用 Hook

持续更新。。。