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
