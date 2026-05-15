# Applications

A self-contained directory bundling configuration, schemas, custom
logic, and optional static files. Each application gets its own
database namespace and URL prefix.

## Directory structure

```
~/yeti/applications/my-app/
  Cargo.toml          # Required — manifest holds [package.metadata.app]
  schemas/            # Table definitions
    schema.graphql
  resources/          # Custom Rust handlers
    greeting.rs
  modules/            # Shared Rust modules
    helpers.rs
  bin/                # Standalone binaries
    worker.rs
  data/               # Seed data (JSON, CSV)
    users.json
  web/                # Static files
    index.html
```

Only `Cargo.toml` is required. The compiler generates `src/lib.rs` and
the build scaffolding from the manifest — don't edit generated files.

## Configuration

App metadata lives under `[package.metadata.app]` in `Cargo.toml`.
Standard cargo fields (`name`, `edition`, `version`) sit at the top
where rust-analyzer and `cargo *` commands can see them.

```toml
[package]
name = "my-app"
edition = "2024"
version = "1.0.0"

[package.metadata.app]
app_id = "my-app"
name = "My Application"
enabled = true

# Protocols (each defaults to true)
rest = true
graphql = true
mcp = false

# Source globs
schemas = { path = "schemas/*.graphql" }
resources = { path = "resources/*.rs", route = "/api" }
static = { path = "web", root = "/", spa = true }
modules = "modules/*.rs"
binaries = "bin/*.rs"

# Seed data + auth-seed (basename routes Roles/Users into yeti-auth)
loaders = { data = "data/*.json", auth = ["auth/roles.json"] }

# Per-app auth (each plugin has its own [package.metadata.<plugin>] block)
[package.metadata.auth]
methods = ["basic", "oauth"]

[package.metadata.auth.oauth]
providers = [{ name = "github", client_id = "${GITHUB_CLIENT_ID}", client_secret = "${GITHUB_CLIENT_SECRET}" }]
rules = [{ strategy = "provider", pattern = "github", role = "standard" }]

# Cargo dependencies for resources/
[dependencies]
serde = "1"
```

| Field | Purpose |
|---|---|
| `app_id` | URL prefix and database namespace |
| `name` | Human-readable name |
| `enabled` | Toggle on/off (default `true`) |
| `rest` / `graphql` / `mcp` / `ws` / `sse` / `mqtt` / `grpc` | Per-protocol toggles (default `true`) |
| `schemas` | `{ path = "..." }` — glob of GraphQL SDL files |
| `resources` | `{ path = "...", route = "/api" }` — Rust handlers + URL prefix |
| `static` | `{ path, root, spa, index, notfound, build }` — static file mount |
| `modules` | `pub mod` files compiled alongside resources |
| `binaries` | Standalone `bin/*.rs` executables |
| `loaders.data` | Glob of JSON/CSV seed files |
| `loaders.auth` | Auth seed files (basename routes Role/User) |
| `required_roles` | Role names required to access this app (empty = unrestricted) |
| `request_timeout` | Handler timeout in seconds (default 30) |

Plugin-specific config lives under sibling `[package.metadata.{auth,vectors,telemetry,...}]` tables, parsed by each plugin at load time.

## Discovery

Yeti scans `~/yeti/applications/*/` for directories containing a
`Cargo.toml` with `[package.metadata.app]`. Drop a directory in and
restart. Apps with `enabled = false` are discovered but not loaded.

## Isolation

- **URL prefix** — all routes under `/{app-id}/` (unless designated
  as `root_app` in `yeti-config.yaml`).
- **Database namespace** — `@table(database: "...")` controls storage isolation.
- **Route space** — resources and tables share the app's route space but cannot conflict with other apps.

## Protocols

Server-wide protocol toggles live in `yeti-config.yaml` under
`interfaces:`. Per-app toggles in the manifest control which protocols
each app exposes:

- **REST** / **GraphQL** — per app via `rest = true` / `graphql = true`.
- **MCP** — per app via `mcp = true`. JSON-RPC 2.0 endpoint at `/{app-id}/mcp`.
- **gRPC** — server-wide only (`interfaces.grpc.enabled`). All `@export`ed tables on the same port.
- **MQTT** — server-wide (`interfaces.mqtt.enabled`). Native MQTTS on 8883; WS proxy at `/mqtt`.
- **SSE** / **WebSocket** — controlled per-table via `@export(sse: true, ws: true)`.

## Plugins

Apps with `plugin = true` in `[package.metadata.app]` provide shared
services (auth, telemetry, AI, etc.). They load first and register
with the runtime; consumer apps opt in via sibling
`[package.metadata.{plugin-name}]` blocks. See [Plugins](plugins.md).

## Naming conventions

- **app_id** — lowercase kebab: `my-app`, `graphql-explorer`, `yeti-auth`
- **Schema types** — PascalCase: `Product`, `UserProfile`, `OrderItem`
- **Resource files** — snake_case: `greeting.rs`, `page_cache.rs`
- **Seed data files** — match table names in lowercase: `products.json`, `authors.json`

## Apps without tables

Apps that only serve static files or custom endpoints can omit
`schemas` entirely:

```toml
[package]
name = "documentation"
edition = "2024"

[package.metadata.app]
app_id = "documentation"
static = { path = "web", root = "/", spa = true }
```
