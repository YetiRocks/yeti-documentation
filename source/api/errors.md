# Error Codes

All errors return JSON: `{"error": "Human-readable message"}`.

## HTTP Status Codes

| Status | YetiError Variant | Description |
|--------|-------------------|-------------|
| 400 | `Validation(msg)` | Invalid input, malformed request, missing required fields |
| 400 | `Query(ParseError)` | Invalid FIQL filter syntax |
| 400 | `Schema(...)` | Invalid schema or type definition |
| 400 | `Encoding(...)` | JSON serialization error |
| 401 | `Unauthorized(msg)` | Authentication required or credentials invalid |
| 403 | `Forbidden(msg)` | Authenticated but insufficient permissions |
| 404 | `NotFound { resource_type, id }` | Resource does not exist |
| 409 | `Storage(WriteConflict)` | Concurrent write conflict (retryable) |
| 500 | `Storage(...)` / `Internal(msg)` | Database or unexpected error |
| 503 | - | Backpressure (maxInFlightRequests exceeded) |

## Using Errors in Resource Handlers

```rust
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

## Error Properties

All `YetiError` variants expose `status_code()`, `error_type()`, and `is_retryable()`.

Retryable errors: `Storage(Io(...))`, `Storage(WriteConflict(...))`, `Backend(NotAvailable(...))`.

## Sub-Error Types

### StorageError

| Variant | Description |
|---------|-------------|
| `KeyNotFound(key)` | Record not found |
| `WriteConflict(key)` | Optimistic locking failure |
| `Corruption(msg)` | Data corruption detected |
| `Io(err)` | File system I/O error |
| `RocksDb(msg)` | RocksDB-specific error |
| `InitializationFailed(msg)` | Database startup failure |

### QueryError

| Variant | Description |
|---------|-------------|
| `ParseError(msg)` | FIQL syntax error |
| `InvalidSelectField(msg)` | Unknown field in select |
| `InvalidSort(msg)` | Invalid sort expression |
| `InvalidPagination(msg)` | Invalid limit/offset |
| `TooComplex { reason }` | Query exceeds limits |

### SchemaError

| Variant | Description |
|---------|-------------|
| `ParseError(msg)` | GraphQL syntax error |
| `TableNotFound(name)` | Referenced table not defined |
| `FieldNotFound { table, field }` | Referenced field not defined |
| `InvalidDirective(msg)` | Invalid directive usage |
| `Duplicate(name)` | Duplicate type or field definition |

## Client Best Practices

1. Check HTTP status code first, then parse the error JSON body.
2. Implement exponential backoff for 503 and 409 responses.
3. Do not retry 400, 401, 403, or 404 errors.
4. Log full error responses for 500 errors.

## See Also

- [REST API](rest.md) - REST endpoint reference
- [Operations API](operations.md) - Administrative API
- [GraphQL API](graphql.md) - GraphQL error format
