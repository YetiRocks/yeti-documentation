# Table Access

Tables are the primary data interface. The SDK provides three levels of table access: `Table` (high-level CRUD), `TableExt` (typed operations on `KvBackend`), and `QueryBuilder` (filtered queries).

## Getting a Table

### From ResourceParams

```rust,ignore
// Shorthand -- most common
let table = ctx.get_table("Product")?;

// Via Tables accessor
let tables = ctx.tables()?;
let users = tables.get("User")?;

// Check existence
if tables.has("Product") {
    // table exists
}
```

### Low-level backend access

```rust,ignore
// Returns Arc<dyn KvBackend> for raw byte operations
let backend = ctx.table("Product")?;
```

## Table (High-Level CRUD)

The `Table` struct provides async CRUD operations with automatic serialization.

### Table metadata

```rust,ignore
fn name(&self) -> &str
fn backend(&self) -> &Arc<dyn KvBackend>
```

### Read operations

```rust,ignore
// Get by ID -- returns Option<Value>
let record = table.get("prod-123").await?;

// Get by ID -- returns 404 if missing
let record = table.get_or_404("prod-123").await?;

// Check existence
let exists: bool = table.does_exist("prod-123").await?;

// Get all records
let records: Vec<Value> = table.get_all().await?;

// Count records
let total: u64 = table.count().await?;
```

### Write operations

```rust,ignore
// Create with auto-generated UUID v7 ID (adds "id" field to the record)
let created: Value = table.create(json!({"name": "Widget", "price": 29.99})).await?;

// Put (upsert -- create or fully replace)
table.put("prod-123", json!({"id": "prod-123", "name": "Widget"})).await?;

// Patch (partial update -- merges fields into existing record)
table.patch("prod-123", json!({"price": 24.99})).await?;

// Delete by ID -- returns true if record existed
let existed: bool = table.delete("prod-123").await?;

// Delete all records -- returns count deleted
let count: u64 = table.delete_all().await?;
```

### Search and aggregation

```rust,ignore
// Find all records where a field matches a value
let active_users: Vec<Value> = table.find("status", "active").await?;

// Find the first matching record
let admin: Option<Value> = table.find_one("role", "admin").await?;

// Count records grouped by field
let by_status: HashMap<String, usize> = table.count_by("status").await?;
// {"active": 42, "inactive": 7, "pending": 3}

// Group records by field
let by_category: HashMap<String, Vec<Value>> = table.group_by("category").await?;
// {"Tools": [{...}], "Electronics": [{...}]}
```

### QueryBuilder

Build filtered queries with a fluent API. Access via `table.query()`:

```rust,ignore
fn query(&self) -> QueryBuilder<'_, dyn KvBackend>
```

```rust,ignore
let results: Vec<Value> = table.query()
    .where_eq("status", "active")
    .where_gt("price", 100)
    .where_lt("price", 500)
    .limit(10)
    .offset(20)
    .execute()
    .await?;
```

#### Condition methods

| Method | Description |
|--------|-------------|
| `where_eq(field, value)` | field == value |
| `where_ne(field, value)` | field != value |
| `where_gt(field, value)` | field > value |
| `where_gte(field, value)` | field >= value |
| `where_lt(field, value)` | field < value |
| `where_lte(field, value)` | field <= value |
| `where_contains(field, value)` | substring match |
| `where_starts_with(field, value)` | prefix match |
| `where_ends_with(field, value)` | suffix match |
| `where_true(field)` | field == true |
| `where_false(field)` | field == false |
| `where_null(field)` | field == null |
| `where_not_null(field)` | field != null |
| `where_between(field, low, high)` | low < field < high |
| `where_between_inclusive(field, low, high)` | low <= field <= high |

#### Conditional filters

Add conditions only when a predicate is true. Useful for optional user input:

```rust,ignore
let category = ctx.get_str("category", "");

let results: Vec<Value> = table.query()
    .where_eq_if("category", &category, !category.is_empty())
    .where_eq_non_empty("status", ctx.get("status").unwrap_or(""))
    .where_gte_if("price", min_price, min_price > 0)
    .execute()
    .await?;
```

Available: `where_eq_if`, `where_eq_non_empty`, `where_gt_if`, `where_gte_if`, `where_lt_if`, `where_lte_if`.

#### Logical operators

```rust,ignore
// Default: AND (all conditions must match)
let results: Vec<Value> = table.query()
    .where_eq("status", "active")
    .where_eq("role", "admin")
    .execute()
    .await?;

// OR: any condition matches
let results: Vec<Value> = table.query()
    .or()
    .where_eq("name", "Alice")
    .where_eq("name", "Bob")
    .execute()
    .await?;
```

#### Pagination

```rust,ignore
let results: Vec<Value> = table.query()
    .where_eq("status", "active")
    .offset(20)
    .limit(10)
    .execute()
    .await?;
```

#### Terminal methods

```rust,ignore
// Get all matching records
let results: Vec<Value> = query.execute().await?;

// Count matching records
let count: usize = query.count().await?;

// Get first matching record
let first: Option<Value> = query.first().await?;

// Get first or error
let record: Value = query.first_or_err("No matching user found").await?;
```

## TableExt (Low-Level Typed Access)

Extension trait on `dyn KvBackend` for typed serialization/deserialization with string keys. Use this when you need to work with custom types or access the raw backend.

### Methods

```rust,ignore
async fn get<T: DeserializeOwned>(&self, key: impl AsRef<str>) -> Result<Option<T>>
async fn get_or<T: DeserializeOwned>(&self, key: impl AsRef<str>, default: T) -> Result<T>
async fn get_required<T: DeserializeOwned>(&self, key: impl AsRef<str>) -> Result<T>
async fn put<T: Serialize>(&self, key: impl AsRef<str>, value: &T) -> Result<()>
async fn delete(&self, key: impl AsRef<str>) -> Result<()>
async fn exists(&self, key: impl AsRef<str>) -> Result<bool>
async fn get_many<T: DeserializeOwned>(&self, keys: &[&str]) -> Result<Vec<Option<T>>>
async fn scan_records<T: DeserializeOwned>(&self) -> Result<Vec<T>>
async fn scan_records_with_prefix<T: DeserializeOwned>(&self, prefix: impl AsRef<str>) -> Result<Vec<T>>
async fn scan_records_with_keys<T: DeserializeOwned>(&self, prefix: impl AsRef<str>) -> Result<Vec<(String, T)>>
async fn scan_key_names(&self, prefix: impl AsRef<str>) -> Result<Vec<String>>
```

### Examples

```rust,ignore
let backend = ctx.table("Config")?;

// Typed get/put
#[derive(Serialize, Deserialize)]
struct AppConfig {
    theme: String,
    max_items: u32,
}

let config: Option<AppConfig> = TableExt::get(&*backend, "settings").await?;

let default_config = AppConfig { theme: "dark".into(), max_items: 100 };
let config: AppConfig = TableExt::get_or(&*backend, "settings", default_config).await?;

TableExt::put(&*backend, "settings", &config).await?;

// Required (errors if missing)
let config: AppConfig = TableExt::get_required(&*backend, "settings").await?;

// Batch get
let configs: Vec<Option<AppConfig>> = TableExt::get_many(&*backend, &["a", "b", "c"]).await?;

// Scan all records
let all: Vec<Value> = TableExt::scan_records(&*backend).await?;

// Scan with prefix
let tenant_users: Vec<Value> = TableExt::scan_records_with_prefix(&*backend, "tenant:123:").await?;

// Scan keys only (no value loading)
let keys: Vec<String> = TableExt::scan_key_names(&*backend, "user:").await?;
```

System keys (`__yeti_` prefix and `:idx:` keys) are automatically filtered from scan results.

## Complete Example

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Dashboard {
    get(request, ctx) => {
        let orders = ctx.get_table("Order")?;

        let total = orders.count().await?;
        let by_status = orders.count_by("status").await?;
        let pending = orders.find("status", "pending").await?;

        let high_value: Vec<Value> = orders.query()
            .where_gt("amount", 1000)
            .where_eq("status", "pending")
            .limit(5)
            .execute()
            .await?;

        ok(json!({
            "totalOrders": total,
            "byStatus": by_status,
            "pendingCount": pending.len(),
            "highValuePending": high_value
        }))
    }
});
```
