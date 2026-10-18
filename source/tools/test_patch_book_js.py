#!/usr/bin/env python3
"""Tests for the book.js patcher (YTC-2140).

Against the stock book.js of the installed mdBook (`mdbook init --theme`):
every patch applies exactly once and the result parses. Against the built
web/ tree when present: every book ships the patched book.js, and none of its
pages renders the markup the skipped blocks need, so each guard is the one
that runs.

Run:
    python3 -m unittest discover -s source/tools -p 'test_*.py'
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import patch_book_js as pb  # noqa: E402

WEB = Path(__file__).resolve().parents[2] / "web"
BOOKS = ("learn", "guides", "reference")


def _stock_book_js() -> str:
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(
            ["mdbook", "init", "--theme", "--force", "--title", "stock", "--ignore", "none", d],
            check=True,
            capture_output=True,
        )
        return (Path(d) / "theme" / "book.js").read_text(encoding="utf-8")


@unittest.skipUnless(shutil.which("mdbook"), "mdbook not installed")
class StockTest(unittest.TestCase):
    def setUp(self) -> None:
        self.stock = _stock_book_js()

    def test_every_anchor_is_in_stock_once(self) -> None:
        for name, anchor, _ in pb.PATCHES:
            self.assertEqual(self.stock.count(anchor), 1, name)

    def test_patched_has_every_guard_and_parses(self) -> None:
        out = pb.patch(self.stock)
        self.assertEqual(out.count(pb.MARK), len(pb.PATCHES))
        self.assertIn("if (themePopup === null || themeToggleButton === null) {", out)
        if shutil.which("node"):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(out)
            try:
                subprocess.run(["node", "--check", f.name], check=True, capture_output=True)
            finally:
                Path(f.name).unlink()

    def test_a_missing_anchor_fails(self) -> None:
        moved = self.stock.replace("document.getElementById('theme-list')", "x()")
        with self.assertRaisesRegex(pb.PatchError, "themes: .* 0 copies"):
            pb.patch(moved)

    def test_patching_twice_fails(self) -> None:
        with self.assertRaises(pb.PatchError):
            pb.patch(pb.patch(self.stock))


@unittest.skipUnless((WEB / "learn" / "book.js").is_file(), "web/ not built")
class BuiltOutputTest(unittest.TestCase):
    """The ids the skipped blocks need are absent from every built page."""

    ABSENT = ('id="theme-list"', 'id="theme-toggle"', 'id="sidebar-resize-handle"',
              'id="menu-bar"', 'class="menu-title"', 'id="mdbook-help-container"')

    def test_every_book_ships_the_patched_book_js(self) -> None:
        for book in BOOKS:
            js = (WEB / book / "book.js").read_text(encoding="utf-8")
            self.assertEqual(js.count(pb.MARK), len(pb.PATCHES), book)

    def test_no_page_renders_the_skipped_markup(self) -> None:
        for book in BOOKS:
            for page in (WEB / book).rglob("*.html"):
                html = page.read_text(encoding="utf-8")
                if "book.js" not in html:
                    continue
                for needle in self.ABSENT:
                    self.assertNotIn(needle, html, f"{page}: {needle}")


if __name__ == "__main__":
    unittest.main()
