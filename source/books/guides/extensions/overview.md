# Building Services

Services (formerly "extensions") add shared capabilities to Yeti -- authentication, telemetry, AI, Kafka bridging. Each service implements the `Service` trait from `yeti-types` and is compiled into the binary.

## The Service Trait

```rust,ignore
pub trait Service: Send + Sync + 'static {
    /// Unique identifier (e.g., "yeti-auth").
    fn id(&self) -> &'static str;
    /// Human-readable name.
    fn name(&self) -> &'static str;
    /// Semantic version.
    fn version(&self) -> &'static str { "0.1.0" }
    /// Service IDs this service depends on (for topological ordering).
    fn depends_on(&self) -> &[&'static str] { &[] }
    /// Whether this service should activate given the current config.
    fn is_required(&self, ctx: &StartupContext) -> bool { true }
    /// Register schemas, resources, hooks, and providers.
    fn register(&self, ctx: &mut RegistrationContext) -> Result<()>;
    /// Post-registration setup (bootstrap data, background tasks).
    fn on_ready(&self, ctx: &ServiceContext) -> Result<()> { Ok(()) }
    /// Whether this is a global extension (loaded before user apps).
    fn is_extension(&self) -> bool { false }
    /// Whether registration failure should abort startup.
    fn is_critical(&self) -> bool { false }
    /// Embedded config.yaml content.
    fn config_yaml(&self) -> Option<&'static str> { None }
    /// Called during graceful shutdown.
    fn on_shutdown(&self) {}
}
```

## Lifecycle

The runtime calls methods in this order:

1. **`is_required(StartupContext)`** -- Decide whether to activate. Inspect tables, app configs, schema directives.
2. **`register(RegistrationContext)`** -- Add schemas, resources, auth providers, hooks, middleware, event subscribers.
3. **`on_ready(ServiceContext)`** -- Post-registration work: bootstrap data, start background tasks, wire up PubSub.
4. **`on_shutdown()`** -- Cleanup on graceful shutdown.

## Conditional Activation

`is_required()` receives a `StartupContext` for introspecting the current deployment:

```rust,ignore
fn is_required(&self, ctx: &StartupContext) -> bool {
    // Only activate if any app has a "kafka" config key
    ctx.any_app_has_config("kafka")
}
```

`StartupContext` methods:

| Method | Description |
|--------|-------------|
| `any_app_has_config(key)` | True if any app config has the given top-level key |
| `any_table_has_field_directive(directive)` | True if any table field type matches (case-insensitive) |
| `any_app_requires_auth()` | True if any app has non-empty `requiredRoles` / `required_roles` |

Services with `is_required() == false` are skipped entirely.

## Registration

`register()` receives a mutable `RegistrationContext` where you add components:

```rust,ignore
fn register(&self, ctx: &mut RegistrationContext) -> Result<()> {
    // Add GraphQL schemas
    ctx.add_schema(include_str!("schema.graphql"));

    // Add resource handlers
    ctx.add_resource(Box::new(MyResource::new()));

    // Add auth providers
    ctx.add_auth_provider(Arc::new(BasicAuthProvider::new()));

    // Add vector hooks
    ctx.add_vector_hook(Arc::new(MyVectorHook::new()));

    // Add AI hooks
    ctx.add_ai_hook(Arc::new(MyAiHook::new()));

    // Add request middleware
    ctx.add_middleware(Arc::new(RateLimiter::new(100)));

    // Add embedded web files
    ctx.add_web_files(vec![EmbeddedFile {
        path: "index.html",
        content: include_bytes!("../web/index.html"),
    }]);

    Ok(())
}
```

`RegistrationContext` methods:

| Method | Description |
|--------|-------------|
| `add_schema(graphql)` | Add a GraphQL schema string |
| `add_resource(handler)` | Add a resource handler |
| `add_auth_provider(provider)` | Add an authentication provider |
| `add_vector_hook(hook)` | Add a vector embedding hook |
| `add_ai_hook(hook)` | Add an AI inference hook |
| `add_middleware(middleware)` | Add request middleware |
| `add_event_subscriber(subscriber)` | Add an event subscriber |
| `add_web_files(files)` | Add embedded static files |
| `app_id()` | Get the application ID |
| `root_dir()` | Get the root directory path |

## Post-Registration Setup

`on_ready()` runs after all schemas and tables are registered:

```rust,ignore
fn on_ready(&self, ctx: &ServiceContext) -> Result<()> {
    // Access tables by name
    let users = ctx.require_table("User")?;

    // Access PubSub for a table
    if let Some(pubsub) = ctx.pubsub("Order") {
        // Subscribe to order changes
    }

    // Set up an event subscriber for tracing events
    ctx.set_event_subscriber(Box::new(MySubscriber::new()));

    Ok(())
}
```

`ServiceContext` methods:

| Method | Description |
|--------|-------------|
| `table(name)` | Get a table backend by name (`Option`) |
| `require_table(name)` | Get a table backend or return an error |
| `pubsub(table_name)` | Get PubSub manager for a table |
| `set_event_subscriber(sub)` | Store an event subscriber for host to spawn |
| `app_id()` | Get the application ID |
| `root_dir()` | Get the root directory path |

## Dependency Ordering

Services declare dependencies via `depends_on()`. The runtime sorts services topologically:

```rust,ignore
fn depends_on(&self) -> &[&'static str] {
    &["yeti-auth"]  // This service starts after yeti-auth
}
```

## Built-In Services

| Service | ID | Purpose |
|---------|----|---------|
| yeti-auth | `yeti-auth` | Authentication (Basic, JWT, OAuth) |
| yeti-telemetry | `yeti-telemetry` | Tracing event capture, log persistence, OTLP export |
| yeti-ai | `yeti-ai` | Vector embeddings and LLM inference (Candle) |
| yeti-admin | `yeti-admin` | Admin dashboard and management API |
| yeti-kafka | `yeti-kafka` | Bidirectional Kafka bridge |
| yeti-benchmarks | `yeti-benchmarks` | Performance benchmarks |

All built-in services are binary-embedded (no filesystem extraction).

## Example: Minimal Service

```rust,ignore
pub struct PingService;

impl Service for PingService {
    fn id(&self) -> &'static str { "ping" }
    fn name(&self) -> &'static str { "Ping" }

    fn is_required(&self, _ctx: &StartupContext) -> bool {
        true  // Always active
    }

    fn register(&self, ctx: &mut RegistrationContext) -> Result<()> {
        ctx.add_resource(Box::new(PingResource));
        Ok(())
    }
}

pub fn service() -> Box<dyn Service> {
    Box::new(PingService)
}
```

## See Also

- [Service Lifecycle](extension-lifecycle.md) -- Detailed startup sequence
- [Event Subscribers](event-subscribers.md) -- Tracing event capture
- [Authentication Overview](auth-overview.md) -- Auth provider integration
- [Telemetry & Observability](telemetry.md) -- Telemetry service
