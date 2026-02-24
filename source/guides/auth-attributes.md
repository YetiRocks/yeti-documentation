# Attribute-Level Access

Beyond table-level CRUD, Yeti supports field-level access control. Different roles see different fields from the same table.

## Configuration

Add `attribute_permissions` within a table's permission block:

```json
{
  "databases": {
    "data": {
      "tables": {
        "Employee": {
          "read": true,
          "insert": false,
          "update": false,
          "delete": false,
          "attribute_permissions": {
            "salary": { "read": false, "write": false },
            "ssn": { "read": false, "write": false }
          }
        }
      }
    }
  }
}
```

## Read Projection

Restricted fields are **omitted entirely** from responses - not null, not redacted.

**Admin** (full access):
```json
{"id": "emp-1", "name": "Alice Smith", "department": "Engineering", "salary": 150000, "ssn": "123-45-6789"}
```

**Viewer** (salary/ssn restricted):
```json
{"id": "emp-1", "name": "Alice Smith", "department": "Engineering"}
```

## Write Validation

Attempting to write restricted fields returns 403:

```bash
curl -sk -u viewer:password -X PUT https://localhost:9996/my-app/Employee/emp-1 \
  -H "Content-Type: application/json" \
  -d '{"id":"emp-1","name":"Alice Smith","salary":200000}'
```

```json
{"error": "Access denied: cannot write attributes [salary] in data.Employee"}
```

## Example Roles

**standard** - restricted sensitive fields:
```json
{
  "super_user": false,
  "databases": {
    "data": {
      "tables": {
        "Employee": {
          "read": true, "insert": true, "update": true, "delete": false,
          "attribute_permissions": {
            "salary": { "read": false, "write": false },
            "ssn": { "read": false, "write": false }
          }
        }
      }
    }
  }
}
```

```bash
# Admin sees all fields
curl -sk -u admin:admin https://localhost:9996/web-auth-demo/Employee

# Standard user - salary and ssn omitted
curl -sk -u user:password https://localhost:9996/web-auth-demo/Employee
```

## Implementation

The `PermissionContext` calculates readable attributes once per query:

1. `from_params()` - intersects schema fields with role's read permissions
2. `needs_projection()` - true if any fields need filtering
3. `project_record()` / `project_records()` - removes restricted fields

Super users bypass all attribute checks.

## See Also

- [Roles & Permissions](auth-rbac.md) - Table-level CRUD permissions
- [Authentication Overview](auth-overview.md) - Auth providers
