# Schema Directives

Reference for all GraphQL schema directives. Directives control how types and fields are stored, indexed, and exposed.

## Type Directives

### @table

Marks a type as a persistent table.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `database` | string | app_id | Database name for storage isolation |
| `table` | string | type name | Custom table name |
| `storage` | string | `"rocksdb"` | Storage backend |
| `expiration` | integer | none | TTL in seconds |

```graphql
type User @table { ... }
type User @table(database: "yeti-auth") { ... }
type Session @table(expiration: 3600) { ... }
```

### @export

Controls which APIs expose this table. Without `@export`, the table is internal-only.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | string | type name | Custom endpoint path |
| `rest` | boolean | app default | Expose REST CRUD endpoints |
| `graphql` | boolean | app default | Include in GraphQL schema |
| `ws` | boolean | app default | Enable WebSocket subscriptions |
| `sse` | boolean | app default | Enable Server-Sent Events |
| `mqtt` | boolean | app default | Enable MQTT publish/subscribe |
| `public` | list | `[]` | Operations accessible without authentication |

```graphql
type User @table @export { ... }
type Rule @table @export(name: "rule") { ... }
type Log @table @export(sse: true) { ... }
```

#### Public Access

The `public` parameter declares which operations bypass authentication entirely -- no login, no token, no session required:

```graphql
type Chat @table @export(public: [read, create, subscribe]) {
    id: ID! @primaryKey
    message: String!
    author: String
    createdAt: String @createdTime
}
```

| Value | HTTP Method | Description |
|-------|------------|-------------|
| `read` | GET | Read records and list queries |
| `create` | POST | Create new records |
| `update` | PUT | Update existing records |
| `delete` | DELETE | Delete records |
| `subscribe` | GET (SSE) | Subscribe to change streams |
| `connect` | WebSocket | Establish WebSocket connections |
| `publish` | MQTT | Publish MQTT messages |

Operations not listed in `public` still require authentication. This is useful for tables that need anonymous reads but authenticated writes, or public chat rooms where anyone can post but only admins can delete.

## Field Directives

### @primaryKey

Designates the primary key. Every table needs exactly one. Typical types: `ID!`, `String`, `String!`.

```graphql
type User @table @export {
    id: ID! @primaryKey
    name: String!
}
```

### @indexed

Creates a secondary index for fast query lookups.

**Standard index** (hash + range):

```graphql
email: String! @indexed
```

**Full-text search index**:

```graphql
body: String @indexed(type: "fulltext")
```

**Vector index** (on `Vector` fields):

The `Vector` type automatically uses HNSW indexing. Adding `@indexed` with `source` enables auto-embedding:

```graphql
embedding: Vector @indexed(source: "content")
```

With explicit model:

```graphql
embedding: Vector @indexed(source: "content", model: "BAAI/bge-small-en-v1.5")
```

Without `source`, the field expects manual vector data on insert.

#### HNSW Tuning Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | string | - | Source field for auto-embedding (requires yeti-vectors) |
| `model` | string | app default or `BAAI/bge-small-en-v1.5` | Embedding model (only used with `source`) |
| `distance` | string | `"cosine"` | `"cosine"` or `"euclidean"` |
| `optimizeRouting` | float | `0.5` | Routing optimization aggressiveness (0.0–1.0) |
| `M` | integer | `16` | Max connections per node per layer |
| `efConstruction` | integer | `100` | Candidate list size during index build |
| `efSearchConstruction` | integer | `50` | Candidate list size during search |
| `mL` | float | `1/ln(M)` | Level generation normalization factor |

If `M` is set without `mL`, the value is auto-computed as `1/ln(M)`.

Each additional index slows writes. Only index fields used in filters.

### @relationship

Defines a relationship between tables for GraphQL joins and REST `?select` expansion.

| Parameter | Type | Description |
|-----------|------|-------------|
| `from` | string | Local field referencing the foreign table's primary key |
| `to` | string | Foreign field referencing this table's primary key (reverse) |

```graphql
type User @table @export {
    username: String @primaryKey
    roleId: String @indexed
    role: Role @relationship(from: roleId)
}

type Role @table @export {
    id: String @primaryKey
    users: [User] @relationship(to: roleId)
}
```

### @createdTime

Auto-populated with the creation timestamp (Unix epoch) on insert.

```graphql
__createdAt__: String @createdTime
```

### @updatedTime

Auto-populated with the current timestamp on every update.

```graphql
__updatedAt__: String @updatedTime
```

### @expiresAt

Per-record expiration timestamp (Unix epoch). Overrides table-level `expiration`.

```graphql
expiresAt: Int @expiresAt
```

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

## See Also

- [Defining Schemas](../guides/defining-schemas.md) - Schema authoring guide
- [Application Configuration](app-config.md) - Schema file configuration
- [Vector Search](../guides/vector-search.md) - HNSW vector search guide
