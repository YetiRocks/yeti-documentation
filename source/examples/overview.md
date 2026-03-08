# Example Applications

All demo applications are open source on GitHub. Browse the source, then install them directly from the Studio.

## Browse Source Code

Visit [github.com/yetiRocks](https://github.com/yetiRocks) to view all available applications:

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

See [Studio](../guides/studio.md) for more on managing applications.

## Create a New Application

Start from scratch or copy an existing app:

```bash
mkdir ~/yeti/applications/my-app
```

Add `config.yaml` and `schema.graphql`, then restart the server. See [Quickstart](../getting-started/quickstart.md) for a step-by-step walkthrough.
