# Security Architecture

Yeti provides layered authentication through the `yeti-auth` extension.

## Auth Pipeline

```
Request ──> BasicAuthProvider (Authorization: Basic, Argon2id verification)
        ──> JwtAuthProvider   (Authorization: Bearer, token validation)
        ──> OAuthAuthProvider  (Session cookie, in-memory cache -> DB fallback)
        ──> 401 Unauthorized
```

Providers are tried in order. First match determines identity and role.

## Password Hashing

**Argon2id** with OWASP-recommended minimum parameters (19 MiB memory, 2 iterations, 1 parallelism). Credential cache with 5-minute TTL avoids repeated hashing.

## JWT Authentication

HMAC-SHA256 signing with two token types:

| Token | TTL | Purpose |
|-------|-----|---------|
| Access | 15 min | API auth, embeds permissions |
| Refresh | 7 days | Exchange for new token pair |

```bash
# Login
curl -sk -X POST https://localhost:9996/yeti-auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Refresh
curl -sk -X POST https://localhost:9996/yeti-auth/jwt_refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"..."}'
```

## OAuth Integration

Per-app OAuth rules in config.yaml:

```yaml
extensions:
  - yeti-auth:
      oauth:
        rules:
          - strategy: provider
            pattern: "google"
            role: admin
          - strategy: email
            pattern: "*@mycompany.com"
            role: standard
```

- **CSRF tokens** stored in DashMap (10-minute TTL, periodic cleanup)
- **SSRF validation** at startup (rejects private IPs, requires HTTPS in production)
- **Session persistence** in memory + database (survives restarts)
- Cookies set with `Secure`, `HttpOnly`, and `SameSite` attributes

## Role-Based Access Control

```json
{
  "id": "admin",
  "permissions": {
    "super_user": true,
    "tables": { "*": { "read": true, "insert": true, "update": true, "delete": true } }
  }
}
```

The `super_user` role is protected from deletion and privilege removal.

### Role Resolution

- **Basic/JWT** - User record's `roleId` resolved against Role table
- **OAuth** - Config rules map provider/email patterns to roles

### Attribute-Level Filtering

```json
{
  "tables": {
    "employees": {
      "read": true,
      "attribute_permissions": { "salary": { "read": false } }
    }
  }
}
```

## Rate Limiting

```yaml
rateLimiting:
  maxRequestsPerSecond: 1000
  maxConcurrentConnections: 100
```

Backpressure via `maxInFlightRequests` returns 503 when exceeded.
