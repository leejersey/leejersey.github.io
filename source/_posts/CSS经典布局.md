---
title: "CSS经典布局"
date: 2018-10-08
---

- 左右布局：左边定宽、右边自适应
- 三栏式布局
- 圣杯布局
- 双飞翼布局
- 圣杯和双飞翼异同
- 利用浮动实现
- 负 magin
- 清除浮动
- 居中布局
- 响应式设计
- Flexbox 布局

本文主要对 CSS 布局中常见的经典问题进行简单说明，并提供相关解决方案的参考链接，涉及到三栏式布局，负 margin，清除浮动，居中布局，响应式设计，Flexbox 布局，等等。

## 左右布局：左边定宽、右边自适应

- 
absolute + padding

  
```html

  
    .example-1 {
      position: relative;
      height: 100px;
      width: 60%;
      padding-left: 100px;
    }
    .example-1 .left {
      position: absolute;
      width: 100px;
      left: 0;
      height: 100%;
      background: #0f0;
    }
    .example-1 .right {
      background: #f00;
      width: 100%;
      height: 100%;
    }
  
  left
  right

```

- 
flex，未来趋势，推荐!

  
```html

  
    .example-2 {
      display: flex;
      height: 100px;
      width: 60%;
    }
    .example-2 .left {
      width: 100px;
      height: 100%;
      background: #0f0;
    }
    .example-2 .right {
      background: #f00;
      height: 100%;
      flex-grow: 1;
    }
  
  left
  right

```

- 
table

  
```html

  
    .example-3 {
      display: table;
      height: 100px;
      width: 60%;
    }
    .example-3 .left {
      width: 100px;
      height: 100%;
      background: #0f0;
      display: table-cell;
    }
    .example-3 .right {
      background: #f00;
      height: 100%;
      display: table-cell;
    }
  
  left
  right

```

- 
float 解决方案

  
```html

  
    .example-4 {
      height: 100px;
      width: 60%;
    }
    .example-4 .left {
      float: left;
      width: 100px;
      height: 100%;
      background: #0f0;
    }
    .example-4 .right {
      background: #f00;
      overflow: hidden;
      height: 100%;
    }
  
  left
  right

```

- 
参考：[alonia](http://blog.csdn.net/alonia/article/details/50957511), `calc` 属性！

```html

  
    .example-5 {
      height: 100px;
      width: 60%;
    }
    .example-5:after {
      clear: both;
    }
    .example-5 .left {
      width: 100px;
      height: 100%;
      background: #0f0;
      float: left;
    }
    .example-5 .right {
      background: #f00;
      height: 100%;
      width: calc(100% - 100px);
      float: right;
    }
  
  left
  right

```

## 三栏式布局

涉及浮动和清除浮动，主要讲解“圣杯”和“双飞翼”两种解决方法。这两种方法实现的都是三栏布局，两边的盒子宽度固定，中间盒子自适应，它们实现的效果是一样的，差别在于其实现的思想。

### 圣杯布局

圣杯：父盒子包含三个子盒子（左，中，右）

- 
中间盒子的宽度设置为 `width: 100%;` 独占一行；

- 
使用负边距(均是 `margin-left`)把左右两边的盒子都拉上去和中间盒子同一行；

- 
`.left {margin-left:-100%;}` 把左边的盒子拉上去

- 
`.right {margin-left：-右边盒子宽度px;}` 把右边的盒子拉上去

- 
父盒子设置左右的 padding 来为左右盒子留位置；

- 
对左右盒子使用相对布局来占据 padding 的空白，避免中间盒子的内容被左右盒子覆盖；

  
```html

    
    中间弹性区
    左边栏
    右边栏

```

### 双飞翼布局

双飞翼：父盒子包含三个子盒子（左，中，右），中间的子盒子里再加一个子盒子。

- 
中间盒子的宽度设置为 `width: 100%;` 独占一行；

- 
使用负边距(均是 `margin-left`)把左右两边的盒子都拉上去和中间盒子同一行；

- 
在中间盒子里面再添加一个 div，然后对这个 div 设置 `margin-left` 和 `margin-right`来为左右盒子留位置；

  
```html

    
    
         中间弹性区
    
    左边栏
    右边栏

```

### 圣杯和双飞翼异同

圣杯布局和双飞翼布局解决的问题是一样的，都是两边定宽，中间自适应的三栏布局，中间栏要在放在文档流前面以优先渲染。

- 两种方法基本思路都相同：三栏全部 float 浮动。首先让中间盒子 100% 宽度占满同一高度的空间，在左右两个盒子被挤出中间盒子所在区域时，使用 margin-left 的负值将左右两个盒子拉回与中间盒子同一高度的空间。接下来进行一些调整避免中间盒子的内容被左右盒子遮挡。
- 
主要区别在于 **如何使中间盒子的内容不被左右盒子遮挡**：

- 
圣杯布局的方法：设置父盒子的 padding 值为左右盒子留出空位，再利用相对布局对左右盒子调整位置占据 padding 出来的空位；

- 双飞翼布局的方法：在中间盒子里再增加一个子盒子，直接设置这个子盒子的 margin 值来让出空位，而不用再调整左右盒子。

简单说起来就是双飞翼布局比圣杯布局多创建了一个 div，但不用相对布局了，少设置几个属性。

### 利用浮动实现

我自己使用浮动也实现了三栏式布局：左边盒子左浮动，右边盒子右浮动，中间盒子利用 `margin-left` 和 `margin-right` 来为左右盒子留位置，同时父盒子设置 `overflow: auto;` 来避免子盒子溢出。

```html

    左边栏
    右边栏
    
    中间弹性区

```

三栏式布局参考下面几个链接:

- [CSS三栏布局——中间固定两边自适应宽度](http://www.w3cplus.com/blog/104.html)： w3cplus 的文章，使用了双飞翼和浮动实现两侧定宽、中间自适应，也实现了两侧自适应、中间定宽
- [简书 - 圣杯布局和双飞翼布局（前端面试必看）](http://www.jianshu.com/p/f9bcddb0e8b4)：只讲了圣杯，不过特别详细
- [In Search of the Holy Grail](https://alistapart.com/article/holygrail)：圣杯布局的来源
- [百度前端学院笔记 - 三栏式布局之双飞翼与圣杯](http://ife.baidu.com/note/detail/id/1025)：百度前端学院学员的前端学习笔记

三栏式布局涉及到负 magin 和 清除浮动的问题。

## 负 magin

这里引出了“负 margin”的问题：

- [负margin用法权威指南](https://www.w3cplus.com/css/the-definitive-guide-to-using-negative-margins.html)：[The Definitive Guide to Using Negative Margins](https://www.smashingmagazine.com/2009/07/the-definitive-guide-to-using-negative-margins/) 的译文,介绍了负 magin 的一些性质和很多实用技巧
- [简书 - margin为负值产生的影响和常见布局应用](http://www.jianshu.com/p/549aaa5fabaa)：包括对自身的影响，对文档流的影响，以及一些在布局中的应用技巧(比如去除列表右边框，负边距+定位实现水平垂直居中，去除列表最后一个 li 元素的 border-bottom，多列等高)
- [博客园 - CSS布局奇淫巧计之-强大的负边距](http://www.cnblogs.com/2050/archive/2012/08/13/2636467.html)：和上文内容差不多

简单总结几点：

- 不使用 float 的话，负 margin 元素是不会破坏页面的文档流。所以如果你使用负 margin 上移一个元素，所有跟随的元素都会被上移(而 relative 定位的元素则不同，会保留原位置，影响文档流)。
- 当 static 元素的 margin-top/margin-left 被赋予负值时，元素将被拉进指定的方向。
- 如果你设置 margin-bottom/right 为负数，元素并不会如你所想的那样向下/右移动，而是将后续的元素拖拉进来，覆盖本来的元素。
- 当元素不存在 width 属性或者 `width: auto` 的时候，负 margin 会增加元素的宽度.
- margin-top 为负值不会增加高度，只会产生向上位移;margin-bottom 为负值不会产生位移，会减少自身的供 CSS 读取的高度，影响下方的元素位置；上下相邻的元素两者均为负时，效果不叠加，取负值更多的那个效果。

## 清除浮动

清除浮动主要是为了解决高度塌陷问题。而简单的 `clear: both` 并不能解决这个问题，所以引出了许多解决方案。

- [StackOverflow - What methods of ‘clearfix’ can I use?](http://stackoverflow.com/questions/211383/what-methods-of-clearfix-can-i-use)：清除浮动黑科技完整解读
- [那些年我们一起清除过的浮动](http://www.iyunlu.com/view/css-xhtml/55.html)：神文，把“清除浮动”定义为“闭合浮动”，把问题由来和解决方案都讲清楚了，并且分析了各种解决方案的优劣。

各种解决方案在上面的链接里有很详细的说明了，这里就不赘述了。大体分为两类：

> - 其一，通过在浮动元素的末尾添加一个空元素，设置 `clear: both` 属性，after 伪元素其实也是通过 content 在元素的后面生成了内容为一个点的块级元素；
> - 其二，通过设置父元素 `overflow` 或者 `display: table` 属性来闭合浮动

*顺便补充一句，clear float(例如 `clear: left`) 是对某个元素设置，以避免其某一边有浮动元素，即对当前元素产生约束，约束的边界为其他的浮动元素。对于已经浮动的元素，设置 clear float 是无效的。*

## 居中布局

- [Centering in CSS: A Complete Guide](https://css-tricks.com/centering-css-complete-guide/)：非常全面的居中定位博客，包括各种情况下的水平居中，垂直居中和水平垂直居中方案。有展示示例及相应的 HTML 和 CSS 代码

文章大致结构：

- 
水平居中

- 
对于行内元素(inline)：`text-align: center;`

- 对于块级元素(block)：设置宽度且 `marigin-left` 和 `margin-right` 是设成 auto
- 
对于多个块级元素：对父元素设置 `text-align: center;`，对子元素设置 `display: inline-block;`；或者使用 flex 布局

- 
垂直居中

- 
对于行内元素(inline)

- 
单行：设置上下 pandding 相等；或者设置 `line-height` 和 `height` 相等

- 
多行：设置上下 pandding 相等；或者设置 `display: table-cell;` 和 `vertical-align: middle;`；或者使用 flex 布局；或者使用伪元素

- 
对于块级元素(block)：下面前两种方案，父元素需使用相对布局

- 
已知高度：子元素使用绝对布局 `top: 50%;`，再用负的 `margin-top` 把子元素往上拉一半的高度

- 未知高度：子元素使用绝对布局 `position: absolute; top: 50%; transform: translateY(-50%);`
- 
使用 Flexbox：选择方向，`justify-content: center;`

- 
水平垂直居中

- 
定高定宽：先用绝对布局 `top: 50%; left: 50%;`，再用和宽高的一半相等的负 margin 把子元素回拉

- 高度和宽度未知：先用绝对布局 `top: 50%; left: 50%;`，再设置 `transform: translate(-50%, -50%);`
- 使用 Flexbox：`justify-content: center; align-items: center;`

## 响应式设计

“响应式设计（Responsive Design)” 是一种让网站针对不同的浏览器和设备“呈现”不同显示效果的策略。

媒体查询(Media Queries)是做此事所需的最强大的工具。

*注： Responsive Web Design ＝ RWD，Adaptive Web Design ＝ AWD*

RWD：

- 采用 CSS 的 media query 技术
- 流体布局（fluid grids）
- 自适应的图片/视频等资源素材

（为小、中、大屏幕做一些优化，目的是让任何尺寸的屏幕空间都能得到充分利用）

AWD：

- CSS media query 技术（仅针对有限几种预设的屏幕尺寸设计）
- 用 JavaScript 来操作 HTML 内容
- 在服务器端操作 HTML 内容（比如为移动端减少内容，为桌面端提供更多内容）

> 以上 RWD 和 AWD 解释引自  [知乎 @屹峰](https://www.zhihu.com/question/20976405/answer/16781171)

可以参考 Bootstrap 的网格系统：[http://getbootstrap.com/css/#grid-less](http://getbootstrap.com/css/#grid-less)

> The Bootstrap 3 grid system has four tiers of classes: xs (phones), sm (tablets), md (desktops), and lg (larger desktops).

自己实现网格系统： [Creating Your Own CSS Grid System](http://j4n.co/blog/Creating-your-own-css-grid-system)

## Flexbox 布局

Flexbox 布局参考下面几篇文章就可以了，几篇文章大同小异，看一两篇就知道大概了，讲的挺详细的，在此不赘述

- [w3cplus - 一个完整的Flexbox指南](http://www.w3cplus.com/css3/a-guide-to-flexbox.html)：[A Complete Guide to Flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox/) 的译文
- [SegmentFault - Flexbox详解](https://segmentfault.com/a/1190000002910324)
- [w3cplus - 图解CSS3 Flexbox属性](https://www.w3cplus.com/css3/a-visual-guide-to-css3-flexbox-properties.html)
- [w3cplus - Flexbox——快速布局神器](http://www.w3cplus.com/css3/flexbox-basics.html)