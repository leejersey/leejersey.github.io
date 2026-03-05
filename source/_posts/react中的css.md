---
title: "react中的css"
date: 2020-06-24
---

## namespaces
> 利用约定好的命名来隔离 CSS 的作用域

comA.css:

```css
.comA .title {
    color: red;
}
.comA .……{
    ……
}
```

comB.css

```css
.comB .title {
    font-size: 14px;
}
.comB .……{
    ……
}
```

嗯，用 CSS 写命名空间写起来貌似有点累。

没事我们有 CSS 预处理器，利用 less、sass、stylus 等预处理器，代码依然简洁。

A.less:

```less
.comA {
    .title {
        color: red;
    }

    .…… {
        ……
    }
}
```

B.less

```less
.comB {
    .title {
        font-size: 14px;
    }

    .…… {
        ……
    }
}
```

貌似很完美解决了 CSS 的作用域问题，但是问题来了，假设 AB 组件是嵌套组件。

那么最后的渲染 DOM 结构为：

```html

    
# 组件A的title

    
        
# 组件组件的title

    

```

comA 的样式又成功作用在了组件 B 上。

没关系，还有解，所有的 class 名以命名空间为前缀。

```html

    
# 组件A的title

    
        
# 组件组件的title

    

```

A.less:

```less
.comA {
    &__title {
        color: red;
    }
}
```

B.less

```less
.comB {
    &__title {
        font-size: 14px;
    }
}
```

如果，我们的样式还遵循 BEM (Block, Element, Modifier) 规范，那，样式名简直不要太长！但是问题确实也解决了，但约定毕竟是约定，靠约定和自觉来解决问题毕竟不是好方法，在多人维护的业务代码中这种约定来解决 CSS 污染问题也变得很难。

## CSS in JS
> 使用 JS 语言写 CSS，也是 React 官方有推荐的一种方式。

从React文档进入

[https://github.com/MicheleBertoli/css-in-js](https://github.com/MicheleBertoli/css-in-js) ，可以发现目前的 CSS in JS 的第三方库有60余种。

看两个比较大众的库：

- reactCSS
- styled-components

### reactCSS
> 支持 React、Redux、React Native、autoprefixed、Hover、伪元素和媒体查询

```js
const styles = reactCSS({
  'default': {
    card: {
      background: '#fff',
      boxShadow: '0 2px 4px rgba(0,0,0,.15)',
    },
  },
  'zIndex-2': {
    card: {
      boxShadow: '0 4px 8px rgba(0,0,0,.15)',
    },
  },
}, {
  'zIndex-2': props.zIndex === 2,
})
```

```js
class Component extends React.Component {
  render() {
    const styles = reactCSS({
      'default': {
        card: {
          background: '#fff',
          boxShadow: '0 2px 4px rgba(0,0,0,.15)',
        },
        title: {
          fontSize: '2.8rem',
          color: this.props.color,
        },
      },
    })
    return (
      
        
          { this.props.title }
        
        { this.props.children }
      
    )
  }
}
```

### styled-components
> styled-components，目前社区里最受欢迎的一款 CSS in JS 方案

```js
const Button = styled.a`
  /* This renders the buttons above... Edit me! */
  display: inline-block;
  border-radius: 3px;
  padding: 0.5rem 0;
  margin: 0.5rem 1rem;
  width: 11rem;
  background: transparent;
  color: white;
  border: 2px solid white;
  /* The GitHub button is a primary button
   * edit this to target it specifically! */
  ${props => props.primary && css`
    background: white;
    color: palevioletred;
  `}
`
render(
  
    
      GitHub
    
    
      Documentation
    
  
)
```

与 reactCSS 不同，styled-components 使用了模板字符串，写法更接近 CSS 的写法。

## CSS Modules
> 利用 webpack 等构建工具使 class 作用域为局部。

CSS 依然是还是 CSS

例如 webpack ，配置 css-loader 的 options modules: true。

```
module.exports = {
  module: {
    rules: [
      {
        test: /\.css$/,
        loader: &apos;css-loader&apos;,
        options: {
          modules: true,
        },
      },
    ],
  },
};
```

modules 更具体的配置项参考：[https://www.npmjs.com/package/css-loader](https://www.npmjs.com/package/css-loader)

loader 会用唯一的标识符(identifier)来替换局部选择器。所选择的唯一标识符以模块形式暴露出去。

示例：

webpack css-loader options

```
options: {
  ...,
  modules: {
    mode: &apos;local&apos;,
    // 样式名规则配置
    localIdentName: &apos;[name]__[local]--[hash:base64:5]&apos;,
  },
},
...
```

App.js

```
...
import styles from "./App.css";
...

  
    
# 标题

    描述
  

```

App.css

```
.header__wrapper {
  text-align: center;
}

.title {
  color: gray;
  font-size: 34px;
  font-weight: bold;
}

.sub-title {
  color: green;
  font-size: 16px;
}
```

编译后端的 CSS，classname 增加了 hash 值。

```
.App__header__wrapper--TW7BP {
  text-align: center;
}

.App__title--2qYnk {
  color: gray;
  font-size: 34px;
  font-weight: bold;
}

.App__sub-title--3k88A {
  color: green;
  font-size: 16px;
}
```

## 总结

（1）如果是 ui 组件库中使用

> 建议使用 namespaces 方案

原因：

ui 组件库维护人员基本固定，遵守约定的规范较为容易，可通过约定规范来解决不同组件 CSS 相互影响问题
由于 ui 组件库会应用于整个公司的产品，在真正的业务场景中，虽然不建议，但是可能无法避免需要覆盖组件样式的特殊场景，如使用其他两种方式，不能支持组件样式覆盖

（2）如果是业务代码/业务组件中使用

> CSS in JS / CSS Modules

业务代码维护人员较多且不固定、代码水平不一致，只通过规范来约束不靠谱，无法保证开发人员严格遵守规范，不能根治 CSS 交叉影响问题，但是从 debug 角度考虑，建议组件外层都添加一个 namespaces 方面定位组件。然后加之 CSS in JS 或 CSS Modules 方案来解决 CSS 交叉影响问题。