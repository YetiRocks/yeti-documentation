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

## Refreshing tokens — rotation by default

```bash
curl -sk -X POST https://localhost:9996/yeti-auth/jwt_refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"eyJhbGciOiJIUzI1NiIs..."}'
```

Returns a **new** token pair. **The old refresh token is invalidated
on every refresh** (rotation, landed May 2026). Clients must drop the
previous refresh and persist the new one — using a rotated refresh
token a second time results in 401 and the user's entire refresh
chain is revoked.

This is RFC 6749 §6 rotating-refresh semantics. It defends against
refresh-token theft: an attacker who exfiltrates a refresh sees it
work once, then the next legitimate refresh from the real client
fails — yeti-auth detects the second use and revokes the family.

Embedded app permissions roll forward across refreshes — the new
access token carries all accumulated app entries.

## Auth Status

```bash
curl -sk -H "Authorization: Bearer $TOKEN" https://localhost:9996/yeti-auth/auth
```

## Per-App JWT Configuration

Each app can define its own JWT secret and token TTLs:

```toml
[package.metadata.auth.jwt]
secret = "${MY_APP_JWT_SECRET}"
access_ttl = 1800       # 30 minutes
refresh_ttl = 86400     # 24 hours
```

Secrets support environment-variable interpolation via `${VAR}`.

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

- [Authentication Overview](overview.md)
- [Basic Authentication](basic.md) - Credential-per-request auth
- [OAuth Integration](oauth.md) - Third-party provider auth
 Credential-per-request auth
- [OAuth Integration](oauth.md) - Third-party provider auth
