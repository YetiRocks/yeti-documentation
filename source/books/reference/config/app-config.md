# Application Configuration

Application metadata lives in `Cargo.toml` at
`~/yeti/applications/{app-id}/Cargo.toml`. Yeti reads
`[package.metadata.app]` plus sibling `[package.metadata.{plugin}]`
blocks for per-plugin config.

The standard cargo fields (`name`, `edition`, `version`) live at the
top of the file where `cargo *` and rust-analyzer can see them.

```toml
[package]
name = "my-app"
edition = "2024"
version = "1.0.0"

[package.metadata.app]
app_id = "my-app"
name = "My Application"
```

## Application metadata

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `app_id` | string | yes | — | URL routing slug (`/{app_id}/...`). Kebab-case, 3–40 chars |
| `name` | string | no | — | Human-readable name |
| `customer_id` | string | no | — | Owning tenant (injected by build server in cloud mode) |
| `enabled` | bool | no | `true` | Load at startup; disabled apps are skipped |
| `plugin` | bool | no | `false` | Global plugin (loaded before user apps) |
| `required_roles` | string[] | no | `[]` | Role names required for access. Missing role = 403; unauthenticated = 401 |
| `request_timeout` | int (s) | no | `30` | Handler timeout (504 on expiry; SSE/WS exempt) |
| `storage_path` | string | no | `{rootDirectory}/data/` | Override RocksDB storage path |

`[package].name` is the cargo crate identity *and* the human-readable
name. It's the only string a developer routinely types for the app.
`app_id` is the URL routing slug; usually it matches `package.name`
but the loader treats them as independent.

## Schemas, resources, static files

Source globs are either scalars (single path) or `{ path = "..." }` tables.

```toml
[package.metadata.app]
schemas   = { path = "schemas/*.graphql" }
resources = { path = "resources/*.rs", route = "/api" }
modules   = "modules/*.rs"
binaries  = "bin/*.rs"
static    = { path = "web", root = "/", spa = true, source = "source", build = "npm run build" }
loaders   = { data = "data/*.json", auth = ["auth/roles.json", "auth/users.json"] }
```

| Field | Type | Description |
|---|---|---|
| `schemas.path` | string \| string[] | Glob(s) for `.graphql` files. Omit entirely for apps without tables |
| `resources.path` | string \| string[] | Glob(s) for Rust handler files |
| `resources.route` | string | URL route prefix (default `"/api"`; apps without `resources` serve tables at `"/"`) |
| `modules` | string \| string[] | Glob(s) for shared `pub mod` files |
| `binaries` | string \| string[] | Glob(s) for `bin/*.rs`; each becomes a `[[bin]]` target |
| `static` | object | Static file mount (see below) |
| `loaders.data` | string \| string[] | Glob(s) for JSON/CSV seed files |
| `loaders.auth` | string[] | Auth-seed files; basename routes to `Role` / `User` tables |

### Static files

```toml
static = { path = "web", root = "/", spa = true, index = "index.html", not_found = "404.html", source = "source", build = "npm run build" }
```

| Field | Default | Description |
|---|---|---|
| `path` | — | Directory containing built static files (relative to app dir) |
| `root` | `"/"` | URL route prefix |
| `spa` | `false` | SPA mode: serve `index.html` for unmatched paths (status 200) |
| `index` | `"index.html"` | Default file for directory requests |
| `not_found` | — | Custom 404 page: string path (served as 404), or `{ file, statusCode }` |
| `source` | — | Frontend source directory; build runs here |
| `build` | — | Build command run before serving (e.g. `"npm run build"`) |

`not_found = "404.html"` distinguishes "custom error page" from
`spa = true` "client-side router". With both unset, missing paths
return the platform JSON 404.

## Protocol toggles

```toml
[package.metadata.app]
rest    = true
graphql = true
ws      = true
sse     = true
mqtt    = true
mcp     = true
grpc    = true
```

All default to `true`. Server-wide caps and toggles live in
`yeti-config.yaml` `[interfaces]`. Per-table overrides happen via
`@export(rest: false, ...)` in the schema.

## Plugin configuration

Per-app plugin settings live in sibling
`[package.metadata.{plugin-name}]` blocks. Each plugin parses its own
block at load time.

Built-in plugin keys: `auth`, `vectors`, `telemetry`, `audit`.

### Auth

```toml
[package.metadata.auth]
signup = "auto"
default_role = "viewer"
methods = ["oauth", "basic"]

[package.metadata.auth.oauth]
providers = [
  { name = "google", client_id = "${GOOGLE_CLIENT_ID}", client_secret = "${GOOGLE_CLIENT_SECRET}" }
]
rules = [
  { strategy = "email", pattern = "*@mycompany.com", role = "admin" }
]
```

| Field | Description |
|---|---|
| `signup` | `"auto"` enables auto-signup on first login |
| `default_role` | Role assigned when no `rules` entry matches |
| `methods` | Enabled auth methods: `basic`, `jwt`, `oauth`, `mtls` |
| `oauth.providers` | Array of `{ name, client_id, client_secret }`. Env-var interpolation supported |
| `oauth.rules` | Provider-to-role mapping rules; first match wins |

See [Authentication](../../guides/auth/overview.md) for the full surface.

### Vectors / Telemetry / Audit

Each plugin's metadata block follows the same pattern. See the plugin
guides:

- [Vector Search](../../guides/querying/vector-search.md)
- [Telemetry](../architecture/telemetry.md)
- [Auditing](../../guides/observability/auditing.md)

## Dependencies

Standard cargo dependencies for resources. **Don't** add `yeti-sdk`
here — the scaffolder injects it via the workspace.

```toml
[dependencies]
chrono = "0.4"
jsonwebtoken = { version = "10.3", features = ["aws_lc_rs"] }
```

## Complete example

```toml
[package]
name = "my-app"
edition = "2024"
version = "1.0.0"

[package.metadata.app]
app_id = "my-app"
name = "My Application"
customer_id = "acme"
request_timeout = 30

schemas   = { path = "schemas/*.graphql" }
resources = { path = "resources/*.rs", route = "/api" }
modules   = "modules/*.rs"
binaries  = "bin/*.rs"
static    = { path = "web", root = "/", spa = true, source = "source", build = "npm run build" }
loaders   = { data = "data/*.json", auth = ["auth/roles.json", "auth/users.json"] }

rest = true
graphql = true
mcp = false

[package.metadata.auth]
methods = ["oauth"]

[package.metadata.auth.oauth]
providers = [
  { name = "google", client_id = "${GOOGLE_CLIENT_ID}", client_secret = "${GOOGLE_CLIENT_SECRET}" }
]
rules = [
  { strategy = "email", pattern = "*@acme.com", role = "admin" }
]

[dependencies]
chrono = "0.4"
```

## See also

- [Schema Directives](schema-directives.md) — table and field directives
- [Server Configuration](server-config.md) — `yeti-config.yaml`
- [Plugin API](../sdk/plugin-api.md) — the `Plugin` trait that consumes these metadata blocks
