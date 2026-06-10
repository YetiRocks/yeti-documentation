#!/usr/bin/env python3
"""Corpus-versioned purge sweep (ADR-028 §5).

After the seed load + vector backfill, renamed or deleted pages leave stale
Passage rows (and stale HNSW entries) behind: the data loader upserts by
primary key but never tombstones. This sweep reconciles the live table
against `data/corpus-manifest.json` — the build's authoritative live
passage-ID set — and deletes every Passage row whose ID is absent from the
manifest.

The manifest also carries the corpus version (docs git SHA). The sweep is
gated on a version change by default: it records the last-swept version in
the `CorpusSweep` table and skips when the version is unchanged, so a plain
restart costs nothing. `--force` runs the reconciliation regardless.

Reconciliation is idempotent: deleting IDs already gone is a no-op, and the
manifest is the single source of truth, so re-running converges.

Usage:
    python3 tools/purge-corpus.py \
        --base https://localhost:9996 \
        --route documentation \
        [--manifest ../data/corpus-manifest.json] \
        [--force] [--dry-run] [--insecure]

Exit status is non-zero on transport/parse failure so a deploy step can fail
loudly. Pure standard library — no third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Route segment for the sweep-state record. Stored in the same database as
# Passage so it travels with the app; the table is created lazily on write
# only if the docs app declares it. Falls back to a local marker file when
# the table is unavailable.
SWEEP_STATE_ROUTE = "corpussweep"
SWEEP_STATE_ID = "passage-corpus"


def log(msg: str) -> None:
    print(f"[purge-corpus] {msg}", file=sys.stderr)


class ApiClient:
    """Minimal yeti REST client for list/delete over the app's table route."""

    def __init__(self, base: str, route: str, insecure: bool, timeout: int = 60) -> None:
        self.base = base.rstrip("/")
        self.route = route.strip("/")
        self.timeout = timeout
        self.ctx: ssl.SSLContext | None = None
        if insecure:
            self.ctx = ssl.create_default_context()
            self.ctx.check_hostname = False
            self.ctx.verify_mode = ssl.CERT_NONE

    def _url(self, table: str, suffix: str = "", query: dict | None = None) -> str:
        url = f"{self.base}/{self.route}/{table}"
        if suffix:
            url = f"{url}/{urllib.parse.quote(suffix, safe='')}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"
        return url

    def _request(self, method: str, url: str) -> tuple[int, bytes]:
        req = urllib.request.Request(url, method=method)
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def list_ids(self, table: str) -> list[str]:
        """Return all primary-key IDs in a table, paging defensively."""
        ids: list[str] = []
        offset = 0
        page = 1000
        while True:
            status, body = self._request(
                "GET", self._url(table, query={"limit": page, "offset": offset})
            )
            if status == 404:
                # Table not present yet (nothing seeded) — nothing to purge.
                return ids
            if status >= 400:
                raise RuntimeError(f"list {table} failed: HTTP {status}: {body[:200]!r}")
            rows = json.loads(body) if body.strip() else []
            if isinstance(rows, dict):
                rows = rows.get("records", rows.get("data", []))
            if not rows:
                break
            for r in rows:
                rid = r.get("id")
                if rid is not None:
                    ids.append(rid)
            if len(rows) < page:
                break
            offset += page
        return ids

    def delete(self, table: str, rid: str) -> None:
        status, body = self._request("DELETE", self._url(table, rid))
        if status >= 400 and status != 404:
            raise RuntimeError(f"delete {table}/{rid} failed: HTTP {status}: {body[:200]!r}")

    def get_record(self, table: str, rid: str) -> dict | None:
        status, body = self._request("GET", self._url(table, rid))
        if status == 404:
            return None
        if status >= 400:
            return None
        return json.loads(body) if body.strip() else None

    def put_record(self, table: str, record: dict) -> bool:
        url = self._url(table, record["id"])
        data = json.dumps(record).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="PUT")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                return resp.status < 400
        except urllib.error.HTTPError:
            return False


def load_manifest(path: Path) -> tuple[str, set[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    version = data["corpusVersion"]
    ids = set(data["passageIds"])
    if data.get("passageCount", len(ids)) != len(ids):
        raise ValueError("manifest passageCount disagrees with passageIds length")
    return version, ids


def read_local_marker(marker: Path) -> str | None:
    return marker.read_text(encoding="utf-8").strip() if marker.exists() else None


def write_local_marker(marker: Path, version: str) -> None:
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(version, encoding="utf-8")


def last_swept_version(client: ApiClient, marker: Path) -> str | None:
    rec = client.get_record(SWEEP_STATE_ROUTE, SWEEP_STATE_ID)
    if rec and rec.get("version"):
        return rec["version"]
    return read_local_marker(marker)


def record_swept_version(client: ApiClient, marker: Path, version: str) -> None:
    # Best-effort: persist into the platform if a CorpusSweep table exists,
    # always persist the local marker so a re-run short-circuits.
    client.put_record(
        SWEEP_STATE_ROUTE,
        {"id": SWEEP_STATE_ID, "version": version},
    )
    write_local_marker(marker, version)


def run_sweep(
    client: ApiClient,
    manifest_version: str,
    live_ids: set[str],
    table: str,
    dry_run: bool,
) -> int:
    """Delete Passage rows absent from the manifest. Returns count removed."""
    current = client.list_ids(table)
    stale = sorted(set(current) - live_ids)
    log(f"table has {len(current)} rows; manifest declares {len(live_ids)}; {len(stale)} stale")
    if dry_run:
        for sid in stale:
            log(f"DRY-RUN would delete: {sid}")
        return len(stale)
    for sid in stale:
        client.delete(table, sid)
    if stale:
        log(f"deleted {len(stale)} stale passages")
    return len(stale)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Corpus-versioned purge sweep (ADR-028 §5).")
    parser.add_argument(
        "--base",
        default=os.environ.get("YETI_BASE_URL", "https://localhost:9996"),
        help="yeti base URL (default: $YETI_BASE_URL or https://localhost:9996)",
    )
    parser.add_argument(
        "--route",
        default=os.environ.get("DOCS_APP_ROUTE", "documentation"),
        help="docs app route prefix (default: $DOCS_APP_ROUTE or documentation)",
    )
    parser.add_argument("--table", default="passage", help="passage table route segment")
    parser.add_argument("--manifest", default="../data/corpus-manifest.json")
    parser.add_argument(
        "--marker",
        default="../data/.corpus-swept-version",
        help="local last-swept-version marker",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="run the sweep even when the corpus version is unchanged",
    )
    parser.add_argument("--dry-run", action="store_true", help="report stale rows, delete nothing")
    parser.add_argument("--insecure", action="store_true", help="skip TLS verification (self-signed)")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        log(f"ERROR: manifest not found: {manifest_path}")
        return 1
    version, live_ids = load_manifest(manifest_path)
    log(f"manifest version {version}, {len(live_ids)} live passages")

    client = ApiClient(args.base, args.route, args.insecure)
    marker = Path(args.marker)

    if not args.force:
        last = last_swept_version(client, marker)
        if last == version:
            log(f"corpus version unchanged ({version}); skipping sweep (use --force to override)")
            return 0
        log(f"corpus version advanced: {last} -> {version}; sweeping")

    try:
        run_sweep(client, version, live_ids, args.table, args.dry_run)
    except (RuntimeError, urllib.error.URLError, OSError) as e:
        log(f"ERROR: sweep failed: {e}")
        return 1

    if not args.dry_run:
        record_swept_version(client, marker, version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
