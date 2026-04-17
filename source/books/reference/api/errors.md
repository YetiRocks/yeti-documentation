# Error Responses

All error responses use [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html) format.

## Response Format

Content-Type: `application/problem+json`

```json
{
  "type": "urn:yeti:error:not_found",
  "title": "not_found",
  "status": 404,
  "detail": "Resource not found: Product with id 'prod-999'"
}
```

| Field    | Description                                          |
|----------|------------------------------------------------------|
| `type`   | URI identifying the error category                   |
| `title`  | Error category label (matches `error_type` in code)  |
| `status` | HTTP status code                                     |
| `detail` | Human-readable explanation of this occurrence         |

## Error Type Reference

Every `YetiError` variant maps to a specific type URI, title, and HTTP status.

### Client Errors (4xx)

| HTTP | Type URI | Title | When |
|------|----------|-------|------|
| 400 | `urn:yeti:error:validation_error` | validation | Invalid input, malformed request, missing required fields |
| 400 | `urn:yeti:error:query_parse_error` | query | FIQL filter syntax error |
| 400 | `urn:yeti:error:query_error` | query | Invalid select, sort, pagination, or query too complex |
| 400 | `urn:yeti:error:schema_error` | schema | Schema parse error, missing table/field, invalid directive, duplicate definition |
| 400 | `urn:yeti:error:encoding_error` | encoding | JSON, MessagePack, UTF-8, key/value encoding errors |
| 401 | `urn:yeti:error:unauthorized` | unauthorized | Authentication required or credentials invalid |
| 403 | `urn:yeti:error:forbidden` | forbidden | Authenticated but insufficient permissions |
| 404 | `urn:yeti:error:not_found` | not_found | Resource does not exist |
| 409 | `urn:yeti:error:write_conflict` | storage | Concurrent write conflict (retryable) |

### Server Errors (5xx)

| HTTP | Type URI | Title | When |
|------|----------|-------|------|
| 500 | `urn:yeti:error:storage_error` | storage | Key not found in storage, corruption, I/O, RocksDB, WAL, or initialization failure |
| 500 | `urn:yeti:error:backend_error` | backend | Backend not available, initialization failed, config error, missing table mapping |
| 500 | `urn:yeti:error:index_error` | index | Index not found, corruption, update failure, scan error |
| 500 | `urn:yeti:error:config_error` | config | Configuration error |
| 500 | `urn:yeti:error:internal_error` | internal | Unexpected internal error |

## Error Properties

All errors expose three metadata fields used internally:

- `status_code` -- HTTP status code
- `error_type` -- category string for metrics and the `title` field
- `error_code` -- machine-readable code (e.g., `NOT_FOUND`, `WRITE_CONFLICT`)

## Retryable Errors

The following errors are safe to retry with exponential backoff:

- `urn:yeti:error:write_conflict` (409) -- optimistic locking failure
- `urn:yeti:error:storage_error` (500) -- when caused by transient I/O
- `urn:yeti:error:backend_error` (500) -- when backend is temporarily unavailable

## Errors in Resource Handlers

```rust,ignore
// 400 - static message
return Err(BadRequest("Email is required"))?;

// 400 - dynamic message
return Err(BadRequestOwned(format!("Invalid field: {}", name)))?;

// 401
return Err(Unauthorized("Authentication required"))?;

// 403
return Err(Forbidden("Admin access required"))?;

// 404
return Err(NotFoundError("Product not found"))?;
```

## Client Best Practices

1. Parse the `type` URI to identify the error category programmatically.
2. Display the `detail` field to users.
3. Implement exponential backoff for 409 and retryable 500 responses.
4. Do not retry 400, 401, 403, or 404 errors.
5. Log full Problem Details bodies for 500 errors.

## See Also

- [REST API](rest.md) -- REST endpoint reference
- [GraphQL API](graphql.md) -- GraphQL error format
- [MCP API](operations.md) -- MCP endpoint reference
