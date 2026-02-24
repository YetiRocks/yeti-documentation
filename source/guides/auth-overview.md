# Authentication & Authorization

The `yeti-auth` extension provides authentication with role-based access control (RBAC) down to the field level. Apps opt in by declaring it in `extensions:`:

```yaml
extensions:
  - yeti-auth:
      oauth:
        rules:
          - strategy: provider
            pattern: "github"
            role: standard
```

## Authentication Methods

The AuthPipeline tries each provider in order until one succeeds:

| Method | Header | Use Case |
|--------|--------|----------|
| [Basic Auth](auth-basic.md) | `Authorization: Basic base64(user:pass)` | Server-to-server, scripts |
| [JWT](auth-jwt.md) | `Authorization: Bearer <token>` | SPAs, mobile apps, APIs |
| [OAuth](auth-oauth.md) | Session cookie | Web apps with third-party login |

## How Auth Works

1. Request arrives at an authenticated application
2. **AuthPipeline** runs each provider in order
3. First provider to recognize credentials returns an **AuthIdentity**
4. Identity's **roleId** resolves to a **Role** from the Role table
5. Role **permissions** are attached as an **AccessControl** object
6. Resource handlers check permissions for table and field access

No matching provider returns `401 Unauthorized`.

## Auth is Per-App

Apps without `yeti-auth` in `extensions:` have no authentication - all requests are permitted. Public and authenticated APIs coexist on the same instance.

## Quick Setup

1. Create a user:

```bash
curl -sk -X POST https://localhost:9996/yeti-auth/users \
  -H "Content-Type: application/json" \
  -d '{"username":"myuser","password":"secure-password-123","roleId":"standard","email":"myuser@example.com"}'
```

2. Add `yeti-auth` to your app:

```yaml
extensions:
  - yeti-auth: {}
```

3. Authenticate:

```bash
# Basic Auth
curl -sk -u myuser:secure-password-123 https://localhost:9996/my-app/MyTable

# JWT
TOKEN=$(curl -sk -X POST https://localhost:9996/yeti-auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"myuser","password":"secure-password-123"}' | jq -r .access_token)

curl -sk -H "Authorization: Bearer $TOKEN" https://localhost:9996/my-app/MyTable
```

## Default Users and Roles

**Users**: `admin` (role: admin), `user` (role: viewer)

**Roles**: `super_user`, `admin`, `standard`, `viewer`

The `super_user` role has full access and cannot be deleted.

## Sub-Guides

- [Basic Authentication](auth-basic.md)
- [JWT Authentication](auth-jwt.md)
- [OAuth Integration](auth-oauth.md)
- [Roles & Permissions](auth-rbac.md)
- [Attribute-Level Access](auth-attributes.md)
