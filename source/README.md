# Yeti

Yeti is a schema-driven application platform built in Rust. Define your data model in GraphQL, and Yeti generates REST, GraphQL, WebSocket, SSE, MQTT, gRPC, and MCP endpoints with authentication - all from a single `config.yaml`.

## Define a schema. Get an API.

```graphql
type Product @table @export(rest: true, graphql: true, sse: true) {
    id: ID! @primaryKey
    name: String!
    price: Float @indexed
    category: String @indexed
    inStock: Boolean
    createdAt: Date @createdTime
}
```

```bash
# Create
curl -sk -X POST https://localhost/my-app/Product \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget", "price": 29.99, "category": "Tools", "inStock": true}'

# Query with FIQL
curl -sk "https://localhost/my-app/Product?category==Tools&price=lt=50&sort=-price&limit=10"

# Real-time stream
curl -sk "https://localhost/my-app/Product?stream=sse"
```

## Why Yeti

**Schema-driven** - Define tables in GraphQL. REST, GraphQL, SSE, WebSocket, gRPC, MQTT, and MCP endpoints are generated automatically. No boilerplate.

**Custom resources in Rust** - Extend any table with business logic using Rust. Resources compile to dynamic libraries and hot-reload without server restart.

**Built-in auth** - Basic, JWT, and OAuth authentication with role-based access control down to individual fields. Add auth to any app with one line of config.

**Real-time by default** - Every table supports Server-Sent Events, WebSocket subscriptions, and MQTT. Clients receive updates as they happen.

**Multi-protocol** - REST, GraphQL, WebSocket, SSE, MQTT, gRPC, and MCP (Model Context Protocol) -- all from the same schema. Toggle protocols per app or server-wide.

**Fast** - Single-process architecture, RocksDB embedded storage, and Rust performance. Yeti Cloud provides multi-node replication and clustering.

## Quick links

- [Installation](getting-started/installation.md) - Install Yeti in minutes
- [Quickstart](getting-started/quickstart.md) - Build a REST API in 5 minutes
- [Core Concepts](concepts/applications.md) - Understand applications, schemas, and resources
- [Custom Resources](guides/custom-resources.md) - Add business logic in Rust
- [API Reference](api/rest.md) - Complete endpoint documentation
- [Example Applications](examples/overview.md) - 11 working apps with source code

## Resources

- [GitHub](https://github.com/yetiRocks) - Example applications and demos
- [Website](https://YetiRocks.com) - Project homepage
- [Configuration Reference](reference/server-config.md) - All server and app config options
- [Architecture](architecture/overview.md) - How Yeti works under the hood
