# CRUD Operations

Examples use a `Product` table in `my-app`:

```graphql
type Product @table @export {
    id: ID! @primaryKey
    name: String!
    price: Float
    category: String @indexed
    inStock: Boolean
}
```

## Create (POST)

```bash
curl -sk https://localhost:9996/my-app/Product -X POST \
  -H "Content-Type: application/json" \
  -d '{"id":"prod-1","name":"Widget","price":9.99,"category":"hardware","inStock":true}'
```

Omit `id` for auto-generated UUID. POST an array for batch create.

## Read (GET)

```bash
# List all
curl -sk https://localhost:9996/my-app/Product

# Single record
curl -sk https://localhost:9996/my-app/Product/prod-1

# Filtered
curl -sk 'https://localhost:9996/my-app/Product?category==hardware'
curl -sk 'https://localhost:9996/my-app/Product?price=gt=10'
```

## Update (PUT) - Full Replace

All fields must be provided. Omitted fields become null.

```bash
curl -sk https://localhost:9996/my-app/Product/prod-1 -X PUT \
  -H "Content-Type: application/json" \
  -d '{"id":"prod-1","name":"Widget Pro","price":14.99,"category":"hardware","inStock":true}'
```

## Update (PATCH) - Partial

Only provided fields are updated; others preserved.

```bash
curl -sk https://localhost:9996/my-app/Product/prod-1 -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"price":12.99,"inStock":false}'
```

## Delete (DELETE)

```bash
curl -sk https://localhost:9996/my-app/Product/prod-3 -X DELETE
```

Returns 204 No Content on success.

## Status Codes

| Status | Meaning |
|--------|---------|
| 200 | Success (GET, PUT, PATCH) |
| 201 | Created (POST) |
| 204 | Deleted |
| 400 | Validation Error |
| 404 | Not Found |
| 405 | Method Not Allowed |
| 409 | Write Conflict |

## Error Responses

All error responses use RFC 9457 Problem Details format with content type `application/problem+json`:

```json
{
  "type": "urn:yeti:error:not_found",
  "title": "Not Found",
  "status": 404,
  "detail": "Record 'prod-999' not found in table 'Product'"
}
```

```json
{
  "type": "urn:yeti:error:validation_error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Missing required field: name"
}
```

```json
{
  "type": "urn:yeti:error:write_conflict",
  "title": "Write Conflict",
  "status": 409,
  "detail": "Concurrent write conflict on key 'prod-1'"
}
```

The `type` field is a stable URI for programmatic error handling. The `detail` field provides a human-readable explanation of the specific occurrence.

## Computed Fields

```graphql
type Article @table @export {
    id: ID! @primaryKey
    title: String!
    createdAt: String @createdTime   # Set on POST only
    updatedAt: String @updatedTime   # Set on every write
}
```
