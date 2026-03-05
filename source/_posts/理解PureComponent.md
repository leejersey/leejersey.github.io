---
title: "理解PureComponent"
date: 2018-12-24
---

## 什么是PureComponent

### 默认渲染行为的问题

在React Component的生命周期中，有一个shouldComponentUpdate方法。这个方法默认返回值是true。

这意味着就算没有改变组件的props或者state，也会导致组件的重绘。这就经常导致组件因为不相关数据的改变导致重绘，这极大的降低了React的渲染效率。比如下面的例子中，任何options的变化，甚至是其他数据的变化都可能导致所有cell的重绘。

```javascript
//Table Component
{this.props.items.map(i =>
    
)}
```

### 重写shouldComponentUpdate

为了避免这个问题，我们可以在Cell中重写shouldComponentUpdate方法，只在option发生改变时进行重绘。

```javascript
class Cell extends React.Component {
  shouldComponentUpdate(nextProps, nextState) {
    if (this.props.option === nextProps.option) {
      return false;
    } else {
      return true;
    }
  }
}
```

这样每个Cell只有在关联option发生变化时进行重绘。

因为上面的情况十分通用，React创建了PureComponent组件创建了默认的shouldComponentUpdate行为。这个默认的shouldComponentUpdate行为会一一比较props和state中所有的属性，只有当其中任意一项发生改变是，才会进行重绘。

**需要注意的是，PureComponent使用浅比较判断组件是否需要重绘**

因此，下面对数据的修改并不会导致重绘（假设Table也是PureComponent)

```javascript
options.push(new Option())
  options.splice(0, 1)
  options[i].name = "Hello"
```

这些例子都是在原对象上进行修改，由于浅比较是比较指针的异同，所以会认为不需要进行重绘。

为了避免出现这些问题，推荐使用[immutable.js](https://link.jianshu.com/?t=https://github.com/facebook/immutable-js)。immutable.js会在每次对原对象进行添加，删除，修改使返回新的对象实例。任何对数据的修改都会导致数据指针的变化。

## 总结

Component中的shouldComponentUpdate方法默认返回值是true。PureComponent创建了默认的shouldComponentUpdate行为。这个默认的shouldComponentUpdate行为会一一比较props和state中所有的属性，只有当其中任意一项发生改变是，才会进行重绘。

参考：[https://wulv.site/2017-05-31/react-purecomponent.html](https://wulv.site/2017-05-31/react-purecomponent.html)