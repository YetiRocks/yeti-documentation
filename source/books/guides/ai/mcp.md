# MCP for Agents

Every `@export`-ed table in your Yeti application is automatically
available to AI agents through the [Model Context
Protocol](https://modelcontextprotocol.io/) — no extra code, no
schema annotations beyond `@export`. Each table becomes six tools,
one resource, and three prompts that any MCP client (Claude Desktop,
Cursor, Claude Code, …) can discover and call.

This guide is how-to oriented. For the JSON-RPC wire spec and method
catalog, see the [MCP API reference](../../reference/api/operations.md).

## What you get for free

Given this schema:

```graphql
type Product @table @export {
    id: ID! @primaryKey
    name: String!
    price: Float!
}
```

your app exposes, at `POST /{app-id}/mcp`:

| Surface | Names | Purpose |
|---|---|---|
| Tools | `product_get`, `product_list`, `product_create`, `product_update`, `product_delete`, `product_search` | CRUD + FIQL search |
| Resource | `yeti://{app-id}/product` | Bulk read |
| Resource template | `yeti://{app-id}/product/{id}` | Record read |
| Prompts | `list_product`, `search_product`, `describe_product` | Pre-templated agent instructions |

Tool names are the lowercased table name plus a verb. Multi-word
table names follow the same lowercase form — `OrderLine` → `orderline_get`.

## Hide a table from agents

Set `mcp: false` in `@export` for tables the agent should not see —
audit logs, internal bookkeeping, secrets:

```graphql
type AuditLog @table @export(mcp: false) {
    id: ID! @primaryKey
    action: String!
    actor: String!
}
```

The table still serves REST/GraphQL/SSE; only the MCP surface is
suppressed. There is no `@mcp(...)` directive — `mcp: false` is the
only knob.

## Auth choices for agents

MCP runs through the same authentication pipeline as the rest of the
app. Pick whichever model fits the agent's role:

### Read-only public agent

For agents that browse a public catalog, open read tools to
unauthenticated callers:

```graphql
type Product @table @export @access(public: [read]) {
    id: ID! @primaryKey
    name: String!
    price: Float!
}
```

Unauthenticated MCP clients can now call `product_get`, `product_list`,
and `product_search`. `product_create`, `product_update`, and
`product_delete` still require auth.

### Authenticated agent

For agents acting on behalf of a service account or end user, send a
JWT in the `Authorization` header (see [JWT
Authentication](../auth/jwt.md)). The auth layer runs before MCP
dispatch, so RBAC and attribute-level access apply unchanged.

## Connect a client

The wire transport is streamable HTTP — every modern MCP client
supports it.

### Claude Desktop

Add an entry to `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "my-yeti-app": {
      "transport": {
        "type": "http",
        "url": "https://localhost/my-app/mcp",
        "headers": {
          "Authorization": "Bearer <your-jwt>"
        }
      }
    }
  }
}
```

Restart Claude Desktop. Your tables appear in the tools menu.

### Cursor

Add `.cursor/mcp.json` at the project root:

```json
{
  "mcpServers": {
    "my-yeti-app": {
      "transport": {
        "type": "http",
        "url": "https://localhost/my-app/mcp",
        "headers": {
          "Authorization": "Bearer <your-jwt>"
        }
      }
    }
  }
}
```

### Claude Code

One-liner:

```bash
claude mcp add my-yeti-app \
  --transport http https://localhost/my-app/mcp \
  --header "Authorization: Bearer $JWT"
```

## Verify it works

Smoke-test the endpoint with curl. First, `initialize` to grab a
session id:

```bash
curl -sk -i -X POST https://localhost/my-app/mcp \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-11-25",
      "capabilities": {},
      "clientInfo": {"name": "smoke", "version": "0"}
    }
  }'
```

The response includes an `mcp-session-id` header. Reuse it on
subsequent calls:

```bash
SID=<paste mcp-session-id value>

curl -sk -X POST https://localhost/my-app/mcp \
  -H "mcp-session-id: $SID" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | jq '.result.tools[].name'
```

You should see one tool per `@export`-ed table × 6 verbs.

## Common patterns

- **Selective exposure.** Mark customer-facing tables `@export` and
  leave internal ones plain `@table`. The MCP surface mirrors the
  REST surface — if it's not exported, agents can't see it.
- **Read-only catalog agent.** `@export @access(public: [read])` lets
  an agent browse without credentials but blocks mutations. Combine
  with [rate limiting](../caching/rate-limiting.md) for safety.
- **Per-user agent.** Use [JWT Authentication](../auth/jwt.md) and let
  RBAC restrict which records the agent can touch. The agent inherits
  the user's permissions exactly.
- **Self-describing entry point.** `GET /{app-id}/mcp` returns a JSON
  description of the available tables and tool counts — useful for
  agents that want to introspect before initializing a session.

## See also

- [MCP API reference](../../reference/api/operations.md) — JSON-RPC
  method catalog, session lifecycle, error codes
- [Schema Directives](../../reference/config/schema-directives.md) —
  full `@export` argument list including `mcp:`
- [REST API](../../reference/api/rest.md) — same CRUD surface, HTTP-native
- [Authentication overview](../auth/overview.md) — auth pipeline applied
  to MCP requests
