# Table Expiration

Yeti supports automatic record expiration (TTL) using RocksDB's built-in TTL compaction.

## Configuring Expiration

Set `expiration` (in seconds) on the `@table` directive:

```graphql
type Session @table(expiration: 3600) @export {
    id: ID! @primaryKey
    userId: String!
    token: String!
    createdAt: Int
}
```

## How It Works

1. RocksDB opens the column family with TTL enabled
2. Each record's creation time is tracked internally
3. During compaction, records exceeding the TTL are removed

Expiration is **not instantaneous** - records may persist slightly beyond the TTL until compaction runs.

## Per-Record Expiration

Use `@expiresAt` for per-record lifetimes:

```graphql
type OAuthSession @table(database: "yeti-auth") @export {
    sessionId: String @primaryKey
    provider: String
    accessToken: String
    refreshToken: String
    tokenExpiresAt: Int
    createdAt: Int
    expiresAt: Int @expiresAt  # Unix timestamp - record deleted after this
}
```

`@expiresAt` overrides table-level expiration for individual records.

## Notes

- Expiration is based on creation time. Updating a record resets the TTL.
- Expired records may briefly appear in queries until compaction runs.
- `@expiresAt` takes precedence over table-level `expiration`.
- Expired records are removed from both primary storage and indexes.

## See Also

- [Caching & Performance](caching.md) - Performance overview
- [Schema Directives](../reference/schema-directives.md) - Complete directive reference
- [Full-Page Caching](full-page-cache.md) - TTL in practice
