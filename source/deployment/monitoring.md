# Monitoring

## Health Check

Liveness probe on the main HTTPS port:

```bash
curl -sk https://localhost:9996/health
```

Returns server status and loaded application count.

## Admin Dashboard

Application management and monitoring via Studio:

```
https://localhost:9996/studio/
```

See [Studio](../guides/studio.md) for details.

## Telemetry Service

### REST Queries

```bash
curl -sk "https://localhost:9996/yeti-telemetry/Log?limit=50&sort=-timestamp"
curl -sk "https://localhost:9996/yeti-telemetry/Log?level==ERROR"
curl -sk "https://localhost:9996/yeti-telemetry/Span?sort=-durationMs&limit=20"
```

### Real-Time SSE

```bash
curl -sk -N "https://localhost:9996/yeti-telemetry/Log?stream=sse"
curl -sk -N "https://localhost:9996/yeti-telemetry/Span?stream=sse"
curl -sk -N "https://localhost:9996/yeti-telemetry/Metric?stream=sse"
```

### Dashboard

```
https://localhost:9996/yeti-telemetry/
```

## OTLP Export

```yaml
telemetry:
  metrics: true
  serviceName: "yeti-production"
  otlpEndpoint: "http://otel-collector:4317"
```

OTLP export lives in `yeti-telemetry` (core has zero OpenTelemetry code). Exports to Grafana, Datadog, Jaeger, Prometheus, etc.

Also configurable via `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable.

## MCP Audit Logging

MCP tool invocations are audit-logged by default:

```yaml
interfaces:
  mcp:
    enabled: true
    audit: true
```

Events flow through telemetry and appear in the Log table.

## Monitoring Tiers

| Tier | Approach | Latency |
|------|----------|---------|
| Real-time | SSE streams or Dashboard | Instant |
| Near-real-time | OTLP export to Grafana | Seconds |
| Historical | REST queries on Log/Span/Metric tables | On-demand |
| Uptime | Health endpoint | Poll-based |
