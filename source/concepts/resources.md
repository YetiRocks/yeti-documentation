# Resources

Resources are custom HTTP handlers written in Rust. They extend or override auto-generated table endpoints with business logic.

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Greeting {
    get => json!({"greeting": "Hello, World!"})
});
```

Creates `GET /{app-id}/greeting`. The `resource!` macro handles struct definition, trait implementation, and plugin registration.

Place `.rs` files in `resources/` and reference them in `config.yaml`:

```yaml
resources:
  - resources/*.rs
```

Resources compile to dynamic libraries and load at runtime. Initial compilation takes ~2 minutes; cached rebuilds are fast.

For HTTP calls, use `fetch()` from `yeti_sdk::prelude`. Do not use `reqwest::blocking::Client` -- crashes in dylib context.

For the full API - request parsing, response helpers, table access, `fetch()` usage, manual trait implementation - see [Custom Resources](../guides/custom-resources.md).

## Routing Priority

Yeti generates routes automatically from schemas and resources. Every `@export`ed table and every resource file produces HTTP endpoints under the app's URL prefix:

```
https://localhost:9996/{app-id}/{resource-or-table}
```

When multiple handlers could match a request, they resolve in this order:

1. **Custom resources** (exact name match)
2. **Table endpoints** (auto-generated from `@export`)
3. **Default resource** (catch-all, one per app)
4. **Static files** (from `web/` directory)
5. **404 Not Found**

A custom resource with the same name as a table takes precedence. Unoverridden methods fall through to the default table handler.

A default resource catches all unmatched paths within an app:

```rust,ignore
resource!(SpaFallback {
    default = true,
    get => ok_html(include_str!("../web/index.html"))
});
```

See also: [REST API](../api/rest.md), [Custom Resources](../guides/custom-resources.md), [Static File Serving](../guides/static-files.md).
