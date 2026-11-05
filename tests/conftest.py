import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402  (our generator module, not a stdlib collision)

FIXTURES = Path(__file__).parent / "fixtures"
SITE_URL = build.SITE_URL


@pytest.fixture
def site(tmp_path):
    """Build the site from Markdown fixtures into a temporary output dir."""
    posts_dir = tmp_path / "posts"
    shutil.copytree(FIXTURES / "posts", posts_dir)
    out_dir = tmp_path / "docs"
    result = build.build_site(posts_dir, out_dir)
    return {"posts_dir": posts_dir, "out_dir": out_dir, "result": result}


def read(out_dir: Path, name: str) -> str:
    return (out_dir / name).read_text(encoding="utf-8")
