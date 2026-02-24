# URL Redirect Management

The `redirect-manager` app provides URL redirects with static and regex matching, versioning, host-specific rules, and time-window activation.

## Modes

- **redirect** - Returns HTTP 301/302/307/308 responses
- **check** - Returns JSON metadata (for CDN/edge worker integration)

```yaml
environment:
  MODE: "redirect"
```

## Schema

### Rule

```graphql
type Rule @table(database: "redirect-manager") @export(name: "rule") {
  id: ID!
  staticPath: String
  regexPattern: String
  targetUrl: String!
  statusCode: Int!
  queryStringOp: String   # preserve, ignore, filter, append
  host: String
  version: String
  utcStartTime: String
  utcEndTime: String
  active: Boolean!
  priority: Int
}
```

### Hosts

```graphql
type Hosts @table(database: "redirect-manager") @export(name: "hosts") {
  id: ID!                 # Hostname
  activeVersion: String
  enabled: Boolean!
  fallbackUrl: String
}
```

## Composite Key

Rules use keys: `{version}||{host}||{path}`

Lookup: version + host + path -> exact match -> global fallback (empty host) -> 404.

## Creating Rules

```bash
curl -sk -X POST https://localhost:9996/redirect-manager/rule \
  -H "Content-Type: application/json" \
  -d '{"id":"0||example.com||/old-page","staticPath":"/old-page","targetUrl":"https://example.com/new-page","statusCode":301,"host":"example.com","version":"0","active":true}'
```

## Version Control

Create rules under a version, then activate:

```bash
# Activate version v2 for a host
curl -sk -X PUT https://localhost:9996/redirect-manager/hosts/example.com \
  -H "Content-Type: application/json" \
  -d '{"id":"example.com","activeVersion":"v2","enabled":true}'
```

## Time Windows

```json
{"utcStartTime": "2025-06-01T00:00:00Z", "utcEndTime": "2025-12-31T23:59:59Z"}
```

Rules outside their window are skipped.

## Check Mode

```bash
curl -sk "https://localhost:9996/redirect-manager/old-page?h=example.com&v=0"
```

```json
{"path":"/old-page","host":"example.com","redirectURL":"/new-page","statusCode":301,"version":"0"}
```

## See Also

- [Custom Resources](custom-resources.md) - Default resource pattern
- [Application Configuration](../reference/app-config.md) - Config reference
