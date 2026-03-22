# Native Replication

Yeti includes a native replication system for distributing data across multiple nodes. Replication is a license-gated feature — without a valid license key, Yeti runs as a standalone single-node server.

## Overview

The replication system has three components:

- **Gossip-based discovery** — nodes find each other and exchange metadata using the chitchat protocol
- **gRPC WAL replication** — write-ahead log batches are pushed between nodes over gRPC with mTLS
- **Conflict resolution** — hybrid logical clocks (HLC) provide last-writer-wins ordering across nodes

All three components share a single port (default: 9997). Gossip runs over UDP and gRPC runs over TCP on the same port number.

## Consistency Model

Yeti uses **asynchronous replication with last-writer-wins conflict resolution**. Every write is stamped with a hybrid logical clock (HLC) timestamp that combines wall-clock time with a logical counter. When two nodes write to the same key concurrently, the write with the higher HLC timestamp wins.

This model provides:

- **Eventual consistency** — all nodes converge to the same state
- **Low-latency writes** — writes succeed locally without waiting for acknowledgment from peers
- **Partition tolerance** — nodes continue operating independently during network partitions; WAL batches catch up when connectivity restores

### CRDT Support

For data types that require conflict-free merging instead of last-writer-wins, Yeti includes built-in CRDT types:

- **Counter** — increment-only counter
- **PN-Counter** — increment/decrement counter
- **OR-Set** — observed-remove set

### Per-Table Consistency (Future)

The `@table` directive will support per-table consistency levels, allowing you to choose the right trade-off for each table:

```graphql
type UserProfile @table @export {
  id: ID! @primaryKey
  name: String!
  email: String!
}

type PageView @table @export {
  id: ID! @primaryKey
  url: String!
  count: Int!
}
```

Full replication (the default) means every node has a complete copy of every table. This is appropriate for most workloads where dataset size is manageable (under 10GB).

## Gossip-Based Node Discovery

Nodes discover each other through a gossip protocol based on [chitchat](https://github.com/quickwit-oss/chitchat). On startup, a node contacts one or more seed nodes to join the cluster. Gossip then propagates membership changes and metadata to all nodes.

Each node advertises via gossip:

- Node ID and address
- Provider and region (for topology-aware routing)
- Server capacity and current load
- Which applications and tables are hosted locally

Gossip metadata enables the replication layer to route WAL batches to the correct peers without a centralized registry.

## WAL Replication

Every write to RocksDB is recorded in the write-ahead log (WAL) with an HLC timestamp and the originating node ID. The async replicator pushes WAL batches to peer nodes over gRPC.

The replication protocol (defined in `replication.proto`) provides three RPC methods:

| RPC | Purpose |
|-----|---------|
| `Replicate` | Push WAL batches to a peer (primary replication path) |
| `Fetch` | Pull WAL batches from a peer (catch-up after restart) |
| `StreamWal` | Server-streaming RPC for continuous real-time replication |

A WAL batch contains:

```protobuf
message WalBatch {
  uint64 sequence = 1;    // WAL sequence number
  uint64 hlc = 2;         // HLC timestamp
  uint64 node_id = 3;     // Originating node
  string table = 4;       // Table name
  repeated KvOp ops = 5;  // Put/Delete operations
}
```

All operations in a batch are applied atomically on the receiving node.

### Catch-Up Replication

When a node restarts or temporarily loses connectivity, it uses `Fetch` to pull any missed WAL batches from peers. The `after_sequence` parameter tells the peer which batches the requesting node already has, so only new batches are sent.

## Shard Map and Distributed Routing

For large datasets where full replication is impractical, Yeti supports sharded replication with distributed query routing.

### Residency Modes

| Mode | Behavior |
|------|----------|
| **Full** | Every node has all data. Reads are always local. Default mode. |
| **Sharded** | Data partitioned by consistent hash. Each record lives on RF (replication factor) nodes. |
| **Mirrored(N)** | At least N copies guaranteed, with adaptive placement based on access patterns. |
| **Adaptive** | Standard sharding plus dynamic copies placed near where data is accessed most. |

### Distributed Query Routing

In sharded mode, a `DistSender` component routes reads and writes to the correct shard owner:

- **Point reads** — hash the key, find the shard owner, send a gRPC `Get` to that node
- **Prefix scans** — identify all shard owners for the table, send parallel `Scan` requests, merge sorted results (scatter-gather)
- **Local preference** — if the local node owns the shard, read directly from RocksDB without a network hop

The replication proto includes dedicated RPCs for shard routing:

```protobuf
service Replication {
  rpc Get(GetRequest) returns (GetResponse);
  rpc GetBatch(GetBatchRequest) returns (GetBatchResponse);
  rpc Scan(ScanRequest) returns (ScanResponse);
  // ... plus replication RPCs
}
```

## Configuration

Enable replication in `yeti-config.yaml`:

```yaml
replication:
  enabled: true
  licenseKey: "yeti-lic-v1.eyJ..."
  port: 9997
  seedNodes:
    - "peer1:9997"
    - "peer2:9997"
  region: "us-east"
  advertiseAddr: ""  # auto-detected if empty
  nodeId: null       # auto-generated if null
```

### Configuration Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable cluster replication |
| `licenseKey` | string | none | Ed25519-signed license key (required when enabled) |
| `port` | u16 | `9997` | Port for gRPC (TCP) and gossip (UDP) |
| `seedNodes` | string[] | `[]` | Addresses of seed nodes for cluster discovery |
| `region` | string | `""` | Region name for topology-aware routing |
| `advertiseAddr` | string | `""` | Address to advertise to peers (auto-detected if empty) |
| `nodeId` | string | auto | Unique node identifier |

### Single Port Design

Gossip (UDP) and gRPC replication (TCP) share the same port number. This simplifies firewall configuration — you only need to open one port for all replication traffic.

### Security

All inter-node communication uses mTLS with per-node X.509 certificates. This provides:

- Mutual authentication — both sides prove their identity
- Encryption in transit — all WAL batches and gossip messages are encrypted
- Per-node revocation — individual node certificates can be revoked without affecting the cluster

## License Gating

Replication requires a valid Ed25519-signed license key. The public key is embedded at compile time in the Yeti binary. Key validation is offline — no network call is needed.

Without a valid license key, the `replication` configuration section is ignored and Yeti runs as a standalone server. All other features (REST, GraphQL, gRPC, MCP, plugins, extensions) work without a license.

License keys encode:

- Customer identifier (wildcard for cloud fleet, specific for enterprise on-prem)
- Feature flags (replication, multi-tenant, build-server)
- Maximum node count
- Expiration date

Keys can be rotated without restart via configuration reload.
