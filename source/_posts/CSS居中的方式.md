---
title: "CSS居中的方式"
date: 2018-10-08
---

## 简言

CSS居中是前端工程师经常要面对的问题，也是基本技能之一。今天有时间把CSS居中的方案汇编整理了一下，目前包括水平居中，垂直居中及水平垂直居中方案共15种。如有漏掉的，还会陆续的补充进来，算做是一个备忘录吧。

![css居中](http://res.42du.cn/up/201803/bqwskx8i.jpg)

## 1 水平居中

### 1.1 内联元素水平居中

利用 `text-align: center` 可以实现在块级元素内部的内联元素水平居中。此方法对内联元素(`inline`), 内联块(`inline-block`), 内联表(`inline-table`), `inline-flex`元素水平居中都有效。

** 核心代码：**

```css
.center-text{
    text-align: center;
 }
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/57)

### 1.2 块级元素水平居中

通过把固定宽度块级元素的`margin-left`和`margin-right`设成auto，就可以使块级元素水平居中。

** 核心代码：**

```css
.center-block{
  margin:0 auto;
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/58)

### 1.3 多块级元素水平居中

#### 1.3.1 利用`inline-block`

如果一行中有两个或两个以上的块级元素，通过设置块级元素的显示类型为`inline-block`和父容器的`text-align`属性从而使多块级元素水平居中。

** 核心代码：**

```css
.container{
    text-align: center;
}
.inline-block{
    display: inline-block;
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/59)

#### 1.3.2 利用`display: flex`

利用弹性布局(`flex`)，实现水平居中，其中`justify-content` 用于设置弹性盒子元素在主轴（横轴）方向上的对齐方式，本例中设置子元素水平居中显示。

** 核心代码：**

```css
.flex-center{
    display: flex;
    justify-content: center;
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/60)

## 2 垂直居中

### 2.1 单行内联(`inline-`)元素垂直居中

通过设置内联元素的高度(`height`)和行高(`line-height`)相等，从而使元素垂直居中。

** 核心代码：**

```css
#v-box{
    height:120px;
    line-height:120px;
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/61)

### 2.2 多行元素垂直居中

#### 2.2.1 利用表布局（`table`）

利用表布局的`vertical-align: middle`可以实现子元素的垂直居中。

** 核心代码：**

```css
.center-table{
    display: table;
}
.v-cell{
    display: table-cell;
    vertical-align: middle;
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/62)

#### 2.2.2 利用flex布局（`flex`）

利用flex布局实现垂直居中，其中`flex-direction: column`定义主轴方向为纵向。因为flex布局是CSS3中定义，在较老的浏览器存在兼容性问题。

** 核心代码：**

```css
.center-flex{
    display: flex;
    flex-direction: column;
    justify-content: center;
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/63)

#### 2.2.3 利用“精灵元素”

利用“精灵元素”(ghost element)技术实现垂直居中，即在父容器内放一个100%高度的伪元素，让文本和伪元素垂直对齐，从而达到垂直居中的目的。

** 核心代码：**

```css
.ghost-center{
    position: relative;
}
.ghost-center::before{
    content:" ";
    display: inline-block;
    height:100%;
    width:1%;
    vertical-align: middle;
}
.ghost-centerp{
    display: inline-block;
    vertical-align: middle;
    width:20rem;
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/64)

### 2.3 块级元素垂直居中

#### 2.3.1 固定高度的块级元素

我们知道居中元素的高度和宽度，垂直居中问题就很简单。通过绝对定位元素距离顶部50%，并设置`margin-top`向上偏移元素高度的一半，就可以实现垂直居中了。

** 核心代码：**

```css
.parent{
  position: relative;
}
.child{
  position: absolute;
  top:50%;
  height:100px;
  margin-top: -50px; 
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/65)

#### 2.3.2 未知高度的块级元素

当垂直居中的元素的高度和宽度未知时，我们可以借助CSS3中的`transform`属性向Y轴反向偏移50%的方法实现垂直居中。但是部分浏览器存在兼容性的问题。

** 核心代码：**

```css
.parent{
    position: relative;
}
.child{
    position: absolute;
    top:50%;
    transform:translateY(-50%);
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/66)

## 3 水平垂直居中

### 3.1 固定宽高元素水平垂直居中

通过margin平移元素整体宽度的一半，使元素水平垂直居中。

** 核心代码：**

```css
.parent{
    position: relative;
}
.child{
    width:300px;
    height:100px;
    padding:20px;
    position: absolute;
    top:50%;
    left:50%;
    margin: -70px 00 -170px;
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/67)

### 3.2 未知宽高元素水平垂直居中

利用2D变换，在水平和垂直两个方向都向反向平移宽高的一半，从而使元素水平垂直居中。

** 核心代码：**

```css
.parent{
    position: relative;
}
.child{
    position: absolute;
    top:50%;
    left:50%;
    transform:translate(-50%, -50%);
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/68)

### 3.3 利用flex布局

利用flex布局，其中`justify-content` 用于设置或检索弹性盒子元素在主轴（横轴）方向上的对齐方式；而`align-items`属性定义flex子项在flex容器的当前行的侧轴（纵轴）方向上的对齐方式。

** 核心代码：**

```css
.parent{
    display: flex;
    justify-content: center;
    align-items: center;
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/69)

### 3.4 利用grid布局

利用grid实现水平垂直居中，兼容性较差，不推荐。

** 核心代码：**

```css
.parent{
  height:140px;
  display: grid;
}
.child{ 
  margin: auto;
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/70)

### 3.5 屏幕上水平垂直居中

屏幕上水平垂直居中十分常用，常规的登录及注册页面都需要用到。要保证较好的兼容性，还需要用到表布局。

** 核心代码：**

```css
.outer{
    display: table;
    position: absolute;
    height:100%;
    width:100%;
}
.middle{
    display: table-cell;
    vertical-align: middle;
}
.inner{
    margin-left: auto;
    margin-right: auto; 
    width:400px;
}
```

​    

**  演示程序：**

[演示代码](http://www.42du.cn/run/10)

## 4 说明

文中所述文字及代码部分汇编于网络。因时间不足，能力有限等原因，存在文字阐述不准及代码测试不足等诸多问题。因此只限于学习范围，不适用于实际应用。

文中所述方案只是居中方案其中的一部分，并不是全部。另代码中涉及CSS3的flex，transform，grid等内容都存在兼容性问题。

## 5 引用参考

[Centering in CSS: A Complete Guide](https://css-tricks.com/centering-css-complete-guide/)

[w3.org centering things](https://www.w3.org/Style/Examples/007/center.en.html)

[How To Center Anything With CSS](https://mayvendev.com/blog/how-to-center-anything-with-css)

[如何使DIV在屏幕上水平垂直居中显示？](http://www.42du.cn/paper/10)