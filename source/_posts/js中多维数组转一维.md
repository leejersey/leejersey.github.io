---
title: "js中多维数组转一维"
date: 2018-12-22
---

法一：使用数组map()方法，对数组中的每一项运行给定函数，返回每次函数调用的结果组成的数组。

```javascript
var arr = [1,[2,[[3,4],5],6]];
function unid(arr){
        var arr1 = (arr + '').split(',');//将数组转字符串后再以逗号分隔转为数组
        var arr2 = arr1.map(function(x){
            return Number(x);
        });
        return arr2;
}
console.log(unid(arra));
```

法二：将数组转为字符串再转为数组，缺点是数组中每项成字符串了

```javascript
var arr = [1,[2,[[3,4],5],6]];
var arr2 = arr.join(',').split(',');
console.log(arr2);//["1", "2", "3", "4", "5", "6"]
//或
var c=[1,3,4,5,[6,[0,1,5],9],[2,5,[1,5]],[5]];
console.log(c.toString().split(','))
```

法三：递归

```javascript
var arr = [1,[2,[[3,4],5],6]];
var newArr = [];
    
function fun(arr){
        for(var i=0;i arr.reduce(
    (acc,val) => acc.concat(Array.isArray(val)? flatten(val):val),[]
)
console.log(flatten(arr));//[1, 2, 3, 4, 5, 6]
```