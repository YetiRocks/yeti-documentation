# Roles & Permissions

Two layers govern access:

1. **Schema-side gating** via `@access` on each table — declarative,
   evaluated per (op, protocol) before any handler runs.
2. **Identity-side roles** via `AppMembership` → `Role` →
   permissions JSON — what each user is allowed to do.

This guide covers layer 2. For the declarative table-side surface,
see the [`@access` directive](../../reference/config/schema-directives.md#access--authorization).

## Schema-side: `@access`

Most apps don't need to hand-write permission JSON. Declare access at
the schema layer:

```graphql
# Public read; writes require a role on the table's matrix
type Article @table @export @access(
  public: [read]
  roles: { create: [editor, admin], update: [editor, admin], delete: [admin] }
) { ... }

# Per-(op, protocol) — admins update via REST, MQTT can't update at all
type Vault @table @export @access(
  roles: { update: { rest: [admin], graphql: [admin] } }
) { ... }
```

`@access(public: [...])` opens specific ops to anonymous traffic.
`@access(roles: {...})` defines which roles can perform each op.
Roles can be split per-protocol — REST / GraphQL / WS / SSE / MQTT
/ MCP / gRPC. See the directive reference for the full shape.

Tables without `@access` follow the app's auth pipeline default
(every authenticated user, unless a `Role`'s permissions JSON denies
the table).

## AppMembership table

Per-app access grants. Each record uses a compound key:

| Field | Type | Description |
|-------|------|-------------|
| `id` | String (PK) | `{appId}:{username}` compound key |
| `appId` | String | Application this membership grants access to |
| `username` | String | User this membership belongs to |
| `roleId` | String | FK to Role.id (`{appId}:{roleName}`) |
| `status` | String | `active`, `invited`, or `suspended` |
| `invitedBy` | String | Username of the inviter (if applicable) |
| `lastAccessAt` | Int | Unix timestamp of last access |
| `createdAt` | Int | Unix timestamp of creation |

A user with no AppMembership for an app has no access to that app (unless auto-signup creates one).

## Role Structure

Roles are scoped to an application via compound key `{appId}:{roleName}`. A role with `appId: "*"` is global.

```json
{
  "id": "my-app:editor",
  "appId": "my-app",
  "name": "Editor",
  "permissions": "{\"super_user\":false,\"databases\":{\"data\":{\"tables\":{\"*\":{\"read\":true,\"insert\":true,\"update\":true,\"delete\":false}}}}}"
}
```

The `permissions` field is a double-encoded JSON string (a JSON object serialized as a string value). The auth system unwraps this before deserializing into the `Permission` struct.

## Permission Struct

```json
{
  "super_user": false,
  "databases": {
    "data": {
      "tables": {
        "*": {
          "read": true, "insert": true, "update": true, "delete": false
        },
        "AuditLog": {
          "read": true, "insert": false, "update": false, "delete": false,
          "attribute_permissions": {
            "salary": { "read": false, "write": false }
          }
        }
      }
    }
  }
}
```

The hierarchy:

- `super_user: true` -- bypasses all permission checks
- `databases.{db}.tables.{TableName}` -- table-specific CRUD grants (`read`, `insert`, `update`, `delete`)
- `databases.{db}.tables.*` -- wildcard fallback for tables without explicit entries
- `attribute_permissions` -- per-field overrides within a table (see [Attribute-Level Access](attributes.md))

Table name matching is case-insensitive: roles store PascalCase names from the schema, but URL-based lookups work regardless of case.

## Role Management

```bash
# Create an app-scoped role
curl -sk -u admin:admin -X POST https://localhost:9996/yeti-auth/roles \
  -H "Content-Type: application/json" \
  -d '{"id":"my-app:editor","appId":"my-app","name":"Editor","permissions":"{\"super_user\":false,\"databases\":{\"data\":{\"tables\":{\"*\":{\"read\":true,\"insert\":true,\"update\":true,\"delete\":false}}}}}"}'

# List all roles
curl -sk -u admin:admin https://localhost:9996/yeti-auth/roles

# Update a role
curl -sk -u admin:admin -X PUT https://localhost:9996/yeti-auth/roles/my-app:editor \
  -H "Content-Type: application/json" \
  -d '{"id":"my-app:editor","appId":"my-app","name":"Editor (Updated)","permissions":"{\"super_user\":false,\"databases\":{\"data\":{\"tables\":{\"*\":{\"read\":true,\"insert\":true,\"update\":true,\"delete\":true}}}}}"}'

# Delete (super_user is protected from deletion)
curl -sk -u admin:admin -X DELETE https://localhost:9996/yeti-auth/roles/my-app:editor
```

## Membership Management

```bash
# Create a membership (grant access)
curl -sk -u admin:admin -X POST https://localhost:9996/yeti-auth/memberships \
  -H "Content-Type: application/json" \
  -d '{"id":"my-app:alice","appId":"my-app","username":"alice","roleId":"my-app:editor","status":"active"}'

# List memberships
curl -sk -u admin:admin https://localhost:9996/yeti-auth/memberships

# Remove access
curl -sk -u admin:admin -X DELETE https://localhost:9996/yeti-auth/memberships/my-app:alice
```

## Role Resolution

All auth methods follow the same resolution path:

1. **JWT with embedded permissions**: Fast path -- if the token's `apps` map contains the target app, permissions are used directly (no DB lookup)
2. **AppMembership exists**: Use its `roleId` to load the Role from the Role table
3. **No membership + auto-signup**: Create a membership with the configured default role
4. **No membership + invite/disabled**: Deny access

For OAuth users, the role is determined by the app's `oauth.rules` configuration before creating the auto-signup membership.

Services can provide an `AuthHook` to intercept role resolution before the default logic. See [Auth Hooks](hooks.md).

## Permission Checks

The permission system operates at two levels:

1. **Table-level**: `can_read_table()`, `can_insert_table()`, `can_update_table()`, `can_delete_table()`
2. **Attribute-level**: `can_read_attribute()`, `can_write_attribute()`, `has_unrestricted_attributes()`

Super users bypass all checks. See [Attribute-Level Access](attributes.md) for field-level details.

## See Also

- [Authentication Overview](overview.md)
- [`@access` directive](../../reference/config/schema-directives.md#access--authorization) — declarative table-side gating
- [Attribute-Level Access](attributes.md) — field-level permissions
- [Auth Hooks](hooks.md) — custom role resolution
