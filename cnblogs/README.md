# 本地发布到博客园（cnblogs）

在本机手动把指定的 Markdown 文章发布到博客园。不走 GitHub Actions、不自动触发，
完全由你决定发哪几篇。

## 文件
- `publish.py` —— 解析文章、渲染 mermaid、转 HTML、调用博客园接口、维护幂等状态
- `.env.example` —— 凭据模板，复制为 `.env` 后填写（`.env` 已被 gitignore）
- `requirements.txt` —— Python 依赖
- `.publish_state.json` —— 自动生成，记录已发文章的远端 id（请勿手改）

## 一、安装

```bash
pip install -r cnblogs/requirements.txt
# 如果文章里有 mermaid 图，需要 mermaid-cli：
npm i -g @mermaid-js/mermaid-cli
```

## 二、配置凭据

1. 博客园后台 → 设置 → 其他设置 → 勾选「允许 MetaWeblog 博客客户端访问」。
2. 同一页生成 **MetaWeblog 访问令牌**（新版必须用令牌，用户名+密码已失效）。
3. 复制 `cnblogs/.env.example` 为 `cnblogs/.env`，填入：
   - `CNBLOGS_BLOGNAME` —— 博客名（URL 里那段，如 `geekchow`）
   - `CNBLOGS_USERNAME` —— 登录用户名
   - `CNBLOGS_TOKEN` —— 上面生成的令牌

## 三、文章 front matter 约定

```markdown
---
title: "生产环境 RAG 的检索质量评估"
date: 2026-06-10
tags: [RAG, LLM, 评估]
cnblogs_categories: ["[随笔分类]AI"]      # 可选，博客园分类
---

正文从这里开始……
```

只有 `title` 是必需的；没有 `title` 的文件会被跳过。

## 四、发布

```bash
python cnblogs/publish.py path/to/文章.md [更多.md ...]
```

- 只发布你显式传入的文件。
- 同一篇再次发布会**更新**原文，不会重复创建（依据 `.publish_state.json`）。
- 发布成功后可把更新后的 `.publish_state.json` 一并提交，方便换机器后仍能更新。

## mermaid 图

博客园默认不渲染 ```mermaid``` 代码块，本脚本会用 `mmdc` 把每个 mermaid 块预渲染成
PNG，上传到博客园后以 `<img>` 嵌入正文。需要本机安装 `@mermaid-js/mermaid-cli`。
（注意：每次重新发布会重新上传该文的 mermaid 图，会在博客园产生新的图片对象。）

## 注意事项

- **图片**：仓库里的相对路径图片在外站打不开。非 mermaid 图片请放图床或对象存储，正文用绝对 URL。
- **Jupyter Notebook**：本流程只处理 `.md`。`.ipynb` 先用 `jupyter nbconvert --to markdown` 转成 markdown 再发布。
- **合规**：发布前清理任何银行内部系统、供应商、数据相关内容，只保留通用模式与个人总结。
