# Server Configuration

Reference for `yeti-config.yaml` at the root directory (default: `~/yeti/yeti-config.yaml`).

Only override what you need — missing fields use sensible defaults. The root directory itself is set in `~/.yeti/settings.toml`, not in this file.

---

## Complete Default Configuration

This is every field with its default value. Your config file only needs the fields you want to change.

```yaml
# ─── Environment ────────────────────────────────────────────────────────────
environment: development          # development | production

# ─── Interfaces ─────────────────────────────────────────────────────────────
# All protocols share the main port except MQTT (separate TLS port).
# Each interface has enabled/audit flags. Global enabled: false cannot be
# overridden by per-table @export directives.
interfaces:
  port: 9996                      # Main HTTPS port (REST, GraphQL, WS, SSE, gRPC, MCP)
  rest:
    enabled: true
    audit: false
  graphql:
    enabled: true
    audit: false
  ws:
    enabled: true
    audit: false
  sse:
    enabled: true
    audit: false
  mqtt:
    enabled: true
    audit: false
    port: 8883                    # MQTTS native TLS port (separate from main port)
    maxClients: 10000             # Maximum simultaneous MQTT connections
    qos: 2                       # Default QoS for bridge-published messages (0, 1, or 2)
  grpc:
    enabled: true
    audit: false
  mcp:
    enabled: true
    audit: true                   # MCP auditing on by default

# ─── HTTP ───────────────────────────────────────────────────────────────────
# Protocol-level settings for request handling, timeouts, and limits.
http:
  cors: true                      # Enable CORS headers
  corsAccessList:                  # Allowed CORS origins
    - "*"
  timeout: 60000                  # Request timeout (ms)
  keepAliveTimeout: 75000         # Keep-alive timeout (ms)
  disconnectTimeout: 5000         # Client disconnect timeout (ms)
  maxConnectionRate: 256          # Maximum new connections per second
  maxInFlightRequests: 10000      # Maximum concurrent requests (503 when exceeded)
  compressionThreshold: 1024     # Compress responses larger than this (bytes)
  maxQueryDepth: 50               # Maximum FIQL query nesting depth
  maxQueryConditions: 200         # Maximum conditions in a single FIQL query
  maxResultSetSize: 10000         # Maximum records returned by scan operations
  maxRequestBodyBytes: 10485760   # Maximum request body size (10 MB)

# ─── Storage ────────────────────────────────────────────────────────────────
# Embedded sharded RocksDB. All fields optional — system auto-tunes.
storage:
  caching: true                   # In-memory read cache
  compression: true               # LZ4 data compression
  # path: null                    # Data directory override (default: {rootDirectory}/data/)
  # cacheSizeMb: null             # Block cache size in MB (default: 2048 = 2 GB)
  # writeBufferSizeMb: null       # Write buffer size in MB (default: 512)
  # shardCount: null              # Parallel shards (default: num_cpus / 2, min 2)
  # inMemory: false               # Volatile in-memory mode (no disk persistence)

# ─── Replication ────────────────────────────────────────────────────────────
# Cluster replication (license-gated). Omit entirely for standalone mode.
replication:
  enabled: false
  # licenseKey: null              # Ed25519-signed license key (offline verification)
  port: 9997                      # gRPC replication (TCP) + gossip membership (UDP)
  # seedNodes: []                 # Peer addresses for cluster discovery
  # advertiseAddr: ""             # Advertised address (auto-detected if empty)
  # nodeId: null                  # Unique node ID (auto-generated if null)
  # region: ""                    # Region name for region-aware replication
  replicationFactor: 3            # Number of replicas per shard

# ─── Logging ────────────────────────────────────────────────────────────────
# Core writes to stdout only. File logging is handled by the yeti-telemetry extension.
logging:
  level: info                     # trace | debug | info | warn | error
  # path: null                   # Log directory override (default: {rootDirectory}/logs/)

# ─── Applications ───────────────────────────────────────────────────────────
applications:
  # path: null                   # Applications directory override (default: {rootDirectory}/applications/)
  autoLoad: []                    # Git repos to clone on startup

# ─── Threads ────────────────────────────────────────────────────────────────
threads:
  # count: null                  # Tokio worker threads (default: CPU count)
  debug: false                    # Thread pool debugging

# ─── TLS ────────────────────────────────────────────────────────────────────
tls:
  autoGenerate: true              # Auto-generate self-signed certs if missing
  domain: localhost               # Domain for cert generation (certs/{domain}-cert.pem)
  # privateKey: null             # Path to PEM private key
  # certificate: null            # Path to PEM certificate

# ─── Rate Limiting ──────────────────────────────────────────────────────────
rateLimiting:
  maxRequestsPerSecond: 1000      # Server-wide rate limit

# ─── Telemetry ──────────────────────────────────────────────────────────────
# Metrics and OTLP export. The yeti-telemetry extension handles log/span/metric persistence.
telemetry:
  metrics: true                   # Enable metrics collection
  serviceName: yeti               # Service name for OTLP export
  # otlpEndpoint: null           # OpenTelemetry collector endpoint (e.g. http://otel:4317)
  metricsIntervalSecs: 10        # System metrics emission interval (seconds)

# ─── Environment Variables ──────────────────────────────────────────────────
# Injected at startup. Real env vars take precedence.
env: {}

# ─── Auth ───────────────────────────────────────────────────────────────────
# Top-level shorthand for extensions.yeti_auth configuration.
# auth:
#   methods: [basic, jwt, oauth]
#   providers: { ... }
```

---

## Field Reference

### environment

| Value | Auth Behavior | Logging | TLS |
|-------|--------------|---------|-----|
| `development` | Bypasses auth for user-defined apps | `info` default | Self-signed OK |
| `production` | Enforces auth on all routes | `warn` default | Real certs expected |

### interfaces

Controls which protocols are available and whether they generate audit logs.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `interfaces.port` | integer | `9996` | Main HTTPS port shared by REST, GraphQL, WebSocket, SSE, gRPC, and MCP |
| `interfaces.rest.enabled` | boolean | `true` | Enable REST API endpoints |
| `interfaces.rest.audit` | boolean | `false` | Log REST operations to audit trail |
| `interfaces.graphql.enabled` | boolean | `true` | Enable GraphQL API |
| `interfaces.graphql.audit` | boolean | `false` | Log GraphQL operations |
| `interfaces.ws.enabled` | boolean | `true` | Enable WebSocket subscriptions |
| `interfaces.ws.audit` | boolean | `false` | Log WebSocket operations |
| `interfaces.sse.enabled` | boolean | `true` | Enable Server-Sent Events |
| `interfaces.sse.audit` | boolean | `false` | Log SSE subscriptions |
| `interfaces.mqtt.enabled` | boolean | `true` | Enable MQTT broker |
| `interfaces.mqtt.audit` | boolean | `false` | Log MQTT publish/subscribe |
| `interfaces.mqtt.port` | integer | `8883` | MQTTS native TLS port (separate from main port) |
| `interfaces.mqtt.maxClients` | integer | `10000` | Maximum simultaneous MQTT connections |
| `interfaces.mqtt.qos` | integer | `2` | Default QoS for bridge messages (0=at most once, 1=at least once, 2=exactly once) |
| `interfaces.grpc.enabled` | boolean | `true` | Enable gRPC tables service (same port as HTTP) |
| `interfaces.grpc.audit` | boolean | `false` | Log gRPC operations |
| `interfaces.mcp.enabled` | boolean | `true` | Enable Model Context Protocol (JSON-RPC 2.0 over HTTP) |
| `interfaces.mcp.audit` | boolean | `true` | Log MCP tool calls (on by default for AI agent observability) |

**Optimization**: Disable unused interfaces to reduce memory and CPU overhead. For example, if you only serve REST clients, disable `graphql`, `ws`, `sse`, `mqtt`, `grpc`, and `mcp`.

### http

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `http.cors` | boolean | `true` | Enable CORS headers |
| `http.corsAccessList` | string[] | `["*"]` | Allowed CORS origins. Use specific domains in production. |
| `http.timeout` | integer | `60000` | Request timeout in ms. Requests exceeding this are terminated. |
| `http.keepAliveTimeout` | integer | `75000` | TCP keep-alive timeout in ms. Set slightly above your load balancer's timeout. |
| `http.disconnectTimeout` | integer | `5000` | Graceful shutdown wait time in ms for in-flight requests. |
| `http.maxConnectionRate` | integer | `256` | Maximum new TCP connections accepted per second. Protects against connection storms. |
| `http.maxInFlightRequests` | integer | `10000` | Maximum concurrent requests. Returns 503 when exceeded. |
| `http.compressionThreshold` | integer | `1024` | Minimum response size (bytes) to trigger gzip compression. |
| `http.maxQueryDepth` | integer | `50` | Maximum FIQL query nesting depth. Prevents stack overflow from deeply nested queries. |
| `http.maxQueryConditions` | integer | `200` | Maximum conditions per FIQL query. Prevents combinatorial explosion. |
| `http.maxResultSetSize` | integer | `10000` | Maximum records returned by scan/list operations. Use pagination for larger datasets. |
| `http.maxRequestBodyBytes` | integer | `10485760` | Maximum request body size (default 10 MB). Increase for bulk imports. |

**Optimization**: For high-throughput APIs, increase `maxInFlightRequests` and `maxConnectionRate`. For large dataset imports, increase `maxRequestBodyBytes` and `maxResultSetSize`. Lower `compressionThreshold` to reduce bandwidth at the cost of CPU.

### storage

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `storage.caching` | boolean | `true` | In-memory block cache for frequently read data. Disable only if memory-constrained. |
| `storage.compression` | boolean | `true` | LZ4 compression for on-disk data. Reduces I/O at minimal CPU cost. |
| `storage.path` | string | `null` | Data directory override. Default: `{rootDirectory}/data/` |
| `storage.cacheSizeMb` | integer | `null` | Block cache size in MB. Default auto-tunes to 2048 (2 GB). |
| `storage.writeBufferSizeMb` | integer | `null` | Write buffer (memtable) size in MB. Default: 512 MB. |
| `storage.shardCount` | integer | `null` | Number of parallel RocksDB shards. Default: `num_cpus / 2` (min 2). |
| `storage.inMemory` | boolean | `false` | Volatile in-memory mode. Fast but all data lost on restart. |

**Optimization**: For read-heavy workloads, increase `cacheSizeMb` (allocate 50-75% of available RAM). For write-heavy workloads, increase `writeBufferSizeMb` and `shardCount`. More shards improve write parallelism but increase file descriptor usage. For ephemeral data (caches, sessions), consider `inMemory: true`.

### replication

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `replication.enabled` | boolean | `false` | Enable cluster replication (requires valid license) |
| `replication.licenseKey` | string | `null` | Ed25519-signed license key for replication feature |
| `replication.port` | integer | `9997` | Single port for both gRPC replication (TCP) and gossip membership (UDP) |
| `replication.seedNodes` | string[] | `[]` | Peer addresses for cluster discovery (e.g. `["peer1:9997"]`) |
| `replication.advertiseAddr` | string | `""` | Address peers use to reach this node. Auto-detected if empty. |
| `replication.nodeId` | string | `null` | Unique node identifier. Auto-generated UUID if null. |
| `replication.region` | string | `""` | Region name for region-aware replication. Empty = flat cluster. |
| `replication.replicationFactor` | integer | `3` | Number of replicas per shard. Higher = more durable, more storage. |

### logging

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `logging.level` | string | `"info"` | Minimum log level: `trace`, `debug`, `info`, `warn`, `error` |
| `logging.path` | string | `null` | Log directory override. Default: `{rootDirectory}/logs/` |

Core writes to stdout only. The yeti-telemetry extension handles file logging, log rotation, and persistence to RocksDB.

**Optimization**: Use `warn` in production to reduce log volume. Use `debug` only when diagnosing specific issues — `trace` generates massive output.

### applications

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `applications.path` | string | `null` | Applications directory override. Default: `{rootDirectory}/applications/` |
| `applications.autoLoad` | string[] | `[]` | Git repository URLs to clone on startup |

### threads

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `threads.count` | integer | `null` | Tokio worker thread count. Default: CPU count. |
| `threads.debug` | boolean | `false` | Enable thread pool debug logging |

**Optimization**: Leave at default (CPU count) for most workloads. For I/O-bound applications, increase to 2x CPU count. For CPU-bound workloads with vector embeddings, reduce to leave cores available for ONNX inference.

### tls

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tls.autoGenerate` | boolean | `true` | Auto-generate self-signed certificates if none exist |
| `tls.domain` | string | `"localhost"` | Domain for certificate generation and file naming |
| `tls.privateKey` | string | `null` | Path to PEM private key file (relative to rootDirectory) |
| `tls.certificate` | string | `null` | Path to PEM certificate file (relative to rootDirectory) |

For production, provide real certificates and set `autoGenerate: false`. For local development, `mkcert` is auto-detected for browser-trusted certificates.

### rateLimiting

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rateLimiting.maxRequestsPerSecond` | integer | `1000` | Server-wide rate limit. Requests beyond this are rejected with 429. |

### telemetry

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `telemetry.metrics` | boolean | `true` | Enable system and per-app metrics collection |
| `telemetry.serviceName` | string | `"yeti"` | Service name reported to OTLP collectors |
| `telemetry.otlpEndpoint` | string | `null` | OpenTelemetry collector endpoint (e.g. `http://otel-collector:4317`) |
| `telemetry.metricsIntervalSecs` | integer | `10` | Seconds between system metric emissions |

**Optimization**: Increase `metricsIntervalSecs` to 30-60 in production to reduce telemetry overhead. Set `otlpEndpoint` to export to Grafana, Datadog, or other observability platforms.

### env

Key-value map of environment variables injected at startup. Real environment variables take precedence. Useful for secrets that extensions read via `std::env::var()`.

```yaml
env:
  JWT_SECRET_KEY: "my-production-secret"
  GOOGLE_CLIENT_ID: "123456.apps.googleusercontent.com"
  GOOGLE_CLIENT_SECRET: "secret-value"
```

### auth

Top-level shorthand parsed into `extensions.yeti_auth` configuration. See the [Authentication](../guides/authentication.md) guide for full details.

---

## Environment Variable Overrides

These environment variables override config file values at startup:

| Variable | Overrides | Description |
|----------|-----------|-------------|
| `APPLICATION_PORT` | `interfaces.port` | HTTPS listening port |
| `LOG_LEVEL` | `logging.level` | Log level (trace/debug/info/warn/error) |
| `ENVIRONMENT` | `environment` | Server environment mode |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `telemetry.otlpEndpoint` | OTLP collector endpoint |
| `REPLICATION_PORT` | `replication.port` | Replication port (also enables replication) |
| `SEED_NODES` | `replication.seedNodes` | Comma-separated peer addresses |

---

## Production Example

```yaml
environment: production

interfaces:
  port: 443

http:
  cors: false
  corsAccessList:
    - "https://app.example.com"
  timeout: 30000
  maxInFlightRequests: 50000
  maxResultSetSize: 5000

storage:
  cacheSizeMb: 8192
  writeBufferSizeMb: 1024
  shardCount: 8

logging:
  level: warn

tls:
  autoGenerate: false
  domain: api.example.com
  privateKey: certs/api.example.com-key.pem
  certificate: certs/api.example.com-cert.pem

telemetry:
  serviceName: yeti-production
  otlpEndpoint: "http://otel-collector:4317"
  metricsIntervalSecs: 30

env:
  JWT_SECRET_KEY: "${JWT_SECRET}"
```

---

## See Also

- [CLI Arguments](cli.md) — Command-line overrides
- [Environment Variables](environment-variables.md) — Environment configuration
- [TLS & HTTPS](tls.md) — Certificate setup
