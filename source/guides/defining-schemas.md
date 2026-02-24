# Defining Schemas

Yeti uses GraphQL schema definitions with custom directives to define your data model. Types with `@table` become storage tables; `@export` makes them API endpoints.

## Core Directives

### @table

Declares a persistent table:

```graphql
type Product @table {
    id: ID! @primaryKey
    name: String!
}

type Author @table(database: "graphql-explorer") {
    id: ID! @primaryKey
    name: String!
}

type PageCache @table(database: "full-page-caching", expiration: 3600) {
    path: String! @primaryKey
    pageContents: String
}
```

`database` groups tables logically. `expiration` sets TTL in seconds.

### @export

Controls API exposure:

```graphql
type Author @table(database: "graphql-explorer") @export(rest: true, graphql: true) {
    id: ID! @primaryKey
    name: String!
}
```

Without `@export`, the table has no HTTP endpoint but is accessible from custom resources via `ctx.get_table("Name")`.

### @primaryKey

Every table must have exactly one. Used for single-record lookups: `GET /{app}/{Table}/{id}`.

### @indexed

Creates a secondary index for efficient filtering:

```graphql
type Book @table @export {
    id: ID! @primaryKey
    title: String!
    isbn: String! @indexed
    genre: String @indexed
    authorId: ID! @indexed
}
```

#### Vector Index

```graphql
type Document @table @export {
    id: ID! @primaryKey
    content: String
    embedding: Vector @indexed(source: "content")
}
```

The `Vector` type automatically uses HNSW indexing -- no `type: "HNSW"` needed. See [Vector Search](vector-search.md) for tuning parameters and model selection.

### @relationship

#### `from` - Many-to-One

```graphql
# Look up Author where Author.id == this.authorId
author: Author @relationship(from: "authorId")
```

#### `to` - One-to-Many

```graphql
# Find all Books where Book.authorId == this.id
books: [Book] @relationship(to: "authorId")
```

See [Relationships & Joins](relationships.md) for query examples.

### @createdTime / @updatedTime

```graphql
type Document @table @export {
    id: ID! @primaryKey
    content: String
    createdAt: String @createdTime    # Set on insert only
    modifiedAt: String @updatedTime   # Set on every write
}
```

### @expiresAt

Per-record TTL as Unix timestamp:

```graphql
type Session @table @export {
    id: ID! @primaryKey
    userId: String!
    expiresAt: Int @expiresAt
}
```

## Field Types

| GraphQL Type | Description |
|-------------|-------------|
| `ID!` | Non-nullable identifier |
| `String` / `String!` | Nullable / required string |
| `Int` | Integer |
| `Float` | Floating-point |
| `Boolean` | Boolean |
| `Vector` | Embedding vector (HNSW-indexed) |
| `[String]` | String array |

## Complete Example

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
    publisherId: ID @indexed
    author: Author @relationship(from: "authorId")
    publisher: Publisher @relationship(from: "publisherId")
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
