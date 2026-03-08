# ResourceParams

The `ctx` parameter in resource handlers provides access to path params, query params, configuration, auth state, extensions, and response headers.

## Path Parameters

```rust,ignore
let id: Option<&str> = ctx.id();             // Path segment after resource name
let id: Option<String> = ctx.path_id();       // Same, owned String
let id: &str = ctx.require_id()?;             // Returns 400 if missing
```

For a request to `GET /app/Product/abc-123`, `ctx.id()` returns `Some("abc-123")`.

## Query Parameters

### Direct access

```rust,ignore
let value: Option<&str> = ctx.get("key");
let name: &str = ctx.get_str("name", "default");
let page: i64 = ctx.get_i64("page", 1);
let active: bool = ctx.get_bool("active", false);
```

### Fluent param builder

```rust,ignore
let page: u32 = ctx.param::<u32>("page").default(1);
let limit: u32 = ctx.param::<u32>("limit").default(25);
let name: String = ctx.param::<String>("name").required()?;  // 400 if missing
```

## Configuration

Access app-level config values from `config.yaml`:

```rust,ignore
let url: &str = ctx.config().get_str("api.endpoint", "https://default.com");
let timeout: i64 = ctx.config().get_i64("api.timeout", 30);
let enabled: bool = ctx.config().get_bool("features.cache", false);
```

Config values are defined under the app's `config.yaml` as top-level or nested keys.

## Authentication

```rust,ignore
let is_admin: bool = ctx.is_super_user();
let identity: Option<&AuthIdentity> = ctx.auth_identity();
let has_auth: bool = ctx.has_auth_identity();
```

### OAuth

```rust,ignore
let oauth_ctx = ctx.oauth_context().await;   // Full OAuth context
let oauth_user = ctx.oauth_user().await;      // Current OAuth user info
```

## Extensions

Access other loaded extensions:

```rust,ignore
let ext = ctx.extension("yeti-auth")?;
let has_vectors: bool = ctx.has_extension("yeti-vectors");
```

### Extension config

```rust,ignore
let auth_config = ctx.extension_config("yeti-auth");
```

## Response Headers

Set headers on the outgoing response:

```rust,ignore
ctx.response_headers().append("x-request-id", &ctx.request_id());
ctx.response_headers().set("cache-control", "no-store");
```

## Request Metadata

```rust,ignore
let req_id: String = ctx.request_id();       // Unique request ID
let ip: Option<String> = ctx.client_ip();     // Client IP address
let host: Option<String> = ctx.hostname();    // Request hostname
```

## Quick Reference

| Method | Returns | Description |
|--------|---------|-------------|
| `id()` | `Option<&str>` | Path ID segment (borrowed) |
| `path_id()` | `Option<String>` | Path ID segment (owned) |
| `require_id()` | `Result<&str>` | Path ID or 400 error |
| `get("key")` | `Option<&str>` | Query param value |
| `get_str("key", default)` | `&str` | Query param with default |
| `get_i64("key", default)` | `i64` | Integer query param |
| `get_bool("key", default)` | `bool` | Boolean query param |
| `param::<T>("key")` | `ParamBuilder<T>` | Fluent param builder |
| `get_table("Name")` | `Result<Table>` | Table reference |
| `tables()` | `Result<Tables>` | All app tables |
| `config()` | `&AppConfig` | App configuration |
| `is_super_user()` | `bool` | Admin check |
| `auth_identity()` | `Option<&AuthIdentity>` | Current auth identity |
| `extension("name")` | `Result<&Extension>` | Extension reference |
| `response_headers()` | `&ResponseHeaders` | Mutable response headers |
| `request_id()` | `String` | Request ID |
| `client_ip()` | `Option<String>` | Client IP address |
| `hostname()` | `Option<String>` | Request hostname |
