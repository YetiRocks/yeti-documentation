# Table Access

Tables are the primary data interface. Get a table reference from the resource context, then use async methods for CRUD, search, and aggregation.

## Getting a Table

```rust,ignore
// Single table by name
let table = ctx.get_table("Product")?;

// All tables for the app
let tables = ctx.tables()?;
let users = tables.get("User")?;
```

## CRUD Operations

### Read

```rust,ignore
// Get by ID (returns Option<Value>)
let record = table.get("prod-123").await?;

// Get by ID, return 404 if missing
let record = table.get_or_404("prod-123").await?;

// Check existence
let exists: bool = table.does_exist("prod-123").await?;

// Get all records
let records: Vec<Value> = table.get_all().await?;

// Count records
let total: usize = table.count().await?;
```

### Write

```rust,ignore
// Create (returns error if ID exists)
table.create("prod-123", json!({"id": "prod-123", "name": "Widget"})).await?;

// Put (upsert - create or replace)
table.put("prod-123", json!({"id": "prod-123", "name": "Widget"})).await?;

// Patch (partial update - merges fields)
table.patch("prod-123", json!({"price": 29.99})).await?;

// Delete by ID
table.delete("prod-123").await?;

// Delete all records
table.delete_all().await?;
```

## Search (NEW)

Find records by field value without loading the entire table:

```rust,ignore
// Find all records matching a field value
let active_users: Vec<Value> = table.find("status", "active").await?;

// Find exactly one record (returns Option<Value>)
let admin: Option<Value> = table.find_one("role", "admin").await?;
```

## Aggregation (NEW)

### count_by

Count records grouped by a field value:

```rust,ignore
let by_status: HashMap<String, usize> = table.count_by("status").await?;
// {"active": 42, "inactive": 7, "pending": 3}
```

Before/after comparison:

```rust,ignore
// Before: manual HashMap building
let records = table.get_all().await?;
let mut by_status: HashMap<String, usize> = HashMap::new();
for record in &records {
    if let Some(status) = record["status"].as_str() {
        *by_status.entry(status.to_string()).or_insert(0) += 1;
    }
}

// After: 1 line
let by_status = table.count_by("status").await?;
```

### group_by

Group full records by a field value:

```rust,ignore
let by_category: HashMap<String, Vec<Value>> = table.group_by("category").await?;
// {"Tools": [{...}, {...}], "Electronics": [{...}]}
```

## Query Builder

Chain query conditions for filtered reads:

```rust,ignore
let results = table.query()
    .where_eq("status", "active")
    .execute()
    .await?;
```

## Complete Example

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Dashboard {
    get(request, ctx) => {
        let orders = ctx.get_table("Order")?;

        let total = orders.count().await?;
        let by_status = orders.count_by("status").await?;
        let recent = orders.find("status", "pending").await?;

        reply().json(json!({
            "totalOrders": total,
            "byStatus": by_status,
            "pendingOrders": recent.len(),
            "pending": recent
        }))
    }
});
```
