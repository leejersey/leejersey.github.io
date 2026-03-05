---
title: "redux源码分析"
date: 2018-10-20
---

redux的源码中，有6个js文件，分别是：

- index.js
- createStore.js
- combineReducers.js
- bindActionCreators.js
- compose.js
- applyMiddleware.js

我们一个一个来分析吧~

## index

这里呢没有太多需要讲的，就是暴露了5个核心的api，分别是：

- createStore：接收state和reducer，生成一颗状态树store
- combineReducers：把子reducer合并成一个大reducer
- bindActionCreators：把actionCreators和dispatch封装成一个函数，也就是把他们两绑定在一起
- applyMiddleware：这是一个中间件
- compose：一个组合函数

## createStore

首先，定义初始化的action

```jsx
exportconst ActionTypes = {
  INIT: '@@redux/INIT'
}
```

这个createStore函数，会传入三个参数和一个返回值，分别是：

`1、 @param {Function} reducer`

这个reducer是一个函数，这个函数接收state和action，作一系列计算之后返回一个新的state。这里就体现了函数式编程的一些特性:

第一，这个reducer是一个纯函数，纯函数的特点是：对于相同的输入，永远会得到相同的输出，而且没有任何可观察的副作用，也不依赖外部环境的状态。不理解纯函数的筒子们，可以上网搜索一下。

第二，state是不可变的，我们这里对state作的一些修改和计算，不是直接修改原来的数据，而是返回修改之后的数据，原来的数据是保持不变。这里可以衍生到immutable，可以使用immutable和redux搭配使用。

`2、@param {any} [preloadedState]`

这是初始化的state，不多说。

`3、@param {Function} [enhancer]`

这个enhancer其实就是一个中间件，它在redux3.1.0之后才加入的。相当于把store做一些增强处理，让store更强大，功能更丰富，在之后的applyMiddleware那里会详细说的。这里也体现了高阶函数的思想，就像react-redux的connect方法一样，做一些包装处理之后，再返回。

`4、@returns {Store}`

这是返回的值，返回的是一棵状态树，也就是store啦。

这是做的源码分析，都写在注释里了。createStore返回的最常用的三个api是dispatch，subscribe，getState，一般我们只要传入reducer和preloadedState，就可以直接调用这三个方法，非常方便。

```jsx
exportdefaultfunctioncreateStore(reducer, preloadedState, enhancer) {
//这里是一些参数校验
//如果第二个参数为函数且没有传入第三个参数，那就交换第二个参数和第三个参数
//意思是createSotre会认为你忽略了preloadedState，而传入了一个enhancer
if (typeof preloadedState === 'function' && typeof enhancer === 'undefined') {
    enhancer = preloadedState
    preloadedState = undefined
  }

if (typeof enhancer !== 'undefined') {
//如果传入了第三个参数，但不是一个函数，就报错
if (typeof enhancer !== 'function') {
thrownewError('Expected the enhancer to be a function.')
    }

//这是一个高阶函数调用方法。这里的enhancer就是applyMiddleware(...middlewares)
//enhancer接受createStore作为参数，对createStore的能力进行增强，并返回增强后的createStore
//然后再将reducer和preloadedState作为参数传给增强后的createStore，得到最终生成的store
return enhancer(createStore)(reducer, preloadedState)
  }

//reducer不是函数，报错
if (typeof reducer !== 'function') {
thrownewError('Expected the reducer to be a function.')
  }

//声明一些变量
let currentReducer = reducer //当前的reducer函数
let currentState = preloadedState//当前的状态树
let currentListeners = [] // 当前的监听器列表
let nextListeners = currentListeners //更新后的监听器列表
let isDispatching = false//是否正在dispatch

//判断当前listener和更新后的listener是不是同一个引用，如果是的话对当前listener进行一个拷贝，防止在操作新的listener列表的时候对正在发生的业务逻辑造成影响
functionensureCanMutateNextListeners() {
if (nextListeners === currentListeners) {
      nextListeners = currentListeners.slice()
    }
  }

/**
   *
   * @returns {any} The current state tree of your application.
   */
//返回当前的状态树
functiongetState() {
return currentState
  }

/**
   *这个函数是给store添加监听函数，把listener作为一个参数传入，
   *注册监听这个函数之后，subscribe方法会返回一个unsubscribe()方法，来注销刚才添加的监听函数
   * @param {Function} listener 传入一个监听器函数
   * @returns {Function} 
   */
functionsubscribe(listener) {
if (typeof listener !== 'function') {
thrownewError('Expected listener to be a function.')
    }
//注册监听
let isSubscribed = true

    ensureCanMutateNextListeners()
//将监听器压进nextListeners队列中
    nextListeners.push(listener)

//注册监听之后，要返回一个取消监听的函数
returnfunctionunsubscribe() {
//如果已经取消监听了，就返回
if (!isSubscribed) {
return
      }
//取消监听
      isSubscribed = false

//在nextListeners中找到这个监听器，并且删除
      ensureCanMutateNextListeners()
const index = nextListeners.indexOf(listener)
      nextListeners.splice(index, 1)
    }
  }

/**
   * @param {Object} action 传入一个action对象
   *
   * @returns {Object} 
   */
functiondispatch(action) {
//校验action是否为一个原生js对象
if (!isPlainObject(action)) {
thrownewError(
'Actions must be plain objects. ' +
'Use custom middleware for async actions.'
      )
    }

//校验action是否包含type对象
if (typeof action.type === 'undefined') {
thrownewError(
'Actions may not have an undefined "type" property. ' +
'Have you misspelled a constant?'
      )
    }

//判断是否正在派发，主要是避免派发死循环
if (isDispatching) {
thrownewError('Reducers may not dispatch actions.')
    }

//设置正在派发的标志位，然后将当前的state和action传给当前的reducer，用于生成新的state
//这就是reducer的工作过程，纯函数接受state和action，再返回一个新的state
try {
      isDispatching = true
      currentState = currentReducer(currentState, action)
    } finally {
      isDispatching = false
    }

//得到新的state之后，遍历当前的监听列表，依次调用所有的监听函数，通知状态的变更
//这里没有把最新的状态作为参数传给监听函数，是因为可以直接调用store.getState（）方法拿到最新的状态
const listeners = currentListeners = nextListeners
for (let i = 0; i  dispatch(actionCreator(...args))
}
/*
 * @param {Function|Object} actionCreators
 *
 * @param {Function} dispatch 
 *
 * @returns {Function|Object}
 * 
 */
exportdefaultfunctionbindActionCreators(actionCreators, dispatch) {
//actionCreators为函数，就直接调用bindActionCreator进行包装
if (typeof actionCreators === 'function') {
return bindActionCreator(actionCreators, dispatch)
  }

if (typeof actionCreators !== 'object' || actionCreators === null) {
thrownewError(
`bindActionCreators expected an object or a function, instead received ${actionCreators === null ? 'null' : typeof actionCreators}. ` +
`Did you write "import ActionCreators from" instead of "import * as ActionCreators from"?`
    )
  }

//以下是actionCreators为对象时的操作
//遍历actionCreators对象的key值
const keys = Object.keys(actionCreators)
//存储dispatch和actionCreator绑定之后的集合
const boundActionCreators = {}
//遍历每一个对象，一一进行绑定
for (let i = 0; i  f(g(h(...args))).
 */

exportdefaultfunctioncompose(...funcs) {
//判断传入参数的数量，做不同的处理
if (funcs.length === 0) {
returnarg => arg
  }

if (funcs.length === 1) {
return funcs[0]
  }

return funcs.reduce((a, b) => (...args) => a(b(...args)))
}
```

这一段代码的主要难点是在最后那一句，着重说一下reduce这个方法。这个reduce不是之前的reducer，这里的reduce函数是es5的一个归并数组的方法，是从数组的第一项开始，逐个遍历数组的所有项。

它接收两个参数，一个是在每一项上调用的函数，还有一个可选参数，是作为归并基础的初始值。调用的那个函数又接收四个参数，前一个值，当前值，项的索引，和数组对象。这个函数返回的任何值都会作为第一个参数自动传递给下一项。这样说可能比较抽象，举个例子：

```jsx
[1,2,3,4,5].reduce((prev, cur) => {
return prev + cur //输出15
})
```

用reduce就可以很快的求的数组所有值相加的和。另外，还有一个reduceRight（）方法，跟reduce是一样的，只不过是从数组的右边开始遍历的。

我们回到源码上面`return funcs.reduce((a, b) => (...args) => a(b(...args)))`，这其实就是遍历传入的参数数组（函数），将这些函数合并成一个函数，从右到左的执行。这就是中间件的创造过程，把store用一个函数包装之后，又用另一个函数包装，就形成了这种包菜式的函数。

## applyMiddleware

applyMiddleware是用来扩展redux功能的，主要就是扩展store.dispatch的功能，像logger、redux-thunk就是一些中间件。

它的实现过程是：在dispatch的时候，会按照在applyMiddleware时传入的中间件顺序，依次执行。最后返回一个经过许多中间件包装之后的store.dispatch方法。

如果理解了之前说的compose函数，这一段代码应该也很容易就能看懂啦。

```jsx
/**
 * @param {...Function} middlewares 接收不定数量的中间件函数
 * @returns {Function} 返回一个经过中间件包装之后的store
 */
exportdefaultfunctionapplyMiddleware(...middlewares) {
//返回一个参数为createStore的匿名函数
return(createStore) => (reducer, preloadedState, enhancer) => {
//生成store
const store = createStore(reducer, preloadedState, enhancer)
//得到dispatch方法
let dispatch = store.dispatch
//定义中间件的chain
let chain = []

//在中间件中要用到的两个方法
const middlewareAPI = {
      getState: store.getState,
      dispatch: (action) => dispatch(action)
    }
//把这两个api给中间件包装一次
    chain = middlewares.map(middleware => middleware(middlewareAPI))
//链式调用每一个中间件，给dispatch进行封装，再返回最后包装之后的dispatch
    dispatch = compose(...chain)(store.dispatch)

return {
      ...store,
      dispatch
    }
  }
}
```

## 总结

整个的源码就全部分析完了，我们可以看到，redux的源码很多地方都体现了函数式编程的思想。函数式编程写出来的代码确实很漂亮很简洁，但是理解起来也比较困难。这也只是函数式编程的很小一部分，有兴趣的话可以去了解一下其他的部分。

写到这里也差不多了，希望以后有机会能多看点源码，get一些新的知识，最后感谢宋老师的宝贵意见，bye