# Full-Page Caching

Store entire HTTP responses keyed by URL path. Cache hit returns immediately; cache miss fetches from origin, stores, and returns.

## Schema

```graphql
type PageCache @table(database: "full-page-caching", expiration: 3600) {
  path: String! @primaryKey
  pageContents: String
  contentType: String
  httpStatus: Int
  cachedAt: Int
}
```

`expiration: 3600` auto-evicts entries after one hour via RocksDB TTL.

## Configuration

```yaml
name: "Full Page Cache"
app_id: "full-page-cache"
schemas:
  path: "schema.graphql"
resources:
  path: "resources/*.rs"
origin:
  url: "https://www.example.com/"
```

## Implementation

```rust,ignore
use yeti_sdk::prelude::*;

pub struct PageCache;

impl Default for PageCache {
    fn default() -> Self { Self }
}

impl Resource for PageCache {
    fn name(&self) -> &str { "PageCache" }
    fn is_default(&self) -> bool { true }

    fn get(&self, ctx: Context) -> ResourceFuture {
        Box::pin(async move {
            let path = ctx.path_id.as_deref().unwrap_or("/");
            let cache = ctx.get_table("PageCache")?;

            if let Some(cached) = cache.get(&path).await? {
                return ok_html(cached.as_str().unwrap_or_default())
                    .map(|r| r.add_header("x-cache", "HIT"));
            }

            let url = format!("https://example.com{}", &path);
            let res = fetch!(&url).send().await
                .map_err(|e| YetiError::Internal(e.to_string()))?;
            let html = res.text().await
                .map_err(|e| YetiError::Internal(e.to_string()))?;

            cache.put(&path, json!(html)).await?;
            ok_html(&html)
                .map(|r| r.add_header("x-cache", "MISS"))
        })
    }
}

register_resource!(PageCache);
```

Uses `fetch!` macro from `yeti_sdk::prelude` for external HTTP calls. Do not use `reqwest::blocking::Client` — it crashes in the dylib context.

## Testing

```bash
# Cache miss - fetches from origin
curl -sk https://localhost:9996/full-page-cache/products
# x-cache: MISS

# Cache hit - served from table
curl -sk https://localhost:9996/full-page-cache/products
# x-cache: HIT
```

## See Also

- [Caching & Performance](caching.md) - Caching overview
- [Table Expiration](table-expiration.md) - TTL configuration
- [Custom Resources](custom-resources.md) - Resource handlers
