# Event Subscribers

Event subscribers receive structured tracing events (logs and spans) as JSON over a bounded channel (capacity 10,000). The yeti-telemetry service uses this to capture runtime data for persistence, export, and real-time dashboards.

## The EventSubscriber Trait

Defined in `yeti-types`:

```rust,ignore
pub trait EventSubscriber: Send + 'static {
    fn run(
        self: Box<Self>,
        rx: mpsc::Receiver<serde_json::Value>,
    ) -> Pin<Box<dyn Future<Output = ()> + Send>>;
}
```

The host calls `run()` after `on_ready()` returns, creating a bounded `mpsc` channel (capacity 10,000) and spawning the returned future on the host tokio runtime.

## Event Format

### Log Events

```json
{
  "kind": "log",
  "timestamp": 1710000000000.0,
  "level": "INFO",
  "target": "my_app::handler",
  "message": "Request processed",
  "fields": { "request_id": "abc-123", "duration_ms": "42" }
}
```

### Span Events

```json
{
  "kind": "span",
  "name": "handle_request",
  "target": "my_app::handler",
  "level": "INFO",
  "startTime": 1710000000000.0,
  "endTime": 1710000000042.0,
  "fields": { "method": "GET", "path": "/users" }
}
```

Fields are always string-valued in JSON, even for numeric tracing fields.

## Registration

Register during `on_ready()` via the `ServiceContext`:

```rust,ignore
fn on_ready(&self, ctx: &ServiceContext) -> Result<()> {
    let log_backend = ctx.require_table("Log")?;
    let subscriber = Box::new(MySubscriber { log_backend });
    ctx.set_event_subscriber(subscriber);
    Ok(())
}
```

Only one subscriber can be active per service. The host takes the subscriber after `on_ready()` returns and spawns it in host context.

## Minimal Example

```rust,ignore
pub struct DebugSubscriber;

impl EventSubscriber for DebugSubscriber {
    fn run(
        self: Box<Self>,
        mut rx: mpsc::Receiver<serde_json::Value>,
    ) -> Pin<Box<dyn Future<Output = ()> + Send>> {
        Box::pin(async move {
            while let Some(event) = rx.recv().await {
                let kind = event["kind"].as_str().unwrap_or("unknown");
                let msg = event["message"].as_str().unwrap_or("");
                println!("[{kind}] {msg}");
            }
        })
    }
}
```

## Registration via RegistrationContext

Event subscribers can also be registered during the `register()` phase:

```rust,ignore
fn register(&self, ctx: &mut RegistrationContext) -> Result<()> {
    ctx.add_event_subscriber(Box::new(MySubscriber::new()));
    Ok(())
}
```

## Feedback Prevention

The `DispatchLayer` filters events from internal targets to prevent infinite recursion when subscribers write to tables or emit tracing events. Only `FILTERED_MESSAGE_PREFIXES` (SSE content checks) are filtered. In production mode, non-ERROR events are skipped.

## Host Spawning

The service constructs the subscriber; the host executes it. After `on_ready()` returns:

1. Host calls `ctx.take_event_subscriber()`
2. Host creates `mpsc::channel(10_000)` in host context
3. Host registers the sender with `DispatchLayer`
4. Host spawns `subscriber.run(rx)` on the host tokio runtime

All async operations (channel receives, table writes, network I/O) run in host context where the tokio runtime is accessible.

## See Also

- [Building Services](plugins/overview.md) -- Service development
- [Service Lifecycle](plugins/lifecycle.md) -- Startup sequence
- [Telemetry & Observability](telemetry.md) -- yeti-telemetry service
