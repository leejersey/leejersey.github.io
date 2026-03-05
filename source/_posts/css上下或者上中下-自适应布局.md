---
title: "css上下或者上中下 自适应布局"
date: 2018-10-10
---

方法一：定位

```html
头部
内容
底部
```

```css
*{
	margin: 0;
	padding: 0;
}
div{
	text-align: center;
	font-size: 30px;
}
.header,.footer{
	width: 100%;
	height: 100px;
	line-height: 100px;
	background-color: red;
}
.content{
	width: 100%;
	position: absolute;
	top: 100px;
	bottom:100px;
	background-color: yellow;
}
.footer{
	position: absolute;
	bottom: 0px;
}
```

方法二：flex

```html

  header
  center
  footer

```

```css
html,body{
  height:100%;
}
.content{
  display: flex;
  flex-direction: column;
  height: 100%;
}

.header{
  background:red;
  height:100px;
  width:100%;
}

.center{
  background: blue;
  flex: 1;
  height: 100%;
}

.footer{
  background:green;
  height:100px;
  width:100%;
}
```