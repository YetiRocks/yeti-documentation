# Replication

Cluster-aware data distribution. License-gated — without a valid
license, yeti runs standalone (every other feature works unchanged).

## Design principles

1. **Zero overhead when off.** A global `OnceLock<Sender>` with
   `None` means one pointer load per write.
2. **Near-zero overhead when on.** One `try_send` per write
   (~20 ns) posts a `WriteEvent` to the replication channel.
3. **Backend-agnostic.** RocksDB and InMemory tables hit the same
   notification point.
4. **Replicas skip the WAL.** The dedicated replication log is the
   durability source for remotely-applied writes; RocksDB WAL covers
   locally-originated writes only. Halves write amplification.
5. **Every node is simultaneously a writer and applier.** No
   primary / replica distinction. Conflict resolution is
   last-writer-wins by HLC; the `@crdt` field directive opts in to
   conflict-free types where merge semantics matter more than LWW.

## Architecture

```
Client write
  → Auth / routing / dispatch
  → TableResource
     → Schema enforcement, indexes, computed fields
     → KvBackend.put()                  [RocksDB or memory]
     → Ok                                [transaction committed]
     → replication::notify(table, op)    [fire-and-forget channel send]
  → Response (200/201/etc.)

Replication loop (background, decoupled):
  Receiver ← channel
     → BatchPackager (100 ops / 10 ms micro-batch)
     → ReplicationLog (append-only, dedicated file per deployment)
     → PeerSender    (persistent gRPC streams, one per peer)

Remote side:
  BatchReceiver
     → TableResolver routes to the destination KvBackend
     → KvBackend.put() with WAL disabled
     → AckTracker advances per-peer watermark
     → notify sender so it can GC its log up to the acked HLC
```

## Conflict resolution — HLC + LWW

Every write is stamped with a hybrid logical clock (HLC) combining
wall-clock milliseconds with a logical counter. Concurrent writes to
the same key resolve by highest HLC; ties break by sorted node id.
This gives:

- **Eventual consistency** — all nodes converge.
- **Low-latency writes** — local commit first, async replicate.
- **Partition tolerance** — independent operation during a split;
  anti-entropy resolves divergence on reconnect via an HLC-sidecar
  column family and a rolling XOR digest.

For state that needs richer merge semantics, use the field-level
`@crdt` directive (counter / pn-counter / or-set) from
[Schema Directives](../config/schema-directives.md).

## Membership — chitchat gossip

Peers discover each other via the [chitchat](https://github.com/quickwit-oss/chitchat)
protocol. On startup a node contacts the configured seed nodes; the
gossip layer propagates membership changes and per-node metadata
(region, advertised address, current load). The transport port
carries both gossip (UDP) and replication gRPC (TCP) — one firewall
rule covers both.

## Residency — `@distribute(residency:)`

Per-table replication shape. Different tables can live differently
inside the same cluster.

| Mode | Behavior |
|---|---|
| `"full"` | Every node has every record. Reads always local. Best for ≤10 GB tables and config/auth data. |
| `"sharded"` | Hash-partitioned across nodes; each record on `replicationFactor` nodes. Reads route via `DistSender`. |
| `"mirrored"` | At least `N` copies, adaptive placement. Hot data lands near the regions reading it. |
| `"adaptive"` | Standard sharding plus dynamic copies that follow access patterns. |

Sharded routing uses HRW (Highest Random Weight) hashing with 256
virtual nodes per peer for uniform distribution and bounded
migration on shard-map changes. The shard map is held by an openraft
consensus state machine — every node sees the same `ShardMap`.

## Consistency routing

Per-request consistency hint:

```
GET /my-app/Order/123          # default eventual (local replica)
X-Yeti-Consistency: strong     # routes to shard leader, waits for quorum
```

| Header value | Behavior |
|---|---|
| `eventual` (default) | Served by local replica — may be stale but fastest |
| `strong` | Routes to shard leader; returns only after quorum ack |

The response echoes `X-Yeti-Consistency` so clients can verify which
path served their read.

## Quorum writes — `put_confirmed`

For writes that need acknowledgement from a quorum of replicas
before returning success:

```rust,ignore
table.put_confirmed("order-123", record).await?;     // blocks until quorum acks
table.put_if_confirmed("order-123", expected, new).await?;  // CAS + quorum
```

`put_confirmed` is the durable-queue write path — claims, leases,
and exactly-once primitives all sit on top of it. The shard leader
collects acks from `replicationFactor / 2 + 1` replicas before the
caller sees `Ok`.

## Replica bootstrap — `yeti clone`

```bash
yeti clone --leader https://node-a.cluster.local:9997
```

Pulls config, joins gossip, replays the leader's replication log
from snapshot, and marks the new node `Ready` once the WAL has
caught up. Takes minutes for typical datasets; the node serves no
traffic until catchup completes.

## Observability

Replication emits standard `metrics::counter!` / `histogram!` /
`gauge!` records via yeti-telemetry. Key series:

| Metric | Type | Use |
|---|---|---|
| `yeti_repl_writes_total` | counter | Outbound writes by `(table, peer, result)` |
| `yeti_repl_batch_size` | histogram | Ops per batch (target 100) |
| `yeti_repl_batch_latency_ms` | histogram | End-to-end batch send + ack |
| `yeti_repl_peer_lag_hlc` | gauge | Per-peer HLC behind |
| `yeti_repl_log_bytes` | gauge | Replication log size on disk |
| `yeti_repl_backpressure_total` | counter | Pause events by peer |
| `yeti_repl_dlq_size` | gauge | Failed-batch dead-letter queue depth |
| `yeti_repl_dial_failures_total` | counter | Connection failures by peer |
| `yeti_repl_anti_entropy_runs_total` | counter | Reconciliation sweep count |

The admin dashboard at `/admin/cluster` surfaces these as a live
view: per-peer connection state, lag in HLC ms, throughput, recent
failures.

## Failover

When a node fails, gossip detects the loss within seconds and:

- Sharded tables: the shard map is rewritten via openraft consensus;
  reads/writes for that shard's keys reroute to a surviving replica.
- Full-residency tables: no rerouting needed (every node has every
  record).

**Tiebreaker.** When multiple candidates could take over, the
cluster picks by sorted hostname — deterministic, no thundering
herd, easy to reason about during incident review.

## mTLS — per-deployment CA

Each yeti deployment owns its CA. Node identity certs have a 90-day
lifetime; renewal happens before expiry via the cluster control
plane. The `BinaryAttestation` field on a node identity binds the
cert to a specific yeti binary hash — prevents a stolen cert from
being used by an out-of-band binary.

## Configuration

Top-level `replication:` in `yeti-config.yaml`:

```yaml
replication:
  enabled: true
  licenseKey: "yeti-lic-v1.eyJ..."
  port: 9997                          # TCP gRPC + UDP gossip (same port)
  seedNodes:
    - "peer1.cluster:9997"
    - "peer2.cluster:9997"
  region: "us-east"                   # for topology-aware routing
  advertiseAddr: ""                   # auto-detected if empty
  nodeId: null                        # auto-generated if null
  replicationFactor: 3                # writes wait for floor(N/2)+1 acks
  logRetentionDays: 7
  logMaxSizeMb: 1024
  backpressurePauseMs: 5000
  backpressureDisconnectMs: 30000
```

| Field | Default | Description |
|---|---|---|
| `enabled` | `false` | Master switch |
| `licenseKey` | none | Ed25519-signed license; **required** when `enabled: true` |
| `port` | `9997` | TCP (gRPC) + UDP (gossip) |
| `seedNodes` | `[]` | Bootstrap peer list |
| `region` | `""` | Topology-aware routing hint |
| `advertiseAddr` | `""` | Address to advertise (auto-detect when empty) |
| `nodeId` | auto | Unique node id |
| `replicationFactor` | `3` | Replicas per shard for `"sharded"` / `"mirrored"` residency |
| `logRetentionDays` | `7` | Replication log retention |
| `logMaxSizeMb` | `1024` | Log cap; oldest pruned on overflow |
| `backpressurePauseMs` | `5000` | Slow-peer pause threshold |
| `backpressureDisconnectMs` | `30000` | Slow-peer disconnect threshold |

### License gating

The license key encodes a `max_peers` cap, expiration, and feature
flags. Without a valid license, `max_peers = 0` — yeti accepts no
outbound peer dials and the cluster pipeline never starts. Every
other feature works. License keys rotate without restart via
configuration reload.

## See also

- [Schema Directives — `@distribute`](../config/schema-directives.md) — `sharding`, `shardKey`, `shardCount`, `residency`, `replicationFactor`, `consistency`
- [Storage Engine](storage.md) — `@store` durability tiers
- [Transaction Log](transaction-log.md) — YTC-203 unified write-side audit feed
- `crates/foundation/yeti-replication/` in the yeti repo — canonical implementation
