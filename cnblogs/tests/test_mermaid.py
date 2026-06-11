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


def test_four_backtick_fence_is_not_treated_as_mermaid():
    # ````mermaid 是文档里转义展示 mermaid 块的写法，不应被当作真实图表
    md = "````mermaid\ngraph TD\nA-->B\n````\n"

    def boom(_):
        raise AssertionError("should not be called")

    out = publish.render_and_embed_mermaid(md, boom, boom)
    assert out == md


def test_render_mermaid_png_errors_when_mmdc_missing(monkeypatch):
    monkeypatch.setattr(publish.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError) as exc:
        publish.render_mermaid_png("graph TD\nA-->B")
    assert "mmdc" in str(exc.value)
