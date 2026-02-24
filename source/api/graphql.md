# GraphQL API

Yeti auto-generates a GraphQL schema from tables with `@export(graphql: true)`.

## Endpoint

```
POST /{app-id}/graphql
```

Request body: `{"query": "...", "variables": {...}, "operationName": "..."}` with `Content-Type: application/json`.

## Queries

### List Records

```bash
curl -sk -X POST https://localhost:9996/my-app/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ Product { id name price category } }"}'
```

### Single Record

```graphql
{ Product(id: "prod-1") { id name price } }
```

### Pagination and Sorting

```graphql
{ Product(limit: 10, offset: 0, sort: "-price") { id name price } }
```

| Argument | Type | Description |
|----------|------|-------------|
| `id` | String | Fetch by primary key |
| `limit` | Int | Max records |
| `offset` | Int | Records to skip |
| `sort` | String | Sort field, prefix `-` for descending |

## Nested Relationships

When tables have `@relationship` directives, queries can traverse them:

```graphql
{
  User(id: "alice") {
    username
    role { id name }
  }
}
```

Reverse relationships work too:

```graphql
{
  Role(id: "admin") {
    name
    users { username }
  }
}
```

## Variables

```bash
curl -sk -X POST https://localhost:9996/my-app/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query GetProduct($id: String!) { Product(id: $id) { id name price } }",
    "variables": { "id": "prod-1" }
  }'
```

## Error Format

```json
{
  "data": null,
  "errors": [{ "message": "Resource not found: Product with id 'prod-999'", "path": ["Product"] }]
}
```

Partial success is possible - `data` may contain results for some fields while `errors` lists failures for others.

## Schema Introspection

```graphql
{ __schema { types { name fields { name type { name } } } } }
```

Browse interactively at `https://localhost:9996/graphql-explorer/`.

## Enabling GraphQL

Application-wide in `config.yaml`:

```yaml
graphql: true
```

Per-table via `@export(graphql: true)` in the schema.

## See Also

- [REST API](rest.md) - REST endpoint reference
- [Relationships & Joins](../guides/relationships.md) - Relationship modeling
- [Schema Directives](../reference/schema-directives.md) - Directive reference
