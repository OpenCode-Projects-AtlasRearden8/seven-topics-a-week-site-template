#!/usr/bin/env python3
"""Static site generator for a weekly topics newsletter, published to GitHub Pages.

One HTML page per weekly topic, generated from Markdown files in ``posts/``,
plus an archive index, an RSS feed, and a next-week scheduling stub.

Pure Python 3 standard library. No frameworks, no external dependencies,
no build tools beyond Python.

Usage:
    python3 build.py build            # generate the site into docs/
    python3 build.py serve            # preview docs/ at http://localhost:8000
    python3 build.py next             # create a stub Markdown file for next week
    python3 build.py check            # sanity-check the posts/ folder
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import html
import re
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path


def _quote_url(path: str) -> str:
    """Percent-encode anything unsafe in a URL path (spaces, quotes, <>&)."""
    return urllib.parse.quote(path, safe="/")

# ---------------------------------------------------------------------------
# Site configuration (edit these to make the template your own)
# ---------------------------------------------------------------------------
TITLE = "One Topic a Week"
TAGLINE = "Plain-English AI, one friendly topic each week."
AUTHOR = "Dylan Asdale"
PUBLISHER = "Asdale Dynamics, LLC"
DESCRIPTION = (
    "A newsletter that sets one beginner-friendly AI topic each week and "
    "explains it like a friend would: plain English, step by step, never "
    "condescending. Written in public."
)
# Used to build absolute links inside the RSS feed. Edit when publishing:
# https://YOUR-USERNAME.github.io/YOUR-REPO
SITE_URL = "https://your-username.github.io/your-repo"

POSTS_DIR = Path("posts")
OUT_DIR = Path("docs")
NOT_ADVICE = "Educational content only — not professional, medical, or legal advice."

# ---------------------------------------------------------------------------
# Parsing: filenames, front matter, Markdown
# ---------------------------------------------------------------------------
FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$", re.IGNORECASE)
FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n?", re.DOTALL)
DRAFT_YES = {"yes", "true", "1", "on"}


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split a ``---`` block from the Markdown body."""
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip().lower()] = value.strip()
    return meta, text[match.end():]


def slug_to_title(slug: str) -> str:
    return " ".join(word.capitalize() for word in re.split(r"[-_]+", slug) if word)


def plain_text(markdown_fragment: str) -> str:
    """Crude plain-text extraction from a Markdown fragment (for RSS/fallbacks)."""
    fragment = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", markdown_fragment)
    fragment = re.sub(r"[`*_>\[\]#]+", " ", fragment)
    return re.sub(r"\s+", " ", fragment).strip()


def first_paragraph(markdown: str, limit: int = 160) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "```", ">", "-", "*", "+")):
            continue
        text = plain_text(stripped)
        if len(text) > limit:
            text = text[: limit - 1].rstrip() + "\u2026"
        return text
    return ""


def _inline(text: str) -> str:
    """Convert inline Markdown to HTML (escapes HTML first, always safe)."""
    text = html.escape(text, quote=False)
    stash: list[str] = []

    def keep_code(match: re.Match) -> str:
        stash.append(f"<code>{match.group(1)}</code>")
        return f"\x00{len(stash) - 1}\x00"

    text = re.sub(r"`([^`]+)`", keep_code, text)
    text = re.sub(
        r"\[([^\]]+)\]\((\S+?)\)",
        lambda m: '<a href="%s">%s</a>'
        % (m.group(2).replace('"', "%22"), m.group(1)),
        text,
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)
    return text


HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
UL_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
OL_RE = re.compile(r"^\s*\d+[.)]\s+(.*)$")
HR_RE = re.compile(r"^(\*\*\*|___|-{3,})\s*$")


def md_to_html(markdown: str) -> str:
    """Convert a small, predictable subset of Markdown to HTML."""
    lines = markdown.split("\n")
    out: list[str] = []
    paragraph: list[str] = []
    i = 0

    def flush() -> None:
        if paragraph:
            out.append("<p>" + "<br>\n".join(_inline(l) for l in paragraph) + "</p>")
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip the closing fence
            out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
            continue

        if not stripped:
            flush()
            i += 1
            continue

        match = HEADING_RE.match(stripped)
        if match:
            flush()
            level = len(match.group(1))
            out.append(f"<h{level}>{_inline(match.group(2))}</h{level}>")
            i += 1
            continue

        if HR_RE.match(stripped):
            flush()
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote>" + md_to_html("\n".join(quote)) + "</blockquote>")
            continue

        if UL_RE.match(stripped):
            flush()
            items = []
            while i < len(lines) and UL_RE.match(lines[i]):
                items.append(UL_RE.match(lines[i]).group(1))
                i += 1
            out.append(
                "<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + "</ul>"
            )
            continue

        if OL_RE.match(stripped):
            flush()
            items = []
            while i < len(lines) and OL_RE.match(lines[i]):
                items.append(OL_RE.match(lines[i]).group(1))
                i += 1
            out.append(
                "<ol>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + "</ol>"
            )
            continue

        paragraph.append(line)
        i += 1

    flush()
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------
@dataclass
class Post:
    date: dt.date
    slug: str
    title: str
    summary: str
    tags: list[str]
    draft: bool
    body_html: str
    source: Path

    @property
    def filename(self) -> str:
        return self.source.name

    @property
    def html_filename(self) -> str:
        return self.source.name[:-3] + ".html"

    @property
    def rel_href(self) -> str:
        """URL-encoded link for HTML and RSS, relative to docs/."""
        return "posts/" + _quote_url(self.html_filename)

    @property
    def iso_date(self) -> str:
        return self.date.strftime("%Y-%m-%d")

    @property
    def long_date(self) -> str:
        return f"{self.date:%B} {self.date.day}, {self.date.year}"


def load_posts(posts_dir: Path) -> list[Post]:
    """Load every Markdown post. Newest first. Drafts are included (flagged)."""
    posts: list[Post] = []
    if not posts_dir.is_dir():
        return posts
    for path in sorted(posts_dir.glob("*.md")):
        match = FILENAME_RE.match(path.name)
        if not match:
            print(
                f"warning: skipped {path.name} — filenames look like "
                "YYYY-MM-DD-your-topic.md",
                file=sys.stderr,
            )
            continue
        date = dt.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        slug = match.group(4)
        meta, body_markdown = parse_front_matter(path.read_text(encoding="utf-8"))
        title = meta.get("title") or slug_to_title(slug)
        summary = meta.get("summary") or first_paragraph(body_markdown)
        tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
        draft = meta.get("draft", "").lower() in DRAFT_YES
        posts.append(
            Post(
                date=date,
                slug=slug,
                title=title,
                summary=summary,
                tags=tags,
                draft=draft,
                body_html=md_to_html(body_markdown.strip()),
                source=path,
            )
        )
    posts.sort(key=lambda p: (p.date, p.slug), reverse=True)
    return posts


def next_issue_date(published: list[Post]) -> dt.date:
    """A weekly cadence: seven days after the most recent issue."""
    last = published[0].date if published else dt.date.today()
    return last + dt.timedelta(days=7)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
STYLE = """
:root {
  --ink: #2b3947; --soft: #5f6f7d; --accent: #7b5ea7; --line: #e6e1d8;
  --paper: #fffdf8; --code: #f4f2ec; --quote-bg: #faf7ff; --ok: #2e7d4f;
}
* { box-sizing: border-box; }
body {
  margin: 0; color: var(--ink); background: var(--paper);
  font-family: ui-sans-serif, system-ui, "Segoe UI", Helvetica, Arial, sans-serif;
  line-height: 1.7;
}
main { max-width: 46rem; margin: 0 auto; padding: 1rem 1.25rem 3rem; }
a { color: var(--accent); }
header { padding: 2.5rem 1.25rem 0.5rem; text-align: center; }
header .brand, header .brand a {
  font-size: 1.35rem; font-weight: 700; color: var(--ink);
  text-decoration: none; letter-spacing: -0.01em;
}
header .tagline { color: var(--soft); margin-top: 0.35rem; font-size: 0.98rem; }
h1, h2, h3 { line-height: 1.25; letter-spacing: -0.01em; }
.meta { color: var(--soft); font-size: 0.92rem; }
blockquote {
  border-left: 4px solid #ddd0f0; background: var(--quote-bg);
  margin: 1.3rem 0; padding: 0.5rem 1.1rem; color: var(--soft);
}
pre {
  background: var(--code); padding: 0.9rem 1.1rem; border-radius: 8px;
  overflow-x: auto; line-height: 1.5;
}
pre code { background: none; padding: 0; }
code {
  background: var(--code); padding: 0.1rem 0.35rem; border-radius: 4px;
  font-size: 0.92em;
}
img { max-width: 100%; }
hr { border: 0; border-top: 1px solid var(--line); margin: 2rem 0; }
.issues { list-style: none; padding-left: 0; }
.issues li { margin: 1.1rem 0; padding-left: 0; }
.issues .summary { color: var(--soft); font-size: 0.95rem; }
.year { color: var(--soft); border-bottom: 1px solid var(--line); }
.background { color: var(--soft); font-size: 0.95rem; }
.back { margin-top: 2.5rem; }
.scheduled {
  border: 1px solid var(--line); border-radius: 8px;
  padding: 0.9rem 1.2rem; background: #f6fbf7;
}
.scheduled .ok { color: var(--ok); font-weight: 600; }
.steps li { margin: 0.45rem 0; }
footer {
  border-top: 1px solid var(--line); text-align: center;
  color: var(--soft); font-size: 0.9rem; padding: 1.4rem 1rem 2rem; line-height: 1.5;
}
footer .fineprint { font-size: 0.82rem; margin-top: 0.4rem; }
"""


def page(title: str, description: str, rel_depth: int, body: str) -> str:
    """Wrap body content in the shared page shell (inline CSS, inline RSS link)."""
    up = "../" * rel_depth
    rss = f"{up}feed.xml"
    home = f"{up}index.html"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="alternate" type="application/rss+xml" title="{html.escape(TITLE)}" href="{rss}">
<style>{STYLE}</style>
</head>
<body>
<header>
<p class="brand"><a href="{home}">{html.escape(TITLE)}</a></p>
<p class="tagline">{html.escape(TAGLINE)}</p>
</header>
<main>
{body}
</main>
<footer>
<p>Written in public by {html.escape(AUTHOR)} &middot; Published by {html.escape(PUBLISHER)} &middot; <a href="{rss}">RSS feed</a> &middot; <a href="{home}">Archive</a></p>
<p class="fineprint">{html.escape(NOT_ADVICE)} &middot; &copy; 2026 {html.escape(PUBLISHER)} &middot; MIT License</p>
</footer>
</body>
</html>
"""


def render_post(post: Post) -> str:
    tags = f" &middot; #{', #'.join(post.tags)}" if post.tags else ""
    body = f"""<article>
<h1>{html.escape(post.title)}</h1>
<p class="meta"><time datetime="{post.iso_date}">{post.long_date}</time>{tags}</p>
{post.body_html}
<p class="back"><a href="../index.html">&larr; All topics</a></p>
</article>"""
    return page(f"{post.title} · {TITLE}", post.summary, 1, body)


def render_index(published: list[Post], drafts: list[Post]) -> str:
    lines = [
        "<section>",
        "<h1>Archive</h1>",
        f'<p class="about">{html.escape(DESCRIPTION)}</p>',
        '<p class="subscribe">Every issue in one place. Subscribe with any RSS '
        'reader: <a href="feed.xml">feed.xml</a>.</p>',
        "</section>",
    ]
    if drafts:
        lines.append("<section>")
        lines.append("<h2 class=\"year\">In the works</h2>")
        lines.append('<p class="background">Drafts staged in posts/ (not published yet):</p>')
        lines.append('<ul class="issues">')
        for d in drafts:
            lines.append(
                f"  <li>{html.escape(d.title)} "
                f'<span class="summary">&mdash; draft, scheduled for '
                f'<time datetime="{d.iso_date}">{d.long_date}</time></span></li>'
            )
        lines.append("</ul>")
        lines.append("</section>")
    if published:
        lines.append("<section>")
        open_year = None
        for post in published:
            if post.date.year != open_year:
                if open_year is not None:
                    lines.append("</ul>")
                open_year = post.date.year
                lines.append(f'<h2 class="year">{open_year}</h2>')
                lines.append('<ul class="issues">')
            lines.append(
                f'  <li><a href="{post.rel_href}">{html.escape(post.title)}</a><br>'
                f'  <time datetime="{post.iso_date}">{post.long_date}</time><br>'
                f'  <span class="summary">{html.escape(post.summary)}</span></li>'
            )
        lines.append("</ul>")
        lines.append("</section>")
    else:
        lines.append('<section><p>No issues published yet — run '
                     '<code>python3 build.py next</code> and write the first '
                     'one.</p></section>')
    body = "\n".join(lines)
    return page(f"Archive · {TITLE}", DESCRIPTION, 0, body)


def render_next(published: list[Post], stub_name: str) -> str:
    date = next_issue_date(published)
    long_date = f"{date:%B} {date.day}, {date.year}"
    body = f"""<article>
<h1>Next week: {long_date}</h1>
<p class="scheduled"><span class="ok">Scheduled.</span> The next issue goes out
<time datetime="{date.strftime('%Y-%m-%d')}">{long_date}</time>.
The weekly cadence is simple: one topic, seven days, every week.</p>
<h2>Write it in public</h2>
<ol class="steps">
<li>Create or edit the stub file: <code>posts/{stub_name}</code>
(if it is missing, run <code>python3 build.py next</code>).</li>
<li>Give it a real <code>title:</code> and <code>summary:</code>, then replace
the TODO with the issue itself.</li>
<li>Preview at home: <code>python3 build.py build &amp;&amp; python3 build.py serve</code>.</li>
<li>When the words are ready for readers, remove the
<code>draft: yes</code> line from the front matter &mdash; that is the
publish switch.</li>
<li>Rebuild and commit both folders together:
<code>python3 build.py build</code>, then commit <code>posts/</code> and
<code>docs/</code> in one commit.</li>
</ol>
<p class="background">While a file is marked <code>draft: yes</code>, it stays
on your machine: it is not built, not in the archive, and not in the RSS
feed. Scheduling is public; drafts are private.</p>
<p class="back"><a href="index.html">&larr; All topics</a></p>
</article>"""
    return page(f"Next week · {TITLE}", "What is scheduled next on the weekly cadence.", 0, body)


def rfc822(date: dt.date) -> str:
    moment = dt.datetime(date.year, date.month, date.day, 9, 0, tzinfo=dt.timezone.utc)
    return email.utils.format_datetime(moment)


def render_feed(published: list[Post]) -> str:
    base = SITE_URL.rstrip("/")
    items = []
    for post in published:
        url = f"{base}/{post.rel_href}"
        items.append(
            f"<item><title>{html.escape(post.title)}</title>"
            f"<link>{html.escape(url)}</link>"
            f'<guid isPermaLink="true">{html.escape(url)}</guid>'
            f"<pubDate>{rfc822(post.date)}</pubDate>"
            f"<description>{html.escape(post.summary)}</description>"
            f"</item>"
        )
    latest = published[0].date if published else dt.date.today()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>{html.escape(TITLE)}</title>
<link>{html.escape(base + "/")}</link>
<description>{html.escape(DESCRIPTION)}</description>
<language>en-us</language>
<pubDate>{rfc822(latest)}</pubDate>
<lastBuildDate>{rfc822(latest)}</lastBuildDate>
{"" if not items else ""}
{"".join(chr(10)+item for item in items)}
</channel>
</rss>
"""


# ---------------------------------------------------------------------------
# Build, stub, check, serve
# ---------------------------------------------------------------------------
def create_next_stub(posts_dir: Path, date: dt.date | None = None) -> tuple[Path, bool]:
    """Create a skeleton Markdown file for next week. Never overwrites."""
    if date is None:
        date = next_issue_date(
            [p for p in load_posts(posts_dir) if not p.draft]
        )
    path = posts_dir / f"{date:%Y-%m-%d}-new-topic.md"
    if path.exists():
        return path, False
    posts_dir.mkdir(parents=True, exist_ok=True)
    long_date = f"{date:%B} {date.day}, {date.year}"
    path.write_text(
        f"""---
title: (Make me a title)
summary: One honest sentence about what readers will learn this week.
tags:
draft: yes
---

TODO — write next week's issue here.

Skeleton that works well for this newsletter:

## The topic in one sentence

## Why it matters to you

## Try it yourself (step by step)

1. ...

## One friendly note

*(Delete this section and replace it with your sign-off.)*

<!-- Scheduled for {long_date}. While `draft: yes`, this file never gets \
published. Remove that line when it is ready, rebuild, and commit. -->
""",
        encoding="utf-8",
    )
    return path, True


def build_site(posts_dir: Path = POSTS_DIR, out_dir: Path = OUT_DIR) -> dict[str, list[str]]:
    """Generate the site. Returns the names of everything written."""
    all_posts = load_posts(posts_dir)
    published = [p for p in all_posts if not p.draft]
    drafts = [p for p in all_posts if p.draft]

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    def write(rel_name: str, content: str) -> None:
        target = out_dir / rel_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(rel_name)

    write("index.html", render_index(published, drafts))
    write("feed.xml", render_feed(published))
    next_date = next_issue_date(published)
    write("next.html", render_next(published, f"{next_date:%Y-%m-%d}-new-topic.md"))
    for post in published:
        write(f"posts/{post.html_filename}", render_post(post))
    return {"published": [p.filename for p in published], "written": written}


def check(posts_dir: Path = POSTS_DIR) -> tuple[list[str], list[str]]:
    """Report problems and heads-ups. Returns (problems, warnings)."""
    problems: list[str] = []
    warnings: list[str] = []
    if "your-username" in SITE_URL:
        warnings.append("SITE_URL in build.py is still a placeholder — edit it before "
                        "publishing so RSS links are absolute.")
    for post in load_posts(posts_dir):
        if post.draft:
            warnings.append(f"{post.filename}: draft (OK — hidden until you remove "
                            "`draft: yes`)")
        if post.date > dt.date.today() and not post.draft:
            problems.append(f"{post.filename}: published post is dated in the future")
        if not post.summary:
            problems.append(f"{post.filename}: empty title and summary")
    seen: dict[tuple, str] = {}
    for post in load_posts(posts_dir):
        key = (post.date, post.slug)
        if key in seen:
            problems.append(f"{post.filename}: same date and slug as {seen[key]}")
        seen[key] = post.filename
    return problems, warnings


def serve(directory: Path, port: int) -> None:
    import functools
    import http.server

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(directory)
    )
    with http.server.ThreadingHTTPServer(("", port), handler) as httpd:
        print(f"Serving {directory} at http://localhost:{port} — press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            return


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the weekly topics newsletter site."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="generate the site into docs/")
    p_build.add_argument("--posts", type=Path, default=POSTS_DIR)
    p_build.add_argument("--out", type=Path, default=OUT_DIR)

    p_next = sub.add_parser("next", help="create a stub Markdown file for next week")
    p_next.add_argument("--posts", type=Path, default=POSTS_DIR)

    p_serve = sub.add_parser("serve", help="preview the built site")
    p_serve.add_argument("--dir", type=Path, default=OUT_DIR)
    p_serve.add_argument("--port", type=int, default=8000)

    p_check = sub.add_parser("check", help="sanity-check the posts folder")
    p_check.add_argument("--posts", type=Path, default=POSTS_DIR)

    args = parser.parse_args(argv)

    if args.command == "build":
        result = build_site(args.posts, args.out)
        print(f"Published {len(result['published'])} issue(s):")
        for name in result["written"]:
            print(f"  docs/{name}")
        return 0

    if args.command == "next":
        path, created = create_next_stub(args.posts)
        if created:
            print(f"Created stub: {path}")
            print("Fill it in, then remove the `draft: yes` line when it is ready.")
        else:
            print(f"Already there: {path} (left untouched).")
        return 0

    if args.command == "check":
        problems, warnings = check(args.posts)
        for line in warnings:
            print(f"warning: {line}")
        for line in problems:
            print(f"problem: {line}")
        if problems:
            return 1
        print("check: all clear.")
        return 0

    serve(args.dir, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
