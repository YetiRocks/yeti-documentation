# Storage Engine

RocksDB key-value store, sharded per database. Each application gets
its own database namespace; data lives under `data/` in the root
directory.

```
~/yeti/data/{app-id}/
├── shard-0/
├── shard-1/
├── shard-2/
└── shard-3/
```

## Per-table tiers — `@store`

Storage behavior is per-table via `@store` (YTC-330). Four durability
tiers form a single ordered scale; each table picks one. Omit
`@store` to inherit the platform default (`"soft"`).

```graphql
# In-memory cache — wiped on restart
type Cache @table @export @store(durability: "memory", evictAfter: 600) { ... }

# Lossy — RocksDB without WAL, minutes-class loss window
type Metrics @table @export @store(durability: "lossy") { ... }

# Soft (default) — RocksDB + WAL + OS-controlled fsync
type Orders @table @export { ... }

# Strong — per-write fsync, 0-ms crash-loss window
type Tickets @table @export @store(durability: "strong") { ... }

# Bounded crash-loss between lossy and soft
type Sessions @table @export @store(durability: "soft", flushIntervalMs: 100) { ... }
```

| Value | Backend | Crash-loss window | Use when |
|---|---|---|---|
| `"memory"` | InMemory HashMap | everything (volatile) | Caches, ephemeral state |
| `"lossy"` | RocksDB, WAL off | ~minutes (memtable flush) | High-throughput append, fire-and-forget metrics |
| `"soft"` | RocksDB, WAL on, OS fsync | ~seconds | The default — fits 95% of tables |
| `"strong"` | RocksDB, WAL on, per-write fsync | 0 ms | Money, tickets, anything where loss is unacceptable |

### Other `@store` arguments

| Arg | Effect |
|---|---|
| `volume` | Override storage path (literal, `s3://...`, or a named volume from `yeti-config.yaml`) |
| `evictAfter` | Per-record TTL in seconds (replaces the older `@table(expiration:)`) |
| `flushIntervalMs` | Force a memtable flush every N ms — bounded crash-loss between `"lossy"` and `"soft"` |
| `compression` | Per-table override of the deployment default (`true` = LZ4) |

For finer per-record TTL, add `@expiresAt` to a Float field — that
overrides `evictAfter`.

## Sharding

Each database splits across `max(num_cpus / 2, 2)` RocksDB instances.
Keys are routed by consistent hash of the primary key. Each shard
runs its own write-ahead log, memtable, and compaction; they share
nothing.

For cluster-aware sharding (where shards live on different physical
nodes), see [Replication](replication.md) and the `@distribute`
directive in [Schema Directives](../config/schema-directives.md).

## Key encoding

Lexicographic binary, sort-order preserving:

```
{table_name}\x00{primary_key_bytes}
```

This shape lights up efficient point lookups, prefix scans, and range
queries. UUID v7 primary keys sort by creation time, so chronological
scans are local in the keyspace (one shard, one SST file family).

## Value encoding

**MessagePack** — 30–50% smaller than JSON, faster
encode/decode. Customers don't see this format; the SDK serializes
JSON in/out at the table boundary.

## BackendManager

Maps table names to sharded RocksDB instances. One `BackendManager`
per app; one sharded RocksDB per database. Plugin tables (auth,
audit, telemetry, vectors) merge into the app's manager at registration
so the app sees a unified namespace.

## KvBackend trait

The low-level interface tables sit on top of. Apps rarely use it
directly — go through `ctx.table()` instead, which gives you the
high-level `Table` API.

| Method | Description |
|---|---|
| `put(key, value)` | Single write |
| `get(key)` | Single read |
| `get_batch(keys)` | Batch read |
| `delete(key)` | Single deletion |
| `scan_prefix(prefix)` | Scan with values |
| `scan_keys(prefix)` | Scan keys only |
| `count_prefix(prefix)` | Count keys |
| `write_batch(ops)` | Atomic batch operations |
| `put_if(key, expected, new)` | CAS — write only if current matches `expected` |

## Server-wide tuning

Set in `yeti-config.yaml` under `storage:` (these apply to every
database; per-table `@store` overrides them):

| Field | Default | Description |
|---|---|---|
| `cache_size_mb` | 2048 | Block cache size per database |
| `write_buffer_size_mb` | 512 | Memtable size before flush |
| `shard_count` | `num_cpus / 2` | RocksDB shards per database |
| `compression` | `true` | LZ4 on SSTables |
| `path` | `data/` | Data directory (relative to root) |

## See also

- [Schema Directives — `@store`](../config/schema-directives.md) — full directive shape + arg table
- [Replication](replication.md) — cluster-aware placement (`@distribute`)
- [Transaction Log](transaction-log.md) — the write-side audit feed (YTC-203)
- [Table Access](../sdk/table-access.md) — `ctx.table()`, CAS via `put_if`
