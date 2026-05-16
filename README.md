# Jersey's Blog

> 基于 VitePress 的个人技术知识库，内容自动同步自 Obsidian 仔库。

## 🏗️ 架构

```
Obsidian 仓库（只读，不修改）
  │
  │  python sync_docs.py
  │  ① 复制 .md → docs/
  │  ② [[wikilink]] → 标准链接
  │  ③ Obsidian callout → VitePress 容器
  │  ④ 自动生成 sidebar.json
  ▼
VitePress 项目（本仓库）
  │
  │  npm run build
  ▼
GitHub Pages（自动部署）
```

---

## 📋 日常使用

### 1. 写完笔记后同步 & 预览

```bash
# 进入项目目录
cd ~/Documents/code/leejersey.github.io

# 同步 Obsidian 笔记到 VitePress
python sync_docs.py

# 本地预览
npm run dev
# 浏览器打开 http://localhost:5173
```

### 2. 发布到线上

```bash
# 同步 + 提交 + 推送（一键完成）
python sync_docs.py
git add -A
git commit -m "docs: 更新笔记"
git push

# GitHub Actions 会自动构建并部署到 GitHub Pages
```

### 3. 一键脚本（推荐）

在项目根目录运行：

```bash
# 同步 + 提交 + 推送
python sync_docs.py && git add -A && git commit -m "docs: sync $(date +%Y-%m-%d)" && git push
```

---

## 📁 项目结构

```
leejersey.github.io/
├── docs/                          ← VitePress 文档目录
│   ├── .vitepress/
│   │   ├── config.mts             ← 主配置（主题、导航、插件）
│   │   └── sidebar.json           ← 侧边栏（sync_docs.py 自动生成）
│   ├── index.md                   ← 首页（Hero + Features 卡片）
│   ├── guide.md                   ← 知识库总览（来自 HOME.md）
│   ├── public/logo.svg            ← 站点 Logo
│   ├── AI工程化/                  ← 同步的笔记目录
│   ├── python/
│   ├── 后端工程/
│   └── ...（23 个分类）
├── sync_docs.py                   ← Obsidian → VitePress 同步脚本
├── package.json                   ← Node.js 依赖
├── .github/workflows/deploy.yml   ← GitHub Actions 自动部署
└── .gitignore
```

---

## ⚙️ 配置说明

### 排除目录

在 `sync_docs.py` 中修改 `EXCLUDE_DIRS`：

```python
EXCLUDE_DIRS = {
    ".obsidian", ".agents", ".claude", ".vscode",
    "Inbox", "求职与面试", "想法与项目", "python知识点",
    # 新增排除目录在这里加
}
```

### 修改导航栏

编辑 `docs/.vitepress/config.mts` 的 `nav` 部分。

### 修改首页

编辑 `docs/index.md` 的 YAML frontmatter。

### 自定义域名

1. 在 `docs/public/` 下创建 `CNAME` 文件，写入域名
2. 在域名 DNS 添加 CNAME 记录指向 `leejersey.github.io`
3. GitHub 仓库 Settings → Pages → Custom domain 填入域名

---

## 🔧 常用命令

| 命令 | 说明 |
|:---|:---|
| `python sync_docs.py` | 同步 Obsidian 笔记 |
| `npm run dev` | 本地开发预览 |
| `npm run build` | 构建生产版本 |
| `npm run preview` | 预览构建产物 |

---

## 📝 同步脚本做了什么

| 功能 | 说明 |
|:---|:---|
| 复制 `.md` 文件 | 保持原目录结构 |
| `[[wikilink]]` 转换 | `[[path/note]]` → `[note](path/note)` |
| `[[note\|别名]]` 转换 | → `[别名](note)` |
| Callout 转换 | `> [!TIP]` → `::: tip` |
| 生成 sidebar | 自动扫描目录生成 `sidebar.json` |
| 跳过排除目录 | 求职面试、私人笔记等不发布 |
| 跳过空文件 | 小于 10 字节的文件不同步 |
