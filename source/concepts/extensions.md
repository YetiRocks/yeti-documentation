# Extensions

Extensions provide shared services to multiple applications. An extension makes its capabilities - auth, telemetry, middleware - available to any app that opts in.

## Built-in Extensions

| Extension | Purpose |
|-----------|---------|
| **yeti-auth** | Authentication (Basic, JWT, OAuth) and role-based access control |
| **yeti-telemetry** | Log collection, span tracing, metrics, and a real-time dashboard |

Both are standard Yeti applications with `extension: true`. You can disable, replace, or supplement them.

## Creating an Extension

Set `extension: true` in config and include a struct implementing the `Extension` trait:

```yaml
name: "My Extension"
app_id: "my-extension"
version: "1.0.0"
enabled: true
extension: true
schemas:
  - schema.graphql
resources:
  - resources/*.rs
```

```rust
use yeti_core::prelude::*;

pub struct MyServiceExtension;

impl Extension for MyServiceExtension {
    fn name(&self) -> &str { "my-service" }

    fn initialize(&self) -> Result<()> {
        eprintln!("[my-service] Extension initialized");
        Ok(())
    }

    fn on_ready(&self, ctx: &ExtensionContext) -> Result<()> {
        if let Some(table) = ctx.table("config") {
            eprintln!("[my-service] Config table available");
        }
        Ok(())
    }
}
```

The compiler auto-detects the extension type by scanning for `struct {Type}Extension`.

## Extension Trait

```rust
pub trait Extension: Send + Sync {
    fn name(&self) -> &str;
    fn initialize(&self) -> Result<()> { Ok(()) }
    fn middleware(&self) -> Option<Arc<dyn RequestMiddleware>> { None }
    fn auth_providers(&self) -> Vec<Arc<dyn AuthProvider>> { Vec::new() }
    fn auth_hooks(&self) -> Vec<Arc<dyn AuthHook>> { Vec::new() }
    fn on_ready(&self, ctx: &ExtensionContext) -> Result<()> { Ok(()) }
}
```

## ExtensionContext

| Method | Purpose |
|--------|---------|
| `ctx.table("name")` | Get an `Arc<TableResource>` by name |
| `ctx.root_dir()` | Root directory path |
| `ctx.auto_router()` | Host-side table lookup |
| `ctx.set_event_subscriber(sub)` | Register a telemetry event handler |

## Consumer Configuration

Apps opt in via `extensions:` in config.yaml with optional inline config:

```yaml
extensions:
  - yeti-auth:
      oauth:
        default_role: "viewer"
        rules:
          - strategy: provider
            pattern: "google"
            role: admin
          - strategy: email
            pattern: "*@corp.com"
            role: standard
```

Per-app config is accessible via `ctx.extension_config("yeti-auth")`.

## Lifecycle

1. Extensions are identified during app scanning
2. Extension dylibs compile and load before regular apps
3. `initialize()` called at registration
4. Extension tables and resources registered
5. `on_ready()` called after routes/tables are in place
6. Declared extensions' tables and auth providers merge into consuming apps

## Dylib Boundary Rules

Extensions compile as dynamic libraries with these constraints:

- **No `tokio::spawn`** - Spawning tasks corrupts the host runtime. Use `set_event_subscriber()` for background work.
- **No `tracing::info!`** - Lost due to TLS isolation. Use `eprintln!` instead.
- **No host statics** - `OnceLock` statics are duplicated in the dylib. Use dylib-local statics.
- **Flag-based patterns** - Set flags in `on_ready()`, let the host check them after the call returns.
