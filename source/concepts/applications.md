# Applications

A self-contained directory bundling configuration, schemas, custom logic, and optional static files. Each application gets its own database namespace and URL prefix.

## Directory Structure

```
~/yeti/applications/my-app/
  config.yaml          # Required
  schemas/             # Table definitions
    schema.graphql
  resources/           # Custom Rust handlers
    greeting.rs
  modules/             # Shared Rust modules
    helpers.rs
  bin/                 # Standalone binaries
    worker.rs
  data/                # Seed data
    users.json
  web/                 # Static files
    index.html
```

Only `config.yaml` is required. The compiler generates `Cargo.toml`, `build.rs`, and `source/` (including `lib.rs`) automatically. Do not edit generated files.

## Configuration

```yaml
name: "My Application"
app_id: "my-app"
version: "1.0.0"
enabled: true

rest: true
graphql: true
mcp: false

schemas:
  path: "schemas/*.graphql"

resources:
  path: "resources/*.rs"
  route: "/api"

static:
  path: web
  route: /
  spa: true

modules:
  - "modules/*.rs"

binaries:
  - "bin/*.rs"

hooks:
  pre_request:
    - "./scripts/rate_limit.sh"
  post_request:
    - "./scripts/log_request.sh"
  post_request_failure:
    - "./scripts/alert_on_failure.sh"

dataLoader: "data/*.json"

auth:
  oauth:
    rules:
      - strategy: provider
        pattern: "github"
        role: standard

dependencies:
  serde_yaml: "0.9"
```

| Field | Purpose |
|-------|---------|
| `app_id` | URL prefix and database namespace |
| `enabled` | Toggle the app on/off (default: true) |
| `rest` / `graphql` / `mcp` | Enable protocol interfaces per app |
| `schemas` | Object with `path` -- glob patterns for GraphQL SDL files |
| `resources` | Object with `path` and `route` -- Rust handlers and their URL prefix (default route: `/api`) |
| `static` | Object with `path`, `route`, `spa` -- serve a directory of static files (aliases: `static_files`, `staticFiles`) |
| `modules` | Shared Rust modules compiled as `pub mod` alongside resources |
| `binaries` | Standalone Rust executables compiled alongside the plugin dylib |
| `hooks` | Shell commands executed around resource dispatch (pre/post request) |
| `dataLoader` | Glob pattern for JSON seed data files |
| `auth` / `telemetry` / `audit` | Per-app service config (opt-in via top-level keys) |
| `dependencies` | Rust crate dependencies for resources |
| `required_roles` | Role names required to access this app (empty = unrestricted) |
| `request_timeout` | Handler timeout in seconds (default: 30) |

## Discovery

Yeti scans `~/yeti/applications/*/` for directories containing a `config.yaml`. Drop a directory in and restart. Apps with `enabled: false` are discovered but not loaded.

## Isolation

- **URL prefix**: All routes are under `/{app-id}/` (unless designated as the `root_app` in `yeti-config.yaml`)
- **Database namespace**: `@table(database: "...")` controls storage isolation
- **Route space**: Resources and tables share the app's route space but cannot conflict with other apps

## Protocols

Server-wide protocol toggles live in `yeti-config.yaml` under `interfaces:`. Per-app toggles in `config.yaml` control which protocols each app exposes:

- **REST** / **GraphQL** -- toggled per app via `rest:`, `graphql:`
- **MCP** (Model Context Protocol) -- per-app via `mcp: true`. Exposes a JSON-RPC 2.0 endpoint at `/{app-id}/mcp`
- **gRPC** -- server-wide only (`interfaces.grpc.enabled`). Exposes all `@export`ed tables via a gRPC tables service on the same port
- **MQTT** -- server-wide (`interfaces.mqtt.enabled`). Native MQTTS on port 8883, WebSocket proxy at `/mqtt`
- **SSE** / **WebSocket** -- controlled per-table via `@export(sse: true, ws: true)` in the schema

## Services

Apps with `extension: true` provide shared services to other apps. They load first and supply auth, telemetry, and middleware. Consumer apps opt in via top-level keys (`auth:`, `telemetry:`, `audit:`). See [Services](extensions.md).

## Hooks

Hook commands run as shell processes around resource dispatch. Environment variables provide request context (`HOOK_EVENT`, request metadata). Exit codes control flow:

- **Exit 0** -- allow the request
- **Exit 2** -- deny the request (returns 403 Forbidden)
- **Other exit codes** -- hook failure (logged, does not block the request)

Post-request hooks are fire-and-forget and do not affect the response.

## Naming Conventions

- **app_id**: Lowercase with hyphens: `my-app`, `graphql-explorer`, `yeti-auth`
- **Schema types**: PascalCase: `Product`, `UserProfile`, `OrderItem`
- **Resource files**: snake_case: `greeting.rs`, `page_cache.rs`
- **Seed data files**: Match table names in lowercase: `products.json`, `authors.json`

## Apps Without Tables

Apps that only serve static files or custom endpoints can omit `schemas:` entirely:

```yaml
name: "Documentation"
app_id: "documentation"
version: "1.0.0"
enabled: true
static:
  path: web
  spa: true
```
eb
  spa: true
```
