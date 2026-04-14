# Server Configuration

Reference for `yeti-config.yaml` at the root directory (default: `~/yeti/yeti-config.yaml`).

Override only what you need -- missing fields use defaults. The root directory is set in `~/.yeti/settings.toml`, not here.

A `.env` file in the root directory is loaded if present. Real environment variables take precedence.

---

## Complete Default Configuration

Every field with its default value. Only include fields you want to change.

```yaml
# ─── Environment ────────────────────────────────────────────────────────────
environment: development          # development | production

# ─── Root App ───────────────────────────────────────────────────────────────
# rootApp: null                   # App ID that serves at "/" instead of "/{appId}/"

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
    max_clients: 10000            # Maximum simultaneous MQTT connections
    qos: 2                        # Default QoS for bridge-published messages (0, 1, or 2)
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
  compressionThreshold: 1024      # Compress responses larger than this (bytes)
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
# Core writes to stdout only. File logging is handled by the yeti-telemetry service.
logging:
  level: info                     # trace | debug | info | warn | error
  # path: null                    # Log directory override (default: {rootDirectory}/logs/)

# ─── Applications ───────────────────────────────────────────────────────────
applications:
  # path: null                    # Applications directory override (default: {rootDirectory}/applications/)
  autoLoad: []                    # Git repos to clone on startup

# ─── Threads ────────────────────────────────────────────────────────────────
threads:
  # count: null                   # Tokio worker threads (default: CPU count)
  debug: false                    # Thread pool debugging

# ─── TLS ────────────────────────────────────────────────────────────────────
tls:
  autoGenerate: true              # Auto-generate self-signed certs if missing
  domain: localhost               # Domain for cert generation (certs/{domain}-cert.pem)
  # privateKey: null              # Path to PEM private key
  # certificate: null             # Path to PEM certificate

# ─── Rate Limiting ──────────────────────────────────────────────────────────
rateLimiting:
  maxRequestsPerSecond: 1000      # Server-wide rate limit

# ─── Telemetry ──────────────────────────────────────────────────────────────
# Metrics and OTLP export. The yeti-telemetry service handles log/span/metric persistence.
telemetry:
  metrics: true                   # Enable metrics collection
  serviceName: yeti               # Service name for OTLP export
  # otlpEndpoint: null            # OpenTelemetry collector endpoint (e.g. http://otel:4317)
  metricsIntervalSecs: 10         # System metrics emission interval (seconds)

# ─── RustFS / S3-Compatible Object Store ────────────────────────────────────
# When disabled (default), uses filesystem fallback at {rootDirectory}/object-store/.
rustfs:
  enabled: false                  # Enable S3 transport
  endpoint: "http://localhost:9000"  # S3-compatible endpoint URL
  accessKey: minioadmin           # Access key (matches MinIO/RustFS defaults)
  secretKey: minioadmin           # Secret key

# ─── Environment Variables ──────────────────────────────────────────────────
# Injected at startup. Real env vars take precedence.
env: {}

# ─── Extensions ─────────────────────────────────────────────────────────────
# Per-extension runtime configuration. Each extension has an enabled flag.
extensions:
  yeti-auth:
    enabled: true
    jwt:
      secret: "development-secret-change-in-production"
      algorithm: HS256
      accessTtl: 900              # Access token TTL in seconds (15 minutes)
      refreshTtl: 604800          # Refresh token TTL in seconds (7 days)
    oauth:
      github:
        clientId: ""
        clientSecret: ""
      google:
        clientId: ""
        clientSecret: ""
      microsoft:
        clientId: ""
        clientSecret: ""
  yeti-telemetry:
    enabled: true
  yeti-ai:
    enabled: true

# ─── Auth (shorthand) ──────────────────────────────────────────────────────
# Top-level shorthand parsed into extensions.yeti-auth configuration.
# auth:
#   enabled: true
#   jwt:
#     secret: "my-secret"
#   oauth:
#     github:
#       clientId: "..."
#       clientSecret: "..."
```

---

## Field Reference

### environment

| Value | Auth Behavior | Logging | TLS |
|-------|--------------|---------|-----|
| `development` | Bypasses auth for user-defined apps | `info` default | Self-signed OK |
| `production` | Enforces auth on all routes | `warn` default | Real certs expected |

### rootApp

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rootApp` | string | `null` | App ID that serves at `"/"` instead of `"/{appId}/"`. All other apps continue to serve at their app ID path. Also accepts the alias `root_app`. |

### interfaces

Protocol availability and audit logging.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `interfaces.port` | integer | `9996` | Main HTTPS port (REST, GraphQL, WS, SSE, gRPC, MCP) |
| `interfaces.rest.enabled` | boolean | `true` | REST API endpoints |
| `interfaces.rest.audit` | boolean | `false` | Audit REST operations |
| `interfaces.graphql.enabled` | boolean | `true` | GraphQL API |
| `interfaces.graphql.audit` | boolean | `false` | Audit GraphQL operations |
| `interfaces.ws.enabled` | boolean | `true` | WebSocket subscriptions |
| `interfaces.ws.audit` | boolean | `false` | Audit WebSocket operations |
| `interfaces.sse.enabled` | boolean | `true` | Server-Sent Events |
| `interfaces.sse.audit` | boolean | `false` | Audit SSE subscriptions |
| `interfaces.mqtt.enabled` | boolean | `true` | MQTT broker |
| `interfaces.mqtt.audit` | boolean | `false` | Audit MQTT publish/subscribe |
| `interfaces.mqtt.port` | integer | `8883` | MQTTS native TLS port (separate from main) |
| `interfaces.mqtt.max_clients` | integer | `10000` | Max simultaneous MQTT connections |
| `interfaces.mqtt.qos` | integer | `2` | Default QoS for bridge messages (0/1/2) |
| `interfaces.grpc.enabled` | boolean | `true` | gRPC tables service (same port as HTTP) |
| `interfaces.grpc.audit` | boolean | `false` | Audit gRPC operations |
| `interfaces.mcp.enabled` | boolean | `true` | Model Context Protocol (JSON-RPC 2.0 over HTTP) |
| `interfaces.mcp.audit` | boolean | `true` | Audit MCP tool calls (on by default) |

Disable unused interfaces to reduce memory and CPU overhead.

### http

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `http.cors` | boolean | `true` | CORS headers |
| `http.corsAccessList` | string[] | `["*"]` | Allowed CORS origins |
| `http.timeout` | integer | `60000` | Request timeout (ms) |
| `http.keepAliveTimeout` | integer | `75000` | TCP keep-alive timeout (ms) |
| `http.disconnectTimeout` | integer | `5000` | Graceful shutdown wait (ms) for in-flight requests |
| `http.maxConnectionRate` | integer | `256` | Max new TCP connections per second |
| `http.maxInFlightRequests` | integer | `10000` | Max concurrent requests (503 when exceeded) |
| `http.compressionThreshold` | integer | `1024` | Min response size (bytes) for gzip |
| `http.maxQueryDepth` | integer | `50` | Max FIQL query nesting depth |
| `http.maxQueryConditions` | integer | `200` | Max conditions per FIQL query |
| `http.maxResultSetSize` | integer | `10000` | Max records per scan/list |
| `http.maxRequestBodyBytes` | integer | `10485760` | Max request body (10 MB default) |

### storage

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `storage.caching` | boolean | `true` | In-memory block cache |
| `storage.compression` | boolean | `true` | LZ4 on-disk compression |
| `storage.path` | string | `null` | Data directory override (default: `{rootDirectory}/data/`) |
| `storage.cacheSizeMb` | integer | `null` | Block cache size in MB (default: 2048) |
| `storage.writeBufferSizeMb` | integer | `null` | Write buffer size in MB (default: 512) |
| `storage.shardCount` | integer | `null` | Parallel RocksDB shards (default: `num_cpus / 2`, min 2) |
| `storage.inMemory` | boolean | `false` | Volatile in-memory mode (data lost on restart) |

Read-heavy: increase `cacheSizeMb`. Write-heavy: increase `writeBufferSizeMb` and `shardCount`. Ephemeral data: consider `inMemory: true`.

### replication

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `replication.enabled` | boolean | `false` | Cluster replication (requires valid license) |
| `replication.licenseKey` | string | `null` | Ed25519-signed license key |
| `replication.port` | integer | `9997` | gRPC replication (TCP) + gossip membership (UDP) |
| `replication.seedNodes` | string[] | `[]` | Peer addresses for discovery (e.g. `["peer1:9997"]`) |
| `replication.advertiseAddr` | string | `""` | Address peers use to reach this node (auto-detected if empty) |
| `replication.nodeId` | string | `null` | Unique node ID (auto-generated UUID if null) |
| `replication.region` | string | `""` | Region name (empty = flat cluster) |
| `replication.replicationFactor` | integer | `3` | Replicas per shard |

### logging

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `logging.level` | string | `"info"` | Minimum log level: `trace`, `debug`, `info`, `warn`, `error` |
| `logging.path` | string | `null` | Log directory override (default: `{rootDirectory}/logs/`) |

Core writes to stdout only. The yeti-telemetry service handles file logging, rotation, and persistence.

Use `warn` in production. Use `debug` only when diagnosing specific issues -- `trace` generates massive output.

### applications

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `applications.path` | string | `null` | Applications directory override (default: `{rootDirectory}/applications/`) |
| `applications.autoLoad` | string[] | `[]` | Git repos to clone on startup |

### threads

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `threads.count` | integer | `null` | Tokio worker threads (default: CPU count) |
| `threads.debug` | boolean | `false` | Thread pool debug logging |

I/O-bound: increase to 2x CPU count. CPU-bound with vector embeddings: reduce to leave cores for inference.

### tls

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tls.autoGenerate` | boolean | `true` | Auto-generate self-signed certs if none exist |
| `tls.domain` | string | `"localhost"` | Domain for cert generation and file naming |
| `tls.privateKey` | string | `null` | PEM private key path (relative to rootDirectory) |
| `tls.certificate` | string | `null` | PEM certificate path (relative to rootDirectory) |

Production: provide real certificates and set `autoGenerate: false`. Development: `mkcert` is auto-detected for browser-trusted certs.

### rateLimiting

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rateLimiting.maxRequestsPerSecond` | integer | `1000` | Server-wide rate limit (429 when exceeded) |

### telemetry

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `telemetry.metrics` | boolean | `true` | System and per-app metrics |
| `telemetry.serviceName` | string | `"yeti"` | Service name for OTLP export |
| `telemetry.otlpEndpoint` | string | `null` | OpenTelemetry collector (e.g. `http://otel-collector:4317`) |
| `telemetry.metricsIntervalSecs` | integer | `10` | Seconds between system metric emissions |

Increase `metricsIntervalSecs` to 30-60 in production to reduce overhead.

### rustfs

S3-compatible object store. When disabled (default), falls back to `{rootDirectory}/object-store/`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rustfs.enabled` | boolean | `false` | S3 transport (filesystem fallback when false) |
| `rustfs.endpoint` | string | `"http://localhost:9000"` | S3-compatible endpoint URL |
| `rustfs.accessKey` | string | `"minioadmin"` | Access key |
| `rustfs.secretKey` | string | `"minioadmin"` | Secret key |

### env

Environment variables injected at startup. Real env vars take precedence. A `.env` file in the root directory is also loaded if present (`#` lines are comments).

```yaml
env:
  JWT_SECRET_KEY: "my-production-secret"
  GOOGLE_CLIENT_ID: "123456.apps.googleusercontent.com"
  GOOGLE_CLIENT_SECRET: "secret-value"
```

### extensions

Per-extension runtime configuration. Each extension has an `enabled` flag and extension-specific settings.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `extensions.yeti-auth.enabled` | boolean | `true` | Authentication extension |
| `extensions.yeti-auth.jwt.secret` | string | `"development-secret-change-in-production"` | JWT signing secret |
| `extensions.yeti-auth.jwt.algorithm` | string | `"HS256"` | JWT signing algorithm |
| `extensions.yeti-auth.jwt.accessTtl` | integer | `900` | Access token TTL (seconds) |
| `extensions.yeti-auth.jwt.refreshTtl` | integer | `604800` | Refresh token TTL (seconds) |
| `extensions.yeti-auth.oauth.github.clientId` | string | `""` | GitHub OAuth client ID |
| `extensions.yeti-auth.oauth.github.clientSecret` | string | `""` | GitHub OAuth client secret |
| `extensions.yeti-auth.oauth.google.clientId` | string | `""` | Google OAuth client ID |
| `extensions.yeti-auth.oauth.google.clientSecret` | string | `""` | Google OAuth client secret |
| `extensions.yeti-auth.oauth.microsoft.clientId` | string | `""` | Microsoft OAuth client ID |
| `extensions.yeti-auth.oauth.microsoft.clientSecret` | string | `""` | Microsoft OAuth client secret |
| `extensions.yeti-telemetry.enabled` | boolean | `true` | Telemetry extension |
| `extensions.yeti-ai.enabled` | boolean | `true` | AI service (embeddings, inference, model management) |

### auth (shorthand)

Top-level `auth:` key is shorthand parsed into `extensions.yeti-auth`. The two forms are equivalent. See [Authentication](../guides/auth-overview.md).

---

## Environment Variable Overrides

Override config file values at startup:

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

rootApp: www

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

extensions:
  yeti-auth:
    jwt:
      secret: "${JWT_SECRET}"
      accessTtl: 300
    oauth:
      github:
        clientId: "${GITHUB_CLIENT_ID}"
        clientSecret: "${GITHUB_CLIENT_SECRET}"

env:
  JWT_SECRET: "loaded-from-env-or-dotenv"
```

---

## See Also

- [CLI Arguments](cli.md) — Command-line overrides
- [Environment Variables](environment-variables.md) — Environment configuration
- [TLS & HTTPS](tls.md) — Certificate setup
