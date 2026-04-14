# JWT Authentication

JWT provides stateless, token-based access. Authenticate once, receive a token pair (access + refresh), then use the access token for subsequent requests.

## Login

Login targets a specific app. The returned token includes the user's permissions for that app:

```bash
curl -sk -X POST https://localhost:9996/yeti-auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin","app_id":"my-app"}'
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

## Per-App Token Accumulation

Tokens use a merged per-app format. The JWT claims contain an `apps` map where each key is an app ID and the value holds the user's role and permissions for that app:

```json
{
  "sub": "admin",
  "exp": 1700000000,
  "iat": 1699999100,
  "token_type": "access",
  "apps": {
    "my-app": {
      "role": "admin",
      "permissions": {
        "super_user": false,
        "databases": { ... }
      }
    }
  }
}
```

Each login adds the target app's entry to the `apps` map. Logging out removes it. A single token carries permissions for multiple apps without re-authenticating.

On each request, `JwtAuthProvider` extracts the target app's entry from the `apps` map. If present, permissions are used directly with no database lookup. If absent, the system falls through to AppMembership lookup.

## Making Requests

```bash
TOKEN=$(curl -sk -X POST https://localhost:9996/yeti-auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin","app_id":"my-app"}' | jq -r .access_token)

curl -sk -H "Authorization: Bearer $TOKEN" https://localhost:9996/my-app/MyTable
```

## Refreshing Tokens

```bash
curl -sk -X POST https://localhost:9996/yeti-auth/jwt_refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"eyJhbGciOiJIUzI1NiIs..."}'
```

Returns a new token pair with all accumulated app entries preserved.

## Auth Status

```bash
curl -sk -H "Authorization: Bearer $TOKEN" https://localhost:9996/yeti-auth/auth
```

## Per-App JWT Configuration

Each app can define its own JWT secret and token TTLs:

```yaml
auth:
  jwt:
    secret: "${MY_APP_JWT_SECRET}"
    accessTtl: 1800     # 30 minutes
    refreshTtl: 86400   # 24 hours
```

Secrets support environment variable interpolation (`${VAR}`).

## JavaScript Example

```javascript
async function login(username, password, appId) {
  const res = await fetch('https://localhost:9996/yeti-auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, app_id: appId }),
  });
  return res.json();
}

async function fetchData(token) {
  const res = await fetch('https://localhost:9996/my-app/MyTable', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json();
}
```

## Security Notes

- Access tokens are short-lived (default 15 minutes). Keep in memory, not localStorage.
- Refresh tokens are longer-lived. Store securely (httpOnly cookie or secure storage).
- Embedded permissions mean JWT is the fastest auth method -- no database call per request.

## See Also

- [Authentication Overview](auth-overview.md)
- [Basic Authentication](auth-basic.md) - Credential-per-request auth
- [OAuth Integration](auth-oauth.md) - Third-party provider auth
 Credential-per-request auth
- [OAuth Integration](auth-oauth.md) - Third-party provider auth
