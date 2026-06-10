#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本地 Markdown 文章发布到博客园（cnblogs）。

用法：
    python cnblogs/publish.py 文章1.md [文章2.md ...]

只发布显式传入的文件。mermaid 代码块会被预渲染成 PNG 并上传后以 <img> 嵌入。
幂等：cnblogs/.publish_state.json 记录 "仓库相对路径 -> cnblogs postid"，
再次发布同一文件会更新而非新建。
"""

import os
import re
import sys
import json
import base64
import shutil
import tempfile
import subprocess
import xmlrpc.client
from datetime import datetime, timezone

import frontmatter            # pip install python-frontmatter
import markdown               # pip install markdown
from dotenv import load_dotenv  # pip install python-dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_FILE = os.path.join(SCRIPT_DIR, ".publish_state.json")
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")


def md_to_html(md_text: str) -> str:
    """Markdown -> HTML5。代码块、表格、目录可正常渲染；原始 HTML（如 <img>）原样透传。"""
    return markdown.markdown(
        md_text,
        extensions=["fenced_code", "tables", "toc", "codehilite", "attr_list"],
        output_format="html5",
    )


MERMAID_RE = re.compile(r"```mermaid[ \t]*\r?\n(.*?)\r?\n```", re.DOTALL)


def render_mermaid_png(code: str, scale: int = 2) -> str:
    """用 mermaid-cli 把一段 mermaid 源码渲染成 PNG，返回 PNG 路径。
    未安装 mmdc 时直接报错，避免发布出缺图的文章。"""
    if shutil.which("mmdc") is None:
        raise RuntimeError(
            "未找到 mmdc：请先安装 mermaid-cli： npm i -g @mermaid-js/mermaid-cli"
        )
    tmpdir = tempfile.mkdtemp(prefix="mermaid_")
    mmd_path = os.path.join(tmpdir, "diagram.mmd")
    png_path = os.path.join(tmpdir, "diagram.png")
    with open(mmd_path, "w", encoding="utf-8") as f:
        f.write(code)
    subprocess.run(
        ["mmdc", "-i", mmd_path, "-o", png_path, "-b", "white", "-s", str(scale)],
        check=True,
    )
    return png_path


def render_and_embed_mermaid(md_text, render_png, upload_png) -> str:
    """把 md_text 中每个 ```mermaid 代码块渲染成 PNG、上传，并替换成 <img>。
    render_png(code)->png_path 与 upload_png(png_path)->url 注入，便于测试。"""

    def repl(match):
        code = match.group(1)
        png_path = render_png(code)
        url = upload_png(png_path)
        return f'<img src="{url}" alt="mermaid diagram">'

    return MERMAID_RE.sub(repl, md_text)


def repo_relative_key(path: str) -> str:
    """把任意路径规范化为相对仓库根目录的路径，作为状态文件的稳定键。"""
    return os.path.relpath(os.path.abspath(path), REPO_ROOT)


def load_state(path: str = STATE_FILE) -> dict:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state: dict, path: str = STATE_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def load_credentials(env_path: str = ENV_FILE) -> dict:
    """从 cnblogs/.env 读取凭据（若文件不存在则仅用已有环境变量）。缺 token 直接报错。"""
    load_dotenv(env_path)  # 文件不存在时是 no-op
    token = os.getenv("CNBLOGS_TOKEN")
    if not token:
        raise SystemExit(
            "缺少 CNBLOGS_TOKEN：请复制 cnblogs/.env.example 为 cnblogs/.env 并填写，"
            "或在环境变量中设置。"
        )
    return {
        "blogname": os.environ.get("CNBLOGS_BLOGNAME", ""),
        "username": os.environ.get("CNBLOGS_USERNAME", ""),
        "token": token,
    }


class CnblogsClient:
    """博客园 MetaWeblog (XML-RPC) 客户端。server 可注入，便于测试。"""

    def __init__(self, blogname: str, username: str, token: str, server=None):
        self.url = f"https://rpc.cnblogs.com/metaweblog/{blogname}"
        self.username = username
        self.token = token            # token 当作密码使用
        self.blogid = blogname        # blogid 任意，用博客名即可
        self.server = server or xmlrpc.client.ServerProxy(self.url, encoding="UTF-8")

    def new_post(self, title, html, tags, categories=None, publish=True) -> str:
        post = {
            "title": title,
            "description": html,
            "categories": categories or [],
            "mt_keywords": ",".join(tags or []),
            "dateCreated": xmlrpc.client.DateTime(datetime.now(timezone.utc)),
        }
        return self.server.metaWeblog.newPost(
            self.blogid, self.username, self.token, post, publish
        )

    def edit_post(self, postid, title, html, tags, categories=None, publish=True) -> bool:
        post = {
            "title": title,
            "description": html,
            "categories": categories or [],
            "mt_keywords": ",".join(tags or []),
        }
        return self.server.metaWeblog.editPost(
            postid, self.username, self.token, post, publish
        )

    def upload_media(self, png_path: str) -> str:
        """上传 PNG，返回博客园托管的图片 URL。"""
        with open(png_path, "rb") as f:
            bits = f.read()
        data = {
            "name": os.path.basename(png_path),
            "type": "image/png",
            "bits": xmlrpc.client.Binary(bits),
        }
        result = self.server.metaWeblog.newMediaObject(
            self.blogid, self.username, self.token, data
        )
        return result["url"]


def publish_file(path: str, client: "CnblogsClient", state: dict) -> None:
    """发布或更新单篇文章。无 title 的文件跳过。"""
    post = frontmatter.load(path)
    title = post.get("title")
    if not title:
        print(f"[skip] 无 title: {path}")
        return

    tags = post.get("tags", []) or []
    categories = post.get("cnblogs_categories", []) or []

    md = render_and_embed_mermaid(post.content, render_mermaid_png, client.upload_media)
    html = md_to_html(md)

    key = repo_relative_key(path)
    rec = state.setdefault(key, {})
    if rec.get("cnblogs_id"):
        client.edit_post(rec["cnblogs_id"], title, html, tags, categories)
        print(f"[cnblogs] 已更新: {path}")
    else:
        pid = client.new_post(title, html, tags, categories)
        rec["cnblogs_id"] = str(pid)
        print(f"[cnblogs] 已创建: {path} -> {pid}")


def main(argv) -> None:
    paths = [a for a in argv if a.endswith(".md") and os.path.exists(a)]
    if not paths:
        raise SystemExit("用法：python cnblogs/publish.py 文章1.md [文章2.md ...]")

    creds = load_credentials()
    client = CnblogsClient(creds["blogname"], creds["username"], creds["token"])
    state = load_state()

    for path in paths:
        try:
            publish_file(path, client, state)
        except Exception as e:
            print(f"[cnblogs] 失败 {path}: {e}", file=sys.stderr)

    save_state(state)


if __name__ == "__main__":
    main(sys.argv[1:])
