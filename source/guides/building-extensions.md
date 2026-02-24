# Building Extensions

Extensions add shared services to Yeti - authentication, telemetry, middleware. They compile as dylib plugins and are loaded at startup.

## Capabilities

Extensions can:
- Register **auth providers** (Basic, JWT, OAuth)
- Register **middleware** that intercepts requests
- Register **auth hooks** for custom role resolution
- Provide an **event subscriber** for tracing events
- Access **tables** for reading and writing data

## Extension Trait

```rust
use yeti_core::prelude::*;

pub struct MyExtension;

impl Extension for MyExtension {
    fn name(&self) -> &str { "my-extension" }

    fn initialize(&self) -> Result<()> {
        eprintln!("[my-extension] Initializing");
        Ok(())
    }

    fn on_ready(&self, ctx: &ExtensionContext) -> Result<()> {
        if let Some(table) = ctx.table("my-table") {
            eprintln!("[my-extension] Table available");
        }
        Ok(())
    }
}
```

## Auto-Detection

The compiler scans source files for `struct {Name}Extension` - no config field needed.

## Configuration

Mark as extension in `config.yaml`:

```yaml
name: "My Extension"
app_id: "my-extension"
extension: true
schemas:
  - schema.graphql
resources:
  - resources/*.rs
```

Apps opt in via `extensions:`:

```yaml
extensions:
  - my-extension: {}
  - yeti-auth:
      oauth:
        rules:
          - strategy: provider
            pattern: "github"
            role: standard
```

Order matters - extensions initialize and run middleware in listed order.

## Dylib Rules

The dylib boundary creates important constraints:

**Do NOT use in on_ready():**
- `tokio::spawn()` - crashes across dylib boundary
- `tracing::info!()` - messages don't reach host log (TLS isolation)
- `tokio::sync::mpsc::channel()` - channels don't work across boundary
- Host statics (`OnceLock`) - dylib has separate copies

**Safe to use:**
- `eprintln!()` - bypasses TLS isolation
- `ctx.table(name)` - Arc clones work across boundary
- `ctx.set_event_subscriber()` - host spawns after on_ready()
- Pure functions (serde, UUID generation, string ops)

**Pattern**: Set state in on_ready(), return. Host performs tokio operations after.

## Auth Providers

```rust
fn auth_providers(&self) -> Vec<Arc<dyn AuthProvider>> {
    vec![
        Arc::new(BasicAuthProvider::new()),
        Arc::new(JwtAuthProvider::new("secret".to_string())),
    ]
}

fn auth_hooks(&self) -> Vec<Arc<dyn AuthHook>> {
    vec![Arc::new(CustomRoleResolver::new())]
}
```

## Middleware

```rust
fn middleware(&self) -> Option<Arc<dyn RequestMiddleware>> {
    Some(Arc::new(RateLimiter::new(100)))
}
```

## Event Subscriber

```rust
fn on_ready(&self, ctx: &ExtensionContext) -> Result<()> {
    let log_table = ctx.table("log");
    ctx.set_event_subscriber(Box::new(MyHandler { log_table }));
    Ok(())
}
```

See [Extension Lifecycle](extension-lifecycle.md) for the full initialization sequence.

## See Also

- [Extension Lifecycle](extension-lifecycle.md) - Detailed initialization order
- [Telemetry & Observability](telemetry.md) - Event subscriber example
- [Authentication Overview](auth-overview.md) - Auth provider integration
- [Troubleshooting](troubleshooting.md) - Plugin and dylib issues
