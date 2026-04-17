# Resources

Resources are custom HTTP handlers written in Rust. They extend or override auto-generated table endpoints with business logic.

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Greeting {
    get => json!({"greeting": "Hello, World!"})
});
```

Creates `GET /{app-id}/api/greeting`. The `resource!` macro handles struct definition, trait implementation, and registration.

Place `.rs` files in `resources/` and reference them in `config.yaml`:

```yaml
resources:
  path: "resources/*.rs"
  route: "/api"
```

The `route` field sets the URL prefix for all resources (default: `/api`). Resources compile to dynamic libraries at runtime. Initial compilation takes ~2 minutes; cached rebuilds are fast.

## Context Access

Add a `ctx` parameter to access request data. Context accumulates fields from each pipeline layer (protocol, router, auth, dispatch):

```rust,ignore
resource!(Items {
    get(ctx) => {
        let items = ctx.get_table("Items")?.get_all().await?;
        reply().json(&items)
    },
    post(ctx) => {
        let item = ctx.require_json_body()?.clone();
        let id = item["id"].as_str().unwrap();
        ctx.get_table("Items")?.put(id, item).await?;
        created(json!({"id": id}))
    },
    get(ctx) => {
        let id = ctx.require_id()?;
        let item = ctx.get_table("Items")?.get(id).await?;
        match item {
            Some(val) => reply().json(&val),
            None => not_found()
        }
    },
    delete(ctx) => {
        let id = ctx.require_id()?;
        ctx.get_table("Items")?.delete(id).await?;
        no_content()
    }
});
```

### Context Fields

| Field / Method | Purpose |
|----------------|---------|
| `ctx.method` | HTTP method |
| `ctx.path` | Full request path |
| `ctx.path_id` | Record ID from path (e.g., `"123"` from `/Table/123`) |
| `ctx.headers` | HTTP headers |
| `ctx.body` | Raw request body bytes |
| `ctx.query_params` | Parsed query parameters |
| `ctx.is_collection` | Whether this is a collection request (no ID) |
| `ctx.app_id` | Application ID |
| `ctx.auth_identity` | Authentication identity (if present) |

### Context Extension Methods

`ContextExt` (included in `prelude::*`) provides convenience methods:

| Method | Purpose |
|--------|---------|
| `ctx.require_id()` | Get path ID or return 400 |
| `ctx.require_json_body()` | Get parsed JSON body or return 400 |
| `ctx.get_table("Name")` | Get a `Table` accessor by name |
| `ctx.tables()` | Get a `Tables` accessor for all backends |
| `ctx.auth_identity()` | Get the auth identity (if present) |
| `ctx.cookie("name")` | Get a cookie value from request headers |
| `ctx.query("key")` | Get a query parameter by name |
| `ctx.query_int("key", default)` | Get a query parameter as i64 |
| `ctx.table("name")` | Get a raw KvBackend by table name |

## Resource Options

```rust,ignore
// Custom endpoint name (URL path differs from struct name)
resource!(MyResource {
    name = "custom-path",
    get => json!({ "data": "value" })
});

// Default/catch-all resource (handles all unmatched paths within the app)
resource!(PageCache {
    default = true,
    get(ctx) => {
        let path = ctx.path_id.as_deref().unwrap_or("/");
        // ... fetch and cache logic
    }
});

// Both options
resource!(CatchAll {
    name = "fallback",
    default = true,
    get => reply().text("Not found")
});
```

## Table Extenders

Override permissions or behavior for auto-generated table endpoints:

```rust,ignore
resource!(TableExtender for Employee {
    get => allow_read(),
    put => allow_update(),
    delete => deny()
});
```

## Constraints

- **HTTP calls**: Use `fetch()` from `yeti_sdk::prelude`. `reqwest::blocking::Client` crashes in dylib context.
- **Logging**: Use `tracing` macros. Never `eprintln!()`.
- **No `tokio::spawn`**: Corrupts the host runtime. Use `futures::stream::unfold` for streaming.

## Routing Priority

When multiple handlers match a request:

1. **Custom resources** (exact name match)
2. **Table endpoints** (auto-generated from `@export`)
3. **Default resource** (catch-all, one per app)
4. **Static files** (from `web/` directory)
5. **404 Not Found**

A custom resource with the same name as a table takes precedence. Unoverridden methods fall through to the default table handler.

See also: [REST API](../api/rest.md), [Routing](routing.md), [Static File Serving](../guides/static-files.md).
