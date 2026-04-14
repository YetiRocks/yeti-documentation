# Caching

Three caching strategies, chosen by access pattern.

## Decision Flowchart

```
Is the data an entire rendered page or API response?
  YES -> Full-page caching
  NO  -> Does the data expire after a fixed time?
    YES -> Table expiration (@expiresAt or table-level TTL)
    NO  -> In-memory read cache (automatic)
```

## Strategy 1: In-Memory Read Cache

**When to use**: Hot query results that are read far more often than written.

Yeti maintains an LRU cache in front of RocksDB by default. Writes automatically invalidate affected entries.

```yaml
storage:
  caching: true   # default, no action needed
```

Best for: lookup-heavy tables (user profiles, product catalogs, configuration).
No tuning required.

## Strategy 2: Table Expiration (@expiresAt)

**When to use**: Records that should automatically disappear after a time window -- sessions, tokens, rate-limit counters, temporary data.

Table-level TTL (all records expire after the same duration):

```graphql
type Session @table(expiration: 3600) @export {
    id: ID! @primaryKey
    token: String!
}
```

Per-record TTL (each record sets its own deadline):

```graphql
type Cache @table @export {
    id: ID! @primaryKey
    value: String
    expiresAt: Int @expiresAt   # Unix timestamp
}
```

See [Table Expiration](table-expiration.md) for details on cleanup behavior.

## Strategy 3: Full-Page Caching

**When to use**: Entire HTTP responses that are expensive to generate and can be served from cache on repeated requests -- rendered pages, aggregated API results, proxy responses.

Store the complete response keyed by URL path. On cache hit, return immediately without recomputation.

See [Full-Page Caching](full-page-cache.md) for the implementation pattern.

## Combined Strategies

Most production apps use all three:

- **Read cache** runs automatically for all table reads
- **Expiration** keeps sessions and temporary data from growing unbounded
- **Full-page cache** accelerates expensive rendered content

## Performance Impact

| Operation | Throughput | Notes |
|-----------|-----------|-------|
| Cached read | 186K ops/s | LRU hit, no disk I/O |
| Uncached read | ~80K ops/s | RocksDB disk read |
| Write (0 indexes) | 82K ops/s | Invalidates cache automatically |

See [Performance Benchmarks](../appendix/benchmarks.md) for detailed measurements.

## See Also

- [Full-Page Caching](full-page-cache.md) - HTTP content caching pattern
- [Table Expiration](table-expiration.md) - Automatic record TTL
- [Rate Limiting](rate-limiting.md) - Server-level throttling
- [Server Configuration](../reference/server-config.md) - All server settings
