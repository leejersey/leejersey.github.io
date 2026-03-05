# Hexo 博客日常操作指南

## 1. 核心流程与分支管理（必看 🚨）

当前项目采用了**源码与静态文件隔离**的分支管理方式：

- **源码分支 (`hexo-source`)**：平时工作的地方。存放 Markdown 文章、主题、配置文件。**写文章、改配置后，需要像普通代码一样 add, commit, push 备份到这个分支。**
- **发布分支 (`master`)**：仅存放生成的 HTML 网页。**绝对不要**手动切换到这个分支修改任何文件。`hexo deploy` 会自动把你的文章变成网页并推送到这个分支。

---

## 2. 日常写作与发布指令

在终端中打开项目目录（`/Users/lizexi/Documents/code/leejersey.github.io`），运行以下命令：

### 第一步：新建一篇文章
```bash
npx hexo new "文章标题"
```
> 执行后，会在 `source/_posts/` 目录下生成一个 `文章标题.md` 的文件，你可以在里面使用 Markdown 语法书写正文。

### 第二步：本地预览（可选）
```bash
npx hexo clean && npx hexo generate && npx hexo server
```
> 启动本地服务器。在浏览器打开 `http://localhost:4000` 预览刚写的文章。确认无误后，在终端按 `Ctrl + C` 退出。

### 第三步：发布到线上网站
```bash
npx hexo clean && npx hexo generate && npx hexo deploy
```
> 一键将网页推送到 GitHub 的 `master` 分支！请注意：推送成功后，GitHub Pages 需要大概 1~3 分钟的缓存刷新时间，稍后访问你的博客就能看到新文章了。

### 第四步：云端备份源码（千万别忘 ⚠️）
文章发布后，务必将你写好的 `.md` 源码同步保存到 GitHub，防止日后电脑重装导致数据丢失：
```bash
git add .
git commit -m "新增文章：文章标题"
git push origin hexo-source
```

---

## 3. 重要的项目结构

如果以后需要修改博客的细节，请认准以下位置：

- **`source/_posts/`**：你的所有博客文章（Markdown）都在这里。
- **`_config.yml`**：站点的系统配置。如果要修改网站名（Title）、语言、部署等，改这个文件。
- **`themes/apollo/_config.yml`**：**Apollo 主题**的配置。如果要修改左侧导航栏菜单、Logo 图标、社交链接，改这个文件。
