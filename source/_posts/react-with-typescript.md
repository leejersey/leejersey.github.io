---
title: "react with typescript"
date: 2019-01-08
---

## 编写第一个 TSX 组件

```jsx
import React from 'react'
import ReactDOM from 'react-dom'

const App = () => {
 return (
  Hello world
 )
}

ReactDOM.render(, document.getElementById('root')
```

上述代码运行时会出现以下错误

```
Cannot find module &apos;react&apos;
Cannot find module &apos;react-dom&apos;
```

错误原因是由于 React 和 React-dom 并不是使用 TS 进行开发的，所以 TS 不知道 React、 React-dom 的类型，以及该模块导出了什么，此时需要引入 .d.ts 的声明文件，比较幸运的是在社区中已经发布了这些常用模块的声明文件 DefinitelyTyped 。

## 安装 `React`、 `React-dom` 类型定义文件

##### 使用 yarn 安装

```shell
yarn add @types/react
yarn add @types/react-dom
```

##### 使用 npm 安装

```shell
npm i @types/react -s
npm i @types/react-dom -s
```

有状态组件开发
我们定义一个 App 有状态组件，props、 state 如下。

Props

| props | 类型 | 是否必传 |
| --- | --- | --- |
| color | string | 是 |
| size | string | 否 |

State

| props | 类型 |
| --- | --- |
| count | string |

## 使用 TSX 我们可以这样写

```typescript
import * as React from 'react'

interface IProps {
  color: string,
  size?: string,
}
interface IState {
  count: number,
}
class App extends React.Component {
  public state = {
    count: 1,
  }
  public render () {
    return (
      Hello world
    )
  }
}
```

TypeScript 可以对 JSX 进行解析，充分利用其本身的静态检查功能，使用泛型进行 Props、 State 的类型定义。定义后在使用 this.state 和 this.props 时可以在编辑器中获得更好的智能提示，并且会对类型进行检查。

那么 Component 的泛型是如何实现的呢，我们可以参考下 React 的类型定义文件 node_modules/@types/react/index.d.ts。

在这里可以看到 Component 这个泛型类， P 代表 Props 的类型， S 代表 State 的类型。

```typescript
class Component {

    readonly props: Readonly & Readonly;

    state: Readonly;

}
```

Component 泛型类在接收到 P ， S 这两个泛型变量后，将只读属性 props 的类型声明为交叉类型 Readonly<{ children?: ReactNode }> & Readonly

; 使其支持 children 以及我们声明的 color 、 size 。

通过泛型的类型别名 Readonly 将 props 的所有属性都设置为只读属性。

Readonly 实现源码 node_modules/typescript/lib/lib.es5.d.ts 。

由于 props 属性被设置为只读，所以通过 this.props.size = ‘sm’ 进行更新时候 TS 检查器会进行错误提示，Error:(23, 16) TS2540: Cannot assign to ‘size’ because it is a constant or a read-only property

## 无状态组件开发

Props

| props | 类型 | 是否必传 |
| --- | --- | --- |
| children | ReactNode | 否 |
| onClick | function | 是 |

SFC类型

在 React 的声明文件中 已经定义了一个 SFC 类型，使用这个类型可以避免我们重复定义 children、 propTypes、 contextTypes、 defaultProps、displayName 的类型。

使用 `SFC` 进行无状态组件开发。

```typescript
import { SFC } from 'react'
import { MouseEvent } from 'react'
import * as React from 'react'
interface IProps {
  onClick (event: MouseEvent): void,
}
const Button: SFC = ({onClick, children}) => {
  return (
    
      { children }
    
  )
}
export default Button
```

## 事件处理

我们在进行事件注册时经常会在事件处理函数中使用 `event` 事件对象，例如当使用鼠标事件时我们通过 `clientX`、`clientY` 去获取指针的坐标。

大家可以想到直接把 `event` 设置为 `any` 类型，但是这样就失去了我们对代码进行静态检查的意义。

```typescript
function handleEvent (event: any) {
  console.log(event.clientY)
}
```

试想下当我们注册一个 Touch 事件，然后错误的通过事件处理函数中的 event 对象去获取其 clientY 属性的值，在这里我们已经将 event 设置为 any 类型，导致 TypeScript 在编译时并不会提示我们错误， 当我们通过 event.clientY 访问时就有问题了，因为 Touch 事件的 event 对象并没有 clientY 这个属性。

通过 interface 对 event 对象进行类型声明编写的话又十分浪费时间，幸运的是 React 的声明文件提供了 Event 对象的类型声明。

#### Event 事件对象类型

常用 Event 事件对象类型：

ClipboardEvent 剪贴板事件对象

DragEvent 拖拽事件对象

ChangeEvent Change 事件对象

KeyboardEvent 键盘事件对象

MouseEvent 鼠标事件对象

TouchEvent 触摸事件对象

WheelEvent 滚轮事件对象

AnimationEvent 动画事件对象

TransitionEvent 过渡事件对象

#### 实例：

```typescript
import { MouseEvent } from 'react'

interface IProps {

  onClick (event: MouseEvent): void,
}
```

#### 事件处理函数类型

当我们定义事件处理函数时有没有更方便定义其函数类型的方式呢？答案是使用 React 声明文件所提供的 EventHandler 类型别名，通过不同事件的 EventHandler 的类型别名来定义事件处理函数的类型。

`EventHandler` 接收 `E` ，其代表事件处理函数中 `event` 对象的类型。

`bivarianceHack` 为事件处理函数的类型定义，函数接收一个 `event` 对象，并且其类型为接收到的泛型变量 `E` 的类型, 返回值为 `void`。

```typescript
interface IProps {
  onClick : MouseEventHandler,
}
```

## Promise 类型

在做异步操作时我们经常使用 async 函数，函数调用时会 return 一个 Promise 对象，可以使用 then 方法添加回调函数。

Promise 是一个泛型类型，T 泛型变量用于确定使用 then 方法时接收的第一个回调函数（onfulfilled）的参数类型。

实例：

```typescript
interface IResponse {
  message: string,
  result: T,
  success: boolean,
}
async function getResponse (): Promise> {
  return {
    message: '获取成功',
    result: [1, 2, 3],
    success: true,
  }
}
getResponse()
  .then(response => {
    console.log(response.result)
  })
```

我们首先声明 IResponse 的泛型接口用于定义 response 的类型，通过 T 泛型变量来确定 result 的类型。

然后声明了一个 异步函数 getResponse 并且将函数返回值的类型定义为 Promise> 。

最后调用 getResponse 方法会返回一个 promise 类型，通过 then 调用，此时 then 方法接收的第一个回调函数的参数 response 的类型为，{ message: string, result: number[], success: boolean} 。

## 工具泛型使用技巧

##### typeof

一般我们都是先定义类型，再去赋值使用，但是使用 `typeof` 我们可以把使用顺序倒过来。

```typescript
const options = {
  a: 1
}
type Options = typeof options
```

##### 使用字符串字面量类型限制值为固定的字符串参数

限制 `props.color` 的值只可以是字符串 `red`、`blue`、`yellow` 。

```typescript
interface IProps {
  color: 'red' | 'blue' | 'yellow',
}
```

##### 使用数字字面量类型限制值为固定的数值参数

限制 `props.index` 的值只可以是数字 `0`、 `1`、 `2` 。

```typescript
interface IProps {
 index: 0 | 1 | 2,
}
```

##### 使用 `Partial` 将所有的 `props` 属性都变为可选值

如果 `props` 所有的属性值都是可选的我们可以借助 `Partial` 这样实现。

```typescript
import { MouseEvent } from 'react'
import * as React from 'react'
interface IProps {
  color: 'red' | 'blue' | 'yellow',
  onClick (event: MouseEvent): void,
}
const Button: SFC> = ({onClick, children, color}) => {
  return (
    
      { children }
    
  )
```

##### 使用 `Required` 将所有 `props` 属性都设为必填项

持续收集…

作者：花生毛豆-
来源：CSDN
原文：[https://blog.csdn.net/s2096828/article/details/83744677](https://blog.csdn.net/s2096828/article/details/83744677)