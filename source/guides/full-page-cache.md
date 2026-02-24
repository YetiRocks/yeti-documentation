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
  - schema.graphql
resources:
  - resources/*.rs
origin:
  url: "https://www.example.com/"
```

## Implementation

```rust
pub struct PageCache;

impl Resource for PageCache {
    fn name(&self) -> &str { "PageCache" }
    fn is_default(&self) -> bool { true }

    fn get(&self, _request: Request<Vec<u8>>, ctx: ResourceParams) -> ResourceFuture {
        async_handler!({
            let path = ctx.id().unwrap_or("/");
            let cache = ctx.get_table("PageCache")?;

            if let Some(cached) = cache.get_by_id(&path).await? {
                ctx.response_headers().append("x-cache", "HIT");
                return ok_html(cached.as_str().unwrap_or_default());
            }

            let origin = ctx.config().get_str("origin.url", "https://example.com/");
            let url = format!("{}{}", origin.trim_end_matches('/'), &path);

            let (tx, rx) = std::sync::mpsc::channel();
            std::thread::spawn(move || {
                let result = reqwest::blocking::get(&url);
                let _ = tx.send(result);
            });
            let html = rx.recv()??.text()?;

            cache.put(&path, json!(html)).await?;
            ctx.response_headers().append("x-cache", "MISS");
            ok_html(&html)
        })
    }
}

register_resource!(PageCache);
```

`reqwest::blocking` on a `std::thread` is required because dylib plugins have their own tokio runtime copy due to TLS isolation.

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
