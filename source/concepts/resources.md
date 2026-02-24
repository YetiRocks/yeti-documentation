# Resources

Resources are custom HTTP handlers written in Rust. They extend or override auto-generated table endpoints with business logic.

```rust
use yeti_core::prelude::*;

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

For the full API - request parsing, response helpers, table access, manual trait implementation - see [Custom Resources](../guides/custom-resources.md).
