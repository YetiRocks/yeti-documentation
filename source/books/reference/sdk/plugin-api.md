# Plugin API

Plugins provide shared capabilities across applications — authentication,
telemetry, AI inference, vector embeddings, custom middleware. They live
in `crates/plugins/` and are compiled into the binary.

## Plugin trait

Contract between the yeti binary and plugin crates. Runtime call order:
`is_required()` → `schemas()` → `resources()` → `on_ready()` →
`install_event_subscriber()` → `on_shutdown()`.

```rust,ignore
use yeti_types::plugins::Plugin;

pub trait Plugin: Send + Sync + 'static {
    /// Unique identifier (e.g., "yeti-auth").
    fn id(&self) -> &'static str;
    /// Human-readable name.
    fn name(&self) -> &'static str;

    fn version(&self) -> &'static str { "0.1.0" }

    /// Plugin IDs this plugin depends on (topological ordering).
    fn depends_on(&self) -> &[&'static str] { &[] }

    /// Whether this plugin activates given the current config.
    fn is_required(&self, ctx: &StartupContext) -> bool { true }

    /// Global plugin: loaded before user apps. Default: false.
    fn is_plugin(&self) -> bool { false }

    /// Whether registration failure aborts startup.
    fn is_critical(&self) -> bool { false }

    /// Embedded `Cargo.toml` content. Discovery extracts
    /// `[package.metadata.app]` + plugin-metadata blocks via
    /// `yeti_sdk::application::cargo_manifest`.
    fn config_toml(&self) -> Option<&'static str> { None }

    /// GraphQL schema strings. Called once during discovery, before
    /// backends exist.
    fn schemas(&self) -> Vec<&'static str> { vec![] }

    /// Register resources, hooks, web files, providers. Called once
    /// during loading, after backends exist.
    fn resources(&self, ctx: &mut RegistrationContext) -> Result<()> { Ok(()) }

    /// Post-registration setup (bootstrap data, background tasks).
    fn on_ready(&self, ctx: &Context) -> Result<()> { Ok(()) }

    /// Build the plugin's telemetry-subscriber `Service<TelemetryEvent>`,
    /// if any. Per ADR-006 this is a Tower service, not a boxed
    /// subscriber. Default: no subscriber.
    fn install_event_subscriber(
        &self,
        ctx: &Context,
    ) -> Result<Option<TelemetryService>> { Ok(None) }

    /// Called during graceful shutdown.
    fn on_shutdown(&self) {}
}
```

Only `id()` and `name()` are required. Everything else has a default.

### Minimal plugin

```rust,ignore
use yeti_sdk::prelude::*;
use yeti_types::plugins::Plugin;

pub struct MyPlugin;

impl Plugin for MyPlugin {
    fn id(&self) -> &'static str { "my-plugin" }
    fn name(&self) -> &'static str { "My Plugin" }
    fn version(&self) -> &'static str { "1.0.0" }

    fn depends_on(&self) -> &[&'static str] {
        &["yeti-auth"]
    }

    fn config_toml(&self) -> Option<&'static str> {
        Some(include_str!("../Cargo.toml"))
    }

    fn schemas(&self) -> Vec<&'static str> {
        vec![include_str!("schema.graphql")]
    }

    fn resources(&self, ctx: &mut RegistrationContext) -> Result<()> {
        ctx.add_resource(Box::new(MyResource));
        Ok(())
    }

    fn on_ready(&self, ctx: &Context) -> Result<()> {
        yeti_log!(info, "[{}] plugin ready", ctx.app_id());
        Ok(())
    }
}
```

## StartupContext

Read-only context passed to `Service::is_required()`. Determines whether a service activates based on application declarations.

```rust,ignore
pub struct StartupContext<'a> {
    pub tables: &'a [TableDefinition],
    pub app_configs: &'a [Value],
}
```

| Method | Returns | Description |
|--------|---------|-------------|
| `any_app_has_config(key)` | `bool` | Any app has a top-level config key (e.g. `"auth"`, `"vectors"`) |
| `any_table_has_field_directive(directive)` | `bool` | Any table has a field whose type matches (case-insensitive) |
| `any_app_requires_auth()` | `bool` | Any app has non-empty `requiredRoles` / `required_roles` |

```rust,ignore
fn is_required(&self, ctx: &StartupContext) -> bool {
    // Activate only if some app uses vector fields
    ctx.any_table_has_field_directive("vector")
}
```

## RegistrationContext

Mutable context passed to `Service::register()`. Collect schemas, resources, hooks, providers, and middleware. The runtime processes them after all services register.

```rust,ignore
pub struct RegistrationContext {
    pub app_id: String,
    pub root_directory: String,
    // ... internal fields populated via methods below
}
```

| Method | Argument | Description |
|--------|----------|-------------|
| `add_schema(graphql)` | `&str` | GraphQL schema string |
| `add_resource(r)` | `Box<dyn Resource>` | Resource handler |
| `add_web_files(files)` | `Vec<EmbeddedFile>` | Embedded static web files |
| `add_auth_provider(p)` | `Arc<dyn AuthProvider>` | Authentication provider |
| `add_vector_hook(h)` | `Arc<dyn VectorHook>` | Vector embedding hook |
| `add_ai_hook(h)` | `Arc<dyn AiHook>` | AI inference hook |
| `add_middleware(m)` | `Arc<dyn RequestMiddleware>` | Request middleware |
| `add_event_subscriber(s)` | `Box<dyn EventSubscriber>` | Telemetry event handler |
| `app_id()` | | Application ID |
| `root_dir()` | | Server root directory path |

```rust,ignore
fn register(&self, ctx: &mut RegistrationContext) -> Result<()> {
    // Schema
    ctx.add_schema("type User @export { id: ID, name: String, email: String }");

    // Resources
    ctx.add_resource(Box::new(LoginResource));
    ctx.add_resource(Box::new(UserResource));

    // Auth
    ctx.add_auth_provider(Arc::new(BasicAuthProvider::new()));
    ctx.add_auth_provider(Arc::new(JwtAuthProvider::new()));

    // Hooks
    ctx.add_vector_hook(Arc::new(CandleVectorHook::new()));
    ctx.add_ai_hook(Arc::new(CandleAiHook::new()));

    // Telemetry
    ctx.add_event_subscriber(Box::new(TelemetryWriter::new()));

    Ok(())
}
```

## ServiceContext

Context passed to `Service::on_ready()` after all registration completes. Tables and routes are available.

```rust,ignore
pub struct ServiceContext {
    pub app_id: String,
    pub root_directory: String,
    // ... internal lookup functions
}
```

| Method | Returns | Description |
|--------|---------|-------------|
| `table(name)` | `Option<Arc<dyn KvBackend>>` | Table backend by name |
| `require_table(name)` | `Result<Arc<dyn KvBackend>>` | Table backend or error |
| `pubsub(table_name)` | `Option<Arc<PubSubManager>>` | PubSub manager for a table |
| `set_event_subscriber(sub)` | `()` | Telemetry event handler |
| `app_id()` | `&str` | Application ID |
| `root_dir()` | `&str` | Server root directory |

```rust,ignore
fn on_ready(&self, ctx: &ServiceContext) -> Result<()> {
    // Access a table
    let users = ctx.require_table("User")?;

    // Subscribe to PubSub events
    if let Some(pubsub) = ctx.pubsub("Chat") {
        // use pubsub manager
    }

    // Register a telemetry event subscriber
    ctx.set_event_subscriber(Box::new(MySubscriber::new()));

    Ok(())
}
```

## EventSubscriber Trait

Processes telemetry events (logs, spans, metrics) in a background task. The host spawns the future after `on_ready()` returns.

```rust,ignore
pub trait EventSubscriber: Send + 'static {
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
                // {"kind": "log"|"span", "timestamp": f64, "level": "INFO", ...}
                tracing::info!("Event: {}", event);
            }
        })
    }
}
```

Channel is bounded (capacity 10,000).

## VectorHook Trait

Vector embedding generation for `@vector` schema fields. Implementations must be **sync** for dylib boundary safety.

```rust,ignore
pub trait VectorHook: Send + Sync {
    fn vectorize_fields(
        &self,
        record: Value,
        mappings: &[FieldMapping],
    ) -> Result<Value, String>;

    fn vectorize_text(&self, text: &str, model: &str) -> Result<Vec<f32>, String>;

    fn vectorize_image(&self, bytes: &[u8], model: &str) -> Result<Vec<f32>, String>;

    fn validate_model(&self, model: &str) -> Result<(), String> { Ok(()) }

    fn warmup_model(&self, model: &str, field_type: &str) -> Result<(), String> { Ok(()) }

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
    pub model: String,       // model identifier (e.g., "BAAI/bge-small-en-v1.5")
    pub field_type: String,  // "text" (default) or "image"
}
```

## AiHook Trait

Local LLM inference. Implementations must be **sync** for dylib boundary safety.

```rust,ignore
pub trait AiHook: Send + Sync {
    /// Single-turn text completion.
    fn complete(&self, prompt: &str, max_tokens: u32) -> Result<String, String>;

    /// Multi-turn chat completion.
    fn chat(
        &self,
        messages: &[(&str, &str)],
        max_tokens: u32,
    ) -> Result<String, String>;

    /// Structured JSON output.
    fn complete_json(
        &self,
        prompt: &str,
        max_tokens: u32,
    ) -> Result<Value, String>;

    /// List available models.
    fn models(&self) -> Vec<ModelInfo>;

    /// Check if a specific model is loaded.
    fn is_loaded(&self, model: &str) -> bool;
}
```

`ModelInfo` describes an available model:

```rust,ignore
pub struct ModelInfo {
    pub id: String,
    pub name: String,
    pub parameters: String,    // "8B", "3B"
    pub quantization: String,  // "Q4_K_M", "F16"
    pub loaded: bool,
    pub memory_bytes: u64,
}
```

## AuthHook Trait

Overrides role resolution before default logic. Return `Some(access)` to override, `None` to fall through.

```rust,ignore
pub trait AuthHook: Send + Sync {
    async fn on_resolve_role(
        &self,
        identity: &AuthIdentity,
        ctx: &Context,
    ) -> Option<Arc<dyn AccessControl>>;
}
```

## ComputedFieldHook Trait

Resolves virtual field values at read time. Fields are `(name, type)` pairs from the schema.

```rust,ignore
#[async_trait]
pub trait ComputedFieldHook: Send + Sync {
    async fn resolve(
        &self,
        record: Value,
        fields: &[(String, String)],
    ) -> Result<Value, String>;
}
```

## Lifecycle Order

1. `Service::is_required(StartupContext)` -- decide activation
2. Services sorted by `depends_on()` (topological order)
3. `Service::register(RegistrationContext)` -- schemas, resources, hooks
4. Tables and routes created from registered schemas
5. `Service::on_ready(ServiceContext)` -- bootstrap data, background tasks
6. Event subscribers spawned
7. Server starts accepting requests
8. `Service::on_shutdown()` on graceful shutdown

Telemetry services sort first so their event subscriber captures other services' startup logs.

## Minimal Service Example

```rust,ignore
use yeti_sdk::prelude::*;

pub struct HealthCheck;

impl Service for HealthCheck {
    fn id(&self) -> &'static str { "health-check" }
    fn name(&self) -> &'static str { "Health Check" }

    fn register(&self, _ctx: &mut RegistrationContext) -> Result<()> {
        Ok(())
    }

    fn on_ready(&self, _ctx: &ServiceContext) -> Result<()> {
        tracing::info!("Health check service ready");
        Ok(())
    }
}
```
