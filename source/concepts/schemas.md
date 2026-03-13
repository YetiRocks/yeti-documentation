# Schemas & Tables

Yeti uses GraphQL SDL to define tables, fields, indexes, and relationships. Yeti generates REST, GraphQL, and real-time endpoints from your schema.

## Example

```graphql
type Author @table(database: "my-app") @export(rest: true, graphql: true) {
    id: ID! @primaryKey
    name: String!
    email: String @indexed
    bio: String
    books: [Book] @relationship(to: "authorId")
}

type Book @table(database: "my-app") @export(rest: true, graphql: true) {
    id: ID! @primaryKey
    title: String!
    isbn: String! @indexed
    genre: String @indexed
    price: Float
    authorId: ID! @indexed
    author: Author @relationship(from: "authorId")
    reviews: [Review] @relationship(to: "bookId")
}

type Review @table(database: "my-app") @export(rest: true, graphql: true) {
    id: ID! @primaryKey
    bookId: ID! @indexed
    rating: Int!
    content: String
    reviewer: String
    book: Book @relationship(from: "bookId")
}
```

Reference schemas in `config.yaml`:

```yaml
schemas:
  - schema.graphql
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

## Type Directives

**`@table(database: "name")`** - Declares a persistent table in the named database.

**`@export`** - Exposes the table as API endpoints:

```graphql
type Product @table(database: "my-app") @export(rest: true, graphql: true) { ... }
```

Transport flags: `rest`, `graphql`, `ws`, `sse`, `mqtt` -- all default to `true` when `@export` is present. Without `@export`, the table exists internally but has no HTTP endpoints.

**`@export(public: [...])`** - Declares operations that bypass authentication:

```graphql
type Chat @table @export(public: [read, create, subscribe]) { ... }
```

Values: `read`, `create`, `update`, `delete`, `subscribe`, `connect`, `publish`.

## Field Directives

| Directive | Purpose |
|-----------|---------|
| `@primaryKey` | Record identifier. Every table needs one. |
| `@indexed` | Secondary index for fast FIQL filtering |
| `@relationship(from: "field")` | Belongs-to join (this table has the FK) |
| `@relationship(to: "field")` | Has-many join (other table has the FK) |
| `@createdTime` | Auto-set to Unix timestamp on creation |
| `@updatedTime` | Auto-set to Unix timestamp on every write |
| `@expiresAt` | TTL - records auto-delete after this time |

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

## Storage

Tables use [RocksDB](https://rocksdb.org/) with MessagePack serialization. Primary key lookups are sub-millisecond. `@indexed` fields use prefix-scanned column families for range queries.
