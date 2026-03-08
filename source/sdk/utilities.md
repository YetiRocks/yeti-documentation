# Utilities

Helper functions and traits available via `use yeti_sdk::prelude::*;`.

## ID Generation

```rust,ignore
let id: String = generate_id();      // Random unique ID
let id: String = generate_id_v7();   // UUIDv7 (time-sortable)
```

## CSV Parsing (NEW)

Parse CSV bytes into a vector of JSON objects. Column headers become field names:

```rust,ignore
let items: Vec<Value> = parse_csv(request.body_bytes());
```

Input:

```csv
name,price,category
Widget,29.99,Tools
Gadget,49.99,Electronics
```

Output:

```json
[
  {"name": "Widget", "price": "29.99", "category": "Tools"},
  {"name": "Gadget", "price": "49.99", "category": "Electronics"}
]
```

## Bulk Import (NEW)

Upsert multiple records with validation:

```rust,ignore
let result: BulkResult = bulk_upsert(
    &table,
    items,
    |item| item["id"].as_str().map(|s| s.to_string()),  // key extractor
    |item| {                                               // validator
        item["name"].as_str().ok_or("missing name")?;
        Ok(item.clone())
    },
).await?;
```

`BulkResult` tracks successes and failures:

```rust,ignore
reply().json(result.to_json("Imported"))
// {"message": "Imported", "created": 45, "updated": 3, "errors": [...]}
```

### Complete CSV import pipeline

```rust,ignore
resource!(Import {
    post(request, ctx) => {
        let table = ctx.get_table("Product")?;
        let items = if request.is_csv() {
            parse_csv(request.body_bytes())
        } else {
            request.json_array()?
        };
        let result = bulk_upsert(&table, items,
            |item| item["id"].as_str().map(|s| s.to_string()),
            |item| {
                item["name"].as_str().ok_or("missing name")?;
                Ok(item.clone())
            },
        ).await?;
        reply().json(result.to_json("Imported"))
    }
});
```

## Composite Keys (NEW)

Build a deterministic key from multiple field values:

```rust,ignore
let key: String = composite_key(&["user-123", "2024-01-15", "metrics"]);
// "user-123::2024-01-15::metrics"
```

## JSON Helpers (JsonValueExt)

Extension trait on `serde_json::Value`:

```rust,ignore
let body = request.json_value()?;

// Dot-path access
let email: Option<&Value> = body.dot_get("user.contact.email");

// Required string field (returns YetiError::Validation if missing)
let name: &str = body.require_str("name")?;

// Typed access with defaults
let count: i64 = body.get_i64("count", 0);
let label: &str = body.get_str("label", "default");
```

## Validation

```rust,ignore
validate_identifier("my-resource-id", "resourceId")?;
// Returns Err(Validation) if ID contains invalid characters
```

## Cookies

### Cookie Reader

```rust,ignore
let session: Option<String> = CookieParser::get_cookie(&request, "session_id");
```

### Cookie Builder

```rust,ignore
let cookie = CookieBuilder::new("session_id", &token)
    .http_only(true)
    .secure(true)
    .same_site("Lax")
    .path("/")
    .max_age(3600)
    .build();

ctx.response_headers().append("set-cookie", &cookie);
```

## Timestamps

```rust,ignore
let ts: u64 = unix_timestamp()?;   // Seconds since epoch (Result<u64>)
let ts: u64 = now_secs();          // Seconds since epoch (plain u64)
```

Note: `unix_timestamp()` returns `Result<u64>` and requires the `?` operator.

## Logging

Use `yeti_log!` in plugins instead of `tracing::info!` (tracing macros do not reach the host log from dylib context):

```rust,ignore
yeti_log!(info, "Processing {} items", items.len());
yeti_log!(error, "Failed to import: {}", err);
yeti_log!(debug, "Cache hit for key={}", key);
```

## Quick Reference

| Function | Returns | Description |
|----------|---------|-------------|
| `generate_id()` | `String` | Random unique ID |
| `generate_id_v7()` | `String` | Time-sortable UUIDv7 |
| `parse_csv(bytes)` | `Vec<Value>` | CSV bytes to JSON objects |
| `bulk_upsert(table, items, key_fn, validate_fn)` | `Result<BulkResult>` | Batch upsert with validation |
| `composite_key(&[...])` | `String` | Join values with `::` separator |
| `validate_identifier(id, field)` | `Result<()>` | Validate ID format |
| `unix_timestamp()` | `Result<u64>` | Current unix timestamp |
| `now_secs()` | `u64` | Current unix timestamp (infallible) |
| `CookieParser::get_cookie(req, name)` | `Option<String>` | Read cookie value |
| `CookieBuilder::new(name, value)` | `CookieBuilder` | Build Set-Cookie header |
