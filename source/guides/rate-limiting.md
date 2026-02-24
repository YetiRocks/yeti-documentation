# Rate Limiting

## Configuration

```yaml
rateLimiting:
  maxRequestsPerSecond: 1000
  maxConcurrentConnections: 100
  maxStorageGB: 10
  ai:
    maxClaudeRequestsPerHour: 100
    maxEmbeddingRequestsPerHour: 1000
```

## Request Rate

`maxRequestsPerSecond` caps overall throughput. Returns `429 Too Many Requests` when exceeded. Server-wide across all apps and clients.

## Connection Limiting

`maxConcurrentConnections` limits simultaneous TCP connections. Protects against connection exhaustion attacks.

## Backpressure

```yaml
http:
  maxInFlightRequests: 500
```

Returns `503 Service Unavailable` when in-flight requests exceed the threshold. Unlike rate limiting (throughput cap), backpressure limits concurrency.

## Storage Quotas

`maxStorageGB` caps total storage per tenant. Writes fail when exceeded; reads continue.

## Timeouts

```yaml
http:
  timeout: 120000         # Request timeout (ms)
  keepAliveTimeout: 30000 # Idle connection timeout (ms)
```

## Error Responses

- **429**: `{"error": "Rate limit exceeded. Maximum 1000 requests per second."}`
- **503**: `{"error": "Server overloaded. Please retry later."}`

Implement exponential backoff on these responses.

## Production Settings

| Setting | Dev | Production |
|---------|-----|------------|
| `maxRequestsPerSecond` | 1000 | Tune to hardware |
| `maxConcurrentConnections` | 100 | 500-5000 |
| `maxInFlightRequests` | 500 | Match thread pool |
| `maxStorageGB` | 10 | Size per tenant |

## See Also

- [Caching & Performance](caching.md) - Performance overview
- [Server Configuration](../reference/server-config.md) - Complete settings
- [Telemetry & Observability](telemetry.md) - Monitoring
