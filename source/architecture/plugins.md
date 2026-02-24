# Plugin System & Hot Reload

Yeti compiles custom resources into dynamic libraries (dylibs) loaded at runtime.

## Compilation Pipeline

```
config.yaml + schema.graphql + resources/*.rs
        │
ApplicationCompiler
  1. Copy resource files to cache/builds/{app}/src/
  2. Generate Cargo.toml (with dependencies from config)
  3. Generate lib.rs (scans source for types)
  4. cargo build --release -> .dylib
        │
cache/builds/{app}/target/release/lib{app}.dylib
```

Fresh builds take ~2 minutes per plugin (pre-built RocksDB avoids 65s C++ compilation). Cached rebuilds take ~10 seconds.

## Hot Reload

Yeti monitors dylib files with filesystem watchers:

1. Watcher detects change in `cache/builds/{app}/target/`
2. New dylib copied to temp file (forces OS to load fresh copy)
3. Plugin loaded, AutoRouter updated with new handlers
4. Old dylib unloaded

Application-level hot reload also watches `applications/` for new or removed apps.

## Plugin Source Cache

The compiler copies source to `cache/builds/{app}/src/` before building. Clear the cache when changes aren't taking effect:

```bash
rm -rf ~/yeti/cache/builds/{app}/src/
rm -rf ~/yeti/cache/builds/{app}/target/
```

## Dylib Boundary Rules

Dynamic libraries get separate copies of all static data, creating critical constraints:

**Do not:**
- Call `tokio::spawn()` from dylib code (crashes with "cannot catch foreign exceptions")
- Use `tracing::info!()` etc. (doesn't reach host log due to TLS isolation)
- Create tokio channels/futures in methods called from dylib context

**Instead:**
- Use `futures::stream::unfold` instead of spawn+channel patterns
- Use `eprintln!()` for debug output
- Use flag-based patterns: dylib sets flags, host checks after `on_ready()` returns

## Extension Plugins

Extensions follow the same pipeline but provide shared services. The compiler auto-detects extension types by scanning source for `struct {Type}Extension`.

```yaml
extension: true
```
