"""End-to-end tests: Markdown fixtures -> generated site (pages, RSS, stub)."""
import datetime as dt
import re
import xml.etree.ElementTree as ET

import build
from conftest import read

SITE_URL = build.SITE_URL


def test_expected_files_written(site):
    written = site["result"]["written"]
    for name in ("index.html", "feed.xml", "next.html"):
        assert name in written
    assert "posts/2026-11-03-ask-ai-like-a-friend-would.html" in written
    assert "posts/2026-10-27-meet-your-first-local-ai.html" in written


def test_index_lists_newest_first(site):
    html_text = read(site["out_dir"], "index.html")
    newer = html_text.index("Ask AI like a friend would")
    older = html_text.index("Meet your first local AI")
    assert newer < older
    assert 'href="posts/2026-11-03-ask-ai-like-a-friend-would.html"' in html_text
    assert 'href="feed.xml"' in html_text


def test_index_groups_by_year(site):
    html_text = read(site["out_dir"], "index.html")
    assert '<h2 class="year">2026</h2>' in html_text


def test_draft_excluded_everywhere(site):
    draft_page = site["out_dir"] / "posts" / "2026-11-10-new-topic.html"
    assert not draft_page.exists()
    # RSS carries only published issues
    assert "(Make me a title)" not in read(site["out_dir"], "feed.xml")
    # the archive only mentions drafts in the "In the works" staging section
    index_text = read(site["out_dir"], "index.html")
    works = index_text.index("In the works")
    assert "(Make me a title)" not in index_text[:works]
    assert (
        site["result"]["published"]
        == [
            "2026-11-03-ask-ai-like-a-friend-would.md",
            "2026-10-27-meet-your-first-local-ai.md",
        ]
    )


def test_index_shows_draft_stage(site):
    html_text = read(site["out_dir"], "index.html")
    assert "In the works" in html_text
    assert "<time datetime=\"2026-11-10\">" in html_text


def test_post_page_markup(site):
    html_text = read(
        site["out_dir"], "posts/2026-10-27-meet-your-first-local-ai.html"
    )
    assert "<h1>Meet your first local AI</h1>" in html_text
    assert "<strong>the answers are generated on your machine" in html_text
    assert '<a href="https://ollama.com">the official guide</a>' in html_text
    assert "<pre><code>ollama pull llama3.2:3b" in html_text
    assert "<blockquote>" in html_text
    # relative depth: post pages live one level down
    assert 'href="../feed.xml"' in html_text
    assert 'href="../index.html"' in html_text


def test_rss_feed_is_valid_xml_with_items(site):
    xml_text = read(site["out_dir"], "feed.xml")
    root = ET.fromstring(xml_text)
    assert root.tag == "rss"
    items = root.findall("./channel/item")
    assert len(items) == 2
    first = items[0]
    assert first.findtext("title") == "Ask AI like a friend would"
    link = first.findtext("link")
    assert link.startswith(SITE_URL.rstrip("/"))
    assert link.endswith("/posts/2026-11-03-ask-ai-like-a-friend-would.html")
    pub_date = first.findtext("pubDate")
    assert re.match(r"^[A-Z][a-z]{2}, \d{2} [A-Z][a-z]{2} \d{4} \d{2}:00:00 [+-]\d{4}$", pub_date)


def test_rss_summary_matches_front_matter(site):
    xml_text = read(site["out_dir"], "feed.xml")
    assert "A gentle, five-minute tour" in xml_text


def test_next_week_stub_is_scheduled(site):
    html_text = read(site["out_dir"], "next.html")
    expected = dt.date(2026, 11, 3) + dt.timedelta(days=7)
    assert expected.strftime("%Y-%m-%d") in html_text
    assert "posts/2026-11-10-new-topic.md" in html_text  # scheduling guidance
    assert "draft: yes" in html_text  # documents the publish switch


def test_pages_have_inline_rss_and_inline_css(site):
    for name in ("index.html", "next.html"):
        html_text = read(site["out_dir"], name)
        assert 'type="application/rss+xml"' in html_text
        assert "<style>" in html_text
    post_html = read(
        site["out_dir"], "posts/2026-11-03-ask-ai-like-a-friend-would.html"
    )
    assert 'type="application/rss+xml"' in post_html


def test_footer_credits(site):
    html_text = read(site["out_dir"], "index.html")
    assert "Asdale Dynamics, LLC" in html_text
    assert "MIT License" in html_text


def test_html_is_escaped_in_titles(tmp_path):
    posts_dir = tmp_path / "weirdposts"
    posts_dir.mkdir()
    (posts_dir / "2026-12-01-breaking-<script>.md").write_text("---\n---\nHi.")
    out_dir = tmp_path / "out"
    build.build_site(posts_dir, out_dir)
    html_text = read(out_dir, "index.html")
    assert "<script>" not in html_text
    assert "&lt;script&gt;" in html_text
