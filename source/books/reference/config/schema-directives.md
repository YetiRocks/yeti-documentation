# Schema Directives

All GraphQL directives that drive table behavior. Each directive owns one
orthogonal axis — mix them freely. Bare `@table` is the only thing the
schema loader requires; everything else has sensible defaults.

```graphql
type Order
  @table
  @store(durability: "strong")
  @export(path: "/v1/orders")
  @access(public: [read])
  @audit(state: true)
  @distribute(sharding: "hash", shardKey: "tenantId", shardCount: 16)
{
  id: ID! @primaryKey
  tenantId: String! @indexed
  total: Float!
  createdAt: Float! @createdTime
}
```

## Type-level directives

| Directive | Axis | Required? |
|---|---|---|
| `@table` | Identity (database, table name) | Always — the marker |
| `@store` | Storage engine (durability, volume, eviction, compression) | Override only |
| `@source` | Where data comes from on miss (URL / fn / another table) | Cache-aside tables |
| `@distribute` | Replication topology (sharding, residency, replicas) | Clustered deploys |
| `@export` | Protocol exposure + URL path | To serve over HTTP |
| `@access` | Public ops + per-op RBAC | Override auth pipeline |
| `@audit` | Compliance: which ops, retention, state capture | Opt in |
| `@compositeIndex` | Multi-field index (repeatable) | Performance |

---

### `@table` — identity

```graphql
type Users @table(database: "auth", table: "users") { ... }
```

| Arg | Type | Default | Description |
|---|---|---|---|
| `database` | String | `"data"` | Database namespace (alias: `schema`) |
| `table` | String | type name | Physical RocksDB table name |

Bare `@table` is fine. `storage:` and `expiration:` moved to `@store`.

---

### `@store` — storage engine

```graphql
type Cache @table @export @store(durability: "lossy", evictAfter: 3600) { ... }
type Tickets @table @export @store(durability: "strong", flushIntervalMs: 100) { ... }
```

| Arg | Type | Default | Description |
|---|---|---|---|
| `durability` | String | `"soft"` | `"memory"` / `"lossy"` / `"soft"` / `"strong"` |
| `volume` | String | app default | Literal path, `s3://...`, or named volume from `yeti-config.yaml` |
| `evictAfter` | Int (seconds) | none | Per-record TTL (replaces `@table(expiration:)`) |
| `flushIntervalMs` | Int | none | Bounded crash-loss window between `"lossy"` and default |
| `compression` | Bool | deployment default | Per-table override |

**Durability tiers** (cost ↑, crash-loss ↓):

| Value | Backend | Crash-loss window |
|---|---|---|
| `"memory"` | InMemory (HashMap) | everything (volatile) |
| `"lossy"` | RocksDB, WAL off | ~minutes (memtable flush) |
| `"soft"` | RocksDB, WAL on, OS fsync (default) | ~seconds |
| `"strong"` | RocksDB, WAL on, per-write fsync | 0 ms |

---

### `@source` — origin

Cache-aside: where to fetch data when the table doesn't have it.
**Exactly one of `url:` / `function:` / `table:` is required.**

```graphql
# HTTP pull on miss
type Pages @table @export @source(
  url: "https://api.example.com/{id}"
  staleAfter: 60
  swr: 30
) { ... }

# Dylib-local Rust function
type Computed @table @export @source(function: "populate_view") { ... }

# Continuous sync from another yeti table (with optional projection)
type BannedTokens @table @export @source(
  table: "AggregatedTokens"
  function: "evaluatePolicy"
  propagateDeletes: false
  maxLag: 500
) { ... }
```

| Arg | Type | When | Description |
|---|---|---|---|
| `url` | String | url arm | HTTP endpoint with `{id}` substitution |
| `function` | String | function or table arm | Rust fn symbol (same dylib) |
| `table` | String | table arm | Source type name (same database) |
| `staleAfter` | Int (s) | url + function | Seconds before entry is stale |
| `swr` | Int (s) | url + function | Stale-while-revalidate window |
| `headers` | object | url | Static headers. Keys are GraphQL identifiers (`authorization:`, not `Authorization:`) |
| `propagateDeletes` | Bool | table, no function | Mirror source deletes (default `true`) |
| `maxLag` | Int (ms) | table | Backpressure source writes if destination lags |

Validators reject mixed arms, cyclic `table:` chains, and unresolved
references at schema load.

**Runtime status (2026-05-14):** only the `url:` arm has a runtime
implementation. `function:` and `table:` parse and validate but are
declarative-only — runtime work tracked in YTC-352.

---

### `@distribute` — replication topology

```graphql
type Events @table @export @distribute(
  sharding: "hash"
  shardKey: "tenantId"
  shardCount: 16
  consistency: "eventual"
) { ... }
```

| Arg | Type | Default | Description |
|---|---|---|---|
| `sharding` | String | none | `"hash"` / `"range"` / custom |
| `shardKey` | String | none | Field hashed/ranged on. **Required** for `"hash"` / `"range"` |
| `shardCount` | Int | cluster default | Explicit count (validated ≥ 2) |
| `residency` | String | none | `"sharded"` / `"full"` / `"mirrored"` / `"adaptive"` |
| `replicationFactor` | Int | cluster default | Replicas (1–255) |
| `consistency` | String | `"eventual"` | `"strong"` / `"eventual"` |
| `replication` | String | none | `"false"` disables; `"global"` for all regions |

---

### `@export` — protocol exposure

```graphql
type Articles @table @export(path: "/v1/articles", rest: true, mqtt: false) { ... }
```

All transport flags default to `true` when `@export` is present. Omit
`@export` entirely → no HTTP endpoints. Authorization moved to `@access`.

| Arg | Type | Default | Description |
|---|---|---|---|
| `path` | String | lowercased type name | URL segment under `{app}/{path}` (replaces `@export(name:)`) |
| `rest` | Bool | `true` | REST CRUD endpoints |
| `graphql` | Bool | `true` | Include in GraphQL schema |
| `ws` | Bool | `true` | WebSocket subscriptions |
| `sse` | Bool | `true` | Server-Sent Events |
| `mqtt` | Bool | `true` | MQTT topic |
| `mcp` | Bool | `true` | Expose as MCP tool |
| `grpc` | Bool | `true` | gRPC service |

Path conflicts (two types resolving to the same path) are refused at
schema load with both type names in the error.

---

### `@access` — authorization

```graphql
# Anonymous reads and subscribes; writes still need auth
type ChatMessage @table @export @access(public: [read, subscribe]) { ... }

# Per-op RBAC matrix
type Orders @table @export @access(
  public: [read]
  roles: { create: [client, admin], update: [admin], delete: [admin] }
) { ... }

# Per-(op, protocol) gating — admins update via REST or GraphQL only, never MQTT
type Vault @table @export @access(roles: {
  update: { rest: [admin], graphql: [admin] }
}) { ... }
```

| Arg | Type | Default | Description |
|---|---|---|---|
| `public` | List | `[]` | Ops anyone can perform without auth |
| `roles` | object | `{}` | Per-op (or per-(op, protocol)) RBAC matrix |

**Operations**: `read`, `create`, `update`, `delete`, `subscribe`, `connect`, `publish`.

**Protocols** (when nesting `roles`): `rest`, `graphql`, `ws`, `sse`, `mqtt`, `mcp`, `grpc`.

Omitting `@access` follows the app's auth pipeline. Public-everything is **not** the default.

---

### `@audit` — compliance

```graphql
# Defaults — log all mutations, 90 days, no state capture
type Orders @table @export @audit { ... }

# Forever retention with before/after state
type FinancialRecord @table @export @audit(
  operations: [read, create, update, delete]
  retention: 0
  state: true
) { ... }
```

| Arg | Type | Default | Description |
|---|---|---|---|
| `operations` | List | `[create, update, delete]` | `read` / `create` / `update` / `delete` |
| `retention` | Int (days) | `90` | `0` = forever |
| `state` | Bool | `false` | Capture before/after JSON (+1 read per write) |

Entries land on the unified TransactionLog (YTC-203), keyed by deployment hash.

---

### `@compositeIndex` — multi-field index

Repeatable at type level. Index name auto-generated.

```graphql
type Product @table @export
  @compositeIndex(fields: "category,price")
  @compositeIndex(fields: "brand,category,rating") { ... }
```

---

## Field-level directives

### `@primaryKey`

Every table needs exactly one. Defaults to `id: ID` if omitted (auto-UUID).

```graphql
id: ID! @primaryKey
username: String! @primaryKey   # alternate primary key
```

### `@indexed`

Three flavors. Each index slows writes — index only fields used in filters or searches.

```graphql
email: String! @indexed                          # standard hash + range index
title: String @indexed(type: "fulltext")          # tokenized inverted index
embedding: Vector @indexed                        # HNSW (auto for `Vector`)
embedding: Vector @indexed(source: "title,description", model: "all-MiniLM-L6-v2")
```

HNSW arguments: `distance` (`"cosine"` / `"euclidean"`), `M`, `efConstruction`, `efSearchConstruction`, `mL`, `optimizeRouting`, `source`, `model`.

### `@relationship`

```graphql
# Many-to-one: User has one Role
type User @table @export {
  roleId: String @indexed
  role: Role @relationship(from: "roleId")
}

# One-to-many: Role has many Users
type Role @table @export {
  id: String! @primaryKey
  users: [User] @relationship(to: "roleId")
}
```

| Arg | Description |
|---|---|
| `from` | Local field holding the foreign key (many side) |
| `to` | Foreign field referencing this table (one side) |

### `@createdTime` / `@updatedTime` / `@expiresAt`

Float fields. No arguments. Auto-populated.

```graphql
createdAt: Float! @createdTime
updatedAt: Float! @updatedTime
expiresAt: Float @expiresAt        # overrides @store(evictAfter:)
```

### `@computed`

```graphql
fullName: String @computed(from: "firstName + ' ' + lastName")
```

### `@default`

```graphql
status: String @default(value: "pending")
priority: Int @default(value: 0)
active: Boolean @default(value: true)
```

Supported: `String`, `ID`, `Date`, `Int`, `Float`, `Boolean`. Adding to an
existing schema reconciles stored records on next access.

### `@crdt`

Conflict-free replicated data types for cluster merge.

```graphql
viewCount: Int @crdt(type: "counter")
score: Int @crdt(type: "pn-counter")
tags: String @crdt(type: "or-set")
```

| Type | Description |
|---|---|
| `counter` | Increment-only |
| `pn-counter` | Increment / decrement |
| `or-set` | Observed-remove set (LWW on conflict) |

---

## Field types

| GraphQL | Storage | Notes |
|---|---|---|
| `ID` / `ID!` | String | Typical primary key |
| `String` | String | UTF-8 |
| `Int` | i64 | 64-bit signed |
| `Float` | f64 | 64-bit float |
| `Boolean` | bool | |
| `Vector` | `[f32]` | HNSW-indexed; needs yeti-ai for auto-embedding |
| `[Type]` | array | For `@relationship` |

`!` = required (non-nullable).

---

## See also

- [Defining Schemas](../../guides/building/defining-schemas.md) — authoring walkthrough
- [Application Configuration](app-config.md) — schema file wiring in `Cargo.toml`
- [Vector Search](../../guides/querying/vector-search.md) — HNSW + auto-embedding
