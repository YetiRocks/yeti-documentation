# Basic Authentication

HTTP Basic authentication sends credentials with every request using `Authorization: Basic base64(username:password)`.

## How It Works

1. Client sends `Authorization: Basic base64(username:password)`
2. `BasicAuthProvider` looks up the user in the User table
3. Password verified against stored Argon2id hash
4. User's `roleId` resolves to a Role with permissions

## Configuration

Add `yeti-auth` to your app's extensions. Basic auth is always available when enabled:

```yaml
extensions:
  - yeti-auth: {}
```

## Creating Users

```bash
curl -sk -X POST https://localhost:9996/yeti-auth/users \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"strong-password-here","roleId":"standard","email":"alice@example.com"}'
```

Passwords are hashed with **Argon2id** (OWASP minimum parameters) before storage.

## Making Requests

```bash
curl -sk -u alice:strong-password-here https://localhost:9996/my-app/MyTable
```

## Credential Cache

The `BasicAuthProvider` caches successful authentications in memory with a **5-minute TTL** to avoid repeated Argon2id verification. Cache invalidates on password change or server restart.

## Managing Users

```bash
# List all users
curl -sk -u admin:admin https://localhost:9996/yeti-auth/users

# Get a specific user
curl -sk -u admin:admin https://localhost:9996/yeti-auth/users/alice

# Update a user's role
curl -sk -u admin:admin -X PUT https://localhost:9996/yeti-auth/users/alice \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","roleId":"admin","email":"alice@example.com"}'

# Delete a user
curl -sk -u admin:admin -X DELETE https://localhost:9996/yeti-auth/users/alice
```

## Security Notes

- Always use HTTPS - Basic auth credentials are base64-encoded, not encrypted
- Yeti runs HTTPS on port 9996 by default
- For browser apps, prefer [JWT](auth-jwt.md) or [OAuth](auth-oauth.md)
- Basic auth is ideal for server-to-server, CLI tools, and scripts

## See Also

- [Authentication Overview](auth-overview.md)
- [JWT Authentication](auth-jwt.md) - Stateless token-based auth
- [Roles & Permissions](auth-rbac.md) - Configuring access
