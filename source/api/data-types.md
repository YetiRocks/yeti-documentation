# Data Types

## Scalar Types

| GraphQL Type | Description | JSON Format | MessagePack Format |
|-------------|-------------|-------------|-------------------|
| `ID` | Unique identifier | String | String |
| `String` | UTF-8 text | String | String |
| `Int` | 64-bit signed integer | Number | Integer |
| `Float` | 64-bit IEEE 754 | Number | Float |
| `Boolean` | True or false | Boolean | Boolean |
| `Vector` | Embedding vector (f32 array) | Array of numbers | Array of f32 |

## Non-Null Modifier

Append `!` to make a field required. Optional fields default to `null` if omitted.

```graphql
type User @table @export {
    id: ID!            # Required
    name: String!      # Required
    bio: String        # Optional (nullable)
}
```

## ID Type

Stored as a string. Yeti generates **UUID v7** (time-ordered) when no ID is provided. Custom string IDs are supported.

```bash
# Auto-generated ID
curl -sk -X POST https://localhost:9996/my-app/User \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'

# Custom ID
curl -sk -X POST https://localhost:9996/my-app/User \
  -H "Content-Type: application/json" \
  -d '{"id": "alice-001", "name": "Alice"}'
```

## Date Handling

Store dates as ISO 8601 strings. Use `@createdTime` for automatic timestamps:

```graphql
type Message @table @export {
    id: ID! @primaryKey
    content: String!
    __createdAt__: String @createdTime
}
```

## Vector Type

Stores f32 embedding arrays. Declaring a `Vector` field automatically creates an HNSW index for similarity search.

```graphql
type Document @table @export {
    id: ID!
    content: String!
    embedding: Vector @indexed(source: "content")
}
```

In JSON, vectors are represented as arrays of numbers:

```json
{
  "id": "doc-1",
  "content": "Hello world",
  "embedding": [0.1, 0.2, 0.3, 0.4]
}
```

Dimensions are determined by the embedding model. Vector fields are excluded from MCP create/update schemas since they auto-generate from the source field. See [Vector Search](../guides/vector-search.md).

## Type Coercion

| Input | Target Type | Result |
|-------|-------------|--------|
| `"42"` | Int | `42` |
| `42` | String | `"42"` |
| `"true"` | Boolean | `true` |
| `1` / `0` | Boolean | `true` / `false` |

Coercion failures return a 400 validation error.

## See Also

- [Schema Directives](../reference/schema-directives.md) -- Directive reference
- [Vector Search](../guides/vector-search.md) -- Similarity search guide
- [REST API](rest.md) -- REST endpoint reference
