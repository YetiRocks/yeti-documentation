# Monitoring

## Operations API

Health check (liveness probe):

```bash
curl -s http://localhost:9995/health
```

System information:

```bash
curl -s http://localhost:9995/system
```

Active configuration (secrets redacted):

```bash
curl -s http://localhost:9995/config
```

## Telemetry Extension

### REST Queries

```bash
curl -sk "https://localhost:9996/yeti-telemetry/Log?limit=50&sort=-timestamp"
curl -sk "https://localhost:9996/yeti-telemetry/Log?filter=level==ERROR"
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

Exports via OpenTelemetry Protocol to Grafana, Datadog, Jaeger, Prometheus, etc.

Also configurable via `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable.

## Monitoring Tiers

| Tier | Approach | Latency |
|------|----------|---------|
| Real-time | SSE streams or Dashboard | Instant |
| Near-real-time | OTLP export to Grafana | Seconds |
| Historical | REST queries on Log/Span/Metric tables | On-demand |
| Uptime | Operations API health check | Poll-based |
