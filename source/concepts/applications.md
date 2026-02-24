# Applications

An application is a self-contained unit deployed to the platform. Each bundles its configuration, schemas, custom logic, seed data, and optional static files into a single directory. Applications are isolated - each gets its own database namespace and URL prefix.

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

schemas:
  - schema.graphql

resources:
  - resources/*.rs

static_files:
  path: web
  route: "/"
  index: index.html

dataLoader: data/*.json

extensions:
  - yeti-auth:
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
| `rest` / `graphql` / `ws` / `sse` | Enable protocol interfaces |
| `schemas` | GraphQL SDL files that define tables |
| `resources` | Glob patterns for custom Rust handlers |
| `static_files` | Serve a directory of static files |
| `dataLoader` | JSON seed data files |
| `extensions` | Extensions to use, with per-app config |
| `dependencies` | Rust crate dependencies for resources |

## Discovery

Yeti scans `~/yeti/applications/*/` for directories with a `config.yaml`. Drop a directory and restart. Apps with `enabled: false` are discovered but not loaded.

## Isolation

- **URL prefix**: All routes are under `/{app-id}/`
- **Database namespace**: `@table(database: "...")` controls storage isolation
- **Route space**: Resources and tables share the app's route space but can't conflict with other apps

## Extensions

Apps with `extension: true` provide shared services to other apps. They load first and can supply auth, telemetry, and middleware. Consumer apps opt in via the `extensions:` field. See [Extensions](extensions.md).

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
  route: /
  index: index.html
```
