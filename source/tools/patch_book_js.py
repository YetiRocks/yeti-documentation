#!/usr/bin/env python3
"""Fit mdBook's stock book.js to this app's theme (YTC-2140).

theme/index.hbs is a heavy rewrite of mdBook's template. It forces the coal
theme and renders no theme picker, owns sidebar visibility itself (an inline
script plus a CSS hamburger), and has no menu bar, no menu title and no
keyboard-help popup. The stock book.js assumes all of those exist. Its
themes() block dereferenced #theme-list on every page of every book and threw
"Cannot read properties of null (reading 'querySelectorAll')", which aborted
the rest of the script.

Each block below whose markup the template does not render now returns before
touching it. A guard tests for the stock element that block needs, so the
same book.js still behaves stock under a stock template. The blocks that fit
the template run as stock: code snippets, the clipboard buttons, and the
arrow-key chapter navigation the template's prev/next links advertise with
aria-keyshortcuts (they carry rel="prev"/rel="next" rather than the stock
.nav-chapters classes).

The stock sidebar() block is skipped rather than guarded line by line: run
under this template it hides the sidebar on load, because it reads
`sidebar-visible` from <html> while the template puts it on <body>.

The source is the book.js of the mdBook doing the build (`mdbook init
--theme`), never a fork kept in theme/, so it cannot drift from the mdBook
that renders the rest of the page. Every patch anchors on one exact stock
line; if a newer mdBook no longer carries it, this exits non-zero and the
build stops instead of shipping an unpatched book.js.

Usage:
    python3 tools/patch_book_js.py <book.js>   # rewrites the file in place
"""

from __future__ import annotations

import sys
from pathlib import Path

MARK = "YTC-2140"


def _guard(anchor: str, why: str, cond: str, indent: str = "    ") -> str:
    """The anchor line, then a guard that returns from the block when `cond`."""
    return (
        f"{anchor}{indent}// {MARK}: {why}\n"
        f"{indent}if ({cond}) {{\n{indent}    return;\n{indent}}}\n"
    )


_THEMES = "    const themePopup = document.getElementById('theme-list');\n"
_SIDEBAR = "    const sidebarCheckbox = document.getElementById('sidebar-toggle-anchor');\n"
_NEXT = "            const nextButton = document.querySelector('.nav-chapters.next');\n"
_PREV = "            const previousButton = document.querySelector('.nav-chapters.previous');\n"
_HELP = "            const overlay = document.getElementById('mdbook-help-popup');\n"
_MENU_TITLE = "    const menuTitle = document.querySelector('.menu-title');\n"
_MENU = "    const menu = document.getElementById('menu-bar');\n"

# (block, exact stock line, what replaces it)
PATCHES: list[tuple[str, str, str]] = [
    ("themes", _THEMES, _guard(
        _THEMES, "this theme renders no theme picker (#theme-list).",
        "themePopup === null || themeToggleButton === null")),
    ("sidebar", _SIDEBAR, _guard(
        _SIDEBAR, "this theme owns sidebar visibility (no #sidebar-resize-handle).",
        "sidebar === null || sidebarToggleButton === null"
        " || sidebarCheckbox === null || sidebarResizeHandle === null")),
    # The template's chapter links are rel="next"/rel="prev", not .nav-chapters.
    ("chapterNavigation.next", _NEXT,
     "            const nextButton = document.querySelector("
     f"'.nav-chapters.next, a[rel=\"next\"]'); // {MARK}\n"),
    ("chapterNavigation.prev", _PREV,
     "            const previousButton = document.querySelector("
     f"'.nav-chapters.previous, a[rel=\"prev\"]'); // {MARK}\n"),
    ("chapterNavigation.help", _HELP, _guard(
        _HELP, "this theme renders no keyboard-help popup.",
        "container === null || overlay === null", indent="            ")),
    ("scrollToTop", _MENU_TITLE, _guard(
        _MENU_TITLE, "this theme renders no menu title.", "menuTitle === null")),
    ("controllMenu", _MENU, _guard(
        _MENU, "this theme renders no menu bar.", "menu === null")),
]


class PatchError(Exception):
    """A stock anchor was missing or ambiguous."""


def patch(src: str) -> str:
    """Return `src` with every patch applied; raise PatchError on a miss."""
    if MARK in src:
        raise PatchError(f"book.js already carries {MARK} patches")
    out = src
    for name, anchor, replacement in PATCHES:
        n = out.count(anchor)
        if n != 1:
            raise PatchError(
                f"{name}: stock book.js has {n} copies of the anchor, expected 1; "
                f"re-check the {MARK} patches against this mdBook:\n  {anchor.strip()}"
            )
        out = out.replace(anchor, replacement)
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(argv[1])
    try:
        path.write_text(patch(path.read_text(encoding="utf-8")), encoding="utf-8")
    except PatchError as e:
        print(f"patch_book_js: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
