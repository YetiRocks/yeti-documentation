#!/usr/bin/env bash
# Build the three mdBooks (learn / guides / reference) plus the docs-corpus.
#
# Mount-agnostic, multi-book asset resolution.
# ---------------------------------------------
# The Yeti web server serves this app under a mount (locally `/documentation/`)
# and injects `<base href="{mount}/">` as the first child of <head>, stripping
# any author <base> (see yeti-http `html_base::inject_base`). Every relative
# asset/nav ref in the served HTML therefore resolves against that single mount
# base — NOT against the page's own directory.
#
# Each book, however, is served one level below the mount, at
# `{mount}/{book}/`. Stock mdBook emits PAGE-relative asset refs via
# `{{ path_to_root }}` (which points at the book root relative to the current
# page). Under the injected mount base those refs collapse to `{mount}/theme/…`
# and 404 — the book slug is missing.
#
# Fix: render each book with a per-book theme in which `{{ path_to_root }}` (and
# the `additional_css/js` loop's `{{ ../path_to_root }}`) is rewritten to the
# base-relative book root `{book}/`. Resolved against the injected
# `<base href="{mount}/">` that yields `{mount}/{book}/…` at ANY mount, for
# pages at ANY depth (the substitution is a fixed string, independent of page
# depth). The bundle stays mount-agnostic: only the book slug is baked, which is
# intrinsic to the site structure, not to the mount.
set -euo pipefail

for book in learn guides reference; do
  theme_tmp="$(mktemp -d)"
  cp -R theme/. "$theme_tmp/"
  # Base-relative book-root prefix, immune to the mount-root <base> injection.
  sed -i.bak \
    -e "s#{{ ../path_to_root }}#${book}/#g" \
    -e "s#{{ path_to_root }}#${book}/#g" \
    "$theme_tmp/index.hbs"
  rm -f "$theme_tmp/index.hbs.bak"
  (
    cd "books/$book"
    MDBOOK_OUTPUT__HTML__SITE_URL="/documentation/$book/" \
    MDBOOK_OUTPUT__HTML__THEME="$theme_tmp" \
      mdbook build
  )
  rm -rf "$theme_tmp"
done

mkdir -p ../web/assets
cp assets/*.svg assets/*.png ../web/assets/
cp books/index.html ../web/index.html
cp books/404.html ../web/404.html
python3 tools/extract_corpus.py --source ..
