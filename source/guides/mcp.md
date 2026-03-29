# MCP Integration

The Model Context Protocol (MCP) allows AI agents to interact with your Yeti tables using a standardized JSON-RPC 2.0 protocol over HTTP. When enabled, Yeti auto-generates tools, resources, and prompts from your schema — no code required.

## What is MCP

MCP is a protocol for connecting AI models to external data sources and tools. It uses JSON-RPC 2.0 over HTTP with a simple session lifecycle:

1. **Initialize** — client and server exchange capabilities
2. **Discover** — client lists available tools, resources, and prompts
3. **Execute** — client calls tools to read and write data
4. **Terminate** — client ends the session

Yeti implements MCP protocol version `2025-03-26` with streamable HTTP transport.

## Enabling MCP

MCP is enabled by default at the server level. To expose tables via MCP, add `@export` to your schema (MCP is enabled by default when `@export` is present):

```graphql
type Product @table @export {
  id: ID! @primaryKey
  name: String!
  price: Float!
  category: String
}

type Order @table @export {
  id: ID! @primaryKey
  productId: String!
  quantity: Int!
  createdAt: Float! @createdAt
}

# Exclude a table from MCP
type InternalCache @table @export(mcp: false) {
  id: ID! @primaryKey
  data: String!
}
```

MCP can be toggled at the server level in `yeti-config.yaml`:

```yaml
interfaces:
  mcp:
    enabled: true
    audit: true    # Log MCP tool calls (enabled by default)
```

## Endpoint

MCP requests are sent to:

```
POST /{app}/mcp
```

For example, if your app is called `my-api`:

```
POST /my-api/mcp
```

A `GET` request to the same endpoint returns a JSON description of the MCP capabilities:

```
GET /my-api/mcp
```

Sessions are terminated with:

```
DELETE /my-api/mcp
```

## Auto-Generated Tools

For each MCP-enabled table, Yeti generates six tools:

| Tool | Description | Annotations |
|------|-------------|-------------|
| `{table}_get` | Get a record by ID | readOnly, idempotent |
| `{table}_list` | List records with pagination and sorting | readOnly, idempotent |
| `{table}_create` | Create a new record | mutating |
| `{table}_update` | Update an existing record by ID | mutating, idempotent |
| `{table}_delete` | Delete a record by ID | mutating, destructive, idempotent |
| `{table}_search` | Search records with a FIQL filter or text query | readOnly, idempotent |

Table names in tool names are lowercased. A `Product` table generates `product_get`, `product_list`, etc.

### Tool Input Schemas

Tool input schemas are generated from your GraphQL field definitions:

- **get/delete**: `{"id": "string"}` (required)
- **create**: All non-computed, non-auto-timestamp fields. Non-nullable fields are required.
- **update**: `{"id": "string"}` (required) plus all updatable fields as optional.
- **list**: `{"limit": integer, "offset": integer, "order_by": string}` (all optional)
- **search**: `{"filter": string, "limit": integer, "offset": integer}` (all optional)

The `search` tool accepts either a FIQL expression (`price=gt=5.00;category==electronics`) or a plain text query (which becomes a wildcard search on the `name` field).

## Resources

MCP resources provide read access to table data via URIs:

| Resource | URI |
|----------|-----|
| Table listing | `yeti://{app}/{table}` |
| Record by ID | `yeti://{app}/{table}/{id}` |

Resource templates use `{id}` as a parameterized URI component.

## Prompts

For each table, three prompts are generated:

| Prompt | Description |
|--------|-------------|
| `list_{table}` | List records (accepts optional `limit` argument) |
| `search_{table}` | Search records (accepts required `query` argument) |
| `describe_{table}` | Describe the table schema and fields |

## Authentication

MCP uses the same authentication pipeline as REST. If your app requires authentication, MCP tool calls must include valid credentials:

```bash
# With Basic auth
curl -X POST https://localhost/my-api/mcp \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '...'

# With Bearer token
curl -X POST https://localhost/my-api/mcp \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '...'
```

Auth context is propagated to each tool call — table-level access control is enforced on every operation.

## Protocol Walkthrough

Here is a complete MCP session using curl.

### Step 1: Initialize

```bash
curl -s -X POST https://localhost/my-api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {
        "name": "my-agent",
        "version": "1.0"
      }
    }
  }'
```

Response (note the `mcp-session-id` header):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "tools": { "listChanged": false },
      "resources": { "listChanged": false },
      "prompts": { "listChanged": false }
    },
    "serverInfo": {
      "name": "yeti/my-api",
      "version": "1.0.0"
    }
  }
}
```

### Step 2: Send Initialized Notification

```bash
curl -s -X POST https://localhost/my-api/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id-from-step-1>" \
  -d '{
    "jsonrpc": "2.0",
    "method": "notifications/initialized"
  }'
```

Returns HTTP 202 (no body for notifications).

### Step 3: List Available Tools

```bash
curl -s -X POST https://localhost/my-api/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "product_get",
        "description": "Get a Product record by ID",
        "inputSchema": {
          "type": "object",
          "properties": {
            "id": { "type": "string", "description": "Record ID" }
          },
          "required": ["id"]
        },
        "annotations": {
          "readOnlyHint": true,
          "idempotentHint": true
        }
      },
      {
        "name": "product_list",
        "description": "List Product records",
        "inputSchema": { "..." : "..." }
      },
      {
        "name": "product_create",
        "description": "Create a new Product record",
        "inputSchema": { "..." : "..." }
      }
    ],
    "nextCursor": null
  }
}
```

### Step 4: Call a Tool

Create a product:

```bash
curl -s -X POST https://localhost/my-api/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "product_create",
      "arguments": {
        "name": "Widget",
        "price": 9.99,
        "category": "gadgets"
      }
    }
  }'
```

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"id\": \"01JEXAMPLE\",\n  \"name\": \"Widget\",\n  \"price\": 9.99,\n  \"category\": \"gadgets\"\n}"
      }
    ]
  }
}
```

Search for products:

```bash
curl -s -X POST https://localhost/my-api/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "product_search",
      "arguments": {
        "filter": "price=gt=5.00",
        "limit": 10
      }
    }
  }'
```

### Step 5: Read a Resource

```bash
curl -s -X POST https://localhost/my-api/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "resources/read",
    "params": {
      "uri": "yeti://my-api/product/01JEXAMPLE"
    }
  }'
```

### Step 6: Terminate Session

```bash
curl -s -X DELETE https://localhost/my-api/mcp \
  -H "Mcp-Session-Id: <session-id>"
```

## Supported Methods

| Method | Description |
|--------|-------------|
| `initialize` | Start a session, exchange capabilities |
| `notifications/initialized` | Client confirms initialization (notification, no response) |
| `ping` | Health check |
| `tools/list` | List available tools (with optional cursor pagination) |
| `tools/call` | Execute a tool |
| `resources/list` | List available resources |
| `resources/templates/list` | List resource URI templates |
| `resources/read` | Read a resource by URI |
| `prompts/list` | List available prompts |
| `prompts/get` | Get a prompt with arguments expanded |

## Integration with AI Agents

### Claude Desktop / Claude Code

Add your Yeti MCP endpoint to the Claude configuration:

```json
{
  "mcpServers": {
    "my-api": {
      "url": "https://localhost/my-api/mcp",
      "headers": {
        "Authorization": "Bearer <your-token>"
      }
    }
  }
}
```

### Other MCP-Aware Agents

Any agent that supports MCP protocol version `2025-03-26` with streamable HTTP transport can connect to Yeti's MCP endpoint. The auto-generated tools provide full CRUD access to your tables through a standardized interface.

## Platform Developer Tools (yeti-mcp)

In addition to per-app table tools, every yeti instance includes `yeti-mcp` -- a built-in MCP endpoint that provides platform-level knowledge and tooling for developer agents.

**Endpoint**: `POST /yeti-mcp/agent`

This is separate from your app's `/my-api/mcp` endpoint. While your app's MCP tools handle table CRUD, yeti-mcp helps agents understand the platform itself:

| Tool | Description |
|------|-------------|
| `docs_search` | Search platform documentation by natural language query |
| `docs_get` | Retrieve a specific documentation page |
| `docs_list_topics` | List all available documentation topics |
| `app_list` | List installed applications |
| `app_inspect` | Get config, schema, and resource details for an app |
| `app_endpoints` | List all endpoints (REST, MCP, SSE, MQTT) for an app |
| `sdk_reference` | Look up SDK documentation (prelude, macros, errors, types) |
| `deploy_checklist` | Validate an app's config before deployment |
| `troubleshoot` | Get fixes for common symptoms |

yeti-mcp also serves 12 static resources (`yeti://guides/*`, `yeti://sdk/*`, `yeti://constraints`, `yeti://anti-patterns`) and 4 prompt templates (`create_application`, `add_resource`, `add_table`, `debug_plugin`).

### Connecting AI Agents to yeti-mcp

```json
{
  "mcpServers": {
    "yeti-platform": {
      "url": "https://localhost/yeti-mcp/agent",
      "headers": {
        "Authorization": "Bearer <your-token>"
      }
    }
  }
}
```

This gives agents like Claude Code, Cursor, and Windsurf the ability to search documentation, inspect running apps, and generate scaffolding -- all through the standard MCP protocol.

## Audit Logging

When `interfaces.mcp.audit` is enabled (the default), Yeti logs every MCP tool call with:

- Timestamp, app ID, session ID
- Client name and version (from `initialize`)
- Method and tool name
- Operation (get, list, create, update, delete, search)
- Tool arguments
- Status (ok/error) and duration
- Client IP and request ID

Audit entries are emitted through the standard telemetry pipeline. Protocol handshake methods (`initialize`, `ping`, notifications) are excluded from audit logging.
