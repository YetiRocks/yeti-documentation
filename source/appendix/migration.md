# Migration Guide

Migrate existing backend applications to Yeti from Node.js/Express, Django, Rails, or similar frameworks.

## What Maps Directly

Applications using REST APIs, JSON data, and standard CRUD patterns translate directly:

| Traditional Approach | Yeti Equivalent |
|---------------------|-----------------|
| Route handlers (Express, Flask, etc.) | Custom resources (Rust plugins) |
| Database models / ORM schemas | GraphQL schema with `@table` directive |
| SQL / MongoDB queries | FIQL query language |
| Static file middleware | `static_files` in config.yaml |
| Auth middleware | yeti-auth extension (JWT, OAuth, RBAC) |
| Environment variables | `env:` section in yeti-config.yaml + `${VAR:-default}` substitution |

## Migration Steps

### 1. Create a Yeti Application

```bash
cd ~/yeti/applications
mkdir my-app && cd my-app
```

### 2. Define Your Schema

Convert database models to a GraphQL schema:

```graphql
type User @table @export {
    id: ID! @primaryKey
    email: String! @indexed
    name: String!
    createdAt: String @createdTime
    updatedAt: String @updatedTime
}
```

### 3. Create Configuration

```yaml
name: my-app
schemas:
  - schema.graphql
rest: true
```

### 4. Port Custom Endpoints

Rewrite traditional route handlers as Rust resources:

**Express (Node.js):**
```javascript
app.post('/users', async (req, res) => {
  req.body.created_at = new Date().toISOString();
  const user = await db.insert('users', req.body);
  res.json(user);
});
```

**Yeti:**
```rust,ignore
pub struct UserResource;
impl Resource for UserResource {
    fn name(&self) -> &'static str { "users" }
    async fn before_create(&self, data: &mut Value) -> Result<()> {
        data["created_at"] = chrono::Utc::now().to_rfc3339().into();
        Ok(())
    }
}
```

Many use cases need no custom resources. Schema-driven tables provide full CRUD, filtering, pagination, and real-time subscriptions out of the box.

### 5. Migrate Data

```bash
# Export from your existing system (adjust as needed)
curl http://old-server/api/users > users.json

# Import to Yeti
cat users.json | jq -c '.[]' | while read record; do
  curl -sk -X POST https://localhost:9996/my-app/User \
    -H "Content-Type: application/json" -d "$record"
done
```

### 6. Verify

```bash
yeti restart

# Test CRUD
curl -sk https://localhost:9996/my-app/User?limit=10
```

## Key Differences from Traditional Backends

| Aspect | Traditional | Yeti |
|--------|------------|------|
| Language | JavaScript/Python/Ruby | Rust (plugins), schema-driven (tables) |
| Database | Separate process (PostgreSQL, MongoDB) | Embedded RocksDB (zero network overhead) |
| API layer | Hand-written routes | Auto-generated from schema |
| Real-time | WebSocket library + custom code | Built-in SSE, WebSocket, MQTT |
| Auth | Passport.js / custom middleware | yeti-auth extension (JWT, OAuth, RBAC) |
| Deployment | App server + database + reverse proxy | Single binary |

## Migration Checklist

- [ ] Back up existing data
- [ ] Define GraphQL schemas for all data models
- [ ] Create config.yaml with appropriate settings
- [ ] Port custom endpoints to Rust resources (if needed)
- [ ] Migrate data to Yeti tables
- [ ] Test CRUD operations and FIQL queries
- [ ] Configure authentication (JWT, OAuth, or both)
- [ ] Set up TLS certificates
- [ ] Load test to verify performance
- [ ] Plan and execute cutover
- [ ] Monitor production
