# seven-topics-a-week-site-template

A static site template for publishing a **weekly topics newsletter** on
GitHub Pages — one HTML page per weekly topic, generated from plain
Markdown in `posts/`, with an archive index, an inline RSS feed, and a
next-week stub for scheduling.

Built for the write-in-public workflow of a **solo author**: write at home,
publish on a schedule, keep drafts private until you flip the switch.

- **No JavaScript framework.** No frameworks at all — the output is plain
  HTML with inline CSS.
- **No build tools beyond Python.** The generator is a single stdlib-only
  script (`build.py`). Python 3.9+ (tested on 3.13).
- **Friendly output.** Explains things like a friend would: plain English,
  step by step, never condescending.

Published by [Asdale Dynamics, LLC](https://dylanasdale.github.io) as part
of Dylan Asdale's plain-English AI guides. MIT licensed — see `LICENSE`.

## Quick start

```bash
python3 build.py next       # create posts/<next-date>-new-topic.md (a draft stub)
# ...write this week's topic in that file...
python3 build.py build      # generate the site into docs/
python3 build.py serve      # preview at http://localhost:8000 (Ctrl+C to stop)
python3 build.py check      # sanity-check posts/: drafts, dates, SITE_URL
```

That is the entire toolchain. No install step, no dependencies, no secrets.

## How the pieces fit together

```
posts/                 ← you write here (one Markdown file per weekly topic)
docs/                  ← generated output: GitHub Pages serves this folder
build.py               ← the whole generator (stdlib only)
tests/                 ← pytest suite with Markdown fixtures
```

Each post file is named `YYYY-MM-DD-your-topic.md` (the date sets the
issue's position on the weekly cadence) and starts with small front matter:

```markdown
---
title: What agents actually do
summary: One honest sentence about what readers will learn this week.
tags: agents, beginners
draft: yes        # optional — the publish switch
---

Your issue, in friendly Markdown: headings, lists, a quote, a code fence,
[links](https://example.com). That is the whole vocabulary you need.
```

On `build`, every non-draft post becomes one HTML page in `docs/posts/`,
plus:

- **`docs/index.html`** — the archive index, newest first, grouped by year,
  with a tiny "In the works" section listing scheduled drafts.
- **`docs/feed.xml`** — the RSS feed. Every page also carries an inline
  `<link rel="alternate" type="application/rss+xml">` so readers can
  subscribe with one click in any RSS-aware browser or reader.
- **`docs/next.html`** — the next-week stub: the scheduled date (always
  exactly seven days after the newest issue) and the step-by-step writing
  checklist.

## The solo-author, write-in-public workflow

1. **Stage next week.** `python3 build.py next` creates a stub file with
   `draft: yes`. Drafts are *never* built, never indexed, never fed — they
   do not exist for readers yet. Scheduling is public; drafts are private.
2. **Write in the stub.** Replace the TODO. Give it a real title and
   summary. There is no deadline drama — the file just waits.
3. **Preview at home.** `python3 build.py build && python3 build.py serve`.
   `build.py check` will gently warn about placeholder configuration.
4. **Flip the switch.** Delete the `draft: yes` line. That is the entire
   publish action.
5. **Rebuild and commit both folders together** — `posts/` and `docs/` in
   one commit — then push. GitHub Pages updates within a minute or two.

## Publishing on GitHub Pages

1. Push this repository to GitHub.
2. Open **Settings → Pages**. Under "Build and deployment", set Source to
   **Deploy from a branch**, branch **main**, folder **`/docs`**.
3. Before your first real deploy, edit `SITE_URL` at the top of `build.py`
   to your page URL (for example
   `https://your-username.github.io/your-repo`) so RSS links are absolute.
   `python3 build.py check` reminds you while it is still a placeholder.
4. Every push to main republishes the site: the new issue, the updated
   archive, and the moved-up "next week" date.

## Making it yours

- Site title, tagline, author, description and `SITE_URL` all live at the
  top of `build.py` — edit four lines and rebuild.
- Add your signing-off line or a tiny logo by editing the `page()` shell
  and `STYLE` constant in the same file.

## Tests

`pytest` must be available (`pip install pytest`), then:

```bash
python3 -m pytest
```

The suite uses Markdown fixture posts in `tests/fixtures/posts/` and
verifies: the tiny Markdown converter (headings, lists, quotes, fences,
links, escaping), page generation, archive ordering, draft exclusion, the
inline RSS feed (valid XML, RFC 822 dates, absolute links), the next-week
stub math, the stub-never-overwrites rule, CLI commands, and check
warnings.

## What this is *not*

This is the **web** newsletter: pages, archive, RSS. It is deliberately
distinct from a plain-email newsletter template (which sends mail) and from
a directory-site starter (which lists many pages of a site, not issues).
Nothing here sends, receives, or stores personal data.

## License

MIT — Copyright (c) 2026 Asdale Dynamics, LLC. See [LICENSE](LICENSE).

Educational content only — not professional, medical, or legal advice.
