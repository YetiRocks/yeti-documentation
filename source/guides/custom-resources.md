# Custom Resources

Custom resources add business logic beyond auto-generated CRUD.

## Getting Started

Place `.rs` files in `resources/` and reference them in `config.yaml`:

```yaml
resources:
  path: "resources/*.rs"
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

### With Context Access

The `ctx` parameter is a `Context` that provides access to the request, path parameters, tables, and auth identity:

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Items {
    get(ctx) => {
        let table = ctx.get_table("Items")?;
        let id = ctx.require_id()?;
        let item = table.get(id).await?;
        match item {
            Some(data) => ok_json!(data),
            None => reply().code(404).json(json!({"error": "Not found"})),
        }
    },
    post(ctx) => {
        let body = ctx.require_json_body()?.clone();
        let name = body["name"].as_str()
            .ok_or_else(|| YetiError::Validation("name is required".into()))?;
        let table = ctx.get_table("Items")?;
        table.put(name, body.clone()).await?;
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
    get(ctx) => {
        let path = ctx.path_id.as_deref().unwrap_or("/");
        reply().code(404).json(json!({"error": "Not found", "path": path}))
    }
});
```

## Context API

The `ctx` parameter provides access to the application environment.

### Table Access

```rust,ignore
let table = ctx.get_table("Product")?;
let record = table.get("prod-123").await?;
table.put("prod-123", json!({"id": "prod-123", "name": "Widget"})).await?;
```

### Path Parameters

```rust,ignore
let id = ctx.path_id.as_deref();   // Option<&str> from /Resource/{id}
let id = ctx.require_id()?;        // Returns 400 if missing
```

### Request Body

```rust,ignore
let body = ctx.require_json_body()?;   // Returns 400 if not valid JSON
let name = body["name"].as_str()
    .ok_or_else(|| YetiError::Validation("name is required".into()))?;
let bio = body.get("bio").and_then(|v| v.as_str());
```

### Auth Identity

```rust,ignore
if let Some(identity) = ctx.auth_identity() {
    // Access authenticated user info
}
```

### Cookies

```rust,ignore
if let Some(session) = ctx.cookie("session_id") {
    // Use cookie value
}
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

    fn get(&self, ctx: Context) -> ResourceFuture {
        Box::pin(async move {
            let path = ctx.path_id.as_deref().unwrap_or("/");
            let cache = ctx.get_table("PageCache")?;
            match cache.get(path).await? {
                Some(cached) => {
                    reply()
                        .header("x-cache", "HIT")
                        .html(cached.as_str().unwrap_or_default())
                }
                None => {
                    reply()
                        .code(404)
                        .header("x-cache", "MISS")
                        .text("Not cached")
                }
            }
        })
    }
}

register_resource!(PageCache);
```

The `resource!` macro handles registration automatically. For manual implementations, add `register_resource!(MyResource);` at the end.

## External HTTP Requests

Use the `fetch!` macro from `yeti_sdk::prelude` for external HTTP calls. Do not use `reqwest::blocking::Client` -- it crashes in the dylib context.

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Proxy {
    get(ctx) => {
        let resp = fetch!("https://api.example.com/data").send()?;

        if resp.ok() {
            let data = resp.json().map_err(|e| YetiError::Internal(e))?;
            ok(data)
        } else {
            reply().code(resp.status).text(&format!("Upstream error: {}", resp.status))
        }
    },
    post(ctx) => {
        let body = ctx.require_json_body()?.clone();
        let data: Value = fetch!("POST", "https://api.example.com/data")
            .json_body(&body)?
            .json()?;

        ok(data)
    }
});
```

`fetch!` accepts one or two arguments: `fetch!(url)` for GET, `fetch!(method, url)` for other methods. Chain builder methods, then call a terminal method:

**Builder methods:** `.header(key, value)`, `.body(str)`, `.json_body(&Value)?`, `.no_redirect()`, `.timeout(seconds)`, `.abort_after(seconds)`.

**Terminal methods:** `.json()` (send + parse JSON), `.text()` (send + return String), `.send()` (raw `FetchResponse`).

**`FetchResponse` fields/methods:** `.status` (u16), `.body` (String), `.url` (String), `.redirected` (bool), `.ok()` (bool), `.json()`, `.text()`, `.header(name)`.

## Supported HTTP Methods

`get`, `post`, `put`, `patch`, `delete`, `search`. Unimplemented methods return 405.
