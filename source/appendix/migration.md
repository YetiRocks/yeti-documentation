# Migrating from Harper to Yeti

## What's Compatible

- Resource API (CRUD), FIQL queries, GraphQL schemas, static file serving, config.yaml, multi-tenancy

## Migration Steps

### 1. Create Yeti Application

```bash
cd ~/yeti/applications
mkdir my-app && cd my-app
```

### 2. Copy Configuration

```bash
cp /path/to/harper-app/config.yaml .
cp /path/to/harper-app/schema.graphql .
cp -r /path/to/harper-app/web ./static
```

No modifications needed - Yeti uses the same config.yaml and schema.graphql formats.

### 3. Port Custom Resources

Harper JavaScript resources need to be rewritten in Rust:

**Harper:**
```javascript
export default {
  users: {
    beforeCreate: async (data) => {
      data.created_at = new Date().toISOString();
      return data;
    }
  }
}
```

**Yeti:**
```rust
pub struct UserResource;
impl Resource for UserResource {
    fn name(&self) -> &'static str { "users" }
    async fn before_create(&self, data: &mut Value) -> Result<()> {
        data["created_at"] = chrono::Utc::now().to_rfc3339().into();
        Ok(())
    }
}
```

### 4. Migrate Data

```bash
# Export from Harper
curl http://localhost:9996/User > users.json

# Import to Yeti
cat users.json | jq -c '.[]' | while read record; do
  curl -X POST http://localhost:9997/User \
    -H "Content-Type: application/json" -d "$record"
done
```

### 5. Verify

```bash
yeti restart

# Compare responses
curl http://localhost:9996/User/test-id > harper.json
curl http://localhost:9997/User/test-id > yeti.json
diff harper.json yeti.json
```

## Migration Checklist

- [ ] Backup Harper database
- [ ] Copy config.yaml and schema.graphql
- [ ] Copy static files
- [ ] Port custom resources to Rust
- [ ] Migrate data
- [ ] Test CRUD operations and FIQL queries
- [ ] Test authentication
- [ ] Load test
- [ ] Plan and execute cutover
- [ ] Monitor production
- [ ] Decommission Harper after validation
