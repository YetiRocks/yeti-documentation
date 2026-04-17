# Authentication & Authorization

The `yeti-auth` service provides multi-app authentication with RBAC down to the field level. Choose a method: [Basic](auth-basic.md) | [JWT](auth-jwt.md) | [OAuth](auth-oauth.md) | [mTLS](auth-mtls.md)

Opt in by adding an `auth:` section to your app's config.yaml:

```yaml
auth:
  methods: [basic, jwt]
  signup: auto
  default_role: user
```

## Authentication Methods

The AuthPipeline tries each configured provider in order until one succeeds:

| Method | Header / Mechanism | Use Case |
|--------|-------------------|----------|
| [mTLS](auth-mtls.md) | Client certificate (TLS handshake) | Service-to-service, IoT, zero-trust |
| [Basic Auth](auth-basic.md) | `Authorization: Basic base64(user:pass)` | Server-to-server, scripts |
| [JWT](auth-jwt.md) | `Authorization: Bearer <token>` | SPAs, mobile apps, APIs |
| [OAuth](auth-oauth.md) | Session cookie | Web apps with third-party login |

## How Auth Works

1. Request arrives at an authenticated application
2. **AuthPipeline** runs each provider in order
3. First provider to recognize credentials returns an **AuthIdentity** (an enum: `Basic`, `Jwt`, `OAuth`, or `Mtls`)
4. The **AppMembership** table is checked for a membership record keyed by `{appId}:{username}`
5. If no membership exists and signup is `"auto"`, a membership is created with the configured default role
6. The membership's **roleId** resolves to a **Role** from the Role table
7. Role **permissions** are attached as an **AccessControl** object on the request context
8. Resource handlers check permissions for table and field access

No matching provider returns `401 Unauthorized`. No matching membership (with signup not `"auto"`) also returns `401`.

## Multi-App Auth

Yeti uses per-app role scoping through the **AppMembership** table. A single user can have different roles in different applications:

- **User** table: Global identity (one record per user, keyed by username)
- **AppMembership** table: Per-app access grants (compound key `{appId}:{username}`, links to an app-scoped Role)
- **Role** table: App-scoped roles (compound key `{appId}:{roleName}`, with `appId: "*"` for global roles)

A user authenticates once (proving identity), then authorization checks their membership in the specific app being accessed.

## Auth is Per-App

Each application independently declares its auth configuration. Apps without an `auth:` section in config.yaml have no authentication -- all requests are permitted. Public and authenticated APIs coexist on the same instance.

## Per-App Config

```yaml
auth:
  methods: [basic, jwt, oauth]   # explicit list, or omit for auto-detect
  signup: auto                    # "auto", "invite", or "disabled"
  default_role: user              # role assigned to auto-signup users
  jwt:
    secret: "${MY_APP_JWT_SECRET}"
    accessTtl: 1800
    refreshTtl: 86400
  oauth:
    github:
      clientId: "${GITHUB_CLIENT_ID}"
      clientSecret: "${GITHUB_CLIENT_SECRET}"
    rules:
      - strategy: provider
        pattern: "github"
        role: developer
```

When `methods` is omitted, auto-detection enables basic always, jwt if a secret is configured, and oauth if providers are present.

## Quick Setup

1. Create a user:

```bash
curl -sk -X POST https://localhost:9996/yeti-auth/users \
  -H "Content-Type: application/json" \
  -d '{"username":"myuser","password":"secure-password-123","roleId":"standard","email":"myuser@example.com"}'
```

2. Add auth to your app's config.yaml:

```yaml
auth: {}
```

3. Authenticate:

```bash
# Basic Auth
curl -sk -u myuser:secure-password-123 https://localhost:9996/my-app/MyTable

# JWT
TOKEN=$(curl -sk -X POST https://localhost:9996/yeti-auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"myuser","password":"secure-password-123","app_id":"my-app"}' | jq -r .access_token)

curl -sk -H "Authorization: Bearer $TOKEN" https://localhost:9996/my-app/MyTable
```

## Bootstrap

On first start with an empty database, yeti-auth consumes `.bootstrap.json` from the root directory. This creates the `super_user` role and an initial admin user with memberships for internal apps (yeti-auth, studio, yeti-admin).

The `super_user` role has full access and cannot be deleted or have its privileges reduced.

## Sub-Guides

- [mTLS Authentication](auth-mtls.md)
- [Basic Authentication](auth-basic.md)
- [JWT Authentication](auth-jwt.md)
- [OAuth Integration](auth-oauth.md)
- [Roles & Permissions](auth-rbac.md)
- [Attribute-Level Access](auth-attributes.md)
- [Auth Hooks](auth-hooks.md)
