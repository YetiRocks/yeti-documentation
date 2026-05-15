# Quickstart

Build a REST API in 5 minutes. Requires a running Yeti server ([install first](installation.md)).

## Step 1: Create an Application

```bash
mkdir ~/yeti/applications/my-app
```

Create `~/yeti/applications/my-app/Cargo.toml`:

```toml
[package]
name = "my-app"
edition = "2024"
version = "1.0.0"

[package.metadata.app]
app_id = "my-app"
name = "My App"
rest = true
graphql = true
schemas = { path = "schema.graphql" }

[dependencies]
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
- `POST /my-app/User` -- Create
- `GET /my-app/User` -- List with FIQL filtering, pagination, sorting
- `GET /my-app/User/{id}` -- Get by ID
- `PUT /my-app/User/{id}` -- Replace
- `PATCH /my-app/User/{id}` -- Partial update
- `DELETE /my-app/User/{id}` -- Delete
- `GET /my-app/User?stream=sse` -- Real-time updates

## Step 3: Restart the Server

Yeti detects new applications on startup. Restart to load yours:

```bash
yeti restart
```

First run compiles the plugin (~2 minutes):

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
# Terminal 1: listen for updates
curl -sk "https://localhost:9996/my-app/User?stream=sse"

# Terminal 2: create a user -- it appears in the stream
curl -sk -X POST https://localhost:9996/my-app/User \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "email": "bob@example.com"}'
```

## Next Steps

- [Your First Application](first-application.md) - Build a complete app with custom resources and seed data
- [FIQL Queries](../guides/fiql.md) - Advanced filtering syntax
- [Authentication](../guides/auth-overview.md) - Add auth to your app
- [Custom Resources](../guides/custom-resources.md) - Add business logic in Rust
