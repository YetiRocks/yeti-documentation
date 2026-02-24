# Troubleshooting

## Plugin Compilation

**Plugin won't compile**

Check the compiler output in the terminal. Common causes:

- Missing `use yeti_core::prelude::*;` at top of resource file
- Syntax error in `schema.graphql` (mismatched braces, missing `@primaryKey`)
- Bad dependency version in `config.yaml` `dependencies:` section

**Source changes aren't taking effect**

The compiler caches source at `cache/builds/{app}/src/`. Clear it:

```bash
rm -rf ~/yeti/cache/builds/{app}/src/
```

**Segfault on startup (no panic, no backtrace)**

Stale `.dylib` files from a previous yeti-core build. Clear the plugin cache:

```bash
rm -rf ~/yeti/cache/builds/*/target/
```

Always clear after `cargo clean` or rebuilding yeti-core.

## Dylib Boundary

These issues only affect custom resources and extensions (code compiled as dynamic libraries).

**`tokio::spawn` crashes with "cannot catch foreign exceptions"**

`tokio::spawn()` cannot be called from dylib code. Use `futures::stream::unfold` instead of spawn+channel patterns. For event subscribers, use `ctx.set_event_subscriber()` and let the host spawn after `on_ready()` returns.

**`tracing::info!()` produces no output**

Tracing macros use thread-local storage, which is duplicated in the dylib. Messages go to the dylib's subscriber, not the host's. Use `eprintln!()` for debug output from plugins.

**Host statics have wrong values**

`OnceLock` and other statics in yeti-core are duplicated in the dylib. The host's copy and the dylib's copy are independent. Use dylib-local statics for state shared between an extension and its resources.

**Methods on host types don't work as expected**

Methods defined on host-compiled structs (like `ExtensionContext`) run in dylib context when called from dylib code. The dylib has its own compiled copy. Creating tokio channels or futures in such methods silently corrupts the host runtime. Fix: set flags in dylib, let the host check flags after `on_ready()` returns.

**`reqwest::blocking::Client` crashes**

Reqwest's blocking client creates an internal tokio runtime that conflicts with the dylib boundary. This crashes in async handlers AND in `std::thread::spawn` threads. For table access, use `ctx.get_table("Name")?.scan_all().await?`. For external HTTP, use `std::process::Command` to call `curl`.

## Networking & TLS

**`curl: (60) SSL certificate problem`**

Development server uses self-signed certificates. Always use `-sk` flags:

```bash
curl -sk https://localhost:9996/health
```

**Connection refused on port 9996**

Check that the server is running and the port matches `yeti-config.yaml`:

```yaml
http:
  port: 9996
```

**Operations API not responding**

The Operations API runs on a separate port (default 9995) over plain HTTP:

```bash
curl -X POST http://localhost:9995/ -d '{"operation":"list_apps"}'
```

## Data & Queries

**`GET /{app}/{Table}` returns schema, not records**

Add `?limit=N` to list records:

```bash
curl -sk "https://localhost:9996/my-app/Product?limit=100"
```

Plain `GET /{app}/{Table}` without query parameters returns table metadata.

**FIQL filter returns empty results**

Check that the filtered field has `@indexed` in the schema. Non-indexed fields can't be filtered with FIQL.

**Seed data not loading**

Seed data loads once when the table is empty. If the table already has records, seed data is skipped. To reload, delete all records first or clear the database directory.

## General

**App not detected on startup**

Yeti scans `~/yeti/applications/*/config.yaml`. Check that:

- The directory is directly under `applications/` (not nested)
- `config.yaml` exists and is valid YAML
- `enabled: true` is set (or not set to `false`)

**`@export` table has no REST endpoints**

Tables need `@export(rest: true)` in the schema AND `rest: true` in `config.yaml`. Both are required.

**Database lock errors in tests**

```bash
rm -rf /tmp/yeti-test-*
```
