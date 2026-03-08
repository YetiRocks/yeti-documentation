# Request Parsing

The SDK extends `http::Request<Vec<u8>>` with two trait extensions: `RequestBodyExt` for body parsing and `RequestExt` for metadata.

## Body Parsing (RequestBodyExt)

### json_value

Parse the body as a generic JSON value:

```rust,ignore
let body: Value = request.json_value()?;
let name = body["name"].as_str().unwrap_or("unknown");
```

### json

Parse the body into a typed struct:

```rust,ignore
#[derive(Deserialize)]
struct CreateUser {
    name: String,
    email: String,
}

let user: CreateUser = request.json()?;
```

### json_array (NEW)

Normalize a body that may be a single object or an array into a `Vec<Value>`:

```rust,ignore
let items: Vec<Value> = request.json_array()?;
```

Before this helper existed:

```rust,ignore
// Before
let items = match request.json_value()? {
    Value::Array(arr) => arr,
    obj => vec![obj],
};

// After
let items = request.json_array()?;
```

### json_field

Extract a nested field by dot-path:

```rust,ignore
let email: String = request.json_field("user.email")?;
```

### json_field_opt

Same as `json_field` but returns `None` instead of an error when missing:

```rust,ignore
let bio: Option<String> = request.json_field_opt("user.bio")?;
```

### body_bytes (NEW)

Access the raw request body as bytes:

```rust,ignore
let raw: &[u8] = request.body_bytes();
```

### Content type checks (NEW)

```rust,ignore
if request.is_csv() {
    let items = parse_csv(request.body_bytes());
    // ...
} else if request.is_json() {
    let items = request.json_array()?;
    // ...
}

// Generic check
if request.content_type_contains("application/xml") {
    // ...
}
```

## Request Metadata (RequestExt)

### Identity and routing

```rust,ignore
let req_id: String = request.id();           // Unique request ID
let ip: Option<String> = request.ip();        // Client IP address
let host: Option<String> = request.hostname(); // Request hostname
let path: Option<String> = request.path_id(); // Path segment after resource name
```

### Headers

```rust,ignore
let auth: Option<&str> = request.header_str("authorization");
let origin: Option<&str> = request.header_str("origin");
```

## Quick Reference

| Method | Returns | Description |
|--------|---------|-------------|
| `json_value()` | `Result<Value>` | Parse body as JSON value |
| `json::<T>()` | `Result<T>` | Parse body as typed struct |
| `json_array()` | `Result<Vec<Value>>` | Normalize single/array to vec |
| `json_field::<T>(path)` | `Result<T>` | Extract nested field by dot-path |
| `json_field_opt::<T>(path)` | `Result<Option<T>>` | Extract nested field, None if missing |
| `body_bytes()` | `&[u8]` | Raw request body bytes |
| `is_csv()` | `bool` | Content-Type is CSV |
| `is_json()` | `bool` | Content-Type is JSON |
| `content_type_contains(mime)` | `bool` | Content-Type contains string |
| `id()` | `String` | Request ID |
| `ip()` | `Option<String>` | Client IP |
| `hostname()` | `Option<String>` | Request hostname |
| `path_id()` | `Option<String>` | Path ID segment |
| `header_str(name)` | `Option<&str>` | Header value as string |
