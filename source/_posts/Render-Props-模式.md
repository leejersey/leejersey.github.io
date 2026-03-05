---
title: "Render Props 模式"
date: 2018-12-27
---

### 概述

`Render Props`模式是一种非常灵活复用性非常高的模式，它可以把特定行为或功能封装成一个组件，提供给其他组件使用让其他组件拥有这样的能力，接下来我们一步一步来看React组件中如何实现这样的功能。

### React 组件数据传递

`React`中我们可以给一个组件传递一些`props`并且在组件内部展示，同样的我们也可以传递一些组件同样也是行得通的，一起看一个例子

#### 1. 组件普通数据传递

我们可以通过组件传递一些字符串数据，并且在组件内部渲染
下面的代码很平常，我们绝大多数代码都是这样。

```javascript
const Foo = ({ title }) => (
  
    
{title}

  
);
class App extends React.Component {
  render() {
    return (
      
        
## 这是一个示例组件

        
      
    );
  }
}
ReactDOM.render(, document.getElementById('app'))
```

#### 2. 组件上传递组件

更进一步，我们可以在组件上传递普通的`HTML 标签`和`React 组件`达到复用的目的

```javascript
// https://codepen.io/tudou/full/OvdrPW
const Bar = () => (
我是Bar组件 ：）
);
const Foo = ({ title, component }) => (
  
    
{title}

    {component()}
  
);
class App extends React.Component {
  render() {
    return (
      
        
## 这是一个示例组件

          } />
      
    );
  }
}
ReactDOM.render(, document.getElementById('app'))
```

在上面的例子中传递普通的`HTML 标签`对我们复用组件没有任何帮助，重点可以看传递`component`这个参数，它传递给`Foo`组件一个函数这个函数返回的是一个`Bar 组件`，我们会在`Foo 组件`中调用并且显示`component`函数中的组件。我们再来写一个小的DEMO进行验证。

#### 3. 一个纯粹的`Render Props`例子

```javascript
// https://codepen.io/tudou/full/dmawvY
const Bar = ({ title }) => (
{title}
);

class Foo extends React.Component {
  constructor(props) {
    super(props);
    this.state = { title: '我是一个state的属性' };
  }
  render() {
    const { render } = this.props;
    const { title } = this.state;

    return (
      
        {render(title)}
      
    )
  }
}

class App extends React.Component {
  render() {
    return (
      
        
## 这是一个示例组件

         } />
      
    );
  }
}
ReactDOM.render(, document.getElementById('app'))
```

在上面的例子中，给`Foo 组件`传递了一个`render`参数它是一个函数这个函数返回一个`Bar`组件，这个函数接受一个参数`title`他来自于`Foo 组件`调用时传递并且我们又将`title 属性`传递给了`Bar 组件`。经过上述的调用过程我们的`Bar 组件`就可以共享到`Foo 组件内部的`state 属性`。

#### 4. 通过`children`传递

这个demo略微不同于上面通过`props`传递，而它是通过组件的`children`传递一个函数给`Foo 组件`

```javascript
// https://codepen.io/tudou/full/WzPPeL
const Bar = ({ title }) => (
{title}
);

class Foo extends React.Component {
  constructor(props) {
    super(props);
    this.state = { title: '我是一个state的属性' };
  }
  render() {
    const { children } = this.props;
    const { title } = this.state;

    return (
      
        {children(title)}
      
    )
  }
}

class App extends React.Component {
  render() {
    return (
      
        
## 这是一个示例组件

        
          {(title) => (
            
          )}
        
      
    );
  }
}
ReactDOM.render(, document.getElementById('app'))
```

观察可发现只是写法略微有些变法，我们将要传递的数据放到的组件的`children`。实际上并无不同之处(都是传递一个函数)

```javascript

  {(title) => (
    
  )}

```

### 注意事项

请注意当我们的`Foo 组件`继承于`React.PureComponent`的时候，我们需要避免下面这样的写法。不然我们的性能优化将付之东流。

```javascript
render() {
    return (
      
        
## 这是一个示例组件

         } />
      
    );
  }
```

如果你在`render`创建一个函数，在每次渲染的时候`render prop`将会是一个新的值，那么每次将会重新渲染`Bar`。

正确的做法应该是在组件内部创建一个函数用于显示组件

```javascript
const Bar = ({ title }) => (
{title}
);

class Foo extends React.Component {
  constructor(props) {
    super(props);
    this.state = { title: '我是一个state的属性' };
  }
  render() {
    const { render } = this.props;
    const { title } = this.state;

    return (
      
        {render(title)}
      
    )
  }
}

class App extends React.Component {
  // 单独创建一个渲染函数
  renderFoo(title) {
    return ;
  }
  render() {
    return (
      
        
## 这是一个示例组件

        
      
    );
  }
}
ReactDOM.render(, document.getElementById('app'))
```

### 总结

学习了解`Render Props`渲染模式原理，使用了`render`和`children`两种不同的渲染方法。