# Operations API

Administrative API on a separate port (default 9995), plain HTTP.

| Property | Value |
|----------|-------|
| Port | 9995 (configurable) |
| Protocol | HTTP (no TLS) |
| Method | POST with JSON body |
| Health | `GET /health` |

All operations use `{"operation": "operation_name"}`.

## System Operations

### health_check

```bash
curl -X POST http://localhost:9995/ \
  -H "Content-Type: application/json" \
  -d '{"operation": "health_check"}'
```

Quick check also available via `GET /health`.

### system_information

```bash
curl -X POST http://localhost:9995/ \
  -H "Content-Type: application/json" \
  -d '{"operation": "system_information"}'
```

Returns hostname, OS, CPU, memory, uptime, and loaded application count.

### get_configuration

```bash
curl -X POST http://localhost:9995/ \
  -H "Content-Type: application/json" \
  -d '{"operation": "get_configuration"}'
```

Returns current server configuration (secrets are sanitized).

## Application Operations

### list_applications

```bash
curl -X POST http://localhost:9995/ \
  -H "Content-Type: application/json" \
  -d '{"operation": "list_apps"}'
```

Returns all deployed applications with ID, name, route prefix, table count, and interface flags.

## Describe Operations

### describe_all

Lists all databases and their tables.

```bash
curl -X POST http://localhost:9995/ \
  -H "Content-Type: application/json" \
  -d '{"operation": "describe_all"}'
```

### describe_table

```bash
curl -X POST http://localhost:9995/ \
  -H "Content-Type: application/json" \
  -d '{"operation": "describe_table", "database": "data", "table": "User"}'
```

## Deployment Operations

### package_component

Package an application for deployment to another server.

```bash
curl -X POST http://localhost:9995/ \
  -H "Content-Type: application/json" \
  -d '{"operation": "package_component", "project": "my-app"}'
```

### deploy_component

Deploy a packaged application. Validates that the package platform matches the target server.

```bash
curl -X POST http://localhost:9995/ \
  -H "Content-Type: application/json" \
  -d '{"operation": "deploy_component", "project": "my-app", "payload": "H4sIAAAAAAAA..."}'
```

## Security

Do not expose port 9995 to the public internet. Restrict access using firewall rules.

```yaml
operationsApi:
  port: 9995
  enabled: true
  cors: false
```

## See Also

- [REST API](rest.md) - Application data API
- [Server Configuration](../reference/server-config.md) - Config reference
- [Error Codes](errors.md) - Error response details
