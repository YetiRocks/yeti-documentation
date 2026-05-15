# Authentication & Authorization

The `yeti-auth` plugin provides multi-app authentication with RBAC
down to the field level. Auth is **per-app**: each application
declares its own configuration in `Cargo.toml`. Apps that omit auth
config are fully public (suitable for static-file apps, internal
read-only endpoints, etc.).

Pick a method (or several): [Basic](basic.md) · [JWT](jwt.md) ·
[OAuth](oauth.md) · [mTLS](mtls.md).

## Opt in

Add `[package.metadata.auth]` to your app's `Cargo.toml`:

```toml
[package.metadata.auth]
methods = ["basic", "jwt"]
signup = "auto"
default_role = "user"
```

| Field | Description |
|---|---|
| `methods` | Explicit list (`"basic"`, `"jwt"`, `"oauth"`, `"mtls"`); omit for auto-detect |
| `signup` | `"auto"`, `"invite"`, `"disabled"`, or `"magic-link"` |
| `default_role` | Role assigned to auto-signup users |

When `methods` is omitted, auto-detect enables: `basic` always; `jwt`
if a secret is configured; `oauth` if providers are present.

## Authentication methods

The `AuthPipeline` tries each enabled provider in order until one
succeeds.

| Method | Mechanism | Best for |
|---|---|---|
| [mTLS](mtls.md) | Client certificate (TLS handshake) | Service-to-service, IoT, zero-trust |
| [Basic](basic.md) | `Authorization: Basic base64(user:pass)` | Scripts, server-to-server |
| [JWT](jwt.md) | `Authorization: Bearer <token>` (+ rotating refresh) | SPAs, mobile, APIs |
| [OAuth](oauth.md) | Session cookie (+ PKCE flow) | Web apps with third-party login |

A request that matches no provider gets `401`. Auth failure inside a
provider (bad password, expired token) also returns `401` with a
provider-specific body.

## How the pipeline runs

```
Request
  ├─ AuthPipeline iterates methods in declared order
  │    ↓
  │  First match wins → AuthIdentity { Basic | Jwt | OAuth | Mtls }
  │    ↓
  ├─ AppMembership lookup keyed by {app_id}:{username}
  │    ↓
  │  No membership + signup="auto" → create with default_role
  │    ↓
  ├─ Role resolution → AccessControl attached to ctx
  │    ↓
  └─ Resource handler runs with permission checks per attribute
```

`AuthIdentity` is an enum on `ctx.auth_identity`:

```rust,ignore
pub enum AuthIdentity {
    Basic  { username: String },
    Jwt    { username: String, claims: Value },
    OAuth  { email: Option<String>, provider: String, claims: Value },
    Mtls   { username: String, cn: String, sans: Vec<String> },
}
```

## Multi-app role scoping

| Table | Purpose | Key shape |
|---|---|---|
| `User` | Global identity (one record per user) | `username` |
| `AppMembership` | Per-app access grants | `{app_id}:{username}` |
| `Role` | App-scoped roles (use `app_id="*"` for global) | `{app_id}:{role_name}` |

One user can hold different roles in different apps. The auth pipe
proves identity once; authorization picks the membership for the
specific app being accessed.

## Authorization — `@access` on tables

Per-table public-ops and RBAC are declared schema-side via
`@access`. See the [Roles & Permissions](rbac.md) guide for the full
matrix.

```graphql
# Anonymous reads and subscribes; writes still need auth
type ChatMessage @table @export @access(public: [read, subscribe]) { ... }

# Per-op RBAC matrix
type Orders @table @export @access(
  public: [read]
  roles: { create: [client, admin], update: [admin], delete: [admin] }
) { ... }

# Per-(op, protocol) matrix — admins can update via REST or GraphQL
# but NOT via MQTT
type Vault @table @export @access(
  roles: { update: { rest: [admin], graphql: [admin] } }
) { ... }
```

The per-protocol matrix lets you split read-only IoT traffic (MQTT)
from full CRUD over REST without writing custom resource code.

## Quick setup

```bash
# 1. Create a user
curl -sk -X POST https://localhost/yeti-auth/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "myuser",
    "password": "secure-password-123",
    "roleId": "standard",
    "email": "myuser@example.com"
  }'

# 2. Add auth to your app's Cargo.toml
#    [package.metadata.auth]
#    methods = ["basic", "jwt"]

# 3. Authenticate — Basic
curl -sk -u myuser:secure-password-123 https://localhost/my-app/MyTable

# 4. Authenticate — JWT
TOKEN=$(curl -sk -X POST https://localhost/yeti-auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"myuser","password":"secure-password-123","app_id":"my-app"}' \
  | jq -r .access_token)

curl -sk -H "Authorization: Bearer $TOKEN" https://localhost/my-app/MyTable
```

## What landed recently

- **Magic-link signup** (May 2026) — passwordless first-touch flow.
  Set `signup = "magic-link"`. yeti-auth issues a one-time link via
  the mail plugin; first click creates the user with the default
  role.
- **Refresh-token rotation** — every successful refresh issues a new
  refresh-token alongside a new access-token; the old refresh is
  invalidated. See [JWT](jwt.md).
- **PKCE on OAuth** (YTC-325 row 18 follow-up) — code-challenge and
  code-verifier on every OAuth flow. Default for all providers.
- **Waitlist** — `signup = "invite"` puts unknown users on a waitlist
  table; admins approve via the admin SPA. Useful for closed betas.
- **Per-(op, protocol) RBAC** (YTC-335, May 2026) — `@access(roles:)`
  accepts the nested-object form documented above.

## Bootstrap

On first start with an empty database, yeti-auth consumes
`.bootstrap.json` from the root directory. This creates the
`super_user` role and an initial admin user with memberships for
internal apps (yeti-auth, studio, yeti-admin).

The `super_user` role has full access and cannot be deleted or have
its privileges reduced.

## Sub-guides

- [Basic Authentication](basic.md)
- [JWT Authentication](jwt.md)
- [OAuth Integration](oauth.md)
- [mTLS Authentication](mtls.md)
- [Roles & Permissions](rbac.md)
- [Attribute-Level Access](attributes.md)
- [Auth Hooks](hooks.md)
