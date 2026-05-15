# Resource Macros

`resource!()` is the primary macro for defining HTTP resources. It
emits a unit struct, an `impl ResourceMetadata` (routing + auth
predicates), and per-verb `tower::Service<Context>` impls — then
auto-registers the resource with the runtime.

## resource! — basic

```rust,ignore
use yeti_sdk::prelude::*;

// Simple — no context
resource!(Health {
    get => json!({"status": "ok"})
});
```

Struct name lower-cased becomes the route: `GET /{app}/health`.

## With context

Pass a parameter to access the request `Context`:

```rust,ignore
resource!(Items {
    get(ctx) => {
        let table = ctx.table("Items")?;
        let id    = ctx.require_id()?;
        ok(table.get(id).await?)
    },
    post(ctx) => {
        let body  = ctx.require_json_body()?;
        let table = ctx.table("Items")?;
        let id    = body["id"].as_str().unwrap_or("unknown");
        table.put(id, body.clone()).await?;
        created(body)
    },
    delete(ctx) => {
        ctx.table("Items")?.delete(ctx.require_id()?).await?;
        no_content()
    }
});
```

Parameter name is arbitrary (`ctx`, `c`, `request`, …).

## Custom path

```rust,ignore
resource!(MyHandler {
    name = "custom-path",
    get => json!({"served_at": "/app/custom-path"})
});
// → GET /{app}/custom-path
```

## Catch-all

```rust,ignore
resource!(Fallback {
    default = true,
    get(ctx) => not_found(&format!("No resource at {}", ctx.path_id))
});
```

`name` and `default` combine in either order.

## Stateful — `fields { ... }`

Resources can hold state. Inside handlers, fields are accessible via
`self`. The `fields` form does **not** support a context parameter
(use a sub-method or capture into a closure).

```rust,ignore
use std::sync::atomic::{AtomicU64, Ordering};

resource!(Counter {
    fields { count: Arc<AtomicU64> },
    get => {
        let n = self.count.fetch_add(1, Ordering::Relaxed);
        ok(json!({"count": n}))
    }
});
```

## Supported verbs

Each verb accepts the `ident => body` or `ident(ctx) => body` shape.

| Verb | HTTP method |
|---|---|
| `get` | `GET` |
| `post` | `POST` |
| `put` | `PUT` |
| `patch` | `PATCH` |
| `delete` | `DELETE` |
| `search` | `SEARCH` |

Real-time verbs (defined on the underlying traits, not via the basic
`resource!()` macro):

| Verb | Trigger |
|---|---|
| `subscribe` | SSE stream |
| `publish` | MQTT publish |
| `connect` | WebSocket open |

## extends_table! — augment a table

Override behavior on an auto-generated table resource. Only declared
methods are overridden; everything else delegates to the default
table implementation.

```rust,ignore
extends_table!(Product {
    get => json!({"message": "custom product listing"})
});
```

For context access in a table extender, use the `TableExtender` form
of `resource!()` (see below).

## Permission overrides — `TableExtender`

Declare publicly-accessible methods on a table without writing real
handler code:

```rust,ignore
resource!(TableExtender for Chat {
    get        => allow_read(),
    post       => allow_create(),
    put        => allow_update(),
    patch      => allow_update(),
    delete     => allow_delete(),
    subscribe  => allow_read(),
});
```

| Helper | Permits |
|---|---|
| `allow_read()` | `get`, `search`, `subscribe`, `connect` |
| `allow_create()` | `post`, `publish` |
| `allow_update()` | `put`, `patch` |
| `allow_delete()` | `delete` |

Multiple verbs mapping to the same permission are deduplicated.

For declarative schema-side gating, prefer
`@access(public: [read, subscribe])` in `schema.graphql`. Use
`TableExtender` only when permissions need code-level logic.

## reply() — response builder

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

Builder methods: `.code(status)`, `.header(name, value)`, `.json(v)`,
`.text(s)`, `.html(s)`.

### Helpers

| Function | Result |
|---|---|
| `ok(value)` | 200 + JSON |
| `created(value)` | 201 + JSON |
| `no_content()` | 204 empty |
| `not_found(msg)` | 404 error |
| `bad_request(msg)` | 400 error |
| `unauthorized(msg)` | 401 error |
| `json_response(status, value)` | custom status + JSON |
| `html_response(content)` | 200 + `text/html` |
| `text_response(content)` | 200 + `text/plain` |

## Trait reference

The `resource!()` macro emits these:

```rust,ignore
use yeti_types::resource::ResourceMetadata;

pub trait ResourceMetadata: Send + Sync + 'static {
    fn name(&self) -> &str;
    fn is_default(&self) -> bool { false }
    fn attribute_names(&self) -> Option<Arc<Vec<String>>> { None }
    fn extends_table(&self) -> Option<&str> { None }
    fn method_overrides(&self) -> MethodOverrides { Default::default() }

    // Permission predicates — read from Context.access (RBAC)
    fn allow_read(&self, ctx: &Context) -> bool;
    fn allow_create(&self, ctx: &Context) -> bool;
    fn allow_update(&self, ctx: &Context) -> bool;
    fn allow_delete(&self, ctx: &Context) -> bool;
    fn allow_subscribe(&self, ctx: &Context) -> bool;
    fn allow_connect(&self, ctx: &Context) -> bool;
    fn allow_publish(&self, ctx: &Context) -> bool;
}
```

Plus one `impl tower::Service<Context>` per declared verb. The macro
hides this; you write `get(ctx) => ...` and get a `Service<Context>`
that the router dispatches via the auto-generated method bindings.

### When to bypass the macro

If you need behavior the macro can't express — streaming responses
beyond the standard verbs, multi-method dispatch from one handler,
custom `Service<R>` layers — implement `ResourceMetadata` directly
and provide your own `Service<Context>` impls. The dispatcher only
sees the trait surface; the macro is convenience, not a contract.

## See also

- [Request Parsing](request-parsing.md) — the `Context` API
- [Table Access](table-access.md) — `ctx.table()`, `Query`, CRUD
- [Plugin API](plugin-api.md) — `Plugin` trait, the cross-cutting analog
