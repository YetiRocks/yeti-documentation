# Yeti

Yeti is a schema-driven application platform built in Rust. Define your data model in GraphQL, and Yeti generates REST APIs, real-time subscriptions, GraphQL endpoints, and authentication - all from a single configuration file.

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
curl -sk -X POST https://localhost:9996/my-app/Product \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget", "price": 29.99, "category": "Tools", "inStock": true}'

# Query with FIQL
curl -sk "https://localhost:9996/my-app/Product?category==Tools&price=lt=50&sort=-price&limit=10"

# Real-time stream
curl -sk "https://localhost:9996/my-app/Product?stream=sse"
```

## Why Yeti

**Schema-driven** - Define tables in GraphQL. REST, GraphQL, SSE, and WebSocket endpoints are generated automatically. No boilerplate.

**Custom resources in Rust** - Extend any table with business logic using Rust. Resources compile to dynamic libraries and hot-reload without server restart.

**Built-in auth** - Basic, JWT, and OAuth authentication with role-based access control down to individual fields. Add auth to any app with one line of config.

**Real-time by default** - Every table supports Server-Sent Events and WebSocket subscriptions. Clients receive updates as they happen.

**Fast** - Single-process architecture, RocksDB storage with embedded and cluster modes, and Rust performance.

## Quick links

- [Installation](getting-started/installation.md) - Get Yeti running locally
- [Quickstart](getting-started/quickstart.md) - Build a REST API in 5 minutes
- [Core Concepts](concepts/applications.md) - Understand applications, schemas, and resources
- [Custom Resources](guides/custom-resources.md) - Add business logic in Rust
- [API Reference](api/rest.md) - Complete endpoint documentation
- [Example Applications](examples/overview.md) - 11 working apps with source code

## Resources

- [GitHub](https://github.com/yetiRocks) - Source code and issues
- [Website](https://YetiRocks.com) - Project homepage
- [Configuration Reference](reference/server-config.md) - All server and app config options
- [Architecture](architecture/overview.md) - How Yeti works under the hood
