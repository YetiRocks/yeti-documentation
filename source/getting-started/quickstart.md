# Quickstart

Build a REST API in 5 minutes.

## Step 1: Create an Application

```bash
mkdir ~/yeti/applications/my-app
```

Create `~/yeti/applications/my-app/config.yaml`:

```yaml
name: "My App"
app_id: "my-app"
version: "1.0.0"
enabled: true
rest: true
graphql: true
sse: true
schemas:
  - schema.graphql
```

## Step 2: Define Your Schema

Create `~/yeti/applications/my-app/schema.graphql`:

```graphql
type User @table @export(rest: true, sse: true) {
    id: ID! @primaryKey
    name: String!
    email: String! @indexed
    role: String @indexed
    active: Boolean
    createdAt: Date @createdTime
    updatedAt: Date @updatedTime
}
```

This generates:
- `POST /my-app/User` - Create
- `GET /my-app/User` - List (with FIQL filtering, pagination, sorting)
- `GET /my-app/User/{id}` - Get by ID
- `PUT /my-app/User/{id}` - Replace
- `PATCH /my-app/User/{id}` - Partial update
- `DELETE /my-app/User/{id}` - Delete
- `GET /my-app/User?stream=sse` - Real-time updates

## Step 3: Restart the Server

```bash
yeti restart
```

First run compiles the plugin (~2 minutes). You'll see:

```
[INFO] Registered my-app (1 table, 0 resources)
```

## Step 4: Test Your API

### Create a user

```bash
curl -sk -X POST https://localhost:9996/my-app/User \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice",
    "email": "alice@example.com",
    "role": "admin",
    "active": true
  }'
```

### List all users

```bash
curl -sk https://localhost:9996/my-app/User
```

### Filter with FIQL

```bash
# Users with role "admin"
curl -sk "https://localhost:9996/my-app/User?role==admin"

# Active users, sorted by name
curl -sk "https://localhost:9996/my-app/User?active==true&sort=name"

# Pagination
curl -sk "https://localhost:9996/my-app/User?limit=10&offset=0"
```

### Update a user

```bash
curl -sk -X PATCH https://localhost:9996/my-app/User/USER_ID \
  -H "Content-Type: application/json" \
  -d '{"role": "viewer"}'
```

### Delete a user

```bash
curl -sk -X DELETE https://localhost:9996/my-app/User/USER_ID
```

### Stream real-time updates

```bash
# In one terminal, listen for updates
curl -sk "https://localhost:9996/my-app/User?stream=sse"

# In another terminal, create a user and it appears in the stream
curl -sk -X POST https://localhost:9996/my-app/User \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "email": "bob@example.com"}'
```

## Next Steps

- [Your First Application](first-application.md) - Build a complete app with custom resources and seed data
- [FIQL Queries](../guides/fiql.md) - Advanced filtering syntax
- [Authentication](../guides/auth-overview.md) - Add auth to your app
- [Custom Resources](../guides/custom-resources.md) - Add business logic in Rust
