# Event Subscribers

Event subscribers receive structured tracing events (logs and spans) as JSON over a bounded channel (capacity 10,000). This is how extensions like yeti-telemetry capture runtime data.

## The EventSubscriber Trait

```rust
pub trait EventSubscriber: Send + 'static {
    fn run(
        self: Box<Self>,
        rx: mpsc::Receiver<Value>,
    ) -> Pin<Box<dyn Future<Output = ()> + Send>>;
}
```

The host calls `run()` after `on_ready()` returns, creating a bounded channel (capacity 10,000) and spawning the future on the host tokio runtime.

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

Register during `on_ready()`:

```rust
fn on_ready(&self, ctx: &ExtensionContext) -> Result<()> {
    let log_table = ctx.table("log");
    let subscriber = Box::new(MySubscriber { log_table });
    ctx.set_event_subscriber(subscriber);
    Ok(())
}
```

Only one subscriber can be active. Last `set_event_subscriber()` wins. No subscriber means events are silently dropped.

## Minimal Example

```rust
pub struct DebugSubscriber;

impl EventSubscriber for DebugSubscriber {
    fn run(
        self: Box<Self>,
        mut rx: mpsc::Receiver<Value>,
    ) -> Pin<Box<dyn Future<Output = ()> + Send>> {
        Box::pin(async move {
            while let Some(event) = rx.recv().await {
                let kind = event["kind"].as_str().unwrap_or("unknown");
                let msg = event["message"].as_str().unwrap_or("");
                eprintln!("[{}] {}", kind, msg);
            }
        })
    }
}
```

## Feedback Prevention

The `DispatchLayer` filters events from internal targets (`yeti_core::pubsub`, `backend`, `resource::table`, `http::sse`) to prevent infinite recursion when subscribers write to tables.

## Dylib Safety

The subscriber is constructed in dylib context but executed by the host. This works because the channel receiver is host-created and `Arc<dyn KvBackend>` uses vtable dispatch across the boundary. Do **not** call `tokio::spawn` or create channels inside `run()`.

## See Also

- [Building Extensions](building-extensions.md) - Extension development
- [Extension Lifecycle](extension-lifecycle.md) - Initialization order
- [Telemetry & Observability](telemetry.md) - yeti-telemetry extension
