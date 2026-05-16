import { defineConfig } from 'vitepress'
import sidebarData from './sidebar.json'

export default defineConfig({
  title: "Jersey's Blog",
  description: "坚持是一种品格 — AI 工程化 & Python 技术知识库",
  lang: 'zh-CN',
  cleanUrls: true,
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
    ['link', { href: 'https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap', rel: 'stylesheet' }],
  ],

  themeConfig: {
    logo: '/logo.svg',
    siteTitle: "Jersey's Blog",

    nav: [
      { text: '首页', link: '/' },
      { text: '知识库', link: '/guide' },
      {
        text: 'Python',
        items: [
          { text: 'Python 学习路径', link: '/python/Python 实战型学习大纲' },
          { text: '异步编程指南', link: '/python/Python 异步编程完全指南' },
          { text: '装饰器与元编程', link: '/python/Python 装饰器与元编程' },
          { text: 'Pydantic V2 指南', link: '/python/Pydantic V2 完全指南' },
          { text: '类型系统实战', link: '/python/Python 类型系统实战' },
        ]
      },
      {
        text: 'AI 工程化',
        items: [
          { text: 'LangChain 实战', link: '/AI工程化/LangChain 实战教程' },
          { text: 'RAG 系统', link: '/AI工程化/构建企业级 RAG 系统' },
          { text: 'Agent 记忆系统', link: '/AI工程化/AI Agent 记忆系统设计' },
          { text: '语音应用开发', link: '/AI工程化/AI 语音应用开发' },
          { text: '构建 AI 助理', link: '/AI工程化/构建个人 AI 助理' },
        ]
      },
      {
        text: '教程系列',
        items: [
          { text: 'FastAPI 入门', link: '/FastAPI入门教程/FastAPI入门教程大纲' },
          { text: 'LangGraph 实战', link: '/LangGraph实战教程/LangGraph实战教程大纲' },
          { text: 'MCP 协议开发', link: '/MCP协议开发实战/MCP协议开发实战大纲' },
          { text: 'Docker 入门', link: '/Docker入门教程/Docker入门教程大纲' },
          { text: 'Redis 入门', link: '/Redis入门教程/Redis入门教程大纲' },
          { text: '算法入门', link: '/算法入门教程/算法入门教程大纲' },
        ]
      },
      {
        text: '后端工程',
        items: [
          { text: 'FastAPI 生产级实战', link: '/后端工程/FastAPI 生产级实战' },
          { text: 'API 设计最佳实践', link: '/后端工程/API 设计最佳实践' },
          { text: '高并发系统设计', link: '/后端工程/高并发系统设计' },
          { text: '分布式系统入门', link: '/后端工程/分布式系统设计入门' },
          { text: 'K8s 入门实战', link: '/后端工程/Kubernetes 入门实战' },
        ]
      },
    ],

    sidebar: sidebarData,

    socialLinks: [
      { icon: 'github', link: 'https://github.com/leejersey' },
    ],

    footer: {
      message: '坚持是一种品格',
      copyright: 'Copyright © 2024-2026 Jersey'
    },

    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索文档', buttonAriaLabel: '搜索' },
          modal: {
            noResultsText: '没有找到结果',
            resetButtonTitle: '清除查询',
            footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' }
          }
        }
      }
    },

    outline: {
      level: [2, 3],
      label: '目录'
    },

    docFooter: {
      prev: '上一篇',
      next: '下一篇'
    },

    lastUpdated: {
      text: '最后更新',
    },

    returnToTopLabel: '返回顶部',
    sidebarMenuLabel: '菜单',
    darkModeSwitchLabel: '外观',
  },

  markdown: {
    lineNumbers: true,
    theme: {
      light: 'github-light',
      dark: 'one-dark-pro'
    }
  },
})
