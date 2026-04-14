# Telemetry Pipeline

Minimal event channel in core (~260 lines). All processing lives in the optional `yeti-telemetry` service.

## Pipeline

```
tracing::info!("message")
        │
  DispatchLayer              Captures events as JSON
        │
  Bounded Channel (10K)      tokio mpsc
        │
  EventSubscriber::run()     Implemented by service
        │
        ├──> Log/Span/Metric tables
        ├──> FileProvider (JSONL rotation)
        ├──> SSE streams
        └──> OtlpOutput (optional)
```

## DispatchLayer

A `tracing` subscriber layer that serializes events and spans to JSON, sent through a bounded channel (capacity 10,000).

### Event Format

```json
{"kind": "log", "timestamp": 1700000000.123, "level": "INFO", "target": "yeti_core::routing", "message": "Request processed"}
{"kind": "span", "timestamp": 1700000000.456, "name": "process_request", "level": "DEBUG", "duration_ms": 12.5}
```

### Feedback Filter

Uses `FILTERED_MESSAGE_PREFIXES` (SSE content checks) to prevent telemetry writes from generating more telemetry. In production mode, only ERROR-level events pass through.

## EventSubscriber Trait

```rust,ignore
pub trait EventSubscriber: Send + 'static {
    fn run(
        self: Box<Self>,
        rx: mpsc::Receiver<Value>,
    ) -> Pin<Box<dyn Future<Output = ()> + Send>>;
}
```

The host creates the channel, registers the sender, and spawns `run()` after `on_ready()`.

## yeti-telemetry Service

| Component | Purpose |
|-----------|---------|
| `TelemetryWriter` | Routes events to outputs |
| `FileProvider` | JSONL file rotation |
| `OtlpOutput` | OpenTelemetry Protocol export |
| Log/Span/Metric tables | Persistent storage + SSE |
| Dashboard UI | `/yeti-telemetry/` |

## Without a Service

DispatchLayer becomes a no-op. Only stdout logging remains.
