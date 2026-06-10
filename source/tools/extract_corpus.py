#!/usr/bin/env python3
"""Docs-corpus passage extractor (ADR-028).

Runs after `mdbook build`, reads each book's rendered output, and emits the
content package beside `web/`:

    data/
      corpus-manifest.json          corpus version + live passage-ID set
      passages/{book}/{page}.json   sharded seed files (one per page)

Each passage carries a stable ID (`book/page#anchor`), title, breadcrumb,
canonical URL, the prose to embed, and `related` — the structural link graph
(same-page sibling sections + outbound in-corpus hyperlinks). No embeddings
are emitted: the platform embeds the `passage` field on ingest/backfill, so
the index-time and query-time models match by construction (ADR-028 §2).

The corpus version lives ONLY in the manifest, never in passage records:
stamping a version into every record would change every shard's bytes each
build and defeat the loader's per-file hash-skip, re-embedding the entire
corpus on every release (ADR-028 §5). Unchanged pages stay byte-identical →
skipped → embeddings persist.

Input layout (CWD is the static `source` dir, per the app build config):
    ../web/{book}/searchindex.js   mdbook search index (authoritative section
                                   list: url, title, breadcrumb, body)
    ../web/{book}/**/*.html        rendered pages (outbound-link graph)

Usage:
    python3 tools/extract-corpus.py [--web ../web] [--data ../data]
                                    [--books learn,guides,reference]

Environment:
    DOCS_CANONICAL_BASE   canonical host for deep links
                          (default: https://docs.yetirocks.com)
    DOCS_CORPUS_VERSION   override the corpus version (default: docs git SHA,
                          falling back to a deterministic content digest)

Pure standard library — no third-party dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

DATABASE = "documentation"
TABLE = "Passage"
DEFAULT_BOOKS = ["learn", "guides", "reference"]
DEFAULT_CANONICAL_BASE = "https://docs.yetirocks.com"
# mdbook's site-url prefix; the published path is /documentation/{book}/...
SITE_PREFIX = "/documentation"

# Captures the JSON payload mdbook wraps in `JSON.parse('...')`.
_SEARCHINDEX_RE = re.compile(r"JSON\.parse\('(.*)'\)", re.DOTALL)


def log(msg: str) -> None:
    print(f"[extract-corpus] {msg}", file=sys.stderr)


@dataclass
class Passage:
    id: str
    book: str
    page: str
    anchor: str
    title: str
    breadcrumb: str
    url: str
    passage: str
    related: list[str] = field(default_factory=list)

    def to_record(self) -> dict:
        return {
            "id": self.id,
            "book": self.book,
            "page": self.page,
            "anchor": self.anchor,
            "title": self.title,
            "breadcrumb": self.breadcrumb,
            "url": self.url,
            "passage": self.passage,
            # `related` is a JSON-array-of-IDs serialized as a string so it
            # maps onto the schema's `related: String` field. Sorted for
            # byte-stability across builds (hash-skip relies on it).
            "related": json.dumps(sorted(set(self.related)), separators=(",", ":")),
        }


def decode_searchindex(text: str) -> dict:
    """Decode mdbook's `searchindex.js` into the parsed JSON object.

    mdbook emits `window.search = Object.assign(window.search,
    JSON.parse('<escaped-json>'))`. The payload is a JS string literal whose
    non-ASCII bytes are backslash-escaped UTF-8, so we unescape the JS string
    then re-decode the bytes as UTF-8.
    """
    m = _SEARCHINDEX_RE.search(text)
    if not m:
        raise ValueError("searchindex.js: no JSON.parse(...) payload found")
    payload = m.group(1)
    # `unicode_escape` turns the JS \xNN / \uNNNN / \\ escapes into the raw
    # bytes mdbook wrote; those bytes are UTF-8.
    decoded = payload.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")
    return json.loads(decoded)


class _LinkExtractor(HTMLParser):
    """Collects href targets from the rendered page's main content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.hrefs.append(value)


def page_outbound_links(html: str, book: str, page: str, valid_pages: set[str]) -> list[str]:
    """Resolve a page's in-corpus outbound hyperlinks to page IDs (`book/page`).

    Cross-book links (`../reference/foo.html`) and same-book relative links
    are both resolved against the book root. Only links whose target page
    exists in the corpus are kept; external links, asset links, and
    fragment-only links are dropped. Anchors are stripped — the link graph is
    page-level, then expanded to section IDs by the caller.
    """
    extractor = _LinkExtractor()
    extractor.feed(html)

    page_dir = os.path.dirname(page)
    targets: set[str] = set()
    for href in extractor.hrefs:
        if href.startswith(("http://", "https://", "mailto:", "//")):
            continue
        # Drop the fragment for page-level resolution.
        path = href.split("#", 1)[0]
        if not path or not path.endswith(".html"):
            continue
        if path.startswith("../"):
            # Relative to the book directory's parent → another book root.
            resolved = os.path.normpath(os.path.join(book, page_dir, path))
            parts = resolved.split(os.sep, 1)
            if len(parts) != 2:
                continue
            tgt_book, tgt_page = parts[0], parts[1]
        else:
            tgt_book = book
            tgt_page = os.path.normpath(os.path.join(page_dir, path)) if page_dir else path
        tgt_page = tgt_page.replace(os.sep, "/")
        tgt_id = f"{tgt_book}/{tgt_page}"
        if tgt_id in valid_pages and tgt_id != f"{book}/{page}":
            targets.add(tgt_id)
    return sorted(targets)


def extract_book(book: str, web_dir: Path, canonical_base: str) -> list[Passage]:
    """Extract every section of a book as a Passage."""
    book_dir = web_dir / book
    searchindex = book_dir / "searchindex.js"
    if not searchindex.exists():
        raise FileNotFoundError(f"missing search index: {searchindex}")

    data = decode_searchindex(searchindex.read_text(encoding="utf-8"))
    doc_urls: list[str] = data["doc_urls"]
    docs: dict = data["index"]["documentStore"]["docs"]

    # First pass: build the passage list and the page-ID set.
    passages: list[Passage] = []
    pages_seen: set[str] = set()
    page_to_passage_ids: dict[str, list[str]] = {}
    # The representative ("root") passage for each page — the first section,
    # which is the page heading. Outbound links point here, not at every
    # section of the target, keeping `related` a focused neighborhood.
    page_root_id: dict[str, str] = {}

    for key, rec in docs.items():
        idx = int(key)
        raw_url = doc_urls[idx]  # e.g. "sdk/overview.html#prelude-exports"
        page, _, anchor = raw_url.partition("#")
        page_id = f"{book}/{page}"
        pages_seen.add(page_id)
        passage_id = f"{book}/{raw_url}"
        title = (rec.get("title") or "").strip()
        breadcrumb = " » ".join(
            part.strip()
            for part in (rec.get("breadcrumbs") or "").split("»")
            if part.strip()
        )
        body = (rec.get("body") or "").strip()
        # Embed the heading alongside the body: short sections embed better
        # with their title as context, and the title is what a reader scans.
        passage_text = f"{title}\n\n{body}".strip() if body else title
        url = f"{canonical_base}{SITE_PREFIX}/{book}/{page}"
        if anchor:
            url = f"{url}#{anchor}"
        p = Passage(
            id=passage_id,
            book=book,
            page=page,
            anchor=anchor,
            title=title,
            breadcrumb=breadcrumb,
            url=url,
            passage=passage_text,
        )
        passages.append(p)
        page_to_passage_ids.setdefault(page_id, []).append(passage_id)
        # First section encountered for a page is its root (mdbook emits the
        # page heading first).
        page_root_id.setdefault(page_id, passage_id)

    # Second pass: build the link graph. `related` = same-page sibling
    # sections + section IDs of in-corpus outbound link targets.
    page_link_cache: dict[str, list[str]] = {}
    for p in passages:
        page_id = f"{p.book}/{p.page}"
        related: set[str] = set()
        # Same-page siblings (every other section on this page).
        for sib in page_to_passage_ids.get(page_id, []):
            if sib != p.id:
                related.add(sib)
        # Outbound in-corpus links (resolved page-level, expanded to that
        # page's section IDs).
        if page_id not in page_link_cache:
            html_path = book_dir / p.page
            if html_path.exists():
                links = page_outbound_links(
                    html_path.read_text(encoding="utf-8", errors="replace"),
                    p.book,
                    p.page,
                    pages_seen,
                )
            else:
                links = []
            page_link_cache[page_id] = links
        for tgt_page_id in page_link_cache[page_id]:
            root = page_root_id.get(tgt_page_id)
            if root:
                related.add(root)
        related.discard(p.id)
        p.related = sorted(related)

    return passages


def shard_path(data_dir: Path, book: str, page: str) -> Path:
    """`data/passages/{book}/{page}.json`, where the page's `.html` becomes
    `.json` and nested dirs are preserved."""
    rel = page[:-5] if page.endswith(".html") else page
    return data_dir / "passages" / book / f"{rel}.json"


def write_shards(passages: list[Passage], data_dir: Path) -> dict[str, list[str]]:
    """Group passages by page and write one seed file per page.

    Returns a map of shard path (relative to data_dir) → passage IDs, used
    only for logging.
    """
    by_page: dict[tuple[str, str], list[Passage]] = {}
    for p in passages:
        by_page.setdefault((p.book, p.page), []).append(p)

    written: dict[str, list[str]] = {}
    for (book, page), group in by_page.items():
        out = shard_path(data_dir, book, page)
        out.parent.mkdir(parents=True, exist_ok=True)
        envelope = {
            "database": DATABASE,
            "table": TABLE,
            "records": [g.to_record() for g in group],
        }
        # Stable, sorted JSON so unchanged pages produce byte-identical
        # shards across builds (ADR-028 §5: preserves hash-skip + embeddings).
        out.write_text(
            json.dumps(envelope, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written[str(out.relative_to(data_dir))] = [g.id for g in group]
    return written


def corpus_version(passages: list[Passage], source_dir: Path) -> str:
    """Corpus version = docs git SHA, or a deterministic content digest.

    Deployed artifacts are not git repos, so we fall back to a SHA-256 over
    the sorted (id, passage) pairs — stable across builds for identical
    content, distinct when content changes (drives the purge sweep on bump).
    """
    override = os.environ.get("DOCS_CORPUS_VERSION")
    if override:
        return override
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=source_dir,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.strip()
        if sha:
            return sha
    except (subprocess.SubprocessError, OSError):
        pass
    h = hashlib.sha256()
    for p in sorted(passages, key=lambda x: x.id):
        h.update(p.id.encode("utf-8"))
        h.update(b"\0")
        h.update(p.passage.encode("utf-8"))
        h.update(b"\0")
    return f"content-{h.hexdigest()}"


def write_manifest(passages: list[Passage], data_dir: Path, version: str) -> Path:
    """Emit `corpus-manifest.json`: version + the live passage-ID set.

    Sits OUTSIDE the seed glob (`data/passages/**/*.json`) so the data loader
    treats it as sweep input, not table records (ADR-028 §1).
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "corpusVersion": version,
        "database": DATABASE,
        "table": TABLE,
        "passageCount": len(passages),
        "passageIds": sorted(p.id for p in passages),
    }
    out = data_dir / "corpus-manifest.json"
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out


def clean_passages(data_dir: Path) -> None:
    """Remove a stale `data/passages/` tree so deleted pages don't linger as
    orphan shards. The manifest purge handles the DB side; this handles the
    artifact side."""
    passages_dir = data_dir / "passages"
    if passages_dir.exists():
        for child in sorted(passages_dir.rglob("*.json"), reverse=True):
            child.unlink()
        # Prune now-empty directories.
        for d in sorted(passages_dir.rglob("*"), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
        if passages_dir.exists() and not any(passages_dir.iterdir()):
            passages_dir.rmdir()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract the docs search corpus (ADR-028).")
    parser.add_argument("--web", default="../web", help="rendered mdbook output dir")
    parser.add_argument("--data", default="../data", help="corpus output dir")
    parser.add_argument(
        "--books",
        default=",".join(DEFAULT_BOOKS),
        help="comma-separated book names",
    )
    parser.add_argument(
        "--source",
        default=".",
        help="docs source dir (for git SHA resolution)",
    )
    args = parser.parse_args(argv)

    web_dir = Path(args.web).resolve()
    data_dir = Path(args.data).resolve()
    source_dir = Path(args.source).resolve()
    books = [b.strip() for b in args.books.split(",") if b.strip()]
    canonical_base = os.environ.get("DOCS_CANONICAL_BASE", DEFAULT_CANONICAL_BASE).rstrip("/")

    if not web_dir.exists():
        log(f"ERROR: web dir not found: {web_dir}")
        return 1

    all_passages: list[Passage] = []
    for book in books:
        passages = extract_book(book, web_dir, canonical_base)
        log(f"{book}: {len(passages)} passages")
        all_passages.extend(passages)

    if not all_passages:
        log("ERROR: no passages extracted")
        return 1

    # Guard: passage IDs must be unique (they are the table primary key).
    ids = [p.id for p in all_passages]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        log(f"ERROR: duplicate passage IDs: {dupes[:10]}")
        return 1

    clean_passages(data_dir)
    written = write_shards(all_passages, data_dir)
    version = corpus_version(all_passages, source_dir)
    manifest_path = write_manifest(all_passages, data_dir, version)

    log(f"wrote {len(written)} shards, {len(all_passages)} passages")
    log(f"manifest: {manifest_path} (version {version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
