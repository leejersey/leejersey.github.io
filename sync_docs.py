#!/usr/bin/env python3
"""
Obsidian → VitePress 同步脚本
从 Obsidian 仓库复制 .md 文件到 VitePress docs/ 目录，
转换 [[wikilink]] 为标准 markdown 相对链接。
"""

import os
import re
import json
import shutil
from pathlib import Path, PurePosixPath

OBSIDIAN_VAULT = Path(os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Iclound"
))
MKDOCS_DOCS = Path(__file__).parent / "docs"

EXCLUDE_DIRS = {
    ".obsidian", ".agents", ".claude", ".vscode", ".serverless",
    ".git", "Inbox", "求职与面试", "想法与项目", "python知识点",
    "node_modules",
}
EXCLUDE_FILES = {".DS_Store"}
PRESERVE_IN_DOCS = {".vitepress", "public", "index.md", "guide.md", "stylesheets"}

# 目录中文名映射（用于 sidebar 显示）
DIR_LABELS = {
    "AI工程化": "🔬 AI 工程化",
    "AI应用开发": "🤖 AI 应用开发",
    "AI成本控制": "💰 AI 成本控制",
    "AI流式输出": "🌊 AI 流式输出",
    "Docker入门教程": "🐳 Docker 入门",
    "FastAPI入门教程": "⚡ FastAPI 入门",
    "LangGraph实战教程": "🔗 LangGraph 实战",
    "MCP协议开发实战": "🔌 MCP 协议",
    "NextJS实战教程": "▲ Next.js 实战",
    "NodeJS": "🟢 Node.js",
    "PostgreSQL入门教程": "🐘 PostgreSQL",
    "Python Redis实战": "📮 Python Redis",
    "Redis入门教程": "🔴 Redis 入门",
    "SQLite入门教程": "📦 SQLite 入门",
    "devops": "🛠️ DevOps",
    "python": "🐍 Python",
    "后端工程": "🏗️ 后端工程",
    "向量数据库实战": "🧮 向量数据库",
    "安全与权限": "🔐 安全与权限",
    "工具与平台": "🔧 工具与平台",
    "数据库": "🗄️ 数据库",
    "环境搭建": "🖥️ 环境搭建",
    "算法入门教程": "🧠 算法入门",
}


def clean_docs_dir():
    if not MKDOCS_DOCS.exists():
        MKDOCS_DOCS.mkdir(parents=True)
        return
    for item in MKDOCS_DOCS.iterdir():
        if item.name in PRESERVE_IN_DOCS:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def should_skip(path: Path) -> bool:
    parts = path.relative_to(OBSIDIAN_VAULT).parts
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    if path.name in EXCLUDE_FILES:
        return True
    return False


def build_file_index() -> dict[str, str]:
    index = {}
    for p in OBSIDIAN_VAULT.rglob("*.md"):
        if should_skip(p):
            continue
        rel = str(p.relative_to(OBSIDIAN_VAULT))
        rel_no_ext = rel[:-3]
        index[rel_no_ext] = rel
        stem = p.stem
        if stem not in index:
            index[stem] = rel
    return index


def compute_relative_path(from_file: str, to_file: str) -> str:
    from_dir = PurePosixPath(from_file).parent
    to_path = PurePosixPath(to_file)
    try:
        rel = os.path.relpath(str(to_path), str(from_dir))
    except ValueError:
        rel = str(to_path)
    # 去掉 .md 后缀（VitePress 的 cleanUrls 模式）
    if rel.endswith(".md"):
        rel = rel[:-3]
    return rel.replace("\\", "/")


def convert_wikilinks(content: str, file_rel_path: str, file_index: dict) -> str:
    current_dir = str(PurePosixPath(file_rel_path).parent)

    def replace_wikilink(match):
        inner = match.group(1)
        if "|" in inner:
            target, alias = inner.split("|", 1)
        else:
            target = inner
            alias = None

        heading = ""
        if "#" in target:
            target, heading = target.split("#", 1)
            heading = "#" + heading.lower().replace(" ", "-")

        target = target.strip()
        display = alias if alias else (target.split("/")[-1] if target else heading.lstrip("#"))

        if not target:
            return f"[{display}]({heading})"

        resolved = None
        if target in file_index:
            resolved = file_index[target]
        elif current_dir != "." and f"{current_dir}/{target}" in file_index:
            resolved = file_index[f"{current_dir}/{target}"]
        else:
            target_stem = target.split("/")[-1]
            if target_stem in file_index:
                resolved = file_index[target_stem]

        if resolved:
            rel_link = compute_relative_path(file_rel_path, resolved)
            link = f"{rel_link}{heading}"
        else:
            link = f"{target}{heading}"

        return f"[{display}]({link})"

    content = re.sub(r'(?<!!)\[\[([^\]]+)\]\]', replace_wikilink, content)
    return content


def convert_obsidian_callouts(content: str) -> str:
    """转换 Obsidian callout 为 VitePress 自定义容器"""
    lines = content.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        callout_match = re.match(r'^>\s*\[!(\w+)\]\s*(.*)?$', line)
        if callout_match:
            callout_type = callout_match.group(1).lower()
            title = callout_match.group(2) or ""
            # VitePress 自定义容器类型
            type_map = {
                "note": "info", "tip": "tip", "important": "important",
                "warning": "warning", "caution": "danger", "danger": "danger",
                "info": "info", "success": "tip", "question": "warning",
                "example": "details", "quote": "info", "abstract": "info", "bug": "danger",
            }
            vp_type = type_map.get(callout_type, "info")
            if title:
                result.append(f"::: {vp_type} {title}")
            else:
                result.append(f"::: {vp_type}")
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                content_line = re.sub(r'^>\s?', '', lines[i])
                result.append(content_line)
                i += 1
            result.append(":::")
            result.append("")
            continue
        result.append(line)
        i += 1

    return "\n".join(result)


def process_file(src: Path, dst: Path, file_rel_path: str, file_index: dict):
    content = src.read_text(encoding="utf-8")
    content = convert_wikilinks(content, file_rel_path, file_index)
    content = convert_obsidian_callouts(content)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")


def generate_sidebar() -> dict:
    """自动生成 VitePress sidebar 配置"""
    sidebar = {}
    docs_path = MKDOCS_DOCS

    for dir_path in sorted(docs_path.iterdir()):
        if not dir_path.is_dir():
            continue
        dir_name = dir_path.name
        if dir_name in PRESERVE_IN_DOCS or dir_name.startswith("."):
            continue

        items = []
        # 查找大纲/索引文件
        for md_file in sorted(dir_path.rglob("*.md")):
            rel = md_file.relative_to(docs_path)
            name = md_file.stem
            link = f"/{str(rel).replace(os.sep, '/')[:-3]}"
            items.append({"text": name, "link": link})

        if items:
            label = DIR_LABELS.get(dir_name, dir_name)
            sidebar[f"/{dir_name}/"] = [
                {
                    "text": label,
                    "collapsed": True,
                    "items": items
                }
            ]

    return sidebar


def sync():
    print(f"📂 Obsidian 仓库: {OBSIDIAN_VAULT}")
    print(f"📁 VitePress 目标: {MKDOCS_DOCS}")
    print(f"🚫 排除目录:      {', '.join(sorted(EXCLUDE_DIRS))}")
    print()

    print("🔍 构建文件索引...")
    file_index = build_file_index()
    print(f"   索引条目: {len(file_index)}")

    clean_docs_dir()

    file_count = 0
    dir_count = set()

    for src_path in OBSIDIAN_VAULT.rglob("*.md"):
        if should_skip(src_path):
            continue
        rel_path = src_path.relative_to(OBSIDIAN_VAULT)
        dst_path = MKDOCS_DOCS / rel_path
        if src_path.stat().st_size < 10:
            continue
        file_rel_str = str(rel_path).replace("\\", "/")
        process_file(src_path, dst_path, file_rel_str, file_index)
        file_count += 1
        dir_count.add(rel_path.parent)

    # 生成 guide.md（知识库总览）— 从 HOME.md 转换
    home_src = OBSIDIAN_VAULT / "HOME.md"
    if home_src.exists():
        process_file(home_src, MKDOCS_DOCS / "guide.md", "guide.md", file_index)
        print("🏠 HOME.md → guide.md（知识库总览）")

    # 生成 sidebar
    print("📋 生成 sidebar 配置...")
    sidebar = generate_sidebar()
    sidebar_path = MKDOCS_DOCS / ".vitepress" / "sidebar.json"
    sidebar_path.write_text(json.dumps(sidebar, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   侧边栏分组: {len(sidebar)} 个")

    print(f"\n✅ 同步完成！")
    print(f"   📄 文件: {file_count} 篇")
    print(f"   📂 目录: {len(dir_count)} 个")
    print(f"\n💡 运行 `npx vitepress dev docs` 预览效果")


if __name__ == "__main__":
    sync()
