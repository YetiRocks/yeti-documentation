# Table Access

Three levels: `Table` (CRUD facade), `Query` (filtered queries), and
`TableExt` (typed raw-backend access). All available via
`yeti_sdk::prelude::*`.

## Getting a table

```rust,ignore
// From a request context — the common case
let products = ctx.table("Product")?;

// Multiple tables in one call
let tables = ctx.tables()?;
let orders = tables.get("Order")?;
let users  = tables.get("User")?;

if tables.has("AuditLog") {
    let audit = tables.get("AuditLog")?;
}
```

The `Table` struct wraps the underlying backend, schema metadata, and
optional pubsub channel. It's cheap to clone (everything inside is
`Arc`-shared).

## CRUD

```rust,ignore
let products = ctx.table("Product")?;

// Read
let one  = products.get("p1").await?;            // Option<Value>
let safe = products.get_or_404("p1").await?;     // 404 on miss
let all  = products.get_all().await?;            // Vec<Value>
let n    = products.count().await?;               // u64
let here = products.does_exist("p1").await?;     // bool

// Write
let created = products.create(json!({"name": "Widget", "price": 29.99})).await?;
//             ^ adds a UUID v7 `id` field
products.put("p1", json!({"id": "p1", "name": "Widget"})).await?;
products.patch("p1", json!({"price": 24.99})).await?;
let existed = products.delete("p1").await?;       // bool
let n = products.delete_all().await?;             // u64
```

`create()` auto-generates a UUID v7 `id`. `put()` is a full replace
(upsert). `patch()` merges into the existing record.

### CAS (compare-and-set)

For lock-free coordination across writers:

```rust,ignore
// Replace only if current value matches `expected`
let current = products.get("p1").await?;
let expected_bytes = current.as_ref().map(|v| serde_json::to_vec(v).unwrap());
products.put_if(
    "p1",
    expected_bytes,
    json!({"id": "p1", "name": "Widget", "price": 19.99}),
).await?;

// Or with raw bytes
products.put_if_bytes("p1", Some(&old_bytes), &new_bytes).await?;
```

`put_if_bytes` is what the durable-queue and other coordination
primitives ride on — see `__yeti_queue` patterns.

### Search and group-by

```rust,ignore
// All records where field == value (uses index if available)
let active = users.find("status", "active").await?;
let admin  = users.find_one("role", "admin").await?;

// Count grouped by field value
let counts: HashMap<String, usize> = orders.count_by("status").await?;
// {"shipped": 42, "pending": 7, "cancelled": 3}

// Records grouped by field value
let by_cat: HashMap<String, Vec<Value>> = products.group_by("category").await?;
```

### Pub/sub on a table

```rust,ignore
let mut rx = orders.subscribe_all().await?;
while let Ok(msg) = rx.recv().await {
    yeti_log::info!("order {:?} {}", msg.id, msg.message_type);
}

// Subscribe to a single record's updates
let mut rx = orders.subscribe_id("order-123").await?;

// Publish to a (table, id) topic
orders.publish("order-123", json!({"event": "shipped"})).await?;
```

Tables with `@export(sse: true, ws: true, mqtt: true)` (defaults) have
pubsub wired automatically; this is the same channel SSE / WS / MQTT
subscribers consume.

## Query — filtered reads

```rust,ignore
let results: Vec<Value> = orders.query()
    .where_eq("status", "pending")
    .where_gt("amount", 100)
    .where_lt("amount", 1000)
    .limit(20)
    .offset(0)
    .execute()
    .await?;
```

### Predicates

| Method | Meaning |
|---|---|
| `where_eq(f, v)` / `where_strict_eq` | `f == v` (coerce) / `f === v` (strict) |
| `where_ne(f, v)` | `f != v` |
| `where_gt` / `where_gte` / `where_lt` / `where_lte` | numeric / lexical |
| `where_contains(f, v)` / `where_starts_with` / `where_ends_with` | substring |
| `where_true(f)` / `where_false(f)` | boolean shortcuts |
| `where_null(f)` / `where_not_null(f)` | null check |
| `where_between(f, lo, hi)` | `lo < f < hi` |
| `where_between_inclusive(f, lo, hi)` | `lo <= f <= hi` |

### Conditional filters

Skip a predicate when its input is empty/zero — clean for forwarding
URL query params:

```rust,ignore
let category = ctx.query("category").unwrap_or("");
let min_price: f64 = ctx.query_int("min_price").unwrap_or(0) as f64;

let results: Vec<Value> = products.query()
    .where_eq_non_empty("category", category)
    .where_gte_if("price", min_price, min_price > 0.0)
    .execute()
    .await?;
```

Available: `where_eq_if`, `where_eq_non_empty`, `where_gt_if`,
`where_gte_if`, `where_lt_if`, `where_lte_if`.

### AND vs OR

```rust,ignore
// AND (default)
.where_eq("status", "active").where_eq("role", "admin")

// OR
.or().where_eq("name", "Alice").where_eq("name", "Bob")
```

### Terminal methods

```rust,ignore
query.execute().await?            // Vec<Value>
query.count().await?               // usize
query.first().await?               // Option<Value>
query.first_or_err("not found").await?   // Value (404)
```

## Vector search

For tables with a `Vector` field (typically auto-indexed HNSW):

```rust,ignore
let results = articles.vector_search(
    "machine learning fundamentals",  // query text (auto-embedded)
    10,                                // top-k
).await?;
```

See [Vector Search](../../guides/querying/vector-search.md) for the
full API including raw-vector input and per-call HNSW params.

## TableExt — raw typed backend

When you need custom keys, batch operations, or types yeti doesn't
serialize for you:

```rust,ignore
let backend = ctx.table("Config")?.backend();

#[derive(Serialize, Deserialize)]
struct AppConfig { theme: String, max_items: u32 }

// Typed get / put
let cfg: Option<AppConfig> = TableExt::get(&*backend, "settings").await?;
TableExt::put(&*backend, "settings", &cfg).await?;

// With default
let cfg: AppConfig = TableExt::get_or(&*backend, "settings", default).await?;

// Required (404 on miss)
let cfg: AppConfig = TableExt::get_required(&*backend, "settings").await?;

// Batch
let many: Vec<Option<AppConfig>> = TableExt::get_many(&*backend, &["a","b","c"]).await?;

// Prefix scan
let tenant_users: Vec<Value> = TableExt::scan_records_with_prefix(&*backend, "tenant:123:").await?;
let keys: Vec<String> = TableExt::scan_key_names(&*backend, "user:").await?;
```

System keys (`__yeti_*`, index entries `:idx:*`) are filtered from
scan results automatically.

## Complete example

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Dashboard {
    get(ctx) => {
        let orders = ctx.table("Order")?;

        let total       = orders.count().await?;
        let by_status   = orders.count_by("status").await?;
        let high_value: Vec<Value> = orders.query()
            .where_gt("amount", 1000)
            .where_eq("status", "pending")
            .limit(5)
            .execute()
            .await?;

        ok(json!({
            "totalOrders":      total,
            "byStatus":         by_status,
            "highValuePending": high_value,
        }))
    }
});
```

## See also

- [Schema Directives](../config/schema-directives.md) — `@indexed`, `@compositeIndex`, `@vector`
- [Vector Search](../../guides/querying/vector-search.md) — semantic queries
- [Pub/Sub](../../guides/realtime/pubsub.md) — subscribe across HTTP/SSE/WS/MQTT
