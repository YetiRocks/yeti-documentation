# Example Applications

These applications are pre-installed by `yeti init` in `~/yeti/applications/`. Each is self-contained with its own config, schema, and optional resources.

## Extensions

| App ID | Description |
|--------|-------------|
| `yeti-auth` | Authentication and authorization (Basic, JWT, OAuth, RBAC) |
| `yeti-telemetry` | Log/Span/Metric collection with dashboard and OTLP export |
| `yeti-vectors` | Automatic text/image embedding with persistent vector cache |

## Applications

| App ID | Description |
|--------|-------------|
| `application-template` | Minimal starter with a single table and custom resource |
| `graphql-explorer` | Multi-table relationships with GraphQL explorer UI |
| `example-queries` | FIQL filtering, sorting, pagination, field selection, joins |
| `vector-search-demo` | Semantic similarity search with auto-embedding |
| `realtime-demo` | SSE streaming with a React UI for live updates |
| `redirect-manager` | URL redirects with pattern matching and cutover |
| `web-auth-demo` | Interactive demo of all auth methods with RBAC visualization |
| `yeti-applications` | Web UI for viewing and managing all Yeti applications |
| `benchmarks` | Performance testing with multiple table types |
| `documentation` | This documentation site (mdBook) |
| `www` | Project homepage |

## Browse an App

Each app is a directory you can read directly:

```bash
ls ~/yeti/applications/graphql-explorer/
# config.yaml  schema.graphql  data/  web/
```

## Creating a New Application

Copy the template:

```bash
cp -r ~/yeti/applications/application-template ~/yeti/applications/my-app
```

Edit `config.yaml` and `schema.graphql`, then restart the server.

## Common Structure

```
~/yeti/applications/{app-id}/
  config.yaml          # Required
  schema.graphql       # Table definitions (if any)
  resources/           # Custom Rust resources (if any)
    *.rs
  data/                # Seed data (if any)
    *.json
  web/                 # Static files (if any)
    index.html
```
