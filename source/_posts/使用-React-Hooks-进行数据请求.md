---
title: "使用 React Hooks 进行数据请求"
date: 2020-05-08
---

转：[https://segmentfault.com/a/1190000018652589](https://segmentfault.com/a/1190000018652589)

通过这个教程，我想告诉你在 React 中如何使用 state 和 effect 这两种 hooks 去请求数据。我们将使用众所周知的 [Hacker News API](https://hn.algolia.com/api) 来获取一些热门文章。你将定义属于你自己的数据请求的 Hooks ，并且可以在你所有的应用中复用，也可以发布到 npm 。

如果你不了解 React 的这些新特性，可以查看我的另一篇文章 [introduction to React Hooks](https://www.robinwieruch.de/react-hooks/)。如果你想直接查看文章的示例，可以直接 checkout 这个 [Github 仓库](https://github.com/the-road-to-learn-react/react-hooks-introduction/blob/master/src/customHook-example/index.js)。

> 注意：在 React 未来的版本中，Hooks 将不会用了获取数据，取而代之的是一种叫做 `Suspense` 的东西。尽管如此，下面的方法依然是了解 state 和 effect 两种 Hooks 的好方法。

## 使用 React Hooks 进行数据请求

如果你没有过在 React 中进行数据请求的经验，可以阅读我的文章：[How to fetch data in React](https://www.robinwieruch.de/react-fetching-data/)。文章讲解了如何使用  Class components 获取数据，如何使用可重用的 Render Props Components 和 Higher Order Components ，以及如何进行错误处理和 loading 状态。在本文中，我想用 Function components 和 React Hooks 来重现这一切。

```javascript
import React, { useState } from'react';
    
functionApp() {
  const [data, setData] = useState({ hits: [] });
    
  return (
    
      {data.hits.map(item => (
        {item.title}
      ))}
    

  );
}
    
export default App;
```

App 组件将展示一个列表，列表信息来自 Hacker News articles 。状态和状态更新函数将通过被称为 `useState` 的状态钩子来生成，它负责管理通过请求得到的 App 组件的本地状态。初始状态是一个空数组，目前没有任何地方给它设置新的状态。

我们将使用 axios 来获取数据，当然也可以使用你熟悉的请求库，或者浏览器自带的 fetch API。如果你还没有安装过 axios ，可以通过 `npm install axios` 进行安装。

```javascript
import React, { useState, useEffect } from'react';
import axios from'axios';
    
functionApp() {
  const [data, setData] = useState({ hits: [] });
    
  useEffect(async () => {
    const result = await axios(
      'http://hn.algolia.com/api/v1/search?query=redux',
    );
    
    setData(result.data);
  });
    
  return (
    
      {data.hits.map(item => (
        {item.title}
      ))}
    

  );
}

export default App;
```

我们在 `useEffect` 这个 effect hook 中，通过 axios 从 API 中获取数据，并使用 state hook 的更新函数，将数据存入到本地 state 中。并且使用 async/await 来解析promise。

然而，当你运行上面的代码的时候，你会陷入到该死的死循环中。effect hook 在组件 mount 和 update 的时候都会执行。因为我们每次获取数据后，都会更新 state，所以组件会更新，并再次运行 effect，这会一次又一次的请求数据。很明显我们需要避免这样的bug产生，**我们只想在组件 mount 的时候请求数据**。你可以在 effect hook 提供的第二个参数中，传入一个空数组，这样做可以避免组件更新的时候执行 effect hook ，但是组件在 mount 依然会执行它。

```javascript
import React, { useState, useEffect } from'react';
import axios from'axios';
    
functionApp() {
  const [data, setData] = useState({ hits: [] });
    
  useEffect(async () => {
    const result = await axios(
      'http://hn.algolia.com/api/v1/search?query=redux',
    );
    
    setData(result.data);
  }, []);
    
  return (
    
      {data.hits.map(item => (
        {item.title}
      ))}
    

  );
}
    
export default App;
```

第二个参数是用来定义 hook 所以依赖的变量的。如果其中一个变量发生变化，hook 将自动运行。如果第二个参数是一个空数组，那么 hook 将不会在组件更新是运行，因为它没有监控任何的变量。

还有一个需要特别注意的点，在代码中，我们使用了 async/await 来获取第三方 API 提供的数据。根据文档，每一个 async 函数都将返回一个隐式的 promise：

> “The async function declaration defines an asynchronous function, which returns an AsyncFunction object. An asynchronous function is a function which operates asynchronously via the event loop, using an implicit Promise to return its result. “
> “async 函数定义了一个异步函数，它返回的是一个异步函数对象，异步函数是一个通过事件循环进行操作的函数，使用隐式的 Promise 返回最终的结果。”

然而，effect hook 应该是什么也不返回的，或者返回一个 clean up 函数的。这就是为什么你会在控制台看到一个错误信息。

`index.js:1452 Warning: useEffect functionmustreturnacleanupfunctionornothing. 
PromisesanduseEffect(async () => …) arenotsupported, butyoucancallanasyncfunctioninsideaneffect.`

这意味着我们不能直接在 `useEffect` 函数使用async。让我们来实现一个解决方案，能够在 effect hook 中使用 async 函数。

```javascript
import React, { useState, useEffect } from'react';
import axios from'axios';
    
functionApp() {
  const [data, setData] = useState({ hits: [] });
    
  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(
        'http://hn.algolia.com/api/v1/search?query=redux',
      );
    
      setData(result.data);
    };
    
    fetchData();
  }, []);
    
  return (
    
      {data.hits.map(item => (
        {item.title}
      ))}
    

  );
}
    
export default App;
```

这就是一个使用 React Hooks 进行数据请求的小案例。但是，如果你对错误处理、loading 态、如何触发表单数据获取以及如何复用出具处理 hook 感兴趣，那我们接着往下看。

## 如何手动或者自动触发一个 hook？

现在我们已经能够在组件 mount 之后获取到数据，但是，如何使用输入框动态告诉 API 选择一个感兴趣的话题呢？可以看到之前的代码，我们默认将 “Redux” 作为查询参数（’[http://hn.algolia.com/api/v1/…](http://hn.algolia.com/api/v1/search?query=redux)‘），但是我们怎么查询关于 React 相关的话题呢？让我们实现一个 input 输入框，可以获得除了 “Redux” 之外的其他的话题。现在，让我们为输入框引入一个新的 state。

```javascript
import React, { Fragment, useState, useEffect } from'react';
import axios from'axios';
    
functionApp() {
  const [data, setData] = useState({ hits: [] });
  const [query, setQuery] = useState('redux');
    
  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(
        'http://hn.algolia.com/api/v1/search?query=redux',
      );
    
      setData(result.data);
    };
    
    fetchData();
  }, []);
    
  return (
    
       setQuery(event.target.value)}
      />
      
        {data.hits.map(item => (
          {item.title}
        ))}
      

    
  );
}
    
export default App;
```

现在，请求数据和查询参数两个 state 相互独立，但是我们需要像一个办法希望他们耦合起来，只获取输入框输入的参数指定的话题文章。通过以下修改，组件应该在 mount 之后按照查询获取相应文章。

```javascript
functionApp() {
  const [data, setData] = useState({ hits: [] });
  const [query, setQuery] = useState('redux');
    
  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(
        `http://hn.algolia.com/api/v1/search?query=${query}`,
      );
    
      setData(result.data);
    };
    
    fetchData();
  }, []);
    
  return (
    ...
  );
}
    
export default App;
```

实际上，我们还缺少部分代码。你会发现当你在输入框输入内容后，并没有获取到新的数据。这是因为 useEffect 的第二个参数只是一个空数组，此时的 effect 不依赖于任何的变量，所以这只会在 mount 只会触发一次。但是，现在我们需要依赖查询条件，一旦查询发送改变，数据请求就应该再次触发。

```javascript
function App() {
  const [data, setData] = useState({ hits: [] });
  const [query, setQuery] = useState('redux');
    
  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(
        `http://hn.algolia.com/api/v1/search?query=${query}`,
      );
    
      setData(result.data);
    };
    
    fetchData();
  }, [query]);
    
  return (
    ...
  );
}
    
export default App;
```

好了，现在一旦你改变输入框内容，数据就会重新获取。但是现在又要另外一个问题：每次输入一个新字符，就会触发 effect 进行一次新的请求。那么我们提供一个按钮来手动触发数据请求呢？

```javascript
function App() {
  const [data, setData] = useState({ hits: [] });
  const [query, setQuery] = useState('redux');
  const [search, setSearch] = useState('redux');
    
  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(
        `http://hn.algolia.com/api/v1/search?query=${search}`,
      );
    
      setData(result.data);
    };
    
    fetchData();
  }, [search]);
    
  return (
    
       setQuery(event.target.value)}
      />
       setSearch(query)}>
        Search
      
      
        {data.hits.map(item => (
          {item.title}
        ))}
      

      
  );
}
```

此外，search state 的初始状态也是设置成了与 query state 相同的状态，因为组件在 mount 的时候会请求一次数据，此时的结果也应该是反应的是输入框中的搜索条件。然而， search state 和 query state 具有类似的值，这看起来比较困惑。为什么不将真实的 URL 设置到 search state 中呢？

```javascript
function App() {
  const [data, setData] = useState({ hits: [] });
  const [query, setQuery] = useState('redux');
  const [url, setUrl] = useState(
    'http://hn.algolia.com/api/v1/search?query=redux',
  );
    
  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(url);
    
      setData(result.data);
    };
    
    fetchData();
  }, [url]);
    
  return (
    
       setQuery(event.target.value)}
      />
      
          setUrl(`http://hn.algolia.com/api/v1/search?query=${query}`)
        }
      >
        Search
      
      
        {data.hits.map(item => (
          {item.title}
        ))}
      

    
  );
}
```

这就是通过 effect hook 获取数据的案例，你可以决定 effect 取决于哪个 state。在这个案例中，如果 URL 的 state 发生改变，则再次运行该 effect 通过 API 重新获取主题文章。

## Loading 态 与 React Hooks

让我们在数据的加载过程中引入一个 Loading 状态。它只是另一个由 state hook 管理的状态。Loading state 用于在 App 组件中呈现 Loading 状态。

```javascript
import React, { Fragment, useState, useEffect } from'react';
import axios from'axios';
    
function App() {
  const [data, setData] = useState({ hits: [] });
  const [query, setQuery] = useState('redux');
  const [url, setUrl] = useState(
    'http://hn.algolia.com/api/v1/search?query=redux',
  );
  const [isLoading, setIsLoading] = useState(false);
    
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
    
      const result = await axios(url);
    
      setData(result.data);
      setIsLoading(false);
    };
    
    fetchData();
  }, [url]);
    
  return (
    
        setQuery(event.target.value)}
      />
      
          setUrl(`http://hn.algolia.com/api/v1/search?query=${query}`)
        }
      >
        Search
      
    
      {isLoading ? (
        Loading ...
      ) : (
        
          {data.hits.map(item => (
            {item.title}
          ))}
        

      )}
    
  );
}
    
export default App;
```

现在当组件处于 mount 状态或者 URL state 被修改时，调用 effect 获取数据，Loading 状态就会变成 true。一旦请求完成，Loading 状态就会再次被设置为 false。

## 错误处理与 React Hooks

通过 React Hooks 进行数据请求时，如何进行错误处理呢？ 错误只是另一个使用 state hook 初始化的另一种状态。一旦出现错误状态，App 组件就可以反馈给用户。当使用  async/await 函数时，通常使用 try/catch 来进行错误捕获，你可以在 effect 中进行下面操作：

```javascript
const [isError, setIsError] = useState(false);
    
useEffect(() => {
  const fetchData = async () => {
    setIsError(false);
    setIsLoading(true);
    
    try {
      const result = await axios(url);
      setData(result.data);
    } catch (error) {
      setIsError(true);
    }
    
    setIsLoading(false);
  };
    
  fetchData();
}, [url]);
    
return (
  
    ...
    {isError && Something went wrong ...}
    ...
  
);
```

effect 每次运行都会重置 error state 的状态，这很有用，因为每次请求失败后，用户可能重新尝试，这样就能够重置错误。为了观察代码是否生效，你可以填写一个无用的 URL ，然后检查错误信息是否会出现。

## 使用表单进行数据获取

什么才是获取数据的正确形式呢？现在我们只有输入框和按钮进行组合，一旦引入更多的 input 元素，你可能想要使用表单来进行包装。此外表单还能够触发键盘的 “Enter” 事件。

```javascript
function App() {
  ...
  const doFetch = (evt) => {
    evt.preventDefault();
    setUrl(`http://hn.algolia.com/api/v1/search?query=${query}`);
  }
  return (
    
      
        setQuery(event.target.value)}
        />
        Search
    
      {isError && Something went wrong ...}
    
      ...
    
  );
}
```

## 自定义 hook 获取数据

我们可以定义一个自定义的 hook，提取出所有与数据请求相关的东西，除了输入框的 query state，除此之外还有 Loading 状态、错误处理。还要确保返回组件中需要用到的变量。

```javascript
const useHackerNewsApi = () => {
  const [data, setData] = useState({ hits: [] });
  const [url, setUrl] = useState(
    'http://hn.algolia.com/api/v1/search?query=redux',
  );
  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);
    
  useEffect(() => {
    const fetchData = async () => {
      setIsError(false);
      setIsLoading(true);
    
      try {
        const result = await axios(url);
    
        setData(result.data);
      } catch (error) {
        setIsError(true);
      }
    
      setIsLoading(false);
    };
    
    fetchData();
  }, [url]);
    
  const doFetch = () => {
    setUrl(`http://hn.algolia.com/api/v1/search?query=${query}`);
  };
    
  return { data, isLoaing, isError, doFetch };
}
```

现在，我们在 App 组件中使用我们的新 hook 。

```
function App() {
  const [query, setQuery] = useState(&apos;redux&apos;);
  const { data, isLoading, isError, doFetch } = useHackerNewsApi();
    
  return (
    
      ...
    
  );
}
```

接下来，在外部传递 URL 给 `DoFetch` 方法。

```javascript
const useHackerNewsApi = () => {
  ...
    
  useEffect(
    ...
  );
    
  const doFetch = url => {
    setUrl(url);
  };
    
  return { data, isLoading, isError, doFetch };
};
    
functionApp() {
  const [query, setQuery] = useState('redux');
  const { data, isLoading, isError, doFetch } = useHackerNewsApi();
    
  return (
    
       {
          doFetch(
            `http://hn.algolia.com/api/v1/search?query=${query}`,
          );
    
          event.preventDefault();
        }}
      >
         setQuery(event.target.value)}
        />
        Search
    
      ...
    
  );
}
```

初始的 state 也是通用的，可以通过参数简单的传递到自定义的 hook 中：

```javascript
import React, { Fragment, useState, useEffect } from 'react';
import axios from 'axios';
    
const useDataApi = (initialUrl, initialData) => {
  const [data, setData] = useState(initialData);
  const [url, setUrl] = useState(initialUrl);
  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);
    
  useEffect(() => {
    const fetchData = async () => {
      setIsError(false);
      setIsLoading(true);
    
      try {
        const result = await axios(url);
    
        setData(result.data);
      } catch (error) {
        setIsError(true);
      }
    
      setIsLoading(false);
    };
    
    fetchData();
  }, [url]);
    
  const doFetch = url => {
    setUrl(url);
  };
    
  return { data, isLoading, isError, doFetch };
};
    
functionApp() {
  const [query, setQuery] = useState('redux');
  const { data, isLoading, isError, doFetch } = useDataApi(
    'http://hn.algolia.com/api/v1/search?query=redux',
    { hits: [] },
  );
    
  return (
     {
          doFetch(
            `http://hn.algolia.com/api/v1/search?query=${query}`,
          );
    
          event.preventDefault();
        }}
      >
         setQuery(event.target.value)}
        />
        Search
    
      {isError && Something went wrong ...}
    
      {isLoading ? (
        Loading ...
      ) : (
        
          {data.hits.map(item => (
            {item.title}
          ))}
        

      )}
    
  );
}

export default App;
```

这就是使用自定义 hook 获取数据的方法，hook 本身对API一无所知，它从外部获取参数，只管理必要的 state ，如数据、 Loading 和错误相关的 state ，并且执行请求并将数据通过 hook 返回给组件。

## 用于数据获取的 Reducer Hook

目前为止，我们已经使用 state hooks 来管理了我们获取到的数据数据、Loading 状态、错误状态。然而，所有的状态都有属于自己的 state hook，但是他们又都连接在一起，关心的是同样的事情。如你所见，所有的它们都在数据获取函数中被使用。它们一个接一个的被调用（比如：`setIsError`、`setIsLoading`），这才是将它们连接在一起的正确用法。让我们用一个 Reducer Hook 将这三者连接在一起。

Reducer Hook 返回一个 state 对象和一个函数（用来改变 state 对象）。这个函数被称为分发函数（dispatch function），它分发一个 action，action 具有 type 和 payload 两个属性。所有的这些信息都在 reducer 函数中被接收，根据之前的状态提取一个新的状态。让我们看看在代码中是如何工作的：

```javascript
import React, {
  Fragment,
  useState,
  useEffect,
  useReducer,
} from'react';
import axios from'axios';
    
const dataFetchReducer = (state, action) => {
  ...
};
    
const useDataApi = (initialUrl, initialData) => {
  const [url, setUrl] = useState(initialUrl);
    
  const [state, dispatch] = useReducer(dataFetchReducer, {
    isLoading: false,
    isError: false,
    data: initialData,
  });
    
  ...
};
```

Reducer Hook 以 reducer 函数和一个初始状态对象作为参数。在我们的案例中，加载的数据、Loading 状态、错误状态都是作为初始状态参数，且不会发生改变，但是他们被聚合到一个状态对象中，由 reducer hook 管理，而不是单个 state hooks。

```javascript
const dataFetchReducer = (state, action) => {
  ...
};
    
const useDataApi = (initialUrl, initialData) => {
  const [url, setUrl] = useState(initialUrl);
    
  const [state, dispatch] = useReducer(dataFetchReducer, {
    isLoading: false,
    isError: false,
    data: initialData,
  });
    
  useEffect(() => {
    const fetchData = async () => {
      dispatch({ type: 'FETCH_INIT' });
    
      try {
        const result = await axios(url);
    
        dispatch({ type: 'FETCH_SUCCESS', payload: result.data });
      } catch (error) {
        dispatch({ type: 'FETCH_FAILURE' });
      }
    };
    
    fetchData();
  }, [url]);
    
  ...
};
```

现在，在获取数据时，可以使用 dispatch 函数向 reducer 函数发送信息。使用 dispatch 函数发送的对象具有一个必填的 `type` 属性和一个可选的 `payload` 属性。type 属性告诉 reducer 函数需要转换的 state 是哪个，还可以从 payload 中提取新的 state。在这里只有三个状态转换：初始化数据过程，通知数据请求成功的结果，以及通知数据请求失败的结果。

在自定义 hook 的末尾，state 像以前一样返回，但是因为我们所有的 state 都在一个对象中，而不再是独立的 state ，所以 state 对象进行解构返回。这样，调用 `useDataApi` 自定义 hook 的人仍然可以 `data`  、`isLoading`和`isError`:

```javascript
const useDataApi = (initialUrl, initialData) => {
  const [url, setUrl] = useState(initialUrl);
    
  const [state, dispatch] = useReducer(dataFetchReducer, {
    isLoading: false,
    isError: false,
    data: initialData,
  });
    
  ...
    
  const doFetch = url => {
    setUrl(url);
  };
    
  return { ...state, doFetch };
};
```

最后我们还缺少 reducer 函数的实现。它需要处理三个不同的状态转换，分被称为 `FEATCH_INIT`、`FEATCH_SUCCESS`、`FEATCH_FAILURE`。每个状态转换都需要返回一个新的状态。让我们看看使用 switch case 如何实现这个逻辑：

```javascript
const dataFetchReducer = (state, action) => {
  switch (action.type) {
    case'FETCH_INIT':
      return { ...state };
    case'FETCH_SUCCESS':
      return { ...state };
    case'FETCH_FAILURE':
      return { ...state };
    default:
      thrownewError();
  }
};
```

reducer 函数可以通过其参数访问当前状态和 dispatch 传入的 action。到目前为止，在 switch case 语句中，每个状态转换只返回前一个状态，析构语句用于保持 state 对象不可变(即状态永远不会被直接更改)。现在让我们重写一些当前 state 返回的属性，以便在每次转换时更改 一些 state:

```javascript
const dataFetchReducer = (state, action) => {
  switch (action.type) {
    case 'FETCH_INIT':
      return {
        ...state,
        isLoading: true,
        isError: false
      };
    case 'FETCH_SUCCESS':
      return {
        ...state,
        isLoading: false,
        isError: false,
        data: action.payload,
      };
    case 'FETCH_FAILURE':
      return {
        ...state,
        isLoading: false,
        isError: true,
      };
    default:
      throw new Error();
  }
};
```

现在，每个状态转换（action.type决定）都返回一个基于先前 state 和可选 payload 的新状态。例如，在请求成功的情况下，payload 用于设置新 state 对象的 data 属性。

总之，reducer hook 确保使用自己的逻辑封装状态管理的这一部分。通过提供 action type 和可选 payload ，总是会得到可预测的状态更改。此外，永远不会遇到无效状态。例如，以前可能会意外地将 `isLoading` 和 `isError` 设置为true。在这种情况下，UI中应该显示什么？ 现在，由 reducer 函数定义的每个 state 转换都指向一个有效的 state 对象。

## 在 Effect Hook 中中断数据请求

在React中，即使组件已经卸载，组件 state 仍然会被被赋值，这是一个常见的问题。我在之前的文章中写过这个问题，它描述了[如何防止在各种场景中为未挂载组件设置状态](https://www.robinwieruch.de/react-warning-cant-call-setstate-on-an-unmounted-component/)。让我们看看在自定义 hook 中，请求数据时如何防止设置状态：

```javascript
const useDataApi = (initialUrl, initialData) => {
  const [url, setUrl] = useState(initialUrl);

  const [state, dispatch] = useReducer(dataFetchReducer, {
    isLoading: false,
    isError: false,
    data: initialData,
  });

  useEffect(() => {
    let didCancel = false;

    const fetchData = async () => {
      dispatch({ type: 'FETCH_INIT' });

      try {
        const result = await axios(url);

        if (!didCancel) {
          dispatch({ type: 'FETCH_SUCCESS', payload: result.data });
        }
      } catch (error) {
        if (!didCancel) {
          dispatch({ type: 'FETCH_FAILURE' });
        }
      }
    };

    fetchData();

    return () => {
      didCancel = true;
    };
  }, [url]);

  const doFetch = url => {
    setUrl(url);
  };

  return { ...state, doFetch };
};
```

每个Effect Hook都带有一个clean up函数，它在组件卸载时运行。clean up 函数是 hook 返回的一个函数。在该案例中，我们使用 `didCancel` 变量来让 `fetchData` 知道组件的状态(挂载/卸载)。如果组件确实被卸载了，则应该将标志设置为 `true`，从而防止在最终异步解析数据获取之后设置组件状态。

> 注意：实际上并没有中止数据获取（不过可以通过Axios取消来实现），但是不再为卸载的组件执行状态转换。由于 Axios 取消在我看来并不是最好的API，所以这个防止设置状态的布尔标志也可以完成这项工作。

[原文链接](https://www.robinwieruch.de/react-hooks-fetch-data/)