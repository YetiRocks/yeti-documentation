# REST API

Yeti generates REST endpoints for every table with `@export(rest: true)`.

## Base URL

```
https://localhost:9996/{app-id}/{TableName}
```

## Endpoints

### List Records

```
GET /{app-id}/{TableName}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Max records to return |
| `offset` | integer | Records to skip (pagination) |
| `sort` | string | Sort field, prefix `-` for descending |
| `select` | string | Comma-separated fields to include |
| `filter` | string | FIQL filter expression |
| `stream` | string | Set to `sse` for Server-Sent Events |

```bash
curl -sk "https://localhost:9996/my-app/Product?limit=10&sort=-createdAt&select=id,name,price"
```

### Create Record

```
POST /{app-id}/{TableName}
```

```bash
curl -sk -X POST https://localhost:9996/my-app/Product \
  -H "Content-Type: application/json" \
  -d '{"id": "prod-3", "name": "Doohickey", "price": 29.99}'
```

Returns `201 Created` with `{"message": "Record created", "id": "prod-3"}`.

### Read Record

```
GET /{app-id}/{TableName}/{id}
```

Returns 200 with the record, or 404 if not found.

### Replace Record

```
PUT /{app-id}/{TableName}/{id}
```

Replaces the entire record. All fields must be provided.

### Partial Update

```
PATCH /{app-id}/{TableName}/{id}
```

Updates specific fields without replacing the full record.

### Delete Record

```
DELETE /{app-id}/{TableName}/{id}
```

## FIQL Filtering

| Operator | Syntax | Description |
|----------|--------|-------------|
| Equal | `field==value` | Exact match |
| Not equal | `field!=value` | Exclude matches |
| Greater than | `field=gt=value` | Numeric/string comparison |
| Greater or equal | `field=ge=value` | Numeric/string comparison |
| Less than | `field=lt=value` | Numeric/string comparison |
| Less or equal | `field=le=value` | Numeric/string comparison |
| AND | `;` | Both conditions must match |
| OR | `,` | Either condition matches |
| Wildcard | `field==*value*` | Contains match |

```bash
curl -sk "https://localhost:9996/my-app/Product?filter=price=gt=10;price=lt=50&sort=-price&limit=5"
```

## Authentication

When yeti-auth is loaded, endpoints require authentication:

```bash
curl -sk -u admin:admin https://localhost:9996/my-app/Product
curl -sk -H "Authorization: Bearer eyJ..." https://localhost:9996/my-app/Product
```

Without yeti-auth, all endpoints are open.

## See Also

- [FIQL Queries](../guides/fiql.md) - Complete FIQL guide
- [Pagination & Sorting](../guides/pagination.md) - Pagination patterns
- [GraphQL API](graphql.md) - Alternative query interface
- [Error Codes](errors.md) - Error response format
