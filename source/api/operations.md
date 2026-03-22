# MCP API

Yeti exposes a [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) endpoint for any application with `mcp: true` in its `config.yaml`. MCP enables AI agents and tool-calling LLMs to interact with application tables using a standardized JSON-RPC 2.0 interface.

## Enabling MCP

```yaml
# config.yaml (application)
mcp: true
```

The MCP endpoint is available at `/{app}/mcp`.

## Protocol

All requests use **JSON-RPC 2.0** over HTTP POST:

```bash
curl -sk -X POST https://localhost:9996/my-app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Methods

### `tools/list`

Returns the available CRUD tools for all MCP-enabled tables in the application.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

Each tool describes its name, description, and input schema (JSON Schema format).

### `tools/call`

Invokes a tool to perform a CRUD operation on a table.

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "create_Product",
    "arguments": {
      "id": "p1",
      "name": "Widget",
      "price": 9.99
    }
  }
}
```

Tool names follow the pattern `{operation}_{TableName}` where operation is one of: `get`, `list`, `create`, `update`, `delete`.

### `resources/list`

Lists the data resources (tables) available in the application.

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/list"
}
```

### `prompts/list`

Lists any registered prompts for the application.

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "prompts/list"
}
```

## Authentication

MCP endpoints use the same authentication as the rest of the application (Basic, JWT, or OAuth). Include credentials in the request headers as you would for any other API call.

## See Also

- [REST API](rest.md) -- Standard REST interface
- [GraphQL API](graphql.md) -- GraphQL interface
- [Application Configuration](../reference/app-config.md) -- Config reference
