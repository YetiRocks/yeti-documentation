# Services

Services provide shared capabilities -- authentication, telemetry, AI, auditing -- to any application that opts in. They are binary-embedded Rust crates that implement the `Service` trait.

## Built-in Services

| Service | Purpose |
|---------|---------|
| **yeti-auth** | Authentication (Basic, JWT, OAuth) and role-based access control |
| **yeti-telemetry** | Log collection, span tracing, metrics, and a real-time dashboard |
| **yeti-ai** | Embedding models (HNSW vector indexing), local LLM inference, and model management |
| **yeti-audit** | Per-table audit logging with configurable retention and state capture |
| **yeti-admin** | Application management UI, file browser, API keys, schema viewer |

All five are statically compiled into the binary. Disable, replace, or supplement as needed.

## Service Trait

Each service implements the `Service` trait from `yeti-types`:

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

    /// Whether this service should be activated given the current config.
    fn is_required(&self, ctx: &StartupContext) -> bool;

    /// Register schemas, resources, hooks, and providers.
    fn register(&self, ctx: &mut RegistrationContext) -> Result<()>;

    /// Post-registration setup (bootstrap data, background tasks, etc.).
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

The runtime calls service methods in order:

### 1. StartupContext -- Activation Check

`is_required(&StartupContext)` decides whether the service activates. `StartupContext` provides read-only introspection:

| Method | Purpose |
|--------|---------|
| `ctx.any_app_has_config("auth")` | Check if any app has a given config key |
| `ctx.any_table_has_field_directive("Vector")` | Check if any table uses a field type |
| `ctx.any_app_requires_auth()` | Check if any app has `required_roles` |

### 2. RegistrationContext -- Resource Registration

`register(&mut RegistrationContext)` adds schemas, resources, providers, and hooks:

| Method | Purpose |
|--------|---------|
| `ctx.add_schema(graphql)` | Register a GraphQL schema string |
| `ctx.add_resource(handler)` | Register a resource handler |
| `ctx.add_web_files(files)` | Register embedded static files |
| `ctx.add_auth_provider(provider)` | Register an authentication provider |
| `ctx.add_vector_hook(hook)` | Register a vector embedding hook |
| `ctx.add_ai_hook(hook)` | Register an AI inference hook |
| `ctx.add_middleware(middleware)` | Register request middleware |
| `ctx.add_event_subscriber(subscriber)` | Register a telemetry event handler |

### 3. ServiceContext -- Post-Registration Setup

`on_ready(&ServiceContext)` runs after all routes and tables are registered:

| Method | Purpose |
|--------|---------|
| `ctx.table("name")` | Get a table backend by name |
| `ctx.require_table("name")` | Get a table backend or return error |
| `ctx.pubsub("table")` | Get a PubSub manager by table name |
| `ctx.set_event_subscriber(sub)` | Register a telemetry event handler |
| `ctx.root_dir()` | Root directory path |
| `ctx.app_id()` | Application ID |

### 4. Shutdown

`on_shutdown()` runs during graceful server shutdown for cleanup.

## Consumer Configuration

Apps opt in to services via top-level keys in `config.yaml`:

```yaml
auth:
  methods: [basic, jwt, oauth]
  oauth:
    default_role: "viewer"
    rules:
      - strategy: provider
        pattern: "google"
        role: admin
      - strategy: email
        pattern: "*@corp.com"
        role: standard

telemetry:
  level: "info"

required_roles: [admin, editor]
```

Short config keys map to full service IDs:

| Config Key | Service ID |
|------------|------------|
| `auth` | `yeti-auth` |
| `telemetry` | `yeti-telemetry` |
| `audit` | `yeti-audit` |
| `vectors` | `yeti-ai` |

Services auto-activate based on configuration introspection. yeti-auth activates when any app has `auth:` config or `required_roles`. yeti-ai activates when any table has `Vector` fields.

## Dependency Ordering

Services declare dependencies via `depends_on()`. The runtime topologically sorts them to ensure correct start order. Telemetry services sort first so the event subscriber captures other services' startup logs.

## Dylib Boundary Rules

User-defined extensions (`extension: true`) compile as dynamic libraries and must observe these constraints:

- **No `tokio::spawn`** -- Spawning tasks corrupts the host runtime. Use `set_event_subscriber()` for background work.
- **No host statics** -- `OnceLock` statics are duplicated in the dylib. Use dylib-local statics.
- **Flag-based patterns** -- Set flags in `on_ready()`, let the host check them after the call returns.
- **Use `tracing` macros** -- Output may not reach the host subscriber due to TLS isolation, but use `tracing::warn!()` for consistent API. Never use `eprintln!()`.
