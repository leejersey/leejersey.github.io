---
title: "React Fiber 架构学习"
date: 2018-10-07
---

前言

React Fiber这个点分享的不多。今日早读文章由腾讯@张臣投稿分享。

> @张臣，现就职于腾讯，负责浏览器前端开发相关工作

正文从这开始～～

> 注：以下内容为查看 react 源代码及相关参考文章后自己的理解

#### react 为什么要花两年时间重构 diff 算法？

主要目的为了提升性能，解决复杂交互场景下，一次 setState 需要同时更新非常多 DOM 元素时，造成页面卡顿的现象，比如用户的输入不能即时响应，动画不连续，页面拖动迟缓等掉帧现象。

先看直观的例子，分别采用不同的架构，每次更新非常多 dom 元素时，动画流畅情况：

[https://claudiopro.github.io/react-fiber-vs-stack-demo/stack.html](https://claudiopro.github.io/react-fiber-vs-stack-demo/stack.html)

[https://claudiopro.github.io/react-fiber-vs-stack-demo/fiber.html](https://claudiopro.github.io/react-fiber-vs-stack-demo/fiber.html)

#### 造成页面卡顿的原因

FPS 决定页面流畅度，即每秒的帧数，最优的帧率是 60，即 16.5ms 左右渲染一次。卡顿的现象可以通过访问页面时直观的感受，或更精确的工具来看 FPS 值。

##### 1. chrome 开发者工具 performance 调试面板

![](https://mmbiz.qpic.cn/mmbiz_jpg/meG6Vo0MevhsmIrSQOicGaFGAM8mh1f6I41EiasyetABWApHI8gcCYu7WiaIf4xRL4ExXDIq9WGWHhWJibET77UlbQ/640?wx_fmt=jpeg&tp=webp&wxfrom=5&wx_lazy=1&wx_co=1)
可以通过绿色的小方块看到每帧的执行时间和帧数。

##### 2. chrome FPS 扩展工具

![](https://mmbiz.qpic.cn/mmbiz_jpg/meG6Vo0MevhsmIrSQOicGaFGAM8mh1f6IIaffEyYuXbcNfFIWlydOib1JKiaPmibDwu1AvNH1ZYzOKnwx51GO6Dicmw/640?wx_fmt=jpeg&tp=webp&wxfrom=5&wx_lazy=1&wx_co=1)

##### 3. 通过 requestAnimationFrame API 计算 FPS

```
const getFpsAndFrame =()=>{
  let lastTime = performance.now();
  let lastFameTime = performance.now();
  let frame =0;
  let fps =0;

  const loop =()=>{
    const now =  performance.now();
    const fs =(now - lastFameTime);

    lastFameTime = now;
    fps =Math.round(1000/ fs);
    frame++;

    if(now - lastTime >1000){
      console.log({
        fps,
        frame,
      });

      frame =0;
      lastTime = now;
    };

    window.requestAnimationFrame(loop);
  }

  window.requestAnimationFrame(loop);
}
```

为了保证页面的流畅度，理想的情况下是每次程序执行的时间控制在
 16.5ms 左右，由于 JavaScript 在浏览器的主线程上运行，与样式计算、布局以及许多情况下的绘制一起运行。如果
JavaScript 运行时间过长，就会阻塞这些其他工作，导致掉帧，表现为页面卡顿。

#### Fiber 之前架构卡顿的原因

React 中调用 render() 和 setState() 方法进行渲染和更新时，主要包含两个阶段：

调度阶段(Reconciler)： Fiber 之前的 reconciler（被称为 Stack reconciler）是自顶向下的递归算法，遍历新数据生成新的Virtual DOM，通过 Diff 算法，找出需要更新的元素，放到更新队列中去。

渲染阶段(Renderer)： 根据所在的渲染环境，遍历更新队列，调用渲染宿主环境的 API, 将对应元素更新渲染。在浏览器中，就是更新对应的DOM元素，除浏览器外，渲染环境还可以是 Native、WebGL 等等。

Fiber
 之前的调度策略 Stack Reconciler，这个策略像函数调用栈一样，递归遍历所有的 Virtual DOM 节点，进行
Diff，一旦开始无法中断，要等整棵 Virtual DOM
树计算完成之后，才将任务出栈释放主线程。而浏览器中的渲染引擎是单线程的，除了网络操作，几乎所有的操作都在这个单线程中执行，此时如果主线程上用户交互、动画等周期性任务无法立即得到处理，影响体验。

#### Fiber 架构如何优化卡顿

Fiber

改进思路是将调度阶段拆分成一系列小任务，每次加入一个节点至任务中，做完看是否还有时间继续下一个任务，有的话继续，没有的话把自己挂起，主线程不忙的时候再继续。每次只做一小段，做完一段就把时间控制权交还给主线程，而不像之前长时间占用，从而实现对任务的暂停、恢复、复用灵活控制，这样主线程上的用户交互及动画可以快速响应，从而解决卡顿的问题。

#### React Fiber 架构

##### 调度拆分为小任务

背后支持 API 是 requestIdleCallback，为了兼容所有平台，facebook 单独实现了其功能，作为一个独立的 npm 包使用 react-schedule

> 其作用是会在浏览器空闲时期依次调用函数， 这就可以在主事件循环中执行后台或低优先级的任务，而且不会对像动画和用户交互这样延迟触发而且关键的事件产生影响。函数一般会按先进先调用的顺序执行，除非函数在浏览器调用它之前就到了它的超时时间。

简化后的大致流程图如下：
![](/2018/10/07/React-Fiber-架构学习/gif;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQImWNgYGBgAAAABQABh6FO1AAAAABJRU5ErkJggg==)

##### Fiber Node 及 Fiber Tree

从流程图上看到会有 Fiber Node 节点，这个是在 react 生成的 Virtual Dom 基础上增加的一层数据结构，主要是为了将递归遍历转变成循环遍历，配合 requestIdleCallback API, 实现任务拆分、中断与恢复。

为了实现循环遍历，Fiber Node 上携带了更多的信息， 其数据结构如下所示：

```
export type Fiber={
  tag:TypeOfWork,
  key:null|string,
  type: any,

  return:Fiber|null,
  child:Fiber|null,
  sibling:Fiber|null,

  effectTag:TypeOfSideEffect,
  nextEffect:Fiber|null,
  firstEffect:Fiber|null,
  lastEffect:Fiber|null,

  alternate:Fiber|null,
  stateNode: any,
  ...
}
```

每一个 Fiber Node 节点与 Virtual Dom 一一对应，所有 Fiber Node 连接起来形成 Fiber tree, 是个单链表树结构，如下图所示：
![](https://mmbiz.qpic.cn/mmbiz_jpg/meG6Vo0MevhsmIrSQOicGaFGAM8mh1f6IU1ffNIqicFVjogiakq3ty1RYiaLlNbmop2GhOEspST0WJHnlhxoRG0MpA/640?wx_fmt=jpeg&tp=webp&wxfrom=5&wx_lazy=1&wx_co=1)

##### reconciliation 处理过程

当执行 setState() 或首次 render() 时，进入工作循环，循环体中处理的单元为 Fiber Node, 即是拆分任务的最小单位，从根节点开始，自顶向下逐节点构造 workInProgress tree（构建中的新 Fiber Tree）。

```
function workLoop(isAsync){
  if(!isAsync){
    // Flush all expired work.
    while(nextUnitOfWork !==null){
      nextUnitOfWork = performUnitOfWork(nextUnitOfWork);
    }
  }else{
    // Flush asynchronous work until the deadline runs out of time.
    while(nextUnitOfWork !==null&&!shouldYield()){
      nextUnitOfWork = performUnitOfWork(nextUnitOfWork);
    }

    if(enableProfilerTimer){
      // If we didn&apos;t finish, pause the "actual" render timer.
      // We&apos;ll restart it when we resume work.
      pauseActualRenderTimerIfRunning();
    }
  }
}
```

每个工作处理单元做的事情，由 beginWork(), completeUnitOfWork() 两部分构成。

```
function performUnitOfWork(workInProgress){
  // 简化后逻辑
  varnext=void0;
  var current = workInProgress.alternate;

  next= beginWork(current, workInProgress, nextRenderExpirationTime);

  if(next===null){
    next= completeUnitOfWork(workInProgress);
  }

  ReactCurrentOwner.current =null;

  returnnext;
}
```

beginWork() 主要做的事情是从顶向下生成所有的 Fiber Node，并标记 Diff, 不包括兄弟节点，每个 Fiber Node 的处理过程根据组件类型略有差异，以 ClassComponent 为例：

- 
如果当前节点不需要更新，直接把子节点clone过来，跳到5，要更新的话标记更新类型

- 
更新当前节点状态（props, state, context等）

- 
调用shouldComponentUpdate()

- 
调用组件实例方法 render() 获得新的子节点，并为子节点创建 Fiber Node（创建过程会尽量复用现有 Fiber Node，子节点增删也发生在这里）

- 
如果没有产生 child fiber，进入下一阶段 completeUnitOfWork

- 
completeUnitOfWork() 当没有子节点，开始遍历兄弟节点作为下一个处理单元，处理完兄弟节点开始向上回溯，真到再次回去根节点为止，将收集向上回溯过程中的所有 diff，拿到 diff 后开始进入 commit 阶段。

整个过程采用深度优先遍历算法，如下图所示：
![](/2018/10/07/React-Fiber-架构学习/gif;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQImWNgYGBgAAAABQABh6FO1AAAAABJRU5ErkJggg==)
构建
 workInProgress tree 的过程就是 diff 的过程，通过 requestIdleCallback
来调度执行一组任务，每完成一个任务后回来看看有没有插队的（更紧急的），把时间控制权交还给主线程，直到下一次
requestIdleCallback 回调再继续构建workInProgress tree。

#### 对生命周期的影响

Fiber 之前的生命周期如下：
![](/2018/10/07/React-Fiber-架构学习/gif;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQImWNgYGBgAAAABQABh6FO1AAAAABJRU5ErkJggg==)
Fiber 架构下，生命周期做了较大调整，不再推荐使用下面三个生命周期，代码中也给出了替代建议：

```
var LIFECYCLE_SUGGESTIONS ={
  UNSAFE_componentWillMount:&apos;componentDidMount&apos;,
  UNSAFE_componentWillReceiveProps:&apos;static getDerivedStateFromProps&apos;,
  UNSAFE_componentWillUpdate:&apos;componentDidUpdate&apos;
};
```

如果项目中依赖了这些生命周期，升级过渡还需要做一些修改，如果继续使用，会给出警告提示，并在下个版本 17 中彻底移除。

```
lowPriorityWarning(
  false,
  &apos;componentWillUpdate is deprecated and will be removed in the next major version. &apos;+
    &apos;Use componentDidUpdate instead. As a temporary workaround, &apos;+
    &apos;you can rename to UNSAFE_componentWillUpdate.&apos;+
    &apos;\n\nPlease update the following components: %s&apos;+
    &apos;\n\nLearn more about this warning here:&apos;+
    &apos;\nhttps://fb.me/react-async-component-lifecycle-hooks&apos;,
  sortedNames,
);
```

为什么要做这么大的改动呢，由于在
 reconciler 阶段，在更新过程中，任务按照节点为单位拆分成了一个个小工作单元，在 render 前可能会中断或恢复，导致在
render 前的这些生命周期在进行一次更新时存在多次执行的情况，可能得到与预期不一致的结果。Fiber
给出的解决方案是增加了两个新的生命周期：

- 
static getDerivedStateFromProps

- 
getSnapshotBeforeUpdate

getDerivedStateFromProps: 是一个静态方法，主要取代 ComponentWillXXX 生命周期，解除此类生命周期带来的副作用。

getSnapshotBeforeUpdate: 会在 render 之后执行，而执行之时 DOM 元素还没有被更新，给了一个机会去获取 DOM 信息，计算得到一个 snapshot。

最后 Fiber 体系下的生命周期变成如下所示：
![](/2018/10/07/React-Fiber-架构学习/gif;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQImWNgYGBgAAAABQABh6FO1AAAAABJRU5ErkJggg==)
同时 react 官方也给出修改建议，Update on Async Rendering，最好所有组件都使用受控组件，避免并行处理负作用，新的生命周期详细使用场景：React.Component。

#### react、react-reconciler、renderer 三者关系

react基础模块： react 基础 API 及组件类，组件内定义 render 、setState 方法和生命周期相关的回调方法，相关 API 如下：

```
constReact={
  Children:{},

  createRef,
  Component,
  PureComponent,

  createContext,
  forwardRef,

  Fragment: REACT_FRAGMENT_TYPE,
  StrictMode: REACT_STRICT_MODE_TYPE,
  unstable_AsyncMode: REACT_ASYNC_MODE_TYPE,
  unstable_Profiler: REACT_PROFILER_TYPE,

  createElement: __DEV__ ? createElementWithValidation : createElement,
  cloneElement: __DEV__ ? cloneElementWithValidation : cloneElement,
  createFactory: __DEV__ ? createFactoryWithValidation : createFactory,
  isValidElement: isValidElement,
};
```

渲染模块：
 针对不同宿主环境采用不同的渲染方法实现，如 react-dom, react-webgl, react-native, react-art,
依赖 react-reconciler, 注入相应的渲染方法到 reconciler 中，react-dom 中相关的 API 如下：

```
constReactDOM:Object={
  createPortal,

  findDOMNode(
    componentOrElement:Element|?React$Component,
  ):null|Element|Text{},

  hydrate(element:React$Node, container:DOMContainer, callback:?Function){},

  render(
    element:React$Element,
    container:DOMContainer,
    callback:?Function,
  ){},

  unstable_renderSubtreeIntoContainer(){},

  unmountComponentAtNode(container:DOMContainer){},

  unstable_batchedUpdates:DOMRenderer.batchedUpdates,

  unstable_deferredUpdates:DOMRenderer.deferredUpdates,

  unstable_interactiveUpdates:DOMRenderer.interactiveUpdates,

  flushSync:DOMRenderer.flushSync,

  unstable_flushControlled:DOMRenderer.flushControlled,
}
```

react-reconciler：
 核心模块，负责调度算法及 Fiber tree diff, 连接 react 及 renderer 模块，注入 setState 方法到
component 实例中，在 diff 阶段执行 react 组件中 render 方法，在 patch 阶段执行 react
组件中生命周期回调并调用 renderer 中注入的相应的方法渲染真实视图结构。

将
 react, react-reconciler, renderer 分离后，具有更好的通用性，针对不同的平台定义相应的 renderer
实现即可，在实际应用时，react-reconciler 是不可见的，被 renderer 中依赖。三部分相互调用关系如下：
![](/2018/10/07/React-Fiber-架构学习/gif;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQImWNgYGBgAAAABQABh6FO1AAAAABJRU5ErkJggg==)

#### 总结

注： 前面所讲的 React Fiber 架构中最重要的 Diff 算法中任务拆分渲染机制，也叫 Async Rendering, 如果项目中已经升级到 react 最新版本，在不变动项目代码默认还是采用的是同步渲染机制，只是使用了新的架构，如下：

```
// 调用 ReactDom.render() 方法时会调用此方法
// 默认 isAsync = false
function legacyCreateRootFromDOMContainer(container, forceHydrate){
  // ...

  // Legacy roots are not async by default.
  var isAsync =false;
  returnnewReactRoot(container, isAsync, shouldHydrate);
}
```

如果要开启异步渲染，现在 API 还没有完全稳定，如下：

```
// 首次 render 阶段
importReactfrom&apos;react&apos;
importReactDOMfrom&apos;react-dom&apos;
importAppfrom&apos;./App&apos;
constAsyncMode=React.unstable_AsyncMode
ReactDOM.render(
  
    
  ,
  document.getElementById(&apos;root&apos;)
)
// update 阶段
ReactDOM.unstable_deferredUpdates(()=>{
  this.setState((state)=>({
    value: state.value +1
  }))
})
```

一旦开启了异步渲染，需要注意生命周期变化带来的影响，移除掉 render 前的生命周期带来的副作用。

本文的主要内容也就仅仅介绍 Fiber 架构中如何实现任务切分调度这一小部分。

16 大版本主要更新还包括以下这些新特性：

- 
render / 纯组件能够 return 任何数据结构，

- 
CreatePortal API，更好的处理 Dialog 这种场景组件

- 
新的 context api，尝试代替一部分 redux 的职责

- 
异步渲染/时间切片(time slicing)，成倍提高性能

- 
componentDidCatch，错误边界，框架层面上提高用户 debug 的能力

- 
网络请求 IO(Suspense)，更好的处理异步网络 IO

#### 参考

- 
requestIdleCallback

- 
React Fiber Architecture

- 
Update on Async Rendering

- 
Lin Clark - A Cartoon Intro to Fiber - React Conf 2017

- 
You Probably Don’t Need Derived State

- 
Beyond React 16 by Dan Abramov - JSConf Iceland

关于本文
作者：@张臣
原文：[https://zhuanlan.zhihu.com/p/44942360](https://zhuanlan.zhihu.com/p/44942360)