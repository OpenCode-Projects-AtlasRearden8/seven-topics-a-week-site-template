# STATUS.md

Last updated: 2026-11-05

## What was built

**seven-topics-a-week-site-template** — a static site template for publishing
a weekly topics newsletter on GitHub Pages, for a solo author working in
public. Published by Asdale Dynamics, LLC. MIT licensed.

Components:

- **`build.py`** — the entire generator, pure Python 3 standard library
  (no frameworks, no external dependencies, no other build tools):
  - A tiny, well-tested Markdown subset converter (headings, bold/italic,
    inline and fenced code, links, lists, blockquotes, horizontal rules,
    HTML escaping — including hostile titles and hrefs).
  - **One HTML page per weekly topic** from `posts/YYYY-MM-DD-topic.md`
    (front matter: `title`, `summary`, `tags`, optional `draft: yes`).
  - **`docs/index.html`** — archive index, newest first, grouped by year,
    plus an "In the works" section listing scheduled drafts.
  - **`docs/feed.xml`** — RSS 2.0 feed (RFC 822 dates, absolute links via
    `SITE_URL`); every generated page also carries an inline
    `<link rel="alternate" type="application/rss+xml">`.
  - **`docs/next.html`** — the next-week stub: the scheduled date (always
    newest issue + 7 days) and the step-by-step writing checklist.
  - **Scheduling workflow**: `python3 build.py next` creates a draft stub
    Markdown file and never overwrites existing files.
  - **Drafts stay private until the author deletes `draft: yes`** — they
    are never built, indexed, or fed.
  - `python3 build.py check` — sanity warnings (placeholder `SITE_URL`,
    drafts staged, future-dated posts, duplicate slugs).
  - `python3 build.py serve` — local preview server (stdlib HTTP).
- **`posts/`** — two sample published issues (local AI; what is MCP) and
  one scheduled draft stub, demonstrating the write-in-public workflow.
- **`tests/`** — pytest suite with Markdown fixtures in
  `tests/fixtures/posts/`.
- **`README.md`** — quick start, workflow (stage → write → preview →
  flip the switch → commit), GitHub Pages setup (`/docs` folder on
  `main`), customization, and testing instructions. Credits
  Asdale Dynamics, LLC.
- **`LICENSE`** — MIT, `Copyright (c) 2026 Asdale Dynamics, LLC`.
- **`docs/`** — pre-built output so Pages can serve immediately.

## How to run it

```bash
python3 build.py next       # stage next week's draft stub
python3 build.py build      # regenerate docs/ from posts/
python3 build.py serve      # preview http://localhost:8000
python3 build.py check      # sanity-check posts/ and configuration
python3 -m pytest           # run the test suite (pytest only dependency)
```

No install step. Python 3.9+ (developed and verified on 3.13).

## Verification results

- `python3 -m pytest` → **32 passed, 0 failed** (0.1 s), covering:
  Markdown conversion and HTML escaping, page generation, archive
  ordering/year grouping, draft exclusion everywhere, inline RSS link on
  all pages, RSS XML validity/absolute links/RFC 822 dates, next-week
  math (+7 days), stub-never-overwrites, CLI commands, and `check`
  warnings/exit codes.
- Real-site run: `build.py build` published 2 issues and generated
  5 files + 2 post pages in `docs/`; `check` returned all clear (with the
  expected placeholder-SITE_URL and draft warnings).
- Preview smoke test via `build.py serve`: index.html, feed.xml,
  next.html, and a post page all HTTP 200 with correct content types;
  `feed.xml` parses as valid XML.
- Scheduling verified: newest issue 2026-11-04 → scheduled 2026-11-11 and
  shown on `next.html` and in the archive's "In the works" section.

## Known gaps

- **`SITE_URL` in build.py is a placeholder** (`https://your-username.github.io/your-repo`)
  by design — edit it before publishing so RSS links are absolute. The
  `check` command reminds you until then.
- The Markdown converter is deliberately minimal (headings h1–h4, lists,
  blockquotes, fences, links, bold/italic/code, hr). No tables, images
  syntax works only via raw rare cases — images are not supported; add
  them if ever needed.
- Filename dates drive the cadence; a front-matter `date` override is not
  supported (documented behavior).
- No incremental build: `build.py build` always regenerates everything.
  Fast enough for a weekly newsletter (sub-second).
- No sitemap or Open Graph tags yet — easy to add in `page()` if wanted.
- The site template intentionally ships with placeholder identity config;
  nothing personal, secret, or private is embedded in any file.
