#!/usr/bin/env python3
"""Yeti offers no free tier and no hosted sign-up (YTC-2900, YTC-2928).

Reads every page source under source/books, the markdown and the two
top-level HTML pages the build copies, so a page can't pitch either again.

Run:
    python3 -m unittest discover -s source/tools -p 'test_*.py'
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

BOOKS = Path(__file__).resolve().parents[1] / "books"
RETIRED = re.compile(r"free[ -]?tier|no credit card|sign up at", re.I)


def _pages() -> list[Path]:
    return sorted(p for p in BOOKS.rglob("*") if p.suffix in (".md", ".html"))


class BooksCopy(unittest.TestCase):
    def test_finds_the_pages(self) -> None:
        names = [p.relative_to(BOOKS).as_posix() for p in _pages()]
        self.assertGreater(len(names), 50)
        self.assertIn("reference/deployment/cloud.md", names)

    def test_no_page_offers_a_free_tier_or_a_sign_up(self) -> None:
        hits = [
            f"{p.relative_to(BOOKS).as_posix()}:{n}"
            for p in _pages()
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if RETIRED.search(line)
        ]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
