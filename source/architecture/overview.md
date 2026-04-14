# System Overview

Schema-driven application platform in Rust. Hosts multiple applications within one runtime, each with isolated databases, routes, and authentication.

## Architecture

```
HTTPS/gRPC/MCP :9996 ──> DynamicRouter ──> /{app-id}/ prefix match
  MQTTS :8883 ───────┘                           │
                                             AutoRouter
                                             (per-app)
                                                  │
                                        ┌─────────┴─────────┐
                                        │                    │
                                  TableResource        Custom Resource
                                  (schema-driven)      (Rust plugin)
                                        │
                                   BackendManager
                                        │
                                 RocksDB Shards
                                 (embedded, per-database)
```

## Request Lifecycle

1. **Protocol Termination** - TLS on `interfaces.port` (default 9996) for HTTPS, gRPC, WebSocket, SSE, and MCP. MQTTS on separate port (default 8883)
2. **DynamicRouter** - Extracts `app-id` from path, looks up application. Intercepts MQTT WebSocket upgrades at `/mqtt`
3. **AutoRouter** - Per-app router generated from schema
4. **Resource Handler** - CRUD for tables or custom logic for plugins
5. **Response** - JSON, SSE stream, gRPC response, or MCP tool result

## Multi-Tenancy

| Concern | Isolation |
|---------|-----------|
| Database | Each app declares its own `database:` name |
| Routes | Prefixed by `/{app-id}/` |
| Auth | Per-app service configuration |
| Plugins | Separate dylib per application |

## Key Components

- **YetiRuntime** - Owns DynamicRouter, DatabaseManager, server lifecycle
- **ApplicationLoader** - Discovers, compiles, and loads applications
- **ApplicationCompiler** - Generates Cargo projects from config.yaml, builds dylibs
- **AutoRouter** - Schema-driven router mapping types to REST/GraphQL/SSE/gRPC/MCP endpoints
- **BackendManager** - Maps table names to storage backends
- **Health Endpoint** - `/health` for liveness checks and app count

## Yeti Cloud

Managed hosting with automated deployment, replication, cgroup isolation, and built-in backups. See [Yeti Cloud](../deployment/cloud.md).

## Directory Layout

```
~/yeti/
├── yeti-config.yaml
├── applications/
│   ├── yeti-auth/
│   ├── documentation/
│   └── ...
├── data/
│   ├── yeti-auth/          # RocksDB databases (embedded mode)
│   └── ...
├── certs/
│   └── localhost/
└── cache/
    └── builds/
        └── {app-id}/
```
