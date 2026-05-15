# Routing

Two-level routing: DynamicRouter dispatches by app prefix, then each application's AutoRouter resolves to table endpoints, custom resources, or static files.

## URL Structure

```
https://localhost/{app-id}/{resource-or-table}/{id}
```

All routes live under the `app_id` prefix. Resources use `resources.route` (default: `/api`), static files use `static.route` (default: `/`).

## Root App

Designate one application as the root app to serve at `/` instead of `/{app-id}/`:

```yaml
# yeti-config.yaml
root_app: www
```

The root app occupies `/`. All other apps remain under `/{app-id}/`. Only one root app is allowed.

## Resolution Order

When multiple handlers match a request:

1. **Custom resources** (exact name match under `resources.route`)
2. **Table endpoints** (auto-generated from `@export`)
3. **Default resource** (catch-all, one per app)
4. **Static files** (from `static.path` directory under `static.route`)
5. **404 Not Found**

A custom resource with the same name as a table takes precedence. Unoverridden methods fall through to the default table handler.

## Route Defaults

| Config Section | Default Route | Purpose |
|----------------|---------------|---------|
| `resources.route` | `/api` | URL prefix for custom resource handlers |
| `static.route` | `/` | URL prefix for static file serving |

Apps without a `resources:` section serve tables at the root path (typical for services and static-only apps).

## Generated Table Endpoints

Every `@export`ed table produces:

```
GET    /{app-id}/{Table}        # List/search
POST   /{app-id}/{Table}        # Create
GET    /{app-id}/{Table}/{id}   # Get by ID
PUT    /{app-id}/{Table}/{id}   # Replace
PATCH  /{app-id}/{Table}/{id}   # Partial update
DELETE /{app-id}/{Table}/{id}   # Delete
```

With `@export(sse: true)`, the table supports `GET /{app-id}/{Table}?stream=sse` for real-time change streams.

### Custom Endpoint Paths

Use `@export(path: "custom-path")` to override the default endpoint path (lowercase type name):

```graphql
type Product @table @export(path: "api/v1/products") { ... }
```

This serves the table at `/{app-id}/api/v1/products` instead of `/{app-id}/product`.

An empty name (`@export(path: "")`) mounts the table at the app root.

## Protocol-Specific Endpoints

- **GraphQL** (`graphql: true`): All GraphQL-enabled tables queryable via `POST /{app-id}/graphql`
- **MCP** (`mcp: true` or `@export(mcp: true)`): JSON-RPC 2.0 at `POST /{app-id}/mcp`
- **gRPC** (`interfaces.grpc.enabled`): HTTP/2 `application/grpc` requests route to the gRPC tables service (Get, Put, Delete, Scan, Query, ListTables, Subscribe)

## Special Routes

| Route | Purpose |
|-------|---------|
| `/health` | Server health check (always available) |
| `/admin/` | Admin UI (yeti-admin service) |
| `/mqtt` | MQTT WebSocket proxy (if MQTT enabled) |
| `/{app-id}/graphql` | GraphQL endpoint (if `graphql: true`) |
| `/{app-id}/mcp` | MCP JSON-RPC 2.0 endpoint (if `mcp: true`) |
| `/yeti.tables.Tables/*` | gRPC tables service (if `interfaces.grpc.enabled`) |

## Static File Routing

Static files serve from `static.path`. With `spa: true`, unmatched paths return `index.html` (status 200), letting the client-side router handle navigation.

```yaml
static:
  path: web
  route: /
  spa: true
```

Without `spa`, unmatched paths return 404.

See also: [Resources](resources.md), [Schemas](schemas.md).
