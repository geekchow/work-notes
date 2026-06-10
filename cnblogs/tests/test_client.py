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
