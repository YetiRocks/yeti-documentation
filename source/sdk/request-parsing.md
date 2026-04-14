# Request Parsing

`Context` accumulates data as a request flows through the pipeline. `ContextExt` adds convenience methods for common handler patterns.

## Context Struct

Each pipeline layer populates its fields:

```text
Protocol adapter  ->  Router  ->  Auth  ->  Dispatch  ->  Resource
     |                  |          |           |             |
     creates            adds       adds        adds          reads
     method, path,      app_id,    identity,   json_body,    everything
     body, headers      resource,  access,     backend
                        path_id,   permission
                        query
```

### Fields

```rust,ignore
pub struct Context {
    // -- Protocol adapter --
    pub method: http::Method,
    pub path: String,
    pub body: Bytes,
    pub headers: http::HeaderMap,

    // -- Router --
    pub app_id: Arc<str>,
    pub resource_id: Arc<str>,
    pub path_id: Option<String>,
    pub query_params: HashMap<String, String>,
    pub is_collection: bool,

    // -- Auth layer --
    pub auth_identity: Option<AuthIdentity>,
    pub access: Option<Arc<dyn AccessControl>>,
    pub permission: TablePermission,

    // -- Table registration --
    pub database: Arc<str>,
    pub table_name: Arc<str>,

    // -- Dispatch layer --
    pub json_body: Option<Value>,
    pub backend_manager: Option<Arc<BackendManager>>,
}
```

### Built-in methods

| Method | Returns | Description |
|--------|---------|-------------|
| `query(name)` | `Option<&str>` | Query parameter by name |
| `query_int(name, default)` | `i64` | Query parameter as integer with default |
| `query_bool(name, default)` | `bool` | Query parameter as boolean with default |
| `table(name)` | `Result<Arc<dyn KvBackend>>` | Low-level backend for a table |
| `table_context()` | `(&str, &str)` | Database and table name pair |

## ContextExt Trait

Imported via `use yeti_sdk::prelude::*`. Higher-level convenience methods on `Context`.

```rust,ignore
pub trait ContextExt {
    fn get_table(&self, name: &str) -> Result<Table>;
    fn tables(&self) -> Result<Tables>;
    fn require_id(&self) -> Result<&str>;
    fn require_json_body(&self) -> Result<&Value>;
    fn auth_identity(&self) -> Option<&AuthIdentity>;
    fn cookie(&self, name: &str) -> Option<String>;
}
```

| Method | Returns | Description |
|--------|---------|-------------|
| `get_table(name)` | `Result<Table>` | Table accessor by name |
| `tables()` | `Result<Tables>` | Accessor for all tables |
| `require_id()` | `Result<&str>` | `path_id` or validation error |
| `require_json_body()` | `Result<&Value>` | Parsed JSON body or validation error |
| `auth_identity()` | `Option<&AuthIdentity>` | Authenticated identity |
| `cookie(name)` | `Option<String>` | Cookie value from request headers |

## Path ID and Record Lookup

The router extracts the path ID from the URL (e.g. `"123"` from `/app/Table/123`). Use `require_id()` when the ID is mandatory.

```rust,ignore
fn get(&self, ctx: Context) -> ResourceFuture {
    Box::pin(async move {
        let id = ctx.require_id()?;
        let table = ctx.get_table("Product")?;
        let product = table.get_or_404(id).await?;
        ok(product)
    })
}
```

For collection requests (no ID), `ctx.is_collection` is `true` and `ctx.path_id` is `None`.

```rust,ignore
fn get(&self, ctx: Context) -> ResourceFuture {
    Box::pin(async move {
        if ctx.is_collection {
            let table = ctx.get_table("Product")?;
            let all = table.get_all().await?;
            ok(all)
        } else {
            let id = ctx.require_id()?;
            let table = ctx.get_table("Product")?;
            let product = table.get_or_404(id).await?;
            ok(product)
        }
    })
}
```

## Request Body Parsing

The dispatch layer eagerly parses JSON bodies into `ctx.json_body`. Use `require_json_body()` when a body is required, or read `ctx.json_body` directly for optional bodies.

```rust,ignore
fn post(&self, ctx: Context) -> ResourceFuture {
    Box::pin(async move {
        let body = ctx.require_json_body()?;
        let name = body["name"].as_str()
            .ok_or_else(|| YetiError::Validation("name is required".into()))?;

        let table = ctx.get_table("User")?;
        let record = table.create(body.clone()).await?;
        ok(record)
    })
}
```

For typed deserialization, parse from the raw bytes:

```rust,ignore
#[derive(Deserialize)]
struct CreateUser {
    name: String,
    email: String,
}

fn post(&self, ctx: Context) -> ResourceFuture {
    Box::pin(async move {
        let user: CreateUser = serde_json::from_slice(&ctx.body)
            .map_err(|e| YetiError::Validation(e.to_string()))?;
        // ...
        ok(json!({"created": user.name}))
    })
}
```

## Query Parameters

The router parses query parameters into `ctx.query_params`. Access them with `query()`, `query_int()`, and `query_bool()`.

```rust,ignore
fn get(&self, ctx: Context) -> ResourceFuture {
    Box::pin(async move {
        let limit = ctx.query_int("limit", 100);
        let offset = ctx.query_int("offset", 0);
        let active = ctx.query_bool("active", true);

        // Raw string access
        let sort = ctx.query("sort").unwrap_or("created_at");

        let table = ctx.get_table("Product")?;
        let results = table.query()
            .limit(limit as usize)
            .offset(offset as usize)
            .execute()
            .await?;
        ok(results)
    })
}
```

`query_bool` recognizes `"true"`, `"1"`, `"yes"`, `"on"` as true.

## Header Access

Standard `http::HeaderMap` on `ctx.headers`.

```rust,ignore
fn get(&self, ctx: Context) -> ResourceFuture {
    Box::pin(async move {
        let auth = ctx.headers.get("authorization")
            .and_then(|v| v.to_str().ok());

        let origin = ctx.headers.get("origin")
            .and_then(|v| v.to_str().ok());

        let accept = ctx.headers.get("accept")
            .and_then(|v| v.to_str().ok())
            .unwrap_or("application/json");

        // ...
        ok(json!({"accept": accept}))
    })
}
```

For cookies, `cookie()` from `ContextExt` handles HTTP/2 cookie header splitting:

```rust,ignore
let session = ctx.cookie("session_id");
let theme = ctx.cookie("theme").unwrap_or_else(|| "light".to_string());
```

## Auth Identity

The auth layer populates `ctx.auth_identity` and `ctx.access`.

```rust,ignore
pub enum AuthIdentity {
    Basic { username: String },
    Jwt { username: String, claims: Value },
    OAuth { email: Option<String>, provider: String, claims: Value },
    Mtls { username: String, cn: String, sans: Vec<String> },
}
```

```rust,ignore
fn post(&self, ctx: Context) -> ResourceFuture {
    Box::pin(async move {
        let identity = ctx.auth_identity()
            .ok_or_else(|| YetiError::Validation("Authentication required".into()))?;

        let username = identity.username();

        // Check specific identity type
        match identity {
            AuthIdentity::Jwt { claims, .. } => {
                let role = claims["role"].as_str();
                // ...
            }
            AuthIdentity::OAuth { provider, .. } => {
                tracing::info!("OAuth login via {}", provider);
            }
            _ => {}
        }

        ok(json!({"user": username}))
    })
}
```

## Table Permission

The auth layer pre-computes `ctx.permission` for field-level access control. The `allow_*` methods use this automatically; read it directly for custom logic.

```rust,ignore
match &ctx.permission {
    TablePermission::Public => { /* no auth required */ }
    TablePermission::FullAccess => { /* super_user or wildcard */ }
    TablePermission::AttributeRestricted { readable, writable } => {
        // Filter response fields based on readable
        // Validate input fields based on writable
    }
}
```

## Table Access

`Table` (from `ctx.get_table()`) provides CRUD operations, querying, and convenience methods.

### CRUD Operations

```rust,ignore
let table = ctx.get_table("Product")?;

// Read
let product = table.get("prod-123").await?;          // Option<Value>
let product = table.get_or_404("prod-123").await?;   // Value (404 if missing)
let all = table.get_all().await?;                     // Vec<Value>

// Create (auto-generates UUID v7 ID)
let created = table.create(json!({"name": "Widget"})).await?;

// Update
table.put("prod-123", json!({"name": "Widget", "price": 29.99})).await?;
table.patch("prod-123", json!({"price": 24.99})).await?;

// Delete
let existed = table.delete("prod-123").await?;        // bool
let count = table.delete_all().await?;                 // u64
```

### Query and Search

```rust,ignore
// Fluent query builder
let results = table.query()
    .where_eq("status", "active")
    .limit(10)
    .execute()
    .await?;

// Convenience scan methods
let active = table.find("status", "active").await?;        // Vec<Value>
let admin = table.find_one("role", "admin").await?;        // Option<Value>
let total = table.count().await?;                           // u64
let by_status = table.count_by("status").await?;           // HashMap<String, usize>
let groups = table.group_by("category").await?;            // HashMap<String, Vec<Value>>
```

### PubSub Subscriptions

```rust,ignore
// Subscribe to all changes on a table
let mut rx = table.subscribe_all().await?;

// Subscribe to changes on a specific record
let mut rx = table.subscribe_id("order-123").await?;

while let Ok(msg) = rx.recv().await {
    // msg.message_type: Update | Delete | Publish | Retained
    // msg.data: Value
    // msg.id: Option<String>
}
```

## Quick Reference

| Source | Method | Returns | Description |
|--------|--------|---------|-------------|
| `Context` | `method` | `http::Method` | HTTP method |
| | `path` | `String` | Request path |
| | `body` | `Bytes` | Raw body |
| | `headers` | `HeaderMap` | HTTP headers |
| | `app_id` | `Arc<str>` | Application ID |
| | `resource_id` | `Arc<str>` | Resource name |
| | `path_id` | `Option<String>` | Record ID from path |
| | `is_collection` | `bool` | No ID in path |
| | `json_body` | `Option<Value>` | Parsed JSON body |
| | `query(name)` | `Option<&str>` | Query parameter |
| | `query_int(name, default)` | `i64` | Integer query parameter |
| | `query_bool(name, default)` | `bool` | Boolean query parameter |
| | `table(name)` | `Result<Arc<dyn KvBackend>>` | Low-level table backend |
| `ContextExt` | `get_table(name)` | `Result<Table>` | Table accessor |
| | `tables()` | `Result<Tables>` | All-tables accessor |
| | `require_id()` | `Result<&str>` | Path ID or 400 |
| | `require_json_body()` | `Result<&Value>` | JSON body or 400 |
| | `auth_identity()` | `Option<&AuthIdentity>` | Authenticated identity |
| | `cookie(name)` | `Option<String>` | Cookie value |
