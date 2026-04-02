# Jersey's Blog

> 坚持是一种品格

基于 [Hexo](https://hexo.io/) 构建的个人技术博客，使用 [Apollo](https://github.com/pinggod/hexo-theme-apollo) 主题，部署在 GitHub Pages。

🔗 **在线访问**：[https://leejersey.github.io](https://leejersey.github.io)

## ✨ 特性

- 📝 Hexo 7 静态博客框架
- 🎨 Apollo 简洁主题
- 📡 RSS 订阅（Atom Feed）
- 🗺️ Sitemap 自动生成
- 🚀 GitHub Pages 自动部署

## 📂 目录结构

```
.
├── source/_posts/       # 博客文章（Markdown）
├── scaffolds/           # 文章模板
├── themes/              # 主题
├── _config.yml          # Hexo 主配置
├── _config.apollo.yml   # Apollo 主题配置
└── package.json
```

## 🚀 快速开始

### 环境要求

- [Node.js](https://nodejs.org/) >= 14
- [Git](https://git-scm.com/)

### 安装依赖

```bash
npm install
```

### 本地预览

```bash
npm run server
```

访问 `http://localhost:4000` 查看博客。

### 新建文章

```bash
npx hexo new "文章标题"
```

文章会生成在 `source/_posts/` 目录下，使用 Markdown 编写。

### 构建 & 部署

```bash
# 清理缓存
npm run clean

# 生成静态文件
npm run build

# 部署到 GitHub Pages
npm run deploy
```

## 📄 内容主题

博客主要涵盖以下前端技术方向：

- **JavaScript** — 核心概念、ES6+、异步编程、设计模式
- **React** — Hooks、组件模式、性能优化、状态管理
- **CSS** — 布局技巧、BFC、自适应方案
- **算法** — 基础数据结构与常见算法题
- **工程化** — 编码规范、开发工具、最佳实践

## 📜 License

本博客内容采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 许可协议。
