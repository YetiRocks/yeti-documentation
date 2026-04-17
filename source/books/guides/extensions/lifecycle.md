# Service Lifecycle

The runtime calls each `Service` trait method in order, with context objects that expose progressively more capability.

## Startup Sequence

### 1. Discovery

All services are registered in the `ServiceRegistry` (a `Vec<Box<dyn Service>>`). Built-in services are compiled into the binary.

### 2. Dependency Sort

Services are sorted topologically based on `depends_on()`. Services with no dependencies start first. Telemetry services are sorted earliest so their event subscriber captures other services' startup events.

```rust,ignore
fn depends_on(&self) -> &[&'static str] {
    &["yeti-auth"]  // Start after yeti-auth
}
```

### 3. is_required(StartupContext)

Each service decides whether to activate. The `StartupContext` provides read-only introspection:

```rust,ignore
pub struct StartupContext<'a> {
    pub tables: &'a [TableDefinition],     // All discovered table definitions
    pub app_configs: &'a [serde_json::Value], // All app configs as raw JSON
}
```

**StartupContext methods:**

| Method | Description |
|--------|-------------|
| `any_app_has_config(key)` | Check if any app has a top-level config key |
| `any_table_has_field_directive(directive)` | Check if any table field type matches |
| `any_app_requires_auth()` | Check if any app has required roles |

Example: yeti-kafka only activates when an app has `kafka:` config:

```rust,ignore
fn is_required(&self, ctx: &StartupContext) -> bool {
    ctx.any_app_has_config("kafka")
}
```

Services with `is_required() == false` are skipped entirely.

### 4. register(RegistrationContext)

Active services add their schemas, resources, hooks, and providers:

```rust,ignore
pub struct RegistrationContext {
    pub schemas: Vec<String>,
    pub resources: Vec<Box<dyn Resource>>,
    pub auth_providers: Vec<Arc<dyn AuthProvider>>,
    pub auth_hooks: Vec<Arc<dyn AuthHook>>,
    pub vector_hooks: Vec<Arc<dyn VectorHook>>,
    pub ai_hooks: Vec<Arc<dyn AiHook>>,
    pub computed_field_hooks: Vec<Arc<dyn ComputedFieldHook>>,
    pub middleware: Vec<Arc<dyn RequestMiddleware>>,
    pub event_subscribers: Vec<Box<dyn EventSubscriber>>,
    pub web_files: Vec<EmbeddedFile>,
    pub background_tasks: Vec<Pin<Box<dyn Future<Output = ()> + Send>>>,
    pub app_id: String,
    pub root_directory: String,
}
```

Helper methods: `add_schema()`, `add_resource()`, `add_auth_provider()`, `add_vector_hook()`, `add_ai_hook()`, `add_middleware()`, `add_event_subscriber()`, `add_web_files()`.

Services with `is_critical() == true` abort startup on registration failure.

### 5. Schema and Table Creation

After all services register, the runtime:
- Parses GraphQL schemas into `TableDefinition` structs
- Creates storage backends (RocksDB)
- Maps REST/GraphQL/SSE/WebSocket/MQTT routes
- Loads seed data

### 6. on_ready(ServiceContext)

Post-registration hook with full runtime access. Tables exist and are queryable:

```rust,ignore
pub struct ServiceContext {
    pub app_id: String,
    pub root_directory: String,
    // + private fields for table/pubsub lookup
}
```

**ServiceContext methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `table(name)` | `Option<Arc<dyn KvBackend>>` | Get table backend by name |
| `require_table(name)` | `Result<Arc<dyn KvBackend>>` | Get table or error (logs warning) |
| `pubsub(table_name)` | `Option<Arc<PubSubManager>>` | Get PubSub manager for a table |
| `set_event_subscriber(sub)` | -- | Store handler for host to spawn |
| `take_event_subscriber()` | `Option<Box<dyn EventSubscriber>>` | Take the stored subscriber |
| `app_id()` | `&str` | Application ID |
| `root_dir()` | `&str` | Root directory path |

Example: yeti-auth bootstraps admin user from `.bootstrap.json`:

```rust,ignore
fn on_ready(&self, ctx: &ServiceContext) -> Result<()> {
    let users = ctx.require_table("User")?;
    let roles = ctx.require_table("Role")?;
    // Bootstrap admin user if .bootstrap.json exists
    bootstrap_from_file(ctx.root_dir(), &users, &roles)?;
    Ok(())
}
```

### 7. Host Spawns Event Subscribers

After `on_ready()` returns, the host:
1. Takes the event subscriber via `take_event_subscriber()`
2. Creates `mpsc::channel(10_000)` in host context
3. Registers the sender with `DispatchLayer`
4. Spawns `subscriber.run(rx)` on the host tokio runtime

This runs in host context, not dylib context, so all tokio operations are safe.

### 8. on_shutdown()

Called during graceful shutdown in reverse dependency order.

## Complete Sequence Diagram

```
ServiceRegistry
    |
    v
[topological sort by depends_on()]
    |
    v
for each service:
    is_required(StartupContext) -----> skip if false
    register(RegistrationContext) ---> add schemas, resources, hooks
    |
[create tables, map routes, load seed data]
    |
for each service:
    on_ready(ServiceContext) ---------> bootstrap data, PubSub, event subscribers
    |
[host spawns event subscribers]
    |
[server starts accepting requests]
    |
[shutdown signal]
    |
for each service (reverse order):
    on_shutdown()
```

## See Also

- [Building Services](building-extensions.md) -- `Service` trait overview
- [Event Subscribers](event-subscribers.md) -- Tracing event capture
- [Telemetry & Observability](telemetry.md) -- Telemetry service
- [PubSub](pubsub.md) -- Internal messaging backbone
