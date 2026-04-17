# Schemas & Tables

GraphQL SDL defines tables, fields, indexes, and relationships. Four type-level directives control identity, interfaces, topology, and compliance. Yeti generates REST, GraphQL, and real-time endpoints from the schema.

## Comprehensive Example

```graphql
type Author
    @table(database: "bookstore")
    @export(rest: true, graphql: true, sse: true, public: [read])
    @audit(operations: [create, update, delete], retention: 365, state: true)
{
    id: ID! @primaryKey
    name: String!
    email: String @indexed
    bio: String
    joinedAt: Float @createdTime
    updatedAt: Float @updatedTime
    books: [Book] @relationship(to: "authorId")
}

type Book
    @table(database: "bookstore")
    @export(rest: true, graphql: true, mcp: true)
    @distribute(sharding: "hash", replicationFactor: 3, consistency: "eventual")
{
    id: ID! @primaryKey
    title: String! @indexed
    isbn: String! @indexed
    genre: String @indexed @default(value: "uncategorized")
    price: Float @default(value: "0.0")
    authorId: ID! @indexed
    author: Author @relationship(from: "authorId")
    embedding: Vector @indexed(source: "title", model: "BAAI/bge-small-en-v1.5")
    reviews: [Review] @relationship(to: "bookId")
}

type Review
    @table(database: "bookstore", expiration: 31536000)
    @export(rest: true, public: [read, create])
{
    id: ID! @primaryKey
    bookId: ID! @indexed
    rating: Int!
    content: String
    reviewer: String
    votes: Int @crdt(type: "counter")
    createdAt: Float @createdTime
    expiresAt: Float @expiresAt
    book: Book @relationship(from: "bookId")
}
```

Reference schemas in `config.yaml`:

```yaml
schemas:
  path: "schemas/*.graphql"
```

## Data Types

| GraphQL Type | Storage |
|-------------|---------|
| `ID` / `ID!` | String key |
| `String` / `String!` | UTF-8 text |
| `Int` / `Int!` | 64-bit integer |
| `Float` / `Float!` | 64-bit float |
| `Boolean` / `Boolean!` | bool |
| `Date` | ISO 8601 string |
| `Vector` | Embedding vector (HNSW-indexed) |

The `!` suffix means non-nullable.

## Type-Level Directives

### `@table` -- Identity & Storage

Declares a persistent table.

```graphql
type Product @table(database: "shop", table: "products", expiration: 3600) { ... }
```

| Argument | Purpose | Default |
|----------|---------|---------|
| `database` | Database namespace | `"data"` |
| `table` | Physical table name | Type name |
| `storage` | Storage backend (`"rocksdb"`) | `"rocksdb"` |
| `expiration` | TTL in seconds for all records | None (no expiry) |

### `@export` -- Interfaces

Exposes the table as API endpoints. Without `@export`, the table exists internally but has no endpoints.

```graphql
type Product @table @export(rest: true, graphql: true, ws: false, mcp: true) { ... }
```

| Argument | Purpose | Default (when @export present) |
|----------|---------|---------|
| `rest` | REST API endpoints | `true` |
| `graphql` | GraphQL schema inclusion | `true` |
| `ws` | WebSocket subscriptions | `true` |
| `sse` | Server-Sent Events stream | `true` |
| `mqtt` | MQTT topic publishing | `true` |
| `mcp` | Model Context Protocol tool | `true` |
| `grpc` | gRPC tables service | `true` |
| `name` | Custom endpoint path | Lowercase type name |
| `public` | Operations bypassing auth | None |

**Public access** -- operations that skip authentication:

```graphql
type Chat @table @export(public: [read, create, subscribe]) { ... }
```

Values: `read`, `create`, `update`, `delete`, `subscribe`, `connect`, `publish`.

### `@distribute` -- Topology

Controls sharding, replication, and consistency for distributed deployments.

```graphql
type Session @table @export @distribute(sharding: "hash", residency: "sharded", replicationFactor: 3, consistency: "strong") { ... }
```

| Argument | Purpose | Default |
|----------|---------|---------|
| `sharding` | Strategy: `"hash"`, `"range"` | None |
| `residency` | Mode: `"full"`, `"sharded"`, `"mirrored"`, `"adaptive"` | `"full"` |
| `replicationFactor` | Number of replicas (1-255) | Cluster default |
| `consistency` | `"strong"` or `"eventual"` | `"eventual"` |

Bare `@distribute` with no arguments inherits cluster defaults.

### `@audit` -- Compliance

Enables audit logging for table operations.

```graphql
type Transaction @table @export @audit(operations: [create, update, delete], retention: 365, state: true) { ... }
```

| Argument | Purpose | Default |
|----------|---------|---------|
| `operations` | Which operations to audit | `[create, update, delete]` |
| `retention` | Retention period in days (0 = forever) | 90 |
| `state` | Capture before/after record snapshots | `false` |

Bare `@audit` uses defaults (all mutations, 90-day retention, no state capture). Audit entries are fire-and-forget and never block writes.

## Field Directives

| Directive | Purpose |
|-----------|---------|
| `@primaryKey` | Record identifier. Every table needs one. |
| `@indexed` | Secondary index for fast FIQL filtering |
| `@indexed(type: "fulltext")` | Full-text search index with tokenization |
| `@relationship(from: "field")` | Belongs-to join (this table has the FK) |
| `@relationship(to: "field")` | Has-many join (other table has the FK) |
| `@createdTime` | Auto-set to Unix timestamp on creation |
| `@updatedTime` | Auto-set to Unix timestamp on every write |
| `@expiresAt` | TTL -- records auto-delete after this time |
| `@default(value: "...")` | Default value injected when field is absent (type-validated at parse time) |
| `@crdt(type: "...")` | CRDT type for conflict-free replication (`"counter"`, `"pn-counter"`, `"or-set"`) |
| `@indexed(source: "field", model: "id")` | On a `Vector` field, auto-embed the source field using the named model (HNSW index) |
| `@computed(from: "expr")` | Virtual field computed at read time |
| `@compositeIndex(fields: "a,b")` | Multi-field composite index (type-level) |

## Generated Endpoints

Every `@export`ed table gets:

```
GET    /{app-id}/{Table}        # List/search
POST   /{app-id}/{Table}        # Create
GET    /{app-id}/{Table}/{id}   # Get by ID
PUT    /{app-id}/{Table}/{id}   # Replace
PATCH  /{app-id}/{Table}/{id}   # Partial update
DELETE /{app-id}/{Table}/{id}   # Delete
```

With `graphql: true`, the table is also queryable via `POST /{app-id}/graphql`.

With `sse: true`, changes stream via `GET /{app-id}/{Table}?stream=sse`.

## Storage

Tables use [RocksDB](https://rocksdb.org/) with MessagePack serialization. Primary key lookups are sub-millisecond. `@indexed` fields use prefix-scanned column families.
