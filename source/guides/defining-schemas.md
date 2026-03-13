# Defining Schemas

Yeti uses GraphQL schema definitions with custom directives to define your data model. Types with `@table` become storage tables; `@export` makes them API endpoints.

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

### Public Access

Tables can declare which operations bypass authentication using `@export(public: [...])`:

```graphql
type Chat @table @export(public: [read, create, subscribe]) {
    id: ID! @primaryKey
    message: String!
    author: String
    createdAt: String @createdTime
}
```

Values: `read`, `create`, `update`, `delete`, `subscribe`, `connect`, `publish`. Operations not listed still require authentication.

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

A multi-table schema with relationships:

```graphql
type Author @table(database: "graphql-explorer") @export(rest: true, graphql: true) {
    id: ID! @primaryKey
    name: String!
    email: String @indexed
    bio: String
    books: [Book] @relationship(to: "authorId")
}

type Book @table(database: "graphql-explorer") @export(rest: true, graphql: true) {
    id: ID! @primaryKey
    title: String!
    isbn: String! @indexed
    genre: String @indexed
    price: Float
    authorId: ID! @indexed
    author: Author @relationship(from: "authorId")
    reviews: [Review] @relationship(to: "bookId")
}

type Review @table(database: "graphql-explorer") @export(rest: true, graphql: true) {
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
