# ResourceParams

The `ResourceParams` struct (typically named `ctx` or `params` in handlers) provides access to path parameters, query parameters, tables, configuration, authentication, extensions, and response headers.

## Path Parameters

```rust,ignore
fn id(&self) -> Option<&str>
fn path_id(&self) -> Option<&str>
fn require_id(&self) -> Result<&str>
```

For a request to `GET /app/Product/abc-123`:
- `ctx.id()` returns `Some("abc-123")`
- `ctx.path_id()` returns `Some("abc-123")` (alias for `id()`)
- `ctx.require_id()` returns `Ok("abc-123")`, or `Err(Validation)` if no ID in path

```rust,ignore
resource!(Product {
    get(request, ctx) => {
        let id = ctx.require_id()?;  // 400 if missing
        let table = ctx.get_table("Product")?;
        let product = table.get_or_404(id).await?;
        ok(product)
    }
});
```

## Query Parameters

### Direct access

```rust,ignore
fn get(&self, key: &str) -> Option<&str>
fn get_str(&self, key: &str, default: &str) -> String
fn get_i64(&self, key: &str, default: i64) -> i64
fn get_u64(&self, key: &str, default: u64) -> u64
fn get_f64(&self, key: &str, default: f64) -> f64
fn get_bool(&self, key: &str, default: bool) -> bool
fn contains_key(&self, key: &str) -> bool
```

```rust,ignore
// GET /app/products?page=2&limit=50&active=true&category=tools
let value: Option<&str> = ctx.get("category");         // Some("tools")
let page: i64 = ctx.get_i64("page", 1);                // 2
let limit: u64 = ctx.get_u64("limit", 25);             // 50
let active: bool = ctx.get_bool("active", false);       // true
let mode: String = ctx.get_str("mode", "default");      // "default"
let has_filter: bool = ctx.contains_key("category");    // true
```

`get_bool` recognizes `"true"`, `"1"`, `"yes"`, `"on"` as true.

### Fluent ParamBuilder

For typed extraction with clear error handling:

```rust,ignore
fn param<T: FromStr>(&self, name: &str) -> ParamBuilder<T>
```

`ParamBuilder` provides three terminal methods:

```rust,ignore
fn required(self) -> Result<T>      // error if missing or invalid
fn optional(self) -> Option<T>      // None if missing or invalid
fn default(self, val: T) -> T       // fallback if missing or invalid
```

```rust,ignore
let page: u32 = ctx.param::<u32>("page").default(1);
let limit: u32 = ctx.param::<u32>("limit").default(25);
let name: String = ctx.param::<String>("name").required()?;  // 400 if missing
let filter: Option<String> = ctx.param::<String>("filter").optional();
let threshold: f64 = ctx.param::<f64>("threshold").default(0.5);
let offset: i64 = ctx.param::<i64>("offset").default(0);
let debug: bool = ctx.param::<bool>("debug").default(false);
```

## Table Access

```rust,ignore
fn get_table(&self, name: &str) -> Result<Table>
fn tables(&self) -> Result<Tables>
fn table(&self, name: impl AsRef<str>) -> Result<Arc<dyn KvBackend>>
```

```rust,ignore
// High-level (recommended)
let products = ctx.get_table("Product")?;
let all = products.get_all().await?;

// Via Tables accessor
let tables = ctx.tables()?;
let users = tables.get("User")?;

// Low-level backend
let backend = ctx.table("Product")?;
```

See [Table Access](table-access.md) for full documentation.

## Parameters Map

```rust,ignore
fn as_map(&self) -> &HashMap<String, String>
fn insert(&mut self, key: String, value: String) -> Option<String>
fn is_empty(&self) -> bool
```

## HTTP Request Context

Access the underlying HTTP request metadata:

```rust,ignore
fn http_context(&self) -> Option<&HttpRequestContext>
```

The `HttpRequestContext` struct provides:

```rust,ignore
impl HttpRequestContext {
    fn cookie(&self, name: &str) -> Option<&str>
    fn cookies(&self) -> &HashMap<String, String>
    fn header(&self, name: &str) -> Option<&str>
    fn content_type(&self) -> Option<&str>
    fn accept(&self) -> Option<&str>
    fn authorization(&self) -> Option<&str>
    fn user_agent(&self) -> Option<&str>
}
```

```rust,ignore
if let Some(ctx) = ctx.http_context() {
    let session = ctx.cookie("session_id");
    let auth = ctx.authorization();
    let ua = ctx.user_agent();
}
```

## Response Headers

Set headers on the outgoing response:

```rust,ignore
fn response_headers(&self) -> ResponseHeadersBuilder
```

```rust,ignore
impl ResponseHeadersBuilder {
    fn append(&self, name: impl Into<String>, value: impl Into<String>)
    fn set(&self, name: impl Into<String>, value: impl Into<String>)
    fn get_all(&self) -> Vec<(String, String)>
}
```

`append` adds a value (allows multiple values for the same header name). `set` replaces any existing values.

```rust,ignore
ctx.response_headers().append("set-cookie", &cookie_string);
ctx.response_headers().set("cache-control", "max-age=3600");
ctx.response_headers().set("x-request-id", &request_id);
```

## Extension Config

Access per-app extension configuration from `config.yaml`:

```rust,ignore
fn extension_config(&self, name: &str) -> Option<&Value>
```

```rust,ignore
let auth_config = ctx.extension_config("yeti-auth");
```

## Quick Reference

| Method | Returns | Description |
|--------|---------|-------------|
| `id()` | `Option<&str>` | Path ID segment |
| `path_id()` | `Option<&str>` | Alias for `id()` |
| `require_id()` | `Result<&str>` | Path ID or 400 error |
| `get(key)` | `Option<&str>` | Query/path param value |
| `get_str(key, default)` | `String` | String param with default |
| `get_i64(key, default)` | `i64` | Integer param with default |
| `get_u64(key, default)` | `u64` | Unsigned integer param |
| `get_f64(key, default)` | `f64` | Float param with default |
| `get_bool(key, default)` | `bool` | Boolean param with default |
| `contains_key(key)` | `bool` | Whether param exists |
| `param::<T>(key)` | `ParamBuilder<T>` | Fluent typed param builder |
| `get_table(name)` | `Result<Table>` | High-level table handle |
| `tables()` | `Result<Tables>` | All app tables |
| `table(name)` | `Result<Arc<dyn KvBackend>>` | Low-level backend |
| `as_map()` | `&HashMap<String, String>` | All params as map |
| `insert(key, value)` | `Option<String>` | Add/replace a param |
| `http_context()` | `Option<&HttpRequestContext>` | HTTP request metadata |
| `response_headers()` | `ResponseHeadersBuilder` | Set response headers |
| `extension_config(name)` | `Option<&Value>` | Per-app extension config |
