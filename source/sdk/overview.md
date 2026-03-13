# SDK Overview

The Yeti SDK (`yeti-sdk`) provides everything a plugin needs to build HTTP resources and extensions. A single import brings in all macros, traits, types, and helpers:

```rust,ignore
use yeti_sdk::prelude::*;
```

## What the prelude provides

| Category | Key exports |
|----------|------------|
| [Resource Macros](resource-macros.md) | `resource!`, `simple_resource!`, `extends_table!`, `export_plugin!`, `register_resource!` |
| [Request Parsing](request-parsing.md) | `RequestBodyExt`, `RequestExt`, `JsonValueExt` |
| [Response Helpers](response-helpers.md) | `ok()`, `reply()`, `ok_json!()`, `created()`, `error_response()` |
| [Table Access](table-access.md) | `Table`, `Tables`, `TableExt`, `KvBackend`, `QueryBuilder` |
| [ResourceParams](resource-params.md) | Path/query params, `ParamBuilder`, table access, config, auth |
| [Utilities](utilities.md) | `fetch()`, cookies, tokens, IDs, timestamps, CSV, validation, logging |
| [Extension API](extension-api.md) | `Extension` trait, `ExtensionContext`, `VectorHook`, `EventSubscriber` |

The prelude also re-exports commonly used external types: `Request`, `Response`, `StatusCode`, `json!`, `Value`, `HashMap`, `Arc`, `Serialize`, `Deserialize`, and more.

## Plugin architecture

Yeti plugins compile to dynamic libraries (`.dylib`). The compiler reads your `config.yaml`, copies resource `.rs` files into a build cache, generates a `lib.rs` that wires everything together, and compiles the result. You write individual resource files; the toolchain handles the rest.

Each resource file defines a struct that implements the `Resource` trait (usually via the `resource!` macro) and is exported via `export_plugin!()` in the generated `lib.rs`.

## Minimal example

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Hello {
    get => json!({"message": "Hello, World!"})
});

export_plugin!(Hello);
```

This registers a resource at `GET /my-app/hello` and exports it as a loadable plugin.

## Full CRUD example

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Items {
    get(request, ctx) => {
        let table = ctx.get_table("Items")?;
        match ctx.id() {
            Some(id) => {
                let item = table.get_or_404(id).await?;
                ok(item)
            },
            None => {
                let all = table.get_all().await?;
                ok(json!(all))
            }
        }
    },
    post(request, ctx) => {
        let table = ctx.get_table("Items")?;
        let body = request.json_value()?;
        let created = table.create(body).await?;
        created(created)
    },
    put(request, ctx) => {
        let table = ctx.get_table("Items")?;
        let id = ctx.require_id()?;
        let body = request.json_value()?;
        table.put(id, body.clone()).await?;
        ok(body)
    },
    delete(request, ctx) => {
        let table = ctx.get_table("Items")?;
        let id = ctx.require_id()?;
        table.delete(id).await?;
        no_content()
    }
});

export_plugin!(Items);
```

## Dylib constraints

Code running inside plugins (resources and extensions) executes in a dynamically loaded library. This imposes several constraints:

- **No `tracing::info!`** -- use `yeti_log!` instead (tracing TLS is isolated per dylib)
- **No `tokio::spawn`** -- causes crashes. Use `futures::stream::unfold` for async patterns
- **No `reqwest::blocking::Client`** -- crashes due to internal tokio conflict. Use `fetch()` for HTTP
- **No host statics** -- `OnceLock` values in yeti-core are duplicated in dylib memory
- **Methods on host types run in dylib context** -- even methods defined in yeti-core execute the dylib's compiled copy when called from plugin code
