# Attribute-Level Access

Beyond table-level CRUD, Yeti supports field-level access control. Different roles see different fields from the same table.

## Configuration

Add `attribute_permissions` within a table's permission block in the role's `permissions` JSON:

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

The `AttributePermission` struct has two fields:

- `read` -- whether this field can be returned in query results
- `write` -- whether this field can be included in insert/update payloads

Fields without an explicit `attribute_permissions` entry default to allowed (`read: true, write: true`).

## Read Filtering

The `restrict_select_fields()` function strips unauthorized fields from the query's select list **before** the storage resolver runs. The resolver never sees restricted fields.

**Admin** (full access):
```json
{"id": "emp-1", "name": "Alice Smith", "department": "Engineering", "salary": 150000, "ssn": "123-45-6789"}
```

**Viewer** (salary/ssn restricted):
```json
{"id": "emp-1", "name": "Alice Smith", "department": "Engineering"}
```

Restricted fields are **omitted entirely** from responses -- not null, not redacted.

For nested relationship sub-fields, `restrict_select_fields()` recursively checks permissions against the target table's definition using the schema.

## Write Validation

The `check_table_write()` function rejects write operations that include unauthorized fields. Attempting to write restricted fields returns 403:

```bash
curl -sk -u viewer:password -X PUT https://localhost:9996/my-app/Employee/emp-1 \
  -H "Content-Type: application/json" \
  -d '{"id":"emp-1","name":"Alice Smith","salary":200000}'
```

```json
{
  "type": "urn:yeti:error:forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Access denied: cannot write attribute 'salary'"
}
```

The `id` field (primary key) is always allowed in write payloads regardless of attribute permissions.

## Fast Path

The `has_unrestricted_attributes()` method provides a fast path: if no `attribute_permissions` are configured for a table, the system skips all per-field checks and uses `FullAccess` mode. Attribute-level enforcement has zero cost for roles that do not use it.

The dispatch layer pre-computes a `TablePermission` enum per request:

- `Public` -- no auth required (from `@access(public: [...])`)
- `FullAccess` -- authenticated with no attribute restrictions
- `AttributeRestricted { readable, writable }` -- pre-computed field sets for this user's role

## Example Roles

**standard** -- restricted sensitive fields:
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
curl -sk -u admin:admin https://localhost:9996/my-app/Employee

# Standard user -- salary and ssn omitted from results
curl -sk -u user:password https://localhost:9996/my-app/Employee
```

## See Also

- [Roles & Permissions](auth-rbac.md) - Table-level CRUD permissions
- [Authentication Overview](auth-overview.md) - Auth providers
