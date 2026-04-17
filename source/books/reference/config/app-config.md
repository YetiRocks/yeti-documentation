# Application Configuration

Reference for `config.yaml` at `~/yeti/applications/{app-id}/config.yaml`.

## Metadata

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | - | Human-readable application name |
| `app_id` | string | yes | - | Application identifier (URL prefix: `/{app_id}`) |
| `customer_id` | string | no | - | Owning tenant (injected by build server in cloud mode). Alias: `customerId` |

## Application State

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Load at startup; disabled apps are skipped |
| `extension` | boolean | `false` | Global extension (shared service loaded before applications) |
| `required_roles` | string[] or `false` | `[]` | Roles required for access. Missing role = 403; unauthenticated = 401 |
| `request_timeout` | integer | `30` | Handler timeout in seconds (504 on expiry). SSE/WebSocket exempt |
| `route_prefix` | string | - | **Deprecated and ignored.** Use `root_app` in `yeti-config.yaml` instead |

## Schemas

Schema file locations. Omit entirely for apps without tables.

```yaml
schemas:
  path: schemas/*.graphql
```

Or with multiple patterns:

```yaml
schemas:
  path:
    - schemas/core.graphql
    - schemas/extra.graphql
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `schemas.path` | string or string[] | - | Glob pattern(s) for `.graphql` schema files |

## Resources

Custom resource files compiled as dynamic library plugins.

```yaml
resources:
  path: resources/*.rs
  route: /api
```

Or with multiple patterns:

```yaml
resources:
  path:
    - resources/*.rs
    - extra/*.rs
  route: /api
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `resources.path` | string or string[] | - | Glob pattern(s) for Rust source files |
| `resources.route` | string | `"/api"` | URL route prefix. Apps without `resources:` serve tables at `"/"` |

## Modules

Shared library code compiled into the plugin as `pub mod` alongside resource modules.

```yaml
modules:
  - modules/*.rs
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `modules` | string[] | `[]` | Glob patterns for shared module source files |

## Binaries

Standalone executables compiled alongside the plugin. Each `.rs` file becomes a `[[bin]]` target.

```yaml
binaries:
  - bin/*.rs
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `binaries` | string[] | `[]` | Glob patterns for binary source files |

## Static Files

```yaml
static:
  path: web
  route: /
  spa: true
  index: index.html
  build:
    sourceDir: source
    command: npm run build
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `static.path` | string | - | Directory containing static files (relative to app directory) |
| `static.route` | string | `"/"` | URL route prefix |
| `static.spa` | boolean | `false` | SPA mode: serve index.html for unmatched paths (200) so client-side router handles navigation |
| `static.index` | string | `"index.html"` | Default file for directory requests |
| `static.not_found` | string or object | - | Custom 404 page: file path string (served as 404) or `{ file: "path", statusCode: 200 }`. Overrides SPA fallback when both set |
| `static.build` | object | - | Frontend build configuration. Runs the build command before serving |
| `static.build.sourceDir` | string | `"source"` | Frontend source directory (relative to app directory) |
| `static.build.command` | string | `"npm run build"` | Build command to run |

Config key aliases: `static_files`, `staticFiles`, `static_config`.

The `build` section uses `camelCase` field names (`sourceDir`, not `source_dir`).

## Hooks

Shell commands around resource dispatch. See [Resource Hooks](../guides/resource-hooks.md).

```yaml
hooks:
  pre_request:
    - "./hooks/validate.sh"
  post_request:
    - "./hooks/audit-log.sh"
  post_request_failure:
    - "./hooks/alert.sh"
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `hooks.pre_request` | string[] | `[]` | Run before handler. Exit 0 = allow, exit 2 = deny (403), other = hook failure |
| `hooks.post_request` | string[] | `[]` | Run after successful response. Fire-and-forget |
| `hooks.post_request_failure` | string[] | `[]` | Run after error response. Fire-and-forget |

Hooks receive JSON on stdin with method, path, app_id, resource_id, auth identity, status, and latency.

## Interface Flags

Protocol flags at the app level. Individual tables override via `@export` directives.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rest` | boolean | `true` | REST API endpoints |
| `graphql` | boolean | `true` | GraphQL endpoint |
| `mcp` | boolean | `false` | MCP endpoint (auto-enabled when any table has `@export(mcp: true)`) |

## Extension Configuration

Per-app extension settings declared as top-level keys using the extension's short name. Captured via the `custom` config flatten and resolved by the extension at runtime.

Built-in short names: `auth`, `vectors`, `telemetry`, `audit`, `applications`.

### Auth Configuration

Requires the yeti-auth service.

```yaml
auth:
  signup: auto
  default_role: viewer
  methods: [oauth, basic]
  oauth:
    google:
      clientId: "${GOOGLE_CLIENT_ID}"
      clientSecret: "${GOOGLE_CLIENT_SECRET}"
    rules:
      - strategy: email
        pattern: "*@mycompany.com"
        role: admin
```

| Field | Type | Description |
|-------|------|-------------|
| `auth.signup` | string | `"auto"` enables auto-signup on first login |
| `auth.default_role` | string | Role assigned when no rule matches |
| `auth.methods` | string[] | Enabled auth methods: `basic`, `jwt`, `oauth`, `mtls` |
| `auth.oauth` | object | OAuth provider configuration (keyed by provider name) |
| `auth.oauth.{provider}.clientId` | string | OAuth client ID |
| `auth.oauth.{provider}.clientSecret` | string | OAuth client secret |
| `auth.oauth.rules` | array | Provider-to-role mapping rules |

See [Authentication & Authorization](../guides/auth-overview.md).

## Auth Loader

Simplified role/user JSON for seeding yeti-auth on first startup. Files are bare arrays (no `database`/`table` wrapper). Permissions are JSON objects (serialized to strings on load). Passwords are plaintext (Argon2id-hashed on load).

```yaml
authLoader:
  roles: auth/roles.json
  users: auth/users.json
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `authLoader.roles` | string | - | Path to roles JSON file (bare array of role records). Optional |
| `authLoader.users` | string | - | Path to users JSON file (bare array of user records). Optional |

Config key alias: `auth_loader`.

## Data Loader

Seed data files loaded on first startup. Accepts either a bare string or an object with a `files` key.

```yaml
# Bare string form
dataLoader: "data/*.json"

# Object form
dataLoader:
  files: "data/*.json"
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `dataLoader` | string or object | - | Glob pattern for data files, or `{ files: "pattern" }` |
| `dataLoader.files` | string | - | Glob pattern for data files (when using object form) |

Config key alias: `data_loader`.

## Dependencies

Rust crate dependencies for the compiled plugin. Cargo.toml dependency syntax in YAML.

```yaml
dependencies:
  chrono: "0.4"
  jsonwebtoken: { version: "10.3", features: ["aws_lc_rs"] }
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `dependencies` | object | `{}` | Crate name to version string or dependency object. Added to generated Cargo.toml |

## Storage

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `storage_path` | string | `{rootDirectory}/data/` | Custom storage path for RocksDB databases. Priority: per-app `storage_path` > global `storage_path` from server config > `{rootDirectory}/data/` |

## Custom Configuration

Unrecognized top-level keys are captured via `serde(flatten)`. Access at runtime via `params.config().get_str("key", "default")` and typed accessors (`get_i64`, `get_u64`, `get_f64`, `get_bool`). Supports dot notation (e.g. `"origin.url"`).

```yaml
# These are custom -- accessible at runtime
origin:
  url: "https://www.example.com/"
api_keys:
  stripe: "${STRIPE_KEY}"
```

Extension short names (`auth`, `vectors`, `telemetry`, `audit`, `applications`) are captured here and routed to the appropriate extension. See [Extension Configuration](#extension-configuration).

## Complete Example

```yaml
name: "My Application"
app_id: "my-app"
customer_id: "acme"
enabled: true
request_timeout: 30

schemas:
  path: schemas/*.graphql

resources:
  path: resources/*.rs
  route: /api

modules:
  - modules/*.rs

binaries:
  - bin/*.rs

static:
  path: web
  route: /
  spa: true
  index: index.html
  build:
    sourceDir: source
    command: npm run build

auth:
  methods: [oauth]
  oauth:
    google:
      clientId: "${GOOGLE_CLIENT_ID}"
      clientSecret: "${GOOGLE_CLIENT_SECRET}"
    rules:
      - strategy: email
        pattern: "*@acme.com"
        role: admin

authLoader:
  roles: auth/roles.json
  users: auth/users.json

dataLoader: "data/*.json"

hooks:
  pre_request:
    - "./hooks/validate.sh"
  post_request:
    - "./hooks/log.sh"

dependencies:
  chrono: "0.4"

rest: true
graphql: true
mcp: false
```

## See Also

- [Schema Directives](schema-directives.md) -- Table and field directives
- [Server Configuration](server-config.md) -- Server-level settings
- [Building Services](../guides/building-extensions.md) -- Service development
