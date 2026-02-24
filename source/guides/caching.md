# Caching & Performance

## Table-Level Caching

When `storage.caching` is enabled (the default), Yeti maintains an in-memory LRU read cache in front of RocksDB.

```yaml
storage:
  caching: true
```

Writes automatically invalidate cache entries. No additional configuration needed.

## Full-Page Caching

Store entire HTTP responses keyed by URL path. On cache hit, return immediately; on miss, fetch and store.

See [Full-Page Caching](full-page-cache.md) for implementation details.

## Table Expiration (TTL)

Configure automatic record expiration:

```graphql
type Session @table(expiration: 3600) @export {
    id: ID! @primaryKey
    userId: String!
    token: String!
}
```

See [Table Expiration](table-expiration.md) for details.

## Rate Limiting

```yaml
rateLimiting:
  maxRequestsPerSecond: 1000
  maxConcurrentConnections: 100
  maxStorageGB: 10
```

Returns HTTP 503 when overloaded. See [Rate Limiting](rate-limiting.md).

## Compression

Responses above `compressionThreshold` are gzip-compressed automatically:

```yaml
http:
  compressionThreshold: 1024  # bytes
```

Clients must send `Accept-Encoding: gzip`.

## Performance Tuning Checklist

1. **Enable caching** - `storage.caching: true` (default)
2. **Index selectively** - only `@indexed` fields you filter on; each index slows writes
3. **Use TTL** - prevent unbounded table growth
4. **Set rate limits** - protect against runaway clients
5. **Tune threads** - `threads.count` matching CPU cores
6. **Enable compression** - reasonable `compressionThreshold` for API traffic
7. **Monitor** - use the telemetry dashboard to identify slow queries

## Performance Characteristics

| Operation | Throughput (no indexes) | Notes |
|-----------|------------------------|-------|
| Read | 186K ops/s | Direct RocksDB with caching |
| Create | 82K ops/s | Single write path |
| Mixed (70R/30W) | 156K ops/s | Typical workload pattern |
| With 1 index | 25K creates/s | Trade-off for query speed |
| With 2 indexes | 15K creates/s | Only index what you filter on |

See [Performance Benchmarks](../reference/benchmarks.md) for detailed measurements.

## See Also

- [Full-Page Caching](full-page-cache.md) - HTTP content caching pattern
- [Table Expiration](table-expiration.md) - Automatic record TTL
- [Rate Limiting](rate-limiting.md) - Server-level throttling
- [Server Configuration](../reference/server-config.md) - All server settings
