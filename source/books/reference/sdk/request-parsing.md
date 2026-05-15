# Request Parsing

`Context` is the request data structure that flows through every
layer of the pipeline. Each layer populates its own fields; resource
handlers receive a fully-populated `Context` and read from it.

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Item {
    get(ctx) => {
        let id    = ctx.require_id()?;
        let table = ctx.table("Item")?;
        ok(table.get_or_404(id).await?)
    }
});
```

## Pipeline order

```text
Protocol adapter → Router → Auth → Table reg → Dispatch → Resource
       │             │       │         │           │          │
       creates       adds    adds      adds        adds       reads
       method, path, app_id, identity, database,   json_body, everything
       body, headers resource path_id, access,     table_name backend
                     query   permission
```

## Fields

```rust,ignore
pub struct Context {
    // — Protocol adapter —
    pub method: http::Method,
    pub protocol: Protocol,           // rest / graphql / ws / sse / mqtt / mcp / grpc
    pub path: String,
    pub body: Bytes,
    pub headers: http::HeaderMap,

    // — Router —
    pub app_id: Arc<str>,
    pub resource_id: Arc<str>,
    pub path_id: String,              // record id from URL (empty for collections)
    pub query_params: HashMap<String, String>,
    pub is_collection: bool,

    // — Auth —
    pub auth_identity: Option<AuthIdentity>,
    pub access: Option<Arc<dyn AccessControl>>,
    pub permission: TablePermission,
    pub requested_format: ContentType,

    // — Table registration —
    pub database: Arc<str>,
    pub table_name: Arc<str>,

    // — Dispatch —
    pub json_body: Option<Value>,
    pub backend_manager: Option<Arc<BackendManager>>,
    pub root_directory: Arc<str>,
}
```

`protocol` was added in YTC-335 — `@access(roles:)` can gate per-(op, protocol) using it.

## Built-in methods

| Method | Returns | Description |
|---|---|---|
| `query(name)` | `Option<&str>` | Query parameter by name |
| `query_int(name, default)` | `i64` | Query param as integer w/ default |
| `query_bool(name, default)` | `bool` | Query param as bool (`true/1/yes/on`) |
| `table_context()` | `(&str, &str)` | `(database, table_name)` pair |

## ContextExt — convenience methods

Imported via `use yeti_sdk::prelude::*`.

```rust,ignore
pub trait ContextExt {
    fn table(&self, name: &str) -> Result<Table>;
    fn tables(&self) -> Result<Tables>;
    fn require_id(&self) -> Result<&str>;
    fn require_json_body(&self) -> Result<&Value>;
    fn auth_identity(&self) -> Option<&AuthIdentity>;
    fn cookie(&self, name: &str) -> Option<String>;
}
```

| Method | Result |
|---|---|
| `table(name)` | `Table` accessor (CRUD + Query + pub/sub) |
| `tables()` | `Tables` (all-tables accessor) |
| `require_id()` | `path_id` or `YetiError::Validation` |
| `require_json_body()` | Parsed JSON body or `YetiError::Validation` |
| `auth_identity()` | Authenticated identity, if any |
| `cookie(name)` | Cookie value (handles HTTP/2 split-header per RFC 7540) |

## Path id and collection mode

The router extracts the record id from the URL. For collection
requests (`GET /{app}/{Table}`), `is_collection = true` and
`path_id = ""`.

```rust,ignore
resource!(Product {
    get(ctx) => {
        let table = ctx.table("Product")?;
        if ctx.is_collection {
            ok(table.get_all().await?)
        } else {
            ok(table.get_or_404(ctx.require_id()?).await?)
        }
    }
});
```

## JSON body

The dispatch layer parses bodies into `ctx.json_body` eagerly when
content-type is `application/json`. Use `require_json_body()` when the
body is mandatory.

```rust,ignore
post(ctx) => {
    let body = ctx.require_json_body()?;
    let name = body["name"].as_str()
        .ok_or(BadRequest("name is required"))?;

    let table = ctx.table("User")?;
    ok(table.create(body.clone()).await?)
}
```

### Typed body via serde

```rust,ignore
#[derive(Deserialize)]
struct CreateUser { name: String, email: String }

post(ctx) => {
    let user: CreateUser = serde_json::from_slice(&ctx.body)
        .map_err(|e| YetiError::Validation(e.to_string()))?;
    ok(json!({"created": user.name}))
}
```

## Query parameters

```rust,ignore
get(ctx) => {
    let limit  = ctx.query_int("limit", 100);
    let offset = ctx.query_int("offset", 0);
    let active = ctx.query_bool("active", true);
    let sort   = ctx.query("sort").unwrap_or("created_at");

    ok(ctx.table("Product")?
        .query()
        .limit(limit as usize)
        .offset(offset as usize)
        .execute()
        .await?)
}
```

`query_bool` matches `"true"`, `"1"`, `"yes"`, `"on"` (case-insensitive)
as true.

**Don't** parse `ctx.path` to get query params — the router already
populated `ctx.query_params` from it. Reading `ctx.path` for queries
silently fails (the `?query` portion isn't there).

## Headers

Standard `http::HeaderMap` on `ctx.headers`.

```rust,ignore
let auth   = ctx.headers.get("authorization").and_then(|v| v.to_str().ok());
let origin = ctx.headers.get("origin").and_then(|v| v.to_str().ok());
let accept = ctx.headers.get("accept").and_then(|v| v.to_str().ok())
    .unwrap_or("application/json");
```

For cookies, prefer `ctx.cookie(name)` — it handles HTTP/2 cookie
header splitting (RFC 7540 §8.1.2.5) that bare `HeaderMap::get("cookie")`
misses.

```rust,ignore
let session = ctx.cookie("session_id");
let theme   = ctx.cookie("theme").unwrap_or_else(|| "light".to_owned());
```

## Auth identity

```rust,ignore
pub enum AuthIdentity {
    Basic  { username: String },
    Jwt    { username: String, claims: Value },
    OAuth  { email: Option<String>, provider: String, claims: Value },
    Mtls   { username: String, cn: String, sans: Vec<String> },
}
```

```rust,ignore
post(ctx) => {
    let identity = ctx.auth_identity().ok_or(Unauthorized("auth required"))?;

    match identity {
        AuthIdentity::Jwt { username, claims } => {
            let role = claims["role"].as_str().unwrap_or("");
            ok(json!({"user": username, "role": role}))
        },
        AuthIdentity::OAuth { provider, email, .. } => {
            yeti_log::info!("OAuth user via {}", provider);
            ok(json!({"email": email}))
        },
        _ => ok(json!({"user": identity.username()})),
    }
}
```

## Permission

The auth layer pre-computes `ctx.permission` for field-level access
control. The `allow_*` predicates on `ResourceMetadata` use this
automatically; read it directly for custom logic.

```rust,ignore
match &ctx.permission {
    TablePermission::Public => { /* @access(public: ...) — no auth */ },
    TablePermission::FullAccess => { /* super_user or wildcard */ },
    TablePermission::AttributeRestricted { readable, writable } => {
        // Filter response fields based on `readable`
        // Reject input fields not in `writable`
    },
}
```

For declarative gating, prefer `@access(roles: {...})` in the schema
(YTC-331). Manual `ctx.permission` reads are for resources that need
to project responses dynamically.

## Quick reference

| Source | Member | Returns | Use |
|---|---|---|---|
| `Context` | `method` / `protocol` / `path` / `body` / `headers` | — | Request basics |
| | `app_id` / `resource_id` / `path_id` | `Arc<str>` / `String` | Routing |
| | `is_collection` | `bool` | True for `/{app}/{Table}` w/o id |
| | `json_body` | `Option<Value>` | Pre-parsed JSON body |
| | `query(name)` / `query_int` / `query_bool` | — | Query params |
| | `table_context()` | `(&str, &str)` | `(database, table_name)` |
| `ContextExt` | `table(name)` / `tables()` | `Table` / `Tables` | Table access |
| | `require_id()` | `Result<&str>` | 400 on missing path id |
| | `require_json_body()` | `Result<&Value>` | 400 on missing JSON body |
| | `auth_identity()` | `Option<&AuthIdentity>` | Authenticated identity |
| | `cookie(name)` | `Option<String>` | Cookie (HTTP/2-safe) |
