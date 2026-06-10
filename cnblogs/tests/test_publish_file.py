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


def test_select_markdown_paths_keeps_valid_and_warns_on_ignored(tmp_path, capsys):
    real = tmp_path / "ok.md"
    real.write_text("x\n", encoding="utf-8")
    missing = str(tmp_path / "typo.md")
    not_md = str(tmp_path / "notes.txt")

    paths = publish.select_markdown_paths([str(real), missing, not_md])

    assert paths == [str(real)]
    err = capsys.readouterr().err
    assert missing in err          # 拼错/不存在的路径被警告而非静默丢弃
    assert not_md in err           # 非 .md 参数被警告
