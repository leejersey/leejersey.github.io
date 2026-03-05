---
title: "javascript数据结构-栈"
date: 2019-01-21
---

## 栈的定义

栈是一种特殊的线性表，仅能够在栈顶进行操作，有着后进先出的特点

## 实现栈

```js
function Stack(){
    var items = [] //使用数组存储数据
    
    this.push = function(item){
        items.push(item)
    }
    
    this.pop = function(){
        return items.pop()
    }
    
    this.top = function(){
        return items[items.length-1]
    }
    
    this.isEmpty = function(){
        return items.length == 0;
    }
    
    this.size = function(){
        return items.length
    }
    
    this.clear = function(){
        items = []
    }
}
```

## 应用

1. 

1. 
2. 
3.