# JWT Authentication

JWT provides stateless, token-based access. Authenticate once, receive a token pair (access + refresh), then use the access token for subsequent requests.

## Login

```bash
curl -sk -X POST https://localhost:9996/yeti-auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

## Making Requests

```bash
TOKEN=$(curl -sk -X POST https://localhost:9996/yeti-auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r .access_token)

curl -sk -H "Authorization: Bearer $TOKEN" https://localhost:9996/my-app/MyTable
```

## Embedded Permissions

The access token contains the user's role permissions directly. The `JwtAuthProvider` decodes permissions from the token without any database call, making JWT the fastest auth method.

## Refreshing Tokens

```bash
curl -sk -X POST https://localhost:9996/yeti-auth/jwt_refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"eyJhbGciOiJIUzI1NiIs..."}'
```

Returns a new token pair.

## Auth Status

```bash
curl -sk -H "Authorization: Bearer $TOKEN" https://localhost:9996/yeti-auth/auth
```

## JavaScript Example

```javascript
async function login(username, password) {
  const res = await fetch('https://localhost:9996/yeti-auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
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
- Changing a user's password invalidates all tokens.

## See Also

- [Authentication Overview](auth-overview.md)
- [Basic Authentication](auth-basic.md) - Credential-per-request auth
- [OAuth Integration](auth-oauth.md) - Third-party provider auth
