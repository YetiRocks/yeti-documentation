# SDK Overview

The Yeti SDK (`yeti-sdk`) is the developer-facing API for building applications. Built on `yeti-types`, it re-exports everything through a single import:

```rust,ignore
use yeti_sdk::prelude::*;
```

## Prelude exports

| Category | Key exports |
|----------|------------|
| [Resource Types](resource-macros.md) | `resource!`, `extends_table!`, `register_resource!`, `Resource`, `Context`, `ContextExt` |
| [Response Builders](response-helpers.md) | `ok()`, `reply()`, `created()`, `no_content()`, `not_found()`, `json_response()`, `html_response()`, `text_response()` |
| [Request Parsing](request-parsing.md) | `RequestBodyExt`, `RequestExt`, `ContextExt::require_json_body()`, `ContextExt::require_id()` |
| [Table Access](table-access.md) | `Table`, `Tables`, `TableExt`, `KvBackend`, `BackendManager` |
| Query & Indexing | `QueryBuilder`, `QueryExt`, `FiqlQuery`, `Condition`, `Comparator` |
| Auth | `AccessControl`, `AuthIdentity`, `AuthProvider`, `AuthHook`, `CookieJar` |
| [Encoding & Crypto](utilities.md) | `base64_encode/decode`, `base64url_encode/decode`, `sha256`, `sha512`, `hmac_sha256`, `hex_encode/decode`, `url_encode/decode`, `KeyEncoder` |
| [Filesystem](utilities.md) | `read_file`, `write_file`, `file_exists`, `mkdir`, `read_dir`, `append_file`, `copy_file`, `remove_file`, `remove_dir` (root-directory-aware) |
| [HTTP Client](utilities.md) | `FetchBuilder`, `FetchResponse`, `fetch!` macro |
| Real-time | `PubSubManager`, `subscribe`, `publish`, `connect` methods on Resource |
| [Logging](utilities.md) | `yeti_log!` macro (dylib-safe, bridges to host tracing) |

The prelude also re-exports: `Request`, `Response`, `StatusCode`, `Method`, `json!`, `Value`, `HashMap`, error types (`YetiError`, `ProblemDetails`, `BadRequest`, `Forbidden`, `NotFoundError`, `Unauthorized`), and `AppRegistration`.

## Application architecture

Applications compile to dynamic libraries (`.dylib`). The compiler reads `Cargo.toml`, copies resource `.rs` files into a build cache, generates a `lib.rs`, and compiles the result. Write individual resource files; the toolchain handles the rest.

Each resource file defines a struct implementing the `Resource` trait (usually via `resource!`). The struct name becomes the route path, lowercased by default.

## Minimal example

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Hello {
    get => json!({"message": "Hello, World!"})
});
```

Registers a resource at `GET /my-app/hello`. The macro generates the struct, implements `Resource`, and registers it for export.

## Context-based example

`Context` carries the full request: method, path, body, headers, auth identity, query parameters, path ID, and table access.

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Items {
    get(ctx) => {
        let table = ctx.get_table("Items")?;
        match ctx.path_id.as_deref() {
            Some(id) => {
                let item = table.get(id).await?;
                ok(item)
            },
            None => {
                let all = table.get_all().await?;
                ok(json!(all))
            }
        }
    },
    post(ctx) => {
        let body = ctx.require_json_body()?.clone();
        let table = ctx.get_table("Items")?;
        let id = body["id"].as_str().unwrap_or("unknown");
        table.put(id, body.clone()).await?;
        created(body)
    },
    delete(ctx) => {
        let id = ctx.require_id()?;
        let table = ctx.get_table("Items")?;
        table.delete(id).await?;
        no_content()
    }
});
```

## Context fields

| Field | Type | Description |
|-------|------|-------------|
| `method` | `http::Method` | HTTP method |
| `path` | `String` | Full request path |
| `body` | `Bytes` | Raw request body |
| `headers` | `HeaderMap` | HTTP headers |
| `app_id` | `Arc<str>` | Application identifier |
| `resource_id` | `Arc<str>` | Resource name |
| `path_id` | `Option<String>` | Record ID from path (e.g. `"123"` from `/Table/123`) |
| `query_params` | `HashMap<String, String>` | Parsed query string |
| `is_collection` | `bool` | True when no ID specified |
| `auth_identity` | `Option<AuthIdentity>` | Authenticated user identity |
| `access` | `Option<Arc<dyn AccessControl>>` | Resolved permissions |

## ContextExt helper methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_table(name)` | `Result<Table>` | Table accessor by name |
| `tables()` | `Result<Tables>` | Accessor for all tables |
| `require_id()` | `Result<&str>` | Path ID or 400 |
| `require_json_body()` | `Result<&Value>` | Parsed JSON body or 400 |
| `auth_identity()` | `Option<&AuthIdentity>` | Authenticated identity |
| `cookie(name)` | `Option<String>` | Cookie value |

## Dylib constraints

Application code runs inside a dynamically loaded library. Constraints:

- **No `tracing::info!`** -- use `yeti_log!` instead (tracing TLS is isolated per dylib)
- **No `tokio::spawn`** -- causes crashes. Use `futures::stream::unfold` for async patterns
- **No `reqwest::blocking::Client`** -- crashes due to internal tokio conflict. Use `fetch!` for HTTP
- **No host statics** -- `OnceLock` values in the host binary are duplicated in dylib memory
