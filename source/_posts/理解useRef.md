---
title: "理解useRef"
date: 2021-05-12
---

## 什么是 useRef

首先, 我们要实现一个需求 – 点击 button 的时候 input 设置焦点.

createRef API

```
import React from "react";
import "./styles.css";
import { createRef } from "react";

export default function App() {
  const inputElement = createRef();
  const focusInput = () => {
    inputElement.current.focus();
  };
  return (
    
      
      焦距input
    
  );
}
```

同样的, 我们可以使用 useRef 来实现完全相同的结果.

useRef Hook

```
import React from "react";
import "./styles.css";
import { useRef } from "react";

export default function App() {
  const inputElement = useRef();
  const focusInput = () => {
    inputElement.current.focus();
  };
  return (
    
      
      焦距input
    
  );
}
```

## createRef 与 useRef 的区别

useRef 在 react hook 中的作用, 正如官网说的, 它像一个变量, 类似于 this , 它就像一个盒子, 你可以存放任何东西. createRef 每次渲染都会返回一个新的引用，而 useRef 每次都会返回相同的引用。

```
import React, { createRef, useRef } from "react";
import "./styles.css";

const App = () => {
  const [renderIndex, setRenderIndex] = React.useState(1);
  const refFromUseRef = useRef();
  const refFromCreateRef = createRef();

  if (!refFromUseRef.current) {
    refFromUseRef.current = renderIndex;
  }

  if (!refFromCreateRef.current) {
    refFromCreateRef.current = renderIndex;
  }

  return (
    <>
      
Current render index: {renderIndex}

      

        **refFromUseRef** value: {refFromUseRef.current}
      

      

        **refFromCreateRef** value:{refFromCreateRef.current}
      

       setRenderIndex(prev => prev + 1)}>
        Cause re-render
      
    
  );
};

export default App;
```

就算组件重新渲染, 由于 refFromUseRef 的值一直存在(类似于 this ) , 无法重新赋值.