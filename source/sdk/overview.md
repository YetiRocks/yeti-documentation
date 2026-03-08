# SDK Overview

yeti-sdk provides everything a plugin needs through a single import:

```rust,ignore
use yeti_sdk::prelude::*;
```

This re-exports all macros, traits, types, and helper functions used in resource and extension development.

## Categories

| Category | What it provides |
|----------|-----------------|
| [Resource Macros](resource-macros.md) | `resource!`, `simple_resource!`, `extends_table!`, `export_plugin!` |
| [Request Parsing](request-parsing.md) | `RequestBodyExt`, `RequestExt` - typed body parsing, headers, metadata |
| [Response Helpers](response-helpers.md) | `ok()`, `reply()`, `ok_json!()` - three layers of response building |
| [Table Access](table-access.md) | `Table`, `Tables` - CRUD, search, aggregation, query builder |
| [ResourceParams](resource-params.md) | `ctx` - path params, query params, config, auth, extensions |
| [Utilities](utilities.md) | ID generation, CSV parsing, bulk import, JSON helpers, cookies |
| [Extension API](extension-api.md) | `Extension` trait, lifecycle hooks, middleware, auth providers |

## Minimal example

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Hello {
    get => json!({"message": "Hello, World!"})
});

export_plugin!(Hello);
```

This creates `GET /my-app/hello` and exports it as a loadable plugin.
