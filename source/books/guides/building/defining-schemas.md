# Defining Schemas

GraphQL schema definitions with custom directives define the data model. Four type-level directives control different concerns:

| Directive | Purpose |
|-----------|---------|
| `@table` | Declares a storage table with database namespace |
| `@export` | Exposes HTTP/MCP/MQTT endpoints and transport flags |
| `@distribute` | Topology: sharding, residency, replication, consistency |
| `@audit` | Compliance: which operations to log, retention, state capture |

## Schema Design

Each entity becomes a type with `@table`:

```graphql
type Product @table {
    id: ID! @primaryKey
    name: String!
    price: Float
}
```

### Queryable Tables

Add `@export` to expose HTTP endpoints. Without it, the table is internal-only (accessible from custom resources via `ctx.get_table("Name")`):

```graphql
type Product @table @export {
    id: ID! @primaryKey
    name: String!
    price: Float
}
```

### Transport Flags

`@export` accepts flags to control which transports are enabled. All default to `true` when `@export` is present:

```graphql
type Event @table @export(rest: true, graphql: true, sse: true, mqtt: true, mcp: true) {
    id: ID! @primaryKey
    payload: String!
}

# Disable MCP for an internal cache table
type InternalCache @table @export(mcp: false) {
    id: ID! @primaryKey
    data: String!
}
```

### Indexes for Filtering

Only index fields you actually filter on -- each index slows writes:

```graphql
type Book @table @export {
    id: ID! @primaryKey
    title: String!
    isbn: String! @indexed
    genre: String @indexed
    authorId: ID! @indexed
}
```

### Related Tables

Use `@relationship` to define joins between tables:

```graphql
# Many-to-one: look up Author where Author.id == this.authorId
author: Author @relationship(from: "authorId")

# One-to-many: find all Books where Book.authorId == this.id
books: [Book] @relationship(to: "authorId")
```

### Timestamps and Expiration

Track record lifecycle automatically:

```graphql
type Document @table @export {
    id: ID! @primaryKey
    content: String
    createdAt: String @createdTime    # Set on insert only
    modifiedAt: String @updatedTime   # Set on every write
}

type Session @table @export {
    id: ID! @primaryKey
    userId: String!
    expiresAt: Int @expiresAt         # Per-record TTL (Unix timestamp)
}
```

### Default Values

The `@default` directive sets a value when a field is omitted on create:

```graphql
type Task @table @export {
    id: ID! @primaryKey
    title: String!
    status: String @default(value: "pending")
    priority: Int @default(value: 0)
    visible: Boolean @default(value: true)
}
```

The value is type-checked against the field type at schema load time.

### CRDT Fields

The `@crdt` directive declares conflict-free replicated data types for fields that may be updated concurrently across replicas:

```graphql
type Counter @table @export @distribute {
    id: ID! @primaryKey
    views: Int @crdt(type: "counter")
    score: Int @crdt(type: "pn-counter")
    tags: String @crdt(type: "or-set")
}
```

| Type | Description |
|------|-------------|
| `counter` | Increment-only counter |
| `pn-counter` | Positive-negative counter (increment and decrement) |
| `or-set` | Observed-remove set (add/remove elements without conflicts) |

### Public Access

Tables can declare which operations bypass authentication using `@access(public: [...])`:

```graphql
type Chat @table @access(public: [read, create, subscribe]) {
    id: ID! @primaryKey
    message: String!
    author: String
    createdAt: String @createdTime
}
```

Values: `read`, `create`, `update`, `delete`, `subscribe`, `connect`, `publish`. Operations not listed still require authentication.

### Distribution Topology

The `@distribute` directive controls cluster behavior. Separate from `@table` to keep storage and topology concerns independent:

```graphql
type UserProfile @table @export @distribute(
    sharding: "hash",
    residency: "full",
    replicationFactor: 3,
    consistency: "strong"
) {
    id: ID! @primaryKey
    name: String!
    email: String @indexed
}

# Bare @distribute inherits cluster defaults
type Event @table @export @distribute {
    id: ID! @primaryKey
    payload: String!
}
```

| Parameter | Values | Default |
|-----------|--------|---------|
| `sharding` | `"hash"`, `"range"`, custom | none |
| `residency` | `"sharded"`, `"full"`, `"mirrored"`, `"adaptive"` | `"full"` |
| `replicationFactor` | 1-255 | cluster default |
| `consistency` | `"strong"`, `"eventual"` | `"eventual"` |
| `replication` | `"false"`, `"global"` | cluster default |

### Audit Trail

The `@audit` directive enables per-table audit logging. Audit entries are emitted fire-and-forget after successful writes:

```graphql
# Default: audit all mutations, 90-day retention, no state capture
type Payment @table @export @audit {
    id: ID! @primaryKey
    amount: Float!
    userId: String! @indexed
}

# Custom: audit reads too, keep forever, capture before/after state
type MedicalRecord @table @export @audit(
    operations: [read, create, update, delete],
    retention: 0,
    state: true
) {
    id: ID! @primaryKey
    patientId: String! @indexed
    content: String!
}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `operations` | `[create, update, delete]` | Which operations to audit; add `read` to opt in |
| `retention` | `90` | Retention in days; `0` = keep forever |
| `state` | `false` | Capture before/after record state on mutations |

### Vector Search

The `Vector` type with `@indexed(source: ...)` enables automatic embedding:

```graphql
type Document @table @export {
    id: ID! @primaryKey
    content: String
    embedding: Vector @indexed(source: "content")
}
```

See [Vector Search](vector-search.md) for tuning parameters and model selection.

## Complete Example

A multi-table schema using all four directives:

```graphql
type Author @table(database: "bookstore") @export(rest: true, graphql: true) {
    id: ID! @primaryKey
    name: String!
    email: String @indexed
    bio: String
    books: [Book] @relationship(to: "authorId")
}

type Book @table(database: "bookstore") @export(rest: true, graphql: true) @audit {
    id: ID! @primaryKey
    title: String!
    isbn: String! @indexed
    genre: String @indexed
    price: Float @default(value: 0.0)
    authorId: ID! @indexed
    author: Author @relationship(from: "authorId")
    reviews: [Review] @relationship(to: "bookId")
}

type Review @table(database: "bookstore") @export(rest: true, graphql: true) {
    id: ID! @primaryKey
    bookId: ID! @indexed
    rating: Int!
    content: String
    book: Book @relationship(from: "bookId")
}
```

## See Also

- [Schema Directives Reference](../reference/schema-directives.md) - Full directive parameters, field types, and HNSW tuning
- [Relationships & Joins](relationships.md) - Query examples for related tables
- [Vector Search](vector-search.md) - Embedding models and similarity queries
 models and similarity queries
