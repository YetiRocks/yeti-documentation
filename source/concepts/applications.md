# Applications

A self-contained unit bundling configuration, schemas, custom logic, seed data, and optional static files into a single directory. Each application gets its own database namespace and URL prefix.

## Directory Structure

```
~/yeti/applications/my-app/
  config.yaml          # Required
  schema.graphql       # Table definitions
  resources/           # Custom Rust handlers
    greeting.rs
  data/                # Seed data
    users.json
  web/                 # Static files
    index.html
```

Only `config.yaml` is required. The compiler generates `Cargo.toml`, `build.rs`, and `source/` (including `lib.rs`) automatically - do not edit these.

## Configuration

```yaml
name: "My Application"
app_id: "my-app"
version: "1.0.0"
enabled: true

rest: true
graphql: true
ws: true
sse: false
mcp: false

schemas:
  - schema.graphql

resources:
  - resources/*.rs

static_files:
  path: web
  spa: true

dataLoader: data/*.json

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
| `enabled` | Toggle the app on/off |
| `rest` / `graphql` / `ws` / `sse` / `mcp` | Enable protocol interfaces per app |
| `schemas` | GraphQL SDL files that define tables |
| `resources` | Glob patterns for custom Rust handlers (**required** if you have `.rs` files -- without this key, plugin sources won't compile) |
| `static_files` | Serve a directory of static files |
| `dataLoader` | JSON seed data files |
| `auth` / `vectors` | Per-app extension config (replaces deprecated `extensions:` list) |
| `dependencies` | Rust crate dependencies for resources |

## Discovery

Yeti scans `~/yeti/applications/*/` for directories with a `config.yaml`. Drop a directory and restart. Apps with `enabled: false` are discovered but not loaded.

## Isolation

- **URL prefix**: All routes are under `/{app-id}/`
- **Database namespace**: `@table(database: "...")` controls storage isolation
- **Route space**: Resources and tables share the app's route space but can't conflict with other apps

## Protocols

Server-wide protocol toggles live in `yeti-config.yaml` under `interfaces:`. Per-app toggles in `config.yaml` control which protocols an individual app exposes:

- **REST** / **GraphQL** / **WebSocket** / **SSE** -- toggled per app via `rest:`, `graphql:`, `ws:`, `sse:`
- **MCP** (Model Context Protocol) -- per-app via `mcp: true`. Exposes a JSON-RPC 2.0 endpoint at `/{app-id}/mcp`
- **gRPC** -- server-wide only (`interfaces.grpc.enabled`). Exposes all `@export`ed tables via a gRPC tables service on the same port
- **MQTT** -- server-wide (`interfaces.mqtt.enabled`). Native MQTTS on port 8883, WebSocket proxy at `/mqtt`

## Extensions

Apps with `extension: true` provide shared services to other apps. They load first and supply auth, telemetry, and middleware. Consumer apps opt in via top-level keys (`auth:`, `vectors:`). See [Extensions](extensions.md).

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
static_files:
  path: web
  spa: true
```
