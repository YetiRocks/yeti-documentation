# Resource Macros

## resource!

The primary macro for defining HTTP resources. It generates a struct, implements the `Resource` trait, and registers the resource for export.

### Simple (no request/context)

For simple responses without request/context:

```rust,ignore
resource!(Health {
    get => json!({"status": "ok"})
});
```

The struct name becomes the route path (lowercased): `GET /app/health`.

### With request and context

Use explicit parameter names to access the request and `ResourceParams`:

```rust,ignore
resource!(Items {
    get(request, ctx) => {
        let table = ctx.get_table("Items")?;
        let id = ctx.require_id()?;
        let item = table.get_or_404(id).await?;
        ok(item)
    },
    post(request, ctx) => {
        let body = request.json_value()?;
        let table = ctx.get_table("Items")?;
        let result = table.create(body).await?;
        created(result)
    },
    delete(request, ctx) => {
        let table = ctx.get_table("Items")?;
        let id = ctx.require_id()?;
        table.delete(id).await?;
        no_content()
    }
});
```

Parameter names are arbitrary (`req`, `params`, `request`, `yeti`, etc.).

### Custom URL path

Override the route path with `name =`:

```rust,ignore
resource!(MyHandler {
    name = "custom-path",
    get => json!({"served_at": "/app/custom-path"})
});
```

The resource registers at `/app/custom-path` instead of `/app/myhandler`.

### Catch-all (default)

A default resource handles any path not matched by other resources or tables:

```rust,ignore
resource!(Fallback {
    default = true,
    get(request, ctx) => {
        let path = ctx.path_id().unwrap_or("/");
        not_found(&format!("No resource at {}", path))
    }
});
```

### Combined options

`name` and `default` can be used together, in either order:

```rust,ignore
resource!(CatchAll {
    name = "fallback",
    default = true,
    get(request, ctx) => {
        ok_text("Not found")
    }
});
```

### Custom fields

Resources can hold state via the `fields` block:

```rust,ignore
resource!(Counter {
    fields { count: Arc<std::sync::atomic::AtomicU64> },
    get(request, ctx) => {
        let n = ctx.count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        ok(json!({"count": n}))
    }
});
```

### Supported methods

The macro supports: `get`, `post`, `put`, `patch`, `delete`, `search`. Each can be used with or without parameters.

## simple_resource!

One-liner for resources that implement a single method:

```rust,ignore
simple_resource!(Ping, get => json!({"pong": true}));
```

Equivalent to:

```rust,ignore
resource!(Ping {
    get => json!({"pong": true})
});
```

## extends_table!

Override behavior on an auto-generated table resource. Only the methods you define are overridden; all others delegate to the default table implementation.

```rust,ignore
extends_table!(Product {
    get(request, ctx) => {
        let table = ctx.get_table("Product")?;
        let records = table.get_all().await?;
        ok(json!({"products": records, "count": records.len()}))
    }
});
```

The macro sets `extends_table()` to return the struct name and generates the appropriate `MethodOverrides`.

## Permission overrides (TableExtender)

Declare which methods on a table resource are publicly accessible without authentication:

```rust,ignore
resource!(TableExtender for Product {
    get => allow_read(),
    subscribe => allow_read(),
});
```

Available permission functions:

| Function | Makes public | Applies to |
|----------|-------------|------------|
| `allow_read()` | Read access | `get`, `search`, `subscribe`, `connect` |
| `allow_create()` | Insert access | `post`, `publish` |
| `allow_update()` | Update access | `put`, `patch` |
| `allow_delete()` | Delete access | `delete` |

Multiple methods can map to the same permission. Duplicate permissions are automatically deduplicated:

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

## Method macros

Method macros simplify trait implementations:

```rust,ignore
impl Resource for MyResource {
    fn name(&self) -> &str { "my" }

    get!(request, ctx, {
        ok(json!({"method": "GET"}))
    });

    post!(request, ctx, {
        let body = request.json_value()?;
        created(body)
    });
}
```

Available: `get!`, `post!`, `put!`, `patch!`, `delete!`, `search!`.

## async_handler!

Wraps an async block into a `ResourceFuture`. Use this when implementing the `Resource` trait directly:

```rust,ignore
impl Resource for MyResource {
    fn name(&self) -> &str { "my" }

    fn get(&self, _req: Request<Vec<u8>>, ctx: ResourceParams) -> ResourceFuture {
        async_handler!({
            let table = ctx.get_table("Data")?;
            let all = table.get_all().await?;
            ok(json!(all))
        })
    }
}
```

## export_plugin!

Declares which resources the plugin exports. Placed at the end of `lib.rs` (auto-generated by the compiler):

```rust,ignore
// Export multiple resources
export_plugin!(Items, Summary, Health);

// Extension-only plugin (no resources)
export_plugin!();
```

## register_resource!

Manual resource registration. Only needed when implementing the `Resource` trait directly instead of using `resource!`:

```rust,ignore
pub struct CustomResource;

impl Default for CustomResource {
    fn default() -> Self { Self }
}

impl Resource for CustomResource {
    fn name(&self) -> &str { "custom" }
    // ... method implementations
}

register_resource!(CustomResource);
```

The `resource!` macro calls `register_resource!` automatically.

## Resource trait reference

For completeness, the full `Resource` trait that macros implement:

```rust,ignore
pub trait Resource: Send + Sync {
    fn name(&self) -> &str;
    fn is_default(&self) -> bool { false }
    fn extends_table(&self) -> Option<&str> { None }
    fn method_overrides(&self) -> MethodOverrides { Default::default() }

    fn get(&self, req: Request<Vec<u8>>, params: ResourceParams) -> ResourceFuture;
    fn post(&self, req: Request<Vec<u8>>, params: ResourceParams) -> ResourceFuture;
    fn put(&self, req: Request<Vec<u8>>, params: ResourceParams) -> ResourceFuture;
    fn patch(&self, req: Request<Vec<u8>>, params: ResourceParams) -> ResourceFuture;
    fn delete(&self, req: Request<Vec<u8>>, params: ResourceParams) -> ResourceFuture;
    fn search(&self, req: Request<Vec<u8>>, params: ResourceParams) -> ResourceFuture;

    fn subscribe(&self, req: Request<Vec<u8>>, params: ResourceParams) -> SubscriptionFuture;
    fn publish(&self, req: Request<Vec<u8>>, params: ResourceParams) -> ResourceFuture;
    fn connect(&self, req: Request<Vec<u8>>, params: ResourceParams) -> ConnectionFuture;

    fn allow_read(&self, access: &dyn AccessControl, target: &RequestTarget, params: &ResourceParams) -> bool;
    fn allow_create(&self, access: &dyn AccessControl, data: &Value, target: &RequestTarget, params: &ResourceParams) -> bool;
    fn allow_update(&self, access: &dyn AccessControl, data: &Value, target: &RequestTarget, params: &ResourceParams) -> bool;
    fn allow_delete(&self, access: &dyn AccessControl, target: &RequestTarget, params: &ResourceParams) -> bool;
    fn allow_subscribe(&self, access: &dyn AccessControl, target: &RequestTarget, params: &ResourceParams) -> bool;
    fn allow_connect(&self, access: &dyn AccessControl, target: &RequestTarget, params: &ResourceParams) -> bool;
    fn allow_publish(&self, access: &dyn AccessControl, target: &RequestTarget, params: &ResourceParams) -> bool;
}
```

All methods except `name()` have default implementations. HTTP methods default to 405 Method Not Allowed. Authorization methods default to RBAC checks against `AccessControl`. `allow_publish` defaults to super_user only.
