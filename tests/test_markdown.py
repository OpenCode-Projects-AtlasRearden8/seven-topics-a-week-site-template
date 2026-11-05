"""Unit tests for the tiny Markdown converter in build.py."""
import build


def test_headings():
    html_text = build.md_to_html("## Two\n### Three")
    assert "<h2>Two</h2>" in html_text
    assert "<h3>Three</h3>" in html_text


def test_paragraphs_join_soft_wraps():
    html_text = build.md_to_html("First line\nsecond line.\n\nNew paragraph.")
    assert "<p>First line<br>\nsecond line.</p>" in html_text
    assert "<p>New paragraph.</p>" in html_text


def test_bold_italic_and_code():
    html_text = build.md_to_html("a **bold** and *soft* and `x=1`")
    assert "<strong>bold</strong>" in html_text
    assert "<em>soft</em>" in html_text
    assert "<code>x=1</code>" in html_text


def test_links():
    html_text = build.md_to_html("see [the guide](https://example.com/guide)")
    assert '<a href="https://example.com/guide">the guide</a>' in html_text


def test_unordered_list():
    html_text = build.md_to_html("- one\n- two")
    assert "<ul><li>one</li><li>two</li></ul>" in html_text


def test_ordered_list():
    html_text = build.md_to_html("1. one\n2. two")
    assert "<ol><li>one</li><li>two</li></ol>" in html_text


def test_blockquote():
    html_text = build.md_to_html("> Start small on purpose.")
    assert "<blockquote>" in html_text and "Start small on purpose." in html_text


def test_code_fence_escapes_html():
    html_text = build.md_to_html("```bash\nollama pull llama3.2:3b\n```")
    assert "<pre><code>ollama pull llama3.2:3b</code></pre>" in html_text


def test_inline_html_is_escaped():
    html_text = build.md_to_html('say "<script>alert(1)</script>"')
    assert "<script>" not in html_text
    assert "&lt;script&gt;" in html_text


def test_link_href_quote_is_neutralized():
    html_text = build.md_to_html('[x](https://ex.com/?a=")')
    assert 'href="https://ex.com/?a=%22"' in html_text


def test_horizontal_rule():
    html_text = build.md_to_html("before\n\n---\n\nafter")
    assert "<hr>" in html_text


def test_inline_works_inside_lists():
    html_text = build.md_to_html("- **bold item** with [a link](https://ex.com)")
    assert "<li><strong>bold item</strong> with <a href=" in html_text
