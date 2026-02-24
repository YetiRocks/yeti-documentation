# Extension Lifecycle

## Stages

### 1. Compiler Detection

The compiler scans source files for `struct {Name}Extension` - no config declaration needed.

```rust
pub struct TelemetryExtension {
    config: TelemetryConfig,
}
```

Source files are copied to `cache/builds/{app}/src/` and `lib.rs` is generated with entry points.

### 2. Dylib Compilation

Compiled as `.dylib` (macOS) or `.so` (Linux). First build ~2 minutes per plugin; cached rebuilds ~10 seconds.

### 3. Dylib Loading

Host loads each dylib via `dlopen`. The extension gets separate copies of thread-local storage, statics, and the tokio runtime.

### 4. initialize()

Earliest point for extension code. Use for lightweight setup only.

```rust
fn initialize(&self) -> Result<()> {
    eprintln!("[my-ext] Loaded");
    Ok(())
}
```

### 5. Auth Provider Registration

Host calls `auth_providers()` and `auth_hooks()` to collect auth components before any requests are processed.

### 6. Routes and Tables Registered

Tables created in storage, REST/GraphQL routes mapped, SSE/WebSocket wired up, seed data loaded.

### 7. on_ready()

Main setup hook with full runtime access:

```rust
fn on_ready(&self, ctx: &ExtensionContext) -> Result<()> {
    let log_table = ctx.table("log").expect("Log table registered");

    let handler = Box::new(MyEventHandler { log_table });
    ctx.set_event_subscriber(handler);
    Ok(())
}
```

### 8. Host Spawns Event Subscriber

After `on_ready()` returns, the host:
1. Takes the event subscriber
2. Creates `mpsc::channel(10_000)` in host context
3. Registers sender with `DispatchLayer`
4. Spawns `subscriber.run(rx)` on host tokio runtime

## ExtensionContext Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `table(name)` | `Option<Arc<TableResource>>` | Get table by lowercase name |
| `root_dir()` | `&str` | Runtime root directory |
| `auto_router()` | `&Arc<AutoRouter>` | App's router |
| `set_event_subscriber(sub)` | - | Store handler for host to spawn |

## Load Order

Telemetry extensions are sorted first so the event subscriber captures other extensions' startup events.

## See Also

- [Building Extensions](building-extensions.md) - Extension trait overview
- [Telemetry & Observability](telemetry.md) - Event subscriber example
- [PubSub](pubsub.md) - Internal messaging
- [Troubleshooting](troubleshooting.md) - Plugin and dylib issues
