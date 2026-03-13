# Server Management

Yeti provides server management through the `/health` endpoint and the built-in extension APIs. There is no centralized admin API -- each extension exposes its own endpoints under its route prefix.

## Health Check

```bash
curl -sk https://localhost:9996/health
```

Returns server health status including loaded application count.

## Extension APIs

Studio and other admin tools interact with each extension's REST API directly. All extension endpoints require `super_user` authentication.

### Applications (yeti-applications)

```bash
# List all deployed applications
curl -sk https://localhost:9996/yeti-applications/Application \
  -H "Authorization: Basic $(echo -n 'YETI_ADMIN:password' | base64)"
```

Returns all deployed applications with metadata.

### Authentication (yeti-auth)

```bash
# List users
curl -sk https://localhost:9996/yeti-auth/users \
  -H "Authorization: Basic $(echo -n 'YETI_ADMIN:password' | base64)"

# List roles
curl -sk https://localhost:9996/yeti-auth/roles \
  -H "Authorization: Basic $(echo -n 'YETI_ADMIN:password' | base64)"
```

User and role management. See [Authentication](../guides/auth-overview.md) for the full API.

### Telemetry (yeti-telemetry)

```bash
# Query logs
curl -sk https://localhost:9996/yeti-telemetry/Log?limit=50 \
  -H "Authorization: Basic $(echo -n 'YETI_ADMIN:password' | base64)"

# Stream logs in real-time
curl -sk https://localhost:9996/yeti-telemetry/Log?stream=sse \
  -H "Authorization: Basic $(echo -n 'YETI_ADMIN:password' | base64)"

# Query metrics
curl -sk https://localhost:9996/yeti-telemetry/Metric?limit=50 \
  -H "Authorization: Basic $(echo -n 'YETI_ADMIN:password' | base64)"
```

Log, span, and metric storage with real-time SSE streaming. See [Telemetry](../guides/telemetry.md).

### Vectors (yeti-vectors)

```bash
# List available models
curl -sk https://localhost:9996/yeti-vectors/models \
  -H "Authorization: Basic $(echo -n 'YETI_ADMIN:password' | base64)"
```

Vector embedding model management. See [Vector Search](../guides/vector-search.md).

## Authentication

All extension APIs use the same authentication as the rest of the platform (Basic, JWT, or OAuth). The user must have the `super_user` role.

## See Also

- [REST API](rest.md) -- Application data API
- [Server Configuration](../reference/server-config.md) -- Config reference
- [Error Codes](errors.md) -- Error response details
