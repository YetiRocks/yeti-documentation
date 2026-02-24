# Roles & Permissions

Each user has a `roleId` that maps to a Role record with structured permissions.

## Role Structure

```json
{
  "id": "standard",
  "name": "Standard User",
  "permissions": "{\"super_user\":false,\"databases\":{\"data\":{\"tables\":{\"*\":{\"read\":true,\"insert\":true,\"update\":true,\"delete\":false}}}}}"
}
```

The `permissions` field is a JSON string:

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
          "read": true, "insert": false, "update": false, "delete": false
        }
      }
    }
  }
}
```

## Permission Hierarchy

Evaluated most-specific first:

1. **Table-specific**: `databases.{db}.tables.{TableName}`
2. **Wildcard**: `databases.{db}.tables.*`
3. **Super user**: `super_user: true` bypasses all checks

## Built-in Roles

| Role | Permissions |
|------|-------------|
| `super_user` | Full access. Cannot be deleted. |
| `admin` | Full access (super_user: true). |
| `standard` | Read, insert, update. No delete. |
| `viewer` | Read-only. |

## Managing Roles

```bash
# Create
curl -sk -u admin:admin -X POST https://localhost:9996/yeti-auth/roles \
  -H "Content-Type: application/json" \
  -d '{"id":"editor","name":"Editor","permissions":"{\"super_user\":false,\"databases\":{\"data\":{\"tables\":{\"*\":{\"read\":true,\"insert\":true,\"update\":true,\"delete\":false}}}}}"}'

# List
curl -sk -u admin:admin https://localhost:9996/yeti-auth/roles

# Update
curl -sk -u admin:admin -X PUT https://localhost:9996/yeti-auth/roles/editor \
  -H "Content-Type: application/json" \
  -d '{"id":"editor","name":"Editor (Updated)","permissions":"{\"super_user\":false,\"databases\":{\"data\":{\"tables\":{\"*\":{\"read\":true,\"insert\":true,\"update\":true,\"delete\":true}}}}}"}'

# Delete (super_user is protected)
curl -sk -u admin:admin -X DELETE https://localhost:9996/yeti-auth/roles/editor
```

## Role Resolution

- **Basic Auth / JWT**: User's `roleId` looked up in Role table
- **OAuth**: Per-app config rules map provider/email patterns to role IDs

Extensions can provide an `AuthHook` to intercept role resolution before default logic. See [Auth Hooks](auth-hooks.md).

## Seed Data

Place role/user JSON in `yeti-auth/data/` for new deployments:

```json
{
  "database": "auth",
  "table": "Role",
  "records": [
    {
      "id": "custom-role",
      "name": "Custom Role",
      "permissions": "{\"super_user\":false,\"databases\":{\"data\":{\"tables\":{\"*\":{\"read\":true,\"insert\":false,\"update\":false,\"delete\":false}}}}}",
      "createdAt": 1738800000
    }
  ]
}
```

Loaded automatically on first start with empty database.

## Permission Checks

1. `check_table_read_permission()` - table read access
2. `check_table_write_permission()` - insert/update/delete access
3. `validate_writable_attributes()` - field-level write permissions
4. `filter_readable_attributes()` - removes restricted fields from responses

Super users bypass all checks.

## See Also

- [Authentication Overview](auth-overview.md)
- [Attribute-Level Access](auth-attributes.md) - Field-level permissions
- [Building Extensions](building-extensions.md) - Custom auth hooks
