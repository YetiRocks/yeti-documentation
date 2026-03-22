# Routing

Yeti routes requests through a two-level router: a top-level DynamicRouter dispatches by app prefix, then each application's AutoRouter resolves to table endpoints, custom resources, or static files.

## URL Structure

```
https://localhost/{app-id}/{resource-or-table}/{id}
```

Every application's routes live under its `app_id` prefix. The `route_prefix` config option can override this:

```yaml
app_id: "my-admin"
route_prefix: /admin
```

## Resolution Order

When multiple handlers could match a request, they resolve in this order:

1. **Custom resources** (exact name match)
2. **Table endpoints** (auto-generated from `@export`)
3. **Default resource** (catch-all, one per app)
4. **Static files** (from `web/` directory)
5. **404 Not Found**

A custom resource with the same name as a table takes precedence. Unoverridden methods fall through to the default table handler.

## Generated Endpoints

Every `@export`ed table produces:

```
GET    /{app-id}/{Table}        # List/search
POST   /{app-id}/{Table}        # Create
GET    /{app-id}/{Table}/{id}   # Get by ID
PUT    /{app-id}/{Table}/{id}   # Replace
PATCH  /{app-id}/{Table}/{id}   # Partial update
DELETE /{app-id}/{Table}/{id}   # Delete
```

With `sse: true`, the table supports `GET /{app-id}/{Table}?stream=sse` for real-time change streams.

## Protocol-Specific Endpoints

With `graphql: true`, the table is queryable via `POST /{app-id}/graphql`.

With `mcp: true` in the app's config.yaml, a JSON-RPC 2.0 endpoint is available at `POST /{app-id}/mcp` for Model Context Protocol clients.

With `interfaces.grpc.enabled` in yeti-config.yaml, all `@export`ed tables are accessible via gRPC on the same port. HTTP/2 requests with `content-type: application/grpc` are routed to the gRPC tables service (Get, Put, Delete, Scan, Query, ListTables, Subscribe).

## Special Routes

| Route | Purpose |
|-------|---------|
| `/health` | Server health check (always available) |
| `/studio/` | Studio admin UI |
| `/mqtt` | MQTT WebSocket proxy (if MQTT enabled) |
| `/{app-id}/graphql` | GraphQL endpoint (if `graphql: true`) |
| `/{app-id}/mcp` | MCP JSON-RPC 2.0 endpoint (if `mcp: true`) |
| `/yeti.tables.Tables/*` | gRPC tables service (if `interfaces.grpc.enabled`) |

See also: [Resources](resources.md), [Custom Resources](../guides/custom-resources.md), [Static File Serving](../guides/static-files.md).
