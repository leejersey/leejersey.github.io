---
title: "react中的classname"
date: 2021-03-18
---

工作中经常会碰到需要给jsx中加多个classname.

## es6模板字符串方法

```
className={`title ${index === this.state.active ? &apos;active&apos; : &apos;&apos;}`}
```

## 字符串连接

```
className={["title", index === this.state.active?"active":null].join(&apos; &apos;)}
```

## classnames

```
var classNames = require(&apos;classnames&apos;);

var Button = React.createClass({
  // ...
  render () {
    var btnClass = classNames({
      btn: true,
      &apos;btn-pressed&apos;: this.state.isPressed,
      &apos;btn-over&apos;: !this.state.isPressed && this.state.isHovered
    });
    return {this.props.label};
  }
});
```