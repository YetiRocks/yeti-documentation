# Telemetry & Observability

The `yeti-telemetry` extension captures tracing events from the core runtime and persists logs, spans, and metrics to tables with real-time SSE streaming and optional OTLP export.

## Architecture

```
tracing::info!(...)
      |
      v
  DispatchLayer (core)         Captures events as JSON
      |
      v
  mpsc::channel (bounded, 10K)  Host-created channel
      |
      v
  EventSubscriber (extension)  Processes events
      |
      +---> Log/Span/Metric tables
      +---> SSE streams
      +---> OTLP export (optional)
```

Core contains only the `DispatchLayer` (~260 lines). All processing lives in the extension.

## Querying

```bash
# REST
curl -sk "https://localhost:9996/yeti-telemetry/Log?limit=50&sort=-timestamp"
curl -sk "https://localhost:9996/yeti-telemetry/Log?filter=level==ERROR"
curl -sk "https://localhost:9996/yeti-telemetry/Span?filter=traceId==abc-123"

# SSE streaming
curl -sk "https://localhost:9996/yeti-telemetry/Log?stream=sse"
curl -sk "https://localhost:9996/yeti-telemetry/Span?stream=sse"
curl -sk "https://localhost:9996/yeti-telemetry/Metric?stream=sse"
```

## Dashboard

```
https://localhost:9996/yeti-telemetry/
```

Live logs with level/target filtering and pipeline status.

## OTLP Export

```yaml
telemetry:
  otlpEndpoint: "http://localhost:4317"
  serviceName: yeti
```

Or: `export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"`

## Configuration

```yaml
telemetry:
  metrics: true
  tracing: false
  auditLog: true
  serviceName: yeti

logging:
  level: info
  auditLog: true
```

## Custom Telemetry

Replace yeti-telemetry by creating your own extension implementing `EventSubscriber`. Register via `ctx.set_event_subscriber()` in `on_ready()`. Without any telemetry extension, only stdout logging works.

## See Also

- [Event Subscribers](event-subscribers.md) - EventSubscriber trait
- [Server-Sent Events](sse.md) - SSE streaming
- [Server Configuration](../reference/server-config.md) - Config reference
