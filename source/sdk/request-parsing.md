# Request Parsing

The SDK extends `http::Request` with three trait extensions: `RequestBodyExt` for body parsing, `RequestExt` for request metadata, and `JsonValueExt` for working with JSON values.

## Body Parsing (RequestBodyExt)

Implemented on `Request<Vec<u8>>` and `Request<&[u8]>`.

### json\<T\>()

Parse the request body into a typed struct.

```rust,ignore
fn json<T: DeserializeOwned>(&self) -> Result<T>
```

```rust,ignore
#[derive(Deserialize)]
struct CreateUser {
    name: String,
    email: String,
}

let user: CreateUser = request.json()?;
```

Returns `Err(YetiError::Validation)` if the body is not valid JSON or does not match the target type.

### json_value()

Parse the body as a generic `serde_json::Value`.

```rust,ignore
fn json_value(&self) -> Result<Value>
```

```rust,ignore
let body: Value = request.json_value()?;
let name = body["name"].as_str().unwrap_or("unknown");
```

### json_array()

Normalize a body that may be a single object or an array into `Vec<Value>`:

```rust,ignore
fn json_array(&self) -> Result<Vec<Value>>
```

```rust,ignore
// Accepts both: {"name": "Alice"} and [{"name": "Alice"}, {"name": "Bob"}]
let items: Vec<Value> = request.json_array()?;
for item in &items {
    // process each item
}
```

### json_field\<T\>(path)

Extract a nested field by dot-path.

```rust,ignore
fn json_field<T: DeserializeOwned>(&self, path: &str) -> Result<T>
```

```rust,ignore
// Body: {"user": {"email": "alice@example.com"}}
let email: String = request.json_field("user.email")?;
```

Returns `Err(YetiError::Validation)` if the field is missing.

### json_field_opt\<T\>(path)

Same as `json_field` but returns `None` instead of an error when the field is missing.

```rust,ignore
fn json_field_opt<T: DeserializeOwned>(&self, path: &str) -> Result<Option<T>>
```

```rust,ignore
let bio: Option<String> = request.json_field_opt("user.bio")?;
```

### body_bytes()

Access the raw request body as bytes.

```rust,ignore
fn body_bytes(&self) -> &[u8]
```

```rust,ignore
let raw: &[u8] = request.body_bytes();
```

### Content type checks

```rust,ignore
fn is_csv(&self) -> bool
fn is_json(&self) -> bool
fn content_type_contains(&self, mime: &str) -> bool
```

```rust,ignore
if request.is_csv() {
    let items = parse_csv(request.body_bytes());
} else if request.is_json() {
    let items = request.json_array()?;
}

if request.content_type_contains("application/xml") {
    // handle XML
}
```

## Request Metadata (RequestExt)

Implemented on `Request<T>` for any body type. Provides access to request identity, routing, and headers.

### id()

Get the request ID. Uses the `X-Request-Id` header if present, otherwise generates a UUID v7.

```rust,ignore
fn id(&self) -> String
```

```rust,ignore
let req_id = request.id();
```

### ip()

Get the client IP address. Checks `X-Forwarded-For` first, then `X-Real-IP`.

```rust,ignore
fn ip(&self) -> Option<String>
```

```rust,ignore
let client_ip = request.ip().unwrap_or_else(|| "unknown".to_string());
```

### host() / hostname()

Get the request host. `hostname()` strips the port.

```rust,ignore
fn host(&self) -> Option<String>
fn hostname(&self) -> Option<String>
```

```rust,ignore
let host = request.host();         // Some("example.com:8080")
let name = request.hostname();     // Some("example.com")
```

### protocol()

Get the protocol. Checks `X-Forwarded-Proto`, defaults to `"https"`.

```rust,ignore
fn protocol(&self) -> &str
```

### original_url()

Get the request URI path (before internal routing).

```rust,ignore
fn original_url(&self) -> String
```

### param(key) / path_id()

Get a path or query parameter by key. `path_id()` is shorthand for `param("_path_id")`.

```rust,ignore
fn param(&self, key: &str) -> Option<String>
fn path_id(&self) -> Option<String>
```

### param_i64 / param_u64 / param_bool

Get typed parameters with defaults:

```rust,ignore
fn param_i64(&self, key: &str, default: i64) -> i64
fn param_u64(&self, key: &str, default: u64) -> u64
fn param_bool(&self, key: &str, default: bool) -> bool
```

`param_bool` recognizes `"true"`, `"1"`, `"yes"` as true and `"false"`, `"0"`, `"no"` as false.

### header_str(name)

Get a header value as a string.

```rust,ignore
fn header_str(&self, name: &str) -> Option<&str>
```

```rust,ignore
let auth = request.header_str("authorization");
let origin = request.header_str("origin");
```

## JSON Value Helpers (JsonValueExt)

Extension trait on `serde_json::Value` for ergonomic access with dot notation and defaults.

### Typed access with defaults

```rust,ignore
fn get(&self, path: &str, default: &str) -> String
fn get_i64(&self, path: &str, default: i64) -> i64
fn get_u64(&self, path: &str, default: u64) -> u64
fn get_f64(&self, path: &str, default: f64) -> f64
fn get_bool(&self, path: &str, default: bool) -> bool
```

```rust,ignore
let body = request.json_value()?;

let name = JsonValueExt::get(&body, "user.name", "anonymous");
let age = body.get_i64("user.age", 0);
let score = body.get_f64("metrics.score", 0.0);
let active = body.get_bool("flags.active", false);
```

### Optional access

```rust,ignore
fn opt_str(&self, path: &str) -> Option<&str>
fn opt_bool(&self, path: &str) -> Option<bool>
fn opt_u64(&self, path: &str) -> Option<u64>
```

### dot_get(path)

Get the raw `&Value` at a dot-separated path.

```rust,ignore
fn dot_get(&self, path: &str) -> Option<&Value>
```

```rust,ignore
let email = body.dot_get("user.contact.email").and_then(|v| v.as_str());
```

Supports nested objects, arrays (by index), and mixed access:

```rust,ignore
let data = json!({
    "teams": [{"name": "Engineering", "members": [{"name": "Alice"}]}]
});
let name = data.dot_get("teams.0.members.0.name"); // Some("Alice")
```

### require_str / require_i64 / require_u64 / require_bool

Get a required field, returning `Err(YetiError::Validation)` if missing.

```rust,ignore
fn require_str(&self, path: &str) -> Result<String>
fn require_i64(&self, path: &str) -> Result<i64>
fn require_u64(&self, path: &str) -> Result<u64>
fn require_bool(&self, path: &str) -> Result<bool>
```

```rust,ignore
let name = body.require_str("name")?;
let count = body.require_i64("count")?;
```

## Quick Reference

| Trait | Method | Returns | Description |
|-------|--------|---------|-------------|
| `RequestBodyExt` | `json::<T>()` | `Result<T>` | Parse body as typed struct |
| | `json_value()` | `Result<Value>` | Parse body as JSON value |
| | `json_array()` | `Result<Vec<Value>>` | Normalize single/array to vec |
| | `json_field::<T>(path)` | `Result<T>` | Extract nested field by dot-path |
| | `json_field_opt::<T>(path)` | `Result<Option<T>>` | Extract field, None if missing |
| | `body_bytes()` | `&[u8]` | Raw request body bytes |
| | `is_csv()` | `bool` | Content-Type contains "csv" |
| | `is_json()` | `bool` | Content-Type contains "json" |
| | `content_type_contains(mime)` | `bool` | Content-Type contains string |
| `RequestExt` | `id()` | `String` | Request ID (header or generated) |
| | `ip()` | `Option<String>` | Client IP |
| | `host()` | `Option<String>` | Host with port |
| | `hostname()` | `Option<String>` | Host without port |
| | `protocol()` | `&str` | "http" or "https" |
| | `original_url()` | `String` | Request URI path |
| | `param(key)` | `Option<String>` | Path/query parameter |
| | `path_id()` | `Option<String>` | Path ID segment |
| | `param_i64(key, default)` | `i64` | Integer parameter |
| | `param_u64(key, default)` | `u64` | Unsigned integer parameter |
| | `param_bool(key, default)` | `bool` | Boolean parameter |
| | `header_str(name)` | `Option<&str>` | Header value |
| `JsonValueExt` | `get(path, default)` | `String` | String with default |
| | `get_i64(path, default)` | `i64` | Integer with default |
| | `get_bool(path, default)` | `bool` | Boolean with default |
| | `dot_get(path)` | `Option<&Value>` | Raw value at path |
| | `require_str(path)` | `Result<String>` | Required string field |
