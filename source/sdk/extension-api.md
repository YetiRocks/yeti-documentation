# Extension API

Extensions provide shared services across applications: authentication, telemetry, vector search, and custom middleware.

## Extension Trait

```rust,ignore
pub trait Extension: Send + Sync {
    fn name(&self) -> &str;

    fn on_ready(&self, ctx: ExtensionContext) -> Result<()> {
        Ok(())
    }

    fn middleware(&self) -> Option<Arc<dyn RequestMiddleware>> {
        None
    }

    fn auth_providers(&self) -> Vec<Arc<dyn AuthProvider>> {
        vec![]
    }

    fn auth_hooks(&self) -> Vec<Arc<dyn AuthHook>> {
        vec![]
    }

    fn vector_hooks(&self) -> Vec<Arc<dyn VectorHook>> {
        vec![]
    }
}
```

All methods except `name()` have default no-op implementations. Implement only what you need.

### Full example

```rust,ignore
use yeti_sdk::prelude::*;

pub struct MyExtension;

impl Extension for MyExtension {
    fn name(&self) -> &str {
        "my-extension"
    }

    fn on_ready(&self, ctx: ExtensionContext) -> Result<()> {
        let config_table = ctx.table("Config")?;
        yeti_log!(info, "Extension ready, config table loaded");
        Ok(())
    }

    fn middleware(&self) -> Option<Arc<dyn RequestMiddleware>> {
        None  // return Some(...) to intercept every request
    }

    fn auth_providers(&self) -> Vec<Arc<dyn AuthProvider>> {
        vec![]  // return providers for Basic, JWT, OAuth auth
    }

    fn auth_hooks(&self) -> Vec<Arc<dyn AuthHook>> {
        vec![]  // override role resolution before default logic
    }

    fn vector_hooks(&self) -> Vec<Arc<dyn VectorHook>> {
        vec![]  // provide vector embedding generation
    }
}
```

## ExtensionContext

Available in `on_ready()`. Provides access to tables, filesystem, routing, and event subscribers.

```rust,ignore
impl ExtensionContext {
    fn table(&self, name: &str) -> Result<Arc<TableResource>>
    fn root_dir(&self) -> &Path
    fn auto_router(&self) -> &AutoRouter
    fn set_event_subscriber(&self, sub: Box<dyn EventSubscriber>)
    fn pubsub(&self, table: &str) -> Option<Arc<PubSubManager>>
}
```

| Method | Returns | Description |
|--------|---------|-------------|
| `table(name)` | `Result<Arc<TableResource>>` | Named table reference |
| `root_dir()` | `&Path` | Server root directory |
| `auto_router()` | `&AutoRouter` | Route registration |
| `set_event_subscriber(sub)` | `()` | Register telemetry event handler |
| `pubsub(table)` | `Option<Arc<PubSubManager>>` | PubSub manager for a table |

```rust,ignore
fn on_ready(&self, ctx: ExtensionContext) -> Result<()> {
    // Access a table
    let config = ctx.table("Config")?;

    // Root directory
    let root: &Path = ctx.root_dir();

    // Register a telemetry event subscriber
    ctx.set_event_subscriber(Box::new(MySubscriber::new()));

    Ok(())
}
```

## EventSubscriber Trait

Process telemetry events (logs, spans, metrics) in a background task.

```rust,ignore
pub trait EventSubscriber: Send {
    fn run(
        self: Box<Self>,
        rx: mpsc::Receiver<Value>,
    ) -> Pin<Box<dyn Future<Output = ()> + Send>>;
}
```

```rust,ignore
pub struct MySubscriber;

impl EventSubscriber for MySubscriber {
    fn run(
        self: Box<Self>,
        rx: mpsc::Receiver<Value>,
    ) -> Pin<Box<dyn Future<Output = ()> + Send>> {
        Box::pin(async move {
            while let Ok(event) = rx.recv().await {
                // Event format:
                // {"kind": "log"|"span", "timestamp": f64, "level": "INFO", ...}
                tracing::info!("Event: {}", event);
            }
        })
    }
}
```

The channel is bounded (capacity 10,000). The host spawns the future after `on_ready()` returns.

## VectorHook Trait

Provide vector embedding generation for `@vector` schema fields. Implementations must be **sync** (not async) for dylib boundary safety.

```rust,ignore
pub trait VectorHook: Send + Sync {
    fn vectorize_fields(
        &self,
        record: Value,
        mappings: &[FieldMapping],
    ) -> Result<Value, String>;

    fn vectorize_text(&self, text: &str, model: &str) -> Result<Vec<f32>, String>;

    fn vectorize_image(&self, bytes: &[u8], model: &str) -> Result<Vec<f32>, String>;

    fn validate_model(&self, model: &str) -> Result<(), String> {
        Ok(())
    }

    fn warmup_model(&self, model: &str, field_type: &str) -> Result<(), String> {
        Ok(())
    }

    fn vectorize_fields_batch(
        &self,
        records: Vec<Value>,
        mappings: &[FieldMapping],
    ) -> Result<Vec<Value>, String>;
}
```

`FieldMapping` describes the source-to-target mapping:

```rust,ignore
pub struct FieldMapping {
    pub source: String,      // source field name
    pub target: String,      // target vector field name
    pub model: String,       // model identifier
    pub field_type: String,  // "text" (default) or "image"
}
```

## AuthHook Trait

Override role resolution before the default logic runs. Useful for custom role assignment based on request context.

## PubSub

Topic-based publish/subscribe for real-time messaging.

```rust,ignore
pub struct PubSubManager {
    // ...
}

impl PubSubManager {
    pub fn new(capacity: usize) -> Self;
    pub async fn subscribe(&self, topic: &str) -> broadcast::Receiver<SubscriptionMessage>;
    pub async fn publish(&self, topic: &str, message: SubscriptionMessage);
    pub async fn notify_update(&self, table: &str, id: &str, data: &Value);
    pub async fn notify_delete(&self, table: &str, id: &str);
    pub async fn notify_create(&self, table: &str, id: &str, data: &Value);
}
```

```rust,ignore
// In on_ready():
let pubsub = ctx.pubsub("Chat").unwrap();
let mut receiver = pubsub.subscribe("Chat/room-1").await;

// Publishing
pubsub.notify_create("Chat", "msg-1", &json!({"text": "Hello"})).await;
```

## export_extension!

Register the extension for the plugin system:

```rust,ignore
export_extension!(MyExtension);
```

Place this at module level alongside `export_plugin!()`.

## Lifecycle Order

1. Plugin `.dylib` loaded
2. Tables and routes registered
3. `Extension::on_ready(ctx)` called
4. Event subscriber spawned (if set via `ctx.set_event_subscriber()`)
5. Server starts accepting requests
6. Graceful shutdown

Telemetry extensions are sorted first in `load_extensions` so their event subscriber captures other extensions' startup.

## Dylib Constraints

These apply to all code running in dylib context (extensions and resources):

| Constraint | Why | Alternative |
|-----------|-----|-------------|
| No `tracing::info!` | TLS isolation between host and dylib | `yeti_log!` or tracing macros (`tracing::info!`, `tracing::warn!`, etc.) for consistent API, even in dylib context |
| No `tokio::spawn` | Crashes: "cannot catch foreign exceptions" | `futures::stream::unfold` |
| No `reqwest::blocking::Client` | Internal tokio runtime conflict causes crash | `fetch()` |
| No host statics | `OnceLock` in yeti-core is duplicated in dylib | Dylib-local statics |
| No tokio channels/futures in host methods | Methods on host types run in dylib context when called from dylib | Flag-based patterns: set flags in dylib, host checks after `on_ready()` |

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
