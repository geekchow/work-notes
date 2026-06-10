# cnblogs Local Publisher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `cnblogs/publish.py` into a cnblogs-only, locally-run publisher that takes explicit markdown file paths, pre-renders mermaid blocks to uploaded PNGs, and publishes/updates posts via MetaWeblog.

**Architecture:** A single Python module (`cnblogs/publish.py`) decomposed into small, individually-testable functions: markdown→HTML conversion, mermaid detection + render + embed, repo-relative state tracking, credential loading from `.env`, a thin `CnblogsClient` XML-RPC wrapper, and a `publish_file` orchestrator. Network calls and the `mmdc` subprocess are isolated behind injectable boundaries so the pure logic is unit-tested without hitting cnblogs or Node.

**Tech Stack:** Python 3.12+, `python-frontmatter`, `markdown`, `python-dotenv`, `xmlrpc.client` (stdlib), pytest for tests, and `@mermaid-js/mermaid-cli` (`mmdc`) as an external runtime prerequisite for mermaid rendering.

**Spec:** `docs/superpowers/specs/2026-06-10-cnblogs-local-publisher-design.md`

---

### Task 1: Scaffolding — deps, config files, remove the workflow

**Files:**
- Delete: `cnblogs/publish.yml`
- Create: `cnblogs/requirements.txt`
- Create: `cnblogs/.env.example`
- Create: `cnblogs/tests/conftest.py`
- Modify: `.gitignore`

- [ ] **Step 1: Delete the obsolete GitHub Actions workflow**

```bash
git rm cnblogs/publish.yml
```

- [ ] **Step 2: Create `cnblogs/requirements.txt`**

```
python-frontmatter
markdown
python-dotenv
pytest
```

- [ ] **Step 3: Create `cnblogs/.env.example`**

```
# 复制为 cnblogs/.env 并填入真实值（cnblogs/.env 已被 gitignore）
# 博客名：博客园 URL 里那段，例如 https://www.cnblogs.com/geekchow -> geekchow
CNBLOGS_BLOGNAME=
# 登录用户名
CNBLOGS_USERNAME=
# MetaWeblog 访问令牌：后台 -> 设置 -> 其他设置 -> 生成令牌
CNBLOGS_TOKEN=
```

- [ ] **Step 4: Append to `.gitignore`**

Add these lines to the end of `.gitignore`:

```
cnblogs/.env
__pycache__/
.pytest_cache/
```

- [ ] **Step 5: Create `cnblogs/tests/conftest.py`** (lets tests `import publish`)

```python
import os
import sys

# 把 cnblogs/ 目录加入 import 路径，使测试可以 `import publish`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

- [ ] **Step 6: Install dependencies**

Run: `pip install -r cnblogs/requirements.txt`
Expected: installs `python-frontmatter`, `markdown`, `python-dotenv`, `pytest` without error.

- [ ] **Step 7: Commit**

```bash
git add cnblogs/requirements.txt cnblogs/.env.example cnblogs/tests/conftest.py .gitignore
git commit -m "chore: scaffold cnblogs local publisher, drop workflow"
```

---

### Task 2: Markdown → HTML conversion

**Files:**
- Create: `cnblogs/publish.py`
- Test: `cnblogs/tests/test_md_to_html.py`

- [ ] **Step 1: Write the failing test**

Create `cnblogs/tests/test_md_to_html.py`:

```python
from publish import md_to_html


def test_md_to_html_renders_heading_code_and_table():
    md = (
        "# 标题\n\n"
        "```python\nprint(1)\n```\n\n"
        "| a | b |\n|---|---|\n| 1 | 2 |\n"
    )
    html = md_to_html(md)
    assert "<h1" in html
    assert "<table>" in html
    assert "print" in html


def test_md_to_html_passes_through_raw_html():
    html = md_to_html('text\n\n<img src="https://x/y.png" alt="d">\n')
    assert '<img src="https://x/y.png"' in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd cnblogs && python -m pytest tests/test_md_to_html.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publish'` (file not created yet).

- [ ] **Step 3: Create `cnblogs/publish.py` with the module header and `md_to_html`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd cnblogs && python -m pytest tests/test_md_to_html.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add cnblogs/publish.py cnblogs/tests/test_md_to_html.py
git commit -m "feat: markdown to html conversion for cnblogs publisher"
```

---

### Task 3: Mermaid detection, render, and embed

**Files:**
- Modify: `cnblogs/publish.py`
- Test: `cnblogs/tests/test_mermaid.py`

- [ ] **Step 1: Write the failing test**

Create `cnblogs/tests/test_mermaid.py`:

```python
import pytest
import publish


def test_mermaid_block_replaced_with_uploaded_img():
    md = "前文\n\n```mermaid\ngraph TD\nA-->B\n```\n\n后文\n"
    seen = {}

    def fake_render(code):
        seen["code"] = code
        return "/tmp/diagram.png"

    def fake_upload(path):
        seen["path"] = path
        return "https://img.cnblogs.com/x.png"

    out = publish.render_and_embed_mermaid(md, fake_render, fake_upload)

    assert "```mermaid" not in out
    assert '<img src="https://img.cnblogs.com/x.png" alt="mermaid diagram">' in out
    assert seen["code"].strip() == "graph TD\nA-->B"
    assert seen["path"] == "/tmp/diagram.png"
    assert "前文" in out and "后文" in out


def test_no_mermaid_leaves_text_unchanged_and_calls_nothing():
    md = "没有图表\n\n```python\nprint(1)\n```\n"

    def boom(_):
        raise AssertionError("should not be called")

    out = publish.render_and_embed_mermaid(md, boom, boom)
    assert out == md


def test_render_mermaid_png_errors_when_mmdc_missing(monkeypatch):
    monkeypatch.setattr(publish.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError) as exc:
        publish.render_mermaid_png("graph TD\nA-->B")
    assert "mmdc" in str(exc.value)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd cnblogs && python -m pytest tests/test_mermaid.py -v`
Expected: FAIL — `AttributeError: module 'publish' has no attribute 'render_and_embed_mermaid'`.

- [ ] **Step 3: Add mermaid functions to `cnblogs/publish.py`**

Add after `md_to_html`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd cnblogs && python -m pytest tests/test_mermaid.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add cnblogs/publish.py cnblogs/tests/test_mermaid.py
git commit -m "feat: render mermaid blocks to png and embed as img"
```

---

### Task 4: State persistence and repo-relative keys

**Files:**
- Modify: `cnblogs/publish.py`
- Test: `cnblogs/tests/test_state.py`

- [ ] **Step 1: Write the failing test**

Create `cnblogs/tests/test_state.py`:

```python
import os
import publish


def test_repo_relative_key_is_relative_to_repo_root():
    abs_path = os.path.join(publish.REPO_ROOT, "cnblogs", "foo.md")
    assert publish.repo_relative_key(abs_path) == os.path.join("cnblogs", "foo.md")


def test_state_save_then_load_roundtrip(tmp_path):
    path = str(tmp_path / "state.json")
    publish.save_state({"cnblogs/a.md": {"cnblogs_id": "7"}}, path)
    assert publish.load_state(path) == {"cnblogs/a.md": {"cnblogs_id": "7"}}


def test_load_state_missing_file_returns_empty(tmp_path):
    assert publish.load_state(str(tmp_path / "nope.json")) == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd cnblogs && python -m pytest tests/test_state.py -v`
Expected: FAIL — `AttributeError: module 'publish' has no attribute 'repo_relative_key'`.

- [ ] **Step 3: Add state functions to `cnblogs/publish.py`**

Add after the mermaid functions:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd cnblogs && python -m pytest tests/test_state.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add cnblogs/publish.py cnblogs/tests/test_state.py
git commit -m "feat: repo-relative state tracking for idempotent publishing"
```

---

### Task 5: Credential loading from .env

**Files:**
- Modify: `cnblogs/publish.py`
- Test: `cnblogs/tests/test_credentials.py`

- [ ] **Step 1: Write the failing test**

Create `cnblogs/tests/test_credentials.py`:

```python
import pytest
import publish


def test_load_credentials_reads_env_vars(monkeypatch, tmp_path):
    monkeypatch.setenv("CNBLOGS_TOKEN", "tok")
    monkeypatch.setenv("CNBLOGS_BLOGNAME", "blog")
    monkeypatch.setenv("CNBLOGS_USERNAME", "user")
    creds = publish.load_credentials(str(tmp_path / "absent.env"))
    assert creds == {"blogname": "blog", "username": "user", "token": "tok"}


def test_load_credentials_missing_token_exits(monkeypatch, tmp_path):
    monkeypatch.delenv("CNBLOGS_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        publish.load_credentials(str(tmp_path / "absent.env"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd cnblogs && python -m pytest tests/test_credentials.py -v`
Expected: FAIL — `AttributeError: module 'publish' has no attribute 'load_credentials'`.

- [ ] **Step 3: Add `load_credentials` to `cnblogs/publish.py`**

Add after the state functions:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd cnblogs && python -m pytest tests/test_credentials.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add cnblogs/publish.py cnblogs/tests/test_credentials.py
git commit -m "feat: load cnblogs credentials from .env with fallback"
```

---

### Task 6: CnblogsClient (MetaWeblog wrapper)

**Files:**
- Modify: `cnblogs/publish.py`
- Test: `cnblogs/tests/test_client.py`

- [ ] **Step 1: Write the failing test**

Create `cnblogs/tests/test_client.py`:

```python
import publish


class FakeMetaWeblog:
    def __init__(self):
        self.calls = []

    def newPost(self, blogid, user, token, post, publish_flag):
        self.calls.append(("newPost", post))
        return "123"

    def editPost(self, postid, user, token, post, publish_flag):
        self.calls.append(("editPost", postid))
        return True

    def newMediaObject(self, blogid, user, token, data):
        self.calls.append(("newMediaObject", data["name"]))
        return {"url": "https://img.cnblogs.com/x.png"}


class FakeServer:
    def __init__(self):
        self.metaWeblog = FakeMetaWeblog()


def test_new_post_sends_title_tags_categories():
    srv = FakeServer()
    c = publish.CnblogsClient("blog", "user", "tok", server=srv)
    pid = c.new_post("标题", "<p>x</p>", ["a", "b"], ["[随笔分类]AI"])
    assert pid == "123"
    name, post = srv.metaWeblog.calls[0]
    assert name == "newPost"
    assert post["title"] == "标题"
    assert post["description"] == "<p>x</p>"
    assert post["mt_keywords"] == "a,b"
    assert post["categories"] == ["[随笔分类]AI"]


def test_edit_post_targets_existing_id():
    srv = FakeServer()
    c = publish.CnblogsClient("blog", "user", "tok", server=srv)
    assert c.edit_post("555", "标题", "<p>x</p>", [], []) is True
    assert srv.metaWeblog.calls[0] == ("editPost", "555")


def test_upload_media_returns_url(tmp_path):
    png = tmp_path / "d.png"
    png.write_bytes(b"\x89PNG\r\n")
    srv = FakeServer()
    c = publish.CnblogsClient("blog", "user", "tok", server=srv)
    url = c.upload_media(str(png))
    assert url == "https://img.cnblogs.com/x.png"
    assert srv.metaWeblog.calls[0] == ("newMediaObject", "d.png")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd cnblogs && python -m pytest tests/test_client.py -v`
Expected: FAIL — `AttributeError: module 'publish' has no attribute 'CnblogsClient'`.

- [ ] **Step 3: Add `CnblogsClient` to `cnblogs/publish.py`**

Add after `load_credentials`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd cnblogs && python -m pytest tests/test_client.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add cnblogs/publish.py cnblogs/tests/test_client.py
git commit -m "feat: CnblogsClient with newPost/editPost/newMediaObject"
```

---

### Task 7: publish_file orchestration and main entry point

**Files:**
- Modify: `cnblogs/publish.py`
- Test: `cnblogs/tests/test_publish_file.py`

- [ ] **Step 1: Write the failing test**

Create `cnblogs/tests/test_publish_file.py`:

```python
import publish


class FakeClient:
    def __init__(self):
        self.new = []
        self.edit = []

    def new_post(self, title, html, tags, categories):
        self.new.append((title, html, tags, categories))
        return "999"

    def edit_post(self, postid, title, html, tags, categories):
        self.edit.append((postid, title))
        return True

    def upload_media(self, path):
        return "https://img.cnblogs.com/x.png"


def test_publish_file_creates_then_updates(tmp_path):
    f = tmp_path / "a.md"
    f.write_text(
        "---\ntitle: 你好\ntags: [x]\ncnblogs_categories: [\"[随笔分类]AI\"]\n---\n\n正文\n",
        encoding="utf-8",
    )
    client = FakeClient()
    state = {}

    publish.publish_file(str(f), client, state)
    key = publish.repo_relative_key(str(f))
    assert state[key]["cnblogs_id"] == "999"
    assert len(client.new) == 1
    assert client.new[0][0] == "你好"

    # 再次发布同一文件 -> 走更新
    publish.publish_file(str(f), client, state)
    assert len(client.edit) == 1
    assert client.edit[0][0] == "999"


def test_publish_file_skips_when_no_title(tmp_path):
    f = tmp_path / "b.md"
    f.write_text("没有 front matter 的正文\n", encoding="utf-8")
    client = FakeClient()
    state = {}
    publish.publish_file(str(f), client, state)
    assert state == {}
    assert client.new == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd cnblogs && python -m pytest tests/test_publish_file.py -v`
Expected: FAIL — `AttributeError: module 'publish' has no attribute 'publish_file'`.

- [ ] **Step 3: Add `publish_file` and `main` to `cnblogs/publish.py`**

Add after `CnblogsClient`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd cnblogs && python -m pytest tests/test_publish_file.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Run the full test suite**

Run: `cd cnblogs && python -m pytest -v`
Expected: PASS (all tests across all files green).

- [ ] **Step 6: Commit**

```bash
git add cnblogs/publish.py cnblogs/tests/test_publish_file.py
git commit -m "feat: publish_file orchestration and CLI entry point"
```

---

### Task 8: Rewrite README for local-only cnblogs workflow

**Files:**
- Modify: `cnblogs/README.md`

- [ ] **Step 1: Replace `cnblogs/README.md` contents**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add cnblogs/README.md
git commit -m "docs: rewrite cnblogs README for local-only workflow"
```

---

### Task 9: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run the complete test suite**

Run: `cd cnblogs && python -m pytest -v`
Expected: all tests pass.

- [ ] **Step 2: Verify the CLI usage guard works**

Run: `python cnblogs/publish.py`
Expected: exits with the usage message `用法：python cnblogs/publish.py 文章1.md [...]` (no network call, since no files were given).

- [ ] **Step 3: Verify the missing-credential guard works**

Run (temporarily ensuring no `cnblogs/.env` and no `CNBLOGS_TOKEN` env var):
`python cnblogs/publish.py cnblogs/README.md`
Expected: exits with the `缺少 CNBLOGS_TOKEN` message. (README has no `title`, but the credential check runs first.)

- [ ] **Step 4: (Manual, requires real credentials) End-to-end smoke test**

With `cnblogs/.env` filled in, create a throwaway `cnblogs/_smoke.md` with a `title`, a code block, and one ` ```mermaid ` block. Run `python cnblogs/publish.py cnblogs/_smoke.md`.
Expected: a post appears on cnblogs with the mermaid block shown as an image; `.publish_state.json` gains an entry. Re-running updates the same post (no duplicate). Delete `cnblogs/_smoke.md` and the test post afterward.

This step is optional and depends on having valid cnblogs credentials; skip if not available.
