# Custom Resources

Custom resources add business logic beyond auto-generated CRUD. They are Rust source files compiled into dynamic library plugins.

## Getting Started

Place `.rs` files in `resources/` and reference them in `config.yaml`:

```yaml
resources:
  - resources/*.rs
```

Every resource file starts with:

```rust
use yeti_core::prelude::*;
```

## The resource! Macro

### Simple Resource

```rust
use yeti_core::prelude::*;

resource!(Greeting {
    get => json!({"greeting": "Hello, World!"})
});
```

Creates `GET /my-app/greeting` returning JSON.

### With Request and Context

```rust
use yeti_core::prelude::*;

resource!(Items {
    get(request, ctx) => {
        let table = ctx.get_table("Items")?;
        let id = ctx.require_id()?;
        let item = table.get_by_id(id).await?;
        match item {
            Some(data) => ok_json!(data),
            None => reply().status(404).json(json!({"error": "Not found"})),
        }
    },
    post(request, ctx) => {
        let body = request.json_value()?;
        let name = body.require_str("name")?;
        let table = ctx.get_table("Items")?;
        table.put(&name, body.clone()).await?;
        created(body)
    }
});
```

### Options

```rust
// Custom URL path
resource!(MyHandler {
    name = "custom-path",
    get => json!({"data": "served at /app/custom-path"})
});

// Catch-all for unmatched paths
resource!(Fallback {
    default = true,
    get(request, ctx) => {
        let path = ctx.path_id().unwrap_or("/");
        reply().status(404).json(json!({"error": "Not found", "path": path}))
    }
});
```

## ResourceParams API

The `ctx` parameter provides access to the application environment.

### Table Access

```rust
let table = ctx.get_table("Product")?;
let record = table.get_by_id("prod-123").await?;
table.put("prod-123", json!({"id": "prod-123", "name": "Widget"})).await?;
```

### Path Parameters

```rust
let id = ctx.path_id();       // Option<&str> from /Resource/{id}
let id = ctx.require_id()?;   // Returns 400 if missing
```

### Configuration Access

```rust
let url = ctx.config().get_str("origin.url", "https://default.com");
let timeout = ctx.config().get_i64("api.timeout", 30);
let enabled = ctx.config().get_bool("features.cache", false);
```

### Response Headers

```rust
ctx.response_headers().append("x-cache", "HIT");
ctx.response_headers().set("X-Custom-Header", "value");
```

## Request Parsing

The `request` parameter is `http::Request<Vec<u8>>`:

```rust
let body = request.json_value()?;
let name = body.require_str("name")?;
let bio = body.get("bio").and_then(|v| v.as_str());
```

## Response Helpers

```rust
// 200 OK with JSON
ok_json!({"status": "ok", "count": 42})
ok_json!(data)

// 201 Created
created(json!({"id": "new-123"}))
created_json!({"id": "new-123"})

// Custom status
reply().status(404).json(json!({"error": "Not found"}))

// Other content types
ok_html("<h1>Hello</h1>")
reply().text("Hello")
reply().redirect("/new-location", Some(302))

// Custom headers
reply()
    .status(200)
    .header("x-cache", "HIT")
    .json(json!({"message": "Hello"}))
```

## Manual Implementation

For full control, implement the `Resource` trait directly:

```rust
use yeti_core::prelude::*;

pub struct PageCache;

impl Default for PageCache {
    fn default() -> Self { Self }
}

impl Resource for PageCache {
    fn name(&self) -> &str { "PageCache" }
    fn is_default(&self) -> bool { true }

    fn get(&self, _request: Request<Vec<u8>>, ctx: ResourceParams) -> ResourceFuture {
        async_handler!({
            let path = ctx.id().unwrap_or("/");
            let cache = ctx.get_table("PageCache")?;
            match cache.get_by_id(path).await? {
                Some(cached) => {
                    ctx.response_headers().append("x-cache", "HIT");
                    ok_html(cached.as_str().unwrap_or_default())
                }
                None => {
                    ctx.response_headers().append("x-cache", "MISS");
                    reply().status(404).text("Not cached")
                }
            }
        })
    }
}

register_resource!(PageCache);
```

The `resource!` macro handles registration automatically. For manual implementations, add `register_resource!(MyResource);` at the end.

## Supported HTTP Methods

`get`, `post`, `put`, `patch`, `delete`, `search`. Unimplemented methods return 405.
