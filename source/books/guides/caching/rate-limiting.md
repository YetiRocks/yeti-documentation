# Rate Limiting

## Configuration

```yaml
rateLimiting:
  maxRequestsPerSecond: 1000
```

## Request Rate

`maxRequestsPerSecond` caps overall throughput. Returns `429 Too Many Requests` when exceeded. Server-wide across all apps and clients.

## Backpressure

```yaml
http:
  maxInFlightRequests: 10000
```

Returns `503 Service Unavailable` when in-flight requests exceed the threshold. Unlike rate limiting (throughput cap), backpressure limits concurrency.

## Timeouts

```yaml
http:
  timeout: 60000          # Request timeout (ms), default 60s
  keepAliveTimeout: 75000 # Idle connection timeout (ms), default 75s
```

## Error Responses

- **429**: Rate limit exceeded (ProblemDetails with `urn:yeti:error:rate_limited`)
- **503**: Server overloaded (ProblemDetails with `urn:yeti:error:overloaded`)

### Example 429 Response

```bash
$ curl -sk -w "\nHTTP %{http_code}\n" https://localhost:9996/my-app/MyTable
{"type":"urn:yeti:error:rate_limited","title":"Too Many Requests","status":429,"detail":"Rate limit exceeded. Maximum 1000 requests per second."}
HTTP 429
```

### Retry with Exponential Backoff (JavaScript)

```javascript
async function fetchWithRetry(url, opts = {}, retries = 3) {
  for (let i = 0; i <= retries; i++) {
    const res = await fetch(url, opts);
    if (res.status !== 429 && res.status !== 503) return res;
    await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)));
  }
  throw new Error(`Failed after ${retries} retries`);
}
```

## What Is Rate-Limited

| Endpoint Type | Rate-Limited | Notes |
|---------------|-------------|-------|
| REST CRUD (`/app/Table`) | Yes | Subject to `maxRequestsPerSecond` |
| SSE streams | Yes (connection) | Counts against `maxInFlightRequests` |
| WebSocket | Yes (connection) | Counts against `maxInFlightRequests` |
| Health check (`/health`) | No | Always available for monitoring |
| Static files | Yes | Same rate limit as API requests |

## Production Settings

| Setting | Dev | Production |
|---------|-----|------------|
| `rateLimiting.maxRequestsPerSecond` | 1000 | Tune to hardware |
| `http.maxInFlightRequests` | 10000 | Match thread pool |

## See Also

- [Caching & Performance](caching.md) - Performance overview
- [Server Configuration](../reference/server-config.md) - Complete settings
- [Telemetry & Observability](telemetry.md) - Monitoring
