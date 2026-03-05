---
title: "react优化总结"
date: 2019-01-02
---

#### 请慎用setState，因其容易导致重新渲染

既然将数据主要交给了Redux来管理，那就尽量使用Redux管理你的数据和状态state，除了少数情况外，别忘了shouldComponentUpdate也需要比较state。

#### 请将方法的bind一律置于constructor

Component的render里不动态bind方法，方法都在constructor里bind好，如果要动态传参，方法可使用闭包返回一个最终可执行函数。如：showDelBtn(item) { return (e) => {}; }。如果每次都在render里面的jsx去bind这个方法，每次都要绑定会消耗性能。

#### 请只传递component需要的props

传得太多，或者层次传得太深，都会加重shouldComponentUpdate里面的数据比较负担，因此，也请慎用spread attributes（）。

#### 请尽量使用const element

我们可以将不怎么变动，或者不需要传入状态的component写成const element的形式，这样能加快这个element的初始渲染速度。

#### 保证key值唯一

保证key值唯一方便diff算法比较，注意不要用数组的index作为key，原因非唯一性

#### 合理使用shouldComponentUpdate

子组件更新时候对props作出新老数据比对，如果改变了，才render子组件

#### 使用pureComponent

使用pureComponent会默认添加shouldComponentUpdate并进行浅比较

#### 使用Immutablejs

使用不可变的数据来解决数据状态的变化比对，提高性能