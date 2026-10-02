# 中英双语阅读站

本站使用 VitePress，默认中文，可从右上角语言菜单切换至同一章节的英文版本。

阅读地址：<https://a-persimmons.github.io/build-your-own-harness/>

## 首次部署

1. 打开仓库 Settings → Pages，将 Source 设置为 **GitHub Actions**。
2. 如果 fork 的 Actions 尚未启用，先在 Actions 页面启用。
3. 选择 **Publish bilingual VitePress site → Run workflow**，或重新运行失败的部署任务。

后续向 `main` 提交修改会自动验证并部署；拉取请求只构建，不发布。

## 本地预览

需要 Node.js 22 或更新的受支持版本。网站只展示教程，Python Agent 仍需在本地运行。

```bash
npm ci
npm run docs:dev
```

构建和预览生产版本：

```bash
npm run docs:build
npm run docs:preview
```

## 翻译维护

- 英文原文保留在根目录及各层目录中。
- 中文译文按原路径放在 `i18n/zh/` 中。
- `scripts/prepare-docs.mjs` 生成临时的 `.book-docs/`，包括两种语言的网页、导航及链接适配。
- `i18n/manifest.json` 记录译文对应英文原文的 SHA-256。英文变更后，构建会提示先校对对应译文；完成校对后再更新该记录，避免两种语言悄悄不同步。
- 代码块与英文原文逐字比较，命令和代码不翻译。代码中的英文注释也按原样保留。
- 目前第 1–4 层有可运行实现，第 5–17 层是路线规划。第 4 层的“下一步”链接指向路线图第 5 层，避免访问不存在的教程目录。
- 原文的 Obsidian 双链指向未包含在仓库中的笔记，阅读站以等宽文字保留名称。
- 原文时效性信息和观点保留原意，译文不作实时事实核验承诺。
