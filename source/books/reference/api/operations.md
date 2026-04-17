# MCP API

[Model Context Protocol](https://modelcontextprotocol.io/) (MCP) endpoint for AI agents and tool-calling LLMs. Standardized JSON-RPC 2.0 interface over application tables.

## Enabling MCP

Auto-enabled for any table with `@export(mcp: true)`. When `@export` is present without arguments, `mcp` defaults to `true`.

```graphql
type Product @table @export(mcp: true) {
    id: ID!
    name: String!
    price: Float!
}
```

Endpoint: `POST /{app-id}/mcp`.

## Transport

Streamable HTTP, JSON-RPC 2.0 over POST:

```bash
curl -sk -X POST https://localhost:9996/my-app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"my-agent","version":"1.0"}}}'
```

Protocol version: `2025-03-26`.

## Session Lifecycle

1. Send `initialize` to start a session. The response includes an `mcp-session-id` header.
2. Send `notifications/initialized` (no `id` field -- it is a notification, returns 202).
3. Use `tools/list`, `resources/list`, or `prompts/list` to discover capabilities.
4. Call `tools/call` to perform operations.
5. Send `DELETE /{app-id}/mcp` with the `mcp-session-id` header to terminate.

## Methods

### `initialize`

Starts a session and returns server capabilities.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {},
    "clientInfo": { "name": "my-agent", "version": "1.0" }
  }
}
```

Response includes `tools`, `resources`, and `prompts` capability declarations.

### `tools/list`

Returns tool definitions. Each MCP-enabled table generates six tools:

| Tool | Description |
|------|-------------|
| `{table}_get` | Get a record by ID |
| `{table}_list` | List records with optional limit, offset, order_by |
| `{table}_create` | Create a new record |
| `{table}_update` | Update an existing record (requires id) |
| `{table}_delete` | Delete a record by ID |
| `{table}_search` | Search with a FIQL filter or text query |

Tool names use lowercase table names: `product_get`, `product_list`, etc.

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

### `tools/call`

Invoke a tool:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "product_create",
    "arguments": {
      "id": "p1",
      "name": "Widget",
      "price": 9.99
    }
  }
}
```

Tool results follow the MCP content format:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [{ "type": "text", "text": "..." }],
    "isError": false
  }
}
```

### `resources/list`

Lists data resources (tables) as MCP resources with `yeti://` URIs.

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/list"
}
```

Each resource has the URI pattern `yeti://{app-id}/{table}`.

### `resources/templates/list`

Lists URI templates for record-level access: `yeti://{app-id}/{table}/{id}`.

### `resources/read`

Reads a resource by URI. Returns table listing or single record depending on the URI.

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "resources/read",
  "params": { "uri": "yeti://my-app/product/p1" }
}
```

### `prompts/list`

Lists prompt templates. Each table generates three prompts:

| Prompt | Arguments | Description |
|--------|-----------|-------------|
| `list_{table}` | `limit` (optional) | List records |
| `search_{table}` | `query` (required) | Search records |
| `describe_{table}` | none | Describe table schema |

### `prompts/get`

Retrieves a prompt with arguments expanded into messages.

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "prompts/get",
  "params": { "name": "search_product", "arguments": { "query": "widget" } }
}
```

### `ping`

Health check. Returns `{}`.

## Tool Annotations

Each tool includes MCP annotations for agent safety:

| Annotation | Description |
|------------|-------------|
| `readOnlyHint` | `true` for get, list, search |
| `destructiveHint` | `true` for delete |
| `idempotentHint` | `true` for get, list, search, update, delete; `false` for create |

## Authentication

MCP endpoints use the same authentication as the rest of the application. Include credentials in request headers.

## GET Endpoint

`GET /{app-id}/mcp` returns a JSON description of the endpoint including available tables, tool counts, and instructions.

## See Also

- [REST API](rest.md) -- Standard REST interface
- [GraphQL API](graphql.md) -- GraphQL interface
- [Schema Directives](../reference/schema-directives.md) -- `@export` directive reference
