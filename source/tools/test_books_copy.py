#!/usr/bin/env python3
"""Yeti offers no hosted cloud, free tier or sign-up (YTC-2900, YTC-2928).

Reads every page source in every book under source/books, the markdown and
the two top-level HTML pages the build copies, so no page can teach any of
them again.

Run:
    python3 -m unittest discover -s source/tools -p 'test_*.py'
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

BOOKS = Path(__file__).resolve().parents[1] / "books"
NAMES = ("learn", "guides", "reference")
RETIRED = re.compile(
    r"free[ -]?tier|no credit card|sign up at"
    r"|yeti cloud|managed hosting|cloud\.yetirocks\.com|cloud mode|build server|usage-based pricing",
    re.I,
)


def _pages() -> list[Path]:
    return sorted(p for p in BOOKS.rglob("*") if p.suffix in (".md", ".html"))


class BooksCopy(unittest.TestCase):
    maxDiff = None  # name every line that fails, not the first

    def test_reads_every_book(self) -> None:
        names = [p.relative_to(BOOKS).as_posix() for p in _pages()]
        self.assertGreater(len(names), 50)
        for book in NAMES:
            self.assertGreater(sum(n.startswith(f"{book}/") for n in names), 5, book)

    def test_no_page_offers_a_hosted_cloud_free_tier_or_sign_up(self) -> None:
        hits = [
            f"{p.relative_to(BOOKS).as_posix()}:{n}"
            for p in _pages()
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if RETIRED.search(line)
        ]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
