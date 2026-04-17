# Resource Macros

## resource!

The primary macro for defining HTTP resources. Generates a struct, implements `Resource`, and registers it for export.

### Simple (no context)

Static responses without request data:

```rust,ignore
resource!(Health {
    get => json!({"status": "ok"})
});
```

Struct name becomes the route path (lowercased): `GET /app/health`.

### With Context

Pass a parameter to access the `Context` (request, path ID, query params, auth identity, headers, body, tables):

```rust,ignore
resource!(Items {
    get(ctx) => {
        let table = ctx.get_table("Items")?;
        let id = ctx.require_id()?;
        let item = table.get(id).await?;
        ok(item)
    },
    post(ctx) => {
        let body = ctx.require_json_body()?.clone();
        let table = ctx.get_table("Items")?;
        let id = body["id"].as_str().unwrap_or("unknown");
        table.put(id, body.clone()).await?;
        created(body)
    },
    delete(ctx) => {
        let table = ctx.get_table("Items")?;
        let id = ctx.require_id()?;
        table.delete(id).await?;
        no_content()
    }
});
```

The parameter name is arbitrary (`ctx`, `c`, `request`, etc.).

### Custom URL path

Override the route path:

```rust,ignore
resource!(MyHandler {
    name = "custom-path",
    get => json!({"served_at": "/app/custom-path"})
});
```

Registers at `/app/custom-path` instead of `/app/myhandler`.

### Catch-all (default)

A default resource handles unmatched paths:

```rust,ignore
resource!(Fallback {
    default = true,
    get(ctx) => {
        let path = ctx.path_id.as_deref().unwrap_or("/");
        not_found(&format!("No resource at {}", path))
    }
});
```

### Combined options

`name` and `default` combine in either order:

```rust,ignore
resource!(CatchAll {
    name = "fallback",
    default = true,
    get(ctx) => {
        reply().text("Not found")
    }
});
```

### Custom fields

Resources hold state via the `fields` block. Fields are accessible via `self` inside handlers (each handler is a `fn get(&self, ctx: Context)` method). The `fields` pattern does not support a context parameter.

```rust,ignore
resource!(Counter {
    fields { count: Arc<std::sync::atomic::AtomicU64> },
    get => {
        let n = self.count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        ok(json!({"count": n}))
    }
});
```

### Supported methods

Supported HTTP methods (each with or without a context parameter):

| Method | Description |
|--------|-------------|
| `get` | GET requests |
| `post` | POST requests |
| `put` | PUT requests |
| `patch` | PATCH requests |
| `delete` | DELETE requests |
| `search` | SEARCH requests |

Real-time methods (available when implementing `Resource` directly):

| Method | Return type | Description |
|--------|-------------|-------------|
| `subscribe` | `SubscriptionFuture` | SSE event streams |
| `publish` | `ResourceFuture` | MQTT publish handling |
| `connect` | `ConnectionFuture` | WebSocket connections |

## extends_table!

Override behavior on an auto-generated table resource. Only defined methods are overridden; others delegate to the default table implementation.

```rust,ignore
extends_table!(Product {
    get => json!({"message": "custom product listing"})
});
```

`extends_table!` uses simple expression syntax (no context parameter). For context access, use `resource!` with the TableExtender pattern or implement `Resource` directly.

## Permission overrides (TableExtender)

Declare publicly accessible methods on a table resource (no authentication required):

```rust,ignore
resource!(TableExtender for Product {
    get => allow_read(),
    subscribe => allow_read(),
});
```

Permission functions:

| Function | Makes public | Applies to |
|----------|-------------|------------|
| `allow_read()` | Read access | `get`, `search`, `subscribe`, `connect` |
| `allow_create()` | Insert access | `post`, `publish` |
| `allow_update()` | Update access | `put`, `patch` |
| `allow_delete()` | Delete access | `delete` |

Multiple methods can map to the same permission. Duplicates are deduplicated:

```rust,ignore
resource!(TableExtender for Chat {
    get => allow_read(),
    post => allow_create(),
    put => allow_update(),
    patch => allow_update(),
    delete => allow_delete(),
    subscribe => allow_read(),
});
```

## Response helpers

### reply() builder

Chainable response builder:

```rust,ignore
resource!(Api {
    get(ctx) => {
        reply()
            .code(200)
            .header("x-cache", "HIT")
            .json(json!({"data": "value"}))
    }
});
```

Builder methods: `.code(status)`, `.header(name, value)`, `.json(value)`, `.text(content)`, `.html(content)`.

### Function helpers

| Function | Description |
|----------|-------------|
| `ok(value)` | 200 + JSON body |
| `created(value)` | 201 + JSON body |
| `no_content()` | 204 empty |
| `not_found(msg)` | 404 error |
| `bad_request(msg)` | 400 error |
| `unauthorized(msg)` | 401 error |
| `json_response(status, value)` | Custom status + JSON |
| `html_response(content)` | 200 + text/html |
| `text_response(content)` | 200 + text/plain |

## Resource trait reference

The full trait that macros implement:

```rust,ignore
pub trait Resource: Send + Sync {
    fn name(&self) -> &str;
    fn is_default(&self) -> bool { false }
    fn attribute_names(&self) -> Option<Arc<Vec<String>>> { None }
    fn extends_table(&self) -> Option<&str> { None }
    fn method_overrides(&self) -> MethodOverrides { Default::default() }

    fn get(&self, ctx: Context) -> ResourceFuture;
    fn post(&self, ctx: Context) -> ResourceFuture;
    fn put(&self, ctx: Context) -> ResourceFuture;
    fn patch(&self, ctx: Context) -> ResourceFuture;
    fn delete(&self, ctx: Context) -> ResourceFuture;
    fn search(&self, ctx: Context) -> ResourceFuture;
    fn copy(&self, ctx: Context) -> ResourceFuture;
    fn move_record(&self, ctx: Context) -> ResourceFuture;
    fn invalidate(&self, ctx: Context) -> ResourceFuture;

    fn subscribe(&self, ctx: Context) -> SubscriptionFuture;
    fn publish(&self, ctx: Context) -> ResourceFuture;
    fn connect(&self, ctx: Context) -> ConnectionFuture;

    fn allow_read(&self, ctx: &Context) -> bool;
    fn allow_create(&self, ctx: &Context) -> bool;
    fn allow_update(&self, ctx: &Context) -> bool;
    fn allow_delete(&self, ctx: &Context) -> bool;
    fn allow_subscribe(&self, ctx: &Context) -> bool;
    fn allow_connect(&self, ctx: &Context) -> bool;
    fn allow_publish(&self, ctx: &Context) -> bool;
}
```

All methods except `name()` have defaults. HTTP methods default to 405. Authorization methods default to RBAC checks against the context's `AccessControl`.
ssControl`.
l`.
essControl`.
ssControl`.
l`.
ext's `AccessControl`.
ssControl`.
l`.
essControl`.
ssControl`.
l`.
trol`.
l`.
`.
essControl`.
ssControl`.
l`.
trol`.
l`.
l`.
