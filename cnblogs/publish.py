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
