# Application Configuration

Reference for `config.yaml` files at `~/yeti/applications/{app-id}/config.yaml`.

## Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Human-readable application name |
| `app_id` | string | no | Application identifier (defaults to directory name, used as URL prefix) |
| `version` | string | no | Semantic version (e.g., `"1.0.0"`) |
| `description` | string | no | Application description |

## Application State

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Whether the application loads at startup |
| `extension` | boolean | `false` | Whether this app provides an extension (shared service) |
| `require_super_user` | boolean | `false` | Require super_user role for all routes |
| `route_prefix` | string | `"/{app_id}"` | Custom route prefix override |

When `extension: true`, the compiler scans source files for `struct {TypeName}Extension` and generates registration code automatically.

When `require_super_user: true`, unauthenticated users receive 401 and non-super_user users receive 403 on all routes, even in development mode.

## Interface Flags

Control which protocols are exposed. Individual schemas can override per-table using `@export` directives.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rest` | boolean | `true` | Enable REST API endpoints |
| `graphql` | boolean | `true` | Enable GraphQL endpoint at `/{app-id}/graphql` |
| `ws` | boolean | `false` | Enable WebSocket subscriptions |
| `sse` | boolean | `false` | Enable Server-Sent Events streaming |
| `mcp` | boolean | `false` | Enable MCP (Model Context Protocol) endpoint |

## Schemas

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `schemas` | string[] | `[]` | List of `.graphql` schema file paths |

Applications without tables should omit the `schemas` section entirely.

## Resources

Custom resource files compiled as dynamic library plugins. Supports glob patterns.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `resources` | string[] | `[]` | Rust source file paths or glob patterns |

## Static Files

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `static_files.path` | string | - | Directory containing static files (relative to app directory) |
| `static_files.route` | string | `"/"` | URL route prefix |
| `static_files.index` | string | `"index.html"` | Default file for directory requests |

## Extension Configuration

Per-app extension configuration uses top-level keys:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `auth` | object | - | Auth extension config (JWT settings, OAuth providers) |
| `vectors` | object | - | Vector extension config (defaultModel, etc.) |

The older `extensions:` list format is deprecated but still supported.

```yaml
# New style (preferred)
auth:
  jwt:
    secret: "${JWT_SECRET:-dev-secret}"

vectors:
  defaultModel: "BAAI/bge-small-en-v1.5"

# Old style (deprecated)
extensions:
  yeti-auth:
    jwt:
      secret: "${JWT_SECRET:-dev-secret}"
```

## Dependencies

Rust crate dependencies for the compiled plugin.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `dependencies` | map | `{}` | Crate name to version mapping |

```yaml
dependencies:
  argon2: "0.5"
  jsonwebtoken: { version: "10.3", features: ["rust_crypto"] }
```

## Data Loader

Seed data files to load on first startup.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `dataLoader` | string | - | Glob pattern for seed data files |

```yaml
dataLoader: data/*.json
```

## Audit Configuration

Per-app audit trail settings. Only takes effect when global `audit.enabled` is true in yeti-config.yaml.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `audit.protocol.mcp` | boolean | `false` | Audit MCP requests |

## Custom Configuration

Accessible via `ctx.config()` in resource handlers and `params.extension_config()` for extensions. Any top-level keys not recognized by Yeti are captured as custom configuration.

```yaml
custom:
  jwt:
    secret: "${JWT_SECRET:-development-secret}"
    access_ttl: 900

origin:
  url: "https://www.example.com/"
```

## See Also

- [Schema Directives](schema-directives.md) - Table and field directives
- [Server Configuration](server-config.md) - Server-level settings
- [Building Extensions](../guides/building-extensions.md) - Extension development
