"""Tests for the solo-author workflow: stubs, CLI commands, check, fallbacks."""
from pathlib import Path

import build
from conftest import read


def test_slug_and_summary_fallbacks(tmp_path):
    posts_dir = tmp_path / "posts"
    posts_dir.mkdir()
    (posts_dir / "2026-12-02-no-meta-here.md").write_text(
        "# Ignored heading\nThe very first paragraph becomes the summary.\n\nMore text.\n"
    )
    posts = build.load_posts(posts_dir)
    assert len(posts) == 1
    post = posts[0]
    assert post.title == "No Meta Here"
    assert post.summary == "The very first paragraph becomes the summary."
    assert post.tags == []
    assert not post.draft


def test_invalid_filenames_are_skipped_with_warning(tmp_path):
    posts_dir = tmp_path / "posts"
    posts_dir.mkdir()
    (posts_dir / "oops.md").write_text("---\n---\nbody")
    (posts_dir / "2026-12-02-real-post.md").write_text("---\n---\nbody")
    posts = build.load_posts(posts_dir)
    assert [p.slug for p in posts] == ["real-post"]


def test_create_next_stub_then_never_overwrites(tmp_path):
    posts_dir = tmp_path / "posts"
    path, created = build.create_next_stub(posts_dir, dt_b())
    assert created and path.exists()
    original = path.read_text(encoding="utf-8")
    path.write_text("my precious edits")
    path2, created2 = build.create_next_stub(posts_dir, dt_b())
    assert not created2
    assert path2 == path
    assert path.read_text(encoding="utf-8") == "my precious edits"


def dt_b():
    import datetime as dt
    return dt.date(2026, 11, 3) + dt.timedelta(days=7)


def test_next_stub_is_draft_and_excluded_from_build(tmp_path):
    posts_dir = tmp_path / "posts"
    path, created = build.create_next_stub(posts_dir, dt_b())
    out_dir = tmp_path / "out"
    build.build_site(posts_dir, out_dir)
    assert "TODO" not in read(out_dir, "feed.xml")
    assert not (out_dir / "posts" / path.name.replace(".md", ".html")).exists()


def test_cli_build_and_next(tmp_path, capsys):
    posts_dir = tmp_path / "posts"
    out_dir = tmp_path / "docs"
    posts_dir.mkdir()
    (posts_dir / "2026-11-03-sample.md").write_text("---\ntitle: Sample\n---\nHi.")
    assert build.main(["build", "--posts", str(posts_dir), "--out", str(out_dir)]) == 0
    assert (out_dir / "index.html").exists()
    assert (out_dir / "feed.xml").exists()
    assert (out_dir / "posts" / "2026-11-03-sample.html").exists()

    assert build.main(["next", "--posts", str(posts_dir)]) == 0
    stub = posts_dir / "2026-11-10-new-topic.md"
    assert stub.exists()
    assert "draft: yes" in stub.read_text(encoding="utf-8")

    # running next again is a no-op
    _ = capsys.readouterr()
    assert build.main(["next", "--posts", str(posts_dir)]) == 0
    assert "Already there" in capsys.readouterr().out


def test_cli_check_reports_draft_and_placeholder(tmp_path, capsys):
    posts_dir = tmp_path / "posts"
    posts_dir.mkdir()
    (posts_dir / "2026-11-03-sample.md").write_text(
        "---\ntitle: Sample\n---\nHi."  # published, clean
    )
    (posts_dir / "2026-11-10-wip.md").write_text(
        "---\ntitle: WIP\nsummary: s\ndraft: yes\n---\nHi."
    )
    assert build.main(["check", "--posts", str(posts_dir)]) == 0
    out = capsys.readouterr().out
    assert "draft" in out
    assert "all clear" in out


def test_cli_check_fails_on_future_published_post(tmp_path, capsys):
    import datetime as dt

    posts_dir = tmp_path / "posts"
    posts_dir.mkdir()
    future = dt.date.today() + dt.timedelta(days=30)
    (posts_dir / f"{future:%Y-%m-%d}-too-early.md").write_text(
        "---\ntitle: Too early\nsummary: s\n---\nHi."
    )
    assert build.main(["check", "--posts", str(posts_dir)]) == 1
    assert "future" in capsys.readouterr().out


def test_weekly_cadence_is_seven_days_after_last_issue():
    import datetime as dt

    last = dt.date(2026, 11, 3)
    posts = [
        build.Post(
            date=last,
            slug="x",
            title="x",
            summary="x",
            tags=[],
            draft=False,
            body_html="",
            source=Path("2026-11-03-x.md"),
        )
    ]
    assert build.next_issue_date(posts) == dt.date(2026, 11, 10)
