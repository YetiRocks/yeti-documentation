# Storage Engine

RocksDB-based key-value store supporting **embedded** (single-node, default) and **cluster** (distributed) modes.

```yaml
storage:
  mode: embedded    # or "cluster"
```

## Embedded Mode

RocksDB runs in-process. Writes go to memtable, flush to SSTables, background compaction maintains read performance.

### Sharding

Each database splits across `max(num_cpus / 2, 2)` RocksDB instances. Keys distributed via consistent hash of the primary key.

```
data/my-app/
├── shard-0/
├── shard-1/
├── shard-2/
└── shard-3/
```

## Cluster Mode

Distributed cluster with automatic sharding, replication, and fault tolerance.

### Configuration

```yaml
storage:
  mode: cluster
  cluster:
    pdEndpoints:
      - "pd1:23791"
      - "pd2:23792"
      - "pd3:23793"
    timeoutMs: 5000
    autoStart: true     # Dev only - starts Docker cluster automatically
```

### Hot Cache

Each table has a local LRU cache (10,000 entries, max 64KB per value):
- Write-through: updated before writes reach cluster
- Negative caching: tracks non-existent keys
- Batch-aware: `get_batch()` checks cache first

### Connection Pool

Sized at `max(num_cpus / 2, 2)` persistent gRPC channels with round-robin distribution.

## Key Encoding

Lexicographic binary format preserving sort order: `{table_name}\x00{primary_key_bytes}`

Enables efficient point lookups, prefix scans, and range queries. UUID v7 keys sort by creation time.

## Value Encoding

**MessagePack** - 30-50% smaller than JSON, faster serialization.

## BackendManager

Maps table names to backend instances. In embedded mode, one sharded RocksDB per database. In cluster mode, key prefix isolation with shared connection pool.

Extension tables are merged via `with_merged_tables()` for extensions declared in the app's `extensions:` list.

## KvBackend Trait

| Method | Description |
|--------|-------------|
| `put(key, value)` | Single write |
| `get(key)` | Single read |
| `get_batch(keys)` | Batch read |
| `delete(key)` | Single deletion |
| `scan_prefix(prefix)` | Scan with values |
| `scan_keys(prefix)` | Scan keys only |
| `count_prefix(prefix)` | Count keys |
| `write_batch(ops)` | Atomic batch operations |

## Storage Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `cache_size_mb` | 2048 | Block cache size per database |
| `write_buffer_size_mb` | 512 | Memtable size before flush |
| `enable_compression` | false | LZ4 compression for SSTables |
| `sync_writes` | true | Sync WAL on every write |

`StorageConfig::high_performance()` enables async writes for 5-10x throughput.

## Table Expiration

```graphql
type PageCache @table(expiration: 3600) { ... }
```

Records older than the specified seconds are automatically cleaned up.
