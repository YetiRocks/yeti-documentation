# Server Configuration

Reference for `yeti-config.yaml` at the root directory (default: `~/yeti/yeti-config.yaml`).

## environment

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `environment` | string | `"development"` | `development`, `production`, or `test`. Affects TLS validation, logging, and security defaults. |

## rootDirectory

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rootDirectory` | string | `"~/yeti"` | Root directory for all Yeti data. Override with `--dir` CLI argument. |

## http

Application API server (default port 9996, HTTPS).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `http.port` | integer | `9996` | HTTPS port |
| `http.cors` | boolean | `true` | Enable CORS headers |
| `http.corsAccessList` | string[] | `["*"]` | Allowed CORS origins |
| `http.timeout` | integer | `120000` | Request timeout (ms) |
| `http.keepAliveTimeout` | integer | `30000` | Keep-alive timeout (ms) |
| `http.compressionThreshold` | integer | `1024` | Compress responses larger than this (bytes) |
| `http.maxConnectionRate` | integer | `256` | Max new connections per second |
| `http.maxInFlightRequests` | integer | `500` | Max concurrent requests (503 when exceeded) |
| `http.disconnectTimeout` | integer | `5000` | Graceful shutdown timeout (ms) |

## storage

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `storage.mode` | string | `"embedded"` | `"embedded"` for single-node RocksDB storage |
| `storage.caching` | boolean | `true` | Enable in-memory read cache |
| `storage.compression` | boolean | `true` | Enable data compression |
| `storage.path` | string | `null` | Custom storage path (default: `$rootDirectory/data/`) |

## logging

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `logging.level` | string | `"info"` | `error`, `warn`, `info`, `debug`, `trace` |
| `logging.auditLog` | boolean | `true` | Enable audit logging for data operations |

## threads

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `threads.count` | integer | `null` | Thread pool size (`null` = CPU count) |

## tls

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tls.autoGenerate` | boolean | `false` | Auto-generate self-signed certificates |
| `tls.privateKey` | string | `null` | Path to PEM private key file |
| `tls.certificate` | string | `null` | Path to PEM certificate file |

## env

Environment variables to inject at startup. Set before extensions initialize, so yeti-auth and other extensions can read them via `std::env::var()`. Real environment variables take precedence over values defined here.

```yaml
env:
  JWT_SECRET_KEY: "my-production-secret"
  GOOGLE_CLIENT_ID: "123456.apps.googleusercontent.com"
  GOOGLE_CLIENT_SECRET: "secret-value"
  ANTHROPIC_API_KEY: "sk-ant-..."
```

## mqtt

Embedded MQTT broker configuration.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mqtt.enabled` | boolean | `false` | Enable the embedded MQTT broker |
| `mqtt.port` | integer | `8883` | MQTTS port for native clients |
| `mqtt.maxClients` | integer | `10000` | Maximum simultaneous MQTT clients |

When enabled, the broker also exposes a WebSocket proxy at `wss://host:9996/mqtt` for browser clients.

## rateLimiting

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rateLimiting.maxRequestsPerSecond` | integer | `1000` | Max requests per second (server-wide) |
| `rateLimiting.maxConcurrentConnections` | integer | `100` | Max simultaneous connections |
| `rateLimiting.maxStorageGB` | integer | `10` | Max storage per tenant (GB) |
| `rateLimiting.ai.maxClaudeRequestsPerHour` | integer | `100` | AI generation rate limit |
| `rateLimiting.ai.maxEmbeddingRequestsPerHour` | integer | `1000` | Embedding rate limit |

## telemetry

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `telemetry.metrics` | boolean | `true` | Enable metrics collection |
| `telemetry.tracing` | boolean | `false` | Enable distributed tracing |
| `telemetry.auditLog` | boolean | `true` | Enable audit logging in telemetry |
| `telemetry.serviceName` | string | `"yeti"` | Service name for OTLP export |
| `telemetry.otlpEndpoint` | string | `""` | OpenTelemetry collector endpoint |

## maintenance

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `maintenance.backup.enabled` | boolean | `true` | Enable automatic backups |
| `maintenance.backup.intervalHours` | integer | `24` | Hours between backups |
| `maintenance.backup.retentionDays` | integer | `30` | Days to retain backups |
| `maintenance.healthCheck.intervalSeconds` | integer | `30` | Health check interval |
| `maintenance.healthCheck.timeoutSeconds` | integer | `5` | Health check timeout |

## audit

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `audit.enabled` | boolean | `false` | Enable global audit trail |

## Example

```yaml
environment: production
rootDirectory: /opt/yeti

http:
  port: 9996
  cors: true
  corsAccessList:
    - "https://app.example.com"
  timeout: 30000
  compressionThreshold: 1024

storage:
  mode: embedded
  caching: true
  compression: true

logging:
  level: info
  auditLog: true

tls:
  privateKey: /etc/ssl/private/yeti.key
  certificate: /etc/ssl/certs/yeti.crt

env:
  JWT_SECRET_KEY: "${JWT_SECRET}"
  GOOGLE_CLIENT_ID: "${GOOGLE_CLIENT_ID}"

mqtt:
  enabled: true
  port: 8883

telemetry:
  serviceName: yeti-production
  otlpEndpoint: "http://otel-collector:4317"
```

## See Also

- [CLI Arguments](cli.md) - Command-line overrides
- [Environment Variables](environment-variables.md) - Environment configuration
- [TLS & HTTPS](tls.md) - Certificate setup
