---
title: "漫谈前端性能，突破React应用瓶颈"
date: 2018-10-07
---

前言

今日早读文章由百度资深开发@Lucas HC投稿分享。

正文从这开始~

性能一直以来是前端开发中非常重要的话题。随着前端能做的事情越来越多，浏览器能力被无限放大和利用：从 web 游戏到复杂单页面应用，从 NodeJS 服务到 web VR/AR、数据可视化，前端工程师总是在突破极限。随之而来的性能问题有的被迎刃而解，有的成为难以逾越的盾墙。

那么，当我们在谈论性能时，到底在说什么？基于 React 框架开发的应用，在性能上又有哪些特点？

这篇文章我们从浏览器和 JavaScript 引擎角度来剖析前端性能，同时创新 React，充分利用浏览器能力突破局限。

#### 性能问题的阿喀琉斯之踵

事实上，性能问题多种多样：瓶颈可能出现在网络传输过程，造成前端数据呈现延迟；也可能是 hybrid 应用中，webview 容器带来限制。但是在分析性能问题时，经常逃不开一个概念——JavaScript 单线程。

浏览器解析渲染 DOM Tree 和 CSS Tree，解析执行 JavaScript，几乎所有的操作都是在主线程中执行。因为 JavaScript 可以操作 DOM，影响渲染，所以 JavaScript 引擎线程和 UI 线程是互斥的。换句话说，JavaScript 代码执行时会阻塞页面的渲染。

通过下面的图示来进行了解：

![](https://mmbiz.qpic.cn/mmbiz_jpg/meG6Vo0Mevhb0653OHO9ynI3Ab4eA2H8sA3mnfIKkGYK8T1BrDtIhMh5Oco5E3O38ic46LLFm0x8NjrwDPBr3Pg/640?wx_fmt=jpeg&tp=webp&wxfrom=5&wx_lazy=1&wx_co=1)

图中的几个关键角色：

Call Stack：调用栈，即 JavaScript 代码执行的地方，Chrome 和 NodeJS 中对应 V8 引擎。当它执行完当前所有任务时，栈为空，等待接收 Event Loop 中 next Tick 的任务。

Browser APIs：这是连接 JavaScript 代码和浏览器内部的桥梁，使得 JavaScript 代码可以通过 Browser APIs 操作 DOM，调用 setTimeout，AJAX 等。

Event queue: 每次通过 AJAX 或者 setTimeout 添加一个异步回调时，回调函数一般会加入到 Event queue 当中。

Job queue: 这是预留给 promise 且优先级较高的通道，代表着“稍后执行这段代码，但是在 next Event Loop tick 之前执行”。它属于 ES 规范，注意区别对待，这里暂不展开。

Next Tick: 表示调用栈 call stack 在下一 tick 将要执行的任务。它由一个 Event queue 中的回调，全部的 job queue，部分或者全部 render queue 组成。注意 current tick 只会在 Job queue 为空时才会进入 next tick。这就涉及到 task 优先级了，可能大家对于 microtask 和 macrotask 更加熟悉，这里不再展开。

Event Loop: 它会“监视”（轮询）call stack 是否为空，call stack 为空时将会由 Event Loop 推送 next tick 中的任务到 call stack 中。

在浏览器主线程中，JavaScript 代码在调用栈 call stack 执行时，可能会调用浏览器的 API，对 DOM 进行操作。也可能执行一些异步任务：这些异步任务如果是以回调的方式处理，那么往往会被添加到 Event queue 当中；如果是以 promise 处理，就会先放到 Job queue 当中。这些异步任务和渲染任务将会在下一个时序当中由调用栈处理执行。

理解了这些，大家就会明白：如果调用栈 call stack 运行一个很耗时的脚本，比如解析一个图片，call stack 就会像北京上下班高峰期的环路入口一样，被这个复杂任务堵塞。主线程其他任务都要排队，进而阻塞 UI 响应。这时候用户点击、输入、页面动画等都没有了响应。

这样的性能瓶颈，就如同阿喀琉斯之踵一样，在一定程度上限制着 JavaScript 的发挥。

#### 两方性能解药

我们一般有两种方案突破上文提到的瓶颈：

- 将耗时高、成本高、易阻塞的长任务切片，分成子任务，并异步执行

这样一来，这些子任务会在不同的 call stack tick 周期执行，进而主线程就可以在子任务间隙当中执行 UI 更新操作。设想常见的一个场景：如果我们需要渲染一个由十万条数据组成的列表，那么相比一次性渲染全部数据，我们可以将数据分段，使用 setTimeout API 去分步处理，构建渲染列表的工作就被分成了不同的子任务在浏览器中执行。在这些子任务间隙，浏览器得以处理 UI 更新。

- 另外一个创新性的做法：使用HTML5 Web worker

Web worker 允许我们将 JavaScript 脚本在不同的浏览器线程中执行。因此，一些耗时的计算过程我们都可以放在 Web worker 开启的线程当中处理。下文会有详解。

#### React 框架性能剖析

社区上关于 React 性能的内容往往聚焦在业务层面，主要是使用框架的“最佳实践”。这里我们不去谈论“使用 shoulComponentUpdate 减少不必要的渲染”、“减少 render 函数中 inline-function”等已经“老生常谈”的话题，本文主要从 React 框架实现层面分析其性能瓶颈和突破策略。

原生 JavaScript 一定是最高效的，这个毫无争议。相比其他框架，React 在 JavaScript 执行层面花费的时间较多，这是因为：

> Virtual DOM 构建 -> 计算 DOM diff -> 生成 render patch

这一系列复杂过程所造成的。也就是说，在一定程度上：React 著名的调度策略 — stack reconcile 是 React 的性能瓶颈。

这并不难理解，因为 DOM 更新只是 JavaScript 调用浏览器的 APIs，这个过程对所有框架以及原生 JavaScript 来讲是一样黑盒执行的，这一部分的性能消耗是同等且不可避免的。

再来看我们的 React：stack reconcile 过程会深度优先遍历所有的 Virtual DOM 节点，进行 diff。整棵 Virtual DOM 计算完成之后，将任务出栈释放主线程。所以，浏览器主线程被 React 更新状态任务占据的时候，用户与浏览器进行任何交互都不能得到反馈，只有等到任务结束，才能得到浏览器的响应。

我们来看一个典型的场景，来自文章：React的新引擎—React Fiber是什么？

这个例子会在页面中创建一个输入框，一个按钮，一个 BlockList 组件。BlockList 组件会根据 NUMBER_OF_BLOCK 数值渲染出对应数量的数字显示框，数字显示框显示点击按钮的次数。

![](https://mmbiz.qpic.cn/mmbiz_png/meG6Vo0Mevhb0653OHO9ynI3Ab4eA2H8VSojNVUbaYKcaia5uicxfXjQoeWUO4Z5psTwuic4tziahcVveDqBPXMBEQ/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1&wx_co=1)

在这个例子中，我们可以设置 NUMBER_OF_BLOCK 的值为 100000。这时候点击按钮，触发 setState，页面开始更新。此时点击输入框，输入一些字符串，比如 “hi，react”。可以看到：页面没有任何响应。等待 7s 之后，输入框中突然出现了之前输入的 “hireact”。同时， BlockList 组件也更新了。

显而易见，这样的用户体验并不好。

浏览器主线程在这 7s 的 performance 如下图所示：

![](https://mmbiz.qpic.cn/mmbiz_png/meG6Vo0Mevhb0653OHO9ynI3Ab4eA2H8IBCNXJMTfXbBbMRdic1icNKp3bfYg1S5Ah0FFhrM6eEpLJUzunjubuvA/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1&wx_co=1)

- 
黄色部分是 JavaScript 执行时间，也是 React 占用主线程时间；

- 
紫色部分是浏览器重新计算 DOM Tree 的时间；

- 
绿色部分是浏览器绘制页面的时间。

这三种任务，总共占用浏览器主线程 7s，此时间内浏览器无法与用户交互。主要是黄色部分执行时间较长，占用了 6s，即 React 较长时间占用主线程，导致主线程无法响应用户输入。这就是一个典型的例子。

#### React 性能升级——React Fiber

React 核心团队很早之前就预知性能风险的存在，并且持续探索可解决的方式。基于浏览器对 requestIdleCallback 和 requestAnimationFrame 这两个API 的支持，React 团队实现新的调度策略 — Fiber reconcile。

更多关于 Fiber 的内容同样推荐文章：React的新引擎—React Fiber是什么？
文章中又在应用 React Fiber 的场景下，重复刚才的例子，不会再出现页面卡顿，交互自然而顺畅。

浏览器主线程的 performance 如下图所示：

![](https://mmbiz.qpic.cn/mmbiz_png/meG6Vo0Mevhb0653OHO9ynI3Ab4eA2H81qH41P2J2fLibL8SJO4yagibkSjG89FENW5tRvsNFsOAZvpKk2r7ibJ7Q/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1&wx_co=1)

可以看到：在黄色 JavaScript 执行过程中，也就是 React 占用浏览器主线程期间，浏览器在也在重新计算 DOM Tree，并且进行重绘。只管来看，黄色和紫色等互相交替，同时页面截图显示，用户输入得以及时响应。简单说，在 React 占用浏览器主线程期间，浏览器也在与用户交互。这显然是“更好的性能”表现。

以上是 React 应用第一种方法：“将耗时高的任务分段”，达到了性能突破。下面我们再来看另一种“民间”做法，应用 Web worker。

#### React 结合 Web worker

关于 Web worker 的概念此文不再赘述，大家可以访问 MDN 地址进行了解。我们聚焦思考点：如果让 React 接入 Web worker 的话，切入点在哪里，该如何实施？

总所周知，标准的 React 应用由两部分构成：

- 
React core：负责绝大部分复杂的 Virtual DOM 计算；

- 
React-Dom：负责与浏览器真实 DOM 交互来展示内容。

那么答案很简单，我们尝试在 Web worker 中运行 React Virtual DOM 的相关计算。即将 React core 部分移入 Web worker 线程中。

确实有人提出了这样的想法，请参考 React 仓库 第 #3092 号 Issue，这也吸引来了 Dan Abramov 的讨论。虽然这样的提案被拒绝，但这并不妨碍我们让 React 结合 worker 做试验。

Talk is cheap, show me the code, and demo:
读者可以访问这里，该网站分别用原生 React 和接入 Web worker 版 React 实现了两个应用，并对比其性能表现。关于代码部分，感兴趣的同学可以私信我。

最终结论：只有当大量的节点发生变化的时，Web worker 提升渲染性能才会有一些效果。当节点数量非常少的时候，接入 Web worker 的性能可能是负收益。我认为这是由于 worker 线程和主线程之间的通信成本所致。

这么看，Web worker 版本的 React 仍有性能提升空间，我简单总结如下：

- 因为 worker 线程和主线程在使用 postMessage 通信时，性能成本较大，我们可以采用 batching 思想减少通信的次数。

如果在每次 DOM 需要改变时，都调用 postMessage 通知主线程，不是特别明智。所以可以用 batching 思想，将 worker 线程中计算出来的 DOM 待更新内容进行收集，再统一发送。这样一来，batching 的粒度就很有意思了。如果我们走极端，每次 batching 收集的变更都非常多，迟迟不向主线程发送，那么在一次 batching 时就给浏览器真正的渲染过程带来了压力，反而适得其反。

- 
使用 postMessage 传递消息时，采用 transferable objects 进行数据负载

- 
关于 worker 版 syntheticEvent

原生 React 有一套事件系统，它在最顶层监听所有的浏览器事件，之后将它们转化为合成事件（syntheticEvent），传递给我们在 Virtual DOM 上定义的事件监听者。

对于我们的 Web worker，由于 worker 线程不能直接操作 DOM，也就不能监听浏览器事件。因此所有事件同样都在主线程中处理，转化为虚拟事件再传递给 worker 线程进行发布，也就意味着所有关于创建虚拟事件的操作还是都在主线程中进行，一个可能改善的方案可以考虑直接将原始事件传递给 worker，由 worker 来生成模拟事件并冒泡传递。

关于 React 结合 worker 还有很多值得深挖的内容，比如：事件处理方面 preventDefault 和 stopPropogation 的同步性保障（worker 线程和主线程通信是异步的）；使用 multiple worker（一个以上 worker）进行探究等。如果读者有兴趣，我会专门写篇文章介绍。

#### Redux 和 Web worker

既然 React 可以接入 Web worker，那么 Redux 当然也能借鉴这样的思想，将 Redux 中 reducer 复杂的纯计算过程放在 worker 线程里，是不是一个很好的思路？

我使用 “N-皇后问题” 模拟大型计算，除了这个极其耗时的算法，页面中还运行这么几个模块，来实现频繁更新 DOM 的渲染逻辑：

- 
一个实时每 16 毫秒，显示计数（每秒增加 1）的 blinker 模块；

- 
一个定时每 500 毫秒，更新背景颜色的 counter 模块；

- 
一个永久往复运动的 slider 模块；

- 
一个每 16 毫秒翻转 5 度的 spinner 模块

如图：

![](https://mmbiz.qpic.cn/mmbiz_gif/meG6Vo0Mevhb0653OHO9ynI3Ab4eA2H81yeBjGaoMoyvxpvE2BEjIDt0kbxCEMXzpBQ4RYFXdCQK5ozpuzBEWA/640?wx_fmt=gif&tp=webp&wxfrom=5&wx_lazy=1)

这些模块都定时频繁地更新 DOM 样式，进行渲染。正常情况下，在 JavaScript 主线程进行 N-皇后计算时，这些渲染过程都将被卡顿。

如果将 N-皇后计算放置到 worker 线程，我们会发现 demo 展现了令人惊讶的性能提升，完全丝滑毫无卡顿。如上图，左半部分为正常版本，不出意外出现了页面卡顿，右侧是接入 worker 之后的应用。

在实现层面，借助 Redux 库的 enchancer 设计，完成了抽象封装。

一个 store enhancer，实际上就是一个 curry 化的高阶函数，这和 React 中的高阶组件的概念很相似，同时也类似我们更加熟悉的中间件。其实参考 Redux 源码，会发现 Redux 源码中 applyMiddleware 方法的执行结果就是一个 store enhancer。