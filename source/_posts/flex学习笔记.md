---
title: "flex学习笔记"
date: 2021-04-27
---

## 认识flex

flex布局现在已经是最常见的布局方式，最近碰到一些类似flex:0 1 auto的代码，决定升入学习一下

## felx

flex布局的属性，一般分为两大类：容器的属性，项目的属性

### 容器的属性

- flex-direction
- flex-wrap
- flex-flow
- justify-content
- align-items
- align-content

#### flex-direction

是决定主轴的方向，它有四个值对应四个方向，row是默认值，使主轴是水平的，而且是自西向东的，而row-reverse刚好相反，它设定的主轴是自东向西，column是从北到南，column-reverse是从南到北

#### flex-wrap

是否换行
有三个值nowrap是默认值，不换行，wrap换行第一行在上面，wrap-reverse换行，第一行在下面

#### flex-flow

注意：
**flex-flow其实就是flex-direction和flex-wrap的简写形式，默认值为：row nowrap**

#### justify-content

定义了主轴上的对齐方式，有五个值

- flex-start 是左对齐
- flex-end 右对齐
- space-between是两端对齐，项目之间的间隔都相等
- space-around 每个项目两边的距离是相等的，所以项目之间的距离是项目和边框距离的两倍。

#### align-items

定义项目在交叉轴上如何对齐的，有五个值

- flex-start 是交叉轴的起点对齐
- flex-end 交叉轴的终点对齐
- center 交叉轴中点对齐
- baseline 项目的第一行文字的基线对齐
- stretch 如果项目未设置高度，或者设置的为auto，将填满整个容器的高度

#### align-content

定义了多根轴线的对齐方式

- flex-start 与交叉轴的起点对齐
- flex-end 与交叉轴的终点对齐
- center 与交叉轴的中点对齐
- space-btween 与交叉轴的两端对齐，轴线之间的间隔平均分配
- space-around 每根轴线两边的间隔都是相等的，所以轴线之间的间隔是轴线和边框的间隔的两倍
stretch 轴线占满整个交叉轴

### 项目的属性

- order
- flex-grow
- flex-shrink
- flex-basis
- flex
- align-self

#### order

定义项目排列顺序 数值越小，排列越靠前 默认为零

#### flex-gorw

定义项目的放大比例，默认值为0，即就算存在剩余空间也不放大，如果所有项目数值为1的话就是所有项目等分剩余空间，如果有一个项目的flex-grow属性为2，其余项目都为1时，则前者占据的剩余空间是后者的两倍。

#### flex-shrink

定义了项目的缩小比例，默认值为1，即如果空间不足的话，所有项目等比例缩小，如果有一个项目的flex-shrink的属性为0，其他项目的为1，则空间不足时，前者不缩小，后者等比例缩小。

#### flex-basis

定义了在分配多余空间之前，项目占据的主轴空间（main size），浏览器根据这个属性计算出主轴是否有剩余空间，它的默认值为auto即项目本身的大小，它可以设为跟width或height属性一样的值（比如350px），则项目将占据固定空间。

注意：
**flex属性是flex-grow，flex-shrink和flex-basis的简写，默认值为0 1 auto，该属性有两个快捷值auto（1 1 auto）和none(0 0 auto)**

#### align-self

允许单个项目与其他项目不一样的对齐方式，可覆盖align-items的属性，默认值为auto，表示继承父元素的属性，如果没有父元素，则等同于stretch，该属性可能取6个值，除了auto，其他都与align-items属性完全一致。

完全指南：[https://css-tricks.com/snippets/css/a-guide-to-flexbox/#examples](https://css-tricks.com/snippets/css/a-guide-to-flexbox/#examples)