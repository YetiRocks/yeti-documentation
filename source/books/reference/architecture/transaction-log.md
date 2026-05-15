# Transaction Log

Every successful write through HTTP, WebSocket, MQTT, GraphQL, MCP,
or replication produces a `LogEntry` on a per-deployment append-only
RocksDB. Stamped with HLC, attributed to the originator, queryable
for audit. Landed YTC-203 (May 2026); replaces the older per-app
audit channel.

## Where it lives

```
{root_directory}/logs/transactions/{deployment_hash}/
```

One RocksDB per deployment. `deployment_hash` is the per-deployment
isolation key — same key used for cgroups, sockets, encryption keys.
Today it's hardcoded `"local"` until Fabric multi-deployment hosting
plumbs a real value through.

WAL is on; per-write fsync is **off** (`sync = false`). The log is
durable to the OS page cache on every write; survives process crash;
loses ~seconds on a power cut. Per-write fsync would dominate the
write path — not worth it for an audit feed.

## LogEntry shape

```rust,ignore
pub struct LogEntry {
    pub hlc: HlcTimestamp,                  // monotonic per-node
    pub node_id: String,
    pub table: TableId,                     // (database, table_name)
    pub op: WriteOp,                        // Put | Delete
    pub prev_hlc: Option<HlcTimestamp>,     // for HLC-LWW comparison
    pub prev_value: Option<Vec<u8>>,        // when @audit(state: true) is set
    pub originator: Originator,
    pub request_id: Option<String>,
    pub interface: Option<String>,          // rest / ws / mqtt / graphql / mcp / internal / replication
}
```

### Originator

```rust,ignore
pub enum Originator {
    /// Local request-pipeline write (user-driven).
    User { user: Option<String> },

    /// Internal write — bootstrap, seed loader, plugin lifecycle.
    Internal,

    /// Applied via the replication pipeline.
    Replication { node_id: String },
}
```

### Interface attribution

Every entry carries the protocol it came in on so audits can filter
by interface:

| Value | Source |
|---|---|
| `rest` | HTTP REST endpoint |
| `ws` | WebSocket subscription write |
| `sse` | (reads only — SSE doesn't write) |
| `mqtt` | MQTT publish |
| `graphql` | GraphQL mutation |
| `mcp` | MCP tool invocation |
| `internal` | Plugin / bootstrap / seed loader |
| `replication` | Applied from a peer |

Interface is threaded from the HTTP entry point down through
dispatch via a task-local. Bare backend writes (without a request
context) report `internal`.

## How it's wired

The `LoggingBackend` in `crates/foundation/yeti-store/` wraps every
per-table `KvBackend`. `create_rocksdb_backend_manager_logged()`
substitutes `LoggingBackend` for raw RocksDB at backend-manager
construction time — so every table gets the audit pipe by default
and there's no opt-in cost at the resource level.

```rust,ignore
// rough shape inside yeti-store
let inner: Arc<dyn KvBackend> = open_rocksdb_shards(...);
let logged: Arc<dyn KvBackend> = Arc::new(
    LoggingBackend::with_capture(inner, log, hlc, node_id, table, capture_state),
);
backend_manager.register(table, logged);
```

## Capture state — `@audit(state: true)`

Opt in per table to record the pre-write value alongside the entry:

```graphql
type Tickets @table @export @audit(state: true) { ... }
```

On every write, `LoggingBackend` reads the existing record first,
serializes it into `prev_value`, then performs the write. **Costs one
extra storage read per write** — opt in only on tables where
before/after diffing matters (compliance, fraud detection, etc.).

Per-write overhead at production scale (YTC-345 bench, 2026-05-12):
- Without capture: **+8.8 µs per write** (TransactionLog enabled, no state).
- With capture: above + ~1 RocksDB read (table cache size dependent).

## Reading the log

The unified `AuditResource` (in yeti-audit) queries the log on demand
through `TransactionLog::read_after(after: HlcTimestamp, limit: usize)`.
No per-app audit table — there's just the deployment log.

```
GET /yeti-audit/transactions?after=2026-05-14T00:00:00Z&limit=100
```

Filterable by `table`, `interface`, `user`, `op`, `request_id`, plus
free-text on the JSON-serialized record. See the
[Auditing guide](../../guides/observability/auditing.md) for query
patterns.

## Retention

Pruning is deployment-wide, not per-app:

```rust,ignore
TransactionLog::sweep(RetentionPolicy {
    max_age_secs: Some(90 * 24 * 3600),   // 90 days
    max_total_bytes: Some(50 * 1024 * 1024 * 1024),  // 50 GB
})
```

`None` disables that dimension. A `#[schedule(every = "6h")]` task
inside yeti-audit calls `sweep()` with the configured policy.

The per-table `@audit(retention:)` value is informational on read
queries — it doesn't drive pruning. Tighter per-table retention
requires reading the log and re-deriving a filtered view.

## Replaces the older audit channel

Pre-YTC-203 yeti had per-app audit tables: `auditlog` table, `AUDIT_BACKEND` channel,
`TABLE_AUDIT_SENDER`, `try_audit(...)`, `AuditContext`. **All of that
is deleted.** The unified TransactionLog is the only audit-side
primitive; do not reintroduce a separate audit pipe.

## See also

- [Storage Engine](storage.md) — `@store` and how durability tiers
  interact with the audit pipe (`memory`-tier tables are still logged)
- [Replication](replication.md) — replication writes are stamped
  with `Originator::Replication`
- [Schema Directives — `@audit`](../config/schema-directives.md) —
  `operations`, `retention`, `state` arguments
- [Auditing](../../guides/observability/auditing.md) — query patterns
