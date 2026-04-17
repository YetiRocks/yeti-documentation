# Plugin System & Hot Reload

Custom resources compile into dynamic libraries (dylibs) loaded at runtime.

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
cache/builds/target/release/lib{app}.dylib
```

Fresh builds take ~2 minutes per plugin. Cached rebuilds take ~10 seconds.

## Hot Reload

Filesystem watchers monitor dylib files:

1. Watcher detects change in `cache/builds/target/`
2. New dylib copied to temp file (forces OS to load fresh copy)
3. Plugin loaded, AutoRouter updated with new handlers
4. Old dylib unloaded

Application-level hot reload also watches `applications/` for new or removed apps.

## Plugin Source Cache

The compiler copies source to `cache/builds/{app}/src/` before building. See [Troubleshooting](../guides/troubleshooting.md) for cache-clearing instructions when changes are not taking effect.

## Dylib Boundary Rules

Dynamic libraries get separate copies of all static data, creating hard constraints:

**Do not:**
- Call `tokio::spawn()` (crashes with "cannot catch foreign exceptions")
- Use `eprintln!()` (never reaches structured output)
- Create tokio channels/futures in methods called from dylib context

**Instead:**
- `futures::stream::unfold` instead of spawn+channel patterns
- `tracing` macros for logging (output may not reach the host subscriber due to TLS isolation, but tracing is the correct interface)
- Flag-based patterns: dylib sets flags, host checks after `on_ready()` returns

## Service Plugins

User-defined services follow the same pipeline. The compiler auto-detects service types by scanning for `struct {Type}Extension`.

```yaml
extension: true
```
