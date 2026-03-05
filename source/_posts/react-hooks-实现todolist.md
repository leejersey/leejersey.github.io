---
title: "react hooks 实现todolist"
date: 2020-05-19
---

最近学习了一些react hooks相关的东西，拿决定拿todolist练手

代码地址：[https://github.com/leejersey/hooks-todo](https://github.com/leejersey/hooks-todo)

无意间发现一个好用的在线编辑工具codesandbox，能在线编辑代码并且同步到github，真的不错:[https://codesandbox.io/dashboard](https://codesandbox.io/dashboard)

### 组件拆分

![WX20200519-100057@2x](/2020/05/19/react-hooks-实现todolist-1/WX20200519-100057@2x-1.png)

### 代码：

Todolist:

```javascript
import React, { memo, useCallback, useState, useEffect } from "react";
import Addtodo from './Addtodo';
import Todos from './Todos';

const Todolist= memo(function Todolist() {
    const [todos, setTodos ] = useState([]);
    const addTodo = useCallback((todo) => {
        setTodos(todos => [...todos,todo]);
    },[])

    const removeTodo = useCallback((id) => {
        setTodos(todos => todos.filter(todo => {
            return todo.id !== id;
        }))
    },[])

    const toggleTodo = useCallback((id) => {
        setTodos(todos => todos.map(todo => {
            return todo.id === id ? 
            { 
                ...todo, 
                complete: !todo.complete
            }:
            {...todo}
        }))
     },[])

     useEffect(() => {
        const todos = JSON.parse(window.localStorage.getItem('todos')) || [];
        setTodos(todos);
    },[])

    useEffect(()=> {
        window.localStorage.setItem('todos',JSON.stringify(todos))
    },[todos])
  return ( 
    
        
        
    
  );
})

export default Todolist;
```

Addtodo:

```javascript
import React, { memo, useRef } from "react";

let idSeq = 0;
const Addtodo= memo(function Addtodo(props) {
    const { addTodo } = props;
    const inputRef = useRef();
    const onSubmit = (e) => {
        e.preventDefault();
        const newText = inputRef.current.value.trim();
        if(newText.length>0){
            addTodo({
                id: ++idSeq,
                text: newText,
                complete:false,
            })
        }
        inputRef.current.value = '';
    }
  return (
    
        
             
        
    
  );
})

export default Addtodo;
```

Todos:

```javascript
import React, { memo } from "react";
import TodoItem from './Todoitem';

const Todos = memo(function Todos(props) {
    const { todos , removeTodo, toggleTodo} = props;
  return (
    
        {
            todos.map(todo => {
                return (
                    
                )
            })
        }
    

  );
})

export default Todos;
```

TodoItem

```
import React, { memo } from "react";

const TodoItem =  memo(function TodoItem (props) {
    const { todo: {
        id,
        text,
        complete
    } , removeTodo, toggleTodo} = props
    const  onChange =() => {
       toggleTodo(id);
    }

    const onRemove = () => {
        removeTodo(id);
    }
    return (
        
            
            {text}
            删除
        
    )
})

export default TodoItem
```

### 总结

该demo对react hooks新特性有一定的展示：
`memo, useCallback, useState, useEffect，useRef`