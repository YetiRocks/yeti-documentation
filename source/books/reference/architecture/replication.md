# Replication

Cluster-aware data distribution. License-gated — without a valid
license, `max_peers = 0` and yeti runs standalone (every other
feature works).

## Current state (2026-05)

| Capability | Status |
|---|---|
| 3-node binary mesh | **Shipped** (YTC-4 Phase 5, May 2026) |
| Streaming gRPC replicator with HLC-ordered batches | **Shipped** |
| Per-deployment mTLS CA + node certs | **Shipped** |
| Dedicated replication log (separate from RocksDB WAL) | **Shipped** |
| Backpressure: pause + disconnect thresholds | **Shipped** |
| Catch-up from snapshot or replay | **Shipped** |
| Chaos suite + 24-hour bake harness | **Shipped** (YTC-347) |
| Sharded residency, multi-region, quorum writes | Planned (see umbrella) |

The yeti-replication crate at `crates/foundation/yeti-replication/`
is the source of truth. This page summarizes the developer-facing
surface.

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
   last-writer-wins by HLC.

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
the same key resolve by highest HLC; ties break by node ID. This
gives:

- **Eventual consistency** — all nodes converge.
- **Low-latency writes** — local commit first, async replicate.
- **Partition tolerance** — independent operation during a split;
  catchup resolves divergence on reconnect.

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

## Backpressure

`backpressure_pause_ms` is the threshold at which the sender stops
appending to the replication log and waits for the slowest peer to
catch up. `backpressure_disconnect_ms` is the threshold at which the
sender drops the slow peer entirely and lets gossip re-elect a
sync target.

## Transaction Log integration

Yeti's [Transaction Log](transaction-log.md) (YTC-203) is a per-deployment
audit feed of every successful write. Replication reads from the same
notification channel but writes to its own log (replication-internal,
distinct from the audit-facing transaction log). The two pipelines
coexist without contending.

## mTLS — per-deployment CA

Each yeti deployment owns its CA. Node identity certs have a 90-day
lifetime; renewal happens before expiry via the cluster control plane.
The `BinaryAttestation` field on a node identity binds the cert to a
specific yeti binary hash — prevents a stolen cert from being used by
an out-of-band binary.

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
  logRetentionDays: 7
  logMaxSizeMb: 1024
  backpressurePauseMs: 5000
  backpressureDisconnectMs: 30000
  maxPeers: 0                         # 0 = unlicensed (standalone)
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
| `logRetentionDays` | `7` | Replication log retention |
| `logMaxSizeMb` | `1024` | Log cap; oldest pruned on overflow |
| `backpressurePauseMs` | `5000` | Slow-peer pause threshold |
| `backpressureDisconnectMs` | `30000` | Slow-peer disconnect threshold |
| `maxPeers` | `0` | License-gated peer cap; `0` = no outbound dials |

### `max_peers` as the license lever

The license key encodes a `max_peers` cap. Without a valid license,
`max_peers = 0` — yeti accepts no outbound peer dials, and the
cluster pipeline never starts. Every other feature works. This is the
single line that gates clustering: replication code paths compile and
the rest of the schema directives (`@distribute`, etc.) parse, but
the runtime refuses to talk to peers.

The cap can be rotated by replacing the license key (configuration
reload, no restart required).

## Residency modes (`@distribute(residency:)`)

| Mode | Behavior | Status |
|---|---|---|
| `"full"` | Every node has every record. Reads always local. | **Default**; shipped |
| `"sharded"` | Hash-partitioned across nodes; each record on `replicationFactor` nodes | Planned |
| `"mirrored"` | At least N copies, adaptive placement | Planned |
| `"adaptive"` | Standard sharding + dynamic locality-following copies | Planned |

Full residency works for most workloads where the dataset fits one
node (~10 GB rule of thumb). Sharded mode + distributed query routing
land in YTC-141's followup.

## See also

- [Storage Engine](storage.md) — `@store` durability tiers
- [Transaction Log](transaction-log.md) — YTC-203 unified audit feed
- [Schema Directives — `@distribute`](../config/schema-directives.md) — sharding + replication topology
- `crates/foundation/yeti-replication/` in the yeti repo — canonical implementation
