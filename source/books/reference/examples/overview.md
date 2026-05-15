# Example Applications

All demos are open source on GitHub. Browse the source, then install from Studio.

## Browse Source Code

Source at [github.com/yetiRocks](https://github.com/yetiRocks):

| Repository | What You'll Learn |
|-----------|-------------------|
| `demo-basic` | CRUD operations, REST endpoints, custom resources |
| `demo-fiql` | FIQL filtering, sorting, pagination, field selection |
| `demo-realtime` | SSE, WebSocket, and MQTT streaming with a React UI |
| `demo-authentication` | Basic, JWT, and OAuth auth with RBAC visualization |
| `demo-vector` | Semantic search with auto-embedding and HNSW indexes |
| `demo-graphql` | Multi-table relationships with GraphQL playground |
| `demo-mcp` | Model Context Protocol integration for AI agents |
| `app-redirector` | URL redirects with pattern matching and scheduled cutover |

## Install from Studio

1. Open Studio at `https://localhost:9996/admin`
2. Go to the **Applications** tab
3. Click **New Application**
4. Select a demo from the list or paste a GitHub repository URL
5. The app installs, compiles, and starts automatically

See [Studio](../guides/studio.md) for details.

## Create a New Application

Start from scratch:

```bash
mkdir ~/yeti/applications/my-app
```

Add `Cargo.toml` and `schema.graphql`, then restart. See [Quickstart](../getting-started/quickstart.md).
