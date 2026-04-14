# Schema Directives

All GraphQL schema directives for `schema.graphql` files. Directives control storage, indexing, exposure, distribution, and auditing.

---

## Type-Level Directives

### @table

Marks a type as a persistent table.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `database` | String | `"data"` | Database namespace |
| `table` | String | type name | Physical table name (if different from type name) |
| `storage` | String | `"rocksdb"` | Storage backend |
| `expiration` | Int | none | Table-wide TTL (seconds) |

```graphql
# Minimal — uses defaults
type Product @table {
    id: ID! @primaryKey
    name: String!
}

# Custom database and table name
type User @table(database: "yeti-auth", table: "users") {
    username: String! @primaryKey
    email: String!
}

# Ephemeral table with 1-hour TTL
type Session @table(expiration: 3600) {
    id: ID! @primaryKey
    token: String!
}
```

Without `@table`, a type is ignored by the schema loader.

---

### @export

Controls which interfaces expose the table and which operations are public. Without `@export`, the table exists internally but has no endpoints.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | String | type name | Custom endpoint path |
| `rest` | Boolean | `true` | REST CRUD endpoints |
| `graphql` | Boolean | `true` | GraphQL schema |
| `ws` | Boolean | `true` | WebSocket subscriptions |
| `sse` | Boolean | `true` | Server-Sent Events |
| `mqtt` | Boolean | `true` | MQTT publish/subscribe |
| `mcp` | Boolean | `true` | Model Context Protocol tools |
| `grpc` | Boolean | `true` | gRPC service |
| `public` | List | `[]` | Unauthenticated operations |

All flags default to `true` when `@export` is present. Set `false` to disable.

```graphql
# All interfaces enabled (defaults)
type Product @table @export {
    id: ID! @primaryKey
    name: String!
}

# Custom endpoint path: GET /myapp/rule instead of /myapp/Rule
type Rule @table @export(name: "rule") {
    id: ID! @primaryKey
    pattern: String!
}

# SSE-only streaming table
type LogEntry @table @export(rest: false, graphql: false, ws: false, sse: true, mqtt: false) {
    id: ID! @primaryKey
    message: String!
    timestamp: String @createdTime
}
```

#### Public Access

The `public` parameter declares operations that bypass authentication entirely.

| Value | Maps To | Description |
|-------|---------|-------------|
| `read` | GET | Read and list |
| `create` | POST | Create records |
| `update` | PUT | Update records |
| `delete` | DELETE | Delete records |
| `subscribe` | SSE | Change streams |
| `connect` | WebSocket | WebSocket connections |
| `publish` | MQTT | MQTT messages |

Unlisted operations still require authentication.

```graphql
# Anonymous reads and subscriptions, authenticated writes
type ChatMessage @table @export(public: [read, subscribe]) {
    id: ID! @primaryKey
    author: String!
    message: String!
    createdAt: String @createdTime
}

# Fully public table
type Announcement @table @export(public: [read, create, update, delete]) {
    id: ID! @primaryKey
    text: String!
}
```

---

### @distribute

Distribution topology for clustered deployments. Bare `@distribute` inherits cluster defaults.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sharding` | String | none | Sharding strategy: `"hash"` or `"range"` |
| `residency` | String | `"full"` | Data residency: `"sharded"`, `"full"`, `"mirrored"`, `"adaptive"` |
| `replicationFactor` | Int | cluster default | Number of replicas (1--255) |
| `consistency` | String | `"eventual"` | `"strong"` or `"eventual"` |
| `replication` | String | none | `"false"` to disable, `"global"` for all regions |

```graphql
# Strong consistency with 3 replicas
type Account @table @export @distribute(consistency: "strong", replicationFactor: 3) {
    id: ID! @primaryKey
    balance: Float!
}

# Hash-sharded with eventual consistency
type Event @table @export @distribute(sharding: "hash", residency: "sharded") {
    id: ID! @primaryKey
    payload: String!
}

# Node-local only, no replication
type Cache @table @export @distribute(replication: "false") {
    key: String! @primaryKey
    value: String!
}
```

---

### @audit

Compliance audit logging. Bare `@audit` logs all mutations, 90-day retention, no state capture.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `operations` | List | `[create, update, delete]` | Operations to audit |
| `retention` | Int | `90` | Retention in days (0 = forever) |
| `state` | Boolean | `false` | Capture before/after record state |

Available: `read`, `create`, `update`, `delete`. Read auditing excluded from defaults; opt in explicitly.

```graphql
# Default audit — log all mutations, 90-day retention
type Order @table @export @audit {
    id: ID! @primaryKey
    total: Float!
}

# Full audit trail with state capture and 1-year retention
type FinancialRecord @table @export @audit(
    operations: [read, create, update, delete],
    retention: 365,
    state: true
) {
    id: ID! @primaryKey
    amount: Float!
    account: String! @indexed
}

# Audit deletes only, keep forever
type Document @table @export @audit(operations: [delete], retention: 0) {
    id: ID! @primaryKey
    content: String!
}
```

Audit entries are emitted asynchronously after successful operations (timestamp, app ID, table, record ID, operation, identity). With `state: true`, before/after record snapshots are included.

---

### @compositeIndex

Multi-field index. Repeatable for multiple indexes. Index name auto-generated from field names.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fields` | String | yes | Comma-separated field names |

```graphql
type Product @table @export
    @compositeIndex(fields: "category,price")
    @compositeIndex(fields: "brand,category,rating")
{
    id: ID! @primaryKey
    category: String!
    brand: String!
    price: Float!
    rating: Float!
}
```

---

## Field-Level Directives

### @primaryKey

Primary key field. Every table needs exactly one. Defaults to `id` if omitted.

```graphql
type User @table @export {
    username: String! @primaryKey
    email: String!
}
```

### @indexed

Secondary index. Three types available.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | String | `"standard"` | Index type: `"standard"`, `"fulltext"`, or `"HNSW"` |
| `source` | String | none | Source field for auto-embedding (vector indexes only) |
| `model` | String | app default | Embedding model identifier (vector indexes only) |

**Standard index** (hash + range) -- for equality and range queries:

```graphql
email: String! @indexed
category: String @indexed
```

**Full-text search index** -- tokenized inverted index:

```graphql
body: String @indexed(type: "fulltext")
title: String @indexed(type: "fulltext")
```

**Vector index** -- HNSW algorithm for similarity search. The `Vector` field type automatically uses HNSW indexing even without explicit `type`:

```graphql
# Manual vectors (caller provides embedding data)
embedding: Vector

# Auto-embedding from a source field (requires yeti-ai)
embedding: Vector @indexed(source: "content")

# Auto-embedding with explicit model
embedding: Vector @indexed(source: "description", model: "BAAI/bge-small-en-v1.5")
```

Each index slows writes. Only index fields used in filters or searches.

### @relationship

Foreign key relationships for GraphQL joins and REST `?select` expansion.

| Parameter | Type | Description |
|-----------|------|-------------|
| `from` | String | Local field referencing the foreign table's primary key (many-to-one) |
| `to` | String | Foreign field referencing this table's primary key (one-to-many) |

Use `from` on the "many" side and `to` on the "one" side:

```graphql
type User @table @export {
    username: String! @primaryKey
    roleId: String @indexed
    role: Role @relationship(from: "roleId")
}

type Role @table @export {
    id: String! @primaryKey
    name: String!
    users: [User] @relationship(to: "roleId")
}
```

### @createdTime

Auto-populated with Unix epoch timestamp on record creation.

```graphql
createdAt: String @createdTime
```

### @updatedTime

Auto-populated with Unix epoch timestamp on every update.

```graphql
updatedAt: String @updatedTime
```

### @expiresAt

Per-record TTL expiration timestamp (Unix epoch). Overrides table-level `expiration`.

```graphql
expiresAt: Int @expiresAt
```

### @computed

Computed/derived field. Value calculated from an expression referencing other fields.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from` | String | yes | Expression to compute the field value |

```graphql
fullName: String @computed(from: "firstName + ' ' + lastName")
```

### @default

Default value when not provided on insert. Type-validated at schema parse time.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `value` | any | yes | Default value (must match field type) |

Supported types: `String`, `ID`, `Date` (stored as string), `Int`, `Float`, `Boolean`.

```graphql
status: String @default(value: "pending")
priority: Int @default(value: 0)
score: Float @default(value: 1.0)
active: Boolean @default(value: true)
```

Adding a `@default` field to an existing schema reconciles stored records on next access.

### @crdt

Conflict-free Replicated Data Type for automatic merge in distributed deployments.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | String | yes | CRDT type: `"counter"`, `"pn-counter"`, or `"or-set"` |

| CRDT Type | Description |
|-----------|-------------|
| `counter` | Increment-only counter |
| `pn-counter` | Increment and decrement counter (positive-negative) |
| `or-set` | Observed-remove set (add/remove elements, last-writer-wins on conflicts) |

```graphql
viewCount: Int @crdt(type: "counter")
score: Int @crdt(type: "pn-counter")
tags: String @crdt(type: "or-set")
```

---

## Field Types

| GraphQL Type | Storage Type | Notes |
|-------------|-------------|-------|
| `ID` / `ID!` | String | Typically with `@primaryKey` |
| `String` / `String!` | String | UTF-8 text |
| `Int` / `Int!` | i64 | 64-bit signed integer |
| `Float` / `Float!` | f64 | 64-bit floating point |
| `Boolean` / `Boolean!` | bool | true/false |
| `Vector` | Array of f32 | HNSW-indexed embedding vector |
| `[Type]` / `[Type!]!` | Array | For relationships |

The `!` suffix means the field is required (non-nullable).

---

## Comprehensive Example

A schema using all four type-level directives together:

```graphql
type Transaction @table(database: "finance", expiration: 7776000)
    @export(name: "transactions", rest: true, sse: true, mqtt: false, public: [read])
    @distribute(consistency: "strong", replicationFactor: 3, sharding: "hash")
    @audit(operations: [create, update, delete], retention: 365, state: true)
    @compositeIndex(fields: "accountId,createdAt")
    @compositeIndex(fields: "status,amount")
{
    id: ID! @primaryKey
    accountId: String! @indexed
    amount: Float!
    currency: String @default(value: "USD")
    status: String @default(value: "pending") @indexed
    memo: String @indexed(type: "fulltext")
    account: Account @relationship(from: "accountId")
    createdAt: String @createdTime
    updatedAt: String @updatedTime
    expiresAt: Int @expiresAt
}
```

---

## See Also

- [Defining Schemas](../guides/defining-schemas.md) -- Schema authoring guide
- [Application Configuration](app-config.md) -- Schema file configuration
- [Vector Search](../guides/vector-search.md) -- HNSW vector search guide
