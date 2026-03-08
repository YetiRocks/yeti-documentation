# Extension API

Extensions provide shared services across applications: authentication, telemetry, vector search, and custom middleware.

## Extension Trait

```rust,ignore
use yeti_sdk::prelude::*;

pub struct MyExtension;

impl Extension for MyExtension {
    fn name(&self) -> &str {
        "my-extension"
    }

    fn initialize(&self) -> Result<()> {
        // Called once at load time. Set up static state here.
        Ok(())
    }

    fn on_ready(&self, ctx: ExtensionContext) -> Result<()> {
        // Called after routes and tables are registered.
        // Access tables, set event subscribers, register hooks.
        let table = ctx.table("Config")?;
        Ok(())
    }

    fn on_shutdown(&self) {
        // Called during graceful shutdown. Clean up resources.
    }

    fn middleware(&self) -> Option<Arc<dyn RequestMiddleware>> {
        // Return request middleware (runs before every request)
        None
    }

    fn auth_providers(&self) -> Vec<Arc<dyn AuthProvider>> {
        // Return authentication providers (Basic, JWT, OAuth)
        vec![]
    }

    fn auth_hooks(&self) -> Vec<Arc<dyn AuthHook>> {
        // Override role resolution before default logic
        vec![]
    }

    fn vector_hooks(&self) -> Vec<Arc<dyn VectorHook>> {
        // Provide vector embedding generation
        vec![]
    }
}
```

All methods except `name()` have default no-op implementations.

## ExtensionContext

Available in `on_ready()`:

```rust,ignore
fn on_ready(&self, ctx: ExtensionContext) -> Result<()> {
    // Access a table
    let config_table = ctx.table("Config")?;

    // Root directory path
    let root: &Path = ctx.root_dir();

    // Get the auto-router for registering custom routes
    let router = ctx.auto_router();

    // Set an event subscriber for telemetry events
    ctx.set_event_subscriber(Box::new(MySubscriber::new()));

    Ok(())
}
```

| Method | Returns | Description |
|--------|---------|-------------|
| `table(name)` | `Result<Arc<TableResource>>` | Named table reference |
| `root_dir()` | `&Path` | Server root directory |
| `auto_router()` | `&AutoRouter` | Route registration |
| `set_event_subscriber(sub)` | `()` | Register telemetry event handler |

## EventSubscriber Trait

Process telemetry events (logs, spans, metrics) in a background task:

```rust,ignore
use yeti_sdk::prelude::*;

pub struct MySubscriber;

impl EventSubscriber for MySubscriber {
    fn run(
        self: Box<Self>,
        rx: mpsc::Receiver<Value>,
    ) -> Pin<Box<dyn Future<Output = ()> + Send>> {
        Box::pin(async move {
            while let Ok(event) = rx.recv().await {
                // Process event JSON
                // {"kind": "log"|"span", "timestamp": f64, "level": "INFO", ...}
                eprintln!("Event: {}", event);
            }
        })
    }
}
```

The channel is bounded (capacity 10,000). The host spawns the future after `on_ready()` returns.

## export_extension!

Register the extension for the plugin system:

```rust,ignore
export_extension!(MyExtension);
```

Place this at module level alongside `export_plugin!()`.

## Lifecycle Order

1. Plugin `.dylib` loaded
2. `Extension::initialize()` called
3. Tables and routes registered
4. `Extension::on_ready(ctx)` called
5. Event subscriber spawned (if set)
6. Server starts accepting requests
7. `Extension::on_shutdown()` called during graceful shutdown

## Important Constraints

These apply to all code running in dylib context (extensions and resources):

- **No `tracing::info!`** -- use `eprintln!` or `yeti_log!` instead (TLS isolation)
- **No `tokio::spawn`** -- causes crashes ("cannot catch foreign exceptions"). Use `futures::stream::unfold` for async patterns
- **No `reqwest::blocking::Client`** -- crashes due to internal tokio runtime conflict. Use `ctx.table()` for data access or `curl_request()` for external HTTP
- **No host statics** -- `OnceLock` values in yeti-core are duplicated in dylib. Use dylib-local statics
- **Flag-based patterns** -- set flags in dylib code, let the host check them after `on_ready()` returns for any tokio operations

## Minimal Extension Example

```rust,ignore
use yeti_sdk::prelude::*;

pub struct HealthCheckExtension;

impl Extension for HealthCheckExtension {
    fn name(&self) -> &str { "health-check" }

    fn on_ready(&self, ctx: ExtensionContext) -> Result<()> {
        yeti_log!(info, "Health check extension ready");
        Ok(())
    }
}

export_extension!(HealthCheckExtension);
export_plugin!();  // No resources, extension only
```
