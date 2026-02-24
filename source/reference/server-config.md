# Server Configuration

Reference for `yeti-config.yaml` at the root directory (default: `~/yeti/yeti-config.yaml`).

## environment

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `environment` | string | `"development"` | `development`, `production`, or `test`. Affects TLS validation, logging, and security defaults. |

## rootDirectory

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rootDirectory` | string | `"~/yeti"` | Root directory for all Yeti data. Override with `--root-dir` CLI argument. |

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

## operationsApi

Administrative API (default port 9995, plain HTTP).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `operationsApi.port` | integer | `9995` | Operations API port |
| `operationsApi.enabled` | boolean | `true` | Enable the operations API |
| `operationsApi.cors` | boolean | `true` | Enable CORS |
| `operationsApi.corsAccessList` | string[] | `["*"]` | CORS allowed origins |

## storage

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `storage.mode` | string | `"embedded"` | `"embedded"` (single-node) or `"cluster"` (distributed) |
| `storage.caching` | boolean | `true` | Enable in-memory read cache |
| `storage.compression` | boolean | `true` | Enable data compression |
| `storage.path` | string | `null` | Custom storage path (default: `$rootDirectory/data/`) |

### storage.cluster

Only used when `storage.mode` is `"cluster"`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `storage.cluster.pdEndpoints` | string[] | `[]` | Placement driver endpoints |
| `storage.cluster.tlsCaPath` | string | `null` | CA certificate for mTLS |
| `storage.cluster.tlsCertPath` | string | `null` | Client certificate for mTLS |
| `storage.cluster.tlsKeyPath` | string | `null` | Client private key for mTLS |
| `storage.cluster.timeoutMs` | integer | `5000` | Timeout per operation (ms) |
| `storage.cluster.autoStart` | boolean | `false` | Auto-start Docker cluster (development only) |

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

telemetry:
  serviceName: yeti-production
  otlpEndpoint: "http://otel-collector:4317"
```

## See Also

- [CLI Arguments](cli.md) - Command-line overrides
- [Environment Variables](environment-variables.md) - Environment configuration
- [TLS & HTTPS](tls.md) - Certificate setup
