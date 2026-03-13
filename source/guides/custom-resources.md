# Custom Resources

Custom resources add business logic beyond auto-generated CRUD.

## Getting Started

Place `.rs` files in `resources/` and reference them in `config.yaml`:

```yaml
resources:
  - resources/*.rs
```

Every resource file starts with:

```rust,ignore
use yeti_sdk::prelude::*;
```

## The resource! Macro

### Simple Resource

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Greeting {
    get => json!({"greeting": "Hello, World!"})
});
```

Creates `GET /my-app/greeting` returning JSON.

### With Request and Context

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Items {
    get(request, ctx) => {
        let table = ctx.get_table("Items")?;
        let id = ctx.require_id()?;
        let item = table.get(id).await?;
        match item {
            Some(data) => ok_json!(data),
            None => reply().code(404).json(json!({"error": "Not found"})),
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

```rust,ignore
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
        reply().code(404).json(json!({"error": "Not found", "path": path}))
    }
});
```

## ResourceParams API

The `ctx` parameter provides access to the application environment.

### Table Access

```rust,ignore
let table = ctx.get_table("Product")?;
let record = table.get("prod-123").await?;
table.put("prod-123", json!({"id": "prod-123", "name": "Widget"})).await?;
```

### Path Parameters

```rust,ignore
let id = ctx.path_id();       // Option<&str> from /Resource/{id}
let id = ctx.require_id()?;   // Returns 400 if missing
```

### Configuration Access

```rust,ignore
let url = ctx.config().get_str("origin.url", "https://default.com");
let timeout = ctx.config().get_i64("api.timeout", 30);
let enabled = ctx.config().get_bool("features.cache", false);
```

### Response Headers

```rust,ignore
ctx.response_headers().append("x-cache", "HIT");
ctx.response_headers().set("X-Custom-Header", "value");
```

## Request Parsing

The `request` parameter is `http::Request<Vec<u8>>`:

```rust,ignore
let body = request.json_value()?;
let name = body.require_str("name")?;
let bio = body.get("bio").and_then(|v| v.as_str());
```

## Response Helpers

```rust,ignore
// 200 OK with JSON
ok_json!({"status": "ok", "count": 42})
ok_json!(data)

// 201 Created
created(json!({"id": "new-123"}))
created_json!({"id": "new-123"})

// Custom status
reply().code(404).json(json!({"error": "Not found"}))

// Other content types
ok_html("<h1>Hello</h1>")
reply().text("Hello")
reply().redirect("/new-location", Some(302))

// Custom headers
reply()
    .code(200)
    .header("x-cache", "HIT")
    .json(json!({"message": "Hello"}))
```

## Manual Implementation

For full control, implement the `Resource` trait directly:

```rust,ignore
use yeti_sdk::prelude::*;

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
            match cache.get(path).await? {
                Some(cached) => {
                    ctx.response_headers().append("x-cache", "HIT");
                    ok_html(cached.as_str().unwrap_or_default())
                }
                None => {
                    ctx.response_headers().append("x-cache", "MISS");
                    reply().code(404).text("Not cached")
                }
            }
        })
    }
}

register_resource!(PageCache);
```

The `resource!` macro handles registration automatically. For manual implementations, add `register_resource!(MyResource);` at the end.

## External HTTP Requests

Use `fetch()` from `yeti_sdk::prelude` for external HTTP calls. Do not use `reqwest::blocking::Client` -- it crashes in the dylib context.

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Proxy {
    get(request, ctx) => {
        let res = fetch("https://api.example.com/data", None)
            .map_err(|e| YetiError::Validation(e))?;

        if res.ok() {
            ok_json!(res.json()?)
        } else {
            reply().code(res.status).text(&format!("Upstream error: {}", res.status))
        }
    },
    post(request, ctx) => {
        let body = request.json_value()?;
        let res = fetch("https://api.example.com/data", Some(FetchOptions {
            method: "POST".to_string(),
            headers: vec![("Content-Type".to_string(), "application/json".to_string())]
                .into_iter().collect(),
            body: Some(body.to_string()),
            ..Default::default()
        })).map_err(|e| YetiError::Validation(e))?;

        ok_json!(res.json()?)
    }
});
```

`FetchResponse` methods: `.ok()`, `.json()`, `.text()`, `.header(name)`, `.status`, `.url`, `.redirected`.

`FetchOptions` fields: `method`, `headers`, `body`, `redirect`, `timeout`, `signal_timeout`.

## Supported HTTP Methods

`get`, `post`, `put`, `patch`, `delete`, `search`. Unimplemented methods return 405.
