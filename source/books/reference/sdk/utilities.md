# Utilities

Available via `use yeti_sdk::prelude::*`.

## HTTP Fetch

Plugin-safe HTTP client. Uses the host's reqwest client via an internal bridge, falling back to curl subprocess. `reqwest::blocking::Client` crashes in dylib plugins -- use this instead.

### fetch! macro

`fetch!` creates a `FetchBuilder`. Terminal methods (`.json()`, `.text()`, `.send()`) execute the request.

```rust,ignore
// Simple GET -> JSON
let data: Value = fetch!("https://api.example.com/data").json()?;

// POST with JSON body
let data: Value = fetch!("POST", "https://api.example.com/users")
    .header("Authorization", &format!("Bearer {token}"))
    .json_body(&json!({"name": "Alice"}))?
    .json()?;

// POST with form body
let resp = fetch!("POST", "https://oauth.example.com/token")
    .header("Content-Type", "application/x-www-form-urlencoded")
    .body("grant_type=authorization_code&code=abc")
    .send()?;

// GET -> text
let html: String = fetch!("https://example.com").text()?;

// Raw response (when you need status/headers)
let resp = fetch!("https://api.example.com/data").send()?;
if resp.ok() { /* ... */ }

// No redirects
let resp = fetch!("https://example.com/old").no_redirect().send()?;

// Custom timeout
let resp = fetch!("https://slow.example.com").timeout(5).send()?;
```

### FetchBuilder

```rust,ignore
pub struct FetchBuilder {
    // Created by fetch! macro -- use builder methods to configure
}

impl FetchBuilder {
    fn header(self, key: &str, value: &str) -> Self  // Add request header
    fn body(self, body: &str) -> Self                 // Set raw string body
    fn json_body(self, value: &Value) -> Result<Self> // Set JSON body + Content-Type
    fn no_redirect(self) -> Self                      // Disable following redirects
    fn timeout(self, seconds: u64) -> Self            // Set timeout (default: 30s)

    // Terminal methods (execute the request):
    fn json(self) -> Result<Value>                    // Send, ensure 2xx, parse JSON
    fn text(self) -> Result<String>                   // Send, ensure 2xx, return body
    fn send(self) -> Result<FetchResponse>            // Send, return raw response
}
```

### FetchResponse

```rust,ignore
pub struct FetchResponse {
    pub status: u16,                         // HTTP status code
    pub body: String,                        // Response body
    pub headers: HashMap<String, String>,    // Response headers (lowercase keys)
    pub url: String,                         // Final URL after redirects
    pub redirected: bool,                    // Whether response was redirected
}

impl FetchResponse {
    fn ok(&self) -> bool                     // true if 200-299
    fn ensure_ok(self) -> Result<Self>       // return self if 2xx, else error
    fn json(&self) -> Result<Value, String>  // parse body as JSON
    fn text(&self) -> &str                   // body as string
    fn bytes(&self) -> &[u8]                 // body as bytes
    fn header(&self, name: &str) -> Option<&str>  // get header (case-insensitive)
    fn status_text(&self) -> &str            // "OK", "Not Found", etc.
}
```

## Cookies

### CookieBuilder

Builds `Set-Cookie` header strings. Defaults: HttpOnly, Secure, SameSite=Lax, Path=/.

```rust,ignore
pub fn new(name: impl Into<String>, value: impl Into<String>) -> Self
pub fn max_age(self, seconds: u64) -> Self
pub fn path(self, path: impl Into<String>) -> Self
pub fn domain(self, domain: impl Into<String>) -> Self
pub fn secure(self, secure: bool) -> Self
pub fn http_only(self, http_only: bool) -> Self
pub fn same_site(self, same_site: SameSite) -> Self
pub fn build(self) -> String
pub fn delete(name: impl Into<String>) -> String   // helper: Max-Age=0
```

```rust,ignore
let cookie = CookieBuilder::new("session_id", &token)
    .max_age(3600)
    .path("/")
    .secure(true)
    .http_only(true)
    .same_site(SameSite::Lax)
    .build();

// Return response with cookie header
reply()
    .header("set-cookie", &cookie)
    .json(json!({"status": "logged in"}))

// Delete a cookie
let delete_cookie = CookieBuilder::delete("session_id");
reply()
    .header("set-cookie", &delete_cookie)
    .json(json!({"status": "logged out"}))
```

### CookieParser

Reads cookies from HTTP requests. Handles HTTP/2 split cookie headers (RFC 7540).

```rust,ignore
pub fn get_cookie<B>(req: &Request<B>, name: &str) -> Option<String>
pub fn get_session_id<B>(req: &Request<B>, cookie_name: &str) -> Option<String>
pub fn parse_all<B>(req: &Request<B>) -> HashMap<String, String>
```

```rust,ignore
let session = CookieParser::get_cookie(&request, "session_id");

// Tries cookie first, then X-Session-Id header
let session = CookieParser::get_session_id(&request, "yeti_session");

let all_cookies = CookieParser::parse_all(&request);
```

## Token Generation

Cryptographically secure random tokens via `rand`.

```rust,ignore
pub struct TokenGenerator;

impl TokenGenerator {
    pub fn generate(length: usize) -> String    // random hex token of N bytes
    pub fn csrf_token() -> String               // 32 bytes = 64 hex chars
}
```

```rust,ignore
let api_key = TokenGenerator::generate(32);   // 64 hex chars
let csrf = TokenGenerator::csrf_token();       // 64 hex chars
```

## ID Generation

```rust,ignore
pub fn generate_id() -> String       // UUID v7 (time-sortable)
pub fn generate_id_v7() -> String    // alias for generate_id()
```

Both return UUID v7 strings (time-ordered for database locality and chronological sorting).

```rust,ignore
let id = generate_id();
// "018e7a9f-3c4d-7890-abcd-ef1234567890"
```

## Timestamps

```rust,ignore
pub fn unix_timestamp() -> Result<u64>   // seconds since epoch (fallible)
pub fn now_secs() -> u64                 // seconds since epoch (infallible)
```

`unix_timestamp()` returns `Result<u64>` and requires the `?` operator:

```rust,ignore
let ts = unix_timestamp()?;
let ts = now_secs();  // no ? needed
```

## Composite Keys

Deterministic keys from multiple parts, joined with `::`:

```rust,ignore
pub fn composite_key(parts: &[&str]) -> String
pub fn composite_key_from(parts: &[impl AsRef<str>]) -> String
```

```rust,ignore
let key = composite_key(&["user-123", "2024-01-15", "metrics"]);
// "user-123::2024-01-15::metrics"
```

## CSV Parsing

Parses CSV bytes into JSON objects. Column headers become field names:

```rust,ignore
pub fn parse_csv(data: &[u8]) -> Vec<Value>
```

```rust,ignore
let items = parse_csv(&ctx.body);
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

## Bulk Import

Upserts multiple records with key extraction and validation:

```rust,ignore
pub async fn bulk_upsert(
    table: &Table,
    items: Vec<Value>,
    key_fn: impl Fn(&Value) -> Option<String>,
    validate_fn: impl Fn(&Value) -> Result<Value, &str>,
) -> Result<BulkResult>
```

```rust,ignore
let result = bulk_upsert(
    &table,
    items,
    |item| item["id"].as_str().map(|s| s.to_string()),
    |item| {
        item["name"].as_str().ok_or("missing name")?;
        Ok(item.clone())
    },
).await?;

reply().json(result.to_json("Imported"))
// {"message": "Imported", "created": 45, "updated": 3, "errors": [...]}
```

### Complete CSV import pipeline

```rust,ignore
resource!(Import {
    post(ctx) => {
        let table = ctx.get_table("Product")?;
        let body = ctx.require_json_body()?;
        let items = if let Some(arr) = body.as_array() {
            arr.clone()
        } else {
            parse_csv(&ctx.body)
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

## Validation

```rust,ignore
pub fn validate_identifier(id: &str, field_name: &str) -> Result<()>
```

Validates identifier characters. Returns `Err(YetiError::Validation)` if invalid.

```rust,ignore
validate_identifier("my-resource-id", "resourceId")?;
```

## Logging

Use `yeti_log!` in plugins. `tracing::info!` does not reach the host log from dylib context (TLS isolation).

```rust,ignore
yeti_log!(info, "Processing {} items", items.len());
yeti_log!(error, "Failed to import: {}", err);
yeti_log!(warn, "Cache miss for key={}", key);
yeti_log!(debug, "Value: {:?}", result);
yeti_log!(trace, "Entering handler");
```

Supported levels: `trace`, `debug`, `info`, `warn`, `error`.

## Quick Reference

| Function | Returns | Description |
|----------|---------|-------------|
| `fetch!(url)` / `fetch!(method, url)` | `FetchBuilder` | HTTP request builder (use `.json()`, `.text()`, or `.send()` to execute) |
| `generate_id()` | `String` | UUID v7 (time-sortable) |
| `generate_id_v7()` | `String` | Alias for `generate_id()` |
| `unix_timestamp()` | `Result<u64>` | Current unix timestamp (fallible) |
| `now_secs()` | `u64` | Current unix timestamp (infallible) |
| `composite_key(&[...])` | `String` | Join parts with `::` separator |
| `composite_key_from(&[...])` | `String` | Same, accepts `AsRef<str>` |
| `parse_csv(bytes)` | `Vec<Value>` | CSV bytes to JSON objects |
| `bulk_upsert(table, items, key_fn, validate_fn)` | `Result<BulkResult>` | Batch upsert with validation |
| `validate_identifier(id, field)` | `Result<()>` | Validate ID format |
| `TokenGenerator::generate(len)` | `String` | Random hex token |
| `TokenGenerator::csrf_token()` | `String` | 32-byte CSRF token |
| `CookieBuilder::new(name, value)` | `CookieBuilder` | Build Set-Cookie header |
| `CookieBuilder::delete(name)` | `String` | Delete-cookie header string |
| `CookieParser::get_cookie(req, name)` | `Option<String>` | Read cookie from request |
| `CookieParser::parse_all(req)` | `HashMap<String, String>` | All cookies from request |
| `delay(ms)` | `async` | Async sleep for N milliseconds |
| `delay_sync(ms)` | `()` | Blocking sleep for N milliseconds |
| `now_ms()` | `u64` | Current time in milliseconds since epoch |
