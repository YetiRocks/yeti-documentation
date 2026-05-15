# MCP API

[Model Context Protocol](https://modelcontextprotocol.io/) endpoint
for AI agents and tool-calling LLMs. JSON-RPC 2.0 over streamable
HTTP, backed by the [`rmcp`](https://crates.io/crates/rmcp) 1.7
official Rust SDK (YTC-325 row 17, May 2026 — replaced 4,000 LOC of
hand-rolled wire layer).

```bash
curl -sk -X POST https://localhost/my-app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-11-25",
      "capabilities": {},
      "clientInfo": {"name": "my-agent", "version": "1.0"}
    }
  }'
```

## Enabling MCP

Auto-enabled on any `@export`-ed table. Disable per table with
`@export(mcp: false)`.

```graphql
type Product @table @export {                    # MCP on
    id: ID! @primaryKey
    name: String!
    price: Float!
}

type AuditLog @table @export(mcp: false) {       # MCP off
    id: ID! @primaryKey
    action: String!
}
```

Endpoint: `POST /{app-id}/mcp`.

Protocol version: **2025-11-25** (rmcp 1.7 default). Older clients
that send `"2025-03-26"` are accepted via negotiation; the server
replies with its preferred version and the client downgrades.

## Session lifecycle

1. **`initialize`** — start a session. Response includes an
   `mcp-session-id` header and the negotiated `protocolVersion`.
2. **`notifications/initialized`** — confirm (notification, no `id`,
   returns 202).
3. **`tools/list`**, **`resources/list`**, **`prompts/list`** —
   discovery.
4. **`tools/call`** — invoke an operation.
5. **`DELETE /{app-id}/mcp`** with the `mcp-session-id` header —
   terminate.

Subsequent requests in the session reuse the `mcp-session-id` header.
The default `LocalSessionManager` stores session state in-memory;
swap for a custom `SessionStore` impl to persist across restarts (see
the rmcp docs).

## Tools

Each MCP-enabled table generates six tools:

| Tool | Effect |
|---|---|
| `{table}_get` | Get a record by id |
| `{table}_list` | List records (`limit`, `offset`, `order_by` optional) |
| `{table}_create` | Create a new record |
| `{table}_update` | Update an existing record (requires `id`) |
| `{table}_delete` | Delete by id |
| `{table}_search` | FIQL filter or full-text query |

Tool names are lowercased table names. For a `Product` table:
`product_get`, `product_list`, `product_create`, ….

```json
{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
```

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "product_create",
    "arguments": {"id": "p1", "name": "Widget", "price": 9.99}
  }
}
```

Responses follow the MCP content shape:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [{"type": "text", "text": "..."}],
    "isError": false
  }
}
```

### Annotations

Tools carry safety hints for agent runtimes:

| Annotation | True for |
|---|---|
| `readOnlyHint` | `get`, `list`, `search` |
| `destructiveHint` | `delete` |
| `idempotentHint` | `get`, `list`, `search`, `update`, `delete` (not `create`) |

### Runtime enable/disable

rmcp 1.5+ supports runtime tool toggling via `tools/list_changed`
notifications. Plugins or admin endpoints can disable a tool without
restarting — the next `tools/list` reflects the change and clients
receive a `notifications/tools/list_changed` push.

## Resources

`resources/list` returns one resource per `@export`-ed table.

```json
{"jsonrpc": "2.0", "id": 4, "method": "resources/list"}
```

URI scheme: `yeti://{app-id}/{table}`. Templates for record-level
access (`resources/templates/list`) expose
`yeti://{app-id}/{table}/{id}`.

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "resources/read",
  "params": {"uri": "yeti://my-app/product/p1"}
}
```

## Prompts

Three per table:

| Prompt | Args | Returns |
|---|---|---|
| `list_{table}` | `limit?` | Pre-templated list-and-summarize prompt |
| `search_{table}` | `query` | Search prompt with FIQL hints |
| `describe_{table}` | none | Schema-aware description prompt |

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "prompts/get",
  "params": {"name": "search_product", "arguments": {"query": "widget"}}
}
```

## Authentication

Same pipeline as the rest of the application — Basic / JWT / OAuth /
mTLS. Send credentials in standard HTTP headers; the auth layer runs
before MCP dispatch.

`@access(public: [read])` lets unauthenticated MCP clients call
`get`, `list`, and `search` tools. `create`, `update`, and `delete`
always require auth.

## Origin header validation

rmcp 1.5 added DNS-rebinding mitigation for streamable HTTP. The
server rejects requests whose `Origin` header doesn't match the
configured allow-list. Configured server-wide in `yeti-config.yaml`
`[http].cors_access_list`.

## GET endpoint

`GET /{app-id}/mcp` returns a JSON description of the endpoint:
available tables, tool counts, instructions for the agent. Useful as
a self-describing entry point for agents that haven't initialized yet.

## ping

```json
{"jsonrpc": "2.0", "id": 7, "method": "ping"}
```

Returns `{}`. Use for health checks and keepalives.

## See also

- [REST API](rest.md) — same CRUD surface, HTTP-native
- [GraphQL API](graphql.md) — schema-introspectable alternative
- [Schema Directives — `@export`](../config/schema-directives.md) — `mcp: true` toggle
- [Authentication](../../guides/auth/overview.md) — applies to MCP equally
