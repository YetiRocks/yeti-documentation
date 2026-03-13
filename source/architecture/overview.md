# System Overview

Yeti is a schema-driven application platform built in Rust. It hosts multiple applications within one runtime, each with isolated databases, routes, and authentication.

## Architecture

```
HTTPS :9996 ──> DynamicRouter ──> /{app-id}/ prefix match
                                        │
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

1. **HTTPS Termination** - TLS on port 9996
2. **DynamicRouter** - Extracts `app-id` from path, looks up application
3. **AutoRouter** - Per-app router generated from schema
4. **Resource Handler** - CRUD for tables or custom logic for plugins
5. **Response** - JSON or SSE stream

## Multi-Tenancy

| Concern | Isolation |
|---------|-----------|
| Database | Each app declares its own `database:` name |
| Routes | Prefixed by `/{app-id}/` |
| Auth | Per-app extension configuration |
| Plugins | Separate dylib per application |

## Key Components

- **YetiRuntime** - Owns DynamicRouter, DatabaseManager, server lifecycle
- **ApplicationLoader** - Discovers, compiles, and loads applications
- **ApplicationCompiler** - Generates Cargo projects from config.yaml, builds dylibs
- **AutoRouter** - Schema-driven router mapping types to REST/GraphQL/SSE endpoints
- **BackendManager** - Maps table names to storage backends
- **Health Endpoint** - `/health` for liveness checks and app count

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
