---
title: "理解useMemo和useCallback"
date: 2020-05-22
---

## 回顾

在hooks诞生之前，如果组件包含内部state，我们都是基于class的形式来创建组件。当时我们也知道，react中，性能的优化点在于：

1. 
2. 

基于上面的两点，我们通常的解决方案是：使用immutable进行比较，在不相等的时候调用setState；在shouldComponentUpdate中判断前后的props和state，如果没有变化，则返回false来阻止更新。

在hooks出来之后，我们能够使用function的形式来创建包含内部state的组件。但是，使用function的形式，失去了上面的shouldComponentUpdate，我们无法通过判断前后状态来决定是否更新。而且，在函数组件中，react不再区分mount和update两个状态，这意味着函数组件的每一次调用都会执行其内部的所有逻辑，那么会带来较大的性能损耗。因此useMemo 和useCallback就是解决性能问题的杀手锏。

## 对比

useMemo和useCallback都会在组件第一次渲染的时候执行，之后会在其依赖的变量发生改变时再次执行；并且这两个hooks都返回缓存的值，useMemo返回缓存的变量，useCallback返回缓存的函数。

## useMemo

```javascript
import React, {useState, useMemo} from "react";
import "./styles.css";

export default function App() {
  const [count, setCount] = useState(1);
    const [val, setValue] = useState('');
    const expensive = useMemo(() => {
        console.log('compute');
        let sum = 0;
        for (let i = 0; i 
        
#### {count}-{expensive}

        {val}
        
             setCount(count + 1)}>+c1
             setValue(event.target.value)}/>
        
    ;
}
```

使用useMemo来执行昂贵的计算，然后将计算值返回，并且将count作为依赖值传递进去。这样，就只会在count改变的时候触发expensive执行，在修改val的时候，返回上一次缓存的值。

## useCallback

```javascript
import React, { useState, useCallback, useEffect } from 'react';
function Parent() {
    const [count, setCount] = useState(1);
    const [val, setVal] = useState('');
 
    const callback = useCallback(() => {
        return count;
    }, [count]);
    return 
        
#### {count}

        
        
             setCount(count + 1)}>+
             setVal(event.target.value)}/>
        
    ;
}
 
function Child({ callback }) {
    const [count, setCount] = useState(() => callback());
    useEffect(() => {
        setCount(callback());
    }, [callback]);
    return 
        {count}
    
}
```

有一个父组件，其中包含子组件，子组件接收一个函数作为props；通常而言，如果父组件更新了，子组件也会执行更新；但是大多数场景下，更新是没有必要的，我们可以借助useCallback来返回函数，然后把这个函数作为props传递给子组件；这样，子组件就能避免不必要的更新。