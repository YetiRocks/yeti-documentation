# Storage Engine

RocksDB key-value store. Each application gets its own database namespace with automatic sharding. Data always lives in `data/` under the root directory.

```yaml
storage:          # RocksDB storage (default, no config needed)
```

## Replication

Replication is configured via a top-level `replication:` section (not under `storage:`). It requires a valid license key (Ed25519-signed, offline verification).

```yaml
replication:
  enabled: true
  licenseKey: "your-license-key"
  port: 9997                    # TCP for gRPC, UDP for gossip
  seedNodes:
    - "peer1:9997"
    - "peer2:9997"
```

When enabled, the cluster coordinator starts, gossip discovers peers, and replication begins automatically. With no peers, the coordinator idles and the node runs standalone. There is no separate "embedded" vs "distributed" mode -- only one storage engine (RocksDB) exists.

## Sharding

Each database splits across `max(num_cpus / 2, 2)` RocksDB instances. Keys are distributed via consistent hash of the primary key.

```
data/my-app/
├── shard-0/
├── shard-1/
├── shard-2/
└── shard-3/
```

## Key Encoding

Lexicographic binary format preserving sort order: `{table_name}\x00{primary_key_bytes}`

Enables efficient point lookups, prefix scans, and range queries. UUID v7 keys sort by creation time.

## Value Encoding

**MessagePack** - 30-50% smaller than JSON, faster serialization.

## BackendManager

Maps table names to backend instances. One sharded RocksDB per database. Extension tables are merged via `with_merged_tables()` for extensions declared in the app's config.

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
| `storage.cacheSizeMb` | 2048 | Block cache size per database |
| `storage.writeBufferSizeMb` | 512 | Memtable size before flush |
| `storage.shardCount` | num_cpus / 2 | Number of RocksDB shards per database |
| `storage.compression` | false | LZ4 compression for SSTables |
| `storage.path` | `data/` | Data directory path |

`StorageConfig::high_performance()` enables async writes for 5-10x throughput.

## Table Expiration

```graphql
type PageCache @table(expiration: 3600) { ... }
```

Records older than the specified seconds are automatically cleaned up. Per-record TTL is also available via the `@expiresAt` field directive.
