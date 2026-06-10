#!/usr/bin/env python3
"""Tests for the docs-corpus pipeline (ADR-028).

Covers the extractor's build-output shape against a synthetic mdbook render
and against the real `web/` tree when present, plus the purge tool's
reconciliation logic against an in-memory fake API.

Run:
    python3 -m unittest discover -s source/tools -p 'test_*.py'
    # or directly:
    python3 source/tools/test_corpus.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import extract_corpus as ec  # noqa: E402
import purge_corpus as pc  # noqa: E402


def _searchindex_js(doc_urls: list[str], docs: dict) -> str:
    """Build a searchindex.js the way mdbook writes it: JSON wrapped in a JS
    string literal inside JSON.parse('...'). We escape exactly the chars the
    decoder reverses (backslash, quote) and let UTF-8 bytes through as the
    \\xNN escapes mdbook emits."""
    payload = json.dumps(
        {
            "doc_urls": doc_urls,
            "index": {"documentStore": {"docs": docs}},
        },
        ensure_ascii=False,
    )
    # Emulate mdbook: non-ASCII becomes backslash-escaped UTF-8 bytes, and
    # the single-quote/backslash that would break the JS literal are escaped.
    escaped = payload.encode("utf-8").decode("latin-1").encode("unicode_escape").decode("ascii")
    escaped = escaped.replace("'", "\\'")
    return f"window.search = Object.assign(window.search, JSON.parse('{escaped}'));\n"


def _make_book(web: Path, book: str, doc_urls: list[str], docs: dict, pages: dict[str, str]) -> None:
    book_dir = web / book
    book_dir.mkdir(parents=True, exist_ok=True)
    (book_dir / "searchindex.js").write_text(_searchindex_js(doc_urls, docs), encoding="utf-8")
    for page, html in pages.items():
        p = book_dir / page
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")


class DecodeTest(unittest.TestCase):
    def test_decode_roundtrips_unicode(self) -> None:
        js = _searchindex_js(
            ["a.html#x"],
            {"0": {"title": "Café »", "breadcrumbs": "Root » Café", "body": "naïve résumé", "id": "0"}},
        )
        data = ec.decode_searchindex(js)
        self.assertEqual(data["doc_urls"], ["a.html#x"])
        rec = data["index"]["documentStore"]["docs"]["0"]
        self.assertEqual(rec["title"], "Café »")
        self.assertEqual(rec["body"], "naïve résumé")

    def test_decode_rejects_garbage(self) -> None:
        with self.assertRaises(ValueError):
            ec.decode_searchindex("not a searchindex")


class ExtractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.web = Path(self.tmp.name) / "web"
        # Book "learn": two pages; intro.html links to api.html.
        _make_book(
            self.web,
            "learn",
            ["intro.html#introduction", "intro.html#why", "api.html#api"],
            {
                "0": {"title": "Introduction", "breadcrumbs": "Learn » Introduction", "body": "Welcome to the docs.", "id": "0"},
                "1": {"title": "Why", "breadcrumbs": "Introduction » Why", "body": "Reasons to use it.", "id": "1"},
                "2": {"title": "API", "breadcrumbs": "Learn » API", "body": "The API surface.", "id": "2"},
            },
            {
                "intro.html": '<html><body><a href="api.html#api">see API</a><a href="https://x.com">ext</a></body></html>',
                "api.html": "<html><body>no links</body></html>",
            },
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_extract_book_shape(self) -> None:
        passages = ec.extract_book("learn", self.web, "https://docs.example.com")
        self.assertEqual(len(passages), 3)
        by_id = {p.id: p for p in passages}

        intro = by_id["learn/intro.html#introduction"]
        self.assertEqual(intro.book, "learn")
        self.assertEqual(intro.page, "intro.html")
        self.assertEqual(intro.anchor, "introduction")
        self.assertEqual(intro.title, "Introduction")
        self.assertEqual(intro.breadcrumb, "Learn » Introduction")
        self.assertEqual(
            intro.url, "https://docs.example.com/documentation/learn/intro.html#introduction"
        )
        self.assertIn("Welcome to the docs.", intro.passage)
        self.assertIn("Introduction", intro.passage)

    def test_related_has_siblings_and_outbound(self) -> None:
        passages = ec.extract_book("learn", self.web, "https://docs.example.com")
        intro = next(p for p in passages if p.anchor == "introduction")
        # sibling section on the same page
        self.assertIn("learn/intro.html#why", intro.related)
        # outbound link resolves to the target page's root passage
        self.assertIn("learn/api.html#api", intro.related)
        # never includes itself
        self.assertNotIn(intro.id, intro.related)

    def test_no_embeddings_in_records(self) -> None:
        passages = ec.extract_book("learn", self.web, "https://docs.example.com")
        for p in passages:
            rec = p.to_record()
            self.assertNotIn("embedding", rec)
            # related is a JSON string, not a list
            self.assertIsInstance(rec["related"], str)
            json.loads(rec["related"])  # parses

    def test_shards_are_per_page_and_byte_stable(self) -> None:
        passages = ec.extract_book("learn", self.web, "https://docs.example.com")
        data_dir = Path(self.tmp.name) / "data"
        ec.write_shards(passages, data_dir)
        intro_shard = ec.shard_path(data_dir, "learn", "intro.html")
        api_shard = ec.shard_path(data_dir, "learn", "api.html")
        self.assertTrue(intro_shard.exists())
        self.assertTrue(api_shard.exists())

        env = json.loads(intro_shard.read_text())
        self.assertEqual(env["database"], ec.DATABASE)
        self.assertEqual(env["table"], ec.TABLE)
        self.assertEqual(len(env["records"]), 2)  # two sections on intro.html

        # Re-emitting identical input yields byte-identical shards (hash-skip).
        first = intro_shard.read_bytes()
        ec.write_shards(passages, data_dir)
        self.assertEqual(first, intro_shard.read_bytes())

    def test_manifest_outside_glob_with_version_and_id_set(self) -> None:
        passages = ec.extract_book("learn", self.web, "https://docs.example.com")
        data_dir = Path(self.tmp.name) / "data"
        ec.write_shards(passages, data_dir)
        path = ec.write_manifest(passages, data_dir, "deadbeef")
        # Manifest sits at data/ root, NOT under data/passages/.
        self.assertEqual(path.parent, data_dir)
        self.assertFalse(str(path).endswith("passages/corpus-manifest.json"))
        m = json.loads(path.read_text())
        self.assertEqual(m["corpusVersion"], "deadbeef")
        self.assertEqual(m["passageCount"], 3)
        self.assertEqual(set(m["passageIds"]), {p.id for p in passages})

    def test_content_version_is_deterministic_and_content_sensitive(self) -> None:
        passages = ec.extract_book("learn", self.web, "https://docs.example.com")
        # No git in a temp dir → deterministic content digest.
        v1 = ec.corpus_version(passages, Path(self.tmp.name))
        v2 = ec.corpus_version(passages, Path(self.tmp.name))
        self.assertEqual(v1, v2)
        self.assertTrue(v1.startswith("content-"))
        passages[0].passage += " changed"
        v3 = ec.corpus_version(passages, Path(self.tmp.name))
        self.assertNotEqual(v1, v3)

    def test_clean_removes_stale_shards(self) -> None:
        passages = ec.extract_book("learn", self.web, "https://docs.example.com")
        data_dir = Path(self.tmp.name) / "data"
        ec.write_shards(passages, data_dir)
        orphan = data_dir / "passages" / "learn" / "deleted-page.json"
        orphan.write_text("{}")
        ec.clean_passages(data_dir)
        self.assertFalse(orphan.exists())


class FakeApi:
    """In-memory stand-in for ApiClient covering list/delete/get/put."""

    def __init__(self, rows: dict[str, list[dict]]) -> None:
        self.tables = {t: {r["id"]: dict(r) for r in rs} for t, rs in rows.items()}
        self.deleted: list[tuple[str, str]] = []

    def list_ids(self, table: str) -> list[str]:
        return list(self.tables.get(table, {}).keys())

    def delete(self, table: str, rid: str) -> None:
        self.tables.get(table, {}).pop(rid, None)
        self.deleted.append((table, rid))

    def get_record(self, table: str, rid: str) -> dict | None:
        return self.tables.get(table, {}).get(rid)

    def put_record(self, table: str, record: dict) -> bool:
        self.tables.setdefault(table, {})[record["id"]] = dict(record)
        return True


class PurgeTest(unittest.TestCase):
    def test_run_sweep_deletes_only_stale(self) -> None:
        api = FakeApi(
            {
                "passage": [
                    {"id": "learn/a.html#x"},
                    {"id": "learn/b.html#y"},  # stale: not in manifest
                    {"id": "reference/c.html#z"},
                ]
            }
        )
        live = {"learn/a.html#x", "reference/c.html#z"}
        removed = pc.run_sweep(api, "v2", live, "passage", dry_run=False)
        self.assertEqual(removed, 1)
        self.assertEqual(api.deleted, [("passage", "learn/b.html#y")])
        self.assertEqual(set(api.list_ids("passage")), live)

    def test_dry_run_deletes_nothing(self) -> None:
        api = FakeApi({"passage": [{"id": "x"}, {"id": "y"}]})
        removed = pc.run_sweep(api, "v1", {"x"}, "passage", dry_run=True)
        self.assertEqual(removed, 1)
        self.assertEqual(api.deleted, [])

    def test_sweep_is_idempotent(self) -> None:
        api = FakeApi({"passage": [{"id": "x"}, {"id": "stale"}]})
        live = {"x"}
        pc.run_sweep(api, "v1", live, "passage", dry_run=False)
        # second run: nothing left to delete
        removed = pc.run_sweep(api, "v1", live, "passage", dry_run=False)
        self.assertEqual(removed, 0)

    def test_version_gate(self) -> None:
        api = FakeApi({pc.SWEEP_STATE_ROUTE: [{"id": pc.SWEEP_STATE_ID, "version": "v1"}]})
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d) / "marker"
            self.assertEqual(pc.last_swept_version(api, marker), "v1")
            pc.record_swept_version(api, marker, "v2")
            self.assertEqual(pc.last_swept_version(api, marker), "v2")
            self.assertEqual(marker.read_text(), "v2")


class RealOutputTest(unittest.TestCase):
    """If the build has produced data/, assert its real shape (ADR-028)."""

    def setUp(self) -> None:
        # source/tools/ -> app root is two levels up.
        self.app_root = Path(__file__).resolve().parents[2]
        self.data = self.app_root / "data"
        if not (self.data / "corpus-manifest.json").exists():
            self.skipTest("no built data/ — run the build first")

    def test_manifest_matches_shards(self) -> None:
        m = json.loads((self.data / "corpus-manifest.json").read_text())
        manifest_ids = set(m["passageIds"])
        shard_ids: set[str] = set()
        for shard in (self.data / "passages").rglob("*.json"):
            env = json.loads(shard.read_text())
            self.assertEqual(env["database"], ec.DATABASE)
            self.assertEqual(env["table"], ec.TABLE)
            for rec in env["records"]:
                self.assertNotIn("embedding", rec)
                for key in ("id", "book", "page", "title", "breadcrumb", "url", "passage", "related"):
                    self.assertIn(key, rec)
                self.assertTrue(rec["url"].startswith("http"))
                self.assertTrue(rec["url"].endswith(rec["anchor"]) or not rec["anchor"])
                shard_ids.add(rec["id"])
        self.assertEqual(manifest_ids, shard_ids, "manifest ID set must equal the union of shards")
        self.assertEqual(m["passageCount"], len(manifest_ids))


if __name__ == "__main__":
    unittest.main(verbosity=2)
